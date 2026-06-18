"""Schnelltest: die in LICENSES.md eingebettete Version == pyproject-Version (#310).

Beim 2.4.1-Release-Bump trug ``LICENSES.md`` noch ``bgremover 2.4.0`` im Titel →
nur der schwere ``License Check``-Workflow (installiert ``.[ai,test]`` +
``pip-licenses`` und läuft separat) fiel darauf herein, die schnelle Unit-Suite
nicht. Dieser netz- und tooling-freie Test fängt die Drift bereits zur PR-Zeit
ab (läuft im normalen ``make test``); der autoritative Volltest bleibt in
``.github/workflows/license-check.yml``.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Root-Doku + alle fünf Übersetzungen.
LICENSE_DOCS = (
    ROOT / "LICENSES.md",
    *(
        ROOT / "docs" / "i18n" / lang / "LICENSES.md"
        for lang in ("en", "es", "fr", "uk", "zh")
    ),
)

# Die H1-Titelzeile (einzelnes ``#``) endet auf ``… – bgremover <version>``.
# ``^#\s`` trifft nur H1 (``##`` & Folgezeilen werden nicht erfasst).
_TITLE_VERSION_RE = re.compile(r"(?m)^#\s+.*\bbgremover\s+(\S+)\s*$")

_REGEN_HINT = (
    "LICENSES.md und docs/i18n/*/LICENSES.md nach einem Versions-Bump neu "
    "generieren (siehe .github/workflows/license-check.yml bzw. "
    "scripts/generate_license_report.py)."
)


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', text)
    assert match, "version nicht in pyproject.toml [project] gefunden"
    return match.group(1)


def _embedded_version(path: Path) -> str:
    match = _TITLE_VERSION_RE.search(path.read_text(encoding="utf-8"))
    assert match, (
        f"{path.relative_to(ROOT)}: keine '# … bgremover <version>'-Titelzeile "
        f"gefunden. {_REGEN_HINT}"
    )
    return match.group(1)


def test_license_docs_exist() -> None:
    for path in LICENSE_DOCS:
        assert path.is_file(), f"fehlende Lizenz-Doku: {path.relative_to(ROOT)}"


def test_license_docs_embed_pyproject_version() -> None:
    """Jede LICENSES.md trägt die aktuelle ``pyproject [project].version``.

    Wird ``pyproject`` gebumpt, ohne die Reports neu zu generieren, schlägt
    dieser Test fehl – mit klarem Hinweis auf den Regenerierungsweg.
    """
    expected = _pyproject_version()
    mismatches = {
        str(path.relative_to(ROOT)): version
        for path in LICENSE_DOCS
        if (version := _embedded_version(path)) != expected
    }
    assert not mismatches, (
        f"LICENSES-Titelversion weicht von pyproject [project].version "
        f"({expected}) ab: {mismatches}. {_REGEN_HINT}"
    )
