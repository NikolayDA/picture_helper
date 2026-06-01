"""Qt plugin path setup shared by the app and local test helpers."""

from __future__ import annotations

import contextlib
import hashlib
import os
import shutil
import stat
import sys
import tempfile
from importlib import metadata
from pathlib import Path

UF_HIDDEN = 0x8000
_POSIX = os.name == "posix"


def _dist_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "unknown"


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _secure_dir(path: Path) -> bool:
    """True, wenn *path* ein echtes, nur dem aktuellen Nutzer zugängliches
    Verzeichnis ist: kein Symlink, Eigentümer = wir, keine Rechte für
    Gruppe/andere.

    ``lstat`` (nicht ``stat``) entlarvt einen untergeschobenen Symlink, der
    sonst auf ein fremdes Ziel zeigen könnte. Auf Nicht-POSIX-Systemen wird
    nur geprüft, dass es ein echtes Verzeichnis ist – dort ist das
    Temp-Verzeichnis bereits pro Benutzerprofil isoliert und das
    Unix-Rechtemodell greift nicht.
    """
    try:
        info = path.lstat()
    except OSError:
        return False
    if not stat.S_ISDIR(info.st_mode):
        return False
    if not _POSIX:
        return True
    if info.st_uid != os.geteuid():
        return False
    return not (info.st_mode & 0o077)


def _secure_stage_root(base_tmp: Path, qt_version: str) -> Path | None:
    """Legt ein nutzerspezifisches ``0700``-Staging-Verzeichnis an und gibt
    den versionierten Unterordner zurück; ``None``, wenn der Pfad nicht
    abgesichert werden kann.

    Der frühere Code nutzte einen für alle Nutzer vorhersagbaren,
    welt-schreibbaren Pfad (``/private/tmp/bgremover_qt_plugins/<ver>``). Ein
    anderer lokaler Nutzer konnte dort die ausführbaren Qt-Plugin-Dylibs
    vorab platzieren – beim ``QApplication``-Start hätte Qt fremden Code aus
    diesem Verzeichnis geladen. Ein nutzerspezifisches, auf ``0700``
    beschränktes Verzeichnis (Name inkl. UID) schließt dieses Pre-Seeding
    aus: gehört das Verzeichnis bereits jemand anderem, schlägt ``chmod``
    fehl bzw. ``_secure_dir`` lehnt ab und das Staging unterbleibt.
    """
    uid = os.geteuid() if _POSIX else 0
    root = base_tmp / f"bgremover_qt_plugins_{uid}"
    try:
        root.mkdir(mode=0o700, exist_ok=True)
        # mkdir wendet ``mode`` bei bereits existierendem Verzeichnis nicht
        # an – Rechte daher explizit nachziehen. Gehört ``root`` einem
        # anderen Nutzer, wirft chmod und wir steigen sicher aus.
        if _POSIX:
            os.chmod(root, 0o700)
    except OSError:
        return None
    if not _secure_dir(root):
        return None
    versioned = root / qt_version
    try:
        versioned.mkdir(mode=0o700, exist_ok=True)
    except OSError:
        return None
    return versioned if _secure_dir(versioned) else None


def _copy_if_needed(src: Path, dst: Path) -> None:
    """Kopiert *src* nach *dst*, wenn nötig – atomar und ohne vorhersagbare
    Zwischendatei.

    Ein SHA-256-Inhaltsvergleich (statt des früheren reinen Größenvergleichs)
    entscheidet, ob neu kopiert wird: eine untergeschobene Datei gleicher
    Größe würde sonst unbemerkt geladen. Die Zwischendatei bekommt über
    ``mkstemp`` einen eindeutigen Namen im Zielverzeichnis – kein fester
    ``.tmp``-Name, den ein Angreifer vorab als Symlink anlegen könnte.
    """
    if dst.exists():
        dst_stat = dst.stat()
        dst_hidden = bool(getattr(dst_stat, "st_flags", 0) & UF_HIDDEN)
        if not dst_hidden and _file_sha256(src) == _file_sha256(dst):
            return

    fd, tmp_name = tempfile.mkstemp(dir=str(dst.parent), prefix=f".{dst.name}.")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as out, open(src, "rb") as in_:
            shutil.copyfileobj(in_, out)
        os.chmod(tmp, src.stat().st_mode & 0o777)
        os.replace(tmp, dst)
    except OSError:
        with contextlib.suppress(OSError):
            tmp.unlink()
        raise


def _stage_platform_plugins(platforms: Path) -> tuple[Path, Path] | None:
    """Copy Qt platform plugins to temp if they are visible to Python.

    Some macOS runners can let Python list a venv under Documents while Qt's
    own directory listing sees an empty plugin directory. A temp copy avoids
    that privacy/sandbox edge case without changing the user's environment.
    Das Staging-Ziel ist ein nutzerspezifisches ``0700``-Verzeichnis (siehe
    ``_secure_stage_root``); lässt es sich nicht absichern, unterbleibt das
    Staging und der Aufrufer fällt auf den Original-Pluginpfad zurück.
    """
    platform_files = [p for p in platforms.iterdir() if p.is_file()]
    if not platform_files:
        return None

    base_tmp = Path(tempfile.gettempdir())
    private_tmp = Path("/private/tmp")
    if sys.platform == "darwin" and private_tmp.is_dir() and os.access(private_tmp, os.W_OK):
        base_tmp = private_tmp

    qt_version = _dist_version("PyQt6-Qt6").replace(os.sep, "_").replace(".", "_")
    staged_root = _secure_stage_root(base_tmp, qt_version)
    if staged_root is None:
        return None
    staged_platforms = staged_root / "platforms"
    try:
        staged_platforms.mkdir(mode=0o700, exist_ok=True)
    except OSError:
        return None
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
