#!/usr/bin/env python3
"""
BgRemover — Hintergrund-Entfernungs & Ersatz-Tool für macOS
Starten: python3 BgRemover.py
"""

import sys
import os
import io
import functools
import logging
import numpy as np
from collections import deque
from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path
from typing import Callable

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QColorDialog,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsObject,
    QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsLineItem,
    QToolButton, QButtonGroup, QGroupBox, QStatusBar,
    QFrame, QMessageBox, QTabWidget, QTabBar, QSpinBox,
    QListWidget, QScrollArea, QStyle, QStylePainter, QStyleOptionTab,
    QDialog, QLineEdit, QComboBox,
)
from PyQt6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QBrush,
    QDragEnterEvent, QDropEvent, QAction, QKeySequence,
    QCursor, QPalette, QPen, QIcon, QPolygonF, QPainterPath,
    QFontMetrics, QFont, QDesktopServices,
)

from PyQt6.QtCore import (
    Qt, QRectF, QPointF, QSize, QRect, pyqtSignal, QThread, QObject,
    QSettings, QStandardPaths, QUrl,
)
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from bgremover.constants import (
    logger, LOG_FILENAME, _MAX_MEGAPIXELS, _UNDO_MEMORY_LIMIT,
    _THREAD_SHUTDOWN_MS, _IS_MACOS,
    _TOOLBAR_WIDTH, _TOOLBAR_BTN_SIZE, _TOOLBAR_ICON_SIZE,
    _RIGHT_PANEL_WIDTH, _CROP_BAR_HEIGHT, _COLOR_BTN_SIZE, _TAB_ICON_PX,
    _WINDOW_MIN_W, _WINDOW_MIN_H,
    _DEFAULT_TOLERANCE, _DEFAULT_BRUSH_RADIUS, _ZOOM_FACTOR,
    TOOL_WAND, TOOL_BRUSH, TOOL_ERASER, TOOL_LASSO,
)
from bgremover.image_utils import (
    flood_fill, make_checker_brush, mask_to_overlay,
    numpy_to_pil, pil_to_numpy, pil_to_qpixmap,
)

try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except (ImportError, RuntimeError, OSError, SystemExit):
    # rembg ist optional; fehlt das onnxruntime-Backend, kann der Import
    # je nach rembg-Version unterschiedlich fehlschlagen (inkl. SystemExit).
    REMBG_AVAILABLE = False

try:
    __version__ = _pkg_version("bgremover")
except PackageNotFoundError:
    # Quelle-Lauf ohne installiertes Paket – pyproject.toml ist maßgeblich.
    __version__ = "2.1.0"

# Vom Logging-Setup gesetzter, tatsächlich beschriebener Log-Pfad. Wird
# vom Einstellungen-Dialog ausgelesen, damit Anzeige und FileHandler nie
# auseinanderlaufen.
_log_file_path: "Path | None" = None

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

def _draw_wand_icon(p: QPainter, s: int) -> None:
    p.setPen(QPen(QColor(220, 220, 220), 2.2,
                  Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(int(s*0.22), int(s*0.78), int(s*0.65), int(s*0.35))
    p.setBrush(QBrush(QColor(220, 220, 220)))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(int(s*0.10), int(s*0.66), int(s*0.24), int(s*0.24))
    gold = QColor(255, 210, 50)
    def _star(cx, cy, r) -> None:
        p.setPen(QPen(gold, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(cx, cy-r, cx, cy+r); p.drawLine(cx-r, cy, cx+r, cy)
    _star(int(s*0.75), int(s*0.22), int(s*0.12))
    _star(int(s*0.88), int(s*0.48), int(s*0.08))
    _star(int(s*0.60), int(s*0.12), int(s*0.07))


def _draw_brush_icon(p: QPainter, s: int) -> None:
    p.setPen(QPen(QColor(190, 190, 190), 2.5,
                  Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(int(s*0.72), int(s*0.12), int(s*0.38), int(s*0.62))
    p.setPen(QPen(QColor(160, 160, 170), 2))
    p.drawLine(int(s*0.42), int(s*0.57), int(s*0.30), int(s*0.69))
    p.setPen(QPen(QColor(80, 150, 240), 3,
                  Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(int(s*0.28), int(s*0.71), int(s*0.18), int(s*0.88))
    p.setPen(QPen(QColor(60, 130, 220), 2,
                  Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(int(s*0.34), int(s*0.72), int(s*0.26), int(s*0.90))
    p.drawLine(int(s*0.22), int(s*0.70), int(s*0.12), int(s*0.86))


def _draw_eraser_icon(p: QPainter, s: int) -> None:
    p.setPen(QPen(QColor(160, 160, 160), 1.5))
    p.setBrush(QBrush(QColor(240, 185, 90, 220)))
    p.drawRoundedRect(int(s*0.12), int(s*0.38), int(s*0.76), int(s*0.36), 3, 3)
    p.setPen(QPen(QColor(200, 120, 50, 200), 2))
    tx = int(s * 0.45)
    p.drawLine(tx, int(s*0.38), tx, int(s*0.74))
    p.setPen(QPen(QColor(120, 120, 120, 100), 1))
    p.setBrush(QBrush(QColor(100, 100, 100, 60)))
    p.drawRoundedRect(int(s*0.12), int(s*0.70), int(s*0.76), int(s*0.10), 2, 2)


def _draw_lasso_icon(p: QPainter, s: int) -> None:
    pts = [
        QPointF(s*0.50, s*0.10),
        QPointF(s*0.88, s*0.38),
        QPointF(s*0.76, s*0.82),
        QPointF(s*0.24, s*0.82),
        QPointF(s*0.12, s*0.38),
    ]
    pen = QPen(QColor(200, 200, 200), 1.8, Qt.PenStyle.DashLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(pts[0])
    for pt in pts[1:]:
        path.lineTo(pt)
    path.closeSubpath()
    p.drawPath(path)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(100, 180, 255)))
    r = max(2, int(s * 0.065))
    for pt in pts:
        p.drawEllipse(pt, r, r)


def _draw_ai_icon(p: QPainter, s: int) -> None:
    bolt = QPolygonF([
        QPointF(s*0.55, s*0.10), QPointF(s*0.28, s*0.52),
        QPointF(s*0.48, s*0.52), QPointF(s*0.42, s*0.90),
        QPointF(s*0.72, s*0.46), QPointF(s*0.52, s*0.46),
    ])
    p.setPen(QPen(QColor(80, 190, 255), 1.5))
    p.setBrush(QBrush(QColor(80, 190, 255, 200)))
    p.drawPolygon(bolt)


def _draw_open_icon(p: QPainter, s: int) -> None:
    p.setPen(QPen(QColor(200, 200, 200), 1.5))
    p.setBrush(QBrush(QColor(200, 170, 80, 200)))
    p.drawRoundedRect(int(s*0.10), int(s*0.38), int(s*0.80), int(s*0.46), 3, 3)
    p.setBrush(QBrush(QColor(220, 190, 100, 200)))
    p.drawRoundedRect(int(s*0.10), int(s*0.30), int(s*0.40), int(s*0.14), 3, 3)
    p.setPen(QPen(QColor(255, 255, 255, 220), 2,
                  Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    mx, my = int(s*0.50), int(s*0.56)
    p.drawLine(mx, my+int(s*0.14), mx, my-int(s*0.10))
    p.drawLine(mx-int(s*0.10), my, mx, my-int(s*0.12))
    p.drawLine(mx+int(s*0.10), my, mx, my-int(s*0.12))


def _draw_save_icon(p: QPainter, s: int) -> None:
    p.setPen(QPen(QColor(160, 160, 160), 1.5))
    p.setBrush(QBrush(QColor(80, 140, 200, 200)))
    p.drawRoundedRect(int(s*0.12), int(s*0.12), int(s*0.76), int(s*0.76), 4, 4)
    p.setBrush(QBrush(QColor(220, 220, 220, 200)))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRect(int(s*0.26), int(s*0.12), int(s*0.48), int(s*0.32))
    p.setBrush(QBrush(QColor(80, 140, 200, 200)))
    p.drawRect(int(s*0.38), int(s*0.12), int(s*0.14), int(s*0.32))
    p.setPen(QPen(QColor(160, 160, 160), 1))
    p.setBrush(QBrush(QColor(60, 110, 170, 200)))
    p.drawRect(int(s*0.22), int(s*0.56), int(s*0.56), int(s*0.28))


def _draw_undo_icon(p: QPainter, s: int) -> None:
    pen = QPen(QColor(180, 200, 230), max(2, int(s * 0.10)),
               Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
               Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(s*0.15, s*0.20, s*0.65, s*0.55), 30 * 16, 240 * 16)
    tip_x, tip_y = s*0.155, s*0.415
    p.drawLine(QPointF(tip_x, tip_y), QPointF(tip_x + s*0.16, tip_y - s*0.14))
    p.drawLine(QPointF(tip_x, tip_y), QPointF(tip_x + s*0.12, tip_y + s*0.18))


def _draw_restore_icon(p: QPainter, s: int) -> None:
    pen = QPen(QColor(150, 210, 160), max(2, int(s * 0.10)),
               Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
               Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    arc_r = QRectF(s*0.15, s*0.15, s*0.70, s*0.70)
    p.drawArc(arc_r,  20 * 16, 160 * 16)
    p.drawArc(arc_r, 200 * 16, 160 * 16)
    p.drawLine(QPointF(s*0.83, s*0.415), QPointF(s*0.68, s*0.22))
    p.drawLine(QPointF(s*0.83, s*0.415), QPointF(s*0.62, s*0.50))
    p.drawLine(QPointF(s*0.17, s*0.585), QPointF(s*0.32, s*0.78))
    p.drawLine(QPointF(s*0.17, s*0.585), QPointF(s*0.38, s*0.50))


def _draw_history_icon(p: QPainter, s: int) -> None:
    c = QColor(180, 200, 230)
    pen = QPen(c, max(2, int(s * 0.09)),
               Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
               Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    cx, cy, r = s * 0.50, s * 0.50, s * 0.34
    p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
    p.drawLine(QPointF(cx, cy), QPointF(cx, cy - r * 0.58))
    p.drawLine(QPointF(cx, cy), QPointF(cx + r * 0.44, cy + r * 0.22))
    p.drawLine(QPointF(cx, cy - r), QPointF(cx - s*0.13, cy - r + s*0.12))
    p.drawLine(QPointF(cx, cy - r), QPointF(cx + s*0.10, cy - r + s*0.15))


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
                pil_img = Image.open(png_path).convert("RGBA").resize(
                    (size, size), Image.Resampling.LANCZOS)
                data = pil_img.tobytes("raw", "RGBA")
                qimg = QImage(data, size, size,
                              QImage.Format.Format_RGBA8888)
                pm = QPixmap.fromImage(qimg)
                if not pm.isNull():
                    return QIcon(pm)
            except Exception:
                logger.debug("Icon-PNG konnte nicht geladen werden: %s",
                             png_path, exc_info=True)
            break
    # ── Fallback: gezeichnetes Vektor-Icon ──────────────────────────────────
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size

    _ICON_DRAW = {
        "wand":    _draw_wand_icon,
        "brush":   _draw_brush_icon,
        "eraser":  _draw_eraser_icon,
        "lasso":   _draw_lasso_icon,
        "ai":      _draw_ai_icon,
        "open":    _draw_open_icon,
        "save":    _draw_save_icon,
        "undo":    _draw_undo_icon,
        "restore": _draw_restore_icon,
        "history": _draw_history_icon,
    }
    if name in _ICON_DRAW:
        _ICON_DRAW[name](p, s)
    p.end()
    return QIcon(pm)


# ─────────────────────────────────────────────────────────────
# KI-Worker (läuft in eigenem Thread)
# ─────────────────────────────────────────────────────────────

class _Worker(QObject):
    """Basisklasse für Hintergrund-Worker.

    Kapselt den in mehreren Workern identischen Ablauf
    ``try: _work() / except Exception: logger.exception(); error.emit()``.
    Unterklassen deklarieren ihr eigenes ``finished``-Signal (die
    Signaturen unterscheiden sich je Worker) und implementieren ``_work``.
    """
    error = pyqtSignal(str)
    _error_context = "Worker-Fehler"

    def run(self) -> None:
        try:
            self._work()
        except Exception as e:
            logger.exception(self._error_context)
            self.error.emit(f"{type(e).__name__}: {e}")

    def _work(self) -> None:
        raise NotImplementedError


class AIWorker(_Worker):
    finished = pyqtSignal(object)   # PIL Image
    _error_context = "rembg-Fehler"

    def __init__(self, pil_image: Image.Image) -> None:
        super().__init__()
        self._img = pil_image

    def _work(self) -> None:
        buf = io.BytesIO()
        self._img.save(buf, format="PNG")
        result_bytes = rembg_remove(buf.getvalue())
        result = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
        self.finished.emit(result)


class RembgWarmupWorker(QObject):
    """Lädt das rembg-ONNX-Modell einmalig im Hintergrund.

    Ohne diesen Warmup blockt der erste KI-Klick rund zehn Sekunden,
    weil rembg sein Modell on-demand initialisiert. Ein remove()-Aufruf
    mit einem winzigen Dummy-Bild reicht, um die rembg-Session global
    zu cachen – nachfolgende Aufrufe sind sofort schnell.
    """
    finished = pyqtSignal()

    def run(self) -> None:
        try:
            buf = io.BytesIO()
            Image.new("RGBA", (16, 16), (0, 0, 0, 255)).save(buf, format="PNG")
            rembg_remove(buf.getvalue())
            logger.info("rembg-Warmup abgeschlossen")
        except Exception:
            logger.exception("rembg-Warmup fehlgeschlagen")
        finally:
            self.finished.emit()


class ImageLoadWorker(_Worker):
    """Lädt + EXIF-orientiert ein Bild im Hintergrund.

    Vermeidet UI-Freeze bei großen Fotos.
    """
    finished = pyqtSignal(object, str)   # (PIL.Image, original_path)
    _error_context = "Bildladen fehlgeschlagen"

    def __init__(self, path: str) -> None:
        super().__init__()
        self._path = path

    def _work(self) -> None:
        img = Image.open(self._path)
        mp = img.width * img.height / 1_000_000
        if mp > _MAX_MEGAPIXELS:
            self.error.emit(
                f"Bild zu groß ({mp:.0f} MP) – Maximum: {_MAX_MEGAPIXELS} MP")
            return
        img = ImageOps.exif_transpose(img).convert("RGBA")
        self.finished.emit(img, self._path)


# ─────────────────────────────────────────────────────────────
# Crop-Overlay (rein visuell – Canvas steuert Interaktion)
# ─────────────────────────────────────────────────────────────

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
        if dx / self._aspect >= dy:
            new_w = max(MIN_PX, dx)
        else:
            new_w = max(MIN_PX, dy * self._aspect)
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

    def paint(self, painter: QPainter, option, widget) -> None:
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


def _requires_image(method: Callable[..., None]) -> Callable[..., None]:
    """Frühausstieg-Guard für ImageCanvas-Methoden ohne geladenes Bild.

    Ersetzt den mehrfach byte-identisch wiederholten Block
    ``if self._pil is None: self.statusMsg.emit("Kein Bild geladen"); return``.
    """
    @functools.wraps(method)
    def wrapper(self: "ImageCanvas", *args: object, **kwargs: object) -> None:
        if self._pil is None:
            self.statusMsg.emit("Kein Bild geladen")
            return
        method(self, *args, **kwargs)
    return wrapper


class ImageCanvas(QGraphicsView):
    statusMsg      = pyqtSignal(str)
    historyChanged = pyqtSignal(list)   # list[str] – Beschreibungen, neueste zuerst
    cropModeChanged = pyqtSignal(bool)  # True = Crop-Overlay aktiv
    imageLoaded    = pyqtSignal(str)    # absoluter Pfad eines frisch geladenen Bildes
    loadRequested  = pyqtSignal(str)    # Drop/Recent → MainWindow lädt asynchron

    def __init__(self, parent=None) -> None:
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
        # Monotoner Zähler: wird bei jedem Bildwechsel erhöht.
        # Externe Worker nutzen ihn als Stale-Check statt Objektidentität.
        self._version:  int = 0
        # Undo-Stack: (Image, Beschreibung der Aktion die dazu führte)
        # Kein festes maxlen – Grösse wird durch _UNDO_MEMORY_LIMIT begrenzt.
        self._undo:     deque = deque()
        # Laufende Summe der Undo-Rohdaten in Bytes (statt deque jedes Mal
        # komplett aufzusummieren – O(1) statt O(n) pro Bearbeitung).
        self._undo_bytes: int = 0
        # Redo-Stack: gespiegelt zum Undo. Wird bei jeder neuen Aktion
        # via _apply_pil(push=True) geleert.
        self._redo:     deque = deque(maxlen=20)

        self._tool      = TOOL_WAND
        self._tolerance = _DEFAULT_TOLERANCE
        self._brush_r   = _DEFAULT_BRUSH_RADIUS
        self._panning   = False
        self._pan_start = QPointF()
        self._drawing   = False

        # Polygon-Lasso-Werkzeug
        self._lasso_pts:       list[tuple[int, int]] = []
        self._lasso_path_item: QGraphicsPathItem | None = None
        self._lasso_line_item: QGraphicsLineItem | None = None
        self._lasso_mods:      Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier

        # Crop-Overlay-Zustand
        self._crop_overlay:      CropOverlayItem | None = None
        self._crop_dragging:     bool    = False
        self._crop_drag_start:   QPointF = QPointF()
        self._crop_start_pos:    QPointF = QPointF()
        self._crop_resizing:     bool    = False   # True = Resize-Drag läuft
        self._crop_resize_corner: int    = -1      # 0-3 welche Ecke

        # Pinsel-Vorschau-Kreis (sichtbar bei Tool=brush/eraser)
        self._brush_preview = QGraphicsEllipseItem()
        self._brush_preview.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
        self._brush_preview.setBrush(QBrush(QColor(74, 144, 217, 30)))
        self._brush_preview.setZValue(20)
        self._brush_preview.setVisible(False)
        self._scene.addItem(self._brush_preview)

    # ── Öffentliche Accessors (Kapselung) ────────────────────

    @property
    def image(self) -> Image.Image | None:
        """Aktuell angezeigtes PIL-Bild (oder ``None``)."""
        return self._pil

    @property
    def has_image(self) -> bool:
        """True, sobald ein Bild geladen ist."""
        return self._pil is not None

    @property
    def version(self) -> int:
        """Monoton steigender Zähler; erhöht sich bei jedem Bildwechsel."""
        return self._version

    def fit_to_view(self) -> None:
        """Bild in die Ansicht einpassen (ohne internen Item-Zugriff von aussen)."""
        self.fitInView(self._img_item, Qt.AspectRatioMode.KeepAspectRatio)

    @staticmethod
    def _img_bytes(img: Image.Image) -> int:
        """Geschätzte RGBA-Rohdatengrösse eines Bildes in Bytes."""
        return img.width * img.height * 4

    # ── Laden ────────────────────────────────────────────────

    def load_image(self, path: str) -> None:
        """Synchroner Lade-Pfad – wird vom Drop-Event und von Tests genutzt.

        Für den File-Dialog läuft der gleiche Vorgang in einem Worker
        (siehe ``MainWindow._load_image_async`` + ``apply_loaded_image``).
        """
        # EXIF-Orientierung anwenden: Smartphone-Fotos sind oft im Sensor
        # gespeichert wie aufgenommen und werden erst über das EXIF-Tag
        # korrekt orientiert. Ohne exif_transpose() erscheinen sie gekippt.
        img = Image.open(path)
        mp = img.width * img.height / 1_000_000
        if mp > _MAX_MEGAPIXELS:
            self.statusMsg.emit(
                f"Bild zu groß ({mp:.0f} MP) – Maximum: {_MAX_MEGAPIXELS} MP")
            return
        img = ImageOps.exif_transpose(img).convert("RGBA")
        self.apply_loaded_image(img, path)

    def apply_loaded_image(self, img: Image.Image, path: str) -> None:
        """Übernimmt ein bereits geladenes (PIL-)Bild als neuen Canvas-State."""
        self._version += 1
        self._original = img.copy()
        self._undo.clear()
        self._undo_bytes = 0
        self._redo.clear()
        self._cancel_crop_overlay()
        self._apply_pil(img, push=False)
        self.fitInView(self._img_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.statusMsg.emit(
            f"Geöffnet: {Path(path).name}  ({img.width} × {img.height} px)")
        self.imageLoaded.emit(str(Path(path).resolve()))

    def _apply_pil(self, img: Image.Image, push: bool = True, desc: str = "Bearbeitung") -> None:
        if push and self._pil is not None:
            self._undo.append((self._pil.copy(), desc))
            self._undo_bytes += self._img_bytes(self._pil)
            # Neue Aktion ⇒ Redo-Branch verwerfen (klassisches Editor-Verhalten)
            self._redo.clear()
            # Älteste Einträge entfernen, solange das Speicherlimit überschritten ist.
            while len(self._undo) > 1 and self._undo_bytes > _UNDO_MEMORY_LIMIT:
                evicted, _ = self._undo.popleft()
                self._undo_bytes -= self._img_bytes(evicted)
            self._emit_history()
        self._set_image_state(img)

    def _refresh_image(self) -> None:
        if self._pil:
            px = pil_to_qpixmap(self._pil)
            self._img_item.setPixmap(px)
            self._scene.setSceneRect(QRectF(px.rect()))
            self._img_item.update()
            self.viewport().update()

    def _refresh_overlay(self) -> None:
        if self._mask is not None and self._pil:
            h, w = self._mask.shape
            self._overlay_item.setPixmap(mask_to_overlay(self._mask, w, h))

    def _set_image_state(self, img: Image.Image) -> None:
        """Übernimmt *img* als aktuellen Bildzustand (Pixmap + leere Maske).

        Kapselt den Block, der zuvor identisch in ``_apply_pil``, ``undo``,
        ``redo``, ``undo_to`` und ``restore_original`` stand. Setzt
        ausschliesslich den Anzeigezustand – Undo-/Redo-Stapelpflege
        bleibt Sache der Aufrufer.
        """
        self._pil  = img
        self._arr  = pil_to_numpy(img)
        self._mask = np.zeros((img.height, img.width), dtype=bool)
        self._refresh_image()
        self._refresh_overlay()

    def _emit_history(self) -> None:
        """Sendet die aktuelle Verlaufsliste (neueste zuerst)."""
        self.historyChanged.emit([d for _, d in reversed(list(self._undo))])

    # ── Undo / Original ──────────────────────────────────────

    def undo(self) -> None:
        if self._crop_overlay is not None:
            self.cancel_crop(); return
        if self._undo:
            img, desc = self._undo.pop()
            self._undo_bytes -= self._img_bytes(img)
            # Aktuellen Stand für mögliches Redo aufbewahren
            if self._pil is not None:
                self._redo.append((self._pil.copy(), desc))
            self._set_image_state(img)
            self._emit_history()
            self.statusMsg.emit(f"↩  Rückgängig: {desc}")
        else:
            self.statusMsg.emit("Nichts mehr zum Rückgängigmachen")

    def redo(self) -> None:
        """Macht ein zuvor mit ``undo()`` rückgängig gemachte Aktion wieder."""
        if self._crop_overlay is not None:
            return
        if self._redo:
            img, desc = self._redo.pop()
            if self._pil is not None:
                self._undo.append((self._pil.copy(), desc))
                self._undo_bytes += self._img_bytes(self._pil)
            self._set_image_state(img)
            self._emit_history()
            self.statusMsg.emit(f"↪  Wiederherstellen: {desc}")
        else:
            self.statusMsg.emit("Nichts mehr zum Wiederherstellen")

    def undo_to(self, steps: int) -> None:
        """Mehrere Schritte auf einmal rückgängig machen.

        Verhält sich wie mehrfaches ``undo()``: jeder übersprungene Stand
        wandert auf den Redo-Stapel, der Sprung ist also wiederherstellbar.
        """
        if self._crop_overlay is not None:
            self.cancel_crop(); return
        actual = min(steps, len(self._undo))
        if actual <= 0:
            return
        img, desc = None, ""
        for _ in range(actual):
            img, desc = self._undo.pop()
            self._undo_bytes -= self._img_bytes(img)
            if self._pil is not None:
                self._redo.append((self._pil.copy(), desc))
            self._pil = img
        self._set_image_state(img)
        self._emit_history()
        self.statusMsg.emit(f"↩  {actual} Schritt(e) rückgängig  (bis: {desc})")

    def restore_original(self) -> None:
        if self._original:
            self._cancel_crop_overlay()
            # Aktuellen Stand für Undo aufbewahren, statt den Verlauf
            # zu verwerfen – so kann der Nutzer das Zurücksetzen
            # selbst wieder rückgängig machen.
            if self._pil is not None:
                self._undo.append((self._pil.copy(), "🔄 Original wiederhergestellt"))
                self._undo_bytes += self._img_bytes(self._pil)
            # Redo verwerfen – „Original wiederherstellen" ist ein Sprung.
            self._redo.clear()
            self._set_image_state(self._original.copy())
            self._emit_history()
            self.statusMsg.emit("🔄  Original wiederhergestellt")

    def clear_selection(self) -> None:
        if self._mask is not None:
            self._mask[:] = False
            self._refresh_overlay()
            self.statusMsg.emit("Auswahl aufgehoben")

    def invert_selection(self) -> None:
        """Kehrt die aktuelle Maske um (Vorder- ↔ Hintergrund)."""
        if self._mask is None or self._pil is None:
            self.statusMsg.emit("Kein Bild geladen")
            return
        self._mask = ~self._mask
        self._refresh_overlay()
        self.statusMsg.emit(
            f"Auswahl invertiert: {int(self._mask.sum()):,} Pixel")

    def _morphology(self, radius: int, kind: str) -> None:
        """Erweitert oder schrumpft die Boolean-Maske um ``radius`` Pixel
        mittels PIL-Morphologie-Filtern."""
        if self._mask is None or self._pil is None or radius <= 0:
            return
        mask_img = Image.fromarray(
            (self._mask * 255).astype(np.uint8), mode="L")
        # PIL-Filter brauchen ungerade Kernelgrößen
        size = radius * 2 + 1
        if kind == "expand":
            filt = ImageFilter.MaxFilter(size)
            label = "erweitert"
        else:
            filt = ImageFilter.MinFilter(size)
            label = "geschrumpft"
        result = mask_img.filter(filt)
        self._mask = np.array(result) > 127
        self._refresh_overlay()
        self.statusMsg.emit(
            f"Auswahl um {radius} px {label}: "
            f"{int(self._mask.sum()):,} Pixel")

    def expand_selection(self, radius: int) -> None:
        self._morphology(radius, "expand")

    def shrink_selection(self, radius: int) -> None:
        self._morphology(radius, "shrink")

    # ── Tool-Einstellungen ───────────────────────────────────

    def set_tool(self, tool: str) -> None:
        if self._tool == TOOL_LASSO and tool != TOOL_LASSO:
            self._lasso_cancel()
        self._tool = tool
        if tool == TOOL_WAND:
            self.setCursor(make_wand_cursor())
            self._brush_preview.setVisible(False)
        elif tool == TOOL_BRUSH:
            self.setCursor(make_brush_cursor(self._brush_r * 2))
        elif tool == TOOL_ERASER:
            self.setCursor(make_eraser_cursor(self._brush_r * 2))
        elif tool == TOOL_LASSO:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
            self._brush_preview.setVisible(False)
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self._brush_preview.setVisible(False)

    def set_tolerance(self, v: int) -> None:
        self._tolerance = v

    def set_brush_size(self, v: int) -> None:
        self._brush_r = max(1, v // 2)
        # Cursor sofort aktualisieren
        if self._tool == TOOL_BRUSH:
            self.setCursor(make_brush_cursor(v))
        elif self._tool == TOOL_ERASER:
            self.setCursor(make_eraser_cursor(v))

    def _update_brush_preview(self, sp: QPointF) -> None:
        """Aktualisiert Position/Sichtbarkeit des Pinsel-Vorschau-Kreises."""
        if self._tool not in (TOOL_BRUSH, TOOL_ERASER) or self._pil is None:
            self._brush_preview.setVisible(False)
            return
        r = self._brush_r
        self._brush_preview.setRect(sp.x() - r, sp.y() - r, r * 2, r * 2)
        self._brush_preview.setVisible(True)

    # ── Operationen ──────────────────────────────────────────

    def apply_remove(self, _checked=False) -> None:
        try:
            if not self._check_selection():
                return
            arr = self._arr.copy()
            arr[self._mask, 3] = 0
            self._apply_pil(numpy_to_pil(arr), desc="Hintergrund entfernt")
            self.viewport().update()
            self.statusMsg.emit("Hintergrund entfernt (transparent)")
        except Exception as e:
            logger.exception("Fehler beim Entfernen")
            self.statusMsg.emit(f"Fehler beim Entfernen: {e}")

    def apply_replace(self, color: QColor) -> None:
        try:
            if not self._check_selection():
                return
            arr = self._arr.copy()
            arr[self._mask] = [color.red(), color.green(), color.blue(), 255]
            self._apply_pil(numpy_to_pil(arr), desc=f"Farbe ersetzt ({color.name()})")
            self.viewport().update()
            self.statusMsg.emit(f"Hintergrund ersetzt: {color.name()}")
        except Exception as e:
            logger.exception("Fehler beim Ersetzen")
            self.statusMsg.emit(f"Fehler beim Ersetzen: {e}")

    def apply_ai_result(self, img: Image.Image) -> None:
        self._apply_pil(img, desc="KI-Hintergrundentfernung")
        self.statusMsg.emit("✅ KI-Hintergrundentfernung abgeschlossen")

    def save_image(self, path: str) -> bool:
        """Speichert das aktuelle Bild; gibt ``True`` bei Erfolg zurück.

        E/A-Fehler (nicht beschreibbarer Pfad, voller Datenträger,
        unbekanntes Format …) werden protokolliert und als Statusmeldung
        gemeldet, statt unbehandelt zu propagieren – konsistent zu
        ``apply_remove``/``apply_replace``. Der Rückgabewert erlaubt dem
        Aufrufer, einen fehlgeschlagenen Pfad nicht als Quick-Save-Ziel
        zu merken.
        """
        if self._pil is None:
            self.statusMsg.emit("Kein Bild zum Speichern")
            return False
        try:
            ext = Path(path).suffix.lower()
            if ext in (".jpg", ".jpeg"):
                # Transparenz auf weißem Hintergrund einbetten
                src = self._pil if self._pil.mode == "RGBA" else self._pil.convert("RGBA")
                bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
                bg.paste(src, mask=src.split()[3])
                bg.convert("RGB").save(path, quality=95)
            elif ext == ".webp":
                self._pil.save(path, "WEBP", quality=90)
            elif ext in (".tif", ".tiff"):
                # TIFF unterstützt RGBA + Transparenz nativ
                self._pil.save(path, "TIFF", compression="tiff_lzw")
            else:
                self._pil.save(path, "PNG")
        except Exception as e:
            logger.exception("Speichern fehlgeschlagen: %s", path)
            self.statusMsg.emit(f"Speichern fehlgeschlagen: {e}")
            return False
        self.statusMsg.emit(f"💾 Gespeichert: {Path(path).name}")
        return True

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

    def mousePressEvent(self, event) -> None:
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
                    self._crop_start_pos  = self._crop_overlay.top_left
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
        elif self._tool == TOOL_LASSO:
            w, h = self._pil.size
            if 0 <= x < w and 0 <= y < h:
                if not self._lasso_pts:
                    self._lasso_mods = mods
                self._lasso_add_point(x, y)
        else:
            self._drawing = True
            self._paint_brush(x, y)

    def mouseMoveEvent(self, event) -> None:
        sp = self.mapToScene(event.position().toPoint())

        # Pinsel-Vorschau (außerhalb von Crop-/Pan-Modi)
        if self._crop_overlay is None and not self._panning:
            self._update_brush_preview(sp)
            # Lasso-Vorschaulinie vom letzten Punkt zur Mausposition
            if self._tool == TOOL_LASSO and self._lasso_pts and self._lasso_line_item is not None:
                last = self._lasso_pts[-1]
                self._lasso_line_item.setLine(last[0], last[1], sp.x(), sp.y())

        # ── Crop-Resize ───────────────────────────────────────
        if self._crop_resizing and self._crop_overlay is not None:
            self._crop_overlay.resize_from_corner(
                self._crop_resize_corner, sp.x(), sp.y())
            cw, ch = self._crop_overlay.size
            self.statusMsg.emit(
                f"⇲ Größe: {int(round(cw))} × {int(round(ch))} px")
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

    def mouseReleaseEvent(self, event) -> None:
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

    def mouseDoubleClickEvent(self, event) -> None:
        if self._tool == TOOL_LASSO and event.button() == Qt.MouseButton.LeftButton:
            if len(self._lasso_pts) >= 3:
                self._lasso_close()
            else:
                self._lasso_cancel()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and self._lasso_pts:
            self._lasso_cancel()
            self.statusMsg.emit("Polygon-Lasso abgebrochen")
            return
        super().keyPressEvent(event)

    def _lasso_add_point(self, x: int, y: int) -> None:
        self._lasso_pts.append((x, y))
        path = QPainterPath()
        path.moveTo(*self._lasso_pts[0])
        for px, py in self._lasso_pts[1:]:
            path.lineTo(px, py)
        pen = QPen(QColor(255, 255, 255, 220), 1.5, Qt.PenStyle.DashLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        if self._lasso_path_item is None:
            self._lasso_path_item = QGraphicsPathItem()
            self._lasso_path_item.setZValue(25)
            self._scene.addItem(self._lasso_path_item)
        self._lasso_path_item.setPen(pen)
        self._lasso_path_item.setPath(path)
        if self._lasso_line_item is None:
            line_pen = QPen(QColor(200, 200, 200, 160), 1.2, Qt.PenStyle.DotLine)
            self._lasso_line_item = QGraphicsLineItem(x, y, x, y)
            self._lasso_line_item.setPen(line_pen)
            self._lasso_line_item.setZValue(25)
            self._scene.addItem(self._lasso_line_item)
        else:
            self._lasso_line_item.setLine(x, y, x, y)
        n = len(self._lasso_pts)
        suffix = "e" if n != 1 else ""
        self.statusMsg.emit(
            f"Polygon-Lasso: {n} Punkt{suffix} — Doppelklick zum Abschließen · Esc = abbrechen")

    def _lasso_close(self) -> None:
        pts = self._lasso_pts.copy()
        mods = self._lasso_mods
        self._lasso_cancel()
        if self._mask is None or self._pil is None:
            return
        h, w = self._mask.shape
        mask_img = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask_img).polygon(pts, fill=255)
        new_mask = np.array(mask_img) > 127
        if mods & Qt.KeyboardModifier.ShiftModifier:
            self._mask |= new_mask
        elif mods & Qt.KeyboardModifier.ControlModifier:
            self._mask &= ~new_mask
        else:
            self._mask = new_mask
        self._refresh_overlay()
        self.statusMsg.emit(
            f"Polygon-Lasso: {int(self._mask.sum()):,} Pixel ausgewählt")

    def _lasso_cancel(self) -> None:
        if self._lasso_path_item is not None:
            self._scene.removeItem(self._lasso_path_item)
            self._lasso_path_item = None
        if self._lasso_line_item is not None:
            self._scene.removeItem(self._lasso_line_item)
            self._lasso_line_item = None
        self._lasso_pts.clear()
        self._lasso_mods = Qt.KeyboardModifier.NoModifier

    def _paint_brush(self, cx: int, cy: int) -> None:
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

    # Zoom-Grenzen: verhindert dass Bild auf 0 schrumpft (kein Klick mehr
    # möglich) oder so groß wird, dass Qt-Rasterung sichtbar wird.
    ZOOM_MIN = 0.05
    ZOOM_MAX = 40.0

    def _zoom(self, factor: float) -> None:
        new_scale = self.transform().m11() * factor
        if self.ZOOM_MIN <= new_scale <= self.ZOOM_MAX:
            self.scale(factor, factor)

    def wheelEvent(self, event) -> None:
        self._zoom(_ZOOM_FACTOR if event.angleDelta().y() > 0 else 1 / _ZOOM_FACTOR)

    def leaveEvent(self, event) -> None:
        # Pinsel-Vorschau verstecken, sobald die Maus den View verlässt
        self._brush_preview.setVisible(False)
        super().leaveEvent(event)

    # ── Drag & Drop ──────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:  # ← PFLICHT: ohne dies wird Drop abgelehnt
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        exts = (".png", ".jpg", ".jpeg", ".webp",
                ".bmp", ".tiff", ".tif", ".gif")
        valid = [url.toLocalFile() for url in event.mimeData().urls()
                 if Path(url.toLocalFile()).suffix.lower() in exts]
        if not valid:
            self.statusMsg.emit("Format nicht unterstützt")
            return
        # Asynchron laden (gleicher Worker-Pfad wie der Datei-Dialog),
        # damit ein grosses Foto die UI nicht einfriert.
        self.loadRequested.emit(valid[0])
        if len(valid) > 1:
            self.statusMsg.emit(
                f"Geöffnet: {Path(valid[0]).name}  "
                f"({len(valid) - 1} weitere Datei(en) ignoriert)")

    # ── Ecken abrunden ───────────────────────────────────────

    @_requires_image
    def apply_round_corners(self, radius: int) -> None:
        """Rundet die Ecken des Bildes mit dem gegebenen Radius ab."""
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

    @_requires_image
    def apply_rotate(self, degrees: int) -> None:
        """Dreht das Bild um den angegebenen Winkel (gegen den Uhrzeigersinn).
        Bei 90° / 270° werden Breite und Höhe getauscht.
        Bei beliebigen Winkeln wird die Canvas so vergrößert, dass nichts abgeschnitten wird.
        """
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

    @_requires_image
    def apply_flip(self, horizontal: bool) -> None:
        """Spiegelt das Bild horizontal oder vertikal."""
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

    @_requires_image
    def start_crop_circle(self) -> None:
        """Startet den interaktiven Kreis-Zuschnitt."""
        size = min(self._pil.width, self._pil.height)
        self._start_crop_overlay(size, size, is_circle=True)

    @_requires_image
    def start_crop_ratio(self, ratio_w: int, ratio_h: int) -> None:
        """Startet den interaktiven Zuschnitt für ein Seitenverhältnis."""
        iw, ih = self._pil.size
        if iw / ih > ratio_w / ratio_h:
            cw, ch = int(ih * ratio_w / ratio_h), ih
        else:
            cw, ch = iw, int(iw * ratio_h / ratio_w)
        self._start_crop_overlay(cw, ch, is_circle=False)

    def _start_crop_overlay(self, cw: int, ch: int, is_circle: bool) -> None:
        self._cancel_crop_overlay()
        self._crop_overlay = CropOverlayItem(
            self._pil.width, self._pil.height, cw, ch, is_circle)
        self._scene.addItem(self._crop_overlay)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.cropModeChanged.emit(True)
        label = "Kreis" if is_circle else f"{cw} × {ch} px"
        self.statusMsg.emit(
            f"✂  Ausschnitt verschieben  [{label}]  —  dann ✓ Anwenden klicken")

    def confirm_crop(self) -> None:
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

    def cancel_crop(self) -> None:
        """Bricht den Zuschnitt ab ohne Änderung."""
        self._cancel_crop_overlay()
        self.cropModeChanged.emit(False)
        self.set_tool(self._tool)
        self.statusMsg.emit("Zuschnitt abgebrochen")

    def _cancel_crop_overlay(self) -> None:
        if self._crop_overlay is not None:
            self._scene.removeItem(self._crop_overlay)
            self._crop_overlay = None
        self._crop_dragging      = False
        self._crop_resizing      = False
        self._crop_resize_corner = -1


# ─────────────────────────────────────────────────────────────
# Haupt-Fenster
# ─────────────────────────────────────────────────────────────

class _Theme:
    """Zentrale UI-Farbpalette.

    Bündelt die im Stylesheet mehrfach wiederholten Farbwerte an einer
    Stelle, damit künftige UI-Erweiterungen konsistente Farben nutzen.
    Die Werte sind exakt die zuvor inline verwendeten – das
    Erscheinungsbild ändert sich nicht (Stylesheets bleiben
    byte-identisch).
    """
    ACCENT      = "#4a90d9"   # Hervorhebung: aktiver Tab, Slider, Auswahl
    BG_PANEL    = "#1a1a1a"   # rechtes Panel / Tab-Pane / Statusleiste
    BG_TABBAR   = "#141414"   # Tab-Leisten-Hintergrund
    BORDER      = "#3a3a3a"   # Rahmen / Trennlinien / Slider-Groove
    DIVIDER     = "#2a2a2a"   # dünne Trennflächen
    TEXT_BRIGHT = "#e0e0e0"   # heller Text (aktiver Tab)


TOOL_STYLE = f"""
    QToolButton {{
        color: #ccc; font-size: 24px; border: none;
        border-radius: 9px; background: {_Theme.BORDER};
    }}
    QToolButton:checked        {{ background: {_Theme.ACCENT}; color: white; }}
    QToolButton:hover          {{ background: #4f4f4f; }}
    QToolButton:checked:hover  {{ background: {_Theme.ACCENT}; color: white; }}
    QToolButton:disabled       {{ color: #555; background: {_Theme.DIVIDER}; }}
"""

SLD_STYLE = f"""
    QSlider::groove:horizontal {{ height: 4px; background: {_Theme.BORDER}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        background: {_Theme.ACCENT}; width: 14px; height: 14px;
        margin: -5px 0; border-radius: 7px;
    }}
"""


class TopIconTabBar(QTabBar):
    """Tab-Bar mit großem Icon oben und zentriertem Text darunter.

    Qt zeichnet das Icon standardmäßig links neben dem Text – ein reines
    Stylesheet kann das nicht ändern. Deshalb wird das Tab hier manuell
    gemalt: Tab-Hintergrund/-Rahmen weiter über den Stil (Stylesheet),
    Icon und Text aber selbst und vertikal gestapelt.
    """

    _ICON_TOP_PAD = 11    # Abstand Tab-Oberkante → Icon
    _ICON_TEXT_GAP = 6    # Abstand Icon → Text
    _TEXT_BOTTOM_PAD = 9  # Abstand Text → Tab-Unterkante
    _TEXT_SIDE_PAD = 8    # seitlicher Mindestabstand Text → Tab-Rand

    def __init__(self, icon_px: int = 30, parent=None) -> None:
        super().__init__(parent)
        self._icon_px = icon_px
        # Breiten werden selbst gleichmäßig auf die volle Breite verteilt –
        # Qts proportionale Expand-Heuristik darf das nicht verändern.
        self.setExpanding(False)

    def _text_font(self, bold: bool = False) -> QFont:
        f = self.font()
        f.setPixelSize(12)
        f.setBold(bold)
        return f

    def _wrap(self, text: str, fm: QFontMetrics, max_w: int) -> list:
        """Bricht ein zu breites Label in max. 2 Zeilen um (an '/' oder Space)."""
        if max_w <= 0 or fm.horizontalAdvance(text) <= max_w:
            return [text]
        if "/" in text:
            i = text.index("/")
            return [text[:i + 1], text[i + 1:].strip()]
        if " " in text:
            i = text.index(" ")
            return [text[:i], text[i + 1:]]
        mid = len(text) // 2
        return [text[:mid], text[mid:]]

    def _equal_width(self, index: int) -> int:
        """Volle Spaltenbreite gleichmäßig auf alle Tabs aufteilen.

        Die Bar-Breite leitet sich aus der Summe der Tab-SizeHints ab –
        deshalb wird hier die Breite des übergeordneten QTabWidget
        verwendet (sonst zirkuläre Abhängigkeit → degenerierte Breite).
        """
        n = self.count() or 1
        parent = self.parentWidget()
        total = parent.width() if parent is not None else 0
        if total <= 0:
            total = self.width()
        if total <= 0:                  # vor dem ersten Layout
            return max(self._icon_px + 20, 80)
        base = total // n
        rem = total - base * n          # Restpixel auf die ersten Tabs verteilen
        return base + (1 if index < rem else 0)

    def tabSizeHint(self, index: int) -> QSize:
        fm = QFontMetrics(self._text_font(bold=True))
        # immer Platz für 2 Zeilen → alle Tabs gleich hoch
        height = (self._ICON_TOP_PAD + self._icon_px + self._ICON_TEXT_GAP
                  + 2 * fm.height() + self._TEXT_BOTTOM_PAD)
        return QSize(self._equal_width(index), height)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Tab-Geometrie an die neue Bar-Breite anpassen (gleiche Breiten).
        self.updateGeometry()

    def paintEvent(self, event) -> None:
        painter = QStylePainter(self)
        opt = QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            rect = self.tabRect(i)

            # Tab-Form (Hintergrund, Auswahl-Unterstrich) über den Stil –
            # Icon/Text vom Stil ausblenden, da selbst gezeichnet wird.
            opt.text = ""
            opt.icon = QIcon()
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, opt)

            selected = bool(opt.state & QStyle.StateFlag.State_Selected)
            hovered = bool(opt.state & QStyle.StateFlag.State_MouseOver)
            enabled = bool(opt.state & QStyle.StateFlag.State_Enabled)

            # Icon zentriert oben
            icon = self.tabIcon(i)
            if not icon.isNull():
                mode = (QIcon.Mode.Normal if enabled
                        else QIcon.Mode.Disabled)
                pm = icon.pixmap(QSize(self._icon_px, self._icon_px), mode)
                ix = rect.x() + (rect.width() - self._icon_px) // 2
                iy = rect.y() + self._ICON_TOP_PAD
                painter.drawPixmap(ix, iy, pm)

            # Text (1–2 Zeilen) zentriert darunter
            if not enabled:
                color = QColor("#555")
            elif selected:
                color = QColor("#e0e0e0")
            elif hovered:
                color = QColor("#aaaaaa")
            else:
                color = QColor("#777777")
            font = self._text_font(bold=selected)
            painter.setFont(font)
            painter.setPen(color)
            fm = QFontMetrics(font)
            lines = self._wrap(self.tabText(i), fm,
                               rect.width() - 2 * self._TEXT_SIDE_PAD)
            line_h = fm.height()
            block_top = (rect.y() + self._ICON_TOP_PAD + self._icon_px
                         + self._ICON_TEXT_GAP)
            # Zeilenblock vertikal in der für 2 Zeilen reservierten Höhe zentrieren
            y0 = block_top + (2 * line_h - len(lines) * line_h) // 2
            for k, line in enumerate(lines):
                r = QRect(rect.x(), y0 + k * line_h, rect.width(), line_h)
                painter.drawText(
                    r,
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                    line)


class TopIconTabWidget(QTabWidget):
    """QTabWidget, das die TopIconTabBar verwendet (setTabBar ist protected)."""

    def __init__(self, icon_px: int = 30, parent=None) -> None:
        super().__init__(parent)
        self.setTabBar(TopIconTabBar(icon_px, self))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Bar deterministisch auf die volle Spaltenbreite ziehen – das löst
        # in der Bar layoutTabs() aus, sodass alle Tabs gleich breit werden
        # und die ganze Breite füllen.
        bar = self.tabBar()
        g = bar.geometry()
        if g.width() != self.width():
            bar.setGeometry(0, g.y(), self.width(), g.height())


class SettingsDialog(QDialog):
    """Dialog zum Bearbeiten persistenter Nutzereinstellungen."""

    FORMATS = ["PNG", "JPEG", "WebP", "TIFF"]
    FORMAT_FILTERS = {
        "PNG":  "PNG (*.png)",
        "JPEG": "JPEG (*.jpg)",
        "WebP": "WebP (*.webp)",
        "TIFF": "TIFF (*.tif)",
    }

    def __init__(self, settings: QSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Einstellungen")
        self.setMinimumWidth(520)
        self._settings = settings
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Einstellungen")
        title.setStyleSheet("font-size: 15px; font-weight: bold;")
        lay.addWidget(title)

        # Verzeichnis zum Öffnen
        open_grp = QGroupBox("Standard-Verzeichnis zum Öffnen")
        open_lay = QHBoxLayout(open_grp)
        self._open_dir_edit = QLineEdit()
        self._open_dir_edit.setPlaceholderText("Leer = zuletzt verwendetes Verzeichnis")
        open_lay.addWidget(self._open_dir_edit)
        btn_open = QPushButton("…")
        btn_open.setFixedWidth(32)
        btn_open.clicked.connect(self._pick_open_dir)
        open_lay.addWidget(btn_open)
        lay.addWidget(open_grp)

        # Verzeichnis zum Speichern/Export
        save_grp = QGroupBox("Standard-Verzeichnis für Export / Speichern")
        save_lay = QHBoxLayout(save_grp)
        self._save_dir_edit = QLineEdit()
        self._save_dir_edit.setPlaceholderText("Leer = zuletzt verwendetes Verzeichnis")
        save_lay.addWidget(self._save_dir_edit)
        btn_save = QPushButton("…")
        btn_save.setFixedWidth(32)
        btn_save.clicked.connect(self._pick_save_dir)
        save_lay.addWidget(btn_save)
        lay.addWidget(save_grp)

        # Bevorzugtes Dateiformat
        fmt_grp = QGroupBox("Bevorzugtes Bilddateiformat")
        fmt_lay = QHBoxLayout(fmt_grp)
        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(self.FORMATS)
        self._fmt_combo.setFixedWidth(140)
        fmt_lay.addWidget(self._fmt_combo)
        fmt_lay.addStretch()
        lay.addWidget(fmt_grp)

        # Protokolldatei
        log_grp = QGroupBox("Protokolldatei")
        log_lay = QHBoxLayout(log_grp)
        self._log_path_edit = QLineEdit()
        self._log_path_edit.setReadOnly(True)
        self._log_path_edit.setToolTip(
            "Pfad der Log-Datei (markieren zum Kopieren)")
        log_lay.addWidget(self._log_path_edit)
        btn_log = QPushButton("Ordner öffnen")
        btn_log.clicked.connect(self._open_log_dir)
        log_lay.addWidget(btn_log)
        lay.addWidget(log_grp)

        lay.addStretch()

        # OK / Abbrechen
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("OK")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self._save_and_accept)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

    def _pick_open_dir(self) -> None:
        start = self._open_dir_edit.text().strip() or str(Path.home())
        d = QFileDialog.getExistingDirectory(
            self, "Verzeichnis zum Öffnen wählen", start)
        if d:
            self._open_dir_edit.setText(d)

    def _pick_save_dir(self) -> None:
        start = self._save_dir_edit.text().strip() or str(Path.home())
        d = QFileDialog.getExistingDirectory(
            self, "Verzeichnis für Export/Speichern wählen", start)
        if d:
            self._save_dir_edit.setText(d)

    def _open_log_dir(self) -> None:
        log_file = current_log_file()
        target = log_file.parent if log_file.parent.exists() else Path.home()
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(target))):
            QMessageBox.warning(
                self, "Protokolldatei",
                f"Ordner konnte nicht geöffnet werden:\n{target}")

    def _load(self) -> None:
        self._open_dir_edit.setText(self._settings.value("open_dir", ""))
        self._save_dir_edit.setText(self._settings.value("save_dir", ""))
        fmt = self._settings.value("preferred_format", "PNG")
        idx = self._fmt_combo.findText(fmt)
        if idx >= 0:
            self._fmt_combo.setCurrentIndex(idx)
        self._log_path_edit.setText(str(current_log_file()))

    def _save_and_accept(self) -> None:
        self._settings.setValue("open_dir", self._open_dir_edit.text().strip())
        self._settings.setValue("save_dir", self._save_dir_edit.text().strip())
        self._settings.setValue("preferred_format", self._fmt_combo.currentText())
        self.accept()


class MainWindow(QMainWindow):
    # Anzahl der zuletzt geöffneten Bilder, die im Datei-Menü angezeigt werden.
    RECENT_MAX = 10
    SETTINGS_RECENT_KEY = "recent_files"

    _TAB_STYLE = f"""
        QTabWidget::pane {{ border: none; background: {_Theme.BG_PANEL}; }}
        QTabBar {{ background: {_Theme.BG_TABBAR}; }}
        QTabBar::tab {{
            background: #1e1e1e; color: #666;
            padding: 10px 0px; min-width: 94px;
            font-size: 12px; border: none;
            border-bottom: 3px solid transparent;
        }}
        QTabBar::tab:selected {{
            color: {_Theme.TEXT_BRIGHT}; background: {_Theme.BG_PANEL};
            border-bottom: 3px solid {_Theme.ACCENT}; font-weight: bold;
        }}
        QTabBar::tab:hover:!selected {{ color: #aaa; background: #242424; }}
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"BgRemover Pro {__version__}")
        self.setMinimumSize(_WINDOW_MIN_W, _WINDOW_MIN_H)
        self._bg_color   = QColor(255, 255, 255)
        self._ai_thread: QThread | None = None
        self._ai_worker: AIWorker | None = None
        # Canvas-Version zum Startzeitpunkt der KI: verhindert, dass ein
        # verspätet eintreffendes Ergebnis ein inzwischen geladenes anderes
        # Bild überschreibt. Robuster als Objekt-Identität (is-Vergleich).
        self._ai_input_version: int = -1
        # Speicher-Pfad des aktuellen Bildes (für Quick-Save ⌘S).
        # Wird beim Laden eines neuen Bildes zurückgesetzt.
        self._save_path: str | None = None
        # Persistente Einstellungen (Recent-Files etc.).
        self._settings = QSettings("BgRemover", "BgRemover")
        # Submenü-Referenz wird in _build_menu gesetzt
        self._recent_menu = None
        # Asynchrones Bildladen
        self._load_thread: QThread | None = None
        # rembg-Warmup (Hintergrund-Modellladung)
        self._warmup_thread: QThread | None = None
        self._warmup_done = False
        self._build_ui()
        self._build_menu()
        if REMBG_AVAILABLE:
            self._start_rembg_warmup()

    # ── Panel-Hilfsmethoden (ehem. nested in _build_right_panel) ─

    @staticmethod
    def _make_section(title: str, accent: str = "#4a90d9") -> tuple:
        """Sektion ohne QGroupBox – farbiger Titel + dünne Trennlinie."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        v = QVBoxLayout(container)
        v.setSpacing(10)
        v.setContentsMargins(0, 14, 0, 10)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            color: {accent};
            font-size: 13px;
            font-weight: bold;
            background: transparent;
            padding: 2px 0 4px 8px;
            border-left: 3px solid {accent};
        """)
        v.addWidget(title_lbl)
        return container, v

    @staticmethod
    def _make_label(text: str, color: str = "#888", size: int = 12) -> QLabel:
        """Einfaches Info-Label mit anpassbarer Farbe und Schriftgrösse."""
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {color}; font-size: {size}px; background: transparent;")
        lbl.setWordWrap(True)
        return lbl

    @staticmethod
    def _make_icon_row(icon_name: str, text: str, color: str = "#888",
                       size: int = 12, icon_px: int = 18) -> QWidget:
        """Info-Zeile: Werkzeug-Icon (wie in der Toolbar) + Text, klein."""
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        ic = QLabel()
        ic.setPixmap(make_tool_icon(icon_name, icon_px)
                     .pixmap(QSize(icon_px, icon_px)))
        ic.setFixedSize(icon_px, icon_px)
        ic.setStyleSheet("background: transparent;")
        txt = QLabel(text)
        txt.setStyleSheet(
            f"color: {color}; font-size: {size}px; background: transparent;")
        txt.setWordWrap(True)
        h.addWidget(ic, 0, Qt.AlignmentFlag.AlignVCenter)
        h.addWidget(txt, 1)
        return row

    @staticmethod
    def _make_hdivider() -> QWidget:
        """Dünne horizontale Trennlinie für das rechte Panel."""
        f = QWidget()
        f.setFixedHeight(1)
        f.setStyleSheet(f"background: {_Theme.DIVIDER};")
        return f

    @staticmethod
    def _make_scroll_tab() -> tuple:
        """Gibt (outer_widget, inner_layout) mit ScrollArea zurück."""
        outer_w = QWidget()
        outer_w.setStyleSheet(f"background: {_Theme.BG_PANEL};")
        outer_lay = QVBoxLayout(outer_w)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: #1a1a1a; border: none; }
            QScrollBar:vertical { background: #1a1a1a; width: 6px; margin: 0; }
            QScrollBar::handle:vertical {
                background: #3a3a3a; border-radius: 3px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        inner_w = QWidget()
        inner_w.setStyleSheet(f"background: {_Theme.BG_PANEL};")
        inner_lay = QVBoxLayout(inner_w)
        inner_lay.setContentsMargins(16, 16, 16, 16)
        inner_lay.setSpacing(14)
        scroll.setWidget(inner_w)
        outer_lay.addWidget(scroll)
        return outer_w, inner_lay

    @staticmethod
    def _make_panel_btn(label: str, bg: str, fg: str, hover: str,
                        tooltip: str = "", height: int = 36,
                        icon_name: str = "") -> QPushButton:
        """Stilisierter Aktions-Button für das rechte Panel."""
        b = QPushButton(label)
        b.setStyleSheet(f"""
            QPushButton {{
                background: {bg}; color: {fg}; border: none;
                border-radius: 8px; padding: 0 14px;
                font-size: 12px; font-weight: 500;
                min-height: {height}px; text-align: center;
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

    @staticmethod
    def _make_slider(lo: int, hi: int, val: int, tip: str = "") -> QSlider:
        """Horizontaler Schieberegler mit einheitlichem Panel-Stil."""
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(lo, hi)
        s.setValue(val)
        s.setStyleSheet(SLD_STYLE)
        if tip:
            s.setToolTip(tip)
        return s

    # ── UI aufbauen ──────────────────────────────────────────

    def _build_ui(self) -> None:
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

        # Canvas zuerst erzeugen, damit die Crop-Leisten-Buttons weiter
        # unten auf ein bereits zugewiesenes self._canvas verweisen
        # (sonst Forward-Reference im Lambda → mypy has-type).
        self._canvas = ImageCanvas()
        self._canvas.statusMsg.connect(self.statusBar().showMessage)
        self._canvas.historyChanged.connect(self._on_history_changed)
        self._canvas.cropModeChanged.connect(self._on_crop_mode_changed)
        self._canvas.imageLoaded.connect(self._on_image_loaded)
        self._canvas.loadRequested.connect(self._load_image_async)

        # ── Crop-Bestätigungsleiste (initial versteckt) ───────
        self._crop_bar = QFrame()
        self._crop_bar.setStyleSheet(
            "QFrame { background: #1e3020; border-bottom: 1px solid #3a7a4a; }")
        self._crop_bar.setFixedHeight(_CROP_BAR_HEIGHT)
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

        self._hist_popup: QDialog | None = None

        cv_lay.addWidget(self._canvas, 1)

        root.addWidget(canvas_container, 1)
        root.addWidget(self._build_right_panel())

        sb = QStatusBar()
        sb.setStyleSheet("QStatusBar { background:#1a1a1a; color:#777; font-size:11px; border-top:1px solid #333; }")
        self.setStatusBar(sb)
        sb.showMessage("Bild öffnen: Datei → Öffnen  oder  per Drag & Drop auf die Arbeitsfläche")

    def _build_toolbar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(_TOOLBAR_WIDTH)
        frame.setStyleSheet("QFrame { background: #242424; border-right: 1px solid #3a3a3a; }")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(9, 16, 9, 16)
        lay.setSpacing(8)

        self._btn_grp = QButtonGroup(self)
        self._btn_grp.setExclusive(True)

        def tbtn(icon_name: str, tip: str, tool: str) -> QToolButton:
            b = QToolButton()
            b.setIcon(make_tool_icon(icon_name, 38))
            b.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
            b.setToolTip(tip)
            b.setCheckable(True)
            b.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
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
        self._btn_lasso  = tbtn("lasso",
            "Polygon-Lasso\nKlicken setzt Punkte · Doppelklick schließt Polygon\n"
            "Shift = addieren  ·  Ctrl = subtrahieren  ·  Esc = abbrechen", TOOL_LASSO)
        self._btn_wand.setChecked(True)

        # Trennlinie
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{_Theme.BORDER}")
        lay.addSpacing(4); lay.addWidget(sep); lay.addSpacing(4)

        self._btn_ai = QToolButton()
        self._btn_ai.setIcon(make_tool_icon("ai", 38))
        self._btn_ai.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
        self._btn_ai.setToolTip(
            "KI-Hintergrundentfernung (rembg)\nEntfernt den Hintergrund vollautomatisch"
            if REMBG_AVAILABLE else
            "rembg nicht installiert\n→ bash setup_bgremover.sh")
        self._btn_ai.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
        self._btn_ai.setStyleSheet(TOOL_STYLE)
        self._btn_ai.setEnabled(REMBG_AVAILABLE)
        self._btn_ai.clicked.connect(self._run_ai)
        lay.addWidget(self._btn_ai, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Trennlinie
        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color:{_Theme.BORDER}")
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
            b.setIcon(make_tool_icon(icon_name, 38))
            b.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
            b.setToolTip(tip)
            b.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
            b.setStyleSheet(HIST_STYLE)
            b.clicked.connect(slot)
            lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
            return b

        hist_btn("undo",     "Rückgängig  (Cmd+Z)\nLetzten Bearbeitungsschritt rückgängig machen",
                 lambda: self._canvas.undo())
        hist_btn("redo",     "Wiederherstellen  (Cmd+Shift+Z)\nLetzten rückgängig gemachten Schritt wiederherstellen",
                 lambda: self._canvas.redo())
        hist_btn("restore",  "Original wiederherstellen\nAlle Bearbeitungen verwerfen",
                 lambda: self._canvas.restore_original())
        self._btn_history = hist_btn(
            "history",
            "Änderungshistorie\nZeigt alle bisherigen Bearbeitungsschritte.\n"
            "Doppelklick auf Eintrag → zu diesem Schritt zurück",
            self._toggle_history_popup)

        lay.addStretch()

        def mini_btn(icon_name: str, tip: str, slot) -> QToolButton:
            b = QToolButton()
            b.setIcon(make_tool_icon(icon_name, 38))
            b.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
            b.setToolTip(tip)
            b.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
            b.setStyleSheet(TOOL_STYLE)
            b.clicked.connect(slot)
            lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
            return b

        mini_btn("open", "Bild öffnen  (Cmd+O)",   self._open_image)
        mini_btn("save", "Bild speichern  (Cmd+S)", self._save)
        return frame

    def _build_right_panel(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(_RIGHT_PANEL_WIDTH)
        frame.setStyleSheet("QFrame { background: #1a1a1a; border-left: 1px solid #333; }")
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Tab-Widget ────────────────────────────────────────
        tabs = TopIconTabWidget(_TAB_ICON_PX)
        tabs.setDocumentMode(True)
        tabs.setStyleSheet(self._TAB_STYLE)
        tabs.setUsesScrollButtons(False)   # niemals Scroll-Pfeile — alle Tabs sichtbar
        tabs.setIconSize(QSize(_TAB_ICON_PX, _TAB_ICON_PX))
        outer.addWidget(tabs)

        # Jeder Builder hängt genau einen Tab an – Aufrufreihenfolge = Tab-Index.
        self._build_tab_selection(tabs)
        self._build_tab_background(tabs)
        self._build_tab_transform(tabs)
        self._build_tab_shape(tabs)
        return frame

    # ── Tab-Builder (je genau ein Tab) ───────────────────────

    def _build_tab_selection(self, tabs: TopIconTabWidget) -> None:
        """Tab 1 – Auswahl 🎯: Werkzeug-Hinweise, Toleranz/Pinsel, Morphologie."""
        t1, l1 = self._make_scroll_tab()
        idx = tabs.addTab(t1, "Auswahl")
        tabs.setTabIcon(idx, make_tool_icon("clear_sel", _TAB_ICON_PX))
        tabs.setTabToolTip(idx, "Auswahl – Zauberstab, Pinsel, Radiergummi")

        g_tool, gt = self._make_section("Werkzeug", "#4a90d9")
        hint_box = QWidget()
        hint_box.setStyleSheet("background:#1e2a38; border-radius:7px;")
        hint_lay = QVBoxLayout(hint_box)
        hint_lay.setContentsMargins(10, 8, 10, 8)
        hint_lay.setSpacing(3)
        for icon_name, txt in [
            ("wand",   "Zauberstab — Farbfläche auswählen"),
            ("brush",  "Pinsel — Auswahl aufmalen"),
            ("eraser", "Radiergummi — Auswahl entfernen"),
            ("lasso",  "Polygon-Lasso — Punkte klicken, Doppelklick abschließen"),
        ]:
            hint_lay.addWidget(self._make_icon_row(icon_name, txt, "#7aacdd", 11))
        hint_lay.addWidget(self._make_hdivider())
        _sub_mod = "Cmd" if _IS_MACOS else "Ctrl"
        hint_lay.addWidget(self._make_label("Shift+Klick  →  Auswahl addieren", "#888", 11))
        hint_lay.addWidget(self._make_label(f"{_sub_mod}+Klick   →  Auswahl subtrahieren", "#888", 11))
        gt.addWidget(hint_box)
        l1.addWidget(g_tool)

        g_sel, gs = self._make_section("Einstellungen", "#4a90d9")
        self._lbl_tol = self._make_label("Toleranz (Zauberstab):  30", "#aaa")
        self._sld_tol = self._make_slider(0, 255, 30,
            "Steuert wie ähnlich Farben sein müssen um ausgewählt zu werden.\n"
            "Niedrig = nur sehr ähnliche Farben · Hoch = viele Farbtöne")
        self._sld_tol.valueChanged.connect(lambda v: (
            self._canvas.set_tolerance(v),
            self._lbl_tol.setText(f"Toleranz (Zauberstab):  {v}")
        ))
        gs.addWidget(self._lbl_tol)
        gs.addWidget(self._sld_tol)
        gs.addWidget(self._make_hdivider())
        self._lbl_brush = self._make_label("Pinselgröße:  30 px", "#aaa")
        self._sld_brush = self._make_slider(4, 200, 30,
            "Größe des Pinsel-/Radiergummi-Werkzeugs in Pixeln")
        self._sld_brush.valueChanged.connect(lambda v: (
            self._canvas.set_brush_size(v),
            self._lbl_brush.setText(f"Pinselgröße:  {v} px")
        ))
        gs.addWidget(self._lbl_brush)
        gs.addWidget(self._sld_brush)
        l1.addWidget(g_sel)

        btn_clr = self._make_panel_btn("Auswahl aufheben", "#2a2a2a", "#c0c0c0", "#363636",
                      "Hebt die aktuelle Auswahl auf (auch: Esc-Taste)",
                      icon_name="clear_sel")
        btn_clr.clicked.connect(lambda _=False: self._canvas.clear_selection())
        l1.addWidget(btn_clr)

        btn_inv = self._make_panel_btn("Auswahl invertieren", "#2a2a2a", "#c0c0c0", "#363636",
                      "Tauscht aus- und nicht-ausgewählte Bereiche  (⌘⇧I)",
                      icon_name="clear_sel")
        btn_inv.clicked.connect(lambda _=False: self._canvas.invert_selection())
        l1.addWidget(btn_inv)

        # Auswahl erweitern / schrumpfen mit Radius-Spinbox
        morph_row = QHBoxLayout(); morph_row.setSpacing(6)
        self._spin_morph = QSpinBox()
        self._spin_morph.setRange(1, 20); self._spin_morph.setValue(2)
        self._spin_morph.setSuffix(" px")
        self._spin_morph.setFixedWidth(72)
        self._spin_morph.setToolTip(
            "Radius in Pixeln für Erweitern/Schrumpfen der Auswahl")
        self._spin_morph.setStyleSheet(
            "QSpinBox { background:#222; color:#ddd; border:1px solid #3a3a3a;"
            " border-radius:6px; padding:3px 5px; font-size:12px; }"
            "QSpinBox::up-button, QSpinBox::down-button { width:18px; }")
        btn_expand = self._make_panel_btn("➕ Erweitern", "#1a3a1a", "#a0d0a0", "#2a5a2a",
                         "Erweitert die Auswahl um den eingestellten Radius")
        btn_expand.clicked.connect(
            lambda _=False: self._canvas.expand_selection(self._spin_morph.value()))
        btn_shrink = self._make_panel_btn("➖ Schrumpfen", "#3a1a1a", "#d0a0a0", "#5a2a2a",
                         "Schrumpft die Auswahl um den eingestellten Radius")
        btn_shrink.clicked.connect(
            lambda _=False: self._canvas.shrink_selection(self._spin_morph.value()))
        morph_row.addWidget(self._spin_morph)
        morph_row.addWidget(btn_expand, 1)
        morph_row.addWidget(btn_shrink, 1)
        l1.addLayout(morph_row)

        l1.addStretch()

    def _build_tab_background(self, tabs: TopIconTabWidget) -> None:
        """Tab 2 – Hintergrund 🖼: transparent machen oder Farbe ersetzen."""
        t2, l2 = self._make_scroll_tab()
        idx = tabs.addTab(t2, "Hintergrund")
        tabs.setTabIcon(idx, make_tool_icon("bg", _TAB_ICON_PX))
        tabs.setTabToolTip(idx, "Hintergrund – Entfernen, Farbe ersetzen")

        g_bg, gb = self._make_section("Hintergrund bearbeiten", "#e05555")
        btn_rem = self._make_panel_btn("Entfernen (transparent)", "#6a1a1a", "white", "#882020",
                      "Macht den ausgewählten Bereich vollständig transparent.\n"
                      "Tipp: Zuerst mit Zauberstab Hintergrund auswählen.",
                      height=38, icon_name="transparency")
        btn_rem.clicked.connect(lambda _=False: self._canvas.apply_remove())
        gb.addWidget(btn_rem)

        gb.addWidget(self._make_hdivider())
        gb.addWidget(self._make_label("Farbe wählen und Auswahl einfärben:", "#888"))
        color_row = QHBoxLayout(); color_row.setSpacing(8)
        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(_COLOR_BTN_SIZE, _COLOR_BTN_SIZE)
        self._color_btn.setToolTip("Klicken um Ersatz-Hintergrundfarbe zu wählen")
        self._color_btn.setStyleSheet(
            "QPushButton { border-radius:6px; border:2px solid #555; }"
            "QPushButton:hover { border-color: #4a90d9; }")
        self._color_btn.clicked.connect(lambda _=False: self._pick_color())
        self._update_color_btn()
        color_row.addWidget(self._color_btn)
        btn_repl = self._make_panel_btn("Farbe ersetzen", "#143a5a", "white", "#1e5080",
                       "Füllt den ausgewählten Bereich mit der gewählten Farbe",
                       icon_name="bg")
        btn_repl.clicked.connect(lambda _=False: self._canvas.apply_replace(self._bg_color))
        color_row.addWidget(btn_repl, 1)
        gb.addLayout(color_row)
        l2.addWidget(g_bg)

        l2.addStretch()

    def _build_tab_transform(self, tabs: TopIconTabWidget) -> None:
        """Tab 3 – Transform ⟲: Drehen (Schnell + freier Winkel) und Spiegeln."""
        t3, l3 = self._make_scroll_tab()
        idx = tabs.addTab(t3, "Drehen/Spiegeln")
        tabs.setTabIcon(idx, make_tool_icon("transparency", _TAB_ICON_PX))
        tabs.setTabToolTip(idx, "Transform – Drehen, Spiegeln")

        g_rot, gr2 = self._make_section("Drehen", "#e09a30")
        ROT_BG = "#2e2510"; ROT_FG = "#f0c060"; ROT_HV = "#4a3a18"

        # Schnell-Drehung
        gr2.addWidget(self._make_label("Schnell-Drehung:", "#888"))
        row_q1 = QHBoxLayout(); row_q1.setSpacing(6)
        for label, deg, tip in [
            ("↺ 90° links",   90,  "90° gegen den Uhrzeigersinn drehen"),
            ("↻ 90° rechts", -90, "90° im Uhrzeigersinn drehen"),
        ]:
            b = self._make_panel_btn(label, ROT_BG, ROT_FG, ROT_HV, tip)
            b.clicked.connect(lambda _=False, d=deg: self._canvas.apply_rotate(d))
            row_q1.addWidget(b)
        gr2.addLayout(row_q1)

        row_q2 = QHBoxLayout(); row_q2.setSpacing(6)
        for label, deg, tip in [
            ("↺ 180°",  180, "Bild um 180° drehen"),
            ("↺ 270°",  270, "270° gegen den Uhrzeigersinn (= 90° rechts)"),
        ]:
            b = self._make_panel_btn(label, ROT_BG, ROT_FG, ROT_HV, tip)
            b.clicked.connect(lambda _=False, d=deg: self._canvas.apply_rotate(d))
            row_q2.addWidget(b)
        gr2.addLayout(row_q2)

        gr2.addWidget(self._make_hdivider())
        gr2.addWidget(self._make_label("Freier Winkel:", "#888"))
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

        btn_rot_free = self._make_panel_btn("Winkel anwenden", ROT_BG, ROT_FG, ROT_HV,
                           "Dreht das Bild um den eingestellten Winkel.\n"
                           "Transparente Ecken entstehen bei schrägen Winkeln.",
                           icon_name="undo")
        btn_rot_free.clicked.connect(
            lambda _=False: self._canvas.apply_rotate(self._spin_rot.value()))
        gr2.addWidget(btn_rot_free)
        l3.addWidget(g_rot)

        g_flip, gf = self._make_section("Spiegeln", "#30a0a0")
        row_flip = QHBoxLayout(); row_flip.setSpacing(6)
        btn_fh = self._make_panel_btn("Horizontal", "#0e2a2a", "#7adada", "#1a4040",
                     "Bild horizontal spiegeln (links ↔ rechts)")
        btn_fh.clicked.connect(lambda _=False: self._canvas.apply_flip(True))
        row_flip.addWidget(btn_fh)
        btn_fv = self._make_panel_btn("Vertikal", "#0e2a2a", "#7adada", "#1a4040",
                     "Bild vertikal spiegeln (oben ↕ unten)")
        btn_fv.clicked.connect(lambda _=False: self._canvas.apply_flip(False))
        row_flip.addWidget(btn_fv)
        gf.addLayout(row_flip)
        l3.addWidget(g_flip)
        l3.addStretch()

    def _build_tab_shape(self, tabs: TopIconTabWidget) -> None:
        """Tab 4 – Form & Zuschnitt ⬤: Ecken abrunden, Format-/Crop-Auswahl."""
        t4, l4 = self._make_scroll_tab()
        idx = tabs.addTab(t4, "Form")
        tabs.setTabIcon(idx, make_tool_icon("form", _TAB_ICON_PX))
        tabs.setTabToolTip(idx, "Form & Zuschnitt – Ecken abrunden, Format-Auswahl")

        g_corner, gc = self._make_section("Ecken abrunden", "#30c060")
        self._lbl_corner = self._make_label("Radius:  0 px", "#aaa")
        self._sld_corner = self._make_slider(0, 500, 0,
            "Radius der Eckenrundung in Pixeln.\n0 = keine Rundung · 500 = maximal rund")
        self._sld_corner.valueChanged.connect(
            lambda v: self._lbl_corner.setText(f"Radius:  {v} px"))
        gc.addWidget(self._lbl_corner)
        gc.addWidget(self._sld_corner)
        btn_corner = self._make_panel_btn("Ecken abrunden", "#0e2a14", "#7add9a", "#1a4520",
                         "Wendet die Eckenrundung an.\n"
                         "Das Ergebnis wird als PNG mit transparenten Ecken gespeichert.",
                         height=38, icon_name="form")
        btn_corner.clicked.connect(
            lambda _=False: self._canvas.apply_round_corners(self._sld_corner.value()))
        gc.addWidget(btn_corner)
        l4.addWidget(g_corner)

        g_fmt, gfm = self._make_section("Ausgabe-Format & Zuschnitt", "#9060d0")

        info_box = QWidget()
        info_box.setStyleSheet("background:#1e1628; border-radius:7px;")
        info_b = QVBoxLayout(info_box)
        info_b.setContentsMargins(10, 8, 10, 8)
        info_b.addWidget(self._make_label(
            "⇲ Format wählen → Rahmen erscheint auf dem Bild\n"
            "• Rahmen verschieben: Mitte ziehen\n"
            "• Größe ändern: Ecken ziehen (Proportionen bleiben)", "#8a7aaa", 10))
        gfm.addWidget(info_box)

        # Kreis + Quadrat
        gfm.addWidget(self._make_label("Sonderformate:", "#777", 10))
        r_special = QHBoxLayout(); r_special.setSpacing(6)
        for label, tip, slot in [
            ("⬤  Kreis",  "Runden Ausschnitt positionieren und zuschneiden",
             self._canvas.start_crop_circle),
            ("■  1 : 1", "Quadratischen Ausschnitt positionieren",
             lambda: self._canvas.start_crop_ratio(1, 1)),
        ]:
            b = self._make_panel_btn(label, "#141e38", "#8aaedd", "#1e2e52", tip)
            b.clicked.connect(lambda _=False, fn=slot: fn())
            r_special.addWidget(b)
        gfm.addLayout(r_special)

        # Querformat
        gfm.addWidget(self._make_hdivider())
        gfm.addWidget(self._make_label("Querformat:", "#777", 10))
        LAND_FORMATS = [
            ("16 : 9", 16, 9), ("4 : 3",  4, 3),
            ("3 : 2",  3, 2),  ("2 : 1",  2, 1),
            ("7 : 4.5", 14, 9),
        ]
        for i in range(0, len(LAND_FORMATS), 2):
            row_fmt = QHBoxLayout(); row_fmt.setSpacing(6)
            for label, rw, rh in LAND_FORMATS[i:i+2]:
                b = self._make_panel_btn(f"▬  {label}", "#1e1428", "#c0a0f0", "#2e1e44",
                        f"Querformat {label} — Ecken ziehen für Größe, Mitte zum Verschieben")
                b.clicked.connect(
                    lambda _=False, w=rw, h=rh: self._canvas.start_crop_ratio(w, h))
                row_fmt.addWidget(b)
            gfm.addLayout(row_fmt)

        # Hochformat
        gfm.addWidget(self._make_hdivider())
        gfm.addWidget(self._make_label("Hochformat:", "#777", 10))
        PORT_FORMATS = [("9 : 16", 9, 16), ("3 : 4", 3, 4)]
        row_port = QHBoxLayout(); row_port.setSpacing(6)
        for label, rw, rh in PORT_FORMATS:
            b = self._make_panel_btn(f"▮  {label}", "#141e28", "#90c8cc", "#1e2e38",
                    f"Hochformat {label} — Ecken ziehen für Größe, Mitte zum Verschieben")
            b.clicked.connect(
                lambda _=False, w=rw, h=rh: self._canvas.start_crop_ratio(w, h))
            row_port.addWidget(b)
        gfm.addLayout(row_port)
        l4.addWidget(g_fmt)
        l4.addStretch()

    def _build_menu(self) -> None:
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

        # Submenü „Zuletzt geöffnet" – wird nach dem ersten load_image
        # mit Inhalt befüllt, persistiert über QSettings.
        self._recent_menu = file_m.addMenu("Zuletzt geöffnet")
        self._rebuild_recent_menu()

        file_m.addSeparator()

        a_save = QAction("Speichern", self)
        a_save.setShortcut(QKeySequence("Ctrl+S"))
        a_save.triggered.connect(self._save)
        file_m.addAction(a_save)

        a_save_as = QAction("Speichern unter…", self)
        a_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        a_save_as.triggered.connect(self._save_as)
        file_m.addAction(a_save_as)

        edit_m = mb.addMenu("Bearbeiten")
        a_undo = QAction("Rückgängig", self)
        a_undo.setShortcut(QKeySequence("Ctrl+Z"))
        a_undo.triggered.connect(self._canvas.undo)
        edit_m.addAction(a_undo)

        a_redo = QAction("Wiederherstellen", self)
        a_redo.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        a_redo.triggered.connect(self._canvas.redo)
        edit_m.addAction(a_redo)

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

        a_invert = QAction("Auswahl invertieren", self)
        a_invert.setShortcut(QKeySequence("Ctrl+Shift+I"))
        a_invert.triggered.connect(self._canvas.invert_selection)
        edit_m.addAction(a_invert)

        a_orig = QAction("Original wiederherstellen", self)
        a_orig.triggered.connect(self._canvas.restore_original)
        edit_m.addAction(a_orig)

        view_m = mb.addMenu("Ansicht")
        a_fit = QAction("Fit to View", self)
        a_fit.setShortcut(QKeySequence("Ctrl+0"))
        a_fit.triggered.connect(lambda: self._canvas.fit_to_view())
        view_m.addAction(a_fit)

        extras_m = mb.addMenu("Extras")
        a_prefs = QAction("Einstellungen…", self)
        a_prefs.setShortcut(QKeySequence("Ctrl+,"))
        a_prefs.triggered.connect(self._open_settings)
        extras_m.addAction(a_prefs)

    # ── Thread-Hilfsmethode ───────────────────────────────────

    def _launch_worker(self, worker: QObject, quit_on: tuple,
                       on_finished=None) -> QThread:
        """Startet *worker* in einem neuen QThread.

        *quit_on* ist ein Tupel von Worker-Signalen, die thread.quit() auslösen
        (typischerweise (worker.finished, worker.error)).
        *on_finished* wird an thread.finished angehängt, falls angegeben.
        """
        thread = QThread(self)
        # Starke Referenz: MainWindow → thread → worker. Ohne sie sammelt
        # CPython den Worker direkt nach dem Aufruf ein (PyQt verbindet
        # Slots gebundener Methoden nur schwach) – run() liefe nie, das
        # Bild würde lautlos nicht geladen.
        thread._worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        for sig in quit_on:
            sig.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        if on_finished is not None:
            thread.finished.connect(on_finished)
        thread.start()
        return thread

    # ── Sauberes Thread-Shutdown beim Schliessen ──────────────

    def _shutdown_thread(self, thread: QThread | None, name: str) -> None:
        """Beendet *thread* sauber, bevor das Fenster zerstört wird.

        Worker-run() macht blockierende C-Aufrufe (rembg) – quit()
        allein reicht nicht. Reihenfolge: quit() → wait(timeout) →
        Notbremse terminate()+wait(), damit das QThread-Objekt nie
        zerstört wird, solange der OS-Thread noch läuft.
        """
        if thread is None or not thread.isRunning():
            return
        thread.quit()
        if not thread.wait(_THREAD_SHUTDOWN_MS):
            logger.warning(
                "Thread '%s' reagierte nicht – wird hart beendet", name)
            thread.terminate()
            thread.wait()

    def closeEvent(self, event) -> None:
        """Stoppt alle Hintergrund-Threads, bevor das Fenster (und damit
        die QThread-C++-Objekte) zerstört wird – sonst stürzt Python
        beim Schliessen ab, solange z. B. der KI-Warmup noch läuft.
        """
        self.statusBar().showMessage("Beende…")
        self._shutdown_thread(self._ai_thread, "KI")
        self._shutdown_thread(self._load_thread, "Bildladen")
        self._shutdown_thread(self._warmup_thread, "rembg-Warmup")
        super().closeEvent(event)

    # ── Slots ─────────────────────────────────────────────────

    def _open_image(self) -> None:
        start_dir = self._settings.value("open_dir", "")
        path, _ = QFileDialog.getOpenFileName(
            self, "Bild öffnen", start_dir,
            "Bilder (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.gif);;"
            "Alle Dateien (*)"
        )
        if path:
            self._load_image_async(path)

    def _load_image_async(self, path: str) -> None:
        """Lädt ein Bild im Hintergrund-Thread, damit die UI nicht blockt."""
        if self._load_thread is not None and self._load_thread.isRunning():
            self.statusBar().showMessage("Lädt bereits ein Bild…")
            return
        self.statusBar().showMessage(f"⏳ Lädt: {Path(path).name}…")
        worker = ImageLoadWorker(path)
        worker.finished.connect(self._on_image_load_done)
        worker.error.connect(self._on_image_load_error)
        self._load_thread = self._launch_worker(
            worker,
            quit_on=(worker.finished, worker.error),
            on_finished=self._on_load_thread_finished,
        )

    def _on_image_load_done(self, img, path: str) -> None:
        self._canvas.apply_loaded_image(img, path)

    def _on_image_load_error(self, msg: str) -> None:
        self.statusBar().showMessage(f"Ladefehler: {msg}")

    def _on_load_thread_finished(self) -> None:
        self._load_thread = None

    # ── rembg-Warmup ────────────────────────────────────────────

    def _start_rembg_warmup(self) -> None:
        """Lädt das rembg-Modell im Hintergrund, damit der erste KI-Klick
        nicht spürbar wartet."""
        self.statusBar().showMessage("🤖 KI-Modell wird geladen…")
        worker = RembgWarmupWorker()
        self._warmup_thread = self._launch_worker(
            worker,
            quit_on=(worker.finished,),
            on_finished=self._on_warmup_done,
        )

    def _on_warmup_done(self) -> None:
        self._warmup_done = True
        self._warmup_thread = None
        self.statusBar().showMessage("🤖 KI bereit")

    def _save(self) -> None:
        """Quick-Save: speichert in den bekannten Pfad, sonst „Speichern unter…"."""
        if self._save_path is None:
            self._save_as()
            return
        if not self._canvas.has_image:
            self.statusBar().showMessage("Kein Bild zum Speichern")
            return
        self._canvas.save_image(self._save_path)

    def _save_as(self) -> None:
        """Speichern unter…: öffnet immer den Datei-Dialog."""
        if not self._canvas.has_image:
            self.statusBar().showMessage("Kein Bild zum Speichern")
            return
        save_dir = self._settings.value("save_dir", "")
        if self._save_path:
            suggest = self._save_path
        elif save_dir:
            suggest = str(Path(save_dir) / "bild_bearbeitet")
        else:
            suggest = "bild_bearbeitet"
        preferred = self._settings.value("preferred_format", "PNG")
        all_filters = {
            "PNG":  "PNG (*.png)",
            "JPEG": "JPEG (*.jpg)",
            "WebP": "WebP (*.webp)",
            "TIFF": "TIFF (*.tif)",
        }
        ordered = [preferred] + [f for f in all_filters if f != preferred]
        filter_str = ";;".join(all_filters[f] for f in ordered)
        path, _ = QFileDialog.getSaveFileName(
            self, "Bild speichern unter…", suggest, filter_str
        )
        if path:
            # Pfad nur als Quick-Save-Ziel merken, wenn das Speichern
            # tatsächlich geklappt hat.
            if self._canvas.save_image(path):
                self._save_path = path

    # ── Recent-Files ────────────────────────────────────────────

    def _recent_paths(self) -> list[str]:
        raw = self._settings.value(self.SETTINGS_RECENT_KEY, [])
        if isinstance(raw, str):       # einzelner Eintrag → in Liste packen
            return [raw]
        return list(raw) if raw else []

    def _add_recent(self, path: str) -> None:
        canonical = str(Path(path).resolve())
        items = [p for p in self._recent_paths() if p != canonical]
        items.insert(0, canonical)
        items = items[:self.RECENT_MAX]
        self._settings.setValue(self.SETTINGS_RECENT_KEY, items)
        self._rebuild_recent_menu()

    def _rebuild_recent_menu(self) -> None:
        if self._recent_menu is None:
            return
        self._recent_menu.clear()
        items = self._recent_paths()
        if not items:
            empty = QAction("(keine)", self)
            empty.setEnabled(False)
            self._recent_menu.addAction(empty)
            return
        for p in items:
            act = QAction(Path(p).name, self)
            act.setToolTip(p)
            act.triggered.connect(lambda _=False, pp=p: self._open_recent(pp))
            self._recent_menu.addAction(act)

    def _open_recent(self, path: str) -> None:
        if not Path(path).exists():
            self.statusBar().showMessage(
                f"Datei nicht mehr vorhanden: {Path(path).name}")
            items = [p for p in self._recent_paths() if p != path]
            self._settings.setValue(self.SETTINGS_RECENT_KEY, items)
            self._rebuild_recent_menu()
            return
        self._load_image_async(path)

    def _on_image_loaded(self, path: str) -> None:
        """Wird nach jedem load_image vom Canvas aufgerufen."""
        self._save_path = None
        self._add_recent(path)

    def _pick_color(self) -> None:
        c = QColorDialog.getColor(self._bg_color, self, "Hintergrundfarbe wählen")
        if c.isValid():
            self._bg_color = c
            self._update_color_btn()

    def _update_color_btn(self) -> None:
        self._color_btn.setStyleSheet(
            f"background: {self._bg_color.name()}; border-radius: 5px; border: 2px solid #555;"
        )

    def _run_ai(self) -> None:
        if not self._canvas.has_image:
            self.statusBar().showMessage("Kein Bild geladen")
            return
        if self._ai_thread is not None and self._ai_thread.isRunning():
            self.statusBar().showMessage("KI läuft bereits…")
            return
        self.statusBar().showMessage("🤖 KI verarbeitet Bild… (kann einige Sekunden dauern)")
        self._btn_ai.setEnabled(False)

        # Canvas-Version merken: falls der Nutzer inzwischen ein anderes
        # Bild lädt, wird das verspätete KI-Ergebnis in _on_ai_done verworfen.
        self._ai_input_version = self._canvas.version

        worker = AIWorker(self._canvas.image.copy())
        worker.finished.connect(self._on_ai_done)
        worker.error.connect(self._on_ai_error)
        self._ai_thread = self._launch_worker(
            worker,
            quit_on=(worker.finished, worker.error),
            on_finished=self._on_ai_thread_finished,
        )
        self._ai_worker = worker

    def _on_ai_thread_finished(self) -> None:
        self._btn_ai.setEnabled(True)
        self._ai_thread = None
        self._ai_worker = None
        self._ai_input_version = -1

    def _on_ai_done(self, img: Image.Image) -> None:
        # Versionsprüfung: Falls der Nutzer das Bild zwischenzeitlich gewechselt
        # hat, ist _version erhöht worden und das KI-Ergebnis wird verworfen.
        if self._canvas.version != self._ai_input_version:
            self.statusBar().showMessage(
                "KI-Ergebnis verworfen – Bild wurde inzwischen geändert")
            return
        self._canvas.apply_ai_result(img)

    def _on_ai_error(self, msg: str) -> None:
        self.statusBar().showMessage(f"KI-Fehler: {msg}")
        QMessageBox.warning(self, "KI-Fehler",
                            f"Fehler bei der automatischen Hintergrundentfernung:\n\n{msg}")

    def _build_history_popup(self) -> None:
        popup = QDialog(self, Qt.WindowType.Tool)
        popup.setWindowTitle("Änderungshistorie")
        popup.setMinimumWidth(270)
        popup.setStyleSheet("QDialog { background: #1a1a1a; }")

        lay = QVBoxLayout(popup)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        lbl = QLabel("Doppelklick auf Eintrag → zu diesem Schritt zurück")
        lbl.setStyleSheet("color: #666; font-size: 10px; background: transparent;")
        lay.addWidget(lbl)

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
        self._history_list.setMinimumHeight(200)
        self._history_list.setToolTip(
            "Verlauf aller Bearbeitungsschritte.\n"
            "Doppelklick auf einen Eintrag springt zu diesem Schritt zurück.")
        self._history_list.itemDoubleClicked.connect(self._undo_to_item)
        lay.addWidget(self._history_list)

        self._hist_popup = popup

    def _toggle_history_popup(self) -> None:
        if self._hist_popup is None:
            self._build_history_popup()
        if self._hist_popup.isVisible():
            self._hist_popup.hide()
        else:
            gp = self._btn_history.mapToGlobal(self._btn_history.rect().topRight())
            self._hist_popup.move(gp.x() + 4, gp.y())
            self._hist_popup.show()
            self._hist_popup.raise_()

    def _on_history_changed(self, history: list) -> None:
        if not hasattr(self, '_history_list'):
            return
        self._history_list.clear()
        for desc in history:
            self._history_list.addItem(desc)

    def _on_crop_mode_changed(self, active: bool) -> None:
        self._crop_bar.setVisible(active)

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._settings, self)
        dlg.exec()

    def _undo_to_item(self, item) -> None:
        row = self._history_list.row(item)
        self._canvas.undo_to(row + 1)


# ─────────────────────────────────────────────────────────────
# Start
# ─────────────────────────────────────────────────────────────

def _resolve_log_dir() -> Path:
    """Ermittelt das Log-Verzeichnis und legt es bei Bedarf an.

    Das Zielverzeichnis wird angelegt – andernfalls bricht der
    ``FileHandler`` den Start mit ``FileNotFoundError`` ab.
    """
    loc = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation)
    log_dir = Path(loc) if loc else (Path.home() / ".bgremover")
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        log_dir = Path.home()
    return log_dir


def current_log_file() -> Path:
    """Pfad der aktiven Log-Datei.

    Liefert den vom ``_setup_logging`` gesetzten Pfad; falls noch kein
    Setup lief (z. B. in Tests), wird er erneut aufgelöst.
    """
    if _log_file_path is not None:
        return _log_file_path
    return _resolve_log_dir() / LOG_FILENAME


def _setup_logging() -> None:
    """Konfiguriert stderr- + Datei-Logging.

    Muss NACH dem Erzeugen der QApplication und dem Setzen von
    Application-/Organization-Name laufen, sonst liefert
    ``QStandardPaths`` keinen app-spezifischen Pfad.
    """
    global _log_file_path
    log_dir = _resolve_log_dir()
    _log_file_path = log_dir / LOG_FILENAME
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(_log_file_path, encoding="utf-8"),
        ],
    )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("BgRemover")
    app.setOrganizationName("BgRemover")
    # Erst jetzt – QApplication + App-Name stehen – ist der Log-Pfad korrekt.
    _setup_logging()
    app.setStyle("Fusion")

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
