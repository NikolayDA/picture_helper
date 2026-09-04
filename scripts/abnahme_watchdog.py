#!/usr/bin/env python3
"""Queue-Watchdog der Release-Abnahme (#915, Epic #914).

Läuft GitHub-hosted parallel zu den Self-hosted-Jobs von
``release-abnahme.yml`` und bewacht deren Queue-Phasen in zwei Stufen:
zuerst die Preflights (kurze Frist ab Dispatch), danach die schweren
Abnahme-Jobs bis zu ihrem Start (längere Frist, weil sie erst nach
``candidate-source`` einplanbar sind; Codex-Review PR #924 – sonst bliebe
ein Runner-Ausfall zwischen Preflight-Ende und Job-Zuweisung unbewacht).
Bleibt ein bewachter Job nach Ablauf seiner Frist ohne Runner-Zuweisung
(Status ``queued``), beendet der Wächter den gesamten Lauf per
**force-cancel** – mit einer ``::error``-Annotation, die die wartenden Jobs
und den Abhilfeweg benennt. Hintergrund: GitHub bricht Jobs ohne
verfügbaren Self-hosted-Runner erst nach 24 h ab, und ``timeout-minutes``
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
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from datetime import date
from typing import Any

JOB_NAME_PREFIX = "Preflight "
API_VERSION = "2022-11-28"
DEFAULT_DEADLINE_S = 600
# Zweite Phase (Codex-Review PR #924): Auch die schweren Abnahme-Jobs werden
# bis zu ihrem Start bewacht. Sie werden erst nach candidate-source
# (timeout-minutes: 15) einplanbar – die Frist muss das abdecken, sonst
# wuerde ein gesunder, nur langsamer Lauf faelschlich abgebrochen.
DEFAULT_ACCEPTANCE_DEADLINE_S = 1500
DEFAULT_POLL_S = 20
REQUEST_TIMEOUT_S = 30.0

# Anzeige-Namen der Preflight- und Abnahme-Jobs in release-abnahme.yml. Die
# erwartete Menge wird aus den Dispatch-Eingaben abgeleitet (Review-Befund
# PR #924): eine direkt nach Laufstart noch unvollstaendige Jobliste darf den
# Wächter nicht vorzeitig mit „alles gestartet" beenden. Namensdrift zwischen
# diesen Tabellen und dem Workflow faengt tests/test_abnahme_watchdog.py ab.
PREFLIGHT_JOB_NAMES: dict[str, str] = {
    "macos-arm64": "Preflight macOS arm64",
    "linux-arm64": "Preflight Linux aarch64",
    "linux-x86_64": "Preflight Linux x86_64",
}
ACCEPTANCE_JOB_NAMES: dict[str, str] = {
    "macos-arm64": "Abnahme macOS arm64",
    "linux-arm64": "Abnahme Linux aarch64",
    "linux-x86_64": "Abnahme Linux x86_64",
}


def _expected_platforms(
    platforms: str, *, x86_enabled: bool, retired: Iterable[str] = (),
) -> tuple[str, ...]:
    """Aktive Plattformen eines Laufs; spiegelt die ``if``-Bedingungen der Jobs.

    ``alle`` umfasst macOS und Linux arm64, x86_64 nur bei gesetzter
    Repository-Variable (sonst sind die Jobs übersprungen und dürfen nicht
    erwartet werden). Eine **ausgetragene** Plattform (Heartbeat-Eskalation
    Stufe 3, #958: ``RUNNER_<PLATTFORM>_RETIRED_SINCE`` gesetzt) ist ebenso
    übersprungen – der Watchdog wartete sonst zehn Minuten auf einen
    Preflight, den der Workflow gar nicht erzeugt, und bräche den Lauf ab.
    """
    if platforms == "alle":
        wanted = ["macos-arm64", "linux-arm64"]
        if x86_enabled:
            wanted.append("linux-x86_64")
    elif platforms == "linux-x86_64" and not x86_enabled:
        wanted = []
    else:
        wanted = [platforms]
    excluded = set(retired)
    return tuple(platform for platform in wanted if platform not in excluded)


def parse_retired(values: Iterable[str]) -> tuple[str, ...]:
    """``<plattform>=<datum>``-Angaben (leerer Wert = aktiv) zu Plattformen.

    Dieselbe Form wie beim Heartbeat, damit der Workflow beiden Skripten
    dieselben Repository-Variablen unveraendert durchreicht. Das Datum
    braucht der Watchdog nicht, ein unlesbares ist trotzdem ein Befund.
    """
    retired: list[str] = []
    for value in values:
        platform, sep, raw = value.partition("=")
        platform = platform.strip()
        if not sep or platform not in PREFLIGHT_JOB_NAMES:
            raise ValueError(
                f"--retired-since erwartet <plattform>=<datum> mit einer der Plattformen "
                f"{', '.join(PREFLIGHT_JOB_NAMES)}, nicht {value!r}"
            )
        raw = raw.strip()
        if not raw:
            continue
        try:
            date.fromisoformat(raw)
        except ValueError as exc:
            raise ValueError(f"{value!r}: {raw!r} ist kein ISO-Datum (YYYY-MM-DD)") from exc
        retired.append(platform)
    return tuple(retired)


def expected_preflights(
    platforms: str, *, x86_enabled: bool, retired: Iterable[str] = (),
) -> tuple[str, ...]:
    """Erwartete Preflight-Jobnamen eines Laufs aus den Dispatch-Eingaben."""
    return tuple(
        PREFLIGHT_JOB_NAMES[platform]
        for platform in _expected_platforms(platforms, x86_enabled=x86_enabled, retired=retired)
    )


def expected_acceptance(
    platforms: str, *, x86_enabled: bool, retired: Iterable[str] = (),
) -> tuple[str, ...]:
    """Erwartete Abnahme-Jobnamen (schwere Plattform-Jobs) desselben Laufs."""
    return tuple(
        ACCEPTANCE_JOB_NAMES[platform]
        for platform in _expected_platforms(platforms, x86_enabled=x86_enabled, retired=retired)
    )


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


def tracked_state(jobs: list[dict[str, Any]], names: tuple[str, ...]) -> QueueState:
    """Zustand einer exakt benannten Jobmenge (z. B. der schweren Abnahme-Jobs).

    Übersprungene/beendete Jobs zählen als bekannt, aber nicht als wartend –
    ein wegen fehlgeschlagenem Preflight geskippter Abnahme-Job beendet die
    Überwachung, statt sie festzuhalten.
    """
    present = {str(job.get("name", "")): str(job.get("status", "")) for job in jobs}
    known = tuple(name for name in names if name in present)
    queued = tuple(name for name in known if present[name] == "queued")
    return QueueState(known=known, queued=queued)


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
    expected: tuple[str, ...],
    *,
    deadline_s: float,
    poll_s: float,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> QueueState:
    """Preflight-Queue bis Start aller **erwarteten** Jobs oder Fristablauf
    beobachten.

    Der Erfolgs-Exit verlangt, dass jeder erwartete Job in der Liste
    erschienen **und** nicht mehr ``queued`` ist – eine direkt nach
    Laufstart noch unvollständige Jobliste (API-Race) beendet die
    Überwachung nicht vorzeitig (Review-Befund PR #924).

    Rückgabe ist die letzte erfolgreiche Beobachtung; gab es nie eine,
    trägt sie ``observed=False`` (kein Verdikt, siehe Modul-Docstring).
    Ein Queue-Verdikt zum Fristablauf braucht eine **frische** Beobachtung
    (jünger als ``2 * poll_s``): War die letzte erfolgreiche Abfrage älter
    (API-Ausfall dazwischen), wird sie zu ``observed=False`` degradiert,
    statt auf veralteter Grundlage abzubrechen – der Runner kann den Job
    längst übernommen haben.
    """
    start = clock()
    last = QueueState(known=(), queued=(), observed=False)
    last_success: float | None = None
    while True:
        try:
            last = observe()
        except (urllib.error.URLError, OSError, ValueError) as exc:
            print(f"::warning::Watchdog: Jobabfrage fehlgeschlagen ({exc}).")
        else:
            last_success = clock()
            if not last.queued and set(expected).issubset(last.known):
                return last
        if clock() - start >= deadline_s:
            stale = last_success is None or clock() - last_success > 2 * poll_s
            if last.queued and stale:
                return replace(last, observed=False)
            return last
        sleep(poll_s)


def _phase_verdict(
    state: QueueState,
    expected: tuple[str, ...],
    *,
    deadline_s: float,
    phase: str,
    cancel: Callable[[], None],
) -> int | None:
    """Watch-Ergebnis einer Phase bewerten.

    ``None`` = alle erwarteten Jobs sind gestartet (nächste Phase darf
    folgen); sonst der Exit-Code: ``0`` für die fail-safe Pfade ohne Verdikt
    (keine frische Beobachtung, erwartete Jobs nie erschienen – Letzteres
    ist API-Anomalie oder Namensdrift, den Drift fängt der Paritäts-Test
    ab), ``1`` nach force-cancel wegen wartender Jobs.
    """
    if not state.observed:
        print(
            f"::warning::Watchdog ({phase}): Queue war zum Fristablauf nicht "
            "frisch beobachtbar (API-Fehler) – kein Verdikt, Lauf bleibt "
            "unangetastet."
        )
        return 0
    if not state.queued:
        missing = tuple(name for name in expected if name not in state.known)
        if missing:
            print(
                f"::warning::Watchdog ({phase}): erwartete Jobs nie in der "
                f"Jobliste erschienen: {', '.join(missing)} – keine "
                "Überwachung möglich, Lauf bleibt unangetastet."
            )
            return 0
        return None
    names = ", ".join(state.queued)
    print(
        f"::error title=Self-hosted Runner nicht verfügbar::{names} wartet nach "
        f"{deadline_s:.0f} s weiterhin auf einen Runner (GitHub bräche "
        "erst nach 24 h ab). Runner prüfen: docs/RELEASE_AUTOMATION.md §2/§6. "
        "Danach die Abnahme mit unveränderten Eingaben neu dispatchen – reiner "
        "Runnerfehler, kein neuer Kandidat nötig (Runbook Schritt 5)."
    )
    try:
        cancel()
        print(
            "[watchdog] Lauf per force-cancel beendet (ein regulärer Cancel ließe "
            "die Aggregation weiterlaufen und eine irreführende Matrix posten)."
        )
    except (urllib.error.URLError, OSError) as exc:
        print(f"::warning::Watchdog: force-cancel fehlgeschlagen ({exc}).")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/repo des laufenden Workflows")
    parser.add_argument("--run-id", required=True, help="GITHUB_RUN_ID des laufenden Workflows")
    parser.add_argument(
        "--platforms", required=True,
        choices=("alle", *PREFLIGHT_JOB_NAMES),
        help="platforms-Dispatch-Eingabe des Laufs (bestimmt die erwarteten Jobs)",
    )
    parser.add_argument("--x86-64-enabled", action="store_true")
    parser.add_argument(
        "--retired-since", action="append", default=[], metavar="PLATTFORM=DATUM",
        help="Ausgetragene Plattform (#958, RUNNER_<PLATTFORM>_RETIRED_SINCE); leer = aktiv.",
    )
    parser.add_argument("--deadline-seconds", type=float, default=DEFAULT_DEADLINE_S)
    parser.add_argument(
        "--acceptance-deadline-seconds", type=float,
        default=DEFAULT_ACCEPTANCE_DEADLINE_S,
        help="Frist der zweiten Phase (schwere Abnahme-Jobs), ab Phasenstart; "
        "muss die candidate-source-Laufzeit (timeout-minutes: 15) abdecken",
    )
    parser.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_S)
    parser.add_argument("--job-prefix", default=JOB_NAME_PREFIX)
    args = parser.parse_args(argv)

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        print("::error::Watchdog: GH_TOKEN/GITHUB_TOKEN fehlt.")
        return 1
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")

    try:
        retired = parse_retired(args.retired_since)
    except ValueError as exc:
        print(f"::error::Watchdog: {exc}")
        return 1
    expected_pre = expected_preflights(
        args.platforms, x86_enabled=args.x86_64_enabled, retired=retired,
    )
    expected_heavy = expected_acceptance(
        args.platforms, x86_enabled=args.x86_64_enabled, retired=retired,
    )
    if not expected_pre:
        print(
            f"[watchdog] Für platforms={args.platforms!r} läuft kein Preflight "
            "(pausiert oder ausgetragen) – nichts zu überwachen."
        )
        return 0

    def observe_preflights() -> QueueState:
        return queue_state(
            fetch_jobs(args.repo, args.run_id, token, api_url=api_url),
            prefix=args.job_prefix,
        )

    def observe_acceptance() -> QueueState:
        return tracked_state(
            fetch_jobs(args.repo, args.run_id, token, api_url=api_url),
            expected_heavy,
        )

    def cancel() -> None:
        force_cancel(args.repo, args.run_id, token, api_url=api_url)

    # Phase 1: Preflights muessen binnen kurzer Frist einen Runner bekommen.
    state = watch(
        observe_preflights, expected_pre,
        deadline_s=args.deadline_seconds, poll_s=args.poll_seconds,
    )
    verdict = _phase_verdict(
        state, expected_pre,
        deadline_s=args.deadline_seconds, phase="Preflight", cancel=cancel,
    )
    if verdict is not None:
        return verdict
    print(f"[watchdog] Preflights gestartet: {', '.join(expected_pre)}")

    # Phase 2 (Codex-Review PR #924): Die schweren Abnahme-Jobs werden erst
    # nach candidate-source einplanbar; faellt der Runner zwischen Preflight-
    # Ende und ihrer Zuweisung aus, hingen sie sonst wieder unbewacht in der
    # Queue. Die laengere Frist deckt die candidate-source-Laufzeit ab.
    state = watch(
        observe_acceptance, expected_heavy,
        deadline_s=args.acceptance_deadline_seconds, poll_s=args.poll_seconds,
    )
    verdict = _phase_verdict(
        state, expected_heavy,
        deadline_s=args.acceptance_deadline_seconds, phase="Abnahme", cancel=cancel,
    )
    if verdict is not None:
        return verdict
    print(
        f"[watchdog] Alle erwarteten Abnahme-Jobs haben einen Runner: "
        f"{', '.join(expected_heavy)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
