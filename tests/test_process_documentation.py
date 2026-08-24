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
    ``required_status_checks.strict == true`` und null erforderliche
    Approvals. Die Konversationsauflösungs-Pflicht ist mit der
    Reviewschleifen-Entschärfung (ADR-2026-reviewschleifen-entschaerfung)
    aus der Branch Protection entfernt; der Snapshot muss diesen Soll-Stand
    ausdrücklich benennen, statt die alte Sperre weiter zu behaupten – und
    Tabelle wie Diagramm dürfen den `strict`-Mergepfad nicht verlieren.
    """
    snapshot = _process_documentation()
    row = _branch_protection_row(snapshot)
    required_row_phrases = (
        "Branch muss aktuell zu `main` sein (`strict`)",
        "Review-Konversationen sind keine Merge-Sperre",
        "kein formales Approval erforderlich",
        "für Admins nicht erzwungen",
    )
    missing = [phrase for phrase in required_row_phrases if phrase not in row]
    assert not missing, f"Branch-Protection-Snapshot unvollständig: {missing}"
    assert "müssen aufgelöst sein" not in row, (
        "Die entfernte Konversationsauflösungs-Pflicht steht wieder als "
        "Merge-Sperre im Snapshot"
    )

    assert 'RQ3{"Branch aktuell zu main?"}' in snapshot
    assert "RQ3 -->|\"nein\"| F4 --> R1" in snapshot


def test_review_workflow_runs_once_per_pr_not_per_push() -> None:
    """Der Ein-Review-Trigger der Reviewschleifen-Entschärfung darf nicht driften.

    Sechs Doku-Stellen (CLAUDE.md, CONTRIBUTING.md, PROZESSE_UML.md, die
    agents-README und die Köpfe beider Claude-Workflows) beschreiben „einmal
    je PR-Start statt je Push, Wiederholung nur per Label ``re-review``,
    Doku-Pfade ausgenommen". Die einzige Quelle der Wahrheit ist der
    Trigger-Block von ``claude-code-review.yml`` – ohne diesen Wächter würde
    ein wieder ergänztes ``synchronize`` alle sechs Stellen still falsch
    machen und ``make check`` bliebe grün (Review-Befund auf PR #857).
    Textbasiert statt über PyYAML, aus demselben Grund wie der
    workflow_run-Wächter unten.
    """
    text = (_ROOT / ".github/workflows/claude-code-review.yml").read_text(encoding="utf-8")
    trigger = re.search(r"(?ms)^on:\n.*?(?=^\S)", text)
    assert trigger, "Trigger-Block in claude-code-review.yml nicht gefunden"
    block = trigger.group(0)
    assert block.count("types:") == 1, "Trigger-Block führt nicht genau eine types-Liste"
    assert re.search(r"(?m)^    types: \[opened, ready_for_review, labeled\]$", block), (
        "Der Ein-Review-Trigger (opened/ready_for_review/labeled) ist verändert – "
        "sechs Doku-Stellen behaupten ihn weiterhin"
    )
    assert "paths-ignore:" in block, (
        "Die Doku-Pfad-Ausnahme (paths-ignore) fehlt im Trigger-Block"
    )
    job_if = re.search(r"(?ms)^    if: >-\n(?P<body>(?:^      .*\n)+)", text)
    assert job_if, "Job-if des Review-Jobs nicht gefunden"
    body = job_if.group("body")
    for condition in (
        "github.event.pull_request.state == 'open'",
        "github.event.pull_request.draft == false",
        "github.event.label.name == 're-review'",
    ):
        assert condition in body, f"Job-if verliert die Bedingung {condition!r}"


def test_workflow_run_sources_are_documented_at_all_three_places() -> None:
    """Die dokumentierte workflow_run-Quellliste darf nicht vom Workflow driften.

    Der workflow_run-Einstieg von recommendations-live-check.yml steht in
    drei Doku-Stellen (PROZESSE_UML.md, TESTING.md, CLAUDE.md). Die
    Anzeigenamen aus dem Trigger werden über das ``name:``-Feld der
    Workflow-Dateien auf Dateinamen abgebildet; jede Doku-Stelle muss alle
    Quellworkflows im Umfeld ihrer ``workflow_run``-Erwähnung nennen
    (Muster wie N6/gl_smoke: Listenkopie ohne Abgleich driftet still).

    PyYAML ist keine deklarierte Projekt-Abhängigkeit (auch nicht in den
    Constraints); ohne PyYAML läuft deshalb ein textbasierter Rückfall
    (Muster aus test_release_gate: textbasierte Invarianten laufen immer),
    damit dieser Wächter im ``.[test]``-Env nie still übersprungen wird.
    """
    workflow_dir = _ROOT / ".github" / "workflows"
    workflow_files = sorted(workflow_dir.glob("*.yml")) + sorted(workflow_dir.glob("*.yaml"))
    trigger_text = (workflow_dir / "recommendations-live-check.yml").read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:
        yaml = None

    by_name: dict[str, list[str]] = {}
    if yaml is not None:
        trigger_doc = yaml.safe_load(trigger_text)
        # PyYAML (YAML 1.1) liest den Schlüssel ``on:`` als ``True``; ein
        # quotiertes ``"on":`` bliebe ein String. Die ``get``-Kette (Idiom aus
        # test_release_gate) lässt jeden Driftfall am ``assert`` mit seiner
        # Aussage enden statt an einem nackten ``KeyError``.
        triggers = trigger_doc.get(True, trigger_doc.get("on")) or {}
        display_names = (triggers.get("workflow_run") or {}).get("workflows") or []
        # Einmalige Namenstabelle statt erneutem Parsen je Anzeigename; die
        # Parsebarkeit sichert bereits tests/test_ci_workflow_yaml.py.
        for path in workflow_files:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(doc, dict) and isinstance(doc.get("name"), str):
                by_name.setdefault(doc["name"], []).append(path.name)
    else:
        # Rückfall bewusst nur für die heutige Inline-Flow-/Quoting-
        # Schreibweise: Eine Umformung fällt hier fail-closed als fehlender
        # Trigger auf, statt den Wächter still zu überspringen.
        block = re.search(
            r"(?ms)^  workflow_run:\n\s*workflows:\s*\[(?P<names>[^\]]*)\]",
            trigger_text,
        )
        assert block, "workflow_run-Trigger in recommendations-live-check.yml nicht gefunden"
        display_names = re.findall(r"""["']([^"']+)["']""", block.group("names"))
        for path in workflow_files:
            name_match = re.search(
                r"""(?m)^name:\s*["']?(?P<name>[^"'\n]+?)["']?\s*$""",
                path.read_text(encoding="utf-8"),
            )
            if name_match:
                by_name.setdefault(name_match.group("name"), []).append(path.name)
    assert display_names, "workflow_run-Trigger ohne Workflow-Namen"

    filenames = []
    for display in display_names:
        matches = by_name.get(display, [])
        # Der leere Fall ist der wertvollste Fund: Der Anzeigename passt auf
        # kein name:-Feld mehr, der Trigger feuert also nie wieder.
        assert matches, (
            f"Anzeigename {display!r} passt auf kein name:-Feld mehr – "
            "der workflow_run-Einstieg würde nie wieder feuern"
        )
        assert len(matches) == 1, (
            f"Anzeigename {display!r} nicht eindeutig auflösbar: {matches}"
        )
        filenames.append(matches[0])

    # Mengenvergleich statt Teilmengenprüfung: So fällt auch ein aus dem
    # Trigger ENTFERNTER Quellworkflow auf, den die Doku noch behauptet.
    # Verglichen wird je Doku-Stelle der Aufzählungspunkt/Absatz um die
    # ``workflow_run``-Erwähnung; die Doku ist damit bewusst an die
    # Backtick-Schreibweise der Workflow-Dateinamen gebunden. Der
    # Trigger-Workflow selbst zählt nicht als Quelle. Der GANZE Punkt zählt:
    # Auch ein dort ergänzter, unbeteiligter Workflow-Verweis macht den Test
    # rot – bewusst fail-closed; die Meldung stellt beide Mengen gegenüber.
    expected = set(filenames)
    for doc in ("docs/PROZESSE_UML.md", "TESTING.md", "CLAUDE.md"):
        text = (_ROOT / doc).read_text(encoding="utf-8")
        anchors = [match.start() for match in re.finditer(r"`workflow_run`", text)]
        assert anchors, f"{doc} erwähnt den workflow_run-Einstieg nicht"
        segments = []
        for anchor in anchors:
            start = max(text.rfind("\n- ", 0, anchor), text.rfind("\n\n", 0, anchor), 0)
            ends = [
                pos
                for pos in (text.find("\n- ", anchor), text.find("\n\n", anchor))
                if pos != -1
            ]
            segment = text[start : min(ends) if ends else len(text)]
            mentioned = {
                name
                for name in re.findall(r"`([A-Za-z0-9_.-]+\.ya?ml)`", segment)
                if (workflow_dir / name).is_file()
            }
            mentioned.discard("recommendations-live-check.yml")
            segments.append(mentioned)
        # ``all`` statt ``any``: Jede Erwähnung muss zum Trigger passen –
        # sonst könnte eine später ergänzte, driftende Zweitnennung hinter
        # einer noch passenden Erstnennung verschwinden. Die Segmentgrenzen
        # kennen nur Top-Level-Aufzählungspunkte; ein verschachtelter Punkt
        # fiele auf den Elternpunkt zurück und schlüge fail-closed an.
        assert all(mentioned == expected for mentioned in segments), (
            f"workflow_run-Quellworkflows in {doc} decken sich nicht mit dem "
            f"Trigger: erwartet {sorted(expected)}, gefunden {[sorted(m) for m in segments]}"
        )
