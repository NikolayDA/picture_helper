"""Tests für die *reine Vergleichslogik* von ``scripts/benchmark.py``.

Die Zeitmessung selbst ist nicht-deterministisch und wird hier bewusst nicht
geprüft; getestet werden die Prozent-Berechnung, das Flaggen jenseits der
Schwelle, das Hinzufügen/Entfallen von Formaten und ein knapper Smoke-Test der
Mess-Pipeline auf einem winzigen Bild.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Das Skript via importlib laden (scripts/ ist kein Paket). Der Modulname muss
# in sys.modules stehen, sonst scheitert die Typprüfung der frozen-dataclasses
# unter ``from __future__ import annotations``.
_SPEC = importlib.util.spec_from_file_location(
    "benchmark", ROOT / "scripts" / "benchmark.py"
)
assert _SPEC is not None and _SPEC.loader is not None
bench = importlib.util.module_from_spec(_SPEC)
sys.modules["benchmark"] = bench
_SPEC.loader.exec_module(bench)


def _result(**process_ms: float) -> dict:
    return {"formats": {fmt: {"process_ms": v} for fmt, v in process_ms.items()}}


# ── pct_change ───────────────────────────────────────────────────────────

def test_pct_change_increase() -> None:
    assert bench.pct_change(100.0, 120.0) == 20.0


def test_pct_change_decrease_is_negative() -> None:
    assert bench.pct_change(100.0, 80.0) == -20.0


def test_pct_change_zero_baseline_is_safe() -> None:
    # Keine Division durch null, kein irreführender Riesenwert.
    assert bench.pct_change(0.0, 50.0) == 0.0
    assert bench.pct_change(-5.0, 50.0) == 0.0


# ── compare / Flaggen ────────────────────────────────────────────────────

def test_compare_flags_only_above_threshold() -> None:
    base = _result(PNG=100.0, JPEG=50.0)
    cur = _result(PNG=110.5, JPEG=55.0)  # PNG +10.5% (>10), JPEG +10.0% (==, nicht >)
    comp = bench.compare(base, cur, threshold=10.0)

    flagged = {d.fmt for d in comp.flagged}
    assert flagged == {"PNG"}
    jpeg = next(d for d in comp.deltas if d.fmt == "JPEG")
    assert jpeg.degraded is False
    assert jpeg.pct_change == 10.0


def test_compare_improvement_not_flagged() -> None:
    comp = bench.compare(_result(WebP=300.0), _result(WebP=200.0))
    assert comp.flagged == []
    assert comp.deltas[0].pct_change < 0


def test_compare_tracks_added_and_removed() -> None:
    comp = bench.compare(_result(PNG=10.0, TIFF=20.0), _result(PNG=10.0, WebP=5.0))
    assert comp.added == ["WebP"]
    assert comp.removed == ["TIFF"]
    # Nur gemeinsame Formate erhalten ein Delta.
    assert [d.fmt for d in comp.deltas] == ["PNG"]


def test_compare_custom_metric() -> None:
    base = {"formats": {"PNG": {"encode_ms": 100.0}}}
    cur = {"formats": {"PNG": {"encode_ms": 130.0}}}
    comp = bench.compare(base, cur, metric="encode_ms", threshold=10.0)
    assert comp.deltas[0].degraded is True
    assert comp.deltas[0].pct_change == 30.0


# ── Report / Issue-Body ──────────────────────────────────────────────────

def test_report_stable_message_when_no_regression() -> None:
    report = bench.format_report(bench.compare(_result(PNG=100.0), _result(PNG=101.0)))
    assert "stabil" in report
    assert "DEGRADIERT" not in report


def test_report_lists_flagged_formats() -> None:
    report = bench.format_report(bench.compare(_result(PNG=100.0), _result(PNG=150.0)))
    assert "DEGRADIERT" in report
    assert "PNG" in report
    assert "+50.0%" in report


def test_issue_body_is_idempotent_marker() -> None:
    comp = bench.compare(_result(PNG=100.0), _result(PNG=150.0))
    body = bench._issue_body(comp.flagged[0], comp)
    assert bench._issue_marker("PNG", "process_ms") in body


def test_post_issues_dry_run_does_not_call_network() -> None:
    comp = bench.compare(_result(PNG=100.0), _result(PNG=150.0))
    results = bench.post_issues(comp, dry_run=True)
    assert results == [{"format": "PNG", "status": "dry-run", "url": ""}]


# ── Mess-Pipeline (winziger Smoke-Test) ──────────────────────────────────

def test_run_benchmark_covers_all_formats() -> None:
    result = bench.run_benchmark(iterations=1, width=16, height=12)
    assert set(result["formats"]) == set(bench.BENCH_FORMATS)
    for metrics in result["formats"].values():
        assert metrics["process_ms"] >= 0.0
        assert metrics["encoded_bytes"] > 0.0


def test_save_and_load_baseline_roundtrip(tmp_path: Path) -> None:
    result = {"schema": 1, "formats": {"PNG": {"process_ms": 1.0}}}
    path = bench.save_result(result, tmp_path)
    assert path.exists()
    # Ohne zweite Datei gibt es keine Baseline.
    assert bench.load_baseline(tmp_path, exclude=path) is None
    # Zweite Datei → die erste ist die Baseline.
    second = bench.save_result({"schema": 1, "formats": {}}, tmp_path)
    loaded = bench.load_baseline(tmp_path, exclude=second)
    assert loaded is not None and loaded[0] == path
