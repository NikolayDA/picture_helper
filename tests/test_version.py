"""Versionskonsistenz.

``__version__`` wird primär aus den Paket-Metadaten gelesen. Für den
Quelle-Lauf ohne installiertes Paket existiert ein Fallback-Literal in
``BgRemover.py``; dieses muss mit der in ``pyproject.toml`` deklarierten
Version übereinstimmen, sonst zeigt ein solcher Lauf eine falsche Version.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_pyproject_version_matches_source_fallback() -> None:
    m = re.search(r'^version\s*=\s*"([^"]+)"', _read("pyproject.toml"), re.M)
    assert m, "version fehlt in pyproject.toml"

    m2 = re.search(r'__version__\s*=\s*"([^"]+)"', _read("BgRemover.py"))
    assert m2, "Fallback-__version__ fehlt in BgRemover.py"
    assert m2.group(1) == m.group(1), (
        "Fallback in BgRemover.py != pyproject-Version – ein Quelle-Lauf "
        "ohne Installation würde eine falsche Version anzeigen."
    )


def test_version_is_sourced_from_package_metadata() -> None:
    src = _read("BgRemover.py")
    assert '_pkg_version("bgremover")' in src, (
        "__version__ muss aus den Paket-Metadaten kommen (Single Source), "
        "damit pyproject.toml die maßgebliche Versionsquelle bleibt."
    )
