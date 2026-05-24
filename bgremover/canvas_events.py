"""Event-Helfer für ImageCanvas (Press/Zoom/Drop)."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

from bgremover.constants import TOOL_LASSO, TOOL_WAND
from bgremover.image_utils import flood_fill


def to_img_xy(canvas, event) -> tuple[int, int]:
    sp = canvas.mapToScene(event.position().toPoint())
    return int(sp.x()), int(sp.y())


def handle_crop_press(canvas, btn: Qt.MouseButton, sp) -> bool:
    """Verarbeitet Press-Events im Crop-Modus; True => Event konsumiert."""
    if canvas._crop_overlay is None:
        return False
    if btn == Qt.MouseButton.LeftButton:
        corner = canvas._crop_overlay.corner_hit(sp.x(), sp.y())
        if corner >= 0:
            canvas._crop_resizing = True
            canvas._crop_resize_corner = corner
            canvas._crop_drag_start = sp
            canvas.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor if corner in (0, 3) else Qt.CursorShape.SizeBDiagCursor))
        elif canvas._crop_overlay.inside(sp.x(), sp.y()):
            canvas._crop_dragging = True
            canvas._crop_drag_start = sp
            canvas._crop_start_pos = canvas._crop_overlay.top_left
            canvas.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
    return True


def start_pan_if_requested(canvas, btn: Qt.MouseButton, mods: Qt.KeyboardModifier, pos) -> bool:
    """Startet Pan-Modus (Alt+LMB oder MMB); True => Event konsumiert."""
    if (btn == Qt.MouseButton.MiddleButton or
            (btn == Qt.MouseButton.LeftButton and mods & Qt.KeyboardModifier.AltModifier)):
        canvas._panning = True
        canvas._pan_start = pos
        canvas.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        return True
    return False


def handle_tool_press(canvas, x: int, y: int, mods: Qt.KeyboardModifier) -> None:
    """Werkzeug-spezifische Reaktion auf linken Maus-Press."""
    if canvas._tool == TOOL_WAND:
        assert canvas._pil is not None and canvas._arr is not None and canvas._mask is not None
        w, h = canvas._pil.size
        if 0 <= x < w and 0 <= y < h:
            new = flood_fill(canvas._arr, x, y, canvas._tolerance)
            if mods & Qt.KeyboardModifier.ShiftModifier:
                canvas._mask |= new
            elif mods & Qt.KeyboardModifier.ControlModifier:
                canvas._mask &= ~new
            else:
                canvas._mask = new
            canvas._refresh_overlay()
            canvas.statusMsg.emit(f"Auswahl: {int(canvas._mask.sum()):,} Pixel")
    elif canvas._tool == TOOL_LASSO:
        assert canvas._pil is not None
        w, h = canvas._pil.size
        if 0 <= x < w and 0 <= y < h:
            canvas._lasso.set_modifiers_if_first(mods)
            canvas.statusMsg.emit(canvas._lasso.add_point(x, y))
    else:
        canvas._drawing = True
        canvas._paint_brush(x, y)


def zoom(canvas, factor: float) -> None:
    new_scale = canvas.transform().m11() * factor
    if canvas.ZOOM_MIN <= new_scale <= canvas.ZOOM_MAX:
        canvas.scale(factor, factor)


def drag_enter_event(canvas, event) -> None:
    if event is None:
        return
    mime = event.mimeData()
    if mime is not None and mime.hasUrls():
        event.acceptProposedAction()


def drag_move_event(canvas, event) -> None:
    if event.mimeData().hasUrls():
        event.acceptProposedAction()


def drop_event(canvas, event) -> None:
    if event is None:
        return
    mime = event.mimeData()
    if mime is None:
        return
    exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".gif")
    valid = [url.toLocalFile() for url in mime.urls() if Path(url.toLocalFile()).suffix.lower() in exts]
    if not valid:
        canvas.statusMsg.emit("Format nicht unterstützt")
        return
    canvas.loadRequested.emit(valid[0])
    if len(valid) > 1:
        canvas.statusMsg.emit(f"Geöffnet: {Path(valid[0]).name}  ({len(valid) - 1} weitere Datei(en) ignoriert)")
