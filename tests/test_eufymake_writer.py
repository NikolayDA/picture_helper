"""Qt-freie Tests fürs Rendern und atomare Schreiben (#353).

Deckt Rendering (Farbmotiv pixelgenau = Komposit inkl. Alpha, Height-Semantik
hell = hoch, 16-Bit-Pfad, Gloss), optionale Assets, deterministische Skalierung,
Manifest, den atomaren Schreib-Erfolg sowie alle Fehlerpfade (Render-Fehler vor
Veröffentlichung, Ersetzungsfehler bewahrt vorhandenes Ziel, Kollision,
Temp-Aufräumen) und das Validierungs-Gating ab.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from bgremover.eufymake_export import build_export_plan
from bgremover.eufymake_writer import (
    MANIFEST_FILENAME,
    ExportConfirmationRequired,
    ExportTargetExistsError,
    ExportTargetNotDirectoryError,
    ExportValidationError,
    render_export,
    write_export,
)
from bgremover.height_map import HEIGHT_MAX_16BIT, HeightField
from bgremover.project_model import (
    META_BIT_DEPTH,
    LayerKind,
    LayerRole,
    Project,
)


def _solid(size: tuple[int, int], color: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", size, color)


def _row_gray(size: tuple[int, int]) -> Image.Image:
    """RGBA-Ebene mit horizontalem Grauverlauf (``R==G==B``), voll deckend."""
    w, h = size
    row = np.linspace(0, 255, num=w, dtype=np.uint8)
    grid = np.tile(row, (h, 1))
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = arr[:, :, 1] = arr[:, :, 2] = grid
    arr[:, :, 3] = 255
    return Image.fromarray(arr, "RGBA")


def _color_project(size: tuple[int, int] = (4, 2)) -> Project:
    project = Project(*size)
    project.create_layer(_solid(size, (10, 20, 30, 200)), name="Farbe")
    return project


def _add_height(project: Project, image: Image.Image | None = None) -> str:
    img = image if image is not None else _row_gray(project.size)
    layer = project.create_layer(img, name="Höhe", kind=LayerKind.HEIGHT)
    project.assign_role(layer.id, LayerRole.HEIGHT_MAP)
    return layer.id


def _add_gloss(project: Project, image: Image.Image | None = None) -> str:
    img = image if image is not None else _row_gray(project.size)
    layer = project.create_layer(img, name="Gloss", kind=LayerKind.GLOSS)
    project.assign_role(layer.id, LayerRole.GLOSS_MASK)
    return layer.id


# ── Rendering ────────────────────────────────────────────────────────────

def test_color_motif_matches_composite_with_alpha() -> None:
    project = _color_project()
    plan = build_export_plan(project)
    rendered = render_export(project, plan)
    motif = rendered.assets[0]
    assert motif.asset.role is LayerRole.COLOR_MOTIF
    assert motif.image.mode == "RGBA"
    expected = np.asarray(project.composite_color())
    assert np.array_equal(np.asarray(motif.image), expected)
    # Alpha verlustfrei erhalten (Eingabe-Alpha war 200).
    assert int(np.asarray(motif.image)[0, 0, 3]) == 200


def test_color_motif_from_explicit_role_layer() -> None:
    project = _color_project()
    layer = project.layers[0]
    project.assign_role(layer.id, LayerRole.COLOR_MOTIF)
    plan = build_export_plan(project)
    assert plan.color_motif.source_layer_id == layer.id
    motif = render_export(project, plan).assets[0]
    assert np.array_equal(np.asarray(motif.image), np.asarray(layer.image))


def test_height_is_grayscale_light_is_high() -> None:
    project = _color_project((4, 1))
    _add_height(project)  # Reihe 0,85,170,255
    plan = build_export_plan(project)
    height = render_export(project, plan).assets[1]
    assert height.asset.role is LayerRole.HEIGHT_MAP
    assert height.image.mode == "L"
    row = np.asarray(height.image)[0]
    assert row.tolist() == [0, 85, 170, 255]
    # Schwarz = niedrigste, Weiß = höchste Stufe.
    assert int(row.min()) == 0 and int(row.max()) == 255


def test_height_16bit_spreads_losslessly() -> None:
    project = _color_project((2, 1))
    arr = np.zeros((1, 2, 4), dtype=np.uint8)
    arr[0, 0, :3] = 0
    arr[0, 1, :3] = 255
    arr[:, :, 3] = 255
    _add_height(project, Image.fromarray(arr, "RGBA"))
    project.metadata[META_BIT_DEPTH] = 16
    plan = build_export_plan(project)
    height = render_export(project, plan).assets[1]
    assert height.image.mode == "I;16"
    row = np.asarray(height.image)[0]
    assert row.tolist() == [0, 65535]


def test_height_16bit_export_preserves_canonical_payload_low_bits() -> None:
    project = _color_project((3, 1))
    values = np.array([[0x1201, 0x1234, 0x12FE]], dtype=np.uint16)
    layer = project.create_layer(
        name="Höhe",
        kind=LayerKind.HEIGHT,
        height_data=HeightField(
            values,
            np.full(values.shape, 255, dtype=np.uint8),
            HEIGHT_MAX_16BIT,
        ),
    )
    project.assign_role(layer.id, LayerRole.HEIGHT_MAP)
    project.metadata[META_BIT_DEPTH] = 16

    height = render_export(project, build_export_plan(project)).assets[1]

    assert height.image.mode == "I;16"
    assert np.array_equal(np.asarray(height.image), values)


def test_gloss_is_grayscale() -> None:
    project = _color_project()
    _add_gloss(project)
    plan = build_export_plan(project)
    gloss = render_export(project, plan).assets[-1]
    assert gloss.asset.role is LayerRole.GLOSS_MASK
    assert gloss.image.mode == "L"


def test_optional_assets_only_when_present() -> None:
    project = _color_project()
    assert len(render_export(project, build_export_plan(project)).assets) == 1
    _add_height(project)
    assert len(render_export(project, build_export_plan(project)).assets) == 2


def test_all_assets_have_target_size() -> None:
    project = _color_project((4, 2))
    _add_height(project)
    _add_gloss(project)
    rendered = render_export(project, build_export_plan(project))
    for item in rendered.assets:
        assert item.image.size == (4, 2)


def test_scaling_is_deterministic_nearest_for_data() -> None:
    project = _color_project((2, 1))
    _add_height(project, _row_gray((2, 1)))  # Werte 0, 255
    plan = build_export_plan(project)
    big = dataclasses.replace(plan, target=dataclasses.replace(plan.target, pixel_size=(4, 1)))
    rendered = render_export(project, big)
    for item in rendered.assets:
        assert item.image.size == (4, 1)
    height_row = np.asarray(rendered.assets[1].image)[0]
    # Nearest erfindet keine Zwischenwerte.
    assert set(height_row.tolist()) <= {0, 255}


# ── Manifest ─────────────────────────────────────────────────────────────

def test_manifest_describes_plan() -> None:
    project = _color_project((6, 3))
    _add_height(project)
    manifest = render_export(project, build_export_plan(project)).manifest
    assert manifest["profile_version"] == 1
    assert manifest["height_semantics"] == "light_is_high"
    assert manifest["target"]["pixel_size"] == [6, 3]
    filenames = [a["filename"] for a in manifest["assets"]]
    assert filenames == ["color_motif.png", "height_map.png"]
    # Stabiles strukturiertes Feld statt freier Notiztext: das Manifest kennzeichnet
    # sich als Import-Asset-Paket und markiert den bewussten Verzicht auf natives
    # ``.empf`` maschinenlesbar über die offene Frage.
    assert manifest["kind"] == "eufymake_import_assets"
    assert "native_empf_project" in manifest["open_questions"]


# ── Atomares Schreiben: Erfolg & Kollision ───────────────────────────────

def test_write_publishes_all_assets(tmp_path: Path) -> None:
    project = _color_project()
    _add_height(project)
    dest = tmp_path / "export"
    out = write_export(project, dest)
    assert out == dest
    names = sorted(p.name for p in dest.iterdir())
    assert names == ["color_motif.png", "height_map.png", MANIFEST_FILENAME]
    # Manifest ist gültiges JSON.
    json.loads((dest / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    # Kein natives .empf erzeugt.
    assert not any(p.suffix == ".empf" for p in dest.iterdir())


def test_existing_target_without_overwrite_raises(tmp_path: Path) -> None:
    project = _color_project()
    dest = tmp_path / "export"
    write_export(project, dest)
    marker = dest / "color_motif.png"
    original = marker.read_bytes()
    with pytest.raises(ExportTargetExistsError):
        write_export(project, dest)
    # Vorhandenes Ziel unverändert, kein Temp-Rest.
    assert marker.read_bytes() == original
    assert not _temp_leftovers(tmp_path, dest)


def test_overwrite_replaces_target(tmp_path: Path) -> None:
    dest = tmp_path / "export"
    write_export(_color_project((4, 2)), dest)
    # Anderes Projekt mit zusätzlicher Height-Ebene überschreibt.
    project2 = _color_project((4, 2))
    _add_height(project2)
    write_export(project2, dest, overwrite=True)
    names = sorted(p.name for p in dest.iterdir())
    assert names == ["color_motif.png", "height_map.png", MANIFEST_FILENAME]
    assert not _temp_leftovers(tmp_path, dest)


# ── Atomares Schreiben: Fehlerpfade ──────────────────────────────────────

def test_render_error_leaves_no_partial_target(tmp_path: Path, monkeypatch) -> None:
    project = _color_project()
    _add_height(project)
    dest = tmp_path / "export"

    import bgremover.eufymake_writer as writer

    calls = {"n": 0}
    real = writer._write_png

    def flaky(image, path):  # 2. Asset schlägt fehl → vor Veröffentlichung
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("inject encode failure")
        return real(image, path)

    monkeypatch.setattr(writer, "_write_png", flaky)
    with pytest.raises(OSError, match="inject"):
        write_export(project, dest)
    assert not dest.exists()
    assert not _temp_leftovers(tmp_path, dest)


def test_replace_error_preserves_existing_target(tmp_path: Path, monkeypatch) -> None:
    dest = tmp_path / "export"
    write_export(_color_project((4, 2)), dest)
    original = (dest / "color_motif.png").read_bytes()
    manifest_before = (dest / MANIFEST_FILENAME).read_text(encoding="utf-8")

    import bgremover.eufymake_writer as writer

    def boom(src, dst):
        raise OSError("inject replace failure")

    monkeypatch.setattr(writer.os, "replace", boom)
    project2 = _color_project((4, 2))
    _add_height(project2)
    with pytest.raises(OSError, match="inject"):
        write_export(project2, dest, overwrite=True)
    # Vorhandenes gültiges Ziel unversehrt, Temp aufgeräumt.
    assert (dest / "color_motif.png").read_bytes() == original
    assert (dest / MANIFEST_FILENAME).read_text(encoding="utf-8") == manifest_before
    assert not (dest / "height_map.png").exists()
    assert not _temp_leftovers(tmp_path, dest)


def test_replace_restore_path_recovers_existing(tmp_path: Path, monkeypatch) -> None:
    dest = tmp_path / "export"
    write_export(_color_project((4, 2)), dest)
    original = (dest / "color_motif.png").read_bytes()

    import bgremover.eufymake_writer as writer

    real_replace = writer.os.replace
    calls = {"n": 0}

    def flaky(src, dst):  # 1. Verschieben aside ok, 2. Einspielen scheitert, 3. Restore ok
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("inject publish failure")
        return real_replace(src, dst)

    monkeypatch.setattr(writer.os, "replace", flaky)
    project2 = _color_project((4, 2))
    _add_height(project2)
    with pytest.raises(OSError, match="inject"):
        write_export(project2, dest, overwrite=True)
    assert (dest / "color_motif.png").read_bytes() == original
    assert not (dest / "height_map.png").exists()
    assert not _temp_leftovers(tmp_path, dest)


# ── Validierungs-Gating (#354-Integration) ───────────────────────────────

def test_errors_block_any_write(tmp_path: Path) -> None:
    project = Project(4, 2)  # nur Height, kein Farbmotiv → Fehler
    _add_height(project)
    dest = tmp_path / "export"
    with pytest.raises(ExportValidationError) as exc:
        write_export(project, dest)
    assert exc.value.findings  # blockierende Fehler mitgeliefert
    assert not dest.exists()
    assert not _temp_leftovers(tmp_path, dest)


def test_warnings_require_confirmation(tmp_path: Path) -> None:
    project = _color_project()
    _add_gloss(project)  # → GLOSS_INK_MODE-Warnung
    dest = tmp_path / "export"
    with pytest.raises(ExportConfirmationRequired) as exc:
        write_export(project, dest)
    assert all(not f.is_error for f in exc.value.findings)
    assert not dest.exists()
    # Mit Bestätigung wird geschrieben.
    write_export(project, dest, confirm_warnings=True)
    assert dest.is_dir()


def test_optional_roles_limit_written_assets(tmp_path: Path) -> None:
    project = _color_project()
    _add_height(project)
    _add_gloss(project)
    dest = tmp_path / "export"
    write_export(project, dest, optional_roles=[], confirm_warnings=True)
    names = sorted(p.name for p in dest.iterdir())
    assert names == ["color_motif.png", MANIFEST_FILENAME]


def test_optional_roles_generator_is_not_exhausted(tmp_path: Path) -> None:
    # Ein Einmal-Iterable (Generator) darf nicht von der Prüfung verbraucht werden,
    # sodass der Plan die gewählte Rolle nicht mehr sieht (Codex-Befund #373).
    project = _color_project()
    _add_height(project)
    dest = tmp_path / "export"
    roles = (r for r in (LayerRole.HEIGHT_MAP,))  # Generator, nur einmal iterierbar
    write_export(project, dest, optional_roles=roles, confirm_warnings=True)
    assert (dest / "height_map.png").is_file()


def test_existing_file_target_is_rejected_even_with_overwrite(tmp_path: Path) -> None:
    # Eine vorhandene Datei als Ziel darf NIE durch den Exportordner ersetzt werden.
    dest = tmp_path / "target"
    dest.write_text("wichtige Datei", encoding="utf-8")
    project = _color_project()
    with pytest.raises(ExportTargetNotDirectoryError):
        write_export(project, dest, overwrite=True)
    # Die Originaldatei bleibt unversehrt, kein Temp-Rest.
    assert dest.is_file() and dest.read_text(encoding="utf-8") == "wichtige Datei"
    assert not _temp_leftovers(tmp_path, dest)


def test_bit_depth_override_writes_16bit_height(tmp_path: Path) -> None:
    project = _color_project((2, 1))
    arr = np.zeros((1, 2, 4), dtype=np.uint8)
    arr[0, 1, :3] = 255
    arr[:, :, 3] = 255
    _add_height(project, Image.fromarray(arr, "RGBA"))
    dest = tmp_path / "export"
    write_export(
        project, dest, optional_roles=[LayerRole.HEIGHT_MAP],
        bit_depth=16, confirm_warnings=True)
    with Image.open(dest / "height_map.png") as img:
        assert img.mode in ("I;16", "I")


def test_validate_false_bypasses_checks(tmp_path: Path) -> None:
    project = _color_project()
    _add_gloss(project)  # hätte eine Warnung – wird mit validate=False übersprungen
    dest = tmp_path / "export"
    write_export(project, dest, validate=False)
    assert dest.is_dir()


def _temp_leftovers(parent: Path, dest: Path) -> list[Path]:
    """Übrig gebliebene Temp-/Backup-Verzeichnisse des Schreibvorgangs."""
    return [
        p
        for p in parent.iterdir()
        if p.name.startswith(f".{dest.name}.tmp-") or p.name.startswith(f".{dest.name}.bak-")
    ]
