"""Tests für das inkrementelle Auswahl-Overlay.

Statt bei jeder Pinselbewegung ein volles RGBA-Overlay (bei 40 MP rund
160 MiB) neu zu bauen, hält der Canvas ein persistentes Pixmap und malt
nur die geänderte Pinsel-Bounding-Box hinein. Bei leerer Auswahl wird gar
kein Overlay-Pixmap allokiert.

Alle Tests fordern die ``qapp``-Fixture an: schon das Konstruieren eines
``ImageCanvas`` (QWidget) ohne laufende ``QApplication`` ruft Qt-seitig
``abort()`` (SIGABRT) – das würde die Datei in Isolation abreißen.
"""
from __future__ import annotations

from PIL import Image

from bgremover import TOOL_BRUSH, ImageCanvas
from bgremover.canvas_selection import CanvasSelection


def _canvas() -> ImageCanvas:
    c = ImageCanvas()
    c.apply_loaded_image(Image.new("RGBA", (40, 40), (0, 0, 0, 255)), "seed.png")
    return c


# ── CanvasSelection.paint_brush gibt die Dirty-Box zurück ──────────────

def test_paint_brush_returns_bounding_box(qapp) -> None:
    sel = CanvasSelection(40, 40)
    rect = sel.paint_brush(20, 20, 3, additive=True)
    assert rect == (17, 17, 24, 24)


def test_paint_brush_clamps_box_to_image(qapp) -> None:
    sel = CanvasSelection(40, 40)
    rect = sel.paint_brush(1, 1, 5, additive=True)
    assert rect == (0, 0, 7, 7)


def test_paint_brush_fully_outside_returns_none(qapp) -> None:
    sel = CanvasSelection(40, 40)
    assert sel.paint_brush(-100, -100, 3, additive=True) is None


# ── Canvas-Overlay-Allokation ──────────────────────────────────────────

def test_empty_selection_has_no_overlay_pixmap(qapp) -> None:
    c = _canvas()
    # Frisch geladen → leere Maske → kein Overlay allokiert.
    assert c._overlay_pixmap is None


def test_paint_brush_allocates_overlay_pixmap(qapp) -> None:
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c._paint_brush(20, 20, additive=True)
    assert c._overlay_pixmap is not None


def test_incremental_stroke_reuses_overlay_pixmap(qapp) -> None:
    """Zweiter Strich malt in dasselbe Pixmap (kein Vollneuaufbau)."""
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c._brush_r = 3
    c._paint_brush(8, 8, additive=True)
    first = c._overlay_pixmap
    assert first is not None
    c._paint_brush(30, 30, additive=True)
    assert c._overlay_pixmap is first  # gleiches Objekt → inkrementell


def test_clearing_selection_drops_overlay_pixmap(qapp) -> None:
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c._paint_brush(20, 20, additive=True)
    assert c._overlay_pixmap is not None
    c.clear_selection()
    # Vollaufbau bei leerer Maske → Pixmap freigegeben.
    assert c._overlay_pixmap is None


def test_incremental_update_matches_full_rebuild(qapp) -> None:
    """Das inkrementell gepflegte Overlay entspricht dem Vollaufbau.

    Vergleicht die Pixmap nach zwei inkrementellen Strichen mit der Pixmap,
    die ein expliziter Vollaufbau derselben Maske ergibt.
    """
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c._brush_r = 3
    c._paint_brush(8, 8, additive=True)
    c._paint_brush(30, 30, additive=True)
    incremental = c._overlay_pixmap.toImage()

    # Vollaufbau erzwingen (dirty=None) und vergleichen.
    c._refresh_overlay()
    full = c._overlay_pixmap.toImage()
    assert incremental == full
