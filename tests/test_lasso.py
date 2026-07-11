"""Tests für ``CanvasLasso`` – Polygon-Lasso-Zustand und Vorschau-Overlays.

Geprüft werden die reinen Zustandsübergänge (Punkte sammeln, Modifikatoren,
Vorschaulinie, Duplikat-Verwerfung beim Doppelklick) sowie das Schließen
des Polygons zu einer Bitmaske. Die Overlay-Items leben in einer echten
``QGraphicsScene``; Pixel werden nicht inspiziert, nur der Modellzustand.
"""
from __future__ import annotations

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsScene

from bgremover.canvas_lasso import CanvasLasso


def _line_items(scene: QGraphicsScene) -> list[QGraphicsLineItem]:
    return [it for it in scene.items() if isinstance(it, QGraphicsLineItem)]


def _lasso(qapp) -> CanvasLasso:
    return CanvasLasso(QGraphicsScene())


# ── Anfangszustand ─────────────────────────────────────────────────────

def test_initial_state_is_empty(qapp):
    lasso = _lasso(qapp)
    assert lasso.has_points is False
    assert lasso.point_count == 0
    assert lasso.points == []
    assert lasso.modifiers == Qt.KeyboardModifier.NoModifier


# ── add_point ──────────────────────────────────────────────────────────

def test_add_point_tracks_state_and_creates_overlay(qapp):
    scene = QGraphicsScene()
    lasso = CanvasLasso(scene)
    assert scene.items() == []
    msg = lasso.add_point(10, 20)
    assert lasso.has_points is True
    assert lasso.point_count == 1
    assert lasso.points == [(10, 20)]
    # Erster Punkt → Singular ohne "e".
    assert "1 Punkt " in msg
    # Overlay-Items wurden der Szene hinzugefügt.
    assert scene.items() != []


def test_add_point_multiple_uses_plural_and_appends(qapp):
    lasso = _lasso(qapp)
    lasso.add_point(0, 0)
    msg = lasso.add_point(5, 5)
    assert lasso.point_count == 2
    assert lasso.points == [(0, 0), (5, 5)]
    assert "2 Punkte" in msg


def test_add_point_reuses_overlay_items(qapp):
    """Ab dem zweiten Punkt dürfen keine weiteren Items entstehen – die
    vorhandenen Overlay-Items werden wiederverwendet statt neu erzeugt."""
    scene = QGraphicsScene()
    lasso = CanvasLasso(scene)
    lasso.add_point(0, 0)
    items_after_first_point = list(scene.items())
    lasso.add_point(10, 0)
    lasso.add_point(10, 10)
    assert list(scene.items()) == items_after_first_point


# ── Modifikatoren ──────────────────────────────────────────────────────

def test_set_modifiers_if_first_sets_only_on_empty(qapp):
    lasso = _lasso(qapp)
    lasso.set_modifiers_if_first(Qt.KeyboardModifier.ShiftModifier)
    assert lasso.modifiers == Qt.KeyboardModifier.ShiftModifier
    # Nach dem ersten Punkt darf ein neuer Modifikator nicht mehr greifen.
    lasso.add_point(1, 1)
    lasso.set_modifiers_if_first(Qt.KeyboardModifier.ControlModifier)
    assert lasso.modifiers == Qt.KeyboardModifier.ShiftModifier


def test_modifiers_property_setter(qapp):
    lasso = _lasso(qapp)
    lasso.modifiers = Qt.KeyboardModifier.ControlModifier
    assert lasso.modifiers == Qt.KeyboardModifier.ControlModifier


def test_points_setter_replaces_list(qapp):
    lasso = _lasso(qapp)
    lasso.points = [(1, 2), (3, 4)]
    assert lasso.points == [(1, 2), (3, 4)]
    assert lasso.point_count == 2


# ── Vorschaulinie ──────────────────────────────────────────────────────

def test_update_preview_line_without_points_is_noop(qapp):
    lasso = _lasso(qapp)
    # Kein Punkt, kein Linien-Item → darf nicht abstürzen.
    lasso.update_preview_line(5.0, 5.0)
    assert lasso.has_points is False


def test_update_preview_line_after_point(qapp):
    scene = QGraphicsScene()
    lasso = CanvasLasso(scene)
    lasso.add_point(0, 0)
    lasso.update_preview_line(50.0, 60.0)
    # Die gestrichelte Vorschaulinie geht vom letzten Punkt bis zum neuen
    # Endpunkt.
    [line_item] = _line_items(scene)
    line = line_item.line()
    assert (line.x1(), line.y1()) == (0.0, 0.0)
    assert (line.x2(), line.y2()) == (50.0, 60.0)


# ── Doppelklick-Duplikat ───────────────────────────────────────────────

def test_undo_last_point_removes_duplicate(qapp):
    lasso = _lasso(qapp)
    lasso.add_point(3, 4)
    lasso.undo_last_point_if_duplicate(3, 4)
    assert lasso.points == []


def test_undo_last_point_keeps_distinct_point(qapp):
    lasso = _lasso(qapp)
    lasso.add_point(3, 4)
    lasso.undo_last_point_if_duplicate(99, 99)
    assert lasso.points == [(3, 4)]


def test_undo_last_point_on_empty_is_noop(qapp):
    lasso = _lasso(qapp)
    lasso.undo_last_point_if_duplicate(0, 0)
    assert lasso.points == []


# ── close_to_selection_mask ────────────────────────────────────────────

def test_close_with_too_few_points_returns_empty_mask(qapp):
    lasso = _lasso(qapp)
    lasso.add_point(1, 1)
    lasso.add_point(2, 2)
    mask = lasso.close_to_selection_mask((10, 10))
    assert mask.shape == (10, 10)
    assert mask.dtype == bool
    assert not mask.any()
    # Schließen leert auch den Zustand.
    assert lasso.points == []


def test_close_with_polygon_fills_interior(qapp):
    lasso = _lasso(qapp)
    # Ein Dreieck, das die obere linke Bildhälfte abdeckt.
    for pt in [(0, 0), (9, 0), (0, 9)]:
        lasso.add_point(*pt)
    mask = lasso.close_to_selection_mask((10, 10))
    assert mask.shape == (10, 10)
    # Ecke (0,0) liegt im Polygon, gegenüberliegende Ecke (9,9) außerhalb.
    assert mask[0, 0]
    assert not mask[9, 9]
    assert mask.sum() > 0
    # Zustand ist nach dem Schließen zurückgesetzt.
    assert lasso.has_points is False


# ── cancel ─────────────────────────────────────────────────────────────

def test_cancel_clears_state_and_overlay(qapp):
    scene = QGraphicsScene()
    lasso = CanvasLasso(scene)
    lasso.modifiers = Qt.KeyboardModifier.ShiftModifier
    lasso.add_point(0, 0)
    lasso.add_point(5, 5)
    assert scene.items() != []
    lasso.cancel()
    assert lasso.points == []
    assert lasso.modifiers == Qt.KeyboardModifier.NoModifier
    assert scene.items() == []
    # Idempotent: erneuter Abbruch ohne Items darf nicht abstürzen.
    lasso.cancel()
    assert isinstance(lasso.close_to_selection_mask((4, 4)), np.ndarray)
