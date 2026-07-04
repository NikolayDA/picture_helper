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
from PyQt6.QtGui import QColor, QFont, QFontMetrics
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from bgremover.color_ops import adjust_color
from bgremover.constants import _COLOR_BTN_SIZE, _IS_MACOS, _RIGHT_PANEL_WIDTH
from bgremover.i18n import tr
from bgremover.icons import make_tool_icon
from bgremover.preview_mode import PreviewMode
from bgremover.theme import (
    CARD_CONTENT_SPACING,
    CARD_PADDING,
    CARD_STACK_BOTTOM_MARGIN,
    CARD_STACK_SIDE_MARGIN,
    CARD_STACK_SPACING,
    CARD_STACK_TOP_MARGIN,
    active_palette,
    card_style,
    num_style,
    panel_btn_style,
    primary_btn_style,
    section_header_style,
    slider_style,
)

if TYPE_CHECKING:
    from bgremover.right_panel import RightPanelActions

# Karten-Maße stammen zentral aus ``theme`` (#414). Die Unterstrich-Aliase
# bleiben als stabile Importfläche für ``right_panel`` und die Tests erhalten.
_CARD_STACK_SIDE_MARGIN = CARD_STACK_SIDE_MARGIN
_CARD_STACK_TOP_MARGIN = CARD_STACK_TOP_MARGIN
_CARD_STACK_BOTTOM_MARGIN = CARD_STACK_BOTTOM_MARGIN
_CARD_STACK_SPACING = CARD_STACK_SPACING
_OPTION_SPACING = 6
# Nutzbare Textbreite innerhalb einer Inspector-Karte (§1: Scrollbereich-
# Seitenrand + §5.1: horizontales Kartenpolster) – als Wortumbruch-Obergrenze
# für lange, nicht kürzbare Button-Beschriftungen (z. B. Übersetzungen), damit
# sie die feste Panelbreite nie sprengen (#423-Review, Spec §5.3).
_CARD_TEXT_WIDTH = _RIGHT_PANEL_WIDTH - 2 * CARD_STACK_SIDE_MARGIN - 2 * CARD_PADDING[0]


def _wrap_to_width(text: str, font: QFont, max_width: int) -> str:
    """Bricht ``text`` wortweise um, sodass keine Zeile ``max_width`` überschreitet.

    Reine Fontmetrik-Messung (keine hartkodierten Sprach-Umbrüche) – funktioniert
    unverändert für alle Laufzeitsprachen (de/en).
    """
    fm = QFontMetrics(font)
    words = text.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if not current or fm.horizontalAdvance(trial) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines)


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
        p = active_palette()
        # inset statt tabbar (#479): der Prototyp hinterlegt den Container
        # dieses Segmented-Controls mit der rezessierten --inset-Fläche.
        self.setStyleSheet(
            f"QWidget#modeSegments {{ background:{p.inset};"
            f" border:1px solid {p.border}; border-radius:9px; }}")
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
        p = active_palette()
        if active:
            return (f"QPushButton {{ background:{p.accent}; color:{p.on_accent};"
                    " border:none; border-radius:6px; font-size:12px;"
                    " font-weight:500; padding:7px 4px; }"
                    f"QPushButton:focus {{ outline:none; border:2px solid {p.on_accent}; }}")
        return (f"QPushButton {{ background:transparent; color:{p.text3};"
                " border:none; border-radius:6px; font-size:12px; padding:7px 4px; }"
                f"QPushButton:hover {{ color:{p.text}; }}"
                f"QPushButton:focus {{ outline:none; border:1px solid {p.accent}; }}")

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
        # min-height sichert die 24-px-Trefferfläche (#441); Textfarbe über Token.
        gloss_visible.setStyleSheet(
            f"QCheckBox {{ color:{_label_color('#bbb')}; background:transparent;"
            " spacing:8px; min-height:24px; }"
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
            btn = _make_neutral_btn(fmt)
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
        btn_eufy = _make_neutral_btn(
            tr("right_panel.export.eufymake"),
            tr("right_panel.export.eufymake.tooltip"), height=40, wrap=True)
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

    def __init__(
        self, actions: RightPanelActions, *, rembg_available: bool = True,
    ) -> None:
        self._actions = actions
        self._rembg_available = rembg_available

    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()

        # KI-Primärbutton oben im Inspector (§9 Schritt 2, #437). Umbruch, da die
        # DE-Beschriftung bei 332 px Panelbreite die Button-Fläche sprengt.
        btn_ai = _make_primary_btn(
            tr("right_panel.ai.remove"),
            (tr("right_panel.ai.remove.tooltip")
             if self._rembg_available else tr("toolbar.ai.missing.tooltip")),
            icon_name="ai", wrap=True)
        btn_ai.setEnabled(self._rembg_available)
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
        row_ci = QHBoxLayout(); row_ci.setObjectName("selectionActionRow")
        row_ci.setSpacing(_OPTION_SPACING)
        btn_inv = _make_neutral_btn(
            tr("right_panel.selection.invert"),
            tr("right_panel.selection.invert.tooltip", modifier=sub_mod))
        btn_inv.clicked.connect(lambda _=False: self._actions.invert_selection())
        btn_clr = _make_neutral_btn(
            tr("right_panel.selection.clear"),
            tr("right_panel.selection.clear.tooltip"))
        btn_clr.clicked.connect(lambda _=False: self._actions.clear_selection())
        row_ci.addWidget(btn_inv, 1)
        row_ci.addWidget(btn_clr, 1)
        gsel.addLayout(row_ci)

        morph_row = QHBoxLayout(); morph_row.setObjectName("selectionMorphRow")
        morph_row.setSpacing(_OPTION_SPACING)
        morph_spin = QSpinBox()
        morph_spin.setRange(1, 20); morph_spin.setValue(2)
        morph_spin.setSuffix(" px")
        # Schmaler als die 72 px anderer Zahlenfelder: nur zweistellige Werte
        # (1-20), muss neben zwei Buttons in der 332-px-Karte Platz finden.
        morph_spin.setFixedWidth(54)
        morph_spin.setToolTip(tr("right_panel.selection.morph.tooltip"))
        morph_spin.setStyleSheet(_spin_style())
        btn_expand = _make_semantic_btn(
            tr("right_panel.selection.expand"), good=True,
            tooltip=tr("right_panel.selection.expand.tooltip"))
        btn_expand.clicked.connect(
            lambda _=False: self._actions.expand_selection(morph_spin.value()))
        btn_shrink = _make_semantic_btn(
            tr("right_panel.selection.shrink"), good=False,
            tooltip=tr("right_panel.selection.shrink.tooltip"))
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
        btn_rem = _make_neutral_btn(
            tr("right_panel.background.remove"),
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
            f"QPushButton:hover {{ border-color: {active_palette().accent}; }}"
            f"QPushButton:focus {{ outline:none; border-color: {active_palette().accent}; }}")
        color_button.clicked.connect(lambda _=False: self._actions.pick_color())
        color_row.addWidget(color_button)
        btn_repl = _make_neutral_btn(
            tr("right_panel.background.replace"),
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
        btn_feather = _make_neutral_btn(
            tr("right_panel.background.feather"),
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

        gr2.addWidget(_make_label(tr("right_panel.transform.quick_label"), "#888"))
        row_q1 = QHBoxLayout(); row_q1.setSpacing(_OPTION_SPACING)
        for label, deg, tip in [
            (tr("right_panel.transform.rotate_left_90"), 90,
             tr("right_panel.transform.rotate_left_90.tooltip")),
            (tr("right_panel.transform.rotate_right_90"), -90,
             tr("right_panel.transform.rotate_right_90.tooltip")),
        ]:
            b = _make_neutral_btn(label, tip)
            b.clicked.connect(lambda _=False, d=deg: self._actions.rotate(d))
            row_q1.addWidget(b, 1)
        gr2.addLayout(row_q1)

        row_q2 = QHBoxLayout(); row_q2.setSpacing(_OPTION_SPACING)
        for label, deg, tip in [
            (tr("right_panel.transform.rotate_180"), 180,
             tr("right_panel.transform.rotate_180.tooltip")),
            (tr("right_panel.transform.rotate_270"), 270,
             tr("right_panel.transform.rotate_270.tooltip")),
        ]:
            b = _make_neutral_btn(label, tip)
            b.clicked.connect(lambda _=False, d=deg: self._actions.rotate(d))
            row_q2.addWidget(b, 1)
        gr2.addLayout(row_q2)

        gr2.addWidget(_make_hdivider())
        gr2.addWidget(_make_label(tr("right_panel.transform.free_label"), "#888"))
        row_free = QHBoxLayout(); row_free.setSpacing(_OPTION_SPACING)
        rotation_slider = QSlider(Qt.Orientation.Horizontal)
        rotation_slider.setRange(-180, 180); rotation_slider.setValue(0)
        rotation_slider.setStyleSheet(slider_style(active_palette()))
        rotation_slider.setToolTip(tr("right_panel.transform.angle_slider.tooltip"))
        rotation_spin = QSpinBox()
        rotation_spin.setRange(-180, 180); rotation_spin.setValue(0)
        rotation_spin.setSuffix("°")
        rotation_spin.setFixedWidth(66)
        rotation_spin.setToolTip(tr("right_panel.transform.angle_spin.tooltip"))
        rotation_spin.setStyleSheet(_spin_style())
        rotation_slider.valueChanged.connect(lambda v: rotation_spin.setValue(v))
        rotation_spin.valueChanged.connect(lambda v: rotation_slider.setValue(v))
        row_free.addWidget(rotation_slider, 1)
        row_free.addWidget(rotation_spin)
        gr2.addLayout(row_free)

        btn_rot_free = _make_neutral_btn(
            tr("right_panel.transform.apply_angle"),
            tr("right_panel.transform.apply_angle.tooltip"),
            icon_name="undo")
        btn_rot_free.clicked.connect(
            lambda _=False: self._actions.rotate(rotation_spin.value()))
        gr2.addWidget(btn_rot_free)
        layout.addWidget(g_rot)

        g_flip, gf = _make_section(tr("right_panel.transform.section.flip"))
        row_flip = QHBoxLayout(); row_flip.setSpacing(_OPTION_SPACING)
        btn_fh = _make_neutral_btn(
            tr("right_panel.transform.flip_h"),
            tr("right_panel.transform.flip_h.tooltip"))
        btn_fh.clicked.connect(lambda _=False: self._actions.flip(True))
        row_flip.addWidget(btn_fh, 1)
        btn_fv = _make_neutral_btn(
            tr("right_panel.transform.flip_v"),
            tr("right_panel.transform.flip_v.tooltip"))
        btn_fv.clicked.connect(lambda _=False: self._actions.flip(False))
        row_flip.addWidget(btn_fv, 1)
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
        btn_corner = _make_neutral_btn(
            tr("right_panel.shape.round"),
            tr("right_panel.shape.round.tooltip"),
            height=38, icon_name="form")
        btn_corner.clicked.connect(
            lambda _=False: self._actions.round_corners(corner_slider.value()))
        gc.addWidget(btn_corner)
        layout.addWidget(g_corner)

        # Karte „Größe ändern" – Inline-Felder w × h (§9 Schritt 4, #438)
        g_size, gsz = _make_section(tr("right_panel.shape.section.resize"))
        size_row = QHBoxLayout(); size_row.setSpacing(_OPTION_SPACING)
        resize_w = QSpinBox(); resize_w.setRange(1, 60000); resize_w.setValue(1200)
        resize_w.setFixedWidth(76); resize_w.setStyleSheet(_spin_style())
        resize_h = QSpinBox(); resize_h.setRange(1, 60000); resize_h.setValue(900)
        resize_h.setFixedWidth(76); resize_h.setStyleSheet(_spin_style())
        size_row.addWidget(resize_w)
        size_row.addWidget(_make_label("×", "#888"))
        size_row.addWidget(resize_h)
        size_row.addWidget(_make_label("px", "#888"))
        size_row.addStretch()
        gsz.addLayout(size_row)
        btn_resize = _make_neutral_btn(
            tr("right_panel.shape.resize_apply"),
            tr("right_panel.shape.resize_apply.tooltip"))
        btn_resize.clicked.connect(
            lambda _=False: self._actions.apply_resize(resize_w.value(), resize_h.value()))
        gsz.addWidget(btn_resize)
        layout.addWidget(g_size)

        # Karte „Zuschnitt-Format" – 3×2-Raster mit genau sechs Formaten (§9)
        g_fmt, gfm = _make_section(tr("right_panel.shape.section.format"))
        grid = QGridLayout(); grid.setObjectName("shapeFormatGrid")
        grid.setSpacing(_OPTION_SPACING)
        btn_circle = _make_neutral_btn(
            tr("right_panel.shape.circle"),
            tr("right_panel.shape.circle.tooltip"))
        btn_circle.clicked.connect(lambda _=False: self._actions.start_crop_circle())
        grid.addWidget(btn_circle, 0, 0)
        ratios = [("1:1", 1, 1), ("16:9", 16, 9), ("4:3", 4, 3),
                  ("9:16", 9, 16), ("3:4", 3, 4)]
        for idx, (label, rw, rh) in enumerate(ratios, start=1):
            b = _make_neutral_btn(label)
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
        btn_reset = _make_neutral_btn(
            tr("right_panel.adjust.reset"),
            tr("right_panel.adjust.reset.tooltip"))
        # „Anwenden" nutzt den akzent-getönten .sel-Look, nicht Amber/Lila (§5.3/§9).
        btn_apply = _make_neutral_btn(
            tr("right_panel.adjust.apply"),
            tr("right_panel.adjust.apply.tooltip"))
        _set_button_selected(btn_apply, True)

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


# Zuordnung der historisch fest gewählten Label-Grautöne auf Paletten-Rollen.
# Gilt seit #441 in **beiden** Schemata: die alten Dunkel-Grautöne #666–#888
# verfehlten auf den Karten die WCAG-AA-Schwelle (z. B. #777 ≈ 3.4:1) – über die
# Token bleiben Hinweistexte in Hell wie Dunkel ≥ 4.5:1 (Kontrastmatrix-Test).
_LABEL_ROLE_MAP = {
    "#aaa": "text2", "#bbb": "text2", "#ccc": "text2",
    "#888": "text3", "#999": "text3", "#777": "text3", "#666": "text3",
    "#8aaed0": "accent_text", "#8aaedd": "accent_text",
}


def _label_color(color: str) -> str:
    """Bildet eine Label-Farbe auf die passende Rolle der aktiven Palette ab (#441)."""
    p = active_palette()
    role = _LABEL_ROLE_MAP.get(color.lower())
    if role is not None:
        return getattr(p, role)
    # Unbekannte (semantische) Farben: dunkel unverändert, hell auf text2 heben.
    return color if p.is_dark else p.text2


def _make_section(title: str, accent: str | None = None) -> tuple[QWidget, QVBoxLayout]:
    """Sektion als **Karte** mit einheitlichem blauem Akzentkopf (Epic #413).

    Kapselt jede Sektion in eine Karte (Hintergrund, dünner Rahmen, Radius) mit
    Kopfzeile aus blauem Akzentstrich + Titel. Der ``accent``-Parameter bleibt aus
    Kompatibilität mit den Aufrufstellen erhalten, wird aber **bewusst ignoriert**:
    alle Sektionsköpfe nutzen denselben Palette-Akzent – keine Amber-/Coral-
    Sonderfarben mehr (Issue #416). Karte und Kopf lesen die **aktive Palette**,
    sodass ein Neuaufbau beim Theme-Wechsel (#428) automatisch umfärbt.
    """
    p = active_palette()
    card = QFrame()
    card.setObjectName("sectionCard")
    # Objektname-Selektor, damit der Karten-Stil NICHT auf Kindwidgets kaskadiert.
    card.setStyleSheet(f"QFrame#sectionCard {{ {card_style(p)} }}")
    v = QVBoxLayout(card)
    v.setSpacing(CARD_CONTENT_SPACING)
    v.setContentsMargins(*CARD_PADDING)
    title_lbl = QLabel(title.upper())  # Kartentitel laufen VERSALIEN (§5.2)
    title_lbl.setStyleSheet(section_header_style(p))
    v.addWidget(title_lbl)
    return card, v


def _make_label(text: str, color: str = "#888", size: int = 12) -> QLabel:
    """Einfaches Info-Label mit anpassbarer Farbe und Schriftgrösse."""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {_label_color(color)}; font-size: {size}px; background: transparent;")
    lbl.setWordWrap(True)
    return lbl


def _make_hdivider() -> QWidget:
    """Dünne horizontale Trennlinie für das rechte Panel."""
    f = QWidget()
    f.setFixedHeight(1)
    f.setStyleSheet(f"background: {active_palette().divider};")
    return f


def _make_scroll_tab() -> tuple[QWidget, QVBoxLayout]:
    """Nicht-scrollender Inhalts-Container (Karten-Stapel) eines Schritts.

    Das Scrollen übernimmt seit #440 die Schritt-Seite (`_content_page`), sodass
    jeder Schritt genau **einen** Scrollbereich hat (kein Doppel-Scroll mehr).
    """
    content = QWidget()
    content.setStyleSheet(f"background: {active_palette().inspector};")
    lay = QVBoxLayout(content)
    # Scrollbereich-Innenabstand + Kartenabstand 1:1 aus dem Prototyp (§1, §5.1).
    lay.setContentsMargins(
        _CARD_STACK_SIDE_MARGIN, _CARD_STACK_TOP_MARGIN,
        _CARD_STACK_SIDE_MARGIN, _CARD_STACK_BOTTOM_MARGIN)
    lay.setSpacing(_CARD_STACK_SPACING)
    return content, lay


def _make_panel_btn(label: str, bg: str, fg: str, hover: str,
                    tooltip: str = "", height: int = 36,
                    icon_name: str = "") -> QPushButton:
    """Stilisierter Aktions-Button für das rechte Panel (semantische Füllfarbe)."""
    p = active_palette()
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
        QPushButton:focus {{ outline: none; border: 1px solid {p.accent}; }}
        QPushButton:disabled {{ background: {p.divider}; color: {p.muted}; }}
    """)
    if icon_name:
        b.setIcon(make_tool_icon(icon_name, 22))
        b.setIconSize(QSize(22, 22))
    if tooltip:
        b.setToolTip(tooltip)
    return b


def _make_neutral_btn(label: str, tooltip: str = "", height: int = 36,
                      icon_name: str = "", wrap: bool = False) -> QPushButton:
    """Neutraler Sekundärbutton (§5.3) – Fläche/Text aus der **aktiven Palette**.

    Ersetzt die früher fest dunkelgrau eingefärbten Aufrufe von ``_make_panel_btn``
    (``#2a2a2a``/``#c0c0c0``/``#363636``), damit diese Buttons im hellen Schema (#428)
    lesbar bleiben. ``wrap=True`` ist die explizit erlaubte Ausnahme vom „kein
    Umbruch"-Grundsatz (§5.3-Hinweis: „außer explizit erlaubt (EufyMake-Button)").
    """
    p = active_palette()
    b = QPushButton(label)
    style = panel_btn_style(p)
    if height != 36:
        style += f"\nQPushButton {{ min-height: {height}px; }}"
    b.setStyleSheet(style)
    if icon_name:
        b.setIcon(make_tool_icon(icon_name, 22, QColor(p.text2)))
        b.setIconSize(QSize(22, 22))
    if wrap:
        font = QFont(); font.setPixelSize(13); font.setWeight(QFont.Weight.Medium)
        b.setText(_wrap_to_width(label, font, _CARD_TEXT_WIDTH - 24))
    if tooltip:
        b.setToolTip(tooltip)
    return b


def _make_semantic_btn(label: str, *, good: bool, tooltip: str = "") -> QPushButton:
    """Erweitern/Schrumpfen-Buttons (§9 Schritt 2): einzige `.bs`-Ausnahme, die
    die semantischen ``good``/``bad``-Töne statt der neutralen Fläche trägt.
    """
    p = active_palette()
    color, soft = (p.good, p.good_soft) if good else (p.bad, p.bad_soft)
    b = QPushButton(label)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {soft}; color: {color}; border: 1px solid {color};
            border-radius: 8px; padding: 0 8px; font-size: 12px; font-weight: 500;
            min-height: 34px;
        }}
        QPushButton:hover {{ background: {soft}; }}
        QPushButton:focus {{ outline: none; border: 2px solid {color}; }}
        QPushButton:disabled {{ background: {p.divider}; color: {p.muted}; border-color: transparent; }}
    """)
    if tooltip:
        b.setToolTip(tooltip)
    return b


def _set_button_selected(btn: QPushButton, selected: bool) -> None:
    """Schaltet einen Sekundärbutton zwischen normal und ausgewählt (`.sel`, §5.3)."""
    p = active_palette()
    if selected:
        btn.setStyleSheet(
            f"QPushButton {{ background:{p.accent_soft}; color:{p.accent_text};"
            f" border:1px solid {p.accent}; border-radius:8px; padding:0 14px;"
            " font-size:12px; font-weight:600; min-height:36px; }"
            f"QPushButton:focus {{ outline:none; border:2px solid {p.accent}; }}")
    else:
        btn.setStyleSheet(panel_btn_style(p))


def _make_primary_btn(
    label: str, tooltip: str = "", icon_name: str = "", wrap: bool = False,
) -> QPushButton:
    """Blauer Primärbutton (§5.4) für hervorgehobene Aktionen im Inspector.

    ``wrap=True`` bricht die Beschriftung fontmetrisch um, statt die feste
    Panelbreite (332 px, §1) durch überlange Übersetzungen zu sprengen.
    """
    b = QPushButton(label)
    b.setStyleSheet(primary_btn_style(active_palette()))
    if icon_name:
        b.setIcon(make_tool_icon(icon_name, 22))
        b.setIconSize(QSize(22, 22))
    if wrap:
        font = QFont(); font.setPixelSize(14); font.setWeight(QFont.Weight.DemiBold)
        icon_allowance = 24 if icon_name else 0
        b.setText(_wrap_to_width(label, font, _CARD_TEXT_WIDTH - 24 - icon_allowance))
    if tooltip:
        b.setToolTip(tooltip)
    return b


def _make_slider(lo: int, hi: int, val: int, tip: str = "") -> QSlider:
    """Horizontaler Schieberegler mit einheitlichem Panel-Stil."""
    s = QSlider(Qt.Orientation.Horizontal)
    s.setRange(lo, hi)
    s.setValue(val)
    s.setStyleSheet(slider_style(active_palette()))
    if tip:
        s.setToolTip(tip)
    return s


def _spin_style() -> str:
    """Spinbox-/Combo-Stil aus der aktiven Palette (#428)."""
    return num_style(active_palette())
