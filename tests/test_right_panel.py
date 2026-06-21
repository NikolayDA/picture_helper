"""Tests for the right-side panel builder without constructing MainWindow."""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QComboBox, QPushButton, QSlider, QWidget

from bgremover.canvas import LayerInfo
from bgremover.layer_panel import LayerPanel, LayerPanelActions
from bgremover.project_model import LayerKind, LayerRole
from bgremover.right_panel import RightPanelActions, build_right_panel
from bgremover.widgets import TopIconTabWidget


def _button(panel_frame, text: str) -> QPushButton:
    for button in panel_frame.findChildren(QPushButton):
        if button.text() == text:
            return button
    raise AssertionError(f"QPushButton {text!r} nicht gefunden")


def _noop_layer_actions() -> LayerPanelActions:
    return LayerPanelActions(
        add_layer=lambda: None,
        delete_active=lambda: None,
        duplicate_active=lambda: None,
        move_active_up=lambda: None,
        move_active_down=lambda: None,
        rename_active=lambda: None,
        set_active=lambda _lid: None,
        set_visible=lambda _lid, _v: None,
        set_opacity=lambda _lid, _o: None,
        set_active_role=lambda _r: None,
    )


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
    panel = build_right_panel(_actions([]), _noop_layer_actions())

    tabs = panel.frame.findChild(TopIconTabWidget)
    assert tabs is not None
    assert tabs.count() == 5
    assert [tabs.tabText(i) for i in range(tabs.count())] == [
        "Auswahl", "Hintergrund", "Drehen/Spiegeln", "Form", "Ebenen",
    ]


def test_right_panel_controls_delegate_to_callbacks(qapp):
    calls: list[tuple] = []
    panel = build_right_panel(_actions(calls), _noop_layer_actions())

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


# ── Ebenen-Panel (#334) ──────────────────────────────────────────────────


def _recording_layer_actions(calls: list[tuple]) -> LayerPanelActions:
    return LayerPanelActions(
        add_layer=lambda: calls.append(("add",)),
        delete_active=lambda: calls.append(("delete",)),
        duplicate_active=lambda: calls.append(("duplicate",)),
        move_active_up=lambda: calls.append(("up",)),
        move_active_down=lambda: calls.append(("down",)),
        rename_active=lambda: calls.append(("rename",)),
        set_active=lambda lid: calls.append(("active", lid)),
        set_visible=lambda lid, v: calls.append(("visible", lid, v)),
        set_opacity=lambda lid, o: calls.append(("opacity", lid, o)),
        set_active_role=lambda r: calls.append(("role", r)),
    )


def _infos() -> list[LayerInfo]:
    return [
        LayerInfo(id="top", name="Oben", kind=LayerKind.COLOR, visible=True,
                  opacity=1.0, locked=False, role=None, active=True),
        LayerInfo(id="bot", name="Unten", kind=LayerKind.COLOR, visible=True,
                  opacity=0.5, locked=False, role=LayerRole.COLOR_MOTIF, active=False),
    ]


def _row_for(widget: QWidget, name: str) -> QWidget:
    name_btn = next(
        b for b in widget.findChildren(QPushButton) if b.text() == name)
    parent = name_btn.parent()
    assert isinstance(parent, QWidget)
    return parent


@pytest.mark.ui_smoke
def test_layer_panel_action_bar_delegates(qapp):
    calls: list[tuple] = []
    panel = LayerPanel(_recording_layer_actions(calls))
    widget, _refs = panel.build()
    panel.refresh(_infos())

    for symbol, expected in (
        ("＋", "add"), ("⧉", "duplicate"), ("🗑", "delete"),
        ("▲", "up"), ("▼", "down"), ("✎", "rename"),
    ):
        _button(widget, symbol).click()
        assert calls[-1] == (expected,)


@pytest.mark.ui_smoke
def test_layer_panel_rows_reflect_and_delegate(qapp):
    calls: list[tuple] = []
    panel = LayerPanel(_recording_layer_actions(calls))
    widget, _refs = panel.build()
    panel.refresh(_infos())

    # Genau zwei Zeilen (oberste zuerst).
    assert [b.text() for b in widget.findChildren(QPushButton)
            if b.text() in ("Oben", "Unten")] == ["Oben", "Unten"]

    # Klick auf Namen wählt die aktive Ebene.
    next(b for b in widget.findChildren(QPushButton)
         if b.text() == "Unten").click()
    assert ("active", "bot") in calls

    # Sichtbarkeit der unteren Ebene umschalten.
    bot_row = _row_for(widget, "Unten")
    vis = next(b for b in bot_row.findChildren(QPushButton)
               if b.text() in ("👁", "🚫"))
    vis.setChecked(False)
    assert ("visible", "bot", False) in calls

    # Opazität der unteren Ebene anpassen (beim Loslassen übernommen).
    slider = bot_row.findChild(QSlider)
    assert slider is not None
    slider.setValue(25)
    slider.sliderReleased.emit()
    assert ("opacity", "bot", pytest.approx(0.25)) in calls


@pytest.mark.ui_smoke
def test_layer_panel_role_combo_reflects_active_and_delegates(qapp):
    calls: list[tuple] = []
    panel = LayerPanel(_recording_layer_actions(calls))
    widget, refs = panel.build()
    panel.refresh(_infos())

    combo = refs["layer_role_combo"]
    assert isinstance(combo, QComboBox)
    # Aktive Ebene „Oben" hat keine Rolle → Index 0 (Keine).
    assert combo.currentData() is None

    combo.setCurrentIndex(2)   # Height Map
    assert ("role", LayerRole.HEIGHT_MAP) in calls


@pytest.mark.ui_smoke
def test_layer_panel_empty_state_disables_actions(qapp):
    panel = LayerPanel(_noop_layer_actions())
    widget, _refs = panel.build()
    panel.refresh([])

    add = _button(widget, "＋")
    assert not add.isEnabled()
