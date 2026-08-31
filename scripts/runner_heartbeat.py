#!/usr/bin/env python3
"""Täglicher Runner-Heartbeat der Release-Abnahme (#921, Epic #914).

Ergänzt den Lauf-Watchdog aus #915 um die Zeit **zwischen** den Läufen: Der
v2.9.0-Verzug entstand, weil der Pi-Runner tagelang offline war und das erst
beim Abnahme-Dispatch auffiel (#881). Ein Watchdog bricht dann schnell ab,
verkürzt die Entdeckungszeit aber nicht — dieses Skript trägt die
Gegenrichtung: Ein geplanter Lauf beschäftigt jeden Runner minimal, und
bleibt einer davon in der Warteschlange, fällt das binnen eines Tages auf.

Zwei Unterkommandos, beide netzarm und nur Standardbibliothek:

``pause-status``
    Bewertet die Repository-Variablen des Wartungsfensters. Eine Pause ist
    **sichtbar** (Warnung + Job-Summary) und **befristet**: ohne gültiges,
    in der Zukunft liegendes Enddatum ist die Pause selbst der Befund. Eine
    unbefristete Pause wäre sonst genau der stille Zustand, den dieses Issue
    abschafft — die Alarmanlage bliebe abgeschaltet, und niemand sähe es.

``watch``
    Beobachtet GitHub-hosted die Heartbeat-Jobs desselben Laufs und meldet
    **beide** Hälften des Signals: den Runner, der den Job gar nicht erst
    annimmt (``queued`` zum Fristablauf), und den, der ihn annimmt und an der
    Bereitschaftsprüfung scheitert (``conclusion`` ``failure``/``timed_out``).
    Die zweite Hälfte braucht den Umweg über die Jobs-API, weil
    ``if: failure()`` in einem Schritt laut GitHub-Referenz nur auf vorherige
    Schritte **desselben** Jobs (und Vorgängerjobs per ``needs``) reagiert –
    die Runner-Jobs sind bewusst keine Vorgänger. Fail-safe wie
    ``abnahme_watchdog.py``: Ohne **frische** Beobachtung (API-Ausfall) gibt
    es kein Verdikt — ein Monitor, der nicht beobachten kann, schlägt keinen
    Alarm, sonst verliert der Alarm seinen Wert.

Anders als der Lauf-Watchdog bricht der Heartbeat **nichts** ab: Er meldet.
Gegen auflaufende Warteschlangen-Jobs schützt stattdessen ``concurrency``
mit ``cancel-in-progress`` im Workflow — der Lauf des nächsten Tages beendet
den noch wartenden von heute.
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
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Final

API_VERSION: Final = "2022-11-28"
REQUEST_TIMEOUT_S: Final = 30.0
# Zwei Fristen, weil zwei verschiedene Fragen (#921-Nachpruefung). Eine
# einzige Frist beantwortete beide falsch: Die Doku versprach "meldet, wenn
# einer den Job nicht binnen 15 Minuten annimmt", die Auswertung wartete aber
# das volle Fenster ab und meldete "wartet nach 1500 s".
#: Bis hierhin muss ein Runner den Job **angenommen** haben. Laeuft sie ab,
#: waehrend ein Job noch ``queued`` ist, steht das Offline-Verdikt sofort
#: fest - auf das Gesamtfenster zu warten verzoegerte nur die Meldung.
DEFAULT_ACCEPTANCE_S: Final = 900
#: Bis hierhin muss die **Bereitschaftspruefung** abgeschlossen sein:
#: Annahmefrist (15 min) plus das Jobbudget des Readiness-Jobs (10 min).
#: Laeuft ein Job darueber hinaus, gibt es kein Verdikt statt eines geratenen.
DEFAULT_DEADLINE_S: Final = 1500
DEFAULT_POLL_S: Final = 20

REPORT_SCHEMA: Final = 1
REPORT_KIND: Final = "runner-heartbeat"

VERDICT_PASS: Final = "PASS"
VERDICT_FAIL: Final = "FAIL"
VERDICT_UNOBSERVED: Final = "UNOBSERVED"
VERDICT_PAUSED: Final = "PAUSED"

# Anzeige-Namen der Heartbeat-Jobs in ``runner-heartbeat.yml``. Namensdrift
# zwischen dieser Tabelle und dem Workflow macht die Beobachtung wirkungslos
# (der Wächter fände seine Jobs nicht); ``tests/test_runner_heartbeat.py``
# hält beide gegeneinander – dasselbe Muster wie beim Lauf-Watchdog.
HEARTBEAT_JOB_NAMES: Final[dict[str, str]] = {
    "macos-arm64": "Heartbeat macOS arm64",
    "linux-arm64": "Heartbeat Linux aarch64",
    "linux-x86_64": "Heartbeat Linux x86_64",
}
PAUSE_VARIABLE: Final = "RUNNER_HEARTBEAT_PAUSED"
PAUSE_UNTIL_VARIABLE: Final = "RUNNER_HEARTBEAT_PAUSED_UNTIL"


# ── Wartungsfenster ────────────────────────────────────────────────────


@dataclass(frozen=True)
class PauseState:
    """Bewertetes Wartungsfenster aus den beiden Repository-Variablen."""

    paused: bool
    until: date | None
    ok: bool
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "paused": self.paused,
            "until": self.until.isoformat() if self.until is not None else None,
            "ok": self.ok,
            "detail": self.detail,
        }


def pause_state(*, paused_raw: str, until_raw: str, today: date) -> PauseState:
    """Wertet Pausenvariable und Enddatum aus.

    ``ok=False`` heißt: Die Pause selbst ist der Befund. Der Heartbeat bleibt
    dann trotzdem pausiert (ein laufendes Wartungsfenster soll keinen
    Fehlalarm erzeugen), aber der Lauf wird rot — die vergessene Pause fällt
    damit täglich auf, statt die Überwachung stillzulegen.
    """
    if paused_raw.strip().lower() != "true":
        return PauseState(
            paused=False, until=None, ok=True,
            detail=f"{PAUSE_VARIABLE} ist nicht gesetzt – Heartbeat aktiv.",
        )
    text = until_raw.strip()
    if not text:
        return PauseState(
            paused=True, until=None, ok=False,
            detail=(
                f"{PAUSE_VARIABLE}=true ohne {PAUSE_UNTIL_VARIABLE}: ein "
                "Wartungsfenster ohne Ende ist keine Pause, sondern eine "
                "abgeschaltete Überwachung. Enddatum (YYYY-MM-DD) setzen "
                "oder die Pause aufheben."
            ),
        )
    try:
        until = date.fromisoformat(text)
    except ValueError:
        return PauseState(
            paused=True, until=None, ok=False,
            detail=(
                f"{PAUSE_UNTIL_VARIABLE}={text!r} ist kein ISO-Datum "
                "(YYYY-MM-DD) – Pause nicht bewertbar."
            ),
        )
    if until < today:
        return PauseState(
            paused=True, until=until, ok=False,
            detail=(
                f"Wartungsfenster endete am {until.isoformat()} und gilt noch "
                f"immer ({PAUSE_VARIABLE}=true). Pause aufheben oder "
                f"{PAUSE_UNTIL_VARIABLE} verlängern."
            ),
        )
    return PauseState(
        paused=True, until=until, ok=True,
        detail=f"Heartbeat pausiert bis einschließlich {until.isoformat()}.",
    )


# ── Beobachtung der Heartbeat-Jobs ─────────────────────────────────────


def expected_jobs(*, x86_enabled: bool) -> tuple[str, ...]:
    """Erwartete Heartbeat-Jobnamen; x86_64 nur bei aktivierter Plattform.

    Spiegelt die ``if``-Bedingungen des Workflows: Der pausierte
    x86_64-Runner (RELEASE_AUTOMATION §5) existiert nicht und darf nicht
    erwartet werden, sonst meldete der Heartbeat täglich einen Ausfall, den
    es gar nicht gibt.
    """
    platforms = ["macos-arm64", "linux-arm64"]
    if x86_enabled:
        platforms.append("linux-x86_64")
    return tuple(HEARTBEAT_JOB_NAMES[platform] for platform in platforms)


# Ergebnisse, die einen Runner als nicht einsatzbereit ausweisen. ``cancelled``
# gehört bewusst nicht dazu: Das ist eine menschliche Handlung (oder die
# ``cancel-in-progress``-Aufräumung), kein Geräteurteil. Bestanden ist ein Job
# aber ausschließlich mit ``success`` – jede andere abgeschlossene Konklusion
# (``cancelled``, ``skipped``, ``stale``, ``startup_failure``, …) belegt keine
# Bereitschaft und landet als ``inconclusive`` im ``UNOBSERVED``-Zweig, statt
# still als bestanden zu gelten (#943 Befund 1: ``evaluate`` meldete sonst
# PASS „Bereitschaftsprüfung bestanden" für ein abgebrochenes Ergebnis).
FAILED_CONCLUSIONS: Final = ("failure", "timed_out")
SUCCESS_CONCLUSION: Final = "success"


@dataclass(frozen=True)
class QueueState:
    """Beobachtung der Heartbeat-Jobs eines Laufs.

    Vier Mengen statt einer: Ein Runner kann den Job gar nicht erst annehmen
    (``queued``), ihn annehmen und an der Bereitschaftsprüfung scheitern
    (``failed``), noch daran arbeiten (``pending``) oder mit einem Ergebnis
    enden, das weder Erfolg noch Gerätescheitern belegt (``inconclusive``,
    als ``(Jobname, Konklusion)``-Paare). Nur ``status`` auszuwerten hiesse,
    den zweiten Fall als Erfolg zu melden; nur ``failure``/``timed_out``
    auszuwerten, den vierten (#943 Befund 1) – der Bericht behauptete dann
    ``PASS`` für ein Gerät ohne belegte Bereitschaft.
    """

    known: tuple[str, ...]
    queued: tuple[str, ...]
    failed: tuple[str, ...] = ()
    pending: tuple[str, ...] = ()
    inconclusive: tuple[tuple[str, str], ...] = ()
    observed: bool = True
    #: Ob die Annahmefrist beim Ende der Beobachtung wirklich abgelaufen war.
    #: ``watch`` kehrt beim ersten gescheiterten Job **sofort** zurueck – dann
    #: kann gleichzeitig ein anderer noch ``queued`` sein, ohne dass er zu
    #: spaet waere. Ohne dieses Flag behauptete der Bericht "wartet nach
    #: 15 min", obwohl 90 s vergangen sind (#938-Review): Der Offline-Zweig
    #: war nie durchlaufen, die Zahl also unbelegt.
    acceptance_expired: bool = False


def queue_state(jobs: list[dict[str, Any]], names: tuple[str, ...]) -> QueueState:
    """Zustand der exakt benannten Heartbeat-Jobs aus Status **und** Ergebnis."""
    present = {
        str(job.get("name", "")): (
            str(job.get("status", "")), str(job.get("conclusion") or ""),
        )
        for job in jobs
    }
    known = tuple(name for name in names if name in present)
    queued = tuple(name for name in known if present[name][0] == "queued")
    pending = tuple(name for name in known if present[name][0] != "completed")
    failed = tuple(
        name for name in known
        if present[name][0] == "completed" and present[name][1] in FAILED_CONCLUSIONS
    )
    # Alles Abgeschlossene, das weder Erfolg noch Gerätescheitern ist –
    # ``cancelled``/``skipped``/``stale``/``startup_failure``/… dürfen nie
    # still als bestanden gelten (#943 Befund 1).
    inconclusive = tuple(
        (name, present[name][1])
        for name in known
        if present[name][0] == "completed"
        and present[name][1] != SUCCESS_CONCLUSION
        and present[name][1] not in FAILED_CONCLUSIONS
    )
    return QueueState(
        known=known, queued=queued, failed=failed, pending=pending,
        inconclusive=inconclusive,
    )


def _request(url: str, token: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "bgremover-runner-heartbeat",
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
    """Jobs des laufenden Versuchs laden (ein Heartbeat-Lauf hat vier Jobs)."""
    url = f"{api_url}/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100"
    with opener(_request(url, token), timeout=REQUEST_TIMEOUT_S) as response:
        payload = json.load(response)
    jobs = payload.get("jobs")
    return [job for job in jobs if isinstance(job, dict)] if isinstance(jobs, list) else []


def watch(
    observe: Callable[[], QueueState],
    expected: tuple[str, ...],
    *,
    acceptance_s: float,
    deadline_s: float,
    poll_s: float,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> QueueState:
    """Beobachtet, bis jeder erwartete Job fertig ist oder eine Frist fällt.

    **Zwei** Fristen, weil zwei verschiedene Fragen: Bis ``acceptance_s`` muss
    ein Runner den Job angenommen haben – ist dann noch einer ``queued``, ist
    das Offline-Verdikt fällig, ohne das Gesamtfenster abzuwarten. Bis
    ``deadline_s`` muss die Bereitschaftsprüfung abgeschlossen sein.

    Erfolg verlangt, dass jeder erwartete Job in der Jobliste erschienen
    **und** nicht mehr ``queued`` ist; eine direkt nach Laufstart noch
    unvollständige Liste beendet die Beobachtung also nicht vorzeitig.
    Ein Verdikt zum Fristablauf braucht eine **frische** Beobachtung (jünger
    als zwei Poll-Intervalle) – sonst wird sie zu ``observed=False``
    degradiert und der Heartbeat schlägt keinen Alarm auf veralteter
    Grundlage.
    """
    start = clock()
    last = QueueState(known=(), queued=(), observed=False)
    last_success: float | None = None

    def _verdict_ready() -> QueueState:
        """Ergebnis eines Fristablaufs – mit Frische-Degradierung."""
        stale = last_success is None or clock() - last_success > 2 * poll_s
        if (last.queued or last.failed) and stale:
            return replace(last, observed=False, acceptance_expired=True)
        return replace(last, acceptance_expired=True)

    while True:
        try:
            last = observe()
        except (urllib.error.URLError, OSError, ValueError) as exc:
            print(f"::warning::Heartbeat: Jobabfrage fehlgeschlagen ({exc}).")
        else:
            last_success = clock()
            # Ein gescheiterter Bereitschaftsjob steht sofort fest – auf die
            # uebrigen zu warten verzoegerte nur die Meldung.
            if last.failed:
                return last
            if not last.pending and set(expected).issubset(last.known):
                return last
        elapsed = clock() - start
        # Annahmefrist: Ein noch wartender Job ist hier bereits das Ergebnis –
        # aber nur auf **frischer** Grundlage. Ist die Beobachtung veraltet
        # (API-Stoerung um die Frist herum), bliebe sonst genau das Fenster
        # ungenutzt, in dem sich die API erholen koennte: Der Monitor gaebe
        # 10 Minuten Beobachtung fuer eine Stoerung auf, die er ueberlebt
        # haette, und meldete UNOBSERVED statt eines echten Verdikts.
        if elapsed >= acceptance_s and last.queued:
            verdict = _verdict_ready()
            if verdict.observed:
                return verdict
        if elapsed >= deadline_s:
            return _verdict_ready()
        sleep(poll_s)


def evaluate(
    state: QueueState, expected: tuple[str, ...], *, acceptance_s: float, deadline_s: float
) -> tuple[str, str]:
    """Bewertet die letzte Beobachtung als ``(Verdikt, Begründung)``."""
    if not state.observed:
        return VERDICT_UNOBSERVED, (
            "Die Jobliste war zum Fristablauf nicht frisch beobachtbar "
            "(API-Fehler) – kein Verdikt. Ein Monitor ohne Beobachtung "
            "schlägt bewusst keinen Alarm."
        )
    reasons: list[str] = []
    if state.queued and state.acceptance_expired:
        # Der zweite moegliche Grund gehoert in die Meldung, nicht nur in die
        # Doku: Self-hosted-Runner nehmen einen Job gleichzeitig an. Laeuft
        # gerade eine Abnahme auf demselben Geraet, wartet der Heartbeat-Job
        # zu Recht – und der Empfaenger des Issue-Kommentars soll nicht nach
        # einem Ausfall suchen, den es nicht gibt.
        reasons.append(
            f"{', '.join(state.queued)} wartet nach {acceptance_s / 60:.0f} min "
            "weiterhin auf einen Runner – offline, nimmt keine Jobs an oder ist "
            "mit einem anderen Lauf belegt"
        )
    elif state.queued:
        # Die Beobachtung endete vorzeitig, weil ein anderer Job bereits
        # gescheitert war. Der wartende Runner ist damit nicht zu spaet – ihn
        # als offline zu melden waere eine Behauptung ohne Beleg.
        reasons.append(
            f"{', '.join(state.queued)} hatte den Job noch nicht angenommen, als "
            "die Beobachtung endete – die Annahmefrist war da noch nicht "
            "abgelaufen, also kein Offline-Befund"
        )
    if state.failed:
        # Die zweite Haelfte des Signals: angenommen, aber nicht einsatzbereit.
        # Ohne sie meldete der Bericht PASS, waehrend der Lauf rot ist.
        reasons.append(
            f"{', '.join(state.failed)} hat die Bereitschaftsprüfung nicht "
            "bestanden – Gerät angenommen, aber nicht einsatzbereit"
        )
    if reasons:
        return VERDICT_FAIL, "; ".join(reasons) + "."
    missing = tuple(name for name in expected if name not in state.known)
    if missing:
        return VERDICT_UNOBSERVED, (
            "Erwartete Jobs sind nie in der Jobliste erschienen: "
            f"{', '.join(missing)} – Namensdrift oder API-Anomalie, "
            "kein Runner-Verdikt."
        )
    if state.inconclusive:
        # ``cancelled`` ist laut FAILED_CONCLUSIONS-Kommentar bewusst kein
        # Geräteurteil – aber Erfolg ist es genauso wenig. Vor #943 fiel
        # dieser Fall durch bis PASS: „Bereitschaftsprüfung bestanden" für
        # einen Job, der abgebrochen oder nie gestartet wurde.
        described = ", ".join(
            f"{name} (Ergebnis {conclusion or 'unbekannt'})"
            for name, conclusion in state.inconclusive
        )
        return VERDICT_UNOBSERVED, (
            f"{described} endete ohne success – abgebrochen, übersprungen "
            "oder verworfen. Das belegt keine Bereitschaft, aber auch kein "
            "Gerätescheitern: kein Verdikt."
        )
    if state.pending:
        return VERDICT_UNOBSERVED, (
            f"{', '.join(state.pending)} lief nach {deadline_s / 60:.0f} min noch – "
            "angenommen, Bereitschaft aber noch offen. Kein Verdikt."
        )
    return VERDICT_PASS, (
        "Alle erwarteten Runner haben ihren Job angenommen und die "
        "Bereitschaftsprüfung bestanden."
    )


# ── Bericht und Summary ────────────────────────────────────────────────


def build_report(
    *,
    verdict: str,
    detail: str,
    expected: tuple[str, ...],
    state: QueueState,
    acceptance_s: float,
    deadline_s: float,
    run_url: str,
) -> dict[str, Any]:
    return {
        "schema": REPORT_SCHEMA,
        "kind": REPORT_KIND,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "detail": detail,
        "acceptance_seconds": acceptance_s,
        "deadline_seconds": deadline_s,
        "run_url": run_url,
        "expected_jobs": list(expected),
        "observed_jobs": list(state.known),
        "queued_jobs": list(state.queued),
        "failed_jobs": list(state.failed),
        "pending_jobs": list(state.pending),
        "inconclusive_jobs": [
            {"name": name, "conclusion": conclusion}
            for name, conclusion in state.inconclusive
        ],
        "observed": state.observed,
        "acceptance_expired": state.acceptance_expired,
    }


def render_summary(report: dict[str, Any]) -> str:
    """Markdown für Job-Summary und – nur im Fehlerfall – Issue-Kommentar."""
    icon = {
        VERDICT_PASS: "✅", VERDICT_FAIL: "❌",
        VERDICT_UNOBSERVED: "⚠️", VERDICT_PAUSED: "⏸️",
    }.get(str(report["verdict"]), "•")
    lines = [f"## {icon} Runner-Heartbeat — {report['verdict']}", ""]
    lines.append(str(report["detail"]))
    lines.append("")
    expected = list(report.get("expected_jobs", []))
    if expected:
        queued = set(report.get("queued_jobs", []))
        failed = set(report.get("failed_jobs", []))
        pending = set(report.get("pending_jobs", []))
        known = set(report.get("observed_jobs", []))
        inconclusive = {
            str(entry.get("name", "")): str(entry.get("conclusion") or "unbekannt")
            for entry in report.get("inconclusive_jobs", [])
            if isinstance(entry, dict)
        }
        lines.append("| Runner-Job | Zustand |")
        lines.append("| --- | --- |")
        for name in expected:
            if name in queued:
                status = "❌ wartet auf einen Runner"
            elif name in failed:
                status = "❌ angenommen, aber nicht einsatzbereit"
            elif name in inconclusive:
                status = f"⚠️ endete ohne success ({inconclusive[name]})"
            elif name in pending:
                status = "⚠️ läuft noch"
            elif name in known:
                status = "✅ angenommen und bestanden"
            else:
                status = "⚠️ nicht in der Jobliste"
            lines.append(f"| {name} | {status} |")
        lines.append("")
    if report["verdict"] == VERDICT_FAIL:
        lines.append(
            "Abhilfe: Gerät einschalten bzw. Runner-Dienst starten "
            "(`docs/RELEASE_AUTOMATION.md` §6). Hat der Runner den Job "
            "angenommen und die Prüfung nicht bestanden, nennt sein Joblog "
            "den fehlenden Punkt – Härtung siehe §2.1/§2.2. Bleibt ein Runner "
            "länger als 30 Tage offline, entfernt GitHub ihn und §2 ist zu "
            "wiederholen."
        )
        lines.append("")
    if report.get("run_url"):
        lines.append(f"Lauf: {report['run_url']}")
        lines.append("")
    return "\n".join(lines)


def write_outputs(
    report: dict[str, Any], *, report_path: Path | None, summary_path: Path | None
) -> None:
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f">> Heartbeat-Bericht geschrieben: {report_path}")
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(render_summary(report), encoding="utf-8")
        print(f">> Heartbeat-Summary geschrieben: {summary_path}")


def append_github_output(name: str, value: str) -> None:
    """Schreibt einen Step-Output, wenn der Workflow einen bereitstellt."""
    target = os.environ.get("GITHUB_OUTPUT")
    if not target:
        return
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


# ── CLI ────────────────────────────────────────────────────────────────


def _cmd_pause_status(args: argparse.Namespace) -> int:
    today = date.fromisoformat(args.today) if args.today else datetime.now(timezone.utc).date()
    state = pause_state(paused_raw=args.paused, until_raw=args.until, today=today)
    append_github_output("paused", "true" if state.paused else "false")
    report = {
        "schema": REPORT_SCHEMA,
        "kind": REPORT_KIND,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": VERDICT_PAUSED if state.paused else VERDICT_PASS,
        "detail": state.detail,
        "pause": state.as_dict(),
        "expected_jobs": [],
        "observed_jobs": [],
        "queued_jobs": [],
        "run_url": args.run_url,
    }
    write_outputs(report, report_path=args.report, summary_path=args.summary)
    if not state.ok:
        print(f"::error title=Heartbeat-Pause ungueltig::{state.detail}")
        return 1
    if state.paused:
        print(f"::warning title=Heartbeat pausiert::{state.detail}")
    else:
        print(f"[heartbeat] {state.detail}")
    return 0


def _cmd_watch(args: argparse.Namespace) -> int:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        print("::error::Kein GH_TOKEN/GITHUB_TOKEN gesetzt (actions: read noetig).")
        return 2
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    expected = expected_jobs(x86_enabled=args.x86_64_enabled)

    def observe() -> QueueState:
        return queue_state(
            fetch_jobs(args.repo, args.run_id, token, api_url=api_url), expected
        )

    state = watch(
        observe, expected,
        acceptance_s=args.acceptance_seconds,
        deadline_s=args.deadline_seconds, poll_s=args.poll_seconds,
    )
    verdict, detail = evaluate(
        state, expected,
        acceptance_s=args.acceptance_seconds, deadline_s=args.deadline_seconds,
    )
    report = build_report(
        verdict=verdict, detail=detail, expected=expected, state=state,
        acceptance_s=args.acceptance_seconds,
        deadline_s=args.deadline_seconds, run_url=args.run_url,
    )
    write_outputs(report, report_path=args.report, summary_path=args.summary)
    if verdict == VERDICT_FAIL:
        print(f"::error title=Self-hosted Runner offline::{detail}")
        return 1
    if verdict == VERDICT_UNOBSERVED:
        print(f"::warning title=Heartbeat ohne Verdikt::{detail}")
        return 0
    print(f"[heartbeat] {detail}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="Zielpfad des JSON-Berichts")
    parser.add_argument("--summary", type=Path, help="Zielpfad der Markdown-Summary")
    parser.add_argument("--run-url", default="", help="URL des laufenden Workflows")
    sub = parser.add_subparsers(dest="command", required=True)

    pause = sub.add_parser("pause-status", help="Wartungsfenster bewerten")
    pause.add_argument("--paused", default="", help=f"Wert von {PAUSE_VARIABLE}")
    pause.add_argument("--until", default="", help=f"Wert von {PAUSE_UNTIL_VARIABLE}")
    pause.add_argument("--today", default="", help="ISO-Datum (nur für Tests)")
    pause.set_defaults(func=_cmd_pause_status)

    watch_cmd = sub.add_parser("watch", help="Heartbeat-Jobs bis zur Zuweisung beobachten")
    watch_cmd.add_argument("--repo", required=True)
    watch_cmd.add_argument("--run-id", required=True)
    watch_cmd.add_argument("--x86-64-enabled", action="store_true")
    watch_cmd.add_argument(
        "--acceptance-seconds", type=float, default=DEFAULT_ACCEPTANCE_S,
        help="Frist bis zur Annahme des Jobs durch den Runner.",
    )
    watch_cmd.add_argument(
        "--deadline-seconds", type=float, default=DEFAULT_DEADLINE_S,
        help="Gesamtfrist bis zum Abschluss der Bereitschaftspruefung.",
    )
    watch_cmd.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_S)
    watch_cmd.set_defaults(func=_cmd_watch)

    args = parser.parse_args(argv)
    # Eine Annahmefrist jenseits des Gesamtfensters waere wirkungslos: Der
    # Offline-Zweig kaeme nie zum Zug, und der Heartbeat haelt sein
    # "<= 15 min" nicht mehr, ohne dass es jemand merkt.
    # Symmetrisch defensiv: Beide Optionen haengen am selben Unterkommando.
    # Nur eine per getattr zu lesen liefe bei einem kuenftigen Unterkommando
    # mit genau einer der beiden in einen AttributeError (#938-Review).
    acceptance = getattr(args, "acceptance_seconds", None)
    deadline = getattr(args, "deadline_seconds", None)
    # ``>=`` statt ``>``: Eine Annahmefrist gleich dem Gesamtfenster ist
    # wirkungslos – der Offline-Zweig kaeme nie frueher zum Zug, und der
    # Heartbeat faellt still auf den Zustand zurueck, den dieser PR behebt.
    # So sind CLI, Docstring und Waechter deckungsgleich.
    if acceptance is not None and deadline is not None and acceptance >= deadline:
        parser.error(
            f"--acceptance-seconds ({acceptance:.0f}) muss kleiner als "
            f"--deadline-seconds ({deadline:.0f}) sein – sonst gibt es kein "
            "frueheres Offline-Verdikt."
        )
    result = args.func(args)
    return int(result)


if __name__ == "__main__":
    sys.exit(main())
