"""Drift-Schutz zwischen Prozessdokumentation und versionierten Workflows."""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def _process_documentation() -> str:
    return (_ROOT / "docs/PROZESSE_UML.md").read_text(encoding="utf-8")


def _branch_protection_row(snapshot: str) -> str:
    match = re.search(
        r"(?m)^\|\s*Branch Protection für `main`\s*\|(?P<body>.*?)\|\s*$",
        snapshot,
    )
    assert match, "Snapshot-Zeile für Branch Protection nicht gefunden"
    return match.group("body")


def test_required_status_name_matches_pr_ci_job() -> None:
    """Der dokumentierte Pflichtstatus muss der exakte PR-CI-Jobname bleiben."""
    workflow = (_ROOT / ".github/workflows/pr-ci.yml").read_text(encoding="utf-8")
    snapshot = _process_documentation()

    job_block = re.search(
        r"(?ms)^  pr-check:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", workflow
    )
    assert job_block, "Job pr-check in pr-ci.yml nicht gefunden"
    job_name_match = re.search(
        r"(?m)^    name:\s*(?P<name>[^#\n]+?)\s*$", job_block.group("body")
    )
    assert job_name_match, "Jobname von pr-check in pr-ci.yml nicht gefunden"
    job_name = job_name_match.group("name")

    assert job_name == "Lightweight PR checks", (
        "Der versionierte PR-CI-Jobname weicht vom live geprüften Pflichtstatus ab: "
        f"{job_name!r}"
    )
    assert f"`{job_name}`" in _branch_protection_row(snapshot), (
        "Der PR-CI-Jobname fehlt in der Branch-Protection-Snapshot-Zeile: "
        f"{job_name!r}"
    )


def test_branch_protection_snapshot_covers_all_live_merge_gates() -> None:
    """Der manuelle Live-Snapshot darf nicht nur den Status-Check kopieren.

    Der authentifizierte Abgleich vom 23.08.2026 ergab zusätzlich
    ``required_status_checks.strict == true``, aufzulösende Konversationen
    und null erforderliche Approvals. Diese Regeln ändern den tatsächlichen
    Mergepfad und müssen deshalb in Tabelle und Diagramm sichtbar bleiben.
    """
    snapshot = _process_documentation()
    row = _branch_protection_row(snapshot)
    required_row_phrases = (
        "Branch muss aktuell zu `main` sein (`strict`)",
        "alle Review-Konversationen müssen aufgelöst sein",
        "kein formales Approval erforderlich",
        "für Admins nicht erzwungen",
    )
    missing = [phrase for phrase in required_row_phrases if phrase not in row]
    assert not missing, f"Branch-Protection-Snapshot unvollständig: {missing}"

    assert "Branch aktuell zu main<br/>und alle Review-Konversationen aufgelöst?" in snapshot
    assert "RQ3 -->|\"nein\"| F4 --> R1" in snapshot


def test_workflow_run_sources_are_documented_at_all_three_places() -> None:
    """Die dokumentierte workflow_run-Quellliste darf nicht vom Workflow driften.

    Der workflow_run-Einstieg von recommendations-live-check.yml steht in
    drei Doku-Stellen (PROZESSE_UML.md, TESTING.md, CLAUDE.md). Die
    Anzeigenamen aus dem Trigger werden über das ``name:``-Feld der
    Workflow-Dateien auf Dateinamen abgebildet; jede Doku-Stelle muss alle
    Quellworkflows im Umfeld ihrer ``workflow_run``-Erwähnung nennen
    (Muster wie N6/gl_smoke: Listenkopie ohne Abgleich driftet still).
    """
    workflow_dir = _ROOT / ".github/workflows"
    trigger = (workflow_dir / "recommendations-live-check.yml").read_text(encoding="utf-8")
    block = re.search(
        r"(?ms)^  workflow_run:\n\s*workflows:\s*\[(?P<names>[^\]]*)\]", trigger
    )
    assert block, "workflow_run-Trigger in recommendations-live-check.yml nicht gefunden"
    display_names = re.findall(r'"([^"]+)"', block.group("names"))
    assert display_names, "workflow_run-Trigger ohne Workflow-Namen"

    filenames = []
    for display in display_names:
        matches = [
            path.name
            for path in sorted(workflow_dir.glob("*.yml"))
            if re.search(
                rf"(?m)^name:\s*{re.escape(display)}\s*$",
                path.read_text(encoding="utf-8"),
            )
        ]
        assert len(matches) == 1, (
            f"Anzeigename {display!r} nicht eindeutig auflösbar: {matches}"
        )
        filenames.append(matches[0])

    window = 600
    for doc in ("docs/PROZESSE_UML.md", "TESTING.md", "CLAUDE.md"):
        text = (_ROOT / doc).read_text(encoding="utf-8")
        anchors = [match.start() for match in re.finditer(r"`workflow_run`", text)]
        assert anchors, f"{doc} erwähnt den workflow_run-Einstieg nicht"
        covered = any(
            all(
                f"`{filename}`" in text[max(0, anchor - window) : anchor + window]
                for filename in filenames
            )
            for anchor in anchors
        )
        assert covered, (
            f"workflow_run-Quellworkflows fehlen im Umfeld der Erwähnung in {doc}: "
            f"{filenames}"
        )
