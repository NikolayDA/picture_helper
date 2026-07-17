"""End-to-End-Beweise der 16-Bit-Höhenpipeline (#590, Epic #581).

Belegt den vollständigen Weg Import → Bearbeitung → Projekt-Roundtrip →
Vorschau-neutraler Zustand → Export → Wiederlesen ohne unbeabsichtigte
8-Bit-Reduktion – inklusive Legacy-Migration, gemischtem Projekt, Undo/Redo
über den Roundtrip, Referenzquantisierung des 8-Bit-Exports und unabhängiger
Metadatenprüfung des 16-Bit-Exports. Alle Tests laufen headless/offscreen;
das 40-MP-Szenario trägt den ``ui``-Marker (nightly via ``make ui``).
"""
from __future__ import annotations

import json
import zipfile

import numpy as np
import pytest
from PIL import Image

from bgremover import ImageCanvas, height_ops
from bgremover.eufymake_writer import write_export
from bgremover.height_map import HeightField, image_to_height_field
from bgremover.project_io import PROJECT_SUFFIX, load_project, save_project
from bgremover.project_model import LayerKind, LayerRole, Project


def _write_png16(path, values: np.ndarray) -> None:
    h, w = values.shape
    raw = np.ascontiguousarray(values, dtype="<u2").tobytes()
    Image.frombytes("I;16", (w, h), raw).save(path)


def _read_png16(path) -> np.ndarray:
    with Image.open(path) as img:
        img.load()
        return image_to_height_field(img).values


def _field16(values: np.ndarray, coverage: np.ndarray | None = None) -> HeightField:
    cov = (
        np.full(values.shape, 255, dtype=np.uint8) if coverage is None else coverage
    )
    return HeightField(values, cov, max_value=65535)


def _height_project(values: np.ndarray, *, with_color: bool = True) -> Project:
    h, w = values.shape
    project = Project(w, h)
    if with_color:
        project.create_layer(
            Image.new("RGBA", (w, h), (200, 40, 10, 255)), name="Farbe")
    layer = project.create_layer(
        name="Höhe", kind=LayerKind.HEIGHT, height_data=_field16(values))
    project.assign_role(layer.id, LayerRole.HEIGHT_MAP)
    return project


def _gradient16(w: int, h: int) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w]
    return ((xx * 997 + yy * 13) % 65536).astype(np.uint16)


def test_gradient_e2e_import_edit_save_export_reimport(qapp, tmp_path) -> None:
    """Import → Operation → Save → Open → 16-Bit-Export → Re-Import bitgenau."""
    values = _gradient16(64, 64)
    assert len(np.unique(values)) > 256                     # echte 16-Bit-Quelle
    src = tmp_path / "gradient16.png"
    _write_png16(src, values)

    canvas = ImageCanvas()
    canvas.apply_loaded_image(
        Image.new("RGBA", (64, 64), (10, 20, 30, 255)), "base.png")
    canvas.import_height_map(str(src))
    canvas.apply_height_op(lambda f: height_ops.gamma(f, 1.3))
    expected = np.clip(
        np.rint((values.astype(np.float64) / 65535.0) ** 1.3 * 65535.0),
        0, 65535,
    ).astype(np.uint16)
    field = canvas.project.active_layer().height_data
    assert field is not None
    assert np.array_equal(field.values, expected)

    proj_path = tmp_path / f"e2e{PROJECT_SUFFIX}"
    save_project(canvas.project, proj_path)
    loaded = load_project(proj_path)
    reloaded = loaded.layer_by_role(LayerRole.HEIGHT_MAP).height_data
    assert reloaded is not None
    assert np.array_equal(reloaded.values, expected)        # Roundtrip bitgenau
    assert len(np.unique(reloaded.values)) > 256            # keine 8-Bit-Reduktion

    dest = tmp_path / "export"
    write_export(
        loaded, dest, optional_roles=[LayerRole.HEIGHT_MAP],
        bit_depth=16, confirm_warnings=True)
    exported = _read_png16(dest / "height_map.png")
    assert np.array_equal(exported, expected)               # Export → Re-Import


def test_low_bit_pattern_stays_distinguishable_until_lossless_export(tmp_path) -> None:
    """Gleiches High-Byte, verschiedene Low-Bytes: bis zum Export unterscheidbar."""
    values = (0x1200 + np.arange(256, dtype=np.uint16)).reshape(16, 16)
    project = _height_project(values)
    proj_path = tmp_path / f"lowbits{PROJECT_SUFFIX}"
    save_project(project, proj_path)
    loaded = load_project(proj_path)

    dest = tmp_path / "export"
    write_export(
        loaded, dest, optional_roles=[LayerRole.HEIGHT_MAP],
        bit_depth=16, confirm_warnings=True)
    exported = _read_png16(dest / "height_map.png")
    assert np.array_equal(exported, values)
    assert len(np.unique(exported)) == 256                  # alle Low-Bytes erhalten


def test_legacy_v1_project_migrates_edits_and_saves_reproducibly(tmp_path) -> None:
    """v1-Projekt: migrieren, bearbeiten, als v2 speichern – reproduzierbar."""
    import io as _io

    gray = np.arange(16, dtype=np.uint8).reshape(4, 4) * 16
    rgba = np.zeros((4, 4, 4), dtype=np.uint8)
    rgba[:, :, :3] = gray[:, :, None]
    rgba[:, :, 3] = 255

    def _png_bytes(img: Image.Image) -> bytes:
        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    manifest = {
        "version": 1, "project_version": 1, "width": 4, "height": 4,
        "active_layer_id": "h1", "metadata": {},
        "layers": [
            {"id": "c1", "name": "Farbe", "kind": "color", "visible": True,
             "opacity": 1.0, "locked": False, "role": "color_motif",
             "bit_depth": 8, "file": "layer_0000.png"},
            {"id": "h1", "name": "Höhe", "kind": "height", "visible": True,
             "opacity": 1.0, "locked": False, "role": "height_map",
             "bit_depth": 8, "file": "layer_0001.png"},
        ],
    }
    v1_path = tmp_path / f"legacy{PROJECT_SUFFIX}"
    with zipfile.ZipFile(v1_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("layer_0000.png", _png_bytes(
            Image.new("RGBA", (4, 4), (1, 2, 3, 255))))
        zf.writestr("layer_0001.png", _png_bytes(Image.fromarray(rgba, "RGBA")))

    migrated = load_project(v1_path)
    height = migrated.layer_by_role(LayerRole.HEIGHT_MAP)
    assert height.height_data is not None
    assert np.array_equal(
        height.height_data.values, gray.astype(np.uint16) * 257)

    # Bearbeitung auf der kanonischen Payload, dann kontrolliert v2 speichern.
    edited = height_ops.levels(height.height_data, 0, 60000)
    migrated.set_layer_height_data(height.id, edited)
    out = tmp_path / f"v2{PROJECT_SUFFIX}"
    save_project(migrated, out)
    first = load_project(out).layer_by_role(LayerRole.HEIGHT_MAP).height_data
    save_project(load_project(out), out)
    second = load_project(out).layer_by_role(LayerRole.HEIGHT_MAP).height_data
    assert first is not None and second is not None
    assert np.array_equal(first.values, edited.values)      # v2 hält den Editierstand
    assert np.array_equal(first.values, second.values)      # reproduzierbar


def test_mixed_project_roundtrip_and_export_without_regression(tmp_path) -> None:
    """COLOR + HEIGHT + GLOSS: Roundtrip + Export ohne semantische Änderung."""
    values = _gradient16(8, 8)
    project = _height_project(values)
    gloss = project.create_layer(
        Image.new("RGBA", (8, 8), (200, 200, 200, 255)), name="Glanz",
        kind=LayerKind.GLOSS)
    project.assign_role(gloss.id, LayerRole.GLOSS_MASK)
    color_before = np.array(project.composite_color())

    proj_path = tmp_path / f"mixed{PROJECT_SUFFIX}"
    save_project(project, proj_path)
    loaded = load_project(proj_path)
    assert np.array_equal(np.array(loaded.composite_color()), color_before)
    field = loaded.layer_by_role(LayerRole.HEIGHT_MAP).height_data
    assert field is not None and np.array_equal(field.values, values)

    dest = tmp_path / "export"
    write_export(
        loaded, dest,
        optional_roles=[LayerRole.HEIGHT_MAP, LayerRole.GLOSS_MASK],
        bit_depth=16, confirm_warnings=True)
    with Image.open(dest / "color_motif.png") as motif:
        assert np.array_equal(np.array(motif.convert("RGBA")), color_before)
    with Image.open(dest / "gloss_mask.png") as mask:
        assert mask.size == (8, 8)                          # Gloss-Regression: da + Größe


def test_undo_redo_before_and_after_project_roundtrip(qapp, tmp_path) -> None:
    """Undo/Redo liefert vor und nach dem Roundtrip dieselben Höhenwerte."""
    values = _gradient16(16, 16)
    canvas = ImageCanvas()
    canvas.set_project(_height_project(values))
    canvas.apply_height_op(lambda f: height_ops.clamp_range(f, 1000, 60000))
    clamped = np.clip(values, 1000, 60000)

    canvas.undo()
    assert np.array_equal(
        canvas.project.active_layer().height_data.values, values)
    canvas.redo()
    assert np.array_equal(
        canvas.project.active_layer().height_data.values, clamped)

    proj_path = tmp_path / f"undo{PROJECT_SUFFIX}"
    save_project(canvas.project, proj_path)
    fresh = ImageCanvas()
    fresh.set_project(load_project(proj_path))
    field = fresh.project.layer_by_role(LayerRole.HEIGHT_MAP).height_data
    assert np.array_equal(field.values, clamped)            # Roundtrip = Redo-Stand
    # Auch nach dem Roundtrip bleibt der Editier-/Undo-Zyklus bitgenau.
    fresh.apply_height_op(lambda f: height_ops.gamma(f, 2.0))
    fresh.undo()
    assert np.array_equal(
        fresh.project.layer_by_role(LayerRole.HEIGHT_MAP).height_data.values,
        clamped,
    )


def test_8bit_export_matches_reference_quantization(tmp_path) -> None:
    """8-Bit-Export quantisiert exakt nach der ADR-Regel rint(v/257)."""
    values = _gradient16(16, 16)
    project = _height_project(values)
    dest = tmp_path / "export8"
    write_export(
        project, dest, optional_roles=[LayerRole.HEIGHT_MAP],
        bit_depth=8, confirm_warnings=True)
    with Image.open(dest / "height_map.png") as img:
        img.load()
        assert img.mode == "L"                              # echtes 8-Bit-Ziel
        exported = np.array(img, dtype=np.uint8)
    reference = np.clip(
        np.rint(values.astype(np.float64) / 257.0), 0, 255).astype(np.uint8)
    assert np.array_equal(exported, reference)              # pixelgenau


def test_16bit_export_metadata_and_independent_reread(tmp_path) -> None:
    """16-Bit-Export: Datentyp, Größe, Manifest und unabhängiges Wiederlesen."""
    values = _gradient16(16, 8)
    project = _height_project(values)
    dest = tmp_path / "export16"
    write_export(
        project, dest, optional_roles=[LayerRole.HEIGHT_MAP],
        bit_depth=16, confirm_warnings=True)

    with Image.open(dest / "height_map.png") as img:
        img.load()
        assert img.mode in ("I;16", "I")                    # echter 16-Bit-Inhalt
        assert img.size == (16, 8)
    # Unabhängiges Wiederlesen über numpy (nicht der Import-Codepfad).
    with Image.open(dest / "height_map.png") as img:
        raw = np.frombuffer(img.tobytes(), dtype="<u2").reshape(8, 16) \
            if img.mode == "I;16" else np.asarray(img, dtype=np.int64)
    assert np.array_equal(raw.astype(np.uint16), values)

    manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
    height_assets = [
        a for a in manifest["assets"] if a["filename"] == "height_map.png"
    ]
    assert height_assets and height_assets[0]["bit_depth"] == 16
    assert manifest["target"]["bit_depth"] == 16
    assert manifest["target"]["pixel_size"] == [16, 8]


@pytest.mark.ui
def test_40mp_e2e_stays_within_budgets(tmp_path) -> None:
    """40-MP-E2E (nightly): Import → Save/Open → 16-Bit-Export in Budget-Schranken."""
    import time

    width, height = 8000, 5000
    values = np.zeros((height, width), dtype=np.uint16)
    values[0, :8] = [0, 1, 255, 256, 32767, 65534, 65535, 0x1234]
    src = tmp_path / "mp40.png"
    _write_png16(src, values)

    start = time.perf_counter()
    with Image.open(src) as img:
        img.load()
        field = image_to_height_field(img)
    project = Project(width, height)
    project.create_layer(
        Image.new("RGBA", (width, height), (5, 5, 5, 255)), name="Farbe")
    layer = project.create_layer(
        name="Höhe", kind=LayerKind.HEIGHT, height_data=field)
    project.assign_role(layer.id, LayerRole.HEIGHT_MAP)

    proj_path = tmp_path / f"mp40{PROJECT_SUFFIX}"
    save_project(project, proj_path)
    loaded = load_project(proj_path)
    dest = tmp_path / "export"
    write_export(
        loaded, dest, optional_roles=[LayerRole.HEIGHT_MAP],
        bit_depth=16, confirm_warnings=True)
    exported = _read_png16(dest / "height_map.png")
    elapsed = time.perf_counter() - start

    assert list(exported[0, :8]) == [0, 1, 255, 256, 32767, 65534, 65535, 0x1234]
    assert elapsed < 300.0                                   # großzügige CI-Schranke
