"""Qt-Pluginpfad-Setup für App-Start und lokale Test-Helfer."""

from __future__ import annotations

import atexit
import contextlib
import hashlib
import os
import re
import secrets
import shutil
import stat
import sys
import tempfile
import threading
import time
from importlib import metadata
from pathlib import Path
from typing import BinaryIO

try:
    import fcntl
except ImportError:  # pragma: no cover - nur auf nicht unterstützten Nicht-POSIX-Systemen
    fcntl = None  # type: ignore[assignment]

UF_HIDDEN = 0x8000
_POSIX = os.name == "posix"
_PROCESS_TOKEN = secrets.token_hex(8)
_STAGE_INSTANCE_RE = re.compile(r"^.+_[0-9a-f]{16}_pid[0-9]+_[0-9a-f]{16}$")
_LEGACY_STAGE_RE = re.compile(r"^.+_[0-9a-f]{16}$")
_UNLEASED_STAGE_GRACE_SECONDS = 300
_STAGE_LEASES: dict[Path, BinaryIO] = {}
_STAGE_LEASES_LOCK = threading.Lock()


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


def _remove_stage_dir(path: Path) -> None:
    """Entfernt ausschließlich einen weiterhin sicheren Staging-Unterordner.

    Der ``lstat``-basierte Check verhindert, dass ein nachträglich ersetzter
    Pfad als Symlink verfolgt wird. Symlinks *innerhalb* des Baums werden von
    ``shutil.rmtree`` nur entfernt, nicht traversiert.
    """
    if _secure_dir(path):
        shutil.rmtree(path, ignore_errors=True)


def _cleanup_stage_dir(path: Path) -> None:
    """Gibt die Prozess-Lease frei und entfernt den eigenen Staging-Baum."""
    with _STAGE_LEASES_LOCK:
        lease = _STAGE_LEASES.pop(path, None)
        if lease is None:
            # Nach fork() erbt das Kind zwar registrierte atexit-Handler, aber
            # nicht die Besitzberechtigung am Staging-Baum des Elternprozesses.
            return

        # Auf POSIX bleibt die Lease während des Löschens gesperrt. Dadurch
        # kann kein parallel startender Prozess denselben Baum zugleich als
        # verwaist einstufen. Nicht-POSIX-Systeme müssen offene Dateien vor
        # rmtree schließen. Der Lock hält zugleich Threads dieses Prozesses
        # von einem erneuten Acquire desselben Pfads ab.
        if lease is not None and not _POSIX:
            with contextlib.suppress(OSError):
                lease.close()
            lease = None
        _remove_stage_dir(path)
        if lease is not None:
            with contextlib.suppress(OSError):
                lease.close()


def _reset_stage_leases_after_fork() -> None:
    """Verwirft im Kind geerbte Leases, ohne Eltern-Bäume anzufassen."""
    global _PROCESS_TOKEN, _STAGE_LEASES_LOCK

    # Ein Lock kann beim fork in einem anderen, nun nicht mehr vorhandenen
    # Thread gehalten worden sein. Deshalb im Kind nicht übernehmen/akquirieren,
    # sondern durch ein frisches Lock ersetzen.
    for lease in _STAGE_LEASES.values():
        with contextlib.suppress(OSError):
            lease.close()
    _STAGE_LEASES.clear()
    _STAGE_LEASES_LOCK = threading.Lock()
    _PROCESS_TOKEN = secrets.token_hex(8)


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_reset_stage_leases_after_fork)


def _acquire_stage_lease(path: Path) -> bool:
    """Hält eine exklusive Prozess-Lease für *path* bis zum Programmende.

    Jede App-Instanz erhält einen eigenen Staging-Baum. Die gesperrte
    ``.lease``-Datei macht zusätzlich auch nach einem harten Prozessabbruch
    erkennbar, ob ein fremder Baum noch aktiv ist: Der Kernel gibt die Sperre
    beim Prozessende automatisch frei.
    """
    with _STAGE_LEASES_LOCK:
        if path in _STAGE_LEASES:
            return True

        # Check, Lock-Aufnahme und Registrierung bilden einen kritischen
        # Abschnitt. Sonst könnten zwei Threads desselben Prozesses zugleich
        # öffnen; der Verlierer würde den gerade vom Gewinner belegten Baum
        # fälschlich als Acquire-Fehler wieder löschen.
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd: int | None = None
        lease: BinaryIO | None = None
        try:
            fd = os.open(path / ".lease", flags, 0o600)
            lease = os.fdopen(fd, "r+b", buffering=0)
            fd = None  # fdopen besitzt den Deskriptor ab hier.
            if fcntl is not None:
                fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            lease.seek(0)
            lease.truncate()
            lease.write(f"{os.getpid()}\n".encode("ascii"))
        except (OSError, BlockingIOError):
            if lease is not None:
                with contextlib.suppress(OSError):
                    lease.close()
            elif fd is not None:
                with contextlib.suppress(OSError):
                    os.close(fd)
            return False

        _STAGE_LEASES[path] = lease
    atexit.register(_cleanup_stage_dir, path)
    return True


def _legacy_stage_is_stale(path: Path) -> bool:
    """Erkennt alte AppImage-Bäume sicher an ihrem gebrochenen ``lib``-Link.

    Vor Einführung der Leases enthielt der Verzeichnisname nur den Hash des
    Quellpfads. Bei einem beendeten AppImage verschwindet dessen zufälliger
    Mount-Pfad und der Link wird gebrochen. Ein noch erreichbares Ziel wird
    vorsichtshalber als aktiv behandelt; stabile venv-Pfade erzeugen ohnehin
    höchstens einen solchen Baum.
    """
    lib_link = path / "Qt6" / "lib"
    return lib_link.is_symlink() and not lib_link.exists()


def _prune_stale_stage_dirs(root: Path) -> None:
    """Entfernt verwaiste Instanz-Bäume, ohne aktive Prozesse zu stören."""
    if not _secure_dir(root):
        return

    try:
        candidates = list(root.iterdir())
    except OSError:
        return

    now = time.time()
    for candidate in candidates:
        if not _secure_dir(candidate):
            continue
        is_instance = _STAGE_INSTANCE_RE.fullmatch(candidate.name) is not None
        if not is_instance:
            if _LEGACY_STAGE_RE.fullmatch(candidate.name) and _legacy_stage_is_stale(candidate):
                _remove_stage_dir(candidate)
            continue

        # Auf manchen BSD-Systemen sind flock-Sperren pro Prozess statt pro
        # File-Description zusammengeführt. Eigene Leases deshalb explizit
        # überspringen, statt probeweise eine zweite Sperre zu öffnen.
        with _STAGE_LEASES_LOCK:
            if candidate in _STAGE_LEASES:
                continue

        lease_path = candidate / ".lease"
        flags = os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(lease_path, flags)
        except FileNotFoundError:
            # Crash im kurzen Fenster zwischen mkdir und Lease-Erstellung:
            # erst nach einer Schonfrist löschen, damit kein aktiver Starter
            # seinen eben angelegten Baum verliert.
            with contextlib.suppress(OSError):
                if now - candidate.stat().st_mtime >= _UNLEASED_STAGE_GRACE_SECONDS:
                    _remove_stage_dir(candidate)
            continue
        except OSError:
            continue

        lease = os.fdopen(fd, "r+b", buffering=0)
        if fcntl is None:
            lease.close()
            continue
        try:
            fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lease.close()
            continue
        except OSError:
            lease.close()
            continue

        # Die Sperre bleibt bis nach rmtree bestehen, damit ein paralleler
        # Pruner nicht denselben Baum gleichzeitig übernimmt.
        _remove_stage_dir(candidate)
        lease.close()


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

    Der Staging-Unterordner wird zusätzlich zur Qt6-Version über Quellpfad,
    PID und einen zufälligen Prozesstoken benannt. Dadurch teilen weder zwei
    AppImage-Mounts noch zwei Prozesse denselben ``Qt6/lib``-Symlink. Eine
    exklusive Lease schützt aktive Bäume; beim normalen Prozessende wird der
    eigene Baum entfernt, nach einem harten Abbruch räumt ihn der nächste
    Start auf. So bleibt die Parallelitätsisolation erhalten, ohne bei jedem
    AppImage-Start dauerhaft einen neuen Temp-Baum zu hinterlassen.
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
    stage_name = f"{qt_version}_{source_key}_pid{os.getpid()}_{_PROCESS_TOKEN}"
    staged_root = _secure_stage_root(base_tmp, stage_name)
    if staged_root is None:
        return None
    if not _acquire_stage_lease(staged_root):
        _remove_stage_dir(staged_root)
        return None
    _prune_stale_stage_dirs(staged_root.parent)

    staged_qt6 = staged_root / "Qt6"
    staged_plugins = staged_qt6 / "plugins"
    staged_platforms = staged_plugins / "platforms"
    try:
        staged_qt6.mkdir(mode=0o700, exist_ok=True)
        staged_plugins.mkdir(mode=0o700, exist_ok=True)
        staged_platforms.mkdir(mode=0o700, exist_ok=True)
    except OSError:
        _cleanup_stage_dir(staged_root)
        return None
    try:
        for src in platform_files:
            _copy_if_needed(src, staged_platforms / src.name)
    except OSError:
        _cleanup_stage_dir(staged_root)
        return None

    if not _ensure_lib_symlink(staged_qt6, real_lib):
        _cleanup_stage_dir(staged_root)
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
