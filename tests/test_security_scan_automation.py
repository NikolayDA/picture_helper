from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Das Skript via importlib laden (scripts/ ist kein Paket), Muster wie
# tests/test_benchmark.py. Der Modulname muss in sys.modules stehen, sonst
# scheitert die Typprüfung der frozen-dataclass unter
# ``from __future__ import annotations``.
_SPEC = importlib.util.spec_from_file_location(
    "create_security_scan_issues", ROOT / "scripts" / "create_security_scan_issues.py"
)
assert _SPEC is not None and _SPEC.loader is not None
scan_issues = importlib.util.module_from_spec(_SPEC)
sys.modules["create_security_scan_issues"] = scan_issues
_SPEC.loader.exec_module(scan_issues)


def _raw_finding(title: str, severity: str, *, reportable: bool = True) -> dict:
    """Minimal-aber-realistisches Roh-Finding für ``load_findings``."""
    return {
        "title": title,
        "severity": severity,
        "reportable": reportable,
        "dedupe_key": f"{title}:{severity}",
        "affected_locations": [{"path": "bgremover/x.py", "start_line": 1, "end_line": 2}],
    }


def _write_findings(tmp_path: Path, findings: list[dict]) -> Path:
    path = tmp_path / "findings.json"
    path.write_text(json.dumps({"findings": findings}), encoding="utf-8")
    return path


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


# ── #323: Filter-/Leerpfade von load_findings/main absichern ───────────────
# Netzunabhängig: github_request wird auf diesen Pfaden nie erreicht – die
# repo/token-Prüfung steckt erst in der Per-Finding-Schleife.

def test_load_findings_skips_non_reportable(tmp_path: Path) -> None:
    path = _write_findings(
        tmp_path,
        [
            _raw_finding("Keep me", "low", reportable=True),
            _raw_finding("Drop me", "high", reportable=False),
        ],
    )
    findings = scan_issues.load_findings(path, "low")
    # reportable:false wird übersprungen; der reportable-Kontroll-Finding bleibt,
    # damit der Test nicht versehentlich durch „alles weggefiltert" grünt.
    assert [f.title for f in findings] == ["Keep me"]


def test_load_findings_applies_severity_threshold(tmp_path: Path) -> None:
    path = _write_findings(
        tmp_path,
        [
            _raw_finding("Low finding", "low"),
            _raw_finding("Medium finding", "medium"),
            _raw_finding("High finding", "high"),
        ],
    )
    findings = scan_issues.load_findings(path, "medium")
    # Schwelle medium: low fällt raus, medium UND high bleiben übrig.
    assert sorted(f.title for f in findings) == ["High finding", "Medium finding"]


def test_main_writes_skipped_result_for_empty_findings(
    tmp_path: Path, monkeypatch
) -> None:
    findings_path = _write_findings(tmp_path, [])
    results_path = tmp_path / "results.json"
    # Deterministisch und ohne Seiteneffekte: Default-Schwelle, kein
    # Step-Summary-Schreibvorgang in eine CI-Datei.
    monkeypatch.delenv("SECURITY_SCAN_MIN_SEVERITY", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "create_security_scan_issues.py",
            str(findings_path),
            "--results",
            str(results_path),
        ],
    )

    assert scan_issues.main() == 0

    results = json.loads(results_path.read_text(encoding="utf-8"))
    assert results == [
        {"title": "No reportable findings", "status": "skipped", "url": ""}
    ]


# ── #324: Repo-Scope des Codex-Scan-Prompts mechanisch absichern ───────────

def test_security_scan_prompt_covers_repo_scope_anchors() -> None:
    """Erzwingt, dass der Codex-Scan-Prompt die zentralen Top-Level-Security-
    Flächen dieses Repos benennt – fällt eine still heraus, bricht CI. Ergänzt
    (lockert nicht) die strukturellen Reportability-/JSON-Assertions oben.

    Drift-Disziplin (analog zur Qt-Paketliste, Befund N6): Eine *bewusste*
    Scope-Änderung muss BEIDE Stellen anpassen – den Prompt
    (`.github/codex/security-scan-prompt.md`) UND diese Ankerliste. So bleibt
    der Repo-Bezug des Scans erzwingbar, statt als reines Review-Ticket zu
    verrotten.
    """
    prompt = (
        (ROOT / ".github/codex/security-scan-prompt.md")
        .read_text(encoding="utf-8")
        .lower()
    )

    required_anchors = [
        "bgremover/",
        "save/export",
        "worker",
        "support logs",
        "qt plugin",
        "dependency",
        "packaging",
        "release/ci",
    ]
    missing = [anchor for anchor in required_anchors if anchor not in prompt]
    assert not missing, f"Prompt fehlt Repo-Scope-Anker: {missing}"
