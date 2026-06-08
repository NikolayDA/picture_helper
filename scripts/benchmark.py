#!/usr/bin/env python3
"""Performance-Benchmark für die Bildverarbeitung von BgRemover.

Misst die Verarbeitungszeit **pro Bildformat** (PNG, JPEG, WebP, TIFF) über die
echten Code-Pfade des Pakets (``bgremover.image_ops`` / ``image_utils``): Encode,
Decode und eine repräsentative Verarbeitungs-Pipeline (Laden → Drehen → Ecken
runden → Zuschneiden → Speichern).

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

from bgremover.image_ops import (  # noqa: E402  (Pfad muss vor dem Import stehen)
    crop_image,
    rotate_image,
    round_corners,
    save_image_file,
)

# Format-Label → Default-Suffix. Spiegelt bewusst ``image_ops.SAVE_FORMATS``;
# als getrennte Liste gehalten, damit der Benchmark auch dann eine stabile
# Reihenfolge hat, wenn sich die Dialog-Filter ändern.
BENCH_FORMATS: dict[str, str] = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "WebP": ".webp",
    "TIFF": ".tif",
}

DEFAULT_ITERATIONS = 7
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
DEFAULT_THRESHOLD = 10.0  # Prozent; darüber gilt ein Format als degradiert.
DEFAULT_METRIC = "process_ms"
RESULTS_DIR = ROOT / "benchmarks" / "results"
SCHEMA_VERSION = 1
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


def run_benchmark(iterations: int, width: int, height: int) -> dict[str, Any]:
    """Führt den Benchmark für alle Formate aus und liefert das Ergebnis-Dict."""
    img = make_sample_image(width, height)
    formats: dict[str, dict[str, float]] = {}
    with tempfile.TemporaryDirectory(prefix="bgremover-bench-") as td:
        work_dir = Path(td)
        for fmt, suffix in BENCH_FORMATS.items():
            formats[fmt] = benchmark_format(img, fmt, suffix, iterations, work_dir)
    return {
        "schema": SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "iterations": iterations,
        "image": {"width": width, "height": height},
        "formats": formats,
    }


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


# ── GitHub-Issues für geflaggte Formate ──────────────────────────────────

def _issue_marker(fmt: str, metric: str) -> str:
    """Stabiler Dedupe-Marker, damit kein Format doppelt gemeldet wird."""
    return f"bgremover-benchmark-regression:{metric}:{fmt}"


def _issue_body(d: FormatDelta, comp: Comparison) -> str:
    return f"""<!-- {_issue_marker(d.fmt, comp.metric)} -->
## Performance-Regression: {d.fmt}

Die Verarbeitungszeit (`{comp.metric}`) für **{d.fmt}** hat sich gegenüber dem
vorigen Benchmark-Lauf um mehr als {comp.threshold:.0f}% verschlechtert.

| | Zeit |
|---|---|
| Vorwoche | {d.baseline_ms:.2f} ms |
| Diese Woche | {d.current_ms:.2f} ms |
| Änderung | +{d.pct_change:.1f}% |

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


def post_issues(comp: Comparison, *, dry_run: bool) -> list[dict[str, str]]:
    """Legt für jedes geflaggte Format ein GitHub-Issue an (idempotent).

    Ohne ``GITHUB_TOKEN``/``GITHUB_REPOSITORY`` (oder mit ``--dry-run``) wird nur
    gedruckt, was passieren würde – derselbe Schutz wie in
    ``create_security_scan_issues.py``.
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
        payload = {"title": title, "body": _issue_body(d, comp)}
        created = _github_request(
            "POST", f"/repos/{repo}/issues", token, api_url=api_url, payload=payload,
        )
        url = str(created.get("html_url") or "")
        print(f"Issue für {d.fmt} angelegt: {url}")
        results.append({"format": d.fmt, "status": "created", "url": url})
    return results


# ── CLI ──────────────────────────────────────────────────────────────────

def _cmd_run(args: argparse.Namespace) -> int:
    result = run_benchmark(args.iterations, args.width, args.height)
    path = save_result(result, args.results_dir)
    print(f"Ergebnis gespeichert: {path.relative_to(ROOT)}")

    if args.no_compare:
        return 0
    baseline = load_baseline(args.results_dir, exclude=path)
    if baseline is None:
        print("Kein früherer Lauf gefunden – dieser Lauf ist die neue Baseline.")
        return 0
    base_path, base_data = baseline
    print(f"Vergleiche gegen Vorwoche: {base_path.relative_to(ROOT)}\n")
    comp = compare(base_data, result, args.metric, args.threshold)
    print(format_report(comp))
    if comp.flagged and (args.post_issues or args.dry_run_issues):
        print()
        post_issues(comp, dry_run=args.dry_run_issues or not args.post_issues)
    return 1 if (comp.flagged and args.fail_on_regression) else 0


def _cmd_compare(args: argparse.Namespace) -> int:
    if args.baseline and args.current:
        base_data = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        cur_data = json.loads(Path(args.current).read_text(encoding="utf-8"))
    else:
        files = _result_files(args.results_dir)
        if len(files) < 2:
            print("Mindestens zwei Ergebnis-Dateien nötig für einen Vergleich.")
            return 2
        base_data = json.loads(files[-2].read_text(encoding="utf-8"))
        cur_data = json.loads(files[-1].read_text(encoding="utf-8"))
        print(f"Vergleiche {files[-2].name} → {files[-1].name}\n")

    comp = compare(base_data, cur_data, args.metric, args.threshold)
    print(format_report(comp))
    if comp.flagged and (args.post_issues or args.dry_run_issues):
        print()
        post_issues(comp, dry_run=args.dry_run_issues or not args.post_issues)
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
