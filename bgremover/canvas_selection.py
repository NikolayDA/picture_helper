"""Auswahl-/Maskenzustand für ``ImageCanvas``."""
from __future__ import annotations

from typing import Literal

import numpy as np
import numpy.typing as npt
from PIL import Image, ImageFilter

from bgremover.image_ops import remove_selection, replace_selection


class CanvasSelection:
    """Verwaltet Auswahlmasken ohne Zugriff auf Canvas-Interna."""

    def __init__(self, width: int, height: int) -> None:
        self._mask: npt.NDArray[np.bool_] = np.zeros((height, width), dtype=bool)
        self._selected_count = 0

    @property
    def mask(self) -> npt.NDArray[np.bool_]:
        """Gibt eine schreibgeschützte Sicht auf die Auswahlmaske zurück."""
        view: npt.NDArray[np.bool_] = self._mask.view()
        view.flags.writeable = False
        return view

    @property
    def selected_count(self) -> int:
        return self._selected_count

    @property
    def has_selection(self) -> bool:
        return self._selected_count > 0

    def reset(self, width: int, height: int) -> None:
        self._mask = np.zeros((height, width), dtype=bool)
        self._selected_count = 0

    def set_mask(self, mask: np.ndarray) -> int:
        """Ersetzt die Maske und synchronisiert den Auswahlpixel-Zähler."""
        self._mask = np.asarray(mask, dtype=bool).copy()
        self._selected_count = int(np.count_nonzero(self._mask))
        return self._selected_count

    def clear(self) -> None:
        self._mask.fill(False)
        self._selected_count = 0

    def invert(self) -> int:
        self._mask = ~self._mask
        self._selected_count = self._mask.size - self._selected_count
        return self._selected_count

    def morphology(self, radius: int, kind: Literal["expand", "shrink"]) -> int:
        if radius <= 0:
            return self._selected_count
        mask_img = Image.fromarray((self._mask * 255).astype(np.uint8), mode="L")
        size = radius * 2 + 1
        filt: ImageFilter.RankFilter = (
            ImageFilter.MaxFilter(size) if kind == "expand" else ImageFilter.MinFilter(size)
        )
        result = mask_img.filter(filt)
        return self.set_mask(np.array(result) > 127)

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

    def paint_brush(
        self, cx: int, cy: int, radius: int, additive: bool,
    ) -> tuple[int, int, int, int] | None:
        """Malt einen Kreis in die Maske; gibt das geänderte Rechteck zurück.

        Rückgabe ``(x0, y0, x1, y1)`` ist die Bounding-Box des Pinsels –
        der Canvas aktualisiert damit nur diesen Ausschnitt des Overlays.
        ``None``, wenn der Pinsel komplett außerhalb des Bildes liegt.
        """
        h, w = self._mask.shape
        y0, y1 = max(0, cy - radius), min(h, cy + radius + 1)
        x0, x1 = max(0, cx - radius), min(w, cx + radius + 1)
        if y0 >= y1 or x0 >= x1:
            return None
        yy, xx = np.ogrid[y0:y1, x0:x1]
        circle = (yy - cy) ** 2 + (xx - cx) ** 2 <= radius ** 2
        region = self._mask[y0:y1, x0:x1]
        changed_pixels = circle & (~region if additive else region)
        changed = int(np.count_nonzero(changed_pixels))
        region[circle] = additive
        self._selected_count += changed if additive else -changed
        return (x0, y0, x1, y1)

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
            return self.set_mask(incoming)
        self._selected_count = int(np.count_nonzero(self._mask))
        return self._selected_count
