"""Regressionsschutz: ANLEITUNG/README muessen auf das neueste Screenshot-Set zeigen.

Hintergrund (#666/#668): Beim Neu-Erstellen eines Screenshot-Sets wurde das alte
Set im Repo belassen, ohne die Doku-Referenzen mitzuziehen - die Anleitung zeigte
danach auf ein totes, verwaistes Set. Dieser Test erkennt genau dieses Muster
automatisch, statt es erst im naechsten manuellen Doku-Audit zu finden.

docs/history/* ist bewusst ausgenommen: dort verlinkte Sets sind gepinnte
Abnahme-Evidenz fuer einen konkreten, abgeschlossenen Lauf (z. B. #595) und
sollen nicht dem jeweils neuesten Set folgen.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = ROOT / "app_screenshots"
SET_NAME_RE = re.compile(r"bgremover_complete_(\d{8}_\d{6})")

# Dateien, die stets auf das aktuellste Set zeigen sollen (kein Pin auf einen
# historischen Abnahmelauf wie bei docs/history/*).
CHECKED_FILES = [
    ROOT / "ANLEITUNG.md",
    ROOT / "README.md",
] + [
    ROOT / "docs" / "i18n" / lang / name
    for lang in ("en", "es", "fr", "uk", "zh")
    for name in ("ANLEITUNG.md", "README.md")
]


def _latest_set_name() -> str:
    sets = sorted(
        p.name for p in SCREENSHOTS_DIR.iterdir() if SET_NAME_RE.fullmatch(p.name)
    )
    assert sets, f"Kein Screenshot-Set unter {SCREENSHOTS_DIR} gefunden"
    return sets[-1]


def test_docs_reference_latest_screenshot_set() -> None:
    """ANLEITUNG.md/README.md (+ i18n-Spiegel) referenzieren nur das neueste Set."""

    latest = _latest_set_name()
    stale: list[str] = []

    for path in CHECKED_FILES:
        text = path.read_text(encoding="utf-8")
        referenced = set(SET_NAME_RE.findall(text))
        for name in referenced:
            if f"bgremover_complete_{name}" != latest:
                stale.append(
                    f"{path.relative_to(ROOT)} referenziert veraltetes Set "
                    f"bgremover_complete_{name} statt {latest}"
                )

    assert not stale, "Veraltete Screenshot-Set-Referenzen:\n" + "\n".join(stale)


def test_latest_screenshot_set_has_manifest() -> None:
    """Das aktuellste Set besitzt ein Manifest (Provenienz-/Inhaltsnachweis)."""

    latest = _latest_set_name()
    manifest = SCREENSHOTS_DIR / latest / "manifest.md"
    assert manifest.is_file(), f"Manifest fehlt im neuesten Set: {manifest}"
