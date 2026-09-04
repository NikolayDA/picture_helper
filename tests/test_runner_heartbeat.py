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
from datetime import date, timedelta
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
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    assert verdict == hb.VERDICT_FAIL
    # #954-Review: Die Konklusion steht im Text – wie bei ``inconclusive``.
    assert "Heartbeat Linux aarch64 (timed_out) hat die Bereitschaftsprüfung" in detail


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
    # Der API-Wert ist extern vorgegeben; die Konstante ist die einzige Quelle
    # im Modul und muss ihn treffen (#957-Review).
    assert hb.STARTUP_FAILURE_CONCLUSION == "startup_failure"
    assert hb.STARTUP_FAILURE_CONCLUSION in hb.FAILED_CONCLUSIONS
    state = hb.queue_state(_jobs("ok", "startup"), EXPECTED)
    assert state.failed == ("Heartbeat Linux aarch64",)
    assert state.failed_conclusions == (
        ("Heartbeat Linux aarch64", hb.STARTUP_FAILURE_CONCLUSION),
    )
    assert state.inconclusive == ()
    verdict, detail = hb.evaluate(state, EXPECTED, acceptance_s=1500, deadline_s=1500)
    assert verdict == hb.VERDICT_FAIL
    assert "nicht einsatzbereit" in detail
    # #954-Review: Es lief keine Pruefung und es gibt kein Joblog – der Text
    # nennt die Konklusion statt einer „nicht bestandenen Pruefung".
    assert hb.STARTUP_FAILURE_CONCLUSION in detail and "kein Joblog" in detail
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
        {"name": "Heartbeat Linux aarch64", "conclusion": hb.STARTUP_FAILURE_CONCLUSION}
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
    # #954-Review: Die Konklusion steht auch in der Zusammenfassung.
    assert "❌ angenommen, aber nicht einsatzbereit (failure)" in summary


# ── Gestufte Eskalation (#958) ─────────────────────────────────────────

LINUX = hb.HEARTBEAT_JOB_NAMES["linux-arm64"]
MACOS = hb.HEARTBEAT_JOB_NAMES["macos-arm64"]
STAGES = hb.OFFLINE_STAGE_DAYS


def _record(days_ago: int, linux: str = "ok", macos: str = "ok") -> hb.RunRecord:
    """Ein früherer Lauf, ``days_ago`` Tage vor ``TODAY``.

    Kurzformen wie in ``_jobs``; ``absent`` lässt den Job ganz weg.
    """
    shapes = {
        "ok": ("completed", "success"),
        "fail": ("completed", "failure"),
        "cancelled": ("completed", "cancelled"),
        "stale": ("completed", "stale"),
        "skipped": ("completed", "skipped"),
        "queued": ("queued", ""),
    }
    jobs = {}
    for name, shape in ((LINUX, linux), (MACOS, macos)):
        if shape != "absent":
            jobs[name] = shapes[shape]
    return hb.RunRecord(day=TODAY - timedelta(days=days_ago), jobs=jobs)


def _episode_of(days: int) -> list[hb.RunRecord]:
    """Historie, in der Linux seit genau ``days`` Tagen scheitert und davor bestand."""
    return [_record(ago, linux="fail") for ago in range(1, days + 1)] + [
        _record(days + 1, linux="ok")
    ]


def _failing_today(*, offline: bool = True) -> hb.QueueState:
    if offline:
        return replace(hb.queue_state(_jobs("ok", "queued"), EXPECTED), acceptance_expired=True)
    return hb.queue_state(_jobs("ok", "fail"), EXPECTED)


@pytest.mark.parametrize(
    ("days", "stage"),
    [(0, 0), (6, 0), (7, 1), (11, 1), (12, 2), (20, 2), (21, 3)],
)
def test_stage_follows_the_days_without_a_passed_heartbeat(days: int, stage: int) -> None:
    """HB-STUFE-03 mit den Owner-Stufen 7/12/21: 0/6/7/11/12/20/21 Tage →
    keine/keine/1/1/2/2/3."""
    assert STAGES == (7, 12, 21)
    episode = hb.offline_episode(_episode_of(days), LINUX, today=TODAY)
    assert (TODAY - episode.since).days == days
    assert episode.at_least is False
    assert hb.offline_stage(days, STAGES) == stage


def test_an_episode_starts_today_when_yesterday_passed() -> None:
    episode = hb.offline_episode([_record(1, linux="ok")], LINUX, today=TODAY)
    assert episode == hb.Episode(since=TODAY, at_least=False)
    # Ohne jede Historie ebenso – Tag 0, nichts "seit mindestens".
    assert hb.offline_episode([], LINUX, today=TODAY) == hb.Episode(since=TODAY, at_least=False)


def test_a_maintenance_window_neither_starts_nor_ends_an_episode() -> None:
    """Die Zählung läuft über eine Pause real weiter (#958) – übersprungene
    Läufe zählen weder als Ausfall noch als Erfolg."""
    # Ausfall, dann drei Tage Pause, dann wieder Ausfall: Episode seit Tag 6.
    history = [
        _record(1, linux="fail"), _record(2, linux="fail"),
        _record(3, linux="skipped"), _record(4, linux="skipped"), _record(5, linux="skipped"),
        _record(6, linux="fail"), _record(7, linux="ok"),
    ]
    assert hb.offline_episode(history, LINUX, today=TODAY).since == TODAY - timedelta(days=6)
    # Nur Pause vor dem ersten Ausfall: die Episode beginnt heute, nicht mit der Pause.
    paused_only = [_record(1, linux="skipped"), _record(2, linux="skipped"), _record(3, linux="ok")]
    assert hb.offline_episode(paused_only, LINUX, today=TODAY).since == TODAY


def test_the_cleanup_cancel_of_a_queued_job_counts_as_a_day_without_success() -> None:
    """Der Offline-Fall sieht in der Historie so aus: Der wartende Job des
    Vortags endet über ``cancel-in-progress`` als ``cancelled`` (oder
    ``stale``). Wäre das neutral, gäbe es für offline Runner nie eine Episode."""
    history = [_record(1, linux="cancelled"), _record(2, linux="stale"), _record(3, linux="ok")]
    assert hb.offline_episode(history, LINUX, today=TODAY).since == TODAY - timedelta(days=2)
    # Ein noch offener oder fehlender Job sagt dagegen nichts.
    open_history = [_record(1, linux="queued"), _record(2, linux="absent"), _record(3, linux="ok")]
    assert hb.offline_episode(open_history, LINUX, today=TODAY).since == TODAY


def test_a_history_without_a_passed_run_reads_as_at_least() -> None:
    history = [_record(ago, linux="fail") for ago in range(1, 4)]
    episode = hb.offline_episode(history, LINUX, today=TODAY)
    assert episode == hb.Episode(since=TODAY - timedelta(days=3), at_least=True)


def test_marker_search_is_scoped_to_platform_and_episode() -> None:
    since = TODAY - timedelta(days=7)
    comments = [
        (TODAY, f"<!-- {hb.stage_marker('linux-arm64', since, 1)} -->\nText"),
        (TODAY, f"<!-- {hb.stage_marker('macos-arm64', since, 2)} -->"),
        (TODAY, f"<!-- {hb.stage_marker('linux-arm64', since - timedelta(days=30), 3)} -->"),
    ]
    assert hb.posted_stages(comments, "linux-arm64", since) == (1,)
    assert hb.posted_stages(comments, "macos-arm64", since) == (2,)
    assert hb.posted_stages(comments, "linux-arm64", TODAY) == ()


def test_a_rerun_on_the_same_day_posts_nothing(tmp_path: Path) -> None:
    """HB-STUFE-04: genau ein Kommentar je Episode und Stufe."""
    records = _episode_of(7)
    first = hb.decide_stages(_failing_today(), records=records, comments=[], today=TODAY)
    (decision,) = first
    assert (decision.platform, decision.stage_due, decision.stage_to_post) == ("linux-arm64", 1, 1)
    body = hb.render_stage_comment(
        decision, mention="owner", run_url="", today=TODAY, repo="o/r",
    )
    # Zweiter Lauf: der Kommentar von eben ist da – nichts mehr fällig.
    second = hb.decide_stages(
        _failing_today(), records=records, comments=[(TODAY, body)], today=TODAY,
    )
    assert second[0].stages_posted == (1,)
    assert second[0].stage_to_post == 0
    assert second[0].retire is False


def test_only_the_highest_due_stage_is_posted_per_run() -> None:
    """Nach einer Pause können zwei Stufen zugleich fällig sein. Gepostet wird
    die höchste – die niedrigere sagte „noch N Tage bis GitHub …" und wäre
    schon falsch."""
    (decision,) = hb.decide_stages(
        _failing_today(), records=_episode_of(13), comments=[], today=TODAY,
    )
    assert (decision.stage_due, decision.stage_to_post) == (2, 2)
    since = decision.since
    posted = [(TODAY, f"<!-- {hb.stage_marker('linux-arm64', since, 2)} -->")]
    (again,) = hb.decide_stages(
        _failing_today(), records=_episode_of(13), comments=posted, today=TODAY,
    )
    assert again.stage_to_post == 0, "Stufe 1 wird nicht nachgeholt, sie ist überholt"


def test_stage_three_retires_and_a_posted_marker_means_it_already_happened() -> None:
    """Stufe 3 trägt aus. Der ``retire``-Job setzt die Variable **vor** dem
    Kommentar – ein vorhandener Stufe-3-Marker belegt also eine erfolgte
    Austragung. Ist die Plattform trotzdem wieder im Bestand (Variable
    entfernt), ist das eine Reaktivierung, und die Episode beginnt neu:
    kein zweites stilles Austragen am alten ``offline_since``."""
    (decision,) = hb.decide_stages(
        _failing_today(), records=_episode_of(21), comments=[], today=TODAY,
    )
    assert (decision.stage_due, decision.stage_to_post, decision.retire) == (3, 3, True)
    posted = [(TODAY, f"<!-- {hb.stage_marker('linux-arm64', decision.since, 3)} -->")]
    (again,) = hb.decide_stages(
        _failing_today(), records=_episode_of(21), comments=posted, today=TODAY,
    )
    assert (again.since, again.days, again.stage_to_post, again.retire) == (TODAY, 0, 0, False)


def test_a_retirement_ends_the_episode() -> None:
    """Reaktiviert (Variable entfernt) und erneut ausgefallen: Die Zählung
    beginnt nach der Austragung neu. Sonst hinge die neue Episode am alten
    ``offline_since``, fände ihre Marker vor und trüge still ein zweites Mal aus."""
    retired_on = TODAY - timedelta(days=10)
    old_since = TODAY - timedelta(days=31)
    history = (
        [_record(ago, linux="fail") for ago in range(1, 4)]            # neue Episode: 3 Tage
        + [_record(ago, linux="skipped") for ago in range(4, 10)]     # ausgetragen: übersprungen
        + [_record(ago, linux="fail") for ago in range(10, 32)]       # alte Episode
    )
    comments = [(retired_on, f"<!-- {hb.stage_marker('linux-arm64', old_since, 3)} -->")]
    assert hb.last_retirement(comments, "linux-arm64") == retired_on
    (decision,) = hb.decide_stages(
        _failing_today(), records=history, comments=comments, today=TODAY,
    )
    assert decision.since == TODAY - timedelta(days=3)
    assert (decision.days, decision.stage_due, decision.retire) == (3, 0, False)
    # Ohne den Austragungskommentar hinge sie an der alten Episode.
    (naive,) = hb.decide_stages(_failing_today(), records=history, comments=[], today=TODAY)
    assert naive.since == old_since and naive.retire is True


def test_only_a_proven_fail_gets_a_stage() -> None:
    """Ein wartender Job bei vorzeitig beendeter Beobachtung ist kein
    Offline-Befund (``evaluate``) – und bekommt deshalb auch keine Stufe."""
    not_expired = hb.queue_state(_jobs("queued", "fail"), EXPECTED)
    assert hb.failing_platforms(not_expired) == [("linux-arm64", hb.CAUSE_NOT_READY, "failure")]
    expired = replace(not_expired, acceptance_expired=True)
    assert hb.failing_platforms(expired) == [
        ("macos-arm64", hb.CAUSE_OFFLINE, ""),
        ("linux-arm64", hb.CAUSE_NOT_READY, "failure"),
    ]


def _decision(days: int, *, offline: bool = True, conclusion: str = "failure") -> hb.StageDecision:
    state = _failing_today(offline=offline)
    if not offline:
        state = hb.queue_state(
            [{"name": MACOS, "status": "completed", "conclusion": "success"},
             {"name": LINUX, "status": "completed", "conclusion": conclusion}],
            EXPECTED,
        )
    (decision,) = hb.decide_stages(state, records=_episode_of(days), comments=[], today=TODAY)
    return decision


def test_stage_comments_pin_platform_since_days_next_stage_and_remedy() -> None:
    """HB-STUFE-06: Jeder Stufenkommentar nennt Plattform/Job, ``offline_since``,
    Tage, Datum der nächsten Stufe und die passende Abhilfe; der Marker steht
    in der ersten Zeile, die Erwähnung ist der Mailweg."""
    since = TODAY - timedelta(days=7)
    body = hb.render_stage_comment(
        _decision(7), mention="NikolayDA", run_url="https://example.invalid/run/9",
        today=TODAY, repo="o/r",
    )
    lines = body.splitlines()
    assert lines[0] == f"<!-- {hb.stage_marker('linux-arm64', since, 1)} -->"
    assert "Stufe 1/3" in lines[1] and LINUX in lines[1]
    assert "@NikolayDA" in body
    assert f"| Plattform / Runner-Job | `linux-arm64` / {LINUX} |" in body
    assert f"| Ohne bestandenen Heartbeat seit | {since.isoformat()} (7 Tage, Stand {TODAY.isoformat()}) |" in body
    # Stufe 1 (offline): GitHubs Frist mit Restlaufzeit und Datum, nächste Stufe am Tag 12.
    removal_day = since + timedelta(days=hb.GITHUB_RUNNER_REMOVAL_DAYS)
    assert f"voraussichtlich ab {removal_day.isoformat()} (**noch 7 Tage**)" in body
    assert f"| Nächste Stufe | Stufe 2 am {(since + timedelta(days=12)).isoformat()} (12 Tage) |" in body
    assert "docs/RUNNER_SETUP.md` §5" in body
    assert "https://example.invalid/run/9" in body
    assert "Simulation" not in body


def test_stage_two_names_githubs_removal_and_announces_retirement() -> None:
    since = TODAY - timedelta(days=12)
    body = hb.render_stage_comment(_decision(12), mention="o", run_url="", today=TODAY, repo="o/r")
    assert "Stufe 2/3" in body
    assert f"| Ohne bestandenen Heartbeat seit | {since.isoformat()} (12 Tage" in body
    assert "(**noch 2 Tage**)" in body and "Danach genügt Wiederbeleben nicht mehr" in body
    assert f"Stufe 3 am {(since + timedelta(days=21)).isoformat()} (21 Tage): Austragung" in body
    assert "`RUNNER_LINUX_ARM64_RETIRED_SINCE`" in body


def test_stage_three_names_retirement_and_the_way_back() -> None:
    body = hb.render_stage_comment(_decision(21), mention="o", run_url="", today=TODAY, repo="o/r")
    assert "Stufe 3/3" in body and "ausgetragen" in body.splitlines()[1]
    assert f"`RUNNER_LINUX_ARM64_RETIRED_SINCE={TODAY.isoformat()}`" in body
    assert "**Reaktivierung:**" in body
    assert "gh variable delete RUNNER_LINUX_ARM64_RETIRED_SINCE --repo o/r" in body
    assert f"„ausgetragen seit {TODAY.isoformat()}\"" in body
    # GitHubs Frist ist zu diesem Zeitpunkt überschritten – und der Text sagt es.
    assert "**entfernt**" in body and "Neuregistrierung nötig" in body


def test_a_not_ready_runner_never_hears_about_githubs_removal() -> None:
    """Die Stufenlogik gilt für beide FAIL-Ursachen, aber nur der Offline-Text
    nennt die 14-Tage-Entfernung – ein verbundener Runner verliert seine
    Registrierung nicht."""
    body = hb.render_stage_comment(
        _decision(7, offline=False), mention="o", run_url="", today=TODAY, repo="o/r",
    )
    assert "angenommen, aber nicht einsatzbereit (`failure`)" in body
    assert "greift hier nicht" in body
    assert "voraussichtlich ab" not in body and "entfernt einen Runner" not in body
    assert "§2.3 (macOS) bzw. §3.4 (Pi)" in body
    startup = hb.render_stage_comment(
        _decision(7, offline=False, conclusion=hb.STARTUP_FAILURE_CONCLUSION),
        mention="o", run_url="", today=TODAY, repo="o/r",
    )
    assert "nicht gestartet (`startup_failure`)" in startup and "`_work`" in startup


def test_the_at_least_case_is_worded_as_a_lower_bound() -> None:
    history = [_record(ago, linux="fail") for ago in range(1, 8)]
    (decision,) = hb.decide_stages(_failing_today(), records=history, comments=[], today=TODAY)
    assert decision.at_least is True and decision.days == 7
    body = hb.render_stage_comment(decision, mention="o", run_url="", today=TODAY, repo="o/r")
    assert "seit ≥ 7 Tagen" in body.splitlines()[1]
    assert f"| Ohne bestandenen Heartbeat seit | mindestens {decision.since.isoformat()} (≥ 7 Tage" in body


def test_collect_history_stops_at_the_first_passed_run_per_job() -> None:
    """Im Regelfall (gestern grün) kostet die Historie einen einzigen Jobs-Aufruf."""
    runs = [
        {"id": 100, "created_at": f"{TODAY.isoformat()}T05:30:00Z"},           # laufender Lauf
        {"id": 99, "created_at": f"{(TODAY - timedelta(days=1)).isoformat()}T05:30:00Z"},
        {"id": 98, "created_at": f"{(TODAY - timedelta(days=2)).isoformat()}T05:30:00Z"},
        {"id": 97, "created_at": "kaputt"},
    ]
    fetched: list[str] = []

    def jobs_for(run_id: str) -> list[dict]:
        fetched.append(run_id)
        conclusion = "success" if run_id == "99" else "failure"
        return [{"name": LINUX, "status": "completed", "conclusion": conclusion}]

    records = hb.collect_history(runs, jobs_for, job_names=[LINUX], exclude_run_id="100")
    assert fetched == ["99"], "der laufende Lauf ist ausgeschlossen, danach reicht ein Aufruf"
    assert [record.day for record in records] == [TODAY - timedelta(days=1)]
    # Ohne Erfolg wird bis zum Ende des Fensters geladen; ein unlesbares Datum überspringt.
    fetched.clear()

    def never_ok(run_id: str) -> list[dict]:
        fetched.append(run_id)
        return [{"name": LINUX, "status": "completed", "conclusion": "failure"}]

    hb.collect_history(runs, never_ok, job_names=[LINUX], exclude_run_id="100")
    assert fetched == ["99", "98"]


def test_stage_files_route_stage_three_to_the_retire_job(tmp_path: Path) -> None:
    """Stufen 1/2 postet ``watch`` selbst; Stufe 3 erst der ``retire``-Job nach
    dem Setzen der Variable – der Kommentar darf nie eine Austragung
    behaupten, die nicht stattfand. Der Variablenname kommt aus dem Skript."""
    stage_platforms, retire = hb.write_stage_files(
        [_decision(7)], directory=tmp_path, mention="o", run_url="", today=TODAY, repo="o/r",
        simulated=False,
    )
    assert (stage_platforms, retire) == (["linux-arm64"], [])
    assert (tmp_path / "stage-comment-linux-arm64.md").is_file()
    assert not (tmp_path / "retire.tsv").exists()

    stage_platforms, retire = hb.write_stage_files(
        [_decision(21)], directory=tmp_path, mention="o", run_url="", today=TODAY, repo="o/r",
        simulated=False,
    )
    assert (stage_platforms, retire) == ([], ["linux-arm64"])
    assert (tmp_path / "retire-comment-linux-arm64.md").is_file()
    assert (tmp_path / "retire.tsv").read_text(encoding="utf-8") == (
        f"linux-arm64\tRUNNER_LINUX_ARM64_RETIRED_SINCE\t{TODAY.isoformat()}\n"
    )
    # Simulation: Stufe 3 wird nur kommentiert, nie ausgetragen.
    sim_dir = tmp_path / "sim"
    stage_platforms, retire = hb.write_stage_files(
        [replace(_decision(21), retire=False)], directory=sim_dir, mention="o", run_url="",
        today=TODAY, repo="o/r", simulated=True,
    )
    assert (stage_platforms, retire) == (["linux-arm64"], [])
    assert not (sim_dir / "retire.tsv").exists()
    assert "**Simulation**" in (sim_dir / "stage-comment-linux-arm64.md").read_text(encoding="utf-8")


def test_report_and_summary_carry_the_stage_decision(tmp_path: Path) -> None:
    """HB-STUFE-10: ``offline_stages`` additiv (Schema bleibt 1), Summary
    rendert Stufe und nächstes Fälligkeitsdatum."""
    decision = _decision(12)
    state = _failing_today()
    report = hb.build_report(
        verdict=hb.VERDICT_FAIL, detail="egal", expected=EXPECTED, state=state,
        acceptance_s=900, deadline_s=1500, run_url="", decisions=[decision],
        comment_issue="939", retired={"macos-arm64": TODAY - timedelta(days=2)},
    )
    assert report["schema"] == 1
    assert report["stage_days"] == [7, 12, 21] and report["removal_days"] == 14
    (entry,) = report["offline_stages"]
    assert entry["stage_due"] == 2 and entry["stage_to_post"] == 2 and entry["retire"] is False
    assert entry["marker"] == hb.stage_marker("linux-arm64", decision.since, 2)
    hb.write_outputs(report, report_path=tmp_path / "r.json", summary_path=tmp_path / "s.md")
    summary = (tmp_path / "s.md").read_text(encoding="utf-8")
    assert "### Eskalation (#958)" in summary
    assert "| 12 | 2 (≥ 12 Tage) | Stufe 2 heute gepostet in #939; nächste Stufe 3 nach 21 Tagen |" in summary
    assert "`macos-arm64` ist seit" in summary and "RUNNER_MACOS_ARM64_RETIRED_SINCE" in summary
    # Die Abhilfe wird aus den Konstanten gerendert – kein handgepflegtes "14 Tage".
    assert f"länger als {hb.GITHUB_RUNNER_REMOVAL_DAYS} Tage ohne Verbindung" in summary
    assert "meldet nach 7/12/21 Tagen" in summary


def test_an_unreadable_history_yields_a_visible_hint_instead_of_a_stage(tmp_path: Path) -> None:
    """HB-STUFE-09: fail-safe – keine geratene Stufe."""
    report = hb.build_report(
        verdict=hb.VERDICT_FAIL, detail="egal", expected=EXPECTED, state=_failing_today(),
        acceptance_s=900, deadline_s=1500, run_url="",
        stage_observation=(False, "Laufhistorie nicht lesbar (api down)"),
    )
    assert report["offline_stages"] == []
    assert report["stage_observation"] == {
        "observed": False, "detail": "Laufhistorie nicht lesbar (api down)",
    }
    assert "Stufenauswertung ohne Entscheidung: Laufhistorie nicht lesbar" in hb.render_summary(report)


def test_retired_platforms_are_not_expected() -> None:
    assert hb.retired_variable("linux-arm64") == "RUNNER_LINUX_ARM64_RETIRED_SINCE"
    assert hb.retired_variable("linux-x86_64") == "RUNNER_LINUX_X86_64_RETIRED_SINCE"
    retired = hb.parse_retired(["macos-arm64=", "linux-arm64=2026-08-20", "linux-x86_64="])
    assert retired == {"linux-arm64": date(2026, 8, 20)}
    assert hb.expected_jobs(x86_enabled=False, retired=retired) == (MACOS,)
    assert hb.expected_jobs(x86_enabled=True, retired=retired) == (MACOS, hb.HEARTBEAT_JOB_NAMES["linux-x86_64"])
    with pytest.raises(ValueError, match="kein ISO-Datum"):
        hb.parse_retired(["linux-arm64=irgendwann"])
    with pytest.raises(ValueError, match="erwartet <plattform>=<datum>"):
        hb.parse_retired(["pi=2026-08-20"])


def test_simulation_inputs_are_only_effective_together() -> None:
    kwargs = {"platform": "linux-arm64", "real_issue": "939"}
    assert hb.simulation_from_args(offline_since="", target_issue="", **kwargs) is None
    with pytest.raises(ValueError, match="gemeinsam"):
        hb.simulation_from_args(offline_since="2026-08-01", target_issue="", **kwargs)
    with pytest.raises(ValueError, match="gemeinsam"):
        hb.simulation_from_args(offline_since="", target_issue="12", **kwargs)
    with pytest.raises(ValueError, match="nie gegen das Betriebs-Issue"):
        hb.simulation_from_args(offline_since="2026-08-01", target_issue="939", **kwargs)
    with pytest.raises(ValueError, match="kein ISO-Datum"):
        hb.simulation_from_args(offline_since="gestern", target_issue="12", **kwargs)
    sim = hb.simulation_from_args(offline_since="2026-08-01", target_issue="12", **kwargs)
    assert sim == hb.Simulation(platform="linux-arm64", since=date(2026, 8, 1), issue="12")
    decision = hb.simulated_decision(sim, comments=[], today=date(2026, 8, 22))
    assert (decision.stage_due, decision.stage_to_post, decision.retire) == (3, 3, False)


def test_the_cli_rejects_a_half_simulation_before_observing(monkeypatch, capsys) -> None:
    monkeypatch.setenv("GH_TOKEN", "t")
    code = hb.main([
        "watch", "--repo", "o/r", "--run-id", "1", "--issue", "939",
        "--simulate-offline-since", "2026-08-01",
    ])
    assert code == 2
    assert "gemeinsam" in capsys.readouterr().out


def test_the_cli_rejects_unordered_stage_days(capsys) -> None:
    with pytest.raises(SystemExit):
        hb.main(["watch", "--repo", "o/r", "--run-id", "1", "--stage-days", "7", "7", "21"])
    assert "streng steigend" in capsys.readouterr().err


def test_an_all_retired_inventory_is_no_pass(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("GH_TOKEN", "t")
    code = hb.main([
        "--report", str(tmp_path / "r.json"), "--summary", str(tmp_path / "s.md"),
        "watch", "--repo", "o/r", "--run-id", "1",
        "--retired-since", "macos-arm64=2026-08-01", "--retired-since", "linux-arm64=2026-08-02",
        "--today", TODAY.isoformat(),
    ])
    assert code == 0
    payload = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert payload["verdict"] == hb.VERDICT_UNOBSERVED
    assert payload["retired"] == {"linux-arm64": "2026-08-02", "macos-arm64": "2026-08-01"}
    assert "alle Plattformen sind ausgetragen" in capsys.readouterr().out


def test_watch_end_to_end_writes_stage_files_and_outputs(tmp_path: Path, monkeypatch) -> None:
    """Der ganze Weg mit injiziertem Netz: Linux wartet nach der Annahmefrist,
    die Historie zeigt sieben Ausfalltage, im Issue steht noch nichts →
    Stufe 1, Kommentardatei, Outputs für den Workflow."""
    monkeypatch.setenv("GH_TOKEN", "t")
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "out.txt"))
    monkeypatch.setattr(hb, "fetch_jobs", lambda *a, **k: _jobs("ok", "queued"))
    monkeypatch.setattr(hb, "fetch_issue_comments", lambda *a, **k: [])
    seen: dict = {}

    def history(repo, token, *, api_url, since, exclude_run_id, job_names, **_):
        seen.update(since=since, exclude=exclude_run_id, jobs=tuple(job_names))
        return _episode_of(7)

    monkeypatch.setattr(hb, "fetch_run_history", history)
    code = hb.main([
        "--report", str(tmp_path / "r.json"), "--summary", str(tmp_path / "s.md"),
        "watch", "--repo", "o/r", "--run-id", "42", "--issue", "939", "--mention", "owner",
        # Echte Uhr: Annahmefrist 0,5 s, ein Poll-Intervall von 1 s hält die
        # Beobachtung "frisch" (juenger als zwei Intervalle).
        "--acceptance-seconds", "0.5", "--deadline-seconds", "5", "--poll-seconds", "1",
        "--comments-dir", str(tmp_path / "hb"), "--today", TODAY.isoformat(),
    ])
    assert code == 1
    assert seen == {
        "since": TODAY - timedelta(days=hb.HISTORY_WINDOW_DAYS), "exclude": "42", "jobs": (LINUX,),
    }
    outputs = (tmp_path / "out.txt").read_text(encoding="utf-8")
    assert "stage_comments=linux-arm64\n" in outputs
    assert "retire=\n" in outputs and "comment_issue=939\n" in outputs
    comment = (tmp_path / "hb" / "stage-comment-linux-arm64.md").read_text(encoding="utf-8")
    assert comment.startswith(f"<!-- {hb.stage_marker('linux-arm64', TODAY - timedelta(days=7), 1)} -->")
    assert "@owner" in comment
    payload = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert payload["offline_stages"][0]["stage_to_post"] == 1
    assert payload["stage_observation"]["observed"] is True
