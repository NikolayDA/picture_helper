"""QThread-Lifecycle-Verwaltung für Bildlade-, KI-, Warmup- und Flood-Fill-Worker."""
from __future__ import annotations

import contextlib
from collections.abc import Callable

import numpy as np
from PIL import Image
from PyQt6.QtCore import QObject, QThread, pyqtBoundSignal

from bgremover.ai_process import InferenceProcess
from bgremover.app_update import UpdateCheckResult
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
    UpdateCheckWorker,
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
        inference: InferenceProcess | None = None,
    ) -> None:
        self._parent = parent
        self._shutdown_ms = shutdown_ms
        self._terminate_wait_ms = terminate_wait_ms
        self._shutting_down = False
        # Inferenz-Kindprozess (rembg/ONNX), gemeinsam von Warmup und KI-Worker
        # genutzt. Die Konstruktion startet noch keinen Prozess – das passiert
        # erst beim ersten Warmup/KI-Aufruf. Injizierbar für Tests.
        self._inference = inference or InferenceProcess()
        self.load_thread: QThread | None = None
        self.ai_thread: QThread | None = None
        self.ai_worker: AIWorker | None = None
        self.warmup_thread: QThread | None = None
        self.warmup_worker: RembgWarmupWorker | None = None
        self.warmup_done = False
        self.update_check_thread: QThread | None = None
        self.update_check_worker: UpdateCheckWorker | None = None
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
    def is_warmup_running(self) -> bool:
        return self.warmup_thread is not None and self.warmup_thread.isRunning()

    @property
    def is_update_check_running(self) -> bool:
        return self.update_check_thread is not None and self.update_check_thread.isRunning()

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
        on_finished: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_cancelled: Callable[[], None] | None = None,
        on_success: Callable[[], None] | None = None,
    ) -> bool:
        """Startet den rembg-Warmup oder hängt sich an einen laufenden an (#570).

        Läuft bereits ein Warmup (der automatische Start-Warmup oder ein
        vorheriger Download-Versuch aus dem KI-Modell-Dialog), werden die
        übergebenen Callbacks zusätzlich an den *laufenden* Worker gehängt,
        statt einen zweiten Thread/Prozess zu starten – beide Aufrufer werden
        über denselben Abschluss benachrichtigt, und es läuft nie mehr als
        eine Modellinitialisierung gleichzeitig. Gibt in beiden Fällen True
        zurück: der Aufrufer wird garantiert benachrichtigt, unabhängig davon,
        ob dieser Aufruf den Warmup gestartet oder sich nur angehängt hat.

        ``on_finished`` feuert **immer** (Erfolg/Fehler/Abbruch) – für
        Aufrufer wie den Start-Warmup, die unabhängig vom Ausgang aufräumen
        müssen (z. B. den KI-Button wieder freigeben). ``on_success`` feuert
        **nur** bei Erfolg; ein Aufrufer, der bei Abbruch/Fehler etwas
        anderes als bei Erfolg zeigen will (z. B. der KI-Modell-Dialog), darf
        dafür NICHT ``on_finished`` verwenden – das würde einen Abbruch/Fehler
        nach der Fehler-/Abbruch-Meldung sofort wieder als Erfolg überschreiben.
        """
        if self.is_warmup_running:
            worker = self.warmup_worker
            assert worker is not None
            if on_finished is not None:
                worker.done.connect(self._guard_ui_callback(on_finished))
            if on_success is not None:
                worker.finished.connect(self._guard_ui_callback(on_success))
            if on_error is not None:
                worker.error.connect(self._guard_ui_callback(on_error))
            if on_cancelled is not None:
                worker.cancelled.connect(self._guard_ui_callback(on_cancelled))
            if self.is_warmup_running:
                return True
            # Race (Review-Befund #574): der Warmup kann zwischen der
            # obigen Prüfung und dem Verbinden auf dem Worker-Thread bereits
            # abgeschlossen sein – Qt liefert kein „Signal-Replay" für einen
            # Emit, der vor dem Connect passierte. Statt diesen Aufrufer
            # dauerhaft ohne Benachrichtigung hängen zu lassen, startet ein
            # frischer Warmup neu und garantiert ihm so einen Abschluss.

        return self._start_new_warmup_thread(on_finished, on_error, on_cancelled, on_success)

    def _start_new_warmup_thread(
        self,
        on_finished: Callable[[], None] | None,
        on_error: Callable[[str], None] | None,
        on_cancelled: Callable[[], None] | None,
        on_success: Callable[[], None] | None,
    ) -> bool:
        worker = RembgWarmupWorker(self._inference)
        if on_success is not None:
            # ``finished`` feuert nur bei Erfolg – klar getrennt vom
            # Lifecycle-Signal ``done`` (siehe ``start_warmup``-Docstring).
            worker.finished.connect(self._guard_ui_callback(on_success))
        if on_error is not None:
            # ``error`` feuert nur im Fehlerfall (vor dem Lifecycle-Ende).
            # So kann der Aufrufer einen fehlgeschlagenen Warmup von einem
            # erfolgreichen unterscheiden, statt blind „KI bereit" zu melden.
            worker.error.connect(self._guard_ui_callback(on_error))
        if on_cancelled is not None:
            worker.cancelled.connect(self._guard_ui_callback(on_cancelled))
        guarded_on_finished = self._guard_ui_callback(on_finished) if on_finished else None
        thread = self._build_thread(
            worker,
            quit_on=(worker.done,),
            on_finished=lambda: self._finish_warmup_thread(guarded_on_finished),
        )
        self.warmup_thread = thread
        self.warmup_worker = worker
        thread.start()
        return True

    def _finish_warmup_thread(self, on_finished: Callable[[], None] | None) -> None:
        self.warmup_done = True
        self.warmup_thread = None
        self.warmup_worker = None
        if on_finished is not None:
            on_finished()

    def cancel_warmup(self) -> None:
        """Markiert den laufenden rembg-Warmup als abgebrochen (#570).

        Der pollende Worker-Thread bemerkt das kooperative Abbruch-Flag,
        beendet den Inferenz-Kindprozess (stoppt den laufenden Modell-
        Download/die Probe-Inferenz) und kehrt zurück, ohne ``finished``
        oder ``error`` zu emittieren – nur ``cancelled`` und (immer)
        ``done``. Ohne laufenden Warmup ein No-op.
        """
        if self.warmup_worker is not None:
            self.warmup_worker.cancel()

    def start_update_check(
        self,
        current_version: str,
        on_result: Callable[[UpdateCheckResult], None],
    ) -> bool:
        """Startet den Update-Check oder hängt sich an einen laufenden an.

        Läuft bereits ein Check (z. B. der stille automatische Start-Check,
        #566), wird ``on_result`` zusätzlich an dessen Ergebnis gehängt,
        statt einen zweiten Netzwerkaufruf zu starten – ein manueller
        „Nach Updates suchen…"-Klick während eines laufenden automatischen
        Checks bekommt so trotzdem seinen Ergebnisdialog, statt nur
        „läuft bereits" zu sehen (Review-Befund #574). Gibt immer True
        zurück.
        """
        if self.is_update_check_running:
            worker = self.update_check_worker
            assert worker is not None
            worker.finished.connect(self._guard_ui_callback(on_result))
            if self.is_update_check_running:
                return True
            # Race (analog start_warmup): der Check kann zwischen der
            # Pruefung und dem Verbinden bereits abgeschlossen sein.

        return self._start_new_update_check_thread(current_version, on_result)

    def _start_new_update_check_thread(
        self,
        current_version: str,
        on_result: Callable[[UpdateCheckResult], None],
    ) -> bool:
        worker = UpdateCheckWorker(current_version)
        guarded_on_result = self._guard_ui_callback(on_result)
        worker.finished.connect(guarded_on_result)
        thread = self._build_thread(
            worker,
            quit_on=(worker.finished,),
            on_finished=self._finish_update_check_thread,
        )
        self.update_check_thread = thread
        self.update_check_worker = worker
        thread.start()
        return True

    def _finish_update_check_thread(self) -> None:
        self.update_check_thread = None
        self.update_check_worker = None

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
        worker = AIWorker(image.copy(), self._inference)
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

        Der pollende Worker-Thread bemerkt das Flag, beendet den
        Inferenz-Kindprozess (stoppt die laufende ONNX-Berechnung und gibt deren
        Ressourcen frei) und kehrt zurück, ohne ein Ergebnis zu emittieren.
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
        self.cancel_warmup()
        # Laufende, nicht unterbrechbare Inferenz sofort entwerten: killt den
        # Inferenz-Kindprozess, sodass der pollende KI-Thread seinen Loop
        # verlässt und kooperativ endet – ohne QThread.terminate() für die KI.
        # Aus dem UI-Thread sicher: ändert nur den Prozess, nicht die
        # Python-Handles (die räumt der KI-Thread bzw. shutdown() unten ab).
        self._inference.request_stop()
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
            (
                "update_check_thread",
                self.shutdown_thread(self.update_check_thread, "Update-Check"),
            ),
        )
        # Inferenz-Kindprozess endgültig beenden und einsammeln. Die
        # KI-/Warmup-Threads sind oben bereits beendet (oder abgebrochen), der
        # Aufruf konkurriert daher nicht mehr mit einem pollenden Worker.
        self._inference.shutdown()
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
        if shutdowns[2][1]:
            self.warmup_worker = None
        if shutdowns[3][1]:
            self.flood_fill_worker = None
        if shutdowns[4][1]:
            self.update_check_worker = None

        all_stopped = all(stopped for _, stopped in shutdowns)
        if not all_stopped:
            # Das Fenster bleibt offen; reguläre Worker-Callbacks dürfen
            # deshalb bei einem späteren Abschluss wieder die lebende UI
            # erreichen.
            self._shutting_down = False
        return all_stopped

    def shutdown_thread(self, thread: QThread | None, name: str) -> bool:
        """Beendet *thread* innerhalb zweier fester Zeitgrenzen.

        Alle Worker sind kooperativ stoppbar: Bildladen ist begrenzte I/O,
        Flood-Fill prüft ein Abbruch-Flag, und die KI pollt nur auf den
        Inferenz-Kindprozess (die nicht unterbrechbare ONNX-Inferenz lebt seit
        #270 nicht mehr im Thread). Der kooperative ``quit()``/``wait()`` greift
        daher; ``terminate()`` bleibt nur ein begrenzter Notfall für einen
        wider Erwarten hängenden Thread. Anders als früher kann ``terminate()``
        hier keinen nativen ONNX-Zustand mehr zerreißen – der liegt im
        Kindprozess, der separat hart beendet wird.
        """
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
