#!/usr/bin/env python3
"""Performance-Benchmark für die Bildverarbeitung von BgRemover.

Misst die Verarbeitungszeit **pro Bildformat** (PNG, JPEG, WebP, TIFF) über die
echten Code-Pfade des Pakets (``bgremover.image_ops``): Encode, Decode und eine
repräsentative Verarbeitungs-Pipeline (Laden → Drehen → Ecken runden →
Zuschneiden → Speichern).

Zwei Unterbefehle:

- ``run``     – Benchmark ausführen, Ergebnis als datiertes JSON unter
               ``benchmarks/results/`` ablegen und – falls ein früherer Lauf
               existiert – direkt gegen den jüngsten vergleichen.
- ``compare`` – Zwei vorhandene Ergebnis-Dateien vergleichen (oder das aktuellste
               gegen das vorherige), Regressionen jenseits der Schwelle melden
               und optional GitHub-Issues anlegen.

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
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from bgremover.height_map import (  # noqa: E402
    HeightField,
    image_to_height_field,
)
from bgremover.height_ops import gaussian_blur  # noqa: E402
from bgremover.image_ops import (  # noqa: E402  (Pfad muss vor dem Import stehen)
    crop_image,
    rotate_image,
    round_corners,
    save_image_file,
)
from bgremover.project_io import load_project, save_project  # noqa: E402
from bgremover.project_model import LayerKind, Project  # noqa: E402
from bgremover.relief_preview import compose_over, relief_shading  # noqa: E402

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
DEFAULT_CONFIRM_RUNS = 3  # Wiederholungen, um eine Auffälligkeit zu bestätigen.
RESULTS_DIR = ROOT / "benchmarks" / "results"
# Schema 2 ergänzt den Umgebungs-Fingerprint (``environment``); ältere Läufe ohne
# diesen Block gelten nicht als automatische Baseline (#277/#278/#279).
SCHEMA_VERSION = 2
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

def _median_ms(fn: Callable[[], Any], iterations: int) -> float:
    """Median der Laufzeit von ``fn`` in Millisekunden über ``iterations`` Läufe.

    Der Median ist robuster gegen GC-/Scheduler-Ausreißer als der Mittelwert.
    """
    samples: list[float] = []
    for _ in range(max(1, iterations)):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    return statistics.median(samples)


def benchmark_format(
    img: Image.Image, fmt: str, suffix: str, iterations: int, work_dir: Path,
) -> dict[str, float]:
    """Misst Encode-, Decode- und End-to-End-Verarbeitungszeit für ein Format."""
    target = work_dir / f"bench{suffix}"

    # Encode: einmal über den App-Pfad schreiben (atomar, mit Format-Vorgaben).
    encode_ms = _median_ms(lambda: save_image_file(img, target), iterations)
    encoded_bytes = target.stat().st_size

    # Decode: vollständig in den Speicher laden (load() erzwingt das Dekodieren).
    def _decode() -> None:
        with Image.open(target) as handle:
            handle.load()

    decode_ms = _median_ms(_decode, iterations)

    # End-to-End: Laden → Drehen → Ecken runden → Zuschneiden → Speichern.
    out = work_dir / f"bench_out{suffix}"

    def _process() -> None:
        with Image.open(target) as handle:
            handle.load()
            stage = rotate_image(handle, 90)
        stage, _ = round_corners(stage, 48)
        w, h = stage.size
        stage = crop_image(stage, (0, 0, w * 3 // 4, h * 3 // 4), is_circle=False)
        save_image_file(stage, out)

    process_ms = _median_ms(_process, iterations)

    return {
        "encode_ms": round(encode_ms, 4),
        "decode_ms": round(decode_ms, 4),
        "process_ms": round(process_ms, 4),
        "encoded_bytes": float(encoded_bytes),
    }


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


def collect_environment() -> dict[str, Any]:
    """Umgebungs-Fingerprint des aktuellen Laufs.

    Hält fest, *worauf* gemessen wurde, damit der Vergleich später entscheiden
    kann, ob zwei Läufe überhaupt vergleichbar sind (#277/#278/#279): Software-
    versionen (Python/Pillow/NumPy) als harte Bedingung, Hardware (Architektur/
    CPU-Anzahl) als weiche. ``runner`` dokumentiert den GitHub-Runner, ``system``/
    ``release``/``processor`` sind rein informativ (gehen nicht in den Vergleich
    ein, da sie zwischen sonst gleichen Runnern schwanken können).
    """
    import platform

    try:
        from PIL import __version__ as pillow_version
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
        "cpu_count": os.cpu_count(),
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


def benchmark_height_pipeline(
    width: int, height: int, iterations: int, work_dir: Path
) -> dict[str, float]:
    """Misst die 16-Bit-Höhenpipeline über die echten Code-Pfade (#590).

    Metriken je Größe: ``import_ms`` (natives 16-Bit-PNG → ``HeightField``),
    ``process_ms`` (separabler ``gaussian_blur`` als repräsentative Operation –
    zugleich die Standard-Vergleichsmetrik des Benchmarks), ``roundtrip_ms``
    (``.bgrproj`` Save + Open, Formatversion 2) und ``preview_ms``
    (Relief-Hillshade + Compose aus der kanonischen Payload).
    """
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
    return {
        "import_ms": import_ms,
        "process_ms": process_ms,
        "roundtrip_ms": roundtrip_ms,
        "preview_ms": preview_ms,
    }


def run_benchmark(
    iterations: int,
    width: int,
    height: int,
    height_sizes: dict[str, tuple[int, int, int]] | None = None,
) -> dict[str, Any]:
    """Führt den Benchmark für alle Formate aus und liefert das Ergebnis-Dict."""
    img = make_sample_image(width, height)
    formats: dict[str, dict[str, float]] = {}
    with tempfile.TemporaryDirectory(prefix="bgremover-bench-") as td:
        work_dir = Path(td)
        for fmt, suffix in BENCH_FORMATS.items():
            formats[fmt] = benchmark_format(img, fmt, suffix, iterations, work_dir)
        # Additiv (#590): die Vergleichslogik behandelt neue Einträge wie neue
        # Formate; Unit-Smoke-Läufe rufen ohne ``height_sizes`` auf.
        for name, (h_width, h_height, h_iters) in (height_sizes or {}).items():
            formats[name] = benchmark_height_pipeline(
                h_width, h_height, h_iters, work_dir)
    return {
        "schema": SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "iterations": iterations,
        "image": {"width": width, "height": height},
        "environment": collect_environment(),
        "formats": formats,
    }


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
    lines = [
        f"Metrik: {comp.metric}   Schwelle: +{comp.threshold:.1f}%",
        "",
        f"{'Format':<8} {'Vorwoche':>12} {'Diese Woche':>14} {'Änderung':>11}  Status",
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

    lines.append("")
    if comp.flagged:
        lines.append(f"⚠️  {len(comp.flagged)} Format(e) über der {comp.threshold:.0f}%-Schwelle:")
        for d in comp.flagged:
            lines.append(
                f"  - {d.fmt}: Vorwoche {d.baseline_ms:.2f}ms → "
                f"diese Woche {d.current_ms:.2f}ms (+{d.pct_change:.1f}%)"
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
# Hardware: Abweichung macht den Vergleich *weich* – Messung bleibt möglich,
# verlangt aber einen Bestätigungslauf.
_HARDWARE_KEYS = (("machine", "Architektur"), ("cpu_count", "CPU-Anzahl"))


@dataclass
class Compatibility:
    """Ob Baseline und aktueller Lauf automatisch vergleichbar sind.

    ``comparable`` = False bedeutet „nur Anzeige, keine automatische Regressions-
    meldung". ``requires_confirmation`` = True heißt „vergleichbar, aber die
    Hardware weicht ab – erst ein Bestätigungslauf darf melden". ``reasons``
    erklärt die Entscheidung menschenlesbar (für Report und Issue-Text).
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

    Harte Inkompatibilität (``comparable=False``): fehlender Umgebungs-Fingerprint
    in der Baseline, abweichende Python-Minor-/Pillow-/NumPy-Version oder
    abweichende Benchmark-Parameter (Iterationszahl, Bildabmessungen). Weiche
    Inkompatibilität (``requires_confirmation=True``): nur Hardware (Architektur/
    CPU-Anzahl) weicht ab.
    """
    base_env = baseline.get("environment") or {}
    cur_env = current.get("environment") or {}
    if not base_env:
        return Compatibility(False, False, [
            "Baseline ohne Umgebungs-Fingerprint – nur Anzeige, keine "
            "automatische Regressionserkennung.",
        ])

    hard: list[str] = []
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
    if hard:
        return Compatibility(False, False, hard)

    soft: list[str] = []
    for key, label in _HARDWARE_KEYS:
        if base_env.get(key) != cur_env.get(key):
            soft.append(
                f"{label} unterschiedlich ({base_env.get(key)} vs. {cur_env.get(key)})."
            )
    if soft:
        soft.append("Hardware weicht ab – Bestätigungslauf erforderlich.")
        return Compatibility(True, True, soft)
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
    keys = ("python", "pillow", "numpy", "system", "machine", "cpu_count", "runner")
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
- Hardware weicht von der Baseline ab: {"ja" if context.requires_confirmation else "nein"}
"""
    return f"""<!-- {_issue_marker(d.fmt, comp.metric)} -->
## Performance-Regression: {d.fmt}

Die Verarbeitungszeit (`{comp.metric}`) für **{d.fmt}** hat sich gegenüber dem
vorigen Benchmark-Lauf um mehr als {comp.threshold:.0f}% verschlechtert.

| | Zeit |
|---|---|
| Vorwoche | {d.baseline_ms:.2f} ms |
| Diese Woche | {d.current_ms:.2f} ms |
| Änderung | +{d.pct_change:.1f}% |
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


# ── CLI ──────────────────────────────────────────────────────────────────

def _cmd_run(args: argparse.Namespace) -> int:
    # Die feste Höhenpipeline-Baseline (bis 40 MP) gehört zum vollen, geplanten
    # Lauf mit den Standardmaßen. Ein manueller/Smoke-Lauf mit reduzierter
    # Größe oder Iterationszahl erwartet dagegen eine schnelle, kleine
    # Messung – ohne explizite Erzwingung (``--height-bench``) läuft die
    # 40-MP-Höhenpipeline dort nicht implizit mit (Codex-Review zu #590).
    is_default_run = (
        args.width == DEFAULT_WIDTH
        and args.height == DEFAULT_HEIGHT
        and args.iterations == DEFAULT_ITERATIONS
    )
    include_height_bench = (
        args.height_bench if args.height_bench is not None else is_default_run
    )
    height_sizes = HEIGHT_BENCH_SIZES if include_height_bench else None
    result = run_benchmark(
        args.iterations, args.width, args.height, height_sizes=height_sizes,
    )
    path = save_result(result, args.results_dir)
    print(f"Ergebnis gespeichert: {_rel(path)}")

    if args.no_compare:
        return 0
    baseline = load_baseline(args.results_dir, exclude=path)
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
    repeats = max(1, args.confirm_runs)
    print(f"\n🔁 {len(comp.flagged)} Format(e) auffällig – Bestätigung mit "
          f"{repeats} Wiederholung(en) …\n")
    confirmed = aggregate_results(
        [result, *(run_benchmark(args.iterations, args.width, args.height,
                                  height_sizes=height_sizes)
                   for _ in range(repeats))]
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
        files = _result_files(args.results_dir)
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
    # Reine Hardware-Abweichung verlangt einen Bestätigungslauf – den kann der
    # statische ``compare`` nicht leisten. Sonst entstünden genau die
    # Hardware-Artefakt-Fehlalarme, die der Gate verhindern soll (#277/#278/#279).
    if compat.requires_confirmation:
        print("\nℹ️  Hardware weicht ab – „compare“ kann nicht nachmessen; "
              "keine Regression gemeldet (für den Bestätigungslauf „run“ nutzen).")
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
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
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
    run_p.add_argument(
        "--height-bench", dest="height_bench", action="store_true", default=None,
        help="Höhenpipeline-Baseline (HEIGHT16-1MP/16MP/40MP) unabhängig von "
             "--width/--height/--iterations erzwingen.")
    run_p.add_argument(
        "--no-height-bench", dest="height_bench", action="store_false",
        help="Höhenpipeline-Baseline auslassen (z. B. für schnelle manuelle "
             "Smoke-Läufe mit reduzierter Größe).")
    run_p.add_argument("--confirm-runs", type=int, default=DEFAULT_CONFIRM_RUNS,
                       help="Wiederholungen zur Bestätigung einer Auffälligkeit "
                            "(Median; Default 3).")
    _add_common(run_p)
    run_p.set_defaults(func=_cmd_run)

    cmp_p = sub.add_parser("compare", help="Zwei Ergebnis-Dateien vergleichen.")
    cmp_p.add_argument("--baseline", type=Path, help="Baseline-JSON (Vorwoche).")
    cmp_p.add_argument("--current", type=Path, help="Aktuelles JSON (diese Woche).")
    _add_common(cmp_p)
    cmp_p.set_defaults(func=_cmd_compare)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
