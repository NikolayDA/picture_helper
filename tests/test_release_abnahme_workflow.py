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
        "needs: [candidate-source, abnahme-macos-arm64, abnahme-linux-arm64, "
        "abnahme-linux-x86_64]" in text
    )
    assert "if: always() && !inputs.dry_run" in text
    assert "scripts/abnahme_aggregate.py" in text
    assert "scripts/abnahme_vision_check.py" in text
    assert "target_issue:" in text
    assert "default: '595'" in text
    assert "TARGET_ISSUE: ${{ inputs.target_issue }}" in text
    assert 'gh issue comment "$TARGET_ISSUE"' in text
    assert "target_issue muss eine positive Issue-Nummer sein" in text
    for script in ("abnahme_aggregate.py", "abnahme_vision_check.py"):
        assert (ROOT / "scripts" / script).is_file(), f"{script} fehlt"


def test_workflow_uploads_evidence_per_platform() -> None:
    """Jeder aktive Plattform-Job lädt sein Evidenz-Artefakt hoch."""
    text = _workflow_text()

    assert "name: abnahme-macos-arm64" in text
    assert "name: abnahme-linux-arm64" in text
    # Sieben Uploads: drei Plattform-Evidenzen, Kandidatenvertrag,
    # Vision-Verdikte (#781), Abschlussmatrix und unveränderliches
    # Freigabemanifest (#744).
    assert text.count("actions/upload-artifact") == 7


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


def test_workflow_binds_acceptance_to_candidate_run_and_head() -> None:
    """#744: Run-Metadaten, Workflow, Commit und fünf Dateien werden vor
    den Hardware-Jobs als gemeinsamer Kandidatenvertrag geprüft."""
    text = _workflow_text()
    assert "candidate-source:" in text
    assert "scripts/release_contract.py prepare-candidate" in text
    assert "SOURCE_RUN_ID: ${{ inputs.run_id }}" in text
    assert '--run-id "$SOURCE_RUN_ID"' in text
    assert '--run-id "${{ inputs.run_id }}"' not in text
    assert "SOURCE_HEAD_SHA: ${{ needs.candidate-source.outputs.head_sha }}" in text
    # Drei Plattform-Evidenzabrufe plus der optionale Vorgänger-Abruf für den
    # echten UPDATE-01-Nachweis (#748) binden sich alle an denselben Commit.
    assert text.count('--commit-sha "$SOURCE_HEAD_SHA"') == 4
    assert "inputs.release_tag" not in text


def test_workflow_emits_immutable_approval_manifest() -> None:
    text = _workflow_text()
    assert "scripts/release_contract.py create-approval" in text
    assert "release-approval-manifest-${{ github.run_attempt }}" in text
    assert "release-freeze-provenance.json" in text
    assert "--summary-output" in text
    assert text.count("retention-days: 90") == 7


def test_workflow_runs_hardware_smoke() -> None:
    """Die aktiven Plattform-Jobs führen den echten Hardware-Smoke aus (#642/#643)."""
    text = _workflow_text()

    assert "scripts/abnahme_smoke.py" in text
    assert "scripts/abnahme_scale_probe.py" in text  # Retina-Nachweis macOS
    for script in ("abnahme_smoke.py", "abnahme_scale_probe.py", "abnahme_probe.py"):
        assert (ROOT / "scripts" / script).is_file(), f"{script} fehlt"
    # Evidenz auch bei fehlgeschlagenem Smoke hochladen (Diagnose bleibt sichtbar).
    assert "if: always()" in text


def test_workflow_requires_graphical_runner_sessions() -> None:
    """Native Qt-/GL-Schritte dürfen nicht versehentlich offscreen laufen."""
    text = _workflow_text()

    assert text.count("name: Grafische Runner-Session pruefen") == 3
    assert "Runner-Benutzer $runner_user ist nicht der angemeldete Konsolenbenutzer" in text
    assert 'if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]' in text
    assert 'if [ -n "${WAYLAND_DISPLAY:-}" ] && [ -z "${XDG_RUNTIME_DIR:-}" ]' in text
    assert text.count("unset QT_QPA_PLATFORM") == 9


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
    assert text.count("--iterations 3") == 3


def test_workflow_supports_optional_update_check_predecessor() -> None:
    """UPDATE-01 (#748): ein optionaler Vorgänger-Tag löst den echten
    Update-Check-Nachweis auf Linux arm64 aus; leer lässt ihn PENDING statt
    ein ungeprüftes PASS zu fabrizieren."""
    text = _workflow_text()

    assert "predecessor_tag:" in text
    assert "default: ''" in text
    assert "if: inputs.predecessor_tag != ''" in text
    assert '--release-tag "$PREDECESSOR_TAG"' in text
    assert "--predecessor-evidence-dir" in text
    assert "--candidate-version" in text
    assert "CANDIDATE_VERSION: ${{ needs.candidate-source.outputs.version }}" in text
    # Beide Argumente gehören in dieselbe Argumentliste: ohne Sollversion
    # bricht der Smoke ab (der Nachweis verlangt UPDATE_AVAILABLE mit exakt
    # der neuen Zielversion, nicht „irgendein Update sichtbar").
    block = text.split("predecessor_args=(", 1)[1].split("\n            )", 1)[0]
    assert "--predecessor-evidence-dir" in block
    assert "--candidate-version" in block
    for script in ("release_abnahme.py", "abnahme_smoke.py", "update_probe_cli.py"):
        assert (ROOT / "scripts" / script).is_file(), f"{script} fehlt"
