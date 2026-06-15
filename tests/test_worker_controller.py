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
from PyQt6 import sip
from PyQt6.QtCore import QCoreApplication, QEvent, QObject, pyqtSignal

from bgremover.ai_process import InferenceError
from bgremover.worker_controller import WorkerController
from tests._fakes import FakeInference


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


def test_build_thread_registers_and_releases_worker(qapp, controller):
    worker = _ImmediateWorker()
    thread = controller._build_thread(worker, quit_on=(worker.finished,))
    thread.start()
    assert worker in controller._workers

    _drain(
        qapp,
        lambda: thread.isFinished() and controller._workers == [],
    )
    assert controller._workers == []


def test_finished_worker_and_thread_are_qt_deleted(qapp, controller):
    """Verhaltens-Ersatz für den früheren AST-Check auf ``deleteLater``:
    Nach Threadende und Zustellung der DeferredDelete-Events sind die
    C++-Objekte von Worker UND Thread tatsächlich freigegeben – ohne die
    ``deleteLater``-Verdrahtung in ``_build_thread`` sammelten sich pro
    Klick Qt-Objekte an.
    """
    worker = _ImmediateWorker()
    thread = controller._build_thread(worker, quit_on=(worker.finished,))
    thread.start()

    def _both_deleted() -> bool:
        # Ohne laufenden Event-Loop werden DeferredDelete-Events nicht von
        # processEvents() zugestellt – explizit ausliefern.
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        return sip.isdeleted(worker) and sip.isdeleted(thread)

    _drain(qapp, _both_deleted)


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

    _drain(
        qapp,
        lambda: controller.load_thread is None and controller._workers == [],
    )

    assert thread.isFinished()
    assert controller.load_thread is None
    assert controller._workers == []


def test_image_load_concurrent_call_returns_false(
    qapp, controller, monkeypatch,
):
    import threading

    from bgremover.workers import ImageLoadWorker

    started = threading.Event()
    release = threading.Event()

    def slow_load(worker):
        started.set()
        release.wait(timeout=5.0)
        worker.error.emit("released")

    monkeypatch.setattr(ImageLoadWorker, "_work", slow_load)

    first = controller.start_image_load(
        "first.png",
        on_loaded=lambda _img, _path: None,
        on_error=lambda _msg: None,
    )
    assert first
    assert started.wait(timeout=2.0)
    thread = controller.load_thread
    assert thread is not None

    second = controller.start_image_load(
        "second.png",
        on_loaded=lambda _img, _path: None,
        on_error=lambda _msg: None,
    )
    assert second is False
    assert len(controller._workers) == 1

    release.set()
    _drain(
        qapp,
        lambda: controller.load_thread is None and controller._workers == [],
    )
    assert thread.isFinished()
    assert controller.load_thread is None
    assert controller._workers == []


def test_ai_releases_worker_on_completion(qapp):
    fake = FakeInference()
    controller = WorkerController(QObject(), shutdown_ms=2000, inference=fake)

    results: list = []
    started = controller.start_ai(
        Image.new("RGBA", (4, 4), (10, 20, 30, 255)),
        on_done=results.append,
        on_error=lambda _msg: None,
        on_finished=lambda: None,
    )
    assert started
    assert len(controller._workers) == 1
    thread = controller.ai_thread
    assert thread is not None

    _drain(
        qapp,
        lambda: (
            controller.ai_thread is None
            and controller.ai_worker is None
            and controller._workers == []
        ),
    )

    assert thread.isFinished()
    assert controller.ai_thread is None
    assert controller.ai_worker is None
    assert controller._workers == []
    assert fake.infer_calls == 1
    assert len(results) == 1   # dekodiertes Ergebnisbild zugestellt


def test_ai_cancel_still_completes_thread_lifecycle(qapp):
    """Abbruch mitten im KI-Lauf muss den Thread-Lifecycle dennoch voll
    abschliessen.

    Regression fuer „Bild laden, waehrend die KI rechnet": ``AIWorker._work``
    kehrt bei Abbruch ohne ``finished``/``error`` zurueck. Quittet der Thread
    dann nicht ueber sein eigenes ``done``-Signal, bleiben
    ``ai_thread``/``ai_worker`` gesetzt, ``on_finished`` laeuft nie und der
    KI-Button bliebe die restliche Session deaktiviert.
    """
    import threading

    # Tor zu lassen: ``infer`` blockiert pollend, bis der Abbruch greift – so
    # ist der Worker beim cancel_ai() garantiert noch aktiv.
    fake = FakeInference(gate=threading.Event())
    controller = WorkerController(QObject(), shutdown_ms=2000, inference=fake)

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

    _drain(
        qapp,
        lambda: (
            controller.ai_thread is None
            and controller.ai_worker is None
            and controller._workers == []
        ),
    )

    assert thread.isFinished()
    assert controller.ai_thread is None
    assert controller.ai_worker is None
    assert controller._workers == []
    assert finished == [True]   # Thread-Abschluss lief -> Button reaktiviert
    assert applied == []        # abgebrochenes Ergebnis wird nicht angewandt


def test_ai_and_flood_fill_use_independent_slots(
    qapp, monkeypatch,
):
    import threading

    import bgremover.workers as _wm

    flood_started = threading.Event()
    release = threading.Event()

    # KI-Inferenz blockiert pollend, bis ``release`` gesetzt ist – so laufen
    # KI- und Flood-Fill-Worker garantiert gleichzeitig.
    fake = FakeInference(gate=release)
    controller = WorkerController(QObject(), shutdown_ms=2000, inference=fake)

    def slow_flood_fill(arr, _x, _y, _tol, should_cancel=None):
        flood_started.set()
        release.wait(timeout=5.0)
        return np.ones(arr.shape[:2], dtype=bool)

    monkeypatch.setattr(_wm, "flood_fill", slow_flood_fill)

    image = Image.new("RGBA", (4, 4), (10, 20, 30, 255))
    arr = np.array(image)
    ai_results: list[Image.Image] = []
    flood_results: list[np.ndarray] = []
    ai_finished: list[bool] = []

    assert controller.start_ai(
        image,
        on_done=ai_results.append,
        on_error=lambda _msg: None,
        on_finished=lambda: ai_finished.append(True),
    )
    _drain(qapp, lambda: fake.infer_calls == 1)
    ai_thread = controller.ai_thread
    assert ai_thread is not None

    assert controller.start_ai(
        image,
        on_done=lambda _img: None,
        on_error=lambda _msg: None,
        on_finished=lambda: None,
    ) is False

    assert controller.start_flood_fill(
        arr, 0, 0, tolerance=0,
        on_done=flood_results.append,
        on_error=lambda _msg: None,
    )
    assert flood_started.wait(timeout=2.0)
    flood_thread = controller.flood_fill_thread
    assert flood_thread is not None

    assert controller.is_ai_running
    assert controller.is_flood_fill_running
    assert len(controller._workers) == 2

    release.set()
    _drain(
        qapp,
        lambda: (
            controller.ai_thread is None
            and controller.flood_fill_thread is None
            and controller._workers == []
        ),
    )

    # Nach dem Teardown kann Qt die QThread-C++-Objekte bereits via deleteLater
    # geloescht haben (auf macOS wegen Event-Loop-Timing eher als unter Linux).
    # Ein geloeschter Thread ist zwangslaeufig beendet – deleteLater wird erst
    # nach dem finished-Signal zugestellt. Daher deletion-sicher pruefen, statt
    # blind .isFinished() auf einem evtl. zerstoerten Wrapper aufzurufen (sonst
    # RuntimeError: wrapped C/C++ object of type QThread has been deleted).
    assert sip.isdeleted(ai_thread) or ai_thread.isFinished()
    assert sip.isdeleted(flood_thread) or flood_thread.isFinished()
    assert controller.ai_thread is None
    assert controller.flood_fill_thread is None
    assert controller._workers == []
    assert len(ai_results) == 1
    assert len(flood_results) == 1
    assert ai_finished == [True]


def test_warmup_releases_worker_on_completion(qapp):
    fake = FakeInference()
    controller = WorkerController(QObject(), shutdown_ms=2000, inference=fake)

    done: list[bool] = []
    started = controller.start_warmup(on_finished=lambda: done.append(True))
    assert started
    assert len(controller._workers) == 1
    thread = controller.warmup_thread
    assert thread is not None

    _drain(
        qapp,
        lambda: controller.warmup_thread is None and controller._workers == [],
    )

    assert thread.isFinished()
    assert controller.warmup_thread is None
    assert controller.warmup_done
    assert done == [True]
    assert controller._workers == []
    assert fake.warmup_calls == 1


def test_warmup_releases_worker_when_inference_raises(qapp):
    """Wirft der Warmup im Inferenzprozess (z. B. rembg offline nicht ladbar),
    muss der Controller den Thread-Lifecycle trotzdem komplett abschliessen
    (Worker freigegeben, ``warmup_done`` gesetzt, ``on_finished`` aufgerufen).
    Sonst haengt das Bootstrap."""
    fake = FakeInference(warmup_error=InferenceError("mock warmup failure"))
    controller = WorkerController(QObject(), shutdown_ms=2000, inference=fake)

    done: list[bool] = []
    started = controller.start_warmup(on_finished=lambda: done.append(True))
    assert started
    thread = controller.warmup_thread
    assert thread is not None

    _drain(
        qapp,
        lambda: controller.warmup_thread is None and controller._workers == [],
    )

    assert thread.isFinished()
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


def test_shutdown_all_cancels_workers_and_visits_every_thread(
    controller, monkeypatch,
):
    class Cancellable:
        def __init__(self):
            self.cancelled = False

        def cancel(self):
            self.cancelled = True

    ai_worker = Cancellable()
    flood_worker = Cancellable()
    threads = {
        "KI": object(),
        "Bildladen": object(),
        "rembg-Warmup": object(),
        "Flood-Fill": object(),
    }
    controller.ai_worker = ai_worker
    controller.flood_fill_worker = flood_worker
    controller.ai_thread = threads["KI"]
    controller.load_thread = threads["Bildladen"]
    controller.warmup_thread = threads["rembg-Warmup"]
    controller.flood_fill_thread = threads["Flood-Fill"]
    shutdowns: list[tuple[object, str]] = []
    monkeypatch.setattr(
        controller,
        "shutdown_thread",
        lambda thread, name: shutdowns.append((thread, name)) or True,
    )

    assert controller.shutdown_all() is True

    assert ai_worker.cancelled
    assert flood_worker.cancelled
    assert shutdowns == [
        (threads["KI"], "KI"),
        (threads["Bildladen"], "Bildladen"),
        (threads["rembg-Warmup"], "rembg-Warmup"),
        (threads["Flood-Fill"], "Flood-Fill"),
    ]
    assert controller.ai_thread is None
    assert controller.load_thread is None
    assert controller.warmup_thread is None
    assert controller.flood_fill_thread is None


def test_shutdown_all_keeps_unstopped_thread_referenced(
    controller, monkeypatch,
):
    ai_thread = object()
    controller.ai_thread = ai_thread
    monkeypatch.setattr(
        controller,
        "shutdown_thread",
        lambda thread, _name: thread is not ai_thread,
    )

    assert controller.shutdown_all() is False

    assert controller.ai_thread is ai_thread
    assert controller.load_thread is None
    assert controller.warmup_thread is None
    assert controller.flood_fill_thread is None
    assert controller._shutting_down is False


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

    _drain(
        qapp,
        lambda: (
            controller.flood_fill_thread is None
            and controller.flood_fill_worker is None
            and controller._workers == []
        ),
    )

    assert thread.isFinished()
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
    _drain(
        qapp,
        lambda: (
            controller.flood_fill_thread is None
            and controller.flood_fill_worker is None
            and controller._workers == []
        ),
    )
    assert thread.isFinished()
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

    _drain(
        qapp,
        lambda: (
            controller.flood_fill_thread is None
            and controller.flood_fill_worker is None
            and controller._workers == []
        ),
    )

    assert thread.isFinished()
    assert controller.flood_fill_thread is None
    assert controller.flood_fill_worker is None
    assert controller._workers == []
    assert masks == []   # abgebrochenes Ergebnis wird nicht zugestellt
