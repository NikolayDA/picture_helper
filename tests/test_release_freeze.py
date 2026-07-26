"""Governance des Release-Freeze-Verfahrens (#699).

Der 2.7.1-Freeze nannte zunächst einen handkopierten Kurz-SHA als verbindliche
Basis; an genau diesem Commit stand ``pyproject.toml`` aber noch auf ``2.7.0``
(ein Dokument kann seinen eigenen Commit-SHA nicht enthalten). Diese Tests
sichern die beiden Korrekturen ab, die das strukturell verhindern:

1. Das Freeze-Dokument bleibt maschinenlesbar und in sich konsistent
   (Kandidatenversion == ``pyproject.toml``, volle 40-stellige SHAs, Fensterzahl
   == Tabellenzeilen).
2. Der **tatsächlich veröffentlichte** Release-Body – die Ausgabe von
   ``scripts/extract_release_notes.py`` – nennt Auswirkung, betroffene
   Anwender:innen, Upgrade-Relevanz und bekannte Einschränkungen in allen sechs
   Sprachen (#683). Ein Entwurf, der nur im Freeze-Dokument steht, erreicht die
   Releases-Seite nie.

Die git-abhängige Vollprüfung (Klassifizierung aller Commits im Fenster,
abgeleiteter Kandidat, protokollierter SHA) läuft absichtlich nicht in der
Default-Suite, sondern als Release-Werkzeug: ``make release-freeze-check``. Sie
bewertet den Zustand *eines Commits* und muss beim Einbringen nach ``main``
bewusst einen Nachtrag verlangen – das wäre als Dauertest ein Fehlsignal.
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "verify_release_freeze", ROOT / "scripts" / "verify_release_freeze.py"
)
assert _SPEC is not None and _SPEC.loader is not None
vrf = importlib.util.module_from_spec(_SPEC)
sys.modules["verify_release_freeze"] = vrf
_SPEC.loader.exec_module(vrf)

_EXTRACT_SPEC = importlib.util.spec_from_file_location(
    "extract_release_notes", ROOT / "scripts" / "extract_release_notes.py"
)
assert _EXTRACT_SPEC is not None and _EXTRACT_SPEC.loader is not None
extract = importlib.util.module_from_spec(_EXTRACT_SPEC)
_EXTRACT_SPEC.loader.exec_module(extract)

LANGUAGES = ("de", "en", "es", "fr", "uk", "zh")
#: Zeilen der Klassifizierungstabelle – voller SHA oder die Selbstzeile.
_COMMIT_ROW_RE = re.compile(r"(?m)^\| `(?:[0-9a-f]{40}|Kandidaten-Commit)`")


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', text)
    assert match is not None
    return match.group(1)


def _freeze_doc_path() -> Path:
    return ROOT / vrf.FREEZE_DOC_TEMPLATE.format(version=_pyproject_version())


def _freeze_doc_text() -> str:
    path = _freeze_doc_path()
    assert path.is_file(), (
        f"Freeze-Dokument {path.relative_to(ROOT)} fehlt – jede Version braucht "
        f"ihren dokumentierten Scope-Freeze (#683/#699)."
    )
    return path.read_text(encoding="utf-8")


def _changelog(language: str) -> str:
    path = ROOT / "CHANGELOG.md" if language == "de" else (
        ROOT / "docs" / "i18n" / language / "CHANGELOG.md"
    )
    return path.read_text(encoding="utf-8")


# ── Freeze-Dokument: maschinenlesbar und in sich konsistent ────────────


def test_freeze_doc_declares_machine_readable_candidate_fields() -> None:
    doc = vrf.parse_freeze_doc(_freeze_doc_text())
    assert doc.version == _pyproject_version(), (
        "Die im Freeze-Dokument genannte Kandidatenversion muss der "
        "pyproject-Version entsprechen – der Ausgangsfehler von #699 war genau "
        "diese Abweichung."
    )
    assert re.fullmatch(r"v\d+\.\d+\.\d+", doc.base_tag)


def test_freeze_doc_window_count_matches_classification_table() -> None:
    """Die genannte Commit-Anzahl deckt sich mit den Tabellenzeilen.

    Damit fällt ein nachgetragener Commit ohne Zeile (oder umgekehrt) sofort auf,
    ohne dass der Test auf git angewiesen ist.
    """
    text = _freeze_doc_text()
    doc = vrf.parse_freeze_doc(text)
    rows = len(_COMMIT_ROW_RE.findall(text))
    assert rows == doc.declared_count, (
        f"{rows} Commit-Zeilen, Dokument nennt {doc.declared_count} Commits im Fenster"
    )
    assert len(doc.classified) + (1 if doc.has_self_row else 0) == doc.declared_count, (
        "Jeder Commit im Fenster braucht genau eine Zeile: entweder mit vollem "
        "SHA oder – für den Kandidaten-Commit selbst – als `Kandidaten-Commit`."
    )


def test_freeze_doc_uses_full_shas_only_as_evidence() -> None:
    """Kurz-SHAs dürfen erläuternd vorkommen, aber nie als einziger Nachweis."""
    doc = vrf.parse_freeze_doc(_freeze_doc_text())
    assert doc.classified, "keine klassifizierten Commits gefunden"
    for sha in doc.classified:
        assert re.fullmatch(r"[0-9a-f]{40}", sha), sha
    assert doc.has_self_row, (
        "Der Kandidaten-Commit selbst braucht eine `Kandidaten-Commit`-Zeile – "
        "er kann seinen eigenen SHA nicht enthalten (#699)."
    )


def test_freeze_doc_pin_is_either_full_sha_or_explicit_placeholder() -> None:
    doc = vrf.parse_freeze_doc(_freeze_doc_text())
    if doc.pinned_candidate is not None:
        assert re.fullmatch(r"[0-9a-f]{40}", doc.pinned_candidate)


# ── Veröffentlichter Release-Body (#683) ───────────────────────────────


def test_published_release_body_names_user_facing_aspects() -> None:
    """Der aus dem CHANGELOG erzeugte Body nennt die vier Pflichtangaben.

    Geprüft wird die Ausgabe von ``extract_release_notes.py`` – exakt der Text,
    den ``release-linux.yml`` per ``--notes-file`` veröffentlicht.
    """
    version = _pyproject_version()
    for language in LANGUAGES:
        notes = extract.extract_release_notes(_changelog(language), version)
        missing = vrf.missing_release_body_markers(notes, language)
        assert not missing, (
            f"Release-Body ({language}) ohne {', '.join(missing)} – der Entwurf im "
            f"Freeze-Dokument erreicht die Releases-Seite nicht (#699)."
        )


def test_release_body_markers_cover_all_four_aspects_per_language() -> None:
    assert set(vrf.RELEASE_BODY_MARKERS) == set(LANGUAGES)
    for language, markers in vrf.RELEASE_BODY_MARKERS.items():
        assert len(markers) == 4, language
        assert len(set(markers)) == 4, language


def test_missing_release_body_markers_reports_gaps() -> None:
    assert vrf.missing_release_body_markers("- **Impact:** x", "en") == (
        "**Affected users:**",
        "**Upgrade relevance:**",
        "**Known limitations:**",
    )
    assert vrf.missing_release_body_markers("\n".join(vrf.RELEASE_BODY_MARKERS["de"]), "de") == ()


# ── Pfadklassifizierung (fail-closed) ─────────────────────────────────


@pytest.mark.parametrize(
    "path",
    [
        "docs/history/RELEASE-2.7.1-scope-freeze.md",
        "docs/history/ADR-2026-3d-reliefvorschau-renderer.md",
        "RECOMMENDATIONS.md",
        "docs/i18n/zh/RECOMMENDATIONS.md",
        "CLAUDE.md",
    ],
)
def test_protocol_paths_do_not_move_the_candidate(path: str) -> None:
    assert not vrf.is_candidate_relevant(path)


@pytest.mark.parametrize(
    "path",
    [
        "pyproject.toml",
        "CHANGELOG.md",
        "docs/i18n/fr/CHANGELOG.md",
        "LICENSES.md",
        "bgremover/viewer_3d.py",
        "tests/test_viewer_3d.py",
        "scripts/verify_release_freeze.py",
        "packaging/linux/de.bgremover.app.metainfo.xml",
        ".github/workflows/release-linux.yml",
        "requirements/constraints.txt",
        "Makefile",
        "docs/PACKAGING_SMOKE.md",
        "irgendein/neuer/pfad.txt",  # fail-closed: Unbekanntes ist relevant
    ],
)
def test_candidate_relevant_paths_are_fail_closed(path: str) -> None:
    assert vrf.is_candidate_relevant(path)


def test_candidate_relevant_paths_filters_and_keeps_order() -> None:
    assert vrf.candidate_relevant_paths(
        ["RECOMMENDATIONS.md", "CHANGELOG.md", "docs/history/x.md", "pyproject.toml"]
    ) == ("CHANGELOG.md", "pyproject.toml")


# ── Dokument-Parser: Fehlerfälle ──────────────────────────────────────


_MINIMAL_DOC = """# Release 9.9.9 – Scope-Freeze

- **Basis-Tag:** `v9.9.8`
- **Kandidatenversion:** `9.9.9`
- **Commits im Fenster:** 2
- **Protokollierter Kandidaten-SHA:** `{pin}`

| Commit | Zweck |
|---|---|
| `{sha}` (#1) | Doku |
| `Kandidaten-Commit` (#2) | Freeze |
"""


def test_parse_freeze_doc_reads_pin_and_rows() -> None:
    sha = "a" * 40
    doc = vrf.parse_freeze_doc(_MINIMAL_DOC.format(pin="b" * 40, sha=sha))
    assert doc.version == "9.9.9"
    assert doc.base_tag == "v9.9.8"
    assert doc.declared_count == 2
    assert doc.pinned_candidate == "b" * 40
    assert doc.classified == (sha,)
    assert doc.has_self_row


def test_parse_freeze_doc_treats_placeholder_as_unpinned() -> None:
    doc = vrf.parse_freeze_doc(_MINIMAL_DOC.format(pin="nachzutragen", sha="c" * 40))
    assert doc.pinned_candidate is None


def test_parse_freeze_doc_rejects_short_sha_pin() -> None:
    """Ein Kurz-SHA im Protokollfeld ist kein gültiger Nachweis (#699)."""
    with pytest.raises(vrf.DocFormatError):
        vrf.parse_freeze_doc(_MINIMAL_DOC.format(pin="ba7e7cd", sha="d" * 40))


def test_parse_freeze_doc_rejects_missing_mandatory_lines() -> None:
    text = _MINIMAL_DOC.format(pin="e" * 40, sha="f" * 40).replace(
        "- **Basis-Tag:** `v9.9.8`\n", ""
    )
    with pytest.raises(vrf.DocFormatError, match="Basis-Tag"):
        vrf.parse_freeze_doc(text)


# ── Klassifizierte SHAs existieren wirklich (git, sonst skip) ──────────


def _git_available() -> bool:
    try:
        subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--git-dir"],
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


def test_classified_shas_exist_in_history() -> None:
    """Jeder in der Tabelle genannte SHA ist ein echter Vorfahr von HEAD.

    Unabhängig von der Merge-Strategie stabil: die klassifizierten Commits liegen
    bereits auf ``main``. Ohne git (Quell-Tarball) wird übersprungen.
    """
    if not _git_available():
        pytest.skip("kein git-Repository verfügbar")
    doc = vrf.parse_freeze_doc(_freeze_doc_text())
    for sha in doc.classified:
        merge_base = subprocess.run(
            ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", sha, "HEAD"],
            capture_output=True,
            check=False,
        )
        assert merge_base.returncode == 0, (
            f"{sha} ist kein Vorfahr von HEAD – die Freeze-Tabelle nennt einen "
            f"Commit, der nicht (mehr) im Kandidatenpfad liegt."
        )
