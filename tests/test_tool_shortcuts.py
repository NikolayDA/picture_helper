"""Tests for main-window tool shortcut wiring."""
from __future__ import annotations

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QKeySequence, QShortcut

from bgremover import TOOL_BRUSH, TOOL_ERASER, TOOL_LASSO, TOOL_WAND, MainWindow


def _portable_shortcut(shortcut: QShortcut) -> str:
    return shortcut.key().toString(QKeySequence.SequenceFormat.PortableText)


def _shortcut_by_key(window: MainWindow) -> dict[str, QShortcut]:
    return {
        _portable_shortcut(shortcut): shortcut
        for shortcut in window.findChildren(QShortcut)
    }


def test_tool_shortcuts_switch_canvas_tool_and_toolbar_state(
    qapp, qtbot, tmp_path, monkeypatch,
) -> None:
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    monkeypatch.setattr(MainWindow, "_start_rembg_warmup", lambda self: None)

    window = MainWindow()
    qtbot.addWidget(window)

    shortcuts = _shortcut_by_key(window)
    assert {"W", "B", "E", "L"} <= set(shortcuts)

    cases = (
        ("B", TOOL_BRUSH, "_btn_brush"),
        ("E", TOOL_ERASER, "_btn_eraser"),
        ("L", TOOL_LASSO, "_btn_lasso"),
        ("W", TOOL_WAND, "_btn_wand"),
    )
    for key, tool, button_attr in cases:
        shortcuts[key].activated.emit()
        assert window._canvas.current_tool == tool
        assert getattr(window, button_attr).isChecked()
