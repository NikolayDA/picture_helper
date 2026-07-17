"""Tests für die reinen Hilfsfunktionen aus ``bgremover.image_utils``."""
import numpy as np
import pytest
from PIL import Image
from PyQt6.QtGui import QImage

from bgremover import (
    flood_fill,
    mask_to_overlay,
    numpy_to_pil,
    pil_to_numpy,
    pil_to_numpy_readonly,
    pil_to_qpixmap,
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
    # Defensive Variante: das Resultat ist schreibbar und ein Schreibzugriff
    # schlägt tatsächlich sichtbar durch.
    assert arr.flags.writeable
    arr[0, 0, 0] = 99
    assert arr[0, 0, 0] == 99


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


def test_pil_to_numpy_readonly_converts_non_rgba_source():
    """#598: Palette-Bild (Modus ``P``) muss vor der Array-Sicht nach
    RGBA konvertiert werden."""
    img = Image.new("P", (4, 3))
    arr = pil_to_numpy_readonly(img)
    assert arr.shape == (3, 4, 4)
    assert arr.dtype == np.uint8


def test_pil_to_qpixmap_converts_non_rgba_source(qapp):
    """#598: RGB-Quellbild wird vor der QPixmap-Erzeugung nach RGBA
    konvertiert (Alpha wird dabei auf 255 gesetzt)."""
    img = Image.new("RGB", (4, 3), (10, 20, 30))
    px = pil_to_qpixmap(img)
    assert px.width() == 4
    assert px.height() == 3
    qi = px.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
    arr = np.array(qi.bits().asarray(4 * 3 * 4)).reshape(3, 4, 4)
    assert (arr[:, :, 3] == 255).all()
    assert (arr[:, :, 0] == 10).all()


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


# Hinweis: Der frühere Uniform-Bild-Test ist als Duplikat entfernt –
# test_flood_fill.py::test_uniform_area_selects_everything deckt denselben
# Fall in der dedizierten Flood-Fill-Suite ab.

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
