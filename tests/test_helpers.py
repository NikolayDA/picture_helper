"""Tests für die reinen Hilfsfunktionen aus BgRemover.py."""
import numpy as np
import pytest
from PIL import Image

from bgremover import (
    flood_fill,
    mask_to_overlay,
    numpy_to_pil,
    pil_to_numpy,
    pil_to_numpy_readonly,
)


# ── pil_to_numpy / numpy_to_pil ─────────────────────────────────────────

def test_pil_to_numpy_returns_rgba_array():
    img = Image.new("RGB", (4, 3), (10, 20, 30))
    arr = pil_to_numpy(img)
    assert arr.shape == (3, 4, 4)
    assert arr.dtype == np.uint8
    # RGB → RGBA: Alpha = 255
    assert (arr[:, :, 3] == 255).all()
    assert (arr[:, :, 0] == 10).all()
    # Defensive Variante: das Resultat ist schreibbar.
    assert arr.flags.writeable
    arr[0, 0, 0] = 99


def test_pil_to_numpy_readonly_is_not_writable():
    """Spar-Variante teilt sich den PIL-Buffer; jedes Schreiben muss
    fehlschlagen, damit Aufrufer ihre Mutationen bewusst auf eine Kopie
    lenken."""
    img = Image.new("RGBA", (3, 2), (10, 20, 30, 255))
    arr = pil_to_numpy_readonly(img)
    assert arr.shape == (2, 3, 4)
    assert not arr.flags.writeable
    with pytest.raises(ValueError):
        arr[0, 0, 0] = 5


def test_numpy_to_pil_round_trip():
    arr = np.zeros((5, 6, 4), dtype=np.uint8)
    arr[:, :, 0] = 200          # R
    arr[:, :, 3] = 128          # halbtransparent
    img = numpy_to_pil(arr)
    assert img.mode == "RGBA"
    assert img.size == (6, 5)   # PIL: (width, height)
    back = pil_to_numpy(img)
    np.testing.assert_array_equal(arr, back)


# ── flood_fill ──────────────────────────────────────────────────────────

def _solid_block(w=10, h=10, color=(50, 100, 150)):
    """Einfarbiges RGBA-Bild als numpy-Array."""
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = color[0]
    arr[:, :, 1] = color[1]
    arr[:, :, 2] = color[2]
    arr[:, :, 3] = 255
    return arr


def test_flood_fill_uniform_image_selects_everything():
    arr = _solid_block(8, 8)
    mask = flood_fill(arr, 0, 0, tolerance=0)
    assert mask.shape == (8, 8)
    assert mask.all()


def test_flood_fill_two_regions_with_tolerance_zero():
    arr = _solid_block(10, 10, color=(0, 0, 0))
    arr[:, 5:, :3] = 255  # rechte Hälfte weiß
    mask = flood_fill(arr, 0, 0, tolerance=0)
    assert mask[:, :5].all()
    assert not mask[:, 5:].any()


def test_flood_fill_high_tolerance_bridges_regions():
    arr = _solid_block(10, 10, color=(0, 0, 0))
    arr[:, 5:, :3] = 255
    mask = flood_fill(arr, 0, 0, tolerance=255)
    assert mask.all()


def test_flood_fill_click_outside_returns_empty_mask():
    arr = _solid_block(4, 4)
    mask = flood_fill(arr, -1, 0, tolerance=10)
    assert mask.shape == (4, 4)
    assert not mask.any()


# ── mask_to_overlay ─────────────────────────────────────────────────────

def test_mask_to_overlay_returns_pixmap_of_correct_size(qapp):
    mask = np.zeros((20, 30), dtype=bool)
    mask[5:10, 10:20] = True
    px = mask_to_overlay(mask, w=30, h=20)
    assert px.width() == 30
    assert px.height() == 20
    assert not px.isNull()


def test_mask_to_overlay_handles_empty_mask(qapp):
    mask = np.zeros((10, 10), dtype=bool)
    px = mask_to_overlay(mask, 10, 10)
    assert not px.isNull()
