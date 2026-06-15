"""Unit-Tests für ``CanvasHistory`` (reine Logik, kein QApplication).

Undo und Redo teilen sich ein Byte-Budget. Die Tests prüfen deshalb nicht nur
die Stapelgrößen, sondern nach jedem relevanten Übergang auch die exakte
Bilanzierung beider Stapel.
"""
from __future__ import annotations

import pytest
from PIL import Image

from bgremover.canvas_history import CanvasHistory


def _img(width: int = 100, height: int = 100) -> Image.Image:
    return Image.new("RGBA", (width, height), (0, 0, 0, 255))


def _bytes(width: int, height: int) -> int:
    return width * height * 4


def _assert_accounting(history: CanvasHistory) -> None:
    undo_bytes = sum(history._img_bytes(img) for img, _ in history._undo)
    redo_bytes = sum(history._img_bytes(img) for img, _ in history._redo)
    assert history._undo_bytes == undo_bytes
    assert history._redo_bytes == redo_bytes
    assert history._history_bytes == undo_bytes + redo_bytes


def test_push_evicts_oldest_states_from_shared_budget() -> None:
    history = CanvasHistory(memory_limit=2_000)

    history.push(_img(10, 10), "small")   # 400 Bytes
    history.push(_img(20, 10), "medium")  # 800 Bytes
    history.push(_img(30, 10), "large")   # 1 200 Bytes

    assert history.descriptions() == ["large", "medium"]
    assert history._history_bytes == 2_000
    _assert_accounting(history)


def test_undo_counts_redo_and_evicts_farthest_redo_state() -> None:
    history = CanvasHistory(memory_limit=3_000)
    history.push(_img(10, 10), "a")  # 400 Bytes
    history.push(_img(20, 10), "b")  # 800 Bytes
    history.push(_img(30, 10), "c")  # 1 200 Bytes

    current = _img(40, 10)  # 1 600 Bytes
    first = history.undo(current)
    assert first is not None
    current = first[0]
    assert history._history_bytes == 2_800
    _assert_accounting(history)

    second = history.undo(current)
    assert second is not None
    # Das fernste Redo-Bild (40×10) wird entfernt, der unmittelbar nächste
    # Redo-Schritt (30×10) bleibt erhalten.
    assert [desc for _, desc in history._redo] == ["b"]
    assert history._history_bytes == _bytes(10, 10) + _bytes(30, 10)
    _assert_accounting(history)

    redone = history.redo(second[0])
    assert redone is not None
    assert redone[1] == "b"
    _assert_accounting(history)


def test_undo_to_updates_both_counters_before_trimming() -> None:
    history = CanvasHistory(memory_limit=3_000)
    history.push(_img(10, 10), "a")
    history.push(_img(20, 10), "b")
    history.push(_img(30, 10), "c")

    result = history.undo_to(_img(40, 10), 2)

    assert result is not None
    assert result[1:] == ("b", 2)
    assert history.descriptions() == ["a"]
    assert [desc for _, desc in history._redo] == ["b"]
    _assert_accounting(history)


def test_restore_clears_redo_and_stays_within_shared_budget() -> None:
    history = CanvasHistory(memory_limit=1_200)
    history.set_original(_img(10, 10))
    history.push(_img(10, 10), "edit")
    undone = history.undo(_img(20, 10))
    assert undone is not None
    assert history._redo_bytes == _bytes(20, 10)

    restored = history.restore(undone[0], "restored")

    assert restored is not None
    assert not history._redo
    assert history._redo_bytes == 0
    assert history._history_bytes <= 1_200
    _assert_accounting(history)


def test_repeated_restore_does_not_grow_history_unbounded() -> None:
    history = CanvasHistory(memory_limit=1_200)
    history.set_original(_img(10, 10))
    current = _img(30, 10)

    for _ in range(20):
        restored = history.restore(current, "restored")
        assert restored is not None
        current = restored
        assert history._history_bytes <= 1_200
        _assert_accounting(history)


def test_trim_keeps_at_least_one_undo_entry() -> None:
    history = CanvasHistory(memory_limit=1)
    history.push(_img(), "a")
    history.push(_img(), "b")

    assert history.descriptions() == ["b"]
    assert history._undo_bytes == _bytes(100, 100)
    assert history._history_bytes > history._memory_limit
    _assert_accounting(history)


def test_redo_stack_cap_updates_byte_counter() -> None:
    cap = 3
    history = CanvasHistory(redo_max=cap)
    assert history._redo.maxlen == cap
    current = _img()
    for _ in range(cap + 5):
        history.push(current, "edit")
        current = _img()

    for _ in range(cap + 5):
        result = history.undo(current)
        if result is None:
            break
        current = result[0]
        _assert_accounting(history)

    assert len(history._redo) == cap
    assert history._redo_bytes == cap * _bytes(100, 100)


def test_negative_redo_cap_is_rejected() -> None:
    with pytest.raises(ValueError, match="redo_max"):
        CanvasHistory(redo_max=-1)


def test_zero_redo_cap_does_not_copy_current_image(monkeypatch) -> None:
    history = CanvasHistory(redo_max=0)
    history.push(_img(), "edit")
    current = _img()
    copies = 0
    original_copy = Image.Image.copy

    def counting_copy(img: Image.Image) -> Image.Image:
        nonlocal copies
        copies += 1
        return original_copy(img)

    monkeypatch.setattr(Image.Image, "copy", counting_copy)
    assert history.undo(current) is not None

    assert copies == 0
    assert not history._redo
    assert history._redo_bytes == 0


def test_push_clears_redo_and_its_counter() -> None:
    history = CanvasHistory()
    history.push(_img(10, 10), "a")
    undone = history.undo(_img(20, 10))
    assert undone is not None
    assert history._redo_bytes == _bytes(20, 10)

    history.push(undone[0], "new branch")

    assert not history._redo
    assert history._redo_bytes == 0
    _assert_accounting(history)


def test_clear_resets_stacks_counters_and_original() -> None:
    history = CanvasHistory()
    history.set_original(_img())
    history.push(_img(), "a")
    undone = history.undo(_img())
    assert undone is not None

    history.clear()

    assert not history._undo
    assert not history._redo
    assert history._undo_bytes == 0
    assert history._redo_bytes == 0
    assert history._history_bytes == 0
    assert history._original is None


def test_repeated_undo_redo_never_exceeds_shared_budget() -> None:
    image_bytes = _bytes(10, 10)
    history = CanvasHistory(memory_limit=image_bytes * 3)
    history.push(_img(10, 10), "a")
    history.push(_img(10, 10), "b")
    history.push(_img(10, 10), "c")
    current = _img(10, 10)

    for _ in range(100):
        undone = history.undo(current)
        assert undone is not None
        current = undone[0]
        assert history._history_bytes <= history._memory_limit
        _assert_accounting(history)

        redone = history.redo(current)
        assert redone is not None
        current = redone[0]
        assert history._history_bytes <= history._memory_limit
        _assert_accounting(history)
