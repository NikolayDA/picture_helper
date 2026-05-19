#!/usr/bin/env python3
"""
BgRemover — Hintergrund-Entfernungs & Ersatz-Tool für macOS
Starten: python3 BgRemover.py
"""

import sys

from PyQt6.QtWidgets import (
    QApplication,
)
from PyQt6.QtGui import (
    QColor, QPalette,
)


from bgremover.logging_config import _setup_logging
from bgremover.main_window import MainWindow

# Übergangs-Re-Export (Runde 5, Phase B): hält ``from BgRemover import X``
# gültig, bis die Tests in Schritt 13 auf ``from bgremover import X``
# umgestellt werden. Bewusst auch intern ungenutzte Namen – daher noqa.
from bgremover import (  # noqa: F401
    LOG_FILENAME,
    REMBG_AVAILABLE,
    SLD_STYLE,
    TOOL_BRUSH,
    TOOL_ERASER,
    TOOL_LASSO,
    TOOL_STYLE,
    TOOL_WAND,
    AIWorker,
    CropOverlayItem,
    ImageCanvas,
    ImageLoadWorker,
    SettingsDialog,
    TopIconTabBar,
    TopIconTabWidget,
    __version__,
    _MAX_MEGAPIXELS,
    _THREAD_SHUTDOWN_MS,
    _UNDO_MEMORY_LIMIT,
    _Theme,
    _resolve_log_dir,
    current_log_file,
    flood_fill,
    logger,
    mask_to_overlay,
    numpy_to_pil,
    pil_to_numpy,
    pil_to_qpixmap,
)


# ─────────────────────────────────────────────────────────────
# Start
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
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
    sys.exit(app.exec())
