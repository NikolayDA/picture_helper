"""Structural checks for translated Markdown documentation."""

import re
from pathlib import Path

from bgremover.i18n import _TRANSLATIONS
from tests._markdown_utils import (
    FENCE_RE,
    HEADING_LINE_RE,
    IMAGE_LINK_RE,
    MARKDOWN_LINK_RE,
    local_target,
    without_fenced_code,
)

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
    "ANLEITUNG.md",
)

README_3D_FEATURE_MARKERS = {
    "de": "**🧊 3D-Reliefvorschau**",
    "en": "**🧊 3D relief preview**",
    "es": "**🧊 Vista previa de relieve 3D**",
    "fr": "**🧊 Aperçu du relief 3D**",
    "uk": "**🧊 3D-перегляд рельєфу**",
    "zh": "**🧊 3D 浮雕预览**",
}
README_3D_SCREENSHOT = "77_function_preview3d_adjusted.png"

# Die 3D-Reliefvorschau muss auch in der Funktionsübersicht des Handbuchs
# stehen (#968). Der Struktur-Paritätstest zählt nur Überschriften,
# Codeblöcke und Tabellen – ein in einer Übersetzung vergessener Listenpunkt
# bliebe ohne diesen Marker still.
ANLEITUNG_3D_FEATURE_MARKERS = {
    "de": "**3D-Reliefvorschau**",
    "en": "**3D relief preview**",
    "es": "**Vista previa de relieve 3D**",
    "fr": "**Aperçu du relief 3D**",
    "uk": "**3D-перегляд рельєфу**",
    "zh": "**3D 浮雕预览**",
}

# Beschriftungen, die das Handbuch wörtlich aus der UI übernimmt (#966/#969).
# Quelle ist die jeweilige Sprachtabelle in bgremover/i18n.py, nicht eine
# freie Übersetzung – wird eine Beschriftung dort umbenannt, zieht das
# Handbuch nach.
QUOTED_UI_LABEL_KEYS = ("right_panel.shape.resize_apply", "menu.view.show_3d")

_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
_H2_SECTION_RE = re.compile(r"(?ms)^## [^\n]+\n.*?(?=^## |\Z)")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _h2_sections_containing(text: str, *markers: str) -> list[str]:
    """Liefert H2-Abschnitte, die alle stabilen Inhaltsanker enthalten."""
    return [
        match.group(0)
        for match in _H2_SECTION_RE.finditer(text)
        if all(marker in match.group(0) for marker in markers)
    ]



def _heading_levels(text: str) -> list[int]:
    return [len(match.group(1)) for match in HEADING_LINE_RE.finditer(without_fenced_code(text))]


def _count_code_blocks(text: str) -> int:
    count = 0
    in_block = False
    fence_char = ""

    for line in text.splitlines():
        match = FENCE_RE.match(line)
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
    lines = without_fenced_code(text).splitlines()
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



def _translated_doc_paths() -> list[Path]:
    return [I18N_ROOT / language / name for language in LANGUAGES for name in DOC_NAMES]


def _all_language_paths(name: str) -> list[Path]:
    """Return the canonical German file followed by all translations."""
    return [ROOT / name, *(I18N_ROOT / language / name for language in LANGUAGES)]


def test_i18n_expected_docs_exist() -> None:
    for name in DOC_NAMES:
        assert (ROOT / name).is_file(), f"missing canonical documentation source: {name}"

    for path in _translated_doc_paths():
        assert path.is_file(), f"missing translated documentation file: {path.relative_to(ROOT)}"


def test_i18n_local_markdown_links_resolve() -> None:
    for path in _translated_doc_paths():
        text = without_fenced_code(_read(path))
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = local_target(match.group(1))
            if target is None:
                continue

            resolved = (path.parent / target).resolve()
            assert resolved.exists(), f"{path.relative_to(ROOT)} links to missing file: {target}"


def test_i18n_markdown_image_links_resolve() -> None:
    for path in _translated_doc_paths():
        text = without_fenced_code(_read(path))
        for match in IMAGE_LINK_RE.finditer(text):
            target = local_target(match.group(1))
            if target is None:
                continue

            resolved = (path.parent / target).resolve()
            assert resolved.is_file(), f"{path.relative_to(ROOT)} links to missing image: {target}"


def test_readmes_document_3d_feature_usage_and_screenshot() -> None:
    paths = {"de": ROOT / "README.md"} | {
        language: I18N_ROOT / language / "README.md" for language in LANGUAGES
    }

    for language, path in paths.items():
        text = without_fenced_code(_read(path))
        assert README_3D_FEATURE_MARKERS[language] in text, (
            f"{path.relative_to(ROOT)} does not list the 3D preview as a feature"
        )
        assert re.search(r"^5\..*\b3D\b", text, re.MULTILINE), (
            f"{path.relative_to(ROOT)} does not explain the 3D entry point in step 5"
        )

        screenshot_links = [
            match.group(1)
            for match in IMAGE_LINK_RE.finditer(text)
            if README_3D_SCREENSHOT in match.group(1)
        ]
        assert len(screenshot_links) == 1, (
            f"{path.relative_to(ROOT)} must embed exactly one accepted 3D screenshot"
        )
        target = local_target(screenshot_links[0])
        assert target is not None
        assert (path.parent / target).resolve().is_file(), (
            f"{path.relative_to(ROOT)} links to a missing 3D screenshot: {target}"
        )


def test_linux_install_docs_cover_appimage_fuse_prerequisite() -> None:
    packaging_guide = _read(ROOT / "packaging" / "linux" / "README.md")
    deb_builder = _read(ROOT / "packaging" / "linux" / "build_deb.sh")
    assert "--appimage-extract-and-run" in packaging_guide
    assert re.search(r"libfuse2\s*\|\s*libfuse2t64", deb_builder)

    required_markers = (
        "libfuse.so.2",
        "`libfuse2`",
        "`libfuse2t64`",
        "`fuse-libs`",
        "`fuse2`",
        "--appimage-extract-and-run",
    )
    for path in _all_language_paths("INSTALL_LINUX.md"):
        text = _read(path)
        quick_start_sections = _h2_sections_containing(
            text,
            "chmod +x BgRemover-*-linux-x86_64-ai.AppImage",
            "sudo apt install ./BgRemover-*-linux-x86_64-ai.deb",
        )
        assert len(quick_start_sections) == 1, (
            f"{path.relative_to(ROOT)} must have exactly one release-artifact "
            "quick-start section"
        )
        quick_start = quick_start_sections[0]
        missing_quick_start = [marker for marker in required_markers if marker not in quick_start]
        assert not missing_quick_start, (
            f"{path.relative_to(ROOT)} quick start misses Linux prerequisites: "
            f"{missing_quick_start}"
        )

        troubleshooting_sections = _h2_sections_containing(text, "dlopen", "libfuse.so.2")
        assert len(troubleshooting_sections) == 1, (
            f"{path.relative_to(ROOT)} must have exactly one troubleshooting "
            "section for the libfuse.so.2 dlopen error"
        )
        troubleshooting = troubleshooting_sections[0]
        missing_troubleshooting = [
            marker for marker in required_markers if marker not in troubleshooting
        ]
        assert not missing_troubleshooting, (
            f"{path.relative_to(ROOT)} troubleshooting misses Linux prerequisites: "
            f"{missing_troubleshooting}"
        )


def test_mac_install_docs_cover_prebuilt_dmg_scope() -> None:
    packaging_guide = _read(ROOT / "packaging" / "mac" / "README.md")
    assert "macOS 11" in packaging_guide
    assert "arm64-only" in packaging_guide

    required_markers = ("macOS 11", "Big Sur", "arm64", "Intel", ".dmg")
    for path in _all_language_paths("INSTALL_MAC.md"):
        text = _read(path)
        matching_paragraphs = [
            paragraph
            for paragraph in text.split("\n\n")
            if all(marker in paragraph for marker in required_markers)
        ]
        assert matching_paragraphs, (
            f"{path.relative_to(ROOT)} must keep the macOS version, architecture, "
            "and Intel boundary together in the prebuilt-DMG paragraph"
        )


def test_mac_install_docs_cover_rosetta_mismatch_recovery() -> None:
    """Alle sechs Anleitungen halten Diagnose, Abhilfe und Zielzustand aus
    #866 zusammen; sonst würde eine Übersetzung den kritischen Neuaufbaupfad
    oder die überprüfbare Log-Evidenz verlieren."""
    required_markers = (
        "x86_64",
        "arm64",
        "Rosetta",
        "sysctl.proc_translated",
        "platform.machine()",
        "`file`",
        "brew install python",
        'rm -rf "$HOME/Library/Application Support/BgRemover/venv"',
        "bash create_BgRemover_app.sh",
        "interpreter_arch=arm64",
        "proc_translated=0",
    )
    for path in _all_language_paths("INSTALL_MAC.md"):
        text = _read(path)
        matching_sections = _h2_sections_containing(text, *required_markers)
        assert len(matching_sections) == 1, (
            f"{path.relative_to(ROOT)} must document Rosetta detection, native "
            "venv rebuild, and runtime log evidence together"
        )


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


def _anleitung_paths() -> dict[str, Path]:
    return {"de": ROOT / "ANLEITUNG.md"} | {
        language: I18N_ROOT / language / "ANLEITUNG.md" for language in LANGUAGES
    }


def test_anleitung_lists_the_3d_relief_preview_as_a_feature() -> None:
    """Abschnitt 1 muss die 3D-Reliefvorschau als eigenen Punkt führen (#968)."""

    for language, path in _anleitung_paths().items():
        text = without_fenced_code(_read(path))
        assert ANLEITUNG_3D_FEATURE_MARKERS[language] in text, (
            f"{path.relative_to(ROOT)} lists no 3D relief preview feature"
        )


def test_anleitung_quotes_ui_labels_verbatim() -> None:
    """Zitierte Bedienelemente tragen den echten ``tr``-Wert (#966/#969).

    Ohne diese Bindung driftet das Handbuch von der UI weg, sobald eine
    Beschriftung in ``bgremover/i18n.py`` umbenannt wird – genau der Fall,
    der zu #966 führte („Übernehmen" statt „Größe anwenden").
    """

    for language, path in _anleitung_paths().items():
        text = without_fenced_code(_read(path))
        for key in QUOTED_UI_LABEL_KEYS:
            label = _TRANSLATIONS[language][key]
            # Ein Sternchen je Seite genügt: Es trifft die kursive Schreibweise
            # der Menüeinträge und steckt zugleich in der fetten der Knöpfe.
            assert f"*{label}*" in text, (
                f"{path.relative_to(ROOT)} does not quote {key} as {label!r}"
            )
