"""Tests für ``scripts/eufymake_fixture_generator.py`` (#687, Epic #681).

Prüft Determinismus (zweimal erzeugen → bitidentische Dateien inkl. Manifest),
dass jede Manifest-Zeile die tatsächlichen Dateieigenschaften (Bittiefe,
PNG-Modus, Maße, SHA-256) korrekt beschreibt, sowie dass die eingecheckten
Fixtures unter ``tests/fixtures/eufymake_hardware/`` nicht vom aktuellen
Generator abweichen (keine stille Drift zwischen Skript und Artefakt).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "eufymake_fixture_generator", ROOT / "scripts" / "eufymake_fixture_generator.py"
)
assert _SPEC is not None and _SPEC.loader is not None
gen = importlib.util.module_from_spec(_SPEC)
sys.modules["eufymake_fixture_generator"] = gen
_SPEC.loader.exec_module(gen)

CHECKED_IN_DIR = ROOT / "tests" / "fixtures" / "eufymake_hardware"


def _write(tmp_path: Path, name: str) -> Path:
    out_dir = tmp_path / name
    gen.write_fixtures(gen.generate_all_fixtures(), out_dir)
    return out_dir


# ── Determinismus ────────────────────────────────────────────────────────

def test_generation_is_deterministic(tmp_path: Path) -> None:
    first = _write(tmp_path, "run1")
    second = _write(tmp_path, "run2")

    first_files = sorted(
        p.relative_to(first) for p in first.rglob("*") if p.is_file()
    )
    second_files = sorted(
        p.relative_to(second) for p in second.rglob("*") if p.is_file()
    )
    assert first_files == second_files
    assert len(first_files) > 0

    for name in first_files:
        assert (first / name).read_bytes() == (second / name).read_bytes(), name


def test_manifest_written_twice_is_byte_identical(tmp_path: Path) -> None:
    first = _write(tmp_path, "run1")
    second = _write(tmp_path, "run2")
    manifest_a = (first / gen.MANIFEST_FILENAME).read_text(encoding="utf-8")
    manifest_b = (second / gen.MANIFEST_FILENAME).read_text(encoding="utf-8")
    assert manifest_a == manifest_b


# ── Manifest ↔ tatsächliche Dateieigenschaften ──────────────────────────

def test_manifest_entries_match_actual_file_properties(tmp_path: Path) -> None:
    out_dir = _write(tmp_path, "run")
    manifest = json.loads((out_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8"))

    assert manifest["schema"] == gen.SCHEMA_VERSION
    assert manifest["fixture_count"] == len(manifest["fixtures"])
    on_disk = {p.name for p in out_dir.iterdir() if p.is_file()} - {gen.MANIFEST_FILENAME}
    assert on_disk == {entry["filename"] for entry in manifest["fixtures"]}
    assert manifest["bundle_count"] == len(manifest["bundles"]) == 1

    for entry in manifest["fixtures"]:
        path = out_dir / entry["filename"]
        data = path.read_bytes()
        assert len(data) == entry["bytes"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]

        with Image.open(path) as img:
            assert img.mode == entry["png_mode"], entry["filename"]
            assert img.width == entry["width"], entry["filename"]
            assert img.height == entry["height"], entry["filename"]
            expected_bits = 16 if img.mode == "I;16" else 8
            assert entry["bit_depth"] == expected_bits, entry["filename"]


def test_fixture_roles_and_counts() -> None:
    specs = gen.generate_all_fixtures()
    by_role: dict[str, int] = {}
    for spec in specs:
        by_role[spec.role] = by_role.get(spec.role, 0) + 1

    # 8-Bit + 16-Bit je Muster, plus die I-04-Pixelmaß- und I-12-Seitenverhältnis-
    # Variante (kein eigenes Muster in _HEIGHT_PATTERNS, siehe die dedizierten
    # Tests unten).
    assert by_role["height_map"] == len(gen._HEIGHT_PATTERNS) * 2 + 3
    # mm/DPI no_phys/phys/conflict plus X/Y-DPI, dimensionsgleiche Referenz
    # und Alpha/Coverage-Kontrolle.
    assert by_role["color_motif"] == len(gen.MM_DPI_COMBOS) * 3 + 3
    assert by_role["gloss_mask"] == len(gen._GLOSS_PATTERNS) + 1

    filenames = [spec.filename for spec in specs]
    assert len(filenames) == len(set(filenames)), "Dateinamen müssen eindeutig sein"


def test_height_fixtures_cover_8_and_16_bit(tmp_path: Path) -> None:
    out_dir = _write(tmp_path, "run")
    manifest = json.loads((out_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    variant_patterns = {
        gen.PIXEL_SIZE_VARIANT_PATTERN,
        gen.ASPECT_RATIO_VARIANT_PATTERN,
        gen.REGISTRATION_PATTERN,
    }
    height_entries = [
        e for e in manifest["fixtures"]
        if e["role"] == "height_map" and e["pattern"] not in variant_patterns
    ]
    patterns = {e["pattern"] for e in height_entries}
    assert patterns == {name for name, _ in gen._HEIGHT_PATTERNS}
    for pattern in patterns:
        depths = {e["bit_depth"] for e in height_entries if e["pattern"] == pattern}
        assert depths == {8, 16}, pattern


# ── Pixelmaß-Variante (I-04) ─────────────────────────────────────────────

def test_pixel_size_variant_fixture_is_precision_preserving_half_size(
    tmp_path: Path,
) -> None:
    """I-04: 128×128-Kopie von height_wedge_16bit.png, kein neu erzeugtes Muster."""
    out_dir = _write(tmp_path, "run")
    manifest = json.loads((out_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    entry = next(
        e for e in manifest["fixtures"] if e["filename"] == "height_wedge_16bit_half.png"
    )
    assert entry["role"] == "height_map"
    assert entry["pattern"] == gen.PIXEL_SIZE_VARIANT_PATTERN
    assert entry["bit_depth"] == 16
    assert entry["png_mode"] == "I;16"
    assert (entry["width"], entry["height"]) == gen.PIXEL_SIZE_VARIANT_SIZE
    # Gleiches Seitenverhältnis wie die 256×256-Referenz (beide Kanten halbiert).
    source_w, source_h = entry["params"]["source_size_px"]
    assert entry["width"] / entry["height"] == source_w / source_h
    assert entry["params"]["source_file"] == gen.PIXEL_SIZE_VARIANT_SOURCE
    # Konstante muss zum tatsächlich erzeugten Dateinamen des Referenzmusters passen.
    assert f"height_{entry['params']['source_pattern']}_16bit.png" == gen.PIXEL_SIZE_VARIANT_SOURCE

    from bgremover.height_map import HEIGHT_MAX_16BIT, HeightField, resize_height_field

    width, height = gen.HEIGHT_SIZE
    pattern = gen._pattern_wedge(width, height)
    values = np.rint(pattern * HEIGHT_MAX_16BIT).astype(np.uint16)
    coverage = np.full(values.shape, 255, dtype=np.uint8)
    expected = resize_height_field(
        HeightField(values, coverage, HEIGHT_MAX_16BIT), *gen.PIXEL_SIZE_VARIANT_SIZE
    )

    with Image.open(out_dir / entry["filename"]) as img:
        actual = np.array(img, dtype=np.uint16)
    assert np.array_equal(actual, expected.values)


# ── Seitenverhältnis-Variante (I-12, H-03) ───────────────────────────────

def test_aspect_ratio_variant_fixture_has_genuinely_different_ratio(
    tmp_path: Path,
) -> None:
    """I-12: echtes anderes Seitenverhältnis, kein Resize eines quadratischen Musters."""
    out_dir = _write(tmp_path, "run")
    manifest = json.loads((out_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    entry = next(
        e for e in manifest["fixtures"] if e["filename"] == "height_wedge_16bit_aspect.png"
    )
    assert entry["role"] == "height_map"
    assert entry["pattern"] == gen.ASPECT_RATIO_VARIANT_PATTERN
    assert entry["bit_depth"] == 16
    assert entry["png_mode"] == "I;16"
    assert (entry["width"], entry["height"]) == gen.ASPECT_RATIO_VARIANT_SIZE

    # Muss sich vom Seitenverhältnis der quadratischen Referenz unterscheiden
    # (sonst wäre es keine H-03-Variante, sondern nur eine weitere Pixelmaß-Kopie).
    ref_w, ref_h = entry["params"]["reference_size_px"]
    assert entry["width"] / entry["height"] != ref_w / ref_h

    expected = np.rint(
        gen._pattern_wedge(*gen.ASPECT_RATIO_VARIANT_SIZE) * gen.HEIGHT_MAX_16BIT
    ).astype(np.uint16)
    with Image.open(out_dir / entry["filename"]) as img:
        actual = np.array(img, dtype=np.uint16)
    assert np.array_equal(actual, expected)


# ── Dimensionsgleiche COLOR/HEIGHT- und Alpha/Coverage-Kontrollen ────────

def test_color_height_reference_matches_canonical_height_dimensions(tmp_path: Path) -> None:
    """I-02 und die I-08-Registriermap nutzen dieselben Pixelmaße."""
    out_dir = _write(tmp_path, "run")
    manifest = json.loads((out_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    by_name = {entry["filename"]: entry for entry in manifest["fixtures"]}

    color = by_name["color_height_reference.png"]
    height = by_name["height_wedge_16bit.png"]
    assert color["role"] == "color_motif"
    assert color["png_mode"] == "RGBA"
    assert (color["width"], color["height"]) == (height["width"], height["height"])
    assert color["params"]["alpha_levels"] == [255]
    assert "height_wedge_16bit.png" in color["params"]["paired_height_files"]
    assert "height_registration_16bit.png" in color["params"]["paired_height_files"]

    with Image.open(out_dir / color["filename"]) as image:
        alpha = np.array(image.getchannel("A"), dtype=np.uint8)
    assert set(np.unique(alpha).tolist()) == {255}


def test_alpha_coverage_fixture_has_exact_fields_and_nonzero_height_pair(
    tmp_path: Path,
) -> None:
    """I-13 variiert nur Coverage; die gekoppelte HEIGHT-Fläche bleibt > 0."""
    out_dir = _write(tmp_path, "run")
    manifest = json.loads((out_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    by_name = {entry["filename"]: entry for entry in manifest["fixtures"]}

    color = by_name["color_alpha_coverage.png"]
    height = by_name[color["params"]["paired_height_file"]]
    assert color["role"] == "color_motif"
    assert color["pattern"] == "alpha_coverage_fields"
    assert (color["width"], color["height"]) == (height["width"], height["height"])
    assert color["params"]["paired_height_value"] > 0

    with Image.open(out_dir / color["filename"]) as image:
        rgb = np.array(image.convert("RGB"), dtype=np.uint8)
        alpha = np.array(image.getchannel("A"), dtype=np.uint8)
    assert np.all(rgb == np.array(gen.ALPHA_FIELD_RGB, dtype=np.uint8))
    assert color["params"]["rgb_payload"] == list(gen.ALPHA_FIELD_RGB)
    assert set(np.unique(alpha).tolist()) == set(gen.ALPHA_FIELD_LEVELS)
    for field in color["params"]["alpha_fields"]:
        values = alpha[:, field["x_start"] : field["x_end_exclusive"]]
        assert set(np.unique(values).tolist()) == {field["alpha"]}

    with Image.open(out_dir / height["filename"]) as image:
        height_values = np.array(image, dtype=np.uint16)
    assert np.all(height_values == color["params"]["paired_height_value"])


def test_registration_height_has_pixel_exact_color_landmarks(tmp_path: Path) -> None:
    """I-08 erkennt Versatz auf beiden Achsen über dieselben asymmetrischen Marker."""
    out_dir = _write(tmp_path, "run")
    manifest = json.loads((out_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    by_name = {entry["filename"]: entry for entry in manifest["fixtures"]}
    color = by_name["color_height_reference.png"]
    height = by_name["height_registration_16bit.png"]

    assert (color["width"], color["height"]) == (height["width"], height["height"])
    assert height["params"]["paired_color_file"] == color["filename"]
    with (
        Image.open(out_dir / color["filename"]) as color_image,
        Image.open(out_dir / height["filename"]) as height_image,
    ):
        color_rgb = np.array(color_image.convert("RGB"), dtype=np.uint8)
        height_values = np.array(height_image, dtype=np.uint16)

    expected_landmarks = np.any(color_rgb != 255, axis=2)
    assert np.array_equal(height_values > 0, expected_landmarks)
    assert set(np.unique(height_values).tolist()) == {0, gen.HEIGHT_MAX_16BIT}


def test_registration_triplet_has_pixel_exact_landmarks(tmp_path: Path) -> None:
    """I-08 nutzt für COLOR, HEIGHT und GLOSS dieselbe Landmarkmaske."""
    out_dir = _write(tmp_path, "run")
    manifest = json.loads((out_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    by_name = {entry["filename"]: entry for entry in manifest["fixtures"]}
    gloss = by_name["gloss_registration.png"]
    assert gloss["params"]["paired_color_file"] == "color_height_reference.png"
    assert gloss["params"]["paired_height_file"] == "height_registration_16bit.png"

    with (
        Image.open(out_dir / "color_height_reference.png") as color_image,
        Image.open(out_dir / "height_registration_16bit.png") as height_image,
        Image.open(out_dir / "gloss_registration.png") as gloss_image,
    ):
        color_landmarks = np.any(
            np.array(color_image.convert("RGB"), dtype=np.uint8) != 255, axis=2,
        )
        height_landmarks = np.array(height_image, dtype=np.uint16) > 0
        gloss_landmarks = np.array(gloss_image, dtype=np.uint8) > 0
    assert np.array_equal(color_landmarks, height_landmarks)
    assert np.array_equal(color_landmarks, gloss_landmarks)


# ── mm/DPI-Fixtures: pHYs-Varianten und Widerspruchstest ────────────────

def test_mm_dpi_fixtures_cover_no_phys_consistent_and_conflicting(tmp_path: Path) -> None:
    out_dir = _write(tmp_path, "run")
    manifest = json.loads((out_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    mm_entries = {e["filename"]: e for e in manifest["fixtures"] if e["role"] == "color_motif"}

    for combo in gen.MM_DPI_COMBOS:
        no_phys = mm_entries[f"mm_{combo.label}_no_phys.png"]
        phys = mm_entries[f"mm_{combo.label}_phys.png"]
        conflict = mm_entries[f"mm_{combo.label}_phys_conflict.png"]

        assert no_phys["params"]["phys_dpi"] is None
        with Image.open(out_dir / no_phys["filename"]) as img:
            assert "dpi" not in img.info

        assert phys["params"]["phys_dpi"] == combo.nominal_dpi
        with Image.open(out_dir / phys["filename"]) as img:
            # PNGs pHYs speichert Pixel/Meter als Ganzzahl; der DPI-Rückweg
            # rundet daher minimal (< 0,01 %) – erwartetes Format-Verhalten.
            assert round(img.info["dpi"][0]) == combo.nominal_dpi

        assert conflict["params"]["phys_dpi"] == combo.conflict_dpi
        assert conflict["params"]["phys_dpi"] != combo.nominal_dpi
        with Image.open(out_dir / conflict["filename"]) as img:
            assert round(img.info["dpi"][0]) == combo.conflict_dpi
            # Gleiches Pixelmaß wie die konsistente Variante – nur die DPI-Angabe
            # widerspricht sich (I-05 im Annahmeninventar).
            assert img.size == (combo.width, combo.height)


def test_mm_dpi_fixture_encodes_x_and_y_dpi_independently(tmp_path: Path) -> None:
    """I-05: nicht-quadratische pHYs-Werte dürfen nicht still gekoppelt werden."""
    out_dir = _write(tmp_path, "run")
    manifest = json.loads((out_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    entry = next(
        item for item in manifest["fixtures"]
        if item["filename"] == "mm_typisch_phys_xy.png"
    )
    assert entry["params"]["phys_dpi"] == list(gen.NON_SQUARE_DPI)
    assert entry["params"]["mm_implied_by_phys_chunk"] == [101.6, 203.2]
    with Image.open(out_dir / entry["filename"]) as image:
        assert round(image.info["dpi"][0]) == gen.NON_SQUARE_DPI[0]
        assert round(image.info["dpi"][1]) == gen.NON_SQUARE_DPI[1]


def test_i06_bundle_uses_real_writer_contract_and_conflicting_phys(tmp_path: Path) -> None:
    """I-06 prüft ein echtes BgRemover-Paket, nicht fixtures_manifest.json."""
    out_dir = _write(tmp_path, "run")
    fixture_manifest = json.loads(
        (out_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    bundle = fixture_manifest["bundles"][0]
    bundle_dir = out_dir / bundle["directory"]
    assert bundle["generated_via"] == "bgremover.eufymake_writer.write_export"
    assert {path.name for path in bundle_dir.iterdir()} == {
        "color_motif.png", "height_map.png", "gloss_mask.png", "manifest.json",
    }

    export_manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    assert export_manifest["profile"] == gen.EXPORT_PROFILE
    assert export_manifest["profile_version"] == gen.EXPORT_PROFILE_VERSION
    assert export_manifest["kind"] == "eufymake_import_assets"
    assert export_manifest["target"]["pixel_size"] == list(gen.COLOR_HEIGHT_PAIR_SIZE)
    assert export_manifest["target"]["bit_depth"] == 16
    assert export_manifest["target"]["dpi"] == list(gen.EXPORT_TARGET_DPI)
    assert [asset["filename"] for asset in export_manifest["assets"]] == [
        "color_motif.png", "height_map.png", "gloss_mask.png",
    ]

    for filename in ("color_motif.png", "height_map.png", "gloss_mask.png"):
        with Image.open(bundle_dir / filename) as image:
            assert tuple(round(value) for value in image.info["dpi"]) == gen.EXPORT_PHYS_DPI

    with (
        Image.open(bundle_dir / "color_motif.png") as color_image,
        Image.open(bundle_dir / "height_map.png") as height_image,
        Image.open(bundle_dir / "gloss_mask.png") as gloss_image,
    ):
        color_landmarks = np.any(
            np.array(color_image.convert("RGB"), dtype=np.uint8) != 255, axis=2,
        )
        assert np.array_equal(color_landmarks, np.array(height_image) > 0)
        assert np.array_equal(color_landmarks, np.array(gloss_image) > 0)


def test_px_to_mm_matches_documented_formula() -> None:
    # mm = Pixel / DPI * 25,4, gerundet auf 3 Nachkommastellen.
    assert gen.px_to_mm(1200, 300) == 101.6
    assert gen.px_to_mm(300, 150) == 50.8


# ── Gloss-Fixtures ────────────────────────────────────────────────────────

def test_gloss_fixtures_are_8bit_grayscale(tmp_path: Path) -> None:
    out_dir = _write(tmp_path, "run")
    manifest = json.loads((out_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    gloss_entries = [e for e in manifest["fixtures"] if e["role"] == "gloss_mask"]
    assert len(gloss_entries) == len(gen._GLOSS_PATTERNS) + 1
    for entry in gloss_entries:
        assert entry["bit_depth"] == 8
        assert entry["png_mode"] == "L"


def test_gloss_min_max_are_solid_extremes(tmp_path: Path) -> None:
    out_dir = _write(tmp_path, "run")
    with Image.open(out_dir / "gloss_min.png") as img:
        assert set(np.array(img).flatten().tolist()) == {0}
    with Image.open(out_dir / "gloss_max.png") as img:
        assert set(np.array(img).flatten().tolist()) == {255}


# ── Checked-in Fixtures dürfen nicht vom Generator abweichen ────────────

_MANIFEST_CONTENT_KEYS = (
    "role", "pattern", "bit_depth", "png_mode", "width", "height", "params",
)


def test_checked_in_fixtures_match_current_generator(tmp_path: Path) -> None:
    """Eingecheckte Fixtures dürfen inhaltlich nicht vom aktuellen Generator abweichen.

    Verglichen werden Pixelinhalt und Bildmetadaten (Modus, Maße, ``dpi``) statt
    PNG-Rohbytes: der zlib-Kompressionsstream unterscheidet sich je nach
    Plattform/Pillow-Build – auf dem macOS-Kandidatenbau von 2.8.0 (Run
    31968057273) erzeugte derselbe Generator für dieselben Pixel andere Bytes
    *und* eine andere Dateigröße als das unter Linux eingecheckte Fixture, obwohl
    Breite/Höhe/Modus/Parameter bitgenau gleich blieben. Ein reiner Byte-Vergleich
    wäre daher plattformabhängig und kein echter Drift-Nachweis.
    """
    assert CHECKED_IN_DIR.is_dir(), (
        "tests/fixtures/eufymake_hardware/ fehlt – "
        "python scripts/eufymake_fixture_generator.py generate ausführen"
    )
    fresh_dir = _write(tmp_path, "fresh")

    checked_in_files = sorted(
        p.relative_to(CHECKED_IN_DIR) for p in CHECKED_IN_DIR.rglob("*") if p.is_file()
    )
    fresh_files = sorted(
        p.relative_to(fresh_dir) for p in fresh_dir.rglob("*") if p.is_file()
    )
    assert checked_in_files == fresh_files, (
        "Eingecheckte Fixtures weichen von der Dateiliste des aktuellen "
        "Generators ab – neu generieren und committen."
    )

    checked_in_manifest = json.loads(
        (CHECKED_IN_DIR / gen.MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    fresh_manifest = json.loads((fresh_dir / gen.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    checked_in_by_name = {e["filename"]: e for e in checked_in_manifest["fixtures"]}
    fresh_by_name = {e["filename"]: e for e in fresh_manifest["fixtures"]}
    assert checked_in_by_name.keys() == fresh_by_name.keys()
    for filename, fresh_entry in fresh_by_name.items():
        checked_in_entry = checked_in_by_name[filename]
        for key in _MANIFEST_CONTENT_KEYS:
            assert checked_in_entry[key] == fresh_entry[key], f"{filename}: {key} weicht ab"

    assert checked_in_manifest["bundle_count"] == fresh_manifest["bundle_count"]
    checked_in_bundles = json.loads(json.dumps(checked_in_manifest["bundles"]))
    fresh_bundles = json.loads(json.dumps(fresh_manifest["bundles"]))
    for bundles in (checked_in_bundles, fresh_bundles):
        for bundle in bundles:
            for entry in bundle["files"]:
                entry.pop("sha256")
                entry.pop("bytes")
    assert checked_in_bundles == fresh_bundles

    for name in checked_in_files:
        if name.name == gen.MANIFEST_FILENAME:
            continue
        if name.name == "manifest.json":
            checked_in_export = json.loads(
                (CHECKED_IN_DIR / name).read_text(encoding="utf-8")
            )
            fresh_export = json.loads((fresh_dir / name).read_text(encoding="utf-8"))
            assert checked_in_export == fresh_export, name
            continue
        with (
            Image.open(CHECKED_IN_DIR / name) as checked_in_img,
            Image.open(fresh_dir / name) as fresh_img,
        ):
            assert checked_in_img.mode == fresh_img.mode, name
            assert checked_in_img.size == fresh_img.size, name
            assert checked_in_img.info.get("dpi") == fresh_img.info.get("dpi"), name
            checked_in_arr = np.array(checked_in_img)
            fresh_arr = np.array(fresh_img)
            assert np.array_equal(checked_in_arr, fresh_arr), (
                f"{name} weicht inhaltlich vom aktuellen Generator ab – "
                "neu generieren und committen."
            )
