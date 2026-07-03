"""Tests für die malenden Höhen-Werkzeuge der Rail (#457).

Canvas-Ebene, headless: Strichstart/-fortsetzung/-abschluss werden direkt
über die (privaten) Strich-Methoden getrieben – analog zu den
``test_viewport``-Tests ohne sichtbares Fenster.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from bgremover import ImageCanvas
from bgremover.constants import (
    _DEFAULT_HEIGHT_STEP,
    TOOL_HEIGHT_DARKEN,
    TOOL_HEIGHT_LIGHTEN,
)
from bgremover.height_map import layer_to_height
from bgremover.i18n import tr
from bgremover.project_model import LayerKind


def _canvas_with_height_layer(gray: int = 100, size=(16, 16)) -> ImageCanvas:
    """Canvas mit Bild + aktiver HEIGHT-Ebene konstanter Höhe *gray*."""
    c = ImageCanvas()
    c.apply_loaded_image(
        Image.new("RGBA", size, (gray, gray, gray, 255)), "seed.png")
    c.generate_height_map()
    active = c.project.active_layer()
    assert active is not None and active.kind is LayerKind.HEIGHT
    return c


def _stroke(canvas: ImageCanvas, points: list[tuple[int, int]]) -> None:
    """Simuliert einen Malstrich: Press auf dem ersten Punkt, Move, Release."""
    first, *rest = points
    canvas._start_height_stroke(*first)
    for point in rest:
        canvas._extend_height_stroke(*point)
    canvas._finish_height_stroke()


def test_lighten_stroke_raises_height_by_step(qapp):
    c = _canvas_with_height_layer(gray=100)
    c.set_tool(TOOL_HEIGHT_LIGHTEN)
    c.set_brush_size(6)  # Radius 3
    before = layer_to_height(c.image).values.copy()

    _stroke(c, [(8, 8)])

    after = layer_to_height(c.image).values
    assert after[8, 8] == before[8, 8] + _DEFAULT_HEIGHT_STEP
    # Außerhalb des Pinselkreises bleibt die Höhe unverändert.
    assert after[0, 0] == before[0, 0]


def test_darken_stroke_lowers_height_clamped(qapp):
    c = _canvas_with_height_layer(gray=10)  # nahe der Untergrenze
    c.set_tool(TOOL_HEIGHT_DARKEN)
    c.set_brush_size(6)

    _stroke(c, [(8, 8)])

    after = layer_to_height(c.image).values
    # 10 − 32 wird auf 0 geklemmt (adjust_height-Semantik, verlustfrei).
    assert after[8, 8] == 0


def test_stroke_adjusts_each_pixel_once(qapp):
    """Überlappende Stempel innerhalb eines Strichs addieren nicht doppelt."""
    c = _canvas_with_height_layer(gray=100)
    c.set_tool(TOOL_HEIGHT_LIGHTEN)
    c.set_brush_size(6)

    _stroke(c, [(8, 8), (9, 8), (8, 8)])

    after = layer_to_height(c.image).values
    assert after[8, 8] == 100 + _DEFAULT_HEIGHT_STEP


def test_live_preview_updates_only_dirty_height_region(qapp, monkeypatch):
    """Während des Strichs wird nur das Pinsel-Rechteck als Layer gebaut."""
    import bgremover.canvas as canvas_mod

    c = _canvas_with_height_layer(gray=100, size=(64, 64))
    c.set_tool(TOOL_HEIGHT_LIGHTEN)
    c.set_brush_size(6)
    calls: list[tuple[int, int]] = []
    original = canvas_mod.height_to_layer

    def _tracking_height_to_layer(field):
        calls.append(field.values.shape)
        return original(field)

    monkeypatch.setattr(canvas_mod, "height_to_layer", _tracking_height_to_layer)
    c._start_height_stroke(8, 8)
    c._extend_height_stroke(10, 8)

    assert calls
    assert (64, 64) not in calls
    assert all(h <= 7 and w <= 7 for h, w in calls)


def test_stroke_is_single_undo_step(qapp):
    c = _canvas_with_height_layer(gray=100)
    c.set_tool(TOOL_HEIGHT_LIGHTEN)
    c.set_brush_size(6)
    depth_before = len(c._history.descriptions())

    _stroke(c, [(4, 4), (6, 4), (8, 4), (10, 4)])

    descriptions = c._history.descriptions()
    assert len(descriptions) == depth_before + 1
    assert descriptions[0] == tr("history.desc.height_lighten")

    # Undo stellt den Vor-Strich-Zustand vollständig wieder her.
    c.undo()
    restored = layer_to_height(c.image).values
    assert (restored == 100).all()


def test_stroke_on_color_layer_is_noop(qapp):
    """Auf COLOR-Ebenen wirkungslos (#364-Vertrag bleibt unangetastet)."""
    c = ImageCanvas()
    c.apply_loaded_image(
        Image.new("RGBA", (16, 16), (100, 100, 100, 255)), "seed.png")
    messages: list[str] = []
    c.statusMsg.connect(messages.append)
    c.set_tool(TOOL_HEIGHT_LIGHTEN)
    before = np.asarray(c.image).copy()
    depth_before = len(c._history.descriptions())

    c._start_height_stroke(8, 8)

    assert c._height_stroke is None
    assert (np.asarray(c.image) == before).all()
    assert len(c._history.descriptions()) == depth_before
    assert tr("canvas.not_height_layer") in messages


def test_empty_stroke_outside_image_pushes_no_history(qapp):
    c = _canvas_with_height_layer(gray=100)
    c.set_tool(TOOL_HEIGHT_DARKEN)
    c.set_brush_size(2)
    depth_before = len(c._history.descriptions())

    _stroke(c, [(500, 500)])  # komplett außerhalb

    assert len(c._history.descriptions()) == depth_before


def test_tool_gate_aborts_running_stroke(qapp):
    """`set_tools_enabled(False)` (Schrittwechsel) verwirft den Strich ohne Commit."""
    c = _canvas_with_height_layer(gray=100)
    c.set_tool(TOOL_HEIGHT_LIGHTEN)
    c.set_brush_size(6)
    depth_before = len(c._history.descriptions())
    c._start_height_stroke(8, 8)
    assert c._height_stroke is not None

    c.set_tools_enabled(False)

    assert c._height_stroke is None
    assert len(c._history.descriptions()) == depth_before
    assert layer_to_height(c.image).values[8, 8] == 100
