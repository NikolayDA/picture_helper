"""Vorbereitungs-Skript für Runbook-Schritt 1/2 (#923).

Drei Eigenschaften tragen dieses Skript, und alle drei sind hier festgehalten:

1. **Determinismus.** Gleiche Eingaben ergeben byte-gleiche Ausgaben. Ohne das
   wäre ein erzeugter Rohstand nicht reproduzierbar überprüfbar.
2. **Fail-closed.** Ein Gerüst mit offenen ``TODO(release)``-Lücken macht den
   Vorbereitungs-PR **nicht** grün – sonst wäre die Automatisierung ein Weg,
   die redaktionelle Pflicht (``NOTES-01``) zu umgehen.
3. **Kein Überschreiben von Handarbeit.** Ein bereits redaktionell bearbeiteter
   Abschnitt wird nie ersetzt, auch nicht bei einem zweiten Lauf.
"""
from __future__ import annotations

import difflib
import json
import re
import subprocess
from pathlib import Path

import pytest

from scripts import prepare_release as pr
from scripts import release_contract as rc
from scripts import verify_release_freeze as vrf

ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = ("de", "en", "es", "fr", "uk", "zh")

#: Dateien, die das Skript liest oder schreibt – mehr braucht ein Fixture-Repo
#: nicht. Sie stammen aus dem echten Repository: Ein Fixture mit erfundener
#: Struktur würde am Tag einer echten Formatänderung stillschweigend weiterlaufen.
_FIXTURE_FILES = (
    "pyproject.toml",
    # Das Gate liest den Extraktor aus dem *gepruefen Commit* – er gehoert
    # deshalb ins Fixture, nicht nur in den Arbeitsbaum.
    "scripts/extract_release_notes.py",
    # ``verify()`` liest zusaetzlich die sechs Lizenz-Snapshots; ohne sie
    # bricht der vollstaendige Lauf ab, bevor er den Platzhalter sieht.
    "LICENSES.md",
    *(f"docs/i18n/{language}/LICENSES.md" for language in ("en", "es", "fr", "uk", "zh")),
    "packaging/linux/de.bgremover.app.metainfo.xml",
    "release/path-policy.json",
    rc.CHECKLIST_PATH,
    *(pr.changelog_path(language) for language in LANGUAGES),
)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    """Minimales Repository mit den echten Dateien und einem Basis-Tag."""
    repo = tmp_path / "repo"
    for relative in _FIXTURE_FILES:
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    _git(repo.parent, "init", "-q", "repo")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "Basis")
    current = re.search(r'(?m)^version\s*=\s*"([^"]+)"', (repo / "pyproject.toml").read_text())
    assert current is not None
    _git(repo, "tag", f"v{current.group(1)}")
    return repo


def _current_version(repo: Path = ROOT) -> str:
    """Version aus ``pyproject.toml`` – im Vorbereitungs-PR ist das die neue.

    Hart notierte ``2.9.0`` würden genau in dem PR fehlschlagen, den dieses
    Skript erzeugt: Dort steht die Zielversion schon in ``pyproject.toml`` und
    ``current-freeze`` zeigt bereits auf das neue Dokument.
    """
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', (repo / "pyproject.toml").read_text("utf-8"))
    assert match is not None
    return match.group(1)


def _current_freeze_version(repo: Path = ROOT) -> str:
    """Version, auf die ``current-freeze`` in der Pfadpolicy zeigt."""
    policy = json.loads((repo / "release" / "path-policy.json").read_text("utf-8"))
    for entry in policy["candidate_relevant"]:
        if entry["id"] == "current-freeze":
            match = re.search(r"RELEASE-(\d+\.\d+\.\d+)-scope-freeze\.md", entry["path"])
            assert match is not None
            return match.group(1)
    raise AssertionError("current-freeze fehlt in der Pfadpolicy")


def _inputs(version: str = "9.9.9") -> pr.ReleaseInputs:
    return pr.ReleaseInputs(
        version=version, release_date="2026-09-15", base_tag="v9.9.8", base_sha="a" * 40
    )


# ── Determinismus und Idempotenz ───────────────────────────────────────


def test_two_runs_produce_byte_identical_output(fixture_repo: Path) -> None:
    """Zweifacher Lauf = identisches Ergebnis (Akzeptanzkriterium).

    Der Vorgänger wird **einmal** bestimmt: Determinismus heißt gleiche
    Eingaben, und nach dem ersten Lauf zeigt ``current-freeze`` bereits auf das
    neue Dokument.
    """
    predecessor = _current_freeze_version(fixture_repo)
    first = pr.plan(fixture_repo, _inputs(), predecessor_version=predecessor)
    pr.apply(fixture_repo, first.files)
    after_first = {item.path: (fixture_repo / item.path).read_bytes() for item in first.files}

    second = pr.plan(fixture_repo, _inputs(), predecessor_version=predecessor)
    pr.apply(fixture_repo, second.files)
    after_second = {item.path: (fixture_repo / item.path).read_bytes() for item in second.files}

    assert after_second == after_first
    assert second.policy_version == first.policy_version


def test_the_rendered_issue_is_deterministic() -> None:
    checklist = rc.load_release_checklist(ROOT / rc.CHECKLIST_PATH)
    kwargs = {
        "checklist_version": str(checklist["checklist_version"]),
        "checklist_sha256": "b" * 64,
        "paused_criteria": pr.paused_x86_64_criteria(checklist),
        "policy_version": 42,
    }
    assert pr.release_issue(_inputs(), **kwargs) == pr.release_issue(_inputs(), **kwargs)


def test_a_second_run_does_not_bump_the_policy_twice(fixture_repo: Path) -> None:
    """Der Rollover ist idempotent – sonst liefe die Policy-Version hoch."""
    predecessor = _current_freeze_version(fixture_repo)
    first = pr.plan(fixture_repo, _inputs(), predecessor_version=predecessor)
    pr.apply(fixture_repo, first.files)
    second = pr.plan(fixture_repo, _inputs(), predecessor_version=predecessor)
    assert second.policy_version == first.policy_version


# ── Fail-closed: das Gerüst ist kein Release ───────────────────────────


def test_every_generated_section_carries_the_editorial_placeholder() -> None:
    for language in LANGUAGES:
        section = pr.changelog_section(language, "9.9.9", "2026-09-15")
        assert pr.PLACEHOLDER in section, language


def test_the_freeze_gate_blocks_on_an_unfilled_skeleton(fixture_repo: Path) -> None:
    """Das Kernversprechen: Ein Gerüst macht den Vorbereitungs-PR nicht grün.

    Geprüft wird die Gate-Funktion selbst, nicht eine Nachbildung – der
    Platzhalter-Wächter ist die Stelle, an der ``prepare_release`` und
    ``verify_release_freeze`` zusammenhängen.
    """
    prepared = pr.plan(fixture_repo, _inputs(), predecessor_version=_current_freeze_version(fixture_repo))
    pr.apply(fixture_repo, prepared.files)
    _git(fixture_repo, "add", "-A")
    _git(fixture_repo, "commit", "-qm", "Geruest")

    doc = vrf.parse_freeze_doc((fixture_repo / pr.freeze_doc_path("9.9.9")).read_text("utf-8"))
    findings = vrf._check_release_body(fixture_repo, "HEAD", doc) + vrf._check_freeze_doc_placeholder(
        fixture_repo, "HEAD", doc
    )
    gaps = [f for f in findings if f.code == "editorial-placeholder"]
    # Alle sechs Sprachfassungen und das Freeze-Dokument, nicht nur eine Stelle.
    assert len(gaps) == len(LANGUAGES) + 1, [f.message for f in gaps]


def test_the_full_gate_reports_the_gap_not_just_the_helper(fixture_repo: Path) -> None:
    """Der Wächter muss in ``verify()`` **verdrahtet** sein, nicht nur existieren.

    Ein Test, der nur ``_check_editorial_placeholders`` direkt aufruft, bliebe
    grün, wenn jemand den Aufruf aus ``verify()`` entfernt – der Befund fiele
    dann still aus dem Gate. Deshalb hier der vollständige Lauf.
    """
    base_tag = _git(fixture_repo, "describe", "--tags", "--abbrev=0")
    inputs = pr.ReleaseInputs(
        version="9.9.9",
        release_date="2026-09-15",
        base_tag=base_tag,
        base_sha=_git(fixture_repo, "rev-list", "-n", "1", base_tag),
    )
    prepared = pr.plan(
        fixture_repo, inputs, predecessor_version=_current_freeze_version(fixture_repo)
    )
    pr.apply(fixture_repo, prepared.files)
    _git(fixture_repo, "add", "-A")
    _git(fixture_repo, "commit", "-qm", "Geruest")

    codes = [finding.code for finding in vrf.verify(fixture_repo, "HEAD")]
    assert "editorial-placeholder" in codes, codes


def test_filling_the_gaps_clears_the_finding(fixture_repo: Path) -> None:
    """Gegenprobe: Der Wächter blockiert die Lücke, nicht das Gerüst als solches."""
    prepared = pr.plan(fixture_repo, _inputs(), predecessor_version=_current_freeze_version(fixture_repo))
    pr.apply(fixture_repo, prepared.files)
    for item in prepared.files:
        target = fixture_repo / item.path
        target.write_text(
            target.read_text("utf-8").replace(pr.PLACEHOLDER, "redaktionell gefüllt"), "utf-8"
        )
    _git(fixture_repo, "add", "-A")
    _git(fixture_repo, "commit", "-qm", "gefuellt")

    doc = vrf.parse_freeze_doc((fixture_repo / pr.freeze_doc_path("9.9.9")).read_text("utf-8"))
    findings = vrf._check_release_body(fixture_repo, "HEAD", doc) + vrf._check_freeze_doc_placeholder(
        fixture_repo, "HEAD", doc
    )
    assert not [f for f in findings if f.code == "editorial-placeholder"]
    assert any(f.code == "editorial-scope" for f in findings)


def test_editorial_work_is_never_overwritten(fixture_repo: Path) -> None:
    prepared = pr.plan(fixture_repo, _inputs(), predecessor_version=_current_freeze_version(fixture_repo))
    pr.apply(fixture_repo, prepared.files)
    changelog = fixture_repo / "CHANGELOG.md"
    changelog.write_text(changelog.read_text("utf-8").replace(pr.PLACEHOLDER, "fertig"), "utf-8")

    with pytest.raises(pr.PrepareError, match="redaktionell bearbeitet"):
        pr.plan(fixture_repo, _inputs(), predecessor_version=_current_freeze_version(fixture_repo))


def test_an_edited_freeze_document_is_never_overwritten(fixture_repo: Path) -> None:
    prepared = pr.plan(fixture_repo, _inputs(), predecessor_version=_current_freeze_version(fixture_repo))
    pr.apply(fixture_repo, prepared.files)
    freeze = fixture_repo / pr.freeze_doc_path("9.9.9")
    freeze.write_text(freeze.read_text("utf-8").replace(pr.PLACEHOLDER, "entschieden"), "utf-8")

    with pytest.raises(pr.PrepareError, match="redaktionell bearbeitet"):
        pr.plan(fixture_repo, _inputs(), predecessor_version=_current_freeze_version(fixture_repo))


# ── Das Gerüst passt zu den Verträgen, die es später prüfen ────────────


def test_the_generated_freeze_document_parses_as_a_freeze_document() -> None:
    """Ein Gerüst, das das Gate nicht einmal *lesen* kann, wäre wertlos."""
    doc = vrf.parse_freeze_doc(
        pr.freeze_document(_inputs(), predecessor_version="2.9.0", policy_version=42)
    )
    assert (doc.version, doc.base_tag, doc.base_sha, doc.policy_version) == (
        "9.9.9",
        "v9.9.8",
        "a" * 40,
        42,
    )


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_generated_section_satisfies_the_release_body_contract(language: str) -> None:
    """Alle vier Pflichtmarker sind da – nur ihre *Werte* fehlen noch.

    Das ist die Arbeitsteilung dieses Skripts: Die Gliederung ist mechanisch,
    die Aussage ist es nicht.
    """
    from scripts.extract_release_notes import extract_release_notes

    changelog = f"## [Unreleased]\n\n{pr.changelog_section(language, '9.9.9', '2026-09-15')}\n"
    assert vrf.changelog_release_date(changelog, "9.9.9") == "2026-09-15"
    notes = extract_release_notes(changelog, "9.9.9")
    assert vrf.missing_release_body_markers(notes, language) == ()


@pytest.mark.parametrize("language", LANGUAGES)
def test_section_headings_match_the_house_style_of_that_language(language: str) -> None:
    """Handgepflegte Kopie gegen ihre Quelle: erfundene Übersetzungen fallen auf.

    Die Überschriften stehen im Skript, verwendet werden sie in sechs
    CHANGELOG-Dateien. Ohne Wächter erzeugte ein Tippfehler sechs falsche
    Abschnitte, die niemand mehr gegenliest.
    """
    changelog = (ROOT / pr.changelog_path(language)).read_text("utf-8")
    for heading in pr.SECTION_HEADINGS[language]:
        assert f"### {heading}" in changelog, (language, heading)


def test_runbook_steps_match_the_canonical_runbook() -> None:
    """Die Schritt-Tabelle des Issues ist eine Kopie der Runbook-Gliederung."""
    runbook = (ROOT / "docs" / "RELEASE_PROCESS.md").read_text("utf-8")
    headings = re.findall(r"(?m)^### [1-9]\. (.+)$", runbook)
    assert tuple(headings) == pr.RUNBOOK_STEPS


def test_paused_criteria_are_derived_from_the_checklist_not_hard_coded() -> None:
    checklist = rc.load_release_checklist(ROOT / rc.CHECKLIST_PATH)
    paused = pr.paused_x86_64_criteria(checklist)
    assert paused == ("LINUX-X64-APPIMAGE-01", "LINUX-X64-DEB-01")
    for criterion in checklist["criteria"]:
        if criterion["id"] in paused:
            assert criterion["verification"] == "platform:linux-x86_64"


def test_the_issue_carries_every_binding_value() -> None:
    checklist = rc.load_release_checklist(ROOT / rc.CHECKLIST_PATH)
    body = pr.release_issue(
        _inputs(),
        checklist_version="2.1.0",
        checklist_sha256="c" * 64,
        paused_criteria=pr.paused_x86_64_criteria(checklist),
        policy_version=42,
    )
    for expected in (
        "9.9.9",              # Version
        "`v9.9.9`",           # geplanter Tag
        "v9.9.8",             # Vorgänger-Tag
        "a" * 40,             # Vorgänger-SHA
        "`2.1.0`",            # Checklisten-Version
        "c" * 64,             # Datei-SHA-256
        "Pfadpolicy `42`",
        "LINUX-X64-APPIMAGE-01",
        "ABNAHME_X86_64_ENABLED",
        pr.freeze_doc_path("9.9.9"),
    ):
        assert expected in body, expected
    # Neun Schritte, keiner vergessen.
    assert len(re.findall(r"(?m)^\| \d ", body)) == len(pr.RUNBOOK_STEPS)


# ── Einzelne Bausteine ─────────────────────────────────────────────────


def test_pyproject_bump_requires_exactly_one_version_line() -> None:
    assert 'version = "2.0.0"' in pr.bump_pyproject('version = "1.0.0"\n', "2.0.0")
    with pytest.raises(pr.PrepareError, match="genau eine version-Zeile"):
        pr.bump_pyproject('version = "1.0.0"\nversion = "1.0.1"\n', "2.0.0")
    with pytest.raises(pr.PrepareError, match="genau eine version-Zeile"):
        pr.bump_pyproject("name = 'x'\n", "2.0.0")


def test_appstream_entry_is_inserted_as_the_newest_release() -> None:
    import xml.etree.ElementTree as ET

    original = (ROOT / pr.APPSTREAM_PATH).read_text("utf-8")
    updated = pr.insert_appstream_release(original, "9.9.9", "2026-09-15")
    releases = ET.fromstring(updated).findall("releases/release")
    assert (releases[0].get("version"), releases[0].get("date")) == ("9.9.9", "2026-09-15")
    # Idempotent: ein zweiter Lauf ersetzt den Eintrag, statt ihn zu verdoppeln.
    assert pr.insert_appstream_release(updated, "9.9.9", "2026-09-15") == updated
    assert len(ET.fromstring(updated).findall("releases/release")) == len(
        ET.fromstring(original).findall("releases/release")
    ) + 1


def test_changelog_insertion_needs_the_unreleased_anchor() -> None:
    with pytest.raises(pr.PrepareError, match="Unreleased"):
        pr.insert_changelog_section("# Changelog\n", "de", "9.9.9", "2026-09-15")


def test_policy_rollover_keeps_the_file_shape_and_bumps_exactly_once() -> None:
    original = (ROOT / "release" / "path-policy.json").read_text("utf-8")
    rolled, version = pr.roll_over_freeze_policy(
        original, version="9.9.9", predecessor_version=_current_freeze_version()
    )
    data = json.loads(rolled)
    assert data["policy_version"] == json.loads(original)["policy_version"] + 1 == version
    predecessor = _current_freeze_version()
    entries = {entry["id"]: entry["path"] for entry in data["candidate_relevant"]}
    assert entries["current-freeze"] == pr.freeze_doc_path("9.9.9")
    assert entries[f"historical-freeze-{predecessor}"] == pr.freeze_doc_path(predecessor)
    # Der Drift-Waechter der Release-Dokumente kennt das neue Dokument (#923-Review):
    # ohne diesen Eintrag ist ``make check`` im erzeugten Stand rot, und zwar an
    # einer rein schematischen Stelle, die kein redaktionelles Fuellen behebt.
    assert pr.freeze_doc_path("9.9.9") in data["drift_guards"]["release_documents"]
    # Nur wenige Zeilen bewegen sich – ein json.dumps-Roundtrip schriebe 650 um.
    # Ein reiner Positionsvergleich taugt hier nicht: Die eingefuegte Zeile
    # verschiebt alles danach, difflib zaehlt die tatsaechliche Aenderung.
    changed = [
        line
        for line in difflib.unified_diff(
            original.splitlines(), rolled.splitlines(), lineterm="", n=0
        )
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    ]
    # Erwartet sind acht Zeilen: ``policy_version`` (alt/neu), die umgehängte
    # ``current-freeze``-Zeile (alt/neu), der neue ``historical-freeze``-Eintrag
    # sowie in ``drift_guards`` die letzte Zeile mit/ohne Komma plus der neue
    # Eintrag. Alles darüber hinaus wäre eine Umformatierung.
    assert len(changed) <= 8, changed


def test_policy_rollover_refuses_an_unexpected_predecessor() -> None:
    original = (ROOT / "release" / "path-policy.json").read_text("utf-8")
    with pytest.raises(pr.PrepareError, match="anderen Stand überschreiben"):
        pr.roll_over_freeze_policy(original, version="9.9.9", predecessor_version="1.2.3")


def test_unknown_paths_are_reported_before_the_candidate_build(fixture_repo: Path) -> None:
    """Der Hinweis gehört in die Vorbereitung – im Kandidatenbau kostet er einen Lauf."""
    (fixture_repo / "voellig/neuer/pfad.txt").parent.mkdir(parents=True, exist_ok=True)
    (fixture_repo / "voellig/neuer/pfad.txt").write_text("x", "utf-8")
    _git(fixture_repo, "add", "-A")
    _git(fixture_repo, "commit", "-qm", "unbekannter Pfad")
    base = _git(fixture_repo, "rev-list", "--max-parents=0", "HEAD")
    assert "voellig/neuer/pfad.txt" in pr.unknown_paths_since(fixture_repo, base)


# ── CLI ────────────────────────────────────────────────────────────────


def _stub_gh(directory: Path, *, exit_code: int = 0) -> None:
    """Legt ein ``gh`` an, das seinen Aufruf protokolliert statt GitHub zu rufen."""
    directory.mkdir(parents=True, exist_ok=True)
    stub = directory / "gh"
    stub.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$@" >> "$GH_STUB_LOG"\n'
        'cat >> "$GH_STUB_LOG"\n'
        f'echo "https://github.com/example/repo/issues/1"\nexit {exit_code}\n',
        encoding="utf-8",
    )
    stub.chmod(0o755)


def test_cli_writes_the_skeleton_and_the_issue_file(fixture_repo: Path, tmp_path: Path) -> None:
    issue = tmp_path / "issue.md"
    exit_code = pr.main(
        ["9.9.9", "--date", "2026-09-15", "--repo", str(fixture_repo), "--issue-output", str(issue)]
    )
    assert exit_code == 0
    assert (fixture_repo / pr.freeze_doc_path("9.9.9")).is_file()
    assert 'version = "9.9.9"' in (fixture_repo / "pyproject.toml").read_text("utf-8")
    assert pr.PLACEHOLDER in issue.read_text("utf-8")


def test_cli_dry_run_changes_nothing(fixture_repo: Path, capsys) -> None:
    before = {
        path: path.read_bytes() for path in sorted(fixture_repo.rglob("*")) if path.is_file()
    }
    assert pr.main(["9.9.9", "--date", "2026-09-15", "--repo", str(fixture_repo), "--dry-run"]) == 0
    after = {path: path.read_bytes() for path in sorted(fixture_repo.rglob("*")) if path.is_file()}
    assert after == before
    assert "geplant" in capsys.readouterr().out


def test_cli_refuses_a_version_that_is_already_current(fixture_repo: Path, capsys) -> None:
    current = re.search(
        r'(?m)^version\s*=\s*"([^"]+)"', (fixture_repo / "pyproject.toml").read_text("utf-8")
    )
    assert current is not None
    assert pr.main([current.group(1), "--repo", str(fixture_repo)]) == 2
    assert "bereits auf" in capsys.readouterr().err


def test_cli_rejects_a_malformed_version(fixture_repo: Path) -> None:
    with pytest.raises(SystemExit):
        pr.main(["2.10", "--repo", str(fixture_repo)])


def test_cli_reports_unknown_paths_as_a_policy_hint(fixture_repo: Path, capsys) -> None:
    (fixture_repo / "unbekannt.xyz").write_text("x", "utf-8")
    _git(fixture_repo, "add", "-A")
    _git(fixture_repo, "commit", "-qm", "unbekannter Pfad")
    assert pr.main(["9.9.9", "--date", "2026-09-15", "--repo", str(fixture_repo)]) == 0
    err = capsys.readouterr().err
    assert "ohne explizite Klassifikation" in err
    assert "unbekannt.xyz" in err


def _with_gh_stub(tmp_path: Path, monkeypatch, *, exit_code: int = 0) -> Path:
    """Setzt einen ``gh``-Stub auf den PATH und liefert seine Protokolldatei."""
    import os

    bin_dir = tmp_path / "bin"
    log = tmp_path / "gh.log"
    _stub_gh(bin_dir, exit_code=exit_code)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.setenv("GH_STUB_LOG", str(log))
    return log


def test_no_github_call_happens_without_the_opt_in(
    fixture_repo: Path, tmp_path: Path, monkeypatch
) -> None:
    """Nicht-Ziel des Issues: kein automatisches Anlegen ohne expliziten Opt-in."""
    log = _with_gh_stub(tmp_path, monkeypatch)
    assert pr.main(["9.9.9", "--date", "2026-09-15", "--repo", str(fixture_repo)]) == 0
    assert not log.exists(), "ohne --create-issue darf gh nicht laufen"


def test_create_issue_passes_title_and_body_to_gh(
    fixture_repo: Path, tmp_path: Path, monkeypatch
) -> None:
    log = _with_gh_stub(tmp_path, monkeypatch)
    assert (
        pr.main(
            [
                "9.9.9",
                "--date",
                "2026-09-15",
                "--repo",
                str(fixture_repo),
                "--issue-output",
                str(tmp_path / "issue.md"),
                "--create-issue",
            ]
        )
        == 0
    )
    recorded = log.read_text("utf-8")
    assert "issue" in recorded and "create" in recorded
    assert "[Release 9.9.9] Abnahme- und Veröffentlichungsprotokoll" in recorded
    # Der Body kommt über stdin, nicht als Argument: sonst sprengt er die Kommandozeile.
    assert "--body-file" in recorded and "## Ziel" in recorded


def test_a_failing_gh_is_reported_and_not_swallowed(
    fixture_repo: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    _with_gh_stub(tmp_path, monkeypatch, exit_code=1)
    assert (
        pr.main(["9.9.9", "--date", "2026-09-15", "--repo", str(fixture_repo), "--create-issue"])
        == 2
    )
    assert "gh issue create fehlgeschlagen" in capsys.readouterr().err


# ── Governance: die Doku sagt, was der Code tut ────────────────────────


def test_the_runbook_names_the_script_as_the_standard_path() -> None:
    """Akzeptanzkriterium: Schritt 1/2 verweist auf das Skript."""
    runbook = (ROOT / "docs" / "RELEASE_PROCESS.md").read_text("utf-8")
    step_one = runbook.split("### 1. Release vorbereiten", 1)[1].split("### 2. ", 1)[0]
    assert "scripts/prepare_release.py" in step_one
    # Und benennt die beiden Eigenschaften, die den Rohstand ungefährlich machen.
    assert pr.PLACEHOLDER in step_one
    assert "NOTES-01" in step_one
    assert "--create-issue" in step_one


def test_the_placeholder_token_has_a_single_source() -> None:
    """Der Token steht im Gate; das Skript importiert ihn, statt ihn zu kopieren.

    Zwei Literale wären der Anfang der Drift: Ein Gerüst mit dem einen und ein
    Wächter mit dem anderen Token liefe still grün durch.
    """
    assert pr.PLACEHOLDER is vrf.EDITORIAL_PLACEHOLDER
    source = (ROOT / "scripts" / "prepare_release.py").read_text("utf-8")
    assert f'"{vrf.EDITORIAL_PLACEHOLDER}"' not in source


def test_dry_run_previews_the_issue_and_never_calls_gh(
    fixture_repo: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    """Ein Probelauf zeigt alles und schreibt nichts – auch nicht über ``gh``."""
    log = _with_gh_stub(tmp_path, monkeypatch)
    assert (
        pr.main(
            [
                "9.9.9",
                "--date",
                "2026-09-15",
                "--repo",
                str(fixture_repo),
                "--dry-run",
                "--create-issue",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "Release-Issue (Vorschau)" in captured.out
    assert "## Gebundener Release-Stand" in captured.out
    assert "im Probelauf nicht ausgeführt" in captured.err
    assert not log.exists()
    assert not (fixture_repo / pr.freeze_doc_path("9.9.9")).exists()


@pytest.mark.parametrize(
    ("version", "predecessor", "expected"),
    [
        ("2.10.0", "2.9.0", "minor-release-2.10.0"),
        ("2.9.1", "2.9.0", "patch-release-2.9.1"),
        ("3.0.0", "2.9.0", "minor-release-3.0.0"),
        ("2.7.3", "2.7.2", "patch-release-2.7.3"),
    ],
)
def test_scope_name_follows_the_house_convention(
    version: str, predecessor: str, expected: str
) -> None:
    """Ableitbar aus dem Versionssprung – die bisherigen Dokumente belegen das Schema."""
    assert pr.scope_name(version, predecessor) == expected


def test_the_existing_freeze_documents_use_that_very_scheme() -> None:
    """Handgepflegte Konvention gegen ihre Quelle: die vier echten Dokumente."""
    any_scope = re.compile(r"(?m)^- \*\*Release-Scope:\*\* `([^`]+)`")
    house_style = re.compile(r"^(?:minor|patch)-release-\d+\.\d+\.\d+$")
    # 2.6.0 und 2.7.1 stammen aus der Zeit vor der maschinenlesbaren Zeile –
    # geprüft wird die Konvention dort, wo die Zeile existiert.
    scopes = {
        document.name: match.group(1)
        for document in sorted((ROOT / "docs" / "history").glob("RELEASE-*-scope-freeze.md"))
        if (match := any_scope.search(document.read_text("utf-8"))) is not None
    }
    assert len(scopes) >= 4, scopes
    for name, scope in scopes.items():
        assert house_style.fullmatch(scope), (name, scope)
