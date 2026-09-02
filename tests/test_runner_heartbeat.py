"""Tests des täglichen Runner-Heartbeats (#921, Epic #914).

Der Netzweg ist injiziert, damit Pausenlogik, Queue-Auswertung und die
fail-safe Pfade ohne GitHub prüfbar sind – dasselbe Muster wie beim
Lauf-Watchdog in ``tests/test_abnahme_watchdog.py``.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "runner_heartbeat", ROOT / "scripts" / "runner_heartbeat.py"
)
assert _SPEC is not None and _SPEC.loader is not None
hb = importlib.util.module_from_spec(_SPEC)
sys.modules["runner_heartbeat"] = hb
_SPEC.loader.exec_module(hb)

TODAY = date(2026, 8, 31)
EXPECTED = hb.expected_jobs(x86_enabled=False)


def _jobs(*states: str, names: tuple[str, ...] = EXPECTED) -> list[dict]:
    """Jobliste aus Kurzformen: ``queued``/``running``/``ok``/``fail``/``timeout``.

    strict=False mit Absicht: ein Test gibt bewusst weniger Zustaende als
    Namen an (unvollstaendige Jobliste direkt nach Laufstart).
    """
    shapes = {
        "queued": ("queued", None),
        "running": ("in_progress", None),
        "ok": ("completed", "success"),
        "fail": ("completed", "failure"),
        "timeout": ("completed", "timed_out"),
        "cancelled": ("completed", "cancelled"),
        "stale": ("completed", "stale"),
        "startup": ("completed", "startup_failure"),
        "skipped": ("completed", "skipped"),
        "noconcl": ("completed", None),
    }
    return [
        {"name": name, "status": shapes[state][0], "conclusion": shapes[state][1]}
        for name, state in zip(names, states, strict=False)
    ]


# ── Wartungsfenster ────────────────────────────────────────────────────

def test_an_unset_variable_keeps_the_heartbeat_active() -> None:
    state = hb.pause_state(paused_raw="", until_raw="", today=TODAY)
    assert (state.paused, state.ok) == (False, True)


@pytest.mark.parametrize("raw", ["false", "0", "nein", "yes", " "])
def test_only_an_explicit_true_pauses(raw: str) -> None:
    assert hb.pause_state(paused_raw=raw, until_raw="", today=TODAY).paused is False


@pytest.mark.parametrize("raw", ["true", "TRUE", " True "])
def test_a_dated_window_pauses_without_becoming_a_finding(raw: str) -> None:
    state = hb.pause_state(paused_raw=raw, until_raw="2026-09-05", today=TODAY)
    assert (state.paused, state.ok) == (True, True)
    assert state.until == date(2026, 9, 5)


def test_the_last_day_of_the_window_still_counts() -> None:
    state = hb.pause_state(paused_raw="true", until_raw=TODAY.isoformat(), today=TODAY)
    assert (state.paused, state.ok) == (True, True)


def test_a_pause_without_an_end_is_itself_the_finding() -> None:
    """Sonst bliebe die Überwachung still abgeschaltet – genau der Zustand,
    gegen den #921 antritt (der Pi war tagelang unbemerkt offline)."""
    state = hb.pause_state(paused_raw="true", until_raw="", today=TODAY)
    assert (state.paused, state.ok) == (True, False)
    assert "ohne Ende" in state.detail


def test_an_expired_window_stays_paused_but_turns_the_run_red() -> None:
    """Pausiert bleibt es (kein Fehlalarm im echten Wartungsfall), rot wird es
    trotzdem – eine vergessene Pause fällt so täglich auf."""
    state = hb.pause_state(paused_raw="true", until_raw="2026-08-30", today=TODAY)
    assert (state.paused, state.ok) == (True, False)
    assert "endete am 2026-08-30" in state.detail


def test_an_unparsable_end_date_is_not_silently_ignored() -> None:
    state = hb.pause_state(paused_raw="true", until_raw="naechste Woche", today=TODAY)
    assert (state.paused, state.ok) == (True, False)
    assert "ISO-Datum" in state.detail


def test_pause_status_writes_the_job_output_and_exit_code(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    output = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    code = hb.main([
        "--summary", str(tmp_path / "s.md"),
        "pause-status", "--paused", "true", "--until", "2000-01-01",
        "--today", TODAY.isoformat(),
    ])
    assert code == 1
    assert "paused=true" in output.read_text(encoding="utf-8")
    assert "::error title=Heartbeat-Pause ungueltig::" in capsys.readouterr().out
    assert "PAUSED" in (tmp_path / "s.md").read_text(encoding="utf-8")


# ── Erwartete Jobs ─────────────────────────────────────────────────────

def test_the_paused_platform_is_not_expected() -> None:
    assert hb.expected_jobs(x86_enabled=False) == (
        "Heartbeat macOS arm64", "Heartbeat Linux aarch64",
    )
    assert hb.expected_jobs(x86_enabled=True)[-1] == "Heartbeat Linux x86_64"


def test_queue_state_counts_only_queued_jobs_as_waiting() -> None:
    state = hb.queue_state(_jobs("ok", "queued"), EXPECTED)
    assert state.known == EXPECTED
    assert state.queued == ("Heartbeat Linux aarch64",)


def test_queue_state_ignores_foreign_jobs() -> None:
    jobs = _jobs("ok", "ok") + [{"name": "Heartbeat-Status", "status": "queued"}]
    assert hb.queue_state(jobs, EXPECTED).queued == ()


# ── Beobachtung ────────────────────────────────────────────────────────

def _watch(
    observe, *, ticks: list[float], deadline: float = 1.0, poll: float = 10.0,
    acceptance: float | None = None,
):
    clock = iter(ticks)
    return hb.watch(
        observe, EXPECTED,
        acceptance_s=deadline if acceptance is None else acceptance,
        deadline_s=deadline, poll_s=poll,
        clock=lambda: next(clock), sleep=lambda _s: None,
    )


def test_watch_returns_as_soon_as_every_runner_accepted() -> None:
    state = _watch(lambda: hb.queue_state(_jobs("ok", "ok"), EXPECTED),
                   ticks=[0, 0, 1])
    assert hb.evaluate(state, EXPECTED, acceptance_s=900, deadline_s=900)[0] == hb.VERDICT_PASS


def test_watch_reports_the_runner_that_never_took_the_job() -> None:
    state = _watch(lambda: hb.queue_state(_jobs("ok", "queued"), EXPECTED),
                   ticks=[0, 0, 1, 2])
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=900, deadline_s=900)
    assert verdict == hb.VERDICT_FAIL
    assert "Heartbeat Linux aarch64" in detail


def test_an_incomplete_job_list_does_not_end_the_watch_early() -> None:
    """Direkt nach Laufstart kennt die API noch nicht alle Jobs."""
    seen = {"n": 0}

    def observe():
        seen["n"] += 1
        if seen["n"] == 1:
            return hb.queue_state(_jobs("ok", names=EXPECTED[:1]), EXPECTED)
        return hb.queue_state(_jobs("ok", "ok"), EXPECTED)

    state = _watch(observe, ticks=[0, 0, 0, 1])
    assert seen["n"] == 2
    assert hb.evaluate(state, EXPECTED, acceptance_s=900, deadline_s=900)[0] == hb.VERDICT_PASS


def test_a_monitor_without_observation_raises_no_alarm() -> None:
    """Ein Fehlalarm bei jedem API-Schluckauf entwertet den Alarm."""
    def boom():
        raise OSError("api down")

    state = _watch(boom, ticks=[0, 1, 2])
    assert hb.evaluate(state, EXPECTED, acceptance_s=900, deadline_s=900)[0] == hb.VERDICT_UNOBSERVED


def test_a_stale_queue_observation_never_becomes_a_verdict() -> None:
    """Der Runner kann den Job längst übernommen haben."""
    seen = {"n": 0}

    def flaky():
        seen["n"] += 1
        if seen["n"] == 1:
            return hb.queue_state(_jobs("queued", "queued"), EXPECTED)
        raise OSError("api down")

    # Ein Tick mehr als früher: Ist die Beobachtung zur Annahmefrist veraltet,
    # terminiert sie dort nicht mehr, sondern fällt auf das Gesamtfenster durch
    # (#938-Review) – hier fallen beide zusammen, also unmittelbar.
    state = _watch(flaky, ticks=[0, 0, 100, 200, 200])
    assert state.observed is False
    assert hb.evaluate(state, EXPECTED, acceptance_s=900, deadline_s=900)[0] == hb.VERDICT_UNOBSERVED


def test_missing_expected_jobs_are_reported_without_a_runner_verdict() -> None:
    state = hb.QueueState(known=EXPECTED[:1], queued=(), observed=True)
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=900, deadline_s=900)
    assert verdict == hb.VERDICT_UNOBSERVED
    assert "Heartbeat Linux aarch64" in detail


# ── Bericht und Summary ────────────────────────────────────────────────

def test_report_and_summary_name_the_offline_runner(tmp_path: Path) -> None:
    state = hb.QueueState(known=EXPECTED, queued=("Heartbeat Linux aarch64",))
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=900, deadline_s=900)
    report = hb.build_report(
        verdict=verdict, detail=detail, expected=EXPECTED, state=state,
        acceptance_s=900, deadline_s=900, run_url="https://example.invalid/run/1",
    )
    hb.write_outputs(
        report, report_path=tmp_path / "r.json", summary_path=tmp_path / "s.md",
    )
    payload = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert payload["schema"] == hb.REPORT_SCHEMA
    assert payload["kind"] == hb.REPORT_KIND
    assert payload["verdict"] == hb.VERDICT_FAIL
    assert payload["queued_jobs"] == ["Heartbeat Linux aarch64"]
    summary = (tmp_path / "s.md").read_text(encoding="utf-8")
    assert "Heartbeat Linux aarch64 | ❌ wartet auf einen Runner" in summary
    assert "Heartbeat macOS arm64 | ✅ angenommen" in summary
    # Der Kommentar im Betriebs-Issue ist dieselbe Datei – er muss den Weg
    # zur Abhilfe nennen, nicht nur den Befund.
    assert "RELEASE_AUTOMATION.md" in summary
    assert "https://example.invalid/run/1" in summary


def test_watch_command_needs_a_token(monkeypatch, capsys) -> None:
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert hb.main(["watch", "--repo", "o/r", "--run-id", "1"]) == 2
    assert "GH_TOKEN" in capsys.readouterr().out


# ── Review PR #930: die zweite Haelfte des Signals ──────────────────────

def test_an_accepted_but_failing_runner_is_never_reported_as_pass() -> None:
    """``if: failure()`` sieht laut GitHub-Referenz nur Schritte DIESES Jobs
    und Vorgaenger per ``needs`` – die Runner-Jobs sind bewusst keine.

    Ohne die Conclusions meldete der Bericht ``PASS`` fuer ein Geraet, das
    gerade an der Bereitschaftspruefung gescheitert ist, und im
    Betriebs-Issue staende nichts.
    """
    state = hb.queue_state(_jobs("ok", "fail"), EXPECTED)
    assert state.queued == ()
    assert state.failed == ("Heartbeat Linux aarch64",)
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    assert verdict == hb.VERDICT_FAIL
    assert "nicht einsatzbereit" in detail


def test_a_timed_out_runner_job_counts_as_not_ready() -> None:
    """Angenommen, aber haengengeblieben – auch das ist keine Bereitschaft."""
    state = hb.queue_state(_jobs("ok", "timeout"), EXPECTED)
    assert state.failed == ("Heartbeat Linux aarch64",)


def test_a_cancelled_job_is_not_a_device_verdict() -> None:
    """Abbruch ist eine menschliche Handlung (oder cancel-in-progress) –
    aber eben auch kein Erfolg: kein FAIL, aber genauso wenig PASS (#943)."""
    state = hb.queue_state(_jobs("ok", "cancelled"), EXPECTED)
    assert state.failed == () and state.queued == ()
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    assert verdict == hb.VERDICT_UNOBSERVED
    assert "cancelled" in detail


def test_both_halves_of_the_signal_appear_together() -> None:
    """Beide Hälften stehen im Bericht – aber nur die belegte fristbezogen."""
    state = hb.queue_state(_jobs("queued", "fail"), EXPECTED)
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    assert verdict == hb.VERDICT_FAIL
    assert "noch nicht angenommen" in detail and "nicht einsatzbereit" in detail


def test_a_short_circuit_never_claims_an_expired_deadline() -> None:
    """``watch`` kehrt beim ersten gescheiterten Job **sofort** zurück.

    Dann kann gleichzeitig ein anderer Runner noch ``queued`` sein, ohne zu
    spät zu sein: Scheitert macOS nach 90 s an der Härtung, hätte der Pi bei
    t=200 s noch annehmen können. Der Bericht sagte trotzdem „wartet nach
    15 min" — eine Zahl, für die der Offline-Zweig nie durchlaufen wurde
    (#938-Review). Ausgerechnet dieser PR macht die Wahrhaftigkeit dieser
    Fristen zum Ziel.
    """
    ticks = iter([0, 0, 90])
    state = hb.watch(
        lambda: hb.queue_state(_jobs("queued", "fail"), EXPECTED), EXPECTED,
        acceptance_s=900, deadline_s=1500, poll_s=20,
        clock=lambda: next(ticks), sleep=lambda _s: None,
    )
    assert state.acceptance_expired is False, "Frist war nicht abgelaufen"
    _, detail = hb.evaluate(state, EXPECTED, acceptance_s=900, deadline_s=1500)
    assert "15 min" not in detail, detail
    assert "noch nicht angenommen" in detail

    # Gegenprobe: Läuft die Frist wirklich ab, steht die Zahl wieder da.
    # Der Beobachtungszeitpunkt liegt dicht an der Frist – sonst gälte die
    # Beobachtung als veraltet und der Heartbeat schlüge (richtigerweise)
    # gar keinen Alarm.
    ticks = iter([0, 890, 900, 900])
    expired = hb.watch(
        lambda: hb.queue_state(_jobs("queued", "queued"), EXPECTED), EXPECTED,
        acceptance_s=900, deadline_s=1500, poll_s=20,
        clock=lambda: next(ticks), sleep=lambda _s: None,
    )
    assert expired.acceptance_expired is True
    _, detail = hb.evaluate(expired, EXPECTED, acceptance_s=900, deadline_s=1500)
    assert "wartet nach 15 min" in detail


def test_a_stale_observation_at_the_acceptance_deadline_keeps_polling() -> None:
    """Ein API-Schluckauf darf das Beobachtungsfenster nicht verschenken.

    Die Frische-Degradierung galt vorher nur am Gesamtfenster. Mit der
    Annahmefrist griffe sie zehn Minuten früher: Eine Störung um t=900
    beendete die Beobachtung als ``UNOBSERVED``, obwohl die API bis 1500 s
    Zeit gehabt hätte, sich zu erholen (#938-Review).
    """
    calls = {"n": 0}

    def observe():
        calls["n"] += 1
        if calls["n"] >= 3:
            raise OSError("Jobs-API kurzzeitig weg")
        return hb.queue_state(_jobs("ok", "queued"), EXPECTED)

    ticks = iter([0, 860, 880, 900, 900, 1200, 1500, 1500, 1500])
    hb.watch(
        observe, EXPECTED, acceptance_s=900, deadline_s=1500, poll_s=20,
        clock=lambda: next(ticks), sleep=lambda _s: None,
    )
    assert calls["n"] >= 3, "Beobachtung endete zur Annahmefrist trotz Störung"


def test_the_offline_reason_names_the_busy_runner_case() -> None:
    """Self-hosted Runner nehmen einen Job gleichzeitig an.

    Läuft zur Heartbeat-Zeit eine Abnahme auf demselben Gerät, wartet der
    Job zu Recht. Der Empfänger des Issue-Kommentars soll dann nicht nach
    einem Ausfall suchen, den es nicht gibt (#938-Review).
    """
    state = hb.queue_state(_jobs("ok", "queued"), EXPECTED)
    _, detail = hb.evaluate(
        replace(state, acceptance_expired=True), EXPECTED,
        acceptance_s=900, deadline_s=1500,
    )
    assert "belegt" in detail, detail
    assert "offline" in detail


def test_the_cli_rejects_a_useless_acceptance_deadline(capsys) -> None:
    """Gleich oder groesser als das Gesamtfenster heisst: kein frueheres Verdikt.

    Der Heartbeat fiele damit still auf den Zustand zurueck, den dieser PR
    behebt — CLI, Docstring und Wächter verlangen deshalb dasselbe ``<``
    (#938-Review).
    """
    for acceptance in ("1500", "1600"):
        with pytest.raises(SystemExit):
            hb.main([
                "--report", "r.json", "--summary", "s.md", "watch",
                "--repo", "o/r", "--run-id", "1",
                "--acceptance-seconds", acceptance, "--deadline-seconds", "1500",
            ])
        assert "muss kleiner als" in capsys.readouterr().err


def test_the_report_records_whether_the_deadline_expired() -> None:
    """Auch die Evidenz muss die Unterscheidung tragen, nicht nur der Text."""
    state = hb.queue_state(_jobs("queued", "fail"), EXPECTED)
    report = hb.build_report(
        verdict=hb.VERDICT_FAIL, detail="egal", expected=EXPECTED, state=state,
        acceptance_s=900, deadline_s=1500, run_url="",
    )
    assert report["acceptance_expired"] is False
    assert report["acceptance_seconds"] == 900 and report["deadline_seconds"] == 1500


def test_watch_reports_a_failed_readiness_job_without_waiting_out_the_deadline() -> None:
    """Der Befund steht fest – warten verzoegerte nur die Meldung."""
    clock = iter([0, 0, 1])
    state = hb.watch(
        lambda: hb.queue_state(_jobs("ok", "fail"), EXPECTED), EXPECTED,
        acceptance_s=1500, deadline_s=1500, poll_s=20,
        clock=lambda: next(clock), sleep=lambda _s: None,
    )
    assert state.failed == ("Heartbeat Linux aarch64",)


def test_watch_waits_for_completion_not_merely_for_acceptance() -> None:
    """Ein noch laufender Job darf die Beobachtung nicht beenden – sonst
    saehe sie sein Scheitern nie."""
    seen = {"n": 0}

    def observe():
        seen["n"] += 1
        if seen["n"] == 1:
            return hb.queue_state(_jobs("running", "running"), EXPECTED)
        return hb.queue_state(_jobs("ok", "fail"), EXPECTED)

    clock = iter([0, 0, 0, 1])
    state = hb.watch(
        observe, EXPECTED, acceptance_s=900, deadline_s=1500, poll_s=20,
        clock=lambda: next(clock), sleep=lambda _s: None,
    )
    assert seen["n"] == 2
    assert state.failed == ("Heartbeat Linux aarch64",)


def test_a_job_still_running_at_the_deadline_yields_no_verdict() -> None:
    """Angenommen ist es – ueber die Bereitschaft ist noch nichts bekannt."""
    state = hb.QueueState(
        known=EXPECTED, queued=(), pending=("Heartbeat macOS arm64",),
    )
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    assert verdict == hb.VERDICT_UNOBSERVED
    assert "noch" in detail


# ── Review-Nachlese #943 Befund 1: PASS nur bei explizitem success ──────

@pytest.mark.parametrize(
    ("shape", "conclusion"),
    [
        ("stale", "stale"),
        ("skipped", "skipped"),
        ("cancelled", "cancelled"),
    ],
)
def test_a_non_success_conclusion_never_passes(shape: str, conclusion: str) -> None:
    """``stale``/``skipped``/``cancelled`` landeten vor #943 in keiner der
    drei Mengen – waren alle erwarteten Jobs vorhanden, meldete ``evaluate``
    PASS „Bereitschaftsprüfung bestanden" ohne jeden Beleg."""
    state = hb.queue_state(_jobs("ok", shape), EXPECTED)
    assert state.inconclusive == (("Heartbeat Linux aarch64", conclusion),)
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    assert verdict == hb.VERDICT_UNOBSERVED
    assert "Heartbeat Linux aarch64" in detail and conclusion in detail


def test_a_startup_failure_is_a_device_finding_with_an_alert_path() -> None:
    """#944-Review: ``startup_failure`` heißt „angenommen, konnte nicht
    starten" – dieselbe Geräteklasse wie ``failure``/``timed_out``. Als
    ``inconclusive`` endete der Lauf mit Exit 0 und der Issue-Kommentar
    (``if: failure()``) bliebe aus – der laut §7 einzige rechtzeitige Kanal."""
    state = hb.queue_state(_jobs("ok", "startup"), EXPECTED)
    assert state.failed == ("Heartbeat Linux aarch64",)
    assert state.failed_conclusions == (("Heartbeat Linux aarch64", "startup_failure"),)
    assert state.inconclusive == ()
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    assert verdict == hb.VERDICT_FAIL
    assert "nicht einsatzbereit" in detail
    # #954-Review: Es lief keine Pruefung und es gibt kein Joblog – der Text
    # nennt die Konklusion statt einer „nicht bestandenen Pruefung".
    assert "startup_failure" in detail and "kein Joblog" in detail
    assert "Bereitschaftsprüfung nicht bestanden" not in detail


def test_the_summary_names_a_startup_failure_and_its_remedy(tmp_path: Path) -> None:
    state = hb.queue_state(_jobs("ok", "startup"), EXPECTED)
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    report = hb.build_report(
        verdict=verdict, detail=detail, expected=EXPECTED, state=state,
        acceptance_s=900, deadline_s=1500, run_url="",
    )
    hb.write_outputs(report, report_path=tmp_path / "r.json", summary_path=tmp_path / "s.md")
    payload = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert payload["failed_job_conclusions"] == [
        {"name": "Heartbeat Linux aarch64", "conclusion": "startup_failure"}
    ]
    summary = (tmp_path / "s.md").read_text(encoding="utf-8")
    assert "❌ angenommen, aber nicht gestartet (startup_failure)" in summary
    assert "Runner-Workspace (`_work`) bereinigen" in summary


def test_a_completed_job_without_conclusion_never_passes() -> None:
    """Auch eine fehlende Konklusion ist kein Erfolg – fail-closed."""
    state = hb.queue_state(_jobs("ok", "noconcl"), EXPECTED)
    assert state.inconclusive == (("Heartbeat Linux aarch64", ""),)
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    assert verdict == hb.VERDICT_UNOBSERVED
    assert "unbekannt" in detail


def test_a_proven_failure_outranks_an_inconclusive_sibling() -> None:
    """Der belegte Befund trägt das Verdikt; das abgebrochene Ergebnis
    degradiert ihn nicht zu UNOBSERVED."""
    state = hb.queue_state(_jobs("cancelled", "fail"), EXPECTED)
    verdict, _ = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    assert verdict == hb.VERDICT_FAIL


def test_report_and_summary_carry_the_inconclusive_conclusion(tmp_path: Path) -> None:
    """Evidenz und Issue-Kommentar müssen das Ergebnis benennen, sonst sucht
    der Empfänger nach einem Ausfall, den es nicht gibt."""
    state = hb.queue_state(_jobs("ok", "cancelled"), EXPECTED)
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    report = hb.build_report(
        verdict=verdict, detail=detail, expected=EXPECTED, state=state,
        acceptance_s=900, deadline_s=1500, run_url="",
    )
    hb.write_outputs(report, report_path=tmp_path / "r.json", summary_path=tmp_path / "s.md")
    payload = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert payload["inconclusive_jobs"] == [
        {"name": "Heartbeat Linux aarch64", "conclusion": "cancelled"}
    ]
    summary = (tmp_path / "s.md").read_text(encoding="utf-8")
    assert "Heartbeat Linux aarch64 | ⚠️ endete ohne success (cancelled)" in summary
    assert "Heartbeat macOS arm64 | ✅ angenommen und bestanden" in summary


def test_the_report_separates_offline_from_not_ready(tmp_path: Path) -> None:
    state = hb.queue_state(_jobs("queued", "fail"), EXPECTED)
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    report = hb.build_report(
        verdict=verdict, detail=detail, expected=EXPECTED, state=state,
        acceptance_s=900, deadline_s=1500, run_url="",
    )
    hb.write_outputs(report, report_path=tmp_path / "r.json", summary_path=tmp_path / "s.md")
    payload = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert payload["queued_jobs"] == ["Heartbeat macOS arm64"]
    assert payload["failed_jobs"] == ["Heartbeat Linux aarch64"]
    summary = (tmp_path / "s.md").read_text(encoding="utf-8")
    assert "❌ wartet auf einen Runner" in summary
    assert "❌ angenommen, aber nicht einsatzbereit" in summary
