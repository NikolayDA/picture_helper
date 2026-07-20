"""Guards for the self-hosted release acceptance workflow (#641)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "release-abnahme.yml"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_exists() -> None:
    assert WORKFLOW.is_file(), "release-abnahme.yml fehlt"


def test_workflow_is_dispatch_only() -> None:
    """Nur workflow_dispatch – nie Push/PR/Fork auf Self-hosted Runnern."""
    text = _workflow_text()

    assert "workflow_dispatch:" in text
    # Keine automatischen Trigger, die fremden Code auf die Runner brächten.
    for forbidden in ("\n  push:", "\n  pull_request:", "pull_request_target"):
        assert forbidden not in text, f"unerlaubter Trigger: {forbidden!r}"


def test_workflow_is_least_privilege() -> None:
    """Nur Lese-Scopes; kein Schreibrecht im Smoke-Gerüst (#641)."""
    text = _workflow_text()

    assert "permissions:" in text
    assert "contents: read" in text
    assert "actions: read" in text
    # Schreib-Scopes gehören erst in den Aggregations-Job (#646), nicht hierher.
    assert "contents: write" not in text
    assert "issues: write" not in text
    assert "pull-requests: write" not in text


def test_workflow_uploads_evidence_per_platform() -> None:
    """Jeder aktive Plattform-Job lädt sein Evidenz-Artefakt hoch."""
    text = _workflow_text()

    assert "name: abnahme-macos-arm64" in text
    assert "name: abnahme-linux-arm64" in text
    # Genau ein Artefakt-Upload je aktivem Plattform-Job (macOS, linux-arm64,
    # linux-x86_64) – der Hinweis-Job lädt nichts hoch.
    assert text.count("actions/upload-artifact") == 3


def test_workflow_gates_and_surfaces_paused_x86_64() -> None:
    """x86_64 ist per Variable gegated und meldet die Pause sichtbar."""
    text = _workflow_text()

    # Job existiert, ist aber über die Repository-Variable deaktiviert.
    assert "abnahme-linux-x86_64:" in text
    assert "vars.ABNAHME_X86_64_ENABLED == 'true'" in text
    # Gegenstück: sichtbarer Hinweis statt stillem Wegfall.
    assert "vars.ABNAHME_X86_64_ENABLED != 'true'" in text
    assert "::notice" in text
    assert "RELEASE_AUTOMATION.md" in text


def test_workflow_runs_evidence_helper() -> None:
    """Die Plattform-Jobs rufen den Evidenz-Helfer auf."""
    text = _workflow_text()

    assert "scripts/release_abnahme.py" in text
    assert (ROOT / "scripts" / "release_abnahme.py").is_file()
