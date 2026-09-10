"""Syntax-Schutz für die GitHub-Actions-Workflows.

Jede Datei unter ``.github/workflows/`` muss valides YAML sein und einen
``jobs``-Block besitzen. Hintergrund: ein unquotierter ``name:``-Wert mit
eingebettetem ``": "`` (z. B. ``name: ... (security: pip>=26.1.2)``) wird von
YAML als verschachteltes Mapping gelesen und lässt den Workflow als
``startup_failure`` mit null Jobs scheitern – ohne dass ein Test läuft. Die
text-basierten CI-Tests (`test_ci_pip_pin`/`test_ci_qt_packages`) fangen das
nicht; dieser Parse-Test schliesst die Lücke.

Aus demselben Grund wird hier auch die **Kontext-Verfügbarkeit** im
Job-``env`` geprüft: ``jobs.<job_id>.env`` erlaubt nur ``github``, ``needs``,
``strategy``, ``matrix``, ``vars``, ``secrets`` und ``inputs``. Ein
``${{ runner.temp }}`` dort lässt GitHub den **gesamten** Workflow-Lauf mit
``Unrecognized named-value: 'runner'`` ablehnen – ebenfalls, bevor ein Test
läuft. Weder ``bash -n`` noch die YAML-lesenden Gate-Tests fangen das, weil die
Expression lokal nie ausgewertet wird (Review-Befund PR #925).

PyYAML ist seit #1016 deklarierte ``[test]``-Abhängigkeit; zuvor wurde der
Test ohne das Paket still übersprungen – in der PR-CI dauerhaft.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_WORKFLOW_DIR = _ROOT / ".github" / "workflows"

_WORKFLOWS = sorted(_WORKFLOW_DIR.glob("*.yml")) + sorted(_WORKFLOW_DIR.glob("*.yaml"))


def test_workflow_dir_is_non_empty() -> None:
    # Schutz gegen einen leeren Glob (verschobenes Verzeichnis o. Ä.), der die
    # Parametrisierung sonst lautlos auf null Fälle schrumpfen liesse.
    assert _WORKFLOWS, f"keine Workflow-Dateien unter {_WORKFLOW_DIR} gefunden"


@pytest.mark.parametrize("path", _WORKFLOWS, ids=lambda p: p.name)
def test_workflow_is_valid_yaml(path: Path) -> None:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover - Fehlertext ist die Aussage
        pytest.fail(f"{path.name} ist kein valides YAML: {exc}")

    assert isinstance(doc, dict), f"{path.name}: Top-Level ist kein Mapping"
    # ``on`` wird von PyYAML (YAML 1.1) als Boolean-Key True gelesen – daher
    # nur den robusten ``jobs``-Block prüfen.
    assert "jobs" in doc, f"{path.name}: kein 'jobs'-Block"


#: Kontexte, die GitHub in ``jobs.<job_id>.env`` auswertet. Alles andere –
#: allen voran ``runner`` und ``env`` selbst – gibt es dort erst auf
#: Schritt-Ebene (``jobs.<job_id>.steps.env``).
_JOB_ENV_CONTEXTS = frozenset(
    {"github", "needs", "strategy", "matrix", "vars", "secrets", "inputs"}
)
_CONTEXT_REF = re.compile(r"(?<![\w.'\"])([A-Za-z_][A-Za-z0-9_-]*)\s*\.")


@pytest.mark.parametrize("path", _WORKFLOWS, ids=lambda p: p.name)
def test_job_level_env_uses_only_available_contexts(path: Path) -> None:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    for job_id, job in (doc.get("jobs") or {}).items():
        for name, value in ((job or {}).get("env") or {}).items():
            for expression in re.findall(r"\$\{\{(.*?)\}\}", str(value), re.S):
                unavailable = {
                    ref
                    for ref in _CONTEXT_REF.findall(expression)
                    if ref not in _JOB_ENV_CONTEXTS
                }
                assert not unavailable, (
                    f"{path.name}: Job '{job_id}', env '{name}' nutzt "
                    f"{sorted(unavailable)} – in jobs.<job_id>.env nicht verfuegbar. "
                    "GitHub lehnt den gesamten Lauf mit 'Unrecognized named-value' ab. "
                    "Auf Schritt-Ebene setzen oder im Shell ueber $GITHUB_ENV bilden."
                )


#: Der einzige erforderliche Branch-Protection-Status (Live-Snapshot in
#: ``docs/PROZESSE_UML.md``, gegen den PR-CI-Jobnamen gehalten von
#: ``tests/test_process_documentation.py``).
_REQUIRED_STATUS_JOB_NAME = "Lightweight PR checks"

#: Workflows, deren PR-Lauf seit #1038 an seine Eingaben gebunden ist. Der
#: Filter ist eine handgepflegte Kopie der Aussage "laeuft nur, wenn seine
#: Eingaben betroffen sind" in ``docs/PROZESSE_UML.md`` §2, ``SECURITY.md`` und
#: ``CLAUDE.md``; ohne Waechter faellt ein entfernter Filter nirgends auf.
_PATH_FILTERED_PR_WORKFLOWS = ("codeql.yml", "dependency-audit.yml", "license-check.yml")


def _triggers(path: Path) -> dict[str, object]:
    """``on:``-Block eines Workflows.

    PyYAML liest ``on`` nach YAML 1.1 als Boolean-Key ``True``; neuere
    Fassungen koennten den String liefern. Beide Formen werden akzeptiert,
    damit der Waechter nicht an der Parser-Version haengt.
    """
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(doc, dict), path.name
    for key in (True, "on"):
        block = doc.get(key)
        if isinstance(block, dict):
            return block
    raise AssertionError(f"{path.name}: kein auswertbarer on-Block")


def _pull_request_is_path_filtered(triggers: dict[str, object]) -> bool:
    trigger = triggers.get("pull_request")
    if not isinstance(trigger, dict):
        return False
    return "paths" in trigger or "paths-ignore" in trigger


def _job_names(path: Path) -> set[str]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    jobs = (doc or {}).get("jobs") or {}
    return {str((job or {}).get("name") or job_id) for job_id, job in jobs.items()}


@pytest.mark.parametrize("path", _WORKFLOWS, ids=lambda p: p.name)
def test_no_path_filtered_workflow_carries_the_required_status_job(path: Path) -> None:
    """Die Vorbedingung der Pfadfilter aus #1038 darf nicht still brechen.

    GitHub meldet fuer einen wegen Pfadfilter uebersprungenen Workflow **gar
    keinen** Status. Ist derselbe Check ein *erforderlicher*
    Branch-Protection-Status, bleibt der PR damit dauerhaft auf ``Expected``
    stehen und ist nicht mehr mergebar – bei genau den Docs-only-PRs, die der
    Filter entlasten soll. Solange ``Lightweight PR checks`` der einzige
    Pflichtstatus ist, ist die Regel einfach: Dieser Jobname und ein
    PR-Pfadfilter schliessen sich aus.

    Der Waechter greift in beide Richtungen – ein Filter in ``pr-ci.yml`` faellt
    genauso auf wie ein nach ``codeql.yml`` verschobener Pflicht-Jobname.
    """
    if not _pull_request_is_path_filtered(_triggers(path)):
        return
    assert _REQUIRED_STATUS_JOB_NAME not in _job_names(path), (
        f"{path.name} filtert seinen pull_request-Trigger nach Pfaden und traegt "
        f"zugleich den Pflichtstatus-Jobnamen {_REQUIRED_STATUS_JOB_NAME!r}. Ein "
        "uebersprungener Pflicht-Check laesst den PR dauerhaft auf 'Expected' "
        "stehen – entweder den Filter entfernen oder den Pflichtstatus umstellen."
    )


@pytest.mark.parametrize("name", _PATH_FILTERED_PR_WORKFLOWS)
def test_documented_pr_path_filters_stay_in_place(name: str) -> None:
    """#1038: Die drei PR-Filter sind dokumentiert und brauchen deshalb einen Wächter."""
    trigger = _triggers(_WORKFLOW_DIR / name).get("pull_request")
    assert isinstance(trigger, dict), f"{name}: pull_request ohne Filterblock"
    paths = trigger.get("paths")
    assert isinstance(paths, list) and paths, (
        f"{name}: pull_request.paths fehlt oder ist leer – Doku (PROZESSE_UML §2, "
        "SECURITY.md, CLAUDE.md) behauptet den Filter weiterhin"
    )
    assert f".github/workflows/{name}" in paths, (
        f"{name}: der Filter muss die eigene Workflow-Datei enthalten, sonst "
        "startet eine Änderung an ihm selbst keinen Probelauf"
    )


@pytest.mark.parametrize("name", _PATH_FILTERED_PR_WORKFLOWS)
def test_freshness_triggers_stay_unfiltered(name: str) -> None:
    """Push- und Zeitplan-Läufe tragen die Frische und bleiben ungefiltert (#1038).

    Ein Pfadfilter dort nähme genau das weg, was den PR-Filter erst vertretbar
    macht: CodeQL-Queries und CVE-Datenbanken ändern sich ohne jeden Commit,
    der Lizenz-Snapshot muss auch nach einem Docs-only-Merge geprüft werden.
    """
    triggers = _triggers(_WORKFLOW_DIR / name)
    for event in ("push", "schedule"):
        trigger = triggers.get(event)
        if not isinstance(trigger, dict):
            continue
        for key in ("paths", "paths-ignore"):
            assert key not in trigger, f"{name}: {event} darf keinen {key}-Filter tragen"


def test_required_status_guard_would_catch_a_real_violation(tmp_path: Path) -> None:
    """Negativkontrolle: Der Wächter oben prüft echte Dateien und wäre sonst tot.

    Aufgerufen wird der **Wächter selbst**, nicht nur seine Helfer – sonst
    bliebe die Kontrolle eine Aussage über das Prädikat statt über die Regel
    (Review #1067).
    """
    offender = tmp_path / "offender.yml"
    offender.write_text(
        "name: X\n"
        "on:\n"
        "  pull_request:\n"
        "    paths: ['**/*.py']\n"
        "jobs:\n"
        "  check:\n"
        f"    name: {_REQUIRED_STATUS_JOB_NAME}\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match=_REQUIRED_STATUS_JOB_NAME):
        test_no_path_filtered_workflow_carries_the_required_status_job(offender)

    clean = tmp_path / "clean.yml"
    clean.write_text(
        "name: X\n"
        "on:\n"
        "  pull_request:\n"
        "    branches: [main]\n"
        "jobs:\n"
        "  check:\n"
        f"    name: {_REQUIRED_STATUS_JOB_NAME}\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )
    # Derselbe Pflicht-Jobname ohne Filter ist erlaubt – der Wächter kehrt
    # ohne Befund zurück (das ist die Lage von pr-ci.yml).
    test_no_path_filtered_workflow_carries_the_required_status_job(clean)
    assert not _pull_request_is_path_filtered(_triggers(clean))
