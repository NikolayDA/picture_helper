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
def test_stepper_focus_visual_uses_accent(qapp):
    """Der Tastaturfokus ist als akzentgetönte Fläche sichtbar – je Schema."""
    from PyQt6.QtCore import QEvent
    from PyQt6.QtGui import QFocusEvent

    from bgremover.theme import DARK, LIGHT, active_palette, set_active_palette

    try:
        for palette in (DARK, LIGHT):
            set_active_palette(palette)
            stepper = Stepper()
            cell = stepper._cells[WorkflowStep.OPEN]
            cell.focusInEvent(QFocusEvent(QEvent.Type.FocusIn))
            assert active_palette().accent_soft in cell.styleSheet()
            cell.focusOutEvent(QFocusEvent(QEvent.Type.FocusOut))
            assert "transparent" in cell.styleSheet()
            stepper.deleteLater()
    finally:
        set_active_palette(DARK)


@pytest.mark.ui_smoke
def test_stepper_cells_meet_minimum_hit_size(qapp):
    """Schritt-Zellen (≥ 32 px) und Kreis (28 px) erfüllen die Trefferflächen (#441)."""
    stepper = Stepper()
    for cell in stepper._cells.values():
        assert cell.minimumHeight() >= 32
        assert cell._circle.width() == cell._circle.height() == 28


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
    for btn in (tb.btn_wand, tb.btn_brush, tb.btn_eraser, tb.btn_lasso,
                tb.btn_ai, tb.btn_history):
        assert btn.width() >= 32 and btn.height() >= 32
