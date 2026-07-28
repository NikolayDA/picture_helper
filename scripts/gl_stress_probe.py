#!/usr/bin/env python3
"""Reproduzierbare GL-Ressourcen-Langzeitsonde der 3D-Reliefvorschau (#684).

Hintergrund: PR #676 hat ein Leck behoben – ``GLReliefViewer._ensure_buffers``
realloziierte Puffer/VAO bei jedem (Wieder-)Upload, ohne die Vorgänger
freizugeben. Für die Freigabe von 2.7.1 (Epic #680) fehlte der *messbare*
Nachweis, dass wiederholte Nutzung keine Ressourcen anhäuft.

**Festgelegter Messwert (Akzeptanzkriterium 2 aus #684):** die Zahl der lebenden,
vom Viewer besessenen GL-Objekte – drei Puffer (Position/Slope/Index) plus VAO.
Zwei unabhängige Quellen dafür:

- :attr:`bgremover.viewer_3d.GLReliefViewer.gl_object_count` – direkt aus den
  gehaltenen Referenzen abgeleitet (kann nicht abdriften), Obergrenze 4.
- :func:`bgremover.viewer_3d.gl_resource_stats` – prozessweite Erzeugungs-/
  Freigabezähler; ``created - destroyed`` ist die Zahl lebender Objekte über
  *alle* Viewer und deckt damit auch verwaiste Objekte auf, die kein Viewer
  mehr referenziert (genau der Leckfall vor #676).

Zwei Modi:

- ``--mode fake`` (Standard, läuft überall inklusive ``QT_QPA_PLATFORM=offscreen``):
  echte Meshes, echter ``_ensure_buffers``/``_release_gl_objects``/``cleanup_gl``-
  Kontrollfluss, aber instrumentierte Puffer-/VAO-Attrappen statt echter
  GL-Objekte. Damit werden zusätzlich Doppelfreigaben und Zugriffe nach der
  Freigabe (use-after-delete) direkt beobachtbar – auf echten Treibern wären sie
  bestenfalls indirekt sichtbar.
- ``--mode gl``: echter GL-Kontext (nur auf einer renderfähigen Qt-Plattform,
  also **nicht** offscreen/minimal). Identische Zyklen, echte ``QOpenGLBuffer``/
  ``QOpenGLVertexArrayObject``; misst denselben Zählerstand auf der Zielhardware.

Ausgabe ist ein JSON-Bericht (Umgebung, Szenarien, Zählerstände vor/nach dem
Lauf, Urteil) – der versionierbare Nachweis für den Testbericht.

Beispiele::

    python scripts/gl_stress_probe.py                       # offscreen, 120 Zyklen
    python scripts/gl_stress_probe.py --cycles 500 --json-out bericht.json
    QT_QPA_PLATFORM=xcb python scripts/gl_stress_probe.py --mode gl

Ein Lauf unter ``MIN_GATING_CYCLES`` Zyklen wird abgelehnt: er ersetzt zu wenig
Puffer, um ein Leck zu zeigen. ``--allow-short-run`` erlaubt ihn ausdrücklich als
Diagnose und markiert den Bericht mit ``gating: false``.

Exit 0 = kein Befund, 1 = Ressourcenbefund, 2 = Sonde nicht ausführbar (keine
renderfähige Plattform, fehlgeschlagener Viewer, ausgebliebener oder
**unvollständiger** Upload – ausdrücklich **kein** bestandener Nachweis).

Zum unvollständigen Upload (#711): ``QOpenGLBuffer.create()``/``bind()`` melden
Fehler nur über ihren Rückgabewert. Der Viewer behandelt beides seit #711 als
harten Fehler; die Sonde verlangt zusätzlich, dass ein Lauf mindestens
``MIN_LIVE_PER_VIEWER`` gehaltene Objekte gesehen hat – eine Messreihe ohne
vollständigen Puffersatz ist konstant und damit formal „ohne Wachstum", aber
kein Nachweis.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Final

import numpy as np

_REPO_ROOT: Final = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:  # Direktaufruf ohne installiertes Paket
    sys.path.insert(0, str(_REPO_ROOT))

from bgremover.height_map import HEIGHT_MAX_16BIT, HeightField  # noqa: E402
from bgremover.relief_mesh import MeshQuality, ReliefMesh, build_relief_mesh  # noqa: E402
from bgremover.viewer_3d import (  # noqa: E402
    GLBufferError,
    GLReliefViewer,
    gl_resource_stats,
)

#: Ein fehlerfreier Viewer hält nie mehr als drei Puffer plus einen VAO.
MAX_LIVE_PER_VIEWER: Final = 4

#: Ein *erfolgreicher* Upload legt immer die drei Puffer (Position/Slope/Index)
#: an; der VAO ist in GL 2.1 eine Erweiterung und darf fehlen. Weniger als drei
#: gehaltene Objekte heißt: es gab keinen vollständigen Upload – eine Messreihe
#: darauf ist kein Nachweis, sondern ein falsches Grün (#711).
MIN_LIVE_PER_VIEWER: Final = 3

#: Qt-Plattformen ohne renderbaren FBO – dort ist ``--mode gl`` unmöglich.
NON_RENDERABLE_PLATFORMS: Final = frozenset({"offscreen", "minimal", "vnc"})

#: Standard-Datensätze: klein / typisch / groß (Akzeptanzkriterium 9 aus #684).
DEFAULT_SIZES: Final[tuple[tuple[str, int, MeshQuality], ...]] = (
    ("klein", 64, MeshQuality.REDUCED),
    ("typisch", 512, MeshQuality.STANDARD),
    ("gross", 2048, MeshQuality.STANDARD),
)

#: Mindestzyklen für einen abnahmefähigen Lauf (#684 verlangt mindestens 100).
#: Darunter findet zu wenig Ersetzung statt, um ein Leck zuverlässig zu zeigen –
#: bei einem einzigen Zyklus gäbe es gar keinen Wieder-Upload, und selbst der
#: Zustand vor PR #676 meldete sich sauber.
MIN_GATING_CYCLES: Final = 100

#: Zyklen, die vor der Bewertung als Initialisierung/Cache gelten. Alles danach
#: muss konstant bleiben – so trennt die Sonde einmalige Aufwärmkosten von einem
#: pro Zyklus weiterwachsenden Verbrauch (Akzeptanzkriterium 3 aus #684).
WARMUP_CYCLES: Final = 2


class ProbeNotExecutable(RuntimeError):
    """Die Sonde konnte in dieser Umgebung nicht messen (Exit 2, **kein** „ok").

    Ausdrücklich kein Ressourcenbefund: ein Lauf, der den GL-Pfad nie erreicht
    hat, darf nicht als bestandener Nachweis durchgehen.
    """


# ── Instrumentierte GL-Attrappen ───────────────────────────────────────


class ResourceLedger:
    """Buchführung über alle im Lauf erzeugten GL-Attrappen.

    Erfasst nicht nur Erzeugung/Freigabe, sondern auch die beiden Fehlerbilder,
    die ein Lebenszyklusfehler produziert: **Doppelfreigabe** (``destroy`` auf
    einem bereits zerstörten Objekt) und **use-after-delete** (Benutzung nach
    der Freigabe).
    """

    def __init__(self) -> None:
        self.created = 0
        self.destroyed = 0
        self.double_destroys: list[str] = []
        self.use_after_destroy: list[str] = []

    @property
    def live(self) -> int:
        return self.created - self.destroyed

    def note_created(self) -> None:
        self.created += 1

    def note_destroyed(self, label: str, already: bool) -> None:
        if already:
            self.double_destroys.append(label)
            return
        self.destroyed += 1

    def note_use_after_destroy(self, label: str) -> None:
        self.use_after_destroy.append(label)


class TrackedGLResource:
    """Puffer-/VAO-Ersatz mit vollständiger Lebenszyklus-Buchführung.

    Bildet die von ``_ensure_buffers``/``_paint_gl`` genutzte Oberfläche von
    ``QOpenGLBuffer``/``QOpenGLVertexArrayObject`` nach. Jede Benutzung nach
    ``destroy`` wird als use-after-delete protokolliert statt (wie ein echter
    Treiber) still zu funktionieren oder zu crashen.

    Gebucht wird erst ein **erfolgreiches** ``create()`` – wie beim echten
    Treiber entsteht der GL-Name dort und nicht schon im Konstruktor (#711).
    ``fail_create``/``fail_bind`` stellen die beiden stillen booleschen
    Fehlschläge deterministisch nach, die es sonst nur auf defekten Treibern
    gibt.
    """

    def __init__(
        self,
        ledger: ResourceLedger,
        label: str,
        *,
        fail_create: bool = False,
        fail_bind: bool = False,
    ) -> None:
        self._ledger = ledger
        self._label = label
        self._fail_create = fail_create
        self._fail_bind = fail_bind
        self.created = 0
        self.destroyed = 0
        self.allocated = 0

    def _touch(self, what: str) -> None:
        if self.destroyed:
            self._ledger.note_use_after_destroy(f"{self._label}.{what}")

    def create(self) -> bool:
        self._touch("create")
        if self._fail_create:
            return False
        self.created += 1
        self._ledger.note_created()
        return True

    def bind(self) -> bool:
        self._touch("bind")
        return not self._fail_bind

    def release(self) -> bool:
        self._touch("release")
        return True

    def allocate(self, *args: object, **kwargs: object) -> None:
        self._touch("allocate")
        self.allocated += 1

    def destroy(self) -> None:
        if not self.created:
            # Ohne erfolgreiches ``create()`` gibt es keinen GL-Namen: die
            # Freigabe ist ein No-op und darf die Bilanz nicht verschieben.
            return
        self._ledger.note_destroyed(self._label, already=bool(self.destroyed))
        self.destroyed += 1


#: Bauplan einer Attrappe: ``(ledger, label) -> TrackedGLResource``. Über diesen
#: Haken injizieren Regressionstests deterministische ``create()``/``bind()``-
#: Fehlschläge, ohne den Patchpunkt der Sonde nachbauen zu müssen (#711).
ResourceFactory = Callable[[ResourceLedger, str], "TrackedGLResource"]


@contextmanager
def tracked_gl_resources(
    ledger: ResourceLedger,
    *,
    buffer_factory: ResourceFactory | None = None,
    vao_factory: ResourceFactory | None = None,
) -> Iterator[None]:
    """Ersetzt Puffer-/VAO-Konstruktion im Viewer-Modul durch Attrappen.

    Bewusst an genau den beiden Stellen, an denen der Viewer GL-Objekte anlegt –
    der übrige Kontrollfluss (Freigabe, Nullen der Referenzen, ``cleanup_gl``)
    bleibt der echte Produktionscode. Der Puffer wird über ``viewer_3d._new_buffer``
    ersetzt und **nicht** über ``_make_buffer``: so läuft die produktive
    ``create()``/``bind()``-Fehlerprüfung mit, statt vom Fake überdeckt zu werden
    (#711).

    ``buffer_factory``/``vao_factory`` sind der Einhängepunkt für Fehlerbilder;
    ohne sie entstehen normale, immer erfolgreiche Attrappen.
    """
    from bgremover import viewer_3d

    original_new_buffer = viewer_3d._new_buffer
    original_vao = viewer_3d.QOpenGLVertexArrayObject
    counter = {"n": 0}
    # Erst beim Aufruf aufgelöst: so wirkt auch ein Patch auf
    # ``TrackedGLResource`` selbst (Szenario-/CLI-Tests).
    make_buffer = buffer_factory or (lambda led, label: TrackedGLResource(led, label))
    make_vao_resource = vao_factory or (lambda led, label: TrackedGLResource(led, label))

    def new_buffer(buffer_type: object) -> TrackedGLResource:
        counter["n"] += 1
        return make_buffer(ledger, f"buffer#{counter['n']}")

    def make_vao(*args: object, **kwargs: object) -> TrackedGLResource:
        counter["n"] += 1
        return make_vao_resource(ledger, f"vao#{counter['n']}")

    viewer_3d._new_buffer = new_buffer  # type: ignore[assignment]
    viewer_3d.QOpenGLVertexArrayObject = make_vao  # type: ignore[assignment,misc]
    try:
        yield
    finally:
        viewer_3d._new_buffer = original_new_buffer  # type: ignore[assignment]
        viewer_3d.QOpenGLVertexArrayObject = original_vao  # type: ignore[assignment,misc]


# ── Messdaten ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ScenarioResult:
    """Ergebnis eines Szenarios (ein Datensatz, N Aktualisierungszyklen).

    ``live_*`` bezieht sich immer auf den **prozessweiten** Bestand relativ zum
    Szenariostart (``created - destroyed``). Der ist der aussagekräftige Wert:
    ein verwaistes GL-Objekt wird vom Viewer nicht mehr referenziert, lebt aber
    weiter – ``max_viewer_objects`` allein würde genau dieses Leck übersehen.
    """

    name: str
    cycles: int
    source_px: str
    vertices: int
    triangles: int
    decimated: bool
    live_after_warmup: int
    live_after_last_cycle: int
    max_live: int
    max_viewer_objects: int
    live_after_cleanup: int
    created_total: int
    destroyed_total: int
    rss_kib_start: int
    rss_kib_end: int
    double_destroys: tuple[str, ...]
    use_after_destroy: tuple[str, ...]
    findings: tuple[str, ...]

    @property
    def growth(self) -> int:
        """Zuwachs lebender Objekte nach der Aufwärmphase (muss 0 sein)."""
        return self.live_after_last_cycle - self.live_after_warmup


@dataclass
class ProbeReport:
    """Gesamtbericht der Sonde (JSON-serialisierbar)."""

    mode: str
    environment: dict[str, str]
    stats_before: dict[str, int]
    stats_after: dict[str, int]
    memory: dict[str, int] = field(default_factory=dict)
    scenarios: list[ScenarioResult] = field(default_factory=list)
    #: Ob der Lauf die Mindestzyklen erreicht und damit als Nachweis taugt.
    gating: bool = True

    @property
    def findings(self) -> list[str]:
        found = [f"{s.name}: {finding}" for s in self.scenarios for finding in s.findings]
        leaked = self.stats_after["live"] - self.stats_before["live"]
        if leaked:
            found.append(
                f"prozessweit: {leaked} GL-Objekt(e) nach dem Lauf nicht freigegeben"
            )
        return found

    def to_json(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "environment": self.environment,
            "stats_before": self.stats_before,
            "stats_after": self.stats_after,
            "memory_kib": self.memory,
            "gating": self.gating,
            "min_gating_cycles": MIN_GATING_CYCLES,
            "scenarios": [
                {**asdict(s), "growth": s.growth} for s in self.scenarios
            ],
            "findings": self.findings,
            "verdict": "ok" if not self.findings else "befund",
        }


# ── Szenarien ──────────────────────────────────────────────────────────


def build_field(size: int, *, empty_coverage: bool = False) -> HeightField:
    """Deterministische Höhenkarte der Kantenlänge *size* (Rampe, voll gedeckt)."""
    ramp = np.tile(
        np.linspace(0, HEIGHT_MAX_16BIT, size, dtype=np.uint16), (size, 1)
    )
    coverage = np.zeros((size, size), np.uint8) if empty_coverage else np.full(
        (size, size), 255, np.uint8
    )
    return HeightField(ramp, coverage, HEIGHT_MAX_16BIT)


def _evaluate(
    name: str,
    cycles: int,
    mesh: ReliefMesh,
    source_px: str,
    samples: Sequence[int],
    viewer_samples: Sequence[int],
    ledger: ResourceLedger | None,
    live_after_cleanup: int,
    created: int,
    destroyed: int,
    rss_start: int,
    rss_end: int,
    *,
    upload_error: str | None = None,
) -> ScenarioResult:
    """Bewertet die Messreihe eines Szenarios gegen die Kriterien aus #684."""
    warmup_index = min(WARMUP_CYCLES, len(samples)) - 1
    live_after_warmup = samples[warmup_index]
    live_last = samples[-1]
    findings: list[str] = []
    if upload_error is not None:
        findings.append(f"Upload fehlgeschlagen: {upload_error}")
    if live_last != live_after_warmup:
        findings.append(
            f"lebende GL-Objekte wachsen nach der Aufwärmphase "
            f"({live_after_warmup} → {live_last} über {cycles} Zyklen)"
        )
    if max(samples) > MAX_LIVE_PER_VIEWER:
        findings.append(
            f"mehr als {MAX_LIVE_PER_VIEWER} lebende GL-Objekte "
            f"(Maximum {max(samples)})"
        )
    if max(viewer_samples) > MAX_LIVE_PER_VIEWER:
        findings.append(
            f"Viewer hält mehr als {MAX_LIVE_PER_VIEWER} GL-Objekte "
            f"(Maximum {max(viewer_samples)})"
        )
    if max(viewer_samples, default=0) < MIN_LIVE_PER_VIEWER:
        # Ohne vollständigen Puffersatz hat nie ein Upload stattgefunden. Eine
        # konstante Messreihe wäre dann formal „ohne Wachstum" – und damit ein
        # falsches Grün (#711).
        findings.append(
            f"kein vollständiger Puffer-Upload nachgewiesen (Viewer hielt "
            f"höchstens {max(viewer_samples, default=0)} statt "
            f"{MIN_LIVE_PER_VIEWER} GL-Objekte)"
        )
    if live_after_cleanup != 0:
        findings.append(
            f"nach cleanup_gl() bleiben {live_after_cleanup} GL-Objekt(e) übrig"
        )
    double = tuple(ledger.double_destroys) if ledger else ()
    use_after = tuple(ledger.use_after_destroy) if ledger else ()
    if double:
        findings.append(f"{len(double)} Doppelfreigabe(n): {', '.join(double[:3])}")
    if use_after:
        findings.append(
            f"{len(use_after)} Zugriff(e) nach Freigabe: {', '.join(use_after[:3])}"
        )
    if ledger is not None and ledger.live != 0:
        findings.append(f"{ledger.live} Attrappe(n) ohne Freigabe")
    return ScenarioResult(
        name=name,
        cycles=cycles,
        source_px=source_px,
        vertices=int(mesh.positions.shape[0]),
        triangles=int(mesh.indices.shape[0]),
        decimated=bool(mesh.is_decimated),
        live_after_warmup=live_after_warmup,
        live_after_last_cycle=live_last,
        max_live=max(samples),
        max_viewer_objects=max(viewer_samples),
        live_after_cleanup=live_after_cleanup,
        created_total=created,
        destroyed_total=destroyed,
        rss_kib_start=rss_start,
        rss_kib_end=rss_end,
        double_destroys=double,
        use_after_destroy=use_after,
        findings=tuple(findings),
    )


def run_fake_scenario(
    name: str, meshes: Sequence[ReliefMesh], cycles: int, source_px: str
) -> ScenarioResult:
    """Fährt *cycles* (Wieder-)Uploads mit instrumentierten GL-Attrappen.

    Ein Zyklus entspricht genau dem Pfad, der das Leck erzeugte: ``set_mesh``
    (Cache-Wiederanzeige, 2D↔3D-Umschalten, neue HEIGHT-Daten) gefolgt vom
    Upload im nächsten Frame. Bei mehreren Meshes wechseln die Zyklen zwischen
    ihnen – das deckt „Laden/Ersetzen unterschiedlich großer HEIGHT-Daten" ab.
    """
    ledger = ResourceLedger()
    samples: list[int] = []
    viewer_samples: list[int] = []
    upload_error: str | None = None
    baseline = gl_resource_stats().live
    rss_start = rss_kib()
    with tracked_gl_resources(ledger):
        viewer = GLReliefViewer()
        for index in range(cycles):
            viewer.set_mesh(meshes[index % len(meshes)])
            try:
                viewer._ensure_buffers()
            except GLBufferError as exc:
                # Fehlgeschlagenes ``create()``/``bind()`` (#711): den Reststand
                # noch messen und den Lauf als Befund beenden – ein Traceback
                # wäre als Nachweis wertlos, ein stilles Weiterlaufen falsch.
                upload_error = str(exc)
                samples.append(gl_resource_stats().live - baseline)
                viewer_samples.append(viewer.gl_object_count)
                break
            samples.append(gl_resource_stats().live - baseline)
            viewer_samples.append(viewer.gl_object_count)
        viewer.cleanup_gl()
        live_after_cleanup = gl_resource_stats().live - baseline
    return _evaluate(
        name, cycles, meshes[0], source_px, samples, viewer_samples, ledger,
        live_after_cleanup, ledger.created, ledger.destroyed, rss_start, rss_kib(),
        upload_error=upload_error,
    )


def run_gl_scenario(
    name: str, meshes: Sequence[ReliefMesh], cycles: int, source_px: str
) -> ScenarioResult:
    """Wie :func:`run_fake_scenario`, aber mit echtem GL-Kontext und echten Puffern.

    Nur auf einer renderfähigen Qt-Plattform aufrufbar; die Messung stützt sich
    hier ausschließlich auf ``gl_object_count``/``gl_resource_stats`` (echte
    ``QOpenGLBuffer`` melden keine Doppelfreigabe).
    """
    from PyQt6.QtWidgets import QApplication

    before = gl_resource_stats()
    rss_start = rss_kib()
    viewer = GLReliefViewer()
    viewer.resize(240, 200)
    viewer.show()
    samples: list[int] = []
    viewer_samples: list[int] = []
    for index in range(cycles):
        viewer.set_mesh(meshes[index % len(meshes)])
        viewer.grab()  # erzwingt paintGL → Upload im echten Kontext
        QApplication.processEvents()
        samples.append(gl_resource_stats().live - before.live)
        viewer_samples.append(viewer.gl_object_count)
    # Ein fehlgeschlagener Viewer (Kontext-, Shader- oder Pufferfehler) rendert
    # nie: ``paintGL`` fängt den Fehler ab, es entstehen 0 GL-Objekte, und die
    # Messreihe wäre konstant 0 – also formal „kein Wachstum". Genau dieser Fall
    # darf nicht als bestandener Nachweis durchgehen (Codex-Review #706).
    if viewer.has_failed:
        raise ProbeNotExecutable(
            f"Szenario {name!r}: der GL-Viewer ist fehlgeschlagen (Kontext-/Shader-/"
            "Pufferfehler) – es wurde nichts gemessen"
        )
    if max(viewer_samples, default=0) == 0:
        raise ProbeNotExecutable(
            f"Szenario {name!r}: kein einziger Upload hat GL-Objekte erzeugt – die "
            "Plattform meldet sich renderfähig, rendert aber nicht"
        )
    # Zusätzlich zum Totalausfall: ein *unvollständiger* Puffersatz. Er entsteht,
    # wenn ``QOpenGLBuffer.create()``/``bind()`` still ``false`` liefern; der
    # Viewer erkennt das seit #711 und gibt frei, die Sonde darf die Messreihe
    # danach trotzdem nicht als Nachweis werten.
    if max(viewer_samples) < MIN_LIVE_PER_VIEWER:
        raise ProbeNotExecutable(
            f"Szenario {name!r}: unvollständiger Puffer-Upload – der Viewer hielt "
            f"höchstens {max(viewer_samples)} statt {MIN_LIVE_PER_VIEWER} GL-Objekte "
            "(fehlgeschlagenes create()/bind()); es wurde nichts Belastbares gemessen"
        )
    viewer.cleanup_gl()
    live_after_cleanup = gl_resource_stats().live - before.live
    viewer.deleteLater()
    QApplication.processEvents()
    after = gl_resource_stats()
    return _evaluate(
        name, cycles, meshes[0], source_px, samples, viewer_samples, None,
        live_after_cleanup, after.created - before.created,
        after.destroyed - before.destroyed, rss_start, rss_kib(),
    )


# ── Qt-Anwendung ───────────────────────────────────────────────────────

#: Die ``QApplication`` muss prozessweit referenziert bleiben – wird sie
#: eingesammelt, während Widgets leben, endet der Lauf im Segfault.
_APP: Any = None


def ensure_app() -> Any:
    """Liefert die (ggf. neu erzeugte) ``QApplication`` und hält sie am Leben."""
    global _APP
    from PyQt6.QtWidgets import QApplication

    existing = QApplication.instance()
    if isinstance(existing, QApplication):
        _APP = existing
    elif _APP is None:
        _APP = QApplication([])
    return _APP


# ── Umgebung ───────────────────────────────────────────────────────────


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        )
    except OSError:  # pragma: no cover – ohne git im PATH
        return "unbekannt"
    return out.stdout.strip() if out.returncode == 0 else "unbekannt"


def environment_info() -> dict[str, str]:
    """Umgebungsangaben für den Nachweis (Akzeptanzkriterium 1 aus #684)."""
    from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
    from PyQt6.QtGui import QGuiApplication

    from bgremover import __version__
    from bgremover.preview3d_capability import probe_3d_capability

    capability = probe_3d_capability(use_cache=False)
    return {
        "commit": _git_commit(),
        "bgremover": __version__,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "qt": QT_VERSION_STR,
        "pyqt": PYQT_VERSION_STR,
        "qpa_platform": QGuiApplication.platformName() or "-",
        "gl_capability": "ok" if capability.ok else "nicht verfügbar",
        "gl_diagnostic": capability.diagnostic or "-",
    }


def rss_kib() -> int:
    """Aktueller Arbeitsspeicher des Prozesses in KiB (0 = nicht ermittelbar).

    Ergänzender Beobachtungswert neben der Objektzählung: unter Linux exakt aus
    ``/proc/self/statm``, sonst best-effort über den Spitzenwert von ``resource``.
    Ein GL-Leck zeigt sich dort nur indirekt (Treiberspeicher liegt oft außerhalb
    des RSS) – der verbindliche Messwert bleibt die Objektzählung.
    """
    try:
        fields = Path("/proc/self/statm").read_text("ascii").split()
        return int(fields[1]) * (os.sysconf("SC_PAGE_SIZE") // 1024)
    except (OSError, IndexError, ValueError):
        pass
    try:
        import resource

        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except (ImportError, ValueError):  # pragma: no cover – exotische Plattform
        return 0


def _stats_dict() -> dict[str, int]:
    stats = gl_resource_stats()
    return {"created": stats.created, "destroyed": stats.destroyed, "live": stats.live}


# ── Lauf ───────────────────────────────────────────────────────────────


def run_probe(mode: str, cycles: int, sizes: Sequence[tuple[str, int, MeshQuality]]) -> ProbeReport:
    """Führt alle Szenarien aus und liefert den Bericht."""
    runner = run_gl_scenario if mode == "gl" else run_fake_scenario
    report = ProbeReport(
        mode=mode,
        environment=environment_info(),
        stats_before=_stats_dict(),
        stats_after={},
        memory={"rss_before": rss_kib(), "rss_after": 0},
    )
    meshes: list[ReliefMesh] = []
    for label, size, quality in sizes:
        mesh = build_relief_mesh(build_field(size), quality)
        meshes.append(mesh)
        report.scenarios.append(runner(label, [mesh], cycles, f"{size}×{size}"))
    if len(meshes) > 1:
        # „Laden/Ersetzen unterschiedlich großer HEIGHT-Daten" in einem Viewer.
        report.scenarios.append(
            runner(
                "wechselnd",
                meshes,
                cycles,
                "+".join(f"{size}×{size}" for _, size, _ in sizes),
            )
        )
    if mode != "gl":
        # Fehlerpfad: vollständig ungedeckte Höhendaten ergeben ein Mesh ohne
        # Dreiecke. Es darf weder werfen noch Ressourcen zurücklassen.
        empty = build_relief_mesh(build_field(64, empty_coverage=True), MeshQuality.REDUCED)
        report.scenarios.append(run_fake_scenario("leere-daten", [empty], cycles, "64×64"))
    report.stats_after = _stats_dict()
    report.memory["rss_after"] = rss_kib()
    return report


def _parse_sizes(raw: str) -> tuple[tuple[str, int, MeshQuality], ...]:
    """``klein:64:REDUCED,gross:2048:STANDARD`` → Szenarienliste."""
    scenarios: list[tuple[str, int, MeshQuality]] = []
    for chunk in raw.split(","):
        parts = chunk.split(":")
        if len(parts) != 3:
            raise argparse.ArgumentTypeError(f"Erwartet NAME:PIXEL:QUALITÄT, erhalten {chunk!r}")
        name, size, quality = parts[0], parts[1], parts[2].upper()
        if not size.isdigit() or int(size) < 2:
            raise argparse.ArgumentTypeError(f"Ungültige Kantenlänge: {size!r}")
        if quality not in MeshQuality.__members__:
            raise argparse.ArgumentTypeError(f"Unbekannte Qualität: {quality!r}")
        scenarios.append((name, int(size), MeshQuality[quality]))
    return tuple(scenarios)


def _print_human(report: ProbeReport) -> None:
    env = report.environment
    print(f"GL-Ressourcensonde – Modus {report.mode}, Commit {env['commit'][:12]}")
    print(f"  {env['platform']} | Python {env['python']} | Qt {env['qt']} "
          f"| QPA {env['qpa_platform']} | GL {env['gl_capability']}")
    for scenario in report.scenarios:
        print(
            f"  {scenario.name:<12} {scenario.source_px:>18}  "
            f"{scenario.cycles} Zyklen  live {scenario.live_after_warmup}"
            f"→{scenario.live_after_last_cycle} (max {scenario.max_live}, "
            f"Viewer max {scenario.max_viewer_objects}), "
            f"erzeugt {scenario.created_total}/freigegeben {scenario.destroyed_total}, "
            f"nach cleanup {scenario.live_after_cleanup}, "
            f"RSS {scenario.rss_kib_start}→{scenario.rss_kib_end} KiB"
        )
    print(f"  Zähler gesamt: {report.stats_before} → {report.stats_after}")
    print(f"  RSS: {report.memory.get('rss_before', 0)} KiB → "
          f"{report.memory.get('rss_after', 0)} KiB")
    if not report.gating:
        print(
            f"HINWEIS Kurzlauf unter {MIN_GATING_CYCLES} Zyklen – Diagnose, "
            "**kein** abnahmefähiger Nachweis für #684"
        )
    if report.findings:
        for finding in report.findings:
            print(f"BEFUND  {finding}")
    else:
        print("OK      kein Ressourcenbefund")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=("fake", "gl"), default="fake",
                        help="fake = instrumentierte Attrappen (überall), gl = echter Kontext")
    parser.add_argument("--cycles", type=int, default=120,
                        help=f"Aktualisierungszyklen je Szenario (Standard 120, "
                             f"Minimum {MIN_GATING_CYCLES} laut #684)")
    parser.add_argument(
        "--allow-short-run", action="store_true",
        help=f"weniger als {MIN_GATING_CYCLES} Zyklen zulassen – der Bericht wird "
             "dann ausdrücklich als nicht abnahmefähig gekennzeichnet (Diagnose)",
    )
    parser.add_argument("--sizes", type=_parse_sizes, default=DEFAULT_SIZES,
                        help="NAME:PIXEL:QUALITÄT, kommagetrennt")
    parser.add_argument("--json-out", type=Path, help="Bericht zusätzlich als JSON-Datei schreiben")
    parser.add_argument("--quiet", action="store_true", help="nur JSON auf stdout")
    args = parser.parse_args(argv)

    if args.cycles < 1:
        parser.error("--cycles muss mindestens 1 sein")
    if args.cycles < MIN_GATING_CYCLES and not args.allow_short_run:
        parser.error(
            f"--cycles {args.cycles} unterschreitet die geforderten "
            f"{MIN_GATING_CYCLES} Zyklen (#684): ein kurzer Lauf ersetzt zu wenig "
            "Puffer, um ein Leck zu zeigen. Für einen bewusst nicht abnahmefähigen "
            "Diagnoselauf --allow-short-run setzen."
        )

    from PyQt6.QtGui import QGuiApplication

    ensure_app()
    platform_name = QGuiApplication.platformName()
    if args.mode == "gl" and platform_name in NON_RENDERABLE_PLATFORMS:
        print(
            f"Modus 'gl' braucht eine renderfähige Qt-Plattform – aktuell "
            f"{platform_name!r}. QT_QPA_PLATFORM setzen (z. B. xcb/wayland/cocoa).",
            file=sys.stderr,
        )
        return 2

    try:
        report = run_probe(args.mode, args.cycles, args.sizes)
    except ProbeNotExecutable as exc:
        print(f"Sonde nicht ausführbar: {exc}", file=sys.stderr)
        return 2
    report.gating = args.cycles >= MIN_GATING_CYCLES
    payload = report.to_json()
    if args.json_out:
        args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", "utf-8")
    if args.quiet:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _print_human(report)
    return 1 if report.findings else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
