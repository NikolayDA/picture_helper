"""Offscreen-3D-Render-Smoke (#593, ADR #591).

Rendert ein kleines Mesh in einen echten GL-Kontext und prüft **strukturelle
Invarianten** (kein Schwarzbild, kein Viewer-Fehler) statt Golden-Pixeln –
treibertolerant. Ohne renderbaren FBO (Plattform ``offscreen``/``minimal`` oder
fehlende OpenGL-Capability) überspringt sich der Test sauber; er läuft real unter
einem echten Windowing-Backend (xcb/Wayland/Cocoa) plus llvmpipe/GPU.
"""
from __future__ import annotations

import numpy as np
import pytest
from PyQt6.QtWidgets import QApplication

from bgremover.height_map import HEIGHT_MAX_16BIT, HeightField
from bgremover.preview3d_capability import probe_3d_capability, reset_capability_cache
from bgremover.relief_mesh import MeshQuality, build_relief_mesh
from bgremover.viewer_3d import GLReliefViewer

pytestmark = pytest.mark.gl_smoke

# QPA-Plattformen ohne QOpenGLWidget-FBO – dort ist kein echtes Rendern möglich.
_NON_RENDERABLE = {"offscreen", "minimal", "vnc"}


def _require_renderable(qapp) -> None:
    app = QApplication.instance()
    assert app is not None
    if app.platformName() in _NON_RENDERABLE:
        pytest.skip(f"Plattform {app.platformName()!r} kann QOpenGLWidget nicht rendern")
    reset_capability_cache()
    if not probe_3d_capability(use_cache=False).ok:
        pytest.skip("Keine OpenGL-2.1-Capability in dieser Umgebung")


def _ramp_mesh():
    ramp = np.tile(np.linspace(0, HEIGHT_MAX_16BIT, 64, dtype=np.uint16), (64, 1))
    field = HeightField(ramp, np.full((64, 64), 255, np.uint8), HEIGHT_MAX_16BIT)
    return build_relief_mesh(field, MeshQuality.REDUCED)


def _mean_brightness(image) -> float:
    total = 0.0
    count = 0
    for y in range(0, image.height(), 8):
        for x in range(0, image.width(), 8):
            c = image.pixelColor(x, y)
            total += (c.red() + c.green() + c.blue()) / 3.0
            count += 1
    return total / max(1, count)


def test_render_produces_nonblack_frame_without_failure(qapp) -> None:
    _require_renderable(qapp)
    viewer = GLReliefViewer()
    viewer.resize(240, 200)
    viewer.set_mesh(_ramp_mesh())
    viewer.set_exaggeration(4.0)
    viewer.show()
    QApplication.processEvents()
    image = viewer.grab().toImage()
    QApplication.processEvents()
    assert not viewer.has_failed
    assert _mean_brightness(image) > 5.0  # etwas wurde gerendert (kein Schwarzbild)
    viewer.cleanup_gl()
