"""Jeder Workflow-Job, der das Freeze-Gate faehrt, braucht den vollen Checkout.

Das fail-closed ``release-freeze-check`` loest den Basis-Tag aus dem
Freeze-Dokument in der lokalen Git-Historie auf; ein flacher Checkout ohne Tags
laesst es mit ``base-tag-missing`` scheitern.

#870 (PR-Merge ``72a97ee``) hat das Gate in den ``pr-check``-Target aufgenommen
und ``fetch-depth: 0`` ergaenzt – aber nur in ``pr-ci.yml``, nicht in
``ci.yml``. Beide fahren ``make pr-check``. Aufgefallen ist die Luecke erst im
2.9.0-Kandidatenbau: ``ci.yml`` laeuft nur woechentlich, manuell oder als Gate
aus ``release-linux.yml``, und alle drei Anlaesse lagen zwischen #870 und dem
Build nicht an. Alle acht Matrix-Beine fielen dann gleichzeitig aus – nach
gruenen Tests, allein am Gate.

Dieselbe Drift-Klasse wie die Qt-apt-Paketliste (Befund N6): eine Voraussetzung,
die in *jedem* aufrufenden Job gelten muss, aber an einer Stelle nachgezogen
wurde.

Die Kette ist zweigliedrig – Job → Make-Target und Target → Gate. Ein Test, der
nur ``make pr-check`` kennt, sichert bloss das erste Glied: Wanderte das Gate
eines Tages von ``pr-check`` nach ``check``, bliebe er gruen, waehrend die
Workflows mit ``make check`` ungeprueft ohne Historie liefen – derselbe
Fehlermodus wie #870, eine Ebene tiefer (Review-Befund auf PR #880). Die
betroffenen Targets werden deshalb **aus dem Makefile abgeleitet**, nicht
hartkodiert.

Bewusst **ohne** ``yaml``: PyYAML ist keine deklarierte Test-Abhaengigkeit. Die
Repo-Konvention dafuer ist ein weicher ``importorskip`` – fuer einen Waechter
waere das der stille Skip genau dort, wo er zaehlt, naemlich in der CI. Die
Zerlegung laeuft daher ueber die Einrueckung, wie in
``test_license_workflow_security.py``.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
MAKEFILE = ROOT / "Makefile"

#: Das Target, dessen Voraussetzung hier durchgesetzt wird.
GATE = "release-freeze-check"

_RULE_RE = re.compile(r"^(?P<target>[A-Za-z][A-Za-z0-9_-]*):(?P<deps>[^=]*)$")


def _uncommented(text: str) -> list[str]:
    """Zeilen ohne reine Kommentarzeilen.

    Ein ``make check`` in einer Kommentarzeile ist kein Aufruf; ``coverage.yml``
    erwaehnt ``pr-check`` genau so.
    """
    return [line for line in text.splitlines() if not line.strip().startswith("#")]


def _make_rules() -> dict[str, list[str]]:
    """``{Target: [Voraussetzungen]}`` aus dem Makefile."""
    rules: dict[str, list[str]] = {}
    for line in _uncommented(MAKEFILE.read_text(encoding="utf-8")):
        if line.startswith((" ", "\t")):
            continue
        match = _RULE_RE.match(line.rstrip())
        if match:
            rules[match.group("target")] = match.group("deps").split()
    return rules


def _gate_targets() -> set[str]:
    """Targets, die ``release-freeze-check`` transitiv ziehen (inkl. es selbst)."""
    rules = _make_rules()
    targets = {GATE}
    changed = True
    while changed:  # Fixpunkt; die Regelmenge ist klein.
        changed = False
        for target, deps in rules.items():
            if target not in targets and targets.intersection(deps):
                targets.add(target)
                changed = True
    return targets


def _job_blocks(text: str) -> dict[str, str]:
    """Jobbloecke eines Workflows nach Jobnamen.

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
        if indent == 2 and stripped.endswith(":") and not stripped.startswith("#"):
            if name is not None:
                blocks[name] = "\n".join(body)
            name, body = stripped[:-1], []
        elif name is not None:
            body.append(line)
    if name is not None:
        blocks[name] = "\n".join(body)
    return blocks


def _steps(block: str) -> list[str]:
    """Die einzelnen Schritte eines Jobblocks als Textstuecke."""
    steps: list[str] = []
    current: list[str] | None = None
    for line in block.splitlines():
        if line.lstrip().startswith("- "):
            if current is not None:
                steps.append("\n".join(current))
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        steps.append("\n".join(current))
    return steps


def _invokes_gate(block: str, targets: set[str]) -> bool:
    body = "\n".join(_uncommented(block))
    return any(re.search(rf"\bmake\s+{re.escape(t)}\b", body) for t in targets)


def _callers() -> list[tuple[str, str, str]]:
    """``(Dateiname, Jobname, Jobblock)`` fuer jeden Job, der das Gate faehrt."""
    targets = _gate_targets()
    paths = sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))
    callers = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for name, block in _job_blocks(text).items():
            if _invokes_gate(block, targets):
                callers.append((path.name, name, block))
    return callers


def _project_checkouts(block: str) -> list[str]:
    """Checkout-Schritte **ohne** ``path:`` – also die des Projekts selbst.

    Ein Zweitklon eines anderen Repos unter ``path:`` sagt nichts ueber die
    Historie aus, die das Gate liest.
    """
    return [
        step
        for step in _steps(block)
        if "actions/checkout" in step
        and not any(line.strip().startswith("path:") for line in step.splitlines())
    ]


def test_gate_target_chain_is_intact() -> None:
    """Fail-closed: Das Gate haengt an mindestens einem aufrufbaren Target.

    Ohne diese Zusicherung liesse ein umbenanntes oder entferntes Gate die
    Pruefung unten still leerlaufen.
    """
    targets = _gate_targets()
    assert targets - {GATE}, (
        f"kein Make-Target zieht {GATE!r} – wurde es entfernt oder umbenannt? "
        "Dann ist dieser Test nachzuziehen."
    )


def test_known_callers_are_both_found() -> None:
    """Die beiden bekannten Aufrufer werden erkannt.

    Haelt die Zerlegung ehrlich: Faende sie nur noch einen, sagte der Test
    unten fuer den anderen nichts mehr aus, ohne fehlzuschlagen.
    """
    files = {name for name, _job, _block in _callers()}
    assert files == {"ci.yml", "pr-ci.yml"}, (
        f"erwarte genau ci.yml und pr-ci.yml als Aufrufer, gefunden: {files}. "
        "Ein neuer Aufrufer ist hier einzutragen – und braucht ebenfalls den "
        "vollen Checkout."
    )


def test_every_gate_job_checks_out_full_history() -> None:
    """Jeder Aufrufer holt Tags und Historie, sonst scheitert das Gate.

    Geprueft wird **jeder** Projekt-Checkout des Jobs, nicht nur irgendeiner:
    Ein flacher Projektklon plus ein spaeterer Vollklon wuerde eine
    ``any``-Pruefung befriedigen, waehrend das Gate weiter flache Historie
    saehe (Review-Befund auf PR #880).
    """
    offenders = []
    for file_name, job, block in _callers():
        checkouts = _project_checkouts(block)
        if not checkouts:
            offenders.append(f"{file_name}:{job} (kein Projekt-Checkout)")
            continue
        shallow = [
            step
            for step in checkouts
            if not any(line.strip() == "fetch-depth: 0" for line in step.splitlines())
        ]
        if shallow:
            offenders.append(f"{file_name}:{job} ({len(shallow)} ohne 'fetch-depth: 0')")

    assert not offenders, (
        "Diese Jobs fahren das Release-Freeze-Gate ohne vollstaendigen Checkout "
        "und scheitern deshalb mit 'base-tag-missing': "
        f"{offenders}. Ergaenze `fetch-depth: 0` am actions/checkout-Schritt."
    )
