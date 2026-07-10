"""Guards for the scheduled benchmark workflow."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "benchmark.yml"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_benchmark_workflow_opens_pr_instead_of_pushing_main() -> None:
    text = _workflow_text()

    assert "pull-requests: write" in text
    assert 'branch="ci/benchmark-results-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"' in text
    assert "git switch -c \"$branch\"" in text
    assert "git push --set-upstream origin \"$branch\"" in text
    assert "gh pr create" in text
    assert "git push\n" not in text
