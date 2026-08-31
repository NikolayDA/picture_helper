#!/usr/bin/env python3
"""Post-Release-Update-Nachweis aus dem Publish-Lauf anstossen (#919, Stufe 2).

Runbook-Schritt 9 startete ``release-abnahme.yml`` bisher von Hand, mit vier
aus dem Issue abgeschriebenen Bindungswerten. Dieses Skript uebernimmt genau
diesen Dispatch am Ende eines erfolgreichen Publish-Laufs.

Zwei Randbedingungen bestimmen den Aufbau:

1. ``workflow_dispatch`` **liefert keine Run-ID zurueck** (die REST-Antwort ist
   HTTP 204 ohne Body). Der erzeugte Lauf laesst sich nur wiederfinden, wenn er
   sich selbst kennzeichnet: ``release-abnahme.yml`` traegt dafuer den Input
   ``dispatch_marker`` in seinem ``run-name`` – laut GitHub-Workflow-Syntax darf
   ``run-name`` die Kontexte ``github`` und ``inputs`` referenzieren. Danach
   findet ihn ein kurzes Polling ueber ``displayTitle``.
2. Ein mit ``GITHUB_TOKEN`` ausgeloester ``workflow_dispatch`` erzeugt
   tatsaechlich einen Lauf. Das ist die ausdrueckliche Ausnahme der
   Rekursionssperre: "With the exception of ``workflow_dispatch`` and
   ``repository_dispatch``, other ``GITHUB_TOKEN``-triggered events do not
   create workflow runs at all" (GitHub-Ereignisreferenz).

**Idempotenz.** Der Marker ist deterministisch aus Tag und Kandidaten-Run-ID
gebildet. Ein Wiederanlauf desselben Publish-Laufs findet den bereits
existierenden Abnahme-Lauf und dispatcht **nicht** erneut – auch dann nicht,
wenn dieser fehlgeschlagen ist. Ein fehlgeschlagener Update-Nachweis ist laut
Runbook ein Incident und wird bewusst nie stillschweigend wiederholt; die
Entscheidung darueber bleibt beim Release-Owner.

**Vorgaenger-Tag.** Er wird nie geraten. ``/releases/latest`` waere durch
Backfills und Pre-Releases verfaelschbar; ohne expliziten Wert wird der
Nachweis sichtbar uebersprungen und die Kriterien bleiben ``PENDING`` statt
fabriziert ``PASS`` – dieselbe Regel, die ``release-abnahme.yml`` fuer seinen
eigenen ``predecessor_tag``-Input bereits fuehrt.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

try:  # Dateiaufruf: ``python scripts/release_update_dispatch.py``
    import release_contract as rc
except ModuleNotFoundError:  # Import ueber Dateipfad bzw. als ``scripts.…``
    from scripts import release_contract as rc

#: Workflow, der den Update-Nachweis auf echter Hardware erbringt.
ACCEPTANCE_WORKFLOW: Final = "release-abnahme.yml"
#: Felder, die das Polling braucht; bewusst knapp gehalten.
RUN_FIELDS: Final = "databaseId,displayTitle,status,conclusion,url,createdAt"
#: Wie viele der juengsten Laeufe nach dem Marker durchsucht werden.
RUN_LIST_LIMIT: Final = 50
#: Polling-Budget nach dem Dispatch. GitHub legt den Lauf in aller Regel in
#: Sekunden an; laenger zu warten verlagert nur Wartezeit in den Publish-Lauf.
POLL_ATTEMPTS: Final = 20
POLL_INTERVAL_S: Final = 6.0

_TAG_RE: Final = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+(?:[.-][0-9A-Za-z.]+)?$")
_RUN_ID_RE: Final = re.compile(r"^[1-9][0-9]*$")

#: Ergebniszustaende. ``dispatched`` ist der Regelfall, die anderen beiden sind
#: bewusst sichtbare Nicht-Handlungen statt stiller Auslassungen.
ACTION_DISPATCHED: Final = "dispatched"
ACTION_ALREADY_PRESENT: Final = "already-present"
ACTION_SKIPPED_NO_PREDECESSOR: Final = "skipped-no-predecessor"


class DispatchError(RuntimeError):
    """Fehler, der den Publish-Lauf sichtbar rot macht."""


@dataclass(frozen=True)
class RunRef:
    """Ein gefundener Abnahme-Lauf."""

    run_id: int
    url: str
    status: str
    conclusion: str
    title: str


def dispatch_marker(*, tag: str, candidate_run_id: str) -> str:
    """Deterministischer Marker – dieselben Bindungswerte, derselbe Marker.

    Genau das traegt die Idempotenz: Ein zweiter Publish-Versuch fuer denselben
    Release erzeugt keinen zweiten Nachweislauf. Der Publish-Lauf selbst geht
    bewusst **nicht** ein; sonst waere jeder Wiederanlauf ein neuer Marker.
    """
    if not _TAG_RE.fullmatch(tag):
        raise DispatchError(f"Tag {tag!r} entspricht nicht dem Schema vX.Y.Z")
    if not _RUN_ID_RE.fullmatch(candidate_run_id):
        raise DispatchError(f"candidate_run_id {candidate_run_id!r} ist keine positive Ganzzahl")
    return f"update-check:{tag}:{candidate_run_id}"


def select_marked_run(runs: object, *, marker: str) -> RunRef | None:
    """Findet den Lauf, der den Marker in seinem ``displayTitle`` traegt.

    Mehrere Treffer werden nicht als Fehler behandelt, sondern der **juengste**
    gewaehlt (die Liste kommt absteigend nach Startzeit): Ein manuell
    nachgezogener Lauf mit demselben Marker ist ein legitimer Zustand, und der
    zuletzt gestartete ist der aussagekraeftige.
    """
    if not isinstance(runs, list):
        raise DispatchError("Laufliste ist keine Liste")
    for item in runs:
        if not isinstance(item, dict):
            continue
        entry: dict[str, Any] = item
        if marker not in str(entry.get("displayTitle") or ""):
            continue
        raw_id = entry.get("databaseId")
        if not isinstance(raw_id, int) or raw_id <= 0:
            raise DispatchError(f"Lauf mit Marker {marker} ohne brauchbare databaseId")
        return RunRef(
            run_id=raw_id,
            url=str(entry.get("url") or ""),
            status=str(entry.get("status") or ""),
            conclusion=str(entry.get("conclusion") or ""),
            title=str(entry.get("displayTitle") or ""),
        )
    return None


#: Ein ``gh``-Aufruf: bekommt die Argumente ohne fuehrendes ``gh`` und liefert
#: stdout. Injizierbar, damit die Entscheidungslogik ohne Netz testbar ist
#: (dasselbe Muster wie der Fetcher in ``scripts/public_download_check.py``).
Runner = Callable[[Sequence[str]], str]


def _gh(args: Sequence[str]) -> str:
    result = subprocess.run(
        ["gh", *args], capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise DispatchError(
            f"gh {' '.join(args)} scheiterte (Exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout


def find_existing_run(runner: Runner, *, repo: str, marker: str) -> RunRef | None:
    """Sucht einen bereits vorhandenen Nachweislauf zu diesem Marker."""
    raw = runner([
        "run", "list", "--repo", repo, "--workflow", ACCEPTANCE_WORKFLOW,
        "--event", "workflow_dispatch", "--limit", str(RUN_LIST_LIMIT),
        "--json", RUN_FIELDS,
    ])
    return select_marked_run(json.loads(raw or "[]"), marker=marker)


def verify_dispatch_ref(runner: Runner, *, repo: str, ref: str, expected_sha: str) -> str:
    """Prueft den Dispatch-Ref gegen den Kandidaten-SHA – **nur vor einem Dispatch**.

    Die Regel selbst liegt im Freigabevertrag (:func:`release_contract.
    validate_release_ref`); hier steht nur der Netzweg. Sie gehoert genau an
    diese Stelle und nicht in einen vorgelagerten Workflow-Schritt: Nach
    Runbook-Schritt 9 darf der Release-Ref geloescht sein, und ein
    Wiederanlauf, der den vorhandenen Nachweislauf findet, dispatcht gar nicht
    mehr. Eine unbedingte Pruefung machte genau diesen idempotenten
    Wiederanlauf rot – wegen einer Quelle, die niemand mehr braucht.
    """
    try:
        raw = runner(["api", f"repos/{repo}/git/ref/heads/{ref}"])
    except DispatchError as exc:
        raise DispatchError(
            f"Dispatch-Ref {ref} ist nicht abrufbar ({exc}). Nach Schritt 9 darf er "
            "geloescht sein - dann bleibt der manuelle Weg aus Runbook-Schritt 9."
        ) from exc
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise DispatchError(f"Ref-Antwort fuer {ref} ist kein JSON: {exc}") from exc
    try:
        return rc.validate_release_ref(payload, expected_ref=ref, expected_sha=expected_sha)
    except rc.ContractError as exc:
        raise DispatchError(f"Dispatch-Ref {ref} nicht verwendbar: {exc}") from exc


def dispatch_acceptance_run(
    runner: Runner,
    *,
    repo: str,
    ref: str,
    candidate_run_id: str,
    predecessor_tag: str,
    target_issue: str,
    publish_run_id: str,
    marker: str,
) -> None:
    """Startet ``release-abnahme.yml`` mit vollstaendig gebundenen Eingaben.

    ``platforms=alle`` ist fest verdrahtet: Beide Post-Release-Kriterien
    (``UPDATE-LINUX-ARM-01`` und ``UPDATE-MACOS-ARM-01``) entstehen nur in einem
    Lauf ueber beide Plattformen; ein Einzelplattform-Lauf liesse das jeweils
    andere Kriterium ``PENDING`` zurueck.

    ``target_issue`` wird **immer** uebergeben, auch leer. Wuerde es beim
    leeren Wert weggelassen, griffe im ausgeloesten Lauf dessen eigener
    Default (``595``) - der Release-Owner hat den Kommentar im Publish-Lauf
    aber ausdruecklich abgewaehlt ("Leer = nur Artefakt und Job-Summary"), und
    aus dieser Nicht-Angabe duerfte kein Schreibvorgang in ein fremdes Issue
    werden. Der Abnahme-Lauf behandelt den leeren Wert seit #919 als
    ausdrueckliches "nicht kommentieren".
    """
    args = [
        "workflow", "run", ACCEPTANCE_WORKFLOW, "--repo", repo, "--ref", ref,
        "-f", f"run_id={candidate_run_id}",
        "-f", "platforms=alle",
        "-f", "dry_run=false",
        "-f", f"predecessor_tag={predecessor_tag}",
        "-f", f"dispatch_marker={marker}",
        "-f", f"publish_run_id={publish_run_id}",
        "-f", f"target_issue={target_issue}",
    ]
    runner(args)


def await_dispatched_run(
    runner: Runner,
    *,
    repo: str,
    marker: str,
    attempts: int = POLL_ATTEMPTS,
    interval_s: float = POLL_INTERVAL_S,
    sleep: Callable[[float], None] = time.sleep,
) -> RunRef:
    """Wartet, bis der eben ausgeloeste Lauf in der Liste auftaucht.

    Ohne diesen Schritt bliebe der Nachweislauf unverlinkt: ``workflow_dispatch``
    antwortet mit HTTP 204 ohne Body, die Run-ID entsteht erst serverseitig.
    """
    for attempt in range(attempts):
        found = find_existing_run(runner, repo=repo, marker=marker)
        if found is not None:
            return found
        if attempt < attempts - 1:
            sleep(interval_s)
    raise DispatchError(
        f"Der ausgeloeste Abnahme-Lauf mit Marker {marker} war nach "
        f"{attempts} Versuchen nicht auffindbar. Der Dispatch kann trotzdem "
        "gelaufen sein - vor einem erneuten Start die Actions-Uebersicht pruefen."
    )


def render_report(
    *, action: str, marker: str, run: RunRef | None, predecessor_tag: str, ref: str
) -> str:
    """Markdown fuer Job-Summary und Issue-Kommentar."""
    lines = [
        "## Post-Release-Update-Nachweis (UPDATE-LINUX-ARM-01 / UPDATE-MACOS-ARM-01)",
        "",
    ]
    if action == ACTION_SKIPPED_NO_PREDECESSOR:
        lines += [
            "**Uebersprungen:** kein `predecessor_tag` angegeben.",
            "",
            "Der Vorgaenger wird bewusst nicht geraten - `/releases/latest` ist durch "
            "Backfills und Pre-Releases verfaelschbar. Beide Update-Kriterien bleiben "
            "`PENDING` und werden ueber den manuellen Weg aus Runbook-Schritt 9 "
            "nachgezogen.",
        ]
        return "\n".join(lines) + "\n"
    assert run is not None  # jeder andere Ausgang hat einen Lauf
    verb = (
        "Bereits vorhanden (kein zweiter Dispatch)"
        if action == ACTION_ALREADY_PRESENT
        else "Ausgeloest"
    )
    lines += [
        f"**{verb}:** [Abnahme-Lauf {run.run_id}]({run.url})",
        "",
        "| Feld | Wert |",
        "|---|---|",
        f"| Marker | `{marker}` |",
        f"| Vorgaenger-Tag | `{predecessor_tag}` |",
        f"| Dispatch-Ref | `{ref}` |",
        f"| Status | `{run.status}` |",
        f"| Ergebnis | `{run.conclusion or 'offen'}` |",
        "",
        "Der Lauf erbringt beide Post-Release-Kriterien und traegt die finale "
        "Release-Instanz nach; bis dahin bleiben sie `PENDING`.",
    ]
    if action == ACTION_ALREADY_PRESENT:
        lines += [
            "",
            "Ein Lauf mit demselben Marker existiert bereits. Ein fehlgeschlagener "
            "Nachweis wird bewusst **nicht** automatisch wiederholt: Laut Runbook ist "
            "das ein Incident, ueber den der Release-Owner entscheidet.",
        ]
    return "\n".join(lines) + "\n"


def _write_outputs(values: dict[str, str]) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    with Path(output).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def run(
    *,
    repo: str,
    ref: str,
    expected_sha: str,
    tag: str,
    candidate_run_id: str,
    predecessor_tag: str,
    target_issue: str,
    publish_run_id: str,
    markdown: Path,
    runner: Runner | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Fuehrt Idempotenzpruefung, Dispatch und Korrelation aus; liefert die Aktion."""
    call = runner if runner is not None else _gh
    marker = dispatch_marker(tag=tag, candidate_run_id=candidate_run_id)

    if not predecessor_tag:
        action, found = ACTION_SKIPPED_NO_PREDECESSOR, None
    else:
        if not _TAG_RE.fullmatch(predecessor_tag):
            raise DispatchError(
                f"predecessor_tag {predecessor_tag!r} entspricht nicht dem Schema vX.Y.Z"
            )
        existing = find_existing_run(call, repo=repo, marker=marker)
        if existing is not None:
            action, found = ACTION_ALREADY_PRESENT, existing
        else:
            verify_dispatch_ref(call, repo=repo, ref=ref, expected_sha=expected_sha)
            dispatch_acceptance_run(
                call,
                repo=repo,
                ref=ref,
                candidate_run_id=candidate_run_id,
                predecessor_tag=predecessor_tag,
                target_issue=target_issue,
                publish_run_id=publish_run_id,
                marker=marker,
            )
            action = ACTION_DISPATCHED
            found = await_dispatched_run(call, repo=repo, marker=marker, sleep=sleep)

    markdown.parent.mkdir(parents=True, exist_ok=True)
    markdown.write_text(
        render_report(
            action=action, marker=marker, run=found,
            predecessor_tag=predecessor_tag, ref=ref,
        ),
        encoding="utf-8",
    )
    _write_outputs({
        "action": action,
        "acceptance_run_id": str(found.run_id) if found else "",
        "acceptance_run_url": found.url if found else "",
        "marker": marker,
    })
    return action


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument(
        "--ref", required=True, help="Dispatch-Ref des Abnahme-Laufs (release/vX.Y.Z)."
    )
    parser.add_argument(
        "--expected-sha", required=True, help="Kandidaten-SHA aus dem Freigabemanifest."
    )
    parser.add_argument("--tag", required=True, help="Veroeffentlichter Release-Tag.")
    parser.add_argument("--candidate-run-id", required=True)
    parser.add_argument("--publish-run-id", required=True)
    parser.add_argument("--predecessor-tag", default="", help="Leer = Nachweis ueberspringen.")
    parser.add_argument("--target-issue", default="")
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        action = run(
            repo=args.repo,
            ref=args.ref,
            expected_sha=args.expected_sha,
            tag=args.tag,
            candidate_run_id=args.candidate_run_id,
            predecessor_tag=args.predecessor_tag,
            target_issue=args.target_issue,
            publish_run_id=args.publish_run_id,
            markdown=args.markdown,
        )
    except DispatchError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 2
    print(f"Update-Nachweis: {action}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
