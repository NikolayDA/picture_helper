"""Tab-Builder für ``RightPanel``.

Jede Tab-Klasse baut genau einen Tab des rechten Panels.
``build()`` liefert ein ``(Widget, dict[str, QWidget])``-Paar, das der
zentrale Builder in das ``RightPanel``-DTO weiterreicht.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import Image
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from bgremover.color_ops import adjust_color
from bgremover.constants import _COLOR_BTN_SIZE, _IS_MACOS
from bgremover.i18n import tr
from bgremover.icons import make_tool_icon
from bgremover.preview_mode import PreviewMode
from bgremover.theme import SLD_STYLE, _Theme

if TYPE_CHECKING:
    from bgremover.right_panel import RightPanelActions


# ── Tab 1 – Vorschau ─────────────────────────────────────────────


class PreviewTab:
    """Expliziter 2D-Anzeigemodus samt live wirksamen Relief-/Gloss-Optionen."""

    def __init__(self, actions: RightPanelActions) -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()
        group, body = _make_section(tr("right_panel.preview.section"), "#65a9e8")
        body.addWidget(_make_label(tr("right_panel.preview.hint"), "#8aaed0", 11))

        body.addWidget(_make_label(tr("right_panel.preview.mode"), "#aaa"))
        mode_combo = QComboBox()
        mode_combo.setToolTip(tr("right_panel.preview.mode.tooltip"))
        mode_combo.setStyleSheet(
            "QComboBox { background:#222; color:#ddd; border:1px solid #3a3a3a;"
            " border-radius:6px; padding:6px 8px; }"
            "QComboBox QAbstractItemView { background:#252525; color:#ddd; }"
        )
        for label, mode in (
            (tr("preview.mode.color"), PreviewMode.COLOR),
            (tr("preview.mode.relief"), PreviewMode.RELIEF),
            (tr("preview.mode.height"), PreviewMode.HEIGHT),
            (tr("preview.mode.gloss"), PreviewMode.GLOSS),
            (tr("preview.mode.combined"), PreviewMode.COMBINED),
        ):
            mode_combo.addItem(label, mode)

        def on_mode_changed(index: int) -> None:
            mode = mode_combo.itemData(index)
            if isinstance(mode, PreviewMode):
                self._actions.set_preview_mode(mode)

        mode_combo.currentIndexChanged.connect(on_mode_changed)
        body.addWidget(mode_combo)
        body.addWidget(_make_hdivider())

        relief_label = _make_label(
            tr("right_panel.preview.relief_strength", value=70), "#aaa"
        )
        relief_slider = _make_slider(
            0, 100, 70, tr("right_panel.preview.relief_strength.tooltip")
        )

        def on_relief(value: int) -> None:
            relief_label.setText(
                tr("right_panel.preview.relief_strength", value=value)
            )
            self._actions.set_relief_strength(value)

        relief_slider.valueChanged.connect(on_relief)
        body.addWidget(relief_label)
        body.addWidget(relief_slider)

        gloss_visible = QCheckBox(tr("right_panel.preview.gloss_visible"))
        gloss_visible.setChecked(True)
        gloss_visible.setToolTip(tr("right_panel.preview.gloss_visible.tooltip"))
        gloss_visible.setStyleSheet(
            "QCheckBox { color:#bbb; background:transparent; spacing:8px; }"
        )
        gloss_visible.toggled.connect(self._actions.set_gloss_visible)
        body.addWidget(gloss_visible)

        info = _make_label(tr("right_panel.preview.export_hint"), "#d6a85f", 11)
        body.addWidget(_make_hdivider())
        body.addWidget(info)
        layout.addWidget(group)
        layout.addStretch()
        return outer, {
            "preview_mode_combo": mode_combo,
            "preview_relief_label": relief_label,
            "preview_relief_slider": relief_slider,
            "preview_gloss_visible": gloss_visible,
            "preview_export_hint": info,
        }


# ── Tab 2 – Auswahl ──────────────────────────────────────────────


class SelectionTab:
    """Werkzeug-Hinweise, Toleranz/Pinsel, Morphologie."""

    def __init__(self, actions: RightPanelActions) -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()

        g_tool, gt = _make_section(tr("right_panel.selection.section.tool"), "#4a90d9")
        hint_box = QWidget()
        hint_box.setStyleSheet("background:#1e2a38; border-radius:7px;")
        hint_lay = QVBoxLayout(hint_box)
        hint_lay.setContentsMargins(10, 8, 10, 8)
        hint_lay.setSpacing(3)
        for icon_name, txt in [
            ("wand", tr("right_panel.selection.hint.wand")),
            ("brush", tr("right_panel.selection.hint.brush")),
            ("eraser", tr("right_panel.selection.hint.eraser")),
            ("lasso", tr("right_panel.selection.hint.lasso")),
        ]:
            hint_lay.addWidget(_make_icon_row(icon_name, txt, "#7aacdd", 11))
        hint_lay.addWidget(_make_hdivider())
        sub_mod = "Cmd" if _IS_MACOS else "Ctrl"
        hint_lay.addWidget(_make_label(tr("right_panel.selection.hint.add"), "#888", 11))
        hint_lay.addWidget(_make_label(
            tr("right_panel.selection.hint.subtract", modifier=sub_mod), "#888", 11))
        gt.addWidget(hint_box)
        layout.addWidget(g_tool)

        g_sel, gs = _make_section(tr("right_panel.selection.section.settings"), "#4a90d9")
        tolerance_label = _make_label(
            tr("right_panel.selection.tolerance", value=30), "#aaa")
        tolerance_slider = _make_slider(0, 255, 30,
            tr("right_panel.selection.tolerance.tooltip"))

        def on_tolerance(value: int) -> None:
            self._actions.set_tolerance(value)
            tolerance_label.setText(tr("right_panel.selection.tolerance", value=value))

        tolerance_slider.valueChanged.connect(on_tolerance)
        gs.addWidget(tolerance_label)
        gs.addWidget(tolerance_slider)
        gs.addWidget(_make_hdivider())

        brush_label = _make_label(
            tr("right_panel.selection.brush_size", value=30), "#aaa")
        brush_slider = _make_slider(4, 200, 30,
            tr("right_panel.selection.brush_size.tooltip"))

        def on_brush(value: int) -> None:
            self._actions.set_brush_size(value)
            brush_label.setText(tr("right_panel.selection.brush_size", value=value))

        brush_slider.valueChanged.connect(on_brush)
        gs.addWidget(brush_label)
        gs.addWidget(brush_slider)
        layout.addWidget(g_sel)

        btn_clr = _make_panel_btn(
            tr("right_panel.selection.clear"), "#2a2a2a", "#c0c0c0", "#363636",
            tr("right_panel.selection.clear.tooltip"),
            icon_name="clear_sel")
        btn_clr.clicked.connect(lambda _=False: self._actions.clear_selection())
        layout.addWidget(btn_clr)

        btn_inv = _make_panel_btn(
            tr("right_panel.selection.invert"), "#2a2a2a", "#c0c0c0", "#363636",
            tr("right_panel.selection.invert.tooltip", modifier=sub_mod),
            icon_name="clear_sel")
        btn_inv.clicked.connect(lambda _=False: self._actions.invert_selection())
        layout.addWidget(btn_inv)

        morph_row = QHBoxLayout(); morph_row.setSpacing(6)
        morph_spin = QSpinBox()
        morph_spin.setRange(1, 20); morph_spin.setValue(2)
        morph_spin.setSuffix(" px")
        morph_spin.setFixedWidth(72)
        morph_spin.setToolTip(tr("right_panel.selection.morph.tooltip"))
        morph_spin.setStyleSheet(_SPIN_STYLE)
        btn_expand = _make_panel_btn(
            tr("right_panel.selection.expand"), "#1a3a1a", "#a0d0a0", "#2a5a2a",
            tr("right_panel.selection.expand.tooltip"))
        btn_expand.clicked.connect(
            lambda _=False: self._actions.expand_selection(morph_spin.value()))
        btn_shrink = _make_panel_btn(
            tr("right_panel.selection.shrink"), "#3a1a1a", "#d0a0a0", "#5a2a2a",
            tr("right_panel.selection.shrink.tooltip"))
        btn_shrink.clicked.connect(
            lambda _=False: self._actions.shrink_selection(morph_spin.value()))
        morph_row.addWidget(morph_spin)
        morph_row.addWidget(btn_expand, 1)
        morph_row.addWidget(btn_shrink, 1)
        layout.addLayout(morph_row)

        layout.addStretch()

        return outer, {
            "tolerance_label": tolerance_label,
            "tolerance_slider": tolerance_slider,
            "brush_label": brush_label,
            "brush_slider": brush_slider,
            "morph_spin": morph_spin,
        }


# ── Tab 2 – Hintergrund ──────────────────────────────────────────


class BackgroundTab:
    """Transparent machen oder Farbe ersetzen."""

    def __init__(self, actions: RightPanelActions) -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()

        g_bg, gb = _make_section(tr("right_panel.background.section"), "#e05555")
        btn_rem = _make_panel_btn(
            tr("right_panel.background.remove"), "#6a1a1a", "white", "#882020",
            tr("right_panel.background.remove.tooltip"),
            height=38, icon_name="transparency")
        btn_rem.clicked.connect(lambda _=False: self._actions.remove_background())
        gb.addWidget(btn_rem)

        gb.addWidget(_make_hdivider())
        gb.addWidget(_make_label(tr("right_panel.background.color_label"), "#888"))
        color_row = QHBoxLayout(); color_row.setSpacing(8)
        color_button = QPushButton()
        color_button.setFixedSize(_COLOR_BTN_SIZE, _COLOR_BTN_SIZE)
        color_button.setToolTip(tr("right_panel.background.color.tooltip"))
        color_button.setStyleSheet(
            "QPushButton { border-radius:6px; border:2px solid #555; }"
            "QPushButton:hover { border-color: #4a90d9; }")
        color_button.clicked.connect(lambda _=False: self._actions.pick_color())
        color_row.addWidget(color_button)
        btn_repl = _make_panel_btn(
            tr("right_panel.background.replace"), "#143a5a", "white", "#1e5080",
            tr("right_panel.background.replace.tooltip"),
            icon_name="bg")
        btn_repl.clicked.connect(lambda _=False: self._actions.replace_background())
        color_row.addWidget(btn_repl, 1)
        gb.addLayout(color_row)
        layout.addWidget(g_bg)

        g_edge, ge = _make_section(tr("right_panel.background.section.feather"), "#30a0a0")
        ge.addWidget(_make_label(tr("right_panel.background.feather_hint"), "#888", 11))
        feather_label = _make_label(
            tr("right_panel.background.feather_radius", value=2), "#aaa")
        feather_slider = _make_slider(
            0, 20, 2, tr("right_panel.background.feather_radius.tooltip"))
        feather_slider.valueChanged.connect(
            lambda v: feather_label.setText(
                tr("right_panel.background.feather_radius", value=v)))
        ge.addWidget(feather_label)
        ge.addWidget(feather_slider)
        btn_feather = _make_panel_btn(
            tr("right_panel.background.feather"), "#0e2a2a", "#7adada", "#1a4040",
            tr("right_panel.background.feather.tooltip"),
            height=38, icon_name="transparency")
        btn_feather.clicked.connect(
            lambda _=False: self._actions.feather(feather_slider.value()))
        ge.addWidget(btn_feather)
        layout.addWidget(g_edge)

        layout.addStretch()

        return outer, {
            "color_button": color_button,
            "feather_slider": feather_slider,
            "feather_label": feather_label,
            "feather_button": btn_feather,
        }


# ── Tab 3 – Transform ────────────────────────────────────────────


class TransformTab:
    """Drehen und Spiegeln."""

    def __init__(self, actions: RightPanelActions) -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()

        g_rot, gr2 = _make_section(tr("right_panel.transform.section.rotate"), "#e09a30")
        rot_bg = "#2e2510"; rot_fg = "#f0c060"; rot_hv = "#4a3a18"

        gr2.addWidget(_make_label(tr("right_panel.transform.quick_label"), "#888"))
        row_q1 = QHBoxLayout(); row_q1.setSpacing(6)
        for label, deg, tip in [
            (tr("right_panel.transform.rotate_left_90"), 90,
             tr("right_panel.transform.rotate_left_90.tooltip")),
            (tr("right_panel.transform.rotate_right_90"), -90,
             tr("right_panel.transform.rotate_right_90.tooltip")),
        ]:
            b = _make_panel_btn(label, rot_bg, rot_fg, rot_hv, tip)
            b.clicked.connect(lambda _=False, d=deg: self._actions.rotate(d))
            row_q1.addWidget(b)
        gr2.addLayout(row_q1)

        row_q2 = QHBoxLayout(); row_q2.setSpacing(6)
        for label, deg, tip in [
            (tr("right_panel.transform.rotate_180"), 180,
             tr("right_panel.transform.rotate_180.tooltip")),
            (tr("right_panel.transform.rotate_270"), 270,
             tr("right_panel.transform.rotate_270.tooltip")),
        ]:
            b = _make_panel_btn(label, rot_bg, rot_fg, rot_hv, tip)
            b.clicked.connect(lambda _=False, d=deg: self._actions.rotate(d))
            row_q2.addWidget(b)
        gr2.addLayout(row_q2)

        gr2.addWidget(_make_hdivider())
        gr2.addWidget(_make_label(tr("right_panel.transform.free_label"), "#888"))
        row_free = QHBoxLayout(); row_free.setSpacing(6)
        rotation_slider = QSlider(Qt.Orientation.Horizontal)
        rotation_slider.setRange(-180, 180); rotation_slider.setValue(0)
        rotation_slider.setStyleSheet(SLD_STYLE)
        rotation_slider.setToolTip(tr("right_panel.transform.angle_slider.tooltip"))
        rotation_spin = QSpinBox()
        rotation_spin.setRange(-180, 180); rotation_spin.setValue(0)
        rotation_spin.setSuffix("°")
        rotation_spin.setFixedWidth(66)
        rotation_spin.setToolTip(tr("right_panel.transform.angle_spin.tooltip"))
        rotation_spin.setStyleSheet(_SPIN_STYLE)
        rotation_slider.valueChanged.connect(lambda v: rotation_spin.setValue(v))
        rotation_spin.valueChanged.connect(lambda v: rotation_slider.setValue(v))
        row_free.addWidget(rotation_slider, 1)
        row_free.addWidget(rotation_spin)
        gr2.addLayout(row_free)

        btn_rot_free = _make_panel_btn(
            tr("right_panel.transform.apply_angle"), rot_bg, rot_fg, rot_hv,
            tr("right_panel.transform.apply_angle.tooltip"),
            icon_name="undo")
        btn_rot_free.clicked.connect(
            lambda _=False: self._actions.rotate(rotation_spin.value()))
        gr2.addWidget(btn_rot_free)
        layout.addWidget(g_rot)

        g_flip, gf = _make_section(tr("right_panel.transform.section.flip"), "#30a0a0")
        row_flip = QHBoxLayout(); row_flip.setSpacing(6)
        btn_fh = _make_panel_btn(
            tr("right_panel.transform.flip_h"), "#0e2a2a", "#7adada", "#1a4040",
            tr("right_panel.transform.flip_h.tooltip"))
        btn_fh.clicked.connect(lambda _=False: self._actions.flip(True))
        row_flip.addWidget(btn_fh)
        btn_fv = _make_panel_btn(
            tr("right_panel.transform.flip_v"), "#0e2a2a", "#7adada", "#1a4040",
            tr("right_panel.transform.flip_v.tooltip"))
        btn_fv.clicked.connect(lambda _=False: self._actions.flip(False))
        row_flip.addWidget(btn_fv)
        gf.addLayout(row_flip)
        layout.addWidget(g_flip)

        g_size, gsz = _make_section(tr("right_panel.transform.section.resize"), "#9060d0")
        btn_resize = _make_panel_btn(
            tr("right_panel.transform.resize"), "#1e1428", "#c0a0f0", "#2e1e44",
            tr("right_panel.transform.resize.tooltip"),
            height=38, icon_name="form")
        btn_resize.clicked.connect(lambda _=False: self._actions.resize())
        gsz.addWidget(btn_resize)
        layout.addWidget(g_size)
        layout.addStretch()

        return outer, {
            "rotation_slider": rotation_slider,
            "rotation_spin": rotation_spin,
        }


# ── Tab 4 – Form & Zuschnitt ─────────────────────────────────────


class ShapeTab:
    """Ecken abrunden und Ausgabeformat-Zuschnitt."""

    def __init__(self, actions: RightPanelActions) -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()

        g_corner, gc = _make_section(tr("right_panel.shape.section.corner"), "#30c060")
        corner_label = _make_label(tr("right_panel.shape.radius", value=0), "#aaa")
        corner_slider = _make_slider(0, 500, 0,
            tr("right_panel.shape.radius.tooltip"))
        corner_slider.valueChanged.connect(
            lambda v: corner_label.setText(tr("right_panel.shape.radius", value=v)))
        gc.addWidget(corner_label)
        gc.addWidget(corner_slider)
        btn_corner = _make_panel_btn(
            tr("right_panel.shape.round"), "#0e2a14", "#7add9a", "#1a4520",
            tr("right_panel.shape.round.tooltip"),
            height=38, icon_name="form")
        btn_corner.clicked.connect(
            lambda _=False: self._actions.round_corners(corner_slider.value()))
        gc.addWidget(btn_corner)
        layout.addWidget(g_corner)

        g_fmt, gfm = _make_section(tr("right_panel.shape.section.format"), "#9060d0")

        info_box = QWidget()
        info_box.setStyleSheet("background:#1e1628; border-radius:7px;")
        info_b = QVBoxLayout(info_box)
        info_b.setContentsMargins(10, 8, 10, 8)
        info_b.addWidget(_make_label(tr("right_panel.shape.format_info"), "#8a7aaa", 10))
        gfm.addWidget(info_box)

        gfm.addWidget(_make_label(tr("right_panel.shape.special_label"), "#777", 10))
        r_special = QHBoxLayout(); r_special.setSpacing(6)
        for label, tip, slot in [
            (tr("right_panel.shape.circle"), tr("right_panel.shape.circle.tooltip"),
             self._actions.start_crop_circle),
            (tr("right_panel.shape.square"), tr("right_panel.shape.square.tooltip"),
             lambda: self._actions.start_crop_ratio(1, 1)),
        ]:
            b = _make_panel_btn(label, "#141e38", "#8aaedd", "#1e2e52", tip)
            b.clicked.connect(lambda _=False, fn=slot: fn())
            r_special.addWidget(b)
        gfm.addLayout(r_special)

        gfm.addWidget(_make_hdivider())
        gfm.addWidget(_make_label(tr("right_panel.shape.landscape_label"), "#777", 10))
        land_formats = [
            ("16 : 9", 16, 9), ("4 : 3",  4, 3),
            ("3 : 2",  3, 2),  ("2 : 1",  2, 1),
            ("7 : 4.5", 14, 9),
        ]
        for i in range(0, len(land_formats), 2):
            row_fmt = QHBoxLayout(); row_fmt.setSpacing(6)
            for label, rw, rh in land_formats[i:i+2]:
                b = _make_panel_btn(f"▬  {label}", "#1e1428", "#c0a0f0", "#2e1e44",
                        tr("right_panel.shape.landscape.tooltip", label=label))
                b.clicked.connect(
                    lambda _=False, w=rw, h=rh: self._actions.start_crop_ratio(w, h))
                row_fmt.addWidget(b)
            gfm.addLayout(row_fmt)

        gfm.addWidget(_make_hdivider())
        gfm.addWidget(_make_label(tr("right_panel.shape.portrait_label"), "#777", 10))
        port_formats = [("9 : 16", 9, 16), ("3 : 4", 3, 4)]
        row_port = QHBoxLayout(); row_port.setSpacing(6)
        for label, rw, rh in port_formats:
            b = _make_panel_btn(f"▮  {label}", "#141e28", "#90c8cc", "#1e2e38",
                    tr("right_panel.shape.portrait.tooltip", label=label))
            b.clicked.connect(
                lambda _=False, w=rw, h=rh: self._actions.start_crop_ratio(w, h))
            row_port.addWidget(b)
        gfm.addLayout(row_port)
        layout.addWidget(g_fmt)
        layout.addStretch()

        return outer, {
            "corner_label": corner_label,
            "corner_slider": corner_slider,
        }


# ── Tab 5 – Anpassen (Farbkorrektur) ─────────────────────────────


class AdjustTab:
    """Farbkorrektur der aktiven COLOR-Ebene (#360): Helligkeit/Kontrast/Sättigung.

    Drei Regler (0–200 %, neutral 100 %) steuern eine an ihre Werte gebundene
    ``color_ops.adjust_color``-Closure. Jede Reglerbewegung aktualisiert die
    Live-Vorschau (``preview_color``); „Anwenden" committet undo-fähig
    (``apply_color``), „Zurücksetzen" stellt die Neutralwerte her und verwirft die
    Vorschau (``cancel_color_preview``). Wirkt nur auf COLOR-Ebenen – der Canvas
    überspringt Nicht-COLOR-Ebenen.
    """

    def __init__(self, actions: RightPanelActions) -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()
        g_adj, ga = _make_section(tr("right_panel.adjust.section"), "#d07ac0")
        ga.addWidget(_make_label(tr("right_panel.adjust.hint"), "#777", 11))

        bright_lbl = _make_label(tr("right_panel.adjust.brightness", value=100), "#aaa")
        bright = _make_slider(0, 200, 100, tr("right_panel.adjust.brightness.tooltip"))
        contrast_lbl = _make_label(tr("right_panel.adjust.contrast", value=100), "#aaa")
        contrast = _make_slider(0, 200, 100, tr("right_panel.adjust.contrast.tooltip"))
        sat_lbl = _make_label(tr("right_panel.adjust.saturation", value=100), "#aaa")
        sat = _make_slider(0, 200, 100, tr("right_panel.adjust.saturation.tooltip"))

        def color_op(img: Image.Image) -> Image.Image:
            # Closure liest die Reglerwerte erst beim Aufruf → stets aktuell.
            return adjust_color(
                img,
                brightness=bright.value() / 100.0,
                contrast=contrast.value() / 100.0,
                saturation=sat.value() / 100.0,
            )

        for slider, label, key in (
            (bright, bright_lbl, "right_panel.adjust.brightness"),
            (contrast, contrast_lbl, "right_panel.adjust.contrast"),
            (sat, sat_lbl, "right_panel.adjust.saturation"),
        ):
            slider.valueChanged.connect(
                lambda v, lbl=label, k=key: lbl.setText(tr(k, value=v)))
            slider.valueChanged.connect(
                lambda _v=0: self._actions.preview_color(color_op))
            ga.addWidget(label)
            ga.addWidget(slider)

        ga.addWidget(_make_hdivider())
        row = QHBoxLayout(); row.setSpacing(6)
        btn_reset = _make_panel_btn(
            tr("right_panel.adjust.reset"), "#2a2a2a", "#c0c0c0", "#363636",
            tr("right_panel.adjust.reset.tooltip"))
        btn_apply = _make_panel_btn(
            tr("right_panel.adjust.apply"), "#2a1e38", "#c8a8ee", "#3a2a50",
            tr("right_panel.adjust.apply.tooltip"))

        def on_reset(_checked: bool = False) -> None:
            for slider, label, key in (
                (bright, bright_lbl, "right_panel.adjust.brightness"),
                (contrast, contrast_lbl, "right_panel.adjust.contrast"),
                (sat, sat_lbl, "right_panel.adjust.saturation"),
            ):
                slider.blockSignals(True)
                slider.setValue(100)
                slider.blockSignals(False)
                label.setText(tr(key, value=100))
            self._actions.cancel_color_preview()

        btn_reset.clicked.connect(on_reset)
        btn_apply.clicked.connect(lambda _=False: self._actions.apply_color(color_op))
        row.addWidget(btn_reset, 1)
        row.addWidget(btn_apply, 1)
        ga.addLayout(row)

        layout.addWidget(g_adj)
        layout.addStretch()
        return outer, {
            "adjust_brightness": bright,
            "adjust_contrast": contrast,
            "adjust_saturation": sat,
            "adjust_reset": btn_reset,
            "adjust_apply": btn_apply,
        }


# ── Gemeinsame Widget-Helper ─────────────────────────────────────


def _make_section(title: str, accent: str = "#4a90d9") -> tuple[QWidget, QVBoxLayout]:
    """Sektion ohne QGroupBox – farbiger Titel + dünne Trennlinie."""
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    v = QVBoxLayout(container)
    v.setSpacing(10)
    v.setContentsMargins(0, 14, 0, 10)
    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(f"""
        color: {accent};
        font-size: 13px;
        font-weight: bold;
        background: transparent;
        padding: 2px 0 4px 8px;
        border-left: 3px solid {accent};
    """)
    v.addWidget(title_lbl)
    return container, v


def _make_label(text: str, color: str = "#888", size: int = 12) -> QLabel:
    """Einfaches Info-Label mit anpassbarer Farbe und Schriftgrösse."""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {color}; font-size: {size}px; background: transparent;")
    lbl.setWordWrap(True)
    return lbl


def _make_icon_row(icon_name: str, text: str, color: str = "#888",
                   size: int = 12, icon_px: int = 18) -> QWidget:
    """Info-Zeile: Werkzeug-Icon (wie in der Toolbar) + Text, klein."""
    row = QWidget()
    row.setStyleSheet("background: transparent;")
    h = QHBoxLayout(row)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(8)
    ic = QLabel()
    ic.setPixmap(make_tool_icon(icon_name, icon_px)
                 .pixmap(QSize(icon_px, icon_px)))
    ic.setFixedSize(icon_px, icon_px)
    ic.setStyleSheet("background: transparent;")
    txt = QLabel(text)
    txt.setStyleSheet(
        f"color: {color}; font-size: {size}px; background: transparent;")
    txt.setWordWrap(True)
    h.addWidget(ic, 0, Qt.AlignmentFlag.AlignVCenter)
    h.addWidget(txt, 1)
    return row


def _make_hdivider() -> QWidget:
    """Dünne horizontale Trennlinie für das rechte Panel."""
    f = QWidget()
    f.setFixedHeight(1)
    f.setStyleSheet(f"background: {_Theme.DIVIDER};")
    return f


def _make_scroll_tab() -> tuple[QWidget, QVBoxLayout]:
    """Gibt (outer_widget, inner_layout) mit ScrollArea zurück."""
    outer_w = QWidget()
    outer_w.setStyleSheet(f"background: {_Theme.BG_PANEL};")
    outer_lay = QVBoxLayout(outer_w)
    outer_lay.setContentsMargins(0, 0, 0, 0)
    outer_lay.setSpacing(0)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setStyleSheet("""
        QScrollArea { background: #1a1a1a; border: none; }
        QScrollBar:vertical { background: #1a1a1a; width: 6px; margin: 0; }
        QScrollBar::handle:vertical {
            background: #3a3a3a; border-radius: 3px; min-height: 20px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    """)
    inner_w = QWidget()
    inner_w.setStyleSheet(f"background: {_Theme.BG_PANEL};")
    inner_lay = QVBoxLayout(inner_w)
    inner_lay.setContentsMargins(16, 16, 16, 16)
    inner_lay.setSpacing(14)
    scroll.setWidget(inner_w)
    outer_lay.addWidget(scroll)
    return outer_w, inner_lay


def _make_panel_btn(label: str, bg: str, fg: str, hover: str,
                    tooltip: str = "", height: int = 36,
                    icon_name: str = "") -> QPushButton:
    """Stilisierter Aktions-Button für das rechte Panel."""
    b = QPushButton(label)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {bg}; color: {fg}; border: none;
            border-radius: 8px; padding: 0 14px;
            font-size: 12px; font-weight: 500;
            min-height: {height}px; text-align: center;
        }}
        QPushButton:hover {{ background: {hover}; }}
        QPushButton:pressed {{ background: {bg}; }}
        QPushButton:disabled {{ background: #252525; color: #555; }}
    """)
    if icon_name:
        b.setIcon(make_tool_icon(icon_name, 22))
        b.setIconSize(QSize(22, 22))
    if tooltip:
        b.setToolTip(tooltip)
    return b


def _make_slider(lo: int, hi: int, val: int, tip: str = "") -> QSlider:
    """Horizontaler Schieberegler mit einheitlichem Panel-Stil."""
    s = QSlider(Qt.Orientation.Horizontal)
    s.setRange(lo, hi)
    s.setValue(val)
    s.setStyleSheet(SLD_STYLE)
    if tip:
        s.setToolTip(tip)
    return s


_SPIN_STYLE = (
    "QSpinBox { background:#222; color:#ddd; border:1px solid #3a3a3a;"
    " border-radius:6px; padding:3px 5px; font-size:12px; }"
    "QSpinBox::up-button, QSpinBox::down-button { width:18px; }"
)
