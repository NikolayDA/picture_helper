"""Bild-/Array-Konvertierung, Flood-Fill, Overlay, Schachbrett-Brush.

Verbatim aus ``BgRemover.py`` verschoben (Runde 5, Phase B – Schritt 3).
Keine Verhaltensänderung.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPixmap

from bgremover.constants import _OVERLAY_COLOR


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
    """Flood-Fill: gibt Boolean-Maske der zusammenhängenden Fläche zurück.

    Die Ähnlichkeitsprüfung ist vektorisiert (wenige NumPy-Operationen
    über das ganze Bild); danach wächst nur noch die zusammenhängende
    Region vom Saatpunkt aus. Das ist deutlich schneller und sparsamer
    als ein Python-Loop, der pro Pixel einen NumPy-Aufruf macht.
    """
    h, w = arr.shape[:2]
    mask = np.zeros((h, w), dtype=bool)
    if not (0 <= x < w and 0 <= y < h):
        return mask
    rgb = arr[:, :, :3]
    target = rgb[y, x].astype(np.int16)
    diff = np.abs(rgb[:, :, 0].astype(np.int16) - target[0])
    np.maximum(diff, np.abs(rgb[:, :, 1].astype(np.int16) - target[1]), out=diff)
    np.maximum(diff, np.abs(rgb[:, :, 2].astype(np.int16) - target[2]), out=diff)
    similar = diff <= tolerance
    if not similar[y, x]:
        return mask
    stack = [(x, y)]
    mask[y, x] = True
    while stack:
        cx, cy = stack.pop()
        for nx, ny in ((cx - 1, cy), (cx + 1, cy),
                       (cx, cy - 1), (cx, cy + 1)):
            if (0 <= nx < w and 0 <= ny < h
                    and similar[ny, nx] and not mask[ny, nx]):
                mask[ny, nx] = True
                stack.append((nx, ny))
    return mask


def mask_to_overlay(mask: np.ndarray, w: int, h: int) -> QPixmap:
    """Konvertiert Boolean-Maske → halbtransparente rote Overlay-QPixmap."""
    overlay = np.zeros((h, w, 4), dtype=np.uint8)
    overlay[mask] = list(_OVERLAY_COLOR)
    raw = overlay.tobytes()
    qi = QImage(raw, w, h, w * 4, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qi.copy())


def make_checker_brush(size: int = 14) -> QBrush:
    """Schachbrettmuster für transparente Bereiche."""
    px = QPixmap(size * 2, size * 2)
    px.fill(QColor(170, 170, 170))
    p = QPainter(px)
    p.fillRect(0, 0, size, size, QColor(210, 210, 210))
    p.fillRect(size, size, size, size, QColor(210, 210, 210))
    p.end()
    return QBrush(px)
