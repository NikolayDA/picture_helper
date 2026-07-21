#!/usr/bin/env python3
"""Performance-Benchmark für die Bildverarbeitung von BgRemover.

Misst die Verarbeitungszeit **pro Bildformat** (PNG, JPEG, WebP, TIFF) über die
echten Code-Pfade des Pakets (``bgremover.image_ops``): Encode, Decode und eine
repräsentative Verarbeitungs-Pipeline (Laden → Drehen → Ecken runden →
Zuschneiden → Speichern).

Drei Unterbefehle:

- ``run``     – Benchmark ausführen, Ergebnis als datiertes JSON unter
               ``benchmarks/results/`` ablegen und – falls ein früherer Lauf
               existiert – direkt gegen den jüngsten vergleichen.
- ``compare`` – Zwei vorhandene Ergebnis-Dateien vergleichen (oder das aktuellste
               gegen das vorherige), Regressionen jenseits der Schwelle melden
               und optional GitHub-Issues anlegen.
- ``paired-compare`` – Mehrere auf demselben Runner erzeugte Baseline-/Current-
                       Paare aggregieren und als A/B-Nachweis vergleichen.

Die *Vergleichslogik* ist bewusst von der (zeitabhängigen) Messung getrennt und
in reinen Funktionen gekapselt, damit sie deterministisch testbar bleibt.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from bgremover.image_ops import (  # noqa: E402  (Pfad muss vor dem Import stehen)
    crop_image,
    rotate_image,
    round_corners,
    save_image_file,
)

if TYPE_CHECKING:
    from bgremover.height_map import HeightField
    from bgremover.relief_mesh import MeshQuality

# Format-Label → Default-Suffix. Spiegelt bewusst ``image_ops.SAVE_FORMATS``;
# als getrennte Liste gehalten, damit der Benchmark auch dann eine stabile
# Reihenfolge hat, wenn sich die Dialog-Filter ändern.
BENCH_FORMATS: dict[str, str] = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "WebP": ".webp",
    "TIFF": ".tif",
}

# 16-Bit-Höhenpipeline (#590, Baseline aus ADR #586): Import, repräsentative
# Operation (separabler Gauß), .bgrproj-Roundtrip und Relief-Preview je
# Projektgröße. Iterationszahl fällt mit der Bildgröße (40 MP: 1 Messung).
HEIGHT_BENCH_SIZES: dict[str, tuple[int, int, int]] = {
    "HEIGHT16-1MP": (1000, 1000, 5),
    "HEIGHT16-16MP": (4000, 4000, 3),
    "HEIGHT16-40MP": (8000, 5000, 1),
}

DEFAULT_ITERATIONS = 7
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
DEFAULT_THRESHOLD = 10.0  # Prozent; darüber gilt ein Format als degradiert.
DEFAULT_METRIC = "process_ms"
DEFAULT_CONFIRM_RUNS = 3  # Gesamtläufe, um eine Auffälligkeit zu bestätigen.
DEFAULT_MINIMUM_PAIRS = 4  # Gerade Zahl: beide A/B-Reihenfolgen gleich oft.
RESULTS_DIR = ROOT / "benchmarks" / "results"
# Schema 3 ergänzt die Benchmark-Suite, den vollständigen Runner-Fingerprint und
# Rohmessungen. Ältere Läufe dürfen deshalb nicht automatisch als vergleichbare
# Baseline gelten (#630).
SCHEMA_VERSION = 3
DEFAULT_API_URL = "https://api.github.com"


# ── Synthetisches Testbild ───────────────────────────────────────────────

def make_sample_image(width: int, height: int) -> Image.Image:
    """Deterministisches RGBA-Bild mit Verläufen, Rauschen und Transparenz.

    Reine Volltonflächen würden alle Encoder unrealistisch schnell machen; die
    Mischung aus Farbverlauf und pseudo-zufälligem Rauschen erzeugt für PNG/WebP
    eine plausible Kompressionslast. Der Alpha-Verlauf hält den RGBA-Pfad
    (inkl. JPEG-Hintergrundkomposition) ehrlich. ``numpy`` wird lokal importiert,
    damit das Modul ohne die volle App-Umgebung importierbar bleibt.
    """
    import numpy as np

    rng = np.random.default_rng(seed=20260608)
    ys = np.linspace(0, 255, height, dtype=np.uint16)[:, None]
    xs = np.linspace(0, 255, width, dtype=np.uint16)[None, :]
    r = ((xs + ys) // 2).astype(np.uint8)
    g = np.broadcast_to(ys.astype(np.uint8), (height, width))
    b = np.broadcast_to(xs.astype(np.uint8), (height, width))
    noise = rng.integers(0, 48, size=(height, width), dtype=np.uint8)
    r = r + noise  # uint8 + uint8 läuft bewusst modulo 256 über (Rauschband)
    a = np.linspace(40, 255, width, dtype=np.uint8)[None, :]
    a = np.broadcast_to(a, (height, width))
    arr = np.dstack([r, g, b, a]).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# ── Messung ──────────────────────────────────────────────────────────────

def _measure_ms(fn: Callable[[], Any], iterations: int) -> tuple[float, list[float]]:
    """Median und Rohwerte von ``fn`` in Millisekunden zurückgeben."""
    samples: list[float] = []
    for _ in range(max(1, iterations)):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    return statistics.median(samples), [round(value, 4) for value in samples]


def _median_ms(fn: Callable[[], Any], iterations: int) -> float:
    """Robusten Median einer Messreihe in Millisekunden zurückgeben."""
    median, _samples = _measure_ms(fn, iterations)
    return median


def _benchmark_format_with_samples(
    img: Image.Image, fmt: str, suffix: str, iterations: int, work_dir: Path,
) -> tuple[dict[str, float], dict[str, list[float]]]:
    """Format messen und zusätzlich die einzelnen Zeitwerte erhalten."""
    target = work_dir / f"bench{suffix}"

    encode_ms, encode_samples = _measure_ms(
        lambda: save_image_file(img, target), iterations,
    )
    encoded_bytes = target.stat().st_size

    def _decode() -> None:
        with Image.open(target) as handle:
            handle.load()

    decode_ms, decode_samples = _measure_ms(_decode, iterations)

    out = work_dir / f"bench_out{suffix}"

    def _process() -> None:
        with Image.open(target) as handle:
            handle.load()
            stage = rotate_image(handle, 90)
        stage, _ = round_corners(stage, 48)
        w, h = stage.size
        stage = crop_image(stage, (0, 0, w * 3 // 4, h * 3 // 4), is_circle=False)
        save_image_file(stage, out)

    process_ms, process_samples = _measure_ms(_process, iterations)
    metrics = {
        "encode_ms": round(encode_ms, 4),
        "decode_ms": round(decode_ms, 4),
        "process_ms": round(process_ms, 4),
        "encoded_bytes": float(encoded_bytes),
    }
    samples = {
        "encode_ms": encode_samples,
        "decode_ms": decode_samples,
        "process_ms": process_samples,
    }
    return metrics, samples


def benchmark_format(
    img: Image.Image, fmt: str, suffix: str, iterations: int, work_dir: Path,
) -> dict[str, float]:
    """Misst Encode-, Decode- und End-to-End-Verarbeitungszeit für ein Format."""
    metrics, _samples = _benchmark_format_with_samples(
        img, fmt, suffix, iterations, work_dir,
    )
    return metrics


def git_commit() -> str | None:
    """Kurzer Commit-Hash des aktuellen Stands, oder ``None`` außerhalb von git."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None if out.returncode == 0 else None


def _cpu_model() -> str | None:
    """Möglichst genaue CPU-Bezeichnung ohne zusätzliche Abhängigkeit liefern."""
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        try:
            for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
                key, separator, value = line.partition(":")
                if separator and key.strip().lower() in {"model name", "hardware"}:
                    model = value.strip()
                    if model:
                        return model
        except OSError:
            pass

    import platform

    return platform.processor() or None


def collect_environment() -> dict[str, Any]:
    """Umgebungs-Fingerprint des aktuellen Laufs.

    Hält fest, *worauf* gemessen wurde, damit der Vergleich später entscheiden
    kann, ob zwei Läufe überhaupt vergleichbar sind (#277/#278/#279): Software-
    versionen, Betriebssystem-/Runner-Image und CPU-Modell sind harte
    Vergleichsbedingungen. Das verhindert, dass ein Wechsel des GitHub-Hosted-
    Runners wie bei #630 als Anwendungsregression gemeldet wird.
    """
    import platform

    try:
        from PIL import __version__ as detected_pillow_version

        pillow_version: str | None = detected_pillow_version
    except Exception:  # pragma: no cover - Pillow ist Pflicht, defensiv dennoch
        pillow_version = None
    try:
        import numpy

        numpy_version: str | None = numpy.__version__
    except Exception:  # pragma: no cover - NumPy ist Pflicht, defensiv dennoch
        numpy_version = None

    return {
        "python": platform.python_version(),
        "pillow": pillow_version,
        "numpy": numpy_version,
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor() or None,
        "cpu_model": _cpu_model(),
        "cpu_count": os.cpu_count(),
        "runner_arch": os.environ.get("RUNNER_ARCH"),
        "runner_environment": os.environ.get("RUNNER_ENVIRONMENT"),
        # GitHub setzt diese beiden Runner-Variablen absichtlich in CamelCase.
        "runner_image_os": os.environ.get("ImageOS"),  # noqa: SIM112
        "runner_image_version": os.environ.get("ImageVersion"),  # noqa: SIM112
        "runner": os.environ.get("RUNNER_NAME")
        or os.environ.get("RUNNER_OS")
        or "local",
    }


def make_height_values(width: int, height: int) -> np.ndarray:
    """Deterministisches 16-Bit-Höhenmuster mit gesetzten Niederbits.

    Baut das Muster aus 1-D-Zeilen-/Spaltenvektoren per Broadcasting statt über
    ``np.mgrid`` – bei 40 MP spart das zwei volle int64-Koordinatengitter
    (~640 MiB transienter Zusatzspeicher), bevor überhaupt das eigentliche
    ``uint16``-Höhenfeld sowie die PNG-/Blur-/Preview-Puffer angelegt werden.
    """
    xx = np.arange(width, dtype=np.int64)
    yy = np.arange(height, dtype=np.int64).reshape(-1, 1)
    return ((xx * 131 + yy * 17) % 65536).astype(np.uint16)


def benchmark_mesh_build(
    field: HeightField, iterations: int,
    quality: MeshQuality | None = None,
) -> dict[str, float]:
    """Misst den 3D-Reliefmesh-Aufbau über den echten Geometriekern (#595).

    Baut das begrenzte Grid-Mesh (:func:`~bgremover.relief_mesh.build_relief_mesh`)
    aus der **kanonischen** 16-Bit-Payload – exakt der Pfad des ``MeshBuildWorker``
    im Viewer, nur ohne Qt/GL. Metriken:

    - ``mesh_build_ms`` – Median-Bauzeit (Näherung „Zeit bis erste sichtbare
      Vorschau", GPU-Upload/Framerate sind hardwaregebunden und im manuellen
      Plattform-Smoke belegt).
    - ``mesh_peak_mb`` – transienter Peak-Speicher **eines** Baus (``tracemalloc``,
      gleiches Muster wie ``test_relief_mesh.test_wide_aspect_is_memory_bounded``).
      Belegt reproduzierbar, dass auch 40 MP kein Vollmesh materialisiert
      (64-MiB-Decimation-Deckel + Zielgitter-Budget).
    - ``mesh_vertices`` / ``mesh_triangles`` – tatsächliche Gittergröße gegen das
      harte Qualitätsbudget (``quality.max_vertices``/``max_triangles``).
    - ``mesh_decimation`` – Vereinfachungsfaktor (``1`` = keine Decimation).

    ``mesh_build_ms`` ist eine reguläre Zeit-Metrik und läuft damit durch dieselbe
    Regressions-/Bestätigungslogik wie ``process_ms`` (Vergleich per
    ``--metric mesh_build_ms``).
    """
    from bgremover.relief_mesh import MeshQuality, build_relief_mesh

    selected_quality = quality or MeshQuality.STANDARD
    mesh_build_ms = _median_ms(
        lambda: build_relief_mesh(field, selected_quality), iterations,
    )

    # Ein einzelner, getrennt verfolgter Bau für den Peak – der Median-Lauf oben
    # verfälschte die Hochwassermarke sonst über wiederholte Allokationen.
    tracemalloc.start()
    tracemalloc.reset_peak()
    mesh = build_relief_mesh(field, selected_quality)
    _current, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "mesh_build_ms": mesh_build_ms,
        "mesh_peak_mb": round(peak_bytes / (1024.0 * 1024.0), 3),
        "mesh_vertices": float(mesh.vertex_count),
        "mesh_triangles": float(mesh.triangle_count),
        "mesh_decimation": float(mesh.decimation_factor),
    }


def benchmark_height_pipeline(
    width: int, height: int, iterations: int, work_dir: Path
) -> dict[str, float]:
    """Misst die 16-Bit-Höhenpipeline über die echten Code-Pfade (#590/#595).

    Metriken je Größe: ``import_ms`` (natives 16-Bit-PNG → ``HeightField``),
    ``process_ms`` (separabler ``gaussian_blur`` als repräsentative Operation –
    zugleich die Standard-Vergleichsmetrik des Benchmarks), ``roundtrip_ms``
    (``.bgrproj`` Save + Open, Formatversion 2), ``preview_ms``
    (2D-Relief-Hillshade + Compose aus der kanonischen Payload) sowie die
    ``mesh_*``-Metriken des 3D-Reliefmesh-Aufbaus (:func:`benchmark_mesh_build`,
    #595) – dieselben 1/16/40-MP-Szenarien tragen damit auch die 3D-Baseline.
    """
    from bgremover.height_map import HeightField, image_to_height_field
    from bgremover.height_ops import gaussian_blur
    from bgremover.project_io import load_project, save_project
    from bgremover.project_model import LayerKind, Project
    from bgremover.relief_preview import compose_over, relief_shading

    values = make_height_values(width, height)
    coverage = np.full((height, width), 255, dtype=np.uint8)
    field = HeightField(values, coverage, max_value=65535)

    png_path = work_dir / f"height16-{width}x{height}.png"
    raw = np.ascontiguousarray(values, dtype="<u2").tobytes()
    Image.frombytes("I;16", (width, height), raw).save(png_path)

    def _import() -> None:
        with Image.open(png_path) as img:
            img.load()
            image_to_height_field(img)

    import_ms = _median_ms(_import, iterations)
    process_ms = _median_ms(lambda: gaussian_blur(field, 2.0), iterations)

    project = Project(width, height)
    project.create_layer(name="H", kind=LayerKind.HEIGHT, height_data=field)
    proj_path = work_dir / f"height16-{width}x{height}.bgrproj"

    def _roundtrip() -> None:
        save_project(project, proj_path)
        load_project(proj_path)

    roundtrip_ms = _median_ms(_roundtrip, iterations)

    base = Image.new("RGBA", (width, height), (128, 96, 64, 255))

    def _preview() -> None:
        compose_over(
            base,
            relief_shading(field, azimuth=315.0, elevation=45.0, strength=1.0),
            strength=0.7,
        )

    preview_ms = _median_ms(_preview, iterations)
    metrics = {
        "import_ms": import_ms,
        "process_ms": process_ms,
        "roundtrip_ms": roundtrip_ms,
        "preview_ms": preview_ms,
    }
    metrics.update(benchmark_mesh_build(field, iterations))
    return metrics


# ── Live-GL-Performance-Suite (#645) ────────────────────────────────────────
# Misst die GPU-gebundenen Metriken der 3D-Vorschau (Zeit bis erstes Bild,
# VBO/IBO-Upload, Framerate, Peak-Speicher). Diese brauchen einen echten
# Hardware-GL-Kontext; die Offscreen-CI kann sie nicht ehrlich liefern und die
# Suite verweigert dort die Messung. Die Messlogik selbst ist über injizierbare
# Hooks Qt-frei getestet; nur der reale Hook (``_QtGlLiveHooks``) berührt Qt/GL.

# Szenarien wie die HEIGHT-Suite; Frames je Szenario für die Frame-Zeit-Statistik.
PREVIEW3D_LIVE_SIZES: dict[str, tuple[int, int]] = {
    "HEIGHT16-1MP": (1000, 1000),
    "HEIGHT16-16MP": (4000, 4000),
    "HEIGHT16-40MP": (8000, 5000),
}
PREVIEW3D_LIVE_FRAMES = 60


class Preview3DLiveUnavailable(RuntimeError):
    """Kein echter Hardware-GL-Kontext – die Live-Messung wird verweigert."""


def _percentile(values: list[float], q: float) -> float:
    """Linear interpoliertes Perzentil ``q`` (0..100) einer Messreihe."""
    if not values:
        return float("nan")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (q / 100.0) * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    frac = rank - low
    return ordered[low] * (1.0 - frac) + ordered[high] * frac


def summarize_frame_times(frame_ms: list[float]) -> dict[str, float]:
    """Frame-Zeiten zu p50/p95 verdichten (→ Framerate-Aussage)."""
    return {
        "gl_frame_ms_p50": round(_percentile(frame_ms, 50.0), 4),
        "gl_frame_ms_p95": round(_percentile(frame_ms, 95.0), 4),
    }


def probe_live_gl() -> tuple[bool, str]:
    """Prüft, ob ein echter Hardware-GL-Kontext vorliegt.

    Nutzt dieselbe Capability-Probe wie der Viewer und die geteilte
    Software-Renderer-Regel (``bgremover.renderer_provenance``). Liefert
    ``(verfügbar, diagnose)``; Software-Renderer (llvmpipe) gelten als **nicht**
    verfügbar.
    """
    from bgremover.preview3d_capability import probe_3d_capability
    from bgremover.renderer_provenance import is_software_renderer

    capability = probe_3d_capability(use_cache=False)
    if not capability.ok:
        return False, ""
    if is_software_renderer(capability.diagnostic):
        return False, capability.diagnostic
    return True, capability.diagnostic


class LiveGlHooks:
    """Injizierbare GL-Messhaken (Qt-frei testbar über Fakes).

    Alle Zeitmessungen in Millisekunden. Der Default-Hook (``_QtGlLiveHooks``)
    berührt Qt/GL; Tests reichen einen Fake mit festen Zeiten herein.
    """

    def upload(self, mesh: Any) -> float:
        raise NotImplementedError

    def first_frame(self) -> float:
        raise NotImplementedError

    def frame(self) -> float:
        raise NotImplementedError

    def peak_mb(self) -> float:
        raise NotImplementedError

    def close(self) -> None:
        """Optionale Freigabe kontextgebundener Ressourcen nach einem Szenario."""
        return None


def measure_preview3d_live(
    mesh: Any, hooks: LiveGlHooks, frames: int = PREVIEW3D_LIVE_FRAMES,
) -> dict[str, float]:
    """Live-GL-Metriken aus den Hooks zusammensetzen (reine Orchestrierung).

    ``gl_upload_ms`` (Buffer-Upload), ``gl_first_frame_ms`` (Mesh-Ready → erstes
    Bild), ``gl_frame_ms_p50``/``_p95`` (Orbit-Frames) und ``gl_peak_mb``.
    """
    try:
        upload_ms = hooks.upload(mesh)
        first_ms = hooks.first_frame()
        frame_ms = [hooks.frame() for _ in range(max(1, frames))]
        metrics = {
            "gl_upload_ms": round(upload_ms, 4),
            "gl_first_frame_ms": round(first_ms, 4),
            "gl_peak_mb": round(hooks.peak_mb(), 3),
        }
        metrics.update(summarize_frame_times(frame_ms))
        return metrics
    finally:
        hooks.close()


def _live_height_field(width: int, height: int) -> HeightField:
    """Deterministisches, glattes 16-Bit-Höhenfeld für die Live-Messung."""
    from bgremover.height_map import HeightField

    ys = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
    xs = np.linspace(0.0, 1.0, width, dtype=np.float32)[None, :]
    ramp = (0.5 + 0.5 * np.sin(6.28318 * (xs + ys))) * 65535.0
    values = ramp.astype(np.uint16)
    coverage = np.full((height, width), 255, np.uint8)
    return HeightField(values, coverage, max_value=65535)


def benchmark_preview3d_live(
    width: int, height: int, quality: Any | None = None,
    hooks: LiveGlHooks | None = None, frames: int = PREVIEW3D_LIVE_FRAMES,
) -> dict[str, float]:
    """Live-GL-Suite für **ein** Szenario (Mesh-Build → GL-Messung).

    Baut das Mesh über den echten Geometriekern und misst die GPU-gebundenen
    Metriken über die Hooks. Ohne echten Hardware-GL-Kontext (bzw. mit
    Software-Renderer) wirft die Funktion ``Preview3DLiveUnavailable`` – sie
    liefert nie stumm llvmpipe-Werte als Hardware-Protokoll.
    """
    from bgremover.relief_mesh import MeshQuality, build_relief_mesh

    if hooks is None:
        available, diagnostic = probe_live_gl()
        if not available:
            raise Preview3DLiveUnavailable(
                f"Kein Hardware-GL-Kontext für die Live-Messung (Diagnose: "
                f"{diagnostic or 'kein GL'})."
            )
        hooks = _QtGlLiveHooks(diagnostic)
    mesh = build_relief_mesh(_live_height_field(width, height), quality or MeshQuality.STANDARD)
    return measure_preview3d_live(mesh, hooks, frames)


class _QtGlLiveHooks(LiveGlHooks):
    """Realer GL-Hook: Offscreen-Kontext + Viewer-Shader (hardware-only, #645).

    **In der Offscreen-CI nicht ausführbar** (dort greift die Verweigerung in
    ``benchmark_preview3d_live``); wird auf einem Self-hosted Runner mit echter
    GPU zum ersten Mal validiert. Wiederverwendet exakt die Kontext-Erzeugung
    der Capability-Probe und die GLSL-Quellen aus ``viewer_3d``.
    """

    def __init__(self, diagnostic: str) -> None:
        self.diagnostic = diagnostic
        self._built = False
        self._buffer_bytes = 0
        self._frame_number = 0
        self._pos: Any = None
        self._slope: Any = None
        self._idx: Any = None
        self._vao: Any = None

    def _build(self) -> None:  # pragma: no cover - hardwaregebunden
        from PyQt6.QtGui import QOffscreenSurface, QOpenGLContext, QSurfaceFormat
        from PyQt6.QtOpenGL import (
            QOpenGLFramebufferObject,
            QOpenGLShader,
            QOpenGLShaderProgram,
            QOpenGLVersionFunctionsFactory,
            QOpenGLVersionProfile,
            QOpenGLVertexArrayObject,
        )

        from bgremover.viewer_3d import _FRAGMENT_SHADER, _VERTEX_SHADER

        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)
        fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
        self._ctx = QOpenGLContext()
        self._ctx.setFormat(fmt)
        if not self._ctx.create():
            raise Preview3DLiveUnavailable("QOpenGLContext.create() fehlgeschlagen")
        self._surface = QOffscreenSurface()
        self._surface.setFormat(self._ctx.format())
        self._surface.create()
        if not self._surface.isValid() or not self._ctx.makeCurrent(self._surface):
            raise Preview3DLiveUnavailable("Kein aktueller Offscreen-Kontext")
        profile = QOpenGLVersionProfile()
        profile.setVersion(2, 1)
        self._fns = QOpenGLVersionFunctionsFactory.get(profile, self._ctx)
        if self._fns is None:
            raise Preview3DLiveUnavailable("Keine GL-2.1-Versionsfunktionen")
        self._fbo = QOpenGLFramebufferObject(
            512, 512, QOpenGLFramebufferObject.Attachment.CombinedDepthStencil,
        )
        if not self._fbo.isValid():
            raise Preview3DLiveUnavailable("GL-Framebuffer ist ungültig")

        self._program = QOpenGLShaderProgram()
        if not self._program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Vertex, _VERTEX_SHADER,
        ):
            raise Preview3DLiveUnavailable(f"Vertex-Shader: {self._program.log()}")
        if not self._program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Fragment, _FRAGMENT_SHADER,
        ):
            raise Preview3DLiveUnavailable(f"Fragment-Shader: {self._program.log()}")
        if not self._program.link():
            raise Preview3DLiveUnavailable(f"Programm-Link: {self._program.log()}")
        self._vao = QOpenGLVertexArrayObject()
        if not self._vao.create():
            self._vao = None
        self._built = True

    def upload(self, mesh: Any) -> float:  # pragma: no cover - hardwaregebunden
        if not self._built:
            self._build()
        from PyQt6.QtOpenGL import QOpenGLBuffer

        from bgremover.preview3d_camera import OrbitCamera

        start = time.perf_counter()
        positions = np.ascontiguousarray(mesh.positions, np.float32)
        slopes = np.ascontiguousarray(mesh.slope, np.float32)
        indices = np.ascontiguousarray(mesh.indices, np.uint32).ravel()
        self._pos = self._make_buffer(QOpenGLBuffer.Type.VertexBuffer, positions)
        self._slope = self._make_buffer(QOpenGLBuffer.Type.VertexBuffer, slopes)
        self._idx = self._make_buffer(QOpenGLBuffer.Type.IndexBuffer, indices)
        self._index_count = int(indices.size)
        self._buffer_bytes = positions.nbytes + slopes.nbytes + indices.nbytes
        self._camera = OrbitCamera()
        lo, hi = mesh.bounds
        self._camera.reset(lo, hi)
        self._fns.glFinish()
        return (time.perf_counter() - start) * 1000.0

    @staticmethod
    def _make_buffer(buffer_type: Any, data: np.ndarray) -> Any:  # pragma: no cover
        from PyQt6.QtOpenGL import QOpenGLBuffer

        buffer = QOpenGLBuffer(buffer_type)
        if not buffer.create():
            raise Preview3DLiveUnavailable("GL-Buffer konnte nicht erzeugt werden")
        buffer.bind()
        raw = data.tobytes()
        buffer.allocate(raw, len(raw))
        buffer.release()
        return buffer

    @staticmethod
    def _bind_attribute(program: Any, name: str, vbo: Any, components: int) -> None:
        from bgremover.viewer_3d import _GL_FLOAT

        location = program.attributeLocation(name)
        if location < 0:
            raise Preview3DLiveUnavailable(f"Shader-Attribut fehlt: {name}")
        vbo.bind()
        program.enableAttributeArray(location)
        program.setAttributeBuffer(location, _GL_FLOAT, 0, components, 0)

    def _draw(self) -> float:  # pragma: no cover - hardwaregebunden
        from bgremover.viewer_3d import (
            _GL_COLOR_BUFFER_BIT,
            _GL_DEPTH_BUFFER_BIT,
            _GL_DEPTH_TEST,
            _GL_TRIANGLES,
            _GL_UNSIGNED_INT,
            _light_direction,
            _qmatrix,
        )

        start = time.perf_counter()
        if not self._ctx.makeCurrent(self._surface):
            raise Preview3DLiveUnavailable("GL-Kontext vor Frame nicht aktuell")
        self._camera.orbit(0.75, 0.15)
        self._fbo.bind()
        self._fns.glViewport(0, 0, 512, 512)
        self._fns.glClearColor(0.02, 0.025, 0.035, 1.0)
        self._fns.glEnable(_GL_DEPTH_TEST)
        self._fns.glClear(_GL_COLOR_BUFFER_BIT | _GL_DEPTH_BUFFER_BIT)

        self._program.bind()
        mvp = self._camera.projection_matrix(1.0) @ self._camera.view_matrix()
        self._program.setUniformValue(
            self._program.uniformLocation("u_mvp"), _qmatrix(mvp),
        )
        self._program.setUniformValue(
            self._program.uniformLocation("u_exagg"), 1.0,
        )
        lx, ly, lz = _light_direction(315.0, 45.0)
        self._program.setUniformValue(
            self._program.uniformLocation("u_light_dir"), lx, ly, lz,
        )
        self._program.setUniformValue(
            self._program.uniformLocation("u_color"), 0.72, 0.74, 0.78,
        )
        if self._vao is not None:
            self._vao.bind()
        self._bind_attribute(self._program, "a_pos", self._pos, 3)
        self._bind_attribute(self._program, "a_slope", self._slope, 2)
        self._idx.bind()
        self._fns.glDrawElements(
            _GL_TRIANGLES, self._index_count, _GL_UNSIGNED_INT, None,
        )
        self._idx.release()
        if self._vao is not None:
            self._vao.release()
        self._program.release()
        self._fns.glFinish()
        self._fbo.release()
        self._frame_number += 1
        return (time.perf_counter() - start) * 1000.0

    def first_frame(self) -> float:  # pragma: no cover - hardwaregebunden
        elapsed = self._draw()
        # Ein Draw-Call allein beweist noch keine Geometrie. Der einmalige
        # Readback liegt bewusst außerhalb der gemessenen Framezeit und weist
        # nach, dass der Viewer-Shader tatsächlich Pixel vom Clear-Wert abhebt.
        image = self._fbo.toImage().scaled(32, 32)
        colors = {
            image.pixel(x, y)
            for y in range(image.height())
            for x in range(image.width())
        }
        if image.isNull() or len(colors) < 2:
            raise Preview3DLiveUnavailable(
                "GL-Frame enthält keine nachweisbar gerenderte Geometrie"
            )
        return elapsed

    def frame(self) -> float:  # pragma: no cover - hardwaregebunden
        return self._draw()

    def peak_mb(self) -> float:  # pragma: no cover - hardwaregebunden
        # Peak-GPU-Speicher ist über GL 2.1 nicht portabel abfragbar. Als
        # reproduzierbare Untergrenze melden wir alle VBO/IBO-Payloads plus
        # Color- und Depth/Stencil-Attachment des 512²-Framebuffers.
        framebuffer_bytes = 512 * 512 * 8
        return round((self._buffer_bytes + framebuffer_bytes) / (1024.0 * 1024.0), 3)

    def close(self) -> None:  # pragma: no cover - hardwaregebunden
        if not self._built:
            return
        try:
            self._ctx.makeCurrent(self._surface)
            for buffer in (self._pos, self._slope, self._idx):
                if buffer is not None:
                    buffer.destroy()
            if self._vao is not None:
                self._vao.destroy()
            self._fbo = None
            self._program = None
        finally:
            self._ctx.doneCurrent()
            self._built = False


def run_benchmark(
    iterations: int,
    width: int,
    height: int,
    height_sizes: dict[str, tuple[int, int, int]] | None = None,
    *,
    include_formats: bool = True,
) -> dict[str, Any]:
    """Eine isolierte Benchmark-Suite ausführen und als Ergebnis zurückgeben."""
    if not include_formats and not height_sizes:
        raise ValueError("Mindestens eine Benchmark-Suite muss aktiviert sein")

    suite = "combined" if include_formats and height_sizes else (
        "formats" if include_formats else "height"
    )
    formats: dict[str, dict[str, float]] = {}
    samples: dict[str, dict[str, list[float]]] = {}
    with tempfile.TemporaryDirectory(prefix="bgremover-bench-") as td:
        work_dir = Path(td)
        if include_formats:
            img = make_sample_image(width, height)
            for fmt, suffix in BENCH_FORMATS.items():
                metrics, raw = _benchmark_format_with_samples(
                    img, fmt, suffix, iterations, work_dir,
                )
                formats[fmt] = metrics
                samples[fmt] = raw
        for name, (h_width, h_height, h_iters) in (height_sizes or {}).items():
            formats[name] = benchmark_height_pipeline(
                h_width, h_height, h_iters, work_dir)
    return {
        "schema": SCHEMA_VERSION,
        "suite": suite,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "iterations": iterations,
        "image": {"width": width, "height": height},
        "environment": collect_environment(),
        "formats": formats,
        "samples": samples,
        "repeats": 1,
    }


def _run_snapshot(result: dict[str, Any]) -> dict[str, Any]:
    """Diagnostisch relevante Einzelwerte eines vollständigen Laufs kopieren."""
    keys = ("timestamp", "git_commit", "environment", "formats", "samples")
    return {key: result.get(key) for key in keys}


def aggregate_results(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Fasst mehrere vollständige Läufe zum Median je Format/Metrik zusammen.

    Grundlage des Bestätigungslaufs (#277/#278/#279): erst der Median über
    mehrere komplette Wiederholungen entscheidet, ob eine Auffälligkeit echt ist
    oder ein einzelner Mess-Ausreißer war. Metadaten (Commit, Umgebung,
    Iterationen, Bildmaße) werden vom letzten Lauf übernommen; ``repeats`` hält
    die Anzahl der Wiederholungen fest.
    """
    if not runs:
        raise ValueError("aggregate_results braucht mindestens einen Lauf")
    all_formats = sorted({fmt for r in runs for fmt in r.get("formats", {})})
    merged_formats: dict[str, dict[str, float]] = {}
    for fmt in all_formats:
        metric_names = sorted(
            {m for r in runs for m in r.get("formats", {}).get(fmt, {})}
        )
        merged_formats[fmt] = {}
        for metric in metric_names:
            values = [
                float(r["formats"][fmt][metric])
                for r in runs
                if metric in r.get("formats", {}).get(fmt, {})
            ]
            merged_formats[fmt][metric] = (
                round(statistics.median(values), 4) if values else float("nan")
            )
    merged = dict(runs[-1])
    merged["formats"] = merged_formats
    merged["repeats"] = len(runs)
    merged["runs"] = [_run_snapshot(run) for run in runs]
    return merged


# ── Persistenz ───────────────────────────────────────────────────────────

def save_result(result: dict[str, Any], results_dir: Path) -> Path:
    """Schreibt ``result`` als datiertes JSON; bei Kollision mit Zeit-Suffix."""
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = results_dir / f"{stamp}.json"
    if path.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
        path = results_dir / f"{stamp}.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return path


def _rel(path: Path) -> str:
    """Pfad relativ zum Repo-Root, sonst der Pfad selbst (z. B. Temp-Dir im Test)."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _result_files(results_dir: Path) -> list[Path]:
    """Alle Ergebnis-JSONs, nach Dateinamen (≈ chronologisch) sortiert."""
    if not results_dir.is_dir():
        return []
    return sorted(p for p in results_dir.glob("*.json") if p.is_file())


def load_baseline(results_dir: Path, exclude: Path | None) -> tuple[Path, dict[str, Any]] | None:
    """Jüngste Ergebnis-Datei vor ``exclude`` laden (die „Vorwoche")."""
    candidates = [p for p in _result_files(results_dir) if p != exclude]
    if not candidates:
        return None
    latest = candidates[-1]
    return latest, json.loads(latest.read_text(encoding="utf-8"))


# ── Vergleich (reine Logik, deterministisch testbar) ─────────────────────

@dataclass(frozen=True)
class FormatDelta:
    """Vergleich eines Formats zwischen Baseline und aktuellem Lauf."""

    fmt: str
    baseline_ms: float
    current_ms: float
    pct_change: float  # positiv = langsamer geworden (Regression)
    degraded: bool


@dataclass
class Comparison:
    """Gesamtergebnis eines Vergleichs zweier Benchmark-Läufe."""

    metric: str
    threshold: float
    timing_basis: str = "direct"
    deltas: list[FormatDelta] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)

    @property
    def flagged(self) -> list[FormatDelta]:
        return [d for d in self.deltas if d.degraded]


def pct_change(baseline_ms: float, current_ms: float) -> float:
    """Prozentuale Änderung von Baseline → aktuell (positiv = langsamer).

    Eine Baseline von 0 (oder negativ) ist nicht sinnvoll vergleichbar; in dem
    Fall liefert die Funktion 0.0, damit kein irreführender Riesenwert oder eine
    Division durch null entsteht.
    """
    if baseline_ms <= 0 or math.isnan(baseline_ms) or math.isnan(current_ms):
        return 0.0
    return (current_ms - baseline_ms) / baseline_ms * 100.0


def compare(
    baseline: dict[str, Any],
    current: dict[str, Any],
    metric: str = DEFAULT_METRIC,
    threshold: float = DEFAULT_THRESHOLD,
) -> Comparison:
    """Vergleicht zwei Ergebnis-Dicts formatweise anhand von ``metric``."""
    base_fmts = baseline.get("formats", {})
    cur_fmts = current.get("formats", {})
    result = Comparison(metric=metric, threshold=threshold)

    for fmt in sorted(set(base_fmts) & set(cur_fmts)):
        b = float(base_fmts[fmt].get(metric, float("nan")))
        c = float(cur_fmts[fmt].get(metric, float("nan")))
        change = pct_change(b, c)
        result.deltas.append(
            FormatDelta(
                fmt=fmt,
                baseline_ms=b,
                current_ms=c,
                pct_change=change,
                degraded=change > threshold,
            )
        )
    result.added = sorted(set(cur_fmts) - set(base_fmts))
    result.removed = sorted(set(base_fmts) - set(cur_fmts))
    return result


def format_report(comp: Comparison) -> str:
    """Menschlich lesbarer Tabellen-Report eines Vergleichs."""
    paired = comp.timing_basis == "paired-log-ratio"
    baseline_heading = "Referenz*" if paired else "Vorwoche"
    current_heading = "Äquivalent*" if paired else "Diese Woche"
    lines = [
        f"Metrik: {comp.metric}   Schwelle: +{comp.threshold:.1f}%",
        "",
        f"{'Format':<8} {baseline_heading:>12} {current_heading:>14} "
        f"{'Änderung':>11}  Status",
        f"{'-' * 8} {'-' * 12} {'-' * 14} {'-' * 11}  {'-' * 8}",
    ]
    for d in comp.deltas:
        status = "DEGRADIERT" if d.degraded else "ok"
        lines.append(
            f"{d.fmt:<8} {d.baseline_ms:>10.2f}ms {d.current_ms:>12.2f}ms "
            f"{d.pct_change:>+10.1f}%  {status}"
        )
    if comp.added:
        lines.append(f"\nNeu (keine Vorwochen-Daten): {', '.join(comp.added)}")
    if comp.removed:
        lines.append(f"Entfallen (fehlen diese Woche): {', '.join(comp.removed)}")
    if paired:
        lines.append(
            "\n* Paar-normalisierte Darstellung: Referenz = Median der Baseline-"
            "Zeiten; Äquivalent = Referenz × aggregiertes Zeitverhältnis."
        )

    lines.append("")
    if comp.flagged:
        lines.append(f"⚠️  {len(comp.flagged)} Format(e) über der {comp.threshold:.0f}%-Schwelle:")
        for d in comp.flagged:
            lines.append(
                f"  - {d.fmt}: {baseline_heading} {d.baseline_ms:.2f}ms → "
                f"{current_heading} {d.current_ms:.2f}ms "
                f"(+{d.pct_change:.1f}%)"
            )
    else:
        lines.append("✅ Alle Formate innerhalb von "
                     f"{comp.threshold:.0f}% der Vorwoche – Benchmarks stabil.")
    return "\n".join(lines)


# ── Kompatibilität von Baseline & aktuellem Lauf ─────────────────────────

# Softwareversionen: Abweichung macht den Vergleich *hart* unmöglich (andere
# Encoder-/Laufzeit-Implementierung). Python wird nur auf Minor verglichen, damit
# ein reiner Patch-Bump die Baseline nicht unnötig verwirft.
_VERSION_KEYS = (("pillow", "Pillow"), ("numpy", "NumPy"))
# Runner-/Hardware-Abweichungen sind hart: Wiederholungen auf der neuen Maschine
# können einen Vergleich gegen die alte Maschine nicht nachträglich legitimieren
# (#630). Dafür gibt es den gepaarten A/B-Lauf auf demselben Runner.
_EXECUTION_KEYS = (
    ("system", "Betriebssystem"),
    ("release", "Kernel/OS-Release"),
    ("machine", "Architektur"),
    ("cpu_model", "CPU-Modell"),
    ("cpu_count", "CPU-Anzahl"),
    ("runner_arch", "Runner-Architektur"),
    ("runner_environment", "Runner-Umgebung"),
    ("runner_image_os", "Runner-Image-OS"),
    ("runner_image_version", "Runner-Image-Version"),
)


@dataclass
class Compatibility:
    """Ob Baseline und aktueller Lauf automatisch vergleichbar sind.

    ``comparable`` = False bedeutet „nur Anzeige, keine automatische Regressions-
    meldung". ``requires_confirmation`` bleibt für Ausgabe-/Issue-Kompatibilität
    erhalten; Schema 3 akzeptiert jedoch nur identische Ausführungsumgebungen.
    """

    comparable: bool
    requires_confirmation: bool
    reasons: list[str] = field(default_factory=list)


def _python_minor(version: str | None) -> str | None:
    """``"3.12.4"`` → ``"3.12"``; gibt sonst die Eingabe unverändert zurück."""
    if not version:
        return None
    parts = version.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else version


def check_compatibility(baseline: dict[str, Any], current: dict[str, Any]) -> Compatibility:
    """Prüft, ob ``baseline`` und ``current`` automatisch vergleichbar sind.

    Schema, Suite, Benchmark-Parameter, Software und Ausführungsumgebung müssen
    übereinstimmen. Ein Bestätigungslauf auf einer anderen Maschine kann eine
    abweichende Baseline nicht vergleichbar machen; dafür dient ``paired-compare``.
    """
    base_env = baseline.get("environment") or {}
    cur_env = current.get("environment") or {}
    if not base_env:
        return Compatibility(False, False, [
            "Baseline ohne Umgebungs-Fingerprint – nur Anzeige, keine "
            "automatische Regressionserkennung.",
        ])

    hard: list[str] = []
    if baseline.get("schema") != current.get("schema"):
        hard.append(
            f"Ergebnisschema unterschiedlich ({baseline.get('schema')} vs. "
            f"{current.get('schema')})."
        )
    if baseline.get("suite") != current.get("suite"):
        hard.append(
            f"Benchmark-Suite unterschiedlich ({baseline.get('suite')} vs. "
            f"{current.get('suite')})."
        )
    if baseline.get("iterations") != current.get("iterations"):
        hard.append(
            f"Iterationszahl unterschiedlich ({baseline.get('iterations')} vs. "
            f"{current.get('iterations')})."
        )
    if baseline.get("image") != current.get("image"):
        hard.append(
            f"Bildabmessungen unterschiedlich ({baseline.get('image')} vs. "
            f"{current.get('image')})."
        )
    if _python_minor(base_env.get("python")) != _python_minor(cur_env.get("python")):
        hard.append(
            f"Python-Version unterschiedlich ({base_env.get('python')} vs. "
            f"{cur_env.get('python')})."
        )
    for key, label in _VERSION_KEYS:
        if base_env.get(key) != cur_env.get(key):
            hard.append(
                f"{label}-Version unterschiedlich ({base_env.get(key)} vs. "
                f"{cur_env.get(key)})."
            )
    for key, label in _EXECUTION_KEYS:
        if base_env.get(key) != cur_env.get(key):
            hard.append(
                f"{label} unterschiedlich ({base_env.get(key)} vs. {cur_env.get(key)})."
            )
    if hard:
        return Compatibility(False, False, hard)
    return Compatibility(True, False, [])


def format_compatibility(compat: Compatibility, base_label: str) -> str:
    """Kurzer Status-Block zur Vergleichbarkeit (vor dem eigentlichen Report)."""
    if not compat.comparable:
        status = "NICHT VERGLEICHBAR – keine automatische Regressionsmeldung."
    elif compat.requires_confirmation:
        status = "bedingt vergleichbar – Bestätigungslauf erforderlich."
    else:
        status = "vergleichbar."
    lines = [f"Baseline: {base_label}", f"Vergleichbarkeit: {status}"]
    lines.extend(f"  • {reason}" for reason in compat.reasons)
    return "\n".join(lines)


# ── GitHub-Issues für geflaggte Formate ──────────────────────────────────

def _issue_marker(fmt: str, metric: str) -> str:
    """Stabiler Dedupe-Marker, damit kein Format doppelt gemeldet wird."""
    return f"bgremover-benchmark-regression:{metric}:{fmt}"


@dataclass
class IssueContext:
    """Bestätigungs- und Umgebungsdaten für den Issue-Text (#277/#278/#279)."""

    baseline_label: str
    current_commit: str | None
    environment: dict[str, Any]
    confirm_runs: int
    requires_confirmation: bool


def _format_env(env: dict[str, Any]) -> str:
    """Kompakte, einzeilige Darstellung des Umgebungs-Fingerprints."""
    if not env:
        return "—"
    keys = (
        "python", "pillow", "numpy", "system", "release", "machine",
        "cpu_model", "cpu_count", "runner_arch", "runner_image_os",
        "runner_image_version", "runner",
    )
    parts = [f"{k}={env.get(k)}" for k in keys if env.get(k) is not None]
    return ", ".join(parts) if parts else "—"


def _issue_body(d: FormatDelta, comp: Comparison, context: IssueContext | None = None) -> str:
    extra = ""
    if context is not None:
        extra = f"""
### Bestätigung & Umgebung

- Baseline: {context.baseline_label}
- Aktueller Commit: {context.current_commit or "unbekannt"}
- Umgebungs-Fingerprint: {_format_env(context.environment)}
- Bestätigungsläufe: {context.confirm_runs} (gemeldet wird der Median)
- Ausführungsumgebung weicht von der Baseline ab: {"ja" if context.requires_confirmation else "nein"}
"""
    paired = comp.timing_basis == "paired-log-ratio"
    baseline_heading = "Referenz (Baseline-Median)" if paired else "Vorwoche"
    current_heading = "Äquivalent (paar-normalisiert)" if paired else "Diese Woche"
    timing_note = (
        "\nDie angezeigte Äquivalentzeit wird aus dem Baseline-Median und dem "
        "Median der paarweisen Log-Verhältnisse abgeleitet.\n"
        if paired else ""
    )
    return f"""<!-- {_issue_marker(d.fmt, comp.metric)} -->
## Performance-Regression: {d.fmt}

Die Verarbeitungszeit (`{comp.metric}`) für **{d.fmt}** hat sich gegenüber dem
vorigen Benchmark-Lauf um mehr als {comp.threshold:.0f}% verschlechtert.

| | Zeit |
|---|---|
| {baseline_heading} | {d.baseline_ms:.2f} ms |
| {current_heading} | {d.current_ms:.2f} ms |
| Änderung | +{d.pct_change:.1f}% |
{timing_note}
{extra}
Erzeugt von `scripts/benchmark.py`.
"""


def _github_request(
    method: str, path: str, token: str, *, api_url: str, payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = api_url.rstrip("/") + path
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {path}: {exc.code} {detail}") from exc
    return json.loads(content) if content else {}


def _issue_exists(repo: str, marker: str, token: str, api_url: str) -> str | None:
    query = f'repo:{repo} is:issue is:open in:body "{marker}"'
    encoded = urllib.parse.urlencode({"q": query, "per_page": "1"})
    result = _github_request("GET", f"/search/issues?{encoded}", token, api_url=api_url)
    items = result.get("items") or []
    return str(items[0].get("html_url") or "") if items else None


def post_issues(
    comp: Comparison, *, dry_run: bool, context: IssueContext | None = None,
) -> list[dict[str, str]]:
    """Legt für jedes geflaggte Format ein GitHub-Issue an (idempotent).

    Ohne ``GITHUB_TOKEN``/``GITHUB_REPOSITORY`` (oder mit ``--dry-run``) wird nur
    gedruckt, was passieren würde – derselbe Schutz wie in
    ``create_security_scan_issues.py``. ``context`` ergänzt im Issue-Text
    Baseline, Commit, Umgebungs-Fingerprint und das Bestätigungsergebnis.
    """
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    api_url = os.environ.get("GITHUB_API_URL", DEFAULT_API_URL)
    results: list[dict[str, str]] = []

    for d in comp.flagged:
        marker = _issue_marker(d.fmt, comp.metric)
        title = f"Performance-Regression: {d.fmt} (+{d.pct_change:.1f}%)"
        if dry_run or not repo or not token:
            print(f"[dry-run] Würde Issue anlegen: {title}")
            results.append({"format": d.fmt, "status": "dry-run", "url": ""})
            continue
        existing = _issue_exists(repo, marker, token, api_url)
        if existing:
            print(f"Bestehendes Issue für {d.fmt}: {existing}")
            results.append({"format": d.fmt, "status": "existing", "url": existing})
            continue
        payload = {"title": title, "body": _issue_body(d, comp, context)}
        created = _github_request(
            "POST", f"/repos/{repo}/issues", token, api_url=api_url, payload=payload,
        )
        url = str(created.get("html_url") or "")
        print(f"Issue für {d.fmt} angelegt: {url}")
        results.append({"format": d.fmt, "status": "created", "url": url})
    return results


def _load_results(paths: list[Path]) -> list[dict[str, Any]]:
    """Ergebnisdateien in der übergebenen Paar-Reihenfolge laden."""
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def _paired_compatibility(
    baseline_runs: list[dict[str, Any]], current_runs: list[dict[str, Any]],
) -> Compatibility:
    """Umgebung und Commit-Kohorten aller A/B-Paare validieren."""
    if len(baseline_runs) != len(current_runs):
        return Compatibility(False, False, [
            "Anzahl der Baseline- und aktuellen Läufe unterscheidet sich "
            f"({len(baseline_runs)} vs. {len(current_runs)}).",
        ])

    reasons: list[str] = []
    for label, runs in (("Baseline", baseline_runs), ("Aktuell", current_runs)):
        commits = [run.get("git_commit") for run in runs]
        missing = [index for index, commit in enumerate(commits, start=1) if not commit]
        if missing:
            reasons.append(
                f"{label}-Kohorte ohne Commit-Hash in Lauf/Läufen "
                f"{', '.join(str(index) for index in missing)}."
            )
        distinct = {str(commit) for commit in commits if commit}
        if len(distinct) > 1:
            reasons.append(
                f"{label}-Kohorte enthält mehrere Commits: "
                f"{', '.join(sorted(distinct))}."
            )

    for index, (baseline, current) in enumerate(
        zip(baseline_runs, current_runs, strict=True), start=1,
    ):
        compatibility = check_compatibility(baseline, current)
        if not compatibility.comparable:
            reasons.extend(
                f"Paar {index}: {reason}" for reason in compatibility.reasons
            )
    for label, runs in (("Baseline", baseline_runs), ("Aktuell", current_runs)):
        for index, run in enumerate(runs[1:], start=2):
            compatibility = check_compatibility(runs[0], run)
            if not compatibility.comparable:
                reasons.extend(
                    f"{label}-Lauf {index}: {reason}"
                    for reason in compatibility.reasons
                )
    if reasons:
        return Compatibility(False, False, reasons)
    return Compatibility(True, False, [])


def compare_paired(
    baseline_runs: list[dict[str, Any]],
    current_runs: list[dict[str, Any]],
    metric: str = DEFAULT_METRIC,
    threshold: float = DEFAULT_THRESHOLD,
) -> tuple[Comparison, list[Comparison]]:
    """A/B-Paare einzeln vergleichen und deren Zeitverhältnisse aggregieren.

    Absolute Runner-Geschwindigkeit kann zwischen Paaren driften. Deshalb wird
    das logarithmische Current/Baseline-Verhältnis zuerst innerhalb jedes Paars
    berechnet. Der Median der Log-Verhältnisse ist richtungssymmetrisch: Reziproke
    Reihenfolgeeffekte heben sich auf. Für den Report wird die aktuelle
    Äquivalentzeit konsistent aus Baseline-Median und aggregiertem Verhältnis
    abgeleitet; die beobachteten Einzelwerte bleiben in ``pair_comparisons``.
    """
    if not baseline_runs or len(baseline_runs) != len(current_runs):
        raise ValueError("compare_paired braucht gleich viele, nicht leere Kohorten")

    pair_comparisons = [
        compare(baseline, current, metric, threshold)
        for baseline, current in zip(baseline_runs, current_runs, strict=True)
    ]
    delta_maps = [
        {delta.fmt: delta for delta in comparison.deltas}
        for comparison in pair_comparisons
    ]
    common_formats = set(delta_maps[0])
    for delta_map in delta_maps[1:]:
        common_formats &= set(delta_map)

    result = Comparison(
        metric=metric, threshold=threshold, timing_basis="paired-log-ratio",
    )
    for fmt in sorted(common_formats):
        deltas = [delta_map[fmt] for delta_map in delta_maps]
        log_ratios = [
            math.log(delta.current_ms / delta.baseline_ms)
            for delta in deltas
            if (
                math.isfinite(delta.baseline_ms)
                and math.isfinite(delta.current_ms)
                and delta.baseline_ms > 0.0
                and delta.current_ms > 0.0
            )
        ]
        if len(log_ratios) != len(deltas):
            raise ValueError(
                f"{fmt}/{metric}: Log-Verhältnis braucht positive, endliche Zeiten"
            )
        aggregate_ratio = math.exp(statistics.median(log_ratios))
        change = round((aggregate_ratio - 1.0) * 100.0, 4)
        representative_baseline = round(
            statistics.median(delta.baseline_ms for delta in deltas), 4,
        )
        result.deltas.append(
            FormatDelta(
                fmt=fmt,
                baseline_ms=representative_baseline,
                current_ms=round(representative_baseline * aggregate_ratio, 4),
                pct_change=change,
                degraded=change > threshold,
            )
        )
    result.added = sorted(
        {fmt for comparison in pair_comparisons for fmt in comparison.added}
    )
    result.removed = sorted(
        {fmt for comparison in pair_comparisons for fmt in comparison.removed}
    )
    return result, pair_comparisons


def _comparison_payload(comp: Comparison) -> dict[str, Any]:
    """Vergleich für das A/B-Artefakt JSON-serialisierbar machen."""
    return {
        "metric": comp.metric,
        "threshold": comp.threshold,
        "timing_basis": comp.timing_basis,
        "deltas": [
            {
                "format": delta.fmt,
                "baseline_ms": delta.baseline_ms,
                "current_ms": delta.current_ms,
                "pct_change": delta.pct_change,
                "degraded": delta.degraded,
            }
            for delta in comp.deltas
        ],
        "added": comp.added,
        "removed": comp.removed,
    }


def _cmd_paired_compare(args: argparse.Namespace) -> int:
    """Mehrere auf demselben Runner gemessene A/B-Paare vergleichen."""
    baseline_runs = _load_results(args.baseline)
    current_runs = _load_results(args.current)
    if len(baseline_runs) < args.minimum_pairs:
        print(
            f"Mindestens {args.minimum_pairs} A/B-Paare nötig; erhalten: "
            f"{len(baseline_runs)}.",
        )
        return 2
    if len(baseline_runs) % 2 != 0:
        print(
            "Eine gerade Anzahl A/B-Paare ist nötig, damit Baseline und aktueller "
            "Commit gleich oft zuerst laufen."
        )
        return 2

    compatibility = _paired_compatibility(baseline_runs, current_runs)
    print(format_compatibility(compatibility, "gepaarte Baseline"))
    if not compatibility.comparable:
        return 2

    baseline = aggregate_results(baseline_runs)
    current = aggregate_results(current_runs)
    comp, pair_comparisons = compare_paired(
        baseline_runs, current_runs, args.metric, args.threshold,
    )
    print()
    print(f"Gepaarter A/B-Vergleich ({len(baseline_runs)} Paare):")
    print("Entscheidungsbasis: Median der paarweisen Log-Zeitverhältnisse.")
    print(format_report(comp))

    comparison_payload = _comparison_payload(comp)
    comparison_payload["aggregation"] = "median-of-pair-log-ratios"
    comparison_payload["pair_comparisons"] = [
        {"pair": index, **_comparison_payload(pair_comp)}
        for index, pair_comp in enumerate(pair_comparisons, start=1)
    ]

    payload = {
        "schema": SCHEMA_VERSION,
        "kind": "paired-comparison",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pairs": len(baseline_runs),
        "baseline": baseline,
        "current": current,
        "comparison": comparison_payload,
    }
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"A/B-Nachweis gespeichert: {_rel(args.output)}")

    context = IssueContext(
        baseline_label=str(baseline.get("git_commit") or "gepaarte Baseline"),
        current_commit=current.get("git_commit"),
        environment=current.get("environment", {}),
        confirm_runs=len(current_runs),
        requires_confirmation=False,
    )
    if comp.flagged and (args.post_issues or args.dry_run_issues):
        print()
        post_issues(
            comp, dry_run=args.dry_run_issues or not args.post_issues,
            context=context,
        )
    return 1 if (comp.flagged and args.fail_on_regression) else 0


# ── CLI ──────────────────────────────────────────────────────────────────

def _cmd_run_preview3d_live(args: argparse.Namespace) -> int:
    """preview3d-live-Suite: GPU-gebundene Metriken auf echter Hardware (#645).

    Verweigert ohne Hardware-GL-Kontext; ``--require-gl`` macht das zum Fehler
    (Abnahme), sonst ein freundlicher Skip ohne gespeichertes Ergebnis.
    """
    # QOffscreenSurface setzt eine QGuiApplication voraus. Im normalen App-
    # Prozess existiert sie bereits; der eigenständige Benchmark legt genau
    # eine Instanz an und hält sie für alle Szenarien am Leben.
    from PyQt6.QtGui import QGuiApplication

    gui_app = QGuiApplication.instance()
    if gui_app is None:
        gui_app = QGuiApplication(["bgremover-preview3d-live"])

    available, diagnostic = probe_live_gl()
    if not available:
        reason = f"Kein Hardware-GL-Kontext (Diagnose: {diagnostic or 'kein GL'})."
        print(f"preview3d-live übersprungen: {reason}")
        return 2 if args.require_gl else 0

    formats: dict[str, dict[str, float]] = {}
    for name, (w, h) in PREVIEW3D_LIVE_SIZES.items():
        formats[name] = benchmark_preview3d_live(w, h)
    environment = collect_environment()
    environment["gl_provenance"] = diagnostic
    result = {
        "schema": SCHEMA_VERSION,
        "suite": "preview3d-live",
        "platform": getattr(args, "platform", None) or "unbekannt",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "iterations": 1,
        "image": {"width": args.width, "height": args.height},
        "environment": environment,
        "formats": formats,
        "samples": {},
        "repeats": 1,
    }
    results_dir = args.results_dir or RESULTS_DIR / args.suite
    path = save_result(result, results_dir)
    print(f"Ergebnis gespeichert: {_rel(path)}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    if args.suite == "preview3d-live":
        return _cmd_run_preview3d_live(args)
    # Format- und HEIGHT/3D-Suite laufen bewusst in getrennten Prozessen. Die
    # großen HEIGHT-Läufe dürfen die Bestätigungswerte des CPU-lastigen PNG-
    # Encoders nicht durch Wärme-, Speicher- oder Scheduler-Effekte verzerren.
    height_sizes = HEIGHT_BENCH_SIZES if args.suite == "height" else None
    include_formats = args.suite == "formats"
    results_dir = args.results_dir or RESULTS_DIR / args.suite
    result = run_benchmark(
        args.iterations, args.width, args.height,
        height_sizes=height_sizes, include_formats=include_formats,
    )
    path = save_result(result, results_dir)
    print(f"Ergebnis gespeichert: {_rel(path)}")

    if args.no_compare:
        return 0
    baseline = load_baseline(results_dir, exclude=path)
    if baseline is None:
        print("Kein früherer Lauf gefunden – dieser Lauf ist die neue Baseline.")
        return 0
    base_path, base_data = baseline
    base_label = base_path.name
    print(f"Vergleiche gegen Vorwoche: {_rel(base_path)}\n")

    compat = check_compatibility(base_data, result)
    print(format_compatibility(compat, base_label))
    print()
    comp = compare(base_data, result, args.metric, args.threshold)
    print(format_report(comp))

    # Inkompatible Baseline: nur anzeigen, niemals melden (#277/#278/#279).
    if not compat.comparable:
        print("\nℹ️  Baseline nicht vergleichbar – keine Regression gemeldet.")
        return 0
    if not comp.flagged:
        return 0

    # Bestätigungslauf: mehrere vollständige Wiederholungen, Median vergleichen.
    # Der zuerst gespeicherte Lauf fließt mit in den Median ein – so beruht die
    # Bestätigung auf allen Messungen, nicht nur auf den Nachläufen.
    repeats = max(2, args.confirm_runs)
    print(f"\n🔁 {len(comp.flagged)} Format(e) auffällig – Bestätigung mit "
          f"insgesamt {repeats} Lauf/Läufen …\n")
    confirmed = aggregate_results(
        [result, *(run_benchmark(args.iterations, args.width, args.height,
                                  height_sizes=height_sizes,
                                  include_formats=include_formats)
                   for _ in range(repeats - 1))]
    )
    # Persistierte Baseline durch den robusten Median ersetzen. Sonst committet
    # der CI-Workflow den (womöglich Ausreißer-)Erstlauf, und der nächste
    # Wochenlauf vergliche gegen eine bekannte Fehlmessung.
    path.write_text(json.dumps(confirmed, indent=2) + "\n", encoding="utf-8")
    print(f"Baseline mit bestätigtem Median ({confirmed['repeats']} Läufe) "
          f"überschrieben: {_rel(path)}\n")
    confirmed_comp = compare(base_data, confirmed, args.metric, args.threshold)
    print("Bestätigungslauf (Median):")
    print(format_report(confirmed_comp))

    if not confirmed_comp.flagged:
        print("\n✅ Bestätigungslauf zeigt keine Regression – Auffälligkeit war ein "
              "Mess-Ausreißer; kein Issue.")
        return 0

    context = IssueContext(
        baseline_label=base_label,
        current_commit=result.get("git_commit"),
        environment=result.get("environment", {}),
        confirm_runs=repeats,
        requires_confirmation=compat.requires_confirmation,
    )
    if args.post_issues or args.dry_run_issues:
        print()
        post_issues(
            confirmed_comp,
            dry_run=args.dry_run_issues or not args.post_issues,
            context=context,
        )
    return 1 if args.fail_on_regression else 0


def _cmd_compare(args: argparse.Namespace) -> int:
    if args.baseline and args.current:
        base_data = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        cur_data = json.loads(Path(args.current).read_text(encoding="utf-8"))
        base_label = Path(args.baseline).name
    else:
        results_dir = args.results_dir or RESULTS_DIR / args.suite
        files = _result_files(results_dir)
        if len(files) < 2:
            print("Mindestens zwei Ergebnis-Dateien nötig für einen Vergleich.")
            return 2
        base_data = json.loads(files[-2].read_text(encoding="utf-8"))
        cur_data = json.loads(files[-1].read_text(encoding="utf-8"))
        base_label = files[-2].name
        print(f"Vergleiche {files[-2].name} → {files[-1].name}\n")

    compat = check_compatibility(base_data, cur_data)
    print(format_compatibility(compat, base_label))
    print()
    comp = compare(base_data, cur_data, args.metric, args.threshold)
    print(format_report(comp))

    # ``compare`` vergleicht statische Dateien und kann nicht nachmessen; eine
    # bestätigte Meldung entsteht nur über ``run``. Bei inkompatibler Baseline
    # wird hier deshalb ebenfalls nichts gemeldet.
    if not compat.comparable:
        print("\nℹ️  Baseline nicht vergleichbar – keine Regression gemeldet.")
        return 0
    if comp.flagged and (args.post_issues or args.dry_run_issues):
        context = IssueContext(
            baseline_label=base_label,
            current_commit=cur_data.get("git_commit"),
            environment=cur_data.get("environment", {}),
            confirm_runs=cur_data.get("repeats", 0),
            requires_confirmation=compat.requires_confirmation,
        )
        print()
        post_issues(
            comp, dry_run=args.dry_run_issues or not args.post_issues, context=context,
        )
    return 1 if (comp.flagged and args.fail_on_regression) else 0


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--results-dir", type=Path,
        help="Ergebnisverzeichnis (Default: benchmarks/results/<suite>).",
    )
    parser.add_argument("--metric", default=DEFAULT_METRIC,
                        help="Vergleichsmetrik (process_ms|encode_ms|decode_ms).")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help="Regressions-Schwelle in Prozent (Default 10).")
    parser.add_argument("--fail-on-regression", action="store_true",
                        help="Exit-Code 1, wenn ein Format degradiert ist.")
    parser.add_argument("--post-issues", action="store_true",
                        help="GitHub-Issues für geflaggte Formate anlegen.")
    parser.add_argument("--dry-run-issues", action="store_true",
                        help="Issue-Anlage nur simulieren (nichts senden).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Benchmark ausführen und vergleichen.")
    run_p.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    run_p.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    run_p.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    run_p.add_argument("--no-compare", action="store_true",
                       help="Nur messen und speichern, nicht vergleichen.")
    suite_group = run_p.add_mutually_exclusive_group()
    suite_group.add_argument(
        "--suite", choices=("formats", "height", "preview3d-live"), default="formats",
        help="Isolierte Benchmark-Suite (Default: formats).",
    )
    run_p.add_argument(
        "--require-gl", action="store_true",
        help="preview3d-live: fehlender Hardware-GL-Kontext ist ein Fehler "
             "(Abnahme-Modus) statt eines freundlichen Skips.",
    )
    run_p.add_argument(
        "--platform", choices=("macos-arm64", "linux-arm64", "linux-x86_64"),
        help="Evidenz-Plattform für preview3d-live (Abnahme-Workflow).",
    )
    # Rückwärtskompatible, nicht mehr beworbene Aliase. Anders als früher
    # koppelt --height-bench die Formatmessung nicht mehr an die HEIGHT-Suite.
    suite_group.add_argument(
        "--height-bench", dest="suite", action="store_const", const="height",
        help=argparse.SUPPRESS,
    )
    suite_group.add_argument(
        "--no-height-bench", dest="suite", action="store_const", const="formats",
        help=argparse.SUPPRESS,
    )
    run_p.add_argument("--confirm-runs", type=int, default=DEFAULT_CONFIRM_RUNS,
                       help="Gesamtzahl der Läufe zur Bestätigung einer "
                            "Auffälligkeit (Median; Default 3).")
    _add_common(run_p)
    run_p.set_defaults(func=_cmd_run)

    cmp_p = sub.add_parser("compare", help="Zwei Ergebnis-Dateien vergleichen.")
    cmp_p.add_argument("--baseline", type=Path, help="Baseline-JSON (Vorwoche).")
    cmp_p.add_argument("--current", type=Path, help="Aktuelles JSON (diese Woche).")
    cmp_p.add_argument("--suite", choices=("formats", "height"), default="formats")
    _add_common(cmp_p)
    cmp_p.set_defaults(func=_cmd_compare)

    paired_p = sub.add_parser(
        "paired-compare",
        help="Mehrere A/B-Läufe von demselben Runner robust vergleichen.",
    )
    paired_p.add_argument(
        "--baseline", type=Path, nargs="+", required=True,
        help="Baseline-JSONs in Paar-Reihenfolge.",
    )
    paired_p.add_argument(
        "--current", type=Path, nargs="+", required=True,
        help="Aktuelle JSONs in Paar-Reihenfolge.",
    )
    paired_p.add_argument(
        "--minimum-pairs", type=int, default=DEFAULT_MINIMUM_PAIRS,
        help="Gerade Mindestzahl ausbalancierter A/B-Paare (Default 4).",
    )
    paired_p.add_argument("--output", type=Path, help="Detailliertes A/B-JSON.")
    paired_p.add_argument("--metric", default=DEFAULT_METRIC)
    paired_p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    paired_p.add_argument("--fail-on-regression", action="store_true")
    paired_p.add_argument("--post-issues", action="store_true")
    paired_p.add_argument("--dry-run-issues", action="store_true")
    paired_p.set_defaults(func=_cmd_paired_compare)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
