"""Tests für CropOverlayItem.

Verteidigt drei Bug-Fixes aus dem Code-Review:

* Fix #2 — Aspect-Ratio bleibt erhalten, wenn der Crop-Rahmen über den
  Bildrand hinaus gezogen wird (gemeinsamer Skalierungsfaktor).
* Fix #3 — ``set_position`` clampt den Rahmen sicher innerhalb des Bildes.
* Fix #5 — ``boundingRect`` enthält Marge für Eck-Handles und Hinweistext.
"""
import pytest

from bgremover import CropOverlayItem


# ── Fix #2: Aspect-Ratio über Bildrand ─────────────────────────────────

def test_resize_preserves_aspect_when_dragged_past_edge(qapp):
    ov = CropOverlayItem(img_w=1000, img_h=600, crop_w=400, crop_h=300)
    ov._cx = 0.0
    ov._cy = 0.0
    aspect = ov._aspect
    ov.resize_from_corner(corner_idx=3, sx=2000.0, sy=2000.0)
    assert ov._cw / ov._ch == pytest.approx(aspect, rel=1e-6)
    assert ov._cw <= ov._iw + 1e-6
    assert ov._ch <= ov._ih + 1e-6


def test_resize_preserves_aspect_on_narrow_image(qapp):
    """Schmales Hochformat-Bild, Querformat-Crop 3:2."""
    ov = CropOverlayItem(img_w=400, img_h=1000, crop_w=300, crop_h=200)
    ov._cx = 0.0
    ov._cy = 0.0
    aspect = ov._aspect
    ov.resize_from_corner(corner_idx=3, sx=5000.0, sy=5000.0)
    assert ov._cw / ov._ch == pytest.approx(aspect, rel=1e-6)
    assert ov._cw <= ov._iw + 1e-6
    assert ov._ch <= ov._ih + 1e-6


def test_resize_minimum_size_enforced(qapp):
    """Sehr kleine Drag-Distanz darf nicht unter MIN_PX (20) gehen."""
    ov = CropOverlayItem(img_w=1000, img_h=1000, crop_w=500, crop_h=500)
    ov._cx = 100.0
    ov._cy = 100.0
    # BR-Ecke fast auf TL ziehen → würde sonst 0×0 ergeben
    ov.resize_from_corner(corner_idx=3, sx=100.5, sy=100.5)
    assert ov._cw >= 20.0
    assert ov._ch >= 20.0


# ── Fix #3: set_position Clamp ─────────────────────────────────────────

def test_set_position_clamps_to_image_bounds(qapp):
    ov = CropOverlayItem(img_w=1000, img_h=800, crop_w=200, crop_h=150)
    ov.set_position(-100.0, -100.0)
    assert ov._cx == 0.0
    assert ov._cy == 0.0
    ov.set_position(5000.0, 5000.0)
    assert ov._cx == pytest.approx(1000 - 200)
    assert ov._cy == pytest.approx(800 - 150)


# ── Fix #5: boundingRect mit Marge ─────────────────────────────────────

def test_bounding_rect_has_margin_for_handles_and_hint(qapp):
    ov = CropOverlayItem(img_w=100, img_h=100, crop_w=50, crop_h=50)
    br = ov.boundingRect()
    assert br.x() < 0
    assert br.y() < 0
    assert br.right() > ov._iw
    assert br.bottom() > ov._ih


# ── corner_hit ─────────────────────────────────────────────────────────

def test_corner_hit_returns_index_on_handle(qapp):
    ov = CropOverlayItem(img_w=1000, img_h=1000, crop_w=400, crop_h=400)
    # Initial zentriert: _cx = 300, _cy = 300
    assert ov.corner_hit(300.0, 300.0) == 0  # TL
    assert ov.corner_hit(700.0, 300.0) == 1  # TR
    assert ov.corner_hit(300.0, 700.0) == 2  # BL
    assert ov.corner_hit(700.0, 700.0) == 3  # BR


def test_corner_hit_returns_minus_one_outside_handle(qapp):
    ov = CropOverlayItem(img_w=1000, img_h=1000, crop_w=400, crop_h=400)
    # Mitte des Rahmens — kein Handle
    assert ov.corner_hit(500.0, 500.0) == -1


# ── crop_rect liefert Pixel-Koordinaten ────────────────────────────────

def test_crop_rect_returns_pixel_coordinates(qapp):
    ov = CropOverlayItem(img_w=800, img_h=600, crop_w=200, crop_h=150)
    rect = ov.crop_rect()
    # Initial zentriert
    assert rect.x() == 300
    assert rect.y() == 225
    assert rect.width() == 200
    assert rect.height() == 150
