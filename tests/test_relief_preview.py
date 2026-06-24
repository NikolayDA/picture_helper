"""Deterministische Qt-freie Relief-Vorschau (#385)."""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

import bgremover.relief_preview as relief_module
from bgremover.height_map import HeightField
from bgremover.relief_preview import (
    NEUTRAL_SHADING,
    ReliefPreviewError,
    compose_over,
    relief_shading,
)


def _field(
    values: np.ndarray,
    *,
    max_value: int = 255,
    coverage: np.ndarray | None = None,
) -> HeightField:
    values16 = values.astype(np.uint16)
    if coverage is None:
        coverage = np.full(values16.shape, 255, dtype=np.uint8)
    return HeightField(values16, coverage, max_value=max_value)


def test_flat_field_is_exactly_neutral_for_every_pixel() -> None:
    field = _field(np.full((3, 4), 173))
    out = relief_shading(field, azimuth=315, elevation=37, strength=1.0)
    assert out.mode == "L"
    assert out.size == (4, 3)
    assert np.asarray(out).tolist() == [[128] * 4] * 3


def test_slope_changes_exact_pixels_with_light_direction() -> None:
    values = np.tile(np.array([0, 64, 128, 192, 255], dtype=np.uint16), (3, 1))
    field = _field(values)

    west = np.asarray(
        relief_shading(field, azimuth=270, elevation=45, strength=1.0)
    )
    east = np.asarray(
        relief_shading(field, azimuth=90, elevation=45, strength=1.0)
    )

    assert west.tolist() == [[147, 147, 147, 147, 147]] * 3
    assert east.tolist() == [[103, 103, 103, 104, 104]] * 3
    assert np.all(west > NEUTRAL_SHADING)
    assert np.all(east < NEUTRAL_SHADING)


def test_logically_equal_8_and_16_bit_fields_match() -> None:
    values8 = np.tile(np.array([0, 64, 128, 192, 255], dtype=np.uint16), (3, 1))
    values16 = values8.astype(np.uint32) * 257
    shade8 = relief_shading(
        _field(values8), azimuth=270, elevation=45, strength=1.0
    )
    shade16 = relief_shading(
        _field(values16, max_value=65535),
        azimuth=270,
        elevation=45,
        strength=1.0,
    )
    assert np.array_equal(np.asarray(shade8), np.asarray(shade16))


def test_zero_strength_and_zero_coverage_are_neutral() -> None:
    values = np.array([[0, 255], [255, 0]], dtype=np.uint16)
    field = _field(values)
    zero = relief_shading(field, azimuth=45, elevation=30, strength=0.0)
    assert np.all(np.asarray(zero) == NEUTRAL_SHADING)

    coverage = np.array([[0, 255], [0, 255]], dtype=np.uint8)
    covered = np.asarray(
        relief_shading(
            _field(values, coverage=coverage),
            azimuth=45,
            elevation=30,
            strength=1.0,
        )
    )
    assert covered[:, 0].tolist() == [NEUTRAL_SHADING, NEUTRAL_SHADING]
    assert np.any(covered[:, 1] != NEUTRAL_SHADING)


def test_compose_preserves_size_mode_and_alpha_exactly() -> None:
    base_arr = np.array(
        [[[100, 50, 20, 17], [100, 50, 20, 123], [100, 50, 20, 255]]],
        dtype=np.uint8,
    )
    base = Image.fromarray(base_arr, "RGBA")
    shading = Image.fromarray(np.array([[0, 128, 255]], dtype=np.uint8), "L")
    result = np.asarray(compose_over(base, shading, strength=1.0))

    assert result.tolist() == [
        [[0, 0, 0, 17], [100, 50, 20, 123], [199, 100, 40, 255]]
    ]
    assert result.shape == base_arr.shape
    assert np.array_equal(result[:, :, 3], base_arr[:, :, 3])


def test_compose_noops_return_original_object() -> None:
    base = Image.new("RGBA", (2, 1), (12, 34, 56, 78))
    neutral = Image.new("L", base.size, NEUTRAL_SHADING)
    directional = Image.new("L", base.size, 255)
    assert compose_over(base, neutral, strength=1.0) is base
    assert compose_over(base, directional, strength=0.0) is base


@pytest.mark.parametrize("strength", [-0.01, 1.01, float("nan"), float("inf")])
def test_invalid_strength_is_rejected(strength: float) -> None:
    field = _field(np.array([[0, 255]]))
    with pytest.raises(ReliefPreviewError):
        relief_shading(field, azimuth=315, elevation=45, strength=strength)


@pytest.mark.parametrize("elevation", [-1.0, 91.0, float("nan")])
def test_invalid_elevation_is_rejected(elevation: float) -> None:
    field = _field(np.array([[0, 255]]))
    with pytest.raises(ReliefPreviewError):
        relief_shading(field, azimuth=315, elevation=elevation, strength=1.0)


def test_compose_rejects_non_rgba_base_and_size_mismatch() -> None:
    with pytest.raises(ReliefPreviewError):
        compose_over(
            Image.new("RGB", (2, 2)), Image.new("L", (2, 2)), strength=1.0
        )
    with pytest.raises(ReliefPreviewError):
        compose_over(
            Image.new("RGBA", (2, 2)), Image.new("L", (1, 2)), strength=1.0
        )


def test_module_is_qt_free() -> None:
    tree = ast.parse(Path(relief_module.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    assert not any(
        name.split(".")[0] in {"PyQt6", "PyQt5", "PySide6"} for name in imported
    )
