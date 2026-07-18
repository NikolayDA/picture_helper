"""Tests der Qt-freien Orbit-Kamera-Mathematik (#593, Epic #582).

Rein numerisch – kein Display-/Grafik-Kontext nötig.
"""
from __future__ import annotations

import numpy as np
import pytest

from bgremover.preview3d_camera import (
    DEFAULT_AZIMUTH,
    DEFAULT_ELEVATION,
    OrbitCamera,
    look_at,
    perspective,
)

_BOX_LO = np.array([-0.5, -0.5, 0.0])
_BOX_HI = np.array([0.5, 0.5, 0.1])


def _fit_camera() -> OrbitCamera:
    cam = OrbitCamera()
    cam.fit_bounds(_BOX_LO, _BOX_HI)
    return cam


def test_look_at_places_focus_on_negative_z_axis() -> None:
    view = look_at(np.array([0.0, 0.0, 5.0]), np.zeros(3), np.array([0.0, 1.0, 0.0]))
    focus = view @ np.array([0.0, 0.0, 0.0, 1.0])
    assert focus[2] == pytest.approx(-5.0)  # Fokus liegt vor der Kamera (−Z)


def test_perspective_maps_focus_to_ndc_center() -> None:
    cam = _fit_camera()
    proj = cam.projection_matrix(1.5)
    view = cam.view_matrix()
    clip = proj @ (view @ np.array([*cam.focus, 1.0]))
    ndc = clip[:3] / clip[3]
    assert ndc[0] == pytest.approx(0.0, abs=1e-6)
    assert ndc[1] == pytest.approx(0.0, abs=1e-6)


def test_fit_centers_focus_and_frames_bounds() -> None:
    cam = _fit_camera()
    assert np.allclose(cam.focus, (_BOX_LO + _BOX_HI) / 2)
    assert cam.distance > 0.0


def test_orbit_clamps_elevation() -> None:
    cam = _fit_camera()
    cam.orbit(0.0, 1000.0)
    assert cam.elevation <= 88.0
    cam.orbit(0.0, -1000.0)
    assert cam.elevation >= -88.0


def test_azimuth_wraps_modulo_360() -> None:
    cam = _fit_camera()
    cam.azimuth = 350.0
    cam.orbit(20.0, 0.0)
    assert 0.0 <= cam.azimuth < 360.0
    assert cam.azimuth == pytest.approx(10.0)


def test_zoom_clamps_distance_within_fit_bounds() -> None:
    cam = _fit_camera()
    for _ in range(60):
        cam.zoom(0.5)
    near = cam.distance
    for _ in range(60):
        cam.zoom(2.0)
    far = cam.distance
    assert near > 0.0
    assert far <= cam._fit_distance * 8.0 + 1e-9


def test_reset_restores_default_angles() -> None:
    cam = _fit_camera()
    cam.orbit(90.0, -40.0)
    cam.zoom(0.3)
    cam.reset(_BOX_LO, _BOX_HI)
    assert cam.azimuth == pytest.approx(DEFAULT_AZIMUTH % 360.0) or \
        cam.azimuth == pytest.approx(DEFAULT_AZIMUTH)
    assert cam.elevation == pytest.approx(DEFAULT_ELEVATION)


def test_pan_shifts_focus() -> None:
    cam = _fit_camera()
    before = cam.focus.copy()
    cam.pan(0.2, 0.0)
    assert not np.allclose(cam.focus, before)


def test_eye_is_finite_and_distanced_from_focus() -> None:
    cam = _fit_camera()
    eye = cam.eye()
    assert np.all(np.isfinite(eye))
    assert np.linalg.norm(eye - cam.focus) == pytest.approx(cam.distance)


def test_perspective_handles_degenerate_aspect() -> None:
    proj = perspective(45.0, 0.0, 0.1, 10.0)  # aspect 0 wird geklemmt
    assert np.all(np.isfinite(proj))
