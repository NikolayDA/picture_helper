"""BgRemover – Hintergrund-Entfernungs- und Bildbearbeitungs-Tool.

Übergangszustand (Phase B des Monolith→Paket-Schnitts, Runde 5): Die
Implementierung liegt aktuell noch in ``BgRemover.py``; dieses Paket
stellt bereits den Paket-Einstiegspunkt bereit (``bgremover`` /
``python -m bgremover``). Module werden schrittweise, verhaltensneutral
hierher verschoben.

Öffentliche Re-Exporte (für Tests / API): wachsen pro Schritt mit, damit
der finale Import-Wechsel ``from BgRemover import X`` →
``from bgremover import X`` ein minimaler Eingriff bleibt.
"""
from bgremover.constants import (
    LOG_FILENAME,
    TOOL_BRUSH,
    TOOL_ERASER,
    TOOL_LASSO,
    TOOL_WAND,
    _MAX_MEGAPIXELS,
    _THREAD_SHUTDOWN_MS,
    _UNDO_MEMORY_LIMIT,
    logger,
)
from bgremover.image_utils import (
    flood_fill,
    mask_to_overlay,
    numpy_to_pil,
    pil_to_numpy,
    pil_to_qpixmap,
)
from bgremover.theme import SLD_STYLE, TOOL_STYLE, _Theme
from bgremover.canvas import ImageCanvas
from bgremover.crop import CropOverlayItem
from bgremover.logging_config import (
    _resolve_log_dir,
    _setup_logging,
    current_log_file,
)
from bgremover.workers import (
    REMBG_AVAILABLE,
    AIWorker,
    ImageLoadWorker,
)

__all__ = [
    "LOG_FILENAME",
    "REMBG_AVAILABLE",
    "SLD_STYLE",
    "TOOL_BRUSH",
    "TOOL_ERASER",
    "TOOL_LASSO",
    "TOOL_STYLE",
    "TOOL_WAND",
    "AIWorker",
    "CropOverlayItem",
    "ImageCanvas",
    "ImageLoadWorker",
    "_MAX_MEGAPIXELS",
    "_THREAD_SHUTDOWN_MS",
    "_UNDO_MEMORY_LIMIT",
    "_Theme",
    "_resolve_log_dir",
    "_setup_logging",
    "current_log_file",
    "flood_fill",
    "logger",
    "mask_to_overlay",
    "numpy_to_pil",
    "pil_to_numpy",
    "pil_to_qpixmap",
]
