"""Konsistenzprüfungen für die mehrsprachigen String-Tabellen des
Lizenz-Report-Generators.

Stellt sicher, dass jede Sprache exakt dieselben Schlüssel wie das
deutsche Referenzset hat, Listen gleich lang sind, und der Report für
alle Sprachen ohne Format-/KeyError rendert.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "generate_license_report", ROOT / "scripts" / "generate_license_report.py"
)
glr = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(glr)


TARGET_LANGS = ["en", "es", "fr", "uk", "zh"]

# build_reports() parst pyproject.toml via tomllib (Python 3.11+).
# Auf Python 3.10 ohne 'tomli'-Backport diese Fälle überspringen –
# die String-Tabellen-Konsistenz wird davon unabhängig geprüft.
needs_toml = pytest.mark.skipif(
    glr.tomllib is None,
    reason="tomllib nicht verfügbar (Python < 3.11, kein tomli-Backport)",
)


def _shape(obj):
    """Strukturelle Signatur: Dicts -> {key: shape}, Listen -> Länge,
    Strings -> 'str'. Erlaubt rekursiven Schlüssel-/Längenvergleich."""
    if isinstance(obj, dict):
        return {k: _shape(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return ("list", len(obj))
    return "str"


def test_all_langs_present():
    assert set(glr.STRINGS) == set(glr.LANGS)
    assert set(glr.LANGS) == {"de", *TARGET_LANGS}


@pytest.mark.parametrize("lang", TARGET_LANGS)
def test_key_and_length_parity_with_german(lang):
    assert _shape(glr.STRINGS[lang]) == _shape(glr.STRINGS["de"]), (
        f"STRINGS[{lang!r}] weicht in Schlüsseln oder Listenlängen vom "
        f"deutschen Referenzset ab."
    )


def test_verdict_branch_lengths():
    for lang in glr.LANGS:
        v = glr.STRINGS[lang]["verdict"]
        assert len(v["gpl"]) == 4
        assert len(v["weak"]) == 3
        assert len(v["permissive"]) == 3


def test_assessment_keys_match_license_categories():
    for lang in glr.LANGS:
        assert set(glr.STRINGS[lang]["assessment"]) == set(glr.LICENSE_CATEGORY)


@needs_toml
@pytest.mark.parametrize("lang", glr.LANGS)
def test_build_reports_renders_without_error(lang):
    nav = glr._switcher(lang, "LICENSES.md", at_root=(lang == "de"))
    full, summary = glr.build_reports(ROOT, lang, nav)
    assert full.strip() and summary.strip()
    # Switcher steht als erste Zeile des vollständigen Reports.
    assert full.splitlines()[0] == nav
    # Keine unaufgelösten Platzhalter im gerenderten Output.
    for blob in (full, summary):
        for token in ("{name}", "{version}", "{lic}", "{count}",
                      "{generated}", "{legend}", "{project_license}",
                      "{path}"):
            assert token not in blob, f"{token} nicht aufgelöst ({lang})"


@pytest.mark.parametrize("lang", glr.LANGS)
def test_classify_returns_known_license_key(lang):
    for raw in ("MIT", "GPL-3.0-only", "Apache-2.0", "", "Nonsense-XYZ",
                "LGPL-3.0", "MPL-2.0"):
        cat, key, _ = glr.classify(raw)
        assert key in glr.LICENSE_CATEGORY
        assert cat == glr.LICENSE_CATEGORY[key]
        # Bewertungstext existiert in jeder Sprache für diesen Key.
        assert glr.STRINGS[lang]["assessment"][key].strip()


@needs_toml
def test_german_output_deterministic():
    nav = glr._switcher("de", "LICENSES.md", at_root=True)
    a, sa = glr.build_reports(ROOT, "de", nav)
    b, sb = glr.build_reports(ROOT, "de", nav)
    assert a == b and sa == sb


def test_switcher_relative_paths():
    root_nav = glr._switcher("de", "LICENSES.md", at_root=True)
    assert "**Deutsch**" in root_nav
    assert "[English](docs/i18n/en/LICENSES.md)" in root_nav

    en_nav = glr._switcher("en", "LICENSES.md", at_root=False)
    assert "**English**" in en_nav
    assert "[Deutsch](../../../LICENSES.md)" in en_nav
    assert "[Español](../es/LICENSES.md)" in en_nav
