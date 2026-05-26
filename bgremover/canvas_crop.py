"""Crop-Overlay-Interaktion für ``ImageCanvas``.

Kapselt Zustand und Mausgesten des Crop-Overlays, damit ``canvas.py``
analog zu ``CanvasHistory`` / ``CanvasLasso`` / ``CanvasSelection`` als
nächste Refaktor-Phase weniger Zuständigkeiten trägt.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QGraphicsScene

from bgremover.crop import CropOverlayItem
from bgremover.image_ops import crop_image, crop_size_for_ratio

if TYPE_CHECKING:
    from bgremover.canvas import ImageCanvas


class CanvasCrop:
    """Verwaltet das Crop-Overlay und seine Drag-/Resize-Gesten."""

    def __init__(
        self,
        scene: QGraphicsScene,
        canvas: "ImageCanvas",
        on_mode_changed: Callable[[bool], None],
    ) -> None:
        self._scene = scene
        self._canvas = canvas
        self._on_mode_changed = on_mode_changed
        self.overlay: CropOverlayItem | None = None
        self._dragging: bool = False
        self._resizing: bool = False
        self._resize_corner: int = -1
        self._drag_start: QPointF = QPointF()
        self._start_pos: QPointF = QPointF()

    # ── Status-Abfragen ──────────────────────────────────────

    @property
    def active(self) -> bool:
        """True, solange ein Crop-Overlay sichtbar ist."""
        return self.overlay is not None

    @property
    def is_resizing(self) -> bool:
        return self._resizing

    @property
    def is_dragging(self) -> bool:
        return self._dragging

    # ── Start / Confirm / Cancel ─────────────────────────────

    def start_circle(self) -> None:
        """Startet den interaktiven Kreis-Zuschnitt."""
        img = self._canvas.image
        if img is None:
            self._canvas.statusMsg.emit("Kein Bild geladen")
            return
        size = min(img.width, img.height)
        self._start(size, size, is_circle=True)

    def start_ratio(self, ratio_w: int, ratio_h: int) -> None:
        """Startet den interaktiven Zuschnitt für ein Seitenverhältnis."""
        img = self._canvas.image
        if img is None:
            self._canvas.statusMsg.emit("Kein Bild geladen")
            return
        cw, ch = crop_size_for_ratio(img.size, ratio_w, ratio_h)
        self._start(cw, ch, is_circle=False)

    def _start(self, cw: int, ch: int, is_circle: bool) -> None:
        img = self._canvas.image
        assert img is not None
        self.cancel_overlay_only()
        self.overlay = CropOverlayItem(img.width, img.height, cw, ch, is_circle)
        self._scene.addItem(self.overlay)
        self._canvas.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self._on_mode_changed(True)
        label = "Kreis" if is_circle else f"{cw} × {ch} px"
        self._canvas.statusMsg.emit(
            f"✂  Ausschnitt verschieben  [{label}]  —  dann ✓ Anwenden klicken")

    def confirm(self) -> None:
        """Wendet den aktuellen Crop-Overlay als Zuschnitt an."""
        img = self._canvas.image
        if self.overlay is None or img is None:
            return
        r = self.overlay.crop_rect()
        cx, cy, cw, ch = r.x(), r.y(), r.width(), r.height()
        is_circle = self.overlay.is_circle
        result = crop_image(img, (cx, cy, cw, ch), is_circle=is_circle)
        if is_circle:
            desc = "Format: Kreis"
        else:
            desc = f"Format: {cw}×{ch} px"
        self.cancel_overlay_only()
        self._on_mode_changed(False)
        self._canvas._apply_pil(result, desc=desc)
        self._canvas.statusMsg.emit(
            f"✂  Zugeschnitten: {result.width} × {result.height} px")

    def cancel(self) -> None:
        """Bricht den Zuschnitt ohne Änderung ab."""
        self.cancel_overlay_only()
        self._on_mode_changed(False)
        # Tool-Cursor wiederherstellen
        self._canvas.set_tool(self._canvas._tool)
        self._canvas.statusMsg.emit("Zuschnitt abgebrochen")

    def cancel_overlay_only(self) -> None:
        """Entfernt das Overlay-Item, ohne ``cropModeChanged`` zu feuern.

        Wird beim Laden eines neuen Bildes verwendet, wenn das Overlay
        bislang gar nicht aktiv war und die Mode-Signale nicht doppelt
        durchgereicht werden sollen.
        """
        if self.overlay is not None:
            self._scene.removeItem(self.overlay)
            self.overlay = None
        self._dragging = False
        self._resizing = False
        self._resize_corner = -1

    # ── Maus-Events ──────────────────────────────────────────

    def handle_press(self, btn: Qt.MouseButton, sp: QPointF) -> bool:
        """Press-Event im Crop-Modus; True => Event konsumiert."""
        if self.overlay is None:
            return False
        if btn == Qt.MouseButton.LeftButton:
            corner = self.overlay.corner_hit(sp.x(), sp.y())
            if corner >= 0:
                self._resizing = True
                self._resize_corner = corner
                self._drag_start = sp
                self._canvas.setCursor(QCursor(
                    Qt.CursorShape.SizeFDiagCursor if corner in (0, 3)
                    else Qt.CursorShape.SizeBDiagCursor))
            elif self.overlay.inside(sp.x(), sp.y()):
                self._dragging = True
                self._drag_start = sp
                self._start_pos = self.overlay.top_left
                self._canvas.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        return True

    def handle_move(self, sp: QPointF) -> bool:
        """Move-Event; True => Event vollständig vom Crop-Modus konsumiert."""
        if self._resizing and self.overlay is not None:
            self.overlay.resize_from_corner(
                self._resize_corner, sp.x(), sp.y())
            cw, ch = self.overlay.size
            self._canvas.statusMsg.emit(
                f"⇲ Größe: {int(round(cw))} × {int(round(ch))} px")
            return True
        if self._dragging and self.overlay is not None:
            delta = sp - self._drag_start
            self.overlay.set_position(
                self._start_pos.x() + delta.x(),
                self._start_pos.y() + delta.y())
            return True
        if self.overlay is not None:
            corner = self.overlay.corner_hit(sp.x(), sp.y())
            if corner >= 0:
                self._canvas.setCursor(QCursor(
                    Qt.CursorShape.SizeFDiagCursor if corner in (0, 3)
                    else Qt.CursorShape.SizeBDiagCursor))
            elif self.overlay.inside(sp.x(), sp.y()):
                self._canvas.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            else:
                self._canvas.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            return True
        return False

    def handle_release(self) -> bool:
        """Release-Event; True => Event vom Crop-Modus konsumiert."""
        if self._resizing:
            self._resizing = False
            self._resize_corner = -1
            if self.overlay is not None:
                self._canvas.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            return True
        if self._dragging:
            self._dragging = False
            if self.overlay is not None:
                self._canvas.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            return True
        return False
