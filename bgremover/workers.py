"""Hintergrund-Worker (eigene QThreads).

Die KI-/rembg-Inferenz läuft NICHT mehr im Worker-Thread, sondern in einem
eigenen Prozess (``bgremover.ai_process``): Eine nicht unterbrechbare native
ONNX-Inferenz darf den GUI-Prozess beim Schließen nicht per
``QThread.terminate()`` gefährden (Befund #270). ``AIWorker`` und
``RembgWarmupWorker`` sprechen nur den ``InferenceProcess`` an und pollen auf
das Ergebnis – ein kooperativ unterbrechbarer Loop.
"""
from __future__ import annotations

import importlib.util
import io

import numpy as np
from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal

from bgremover.ai_process import InferenceCancelled, InferenceProcess
from bgremover.app_update import UpdateCheckResult, UpdateStatus, check_for_update
from bgremover.constants import logger
from bgremover.image_loading import open_validated_image
from bgremover.image_utils import flood_fill

# rembg (zieht onnxruntime) wird bewusst NICHT auf Modulebene importiert: der
# Import kostet beim Start mehrere Sekunden, und ``main_window`` lädt ``workers``
# für ``REMBG_AVAILABLE`` schon vor dem ersten Fensterzeichnen. ``find_spec``
# prüft nur die *Installation* (ohne den teuren Import); der echte Import läuft
# lazy im Inferenz-Kindprozess (``ai_process``), wo ein defektes
# onnxruntime-Backend als normaler Worker-Fehler gemeldet wird statt den Start
# zu verzögern.
try:
    REMBG_AVAILABLE = importlib.util.find_spec("rembg") is not None
except (ImportError, ValueError):
    REMBG_AVAILABLE = False


class _Worker(QObject):
    """Basisklasse für Hintergrund-Worker.

    Kapselt den in mehreren Workern identischen Ablauf
    ``try: _work() / except Exception: logger.exception(); error.emit()``.
    Unterklassen deklarieren ihr eigenes ``finished``-Signal (die
    Signaturen unterscheiden sich je Worker) und implementieren ``_work``.
    ``_always_finished`` ist ein Hook, der im ``finally``-Zweig nach jedem
    Lauf läuft – Default ist no-op; der Warmup-Worker überschreibt ihn,
    um sein parameterloses ``finished``-Signal auch im Fehlerfall zu feuern.
    """
    error = pyqtSignal(str)
    _error_context = "Worker-Fehler"

    def run(self) -> None:
        try:
            self._work()
        except Exception as e:
            logger.exception(self._error_context)
            self.error.emit(f"{type(e).__name__}: {e}")
        finally:
            self._always_finished()

    def _work(self) -> None:
        raise NotImplementedError

    def _always_finished(self) -> None:
        """Hook für Worker, die ``finished`` unabhängig vom Ausgang feuern."""


class AIWorker(_Worker):
    """Entfernt den Hintergrund per rembg über den Inferenz-Kindprozess.

    Der Worker selbst rechnet nicht: Er reicht das Bild als PNG an den
    ``InferenceProcess`` weiter und pollt auf das Ergebnis. Die nicht
    unterbrechbare ONNX-Inferenz läuft im Kindprozess, sodass ``cancel()``
    bzw. das Schließen sie per Prozess-Kill stoppen können – ohne
    ``QThread.terminate()`` und ohne den GUI-Prozess zu gefährden (#270).

    ``finished`` trägt das Ergebnisbild und feuert nur im Erfolgsfall.
    ``done`` ist parameterlos und feuert über ``_always_finished``
    **immer** – auch bei Abbruch und Fehler – und dient dem
    WorkerController als Quit-Signal für den Thread-Lifecycle. Ohne ein
    garantiert feuerndes Abschluss-Signal liefe der QThread nach einem
    ``cancel()`` weiter (``_work`` kehrt dann ohne ``finished``/``error``
    zurück): ``ai_thread``/``ai_worker`` blieben gesetzt, ``on_finished``
    liefe nie und der KI-Button bliebe die restliche Session deaktiviert.
    """
    finished = pyqtSignal(object)   # PIL Image – nur bei Erfolg
    done = pyqtSignal()             # immer – Thread-Abschluss (auch Abbruch/Fehler)
    _error_context = "rembg-Fehler"

    def __init__(self, pil_image: Image.Image, inference: InferenceProcess) -> None:
        super().__init__()
        self._img = pil_image
        self._inference = inference
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def _work(self) -> None:
        buf = io.BytesIO()
        self._img.save(buf, format="PNG")
        try:
            result_bytes = self._inference.infer(
                buf.getvalue(), should_cancel=lambda: self._cancelled,
            )
        except InferenceCancelled:
            # Regulärer Abbruch: kein ``finished``/``error``; ``done`` feuert
            # über ``_always_finished`` und schließt den Lifecycle ab.
            return
        if self._cancelled:
            return
        result = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
        self.finished.emit(result)

    def _always_finished(self) -> None:
        self.done.emit()


class RembgWarmupWorker(_Worker):
    """Initialisiert den Inferenz-Kindprozess samt rembg-Session einmalig.

    Ohne diesen Warmup blockt der erste KI-Klick rund zehn Sekunden, weil
    rembg sein ONNX-Modell sonst erst dann lädt. Der Warmup startet den
    ``InferenceProcess`` und lässt ihn die Session genau einmal erzeugen (der
    teure Schritt) und eine kleine Probe-Inferenz ausführen; jeder spätere
    ``AIWorker`` nutzt dieselbe Session im selben Prozess wieder (#229).

    ``finished`` feuert nur bei Erfolg; ``done`` feuert über
    ``_always_finished`` **immer** (Erfolg, Fehler, Abbruch) und ist das
    Abschluss-Signal für den WorkerController-Thread-Lifecycle (analog
    ``AIWorker``/``FloodFillWorker``, #270). Ein fehlgeschlagener Warmup
    meldet zusätzlich ``error`` (Import-/Init-Fehler aus dem Kindprozess).
    ``cancel()`` markiert ein Flag, das ``InferenceProcess.warmup`` über
    ``should_cancel`` kooperativ prüft: ein Abbruch beendet den
    Inferenz-Kindprozess und emittiert **weder** ``finished`` noch ``error``,
    sondern das dedizierte ``cancelled``-Signal – der KI-Modell-Dialog (#569)
    kann den Modell-Download darüber sauber abbrechen, ohne dass ein
    Aufrufer den Abbruch fälschlich als „KI bereit" oder als Fehler deutet
    (#570).
    """
    finished = pyqtSignal()    # nur bei Erfolg
    cancelled = pyqtSignal()   # nur bei Abbruch
    done = pyqtSignal()        # immer – Thread-Abschluss (auch Fehler/Abbruch)
    _error_context = "rembg-Warmup"

    def __init__(self, inference: InferenceProcess) -> None:
        super().__init__()
        self._inference = inference
        self._cancelled_flag = False

    def cancel(self) -> None:
        self._cancelled_flag = True

    def _work(self) -> None:
        try:
            self._inference.warmup(should_cancel=lambda: self._cancelled_flag)
        except InferenceCancelled:
            self.cancelled.emit()
            return
        logger.info("rembg-Warmup abgeschlossen")
        self.finished.emit()

    def _always_finished(self) -> None:
        self.done.emit()


class UpdateCheckWorker(_Worker):
    """Fragt im Hintergrund die neueste GitHub-Release ab (#565).

    ``check_for_update`` fängt bereits jeden Netzwerk-/Parsing-Fehler intern
    ab und liefert nie eine Exception – ``finished`` feuert deshalb über
    ``_always_finished`` immer mit einem gültigen ``UpdateCheckResult``
    (nötigenfalls ``CHECK_FAILED``, falls die Basisklasse doch einmal einen
    unerwarteten Fehler abfängt).
    """
    finished = pyqtSignal(object)   # UpdateCheckResult – immer
    _error_context = "Update-Check"

    def __init__(self, current_version: str, timeout: float = 5.0) -> None:
        super().__init__()
        self._current_version = current_version
        self._timeout = timeout
        # Defensiver Startwert, falls die Basisklasse doch einen unerwarteten
        # Fehler aus ``_work`` abfaengt, bevor ``self._result`` gesetzt wird.
        self._result = UpdateCheckResult(status=UpdateStatus.CHECK_FAILED)

    def _work(self) -> None:
        self._result = check_for_update(self._current_version, timeout=self._timeout)

    def _always_finished(self) -> None:
        self.finished.emit(self._result)


class ImageLoadWorker(_Worker):
    """Lädt + EXIF-orientiert ein Bild im Hintergrund.

    Vermeidet UI-Freeze bei großen Fotos.
    """
    finished = pyqtSignal(object, str)   # (PIL.Image, original_path)
    _error_context = "Bildladen fehlgeschlagen"

    def __init__(self, path: str) -> None:
        super().__init__()
        self._path = path

    def _work(self) -> None:
        img, err = open_validated_image(self._path)
        if err is not None:
            self.error.emit(err)
            return
        assert img is not None
        self.finished.emit(img, self._path)


class FloodFillWorker(_Worker):
    """Berechnet die Zauberstab-Auswahl im Hintergrund.

    Bei grossen, einfarbigen Flaechen kann ein synchroner Flood-Fill die UI
    sichtbar blockieren. Trotz Scanline-Optimierung wird die
    zusammenhaengende Region schrittweise aufgebaut. Der Worker laeuft auf
    einem kurzlebigen ``QThread``; das Ergebnis kommt per
    ``finished``-Signal auf den UI-Thread zurueck. Der ``arr``-Parameter
    ist die schreibgeschuetzte NumPy-Sicht aus ``ImageCanvas._arr``;
    weil ``np.asarray`` eine ``base``-Referenz auf das PIL-Bild haelt,
    bleibt der Buffer waehrend der Worker-Laufzeit auch dann gueltig,
    wenn der Canvas das Bild zwischenzeitlich austauscht.
    """
    finished = pyqtSignal(object)   # np.ndarray (bool-Maske) – nur bei Erfolg
    done = pyqtSignal()             # immer – Thread-Abschluss (auch Abbruch/Fehler)
    _error_context = "Flood-Fill-Fehler"

    def __init__(
        self, arr: np.ndarray, x: int, y: int, tolerance: int,
    ) -> None:
        super().__init__()
        self._arr = arr
        self._x = x
        self._y = y
        self._tolerance = tolerance
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def _work(self) -> None:
        mask = flood_fill(
            self._arr, self._x, self._y, self._tolerance,
            should_cancel=lambda: self._cancelled,
        )
        if self._cancelled:
            return
        self.finished.emit(mask)

    def _always_finished(self) -> None:
        self.done.emit()
