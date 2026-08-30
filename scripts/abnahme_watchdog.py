#!/usr/bin/env python3
"""Queue-Watchdog der Release-Abnahme (#915, Epic #914).

Läuft GitHub-hosted parallel zu den Preflight-Jobs von
``release-abnahme.yml``: Bleibt ein Preflight nach Ablauf der Frist ohne
Runner-Zuweisung (Status ``queued``), beendet dieser Wächter den gesamten
Lauf per **force-cancel** – mit einer ``::error``-Annotation, die die
wartenden Jobs und den Abhilfeweg benennt. Hintergrund: GitHub bricht Jobs
ohne verfügbaren Self-hosted-Runner erst nach 24 h ab, und ``timeout-minutes``
zählt erst ab Jobstart – gegen die Queue-Phase schützt es nicht (beobachtet:
7:58 h Warteschlange in Lauf 33071408111, Release v2.9.0/#881).

Force-cancel statt cancel: Ein regulärer Cancel lässt ``if: always()``- bzw.
``!cancelled()``-Jobs (die Aggregation) weiterlaufen – genau daraus entstand
die missverständliche Abschlussmatrix des abgebrochenen Laufs.
``POST …/actions/runs/{id}/force-cancel`` beendet auch diese Jobs.

Fail-safe für den Wächter selbst: Kann die Job-Liste nicht beobachtet werden
(API-Fehler), wird **nicht** abgebrochen – ein Wächter ohne Beobachtung fällt
nie ein Verdikt. Das gilt auch für **veraltete** Beobachtungen
(Review-Befund PR #924): Abgebrochen wird nur, wenn eine *frische*
Beobachtung (jünger als zwei Poll-Intervalle) zum Fristablauf weiterhin
wartende Preflights zeigt – eine minutenalte Queue-Beobachtung kann längst
überholt sein, und ein fälschlicher Abbruch kostet den gesamten
Hardware-Abnahmelauf.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

JOB_NAME_PREFIX = "Preflight "
API_VERSION = "2022-11-28"
DEFAULT_DEADLINE_S = 600
DEFAULT_POLL_S = 20
REQUEST_TIMEOUT_S = 30.0


@dataclass(frozen=True)
class QueueState:
    """Beobachtung der Preflight-Jobs eines Laufs."""

    known: tuple[str, ...]
    queued: tuple[str, ...]
    observed: bool = True


def queue_state(
    jobs: list[dict[str, Any]], *, prefix: str = JOB_NAME_PREFIX,
) -> QueueState:
    """Preflight-Jobs (Namenspräfix) und ihren Queue-Zustand extrahieren.

    Übersprungene Jobs (``status == completed``/``conclusion == skipped``,
    z. B. pausiertes x86_64) zählen als bekannt, aber nicht als wartend.
    """
    known: list[str] = []
    queued: list[str] = []
    for job in jobs:
        name = str(job.get("name", ""))
        if not name.startswith(prefix):
            continue
        known.append(name)
        if str(job.get("status", "")) == "queued":
            queued.append(name)
    return QueueState(known=tuple(known), queued=tuple(queued))


def _request(url: str, token: str, *, method: str = "GET") -> urllib.request.Request:
    return urllib.request.Request(
        url,
        method=method,
        data=b"" if method == "POST" else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "bgremover-abnahme-watchdog",
        },
    )


def fetch_jobs(
    repo: str,
    run_id: str,
    token: str,
    *,
    api_url: str,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[dict[str, Any]]:
    """Jobs des aktuellen Versuchs laden (ein Lauf hat weit unter 100 Jobs)."""
    url = f"{api_url}/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100"
    with opener(_request(url, token), timeout=REQUEST_TIMEOUT_S) as response:
        payload = json.load(response)
    jobs = payload.get("jobs")
    return [job for job in jobs if isinstance(job, dict)] if isinstance(jobs, list) else []


def force_cancel(
    repo: str,
    run_id: str,
    token: str,
    *,
    api_url: str,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> None:
    """Lauf hart beenden – auch ``always()``-/``!cancelled()``-Jobs."""
    url = f"{api_url}/repos/{repo}/actions/runs/{run_id}/force-cancel"
    with opener(_request(url, token, method="POST"), timeout=REQUEST_TIMEOUT_S):
        pass


def watch(
    observe: Callable[[], QueueState],
    *,
    deadline_s: float,
    poll_s: float,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> QueueState:
    """Preflight-Queue bis Start aller Jobs oder Fristablauf beobachten.

    Rückgabe ist die letzte erfolgreiche Beobachtung; gab es nie eine,
    trägt sie ``observed=False`` (kein Verdikt, siehe Modul-Docstring).
    Ein Queue-Verdikt zum Fristablauf braucht eine **frische** Beobachtung
    (jünger als ``2 * poll_s``): War die letzte erfolgreiche Abfrage älter
    (API-Ausfall dazwischen), wird sie zu ``observed=False`` degradiert,
    statt auf veralteter Grundlage abzubrechen – der Runner kann den Job
    längst übernommen haben (Review-Befund PR #924).
    Eine leere Preflight-Jobliste direkt nach Laufstart kann ein API-Race
    sein – erst zwei aufeinanderfolgende Leer-Beobachtungen gelten als
    „nichts zu überwachen".
    """
    start = clock()
    last = QueueState(known=(), queued=(), observed=False)
    last_success: float | None = None
    empty_known_streak = 0
    while True:
        try:
            last = observe()
        except (urllib.error.URLError, OSError, ValueError) as exc:
            print(f"::warning::Watchdog: Jobabfrage fehlgeschlagen ({exc}).")
        else:
            last_success = clock()
            if last.known:
                empty_known_streak = 0
                if not last.queued:
                    return last
            else:
                empty_known_streak += 1
                if empty_known_streak >= 2:
                    return last
        if clock() - start >= deadline_s:
            stale = last_success is None or clock() - last_success > 2 * poll_s
            if last.queued and stale:
                return replace(last, observed=False)
            return last
        sleep(poll_s)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/repo des laufenden Workflows")
    parser.add_argument("--run-id", required=True, help="GITHUB_RUN_ID des laufenden Workflows")
    parser.add_argument("--deadline-seconds", type=float, default=DEFAULT_DEADLINE_S)
    parser.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_S)
    parser.add_argument("--job-prefix", default=JOB_NAME_PREFIX)
    args = parser.parse_args(argv)

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        print("::error::Watchdog: GH_TOKEN/GITHUB_TOKEN fehlt.")
        return 1
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")

    def observe() -> QueueState:
        return queue_state(
            fetch_jobs(args.repo, args.run_id, token, api_url=api_url),
            prefix=args.job_prefix,
        )

    state = watch(
        observe, deadline_s=args.deadline_seconds, poll_s=args.poll_seconds,
    )
    if not state.observed:
        print(
            "::warning::Watchdog: Preflight-Queue war zum Fristablauf nicht "
            "frisch beobachtbar (API-Fehler) – kein Verdikt, Lauf bleibt "
            "unangetastet."
        )
        return 0
    if not state.known:
        print("[watchdog] Keine Preflight-Jobs in diesem Lauf – nichts zu überwachen.")
        return 0
    if not state.queued:
        print(
            f"[watchdog] Alle Preflight-Jobs haben einen Runner: {', '.join(state.known)}"
        )
        return 0
    names = ", ".join(state.queued)
    print(
        f"::error title=Self-hosted Runner nicht verfügbar::{names} wartet nach "
        f"{args.deadline_seconds:.0f} s weiterhin auf einen Runner (GitHub bräche "
        "erst nach 24 h ab). Runner prüfen: docs/RELEASE_AUTOMATION.md §2/§6. "
        "Danach die Abnahme mit unveränderten Eingaben neu dispatchen – reiner "
        "Runnerfehler, kein neuer Kandidat nötig (Runbook Schritt 5)."
    )
    try:
        force_cancel(args.repo, args.run_id, token, api_url=api_url)
        print(
            "[watchdog] Lauf per force-cancel beendet (ein regulärer Cancel ließe "
            "die Aggregation weiterlaufen und eine irreführende Matrix posten)."
        )
    except (urllib.error.URLError, OSError) as exc:
        print(f"::warning::Watchdog: force-cancel fehlgeschlagen ({exc}).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
