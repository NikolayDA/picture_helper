"""Tab-Builder für ``RightPanel``.

Jede Tab-Klasse baut genau einen Tab des rechten Panels.
``build()`` liefert ein ``(Widget, dict[str, QWidget])``-Paar, das der
zentrale Builder in das ``RightPanel``-DTO weiterreicht.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PIL import Image
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
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
from bgremover.theme import (
    CARD_STYLE,
    PRIMARY_BTN_STYLE,
    SECTION_HEADER_STYLE,
    SLD_STYLE,
    _Theme,
)

if TYPE_CHECKING:
    from bgremover.right_panel import RightPanelActions


# ── Segmented-Control für den Vorschaumodus (§5.7) ───────────────


class _ModeSegments(QWidget):
    """Segmented-Control für den 2D-Vorschaumodus (Farbe/Relief/Höhe/Gloss).

    Ein Klick meldet den Modus über ``on_select``; ``set_mode`` spiegelt einen
    von außen gesetzten Modus, ohne erneut zu melden (kein Feedback-Loop mit dem
    ``previewSettingsChanged``-Sync). Der kombinierte Modus bleibt bewusst außen
    vor (über das Ansicht-Menü erreichbar, §9 Schritt 6).
    """

    def __init__(
        self, on_select: Callable[[PreviewMode], None], parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_select = on_select
        self._buttons: dict[PreviewMode, QPushButton] = {}
        self._current = PreviewMode.COLOR
        self.setObjectName("modeSegments")
        self.setStyleSheet(
            f"QWidget#modeSegments {{ background:{_Theme.BG_TABBAR};"
            f" border:1px solid {_Theme.BORDER}; border-radius:9px; }}")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(3)
        # Literale ``tr``-Kurzlabels (i18n-Coverage zählt nur Literal-Aufrufe).
        modes: list[tuple[str, PreviewMode]] = [
            (tr("preview.seg.color"), PreviewMode.COLOR),
            (tr("preview.seg.relief"), PreviewMode.RELIEF),
            (tr("preview.seg.height"), PreviewMode.HEIGHT),
            (tr("preview.seg.gloss"), PreviewMode.GLOSS),
        ]
        for label, mode in modes:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, m=mode: self._select(m))
            self._buttons[mode] = btn
            lay.addWidget(btn, 1)
        self.set_mode(PreviewMode.COLOR)

    @staticmethod
    def _seg_style(active: bool) -> str:
        if active:
            return (f"QPushButton {{ background:{_Theme.ACCENT}; color:#fff;"
                    " border:none; border-radius:6px; font-size:12px;"
                    " font-weight:500; padding:7px 4px; }")
        return (f"QPushButton {{ background:transparent; color:{_Theme.TEXT_3};"
                " border:none; border-radius:6px; font-size:12px; padding:7px 4px; }"
                f"QPushButton:hover {{ color:{_Theme.TEXT_BRIGHT}; }}")

    def set_mode(self, mode: PreviewMode) -> None:
        """Spiegelt den aktiven Modus (rein visuell, ohne ``on_select``)."""
        self._current = mode
        for m, btn in self._buttons.items():
            active = m is mode
            btn.setChecked(active)
            btn.setStyleSheet(self._seg_style(active))

    def _select(self, mode: PreviewMode) -> None:
        self.set_mode(mode)
        self._on_select(mode)

    def current_mode(self) -> PreviewMode:
        return self._current

    def mode_labels(self) -> list[str]:
        return [btn.text() for btn in self._buttons.values()]


# ── Tab 1 – Vorschau ─────────────────────────────────────────────


class PreviewTab:
    """Expliziter 2D-Anzeigemodus samt live wirksamen Relief-/Gloss-Optionen."""

    def __init__(self, actions: RightPanelActions) -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()
        group, body = _make_section(tr("right_panel.preview.section"))
        body.addWidget(_make_label(tr("right_panel.preview.hint"), "#8aaed0", 11))

        body.addWidget(_make_label(tr("right_panel.preview.mode"), "#aaa"))
        # Segmented-Control statt Combobox (§5.7, §9 Schritt 6, #439). Der
        # kombinierte Modus bleibt über das Ansicht-Menü erreichbar.
        mode_segments = _ModeSegments(self._actions.set_preview_mode)
        body.addWidget(mode_segments)
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

        info = _make_label(tr("right_panel.preview.export_hint"), "#8aaed0", 11)
        body.addWidget(_make_hdivider())
        body.addWidget(info)
        layout.addWidget(group)
        refs_extra = {"preview_mode_segments": mode_segments}

        # ── Karte „Speichern" (§9 Schritt 6, #439) ──
        g_save, gsv = _make_section(tr("right_panel.export.section.save"))
        gsv.addWidget(_make_label(tr("right_panel.export.format_label"), "#aaa"))
        fmt_grid = QGridLayout(); fmt_grid.setSpacing(8)
        fmt_buttons: dict[str, QPushButton] = {}

        def select_format(fmt: str) -> None:
            self._actions.set_save_format(fmt)
            for name, btn in fmt_buttons.items():
                _set_button_selected(btn, name == fmt)

        for i, fmt in enumerate(("PNG", "JPEG", "WebP", "TIFF")):
            btn = _make_panel_btn(fmt, "#2a2a2a", "#c0c0c0", "#363636")
            btn.clicked.connect(lambda _=False, f=fmt: select_format(f))
            fmt_buttons[fmt] = btn
            fmt_grid.addWidget(btn, i // 2, i % 2)
        _set_button_selected(fmt_buttons["PNG"], True)
        gsv.addLayout(fmt_grid)
        btn_save = _make_primary_btn(
            tr("right_panel.export.save"), tr("right_panel.export.save.tooltip"))
        btn_save.clicked.connect(lambda _=False: self._actions.save())
        gsv.addWidget(btn_save)
        layout.addWidget(g_save)

        # ── Karte „UV-Druck" (§9 Schritt 6, #439) ──
        g_uv, guv = _make_section(tr("right_panel.export.section.uvprint"))
        btn_eufy = _make_panel_btn(
            tr("right_panel.export.eufymake"), "#141e38", "#8aaedd", "#1e2e52",
            tr("right_panel.export.eufymake.tooltip"), height=44)
        btn_eufy.clicked.connect(lambda _=False: self._actions.export_eufymake())
        guv.addWidget(btn_eufy)
        layout.addWidget(g_uv)

        layout.addStretch()
        return outer, {
            **refs_extra,
            "preview_relief_label": relief_label,
            "preview_relief_slider": relief_slider,
            "preview_gloss_visible": gloss_visible,
            "preview_export_hint": info,
            "export_save": btn_save,
            "export_eufymake": btn_eufy,
            "export_format_png": fmt_buttons["PNG"],
            "export_format_jpeg": fmt_buttons["JPEG"],
        }


# ── Tab 2 – Auswahl ──────────────────────────────────────────────


class SelectionTab:
    """Werkzeug-Hinweise, Toleranz/Pinsel, Morphologie."""

    def __init__(self, actions: RightPanelActions) -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()

        # KI-Primärbutton oben im Inspector (§9 Schritt 2, #437).
        btn_ai = _make_primary_btn(
            tr("right_panel.ai.remove"), tr("right_panel.ai.remove.tooltip"))
        btn_ai.clicked.connect(lambda _=False: self._actions.run_ai())
        layout.addWidget(btn_ai)

        sub_mod = "Cmd" if _IS_MACOS else "Ctrl"

        # Karte „Werkzeug-Einstellungen" – Toleranz + Pinselgröße (§9 Schritt 2)
        g_sel, gs = _make_section(tr("right_panel.selection.section.settings"))
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

        # Karte „Auswahl" – Invertieren/Aufheben + Erweitern/Schrumpfen (§9)
        g_select, gsel = _make_section(tr("right_panel.selection.section.select"))
        row_ci = QHBoxLayout(); row_ci.setSpacing(6)
        btn_inv = _make_panel_btn(
            tr("right_panel.selection.invert"), "#2a2a2a", "#c0c0c0", "#363636",
            tr("right_panel.selection.invert.tooltip", modifier=sub_mod))
        btn_inv.clicked.connect(lambda _=False: self._actions.invert_selection())
        btn_clr = _make_panel_btn(
            tr("right_panel.selection.clear"), "#2a2a2a", "#c0c0c0", "#363636",
            tr("right_panel.selection.clear.tooltip"))
        btn_clr.clicked.connect(lambda _=False: self._actions.clear_selection())
        row_ci.addWidget(btn_inv)
        row_ci.addWidget(btn_clr)
        gsel.addLayout(row_ci)

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
        gsel.addLayout(morph_row)
        layout.addWidget(g_select)

        layout.addStretch()

        return outer, {
            "ai_remove": btn_ai,
            "tolerance_label": tolerance_label,
            "tolerance_slider": tolerance_slider,
            "brush_label": brush_label,
            "brush_slider": brush_slider,
            "morph_spin": morph_spin,
        }


# ── Tab 3 – Hintergrund ──────────────────────────────────────────


class BackgroundTab:
    """Transparent machen oder Farbe ersetzen."""

    def __init__(self, actions: RightPanelActions) -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()

        g_bg, gb = _make_section(tr("right_panel.background.section"))
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

        g_edge, ge = _make_section(tr("right_panel.background.section.feather"))
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


# ── Tab 5 – Transform ────────────────────────────────────────────


class TransformTab:
    """Drehen und Spiegeln."""

    def __init__(self, actions: RightPanelActions) -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()

        g_rot, gr2 = _make_section(tr("right_panel.transform.section.rotate"))
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

        g_flip, gf = _make_section(tr("right_panel.transform.section.flip"))
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
        layout.addStretch()

        return outer, {
            "rotation_slider": rotation_slider,
            "rotation_spin": rotation_spin,
        }


# ── Tab 6 – Form & Zuschnitt ─────────────────────────────────────


class ShapeTab:
    """Ecken abrunden und Ausgabeformat-Zuschnitt."""

    def __init__(self, actions: RightPanelActions) -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()

        g_corner, gc = _make_section(tr("right_panel.shape.section.corner"))
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

        # Karte „Größe ändern" – Inline-Felder w × h (§9 Schritt 4, #438)
        g_size, gsz = _make_section(tr("right_panel.shape.section.resize"))
        size_row = QHBoxLayout(); size_row.setSpacing(6)
        resize_w = QSpinBox(); resize_w.setRange(1, 60000); resize_w.setValue(1200)
        resize_w.setFixedWidth(76); resize_w.setStyleSheet(_SPIN_STYLE)
        resize_h = QSpinBox(); resize_h.setRange(1, 60000); resize_h.setValue(900)
        resize_h.setFixedWidth(76); resize_h.setStyleSheet(_SPIN_STYLE)
        size_row.addWidget(resize_w)
        size_row.addWidget(_make_label("×", "#888"))
        size_row.addWidget(resize_h)
        size_row.addWidget(_make_label("px", "#888"))
        size_row.addStretch()
        gsz.addLayout(size_row)
        btn_resize = _make_panel_btn(
            tr("right_panel.shape.resize_apply"), "#2a2a2a", "#c0c0c0", "#363636",
            tr("right_panel.shape.resize_apply.tooltip"))
        btn_resize.clicked.connect(
            lambda _=False: self._actions.apply_resize(resize_w.value(), resize_h.value()))
        gsz.addWidget(btn_resize)
        layout.addWidget(g_size)

        # Karte „Zuschnitt-Format" – 3×2-Raster mit genau sechs Formaten (§9)
        g_fmt, gfm = _make_section(tr("right_panel.shape.section.format"))
        grid = QGridLayout(); grid.setSpacing(8)
        btn_circle = _make_panel_btn(
            tr("right_panel.shape.circle"), "#2a2a2a", "#c0c0c0", "#363636",
            tr("right_panel.shape.circle.tooltip"))
        btn_circle.clicked.connect(lambda _=False: self._actions.start_crop_circle())
        grid.addWidget(btn_circle, 0, 0)
        ratios = [("1:1", 1, 1), ("16:9", 16, 9), ("4:3", 4, 3),
                  ("9:16", 9, 16), ("3:4", 3, 4)]
        for idx, (label, rw, rh) in enumerate(ratios, start=1):
            b = _make_panel_btn(label, "#2a2a2a", "#c0c0c0", "#363636")
            b.clicked.connect(
                lambda _=False, w=rw, h=rh: self._actions.start_crop_ratio(w, h))
            grid.addWidget(b, idx // 3, idx % 3)
        gfm.addLayout(grid)
        layout.addWidget(g_fmt)
        layout.addStretch()

        return outer, {
            "corner_label": corner_label,
            "corner_slider": corner_slider,
            "resize_w": resize_w,
            "resize_h": resize_h,
        }


# ── Tab 4 – Anpassen (Farbkorrektur) ─────────────────────────────


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
        g_adj, ga = _make_section(tr("right_panel.adjust.section"))
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


def _make_section(title: str, accent: str = _Theme.ACCENT) -> tuple[QWidget, QVBoxLayout]:
    """Sektion als **Karte** mit einheitlichem blauem Akzentkopf (Epic #413).

    Kapselt jede Sektion in eine Karte (Hintergrund, dünner Rahmen, Radius) mit
    Kopfzeile aus blauem Akzentstrich + Titel. Der ``accent``-Parameter bleibt aus
    Kompatibilität mit den Aufrufstellen erhalten, wird aber **bewusst ignoriert**:
    alle Sektionsköpfe nutzen dasselbe Blau (``_Theme.ACCENT``) – keine
    Amber-/Coral-Sonderfarben mehr (Issue #416).
    """
    card = QFrame()
    card.setObjectName("sectionCard")
    # Objektname-Selektor, damit der Karten-Stil NICHT auf Kindwidgets kaskadiert.
    card.setStyleSheet(f"QFrame#sectionCard {{ {CARD_STYLE} }}")
    v = QVBoxLayout(card)
    v.setSpacing(10)
    v.setContentsMargins(14, 13, 14, 13)
    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(SECTION_HEADER_STYLE)
    v.addWidget(title_lbl)
    return card, v


def _make_label(text: str, color: str = "#888", size: int = 12) -> QLabel:
    """Einfaches Info-Label mit anpassbarer Farbe und Schriftgrösse."""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {color}; font-size: {size}px; background: transparent;")
    lbl.setWordWrap(True)
    return lbl


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


def _set_button_selected(btn: QPushButton, selected: bool) -> None:
    """Schaltet einen Sekundärbutton zwischen normal und ausgewählt (`.sel`, §5.3)."""
    if selected:
        btn.setStyleSheet(
            f"QPushButton {{ background:{_Theme.ACCENT_SOFT}; color:{_Theme.ACCENT_TEXT};"
            f" border:1px solid {_Theme.ACCENT}; border-radius:8px; padding:0 14px;"
            " font-size:12px; font-weight:600; min-height:36px; }")
    else:
        btn.setStyleSheet(
            "QPushButton { background:#2a2a2a; color:#c0c0c0; border:none;"
            " border-radius:8px; padding:0 14px; font-size:12px; min-height:36px; }"
            "QPushButton:hover { background:#363636; }")


def _make_primary_btn(label: str, tooltip: str = "") -> QPushButton:
    """Blauer Primärbutton (§5.4) für hervorgehobene Aktionen im Inspector."""
    b = QPushButton(label)
    b.setStyleSheet(PRIMARY_BTN_STYLE)
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
