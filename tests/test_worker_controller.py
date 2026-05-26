"""Tests fuer ``WorkerController``-Lifecycle-Buchhaltung.

Stellt sicher, dass jeder ueber den Controller gestartete Worker waehrend
seiner Laufzeit in ``_workers`` registriert ist und nach ``thread.finished``
wieder ausgetragen wird – sonst wuechsen Memory und Threads pro Klick.
"""
from __future__ import annotations

import time

import pytest
from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal

from bgremover.worker_controller import WorkerController


class _ImmediateWorker(QObject):
    """Minimaler Worker: emittiert ``finished`` sofort und beendet damit den Thread."""
    finished = pyqtSignal()

    def run(self) -> None:
        self.finished.emit()


def _drain(qapp, predicate, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qapp.processEvents()
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("Bedingung nicht innerhalb des Timeouts erfuellt")


@pytest.fixture
def controller(qapp):
    parent = QObject()
    return WorkerController(parent, shutdown_ms=2000)


def test_workers_list_starts_empty(controller):
    assert controller._workers == []


def test_launch_worker_registers_and_releases_worker(qapp, controller):
    worker = _ImmediateWorker()
    thread = controller.launch_worker(worker, quit_on=(worker.finished,))
    assert worker in controller._workers

    _drain(qapp, thread.isFinished)
    # Ein zweiter processEvents-Tick, damit die finished-Slots durchlaufen.
    qapp.processEvents()
    assert controller._workers == []


def test_image_load_releases_worker_on_completion(qapp, controller, tmp_path):
    p = tmp_path / "x.png"
    Image.new("RGB", (8, 8), (1, 2, 3)).save(p)
    started = controller.start_image_load(
        str(p),
        on_loaded=lambda _img, _path: None,
        on_error=lambda _msg: None,
    )
    assert started
    assert len(controller._workers) == 1
    thread = controller.load_thread
    assert thread is not None

    _drain(qapp, thread.isFinished)
    qapp.processEvents()

    assert controller.load_thread is None
    assert controller._workers == []


def test_ai_releases_worker_on_completion(qapp, controller, monkeypatch):
    import bgremover.workers as _wm
    # rembg muss patchbar sein, falls onnxruntime nicht installiert ist.
    if not hasattr(_wm, "rembg_remove"):
        monkeypatch.setattr(_wm, "rembg_remove", lambda _b: b"", raising=False)

    import io as _io
    result_buf = _io.BytesIO()
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(result_buf, format="PNG")
    monkeypatch.setattr(_wm, "rembg_remove", lambda _b: result_buf.getvalue())

    started = controller.start_ai(
        Image.new("RGBA", (4, 4), (10, 20, 30, 255)),
        on_done=lambda _img: None,
        on_error=lambda _msg: None,
        on_finished=lambda: None,
    )
    assert started
    assert len(controller._workers) == 1
    thread = controller.ai_thread
    assert thread is not None

    _drain(qapp, thread.isFinished)
    qapp.processEvents()

    assert controller.ai_thread is None
    assert controller.ai_worker is None
    assert controller._workers == []


def test_warmup_releases_worker_on_completion(qapp, controller, monkeypatch):
    import bgremover.workers as _wm
    monkeypatch.setattr(_wm, "rembg_remove", lambda _b: b"", raising=False)

    done: list[bool] = []
    started = controller.start_warmup(on_finished=lambda: done.append(True))
    assert started
    assert len(controller._workers) == 1
    thread = controller.warmup_thread
    assert thread is not None

    _drain(qapp, thread.isFinished)
    qapp.processEvents()

    assert controller.warmup_thread is None
    assert controller.warmup_done
    assert done == [True]
    assert controller._workers == []


def test_release_worker_is_idempotent(controller):
    """``_release_worker`` darf doppelt feuern, ohne zu werfen."""
    sentinel = QObject()
    controller._workers.append(sentinel)
    controller._release_worker(sentinel)
    controller._release_worker(sentinel)
    assert controller._workers == []
