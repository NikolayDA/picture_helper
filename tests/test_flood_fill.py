"""Tests für den Scanline-Flood-Fill.

Der frühere Algorithmus pushte jeden Pixel einzeln auf einen Python-Stack
(bei 2,25 MP einfarbig ≈ 3,3 s gemessen). Die Scanline-Variante füllt ganze
horizontale Spannen und sucht Nachbarzeilen vektorisiert ab.

Kern dieser Tests ist ein Property-Vergleich gegen eine bewusst simple
4-Nachbar-Referenz: Für viele Zufallsbilder muss die optimierte Funktion
bit-identische Masken liefern.
"""
from __future__ import annotations

import numpy as np

from bgremover.image_utils import flood_fill


def _reference_flood_fill(
    arr: np.ndarray, x: int, y: int, tolerance: int,
) -> np.ndarray:
    """Naive, offensichtlich korrekte 4-Nachbar-Referenz (Pixel-Stack)."""
    h, w = arr.shape[:2]
    mask = np.zeros((h, w), dtype=bool)
    if not (0 <= x < w and 0 <= y < h):
        return mask
    rgb = arr[:, :, :3].astype(np.int16)
    target = rgb[y, x]
    diff = np.abs(rgb - target).max(axis=2)
    similar = diff <= tolerance
    if not similar[y, x]:
        return mask
    stack = [(x, y)]
    mask[y, x] = True
    while stack:
        cx, cy = stack.pop()
        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
            if (0 <= nx < w and 0 <= ny < h
                    and similar[ny, nx] and not mask[ny, nx]):
                mask[ny, nx] = True
                stack.append((nx, ny))
    return mask


def test_matches_reference_on_random_images() -> None:
    rng = np.random.default_rng(20260531)
    for _ in range(40):
        h = int(rng.integers(3, 40))
        w = int(rng.integers(3, 40))
        # Wenige Graustufen → viele zusammenhängende Flächen mit Löchern.
        arr = np.zeros((h, w, 4), dtype=np.uint8)
        arr[:, :, 3] = 255
        levels = rng.integers(0, 4, size=(h, w)).astype(np.uint8) * 80
        for c in range(3):
            arr[:, :, c] = levels
        x = int(rng.integers(0, w))
        y = int(rng.integers(0, h))
        tol = int(rng.integers(0, 60))
        got = flood_fill(arr, x, y, tol)
        exp = _reference_flood_fill(arr, x, y, tol)
        assert np.array_equal(got, exp), (
            f"Abweichung bei {w}x{h} seed=({x},{y}) tol={tol}")


def test_uniform_area_selects_everything() -> None:
    arr = np.zeros((50, 60, 4), dtype=np.uint8)
    arr[:, :, 3] = 255
    mask = flood_fill(arr, 25, 30, tolerance=10)
    assert mask.all()


def test_u_shape_connectivity() -> None:
    # U-Form aus gleicher Farbe vor andersfarbigem Hintergrund: der
    # Mittelbalken oben fehlt, beide Schenkel sind unten verbunden.
    arr = np.full((7, 7, 4), 255, dtype=np.uint8)   # weiß
    arr[:, :, 0:3] = 255
    u = np.zeros((7, 7), dtype=bool)
    u[1:6, 1] = True      # linker Schenkel
    u[1:6, 5] = True      # rechter Schenkel
    u[5, 1:6] = True      # Boden
    for c in range(3):
        arr[:, :, c] = np.where(u, 0, 255)
    mask = flood_fill(arr, 1, 1, tolerance=10)   # Saat im linken Schenkel
    assert mask[5, 5]                              # rechter Schenkel erreichbar
    assert (mask == u).all()                       # genau die U-Form


def test_diagonal_is_not_connected() -> None:
    # 4-Konnektivität: rein diagonale Nachbarn zählen nicht.
    arr = np.full((3, 3, 4), 255, dtype=np.uint8)
    for c in range(3):
        arr[:, :, c] = 255
    arr[0, 0, 0:3] = 0
    arr[1, 1, 0:3] = 0
    mask = flood_fill(arr, 0, 0, tolerance=10)
    assert mask[0, 0]
    assert not mask[1, 1]   # diagonal → nicht verbunden


def test_should_cancel_returns_partial() -> None:
    # Mehr Zeilen als ein Abbruch-Intervall (256), damit der Check sicher
    # vor dem Ende greift; eine Iteration füllt grob eine Zeile.
    h, w = 1024, 64
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 3] = 255   # große einfarbige Fläche
    mask = flood_fill(arr, w // 2, h // 2, tolerance=10, should_cancel=lambda: True)
    # Abbruch muss VOR dem Füllen aller Zeilen greifen.
    assert 0 < mask.sum() < h * w


def test_should_cancel_false_completes_normally() -> None:
    arr = np.zeros((30, 30, 4), dtype=np.uint8)
    arr[:, :, 3] = 255
    mask = flood_fill(arr, 0, 0, tolerance=10, should_cancel=lambda: False)
    assert mask.all()
