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
    assert c.overlay_pixmap is None


def test_paint_brush_allocates_overlay_pixmap(qapp) -> None:
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c._paint_brush(20, 20, additive=True)
    assert c.overlay_pixmap is not None


def test_incremental_stroke_reuses_overlay_pixmap(qapp) -> None:
    """Zweiter Strich malt in dasselbe Pixmap (kein Vollneuaufbau)."""
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c._brush_r = 3
    c._paint_brush(8, 8, additive=True)
    first = c.overlay_pixmap
    assert first is not None
    c._paint_brush(30, 30, additive=True)
    assert c.overlay_pixmap is first  # gleiches Objekt → inkrementell


def test_clearing_selection_drops_overlay_pixmap(qapp) -> None:
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c._paint_brush(20, 20, additive=True)
    assert c.overlay_pixmap is not None
    c.clear_selection()
    # Vollaufbau bei leerer Maske → Pixmap freigegeben.
    assert c.overlay_pixmap is None


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
    incremental = c.overlay_pixmap.toImage()

    # Vollaufbau erzwingen (dirty=None) und vergleichen.
    c._refresh_overlay()
    full = c.overlay_pixmap.toImage()
    assert incremental == full


# ── Inkrementelles Radieren bis zur leeren Auswahl (#251) ──────────────

def test_erasing_last_pixel_drops_overlay_pixmap(qapp) -> None:
    """Wird der letzte Auswahlpixel inkrementell weg-radiert, darf keine
    transparente Vollbild-QPixmap im Canvas hängen bleiben (#251)."""
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c._brush_r = 4
    c._paint_brush(20, 20, additive=True)
    assert c.selection_mask is not None and c.selection_mask.any()
    assert c.overlay_pixmap is not None
    assert not c._overlay_item.pixmap().isNull()

    # Denselben Bereich vollständig wegradieren (eraser → additive=False).
    c._paint_brush(20, 20, additive=False)

    assert c.selection_mask is not None and not c.selection_mask.any()
    assert c.overlay_pixmap is None
    assert c._overlay_item.pixmap().isNull()


def test_partial_erase_keeps_incremental_overlay(qapp) -> None:
    """Teilweises Radieren lässt die Auswahl nicht leer werden und
    aktualisiert weiterhin nur das Dirty-Rechteck (dasselbe Pixmap-Objekt)."""
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c._brush_r = 3
    # Zwei getrennte Bereiche auswählen.
    c._paint_brush(8, 8, additive=True)
    c._paint_brush(30, 30, additive=True)
    pixmap = c.overlay_pixmap
    assert pixmap is not None

    # Nur einen der beiden Bereiche wegradieren → Auswahl bleibt nicht leer.
    c._paint_brush(8, 8, additive=False)

    assert c.selection_mask is not None and c.selection_mask.any()
    # Inkrementell: kein Vollneuaufbau, dasselbe Pixmap-Objekt.
    assert c.overlay_pixmap is pixmap
    # Inhalt entspricht weiterhin dem Vollaufbau derselben (Teil-)Maske.
    incremental = c.overlay_pixmap.toImage()
    c._refresh_overlay()
    assert incremental == c.overlay_pixmap.toImage()


def test_erasing_last_pixel_releases_full_buffer_on_large_image(qapp) -> None:
    """Größeres Bild: solange eine Auswahl existiert, hält der Canvas eine
    Overlay-QPixmap in voller Bildgröße; nach vollständigem Radieren wird sie
    freigegeben (kein gehaltener Vollbildpuffer ohne Nutzen, #251)."""
    c = ImageCanvas()
    c.apply_loaded_image(Image.new("RGBA", (1200, 900), (0, 0, 0, 255)), "big.png")
    c.set_tool(TOOL_BRUSH)
    c._brush_r = 5
    c._paint_brush(600, 450, additive=True)
    pm = c.overlay_pixmap
    assert pm is not None
    assert (pm.width(), pm.height()) == (1200, 900)

    c._paint_brush(600, 450, additive=False)

    assert c.selection_mask is not None and not c.selection_mask.any()
    assert c.overlay_pixmap is None
    assert c._overlay_item.pixmap().isNull()
