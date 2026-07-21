"""Tests der Evidenz-Aggregation und Abschlussmatrix (#646)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "abnahme_aggregate", ROOT / "scripts" / "abnahme_aggregate.py"
)
assert _SPEC is not None and _SPEC.loader is not None
agg = importlib.util.module_from_spec(_SPEC)
sys.modules["abnahme_aggregate"] = agg
_SPEC.loader.exec_module(agg)


def _evidence(platform: str, status: str = "bestanden", **extra: object) -> dict:
    base = {
        "schema": 1, "kind": "abnahme-evidenz", "platform": platform, "status": status,
        "commit_sha": "abc", "quelle": {"art": "release-tag", "wert": "v2.7.0"},
        "artefakte": [], "umgebung": {}, "erzeugt_am": "2026-07-21T00:00:00+00:00",
        "gl_provenance": "Broadcom / V3D 7.1 / 3.1",
    }
    base.update(extra)
    return base


def _write(root: Path, platform: str, data: dict) -> None:
    d = root / f"abnahme-{platform}"
    d.mkdir(parents=True)
    (d / "evidenz.json").write_text(json.dumps(data), encoding="utf-8")


def test_validate_evidence_reports_missing_fields() -> None:
    assert agg.validate_evidence(_evidence("linux-arm64")) == []
    broken = _evidence("linux-arm64")
    del broken["commit_sha"]
    del broken["umgebung"]
    assert set(agg.validate_evidence(broken)) == {"commit_sha", "umgebung"}


def test_matrix_all_passed(tmp_path: Path) -> None:
    _write(tmp_path, "macos-arm64", _evidence("macos-arm64"))
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    rows = agg.build_matrix(
        agg.load_evidence(tmp_path), e2e={"status": "bestanden"},
    )
    by = {r.kriterium: r.status for r in rows}
    assert by[agg.EXPECTED_PLATFORMS["macos-arm64"]] == "erfuellt"
    assert by[agg.EXPECTED_PLATFORMS["linux-arm64"]] == "erfuellt"
    # x86_64 immer sichtbar als pausiert (kein GPU-Zugang).
    assert any(r.status == "pausiert" and r.kriterium == agg.PAUSED_LABEL for r in rows)
    assert not agg.has_blocking_gaps(rows)


def test_missing_platform_is_gap(tmp_path: Path) -> None:
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    rows = agg.build_matrix(agg.load_evidence(tmp_path))
    by = {r.kriterium: r.status for r in rows}
    assert by[agg.EXPECTED_PLATFORMS["macos-arm64"]] == "fehlt"
    assert agg.has_blocking_gaps(rows)


def test_failed_status_maps_and_blocks(tmp_path: Path) -> None:
    _write(tmp_path, "macos-arm64", _evidence("macos-arm64", status="fehlgeschlagen"))
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    rows = agg.build_matrix(agg.load_evidence(tmp_path), e2e={"status": "bestanden"})
    by = {r.kriterium: r.status for r in rows}
    assert by[agg.EXPECTED_PLATFORMS["macos-arm64"]] == "fehlgeschlagen"
    assert agg.has_blocking_gaps(rows)


def test_contract_violation_flags_unbewertet(tmp_path: Path) -> None:
    broken = _evidence("linux-arm64")
    del broken["commit_sha"]
    _write(tmp_path, "macos-arm64", _evidence("macos-arm64"))
    _write(tmp_path, "linux-arm64", broken)
    rows = agg.build_matrix(agg.load_evidence(tmp_path))
    row = next(r for r in rows if r.kriterium == agg.EXPECTED_PLATFORMS["linux-arm64"])
    assert row.status == "unbewertet"
    assert "commit_sha" in row.hinweis


def test_x86_64_enabled_uses_evidence(tmp_path: Path) -> None:
    _write(tmp_path, "macos-arm64", _evidence("macos-arm64"))
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    _write(tmp_path, "linux-x86_64", _evidence("linux-x86_64"))
    rows = agg.build_matrix(agg.load_evidence(tmp_path), x86_64_enabled=True)
    row = next(r for r in rows if r.kriterium == agg.PAUSED_LABEL)
    assert row.status == "erfuellt"


def test_render_markdown_contains_all_states(tmp_path: Path) -> None:
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    rows = agg.build_matrix(agg.load_evidence(tmp_path))
    md = agg.render_markdown(rows, commit_sha="deadbeef")
    assert "Abschlussmatrix" in md
    assert "deadbeef" in md
    assert "pausiert" in md
    assert "Go/No-Go entscheidet ein Mensch" in md


def test_vision_verdicts_embedded_and_block(tmp_path: Path) -> None:
    _write(tmp_path, "macos-arm64", _evidence("macos-arm64"))
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    # nicht_erfuellt → Screenshots-Zeile fehlgeschlagen.
    vision = [
        {"screenshot": "a.png", "criterion": "fenster_sichtbar", "verdict": "erfuellt"},
        {"screenshot": "b.png", "criterion": "relief_sichtbar", "verdict": "nicht_erfuellt"},
    ]
    rows = agg.build_matrix(agg.load_evidence(tmp_path), e2e={"status": "bestanden"}, vision=vision)
    row = next(r for r in rows if "Vision" in r.kriterium)
    assert row.status == "fehlgeschlagen"
    assert agg.has_blocking_gaps(rows)


def test_vision_load_from_disk(tmp_path: Path) -> None:
    (tmp_path / "vision-verdikte.json").write_text(
        json.dumps({"verdikte": [{"screenshot": "a.png", "criterion": "x", "verdict": "erfuellt"}]}),
        encoding="utf-8",
    )
    loaded = agg.load_vision(tmp_path)
    assert loaded and loaded[0]["verdict"] == "erfuellt"


def test_main_writes_matrix(tmp_path: Path) -> None:
    _write(tmp_path, "linux-arm64", _evidence("linux-arm64"))
    out = tmp_path / "matrix.md"
    rc = agg.main(["--artifacts-dir", str(tmp_path), "--output", str(out),
                   "--commit-sha", "abc123"])
    assert rc == 0
    assert "Abschlussmatrix" in out.read_text(encoding="utf-8")
