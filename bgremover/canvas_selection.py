"""Auswahl-/Maskenoperationen für ImageCanvas."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

from bgremover.constants import TOOL_BRUSH, logger
from bgremover.image_ops import remove_selection, replace_selection


def clear_selection(canvas) -> None:
    if canvas._mask is not None:
        canvas._mask[:] = False
        canvas._refresh_overlay()
        canvas.statusMsg.emit("Auswahl aufgehoben")


def invert_selection(canvas) -> None:
    """Kehrt die aktuelle Maske um (Vorder- ↔ Hintergrund)."""
    if canvas._mask is None or canvas._pil is None:
        canvas.statusMsg.emit("Kein Bild geladen")
        return
    canvas._mask = ~canvas._mask
    canvas._refresh_overlay()
    canvas.statusMsg.emit(f"Auswahl invertiert: {int(canvas._mask.sum()):,} Pixel")


def morphology(canvas, radius: int, kind: str) -> None:
    """Erweitert oder schrumpft die Boolean-Maske um ``radius`` Pixel."""
    if canvas._mask is None or canvas._pil is None or radius <= 0:
        return
    mask_img = Image.fromarray((canvas._mask * 255).astype(np.uint8), mode="L")
    size = radius * 2 + 1
    filt: ImageFilter.RankFilter
    if kind == "expand":
        filt = ImageFilter.MaxFilter(size)
        label = "erweitert"
    else:
        filt = ImageFilter.MinFilter(size)
        label = "geschrumpft"
    result = mask_img.filter(filt)
    canvas._mask = np.array(result) > 127
    canvas._refresh_overlay()
    canvas.statusMsg.emit(f"Auswahl um {radius} px {label}: {int(canvas._mask.sum()):,} Pixel")


def check_selection(canvas) -> bool:
    if canvas._pil is None:
        canvas.statusMsg.emit("Kein Bild geladen")
        return False
    if canvas._mask is None or not canvas._mask.any():
        canvas.statusMsg.emit("Keine Auswahl – erst Bereich mit Zauberstab oder Pinsel auswählen")
        return False
    return True


def apply_remove(canvas, _checked=False) -> None:
    try:
        if not check_selection(canvas):
            return
        assert canvas._arr is not None
        assert canvas._mask is not None
        canvas._apply_pil(remove_selection(canvas._arr, canvas._mask), desc="Hintergrund entfernt")
        canvas._vp.update()
        canvas.statusMsg.emit("Hintergrund entfernt (transparent)")
    except Exception as e:
        logger.exception("Fehler beim Entfernen")
        canvas.statusMsg.emit(f"Fehler beim Entfernen: {e}")


def apply_replace(canvas, color) -> None:
    try:
        if not check_selection(canvas):
            return
        assert canvas._arr is not None
        assert canvas._mask is not None
        canvas._apply_pil(
            replace_selection(canvas._arr, canvas._mask, (color.red(), color.green(), color.blue())),
            desc=f"Farbe ersetzt ({color.name()})",
        )
        canvas._vp.update()
        canvas.statusMsg.emit(f"Hintergrund ersetzt: {color.name()}")
    except Exception as e:
        logger.exception("Fehler beim Ersetzen")
        canvas.statusMsg.emit(f"Fehler beim Ersetzen: {e}")


def paint_brush(canvas, cx: int, cy: int) -> None:
    if canvas._mask is None or canvas._pil is None:
        return
    r = canvas._brush_r
    h, w = canvas._mask.shape
    y0, y1 = max(0, cy - r), min(h, cy + r + 1)
    x0, x1 = max(0, cx - r), min(w, cx + r + 1)
    yy, xx = np.ogrid[y0:y1, x0:x1]
    circle = (yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2
    if canvas._tool == TOOL_BRUSH:
        canvas._mask[y0:y1, x0:x1][circle] = True
    else:
        canvas._mask[y0:y1, x0:x1][circle] = False
    canvas._refresh_overlay()
