"""Drift-Schutz für den geteilten Diagnoseschritt der Claude-Workflows (#825).

``claude-code-review.yml`` und ``claude.yml`` führen denselben Schritt
„Abgelehnte Werkzeugaufrufe ausweisen": Er zieht aus dem Protokoll der Action
ausschließlich ``permission_denials`` ins Joblog. Der Schritt existiert, weil
ein Agent, der eine Quelle nicht abrufen darf, stillschweigend rät statt
nachzuschlagen – und weil abgelehnte Aufrufe Turns bis zum Budgetende
verbrauchen. Beides war ohne diese Ausgabe nicht erkennbar.

Der Block ist bewusst in beide Dateien kopiert (ein Workflow kann keinen
Schritt aus einem anderen einbinden). Dieser Test hält die Kopien wortgleich –
dasselbe Muster wie der Qt-Paketlisten-Schutz aus Befund N6.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

_ROOT = Path(__file__).resolve().parent.parent
_WORKFLOWS = (
    ".github/workflows/claude-code-review.yml",
    ".github/workflows/claude.yml",
)
_DIAGNOSTIC_NAME = "Abgelehnte Werkzeugaufrufe ausweisen"


def _steps(relative: str) -> list[dict[str, Any]]:
    """Die Schritte des einzigen Jobs in *relative*."""
    data = yaml.safe_load((_ROOT / relative).read_text(encoding="utf-8"))
    jobs = list(data["jobs"].values())
    assert len(jobs) == 1, f"{relative}: unerwartet mehrere Jobs"
    return list(jobs[0]["steps"])


def _step_by_name(relative: str, name: str) -> dict[str, Any]:
    for step in _steps(relative):
        if step.get("name") == name:
            return step
    raise AssertionError(f"{relative}: Schritt {name!r} fehlt")


@pytest.mark.parametrize("relative", _WORKFLOWS)
def test_action_step_carries_the_referenced_id(relative: str) -> None:
    """Der Diagnoseschritt liest ``steps.claude.*`` – die ID muss vergeben sein.

    Ohne ``id: claude`` liefern sowohl ``outcome`` als auch ``execution_file``
    still einen leeren Wert; der Schritt liefe dann nie an, ohne dass es
    auffällt.
    """
    ids = {s.get("id") for s in _steps(relative) if "claude-code-action" in str(s.get("uses", ""))}
    assert ids == {"claude"}, f"{relative}: Action-Schritt ohne id 'claude' ({ids})"


@pytest.mark.parametrize("relative", _WORKFLOWS)
def test_diagnostic_step_never_fails_the_job(relative: str) -> None:
    """Die Diagnose darf einen sonst grünen Lauf nie rot färben.

    Zusätzlich hängt das Gating am Schritt-*Ergebnis*, nicht am Output-Pfad:
    Bricht die Action früh ab (Auth, Nutzungslimit, Modell nicht gedeckt), gibt
    es kein ``execution_file`` – und genau dann wird die Diagnose gebraucht.
    """
    step = _step_by_name(relative, _DIAGNOSTIC_NAME)
    assert step.get("continue-on-error") is True
    assert step.get("if") == "always() && steps.claude.outcome != 'skipped'"


def test_diagnostic_step_is_identical_in_both_workflows() -> None:
    """Beide Kopien müssen wortgleich bleiben (Drift-Schutz analog N6)."""
    first, second = (_step_by_name(w, _DIAGNOSTIC_NAME) for w in _WORKFLOWS)
    assert first == second, "Diagnoseschritt driftet zwischen den Claude-Workflows"


def test_diagnostic_reports_unreadable_log_instead_of_zero() -> None:
    """Ein jq-Fehler darf nicht als „0 Ablehnungen" durchgehen.

    Das wäre im Joblog nicht vom sauberen Lauf zu unterscheiden – dieselbe
    Falle, die CLAUDE.md für den ClamAV-Scan ausschließt („ein still
    übersprungener Scan gilt nie als bestanden").
    """
    script = _step_by_name(_WORKFLOWS[0], _DIAGNOSTIC_NAME)["run"]
    assert "if ! denials=$(jq" in script, "jq-Fehler wird nicht abgefangen"
    assert "::warning::Protokoll nicht auswertbar" in script
