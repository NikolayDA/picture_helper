"""Tests für die interaktive Zoom-Kontrolle auf der Arbeitsfläche (#464).

Headless: das Overlay ist ein Kind des Canvas; Sichtbarkeit wird über
``isHidden`` geprüft (offscreen ist kein Fenster „sichtbar").
"""
from __future__ import annotations

import pytest
from PIL import Image

from bgremover import ImageCanvas
from bgremover.constants import (
    _ZOOM_CTRL_MAX_PCT,
    _ZOOM_CTRL_MIN_PCT,
)
from bgremover.i18n import tr

# Prototyp-Spec-Wert (§ Redesign): bewusst als *literaler* Vertrag geführt und
# **nicht** aus ``zoom_control._MARGIN`` importiert. Sonst würde der Test die
# Verankerung nur gegen dieselbe Implementierungskonstante prüfen, die sie
# positioniert (tautologisch) – ein versehentliches Verstellen von ``_MARGIN``
# weg von den geforderten 14 px bliebe unentdeckt.
_PROTOTYPE_MARGIN_PX = 14


def _canvas(size=(120, 80)) -> ImageCanvas:
    c = ImageCanvas()
    c.apply_loaded_image(Image.new("RGBA", size, (10, 20, 30, 255)), "seed.png")
    return c


def _reset_zoom(c: ImageCanvas) -> None:
    """Setzt den View auf 1:1 (100 %) und synchronisiert die Anzeige."""
    c.resetTransform()
    c._viewport._notify_zoom()


# ── Sichtbarkeit ───────────────────────────────────────────────────────


def test_overlay_hidden_without_image(qapp):
    c = ImageCanvas()
    assert c.zoom_control.isHidden()


def test_overlay_shown_once_image_loaded(qapp):
    c = _canvas()
    assert not c.zoom_control.isHidden()


# ── +/− in 10-%-Schritten, geklemmt auf 25–4000 % ──────────────────────


def test_plus_and_minus_step_by_ten_percent(qapp, qtbot):
    c = _canvas()
    _reset_zoom(c)
    assert c.zoom_control.label.text() == "100%"

    c.zoom_control.btn_in.click()
    assert c._viewport.zoom_percent == pytest.approx(110)
    assert c.zoom_control.label.text() == "110%"

    c.zoom_control.btn_out.click()
    assert c._viewport.zoom_percent == pytest.approx(100)
    assert c.zoom_control.label.text() == "100%"


def test_zoom_clamped_at_maximum(qapp):
    c = _canvas()
    c.resetTransform()
    c.scale(39.95, 39.95)
    c._viewport._notify_zoom()

    c.zoom_control.btn_in.click()
    assert c._viewport.zoom_percent == pytest.approx(_ZOOM_CTRL_MAX_PCT)
    c.zoom_control.btn_in.click()  # bereits am Maximum → No-op
    assert c._viewport.zoom_percent == pytest.approx(_ZOOM_CTRL_MAX_PCT)
    assert c.zoom_control.label.text() == "4000%"


def test_plus_button_continues_beyond_legacy_300_percent(qapp):
    c = _canvas()
    c.resetTransform()
    c.scale(3.0, 3.0)
    c._viewport._notify_zoom()

    c.zoom_control.btn_in.click()

    assert c._viewport.zoom_percent == pytest.approx(310)
    assert c.zoom_control.label.text() == "310%"


def test_zoom_clamped_at_minimum(qapp):
    c = _canvas()
    c.resetTransform()
    c.scale(0.30, 0.30)
    c._viewport._notify_zoom()

    c.zoom_control.btn_out.click()
    assert c._viewport.zoom_percent == pytest.approx(_ZOOM_CTRL_MIN_PCT)
    c.zoom_control.btn_out.click()
    assert c._viewport.zoom_percent == pytest.approx(_ZOOM_CTRL_MIN_PCT)
    assert c.zoom_control.label.text() == "25%"


def test_step_buttons_do_not_reverse_direction_outside_control_range(qapp):
    c = _canvas()
    c.resetTransform()
    c.scale(0.20, 0.20)
    c._viewport._notify_zoom()

    c.zoom_control.btn_out.click()
    assert c._viewport.zoom_percent == pytest.approx(20)

    c.resetTransform()
    c.scale(40.10, 40.10)
    c._viewport._notify_zoom()

    c.zoom_control.btn_in.click()
    assert c._viewport.zoom_percent == pytest.approx(4010)


# ── Fixier-Lock ────────────────────────────────────────────────────────


def test_lock_freezes_buttons_and_wheel(qapp):
    c = _canvas()
    _reset_zoom(c)

    c.zoom_control.btn_lock.setChecked(True)
    assert c._viewport.zoom_locked is True
    assert not c.zoom_control.btn_in.isEnabled()
    assert not c.zoom_control.btn_out.isEnabled()
    assert c.zoom_control.btn_lock.toolTip() == tr("zoom.unlock.tooltip")

    before = c.transform().m11()
    c._viewport.step_zoom(10)     # Buttons wirkungslos …
    c._viewport.handle_wheel(120)  # … und Mausrad-Zoom ebenso
    assert c.transform().m11() == before

    # Entriegeln stellt beides wieder her.
    c.zoom_control.btn_lock.setChecked(False)
    assert c._viewport.zoom_locked is False
    assert c.zoom_control.btn_in.isEnabled()
    assert c.zoom_control.btn_lock.toolTip() == tr("zoom.lock.tooltip")
    c._viewport.handle_wheel(120)
    assert c.transform().m11() > before


# ── Reiner UI-State: kein Undo-/Dirty-Eintrag ──────────────────────────


def test_zoom_and_lock_do_not_touch_history_or_revision(qapp):
    c = _canvas()
    _reset_zoom(c)
    revision = c.content_revision
    assert c._history.descriptions() == []

    c.zoom_control.btn_in.click()
    c.zoom_control.btn_lock.setChecked(True)
    c.zoom_control.btn_lock.setChecked(False)
    c.zoom_control.btn_out.click()

    assert c._history.descriptions() == []
    assert c.content_revision == revision


# ── Live-Anzeige folgt jeder Zoom-Quelle ───────────────────────────────


def test_label_follows_wheel_and_fit(qapp):
    c = _canvas()
    _reset_zoom(c)
    c._viewport.handle_wheel(120)
    expected = round(c._viewport.zoom_percent)
    assert c.zoom_control.label.text() == f"{expected}%"

    c.fit_to_view()
    expected = round(c._viewport.zoom_percent)
    assert c.zoom_control.label.text() == f"{expected}%"


def test_overlay_repositions_bottom_right(qapp):
    c = _canvas()
    c.resize(400, 300)
    c.show()
    qapp.processEvents()
    ctrl = c.zoom_control
    parent = ctrl.parentWidget()
    assert parent is c.viewport()
    ctrl.reposition()
    assert ctrl.x() + ctrl.width() <= parent.width()
    assert ctrl.y() + ctrl.height() <= parent.height()
    # Verankerung an der rechten/unteren Viewport-Kante (Prototyp: 14 px Abstand,
    # bewusst als implementierungsunabhängiger Spec-Vertrag – siehe Modulkopf).
    assert ctrl.x() + ctrl.width() == parent.width() - _PROTOTYPE_MARGIN_PX
    assert ctrl.y() + ctrl.height() == parent.height() - _PROTOTYPE_MARGIN_PX


def test_overlay_repositions_inside_viewport_when_scrollbars_are_visible(qapp):
    c = _canvas(size=(2000, 2000))
    c.resize(400, 300)
    c.show()
    qapp.processEvents()
    c.resetTransform()
    c.scale(2.0, 2.0)
    c._viewport._notify_zoom()
    qapp.processEvents()

    assert c.horizontalScrollBar().isVisible()
    assert c.verticalScrollBar().isVisible()
    ctrl = c.zoom_control
    parent = c.viewport()
    assert ctrl.parentWidget() is parent
    assert ctrl.x() + ctrl.width() == parent.width() - _PROTOTYPE_MARGIN_PX
    assert ctrl.y() + ctrl.height() == parent.height() - _PROTOTYPE_MARGIN_PX
