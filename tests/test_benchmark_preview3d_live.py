"""Tests der Live-GL-Performance-Suite (#645) – reine Logik ohne echtes GL."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
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
        self.closed = False

    def upload(self, mesh: object) -> float:
        return 4.0

    def first_frame(self) -> float:
        return 9.0

    def frame(self) -> float:
        self._frame += 1.0
        return self._frame  # 1,2,3,… ms

    def peak_mb(self) -> float:
        return 12.5

    def close(self) -> None:
        self.closed = True


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
    hooks = _FakeHooks()
    metrics = bench.measure_preview3d_live(object(), hooks, frames=10)
    assert set(metrics) == {
        "gl_upload_ms", "gl_first_frame_ms", "gl_peak_mb",
        "gl_frame_ms_p50", "gl_frame_ms_p95",
    }
    assert metrics["gl_upload_ms"] == 4.0
    assert metrics["gl_first_frame_ms"] == 9.0
    assert metrics["gl_peak_mb"] == 12.5
    # Frames 1..10 → p50 = 5.5.
    assert metrics["gl_frame_ms_p50"] == pytest.approx(5.5)
    assert hooks.closed


def test_benchmark_with_injected_hooks_builds_real_mesh() -> None:
    # Kleines Feld → echter Mesh-Build, aber GL über Fake gemessen.
    metrics = bench.benchmark_preview3d_live(32, 32, hooks=_FakeHooks(), frames=5)
    assert metrics["gl_upload_ms"] == 4.0
    assert "gl_frame_ms_p95" in metrics


def test_repeated_live_gl_uses_medians_peak_max_and_keeps_samples(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    measurements = iter([
        {"gl_upload_ms": 9.0, "gl_first_frame_ms": 30.0, "gl_peak_mb": 100.0,
         "gl_frame_ms_p50": 6.0, "gl_frame_ms_p95": 10.0},
        {"gl_upload_ms": 3.0, "gl_first_frame_ms": 10.0, "gl_peak_mb": 120.0,
         "gl_frame_ms_p50": 2.0, "gl_frame_ms_p95": 4.0},
        {"gl_upload_ms": 6.0, "gl_first_frame_ms": 20.0, "gl_peak_mb": 110.0,
         "gl_frame_ms_p50": 4.0, "gl_frame_ms_p95": 7.0},
    ])
    monkeypatch.setattr(bench, "benchmark_preview3d_live", lambda *a, **kw: next(measurements))

    summary, samples = bench.benchmark_preview3d_live_repeated(32, 32, 3)

    assert summary["gl_upload_ms"] == 6.0
    assert summary["gl_first_frame_ms"] == 20.0
    assert summary["gl_frame_ms_p95"] == 7.0
    assert summary["gl_peak_mb"] == 120.0
    assert samples["gl_upload_ms"] == [9.0, 3.0, 6.0]


def test_process_peak_rss_converts_linux_kib_and_macos_bytes() -> None:
    assert bench._process_peak_rss_mb(128 * 1024, "linux") == 128.0
    assert bench._process_peak_rss_mb(128 * 1024 * 1024, "darwin") == 128.0


@pytest.mark.gl_smoke
def test_real_hook_renders_and_measures_real_metrics(qapp) -> None:  # type: ignore[no-untyped-def]
    """Verhaltensnachweis statt Source-Grep (#716): treibt den echten
    Shader-/Buffer-/Draw-Pfad von ``_QtGlLiveHooks`` end-to-end durch einen
    echten, renderbaren GL-Kontext, statt nur nach Literal-Substrings im
    Quelltext zu suchen (das würde bei totem/verschobenem Code weiter grün
    bleiben). Läuft – wie die übrigen ``gl_smoke``-Tests – nur dort, wo ein
    echter FBO gerendert werden kann; sonst übersprungen."""
    from PyQt6.QtWidgets import QApplication

    from bgremover.height_map import HEIGHT_MAX_16BIT, HeightField
    from bgremover.preview3d_capability import probe_3d_capability, reset_capability_cache
    from bgremover.relief_mesh import MeshQuality, build_relief_mesh

    app = QApplication.instance()
    assert app is not None
    if app.platformName() in {"offscreen", "minimal", "vnc"}:
        pytest.skip(f"Plattform {app.platformName()!r} kann keinen echten GL-Kontext rendern")
    reset_capability_cache()
    if not probe_3d_capability(use_cache=False).ok:
        pytest.skip("Keine OpenGL-2.1-Capability in dieser Umgebung")
    available, diagnostic = bench.probe_live_gl()
    if not available:
        pytest.skip(f"probe_live_gl meldet keinen Hardware-GL-Kontext ({diagnostic!r})")

    ramp = np.tile(np.linspace(0, HEIGHT_MAX_16BIT, 32, dtype=np.uint16), (32, 1))
    field = HeightField(ramp, np.full((32, 32), 255, np.uint8), HEIGHT_MAX_16BIT)
    mesh = build_relief_mesh(field, MeshQuality.REDUCED)

    hooks = bench._QtGlLiveHooks(diagnostic)
    metrics = bench.measure_preview3d_live(mesh, hooks, frames=3)

    assert metrics["gl_upload_ms"] >= 0.0
    assert metrics["gl_first_frame_ms"] >= 0.0
    assert metrics["gl_peak_mb"] > 0.0
    assert metrics["gl_frame_ms_p50"] >= 0.0
    assert metrics["gl_frame_ms_p95"] >= 0.0
    # first_frame() zaehlt einen Draw, die drei angeforderten frame()-Aufrufe
    # (frames=3) je einen weiteren – ein auf eine Dummy-Zeit ohne echten Draw
    # regressiertes frame() wuerde den Zaehler bei 1 belassen und hier auffallen.
    assert hooks._frame_number == 4


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
            results_dir=None, iterations=3,
        )

    # Offscreen: ohne --require-gl freundlicher Skip (0), mit --require-gl Fehler (2).
    assert bench._cmd_run_preview3d_live(_args(False)) == 0
    assert bench._cmd_run_preview3d_live(_args(True)) == 2


def test_cmd_run_persists_repeats_and_raw_samples(qapp, monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    import argparse

    saved: dict[str, object] = {}
    monkeypatch.setattr(bench, "probe_live_gl", lambda: (True, "Apple / M3 / Metal"))
    monkeypatch.setattr(
        bench,
        "benchmark_preview3d_live_repeated",
        lambda *a, **kw: (
            {"gl_upload_ms": 4.0, "gl_first_frame_ms": 9.0, "gl_peak_mb": 80.0,
             "gl_frame_ms_p50": 2.0, "gl_frame_ms_p95": 3.0},
            {"gl_upload_ms": [3.0, 4.0, 5.0]},
        ),
    )
    monkeypatch.setattr(bench, "collect_environment", lambda: {})
    monkeypatch.setattr(bench, "git_commit", lambda: "abc")

    def _save(result, results_dir):  # type: ignore[no-untyped-def]
        saved.update(result)
        return tmp_path / "result.json"

    monkeypatch.setattr(bench, "save_result", _save)
    args = argparse.Namespace(
        suite="preview3d-live", require_gl=True, width=1920, height=1080,
        results_dir=tmp_path, iterations=3, platform="macos-arm64",
    )

    assert bench._cmd_run_preview3d_live(args) == 0
    assert saved["iterations"] == 3
    assert saved["repeats"] == 3
    assert saved["platform"] == "macos-arm64"
    assert saved["samples"]
