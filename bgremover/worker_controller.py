"""QThread-Lifecycle-Verwaltung für Bildlade-, KI-, Warmup- und Flood-Fill-Worker."""
from __future__ import annotations

import contextlib
from collections.abc import Callable

import numpy as np
from PIL import Image
from PyQt6.QtCore import QObject, QThread, pyqtBoundSignal

from bgremover.constants import (
    _THREAD_SHUTDOWN_MS,
    _THREAD_TERMINATE_WAIT_MS,
    logger,
)
from bgremover.workers import (
    AIWorker,
    FloodFillWorker,
    ImageLoadWorker,
    RembgWarmupWorker,
    _Worker,
)

QuitSignals = tuple[pyqtBoundSignal, ...]


class WorkerController:
    """Besitzt und verwaltet Hintergrund-Worker-Threads und ihre Shutdown-Semantik."""

    def __init__(
        self,
        parent: QObject,
        shutdown_ms: int = _THREAD_SHUTDOWN_MS,
        terminate_wait_ms: int = _THREAD_TERMINATE_WAIT_MS,
    ) -> None:
        self._parent = parent
        self._shutdown_ms = shutdown_ms
        self._terminate_wait_ms = terminate_wait_ms
        self._shutting_down = False
        self.load_thread: QThread | None = None
        self.ai_thread: QThread | None = None
        self.ai_worker: AIWorker | None = None
        self.warmup_thread: QThread | None = None
        self.warmup_done = False
        self.flood_fill_thread: QThread | None = None
        self.flood_fill_worker: FloodFillWorker | None = None
        # Starke Python-Referenz auf jeden aktiven Worker. PyQt verbindet
        # Slots gebundener Methoden nur schwach: ohne diese Liste sammelt
        # CPython den Worker direkt nach _build_thread ein und run() liefe
        # nie. Frueher hing der Worker per setattr(thread, "_worker", w)
        # am QThread – das war ein versteckter Vertrag; die explizite Liste
        # macht Eigentumsverhaeltnisse und Cleanup sichtbar.
        self._workers: list[QObject] = []

    def _guard_ui_callback(
        self, callback: Callable[..., None],
    ) -> Callable[..., None]:
        """Unterdrückt verspätete Worker-Callbacks während des Fensterabbaus."""
        def guarded(*args: object) -> None:
            if not self._shutting_down:
                callback(*args)

        return guarded

    @property
    def is_loading(self) -> bool:
        return self.load_thread is not None and self.load_thread.isRunning()

    @property
    def is_ai_running(self) -> bool:
        return self.ai_thread is not None and self.ai_thread.isRunning()

    @property
    def is_flood_fill_running(self) -> bool:
        return (self.flood_fill_thread is not None
                and self.flood_fill_thread.isRunning())

    def _build_thread(
        self,
        worker: _Worker,
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
        """Startet asynchrones Bildladen; gibt False zurück, wenn bereits ein Ladevorgang läuft."""
        if self.is_loading:
            return False
        worker = ImageLoadWorker(path)
        worker.finished.connect(self._guard_ui_callback(on_loaded))
        worker.error.connect(self._guard_ui_callback(on_error))
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

    def start_warmup(
        self,
        on_finished: Callable[[], None],
        on_error: Callable[[str], None] | None = None,
    ) -> bool:
        """Startet den rembg-Warmup; gibt False zurück, wenn der Warmup bereits läuft."""
        if self.warmup_thread is not None and self.warmup_thread.isRunning():
            return False
        worker = RembgWarmupWorker()
        if on_error is not None:
            # ``error`` feuert nur im Fehlerfall (vor dem finished/Lifecycle).
            # So kann der Aufrufer einen fehlgeschlagenen Warmup von einem
            # erfolgreichen unterscheiden, statt blind „KI bereit" zu melden.
            worker.error.connect(self._guard_ui_callback(on_error))
        guarded_on_finished = self._guard_ui_callback(on_finished)
        thread = self._build_thread(
            worker,
            quit_on=(worker.finished,),
            on_finished=lambda: self._finish_warmup_thread(guarded_on_finished),
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
        """Startet die KI-Hintergrundentfernung; gibt False zurück, wenn die KI bereits läuft."""
        if self.is_ai_running:
            return False
        worker = AIWorker(image.copy())
        worker.finished.connect(self._guard_ui_callback(on_done))
        worker.error.connect(self._guard_ui_callback(on_error))
        guarded_on_finished = self._guard_ui_callback(on_finished)
        self.ai_worker = worker
        thread = self._build_thread(
            worker,
            # ``done`` feuert über _always_finished IMMER (Erfolg, Fehler,
            # Abbruch). Nur deshalb quittet der Thread auch nach cancel_ai(),
            # bei dem weder ``finished`` noch ``error`` emittiert wird.
            quit_on=(worker.done,),
            on_finished=lambda: self._finish_ai_thread(guarded_on_finished),
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

    def start_flood_fill(
        self,
        arr: np.ndarray,
        x: int,
        y: int,
        tolerance: int,
        on_done: Callable[[np.ndarray], None],
        on_error: Callable[[str], None],
    ) -> bool:
        """Startet den asynchronen Zauberstab-Flood-Fill; gibt False zurück, wenn bereits einer läuft."""
        if self.is_flood_fill_running:
            return False
        worker = FloodFillWorker(arr, x, y, tolerance)
        worker.finished.connect(self._guard_ui_callback(on_done))
        worker.error.connect(self._guard_ui_callback(on_error))
        self.flood_fill_worker = worker
        thread = self._build_thread(
            worker,
            # ``done`` feuert über _always_finished IMMER (Erfolg, Fehler,
            # Abbruch). Nur deshalb quittet der Thread auch nach cancel().
            quit_on=(worker.done,),
            on_finished=self._finish_flood_fill_thread,
        )
        self.flood_fill_thread = thread
        thread.start()
        return True

    def cancel_flood_fill(self) -> None:
        """Markiert einen laufenden Flood-Fill als abgebrochen.

        Der Worker bricht die Berechnung beim nächsten Abbruch-Check ab und
        emittiert kein Ergebnis; der Thread-Lifecycle läuft über ``done``.
        """
        if self.flood_fill_worker is not None:
            self.flood_fill_worker.cancel()

    def _finish_flood_fill_thread(self) -> None:
        self.flood_fill_thread = None
        self.flood_fill_worker = None

    def shutdown_all(self) -> bool:
        """Stoppt alle Worker; False hält das besitzende Fenster am Leben."""
        self._shutting_down = True
        self.cancel_ai()
        self.cancel_flood_fill()
        shutdowns = (
            ("ai_thread", self.shutdown_thread(self.ai_thread, "KI")),
            ("load_thread", self.shutdown_thread(self.load_thread, "Bildladen")),
            (
                "warmup_thread",
                self.shutdown_thread(self.warmup_thread, "rembg-Warmup"),
            ),
            (
                "flood_fill_thread",
                self.shutdown_thread(self.flood_fill_thread, "Flood-Fill"),
            ),
        )
        # ``thread.finished``-Slots werden beim blockierenden wait() nicht
        # zwingend sofort im Besitzer-Thread zugestellt. Nach dem synchronen
        # Shutdown dürfen deshalb für beendete Threads keine stale
        # QThread-Referenzen verbleiben. Nicht beendete Threads müssen dagegen
        # referenziert bleiben, solange das Fenster weiterlebt.
        for attr_name, stopped in shutdowns:
            if stopped:
                setattr(self, attr_name, None)
        if shutdowns[0][1]:
            self.ai_worker = None
        if shutdowns[3][1]:
            self.flood_fill_worker = None

        all_stopped = all(stopped for _, stopped in shutdowns)
        if not all_stopped:
            # Das Fenster bleibt offen; reguläre Worker-Callbacks dürfen
            # deshalb bei einem späteren Abschluss wieder die lebende UI
            # erreichen.
            self._shutting_down = False
        return all_stopped

    def shutdown_thread(self, thread: QThread | None, name: str) -> bool:
        """Beendet *thread* innerhalb zweier fester Zeitgrenzen."""
        if thread is None or not thread.isRunning():
            return True
        thread.quit()
        if thread.wait(self._shutdown_ms):
            return True

        logger.warning(
            "Thread '%s' reagierte nach %d ms nicht; begrenzter "
            "Notfallabbruch per QThread.terminate()",
            name,
            self._shutdown_ms,
        )
        thread.terminate()
        if thread.wait(self._terminate_wait_ms):
            return True

        logger.critical(
            "Thread '%s' läuft trotz terminate() nach weiteren %d ms; "
            "das Fenster bleibt geöffnet",
            name,
            self._terminate_wait_ms,
        )
        return False
