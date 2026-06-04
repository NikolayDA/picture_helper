"""Tests für die Zoom-Limits in ImageCanvas.

Vor dem Fix war ``wheelEvent`` unbegrenzt — durch mehrfaches Scrollen
konnte das Bild auf 0 schrumpfen (kein Klick mehr möglich) oder so groß
gezoomt werden, dass Qt-Rasterung sichtbar wurde.
"""
from bgremover import ImageCanvas


def test_zoom_in_is_capped_at_max(qapp):
    canvas = ImageCanvas()
    for _ in range(200):
        canvas._zoom(1.15)
    assert canvas.transform().m11() <= canvas.ZOOM_MAX + 1e-6


def test_zoom_out_is_capped_at_min(qapp):
    canvas = ImageCanvas()
    for _ in range(200):
        canvas._zoom(1 / 1.15)
    assert canvas.transform().m11() >= canvas.ZOOM_MIN - 1e-6


def test_zoom_within_bounds_applies(qapp):
    """Im erlaubten Bereich muss `_zoom` den Skalierungsfaktor ändern."""
    canvas = ImageCanvas()
    start = canvas.transform().m11()
    canvas._zoom(2.0)
    assert canvas.transform().m11() == start * 2.0
