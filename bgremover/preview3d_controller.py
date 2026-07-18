"""Workflow-/State-/Cache-Orchestrierung der 3D-Reliefvorschau (#594, Epic #582).

Bindet den Zustandscontainer (:class:`~bgremover.viewer_3d.Relief3DView`) an den
realen Projekt-/Preview-Workflow: Capability-Gating, aktiver HEIGHT-Zustand,
entprellter asynchroner Mesh-Build mit Generation-IDs und stale-result-Schutz,
ein Ein-Mesh-Cache mit inhaltsbasiertem Schlüssel sowie die reinen
Anzeige-Uniforms (Überhöhung/Licht/Kamera), die **keinen** Rebuild erzwingen.

Die 2D-``PreviewMode``-Pipeline bleibt unberührt; der Viewer hat keinerlei
Schreibpfad ins Modell (Kamera/Überhöhung ändern nie Bild-, HEIGHT- oder
Exportdaten). Die Klasse ist bewusst schlank an Qt gekoppelt (nur ein
Debounce-``QTimer``); die Zustands-/Cache-/Generation-Logik ist mit einem
Fake-Canvas/-WorkerController ohne GL-Kontext testbar.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from bgremover.constants import logger
from bgremover.preview3d_capability import (
    RendererCapability,
    probe_3d_capability,
    reset_capability_cache,
)
from bgremover.relief_mesh import MeshCacheKey, MeshQuality, ReliefMesh, mesh_cache_key
from bgremover.viewer_3d import Relief3DView

# Debounce der geometriewirksamen Änderungen (ADR: 200 ms nach der letzten).
_DEBOUNCE_MS = 200


class _CanvasLike(Protocol):
    """Minimaler Canvas-Vertrag, den der Controller lesend konsumiert."""

    def height_preview_field(self) -> object | None: ...
    def physical_size_mm(self) -> tuple[float, float] | None: ...
    @property
    def content_revision(self) -> int: ...


class _WorkerLike(Protocol):
    def start_mesh_build(
        self,
        field: object,
        quality: object,
        generation_id: int,
        on_done: Callable[[object, int], None],
        *,
        on_error: Callable[[str, int], None] | None = None,
        physical_size_mm: tuple[float, float] | None = None,
    ) -> bool: ...
    def cancel_mesh_build(self) -> None: ...


class Preview3DController(QObject):
    """Orchestriert Gating, Build, Cache und Anzeige der 3D-Vorschau."""

    capabilityChecked = pyqtSignal(object)

    def __init__(
        self,
        view: Relief3DView,
        canvas: _CanvasLike,
        worker_controller: _WorkerLike,
        *,
        capability_probe: Callable[[], RendererCapability] = probe_3d_capability,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._view = view
        self._canvas = canvas
        self._workers = worker_controller
        self._capability_probe = capability_probe

        self._active = False
        self._quality = MeshQuality.STANDARD
        self._exaggeration = 1.0
        self._light = (315.0, 45.0)

        self._generation = 0
        self._cache_key: MeshCacheKey | None = None
        self._cache_mesh: ReliefMesh | None = None
        self._pending_key: MeshCacheKey | None = None
        self._displaying = False

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(_DEBOUNCE_MS)
        self._debounce.timeout.connect(self._start_build)

        self._view.retryRequested.connect(self.retry)

    # ── Öffentliche Steuerung (MainWindow) ───────────────────────────────
    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def view(self) -> Relief3DView:
        return self._view

    @property
    def quality(self) -> MeshQuality:
        return self._quality

    @property
    def exaggeration(self) -> float:
        return self._exaggeration

    @property
    def light(self) -> tuple[float, float]:
        return self._light

    def set_show_2d_callback(self, callback: Callable[[], None]) -> None:
        """Verbindet den „2D-Relief anzeigen"-Button des Fehlerzustands."""
        self._view.show2DRequested.connect(callback)

    def set_active(self, active: bool) -> None:
        """Aktiviert/deaktiviert den 3D-Modus (Umschalter/Menü)."""
        if active == self._active:
            return
        self._active = active
        if active:
            self._evaluate(force_rebuild=False)
        else:
            self._debounce.stop()
            self._workers.cancel_mesh_build()

    def refresh(self) -> None:
        """Reagiert auf Layer-/Inhalts-/Projektänderungen (nur im 3D-Modus)."""
        if self._active:
            self._evaluate(force_rebuild=False)

    def set_quality(self, quality: MeshQuality) -> None:
        """Qualitätswechsel – geometriebestimmend, löst Rebuild aus."""
        if quality is self._quality:
            return
        self._quality = quality
        if self._active:
            self._evaluate(force_rebuild=False)

    def set_exaggeration(self, value: float) -> None:
        """Überhöhung – reiner Anzeige-Uniform, **kein** Rebuild."""
        self._exaggeration = value
        self._view.set_exaggeration(value)

    def set_light(self, azimuth: float, elevation: float) -> None:
        """Lichtrichtung – reiner Anzeige-Uniform, **kein** Rebuild."""
        self._light = (azimuth, elevation)
        self._view.set_light(azimuth, elevation)

    def fit_view(self) -> None:
        self._view.fit_view()

    def reset_view(self) -> None:
        self.set_quality(MeshQuality.STANDARD)
        self._exaggeration = 1.0
        self._light = (315.0, 45.0)
        self._view.reset_view()

    def retry(self) -> None:
        """„Erneut versuchen": Capability-Cache verwerfen und neu bewerten."""
        reset_capability_cache()
        if self._active:
            self._evaluate(force_rebuild=True)

    def cleanup(self) -> None:
        """Bricht laufende Builds ab und gibt Viewer-Ressourcen frei."""
        self._debounce.stop()
        self._workers.cancel_mesh_build()
        self._view.cleanup()

    # ── Kernlogik ────────────────────────────────────────────────────────
    def _evaluate(self, *, force_rebuild: bool) -> None:
        """Bestimmt den Zielzustand: unavailable/empty/cache-hit/(debounced) build."""
        capability = self._capability_probe()
        self.capabilityChecked.emit(capability)
        if not capability.ok:
            self._debounce.stop()
            self._workers.cancel_mesh_build()
            self._displaying = False
            self._view.show_unavailable()
            return
        field = self._canvas.height_preview_field()
        if field is None:
            self._debounce.stop()
            self._workers.cancel_mesh_build()
            self._displaying = False
            self._view.show_empty()
            return

        key = mesh_cache_key(
            content_revision=self._canvas.content_revision,
            source_size=field.size,  # type: ignore[attr-defined]
            quality=self._quality,
            physical_size_mm=self._canvas.physical_size_mm(),
        )
        if (
            not force_rebuild
            and self._cache_mesh is not None
            and self._cache_key == key
        ):
            # Sicherer Cache-Treffer: nichts Geometriebestimmendes hat sich
            # geändert (Kamera/Licht/Überhöhung sind nicht Teil des Keys).
            self._debounce.stop()
            self._show_cached()
            return
        if (
            not force_rebuild
            and key == self._pending_key
            and self._debounce.isActive()
        ):
            # Für genau diesen Zustand ist bereits ein Build entprellt – kein
            # unnötiges Neubumpen/Cancel-Restart im 200-ms-Fenster.
            return
        # Cache-Miss → **generationssicherer**, entprellter Rebuild. Die
        # Generation wird bereits *hier* erhöht (nicht erst beim Build-Start) und
        # ein laufender Build kooperativ abgebrochen: ein verspätetes älteres
        # Ergebnis trägt damit eine veraltete Generation und wird in
        # ``_on_mesh_ready`` verworfen – es kann nie unter dem neuen Key gecacht
        # oder angezeigt werden (stale-result-Schutz, Review #620). Ein bereits
        # angezeigtes Mesh bleibt stehen (kein Schwarzbild).
        self._generation += 1
        self._workers.cancel_mesh_build()
        self._pending_key = key
        if not self._displaying:
            self._view.show_loading()
        self._debounce.start()

    def _start_build(self) -> None:
        """Startet den asynchronen Mesh-Build für die aktuelle Generation.

        Die Generation-ID stammt aus :meth:`_evaluate` (dort erhöht); hier wird
        sie **nicht** erneut erhöht, damit ein zwischenzeitlich superseded
        Zustand (erneutes ``_evaluate``) diesen Build eindeutig entwertet.
        """
        if not self._active:
            return
        field = self._canvas.height_preview_field()
        if field is None:
            self._view.show_empty()
            self._displaying = False
            return
        generation = self._generation
        self._workers.start_mesh_build(
            field, self._quality, generation, self._on_mesh_ready,
            on_error=self._on_mesh_error,
            physical_size_mm=self._canvas.physical_size_mm(),
        )

    def _on_mesh_ready(self, mesh: object, generation: int) -> None:
        """Übernimmt ein Build-Ergebnis nur, wenn es aktuell und im 3D-Modus ist."""
        if not self._active:
            return
        if generation != self._generation:
            # Veraltetes Ergebnis (neuere Generation existiert) – verwerfen,
            # nie anzeigen (stale-result-Schutz, #594).
            logger.debug("3D-Mesh (Generation %d) verworfen – veraltet", generation)
            return
        assert isinstance(mesh, ReliefMesh)
        self._cache_mesh = mesh
        self._cache_key = self._pending_key
        self._show_cached()

    def _on_mesh_error(self, message: str, generation: int) -> None:
        """Meldet einen Mesh-Build-Fehler als Fehlerzustand (mit Retry-Pfad).

        Nur für die aktuelle Generation im aktiven 3D-Modus – ein Fehler eines
        bereits superseded Builds wird ignoriert. So bleibt der Nutzer nicht im
        Ladezustand hängen, wenn der Worker unerwartet scheitert (Review #620).
        """
        if not self._active or generation != self._generation:
            return
        logger.warning("3D-Mesh-Build fehlgeschlagen: %s", message)
        self._displaying = False
        self._view.show_error()

    def _show_cached(self) -> None:
        assert self._cache_mesh is not None
        self._view.show_mesh(self._cache_mesh)
        self._view.set_exaggeration(self._exaggeration)
        self._view.set_light(*self._light)
        self._displaying = self._view.state == "ready"
