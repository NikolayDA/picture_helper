"""Versionskonsistenz.

``__version__`` wird primär aus den Paket-Metadaten gelesen. Für den
Quelle-Lauf ohne installiertes Paket liest das Paket ``pyproject.toml``
direkt – ein hardgecodetes Fallback-Literal entfällt, damit ein
Versionsbump nicht versehentlich nur eine der beiden Stellen anfasst.
"""
import re
from importlib.metadata import PackageNotFoundError
from pathlib import Path

import bgremover
from bgremover import _version

ROOT = Path(__file__).resolve().parent.parent


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _pyproject_version() -> str:
    m = re.search(r'^version\s*=\s*"([^"]+)"', _read("pyproject.toml"), re.M)
    assert m, "version fehlt in pyproject.toml"
    return m.group(1)


def test_version_prefers_package_metadata_over_pyproject_fallback(monkeypatch) -> None:
    """``get_version()`` muss verfügbare Paket-Metadaten immer vor dem
    pyproject-Fallback verwenden (Single Source of Truth), damit ein
    installiertes Paket nicht versehentlich die Quelldatei statt seiner
    eigenen Metadaten meldet."""
    monkeypatch.setattr(_version, "_pkg_version", lambda _name: "9.9.9-from-metadata")

    def _unexpected_fallback() -> str:
        raise AssertionError(
            "pyproject-Fallback wurde aufgerufen, obwohl Paket-Metadaten "
            "verfügbar waren")

    monkeypatch.setattr(_version, "_read_pyproject_version", _unexpected_fallback)

    assert _version.get_version() == "9.9.9-from-metadata"


def test_source_fallback_reads_pyproject_directly() -> None:
    """Der Source-Lauf-Fallback liest pyproject.toml zur Laufzeit –
    kein hardgecodetes Versions-Literal mehr, das beim Bump vergessen
    werden könnte."""
    assert bgremover._read_pyproject_version() == _pyproject_version()


def test_exported_version_matches_pyproject() -> None:
    """``bgremover.__version__`` muss zur in pyproject.toml deklarierten
    Version passen – egal ob via Paket-Metadaten oder Source-Fallback."""
    assert bgremover.__version__ == _pyproject_version()


def test_version_lookup_never_crashes_without_metadata_or_pyproject(monkeypatch) -> None:
    """Fehlen Paket-Metadaten UND pyproject.toml (eingefrorenes Bundle ohne
    eingebackene Metadaten), darf die Versionsermittlung den Import von
    ``bgremover`` nicht abbrechen – sonst startet die macOS-.dmg-App nicht.
    Erwartet wird ein nicht-leerer ``unbekannt``-Sentinel statt einer Exception.
    """
    def _no_metadata(_name: str) -> str:
        raise PackageNotFoundError("bgremover")

    def _no_pyproject() -> str:
        raise FileNotFoundError("keine pyproject.toml im Bundle")

    monkeypatch.setattr(_version, "_pkg_version", _no_metadata)
    monkeypatch.setattr(_version, "_read_pyproject_version", _no_pyproject)

    result = _version.get_version()
    assert isinstance(result, str)
    assert result
