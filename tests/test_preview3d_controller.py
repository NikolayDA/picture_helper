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
from bgremover.viewer_3d import STATE_ERROR, STATE_LOADING, STATE_READY, Relief3DView


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
        self.errors: list[Callable] = []
        self.cancelled = 0

    def start_mesh_build(self, field, quality, generation_id, on_done, *,
                         on_error=None, physical_size_mm=None) -> bool:
        self.calls.append((generation_id, on_done))
        self.errors.append(on_error)
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
    checked: list[RendererCapability] = []
    ctrl.capabilityChecked.connect(checked.append)
    ctrl.set_active(True)
    assert view.state == "unavailable"
    assert worker.calls == []
    assert checked == [_unavailable()]


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
    """Ein verspätetes Ergebnis erreicht weder Anzeige noch Cache.

    Geprüft wird über die beobachtbare Wirkung statt über ``ctrl._cache_mesh``
    (#869): Was der Controller anzeigt, geht durch ``view.show_mesh`` – und was
    er gecacht hat, zeigt sich daran, welches Mesh ein Cache-Treffer erneut
    anzeigt (ohne neuen Build).
    """
    ctrl, canvas, worker, view = _make(qapp, _ok)
    shown: list[object] = []
    real_show_mesh = view.show_mesh

    def _record(mesh: object) -> None:
        shown.append(mesh)
        real_show_mesh(mesh)                  # type: ignore[arg-type]

    view.show_mesh = _record                  # type: ignore[method-assign]

    ctrl.set_active(True)
    ctrl._start_build()                       # Build der Generation 1 (K1)
    gen1, cb1 = worker.calls[0]
    # Inhalt ändert sich, während Generation 1 „läuft": _evaluate erhöht die
    # Generation *sofort* und bricht den laufenden Build ab.
    canvas.content_revision = 2
    ctrl.refresh()
    ctrl._start_build()                       # Build der Generation 2 (K2)
    gen2, cb2 = worker.calls[1]
    assert gen1 != gen2
    fresh = build_relief_mesh(_field(), MeshQuality.STANDARD)
    cb2(fresh, gen2)                          # aktuelles Ergebnis
    assert view.state == "ready"
    assert shown == [fresh]

    # Das verspätete Ergebnis der Generation 1 wird verworfen – nie angezeigt …
    stale = build_relief_mesh(_field(), MeshQuality.STANDARD)
    cb1(stale, gen1)
    assert shown == [fresh]
    assert view.state == "ready"

    # … und nie gecacht: der Cache-Treffer zeigt weiterhin ``fresh``, ohne
    # dass ein dritter Build angefordert wird.
    ctrl.refresh()
    assert len(worker.calls) == 2
    assert shown == [fresh, fresh]


def test_supersede_cancels_running_build(qapp) -> None:
    ctrl, canvas, worker, _view = _make(qapp, _ok)
    ctrl.set_active(True)
    ctrl._start_build()
    cancels_before = worker.cancelled
    canvas.content_revision = 5
    ctrl.refresh()                            # _evaluate bricht laufenden Build ab
    assert worker.cancelled > cancels_before


def test_mesh_build_error_shows_error_state(qapp) -> None:
    ctrl, _canvas, worker, view = _make(qapp, _ok)
    ctrl.set_active(True)
    ctrl._start_build()
    gen, _cb = worker.calls[0]
    on_error = worker.errors[0]
    assert on_error is not None
    on_error("Kaputt", gen)                   # Worker-Fehler der aktuellen Generation
    assert view.state == "error"


def test_stale_mesh_error_is_ignored(qapp) -> None:
    ctrl, canvas, worker, view = _make(qapp, _ok)
    ctrl.set_active(True)
    ctrl._start_build()
    gen1, _cb1 = worker.calls[0]
    stale_error = worker.errors[0]
    canvas.content_revision = 2
    ctrl.refresh()
    ctrl._start_build()
    _deliver(ctrl, worker, index=1)
    assert view.state == "ready"
    stale_error("alter Fehler", gen1)         # veraltete Generation → ignorieren
    assert view.state == "ready"


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


# ── Asynchroner Renderbeweis: ready → error (#1004/#1005, Testlücke #1044) ──


def _ready(qapp) -> tuple[Preview3DController, _FakeCanvas, _FakeWorker, Relief3DView]:
    """Controller mit erfolgreich gebautem und angezeigtem Mesh."""
    ctrl, canvas, worker, view = _make(qapp, _ok)
    ctrl.set_active(True)
    ctrl._start_build()
    _deliver(ctrl, worker)
    assert view.state == STATE_READY
    return ctrl, canvas, worker, view


def _render_proof_fails(view: Relief3DView) -> None:
    """Die Absage auf dem Produktivpfad: ``GLReliefViewer._fail`` → ``initFailed``
    → ``Relief3DView.show_error``. Bewusst nicht ``view.show_error()`` allein –
    das verschöbe nur den Container, der Viewer bliebe gesund, und
    ``_ensure_viewer`` (#1005) verhielte sich anders (Review PR #1051)."""
    viewer = view.viewer()
    assert viewer is not None and not viewer.has_failed
    viewer._fail("Qt hält keinen Widget-Framebuffer")
    assert viewer.has_failed
    assert view.state == STATE_ERROR


def test_async_error_after_ready_lets_the_next_build_show_loading(qapp) -> None:
    """Der Renderbeweis des Viewers zieht den Zustand **asynchron** von ``ready``
    auf ``error`` (kein Widget-Framebuffer), nachdem ``_show_cached`` gelaufen
    ist. Ein mitgeführtes „zeigt ein Mesh"-Flag behauptete danach weiter das
    Gegenteil und unterdrückte die Ladeseite über der Fehlerseite; seit #1004
    fragt der Controller die Ansicht direkt.

    Der fertige Build landet danach wieder auf der Fehlerseite: Ein Viewer ohne
    Renderbeweis wird nicht bei jeder Inhaltsänderung neu gebaut (#1005) –
    erst der ausdrückliche Retry gibt den Neuaufbau frei.
    """
    ctrl, canvas, worker, view = _ready(qapp)
    failed_viewer = view.viewer()
    _render_proof_fails(view)
    canvas.content_revision = 2
    ctrl.refresh()
    assert view.state == STATE_LOADING  # der #1004-Zweig: state != ready
    ctrl._start_build()
    _deliver(ctrl, worker)
    assert view.state == STATE_ERROR  # #1005: kein stiller Neuaufbau
    assert view.viewer() is failed_viewer

    ctrl.retry()
    assert view.state == STATE_LOADING
    ctrl._start_build()
    _deliver(ctrl, worker)
    assert view.state == STATE_READY
    assert view.viewer() is not failed_viewer
    assert len(worker.calls) == 3


def test_displayed_mesh_stays_visible_while_rebuilding(qapp) -> None:
    """Gegenkontrolle: Ohne Absage bleibt das angezeigte Mesh während des
    Rebuilds stehen (kein Schwarzbild) – die Ladeseite erscheint nur über
    einem Nicht-``ready``-Zustand."""
    ctrl, canvas, worker, view = _ready(qapp)
    canvas.content_revision = 2
    ctrl.refresh()
    assert view.state == STATE_READY
    ctrl._start_build()
    _deliver(ctrl, worker)
    assert view.state == STATE_READY


def test_cache_hit_after_async_error_stays_on_error_until_retry(qapp) -> None:
    """Nach einer asynchronen Abstufung startet ein Cache-Treffer keinen Build,
    zeigt das gecachte Mesh aber auch nicht wieder an: Der Viewer hat den
    Renderbeweis verloren und wird erst nach ``retry`` neu aufgebaut (#1005)."""
    ctrl, _canvas, worker, view = _ready(qapp)
    _render_proof_fails(view)
    ctrl.refresh()
    assert view.state == STATE_ERROR
    assert len(worker.calls) == 1
    ctrl.retry()
    assert view.state == STATE_LOADING
    ctrl._start_build()
    assert len(worker.calls) == 2


# ── Ränder von Build-Start und Ergebnisübernahme (Restzeilen aus #1044) ──


def test_debounced_build_does_not_start_after_deactivation(qapp) -> None:
    """Feuert der Debounce nach dem Verlassen des 3D-Modus, startet kein Build."""
    ctrl, _canvas, worker, _view = _make(qapp, _ok)
    ctrl.set_active(True)
    ctrl.set_active(False)
    ctrl._start_build()
    assert worker.calls == []


def test_field_vanishing_before_build_start_shows_empty(qapp) -> None:
    """Zwischen Entprellung und Build-Start kann das Höhenfeld verschwinden
    (Ebene gelöscht): dann Leerseite statt Build mit ``None``."""
    ctrl, canvas, worker, view = _make(qapp, _ok)
    ctrl.set_active(True)
    assert view.state == STATE_LOADING
    canvas._field = None
    ctrl._start_build()
    assert worker.calls == []
    assert view.state == "empty"


def test_mesh_arriving_after_deactivation_is_not_shown(qapp) -> None:
    """Ein Ergebnis, das nach dem Wechsel zurück auf 2D eintrifft, wird weder
    angezeigt noch gecacht – ein späteres Aktivieren baut neu."""
    ctrl, _canvas, worker, view = _make(qapp, _ok)
    ctrl.set_active(True)
    ctrl._start_build()
    ctrl.set_active(False)
    _deliver(ctrl, worker)
    assert view.state == STATE_LOADING  # unverändert, kein Mesh übernommen
    ctrl.set_active(True)
    ctrl._start_build()
    assert len(worker.calls) == 2  # kein Cache-Treffer aus dem verworfenen Ergebnis
