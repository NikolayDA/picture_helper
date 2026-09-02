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
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
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


def test_the_full_gate_reports_the_gap_not_just_the_helper(
    fixture_repo: Path, monkeypatch
) -> None:
    """Der Wächter muss in ``verify()`` **verdrahtet** sein, nicht nur existieren.

    Ein Test, der nur die Hilfsfunktionen direkt aufruft, bliebe grün, wenn
    jemand den Aufruf aus ``verify()`` entfernt – der Befund fiele dann still
    aus dem Gate. Deshalb hier der vollständige Lauf.

    Die Actions-Umgebung wird dafür neutralisiert: ``_check_workflow_candidate``
    bindet das Gate sonst an ``GITHUB_SHA``, und dieser Commit existiert im
    Fixture-Repository nicht. Lokal fiel das nicht auf, in der PR-CI schon –
    dieselbe Vorsichtsmaßnahme trifft ``tests/test_release_freeze.py``.
    """
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    for name in (
        "GITHUB_SHA",
        "GITHUB_REPOSITORY",
        "GITHUB_WORKFLOW",
        "GITHUB_RUN_ID",
        "GITHUB_RUN_ATTEMPT",
    ):
        monkeypatch.delenv(name, raising=False)
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

    with pytest.raises(pr.PrepareError, match="weicht vom erzeugten Gerüst ab"):
        pr.plan(fixture_repo, _inputs(), predecessor_version=_current_freeze_version(fixture_repo))


def test_partially_filled_sections_are_never_overwritten(fixture_repo: Path) -> None:
    """#932-Review: „enthält noch einen Platzhalter" ist kein Beleg für „unberührt".

    Realistischer Ablauf: Skript laufen lassen, die Einträge in sechs Sprachen
    ausformulieren, die Notizen-Marker offen lassen — und das Skript wegen
    eines verschobenen Datums erneut aufrufen. Unter der alten Bedingung wären
    die fertigen Einträge kommentarlos durch das Gerüst ersetzt worden.
    """
    predecessor = _current_freeze_version(fixture_repo)
    prepared = pr.plan(fixture_repo, _inputs(), predecessor_version=predecessor)
    pr.apply(fixture_repo, prepared.files)

    changelog = fixture_repo / "CHANGELOG.md"
    text = changelog.read_text("utf-8")
    # Nur EINE Lücke füllen; die Notizen-Marker bleiben offen.
    filled = text.replace(f"- {pr.PLACEHOLDER}", "- **Neues Werkzeug.** Ausformuliert.", 1)
    assert pr.PLACEHOLDER in filled, "Vorbedingung: es bleiben Platzhalter übrig"
    changelog.write_text(filled, "utf-8")

    with pytest.raises(pr.PrepareError, match="weicht vom erzeugten Gerüst ab"):
        pr.plan(fixture_repo, _inputs(), predecessor_version=predecessor)


def test_a_partially_written_freeze_scope_is_never_overwritten(fixture_repo: Path) -> None:
    predecessor = _current_freeze_version(fixture_repo)
    prepared = pr.plan(fixture_repo, _inputs(), predecessor_version=predecessor)
    pr.apply(fixture_repo, prepared.files)

    freeze = fixture_repo / pr.freeze_doc_path("9.9.9")
    text = freeze.read_text("utf-8")
    freeze.write_text(text.replace(f"{pr.PLACEHOLDER}: Fachlichen Scope", "Der Scope ist", 1), "utf-8")
    assert pr.PLACEHOLDER in freeze.read_text("utf-8")

    with pytest.raises(pr.PrepareError, match="weicht vom erzeugten Gerüst ab"):
        pr.plan(fixture_repo, _inputs(), predecessor_version=predecessor)


def test_a_changed_date_still_refreshes_an_untouched_skeleton(fixture_repo: Path) -> None:
    """Die eine zulässige Abweichung: ein Lauf mit anderem ``--date``."""
    predecessor = _current_freeze_version(fixture_repo)
    pr.apply(fixture_repo, pr.plan(fixture_repo, _inputs(), predecessor_version=predecessor).files)
    later = pr.ReleaseInputs(
        version="9.9.9", release_date="2026-10-01", base_tag="v9.9.8", base_sha="a" * 40
    )
    refreshed = pr.plan(fixture_repo, later, predecessor_version=predecessor)
    changelog = next(item for item in refreshed.files if item.path == "CHANGELOG.md")
    assert "## [9.9.9] – 2026-10-01" in changelog.content
    assert "## [9.9.9] – 2026-09-15" not in changelog.content


def test_unreleased_entries_move_under_the_skeleton_and_survive_a_rerun(
    fixture_repo: Path,
) -> None:
    """Review 2026-09-02: Ein gefülltes ``[Unreleased]`` ist vor einem Release der
    Normalfall. Seine Einträge wandern beim ersten Lauf unter das Gerüst der
    neuen Version; ein zweiter Lauf – auch mit anderem Datum – erkennt das
    Gerüst weiterhin und lässt die gewanderten Einträge wortgleich stehen.
    Über die CLI trifft das nur den Wiederanlauf mit zurückgedrehter
    ``pyproject.toml`` (sonst greift der Downgrade-Schutz zuerst); ``plan()``
    direkt trifft den Zweig immer, und vorher scheiterte er bei gefülltem
    ``[Unreleased]`` grundsätzlich mit „weicht vom Gerüst ab".
    """
    predecessor = _current_freeze_version(fixture_repo)
    entry = "- **Neues Werkzeug (#1).** Stand vor dem Lauf unter [Unreleased]."
    for language in LANGUAGES:
        path = fixture_repo / pr.changelog_path(language)
        text = path.read_text("utf-8")
        text = re.sub(
            r"(?m)^## \[Unreleased\][ \t]*$",
            f"## [Unreleased]\n\n### Neu\n\n{entry}",
            text,
            count=1,
        )
        path.write_text(text, "utf-8")

    pr.apply(fixture_repo, pr.plan(fixture_repo, _inputs(), predecessor_version=predecessor).files)
    changelog = fixture_repo / "CHANGELOG.md"
    first = changelog.read_text("utf-8")
    unreleased = first.split("## [Unreleased]", 1)[1].split("## [9.9.9]", 1)[0]
    assert entry not in unreleased and "- " not in unreleased, "Unreleased muss leer sein"
    section = first.split("## [9.9.9]", 1)[1].split("\n## [", 1)[0]
    assert entry in section and pr.PLACEHOLDER in section

    # Gleiches Datum: byte-gleich.
    pr.apply(fixture_repo, pr.plan(fixture_repo, _inputs(), predecessor_version=predecessor).files)
    assert changelog.read_text("utf-8") == first

    # Anderes Datum: Gerüst erneuert, gewanderter Eintrag bleibt.
    later = pr.ReleaseInputs(
        version="9.9.9", release_date="2026-10-01", base_tag="v9.9.8", base_sha="a" * 40
    )
    refreshed = next(
        item
        for item in pr.plan(fixture_repo, later, predecessor_version=predecessor).files
        if item.path == "CHANGELOG.md"
    ).content
    assert "## [9.9.9] – 2026-10-01" in refreshed and "2026-09-15" not in refreshed
    assert entry in refreshed and refreshed.count(entry) == 1

    # Handarbeit an der letzten Gerüstzeile bleibt geschützt.
    head, _, tail = first.rpartition(pr.PLACEHOLDER)
    changelog.write_text(f"{head}keine{tail}", "utf-8")
    with pytest.raises(pr.PrepareError, match="weicht vom erzeugten Gerüst ab"):
        pr.plan(fixture_repo, _inputs(), predecessor_version=predecessor)


def test_cli_rerun_needs_a_pyproject_reset_and_then_keeps_moved_entries(
    fixture_repo: Path, tmp_path: Path, capsys
) -> None:
    """#954-Review: der Wiederanlaufweg über die CLI, nicht nur über ``plan()``.

    Ein unveränderter zweiter Aufruf ist **kein** Wiederanlauf: ``pyproject.toml``
    trägt nach dem ersten Lauf die Zielversion, und ``main()`` bricht am
    #944-Schutz ab, bevor ``insert_changelog_section`` läuft. Erst
    ``git checkout pyproject.toml`` erreicht den Zweig erneut – dann bleiben
    die aus ``[Unreleased]`` gewanderten Einträge stehen und das Ergebnis ist
    byte-gleich.
    """
    entry = "- **Neues Werkzeug (#1).** Stand vor dem Lauf unter [Unreleased]."
    for language in LANGUAGES:
        path = fixture_repo / pr.changelog_path(language)
        path.write_text(
            re.sub(
                r"(?m)^## \[Unreleased\][ \t]*$",
                f"## [Unreleased]\n\n### Neu\n\n{entry}",
                path.read_text("utf-8"),
                count=1,
            ),
            "utf-8",
        )
    args = [
        "9.9.9", "--date", "2026-09-15", "--repo", str(fixture_repo),
        "--issue-output", str(tmp_path / "issue.md"),
    ]
    assert pr.main(args) == 0
    changelog = fixture_repo / "CHANGELOG.md"
    first = changelog.read_text("utf-8")
    assert entry in first.split("## [9.9.9]", 1)[1].split("\n## [", 1)[0]

    # Unveränderter zweiter Aufruf: Downgrade-/Gleichheitsschutz, nichts geschrieben.
    assert pr.main(args) == 2
    err = capsys.readouterr().err
    assert "pyproject" in err and "9.9.9" in err
    assert changelog.read_text("utf-8") == first

    # Wiederanlauf: pyproject zurückdrehen, CHANGELOGs stehen lassen.
    _git(fixture_repo, "checkout", "--", "pyproject.toml")
    assert pr.main(args) == 0
    assert changelog.read_text("utf-8") == first


def test_the_freeze_boilerplate_never_carries_the_placeholder_itself() -> None:
    """#932-Review (P1): Der Wächter durchsucht die ganze Datei.

    Stünde der Token in einem erklärenden Satz, bliebe das Dokument auch nach
    dem Füllen aller echten Lücken für immer rot.
    """
    document = pr.freeze_document(_inputs(), predecessor_version="2.9.0", policy_version=42)
    gaps = [line for line in document.splitlines() if pr.PLACEHOLDER in line]
    assert gaps, "das Gerüst muss überhaupt Lücken markieren"
    for line in gaps:
        assert line.lstrip().startswith(pr.PLACEHOLDER), (
            f"Platzhalter nur als Markierung einer Lücke, nicht in Prosa: {line!r}"
        )
    # Gegenprobe der Behebbarkeit: Nach dem Füllen der markierten Lücken ist
    # der Token weg – ohne dass jemand einen Fließtext anfassen muss.
    filled = "\n".join(
        "gefüllt" if pr.PLACEHOLDER in line else line for line in document.splitlines()
    )
    assert pr.PLACEHOLDER not in filled


def test_an_edited_freeze_document_is_never_overwritten(fixture_repo: Path) -> None:
    prepared = pr.plan(fixture_repo, _inputs(), predecessor_version=_current_freeze_version(fixture_repo))
    pr.apply(fixture_repo, prepared.files)
    freeze = fixture_repo / pr.freeze_doc_path("9.9.9")
    freeze.write_text(freeze.read_text("utf-8").replace(pr.PLACEHOLDER, "entschieden"), "utf-8")

    with pytest.raises(pr.PrepareError, match="weicht vom erzeugten Gerüst ab"):
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
    """Legt ein ``gh`` an, das seinen Aufruf protokolliert statt GitHub zu rufen.

    Der Body kommt seit #933 als Datei. Der Stub legt sie unter
    ``$GH_STUB_BODY`` ab – erst das macht den bytegenauen Vergleich möglich.
    """
    directory.mkdir(parents=True, exist_ok=True)
    stub = directory / "gh"
    stub.write_text(
        "#!/bin/sh\n"
        'previous=""\n'
        "for argument do\n"
        '  printf "%s\\n" "$argument" >> "$GH_STUB_LOG"\n'
        '  if [ "$previous" = "--body-file" ] && [ -n "$GH_STUB_BODY" ]; then\n'
        '    cp "$argument" "$GH_STUB_BODY"\n'
        "  fi\n"
        '  previous="$argument"\n'
        "done\n"
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


def test_cli_refuses_a_downgrade_target(fixture_repo: Path, capsys) -> None:
    """#943 Befund 3: Bei Stand 2.9.0 lief ein Aufruf für 2.8.1 durch und
    plante ein in sich konsistentes Downgrade-Gerüst über pyproject, sechs
    CHANGELOGs, AppStream, Pfadpolicy und Freeze-Dokument – auch der
    ``--dry-run`` meldete Erfolg."""
    before = {
        path: path.read_bytes() for path in sorted(fixture_repo.rglob("*")) if path.is_file()
    }
    assert pr.main(["0.0.1", "--repo", str(fixture_repo)]) == 2
    assert "liegt nicht über" in capsys.readouterr().err
    after = {path: path.read_bytes() for path in sorted(fixture_repo.rglob("*")) if path.is_file()}
    assert after == before, "ein abgewiesenes Downgrade darf nichts schreiben"


def test_an_unwritable_issue_output_leaves_the_repo_untouched(
    fixture_repo: Path, tmp_path: Path, capsys
) -> None:
    """#943 Befund 4: ``apply`` lief vor der Issue-Ablage – ein nicht
    beschreibbarer ``--issue-output`` hinterließ ein bereits mutiertes Repo,
    dessen Wiederanlauf abbricht („pyproject steht bereits auf …")."""
    blocked = tmp_path / "blocked"
    blocked.mkdir()  # ein Verzeichnis als Zieldatei scheitert beim os.replace
    before = {
        path: path.read_bytes() for path in sorted(fixture_repo.rglob("*")) if path.is_file()
    }
    code = pr.main(
        ["9.9.9", "--date", "2026-09-15", "--repo", str(fixture_repo),
         "--issue-output", str(blocked)]
    )
    assert code == 2
    assert "nicht beschreibbar" in capsys.readouterr().err
    after = {path: path.read_bytes() for path in sorted(fixture_repo.rglob("*")) if path.is_file()}
    assert after == before, "eine gescheiterte Issue-Ablage darf nichts mutiert haben"


def test_the_issue_file_is_persisted_before_the_repo_is_touched(
    fixture_repo: Path, tmp_path: Path, monkeypatch
) -> None:
    """Die Reihenfolge selbst ist der Vertrag: Erst die externe Ablage, dann
    ``apply`` – sonst kehrt der Fehler aus Befund 4 mit dem nächsten Umbau
    zurück."""
    issue = tmp_path / "issue.md"

    def boom(repo: Path, planned) -> None:
        raise RuntimeError("apply erreicht")

    monkeypatch.setattr(pr, "apply", boom)
    with pytest.raises(RuntimeError, match="apply erreicht"):
        pr.main(
            ["9.9.9", "--date", "2026-09-15", "--repo", str(fixture_repo),
             "--issue-output", str(issue)]
        )
    assert issue.is_file(), "Issue-Text muss vor der ersten Repo-Schreibung liegen"
    assert 'version = "9.9.9"' not in (fixture_repo / "pyproject.toml").read_text("utf-8")


def test_the_downgrade_guard_compares_numerically_not_lexicographically(
    fixture_repo: Path, capsys
) -> None:
    """Als Text verglichen läge ``2.10.0`` unter ``2.9.0`` – der reguläre
    Minor-Sprung wäre ausgerechnet der abgewiesene Fall."""
    assert pr._semver_key("2.10.0") > pr._semver_key("2.9.0")
    major, minor, _patch = pr._semver_key(_current_version(fixture_repo))
    target = f"{major}.{minor + 1}.0"
    assert pr.main([target, "--date", "2026-09-15", "--repo", str(fixture_repo), "--dry-run"]) == 0
    assert "geplant" in capsys.readouterr().out


def test_a_leading_zero_spelling_is_rejected(fixture_repo: Path) -> None:
    """#944-Review: ``2.09.0`` bei Stand ``2.9.0`` umging beide Prüfungen –
    der String-Vergleich sieht Ungleichheit, der Ordnungsvergleich Gleichheit –
    und erzeugte Release-Dateien für eine Schreibweise, die Packaging-Werkzeuge
    auf die bereits aktuelle Version normalisieren."""
    major, minor, patch = pr._semver_key(_current_version(fixture_repo))
    respelled = f"{major}.0{minor}.{patch}"
    for version in (respelled, "2.09.0", "02.9.0", "2.9.00"):
        with pytest.raises(SystemExit):
            pr.main([version, "--repo", str(fixture_repo)])


def test_atomic_writes_preserve_the_tracked_file_mode(tmp_path: Path) -> None:
    """#944-Review: ``mkstemp`` erzeugt 0600, und ``os.replace`` installierte
    diesen Inode über die getrackte 0644-Datei – pyproject/CHANGELOGs wären
    danach für andere Konten eines geteilten Checkouts unlesbar."""
    import stat as stat_module

    tracked = tmp_path / "pyproject.toml"
    tracked.write_text("alt", encoding="utf-8")
    os.chmod(tracked, 0o644)
    pr.write_text_atomic(tracked, "neu")
    assert tracked.read_text(encoding="utf-8") == "neu"
    assert stat_module.S_IMODE(tracked.stat().st_mode) == 0o644

    executable = tmp_path / "hook.sh"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    os.chmod(executable, 0o755)
    pr.write_text_atomic(executable, "#!/bin/sh\nexit 0\n")
    assert stat_module.S_IMODE(executable.stat().st_mode) == 0o755

    fresh = tmp_path / "neu.md"
    previous_mask = os.umask(0o022)
    try:
        pr.write_text_atomic(fresh, "x")
    finally:
        os.umask(previous_mask)
    assert stat_module.S_IMODE(fresh.stat().st_mode) == 0o644


def test_cli_reports_unknown_paths_as_a_policy_hint(fixture_repo: Path, capsys) -> None:
    (fixture_repo / "unbekannt.xyz").write_text("x", "utf-8")
    _git(fixture_repo, "add", "-A")
    _git(fixture_repo, "commit", "-qm", "unbekannter Pfad")
    assert pr.main(["9.9.9", "--date", "2026-09-15", "--repo", str(fixture_repo)]) == 0
    err = capsys.readouterr().err
    assert "ohne explizite Klassifikation" in err
    assert "unbekannt.xyz" in err


#: Die eine ausführbare Zeile, die der Fehlerpfad ausgibt.
_RESUME_LINE = re.compile(r"(?m)^\s*(cd .+ && gh issue create .+)$")


def _resume_command(stderr: str) -> str:
    """Zieht den ausgegebenen Wiederanlaufbefehl aus der Fehlermeldung."""
    match = _RESUME_LINE.search(stderr)
    assert match is not None, stderr
    return match.group(1)


def _worktree_hashes(repo: Path) -> dict[str, str]:
    """SHA-256 jeder Arbeitsbaumdatei – ``.git`` bleibt außen vor."""
    return {
        str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(repo.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(repo).parts
    }


def _with_gh_stub(tmp_path: Path, monkeypatch, *, exit_code: int = 0) -> Path:
    """Setzt einen ``gh``-Stub auf den PATH und liefert seine Protokolldatei.

    Zieht dabei auch die Fallback-Ablage unter die pytest-Aufräumung: Der
    Fehlerpfad räumt bewusst nicht auf, sonst bliebe je Lauf ein
    ``bgremover-release-*`` im System-Tempverzeichnis liegen. ``tempfile``
    cacht ``gettempdir()``, ein gesetztes ``TMPDIR`` wirkte hier also nicht
    mehr – deshalb direkt ``tempfile.tempdir``.
    """
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    bin_dir = tmp_path / "bin"
    log = tmp_path / "gh.log"
    _stub_gh(bin_dir, exit_code=exit_code)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.setenv("GH_STUB_LOG", str(log))
    monkeypatch.setenv("GH_STUB_BODY", str(tmp_path / "gh-body.md"))
    return log


def test_no_github_call_happens_without_the_opt_in(
    fixture_repo: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    """Nicht-Ziel des Issues: kein automatisches Anlegen ohne expliziten Opt-in.

    Und ohne Opt-in bleibt es bei der Standardausgabe: Die Ablage aus #933
    entsteht nur, wenn wirklich ein ``gh``-Aufruf bevorsteht.
    """
    log = _with_gh_stub(tmp_path, monkeypatch)
    assert pr.main(["9.9.9", "--date", "2026-09-15", "--repo", str(fixture_repo)]) == 0
    assert not log.exists(), "ohne --create-issue darf gh nicht laufen"
    out = capsys.readouterr().out
    assert "--- Release-Issue:" in out and "## Gebundener Release-Stand" in out
    assert "gesichert für den Wiederanlauf" not in out


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
    # Der Body kommt als Datei, nicht als Argument: sonst sprengt er die
    # Kommandozeile. Übergeben wird genau die mit --issue-output erzeugte Datei.
    assert "--body-file" in recorded and "## Ziel" not in recorded
    assert str(tmp_path / "issue.md") in recorded
    assert (tmp_path / "gh-body.md").read_bytes() == (tmp_path / "issue.md").read_bytes()


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


def test_the_policy_hint_reads_the_selected_repositorys_policy(fixture_repo: Path) -> None:
    """``--repo`` muss auch für die Pfadpolicy gelten (#932-Review).

    Sonst klassifizierte der Hinweis fremde Historie gegen die Policy des
    Checkouts, in dem dieses Skript liegt – er verschwiege unbekannte Pfade
    oder erfände welche, und weil er nichts blockiert, fiele das nirgends auf.
    """
    # Im Fixture-Repo eine Policy, die den sonst unbekannten Pfad erlaubt.
    policy_file = fixture_repo / pr.POLICY_PATH
    policy = json.loads(policy_file.read_text("utf-8"))
    policy["release_neutral"].append(
        {
            "id": "test-only",
            "kind": "exact",
            "path": "nur-hier-bekannt.txt",
            "sample_path": "nur-hier-bekannt.txt",
            "reason": "Fixture-Eintrag für den --repo-Test.",
            "evidence": ["nur im Fixture"],
        }
    )
    policy_file.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", "utf-8")
    (fixture_repo / "nur-hier-bekannt.txt").write_text("x", "utf-8")
    _git(fixture_repo, "add", "-A")
    _git(fixture_repo, "commit", "-qm", "Pfad, den nur die Fixture-Policy kennt")

    base = _git(fixture_repo, "rev-list", "--max-parents=0", "HEAD")
    unknown = pr.unknown_paths_since(fixture_repo, base)
    assert "nur-hier-bekannt.txt" not in unknown, (
        "die Policy des gewählten Repositorys muss gelten, nicht die des Skript-Checkouts"
    )


def test_a_unicode_digit_version_is_rejected(fixture_repo: Path) -> None:
    """``\\d`` akzeptiert auch ``２.１０.０`` – das liefe bis in Tags und Metadaten."""
    with pytest.raises(SystemExit):
        pr.main(["２.１０.０", "--repo", str(fixture_repo)])


def test_an_impossible_calendar_date_is_rejected(fixture_repo: Path) -> None:
    """Formprüfung genügt nicht: ``2026-02-31`` stünde danach in acht Dateien."""
    with pytest.raises(SystemExit):
        pr.main(["9.9.9", "--date", "2026-02-31", "--repo", str(fixture_repo)])


def test_a_failed_issue_creation_names_the_retry_path(
    fixture_repo: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    """Nach einem gescheiterten ``gh`` bricht ein zweiter Skriptlauf ab.

    Der Rohstand steht dann bereits, und die Zielversion entspricht der
    pyproject-Version – ohne konkreten Wiederanlauf säße der Release-Owner in
    einer Sackgasse.
    """
    _with_gh_stub(tmp_path, monkeypatch, exit_code=1)
    issue = tmp_path / "issue.md"
    assert (
        pr.main(
            [
                "9.9.9",
                "--date",
                "2026-09-15",
                "--repo",
                str(fixture_repo),
                "--issue-output",
                str(issue),
                "--create-issue",
            ]
        )
        == 2
    )
    err = capsys.readouterr().err
    assert "gh issue create" in err and str(issue) in err
    assert issue.is_file(), "die Issue-Datei muss vor dem gh-Aufruf geschrieben sein"
    # Der Wiederanlauf trägt den mit --repo gewählten Zielkontext: ``gh`` liest
    # das Zielrepository aus dem Arbeitsverzeichnis.
    command = _resume_command(err)
    assert command.startswith(f"cd {shlex.quote(str(fixture_repo))} && gh issue create ")


def test_the_default_call_leaves_an_executable_resume(
    fixture_repo: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    """Der Standardfehlerfall **ohne** ``--issue-output`` (#933).

    Bis dahin verwies die Meldung auf einen Platzhalter statt auf eine Datei:
    Der Rohstand stand, der gerenderte Issue-Text war nur Standardausgabe, und
    ein zweiter Skriptlauf bricht ab ("pyproject steht bereits auf ...").

    Der Test führt deshalb **genau** die ausgegebene Zeile aus und vergleicht
    den übergebenen Body bytegenau mit dem eines sauberen Laufs.
    """
    # Vergleichsmaßstab auf einer Kopie – unabhängig von der Datei, die der
    # Fehlerpfad selbst schreibt (sonst prüfte der Test sich selbst).
    reference = tmp_path / "reference"
    shutil.copytree(fixture_repo, reference)
    expected = tmp_path / "expected.md"
    assert (
        pr.main(
            [
                "9.9.9",
                "--date",
                "2026-09-15",
                "--repo",
                str(reference),
                "--issue-output",
                str(expected),
            ]
        )
        == 0
    )

    _with_gh_stub(tmp_path, monkeypatch, exit_code=1)
    assert (
        pr.main(["9.9.9", "--date", "2026-09-15", "--repo", str(fixture_repo), "--create-issue"])
        == 2
    )
    err = capsys.readouterr().err
    command = _resume_command(err)
    assert command.startswith(f"cd {shlex.quote(str(fixture_repo))} && gh issue create ")

    body_file = Path(shlex.split(command[command.index("gh issue create") :])[-1])
    assert body_file.is_file(), "der Wiederanlauf darf nur vorhandene Eingaben nennen"
    # Außerhalb des Arbeitsbaums: im Repository wäre die Ablage ein unbekannter
    # Pfad und blockierte damit das Freeze-Gate.
    assert fixture_repo not in body_file.parents

    before = _worktree_hashes(fixture_repo)
    delivered = tmp_path / "delivered.md"
    success_bin = tmp_path / "bin-ok"
    _stub_gh(success_bin)
    result = subprocess.run(
        command,
        # Genau die ausgegebene Zeile, unverändert – das ist der Kern des Tests.
        shell=True,
        env={
            **os.environ,
            "PATH": f"{success_bin}:{os.environ['PATH']}",
            "GH_STUB_LOG": str(tmp_path / "resume.log"),
            "GH_STUB_BODY": str(delivered),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert delivered.read_bytes() == expected.read_bytes()
    # Idempotent gegenüber den Release-Dateien: der Wiederanlauf legt das Issue
    # an und sonst nichts.
    assert _worktree_hashes(fixture_repo) == before


def test_a_relative_issue_output_stays_valid_for_gh_and_the_resume(
    fixture_repo: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    """Relativer ``--issue-output`` (#933-Review).

    Geschrieben wird relativ zum **Prozess-CWD**, ``gh`` läuft aber mit
    ``cwd=repo``: Unaufgelöst zeigte derselbe Pfad damit auf zwei verschiedene
    Dateien – und die Wiederanlaufzeile auf gar keine. Der Fallback verdeckte
    das, weil ``mkdtemp`` absolut liefert.
    """
    log = _with_gh_stub(tmp_path, monkeypatch, exit_code=1)
    workdir = tmp_path / "cwd"
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    assert (
        pr.main(
            [
                "9.9.9",
                "--date",
                "2026-09-15",
                "--repo",
                str(fixture_repo),
                "--issue-output",
                "issue.md",
                "--create-issue",
            ]
        )
        == 2
    )
    written = workdir / "issue.md"
    assert written.is_file() and not (fixture_repo / "issue.md").exists()
    # ``gh`` bekommt den absoluten Pfad – sonst suchte es <repo>/issue.md.
    assert str(written) in log.read_text("utf-8")
    command = _resume_command(capsys.readouterr().err)
    body_file = Path(shlex.split(command[command.index("gh issue create") :])[-1])
    assert body_file == written and body_file.is_file()


def test_a_successful_creation_leaves_no_stray_copy(
    fixture_repo: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    """Die Ablage trägt den Wiederanlauf – nach Erfolg ist sie überflüssig.

    Eine zurückbleibende zweite Fassung des Issue-Texts wäre nur noch eine
    alternde Kopie dessen, was auf GitHub steht.
    """
    _with_gh_stub(tmp_path, monkeypatch)
    assert (
        pr.main(["9.9.9", "--date", "2026-09-15", "--repo", str(fixture_repo), "--create-issue"])
        == 0
    )
    out = capsys.readouterr().out
    saved = re.search(r"(?m)^\s*gesichert für den Wiederanlauf: (.+)$", out)
    assert saved is not None, out
    assert "Issue angelegt" in out
    # Der Body war da, als gh lief – nur die Ablage ist danach weg.
    assert (tmp_path / "gh-body.md").is_file()
    fallback = Path(saved.group(1))
    assert not fallback.exists() and not fallback.parent.exists()


def test_the_fallback_never_lands_inside_the_worktree(fixture_repo: Path, monkeypatch) -> None:
    """``TMPDIR`` im Arbeitsbaum darf die Ablage nicht ins Repository ziehen.

    Sie wäre dort ein unbekannter Pfad, den ein ``git add -A`` mitnimmt – und
    blockierte damit ausgerechnet das fail-closed Freeze-Gate, das der Rohstand
    bestehen soll (#933-Review).
    """
    inside = fixture_repo / "tmp"
    inside.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(inside))
    root = pr.fallback_root(fixture_repo)
    assert fixture_repo != root and fixture_repo not in root.parents

    path = pr.fallback_issue_path("9.9.9", fixture_repo)
    assert fixture_repo not in path.parents
    pr.discard_fallback(path)


def test_the_fallback_uses_the_temporary_directory_when_it_is_outside(
    fixture_repo: Path, tmp_path: Path, monkeypatch
) -> None:
    """Der Normalfall bleibt das Tempverzeichnis – nicht der Repo-Elternpfad."""
    outside = tmp_path / "temp"
    outside.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(outside))
    assert pr.fallback_root(fixture_repo) == outside.resolve()


def test_the_help_explains_where_the_issue_text_is_kept(capsys) -> None:
    """Akzeptanzkriterium: Die Hilfe nennt Speicherort und Wiederanlauf."""
    with pytest.raises(SystemExit):
        pr.main(["--help"])
    # argparse bricht die Hilfe auf die Terminalbreite um.
    help_text = " ".join(capsys.readouterr().out.split())
    assert "temporäre Datei" in help_text and "Wiederanlauf" in help_text
    assert "Wiederanlaufbefehl" in help_text


def test_the_runbook_describes_the_resume_after_a_github_error() -> None:
    """Akzeptanzkriterium: Schritt 1 nennt Speicherort und Wiederanlauf."""
    runbook = (ROOT / "docs" / "RELEASE_PROCESS.md").read_text("utf-8")
    step_one = runbook.split("### 1. Release vorbereiten", 1)[1].split("### 2. ", 1)[0]
    # "Wiederanlauf" allein trägt nicht: das Wort steht ohnehin in der
    # Fehlerzeile jedes Schritts.
    assert "Wiederanlaufbefehl" in step_one
    assert "gh issue create" in step_one
    # Speicherort: beide Fälle – gewählter Pfad und temporäre Ablage.
    assert "--issue-output" in step_one and "temporär" in step_one


def test_an_appstream_entry_that_is_not_first_is_moved_to_the_front() -> None:
    """Das Gate liest den **ersten** ``<release>`` – in place zu aktualisieren genügt nicht."""
    import xml.etree.ElementTree as ET

    original = (ROOT / pr.APPSTREAM_PATH).read_text("utf-8")
    entry = '    <release version="9.9.9" date="2026-09-15"/>\n'
    # Eintrag existiert, steht aber an dritter Stelle.
    releases = list(re.finditer(r'(?m)^[ \t]*<release [^\n]*\n', original))
    mangled = original[: releases[2].start()] + entry + original[releases[2].start() :]

    updated = pr.insert_appstream_release(mangled, "9.9.9", "2026-09-15")
    parsed = ET.fromstring(updated).findall("releases/release")
    assert parsed[0].get("version") == "9.9.9"
    assert [r.get("version") for r in parsed].count("9.9.9") == 1
