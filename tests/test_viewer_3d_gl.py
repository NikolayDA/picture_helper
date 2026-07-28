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
from bgremover.viewer_3d import GLReliefViewer, gl_resource_stats, reset_gl_resource_stats

pytestmark = pytest.mark.gl_smoke

#: Zyklen des Langzeitnachweises unter echtem GL (#684 verlangt mindestens 100).
_STRESS_CYCLES = 110

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


def _ramp_mesh(size: int = 64):
    ramp = np.tile(np.linspace(0, HEIGHT_MAX_16BIT, size, dtype=np.uint16), (size, 1))
    field = HeightField(ramp, np.full((size, size), 255, np.uint8), HEIGHT_MAX_16BIT)
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


def test_repeated_uploads_do_not_accumulate_gl_objects(qapp) -> None:
    """Langzeitnachweis unter echtem GL: >100 Uploads lassen den Bestand konstant (#684).

    Dieselbe Messgröße wie in ``tests/test_viewer_3d_gl_lifecycle.py`` und
    ``scripts/gl_stress_probe.py`` – nur hier mit echten ``QOpenGLBuffer``/
    ``QOpenGLVertexArrayObject`` in einem echten Kontext. Der Test läuft
    ausschließlich dort, wo real gerendert werden kann (Hardware/llvmpipe), und
    ist damit der Brückenkopf zwischen CI-Aussage und Hardware-Abnahme.
    """
    _require_renderable(qapp)
    reset_gl_resource_stats()
    small, large = _ramp_mesh(), _ramp_mesh(256)
    viewer = GLReliefViewer()
    viewer.resize(240, 200)
    viewer.show()
    QApplication.processEvents()

    live_samples: list[int] = []
    for index in range(_STRESS_CYCLES):
        # Wechselnde Datengrößen: neuer Upload, kein bloßer Cache-Treffer.
        viewer.set_mesh(large if index % 2 else small)
        viewer.grab()
        QApplication.processEvents()
        live_samples.append(gl_resource_stats().live)

    assert not viewer.has_failed
    assert viewer.gl_object_count <= 4
    # Untergrenze, nicht nur Obergrenze (#711): ein echter GL-Lauf ohne
    # erfolgreichen Puffer-Upload wäre konstant 0 und damit formal „ohne
    # Wachstum" – er darf hier nicht als bestandener Nachweis durchgehen.
    assert viewer.gl_object_count >= 3
    assert min(live_samples[1:]) >= 3
    # Nach dem ersten Upload konstant – kein Zuwachs je Zyklus.
    assert set(live_samples[1:]) == {live_samples[1]}
    assert max(live_samples) <= 4

    viewer.cleanup_gl()
    QApplication.processEvents()

    assert gl_resource_stats().live == 0
