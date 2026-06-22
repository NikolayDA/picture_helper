"""Qt-freie Tests für die EufyMake-Export-Planung (#352).

Deckt Rollen→Asset-Abbildung (Pflicht-/Optionalrollen), deterministische
Benennung/Profilversionierung, Metadatenableitung (physische Größe, DPI,
Bittiefe) inklusive Defaults sowie die strukturierten Fehler bei ungültigen
Werten ab. Reines Datenmodell – keine Pixel, keine Dateien, kein Qt.
"""
from __future__ import annotations

import math

import numpy as np
import pytest
from PIL import Image

from bgremover.eufymake_export import (
    DEFAULT_BIT_DEPTH,
    EXPORT_PROFILE,
    EXPORT_PROFILE_VERSION,
    HEIGHT_SEMANTICS,
    MM_PER_INCH,
    AssetPixelFormat,
    EufyMakeExportError,
    HeightSemantics,
    InvalidBitDepthError,
    InvalidPhysicalSizeError,
    MissingColorMotifError,
    OpenQuestion,
    build_export_plan,
)
from bgremover.project_model import (
    META_BIT_DEPTH,
    META_PHYSICAL_SIZE_MM,
    LayerKind,
    LayerRole,
    Project,
)


def _solid(size: tuple[int, int], color: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", size, color)


def _gray_layer_image(size: tuple[int, int], value: int) -> Image.Image:
    """Graustufige HEIGHT-Ebene (``R==G==B==Höhe``) zum Anlegen einer Höhenkarte."""
    arr = np.full((size[1], size[0], 4), (value, value, value, 255), dtype=np.uint8)
    return Image.fromarray(arr, "RGBA")


def _color_project(size: tuple[int, int] = (8, 4)) -> Project:
    """Projekt mit genau einer COLOR-Ebene (ohne explizite Rollen)."""
    project = Project(*size)
    project.create_layer(_solid(size, (10, 20, 30, 255)), name="Farbe")
    return project


# ── Farbmotiv: Pflicht-Asset ─────────────────────────────────────────────

def test_color_motif_falls_back_to_composite_without_role() -> None:
    plan = build_export_plan(_color_project())
    motif = plan.color_motif
    assert motif.role is LayerRole.COLOR_MOTIF
    assert motif.required is True
    assert motif.pixel_format is AssetPixelFormat.RGBA
    assert motif.bit_depth == DEFAULT_BIT_DEPTH
    # Ohne Rolle stammt das Motiv aus dem COLOR-Komposit.
    assert motif.source_layer_id is None
    assert motif.from_color_composite is True


def test_color_motif_uses_explicit_role_layer() -> None:
    project = _color_project()
    layer_id = project.layers[0].id
    project.assign_role(layer_id, LayerRole.COLOR_MOTIF)

    motif = build_export_plan(project).color_motif
    assert motif.source_layer_id == layer_id
    assert motif.from_color_composite is False


def test_missing_color_motif_raises_structured_error() -> None:
    # Projekt nur mit einer HEIGHT-Ebene: kein Farbmotiv ableitbar.
    project = Project(8, 4)
    project.create_layer(_gray_layer_image((8, 4), 128), name="Höhe", kind=LayerKind.HEIGHT)

    with pytest.raises(MissingColorMotifError):
        build_export_plan(project)


def test_empty_project_has_no_color_motif() -> None:
    with pytest.raises(MissingColorMotifError):
        build_export_plan(Project(8, 4))


# ── Optionale Rollen: Höhenkarte & Gloss-Maske ───────────────────────────

def test_height_and_gloss_absent_by_default() -> None:
    plan = build_export_plan(_color_project())
    assert plan.asset_for(LayerRole.HEIGHT_MAP) is None
    assert plan.asset_for(LayerRole.GLOSS_MASK) is None
    assert plan.optional_assets == ()
    # Nur das Farbmotiv ist vorhanden.
    assert len(plan.assets) == 1


def test_height_map_role_maps_to_optional_grayscale_asset() -> None:
    project = _color_project()
    height = project.create_layer(
        _gray_layer_image((8, 4), 200), name="Höhe", kind=LayerKind.HEIGHT
    )
    project.assign_role(height.id, LayerRole.HEIGHT_MAP)

    plan = build_export_plan(project)
    asset = plan.asset_for(LayerRole.HEIGHT_MAP)
    assert asset is not None
    assert asset.required is False
    assert asset.experimental is False
    assert asset.pixel_format is AssetPixelFormat.GRAYSCALE
    assert asset.source_layer_id == height.id
    assert OpenQuestion.HEIGHT_MAP_BIT_DEPTH in plan.open_questions


def test_gloss_mask_role_maps_to_experimental_optional_asset() -> None:
    project = _color_project()
    gloss = project.create_layer(
        _solid((8, 4), (255, 255, 255, 255)), name="Gloss", kind=LayerKind.GLOSS
    )
    project.assign_role(gloss.id, LayerRole.GLOSS_MASK)

    plan = build_export_plan(project)
    asset = plan.asset_for(LayerRole.GLOSS_MASK)
    assert asset is not None
    assert asset.required is False
    assert asset.experimental is True
    assert asset.pixel_format is AssetPixelFormat.GRAYSCALE
    assert OpenQuestion.GLOSS_MASK_SEMANTICS in plan.open_questions


# ── Deterministische Benennung & Reihenfolge ─────────────────────────────

def test_asset_filenames_are_deterministic_and_ordered() -> None:
    project = _color_project()
    height = project.create_layer(
        _gray_layer_image((8, 4), 100), name="Höhe", kind=LayerKind.HEIGHT
    )
    project.assign_role(height.id, LayerRole.HEIGHT_MAP)
    gloss = project.create_layer(
        _solid((8, 4), (255, 255, 255, 255)), name="Gloss", kind=LayerKind.GLOSS
    )
    project.assign_role(gloss.id, LayerRole.GLOSS_MASK)

    plan = build_export_plan(project)
    # Stabile Reihenfolge: Farbmotiv, Höhenkarte, Gloss-Maske.
    assert plan.filenames == ("color_motif.png", "height_map.png", "gloss_mask.png")
    assert [a.role for a in plan.assets] == [
        LayerRole.COLOR_MOTIF,
        LayerRole.HEIGHT_MAP,
        LayerRole.GLOSS_MASK,
    ]


def test_filenames_stable_across_repeated_builds() -> None:
    project = _color_project()
    assert build_export_plan(project).filenames == build_export_plan(project).filenames


# ── Profil- & Höhenvertrag ───────────────────────────────────────────────

def test_plan_carries_profile_and_version() -> None:
    plan = build_export_plan(_color_project())
    assert plan.profile == EXPORT_PROFILE
    assert plan.profile_version == EXPORT_PROFILE_VERSION
    assert isinstance(plan.profile_version, int)


def test_height_semantics_is_light_is_high() -> None:
    plan = build_export_plan(_color_project())
    assert plan.height_semantics is HeightSemantics.LIGHT_IS_HIGH
    assert plan.height_semantics is HEIGHT_SEMANTICS


def test_native_empf_is_always_an_open_question() -> None:
    # Der Plan plant nie ein natives .empf-Projekt – das bleibt explizit offen.
    plan = build_export_plan(_color_project())
    assert OpenQuestion.NATIVE_EMPF_PROJECT in plan.open_questions


# ── Metadatenableitung & Defaults ────────────────────────────────────────

def test_target_pixel_size_matches_canvas() -> None:
    plan = build_export_plan(_color_project((16, 9)))
    assert plan.target.pixel_size == (16, 9)


def test_bit_depth_defaults_when_metadata_absent() -> None:
    plan = build_export_plan(_color_project())
    assert plan.target.bit_depth == DEFAULT_BIT_DEPTH


def test_bit_depth_read_from_metadata() -> None:
    project = _color_project()
    project.metadata[META_BIT_DEPTH] = 16
    height = project.create_layer(
        _gray_layer_image((8, 4), 100), name="Höhe", kind=LayerKind.HEIGHT
    )
    project.assign_role(height.id, LayerRole.HEIGHT_MAP)

    plan = build_export_plan(project)
    assert plan.target.bit_depth == 16
    # Die Höhenkarte erbt die geplante Bittiefe, das Farbmotiv bleibt 8-Bit.
    assert plan.asset_for(LayerRole.HEIGHT_MAP).bit_depth == 16  # type: ignore[union-attr]
    assert plan.color_motif.bit_depth == DEFAULT_BIT_DEPTH


def test_physical_size_unknown_without_metadata() -> None:
    plan = build_export_plan(_color_project())
    assert plan.target.physical_size_mm is None
    assert plan.target.dpi is None


def test_physical_size_and_dpi_derived_from_metadata() -> None:
    project = _color_project((254, 127))
    project.metadata[META_PHYSICAL_SIZE_MM] = (50.8, 25.4)  # 2 in × 1 in

    plan = build_export_plan(project)
    assert plan.target.physical_size_mm == (50.8, 25.4)
    assert plan.target.dpi is not None
    dpi_x, dpi_y = plan.target.dpi
    # 254 px / 2 in = 127 dpi; 127 px / 1 in = 127 dpi.
    assert math.isclose(dpi_x, 127.0)
    assert math.isclose(dpi_y, 127.0)
    assert math.isclose(dpi_x, 254 * MM_PER_INCH / 50.8)


def test_physical_size_accepts_list_metadata() -> None:
    project = _color_project((100, 100))
    project.metadata[META_PHYSICAL_SIZE_MM] = [25.4, 25.4]
    plan = build_export_plan(project)
    assert plan.target.physical_size_mm == (25.4, 25.4)


# ── Ungültige Werte → strukturierte Fehler ───────────────────────────────

@pytest.mark.parametrize("bad", [0, 7, 24, -8, "8", 8.0, True])
def test_invalid_bit_depth_raises(bad: object) -> None:
    project = _color_project()
    project.metadata[META_BIT_DEPTH] = bad
    with pytest.raises(InvalidBitDepthError):
        build_export_plan(project)


@pytest.mark.parametrize(
    "bad",
    [
        (0.0, 10.0),
        (-1.0, 10.0),
        (10.0, 0.0),
        (10.0,),
        (10.0, 10.0, 10.0),
        "10x10",
        10.0,
        (float("inf"), 10.0),
        (float("nan"), 10.0),
        ("10", "10"),
        (True, 10.0),
    ],
)
def test_invalid_physical_size_raises(bad: object) -> None:
    project = _color_project()
    project.metadata[META_PHYSICAL_SIZE_MM] = bad
    with pytest.raises(InvalidPhysicalSizeError):
        build_export_plan(project)


def test_structured_errors_share_common_base() -> None:
    assert issubclass(MissingColorMotifError, EufyMakeExportError)
    assert issubclass(InvalidBitDepthError, EufyMakeExportError)
    assert issubclass(InvalidPhysicalSizeError, EufyMakeExportError)


# ── Unveränderlichkeit der DTOs ──────────────────────────────────────────

def test_plan_and_assets_are_frozen() -> None:
    plan = build_export_plan(_color_project())
    with pytest.raises(AttributeError):
        plan.profile = "x"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        plan.color_motif.filename = "x"  # type: ignore[misc]
