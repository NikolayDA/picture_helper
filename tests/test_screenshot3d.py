"""Tests für den nativen 3D-Screenshot-Automationshook (#648).

Der Erfolgspfad braucht einen echten renderbaren GL-Kontext (``gl_smoke``,
überspringt sich offscreen); der Fallback-Pfad (kein GL ⇒ ``unavailable``)
läuft headless in jeder CI (``ui_smoke``) und deckt ab, dass der Hook nie
wirft und keinen Screenshot hinterlässt, wenn der 3D-Zweig nicht bereit wird.

Die negativen Post-``ready``-Zweige (``viewer is None``, Frame-/Viewer-Fehler,
leere Geometrie, fehlende Provenance, Software-Renderer, ``grab().save()``-
Fehler) lassen sich ohne echten GL-Kontext nicht über ein reales
``MainWindow`` erreichen – sie werden isoliert über ein Fake-Fenster geprüft
(#659, O8), das nur die von ``run_native_3d_screenshot`` genutzte Oberfläche
nachbildet.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from PyQt6.QtWidgets import QApplication

from bgremover import MainWindow
from bgremover.preview3d_capability import probe_3d_capability, reset_capability_cache
from bgremover.screenshot3d import Screenshot3DResult, run_native_3d_screenshot

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


# ── Negative Post-ready-Zweige über ein Fake-Fenster (#659, O8) ──────────


class _FakeCanvas:
    def apply_loaded_image(self, image: Any, name: str) -> None:
        pass

    def fit_to_view(self) -> None:
        pass

    def generate_height_map(self) -> None:
        pass


class _FakeReliefView:
    def __init__(self, state: str = "ready", viewer: Any = None) -> None:
        self.state = state
        self._viewer = viewer

    def viewer(self) -> Any:
        return self._viewer


class _FakeViewer:
    def __init__(
        self,
        *,
        has_failed: bool = False,
        valid: bool = True,
        gl_ready: bool = True,
        mesh: Any = "mesh",
        pending_mesh: Any = None,
        index_count: int = 1,
    ) -> None:
        self.has_failed = has_failed
        self._valid = valid
        self._gl_ready = gl_ready
        self._mesh = mesh
        self._pending_mesh = pending_mesh
        self._index_count = index_count

    def isValid(self) -> bool:  # noqa: N802 (Qt-Namenskonvention gespiegelt)
        return self._valid


class _FakeCapability:
    def __init__(self, diagnostic: str) -> None:
        self.diagnostic = diagnostic


class _FakePreview3D:
    def __init__(self, diagnostic: str) -> None:
        self._diagnostic = diagnostic

    def _capability_probe(self) -> _FakeCapability:
        return _FakeCapability(self._diagnostic)


class _FakeGrab:
    def __init__(self, ok: bool) -> None:
        self._ok = ok

    def save(self, path: str) -> bool:
        return self._ok


class _FakeWindow:
    """Bildet nur die von ``run_native_3d_screenshot`` genutzte Oberfläche nach."""

    def __init__(
        self,
        relief_view: _FakeReliefView,
        *,
        diagnostic: str = "NVIDIA Corporation / NVIDIA GeForce RTX 3080 / 4.6.0",
        grab_ok: bool = True,
    ) -> None:
        self._canvas = _FakeCanvas()
        self._relief3d_view = relief_view
        self._preview3d = _FakePreview3D(diagnostic)
        self._grab_ok = grab_ok

    def _set_preview3d_mode(self, enabled: bool) -> None:
        pass

    def grab(self) -> _FakeGrab:
        return _FakeGrab(self._grab_ok)


def _run(window: _FakeWindow, tmp_path: Path, timeout_ms: int = 200) -> Screenshot3DResult:
    return run_native_3d_screenshot(
        window, tmp_path / "shot.png", timeout_ms=timeout_ms  # type: ignore[arg-type]
    )


def test_ready_state_without_viewer_reports_missing_viewer(qapp, tmp_path: Path) -> None:
    window = _FakeWindow(_FakeReliefView(state="ready", viewer=None))
    result = _run(window, tmp_path)
    assert result.ok is False
    assert result.state == "ready"
    assert "GL-Viewer" in result.message


def test_failed_viewer_reports_frame_failure(qapp, tmp_path: Path) -> None:
    viewer = _FakeViewer(has_failed=True)
    window = _FakeWindow(_FakeReliefView(state="ready", viewer=viewer))
    result = _run(window, tmp_path)
    assert result.ok is False
    assert "GL-Frame" in result.message


def test_frame_never_ready_times_out_as_frame_failure(qapp, tmp_path: Path) -> None:
    # gl_ready bleibt False: das Frame-Prädikat wird nie wahr, der Hook
    # wartet nur bis zum (kurzen) Timeout statt endlos zu blockieren.
    viewer = _FakeViewer(gl_ready=False)
    window = _FakeWindow(_FakeReliefView(state="ready", viewer=viewer))
    result = _run(window, tmp_path, timeout_ms=100)
    assert result.ok is False
    assert "GL-Frame" in result.message


def test_zero_index_count_reports_missing_geometry(qapp, tmp_path: Path) -> None:
    viewer = _FakeViewer(index_count=0)
    window = _FakeWindow(_FakeReliefView(state="ready", viewer=viewer))
    result = _run(window, tmp_path)
    assert result.ok is False
    assert "Geometrie" in result.message


def test_blank_diagnostic_reports_missing_provenance(qapp, tmp_path: Path) -> None:
    viewer = _FakeViewer()
    window = _FakeWindow(_FakeReliefView(state="ready", viewer=viewer), diagnostic="  ")
    result = _run(window, tmp_path)
    assert result.ok is False
    assert "Provenance" in result.message


def test_software_renderer_diagnostic_is_rejected(qapp, tmp_path: Path) -> None:
    viewer = _FakeViewer()
    window = _FakeWindow(
        _FakeReliefView(state="ready", viewer=viewer),
        diagnostic="Mesa / llvmpipe (LLVM 15) / 4.5",
    )
    result = _run(window, tmp_path)
    assert result.ok is False
    assert result.diagnostic == "Mesa / llvmpipe (LLVM 15) / 4.5"
    assert "Software-Renderer" in result.message


def test_grab_save_failure_is_reported_without_writing_sidecar(qapp, tmp_path: Path) -> None:
    viewer = _FakeViewer()
    window = _FakeWindow(_FakeReliefView(state="ready", viewer=viewer), grab_ok=False)
    target = tmp_path / "shot.png"
    result = run_native_3d_screenshot(window, target, timeout_ms=200)  # type: ignore[arg-type]
    assert result.ok is False
    assert "nicht speicherbar" in result.message
    assert not target.with_name(target.name + ".json").exists()
