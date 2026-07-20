"""Qt-Pluginpfad-Setup für App-Start und lokale Test-Helfer."""

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

    Ein nutzerspezifisches, auf ``0700`` beschränktes Verzeichnis (Name
    inkl. UID) verhindert, dass ein anderer lokaler Nutzer ausführbare
    Qt-Plugin-Dylibs vorab in einen gemeinsam beschreibbaren Temp-Pfad
    legt. Gehört das Verzeichnis bereits jemand anderem, schlägt
    ``chmod`` fehl bzw. ``_secure_dir`` lehnt ab und das Staging
    unterbleibt.
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

    Ein SHA-256-Inhaltsvergleich entscheidet, ob neu kopiert wird: eine
    untergeschobene Datei gleicher Größe würde sonst unbemerkt geladen.
    Die Zwischendatei bekommt über ``mkstemp`` einen eindeutigen Namen im
    Zielverzeichnis – kein fester ``.tmp``-Name, den ein Angreifer vorab
    als Symlink anlegen könnte.
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


def _ensure_lib_symlink(staged_qt6: Path, real_lib: Path) -> bool:
    """Verlinkt ``staged_qt6/lib`` sicher auf das echte Qt6-``lib``-Verzeichnis.

    Gestagte Platform-Plugins tragen ein einkompiliertes ``RUNPATH`` von
    ``$ORIGIN/../../lib`` (z. B. sucht ``libqxcb.so`` dort seine
    ``libQt6XcbQpa.so.6``). Ohne diesen Symlink läuft der Loader bei
    ``$ORIGIN/../../lib`` ins Leere und weicht auf eine ggf. inkompatible
    System-Qt6 aus (beobachtet auf Raspberry Pi OS: ``undefined symbol``).
    Die Zwischendatei bekommt über ``mkstemp`` einen eindeutigen Namen,
    damit kein vorhersagbarer Pfad kurzzeitig existiert.

    Gibt ``True`` zurück, wenn ``staged_qt6/lib`` danach korrekt auf
    *real_lib* zeigt (oder kein ``lib``-Verzeichnis existiert, z. B. bei
    manchen macOS-Layouts – dort greift dieses RUNPATH-Problem nicht).
    ``False`` signalisiert, dass der Symlink trotz vorhandenem *real_lib*
    nicht sicher hergestellt werden konnte (z. B. Dateisystem ohne
    Symlink-Unterstützung) – der Aufrufer muss das Staging dann verwerfen,
    statt einen Baum mit fehlendem RUNPATH-Ziel als nutzbar zu melden.
    """
    if not real_lib.is_dir():
        return True
    link = staged_qt6 / "lib"
    with contextlib.suppress(OSError):
        if link.is_symlink() and Path(os.readlink(link)) == real_lib:
            return True

    tmp: Path | None = None
    try:
        fd, tmp_name = tempfile.mkstemp(dir=str(staged_qt6), prefix=".lib.")
        os.close(fd)
        tmp = Path(tmp_name)
        tmp.unlink()
        os.symlink(real_lib, tmp)
        os.replace(tmp, link)
        return True
    except OSError:
        if tmp is not None:
            with contextlib.suppress(OSError):
                tmp.unlink()
        return False


def _stage_platform_plugins(platforms: Path) -> tuple[Path, Path] | None:
    """Kopiert Qt-Platform-Plugins bei Bedarf in ein Temp-Verzeichnis.

    Manche macOS-Läufe können eine venv unter ``Documents`` aus Python
    heraus lesen, während Qts eigene Verzeichnisabfrage dort keine
    Plugin-Dateien sieht. Die temporäre Kopie umgeht diesen
    Datenschutz-/Sandbox-Randfall, ohne die Nutzerumgebung zu verändern.
    Das Staging-Ziel ist ein nutzerspezifisches ``0700``-Verzeichnis (siehe
    ``_secure_stage_root``); lässt es sich nicht absichern, unterbleibt das
    Staging und der Aufrufer fällt auf den Original-Pluginpfad zurück.

    Die Verzeichnisstruktur unter dem Staging-Root spiegelt bewusst die
    Original-Verschachtelung ``Qt6/plugins/platforms`` (statt flach
    ``platforms``): Das einkompilierte Plugin-``RUNPATH``
    (``$ORIGIN/../../lib``) erwartet ein ``lib``-Verzeichnis exakt zwei
    Ebenen über den Plugin-Dateien. Ein zusätzlicher Symlink
    ``Qt6/lib`` (siehe ``_ensure_lib_symlink``) macht diesen Pfad im
    gestagten Baum auffindbar, statt beim geglätteten Layout ins Leere zu
    laufen. Lässt sich dieser Symlink nicht sicher herstellen, wird das
    Staging verworfen (``None``) statt einen Baum mit fehlendem
    RUNPATH-Ziel als nutzbar zu melden.

    Der Staging-Unterordner wird zusätzlich zur Qt6-Version über einen Hash
    des echten ``Qt6``-Quellpfads benannt: Zwei gleichzeitig laufende
    Instanzen derselben Qt6-Version, aber aus unterschiedlichen Quellen
    (z. B. zwei parallel gemountete AppImages – jedes FUSE-Mount bekommt
    einen eigenen, zufälligen Pfad), teilen sich sonst denselben
    ``Qt6/lib``-Symlink und überschreiben ihn gegenseitig; endet eine
    Instanz (Mount verschwindet), zeigt der verbliebene Symlink dann ins
    Leere. Der Hash hält solche Instanzen in getrennten Staging-Bäumen.
    """
    platform_files = [p for p in platforms.iterdir() if p.is_file()]
    if not platform_files:
        return None

    base_tmp = Path(tempfile.gettempdir())
    private_tmp = Path("/private/tmp")
    if sys.platform == "darwin" and private_tmp.is_dir() and os.access(private_tmp, os.W_OK):
        base_tmp = private_tmp

    real_lib = platforms.parent.parent / "lib"
    qt_version = _dist_version("PyQt6-Qt6").replace(os.sep, "_").replace(".", "_")
    source_key = hashlib.sha256(str(real_lib).encode("utf-8")).hexdigest()[:16]
    staged_root = _secure_stage_root(base_tmp, f"{qt_version}_{source_key}")
    if staged_root is None:
        return None

    staged_qt6 = staged_root / "Qt6"
    staged_plugins = staged_qt6 / "plugins"
    staged_platforms = staged_plugins / "platforms"
    try:
        staged_qt6.mkdir(mode=0o700, exist_ok=True)
        staged_plugins.mkdir(mode=0o700, exist_ok=True)
        staged_platforms.mkdir(mode=0o700, exist_ok=True)
    except OSError:
        return None
    for src in platform_files:
        _copy_if_needed(src, staged_platforms / src.name)

    if not _ensure_lib_symlink(staged_qt6, real_lib):
        return None

    return staged_plugins, staged_platforms


def ensure_qt_plugin_path() -> None:
    """Macht PyQt6-Platform-Plugins vor ``QApplication`` auffindbar."""
    try:
        import PyQt6  # noqa: F401 -- nur für den Paketpfad benötigt
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
