"""Bild-/Array-Konvertierung, Flood-Fill, Overlay, Schachbrett-Brush."""
from __future__ import annotations

from collections.abc import Callable

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
    """RGBA-Sicht als unabhaengiges, schreibbares Array.

    Defensive Variante mit Heap-Kopie – fuer Aufrufer, die das Ergebnis
    mutieren (z. B. ein bearbeitetes Bild zurueckschreiben).
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    return np.asarray(img).copy()


def pil_to_numpy_readonly(img: Image.Image) -> np.ndarray:
    """RGBA-Sicht ohne defensive Kopie.

    Spart bei grossen Bildern eine Heap-Allokation. Das Array ist nicht
    schreibbar (numpy meldet ``ValueError`` bei jedem Schreibversuch);
    Aufrufer, die mutieren wollen, muessen ``pil_to_numpy`` oder ein
    explizites ``.copy()`` nehmen.
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    return np.asarray(img)


def numpy_to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def flood_fill(
    arr: np.ndarray,
    x: int,
    y: int,
    tolerance: int,
    should_cancel: Callable[[], bool] | None = None,
) -> np.ndarray:
    """Flood-Fill: gibt Boolean-Maske der zusammenhängenden Fläche zurück.

    Zuerst wird die Ähnlichkeit vektorisiert über das ganze Bild bestimmt;
    danach wächst die zusammenhängende Region per **Scanline-Verfahren**:
    pro Iteration wird eine ganze horizontale Spanne auf einmal gefüllt und
    die beiden Nachbarzeilen werden vektorisiert (NumPy) nach neuen
    Saatpunkten abgesucht. Damit läuft die innere Arbeit in NumPy statt in
    einer Python-Schleife pro Pixel – bei großen, einfarbigen Flächen ist
    das um Größenordnungen schneller (eine Spanne pro Zeile statt Millionen
    einzelner Pixel-Pushes).

    ``should_cancel`` wird gelegentlich abgefragt; liefert es ``True``, kehrt
    die Funktion früh mit der bis dahin gefüllten (Teil-)Maske zurück. So
    kann ein abgebrochener Worker zügig aussteigen, statt eine sehr große
    Fläche zu Ende zu rechnen.
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

    stack: list[tuple[int, int]] = [(x, y)]
    steps = 0
    # Eine Iteration füllt grob eine Bildzeile; alle 256 Zeilen den Abbruch
    # prüfen hält den Callback billig und bleibt selbst bei 40 MP (~6300
    # Zeilen → ~25 Prüfungen) reaktionsschnell.
    _CANCEL_INTERVAL = 256
    while stack:
        cx, cy = stack.pop()
        if mask[cy, cx] or not similar[cy, cx]:
            continue
        row = similar[cy]
        # Maximale zusammenhängende similar-Spanne, die cx enthält.
        left_falses = np.flatnonzero(~row[:cx])
        xl = int(left_falses[-1]) + 1 if left_falses.size else 0
        right_falses = np.flatnonzero(~row[cx + 1:])
        xr = cx + int(right_falses[0]) if right_falses.size else w - 1
        mask[cy, xl:xr + 1] = True
        # Nachbarzeilen nach neuen, noch nicht gefüllten Spannen absuchen und
        # je zusammenhängendem Lauf genau einen Saatpunkt pushen.
        for ny in (cy - 1, cy + 1):
            if 0 <= ny < h:
                seg = similar[ny, xl:xr + 1] & ~mask[ny, xl:xr + 1]
                idx = np.flatnonzero(seg)
                if idx.size:
                    run_starts = idx[np.concatenate(([True], np.diff(idx) > 1))]
                    for s in run_starts:
                        stack.append((int(s) + xl, ny))
        steps += 1
        if (should_cancel is not None
                and steps % _CANCEL_INTERVAL == 0
                and should_cancel()):
            return mask
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
