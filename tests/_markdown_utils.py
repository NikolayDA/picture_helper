"""Geteilte Markdown-Hilfen der Doku-Wächter.

Einzige Quelle für Codeblock-Ausblendung, Linkziel-Zerlegung und die
GitHub-Ankerregel. ``tests/test_markdown_links.py`` und
``tests/test_i18n_docs.py`` importieren von hier, statt die Helfer erneut zu
kopieren (Drift-Disziplin, CLAUDE.md).
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
IMAGE_LINK_RE = re.compile(r"!\[[^\]]*]\(([^)]+)\)")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+]\(([^)]+)\)")
SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)

# ATX-Überschrift einer einzelnen Zeile: Rautenfolge, Trenner, Text.
HEADING_LINE_RE = re.compile(r"^(#{1,6})[ \t]+(\S.*)$", re.MULTILINE)
# Optionale schließende Rautenfolge einer ATX-Überschrift (CommonMark).
_CLOSING_HASHES_RE = re.compile(r"[ \t]+#+[ \t]*$")
# Inline-Link/-Bild in einer Überschrift: GitHub bildet den Anker aus dem
# gerenderten Text, also aus der Beschriftung ohne Ziel.
_INLINE_LINK_RE = re.compile(r"!?\[([^\]]*)]\([^)]*\)")
_HTML_TAG_RE = re.compile(r"<[^>]+>")

IGNORED_MARKDOWN_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "bgremover.egg-info",
    "build",
    "dist",
    "htmlcov",
}


def markdown_files(root: Path = ROOT) -> list[Path]:
    """Alle Markdown-Dateien des Repositories ohne die ausgeschlossenen Ordner."""
    return [
        path
        for path in sorted(root.rglob("*.md"))
        if not any(part in IGNORED_MARKDOWN_DIRS for part in path.relative_to(root).parts[:-1])
    ]


def iter_content_lines(text: str) -> Iterator[tuple[int, str]]:
    """Liefert ``(1-basierte Zeilennummer, Zeile)`` für alle Zeilen außerhalb
    von Codeblöcken. Die Zaunzeilen selbst zählen nicht als Inhalt."""
    in_block = False
    fence_char = ""

    for number, line in enumerate(text.splitlines(), start=1):
        match = FENCE_RE.match(line)
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
            yield number, line


def without_fenced_code(text: str) -> str:
    """Text ohne Codeblöcke; Zeilennummern verschieben sich dabei."""
    return "\n".join(line for _, line in iter_content_lines(text))


def mask_fenced_code(text: str) -> str:
    """Wie :func:`without_fenced_code`, ersetzt Codeblockzeilen aber durch
    Leerzeilen – so bleiben Zeilennummern für Fehlermeldungen erhalten."""
    kept = dict(iter_content_lines(text))
    total = len(text.splitlines())
    return "\n".join(kept.get(number, "") for number in range(1, total + 1))


def split_target(raw_target: str) -> tuple[str, str] | None:
    """Zerlegt ein Linkziel in ``(Pfadanteil, Fragment)``.

    Liefert ``None`` für leere Ziele und für Ziele mit Schema (``https:``,
    ``mailto:`` …). Beide Anteile sind prozent-dekodiert.
    """
    target = raw_target.strip()
    if not target:
        return None
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split()[0]

    if SCHEME_RE.match(target):
        return None

    path_part, _, fragment = target.partition("#")
    return unquote(path_part), unquote(fragment)


def local_target(raw_target: str) -> str | None:
    """Pfadanteil eines lokalen Linkziels; ``None`` für Schemata und reine Anker."""
    parts = split_target(raw_target)
    if parts is None:
        return None
    return parts[0] or None


def anchor_slug(heading_text: str) -> str:
    """Bildet den GitHub-Anker einer Überschrift.

    Regel: Kleinschreibung, Satzzeichen und Symbole entfallen ersatzlos
    (aus ``–``/``&``/``（）`` werden dadurch doppelte Bindestriche),
    Leerzeichen werden zu ``-``. Buchstaben, Ziffern, ``_``, ``-`` und
    kombinierende Zeichen bleiben unverändert – Umlaute, Kyrillisch und CJK
    überstehen den Anker also unbeschadet.
    """
    text = _INLINE_LINK_RE.sub(r"\1", heading_text)
    text = _HTML_TAG_RE.sub("", text).lower()
    return "".join(
        "-" if char == " " else char
        for char in text
        if char in "-_ " or char.isalnum() or unicodedata.category(char).startswith("M")
    )


def heading_anchors(text: str) -> dict[str, int]:
    """Anker → Zeilennummer der erzeugenden Überschrift.

    Überschriften in Codeblöcken zählen nicht. Mehrfach gleichnamige
    Überschriften erhalten wie bei GitHub die Suffixe ``-1``, ``-2``, …
    """
    seen: Counter[str] = Counter()
    anchors: dict[str, int] = {}

    for number, line in iter_content_lines(text):
        match = HEADING_LINE_RE.match(line)
        if not match:
            continue
        base = anchor_slug(_CLOSING_HASHES_RE.sub("", match.group(2)).rstrip())
        if not base:
            continue
        # Wie github-slugger: Der Zähler läuft je Basis-Slug, die Kollision
        # wird aber gegen die bereits *vergebenen* Anker geprüft. Sonst
        # verlöre eine Überschrift, deren Titel selbst auf ``-1`` endet,
        # ihren Anker an eine gleichnamige Dublette.
        index = seen[base]
        candidate = base if index == 0 else f"{base}-{index}"
        while candidate in anchors:
            index += 1
            candidate = f"{base}-{index}"
        seen[base] = index + 1
        anchors[candidate] = number

    return anchors


def iter_link_targets(text: str) -> Iterator[tuple[int, str]]:
    """Liefert ``(Zeilennummer, rohes Ziel)`` für Links und Bilder außerhalb
    von Codeblöcken. Über mehrere Zeilen umbrochene Ziele zählen zur Zeile,
    in der die Beschriftung beginnt."""
    masked = mask_fenced_code(text)
    for pattern in (MARKDOWN_LINK_RE, IMAGE_LINK_RE):
        for match in pattern.finditer(masked):
            yield masked.count("\n", 0, match.start()) + 1, match.group(1)


def _display(path: Path, root: Path) -> str:
    """Pfad relativ zu ``root``; außerhalb davon nur der Dateiname."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return path.name


def broken_anchor_links(paths: Iterable[Path], *, root: Path = ROOT) -> list[str]:
    """Nicht auflösbare dokumentinterne Anker der übergebenen Dateien.

    Geprüft werden ``#abschnitt`` gegen die Überschriften derselben Datei und
    ``pfad.md#abschnitt`` gegen die der Zieldatei; Ziele ohne Fragment, mit
    Schema oder auf Nicht-Markdown bleiben außen vor. Jeder Eintrag nennt
    Datei, Zeile und den Anker.
    """
    anchors_by_file: dict[Path, dict[str, int]] = {}

    def anchors_of(path: Path) -> dict[str, int]:
        if path not in anchors_by_file:
            anchors_by_file[path] = heading_anchors(path.read_text(encoding="utf-8"))
        return anchors_by_file[path]

    broken: list[str] = []
    for path in paths:
        for line, raw_target in iter_link_targets(path.read_text(encoding="utf-8")):
            parts = split_target(raw_target)
            if parts is None:
                continue
            path_part, fragment = parts
            if not fragment:
                continue

            target_path = path if not path_part else (path.parent / path_part).resolve()
            if target_path.suffix.lower() != ".md" or not target_path.is_file():
                continue

            if fragment not in anchors_of(target_path):
                where = "" if target_path == path else f" in {_display(target_path, root)}"
                broken.append(
                    f"{_display(path, root)}:{line} anchor does not resolve{where}: #{fragment}"
                )

    return broken
