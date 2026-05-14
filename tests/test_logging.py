"""Tests für das Logging-Setup (Fix A3).

Vor dem Fix landeten Ausnahmen in ``apply_remove``/``apply_replace`` und
im ``AIWorker`` nur über ``traceback.print_exc()`` auf stderr — nie im
UI, nie in einer Datei. Jetzt wird ein modulweiter Logger genutzt.
"""
import logging

import numpy as np
from PIL import Image

import BgRemover
from BgRemover import ImageCanvas


def test_module_logger_exists():
    assert isinstance(BgRemover.logger, logging.Logger)
    assert BgRemover.logger.name == "BgRemover"


def test_apply_remove_logs_unexpected_exception(qapp, caplog):
    """Wenn die Auswahl-Anwendung crasht, muss der Logger das
    aufzeichnen (statt das Programm stumm zu lassen)."""
    canvas = ImageCanvas()
    canvas._pil  = Image.new("RGBA", (10, 10), (0, 0, 0, 255))
    canvas._arr  = None                          # provoziert AttributeError
    canvas._mask = np.ones((10, 10), dtype=bool)
    with caplog.at_level(logging.ERROR, logger="BgRemover"):
        canvas.apply_remove()
    assert any("Fehler" in record.message for record in caplog.records)


def test_apply_replace_logs_unexpected_exception(qapp, caplog):
    from PyQt6.QtGui import QColor
    canvas = ImageCanvas()
    canvas._pil  = Image.new("RGBA", (10, 10), (0, 0, 0, 255))
    canvas._arr  = None
    canvas._mask = np.ones((10, 10), dtype=bool)
    with caplog.at_level(logging.ERROR, logger="BgRemover"):
        canvas.apply_replace(QColor(255, 0, 0))
    assert any("Fehler" in record.message for record in caplog.records)
