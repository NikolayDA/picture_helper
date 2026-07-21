"""Tests für den nativen 3D-Screenshot-Automationshook (#648).

Der Erfolgspfad braucht einen echten renderbaren GL-Kontext (``gl_smoke``,
überspringt sich offscreen); der Fallback-Pfad (kein GL ⇒ ``unavailable``)
läuft headless in jeder CI (``ui_smoke``) und deckt ab, dass der Hook nie
wirft und keinen Screenshot hinterlässt, wenn der 3D-Zweig nicht bereit wird.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

from bgremover import MainWindow
from bgremover.preview3d_capability import probe_3d_capability, reset_capability_cache
from bgremover.screenshot3d import run_native_3d_screenshot

pytestmark = pytest.mark.ui_smoke

_NON_RENDERABLE = {"offscreen", "minimal", "vnc"}


def test_headless_fallback_reports_unavailable_without_writing_file(
    qapp, qtbot, tmp_path: Path,
) -> None:  # type: ignore[no-untyped-def]
    """Offscreen erreicht den dokumentierten Fallback statt eines Fehlers."""
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    target = tmp_path / "native_preview3d_ready.png"
    try:
        result = run_native_3d_screenshot(win, target, timeout_ms=5_000)
    finally:
        win.close()

    assert result.ok is False
    assert result.state in {"unavailable", "error"}
    assert not target.exists()
    assert not target.with_name(target.name + ".json").exists()


@pytest.mark.gl_smoke
def test_native_gl_run_writes_png_and_provenance_sidecar(
    qapp, qtbot, tmp_path: Path,
) -> None:  # type: ignore[no-untyped-def]
    """Unter echtem GL entsteht ein Screenshot + Provenance-JSON (#648)."""
    app = QApplication.instance()
    assert app is not None
    if app.platformName() in _NON_RENDERABLE:
        pytest.skip(f"Plattform {app.platformName()!r} kann QOpenGLWidget nicht rendern")
    reset_capability_cache()
    if not probe_3d_capability(use_cache=False).ok:
        pytest.skip("Keine OpenGL-2.1-Capability in dieser Umgebung")

    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    target = tmp_path / "native_preview3d_ready.png"
    try:
        result = run_native_3d_screenshot(win, target, timeout_ms=30_000)
    finally:
        win.close()

    assert result.ok is True, result.message
    assert result.state == "ready"
    assert result.diagnostic.strip()
    assert target.is_file()

    sidecar = target.with_name(target.name + ".json")
    assert sidecar.is_file()
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["kind"] == "abnahme-native-3d-screenshot"
    assert payload["gl_provenance"] == result.diagnostic
