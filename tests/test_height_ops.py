"""Höhen-Optimierung: reine, deterministische Operationen (#348).

Pixel-Asserts für Tonwert (Levels/Gamma), Glättung (Gauß/Median), Schwelle,
Stufenreduzierung und Höhenbereich-Clamp – inkl. 16-Bit-Tauglichkeit
(``max_value`` != 255) und Unveränderlichkeit der Eingabe.
"""
from __future__ import annotations

import numpy as np
import pytest

from bgremover.height_map import HeightField, HeightMapError
from bgremover.height_ops import (
    clamp_range,
    gamma,
    gaussian_blur,
    levels,
    median_blur,
    quantize,
    threshold,
)


def _field(values: list[list[int]], *, max_value: int = 255, coverage: int = 200) -> HeightField:
    arr = np.array(values, dtype=np.uint16)
    cov = np.full(arr.shape, coverage, dtype=np.uint8)
    return HeightField(arr, cov, max_value=max_value)


# ── Tonwert ──────────────────────────────────────────────────────────────


def test_levels_linear_remap() -> None:
    out = levels(_field([[32, 64, 128, 192, 224]]), black=64, white=192)
    assert list(out.values[0]) == [0, 0, 128, 255, 255]   # 128 → 0.5*255 = 127.5 → 128
    assert np.all(out.coverage == 200)                    # Deckung unberührt


def test_levels_rejects_invalid_points() -> None:
    with pytest.raises(HeightMapError):
        levels(_field([[0]]), black=200, white=100)
    with pytest.raises(HeightMapError):
        levels(_field([[0]]), black=0, white=300)


def test_gamma_curve() -> None:
    out = gamma(_field([[0, 51, 255]]), 2.0)
    assert list(out.values[0]) == [0, 10, 255]            # (51/255)^2*255 = 10.2 → 10


def test_gamma_rejects_non_positive() -> None:
    with pytest.raises(HeightMapError):
        gamma(_field([[0]]), 0.0)


# ── Glättung ─────────────────────────────────────────────────────────────


def test_gaussian_preserves_constant() -> None:
    field = _field([[120] * 4] * 4)
    out = gaussian_blur(field, sigma=1.5)
    assert np.all(out.values == 120)                      # Reflexion + normierter Kernel


def test_gaussian_is_symmetric_and_spreads_impulse() -> None:
    arr = np.zeros((5, 5), dtype=np.uint16)
    arr[2, 2] = 255
    field = HeightField(arr, np.full((5, 5), 255, np.uint8))
    out = gaussian_blur(field, sigma=1.0).values
    assert out[2, 2] < 255                                # Zentrum verteilt sich
    assert out[2, 1] == out[2, 3] == out[1, 2] == out[3, 2] > 0   # 4-fach symmetrisch


def test_gaussian_is_deterministic() -> None:
    field = _field([[10, 200, 30], [40, 50, 250], [5, 90, 120]])
    assert np.array_equal(gaussian_blur(field, 1.2).values, gaussian_blur(field, 1.2).values)


def test_gaussian_rejects_non_positive_sigma() -> None:
    with pytest.raises(HeightMapError):
        gaussian_blur(_field([[0]]), 0.0)


def test_median_removes_outlier_and_preserves_constant() -> None:
    arr = np.full((3, 3), 50, dtype=np.uint16)
    arr[1, 1] = 250                                       # Ausreißer
    field = HeightField(arr, np.full((3, 3), 255, np.uint8))
    out = median_blur(field, radius=1).values
    assert out[1, 1] == 50                                # Median tilgt den Ausreißer
    assert np.all(median_blur(_field([[70] * 3] * 3), 1).values == 70)


def test_median_rejects_radius_below_one() -> None:
    with pytest.raises(HeightMapError):
        median_blur(_field([[0]]), 0)


# ── Begrenzung / Stufen ──────────────────────────────────────────────────


def test_threshold_binary() -> None:
    out = threshold(_field([[0, 99, 100, 200]]), 100)
    assert list(out.values[0]) == [0, 0, 255, 255]


def test_threshold_rejects_out_of_range() -> None:
    with pytest.raises(HeightMapError):
        threshold(_field([[0]]), 300)


def test_quantize_steps() -> None:
    out = quantize(_field([[0, 100, 200, 255]]), steps=2)
    assert list(out.values[0]) == [0, 0, 255, 255]        # 2 Stufen → 0/255
    out3 = quantize(_field([[0, 128, 255]]), steps=3)
    assert list(out3.values[0]) == [0, 128, 255]          # 3 Stufen → 0/128/255


def test_quantize_rejects_too_few_steps() -> None:
    with pytest.raises(HeightMapError):
        quantize(_field([[0]]), 1)


def test_clamp_range_clips_without_stretch() -> None:
    out = clamp_range(_field([[10, 128, 250]]), 50, 200)
    assert list(out.values[0]) == [50, 128, 200]


def test_clamp_range_rejects_invalid_bounds() -> None:
    with pytest.raises(HeightMapError):
        clamp_range(_field([[0]]), 200, 100)


# ── 16-Bit-Tauglichkeit & Unveränderlichkeit ─────────────────────────────


def test_ops_are_16bit_capable() -> None:
    """Operationen rechnen im Bereich ``0..max_value`` (hier 1023)."""
    field = _field([[0, 512, 1023]], max_value=1023)
    assert list(levels(field, 0, 1023).values[0]) == [0, 512, 1023]
    assert list(threshold(field, 700).values[0]) == [0, 0, 1023]   # 512<700<=1023
    assert list(quantize(field, 2).values[0]) == [0, 1023, 1023]   # 512/1023>0.5→round 1
    assert list(clamp_range(field, 100, 800).values[0]) == [100, 512, 800]


def test_ops_do_not_mutate_input() -> None:
    field = _field([[10, 200, 30]])
    before = field.values.copy()
    levels(field, 20, 180)
    gamma(field, 1.5)
    gaussian_blur(field, 1.0)
    median_blur(field, 1)
    threshold(field, 100)
    quantize(field, 4)
    clamp_range(field, 20, 180)
    assert np.array_equal(field.values, before)
