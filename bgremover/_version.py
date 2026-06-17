"""Qt-unabhängige Versionsermittlung für ``bgremover.__version__``."""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path


def _read_pyproject_version() -> str:
    """Liest ``project.version`` aus ``pyproject.toml``.

    Wird nur benutzt, wenn ``importlib.metadata.version("bgremover")``
    scheitert (Paket nicht installiert). pyproject.toml ist die einzige
    Quelle der Wahrheit – kein hardgecodetes Fallback-Literal im Code,
    das beim Versionsbump vergessen werden könnte.
    """
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    try:
        import tomllib  # stdlib ab Py3.11
    except ImportError:
        # Py3.10 ohne tomli-Abhängigkeit: einfache Regex genügt, weil die
        # ``version = "..."``-Zeile im aktuellen pyproject eindeutig ist.
        import re
        m = re.search(
            r'^version\s*=\s*"([^"]+)"',
            pyproject.read_text(encoding="utf-8"),
            re.M,
        )
        return m.group(1) if m else "0.0.0"
    with pyproject.open("rb") as f:
        return tomllib.load(f)["project"]["version"]


def get_version() -> str:
    """Liefert ``__version__`` – Paket-Metadaten mit pyproject-Fallback.

    Die Versionsermittlung darf den Import von ``bgremover`` NIE scheitern
    lassen: Sie läuft als Allererstes (vor dem Qt-Stack), und ``__version__``
    ist rein informativ. Im eingefrorenen Bundle (PyInstaller) ohne
    eingebackene Metadaten UND ohne ``pyproject.toml`` würde der direkte
    Datei-Fallback sonst mit ``FileNotFoundError`` den gesamten Start
    abbrechen – genau dieser Fehler legte die macOS-.dmg-App lautlos lahm.
    """
    try:
        return _pkg_version("bgremover")
    except PackageNotFoundError:
        pass
    try:
        return _read_pyproject_version()
    except (OSError, KeyError, ValueError):
        # Weder installierte Metadaten noch lesbare pyproject.toml – die Version
        # ist unbekannt. Kein gepflegtes Versions-Literal, sondern ein reiner
        # „unbekannt"-Sentinel: der Import bleibt erfolgreich, der Start geht vor.
        return "0.0.0"
