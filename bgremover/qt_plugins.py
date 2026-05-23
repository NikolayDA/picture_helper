"""Qt plugin path setup shared by the app and local test helpers."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from importlib import metadata
from pathlib import Path

UF_HIDDEN = 0x8000


def _dist_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "unknown"


def _copy_if_needed(src: Path, dst: Path) -> None:
    if dst.exists():
        dst_stat = dst.stat()
        dst_hidden = bool(getattr(dst_stat, "st_flags", 0) & UF_HIDDEN)
        if src.stat().st_size == dst_stat.st_size and not dst_hidden:
            return

    tmp = dst.with_name(f"{dst.name}.tmp")
    if tmp.exists():
        tmp.unlink()
    shutil.copyfile(src, tmp)
    os.chmod(tmp, src.stat().st_mode & 0o777)
    os.replace(tmp, dst)


def _stage_platform_plugins(platforms: Path) -> tuple[Path, Path] | None:
    """Copy Qt platform plugins to temp if they are visible to Python.

    Some macOS runners can let Python list a venv under Documents while Qt's
    own directory listing sees an empty plugin directory. A temp copy avoids
    that privacy/sandbox edge case without changing the user's environment.
    """
    platform_files = [p for p in platforms.iterdir() if p.is_file()]
    if not platform_files:
        return None

    base_tmp = Path(tempfile.gettempdir())
    private_tmp = Path("/private/tmp")
    if sys.platform == "darwin" and private_tmp.is_dir() and os.access(private_tmp, os.W_OK):
        base_tmp = private_tmp

    qt_version = _dist_version("PyQt6-Qt6").replace(os.sep, "_").replace(".", "_")
    staged_root = base_tmp / "bgremover_qt_plugins" / qt_version
    staged_platforms = staged_root / "platforms"
    staged_platforms.mkdir(parents=True, exist_ok=True)
    for src in platform_files:
        _copy_if_needed(src, staged_platforms / src.name)
    return staged_root, staged_platforms


def ensure_qt_plugin_path() -> None:
    """Make PyQt6 platform plugins discoverable before QApplication starts."""
    try:
        import PyQt6  # noqa: F401 -- only used for package location
    except ImportError:
        return

    pkg_dir = Path(PyQt6.__file__).resolve().parent
    plugins_root = pkg_dir / "Qt6" / "plugins"
    if not plugins_root.is_dir():
        return

    plugin_root_for_env = plugins_root
    platform_for_env = plugins_root / "platforms"
    if platform_for_env.is_dir():
        staged = _stage_platform_plugins(platform_for_env)
        if staged is not None:
            plugin_root_for_env, platform_for_env = staged
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platform_for_env))
    os.environ.setdefault("QT_PLUGIN_PATH", str(plugin_root_for_env))
