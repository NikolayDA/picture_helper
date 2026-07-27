"""GL-Ressourcen-Langzeit- und Lebenszyklustests der 3D-Vorschau (#684, Epic #680).

Sichert den in PR #676 behobenen Lebenszyklus automatisiert ab: ``GLReliefViewer``
gab beim (Wieder-)Upload die vorherigen Puffer/VAO nicht frei, verwaiste GL-Objekte
akkumulierten über die Sitzung.

Gemessen wird der in :mod:`scripts.gl_stress_probe` festgelegte Wert – die Zahl
lebender, vom Viewer besessener GL-Objekte (drei Puffer + VAO) – über deutlich
mehr als 100 Aktualisierungszyklen und mit kleinen, typischen und großen
HEIGHT-Daten. Die Messsonde selbst ist geteilt: Tests und der reproduzierbare
Nachweislauf (``make gl-stress``) benutzen exakt denselben Code, damit die
CI-Aussage und der Release-Nachweis nicht auseinanderdriften.

Die Tests laufen **ohne** GL-Kontext (Offscreen-CI hat keinen renderbaren FBO):
der echte Kontrollfluss aus ``_ensure_buffers``/``_release_gl_objects``/
``cleanup_gl`` wird gefahren, nur die GL-Objekte selbst sind instrumentierte
Attrappen. Der Nachweis unter echtem GL liegt in ``tests/test_viewer_3d_gl.py``
(Marker ``gl_smoke``) und in der Hardware-Prozedur des Testberichts.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from bgremover import viewer_3d
from bgremover.height_map import HeightField
from bgremover.preview3d_capability import UNAVAILABLE_KEY, RendererCapability
from bgremover.preview3d_controller import Preview3DController
from bgremover.relief_mesh import MeshQuality, build_relief_mesh
from bgremover.viewer_3d import (
    GLReliefViewer,
    Relief3DView,
    gl_resource_stats,
    reset_gl_resource_stats,
)

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "gl_stress_probe", ROOT / "scripts" / "gl_stress_probe.py"
)
assert _SPEC is not None and _SPEC.loader is not None
probe = importlib.util.module_from_spec(_SPEC)
# Vor dem Ausführen registrieren: ``@dataclass`` schlägt das eigene Modul in
# ``sys.modules`` nach (Typauflösung) und scheitert sonst mit AttributeError.
sys.modules[_SPEC.name] = probe
_SPEC.loader.exec_module(probe)

#: Deutlich über der in #684 geforderten Mindestzahl von 100 Zyklen.
CYCLES = 110

#: Klein / typisch / groß. Die großen Quellen laufen bewusst mit ``REDUCED``:
#: die Decimation greift vor der float-Expansion, das Vertexbudget bleibt also
#: testtauglich, während der Lade-/Ersetzungspfad derselbe ist.
SIZES = (
    ("klein", 64, MeshQuality.REDUCED),
    ("typisch", 512, MeshQuality.REDUCED),
    ("gross", 2048, MeshQuality.REDUCED),
)


def _mesh(size: int, quality: MeshQuality = MeshQuality.REDUCED) -> object:
    return build_relief_mesh(probe.build_field(size), quality)


@pytest.fixture(autouse=True)
def _fresh_counters():
    """Jeder Test misst ab null – die Zähler sind prozessweit."""
    reset_gl_resource_stats()
    yield
    reset_gl_resource_stats()


# ── Langzeitlauf: kein unbeschränkter Anstieg ────────────────────────────


@pytest.mark.parametrize(("label", "size", "quality"), SIZES)
def test_long_run_keeps_live_gl_objects_bounded(qapp, label, size, quality) -> None:
    """>100 Zyklen je Datensatzgröße halten die lebenden GL-Objekte konstant.

    Regression zu PR #676: ohne Freigabe im Upload-Pfad wüchse die Zahl je Zyklus
    um vier Objekte. Geprüft wird nicht „kein Absturz", sondern der Zählerstand
    nach der Aufwärmphase gegen den Stand nach dem letzten Zyklus.
    """
    result = probe.run_fake_scenario(label, [_mesh(size, quality)], CYCLES, f"{size}×{size}")

    assert result.findings == ()
    assert result.growth == 0
    assert result.max_live <= probe.MAX_LIVE_PER_VIEWER
    assert result.live_after_cleanup == 0
    assert result.created_total == result.destroyed_total == CYCLES * 4


def test_long_run_with_changing_height_data_is_bounded(qapp) -> None:
    """Wiederholtes Laden/Ersetzen *unterschiedlich großer* HEIGHT-Daten leckt nicht."""
    meshes = [_mesh(size, quality) for _, size, quality in SIZES]

    result = probe.run_fake_scenario("wechselnd", meshes, CYCLES, "gemischt")

    assert result.findings == ()
    assert result.growth == 0
    assert result.live_after_cleanup == 0


def test_probe_detects_a_missing_release_path(qapp, monkeypatch) -> None:
    """Negativkontrolle: ohne Freigabe im Upload-Pfad meldet die Messung einen Befund.

    Ohne diesen Test wäre der grüne Langzeitlauf wertlos – er könnte auch dann
    grün sein, wenn die Messung gar nichts sieht. Hier wird der Zustand *vor*
    PR #676 nachgestellt (``_release_gl_objects`` im Upload-Pfad wirkungslos).
    """
    real_release = GLReliefViewer._release_gl_objects
    calls = {"n": 0}

    def leaky_release(self) -> None:
        # Nur der erste Aufruf (aus ``_ensure_buffers``) fällt aus; ``cleanup_gl``
        # räumt danach weiterhin auf – genau das Bild des alten Fehlers.
        calls["n"] += 1
        if calls["n"] <= CYCLES:
            return
        real_release(self)

    monkeypatch.setattr(GLReliefViewer, "_release_gl_objects", leaky_release)

    result = probe.run_fake_scenario("leck", [_mesh(64)], CYCLES, "64×64")

    assert result.findings, "Die Sonde muss ein Leck erkennen"
    assert result.growth > 0
    assert result.max_live > probe.MAX_LIVE_PER_VIEWER


# ── Freigabepfad: genau einmal, nie doppelt, nie danach benutzt ─────────


def test_every_created_object_is_released_exactly_once(qapp) -> None:
    """Zu jedem erfolgreichen Aufbau läuft genau ein Freigabepfad."""
    ledger = probe.ResourceLedger()
    with probe.tracked_gl_resources(ledger):
        viewer = GLReliefViewer()
        mesh = _mesh(64)
        for _ in range(5):
            viewer.set_mesh(mesh)
            viewer._ensure_buffers()
        viewer.cleanup_gl()

    assert ledger.created == ledger.destroyed == 20
    assert ledger.double_destroys == []
    assert ledger.use_after_destroy == []
    assert ledger.live == 0


def test_repeated_cleanup_does_not_double_free(qapp) -> None:
    """``cleanup_gl`` ist idempotent – kein zweiter ``destroy`` auf demselben Objekt."""
    ledger = probe.ResourceLedger()
    with probe.tracked_gl_resources(ledger):
        viewer = GLReliefViewer()
        viewer.set_mesh(_mesh(64))
        viewer._ensure_buffers()
        viewer.cleanup_gl()
        viewer.cleanup_gl()
        viewer._release_gl_objects()

    assert ledger.double_destroys == []
    assert ledger.destroyed == 4
    assert gl_resource_stats().live == 0


def test_stats_report_a_leak_when_release_is_skipped(qapp, monkeypatch) -> None:
    """Der Zähler ist ein echter Nachweis: übersprungene Freigabe bleibt sichtbar."""
    ledger = probe.ResourceLedger()
    monkeypatch.setattr(GLReliefViewer, "_release_gl_objects", lambda self: None)
    with probe.tracked_gl_resources(ledger):
        viewer = GLReliefViewer()
        viewer.set_mesh(_mesh(64))
        viewer._ensure_buffers()
        viewer.cleanup_gl()

    assert gl_resource_stats().live == 4


# ── Fehler-/Randpfade ───────────────────────────────────────────────────


def test_upload_without_pending_mesh_creates_nothing(qapp) -> None:
    """Ein Frame ohne neues Mesh alloziert nichts neu (keine Churn-Quelle)."""
    ledger = probe.ResourceLedger()
    with probe.tracked_gl_resources(ledger):
        viewer = GLReliefViewer()
        viewer.set_mesh(_mesh(64))
        viewer._ensure_buffers()
        for _ in range(50):
            viewer._ensure_buffers()

        assert ledger.created == 4
        assert viewer.gl_object_count == 4
        viewer.cleanup_gl()

    assert ledger.live == 0


def test_empty_height_data_uploads_and_releases_cleanly(qapp) -> None:
    """Vollständig ungedeckte Höhendaten (0 Dreiecke) werfen nicht und lecken nicht."""
    field = probe.build_field(64, empty_coverage=True)
    mesh = build_relief_mesh(field, MeshQuality.REDUCED)
    ledger = probe.ResourceLedger()
    with probe.tracked_gl_resources(ledger):
        viewer = GLReliefViewer()
        for _ in range(10):
            viewer.set_mesh(mesh)
            viewer._ensure_buffers()

        assert viewer._index_count == 0
        viewer.cleanup_gl()

    assert ledger.created == ledger.destroyed == 40
    assert not viewer.has_failed


def test_failed_buffer_creation_leaves_no_orphans(qapp, monkeypatch) -> None:
    """Scheitert die VAO-Erzeugung, bleibt kein verwaistes Objekt zurück."""
    ledger = probe.ResourceLedger()

    class _FailingVao(probe.TrackedGLResource):
        def create(self) -> bool:
            return False

    with probe.tracked_gl_resources(ledger):
        monkeypatch.setattr(
            viewer_3d, "QOpenGLVertexArrayObject",
            lambda *a, **k: _FailingVao(ledger, "vao-fail"),
        )
        viewer = GLReliefViewer()
        for _ in range(20):
            viewer.set_mesh(_mesh(64))
            viewer._ensure_buffers()

        # Der fehlgeschlagene VAO wird verworfen (``_vao is None``); der Viewer
        # hält dann nur die drei Puffer – und genau die werden freigegeben.
        assert viewer.gl_object_count == 3
        viewer.cleanup_gl()

    assert viewer.gl_object_count == 0
    assert ledger.double_destroys == []
    # Die 20 nicht übernommenen VAO-Attrappen bleiben als bekannte Differenz
    # stehen – sie gehören dem Viewer nie, Qt gibt sie mit dem Parent frei.
    assert ledger.destroyed == 20 * 3


def test_context_loss_releases_and_schedules_reupload(qapp) -> None:
    """Kontextverlust gibt frei und lädt im neuen Kontext erneut hoch – ohne Wachstum."""
    ledger = probe.ResourceLedger()
    with probe.tracked_gl_resources(ledger):
        viewer = GLReliefViewer()
        mesh = _mesh(64)
        viewer.set_mesh(mesh)
        viewer._ensure_buffers()
        for _ in range(30):
            viewer._on_context_about_to_be_destroyed()

            assert viewer.gl_object_count == 0
            assert viewer._pending_mesh is mesh  # Reupload ist eingeplant

            viewer._gl_ready = True
            viewer._ensure_buffers()

            assert viewer.gl_object_count == 4
        viewer.cleanup_gl()

    assert ledger.created == ledger.destroyed
    assert ledger.use_after_destroy == []


def test_close_while_update_is_pending_leaves_nothing(qapp) -> None:
    """Schließen während/kurz nach einer Aktualisierung gibt alles frei."""
    ledger = probe.ResourceLedger()
    with probe.tracked_gl_resources(ledger):
        viewer = GLReliefViewer()
        for _ in range(20):
            viewer.set_mesh(_mesh(64))
            viewer._ensure_buffers()
            viewer.set_mesh(_mesh(64))   # neuer Upload eingeplant, noch nicht gefahren
            viewer.cleanup_gl()

    assert ledger.created == ledger.destroyed
    assert gl_resource_stats().live == 0


def test_paint_before_initialization_allocates_nothing(qapp) -> None:
    """Ein Frame vor ``initializeGL`` (kein Kontext) alloziert nichts und wirft nicht."""
    ledger = probe.ResourceLedger()
    with probe.tracked_gl_resources(ledger):
        viewer = GLReliefViewer()
        viewer.set_mesh(_mesh(64))
        viewer.paintGL()   # _gl_ready ist False → früher Rücksprung

    assert ledger.created == 0
    assert viewer.gl_object_count == 0
    assert not viewer.has_failed


def test_cleanup_on_destroyed_widget_does_not_raise(qapp, monkeypatch) -> None:
    """Ein bereits zerstörtes Widget führt beim Aufräumen nicht zur Ausnahme."""
    viewer = GLReliefViewer()

    def deleted(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("wrapped C/C++ object of type GLReliefViewer has been deleted")

    monkeypatch.setattr(GLReliefViewer, "makeCurrent", deleted, raising=False)
    monkeypatch.setattr(GLReliefViewer, "doneCurrent", deleted, raising=False)

    viewer.cleanup_gl()  # darf nicht werfen

    assert viewer.gl_object_count == 0


# ── Container-/Controller-Ebene: Öffnen, Schließen, 2D↔3D ───────────────


def test_view_reuses_one_viewer_across_many_show_cycles(qapp) -> None:
    """Wiederholtes Anzeigen erzeugt keinen zweiten Viewer (und keine zweite Puffergarnitur)."""
    view = Relief3DView()
    mesh = _mesh(64)
    view.show_mesh(mesh)
    first = view.viewer()
    for _ in range(CYCLES):
        view.show_mesh(mesh)

    assert view.viewer() is first
    assert view.state == "ready"


def test_view_cleanup_and_reopen_cycles_stay_bounded(qapp) -> None:
    """Projekt öffnen → schließen → erneut öffnen häuft keine GL-Objekte an."""
    ledger = probe.ResourceLedger()
    with probe.tracked_gl_resources(ledger):
        view = Relief3DView()
        mesh = _mesh(64)
        for _ in range(CYCLES):
            view.show_mesh(mesh)
            viewer = view.viewer()
            assert viewer is not None
            viewer._ensure_buffers()
            view.show_empty()
            view.cleanup()   # Projektwechsel/Schließen

            assert viewer.gl_object_count == 0

    assert ledger.created == ledger.destroyed == CYCLES * 4
    assert ledger.double_destroys == []


class _FakeCanvas:
    """Minimaler Canvas-Vertrag für den Controller (wie test_preview3d_controller)."""

    def __init__(self) -> None:
        self.content_revision = 1
        self._field = probe.build_field(64)

    def height_preview_field(self) -> HeightField | None:
        return self._field

    def physical_size_mm(self) -> tuple[float, float] | None:
        return None


class _FakeWorker:
    def __init__(self) -> None:
        self.calls: list[tuple[int, object]] = []
        self.cancelled = 0

    def start_mesh_build(self, field, quality, generation_id, on_done, *,
                         on_error=None, physical_size_mm=None) -> bool:
        self.calls.append((generation_id, on_done))
        return True

    def cancel_mesh_build(self) -> None:
        self.cancelled += 1


def test_2d_3d_toggle_cycles_do_not_accumulate_gl_objects(qapp) -> None:
    """>100 Wechsel 2D↔3D: der Cache-Treffer lädt erneut hoch, wächst aber nicht.

    Genau dieser Pfad ließ die GL-Objekte vor PR #676 anwachsen: derselbe Mesh
    wurde bei jedem Umschalten neu hochgeladen.
    """
    ledger = probe.ResourceLedger()
    canvas, worker = _FakeCanvas(), _FakeWorker()
    with probe.tracked_gl_resources(ledger):
        view = Relief3DView()
        ctrl = Preview3DController(
            view, canvas, worker,
            capability_probe=lambda: RendererCapability(ok=True, diagnostic="test"),
        )
        ctrl.set_active(True)
        ctrl._start_build()
        generation, on_done = worker.calls[-1]
        on_done(build_relief_mesh(canvas.height_preview_field(), MeshQuality.STANDARD), generation)
        viewer = view.viewer()
        assert viewer is not None

        for _ in range(CYCLES):
            ctrl.set_active(False)      # zurück auf 2D
            ctrl.set_active(True)       # wieder 3D (Cache-Treffer, kein Rebuild)
            viewer._ensure_buffers()    # der Frame, der den Upload fährt

            assert viewer.gl_object_count == 4

        assert len(worker.calls) == 1, "Cache-Treffer darf keinen Rebuild auslösen"
        ctrl.cleanup()

    assert ledger.created == ledger.destroyed
    assert ledger.double_destroys == []
    assert gl_resource_stats().live == 0


def test_cancelled_build_and_unavailable_capability_release_resources(qapp) -> None:
    """Abgebrochener Ladevorgang und wegfallende Capability lassen nichts zurück."""
    ledger = probe.ResourceLedger()
    canvas, worker = _FakeCanvas(), _FakeWorker()
    capability = {"ok": True}
    with probe.tracked_gl_resources(ledger):
        view = Relief3DView()
        ctrl = Preview3DController(
            view, canvas, worker,
            capability_probe=lambda: (
                RendererCapability(ok=True, diagnostic="test") if capability["ok"]
                else RendererCapability(ok=False, error_key=UNAVAILABLE_KEY)
            ),
        )
        ctrl.set_active(True)
        ctrl._start_build()
        generation, on_done = worker.calls[-1]
        on_done(build_relief_mesh(canvas.height_preview_field(), MeshQuality.STANDARD), generation)
        viewer = view.viewer()
        assert viewer is not None
        viewer._ensure_buffers()

        for index in range(20):
            canvas.content_revision += 1
            ctrl.refresh()                 # neuer Build entprellt …
            ctrl._start_build()
            stale_generation, stale_done = worker.calls[-1]
            canvas.content_revision += 1
            ctrl.refresh()                 # … und sofort superseded (Abbruch)
            stale_done(
                build_relief_mesh(canvas.height_preview_field(), MeshQuality.STANDARD),
                stale_generation,
            )

            assert viewer.gl_object_count == 4, "verworfenes Ergebnis lädt nichts hoch"
            if index == 10:
                capability["ok"] = False
                ctrl.refresh()

                assert view.state == "unavailable"
                capability["ok"] = True

        ctrl.cleanup()

    assert worker.cancelled > 0
    assert ledger.created == ledger.destroyed
    assert gl_resource_stats().live == 0


# ── Messsonde/CLI: der Nachweis selbst muss reproduzierbar sein ─────────


def test_parse_sizes_accepts_and_rejects(qapp) -> None:
    """Die Szenariendefinition der Sonde ist eindeutig und fail-fast."""
    assert probe._parse_sizes("klein:64:REDUCED,gross:2048:standard") == (
        ("klein", 64, MeshQuality.REDUCED),
        ("gross", 2048, MeshQuality.STANDARD),
    )
    for invalid in ("klein:64", "klein:0:REDUCED", "klein:64:ULTRA"):
        with pytest.raises(argparse.ArgumentTypeError):
            probe._parse_sizes(invalid)


def test_probe_cli_writes_a_reproducible_json_report(qapp, tmp_path) -> None:
    """``main`` schreibt den versionierbaren Nachweis und meldet „ok"."""
    out = tmp_path / "gl-stress.json"
    code = probe.main(
        ["--cycles", "5", "--sizes", "klein:64:REDUCED", "--json-out", str(out), "--quiet"]
    )

    assert code == 0
    payload = json.loads(out.read_text("utf-8"))
    assert payload["verdict"] == "ok"
    assert payload["findings"] == []
    assert payload["mode"] == "fake"
    assert payload["stats_before"]["live"] == payload["stats_after"]["live"]
    assert set(payload["memory_kib"]) == {"rss_before", "rss_after"}
    # Umgebungsangaben aus Akzeptanzkriterium 1 (#684).
    for key in ("commit", "bgremover", "python", "platform", "qt", "pyqt", "qpa_platform"):
        assert payload["environment"][key]
    names = [scenario["name"] for scenario in payload["scenarios"]]
    assert names == ["klein", "leere-daten"]
    assert all(scenario["growth"] == 0 for scenario in payload["scenarios"])


def test_probe_cli_fails_when_resources_leak(qapp, monkeypatch) -> None:
    """Ein Leck führt zu Exit 1 – die Sonde taugt damit als Gate."""
    monkeypatch.setattr(GLReliefViewer, "_release_gl_objects", lambda self: None)

    assert probe.main(["--cycles", "5", "--sizes", "klein:64:REDUCED", "--quiet"]) == 1


def test_probe_cli_refuses_gl_mode_without_renderable_platform(qapp) -> None:
    """``--mode gl`` bricht auf offscreen/minimal sauber mit Exit 2 ab."""
    if qapp.platformName() not in probe.NON_RENDERABLE_PLATFORMS:
        pytest.skip("Plattform ist renderfähig – der Abbruchpfad gilt hier nicht")

    assert probe.main(["--mode", "gl", "--cycles", "2"]) == 2
