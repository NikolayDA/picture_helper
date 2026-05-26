"""Tests für das Logging-Setup (Fix A3).

Vor dem Fix landeten Ausnahmen in ``apply_remove``/``apply_replace`` und
im ``AIWorker`` nur über ``traceback.print_exc()`` auf stderr — nie im
UI, nie in einer Datei. Jetzt wird ein modulweiter Logger genutzt.
"""
import logging
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler

import numpy as np
from PIL import Image

import bgremover
from bgremover import ImageCanvas
from bgremover import logging_config as _lc


@contextmanager
def _isolated_logging_setup(target, monkeypatch):
    class _FakeQSP:
        class StandardLocation:
            AppDataLocation = 0

        @staticmethod
        def writableLocation(_loc):
            return str(target)

    monkeypatch.setattr(_lc, "QStandardPaths", _FakeQSP)
    root = logging.getLogger()
    before = list(root.handlers)
    before_level = root.level
    previous_log_file = _lc._log_file_path
    for handler in before:
        root.removeHandler(handler)
    try:
        _lc._setup_logging()
        yield
    finally:
        for handler in list(root.handlers):
            handler.close()
            root.removeHandler(handler)
        for handler in before:
            root.addHandler(handler)
        root.setLevel(before_level)
        _lc._log_file_path = previous_log_file


def test_module_logger_exists():
    assert isinstance(bgremover.logger, logging.Logger)
    assert bgremover.logger.name == "BgRemover"


def test_apply_remove_logs_unexpected_exception(qapp, caplog):
    """Wenn die Auswahl-Anwendung crasht, muss der Logger das
    aufzeichnen (statt das Programm stumm zu lassen)."""
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (10, 10), (0, 0, 0, 255)), "seed.png")
    canvas._arr  = None                          # provoziert AttributeError
    canvas._mask = np.ones((10, 10), dtype=bool)
    with caplog.at_level(logging.ERROR, logger="BgRemover"):
        canvas.apply_remove()
    assert any("Fehler" in record.message for record in caplog.records)


def test_apply_replace_logs_unexpected_exception(qapp, caplog):
    from PyQt6.QtGui import QColor
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (10, 10), (0, 0, 0, 255)), "seed.png")
    canvas._arr  = None
    canvas._mask = np.ones((10, 10), dtype=bool)
    with caplog.at_level(logging.ERROR, logger="BgRemover"):
        canvas.apply_replace(QColor(255, 0, 0))
    assert any("Fehler" in record.message for record in caplog.records)


def test_setup_logging_creates_missing_directory(tmp_path, monkeypatch):
    """``_setup_logging`` muss das Zielverzeichnis anlegen – sonst bricht
    der Datei-Handler den Programmstart mit FileNotFoundError ab."""
    target = tmp_path / "deep" / "appdir"

    with _isolated_logging_setup(target, monkeypatch):
        assert target.exists()
        assert not (target / "bgremover.log").exists()


def test_setup_logging_uses_rotating_file_handler(tmp_path, monkeypatch):
    target = tmp_path / "appdir"

    with _isolated_logging_setup(target, monkeypatch):
        rotating_handlers = [
            handler
            for handler in logging.getLogger().handlers
            if isinstance(handler, RotatingFileHandler)
        ]

    assert len(rotating_handlers) == 1
    assert rotating_handlers[0].maxBytes == 5 * 1024 * 1024
    assert rotating_handlers[0].backupCount == 3


def test_current_log_file_matches_setup(tmp_path, monkeypatch):
    """``current_log_file()`` muss exakt den Pfad liefern, den
    ``_setup_logging`` gerade als FileHandler-Ziel verwendet – sonst
    zeigt der Einstellungen-Dialog einen falschen Pfad an."""
    target = tmp_path / "appdir"

    with _isolated_logging_setup(target, monkeypatch):
        assert _lc.current_log_file() == target / "bgremover.log"
