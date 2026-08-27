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

Bewusst **ohne** ``yaml``: PyYAML ist keine deklarierte Test-Abhaengigkeit. Die
uebliche Repo-Konvention dafuer ist ein weicher ``try/except ImportError``
(siehe ``test_process_documentation.py``) – fuer einen Waechter waere das der
stille Skip genau dort, wo er zaehlt, naemlich in der CI. Stattdessen wird der
Jobblock wie in ``test_license_workflow_security.py`` ueber die Einrueckung
zerlegt.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"

#: Das Target, dessen Voraussetzung hier durchgesetzt wird.
PR_CHECK = "make pr-check"


def _job_blocks(text: str) -> dict[str, str]:
    """Die Jobbloecke eines Workflows, aufgeschluesselt nach Jobnamen.

    Jobs stehen zwei Leerzeichen unter ``jobs:``; ein Block reicht bis zum
    naechsten Jobnamen oder zum Dateiende.
    """
    lines = text.splitlines()
    try:
        start = lines.index("jobs:")
    except ValueError:
        return {}

    blocks: dict[str, str] = {}
    name: str | None = None
    body: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        is_job_header = (
            indent == 2 and stripped.endswith(":") and not stripped.startswith("#")
        )
        if is_job_header:
            if name is not None:
                blocks[name] = "\n".join(body)
            name, body = stripped[:-1], []
        elif name is not None:
            body.append(line)
    if name is not None:
        blocks[name] = "\n".join(body)
    return blocks


def _callers() -> list[tuple[str, str, str]]:
    """Alle ``(Dateiname, Jobname, Jobblock)``-Tripel mit ``make pr-check``."""
    callers = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if PR_CHECK not in text:
            continue
        for name, block in _job_blocks(text).items():
            if PR_CHECK in block:
                callers.append((path.name, name, block))
    return callers


def test_pr_check_is_actually_called_somewhere() -> None:
    """Fail-closed: Findet der Test keine Aufrufer, prueft er nichts.

    Ohne diese Zusicherung liesse eine Umbenennung des Targets – oder ein
    Fehler in der Blockzerlegung – die eigentliche Pruefung unten still
    leerlaufen.
    """
    callers = _callers()
    assert callers, (
        f"kein Jobblock fuehrt {PR_CHECK!r} aus – wurde das Makefile-Target "
        "umbenannt oder die Workflow-Struktur geaendert? Dann ist dieser Test "
        "nachzuziehen."
    )


def test_known_callers_are_both_found() -> None:
    """Die beiden bekannten Aufrufer werden erkannt.

    Haelt die Blockzerlegung ehrlich: Faende sie nur noch einen der beiden,
    wuerde der Test unten fuer den anderen nichts mehr aussagen, ohne
    fehlzuschlagen.
    """
    files = {name for name, _job, _block in _callers()}
    assert files == {"ci.yml", "pr-ci.yml"}, (
        f"erwarte genau ci.yml und pr-ci.yml als Aufrufer, gefunden: {files}. "
        "Ein neuer Aufrufer ist hier einzutragen – und braucht ebenfalls den "
        "vollen Checkout."
    )


def test_every_pr_check_job_checks_out_full_history() -> None:
    """Jeder Aufrufer holt Tags und Historie, sonst scheitert das Freeze-Gate."""
    offenders = []
    for file_name, job, block in _callers():
        if "actions/checkout" not in block:
            offenders.append(f"{file_name}:{job} (kein Checkout-Schritt)")
        elif not any(
            line.strip() == "fetch-depth: 0" for line in block.splitlines()
        ):
            offenders.append(f"{file_name}:{job} (kein 'fetch-depth: 0')")

    assert not offenders, (
        "Diese Jobs fahren `make pr-check` ohne vollstaendigen Checkout und "
        "scheitern deshalb mit 'base-tag-missing' am Release-Freeze-Gate: "
        f"{offenders}. Ergaenze `fetch-depth: 0` am actions/checkout-Schritt."
    )
