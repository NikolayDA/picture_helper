"""Guards for the scheduled benchmark workflow."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "benchmark.yml"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_benchmark_workflow_carries_baseline_via_artifact() -> None:
    """Die Baseline gleitet ueber das Ergebnis-Artefakt statt ueber main.

    Der geschuetzte ``main``-Branch laesst sich vom ``GITHUB_TOKEN`` nicht
    beschreiben (Issue #545). Der Job holt daher vor dem Messen das Artefakt des
    letzten erfolgreichen Laufs zurueck und laedt sein eigenes Ergebnis wieder
    hoch – ganz ohne Schreibzugriff auf main.
    """
    text = _workflow_text()

    # actions: read wird gebraucht, um das Vorlauf-Artefakt zu laden.
    assert "actions: read" in text
    # Baseline des letzten erfolgreichen Laufs zurueckholen …
    assert "gh run download" in text
    assert "--status success" in text
    # … und das eigene Ergebnis fuer den naechsten Lauf weiterreichen.
    assert "actions/upload-artifact" in text
    assert "name: benchmark-results" in text


def test_benchmark_workflow_never_writes_to_protected_main() -> None:
    """Kein Push/PR und keine Schreibrechte – sonst kehrt Issue #545 zurueck."""
    text = _workflow_text()

    # Weder Direkt-Push noch Auto-PR: beide scheitern an der Branch-Protection.
    assert "git push" not in text
    assert "gh pr create" not in text
    assert "git commit" not in text
    # Keine Schreib-Scopes, die einen main-Write ueberhaupt ermoeglichen wuerden.
    assert "contents: write" not in text
    assert "pull-requests: write" not in text


def test_benchmark_workflow_still_fails_on_real_regression() -> None:
    """Eine bestaetigte Regression macht den Job weiterhin sichtbar rot."""
    text = _workflow_text()

    assert "--fail-on-regression" in text
    assert "steps.bench.outcome == 'failure'" in text
