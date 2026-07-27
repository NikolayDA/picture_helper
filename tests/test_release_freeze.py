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


def _git(*args: str) -> int:
    """Exit-Code eines git-Aufrufs im Repository (Ausgabe verworfen)."""
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, check=False
    ).returncode


def _git_available() -> bool:
    try:
        return _git("rev-parse", "--git-dir") == 0
    except OSError:
        return False


def _repo_is_shallow() -> bool:
    """Ob der Klon abgeschnitten ist (``actions/checkout`` nutzt ``fetch-depth: 1``)."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--is-shallow-repository"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() == "true"


# ── Kandidatenableitung gegen ein echtes Mini-Repository ──────────────
#
# Codex-Review auf PR #701: Ein unsquashed Merge kann kandidatenrelevante
# Seitenzweig-Commits enthalten, deren Änderung nie in der Release-Linie ankommt
# (Konfliktauflösung, `-s ours`, späterer Revert). Würde die Ableitung alle
# Commits aufzählen, liefen Versions-, Release-Body- und Pin-Prüfung gegen einen
# Baum, der nie getaggt wird. Die Ableitung folgt deshalb der Mainline.


def _run(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _write(repo: Path, relative: str, text: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _commit(repo: Path, relative: str, text: str, message: str) -> str:
    _write(repo, relative, text)
    _run(repo, "add", "-A")
    _run(repo, "commit", "-m", message)
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


@pytest.fixture
def tiny_repo(tmp_path: Path) -> Path:
    """Winziges Repository mit Basis-Commit (nur für die git-Logik des Skripts)."""
    if not _git_available():
        pytest.skip("kein git verfügbar")
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "init", "-q", "-b", "main")
    _run(repo, "config", "user.email", "test@example.invalid")
    _run(repo, "config", "user.name", "Test")
    _commit(repo, "README.md", "start\n", "base")
    return repo


def test_derive_candidate_ignores_discarded_side_branch_commits(tiny_repo: Path) -> None:
    """Ein Seitenzweig-Commit, dessen Baum nie ankommt, wird nicht Kandidat."""
    base = subprocess.run(
        ["git", "-C", str(tiny_repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    _run(tiny_repo, "checkout", "-q", "-b", "seite")
    side = _commit(tiny_repo, "bgremover/leck.py", "x = 1\n", "kandidatenrelevant")

    _run(tiny_repo, "checkout", "-q", "main")
    _commit(tiny_repo, "docs/history/notiz.md", "protokoll\n", "protokoll")
    # '-s ours' übernimmt die Seitenzweig-Historie, aber nicht deren Baum.
    _run(tiny_repo, "merge", "-q", "-s", "ours", "--no-edit", "seite")

    assert side in vrf.commits_between(tiny_repo, base, "HEAD")
    assert side not in vrf.commits_between(tiny_repo, base, "HEAD", first_parent=True)
    assert vrf.derive_candidate(tiny_repo, base, "HEAD") is None


def test_derive_candidate_picks_merge_that_really_incorporates_changes(tiny_repo: Path) -> None:
    base = subprocess.run(
        ["git", "-C", str(tiny_repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    _run(tiny_repo, "checkout", "-q", "-b", "seite")
    _commit(tiny_repo, "bgremover/fix.py", "y = 2\n", "kandidatenrelevant")
    _run(tiny_repo, "checkout", "-q", "main")
    _run(tiny_repo, "merge", "-q", "--no-ff", "--no-edit", "seite")

    merge = subprocess.run(
        ["git", "-C", str(tiny_repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert vrf.derive_candidate(tiny_repo, base, "HEAD") == merge
    assert vrf.candidate_relevant_paths(vrf.changed_paths(tiny_repo, merge)) == ("bgremover/fix.py",)


def test_release_note_extractor_comes_from_the_checked_revision(tiny_repo: Path) -> None:
    """Der Body wird mit dem Extraktor *des Kandidaten* erzeugt, nicht dem lokalen."""
    _commit(
        tiny_repo,
        "scripts/extract_release_notes.py",
        # ``__file__`` wie im echten Skript (CHANGELOG-Default) – der Loader muss
        # es bereitstellen, sonst scheitert schon der Import.
        "from pathlib import Path\n"
        "_DEFAULT = Path(__file__).resolve().parent.parent / 'CHANGELOG.md'\n"
        "def extract_release_notes(changelog: str, version: str) -> str:\n"
        "    return 'aus dem Commit'\n",
        "extractor",
    )
    _write(
        tiny_repo,
        "scripts/extract_release_notes.py",
        "def extract_release_notes(changelog: str, version: str) -> str:\n"
        "    return 'aus dem Arbeitsbaum'\n",
    )
    extract = vrf.load_extract_release_notes(tiny_repo, "HEAD")
    assert extract("egal", "1.0.0") == "aus dem Commit"


def _doc(pin: str) -> object:
    return vrf.FreezeDoc(
        version="1.0.0",
        base_tag="v0.9.0",
        declared_count=1,
        pinned_candidate=pin,
        classified=(),
        has_self_row=True,
    )


def test_require_pin_rejects_a_merely_equivalent_candidate(tiny_repo: Path) -> None:
    """Gate für #685/#686: nur der exakte, aktuelle SHA zählt.

    Ein freeze-äquivalenter Nachfolger (reiner Protokoll-Commit darüber) ist im
    Alltag nur eine Warnung – als Release-Gate aber ein Fehler, sonst baut oder
    taggt der Release einen anderen Commit als den dokumentierten.
    """
    pinned = _commit(tiny_repo, "bgremover/a.py", "a = 1\n", "kandidat")
    successor = _commit(tiny_repo, "docs/history/x.md", "nur protokoll\n", "protokoll")

    warn = vrf._check_pin(tiny_repo, "HEAD", successor, _doc(pinned), False)
    assert (warn.severity, warn.code) == ("warning", "candidate-sha-equivalent")

    hard = vrf._check_pin(tiny_repo, "HEAD", successor, _doc(pinned), True)
    assert (hard.severity, hard.code) == ("error", "candidate-sha-equivalent")


def test_pin_mismatch_with_real_drift_is_always_an_error(tiny_repo: Path) -> None:
    pinned = _commit(tiny_repo, "bgremover/a.py", "a = 1\n", "kandidat")
    drifted = _commit(tiny_repo, "bgremover/b.py", "b = 2\n", "andere Änderung")

    finding = vrf._check_pin(tiny_repo, "HEAD", drifted, _doc(pinned), False)
    assert (finding.severity, finding.code) == ("error", "candidate-sha-mismatch")
    assert "bgremover/b.py" in finding.message


def test_classified_shas_exist_in_history() -> None:
    """Jeder bekannte, in der Tabelle genannte SHA ist ein echter Vorfahr von HEAD.

    Unabhängig von der Merge-Strategie stabil: die klassifizierten Commits liegen
    bereits auf ``main``. In einem flachen Klon (CI checkout mit ``fetch-depth: 1``)
    sind ältere Commits schlicht nicht vorhanden – dort wird der jeweilige SHA
    übersprungen statt als „kein Vorfahr" gemeldet. Ohne git (Quell-Tarball)
    entfällt der Test ganz.
    """
    if not _git_available():
        pytest.skip("kein git-Repository verfügbar")
    shallow = _repo_is_shallow()
    doc = vrf.parse_freeze_doc(_freeze_doc_text())
    checked = 0
    for sha in doc.classified:
        if _git("cat-file", "-e", f"{sha}^{{commit}}") != 0:
            assert shallow, (
                f"{sha} existiert nicht im vollständigen Klon – die Freeze-Tabelle "
                f"nennt einen Commit, den es nicht gibt."
            )
            continue  # außerhalb der Klontiefe: nicht prüfbar, kein Befund
        assert _git("merge-base", "--is-ancestor", sha, "HEAD") == 0, (
            f"{sha} ist kein Vorfahr von HEAD – die Freeze-Tabelle nennt einen "
            f"Commit, der nicht (mehr) im Kandidatenpfad liegt."
        )
        checked += 1
    if not checked:
        pytest.skip("flacher Klon ohne die klassifizierten Commits – nicht prüfbar")
