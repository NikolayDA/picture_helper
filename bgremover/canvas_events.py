"""Kleine Event-Helfer für ``ImageCanvas``.

Ziel: UI-Ereignisentscheidungen aus ``canvas.py`` herausziehen,
um die Event-Dispatcher leichter lesbar und testbarer zu halten.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QScrollBar


def should_start_pan(btn: Qt.MouseButton, mods: Qt.KeyboardModifier) -> bool:
    """True bei Mittelklick oder Alt+Linksklick."""
    return bool(
        btn == Qt.MouseButton.MiddleButton
        or (btn == Qt.MouseButton.LeftButton and mods & Qt.KeyboardModifier.AltModifier)
    )


def cursor_for_crop_hit(corner: int, inside: bool) -> QCursor:
    """Bestimmt Cursor im Crop-Modus anhand Hit-Test-Ergebnis."""
    if corner >= 0:
        shape = (Qt.CursorShape.SizeFDiagCursor
                 if corner in (0, 3)
                 else Qt.CursorShape.SizeBDiagCursor)
        return QCursor(shape)
    if inside:
        return QCursor(Qt.CursorShape.OpenHandCursor)
    return QCursor(Qt.CursorShape.ArrowCursor)


def apply_pan_delta(hbar: QScrollBar, vbar: QScrollBar, dx: float, dy: float) -> None:
    """Verschiebt View-Scrollbars um das gegebene Delta."""
    hbar.setValue(hbar.value() - int(dx))
    vbar.setValue(vbar.value() - int(dy))
