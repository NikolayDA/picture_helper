"""Jeder Workflow, der ``make pr-check`` faehrt, braucht den vollen Checkout.

``pr-check`` enthaelt seit #870 (PR-Merge ``72a97ee``) das fail-closed
``release-freeze-check``. Das Gate loest den Basis-Tag aus dem Freeze-Dokument
in der lokalen Git-Historie auf; ein flacher Checkout ohne Tags laesst es mit
``base-tag-missing`` scheitern.

#870 hat ``fetch-depth: 0`` nur in ``pr-ci.yml`` ergaenzt, nicht in ``ci.yml``.
Beide fahren ``make pr-check``. Aufgefallen ist die Luecke erst im
2.9.0-Kandidatenbau: ``ci.yml`` laeuft nur woechentlich, manuell oder als Gate
aus ``release-linux.yml``, und alle drei Anlaesse lagen zwischen #870 und dem
Build nicht an. Alle acht Matrix-Beine fielen dann gleichzeitig aus – nach
gruenen Tests, allein am Gate.

Das ist dieselbe Drift-Klasse wie die Qt-apt-Paketliste (Befund N6): eine
Voraussetzung, die in *jedem* aufrufenden Workflow gelten muss, aber an einer
Stelle nachgezogen wurde. Dieser Test bindet beide Seiten aneinander, statt sich
auf die Sorgfalt beim naechsten Umbau zu verlassen.
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"

#: Das Target, dessen Voraussetzung hier durchgesetzt wird.
PR_CHECK = "make pr-check"
CHECKOUT = "actions/checkout"


def _jobs_running_pr_check(document: dict) -> dict[str, dict]:
    """Jobs des Dokuments, deren Schritte ``make pr-check`` ausfuehren."""
    found = {}
    for name, job in (document.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if isinstance(step, dict) and PR_CHECK in str(step.get("run") or ""):
                found[name] = job
                break
    return found


def _checkout_steps(job: dict) -> list[dict]:
    return [
        step
        for step in job.get("steps") or []
        if isinstance(step, dict) and CHECKOUT in str(step.get("uses") or "")
    ]


def _callers() -> list[tuple[Path, str, dict]]:
    """Alle ``(Datei, Jobname, Job)``-Tripel, die ``make pr-check`` fahren."""
    callers = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if PR_CHECK not in text:
            continue
        document = yaml.safe_load(text)
        for name, job in _jobs_running_pr_check(document).items():
            callers.append((path, name, job))
    return callers


def test_pr_check_is_actually_called_somewhere() -> None:
    """Fail-closed: Findet der Test keine Aufrufer, prueft er nichts.

    Ohne diese Zusicherung wuerde eine Umbenennung des Targets die eigentliche
    Pruefung unten stillschweigend leerlaufen lassen.
    """
    callers = _callers()
    assert callers, (
        f"kein Workflow fuehrt {PR_CHECK!r} aus – wurde das Makefile-Target "
        "umbenannt? Dann ist dieser Test nachzuziehen."
    )


def test_every_pr_check_job_checks_out_full_history() -> None:
    """Jeder Aufrufer holt Tags und Historie, sonst scheitert das Freeze-Gate."""
    offenders = []
    for path, name, job in _callers():
        depths = [
            (step.get("with") or {}).get("fetch-depth") for step in _checkout_steps(job)
        ]
        if not depths:
            offenders.append(f"{path.name}:{name} (kein Checkout-Schritt)")
        elif not any(str(depth) == "0" for depth in depths):
            offenders.append(f"{path.name}:{name} (fetch-depth={depths})")

    assert not offenders, (
        "Diese Jobs fahren `make pr-check` ohne vollstaendigen Checkout und "
        "scheitern deshalb mit 'base-tag-missing' am Release-Freeze-Gate: "
        f"{offenders}. Ergaenze `fetch-depth: 0` am actions/checkout-Schritt."
    )
