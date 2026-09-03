#!/usr/bin/env python3
"""EufyMake-Hardware-Fixtures unmittelbar vor dem Studio-Import prüfen.

Der Generator belegt, wie die Testdateien entstehen. Dieses Skript liest die
bereits übertragenen Dateien dagegen unabhängig neu ein: SHA-256, Bytegröße,
Pillow-Lesbarkeit/-Version, IHDR-Felder, PNG-Chunkfolge, ``pHYs`` und CRC
jedes Chunks. Der Pillow-Modus ist nur diagnostisch; Bittiefe und Farbtyp
werden versionsunabhängig aus IHDR validiert. Der JSON-Report ist der
maschinenlesbare Pre-Import-Nachweis für #688–#690.

Aufruf am Zielrechner, nachdem die Fixtures dorthin kopiert wurden::

    python scripts/eufymake_fixture_inspector.py \
      --fixture-dir tests/fixtures/eufymake_hardware \
      --expected-manifest-sha256 <SHA-256-aus-der-Testdokumentation> \
      --output eufymake-pre-import-report.json

Exitcode 0 bedeutet, dass Dateiliste und alle geprüften Eigenschaften mit dem
Manifest übereinstimmen. Abweichungen liefern Exitcode 1 und werden im Report
je Datei protokolliert. Lässt sich die Prüfung gar nicht starten (Verzeichnis
oder Manifest fehlt bzw. ist kein lesbares JSON), endet das Skript mit
Exitcode 2 **ohne** Report – ein fehlender Report ist damit selbst ein Befund,
kein Erfolg. Fremddateien im Ordner (etwa ``.DS_Store``) sind ein Fehler.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

from PIL import Image
from PIL import __version__ as PILLOW_VERSION

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "eufymake_hardware"
MANIFEST_FILENAME = "fixtures_manifest.json"
BUNDLE_MANIFEST_FILENAME = "manifest.json"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXPECTED_MANIFEST_SCHEMA = 5

_PNG_COLOR_TYPE_BY_MODE = {
    "L": 0,
    "I;16": 0,
    "RGB": 2,
    "RGBA": 6,
}
_ALLOWED_CHUNKS = {"IHDR", "IDAT", "IEND", "pHYs"}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_png(data: bytes) -> dict[str, Any]:
    """PNG-Struktur ohne Generatorcode/PIL-Metadatenheuristik auslesen."""
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("PNG-Signatur fehlt oder ist beschädigt")

    offset = len(PNG_SIGNATURE)
    chunks: list[str] = []
    ihdr: dict[str, int] | None = None
    phys: dict[str, float | int] | None = None
    saw_iend = False

    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError(f"abgeschnittener PNG-Chunk bei Byte {offset}")
        length = struct.unpack_from(">I", data, offset)[0]
        chunk_start = offset + 8
        chunk_end = chunk_start + length
        crc_end = chunk_end + 4
        if crc_end > len(data):
            raise ValueError(f"abgeschnittener PNG-Chunk bei Byte {offset}")

        chunk_type_bytes = data[offset + 4 : offset + 8]
        try:
            chunk_type = chunk_type_bytes.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError(f"ungültiger PNG-Chunktyp bei Byte {offset}") from exc
        chunk_data = data[chunk_start:chunk_end]
        expected_crc = struct.unpack_from(">I", data, chunk_end)[0]
        actual_crc = zlib.crc32(chunk_type_bytes + chunk_data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError(f"CRC-Abweichung im Chunk {chunk_type}")

        chunks.append(chunk_type)
        if chunk_type == "IHDR":
            if ihdr is not None or length != 13:
                raise ValueError("ungültiger oder doppelter IHDR-Chunk")
            width, height, bit_depth, color_type, compression, filtering, interlace = (
                struct.unpack(">IIBBBBB", chunk_data)
            )
            ihdr = {
                "width": width,
                "height": height,
                "bit_depth": bit_depth,
                "color_type": color_type,
                "compression": compression,
                "filter": filtering,
                "interlace": interlace,
            }
        elif chunk_type == "pHYs":
            if phys is not None or length != 9:
                raise ValueError("ungültiger oder doppelter pHYs-Chunk")
            x_ppm, y_ppm, unit = struct.unpack(">IIB", chunk_data)
            phys = {
                "x_pixels_per_meter": x_ppm,
                "y_pixels_per_meter": y_ppm,
                "unit": unit,
                "x_dpi": round(x_ppm * 0.0254, 6) if unit == 1 else 0.0,
                "y_dpi": round(y_ppm * 0.0254, 6) if unit == 1 else 0.0,
            }
        elif chunk_type == "IEND":
            if length != 0:
                raise ValueError("IEND-Chunk enthält unerwartete Daten")
            saw_iend = True
            offset = crc_end
            break
        offset = crc_end

    if not chunks or chunks[0] != "IHDR" or ihdr is None:
        raise ValueError("IHDR muss der erste PNG-Chunk sein")
    if "IDAT" not in chunks:
        raise ValueError("IDAT-Chunk fehlt")
    if not saw_iend or chunks[-1] != "IEND":
        raise ValueError("IEND-Chunk fehlt")
    if offset != len(data):
        raise ValueError("unerwartete Daten hinter dem IEND-Chunk")

    return {"ihdr": ihdr, "chunks": chunks, "phys": phys}


def _inspect_entry(path: Path, expected: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    data = path.read_bytes()
    png = parse_png(data)
    ihdr = png["ihdr"]

    with Image.open(path) as image:
        image.load()
        pil_mode = image.mode
        pil_size = [image.width, image.height]

    actual = {
        "sha256": _sha256(data),
        "bytes": len(data),
        "pil_mode": pil_mode,
        "width": ihdr["width"],
        "height": ihdr["height"],
        "ihdr_bit_depth": ihdr["bit_depth"],
        "ihdr_color_type": ihdr["color_type"],
        "chunks": png["chunks"],
        "phys": png["phys"],
    }

    comparisons = (
        (actual["sha256"], expected["sha256"], "SHA-256"),
        (actual["bytes"], expected["bytes"], "Bytegröße"),
        (pil_size, [expected["width"], expected["height"]], "Bildmaß"),
        (ihdr["bit_depth"], expected["bit_depth"], "IHDR-Bittiefe"),
    )
    for got, wanted, label in comparisons:
        if got != wanted:
            errors.append(f"{label}: erwartet {wanted!r}, tatsächlich {got!r}")

    expected_color_type = _PNG_COLOR_TYPE_BY_MODE.get(expected["png_mode"])
    if expected_color_type is None:
        errors.append(f"Manifest enthält unbekannten PNG-Modus {expected['png_mode']!r}")
    elif ihdr["color_type"] != expected_color_type:
        errors.append(
            "IHDR-Farbtyp: erwartet "
            f"{expected_color_type}, tatsächlich {ihdr['color_type']}"
        )

    unexpected_chunks = sorted(set(png["chunks"]) - _ALLOWED_CHUNKS)
    if unexpected_chunks:
        errors.append(f"unerwartete PNG-Chunks: {unexpected_chunks}")

    expected_dpi = expected.get("params", {}).get("phys_dpi")
    if expected_dpi is None and png["phys"] is not None:
        errors.append("pHYs vorhanden, obwohl das Manifest keine physische DPI erwartet")
    elif expected_dpi is not None:
        if isinstance(expected_dpi, (int, float)):
            expected_x_dpi = expected_y_dpi = float(expected_dpi)
        elif (
            isinstance(expected_dpi, list)
            and len(expected_dpi) == 2
            and all(isinstance(value, (int, float)) for value in expected_dpi)
        ):
            expected_x_dpi, expected_y_dpi = map(float, expected_dpi)
        else:
            raise ValueError(
                "params.phys_dpi muss eine Zahl, ein Zahlenpaar oder null sein"
            )
        if png["phys"] is None:
            errors.append(f"pHYs fehlt; erwartet werden ungefähr {expected_dpi} dpi")
        else:
            phys = png["phys"]
            if phys["unit"] != 1:
                errors.append("pHYs verwendet keine Meter-Einheit")
            for axis, wanted in (
                ("x_dpi", expected_x_dpi),
                ("y_dpi", expected_y_dpi),
            ):
                if abs(float(phys[axis]) - wanted) > 0.02:
                    errors.append(
                        f"pHYs {axis}: erwartet ungefähr {wanted}, "
                        f"tatsächlich {phys[axis]}"
                    )

    return {
        "filename": expected["filename"],
        "role": expected["role"],
        "pattern": expected["pattern"],
        "expected": {
            "sha256": expected["sha256"],
            "bytes": expected["bytes"],
            "png_mode": expected["png_mode"],
            "bit_depth": expected["bit_depth"],
            "width": expected["width"],
            "height": expected["height"],
            "phys_dpi": expected_dpi,
        },
        "actual": actual,
        "ok": not errors,
        "errors": errors,
    }


def _inspect_export_manifest(
    path: Path,
    expected: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    """Prüft das echte BgRemover-Manifest unabhängig vom Generator semantisch."""
    errors: list[str] = []
    data = path.read_bytes()
    actual_manifest = json.loads(data.decode("utf-8"))
    if not isinstance(actual_manifest, dict):
        raise ValueError("Exportmanifest muss ein JSON-Objekt sein")
    target = actual_manifest.get("target")
    if not isinstance(target, dict):
        errors.append("Exportmanifest enthält kein gültiges target-Objekt")
        target = {}
    assets = actual_manifest.get("assets")
    if not isinstance(assets, list):
        errors.append("Exportmanifest enthält keine gültige assets-Liste")
        actual_asset_names = None
    elif not all(isinstance(asset, dict) for asset in assets):
        errors.append("Exportmanifest assets enthält einen ungültigen Eintrag")
        actual_asset_names = None
    else:
        actual_asset_names = [asset.get("filename") for asset in assets]
    actual_contract = {
        "profile": actual_manifest.get("profile"),
        "profile_version": actual_manifest.get("profile_version"),
        "kind": actual_manifest.get("kind"),
        "pixel_size": target.get("pixel_size"),
        "bit_depth": target.get("bit_depth"),
        "physical_size_mm": target.get("physical_size_mm"),
        "dpi": target.get("dpi"),
        "assets": actual_asset_names,
    }
    for key, wanted in contract.items():
        got = actual_contract.get(key)
        if got != wanted:
            errors.append(
                f"Exportmanifest {key}: erwartet {wanted!r}, tatsächlich {got!r}"
            )
    actual = {
        "sha256": _sha256(data),
        "bytes": len(data),
        "contract": actual_contract,
    }
    if actual["sha256"] != expected["sha256"]:
        errors.append(
            f"SHA-256: erwartet {expected['sha256']!r}, "
            f"tatsächlich {actual['sha256']!r}"
        )
    if actual["bytes"] != expected["bytes"]:
        errors.append(
            f"Bytegröße: erwartet {expected['bytes']!r}, "
            f"tatsächlich {actual['bytes']!r}"
        )
    return {
        "filename": expected["filename"],
        "media_type": expected["media_type"],
        "expected": {
            "sha256": expected["sha256"],
            "bytes": expected["bytes"],
            "contract": contract,
        },
        "actual": actual,
        "ok": not errors,
        "errors": errors,
    }


def validate_bundles(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate the catalog structure shared by inspection and preservation."""
    bundles = manifest.get("bundles")
    if not isinstance(bundles, list):
        raise ValueError("Manifestfeld 'bundles' muss eine Liste sein")
    required_bundle_fields = {
        "id",
        "directory",
        "purpose",
        "generated_via",
        "manifest_contract",
        "file_count",
        "files",
    }
    required_contract_fields = {
        "profile",
        "profile_version",
        "kind",
        "pixel_size",
        "bit_depth",
        "physical_size_mm",
        "dpi",
        "assets",
    }
    seen_directories: set[str] = set()
    for bundle_index, bundle in enumerate(bundles):
        if not isinstance(bundle, dict):
            raise ValueError(f"Bundle {bundle_index} muss ein Objekt sein")
        missing = sorted(required_bundle_fields - bundle.keys())
        if missing:
            raise ValueError(f"Bundle {bundle_index} enthält nicht alle Pflichtfelder: {missing}")
        for text_field in ("id", "purpose", "generated_via"):
            if not isinstance(bundle[text_field], str) or not bundle[text_field]:
                raise ValueError(
                    f"Bundle {bundle_index}: {text_field} muss nichtleer sein"
                )
        if not isinstance(bundle["manifest_contract"], dict):
            raise ValueError(f"Bundle {bundle_index}: manifest_contract muss ein Objekt sein")
        contract = bundle["manifest_contract"]
        missing_contract_fields = sorted(required_contract_fields - contract.keys())
        if missing_contract_fields:
            raise ValueError(
                f"Bundle {bundle_index}: manifest_contract enthält nicht alle "
                f"Pflichtfelder: {missing_contract_fields}"
            )
        directory = bundle["directory"]
        if (
            not isinstance(directory, str)
            or not directory
            or Path(directory).name != directory
            or directory in {".", ".."}
        ):
            raise ValueError(f"Bundle {bundle_index} enthält keinen gültigen Verzeichnisnamen")
        if directory in seen_directories:
            raise ValueError(f"Manifest enthält doppeltes Bundle-Verzeichnis {directory!r}")
        seen_directories.add(directory)
        files = bundle["files"]
        if not isinstance(files, list):
            raise ValueError(f"Bundle {bundle_index}: 'files' muss eine Liste sein")
        if bundle["file_count"] != len(files):
            raise ValueError(f"Bundle {bundle_index}: file_count stimmt nicht")
        seen_files: set[str] = set()
        png_files: list[str] = []
        manifest_files: list[str] = []
        for file_index, entry in enumerate(files):
            if not isinstance(entry, dict):
                raise ValueError(
                    f"Bundle {bundle_index}, Datei {file_index} muss ein Objekt sein"
                )
            basic_fields = {"filename", "media_type", "sha256", "bytes"}
            missing = sorted(basic_fields - entry.keys())
            if missing:
                raise ValueError(
                    f"Bundle {bundle_index}, Datei {file_index} enthält nicht alle "
                    f"Pflichtfelder: {missing}"
                )
            filename = entry["filename"]
            if (
                not isinstance(filename, str)
                or not filename
                or Path(filename).name != filename
            ):
                raise ValueError(
                    f"Bundle {bundle_index}, Datei {file_index} enthält einen Pfad"
                )
            if filename in seen_files:
                raise ValueError(
                    f"Bundle {bundle_index} enthält doppelten Dateinamen {filename!r}"
                )
            seen_files.add(filename)
            if entry["media_type"] == "image/png":
                png_files.append(filename)
                png_fields = {
                    "role", "pattern", "png_mode", "bit_depth", "width", "height",
                }
                missing = sorted(png_fields - entry.keys())
                if missing:
                    raise ValueError(
                        f"Bundle {bundle_index}, PNG {file_index} enthält nicht alle "
                        f"Pflichtfelder: {missing}"
                    )
            elif entry["media_type"] == "application/json":
                manifest_files.append(filename)
            else:
                raise ValueError(
                    f"Bundle {bundle_index}, Datei {file_index}: unbekannter Medientyp"
                )
        if manifest_files != [BUNDLE_MANIFEST_FILENAME]:
            raise ValueError(
                f"Bundle {bundle_index}: genau {BUNDLE_MANIFEST_FILENAME!r} muss "
                "das Exportmanifest sein"
            )
        assets = contract["assets"]
        if (
            not isinstance(assets, list)
            or not all(isinstance(asset, str) for asset in assets)
            or len(set(assets)) != len(assets)
            or set(assets) != set(png_files)
        ):
            raise ValueError(
                f"Bundle {bundle_index}: manifest_contract.assets stimmt nicht "
                "mit den PNG-Dateien überein"
            )
    return bundles


def inspect_bundle(fixture_dir: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    """Inspect one structurally validated bundle without following symlinks."""
    bundle_dir = fixture_dir / bundle["directory"]
    errors: list[str] = []
    expected_names = {entry["filename"] for entry in bundle["files"]}
    bundle_dir_valid = bundle_dir.is_dir() and not bundle_dir.is_symlink()
    actual_entries = list(bundle_dir.iterdir()) if bundle_dir_valid else []
    actual_file_names = {
        path.name
        for path in actual_entries
        if path.is_file() and not path.is_symlink()
    }
    non_file_names = {
        path.name
        for path in actual_entries
        if not path.is_file() or path.is_symlink()
    }
    missing = sorted(expected_names - actual_file_names)
    unexpected = sorted((actual_file_names - expected_names) | non_file_names)
    if bundle_dir.is_symlink():
        errors.append("Bundle-Verzeichnis darf kein Symlink sein")
    elif not bundle_dir.is_dir():
        errors.append("Bundle-Verzeichnis fehlt")
    if missing:
        errors.append(f"fehlende Bundle-Dateien: {missing}")
    if unexpected:
        errors.append(f"unerwartete Bundle-Dateien: {unexpected}")

    results: list[dict[str, Any]] = []
    for entry in sorted(bundle["files"], key=lambda item: item["filename"]):
        path = bundle_dir / entry["filename"]
        if not bundle_dir_valid or not path.is_file() or path.is_symlink():
            results.append({
                "filename": entry["filename"],
                "media_type": entry["media_type"],
                "ok": False,
                "errors": ["Datei fehlt"],
            })
            continue
        try:
            if entry["media_type"] == "image/png":
                result = _inspect_entry(path, entry)
                result["media_type"] = entry["media_type"]
            else:
                result = _inspect_export_manifest(
                    path, entry, bundle["manifest_contract"],
                )
            results.append(result)
        except (
            OSError,
            ValueError,
            json.JSONDecodeError,
            struct.error,
            Image.DecompressionBombError,
        ) as exc:
            results.append({
                "filename": entry["filename"],
                "media_type": entry["media_type"],
                "ok": False,
                "errors": [str(exc)],
            })
    failed = sum(not result["ok"] for result in results)
    return {
        "id": bundle["id"],
        "directory": bundle["directory"],
        "generated_via": bundle["generated_via"],
        "ok": not errors and failed == 0,
        "errors": errors,
        "summary": {
            "expected": len(bundle["files"]),
            "passed": len(results) - failed,
            "failed": failed,
            "missing": missing,
            "unexpected": unexpected,
        },
        "files": results,
    }


def inspect_fixture_dir(
    fixture_dir: Path,
    *,
    expected_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    """Manifest und alle referenzierten PNGs prüfen; niemals still ergänzen."""
    fixture_dir = fixture_dir.resolve()
    manifest_path = fixture_dir / MANIFEST_FILENAME
    manifest_data = manifest_path.read_bytes()
    manifest_sha256 = _sha256(manifest_data)
    manifest = json.loads(manifest_data.decode("utf-8"))
    entries = manifest.get("fixtures")
    if not isinstance(entries, list):
        raise ValueError("Manifestfeld 'fixtures' muss eine Liste sein")
    bundles = validate_bundles(manifest)

    required_fields = {
        "filename",
        "role",
        "pattern",
        "sha256",
        "bytes",
        "png_mode",
        "bit_depth",
        "width",
        "height",
    }
    seen_filenames: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Manifestzeile {index} muss ein Objekt sein")
        missing_fields = sorted(required_fields - entry.keys())
        if missing_fields:
            raise ValueError(
                f"Manifestzeile {index} enthält nicht alle Pflichtfelder: "
                f"{missing_fields}"
            )
        if not isinstance(entry["filename"], str) or not entry["filename"]:
            raise ValueError(f"Manifestzeile {index} enthält keinen gültigen Dateinamen")
        filename = entry["filename"]
        if Path(filename).name != filename:
            raise ValueError(
                f"Manifestzeile {index} enthält einen Pfad statt eines Dateinamens"
            )
        if filename in seen_filenames:
            raise ValueError(f"Manifest enthält doppelten Dateinamen {filename!r}")
        seen_filenames.add(filename)

    global_errors: list[str] = []
    if manifest.get("schema") != EXPECTED_MANIFEST_SCHEMA:
        global_errors.append(
            "Manifest-Schema: erwartet "
            f"{EXPECTED_MANIFEST_SCHEMA}, tatsächlich {manifest.get('schema')!r}"
        )
    if (
        expected_manifest_sha256 is not None
        and manifest_sha256 != expected_manifest_sha256
    ):
        global_errors.append(
            "Manifest-SHA-256: erwartet "
            f"{expected_manifest_sha256}, tatsächlich {manifest_sha256}"
        )
    if manifest.get("fixture_count") != len(entries):
        global_errors.append(
            "fixture_count stimmt nicht mit der Anzahl der Manifestzeilen überein"
        )
    if manifest.get("bundle_count") != len(bundles):
        global_errors.append(
            "bundle_count stimmt nicht mit der Anzahl der Bundles überein"
        )

    expected_names = {entry["filename"] for entry in entries}
    actual_names = {path.name for path in fixture_dir.iterdir() if path.is_file()}
    actual_fixture_names = actual_names - {MANIFEST_FILENAME}
    missing = sorted(expected_names - actual_fixture_names)
    unexpected = sorted(actual_fixture_names - expected_names)
    if missing:
        global_errors.append(f"fehlende Fixture-Dateien: {missing}")
    if unexpected:
        global_errors.append(f"unerwartete Dateien im Fixture-Verzeichnis: {unexpected}")
    expected_directories = {bundle["directory"] for bundle in bundles}
    actual_directories = {path.name for path in fixture_dir.iterdir() if path.is_dir()}
    missing_directories = sorted(expected_directories - actual_directories)
    unexpected_directories = sorted(actual_directories - expected_directories)
    if missing_directories:
        global_errors.append(f"fehlende Bundle-Verzeichnisse: {missing_directories}")
    if unexpected_directories:
        global_errors.append(f"unerwartete Verzeichnisse: {unexpected_directories}")

    results: list[dict[str, Any]] = []
    for entry in sorted(entries, key=lambda item: item["filename"]):
        path = fixture_dir / entry["filename"]
        if not path.is_file():
            results.append({
                "filename": entry["filename"],
                "role": entry.get("role"),
                "pattern": entry.get("pattern"),
                "ok": False,
                "errors": ["Datei fehlt"],
            })
            continue
        try:
            results.append(_inspect_entry(path, entry))
        except (OSError, ValueError, struct.error, Image.DecompressionBombError) as exc:
            results.append({
                "filename": entry["filename"],
                "role": entry.get("role"),
                "pattern": entry.get("pattern"),
                "ok": False,
                "errors": [str(exc)],
            })

    failed = sum(not result["ok"] for result in results)
    bundle_results = [inspect_bundle(fixture_dir, bundle) for bundle in bundles]
    failed_bundles = sum(not bundle["ok"] for bundle in bundle_results)
    return {
        "schema": 1,
        "inspector": {"pillow_version": PILLOW_VERSION},
        "fixture_dir": str(fixture_dir),
        "manifest": {
            "filename": MANIFEST_FILENAME,
            "sha256": manifest_sha256,
            "expected_sha256": expected_manifest_sha256,
            "schema": manifest.get("schema"),
            "declared_fixture_count": manifest.get("fixture_count"),
            "declared_bundle_count": manifest.get("bundle_count"),
        },
        "summary": {
            "expected": len(entries),
            "passed": len(results) - failed,
            "failed": failed,
            "missing": missing,
            "unexpected": unexpected,
        },
        "bundle_summary": {
            "expected": len(bundle_results),
            "passed": len(bundle_results) - failed_bundles,
            "failed": failed_bundles,
            "missing": missing_directories,
            "unexpected": unexpected_directories,
        },
        "ok": not global_errors and failed == 0 and failed_bundles == 0,
        "errors": global_errors,
        "fixtures": results,
        "bundles": bundle_results,
    }


def _sha256_argument(value: str) -> str:
    normalized = value.lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise argparse.ArgumentTypeError("erwartet werden genau 64 hexadezimale Zeichen")
    return normalized


def _print_failure_summary(report: dict[str, Any]) -> None:
    for error in report["errors"]:
        print(f"FEHLER: {error}", file=sys.stderr)
    for fixture in report["fixtures"]:
        if not fixture["ok"]:
            details = "; ".join(fixture["errors"])
            print(f"FEHLER: {fixture['filename']}: {details}", file=sys.stderr)
    for bundle in report["bundles"]:
        for error in bundle["errors"]:
            print(f"FEHLER: {bundle['directory']}: {error}", file=sys.stderr)
        for entry in bundle["files"]:
            if not entry["ok"]:
                details = "; ".join(entry["errors"])
                print(
                    f"FEHLER: {bundle['directory']}/{entry['filename']}: {details}",
                    file=sys.stderr,
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument(
        "--output",
        type=Path,
        help="JSON-Report schreiben; ohne Angabe wird er auf stdout ausgegeben.",
    )
    parser.add_argument(
        "--expected-manifest-sha256",
        type=_sha256_argument,
        help="Vertrauenswürdiger SHA-256 des erwarteten Fixture-Manifests.",
    )
    args = parser.parse_args(argv)

    try:
        report = inspect_fixture_dir(
            args.fixture_dir,
            expected_manifest_sha256=args.expected_manifest_sha256,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Fixture-Prüfung konnte nicht gestartet werden: {exc}\n")

    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        status = "OK" if report["ok"] else "FEHLER"
        print(
            f"Status: {status}; "
            f"{report['summary']['passed']}/{report['summary']['expected']} Fixtures geprüft; "
            f"{report['bundle_summary']['passed']}/"
            f"{report['bundle_summary']['expected']} Exportpakete geprüft; "
            f"Report: {args.output}",
        )
        if not report["ok"]:
            _print_failure_summary(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
