"""Test für sauberes Thread-Shutdown beim Schliessen des Fensters.

Headless (offscreen): startet einen künstlich blockierenden Worker über
den echten ``WorkerController._build_thread``-Pfad, schliesst das Fenster und
prüft, dass ``closeEvent`` den Thread sauber stoppt, statt zu crashen
(Regression gegen „QThread: Destroyed while thread is still running“).
"""
import gc
import threading
import time

from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal

from bgremover import MainWindow
from bgremover.worker_controller import WorkerController


class _BlockingWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, secs: float) -> None:
        super().__init__()
        self._secs = secs

    def run(self) -> None:
        time.sleep(self._secs)        # simuliert blockierenden C-Call
        self.finished.emit()


class _RecordingWorker(QObject):
    """Hängt einen Marker in *sink*, sobald run() läuft."""
    finished = pyqtSignal()

    def __init__(self, sink: list) -> None:
        super().__init__()
        self._sink = sink            # Worker → Liste; Liste hält Worker NICHT

    def run(self) -> None:
        self._sink.append(True)
        self.finished.emit()


class _FakeThread:
    def __init__(self, wait_results: list[bool]) -> None:
        self.quit_called = False
        self.terminate_called = False
        self.wait_results = wait_results
        self.wait_timeouts: list[int] = []

    def isRunning(self) -> bool:
        return True

    def quit(self) -> None:
        self.quit_called = True

    def wait(self, ms: int) -> bool:
        self.wait_timeouts.append(ms)
        return self.wait_results.pop(0)

    def terminate(self) -> None:
        self.terminate_called = True


def test_build_thread_keeps_worker_alive_without_caller_ref(qapp, monkeypatch):
    """Regression: ``WorkerController._build_thread`` muss eine starke Referenz
    auf den Worker halten. Sonst sammelt CPython ihn ein, sobald der Aufrufer
    keine Referenz mehr hält (PyQt verbindet Slots gebundener Methoden
    nur schwach) – ``run()`` liefe nie, das Bild würde lautlos nicht
    geladen (Datei-öffnen-Bug über Button UND Drag & Drop).
    """
    monkeypatch.setattr(MainWindow, "_start_rembg_warmup", lambda self: None)
    win = MainWindow()
    ran: list[bool] = []

    def _start_without_keeping_worker_ref():
        # Der Worker existiert NUR in dieser Funktion und verlässt sie
        # nicht – exakt die Situation in _load_image_async / _run_ai.
        w = _RecordingWorker(ran)
        thread = win._worker_controller._build_thread(w, quit_on=(w.finished,))
        thread.start()
        return thread

    thread = _start_without_keeping_worker_ref()
    win._worker_controller.ai_thread = thread
    gc.collect()                       # ohne Fix: Worker hier bereits weg

    deadline = time.monotonic() + 5.0
    while not thread.isFinished() and time.monotonic() < deadline:
        qapp.processEvents()
        thread.wait(50)

    # run() lief trotz fehlender Aufrufer-Referenz → Worker überlebte.
    assert ran == [True]
    win.close()


def test_close_event_stops_running_thread(qapp, monkeypatch):
    # Warmup nicht automatisch starten (rembg evtl. nicht installiert
    # bzw. nicht-deterministisch).
    monkeypatch.setattr(MainWindow, "_start_rembg_warmup", lambda self: None)

    win = MainWindow()
    worker = _BlockingWorker(0.05)
    thread = win._worker_controller._build_thread(worker, quit_on=(worker.finished,))
    thread.start()
    win._worker_controller.ai_thread = thread
    assert thread.isRunning()

    win.close()                            # darf NICHT crashen

    assert not thread.isRunning()          # Thread sauber beendet


def test_shutdown_thread_finishes_cooperatively_within_timeout(qapp):
    controller = WorkerController(
        QObject(), shutdown_ms=17, terminate_wait_ms=23)
    fake_thread = _FakeThread([True])

    assert controller.shutdown_thread(fake_thread, "Bildladen") is True

    assert fake_thread.quit_called
    assert not fake_thread.terminate_called
    assert fake_thread.wait_timeouts == [17]


def test_shutdown_thread_uses_bounded_fallback_after_timeout(qapp):
    controller = WorkerController(
        QObject(), shutdown_ms=17, terminate_wait_ms=23)
    fake_thread = _FakeThread([False, True])

    assert controller.shutdown_thread(fake_thread, "KI") is True

    assert fake_thread.quit_called
    assert fake_thread.terminate_called
    assert fake_thread.wait_timeouts == [17, 23]


def test_shutdown_thread_reports_thread_that_survives_fallback(qapp, caplog):
    controller = WorkerController(
        QObject(), shutdown_ms=17, terminate_wait_ms=23)
    fake_thread = _FakeThread([False, False])

    assert controller.shutdown_thread(fake_thread, "rembg-Warmup") is False

    assert fake_thread.quit_called
    assert fake_thread.terminate_called
    assert fake_thread.wait_timeouts == [17, 23]
    assert "Fenster bleibt geöffnet" in caplog.text


def test_guarded_ui_callback_ignores_signal_during_shutdown(qapp):
    class _Emitter(QObject):
        finished = pyqtSignal(object)

    controller = WorkerController(QObject())
    received: list[object] = []
    emitter = _Emitter()
    emitter.finished.connect(controller._guard_ui_callback(received.append))

    controller._shutting_down = True
    emitter.finished.emit("late result")

    assert received == []


def test_close_event_noop_without_threads(qapp, monkeypatch):
    monkeypatch.setattr(MainWindow, "_start_rembg_warmup", lambda self: None)
    win = MainWindow()
    assert win._worker_controller.ai_thread is None
    win.close()                            # keine Threads -> kein Fehler


def test_cancelled_ai_shutdown_skips_result_decode(qapp):
    """Abbruch + Schließen während laufender KI: kein Ergebnis wird angewandt und
    der Shutdown ist schnell (der pollende KI-Thread bricht kooperativ ab)."""
    from tests._fakes import FakeInference

    parent = QObject()
    # Tor zu: die (gefälschte) Inferenz blockiert pollend, bis abgebrochen wird.
    fake = FakeInference(gate=threading.Event())
    controller = WorkerController(parent, shutdown_ms=1000, inference=fake)

    applied: list = []
    try:
        started = controller.start_ai(
            Image.new("RGBA", (2, 2), (1, 2, 3, 255)),
            on_done=applied.append,
            on_error=lambda _msg: None,
            on_finished=lambda: None,
        )
        assert started

        # Warten, bis der KI-Thread tatsächlich in der Inferenz pollt.
        deadline = time.monotonic() + 2.0
        while fake.infer_calls == 0 and time.monotonic() < deadline:
            qapp.processEvents()
            time.sleep(0.01)
        assert fake.infer_calls == 1

        controller.cancel_ai()
        started_at = time.monotonic()
        all_stopped = controller.shutdown_all()
        elapsed = time.monotonic() - started_at

        assert all_stopped
        assert elapsed < 0.5
        assert applied == []   # abgebrochenes Ergebnis wird nicht angewandt
    finally:
        controller.shutdown_all()


def test_ai_thread_shuts_down_cooperatively_without_terminate(qapp):
    """Kern von #270: Auch wenn die native Inferenz hängt, endet der KI-Thread
    beim Schließen KOOPERATIV – der Inferenz-Kindprozess wird gekillt, der
    pollende Thread löst sich auf. ``QThread.terminate()`` wird nie erreicht.

    Hier mit einem echten ``InferenceProcess`` über einen blockierenden
    Server-Stub (statt rembg): genau der „nicht reagierende/blockierte native
    Aufruf" aus den Akzeptanzkriterien.
    """
    from bgremover.ai_process import InferenceProcess
    from tests.test_ai_process import _blocking_server

    parent = QObject()
    inference = InferenceProcess(target=_blocking_server)
    controller = WorkerController(parent, shutdown_ms=2000, inference=inference)

    try:
        started = controller.start_ai(
            Image.new("RGBA", (2, 2), (1, 2, 3, 255)),
            on_done=lambda _img: None,
            on_error=lambda _msg: None,
            on_finished=lambda: None,
        )
        assert started
        ai_thread = controller.ai_thread
        assert ai_thread is not None

        # terminate() am konkreten Thread instrumentieren: Wird es erreicht,
        # schlägt der Test fehl – der Thread muss rein kooperativ enden.
        terminate_calls: list[bool] = []
        original_terminate = ai_thread.terminate
        ai_thread.terminate = lambda: (  # type: ignore[method-assign]
            terminate_calls.append(True) or original_terminate()
        )

        # Warten, bis der Inferenz-Kindprozess wirklich läuft und der Thread
        # in der Inferenz pollt.
        deadline = time.monotonic() + 5.0
        while not inference.is_alive and time.monotonic() < deadline:
            qapp.processEvents()
            time.sleep(0.01)
        assert inference.is_alive

        started_at = time.monotonic()
        all_stopped = controller.shutdown_all()
        elapsed = time.monotonic() - started_at

        assert all_stopped
        assert ai_thread.isFinished()
        assert terminate_calls == []          # terminate() nie erreicht
        assert not inference.is_alive          # Kindprozess hart beendet
        assert elapsed < 2.0                   # kooperativ, lange vor 2000 ms
    finally:
        inference.shutdown()
        controller.shutdown_all()
