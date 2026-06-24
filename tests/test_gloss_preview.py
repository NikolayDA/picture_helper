"""Deterministische Qt-freie Gloss-Vorschau (#386)."""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

import bgremover.gloss_preview as gloss_module
from bgremover.gloss_preview import (
    GLOSS_MAX_ALPHA,
    GLOSS_TINT,
    GlossPreviewError,
    compose_over,
    gloss_overlay,
)


def test_gloss_mask_produces_exact_visible_overlay() -> None:
    gloss = Image.fromarray(np.array([[0, 128, 255]], dtype=np.uint8), "L")
    overlay = np.asarray(gloss_overlay(gloss, intensity=1.0))
    assert overlay.tolist() == [
        [
            [*GLOSS_TINT, 0],
            [*GLOSS_TINT, 96],
            [*GLOSS_TINT, GLOSS_MAX_ALPHA],
        ]
    ]


def test_zero_mask_and_zero_intensity_are_transparent_noops() -> None:
    black = Image.new("L", (2, 2), 0)
    white = Image.new("L", (2, 2), 255)
    assert not np.any(np.asarray(gloss_overlay(black, intensity=1.0))[:, :, 3])
    assert not np.any(np.asarray(gloss_overlay(white, intensity=0.0))[:, :, 3])

    base = Image.new("RGBA", (2, 2), (12, 34, 56, 78))
    assert compose_over(base, gloss_overlay(black, intensity=1.0), intensity=1.0) is base
    assert compose_over(base, gloss_overlay(white, intensity=1.0), intensity=0.0) is base


def test_source_alpha_limits_gloss_visibility() -> None:
    source = np.array([[[255, 255, 255, 0], [255, 255, 255, 128]]], dtype=np.uint8)
    overlay = np.asarray(gloss_overlay(Image.fromarray(source, "RGBA"), intensity=1.0))
    assert overlay[0, :, 3].tolist() == [0, 96]


def test_16_bit_gloss_mask_uses_full_value_range() -> None:
    values = np.array([[0, 32768, 65535]], dtype=np.uint16)
    overlay = np.asarray(
        gloss_overlay(Image.fromarray(values), intensity=1.0)
    )
    assert overlay[0, :, 3].tolist() == [0, 96, GLOSS_MAX_ALPHA]


def test_compose_is_visible_and_preserves_base_alpha_exactly() -> None:
    base_arr = np.array(
        [[[0, 0, 0, 17], [0, 0, 0, 123], [0, 0, 0, 255]]], dtype=np.uint8
    )
    base = Image.fromarray(base_arr, "RGBA")
    mask = Image.fromarray(np.array([[0, 128, 255]], dtype=np.uint8), "L")
    result = np.asarray(
        compose_over(base, gloss_overlay(mask, intensity=1.0), intensity=1.0)
    )

    assert result.tolist() == [
        [[0, 0, 0, 17], [79, 90, 96, 123], [158, 181, 192, 255]]
    ]
    assert result.shape == base_arr.shape
    assert np.array_equal(result[:, :, 3], base_arr[:, :, 3])


def test_compose_intensity_scales_overlay() -> None:
    base = Image.new("RGBA", (1, 1), (0, 0, 0, 77))
    overlay = Image.new("RGBA", (1, 1), (*GLOSS_TINT, 255))
    result = np.asarray(compose_over(base, overlay, intensity=0.5))
    assert result[0, 0].tolist() == [105, 120, 128, 77]


@pytest.mark.parametrize("intensity", [-0.01, 1.01, float("nan"), float("inf")])
def test_invalid_intensity_is_rejected(intensity: float) -> None:
    with pytest.raises(GlossPreviewError):
        gloss_overlay(Image.new("L", (1, 1)), intensity=intensity)


def test_compose_rejects_non_rgba_base_and_size_mismatch() -> None:
    with pytest.raises(GlossPreviewError):
        compose_over(
            Image.new("RGB", (2, 2)), Image.new("RGBA", (2, 2)), intensity=1.0
        )
    with pytest.raises(GlossPreviewError):
        compose_over(
            Image.new("RGBA", (2, 2)), Image.new("RGBA", (1, 2)), intensity=1.0
        )


def test_module_is_qt_free() -> None:
    tree = ast.parse(Path(gloss_module.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    assert not any(
        name.split(".")[0] in {"PyQt6", "PyQt5", "PySide6"} for name in imported
    )
