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

AUTOMATION = ROOT / "docs" / "RELEASE_AUTOMATION.md"


def _automation_section(number: str) -> str:
    """Text eines ``## <number>.``-Abschnitts bis zur nächsten gleichen Ebene."""
    text = AUTOMATION.read_text(encoding="utf-8")
    head = re.search(rf"(?m)^## {re.escape(number)}\. ", text)
    assert head is not None, f"Abschnitt {number} fehlt in RELEASE_AUTOMATION.md"
    rest = text[head.start() :]
    following = re.search(r"(?m)^## ", rest[1:])
    return rest[: following.start() + 1] if following else rest


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
    """Schreibrechte nur dort, wo tatsächlich geschrieben wird (HB-STUFE-08).

    Der Heartbeat trägt **kein** ``actions: write`` – er bricht nie einen Lauf
    ab, er meldet. Auch die Austragung (#958) kommt ohne aus: Sie ist ein
    Label am Betriebs-Issue und braucht nur ``issues: write``, dasselbe Recht
    wie der Kommentar (der Variablen-Entwurf scheiterte daran, dass
    ``GITHUB_TOKEN`` keine Repository-Variable setzen kann; Review PR #981).
    """
    doc = _load(HEARTBEAT)
    assert doc["permissions"] == {"contents": "read"}
    text = _text()
    assert "contents: write" not in text
    assert "actions: write" not in text, (
        "der Heartbeat bricht nie einen Lauf ab – er meldet nur"
    )
    jobs = _jobs(HEARTBEAT)
    assert jobs["watch"]["permissions"]["actions"] == "read"
    assert jobs["status"]["permissions"] == {"contents": "read", "issues": "read"}
    commenting = [
        name for name, job in jobs.items()
        if any("gh issue comment" in str(step.get("run", "")) for step in job.get("steps", []))
    ]
    writing = [
        name for name, job in jobs.items()
        if (job.get("permissions") or {}).get("issues") == "write"
    ]
    assert commenting == writing == ["watch", "retire"], (
        f"issues: write und Kommentarschritt driften auseinander: "
        f"{writing} vs. {commenting}"
    )
    # Kein Job kennt gh variable oder einen Run-Abbruch als Kommando (das
    # Wort "cancelled" in einer Fehlermeldung ist keiner).
    for name, job in jobs.items():
        body = " ".join(str(step.get("run", "")) for step in job.get("steps", []))
        assert "gh variable" not in body, name
        assert not re.search(r"\bgh run\b|\bgh api\b[^\n]*cancel", body), name


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


def test_both_deadlines_agree_across_code_workflow_and_docs() -> None:
    """#921-Nachprüfung: **eine** Aussage über die Fristen, nicht drei.

    Vorher versprach die Doku „binnen 15 Minuten", der Workflow übergab ein
    Gesamtfenster von 1500 s, und die Fehlermeldung sagte „wartet nach
    1500 s". Alle drei beschrieben dieselbe Sache verschieden — die Art
    Drift, gegen die diese Datei sonst Wächter stellt.
    """
    acceptance = int(heartbeat.DEFAULT_ACCEPTANCE_S)
    deadline = int(heartbeat.DEFAULT_DEADLINE_S)
    # Eine Annahmefrist jenseits des Gesamtfensters wäre wirkungslos.
    assert acceptance < deadline, (acceptance, deadline)

    # 1. Der Workflow übergibt genau diese Werte – sichtbar im Joblog.
    body = HEARTBEAT.read_text(encoding="utf-8")
    assert f"--acceptance-seconds {acceptance}" in body
    assert f"--deadline-seconds {deadline}" in body

    # 2. Die Doku nennt beide in Minuten und begründet die Summe.
    section = _automation_section("7")
    assert f"**{acceptance // 60} min** ({acceptance} s)" in section
    assert f"**{deadline // 60} min** ({deadline} s)" in section

    # 3. Das Gesamtfenster deckt Annahme plus das Jobbudget des Readiness-Jobs.
    readiness = [
        int(job["timeout-minutes"]) * 60
        for job in _jobs(HEARTBEAT).values()
        if "abnahme_preflight.py" in " ".join(
            str(step.get("run", "")) for step in job.get("steps", [])
        )
    ]
    assert readiness and deadline >= acceptance + max(readiness), (deadline, readiness)

    # 4. Und die Auswertung selbst hat Zeit, das Fenster auszusitzen.
    watch_budget = int(_jobs(HEARTBEAT)["watch"]["timeout-minutes"]) * 60
    assert watch_budget > deadline, (watch_budget, deadline)


def test_the_offline_case_is_not_claimed_to_be_a_visible_failure() -> None:
    """Der Workflow darf nicht behaupten, was er nicht hält (#921-Nachprüfung).

    Ein Kommentar sagte, der Fehlschlag bleibe „als Fehlschlag sichtbar" —
    tatsächlich beendet der Folgelauf ihn per `cancel-in-progress` als
    `cancelled`, also **ohne** Actions-Fehlermail. Genau deshalb ist der
    Issue-Kommentar Pflicht; die Falschaussage nahm dieser Pflicht ihre
    Begründung.
    """
    body = HEARTBEAT.read_text(encoding="utf-8")
    assert "Fehlschlag bleibt als Fehlschlag sichtbar" not in body
    concurrency = body[body.index("concurrency:") - 900 : body.index("concurrency:")]
    assert "cancelled" in concurrency and "Fehlermail" in concurrency
    assert "RUNNER_HEARTBEAT_ISSUE" in concurrency


def test_every_readiness_job_can_afford_the_runtime_build() -> None:
    """#934/#937-Review: Das Baubudget muss in **jedes** Jobbudget passen.

    Der Preflight wird an zwei Orten gerufen — Abnahme und Heartbeat. Ein
    Budget nur gegen den einen Workflow zu halten wäre genau die Drift, die
    diese Datei sonst maschinell abfängt: Im Heartbeat stünden die zehn
    Minuten heute passend da, aber an nichts gebunden. Reicht das Jobbudget
    nicht, schneidet GitHub den Lauf ab, bevor der benannte Fehler entsteht —
    der Befund wäre ein nacktes „job timed out".
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "abnahme_preflight_budget", ROOT / "scripts" / "abnahme_preflight.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    budgets: dict[str, int] = {}
    for workflow in (HEARTBEAT, ACCEPTANCE):
        for name, job in _jobs(workflow).items():
            steps = " ".join(str(step.get("run", "")) for step in job.get("steps", []))
            if "abnahme_preflight.py" in steps:
                budgets[f"{workflow.name}:{name}"] = int(job["timeout-minutes"])
    # Beide Workflows, drei Plattformen – der pausierte x86_64-Pfad zählt mit,
    # weil sein Budget beim Reaktivieren sonst unbemerkt zu klein wäre.
    assert len(budgets) == 6, budgets
    for job, minutes in budgets.items():
        assert minutes * 60 > module.RUNTIME_BUILD_TIMEOUT_S, (job, minutes)


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


# ── Gestufte Eskalation (#958) ─────────────────────────────────────────

RUNNER_SETUP = ROOT / "docs" / "RUNNER_SETUP.md"
CLAUDE_MD = ROOT / "CLAUDE.md"
PLATFORMS = ("macos-arm64", "linux-arm64", "linux-x86_64")


def _setup_section(number: str) -> str:
    """Text eines ``## <number>.``-Abschnitts von RUNNER_SETUP.md."""
    text = RUNNER_SETUP.read_text(encoding="utf-8")
    head = re.search(rf"(?m)^## {re.escape(number)}\. ", text)
    assert head is not None, f"Abschnitt {number} fehlt in RUNNER_SETUP.md"
    rest = text[head.start() :]
    following = re.search(r"(?m)^## ", rest[1:])
    return rest[: following.start() + 1] if following else rest


def _claude_heartbeat_section() -> str:
    text = CLAUDE_MD.read_text(encoding="utf-8")
    head = text.index("### Runner-Heartbeat und Geräte-Härtung")
    tail = text.index("\n### ", head + 1)
    return text[head:tail]


def _stage_sources() -> dict[str, str]:
    """Alle Kopien der Fristen: Workflow-Argumente und jede Doku-Stelle."""
    return {
        "workflow": _text(),
        "RELEASE_AUTOMATION §6": _automation_section("6"),
        "RELEASE_AUTOMATION §7": _automation_section("7"),
        "RUNNER_SETUP §0": _setup_section("0"),
        "RUNNER_SETUP §4": _setup_section("4"),
        "RUNNER_SETUP §5": _setup_section("5"),
        "CLAUDE.md": _claude_heartbeat_section(),
    }


def stage_drift(
    sources: dict[str, str], *, stages: tuple[int, ...], removal: int,
) -> list[str]:
    """Jede Kopie muss die Zahlen aus dem Skript wörtlich tragen.

    Reine Funktion, damit die Negativkontrolle unten dieselbe Prüfung mit
    einem verfälschten Text füttern kann – ein Wächter, der nie rot war,
    beweist nichts.
    """
    s1, s2, s3 = stages
    required = {
        "workflow": (f"--stage-days {s1} {s2} {s3}", f"--removal-days {removal}"),
        "RELEASE_AUTOMATION §6": (f"entfernt GitHub nach {removal} Tagen automatisch",),
        "RELEASE_AUTOMATION §7": (
            f"| 1 | ≥ {s1} Tage |", f"| 2 | ≥ {s2} Tage |", f"| 3 | ≥ {s3} Tage |",
            f"nach {removal} Tagen ohne Verbindung",
        ),
        "RUNNER_SETUP §0": (f"**mehr als {removal} Tage** nicht verbunden",),
        "RUNNER_SETUP §4": (f"Stufe 3 ({s3} Tage)", "runner-retired:<plattform>:<datum>"),
        "RUNNER_SETUP §5": (
            f"Mehr als {removal} Tage offline, von GitHub entfernt",
            f"ausgetragen (Stufe 3, {s3} Tage)",
        ),
        "CLAUDE.md": (f"{s1}/{s2}/{s3}", f"{removal} Tagen"),
    }
    drift: list[str] = []
    for label, phrases in required.items():
        text = sources[label]
        for phrase in phrases:
            if phrase not in text:
                drift.append(f"{label}: {phrase!r} fehlt")
    return drift


def test_offline_stages_and_removal_days_agree_across_code_workflow_and_docs() -> None:
    """HB-STUFE-01/02: **eine** Aussage über die Fristen, nicht sieben.

    Vor #958 stand GitHubs 14-Tage-Frist an vier handgepflegten Stellen ohne
    Wächter (``grep -rn "14 Tage" tests/`` war leer). Jetzt sind die Konstanten
    im Skript die einzige Quelle; Workflow und jede Doku-Stelle werden
    dagegen gehalten.
    """
    stages = heartbeat.OFFLINE_STAGE_DAYS
    removal = heartbeat.GITHUB_RUNNER_REMOVAL_DAYS
    assert stages == (7, 12, 21), "Owner-Entscheid E3 (#958)"
    assert list(stages) == sorted(set(stages)) and stages[0] > 0
    # Die zweite Warnung liegt vor GitHubs Entfernung, die dritte danach.
    assert stages[1] < removal < stages[2], (stages, removal)
    # Und das Historienfenster reicht bis hinter die letzte Stufe.
    assert stages[-1] < heartbeat.HISTORY_WINDOW_DAYS
    assert HEARTBEAT.name == heartbeat.WORKFLOW_FILE

    assert stage_drift(_stage_sources(), stages=stages, removal=removal) == []


def test_the_stage_guard_turns_red_on_a_drifted_copy() -> None:
    """Negativkontrolle (HB-STUFE-02): ein abweichender Wert in einer Kopie
    schlägt nachweislich an – und nur dort."""
    stages = heartbeat.OFFLINE_STAGE_DAYS
    removal = heartbeat.GITHUB_RUNNER_REMOVAL_DAYS
    sources = _stage_sources()

    drifted = dict(sources)
    drifted["workflow"] = sources["workflow"].replace(
        f"--stage-days {stages[0]} {stages[1]} {stages[2]}", "--stage-days 7 14 21",
    )
    findings = stage_drift(drifted, stages=stages, removal=removal)
    assert findings == [f"workflow: '--stage-days {stages[0]} {stages[1]} {stages[2]}' fehlt"]

    drifted = dict(sources)
    drifted["RUNNER_SETUP §0"] = sources["RUNNER_SETUP §0"].replace(
        f"**mehr als {removal} Tage**", "**mehr als 30 Tage**",
    )
    findings = stage_drift(drifted, stages=stages, removal=removal)
    assert findings == [f"RUNNER_SETUP §0: '**mehr als {removal} Tage** nicht verbunden' fehlt"]

    drifted = dict(sources)
    drifted["RELEASE_AUTOMATION §7"] = sources["RELEASE_AUTOMATION §7"].replace(
        f"| 2 | ≥ {stages[1]} Tage |", "| 2 | ≥ 14 Tage |",
    )
    assert stage_drift(drifted, stages=stages, removal=removal) == [
        f"RELEASE_AUTOMATION §7: '| 2 | ≥ {stages[1]} Tage |' fehlt"
    ]


def test_the_script_renders_deadline_texts_from_the_constants_only() -> None:
    """HB-STUFE-01: kein Stringliteral im Skript trägt eine der Fristen als
    Zahl – die Texte entstehen aus ``OFFLINE_STAGE_DAYS`` und
    ``GITHUB_RUNNER_REMOVAL_DAYS``. Kommentare sind ausgenommen."""
    import io
    import tokenize

    source = (ROOT / "scripts" / "runner_heartbeat.py").read_text(encoding="utf-8")
    numbers = {*heartbeat.OFFLINE_STAGE_DAYS, heartbeat.GITHUB_RUNNER_REMOVAL_DAYS}
    pattern = re.compile(r"\b(" + "|".join(str(n) for n in sorted(numbers)) + r")[ -]Tage")
    offenders = [
        f"Zeile {token.start[0]}: {token.string[:60]!r}"
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.STRING and pattern.search(token.string)
    ]
    assert offenders == [], offenders


def test_retired_platforms_are_skipped_and_not_expected() -> None:
    """HB-STUFE-07: Nach Stufe 3 erwartet der Heartbeat die Plattform nicht mehr.

    Der Bestand kommt aus den Labels des Betriebs-Issues (``retired-status``
    im Job ``status``, ``issues: read``). Beide Hälften müssen passen: Der
    Runner-Job wird über den Output übersprungen, **und** die Auswertung
    bekommt denselben Wert – sonst meldete sie täglich einen Ausfall, den es
    nicht gibt (Muster x86_64).
    """
    jobs = _jobs(HEARTBEAT)
    status = jobs["status"]
    status_body = " ".join(str(step.get("run", "")) for step in status["steps"])
    assert "scripts/runner_heartbeat.py retired-status" in status_body
    assert "RUNNER_HEARTBEAT_ISSUE" in str(status["steps"])
    by_platform = {
        "macos-arm64": "heartbeat-macos-arm64",
        "linux-arm64": "heartbeat-linux-arm64",
        "linux-x86_64": "heartbeat-linux-x86_64",
    }
    watch_body = " ".join(str(step.get("run", "")) for step in jobs["watch"]["steps"])
    watch_env = str(next(s for s in jobs["watch"]["steps"] if s.get("id") == "watch")["env"])
    for platform, job_id in by_platform.items():
        output = heartbeat.retired_output_name(platform)
        assert output in status["outputs"], output
        assert f"needs.status.outputs.{output} == ''" in str(jobs[job_id]["if"]), (
            platform, jobs[job_id]["if"],
        )
        assert f'--retired-since "{platform}=' in watch_body, platform
        assert f"needs.status.outputs.{output}" in watch_env, platform
    # Kein Rest des Variablen-Entwurfs.
    assert "RETIRED_SINCE" not in _text()


def test_the_retire_job_sets_the_label_before_it_comments() -> None:
    """E2 (automatisch): eigener Job mit ``issues: write`` (und nichts weiter),
    Label erst setzen, dann kommentieren – ein Kommentar darf nie eine
    Austragung behaupten, die nicht stattfand. Plattform, Label und Datum
    kommen aus ``retire.tsv``, das Namensschema wird nicht in der Shell
    nachgebaut."""
    jobs = _jobs(HEARTBEAT)
    retire = jobs["retire"]
    assert retire["needs"] == "watch"
    assert "needs.watch.outputs.retire != ''" in str(retire["if"])
    assert "!cancelled()" in str(retire["if"]), "watch endet bei FAIL mit Exit 1"
    assert retire["runs-on"] == "ubuntu-latest"
    assert retire["permissions"] == {"contents": "read", "issues": "write"}
    uses = [str(step.get("uses", "")) for step in retire["steps"]]
    assert any(u.startswith("actions/download-artifact@") for u in uses)
    body = " ".join(str(step.get("run", "")) for step in retire["steps"])
    assert "heartbeat/retire.tsv" in body
    assert body.index("gh label create") < body.index("gh issue edit") < body.index("gh issue comment")
    assert "--force" in body, "Wiederanlauf am selben Tag legt kein zweites Label an"
    assert "--add-label" in body
    assert "retire-comment-${platform}.md" in body
    assert "runner-retired" not in body, "das Label kommt aus der TSV, nicht aus der Shell"
    # Die Auswertung reicht genau diese beiden Outputs weiter.
    assert set(jobs["watch"]["outputs"]) == {"retire", "comment_issue"}


def test_no_daily_comment_remains_only_stage_comments() -> None:
    """E1: kein Tageskommentar mehr. Der Kommentarschritt der Auswertung
    postet ausschließlich Stufendateien, gesteuert vom Skript-Output, und
    läuft über ``!cancelled()`` – bei FAIL endet der Beobachtungsschritt mit
    Exit 1, und genau dann ist eine Stufe fällig."""
    steps = _jobs(HEARTBEAT)["watch"]["steps"]
    commenting = [step for step in steps if "gh issue comment" in str(step.get("run", ""))]
    assert [step["name"] for step in commenting] == [
        "Stufenkommentar posten", "Simulationskommentar posten",
    ]
    step, simulation = commenting
    assert "!cancelled()" in str(step["if"]) and "stage_comments != ''" in str(step["if"])
    assert "failure()" not in str(step["if"])
    assert "stage-comment-${platform}.md" in step["run"]
    assert "heartbeat.md" not in step["run"], "der Tagesbericht wird nicht mehr gepostet"
    assert "--body-file" in step["run"]
    # Die Simulation (Review PR #981) laeuft zusaetzlich, mit eigenem Ziel und
    # eigenen Dateien – sie verdraengt die echte Eskalation nicht.
    assert "simulation_comments != ''" in str(simulation["if"])
    assert "simulation-comment-${platform}.md" in simulation["run"]
    assert "steps.watch.outputs.simulation_issue" in str(simulation["env"].values())
    assert "COMMENT_ISSUE" not in simulation["run"]
    # Die Erwähnung des Owners – der Mailweg – kommt aus dem Repository-Kontext.
    watch = next(s for s in steps if s.get("id") == "watch")
    assert '--mention "$GITHUB_REPOSITORY_OWNER"' in watch["run"]
    assert '--issue "$TARGET_ISSUE"' in watch["run"]


def test_simulation_inputs_reach_the_script_together() -> None:
    """HB-STUFE-05: Die drei Dispatch-Eingaben gehen gemeinsam ans Skript, das
    ihre Kopplung prüft (nur gemeinsam wirksam, nie gegen das Betriebs-Issue).
    Die Austragung läuft in der Simulation nie – das Skript schreibt dann
    keine ``retire.tsv``, und ohne ``retire``-Output startet der Job nicht."""
    doc = _load(HEARTBEAT)
    triggers = doc[True] if True in doc else doc["on"]
    inputs = triggers["workflow_dispatch"]["inputs"]
    assert set(inputs) == {"simulate_offline_since", "simulate_target_issue", "simulate_platform"}
    assert inputs["simulate_offline_since"]["default"] == ""
    assert inputs["simulate_target_issue"]["default"] == ""
    assert set(inputs["simulate_platform"]["options"]) == set(PLATFORMS)
    watch = next(s for s in _jobs(HEARTBEAT)["watch"]["steps"] if s.get("id") == "watch")
    for flag in ("--simulate-offline-since", "--simulate-target-issue", "--simulate-platform"):
        assert flag in watch["run"], flag
    for name in ("SIMULATE_OFFLINE_SINCE", "SIMULATE_TARGET_ISSUE", "SIMULATE_PLATFORM"):
        assert name in watch["env"], name
