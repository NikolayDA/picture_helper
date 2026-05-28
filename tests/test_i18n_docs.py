"""Structural checks for translated Markdown documentation."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N_ROOT = ROOT / "docs" / "i18n"
LANGUAGES = ("en", "es", "fr", "uk", "zh")
DOC_NAMES = (
    "README.md",
    "LICENSES.md",
    "INSTALL_LINUX.md",
    "CHANGELOG.md",
    "INSTALL_MAC.md",
    "RESOURCES.md",
    "RECOMMENDATIONS.md",
)

_HEADING_RE = re.compile(r"^(#{1,6})\s+\S", re.MULTILINE)
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_IMAGE_LINK_RE = re.compile(r"!\[[^\]]*]\(([^)]+)\)")
_MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+]\(([^)]+)\)")
_TABLE_SEPARATOR_RE = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)


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
    return [len(match.group(1)) for match in _HEADING_RE.finditer(_without_fenced_code(text))]


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


def _count_tables(text: str) -> int:
    lines = _without_fenced_code(text).splitlines()
    count = 0
    index = 0

    while index < len(lines) - 1:
        if "|" in lines[index] and _TABLE_SEPARATOR_RE.match(lines[index + 1]):
            count += 1
            index += 2
            while index < len(lines) and "|" in lines[index]:
                index += 1
        else:
            index += 1

    return count


def _local_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if not target:
        return None
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split()[0]

    if _SCHEME_RE.match(target) or target.startswith("#"):
        return None

    path_part = target.split("#", 1)[0]
    return path_part or None


def _translated_doc_paths() -> list[Path]:
    return [I18N_ROOT / language / name for language in LANGUAGES for name in DOC_NAMES]


def test_i18n_expected_docs_exist() -> None:
    for name in DOC_NAMES:
        assert (ROOT / name).is_file(), f"missing canonical documentation source: {name}"

    for path in _translated_doc_paths():
        assert path.is_file(), f"missing translated documentation file: {path.relative_to(ROOT)}"


def test_i18n_local_markdown_links_resolve() -> None:
    for path in _translated_doc_paths():
        text = _without_fenced_code(_read(path))
        for match in _MARKDOWN_LINK_RE.finditer(text):
            target = _local_target(match.group(1))
            if target is None:
                continue

            resolved = (path.parent / target).resolve()
            assert resolved.exists(), f"{path.relative_to(ROOT)} links to missing file: {target}"


def test_i18n_markdown_image_links_resolve() -> None:
    for path in _translated_doc_paths():
        text = _without_fenced_code(_read(path))
        for match in _IMAGE_LINK_RE.finditer(text):
            target = _local_target(match.group(1))
            if target is None:
                continue

            resolved = (path.parent / target).resolve()
            assert resolved.is_file(), f"{path.relative_to(ROOT)} links to missing image: {target}"


def test_i18n_docs_match_canonical_structure() -> None:
    for name in DOC_NAMES:
        canonical_text = _read(ROOT / name)
        expected = (
            _heading_levels(canonical_text),
            _count_code_blocks(canonical_text),
            _count_tables(canonical_text),
        )

        for language in LANGUAGES:
            path = I18N_ROOT / language / name
            translated_text = _read(path)
            actual = (
                _heading_levels(translated_text),
                _count_code_blocks(translated_text),
                _count_tables(translated_text),
            )
            assert actual == expected, (
                f"{path.relative_to(ROOT)} structure differs from canonical {name}: "
                f"headings/code blocks/tables = {actual}, expected {expected}"
            )
