"""CI-Smoke-Check für ``scripts/generate_app_screenshots.py`` (Issue #500).

Das Skript war nach der Umstellung auf den geführten Workflow still
gebrochen (es suchte das entfernte ``QTabWidget`` der alten Tab-Spalte) –
ohne Testabdeckung fiel das erst bei der nächsten manuellen Nutzung auf.
Dieser Smoke-Check lässt den Generator vollständig (offscreen) in ein
Temp-Verzeichnis laufen und schlägt fehl, sobald er erneut bricht.

Bewusst ohne ``ui``-Marker (wie ``test_app_smoke``): Der Lauf ist ein
eigenständiger Subprozess ohne qtbot und läuft damit in der normalen CI
mit – genau dort wäre der Redesign-Bruch (#500) aufgefallen.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Ein Screenshot je Workflow-Schritt (Spec §6: sechs Schritte) plus die vom
# Generator zugesicherten Sammel-Artefakte.
_EXPECTED_ARTIFACTS = [
    "10_step_1_open.png",
    "11_step_2_cutout.png",
    "12_step_3_adjust.png",
    "13_step_4_shape.png",
    "14_step_5_relief.png",
    "15_step_6_export.png",
    "00_contact_sheet.png",
    "manifest.md",
]


def test_generate_app_screenshots_covers_all_workflow_steps(tmp_path):
    """Der Generator läuft fehlerfrei durch und liefert alle sechs Schritte."""
    out = tmp_path / "shots"
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_app_screenshots.py"),
         "--output-dir", str(out)],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=600,
    )
    assert r.returncode == 0, (
        f"generate_app_screenshots.py endete mit {r.returncode}\n"
        f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
    )
    missing = [name for name in _EXPECTED_ARTIFACTS if not (out / name).is_file()]
    assert not missing, f"Erwartete Screenshot-Artefakte fehlen: {missing}"
