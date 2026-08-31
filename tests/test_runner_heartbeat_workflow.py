"""Governance des Runner-Heartbeats und der Self-hosted-Exklusivität (#921).

Bis #921 stand die Regel „nur der Abnahme-Workflow spricht Self-hosted-Labels
an" ausschließlich als Häkchen in ``docs/RELEASE_AUTOMATION.md`` §3 – kein
Test hat sie erzwungen. Der Heartbeat erweitert die Regel bewusst um genau
einen zweiten Workflow; dieselbe Erweiterung macht sie hier erstmals
maschinell prüfbar. Ein dritter Workflow mit Self-hosted-Labels fällt damit
auf, statt still dazuzukommen.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = ROOT / ".github" / "workflows"
HEARTBEAT = WORKFLOW_DIR / "runner-heartbeat.yml"
ACCEPTANCE = WORKFLOW_DIR / "release-abnahme.yml"

# Genau diese Workflows dürfen Self-hosted-Runner beschäftigen. Jede
# Erweiterung ist eine bewusste Entscheidung mit denselben Schutzbedingungen
# (dispatch-/schedule-only, minimale Permissions, Checkout ohne Credentials).
SELF_HOSTED_WORKFLOWS = {"release-abnahme.yml", "runner-heartbeat.yml"}

_SPEC = importlib.util.spec_from_file_location(
    "runner_heartbeat", ROOT / "scripts" / "runner_heartbeat.py"
)
assert _SPEC is not None and _SPEC.loader is not None
heartbeat = importlib.util.module_from_spec(_SPEC)
sys.modules["runner_heartbeat"] = heartbeat
_SPEC.loader.exec_module(heartbeat)


def _workflow_files(directory: Path = WORKFLOW_DIR) -> list[Path]:
    """Alle Workflow-Dateien – GitHub erkennt ``.yml`` **und** ``.yaml``.

    Nur ``*.yml`` zu scannen hiesse, dass ein als ``.yaml`` angelegter dritter
    Workflow die Exklusivitaetsregel unbemerkt umginge (Codex-Review PR #930).
    """
    return sorted(
        path for pattern in ("*.yml", "*.yaml") for path in directory.glob(pattern)
    )


def test_the_scan_covers_both_workflow_extensions(tmp_path: Path) -> None:
    """Wächter über den Wächter, an einem echten Verzeichnis geprüft.

    Die erste Fassung dieses Tests verglich die gefundenen Endungen mit ihrer
    eigenen Sollmenge **vereinigt** – und war damit immer wahr. Hier fällt ein
    auf ``*.yml`` verengter Glob tatsächlich auf.
    """
    (tmp_path / "a.yml").write_text("x", encoding="utf-8")
    (tmp_path / "b.yaml").write_text("x", encoding="utf-8")
    (tmp_path / "c.txt").write_text("x", encoding="utf-8")
    assert {path.name for path in _workflow_files(tmp_path)} == {"a.yml", "b.yaml"}


def _text() -> str:
    return HEARTBEAT.read_text(encoding="utf-8")


def _load(path: Path) -> dict:
    yaml = pytest.importorskip("yaml")
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


def _jobs(path: Path) -> dict:
    jobs = _load(path)["jobs"]
    assert isinstance(jobs, dict) and jobs
    return jobs


def _self_hosted_jobs(path: Path) -> dict:
    return {
        name: job for name, job in _jobs(path).items()
        if "self-hosted" in (job.get("runs-on") or [])
    }


# ── Exklusivität über alle Workflows ───────────────────────────────────

def test_only_the_declared_workflows_address_self_hosted_runners() -> None:
    """Die erweiterte §3-Regel, erstmals als Test statt als Häkchen.

    Ein Workflow mit Self-hosted-Labels bringt Code auf fremde Hardware. Wer
    einen dritten hinzufügt, muss diese Liste bewusst ändern – und stößt
    dabei auf die Schutzbedingungen unten.
    """
    using = {
        path.name for path in _workflow_files()
        if "self-hosted" in path.read_text(encoding="utf-8")
    }
    assert using == SELF_HOSTED_WORKFLOWS, (
        f"unerwartet: {sorted(using - SELF_HOSTED_WORKFLOWS)} zu viel, "
        f"{sorted(SELF_HOSTED_WORKFLOWS - using)} fehlt"
    )


@pytest.mark.parametrize("name", sorted(SELF_HOSTED_WORKFLOWS))
def test_every_self_hosted_workflow_keeps_foreign_code_off_the_runners(name: str) -> None:
    """Kein Push-, PR- oder Fork-Trigger – für **beide** erlaubten Workflows."""
    text = (WORKFLOW_DIR / name).read_text(encoding="utf-8")
    for forbidden in ("\n  push:", "\n  pull_request:", "pull_request_target"):
        assert forbidden not in text, f"{name}: unerlaubter Trigger {forbidden!r}"


@pytest.mark.parametrize("name", sorted(SELF_HOSTED_WORKFLOWS))
def test_self_hosted_jobs_check_out_without_persisting_credentials(name: str) -> None:
    """Kein Git-Token bleibt auf fremder Hardware liegen."""
    path = WORKFLOW_DIR / name
    jobs = _self_hosted_jobs(path)
    assert jobs, f"{name}: kein Self-hosted-Job gefunden"
    for job_name, job in jobs.items():
        for step in job.get("steps", []):
            uses = str(step.get("uses", ""))
            if uses.startswith("actions/checkout"):
                assert step.get("with", {}).get("persist-credentials") is False, (
                    f"{name}/{job_name}: checkout ohne persist-credentials: false"
                )


# ── Heartbeat-spezifische Schutzbedingungen ────────────────────────────

def test_heartbeat_runs_on_a_schedule_and_on_demand_only() -> None:
    doc = _load(HEARTBEAT)
    triggers = doc[True] if True in doc else doc["on"]
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    # Täglich – ein wöchentlicher Takt liesse einen Ausfall bis zu sieben Tage
    # unentdeckt und verfehlte das Ziel aus #921 ("binnen eines Tages").
    (schedule,) = triggers["schedule"]
    minute, hour, day_of_month, month, day_of_week = schedule["cron"].split()
    assert (day_of_month, month, day_of_week) == ("*", "*", "*"), schedule["cron"]


def test_heartbeat_is_least_privilege() -> None:
    """Schreibrechte nur dort, wo tatsächlich geschrieben wird."""
    doc = _load(HEARTBEAT)
    assert doc["permissions"] == {"contents": "read"}
    text = _text()
    assert "contents: write" not in text
    assert "actions: write" not in text, (
        "der Heartbeat bricht nie einen Lauf ab – er meldet nur"
    )
    commenting = [
        name for name, job in _jobs(HEARTBEAT).items()
        if any("gh issue comment" in str(step.get("run", "")) for step in job.get("steps", []))
    ]
    writing = [
        name for name, job in _jobs(HEARTBEAT).items()
        if (job.get("permissions") or {}).get("issues") == "write"
    ]
    assert commenting == writing, (
        f"issues: write und Kommentarschritt driften auseinander: "
        f"{writing} vs. {commenting}"
    )


def test_every_self_hosted_heartbeat_job_is_gated_and_bounded() -> None:
    """Pause-Gate und Zeitgrenze auf jedem Runner-Job."""
    jobs = _self_hosted_jobs(HEARTBEAT)
    assert set(jobs) == {
        "heartbeat-macos-arm64", "heartbeat-linux-arm64", "heartbeat-linux-x86_64",
    }
    for name, job in jobs.items():
        assert "needs.status.outputs.paused != 'true'" in str(job.get("if", "")), name
        assert job.get("timeout-minutes"), name
        assert job.get("needs") == "status", name


def test_paused_x86_64_platform_is_not_expected_daily() -> None:
    """Ein nicht registrierter Runner darf keinen täglichen Fehlalarm erzeugen."""
    job = _jobs(HEARTBEAT)["heartbeat-linux-x86_64"]
    assert "vars.ABNAHME_X86_64_ENABLED == 'true'" in str(job["if"])
    # Dieselbe Bedingung muss auch die Auswertung kennen, sonst erwartete sie
    # einen Job, den der Workflow gar nicht erzeugt.
    watch = _jobs(HEARTBEAT)["watch"]
    body = " ".join(str(step.get("run", "")) for step in watch["steps"])
    assert "--x86-64-enabled" in body


def test_watch_job_observes_in_parallel_instead_of_waiting_for_the_runners() -> None:
    """``needs`` auf die Runner-Jobs würde die Meldung genauso lange blockieren,
    wie sie melden soll – ein Monitor darf nicht auf sein Messobjekt warten."""
    watch = _jobs(HEARTBEAT)["watch"]
    assert watch["needs"] == "status"
    assert watch["runs-on"] == "ubuntu-latest"
    assert watch["permissions"]["actions"] == "read"


def test_a_stale_queued_run_cannot_pile_up() -> None:
    """Bei offline Runner bleibt der Job bis zu 24 h in der Queue.

    Ohne ``cancel-in-progress`` sammelten sich täglich weitere an; der
    Heartbeat bricht bewusst nicht selbst ab (ein force-cancel liesse den Lauf
    als "cancelled" ohne Fehlermeldung enden).
    """
    doc = _load(HEARTBEAT)
    assert doc["concurrency"]["cancel-in-progress"] is True
    assert doc["concurrency"]["group"]


def test_heartbeat_job_names_match_the_watcher_table() -> None:
    """Namensdrift machte die Beobachtung wirkungslos (sie fände nichts)."""
    names = {
        job["name"] for name, job in _self_hosted_jobs(HEARTBEAT).items()
    }
    assert names == set(heartbeat.HEARTBEAT_JOB_NAMES.values())


def test_runner_jobs_execute_only_repository_code() -> None:
    """Auf fremder Hardware läuft nichts Drittes ausser dem Checkout selbst."""
    for name, job in _self_hosted_jobs(HEARTBEAT).items():
        for step in job.get("steps", []):
            uses = str(step.get("uses", ""))
            if uses:
                assert uses.startswith("actions/checkout@"), f"{name}: {uses}"
            run = str(step.get("run", ""))
            if run:
                assert "scripts/" in run, f"{name}: {run!r}"


def test_runner_jobs_run_the_hardening_tier_strictly() -> None:
    """#921: Der tägliche Lauf ist die Durchsetzungsstelle der Geräte-Härtung.

    Im Abnahme-Preflight bleibt sie bewusst ein Hinweis – ein Release soll
    nicht an einer Display-Sleep-Einstellung scheitern.
    """
    for name, job in _self_hosted_jobs(HEARTBEAT).items():
        body = " ".join(str(step.get("run", "")) for step in job["steps"])
        assert "scripts/abnahme_preflight.py" in body, name
        assert "--hardening-strict" in body, name
    acceptance = " ".join(
        str(step.get("run", ""))
        for job in _jobs(ACCEPTANCE).values()
        for step in job.get("steps", [])
    )
    assert "abnahme_preflight.py" in acceptance
    assert "--hardening-strict" not in acceptance


def test_the_notification_channel_is_mandatory_not_optional() -> None:
    """Der Issue-Kommentar ist im Offline-Fall der einzige Kanal, der trägt.

    Bleibt ein Runner-Job in der Warteschlange, ist der **Lauf** nicht
    abgeschlossen – Actions benachrichtigt aber erst beim Laufabschluss, und
    der kommt dann erst am nächsten Tag über `cancel-in-progress`, also als
    „cancelled" und damit ohne Fehlermeldung. Eine optionale Zielvariable
    liesse den Ausfall genau im Zielszenario unbemerkt.
    """
    steps = _jobs(HEARTBEAT)["watch"]["steps"]
    names = [step.get("name") for step in steps]
    check = next(step for step in steps if step.get("name") == "Meldeweg pruefen")
    assert "RUNNER_HEARTBEAT_ISSUE ist nicht gesetzt" in check["run"]
    assert "exit 1" in check["run"]
    # Vor der Messung, damit die Fehlkonfiguration sofort auffällt.
    assert names.index("Meldeweg pruefen") < names.index("Runner-Annahme beobachten")


def test_repository_variables_never_reach_the_shell_as_code() -> None:
    """``${{ vars.… }}`` direkt in einer Kommandozeile wäre Text, kein Wert."""
    for job in _jobs(HEARTBEAT).values():
        for step in job.get("steps", []):
            run = str(step.get("run", ""))
            assert not re.search(r"\$\{\{\s*vars\.", run), run
