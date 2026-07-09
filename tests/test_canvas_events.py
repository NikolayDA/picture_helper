"""Tests für die Event-Handler und Steuerlogik von ``ImageCanvas``.

Deckt die bislang dünn getesteten Pfade in ``canvas.py`` ab: Maus-,
Tastatur-, Wheel- und Drag-Handler (über synthetische Qt-Events), die
Zauberstab-Ergebnisflüsse, Tool-Einstellungen, Undo/Redo bei aktivem
Crop sowie diverse Guard-Pfade ohne geladenes Bild.

Synthetische Qt-Events sind hier bewusst kein ``ui``-Test: es wird der
Handler direkt aufgerufen und der Modellzustand geprüft (kein qtbot,
kein sichtbares Fenster) – damit zählen diese Tests in die CI-Coverage.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from PyQt6.QtCore import QEvent, QMimeData, QPoint, QPointF, Qt, QUrl
from PyQt6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDragMoveEvent,
    QKeyEvent,
    QMouseEvent,
    QWheelEvent,
)

from bgremover import TOOL_BRUSH, TOOL_ERASER, TOOL_LASSO, TOOL_WAND, ImageCanvas
from bgremover.constants import TOOL_HEIGHT_DARKEN, TOOL_HEIGHT_LIGHTEN
from bgremover.i18n import tr
from bgremover.status_messages import StatusMessages as SM

NO_MOD = Qt.KeyboardModifier.NoModifier


def _canvas(size=(20, 20), color=(10, 20, 30, 255)) -> ImageCanvas:
    c = ImageCanvas()
    c.apply_loaded_image(Image.new("RGBA", size, color), "seed.png")
    return c


def _canvas_with_mask() -> ImageCanvas:
    c = _canvas()
    mask = np.zeros((20, 20), dtype=bool)
    mask[8:12, 8:12] = True
    c._mask = mask
    return c


def _mouse(kind: QEvent.Type, x: float, y: float,
           button=Qt.MouseButton.LeftButton, buttons=None) -> QMouseEvent:
    if buttons is None:
        buttons = button
    return QMouseEvent(kind, QPointF(x, y), button, buttons, NO_MOD)


# ── _mask-Setter mit None ──────────────────────────────────────────────

def test_mask_setter_none_resets_selection(qapp):
    c = _canvas_with_mask()
    assert c._mask.any()
    c._mask = None
    # Bei geladenem Bild liefert der Getter eine leere Maske (nicht None).
    assert c._mask is not None
    assert not c._mask.any()


# ── Undo / Redo / Undo-to bei aktivem Crop ─────────────────────────────

def test_undo_with_active_crop_cancels_crop(qapp):
    c = _canvas()
    c.start_crop_ratio(1, 1)
    assert c._crop.active
    c.undo()
    assert c._crop.active is False


def test_redo_with_active_crop_is_noop(qapp):
    c = _canvas()
    c.start_crop_ratio(1, 1)
    c.redo()
    assert c._crop.active is True


def test_undo_to_with_active_crop_cancels_crop(qapp):
    c = _canvas()
    c.start_crop_ratio(1, 1)
    c.undo_to(2)
    assert c._crop.active is False


def test_undo_to_with_nothing_to_undo_is_noop(qapp):
    c = _canvas()  # frisch geladen, kein Verlauf
    before = c.image
    c.undo_to(3)
    assert c.image is before


# ── clear_selection ────────────────────────────────────────────────────

def test_clear_selection_empties_mask(qapp):
    c = _canvas_with_mask()
    assert c._mask.any()
    c.clear_selection()
    assert not c._mask.any()


# ── set_tool / set_tolerance / set_brush_size ──────────────────────────

def test_set_tool_lasso_to_other_cancels_lasso(qapp):
    c = _canvas()
    c.set_tool(TOOL_LASSO)
    c._lasso.add_point(1, 1)
    assert c._lasso.has_points
    c.set_tool(TOOL_WAND)
    assert c._lasso.points == []


def test_set_tool_lasso_activates_lasso(qapp):
    c = _canvas()
    c.set_tool(TOOL_LASSO)
    assert c.current_tool == TOOL_LASSO
    assert not c._brush_preview.isVisible()


def test_set_tool_unknown_uses_arrow_fallback(qapp):
    c = _canvas()
    c.set_tool("nonexistent-tool")  # else-Zweig: Arrow-Cursor
    assert c.current_tool == "nonexistent-tool"
    assert not c._brush_preview.isVisible()


def test_set_tolerance_stores_value(qapp):
    c = _canvas()
    c.set_tolerance(42)
    assert c._tolerance == 42


def test_set_brush_size_updates_radius_for_brush(qapp):
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c.set_brush_size(20)
    assert c._brush_r == 10


def test_set_brush_size_updates_radius_for_eraser(qapp):
    c = _canvas()
    c.set_tool(TOOL_ERASER)
    c.set_brush_size(16)
    assert c._brush_r == 8


# ── apply_remove / apply_replace Guard-Pfade ───────────────────────────

def test_apply_remove_without_image_reports_status(qapp):
    c = ImageCanvas()
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c.apply_remove()
    assert SM.KEIN_BILD_GELADEN in msgs


def test_apply_remove_without_selection_reports_status(qapp):
    c = _canvas()  # Bild, aber keine Auswahl
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c.apply_remove()
    assert SM.KEINE_AUSWAHL in msgs


# ── apply_ai_result ────────────────────────────────────────────────────

def test_apply_ai_result_replaces_image(qapp):
    c = _canvas()
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c.apply_ai_result(Image.new("RGBA", (5, 5), (9, 9, 9, 255)))
    assert c.image is not None and c.image.size == (5, 5)
    # Locale-unabhaengig: gegen denselben tr()-Schluessel pruefen, den
    # apply_ai_result emittiert (Substring "KI" war DE-only und brach im EN-CI).
    assert tr("canvas.ai_done") in msgs


# ── Zauberstab-Ergebnis ────────────────────────────────────────────────

def test_apply_wand_result_applies_when_revision_matches(qapp):
    c = _canvas()
    c._handle_tool_press(5, 5, NO_MOD)  # setzt _wand_busy + Revision
    assert c.wand_busy
    mask = np.zeros((20, 20), dtype=bool)
    mask[1:3, 1:3] = True
    c.apply_wand_result(mask)
    assert c.wand_busy is False
    assert c._mask[1, 1]


def test_apply_wand_result_discarded_when_stale(qapp):
    c = _canvas()
    c._handle_tool_press(5, 5, NO_MOD)
    # Bild zwischenzeitlich verändert → Revision springt weiter.
    c.apply_edit(Image.new("RGBA", (20, 20), (1, 1, 1, 255)), desc="x")
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c.apply_wand_result(np.ones((20, 20), dtype=bool))
    assert c.wand_busy is False
    assert SM.WAND_VERWORFEN in msgs


def test_apply_wand_result_ignored_when_not_busy(qapp):
    c = _canvas()
    c.apply_wand_result(np.ones((20, 20), dtype=bool))  # nie gestartet
    assert c.wand_busy is False
    assert not c._mask.any()


def test_cancel_pending_wand_when_busy(qapp):
    c = _canvas()
    c._wand_busy = True
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c.cancel_pending_wand("Worker kaputt")
    assert c.wand_busy is False
    assert any("Worker kaputt" in m for m in msgs)


def test_cancel_pending_wand_when_idle_is_noop(qapp):
    c = _canvas()
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c.cancel_pending_wand("ignoriert")
    assert c.wand_busy is False
    assert msgs == []


def test_reset_pending_wand_clears_gate_silently(qapp):
    """Stiller Gate-Reset für den Ladepfad: gibt ``_wand_busy`` frei, ohne
    die (hier irreführende) „Auswahl-Fehler"-Meldung von
    ``cancel_pending_wand`` zu senden.
    """
    c = _canvas()
    c._wand_busy = True
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c.reset_pending_wand()
    assert c.wand_busy is False
    assert msgs == []


def test_reset_pending_wand_when_idle_is_noop(qapp):
    c = _canvas()
    c.reset_pending_wand()
    assert c.wand_busy is False


def test_apply_loaded_image_resets_pending_wand(qapp):
    """Bildwechsel während laufender Zauberstab-Berechnung darf das
    ``_wand_busy``-Gate nicht hängen lassen – sonst bliebe der Zauberstab auf
    dem neuen Bild blockiert, bis der alte Worker fertig ist. Ein verspätet
    eintreffendes Ergebnis des alten Workers wird sauber ignoriert.
    """
    c = _canvas()
    c._handle_tool_press(5, 5, NO_MOD)   # setzt _wand_busy
    assert c.wand_busy
    c.apply_loaded_image(Image.new("RGBA", (20, 20), (9, 9, 9, 255)), "neu.png")
    assert c.wand_busy is False
    # Verspätetes Ergebnis des alten Workers: dank _wand_busy-Guard ignoriert.
    c.apply_wand_result(np.ones((20, 20), dtype=bool))
    assert not c._mask.any()


def test_restore_original_resets_pending_wand(qapp):
    """Auch ``restore_original`` läuft durch ``_reset_transient_state`` und
    muss ein hängendes ``_wand_busy`` lösen."""
    c = _canvas()
    c.apply_edit(Image.new("RGBA", (20, 20), (5, 5, 5, 255)), desc="edit")
    c._handle_tool_press(5, 5, NO_MOD)
    assert c.wand_busy
    c.restore_original()
    assert c.wand_busy is False


# ── _handle_tool_press ─────────────────────────────────────────────────

def test_handle_tool_press_wand_in_bounds_starts_request(qapp):
    c = _canvas()
    requests: list[tuple] = []
    c.wandRequested.connect(lambda *a: requests.append(a))
    c._handle_tool_press(5, 5, NO_MOD)
    assert c.wand_busy is True
    assert len(requests) == 1


def test_handle_tool_press_wand_busy_reports_status(qapp):
    c = _canvas()
    c._wand_busy = True
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c._handle_tool_press(5, 5, NO_MOD)
    assert SM.ZAUBERSTAB_ARBEITET in msgs


def test_handle_tool_press_wand_out_of_bounds_does_nothing(qapp):
    c = _canvas()
    c._handle_tool_press(999, 999, NO_MOD)
    assert c.wand_busy is False


def test_handle_tool_press_lasso_adds_point(qapp):
    c = _canvas()
    c.set_tool(TOOL_LASSO)
    c._handle_tool_press(5, 5, NO_MOD)
    assert c._lasso.points == [(5, 5)]


def test_handle_tool_press_brush_starts_drawing(qapp):
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c._handle_tool_press(10, 10, NO_MOD)
    assert c._drawing is True


# ── _lasso_close / _paint_brush Guards ─────────────────────────────────

def test_lasso_close_without_image_is_noop(qapp):
    c = ImageCanvas()
    c._lasso.add_point(4, 5)
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)

    c._lasso_close()

    assert c.image is None
    assert c._lasso.points == [(4, 5)]
    assert msgs == []


def test_paint_brush_without_image_is_noop(qapp, monkeypatch):
    c = ImageCanvas()
    painted: list[tuple[int, int, bool]] = []
    monkeypatch.setattr(
        c._selection,
        "paint_brush",
        lambda x, y, *, additive: painted.append((x, y, additive)),
    )

    c._paint_brush(0, 0, additive=True)

    assert c.image is None
    assert painted == []


# ── Maus-Events (synthetische QMouseEvents) ────────────────────────────

def test_mouse_press_without_image_is_ignored(qapp):
    c = ImageCanvas()
    c.mousePressEvent(_mouse(QEvent.Type.MouseButtonPress, 5, 5))
    assert c.image is None


def test_mouse_press_brush_starts_drawing(qapp):
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c.mousePressEvent(_mouse(QEvent.Type.MouseButtonPress, 5, 5))
    assert c._drawing is True


def test_mouse_move_shows_brush_preview(qapp):
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, 8, 8,
                            button=Qt.MouseButton.NoButton))
    assert c._brush_preview.isVisible()


def test_mouse_move_while_drawing_paints(qapp, monkeypatch):
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c._drawing = True
    painted: list[bool] = []
    monkeypatch.setattr(c, "_paint_brush",
                        lambda *a, **k: painted.append(True))
    c.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, 8, 8,
                            button=Qt.MouseButton.LeftButton))
    assert painted == [True]


def test_mouse_release_stops_drawing(qapp):
    c = _canvas()
    c._drawing = True
    c.mouseReleaseEvent(_mouse(QEvent.Type.MouseButtonRelease, 5, 5,
                               button=Qt.MouseButton.LeftButton,
                               buttons=Qt.MouseButton.NoButton))
    assert c._drawing is False


def test_double_click_closes_lasso_polygon(qapp):
    c = _canvas()
    c.set_tool(TOOL_LASSO)
    for pt in [(2, 2), (16, 2), (16, 16), (2, 16)]:
        c._lasso.add_point(*pt)
    c.mouseDoubleClickEvent(
        _mouse(QEvent.Type.MouseButtonDblClick, 9, 9))
    # Mit >= 3 Punkten wird das Polygon geschlossen → Punkte geleert.
    assert c._lasso.points == []
    assert c._mask is not None and c._mask.any()


def test_double_click_with_few_points_cancels_lasso(qapp):
    c = _canvas()
    c.set_tool(TOOL_LASSO)
    c._lasso.add_point(2, 2)
    c._lasso.add_point(16, 2)
    c.mouseDoubleClickEvent(
        _mouse(QEvent.Type.MouseButtonDblClick, 18, 18))
    # < 3 Punkte → Abbruch.
    assert c._lasso.points == []


def test_escape_cancels_active_lasso(qapp):
    c = _canvas()
    c.set_tool(TOOL_LASSO)
    c._lasso.add_point(3, 3)
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, NO_MOD))
    assert c._lasso.points == []
    assert any("abgebrochen" in m for m in msgs)


def test_cancel_active_interaction_prioritizes_crop_then_lasso(qapp):
    c = _canvas_with_mask()
    c.set_tool(TOOL_LASSO)
    c._lasso.add_point(3, 3)
    c.start_crop_ratio(1, 1)
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)

    assert c.cancel_active_interaction() is True
    assert c._crop.active is False
    assert c._lasso.points == [(3, 3)]
    assert c._mask.any()
    assert msgs[-1] == tr("canvas.crop_cancelled")

    assert c.cancel_active_interaction() is True
    assert c._lasso.points == []
    assert c._mask.any()
    assert msgs[-1] == tr("canvas.lasso_cancelled")

    assert c.cancel_active_interaction() is False


def test_leave_event_hides_brush_preview(qapp):
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c._update_brush_preview(QPointF(5, 5))
    assert c._brush_preview.isVisible()
    c.leaveEvent(QEvent(QEvent.Type.Leave))
    assert not c._brush_preview.isVisible()


# ── Drag-Events ────────────────────────────────────────────────────────

def test_drag_enter_accepts_image_urls(qapp):
    c = ImageCanvas()
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile("/tmp/x.png")])
    ev = QDragEnterEvent(QPoint(1, 1), Qt.DropAction.CopyAction, mime,
                         Qt.MouseButton.LeftButton, NO_MOD)
    c.dragEnterEvent(ev)
    assert ev.isAccepted()


def test_drag_move_accepts_image_urls(qapp):
    c = ImageCanvas()
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile("/tmp/x.png")])
    ev = QDragMoveEvent(QPoint(1, 1), Qt.DropAction.CopyAction, mime,
                        Qt.MouseButton.LeftButton, NO_MOD,
                        QEvent.Type.DragMove)
    c.dragMoveEvent(ev)
    assert ev.isAccepted()


def test_drag_enter_none_is_noop(qapp):
    c = ImageCanvas()
    requested: list[str] = []
    c.loadRequested.connect(requested.append)

    c.dragEnterEvent(None)

    assert requested == []
    assert c.image is None


def test_drop_none_is_noop(qapp):
    c = ImageCanvas()
    requested: list[str] = []
    msgs: list[str] = []
    c.loadRequested.connect(requested.append)
    c.statusMsg.connect(msgs.append)

    c.dropEvent(None)

    assert requested == []
    assert msgs == []
    assert c.image is None


def test_drag_enter_without_urls_is_not_accepted(qapp):
    c = ImageCanvas()
    mime = QMimeData()  # keine URLs
    ev = QDragEnterEvent(QPoint(1, 1), Qt.DropAction.CopyAction, mime,
                         Qt.MouseButton.LeftButton, NO_MOD)
    c.dragEnterEvent(ev)
    assert not ev.isAccepted()


# ── Maus-Routing: Crop- und Pan-Pfade ──────────────────────────────────

def test_mouse_press_with_active_crop_is_consumed(qapp):
    """Bei aktivem Crop konsumiert das Overlay den Press – das Werkzeug
    (hier Pinsel) darf NICHT mit dem Zeichnen beginnen."""
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c.start_crop_ratio(1, 1)
    c.mousePressEvent(_mouse(QEvent.Type.MouseButtonPress, 5, 5))
    assert c._drawing is False


def test_mouse_press_middle_button_starts_pan(qapp):
    c = _canvas()
    c.mousePressEvent(_mouse(QEvent.Type.MouseButtonPress, 5, 5,
                             button=Qt.MouseButton.MiddleButton))
    assert c._viewport.is_panning is True


def test_mouse_press_right_button_does_not_draw(qapp):
    c = _canvas()
    c.set_tool(TOOL_BRUSH)
    c.mousePressEvent(_mouse(QEvent.Type.MouseButtonPress, 5, 5,
                             button=Qt.MouseButton.RightButton))
    assert c._drawing is False


def test_mouse_move_while_panning_updates_pan(qapp, monkeypatch):
    c = _canvas()
    c._viewport.start_pan_if_requested(
        Qt.MouseButton.MiddleButton, NO_MOD, QPointF(5, 5))
    assert c._viewport.is_panning
    panned: list[object] = []
    monkeypatch.setattr(c._viewport, "update_pan",
                        lambda pos: panned.append(pos))
    c.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, 10, 12,
                            button=Qt.MouseButton.NoButton))
    assert panned  # update_pan wurde aufgerufen


def test_mouse_move_with_active_crop_is_consumed(qapp):
    c = _canvas()
    c.start_crop_ratio(1, 1)
    c.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, 8, 8,
                            button=Qt.MouseButton.NoButton))
    assert c._crop.active is True  # Crop verarbeitet das Move


def test_mouse_release_while_panning_stops_pan(qapp):
    c = _canvas()
    c._viewport.start_pan_if_requested(
        Qt.MouseButton.MiddleButton, NO_MOD, QPointF(5, 5))
    c.mouseReleaseEvent(_mouse(QEvent.Type.MouseButtonRelease, 5, 5,
                               button=Qt.MouseButton.NoButton))
    assert c._viewport.is_panning is False


def test_mouse_release_with_active_crop_is_consumed(qapp):
    c = _canvas()
    c.start_crop_ratio(1, 1)
    ov = c._crop.overlay
    assert ov is not None
    tl = ov._corners()[0]
    c._crop.handle_press(Qt.MouseButton.LeftButton, QPointF(tl.x(), tl.y()))
    assert c._crop.is_resizing
    c.mouseReleaseEvent(_mouse(QEvent.Type.MouseButtonRelease, 5, 5))
    assert c._crop.is_resizing is False


def test_double_click_non_lasso_passes_through(qapp):
    c = _canvas()  # Standard-Tool ist Zauberstab, kein Lasso
    c.mouseDoubleClickEvent(_mouse(QEvent.Type.MouseButtonDblClick, 5, 5))
    assert c.current_tool == TOOL_WAND  # kein Crash, Tool unverändert


def test_key_press_non_escape_passes_through(qapp):
    c = _canvas()
    c.set_tool(TOOL_LASSO)
    c._lasso.add_point(3, 3)
    # Eine andere Taste darf das Lasso NICHT abbrechen.
    c.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, NO_MOD))
    assert c._lasso.points == [(3, 3)]


# ── Wheel-Zoom ─────────────────────────────────────────────────────────

def test_wheel_event_zooms_in(qapp):
    c = _canvas()
    before = c.transform().m11()
    ev = QWheelEvent(QPointF(5, 5), QPointF(5, 5), QPoint(0, 0), QPoint(0, 120),
                     Qt.MouseButton.NoButton, NO_MOD,
                     Qt.ScrollPhase.NoScrollPhase, False)
    c.wheelEvent(ev)
    assert c.transform().m11() > before


# ── Sonstige Delegatoren / Guards ──────────────────────────────────────

def test_fit_to_view_delegates_to_viewport(qapp, monkeypatch):
    c = _canvas()
    calls: list[bool] = []
    monkeypatch.setattr(c._viewport, "fit_to_view", lambda: calls.append(True))

    c.fit_to_view()

    assert calls == [True]


def test_apply_replace_without_selection_reports_status(qapp):
    c = _canvas()
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c.apply_replace(QColor(255, 0, 0))
    assert SM.KEINE_AUSWAHL in msgs


def test_mouse_move_with_lasso_updates_preview_line(qapp, monkeypatch):
    c = _canvas()
    c.set_tool(TOOL_LASSO)
    c._handle_tool_press(5, 5, NO_MOD)  # erster Punkt → Linien-Item existiert
    updated: list[tuple] = []
    monkeypatch.setattr(c._lasso, "update_preview_line",
                        lambda x, y: updated.append((x, y)))
    c.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, 12, 14,
                            button=Qt.MouseButton.NoButton))
    assert updated  # Vorschaulinie wurde nachgeführt


def test_set_brush_size_with_wand_updates_radius_only(qapp):
    c = _canvas()  # Standard-Tool: Zauberstab
    c.set_brush_size(20)
    assert c._brush_r == 10  # Radius gesetzt, kein Cursor-Zweig


def test_drag_move_without_urls_is_not_accepted(qapp):
    c = ImageCanvas()
    mime = QMimeData()  # keine URLs
    ev = QDragMoveEvent(QPoint(1, 1), Qt.DropAction.CopyAction, mime,
                        Qt.MouseButton.LeftButton, NO_MOD,
                        QEvent.Type.DragMove)
    c.dragMoveEvent(ev)
    assert not ev.isAccepted()


# ── Zoom-bewusster Pinsel-Cursor (#509) ───────────────────────────────

# Cursor-Bitmap: Bildschirm-Durchmesser + 2×6 px Innenabstand der Fabriken.
_CURSOR_PAD = 12


def test_brush_cursor_matches_zoom_at_tool_selection(qapp):
    """Cursorgröße = Pinseldurchmesser (Bildpixel) × View-Zoom, je Werkzeug."""
    c = _canvas()
    c.set_brush_size(100)  # _brush_r = 50 → 100 Bildpixel Durchmesser
    for tool in (TOOL_BRUSH, TOOL_ERASER, TOOL_HEIGHT_LIGHTEN, TOOL_HEIGHT_DARKEN):
        for scale, expected in ((0.25, 25), (0.5, 50), (1.0, 100), (2.0, 200)):
            c.resetTransform()
            c.scale(scale, scale)
            c.set_tool(tool)
            pm = c.cursor().pixmap()
            assert pm.width() == expected + _CURSOR_PAD, (tool, scale)
            assert pm.height() == expected + _CURSOR_PAD, (tool, scale)


def test_zoom_change_updates_active_brush_cursor(qapp):
    """Zoomwechsel bei aktivem Werkzeug erneuert den Cursor sofort (#509)."""
    c = _canvas()
    c.set_brush_size(100)
    for tool in (TOOL_BRUSH, TOOL_ERASER, TOOL_HEIGHT_LIGHTEN, TOOL_HEIGHT_DARKEN):
        c.resetTransform()  # 100 %
        c.set_tool(tool)
        assert c.cursor().pixmap().width() == 100 + _CURSOR_PAD
        c._viewport.zoom(0.5)  # Mausrad-/API-Pfad → zoomChanged
        assert c.cursor().pixmap().width() == 50 + _CURSOR_PAD, tool


def test_zoom_control_step_updates_active_brush_cursor(qapp):
    """Auch der Zoom-Kontroll-Pfad (step_zoom) erneuert den Cursor."""
    c = _canvas()
    c.set_brush_size(100)
    c.resetTransform()
    c._viewport.zoom(0.5)  # 50 %
    c.set_tool(TOOL_BRUSH)
    assert c.cursor().pixmap().width() == 50 + _CURSOR_PAD
    c._viewport.step_zoom(10)  # 50 % → 60 %
    assert c.cursor().pixmap().width() == 60 + _CURSOR_PAD


def test_oversized_brush_cursor_falls_back_to_crosshair(qapp):
    """Oberhalb der Bitmap-Grenze zeigt ein Fadenkreuz; die Ellipse trägt die Größe."""
    from bgremover.constants import BRUSH_CURSOR_MAX_SCREEN_PX

    c = _canvas()
    c.set_brush_size(200)  # 200 Bildpixel Durchmesser
    c.resetTransform()
    c.scale(2.0, 2.0)  # 400 Bildschirmpixel > 256
    assert BRUSH_CURSOR_MAX_SCREEN_PX < 200 * 2
    c.set_tool(TOOL_BRUSH)
    assert c.cursor().shape() == Qt.CursorShape.CrossCursor
    # Zurück unter die Grenze: wieder exakter Bitmap-Cursor.
    c._viewport.zoom(0.5)  # 200 % → 100 %
    assert c.cursor().pixmap().width() == 200 + _CURSOR_PAD


def test_tiny_zoom_keeps_brush_cursor_visible(qapp):
    """Weit herausgezoomt greift der 6-px-Sichtbarkeitsboden der Cursor-Fabrik."""
    c = _canvas()
    c.set_brush_size(30)  # Standardgröße, _brush_r = 15
    c.resetTransform()
    c.scale(0.1, 0.1)  # 3 Bildschirmpixel → Boden 6
    c.set_tool(TOOL_BRUSH)
    assert c.cursor().pixmap().width() == 6 + _CURSOR_PAD
