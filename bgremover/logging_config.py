"""Logging-Konfiguration und der aktive Log-Pfad (einzige Quelle).

``_log_file_path`` lebt ausschließlich hier; die Auslese-Schnittstelle
ist ``current_log_file()``. Auch der Einstellungen-Dialog liest darüber,
nie den Modul-Globalwert direkt.
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PyQt6.QtCore import QStandardPaths

from bgremover.constants import LOG_FILENAME

# Vom Logging-Setup gesetzter, tatsächlich beschriebener Log-Pfad. Wird
# vom Einstellungen-Dialog ausgelesen, damit Anzeige und FileHandler nie
# auseinanderlaufen.
_log_file_path: Path | None = None


def _resolve_log_dir() -> Path:
    """Ermittelt das Log-Verzeichnis und legt es bei Bedarf an.

    Das Zielverzeichnis wird angelegt – andernfalls bricht der
    Datei-Handler den Start mit ``FileNotFoundError`` ab.
    """
    loc = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation)
    log_dir = Path(loc) if loc else (Path.home() / ".bgremover")
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        log_dir = Path.home()
    return log_dir


def current_log_file() -> Path:
    """Pfad der aktiven Log-Datei.

    Liefert den vom ``_setup_logging`` gesetzten Pfad; falls noch kein
    Setup lief (z. B. in Tests), wird er erneut aufgelöst.
    """
    if _log_file_path is not None:
        return _log_file_path
    return _resolve_log_dir() / LOG_FILENAME


def _setup_logging() -> None:
    """Konfiguriert stderr- + Datei-Logging für den benannten App-Logger.

    Muss NACH dem Erzeugen der QApplication und dem Setzen von
    Application-/Organization-Name laufen, sonst liefert
    ``QStandardPaths`` keinen app-spezifischen Pfad.

    Konfiguriert gezielt den ``BgRemover``-Logger (alle App-Module teilen
    sich diesen, siehe ``constants.logger``) statt des Root-Loggers und
    schaltet dessen Propagation ab. Das hat zwei Vorteile gegenüber dem
    früheren ``logging.basicConfig(force=True)``:

    1. **Kein Fremd-Rauschen in der Support-Logdatei.** Der Datei-Handler
       hängt nur am App-Logger; INFO-Logs von Fremdbibliotheken
       (rembg/onnxruntime/Pillow) laufen über den Root und landen NICHT in
       ``bgremover.log``. Die Datei, die der Einstellungen-Dialog für
       Support-Mails anbietet, bleibt damit lesbar.
    2. **Keine Kollision mit Fremd-Handlern.** ``force=True`` riss alle
       bereits am Root registrierten Handler ab; der benannte Logger
       konfiguriert sich unabhängig vom Root-Zustand.

    Idempotent: vorhandene Handler des App-Loggers werden zuvor entfernt
    und geschlossen (z. B. bei wiederholtem Setup in Tests).
    """
    global _log_file_path
    log_dir = _resolve_log_dir()
    _log_file_path = log_dir / LOG_FILENAME

    app_logger = logging.getLogger("BgRemover")
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
    for handler in list(app_logger.handlers):
        app_logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s")
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        _log_file_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
        delay=True,
    )
    file_handler.setFormatter(formatter)
    app_logger.addHandler(stream_handler)
    app_logger.addHandler(file_handler)
