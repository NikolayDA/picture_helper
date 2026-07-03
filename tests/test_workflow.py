"""Smoke-Tests für den geführten Workflow (Epic #418): Schrittleiste,
Schritt-Gating, Navigation und kontextuelle Werkzeugleiste.

Headless (``QT_QPA_PLATFORM=offscreen``); die Fenster werden – wie in
``test_tool_shortcuts`` – direkt konstruiert (rembg-Warmup gepatcht).
"""
from __future__ import annotations

import pytest
from PIL import Image
from PyQt6.QtCore import QSettings

from bgremover import MainWindow
from bgremover.stepper import Stepper, WorkflowStep, step_label


@pytest.fixture
def window(qapp, qtbot, tmp_path, monkeypatch):
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    monkeypatch.setattr(MainWindow, "_start_rembg_warmup", lambda self: None)
    win = MainWindow()
    qtbot.addWidget(win)
    return win


def _load_image(win: MainWindow) -> None:
    win._canvas.apply_loaded_image(Image.new("RGBA", (16, 16), (10, 20, 30, 255)), "x.png")


def _load_sized_image(win: MainWindow, width: int, height: int) -> None:
    win._canvas.apply_loaded_image(
        Image.new("RGBA", (width, height), (10, 20, 30, 255)), "sized.png")


# ── Schrittleiste (Issue #419) ────────────────────────────────────────────


@pytest.mark.ui_smoke
def test_stepper_renders_six_steps(qapp):
    stepper = Stepper()
    assert len(stepper._cells) == 6
    # Labels laufen über tr() und stimmen mit den sechs Schritten überein.
    assert step_label(WorkflowStep.OPEN) == "Öffnen"
    assert step_label(WorkflowStep.EXPORT) == "Export"


@pytest.mark.ui_smoke
def test_stepper_emits_selected_step(qapp, qtbot):
    stepper = Stepper()
    with qtbot.waitSignal(stepper.stepSelected, timeout=500) as blocker:
        stepper._cells[WorkflowStep.OPEN].clicked.emit(int(WorkflowStep.OPEN))
    assert blocker.args == [int(WorkflowStep.OPEN)]


# ── Gating (Issue #420) ───────────────────────────────────────────────────


@pytest.mark.ui_smoke
def test_steps_locked_until_image_loaded(window):
    w = window
    assert w._step is WorkflowStep.OPEN
    assert w._stepper._locked is True
    # Klick auf einen gesperrten Schritt bleibt wirkungslos.
    w._stepper.stepSelected.emit(int(WorkflowStep.SHAPE))
    assert w._step is WorkflowStep.OPEN


@pytest.mark.ui_smoke
def test_loading_image_unlocks_and_advances(window):
    w = window
    _load_image(w)
    # Bild geladen → Schritte frei, automatisch weiter zu „Freistellen".
    assert w._stepper._locked is False
    assert w._step is WorkflowStep.CUTOUT
    # Jetzt ist ein Sprung zu einem späteren Schritt erlaubt.
    w._stepper.stepSelected.emit(int(WorkflowStep.RELIEF))
    assert w._step is WorkflowStep.RELIEF


@pytest.mark.ui_smoke
def test_step_change_updates_status_bar(window):
    """#420: Jeder Schrittwechsel spiegelt sich in der Statuszeile."""
    w = window
    _load_image(w)  # Autosprung zu „Freistellen" meldet den Schritt
    assert w._sb.currentMessage() == "Schritt 2/6: Freistellen"
    w._go_to_step(WorkflowStep.ADJUST)
    assert w._sb.currentMessage() == "Schritt 3/6: Anpassen"
    w._prev_step()
    assert w._sb.currentMessage() == "Schritt 2/6: Freistellen"


@pytest.mark.ui_smoke
def test_shape_resize_fields_follow_loaded_and_resized_project(window):
    """#448: Inline-Größenfelder spiegeln Bild-/Projektgröße statt 1200x900."""
    w = window
    _load_sized_image(w, 32, 24)
    w._go_to_step(WorkflowStep.SHAPE)

    assert w._right_panel.resize_w.value() == 32
    assert w._right_panel.resize_h.value() == 24

    applied: list[tuple[int, int]] = []
    original_apply_resize = w._canvas.apply_resize

    def record_resize(width: int, height: int):
        applied.append((width, height))
        original_apply_resize(width, height)

    w._canvas.apply_resize = record_resize
    _button = next(
        b for b in w._right_panel.frame.findChildren(type(w._right_panel.nav_next))
        if b.text().replace("\n", " ") == "Größe anwenden")
    _button.click()

    assert applied == [(32, 24)]
    assert w._right_panel.resize_w.value() == 32
    assert w._right_panel.resize_h.value() == 24

    w._right_panel.resize_w.setValue(20)
    w._right_panel.resize_h.setValue(10)
    _button.click()
    assert w._canvas.project is not None
    assert w._canvas.project.size == (20, 10)
    assert w._right_panel.resize_w.value() == 20
    assert w._right_panel.resize_h.value() == 10


# ── Navigation (Issue #421) ───────────────────────────────────────────────


@pytest.mark.ui_smoke
def test_nav_next_and_prev(window):
    w = window
    _load_image(w)  # Schritt 2
    w._next_step()
    assert w._step is WorkflowStep.ADJUST
    w._prev_step()
    assert w._step is WorkflowStep.CUTOUT
    # Weiter-Beschriftung spiegelt das nächste Ziel.
    assert w._right_panel.nav_next.text() == "Weiter: Anpassen →"


@pytest.mark.ui_smoke
def test_export_button_triggers_save_and_stays(window, monkeypatch):
    w = window
    _load_image(w)
    w._go_to_step(WorkflowStep.EXPORT)
    saved: list[bool] = []
    monkeypatch.setattr(w, "_save", lambda: saved.append(True))
    w._next_step()  # „Exportieren ✓" löst das Speichern aus, bleibt im Schritt
    assert saved == [True]
    assert w._step is WorkflowStep.EXPORT
    assert w._right_panel.nav_next.text() == "Exportieren ✓"


@pytest.mark.ui_smoke
def test_loading_image_resets_from_later_step(window):
    """Ein neues Bild steigt immer beim Freistellen neu ein (PR #423-Review)."""
    w = window
    _load_image(w)
    w._go_to_step(WorkflowStep.EXPORT)
    _load_image(w)  # zweites Bild, während Schritt „Export" aktiv war
    assert w._step is WorkflowStep.CUTOUT


# ── Kontextuelle Werkzeugleiste + Canvas-Gate (Issue #422, PR #423-Review) ──


@pytest.mark.ui_smoke
def test_canvas_tools_gated_outside_cutout(window):
    w = window
    _load_image(w)  # Schritt 2 = Freistellen → Werkzeuge aktiv
    assert w._canvas._tools_enabled is True
    w._go_to_step(WorkflowStep.ADJUST)
    assert w._canvas._tools_enabled is False
    w._go_to_step(WorkflowStep.CUTOUT)
    assert w._canvas._tools_enabled is True


# ── Kontextuelle Werkzeugleiste (Issue #422) ──────────────────────────────


@pytest.mark.ui_smoke
def test_selection_tools_visible_only_in_cutout(window):
    w = window
    _load_image(w)  # Schritt 2 = Freistellen
    assert not w.toolbar.btn_brush.isHidden()
    assert not w.toolbar.btn_lasso.isHidden()
    # In einem anderen Schritt sind die Auswahlwerkzeuge ausgeblendet.
    w._go_to_step(WorkflowStep.ADJUST)
    assert w.toolbar.btn_brush.isHidden()
    assert w.toolbar.sel_separator.isHidden()


# ── A11y: Tastaturbedienung der Schrittleiste (#441) ──────────────────────


@pytest.mark.ui_smoke
def test_stepper_cells_keyboard_activation(qapp, qtbot):
    """Enter/Leertaste aktivieren einen fokussierbaren Schritt wie ein Klick."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    stepper = Stepper()
    qtbot.addWidget(stepper)
    received: list[int] = []
    stepper.stepSelected.connect(received.append)

    cell = stepper._cells[WorkflowStep.ADJUST]
    assert cell.focusPolicy() == Qt.FocusPolicy.StrongFocus
    QTest.keyClick(cell, Qt.Key.Key_Space)
    QTest.keyClick(cell, Qt.Key.Key_Return)
    assert received == [int(WorkflowStep.ADJUST)] * 2


@pytest.mark.ui_smoke
def test_stepper_locked_cells_are_not_focusable(qapp):
    """Gesperrte Schritte sind deaktiviert und fallen aus der Tab-Reihenfolge."""
    stepper = Stepper()
    stepper.set_locked(True)
    assert stepper._cells[WorkflowStep.OPEN].isEnabled()
    for step in (WorkflowStep.CUTOUT, WorkflowStep.ADJUST, WorkflowStep.SHAPE,
                 WorkflowStep.RELIEF, WorkflowStep.EXPORT):
        # Deaktivierte Widgets erhalten in Qt keinen Tastaturfokus.
        assert not stepper._cells[step].isEnabled()
    stepper.set_locked(False)
    assert all(cell.isEnabled() for cell in stepper._cells.values())


@pytest.mark.ui_smoke
def test_stepper_focus_visible_only_for_keyboard(qapp):
    """Fokus-Markierung mit ``:focus-visible``-Semantik: Maus-Fokus lässt das
    Zell-Stylesheet unverändert (Layout exakt wie im Prototyp, Spec §6),
    Tab-Fokus zeigt die akzentgetönte Fläche – rahmenlos, denn ein ``border``
    in der selektorlosen Zell-Regel erschien früher als Doppelrahmen um den
    aktiven Schritt (Zelle + Label).
    """
    from PyQt6.QtCore import QEvent, Qt
    from PyQt6.QtGui import QFocusEvent

    from bgremover.theme import DARK, LIGHT, active_palette, set_active_palette

    try:
        for palette in (DARK, LIGHT):
            set_active_palette(palette)
            stepper = Stepper()
            cell = stepper._cells[WorkflowStep.OPEN]
            resting = cell.styleSheet()
            # Die Ruhe-Regel schirmt Kreis/Label gegen das ``border-bottom``
            # des Steppers ab und hält die Zelle transparent.
            assert "transparent" in resting
            assert "border: none" in resting
            # Maus-Klick: keine sichtbare Fokus-Änderung.
            cell.focusInEvent(
                QFocusEvent(QEvent.Type.FocusIn, Qt.FocusReason.MouseFocusReason))
            assert cell.styleSheet() == resting
            # Tastatur (Tab): getönte, rahmenlose Fläche.
            cell.focusInEvent(
                QFocusEvent(QEvent.Type.FocusIn, Qt.FocusReason.TabFocusReason))
            sheet = cell.styleSheet()
            assert active_palette().accent_soft in sheet
            assert "solid" not in sheet
            cell.focusOutEvent(QFocusEvent(QEvent.Type.FocusOut))
            assert cell.styleSheet() == resting
            stepper.deleteLater()
    finally:
        set_active_palette(DARK)


@pytest.mark.ui_smoke
def test_stepper_cells_meet_minimum_hit_size(qapp):
    """Schritt-Zellen (≥ 32 px) erfüllen die Trefferfläche (#441); der Kreis ist
    nur der visuelle Indikator und ist gemäß Spec §6 je Zustand 26 px
    (ausstehend/erledigt) oder 28 px (aktiv) groß – die klickbare Fläche ist
    die ganze Zelle (``mousePressEvent`` sitzt auf ``_StepCell``, nicht ``_circle``).
    """
    stepper = Stepper()
    for step, cell in stepper._cells.items():
        assert cell.minimumHeight() >= 32
        expected = 28 if step is WorkflowStep.OPEN else 26
        assert cell._circle.width() == cell._circle.height() == expected


@pytest.mark.ui_smoke
def test_stepper_tab_order_follows_step_sequence(qapp):
    """#441: Die Tab-Reihenfolge der Schrittleiste folgt der Schrittfolge 1→6."""
    from bgremover.stepper import _StepCell

    stepper = Stepper()
    chain: list[int] = []
    widget = stepper._cells[WorkflowStep.OPEN]
    start = widget
    while True:
        if isinstance(widget, _StepCell):
            chain.append(int(widget._step))
        widget = widget.nextInFocusChain()
        if widget is start or widget is None:
            break
    assert chain == [1, 2, 3, 4, 5, 6]


@pytest.mark.ui_smoke
def test_toolbar_buttons_meet_minimum_hit_size(window):
    """#441: Werkzeugleisten-Buttons sind großzügige Ziele (54 px ≥ 32 px)."""
    tb = window.toolbar
    for btn in (tb.btn_move, tb.btn_wand, tb.btn_brush, tb.btn_eraser,
                tb.btn_lasso, tb.btn_height_lighten, tb.btn_height_darken,
                tb.btn_undo, tb.btn_redo, tb.btn_theme):
        assert btn.width() >= 32 and btn.height() >= 32


# ── Rail 1:1 zum Prototyp (Epic #455) ─────────────────────────────────────


@pytest.mark.ui_smoke
def test_move_tool_always_present_and_auto_activated(window):
    """#456: „Verschieben / Zoom" ist oberster Rail-Button in allen Schritten;
    Schritte ohne Auswahl-/Höhen-Werkzeuge aktivieren Move sichtbar."""
    from bgremover.constants import TOOL_MOVE

    w = window
    _load_image(w)  # Schritt 2
    assert not w.toolbar.btn_move.isHidden()
    # In Schritt 2 ist das Auswahlwerkzeug aktiv, nicht Move.
    assert w._canvas.current_tool != TOOL_MOVE
    for step in (WorkflowStep.OPEN, WorkflowStep.ADJUST, WorkflowStep.SHAPE,
                 WorkflowStep.RELIEF, WorkflowStep.EXPORT):
        w._go_to_step(step)
        assert not w.toolbar.btn_move.isHidden()
        assert w._canvas.current_tool == TOOL_MOVE
        assert w.toolbar.btn_move.isChecked()


@pytest.mark.ui_smoke
def test_returning_to_cutout_restores_last_selection_tool(window):
    """#456: Zurück im Freistellen greift das zuletzt gewählte Auswahlwerkzeug."""
    from bgremover.constants import TOOL_ERASER

    w = window
    _load_image(w)  # Schritt 2, Default Zauberstab
    w._set_tool(TOOL_ERASER)
    w._go_to_step(WorkflowStep.SHAPE)
    w._go_to_step(WorkflowStep.CUTOUT)
    assert w._canvas.current_tool == TOOL_ERASER
    assert w.toolbar.btn_eraser.isChecked()


@pytest.mark.ui_smoke
def test_height_tools_visible_only_in_relief_step(window):
    """#457: Aufhellen/Abdunkeln (nach Trenner) genau in Schritt 5."""
    w = window
    _load_image(w)
    for step in (WorkflowStep.CUTOUT, WorkflowStep.ADJUST, WorkflowStep.SHAPE,
                 WorkflowStep.EXPORT):
        w._go_to_step(step)
        assert w.toolbar.btn_height_lighten.isHidden()
        assert w.toolbar.btn_height_darken.isHidden()
        assert w.toolbar.height_separator.isHidden()
    w._go_to_step(WorkflowStep.RELIEF)
    assert not w.toolbar.btn_height_lighten.isHidden()
    assert not w.toolbar.btn_height_darken.isHidden()
    assert not w.toolbar.height_separator.isHidden()


@pytest.mark.ui_smoke
def test_height_tools_enabled_only_with_active_height_layer(window):
    """#457: Ohne aktive HEIGHT-Ebene deaktiviert (Tooltip nennt den Grund);
    eine erzeugte Höhenkarte gibt die Werkzeuge frei."""
    from bgremover.constants import TOOL_HEIGHT_LIGHTEN, TOOL_MOVE
    from bgremover.i18n import tr

    w = window
    _load_image(w)
    w._go_to_step(WorkflowStep.RELIEF)
    assert not w.toolbar.btn_height_lighten.isEnabled()
    assert (w.toolbar.btn_height_lighten.toolTip()
            == tr("toolbar.height_tools.disabled.tooltip"))

    w._canvas.generate_height_map()  # neue HEIGHT-Ebene wird aktiv
    assert w.toolbar.btn_height_lighten.isEnabled()
    assert w.toolbar.btn_height_darken.isEnabled()
    assert (w.toolbar.btn_height_lighten.toolTip()
            == tr("toolbar.height_lighten.tooltip"))

    # Wechsel auf eine Nicht-HEIGHT-Ebene sperrt wieder und fällt auf Move zurück.
    w._set_tool(TOOL_HEIGHT_LIGHTEN)
    color_layer = next(
        layer for layer in w._canvas.project.layers
        if layer.kind.name == "COLOR")
    w._canvas.set_active_layer(color_layer.id)
    assert not w.toolbar.btn_height_lighten.isEnabled()
    assert w._canvas.current_tool == TOOL_MOVE


@pytest.mark.ui_smoke
def test_rail_foot_visible_in_all_steps(window):
    """#458: Rail-Fuß (Trenner · Undo · Redo · Theme) ist schrittunabhängig."""
    w = window
    _load_image(w)
    for step in WorkflowStep:
        w._go_to_step(step)
        assert not w.toolbar.btn_undo.isHidden()
        assert not w.toolbar.btn_redo.isHidden()
        assert not w.toolbar.btn_theme.isHidden()
        assert not w.toolbar.foot_separator.isHidden()


@pytest.mark.ui_smoke
def test_removed_rail_functions_stay_reachable(window):
    """#458: KI/Original/Verlauf/Öffnen/Speichern bleiben ohne Rail-Buttons
    erreichbar (Inspector-Primärbutton bzw. Menü-Actions mit Kürzeln)."""
    from PyQt6.QtGui import QKeySequence

    w = window
    # KI: Schritt-2-Primärbutton im Inspector (#437).
    assert w._right_panel.ai_button is not None
    actions = {a.text(): a for a in w.findChildren(type(w._escape_action))}
    fmt = QKeySequence.SequenceFormat.PortableText
    assert actions["Öffnen…"].shortcut().toString(fmt) == "Ctrl+O"
    assert actions["Speichern"].shortcut().toString(fmt) == "Ctrl+S"
    assert "Original wiederherstellen" in actions
    # Verlauf: neuer Menü-Anker „Ansicht → Verlauf" öffnet das Popup.
    assert w._history_popup._popup is None
    actions["Verlauf"].trigger()
    assert w._history_popup._popup is not None
    assert w._history_popup._popup.isVisible()
    actions["Verlauf"].trigger()
    assert not w._history_popup._popup.isVisible()


@pytest.mark.ui_smoke
def test_rail_foot_undo_redo_respect_history_state(window):
    """#458: Undo/Redo im Rail-Fuß folgen dem tatsächlichen History-Zustand."""
    from PIL import Image as PILImage

    w = window
    _load_image(w)
    assert not w.toolbar.btn_undo.isEnabled()
    assert not w.toolbar.btn_redo.isEnabled()

    w._canvas.apply_edit(
        PILImage.new("RGBA", (16, 16), (1, 2, 3, 255)), "Testschritt")
    assert w.toolbar.btn_undo.isEnabled()
    assert not w.toolbar.btn_redo.isEnabled()

    w.toolbar.btn_undo.click()
    assert not w.toolbar.btn_undo.isEnabled()
    assert w.toolbar.btn_redo.isEnabled()

    w.toolbar.btn_redo.click()
    assert w.toolbar.btn_undo.isEnabled()
    assert not w.toolbar.btn_redo.isEnabled()


@pytest.mark.ui_smoke
def test_rail_foot_theme_button_syncs_with_menu(window):
    """#458: Der Rail-Theme-Umschalter löst dieselbe Aktion wie das Menü aus
    und hält dessen Häkchen synchron (kein widersprüchlicher Zustand)."""
    from PyQt6.QtWidgets import QApplication

    from bgremover.i18n import tr
    from bgremover.theme import DARK, active_palette, set_active_palette

    w = window
    app = QApplication.instance()
    original_sheet = app.styleSheet() if app is not None else ""
    original_palette = app.palette() if app is not None else None
    set_active_palette(DARK)
    try:
        action = w._theme_menu_action()
        assert action is not None and not action.isChecked()

        w.toolbar.btn_theme.click()
        assert not active_palette().is_dark
        assert action.isChecked()
        assert w._light_mode is True
        assert (w.toolbar.btn_theme.toolTip()
                == tr("toolbar.theme.to_dark.tooltip"))

        w.toolbar.btn_theme.click()
        assert active_palette().is_dark
        assert not action.isChecked()
        assert (w.toolbar.btn_theme.toolTip()
                == tr("toolbar.theme.to_light.tooltip"))
    finally:
        set_active_palette(DARK)
        if app is not None:
            app.setStyleSheet(original_sheet)
            if original_palette is not None:
                app.setPalette(original_palette)


@pytest.mark.ui_smoke
def test_move_tool_pans_with_left_drag(window):
    """#456: Im Move-Modus startet Linksklick den Pan (mittlere Maustaste
    bleibt in jedem Modus verfügbar, Zauberstab-Klick pannt nicht)."""
    from PyQt6.QtCore import QPointF, Qt

    from bgremover.constants import TOOL_MOVE, TOOL_WAND

    w = window
    _load_image(w)
    w._go_to_step(WorkflowStep.ADJUST)  # aktiviert Move
    assert w._canvas.current_tool == TOOL_MOVE

    w._canvas._viewport.start_pan(QPointF(5.0, 5.0))
    assert w._canvas._viewport.is_panning
    w._canvas._viewport.stop_pan()

    # Auswahlwerkzeug aktiv → Linksklick ohne Alt pannt weiterhin nicht.
    w._go_to_step(WorkflowStep.CUTOUT)
    assert w._canvas.current_tool == TOOL_WAND
    consumed = w._canvas._viewport.start_pan_if_requested(
        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPointF(0.0, 0.0))
    assert consumed is False
