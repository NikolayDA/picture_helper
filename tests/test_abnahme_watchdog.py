"""Tests des Queue-Watchdogs der Release-Abnahme (#915, Epic #914)."""
from __future__ import annotations

import importlib.util
import sys
import urllib.error
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "abnahme_watchdog", ROOT / "scripts" / "abnahme_watchdog.py"
)
assert _SPEC is not None and _SPEC.loader is not None
watchdog = importlib.util.module_from_spec(_SPEC)
sys.modules["abnahme_watchdog"] = watchdog
_SPEC.loader.exec_module(watchdog)

MACOS = watchdog.PREFLIGHT_JOB_NAMES["macos-arm64"]
LINUX = watchdog.PREFLIGHT_JOB_NAMES["linux-arm64"]
X86 = watchdog.PREFLIGHT_JOB_NAMES["linux-x86_64"]
HEAVY_MACOS = watchdog.ACCEPTANCE_JOB_NAMES["macos-arm64"]
HEAVY_LINUX = watchdog.ACCEPTANCE_JOB_NAMES["linux-arm64"]


def _job(name: str, status: str = "queued", conclusion: str | None = None) -> dict[str, Any]:
    return {"name": name, "status": status, "conclusion": conclusion}


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def test_expected_preflights_mirror_job_gating() -> None:
    """Die erwartete Menge spiegelt die if-Bedingungen der Preflight-Jobs."""
    assert watchdog.expected_preflights("alle", x86_enabled=False) == (MACOS, LINUX)
    assert watchdog.expected_preflights("alle", x86_enabled=True) == (MACOS, LINUX, X86)
    assert watchdog.expected_preflights("macos-arm64", x86_enabled=False) == (MACOS,)
    assert watchdog.expected_preflights("linux-arm64", x86_enabled=False) == (LINUX,)
    # Pausierter x86_64-Pfad: der Preflight-Job wird uebersprungen und darf
    # nicht erwartet werden.
    assert watchdog.expected_preflights("linux-x86_64", x86_enabled=False) == ()
    assert watchdog.expected_preflights("linux-x86_64", x86_enabled=True) == (X86,)


def test_expected_acceptance_mirrors_job_gating() -> None:
    """Phase 2 (Codex-Review PR #924) erwartet dieselben aktiven Plattformen."""
    assert watchdog.expected_acceptance("alle", x86_enabled=False) == (
        HEAVY_MACOS, HEAVY_LINUX,
    )
    assert watchdog.expected_acceptance("linux-x86_64", x86_enabled=False) == ()


def test_preflight_job_names_match_workflow() -> None:
    """Namensdrift zwischen Skript-Tabellen und Workflow-Anzeigenamen faellt auf."""
    workflow = (ROOT / ".github" / "workflows" / "release-abnahme.yml").read_text(
        encoding="utf-8"
    )
    for name in watchdog.PREFLIGHT_JOB_NAMES.values():
        assert f"name: {name}" in workflow, name
        assert name.startswith(watchdog.JOB_NAME_PREFIX)
    for name in watchdog.ACCEPTANCE_JOB_NAMES.values():
        assert f"name: {name}" in workflow, name


def test_tracked_state_reports_named_jobs() -> None:
    jobs = [
        _job(HEAVY_MACOS, "in_progress"),
        _job(HEAVY_LINUX, "queued"),
        _job("Abschlussmatrix", "queued"),
    ]
    state = watchdog.tracked_state(jobs, (HEAVY_MACOS, HEAVY_LINUX, X86))
    # X86-Job existiert nicht im Lauf: bekannt sind nur die vorhandenen.
    assert state.known == (HEAVY_MACOS, HEAVY_LINUX)
    assert state.queued == (HEAVY_LINUX,)


def test_queue_state_filters_by_prefix_and_status() -> None:
    jobs = [
        _job(MACOS, "queued"),
        _job(LINUX, "in_progress"),
        _job(X86, "completed", "skipped"),
        _job("Abnahme macOS arm64", "queued"),
        _job("Runner-Watchdog (Queue-Abbruch)", "in_progress"),
    ]
    state = watchdog.queue_state(jobs)
    assert state.known == (MACOS, LINUX, X86)
    # Nur der wartende Preflight zaehlt; schwere Jobs und Skips nicht.
    assert state.queued == (MACOS,)
    assert state.observed


def test_watch_returns_immediately_when_all_expected_started() -> None:
    clock = _Clock()
    calls: list[int] = []

    def observe() -> Any:
        calls.append(1)
        return watchdog.queue_state([_job(MACOS, "in_progress")])

    state = watchdog.watch(
        observe, (MACOS,), deadline_s=600, poll_s=20, clock=clock, sleep=clock.sleep,
    )
    assert state.queued == ()
    assert len(calls) == 1
    assert clock.now == 0.0


def test_watch_waits_for_partially_populated_job_list() -> None:
    """Review-Befund PR #924: Zeigt die erste Antwort nur einen Teil der
    erwarteten Preflights (API-Race direkt nach Laufstart), darf der Waechter
    nicht mit „alles gestartet" enden – sonst bliebe der fehlende Job wieder
    unbewacht in der Queue haengen (Lauf 33071408111)."""
    clock = _Clock()
    attempts: list[int] = []

    def observe() -> Any:
        attempts.append(1)
        if len(attempts) == 1:
            # Linux-Eintrag existiert noch nicht.
            return watchdog.queue_state([_job(MACOS, "in_progress")])
        return watchdog.queue_state(
            [_job(MACOS, "in_progress"), _job(LINUX, "in_progress")]
        )

    state = watchdog.watch(
        observe, (MACOS, LINUX), deadline_s=600, poll_s=20,
        clock=clock, sleep=clock.sleep,
    )
    assert state.known == (MACOS, LINUX)
    assert len(attempts) == 2
    assert clock.now == 20.0


def test_watch_reports_still_queued_at_deadline() -> None:
    clock = _Clock()

    def observe() -> Any:
        return watchdog.queue_state([_job(LINUX, "queued")])

    state = watchdog.watch(
        observe, (LINUX,), deadline_s=60, poll_s=20, clock=clock, sleep=clock.sleep,
    )
    assert state.queued == (LINUX,)
    # Frische Beobachtung zum Fristablauf: das Verdikt gilt.
    assert state.observed
    assert clock.now >= 60


def test_watch_recovers_after_transient_api_error() -> None:
    clock = _Clock()
    attempts: list[int] = []

    def observe() -> Any:
        attempts.append(1)
        if len(attempts) == 1:
            raise urllib.error.URLError("api kurz weg")
        return watchdog.queue_state([_job(MACOS, "in_progress")])

    state = watchdog.watch(
        observe, (MACOS,), deadline_s=600, poll_s=20, clock=clock, sleep=clock.sleep,
    )
    assert state.queued == ()
    assert len(attempts) == 2


def test_watch_without_any_observation_gives_no_verdict() -> None:
    clock = _Clock()

    def observe() -> Any:
        raise urllib.error.URLError("api dauerhaft weg")

    state = watchdog.watch(
        observe, (MACOS,), deadline_s=40, poll_s=20, clock=clock, sleep=clock.sleep,
    )
    assert not state.observed
    assert state.queued == ()


def test_watch_stale_queue_observation_gives_no_verdict() -> None:
    """Review-Befund PR #924: Eine bei t=0 beobachtete Queue, danach nur noch
    API-Fehler bis zum Fristablauf – der Runner kann den Job laengst
    uebernommen haben. Ein Verdikt auf minutenalter Grundlage wuerde einen
    gesunden Abnahmelauf force-canceln; stattdessen wird zu observed=False
    degradiert (kein Verdikt, kein Abbruch)."""
    clock = _Clock()
    attempts: list[int] = []

    def observe() -> Any:
        attempts.append(1)
        if len(attempts) == 1:
            return watchdog.queue_state([_job(LINUX, "queued")])
        raise urllib.error.URLError("api ab jetzt weg")

    state = watchdog.watch(
        observe, (LINUX,), deadline_s=100, poll_s=20, clock=clock, sleep=clock.sleep,
    )
    assert not state.observed
    # Die veraltete Beobachtung bleibt als Diagnose sichtbar, traegt aber
    # kein Verdikt mehr.
    assert state.queued == (LINUX,)


def _run_main(
    monkeypatch: pytest.MonkeyPatch,
    jobs: list[dict[str, Any]] | Exception,
    *,
    platforms: str = "alle",
    extra_args: tuple[str, ...] = (),
) -> tuple[int, list[str]]:
    monkeypatch.setenv("GH_TOKEN", "token")
    cancelled: list[str] = []

    def _fetch(repo: str, run_id: str, token: str, *, api_url: str) -> list[dict[str, Any]]:
        if isinstance(jobs, Exception):
            raise jobs
        return jobs

    def _cancel(repo: str, run_id: str, token: str, *, api_url: str) -> None:
        cancelled.append(run_id)

    monkeypatch.setattr(watchdog, "fetch_jobs", _fetch)
    monkeypatch.setattr(watchdog, "force_cancel", _cancel)
    rc = watchdog.main(
        [
            "--repo", "o/r", "--run-id", "42", "--platforms", platforms,
            "--deadline-seconds", "0", "--acceptance-deadline-seconds", "0",
            "--poll-seconds", "1", *extra_args,
        ],
    )
    return rc, cancelled


def test_main_force_cancels_when_preflight_stays_queued(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    rc, cancelled = _run_main(monkeypatch, [_job(LINUX, "queued")])
    out = capsys.readouterr().out
    assert rc == 1
    assert cancelled == ["42"]
    assert "::error title=Self-hosted Runner nicht verfügbar::" in out
    assert "RELEASE_AUTOMATION.md" in out
    assert "force-cancel" in out


def test_main_passes_when_preflights_and_acceptance_jobs_started(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    rc, cancelled = _run_main(
        monkeypatch,
        [
            _job(MACOS, "in_progress"), _job(LINUX, "in_progress"),
            _job(HEAVY_MACOS, "in_progress"), _job(HEAVY_LINUX, "in_progress"),
        ],
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert cancelled == []
    assert "Preflights gestartet" in out
    assert "haben einen Runner" in out


def test_main_force_cancels_when_acceptance_job_stays_queued(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Phase 2 (Codex-Review PR #924): Faellt der Runner zwischen Preflight-
    Ende und Zuweisung des schweren Abnahme-Jobs aus, bricht der Waechter den
    Lauf ebenfalls ab, statt ihn unbewacht queuen zu lassen."""
    rc, cancelled = _run_main(
        monkeypatch,
        [
            _job(MACOS, "completed", "success"), _job(LINUX, "completed", "success"),
            _job(HEAVY_MACOS, "in_progress"), _job(HEAVY_LINUX, "queued"),
        ],
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert cancelled == ["42"]
    assert HEAVY_LINUX in out
    assert "::error title=Self-hosted Runner nicht verfügbar::" in out


def test_main_treats_skipped_acceptance_job_as_terminal(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    # Ein wegen fehlgeschlagenem Preflight geskippter Abnahme-Job beendet die
    # Ueberwachung (der Lauf wird ohnehin rot), statt sie festzuhalten.
    rc, cancelled = _run_main(
        monkeypatch,
        [
            _job(MACOS, "completed", "success"), _job(LINUX, "completed", "failure"),
            _job(HEAVY_MACOS, "in_progress"), _job(HEAVY_LINUX, "completed", "skipped"),
        ],
    )
    assert rc == 0
    assert cancelled == []


def test_main_warns_when_expected_job_never_appears(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Ein erwarteter Preflight, der bis Fristablauf nie in der Jobliste
    erscheint, ist nicht beurteilbar: Warnung statt Verdikt (fail-safe)."""
    rc, cancelled = _run_main(monkeypatch, [_job(MACOS, "in_progress")])
    out = capsys.readouterr().out
    assert rc == 0
    assert cancelled == []
    assert "nie in der Jobliste erschienen" in out
    assert LINUX in out


def test_main_is_failsafe_without_observation(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    rc, cancelled = _run_main(monkeypatch, urllib.error.URLError("api weg"))
    out = capsys.readouterr().out
    assert rc == 0
    assert cancelled == []
    assert "kein Verdikt" in out


def test_main_paused_x86_only_run_is_a_noop(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    # platforms=linux-x86_64 ohne --x86-64-enabled: der Preflight-Job ist
    # uebersprungen, es gibt nichts zu ueberwachen (und nichts abzubrechen).
    rc, cancelled = _run_main(monkeypatch, [], platforms="linux-x86_64")
    assert rc == 0
    assert cancelled == []
    assert "nichts zu überwachen" in capsys.readouterr().out


def test_main_expects_x86_preflight_when_enabled(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    rc, cancelled = _run_main(
        monkeypatch, [_job(X86, "queued")],
        platforms="linux-x86_64", extra_args=("--x86-64-enabled",),
    )
    assert rc == 1
    assert cancelled == ["42"]


def test_main_requires_token(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    rc = watchdog.main(["--repo", "o/r", "--run-id", "42", "--platforms", "alle"])
    assert rc == 1
    assert "GH_TOKEN" in capsys.readouterr().out


def test_retired_platforms_are_not_expected() -> None:
    """#958: Eine per Heartbeat-Eskalation ausgetragene Plattform ist im
    Workflow uebersprungen – der Watchdog wartete sonst zehn Minuten auf
    einen Preflight, den es nicht gibt, und braeche den Lauf ab."""
    retired = watchdog.parse_retired(["macos-arm64=2026-09-01", "linux-arm64=", "linux-x86_64="])
    assert retired == ("macos-arm64",)
    assert watchdog.expected_preflights("alle", x86_enabled=False, retired=retired) == (LINUX,)
    assert watchdog.expected_acceptance("alle", x86_enabled=True, retired=retired) == (
        HEAVY_LINUX, watchdog.ACCEPTANCE_JOB_NAMES["linux-x86_64"],
    )
    # Ein Einzelplattform-Lauf auf der ausgetragenen Plattform hat nichts zu bewachen.
    assert watchdog.expected_preflights("macos-arm64", x86_enabled=False, retired=retired) == ()
    with pytest.raises(ValueError, match="kein ISO-Datum"):
        watchdog.parse_retired(["macos-arm64=neulich"])
    with pytest.raises(ValueError, match="erwartet <plattform>=<datum>"):
        watchdog.parse_retired(["mac"])


def test_main_retired_platform_run_is_a_noop(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    rc, cancelled = _run_main(
        monkeypatch, [_job(MACOS, "queued")], platforms="macos-arm64",
        extra_args=("--retired-since", "macos-arm64=2026-09-01"),
    )
    assert rc == 0
    assert cancelled == []
    assert "nichts zu überwachen" in capsys.readouterr().out


def test_main_rejects_an_unreadable_retirement_date(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    rc, cancelled = _run_main(
        monkeypatch, [_job(MACOS, "queued")], platforms="alle",
        extra_args=("--retired-since", "macos-arm64=bald"),
    )
    assert rc == 1
    assert cancelled == []
    assert "kein ISO-Datum" in capsys.readouterr().out
