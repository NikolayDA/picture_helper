"""Tests für die *reine Vergleichslogik* von ``scripts/benchmark.py``.

Die Zeitmessung selbst ist nicht-deterministisch und wird hier bewusst nicht
geprüft; getestet werden die Prozent-Berechnung, das Flaggen jenseits der
Schwelle, das Hinzufügen/Entfallen von Formaten und ein knapper Smoke-Test der
Mess-Pipeline auf einem winzigen Bild.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

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


# ── Umgebungs-Fingerprint (#277/#278/#279) ───────────────────────────────

def test_collect_environment_has_expected_keys() -> None:
    env = bench.collect_environment()
    for key in (
        "python", "pillow", "numpy", "system", "release", "machine",
        "cpu_model", "cpu_count", "runner_arch", "runner_environment",
        "runner_image_os", "runner_image_version", "runner",
    ):
        assert key in env
    # Python/Pillow/NumPy müssen für die Vergleichbarkeit auflösbar sein.
    assert env["python"] and env["pillow"] and env["numpy"]


def test_run_benchmark_records_environment_and_schema() -> None:
    result = bench.run_benchmark(iterations=1, width=16, height=12)
    assert result["schema"] == bench.SCHEMA_VERSION == 3
    assert result["suite"] == "formats"
    assert isinstance(result["environment"], dict)
    assert result["environment"]["python"]
    assert len(result["samples"]["PNG"]["process_ms"]) == 1


# ── Kompatibilität ───────────────────────────────────────────────────────

def _env(**over: object) -> dict:
    base = {
        "python": "3.12.4", "pillow": "11.0.0", "numpy": "2.1.0",
        "system": "Linux", "release": "6.17.0", "machine": "x86_64",
        "cpu_model": "Example CPU", "cpu_count": 4, "runner_arch": "X64",
        "runner_environment": "github-hosted", "runner_image_os": "ubuntu24",
        "runner_image_version": "20260720.1",
    }
    base.update(over)
    return base


def _run(
    env: dict,
    *,
    iterations: int = 7,
    image: dict | None = None,
    commit: str | None = "abc1234",
    **process_ms: float,
) -> dict:
    return {
        "schema": bench.SCHEMA_VERSION,
        "suite": "formats",
        "git_commit": commit,
        "iterations": iterations,
        "image": image or {"width": 1920, "height": 1080},
        "environment": env,
        "formats": {fmt: {"process_ms": v} for fmt, v in process_ms.items()},
        "samples": {},
        "repeats": 1,
    }


def test_compatibility_same_environment_is_comparable() -> None:
    compat = bench.check_compatibility(_run(_env()), _run(_env()))
    assert compat.comparable is True
    assert compat.requires_confirmation is False


def test_compatibility_python_patch_difference_is_ok() -> None:
    # Reiner Patch-Bump (3.12.4 → 3.12.9) darf die Baseline nicht verwerfen.
    compat = bench.check_compatibility(_run(_env(python="3.12.4")), _run(_env(python="3.12.9")))
    assert compat.comparable is True


def test_compatibility_missing_fingerprint_blocks() -> None:
    legacy = {"iterations": 7, "image": {"width": 1920, "height": 1080}, "formats": {}}
    compat = bench.check_compatibility(legacy, _run(_env()))
    assert compat.comparable is False


def test_compatibility_schema_or_suite_mismatch_blocks() -> None:
    baseline = _run(_env())
    baseline["schema"] = 2
    assert bench.check_compatibility(baseline, _run(_env())).comparable is False

    baseline = _run(_env())
    baseline["suite"] = "height"
    assert bench.check_compatibility(baseline, _run(_env())).comparable is False


def test_compatibility_version_mismatch_blocks() -> None:
    for over in ({"pillow": "12.0.0"}, {"numpy": "3.0.0"}, {"python": "3.13.0"}):
        compat = bench.check_compatibility(_run(_env()), _run(_env(**over)))
        assert compat.comparable is False, over


def test_compatibility_benchmark_param_mismatch_blocks() -> None:
    assert bench.check_compatibility(
        _run(_env(), iterations=5), _run(_env(), iterations=7)
    ).comparable is False
    assert bench.check_compatibility(
        _run(_env(), image={"width": 800, "height": 600}), _run(_env())
    ).comparable is False


def test_compatibility_hardware_difference_blocks_comparison() -> None:
    compat = bench.check_compatibility(_run(_env(cpu_count=2)), _run(_env(cpu_count=8)))
    assert compat.comparable is False
    assert compat.requires_confirmation is False
    assert compat.reasons  # nennt den Grund


def test_compatibility_runner_image_difference_blocks_comparison() -> None:
    compat = bench.check_compatibility(
        _run(_env(runner_image_version="20260713.1")),
        _run(_env(runner_image_version="20260720.1")),
    )
    assert compat.comparable is False
    assert "Runner-Image-Version" in " ".join(compat.reasons)


# ── Median-Aggregation (Bestätigungslauf) ────────────────────────────────

def test_aggregate_results_takes_median_per_metric() -> None:
    runs = [
        _run(_env(), PNG=10.0),
        _run(_env(), PNG=30.0),
        _run(_env(), PNG=20.0),
    ]
    merged = bench.aggregate_results(runs)
    assert merged["formats"]["PNG"]["process_ms"] == 20.0
    assert merged["repeats"] == 3
    assert [run["formats"]["PNG"]["process_ms"] for run in merged["runs"]] == [
        10.0, 30.0, 20.0,
    ]


# ── Issue-Kontext ────────────────────────────────────────────────────────

def test_issue_body_includes_confirmation_context() -> None:
    comp = bench.compare(_result(PNG=100.0), _result(PNG=150.0))
    ctx = bench.IssueContext(
        baseline_label="2026-06-15.json",
        current_commit="abc1234",
        environment=_env(),
        confirm_runs=3,
        requires_confirmation=True,
    )
    body = bench._issue_body(comp.flagged[0], comp, ctx)
    assert "2026-06-15.json" in body
    assert "abc1234" in body
    assert "Bestätigungsläufe: 3" in body
    assert "python=3.12.4" in body


# ── CLI-Gate: nur bestätigte, vergleichbare Regressionen werden gemeldet ──

def _seed_baseline(tmp_path: Path, env: dict, **process_ms: float) -> None:
    """Schreibt eine ältere Baseline-Datei (alphabetisch vor dem Lauf-Datum)."""
    (tmp_path / "2000-01-01.json").write_text(
        json.dumps(_run(env, **process_ms)), encoding="utf-8"
    )


def test_run_does_not_post_issue_when_baseline_incompatible(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # Baseline mit abweichender Pillow-Version → nicht vergleichbar.
    _seed_baseline(tmp_path, _env(pillow="9.0.0"), PNG=1.0, JPEG=1.0, WebP=1.0, TIFF=1.0)
    monkeypatch.setattr(
        bench, "run_benchmark",
        lambda *a, **k: _run(_env(), PNG=500.0, JPEG=500.0, WebP=500.0, TIFF=500.0),
    )
    posted: list = []
    monkeypatch.setattr(bench, "post_issues", lambda *a, **k: posted.append(a) or [])

    rc = bench.main([
        "run", "--results-dir", str(tmp_path), "--dry-run-issues",
        "--fail-on-regression", "--confirm-runs", "3",
    ])
    assert rc == 0
    assert posted == []
    assert "NICHT VERGLEICHBAR" in capsys.readouterr().out


def test_run_clears_flag_when_confirmation_shows_no_regression(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # Kompatible Baseline; der erste Lauf ist auffällig, der Bestätigungslauf
    # liegt aber wieder unter der Schwelle → kein Issue, Exit 0.
    _seed_baseline(tmp_path, _env(), PNG=100.0, JPEG=100.0, WebP=100.0, TIFF=100.0)
    outcomes = iter([
        # 1) gespeicherter Lauf: stark erhöht → wird zunächst geflaggt
        _run(_env(), PNG=200.0, JPEG=200.0, WebP=200.0, TIFF=200.0),
        # 2..) Bestätigungsläufe: wieder im grünen Bereich
        _run(_env(), PNG=101.0, JPEG=101.0, WebP=101.0, TIFF=101.0),
        _run(_env(), PNG=100.0, JPEG=100.0, WebP=100.0, TIFF=100.0),
    ])
    monkeypatch.setattr(bench, "run_benchmark", lambda *a, **k: next(outcomes))
    posted: list = []
    monkeypatch.setattr(bench, "post_issues", lambda *a, **k: posted.append(a) or [])

    rc = bench.main([
        "run", "--results-dir", str(tmp_path), "--dry-run-issues",
        "--fail-on-regression", "--confirm-runs", "3",
    ])
    assert rc == 0
    assert posted == []
    assert "Bestätigungslauf zeigt keine Regression" in capsys.readouterr().out

    # Die committete Baseline muss der bestätigte Median sein (200/101/100 → 101),
    # nicht der gespeicherte Erstlauf-Ausreißer (200).
    saved_path = next(p for p in tmp_path.glob("*.json") if p.name != "2000-01-01.json")
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    assert saved["repeats"] == 3
    assert saved["formats"]["PNG"]["process_ms"] == 101.0


def test_compare_blocks_report_for_hardware_mismatch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # Reine Hardware-Abweichung: ``compare`` kann nicht nachmessen → kein Issue.
    base = tmp_path / "base.json"
    cur = tmp_path / "cur.json"
    base.write_text(json.dumps(_run(_env(cpu_count=2), PNG=100.0)), encoding="utf-8")
    cur.write_text(json.dumps(_run(_env(cpu_count=8), PNG=200.0)), encoding="utf-8")
    posted: list = []
    monkeypatch.setattr(bench, "post_issues", lambda *a, **k: posted.append(a) or [])

    rc = bench.main([
        "compare", "--baseline", str(base), "--current", str(cur),
        "--dry-run-issues", "--fail-on-regression",
    ])
    assert rc == 0
    assert posted == []
    assert "NICHT VERGLEICHBAR" in capsys.readouterr().out


def test_compare_reports_for_fully_comparable_baseline(
    tmp_path: Path, monkeypatch
) -> None:
    # Gegenprobe: vollständig vergleichbare Baseline meldet eine Regression.
    base = tmp_path / "base.json"
    cur = tmp_path / "cur.json"
    base.write_text(json.dumps(_run(_env(), PNG=100.0)), encoding="utf-8")
    cur.write_text(json.dumps(_run(_env(), PNG=200.0)), encoding="utf-8")
    posted: list = []
    monkeypatch.setattr(bench, "post_issues", lambda *a, **k: posted.append(a) or [])

    rc = bench.main([
        "compare", "--baseline", str(base), "--current", str(cur),
        "--dry-run-issues", "--fail-on-regression",
    ])
    assert rc == 1
    assert len(posted) == 1


def test_paired_compare_persists_all_runs_and_stays_green(
    tmp_path: Path, capsys,
) -> None:
    baseline_paths: list[Path] = []
    current_paths: list[Path] = []
    for index, (baseline_ms, current_ms) in enumerate(
        [(100.0, 105.0), (102.0, 103.0), (98.0, 104.0), (101.0, 102.0)],
        start=1,
    ):
        baseline = tmp_path / f"baseline-{index}.json"
        current = tmp_path / f"current-{index}.json"
        baseline.write_text(
            json.dumps(_run(_env(), commit="base123", PNG=baseline_ms)),
            encoding="utf-8",
        )
        current.write_text(
            json.dumps(_run(_env(), commit="cur456", PNG=current_ms)),
            encoding="utf-8",
        )
        baseline_paths.append(baseline)
        current_paths.append(current)

    output = tmp_path / "paired.json"
    rc = bench.main([
        "paired-compare",
        "--baseline", *(str(path) for path in baseline_paths),
        "--current", *(str(path) for path in current_paths),
        "--output", str(output),
        "--fail-on-regression",
    ])

    assert rc == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["kind"] == "paired-comparison"
    assert payload["pairs"] == 4
    assert payload["baseline"]["repeats"] == 4
    assert len(payload["current"]["runs"]) == 4
    assert payload["comparison"]["deltas"][0]["degraded"] is False
    assert payload["comparison"]["aggregation"] == (
        "median-of-pair-percentage-changes"
    )
    assert len(payload["comparison"]["pair_comparisons"]) == 4
    assert "Gepaarter A/B-Vergleich (4 Paare)" in capsys.readouterr().out


def test_paired_compare_aggregates_pairwise_percentage_changes(
    tmp_path: Path,
) -> None:
    """Runner-Drift zwischen Paaren darf einen Mehrheitsbefund nicht verdecken."""
    baseline_paths: list[Path] = []
    current_paths: list[Path] = []
    for index, (baseline_ms, current_ms) in enumerate(
        [(100.0, 120.0), (100.0, 120.0), (1000.0, 1200.0), (1000.0, 500.0)],
        start=1,
    ):
        baseline = tmp_path / f"baseline-{index}.json"
        current = tmp_path / f"current-{index}.json"
        baseline.write_text(
            json.dumps(_run(_env(), commit="base123", PNG=baseline_ms)),
            encoding="utf-8",
        )
        current.write_text(
            json.dumps(_run(_env(), commit="cur456", PNG=current_ms)),
            encoding="utf-8",
        )
        baseline_paths.append(baseline)
        current_paths.append(current)

    output = tmp_path / "paired.json"
    rc = bench.main([
        "paired-compare",
        "--baseline", *(str(path) for path in baseline_paths),
        "--current", *(str(path) for path in current_paths),
        "--output", str(output),
        "--fail-on-regression",
    ])

    assert rc == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    delta = payload["comparison"]["deltas"][0]
    assert delta["pct_change"] == 20.0
    assert delta["degraded"] is True
    assert [
        pair["deltas"][0]["pct_change"]
        for pair in payload["comparison"]["pair_comparisons"]
    ] == [20.0, 20.0, 20.0, -50.0]


def test_paired_compare_rejects_mixed_commits(tmp_path: Path, capsys) -> None:
    baseline_paths: list[Path] = []
    current_paths: list[Path] = []
    for index in range(4):
        baseline = tmp_path / f"baseline-{index}.json"
        current = tmp_path / f"current-{index}.json"
        baseline.write_text(
            json.dumps(
                _run(
                    _env(), commit="other789" if index == 3 else "base123",
                    PNG=100.0,
                )
            ),
            encoding="utf-8",
        )
        current.write_text(
            json.dumps(_run(_env(), commit="cur456", PNG=100.0)),
            encoding="utf-8",
        )
        baseline_paths.append(baseline)
        current_paths.append(current)

    rc = bench.main([
        "paired-compare",
        "--baseline", *(str(path) for path in baseline_paths),
        "--current", *(str(path) for path in current_paths),
    ])

    assert rc == 2
    assert "mehrere Commits" in capsys.readouterr().out


def test_paired_compare_rejects_odd_pair_count(tmp_path: Path, capsys) -> None:
    baseline_paths: list[Path] = []
    current_paths: list[Path] = []
    for index in range(3):
        baseline = tmp_path / f"baseline-{index}.json"
        current = tmp_path / f"current-{index}.json"
        baseline.write_text(
            json.dumps(_run(_env(), commit="base123", PNG=100.0)),
            encoding="utf-8",
        )
        current.write_text(
            json.dumps(_run(_env(), commit="cur456", PNG=100.0)),
            encoding="utf-8",
        )
        baseline_paths.append(baseline)
        current_paths.append(current)

    rc = bench.main([
        "paired-compare",
        "--baseline", *(str(path) for path in baseline_paths),
        "--current", *(str(path) for path in current_paths),
        "--minimum-pairs", "3",
    ])

    assert rc == 2
    assert "gerade Anzahl" in capsys.readouterr().out


def test_paired_compare_rejects_different_runner_images(tmp_path: Path) -> None:
    baseline_paths: list[Path] = []
    current_paths: list[Path] = []
    for index in range(4):
        baseline = tmp_path / f"baseline-{index}.json"
        current = tmp_path / f"current-{index}.json"
        baseline.write_text(
            json.dumps(
                _run(
                    _env(runner_image_version="old"), commit="base123", PNG=100.0,
                )
            ),
            encoding="utf-8",
        )
        current.write_text(
            json.dumps(
                _run(
                    _env(runner_image_version="new"), commit="cur456", PNG=100.0,
                )
            ),
            encoding="utf-8",
        )
        baseline_paths.append(baseline)
        current_paths.append(current)

    rc = bench.main([
        "paired-compare",
        "--baseline", *(str(path) for path in baseline_paths),
        "--current", *(str(path) for path in current_paths),
    ])
    assert rc == 2


def test_run_benchmark_height_pipeline_metrics(tmp_path: Path) -> None:
    """Höhen-Baseline (#590): kleine Größen liefern alle vier Metriken."""
    result = bench.run_benchmark(
        iterations=1, width=16, height=12,
        height_sizes={"HEIGHT16-TINY": (8, 6, 1)},
    )
    metrics = result["formats"]["HEIGHT16-TINY"]
    for key in ("import_ms", "process_ms", "roundtrip_ms", "preview_ms"):
        assert metrics[key] >= 0.0
    # Bestehende Format-Messungen bleiben unangetastet daneben stehen.
    assert set(bench.BENCH_FORMATS) <= set(result["formats"])


def test_run_benchmark_can_isolate_height_suite() -> None:
    result = bench.run_benchmark(
        iterations=1, width=16, height=12,
        height_sizes={"HEIGHT16-TINY": (8, 6, 1)}, include_formats=False,
    )
    assert result["suite"] == "height"
    assert set(result["formats"]) == {"HEIGHT16-TINY"}
    assert result["samples"] == {}


def test_run_benchmark_includes_mesh_build_metrics(tmp_path: Path) -> None:
    """3D-Baseline (#595): die Höhenszenarien tragen die ``mesh_*``-Metriken."""
    result = bench.run_benchmark(
        iterations=1, width=16, height=12,
        height_sizes={"HEIGHT16-TINY": (64, 48, 1)},
    )
    metrics = result["formats"]["HEIGHT16-TINY"]
    for key in ("mesh_build_ms", "mesh_peak_mb", "mesh_vertices",
                "mesh_triangles", "mesh_decimation"):
        assert key in metrics
    assert metrics["mesh_build_ms"] >= 0.0
    assert metrics["mesh_vertices"] > 0.0
    assert metrics["mesh_decimation"] >= 1.0


def test_benchmark_mesh_build_respects_quality_budget() -> None:
    """Auch ein großes Feld bleibt unter dem harten Vertex-/Dreiecksbudget und
    hält den transienten Peak-Speicher unter dem 128-MB-Deckel (kein Vollmesh)."""
    from bgremover.height_map import HeightField
    from bgremover.relief_mesh import MeshQuality

    width = height = 4000  # 16 MP
    values = bench.make_height_values(width, height)
    coverage = np.full((height, width), 255, dtype=np.uint8)
    field = HeightField(values, coverage, max_value=65535)

    metrics = bench.benchmark_mesh_build(field, iterations=1)
    assert metrics["mesh_vertices"] <= float(MeshQuality.STANDARD.max_vertices)
    assert metrics["mesh_triangles"] <= float(MeshQuality.STANDARD.max_triangles)
    assert metrics["mesh_decimation"] > 1.0  # 16 MP wird zwingend decimiert
    assert metrics["mesh_peak_mb"] < 128.0


def test_make_height_values_matches_mgrid_reference() -> None:
    """Die broadcasting-basierte Musterbildung bleibt bitgenau zur Referenz."""
    width, height = 37, 19
    yy, xx = np.mgrid[0:height, 0:width]
    reference = ((xx * 131 + yy * 17) % 65536).astype(np.uint16)
    assert np.array_equal(bench.make_height_values(width, height), reference)


# ── CLI isoliert Format- und HEIGHT-Suite (#630) ─────────────────────────

def test_cli_run_defaults_to_format_suite(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[tuple[dict | None, bool]] = []

    def fake_run_benchmark(
        iterations, width, height, height_sizes=None, *, include_formats=True,
    ):
        calls.append((height_sizes, include_formats))
        return _run(_env(), iterations=iterations)

    monkeypatch.setattr(bench, "run_benchmark", fake_run_benchmark)
    rc = bench.main([
        "run", "--results-dir", str(tmp_path), "--no-compare",
        "--iterations", str(bench.DEFAULT_ITERATIONS),
        "--width", str(bench.DEFAULT_WIDTH),
        "--height", str(bench.DEFAULT_HEIGHT),
    ])
    assert rc == 0
    assert calls == [(None, True)]


def test_cli_run_scaled_dimensions_stays_in_format_suite(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[tuple[dict | None, bool]] = []

    def fake_run_benchmark(
        iterations, width, height, height_sizes=None, *, include_formats=True,
    ):
        calls.append((height_sizes, include_formats))
        return _run(_env(), iterations=iterations, image={"width": width, "height": height})

    monkeypatch.setattr(bench, "run_benchmark", fake_run_benchmark)
    rc = bench.main([
        "run", "--results-dir", str(tmp_path), "--no-compare",
        "--width", "16", "--height", "12", "--iterations", "1",
    ])
    assert rc == 0
    assert calls == [(None, True)]


def test_cli_height_suite_excludes_format_benchmark(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[tuple[dict | None, bool]] = []

    def fake_run_benchmark(
        iterations, width, height, height_sizes=None, *, include_formats=True,
    ):
        calls.append((height_sizes, include_formats))
        result = _run(
            _env(), iterations=iterations, image={"width": width, "height": height},
        )
        result["suite"] = "height"
        return result

    monkeypatch.setattr(bench, "run_benchmark", fake_run_benchmark)
    rc = bench.main([
        "run", "--results-dir", str(tmp_path), "--no-compare",
        "--width", "16", "--height", "12", "--iterations", "1",
        "--suite", "height",
    ])
    assert rc == 0
    assert calls == [(bench.HEIGHT_BENCH_SIZES, False)]


def test_cli_height_bench_alias_is_isolated(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[tuple[dict | None, bool]] = []

    def fake_run_benchmark(
        iterations, width, height, height_sizes=None, *, include_formats=True,
    ):
        calls.append((height_sizes, include_formats))
        result = _run(_env(), iterations=iterations)
        result["suite"] = "height"
        return result

    monkeypatch.setattr(bench, "run_benchmark", fake_run_benchmark)
    rc = bench.main([
        "run", "--results-dir", str(tmp_path), "--no-compare",
        "--iterations", str(bench.DEFAULT_ITERATIONS),
        "--width", str(bench.DEFAULT_WIDTH),
        "--height", str(bench.DEFAULT_HEIGHT),
        "--height-bench",
    ])
    assert rc == 0
    assert calls == [(bench.HEIGHT_BENCH_SIZES, False)]
