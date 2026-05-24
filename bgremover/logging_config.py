"""Logging-Konfiguration und der aktive Log-Pfad (einzige Quelle).

``_log_file_path`` lebt ausschließlich hier; die Auslese-Schnittstelle
ist ``current_log_file()``. Auch der Einstellungen-Dialog liest darüber,
nie den Modul-Globalwert direkt.
"""
from __future__ import annotations

import logging
import sys
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
    ``FileHandler`` den Start mit ``FileNotFoundError`` ab.
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
    """Konfiguriert stderr- + Datei-Logging.

    Muss NACH dem Erzeugen der QApplication und dem Setzen von
    Application-/Organization-Name laufen, sonst liefert
    ``QStandardPaths`` keinen app-spezifischen Pfad.
    """
    global _log_file_path
    log_dir = _resolve_log_dir()
    _log_file_path = log_dir / LOG_FILENAME
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(_log_file_path, encoding="utf-8"),
        ],
    )
