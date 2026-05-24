"""Polygon-Lasso-Interaktion für ``ImageCanvas``.

Kapselt Zustand + Overlay-Objekte des Lasso-Werkzeugs, damit ``canvas.py``
als nächste Refaktor-Phase weniger Zuständigkeiten trägt.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsPathItem, QGraphicsScene


class CanvasLasso:
    """Verwaltet Polygon-Lasso-Zustand und Vorschau-Overlays."""

    def __init__(self, scene: QGraphicsScene) -> None:
        self._scene = scene
        self._pts: list[tuple[int, int]] = []
        self._path_item: QGraphicsPathItem | None = None
        self._line_item: QGraphicsLineItem | None = None
        self._mods = Qt.KeyboardModifier.NoModifier

    @property
    def has_points(self) -> bool:
        return bool(self._pts)

    @property
    def point_count(self) -> int:
        return len(self._pts)

    def set_modifiers_if_first(self, mods: Qt.KeyboardModifier) -> None:
        if not self._pts:
            self._mods = mods

    def add_point(self, x: int, y: int) -> str:
        self._pts.append((x, y))
        path = QPainterPath()
        path.moveTo(*self._pts[0])
        for px, py in self._pts[1:]:
            path.lineTo(px, py)
        pen = QPen(QColor(255, 255, 255, 220), 1.5, Qt.PenStyle.DashLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        if self._path_item is None:
            self._path_item = QGraphicsPathItem()
            self._path_item.setZValue(25)
            self._scene.addItem(self._path_item)
        self._path_item.setPen(pen)
        self._path_item.setPath(path)
        if self._line_item is None:
            line_pen = QPen(QColor(200, 200, 200, 160), 1.2, Qt.PenStyle.DotLine)
            self._line_item = QGraphicsLineItem(x, y, x, y)
            self._line_item.setPen(line_pen)
            self._line_item.setZValue(25)
            self._scene.addItem(self._line_item)
        else:
            self._line_item.setLine(x, y, x, y)
        n = len(self._pts)
        suffix = "e" if n != 1 else ""
        return f"Polygon-Lasso: {n} Punkt{suffix} — Doppelklick zum Abschließen · Esc = abbrechen"

    def update_preview_line(self, x: float, y: float) -> None:
        if self._pts and self._line_item is not None:
            last = self._pts[-1]
            self._line_item.setLine(last[0], last[1], x, y)

    def undo_last_point(self) -> None:
        """Entfernt den zuletzt gesetzten Punkt (z. B. bei Doppelklick-Sequenz)."""
        if self._pts:
            self._pts.pop()

    def close_to_mask(self, base_mask: np.ndarray) -> np.ndarray:
        pts = self._pts.copy()
        mods = self._mods
        self.cancel()
        h, w = base_mask.shape
        mask_img = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask_img).polygon(pts, fill=255)
        new_mask = np.array(mask_img) > 127
        if mods & Qt.KeyboardModifier.ShiftModifier:
            return base_mask | new_mask
        if mods & Qt.KeyboardModifier.ControlModifier:
            return base_mask & ~new_mask
        return new_mask

    def cancel(self) -> None:
        if self._path_item is not None:
            self._scene.removeItem(self._path_item)
            self._path_item = None
        if self._line_item is not None:
            self._scene.removeItem(self._line_item)
            self._line_item = None
        self._pts.clear()
        self._mods = Qt.KeyboardModifier.NoModifier
