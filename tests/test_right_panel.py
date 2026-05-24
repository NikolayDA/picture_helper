"""Tests for the right-side panel builder without constructing MainWindow."""
from __future__ import annotations

from PyQt6.QtWidgets import QPushButton

from bgremover.right_panel import RightPanelActions, build_right_panel
from bgremover.widgets import TopIconTabWidget


def _button(panel_frame, text: str) -> QPushButton:
    for button in panel_frame.findChildren(QPushButton):
        if button.text() == text:
            return button
    raise AssertionError(f"QPushButton {text!r} nicht gefunden")


def _actions(calls: list[tuple]) -> RightPanelActions:
    return RightPanelActions(
        set_tolerance=lambda value: calls.append(("tolerance", value)),
        set_brush_size=lambda value: calls.append(("brush", value)),
        clear_selection=lambda: calls.append(("clear",)),
        invert_selection=lambda: calls.append(("invert",)),
        expand_selection=lambda value: calls.append(("expand", value)),
        shrink_selection=lambda value: calls.append(("shrink", value)),
        remove_background=lambda: calls.append(("remove",)),
        pick_color=lambda: calls.append(("pick_color",)),
        replace_background=lambda: calls.append(("replace",)),
        rotate=lambda value: calls.append(("rotate", value)),
        flip=lambda horizontal: calls.append(("flip", horizontal)),
        round_corners=lambda value: calls.append(("round", value)),
        start_crop_circle=lambda: calls.append(("crop_circle",)),
        start_crop_ratio=lambda w, h: calls.append(("crop_ratio", w, h)),
    )


def test_right_panel_builder_creates_expected_tabs(qapp):
    panel = build_right_panel(_actions([]))

    tabs = panel.frame.findChild(TopIconTabWidget)
    assert tabs is not None
    assert tabs.count() == 4
    assert [tabs.tabText(i) for i in range(tabs.count())] == [
        "Auswahl", "Hintergrund", "Drehen/Spiegeln", "Form",
    ]


def test_right_panel_controls_delegate_to_callbacks(qapp):
    calls: list[tuple] = []
    panel = build_right_panel(_actions(calls))

    panel.tolerance_slider.setValue(42)
    panel.brush_slider.setValue(55)
    panel.morph_spin.setValue(5)
    _button(panel.frame, "Auswahl aufheben").click()
    _button(panel.frame, "Auswahl invertieren").click()
    _button(panel.frame, "➕ Erweitern").click()
    _button(panel.frame, "➖ Schrumpfen").click()
    _button(panel.frame, "Entfernen (transparent)").click()
    panel.color_button.click()
    _button(panel.frame, "Farbe ersetzen").click()

    _button(panel.frame, "↺ 90° links").click()
    _button(panel.frame, "↻ 90° rechts").click()
    panel.rotation_spin.setValue(33)
    _button(panel.frame, "Winkel anwenden").click()
    _button(panel.frame, "Horizontal").click()
    _button(panel.frame, "Vertikal").click()

    panel.corner_slider.setValue(12)
    _button(panel.frame, "Ecken abrunden").click()
    _button(panel.frame, "⬤  Kreis").click()
    _button(panel.frame, "■  1 : 1").click()
    _button(panel.frame, "▬  16 : 9").click()
    _button(panel.frame, "▮  9 : 16").click()

    assert calls == [
        ("tolerance", 42),
        ("brush", 55),
        ("clear",),
        ("invert",),
        ("expand", 5),
        ("shrink", 5),
        ("remove",),
        ("pick_color",),
        ("replace",),
        ("rotate", 90),
        ("rotate", -90),
        ("rotate", 33),
        ("flip", True),
        ("flip", False),
        ("round", 12),
        ("crop_circle",),
        ("crop_ratio", 1, 1),
        ("crop_ratio", 16, 9),
        ("crop_ratio", 9, 16),
    ]
