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

    @property
    def points(self) -> list[tuple[int, int]]:
        """Aktuelle Polygonpunkte (kompatibel zu älteren Tests)."""
        return self._pts

    @points.setter
    def points(self, pts: list[tuple[int, int]]) -> None:
        self._pts = list(pts)

    @property
    def modifiers(self) -> Qt.KeyboardModifier:
        """Modifikatorzustand des aktuellen Lasso-Durchlaufs."""
        return self._mods

    @modifiers.setter
    def modifiers(self, mods: Qt.KeyboardModifier) -> None:
        self._mods = mods

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

    def undo_last_point_if_duplicate(self, x: int, y: int) -> None:
        """Entfernt den letzten Punkt nur dann, wenn er der Doppelklick-Position entspricht.

        Qt liefert vor ``mouseDoubleClickEvent`` bereits ein ``mousePressEvent``.
        Dadurch kann ein Duplikatpunkt entstehen, wenn per Doppelklick nur
        abgeschlossen werden soll. Ein bewusst gesetzter neuer Eckpunkt bleibt
        erhalten.
        """
        if not self._pts:
            return
        if self._pts[-1] == (x, y):
            self._pts.pop()

    def close_to_mask(self, base_mask: np.ndarray) -> np.ndarray:
        pts = self._pts.copy()
        mods = self._mods
        new_mask = self.close_to_selection_mask(base_mask.shape)
        if len(pts) < 3:
            return base_mask
        if mods & Qt.KeyboardModifier.ShiftModifier:
            return base_mask | new_mask
        if mods & Qt.KeyboardModifier.ControlModifier:
            return base_mask & ~new_mask
        return new_mask

    def close_to_selection_mask(self, shape: tuple[int, int]) -> np.ndarray:
        pts = self._pts.copy()
        self.cancel()
        h, w = shape
        new_mask = np.zeros((h, w), dtype=bool)
        if len(pts) < 3:
            return new_mask
        mask_img = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask_img).polygon(pts, fill=255)
        return np.array(mask_img) > 127

    def cancel(self) -> None:
        if self._path_item is not None:
            self._scene.removeItem(self._path_item)
            self._path_item = None
        if self._line_item is not None:
            self._scene.removeItem(self._line_item)
            self._line_item = None
        self._pts.clear()
        self._mods = Qt.KeyboardModifier.NoModifier
