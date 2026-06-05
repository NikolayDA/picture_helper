from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_security_scan_workflow_is_scheduled_and_isolates_issue_token() -> None:
    workflow = (ROOT / ".github/workflows/codex-security-scan.yml").read_text(
        encoding="utf-8"
    )

    assert "cron: '23 4 * * 1'" in workflow
    assert "SCAN_ANCHOR_DATE: '2026-06-08'" in workflow
    assert "openai/codex-action@v1" in workflow
    assert "output-schema-file: .github/codex/security-findings.schema.json" in workflow
    assert "sandbox: read-only" in workflow
    assert "safety-strategy: read-only" in workflow
    assert "persist-credentials: false" in workflow

    scan_job = workflow.split("  scan:", 1)[1].split("  create-issues:", 1)[0]
    issue_job = workflow.split("  create-issues:", 1)[1]
    assert "issues: write" not in scan_job
    assert "issues: write" in issue_job


def test_security_scan_prompt_requires_structured_reportable_findings() -> None:
    prompt = (ROOT / ".github/codex/security-scan-prompt.md").read_text(encoding="utf-8")

    assert "Return only JSON" in prompt
    assert "Do not modify files" in prompt
    assert "empty `findings` array" in prompt
    assert "stable `dedupe_key`" in prompt


def test_security_findings_schema_requires_dedupe_key_and_locations() -> None:
    schema = json.loads(
        (ROOT / ".github/codex/security-findings.schema.json").read_text(
            encoding="utf-8"
        )
    )
    required = set(schema["properties"]["findings"]["items"]["required"])

    assert {"dedupe_key", "reportable", "affected_locations", "remediation"} <= required


def test_security_issue_script_dry_run_outputs_dedupe_marker(tmp_path: Path) -> None:
    findings = {
        "scan_summary": {
            "scope": "test",
            "method": "unit",
            "limitations": "none",
        },
        "findings": [
            {
                "title": "Example issue",
                "severity": "low",
                "confidence": "high",
                "category": "Test category",
                "cwe": ["CWE-200"],
                "dedupe_key": "tests/example.py:12:test-category",
                "reportable": True,
                "summary": "Example summary",
                "impact": "Example impact",
                "evidence": ["Example evidence"],
                "affected_locations": [
                    {"path": "tests/example.py", "start_line": 12, "end_line": 13}
                ],
                "remediation": ["Example remediation"],
                "notes": "Example note",
            }
        ],
    }
    path = tmp_path / "findings.json"
    path.write_text(json.dumps(findings), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/create_security_scan_issues.py"),
            str(path),
            "--dry-run",
            "--results",
            str(tmp_path / "results.json"),
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "Would create or reuse issue for: Example issue" in result.stdout
    assert "<!-- codex-security-scan:" in result.stdout
