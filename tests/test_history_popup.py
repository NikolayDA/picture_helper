"""Behavioral tests for the lazily built history popup."""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QPushButton, QWidget

from bgremover.history_popup import HistoryPopup


@pytest.fixture
def popup_fixture(qapp):
    parent = QWidget()
    parent.resize(500, 300)
    anchor = QPushButton("History", parent)
    anchor.setGeometry(20, 30, 100, 30)
    parent.show()
    qapp.processEvents()

    jumps: list[int] = []
    popup = HistoryPopup(parent, anchor, jumps.append)
    yield popup, anchor, jumps

    parent.close()
    qapp.processEvents()


def test_toggle_builds_positions_and_populates_popup(qapp, popup_fixture):
    popup, anchor, _jumps = popup_fixture
    popup.update_entries(["Newest", "Oldest"])
    assert popup._popup is None

    popup.toggle()
    qapp.processEvents()

    assert popup._popup is not None
    assert popup._popup.isVisible()
    assert popup._history_list is not None
    assert [popup._history_list.item(i).text() for i in range(2)] == [
        "Newest",
        "Oldest",
    ]
    expected = anchor.mapToGlobal(anchor.rect().topRight())
    assert popup._popup.pos().x() == expected.x() + 4
    assert popup._popup.pos().y() == expected.y()

    popup.toggle()
    assert not popup._popup.isVisible()


def test_update_and_double_click_use_one_based_history_index(qapp, popup_fixture):
    popup, _anchor, jumps = popup_fixture
    popup.toggle()
    popup.update_entries(["Current", "Previous", "Original"])

    assert popup._history_list is not None
    assert popup._history_list.count() == 3
    item = popup._history_list.item(1)
    assert item is not None

    popup._history_list.itemDoubleClicked.emit(item)

    assert jumps == [2]
