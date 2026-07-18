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
