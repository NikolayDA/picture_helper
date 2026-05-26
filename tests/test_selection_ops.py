"""Tests für die Auswahl-Operationen (E1, E4, E8).

* ``invert_selection`` kehrt die Boolean-Maske um.
* ``expand_selection`` / ``shrink_selection`` wenden PIL-Morphologie an.
* ``_brush_preview`` ist nur bei Brush/Eraser sichtbar.
"""
import numpy as np
from PIL import Image
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor

from bgremover import TOOL_BRUSH, TOOL_ERASER, TOOL_WAND, ImageCanvas


def _canvas_with_mask():
    """Canvas mit 20×20-Bild und 4×4-Auswahl in der Mitte."""
    c = ImageCanvas()
    c.apply_loaded_image(Image.new("RGBA", (20, 20), (0, 0, 0, 255)), "seed.png")
    c._mask = np.zeros((20, 20), dtype=bool)
    c._mask[8:12, 8:12] = True
    return c


def _canvas_image(c: ImageCanvas) -> Image.Image:
    img = c.image
    assert img is not None
    return img


# ── E1: invert_selection ────────────────────────────────────────────────

def test_invert_selection_flips_mask(qapp):
    c = _canvas_with_mask()
    selected_before = int(c._mask.sum())
    c.invert_selection()
    assert int(c._mask.sum()) == 20 * 20 - selected_before


def test_invert_selection_without_image_is_noop(qapp):
    c = ImageCanvas()
    c.invert_selection()                       # darf nicht crashen
    assert c._mask is None


def test_double_invert_returns_to_original(qapp):
    c = _canvas_with_mask()
    before = c._mask.copy()
    c.invert_selection()
    c.invert_selection()
    np.testing.assert_array_equal(c._mask, before)


# ── E4: expand / shrink ─────────────────────────────────────────────────

def test_expand_selection_grows_block(qapp):
    c = _canvas_with_mask()
    before = int(c._mask.sum())
    c.expand_selection(2)
    after = int(c._mask.sum())
    assert after > before
    # 4×4-Block mit Radius 2 → maximal 8×8 = 64
    assert after <= 64


def test_shrink_selection_reduces_block(qapp):
    c = _canvas_with_mask()
    before = int(c._mask.sum())
    c.shrink_selection(1)
    after = int(c._mask.sum())
    assert after < before
    # 4×4 mit Radius 1 → 2×2 = 4
    assert after == 4


def test_expand_with_zero_radius_is_noop(qapp):
    c = _canvas_with_mask()
    before = c._mask.copy()
    c.expand_selection(0)
    np.testing.assert_array_equal(c._mask, before)


def test_morphology_without_image_is_noop(qapp):
    c = ImageCanvas()
    c.expand_selection(3)                      # darf nicht crashen
    c.shrink_selection(3)
    assert c._mask is None


# ── E8: Pinsel-Vorschau-Kreis ───────────────────────────────────────────

def test_brush_preview_invisible_by_default(qapp):
    c = ImageCanvas()
    assert not c._brush_preview.isVisible()


def test_brush_preview_visible_for_brush_after_move(qapp):
    c = _canvas_with_mask()
    c.set_tool(TOOL_BRUSH)
    c._update_brush_preview(QPointF(10, 10))
    assert c._brush_preview.isVisible()
    # Größe = 2 * brush_r
    rect = c._brush_preview.rect()
    assert rect.width() == c._brush_r * 2


def test_brush_preview_visible_for_eraser(qapp):
    c = _canvas_with_mask()
    c.set_tool(TOOL_ERASER)
    c._update_brush_preview(QPointF(5, 5))
    assert c._brush_preview.isVisible()


def test_brush_preview_hidden_for_wand(qapp):
    c = _canvas_with_mask()
    c.set_tool(TOOL_BRUSH)
    c._update_brush_preview(QPointF(10, 10))
    assert c._brush_preview.isVisible()
    # Wechsel auf Wand muss den Kreis sofort verstecken
    c.set_tool(TOOL_WAND)
    assert not c._brush_preview.isVisible()


def test_brush_preview_hidden_without_image(qapp):
    c = ImageCanvas()
    c.set_tool(TOOL_BRUSH)
    c._update_brush_preview(QPointF(10, 10))
    assert not c._brush_preview.isVisible()


# ── Pinsel/Radiergummi: tatsächlicher Maskeneffekt ─────────────────────

def test_paint_brush_marks_circle(qapp):
    c = _canvas_with_mask()
    c._mask[:] = False
    c.set_tool(TOOL_BRUSH)
    c._brush_r = 3
    c._paint_brush(10, 10)
    assert c._mask[10, 10]
    assert not c._mask[0, 0]


def test_eraser_clears_circle(qapp):
    c = _canvas_with_mask()
    c._mask[:] = True
    c.set_tool(TOOL_ERASER)
    c._brush_r = 3
    c._paint_brush(10, 10)
    assert not c._mask[10, 10]
    assert c._mask[0, 0]


# ── Polygon-Lasso ──────────────────────────────────────────────────────

def test_lasso_close_builds_mask_from_polygon(qapp):
    c = _canvas_with_mask()
    c._mask[:] = False
    c._lasso.points = [(2, 2), (10, 2), (10, 10), (2, 10)]
    c._lasso.modifiers = Qt.KeyboardModifier.NoModifier
    c._lasso_close()
    assert c._mask[5, 5]            # innerhalb des Polygons
    assert not c._mask[18, 18]      # ausserhalb
    assert c._lasso.points == []    # Punkte nach Abschluss geleert


def test_lasso_close_shift_adds_to_existing(qapp):
    c = _canvas_with_mask()         # 8:12, 8:12 = True
    existing = c._mask.copy()
    c._lasso.points = [(0, 0), (4, 0), (4, 4), (0, 4)]
    c._lasso.modifiers = Qt.KeyboardModifier.ShiftModifier
    c._lasso_close()
    assert c._mask[2, 2]            # neu hinzugefügt
    assert c._mask[10, 10]          # alte Auswahl bleibt
    assert (c._mask >= existing).all()


def test_lasso_close_ctrl_subtracts(qapp):
    c = _canvas_with_mask()         # 8:12, 8:12 = True
    c._lasso.points = [(8, 8), (12, 8), (12, 12), (8, 12)]
    c._lasso.modifiers = Qt.KeyboardModifier.ControlModifier
    c._lasso_close()
    assert not c._mask[10, 10]      # Überlappung wurde abgezogen


def test_lasso_cancel_clears_state(qapp):
    c = _canvas_with_mask()
    c._lasso.points = [(1, 1), (2, 2)]
    c._lasso.cancel()
    assert c._lasso.points == []
    assert c._lasso.modifiers == Qt.KeyboardModifier.NoModifier


# ── apply_remove / apply_replace – Erfolgsfall ─────────────────────────

def test_apply_remove_makes_selection_transparent(qapp):
    c = ImageCanvas()
    img = Image.new("RGBA", (10, 10), (10, 20, 30, 255))
    c.apply_loaded_image(img, "seed.png")
    c._mask = np.zeros((10, 10), dtype=bool)
    c._mask[2:5, 2:5] = True
    c.apply_remove()
    arr = np.array(_canvas_image(c))
    assert (arr[2:5, 2:5, 3] == 0).all()    # Auswahl → transparent
    assert arr[0, 0, 3] == 255              # Rest unverändert


def test_apply_replace_fills_selection_with_color(qapp):
    c = ImageCanvas()
    img = Image.new("RGBA", (10, 10), (10, 20, 30, 255))
    c.apply_loaded_image(img, "seed.png")
    c._mask = np.zeros((10, 10), dtype=bool)
    c._mask[0:4, 0:4] = True
    c.apply_replace(QColor(255, 0, 0))
    arr = np.array(_canvas_image(c))
    assert arr[0, 0].tolist() == [255, 0, 0, 255]
    assert arr[9, 9].tolist() == [10, 20, 30, 255]
