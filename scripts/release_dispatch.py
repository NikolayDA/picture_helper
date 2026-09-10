#!/usr/bin/env python3
"""Owner-Skript fuer die Release-Dispatches (#1039).

Runbook-Schritte 3, 5, 6, 8 und 9 dispatchen drei Workflows von Hand. Der
Release-Owner kopiert dabei ``CANDIDATE_RUN_ID``, ``ACCEPTANCE_RUN_ID``,
``APPROVAL_ARTIFACT_NAME``, ``RELEASE_REF``, ``RELEASE_TAG``,
``PREDECESSOR_TAG`` und ``RELEASE_ISSUE`` zwischen den Schritten – #914 nennt
genau das als fehleranfaellig. Dieses Skript leitet die IDs stattdessen aus der
GitHub-API ab und haelt die Bindungswerte in einer versionierten Zustandsdatei.

**Was es nicht tut.** Es aendert weder ``release-linux.yml`` noch
``release-abnahme.yml``, ``release-publish.yml`` oder
``scripts/release_contract.py``. Es gibt kein Environment-Gate und keinen
automatischen Uebergang zum Publish: ``approve`` zeigt nur, ``publish``
verlangt eine ausdrueckliche Bestaetigung. Die Handprozedur im Runbook bleibt
Rueckfallweg und Referenz – sie ist byteidentisch gueltig, dieses Skript ruft
dieselben ``gh``-Kommandos und dieselben Vertragspruefungen auf.

Drei Eigenschaften tragen den Aufbau:

1. **``workflow_dispatch`` liefert keine Run-ID zurueck** (HTTP 204 ohne Body).
   Der erzeugte Lauf wird deshalb korreliert: vor dem Dispatch die bereits
   bekannten Run-IDs erfassen, danach genau **einen neuen** Lauf mit passendem
   Workflow, Ereignis, Ref, Head-SHA und Erstellungszeit akzeptieren. Null oder
   mehrere Treffer brechen benannt ab, statt zu raten.
2. **Kein Wiederholungsaufruf erzeugt einen zweiten Lauf.** Zwei Fenster,
   zwei Sperren: Vor jedem Dispatch wird ein ``pending``-Eintrag atomar
   geschrieben – beim Wiederanlauf wird zuerst versoehnt (genau ein passender
   neuer Lauf: uebernehmen; keiner: erneut dispatchen; mehrere: abbrechen).
   Und steht die Run-ID schon im Zustand, weil erst das Beobachten abbrach,
   wird sie wieder aufgegriffen statt neu ausgeloest. Ein bewusst neuer Lauf
   auf demselben SHA bleibt der Handprozedur bzw. einer eigenen Zustandsdatei
   vorbehalten – er ist eine Entscheidung, kein Nebeneffekt.
3. **Fremder oder beschaedigter Zustand ist fail-closed.** Die Zustandsdatei
   traegt Schema, Repository, Version, Ref und Kandidaten-SHA; ein Kommando,
   dessen Bindung davon abweicht, bricht ab, statt Run-IDs zweier Releases zu
   mischen. Run-IDs sind keine Secrets – die Datei liegt trotzdem mit
   restriktiven Rechten ausserhalb des Arbeitsbaums, damit sie weder in einen
   Commit noch in ein Artefakt geraet.

Der Kandidaten-SHA wird **nie** aus dem Ref abgelesen: ``candidate`` verlangt
ihn als ``--candidate-sha`` aus Runbook-Schritt 2, wo er im Release-Issue
protokolliert ist. Erst dadurch pruefen ``verify-ref-protection`` und
``verify-release-ref`` gegen eine unabhaengige Quelle, statt den Ref gegen sich
selbst. ``approve`` und ``finalize`` nutzen Vertrag und Checkliste aus genau
dieser Kandidatenrevision – nicht aus dem gerade ausgecheckten Arbeitsbaum.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Final

try:  # Dateiaufruf: ``python scripts/release_dispatch.py``
    import release_contract as rc
    import release_update_dispatch as rud
except ModuleNotFoundError:  # Import ueber Dateipfad bzw. als ``scripts.…``
    from scripts import release_contract as rc
    from scripts import release_update_dispatch as rud

#: Standard-Repository. Dieselbe feste Angabe wie in den ``gh api``-Aufrufen des
#: Runbooks; ``--repo`` bleibt fuer Forks und Proben ueberschreibbar.
DEFAULT_REPO: Final = "NikolayDA/picture_helper"

BUILD_WORKFLOW: Final = "release-linux.yml"
ACCEPTANCE_WORKFLOW: Final = "release-abnahme.yml"
PUBLISH_WORKFLOW: Final = "release-publish.yml"

#: Pfade der Workflows im Repository – die Form, in der GitHub sie in den
#: Run-Metadaten fuehrt und in der ``release_contract`` sie erwartet.
_WORKFLOW_PATHS: Final = {
    BUILD_WORKFLOW: rc.BUILD_WORKFLOW,
    ACCEPTANCE_WORKFLOW: rc.ACCEPTANCE_WORKFLOW,
    PUBLISH_WORKFLOW: ".github/workflows/release-publish.yml",
}

#: Felder, die die Korrelation braucht. ``event``/``headBranch``/``headSha``
#: werden zusaetzlich am Datensatz geprueft, obwohl ``gh run list`` bereits
#: danach filtert: Ein Filter, dem man blind vertraut, ist genau die Stelle, an
#: der ein Dry-Run als Kandidat durchginge.
RUN_FIELDS: Final = (
    "databaseId,displayTitle,status,conclusion,url,createdAt,headSha,headBranch,event"
)
#: Wie viele der juengsten Laeufe je Abfrage betrachtet werden.
RUN_LIST_LIMIT: Final = 50
#: Polling nach dem Dispatch. GitHub legt den Lauf in aller Regel in Sekunden
#: an; das Budget deckt eine langsame Antwort ab, ohne den Owner zu binden.
POLL_ATTEMPTS: Final = 20
POLL_INTERVAL_S: Final = 6.0
#: Toleranz der Erstellungszeit gegen Uhrenversatz zwischen Owner-Rechner und
#: GitHub. Die **tragende** Abgrenzung ist die Menge der vor dem Dispatch
#: bekannten Run-IDs; die Zeit ist die zweite, unabhaengige Schranke. Ohne
#: Toleranz liesse eine vorgehende lokale Uhr den soeben ausgeloesten Lauf
#: durchfallen und erzeugte einen falschen "nicht gefunden"-Abbruch.
CLOCK_SKEW_TOLERANCE_S: Final = 120

STATE_SCHEMA: Final = 1
STATE_KIND: Final = "release-dispatch-state"
#: Dateimodus der Zustandsdatei. Run-IDs sind keine Secrets; der Zustand ist
#: aber die einzige Bindung zwischen den Schritten und geht niemanden sonst an.
STATE_MODE: Final = 0o600

_VERSION_RE: Final = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_TAG_RE: Final = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+(?:[.-][0-9A-Za-z.]+)?$")
_SHA_RE: Final = re.compile(r"^[0-9a-f]{40}$")
_ISSUE_RE: Final = re.compile(r"^[1-9][0-9]*$")
_MANIFEST_ARTIFACT_RE: Final = re.compile(r"^release-approval-manifest-([1-9][0-9]*)$")

#: Artefaktname der finalen Release-Instanz aus dem Update-Abnahmelauf (#919).
FINAL_INSTANCE_PATTERN: Final = "release-acceptance-instance-final-*"

#: Operationen mit Dispatch. ``approve`` und ``finalize`` loesen nichts aus und
#: schreiben deshalb auch keinen ``pending``-Eintrag.
OP_CANDIDATE: Final = "candidate"
OP_ACCEPTANCE: Final = "acceptance"
OP_PUBLISH: Final = "publish"


class DispatchError(RuntimeError):
    """Benannter Abbruch. Jede Meldung nennt Ursache **und** naechsten Schritt."""


# ── Zeit ───────────────────────────────────────────────────────────────


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_github_timestamp(value: object, *, field: str) -> datetime:
    """GitHub-Zeitstempel (``2026-09-10T12:00:00Z``) als aware ``datetime``.

    ``datetime.fromisoformat`` kennt das abschliessende ``Z`` erst ab Python
    3.11; das Projekt zielt auf 3.10.
    """
    if not isinstance(value, str) or not value:
        raise DispatchError(f"{field} fehlt oder ist kein Zeitstempel: {value!r}")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DispatchError(f"{field} ist kein ISO-8601-Zeitstempel: {value!r} ({exc})") from exc


# ── Ausfuehrung: gh, git, python ───────────────────────────────────────

#: Ein ``gh``-Aufruf ohne fuehrendes ``gh``; liefert stdout. Injizierbar, damit
#: Korrelation, Versoehnung und Abbruchbedingungen ohne Netz pruefbar sind
#: (Muster aus ``scripts/release_update_dispatch.py``).
Runner = Callable[[Sequence[str]], str]
#: Ein beliebiges Kommando mit vollstaendiger Argumentliste (``git``/``python``).
#: Liefert **Bytes**, nicht Text: ``git show <rev>:<pfad>`` gibt den Blob roh
#: heraus, und die Abnahme-Checkliste ist ueber ihren SHA-256 in der
#: Release-Instanz gepinnt (``release_contract.validate_release_instance``
#: vergleicht ``_sha256_file``). Ein ``text=True``-Kanal dekodierte mit
#: ``locale.getpreferredencoding`` und uebersetzte Zeilenenden – unter
#: ``LC_ALL=C`` ergaebe das entweder einen ``UnicodeDecodeError`` oder eine
#: Datei, deren Hash nicht mehr zur Kandidatenrevision passt. Der Fehler faende
#: sich erst am Release-Tag in Schritt 6, und seine Meldung saehe wie ein
#: inhaltlicher Checklisten-Drift aus.
Command = Callable[[Sequence[str]], bytes]
#: Ein streamendes Kommando – ``gh run watch`` schreibt direkt auf das Terminal
#: und liefert nur seinen Exit-Code.
Watcher = Callable[[int], int]


def render_command(argv: Sequence[str]) -> str:
    """Der ausgefuehrte Befehl als kopierbare Zeile.

    **Eine** Quelle fuer Anzeige und Wiederanlaufhinweis: Was hier steht, ist
    exakt das, was das Skript aufruft (Muster ``resume_command`` in
    ``scripts/prepare_release.py``).
    """
    return shlex.join(list(argv))


def traced(runner: Runner, *, echo: Callable[[str], None] = print) -> Runner:
    """Druckt jeden ``gh``-Aufruf, bevor er laeuft.

    Der Owner muss jederzeit von Hand weitermachen koennen; dafuer muss er
    sehen, welchen Befehl das Skript gerade absetzt.
    """

    def call(args: Sequence[str]) -> str:
        echo(f"$ {render_command(['gh', *args])}")
        return runner(args)

    return call


def _gh(args: Sequence[str]) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise DispatchError(
            f"gh {' '.join(args)} scheiterte (Exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout


def _command(argv: Sequence[str]) -> bytes:
    # Ohne ``text=True``: siehe Vertrag von ``Command``. Nur die Fehlermeldung
    # wird dekodiert, und dort verlustfrei-tolerant.
    result = subprocess.run(list(argv), capture_output=True, check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).decode("utf-8", "replace").strip()
        raise DispatchError(
            f"{render_command(argv)} scheiterte (Exit {result.returncode}): {detail}"
        )
    return result.stdout


def _watch(run_id: int) -> int:
    argv = ["gh", "run", "watch", str(run_id), "--exit-status"]
    print(f"$ {render_command(argv)}")
    return subprocess.run(argv, check=False).returncode


def _json(raw: str, *, field: str) -> Any:
    try:
        return json.loads(raw or "null")
    except json.JSONDecodeError as exc:
        raise DispatchError(f"{field} ist kein JSON: {exc}") from exc


# ── Zustandsdatei ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class PendingDispatch:
    """Ein abgesetzter, noch nicht korrelierter Dispatch.

    Er existiert genau zwischen ``gh workflow run`` und der uebernommenen
    Run-ID. Faellt das Skript in diesem Fenster aus, ist er beim naechsten Lauf
    die Anweisung, **zuerst zu suchen statt zu dispatchen**.
    """

    operation: str
    workflow: str
    ref: str
    expected_head_sha: str
    marker: str
    not_before: str
    known_run_ids: tuple[int, ...]
    recorded_at: str

    def as_json(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "workflow": self.workflow,
            "ref": self.ref,
            "expected_head_sha": self.expected_head_sha,
            "marker": self.marker,
            "not_before": self.not_before,
            "known_run_ids": list(self.known_run_ids),
            "recorded_at": self.recorded_at,
        }

    @staticmethod
    def from_json(payload: object) -> PendingDispatch:
        if not isinstance(payload, dict):
            raise DispatchError("pending-Eintrag ist kein Objekt")
        entry: dict[str, Any] = payload
        ids = entry.get("known_run_ids")
        # ``isinstance(True, int)`` ist wahr – ``bool`` deshalb ausdruecklich
        # abweisen, wie in ``_optional_run_id``.
        if not isinstance(ids, list) or any(
            not isinstance(i, int) or isinstance(i, bool) or i <= 0 for i in ids
        ):
            raise DispatchError("pending.known_run_ids ist keine Liste positiver Ganzzahlen")
        return PendingDispatch(
            operation=_text(entry.get("operation"), "pending.operation"),
            workflow=_text(entry.get("workflow"), "pending.workflow"),
            ref=_text(entry.get("ref"), "pending.ref"),
            expected_head_sha=_sha(entry.get("expected_head_sha"), "pending.expected_head_sha"),
            marker=str(entry.get("marker") or ""),
            not_before=_text(entry.get("not_before"), "pending.not_before"),
            known_run_ids=tuple(sorted(int(i) for i in ids)),
            recorded_at=_text(entry.get("recorded_at"), "pending.recorded_at"),
        )


@dataclass(frozen=True)
class ReleaseState:
    """Die Bindungswerte eines Releases – genau eines.

    ``repo``, ``version`` und ``candidate_sha`` sind die Identitaet; Tag und Ref
    werden daraus abgeleitet statt gespeichert, damit sie nicht auseinander
    laufen koennen.
    """

    repo: str
    version: str
    candidate_sha: str
    release_issue: str
    candidate_run_id: int | None = None
    acceptance_run_id: int | None = None
    approval_artifact_name: str = ""
    predecessor_tag: str = ""
    publish_run_id: int | None = None
    update_acceptance_run_id: int | None = None
    pending: PendingDispatch | None = None
    updated_at: str = ""

    @property
    def tag(self) -> str:
        return f"v{self.version}"

    @property
    def ref(self) -> str:
        return f"{rc.RELEASE_REF_PREFIX}{self.tag}"

    def as_json(self) -> dict[str, Any]:
        return {
            "schema": STATE_SCHEMA,
            "kind": STATE_KIND,
            "repo": self.repo,
            "version": self.version,
            "release_tag": self.tag,
            "release_ref": self.ref,
            "candidate_sha": self.candidate_sha,
            "release_issue": self.release_issue,
            "candidate_run_id": self.candidate_run_id,
            "acceptance_run_id": self.acceptance_run_id,
            "approval_artifact_name": self.approval_artifact_name,
            "predecessor_tag": self.predecessor_tag,
            "publish_run_id": self.publish_run_id,
            "update_acceptance_run_id": self.update_acceptance_run_id,
            "pending": self.pending.as_json() if self.pending else None,
            "updated_at": self.updated_at or _iso(_utc_now()),
        }


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise DispatchError(f"{field} fehlt oder ist leer")
    return value


def _sha(value: object, field: str) -> str:
    text = _text(value, field)
    if not _SHA_RE.fullmatch(text):
        raise DispatchError(f"{field} ist kein vollstaendiger 40-stelliger Commit-SHA: {text!r}")
    return text


def _optional_run_id(value: object, field: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise DispatchError(f"{field} ist keine positive Ganzzahl: {value!r}")
    return value


def default_state_path() -> Path:
    """Benutzer-State-Verzeichnis, **nie** das Repository.

    Im Arbeitsbaum waere die Datei ein unbekannter Pfad fuer das Freeze-Gate
    und stuende in jedem ``git status`` waehrend eines Releases im Weg.
    """
    root = os.environ.get("XDG_STATE_HOME")
    base = Path(root) if root else Path.home() / ".local" / "state"
    return base / "bgremover" / "release-dispatch.json"


def load_state(path: Path) -> ReleaseState | None:
    """Liest den Zustand fail-closed; ``None`` heisst "es gibt keinen"."""
    if not path.exists():
        return None
    payload = _json(path.read_text(encoding="utf-8"), field=f"Zustandsdatei {path}")
    if not isinstance(payload, dict):
        raise DispatchError(f"Zustandsdatei {path} enthaelt kein Objekt")
    entry: dict[str, Any] = payload
    if entry.get("schema") != STATE_SCHEMA or entry.get("kind") != STATE_KIND:
        raise DispatchError(
            f"Zustandsdatei {path} ist kein {STATE_KIND} in Schema {STATE_SCHEMA} "
            f"(gelesen: kind={entry.get('kind')!r}, schema={entry.get('schema')!r}). "
            "Fremde oder beschaedigte Datei – pruefen und bewusst entfernen."
        )
    version = _text(entry.get("version"), "version")
    if not _VERSION_RE.fullmatch(version):
        raise DispatchError(f"version {version!r} entspricht nicht dem Schema X.Y.Z")
    state = ReleaseState(
        repo=_text(entry.get("repo"), "repo"),
        version=version,
        candidate_sha=_sha(entry.get("candidate_sha"), "candidate_sha"),
        release_issue=str(entry.get("release_issue") or ""),
        candidate_run_id=_optional_run_id(entry.get("candidate_run_id"), "candidate_run_id"),
        acceptance_run_id=_optional_run_id(entry.get("acceptance_run_id"), "acceptance_run_id"),
        approval_artifact_name=str(entry.get("approval_artifact_name") or ""),
        predecessor_tag=str(entry.get("predecessor_tag") or ""),
        publish_run_id=_optional_run_id(entry.get("publish_run_id"), "publish_run_id"),
        update_acceptance_run_id=_optional_run_id(
            entry.get("update_acceptance_run_id"), "update_acceptance_run_id"
        ),
        pending=(
            PendingDispatch.from_json(entry["pending"])
            if entry.get("pending") is not None
            else None
        ),
        updated_at=str(entry.get("updated_at") or ""),
    )
    # Abgeleitete Felder sind auch gespeichert – wenn sie widersprechen, ist die
    # Datei von Hand bearbeitet worden und darf nicht weiterverwendet werden.
    for field, expected in (("release_tag", state.tag), ("release_ref", state.ref)):
        stored = entry.get(field)
        if stored is not None and stored != expected:
            raise DispatchError(
                f"Zustandsdatei {path}: {field}={stored!r} passt nicht zu version "
                f"{version!r} (erwartet {expected!r})."
            )
    return state


def save_state(path: Path, state: ReleaseState) -> None:
    """Schreibt den Zustand atomar (``mkstemp`` + ``os.replace``), Modus 0600.

    Atomar, weil genau die Datei den Wiederanlauf traegt: Ein halb
    geschriebener ``pending``-Eintrag waere schlimmer als keiner.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        replace(state, updated_at=_iso(_utc_now())).as_json(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        os.fchmod(fd, STATE_MODE)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
        os.replace(tmp_name, path)
    finally:
        Path(tmp_name).unlink(missing_ok=True)


def require_state(path: Path, *, repo: str) -> ReleaseState:
    """Laedt den Zustand fuer ein Folgekommando und prueft die Bindung."""
    state = load_state(path)
    if state is None:
        raise DispatchError(
            f"Keine Zustandsdatei unter {path}. Zuerst 'candidate' ausfuehren "
            "(Runbook-Schritt 3) oder --state-file auf die richtige Datei zeigen lassen."
        )
    if state.repo != repo:
        raise DispatchError(
            f"Zustandsdatei {path} gehoert zu {state.repo}, angefragt ist {repo}. "
            "Zustaende verschiedener Repositories werden nicht gemischt."
        )
    return state


# ── Korrelation ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RunRef:
    """Ein korrelierter Workflow-Lauf."""

    run_id: int
    url: str
    status: str
    conclusion: str
    title: str
    head_sha: str
    created_at: str


def list_runs(runner: Runner, *, repo: str, workflow: str, ref: str) -> list[Any]:
    """Die juengsten ``workflow_dispatch``-Laeufe eines Workflows auf einem Ref."""
    raw = runner([
        "run", "list", "--repo", repo, "--workflow", workflow,
        "--branch", ref, "--event", "workflow_dispatch",
        "--limit", str(RUN_LIST_LIMIT), "--json", RUN_FIELDS,
    ])
    payload = _json(raw, field=f"Laufliste {workflow}")
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise DispatchError(f"Laufliste {workflow} ist keine Liste, sondern {type(payload).__name__}")
    return payload


def known_run_ids(runner: Runner, *, repo: str, workflow: str, ref: str) -> tuple[int, ...]:
    """Run-IDs, die es **vor** dem Dispatch schon gab.

    Die tragende Abgrenzung der Korrelation: Alles hier Erfasste kann der
    gleich ausgeloeste Lauf nicht sein.
    """
    found: set[int] = set()
    for item in list_runs(runner, repo=repo, workflow=workflow, ref=ref):
        if isinstance(item, dict):
            raw_id = item.get("databaseId")
            if isinstance(raw_id, int) and raw_id > 0:
                found.add(raw_id)
    return tuple(sorted(found))


def select_new_runs(
    runs: Iterable[Any],
    *,
    known: Sequence[int],
    ref: str,
    expected_head_sha: str,
    not_before: datetime,
    marker: str = "",
) -> list[RunRef]:
    """Alle Laeufe, die als "der eben ausgeloeste" in Frage kommen.

    Fuenf unabhaengige Bedingungen, jede fuer sich notwendig: neue Run-ID,
    Ereignis ``workflow_dispatch`` (ein ``schedule``-Dry-Run ist nie ein
    Kandidat, #922), der Release-Ref, der Kandidaten-SHA und eine
    Erstellungszeit nach dem Dispatch. Ein Marker kommt hinzu, wo der Workflow
    einen fuehrt (``release-abnahme.yml``).

    Liefert bewusst eine **Liste**: Der Aufrufer unterscheidet zwischen
    "keiner" (weiter warten oder erneut dispatchen) und "mehrere" (benannt
    abbrechen). Ein "nimm den juengsten" waere hier die falsche Grosszuegigkeit
    – zwei passende Laeufe bedeuten, dass jemand parallel dispatcht hat.
    """
    known_ids = set(known)
    pattern = rud.marker_pattern(marker) if marker else None
    matches: list[RunRef] = []
    for item in runs:
        if not isinstance(item, dict):
            continue
        entry: dict[str, Any] = item
        raw_id = entry.get("databaseId")
        if not isinstance(raw_id, int) or raw_id <= 0 or raw_id in known_ids:
            continue
        if entry.get("event") != "workflow_dispatch":
            continue
        if str(entry.get("headBranch") or "") != ref:
            continue
        if str(entry.get("headSha") or "") != expected_head_sha:
            continue
        created = parse_github_timestamp(entry.get("createdAt"), field=f"Lauf {raw_id}.createdAt")
        if created < not_before:
            continue
        title = str(entry.get("displayTitle") or "")
        if pattern is not None and pattern.search(title) is None:
            continue
        matches.append(
            RunRef(
                run_id=raw_id,
                url=str(entry.get("url") or ""),
                status=str(entry.get("status") or ""),
                conclusion=str(entry.get("conclusion") or ""),
                title=title,
                head_sha=str(entry.get("headSha") or ""),
                created_at=str(entry.get("createdAt") or ""),
            )
        )
    return matches


def await_new_run(
    runner: Runner,
    *,
    repo: str,
    pending: PendingDispatch,
    attempts: int = POLL_ATTEMPTS,
    interval_s: float = POLL_INTERVAL_S,
    sleep: Callable[[float], None] = time.sleep,
) -> RunRef | None:
    """Wartet auf **genau einen** neuen passenden Lauf.

    ``None`` heisst "nach dem vollen Budget keiner" – fuer den Aufrufer die
    Erlaubnis, (erneut) zu dispatchen. Mehrere Treffer werfen sofort: Dann ist
    die Lage mehrdeutig, und Raten waere hier der teuerste Fehler.
    """
    not_before = parse_github_timestamp(pending.not_before, field="pending.not_before")
    for attempt in range(attempts):
        matches = select_new_runs(
            list_runs(runner, repo=repo, workflow=pending.workflow, ref=pending.ref),
            known=pending.known_run_ids,
            ref=pending.ref,
            expected_head_sha=pending.expected_head_sha,
            not_before=not_before,
            marker=pending.marker,
        )
        if len(matches) > 1:
            raise DispatchError(
                f"Mehrdeutig: {len(matches)} neue {pending.workflow}-Laeufe auf "
                f"{pending.ref} passen auf den Dispatch "
                f"({', '.join(str(m.run_id) for m in matches)}). Es darf genau einer sein – "
                "Actions-Uebersicht pruefen, ueberzaehlige Laeufe abbrechen und erst dann "
                "erneut aufrufen."
            )
        if matches:
            return matches[0]
        if attempt < attempts - 1:
            sleep(interval_s)
    return None


def _record_pending(
    runner: Runner,
    state_path: Path,
    state: ReleaseState,
    *,
    operation: str,
    workflow: str,
    marker: str = "",
) -> tuple[ReleaseState, PendingDispatch]:
    """Erfasst bekannte Laeufe und schreibt den ``pending``-Eintrag – **vor** dem Dispatch."""
    known = known_run_ids(runner, repo=state.repo, workflow=workflow, ref=state.ref)
    # Auf volle Sekunden abrunden: GitHub fuehrt ``createdAt`` sekundengenau,
    # ein Bruchteil hier liesse den Lauf derselben Sekunde durchfallen.
    not_before = _utc_now().replace(microsecond=0) - timedelta(seconds=CLOCK_SKEW_TOLERANCE_S)
    pending = PendingDispatch(
        operation=operation,
        workflow=workflow,
        ref=state.ref,
        expected_head_sha=state.candidate_sha,
        marker=marker,
        not_before=_iso(not_before),
        known_run_ids=known,
        recorded_at=_iso(_utc_now()),
    )
    state = replace(state, pending=pending)
    save_state(state_path, state)
    return state, pending


def run_url(repo: str, run_id: int) -> str:
    return f"https://github.com/{repo}/actions/runs/{run_id}"


def reconcile_or_dispatch(
    runner: Runner,
    state_path: Path,
    state: ReleaseState,
    *,
    operation: str,
    workflow: str,
    dispatch_args: Sequence[str],
    existing_run_id: int | None = None,
    marker: str = "",
    sleep: Callable[[float], None] = time.sleep,
    echo: Callable[[str], None] = print,
) -> tuple[ReleaseState, RunRef]:
    """Der wiederanlauf-sichere Dispatch.

    Reihenfolge, und nur diese: bereits korrelierte Run-ID wieder aufgreifen →
    sonst vorhandenen ``pending``-Eintrag versoehnen → sonst ``pending``
    schreiben → dispatchen → korrelieren → ``pending`` loeschen und Run-ID
    festhalten.

    Der erste Zweig ist nicht Bequemlichkeit, sondern eine Sperre: Bricht
    ``gh run watch`` ab (Netz, geschlossenes Terminal, roter Lauf), steht die
    Run-ID laengst im Zustand und der ``pending``-Eintrag ist weg. Ohne diesen
    Zweig loeste derselbe Befehl einen **zweiten** Kandidatenbau aus – genau
    die Verwechslung, die die Wiederanlaufmatrix ausschliesst ("alte und neue
    Run-ID mischen"). Ein bewusst neuer Lauf auf demselben SHA bleibt moeglich,
    aber nur ueber die Handprozedur oder eine eigene Zustandsdatei; er ist eine
    Entscheidung, kein Nebeneffekt eines Wiederholungsaufrufs.
    """
    pending = state.pending
    if pending is not None and pending.operation != operation:
        raise DispatchError(
            f"Offener Dispatch der Operation {pending.operation!r} (Workflow "
            f"{pending.workflow}, notiert {pending.recorded_at}). Erst diesen "
            f"abschliessen – '{pending.operation}' erneut aufrufen –, bevor "
            f"'{operation}' laeuft."
        )
    if existing_run_id is not None:
        echo(
            f"Lauf {existing_run_id} steht bereits im Zustand – er wird erneut "
            "beobachtet statt ein zweiter ausgeloest."
        )
        return replace(state, pending=None), RunRef(
            run_id=existing_run_id,
            url=run_url(state.repo, existing_run_id),
            status="",
            conclusion="",
            title="",
            head_sha=state.candidate_sha,
            created_at="",
        )
    if pending is not None:
        if pending.ref != state.ref or pending.expected_head_sha != state.candidate_sha:
            raise DispatchError(
                f"Offener Dispatch bindet {pending.ref}@{pending.expected_head_sha[:12]}, "
                f"der Zustand aber {state.ref}@{state.candidate_sha[:12]}. Vermischter "
                "Release-Zustand – Zustandsdatei pruefen, nichts dispatchen."
            )
        echo(
            f"Offener {operation}-Dispatch vom {pending.recorded_at} gefunden – "
            "zuerst suchen statt erneut ausloesen."
        )
        found = await_new_run(runner, repo=state.repo, pending=pending, sleep=sleep)
        if found is not None:
            echo(f"Uebernommen: Lauf {found.run_id} ({found.url}) – kein zweiter Dispatch.")
            return replace(state, pending=None), found
        echo("Kein passender Lauf – der Dispatch hat GitHub nicht erreicht, er wird wiederholt.")

    state, pending = _record_pending(
        runner, state_path, state, operation=operation, workflow=workflow, marker=marker
    )
    runner(dispatch_args)
    found = await_new_run(runner, repo=state.repo, pending=pending, sleep=sleep)
    if found is None:
        raise DispatchError(
            f"Der ausgeloeste {workflow}-Lauf war nach {POLL_ATTEMPTS} Versuchen nicht "
            f"auffindbar. Der Dispatch kann trotzdem gelaufen sein: Der offene Eintrag "
            f"bleibt in {state_path} stehen, ein erneuter Aufruf sucht zuerst weiter und "
            "dispatcht nur, wenn wirklich kein Lauf existiert. Vorher die "
            "Actions-Uebersicht ansehen."
        )
    echo(f"Korreliert: Lauf {found.run_id} ({found.url})")
    return replace(state, pending=None), found


def watch(
    watcher: Watcher, run: RunRef, *, echo: Callable[[str], None] = print, hint: str = ""
) -> None:
    """Wartet auf das Ende des Laufs; ein roter Lauf bricht benannt ab."""
    code = watcher(run.run_id)
    if code != 0:
        raise DispatchError(
            f"Lauf {run.run_id} ist nicht erfolgreich beendet (gh run watch Exit {code}): "
            f"{run.url}. Runbook 'Wiederanlaufmatrix' anwenden – nicht blind wiederholen."
            + (f" {hint}" if hint else "")
        )
    echo(f"Lauf {run.run_id} erfolgreich: {run.url}")


# ── Vertragspruefungen ueber gh ────────────────────────────────────────


def verify_ref_protection(runner: Runner, *, repo: str, ref: str) -> tuple[str, ...]:
    """Runbook-Schritt 3: greift das Ruleset fuer ``release/*`` auf diesem Ref?"""
    payload = _json(
        runner(["api", f"repos/{repo}/rules/branches/{ref}"]), field=f"Regeln fuer {ref}"
    )
    try:
        return rc.validate_ref_protection(payload, expected_ref=ref)
    except rc.ContractError as exc:
        raise DispatchError(f"Ref-Schutz von {ref} nicht ausreichend: {exc}") from exc


def verify_release_ref(runner: Runner, *, repo: str, ref: str, expected_sha: str) -> str:
    """Zeigt der Release-Ref exakt auf den Kandidaten-SHA aus Schritt 2?"""
    payload = _json(
        runner(["api", f"repos/{repo}/git/ref/heads/{ref}"]), field=f"Ref-Antwort {ref}"
    )
    if not isinstance(payload, dict):
        raise DispatchError(f"Ref-Antwort fuer {ref} ist kein Objekt")
    try:
        return rc.validate_release_ref(payload, expected_ref=ref, expected_sha=expected_sha)
    except rc.ContractError as exc:
        raise DispatchError(f"Release-Ref {ref} nicht verwendbar: {exc}") from exc


def validate_run(
    runner: Runner, *, repo: str, run_id: int, workflow: str, expected_head_sha: str
) -> dict[str, Any]:
    """Bindet einen Lauf ueber den Freigabevertrag, nicht ueber eigene Regeln.

    ``rc.validate_workflow_run`` verlangt fail-closed ``workflow_dispatch``,
    erfolgreichen Abschluss, den richtigen Workflow-Pfad und den erwarteten
    Head-SHA – dieselbe Pruefung, die ``release-abnahme.yml`` im Job
    ``candidate-source`` fuehrt. Ein ``schedule``-Dry-Run (#922) faellt hier
    ein zweites Mal durch, auch wenn er die Korrelation je erreichen sollte.
    """
    payload = _json(
        runner(["api", f"repos/{repo}/actions/runs/{run_id}"]), field=f"Run-Metadaten {run_id}"
    )
    if not isinstance(payload, dict):
        raise DispatchError(f"Run-Metadaten {run_id} sind kein Objekt")
    try:
        return rc.validate_workflow_run(
            payload,
            expected_run_id=run_id,
            expected_workflow=_WORKFLOW_PATHS[workflow],
            expected_head_sha=expected_head_sha,
        )
    except rc.ContractError as exc:
        raise DispatchError(f"Lauf {run_id} ist kein gueltiger {workflow}-Lauf: {exc}") from exc


def resolve_approval_artifact(
    runner: Runner, *, repo: str, run_id: int, run_attempt: int
) -> str:
    """Der exakte Manifestname des Laufs – an seinen ``run_attempt`` gebunden.

    ``release-abnahme.yml`` legt das Manifest als
    ``release-approval-manifest-<run_attempt>`` ab. Ein Wiederanlauf desselben
    Laufs erzeugt daher ein zweites Artefakt; nur das des aktuellen Versuchs
    gehoert zur soeben beobachteten Abnahme. Abgelaufene Artefakte scheiden
    aus – ihr Name existiert noch, ihr Inhalt nicht mehr.
    """
    payload = _json(
        runner(["api", f"repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100"]),
        field=f"Artefaktliste {run_id}",
    )
    if not isinstance(payload, dict):
        raise DispatchError(f"Artefaktliste {run_id} ist kein Objekt")
    listing = payload.get("artifacts")
    if not isinstance(listing, list):
        raise DispatchError(f"Artefaktliste {run_id} ohne 'artifacts'-Feld")
    expected = f"release-approval-manifest-{run_attempt}"
    found: list[str] = []
    other_attempts: list[str] = []
    for item in listing:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        if not _MANIFEST_ARTIFACT_RE.fullmatch(name):
            continue
        if bool(item.get("expired")):
            continue
        (found if name == expected else other_attempts).append(name)
    if len(found) == 1:
        return found[0]
    hint = (
        f" Nicht abgelaufene Manifeste anderer Versuche: {', '.join(sorted(other_attempts))}."
        if other_attempts
        else ""
    )
    raise DispatchError(
        f"Erwartet ist genau ein nicht abgelaufenes Artefakt {expected!r} in Lauf {run_id} "
        f"(run_attempt {run_attempt}); gefunden: {len(found)}.{hint} Ohne eindeutiges "
        "Manifest wird nichts abgenommen – Artefaktliste des Laufs pruefen."
    )


# ── Kandidatenrevision: Vertrag und Checkliste ─────────────────────────

#: Beide Dateien werden aus der Kandidatenrevision geholt, nicht aus dem
#: Arbeitsbaum: Die Instanz pinnt den Dateihash der Checkliste, und ein
#: inzwischen weiterentwickelter Vertrag pruefte einen anderen Stand, als
#: abgenommen wurde.
CANDIDATE_SOURCES: Final = (
    ("scripts/release_contract.py", "release_contract.py"),
    (rc.CHECKLIST_PATH, "RELEASE_ACCEPTANCE_CHECKLIST.md"),
)


def materialize_candidate_sources(
    command: Command, *, repo_dir: Path, candidate_sha: str, target: Path
) -> tuple[Path, Path]:
    """Legt Vertrag und Checkliste der Kandidatenrevision in *target* ab.

    ``git show`` statt eines zweiten Checkouts: Der Owner arbeitet oft auf
    ``main``, waehrend der Kandidat auf dem Release-Ref liegt. Fehlt der Commit
    lokal, ist das ein benannter Abbruch mit dem Fetch-Hinweis – nicht ein
    stiller Rueckfall auf den Arbeitsbaum.
    """
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for source, name in CANDIDATE_SOURCES:
        try:
            blob = command(["git", "-C", str(repo_dir), "show", f"{candidate_sha}:{source}"])
        except DispatchError as exc:
            raise DispatchError(
                f"{source} ist in der Kandidatenrevision {candidate_sha[:12]} nicht lesbar "
                f"({exc}). Revision holen: git fetch origin '+refs/heads/*:refs/remotes/origin/*'"
            ) from exc
        path = target / name
        # ``write_bytes``: Die Datei muss byteidentisch zur Kandidatenrevision
        # sein, sonst schlaegt der Checklisten-Hash der Instanz fehl.
        path.write_bytes(blob)
        written.append(path)
    return written[0], written[1]


def find_payload(root: Path, name: str) -> Path:
    """Findet eine heruntergeladene Datei in beiden ``gh run download``-Layouts.

    ``gh`` legt je nach Trefferzahl flach oder in einem Unterverzeichnis je
    Artefaktnamen ab – dieselbe Doppeldeutigkeit, die
    ``release_contract.select_instance_payload`` beim Manifest abfaengt.
    """
    matches = sorted(p for p in root.rglob(name) if p.is_file())
    if len(matches) != 1:
        raise DispatchError(
            f"Erwartet ist genau eine {name} unter {root}, gefunden: {len(matches)}. "
            "Download-Verzeichnis pruefen (leeren und erneut laden)."
        )
    return matches[0]


def _instance_summary(instance_path: Path) -> str:
    """Kriterienmatrix der Instanz als Text – die Entscheidungsgrundlage."""
    payload = _json(instance_path.read_text(encoding="utf-8"), field=str(instance_path))
    if not isinstance(payload, dict):
        raise DispatchError(f"{instance_path} enthaelt kein Objekt")
    criteria = payload.get("criteria")
    if not isinstance(criteria, list):
        return "(keine Kriterienliste in der Instanz)"
    lines = []
    for item in criteria:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  {str(item.get('id') or '?'):<24} "
            f"{str(item.get('phase') or '?'):<12} "
            f"{str(item.get('requirement') or '?'):<12} "
            f"{str(item.get('status') or '?')}"
        )
    return "\n".join(lines) or "(leere Kriterienliste)"


# ── Unterkommandos ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class Context:
    """Alle Aussenkanten an einer Stelle – in Tests vollstaendig ersetzbar."""

    runner: Runner
    command: Command
    watcher: Watcher
    state_path: Path
    repo_dir: Path
    echo: Callable[[str], None] = print
    sleep: Callable[[float], None] = time.sleep
    confirm: Callable[[str], str] = input


def acceptance_marker(*, tag: str, candidate_run_id: int) -> str:
    """Korrelationsmarker des Abnahme-Dispatches.

    Eigener Namensraum neben ``update-check:`` (#919), damit der Post-Release-
    Nachweislauf und der Abnahmelauf desselben Releases nie denselben Marker
    tragen. Deterministisch aus Tag und Kandidaten-Run-ID: Derselbe Release
    ergibt denselben Marker, ein Wiederanlauf findet also seinen eigenen Lauf.
    """
    if not _TAG_RE.fullmatch(tag):
        raise DispatchError(f"Tag {tag!r} entspricht nicht dem Schema vX.Y.Z")
    return f"release-dispatch:acceptance:{tag}:{candidate_run_id}"


def cmd_candidate(
    ctx: Context, *, repo: str, version: str, candidate_sha: str, target_issue: str
) -> ReleaseState:
    """Runbook-Schritt 3: Kandidaten bauen."""
    if not _VERSION_RE.fullmatch(version):
        raise DispatchError(f"--version {version!r} entspricht nicht dem Schema X.Y.Z")
    candidate_sha = _sha(candidate_sha, "--candidate-sha")
    if not _ISSUE_RE.fullmatch(target_issue):
        raise DispatchError(f"--target-issue {target_issue!r} ist keine Issue-Nummer")

    existing = load_state(ctx.state_path)
    if existing is not None and (
        existing.repo != repo
        or existing.version != version
        or existing.candidate_sha != candidate_sha
    ):
        raise DispatchError(
            f"In {ctx.state_path} steht bereits ein Release "
            f"({existing.repo} {existing.tag} @ {existing.candidate_sha[:12]}), angefragt ist "
            f"({repo} v{version} @ {candidate_sha[:12]}). Zustaende verschiedener Releases "
            "werden nicht gemischt: den alten Release abschliessen, die Datei bewusst "
            "entfernen oder --state-file auf eine eigene Datei zeigen lassen."
        )
    state = existing or ReleaseState(
        repo=repo, version=version, candidate_sha=candidate_sha, release_issue=target_issue
    )
    state = replace(state, release_issue=target_issue)

    ctx.echo(f"Release {state.tag} · Ref {state.ref} · Kandidat {candidate_sha}")
    rules = verify_ref_protection(ctx.runner, repo=repo, ref=state.ref)
    ctx.echo(f"Ref-Schutz aktiv: {', '.join(rules)}")
    verify_release_ref(ctx.runner, repo=repo, ref=state.ref, expected_sha=candidate_sha)
    ctx.echo("Release-Ref zeigt auf den Kandidaten-SHA aus Schritt 2.")

    state, run = reconcile_or_dispatch(
        ctx.runner,
        ctx.state_path,
        state,
        operation=OP_CANDIDATE,
        workflow=BUILD_WORKFLOW,
        dispatch_args=[
            "workflow", "run", BUILD_WORKFLOW, "--repo", repo, "--ref", state.ref,
            "-f", "with_ai=true",
        ],
        existing_run_id=state.candidate_run_id,
        sleep=ctx.sleep,
        echo=ctx.echo,
    )
    state = replace(state, candidate_run_id=run.run_id)
    save_state(ctx.state_path, state)

    watch(
        ctx.watcher,
        run,
        echo=ctx.echo,
        hint=(
            f"Die Run-ID steht bereits in {ctx.state_path}; ein weiterer 'candidate'-Aufruf "
            "beobachtet genau diesen Lauf erneut, statt einen zweiten zu starten. Soll ein "
            "neuer Bau auf demselben SHA laufen (Wiederanlaufmatrix), gehoert er in einen "
            "eigenen Zustand: --state-file setzen oder die Datei bewusst entfernen."
        ),
    )
    validate_run(
        ctx.runner,
        repo=repo,
        run_id=run.run_id,
        workflow=BUILD_WORKFLOW,
        expected_head_sha=candidate_sha,
    )
    ctx.echo(
        f"CANDIDATE_RUN_ID={run.run_id} · in {ctx.state_path} festgehalten. "
        "Weiter mit Runbook-Schritt 4 (Sicherheitsbefunde), danach 'acceptance'."
    )
    return state


def cmd_acceptance(ctx: Context, *, repo: str) -> ReleaseState:
    """Runbook-Schritt 5: Hardware-Abnahme."""
    state = require_state(ctx.state_path, repo=repo)
    if state.candidate_run_id is None:
        raise DispatchError(
            "Keine Kandidaten-Run-ID im Zustand. Zuerst 'candidate' (Runbook-Schritt 3)."
        )
    if not _ISSUE_RE.fullmatch(state.release_issue):
        raise DispatchError(
            f"release_issue {state.release_issue!r} im Zustand ist keine Issue-Nummer. "
            "'candidate' mit --target-issue erneut aufrufen."
        )

    verify_release_ref(ctx.runner, repo=repo, ref=state.ref, expected_sha=state.candidate_sha)
    # Die gespeicherte Kandidaten-Run-ID **vor** dem Hardware-Lauf gegen den
    # Freigabevertrag halten, nicht erst danach. Der Fall dahinter ist real: Ein
    # roter Kandidatenbau hinterlaesst seine Run-ID im Zustand (sie wird vor dem
    # Beobachten geschrieben, damit ein Abbruch keinen zweiten Lauf erzeugt).
    # Dispatcht der Owner danach laut Wiederanlaufmatrix von Hand neu, kennt der
    # Zustand die neue ID nicht – ``acceptance`` schickte die alte, gescheiterte
    # in die Abnahme. ``candidate-source`` weist sie dort zwar ab (derselbe
    # ``validate_workflow_run``-Vertrag), aber erst nach einem vollstaendigen
    # Anlauf auf Self-hosted-Hardware und mit einem Befund, der nicht nach
    # "falsche Run-ID" aussieht.
    validate_run(
        ctx.runner,
        repo=repo,
        run_id=state.candidate_run_id,
        workflow=BUILD_WORKFLOW,
        expected_head_sha=state.candidate_sha,
    )
    marker = acceptance_marker(tag=state.tag, candidate_run_id=state.candidate_run_id)
    state, run = reconcile_or_dispatch(
        ctx.runner,
        ctx.state_path,
        state,
        operation=OP_ACCEPTANCE,
        workflow=ACCEPTANCE_WORKFLOW,
        dispatch_args=[
            "workflow", "run", ACCEPTANCE_WORKFLOW, "--repo", repo, "--ref", state.ref,
            "-f", f"run_id={state.candidate_run_id}",
            "-f", "platforms=alle",
            "-f", "dry_run=false",
            "-f", f"target_issue={state.release_issue}",
            "-f", f"dispatch_marker={marker}",
        ],
        existing_run_id=state.acceptance_run_id,
        marker=marker,
        sleep=ctx.sleep,
        echo=ctx.echo,
    )
    state = replace(state, acceptance_run_id=run.run_id)
    save_state(ctx.state_path, state)

    watch(ctx.watcher, run, echo=ctx.echo)
    metadata = validate_run(
        ctx.runner,
        repo=repo,
        run_id=run.run_id,
        workflow=ACCEPTANCE_WORKFLOW,
        expected_head_sha=state.candidate_sha,
    )
    attempt = int(metadata["run_attempt"])
    artifact = resolve_approval_artifact(
        ctx.runner, repo=repo, run_id=run.run_id, run_attempt=attempt
    )
    state = replace(state, approval_artifact_name=artifact)
    save_state(ctx.state_path, state)
    ctx.echo(
        f"ACCEPTANCE_RUN_ID={run.run_id} (run_attempt {attempt}) · "
        f"APPROVAL_ARTIFACT_NAME={artifact}. Weiter mit 'approve'."
    )
    return state


def cmd_approve(ctx: Context, *, repo: str, work_dir: Path | None = None) -> ReleaseState:
    """Runbook-Schritt 6: Freigabemanifest und Instanz **anzeigen**, nicht freigeben."""
    state = require_state(ctx.state_path, repo=repo)
    if state.acceptance_run_id is None or not state.approval_artifact_name:
        raise DispatchError(
            "Kein Abnahmelauf mit Manifestnamen im Zustand. Zuerst 'acceptance' "
            "(Runbook-Schritt 5)."
        )
    with _Workspace(work_dir) as workspace:
        contract, checklist = materialize_candidate_sources(
            ctx.command,
            repo_dir=ctx.repo_dir,
            candidate_sha=state.candidate_sha,
            target=workspace / "candidate",
        )
        download = workspace / "approval"
        download.mkdir(parents=True, exist_ok=True)
        ctx.runner([
            "run", "download", str(state.acceptance_run_id), "--repo", repo,
            "-n", state.approval_artifact_name, "-D", str(download),
        ])
        manifest = find_payload(download, "release-approval-manifest.json")
        instance = workspace / "release-acceptance-instance.json"
        ctx.command([
            sys.executable, str(contract), "extract-instance",
            "--manifest", str(manifest), "--output", str(instance),
        ])
        ctx.command([
            sys.executable, str(contract), "validate-instance",
            "--checklist", str(checklist), "--instance", str(instance),
            "--through-phase", "pre-release",
        ])
        ctx.echo(
            f"Instanz aus {state.approval_artifact_name} gegen Vertrag und Checkliste der "
            f"Kandidatenrevision {state.candidate_sha[:12]} bis 'pre-release' validiert:"
        )
        ctx.echo(_instance_summary(instance))
    ctx.echo(
        "Go-/No-Go bleibt eine menschliche Entscheidung. Bei Go weiter mit "
        "'publish --predecessor vA.B.C'."
    )
    return state


def cmd_publish(
    ctx: Context, *, repo: str, predecessor_tag: str, assume_yes: bool = False
) -> ReleaseState:
    """Runbook-Schritt 8: die abgenommenen Bytes veroeffentlichen."""
    state = require_state(ctx.state_path, repo=repo)
    missing = [
        name
        for name, value in (
            ("candidate_run_id", state.candidate_run_id),
            ("acceptance_run_id", state.acceptance_run_id),
            ("approval_artifact_name", state.approval_artifact_name),
        )
        if not value
    ]
    if missing:
        raise DispatchError(
            f"Unvollstaendiger Zustand fuer 'publish': {', '.join(missing)} fehlt. "
            "Schritte 3 und 5 ueber dieses Skript fahren oder die Werte von Hand "
            "nach Runbook-Schritt 8 einsetzen."
        )
    # Leer ist ein **gueltiger, ausdruecklicher** Wert: ``release-publish.yml``
    # fuehrt ``predecessor_tag`` als optional ("Leer = kein Dispatch;
    # UPDATE-LINUX-ARM-01/UPDATE-MACOS-ARM-01 bleiben PENDING"), und genau dieser
    # Zustand tritt auf, wenn der Vorgaenger den In-Prozess-Hook noch nicht
    # traegt (macOS < 2.7.3) oder keiner existiert. Das Argument bleibt
    # trotzdem **pflichtig**: Vergessen und bewusst Ueberspringen duerfen nicht
    # dasselbe Kommando sein – wer den Nachweis auslaesst, tippt ``--predecessor ''``.
    if predecessor_tag and not _TAG_RE.fullmatch(predecessor_tag):
        raise DispatchError(
            f"--predecessor {predecessor_tag!r} entspricht nicht dem Schema vX.Y.Z. Der "
            "Vorgaenger wird nie geraten – fuer einen bewussten Verzicht --predecessor '' "
            "angeben; beide Update-Kriterien bleiben dann PENDING."
        )
    if predecessor_tag == state.tag:
        raise DispatchError(
            f"--predecessor {predecessor_tag} ist der Release selbst. Der Nachweis "
            "vergleicht zwei Versionen und braucht den echten Vorgaenger."
        )

    verify_release_ref(ctx.runner, repo=repo, ref=state.ref, expected_sha=state.candidate_sha)
    predecessor_note = predecessor_tag or (
        "keiner – Update-Nachweis wird uebersprungen, beide Kriterien bleiben PENDING"
    )
    ctx.echo(
        "Veroeffentlicht wird:\n"
        f"  Repository            {repo}\n"
        f"  Tag                   {state.tag} (wird im Lauf angelegt, create_tag=true)\n"
        f"  Release-Ref           {state.ref}\n"
        f"  Kandidaten-Commit     {state.candidate_sha}\n"
        f"  Kandidaten-Lauf       {state.candidate_run_id}\n"
        f"  Abnahme-Lauf          {state.acceptance_run_id}\n"
        f"  Freigabemanifest      {state.approval_artifact_name}\n"
        f"  Vorgaenger            {predecessor_note}\n"
        f"  Release-Issue         {state.release_issue}"
    )
    if not assume_yes:
        answer = ctx.confirm(f"Zum Veroeffentlichen den Tag eingeben ({state.tag}): ").strip()
        if answer != state.tag:
            raise DispatchError(
                f"Abgebrochen: {answer!r} ist nicht {state.tag}. Es wurde nichts dispatcht."
            )

    state = replace(state, predecessor_tag=predecessor_tag)
    save_state(ctx.state_path, state)
    state, run = reconcile_or_dispatch(
        ctx.runner,
        ctx.state_path,
        state,
        operation=OP_PUBLISH,
        workflow=PUBLISH_WORKFLOW,
        dispatch_args=[
            "workflow", "run", PUBLISH_WORKFLOW, "--repo", repo, "--ref", state.ref,
            "-f", f"tag={state.tag}",
            "-f", f"candidate_run_id={state.candidate_run_id}",
            "-f", f"acceptance_run_id={state.acceptance_run_id}",
            "-f", f"approval_artifact_name={state.approval_artifact_name}",
            "-f", "create_tag=true",
            "-f", f"predecessor_tag={predecessor_tag}",
            "-f", f"target_issue={state.release_issue}",
        ],
        existing_run_id=state.publish_run_id,
        sleep=ctx.sleep,
        echo=ctx.echo,
    )
    state = replace(state, publish_run_id=run.run_id)
    save_state(ctx.state_path, state)
    watch(ctx.watcher, run, echo=ctx.echo)
    ctx.echo(f"PUBLISH_RUN_ID={run.run_id}. Weiter mit 'finalize' (Runbook-Schritt 9).")
    return state


def cmd_finalize(ctx: Context, *, repo: str, work_dir: Path | None = None) -> ReleaseState:
    """Runbook-Schritt 9: den Post-Release-Update-Nachweis abschliessen."""
    state = require_state(ctx.state_path, repo=repo)
    if state.publish_run_id is None or state.candidate_run_id is None:
        raise DispatchError(
            "Kein Publish-Lauf im Zustand. Zuerst 'publish' (Runbook-Schritt 8)."
        )
    if not state.predecessor_tag:
        # Kein Fehler, sondern der dokumentierte Zustand: ohne Vorgaenger gibt
        # es keinen Nachweis. Ihn hier zu erfinden waere genau der Fehler, den
        # das Runbook fuer die beiden Update-Kriterien ausschliesst.
        ctx.echo(
            "Kein predecessor_tag im Zustand: Der Publish-Lauf hat den Update-Nachweis "
            "sichtbar uebersprungen. UPDATE-LINUX-ARM-01 und UPDATE-MACOS-ARM-01 bleiben "
            "PENDING und werden ueber den Rueckfallweg in Runbook-Schritt 9 nachgezogen – "
            "sie werden nicht auf PASS gesetzt."
        )
        return state

    marker = rud.dispatch_marker(
        tag=state.tag, candidate_run_id=str(state.candidate_run_id)
    )
    try:
        found = rud.find_existing_run(ctx.runner, repo=repo, marker=marker)
    except (rud.DispatchError, json.JSONDecodeError) as exc:
        # ``release_update_dispatch`` fuehrt eine **eigene** DispatchError-Klasse
        # und liest die Laufliste ungeschuetzt mit ``json.loads``. Beides
        # entkaeme dem ``except DispatchError`` in ``main`` und endete als
        # Traceback – ausgerechnet in Schritt 9, wo dieses Modul benannte
        # Abbrueche mit naechstem Schritt zusichert.
        raise DispatchError(
            f"Suche nach dem Update-Abnahmelauf (Marker {marker}) scheiterte: {exc}. "
            "Laufliste in der Actions-Uebersicht pruefen; sonst gilt der Rueckfallweg "
            "aus Runbook-Schritt 9."
        ) from exc
    if found is None:
        raise DispatchError(
            f"Kein Abnahme-Lauf mit Marker {marker} gefunden. Der Publish-Lauf sollte ihn "
            "ausgeloest haben (#919): Job 'Post-Release' im Lauf "
            f"{state.publish_run_id} pruefen. Fehlt er wirklich, gilt der Rueckfallweg aus "
            "Runbook-Schritt 9 – von Hand, mit derselben Kandidaten-Run-ID."
        )
    ctx.echo(f"Update-Abnahmelauf {found.run_id} ({found.url}) ueber den Marker gefunden.")
    watch(
        ctx.watcher,
        RunRef(
            run_id=found.run_id,
            url=found.url,
            status=found.status,
            conclusion=found.conclusion,
            title=found.title,
            head_sha=state.candidate_sha,
            created_at="",
        ),
        echo=ctx.echo,
    )
    state = replace(state, update_acceptance_run_id=found.run_id)
    save_state(ctx.state_path, state)

    with _Workspace(work_dir) as workspace:
        contract, checklist = materialize_candidate_sources(
            ctx.command,
            repo_dir=ctx.repo_dir,
            candidate_sha=state.candidate_sha,
            target=workspace / "candidate",
        )
        download = workspace / "instance"
        download.mkdir(parents=True, exist_ok=True)
        ctx.runner([
            "run", "download", str(found.run_id), "--repo", repo,
            "--pattern", FINAL_INSTANCE_PATTERN, "-D", str(download),
        ])
        instance = find_payload(download, rc.INSTANCE_PAYLOAD_NAME)
        ctx.command([
            sys.executable, str(contract), "validate-instance",
            "--checklist", str(checklist), "--instance", str(instance),
            "--through-phase", "post-release",
        ])
        ctx.echo("Finale Release-Instanz bis 'post-release' validiert:")
        ctx.echo(_instance_summary(instance))
    ctx.echo(
        "ROLLBACK-01 (SHOULD, Go-/No-Go-Protokollierung) bleibt in der Hand des "
        "Release-Owners. Danach kann das Release-Issue geschlossen werden."
    )
    return state


class _Workspace:
    """Arbeitsverzeichnis: uebergeben (bleibt stehen) oder temporaer (wird geraeumt)."""

    def __init__(self, given: Path | None) -> None:
        self._given = given
        self._tmp: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> Path:
        if self._given is not None:
            self._given.mkdir(parents=True, exist_ok=True)
            return self._given
        self._tmp = tempfile.TemporaryDirectory(prefix="release-dispatch-")
        return Path(self._tmp.name)

    def __exit__(self, *exc: object) -> None:
        if self._tmp is not None:
            self._tmp.cleanup()


# ── CLI ────────────────────────────────────────────────────────────────


#: Kurzhilfe. Anders als bei den CI-internen Skripten liest ein Mensch dieses
#: ``--help`` unter Zeitdruck; das vollstaendige Modul-Docstring waere dort
#: Rauschen. Die Zuordnung Schritt -> Unterkommando ist die eine Information,
#: die er dabei sucht.
_CLI_DESCRIPTION: Final = (
    "Standardweg fuer die Release-Dispatches (#1039): leitet Run-IDs und "
    "Artefaktnamen aus der GitHub-API ab, statt sie zwischen den Runbook-"
    "Schritten von Hand zu kopieren. Aendert keine Workflows und keine "
    "Vertraege; die Handprozedur in docs/RELEASE_PROCESS.md bleibt gueltig "
    "und gilt bei Widerspruch."
)
_CLI_EPILOG: Final = """Runbook-Schritte:
  3  candidate --version X.Y.Z --candidate-sha <SHA> --target-issue N
  5  acceptance
  6  approve
  8  publish --predecessor vA.B.C   (--predecessor '' laesst den Nachweis aus)
  9  finalize
"""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=_CLI_DESCRIPTION,
        epilog=_CLI_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repo", default=DEFAULT_REPO, help=f"owner/repo (Standard: {DEFAULT_REPO})")
    parser.add_argument(
        "--state-file",
        type=Path,
        default=None,
        help=(
            "Zustandsdatei. Standard: Benutzer-State-Verzeichnis "
            f"({default_state_path()}), bewusst ausserhalb des Arbeitsbaums."
        ),
    )
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=Path.cwd(),
        help="Lokaler Checkout, aus dem die Kandidatenrevision gelesen wird.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    candidate = commands.add_parser(OP_CANDIDATE, help="Runbook-Schritt 3: Kandidaten bauen")
    candidate.add_argument("--version", required=True, help="Zielversion X.Y.Z (ohne 'v').")
    candidate.add_argument(
        "--candidate-sha",
        required=True,
        help="Vollstaendiger Kandidaten-SHA aus Runbook-Schritt 2 (im Release-Issue).",
    )
    candidate.add_argument("--target-issue", required=True, help="Nummer des Release-Issues.")

    commands.add_parser(OP_ACCEPTANCE, help="Runbook-Schritt 5: Hardware-Abnahme")

    approve = commands.add_parser("approve", help="Runbook-Schritt 6: Manifest und Instanz pruefen")
    approve.add_argument("--work-dir", type=Path, default=None)

    publish = commands.add_parser(OP_PUBLISH, help="Runbook-Schritt 8: veroeffentlichen")
    publish.add_argument(
        "--predecessor",
        required=True,
        help=(
            "Vorgaenger-Tag vA.B.C fuer den Post-Release-Update-Nachweis. "
            "Ausdruecklich leer ('') laesst ihn aus; beide Update-Kriterien bleiben "
            "dann PENDING. Pflichtangabe, damit Vergessen und Verzicht sich unterscheiden."
        ),
    )
    publish.add_argument(
        "--yes",
        action="store_true",
        help="Bestaetigung ueberspringen (nur fuer Proben ohne Terminal).",
    )

    finalize = commands.add_parser("finalize", help="Runbook-Schritt 9: Nachweis abschliessen")
    finalize.add_argument("--work-dir", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    ctx = Context(
        runner=traced(_gh),
        command=_command,
        watcher=_watch,
        state_path=args.state_file or default_state_path(),
        repo_dir=args.repo_dir,
    )
    try:
        if args.command == OP_CANDIDATE:
            cmd_candidate(
                ctx,
                repo=args.repo,
                version=args.version,
                candidate_sha=args.candidate_sha,
                target_issue=args.target_issue,
            )
        elif args.command == OP_ACCEPTANCE:
            cmd_acceptance(ctx, repo=args.repo)
        elif args.command == "approve":
            cmd_approve(ctx, repo=args.repo, work_dir=args.work_dir)
        elif args.command == OP_PUBLISH:
            cmd_publish(
                ctx, repo=args.repo, predecessor_tag=args.predecessor, assume_yes=args.yes
            )
        elif args.command == "finalize":
            cmd_finalize(ctx, repo=args.repo, work_dir=args.work_dir)
        else:  # pragma: no cover - argparse laesst nichts anderes durch
            raise DispatchError(f"Unbekanntes Unterkommando {args.command!r}")
    except DispatchError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
