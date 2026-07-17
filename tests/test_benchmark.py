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
    for key in ("python", "pillow", "numpy", "system", "machine", "cpu_count", "runner"):
        assert key in env
    # Python/Pillow/NumPy müssen für die Vergleichbarkeit auflösbar sein.
    assert env["python"] and env["pillow"] and env["numpy"]


def test_run_benchmark_records_environment_and_schema() -> None:
    result = bench.run_benchmark(iterations=1, width=16, height=12)
    assert result["schema"] == bench.SCHEMA_VERSION == 2
    assert isinstance(result["environment"], dict)
    assert result["environment"]["python"]


# ── Kompatibilität ───────────────────────────────────────────────────────

def _env(**over: object) -> dict:
    base = {
        "python": "3.12.4", "pillow": "11.0.0", "numpy": "2.1.0",
        "machine": "x86_64", "cpu_count": 4,
    }
    base.update(over)
    return base


def _run(env: dict, *, iterations: int = 7, image: dict | None = None, **process_ms: float) -> dict:
    return {
        "iterations": iterations,
        "image": image or {"width": 1920, "height": 1080},
        "environment": env,
        "formats": {fmt: {"process_ms": v} for fmt, v in process_ms.items()},
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


def test_compatibility_hardware_difference_requires_confirmation() -> None:
    compat = bench.check_compatibility(_run(_env(cpu_count=2)), _run(_env(cpu_count=8)))
    assert compat.comparable is True
    assert compat.requires_confirmation is True
    assert compat.reasons  # nennt den Grund


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
        "--fail-on-regression", "--confirm-runs", "2",
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
        "--fail-on-regression", "--confirm-runs", "2",
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
    assert "Hardware weicht ab" in capsys.readouterr().out


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
