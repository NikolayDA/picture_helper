"""Drift-Schutz für die pip-Sicherheitsmindestversion (#202).

`pip` ist **keine** deklarierte Projekt-Abhängigkeit, sondern das
Installationswerkzeug selbst – es lässt sich daher nicht über
``requirements/constraints.txt`` anheben. Stattdessen wird die gepatchte
Mindestversion an jeder Stelle erzwungen, die mit pip installiert: in den
sechs pip-installierenden CI-Workflows und im Web-SessionStart-Hook.

Hintergrund: pip 24.0 trägt fünf bekannte CVEs (Path-Traversal in der
Wheel-Extraktion, Symlink-Angriff, Modul-Hijacking beim Self-Update,
Entry-Points ausserhalb des Zielverzeichnisses, mehrdeutige tar+ZIP-Archive).
Alle fünf sind ab pip 26.1.2 geschlossen. Fehlt der Pin in einer Datei,
zieht der Runner/Container wieder die verwundbare Default-Version – dieser
Test hält die Stellen konsistent (vgl. Befund N6 / test_ci_qt_packages.py).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

_ROOT = Path(__file__).resolve().parent.parent

# Stellen, die pip vor dem Installieren anheben müssen. Die sechs
# pip-installierenden CI-Workflows plus der Web-SessionStart-Hook.
# ``release-linux.yml`` fehlt bewusst – es baut nur AppImages über ein
# isoliertes Tooling-venv und installiert das Projekt nicht in den Runner.
_PIP_PIN_SOURCES = (
    ".github/workflows/ci.yml",
    ".github/workflows/pr-ci.yml",
    ".github/workflows/ui-nightly.yml",
    ".github/workflows/benchmark.yml",
    ".github/workflows/license-check.yml",
    ".github/workflows/dependency-audit.yml",
    ".claude/hooks/session-start.sh",
)

# Erste Version, die alle fünf #202-CVEs schliesst (Entry-Points-Fix: 26.1.2).
_MIN_PIP = Version("26.1.2")
# Höchste verwundbare Version unmittelbar darunter (CVE-2026-8643).
_LAST_VULNERABLE = Version("26.1.1")
# Die in CI/Dev tatsächlich vorgefundene Altversion.
_FOUND_IN_THE_WILD = Version("24.0")

_PIP_SPEC_RE = re.compile(r'pip(?:>=|==)[0-9][0-9A-Za-z.\-]*')


def _pip_requirement(text: str) -> Requirement | None:
    """Erste pip-Versionsspezifikation (``pip>=…``/``pip==…``) im Text.

    ``cache: pip`` und blanke ``pip install``-Aufrufe (ohne Operator) matchen
    bewusst nicht – nur ein expliziter Pin zählt.
    """
    match = _PIP_SPEC_RE.search(text)
    if match is None:
        return None
    return Requirement(match.group(0))


@pytest.mark.parametrize("rel_path", _PIP_PIN_SOURCES)
def test_pip_is_pinned_to_patched_release(rel_path: str) -> None:
    text = (_ROOT / rel_path).read_text(encoding="utf-8")
    req = _pip_requirement(text)
    assert req is not None, (
        f"{rel_path} hebt pip nicht auf eine gepinnte Version – erwartet "
        f'`pip install --upgrade \"pip>=26.1.2\"` (CVE-Batch #202).'
    )

    spec = req.specifier
    assert _MIN_PIP in spec, (
        f"{rel_path}: pip-Pin {req} laesst die gepatchte {_MIN_PIP} nicht zu."
    )
    assert _LAST_VULNERABLE not in spec, (
        f"{rel_path}: pip-Pin {req} erlaubt die verwundbare {_LAST_VULNERABLE} "
        f"(CVE-2026-8643, Entry-Points ausserhalb des Zielverzeichnisses)."
    )
    assert _FOUND_IN_THE_WILD not in spec, (
        f"{rel_path}: pip-Pin {req} erlaubt die in CI/Dev gefundene "
        f"{_FOUND_IN_THE_WILD} (5 CVEs)."
    )
