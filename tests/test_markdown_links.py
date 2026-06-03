"""Repository-wide Markdown link hygiene checks."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
IMAGE_LINK_RE = re.compile(r"!\[[^\]]*]\(([^)]+)\)")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+]\(([^)]+)\)")
SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)
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


def _without_fenced_code(text: str) -> str:
    lines: list[str] = []
    in_block = False
    fence_char = ""

    for line in text.splitlines():
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
            lines.append(line)

    return "\n".join(lines)


def _local_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if not target:
        return None
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split()[0]

    if SCHEME_RE.match(target) or target.startswith("#"):
        return None

    path_part = target.split("#", 1)[0]
    return unquote(path_part) or None


def test_all_markdown_local_links_and_images_resolve() -> None:
    """Every local Markdown link/image target in the repository must exist."""

    missing: list[str] = []
    for path in sorted(ROOT.rglob("*.md")):
        relative_parts = path.relative_to(ROOT).parts
        if any(part in IGNORED_MARKDOWN_DIRS for part in relative_parts[:-1]):
            continue

        text = _without_fenced_code(path.read_text(encoding="utf-8"))
        for kind, pattern in (("link", MARKDOWN_LINK_RE), ("image", IMAGE_LINK_RE)):
            for match in pattern.finditer(text):
                target = _local_target(match.group(1))
                if target is None:
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    missing.append(
                        f"{path.relative_to(ROOT)} {kind} target does not exist: {target}"
                    )

    assert not missing, "Broken local Markdown targets:\n" + "\n".join(missing)
