"""Leichtgewichtiger Paket-Einstieg fuer BgRemover.

``import bgremover`` stellt Versionsinformationen ohne Qt-Abhaengigkeit
bereit. Etablierte Re-Exports fuer Tests und kleine Integrationen bleiben
kompatibel, werden aber erst beim konkreten Attributzugriff importiert.
"""
from __future__ import annotations

from importlib import import_module
from typing import Any, Final

from bgremover._version import (
    _read_pyproject_version as _read_pyproject_version,
)
from bgremover._version import get_version

__version__ = get_version()

_LAZY_EXPORTS: Final[dict[str, tuple[str, str]]] = {
    "LOG_FILENAME": ("bgremover.constants", "LOG_FILENAME"),
    "REMBG_AVAILABLE": ("bgremover.workers", "REMBG_AVAILABLE"),
    "SLD_STYLE": ("bgremover.theme", "SLD_STYLE"),
    "TOOL_BRUSH": ("bgremover.constants", "TOOL_BRUSH"),
    "TOOL_ERASER": ("bgremover.constants", "TOOL_ERASER"),
    "TOOL_LASSO": ("bgremover.constants", "TOOL_LASSO"),
    "TOOL_STYLE": ("bgremover.theme", "TOOL_STYLE"),
    "TOOL_WAND": ("bgremover.constants", "TOOL_WAND"),
    "AIWorker": ("bgremover.workers", "AIWorker"),
    "CropOverlayItem": ("bgremover.crop", "CropOverlayItem"),
    "FloodFillWorker": ("bgremover.workers", "FloodFillWorker"),
    "ImageCanvas": ("bgremover.canvas", "ImageCanvas"),
    "ImageLoadWorker": ("bgremover.workers", "ImageLoadWorker"),
    "MainWindow": ("bgremover.main_window", "MainWindow"),
    "SettingsDialog": ("bgremover.settings_dialog", "SettingsDialog"),
    "current_log_file": ("bgremover.logging_config", "current_log_file"),
    "flood_fill": ("bgremover.image_utils", "flood_fill"),
    "logger": ("bgremover.constants", "logger"),
    "mask_to_overlay": ("bgremover.image_utils", "mask_to_overlay"),
    "numpy_to_pil": ("bgremover.image_utils", "numpy_to_pil"),
    "pil_to_numpy": ("bgremover.image_utils", "pil_to_numpy"),
    "pil_to_numpy_readonly": ("bgremover.image_utils", "pil_to_numpy_readonly"),
    "pil_to_qpixmap": ("bgremover.image_utils", "pil_to_qpixmap"),
}

__all__ = ["__version__", "get_version", *_LAZY_EXPORTS]


def __getattr__(name: str) -> Any:
    """Laedt einen etablierten Re-Export erst bei seinem ersten Zugriff."""
    try:
        module_name, attribute_name = _LAZY_EXPORTS[name]
    except KeyError:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        ) from None

    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Zeigt Lazy Exports wie regulaer definierte Paketattribute an."""
    return sorted(set(globals()) | set(__all__))
