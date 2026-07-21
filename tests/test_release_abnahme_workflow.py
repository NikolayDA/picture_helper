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
    """Nur Lese-Scopes im Smoke-Gerüst; Schreibrechte nur im Aggregations-Job (#646)."""
    text = _workflow_text()

    assert "permissions:" in text
    assert "contents: read" in text
    assert "actions: read" in text
    # contents: write gibt es nirgends; pull-requests: write auch nicht.
    assert "contents: write" not in text
    assert "pull-requests: write" not in text
    # issues: write existiert genau einmal – ausschließlich im Aggregations-Job.
    assert text.count("issues: write") == 1


def test_aggregation_job_scoped_and_posts() -> None:
    """Der Aggregations-Job (#646) läuft nachgelagert, fail-safe, mit Kommentar."""
    text = _workflow_text()

    assert "aggregation:" in text
    assert (
        "needs: [abnahme-macos-arm64, abnahme-linux-arm64, "
        "abnahme-linux-x86_64]" in text
    )
    assert "if: always() && !inputs.dry_run" in text
    assert "scripts/abnahme_aggregate.py" in text
    assert "scripts/abnahme_vision_check.py" in text
    assert "gh issue comment 595" in text
    for script in ("abnahme_aggregate.py", "abnahme_vision_check.py"):
        assert (ROOT / "scripts" / script).is_file(), f"{script} fehlt"


def test_workflow_uploads_evidence_per_platform() -> None:
    """Jeder aktive Plattform-Job lädt sein Evidenz-Artefakt hoch."""
    text = _workflow_text()

    assert "name: abnahme-macos-arm64" in text
    assert "name: abnahme-linux-arm64" in text
    # Vier Uploads: je ein Evidenz-Artefakt der drei aktiven Plattform-Jobs
    # (macOS, linux-arm64, linux-x86_64) plus die Abschlussmatrix des
    # Aggregations-Jobs (#646); der Hinweis-Job lädt nichts hoch.
    assert text.count("actions/upload-artifact") == 4


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


def test_workflow_runs_hardware_smoke() -> None:
    """Die aktiven Plattform-Jobs führen den echten Hardware-Smoke aus (#642/#643)."""
    text = _workflow_text()

    assert "scripts/abnahme_smoke.py" in text
    assert "scripts/abnahme_scale_probe.py" in text  # Retina-Nachweis macOS
    for script in ("abnahme_smoke.py", "abnahme_scale_probe.py", "abnahme_probe.py"):
        assert (ROOT / "scripts" / script).is_file(), f"{script} fehlt"
    # Evidenz auch bei fehlgeschlagenem Smoke hochladen (Diagnose bleibt sichtbar).
    assert "if: always()" in text


def test_workflow_runs_native_e2e_and_persists_evidence() -> None:
    """Jeder Hardwarepfad verlangt 3D-ready und schreibt E2E-Evidenz (#644)."""
    text = _workflow_text()

    assert text.count("tests/test_e2e_release_regression.py") == 3
    assert text.count("ABNAHME_EVIDENCE_DIR:") == 3
    assert text.count("ABNAHME_PLATFORM:") == 3
    assert text.count("ABNAHME_REQUIRE_NATIVE_3D: '1'") == 3
    assert text.count('-e ".[test]" -c requirements/constraints.txt') == 3
    conftest = (ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert 'os.environ.get("ABNAHME_REQUIRE_NATIVE_3D") != "1"' in conftest


def test_workflow_installs_vision_sdk_in_dedicated_venv() -> None:
    """Vision läuft auf einem frischen Runner mit reproduzierbar gepinntem SDK."""
    text = _workflow_text()

    assert "abnahme-vision-venv" in text
    assert '"anthropic==0.117.0"' in text
    assert "continue-on-error: true" in text
    assert "vision_python=python3" in text
    assert '"$vision_python" scripts/abnahme_vision_check.py' in text


def test_workflow_tags_live_gl_results_with_platform() -> None:
    """Die Aggregation kann jedes Live-GL-Ergebnis eindeutig zuordnen."""
    text = _workflow_text()

    for platform in ("macos-arm64", "linux-arm64", "linux-x86_64"):
        assert f"--platform {platform}" in text
