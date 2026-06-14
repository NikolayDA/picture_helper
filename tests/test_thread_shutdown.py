"""Test für sauberes Thread-Shutdown beim Schliessen des Fensters.

Headless (offscreen): startet einen künstlich blockierenden Worker über
den echten ``WorkerController._build_thread``-Pfad, schliesst das Fenster und
prüft, dass ``closeEvent`` den Thread sauber stoppt, statt zu crashen
(Regression gegen „QThread: Destroyed while thread is still running“).
"""
import gc
import threading
import time
from unittest.mock import patch

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


class _FakeStuckThread:
    def __init__(self) -> None:
        self.quit_called = False
        self.terminate_called = False
        self.wait_calls = 0

    def isRunning(self) -> bool:
        return True

    def quit(self) -> None:
        self.quit_called = True

    def wait(self, _ms=None) -> bool:
        self.wait_calls += 1
        return self.terminate_called

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


def test_shutdown_thread_terminates_after_timeout(qapp, monkeypatch):
    monkeypatch.setattr(MainWindow, "_start_rembg_warmup", lambda self: None)
    win = MainWindow()
    fake_thread = _FakeStuckThread()

    win._worker_controller.shutdown_thread(fake_thread, "KI")

    assert fake_thread.quit_called
    assert fake_thread.terminate_called
    assert fake_thread.wait_calls == 2
    win.close()


def test_close_event_noop_without_threads(qapp, monkeypatch):
    monkeypatch.setattr(MainWindow, "_start_rembg_warmup", lambda self: None)
    win = MainWindow()
    assert win._worker_controller.ai_thread is None
    win.close()                            # keine Threads -> kein Fehler


def test_cancelled_ai_shutdown_skips_result_decode(qapp):
    # Direkt am WorkerController: das kurze Shutdown-Timeout kommt über den
    # öffentlichen Konstruktor-Parameter statt durch Schreiben des privaten
    # ``_shutdown_ms`` auf dem Controller eines MainWindow.
    parent = QObject()
    controller = WorkerController(parent, shutdown_ms=1000)
    rembg_started = threading.Event()
    rembg_can_return = threading.Event()

    def _fake_rembg(_data, session=None):
        rembg_started.set()
        assert rembg_can_return.wait(2.0)
        return b"result png"

    def _slow_open(_data):
        time.sleep(1.5)
        return Image.new("RGBA", (2, 2), (0, 0, 0, 0))

    try:
        with (
            patch("bgremover.workers.rembg_remove", side_effect=_fake_rembg, create=True),
            patch("bgremover.workers.Image.open", side_effect=_slow_open),
        ):
            started = controller.start_ai(
                Image.new("RGBA", (2, 2), (1, 2, 3, 255)),
                on_done=lambda _img: None,
                on_error=lambda _msg: None,
                on_finished=lambda: None,
            )
            assert started

            deadline = time.monotonic() + 2.0
            while not rembg_started.is_set() and time.monotonic() < deadline:
                qapp.processEvents()
                time.sleep(0.01)
            assert rembg_started.is_set()

            controller.cancel_ai()
            rembg_can_return.set()
            started_at = time.monotonic()
            controller.shutdown_all()
            elapsed = time.monotonic() - started_at

        assert elapsed < 0.5
    finally:
        rembg_can_return.set()
        controller.shutdown_all()
