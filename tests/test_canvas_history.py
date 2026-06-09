"""Unit-Tests für ``CanvasHistory`` (reine Logik, kein QApplication).

Schwerpunkt: das Undo-Speicherbudget muss auf JEDEM wachsenden Pfad
greifen – nicht nur in ``push``, sondern auch in ``redo`` und ``restore``
– und selbst bei sehr kleinem Budget mindestens einen Undo-Schritt behalten.
"""
from __future__ import annotations

from PIL import Image

from bgremover.canvas_history import CanvasHistory

# 100×100 RGBA ⇒ 40 000 Bytes je Bild (siehe CanvasHistory._img_bytes).
_IMG_BYTES = 100 * 100 * 4
_LIMIT = _IMG_BYTES * 2  # Budget für ~2 Bilder


def _img() -> Image.Image:
    return Image.new("RGBA", (100, 100), (0, 0, 0, 255))


def test_push_enforces_budget() -> None:
    h = CanvasHistory(memory_limit=_LIMIT)
    for _ in range(20):
        h.push(_img(), "edit")
    assert h._undo_bytes <= _LIMIT
    assert len(h._undo) <= 2


def test_restore_does_not_grow_undo_unbounded() -> None:
    """Wiederholtes Wiederherstellen darf das Budget nicht umgehen."""
    h = CanvasHistory(memory_limit=_LIMIT)
    h.set_original(_img())
    current = _img()
    for _ in range(20):
        restored = h.restore(current, "restored")
        assert restored is not None
        current = restored
    assert h._undo_bytes <= _LIMIT
    assert len(h._undo) <= 2


def test_redo_respects_budget() -> None:
    """Auch der redo→undo-Pfad budgetiert den Undo-Stapel."""
    h = CanvasHistory(memory_limit=_LIMIT)
    # Stapel aufbauen und einige Schritte zurücknehmen, damit redo gefüllt ist.
    current = _img()
    for _ in range(5):
        h.push(current, "edit")
        current = _img()
    for _ in range(5):
        result = h.undo(current)
        if result is None:
            break
        current = result[0]
    # Jetzt mehrfach redo → hängt jeweils an undo an.
    for _ in range(5):
        result = h.redo(current)
        if result is None:
            break
        current = result[0]
    assert h._undo_bytes <= _LIMIT
    assert len(h._undo) <= 2


def test_trim_keeps_at_least_one_entry() -> None:
    """Selbst bei winzigem Budget bleibt ein Undo-Schritt erhalten."""
    h = CanvasHistory(memory_limit=1)  # kleiner als jedes Bild
    h.push(_img(), "a")
    h.push(_img(), "b")
    assert len(h._undo) == 1
    assert h._undo_bytes == _IMG_BYTES


def test_redo_stack_capped_by_maxlen() -> None:
    """Der Redo-Stapel wird allein durch ``deque(maxlen=redo_max)`` begrenzt.

    Regression für #199: Das früher separat gepflegte Attribut ``_redo_max``
    war write-only – ``maxlen`` ist die einzige Quelle der Begrenzung. Nach
    mehr Undo-Schritten als ``redo_max`` darf der Redo-Stapel nicht über die
    Obergrenze hinaus wachsen.
    """
    cap = 3
    h = CanvasHistory(redo_max=cap)
    assert h._redo.maxlen == cap
    current = _img()
    for _ in range(cap + 5):
        h.push(current, "edit")
        current = _img()
    for _ in range(cap + 5):
        result = h.undo(current)
        if result is None:
            break
        current = result[0]
    assert len(h._redo) == cap
