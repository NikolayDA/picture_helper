"""Integrationstest der 3D-Vorschau im MainWindow-Workflow (#594, Epic #582).

Prüft Gating, Moduswechsel (Canvas-Stack) und die Nicht-Mutation des Projekts
durch die 3D-Ansicht. Die Capability-Probe wird gemockt, damit der aktivierte
Pfad auch ohne echten GL-Kontext (Offscreen-CI) prüfbar ist.
"""
from __future__ import annotations

import numpy as np
import pytest
from PyQt6.QtCore import QSettings

import bgremover.main_window as mw
from bgremover.preview3d_capability import RendererCapability
from bgremover.project_model import LayerKind, LayerRole, Project
from bgremover.relief_mesh import MeshQuality
from bgremover.settings_schema import (
    PREVIEW3D_EXAGGERATION_KEY,
    PREVIEW3D_LIGHT_AZIMUTH_KEY,
    PREVIEW3D_LIGHT_ELEVATION_KEY,
    PREVIEW3D_QUALITY_KEY,
)

pytestmark = pytest.mark.ui_smoke


def _solid(w: int, h: int, rgba: tuple[int, int, int, int]):
    from PIL import Image
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :] = rgba
    return Image.fromarray(arr, "RGBA")


def _height_project(w: int = 16, h: int = 16) -> Project:
    project = Project(w, h)
    project.create_layer(_solid(w, h, (200, 0, 0, 255)), name="C", kind=LayerKind.COLOR)
    heights = np.tile(np.linspace(0, 255, w, dtype=np.uint8), (h, 1))
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, 0] = heights
    rgba[:, :, 3] = 255
    from PIL import Image
    project.create_layer(
        Image.fromarray(rgba, "RGBA"), name="H",
        kind=LayerKind.HEIGHT, role=LayerRole.HEIGHT_MAP,
    )
    return project


@pytest.fixture()
def window(qapp, tmp_path, monkeypatch):
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    monkeypatch.setattr(
        mw, "probe_3d_capability",
        lambda *a, **k: RendererCapability(ok=True, diagnostic="test"))
    w = mw.MainWindow()
    yield w
    w._preview3d.cleanup()
    w._worker_controller.shutdown_all()


def test_3d_available_only_with_height_layer(window) -> None:
    # Ohne Projekt: 3D-Segment gesperrt.
    assert not window._height_panel._btn_3d.isEnabled()
    window._canvas.set_project(_height_project())
    window._update_preview3d_availability()
    assert window._height_panel._btn_3d.isEnabled()


def test_toggle_switches_canvas_stack_and_menu(window) -> None:
    window._canvas.set_project(_height_project())
    window._update_preview3d_availability()
    window._set_preview3d_mode(True)
    assert window._preview3d_active
    assert window._canvas_stack.currentIndex() == 1
    action = window._preview3d_menu_action()
    assert action is not None and action.isChecked()
    window._set_preview3d_mode(False)
    assert not window._preview3d_active
    assert window._canvas_stack.currentIndex() == 0
    assert not action.isChecked()


def test_3d_mode_does_not_mutate_project(window) -> None:
    project = _height_project()
    window._canvas.set_project(project)
    window._update_preview3d_availability()
    before = window._canvas.content_revision
    export_before = np.array(window._canvas._render_export_image())
    window._set_preview3d_mode(True)
    window._preview3d.set_exaggeration(5.0)
    window._preview3d.set_light(120.0, 60.0)
    window._set_preview3d_mode(False)
    assert window._canvas.content_revision == before
    export_after = np.array(window._canvas._render_export_image())
    assert np.array_equal(export_before, export_after)


def test_leaving_relief_step_returns_to_2d(window) -> None:
    from bgremover.stepper import WorkflowStep
    window._canvas.set_project(_height_project())
    window._update_preview3d_availability()
    window._go_to_step(WorkflowStep.RELIEF)
    window._set_preview3d_mode(True)
    assert window._preview3d_active
    window._go_to_step(WorkflowStep.EXPORT)
    assert not window._preview3d_active
    assert window._canvas_stack.currentIndex() == 0


def test_activating_3d_from_other_step_routes_to_relief(window) -> None:
    # Review #620 (P2): 3D aus einem Nicht-Relief-Schritt (z. B. Ansicht-Menü)
    # navigiert zuerst in den Relief-Schritt statt Stepper/Panel stehen zu lassen.
    from bgremover.stepper import WorkflowStep
    window._canvas.set_project(_height_project())
    window._update_preview3d_availability()
    window._go_to_step(WorkflowStep.EXPORT)
    window._set_preview3d_mode(True)
    assert window._preview3d_active
    assert window._step is WorkflowStep.RELIEF
    assert window._canvas_stack.currentIndex() == 1


def test_capability_probe_is_lazy_until_first_3d_request(
    qapp, tmp_path, monkeypatch,
) -> None:
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path)
    )
    calls = 0

    def probe() -> RendererCapability:
        nonlocal calls
        calls += 1
        return RendererCapability(ok=True, diagnostic="test")

    monkeypatch.setattr(mw, "probe_3d_capability", probe)
    w = mw.MainWindow()
    try:
        assert calls == 0
        w._canvas.set_project(_height_project())
        w._update_preview3d_availability()
        assert calls == 0
        w._set_preview3d_mode(True)
        assert calls == 1
    finally:
        w._preview3d.cleanup()
        w._worker_controller.shutdown_all()


def test_persisted_3d_state_is_reflected_and_reset_consistently(
    qapp, tmp_path, monkeypatch,
) -> None:
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path)
    )
    settings = QSettings("BgRemover", "BgRemover")
    settings.setValue(PREVIEW3D_QUALITY_KEY, MeshQuality.HIGH.value)
    settings.setValue(PREVIEW3D_EXAGGERATION_KEY, 4.0)
    settings.setValue(PREVIEW3D_LIGHT_AZIMUTH_KEY, 120.0)
    settings.setValue(PREVIEW3D_LIGHT_ELEVATION_KEY, 60.0)
    settings.sync()
    monkeypatch.setattr(
        mw, "probe_3d_capability",
        lambda: RendererCapability(ok=True, diagnostic="test"),
    )

    w = mw.MainWindow()
    try:
        panel = w._height_panel
        assert w._preview3d.quality is MeshQuality.HIGH
        assert w._preview3d.exaggeration == pytest.approx(4.0)
        assert w._preview3d.light == pytest.approx((120.0, 60.0))
        assert panel._selected_quality is MeshQuality.HIGH
        assert panel._exagg_slider.value() == 80
        assert panel._azimuth_slider.value() == 120
        assert panel._elevation_slider.value() == 60

        # Ein Panel-Neuaufbau (z. B. Theme-Wechsel) darf nicht auf Standard driften.
        w._rebuild_right_panel()
        assert w._height_panel._selected_quality is MeshQuality.HIGH

        # Der Viewer-Shortcut wird an denselben zentralen Resetpfad weitergereicht.
        w._relief3d_view.resetRequested.emit()
        panel = w._height_panel
        assert w._preview3d.quality is MeshQuality.STANDARD
        assert w._preview3d.exaggeration == pytest.approx(1.0)
        assert w._preview3d.light == pytest.approx((315.0, 45.0))
        assert panel._selected_quality is MeshQuality.STANDARD
        assert panel._exagg_slider.value() == 50
        assert panel._azimuth_slider.value() == 315
        assert panel._elevation_slider.value() == 45
        assert settings.value(PREVIEW3D_QUALITY_KEY) == MeshQuality.STANDARD.value
        assert float(settings.value(PREVIEW3D_EXAGGERATION_KEY)) == pytest.approx(1.0)
        assert float(settings.value(PREVIEW3D_LIGHT_AZIMUTH_KEY)) == pytest.approx(315.0)
        assert float(settings.value(PREVIEW3D_LIGHT_ELEVATION_KEY)) == pytest.approx(45.0)
    finally:
        w._preview3d.cleanup()
        w._worker_controller.shutdown_all()
