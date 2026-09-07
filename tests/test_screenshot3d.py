"""Tests für den nativen 3D-Screenshot-Automationshook (#648).

Der Erfolgspfad braucht einen echten **Hardware**-GL-Kontext (``gl_smoke``,
überspringt sich offscreen und seit #1013 auch unter einem Software-Renderer);
der Gegenpfad läuft headless in jeder CI (``ui_smoke``) und deckt ab, dass der
Hook nie wirft und keinen Screenshot hinterlässt, wenn kein gültiger Nachweis
entsteht – weder ohne Kontext (``unavailable``/``error``) noch unter llvmpipe,
wo der Viewer ``ready`` wird und erst die Provenance abgewiesen wird (#642).

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
from bgremover import screenshot3d as screenshot3d_module
from bgremover.preview3d_capability import (
    NON_RENDERABLE_PLATFORMS,
    probe_3d_capability,
    reset_capability_cache,
)
from bgremover.renderer_provenance import is_software_renderer
from bgremover.screenshot3d import (
    Preview3DControlsEvidence,
    Screenshot3DResult,
    ensure_preview3d_controls_visible,
    run_native_3d_screenshot,
)
from bgremover.stepper import WorkflowStep

pytestmark = pytest.mark.ui_smoke

# Geteilte Regel statt eigener Kopie (#1002): dieselbe Menge entscheidet das
# produktive 3D-Gating.
_NON_RENDERABLE = NON_RENDERABLE_PLATFORMS
_REQUIRED_CONTROLS = {
    "preview3d_azimuth",
    "preview3d_elevation",
    "preview3d_quality_standard",
}


def test_required_preview3d_controls_fit_together_in_scroll_viewport(
    qapp,
    qtbot,
) -> None:  # type: ignore[no-untyped-def]
    """Der reale Mindestgrößen-Dialog kann alle drei Pflichtregler zeigen."""
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    win._right_panel.set_step(WorkflowStep.RELIEF)
    win._height_panel.set_preview3d_active(True)
    qapp.processEvents()
    try:
        evidence = ensure_preview3d_controls_visible(win)
    finally:
        win.close()

    assert evidence.ok, evidence.message
    assert set(evidence.visible_controls) == _REQUIRED_CONTROLS


def test_without_hardware_gl_no_screenshot_and_no_silent_success(
    qapp,
    qtbot,
    tmp_path: Path,
    gl_capability,
) -> None:  # type: ignore[no-untyped-def]
    """Ohne **Hardware**-GL entsteht keine Datei – und kein stiller Erfolg.

    Zwei Umgebungen ohne gültigen Nachweis, ein Ergebnis: kein Kontext
    (``unavailable``/``error``) und der Software-Renderer, der bis ``ready``
    kommt und erst an der Provenance scheitert (#642). Die Abweisung selbst
    prüft ``test_software_renderer_diagnostic_is_rejected`` überall über das
    Fake-Fenster; ungeprüft war bis #1013 der **End-to-End-Weg** mit echtem
    ``MainWindow`` – ausgerechnet auf der Umgebung, auf der er greift: Unter
    ``xvfb``/llvmpipe übersprang sich dieser Test (Capability vorhanden) und
    der ``gl_smoke``-Test unten wurde rot, obwohl sich das Produkt korrekt
    verhielt. Der Erfolgsfall (``ready`` + Hardware) gehört dorthin, nicht
    hierher.
    """
    software = gl_capability.ok and is_software_renderer(gl_capability.diagnostic)
    if gl_capability.ok and not software:
        pytest.skip(
            "GL-Capability vorhanden (Hardware-Renderer) – der Erfolgsfall "
            "gehört zum gl_smoke-Test"
        )

    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    target = tmp_path / "native_preview3d_ready.png"
    try:
        # Der Software-Renderer läuft bis zur Provenance-Prüfung durch und
        # braucht dafür dieselbe Frist wie der Erfolgsfall; ohne Kontext
        # entscheidet die kurze Frist des Fallbacks.
        result = run_native_3d_screenshot(
            win, target, timeout_ms=30_000 if software else 5_000
        )
    finally:
        win.close()

    assert result.ok is False
    if software:
        # Erwartet wird die Provenienz-Abweisung nach ``ready``. Festgeschrieben
        # wird sie nicht: Die Capability-Probe ist notwendig, nicht hinreichend
        # (#1002), der Renderbeweis (#1004) kann vorher greifen. Das wäre
        # wieder eine fest kodierte Umgebungsannahme – genau der Befund #1013.
        if result.state == "ready":
            assert "Software-Renderer" in result.message
            assert is_software_renderer(result.diagnostic)
        else:
            assert result.state == "error"
            assert result.message.strip()
    else:
        assert result.state in {"unavailable", "error"}
    assert not target.exists()
    assert not target.with_name(target.name + ".json").exists()


@pytest.mark.gl_smoke
def test_native_gl_run_writes_png_and_provenance_sidecar(
    qapp,
    qtbot,
    tmp_path: Path,
) -> None:  # type: ignore[no-untyped-def]
    """Unter echtem GL entsteht ein Screenshot + Provenance-JSON (#648)."""
    app = QApplication.instance()
    assert app is not None
    if app.platformName() in _NON_RENDERABLE:
        pytest.skip(f"Plattform {app.platformName()!r} kann QOpenGLWidget nicht rendern")
    reset_capability_cache()
    capability = probe_3d_capability(use_cache=False)
    if not capability.ok:
        pytest.skip("Keine OpenGL-2.1-Capability in dieser Umgebung")
    # Dritte Weiche (#1013, Muster von ``benchmark.probe_live_gl``): Eine
    # renderfähige Sitzungsplattform heißt nicht Hardware. Unter llvmpipe
    # weist ``run_native_3d_screenshot`` die Provenienz zu Recht ab (#642) –
    # der Test darf daran nicht scheitern, sondern muss sichtbar aussetzen.
    # Dass die Abweisung selbst geprüft bleibt, trägt der Test oben.
    if is_software_renderer(capability.diagnostic):
        pytest.skip(f"Software-Renderer statt Hardware-GL: {capability.diagnostic}")

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
    assert payload["schema"] == 2
    assert payload["kind"] == "abnahme-native-3d-screenshot"
    assert payload["gl_provenance"] == result.diagnostic
    assert payload["preview3d_controls_visible"] is True
    assert set(payload["preview3d_visible_controls"]) == _REQUIRED_CONTROLS


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
        failure_reason: str = "",
    ) -> None:
        self.has_failed = has_failed
        self.failure_reason = failure_reason
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
        window,
        tmp_path / "shot.png",
        timeout_ms=timeout_ms,  # type: ignore[arg-type]
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


def test_a_failed_viewer_hands_its_own_reason_to_the_acceptance(
    qapp, tmp_path: Path
) -> None:
    """Der Grund muss durchkommen (#1004, Review PR #1005).

    Seit dem Renderbeweis kann auch „Qt hält keinen Widget-Framebuffer" hier
    landen. Ein blankes „GL-Frame fehlgeschlagen" ließe einen
    Wächter-Fehlalarm wie einen Renderfehler aussehen – und dieses Ergebnis
    trägt ein Abnahmekriterium.
    """
    viewer = _FakeViewer(
        has_failed=True,
        failure_reason="paintEvent: Qt hält keinen Widget-Framebuffer (3 …)",
    )
    window = _FakeWindow(_FakeReliefView(state="ready", viewer=viewer))
    result = _run(window, tmp_path)
    assert result.ok is False
    assert "Widget-Framebuffer" in result.message


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


def test_missing_right_panel_attrs_fail_closed_without_grab(qapp, tmp_path: Path) -> None:
    """Ohne prüfbare Controls darf kein scheinbar grüner Nachweis entstehen."""
    viewer = _FakeViewer()
    window = _FakeWindow(_FakeReliefView(state="ready", viewer=viewer), grab_ok=True)
    result = _run(window, tmp_path)
    assert result.ok is False
    assert "3D-Controls nicht nachweisbar" in result.message
    assert not (tmp_path / "shot.png").exists()


def test_grab_save_failure_is_reported_without_writing_sidecar(
    qapp,
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    viewer = _FakeViewer()
    window = _FakeWindow(_FakeReliefView(state="ready", viewer=viewer), grab_ok=False)
    monkeypatch.setattr(
        screenshot3d_module,
        "ensure_preview3d_controls_visible",
        lambda _window: Preview3DControlsEvidence(
            True, tuple(sorted(_REQUIRED_CONTROLS)), "vollständig sichtbar"
        ),
    )
    target = tmp_path / "shot.png"
    result = run_native_3d_screenshot(window, target, timeout_ms=200)  # type: ignore[arg-type]
    assert result.ok is False
    assert "nicht speicherbar" in result.message
    assert not target.with_name(target.name + ".json").exists()
