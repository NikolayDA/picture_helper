"""Crop-Overlay (rein visuell – die Canvas steuert die Interaktion).

Werkzeug-Namen liegen in ``constants``;
``CropOverlayItem`` benötigt sie nicht.
"""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRect, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QGraphicsObject,
    QStyleOptionGraphicsItem,
    QWidget,
)


class CropOverlayItem(QGraphicsObject):
    """Zeigt den verschiebbaren und skalierbaren Ausschnittrahmen auf der Canvas."""

    # Griff-Radius in Szene-Pixeln innerhalb dessen ein Klick als Resize gilt
    HANDLE_R = 16.0

    def __init__(self, img_w: int, img_h: int,
                 crop_w: int, crop_h: int, is_circle: bool = False) -> None:
        super().__init__()
        self._iw = img_w;  self._ih = img_h
        self._cw = float(crop_w); self._ch = float(crop_h)
        # Seitenverhältnis merken (für proportionales Resize)
        self._aspect = self._cw / self._ch if self._ch > 0 else 1.0
        self.is_circle = is_circle
        # Startposition: zentriert
        self._cx = (img_w - crop_w) / 2.0
        self._cy = (img_h - crop_h) / 2.0
        self.setZValue(10)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)   # Canvas übernimmt Events

    # ── Corners: index 0=TL 1=TR 2=BL 3=BR ──────────────────
    def _corners(self) -> list[QPointF]:
        return [
            QPointF(self._cx,              self._cy),
            QPointF(self._cx + self._cw,   self._cy),
            QPointF(self._cx,              self._cy + self._ch),
            QPointF(self._cx + self._cw,   self._cy + self._ch),
        ]

    def corner_hit(self, sx: float, sy: float) -> int:
        """Gibt Corner-Index (0-3) zurück falls Klick auf Griff, sonst -1."""
        for i, c in enumerate(self._corners()):
            if abs(sx - c.x()) <= self.HANDLE_R and abs(sy - c.y()) <= self.HANDLE_R:
                return i
        return -1

    def set_position(self, cx: float, cy: float) -> None:
        self._cx = max(0.0, min(cx, self._iw - self._cw))
        self._cy = max(0.0, min(cy, self._ih - self._ch))
        self.update()

    def resize_from_corner(self, corner_idx: int, sx: float, sy: float) -> None:
        """Skaliert den Ausschnitt proportional vom gegenüberliegenden Eck-Ankerpunkt."""
        # Ankerpunkt ist die gegenüberliegende Ecke
        if corner_idx == 0:    # TL gezogen → Anker BR
            anchor_x = self._cx + self._cw
            anchor_y = self._cy + self._ch
            dx = anchor_x - sx
            dy = anchor_y - sy
        elif corner_idx == 1:  # TR gezogen → Anker BL
            anchor_x = self._cx
            anchor_y = self._cy + self._ch
            dx = sx - anchor_x
            dy = anchor_y - sy
        elif corner_idx == 2:  # BL gezogen → Anker TR
            anchor_x = self._cx + self._cw
            anchor_y = self._cy
            dx = anchor_x - sx
            dy = sy - anchor_y
        else:                  # BR gezogen → Anker TL
            anchor_x = self._cx
            anchor_y = self._cy
            dx = sx - anchor_x
            dy = sy - anchor_y

        # Größe aus der größeren Delta-Achse, Proportionen halten
        MIN_PX = 20.0
        new_w = max(MIN_PX, dx) if dx / self._aspect >= dy else max(MIN_PX, dy * self._aspect)
        new_h = new_w / self._aspect

        # Nicht über Bildrand – gemeinsamen Skalierungsfaktor anwenden,
        # damit das Seitenverhältnis erhalten bleibt
        scale = min(self._iw / new_w, self._ih / new_h, 1.0)
        new_w *= scale
        new_h *= scale

        self._cw = new_w
        self._ch = new_h

        # Neue Ecken-Position aus Anker berechnen
        if corner_idx == 0:
            self._cx = anchor_x - new_w
            self._cy = anchor_y - new_h
        elif corner_idx == 1:
            self._cx = anchor_x
            self._cy = anchor_y - new_h
        elif corner_idx == 2:
            self._cx = anchor_x - new_w
            self._cy = anchor_y
        else:
            self._cx = anchor_x
            self._cy = anchor_y

        # Clamp an Bildrand
        self._cx = max(0.0, min(self._cx, self._iw - self._cw))
        self._cy = max(0.0, min(self._cy, self._ih - self._ch))
        self.update()

    def crop_rect(self) -> QRect:
        """Ausschnitt in Bildpixel-Koordinaten."""
        return QRect(int(round(self._cx)), int(round(self._cy)),
                     int(round(self._cw)), int(round(self._ch)))

    def inside(self, sx: float, sy: float) -> bool:
        return (self._cx <= sx <= self._cx + self._cw and
                self._cy <= sy <= self._cy + self._ch)

    @property
    def top_left(self) -> QPointF:
        """Linke obere Ecke des Ausschnitts in Bild-Koordinaten."""
        return QPointF(self._cx, self._cy)

    @property
    def size(self) -> tuple[float, float]:
        """Aktuelle (Breite, Höhe) des Ausschnitts."""
        return self._cw, self._ch

    def boundingRect(self) -> QRectF:
        # Marge für Eck-Handles und zentrierten Hinweistext
        margin = 220.0
        return QRectF(-margin, -margin,
                      self._iw + 2 * margin, self._ih + 2 * margin)

    def paint(self, painter: QPainter | None,
              option: QStyleOptionGraphicsItem | None = None,
              widget: QWidget | None = None) -> None:
        if painter is None:
            return
        # ── Dunkles Außen-Overlay ──────────────────────────────
        outer = QPainterPath()
        outer.addRect(QRectF(0, 0, self._iw, self._ih))
        inner = QPainterPath()
        crop_rf = QRectF(self._cx, self._cy, self._cw, self._ch)
        if self.is_circle:
            inner.addEllipse(crop_rf)
        else:
            inner.addRect(crop_rf)
        painter.fillPath(outer.subtracted(inner), QColor(0, 0, 0, 150))

        # ── Rahmen ────────────────────────────────────────────
        painter.setBrush(Qt.BrushStyle.NoBrush)
        dash_pen = QPen(QColor(255, 255, 255, 220), 1.5, Qt.PenStyle.DashLine)
        solid_pen = QPen(QColor(255, 255, 255, 255), 2.5, Qt.PenStyle.SolidLine,
                         Qt.PenCapStyle.SquareCap)
        if self.is_circle:
            painter.setPen(dash_pen)
            painter.drawEllipse(crop_rf)
        else:
            painter.setPen(dash_pen)
            painter.drawRect(crop_rf)
            # Drittel-Raster (Rule of Thirds)
            painter.setPen(QPen(QColor(255, 255, 255, 55), 0.7))
            for i in (1, 2):
                xi = self._cx + self._cw * i / 3
                yi = self._cy + self._ch * i / 3
                painter.drawLine(QPointF(xi, self._cy),
                                 QPointF(xi, self._cy + self._ch))
                painter.drawLine(QPointF(self._cx, yi),
                                 QPointF(self._cx + self._cw, yi))

        # ── Eck-Griffe (Resize-Handles) ───────────────────────
        hs = 10.0
        painter.setPen(solid_pen)
        painter.setBrush(QBrush(QColor(74, 144, 217, 230)))
        for c in self._corners():
            painter.drawRect(QRectF(c.x() - hs / 2, c.y() - hs / 2, hs, hs))

        # ── Hinweis-Text ──────────────────────────────────────
        mid_x = self._cx + self._cw / 2
        mid_y = self._cy + self._ch / 2
        painter.setPen(QPen(QColor(255, 255, 255, 160)))
        hint = "⇲ Ecken ziehen zum Skalieren  •  Mitte ziehen zum Verschieben"
        painter.drawText(
            QRectF(mid_x - 200, mid_y - 10, 400, 20),
            Qt.AlignmentFlag.AlignCenter,
            hint
        )
