"""Crop-Overlay-Zustand und Interaktion fuer ``ImageCanvas``."""
from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from PIL import Image
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QGraphicsScene

from bgremover.crop import CropOverlayItem
from bgremover.image_ops import crop_image, crop_size_for_ratio


class _CropOwner(Protocol):
    @property
    def image(self) -> Image.Image | None: ...

    def apply_edit(self, img: Image.Image, desc: str = "Bearbeitung") -> None: ...


class CanvasCrop:
    """Verwaltet Crop-Overlay, Drag/Resize-Zustand und Zuschnitt."""

    def __init__(
        self,
        scene: QGraphicsScene,
        owner: _CropOwner,
        emit_status: Callable[[str], None],
        emit_crop_mode: Callable[[bool], None],
        set_cursor: Callable[[QCursor], None],
        restore_cursor: Callable[[], None],
    ) -> None:
        self._scene = scene
        self._owner = owner
        self._emit_status = emit_status
        self._emit_crop_mode = emit_crop_mode
        self._set_cursor = set_cursor
        self._restore_cursor = restore_cursor

        self._overlay: CropOverlayItem | None = None
        self._dragging = False
        self._drag_start = QPointF()
        self._start_pos = QPointF()
        self._resizing = False
        self._resize_corner = -1

    @property
    def overlay(self) -> CropOverlayItem | None:
        return self._overlay

    def start_circle(self) -> None:
        img = self._owner.image
        assert img is not None
        size = min(img.width, img.height)
        self.start_overlay(size, size, is_circle=True)

    def start_ratio(self, ratio_w: int, ratio_h: int) -> None:
        img = self._owner.image
        assert img is not None
        cw, ch = crop_size_for_ratio(img.size, ratio_w, ratio_h)
        self.start_overlay(cw, ch, is_circle=False)

    def start_overlay(self, cw: int, ch: int, is_circle: bool) -> None:
        img = self._owner.image
        assert img is not None
        self._clear_overlay()
        self._overlay = CropOverlayItem(img.width, img.height, cw, ch, is_circle)
        self._scene.addItem(self._overlay)
        self._set_cursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self._emit_crop_mode(True)
        label = "Kreis" if is_circle else f"{cw} × {ch} px"
        self._emit_status(
            f"✂  Ausschnitt verschieben  [{label}]  —  dann ✓ Anwenden klicken")

    def confirm(self) -> None:
        img = self._owner.image
        if self._overlay is None or img is None:
            return
        r = self._overlay.crop_rect()
        cx, cy, cw, ch = r.x(), r.y(), r.width(), r.height()
        is_circle = self._overlay.is_circle
        result = crop_image(img, (cx, cy, cw, ch), is_circle=is_circle)
        desc = "Format: Kreis" if is_circle else f"Format: {cw}×{ch} px"

        self._clear_overlay()
        self._emit_crop_mode(False)
        self._owner.apply_edit(result, desc=desc)
        self._emit_status(f"✂  Zugeschnitten: {result.width} × {result.height} px")

    def cancel(self) -> None:
        self._clear_overlay()
        self._emit_crop_mode(False)
        self._restore_cursor()
        self._emit_status("Zuschnitt abgebrochen")

    def clear(self) -> None:
        self._clear_overlay()

    def _clear_overlay(self) -> None:
        if self._overlay is not None:
            self._scene.removeItem(self._overlay)
            self._overlay = None
        self._dragging = False
        self._resizing = False
        self._resize_corner = -1

    def handle_press(self, btn: Qt.MouseButton, sp: QPointF) -> bool:
        """Verarbeitet Press-Events im Crop-Modus; True => Event konsumiert."""
        if self._overlay is None:
            return False
        if btn == Qt.MouseButton.LeftButton:
            corner = self._overlay.corner_hit(sp.x(), sp.y())
            if corner >= 0:
                self._resizing = True
                self._resize_corner = corner
                self._drag_start = sp
                self._set_cursor(QCursor(Qt.CursorShape.SizeFDiagCursor
                                         if corner in (0, 3)
                                         else Qt.CursorShape.SizeBDiagCursor))
            elif self._overlay.inside(sp.x(), sp.y()):
                self._dragging = True
                self._drag_start = sp
                self._start_pos = self._overlay.top_left
                self._set_cursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        return True

    def handle_move(self, sp: QPointF) -> bool:
        if self._resizing and self._overlay is not None:
            self._overlay.resize_from_corner(self._resize_corner, sp.x(), sp.y())
            cw, ch = self._overlay.size
            self._emit_status(
                f"⇲ Größe: {int(round(cw))} × {int(round(ch))} px")
            return True

        if self._dragging and self._overlay is not None:
            delta = sp - self._drag_start
            self._overlay.set_position(
                self._start_pos.x() + delta.x(),
                self._start_pos.y() + delta.y())
            return True

        if self._overlay is not None:
            corner = self._overlay.corner_hit(sp.x(), sp.y())
            if corner >= 0:
                self._set_cursor(QCursor(Qt.CursorShape.SizeFDiagCursor
                                         if corner in (0, 3)
                                         else Qt.CursorShape.SizeBDiagCursor))
            elif self._overlay.inside(sp.x(), sp.y()):
                self._set_cursor(QCursor(Qt.CursorShape.OpenHandCursor))
            else:
                self._set_cursor(QCursor(Qt.CursorShape.ArrowCursor))
            return True

        return False

    def handle_release(self, _sp: QPointF) -> bool:
        if self._resizing:
            self._resizing = False
            self._resize_corner = -1
            if self._overlay is not None:
                self._set_cursor(QCursor(Qt.CursorShape.OpenHandCursor))
            return True
        if self._dragging:
            self._dragging = False
            if self._overlay is not None:
                self._set_cursor(QCursor(Qt.CursorShape.OpenHandCursor))
            return True
        return False
