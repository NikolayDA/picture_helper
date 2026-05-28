"""Soft-Drift-Prüfung: strukturelle Synchronität zwischen DE-Original
und i18n-Kopien für CHANGELOG.md, INSTALL_MAC.md und INSTALL_LINUX.md.

„Strukturell" = identische Heading-Hierarchie und identische Anzahl
Code-Blöcke. Abweichungen schlagen nicht hart fehl, sondern werden als
pytest.warns-kompatible Warnungen ausgegeben, damit das CI grün bleibt,
aber Drift sichtbar wird.
"""
from __future__ import annotations

import re
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N_ROOT = ROOT / "docs" / "i18n"
LANGUAGES = ("en", "es", "fr", "uk", "zh")

WATCHED_DOCS = (
    "CHANGELOG.md",
    "INSTALL_MAC.md",
    "INSTALL_LINUX.md",
)

_HEADING_RE = re.compile(r"^(#{1,6})\s+\S", re.MULTILINE)
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _without_fenced_code(text: str) -> str:
    lines: list[str] = []
    in_block = False
    fence_char = ""
    for line in text.splitlines():
        match = _FENCE_RE.match(line)
        if match:
            current = match.group(1)[0]
            if not in_block:
                in_block = True
                fence_char = current
            elif current == fence_char:
                in_block = False
                fence_char = ""
            continue
        if not in_block:
            lines.append(line)
    return "\n".join(lines)


def _heading_levels(text: str) -> list[int]:
    return [
        len(m.group(1))
        for m in _HEADING_RE.finditer(_without_fenced_code(text))
    ]


def _count_code_blocks(text: str) -> int:
    count = 0
    in_block = False
    fence_char = ""
    for line in text.splitlines():
        match = _FENCE_RE.match(line)
        if not match:
            continue
        current = match.group(1)[0]
        if not in_block:
            count += 1
            in_block = True
            fence_char = current
        elif current == fence_char:
            in_block = False
            fence_char = ""
    return count


def _check_drift(name: str) -> list[str]:
    """Gibt eine Liste lesbarer Abweichungsmeldungen zurück (leer = kein Drift)."""
    canonical_path = ROOT / name
    if not canonical_path.is_file():
        return [f"Kanonische Datei fehlt: {name}"]

    canonical_text = _read(canonical_path)
    expected_headings = _heading_levels(canonical_text)
    expected_blocks = _count_code_blocks(canonical_text)

    diffs: list[str] = []
    for lang in LANGUAGES:
        path = I18N_ROOT / lang / name
        if not path.is_file():
            diffs.append(f"{lang}/{name}: Datei fehlt")
            continue
        text = _read(path)
        actual_headings = _heading_levels(text)
        actual_blocks = _count_code_blocks(text)
        if actual_headings != expected_headings:
            diffs.append(
                f"{lang}/{name}: Heading-Hierarchie weicht ab – "
                f"erwartet {expected_headings}, gefunden {actual_headings}"
            )
        if actual_blocks != expected_blocks:
            diffs.append(
                f"{lang}/{name}: Code-Blöcke weichen ab – "
                f"erwartet {expected_blocks}, gefunden {actual_blocks}"
            )
    return diffs


def test_i18n_sync_soft_drift() -> None:
    """Soft-Drift-Prüfung: gibt Warnungen aus, schlägt nicht hart fehl."""
    all_diffs: list[str] = []
    for name in WATCHED_DOCS:
        all_diffs.extend(_check_drift(name))

    if all_diffs:
        message = (
            "i18n-Struktur-Drift festgestellt (kein harter Fehler – bitte prüfen):\n"
            + "\n".join(f"  • {d}" for d in all_diffs)
        )
        warnings.warn(message, stacklevel=1)
