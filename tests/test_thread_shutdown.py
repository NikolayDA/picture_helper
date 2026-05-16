"""Test für sauberes Thread-Shutdown beim Schliessen des Fensters.

Headless (offscreen): startet einen künstlich blockierenden Worker über
den echten ``_launch_worker``-Pfad, schliesst das Fenster und prüft, dass
``closeEvent`` den Thread sauber stoppt, statt zu crashen (Regression
gegen „QThread: Destroyed while thread is still running“).
"""
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
