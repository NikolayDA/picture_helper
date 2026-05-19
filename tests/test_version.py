"""Versionskonsistenz.

``__version__`` wird primär aus den Paket-Metadaten gelesen. Für den
Quelle-Lauf ohne installiertes Paket existiert ein Fallback-Literal im
Paket-``__init__``; dieses muss mit der in ``pyproject.toml`` deklarierten
Version übereinstimmen, sonst zeigt ein solcher Lauf eine falsche Version.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INIT = "bgremover/__init__.py"


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_pyproject_version_matches_source_fallback() -> None:
    m = re.search(r'^version\s*=\s*"([^"]+)"', _read("pyproject.toml"), re.M)
    assert m, "version fehlt in pyproject.toml"

    m2 = re.search(r'__version__\s*=\s*"([^"]+)"', _read(INIT))
    assert m2, f"Fallback-__version__ fehlt in {INIT}"
    assert m2.group(1) == m.group(1), (
        f"Fallback in {INIT} != pyproject-Version – ein Quelle-Lauf "
        "ohne Installation würde eine falsche Version anzeigen."
    )


def test_version_is_sourced_from_package_metadata() -> None:
    src = _read(INIT)
    assert '_pkg_version("bgremover")' in src, (
        "__version__ muss aus den Paket-Metadaten kommen (Single Source), "
        "damit pyproject.toml die maßgebliche Versionsquelle bleibt."
    )
