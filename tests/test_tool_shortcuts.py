"""Tests for main-window tool shortcut wiring.

Seit der kontextuellen Werkzeugleiste (#422) sind die Kürzel W/B/E/L an den
Schritt „Freistellen" gebunden: außerhalb davon sind die QShortcuts
deaktiviert (deaktivierte Shortcuts feuern in Qt nicht) – das Kürzel greift
nur, wenn das Werkzeug im aktuellen Schritt verfügbar ist.
"""
from __future__ import annotations

import pytest
from PIL import Image
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QKeySequence, QShortcut

from bgremover import TOOL_BRUSH, TOOL_ERASER, TOOL_LASSO, TOOL_WAND, MainWindow
from bgremover.stepper import WorkflowStep


def _portable_shortcut(shortcut: QShortcut) -> str:
    return shortcut.key().toString(QKeySequence.SequenceFormat.PortableText)


def _shortcut_by_key(window: MainWindow) -> dict[str, QShortcut]:
    return {
        _portable_shortcut(shortcut): shortcut
        for shortcut in window.findChildren(QShortcut)
    }


@pytest.fixture
def window(qapp, qtbot, tmp_path, monkeypatch) -> MainWindow:
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    monkeypatch.setattr(MainWindow, "_start_rembg_warmup", lambda self: None)
    win = MainWindow()
    qtbot.addWidget(win)
    return win


def _load_image(win: MainWindow) -> None:
    """Lädt ein Mini-Bild → Schritte frei, aktiver Schritt „Freistellen"."""
    win._canvas.apply_loaded_image(Image.new("RGBA", (16, 16), (10, 20, 30, 255)), "x.png")


def test_tool_shortcuts_switch_canvas_tool_and_toolbar_state(window) -> None:
    _load_image(window)  # Kürzel greifen nur im Schritt „Freistellen" (#422)

    shortcuts = _shortcut_by_key(window)
    assert {"W", "B", "E", "L"} <= set(shortcuts)

    cases = (
        ("B", TOOL_BRUSH, "btn_brush"),
        ("E", TOOL_ERASER, "btn_eraser"),
        ("L", TOOL_LASSO, "btn_lasso"),
        ("W", TOOL_WAND, "btn_wand"),
    )
    for key, tool, button_attr in cases:
        shortcuts[key].activated.emit()
        assert window._canvas.current_tool == tool
        assert getattr(window.toolbar, button_attr).isChecked()


def test_tool_shortcuts_disabled_without_image(window) -> None:
    """Ohne Bild (Schritt „Öffnen") sind die Werkzeug-Kürzel deaktiviert."""
    assert window._step is WorkflowStep.OPEN
    shortcuts = _shortcut_by_key(window)
    for key in ("W", "B", "E", "L"):
        assert not shortcuts[key].isEnabled(), key


def test_tool_shortcuts_follow_step_availability(window) -> None:
    """Kürzel nur im Schritt „Freistellen" aktiv – wie die Werkzeug-Buttons (#422)."""
    _load_image(window)  # → Schritt „Freistellen"
    shortcuts = _shortcut_by_key(window)
    tool_keys = ("W", "B", "E", "L")
    assert all(shortcuts[k].isEnabled() for k in tool_keys)

    window._go_to_step(WorkflowStep.ADJUST)
    assert all(not shortcuts[k].isEnabled() for k in tool_keys)

    window._go_to_step(WorkflowStep.CUTOUT)
    assert all(shortcuts[k].isEnabled() for k in tool_keys)
