"""Menü- und QAction-Verdrahtung für das Hauptfenster."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence
from PyQt6.QtWidgets import QMenu, QMenuBar

from bgremover.i18n import tr
from bgremover.preview_mode import PreviewMode
from bgremover.recent_files import RecentFiles, RecentFilesMenu
from bgremover.theme import active_palette, menu_style


@dataclass(frozen=True)
class MainMenuCallbacks:
    """Slots für das Hauptmenü, ohne direkte Abhängigkeit von ``MainWindow``."""

    open_image: Callable[[], None]
    open_recent_path: Callable[[str], None]
    recent_path_missing: Callable[[str], None]
    save: Callable[[], None]
    save_as: Callable[[], None]
    new_project: Callable[[], None]
    open_project: Callable[[], None]
    save_project: Callable[[], None]
    save_project_as: Callable[[], None]
    export_eufymake: Callable[[], None]
    undo: Callable[[], None]
    redo: Callable[[], None]
    rotate: Callable[[int], None]
    flip: Callable[[bool], None]
    resize: Callable[[], None]
    clear_selection: Callable[[], None]
    invert_selection: Callable[[], None]
    restore_original: Callable[[], None]
    fit_to_view: Callable[[], None]
    # Verlauf-Popup (#458): neuer Menü-Anker, nachdem der Rail-Button entfiel.
    toggle_history: Callable[[], None]
    set_preview_mode: Callable[[PreviewMode], None]
    toggle_preview3d: Callable[[bool], None]
    toggle_light_mode: Callable[[bool], None]
    open_settings: Callable[[], None]
    check_for_updates: Callable[[], None]
    manage_ai_model: Callable[[], None]
    install_ai_backend: Callable[[], None]


def build_main_menu(
    parent: QObject,
    menu_bar: QMenuBar,
    recent_files: RecentFiles,
    callbacks: MainMenuCallbacks,
    *,
    light_mode: bool = False,
) -> RecentFilesMenu:
    """Baut die Menüleiste und gibt den Recent-Files-Adapter zurück."""

    menu_bar.setStyleSheet(menu_style(active_palette()))

    file_menu = _add_menu(menu_bar, tr("menu.file"))
    _add_action(file_menu, parent, tr("action.open"), callbacks.open_image, "Ctrl+O")

    recent_qmenu = _add_submenu(file_menu, tr("menu.recent_files"))
    recent_menu = RecentFilesMenu(
        parent,
        recent_qmenu,
        recent_files,
        open_path=callbacks.open_recent_path,
        missing_path=callbacks.recent_path_missing,
    )

    file_menu.addSeparator()
    _add_action(file_menu, parent, tr("action.save"), callbacks.save, "Ctrl+S")
    _add_action(file_menu, parent, tr("action.save_as"), callbacks.save_as, "Ctrl+Shift+S")

    # Projekt-Menü: eigene, dokumentierte Kürzel; Ctrl+O/Ctrl+S bleiben den
    # Bild-Workflows vorbehalten (#334).
    project_menu = _add_menu(menu_bar, tr("menu.project"))
    _add_action(
        project_menu, parent, tr("action.new_project"),
        callbacks.new_project, "Ctrl+N")
    _add_action(
        project_menu, parent, tr("action.open_project"),
        callbacks.open_project, "Ctrl+Shift+O")
    project_menu.addSeparator()
    _add_action(
        project_menu, parent, tr("action.save_project"),
        callbacks.save_project, "Ctrl+Alt+S")
    _add_action(
        project_menu, parent, tr("action.save_project_as"),
        callbacks.save_project_as, "Ctrl+Alt+Shift+S")
    project_menu.addSeparator()
    _add_action(
        project_menu, parent, tr("action.export_eufymake"),
        callbacks.export_eufymake, "Ctrl+Alt+E")

    edit_menu = _add_menu(menu_bar, tr("menu.edit"))
    _add_action(edit_menu, parent, tr("action.undo"), callbacks.undo, "Ctrl+Z")
    _add_action(edit_menu, parent, tr("action.redo"), callbacks.redo, "Ctrl+Shift+Z")
    edit_menu.addSeparator()
    _add_action(edit_menu, parent, tr("action.rotate_left_90"), lambda: callbacks.rotate(90), "Ctrl+Left")
    _add_action(edit_menu, parent, tr("action.rotate_right_90"), lambda: callbacks.rotate(-90), "Ctrl+Right")
    _add_action(edit_menu, parent, tr("action.rotate_180"), lambda: callbacks.rotate(180))
    _add_action(edit_menu, parent, tr("action.flip_horizontal"), lambda: callbacks.flip(True))
    _add_action(edit_menu, parent, tr("action.flip_vertical"), lambda: callbacks.flip(False))
    _add_action(edit_menu, parent, tr("action.resize"), callbacks.resize, "Ctrl+R")
    edit_menu.addSeparator()
    _add_action(edit_menu, parent, tr("action.clear_selection"), callbacks.clear_selection)
    _add_action(edit_menu, parent, tr("action.invert_selection"), callbacks.invert_selection, "Ctrl+Shift+I")
    _add_action(edit_menu, parent, tr("action.restore_original"), callbacks.restore_original)

    view_menu = _add_menu(menu_bar, tr("menu.view"))
    _add_action(view_menu, parent, tr("action.fit_to_view"), callbacks.fit_to_view, "Ctrl+0")
    _add_action(view_menu, parent, tr("action.history"), callbacks.toggle_history)
    preview_menu = _add_submenu(view_menu, tr("menu.preview_mode"))
    preview_group = QActionGroup(parent)
    preview_group.setExclusive(True)
    for mode, label in (
        (PreviewMode.COLOR, tr("preview.mode.color")),
        (PreviewMode.RELIEF, tr("preview.mode.relief")),
        (PreviewMode.HEIGHT, tr("preview.mode.height")),
        (PreviewMode.GLOSS, tr("preview.mode.gloss")),
        (PreviewMode.COMBINED, tr("preview.mode.combined")),
    ):
        action = _add_action(
            preview_menu,
            parent,
            label,
            partial(callbacks.set_preview_mode, mode),
        )
        action.setCheckable(True)
        action.setChecked(mode is PreviewMode.COLOR)
        action.setData(mode)
        action.setObjectName(f"preview_mode_{mode.value}")
        preview_group.addAction(action)

    # 3D-Reliefvorschau (Epic #582): checkbarer Umschalter, signalbasiert mit
    # dem Höhen-Tab-Segment synchron (kein Shortcut im MVP, UX-Vertrag §1).
    show_3d_action = QAction(tr("menu.view.show_3d"), parent)
    show_3d_action.setObjectName("preview3d_toggle")
    show_3d_action.setCheckable(True)
    show_3d_action.toggled.connect(lambda checked: callbacks.toggle_preview3d(checked))
    view_menu.addAction(show_3d_action)

    view_menu.addSeparator()
    # Helles Design umschalten (#428) – reiner UI-Zustand, in QSettings gemerkt.
    theme_action = QAction(tr("action.light_mode"), parent)
    theme_action.setObjectName("theme_toggle")
    theme_action.setCheckable(True)
    theme_action.setChecked(light_mode)
    theme_action.toggled.connect(lambda checked: callbacks.toggle_light_mode(checked))
    view_menu.addAction(theme_action)

    extras_menu = _add_menu(menu_bar, tr("menu.extras"))
    _add_action(extras_menu, parent, tr("action.settings"), callbacks.open_settings, "Ctrl+,")
    extras_menu.addSeparator()
    _add_action(
        extras_menu, parent, tr("action.check_for_updates"), callbacks.check_for_updates)
    # Bewusst IMMER aktiv – auch ohne installiertes rembg (#575): Qt zeigt
    # Tooltips in Menüs standardmäßig nicht an, ein still deaktivierter
    # Eintrag wirkt daher wie ein Bug („Klick tut nichts"). Der Dialog selbst
    # erklärt den Zustand (``ModelStatus.REMBG_UNAVAILABLE`` inkl. aktiver
    # Python-Umgebung) und sperrt den Download-Button.
    _add_action(
        extras_menu, parent, tr("action.manage_ai_model"), callbacks.manage_ai_model)
    # Ebenfalls immer aktiv (analog #575): zeigt den Nachrüst-Befehl auch dann,
    # wenn rembg bereits installiert ist (harmloser Hinweis statt Sackgasse).
    _add_action(
        extras_menu, parent, tr("action.install_ai_backend"), callbacks.install_ai_backend)

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
    # QAction.triggered liefert den checked-State; die Callbacks erwarten
    # keine Argumente.
    action.triggered.connect(lambda _checked=False: triggered())
    menu.addAction(action)
    return action
