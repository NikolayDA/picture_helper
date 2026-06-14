"""Importvertrag des Paket-Einstiegs ohne impliziten Qt-Stack."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import bgremover

ROOT = Path(__file__).resolve().parent.parent


def _run_fresh_python(code: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_lightweight_import_works_when_pyqt6_is_unavailable() -> None:
    """Metadatenimporte dürfen keinen GUI-Import versuchen."""
    code = """
import importlib.abc
import sys

class BlockPyQt6(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "PyQt6" or fullname.startswith("PyQt6."):
            raise RuntimeError(f"unexpected Qt import: {fullname}")
        return None

sys.meta_path.insert(0, BlockPyQt6())
import bgremover
from bgremover._version import get_version

assert bgremover.__version__ == get_version()
assert "bgremover.canvas" not in sys.modules
assert "bgremover.main_window" not in sys.modules
assert not any(
    name == "PyQt6" or name.startswith("PyQt6.")
    for name in sys.modules
)
"""
    result = _run_fresh_python(code)

    assert result.returncode == 0, (
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )


def test_gui_reexport_is_loaded_lazily_and_cached() -> None:
    code = """
import sys
import bgremover

assert "bgremover.canvas" not in sys.modules
from bgremover import ImageCanvas

assert "bgremover.canvas" in sys.modules
assert bgremover.ImageCanvas is ImageCanvas
assert ImageCanvas.__module__ == "bgremover.canvas"
"""
    result = _run_fresh_python(code)

    assert result.returncode == 0, (
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )


def test_lazy_exports_remain_discoverable() -> None:
    expected = {
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
        "FloodFillWorker",
        "__version__",
        "get_version",
        "ImageCanvas",
        "ImageLoadWorker",
        "MainWindow",
        "SettingsDialog",
        "TopIconTabBar",
        "TopIconTabWidget",
        "current_log_file",
        "flood_fill",
        "logger",
        "mask_to_overlay",
        "numpy_to_pil",
        "pil_to_numpy",
        "pil_to_numpy_readonly",
        "pil_to_qpixmap",
    }

    assert set(bgremover.__all__) == expected
    assert expected <= set(dir(bgremover))
