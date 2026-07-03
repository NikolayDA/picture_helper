"""Cursor- und Toolbar-Icon-Generatoren.

Asset-Auflösung läuft über ``importlib.resources`` aus den Paket-Daten
``bgremover/icons/``. Kontrakt: PNG vorhanden ⇒ PNG-Icon, sonst das
gezeichnete Vektor-Fallback.
"""
from __future__ import annotations

import importlib.resources

from PIL import Image
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QIcon,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)

from bgremover.constants import logger


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


def _draw_move_icon(p: QPainter, s: int) -> None:
    """Verschieben/Zoom (#456): Pfeilkreuz wie im Prototyp."""
    pen = QPen(QColor(200, 200, 200), max(2, int(s * 0.075)),
               Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
               Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    c = s * 0.5
    lo, hi = s * 0.16, s * 0.84
    head = s * 0.14
    p.drawLine(QPointF(c, lo), QPointF(c, hi))
    p.drawLine(QPointF(lo, c), QPointF(hi, c))
    for tip, d1, d2 in (
        (QPointF(c, lo), QPointF(c - head, lo + head), QPointF(c + head, lo + head)),
        (QPointF(c, hi), QPointF(c - head, hi - head), QPointF(c + head, hi - head)),
        (QPointF(lo, c), QPointF(lo + head, c - head), QPointF(lo + head, c + head)),
        (QPointF(hi, c), QPointF(hi - head, c - head), QPointF(hi - head, c + head)),
    ):
        p.drawLine(tip, d1)
        p.drawLine(tip, d2)


def _draw_height_lighten_icon(p: QPainter, s: int) -> None:
    """Aufhellen (höher, #457): Kreis nur als Kontur – wie im Prototyp."""
    p.setPen(QPen(QColor(220, 220, 220), max(2, int(s * 0.08))))
    p.setBrush(Qt.BrushStyle.NoBrush)
    r = s * 0.28
    p.drawEllipse(QPointF(s * 0.5, s * 0.5), r, r)


def _draw_height_darken_icon(p: QPainter, s: int) -> None:
    """Abdunkeln (tiefer, #457): gefüllter Kreis – wie im Prototyp."""
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(220, 220, 220)))
    r = s * 0.30
    p.drawEllipse(QPointF(s * 0.5, s * 0.5), r, r)


def _draw_lock_icon(p: QPainter, s: int) -> None:
    """Fixier-Schloss der Zoom-Kontrolle (#464)."""
    c = QColor(200, 200, 200)
    pen = QPen(c, max(2, int(s * 0.08)),
               Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
               Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(s * 0.24, s * 0.46, s * 0.52, s * 0.38),
                      s * 0.08, s * 0.08)
    p.drawArc(QRectF(s * 0.34, s * 0.14, s * 0.32, s * 0.42), 0, 180 * 16)


def _draw_theme_icon(p: QPainter, s: int) -> None:
    """Theme-Umschalter (#458): halb gefüllter Kreis wie im Prototyp."""
    c = QColor(200, 200, 200)
    p.setPen(QPen(c, max(2, int(s * 0.08))))
    p.setBrush(Qt.BrushStyle.NoBrush)
    r = s * 0.34
    p.drawEllipse(QPointF(s * 0.5, s * 0.5), r, r)
    path = QPainterPath()
    path.moveTo(s * 0.5, s * 0.5 - r)
    path.arcTo(QRectF(s * 0.5 - r, s * 0.5 - r, r * 2, r * 2), 90, -180)
    path.closeSubpath()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(c))
    p.drawPath(path)


def make_tool_icon(name: str, size: int = 28) -> QIcon:
    """Lädt PNG aus den Paket-Daten (``bgremover/icons/``) via Pillow,
    fällt auf gezeichnetes Vektor-Icon zurück."""
    try:
        res = importlib.resources.files("bgremover") / "icons" / f"{name}.png"
        with importlib.resources.as_file(res) as png_path:
            if png_path.is_file():
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
                     name, exc_info=True)
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
        "move":           _draw_move_icon,
        "height_lighten": _draw_height_lighten_icon,
        "height_darken":  _draw_height_darken_icon,
        "theme":          _draw_theme_icon,
        "lock":           _draw_lock_icon,
    }
    if name in _ICON_DRAW:
        _ICON_DRAW[name](p, s)
    p.end()
    return QIcon(pm)
