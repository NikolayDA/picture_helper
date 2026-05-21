"""Anwendungs-Einstiegspunkt.

Verbatim aus dem ``__main__``-Block von ``BgRemover.py`` (Runde 5,
Phase B – Schritt 12). Liefert ``int`` zurueck (Exit-Code), damit
``raise SystemExit(main())`` in ``__main__.py`` korrekt durchschlaegt.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_qt_plugin_path() -> None:
    """Macht die PyQt6-Plugins (insb. ``platforms/cocoa``) zuverlässig findbar.

    Auf manchen macOS-Setups (vor allem in venv/conda-Installationen mit
    PyQt6 6.11+) findet Qt sein eigenes ``cocoa``-Plugin nicht und bricht
    den Start mit ``Could not find the Qt platform plugin "cocoa" in ""``
    ab. Wir setzen ``QT_QPA_PLATFORM_PLUGIN_PATH`` und ``QT_PLUGIN_PATH``
    explizit aus der PyQt6-Installation – das ist der zuverlässige Ort,
    an dem die Plugins liegen. Vom Nutzer gesetzte Werte werden respek-
    tiert (nichts überschrieben).

    Muss VOR ``from PyQt6.QtWidgets import QApplication`` bzw. dem
    ersten ``QApplication(...)``-Aufruf laufen, damit Qt die Variablen
    beim Plugin-Lookup tatsächlich sieht.
    """
    try:
        import PyQt6  # noqa: F401  -- nur um __file__ zu erhalten
    except ImportError:
        return
    pkg_dir = Path(PyQt6.__file__).resolve().parent
    plugins_root = pkg_dir / "Qt6" / "plugins"
    if not plugins_root.is_dir():
        return
    platforms = plugins_root / "platforms"
    if platforms.is_dir():
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platforms))
    os.environ.setdefault("QT_PLUGIN_PATH", str(plugins_root))


_ensure_qt_plugin_path()

from PyQt6.QtGui import QColor, QPalette  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from bgremover.logging_config import _setup_logging  # noqa: E402
from bgremover.main_window import MainWindow  # noqa: E402


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

    # Selbsttest-Hook für CI/Smoke-Tests: ist BGREMOVER_SMOKE_TEST
    # gesetzt, beendet die App sich nach dem ersten Event-Loop-Durchlauf
    # selbst (Exit-Code 0). Sie ist dann vollständig hochgefahren –
    # QApplication, Palette, MainWindow inkl. Toolbar/Panels/Canvas –,
    # ohne dass der Test einen Fensterprozess killen muss.
    if os.environ.get("BGREMOVER_SMOKE_TEST"):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, app.quit)

    return app.exec()
