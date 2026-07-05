"""Cursor- und Toolbar-Icon-Generatoren.

Asset-Auflösung läuft über ``importlib.resources`` aus den Paket-Daten
``bgremover/icons/``. Kontrakt: PNG vorhanden ⇒ PNG-Icon, sonst das
gezeichnete Vektor-Fallback. Farb-/Rail-gesteuerte Icons nutzen bewusst immer
den Vektorpfad, damit stale Paketdaten-PNGs die Theme-Farbe nicht überdecken.
"""
from __future__ import annotations

import importlib.resources
from collections.abc import Callable

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

# Platzhalterfarbe, wenn ``make_tool_icon`` ohne explizite Palette-Farbe
# gerufen wird: Default für die mehrfarbigen Nicht-Rail-Icons (ignorieren
# den Farbparameter ohnehin) und Fallback, falls ein Rail-Icon ausnahmsweise
# ohne Palette angefordert wird. Die eigentliche Zustands-/Theme-Einfärbung
# der Rail läuft über ``make_stateful_tool_icon``/``make_tool_icon(color=...)``
# (#486), gespeist aus ``Palette.text3``/``Palette.accent_text``.
_RAIL_ICON_COLOR = QColor(200, 200, 200)
_VECTOR_ONLY_ICON_NAMES = frozenset({
    "move",
    "wand",
    "brush",
    "eraser",
    "lasso",
    "height_lighten",
    "height_darken",
    "undo",
    "redo",
    "theme",
})


def _draw_wand_icon(p: QPainter, s: int, color: QColor) -> None:
    """Zauberstab (§8): Diagonale + ein Sparkle, 1:1 zum Prototyp-SVG (viewBox 20)."""
    k = s / 20.0
    p.setPen(QPen(color, max(1.0, 1.6 * k), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(4 * k, 16 * k), QPointF(12 * k, 8 * k))
    sparkle = QPainterPath()
    pts = [(14, 3), (14.7, 5), (16.7, 5.7), (14.7, 6.4),
           (14, 8.4), (13.3, 6.4), (11.3, 5.7), (13.3, 5)]
    sparkle.moveTo(pts[0][0] * k, pts[0][1] * k)
    for x, y in pts[1:]:
        sparkle.lineTo(x * k, y * k)
    sparkle.closeSubpath()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(color))
    p.drawPath(sparkle)


def _draw_brush_icon(p: QPainter, s: int, color: QColor) -> None:
    """Pinsel (§8): Diagonale + rotierte Borsten-Spitze, 1:1 zum Prototyp-SVG."""
    k = s / 20.0
    p.setPen(QPen(color, max(1.0, 1.6 * k), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(16 * k, 5 * k), QPointF(9 * k, 12 * k))
    p.save()
    p.translate(7 * k, 14 * k)
    p.rotate(45)
    p.translate(-7 * k, -14 * k)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(color))
    p.drawRoundedRect(QRectF(3.5 * k, 11 * k, 7 * k, 6 * k), 2.2 * k, 2.2 * k)
    p.restore()


def _draw_eraser_icon(p: QPainter, s: int, color: QColor) -> None:
    """Radiergummi (§8): rotierte Kontur + Grundlinie, 1:1 zum Prototyp-SVG."""
    k = s / 20.0
    pen = QPen(color, max(1.0, 1.6 * k), Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.save()
    p.translate(9 * k, 11 * k)
    p.rotate(-32)
    p.translate(-9 * k, -11 * k)
    p.drawRoundedRect(QRectF(3 * k, 8 * k, 12 * k, 7 * k), 1.5 * k, 1.5 * k)
    p.restore()
    p.drawLine(QPointF(8 * k, 16.5 * k), QPointF(17 * k, 16.5 * k))


def _draw_lasso_icon(p: QPainter, s: int, color: QColor) -> None:
    """Polygon-Lasso (§8): gestrichelte 5-Punkt-Kontur ohne Eckpunkt-Marker,
    1:1 zum Prototyp-SVG (viewBox 20)."""
    k = s / 20.0
    width = max(1.0, 1.5 * k)
    pen = QPen(color, width, Qt.PenStyle.CustomDashLine,
               Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.RoundJoin)
    pen.setDashPattern([2.4 / 1.5, 2.2 / 1.5])
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    pts = [(10, 3), (16, 8), (14, 16), (6, 16), (4, 8)]
    p.drawPolygon(QPolygonF([QPointF(x * k, y * k) for x, y in pts]))


def _draw_ai_icon(p: QPainter, s: int, _color: QColor) -> None:
    bolt = QPolygonF([
        QPointF(s*0.55, s*0.10), QPointF(s*0.28, s*0.52),
        QPointF(s*0.48, s*0.52), QPointF(s*0.42, s*0.90),
        QPointF(s*0.72, s*0.46), QPointF(s*0.52, s*0.46),
    ])
    p.setPen(QPen(QColor(80, 190, 255), 1.5))
    p.setBrush(QBrush(QColor(80, 190, 255, 200)))
    p.drawPolygon(bolt)


def _draw_open_icon(p: QPainter, s: int, _color: QColor) -> None:
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


def _draw_save_icon(p: QPainter, s: int, _color: QColor) -> None:
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


def _draw_undo_icon(p: QPainter, s: int, color: QColor) -> None:
    """Rückgängig (§5.9 Rail-Fuß): rechtwinkliger Haken-Pfad, 1:1 zum
    Prototyp-SVG (`M7 8 H13 a4 4 0 0 1 0 8 H9` + Pfeilspitze)."""
    k = s / 20.0
    pen = QPen(color, max(1.0, 1.6 * k), Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(7 * k, 8 * k)
    path.lineTo(13 * k, 8 * k)
    path.arcTo(QRectF(9 * k, 8 * k, 8 * k, 8 * k), 90, -180)
    path.lineTo(9 * k, 16 * k)
    path.moveTo(9 * k, 5 * k)
    path.lineTo(6 * k, 8 * k)
    path.lineTo(9 * k, 11 * k)
    p.drawPath(path)


def _draw_redo_icon(p: QPainter, s: int, color: QColor) -> None:
    """Wiederholen (§5.9 Rail-Fuß): horizontal gespiegelter Rückgängig-Pfad,
    1:1 zum Prototyp-SVG (`M13 8 H7 a4 4 0 0 0 0 8 H11` + Pfeilspitze)."""
    k = s / 20.0
    pen = QPen(color, max(1.0, 1.6 * k), Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(13 * k, 8 * k)
    path.lineTo(7 * k, 8 * k)
    path.arcTo(QRectF(3 * k, 8 * k, 8 * k, 8 * k), 90, 180)
    path.lineTo(11 * k, 16 * k)
    path.moveTo(11 * k, 5 * k)
    path.lineTo(14 * k, 8 * k)
    path.lineTo(11 * k, 11 * k)
    p.drawPath(path)


def _draw_restore_icon(p: QPainter, s: int, _color: QColor) -> None:
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


def _draw_history_icon(p: QPainter, s: int, _color: QColor) -> None:
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


def _draw_move_icon(p: QPainter, s: int, color: QColor) -> None:
    """Verschieben/Zoom (#456): Pfeilkreuz, 1:1 zum Prototyp-SVG (viewBox 20)."""
    k = s / 20.0
    pen = QPen(color, max(1.0, 1.5 * k),
               Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
               Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(10 * k, 3.5 * k), QPointF(10 * k, 16.5 * k))
    p.drawLine(QPointF(3.5 * k, 10 * k), QPointF(16.5 * k, 10 * k))
    for a, b, c in (
        ((7.5, 6), (10, 3.5), (12.5, 6)),
        ((7.5, 14), (10, 16.5), (12.5, 14)),
        ((6, 7.5), (3.5, 10), (6, 12.5)),
        ((14, 7.5), (16.5, 10), (14, 12.5)),
    ):
        p.drawPolyline(QPolygonF([QPointF(a[0] * k, a[1] * k),
                                   QPointF(b[0] * k, b[1] * k),
                                   QPointF(c[0] * k, c[1] * k)]))


def _draw_height_lighten_icon(p: QPainter, s: int, color: QColor) -> None:
    """Aufhellen (höher, #457): Kreis-Kontur, 1:1 zum Prototyp-SVG (r=5.5 von 20)."""
    k = s / 20.0
    p.setPen(QPen(color, max(1.0, 1.6 * k)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(10 * k, 10 * k), 5.5 * k, 5.5 * k)


def _draw_height_darken_icon(p: QPainter, s: int, color: QColor) -> None:
    """Abdunkeln (tiefer, #457): gefüllter Kreis, 1:1 zum Prototyp-SVG (r=5.5 von 20)."""
    k = s / 20.0
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(color))
    p.drawEllipse(QPointF(10 * k, 10 * k), 5.5 * k, 5.5 * k)


def _draw_lock_icon(p: QPainter, s: int, _color: QColor) -> None:
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


def _draw_theme_icon(p: QPainter, s: int, color: QColor) -> None:
    """Theme-Umschalter (#458): halb gefüllter Kreis, 1:1 zum Prototyp-SVG
    (Kreis r=7 von 20 + Halbfläche `M10 3 a7 7 0 0 1 0 14 Z`)."""
    k = s / 20.0
    r = 7 * k
    p.setPen(QPen(color, max(1.0, 1.6 * k)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(10 * k, 10 * k), r, r)
    path = QPainterPath()
    path.moveTo(10 * k, 10 * k - r)
    path.arcTo(QRectF(10 * k - r, 10 * k - r, r * 2, r * 2), 90, -180)
    path.closeSubpath()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(color))
    p.drawPath(path)


# Zeichenfunktion je Icon-Name, Signatur ``(QPainter, Größe, Farbe)``. Die
# zehn Rail-Icons (sieben Werkzeuge + drei Rail-Fuß-Aktionen) verwenden die
# Farbe für ihren einzigen Strich/ihre Füllung; die übrigen, mehrfarbigen
# Icons (Inspector/Zoom-Pille, außerhalb der Rail) ignorieren sie bewusst –
# eigenes Farbschema je Icon, kein Verbraucher für Palette-Einfärbung (#486).
_ICON_DRAW: dict[str, Callable[[QPainter, int, QColor], None]] = {
    "wand":    _draw_wand_icon,
    "brush":   _draw_brush_icon,
    "eraser":  _draw_eraser_icon,
    "lasso":   _draw_lasso_icon,
    "ai":      _draw_ai_icon,
    "open":    _draw_open_icon,
    "save":    _draw_save_icon,
    "undo":    _draw_undo_icon,
    "redo":    _draw_redo_icon,
    "restore": _draw_restore_icon,
    "history": _draw_history_icon,
    "move":           _draw_move_icon,
    "height_lighten": _draw_height_lighten_icon,
    "height_darken":  _draw_height_darken_icon,
    "theme":          _draw_theme_icon,
    "lock":           _draw_lock_icon,
}


def _render_icon_pixmap(
    draw: Callable[[QPainter, int, QColor], None], size: int, color: QColor,
) -> QPixmap:
    """Rendert eine einzelne Icon-Pixmap über eine ``_draw_*_icon``-Funktion."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw(p, size, color)
    p.end()
    return pm


def make_tool_icon(name: str, size: int = 28, color: QColor | None = None) -> QIcon:
    """Lädt PNG aus den Paket-Daten (``bgremover/icons/``) via Pillow,
    fällt auf gezeichnetes Vektor-Icon zurück. ``color`` färbt den
    Vektor-Pfad ein; farb-/Rail-gesteuerte Icons ignorieren eventuell
    vorhandene PNGs bewusst, weil Rastergrafiken nicht sauber umgefärbt
    werden können. Ohne Angabe greift ein neutraler Platzhalterton (#486)."""
    draw = _ICON_DRAW.get(name)
    if draw is not None and (color is not None or name in _VECTOR_ONLY_ICON_NAMES):
        return QIcon(_render_icon_pixmap(draw, size, color or _RAIL_ICON_COLOR))

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
    if draw is None:
        return QIcon()
    return QIcon(_render_icon_pixmap(draw, size, color or _RAIL_ICON_COLOR))


def make_stateful_tool_icon(
    name: str, size: int, idle_color: QColor, active_color: QColor,
) -> QIcon:
    """Rail-Werkzeug-Icon mit getrennter Aus-/An-Pixmap (Prototyp:
    ``currentColor`` folgt ``.tool``/``.tool.on``, §6/§8). Qt zeigt bei
    ``QToolButton.setChecked()`` automatisch die passende Variante – kein
    manuelles Neusetzen des Icons beim Werkzeugwechsel nötig (#486). Nutzt
    immer den Vektor-Pfad (kein PNG-Fallback): eine zustandsabhängig
    eingefärbte Pixmap lässt sich aus einer Rastergrafik nicht ableiten.
    """
    draw = _ICON_DRAW.get(name)
    if draw is None:
        return make_tool_icon(name, size, idle_color)
    icon = QIcon()
    icon.addPixmap(_render_icon_pixmap(draw, size, idle_color),
                   QIcon.Mode.Normal, QIcon.State.Off)
    icon.addPixmap(_render_icon_pixmap(draw, size, active_color),
                   QIcon.Mode.Normal, QIcon.State.On)
    return icon
