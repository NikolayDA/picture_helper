"""Drift-Schutz zwischen Prozessdokumentation und versionierten Workflows."""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def test_required_status_name_matches_pr_ci_job() -> None:
    """Der dokumentierte Pflichtstatus muss der exakte PR-CI-Jobname bleiben."""
    workflow = (_ROOT / ".github/workflows/pr-ci.yml").read_text(encoding="utf-8")
    snapshot = (_ROOT / "docs/PROZESSE_UML.md").read_text(encoding="utf-8")

    job_block = re.search(
        r"(?ms)^  pr-check:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", workflow
    )
    assert job_block, "Job pr-check in pr-ci.yml nicht gefunden"
    job_name_match = re.search(
        r"(?m)^    name:\s*(?P<name>[^#\n]+?)\s*$", job_block.group("body")
    )
    assert job_name_match, "Jobname von pr-check in pr-ci.yml nicht gefunden"
    job_name = job_name_match.group("name")

    row = re.search(
        r"(?m)^\|\s*Branch Protection für `main`\s*\|(?P<body>.*?)\|\s*$",
        snapshot,
    )
    assert row, "Snapshot-Zeile für Branch Protection nicht gefunden"
    assert job_name == "Lightweight PR checks", (
        "Der versionierte PR-CI-Jobname weicht vom live geprüften Pflichtstatus ab: "
        f"{job_name!r}"
    )
    assert f"`{job_name}`" in row.group("body"), (
        "Der PR-CI-Jobname fehlt in der Branch-Protection-Snapshot-Zeile: "
        f"{job_name!r}"
    )
