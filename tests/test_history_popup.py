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


def test_toggle_opens_and_populates_popup_anchored_to_button(qapp, popup_fixture):
    popup, anchor, _jumps = popup_fixture
    popup.update_entries(["Newest", "Oldest"])
    assert popup.is_open is False

    popup.toggle()
    qapp.processEvents()

    assert popup.is_open is True
    assert popup.item_texts() == ["Newest", "Oldest"]
    # Ankerbezug: das Popup öffnet sich rechts neben dem Anker, auf dessen
    # Höhe – der genaue Pixel-Versatz ist kein geprüfter Vertrag.
    assert popup.list_widget is not None
    popup_pos = popup.list_widget.window().pos()
    anchor_top_right = anchor.mapToGlobal(anchor.rect().topRight())
    assert popup_pos.x() > anchor_top_right.x()
    assert popup_pos.y() == anchor_top_right.y()

    popup.toggle()
    assert popup.is_open is False


def test_update_and_double_click_use_one_based_history_index(qapp, popup_fixture):
    popup, _anchor, jumps = popup_fixture
    popup.toggle()
    popup.update_entries(["Current", "Previous", "Original"])

    assert popup.item_texts() == ["Current", "Previous", "Original"]
    lst = popup.list_widget
    assert lst is not None
    item = lst.item(1)
    assert item is not None

    lst.itemDoubleClicked.emit(item)

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

    lst = popup.list_widget
    assert lst is not None
    lst.setCurrentRow(2)
    QTest.keyClick(lst, Qt.Key.Key_Return)
    assert jumps == [3]
    # Ohne Auswahl bleibt Enter wirkungslos (kein Sprung ins Leere).
    lst.setCurrentRow(-1)
    QTest.keyClick(lst, Qt.Key.Key_Return)
    assert jumps == [3]


def test_popup_follows_active_palette(qapp, popup_fixture):
    """#428/#441: Das lazy gebaute Popup wird bei jedem Öffnen neu gestylt.

    Dokumentierter White-Box-Guard: prüft bewusst die Stylesheet-Strings des
    internen Listen-Widgets (öffentlich über ``list_widget``, da es das
    reale Zielwidget für Interaktionstests ist) und des Dialog-Fensters
    (``QDialog.window()`` – die Palette wird auf das oberste Fenster
    angewandt, kein Zugriff auf das private ``_popup`` nötig).
    """
    from bgremover.theme import DARK, LIGHT, set_active_palette

    popup, _anchor, _jumps = popup_fixture
    try:
        set_active_palette(DARK)
        popup.toggle()  # dunkel gebaut
        lst = popup.list_widget
        assert lst is not None
        assert DARK.tabbar in lst.styleSheet()
        assert ":focus" in lst.styleSheet()

        popup.toggle()  # schließen
        set_active_palette(LIGHT)
        popup.toggle()  # erneut öffnen → helle Stile
        lst = popup.list_widget
        assert lst is not None
        assert LIGHT.tabbar in lst.styleSheet()
        assert LIGHT.inspector in lst.window().styleSheet()
    finally:
        set_active_palette(DARK)
