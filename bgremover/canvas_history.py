"""Undo/Redo-Verlaufslogik für ImageCanvas."""
from __future__ import annotations

from PIL import Image


def img_bytes(img: Image.Image) -> int:
    """Geschätzte RGBA-Rohdatengröße eines Bildes in Bytes."""
    return img.width * img.height * 4


def emit_history(canvas) -> None:
    """Sendet die aktuelle Verlaufsliste (neueste zuerst)."""
    canvas.historyChanged.emit([d for _, d in reversed(list(canvas._undo))])


def undo(canvas) -> None:
    if canvas._crop_overlay is not None:
        canvas.cancel_crop()
        return
    if canvas._undo:
        img, desc = canvas._undo.pop()
        canvas._undo_bytes -= img_bytes(img)
        if canvas._pil is not None:
            canvas._redo.append((canvas._pil.copy(), desc))
        canvas._set_image_state(img)
        emit_history(canvas)
        canvas.statusMsg.emit(f"↩  Rückgängig: {desc}")
    else:
        canvas.statusMsg.emit("Nichts mehr zum Rückgängigmachen")


def redo(canvas) -> None:
    if canvas._crop_overlay is not None:
        return
    if canvas._redo:
        img, desc = canvas._redo.pop()
        if canvas._pil is not None:
            canvas._undo.append((canvas._pil.copy(), desc))
            canvas._undo_bytes += img_bytes(canvas._pil)
        canvas._set_image_state(img)
        emit_history(canvas)
        canvas.statusMsg.emit(f"↪  Wiederherstellen: {desc}")
    else:
        canvas.statusMsg.emit("Nichts mehr zum Wiederherstellen")


def undo_to(canvas, steps: int) -> None:
    if canvas._crop_overlay is not None:
        canvas.cancel_crop()
        return
    actual = min(steps, len(canvas._undo))
    if actual <= 0:
        return
    img, desc = None, ""
    for _ in range(actual):
        img, desc = canvas._undo.pop()
        canvas._undo_bytes -= img_bytes(img)
        if canvas._pil is not None:
            canvas._redo.append((canvas._pil.copy(), desc))
        canvas._pil = img
    assert img is not None
    canvas._set_image_state(img)
    emit_history(canvas)
    canvas.statusMsg.emit(f"↩  {actual} Schritt(e) rückgängig  (bis: {desc})")


def restore_original(canvas) -> None:
    if canvas._original:
        canvas._cancel_crop_overlay()
        if canvas._pil is not None:
            canvas._undo.append((canvas._pil.copy(), "🔄 Original wiederhergestellt"))
            canvas._undo_bytes += img_bytes(canvas._pil)
        canvas._redo.clear()
        canvas._set_image_state(canvas._original.copy())
        emit_history(canvas)
        canvas.statusMsg.emit("🔄  Original wiederhergestellt")
