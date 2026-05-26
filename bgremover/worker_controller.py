"""QThread lifecycle management for image load, AI, and warmup workers."""
from __future__ import annotations

import contextlib
from collections.abc import Callable

from PIL import Image
from PyQt6.QtCore import QObject, QThread, pyqtBoundSignal

from bgremover.constants import _THREAD_SHUTDOWN_MS, logger
from bgremover.workers import AIWorker, ImageLoadWorker, RembgWarmupWorker, _Worker

QuitSignals = tuple[pyqtBoundSignal, ...]


class WorkerController:
    """Owns background worker threads and their shutdown semantics."""

    def __init__(self, parent: QObject, shutdown_ms: int = _THREAD_SHUTDOWN_MS) -> None:
        self._parent = parent
        self._shutdown_ms = shutdown_ms
        self.load_thread: QThread | None = None
        self.ai_thread: QThread | None = None
        self.ai_worker: AIWorker | None = None
        self.warmup_thread: QThread | None = None
        self.warmup_done = False
        # Starke Python-Referenz auf jeden aktiven Worker. PyQt verbindet
        # Slots gebundener Methoden nur schwach: ohne diese Liste sammelt
        # CPython den Worker direkt nach _build_thread ein und run() liefe
        # nie. Frueher hing der Worker per setattr(thread, "_worker", w)
        # am QThread – das war ein versteckter Vertrag; die explizite Liste
        # macht Eigentumsverhaeltnisse und Cleanup sichtbar.
        self._workers: list[QObject] = []

    @property
    def is_loading(self) -> bool:
        return self.load_thread is not None and self.load_thread.isRunning()

    @property
    def is_ai_running(self) -> bool:
        return self.ai_thread is not None and self.ai_thread.isRunning()

    def launch_worker(
        self,
        worker: _Worker | RembgWarmupWorker,
        quit_on: QuitSignals,
        on_finished: Callable[[], None] | None = None,
    ) -> QThread:
        """Start *worker* in a new QThread and return the thread."""
        thread = self._build_thread(worker, quit_on, on_finished)
        thread.start()
        return thread

    def _build_thread(
        self,
        worker: _Worker | RembgWarmupWorker,
        quit_on: QuitSignals,
        on_finished: Callable[[], None] | None = None,
    ) -> QThread:
        thread = QThread(self._parent)
        self._workers.append(worker)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        for sig in quit_on:
            sig.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda w=worker: self._release_worker(w))
        if on_finished is not None:
            thread.finished.connect(on_finished)
        return thread

    def _release_worker(self, worker: QObject) -> None:
        """Gibt die Python-Referenz auf *worker* nach Threadende frei."""
        # Doppelt verbundener Slot oder shutdown_all-Race – idempotent
        # halten, nicht den finished-Pfad mit einer Exception belasten.
        with contextlib.suppress(ValueError):
            self._workers.remove(worker)

    def start_image_load(
        self,
        path: str,
        on_loaded: Callable[[object, str], None],
        on_error: Callable[[str], None],
    ) -> bool:
        """Start asynchronous image loading; return False if a load is active."""
        if self.is_loading:
            return False
        worker = ImageLoadWorker(path)
        worker.finished.connect(on_loaded)
        worker.error.connect(on_error)
        thread = self._build_thread(
            worker,
            quit_on=(worker.finished, worker.error),
            on_finished=self._finish_load_thread,
        )
        self.load_thread = thread
        thread.start()
        return True

    def _finish_load_thread(self) -> None:
        self.load_thread = None

    def start_warmup(self, on_finished: Callable[[], None]) -> bool:
        """Start rembg warmup; return False if warmup is already active."""
        if self.warmup_thread is not None and self.warmup_thread.isRunning():
            return False
        worker = RembgWarmupWorker()
        thread = self._build_thread(
            worker,
            quit_on=(worker.finished,),
            on_finished=lambda: self._finish_warmup_thread(on_finished),
        )
        self.warmup_thread = thread
        thread.start()
        return True

    def _finish_warmup_thread(self, on_finished: Callable[[], None]) -> None:
        self.warmup_done = True
        self.warmup_thread = None
        on_finished()

    def start_ai(
        self,
        image: Image.Image,
        on_done: Callable[[Image.Image], None],
        on_error: Callable[[str], None],
        on_finished: Callable[[], None],
    ) -> bool:
        """Start AI background removal; return False if AI is already active."""
        if self.is_ai_running:
            return False
        worker = AIWorker(image.copy())
        worker.finished.connect(on_done)
        worker.error.connect(on_error)
        self.ai_worker = worker
        thread = self._build_thread(
            worker,
            quit_on=(worker.finished, worker.error),
            on_finished=lambda: self._finish_ai_thread(on_finished),
        )
        self.ai_thread = thread
        thread.start()
        return True

    def _finish_ai_thread(self, on_finished: Callable[[], None]) -> None:
        self.ai_thread = None
        self.ai_worker = None
        on_finished()

    def cancel_ai(self) -> None:
        """Markiert den laufenden AI-Worker als abgebrochen.

        Der Thread läuft die aktuelle rembg-Berechnung noch zu Ende, aber
        das Ergebnis wird nicht emittiert.
        """
        if self.ai_worker is not None:
            self.ai_worker.cancel()

    def shutdown_all(self) -> None:
        self.cancel_ai()
        self.shutdown_thread(self.ai_thread, "KI")
        self.shutdown_thread(self.load_thread, "Bildladen")
        self.shutdown_thread(self.warmup_thread, "rembg-Warmup")

    def shutdown_thread(self, thread: QThread | None, name: str) -> None:
        """Stop *thread* cleanly before the owning window is destroyed."""
        if thread is None or not thread.isRunning():
            return
        thread.quit()
        if not thread.wait(self._shutdown_ms):
            logger.warning(
                "Thread '%s' reagierte nicht – wird hart beendet", name)
            thread.terminate()
            thread.wait()
