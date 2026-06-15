"""Modulweite Konstanten und der Logger.

``_log_file_path`` lebt bewusst nicht hier, sondern in ``logging_config``
als zentrale Quelle.
"""
from __future__ import annotations

import logging
import sys

from PIL import Image

# Zentraler App-Logger. Sub-Module importieren ihn direkt, damit ihre Meldungen
# in den von ``logging_config`` eingerichteten Support-Handlern landen. Falls
# später modulspezifische Filter nötig werden, können Kind-Logger unterhalb von
# ``BgRemover`` verwendet werden.
logger = logging.getLogger("BgRemover")

LOG_FILENAME = "bgremover.log"

# Bildgrössen-Limit beim Laden (Pixel), um hohe Laufzeit / OOM zu vermeiden.
# Die Zauberstab-Flood-Fill läuft zwar asynchron, braucht bei sehr grossen
# Bildern aber weiterhin entsprechend Zeit und Speicher.
_MAX_MEGAPIXELS = 40
# Decompression-Bomb-Schutz von Pillow am eigenen Limit ausrichten.
_MAX_IMAGE_PIXELS = _MAX_MEGAPIXELS * 1_000_000
# Maximale Größe der *Eingabedatei* (Bytes), bevor ihr Inhalt überhaupt in den
# Arbeitsspeicher gelesen wird. Schützt – unabhängig vom Megapixel-Limit, das
# erst nach dem Dekodieren greift – vor extrem großen (auch falsch benannten
# oder beschädigten) Dateien, die sonst einen ebenso großen bytes-Puffer
# erzeugen würden (Befund #230).
_MAX_INPUT_FILE_BYTES = 512 * 1024 * 1024  # 512 MB
# Explizit unterstützte Eingabeformate für den asynchronen Ladepfad.
_ALLOWED_IMAGE_FORMATS = frozenset({
    "PNG", "JPEG", "WEBP", "TIFF", "BMP", "GIF"
})
# Gemeinsames Speicherlimit des Undo-/Redo-Verlaufs (RGBA-Rohdaten,
# geschätzt in Bytes). Originalbild und aktueller Canvas-Zustand liegen
# bewusst außerhalb dieses History-Budgets.
_HISTORY_MEMORY_LIMIT = 256 * 1024 * 1024  # 256 MiB
# Maximale Anzahl Redo-Einträge.
_REDO_MAX_ENTRIES = 20
# Maximale Wartezeiten (ms) auf einen Hintergrund-Thread beim Schliessen.
# Alle Worker sind kooperativ stoppbar (die nicht unterbrechbare ONNX-Inferenz
# läuft seit #270 im Inferenz-Kindprozess, nicht im Thread), daher greift der
# kooperative quit()/wait() innerhalb dieser Frist. terminate() bleibt nur eine
# begrenzte Notbremse für einen wider Erwarten hängenden Thread; reagiert er
# auch darauf nicht, bleibt das Fenster offen. terminate() kann hier keinen
# nativen ONNX-Zustand mehr zerreißen – der liegt im separat beendeten Prozess.
_THREAD_SHUTDOWN_MS = 5000
_THREAD_TERMINATE_WAIT_MS = 1000

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
