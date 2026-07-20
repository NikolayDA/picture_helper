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


def test_native_qt_platform_preserves_explicit_linux_platform(monkeypatch):
    """Native 3D capture must not erase an explicit Wayland/X11 selection."""
    from scripts import generate_app_screenshots as screenshots

    monkeypatch.setattr(screenshots.sys, "platform", "linux")
    monkeypatch.setenv("QT_QPA_PLATFORM", "wayland")

    screenshots._configure_qt_platform("native")

    assert os.environ["QT_QPA_PLATFORM"] == "wayland"


def test_native_qt_platform_clears_inherited_headless_platform(monkeypatch):
    """Native 3D capture may clear inherited headless values before probing GL."""
    from scripts import generate_app_screenshots as screenshots

    monkeypatch.setattr(screenshots.sys, "platform", "linux")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    screenshots._configure_qt_platform("native")

    assert "QT_QPA_PLATFORM" not in os.environ


def test_native_qt_platform_clears_headless_first_fallback_list(monkeypatch):
    """Qt fallback lists should not keep a headless-first native capture."""
    from scripts import generate_app_screenshots as screenshots

    monkeypatch.setattr(screenshots.sys, "platform", "linux")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen;xcb")

    screenshots._configure_qt_platform("native")

    assert "QT_QPA_PLATFORM" not in os.environ


def test_native_qt_platform_preserves_native_first_fallback_list(monkeypatch):
    """Native-first fallback lists remain explicit caller choices."""
    from scripts import generate_app_screenshots as screenshots

    monkeypatch.setattr(screenshots.sys, "platform", "linux")
    monkeypatch.setenv("QT_QPA_PLATFORM", "wayland;offscreen")

    screenshots._configure_qt_platform("native")

    assert os.environ["QT_QPA_PLATFORM"] == "wayland;offscreen"


def test_live_3d_acceptance_rejects_known_software_renderers():
    """Native Qt alone is insufficient evidence when GL still uses the CPU."""
    from scripts import generate_app_screenshots as screenshots

    assert screenshots._is_software_renderer("Mesa / llvmpipe (LLVM 18.1.8, 256 bits) / 4.5")
    assert screenshots._is_software_renderer(
        "Google Inc. / ANGLE (SwiftShader Device) / OpenGL 4.1"
    )
    assert not screenshots._is_software_renderer("Apple / Apple M3 Max / 4.1 Metal - 89.3")


def test_live_3d_manifest_records_renderer_provenance(tmp_path):
    """Accepted live screenshots must name environment and renderer explicitly."""
    from scripts import generate_app_screenshots as screenshots

    provenance = screenshots.Live3DProvenance(
        captured_at="2026-07-20T16:30:00+02:00",
        qt_platform="cocoa",
        host="Darwin 25.5.0 (arm64)",
        renderer="Apple / Apple M3 Max / 4.1 Metal - 89.3",
    )
    screenshots._write_manifest(
        tmp_path,
        [
            (
                "77b_function_preview3d_controls.png",
                "Funktion: 3D-Reliefvorschau mit vollstaendigen Controls",
                2640,
                1640,
            )
        ],
        live_3d_provenance=provenance,
    )

    manifest = (tmp_path / "manifest.md").read_text(encoding="utf-8")
    assert "## 3D-Renderer-Provenienz" in manifest
    assert "Qt-Plattform: `cocoa`" in manifest
    assert "Betriebssystem/Architektur: `Darwin 25.5.0 (arm64)`" in manifest
    assert "Apple / Apple M3 Max / 4.1 Metal - 89.3" in manifest


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
