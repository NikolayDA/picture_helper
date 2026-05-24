"""Modulweite Konstanten und der Logger.

Verbatim aus ``BgRemover.py`` verschoben (Runde 5, Phase B – Schritt 2).
Keine Verhaltensänderung. ``_log_file_path`` bleibt bewusst hier *nicht*
enthalten (zentrale Quelle: ``logging_config``, Schritt 9).
"""
from __future__ import annotations

import logging
import sys

from PIL import Image

logger = logging.getLogger("BgRemover")

LOG_FILENAME = "bgremover.log"

# Bildgrössen-Limit beim Laden (Pixel), um UI-Freeze / OOM zu vermeiden.
# Die Zauberstab-Flood-Fill läuft synchron im GUI-Thread; jenseits ~40 MP
# wird selbst die vektorisierte Variante spürbar träge.
_MAX_MEGAPIXELS = 40
# Decompression-Bomb-Schutz von Pillow am eigenen Limit ausrichten.
_MAX_IMAGE_PIXELS = _MAX_MEGAPIXELS * 1_000_000
# Speicherlimit des Undo-Stacks (RGBA-Rohdaten, geschätzt in Bytes).
_UNDO_MEMORY_LIMIT = 256 * 1024 * 1024  # 256 MB
# Maximale Anzahl Redo-Einträge.
_REDO_MAX_ENTRIES = 20
# Maximale Wartezeit (ms) auf einen Hintergrund-Thread beim Schliessen,
# bevor er hart terminiert wird. Der rembg-Warmup darf einige Sekunden
# brauchen; danach ist hartes Beenden besser als ein Hänger oder Crash.
_THREAD_SHUTDOWN_MS = 5000

# Plattform-Erkennung für tastaturabhängige Hinweistexte (macOS = Cmd).
_IS_MACOS = sys.platform == "darwin"

# ── UI-Layoutkonstanten ──────────────────────────────────────
_TOOLBAR_WIDTH      = 74
_TOOLBAR_BTN_SIZE   = 54
_TOOLBAR_ICON_SIZE  = 38
_RIGHT_PANEL_WIDTH  = 384
_CROP_BAR_HEIGHT    = 46
_COLOR_BTN_SIZE     = 38
_TAB_ICON_PX        = 30
_WINDOW_MIN_W       = 1100
_WINDOW_MIN_H       = 720

# ── Canvas-Standardwerte ─────────────────────────────────────
_DEFAULT_TOLERANCE    = 30
_DEFAULT_BRUSH_RADIUS = 15
_ZOOM_FACTOR          = 1.15

# ── Auswahloverlay-Farbe (RGBA) ──────────────────────────────
_OVERLAY_COLOR = (220, 60, 60, 130)

# ── Werkzeug-Namen ───────────────────────────────────────────
TOOL_WAND   = "wand"
TOOL_BRUSH  = "brush"
TOOL_ERASER = "eraser"
TOOL_LASSO  = "lasso"


def init_runtime() -> None:
    """Initialisiert explizite Runtime-Seiteneffekte für die Anwendung."""
    Image.MAX_IMAGE_PIXELS = _MAX_IMAGE_PIXELS
