"""Tests für den unabhängigen EufyMake-Pre-Import-Report (#688)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def _load_script(module_name: str, filename: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(module_name, ROOT / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


gen = _load_script("eufymake_fixture_generator_for_inspector", "eufymake_fixture_generator.py")
inspector = _load_script("eufymake_fixture_inspector", "eufymake_fixture_inspector.py")


def _fixtures(tmp_path: Path) -> Path:
    out_dir = tmp_path / "fixtures"
    gen.write_fixtures(gen.generate_all_fixtures(), out_dir)
    return out_dir


def test_inspector_reports_all_generated_fixtures_and_raw_png_properties(
    tmp_path: Path,
) -> None:
    out_dir = _fixtures(tmp_path)
    report = inspector.inspect_fixture_dir(out_dir)

    assert report["ok"] is True
    assert report["errors"] == []
    assert report["summary"] == {
        "expected": len(gen.generate_all_fixtures()),
        "passed": len(gen.generate_all_fixtures()),
        "failed": 0,
        "missing": [],
        "unexpected": [],
    }

    by_name = {entry["filename"]: entry for entry in report["fixtures"]}
    height = by_name["height_wedge_16bit.png"]
    assert height["actual"]["ihdr_bit_depth"] == 16
    assert height["actual"]["ihdr_color_type"] == 0
    assert height["actual"]["chunks"] == ["IHDR", "IDAT", "IEND"]
    assert height["actual"]["phys"] is None

    mm = by_name["mm_typisch_phys.png"]
    assert mm["actual"]["ihdr_bit_depth"] == 8
    assert mm["actual"]["ihdr_color_type"] == 6
    assert mm["actual"]["chunks"] == ["IHDR", "pHYs", "IDAT", "IEND"]
    assert round(mm["actual"]["phys"]["x_dpi"]) == 300


def test_inspector_detects_changed_bytes_even_if_png_remains_valid(tmp_path: Path) -> None:
    out_dir = _fixtures(tmp_path)
    target = out_dir / "height_zero_8bit.png"
    with Image.open(target) as image:
        changed = image.copy()
    changed.putpixel((0, 0), 1)
    changed.save(target, "PNG")

    report = inspector.inspect_fixture_dir(out_dir)
    changed_result = next(
        entry for entry in report["fixtures"] if entry["filename"] == target.name
    )
    assert report["ok"] is False
    assert changed_result["ok"] is False
    assert any("SHA-256" in error for error in changed_result["errors"])


def test_inspector_detects_missing_and_unexpected_files(tmp_path: Path) -> None:
    out_dir = _fixtures(tmp_path)
    (out_dir / "height_zero_8bit.png").unlink()
    (out_dir / "unexpected.png").write_bytes(b"not a png")

    report = inspector.inspect_fixture_dir(out_dir)
    assert report["ok"] is False
    assert report["summary"]["missing"] == ["height_zero_8bit.png"]
    assert report["summary"]["unexpected"] == ["unexpected.png"]


def test_inspector_rejects_incomplete_manifest_entry(tmp_path: Path) -> None:
    out_dir = _fixtures(tmp_path)
    manifest_path = out_dir / gen.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["fixtures"][0]["sha256"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    try:
        inspector.inspect_fixture_dir(out_dir)
    except ValueError as exc:
        assert "Pflichtfelder" in str(exc)
        assert "sha256" in str(exc)
    else:
        raise AssertionError("unvollständiger Manifesteintrag wurde akzeptiert")


def test_inspector_rejects_duplicate_manifest_filename(tmp_path: Path) -> None:
    out_dir = _fixtures(tmp_path)
    manifest_path = out_dir / gen.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["fixtures"][1]["filename"] = manifest["fixtures"][0]["filename"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    try:
        inspector.inspect_fixture_dir(out_dir)
    except ValueError as exc:
        assert "doppelten Dateinamen" in str(exc)
    else:
        raise AssertionError("doppelter Manifestdateiname wurde akzeptiert")


def test_inspector_rejects_stale_manifest_schema(tmp_path: Path) -> None:
    out_dir = _fixtures(tmp_path)
    manifest_path = out_dir / gen.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema"] = 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = inspector.inspect_fixture_dir(out_dir)
    assert report["ok"] is False
    assert any("Manifest-Schema" in error for error in report["errors"])


def test_inspector_reports_decompression_bomb_as_fixture_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    out_dir = _fixtures(tmp_path)
    original_open = inspector.Image.open

    def open_with_bomb(path, *args, **kwargs):  # type: ignore[no-untyped-def]
        if Path(path).name == "height_zero_8bit.png":
            raise inspector.Image.DecompressionBombError("Test-Bild ist zu groß")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(inspector.Image, "open", open_with_bomb)
    report = inspector.inspect_fixture_dir(out_dir)
    failed = next(
        entry for entry in report["fixtures"]
        if entry["filename"] == "height_zero_8bit.png"
    )
    assert report["ok"] is False
    assert failed["errors"] == ["Test-Bild ist zu groß"]


def test_inspector_cli_writes_machine_readable_report(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    out_dir = _fixtures(tmp_path)
    report_path = tmp_path / "reports" / "pre-import.json"

    assert inspector.main([
        "--fixture-dir",
        str(out_dir),
        "--output",
        str(report_path),
    ]) == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["ok"] is True
    assert report["summary"]["failed"] == 0
    assert report["inspector"]["pillow_version"] == inspector.PILLOW_VERSION
    assert "Status: OK" in capsys.readouterr().out


def test_inspector_cli_rejects_wrong_trusted_manifest_hash_with_diagnostics(
    tmp_path: Path,
    capsys,
) -> None:  # type: ignore[no-untyped-def]
    out_dir = _fixtures(tmp_path)
    report_path = tmp_path / "pre-import.json"

    assert inspector.main([
        "--fixture-dir",
        str(out_dir),
        "--output",
        str(report_path),
        "--expected-manifest-sha256",
        "0" * 64,
    ]) == 1
    captured = capsys.readouterr()
    assert "Status: FEHLER" in captured.out
    assert "Manifest-SHA-256" in captured.err
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["ok"] is False
    assert report["manifest"]["expected_sha256"] == "0" * 64
