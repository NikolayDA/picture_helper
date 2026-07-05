"""Tests for the right-side panel builder without constructing MainWindow."""
from __future__ import annotations

import numpy as np
import pytest
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QWidget,
)

from bgremover import height_ops
from bgremover.canvas import LayerInfo
from bgremover.height_map import HeightField
from bgremover.height_map_panel import HeightMapActions, HeightMapPanel
from bgremover.layer_panel import LayerPanel, LayerPanelActions
from bgremover.preview_mode import PreviewMode
from bgremover.project_model import LayerKind, LayerRole
from bgremover.right_panel import RightPanelActions, build_right_panel
from bgremover.stepper import WorkflowStep


def _button(panel_frame, text: str) -> QPushButton:
    for button in panel_frame.findChildren(QPushButton):
        # Manche Primär-/EufyMake-Buttons brechen bei 332 px Panelbreite
        # fontmetrisch um (§5.3-Ausnahme); der Vergleich ist umbruch-tolerant.
        if button.text().replace("\n", " ") == text:
            return button
    raise AssertionError(f"QPushButton {text!r} nicht gefunden")


def _noop_height_actions() -> HeightMapActions:
    return HeightMapActions(
        generate=lambda: None,
        import_file=lambda: None,
        lighten=lambda _a: None,
        darken=lambda _a: None,
        set_height=lambda _v: None,
        invert=lambda: None,
        preview_op=lambda _op: None,
        apply_op=lambda _op: None,
        cancel_preview=lambda: None,
    )


def _noop_layer_actions() -> LayerPanelActions:
    return LayerPanelActions(
        add_layer=lambda: None,
        delete_active=lambda: None,
        duplicate_active=lambda: None,
        move_active_up=lambda: None,
        move_active_down=lambda: None,
        rename_active=lambda: None,
        set_active=lambda _lid: None,
        set_visible=lambda _lid, _v: None,
        set_opacity=lambda _lid, _o: None,
        set_active_role=lambda _r: None,
    )


def _actions(calls: list[tuple]) -> RightPanelActions:
    return RightPanelActions(
        set_tolerance=lambda value: calls.append(("tolerance", value)),
        set_brush_size=lambda value: calls.append(("brush", value)),
        clear_selection=lambda: calls.append(("clear",)),
        invert_selection=lambda: calls.append(("invert",)),
        expand_selection=lambda value: calls.append(("expand", value)),
        shrink_selection=lambda value: calls.append(("shrink", value)),
        remove_background=lambda: calls.append(("remove",)),
        pick_color=lambda: calls.append(("pick_color",)),
        replace_background=lambda: calls.append(("replace",)),
        feather=lambda value: calls.append(("feather", value)),
        rotate=lambda value: calls.append(("rotate", value)),
        flip=lambda horizontal: calls.append(("flip", horizontal)),
        resize=lambda: calls.append(("resize",)),
        round_corners=lambda value: calls.append(("round", value)),
        start_crop_circle=lambda: calls.append(("crop_circle",)),
        start_crop_ratio=lambda w, h: calls.append(("crop_ratio", w, h)),
        preview_color=lambda op: calls.append(("preview_color",)),
        apply_color=lambda op: calls.append(("apply_color",)),
        cancel_color_preview=lambda: calls.append(("cancel_color",)),
        set_preview_mode=lambda mode: calls.append(("preview_mode", mode)),
        set_relief_strength=lambda value: calls.append(("relief_strength", value)),
        set_gloss_visible=lambda visible: calls.append(("gloss_visible", visible)),
        run_ai=lambda: calls.append(("run_ai",)),
        apply_resize=lambda w, h: calls.append(("apply_resize", w, h)),
        save=lambda: calls.append(("save",)),
        export_eufymake=lambda: calls.append(("export_eufymake",)),
        set_save_format=lambda fmt: calls.append(("save_format", fmt)),
    )


def test_right_panel_builder_creates_stepped_pages(qapp):
    """Der Inspector ist ein 6-Schritte-Stack mit Kopf + Navigation (Epic #418)."""
    from PyQt6.QtWidgets import QStackedWidget

    panel = build_right_panel(_actions([]), _noop_layer_actions(), _noop_height_actions())

    assert isinstance(panel.stack, QStackedWidget)
    assert panel.stack.count() == 6

    # Start: Schritt 1 (Öffnen) – Zurück deaktiviert, Weiter nennt das nächste Ziel.
    assert panel.stack.currentIndex() == 0
    assert not panel.nav_prev.isEnabled()
    assert panel.nav_next.text() == "Weiter: Freistellen →"

    # Schritt wechseln: Stack, Kopf und Weiter-Beschriftung folgen.
    panel.set_step(WorkflowStep.CUTOUT)
    assert panel.stack.currentIndex() == 1
    assert panel.step_title.text() == "Schritt 2 · Freistellen"
    assert panel.nav_next.text() == "Weiter: Anpassen →"
    assert panel.nav_prev.isEnabled()

    panel.set_step(WorkflowStep.EXPORT)
    assert panel.nav_next.text() == "Exportieren ✓"


def test_step_pages_single_scroll(qapp):
    """Kein Doppel-Scroll: Tab-Inhalte scrollen nicht selbst; eine Ein-Tab-Seite
    hat genau einen Scrollbereich (#440)."""
    from unittest.mock import MagicMock

    from PyQt6.QtWidgets import QScrollArea

    from bgremover.right_panel_tabs import SelectionTab, ShapeTab

    for tab_cls in (SelectionTab, ShapeTab):
        widget, _refs = tab_cls(MagicMock()).build()
        assert widget.findChildren(QScrollArea) == []

    panel = build_right_panel(
        _actions([]), _noop_layer_actions(), _noop_height_actions())
    adjust_page = panel.stack.widget(int(WorkflowStep.ADJUST) - 1)
    assert len(adjust_page.findChildren(QScrollArea)) == 1


def test_step2_ai_and_step6_save_export_delegate(qapp):
    """KI-Button (S2) und Speichern/Format/EufyMake (S6) rufen ihre Callbacks (§9)."""
    calls: list[tuple] = []
    panel = build_right_panel(
        _actions(calls), _noop_layer_actions(), _noop_height_actions())

    _button(panel.frame, "Hintergrund automatisch entfernen (KI)").click()
    _button(panel.frame, "JPEG").click()
    _button(panel.frame, "Bild speichern").click()
    _button(panel.frame, "Assets für EufyMake Studio exportieren…").click()

    assert ("run_ai",) in calls
    assert ("save_format", "JPEG") in calls
    assert ("save",) in calls
    assert ("export_eufymake",) in calls


def test_step2_ai_button_respects_rembg_availability(qapp):
    """#446: Der Inspector-KI-Button ist ohne rembg wie die Toolbar gesperrt."""
    panel = build_right_panel(
        _actions([]), _noop_layer_actions(), _noop_height_actions(),
        rembg_available=False)

    ai_button = _button(panel.frame, "Hintergrund automatisch entfernen (KI)")
    assert ai_button is panel.ai_button
    assert not ai_button.isEnabled()
    assert "rembg" in ai_button.toolTip()


def test_open_step_recent_card_delegates(qapp, tmp_path):
    """Die Karte „Zuletzt geöffnet" öffnet den geklickten Eintrag (§9 Schritt 1)."""
    opened: list[str] = []
    a, b = str(tmp_path / "a.png"), str(tmp_path / "b.jpg")
    panel = build_right_panel(
        _actions([]), _noop_layer_actions(), _noop_height_actions(),
        recent=[a, b], on_open_path=lambda p: opened.append(p))

    _button(panel.frame, "a.png").click()
    assert opened == [a]


def test_open_step_recent_rows_show_prototype_thumbnail_and_text(qapp, tmp_path):
    """Step 1 übernimmt die Prototyp-Zeile mit 30px-Vorschau links."""
    from bgremover.theme import DARK, set_active_palette

    set_active_palette(DARK)
    p = tmp_path / "motiv.png"
    pix = QPixmap(8, 8)
    pix.fill(QColor("#8ab4ff"))
    assert pix.save(str(p))

    panel = build_right_panel(
        _actions([]), _noop_layer_actions(), _noop_height_actions(),
        recent=[str(p)], on_open_path=lambda _p: None)

    row = _button(panel.frame, "motiv.png")
    assert not row.icon().isNull()
    assert row.iconSize().width() == 30
    assert row.iconSize().height() == 30
    assert DARK.text2 in row.styleSheet()
    assert "padding:9px 8px" in row.styleSheet()


def test_open_step_recent_card_uses_prototype_background(qapp, tmp_path):
    """Die ganze „Zuletzt geöffnet"-Kachel nutzt den Prototyp-Kartenton."""
    from bgremover.theme import DARK, set_active_palette

    set_active_palette(DARK)
    p = str(tmp_path / "a.png")
    panel = build_right_panel(
        _actions([]), _noop_layer_actions(), _noop_height_actions(),
        recent=[p], on_open_path=lambda _p: None)

    card = panel.frame.findChild(QFrame, "recentCard")
    assert card is not None
    assert "#2e353f" in card.styleSheet()


def test_section_headers_use_single_blue_accent_and_are_cards(qapp):
    """Alle Sektionsköpfe nutzen dasselbe Blau; jede Sektion ist eine Karte (#415/#416)."""
    # Live-Vertrag gegen die aktuelle Palette prüfen, nicht gegen die
    # eingefrorene ``_Theme.ACCENT``-Rückwärtskompat-Konstante (#477 hellt
    # ``DARK.accent`` gegenüber dem alten Snapshot auf).
    from bgremover.theme import DARK, set_active_palette

    set_active_palette(DARK)

    panel = build_right_panel(
        _actions([]), _noop_layer_actions(), _noop_height_actions())

    headers = [
        lbl for lbl in panel.frame.findChildren(QLabel)
        if "border-left" in lbl.styleSheet()
    ]
    assert headers, "keine Sektionsköpfe gefunden"
    removed = (
        "#e05555", "#e09a30", "#9060d0", "#c08adf",
        "#65a9e8", "#d07ac0", "#30c060", "#30a0a0",
    )
    for lbl in headers:
        style = lbl.styleSheet()
        assert DARK.accent in style, style
        for old in removed:
            assert old not in style, f"Alt-Akzent {old} noch vorhanden"

    cards = [
        f for f in panel.frame.findChildren(QFrame)
        if f.objectName() == "sectionCard"
    ]
    assert cards, "keine Karten-Sektionen gefunden"
    for card in cards:
        assert DARK.card_bg in card.styleSheet()


def test_right_panel_sliders_use_prototype_range_style(qapp):
    """Alle Slider der rechten Spalte nutzen den Prototyp-Range-Look (§5.5)."""
    from bgremover.theme import DARK, set_active_palette

    set_active_palette(DARK)
    panel = build_right_panel(
        _actions([]), _noop_layer_actions(), _noop_height_actions())

    sliders = panel.frame.findChildren(QSlider)
    assert sliders, "keine Slider in der rechten Spalte gefunden"
    for slider in sliders:
        style = slider.styleSheet()
        assert "QSlider { margin: 9px 0 2px 0; min-height: 22px; }" in style
        assert "QSlider::sub-page:horizontal" in style
        assert f"background: {DARK.accent}" in style
        assert "QSlider::add-page:horizontal" in style
        assert "background: #e6e6e6" in style
        assert "border: 1px solid #ffffff" in style
        assert f"background: {DARK.on_accent}" in style
        assert "width: 16px" in style
        assert "height: 16px" in style


def test_step2_and_step4_option_spacing_is_uniform(qapp):
    """Optionszeilen in Schritt 2/4 nutzen denselben horizontalen Abstand."""
    from bgremover.right_panel_tabs import _OPTION_SPACING

    panel = build_right_panel(
        _actions([]), _noop_layer_actions(), _noop_height_actions())
    for name in ("selectionActionRow", "selectionMorphRow"):
        row = panel.frame.findChild(QHBoxLayout, name)
        assert row is not None
        assert row.spacing() == _OPTION_SPACING

    grid = panel.frame.findChild(QGridLayout, "shapeFormatGrid")
    assert grid is not None
    assert grid.horizontalSpacing() == _OPTION_SPACING
    assert grid.verticalSpacing() == _OPTION_SPACING


def test_step2_and_step4_card_spacing_is_uniform_across_blocks(qapp):
    """Kombinierte Schrittinhalte stapeln keine Spacer/Außenabstände."""
    from bgremover.right_panel_tabs import (
        _CARD_STACK_BOTTOM_MARGIN,
        _CARD_STACK_SPACING,
        _CARD_STACK_TOP_MARGIN,
    )

    panel = build_right_panel(
        _actions([]), _noop_layer_actions(), _noop_height_actions())
    for step in (WorkflowStep.CUTOUT, WorkflowStep.SHAPE):
        page = panel.stack.widget(int(step) - 1)
        scroll = page.findChild(QScrollArea)
        assert scroll is not None
        container = scroll.widget()
        assert container is not None
        layout = container.layout()
        assert layout is not None
        blocks = [
            item.widget()
            for index in range(layout.count())
            if (item := layout.itemAt(index)).widget() is not None
        ]
        assert len(blocks) == 2
        first = blocks[0].layout()
        second = blocks[1].layout()
        assert first is not None
        assert second is not None
        first_margins = first.getContentsMargins()
        second_margins = second.getContentsMargins()
        assert first.itemAt(first.count() - 1).spacerItem() is None
        assert second.itemAt(second.count() - 1).spacerItem() is None
        assert first_margins[1] == _CARD_STACK_TOP_MARGIN
        assert first_margins[3] == 0
        assert second_margins[1] == _CARD_STACK_SPACING
        assert second_margins[3] == _CARD_STACK_BOTTOM_MARGIN


@pytest.mark.ui_smoke
def test_panel_buttons_not_clipped_at_min_width(qapp):
    """Kein Button schneidet seinen Text bei Mindestfensterbreite ab (#417)."""
    from PyQt6.QtGui import QFontMetrics
    from PyQt6.QtWidgets import QMainWindow, QPushButton

    from bgremover.constants import _WINDOW_MIN_H, _WINDOW_MIN_W

    panel = build_right_panel(
        _actions([]), _noop_layer_actions(), _noop_height_actions())
    win = QMainWindow()
    win.setCentralWidget(panel.frame)
    win.resize(_WINDOW_MIN_W, _WINDOW_MIN_H)
    win.show()
    qapp.processEvents()
    try:
        for step in WorkflowStep:
            panel.set_step(step)
            qapp.processEvents()
            for button in panel.frame.findChildren(QPushButton):
                if not button.isVisible() or not button.text().strip():
                    continue
                fm = QFontMetrics(button.font())
                # Mnemonic-Escaping ("&&" -> gerendertes "&", §11-Labels wie
                # „Relief & Ebenen") und bewusst umgebrochene Buttons (§5.3-
                # Ausnahme, z. B. der KI-/EufyMake-Button) sind kein Clipping:
                # jede *gerenderte* Zeile muss passen, nicht der Rohtext am Stück.
                lines = button.text().replace("&&", "&").split("\n")
                needed = max(fm.horizontalAdvance(line) for line in lines)
                # Der reine Text muss in die Button-Box passen (echte Clipping-
                # Bedingung; Innenabstand zentriert lediglich).
                assert needed <= button.width(), (
                    step.name, button.text(), needed, button.width())
    finally:
        win.hide()


def test_open_step_drop_frame_forwards_image_path(qapp, tmp_path):
    """Das Ablagefeld in Schritt 1 leitet abgelegte Bildpfade weiter (PR #423)."""
    from PyQt6.QtCore import QMimeData, QUrl

    from bgremover.right_panel import _DropFrame

    dropped: list[str] = []
    frame = _DropFrame(on_open=None, on_open_path=lambda p: dropped.append(p))
    assert frame.acceptDrops() is True

    class _Evt:
        def __init__(self, mime: QMimeData) -> None:
            self._mime = mime

        def mimeData(self) -> QMimeData:
            return self._mime

        def acceptProposedAction(self) -> None:
            pass

    png = QMimeData()
    png.setUrls([QUrl.fromLocalFile(str(tmp_path / "motiv.png"))])
    frame.dropEvent(_Evt(png))  # type: ignore[arg-type]
    assert dropped == [str(tmp_path / "motiv.png")]

    # Nicht-Bild-Ablage wird ignoriert.
    txt = QMimeData()
    txt.setUrls([QUrl.fromLocalFile(str(tmp_path / "notiz.txt"))])
    frame.dropEvent(_Evt(txt))  # type: ignore[arg-type]
    assert dropped == [str(tmp_path / "motiv.png")]


def test_right_panel_controls_delegate_to_callbacks(qapp):
    calls: list[tuple] = []
    panel = build_right_panel(_actions(calls), _noop_layer_actions(), _noop_height_actions())

    _button(panel.frame, "Relief").click()
    panel.preview_relief_slider.setValue(35)
    panel.preview_gloss_visible.setChecked(False)
    panel.tolerance_slider.setValue(42)
    panel.brush_slider.setValue(55)
    panel.morph_spin.setValue(5)
    # "Invertieren" existiert wortgleich auch in der Höhenkarten-Karte (§9 Schritt
    # 5) - Suche hier gezielt in der Freistellen-Seite (Schritt 2), um die
    # Selektions- statt der Höhen-Variante zu treffen.
    cutout_page = panel.stack.widget(int(WorkflowStep.CUTOUT) - 1)
    _button(cutout_page, "Aufheben").click()
    _button(cutout_page, "Invertieren").click()
    _button(cutout_page, "+ Erweitern").click()
    _button(cutout_page, "− Schrumpfen").click()
    _button(panel.frame, "Entfernen (transparent)").click()
    panel.color_button.click()
    _button(panel.frame, "Farbe ersetzen").click()
    _button(panel.frame, "Kante glätten").click()

    _button(panel.frame, "↺ 90° links").click()
    _button(panel.frame, "↻ 90° rechts").click()
    panel.rotation_spin.setValue(33)
    _button(panel.frame, "↺ Winkel anwenden").click()
    _button(panel.frame, "Horizontal").click()
    _button(panel.frame, "Vertikal").click()
    _button(panel.frame, "Größe anwenden").click()

    panel.corner_slider.setValue(12)
    _button(panel.frame, "Ecken abrunden").click()
    _button(panel.frame, "⬤  Kreis").click()
    _button(panel.frame, "1:1").click()
    _button(panel.frame, "16:9").click()
    _button(panel.frame, "9:16").click()

    assert calls == [
        ("preview_mode", PreviewMode.RELIEF),
        ("relief_strength", 35),
        ("gloss_visible", False),
        ("tolerance", 42),
        ("brush", 55),
        ("clear",),
        ("invert",),
        ("expand", 5),
        ("shrink", 5),
        ("remove",),
        ("pick_color",),
        ("replace",),
        ("feather", 2),
        ("rotate", 90),
        ("rotate", -90),
        ("rotate", 33),
        ("flip", True),
        ("flip", False),
        ("apply_resize", 1200, 900),
        ("round", 12),
        ("crop_circle",),
        ("crop_ratio", 1, 1),
        ("crop_ratio", 16, 9),
        ("crop_ratio", 9, 16),
    ]


@pytest.mark.ui_smoke
def test_preview_tab_controls_and_export_hint(qapp) -> None:
    from bgremover.right_panel_tabs import PreviewTab

    calls: list[tuple] = []
    _widget, refs = PreviewTab(_actions(calls)).build()
    segments = refs["preview_mode_segments"]
    slider = refs["preview_relief_slider"]
    gloss = refs["preview_gloss_visible"]

    _button(_widget, "Relief").click()
    slider.setValue(15)
    gloss.setChecked(False)

    assert calls == [
        ("preview_mode", PreviewMode.RELIEF),
        ("relief_strength", 15),
        ("gloss_visible", False),
    ]
    assert segments.current_mode() is PreviewMode.RELIEF
    assert "Bild speichern" in refs["preview_export_hint"].text()


# ── Kantenglättung / Feather (#361) ───────────────────────────────────────


@pytest.mark.ui_smoke
def test_background_tab_feather_button_delegates_radius(qapp):
    from bgremover.right_panel_tabs import BackgroundTab

    calls: list[tuple] = []
    _widget, refs = BackgroundTab(_actions(calls)).build()

    refs["feather_slider"].setValue(5)
    assert "5 px" in refs["feather_label"].text()
    refs["feather_button"].click()
    assert calls == [("feather", 5)]


def test_prototype_image_icon_used_for_affected_inspector_tiles(qapp):
    """Die betroffenen Prototyp-Kacheln nutzen das neue Bild-SVG statt Alt-Icons."""
    panel = build_right_panel(
        _actions([]), _noop_layer_actions(), _noop_height_actions())

    for text in (
        "Entfernen (transparent)",
        "Farbe ersetzen",
        "Kante glätten",
        "Ecken abrunden",
        "Graustufe importieren…",
    ):
        button = _button(panel.frame, text)
        assert button.property("prototypeIconName") == "prototype_image"
        assert not button.icon().isNull()
        assert button.iconSize().width() == 14
        assert button.iconSize().height() == 14

    generate = _button(panel.frame, "Aus Bild erzeugen")
    assert generate.property("prototypeIconName") is None
    assert generate.icon().isNull()

    rotate_apply = _button(panel.frame, "↺ Winkel anwenden")
    assert rotate_apply.property("prototypeIconName") is None
    assert rotate_apply.icon().isNull()


# ── Anpassen-Tab / Farbkorrektur (#360) ───────────────────────────────────


@pytest.mark.ui_smoke
def test_adjust_tab_sliders_drive_preview_apply_reset(qapp):
    from bgremover.right_panel_tabs import AdjustTab

    calls: list[tuple] = []
    _widget, refs = AdjustTab(_actions(calls)).build()

    # Reglerbewegung → Live-Vorschau
    refs["adjust_brightness"].setValue(150)
    refs["adjust_contrast"].setValue(120)
    refs["adjust_saturation"].setValue(0)
    assert calls.count(("preview_color",)) == 3

    refs["adjust_apply"].click()
    assert ("apply_color",) in calls

    # Zurücksetzen: Regler auf 100 % + Vorschau verwerfen (ohne neue Preview-Spam).
    calls.clear()
    refs["adjust_reset"].click()
    assert refs["adjust_brightness"].value() == 100
    assert refs["adjust_contrast"].value() == 100
    assert refs["adjust_saturation"].value() == 100
    assert calls == [("cancel_color",)]


# ── Ebenen-Panel (#334) ──────────────────────────────────────────────────


def _recording_layer_actions(calls: list[tuple]) -> LayerPanelActions:
    return LayerPanelActions(
        add_layer=lambda: calls.append(("add",)),
        delete_active=lambda: calls.append(("delete",)),
        duplicate_active=lambda: calls.append(("duplicate",)),
        move_active_up=lambda: calls.append(("up",)),
        move_active_down=lambda: calls.append(("down",)),
        rename_active=lambda: calls.append(("rename",)),
        set_active=lambda lid: calls.append(("active", lid)),
        set_visible=lambda lid, v: calls.append(("visible", lid, v)),
        set_opacity=lambda lid, o: calls.append(("opacity", lid, o)),
        set_active_role=lambda r: calls.append(("role", r)),
    )


def _infos() -> list[LayerInfo]:
    return [
        LayerInfo(id="top", name="Oben", kind=LayerKind.COLOR, visible=True,
                  opacity=1.0, locked=False, role=None, active=True),
        LayerInfo(id="bot", name="Unten", kind=LayerKind.COLOR, visible=True,
                  opacity=0.5, locked=False, role=LayerRole.COLOR_MOTIF, active=False),
    ]


def _row_for(widget: QWidget, name: str) -> QWidget:
    name_btn = next(
        b for b in widget.findChildren(QPushButton) if b.text() == name)
    parent = name_btn.parent()
    assert isinstance(parent, QWidget)
    return parent


@pytest.mark.ui_smoke
def test_layer_panel_action_bar_delegates(qapp):
    calls: list[tuple] = []
    panel = LayerPanel(_recording_layer_actions(calls))
    widget, _refs = panel.build()
    panel.refresh(_infos())

    for icon_name, expected in (
        ("layer_add", "add"),
        ("layer_duplicate", "duplicate"),
        ("layer_delete", "delete"),
        ("layer_move_up", "up"),
        ("layer_move_down", "down"),
        ("layer_rename", "rename"),
    ):
        button = next(
            b for b in widget.findChildren(QPushButton)
            if b.property("prototypeIconName") == icon_name)
        button.click()
        assert calls[-1] == (expected,)


@pytest.mark.ui_smoke
def test_layer_panel_rows_reflect_and_delegate(qapp):
    calls: list[tuple] = []
    panel = LayerPanel(_recording_layer_actions(calls))
    widget, _refs = panel.build()
    panel.refresh(_infos())

    # Genau zwei Zeilen (oberste zuerst).
    assert [b.text() for b in widget.findChildren(QPushButton)
            if b.text() in ("Oben", "Unten")] == ["Oben", "Unten"]

    # Klick auf Namen wählt die aktive Ebene.
    next(b for b in widget.findChildren(QPushButton)
         if b.text() == "Unten").click()
    assert ("active", "bot") in calls

    # Sichtbarkeit der unteren Ebene umschalten.
    bot_row = _row_for(widget, "Unten")
    vis = next(
        b for b in bot_row.findChildren(QPushButton)
        if b.property("prototypeIconName") == "layer_visible")
    vis.setChecked(False)
    assert ("visible", "bot", False) in calls

    # Opazität der unteren Ebene anpassen (beim Loslassen übernommen).
    slider = bot_row.findChild(QSlider)
    assert slider is not None
    slider.setValue(25)
    slider.sliderReleased.emit()
    assert ("opacity", "bot", pytest.approx(0.25)) in calls


def test_layer_panel_opacity_slider_uses_prototype_range_style(qapp):
    from bgremover.theme import DARK, set_active_palette

    set_active_palette(DARK)
    panel = LayerPanel(_recording_layer_actions([]))
    widget, _refs = panel.build()
    panel.refresh(_infos())

    slider = widget.findChild(QSlider)
    assert slider is not None
    style = slider.styleSheet()
    assert "QSlider::sub-page:horizontal" in style
    assert f"background: {DARK.accent}" in style
    assert "QSlider::add-page:horizontal" in style
    assert "background: #e6e6e6" in style
    assert "border: 1px solid #ffffff" in style
    assert f"background: {DARK.on_accent}" in style


@pytest.mark.ui_smoke
def test_layer_panel_role_combo_reflects_active_and_delegates(qapp):
    calls: list[tuple] = []
    panel = LayerPanel(_recording_layer_actions(calls))
    widget, refs = panel.build()
    panel.refresh(_infos())

    combo = refs["layer_role_combo"]
    assert isinstance(combo, QComboBox)
    # Aktive Ebene „Oben" hat keine Rolle → Index 0 (Keine).
    assert combo.currentData() is None

    # Typverträgliche Rolle (COLOR_MOTIF, Index 1) wird delegiert.
    combo.setCurrentIndex(1)
    assert ("role", LayerRole.COLOR_MOTIF) in calls


def _role_item_enabled(combo: QComboBox, index: int) -> bool:
    model = combo.model()
    item = model.item(index)            # QStandardItemModel der QComboBox
    return item is not None and item.isEnabled()


@pytest.mark.ui_smoke
def test_layer_panel_role_combo_restricts_height_map_to_height(qapp):
    """HEIGHT_MAP (Index 2) ist nur für eine aktive HEIGHT-Ebene wählbar (#364)."""
    panel = LayerPanel(_noop_layer_actions())
    _widget, refs = panel.build()
    combo = refs["layer_role_combo"]
    assert isinstance(combo, QComboBox)

    # Aktive COLOR-Ebene: HEIGHT_MAP gesperrt, übrige Optionen offen.
    panel.refresh(_infos())
    assert not _role_item_enabled(combo, 2)         # Height Map
    assert _role_item_enabled(combo, 0)             # Keine
    assert _role_item_enabled(combo, 1)             # Farbmotiv

    # Aktive HEIGHT-Ebene: HEIGHT_MAP wählbar.
    height = [LayerInfo(id="h", name="Höhe", kind=LayerKind.HEIGHT, visible=True,
                        opacity=1.0, locked=False, role=None, active=True)]
    panel.refresh(height)
    assert _role_item_enabled(combo, 2)


@pytest.mark.ui_smoke
def test_layer_panel_empty_state_disables_actions(qapp):
    panel = LayerPanel(_noop_layer_actions())
    widget, _refs = panel.build()
    panel.refresh([])

    add = next(
        b for b in widget.findChildren(QPushButton)
        if b.property("prototypeIconName") == "layer_add")
    assert not add.isEnabled()


def test_layer_panel_action_bar_uses_prototype_icon_buttons(qapp):
    panel = LayerPanel(_noop_layer_actions())
    widget, _refs = panel.build()

    buttons = [
        b for b in widget.findChildren(QPushButton)
        if b.objectName() == "layerActionButton"
    ]
    assert [b.property("prototypeIconName") for b in buttons] == [
        "layer_add",
        "layer_duplicate",
        "layer_delete",
        "layer_move_up",
        "layer_move_down",
        "layer_rename",
    ]
    for button in buttons:
        assert button.text() == ""
        assert not button.icon().isNull()
        assert button.width() == 32
        assert button.height() == 30


# ── Height-Map-Panel (#349) ──────────────────────────────────────────────


def _recording_height_actions(calls: list[tuple]) -> HeightMapActions:
    return HeightMapActions(
        generate=lambda: calls.append(("generate",)),
        import_file=lambda: calls.append(("import",)),
        lighten=lambda a: calls.append(("lighten", a)),
        darken=lambda a: calls.append(("darken", a)),
        set_height=lambda v: calls.append(("set", v)),
        invert=lambda: calls.append(("invert",)),
        preview_op=lambda op: calls.append(("preview", op)),
        apply_op=lambda op: calls.append(("apply", op)),
        cancel_preview=lambda: calls.append(("cancel",)),
    )


def _height_layers(*, active_kind: LayerKind = LayerKind.HEIGHT) -> list[LayerInfo]:
    return [
        LayerInfo(id="h", name="Höhenkarte", kind=active_kind, visible=True,
                  opacity=1.0, locked=False, role=LayerRole.HEIGHT_MAP, active=True),
    ]


@pytest.mark.ui_smoke
def test_height_panel_acquire_and_edit_delegate(qapp):
    calls: list[tuple] = []
    panel = HeightMapPanel(_recording_height_actions(calls))
    widget, _refs = panel.build()
    panel.refresh(_height_layers())

    _button(widget, "Aus Bild erzeugen").click()
    _button(widget, "Graustufe importieren…").click()
    _button(widget, "Aufhellen").click()
    _button(widget, "Abdunkeln").click()
    _button(widget, "Höhe setzen").click()
    _button(widget, "Invertieren").click()

    assert calls == [
        ("generate",), ("import",),
        ("lighten", 32), ("darken", 32),   # Standard-Stärke aus dem Spin
        ("set", 128), ("invert",),
    ]


@pytest.mark.ui_smoke
def test_height_panel_optimize_preview_and_apply(qapp):
    calls: list[tuple] = []
    panel = HeightMapPanel(_recording_height_actions(calls))
    _widget, refs = panel.build()
    panel.refresh(_height_layers())

    # Reglerbewegung erzeugt eine Live-Vorschau …
    gamma = refs["height_gamma"]
    assert isinstance(gamma, QSpinBox)
    gamma.setValue(200)
    assert calls[-1][0] == "preview"

    # … und „Anwenden" committet dieselbe Operation. Die übergebene Closure
    # wendet height_ops.gamma(·, 2.0) an – an einem Probefeld verifiziert.
    refs["height_apply_gamma"].click()
    assert calls[-1][0] == "apply"
    op = calls[-1][1]
    field = HeightField(
        np.array([[0, 51, 255]], dtype=np.uint16),
        np.full((1, 3), 255, dtype=np.uint8))
    assert list(op(field).values[0]) == [0, 10, 255]   # (51/255)^2*255 → 10


@pytest.mark.ui_smoke
def test_height_panel_optimize_ops_wire_correct_functions(qapp):
    """Jede „Anwenden"-Schaltfläche reicht die passende height_ops-Operation
    mit den aktuellen Reglerwerten durch (am Probefeld gegen die Direktaufrufe
    verifiziert)."""
    calls: list[tuple] = []
    panel = HeightMapPanel(_recording_height_actions(calls))
    _widget, refs = panel.build()
    panel.refresh(_height_layers())
    field = HeightField(
        np.array([[0, 64, 130, 200, 255]], dtype=np.uint16),
        np.full((1, 5), 255, dtype=np.uint8))

    def captured(key: str):
        refs[f"height_apply_{key}"].click()
        assert calls[-1][0] == "apply"
        return calls[-1][1]

    refs["height_levels_black"].setValue(32)
    refs["height_levels_white"].setValue(200)
    assert np.array_equal(captured("levels")(field).values,
                          height_ops.levels(field, 32, 200).values)
    refs["height_gamma"].setValue(180)
    assert np.array_equal(captured("gamma")(field).values,
                          height_ops.gamma(field, 1.8).values)
    refs["height_gauss"].setValue(3)
    assert np.array_equal(captured("gauss")(field).values,
                          height_ops.gaussian_blur(field, 3.0).values)
    refs["height_median"].setValue(2)
    assert np.array_equal(captured("median")(field).values,
                          height_ops.median_blur(field, 2).values)
    refs["height_threshold"].setValue(100)
    assert np.array_equal(captured("threshold")(field).values,
                          height_ops.threshold(field, 100).values)
    refs["height_steps"].setValue(5)
    assert np.array_equal(captured("steps")(field).values,
                          height_ops.quantize(field, 5).values)
    refs["height_range_lo"].setValue(50)
    refs["height_range_hi"].setValue(180)
    assert np.array_equal(captured("range")(field).values,
                          height_ops.clamp_range(field, 50, 180).values)


@pytest.mark.ui_smoke
def test_height_panel_is_mode_contextual(qapp):
    panel = HeightMapPanel(_noop_height_actions())
    widget, _refs = panel.build()

    # COLOR aktiv: Beschaffen aktiv, Bearbeiten/Optimieren gesperrt.
    color = [LayerInfo(id="c", name="Farbe", kind=LayerKind.COLOR, visible=True,
                       opacity=1.0, locked=False, role=None, active=True)]
    panel.refresh(color)
    assert _button(widget, "Aus Bild erzeugen").isEnabled()
    assert not _button(widget, "Aufhellen").isEnabled()
    assert not _button(widget, "Invertieren").isEnabled()

    # HEIGHT aktiv: Höhenwerkzeuge frei.
    panel.refresh(_height_layers())
    assert _button(widget, "Aufhellen").isEnabled()
    assert _button(widget, "Invertieren").isEnabled()

    # Rolle HEIGHT_MAP allein genügt NICHT mehr: eine COLOR-Ebene mit der Rolle
    # bleibt für Höhenwerkzeuge gesperrt (Vertrag #364 – nur Kind entscheidet).
    panel.refresh(_height_layers(active_kind=LayerKind.COLOR))
    assert not _button(widget, "Aufhellen").isEnabled()
    assert not _button(widget, "Invertieren").isEnabled()

    # Kein Projekt: alles gesperrt.
    panel.refresh([])
    assert not _button(widget, "Aus Bild erzeugen").isEnabled()
    assert not _button(widget, "Aufhellen").isEnabled()


# ── A11y: Fokuszustände, Trefferflächen, Tastaturpfade (#441) ─────────────


def _full_panel(calls: list[tuple], opened: list[bool] | None = None):
    """Panel mit Öffnen-Seite (Ablagefeld + Recent-Karte) und Ebenen-Zeile."""
    open_log = opened if opened is not None else []
    panel = build_right_panel(
        _actions(calls), _noop_layer_actions(), _noop_height_actions(),
        on_open=lambda: open_log.append(True),
        on_open_path=lambda _p: None,
        recent=["/tmp/a.png"],
    )
    # Eine Ebenen-Zeile einblenden, damit auch die Zeilen-Buttons geprüft werden.
    panel.layer_panel.refresh([
        LayerInfo(id="c", name="Farbe", kind=LayerKind.COLOR, visible=True,
                  opacity=1.0, locked=False, role=None, active=True),
    ])
    return panel


def test_buttons_with_custom_border_define_their_own_focus_state(qapp):
    """#441: Wer im Inline-Stylesheet ``border`` anfasst, muss ``:focus`` liefern.

    Widget-Stylesheets haben bei ``border``-Konflikten Vorrang vor der
    App-QSS-Fokusregel; ohne eigenen ``:focus``-Block bliebe der Fokus dort
    unsichtbar. Geprüft über alle Buttons aller sechs Schritt-Seiten.
    """
    from PyQt6.QtWidgets import QToolButton

    panel = _full_panel([])
    offenders = [
        f"{type(w).__name__}({w.text()!r} / {w.objectName()!r})"
        for cls in (QPushButton, QToolButton)
        for w in panel.frame.findChildren(cls)
        if "border" in w.styleSheet() and ":focus" not in w.styleSheet()
    ]
    assert not offenders, f"Buttons ohne sichtbaren Fokuszustand: {offenders}"


def test_drop_frame_opens_via_keyboard(qapp):
    """#441: Enter/Leertaste auf dem Ablagefeld öffnen den Datei-Dialog."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    from bgremover.right_panel import _DropFrame

    opened: list[bool] = []
    panel = _full_panel([], opened)
    drop = panel.frame.findChild(_DropFrame)
    assert drop is not None
    assert drop.focusPolicy() == Qt.FocusPolicy.StrongFocus
    QTest.keyClick(drop, Qt.Key.Key_Return)
    QTest.keyClick(drop, Qt.Key.Key_Space)
    assert opened == [True, True]


@pytest.mark.ui_smoke
def test_interactive_targets_meet_minimum_hit_size(qapp):
    """#441: Sichtbare interaktive Ziele sind ≥ 24 px hoch, primäre ≥ 32 px.

    Dokumentierte Ausnahmen: **Slider** (Klickziel ist der gesamte Groove, der
    14-px-Griff allein zählt nicht) und das **Ablagefeld** (Maus-Komfort;
    der Tastatur-/Primärpfad ist der „Datei öffnen…"-Button, plus Enter/Space
    direkt auf dem Feld).
    """
    from PyQt6.QtWidgets import QCheckBox, QMainWindow, QToolButton

    from bgremover.constants import _WINDOW_MIN_H, _WINDOW_MIN_W

    panel = _full_panel([])
    win = QMainWindow()
    win.setCentralWidget(panel.frame)
    win.resize(_WINDOW_MIN_W, _WINDOW_MIN_H)
    win.show()
    qapp.processEvents()
    try:
        for step in WorkflowStep:
            panel.set_step(step)
            qapp.processEvents()
            targets = [
                w
                for cls in (QPushButton, QToolButton, QSpinBox, QComboBox, QCheckBox)
                for w in panel.frame.findChildren(cls)
                if w.isVisible()
            ]
            assert targets, f"Schritt {step.name}: keine sichtbaren Ziele"
            for w in targets:
                label = f"{step.name}: {type(w).__name__}({w.text() if hasattr(w, 'text') else ''!r})"
                assert w.height() >= 24, f"{label} nur {w.height()} px hoch"
                assert w.width() >= 24, f"{label} nur {w.width()} px breit"
        # Primäre Workflow-Controls: bevorzugt ≥ 32 px (Spec #441).
        panel.set_step(WorkflowStep.OPEN)
        qapp.processEvents()
        assert panel.open_button.height() >= 32
        assert panel.nav_next.height() >= 32
    finally:
        win.close()


@pytest.mark.ui_smoke
def test_open_page_tab_order_is_visual_order(qapp):
    """#441: Fokuskette der Öffnen-Seite: Ablagefeld → „Datei öffnen…" → Recent."""
    from bgremover.right_panel import _DropFrame

    panel = _full_panel([])
    drop = panel.frame.findChild(_DropFrame)
    recent_row = _button(panel.frame, "a.png")
    assert drop is not None

    order: list[str] = []
    widget = drop
    for _ in range(200):  # Kette ist zyklisch; harte Obergrenze
        if widget is panel.open_button:
            order.append("open")
        elif widget is recent_row:
            order.append("recent")
        widget = widget.nextInFocusChain()
        if widget is drop or widget is None:
            break
    assert order[:2] == ["open", "recent"]
