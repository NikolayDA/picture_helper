#!/usr/bin/env python3
"""
BgRemover — Hintergrund-Entfernungs & Ersatz-Tool für macOS
Starten: python3 BgRemover.py
"""

import sys
import os
import io
import numpy as np
from collections import deque
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QColorDialog,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsObject,
    QToolButton, QButtonGroup, QGroupBox, QStatusBar,
    QFrame, QSizePolicy, QMessageBox, QTabWidget, QSpinBox, QListWidget,
    QScrollArea
)
from PyQt6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QBrush,
    QDragEnterEvent, QDropEvent, QAction, QKeySequence,
    QCursor, QPalette, QPen, QIcon, QPolygonF, QPainterPath
)

from PyQt6.QtCore import Qt, QRectF, QPointF, QSize, QRect, pyqtSignal, QThread, QObject, QEvent
from PIL import Image, ImageDraw

try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

# ─────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ─────────────────────────────────────────────────────────────

def pil_to_qpixmap(img: Image.Image) -> QPixmap:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    w, h = img.size
    raw = img.tobytes("raw", "RGBA")
    qi = QImage(raw, w, h, w * 4, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qi.copy())


def pil_to_numpy(img: Image.Image) -> np.ndarray:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    return np.asarray(img).copy()


def numpy_to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def flood_fill(arr: np.ndarray, x: int, y: int, tolerance: int) -> np.ndarray:
    """Flood-Fill: gibt Boolean-Maske der zusammenhängenden Fläche zurück."""
    h, w = arr.shape[:2]
    mask = np.zeros((h, w), dtype=bool)
    if not (0 <= x < w and 0 <= y < h):
        return mask
    target = arr[y, x, :3].astype(np.int32)
    visited = np.zeros((h, w), dtype=bool)
    queue = deque([(x, y)])
    visited[y, x] = True
    while queue:
        cx, cy = queue.popleft()
        diff = int(np.max(np.abs(arr[cy, cx, :3].astype(np.int32) - target)))
        if diff <= tolerance:
            mask[cy, cx] = True
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx]:
                    visited[ny, nx] = True
                    queue.append((nx, ny))
    return mask


def mask_to_overlay(mask: np.ndarray, w: int, h: int) -> QPixmap:
    """Konvertiert Boolean-Maske → halbtransparente rote Overlay-QPixmap."""
    overlay = np.zeros((h, w, 4), dtype=np.uint8)
    overlay[mask] = [220, 60, 60, 130]
    raw = overlay.tobytes()
    qi = QImage(raw, w, h, w * 4, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qi.copy())


# ─────────────────────────────────────────────────────────────
# Cursor-Generatoren
# ─────────────────────────────────────────────────────────────

def make_wand_cursor() -> QCursor:
    """Fadenkreuz-Cursor mit goldenem Mittelpunkt für den Zauberstab."""
    sz = 32
    pm = QPixmap(sz, sz)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    white = QColor(255, 255, 255, 220)
    black = QColor(0, 0, 0, 120)
    # Schwarzer Schatten (leicht versetzt)
    p.setPen(QPen(black, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
    for dx, dy in ((1,1),):
        p.drawLine(16+dx, 2+dy, 16+dx, 13+dy)
        p.drawLine(16+dx, 19+dy, 16+dx, 30+dy)
        p.drawLine(2+dx, 16+dy, 13+dx, 16+dy)
        p.drawLine(19+dx, 16+dy, 30+dx, 16+dy)
    # Weißes Fadenkreuz
    p.setPen(QPen(white, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
    p.drawLine(16, 2, 16, 13)
    p.drawLine(16, 19, 16, 30)
    p.drawLine(2, 16, 13, 16)
    p.drawLine(19, 16, 30, 16)
    # Goldener Mittelpunkt
    p.setPen(QPen(QColor(255, 210, 40, 255), 1))
    p.setBrush(QBrush(QColor(255, 210, 40, 230)))
    p.drawEllipse(13, 13, 6, 6)
    p.end()
    return QCursor(pm, 16, 16)


def make_brush_cursor(diameter: int) -> QCursor:
    """Runder Pinsel-Cursor der die tatsächliche Pinselgröße zeigt."""
    d = max(diameter, 6)
    pad = 6
    sz = d + pad * 2
    pm = QPixmap(sz, sz)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    cx = sz // 2
    # Äußerer schwarzer Ring
    p.setPen(QPen(QColor(0, 0, 0, 160), 2.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(pad - 1, pad - 1, d + 2, d + 2)
    # Innerer weißer Ring
    p.setPen(QPen(QColor(255, 255, 255, 230), 1.5))
    p.drawEllipse(pad, pad, d, d)
    # Kleines Kreuz in der Mitte
    p.setPen(QPen(QColor(255, 255, 255, 200), 1))
    p.drawLine(cx - 3, cx, cx + 3, cx)
    p.drawLine(cx, cx - 3, cx, cx + 3)
    p.end()
    return QCursor(pm, cx, cx)


def make_eraser_cursor(diameter: int) -> QCursor:
    """Quadratischer Radiergummi-Cursor."""
    d = max(diameter, 6)
    pad = 6
    sz = d + pad * 2
    pm = QPixmap(sz, sz)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    cx = sz // 2
    # Äußerer schwarzer Rahmen
    p.setPen(QPen(QColor(0, 0, 0, 160), 2.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(pad - 1, pad - 1, d + 2, d + 2, 3, 3)
    # Innerer gelber Rahmen
    p.setPen(QPen(QColor(255, 200, 60, 230), 1.5))
    p.drawRoundedRect(pad, pad, d, d, 2, 2)
    # Kleines Kreuz in der Mitte
    p.setPen(QPen(QColor(255, 200, 60, 200), 1))
    p.drawLine(cx - 3, cx, cx + 3, cx)
    p.drawLine(cx, cx - 3, cx, cx + 3)
    p.end()
    return QCursor(pm, cx, cx)


# ─────────────────────────────────────────────────────────────
# Icon-Generatoren für Toolbar-Buttons
# ─────────────────────────────────────────────────────────────

def make_tool_icon(name: str, size: int = 28) -> QIcon:
    """Lädt PNG aus icons/-Ordner neben BgRemover.py via Pillow, fällt auf gezeichnetes Icon zurück."""
    # Mehrere Suchpfade für robuste Erkennung
    _candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons"),
        os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),  "icons"),
        os.path.join(os.getcwd(), "icons"),
    ]
    for _icon_dir in _candidates:
        png_path = os.path.join(_icon_dir, f"{name}.png")
        if os.path.isfile(png_path):
            try:
                from PIL import Image as _Img
                pil_img = _Img.open(png_path).convert("RGBA").resize(
                    (size, size), _Img.LANCZOS)
                data = pil_img.tobytes("raw", "RGBA")
                qimg = QImage(data, size, size,
                              QImage.Format.Format_RGBA8888)
                pm = QPixmap.fromImage(qimg)
                if not pm.isNull():
                    return QIcon(pm)
            except Exception:
                pass
            break
    # ── Fallback: gezeichnetes Vektor-Icon ──────────────────────────────────
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size

    if name == "wand":
        # Zauberstab: diagonale Linie + Sterne
        p.setPen(QPen(QColor(220, 220, 220), 2.2,
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(int(s*0.22), int(s*0.78), int(s*0.65), int(s*0.35))
        p.setBrush(QBrush(QColor(220, 220, 220)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(s*0.10), int(s*0.66), int(s*0.24), int(s*0.24))
        # Sterne (Kreuzform)
        gold = QColor(255, 210, 50)
        def star(cx, cy, r):
            p.setPen(QPen(gold, 1.5, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap))
            p.drawLine(cx, cy-r, cx, cy+r)
            p.drawLine(cx-r, cy, cx+r, cy)
        star(int(s*0.75), int(s*0.22), int(s*0.12))
        star(int(s*0.88), int(s*0.48), int(s*0.08))
        star(int(s*0.60), int(s*0.12), int(s*0.07))

    elif name == "brush":
        # Pinsel: Griff + Borsten
        p.setPen(QPen(QColor(190, 190, 190), 2.5,
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(int(s*0.72), int(s*0.12), int(s*0.38), int(s*0.62))
        # Ferrule (Metallring)
        p.setPen(QPen(QColor(160, 160, 170), 2))
        p.drawLine(int(s*0.42), int(s*0.57), int(s*0.30), int(s*0.69))
        # Borsten (blau)
        p.setPen(QPen(QColor(80, 150, 240), 3,
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(int(s*0.28), int(s*0.71), int(s*0.18), int(s*0.88))
        p.setPen(QPen(QColor(60, 130, 220), 2,
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(int(s*0.34), int(s*0.72), int(s*0.26), int(s*0.90))
        p.drawLine(int(s*0.22), int(s*0.70), int(s*0.12), int(s*0.86))

    elif name == "eraser":
        # Radiergummi: abgerundetes Rechteck + Streifen
        p.setPen(QPen(QColor(160, 160, 160), 1.5))
        p.setBrush(QBrush(QColor(240, 185, 90, 220)))
        p.drawRoundedRect(int(s*0.12), int(s*0.38),
                          int(s*0.76), int(s*0.36), 3, 3)
        # Trennstreifen
        p.setPen(QPen(QColor(200, 120, 50, 200), 2))
        tx = int(s * 0.45)
        p.drawLine(tx, int(s*0.38), tx, int(s*0.74))
        # Wischspur (Schatten unten)
        p.setPen(QPen(QColor(120, 120, 120, 100), 1))
        p.setBrush(QBrush(QColor(100, 100, 100, 60)))
        p.drawRoundedRect(int(s*0.12), int(s*0.70),
                          int(s*0.76), int(s*0.10), 2, 2)

    elif name == "ai":
        # KI: Blitz / Neuron-Symbol
        bolt = QPolygonF([
            QPointF(s*0.55, s*0.10),
            QPointF(s*0.28, s*0.52),
            QPointF(s*0.48, s*0.52),
            QPointF(s*0.42, s*0.90),
            QPointF(s*0.72, s*0.46),
            QPointF(s*0.52, s*0.46),
        ])
        p.setPen(QPen(QColor(80, 190, 255), 1.5))
        p.setBrush(QBrush(QColor(80, 190, 255, 200)))
        p.drawPolygon(bolt)

    elif name == "open":
        # Ordner öffnen
        p.setPen(QPen(QColor(200, 200, 200), 1.5))
        p.setBrush(QBrush(QColor(200, 170, 80, 200)))
        p.drawRoundedRect(int(s*0.10), int(s*0.38),
                          int(s*0.80), int(s*0.46), 3, 3)
        p.setBrush(QBrush(QColor(220, 190, 100, 200)))
        p.drawRoundedRect(int(s*0.10), int(s*0.30),
                          int(s*0.40), int(s*0.14), 3, 3)
        # Pfeil
        p.setPen(QPen(QColor(255, 255, 255, 220), 2,
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        mx, my = int(s*0.50), int(s*0.56)
        p.drawLine(mx, my+int(s*0.14), mx, my-int(s*0.10))
        p.drawLine(mx-int(s*0.10), my, mx, my-int(s*0.12))
        p.drawLine(mx+int(s*0.10), my, mx, my-int(s*0.12))

    elif name == "save":
        # Diskette / Speichern
        p.setPen(QPen(QColor(160, 160, 160), 1.5))
        p.setBrush(QBrush(QColor(80, 140, 200, 200)))
        p.drawRoundedRect(int(s*0.12), int(s*0.12),
                          int(s*0.76), int(s*0.76), 4, 4)
        # Etikettfläche
        p.setBrush(QBrush(QColor(220, 220, 220, 200)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(int(s*0.26), int(s*0.12),
                   int(s*0.48), int(s*0.32))
        # Spirale (Schreib-Nut)
        p.setBrush(QBrush(QColor(80, 140, 200, 200)))
        p.drawRect(int(s*0.38), int(s*0.12),
                   int(s*0.14), int(s*0.32))
        # Bodenfach
        p.setPen(QPen(QColor(160, 160, 160), 1))
        p.setBrush(QBrush(QColor(60, 110, 170, 200)))
        p.drawRect(int(s*0.22), int(s*0.56),
                   int(s*0.56), int(s*0.28))

    elif name == "undo":
        # Gebogener Rückgängig-Pfeil
        pen = QPen(QColor(180, 200, 230), max(2, int(s * 0.10)),
                   Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                   Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        from PyQt6.QtCore import QRectF as _QRectF
        import math
        arc_rect = _QRectF(s*0.15, s*0.20, s*0.65, s*0.55)
        p.drawArc(arc_rect, 30 * 16, 240 * 16)   # Bogen von 30° bis 270°
        # Pfeilspitze links oben
        tip_x, tip_y = s*0.155, s*0.415
        p.setPen(QPen(QColor(180, 200, 230), max(2, int(s * 0.10)),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                      Qt.PenJoinStyle.RoundJoin))
        p.drawLine(QPointF(tip_x, tip_y),
                   QPointF(tip_x + s*0.16, tip_y - s*0.14))
        p.drawLine(QPointF(tip_x, tip_y),
                   QPointF(tip_x + s*0.12, tip_y + s*0.18))

    elif name == "restore":
        # Kreisförmiger Refresh-Pfeil (zwei Halbbögen + Spitzen)
        pen = QPen(QColor(150, 210, 160), max(2, int(s * 0.10)),
                   Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                   Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        from PyQt6.QtCore import QRectF as _QRectF2
        arc_r = _QRectF2(s*0.15, s*0.15, s*0.70, s*0.70)
        p.drawArc(arc_r,  20 * 16, 160 * 16)   # oberer Bogen
        p.drawArc(arc_r, 200 * 16, 160 * 16)   # unterer Bogen
        # obere Pfeilspitze (rechts)
        p.drawLine(QPointF(s*0.83, s*0.415), QPointF(s*0.68, s*0.22))
        p.drawLine(QPointF(s*0.83, s*0.415), QPointF(s*0.62, s*0.50))
        # untere Pfeilspitze (links)
        p.drawLine(QPointF(s*0.17, s*0.585), QPointF(s*0.32, s*0.78))
        p.drawLine(QPointF(s*0.17, s*0.585), QPointF(s*0.38, s*0.50))

    p.end()
    return QIcon(pm)


def make_checker_brush(size: int = 14) -> QBrush:
    """Schachbrettmuster für transparente Bereiche."""
    px = QPixmap(size * 2, size * 2)
    px.fill(QColor(170, 170, 170))
    p = QPainter(px)
    p.fillRect(0, 0, size, size, QColor(210, 210, 210))
    p.fillRect(size, size, size, size, QColor(210, 210, 210))
    p.end()
    return QBrush(px)


# ─────────────────────────────────────────────────────────────
# KI-Worker (läuft in eigenem Thread)
# ─────────────────────────────────────────────────────────────

class AIWorker(QObject):
    finished = pyqtSignal(object)   # PIL Image
    error = pyqtSignal(str)

    def __init__(self, pil_image: Image.Image):
        super().__init__()
        self._img = pil_image

    def run(self):
        try:
            buf = io.BytesIO()
            self._img.save(buf, format="PNG")
            result_bytes = rembg_remove(buf.getvalue())
            result = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ─────────────────────────────────────────────────────────────
# Crop-Overlay (rein visuell – Canvas steuert Interaktion)
# ─────────────────────────────────────────────────────────────

class CropOverlayItem(QGraphicsObject):
    """Zeigt den verschiebbaren und skalierbaren Ausschnittrahmen auf der Canvas."""

    # Griff-Radius in Szene-Pixeln innerhalb dessen ein Klick als Resize gilt
    HANDLE_R = 16.0

    def __init__(self, img_w: int, img_h: int,
                 crop_w: int, crop_h: int, is_circle: bool = False):
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
    def _corners(self):
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

    def set_position(self, cx: float, cy: float):
        self._cx = max(0.0, min(cx, self._iw - self._cw))
        self._cy = max(0.0, min(cy, self._ih - self._ch))
        self.update()

    def resize_from_corner(self, corner_idx: int, sx: float, sy: float):
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
        if dx / self._aspect >= dy:
            new_w = max(MIN_PX, dx)
        else:
            new_w = max(MIN_PX, dy * self._aspect)
        new_h = new_w / self._aspect

        # Nicht über Bildrand
        new_w = min(new_w, float(self._iw))
        new_h = min(new_h, float(self._ih))

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

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._iw, self._ih)

    def paint(self, painter: QPainter, option, widget):
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


# ─────────────────────────────────────────────────────────────
# Bild-Canvas
# ─────────────────────────────────────────────────────────────

TOOL_WAND   = "wand"
TOOL_BRUSH  = "brush"
TOOL_ERASER = "eraser"


class ImageCanvas(QGraphicsView):
    statusMsg      = pyqtSignal(str)
    historyChanged = pyqtSignal(list)   # list[str] – Beschreibungen, neueste zuerst
    cropModeChanged = pyqtSignal(bool)  # True = Crop-Overlay aktiv

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(make_checker_brush())
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)

        self._img_item     = QGraphicsPixmapItem()
        self._overlay_item = QGraphicsPixmapItem()
        self._scene.addItem(self._img_item)
        self._scene.addItem(self._overlay_item)
        self._overlay_item.setZValue(1)

        self._pil:      Image.Image | None = None
        self._original: Image.Image | None = None
        self._arr:      np.ndarray  | None = None
        self._mask:     np.ndarray  | None = None
        # Undo-Stack: (Image, Beschreibung der Aktion die dazu führte)
        self._undo:     deque = deque(maxlen=20)

        self._tool      = TOOL_WAND
        self._tolerance = 30
        self._brush_r   = 15
        self._panning   = False
        self._pan_start = QPointF()
        self._drawing   = False

        # Crop-Overlay-Zustand
        self._crop_overlay:      CropOverlayItem | None = None
        self._crop_dragging:     bool    = False
        self._crop_drag_start:   QPointF = QPointF()
        self._crop_start_pos:    QPointF = QPointF()
        self._crop_resizing:     bool    = False   # True = Resize-Drag läuft
        self._crop_resize_corner: int    = -1      # 0-3 welche Ecke

    # ── Laden ────────────────────────────────────────────────

    def load_image(self, path: str):
        img = Image.open(path).convert("RGBA")
        self._original = img.copy()
        self._undo.clear()
        self._cancel_crop_overlay()
        self._apply_pil(img, push=False)
        self.fitInView(self._img_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.statusMsg.emit(f"Geöffnet: {Path(path).name}  ({img.width} × {img.height} px)")

    def _apply_pil(self, img: Image.Image, push: bool = True, desc: str = "Bearbeitung"):
        if push and self._pil is not None:
            self._undo.append((self._pil.copy(), desc))
            self.historyChanged.emit(
                [d for _, d in reversed(list(self._undo))])
        self._pil  = img
        self._arr  = pil_to_numpy(img)
        self._mask = np.zeros((img.height, img.width), dtype=bool)
        self._refresh_image()
        self._refresh_overlay()

    def _refresh_image(self):
        if self._pil:
            px = pil_to_qpixmap(self._pil)
            self._img_item.setPixmap(px)
            self._scene.setSceneRect(QRectF(px.rect()))
            self._img_item.update()
            self.viewport().update()

    def _refresh_overlay(self):
        if self._mask is not None and self._pil:
            h, w = self._mask.shape
            self._overlay_item.setPixmap(mask_to_overlay(self._mask, w, h))

    # ── Undo / Original ──────────────────────────────────────

    def undo(self):
        if self._crop_overlay is not None:
            self.cancel_crop(); return
        if self._undo:
            img, desc = self._undo.pop()
            # Direkt setzen ohne erneuten Push
            self._pil  = img
            self._arr  = pil_to_numpy(img)
            self._mask = np.zeros((img.height, img.width), dtype=bool)
            self._refresh_image()
            self._refresh_overlay()
            self.historyChanged.emit(
                [d for _, d in reversed(list(self._undo))])
            self.statusMsg.emit(f"↩  Rückgängig: {desc}")
        else:
            self.statusMsg.emit("Nichts mehr zum Rückgängigmachen")

    def undo_to(self, steps: int):
        """Mehrere Schritte auf einmal rückgängig machen."""
        actual = min(steps, len(self._undo))
        if actual <= 0:
            return
        img, desc = None, ""
        for _ in range(actual):
            img, desc = self._undo.pop()
        self._pil  = img
        self._arr  = pil_to_numpy(img)
        self._mask = np.zeros((img.height, img.width), dtype=bool)
        self._refresh_image()
        self._refresh_overlay()
        self.historyChanged.emit(
            [d for _, d in reversed(list(self._undo))])
        self.statusMsg.emit(f"↩  {actual} Schritt(e) rückgängig  (bis: {desc})")

    def restore_original(self):
        if self._original:
            self._cancel_crop_overlay()
            self._undo.clear()
            self._pil  = self._original.copy()
            self._arr  = pil_to_numpy(self._pil)
            self._mask = np.zeros((self._pil.height, self._pil.width), dtype=bool)
            self._refresh_image()
            self._refresh_overlay()
            self.historyChanged.emit([])
            self.statusMsg.emit("🔄  Original wiederhergestellt")

    def clear_selection(self):
        if self._mask is not None:
            self._mask[:] = False
            self._refresh_overlay()
            self.statusMsg.emit("Auswahl aufgehoben")

    # ── Tool-Einstellungen ───────────────────────────────────

    def set_tool(self, tool: str):
        self._tool = tool
        if tool == TOOL_WAND:
            self.setCursor(make_wand_cursor())
        elif tool == TOOL_BRUSH:
            self.setCursor(make_brush_cursor(self._brush_r * 2))
        elif tool == TOOL_ERASER:
            self.setCursor(make_eraser_cursor(self._brush_r * 2))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def set_tolerance(self, v: int):
        self._tolerance = v

    def set_brush_size(self, v: int):
        self._brush_r = max(1, v // 2)
        # Cursor sofort aktualisieren
        if self._tool == TOOL_BRUSH:
            self.setCursor(make_brush_cursor(v))
        elif self._tool == TOOL_ERASER:
            self.setCursor(make_eraser_cursor(v))

    # ── Operationen ──────────────────────────────────────────

    def apply_remove(self, _checked=False):
        try:
            if not self._check_selection():
                return
            arr = self._arr.copy()
            arr[self._mask, 3] = 0
            self._apply_pil(numpy_to_pil(arr), desc="Hintergrund entfernt")
            self.viewport().update()
            self.statusMsg.emit("Hintergrund entfernt (transparent)")
        except Exception as e:
            import traceback; traceback.print_exc()
            self.statusMsg.emit(f"Fehler beim Entfernen: {e}")

    def apply_replace(self, color: QColor):
        try:
            if not self._check_selection():
                return
            arr = self._arr.copy()
            arr[self._mask] = [color.red(), color.green(), color.blue(), 255]
            self._apply_pil(numpy_to_pil(arr), desc=f"Farbe ersetzt ({color.name()})")
            self.viewport().update()
            self.statusMsg.emit(f"Hintergrund ersetzt: {color.name()}")
        except Exception as e:
            import traceback; traceback.print_exc()
            self.statusMsg.emit(f"Fehler beim Ersetzen: {e}")

    def apply_ai_result(self, img: Image.Image):
        self._apply_pil(img, desc="KI-Hintergrundentfernung")
        self.statusMsg.emit("✅ KI-Hintergrundentfernung abgeschlossen")

    def save_image(self, path: str):
        if self._pil is None:
            return
        ext = Path(path).suffix.lower()
        if ext in (".jpg", ".jpeg"):
            # Transparenz auf weißem Hintergrund einbetten
            bg = Image.new("RGBA", self._pil.size, (255, 255, 255, 255))
            bg.paste(self._pil, mask=self._pil.split()[3])
            bg.convert("RGB").save(path, quality=95)
        elif ext == ".webp":
            self._pil.save(path, "WEBP", quality=90)
        else:
            self._pil.save(path, "PNG")
        self.statusMsg.emit(f"💾 Gespeichert: {Path(path).name}")

    def _check_selection(self) -> bool:
        if self._pil is None:
            self.statusMsg.emit("Kein Bild geladen")
            return False
        if self._mask is None or not self._mask.any():
            self.statusMsg.emit("Keine Auswahl – erst Bereich mit Zauberstab oder Pinsel auswählen")
            return False
        return True

    # ── Maus-Events ──────────────────────────────────────────

    def _to_img_xy(self, event) -> tuple[int, int]:
        sp = self.mapToScene(event.position().toPoint())
        return int(sp.x()), int(sp.y())

    def mousePressEvent(self, event):
        if self._pil is None:
            return super().mousePressEvent(event)

        btn  = event.button()
        sp   = self.mapToScene(event.position().toPoint())
        mods = QApplication.keyboardModifiers()

        # ── Crop-Modus ────────────────────────────────────────
        if self._crop_overlay is not None:
            if btn == Qt.MouseButton.LeftButton:
                corner = self._crop_overlay.corner_hit(sp.x(), sp.y())
                if corner >= 0:
                    # Resize-Drag starten
                    self._crop_resizing      = True
                    self._crop_resize_corner = corner
                    self._crop_drag_start    = sp
                    self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor
                                          if corner in (0, 3)
                                          else Qt.CursorShape.SizeBDiagCursor))
                elif self._crop_overlay.inside(sp.x(), sp.y()):
                    self._crop_dragging   = True
                    self._crop_drag_start = sp
                    self._crop_start_pos  = QPointF(
                        self._crop_overlay._cx, self._crop_overlay._cy)
                    self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            return  # alle anderen Aktionen im Crop-Modus blockieren

        # ── Pan: Alt+Drag oder Mittelklick ────────────────────
        if (btn == Qt.MouseButton.MiddleButton or
                (btn == Qt.MouseButton.LeftButton and
                 mods & Qt.KeyboardModifier.AltModifier)):
            self._panning   = True
            self._pan_start = event.position()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            return

        if btn != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)

        x, y = int(sp.x()), int(sp.y())

        if self._tool == TOOL_WAND:
            w, h = self._pil.size
            if 0 <= x < w and 0 <= y < h:
                new = flood_fill(self._arr, x, y, self._tolerance)
                if mods & Qt.KeyboardModifier.ShiftModifier:
                    self._mask |= new
                elif mods & Qt.KeyboardModifier.ControlModifier:
                    self._mask &= ~new
                else:
                    self._mask = new
                self._refresh_overlay()
                self.statusMsg.emit(f"Auswahl: {int(self._mask.sum()):,} Pixel")
        else:
            self._drawing = True
            self._paint_brush(x, y)

    def mouseMoveEvent(self, event):
        sp = self.mapToScene(event.position().toPoint())

        # ── Crop-Resize ───────────────────────────────────────
        if self._crop_resizing and self._crop_overlay is not None:
            self._crop_overlay.resize_from_corner(
                self._crop_resize_corner, sp.x(), sp.y())
            cw = int(round(self._crop_overlay._cw))
            ch = int(round(self._crop_overlay._ch))
            self.statusMsg.emit(f"⇲ Größe: {cw} × {ch} px")
            return

        # ── Crop-Drag ─────────────────────────────────────────
        if self._crop_dragging and self._crop_overlay is not None:
            delta = sp - self._crop_drag_start
            self._crop_overlay.set_position(
                self._crop_start_pos.x() + delta.x(),
                self._crop_start_pos.y() + delta.y())
            return

        # Cursor im Crop-Modus anpassen
        if self._crop_overlay is not None:
            corner = self._crop_overlay.corner_hit(sp.x(), sp.y())
            if corner >= 0:
                self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor
                                       if corner in (0, 3)
                                       else Qt.CursorShape.SizeBDiagCursor))
            elif self._crop_overlay.inside(sp.x(), sp.y()):
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            return

        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y()))
            return
        if self._drawing and event.buttons() & Qt.MouseButton.LeftButton:
            self._paint_brush(int(sp.x()), int(sp.y()))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._crop_resizing:
            self._crop_resizing = False
            self._crop_resize_corner = -1
            if self._crop_overlay is not None:
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            return
        if self._crop_dragging:
            self._crop_dragging = False
            if self._crop_overlay is not None:
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            return
        if self._panning:
            self._panning = False
            self.set_tool(self._tool)
            return
        self._drawing = False
        super().mouseReleaseEvent(event)

    def _paint_brush(self, cx: int, cy: int):
        if self._mask is None or self._pil is None:
            return
        r  = self._brush_r
        h, w = self._mask.shape
        y0, y1 = max(0, cy - r), min(h, cy + r + 1)
        x0, x1 = max(0, cx - r), min(w, cx + r + 1)
        yy, xx = np.ogrid[y0:y1, x0:x1]
        circle = (yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2
        if self._tool == TOOL_BRUSH:
            self._mask[y0:y1, x0:x1][circle] = True
        else:
            self._mask[y0:y1, x0:x1][circle] = False
        self._refresh_overlay()

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    # ── Drag & Drop ──────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):          # ← PFLICHT: ohne dies wird Drop abgelehnt
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if Path(path).suffix.lower() in (
                    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".gif"):
                self.load_image(path)
                return
        self.statusMsg.emit("Format nicht unterstützt")

    # ── Ecken abrunden ───────────────────────────────────────

    def apply_round_corners(self, radius: int):
        """Rundet die Ecken des Bildes mit dem gegebenen Radius ab."""
        if self._pil is None:
            self.statusMsg.emit("Kein Bild geladen")
            return
        if radius <= 0:
            self.statusMsg.emit("Radius muss > 0 sein")
            return
        img = self._pil.convert("RGBA")
        w, h = img.size
        r = min(radius, w // 2, h // 2)

        # Neue Alpha-Maske: abgerundetes Rechteck
        mask = Image.new("L", (w, h), 0)
        draw_m = ImageDraw.Draw(mask)
        draw_m.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)

        # Vorhandene Alpha mit neuer Maske UND-verknüpfen
        orig_a = np.array(img.split()[3])
        new_a  = np.minimum(orig_a, np.array(mask))
        channels = list(img.split())
        channels[3] = Image.fromarray(new_a.astype(np.uint8))
        result = Image.merge("RGBA", channels)
        self._apply_pil(result, desc=f"Ecken abgerundet ({r} px)")
        self.statusMsg.emit(f"Ecken abgerundet: {r} px Radius")

    # ── Drehen ───────────────────────────────────────────────

    def apply_rotate(self, degrees: int):
        """Dreht das Bild um den angegebenen Winkel (gegen den Uhrzeigersinn).
        Bei 90° / 270° werden Breite und Höhe getauscht.
        Bei beliebigen Winkeln wird die Canvas so vergrößert, dass nichts abgeschnitten wird.
        """
        if self._pil is None:
            self.statusMsg.emit("Kein Bild geladen")
            return
        img = self._pil.convert("RGBA")

        if degrees % 90 == 0:
            # Verlustfreie 90°-Schritte – kein Qualitätsverlust, exakte Pixelgröße
            result = img.rotate(degrees, expand=True)
        else:
            # Freier Winkel: transparente Außenbereiche
            result = img.rotate(degrees, expand=True,
                                resample=Image.Resampling.BICUBIC)

        direction = "↺" if degrees > 0 else "↻"
        self._apply_pil(result, desc=f"{direction} Gedreht {abs(degrees)}°")
        self.statusMsg.emit(
            f"{direction} Gedreht: {abs(degrees)}°  "
            f"({result.width} × {result.height} px)"
        )

    # ── Spiegeln ─────────────────────────────────────────────

    def apply_flip(self, horizontal: bool):
        """Spiegelt das Bild horizontal oder vertikal."""
        if self._pil is None:
            self.statusMsg.emit("Kein Bild geladen")
            return
        img = self._pil.convert("RGBA")
        if horizontal:
            result = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            self._apply_pil(result, desc="↔ Horizontal gespiegelt")
            self.statusMsg.emit("↔ Horizontal gespiegelt")
        else:
            result = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            self._apply_pil(result, desc="↕ Vertikal gespiegelt")
            self.statusMsg.emit("↕ Vertikal gespiegelt")

    # ── Ausgabeformat – Crop-Overlay ─────────────────────────

    def start_crop_circle(self):
        """Startet den interaktiven Kreis-Zuschnitt."""
        if self._pil is None:
            self.statusMsg.emit("Kein Bild geladen"); return
        size = min(self._pil.width, self._pil.height)
        self._start_crop_overlay(size, size, is_circle=True)

    def start_crop_ratio(self, ratio_w: int, ratio_h: int):
        """Startet den interaktiven Zuschnitt für ein Seitenverhältnis."""
        if self._pil is None:
            self.statusMsg.emit("Kein Bild geladen"); return
        iw, ih = self._pil.size
        if iw / ih > ratio_w / ratio_h:
            cw, ch = int(ih * ratio_w / ratio_h), ih
        else:
            cw, ch = iw, int(iw * ratio_h / ratio_w)
        self._start_crop_overlay(cw, ch, is_circle=False)

    def _start_crop_overlay(self, cw: int, ch: int, is_circle: bool):
        self._cancel_crop_overlay()
        self._crop_overlay = CropOverlayItem(
            self._pil.width, self._pil.height, cw, ch, is_circle)
        self._scene.addItem(self._crop_overlay)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.cropModeChanged.emit(True)
        label = "Kreis" if is_circle else f"{cw} × {ch} px"
        self.statusMsg.emit(
            f"✂  Ausschnitt verschieben  [{label}]  —  dann ✓ Anwenden klicken")

    def confirm_crop(self):
        """Wendet den aktuellen Crop-Overlay als Zuschnitt an."""
        if self._crop_overlay is None or self._pil is None:
            return
        r = self._crop_overlay.crop_rect()
        cx, cy, cw, ch = r.x(), r.y(), r.width(), r.height()
        img = self._pil.convert("RGBA")
        cropped = img.crop((cx, cy, cx + cw, cy + ch))

        if self._crop_overlay.is_circle:
            mask = Image.new("L", (cw, ch), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, cw - 1, ch - 1], fill=255)
            orig_a = np.array(cropped.split()[3])
            new_a  = np.minimum(orig_a, np.array(mask))
            channels = list(cropped.split())
            channels[3] = Image.fromarray(new_a.astype(np.uint8))
            result = Image.merge("RGBA", channels)
            desc = "Format: Kreis"
        else:
            result = cropped
            desc = f"Format: {cw}×{ch} px"

        self._cancel_crop_overlay()
        self.cropModeChanged.emit(False)
        self._apply_pil(result, desc=desc)
        self.statusMsg.emit(f"✂  Zugeschnitten: {result.width} × {result.height} px")

    def cancel_crop(self):
        """Bricht den Zuschnitt ab ohne Änderung."""
        self._cancel_crop_overlay()
        self.cropModeChanged.emit(False)
        self.set_tool(self._tool)
        self.statusMsg.emit("Zuschnitt abgebrochen")

    def _cancel_crop_overlay(self):
        if self._crop_overlay is not None:
            self._scene.removeItem(self._crop_overlay)
            self._crop_overlay = None
        self._crop_dragging      = False
        self._crop_resizing      = False
        self._crop_resize_corner = -1


# ─────────────────────────────────────────────────────────────
# Haupt-Fenster
# ─────────────────────────────────────────────────────────────

BTN_STYLE = """
    QPushButton {{
        background: {bg}; color: {fg}; border: none;
        border-radius: 6px; padding: 7px 10px; font-size: 12px;
    }}
    QPushButton:hover {{ background: {hover}; }}
    QPushButton:disabled {{ background: #333; color: #666; }}
"""

TOOL_STYLE = """
    QToolButton {
        color: #ccc; font-size: 24px; border: none;
        border-radius: 9px; background: #3a3a3a;
    }
    QToolButton:checked  { background: #4a90d9; color: white; }
    QToolButton:hover    { background: #4f4f4f; }
    QToolButton:disabled { color: #555; background: #2a2a2a; }
"""

GRP_STYLE = """
    QGroupBox {
        color: #ddd; border: 1px solid #3f3f3f;
        border-radius: 7px; margin-top: 10px; font-size: 12px;
        font-weight: bold;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; }
"""

SLD_STYLE = """
    QSlider::groove:horizontal { height: 4px; background: #3a3a3a; border-radius: 2px; }
    QSlider::handle:horizontal {
        background: #4a90d9; width: 14px; height: 14px;
        margin: -5px 0; border-radius: 7px;
    }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BgRemover Pro")
        self.setMinimumSize(1100, 720)
        self._bg_color   = QColor(255, 255, 255)
        self._ai_thread: QThread | None = None
        self._build_ui()
        self._build_menu()

    # ── UI aufbauen ──────────────────────────────────────────

    def _build_ui(self):
        root_w = QWidget()
        self.setCentralWidget(root_w)
        root = QHBoxLayout(root_w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())

        # Canvas + Crop-Bestätigungsleiste in vertikalem Container
        canvas_container = QWidget()
        canvas_container.setStyleSheet("background: transparent;")
        cv_lay = QVBoxLayout(canvas_container)
        cv_lay.setContentsMargins(0, 0, 0, 0)
        cv_lay.setSpacing(0)

        # ── Crop-Bestätigungsleiste (initial versteckt) ───────
        self._crop_bar = QFrame()
        self._crop_bar.setStyleSheet(
            "QFrame { background: #1e3020; border-bottom: 1px solid #3a7a4a; }")
        self._crop_bar.setFixedHeight(46)
        cb_lay = QHBoxLayout(self._crop_bar)
        cb_lay.setContentsMargins(14, 4, 14, 4); cb_lay.setSpacing(10)
        crop_lbl = QLabel("✂  Ausschnitt positionieren, dann bestätigen:")
        crop_lbl.setStyleSheet("color: #8fdd9f; font-size: 12px; font-weight: bold;"
                               " background: transparent;")
        cb_lay.addWidget(crop_lbl)
        cb_lay.addStretch()
        btn_confirm = QPushButton("✓  Zuschnitt anwenden")
        btn_confirm.setStyleSheet(
            "QPushButton { background:#2a6a2a; color:white; border:none;"
            " border-radius:5px; padding:7px 16px; font-size:12px; font-weight:bold; }"
            "QPushButton:hover { background:#3a8a3a; }")
        btn_confirm.clicked.connect(lambda: self._canvas.confirm_crop())
        btn_cancel = QPushButton("✗  Abbrechen")
        btn_cancel.setStyleSheet(
            "QPushButton { background:#5a2525; color:white; border:none;"
            " border-radius:5px; padding:7px 14px; font-size:12px; }"
            "QPushButton:hover { background:#7a3535; }")
        btn_cancel.clicked.connect(lambda: self._canvas.cancel_crop())
        cb_lay.addWidget(btn_confirm)
        cb_lay.addWidget(btn_cancel)
        self._crop_bar.setVisible(False)
        cv_lay.addWidget(self._crop_bar)

        self._canvas = ImageCanvas()
        self._canvas.statusMsg.connect(self.statusBar().showMessage)
        self._canvas.historyChanged.connect(self._on_history_changed)
        self._canvas.cropModeChanged.connect(self._on_crop_mode_changed)
        cv_lay.addWidget(self._canvas, 1)

        root.addWidget(canvas_container, 1)
        root.addWidget(self._build_right_panel())

        sb = QStatusBar()
        sb.setStyleSheet("QStatusBar { background:#1a1a1a; color:#777; font-size:11px; border-top:1px solid #333; }")
        self.setStatusBar(sb)
        sb.showMessage("Bild öffnen: Datei → Öffnen  oder  per Drag & Drop auf die Arbeitsfläche")

    def _build_toolbar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(66)
        frame.setStyleSheet("QFrame { background: #242424; border-right: 1px solid #3a3a3a; }")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(9, 16, 9, 16)
        lay.setSpacing(8)

        self._btn_grp = QButtonGroup(self)
        self._btn_grp.setExclusive(True)

        def tbtn(icon_name: str, tip: str, tool: str) -> QToolButton:
            b = QToolButton()
            b.setIcon(make_tool_icon(icon_name, 38))
            b.setIconSize(QSize(38, 38))
            b.setToolTip(tip)
            b.setCheckable(True)
            b.setFixedSize(54, 54)
            b.setStyleSheet(TOOL_STYLE)
            b.clicked.connect(lambda checked=False, t=tool: self._canvas.set_tool(t))
            self._btn_grp.addButton(b)
            lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
            return b

        self._btn_wand   = tbtn("wand",
            "Zauberstab\nKlick wählt Farbfläche (Flood Fill)\n"
            "Shift = addieren  ·  Ctrl = subtrahieren", TOOL_WAND)
        self._btn_brush  = tbtn("brush",
            "Pinsel\nBereiche manuell zur Auswahl hinzufügen", TOOL_BRUSH)
        self._btn_eraser = tbtn("eraser",
            "Radiergummi\nAuswahl-Bereiche wieder entfernen", TOOL_ERASER)
        self._btn_wand.setChecked(True)

        # Trennlinie
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#3a3a3a")
        lay.addSpacing(4); lay.addWidget(sep); lay.addSpacing(4)

        self._btn_ai = QToolButton()
        self._btn_ai.setIcon(make_tool_icon("ai", 38))
        self._btn_ai.setIconSize(QSize(38, 38))
        self._btn_ai.setToolTip(
            "KI-Hintergrundentfernung (rembg)\nEntfernt den Hintergrund vollautomatisch"
            if REMBG_AVAILABLE else
            "rembg nicht installiert\n→ bash setup_bgremover.sh")
        self._btn_ai.setFixedSize(54, 54)
        self._btn_ai.setStyleSheet(TOOL_STYLE)
        self._btn_ai.setEnabled(REMBG_AVAILABLE)
        self._btn_ai.clicked.connect(self._run_ai)
        lay.addWidget(self._btn_ai, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Trennlinie
        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color:#3a3a3a")
        lay.addSpacing(4); lay.addWidget(sep2); lay.addSpacing(4)

        # Rückgängig + Original
        HIST_STYLE = """
            QToolButton {
                color: #bbb; font-size: 20px; border: none;
                border-radius: 9px; background: #2e2e2e;
            }
            QToolButton:hover    { background: #3e3e3e; }
            QToolButton:pressed  { background: #252525; }
            QToolButton:disabled { color: #444; background: #222; }
        """

        def hist_btn(icon_name: str, tip: str, slot) -> QToolButton:
            b = QToolButton()
            b.setIcon(make_tool_icon(icon_name, 36))
            b.setIconSize(QSize(36, 36))
            b.setToolTip(tip)
            b.setFixedSize(54, 54)
            b.setStyleSheet(HIST_STYLE)
            b.clicked.connect(slot)
            lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
            return b

        hist_btn("undo",     "Rückgängig  (Cmd+Z)\nLetzten Bearbeitungsschritt rückgängig machen",
                 lambda: self._canvas.undo())
        hist_btn("restore",  "Original wiederherstellen\nAlle Bearbeitungen verwerfen",
                 lambda: self._canvas.restore_original())

        lay.addStretch()

        def mini_btn(icon_name: str, tip: str, slot) -> QToolButton:
            b = QToolButton()
            b.setIcon(make_tool_icon(icon_name, 32))
            b.setIconSize(QSize(32, 32))
            b.setToolTip(tip)
            b.setFixedSize(54, 46)
            b.setStyleSheet(TOOL_STYLE)
            b.clicked.connect(slot)
            lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
            return b

        mini_btn("open", "Bild öffnen  (Cmd+O)",   self._open_image)
        mini_btn("save", "Bild speichern  (Cmd+S)", self._save_image)
        return frame

    def _build_right_panel(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(340)
        frame.setStyleSheet("QFrame { background: #1a1a1a; border-left: 1px solid #333; }")
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Styles ───────────────────────────────────────────
        TAB_STYLE = """
            QTabWidget::pane { border: none; background: #1a1a1a; }
            QTabBar { background: #141414; }
            QTabBar::tab {
                background: #1e1e1e;
                color: #666;
                padding: 10px 0px;
                min-width: 82px;
                font-size: 12px;
                border: none;
                border-bottom: 3px solid transparent;
            }
            QTabBar::tab:selected {
                color: #e0e0e0;
                background: #1a1a1a;
                border-bottom: 3px solid #4a90d9;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                color: #aaa;
                background: #242424;
            }
        """

        def sec(title: str, accent: str = "#4a90d9") -> tuple:
            """Sektion ohne QGroupBox – farbiger Titel + dünne Trennlinie."""
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            v = QVBoxLayout(container)
            v.setSpacing(10)
            v.setContentsMargins(0, 14, 0, 6)
            # Titel-Label in Akzentfarbe
            title_lbl = QLabel(title)
            title_lbl.setStyleSheet(f"""
                color: {accent};
                font-size: 13px;
                font-weight: bold;
                background: transparent;
                padding-bottom: 5px;
                border-bottom: 1px solid #2e2e2e;
            """)
            v.addWidget(title_lbl)
            return container, v

        def lbl(text: str, color: str = "#888", size: int = 11) -> QLabel:
            l = QLabel(text)
            l.setStyleSheet(f"color: {color}; font-size: {size}px; background: transparent;")
            l.setWordWrap(True)
            return l

        def hdivider() -> QFrame:
            f = QFrame()
            f.setFrameShape(QFrame.Shape.HLine)
            f.setStyleSheet("background: #2a2a2a; max-height: 1px; margin: 4px 0;")
            return f

        def scroll_tab() -> tuple:
            """Returns (outer_widget, inner_layout) mit ScrollArea."""
            outer_w = QWidget()
            outer_w.setStyleSheet("background: #1a1a1a;")
            outer_lay = QVBoxLayout(outer_w)
            outer_lay.setContentsMargins(0, 0, 0, 0)
            outer_lay.setSpacing(0)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setStyleSheet("""
                QScrollArea { background: #1a1a1a; border: none; }
                QScrollBar:vertical {
                    background: #1a1a1a; width: 6px; margin: 0;
                }
                QScrollBar::handle:vertical {
                    background: #3a3a3a; border-radius: 3px; min-height: 20px;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            """)

            inner_w = QWidget()
            inner_w.setStyleSheet("background: #1a1a1a;")
            inner_lay = QVBoxLayout(inner_w)
            inner_lay.setContentsMargins(14, 14, 14, 14)
            inner_lay.setSpacing(12)

            scroll.setWidget(inner_w)
            outer_lay.addWidget(scroll)
            return outer_w, inner_lay

        def btn(label: str, bg: str, fg: str, hover: str,
                tooltip: str = "", height: int = 36,
                icon_name: str = "") -> QPushButton:
            b = QPushButton(label)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {bg}; color: {fg}; border: none;
                    border-radius: 8px; padding: 0 14px;
                    font-size: 12px; font-weight: 500;
                    min-height: {height}px;
                    text-align: center;
                }}
                QPushButton:hover {{ background: {hover}; }}
                QPushButton:pressed {{ background: {bg}; }}
                QPushButton:disabled {{ background: #252525; color: #555; }}
            """)
            if icon_name:
                b.setIcon(make_tool_icon(icon_name, 22))
                b.setIconSize(QSize(22, 22))
            if tooltip:
                b.setToolTip(tooltip)
            return b

        def slider_row(lo: int, hi: int, val: int,
                       tip: str = "") -> QSlider:
            s = QSlider(Qt.Orientation.Horizontal)
            s.setRange(lo, hi); s.setValue(val)
            s.setStyleSheet(SLD_STYLE)
            if tip:
                s.setToolTip(tip)
            return s

        # ── Tab-Widget ────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setStyleSheet(TAB_STYLE)
        tabs.setUsesScrollButtons(False)   # niemals Scroll-Pfeile — alle Tabs sichtbar
        outer.addWidget(tabs)

        # ════════════════════════════════════════════════════
        # Tab 1 – Auswahl  🎯
        # ════════════════════════════════════════════════════
        t1, l1 = scroll_tab()
        tabs.addTab(t1, "🎯 Auswahl")
        tabs.setTabToolTip(0, "Auswahl – Zauberstab, Pinsel, Radiergummi")

        g_tool, gt = sec("Werkzeug", "#4a90d9")
        hint_box = QWidget()
        hint_box.setStyleSheet("background:#1e2a38; border-radius:7px;")
        hint_lay = QVBoxLayout(hint_box)
        hint_lay.setContentsMargins(10, 8, 10, 8)
        hint_lay.setSpacing(3)
        for txt in [
            "🪄  Zauberstab — Farbfläche auswählen",
            "🖌  Pinsel — Auswahl aufmalen",
            "◻  Radiergummi — Auswahl entfernen",
        ]:
            hint_lay.addWidget(lbl(txt, "#7aacdd", 11))
        hint_lay.addWidget(hdivider())
        hint_lay.addWidget(lbl("Shift+Klick  →  Auswahl addieren", "#888", 10))
        hint_lay.addWidget(lbl("Ctrl+Klick   →  Auswahl subtrahieren", "#888", 10))
        gt.addWidget(hint_box)
        l1.addWidget(g_tool)

        g_sel, gs = sec("Einstellungen", "#4a90d9")
        self._lbl_tol = lbl("Toleranz (Zauberstab):  30", "#aaa")
        self._sld_tol = slider_row(0, 255, 30,
            "Steuert wie ähnlich Farben sein müssen um ausgewählt zu werden.\n"
            "Niedrig = nur sehr ähnliche Farben · Hoch = viele Farbtöne")
        self._sld_tol.valueChanged.connect(lambda v: (
            self._canvas.set_tolerance(v),
            self._lbl_tol.setText(f"Toleranz (Zauberstab):  {v}")
        ))
        gs.addWidget(self._lbl_tol)
        gs.addWidget(self._sld_tol)
        gs.addWidget(hdivider())
        self._lbl_brush = lbl("Pinselgröße:  30 px", "#aaa")
        self._sld_brush = slider_row(4, 200, 30,
            "Größe des Pinsel-/Radiergummi-Werkzeugs in Pixeln")
        self._sld_brush.valueChanged.connect(lambda v: (
            self._canvas.set_brush_size(v),
            self._lbl_brush.setText(f"Pinselgröße:  {v} px")
        ))
        gs.addWidget(self._lbl_brush)
        gs.addWidget(self._sld_brush)
        l1.addWidget(g_sel)

        btn_clr = btn("Auswahl aufheben", "#2a2a2a", "#c0c0c0", "#363636",
                      "Hebt die aktuelle Auswahl auf (auch: Esc-Taste)",
                      icon_name="clear_sel")
        btn_clr.clicked.connect(lambda _=False: self._canvas.clear_selection())
        l1.addWidget(btn_clr)
        l1.addStretch()

        # ════════════════════════════════════════════════════
        # Tab 2 – Hintergrund  🖼
        # ════════════════════════════════════════════════════
        t2, l2 = scroll_tab()
        tabs.addTab(t2, "🖼 Hintergr.")
        tabs.setTabToolTip(1, "Hintergrund – Entfernen, Farbe ersetzen, Verlauf")

        g_bg, gb = sec("Hintergrund bearbeiten", "#e05555")
        btn_rem = btn("Entfernen (transparent)", "#6a1a1a", "white", "#882020",
                      "Macht den ausgewählten Bereich vollständig transparent.\n"
                      "Tipp: Zuerst mit Zauberstab Hintergrund auswählen.",
                      height=38, icon_name="transparency")
        btn_rem.clicked.connect(lambda _=False: self._canvas.apply_remove())
        gb.addWidget(btn_rem)

        gb.addWidget(hdivider())
        gb.addWidget(lbl("Farbe wählen und Auswahl einfärben:", "#888"))
        color_row = QHBoxLayout(); color_row.setSpacing(8)
        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(38, 38)
        self._color_btn.setToolTip("Klicken um Ersatz-Hintergrundfarbe zu wählen")
        self._color_btn.setStyleSheet(
            "QPushButton { border-radius:6px; border:2px solid #555; }"
            "QPushButton:hover { border-color: #4a90d9; }")
        self._color_btn.clicked.connect(lambda _=False: self._pick_color())
        self._update_color_btn()
        color_row.addWidget(self._color_btn)
        btn_repl = btn("Farbe ersetzen", "#143a5a", "white", "#1e5080",
                       "Füllt den ausgewählten Bereich mit der gewählten Farbe",
                       icon_name="bg")
        btn_repl.clicked.connect(lambda _=False: self._canvas.apply_replace(self._bg_color))
        color_row.addWidget(btn_repl, 1)
        gb.addLayout(color_row)
        l2.addWidget(g_bg)

        g_hist, gh = sec("Verlauf", "#888")
        gh.addWidget(lbl("Doppelklick auf Eintrag → zu diesem Schritt zurück", "#666", 10))
        self._history_list = QListWidget()
        self._history_list.setStyleSheet("""
            QListWidget {
                background: #141414; color: #bbb; border: 1px solid #2a2a2a;
                border-radius: 6px; font-size: 11px;
            }
            QListWidget::item { padding: 6px 10px; border-bottom: 1px solid #1e1e1e; }
            QListWidget::item:selected { background: #1e3a5a; color: #7aacdd; }
            QListWidget::item:hover:!selected { background: #202020; }
        """)
        self._history_list.setFixedHeight(160)
        self._history_list.setToolTip(
            "Verlauf aller Bearbeitungsschritte.\n"
            "Doppelklick auf einen Eintrag springt zu diesem Schritt zurück.")
        self._history_list.itemDoubleClicked.connect(self._undo_to_item)
        gh.addWidget(self._history_list)
        l2.addWidget(g_hist)
        l2.addStretch()

        # ════════════════════════════════════════════════════
        # Tab 3 – Transform  ⟲
        # ════════════════════════════════════════════════════
        t3, l3 = scroll_tab()
        tabs.addTab(t3, "⟲ Trans.")
        tabs.setTabToolTip(2, "Transform – Drehen, Spiegeln")

        g_rot, gr2 = sec("Drehen", "#e09a30")
        ROT_BG = "#2e2510"; ROT_FG = "#f0c060"; ROT_HV = "#4a3a18"

        # Schnell-Drehung
        gr2.addWidget(lbl("Schnell-Drehung:", "#888"))
        row_q1 = QHBoxLayout(); row_q1.setSpacing(6)
        for label, deg, tip in [
            ("↺ 90° links",   90,  "90° gegen den Uhrzeigersinn drehen"),
            ("↻ 90° rechts", -90, "90° im Uhrzeigersinn drehen"),
        ]:
            b = btn(label, ROT_BG, ROT_FG, ROT_HV, tip)
            b.clicked.connect(lambda _=False, d=deg: self._canvas.apply_rotate(d))
            row_q1.addWidget(b)
        gr2.addLayout(row_q1)

        row_q2 = QHBoxLayout(); row_q2.setSpacing(6)
        for label, deg, tip in [
            ("↺ 180°",  180, "Bild um 180° drehen"),
            ("↺ 270°", -270, "270° gegen den Uhrzeigersinn (= 90° rechts)"),
        ]:
            b = btn(label, ROT_BG, ROT_FG, ROT_HV, tip)
            b.clicked.connect(lambda _=False, d=deg: self._canvas.apply_rotate(d))
            row_q2.addWidget(b)
        gr2.addLayout(row_q2)

        gr2.addWidget(hdivider())
        gr2.addWidget(lbl("Freier Winkel:", "#888"))
        row_free = QHBoxLayout(); row_free.setSpacing(6)
        self._sld_rot = QSlider(Qt.Orientation.Horizontal)
        self._sld_rot.setRange(-180, 180); self._sld_rot.setValue(0)
        self._sld_rot.setStyleSheet(SLD_STYLE)
        self._sld_rot.setToolTip("Drehwinkel einstellen: −180° bis +180°")
        self._spin_rot = QSpinBox()
        self._spin_rot.setRange(-180, 180); self._spin_rot.setValue(0)
        self._spin_rot.setSuffix("°")
        self._spin_rot.setFixedWidth(66)
        self._spin_rot.setToolTip("Drehwinkel direkt eingeben")
        self._spin_rot.setStyleSheet(
            "QSpinBox { background:#222; color:#ddd; border:1px solid #3a3a3a;"
            " border-radius:6px; padding:3px 5px; font-size:12px; }"
            "QSpinBox::up-button, QSpinBox::down-button { width:18px; }")
        self._sld_rot.valueChanged.connect(lambda v: self._spin_rot.setValue(v))
        self._spin_rot.valueChanged.connect(lambda v: self._sld_rot.setValue(v))
        row_free.addWidget(self._sld_rot, 1)
        row_free.addWidget(self._spin_rot)
        gr2.addLayout(row_free)

        btn_rot_free = btn("Winkel anwenden", ROT_BG, ROT_FG, ROT_HV,
                           "Dreht das Bild um den eingestellten Winkel.\n"
                           "Transparente Ecken entstehen bei schrägen Winkeln.",
                           icon_name="undo")
        btn_rot_free.clicked.connect(
            lambda _=False: self._canvas.apply_rotate(self._spin_rot.value()))
        gr2.addWidget(btn_rot_free)
        l3.addWidget(g_rot)

        g_flip, gf = sec("Spiegeln", "#30a0a0")
        row_flip = QHBoxLayout(); row_flip.setSpacing(6)
        btn_fh = btn("Horizontal", "#0e2a2a", "#7adada", "#1a4040",
                     "Bild horizontal spiegeln (links ↔ rechts)")
        btn_fh.clicked.connect(lambda _=False: self._canvas.apply_flip(True))
        row_flip.addWidget(btn_fh)
        btn_fv = btn("Vertikal", "#0e2a2a", "#7adada", "#1a4040",
                     "Bild vertikal spiegeln (oben ↕ unten)")
        btn_fv.clicked.connect(lambda _=False: self._canvas.apply_flip(False))
        row_flip.addWidget(btn_fv)
        gf.addLayout(row_flip)
        l3.addWidget(g_flip)
        l3.addStretch()

        # ════════════════════════════════════════════════════
        # Tab 4 – Form & Zuschnitt  ⬤
        # ════════════════════════════════════════════════════
        t4, l4 = scroll_tab()
        tabs.addTab(t4, "⬤ Form")
        tabs.setTabToolTip(3, "Form & Zuschnitt – Ecken abrunden, Format-Auswahl")

        g_corner, gc = sec("Ecken abrunden", "#30c060")
        self._lbl_corner = lbl("Radius:  0 px", "#aaa")
        self._sld_corner = slider_row(0, 500, 0,
            "Radius der Eckenrundung in Pixeln.\n0 = keine Rundung · 500 = maximal rund")
        self._sld_corner.valueChanged.connect(
            lambda v: self._lbl_corner.setText(f"Radius:  {v} px"))
        gc.addWidget(self._lbl_corner)
        gc.addWidget(self._sld_corner)
        btn_corner = btn("Ecken abrunden", "#0e2a14", "#7add9a", "#1a4520",
                         "Wendet die Eckenrundung an.\n"
                         "Das Ergebnis wird als PNG mit transparenten Ecken gespeichert.",
                         height=38, icon_name="form")
        btn_corner.clicked.connect(
            lambda _=False: self._canvas.apply_round_corners(self._sld_corner.value()))
        gc.addWidget(btn_corner)
        l4.addWidget(g_corner)

        g_fmt, gfm = sec("Ausgabe-Format & Zuschnitt", "#9060d0")

        info_box = QWidget()
        info_box.setStyleSheet("background:#1e1628; border-radius:7px;")
        info_b = QVBoxLayout(info_box)
        info_b.setContentsMargins(10, 8, 10, 8)
        info_b.addWidget(lbl(
            "⇲ Format wählen → Rahmen erscheint auf dem Bild\n"
            "• Rahmen verschieben: Mitte ziehen\n"
            "• Größe ändern: Ecken ziehen (Proportionen bleiben)", "#8a7aaa", 10))
        gfm.addWidget(info_box)

        # Kreis + Quadrat
        gfm.addWidget(lbl("Sonderformate:", "#777", 10))
        r_special = QHBoxLayout(); r_special.setSpacing(6)
        for label, tip, slot in [
            ("⬤  Kreis",  "Runden Ausschnitt positionieren und zuschneiden",
             self._canvas.start_crop_circle),
            ("■  1 : 1", "Quadratischen Ausschnitt positionieren",
             lambda: self._canvas.start_crop_ratio(1, 1)),
        ]:
            b = btn(label, "#141e38", "#8aaedd", "#1e2e52", tip)
            b.clicked.connect(lambda _=False, fn=slot: fn())
            r_special.addWidget(b)
        gfm.addLayout(r_special)

        # Querformat
        gfm.addWidget(hdivider())
        gfm.addWidget(lbl("Querformat:", "#777", 10))
        LAND_FORMATS = [
            ("16 : 9", 16, 9), ("4 : 3",  4, 3),
            ("3 : 2",  3, 2),  ("2 : 1",  2, 1),
            ("7 : 4.5", 14, 9),
        ]
        for i in range(0, len(LAND_FORMATS), 2):
            row_fmt = QHBoxLayout(); row_fmt.setSpacing(6)
            for label, rw, rh in LAND_FORMATS[i:i+2]:
                b = btn(f"▬  {label}", "#1e1428", "#c0a0f0", "#2e1e44",
                        f"Querformat {label} — Ecken ziehen für Größe, Mitte zum Verschieben")
                b.clicked.connect(
                    lambda _=False, w=rw, h=rh: self._canvas.start_crop_ratio(w, h))
                row_fmt.addWidget(b)
            gfm.addLayout(row_fmt)

        # Hochformat
        gfm.addWidget(hdivider())
        gfm.addWidget(lbl("Hochformat:", "#777", 10))
        PORT_FORMATS = [("9 : 16", 9, 16), ("3 : 4", 3, 4)]
        row_port = QHBoxLayout(); row_port.setSpacing(6)
        for label, rw, rh in PORT_FORMATS:
            b = btn(f"▮  {label}", "#141e28", "#90c8cc", "#1e2e38",
                    f"Hochformat {label} — Ecken ziehen für Größe, Mitte zum Verschieben")
            b.clicked.connect(
                lambda _=False, w=rw, h=rh: self._canvas.start_crop_ratio(w, h))
            row_port.addWidget(b)
        gfm.addLayout(row_port)
        l4.addWidget(g_fmt)
        l4.addStretch()

        return frame


    def _build_menu(self):
        mb = self.menuBar()
        mb.setStyleSheet("""
            QMenuBar { background: #1a1a1a; color: #ccc; }
            QMenuBar::item:selected { background: #333; }
            QMenu { background: #252525; color: #ccc; border: 1px solid #3a3a3a; }
            QMenu::item:selected { background: #4a90d9; }
        """)

        file_m = mb.addMenu("Datei")
        a_open = QAction("Öffnen…", self)
        a_open.setShortcut(QKeySequence("Ctrl+O"))
        a_open.triggered.connect(self._open_image)
        file_m.addAction(a_open)

        a_save = QAction("Speichern…", self)
        a_save.setShortcut(QKeySequence("Ctrl+S"))
        a_save.triggered.connect(self._save_image)
        file_m.addAction(a_save)

        edit_m = mb.addMenu("Bearbeiten")
        a_undo = QAction("Rückgängig", self)
        a_undo.setShortcut(QKeySequence("Ctrl+Z"))
        a_undo.triggered.connect(self._canvas.undo)
        edit_m.addAction(a_undo)

        edit_m.addSeparator()
        a_rot_l = QAction("90° links drehen", self)
        a_rot_l.setShortcut(QKeySequence("Ctrl+Left"))
        a_rot_l.triggered.connect(lambda: self._canvas.apply_rotate(90))
        edit_m.addAction(a_rot_l)

        a_rot_r = QAction("90° rechts drehen", self)
        a_rot_r.setShortcut(QKeySequence("Ctrl+Right"))
        a_rot_r.triggered.connect(lambda: self._canvas.apply_rotate(-90))
        edit_m.addAction(a_rot_r)

        a_rot_180 = QAction("180° drehen", self)
        a_rot_180.triggered.connect(lambda: self._canvas.apply_rotate(180))
        edit_m.addAction(a_rot_180)

        a_flip_h = QAction("Horizontal spiegeln", self)
        a_flip_h.triggered.connect(lambda: self._canvas.apply_flip(True))
        edit_m.addAction(a_flip_h)

        a_flip_v = QAction("Vertikal spiegeln", self)
        a_flip_v.triggered.connect(lambda: self._canvas.apply_flip(False))
        edit_m.addAction(a_flip_v)
        edit_m.addSeparator()

        a_clear = QAction("Auswahl aufheben", self)
        a_clear.setShortcut(QKeySequence("Escape"))
        a_clear.triggered.connect(self._canvas.clear_selection)
        edit_m.addAction(a_clear)

        a_orig = QAction("Original wiederherstellen", self)
        a_orig.triggered.connect(self._canvas.restore_original)
        edit_m.addAction(a_orig)

        view_m = mb.addMenu("Ansicht")
        a_fit = QAction("Fit to View", self)
        a_fit.setShortcut(QKeySequence("Ctrl+0"))
        a_fit.triggered.connect(
            lambda: self._canvas.fitInView(
                self._canvas._img_item, Qt.AspectRatioMode.KeepAspectRatio))
        view_m.addAction(a_fit)

    # ── Slots ─────────────────────────────────────────────────

    def _open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Bild öffnen", "",
            "Bilder (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.gif);;"
            "Alle Dateien (*)"
        )
        if path:
            self._canvas.load_image(path)

    def _save_image(self):
        if self._canvas._pil is None:
            self.statusBar().showMessage("Kein Bild zum Speichern")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Bild speichern", "bild_bearbeitet",
            "PNG (*.png);;JPEG (*.jpg);;WebP (*.webp)"
        )
        if path:
            self._canvas.save_image(path)

    def _pick_color(self):
        c = QColorDialog.getColor(self._bg_color, self, "Hintergrundfarbe wählen")
        if c.isValid():
            self._bg_color = c
            self._update_color_btn()

    def _update_color_btn(self):
        self._color_btn.setStyleSheet(
            f"background: {self._bg_color.name()}; border-radius: 5px; border: 2px solid #555;"
        )

    def _run_ai(self):
        if self._canvas._pil is None:
            self.statusBar().showMessage("Kein Bild geladen")
            return
        if self._ai_thread and self._ai_thread.isRunning():
            self.statusBar().showMessage("KI läuft bereits…")
            return
        self.statusBar().showMessage("🤖 KI verarbeitet Bild… (kann einige Sekunden dauern)")
        self._btn_ai.setEnabled(False)

        self._ai_thread = QThread()
        self._ai_worker = AIWorker(self._canvas._pil.copy())
        self._ai_worker.moveToThread(self._ai_thread)
        self._ai_thread.started.connect(self._ai_worker.run)
        self._ai_worker.finished.connect(self._on_ai_done)
        self._ai_worker.error.connect(self._on_ai_error)
        self._ai_worker.finished.connect(self._ai_thread.quit)
        self._ai_worker.error.connect(self._ai_thread.quit)
        self._ai_thread.finished.connect(lambda: self._btn_ai.setEnabled(True))
        self._ai_thread.start()

    def _on_ai_done(self, img: Image.Image):
        self._canvas.apply_ai_result(img)

    def _on_ai_error(self, msg: str):
        self.statusBar().showMessage(f"KI-Fehler: {msg}")
        QMessageBox.warning(self, "KI-Fehler",
                            f"Fehler bei der automatischen Hintergrundentfernung:\n\n{msg}")

    def _on_history_changed(self, history: list):
        self._history_list.clear()
        for desc in history:
            self._history_list.addItem(desc)

    def _on_crop_mode_changed(self, active: bool):
        self._crop_bar.setVisible(active)

    def _undo_to_item(self, item):
        row = self._history_list.row(item)
        self._canvas.undo_to(row + 1)


# ─────────────────────────────────────────────────────────────
# Start
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("BgRemover")

    # Dunkles Farbschema
    pal = QPalette()
    dark = QColor(30, 30, 30)
    pal.setColor(QPalette.ColorRole.Window,          QColor(37, 37, 37))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor(220, 220, 220))
    pal.setColor(QPalette.ColorRole.Base,            dark)
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor(53, 53, 53))
    pal.setColor(QPalette.ColorRole.Text,            QColor(220, 220, 220))
    pal.setColor(QPalette.ColorRole.Button,          QColor(53, 53, 53))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor(220, 220, 220))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor(74, 144, 217))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    pal.setColor(QPalette.ColorRole.ToolTipBase,     QColor(50, 50, 50))
    pal.setColor(QPalette.ColorRole.ToolTipText,     QColor(220, 220, 220))
    app.setPalette(pal)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())
