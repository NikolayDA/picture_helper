"""Anwendungs-Einstiegspunkt.

Liefert ``int`` zurueck (Exit-Code), damit ``raise SystemExit(main())``
in ``__main__.py`` korrekt durchschlaegt.
"""
from __future__ import annotations

import os
import sys

from bgremover.qt_plugins import ensure_qt_plugin_path


ensure_qt_plugin_path()

from PyQt6.QtGui import QColor, QPalette  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from bgremover.constants import init_runtime  # noqa: E402
from bgremover.logging_config import _setup_logging  # noqa: E402
from bgremover.main_window import MainWindow  # noqa: E402


def main() -> int:
    init_runtime()
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

    # Selbsttest-Hook für CI/Smoke-Tests: ist BGREMOVER_SMOKE_TEST
    # gesetzt, beendet die App sich nach dem ersten Event-Loop-Durchlauf
    # selbst (Exit-Code 0). Sie ist dann vollständig hochgefahren –
    # QApplication, Palette, MainWindow inkl. Toolbar/Panels/Canvas –,
    # ohne dass der Test einen Fensterprozess killen muss.
    if os.environ.get("BGREMOVER_SMOKE_TEST"):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, app.quit)

    return app.exec()
