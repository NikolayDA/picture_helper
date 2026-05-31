"""Modulweite Konstanten und der Logger.

``_log_file_path`` lebt bewusst nicht hier, sondern in ``logging_config``
als zentrale Quelle.
"""
from __future__ import annotations

import logging
import sys

from PIL import Image

# Zentraler App-Logger. Sub-Module dürfen den hier importieren oder einen
# eigenen ``logger = logging.getLogger(__name__)`` führen – letzteres ist
# in neuem Code zu bevorzugen, weil es Log-Filter pro Modul ermöglicht,
# ohne die zentrale "BgRemover"-Konfiguration anzufassen. Eine
# durchgängige Migration ist ausdrücklich Folge-PR-Material, kein
# Big-Bang im selben Commit.
logger = logging.getLogger("BgRemover")

LOG_FILENAME = "bgremover.log"

# Bildgrössen-Limit beim Laden (Pixel), um hohe Laufzeit / OOM zu vermeiden.
# Die Zauberstab-Flood-Fill läuft zwar asynchron, braucht bei sehr grossen
# Bildern aber weiterhin entsprechend Zeit und Speicher.
_MAX_MEGAPIXELS = 40
# Decompression-Bomb-Schutz von Pillow am eigenen Limit ausrichten.
_MAX_IMAGE_PIXELS = _MAX_MEGAPIXELS * 1_000_000
# Explizit unterstützte Eingabeformate für den asynchronen Ladepfad.
_ALLOWED_IMAGE_FORMATS = frozenset({
    "PNG", "JPEG", "WEBP", "TIFF", "BMP", "GIF"
})
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
    """Initialisiert explizite Runtime-Seiteneffekte für die Anwendung.

    Achtung – prozessweiter Seiteneffekt: setzt ``Image.MAX_IMAGE_PIXELS``
    auf das Megapixel-Limit der App. Das hebt den Pillow-eigenen
    Decompression-Bomb-Schutz für *jeden* Aufrufer im selben Prozess an
    (auch importierte Bibliotheken, die selbst Pillow nutzen). Wird daher
    explizit aus ``bgremover.app.main`` aufgerufen und nicht implizit beim
    Import von ``bgremover``.
    """
    Image.MAX_IMAGE_PIXELS = _MAX_IMAGE_PIXELS
