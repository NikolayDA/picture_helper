"""Tests für das Logging-Setup (Fix A3).

Vor dem Fix landeten Ausnahmen in ``apply_remove``/``apply_replace`` und
im ``AIWorker`` nur über ``traceback.print_exc()`` auf stderr — nie im
UI, nie in einer Datei. Jetzt wird ein modulweiter Logger genutzt.
"""
import logging

import numpy as np
from PIL import Image

import bgremover
from bgremover import logging_config as _lc
from bgremover import ImageCanvas


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
    der FileHandler den Programmstart mit FileNotFoundError ab."""
    target = tmp_path / "deep" / "appdir"

    class _FakeQSP:
        class StandardLocation:
            AppDataLocation = 0

        @staticmethod
        def writableLocation(_loc):
            return str(target)

    monkeypatch.setattr(_lc, "QStandardPaths", _FakeQSP)
    root = logging.getLogger()
    before = list(root.handlers)
    try:
        _lc._setup_logging()
        assert target.exists()
        assert (target / "bgremover.log").exists()
    finally:
        for h in list(root.handlers):
            if h not in before:
                h.close()
                root.removeHandler(h)
        for h in before:
            if h not in root.handlers:
                root.addHandler(h)


def test_current_log_file_matches_setup(tmp_path, monkeypatch):
    """``current_log_file()`` muss exakt den Pfad liefern, den
    ``_setup_logging`` gerade als FileHandler-Ziel verwendet – sonst
    zeigt der Einstellungen-Dialog einen falschen Pfad an."""
    target = tmp_path / "appdir"

    class _FakeQSP:
        class StandardLocation:
            AppDataLocation = 0

        @staticmethod
        def writableLocation(_loc):
            return str(target)

    monkeypatch.setattr(_lc, "QStandardPaths", _FakeQSP)
    root = logging.getLogger()
    before = list(root.handlers)
    try:
        _lc._setup_logging()
        assert _lc.current_log_file() == target / "bgremover.log"
    finally:
        for h in list(root.handlers):
            if h not in before:
                h.close()
                root.removeHandler(h)
        for h in before:
            if h not in root.handlers:
                root.addHandler(h)
