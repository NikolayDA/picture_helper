"""Tests der Live-GL-Performance-Suite (#645) – reine Logik ohne echtes GL."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location("benchmark", ROOT / "scripts" / "benchmark.py")
assert _SPEC is not None and _SPEC.loader is not None
bench = importlib.util.module_from_spec(_SPEC)
sys.modules["benchmark"] = bench
_SPEC.loader.exec_module(bench)


class _FakeHooks(bench.LiveGlHooks):
    """Liefert feste Zeiten; ``frame`` zählt aufsteigend für eine echte Verteilung."""

    def __init__(self) -> None:
        self._frame = 0.0

    def upload(self, mesh: object) -> float:
        return 4.0

    def first_frame(self) -> float:
        return 9.0

    def frame(self) -> float:
        self._frame += 1.0
        return self._frame  # 1,2,3,… ms

    def peak_mb(self) -> float:
        return 12.5


def test_percentile_linear_interpolation() -> None:
    values = [1.0, 2.0, 3.0, 4.0]
    assert bench._percentile(values, 50.0) == pytest.approx(2.5)
    assert bench._percentile(values, 0.0) == 1.0
    assert bench._percentile(values, 100.0) == 4.0
    assert bench._percentile([], 50.0) != bench._percentile([], 50.0)  # nan
    assert bench._percentile([7.0], 95.0) == 7.0


def test_summarize_frame_times() -> None:
    frames = [float(i) for i in range(1, 101)]  # 1..100
    summary = bench.summarize_frame_times(frames)
    assert summary["gl_frame_ms_p50"] == pytest.approx(50.5)
    assert summary["gl_frame_ms_p95"] == pytest.approx(95.05, abs=0.1)


def test_measure_assembles_all_five_metrics() -> None:
    metrics = bench.measure_preview3d_live(object(), _FakeHooks(), frames=10)
    assert set(metrics) == {
        "gl_upload_ms", "gl_first_frame_ms", "gl_peak_mb",
        "gl_frame_ms_p50", "gl_frame_ms_p95",
    }
    assert metrics["gl_upload_ms"] == 4.0
    assert metrics["gl_first_frame_ms"] == 9.0
    assert metrics["gl_peak_mb"] == 12.5
    # Frames 1..10 → p50 = 5.5.
    assert metrics["gl_frame_ms_p50"] == pytest.approx(5.5)


def test_benchmark_with_injected_hooks_builds_real_mesh() -> None:
    # Kleines Feld → echter Mesh-Build, aber GL über Fake gemessen.
    metrics = bench.benchmark_preview3d_live(32, 32, hooks=_FakeHooks(), frames=5)
    assert metrics["gl_upload_ms"] == 4.0
    assert "gl_frame_ms_p95" in metrics


def test_refuses_without_hardware_gl_offscreen(qapp) -> None:  # type: ignore[no-untyped-def]
    # In der Offscreen-CI gibt es keinen GL-Kontext → Verweigerung, kein llvmpipe.
    with pytest.raises(bench.Preview3DLiveUnavailable):
        bench.benchmark_preview3d_live(32, 32)


def test_probe_live_gl_rejects_software_renderer(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from bgremover import preview3d_capability as cap
    from bgremover.preview3d_capability import RendererCapability

    monkeypatch.setattr(
        cap, "probe_3d_capability",
        lambda use_cache=True: RendererCapability(ok=True, diagnostic="Mesa / llvmpipe / 4.5"),
    )
    available, diagnostic = bench.probe_live_gl()
    assert not available
    assert "llvmpipe" in diagnostic


def test_cmd_run_skips_or_fails_without_gl(qapp) -> None:  # type: ignore[no-untyped-def]
    import argparse

    def _args(require_gl: bool) -> argparse.Namespace:
        return argparse.Namespace(
            suite="preview3d-live", require_gl=require_gl, width=1920, height=1080,
            results_dir=None,
        )

    # Offscreen: ohne --require-gl freundlicher Skip (0), mit --require-gl Fehler (2).
    assert bench._cmd_run_preview3d_live(_args(False)) == 0
    assert bench._cmd_run_preview3d_live(_args(True)) == 2
