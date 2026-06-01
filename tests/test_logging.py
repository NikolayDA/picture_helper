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
    """Ruft ``_setup_logging`` isoliert auf und stellt den App-Logger danach
    wieder her.

    ``_setup_logging`` konfiguriert gezielt den benannten ``BgRemover``-Logger
    (nicht den Root), daher snapshottet
    der Helfer dessen Handler/Level/Propagation.
    """
    class _FakeQSP:
        class StandardLocation:
            AppDataLocation = 0

        @staticmethod
        def writableLocation(_loc):
            return str(target)

    monkeypatch.setattr(_lc, "QStandardPaths", _FakeQSP)
    app_logger = logging.getLogger("BgRemover")
    before = list(app_logger.handlers)
    before_level = app_logger.level
    before_propagate = app_logger.propagate
    previous_log_file = _lc._log_file_path
    for handler in before:
        app_logger.removeHandler(handler)
    try:
        _lc._setup_logging()
        yield
    finally:
        for handler in list(app_logger.handlers):
            handler.close()
            app_logger.removeHandler(handler)
        for handler in before:
            app_logger.addHandler(handler)
        app_logger.setLevel(before_level)
        app_logger.propagate = before_propagate
        _lc._log_file_path = previous_log_file


def test_module_logger_exists():
    assert isinstance(bgremover.logger, logging.Logger)
    assert bgremover.logger.name == "BgRemover"


def _raise_value_error(*_args, **_kwargs):
    raise ValueError("simulierter Bildverarbeitungsfehler")


def test_apply_remove_logs_expected_value_error(qapp, caplog, monkeypatch):
    """Erwartete Bildverarbeitungsfehler (ValueError) landen im Logger
    und als Statusmeldung statt unbehandelt auf stderr zu enden."""
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (10, 10), (0, 0, 0, 255)), "seed.png")
    canvas._mask = np.ones((10, 10), dtype=bool)
    monkeypatch.setattr(
        canvas._selection, "remove_background", _raise_value_error)
    with caplog.at_level(logging.ERROR, logger="BgRemover"):
        canvas.apply_remove()
    assert any("Fehler" in record.message for record in caplog.records)


def test_apply_replace_logs_expected_value_error(qapp, caplog, monkeypatch):
    from PyQt6.QtGui import QColor
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (10, 10), (0, 0, 0, 255)), "seed.png")
    canvas._mask = np.ones((10, 10), dtype=bool)
    monkeypatch.setattr(
        canvas._selection, "replace_background", _raise_value_error)
    with caplog.at_level(logging.ERROR, logger="BgRemover"):
        canvas.apply_replace(QColor(255, 0, 0))
    assert any("Fehler" in record.message for record in caplog.records)


def test_apply_remove_propagates_unexpected_bug(qapp):
    """Echte Bugs (AttributeError o.ä.) werden bewusst nicht mehr
    stillschweigend verschluckt – der Engpass im except ist eng auf
    OSError/ValueError/UnidentifiedImageError gefasst."""
    import pytest
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (10, 10), (0, 0, 0, 255)), "seed.png")
    canvas._arr  = None                          # provoziert AssertionError
    canvas._mask = np.ones((10, 10), dtype=bool)
    with pytest.raises(AssertionError):
        canvas.apply_remove()


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
        app_logger = logging.getLogger("BgRemover")
        rotating_handlers = [
            handler
            for handler in app_logger.handlers
            if isinstance(handler, RotatingFileHandler)
        ]
        # Der App-Logger darf nicht zum Root propagieren – sonst würde sein
        # FileHandler bei künftiger Root-Konfiguration doppelt schreiben.
        assert app_logger.propagate is False

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


def test_setup_logging_isolates_app_logger_from_foreign_root_handler(
    tmp_path, monkeypatch,
):
    """Regression (#11 / Re-Review #C): das Logging-Setup darf nicht vom
    Root-Logger-Zustand abhängen.

    Historie: Ursprünglich war ``basicConfig`` ein No-op, sobald der Root
    bereits einen Fremd-Handler hatte → KEIN FileHandler. Der Nachfolger
    ``force=True`` installierte zwar einen, riss dafür aber alle Fremd-Handler
    vom Root und zog deren Logs in die App-Datei. Jetzt wird der benannte
    ``BgRemover``-Logger direkt konfiguriert: der FileHandler landet
    unabhängig vom Root, und ein vorhandener Fremd-Root-Handler bleibt
    unangetastet.
    """
    target = tmp_path / "appdir"

    class _FakeQSP:
        class StandardLocation:
            AppDataLocation = 0

        @staticmethod
        def writableLocation(_loc):
            return str(target)

    monkeypatch.setattr(_lc, "QStandardPaths", _FakeQSP)

    app_logger = logging.getLogger("BgRemover")
    before = list(app_logger.handlers)
    before_level = app_logger.level
    before_propagate = app_logger.propagate
    previous_log_file = _lc._log_file_path
    for handler in before:
        app_logger.removeHandler(handler)

    root = logging.getLogger()
    foreign = logging.StreamHandler()
    root.addHandler(foreign)  # simuliert einen Fremd-Handler einer Bibliothek
    try:
        _lc._setup_logging()
        rotating = [
            h for h in app_logger.handlers if isinstance(h, RotatingFileHandler)
        ]
        assert len(rotating) == 1
        assert _lc.current_log_file() == target / "bgremover.log"
        # Fremd-Handler am Root bleibt unberührt (kein force=True-Kahlschlag).
        assert foreign in root.handlers
    finally:
        for handler in list(app_logger.handlers):
            handler.close()
            app_logger.removeHandler(handler)
        for handler in before:
            app_logger.addHandler(handler)
        app_logger.setLevel(before_level)
        app_logger.propagate = before_propagate
        root.removeHandler(foreign)
        foreign.close()
        _lc._log_file_path = previous_log_file


def test_setup_logging_keeps_third_party_logs_out_of_app_file(
    tmp_path, monkeypatch,
):
    """Kern von #C: Logs von Fremdbibliotheken (über den Root-Logger) dürfen
    NICHT in der App-Logdatei landen.

    Der frühere ``basicConfig(force=True)`` hängte den FileHandler an den
    Root, sodass jeder INFO-Log irgendeiner importierten Bibliothek in
    ``bgremover.log`` geschrieben wurde – schlecht für eine als Support-Hilfe
    gedachte Datei. Mit dem benannten App-Logger ist nur noch dessen eigener
    Output in der Datei.
    """
    target = tmp_path / "appdir"

    # NullHandler am Root verhindert nur Pythons "last resort"-Ausgabe auf
    # stderr während des Tests; er schreibt selbst nichts in die App-Datei.
    root = logging.getLogger()
    null = logging.NullHandler()
    root.addHandler(null)
    try:
        with _isolated_logging_setup(target, monkeypatch):
            logging.getLogger("some_third_party_lib").warning("FREMD-RAUSCHEN")
            logging.getLogger("BgRemover").warning("APP-EINTRAG")
    finally:
        root.removeHandler(null)

    content = (target / "bgremover.log").read_text(encoding="utf-8")
    assert "APP-EINTRAG" in content
    assert "FREMD-RAUSCHEN" not in content
