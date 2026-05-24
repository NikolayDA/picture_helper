"""Auswahl-/Maskenzustand für ``ImageCanvas``."""
from __future__ import annotations

from typing import Literal

import numpy as np
from PIL import Image, ImageFilter

from bgremover.image_ops import remove_selection, replace_selection


class CanvasSelection:
    """Verwaltet Auswahlmasken ohne Zugriff auf Canvas-Interna."""

    def __init__(self, width: int, height: int) -> None:
        self._mask = np.zeros((height, width), dtype=bool)

    @property
    def mask(self) -> np.ndarray:
        return self._mask

    @property
    def has_selection(self) -> bool:
        return bool(self._mask.any())

    def reset(self, width: int, height: int) -> None:
        self._mask = np.zeros((height, width), dtype=bool)

    def clear(self) -> None:
        self._mask[:] = False

    def invert(self) -> int:
        self._mask = ~self._mask
        return int(self._mask.sum())

    def morphology(self, radius: int, kind: Literal["expand", "shrink"]) -> int:
        if radius <= 0:
            return int(self._mask.sum())
        mask_img = Image.fromarray((self._mask * 255).astype(np.uint8), mode="L")
        size = radius * 2 + 1
        filt: ImageFilter.RankFilter
        if kind == "expand":
            filt = ImageFilter.MaxFilter(size)
        else:
            filt = ImageFilter.MinFilter(size)
        result = mask_img.filter(filt)
        self._mask = np.array(result) > 127
        return int(self._mask.sum())

    def set_wand_result(
        self,
        new_mask: np.ndarray,
        mode: Literal["set", "add", "subtract"],
    ) -> int:
        return self._set_result(new_mask, mode)

    def set_polygon_result(
        self,
        new_mask: np.ndarray,
        mode: Literal["set", "add", "subtract"],
    ) -> int:
        return self._set_result(new_mask, mode)

    def paint_brush(self, cx: int, cy: int, radius: int, additive: bool) -> None:
        h, w = self._mask.shape
        y0, y1 = max(0, cy - radius), min(h, cy + radius + 1)
        x0, x1 = max(0, cx - radius), min(w, cx + radius + 1)
        if y0 >= y1 or x0 >= x1:
            return
        yy, xx = np.ogrid[y0:y1, x0:x1]
        circle = (yy - cy) ** 2 + (xx - cx) ** 2 <= radius ** 2
        region = self._mask[y0:y1, x0:x1]
        region[circle] = additive

    def remove_background(self, arr: np.ndarray) -> Image.Image:
        return remove_selection(arr, self._mask)

    def replace_background(
        self,
        arr: np.ndarray,
        color: tuple[int, int, int],
    ) -> Image.Image:
        return replace_selection(arr, self._mask, color)

    def _set_result(
        self,
        new_mask: np.ndarray,
        mode: Literal["set", "add", "subtract"],
    ) -> int:
        incoming = np.asarray(new_mask, dtype=bool)
        if mode == "add":
            self._mask |= incoming
        elif mode == "subtract":
            self._mask &= ~incoming
        else:
            self._mask = incoming.copy()
        return int(self._mask.sum())
