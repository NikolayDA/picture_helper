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


_HEADING_LINE_RE = re.compile(r"(?m)^## \[(\d+\.\d+\.\d+)\](.*)$")
_HEADING_DATE_RE = re.compile(r" – \d{4}-\d{2}-\d{2}$")


def _version_headings(text: str, path: Path) -> list[str]:
    """Version headings, in file order. A malformed date/dash raises instead of
    silently dropping the heading out of every check below (fail-closed)."""

    versions = []
    for match in _HEADING_LINE_RE.finditer(text):
        version, rest = match.group(1), match.group(2)
        assert _HEADING_DATE_RE.fullmatch(rest), (
            f"{path.relative_to(ROOT)}: heading '## [{version}]{rest}' does not "
            f"match '## [X.Y.Z] – YYYY-MM-DD' (wrong dash or date format?)"
        )
        versions.append(version)
    return versions


def _footer_link_entries(text: str) -> list[tuple[str, str]]:
    return re.findall(r"(?m)^\[(\d+\.\d+\.\d+)\]: (\S+)$", text)


_COMPARE_TARGET_RE = re.compile(r"\.\.\.v(\d+\.\d+\.\d+)$")
_COMPARE_BASE_RE = re.compile(r"compare/v(\d+\.\d+\.\d+)\.\.\.")

# Pre-tag history: these footer links point at raw commit SHAs (or, for
# 2.0.0, a /tree/ link) instead of the 'vX.Y.Z' compare convention used by
# every later release, so they don't end in '...vX.Y.Z'.
_LEGACY_SHA_LINKED_VERSIONS = frozenset({"2.0.0", "2.1.0", "2.2.0"})


def _unreleased_footer_target(text: str) -> str:
    match = re.search(r"(?m)^\[Unreleased\]: (\S+)$", text)
    assert match is not None, "CHANGELOG.md needs an [Unreleased] footer link"
    return match.group(1)


ALL_CHANGELOGS = (ROOT / "CHANGELOG.md",) + tuple(
    ROOT / "docs" / "i18n" / language / "CHANGELOG.md" for language in LANGUAGES
)


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


def test_changelog_version_headings_have_matching_footer_links() -> None:
    """Every '## [X.Y.Z]' heading needs a matching '[X.Y.Z]: https://...' footer
    link, and [Unreleased] must compare against the latest released version.

    Regression test for #773/#827: the same mechanical footer-link bug (missing
    entry for the newest heading, stale [Unreleased] compare target) slipped
    through untested at two consecutive release cuts because nothing checked
    the footer against the headings. Also catches the adjacent mechanical
    slips of the same class: a duplicate footer definition, a footer entry
    without a matching heading (typo'd version, or leftover after a retracted
    release), and a copy-paste compare link whose base or target doesn't match
    its neighbouring headings.
    """

    for path in ALL_CHANGELOGS:
        text = _read(path)
        headings = _version_headings(text, path)
        assert headings, f"{path.relative_to(ROOT)} has no version headings"
        heading_index = {version: i for i, version in enumerate(headings)}

        entries = _footer_link_entries(text)
        footer_versions = [version for version, _link in entries]
        duplicates = sorted({v for v in footer_versions if footer_versions.count(v) > 1})
        assert not duplicates, (
            f"{path.relative_to(ROOT)}: duplicate footer link definition(s) for {duplicates}"
        )

        missing = [v for v in headings if v not in footer_versions]
        assert not missing, (
            f"{path.relative_to(ROOT)}: version heading(s) {missing} have no "
            f"matching '[X.Y.Z]: https://...' footer link definition"
        )

        extra = sorted(set(v for v in footer_versions if v not in heading_index))
        assert not extra, (
            f"{path.relative_to(ROOT)}: footer link(s) {extra} have no matching "
            f"'## [X.Y.Z]' heading"
        )

        for version, link in entries:
            target_match = _COMPARE_TARGET_RE.search(link)
            if target_match is not None:
                assert target_match.group(1) == version, (
                    f"{path.relative_to(ROOT)}: footer link [{version}] targets "
                    f"...v{target_match.group(1)}, expected ...v{version}"
                )
            else:
                assert version in _LEGACY_SHA_LINKED_VERSIONS, (
                    f"{path.relative_to(ROOT)}: footer link [{version}] doesn't end "
                    f"in '...vX.Y.Z' and isn't one of the known historical "
                    f"SHA-/tree-based links {sorted(_LEGACY_SHA_LINKED_VERSIONS)}"
                )

            idx = heading_index[version]
            if idx + 1 < len(headings):
                expected_base = headings[idx + 1]
                base_match = _COMPARE_BASE_RE.search(link)
                if base_match is not None:
                    assert base_match.group(1) == expected_base, (
                        f"{path.relative_to(ROOT)}: footer link [{version}] has base "
                        f"v{base_match.group(1)}, expected v{expected_base} (the next "
                        f"older release heading)"
                    )

        latest = max(headings, key=lambda v: tuple(int(p) for p in v.split(".")))
        assert headings[0] == latest, (
            f"{path.relative_to(ROOT)}: version headings are not in descending "
            f"order (top heading {headings[0]}, newest release {latest})"
        )

        unreleased_target = _unreleased_footer_target(text)
        expected_suffix = f"compare/v{latest}...HEAD"
        assert unreleased_target.endswith(expected_suffix), (
            f"{path.relative_to(ROOT)}: [Unreleased] points at {unreleased_target!r}, "
            f"expected it to end with {expected_suffix!r} (latest release is {latest})"
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
