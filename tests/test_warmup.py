"""Tests für den rembg-Warmup-Lebenszyklus.

Geprüft wird, dass ein fehlgeschlagener Warmup NICHT als „KI bereit"
gemeldet wird und dass der KI-Button während des Warmups gesperrt ist
(keine parallele Modellinitialisierung).
"""
from __future__ import annotations

import time

import pytest
from PyQt6.QtCore import QObject

from bgremover import MainWindow
from bgremover.status_messages import StatusMessages as SM
from bgremover.worker_controller import WorkerController

# Echte Methode beim Import erfassen – VOR dem autouse-Patch
# ``_no_rembg_warmup`` (conftest), der sie pro Test auf no-op setzt.
_REAL_START_WARMUP = MainWindow._start_rembg_warmup


@pytest.fixture
def main_window(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    return w


def test_start_warmup_propagates_error_to_callback(qapp):
    """start_warmup meldet Inferenz-Fehler an on_error – nur so kann die UI
    einen fehlgeschlagenen Warmup von einem erfolgreichen unterscheiden."""
    from bgremover.ai_process import InferenceError
    from tests._fakes import FakeInference

    fake = FakeInference(warmup_error=InferenceError("mock warmup failure"))
    controller = WorkerController(QObject(), shutdown_ms=2000, inference=fake)
    errors: list[str] = []
    done: list[bool] = []
    started = controller.start_warmup(
        on_finished=lambda: done.append(True),
        on_error=errors.append,
    )
    assert started
    thread = controller.warmup_thread
    assert thread is not None

    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline and not thread.isFinished():
        qapp.processEvents()
        time.sleep(0.01)
    qapp.processEvents()

    assert done == [True]              # Lifecycle vollständig abgeschlossen
    assert len(errors) == 1           # Fehler wurde gemeldet
    assert "mock warmup failure" in errors[0]
    assert controller.warmup_thread is None


def test_warmup_failure_does_not_report_ready(main_window):
    """Nach Warmup-Fehler darf nicht „KI bereit" erscheinen; der KI-Button
    bleibt ohne geladenes Bild aber gesperrt."""
    w = main_window
    w._on_warmup_error("boom")
    w._on_warmup_done()
    assert w._warmup_failed is True
    assert w._toolbar.btn_ai.isEnabled() is False
    assert w._right_panel.ai_button.isEnabled() is False
    assert w._sb.currentMessage() == SM.KI_FEHLER_WARMUP


def test_warmup_success_reports_ready(main_window):
    w = main_window
    w._on_warmup_done()
    assert w._warmup_failed is False
    assert w._toolbar.btn_ai.isEnabled() is False
    assert w._right_panel.ai_button.isEnabled() is False
    assert w._sb.currentMessage() == SM.KI_BEREIT


def test_start_warmup_disables_ai_button(main_window, monkeypatch):
    """Während des Warmups ist der KI-Button gesperrt."""
    w = main_window
    # Controller-Aufruf neutralisieren – nur das Gating prüfen, kein Thread.
    monkeypatch.setattr(
        w._worker_controller, "start_warmup", lambda **kwargs: True)
    w._toolbar.btn_ai.setEnabled(True)
    w._right_panel.ai_button.setEnabled(True)
    _REAL_START_WARMUP(w)  # echte Methode, umgeht den autouse-No-op
    assert w._toolbar.btn_ai.isEnabled() is False
    assert w._right_panel.ai_button.isEnabled() is False
