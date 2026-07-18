"""Tests des 3D-Viewer-Containers und der Fallback-Zustände (#593, Epic #582).

Der Zustandsautomat (Empty/Unavailable/Loading/Error/Ready) und der Decimation-
Badge sind ohne GL-Kontext prüfbar; der GL-Viewer selbst rendert im
Offscreen-CI nicht (echter Fallbackpfad), seine Konstruktion/Fehlerbehandlung
propagiert aber nie eine Exception.
"""
from __future__ import annotations

import numpy as np
import pytest

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


def test_gl_viewer_reports_init_failure_without_propagating(qapp) -> None:
    viewer = GLReliefViewer()
    failures: list[str] = []
    viewer.initFailed.connect(failures.append)
    # initializeGL ist gekapselt: ohne echten GL-Kontext schlägt es fehl,
    # propagiert aber nie – es meldet höchstens initFailed.
    viewer.initializeGL()
    assert viewer.has_failed or not failures  # kein Crash, definierter Zustand


def test_accessible_names_present(qapp) -> None:
    viewer = GLReliefViewer()
    assert viewer.accessibleName()
    assert viewer.accessibleDescription()
