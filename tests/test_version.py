"""Versionskonsistenz.

``__version__`` wird primär aus den Paket-Metadaten gelesen. Für den
Quelle-Lauf ohne installiertes Paket liest das Paket ``pyproject.toml``
direkt – ein hardgecodetes Fallback-Literal entfällt, damit ein
Versionsbump nicht versehentlich nur eine der beiden Stellen anfasst.
"""
import re
from pathlib import Path

import bgremover

ROOT = Path(__file__).resolve().parent.parent
VERSION_MODULE = "bgremover/_version.py"


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _pyproject_version() -> str:
    m = re.search(r'^version\s*=\s*"([^"]+)"', _read("pyproject.toml"), re.M)
    assert m, "version fehlt in pyproject.toml"
    return m.group(1)


def test_version_is_sourced_from_package_metadata() -> None:
    src = _read(VERSION_MODULE)
    assert '_pkg_version("bgremover")' in src, (
        "__version__ muss primaer aus den Paket-Metadaten kommen (Single "
        "Source), damit pyproject.toml die maßgebliche Versionsquelle bleibt."
    )


def test_source_fallback_reads_pyproject_directly() -> None:
    """Der Source-Lauf-Fallback liest pyproject.toml zur Laufzeit –
    kein hardgecodetes Versions-Literal mehr, das beim Bump vergessen
    werden könnte."""
    assert bgremover._read_pyproject_version() == _pyproject_version()


def test_exported_version_matches_pyproject() -> None:
    """``bgremover.__version__`` muss zur in pyproject.toml deklarierten
    Version passen – egal ob via Paket-Metadaten oder Source-Fallback."""
    assert bgremover.__version__ == _pyproject_version()
