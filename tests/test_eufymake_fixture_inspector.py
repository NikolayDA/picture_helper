"""Tests für den unabhängigen EufyMake-Pre-Import-Report (#688/#689/#690)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
import zlib
from pathlib import Path

import pytest
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
    assert report["bundle_summary"] == {
        "expected": 1 + len(gen.GLOSS_BUNDLE_DIRNAMES),
        "passed": 1 + len(gen.GLOSS_BUNDLE_DIRNAMES),
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

    mm_xy = by_name["mm_typisch_phys_xy.png"]
    assert round(mm_xy["actual"]["phys"]["x_dpi"]) == 300
    assert round(mm_xy["actual"]["phys"]["y_dpi"]) == 150

    bundle = report["bundles"][0]
    assert bundle["ok"] is True
    bundle_by_name = {entry["filename"]: entry for entry in bundle["files"]}
    assert bundle_by_name["manifest.json"]["actual"]["contract"]["dpi"] == [300.0, 300.0]
    assert round(bundle_by_name["color_motif.png"]["actual"]["phys"]["x_dpi"]) == 150

    mismatch = next(
        item for item in report["bundles"]
        if item["id"] == "gloss_dimension_mismatch"
    )
    mismatch_by_name = {entry["filename"]: entry for entry in mismatch["files"]}
    assert mismatch["ok"] is True
    assert mismatch_by_name["gloss_mask.png"]["actual"]["width"] == 128
    assert mismatch_by_name["gloss_mask.png"]["actual"]["height"] == 256


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


def test_inspector_detects_missing_bundle_file(tmp_path: Path) -> None:
    out_dir = _fixtures(tmp_path)
    (out_dir / gen.EXPORT_BUNDLE_DIRNAME / "gloss_mask.png").unlink()

    report = inspector.inspect_fixture_dir(out_dir)
    bundle = report["bundles"][0]
    assert report["ok"] is False
    assert report["bundle_summary"]["failed"] == 1
    assert bundle["summary"]["missing"] == ["gloss_mask.png"]


def test_inspector_checks_export_manifest_semantics_beyond_catalog_hash(
    tmp_path: Path,
) -> None:
    out_dir = _fixtures(tmp_path)
    export_manifest_path = out_dir / gen.EXPORT_BUNDLE_DIRNAME / "manifest.json"
    export_manifest = json.loads(export_manifest_path.read_text(encoding="utf-8"))
    export_manifest["target"]["dpi"] = [72.0, 72.0]
    changed = json.dumps(export_manifest, indent=2, ensure_ascii=False).encode("utf-8")
    export_manifest_path.write_bytes(changed)

    # SHA/Bytegröße im Katalog bewusst nachziehen: Die unabhängige semantische
    # Prüfung muss den Vertragsbruch trotzdem erkennen.
    fixture_manifest_path = out_dir / gen.MANIFEST_FILENAME
    fixture_manifest = json.loads(fixture_manifest_path.read_text(encoding="utf-8"))
    entry = next(
        item for item in fixture_manifest["bundles"][0]["files"]
        if item["filename"] == "manifest.json"
    )
    entry["sha256"] = hashlib.sha256(changed).hexdigest()
    entry["bytes"] = len(changed)
    fixture_manifest_path.write_text(json.dumps(fixture_manifest), encoding="utf-8")

    report = inspector.inspect_fixture_dir(out_dir)
    manifest_result = next(
        item for item in report["bundles"][0]["files"]
        if item["filename"] == "manifest.json"
    )
    assert report["ok"] is False
    assert manifest_result["ok"] is False
    assert any("Exportmanifest dpi" in error for error in manifest_result["errors"])


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


# ── parse_png: Fehlerpfade (#954-Review, vorher ungetestet) ─────────────


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


_IHDR_1x1_GRAY = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
_IDAT_1x1 = zlib.compress(b"\x00\x00")  # Filterbyte + ein Pixel
_PHYS_300DPI = struct.pack(">IIB", 11811, 11811, 1)


def _png(*chunks: bytes) -> bytes:
    return inspector.PNG_SIGNATURE + b"".join(chunks)


def _valid_png(*, phys: bool = False) -> bytes:
    middle = (_png_chunk(b"pHYs", _PHYS_300DPI),) if phys else ()
    return _png(
        _png_chunk(b"IHDR", _IHDR_1x1_GRAY),
        *middle,
        _png_chunk(b"IDAT", _IDAT_1x1),
        _png_chunk(b"IEND", b""),
    )


def test_parse_png_reads_ihdr_chunks_and_phys_of_a_minimal_file() -> None:
    parsed = inspector.parse_png(_valid_png(phys=True))
    assert parsed["chunks"] == ["IHDR", "pHYs", "IDAT", "IEND"]
    assert parsed["ihdr"]["width"] == 1 and parsed["ihdr"]["bit_depth"] == 8
    assert parsed["phys"]["x_pixels_per_meter"] == 11811 and parsed["phys"]["unit"] == 1
    assert inspector.parse_png(_valid_png())["phys"] is None


def _crc_flipped(data: bytes) -> bytes:
    # Letztes CRC-Byte des IHDR-Chunks kippen: 8 Signatur + 4 Länge + 4 Typ + 13 Daten + 4 CRC
    index = 8 + 4 + 4 + 13 + 3
    return data[:index] + bytes([data[index] ^ 0x01]) + data[index + 1 :]


@pytest.mark.parametrize(
    ("label", "data", "message"),
    [
        ("signature", b"GIF89a" + _valid_png()[6:], "PNG-Signatur"),
        ("crc", _crc_flipped(_valid_png()), "CRC-Abweichung im Chunk IHDR"),
        (
            "order",
            _png(
                _png_chunk(b"pHYs", _PHYS_300DPI),
                _png_chunk(b"IHDR", _IHDR_1x1_GRAY),
                _png_chunk(b"IDAT", _IDAT_1x1),
                _png_chunk(b"IEND", b""),
            ),
            "IHDR muss der erste PNG-Chunk sein",
        ),
        ("truncated", _valid_png()[:-4], "abgeschnittener PNG-Chunk"),
        ("trailing", _valid_png() + b"\x00", "unerwartete Daten hinter dem IEND-Chunk"),
        (
            "duplicate-ihdr",
            _png(
                _png_chunk(b"IHDR", _IHDR_1x1_GRAY),
                _png_chunk(b"IHDR", _IHDR_1x1_GRAY),
                _png_chunk(b"IDAT", _IDAT_1x1),
                _png_chunk(b"IEND", b""),
            ),
            "doppelter IHDR-Chunk",
        ),
        (
            "duplicate-phys",
            _png(
                _png_chunk(b"IHDR", _IHDR_1x1_GRAY),
                _png_chunk(b"pHYs", _PHYS_300DPI),
                _png_chunk(b"pHYs", _PHYS_300DPI),
                _png_chunk(b"IDAT", _IDAT_1x1),
                _png_chunk(b"IEND", b""),
            ),
            "doppelter pHYs-Chunk",
        ),
        # Länge ≠ 13 bzw. ≠ 9 teilt sich die Meldung mit dem Duplikat – beide
        # Zweige werden hier einzeln belegt (#956-Review).
        (
            "ihdr-length",
            _png(
                _png_chunk(b"IHDR", _IHDR_1x1_GRAY + b"\x00"),
                _png_chunk(b"IDAT", _IDAT_1x1),
                _png_chunk(b"IEND", b""),
            ),
            "ungültiger oder doppelter IHDR-Chunk",
        ),
        (
            "phys-length",
            _png(
                _png_chunk(b"IHDR", _IHDR_1x1_GRAY),
                _png_chunk(b"pHYs", _PHYS_300DPI + b"\x00"),
                _png_chunk(b"IDAT", _IDAT_1x1),
                _png_chunk(b"IEND", b""),
            ),
            "ungültiger oder doppelter pHYs-Chunk",
        ),
        (
            # 8 Signatur + 25 IHDR-Chunk = Byte 33
            "non-ascii-type",
            _png(
                _png_chunk(b"IHDR", _IHDR_1x1_GRAY),
                _png_chunk(b"tE\xfft", b"x"),
                _png_chunk(b"IDAT", _IDAT_1x1),
                _png_chunk(b"IEND", b""),
            ),
            "ungültiger PNG-Chunktyp bei Byte 33",
        ),
        (
            "missing-idat",
            _png(_png_chunk(b"IHDR", _IHDR_1x1_GRAY), _png_chunk(b"IEND", b"")),
            "IDAT-Chunk fehlt",
        ),
        (
            "missing-iend",
            _png(_png_chunk(b"IHDR", _IHDR_1x1_GRAY), _png_chunk(b"IDAT", _IDAT_1x1)),
            "IEND-Chunk fehlt",
        ),
        (
            "iend-with-data",
            _png(
                _png_chunk(b"IHDR", _IHDR_1x1_GRAY),
                _png_chunk(b"IDAT", _IDAT_1x1),
                _png_chunk(b"IEND", b"x"),
            ),
            "IEND-Chunk enthält unerwartete Daten",
        ),
    ],
)
def test_parse_png_rejects_structural_defects(label: str, data: bytes, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        inspector.parse_png(data)


def test_inspector_reports_a_truncated_fixture_per_file_instead_of_raising(tmp_path: Path) -> None:
    """Ein defekter Transfer wird als Dateibefund protokolliert, nicht als Traceback."""
    out_dir = _fixtures(tmp_path)
    target = out_dir / "height_zero_8bit.png"
    target.write_bytes(target.read_bytes()[:-4])

    report = inspector.inspect_fixture_dir(out_dir)
    result = next(entry for entry in report["fixtures"] if entry["filename"] == target.name)
    assert report["ok"] is False and result["ok"] is False
    assert any("abgeschnitten" in error for error in result["errors"]), result["errors"]
