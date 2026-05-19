"""Anwendungs-Einstiegspunkt.

Verbatim aus dem ``__main__``-Block von ``BgRemover.py`` (Runde 5,
Phase B – Schritt 12). Liefert ``int`` zurueck (Exit-Code), damit
``raise SystemExit(main())`` in ``__main__.py`` korrekt durchschlaegt.
``BgRemover.py`` enthaelt vorerst denselben Body byte-identisch
nochmal; ab Schritt 13 wird ``BgRemover.py`` entfernt.
"""
from __future__ import annotations

import sys

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from bgremover.logging_config import _setup_logging
from bgremover.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("BgRemover")
    app.setOrganizationName("BgRemover")
    # Erst jetzt – QApplication + App-Name stehen – ist der Log-Pfad korrekt.
    _setup_logging()
    app.setStyle("Fusion")

    # Dunkles Farbschema
    pal = QPalette()
    dark = QColor(30, 30, 30)
    pal.setColor(QPalette.ColorRole.Window,          QColor(37, 37, 37))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor(220, 220, 220))
    pal.setColor(QPalette.ColorRole.Base,            dark)
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor(53, 53, 53))
    pal.setColor(QPalette.ColorRole.Text,            QColor(220, 220, 220))
    pal.setColor(QPalette.ColorRole.Button,          QColor(53, 53, 53))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor(220, 220, 220))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor(74, 144, 217))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    pal.setColor(QPalette.ColorRole.ToolTipBase,     QColor(50, 50, 50))
    pal.setColor(QPalette.ColorRole.ToolTipText,     QColor(220, 220, 220))
    app.setPalette(pal)

    win = MainWindow()
    win.show()
    return app.exec()
