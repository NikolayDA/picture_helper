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
