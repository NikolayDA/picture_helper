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
    _MEDIAN_MAX_TEMP_BYTES,
    _median_band_rows,
    clamp_range,
    gamma,
    gaussian_blur,
    levels,
    median_blur,
    quantize,
    threshold,
)


def _median_reference(arr: np.ndarray, radius: int) -> np.ndarray:
    """Frühere Vollstapel-Median-Implementierung – Referenz für die Äquivalenz."""
    padded = np.pad(arr, radius, mode="reflect")
    h, w = arr.shape[:2]
    windows = [
        padded[dy:dy + h, dx:dx + w]
        for dy in range(2 * radius + 1)
        for dx in range(2 * radius + 1)
    ]
    return np.median(np.stack(windows, axis=0), axis=0)


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


# ── Speicherbeschränkter Median (#365) ────────────────────────────────────


@pytest.mark.parametrize("radius", [1, 2, 3, 5, 8, 10])
def test_median_matches_full_stack_reference_all_radii(radius: int) -> None:
    """Bitgenaue Gleichheit zur früheren Vollstapel-Variante über alle UI-Radien."""
    rng = np.random.default_rng(radius)
    arr = rng.integers(0, 256, size=(17, 23), dtype=np.uint16)
    field = HeightField(arr, np.full(arr.shape, 200, np.uint8))
    expected = _median_reference(arr, radius)
    out = median_blur(field, radius).values
    assert np.array_equal(out, np.clip(np.rint(expected), 0, 255).astype(np.uint16))


def test_median_band_split_is_independent_of_band_size() -> None:
    """Sehr kleines Budget erzwingt viele Bänder – Ergebnis bleibt identisch,
    auch über die Bandgrenzen hinweg (Höhe kein Vielfaches der Bandbreite)."""
    rng = np.random.default_rng(7)
    arr = rng.integers(0, 65536, size=(31, 19), dtype=np.uint16)
    field = HeightField(arr, np.full(arr.shape, 255, np.uint8), max_value=65535)
    full = median_blur(field, radius=3)                       # Standardbudget
    tiny = median_blur(field, radius=3, max_temp_bytes=1)     # erzwingt band_rows=1
    assert np.array_equal(full.values, tiny.values)
    # Referenz bestätigt zusätzlich die Korrektheit beider Wege.
    expected = np.clip(np.rint(_median_reference(arr, 3)), 0, 65535).astype(np.uint16)
    assert np.array_equal(tiny.values, expected)


def test_median_band_rows_stays_within_budget_at_40mp_radius10() -> None:
    """Worst Case der 40-MP-Hülle: der Fensterstapel je Band bleibt im Budget."""
    width = height = 6325                                      # ~40,0 MP, quadratisch
    radius = 10                                                # UI-Maximum
    band_rows = _median_band_rows(width, radius, _MEDIAN_MAX_TEMP_BYTES)
    assert band_rows >= 1
    stack_bytes = (2 * radius + 1) ** 2 * band_rows * width * 2
    assert stack_bytes <= _MEDIAN_MAX_TEMP_BYTES
    # Die alte Vollstapel-Variante hätte hier zweistellige GiB belegt.
    full_stack_bytes = (2 * radius + 1) ** 2 * height * width * 2
    assert full_stack_bytes > 30 * 1024**3


def test_median_handles_multi_band_large_input_bounded() -> None:
    """Mehr-Band-Lauf auf größerem Bild mit UI-Maximalradius bleibt korrekt.

    Kleines Budget erzwingt viele Bänder; bei Erfolg ist die Operation
    speicherbeschränkt durchgelaufen (der Vollstapel wäre ~0,8 GiB groß)."""
    rng = np.random.default_rng(123)
    arr = rng.integers(0, 256, size=(200, 150), dtype=np.uint16)
    field = HeightField(arr, np.full(arr.shape, 255, np.uint8))
    out = median_blur(field, radius=10, max_temp_bytes=256 * 1024)
    assert out.values.shape == (200, 150)
    expected = np.clip(np.rint(_median_reference(arr, 10)), 0, 255).astype(np.uint16)
    assert np.array_equal(out.values, expected)


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
    """Operationen rechnen im Bereich ``0..max_value`` (kanonisch 65535, ADR #586)."""
    field = _field([[0, 32768, 65535]], max_value=65535)
    assert list(levels(field, 0, 65535).values[0]) == [0, 32768, 65535]
    assert list(threshold(field, 40000).values[0]) == [0, 0, 65535]  # 32768<40000<=65535
    # 32768/65535 > 0.5 → Stufe 1 von 2.
    assert list(quantize(field, 2).values[0]) == [0, 65535, 65535]
    assert list(clamp_range(field, 100, 50000).values[0]) == [100, 32768, 50000]


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
