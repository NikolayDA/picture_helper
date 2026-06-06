"""Tests für ``CanvasViewport`` – Zoom, Pan und Pixmap-Refresh.

Die Pan-Routing-Entscheidung (Alt+LMB / MMB) und die Zoom-Grenzen sind
reine Logik und werden hier direkt über die ``ImageCanvas``-Instanz
geprüft, ohne ein sichtbares Fenster.
"""
from __future__ import annotations

from PIL import Image
from PyQt6.QtCore import QPointF, Qt

from bgremover import ImageCanvas
from bgremover.canvas_viewport import CanvasViewport


def _canvas(size=(120, 80)) -> ImageCanvas:
    c = ImageCanvas()
    c.apply_loaded_image(Image.new("RGBA", size, (10, 20, 30, 255)), "seed.png")
    return c


# ── refresh_image ──────────────────────────────────────────────────────

def test_refresh_image_with_none_is_noop(qapp):
    c = _canvas()
    item = c._viewport._img_item
    before_pixmap = item.pixmap().cacheKey()
    scene = c.scene()
    assert scene is not None
    before_rect = scene.sceneRect()

    c._viewport.refresh_image(None)

    assert item.pixmap().cacheKey() == before_pixmap
    assert scene.sceneRect() == before_rect


# ── Zoom ───────────────────────────────────────────────────────────────

def test_zoom_within_bounds_scales_view(qapp):
    c = _canvas()
    before = c.transform().m11()
    c._viewport.zoom(2.0)
    assert c.transform().m11() == 2.0 * before


def test_zoom_beyond_max_is_ignored(qapp):
    c = _canvas()
    before = c.transform().m11()
    # Faktor weit über ZOOM_MAX → wird verworfen, Skalierung bleibt.
    c._viewport.zoom(CanvasViewport.ZOOM_MAX * 10)
    assert c.transform().m11() == before


def test_zoom_below_min_is_ignored(qapp):
    c = _canvas()
    before = c.transform().m11()
    c._viewport.zoom(CanvasViewport.ZOOM_MIN / 10)
    assert c.transform().m11() == before


def test_handle_wheel_in_zooms_in(qapp):
    c = _canvas()
    before = c.transform().m11()
    c._viewport.handle_wheel(120)  # angle_y > 0 → reinzoomen
    assert c.transform().m11() > before


def test_handle_wheel_out_zooms_out(qapp):
    c = _canvas()
    c._viewport.zoom(4.0)  # erst etwas reinzoomen, damit Rauszoomen Spielraum hat
    before = c.transform().m11()
    c._viewport.handle_wheel(-120)  # angle_y < 0 → rauszoomen
    assert c.transform().m11() < before


# ── Pan-Routing ────────────────────────────────────────────────────────

def test_start_pan_with_middle_button(qapp):
    c = _canvas()
    consumed = c._viewport.start_pan_if_requested(
        Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.NoModifier,
        QPointF(10.0, 10.0))
    assert consumed is True
    assert c._viewport.is_panning is True


def test_start_pan_with_alt_left_button(qapp):
    c = _canvas()
    consumed = c._viewport.start_pan_if_requested(
        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.AltModifier,
        QPointF(0.0, 0.0))
    assert consumed is True
    assert c._viewport.is_panning is True


def test_plain_left_button_does_not_pan(qapp):
    c = _canvas()
    consumed = c._viewport.start_pan_if_requested(
        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPointF(0.0, 0.0))
    assert consumed is False
    assert c._viewport.is_panning is False


def test_update_pan_moves_scrollbars(qapp):
    c = _canvas()
    c._viewport.start_pan_if_requested(
        Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.NoModifier,
        QPointF(100.0, 100.0))
    hbar = c.horizontalScrollBar()
    vbar = c.verticalScrollBar()
    assert hbar is not None and vbar is not None
    hbar.setRange(0, 500)
    vbar.setRange(0, 500)
    hbar.setValue(200)
    vbar.setValue(200)
    # Maus bewegt sich nach rechts/unten → Scrollbar-Werte sinken.
    c._viewport.update_pan(QPointF(140.0, 130.0))
    assert hbar.value() == 200 - 40
    assert vbar.value() == 200 - 30


def test_stop_pan_clears_flag(qapp):
    c = _canvas()
    c._viewport.start_pan_if_requested(
        Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.NoModifier,
        QPointF(0.0, 0.0))
    assert c._viewport.is_panning is True
    c._viewport.stop_pan()
    assert c._viewport.is_panning is False
