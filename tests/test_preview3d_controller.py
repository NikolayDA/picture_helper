"""Tests der 3D-Workflow-/State-/Cache-Orchestrierung (#594, Epic #582).

Fake-Canvas + Fake-WorkerController: die Gating-, Generation- und Cache-Logik
wird ohne GL-Kontext getestet. Der Debounce-Timer wird durch direkten Aufruf von
``_start_build`` überbrückt (das Fire-Verhalten des ``QTimer`` gehört zu Qt).
"""
from __future__ import annotations

from collections.abc import Callable

import numpy as np

from bgremover.height_map import HEIGHT_MAX_16BIT, HeightField
from bgremover.preview3d_capability import UNAVAILABLE_KEY, RendererCapability
from bgremover.preview3d_controller import Preview3DController
from bgremover.relief_mesh import MeshQuality, build_relief_mesh
from bgremover.viewer_3d import Relief3DView


def _field(value: int = 5000, size: int = 24) -> HeightField:
    return HeightField(
        np.full((size, size), value, np.uint16),
        np.full((size, size), 255, np.uint8),
        HEIGHT_MAX_16BIT,
    )


class _FakeCanvas:
    def __init__(self) -> None:
        self._field: HeightField | None = _field()
        self.content_revision = 1
        self._mm: tuple[float, float] | None = None

    def height_preview_field(self) -> HeightField | None:
        return self._field

    def physical_size_mm(self) -> tuple[float, float] | None:
        return self._mm


class _FakeWorker:
    def __init__(self) -> None:
        self.calls: list[tuple[int, Callable]] = []
        self.cancelled = 0

    def start_mesh_build(self, field, quality, generation_id, on_done, *,
                         physical_size_mm=None) -> bool:
        self.calls.append((generation_id, on_done))
        return True

    def cancel_mesh_build(self) -> None:
        self.cancelled += 1


def _ok() -> RendererCapability:
    return RendererCapability(ok=True, diagnostic="test")


def _unavailable() -> RendererCapability:
    return RendererCapability(ok=False, error_key=UNAVAILABLE_KEY)


def _make(qapp, capability) -> tuple[Preview3DController, _FakeCanvas, _FakeWorker,
                                     Relief3DView]:
    view = Relief3DView()
    canvas = _FakeCanvas()
    worker = _FakeWorker()
    ctrl = Preview3DController(view, canvas, worker, capability_probe=capability)
    return ctrl, canvas, worker, view


def _deliver(ctrl: Preview3DController, worker: _FakeWorker, index: int = -1) -> None:
    """Simuliert den erfolgreichen Worker-Abschluss des `index`-ten Builds."""
    generation, on_done = worker.calls[index]
    mesh = build_relief_mesh(_field(), MeshQuality.STANDARD)
    on_done(mesh, generation)


# ── Gating ────────────────────────────────────────────────────────────────
def test_unavailable_capability_shows_unavailable(qapp) -> None:
    ctrl, _canvas, worker, view = _make(qapp, _unavailable)
    ctrl.set_active(True)
    assert view.state == "unavailable"
    assert worker.calls == []


def test_no_height_field_shows_empty(qapp) -> None:
    ctrl, canvas, worker, view = _make(qapp, _ok)
    canvas._field = None
    ctrl.set_active(True)
    assert view.state == "empty"
    assert worker.calls == []


def test_active_with_field_schedules_build_then_shows_mesh(qapp) -> None:
    ctrl, _canvas, worker, view = _make(qapp, _ok)
    ctrl.set_active(True)
    assert view.state == "loading"
    ctrl._start_build()            # Debounce überbrücken
    assert len(worker.calls) == 1
    _deliver(ctrl, worker)
    assert view.state == "ready"


# ── Generation-/Stale-Schutz ───────────────────────────────────────────────
def test_stale_generation_is_discarded(qapp) -> None:
    ctrl, canvas, worker, view = _make(qapp, _ok)
    ctrl.set_active(True)
    ctrl._start_build()                       # Generation 1
    stale_gen, stale_cb = worker.calls[0]
    canvas.content_revision = 2
    ctrl._start_build()                       # Generation 2
    _deliver(ctrl, worker, index=1)           # aktuelles Ergebnis
    assert view.state == "ready"
    # Verspätetes Ergebnis der Generation 1 darf den Zustand nicht überschreiben.
    mesh = build_relief_mesh(_field(), MeshQuality.STANDARD)
    stale_cb(mesh, stale_gen)
    assert ctrl._generation == 2


# ── Cache ──────────────────────────────────────────────────────────────────
def test_unchanged_state_reuses_cache_without_rebuild(qapp) -> None:
    ctrl, _canvas, worker, view = _make(qapp, _ok)
    ctrl.set_active(True)
    ctrl._start_build()
    _deliver(ctrl, worker)
    assert len(worker.calls) == 1
    ctrl.refresh()                 # nichts Geometriebestimmendes geändert
    assert view.state == "ready"
    assert len(worker.calls) == 1  # kein zweiter Build


def test_quality_change_triggers_rebuild(qapp) -> None:
    ctrl, _canvas, worker, view = _make(qapp, _ok)
    ctrl.set_active(True)
    ctrl._start_build()
    _deliver(ctrl, worker)
    ctrl.set_quality(MeshQuality.HIGH)
    assert view.state in ("loading", "ready")  # loading, weil noch angezeigt bleibt
    ctrl._start_build()
    assert len(worker.calls) == 2


def test_content_change_triggers_rebuild(qapp) -> None:
    ctrl, canvas, worker, _view = _make(qapp, _ok)
    ctrl.set_active(True)
    ctrl._start_build()
    _deliver(ctrl, worker)
    canvas.content_revision = 99
    ctrl.refresh()
    ctrl._start_build()
    assert len(worker.calls) == 2


def test_exaggeration_and_light_are_uniforms_no_rebuild(qapp) -> None:
    ctrl, _canvas, worker, _view = _make(qapp, _ok)
    ctrl.set_active(True)
    ctrl._start_build()
    _deliver(ctrl, worker)
    ctrl.set_exaggeration(4.0)
    ctrl.set_light(120.0, 60.0)
    assert len(worker.calls) == 1  # kein Rebuild


# ── Deaktivierung / Retry ───────────────────────────────────────────────────
def test_deactivate_cancels_running_build(qapp) -> None:
    ctrl, _canvas, worker, _view = _make(qapp, _ok)
    ctrl.set_active(True)
    ctrl.set_active(False)
    assert worker.cancelled >= 1


def test_retry_reevaluates(qapp) -> None:
    state = {"cap": _unavailable()}
    ctrl, _canvas, _worker, view = _make(qapp, lambda: state["cap"])
    ctrl.set_active(True)
    assert view.state == "unavailable"
    state["cap"] = _ok()
    ctrl.retry()
    assert view.state == "loading"
