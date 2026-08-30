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


def _job(name: str, status: str = "queued", conclusion: str | None = None) -> dict[str, Any]:
    return {"name": name, "status": status, "conclusion": conclusion}


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def test_queue_state_filters_by_prefix_and_status() -> None:
    jobs = [
        _job("Preflight macOS arm64", "queued"),
        _job("Preflight Linux aarch64", "in_progress"),
        _job("Preflight Linux x86_64", "completed", "skipped"),
        _job("Abnahme macOS arm64", "queued"),
        _job("Runner-Watchdog (Queue-Abbruch)", "in_progress"),
    ]
    state = watchdog.queue_state(jobs)
    assert state.known == (
        "Preflight macOS arm64", "Preflight Linux aarch64", "Preflight Linux x86_64",
    )
    # Nur der wartende Preflight zaehlt; schwere Jobs und Skips nicht.
    assert state.queued == ("Preflight macOS arm64",)
    assert state.observed


def test_watch_returns_immediately_when_nothing_queued() -> None:
    clock = _Clock()
    calls: list[int] = []

    def observe() -> Any:
        calls.append(1)
        return watchdog.queue_state([_job("Preflight macOS arm64", "in_progress")])

    state = watchdog.watch(
        observe, deadline_s=600, poll_s=20, clock=clock, sleep=clock.sleep,
    )
    assert state.queued == ()
    assert len(calls) == 1
    assert clock.now == 0.0


def test_watch_reports_still_queued_at_deadline() -> None:
    clock = _Clock()

    def observe() -> Any:
        return watchdog.queue_state([_job("Preflight Linux aarch64", "queued")])

    state = watchdog.watch(
        observe, deadline_s=60, poll_s=20, clock=clock, sleep=clock.sleep,
    )
    assert state.queued == ("Preflight Linux aarch64",)
    assert clock.now >= 60


def test_watch_recovers_after_transient_api_error() -> None:
    clock = _Clock()
    attempts: list[int] = []

    def observe() -> Any:
        attempts.append(1)
        if len(attempts) == 1:
            raise urllib.error.URLError("api kurz weg")
        return watchdog.queue_state([_job("Preflight macOS arm64", "in_progress")])

    state = watchdog.watch(
        observe, deadline_s=600, poll_s=20, clock=clock, sleep=clock.sleep,
    )
    assert state.queued == ()
    assert len(attempts) == 2


def test_watch_gives_empty_job_list_a_second_chance() -> None:
    # Direkt nach Laufstart kann die Jobliste noch unvollstaendig sein (API-
    # Race): erst zwei aufeinanderfolgende Leer-Beobachtungen beenden die
    # Ueberwachung als "nichts zu ueberwachen".
    clock = _Clock()
    attempts: list[int] = []

    def observe() -> Any:
        attempts.append(1)
        return watchdog.queue_state([])

    state = watchdog.watch(
        observe, deadline_s=600, poll_s=20, clock=clock, sleep=clock.sleep,
    )
    assert state.known == ()
    assert len(attempts) == 2
    assert clock.now == 20.0


def test_watch_without_any_observation_gives_no_verdict() -> None:
    clock = _Clock()

    def observe() -> Any:
        raise urllib.error.URLError("api dauerhaft weg")

    state = watchdog.watch(
        observe, deadline_s=40, poll_s=20, clock=clock, sleep=clock.sleep,
    )
    assert not state.observed
    assert state.queued == ()


def _run_main(
    monkeypatch: pytest.MonkeyPatch, jobs: list[dict[str, Any]] | Exception,
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
        ["--repo", "o/r", "--run-id", "42", "--deadline-seconds", "0", "--poll-seconds", "1"],
    )
    return rc, cancelled


def test_main_force_cancels_when_preflight_stays_queued(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    rc, cancelled = _run_main(monkeypatch, [_job("Preflight Linux aarch64", "queued")])
    out = capsys.readouterr().out
    assert rc == 1
    assert cancelled == ["42"]
    assert "::error title=Self-hosted Runner nicht verfügbar::" in out
    assert "RELEASE_AUTOMATION.md" in out
    assert "force-cancel" in out


def test_main_passes_when_all_preflights_started(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    rc, cancelled = _run_main(monkeypatch, [_job("Preflight macOS arm64", "in_progress")])
    assert rc == 0
    assert cancelled == []
    assert "haben einen Runner" in capsys.readouterr().out


def test_main_is_failsafe_without_observation(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    rc, cancelled = _run_main(monkeypatch, urllib.error.URLError("api weg"))
    out = capsys.readouterr().out
    assert rc == 0
    assert cancelled == []
    assert "kein Verdikt" in out


def test_main_without_preflight_jobs_is_a_noop(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    rc, cancelled = _run_main(monkeypatch, [_job("Abnahme macOS arm64", "queued")])
    assert rc == 0
    assert cancelled == []
    assert "nichts zu überwachen" in capsys.readouterr().out


def test_main_requires_token(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    rc = watchdog.main(["--repo", "o/r", "--run-id", "42"])
    assert rc == 1
    assert "GH_TOKEN" in capsys.readouterr().out
