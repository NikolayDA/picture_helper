"""Kleine stateless Helfer fuer ``ImageCanvas``."""
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Literal

from PyQt6.QtCore import Qt


def _requires_image(method: Callable[..., None]) -> Callable[..., None]:
    """Fruehausstieg-Guard fuer Canvas-Methoden ohne geladenes Bild."""
    @functools.wraps(method)
    def wrapper(self, *args: object, **kwargs: object) -> None:
        if self._pil is None:
            self.statusMsg.emit("Kein Bild geladen")
            return
        method(self, *args, **kwargs)
    return wrapper


def _selection_mode_from_modifiers(
    mods: Qt.KeyboardModifier,
) -> Literal["set", "add", "subtract"]:
    if mods & Qt.KeyboardModifier.ShiftModifier:
        return "add"
    if mods & Qt.KeyboardModifier.ControlModifier:
        return "subtract"
    return "set"
