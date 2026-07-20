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
    assert "--event schedule" in text
    # … ausschliesslich von main, damit ein Feature-Branch-Dispatch die
    # main-Baseline nicht verfaelscht …
    assert "--branch main" in text
    # … in ein leeres Temp-Verzeichnis (gh run download ueberschreibt keine
    # vorhandenen Dateien), sonst rueckt die gleitende Baseline nie vor …
    assert "mktemp" in text
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
    assert "steps.format_bench.outcome == 'failure'" in text
    assert "steps.height_bench.outcome == 'failure'" in text


def test_benchmark_workflow_isolates_format_and_height_suites() -> None:
    """Die 40-MP-Höhenpipeline darf PNG-Wiederholungen nicht beeinflussen."""
    text = _workflow_text()

    assert "--suite formats" in text
    assert "--suite height" in text
    assert "id: format_bench" in text
    assert "id: height_bench" in text


def test_benchmark_workflow_supports_paired_same_runner_comparison() -> None:
    """A/B nutzt denselben Harness/Runner und alterniert die Messreihenfolge."""
    text = _workflow_text()

    assert "mode == 'paired'" in text
    assert "fetch-depth: 0" in text
    assert "git worktree add --detach" in text
    assert 'cp scripts/benchmark.py "$baseline_root/scripts/benchmark.py"' in text
    assert "pair % 2" in text
    assert "default: '4'" in text
    assert "PAIRS % 2" in text
    assert "gerade Zahl zwischen 4 und 10" in text
    assert "paired-compare" in text
    assert "benchmark-ab-results" in text
