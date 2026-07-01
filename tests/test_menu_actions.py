"""Tests for the menu/action builder without constructing ``MainWindow``."""
from __future__ import annotations

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QMainWindow

from bgremover.menu_actions import MainMenuCallbacks, build_main_menu
from bgremover.preview_mode import PreviewMode
from bgremover.recent_files import RecentFiles, RecentFilesMenu


def _portable_shortcut(action: QAction) -> str:
    return action.shortcut().toString(QKeySequence.SequenceFormat.PortableText)


def _actions(window: QMainWindow) -> dict[str, QAction]:
    return {action.text(): action for action in window.findChildren(QAction)}


def test_main_menu_builder_creates_expected_actions(qapp, tmp_path):
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    window = QMainWindow()
    calls: list[str] = []
    rotations: list[int] = []
    flips: list[bool] = []
    opened_recent: list[str] = []
    missing_recent: list[str] = []
    preview_modes: list[PreviewMode] = []

    recent_menu = build_main_menu(
        window,
        window.menuBar(),
        RecentFiles(QSettings("BgRemover", "BgRemover")),
        MainMenuCallbacks(
            open_image=lambda: calls.append("open"),
            open_recent_path=opened_recent.append,
            recent_path_missing=missing_recent.append,
            save=lambda: calls.append("save"),
            save_as=lambda: calls.append("save_as"),
            new_project=lambda: calls.append("new_project"),
            open_project=lambda: calls.append("open_project"),
            save_project=lambda: calls.append("save_project"),
            save_project_as=lambda: calls.append("save_project_as"),
            export_eufymake=lambda: calls.append("export_eufymake"),
            undo=lambda: calls.append("undo"),
            redo=lambda: calls.append("redo"),
            rotate=rotations.append,
            flip=flips.append,
            resize=lambda: calls.append("resize"),
            clear_selection=lambda: calls.append("clear"),
            invert_selection=lambda: calls.append("invert"),
            restore_original=lambda: calls.append("restore"),
            fit_to_view=lambda: calls.append("fit"),
            set_preview_mode=preview_modes.append,
            toggle_light_mode=lambda light: calls.append(f"theme:{light}"),
            open_settings=lambda: calls.append("settings"),
        ),
    )

    assert isinstance(recent_menu, RecentFilesMenu)
    assert [action.text() for action in window.menuBar().actions()] == [
        "Datei", "Projekt", "Bearbeiten", "Ansicht", "Extras",
    ]

    actions = _actions(window)
    expected = {
        "Öffnen…", "Speichern", "Speichern unter…",
        "Neues Projekt", "Projekt öffnen…", "Projekt speichern",
        "Projekt speichern unter…", "Assets für EufyMake Studio exportieren…",
        "Rückgängig", "Wiederherstellen",
        "90° links drehen", "90° rechts drehen", "180° drehen",
        "Horizontal spiegeln", "Vertikal spiegeln", "Größe ändern…",
        "Auswahl aufheben", "Auswahl invertieren",
        "Original wiederherstellen", "Fit to View", "Einstellungen…",
        "Farbe", "Relief über Farbe", "Höhe (Graustufe)", "Gloss", "Kombiniert",
    }
    assert expected <= set(actions)
    assert _portable_shortcut(actions["Öffnen…"]) == "Ctrl+O"
    assert _portable_shortcut(actions["Größe ändern…"]) == "Ctrl+R"
    assert _portable_shortcut(actions["Speichern unter…"]) == "Ctrl+Shift+S"
    assert _portable_shortcut(actions["Fit to View"]) == "Ctrl+0"
    assert _portable_shortcut(actions["Auswahl aufheben"]) == ""
    # Projekt-Aktionen mit eigenen, dokumentierten Kürzeln.
    assert _portable_shortcut(actions["Neues Projekt"]) == "Ctrl+N"
    assert _portable_shortcut(actions["Projekt öffnen…"]) == "Ctrl+Shift+O"
    assert _portable_shortcut(actions["Projekt speichern"]) == "Ctrl+Alt+S"
    assert _portable_shortcut(actions["Projekt speichern unter…"]) == "Ctrl+Alt+Shift+S"
    assert _portable_shortcut(
        actions["Assets für EufyMake Studio exportieren…"]) == "Ctrl+Alt+E"

    actions["Öffnen…"].trigger()
    actions["Speichern"].trigger()
    actions["Speichern unter…"].trigger()
    actions["Rückgängig"].trigger()
    actions["Wiederherstellen"].trigger()
    actions["Auswahl aufheben"].trigger()
    actions["Auswahl invertieren"].trigger()
    actions["Original wiederherstellen"].trigger()
    actions["Fit to View"].trigger()
    actions["Einstellungen…"].trigger()
    actions["Relief über Farbe"].trigger()
    actions["Kombiniert"].trigger()

    actions["Neues Projekt"].trigger()
    actions["Projekt öffnen…"].trigger()
    actions["Projekt speichern"].trigger()
    actions["Projekt speichern unter…"].trigger()
    actions["Assets für EufyMake Studio exportieren…"].trigger()

    actions["90° links drehen"].trigger()
    actions["90° rechts drehen"].trigger()
    actions["180° drehen"].trigger()
    actions["Horizontal spiegeln"].trigger()
    actions["Vertikal spiegeln"].trigger()
    actions["Größe ändern…"].trigger()

    assert calls == [
        "open", "save", "save_as", "undo", "redo",
        "clear", "invert", "restore", "fit", "settings",
        "new_project", "open_project", "save_project", "save_project_as",
        "export_eufymake",
        "resize",
    ]
    assert rotations == [90, -90, 180]
    assert flips == [True, False]
    assert preview_modes == [PreviewMode.RELIEF, PreviewMode.COMBINED]
    assert actions["Kombiniert"].isChecked()
    assert not actions["Relief über Farbe"].isChecked()
    assert opened_recent == []
    assert missing_recent == []
