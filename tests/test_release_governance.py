"""Regression contracts for the canonical release documentation (#737/#745/#746)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
RUNBOOK = (ROOT / "docs" / "RELEASE_PROCESS.md").read_text(encoding="utf-8")
CHECKLIST = (ROOT / "docs" / "RELEASE_ACCEPTANCE_CHECKLIST.md").read_text(encoding="utf-8")


def test_claude_has_sources_instead_of_manual_release_state() -> None:
    assert "Letzter **veröffentlichter** Release" not in CLAUDE
    assert not re.search(r"(?i)aktueller\s+versionsschnitt.{0,80}\d+\.\d+\.\d+", CLAUDE)
    assert not re.search(r"(?i)(?:letzter\s+release-stand|aktuell)\D{0,30}v?\d+\.\d+\.\d+", CLAUDE)
    assert "project.version" in CLAUDE
    assert "docs/RELEASE_PROCESS.md" in CLAUDE
    assert "docs/RELEASE_ACCEPTANCE_CHECKLIST.md" in CLAUDE
    assert "github.com/NikolayDA/picture_helper/releases" in CLAUDE


def test_runbook_has_nine_complete_steps_and_operational_paths() -> None:
    steps = re.split(r"(?m)^### [1-9]\. ", RUNBOOK)[1:]
    assert len(steps) == 9
    for step in steps:
        for field in (
            "**Trigger:**",
            "**Owner:**",
            "**Input:**",
            "**Output/Evidenz:**",
            "**Erwartetes Ergebnis:**",
            "**Fehler/Wiederanlauf:**",
        ):
            assert field in step
    for required in (
        "## Hotfix-Pfad",
        "## Rollback, Yank und Teilzustände",
        "## Wiederanlaufmatrix",
        "## Eskalation und Waiver",
        "RELEASE_ACCEPTANCE_CHECKLIST.md",
        "ADR-2026-release-manifest-publish.md",
        "PUBLIC-DOWNLOAD-01",
        "UPDATE-01",
    ):
        assert required in RUNBOOK


def test_runbook_names_all_release_workflows_and_dispatch_inputs() -> None:
    for workflow in ("release-linux.yml", "release-abnahme.yml", "release-publish.yml"):
        assert workflow in RUNBOOK
    for input_name in (
        "with_ai",
        "run_id",
        "platforms",
        "dry_run",
        "target_issue",
        "tag",
        "candidate_run_id",
        "acceptance_run_id",
        "approval_artifact_name",
    ):
        assert re.search(rf"(?:-f |`){input_name}(?:=|`)", RUNBOOK), input_name


def test_secondary_docs_only_point_to_canonical_release_sources() -> None:
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    automation = (ROOT / "docs" / "RELEASE_AUTOMATION.md").read_text(encoding="utf-8")
    packaging = (ROOT / "docs" / "PACKAGING_SMOKE.md").read_text(encoding="utf-8")
    for text in (contributing, automation, packaging):
        assert "RELEASE_PROCESS.md" in text
        assert "RELEASE_ACCEPTANCE_CHECKLIST.md" in text
    assert "attaches it to the GitHub Release on every `v*` tag" not in (
        ROOT / "packaging" / "mac" / "README.md"
    ).read_text(encoding="utf-8")


def test_workflows_create_and_verify_pinned_release_instance() -> None:
    acceptance = (ROOT / ".github" / "workflows" / "release-abnahme.yml").read_text(
        encoding="utf-8"
    )
    publish = (ROOT / ".github" / "workflows" / "release-publish.yml").read_text(encoding="utf-8")
    assert '--checklist "docs/RELEASE_ACCEPTANCE_CHECKLIST.md"' in acceptance
    assert "extract-instance" in acceptance
    assert '--checklist "candidate-source/docs/RELEASE_ACCEPTANCE_CHECKLIST.md"' in publish
    assert "release-checklist-json:start" in CHECKLIST
    assert "release-checklist-json:end" in CHECKLIST
