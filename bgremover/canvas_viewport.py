"""Viewport-Operationen für ``ImageCanvas``.

Kapselt Zoom, Pan, Fit-to-View und das Refreshen des Bild-Pixmaps –
analog zu CanvasCrop / CanvasHistory / CanvasLasso / CanvasSelection /
CanvasTransform.

Das Mouse-Routing für Pan bleibt in ``ImageCanvas.mousePressEvent`` /
``mouseMoveEvent`` / ``mouseReleaseEvent``; diese Klasse stellt mit
``start_pan_if_requested`` / ``update_pan`` / ``stop_pan`` nur die
Hilfsmethoden bereit und beantwortet ``is_panning`` für die
Routing-Entscheidung.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import Image
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QWidget

from bgremover.constants import (
    _ZOOM_CTRL_MAX_PCT,
    _ZOOM_CTRL_MIN_PCT,
    _ZOOM_FACTOR,
)
from bgremover.image_utils import pil_to_qpixmap

if TYPE_CHECKING:
    from bgremover.canvas import ImageCanvas


class CanvasViewport:
    """Verwaltet Zoom-, Pan- und Fit-Operationen für den ``ImageCanvas``."""

    # Zoom-Grenzen: verhindert dass Bild auf 0 schrumpft (kein Klick mehr
    # möglich) oder so groß wird, dass Qt-Rasterung sichtbar wird.
    ZOOM_MIN = 0.05
    ZOOM_MAX = 40.0

    def __init__(
        self,
        canvas: ImageCanvas,
        scene: QGraphicsScene,
        img_item: QGraphicsPixmapItem,
        viewport_widget: QWidget,
    ) -> None:
        self._canvas = canvas
        self._scene = scene
        self._img_item = img_item
        self._vp = viewport_widget
        self._panning: bool = False
        self._pan_start: QPointF = QPointF()
        # Fixier-Lock der Zoom-Kontrolle (#464): reiner UI-Zustand, friert den
        # aktuellen Zoomwert gegen Mausrad und +/−-Buttons ein.
        self._zoom_locked: bool = False

    # ── Status-Abfragen ──────────────────────────────────────

    @property
    def is_panning(self) -> bool:
        return self._panning

    @property
    def zoom_locked(self) -> bool:
        """True, solange der Zoomwert fixiert ist (#464)."""
        return self._zoom_locked

    @property
    def zoom_percent(self) -> float:
        """Aktueller Zoom in Prozent (100 = 1:1-Pixelabbildung)."""
        return self._canvas.transform().m11() * 100.0

    # ── View-Operationen ─────────────────────────────────────

    def fit_to_view(self) -> None:
        """Passt das Bild in die Ansicht ein."""
        self._canvas.fitInView(self._img_item, Qt.AspectRatioMode.KeepAspectRatio)
        self._notify_zoom()

    def _notify_zoom(self) -> None:
        """Meldet den aktuellen Zoomwert an die Anzeige (Zoom-Kontrolle, #464)."""
        self._canvas.zoomChanged.emit(self.zoom_percent)

    def refresh_image(self, img: Image.Image | None) -> None:
        """Rendert das aktuelle PIL-Bild neu in den ``QGraphicsPixmapItem``."""
        if img is None:
            return
        px = pil_to_qpixmap(img)
        self._img_item.setPixmap(px)
        self._scene.setSceneRect(QRectF(px.rect()))
        self._img_item.update()
        self._vp.update()

    def zoom(self, factor: float) -> None:
        """Wendet einen Skalierungsfaktor an, beschnitten auf ``[ZOOM_MIN, ZOOM_MAX]``.

        Bei fixiertem Zoom (#464) ein No-op – der Wert bleibt eingefroren,
        bis der Fixier-Lock wieder gelöst wird.
        """
        if self._zoom_locked:
            return
        new_scale = self._canvas.transform().m11() * factor
        if self.ZOOM_MIN <= new_scale <= self.ZOOM_MAX:
            self._canvas.scale(factor, factor)
            self._notify_zoom()

    def handle_wheel(self, angle_y: int) -> None:
        """Zoomt auf Basis eines Rad-Deltas (``angle_y > 0`` zoomt rein)."""
        self.zoom(_ZOOM_FACTOR if angle_y > 0 else 1 / _ZOOM_FACTOR)

    def step_zoom(self, delta_pct: int) -> None:
        """Zoomt in Prozent-Schritten der Zoom-Kontrolle (#464).

        ``zoomBy``-Logik des Prototyps: Zielwert = aktueller Prozentwert plus
        *delta_pct*, geklemmt auf ``[_ZOOM_CTRL_MIN_PCT, _ZOOM_CTRL_MAX_PCT]``.
        Bei fixiertem Zoom ein No-op.
        """
        if self._zoom_locked:
            return
        current = self.zoom_percent
        target = max(_ZOOM_CTRL_MIN_PCT, min(_ZOOM_CTRL_MAX_PCT, current + delta_pct))
        if target == current:
            return
        self._canvas.scale(target / current, target / current)
        self._notify_zoom()

    def set_zoom_locked(self, locked: bool) -> None:
        """Friert den aktuellen Zoomwert ein bzw. gibt ihn wieder frei (#464)."""
        self._zoom_locked = locked

    # ── Pan-Hilfsmethoden (Routing bleibt im Canvas) ─────────

    def start_pan_if_requested(
        self,
        btn: Qt.MouseButton,
        mods: Qt.KeyboardModifier,
        pos: QPointF,
    ) -> bool:
        """Startet Pan-Modus (Alt+LMB oder MMB); ``True`` => Event konsumiert."""
        if (btn == Qt.MouseButton.MiddleButton or
                (btn == Qt.MouseButton.LeftButton and
                 mods & Qt.KeyboardModifier.AltModifier)):
            self.start_pan(pos)
            return True
        return False

    def start_pan(self, pos: QPointF) -> None:
        """Startet den Pan-Modus bedingungslos (Move-Werkzeug, #456)."""
        self._panning = True
        self._pan_start = pos
        self._canvas.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def update_pan(self, pos: QPointF) -> None:
        """Verschiebt die Scrollbars relativ zum letzten Pan-Punkt."""
        delta = pos - self._pan_start
        self._pan_start = pos
        hbar = self._canvas.horizontalScrollBar()
        vbar = self._canvas.verticalScrollBar()
        assert hbar is not None and vbar is not None
        hbar.setValue(hbar.value() - int(delta.x()))
        vbar.setValue(vbar.value() - int(delta.y()))

    def stop_pan(self) -> None:
        """Beendet den Pan-Modus (Cursor wird vom Canvas via ``set_tool`` wiederhergestellt)."""
        self._panning = False
