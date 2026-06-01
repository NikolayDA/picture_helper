"""Undo/Redo-Verlaufszustand für ImageCanvas."""
from __future__ import annotations

from collections import deque

from PIL import Image

from bgremover.constants import _REDO_MAX_ENTRIES, _UNDO_MEMORY_LIMIT


class CanvasHistory:
    """Verwaltet Undo/Redo-Bildzustände ohne Zugriff auf Canvas-Interna."""

    def __init__(
        self,
        memory_limit: int = _UNDO_MEMORY_LIMIT,
        redo_max: int = _REDO_MAX_ENTRIES,
    ) -> None:
        self._undo: deque[tuple[Image.Image, str]] = deque()
        self._undo_bytes: int = 0
        self._redo: deque[tuple[Image.Image, str]] = deque(maxlen=redo_max)
        self._original: Image.Image | None = None
        self._memory_limit: int = memory_limit
        self._redo_max: int = redo_max

    @staticmethod
    def _img_bytes(img: Image.Image) -> int:
        return img.width * img.height * 4

    def _trim(self) -> None:
        """Setzt das Undo-Speicherbudget durch (behält mind. einen Eintrag).

        Einzige Stelle der Eviction – von jedem Pfad aufgerufen, der den
        Undo-Stapel wachsen lässt (``push``, ``redo``, ``restore``). Ohne
        diesen gemeinsamen Aufruf umgingen ``redo``/``restore`` das Budget
        und wiederholtes Wiederherstellen ließe den Speicher unbeschränkt
        wachsen.
        """
        while len(self._undo) > 1 and self._undo_bytes > self._memory_limit:
            evicted, _ = self._undo.popleft()
            self._undo_bytes -= self._img_bytes(evicted)

    def push(self, current: Image.Image, desc: str) -> None:
        self._undo.append((current.copy(), desc))
        self._undo_bytes += self._img_bytes(current)
        self._redo.clear()
        self._trim()

    def undo(self, current: Image.Image | None) -> tuple[Image.Image, str] | None:
        if not self._undo:
            return None
        img, desc = self._undo.pop()
        self._undo_bytes -= self._img_bytes(img)
        if current is not None:
            self._redo.append((current.copy(), desc))
        return img, desc

    def redo(self, current: Image.Image | None) -> tuple[Image.Image, str] | None:
        if not self._redo:
            return None
        img, desc = self._redo.pop()
        if current is not None:
            self._undo.append((current.copy(), desc))
            self._undo_bytes += self._img_bytes(current)
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
            img, desc = self._undo.pop()
            self._undo_bytes -= self._img_bytes(img)
            if redo_current is not None:
                self._redo.append((redo_current.copy(), desc))
            redo_current = img

        assert img is not None
        return img, desc, actual

    def set_original(self, img: Image.Image) -> None:
        self._original = img.copy()

    def restore(self, current: Image.Image | None) -> Image.Image | None:
        if self._original is None:
            return None
        if current is not None:
            self._undo.append((current.copy(), "🔄 Original wiederhergestellt"))
            self._undo_bytes += self._img_bytes(current)
            self._trim()
        self._redo.clear()
        return self._original.copy()

    def descriptions(self) -> list[str]:
        return [desc for _, desc in reversed(self._undo)]

    def clear(self) -> None:
        self._undo.clear()
        self._undo_bytes = 0
        self._redo.clear()
        self._original = None
