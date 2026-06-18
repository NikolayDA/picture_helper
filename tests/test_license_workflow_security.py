"""Security invariants for the pull-request license workflow."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "license-check.yml"


def _yaml_block(text: str, key: str, indent: int) -> str:
    """Return one mapping block from the repository's simple workflow YAML."""
    lines = text.splitlines()
    marker = f"{' ' * indent}{key}:"
    start = lines.index(marker)
    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        current_indent = len(line) - len(line.lstrip())
        if current_indent <= indent:
            end = index
            break
    return "\n".join(lines[start:end])


def test_workflow_default_permissions_are_read_only() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    permissions = _yaml_block(text, "permissions", indent=0)

    assert "contents: read" in permissions
    assert "pull-requests: write" not in permissions


def test_license_job_runs_pr_code_without_write_credentials() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    job = _yaml_block(text, "license-check", indent=2)

    assert "permissions:" in job
    assert "contents: read" in job
    assert "pull-requests: write" not in job
    assert "persist-credentials: false" in job
    assert "python scripts/generate_license_report.py" in job


def test_comment_job_is_minimal_and_owns_the_only_pr_write_permission() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    comment_job = _yaml_block(text, "comment-summary", indent=2)

    assert text.count("pull-requests: write") == 1
    assert "needs: license-check" in comment_job
    assert "github.event_name == 'pull_request'" in comment_job
    assert "pull-requests: write" in comment_job
    assert "actions/download-artifact@v8" in comment_job
    assert "actions/github-script@v9" in comment_job
    assert "actions/checkout@" not in comment_job
    assert sum("uses:" in line for line in comment_job.splitlines()) == 2
    assert all(
        not line.lstrip().startswith("run:")
        for line in comment_job.splitlines()
    )
