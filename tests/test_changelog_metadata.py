"""Guards for changelog translations and release metadata consistency."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = ("en", "es", "fr", "uk", "zh")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _unreleased_section(text: str) -> str:
    match = re.search(r"^## \[Unreleased\].*?(?=^## \[\d)", text, re.M | re.S)
    assert match is not None, "CHANGELOG.md needs an [Unreleased] section"
    return match.group(0)


def _top_level_bullet_count(section: str) -> int:
    return len(re.findall(r"(?m)^- ", section))


def _project_version() -> str:
    text = _read(ROOT / "pyproject.toml")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    assert match is not None, "pyproject.toml needs [project].version"
    return match.group(1)


def _changelog_release_date(version: str) -> str:
    text = _read(ROOT / "CHANGELOG.md")
    match = re.search(rf"^## \[{re.escape(version)}\] – (\d{{4}}-\d{{2}}-\d{{2}})$", text, re.M)
    assert match is not None, f"CHANGELOG.md needs a release heading for {version}"
    return match.group(1)


def test_translated_changelogs_keep_unreleased_entries_in_sync() -> None:
    """Translated changelogs mirror the German [Unreleased] bullet count."""

    german_count = _top_level_bullet_count(_unreleased_section(_read(ROOT / "CHANGELOG.md")))

    for language in LANGUAGES:
        path = ROOT / "docs" / "i18n" / language / "CHANGELOG.md"
        translated_count = _top_level_bullet_count(_unreleased_section(_read(path)))
        assert translated_count == german_count, (
            f"{path.relative_to(ROOT)} has {translated_count} top-level [Unreleased] "
            f"entries, expected {german_count}"
        )


def test_appstream_release_date_matches_changelog_version_date() -> None:
    """The AppStream release metadata mirrors pyproject version and changelog date."""

    version = _project_version()
    expected_date = _changelog_release_date(version)
    root = ET.parse(ROOT / "packaging" / "linux" / "de.bgremover.app.metainfo.xml").getroot()
    release = root.find("releases/release")
    assert release is not None
    assert release.get("version") == version
    assert release.get("date") == expected_date
