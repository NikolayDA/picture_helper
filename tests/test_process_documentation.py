"""Drift-Schutz zwischen Prozessdokumentation und versionierten Workflows."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def test_required_status_name_matches_pr_ci_job() -> None:
    """Der dokumentierte Pflichtstatus muss der exakte PR-CI-Jobname bleiben."""
    workflow = (_ROOT / ".github/workflows/pr-ci.yml").read_text(encoding="utf-8")
    snapshot = (_ROOT / "docs/PROZESSE_UML.md").read_text(encoding="utf-8")

    assert "name: Lightweight PR checks" in workflow
    assert (
        "| Branch Protection für `main` | einziger erforderlicher Status: "
        "`Lightweight PR checks`;" in snapshot
    )
