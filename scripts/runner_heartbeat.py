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
    Bereitschaftsprüfung scheitert (``conclusion`` ``failure``/``timed_out``/
    ``startup_failure``). Bestanden ist ein Job ausschließlich mit ``success``;
    jede andere abgeschlossene Konklusion (``cancelled``/``skipped``/``stale``/
    fehlend) belegt keine Bereitschaft und ergibt ``UNOBSERVED`` mit benannter
    Konklusion (#944).
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

**Gestufte Eskalation (#958).** Ein FAIL-Tag erzeugt keinen Kommentar mehr
(Owner-Entscheid E1: der Tageszustand bleibt Job-Summary und Artefakt).
Stattdessen zählt ``watch`` je Plattform die Tage ohne bestandenen Heartbeat
aus der Laufhistorie desselben Workflows und postet an genau drei Stufen
(``OFFLINE_STAGE_DAYS``) einen Kommentar mit Erwähnung des Owners – die
Erwähnung ist der E-Mail-Kanal, ohne SMTP und ohne neues Geheimnis. Jeder
Stufenkommentar trägt einen deterministischen Marker je Plattform, Episode
und Stufe; ein Wiederanlauf am selben Tag findet ihn und postet nichts. Die
dritte Stufe trägt die Plattform aus dem erwarteten Bestand aus: Der
``retire``-Job des Workflows setzt das Label
``runner-retired:<plattform>:<datum>`` auf das Betriebs-Issue – mit
``issues: write``, das die kommentierenden Jobs ohnehin tragen. Eine
Repository-Variable war die erste Wahl und ist es nicht mehr: ``GITHUB_TOKEN``
kann keine Variable setzen (die Variablen-API verlangt die eigene
Berechtigung „Variables", die der ``permissions:``-Block eines Workflows
nicht kennt; Review PR #981). Das Unterkommando ``retired-status`` liest die
Labels und liefert beiden Self-hosted-Workflows die ausgetragenen
Plattformen. Ohne lesbare Historie oder Kommentarliste gibt es keine
Stufenentscheidung, sondern einen sichtbaren Hinweis – nie eine geratene
Stufe.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
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

# ── Gestufte Eskalation (#958) ─────────────────────────────────────────
#
# Bis #958 kommentierte ein offline Runner **jeden Tag** gleichlautend im
# Betriebs-Issue – ohne Erwaehnung, ohne Abstufung und ohne Bezug zur einzigen
# harten Frist: GitHub entfernt einen Self-hosted Runner, der laenger als 14
# Tage nicht verbunden war, automatisch aus der Registrierung (Plattformregel,
# nicht konfigurierbar). Statt dessen drei Stufen je Plattform, gezaehlt in
# Tagen ohne bestandenen Heartbeat. Die Zahlen stehen **nur hier**; der
# Workflow uebergibt sie explizit (wie die beiden Fristen oben), Abhilfetexte
# werden daraus gerendert, und ``tests/test_runner_heartbeat_workflow.py``
# haelt Workflow und Doku dagegen.
#: Faelligkeit der Stufen in Tagen seit ``offline_since`` (Owner-Entscheid E3
#: zu #958: 7/12/21). Die zweite Warnung liegt bewusst **vor** GitHubs
#: 14-Tage-Entfernung statt mit ihr zusammen – danach genuegt Wiederbeleben
#: nicht mehr, und genau das soll die Mail noch rechtzeitig sagen.
OFFLINE_STAGE_DAYS: Final[tuple[int, int, int]] = (7, 12, 21)
#: GitHubs eigene Frist: Nach so vielen Tagen ohne Verbindung entfernt GitHub
#: die Runner-Registrierung. Nicht beeinflussbar – dieses Skript kann nur
#: vorher warnen und danach den eigenen Bestand bereinigen.
GITHUB_RUNNER_REMOVAL_DAYS: Final = 14
#: Rueckblick in die Laufhistorie. Laenger als Stufe 3, damit ``offline_since``
#: bis zur Austragung an einem echten Lauf haengt – der Marker im Kommentar
#: bleibt dadurch stabil, statt mit dem Fensterrand zu wandern. Reicht die
#: Historie nicht bis zu einem bestandenen Lauf zurueck, gilt „seit mindestens".
HISTORY_WINDOW_DAYS: Final = 45
#: Workflow-Datei, deren Laufhistorie die Zaehlbasis liefert.
WORKFLOW_FILE: Final = "runner-heartbeat.yml"
#: Praefix des Kommentar-Markers (Muster ``dispatch_marker`` aus #919):
#: ``runner-heartbeat:<plattform>:offline:<offline_since>:stage-<n>``.
MARKER_PREFIX: Final = "runner-heartbeat"
#: Ursache eines FAIL-Tages. Nur ``offline`` nennt GitHubs Entfernung – ein
#: verbundener, aber nicht einsatzbereiter Runner verliert seine
#: Registrierung nicht.
CAUSE_OFFLINE: Final = "offline"
CAUSE_NOT_READY: Final = "not_ready"
#: Ergebnisklassen eines frueheren Laufs je Heartbeat-Job.
OUTCOME_SUCCESS: Final = "success"
OUTCOME_NO_SUCCESS: Final = "no_success"
OUTCOME_NEUTRAL: Final = "neutral"


#: Praefix des Austragungs-Labels am Betriebs-Issue:
#: ``runner-retired:<plattform>:<datum>``. Das Datum steckt im Namen, damit
#: ein einziger Lese-Aufruf (die Labels des Issues) Bestand **und** Datum
#: liefert; Reaktivierung heisst: das Label vom Issue entfernen.
RETIRED_LABEL_PREFIX: Final = "runner-retired"
_RETIRED_LABEL_RE = re.compile(
    rf"^{re.escape(RETIRED_LABEL_PREFIX)}:([a-z0-9_-]+):(\d{{4}}-\d{{2}}-\d{{2}})$"
)


def retired_label(platform: str, day: date) -> str:
    """Label, das eine Plattform seit ``day`` aus dem Bestand austraegt.

    Einzige Quelle des Namensschemas – ``retire.tsv``, Kommentartexte,
    Doku und der Wächter werden dagegen gehalten.
    """
    return f"{RETIRED_LABEL_PREFIX}:{platform}:{day.isoformat()}"


def parse_retired_labels(names: Iterable[str]) -> dict[str, date]:
    """Ausgetragene Plattformen aus den Label-Namen eines Issues.

    Fremde Labels werden ignoriert; ein Austragungs-Label mit unbekannter
    Plattform oder unlesbarem Datum ist ein Befund (fail-closed – es wuerde
    sonst je nach Lesart still austragen oder still ignoriert). Tragen
    mehrere Labels dieselbe Plattform, gilt das juengste Datum.
    """
    retired: dict[str, date] = {}
    for name in names:
        if not name.startswith(f"{RETIRED_LABEL_PREFIX}:"):
            continue
        match = _RETIRED_LABEL_RE.match(name)
        if match is None:
            raise ValueError(
                f"Label {name!r} passt nicht auf {RETIRED_LABEL_PREFIX}:<plattform>:<YYYY-MM-DD>"
            )
        platform, raw = match.group(1), match.group(2)
        if platform not in HEARTBEAT_JOB_NAMES:
            raise ValueError(
                f"Label {name!r} nennt eine unbekannte Plattform – erwartet eine von "
                f"{', '.join(HEARTBEAT_JOB_NAMES)}"
            )
        try:
            day = date.fromisoformat(raw)
        except ValueError as exc:
            raise ValueError(f"Label {name!r}: {raw!r} ist kein gueltiges Datum") from exc
        retired[platform] = max(retired.get(platform, day), day)
    return retired


def retired_output_name(platform: str) -> str:
    """Step-Output je Plattform (``retired_macos_arm64`` …) – die Workflows
    lesen ihn ueber ``needs.<job>.outputs`` in ihren ``if``-Bedingungen."""
    return f"retired_{platform.replace('-', '_')}"


def parse_retired(values: Iterable[str]) -> dict[str, date]:
    """``<plattform>=<datum>``-Angaben; ein leeres Datum heisst „nicht ausgetragen".

    Ein unlesbares Datum ist ein Befund, kein stiller Rueckfall: Je nachdem,
    wie man den Tippfehler liest, erwartete der Heartbeat die Plattform
    weiter oder truege sie still aus – beides falsch.
    """
    retired: dict[str, date] = {}
    for value in values:
        platform, sep, raw = value.partition("=")
        platform = platform.strip()
        if not sep or platform not in HEARTBEAT_JOB_NAMES:
            raise ValueError(
                f"--retired-since erwartet <plattform>=<datum> mit einer der "
                f"Plattformen {', '.join(HEARTBEAT_JOB_NAMES)}, nicht {value!r}"
            )
        raw = raw.strip()
        if not raw:
            continue
        try:
            retired[platform] = date.fromisoformat(raw)
        except ValueError as exc:
            raise ValueError(
                f"--retired-since {platform}={raw!r}: kein ISO-Datum (YYYY-MM-DD)"
            ) from exc
    return retired


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


def expected_jobs(*, x86_enabled: bool, retired: Iterable[str] = ()) -> tuple[str, ...]:
    """Erwartete Heartbeat-Jobnamen; x86_64 nur bei aktivierter Plattform.

    Spiegelt die ``if``-Bedingungen des Workflows: Der pausierte
    x86_64-Runner (RELEASE_AUTOMATION §5) existiert nicht und darf nicht
    erwartet werden, sonst meldete der Heartbeat täglich einen Ausfall, den
    es gar nicht gibt. Dasselbe gilt seit #958 für eine **ausgetragene**
    Plattform (Stufe 3): Ihr Runner-Job ist per Variable übersprungen, und
    die Auswertung darf ihn weder erwarten noch weiter eskalieren.
    """
    platforms = ["macos-arm64", "linux-arm64"]
    if x86_enabled:
        platforms.append("linux-x86_64")
    excluded = set(retired)
    return tuple(
        HEARTBEAT_JOB_NAMES[platform] for platform in platforms if platform not in excluded
    )


# Ergebnisse, die einen Runner als nicht einsatzbereit ausweisen.
# ``startup_failure`` gehört dazu (#944-Review): Der Runner hat den Job
# angenommen und konnte ihn nicht starten (kaputter Workspace, volles
# ``_work``, Dienst am Ende) – dieselbe Aussage wie ``failure``/``timed_out``,
# nur früher im Lebenszyklus, und nur der FAIL-Zweig erreicht den
# Issue-Kommentar (``if: failure()`` im Workflow). ``cancelled`` bleibt
# draußen: menschliche Handlung (oder die ``cancel-in-progress``-Aufräumung),
# kein Geräteurteil. Bestanden ist ein Job aber ausschließlich mit
# ``success`` – jede andere abgeschlossene Konklusion (``cancelled``,
# ``skipped``, ``stale``, …) belegt keine Bereitschaft und landet als
# ``inconclusive`` im ``UNOBSERVED``-Zweig, statt still als bestanden zu
# gelten (#943 Befund 1: ``evaluate`` meldete sonst PASS
# „Bereitschaftsprüfung bestanden" für ein abgebrochenes Ergebnis).
# ``stale`` zählt bewusst nicht wie ``queued`` als Offline-Beleg: GitHub
# setzt es erst nach Laufabschluss für nie zugewiesene Jobs – während der
# Beobachtung des eigenen, laufenden Runs erscheint derselbe Zustand als
# ``queued`` und trägt dort bereits das fristgebundene Offline-Verdikt.
#: „Angenommen, konnte nicht starten" – einzige Quelle des Literals, damit
#: ``evaluate`` und ``render_summary`` nicht still auf den generischen
#: Gerätebefund zurückfallen (#957-Review).
STARTUP_FAILURE_CONCLUSION: Final = "startup_failure"
FAILED_CONCLUSIONS: Final = ("failure", "timed_out", STARTUP_FAILURE_CONCLUSION)
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
    #: Konklusion je gescheitertem Job, gleiche Reihenfolge wie ``failed`` –
    #: ``startup_failure`` braucht einen anderen Meldetext als ``failure``:
    #: Dort lief keine Prüfung und es gibt kein Joblog (#954-Review).
    failed_conclusions: tuple[tuple[str, str], ...] = ()
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
    # ``cancelled``/``skipped``/``stale``/… dürfen nie still als bestanden
    # gelten (#943 Befund 1). ``startup_failure`` gehört seit #944 zu
    # ``FAILED_CONCLUSIONS`` und landet in ``failed``, nie hier.
    inconclusive = tuple(
        (name, present[name][1])
        for name in known
        if present[name][0] == "completed"
        and present[name][1] != SUCCESS_CONCLUSION
        and present[name][1] not in FAILED_CONCLUSIONS
    )
    failed_conclusions = tuple((name, present[name][1]) for name in failed)
    return QueueState(
        known=known, queued=queued, failed=failed, pending=pending,
        inconclusive=inconclusive, failed_conclusions=failed_conclusions,
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
        # Ohne sie meldete der Bericht PASS, waehrend der Lauf rot ist. Bei
        # ``startup_failure`` lief keine Pruefung und es gibt kein Joblog –
        # der Text darf also weder eine „nicht bestandene Pruefung" noch ein
        # Joblog behaupten (#954-Review).
        conclusions = dict(state.failed_conclusions)
        not_started = tuple(
            name for name in state.failed
            if conclusions.get(name) == STARTUP_FAILURE_CONCLUSION
        )
        not_ready = tuple(name for name in state.failed if name not in not_started)
        if not_ready:
            named = ", ".join(
                f"{name} ({conclusions.get(name) or 'unbekannt'})" for name in not_ready
            )
            reasons.append(
                f"{named} hat die Bereitschaftsprüfung nicht bestanden – Gerät "
                "angenommen, aber nicht einsatzbereit"
            )
        if not_started:
            reasons.append(
                f"{', '.join(not_started)} konnte den angenommenen Job nicht starten "
                f"({STARTUP_FAILURE_CONCLUSION}) – Gerät angenommen, aber nicht einsatzbereit; es "
                "lief keine Prüfung und es gibt kein Joblog"
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


# ── Gestufte Eskalation: Zaehlbasis, Stufen, Marker (#958) ─────────────


@dataclass(frozen=True)
class RunRecord:
    """Ein frueherer Heartbeat-Lauf: Tag und ``(status, conclusion)`` je Job."""

    day: date
    jobs: dict[str, tuple[str, str]]


def job_outcome(record: RunRecord, job_name: str) -> str:
    """Bestanden, nicht bestanden oder ohne Aussage.

    ``skipped`` ist bewusst neutral: So sehen Wartungsfenster, die
    deaktivierte x86_64-Plattform und eine ausgetragene Plattform aus – kein
    Beleg fuer offline, aber auch kein bestandener Heartbeat. Ein noch
    offener oder nie erschienener Job sagt ebenfalls nichts. Alles andere
    (``failure``, ``timed_out``, ``startup_failure``, ``cancelled`` aus dem
    ``cancel-in-progress``-Aufraeumen des naechsten Tages, ``stale``) ist ein
    Tag ohne bestandenen Heartbeat.
    """
    status, conclusion = record.jobs.get(job_name, ("", ""))
    if status != "completed":
        return OUTCOME_NEUTRAL
    if conclusion == SUCCESS_CONCLUSION:
        return OUTCOME_SUCCESS
    if conclusion == "skipped":
        return OUTCOME_NEUTRAL
    return OUTCOME_NO_SUCCESS


@dataclass(frozen=True)
class Episode:
    """Laufende Episode ohne bestandenen Heartbeat einer Plattform."""

    since: date
    #: Die Historie reicht nicht bis zu einem bestandenen Lauf zurueck – die
    #: Episode begann spaetestens ``since``, moeglicherweise frueher.
    at_least: bool


def offline_episode(records: Iterable[RunRecord], job_name: str, *, today: date) -> Episode:
    """``offline_since`` aus der Laufhistorie: erster Lauf der laufenden Episode.

    Rueckwaerts vom juengsten Lauf: Der erste bestandene Lauf beendet die
    Suche; jeder Lauf ohne Erfolg schiebt den Episodenbeginn nach hinten;
    neutrale Laeufe (Pause, uebersprungen, offen) zaehlen nicht, **beenden
    die Episode aber auch nicht** – die Zaehlung laeuft ueber ein
    Wartungsfenster real weiter (#958). Ohne einen einzigen Lauf ohne Erfolg
    beginnt die Episode heute (Tag 0).
    """
    since = today
    seen_no_success = False
    for record in sorted(records, key=lambda entry: entry.day, reverse=True):
        if record.day > today:
            continue
        outcome = job_outcome(record, job_name)
        if outcome == OUTCOME_SUCCESS:
            return Episode(since=since, at_least=False)
        if outcome == OUTCOME_NO_SUCCESS:
            since = record.day
            seen_no_success = True
    return Episode(since=since, at_least=seen_no_success)


def offline_stage(days: int, stages: tuple[int, ...] = OFFLINE_STAGE_DAYS) -> int:
    """Hoechste faellige Stufe (1-basiert); ``0`` = keine Stufe faellig."""
    return sum(1 for threshold in stages if days >= threshold)


def stage_marker(platform: str, since: date, stage: int) -> str:
    """Deterministischer Marker je Plattform, Episode und Stufe."""
    return f"{MARKER_PREFIX}:{platform}:offline:{since.isoformat()}:stage-{stage}"


_MARKER_RE = re.compile(
    rf"{re.escape(MARKER_PREFIX)}:([a-z0-9_-]+):offline:(\d{{4}}-\d{{2}}-\d{{2}}):stage-(\d+)"
)


def posted_stages(comments: Iterable[tuple[date, str]], platform: str, since: date) -> tuple[int, ...]:
    """Bereits gepostete Stufen dieser Episode, aus den Markern der Kommentare."""
    found: set[int] = set()
    for _day, body in comments:
        for match in _MARKER_RE.finditer(body):
            if match.group(1) == platform and match.group(2) == since.isoformat():
                found.add(int(match.group(3)))
    return tuple(sorted(found))


def last_retirement(
    comments: Iterable[tuple[date, str]], platform: str, *,
    stages: tuple[int, ...] = OFFLINE_STAGE_DAYS,
) -> date | None:
    """Tag des juengsten Austragungs-Kommentars (letzte Stufe) dieser Plattform.

    Eine Austragung **beendet** die Episode: Wird die Plattform spaeter
    reaktiviert (Variable entfernt) und faellt erneut aus, beginnt die
    Zaehlung nach der Austragung neu – sonst haengte die neue Episode am
    alten ``offline_since``, faende ihre Marker bereits vor und traege die
    Plattform still, ohne Kommentar, ein zweites Mal aus.
    """
    days = [
        day
        for day, body in comments
        if any(
            match.group(1) == platform and match.group(3) == str(len(stages))
            for match in _MARKER_RE.finditer(body)
        )
    ]
    return max(days) if days else None


@dataclass(frozen=True)
class StageDecision:
    """Stufenentscheidung einer Plattform mit belegtem FAIL am heutigen Tag."""

    platform: str
    job: str
    cause: str
    conclusion: str
    since: date
    at_least: bool
    days: int
    stage_due: int
    stages_posted: tuple[int, ...]
    #: Zu postende Stufe (0 = keine): die hoechste faellige, noch nicht
    #: gepostete. Niedrigere, nie gepostete Stufen gelten als ueberholt –
    #: ihr Text („noch N Tage bis GitHub …") waere bereits falsch.
    stage_to_post: int
    #: Austragung faellig (Stufe 3 erreicht). Der ``retire``-Job setzt die
    #: Variable **vor** dem Kommentar; ein vorhandener Stufe-3-Marker belegt
    #: also eine erfolgte Austragung, und ``last_retirement`` hat die Episode
    #: dann bereits neu begonnen – ein zweites stilles Austragen gibt es nicht.
    retire: bool
    stages: tuple[int, ...]
    removal_days: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "job": self.job,
            "cause": self.cause,
            "conclusion": self.conclusion,
            "offline_since": self.since.isoformat(),
            "at_least": self.at_least,
            "days": self.days,
            "stage_due": self.stage_due,
            "stages_posted": list(self.stages_posted),
            "stage_to_post": self.stage_to_post,
            "retire": self.retire,
            "marker": stage_marker(self.platform, self.since, self.stage_to_post)
            if self.stage_to_post
            else None,
        }


def failing_platforms(state: QueueState) -> list[tuple[str, str, str]]:
    """``(Plattform, Ursache, Konklusion)`` je heute **belegtem** FAIL.

    Nur ein nach abgelaufener Annahmefrist wartender Job ist ein
    Offline-Befund; ein wartender Job bei vorzeitig beendeter Beobachtung
    ist keiner (siehe ``evaluate``).
    """
    by_job = {job: platform for platform, job in HEARTBEAT_JOB_NAMES.items()}
    conclusions = dict(state.failed_conclusions)
    failing: list[tuple[str, str, str]] = []
    if state.acceptance_expired:
        failing.extend((by_job[job], CAUSE_OFFLINE, "") for job in state.queued if job in by_job)
    failing.extend(
        (by_job[job], CAUSE_NOT_READY, conclusions.get(job, ""))
        for job in state.failed
        if job in by_job
    )
    return failing


def decide_stage(
    platform: str,
    cause: str,
    conclusion: str,
    *,
    records: Iterable[RunRecord],
    comments: Iterable[tuple[date, str]],
    today: date,
    stages: tuple[int, ...] = OFFLINE_STAGE_DAYS,
    removal_days: int = GITHUB_RUNNER_REMOVAL_DAYS,
) -> StageDecision:
    """Reine Stufenentscheidung einer Plattform aus Historie und Kommentaren."""
    comments = list(comments)
    job = HEARTBEAT_JOB_NAMES[platform]
    retired_on = last_retirement(comments, platform, stages=stages)
    history = [
        record for record in records if retired_on is None or record.day > retired_on
    ]
    episode = offline_episode(history, job, today=today)
    if retired_on is not None and episode.at_least:
        # Die Austragung begrenzt die Episode nach hinten exakt – „seit
        # mindestens" waere hier eine falsche Unschaerfe (Review PR #981).
        episode = Episode(since=episode.since, at_least=False)
    days = (today - episode.since).days
    due = offline_stage(days, stages)
    posted = posted_stages(comments, platform, episode.since)
    return StageDecision(
        platform=platform, job=job, cause=cause, conclusion=conclusion,
        since=episode.since, at_least=episode.at_least, days=days,
        stage_due=due, stages_posted=posted,
        stage_to_post=due if due and due not in posted else 0,
        retire=due >= len(stages),
        stages=stages, removal_days=removal_days,
    )


def decide_stages(
    state: QueueState,
    *,
    records: Iterable[RunRecord],
    comments: Iterable[tuple[date, str]],
    today: date,
    stages: tuple[int, ...] = OFFLINE_STAGE_DAYS,
    removal_days: int = GITHUB_RUNNER_REMOVAL_DAYS,
) -> list[StageDecision]:
    """Stufenentscheidungen fuer jede Plattform mit belegtem FAIL."""
    records = list(records)
    comments = list(comments)
    return [
        decide_stage(
            platform, cause, conclusion, records=records, comments=comments,
            today=today, stages=stages, removal_days=removal_days,
        )
        for platform, cause, conclusion in failing_platforms(state)
    ]


def _run_day(run: dict[str, Any]) -> date | None:
    raw = str(run.get("created_at") or "")
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def collect_history(
    runs: Iterable[dict[str, Any]],
    fetch_jobs_for: Callable[[str], list[dict[str, Any]]],
    *,
    job_names: Iterable[str],
    exclude_run_id: str,
) -> list[RunRecord]:
    """Laufhistorie als ``RunRecord``s, juengster Lauf zuerst.

    Der laufende Lauf ist ausgeschlossen (sein Ergebnis liefert ``watch``
    selbst). Jobs werden nur so weit rueckwaerts geladen, bis jeder
    interessierende Job einmal bestanden hat – im Regelfall (gestern gruen)
    ein einziger Aufruf; ``offline_episode`` braucht nichts, was dahinter
    liegt.
    """
    pending = set(job_names)
    ordered = sorted(
        (run for run in runs if str(run.get("id")) != str(exclude_run_id)),
        key=lambda run: str(run.get("created_at") or ""),
        reverse=True,
    )
    records: list[RunRecord] = []
    for run in ordered:
        if not pending:
            break
        day = _run_day(run)
        if day is None:
            continue
        jobs = {
            str(job.get("name", "")): (str(job.get("status", "")), str(job.get("conclusion") or ""))
            for job in fetch_jobs_for(str(run.get("id")))
            if isinstance(job, dict)
        }
        record = RunRecord(day=day, jobs=jobs)
        records.append(record)
        pending -= {name for name in pending if job_outcome(record, name) == OUTCOME_SUCCESS}
    return records


def fetch_run_history(
    repo: str,
    token: str,
    *,
    api_url: str,
    since: date,
    exclude_run_id: str,
    job_names: Iterable[str],
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[RunRecord]:
    """Laeufe von ``WORKFLOW_FILE`` ab ``since`` samt Job-Ergebnissen laden."""
    runs: list[dict[str, Any]] = []
    page = 1
    while True:
        query = urllib.parse.urlencode(
            {"per_page": 100, "page": page, "created": f">={since.isoformat()}"}
        )
        url = f"{api_url}/repos/{repo}/actions/workflows/{WORKFLOW_FILE}/runs?{query}"
        with opener(_request(url, token), timeout=REQUEST_TIMEOUT_S) as response:
            payload = json.load(response)
        batch = payload.get("workflow_runs") if isinstance(payload, dict) else None
        batch = [run for run in batch if isinstance(run, dict)] if isinstance(batch, list) else []
        runs.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return collect_history(
        runs,
        lambda run_id: fetch_jobs(repo, run_id, token, api_url=api_url, opener=opener),
        job_names=job_names, exclude_run_id=exclude_run_id,
    )


def fetch_issue_comments(
    repo: str,
    issue: str,
    token: str,
    *,
    api_url: str,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[tuple[date, str]]:
    """Alle Kommentare eines Issues als ``(Tag, Text)`` – nur die Marker zaehlen."""
    comments: list[tuple[date, str]] = []
    page = 1
    while True:
        query = urllib.parse.urlencode({"per_page": 100, "page": page})
        url = f"{api_url}/repos/{repo}/issues/{issue}/comments?{query}"
        with opener(_request(url, token), timeout=REQUEST_TIMEOUT_S) as response:
            payload = json.load(response)
        batch = [entry for entry in payload if isinstance(entry, dict)] if isinstance(payload, list) else []
        for entry in batch:
            day = _run_day(entry)
            if day is not None:
                comments.append((day, str(entry.get("body") or "")))
        if len(batch) < 100:
            break
        page += 1
    return comments


def _cause_line(decision: StageDecision) -> str:
    if decision.cause == CAUSE_OFFLINE:
        return (
            "wartet nach der Annahmefrist auf einen Runner – offline, nimmt "
            "keine Jobs an oder ist mit einem anderen Lauf belegt"
        )
    if decision.conclusion == STARTUP_FAILURE_CONCLUSION:
        return (
            f"angenommen, aber nicht gestartet (`{STARTUP_FAILURE_CONCLUSION}`) – "
            "es lief keine Prüfung, es gibt kein Joblog"
        )
    return (
        "angenommen, aber nicht einsatzbereit "
        f"(`{decision.conclusion or 'unbekannt'}`) – Bereitschaftsprüfung nicht bestanden"
    )


def _registration_line(decision: StageDecision) -> str:
    removal = decision.removal_days
    if decision.cause != CAUSE_OFFLINE:
        return (
            "verbunden – der Runner nimmt Jobs an; GitHubs "
            f"{removal}-Tage-Entfernung greift hier nicht"
        )
    removal_day = decision.since + timedelta(days=removal)
    remaining = removal - decision.days
    if remaining > 0:
        return (
            f"GitHub entfernt einen Runner nach {removal} Tagen ohne Verbindung – "
            f"voraussichtlich ab {removal_day.isoformat()} (**noch {remaining} Tage**). "
            "Danach genügt Wiederbeleben nicht mehr"
        )
    return (
        f"voraussichtlich seit {removal_day.isoformat()} **entfernt** – GitHubs Frist "
        f"von {removal} Tagen ohne Verbindung ist um {-remaining} Tage überschritten; "
        "Neuregistrierung nötig"
    )


def _next_stage_line(decision: StageDecision, *, today: date, simulated: bool = False) -> str:
    stages = decision.stages
    label = retired_label(decision.platform, today)
    if decision.stage_to_post >= len(stages):
        if simulated:
            return (
                f"keine – im Ernstfall Austragung (Label `{label}` am Betriebs-Issue), "
                "in der Simulation unterblieben"
            )
        return f"keine – Plattform ausgetragen (Label `{label}` am Betriebs-Issue)"
    index = decision.stage_to_post  # naechste Stufe ist 1-basiert index+1
    due_day = decision.since + timedelta(days=stages[index])
    text = f"Stufe {index + 1} am {due_day.isoformat()} ({stages[index]} Tage)"
    if index + 1 == len(stages):
        text += (
            ": Austragung aus dem erwarteten Bestand – Label "
            f"`{RETIRED_LABEL_PREFIX}:{decision.platform}:<datum>` am Betriebs-Issue; "
            "Heartbeat und Abnahme-Matrix führen die Plattform dann als „ausgetragen\""
        )
    return text


def _remedy_line(
    decision: StageDecision, *, today: date, repo: str, issue: str, simulated: bool = False,
) -> str:
    label = retired_label(decision.platform, today)
    setup = "`docs/RUNNER_SETUP.md`"
    if decision.stage_to_post >= len(decision.stages):
        where = f"#{issue}" if issue else "dem Betriebs-Issue"
        return (
            ("**Reaktivierung (im Ernstfall):** " if simulated else "**Reaktivierung:** ")
            + f"Gerät nach {setup} §2 (macOS) bzw. §3 (Pi) neu "
            "registrieren"
            + (" und die Härtung nachziehen (§2.3/§3.4)" if decision.cause == CAUSE_NOT_READY else "")
            + f", dann das Label von {where} entfernen (`gh issue edit {issue or '<issue>'} "
            f"--repo {repo} --remove-label '{label}'`) und den Heartbeat von Hand starten "
            "(Kommandos in §4). Bis dahin erwartet der Heartbeat die Plattform nicht, und "
            "die Abnahme-Matrix führt sie als „ausgetragen seit "
            f"{today.isoformat()}\" (kein Abnahmeergebnis, Freigabe bleibt blockiert)."
        )
    if decision.cause == CAUSE_OFFLINE:
        return (
            f"**Abhilfe:** Gerät einschalten bzw. Runner-Dienst starten – {setup} §5 "
            "(Wiederbeleben statt neu aufsetzen). Ist die Registrierung bereits "
            "entfernt: Neuregistrierung nach §2/§3, danach Heartbeat von Hand starten (§0.2)."
        )
    remedy = (
        f"**Abhilfe:** Das Joblog des Runner-Jobs nennt den fehlenden Punkt – Härtung "
        f"nach {setup} §2.3 (macOS) bzw. §3.4 (Pi), Störungstabelle §5."
    )
    if decision.conclusion == STARTUP_FAILURE_CONCLUSION:
        remedy += (
            " Bei `startup_failure` gibt es kein Joblog: Runner-Workspace (`_work`) "
            "bereinigen bzw. Dienst neu starten und den Heartbeat erneut anstoßen."
        )
    return remedy


def render_stage_comment(
    decision: StageDecision,
    *,
    mention: str,
    run_url: str,
    today: date,
    repo: str,
    issue: str = "",
    simulated: bool = False,
) -> str:
    """Stufenkommentar fuer das Betriebs-Issue.

    Die ``@``-Erwaehnung ist der E-Mail-Kanal: GitHub benachrichtigt den
    Erwaehnten unabhaengig vom Watch-Status des Threads. Der Marker steht als
    HTML-Kommentar in der ersten Zeile, damit der naechste Lauf ihn findet.
    """
    stage = decision.stage_to_post
    total = len(decision.stages)
    icon = "⛔" if stage >= total else "⚠️"
    since_text = decision.since.isoformat()
    if decision.at_least:
        since_text = f"mindestens {since_text}"
    days_text = f"≥ {decision.days}" if decision.at_least else str(decision.days)
    if stage >= total:
        headline = f"nach {days_text} Tagen ausgetragen"
        lead = "die Plattform ist aus dem erwarteten Bestand ausgetragen."
    else:
        headline = f"seit {days_text} Tagen ohne bestandenen Heartbeat"
        lead = (
            "erster Hinweis der gestuften Eskalation (#958)."
            if stage == 1
            else f"{stage}. Hinweis der gestuften Eskalation (#958)."
        )
    lines = [
        f"<!-- {stage_marker(decision.platform, decision.since, stage)} -->",
        f"## {icon} Runner-Heartbeat – Stufe {stage}/{total}: {decision.job} {headline}",
        "",
    ]
    if simulated:
        lines += [
            "> **Simulation** (#958, HB-STUFE-05): kein echter Befund – dieser "
            "Kommentar belegt nur den E-Mail-Weg der Stufe. Es wurde nichts ausgetragen.",
            "",
        ]
    lines += [
        f"@{mention} – {lead}",
        "",
        "| | |",
        "| --- | --- |",
        f"| Plattform / Runner-Job | `{decision.platform}` / {decision.job} |",
        f"| Ohne bestandenen Heartbeat seit | {since_text} ({days_text} Tage, Stand {today.isoformat()}) |",
        f"| Befund heute | {_cause_line(decision)} |",
        f"| GitHub-Registrierung | {_registration_line(decision)} |",
        f"| Nächste Stufe | {_next_stage_line(decision, today=today, simulated=simulated)} |",
        "",
        _remedy_line(decision, today=today, repo=repo, issue=issue, simulated=simulated),
        "",
    ]
    if run_url:
        lines += [f"Lauf: {run_url}", ""]
    return "\n".join(lines)


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
    stages: tuple[int, ...] = OFFLINE_STAGE_DAYS,
    removal_days: int = GITHUB_RUNNER_REMOVAL_DAYS,
    retired: dict[str, date] | None = None,
    decisions: Iterable[StageDecision] = (),
    stage_observation: tuple[bool, str] = (True, ""),
    comment_issue: str = "",
    simulation: tuple[str, StageDecision] | None = None,
) -> dict[str, Any]:
    """Bericht (Schema 1). Die Eskalationsfelder sind seit #958 additiv:
    ``offline_stages`` je Plattform mit belegtem FAIL, ``stage_observation``
    als Fail-safe-Vermerk, ``retired`` fuer ausgetragene Plattformen."""
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
        "failed_job_conclusions": [
            {"name": name, "conclusion": conclusion}
            for name, conclusion in state.failed_conclusions
        ],
        "pending_jobs": list(state.pending),
        "inconclusive_jobs": [
            {"name": name, "conclusion": conclusion}
            for name, conclusion in state.inconclusive
        ],
        "observed": state.observed,
        "acceptance_expired": state.acceptance_expired,
        "stage_days": list(stages),
        "removal_days": removal_days,
        "retired": {
            platform: day.isoformat() for platform, day in sorted((retired or {}).items())
        },
        "offline_stages": [decision.as_dict() for decision in decisions],
        "stage_observation": {
            "observed": stage_observation[0], "detail": stage_observation[1],
        },
        "comment_issue": comment_issue,
        "simulation": (
            {"issue": simulation[0], "decision": simulation[1].as_dict()}
            if simulation is not None
            else None
        ),
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
        failed_conclusions = {
            str(entry.get("name", "")): str(entry.get("conclusion") or "")
            for entry in report.get("failed_job_conclusions", [])
            if isinstance(entry, dict)
        }
        lines.append("| Runner-Job | Zustand |")
        lines.append("| --- | --- |")
        for name in expected:
            if name in queued:
                status = "❌ wartet auf einen Runner"
            elif name in failed and failed_conclusions.get(name) == STARTUP_FAILURE_CONCLUSION:
                status = f"❌ angenommen, aber nicht gestartet ({STARTUP_FAILURE_CONCLUSION})"
            elif name in failed:
                conclusion = failed_conclusions.get(name) or "unbekannt"
                status = f"❌ angenommen, aber nicht einsatzbereit ({conclusion})"
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
    retired = report.get("retired") or {}
    if isinstance(retired, dict) and retired:
        for platform, since in sorted(retired.items()):
            lines.append(
                f"⛔ `{platform}` ist seit {since} ausgetragen (Label "
                f"`{RETIRED_LABEL_PREFIX}:{platform}:{since}` am Betriebs-Issue) und wird "
                "nicht erwartet – Reaktivierung: `docs/RUNNER_SETUP.md` §4."
            )
        lines.append("")
    stages = tuple(int(day) for day in report.get("stage_days") or OFFLINE_STAGE_DAYS)
    removal = int(report.get("removal_days") or GITHUB_RUNNER_REMOVAL_DAYS)
    if report["verdict"] == VERDICT_FAIL:
        stage_text = "/".join(str(day) for day in stages)
        lines.append(
            "Abhilfe: Gerät einschalten bzw. Runner-Dienst starten "
            "(`docs/RUNNER_SETUP.md` §5, `docs/RELEASE_AUTOMATION.md` §6). Hat der "
            "Runner den Job angenommen und die Prüfung nicht bestanden, nennt sein "
            "Joblog den fehlenden Punkt – Härtung siehe §2.1/§2.2. Bleibt ein Runner "
            f"länger als {removal} Tage ohne Verbindung, entfernt GitHub seine "
            f"Registrierung; die gestufte Eskalation (§7) meldet nach {stage_text} "
            "Tagen im Betriebs-Issue und trägt die Plattform mit der letzten Stufe aus."
        )
        if any(
            entry.get("conclusion") == STARTUP_FAILURE_CONCLUSION
            for entry in report.get("failed_job_conclusions", [])
            if isinstance(entry, dict)
        ):
            lines.append(
                f"Bei `{STARTUP_FAILURE_CONCLUSION}` lief keine Prüfung und es gibt kein Joblog: "
                "Runner-Workspace (`_work`) bereinigen bzw. Dienst neu starten "
                "(`docs/RELEASE_AUTOMATION.md` §6) und den Heartbeat erneut anstoßen."
            )
        lines.append("")
    lines.extend(_render_stage_section(report, stages=stages))
    if report.get("run_url"):
        lines.append(f"Lauf: {report['run_url']}")
        lines.append("")
    return "\n".join(lines)


def _render_stage_section(report: dict[str, Any], *, stages: tuple[int, ...]) -> list[str]:
    """Eskalationsabschnitt der Summary (#958) – nur, wenn es etwas zu sagen gibt."""
    observation = report.get("stage_observation") or {}
    decisions = [entry for entry in report.get("offline_stages") or [] if isinstance(entry, dict)]
    lines: list[str] = []
    if isinstance(observation, dict) and observation.get("observed") is False:
        lines += [
            "⚠️ Stufenauswertung ohne Entscheidung: "
            f"{observation.get('detail') or 'Historie oder Kommentare nicht lesbar.'}",
            "",
        ]
    simulation = report.get("simulation")
    if isinstance(simulation, dict) and isinstance(simulation.get("decision"), dict):
        sim = simulation["decision"]
        sim_posted = int(sim.get("stage_to_post") or 0)
        lines += [
            f"🧪 Simulation (#958, HB-STUFE-05) gegen #{simulation.get('issue')}: "
            f"`{sim.get('platform')}` seit {sim.get('offline_since')} ({sim.get('days')} Tage), "
            f"Stufe {sim.get('stage_due')} fällig – "
            + (f"Stufe {sim_posted} gepostet." if sim_posted else "bereits gepostet, nichts neu.")
            + " Keine Austragung, echte Auswertung unberührt.",
            "",
        ]
    if not decisions:
        return lines
    issue = str(report.get("comment_issue") or "")
    where = f" in #{issue}" if issue else ""
    lines += [
        "### Eskalation (#958)",
        "",
        "| Plattform | Ohne bestandenen Heartbeat seit | Tage | Stufe fällig | Kommentar |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in decisions:
        days = int(entry.get("days") or 0)
        since = str(entry.get("offline_since") or "")
        if entry.get("at_least"):
            since, days_text = f"mindestens {since}", f"≥ {days}"
        else:
            days_text = str(days)
        due = int(entry.get("stage_due") or 0)
        to_post = int(entry.get("stage_to_post") or 0)
        posted = [int(stage) for stage in entry.get("stages_posted") or []]
        if due == 0:
            next_index = 0
            due_text = f"keine (Stufe 1 ab {stages[0]} Tagen)"
        else:
            next_index = due
            due_text = f"{due} (≥ {stages[due - 1]} Tage)"
        if to_post:
            comment = f"Stufe {to_post} heute gepostet{where}"
        elif due and due in posted:
            comment = f"Stufe {due} bereits gepostet{where}"
        else:
            comment = "keiner fällig"
        if next_index < len(stages):
            comment += f"; nächste Stufe {next_index + 1} nach {stages[next_index]} Tagen"
        if entry.get("retire"):
            comment += f" – **Austragung** (Label `{RETIRED_LABEL_PREFIX}:{entry.get('platform')}:…`)"
        lines.append(
            f"| {entry.get('job')} (`{entry.get('platform')}`) | {since} | {days_text} | "
            f"{due_text} | {comment} |"
        )
    lines.append("")
    return lines


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


@dataclass(frozen=True)
class Simulation:
    """Simulierte Episode fuer den einmaligen Mail-Nachweis (HB-STUFE-05)."""

    platform: str
    since: date
    issue: str


def simulation_from_args(
    *, offline_since: str, target_issue: str, platform: str, real_issue: str
) -> Simulation | None:
    """Simulationseingaben pruefen – **nur gemeinsam wirksam**, nie gegen das Betriebs-Issue.

    Eine halb gesetzte Simulation darf weder still ins echte Issue schreiben
    noch still wirkungslos bleiben: beides ist ein Fehler mit Begruendung.
    """
    since_raw, issue = offline_since.strip(), target_issue.strip()
    if not since_raw and not issue:
        return None
    if not since_raw or not issue:
        raise ValueError(
            "Simulation braucht simulate_offline_since UND simulate_target_issue "
            "gemeinsam – eine halbe Angabe ist wirkungslos und wird abgewiesen."
        )
    if not re.fullmatch(r"[1-9][0-9]*", issue):
        raise ValueError("simulate_target_issue muss eine positive Issue-Nummer sein.")
    if issue == real_issue.strip():
        raise ValueError(
            f"Simulation nie gegen das Betriebs-Issue #{issue} – ein Test-Issue angeben."
        )
    try:
        since = date.fromisoformat(since_raw)
    except ValueError as exc:
        raise ValueError(
            f"simulate_offline_since={since_raw!r} ist kein ISO-Datum (YYYY-MM-DD)."
        ) from exc
    if platform not in HEARTBEAT_JOB_NAMES:
        raise ValueError(f"simulate_platform muss eine von {', '.join(HEARTBEAT_JOB_NAMES)} sein.")
    return Simulation(platform=platform, since=since, issue=issue)


def simulated_decision(
    simulation: Simulation,
    *,
    comments: Iterable[tuple[date, str]],
    today: date,
    stages: tuple[int, ...] = OFFLINE_STAGE_DAYS,
    removal_days: int = GITHUB_RUNNER_REMOVAL_DAYS,
) -> StageDecision:
    """Stufenentscheidung aus einer simulierten Episode (Ursache offline).

    Nur die Historie ist simuliert – die Marker werden echt gegen das
    Test-Issue geprueft, damit auch die Idempotenz im Nachweis sichtbar wird.
    Eine Simulation traegt nie aus.
    """
    days = (today - simulation.since).days
    due = offline_stage(days, stages)
    posted = posted_stages(comments, simulation.platform, simulation.since)
    return StageDecision(
        platform=simulation.platform, job=HEARTBEAT_JOB_NAMES[simulation.platform],
        cause=CAUSE_OFFLINE, conclusion="", since=simulation.since, at_least=False,
        days=days, stage_due=due, stages_posted=posted,
        stage_to_post=due if due and due not in posted else 0, retire=False,
        stages=stages, removal_days=removal_days,
    )


def write_stage_files(
    decisions: Iterable[StageDecision],
    *,
    directory: Path,
    mention: str,
    run_url: str,
    today: date,
    repo: str,
    simulated: bool,
    issue: str = "",
) -> tuple[list[str], list[str]]:
    """Kommentardateien und Austragungsliste fuer den Workflow schreiben.

    Stufen 1 und 2 postet der ``watch``-Job selbst
    (``stage-comment-<plattform>.md``); Stufe 3 postet erst der
    ``retire``-Job **nach** dem Setzen der Variable
    (``retire-comment-<plattform>.md``), damit der Kommentar nie eine
    Austragung behauptet, die nicht stattgefunden hat. ``retire.tsv`` nennt
    je Zeile Plattform, Label und Datum – das Label kommt von hier, damit das
    Namensschema nicht in der Shell nachgebaut wird.
    In der Simulation gibt es nur ``simulation-comment-<plattform>.md`` – ein
    eigener Dateiname und ein eigenes Ziel-Issue, damit ein Simulationslauf
    die echte Eskalation desselben Tages weder verdraengt noch mit ihr
    vermischt (Review PR #981) – und nie ``retire.tsv``.
    """
    directory.mkdir(parents=True, exist_ok=True)
    stage_platforms: list[str] = []
    retire_platforms: list[str] = []
    retire_rows: list[str] = []
    for decision in decisions:
        if decision.stage_to_post:
            body = render_stage_comment(
                decision, mention=mention, run_url=run_url, today=today, repo=repo,
                issue=issue, simulated=simulated,
            )
            if simulated:
                path = directory / f"simulation-comment-{decision.platform}.md"
                stage_platforms.append(decision.platform)
            elif decision.stage_to_post >= len(decision.stages):
                path = directory / f"retire-comment-{decision.platform}.md"
            else:
                path = directory / f"stage-comment-{decision.platform}.md"
                stage_platforms.append(decision.platform)
            path.write_text(body, encoding="utf-8")
            print(f">> Stufenkommentar geschrieben: {path}")
        if decision.retire and not simulated:
            retire_platforms.append(decision.platform)
            retire_rows.append(
                f"{decision.platform}\t{retired_label(decision.platform, today)}\t{today.isoformat()}"
            )
    if retire_rows:
        target = directory / "retire.tsv"
        target.write_text("\n".join(retire_rows) + "\n", encoding="utf-8")
        print(f">> Austragungsliste geschrieben: {target}")
    return stage_platforms, retire_platforms


def fetch_issue_labels(
    repo: str,
    issue: str,
    token: str,
    *,
    api_url: str,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[str]:
    """Label-Namen eines Issues – ein einziger Aufruf, ``issues: read`` genuegt."""
    url = f"{api_url}/repos/{repo}/issues/{issue}"
    with opener(_request(url, token), timeout=REQUEST_TIMEOUT_S) as response:
        payload = json.load(response)
    labels = payload.get("labels") if isinstance(payload, dict) else None
    if not isinstance(labels, list):
        raise ValueError("Issue-Antwort ohne Label-Liste")
    return [
        str(entry.get("name") or "") if isinstance(entry, dict) else str(entry)
        for entry in labels
    ]


def _cmd_retired_status(args: argparse.Namespace) -> int:
    """Ausgetragene Plattformen aus den Labels des Betriebs-Issues (#958).

    Liefert je Plattform einen Step-Output (Datum oder leer), den beide
    Self-hosted-Workflows in ihren ``if``-Bedingungen lesen. Fail-closed:
    Ohne lesbares Issue gibt es keinen Bestand – der Lauf bricht mit
    Begruendung ab, statt eine ausgetragene Plattform still wieder zu
    erwarten oder eine aktive still auszutragen.
    """
    issue = args.issue.strip()
    if not re.fullmatch(r"[1-9][0-9]*", issue):
        print(
            "::error title=Kein Meldeweg::RUNNER_HEARTBEAT_ISSUE fehlt oder ist keine "
            "positive Issue-Nummer – ohne Betriebs-Issue ist der Austragungsbestand "
            "nicht lesbar (RELEASE_AUTOMATION §7)."
        )
        return 1
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        print("::error::Kein GH_TOKEN/GITHUB_TOKEN gesetzt (issues: read noetig).")
        return 2
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    try:
        retired = parse_retired_labels(fetch_issue_labels(args.repo, issue, token, api_url=api_url))
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print(f"::error title=Austragungsbestand nicht lesbar::Labels von #{issue}: {exc}")
        return 1
    for platform in HEARTBEAT_JOB_NAMES:
        day = retired.get(platform)
        append_github_output(retired_output_name(platform), day.isoformat() if day else "")
    append_github_output(
        "retired", " ".join(f"{p}={d.isoformat()}" for p, d in sorted(retired.items()))
    )
    if retired:
        for platform, day in sorted(retired.items()):
            print(
                f"::warning title=Plattform ausgetragen::{platform} seit {day.isoformat()} "
                f"(Label {retired_label(platform, day)} an #{issue}); Reaktivierung: "
                "docs/RUNNER_SETUP.md §4"
            )
    else:
        print(f"[heartbeat] Keine ausgetragene Plattform (Labels von #{issue}).")
    return 0


def _cmd_watch(args: argparse.Namespace) -> int:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        print("::error::Kein GH_TOKEN/GITHUB_TOKEN gesetzt (actions: read noetig).")
        return 2
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    stages = tuple(args.stage_days)
    try:
        retired = parse_retired(args.retired_since)
        simulation = simulation_from_args(
            offline_since=args.simulate_offline_since,
            target_issue=args.simulate_target_issue,
            platform=args.simulate_platform, real_issue=args.issue,
        )
    except ValueError as exc:
        print(f"::error title=Heartbeat-Konfiguration ungueltig::{exc}")
        return 2
    today = date.fromisoformat(args.today) if args.today else datetime.now(timezone.utc).date()
    expected = expected_jobs(x86_enabled=args.x86_64_enabled, retired=retired)
    comment_issue = args.issue.strip()
    if not expected:
        # Ein leerer Bestand darf nie als "alle bestanden" durchgehen.
        detail = (
            "Kein Runner erwartet – alle Plattformen sind ausgetragen ("
            + ", ".join(f"{p} seit {d.isoformat()}" for p, d in sorted(retired.items()))
            + "). Reaktivierung: docs/RUNNER_SETUP.md §4."
        )
        report = build_report(
            verdict=VERDICT_UNOBSERVED, detail=detail, expected=expected,
            state=QueueState(known=(), queued=()), acceptance_s=args.acceptance_seconds,
            deadline_s=args.deadline_seconds, run_url=args.run_url, stages=stages,
            removal_days=args.removal_days, retired=retired, comment_issue=comment_issue,
        )
        write_outputs(report, report_path=args.report, summary_path=args.summary)
        print(f"::warning title=Heartbeat ohne Bestand::{detail}")
        return 0

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

    # Eskalation (#958): nur fuer belegte FAILs, nur mit Meldeweg, und nur
    # auf frischer Grundlage – Historie und Kommentarliste muessen lesbar sein.
    # Die Simulation laeuft **zusaetzlich**, nie statt der echten Auswertung
    # (Review PR #981): eigenes Ziel-Issue, eigene Dateien, keine Austragung.
    decisions: list[StageDecision] = []
    stage_observation = (True, "")
    simulated: list[StageDecision] = []
    if simulation is not None:
        try:
            comments = fetch_issue_comments(args.repo, simulation.issue, token, api_url=api_url)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            stage_observation = (False, f"Kommentare von #{simulation.issue} nicht lesbar ({exc}).")
        else:
            simulated = [
                simulated_decision(
                    simulation, comments=comments, today=today, stages=stages,
                    removal_days=args.removal_days,
                )
            ]
    if verdict == VERDICT_FAIL and failing_platforms(state):
        if not comment_issue:
            stage_observation = (False, "Kein Betriebs-Issue (--issue) uebergeben.")
        else:
            job_names = [HEARTBEAT_JOB_NAMES[p] for p, _c, _k in failing_platforms(state)]
            try:
                comments = fetch_issue_comments(args.repo, comment_issue, token, api_url=api_url)
                records = fetch_run_history(
                    args.repo, token, api_url=api_url,
                    since=today - timedelta(days=HISTORY_WINDOW_DAYS),
                    exclude_run_id=args.run_id, job_names=job_names,
                )
            except (urllib.error.URLError, OSError, ValueError) as exc:
                stage_observation = (
                    False, f"Laufhistorie oder Kommentare nicht lesbar ({exc}) – keine Stufe.",
                )
            else:
                decisions = decide_stages(
                    state, records=records, comments=comments, today=today,
                    stages=stages, removal_days=args.removal_days,
                )
    stage_platforms, retire_platforms = write_stage_files(
        decisions, directory=args.comments_dir, mention=args.mention, run_url=args.run_url,
        today=today, repo=args.repo, simulated=False, issue=comment_issue,
    )
    simulation_platforms, _never = write_stage_files(
        simulated, directory=args.comments_dir, mention=args.mention, run_url=args.run_url,
        today=today, repo=args.repo, simulated=True, issue=comment_issue,
    )
    append_github_output("stage_comments", " ".join(stage_platforms))
    append_github_output("retire", " ".join(retire_platforms))
    append_github_output("comment_issue", comment_issue)
    append_github_output("simulation_comments", " ".join(simulation_platforms))
    append_github_output("simulation_issue", simulation.issue if simulation else "")

    report = build_report(
        verdict=verdict, detail=detail, expected=expected, state=state,
        acceptance_s=args.acceptance_seconds,
        deadline_s=args.deadline_seconds, run_url=args.run_url,
        stages=stages, removal_days=args.removal_days, retired=retired,
        decisions=decisions, stage_observation=stage_observation,
        comment_issue=comment_issue,
        simulation=(simulation.issue, simulated[0]) if simulation and simulated else None,
    )
    write_outputs(report, report_path=args.report, summary_path=args.summary)
    if not stage_observation[0]:
        print(f"::warning title=Stufenauswertung ohne Entscheidung::{stage_observation[1]}")
    for decision, label in [(d, "") for d in decisions] + [(d, " – Simulation") for d in simulated]:
        if decision.stage_to_post:
            print(
                f"[heartbeat] Stufe {decision.stage_to_post} fuer {decision.platform} "
                f"faellig (seit {decision.since.isoformat()}, {decision.days} Tage){label}"
            )
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

    retired_cmd = sub.add_parser(
        "retired-status", help="Ausgetragene Plattformen aus den Labels des Betriebs-Issues",
    )
    retired_cmd.add_argument("--repo", required=True)
    retired_cmd.add_argument("--issue", default="", help="Wert von RUNNER_HEARTBEAT_ISSUE")
    retired_cmd.set_defaults(func=_cmd_retired_status)

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
    # Gestufte Eskalation (#958): Zahlen explizit uebergeben, damit sie im
    # Joblog stehen; Voreinstellung und einzige Quelle bleiben die Konstanten.
    watch_cmd.add_argument(
        "--stage-days", type=int, nargs=len(OFFLINE_STAGE_DAYS), default=list(OFFLINE_STAGE_DAYS),
        metavar="TAGE", help="Faelligkeit der drei Stufen in Tagen ohne bestandenen Heartbeat.",
    )
    watch_cmd.add_argument(
        "--removal-days", type=int, default=GITHUB_RUNNER_REMOVAL_DAYS,
        help="GitHubs Frist, nach der ein nicht verbundener Runner entfernt wird.",
    )
    watch_cmd.add_argument(
        "--issue", default="",
        help="Betriebs-Issue fuer Stufenkommentare (Wert von RUNNER_HEARTBEAT_ISSUE).",
    )
    watch_cmd.add_argument(
        "--mention", default="", help="GitHub-Login, der in Stufenkommentaren erwaehnt wird.",
    )
    watch_cmd.add_argument(
        "--retired-since", action="append", default=[], metavar="PLATTFORM=DATUM",
        help="Ausgetragene Plattform (Output von retired-status); leer = aktiv.",
    )
    watch_cmd.add_argument(
        "--comments-dir", type=Path, default=Path("heartbeat"),
        help="Ablage der Stufenkommentare und der Austragungsliste.",
    )
    watch_cmd.add_argument("--simulate-offline-since", default="", metavar="DATUM")
    watch_cmd.add_argument("--simulate-target-issue", default="", metavar="ISSUE")
    watch_cmd.add_argument(
        "--simulate-platform", default="linux-arm64", choices=tuple(HEARTBEAT_JOB_NAMES),
    )
    watch_cmd.add_argument("--today", default="", help="ISO-Datum (nur für Tests)")
    watch_cmd.set_defaults(func=_cmd_watch)

    args = parser.parse_args(argv)
    stage_days = getattr(args, "stage_days", None)
    if stage_days is not None:
        # Streng steigend und positiv – eine Stufe, die vor der vorigen faellig
        # wird, machte "die hoechste faellige Stufe" mehrdeutig.
        if any(day <= 0 for day in stage_days) or list(stage_days) != sorted(set(stage_days)):
            parser.error(f"--stage-days muss streng steigend und positiv sein: {stage_days}")
        if getattr(args, "removal_days", 1) <= 0:
            parser.error("--removal-days muss positiv sein.")
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
