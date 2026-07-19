"""End-to-End-/Abnahmetests der 3D-Reliefvorschau (#595, Epic #582).

Ergänzt die Bausteintests (``test_preview3d_controller``/``_integration``) um die
Abnahmekriterien aus #595, die sich **headless/offscreen** reproduzierbar prüfen
lassen:

- Entprellte, generationssichere Behandlung schneller Änderungsfolgen; veraltete
  Ergebnisse werden verworfen und der Cache hält nur genau ein Mesh.
- Viewer-Lifecycle-Churn (100 Zyklen aus Aufbau/Anzeige/Cleanup) ohne Absturz
  oder unbegrenztes Objektwachstum.
- Diagnosemeldungen der Capability-Probe klassifizieren den Fehler, ohne private
  Pfade oder Bildinhalte zu protokollieren.
- Nicht-Mutation von Projekt/Export/History über beliebige 3D-Interaktion sowie
  korrektes Verhalten gemischter COLOR/HEIGHT/GLOSS-Projekte und wiederholter
  Moduswechsel (2D ↔ 3D).

Die hardwaregebundenen Kriterien (GPU-Upload/Framerate, Packaging-/Plattform-
Smokes, Screenshots) sind in ``docs/PACKAGING_SMOKE.md`` als reproduzierbare
manuelle Prozeduren dokumentiert – sie können in der Offscreen-CI nicht ehrlich
grün gemeldet werden.
"""
from __future__ import annotations

import gc
import os
from collections.abc import Callable

import numpy as np
import pytest

from bgremover.height_map import HEIGHT_MAX_16BIT, HeightField
from bgremover.preview3d_capability import (
    probe_3d_capability,
    reset_capability_cache,
)
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
        self.errors: list[Callable] = []
        self.cancelled = 0

    def start_mesh_build(self, field, quality, generation_id, on_done, *,
                         on_error=None, physical_size_mm=None) -> bool:
        self.calls.append((generation_id, on_done))
        self.errors.append(on_error)
        return True

    def cancel_mesh_build(self) -> None:
        self.cancelled += 1


def _ok():
    from bgremover.preview3d_capability import RendererCapability
    return RendererCapability(ok=True, diagnostic="test")


# ── Entprellung / Stale-Schutz über zehn Änderungen ────────────────────────
def test_ten_rapid_changes_build_only_latest_and_discard_stale(qapp) -> None:
    """Zehn schnelle Änderungen: nur die jüngste Generation wird gebaut/angezeigt;
    alle veralteten Worker-Ergebnisse werden verworfen (Cache hält ein Mesh)."""
    view = Relief3DView()
    canvas = _FakeCanvas()
    worker = _FakeWorker()
    ctrl = Preview3DController(view, canvas, worker, capability_probe=_ok)
    ctrl.set_active(True)

    # Ein erster Build wird tatsächlich beim Worker registriert (Generation G1),
    # der Callback aber noch nicht ausgelöst – dieser Build „läuft" also, während
    # die Änderungsflut eintrifft.
    ctrl._start_build()
    stale_gen, stale_cb = worker.calls[0]

    # Zehn geometriewirksame Änderungen in schneller Folge. Jede erhöht die
    # Generation sofort und bricht den laufenden Build kooperativ ab; der
    # Debounce-Timer wird pro Test durch direkten ``_start_build``-Aufruf
    # überbrückt (das Fire-Verhalten des QTimer gehört zu Qt).
    for revision in range(2, 12):
        canvas.content_revision = revision
        ctrl.refresh()
    assert worker.cancelled >= 10  # jede Änderung entwertet den Vorgänger

    ctrl._start_build()  # nur der zuletzt entprellte Zustand baut wirklich
    latest_gen, latest_cb = worker.calls[-1]
    assert latest_gen != stale_gen  # die Generation wurde nachweislich erhöht

    fresh = build_relief_mesh(_field(), MeshQuality.STANDARD)
    latest_cb(fresh, latest_gen)
    assert view.state == "ready"
    assert ctrl._cache_mesh is fresh  # genau ein Mesh im Cache

    # Das verspätete Ergebnis des ersten (superseded) Builds trifft *nach* dem
    # aktuellen ein – es darf den Cache nie überschreiben (stale-result-Schutz).
    stale_cb(build_relief_mesh(_field(), MeshQuality.STANDARD), stale_gen)
    assert ctrl._cache_mesh is fresh
    assert view.state == "ready"

    ctrl.cleanup()


def test_returning_to_cached_state_reuses_without_rebuild(qapp) -> None:
    """Cache-Treffer: ein unveränderter geometriebestimmender Zustand zeigt das
    vorhandene Mesh ohne zweiten Build (messbar: keine weitere Worker-Anfrage)."""
    view = Relief3DView()
    canvas = _FakeCanvas()
    worker = _FakeWorker()
    ctrl = Preview3DController(view, canvas, worker, capability_probe=_ok)
    ctrl.set_active(True)
    ctrl._start_build()
    gen, cb = worker.calls[0]
    cb(build_relief_mesh(_field(), MeshQuality.STANDARD), gen)
    assert view.state == "ready"
    builds_after_first = len(worker.calls)

    # Reine Anzeige-Uniforms + erneutes refresh() ohne Geometrieänderung.
    ctrl.set_exaggeration(3.0)
    ctrl.set_light(120.0, 60.0)
    ctrl.refresh()
    assert view.state == "ready"
    assert len(worker.calls) == builds_after_first  # kein Rebuild

    ctrl.cleanup()


# ── Viewer-Lifecycle-Churn / Speicherdisziplin ─────────────────────────────
def test_hundred_viewer_lifecycle_cycles_do_not_leak_or_crash(qapp) -> None:
    """100 vollständige Lifecycle-Zyklen (Aktivieren → Build → Anzeige → GL-
    Cleanup → Deaktivieren) auf demselben Container zeigen kein stetiges
    Wachstum: der Cache hält genau **ein** Mesh und es existiert nie mehr als
    **ein** GL-Viewer (Wiederverwendung statt Anhäufung); der Lauf ist
    absturzfrei."""
    import weakref

    view = Relief3DView()
    canvas = _FakeCanvas()
    worker = _FakeWorker()
    ctrl = Preview3DController(view, canvas, worker, capability_probe=_ok)

    # Schwache Referenzen auf jedes selbst gebaute Mesh: ein prozessweiter
    # ``gc.get_objects()``-Scan wäre durch andere, in derselben Session zuvor
    # gelaufene Tests (z. B. nicht per ``deleteLater``/``processEvents``
    # abgeräumte Viewer-Widgets aus ``test_viewer_3d.py``) verfälschbar – die
    # gezielte Weakref-Liste prüft ausschließlich die 100 hier gebauten Meshes.
    mesh_refs: list[weakref.ReferenceType] = []
    first_viewer = None

    for revision in range(2, 102):
        canvas.content_revision = revision
        ctrl.set_active(True)
        ctrl.refresh()
        ctrl._start_build()
        gen, cb = worker.calls[-1]
        mesh = build_relief_mesh(_field(), MeshQuality.STANDARD)
        mesh_refs.append(weakref.ref(mesh))
        cb(mesh, gen)
        del mesh
        assert view.state == "ready"
        viewer = view.viewer()
        assert viewer is not None               # Viewer real erzeugt/angezeigt
        if first_viewer is None:
            first_viewer = viewer
        else:
            # Identitätsprüfung statt prozessweitem Objekt-Scan: derselbe
            # Viewer wird über alle 100 Zyklen wiederverwendet, nicht je
            # Zyklus neu erzeugt (kein Akkumulieren von GL-Ressourcen).
            assert viewer is first_viewer
        ctrl.cleanup()                          # GL-Ressourcen je Zyklus freigeben
        ctrl.set_active(False)

    qapp.processEvents()
    gc.collect()
    # Kernaussage: von den 100 hier gebauten Meshes bleibt genau eines (das
    # aktuell gecachte) am Leben – die anderen 99 wurden freigegeben, kein
    # stetiges Anwachsen.
    alive = [r for r in mesh_refs if r() is not None]
    assert len(alive) == 1
    assert alive[0]() is ctrl._cache_mesh

    ctrl.cleanup()


# ── Diagnose ohne Geheimnisse/Pfade ────────────────────────────────────────
def test_capability_diagnostic_does_not_leak_paths_or_secrets(qapp) -> None:
    """Die reale (offscreen echt fehlschlagende) Capability-Probe liefert einen
    knappen technischen Grund – ohne Home-/Dateipfade oder Bildinhalte."""
    reset_capability_cache()
    try:
        cap = probe_3d_capability(use_cache=False)
    finally:
        reset_capability_cache()

    haystack = f"{cap.diagnostic} {cap.detail} {cap.error_key or ''}"
    home = os.path.expanduser("~")
    assert home not in haystack
    for needle in ("/home/", "/Users/", "\\Users\\", ".png", ".bgrproj", "/tmp/"):
        assert needle not in haystack
    # Bei ok=False trägt die Probe einen strukturierten i18n-Key + Kurzgrund.
    if not cap.ok:
        assert cap.error_key == "preview3d.unavailable"
        assert cap.detail  # nicht leer, aber technisch (kein Nutzerinhalt)


# ── Window-gebundene End-to-End-Abnahme (ui_smoke) ─────────────────────────
_ui_smoke = pytest.mark.ui_smoke


def _mixed_project(w: int = 16, h: int = 16):
    """Projekt mit COLOR-, HEIGHT- (HEIGHT_MAP) und GLOSS-Ebene (GLOSS_MASK)."""
    from PIL import Image

    from bgremover.project_model import LayerKind, LayerRole, Project

    project = Project(w, h)
    # COLOR-Ebene bewusst als Verlauf (nicht rotationsinvariant), damit
    # Bearbeitungen im Export sichtbar werden.
    color = np.zeros((h, w, 4), dtype=np.uint8)
    color[:, :, 0] = np.tile(np.linspace(0, 255, w, dtype=np.uint8), (h, 1))
    color[:, :, 1] = np.tile(
        np.linspace(0, 255, h, dtype=np.uint8).reshape(h, 1), (1, w))
    color[:, :, 3] = 255
    project.create_layer(Image.fromarray(color, "RGBA"), name="C",
                         kind=LayerKind.COLOR)
    heights = np.tile(np.linspace(0, 255, w, dtype=np.uint8), (h, 1))
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, 0] = heights
    rgba[:, :, 3] = 255
    project.create_layer(Image.fromarray(rgba, "RGBA"), name="H",
                         kind=LayerKind.HEIGHT, role=LayerRole.HEIGHT_MAP)
    gloss = np.zeros((h, w, 4), dtype=np.uint8)
    gloss[:, :, :3] = 128
    gloss[:, :, 3] = 255
    project.create_layer(Image.fromarray(gloss, "RGBA"), name="G",
                         kind=LayerKind.GLOSS, role=LayerRole.GLOSS_MASK)
    return project


@pytest.fixture()
def window(qapp, tmp_path, monkeypatch):
    from PyQt6.QtCore import QSettings

    import bgremover.main_window as mw
    from bgremover.preview3d_capability import RendererCapability

    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                      str(tmp_path))
    monkeypatch.setattr(
        mw, "probe_3d_capability",
        lambda *a, **k: RendererCapability(ok=True, diagnostic="test"))
    w = mw.MainWindow()
    yield w
    w._preview3d.cleanup()
    w._worker_controller.shutdown_all()


@_ui_smoke
def test_export_bytes_identical_after_full_3d_interaction(window) -> None:
    """Beliebige 3D-Interaktion (Aktivieren, Kamera-Orbit, Überhöhung/Licht,
    Qualität, Deaktivieren) lässt den Exportpfad byte-identisch (kein Schreibpfad
    ins Modell)."""
    window._canvas.set_project(_mixed_project())
    window._update_preview3d_availability()
    before = np.array(window._canvas._render_export_image())
    revision_before = window._canvas.content_revision

    window._set_preview3d_mode(True)
    ctrl = window._preview3d
    # Statt auf den realen 200-ms-async-Build zu warten: den debounced Build
    # deterministisch überbrücken und ein synchron gebautes Mesh einspeisen, damit
    # der GL-Viewer real erzeugt wird und die Kamera-Interaktion wirklich läuft.
    ctrl._debounce.stop()
    ctrl._workers.cancel_mesh_build()
    field = window._canvas.height_preview_field()
    assert field is not None
    mesh = build_relief_mesh(
        field, ctrl.quality, physical_size_mm=window._canvas.physical_size_mm())
    ctrl._on_mesh_ready(mesh, ctrl._generation)
    viewer = window._relief3d_view.viewer()
    assert viewer is not None  # echte Viewer-Interaktion folgt (Kamera = Uniform)
    viewer.camera.orbit(30.0, -20.0)
    viewer.camera.zoom(1.3)
    ctrl.set_exaggeration(6.0)
    ctrl.set_light(90.0, 30.0)
    ctrl.set_quality(MeshQuality.HIGH)
    ctrl._debounce.stop()  # den durch die Qualitätsänderung geplanten Build stoppen
    window._set_preview3d_mode(False)

    after = np.array(window._canvas._render_export_image())
    assert window._canvas.content_revision == revision_before
    assert np.array_equal(before, after)


@_ui_smoke
def test_mixed_project_feeds_height_layer_to_3d(window) -> None:
    """Ein gemischtes COLOR/HEIGHT/GLOSS-Projekt speist die 3D-Vorschau aus der
    HEIGHT-Ebene (nicht Farbe/Gloss); Auswahl/Preview bleiben konsistent."""
    project = _mixed_project(20, 12)
    window._canvas.set_project(project)
    window._update_preview3d_availability()

    from bgremover.project_model import LayerRole

    field = window._canvas.height_preview_field()
    assert field is not None
    assert field.size == (20, 12)  # (width, height) der HEIGHT-Payload

    # Nicht nur die Größe (alle drei Ebenen sind gleich groß), sondern die echten
    # Werte prüfen: die 3D-Quelle ist die HEIGHT-Payload, nicht Farbe/Gloss.
    height_layer = project.layer_by_role(LayerRole.HEIGHT_MAP)
    assert height_layer is not None
    assert np.array_equal(field.values, height_layer.height_data.values)
    # Der HEIGHT-Gradient ist bewusst distinktiv: Spaltenverlauf 0 → Maximum,
    # klar unterscheidbar von der konstanten Gloss-Fläche (128) oder der Farbe.
    assert int(field.values.min()) == 0
    assert int(field.values.max()) >= 65000
    assert field.values[:, 0].max() < field.values[:, -1].min()

    window._set_preview3d_mode(True)
    assert window._preview3d_active
    # Das Gating erlaubt 3D nur mit gültiger HEIGHT-Payload.
    assert window._height_panel._btn_3d.isEnabled()
    window._set_preview3d_mode(False)


@_ui_smoke
def test_repeated_mode_switches_are_stable(window) -> None:
    """Wiederholte Wechsel 2D-Leinwand ↔ 3D-Viewer sind idempotent stabil und
    hinterlassen jeweils den erwarteten Stack-/Aktiv-Zustand."""
    window._canvas.set_project(_mixed_project())
    window._update_preview3d_availability()
    for _ in range(6):
        window._set_preview3d_mode(True)
        assert window._preview3d_active
        assert window._canvas_stack.currentIndex() == 1
        window._set_preview3d_mode(False)
        assert not window._preview3d_active
        assert window._canvas_stack.currentIndex() == 0


@_ui_smoke
def test_viewer_error_does_not_corrupt_project_or_history(window) -> None:
    """Ein Renderer-/Mesh-Build-Fehler beschädigt weder Projektzustand noch
    History; Bearbeitung/Undo bleiben danach funktionsfähig."""
    window._canvas.set_project(_mixed_project())
    window._update_preview3d_availability()
    window._set_preview3d_mode(True)

    # Fehler der aktuellen Generation simulieren (Worker scheitert). Den realen
    # async-Build vorher deterministisch stoppen, damit ausschließlich der
    # Fehlerpfad greift und der Container exakt in den Fehlerzustand wechselt.
    ctrl = window._preview3d
    ctrl._debounce.stop()
    ctrl._workers.cancel_mesh_build()
    ctrl._on_mesh_error("simulierter Bufferfehler", ctrl._generation)
    assert window._relief3d_view.state == "error"

    # Projekt/History intakt: eine reguläre Bearbeitung + Undo greift weiter.
    window._set_preview3d_mode(False)
    assert window._canvas.height_preview_field() is not None  # HEIGHT-Payload intakt
    export_before = np.array(window._canvas._render_export_image())
    window._canvas.apply_rotate(90)
    assert not np.array_equal(
        export_before, np.array(window._canvas._render_export_image()))
    assert window._canvas.can_undo
    window._canvas.undo()
    # Undo stellt den Bildzustand bitgenau wieder her (History unbeschädigt).
    assert np.array_equal(
        export_before, np.array(window._canvas._render_export_image()))
