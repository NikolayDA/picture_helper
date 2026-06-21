"""Qt-freie Höhen-Repräsentation und 2D-Visualisierung (#345).

Belegt das Fundament des Height-Map-Arbeitsbereichs (#344): die verlustfreie
Konvertierung Höhe ↔ Graustufen-Array (Konvention ``R==G==B==Höhe``,
``A==Deckung``), die Normalisierung beliebiger Werte auf den Höhenbereich, die
Canvas-Größen-Validierung und die 16-Bit-Erweiterbarkeit über ``max_value``.
"""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from bgremover.height_map import (
    HEIGHT_MAX_8BIT,
    HeightField,
    HeightMapError,
    height_to_layer,
    layer_to_gray_image,
    layer_to_height,
    normalize_to_height,
    validate_canvas_size,
)


def _gray_layer(values: np.ndarray, alpha: np.ndarray) -> Image.Image:
    """Baut eine graustufige RGBA-Ebene (``R==G==B==values``, ``A==alpha``)."""
    h, w = values.shape
    arr = np.empty((h, w, 4), dtype=np.uint8)
    for c in range(3):
        arr[:, :, c] = values
    arr[:, :, 3] = alpha
    return Image.fromarray(arr, "RGBA")


# ── Konvertierung Höhe ↔ Array ───────────────────────────────────────────


def test_layer_to_height_reads_red_as_height_and_alpha_as_coverage() -> None:
    values = np.array([[0, 64], [128, 255]], dtype=np.uint8)
    alpha = np.array([[255, 200], [10, 0]], dtype=np.uint8)
    field = layer_to_height(_gray_layer(values, alpha))

    assert field.values.dtype == np.uint16
    assert field.coverage.dtype == np.uint8
    assert field.max_value == HEIGHT_MAX_8BIT
    assert np.array_equal(field.values, values.astype(np.uint16))
    assert np.array_equal(field.coverage, alpha)


def test_layer_to_height_uses_red_channel_only() -> None:
    """Die Höhe stammt aus dem Rotkanal (Konvention ``R==G==B``)."""
    arr = np.zeros((2, 2, 4), dtype=np.uint8)
    arr[:, :, 0] = 90      # Rot = Höhe
    arr[:, :, 1] = 30      # abweichendes Grün
    arr[:, :, 2] = 60      # abweichendes Blau
    arr[:, :, 3] = 255
    field = layer_to_height(Image.fromarray(arr, "RGBA"))
    assert np.all(field.values == 90)


def test_layer_to_height_converts_non_rgba_input() -> None:
    field = layer_to_height(Image.new("L", (3, 2), 123))
    assert field.size == (3, 2)
    assert np.all(field.values == 123)
    assert np.all(field.coverage == 255)   # „L" → RGBA: Alpha voll deckend


def test_height_to_layer_produces_grayscale_rgba() -> None:
    values = np.array([[10, 200]], dtype=np.uint16)
    coverage = np.array([[255, 128]], dtype=np.uint8)
    layer = height_to_layer(HeightField(values, coverage))

    assert layer.mode == "RGBA"
    arr = np.array(layer)
    assert np.array_equal(arr[:, :, 0], arr[:, :, 1])   # R==G
    assert np.array_equal(arr[:, :, 1], arr[:, :, 2])   # G==B
    assert np.array_equal(arr[:, :, 0], values.astype(np.uint8))
    assert np.array_equal(arr[:, :, 3], coverage)


def test_round_trip_is_lossless_for_grayscale_layer() -> None:
    """``height_to_layer(layer_to_height(img))`` ist bitgenau ``img`` (Graustufe)."""
    rng = np.random.default_rng(42)
    values = rng.integers(0, 256, size=(7, 5), dtype=np.uint8)
    alpha = rng.integers(0, 256, size=(7, 5), dtype=np.uint8)
    original = _gray_layer(values, alpha)

    round_tripped = height_to_layer(layer_to_height(original))
    assert np.array_equal(np.array(original), np.array(round_tripped))


def test_layer_to_gray_image_forces_grayscale() -> None:
    """Der Anzeigepfad graustuft auch eine nicht-graue Ebene (G/B → Höhe=R)."""
    arr = np.zeros((2, 3, 4), dtype=np.uint8)
    arr[:, :, 0] = 77      # Rot = Höhe
    arr[:, :, 1] = 200     # wird verworfen
    arr[:, :, 2] = 5       # wird verworfen
    arr[:, :, 3] = 255
    out = np.array(layer_to_gray_image(Image.fromarray(arr, "RGBA")))
    assert np.all(out[:, :, 0] == 77)
    assert np.all(out[:, :, 1] == 77)
    assert np.all(out[:, :, 2] == 77)
    assert np.all(out[:, :, 3] == 255)


# ── 16-Bit-Erweiterbarkeit ───────────────────────────────────────────────


def test_height_to_layer_scales_down_higher_bit_depth() -> None:
    """Ein ``max_value`` > 255 (16-Bit-Pfad) wird linear auf 8-Bit-Grau skaliert."""
    values = np.array([[0, 511, 1023]], dtype=np.uint16)
    coverage = np.full((1, 3), 255, dtype=np.uint8)
    arr = np.array(height_to_layer(HeightField(values, coverage, max_value=1023)))
    assert list(arr[0, :, 0]) == [0, 127, 255]   # 0/255, 511*255/1023≈127, 1023→255


def test_height_field_rejects_value_above_max() -> None:
    values = np.array([[300]], dtype=np.uint16)
    coverage = np.array([[255]], dtype=np.uint8)
    with pytest.raises(HeightMapError):
        HeightField(values, coverage, max_value=255)


def test_height_field_rejects_shape_dtype_and_max_value() -> None:
    coverage = np.zeros((2, 2), dtype=np.uint8)
    with pytest.raises(HeightMapError):
        HeightField(np.zeros((2, 3), dtype=np.uint16), coverage)         # Form
    with pytest.raises(HeightMapError):
        HeightField(np.zeros((2, 2), dtype=np.uint8), coverage)          # dtype values
    with pytest.raises(HeightMapError):
        HeightField(np.zeros((2, 2), dtype=np.uint16),
                    np.zeros((2, 2), dtype=np.uint16))                    # dtype coverage
    with pytest.raises(HeightMapError):
        HeightField(np.zeros((2,), dtype=np.uint16),
                    np.zeros((2,), dtype=np.uint8))                       # nicht 2D
    with pytest.raises(HeightMapError):
        HeightField(np.zeros((1, 1), dtype=np.uint16),
                    np.zeros((1, 1), dtype=np.uint8), max_value=0)        # max_value


# ── Normalisierung ───────────────────────────────────────────────────────


def test_normalize_to_height_min_max_scaling() -> None:
    data = np.array([[10.0, 20.0], [30.0, 50.0]])
    out = normalize_to_height(data)
    assert out.dtype == np.uint16
    assert int(out.min()) == 0          # kleinstes Element → 0
    assert int(out.max()) == 255        # größtes Element → max_value
    # Linearität: 30 liegt bei (30-10)/(50-10)=0.5 → 128 (gerundet).
    assert out[1, 0] == 128


def test_normalize_to_height_constant_input_is_zero_field() -> None:
    out = normalize_to_height(np.full((3, 3), 7.0))
    assert out.shape == (3, 3)
    assert np.all(out == 0)


def test_normalize_to_height_custom_max_value() -> None:
    out = normalize_to_height(np.array([0.0, 1.0]), max_value=1023)
    assert list(out) == [0, 1023]


def test_normalize_to_height_rejects_empty_and_non_finite() -> None:
    with pytest.raises(HeightMapError):
        normalize_to_height(np.array([], dtype=np.float64))
    with pytest.raises(HeightMapError):
        normalize_to_height(np.array([1.0, np.nan]))
    with pytest.raises(HeightMapError):
        normalize_to_height(np.array([1.0, np.inf]))
    with pytest.raises(HeightMapError):
        normalize_to_height(np.array([1.0, 2.0]), max_value=0)


# ── Canvas-Größen-Validierung ────────────────────────────────────────────


def test_validate_canvas_size_accepts_matching_size() -> None:
    field = layer_to_height(Image.new("RGBA", (5, 3)))   # (W, H)
    assert field.size == (5, 3)
    validate_canvas_size(field, (5, 3))                  # kein Fehler


def test_validate_canvas_size_rejects_mismatch() -> None:
    field = layer_to_height(Image.new("RGBA", (5, 3)))
    with pytest.raises(HeightMapError):
        validate_canvas_size(field, (3, 5))
