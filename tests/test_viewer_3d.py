"""Tests des 3D-Viewer-Containers und der Fallback-Zustände (#593, Epic #582).

Der Zustandsautomat (Empty/Unavailable/Loading/Error/Ready) und der Decimation-
Badge sind ohne GL-Kontext prüfbar; der GL-Viewer selbst rendert im
Offscreen-CI nicht (echter Fallbackpfad), seine Konstruktion/Fehlerbehandlung
propagiert aber nie eine Exception.
"""
from __future__ import annotations

import numpy as np
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

from bgremover.height_map import HEIGHT_MAX_16BIT, HeightField
from bgremover.relief_mesh import MeshQuality, build_relief_mesh
from bgremover.viewer_3d import GLReliefViewer, Relief3DView

pytestmark = pytest.mark.ui_smoke


def _mesh(size: int = 24) -> object:
    field = HeightField(
        np.full((size, size), 5000, np.uint16),
        np.full((size, size), 255, np.uint8),
        HEIGHT_MAX_16BIT,
    )
    return build_relief_mesh(field, MeshQuality.REDUCED)


def _large_mesh() -> object:
    field = HeightField(
        np.zeros((2000, 2000), np.uint16),
        np.full((2000, 2000), 255, np.uint8),
        HEIGHT_MAX_16BIT,
    )
    return build_relief_mesh(field, MeshQuality.STANDARD)


def test_state_machine_transitions(qapp) -> None:
    view = Relief3DView()
    assert view.state == "empty"
    view.show_unavailable()
    assert view.state == "unavailable"
    view.show_loading()
    assert view.state == "loading"
    view.show_error()
    assert view.state == "error"
    view.show_empty()
    assert view.state == "empty"


def test_show_mesh_reaches_ready_or_error(qapp) -> None:
    view = Relief3DView()
    view.show_mesh(_mesh())
    # Ready (Viewer konstruiert) oder Error (kein GL) – nie eine Exception.
    assert view.state in ("ready", "error")


def test_failed_viewer_is_recreated_on_retry(qapp) -> None:
    view = Relief3DView()
    view.show_mesh(_mesh())
    viewer = view.viewer()
    if viewer is None:
        pytest.skip("Kein GL-Viewer-Widget verfügbar")
    # GL-Fehler simulieren: der Viewer ist nicht mehr renderfähig.
    viewer._failed = True
    view.show_mesh(_mesh())
    new_viewer = view.viewer()
    # Der fehlgeschlagene Viewer wurde verworfen und ein frischer aufgebaut.
    assert new_viewer is not None
    assert new_viewer is not viewer
    assert not new_viewer.has_failed


def test_decimation_badge_reflects_factor(qapp) -> None:
    view = Relief3DView()
    view.show_mesh(_large_mesh())
    if view.state == "ready":
        assert "1:" in view._badge.text()


def test_show2d_and_retry_signals_fire(qapp) -> None:
    view = Relief3DView()
    fired: list[str] = []
    view.show2DRequested.connect(lambda: fired.append("2d"))
    view.retryRequested.connect(lambda: fired.append("retry"))
    view.show2DRequested.emit()
    view.retryRequested.emit()
    assert fired == ["2d", "retry"]


def test_gl_viewer_construction_and_params_do_not_raise(qapp) -> None:
    viewer = GLReliefViewer()
    viewer.set_mesh(_mesh())
    viewer.set_exaggeration(3.0)
    viewer.set_light(120.0, 60.0)
    viewer.fit_view()
    viewer.reset_view()
    viewer.cleanup_gl()  # doppelte Freigabe muss ebenfalls sicher sein
    viewer.cleanup_gl()


def test_shift_home_requests_central_reset(qapp) -> None:
    viewer = GLReliefViewer()
    requested: list[bool] = []
    viewer.resetRequested.connect(lambda: requested.append(True))

    viewer.keyPressEvent(QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_Home,
        Qt.KeyboardModifier.ShiftModifier,
    ))

    assert requested == [True]


def test_gl_viewer_reports_init_failure_without_propagating(qapp) -> None:
    viewer = GLReliefViewer()
    failures: list[str] = []
    viewer.initFailed.connect(failures.append)
    # initializeGL ist gekapselt: ohne echten GL-Kontext schlägt es fehl,
    # propagiert aber nie – es meldet höchstens initFailed.
    viewer.initializeGL()
    assert viewer.has_failed or not failures  # kein Crash, definierter Zustand


def test_context_loss_requeues_cpu_mesh_for_upload(qapp) -> None:
    """ADR #591: Ein neuer GL-Kontext lädt die gehaltene CPU-Kopie erneut."""
    viewer = GLReliefViewer()
    mesh = _mesh()
    viewer.set_mesh(mesh)
    viewer._pending_mesh = None  # simuliert: bereits in den alten Kontext geladen
    viewer._gl_ready = True

    viewer._on_context_about_to_be_destroyed()

    assert viewer._pending_mesh is mesh
    assert viewer._mesh is mesh
    assert not viewer._gl_ready
    assert viewer._index_count == 0


def test_accessible_names_present(qapp) -> None:
    viewer = GLReliefViewer()
    assert viewer.accessibleName()
    assert viewer.accessibleDescription()
