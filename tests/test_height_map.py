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
    HEIGHT_MAX_16BIT,
    LUMA_WEIGHTS_REC601,
    HeightField,
    HeightMapError,
    adjust_height,
    expand_to_16bit,
    generate_from_image,
    height_to_layer,
    invert_height,
    layer_to_gray_image,
    layer_to_height,
    normalize_to_height,
    resize_height_field,
    set_height,
    validate_canvas_size,
)


def _rgba(pixel: tuple[int, int, int, int], size: tuple[int, int] = (2, 2)) -> Image.Image:
    """Einfarbiges RGBA-Bild für deterministische Erzeugungs-Asserts."""
    return Image.new("RGBA", size, pixel)


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
    """Ein 16-Bit-Feld wird per ``rint(v16 / 257)`` auf 8-Bit-Grau skaliert (ADR #586)."""
    values = np.array([[0, 1, 32768, 65534, 65535]], dtype=np.uint16)
    coverage = np.full((1, 5), 255, dtype=np.uint8)
    arr = np.array(height_to_layer(HeightField(values, coverage, max_value=65535)))
    assert list(arr[0, :, 0]) == [0, 0, 128, 255, 255]   # Beispieltabelle des ADR


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


# ── Erzeugung aus Bild (#346) ────────────────────────────────────────────


def test_generate_channel_weighting_is_deterministic() -> None:
    """Reine Kanalgewichtung: (1,0,0)→R, (0,1,0)→G, (0,0,1)→B."""
    px = _rgba((200, 50, 10, 255))
    assert np.all(generate_from_image(px, weights=(1, 0, 0)).values == 200)
    assert np.all(generate_from_image(px, weights=(0, 1, 0)).values == 50)
    assert np.all(generate_from_image(px, weights=(0, 0, 1)).values == 10)


def test_generate_default_luma_rec601() -> None:
    """Standardgewichte sind Rec.-601-Luma (Summe 1.0)."""
    field = generate_from_image(_rgba((100, 150, 200, 255)))
    assert field.max_value == HEIGHT_MAX_8BIT
    assert np.all(field.values == 141)   # rint(100*.299 + 150*.587 + 200*.114)
    # Reine Graustufe (R==G==B) ergibt exakt ihren Grauwert (Import-Pfad).
    assert np.all(generate_from_image(_rgba((90, 90, 90, 255))).values == 90)


def test_generate_tone_curve_levels() -> None:
    """Schwarz-/Weißpunkt remappt linear: black→0, white→255, Mitte→128."""
    w = (1, 0, 0)
    assert np.all(generate_from_image(_rgba((64, 0, 0, 255)), weights=w, black=64, white=192).values == 0)
    assert np.all(generate_from_image(_rgba((192, 0, 0, 255)), weights=w, black=64, white=192).values == 255)
    assert np.all(generate_from_image(_rgba((128, 0, 0, 255)), weights=w, black=64, white=192).values == 128)


def test_generate_gamma() -> None:
    """Gamma wirkt auf den normierten Wert: 0.2 ** 2 * 255 = 10.2 → 10."""
    field = generate_from_image(_rgba((51, 0, 0, 255)), weights=(1, 0, 0), gamma=2.0)
    assert np.all(field.values == 10)


def test_generate_invert() -> None:
    """Invertieren spiegelt die Höhe (0.2 → 0.8 → 204)."""
    field = generate_from_image(_rgba((51, 0, 0, 255)), weights=(1, 0, 0), invert=True)
    assert np.all(field.values == 204)


def test_generate_preserves_alpha_as_coverage() -> None:
    field = generate_from_image(_rgba((255, 255, 255, 128)))
    assert np.all(field.coverage == 128)
    assert np.all(field.values == 255)


def test_generate_rejects_invalid_params() -> None:
    px = _rgba((10, 20, 30, 255))
    with pytest.raises(HeightMapError):
        generate_from_image(px, weights=(0, 0, 0))         # Summe 0
    with pytest.raises(HeightMapError):
        generate_from_image(px, weights=(-1, 1, 1))        # negativ
    with pytest.raises(HeightMapError):
        generate_from_image(px, weights=(1, 1))            # nicht drei Werte
    with pytest.raises(HeightMapError):
        generate_from_image(px, black=200, white=100)      # black >= white
    with pytest.raises(HeightMapError):
        generate_from_image(px, gamma=0.0)                 # gamma <= 0
    with pytest.raises(HeightMapError):
        generate_from_image(px, max_value=0)               # max_value <= 0


def test_generate_default_weights_constant_is_rec601() -> None:
    assert LUMA_WEIGHTS_REC601 == (0.299, 0.587, 0.114)
    assert sum(LUMA_WEIGHTS_REC601) == pytest.approx(1.0)


# ── Editier-Operationen: Aufhellen/Abdunkeln/Setzen/Invertieren (#347) ────


def _field(values: list[list[int]], coverage: int = 255) -> HeightField:
    arr = np.array(values, dtype=np.uint16)
    cov = np.full(arr.shape, coverage, dtype=np.uint8)
    return HeightField(arr, cov)


def test_adjust_height_lighten_and_clamp() -> None:
    field = _field([[100, 200]])
    out = adjust_height(field, 100)
    assert list(out.values[0]) == [200, 255]   # 300 → geklemmt auf 255
    assert np.array_equal(out.coverage, field.coverage)


def test_adjust_height_darken_and_clamp() -> None:
    out = adjust_height(_field([[100, 40]]), -80)
    assert list(out.values[0]) == [20, 0]       # -40 → geklemmt auf 0


def test_adjust_height_respects_mask() -> None:
    field = _field([[100, 100]])
    mask = np.array([[True, False]])
    out = adjust_height(field, 50, mask=mask)
    assert list(out.values[0]) == [150, 100]    # nur maskiertes Pixel verändert


def test_set_height_global_and_masked() -> None:
    assert np.all(set_height(_field([[10, 20]]), 200).values == 200)
    out = set_height(_field([[10, 20]]), 200, mask=np.array([[False, True]]))
    assert list(out.values[0]) == [10, 200]


def test_set_height_rejects_out_of_range() -> None:
    with pytest.raises(HeightMapError):
        set_height(_field([[0]]), 300)
    with pytest.raises(HeightMapError):
        set_height(_field([[0]]), -1)


def test_invert_height_is_lossless() -> None:
    field = _field([[0, 64, 200, 255]])
    once = invert_height(field)
    assert list(once.values[0]) == [255, 191, 55, 0]
    twice = invert_height(once)
    assert np.array_equal(twice.values, field.values)   # verlustfrei


def test_invert_height_masked() -> None:
    out = invert_height(_field([[0, 0]]), mask=np.array([[True, False]]))
    assert list(out.values[0]) == [255, 0]


def test_height_edit_does_not_mutate_input() -> None:
    field = _field([[100, 100]])
    adjust_height(field, 50)
    set_height(field, 0)
    invert_height(field)
    assert list(field.values[0]) == [100, 100]   # Eingabe unverändert


def test_height_edit_validates_mask_shape_and_dtype() -> None:
    field = _field([[10, 20]])
    with pytest.raises(HeightMapError):
        adjust_height(field, 10, mask=np.array([[True]]))            # Form
    with pytest.raises(HeightMapError):
        invert_height(field, mask=np.array([[1, 0]], dtype=np.uint8))  # dtype


# ── Canvas-Größen-Validierung ────────────────────────────────────────────


def test_validate_canvas_size_accepts_matching_size() -> None:
    field = layer_to_height(Image.new("RGBA", (5, 3)))   # (W, H)
    assert field.size == (5, 3)
    validate_canvas_size(field, (5, 3))                  # kein Fehler


def test_validate_canvas_size_rejects_mismatch() -> None:
    field = layer_to_height(Image.new("RGBA", (5, 3)))
    with pytest.raises(HeightMapError):
        validate_canvas_size(field, (3, 5))


# ── 16-Bit-Vertrag: Whitelist, Write-Lock, Migration, Resize (#587) ──────


def test_height_field_rejects_non_contract_max_value() -> None:
    """Nur die Vertragswerte 255 und 65535 sind erlaubt (ADR #586)."""
    values = np.zeros((1, 1), dtype=np.uint16)
    coverage = np.zeros((1, 1), dtype=np.uint8)
    for bad in (0, -1, 1, 254, 256, 1023, 4095, 65534, 65536):
        with pytest.raises(HeightMapError):
            HeightField(values.copy(), coverage.copy(), max_value=bad)
    HeightField(values.copy(), coverage.copy(), max_value=HEIGHT_MAX_8BIT)
    HeightField(values.copy(), coverage.copy(), max_value=HEIGHT_MAX_16BIT)


def test_height_field_accepts_full_16bit_boundary_values() -> None:
    """Grenzwerte des Vertrags konstruieren und lesen verlustfrei."""
    values = np.array([[0, 1, 255, 256, 32767, 65534, 65535]], dtype=np.uint16)
    coverage = np.full(values.shape, 255, dtype=np.uint8)
    field = HeightField(values, coverage, max_value=HEIGHT_MAX_16BIT)
    assert list(field.values[0]) == [0, 1, 255, 256, 32767, 65534, 65535]


def test_height_field_arrays_are_write_locked() -> None:
    """Aliasing-Verstöße schlagen hart fehl (ADR #586, Abschnitt 5)."""
    values = np.zeros((2, 2), dtype=np.uint16)
    coverage = np.zeros((2, 2), dtype=np.uint8)
    field = HeightField(values, coverage)
    with pytest.raises(ValueError):
        field.values[0, 0] = 1
    with pytest.raises(ValueError):
        field.coverage[0, 0] = 1
    # Auch das ursprünglich übergebene Array ist gesperrt (gleicher Puffer).
    with pytest.raises(ValueError):
        values[0, 0] = 1
    # Kopien sind dagegen normal beschreibbar (Ersetzen-statt-Mutieren-Vertrag).
    writable = field.values.copy()
    writable[0, 0] = 1


def test_expand_to_16bit_matches_adr_table_and_roundtrips() -> None:
    """``v16 = v8 × 257`` gemäß Beispieltabelle; Rückweg über die Ansicht exakt."""
    values = np.array([[0, 1, 128, 254, 255]], dtype=np.uint16)
    coverage = np.array([[0, 1, 128, 254, 255]], dtype=np.uint8)
    legacy = HeightField(values, coverage, max_value=HEIGHT_MAX_8BIT)
    out = expand_to_16bit(legacy)
    assert out.max_value == HEIGHT_MAX_16BIT
    assert out.values.dtype == np.uint16
    assert list(out.values[0]) == [0, 257, 32896, 65278, 65535]
    # Deckung bleibt wertgleich (orthogonal zur Höhe).
    assert np.array_equal(out.coverage, legacy.coverage)
    # Rückweg (16→8-Ansicht) reproduziert alle 256 Stufen exakt.
    full = HeightField(
        np.arange(256, dtype=np.uint16).reshape(16, 16),
        np.full((16, 16), 255, dtype=np.uint8),
    )
    round_tripped = np.array(height_to_layer(expand_to_16bit(full)))[:, :, 0]
    assert np.array_equal(round_tripped, np.arange(256, dtype=np.uint8).reshape(16, 16))


def test_expand_to_16bit_is_identity_for_canonical_fields() -> None:
    field = HeightField(
        np.array([[4660]], dtype=np.uint16),   # 0x1234: bewusst gesetzte Niederbits
        np.array([[255]], dtype=np.uint8),
        max_value=HEIGHT_MAX_16BIT,
    )
    assert expand_to_16bit(field) is field


def test_resize_height_field_keeps_uint16_and_low_bits_nearest() -> None:
    """NEAREST-Resize repliziert Werte exakt – inklusive Niederbits (0x1234)."""
    values = np.array([[0x1234, 0x0001], [0xFFFE, 0x8000]], dtype=np.uint16)
    coverage = np.array([[255, 0], [7, 255]], dtype=np.uint8)
    field = HeightField(values, coverage, max_value=HEIGHT_MAX_16BIT)
    out = resize_height_field(field, 4, 4, resample=Image.Resampling.NEAREST)
    assert out.values.dtype == np.uint16
    assert out.max_value == HEIGHT_MAX_16BIT
    assert out.size == (4, 4)
    assert np.array_equal(out.values, np.repeat(np.repeat(values, 2, axis=0), 2, axis=1))
    assert np.array_equal(
        out.coverage, np.repeat(np.repeat(coverage, 2, axis=0), 2, axis=1))


def test_resize_height_field_interpolates_in_float_without_8bit_step() -> None:
    """Bilinear: Ergebnis entspricht der float-Interpolation, nicht einer 8-Bit-Stufe."""
    values = np.array([[0, 257]], dtype=np.uint16)      # zwei benachbarte 16-Bit-Stufen
    coverage = np.full((1, 2), 255, dtype=np.uint8)
    field = HeightField(values, coverage, max_value=HEIGHT_MAX_16BIT)
    out = resize_height_field(field, 4, 1, resample=Image.Resampling.BILINEAR)
    # Alle Zwischenwerte liegen im Intervall [0, 257] – eine 8-Bit-Pipeline
    # (rint(v/257) vor der Interpolation) könnte nur 0 oder 257 liefern.
    assert out.values.dtype == np.uint16
    assert int(out.values.min()) >= 0 and int(out.values.max()) <= 257
    assert any(0 < v < 257 for v in out.values[0])


def test_resize_height_field_same_size_is_identity() -> None:
    field = HeightField(
        np.array([[1, 2]], dtype=np.uint16), np.array([[3, 4]], dtype=np.uint8))
    assert resize_height_field(field, 2, 1) is field


def test_resize_height_field_rejects_nonpositive_target() -> None:
    field = HeightField(
        np.zeros((1, 1), dtype=np.uint16), np.zeros((1, 1), dtype=np.uint8))
    with pytest.raises(HeightMapError):
        resize_height_field(field, 0, 4)
    with pytest.raises(HeightMapError):
        resize_height_field(field, 4, -1)


def test_generate_from_image_rejects_non_contract_max_value() -> None:
    with pytest.raises(HeightMapError):
        generate_from_image(_rgba((10, 10, 10, 255)), max_value=1023)


def test_generate_from_image_16bit_target_scales_full_range() -> None:
    """Erzeugung direkt auf den 16-Bit-Vertrag: Weiß → 65535, Schwarz → 0."""
    img = Image.new("RGBA", (1, 2))
    img.putpixel((0, 0), (0, 0, 0, 255))
    img.putpixel((0, 1), (255, 255, 255, 255))
    field = generate_from_image(img, max_value=HEIGHT_MAX_16BIT)
    assert field.max_value == HEIGHT_MAX_16BIT
    assert int(field.values[0, 0]) == 0
    assert int(field.values[1, 0]) == HEIGHT_MAX_16BIT
