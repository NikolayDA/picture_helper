"""Tests fuer ``WorkerController``-Lifecycle-Buchhaltung.

Stellt sicher, dass jeder ueber den Controller gestartete Worker waehrend
seiner Laufzeit in ``_workers`` registriert ist und nach ``thread.finished``
wieder ausgetragen wird – sonst wuechsen Memory und Threads pro Klick.
"""
from __future__ import annotations

import time

import numpy as np
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


def test_ai_cancel_still_completes_thread_lifecycle(qapp, controller, monkeypatch):
    """Abbruch mitten im KI-Lauf muss den Thread-Lifecycle dennoch voll
    abschliessen.

    Regression fuer „Bild laden, waehrend die KI rechnet": ``AIWorker._work``
    kehrt bei Abbruch ohne ``finished``/``error`` zurueck. Quittet der Thread
    dann nicht ueber sein eigenes ``done``-Signal, bleiben
    ``ai_thread``/``ai_worker`` gesetzt, ``on_finished`` laeuft nie und der
    KI-Button bliebe die restliche Session deaktiviert.
    """
    import io as _io
    import threading

    import bgremover.workers as _wm

    gate = threading.Event()
    result_buf = _io.BytesIO()
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(result_buf, format="PNG")

    def slow_rembg(_b):
        # Blockiert, bis der Test abgebrochen und das Tor geoeffnet hat – so
        # ist der Worker beim cancel_ai() garantiert noch aktiv.
        gate.wait(timeout=5.0)
        return result_buf.getvalue()

    monkeypatch.setattr(_wm, "rembg_remove", slow_rembg, raising=False)

    applied: list = []
    finished: list[bool] = []
    started = controller.start_ai(
        Image.new("RGBA", (4, 4), (10, 20, 30, 255)),
        on_done=applied.append,
        on_error=lambda _msg: None,
        on_finished=lambda: finished.append(True),
    )
    assert started
    thread = controller.ai_thread
    assert thread is not None

    controller.cancel_ai()
    gate.set()

    _drain(qapp, thread.isFinished)
    qapp.processEvents()

    assert controller.ai_thread is None
    assert controller.ai_worker is None
    assert controller._workers == []
    assert finished == [True]   # Thread-Abschluss lief -> Button reaktiviert
    assert applied == []        # abgebrochenes Ergebnis wird nicht angewandt


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


def test_warmup_releases_worker_when_rembg_raises(qapp, controller, monkeypatch):
    """Wirft ``rembg_remove`` waehrend des Warmups, muss der Controller den
    Thread-Lifecycle trotzdem komplett abschliessen (Worker freigegeben,
    ``warmup_done`` gesetzt, ``on_finished`` aufgerufen). Sonst haengt das
    Bootstrap, falls das Modell beim ersten Start nicht geladen werden
    kann (z. B. offline)."""
    import bgremover.workers as _wm

    def _raise(_b):
        raise RuntimeError("mock warmup failure")

    monkeypatch.setattr(_wm, "rembg_remove", _raise, raising=False)

    done: list[bool] = []
    started = controller.start_warmup(on_finished=lambda: done.append(True))
    assert started
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


def test_flood_fill_releases_worker_on_completion(qapp, controller):
    arr = np.zeros((6, 8, 4), dtype=np.uint8)
    arr[..., 3] = 255  # opak; Pixelinhalt egal fuer Tolerance=0/Saat (0,0)
    masks: list[np.ndarray] = []
    started = controller.start_flood_fill(
        arr, 0, 0, tolerance=0,
        on_done=masks.append,
        on_error=lambda _msg: None,
    )
    assert started
    assert len(controller._workers) == 1
    thread = controller.flood_fill_thread
    assert thread is not None

    _drain(qapp, thread.isFinished)
    qapp.processEvents()

    assert controller.flood_fill_thread is None
    assert controller._workers == []
    assert len(masks) == 1
    assert masks[0].shape == (6, 8)
    assert masks[0].all()


def test_flood_fill_concurrent_call_returns_false(qapp, controller, monkeypatch):
    """Zweiter Start waehrend der erste laeuft muss False liefern (kein
    parallel laufender Wand-Worker, weil sonst zwei Resultate gleichzeitig
    auf den Canvas-State zugreifen wuerden)."""
    import threading

    import bgremover.workers as _wm

    # Den Flood-Fill in einen Bremsklotz patchen: blockiert solange, bis
    # wir es freigeben. Damit ist der erste Worker waehrend des zweiten
    # start_flood_fill-Aufrufs garantiert noch aktiv.
    gate = threading.Event()

    def slow_flood_fill(arr, x, y, tol, should_cancel=None):
        gate.wait(timeout=5.0)
        return np.zeros(arr.shape[:2], dtype=bool)

    monkeypatch.setattr(_wm, "flood_fill", slow_flood_fill)

    arr = np.zeros((4, 4, 4), dtype=np.uint8)
    arr[..., 3] = 255

    first = controller.start_flood_fill(
        arr, 0, 0, tolerance=0,
        on_done=lambda _m: None,
        on_error=lambda _msg: None,
    )
    assert first
    # Solange der erste Worker im Slow-Path haengt, lehnt der Controller
    # einen Parallelstart ab.
    second = controller.start_flood_fill(
        arr, 0, 0, tolerance=0,
        on_done=lambda _m: None,
        on_error=lambda _msg: None,
    )
    assert not second

    # Bremsklotz freigeben und sauber abklingen lassen.
    gate.set()
    thread = controller.flood_fill_thread
    assert thread is not None
    _drain(qapp, thread.isFinished)
    qapp.processEvents()
    assert controller.flood_fill_thread is None


def test_flood_fill_cancel_completes_lifecycle_without_result(qapp, controller, monkeypatch):
    """Abbruch eines laufenden Flood-Fill: kein Ergebnis angewandt, aber der
    Thread-Lifecycle wird vollständig abgeschlossen (Worker/Thread freigegeben)."""
    import threading

    import bgremover.workers as _wm

    gate = threading.Event()

    def slow_flood_fill(arr, x, y, tol, should_cancel=None):
        gate.wait(timeout=5.0)
        return np.ones(arr.shape[:2], dtype=bool)

    monkeypatch.setattr(_wm, "flood_fill", slow_flood_fill)

    arr = np.zeros((4, 4, 4), dtype=np.uint8)
    arr[..., 3] = 255
    masks: list = []
    started = controller.start_flood_fill(
        arr, 0, 0, tolerance=0,
        on_done=masks.append,
        on_error=lambda _msg: None,
    )
    assert started
    thread = controller.flood_fill_thread
    assert thread is not None

    controller.cancel_flood_fill()
    gate.set()

    _drain(qapp, thread.isFinished)
    qapp.processEvents()

    assert controller.flood_fill_thread is None
    assert controller.flood_fill_worker is None
    assert controller._workers == []
    assert masks == []   # abgebrochenes Ergebnis wird nicht zugestellt
