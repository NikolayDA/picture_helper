"""Crop-Overlay-Interaktion für ``ImageCanvas``.

Kapselt Zustand und Mausgesten des Crop-Overlays, damit ``canvas.py``
analog zu ``CanvasLasso`` / ``CanvasSelection`` weniger
Zuständigkeiten trägt.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QGraphicsScene

from bgremover.crop import CropOverlayItem
from bgremover.height_map import crop_height_field
from bgremover.i18n import tr
from bgremover.image_ops import crop_image, crop_size_for_ratio
from bgremover.status_messages import StatusMessages as SM

if TYPE_CHECKING:
    from bgremover.canvas import ImageCanvas


class CanvasCrop:
    """Verwaltet das Crop-Overlay und seine Drag-/Resize-Gesten."""

    def __init__(
        self,
        scene: QGraphicsScene,
        canvas: ImageCanvas,
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
            self._canvas.statusMsg.emit(SM.KEIN_BILD_GELADEN)
            return
        size = min(img.width, img.height)
        self._start(size, size, is_circle=True)

    def start_ratio(self, ratio_w: int, ratio_h: int) -> None:
        """Startet den interaktiven Zuschnitt für ein Seitenverhältnis."""
        img = self._canvas.image
        if img is None:
            self._canvas.statusMsg.emit(SM.KEIN_BILD_GELADEN)
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
        if is_circle:
            self._canvas.statusMsg.emit(tr("canvas.crop_start_circle"))
        else:
            self._canvas.statusMsg.emit(tr("canvas.crop_start_ratio", w=cw, h=ch))

    def confirm(self) -> None:
        """Wendet den aktuellen Crop-Overlay als Zuschnitt an."""
        img = self._canvas.image
        if self.overlay is None or img is None:
            return
        r = self.overlay.crop_rect()
        cx, cy, cw, ch = r.x(), r.y(), r.width(), r.height()
        is_circle = self.overlay.is_circle
        if is_circle:
            desc = tr("history.desc.crop_circle")
        else:
            desc = tr("history.desc.crop_ratio", w=cw, h=ch)
        self._finish_mode()
        # Zuschnitt ändert die Canvas-Größe → über apply_geometry auf alle Ebenen
        # einheitlich (Canvas-Zuschnitt; bei genau einer Ebene wie bisher).
        self._canvas.apply_geometry(
            lambda im: crop_image(im, (cx, cy, cw, ch), is_circle=is_circle),
            desc=desc,
            height_transform=lambda field: crop_height_field(
                field, (cx, cy, cw, ch), is_circle=is_circle
            ),
        )
        result = self._canvas.image
        assert result is not None
        self._canvas.statusMsg.emit(tr(
            "canvas.cropped", w=result.width, h=result.height))

    def cancel(self) -> None:
        """Bricht den Zuschnitt ohne Änderung ab."""
        if self._finish_mode():
            self._canvas.statusMsg.emit(tr("canvas.crop_cancelled"))

    def discard(self) -> bool:
        """Verwirft einen aktiven Crop still und stellt den Tool-Cursor wieder her."""
        return self._finish_mode()

    def _finish_mode(self) -> bool:
        """Beendet den Crop-Modus vollständig; ``False`` wenn keiner aktiv war."""
        if self.overlay is None:
            return False
        self.cancel_overlay_only()
        self._on_mode_changed(False)
        self._canvas.set_tool(self._canvas.current_tool)
        return True

    def cancel_overlay_only(self) -> None:
        """Entfernt das Overlay-Item, ohne ``cropModeChanged`` zu feuern.

        Interne Primitive für das Ersetzen oder vollständige Beenden eines
        Overlays; Signal und Cursor stellt ``_finish_mode`` zentral wieder her.
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
                tr("canvas.crop_size", w=int(round(cw)), h=int(round(ch))))
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
