"""Tests des 3D-Viewer-Containers und der Fallback-Zustände (#593, Epic #582).

Der Zustandsautomat (Empty/Unavailable/Loading/Error/Ready) und der Decimation-
Badge sind ohne GL-Kontext prüfbar; der GL-Viewer selbst rendert im
Offscreen-CI nicht (echter Fallbackpfad), seine Konstruktion/Fehlerbehandlung
propagiert aber nie eine Exception.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent

from bgremover import viewer_3d
from bgremover.height_map import HEIGHT_MAX_16BIT, HeightField
from bgremover.relief_mesh import MeshQuality, build_relief_mesh
from bgremover.viewer_3d import (
    SETTLED_STATES,
    STATE_ERROR,
    STATE_READY,
    GLReliefViewer,
    Relief3DView,
)

pytestmark = pytest.mark.ui_smoke

NO_MOD = Qt.KeyboardModifier.NoModifier


def _mesh(size: int = 24) -> object:
    field = HeightField(
        np.full((size, size), 5000, np.uint16),
        np.full((size, size), 255, np.uint8),
        HEIGHT_MAX_16BIT,
    )
    return build_relief_mesh(field, MeshQuality.REDUCED)


def _mouse_event(
    kind: QEvent.Type, x: float, y: float,
    button: Qt.MouseButton = Qt.MouseButton.LeftButton,
    buttons: Qt.MouseButton | None = None,
) -> QMouseEvent:
    return QMouseEvent(kind, QPointF(x, y), button, buttons or button, NO_MOD)


def _wheel_event(delta_y: int) -> QWheelEvent:
    return QWheelEvent(
        QPointF(5, 5), QPointF(5, 5), QPoint(0, 0), QPoint(0, delta_y),
        Qt.MouseButton.NoButton, NO_MOD, Qt.ScrollPhase.NoScrollPhase, False,
    )


def _key_event(key: Qt.Key, modifiers: Qt.KeyboardModifier = NO_MOD) -> QKeyEvent:
    return QKeyEvent(QKeyEvent.Type.KeyPress, key, modifiers)


def _large_mesh() -> object:
    field = HeightField(
        np.zeros((2000, 2000), np.uint16),
        np.full((2000, 2000), 255, np.uint8),
        HEIGHT_MAX_16BIT,
    )
    return build_relief_mesh(field, MeshQuality.STANDARD)


def test_state_machine_transitions(qapp) -> None:
    view = Relief3DView()
    assert view.state == "empty"
    view.show_unavailable()
    assert view.state == "unavailable"
    view.show_loading()
    assert view.state == "loading"
    view.show_error()
    assert view.state == "error"
    view.show_empty()
    assert view.state == "empty"


def test_show_mesh_reaches_ready_or_error(qapp) -> None:
    view = Relief3DView()
    view.show_mesh(_mesh())
    # Ready (Viewer konstruiert) oder Error (kein GL) – nie eine Exception.
    assert view.state in ("ready", "error")


def test_failed_viewer_is_recreated_on_retry(qapp) -> None:
    view = Relief3DView()
    view.show_mesh(_mesh())
    viewer = view.viewer()
    if viewer is None:
        pytest.skip("Kein GL-Viewer-Widget verfügbar")
    # GL-Fehler simulieren: der Viewer ist nicht mehr renderfähig.
    viewer._failed = True
    # Seit #1004 ist der ausdrückliche Retry der einzige Weg zum Neuaufbau –
    # sonst entstünde bei jeder Inhaltsänderung ein neuer, gleich scheiternder
    # GL-Kontext (Review PR #1005).
    view.allow_viewer_retry()
    view.show_mesh(_mesh())
    new_viewer = view.viewer()
    # Der fehlgeschlagene Viewer wurde verworfen und ein frischer aufgebaut.
    assert new_viewer is not None
    assert new_viewer is not viewer
    assert not new_viewer.has_failed


def test_decimation_badge_reflects_factor(qapp) -> None:
    mesh = _large_mesh()
    assert mesh.is_decimated and mesh.decimation_factor > 1
    view = Relief3DView()
    view.show_mesh(mesh)
    # ``show_mesh`` konstruiert den GL-Viewer synchron (initializeGL läuft erst
    # beim ersten Paint) – der Zustand wird auch offscreen deterministisch
    # ``ready``, unabhängig davon, ob der Kontext später real rendert.
    assert view.state == STATE_READY
    assert f"1:{mesh.decimation_factor}" in view._badge.text()


def test_show2d_and_retry_signals_fire(qapp) -> None:
    view = Relief3DView()
    fired: list[str] = []
    view.show2DRequested.connect(lambda: fired.append("2d"))
    view.retryRequested.connect(lambda: fired.append("retry"))
    view.show2DRequested.emit()
    view.retryRequested.emit()
    assert fired == ["2d", "retry"]


def test_gl_viewer_construction_and_params_do_not_raise(qapp) -> None:
    mesh = _mesh()
    viewer = GLReliefViewer()
    viewer.set_mesh(mesh)
    assert viewer._mesh is mesh
    assert viewer._pending_mesh is mesh

    viewer.set_exaggeration(3.0)
    assert viewer._exaggeration == 3.0
    viewer.set_exaggeration(50.0)  # oberhalb der Klemme
    assert viewer._exaggeration == 10.0

    viewer.set_light(120.0, 60.0)
    assert viewer._light == (120.0, 60.0)

    fitted_distance = viewer.camera.distance
    viewer.camera.zoom(5.0)
    assert viewer.camera.distance != fitted_distance
    viewer.fit_view()
    assert viewer.camera.distance == pytest.approx(fitted_distance)

    viewer.reset_view()
    assert viewer._exaggeration == 1.0
    assert viewer._light == (315.0, 45.0)
    assert viewer.camera.distance == pytest.approx(fitted_distance)

    viewer.cleanup_gl()  # doppelte Freigabe muss ebenfalls sicher sein
    assert viewer._gl_ready is False
    assert viewer._index_count == 0
    viewer.cleanup_gl()
    assert viewer._gl_ready is False


def test_shift_home_requests_central_reset(qapp) -> None:
    viewer = GLReliefViewer()
    requested: list[bool] = []
    viewer.resetRequested.connect(lambda: requested.append(True))

    viewer.keyPressEvent(QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_Home,
        Qt.KeyboardModifier.ShiftModifier,
    ))

    assert requested == [True]


def test_gl_viewer_reports_init_failure_without_propagating(qapp) -> None:
    viewer = GLReliefViewer()
    failures: list[str] = []
    viewer.initFailed.connect(failures.append)
    # initializeGL ist gekapselt: ohne echten GL-Kontext (Offscreen-Plattform)
    # schlägt es deterministisch fehl, propagiert aber nie – es meldet
    # initFailed genau einmal und hinterlässt einen definierten Fehlerzustand.
    viewer.initializeGL()
    assert viewer.has_failed is True
    assert len(failures) == 1
    assert "initializeGL" in failures[0]
    assert viewer._gl_ready is False


def test_context_loss_requeues_cpu_mesh_for_upload(qapp) -> None:
    """ADR #591: Ein neuer GL-Kontext lädt die gehaltene CPU-Kopie erneut."""
    viewer = GLReliefViewer()
    mesh = _mesh()
    viewer.set_mesh(mesh)
    viewer._pending_mesh = None  # simuliert: bereits in den alten Kontext geladen
    viewer._gl_ready = True

    viewer._on_context_about_to_be_destroyed()

    assert viewer._pending_mesh is mesh
    assert viewer._mesh is mesh
    assert not viewer._gl_ready
    assert viewer._index_count == 0


def test_accessible_names_present(qapp) -> None:
    viewer = GLReliefViewer()
    assert viewer.accessibleName()
    assert viewer.accessibleDescription()


# ── Maus-/Wheel-/Tastatur-Dispatch (#659, O8) ────────────────────────────

def test_mouse_press_sets_last_pos(qapp) -> None:
    viewer = GLReliefViewer()
    viewer.mousePressEvent(_mouse_event(QEvent.Type.MouseButtonPress, 10.0, 20.0))
    assert viewer._last_pos == (10.0, 20.0)


def test_mouse_press_ignores_none_event(qapp) -> None:
    viewer = GLReliefViewer()
    viewer.mousePressEvent(None)
    assert viewer._last_pos is None


def test_mouse_drag_with_left_button_orbits_camera(qapp) -> None:
    viewer = GLReliefViewer()
    before_azimuth = viewer.camera.azimuth
    viewer.mousePressEvent(_mouse_event(QEvent.Type.MouseButtonPress, 0.0, 0.0))
    viewer.mouseMoveEvent(_mouse_event(
        QEvent.Type.MouseMove, 10.0, 0.0, buttons=Qt.MouseButton.LeftButton,
    ))
    assert viewer.camera.azimuth != before_azimuth


def test_mouse_drag_with_middle_button_pans_camera(qapp) -> None:
    viewer = GLReliefViewer()
    before_focus = viewer.camera.focus.copy()
    viewer.mousePressEvent(_mouse_event(
        QEvent.Type.MouseButtonPress, 0.0, 0.0, button=Qt.MouseButton.MiddleButton,
    ))
    viewer.mouseMoveEvent(_mouse_event(
        QEvent.Type.MouseMove, 10.0, 10.0, buttons=Qt.MouseButton.MiddleButton,
    ))
    assert not np.array_equal(viewer.camera.focus, before_focus)


def test_mouse_drag_with_left_button_and_alt_pans_camera(qapp) -> None:
    viewer = GLReliefViewer()
    before_focus = viewer.camera.focus.copy()
    viewer.mousePressEvent(_mouse_event(
        QEvent.Type.MouseButtonPress, 0.0, 0.0, button=Qt.MouseButton.LeftButton,
    ))
    ev = QMouseEvent(
        QEvent.Type.MouseMove, QPointF(10.0, 10.0), Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.AltModifier,
    )
    viewer.mouseMoveEvent(ev)
    assert not np.array_equal(viewer.camera.focus, before_focus)


def test_mouse_move_without_prior_press_is_noop(qapp) -> None:
    viewer = GLReliefViewer()
    before_azimuth = viewer.camera.azimuth
    viewer.mouseMoveEvent(_mouse_event(
        QEvent.Type.MouseMove, 10.0, 0.0, buttons=Qt.MouseButton.LeftButton,
    ))
    assert viewer.camera.azimuth == before_azimuth


def test_mouse_move_ignores_none_event(qapp) -> None:
    viewer = GLReliefViewer()
    viewer.mousePressEvent(_mouse_event(QEvent.Type.MouseButtonPress, 0.0, 0.0))
    before_last_pos = viewer._last_pos
    before_azimuth = viewer.camera.azimuth
    viewer.mouseMoveEvent(None)  # darf nicht werfen
    assert viewer._last_pos == before_last_pos
    assert viewer.camera.azimuth == before_azimuth


def test_mouse_release_clears_last_pos(qapp) -> None:
    viewer = GLReliefViewer()
    viewer.mousePressEvent(_mouse_event(QEvent.Type.MouseButtonPress, 0.0, 0.0))
    assert viewer._last_pos is not None
    viewer.mouseReleaseEvent(_mouse_event(QEvent.Type.MouseButtonRelease, 0.0, 0.0))
    assert viewer._last_pos is None


def test_wheel_event_zooms_camera_distance_both_directions(qapp) -> None:
    viewer = GLReliefViewer()
    before = viewer.camera.distance
    viewer.wheelEvent(_wheel_event(120))
    assert viewer.camera.distance < before

    before = viewer.camera.distance
    viewer.wheelEvent(_wheel_event(-120))
    assert viewer.camera.distance > before


def test_wheel_event_zero_delta_and_none_event_are_noops(qapp) -> None:
    viewer = GLReliefViewer()
    before = viewer.camera.distance
    viewer.wheelEvent(_wheel_event(0))
    viewer.wheelEvent(None)
    assert viewer.camera.distance == before


def test_key_press_left_right_orbit_azimuth(qapp) -> None:
    viewer = GLReliefViewer()
    before = viewer.camera.azimuth
    viewer.keyPressEvent(_key_event(Qt.Key.Key_Right))
    assert viewer.camera.azimuth != before


def test_key_press_up_down_orbit_elevation(qapp) -> None:
    viewer = GLReliefViewer()
    before = viewer.camera.elevation
    viewer.keyPressEvent(_key_event(Qt.Key.Key_Up))
    assert viewer.camera.elevation != before


def test_key_press_shift_arrows_pan_camera(qapp) -> None:
    viewer = GLReliefViewer()
    before_focus = viewer.camera.focus.copy()
    viewer.keyPressEvent(
        _key_event(Qt.Key.Key_Right, Qt.KeyboardModifier.ShiftModifier)
    )
    assert not np.array_equal(viewer.camera.focus, before_focus)


def test_key_press_plus_minus_zoom_camera(qapp) -> None:
    viewer = GLReliefViewer()
    before = viewer.camera.distance
    viewer.keyPressEvent(_key_event(Qt.Key.Key_Plus))
    assert viewer.camera.distance < before

    before = viewer.camera.distance
    viewer.keyPressEvent(_key_event(Qt.Key.Key_Minus))
    assert viewer.camera.distance > before


def test_key_press_home_without_shift_fits_view(qapp) -> None:
    viewer = GLReliefViewer()
    viewer.set_mesh(_mesh())
    fitted_distance = viewer.camera.distance
    viewer.camera.zoom(5.0)
    assert viewer.camera.distance != fitted_distance
    viewer.keyPressEvent(_key_event(Qt.Key.Key_Home))
    assert viewer.camera.distance == pytest.approx(fitted_distance)


def test_key_press_unhandled_key_passes_through_without_raising(qapp) -> None:
    viewer = GLReliefViewer()
    before_azimuth = viewer.camera.azimuth
    viewer.keyPressEvent(_key_event(Qt.Key.Key_A))  # kein zugeordnetes Kürzel
    assert viewer.camera.azimuth == before_azimuth


def test_key_press_ignores_none_event(qapp) -> None:
    viewer = GLReliefViewer()
    before_azimuth = viewer.camera.azimuth
    before_elevation = viewer.camera.elevation
    viewer.keyPressEvent(None)  # darf nicht werfen
    assert viewer.camera.azimuth == before_azimuth
    assert viewer.camera.elevation == before_elevation

# GL-Ressourcen-Hygiene beim (Wieder-)Upload (``_release_gl_objects``,
# Leak-Freiheit über wiederholte Uploads) ist in
# ``tests/test_viewer_3d_gl_lifecycle.py`` gründlicher über die geteilte
# ``ResourceLedger``/``tracked_gl_resources``-Instrumentierung abgedeckt
# (u. a. ``test_every_created_object_is_released_exactly_once``) – die
# frühere, weniger strenge ``_FakeGLResource``-Variante hier war ein reines
# Duplikat (#716).


# ── Zoom-Pille in der 3D-Ansicht (#464-Parität) ──────────────────────────

def _ready_view() -> tuple[Relief3DView, GLReliefViewer]:
    view = Relief3DView()
    view.show_mesh(_mesh())
    viewer = view.viewer()
    if view.state != "ready" or viewer is None:
        pytest.skip("Kein GL-Viewer-Widget verfügbar")
    return view, viewer


def test_zoom_pill_hidden_outside_ready_state(qapp) -> None:
    view = Relief3DView()
    assert view._zoom_ctrl.isHidden()
    view.show_loading()
    assert view._zoom_ctrl.isHidden()
    view.show_error()
    assert view._zoom_ctrl.isHidden()


def test_zoom_pill_visible_and_at_100_percent_in_ready_state(qapp) -> None:
    view, _viewer = _ready_view()
    assert not view._zoom_ctrl.isHidden()
    assert view._zoom_ctrl.label.text() == "100%"


def test_zoom_pill_hides_again_when_leaving_ready_state(qapp) -> None:
    view, _viewer = _ready_view()
    view.show_error()
    assert view._zoom_ctrl.isHidden()


def test_zoom_pill_buttons_step_camera_percent(qapp) -> None:
    view, viewer = _ready_view()
    view._zoom_ctrl.btn_in.click()
    assert viewer.zoom_percent == pytest.approx(110)
    assert view._zoom_ctrl.label.text() == "110%"
    view._zoom_ctrl.btn_out.click()
    assert viewer.zoom_percent == pytest.approx(100)
    assert view._zoom_ctrl.label.text() == "100%"


def test_zoom_pill_label_follows_wheel_and_key_zoom(qapp) -> None:
    view, viewer = _ready_view()
    viewer.wheelEvent(_wheel_event(120))
    assert view._zoom_ctrl.label.text() == f"{round(viewer.zoom_percent)}%"
    viewer.keyPressEvent(_key_event(Qt.Key.Key_Minus))
    assert view._zoom_ctrl.label.text() == f"{round(viewer.zoom_percent)}%"


def test_zoom_pill_label_follows_fit_and_reset(qapp) -> None:
    view, viewer = _ready_view()
    viewer.wheelEvent(_wheel_event(120))
    assert view._zoom_ctrl.label.text() != "100%"
    view.fit_view()
    assert view._zoom_ctrl.label.text() == "100%"


def test_zoom_pill_lock_freezes_wheel_keys_and_buttons(qapp) -> None:
    view, viewer = _ready_view()
    view._zoom_ctrl.btn_lock.setChecked(True)
    assert viewer.zoom_locked is True
    assert not view._zoom_ctrl.btn_in.isEnabled()
    assert not view._zoom_ctrl.btn_out.isEnabled()

    before = viewer.camera.distance
    viewer.wheelEvent(_wheel_event(120))
    viewer.keyPressEvent(_key_event(Qt.Key.Key_Plus))
    viewer.step_zoom(10)
    assert viewer.camera.distance == before

    view._zoom_ctrl.btn_lock.setChecked(False)
    assert viewer.zoom_locked is False
    viewer.wheelEvent(_wheel_event(120))
    assert viewer.camera.distance < before


def test_zoom_pill_lock_survives_viewer_rebuild(qapp) -> None:
    view, viewer = _ready_view()
    view._zoom_ctrl.btn_lock.setChecked(True)
    viewer._failed = True  # GL-Fehler simulieren → Retry baut neu auf
    view.allow_viewer_retry()
    view.show_mesh(_mesh())
    new_viewer = view.viewer()
    assert new_viewer is not None and new_viewer is not viewer
    assert new_viewer.zoom_locked is True


def test_step_zoom_clamps_at_camera_near_limit(qapp) -> None:
    viewer = GLReliefViewer()
    viewer.set_mesh(_mesh())
    viewer.camera.set_zoom_percent(995.0)  # dicht an der Nahklemme (1000 %)
    viewer.step_zoom(10)
    assert viewer.zoom_percent == pytest.approx(1000.0)
    viewer.step_zoom(10)  # an der Kameraklemme → keine Änderung mehr
    assert viewer.zoom_percent == pytest.approx(1000.0)


def test_step_zoom_moves_only_toward_control_range(qapp) -> None:
    from bgremover.constants import _ZOOM_CTRL_MIN_PCT

    viewer = GLReliefViewer()
    viewer.set_mesh(_mesh())
    viewer.camera.set_zoom_percent(12.5)  # Fernklemme, unter dem Pillenbereich
    viewer.step_zoom(-10)                 # weiter hinaus → No-op (wie 2D)
    assert viewer.zoom_percent == pytest.approx(12.5)
    viewer.step_zoom(10)                  # zurück in Richtung Bereich
    assert viewer.zoom_percent == pytest.approx(_ZOOM_CTRL_MIN_PCT)


def test_zoom_pill_repositions_bottom_right(qapp) -> None:
    view, _viewer = _ready_view()
    view.resize(400, 300)
    view.show()
    qapp.processEvents()
    ctrl = view._zoom_ctrl
    assert ctrl.parentWidget() is view
    # Verankerung wie auf der 2D-Leinwand (Prototyp: 14 px Abstand, siehe
    # tests/test_zoom_control.py zum literalen Spec-Vertrag).
    assert ctrl.x() + ctrl.width() == view.width() - 14
    assert ctrl.y() + ctrl.height() == view.height() - 14


def test_locked_zoom_percent_survives_set_mesh(qapp) -> None:
    """Review-Befund PR #863: Re-Anzeige (Cache-Hit/Qualität/Höhen-Edit)
    läuft über ``set_mesh`` – der fixierte Prozentwert darf dabei nicht
    still auf 100 % zurückspringen."""
    viewer = GLReliefViewer()
    viewer.set_mesh(_mesh())
    viewer.camera.set_zoom_percent(250.0)
    viewer.set_zoom_locked(True)
    viewer.set_mesh(_mesh())
    assert viewer.zoom_percent == pytest.approx(250.0)
    # Ohne Lock rahmt ein neues Mesh weiterhin ein (Altverhalten).
    viewer.set_zoom_locked(False)
    viewer.set_mesh(_mesh())
    assert viewer.zoom_percent == pytest.approx(100.0)


def test_locked_zoom_percent_survives_show_mesh_redisplay(qapp) -> None:
    view, viewer = _ready_view()
    viewer.camera.set_zoom_percent(250.0)
    view._zoom_ctrl.btn_lock.setChecked(True)
    view.show_mesh(_mesh())  # Re-Anzeige, z. B. Cache-Hit beim 2D→3D-Wechsel
    current = view.viewer()
    assert current is not None
    assert current.zoom_percent == pytest.approx(250.0)
    assert view._zoom_ctrl.label.text() == "250%"


def test_explicit_fit_view_overrides_lock_like_2d(qapp) -> None:
    viewer = GLReliefViewer()
    viewer.set_mesh(_mesh())
    viewer.camera.set_zoom_percent(250.0)
    viewer.set_zoom_locked(True)
    viewer.fit_view()  # explizites Kommando – wie Fit-to-View in 2D
    assert viewer.zoom_percent == pytest.approx(100.0)


def test_step_zoom_at_camera_clamp_emits_no_signal(qapp) -> None:
    """Review-Befund PR #863: an der Kameraklemme darf ein wirkungsloser
    Pillen-Klick weder Signal noch Repaint auslösen (2D-Kurzschluss-Parität)."""
    viewer = GLReliefViewer()
    viewer.set_mesh(_mesh())
    viewer.camera.set_zoom_percent(1000.0)  # Nahklemme
    fired: list[float] = []
    viewer.zoomChanged.connect(fired.append)
    viewer.step_zoom(10)   # Klemme neutralisiert den Schritt → still
    assert fired == []
    assert viewer.zoom_percent == pytest.approx(1000.0)
    viewer.step_zoom(-10)  # echter Schritt → genau ein Signal
    assert len(fired) == 1


def test_zoom_pill_stays_anchored_after_zoom_changes_width(qapp) -> None:
    """Review-Befund PR #863: ``set_percent`` ändert die Pillenbreite
    (``adjustSize``); jede Zoomänderung muss deshalb auch neu verankern."""
    view, viewer = _ready_view()
    view.resize(400, 300)
    view.show()
    qapp.processEvents()
    ctrl = view._zoom_ctrl
    # An die Nahklemme zoomen: „1000%" sprengt die 40-px-Mindestbreite
    # des Labels, die Pille wird breiter.
    viewer.camera.set_zoom_percent(1000.0)
    viewer._notify_zoom()
    assert ctrl.label.text() == "1000%"
    assert ctrl.x() + ctrl.width() == view.width() - 14
    assert ctrl.y() + ctrl.height() == view.height() - 14


# ── Beobachtender Renderbeweis (#1004) ───────────────────────────────────
#
# Qts Absage „No fbo, cannot render" ist eine ``qWarning`` aus
# ``QOpenGLWidgetPrivate::render``, keine Ausnahme – der bisherige, rein
# exception-basierte Fehlerpfad sah sie nie. Gegen den Plattformnamen zu
# prüfen genügt hier nicht: Gemessen (``xvfb-run``, llvmpipe) ist die Signatur
# eines gesunden **verborgenen** Viewers bitgleich zur kaputten. Getrennt
# werden sie dadurch, dass Qt einem verborgenen Widget gar keinen ``paintEvent``
# schickt – deshalb hängt der Wächter dort und nicht an ``isVisible()`` (ein
# verdecktes Fenster wäre sichtbar und malte trotzdem nicht).

def _refuse_frames(viewer, monkeypatch) -> None:
    """Lässt ``defaultFramebufferObject()`` 0 melden – Qts Absage."""
    monkeypatch.setattr(type(viewer), "defaultFramebufferObject", lambda self: 0)


def _grant_frames(viewer, monkeypatch) -> None:
    monkeypatch.setattr(type(viewer), "defaultFramebufferObject", lambda self: 1)


def _paint(viewer, times: int = 1) -> None:
    from PyQt6.QtCore import QRect
    from PyQt6.QtGui import QPaintEvent

    for _ in range(times):
        viewer.paintEvent(QPaintEvent(QRect(0, 0, 10, 10)))


def _settle(qapp) -> None:
    """Stellt den Befund zu – er verlässt Qts Paint-Zustellung per Timer."""
    for _ in range(3):
        qapp.processEvents()


def test_frame_swapped_marks_the_viewer_as_rendered(qapp) -> None:
    """``frameSwapped`` ist der einzige positive Zeuge – und kommt von Qt."""
    viewer = GLReliefViewer()
    viewer._refused_paints = 2

    viewer._on_frame_swapped()

    assert viewer._has_rendered is True
    assert viewer._refused_paints == 0


def test_a_single_refused_paint_does_not_downgrade(qapp, monkeypatch) -> None:
    """Eine einzelne Absage kann ein Übergang sein.

    Gemessen zeigt selbst der kaputte Fall beim ersten Paint noch einen
    Framebuffer; erst der zweite ist 0.
    """
    viewer = GLReliefViewer()
    _refuse_frames(viewer, monkeypatch)

    _paint(viewer, 1)

    assert viewer.has_failed is False
    assert viewer._refused_paints == 1


def test_repeated_refusals_report_the_missing_widget_framebuffer(
    qapp, monkeypatch
) -> None:
    """Der eigentliche #1004-Fall: Qt weist dauerhaft ab, ohne je zu werfen."""
    viewer = GLReliefViewer()
    failures: list[str] = []
    viewer.initFailed.connect(failures.append)
    _refuse_frames(viewer, monkeypatch)

    _paint(viewer, 3)
    _settle(qapp)

    assert viewer.has_failed is True
    assert len(failures) == 1
    assert "Widget-Framebuffer" in failures[0]
    # Die Meldung trägt die tatsächliche Zahl: „0 Anforderungen abgewiesen"
    # war der Fingerabdruck des zurückgenommenen Befundes (siehe oben).
    assert "3 Anforderungen abgewiesen" in failures[0]


def test_a_successful_paint_resets_the_refusal_count(qapp, monkeypatch) -> None:
    viewer = GLReliefViewer()
    _refuse_frames(viewer, monkeypatch)
    _paint(viewer, 2)
    assert viewer._refused_paints == 2

    _grant_frames(viewer, monkeypatch)
    _paint(viewer, 1)

    assert viewer._refused_paints == 0
    assert viewer.has_failed is False


def test_a_viewer_that_rendered_once_is_never_downgraded(qapp, monkeypatch) -> None:
    """Die asymmetrische Zusage: Wer je einen Frame lieferte, bleibt verschont.

    ``defaultFramebufferObject()`` ist Beobachtungswissen, kein zugesicherter
    Qt-Vertrag. Es darf deshalb nie gegen einen Viewer zeugen, für den Qt
    selbst schon einen Frame bestätigt hat.
    """
    viewer = GLReliefViewer()
    viewer._on_frame_swapped()
    _refuse_frames(viewer, monkeypatch)

    _paint(viewer, 10)

    assert viewer.has_failed is False
    assert viewer._refused_paints == 0


def test_a_frame_after_the_threshold_takes_the_downgrade_back(qapp, monkeypatch) -> None:
    """Der Freispruch gilt auch, wenn er die Zustellung knapp gewinnt.

    Die Schwelle fordert den Befund nur an; zugestellt wird er über einen
    Kind-Timer (Review PR #1005). Kommt der echte Frame dazwischen, war der
    Viewer nie kaputt – bis hierher stufte ihn der Timer trotzdem ab, und zwar
    mit „0 Anforderungen abgewiesen", weil der Freispruch den Zähler nullt.
    Das ist die Fehlklassifikation, die auf einer Plattform mit spätem erstem
    Frame-Tausch entstünde (#1010).
    """
    viewer = GLReliefViewer()
    failures: list[str] = []
    viewer.initFailed.connect(failures.append)
    _refuse_frames(viewer, monkeypatch)
    _paint(viewer, 3)
    assert viewer._fail_pending is True, "Schwelle nicht erreicht – Test misst nichts"

    viewer._on_frame_swapped()
    _settle(qapp)

    assert viewer.has_failed is False
    assert failures == []
    assert viewer._has_rendered is True


def test_the_reporter_stands_down_after_an_acquittal(qapp, monkeypatch) -> None:
    """Die zweite Barriere im Reporter, direkt geprüft.

    ``_clear_pending_failure`` stoppt den Timer – die beiden Tests hier herum
    betreten ``_report_missing_framebuffer`` deshalb gar nicht, und sein
    ``if`` bliebe ohne diesen Test ungeprüft (streichbar, ohne dass etwas rot
    wird). Hergestellt wird darum genau die Lage, gegen die es verteidigt: Der
    Reporter läuft, obwohl die Anforderung längst zurückgenommen ist.
    """
    viewer = GLReliefViewer()
    failures: list[str] = []
    viewer.initFailed.connect(failures.append)
    _refuse_frames(viewer, monkeypatch)
    _paint(viewer, 3)
    viewer._on_frame_swapped()
    assert viewer._fail_pending is False

    viewer._report_missing_framebuffer()   # als wäre das Timeout schon zugestellt

    assert viewer.has_failed is False
    assert failures == []


def test_a_context_loss_after_the_threshold_takes_the_downgrade_back(
    qapp, monkeypatch
) -> None:
    """Dieselbe Rücknahme aus dem zweiten Grund: Der Befund gehört dem alten
    Kontext. Ohne sie widerspräche die Zustellung der Zusage direkt daneben,
    dass eine Abweisung aus dem alten Kontext den neuen nicht belastet."""
    viewer = GLReliefViewer()
    failures: list[str] = []
    viewer.initFailed.connect(failures.append)
    _refuse_frames(viewer, monkeypatch)
    _paint(viewer, 3)
    assert viewer._fail_pending is True

    viewer._on_context_about_to_be_destroyed()
    _settle(qapp)

    assert viewer.has_failed is False
    assert failures == []


def test_a_context_loss_clears_the_refusal_count(qapp, monkeypatch) -> None:
    """Der neue Kontext baut seinen Framebuffer erst auf – alte Absagen zählen nicht."""
    viewer = GLReliefViewer()
    _refuse_frames(viewer, monkeypatch)
    _paint(viewer, 2)

    viewer._on_context_about_to_be_destroyed()

    assert viewer._refused_paints == 0
    assert viewer.has_failed is False


# ── Drift-Schutz: dokumentierte Renderbeweis-Sonde (#1010) ───────────────


_PROBE_VIEWER_API = (
    "set_mesh",
    "frameSwapped",
    "defaultFramebufferObject",
    "paintEvent",
    "paintGL",
    "cleanup_gl",
    "_has_rendered",
    "_refused_paints",
    "has_failed",
    "failure_reason",
)


def _documented_probe_source() -> str:
    """Der Python-Teil der Sonde aus ``TESTING.md`` (Heredoc im bash-Block)."""
    text = (Path(__file__).resolve().parent.parent / "TESTING.md").read_text(
        encoding="utf-8"
    )
    start = text.find("### Renderbeweis-Sonde")
    assert start != -1, (
        "Abschnitt „### Renderbeweis-Sonde\" in TESTING.md nicht gefunden – "
        "Überschrift geändert? Anker hier nachziehen."
    )
    body = text[start:]
    open_marker = body.find("<<'PY'\n")
    close_marker = body.find("\nPY\n", open_marker)
    assert open_marker != -1 and close_marker != -1, (
        "Heredoc der Sonde (<<'PY' … PY) in TESTING.md nicht gefunden – "
        "Codeblock umgebaut? Anker hier nachziehen."
    )
    return body[open_marker + len("<<'PY'\n") : close_marker]


#: Aufrufe der Sonde, die gegen die echte Signatur gebunden werden (#1010).
#: Beide nehmen ihre Argumente dort **positionell** entgegen; ein später
#: eingezogener ``*``-Trenner oder eine umsortierte ``HeightField``-Feldfolge
#: bliebe von einer reinen Namensprüfung unbemerkt.
_PROBE_CALL_TARGETS = {
    "HeightField": HeightField,
    "build_relief_mesh": build_relief_mesh,
}


def test_documented_probe_calls_bind_against_the_real_signatures() -> None:
    """Die Sonde muss auch in der **Aufrufform** passen, nicht nur in den Namen.

    Der Namenswächter unten sähe eine Umsortierung von ``HeightField`` oder ein
    hinter den ``*``-Trenner gezogenes ``quality`` nicht – die Prozedur bräche
    erst auf fremder Hardware, Wochen später. Gebunden wird mit Platzhaltern
    über ``inspect.signature``; ausgeführt wird nichts, GL ist nicht nötig.
    """
    import ast
    import inspect

    quelle = _documented_probe_source()
    gebunden: set[str] = set()
    for knoten in ast.walk(ast.parse(quelle)):
        if not isinstance(knoten, ast.Call) or not isinstance(knoten.func, ast.Name):
            continue
        ziel = _PROBE_CALL_TARGETS.get(knoten.func.id)
        if ziel is None:
            continue
        args = ["<platzhalter>"] * len(knoten.args)
        kwargs = {kw.arg: "<platzhalter>" for kw in knoten.keywords if kw.arg is not None}
        try:
            inspect.signature(ziel).bind_partial(*args, **kwargs)
        except TypeError as exc:
            raise AssertionError(
                f"Die Sonde in TESTING.md ruft {knoten.func.id} so nicht mehr "
                f"gültig auf ({exc}). Prozedur nachziehen."
            ) from exc
        gebunden.add(knoten.func.id)

    assert gebunden == set(_PROBE_CALL_TARGETS), (
        f"Erwartet gebundene Aufrufe {sorted(_PROBE_CALL_TARGETS)}, gefunden "
        f"{sorted(gebunden)} – Sonde umgebaut oder Anker zu eng?"
    )


def test_documented_render_proof_probe_matches_the_viewer_api(qapp) -> None:
    """Die Sonde in TESTING.md muss zur echten Viewer-API passen (#1010).

    Sie ist bewusst kein committetes Skript (Issue-Vorgabe) und läuft genau
    einmal, auf fremder Hardware, Wochen später – eine Umbenennung von
    ``_refused_paints`` fiele sonst erst dort auf, im ungünstigsten Moment.
    Geprüft wird beides: dass der Codeblock syntaktisch gültig ist, dass seine
    Importe aus ``bgremover`` existieren, und dass die ausgewerteten
    Viewer-Namen an einem echten Viewer vorhanden sind.
    """
    import ast
    import importlib

    quelle = _documented_probe_source()
    baum = ast.parse(quelle, filename="TESTING.md:Renderbeweis-Sonde")

    fehlende_importe: list[str] = []
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.ImportFrom) and (knoten.module or "").startswith(
            "bgremover"
        ):
            modul = importlib.import_module(knoten.module or "")
            fehlende_importe += [
                f"{knoten.module}.{alias.name}"
                for alias in knoten.names
                if not hasattr(modul, alias.name)
            ]
    assert not fehlende_importe, (
        f"Die Sonde in TESTING.md importiert {fehlende_importe} – so nicht "
        "mehr vorhanden. Prozedur nachziehen."
    )

    viewer = GLReliefViewer()
    fehlende_api = [name for name in _PROBE_VIEWER_API if not hasattr(viewer, name)]
    assert not fehlende_api, (
        f"Die Sonde in TESTING.md wertet {fehlende_api} aus – am Viewer nicht "
        "mehr vorhanden. Prozedur nachziehen."
    )
    ungenannt = [name for name in _PROBE_VIEWER_API if name not in quelle]
    assert not ungenannt, (
        f"{ungenannt} steht in dieser Liste, aber nicht mehr in der Sonde – "
        "die Liste beschreibt sonst eine Prozedur, die es so nicht gibt."
    )


def test_refusals_reach_the_container_as_the_documented_error_state(
    qapp, monkeypatch
) -> None:
    """Der Zustandsvertrag: [F], nicht [E] (UX §5).

    Verdrahtet ist das über das bestehende ``initFailed`` – der Wächter
    braucht dafür keinen eigenen Pfad in den Container.
    """
    view = Relief3DView()
    view.show_mesh(_mesh())
    viewer = view.viewer()
    if viewer is None:
        pytest.skip("Kein GL-Viewer konstruierbar")
    assert view.state == STATE_READY
    _refuse_frames(viewer, monkeypatch)

    _paint(viewer, 3)
    _settle(qapp)

    assert view.state == STATE_ERROR


def test_the_finding_leaves_qts_paint_delivery(qapp, monkeypatch) -> None:
    """Der Zustandswechsel darf nicht im eigenen Paint-Dispatch laufen (#1005).

    ``_fail`` blendet über ``initFailed`` die Ready-Seite aus – ein ``hide()``
    mitten in Qts Zustellung des gerade gemalten Widgets. Der Befund steht
    deshalb sofort fest (``_fail_pending`` sperrt weitere Bewertung), wird aber
    erst im nächsten Ereignisdurchlauf gemeldet.
    """
    viewer = GLReliefViewer()
    _refuse_frames(viewer, monkeypatch)

    _paint(viewer, 3)

    assert viewer._fail_pending is True
    assert viewer.has_failed is False

    _paint(viewer, 5)  # bis zur Zustellung zählt nichts weiter
    assert viewer._refused_paints == 3

    _settle(qapp)
    assert viewer.has_failed is True


def test_a_context_loss_also_clears_the_positive_witness(qapp, monkeypatch) -> None:
    """Der Freispruch gilt nur für den Kontext, der ihn gab (#1005).

    Bliebe ``_has_rendered`` über die Kontextzerstörung stehen, kehrte jeder
    Paint des Ersatzkontexts vor der Framebuffer-Prüfung um – und genau der
    Zustand, den dieser Beweis sucht, bliebe an ihm unentdeckt.
    """
    viewer = GLReliefViewer()
    viewer._on_frame_swapped()
    assert viewer._has_rendered is True

    viewer._on_context_about_to_be_destroyed()
    assert viewer._has_rendered is False

    _refuse_frames(viewer, monkeypatch)
    _paint(viewer, 3)
    _settle(qapp)

    assert viewer.has_failed is True


def test_a_lost_render_proof_is_not_rebuilt_on_every_change(qapp, monkeypatch) -> None:
    """Kein Neuaufbau-Zyklus auf einer dauerhaft render-unfähigen Anzeige (#1005).

    Ohne diese Bedingung baute jede Layer-/Inhaltsänderung einen kompletten
    ``QOpenGLWidget`` samt Kontext neu auf, und die UI spränge sichtbar
    zwischen leerer Ready-Fläche und Fehlerseite. Erst der ausdrückliche Retry
    ist der Weg zurück – analog zum Capability-Cache.
    """
    view = Relief3DView()
    view.show_mesh(_mesh())
    viewer = view.viewer()
    if viewer is None:
        pytest.skip("Kein GL-Viewer konstruierbar")
    _refuse_frames(viewer, monkeypatch)
    _paint(viewer, 3)
    _settle(qapp)
    assert view.state == STATE_ERROR

    view.show_mesh(_mesh())  # wie ein `refresh()` bei unverändertem Cache-Key

    assert view.state == STATE_ERROR
    assert view.viewer() is viewer

    view.allow_viewer_retry()
    view.show_mesh(_mesh())

    assert view.viewer() is not viewer


def test_the_settled_states_are_the_real_state_names(qapp) -> None:
    """Wächter gegen Drift der Zustandsnamen über Modulgrenzen (#1005).

    ``state`` ist als ``str`` typisiert – ein Tippfehler in ``screenshot3d``
    oder im Controller bliebe sonst still.
    """
    view = Relief3DView()
    seen = {view.state}
    for call in (view.show_unavailable, view.show_loading, view.show_error):
        call()
        seen.add(view.state)
    view.show_empty()
    seen.add(view.state)

    assert seen | {STATE_READY} >= SETTLED_STATES
    assert STATE_READY not in seen  # ohne Mesh nie erreicht


# ── Kontextwiederherstellung nach ``paintGL`` (#1024) ────────────────────
#
# Qt macht den Kontext vor ``paintGL`` aktuell und greift danach ohne
# Null-Prüfung auf ``currentContext()`` zu. Gibt die Garbage-Collection mitten
# im Nutzer-Paint ein fremdes ``QOpenGLWidget`` frei, räumt dessen ``reset()``
# per ``doneCurrent`` den aktuellen Kontext ab – Qt dereferenziert dann einen
# Nullzeiger (SIGSEGV, im Suite-Lauf unter ``xcb`` reproduziert). Der Viewer
# stellt seinen Kontext deshalb selbst wieder her. GL-frei geprüft über
# Attrappen für ``context``/``makeCurrent``/``currentContext``; die echte
# Nachstellung mit C++-Freigabe steht in ``test_viewer_3d_gl.py``.

class _FakeContextRegistry:
    """Ersetzt ``viewer_3d.QOpenGLContext``: ``currentContext`` liest ein Feld."""

    current: object = None

    @classmethod
    def currentContext(cls):  # noqa: N802 (Qt-API)
        return cls.current


def _viewer_with_fake_context(monkeypatch, *, context: object | None):
    """Ein ``paintGL``-fähiger Viewer ohne GL; ``makeCurrent`` wird protokolliert."""
    viewer = GLReliefViewer()
    calls: list[str] = []

    def make_current(self) -> None:
        calls.append("makeCurrent")
        _FakeContextRegistry.current = context  # wie Qt: danach ist er wieder aktuell

    monkeypatch.setattr(type(viewer), "context", lambda self: context)
    monkeypatch.setattr(type(viewer), "makeCurrent", make_current)
    _FakeContextRegistry.current = context
    monkeypatch.setattr(viewer_3d, "QOpenGLContext", _FakeContextRegistry)
    viewer._gl_ready = True
    return viewer, calls


def test_paint_gl_reasserts_its_context_after_a_foreign_done_current(
    qapp, monkeypatch
) -> None:
    """Der Kern von #1024: Nach dem Nutzer-Paint ist der Kontext wieder der eigene."""
    own = object()
    viewer, calls = _viewer_with_fake_context(monkeypatch, context=own)

    def paint_and_lose_context() -> None:
        # Was ein fremdes ``reset()`` mitten im Paint tut: ``doneCurrent``.
        _FakeContextRegistry.current = None
    viewer._paint_gl = paint_and_lose_context

    viewer.paintGL()

    assert calls == ["makeCurrent"]
    assert viewer.has_failed is False


def test_paint_gl_leaves_an_intact_context_alone(qapp, monkeypatch) -> None:
    """Negativkontrolle: Ohne Verlust kein zusätzliches ``makeCurrent``."""
    own = object()
    viewer, calls = _viewer_with_fake_context(monkeypatch, context=own)
    viewer._paint_gl = lambda: None

    viewer.paintGL()

    assert calls == []


def test_the_context_is_reasserted_even_when_painting_fails(qapp, monkeypatch) -> None:
    """Qts Nachlauf kommt auch nach einer Ausnahme – die Wiederherstellung ebenso."""
    own = object()
    viewer, calls = _viewer_with_fake_context(monkeypatch, context=own)
    failures: list[str] = []
    viewer.initFailed.connect(failures.append)

    def paint_lose_and_raise() -> None:
        _FakeContextRegistry.current = None
        raise RuntimeError("Attrappe")
    viewer._paint_gl = paint_lose_and_raise

    viewer.paintGL()

    assert calls == ["makeCurrent"]
    assert viewer.has_failed is True
    assert failures and "paintGL: RuntimeError" in failures[0]


def test_a_viewer_without_context_never_calls_make_current(qapp, monkeypatch) -> None:
    """Ohne eigenen Kontext gibt es nichts wiederherzustellen – und nichts zu riskieren."""
    viewer, calls = _viewer_with_fake_context(monkeypatch, context=None)
    viewer._paint_gl = lambda: None

    viewer.paintGL()

    assert calls == []


def test_the_early_return_of_a_failed_viewer_still_reasserts(qapp, monkeypatch) -> None:
    """Review PR #1026: Auch der frühe Rückweg liegt in Qts ``render()``.

    Ein fehlgeschlagener oder noch nicht bereiter Viewer malt nicht – Qts
    Nachlauf mit dem ungeprüften ``currentContext()`` folgt trotzdem. Die
    Wachklausel steht deshalb **im** ``try``; ohne das liefe die
    Wiederherstellung hier nie.
    """
    own = object()
    viewer, calls = _viewer_with_fake_context(monkeypatch, context=own)
    viewer._paint_gl = lambda: pytest.fail("ein fehlgeschlagener Viewer malt nicht")
    viewer._failed = True
    _FakeContextRegistry.current = None  # Verlust vor dem Aufruf, etwa aus einer Collection

    viewer.paintGL()

    assert calls == ["makeCurrent"]


def test_a_failed_restore_leaves_a_trace_in_the_log(qapp, monkeypatch, caplog) -> None:
    """Review PR #1026: Ein gescheiterter Restore ist kein stiller Fall mehr.

    Beide Ausprägungen: ``makeCurrent`` wirft, oder es kehrt still zurück, ohne
    den Kontext zu setzen (Qt bei nicht initialisiertem Widget). Kein
    ``_fail`` – nur die Log-Zeile, die beim nächsten gdb-Lauf den Weg spart.
    """
    import logging

    own = object()
    viewer, calls = _viewer_with_fake_context(monkeypatch, context=own)
    monkeypatch.setattr(type(viewer), "makeCurrent", lambda self: calls.append("still"))
    _FakeContextRegistry.current = None
    viewer._paint_gl = lambda: None

    with caplog.at_level(logging.WARNING, logger="BgRemover"):
        viewer.paintGL()
    assert calls == ["still"]
    assert viewer.has_failed is False
    assert any("nicht wiederhergestellt" in r.getMessage() for r in caplog.records)

    caplog.clear()

    def raising(self) -> None:
        raise RuntimeError("Attrappe")
    monkeypatch.setattr(type(viewer), "makeCurrent", raising)
    with caplog.at_level(logging.WARNING, logger="BgRemover"):
        viewer.paintGL()
    assert viewer.has_failed is False
    assert any("makeCurrent scheiterte: Attrappe" in r.getMessage() for r in caplog.records)
