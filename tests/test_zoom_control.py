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


# ── +/− in 10-%-Schritten, geklemmt auf 25–300 % ───────────────────────


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
    c.scale(2.95, 2.95)
    c._viewport._notify_zoom()

    c.zoom_control.btn_in.click()
    assert c._viewport.zoom_percent == pytest.approx(_ZOOM_CTRL_MAX_PCT)
    c.zoom_control.btn_in.click()  # bereits am Maximum → No-op
    assert c._viewport.zoom_percent == pytest.approx(_ZOOM_CTRL_MAX_PCT)
    assert c.zoom_control.label.text() == "300%"


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
    from PyQt6.QtCore import QSize
    from PyQt6.QtGui import QResizeEvent

    c = _canvas()
    c.resize(400, 300)
    # Offscreen stellt Qt Resize-Events verborgener Widgets erst beim Anzeigen
    # zu – das Event daher direkt an den Override liefern.
    c.resizeEvent(QResizeEvent(QSize(400, 300), QSize(0, 0)))
    ctrl = c.zoom_control
    assert ctrl.x() + ctrl.width() <= 400
    assert ctrl.y() + ctrl.height() <= 300
    # Verankerung an der rechten/unteren Kante (Prototyp: 14 px Abstand).
    assert ctrl.x() + ctrl.width() == 400 - 14
    assert ctrl.y() + ctrl.height() == 300 - 14
