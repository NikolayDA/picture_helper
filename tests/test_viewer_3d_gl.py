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
from bgremover.preview3d_capability import (
    NON_RENDERABLE_PLATFORMS,
    probe_3d_capability,
    reset_capability_cache,
)
from bgremover.relief_mesh import MeshQuality, build_relief_mesh
from bgremover.viewer_3d import GLReliefViewer, gl_resource_stats, reset_gl_resource_stats

pytestmark = pytest.mark.gl_smoke

#: Zyklen des Langzeitnachweises unter echtem GL (#684 verlangt mindestens 100).
_STRESS_CYCLES = 110

#: Obergrenze für den ersten ``frameSwapped`` eines sichtbaren Viewers (#1015).
#: Auf dem Raspberry Pi 5 (Broadcom V3D) kommt er gemessen nach 72 ms
#: (``wayland``) bzw. 99 ms (``xcb``); 40 nackte ``processEvents``-Durchläufe
#: waren dort in wenigen Millisekunden abgearbeitet und der Test rot, obwohl der
#: Viewer gesund war. Die Schranke ist eine **Obergrenze**, kein Zeuge – der
#: positive Zeuge bleibt das Signal selbst.
_FRAME_TIMEOUT_MS = 2000

#: Beobachtungsfenster der Negativkontrolle. Maßgeblich ist nicht die
#: Frame-Latenz, sondern dass Qt einem verborgenen Widget überhaupt keinen
#: ``paintEvent`` zustellt – die Bewertung läuft dort nie an. Das Fenster ist
#: an ``_FRAME_TIMEOUT_MS`` gekoppelt, damit „nie abgestuft" nicht schwächer
#: belegt ist als das, was der Positivfall als Frame-Latenz zugesteht.
_NO_FRAME_WINDOW_MS = _FRAME_TIMEOUT_MS

# QPA-Plattformen ohne QOpenGLWidget-FBO – dort ist kein echtes Rendern möglich.
# Seit #1002 kommt die Menge aus dem Produktivpfad: Dieselbe Regel entscheidet
# das 3D-Gating, eine eigene Kopie hier könnte davon abdriften.
_NON_RENDERABLE = NON_RENDERABLE_PLATFORMS


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


# ── Renderbeweis unter echtem GL (#1004) ─────────────────────────────────

def test_a_visible_viewer_proves_its_frame(qapp, qtbot) -> None:
    """Der positive Zeuge kommt von Qt, nicht von einer Zeitschranke.

    Gemessen (``xvfb-run`` + ``xcb``, llvmpipe): ``frameSwapped`` feuert genau
    im gesunden sichtbaren Fall. Unter ``offscreen`` – wo ``QOpenGLWidget``
    laut Qt „not supported on this platform" ist – bleibt es aus, und Qt weist
    stattdessen die Paints ab. Dieser Test läuft nur dort, wo wirklich
    gerendert werden kann, und belegt die freisprechende Seite der Regel.

    Gewartet wird auf das Signal, nicht eine feste Zahl von Ereignisdurchläufen
    (#1015): Auf echter Hardware liegt der erste Frame-Tausch hinter dem
    Frame-Callback des Compositors bzw. des X-Servers, und eine Schleife ohne
    Wartezeit ist vorher durch. Die Zeitschranke begrenzt nur das Warten.
    """
    _require_renderable(qapp)
    viewer = GLReliefViewer()
    qtbot.addWidget(viewer)
    viewer.resize(240, 200)
    viewer.set_mesh(_ramp_mesh())
    with qtbot.waitSignal(viewer.frameSwapped, timeout=_FRAME_TIMEOUT_MS, raising=False) as swap:
        viewer.show()

    assert swap.signal_triggered, "kein frameSwapped trotz renderfähiger Plattform"
    assert viewer._has_rendered is True
    assert viewer.has_failed is False
    assert viewer._refused_paints == 0
    viewer.cleanup_gl()


def test_a_hidden_viewer_is_never_downgraded(qapp, qtbot) -> None:
    """Die Gegenprobe, die den Wächter überhaupt erst zulässig macht.

    Ein gesunder **verborgener** Viewer liefert dieselben Messwerte wie ein
    kaputter (kein Swap, kein Framebuffer, keine GL-Objekte). Getrennt werden
    sie allein dadurch, dass Qt ihm keinen ``paintEvent`` schickt – bliebe das
    aus, stufte der Wächter funktionierende Hardware ab. Genau das hält dieser
    Test fest.
    """
    _require_renderable(qapp)
    viewer = GLReliefViewer()
    qtbot.addWidget(viewer)
    viewer.resize(240, 200)
    viewer.set_mesh(_ramp_mesh())
    qtbot.wait(_NO_FRAME_WINDOW_MS)

    assert viewer.isVisible() is False
    assert viewer._has_rendered is False   # nie gerendert …
    assert viewer._refused_paints == 0     # … aber auch nie bewertet
    assert viewer.has_failed is False
    viewer.cleanup_gl()
