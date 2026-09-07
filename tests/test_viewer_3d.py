"""Tests des 3D-Viewer-Containers und der Fallback-Zustände (#593, Epic #582).

Der Zustandsautomat (Empty/Unavailable/Loading/Error/Ready) und der Decimation-
Badge sind ohne GL-Kontext prüfbar; der GL-Viewer selbst rendert im
Offscreen-CI nicht (echter Fallbackpfad), seine Konstruktion/Fehlerbehandlung
propagiert aber nie eine Exception.
"""
from __future__ import annotations

import numpy as np
import pytest
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent

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


def test_a_context_loss_clears_the_refusal_count(qapp, monkeypatch) -> None:
    """Der neue Kontext baut seinen Framebuffer erst auf – alte Absagen zählen nicht."""
    viewer = GLReliefViewer()
    _refuse_frames(viewer, monkeypatch)
    _paint(viewer, 2)

    viewer._on_context_about_to_be_destroyed()

    assert viewer._refused_paints == 0
    assert viewer.has_failed is False


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
