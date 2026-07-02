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


def test_enter_jumps_to_selected_entry(qapp, popup_fixture):
    """#441: Enter/Return springt zum gewählten Eintrag (Tastaturpfad).

    Bewusst über Widget-Shortcuts statt ``itemActivated``: Letzteres feuert
    plattformabhängig auch beim Doppelklick, und ``undo_to`` ist **relativ** –
    ein Doppel-Sprung wäre ein Bug.
    """
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    popup, _anchor, jumps = popup_fixture
    popup.toggle()
    popup.update_entries(["Current", "Previous", "Original"])

    lst = popup._history_list
    assert lst is not None
    lst.setCurrentRow(2)
    QTest.keyClick(lst, Qt.Key.Key_Return)
    assert jumps == [3]
    # Ohne Auswahl bleibt Enter wirkungslos (kein Sprung ins Leere).
    lst.setCurrentRow(-1)
    QTest.keyClick(lst, Qt.Key.Key_Return)
    assert jumps == [3]


def test_popup_follows_active_palette(qapp, popup_fixture):
    """#428/#441: Das lazy gebaute Popup wird bei jedem Öffnen neu gestylt."""
    from bgremover.theme import DARK, LIGHT, set_active_palette

    popup, _anchor, _jumps = popup_fixture
    try:
        set_active_palette(DARK)
        popup.toggle()  # dunkel gebaut
        assert popup._history_list is not None
        assert DARK.tabbar in popup._history_list.styleSheet()
        assert ":focus" in popup._history_list.styleSheet()

        popup.toggle()  # schließen
        set_active_palette(LIGHT)
        popup.toggle()  # erneut öffnen → helle Stile
        assert LIGHT.tabbar in popup._history_list.styleSheet()
        assert popup._popup is not None
        assert LIGHT.inspector in popup._popup.styleSheet()
    finally:
        set_active_palette(DARK)
