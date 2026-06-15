"""Undo/Redo-Verlaufszustand für ImageCanvas."""
from __future__ import annotations

from collections import deque

from PIL import Image

from bgremover.constants import _HISTORY_MEMORY_LIMIT, _REDO_MAX_ENTRIES


class CanvasHistory:
    """Verwaltet Undo/Redo-Bildzustände ohne Zugriff auf Canvas-Interna."""

    def __init__(
        self,
        memory_limit: int = _HISTORY_MEMORY_LIMIT,
        redo_max: int = _REDO_MAX_ENTRIES,
    ) -> None:
        if redo_max < 0:
            raise ValueError("redo_max must be non-negative")
        self._undo: deque[tuple[Image.Image, str]] = deque()
        self._undo_bytes: int = 0
        self._redo: deque[tuple[Image.Image, str]] = deque(maxlen=redo_max)
        self._redo_bytes: int = 0
        self._original: Image.Image | None = None
        self._memory_limit: int = memory_limit

    @property
    def _history_bytes(self) -> int:
        return self._undo_bytes + self._redo_bytes

    @staticmethod
    def _img_bytes(img: Image.Image) -> int:
        return img.width * img.height * 4

    def _append_undo(self, current: Image.Image, desc: str) -> None:
        stored = current.copy()
        self._undo.append((stored, desc))
        self._undo_bytes += self._img_bytes(stored)

    def _append_redo(self, current: Image.Image, desc: str) -> None:
        if self._redo.maxlen == 0:
            return
        if len(self._redo) == self._redo.maxlen:
            self._evict_oldest_redo()
        stored = current.copy()
        self._redo.append((stored, desc))
        self._redo_bytes += self._img_bytes(stored)

    def _pop_undo(self) -> tuple[Image.Image, str]:
        img, desc = self._undo.pop()
        self._undo_bytes -= self._img_bytes(img)
        return img, desc

    def _pop_redo(self) -> tuple[Image.Image, str]:
        img, desc = self._redo.pop()
        self._redo_bytes -= self._img_bytes(img)
        return img, desc

    def _evict_oldest_undo(self) -> None:
        img, _ = self._undo.popleft()
        self._undo_bytes -= self._img_bytes(img)

    def _evict_oldest_redo(self) -> None:
        img, _ = self._redo.popleft()
        self._redo_bytes -= self._img_bytes(img)

    def _clear_redo(self) -> None:
        self._redo.clear()
        self._redo_bytes = 0

    def _trim(self) -> None:
        """Setzt das gemeinsame Undo-/Redo-Speicherbudget durch.

        Zuerst fallen die ältesten Undo-Zustände, jedoch nie der letzte
        Undo-Schritt. Reicht das nicht, werden die am weitesten entfernten
        Redo-Zustände entfernt. Ein einzelner Undo-Eintrag darf das Limit
        daher bewusst überschreiten; Originalbild und aktueller Zustand sind
        nicht Teil dieses Budgets.
        """
        while self._history_bytes > self._memory_limit:
            if len(self._undo) > 1:
                self._evict_oldest_undo()
            elif self._redo:
                self._evict_oldest_redo()
            else:
                break

    def push(self, current: Image.Image, desc: str) -> None:
        self._append_undo(current, desc)
        self._clear_redo()
        self._trim()

    def undo(self, current: Image.Image | None) -> tuple[Image.Image, str] | None:
        if not self._undo:
            return None
        img, desc = self._pop_undo()
        if current is not None:
            self._append_redo(current, desc)
            self._trim()
        return img, desc

    def redo(self, current: Image.Image | None) -> tuple[Image.Image, str] | None:
        if not self._redo:
            return None
        img, desc = self._pop_redo()
        if current is not None:
            self._append_undo(current, desc)
            self._trim()
        return img, desc

    def undo_to(
        self,
        current: Image.Image | None,
        steps: int,
    ) -> tuple[Image.Image, str, int] | None:
        actual = min(steps, len(self._undo))
        if actual <= 0:
            return None

        img: Image.Image | None = None
        desc = ""
        redo_current = current
        for _ in range(actual):
            img, desc = self._pop_undo()
            if redo_current is not None:
                self._append_redo(redo_current, desc)
            redo_current = img

        assert img is not None
        self._trim()
        return img, desc, actual

    def set_original(self, img: Image.Image) -> None:
        self._original = img.copy()

    def restore(
        self,
        current: Image.Image | None,
        desc: str,
    ) -> Image.Image | None:
        if self._original is None:
            return None
        self._clear_redo()
        if current is not None:
            self._append_undo(current, desc)
            self._trim()
        return self._original.copy()

    def descriptions(self) -> list[str]:
        return [desc for _, desc in reversed(self._undo)]

    def clear(self) -> None:
        self._undo.clear()
        self._undo_bytes = 0
        self._clear_redo()
        self._original = None
