"""Tab-Klassen fuer das rechte Panel."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from bgremover.constants import _COLOR_BTN_SIZE, _IS_MACOS
from bgremover.theme import SLD_STYLE
from bgremover.right_panel_widgets import (
    _SPIN_STYLE,
    _make_hdivider,
    _make_icon_row,
    _make_label,
    _make_panel_btn,
    _make_scroll_tab,
    _make_section,
    _make_slider,
)

if TYPE_CHECKING:
    from bgremover.right_panel import RightPanelActions


WidgetRefs = dict[str, QWidget]


class SelectionTab:
    def __init__(self, actions: "RightPanelActions") -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, WidgetRefs]:
        t1, l1 = _make_scroll_tab()
        refs: WidgetRefs = {}

        g_tool, gt = _make_section("Werkzeug", "#4a90d9")
        hint_box = QWidget()
        hint_box.setStyleSheet("background:#1e2a38; border-radius:7px;")
        hint_lay = QVBoxLayout(hint_box)
        hint_lay.setContentsMargins(10, 8, 10, 8)
        hint_lay.setSpacing(3)
        for icon_name, txt in [
            ("wand",   "Zauberstab — Farbfläche auswählen"),
            ("brush",  "Pinsel — Auswahl aufmalen"),
            ("eraser", "Radiergummi — Auswahl entfernen"),
            ("lasso",  "Polygon-Lasso — Punkte klicken, Doppelklick abschließen"),
        ]:
            hint_lay.addWidget(_make_icon_row(icon_name, txt, "#7aacdd", 11))
        hint_lay.addWidget(_make_hdivider())
        sub_mod = "Cmd" if _IS_MACOS else "Ctrl"
        hint_lay.addWidget(_make_label("Shift+Klick  →  Auswahl addieren", "#888", 11))
        hint_lay.addWidget(_make_label(f"{sub_mod}+Klick   →  Auswahl subtrahieren", "#888", 11))
        gt.addWidget(hint_box)
        l1.addWidget(g_tool)

        g_sel, gs = _make_section("Einstellungen", "#4a90d9")
        tolerance_label = _make_label("Toleranz (Zauberstab):  30", "#aaa")
        tolerance_slider = _make_slider(0, 255, 30,
            "Steuert wie ähnlich Farben sein müssen um ausgewählt zu werden.\n"
            "Niedrig = nur sehr ähnliche Farben · Hoch = viele Farbtöne")

        def on_tolerance(value: int) -> None:
            self._actions.set_tolerance(value)
            tolerance_label.setText(f"Toleranz (Zauberstab):  {value}")

        tolerance_slider.valueChanged.connect(on_tolerance)
        gs.addWidget(tolerance_label)
        gs.addWidget(tolerance_slider)
        gs.addWidget(_make_hdivider())

        brush_label = _make_label("Pinselgröße:  30 px", "#aaa")
        brush_slider = _make_slider(4, 200, 30,
            "Größe des Pinsel-/Radiergummi-Werkzeugs in Pixeln")

        def on_brush(value: int) -> None:
            self._actions.set_brush_size(value)
            brush_label.setText(f"Pinselgröße:  {value} px")

        brush_slider.valueChanged.connect(on_brush)
        gs.addWidget(brush_label)
        gs.addWidget(brush_slider)
        l1.addWidget(g_sel)

        btn_clr = _make_panel_btn("Auswahl aufheben", "#2a2a2a", "#c0c0c0", "#363636",
                      "Hebt die aktuelle Auswahl auf (auch: Esc-Taste)",
                      icon_name="clear_sel")
        btn_clr.clicked.connect(lambda _=False: self._actions.clear_selection())
        l1.addWidget(btn_clr)

        btn_inv = _make_panel_btn("Auswahl invertieren", "#2a2a2a", "#c0c0c0", "#363636",
                      "Tauscht aus- und nicht-ausgewählte Bereiche  (⌘⇧I)",
                      icon_name="clear_sel")
        btn_inv.clicked.connect(lambda _=False: self._actions.invert_selection())
        l1.addWidget(btn_inv)

        morph_row = QHBoxLayout(); morph_row.setSpacing(6)
        morph_spin = QSpinBox()
        morph_spin.setRange(1, 20); morph_spin.setValue(2)
        morph_spin.setSuffix(" px")
        morph_spin.setFixedWidth(72)
        morph_spin.setToolTip(
            "Radius in Pixeln für Erweitern/Schrumpfen der Auswahl")
        morph_spin.setStyleSheet(_SPIN_STYLE)
        btn_expand = _make_panel_btn("➕ Erweitern", "#1a3a1a", "#a0d0a0", "#2a5a2a",
                         "Erweitert die Auswahl um den eingestellten Radius")
        btn_expand.clicked.connect(
            lambda _=False: self._actions.expand_selection(morph_spin.value()))
        btn_shrink = _make_panel_btn("➖ Schrumpfen", "#3a1a1a", "#d0a0a0", "#5a2a2a",
                         "Schrumpft die Auswahl um den eingestellten Radius")
        btn_shrink.clicked.connect(
            lambda _=False: self._actions.shrink_selection(morph_spin.value()))
        morph_row.addWidget(morph_spin)
        morph_row.addWidget(btn_expand, 1)
        morph_row.addWidget(btn_shrink, 1)
        l1.addLayout(morph_row)
        l1.addStretch()

        refs.update(
            tolerance_label=tolerance_label,
            tolerance_slider=tolerance_slider,
            brush_label=brush_label,
            brush_slider=brush_slider,
            morph_spin=morph_spin,
        )
        return t1, refs


class BackgroundTab:
    def __init__(self, actions: "RightPanelActions") -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, WidgetRefs]:
        t2, l2 = _make_scroll_tab()
        g_bg, gb = _make_section("Hintergrund bearbeiten", "#e05555")
        btn_rem = _make_panel_btn("Entfernen (transparent)", "#6a1a1a", "white", "#882020",
                      "Macht den ausgewählten Bereich vollständig transparent.\n"
                      "Tipp: Zuerst mit Zauberstab Hintergrund auswählen.",
                      height=38, icon_name="transparency")
        btn_rem.clicked.connect(lambda _=False: self._actions.remove_background())
        gb.addWidget(btn_rem)

        gb.addWidget(_make_hdivider())
        gb.addWidget(_make_label("Farbe wählen und Auswahl einfärben:", "#888"))
        color_row = QHBoxLayout(); color_row.setSpacing(8)
        color_button = QPushButton()
        color_button.setFixedSize(_COLOR_BTN_SIZE, _COLOR_BTN_SIZE)
        color_button.setToolTip("Klicken um Ersatz-Hintergrundfarbe zu wählen")
        color_button.setStyleSheet(
            "QPushButton { border-radius:6px; border:2px solid #555; }"
            "QPushButton:hover { border-color: #4a90d9; }")
        color_button.clicked.connect(lambda _=False: self._actions.pick_color())
        color_row.addWidget(color_button)
        btn_repl = _make_panel_btn("Farbe ersetzen", "#143a5a", "white", "#1e5080",
                       "Füllt den ausgewählten Bereich mit der gewählten Farbe",
                       icon_name="bg")
        btn_repl.clicked.connect(lambda _=False: self._actions.replace_background())
        color_row.addWidget(btn_repl, 1)
        gb.addLayout(color_row)
        l2.addWidget(g_bg)
        l2.addStretch()
        return t2, {"color_button": color_button}


class TransformTab:
    def __init__(self, actions: "RightPanelActions") -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, WidgetRefs]:
        t3, l3 = _make_scroll_tab()
        g_rot, gr2 = _make_section("Drehen", "#e09a30")
        rot_bg = "#2e2510"; rot_fg = "#f0c060"; rot_hv = "#4a3a18"

        gr2.addWidget(_make_label("Schnell-Drehung:", "#888"))
        row_q1 = QHBoxLayout(); row_q1.setSpacing(6)
        for label, deg, tip in [
            ("↺ 90° links",   90,  "90° gegen den Uhrzeigersinn drehen"),
            ("↻ 90° rechts", -90, "90° im Uhrzeigersinn drehen"),
        ]:
            b = _make_panel_btn(label, rot_bg, rot_fg, rot_hv, tip)
            b.clicked.connect(lambda _=False, d=deg: self._actions.rotate(d))
            row_q1.addWidget(b)
        gr2.addLayout(row_q1)

        row_q2 = QHBoxLayout(); row_q2.setSpacing(6)
        for label, deg, tip in [
            ("↺ 180°",  180, "Bild um 180° drehen"),
            ("↺ 270°",  270, "270° gegen den Uhrzeigersinn (= 90° rechts)"),
        ]:
            b = _make_panel_btn(label, rot_bg, rot_fg, rot_hv, tip)
            b.clicked.connect(lambda _=False, d=deg: self._actions.rotate(d))
            row_q2.addWidget(b)
        gr2.addLayout(row_q2)

        gr2.addWidget(_make_hdivider())
        gr2.addWidget(_make_label("Freier Winkel:", "#888"))
        row_free = QHBoxLayout(); row_free.setSpacing(6)
        rotation_slider = QSlider(Qt.Orientation.Horizontal)
        rotation_slider.setRange(-180, 180); rotation_slider.setValue(0)
        rotation_slider.setStyleSheet(SLD_STYLE)
        rotation_slider.setToolTip("Drehwinkel einstellen: −180° bis +180°")
        rotation_spin = QSpinBox()
        rotation_spin.setRange(-180, 180); rotation_spin.setValue(0)
        rotation_spin.setSuffix("°")
        rotation_spin.setFixedWidth(66)
        rotation_spin.setToolTip("Drehwinkel direkt eingeben")
        rotation_spin.setStyleSheet(_SPIN_STYLE)
        rotation_slider.valueChanged.connect(lambda v: rotation_spin.setValue(v))
        rotation_spin.valueChanged.connect(lambda v: rotation_slider.setValue(v))
        row_free.addWidget(rotation_slider, 1)
        row_free.addWidget(rotation_spin)
        gr2.addLayout(row_free)

        btn_rot_free = _make_panel_btn("Winkel anwenden", rot_bg, rot_fg, rot_hv,
                           "Dreht das Bild um den eingestellten Winkel.\n"
                           "Transparente Ecken entstehen bei schrägen Winkeln.",
                           icon_name="undo")
        btn_rot_free.clicked.connect(
            lambda _=False: self._actions.rotate(rotation_spin.value()))
        gr2.addWidget(btn_rot_free)
        l3.addWidget(g_rot)

        g_flip, gf = _make_section("Spiegeln", "#30a0a0")
        row_flip = QHBoxLayout(); row_flip.setSpacing(6)
        btn_fh = _make_panel_btn("Horizontal", "#0e2a2a", "#7adada", "#1a4040",
                     "Bild horizontal spiegeln (links ↔ rechts)")
        btn_fh.clicked.connect(lambda _=False: self._actions.flip(True))
        row_flip.addWidget(btn_fh)
        btn_fv = _make_panel_btn("Vertikal", "#0e2a2a", "#7adada", "#1a4040",
                     "Bild vertikal spiegeln (oben ↕ unten)")
        btn_fv.clicked.connect(lambda _=False: self._actions.flip(False))
        row_flip.addWidget(btn_fv)
        gf.addLayout(row_flip)
        l3.addWidget(g_flip)
        l3.addStretch()
        return t3, {
            "rotation_slider": rotation_slider,
            "rotation_spin": rotation_spin,
        }


class ShapeTab:
    def __init__(self, actions: "RightPanelActions") -> None:
        self._actions = actions

    def build(self) -> tuple[QWidget, WidgetRefs]:
        t4, l4 = _make_scroll_tab()
        g_corner, gc = _make_section("Ecken abrunden", "#30c060")
        corner_label = _make_label("Radius:  0 px", "#aaa")
        corner_slider = _make_slider(0, 500, 0,
            "Radius der Eckenrundung in Pixeln.\n0 = keine Rundung · 500 = maximal rund")
        corner_slider.valueChanged.connect(
            lambda v: corner_label.setText(f"Radius:  {v} px"))
        gc.addWidget(corner_label)
        gc.addWidget(corner_slider)
        btn_corner = _make_panel_btn("Ecken abrunden", "#0e2a14", "#7add9a", "#1a4520",
                         "Wendet die Eckenrundung an.\n"
                         "Das Ergebnis wird als PNG mit transparenten Ecken gespeichert.",
                         height=38, icon_name="form")
        btn_corner.clicked.connect(
            lambda _=False: self._actions.round_corners(corner_slider.value()))
        gc.addWidget(btn_corner)
        l4.addWidget(g_corner)

        g_fmt, gfm = _make_section("Ausgabe-Format & Zuschnitt", "#9060d0")
        info_box = QWidget()
        info_box.setStyleSheet("background:#1e1628; border-radius:7px;")
        info_b = QVBoxLayout(info_box)
        info_b.setContentsMargins(10, 8, 10, 8)
        info_b.addWidget(_make_label(
            "⇲ Format wählen → Rahmen erscheint auf dem Bild\n"
            "• Rahmen verschieben: Mitte ziehen\n"
            "• Größe ändern: Ecken ziehen (Proportionen bleiben)", "#8a7aaa", 10))
        gfm.addWidget(info_box)

        gfm.addWidget(_make_label("Sonderformate:", "#777", 10))
        r_special = QHBoxLayout(); r_special.setSpacing(6)
        for label, tip, slot in [
            ("⬤  Kreis",  "Runden Ausschnitt positionieren und zuschneiden",
             self._actions.start_crop_circle),
            ("■  1 : 1", "Quadratischen Ausschnitt positionieren",
             lambda: self._actions.start_crop_ratio(1, 1)),
        ]:
            b = _make_panel_btn(label, "#141e38", "#8aaedd", "#1e2e52", tip)
            b.clicked.connect(lambda _=False, fn=slot: fn())
            r_special.addWidget(b)
        gfm.addLayout(r_special)

        gfm.addWidget(_make_hdivider())
        gfm.addWidget(_make_label("Querformat:", "#777", 10))
        land_formats = [
            ("16 : 9", 16, 9), ("4 : 3",  4, 3),
            ("3 : 2",  3, 2),  ("2 : 1",  2, 1),
            ("7 : 4.5", 14, 9),
        ]
        for i in range(0, len(land_formats), 2):
            row_fmt = QHBoxLayout(); row_fmt.setSpacing(6)
            for label, rw, rh in land_formats[i:i+2]:
                b = _make_panel_btn(f"▬  {label}", "#1e1428", "#c0a0f0", "#2e1e44",
                        f"Querformat {label} — Ecken ziehen für Größe, Mitte zum Verschieben")
                b.clicked.connect(
                    lambda _=False, w=rw, h=rh: self._actions.start_crop_ratio(w, h))
                row_fmt.addWidget(b)
            gfm.addLayout(row_fmt)

        gfm.addWidget(_make_hdivider())
        gfm.addWidget(_make_label("Hochformat:", "#777", 10))
        port_formats = [("9 : 16", 9, 16), ("3 : 4", 3, 4)]
        row_port = QHBoxLayout(); row_port.setSpacing(6)
        for label, rw, rh in port_formats:
            b = _make_panel_btn(f"▮  {label}", "#141e28", "#90c8cc", "#1e2e38",
                    f"Hochformat {label} — Ecken ziehen für Größe, Mitte zum Verschieben")
            b.clicked.connect(
                lambda _=False, w=rw, h=rh: self._actions.start_crop_ratio(w, h))
            row_port.addWidget(b)
        gfm.addLayout(row_port)
        l4.addWidget(g_fmt)
        l4.addStretch()
        return t4, {
            "corner_label": corner_label,
            "corner_slider": corner_slider,
        }
