"""Tests für die interaktive Zoom-Kontrolle auf der Arbeitsfläche (#464).

Headless: das Overlay ist ein Kind des Canvas; Sichtbarkeit wird über
``isHidden`` geprüft (offscreen ist kein Fenster „sichtbar").

Seit #863 bedient die Pille ein generisches :class:`ZoomTarget`-Protocol –
auf der 2D-Leinwand den ``CanvasViewport``, in der 3D-Reliefvorschau die
``Relief3DView``. Der Abschnitt „ZoomTarget-Protocol" prüft sie deshalb
zusätzlich gegen ein minimales Fake-Ziel, also gegen den *Vertrag* statt nur
gegen die beiden konkreten Implementierungen (#869).
"""
from __future__ import annotations

import inspect

import pytest
from PIL import Image
from PyQt6.QtWidgets import QWidget

from bgremover import ImageCanvas
from bgremover.constants import (
    _ZOOM_CTRL_MAX_PCT,
    _ZOOM_CTRL_MIN_PCT,
    _ZOOM_CTRL_STEP_PCT,
)
from bgremover.i18n import tr
from bgremover.zoom_control import ZoomControl, ZoomTarget

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


# ── ZoomTarget-Protocol: Pille ohne Canvas/3D-Viewer ───────────────────


class _FakeZoomTarget:
    """Minimale ``ZoomTarget``-Implementierung, die nur mitschreibt.

    Alles, was ``ZoomControl`` von seinem Ziel verlangt, sind ``step_zoom``
    und ``set_zoom_locked``; Klemmen, Schrittweite und Lock-Semantik liegen im
    Ziel. Das Fake macht genau diese Grenze prüfbar – ein isolierter Umbau der
    Pille fällt hier auf, auch wenn beide realen Ziele unverändert bleiben.
    """

    def __init__(self) -> None:
        self.steps: list[int] = []
        self.locks: list[bool] = []

    def step_zoom(self, delta_pct: int) -> None:
        self.steps.append(delta_pct)

    def set_zoom_locked(self, locked: bool) -> None:
        self.locks.append(locked)


def _fake_pill(qapp) -> tuple[ZoomControl, _FakeZoomTarget, QWidget]:
    """Pille über einem Fake-Ziel; das Elternwidget wird mit zurückgegeben,
    damit es der Test am Leben hält (sonst nimmt Qt das Kind mit)."""
    target = _FakeZoomTarget()
    parent = QWidget()
    return ZoomControl(target, parent), target, parent


def test_protocol_target_receives_only_step_and_lock(qapp) -> None:
    ctrl, target, _parent = _fake_pill(qapp)

    ctrl.btn_in.click()
    ctrl.btn_out.click()
    assert target.steps == [_ZOOM_CTRL_STEP_PCT, -_ZOOM_CTRL_STEP_PCT]
    assert target.locks == []


def test_protocol_lock_forwards_state_and_gates_the_buttons(qapp) -> None:
    ctrl, target, _parent = _fake_pill(qapp)

    ctrl.btn_lock.setChecked(True)
    assert target.locks == [True]
    assert not ctrl.btn_in.isEnabled()
    assert not ctrl.btn_out.isEnabled()
    assert ctrl.btn_lock.toolTip() == tr("zoom.unlock.tooltip")

    ctrl.btn_lock.setChecked(False)
    assert target.locks == [True, False]
    assert ctrl.btn_in.isEnabled()
    assert ctrl.btn_out.isEnabled()
    assert ctrl.btn_lock.toolTip() == tr("zoom.lock.tooltip")

    # Der Lock gehört dem Ziel: die Pille schickt keine Zoom-Schritte los.
    assert target.steps == []


def test_protocol_percent_display_is_write_only(qapp) -> None:
    """``set_percent`` ist reine Anzeige – gerundet und ohne Rückwirkung."""
    ctrl, target, _parent = _fake_pill(qapp)

    ctrl.set_percent(133.4)
    assert ctrl.label.text() == "133%"
    ctrl.set_percent(99.6)
    assert ctrl.label.text() == "100%"

    assert target.steps == []
    assert target.locks == []


def test_real_zoom_targets_still_match_the_protocol(qapp) -> None:
    """Beide produktiven Ziele erfüllen den Protokollvertrag signaturgleich.

    Driftet eine der Implementierungen (umbenannter Parameter, geänderte
    Signatur), schlägt das hier fehl statt erst zur Laufzeit in der Pille –
    ``Protocol`` selbst wird ohne ``@runtime_checkable`` nicht geprüft.
    """
    from bgremover.canvas_viewport import CanvasViewport
    from bgremover.viewer_3d import Relief3DView

    expected = {
        name: inspect.signature(getattr(ZoomTarget, name))
        for name in ("step_zoom", "set_zoom_locked")
    }
    for impl in (CanvasViewport, Relief3DView, _FakeZoomTarget):
        for name, signature in expected.items():
            method = getattr(impl, name, None)
            assert callable(method), f"{impl.__name__} erfüllt ZoomTarget.{name} nicht"
            assert inspect.signature(method) == signature, (
                f"{impl.__name__}.{name} weicht vom ZoomTarget-Vertrag ab")
