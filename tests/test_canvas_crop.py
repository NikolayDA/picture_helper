"""Tests für ``CanvasCrop`` – Zustand und Mausgesten des Crop-Overlays.

Geprüft werden die Guard-Pfade ohne geladenes Bild, das Starten/Bestätigen
und vor allem die Maus-Gesten (Press auf Eck-Handle → Resize, Press in der
Mitte → Drag, Move/Release) über ein echtes ``ImageCanvas``. Es werden
ausschließlich Modellzustände inspiziert, keine View-Pixel.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from PyQt6.QtCore import QPointF, Qt

from bgremover import ImageCanvas
from bgremover.constants import TOOL_LASSO
from bgremover.status_messages import StatusMessages as SM


def _canvas(size=(600, 400), color=(10, 20, 30, 255)) -> ImageCanvas:
    c = ImageCanvas()
    c.apply_loaded_image(Image.new("RGBA", size, color), "seed.png")
    return c


def _canvas_with_crop(size=(600, 400)) -> ImageCanvas:
    """Canvas mit aktivem 1:1-Crop. Auf 600×400 ergibt das einen
    400×400-Rahmen, zentriert bei (100, 0) – also kleiner als das Bild,
    sodass Drag/Resize echten Spielraum haben.
    """
    c = _canvas(size=size)
    c.start_crop_ratio(1, 1)
    return c


# ── Guards ohne geladenes Bild ─────────────────────────────────────────

def test_start_circle_without_image_emits_status(qapp):
    c = ImageCanvas()
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c.start_crop_circle()
    assert c._crop.overlay is None
    assert msgs[-1] == SM.KEIN_BILD_GELADEN


def test_start_ratio_without_image_emits_status(qapp):
    c = ImageCanvas()
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c.start_crop_ratio(16, 9)
    assert c._crop.overlay is None
    assert msgs[-1] == SM.KEIN_BILD_GELADEN


def test_confirm_without_overlay_is_noop(qapp):
    c = _canvas()
    before = c.image
    c.confirm_crop()  # kein Overlay aktiv → darf nichts tun
    assert c.image is before


# ── Start ──────────────────────────────────────────────────────────────

def test_start_ratio_creates_centered_overlay(qapp):
    c = _canvas_with_crop()
    ov = c._crop.overlay
    assert ov is not None
    assert c._crop.active is True
    assert ov.size == (400.0, 400.0)
    assert ov.top_left == QPointF(100.0, 0.0)


def test_start_circle_marks_overlay_circular(qapp):
    c = _canvas()
    c.start_crop_circle()
    ov = c._crop.overlay
    assert ov is not None
    assert ov.is_circle is True


# ── Press → Resize / Drag ──────────────────────────────────────────────

def test_press_on_corner_starts_resizing(qapp):
    c = _canvas_with_crop()
    ov = c._crop.overlay
    assert ov is not None
    tl = ov._corners()[0]
    consumed = c._crop.handle_press(Qt.MouseButton.LeftButton,
                                    QPointF(tl.x(), tl.y()))
    assert consumed is True
    assert c._crop.is_resizing is True
    assert c._crop.is_dragging is False
    # Verhaltens-Check statt internem Ecken-Sentinel: Der Resize ist an der
    # gedrückten Ecke (oben links) verankert – ein Move ändert die Größe UND
    # verschiebt die linke obere Ecke mit (Drag würde nur verschieben,
    # Resize an einer anderen Ecke ließe top_left unangetastet).
    size_before, tl_before = ov.size, ov.top_left
    c._crop.handle_move(QPointF(tl.x() + 40, tl.y() + 40))
    assert ov.size != size_before
    assert ov.top_left != tl_before


def test_press_inside_starts_dragging(qapp):
    c = _canvas_with_crop()
    ov = c._crop.overlay
    assert ov is not None
    mid = QPointF(ov._cx + ov._cw / 2, ov._cy + ov._ch / 2)
    consumed = c._crop.handle_press(Qt.MouseButton.LeftButton, mid)
    assert consumed is True
    assert c._crop.is_dragging is True
    assert c._crop.is_resizing is False


def test_press_with_right_button_is_consumed_but_inert(qapp):
    """Im Crop-Modus konsumiert die Klasse alle Press-Events, startet
    aber nur bei der linken Taste Resize/Drag."""
    c = _canvas_with_crop()
    consumed = c._crop.handle_press(Qt.MouseButton.RightButton,
                                    QPointF(300.0, 200.0))
    assert consumed is True
    assert c._crop.is_dragging is False
    assert c._crop.is_resizing is False


def test_press_without_overlay_returns_false(qapp):
    c = _canvas()  # kein Crop gestartet → kein Overlay
    consumed = c._crop.handle_press(Qt.MouseButton.LeftButton,
                                    QPointF(10.0, 10.0))
    assert consumed is False


# ── Move ───────────────────────────────────────────────────────────────

def test_move_while_resizing_changes_size(qapp):
    c = _canvas_with_crop()
    ov = c._crop.overlay
    assert ov is not None
    tl = ov._corners()[0]
    c._crop.handle_press(Qt.MouseButton.LeftButton, QPointF(tl.x(), tl.y()))
    before = ov.size
    consumed = c._crop.handle_move(QPointF(tl.x() + 40, tl.y() + 40))
    assert consumed is True
    assert ov.size != before


def test_move_while_dragging_changes_position(qapp):
    c = _canvas_with_crop()
    ov = c._crop.overlay
    assert ov is not None
    mid = QPointF(ov._cx + ov._cw / 2, ov._cy + ov._ch / 2)
    c._crop.handle_press(Qt.MouseButton.LeftButton, mid)
    before = ov.top_left
    consumed = c._crop.handle_move(QPointF(mid.x() + 20, mid.y() + 10))
    assert consumed is True
    assert ov.top_left != before


def test_move_hover_is_consumed_without_drag(qapp):
    """Ein Move ohne aktiven Drag/Resize aktualisiert nur den Cursor,
    konsumiert das Event aber trotzdem (Overlay aktiv)."""
    c = _canvas_with_crop()
    ov = c._crop.overlay
    assert ov is not None
    before = ov.top_left
    consumed = c._crop.handle_move(QPointF(ov._cx + 5, ov._cy + 5))
    assert consumed is True
    assert ov.top_left == before  # nichts verschoben


def test_move_hover_inside_frame_is_consumed(qapp):
    """Hover über der Rahmenmitte (keine Ecke) setzt den Greif-Cursor und
    konsumiert das Event, ohne zu verschieben."""
    c = _canvas_with_crop()
    ov = c._crop.overlay
    assert ov is not None
    before = ov.top_left
    mid = QPointF(ov._cx + ov._cw / 2, ov._cy + ov._ch / 2)
    assert c._crop.handle_move(mid) is True
    assert ov.top_left == before


def test_move_hover_outside_frame_is_consumed(qapp):
    """Hover außerhalb des Rahmens (Pfeil-Cursor-Zweig) bleibt konsumiert,
    solange ein Overlay aktiv ist."""
    c = _canvas_with_crop()
    ov = c._crop.overlay
    assert ov is not None
    before = ov.top_left
    assert c._crop.handle_move(QPointF(5.0, 5.0)) is True
    assert ov.top_left == before


def test_move_without_overlay_returns_false(qapp):
    c = _canvas()
    assert c._crop.handle_move(QPointF(5.0, 5.0)) is False


# ── Release ────────────────────────────────────────────────────────────

def test_release_after_resize_clears_flag(qapp):
    c = _canvas_with_crop()
    ov = c._crop.overlay
    assert ov is not None
    tl = ov._corners()[0]
    c._crop.handle_press(Qt.MouseButton.LeftButton, QPointF(tl.x(), tl.y()))
    assert c._crop.handle_release() is True
    assert c._crop.is_resizing is False
    # Verhaltens-Check statt internem Sentinel-Reset: Nach dem Release ist
    # die Geste vollständig beendet – ein weiterer Move ist nur noch Hover
    # und ändert die Rahmengröße nicht mehr.
    size_before = ov.size
    c._crop.handle_move(QPointF(tl.x() + 40, tl.y() + 40))
    assert ov.size == size_before


def test_release_after_drag_clears_flag(qapp):
    c = _canvas_with_crop()
    ov = c._crop.overlay
    assert ov is not None
    mid = QPointF(ov._cx + ov._cw / 2, ov._cy + ov._ch / 2)
    c._crop.handle_press(Qt.MouseButton.LeftButton, mid)
    assert c._crop.handle_release() is True
    assert c._crop.is_dragging is False


def test_release_without_gesture_returns_false(qapp):
    c = _canvas_with_crop()
    assert c._crop.handle_release() is False


# ── Confirm / Cancel über die Gesten ───────────────────────────────────

def test_confirm_after_drag_applies_crop(qapp):
    c = _canvas_with_crop()
    ov = c._crop.overlay
    assert ov is not None
    expected_w, expected_h = (int(round(ov.size[0])), int(round(ov.size[1])))
    c.confirm_crop()
    assert c._crop.overlay is None
    assert c.image is not None
    assert c.image.size == (expected_w, expected_h)


def test_cancel_removes_overlay_and_keeps_image(qapp):
    c = _canvas_with_crop()
    before = c.image
    c.cancel_crop()
    assert c._crop.overlay is None
    assert c.image is before


# ── Transienter Zustand bei Bildwechsel ────────────────────────────────

def test_loading_image_during_crop_emits_mode_off(qapp):
    """Bild laden bei aktivem Crop muss das Overlay entfernen UND
    cropModeChanged(False) melden – sonst bleibt die Crop-Leiste sichtbar."""
    c = _canvas_with_crop()
    modes: list[bool] = []
    c.cropModeChanged.connect(modes.append)
    assert c._crop_overlay is not None
    c.apply_loaded_image(Image.new("RGBA", (50, 50), (1, 2, 3, 255)), "next.png")
    assert c._crop_overlay is None
    assert modes == [False]


def test_loading_image_clears_pending_lasso(qapp):
    """Begonnenes Polygon-Lasso darf nicht auf das neue Bild übertragen werden."""
    c = _canvas()
    c.set_tool(TOOL_LASSO)
    c._handle_tool_press(10, 10, Qt.KeyboardModifier.NoModifier)
    c._handle_tool_press(20, 20, Qt.KeyboardModifier.NoModifier)
    assert c._lasso.has_points
    c.apply_loaded_image(Image.new("RGBA", (50, 50), (1, 2, 3, 255)), "next.png")
    assert not c._lasso.has_points


def test_loading_image_without_crop_emits_no_mode_signal(qapp):
    """Ohne aktiven Crop darf kein spurious cropModeChanged(False) feuern."""
    c = _canvas()
    modes: list[bool] = []
    c.cropModeChanged.connect(modes.append)
    c.apply_loaded_image(Image.new("RGBA", (40, 40), (5, 6, 7, 255)), "next.png")
    assert modes == []


# ── Bildzustandswechsel verwirft veraltetes Crop-Overlay (#247) ─────────

def _alpha_min(img: Image.Image) -> int:
    """Kleinster Alpha-Wert – < 255 verrät transparente Padding-Pixel."""
    return int(np.array(img.convert("RGBA"))[:, :, 3].min())


def test_rotate_during_active_crop_discards_stale_overlay(qapp):
    """Regression #247: 400×200, aktiver 16:9-Crop, 90°-Drehung.

    Das alte Rechteck ``≈(22, 0, 355, 200)`` darf das gedrehte 200×400-Bild
    nicht mehr zuschneiden – sonst ergänzt Pillow transparente Padding-Pixel.
    Nach der Drehung ist kein Crop mehr aktiv, ``cropModeChanged`` feuert genau
    einmal ``False`` und ein anschließendes ``confirm_crop()`` ist wirkungslos.
    """
    c = ImageCanvas()
    c.apply_loaded_image(Image.new("RGBA", (400, 200), (10, 20, 30, 255)), "seed.png")
    c.start_crop_ratio(16, 9)
    ov = c._crop_overlay
    assert ov is not None
    # Vorbedingung: Das initiale Rechteck ragt nach einer 90°-Drehung
    # (Bild dann 200 breit) über die rechte Kante hinaus.
    assert ov.crop_rect().width() > 200

    modes: list[bool] = []
    c.cropModeChanged.connect(modes.append)

    c.apply_rotate(90)

    # Overlay verworfen, Modus genau einmal beendet.
    assert c._crop_overlay is None
    assert c._crop.active is False
    assert modes == [False]
    # Reines 90°-Drehergebnis, kein altes Crop-Rechteck angewendet.
    assert c.image is not None
    assert c.image.size == (200, 400)
    assert _alpha_min(c.image) == 255

    # Ein nachgelagertes confirm_crop kann kein veraltetes Rechteck anwenden.
    rotated = c.image
    c.confirm_crop()
    assert c.image is rotated
    assert c.image.size == (200, 400)
    assert _alpha_min(c.image) == 255


def test_image_state_change_restores_tool_cursor_after_crop(qapp):
    """Regression #260: automatisches Crop-Verwerfen stellt den Cursor des
    aktiven Werkzeugs wieder her, statt einen Crop-Hover-Cursor zu behalten.
    """
    c = _canvas(size=(400, 200))
    c.set_tool(TOOL_LASSO)
    c.start_crop_ratio(16, 9)
    ov = c._crop_overlay
    assert ov is not None
    c._crop.handle_move(QPointF(
        ov._cx + ov._cw / 2,
        ov._cy + ov._ch / 2,
    ))
    assert c.cursor().shape() == Qt.CursorShape.OpenHandCursor

    c.apply_rotate(90)

    assert c._crop_overlay is None
    assert c.cursor().shape() == Qt.CursorShape.CrossCursor


def test_crop_mode_signal_sequence_start_then_transform(qapp):
    """Die Signalfolge ist genau ``[True, False]`` – der Crop-Start meldet
    ``True``, die Transformation beendet den Modus mit ``False`` (die UI bleibt
    nicht dauerhaft im Crop-Modus)."""
    c = _canvas(size=(400, 200))
    modes: list[bool] = []
    c.cropModeChanged.connect(modes.append)
    c.start_crop_ratio(16, 9)
    c.apply_flip(horizontal=True)
    assert modes == [True, False]
    assert c._crop_overlay is None


def test_ai_result_during_active_crop_discards_overlay(qapp):
    """Ein KI-Ergebnis wechselt den Bildzustand und muss den Crop verwerfen."""
    c = _canvas(size=(400, 200))
    c.start_crop_ratio(16, 9)
    modes: list[bool] = []
    c.cropModeChanged.connect(modes.append)
    c.apply_ai_result(Image.new("RGBA", (123, 77), (9, 9, 9, 255)))
    assert c._crop_overlay is None
    assert modes == [False]
    assert c.image is not None and c.image.size == (123, 77)


def test_apply_edit_during_active_crop_discards_overlay(qapp):
    """Auch ein generischer ``apply_edit`` (Undo-fähiger Schritt) räumt das
    Crop-Overlay ab und meldet das Modus-Ende einmal."""
    c = _canvas(size=(400, 200))
    c.start_crop_ratio(16, 9)
    modes: list[bool] = []
    c.cropModeChanged.connect(modes.append)
    c.apply_edit(Image.new("RGBA", (50, 50), (1, 1, 1, 255)), desc="x")
    assert c._crop_overlay is None
    assert modes == [False]


def test_restore_original_during_active_crop_discards_overlay(qapp):
    """``restore_original`` ist ein geometrieinkompatibler Wechsel und darf
    kein veraltetes Crop-Overlay zurücklassen."""
    c = _canvas(size=(400, 200))
    c.apply_edit(Image.new("RGBA", (100, 100), (1, 1, 1, 255)), desc="edit")
    c.start_crop_ratio(16, 9)
    assert c._crop_overlay is not None
    modes: list[bool] = []
    c.cropModeChanged.connect(modes.append)
    c.restore_original()
    assert c._crop_overlay is None
    assert modes == [False]
    assert c.image is not None and c.image.size == (400, 200)


def test_image_state_change_discards_pending_lasso(qapp):
    """Ein begonnenes Polygon-Lasso wird bei einem inkompatiblen
    Bildzustandswechsel (hier eine Transformation) ebenfalls verworfen."""
    c = _canvas(size=(400, 200))
    c.set_tool(TOOL_LASSO)
    c._handle_tool_press(10, 10, Qt.KeyboardModifier.NoModifier)
    c._handle_tool_press(20, 20, Qt.KeyboardModifier.NoModifier)
    assert c._lasso.has_points
    c.apply_rotate(90)
    assert not c._lasso.has_points


def test_confirm_crop_remains_single_undo_step(qapp):
    """Crop-Bestätigung bleibt ein einzelner Undo-fähiger Schritt: ein Undo
    stellt exakt das Bild vor dem Zuschnitt wieder her."""
    c = _canvas(size=(400, 200))
    before = c.image
    assert before is not None
    before_size = before.size
    c.start_crop_ratio(1, 1)
    c.confirm_crop()
    assert c.image is not None and c.image.size != before_size
    c.undo()
    assert c.image is not None and c.image.size == before_size
