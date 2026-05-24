"""Tests für Geometrie-Operationen: Drehen, Spiegeln, Ecken abrunden,
interaktiver Zuschnitt (Ratio + Kreis).

Diese Pfade waren bislang nur statisch bzw. über das Overlay-Item
abgedeckt – hier wird der tatsächliche Pixel-Output geprüft.
"""
import numpy as np
from PIL import Image

from bgremover import ImageCanvas, pil_to_numpy


def _canvas(color=(10, 20, 30, 255), size=(40, 20)):
    c = ImageCanvas()
    img = Image.new("RGBA", size, color)
    c.apply_loaded_image(img, "seed.png")
    c._mask = np.zeros((size[1], size[0]), dtype=bool)
    return c


def _canvas_image(c: ImageCanvas) -> Image.Image:
    img = c.image
    assert img is not None
    return img


# ── Drehen ─────────────────────────────────────────────────────────────

def test_rotate_90_swaps_dimensions(qapp):
    c = _canvas(size=(40, 20))
    c.apply_rotate(90)
    assert _canvas_image(c).size == (20, 40)


def test_rotate_270_swaps_dimensions(qapp):
    c = _canvas(size=(40, 20))
    c.apply_rotate(270)
    assert _canvas_image(c).size == (20, 40)


def test_rotate_180_keeps_dimensions(qapp):
    c = _canvas(size=(40, 20))
    c.apply_rotate(180)
    assert _canvas_image(c).size == (40, 20)


def test_rotate_free_angle_expands_canvas(qapp):
    c = _canvas(size=(40, 20))
    c.apply_rotate(45)
    w, h = _canvas_image(c).size
    assert w > 40 and h > 20            # Expand verhindert Abschneiden


def test_rotate_without_image_is_noop(qapp):
    c = ImageCanvas()
    c.apply_rotate(90)                  # darf nicht crashen
    assert c.image is None


# ── Spiegeln ───────────────────────────────────────────────────────────

def test_flip_horizontal_mirrors(qapp):
    c = _canvas(size=(4, 1))
    img = _canvas_image(c)
    img.putpixel((0, 0), (255, 0, 0, 255))
    c._arr = pil_to_numpy(img)
    c.apply_flip(True)
    assert _canvas_image(c).getpixel((3, 0)) == (255, 0, 0, 255)


def test_flip_vertical_mirrors(qapp):
    c = _canvas(size=(1, 4))
    img = _canvas_image(c)
    img.putpixel((0, 0), (0, 255, 0, 255))
    c._arr = pil_to_numpy(img)
    c.apply_flip(False)
    assert _canvas_image(c).getpixel((0, 3)) == (0, 255, 0, 255)


# ── Ecken abrunden ─────────────────────────────────────────────────────

def test_round_corners_makes_corner_transparent(qapp):
    c = _canvas(color=(0, 0, 0, 255), size=(40, 40))
    c.apply_round_corners(15)
    arr = np.array(_canvas_image(c))
    assert arr[0, 0, 3] == 0           # Ecke transparent
    assert arr[20, 20, 3] == 255       # Mitte opak


def test_round_corners_zero_radius_is_noop(qapp):
    c = _canvas(color=(0, 0, 0, 255), size=(20, 20))
    before = np.array(_canvas_image(c)).copy()
    c.apply_round_corners(0)
    np.testing.assert_array_equal(np.array(_canvas_image(c)), before)


# ── Interaktiver Zuschnitt ─────────────────────────────────────────────

def test_confirm_crop_ratio_changes_size(qapp):
    c = _canvas(color=(5, 5, 5, 255), size=(40, 20))
    c.start_crop_ratio(1, 1)
    assert c._crop_overlay is not None
    c.confirm_crop()
    assert c._crop_overlay is None
    w, h = _canvas_image(c).size
    assert w == h                      # 1:1 zugeschnitten


def test_confirm_crop_circle_adds_alpha_mask(qapp):
    c = _canvas(color=(0, 0, 0, 255), size=(40, 40))
    c.start_crop_circle()
    c.confirm_crop()
    arr = np.array(_canvas_image(c))
    h, w = arr.shape[:2]
    assert arr[0, 0, 3] == 0                   # Ecke ausserhalb des Kreises
    assert arr[h // 2, w // 2, 3] == 255       # Mitte opak


def test_cancel_crop_removes_overlay_without_change(qapp):
    c = _canvas(color=(9, 9, 9, 255), size=(30, 30))
    before = _canvas_image(c).size
    c.start_crop_ratio(16, 9)
    c.cancel_crop()
    assert c._crop_overlay is None
    assert _canvas_image(c).size == before
