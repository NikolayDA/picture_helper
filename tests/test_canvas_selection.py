"""Korrektheits- und Zustandszaehler-Tests fuer ``CanvasSelection``."""
from __future__ import annotations

import numpy as np
import pytest

from bgremover.canvas_selection import CanvasSelection


def _assert_state(selection: CanvasSelection, expected: np.ndarray) -> None:
    count = int(np.count_nonzero(expected))
    np.testing.assert_array_equal(selection.mask, expected)
    assert selection.selected_count == count
    assert selection.has_selection is (count > 0)


def test_set_clear_reset_and_read_only_mask_stay_synchronized() -> None:
    selection = CanvasSelection(5, 4)
    mask = np.zeros((4, 5), dtype=bool)
    mask[1:3, 2:4] = True

    assert selection.set_mask(mask) == 4
    _assert_state(selection, mask)
    with pytest.raises(ValueError):
        selection.mask[0, 0] = True

    selection.clear()
    _assert_state(selection, np.zeros((4, 5), dtype=bool))

    selection.reset(3, 2)
    _assert_state(selection, np.zeros((2, 3), dtype=bool))


def test_set_add_and_subtract_results_update_count() -> None:
    selection = CanvasSelection(5, 4)
    first = np.zeros((4, 5), dtype=bool)
    first[1:3, 1:3] = True
    added = np.zeros((4, 5), dtype=bool)
    added[2:4, 2:4] = True
    removed = np.zeros((4, 5), dtype=bool)
    removed[1, 1:3] = True

    assert selection.set_wand_result(first, "set") == 4
    expected = first.copy()
    _assert_state(selection, expected)

    assert selection.set_polygon_result(added, "add") == 7
    expected |= added
    _assert_state(selection, expected)

    assert selection.set_wand_result(removed, "subtract") == 5
    expected &= ~removed
    _assert_state(selection, expected)


def test_invert_and_morphology_update_count() -> None:
    selection = CanvasSelection(7, 7)
    mask = np.zeros((7, 7), dtype=bool)
    mask[3, 3] = True
    selection.set_mask(mask)

    assert selection.invert() == 48
    _assert_state(selection, ~mask)
    assert selection.invert() == 1
    _assert_state(selection, mask)

    expanded_count = selection.morphology(1, "expand")
    assert expanded_count == 9
    assert selection.selected_count == 9
    assert selection.morphology(0, "shrink") == 9

    shrunk_count = selection.morphology(1, "shrink")
    assert shrunk_count == 1
    _assert_state(selection, mask)


def test_brush_updates_count_only_for_changed_pixels() -> None:
    selection = CanvasSelection(20, 20)

    selection.paint_brush(5, 5, 2, additive=True)
    first_count = selection.selected_count
    assert first_count > 0

    selection.paint_brush(5, 5, 2, additive=True)
    assert selection.selected_count == first_count

    selection.paint_brush(14, 14, 2, additive=True)
    assert selection.selected_count == first_count * 2

    selection.paint_brush(5, 5, 2, additive=False)
    assert selection.selected_count == first_count
    assert selection.has_selection

    selection.paint_brush(14, 14, 2, additive=False)
    assert selection.selected_count == 0
    assert not selection.has_selection
