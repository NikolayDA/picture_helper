"""Hintergrund-Worker (eigene QThreads) und der optionale rembg-Import.

Der optionale ``rembg``-Import liegt hier, weil ausschließlich dieses
Modul ``rembg_remove`` aufruft; Tests patchen entsprechend
``bgremover.workers.rembg_remove`` bzw. ``bgremover.workers.Image.open``.
"""
from __future__ import annotations

import io

from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal

from bgremover.constants import logger
from bgremover.image_loading import open_validated_image

try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except (ImportError, RuntimeError, OSError, SystemExit):
    # rembg ist optional; fehlt das onnxruntime-Backend, kann der Import
    # je nach rembg-Version unterschiedlich fehlschlagen (inkl. SystemExit).
    REMBG_AVAILABLE = False


class _Worker(QObject):
    """Basisklasse für Hintergrund-Worker.

    Kapselt den in mehreren Workern identischen Ablauf
    ``try: _work() / except Exception: logger.exception(); error.emit()``.
    Unterklassen deklarieren ihr eigenes ``finished``-Signal (die
    Signaturen unterscheiden sich je Worker) und implementieren ``_work``.
    """
    error = pyqtSignal(str)
    _error_context = "Worker-Fehler"

    def run(self) -> None:
        try:
            self._work()
        except Exception as e:
            logger.exception(self._error_context)
            self.error.emit(f"{type(e).__name__}: {e}")

    def _work(self) -> None:
        raise NotImplementedError


class AIWorker(_Worker):
    finished = pyqtSignal(object)   # PIL Image
    _error_context = "rembg-Fehler"

    def __init__(self, pil_image: Image.Image) -> None:
        super().__init__()
        self._img = pil_image
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def _work(self) -> None:
        buf = io.BytesIO()
        self._img.save(buf, format="PNG")
        result_bytes = rembg_remove(buf.getvalue())
        if self._cancelled:
            return
        result = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
        self.finished.emit(result)


class RembgWarmupWorker(QObject):
    """Lädt das rembg-ONNX-Modell einmalig im Hintergrund.

    Ohne diesen Warmup blockt der erste KI-Klick rund zehn Sekunden,
    weil rembg sein Modell on-demand initialisiert. Ein remove()-Aufruf
    mit einem winzigen Dummy-Bild reicht, um die rembg-Session global
    zu cachen – nachfolgende Aufrufe sind sofort schnell.
    """
    finished = pyqtSignal()

    def run(self) -> None:
        try:
            buf = io.BytesIO()
            Image.new("RGBA", (16, 16), (0, 0, 0, 255)).save(buf, format="PNG")
            rembg_remove(buf.getvalue())
            logger.info("rembg-Warmup abgeschlossen")
        except Exception:
            logger.exception("rembg-Warmup fehlgeschlagen")
        finally:
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
