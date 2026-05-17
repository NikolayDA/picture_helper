"""Test für sauberes Thread-Shutdown beim Schliessen des Fensters.

Headless (offscreen): startet einen künstlich blockierenden Worker über
den echten ``_launch_worker``-Pfad, schliesst das Fenster und prüft, dass
``closeEvent`` den Thread sauber stoppt, statt zu crashen (Regression
gegen „QThread: Destroyed while thread is still running“).
"""
import gc
import time

from PyQt6.QtCore import QObject, pyqtSignal

import BgRemover
from BgRemover import MainWindow


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


def test_launch_worker_keeps_worker_alive_without_caller_ref(qapp, monkeypatch):
    """Regression: ``_launch_worker`` muss eine starke Referenz auf den
    Worker halten. Sonst sammelt CPython ihn ein, sobald der Aufrufer
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
        return win._launch_worker(w, quit_on=(w.finished,))

    win._ai_thread = _start_without_keeping_worker_ref()
    gc.collect()                       # ohne Fix: Worker hier bereits weg

    deadline = time.monotonic() + 5.0
    while not win._ai_thread.isFinished() and time.monotonic() < deadline:
        qapp.processEvents()
        win._ai_thread.wait(50)

    # run() lief trotz fehlender Aufrufer-Referenz → Worker überlebte.
    assert ran == [True]
    win.close()


def test_close_event_stops_running_thread(qapp, monkeypatch):
    # Warmup nicht automatisch starten (rembg evtl. nicht installiert
    # bzw. nicht-deterministisch).
    monkeypatch.setattr(MainWindow, "_start_rembg_warmup", lambda self: None)
    # Kurzes Timeout: Test soll schnell sein und den terminate()-
    # Fallback-Pfad zuverlässig erzwingen.
    monkeypatch.setattr(BgRemover, "_THREAD_SHUTDOWN_MS", 200)

    win = MainWindow()
    worker = _BlockingWorker(5.0)          # läuft länger als Timeout
    win._ai_thread = win._launch_worker(worker, quit_on=(worker.finished,))
    assert win._ai_thread.isRunning()

    win.close()                            # darf NICHT crashen

    assert not win._ai_thread.isRunning()  # Thread sauber beendet


def test_close_event_noop_without_threads(qapp, monkeypatch):
    monkeypatch.setattr(MainWindow, "_start_rembg_warmup", lambda self: None)
    win = MainWindow()
    assert win._ai_thread is None
    win.close()                            # keine Threads -> kein Fehler
