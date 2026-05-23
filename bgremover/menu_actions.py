"""Menu and QAction wiring for the main window."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QMenu, QMenuBar

from bgremover.recent_files import RecentFiles, RecentFilesMenu


MENU_STYLE = """
    QMenuBar { background: #1a1a1a; color: #ccc; }
    QMenuBar::item:selected { background: #333; }
    QMenu { background: #252525; color: #ccc; border: 1px solid #3a3a3a; }
    QMenu::item:selected { background: #4a90d9; }
"""


@dataclass(frozen=True)
class MainMenuCallbacks:
    """Slots used by the main menu without depending on ``MainWindow``."""

    open_image: Callable[[], None]
    open_recent_path: Callable[[str], None]
    recent_path_missing: Callable[[str], None]
    save: Callable[[], None]
    save_as: Callable[[], None]
    undo: Callable[[], None]
    redo: Callable[[], None]
    rotate: Callable[[int], None]
    flip: Callable[[bool], None]
    clear_selection: Callable[[], None]
    invert_selection: Callable[[], None]
    restore_original: Callable[[], None]
    fit_to_view: Callable[[], None]
    open_settings: Callable[[], None]


def build_main_menu(
    parent: QObject,
    menu_bar: QMenuBar,
    recent_files: RecentFiles,
    callbacks: MainMenuCallbacks,
) -> RecentFilesMenu:
    """Build the top-level menu bar and return the recent-files adapter."""

    menu_bar.setStyleSheet(MENU_STYLE)

    file_menu = _add_menu(menu_bar, "Datei")
    _add_action(file_menu, parent, "Öffnen…", callbacks.open_image, "Ctrl+O")

    recent_qmenu = _add_submenu(file_menu, "Zuletzt geöffnet")
    recent_menu = RecentFilesMenu(
        parent,
        recent_qmenu,
        recent_files,
        open_path=callbacks.open_recent_path,
        missing_path=callbacks.recent_path_missing,
    )

    file_menu.addSeparator()
    _add_action(file_menu, parent, "Speichern", callbacks.save, "Ctrl+S")
    _add_action(file_menu, parent, "Speichern unter…", callbacks.save_as, "Ctrl+Shift+S")

    edit_menu = _add_menu(menu_bar, "Bearbeiten")
    _add_action(edit_menu, parent, "Rückgängig", callbacks.undo, "Ctrl+Z")
    _add_action(edit_menu, parent, "Wiederherstellen", callbacks.redo, "Ctrl+Shift+Z")
    edit_menu.addSeparator()
    _add_action(edit_menu, parent, "90° links drehen", lambda: callbacks.rotate(90), "Ctrl+Left")
    _add_action(edit_menu, parent, "90° rechts drehen", lambda: callbacks.rotate(-90), "Ctrl+Right")
    _add_action(edit_menu, parent, "180° drehen", lambda: callbacks.rotate(180))
    _add_action(edit_menu, parent, "Horizontal spiegeln", lambda: callbacks.flip(True))
    _add_action(edit_menu, parent, "Vertikal spiegeln", lambda: callbacks.flip(False))
    edit_menu.addSeparator()
    _add_action(edit_menu, parent, "Auswahl aufheben", callbacks.clear_selection, "Escape")
    _add_action(edit_menu, parent, "Auswahl invertieren", callbacks.invert_selection, "Ctrl+Shift+I")
    _add_action(edit_menu, parent, "Original wiederherstellen", callbacks.restore_original)

    view_menu = _add_menu(menu_bar, "Ansicht")
    _add_action(view_menu, parent, "Fit to View", callbacks.fit_to_view, "Ctrl+0")

    extras_menu = _add_menu(menu_bar, "Extras")
    _add_action(extras_menu, parent, "Einstellungen…", callbacks.open_settings, "Ctrl+,")

    return recent_menu


def _add_menu(menu_bar: QMenuBar, title: str) -> QMenu:
    menu = menu_bar.addMenu(title)
    assert menu is not None
    return menu


def _add_submenu(menu: QMenu, title: str) -> QMenu:
    submenu = menu.addMenu(title)
    assert submenu is not None
    return submenu


def _add_action(
    menu: QMenu,
    parent: QObject,
    text: str,
    triggered: Callable[[], None],
    shortcut: str | None = None,
) -> QAction:
    action = QAction(text, parent)
    if shortcut is not None:
        action.setShortcut(QKeySequence(shortcut))
    action.triggered.connect(triggered)
    menu.addAction(action)
    return action
