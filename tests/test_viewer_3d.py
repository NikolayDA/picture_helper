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
from bgremover.viewer_3d import GLReliefViewer, Relief3DView

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
    assert view.state == "ready"
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
