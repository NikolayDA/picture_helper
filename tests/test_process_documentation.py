"""Drift-Schutz zwischen Prozessdokumentation und versionierten Workflows."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

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

    ``yaml`` ist keine deklarierte Projekt-Abhängigkeit, aber im Test-Env
    vorhanden – fehlt es, wird nur dieser Test übersprungen.
    """
    yaml = pytest.importorskip("yaml")
    workflow_dir = _ROOT / ".github" / "workflows"
    workflow_files = sorted(workflow_dir.glob("*.yml")) + sorted(workflow_dir.glob("*.yaml"))
    trigger_doc = yaml.safe_load(
        (workflow_dir / "recommendations-live-check.yml").read_text(encoding="utf-8")
    )
    # PyYAML (YAML 1.1) liest den Schlüssel ``on:`` als ``True``; ein
    # quotiertes ``"on":`` bliebe ein String. Die ``get``-Kette (Idiom aus
    # test_release_gate) lässt jeden Driftfall am ``assert`` mit seiner
    # Aussage enden statt an einem nackten ``KeyError``.
    triggers = trigger_doc.get(True, trigger_doc.get("on")) or {}
    display_names = (triggers.get("workflow_run") or {}).get("workflows") or []
    assert display_names, "workflow_run-Trigger ohne Workflow-Namen"

    # Einmalige Namenstabelle statt erneutem Parsen je Anzeigename; die
    # Parsebarkeit der Dateien sichert bereits tests/test_ci_workflow_yaml.py.
    by_name: dict[str, list[str]] = {}
    for path in workflow_files:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(doc, dict) and isinstance(doc.get("name"), str):
            by_name.setdefault(doc["name"], []).append(path.name)

    filenames = []
    for display in display_names:
        matches = by_name.get(display, [])
        assert len(matches) == 1, (
            f"Anzeigename {display!r} nicht eindeutig auflösbar: {matches}"
        )
        filenames.append(matches[0])

    # Mengenvergleich statt Teilmengenprüfung: So fällt auch ein aus dem
    # Trigger ENTFERNTER Quellworkflow auf, den die Doku noch behauptet.
    # Verglichen wird je Doku-Stelle der Aufzählungspunkt/Absatz um die
    # ``workflow_run``-Erwähnung; die Doku ist damit bewusst an die
    # Backtick-Schreibweise der Workflow-Dateinamen gebunden. Der
    # Trigger-Workflow selbst zählt nicht als Quelle.
    expected = set(filenames)
    for doc in ("docs/PROZESSE_UML.md", "TESTING.md", "CLAUDE.md"):
        text = (_ROOT / doc).read_text(encoding="utf-8")
        anchors = [match.start() for match in re.finditer(r"`workflow_run`", text)]
        assert anchors, f"{doc} erwähnt den workflow_run-Einstieg nicht"
        segments = []
        for anchor in anchors:
            start = max(text.rfind("\n- ", 0, anchor), text.rfind("\n\n", 0, anchor), 0)
            ends = [pos for pos in (text.find("\n- ", anchor), text.find("\n\n", anchor)) if pos != -1]
            segment = text[start : min(ends) if ends else len(text)]
            mentioned = {
                name
                for name in re.findall(r"`([A-Za-z0-9_.-]+\.ya?ml)`", segment)
                if (workflow_dir / name).is_file()
            }
            mentioned.discard("recommendations-live-check.yml")
            segments.append(mentioned)
        assert any(mentioned == expected for mentioned in segments), (
            f"workflow_run-Quellworkflows in {doc} decken sich nicht mit dem "
            f"Trigger: erwartet {sorted(expected)}, gefunden {[sorted(m) for m in segments]}"
        )
