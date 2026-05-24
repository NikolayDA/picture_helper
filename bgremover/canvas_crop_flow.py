"""Crop-Overlay-Lebenszyklus für ImageCanvas."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

from bgremover.crop import CropOverlayItem
from bgremover.image_ops import crop_image


def start_crop_overlay(canvas, cw: int, ch: int, is_circle: bool) -> None:
    assert canvas._pil is not None
    cancel_crop_overlay(canvas)
    canvas._crop_overlay = CropOverlayItem(canvas._pil.width, canvas._pil.height, cw, ch, is_circle)
    canvas._scene.addItem(canvas._crop_overlay)
    canvas.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
    canvas.cropModeChanged.emit(True)
    label = "Kreis" if is_circle else f"{cw} × {ch} px"
    canvas.statusMsg.emit(f"✂  Ausschnitt verschieben  [{label}]  —  dann ✓ Anwenden klicken")


def confirm_crop(canvas) -> None:
    if canvas._crop_overlay is None or canvas._pil is None:
        return
    r = canvas._crop_overlay.crop_rect()
    cx, cy, cw, ch = r.x(), r.y(), r.width(), r.height()
    is_circle = canvas._crop_overlay.is_circle
    result = crop_image(canvas._pil, (cx, cy, cw, ch), is_circle=is_circle)
    desc = "Format: Kreis" if is_circle else f"Format: {cw}×{ch} px"
    cancel_crop_overlay(canvas)
    canvas.cropModeChanged.emit(False)
    canvas._apply_pil(result, desc=desc)
    canvas.statusMsg.emit(f"✂  Zugeschnitten: {result.width} × {result.height} px")


def cancel_crop(canvas) -> None:
    cancel_crop_overlay(canvas)
    canvas.cropModeChanged.emit(False)
    canvas.set_tool(canvas._tool)
    canvas.statusMsg.emit("Zuschnitt abgebrochen")


def cancel_crop_overlay(canvas) -> None:
    if canvas._crop_overlay is not None:
        canvas._scene.removeItem(canvas._crop_overlay)
        canvas._crop_overlay = None
    canvas._crop_dragging = False
    canvas._crop_resizing = False
    canvas._crop_resize_corner = -1
