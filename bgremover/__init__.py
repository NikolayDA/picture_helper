"""BgRemover – Hintergrund-Entfernungs- und Bildbearbeitungs-Tool.

Das Projekt ist als Paket ``bgremover`` strukturiert und kann per
Console-Script ``bgremover`` oder ``python -m bgremover`` gestartet
werden. Einige etablierte Klassen und Helfer werden hier für Tests und
kleine Integrationen re-exportiert.
"""
from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__ = _pkg_version("bgremover")
except PackageNotFoundError:
    # Quelle-Lauf ohne installiertes Paket – pyproject.toml ist maßgeblich.
    __version__ = "2.2.0"

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
    pil_to_numpy_readonly,
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
from bgremover.settings_dialog import SettingsDialog
from bgremover.widgets import TopIconTabBar, TopIconTabWidget
from bgremover.workers import (
    REMBG_AVAILABLE,
    AIWorker,
    ImageLoadWorker,
)
from bgremover.main_window import MainWindow

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
    "MainWindow",
    "SettingsDialog",
    "TopIconTabBar",
    "TopIconTabWidget",
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
    "pil_to_numpy_readonly",
    "pil_to_qpixmap",
]
