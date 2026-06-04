"""Hintergrund-Worker (eigene QThreads) und der optionale rembg-Import.

Der optionale ``rembg``-Import liegt hier, weil ausschließlich dieses
Modul ``rembg_remove`` aufruft; Tests patchen entsprechend
``bgremover.workers.rembg_remove`` bzw. ``bgremover.workers.Image.open``.
"""
from __future__ import annotations

import importlib.util
import io
import threading

import numpy as np
from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal

from bgremover.constants import logger
from bgremover.image_loading import open_validated_image
from bgremover.image_utils import flood_fill

# rembg (zieht onnxruntime) wird bewusst NICHT auf Modulebene importiert: der
# Import kostet beim Start mehrere Sekunden, und ``main_window`` lädt ``workers``
# für ``REMBG_AVAILABLE`` schon vor dem ersten Fensterzeichnen. ``find_spec``
# prüft nur die *Installation* (ohne den teuren Import); der echte Import läuft
# lazy im Hintergrund-Thread (Warmup / erster KI-Klick), wo ein defektes
# onnxruntime-Backend als normaler Worker-Fehler gemeldet wird statt den Start
# zu verzögern.
try:
    REMBG_AVAILABLE = importlib.util.find_spec("rembg") is not None
except (ImportError, ValueError):
    REMBG_AVAILABLE = False

# Lazy-Handle auf ``rembg.remove`` (befüllt beim ersten echten Bedarf im
# Worker-Thread). Modulebene, damit Tests ``bgremover.workers.rembg_remove``
# direkt patchen können.
rembg_remove = None

# Serialisiert den Lazy-Import unten gegen konkurrierende Threads. Der
# ``WorkerController`` reiht Warmup/KI zwar ohnehin sequenziell ein – der Lock
# macht ``_ensure_rembg_remove`` aber unabhängig davon thread-sicher.
_rembg_lock = threading.Lock()


def _ensure_rembg_remove():
    """Importiert ``rembg.remove`` beim ersten Aufruf und cached es modulweit.

    Hält den teuren ``onnxruntime``-Import aus dem App-Start heraus – er läuft
    erst hier, im Warmup- bzw. KI-Worker-Thread. Schlägt der Import fehl (z. B.
    defektes Backend), propagiert die Exception in ``_Worker.run`` und wird wie
    ein fehlgeschlagener ``remove()``-Aufruf als ``error`` gemeldet. Ist
    ``rembg_remove`` bereits gesetzt (echter Import *oder* Test-Patch), wird es
    unverändert zurückgegeben.

    Der Lazy-Import ist per Double-Checked-Locking thread-sicher: ohne Lock
    könnten zwei Threads gleichzeitig ``rembg_remove is None`` sehen und beide
    den Import-Pfad betreten.
    """
    global rembg_remove
    if rembg_remove is None:
        with _rembg_lock:
            # Zweite Prüfung im Lock: ein konkurrierender Thread kann
            # ``rembg_remove`` während des Wartens bereits gesetzt haben.
            if rembg_remove is None:
                from rembg import remove
                rembg_remove = remove
    return rembg_remove


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
    """Entfernt den Hintergrund per rembg im Hintergrund-Thread.

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

    def __init__(self, pil_image: Image.Image) -> None:
        super().__init__()
        self._img = pil_image
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def _work(self) -> None:
        remove = _ensure_rembg_remove()
        buf = io.BytesIO()
        self._img.save(buf, format="PNG")
        result_bytes = remove(buf.getvalue())
        if self._cancelled:
            return
        result = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
        self.finished.emit(result)

    def _always_finished(self) -> None:
        self.done.emit()


class RembgWarmupWorker(_Worker):
    """Lädt das rembg-ONNX-Modell einmalig im Hintergrund.

    Ohne diesen Warmup blockt der erste KI-Klick rund zehn Sekunden,
    weil rembg sein Modell on-demand initialisiert. Ein remove()-Aufruf
    mit einem winzigen Dummy-Bild reicht, um die rembg-Session global
    zu cachen – nachfolgende Aufrufe sind sofort schnell.

    ``finished`` ist parameterlos (anders als bei den Daten-Workern) und
    wird bewusst auch im Fehlerfall gefeuert – der WorkerController nutzt
    es als Abschluss-Signal für den Thread-Lifecycle.
    """
    finished = pyqtSignal()
    _error_context = "rembg-Warmup"

    def _work(self) -> None:
        remove = _ensure_rembg_remove()
        buf = io.BytesIO()
        Image.new("RGBA", (16, 16), (0, 0, 0, 255)).save(buf, format="PNG")
        remove(buf.getvalue())
        logger.info("rembg-Warmup abgeschlossen")

    def _always_finished(self) -> None:
        self.finished.emit()


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
