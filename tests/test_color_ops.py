"""Tests für die Qt-freie Farbkorrektur ``bgremover.color_ops`` (#360)."""
from __future__ import annotations

import numpy as np
from PIL import Image

from bgremover.color_ops import adjust_color


def _rng_rgba(seed: int = 0) -> Image.Image:
    arr = np.random.default_rng(seed).integers(0, 256, (8, 8, 4), dtype=np.uint8)
    return Image.fromarray(arr, "RGBA")


def test_neutral_values_are_bit_identical_noop() -> None:
    img = _rng_rgba()
    result = adjust_color(img)
    assert result is img   # echtes No-op (dasselbe Objekt)
    assert np.array_equal(np.asarray(result), np.asarray(img))
    # Auch explizit gesetzte Neutralwerte sind ein No-op.
    assert adjust_color(img, brightness=1.0, contrast=1.0, saturation=1.0) is img


def test_alpha_channel_is_preserved_exactly() -> None:
    img = _rng_rgba(1)
    out = adjust_color(img, brightness=1.4, contrast=1.6, saturation=0.2)
    assert np.array_equal(np.asarray(out)[:, :, 3], np.asarray(img)[:, :, 3])
    # RGB hat sich geändert (sonst wäre der Test wirkungslos).
    assert not np.array_equal(np.asarray(out)[:, :, :3], np.asarray(img)[:, :, :3])


def test_brightness_up_lightens() -> None:
    img = Image.new("RGBA", (4, 4), (100, 100, 100, 255))
    out = np.asarray(adjust_color(img, brightness=1.5))
    assert out[0, 0, :3].tolist() == [150, 150, 150]
    assert np.all(out[:, :, 3] == 255)


def test_brightness_down_darkens() -> None:
    img = Image.new("RGBA", (4, 4), (100, 100, 100, 255))
    out = np.asarray(adjust_color(img, brightness=0.5))
    assert out[0, 0, :3].tolist() == [50, 50, 50]


def test_contrast_up_spreads_around_mean() -> None:
    arr = np.zeros((4, 4, 4), dtype=np.uint8)
    arr[:, :, 3] = 255
    arr[:, :, 0] = arr[:, :, 1] = arr[:, :, 2] = np.array([[40, 80, 160, 200]] * 4)
    img = Image.fromarray(arr, "RGBA")
    before = np.asarray(img)[:, :, 0].astype(float).std()
    after = np.asarray(adjust_color(img, contrast=1.8))[:, :, 0].astype(float).std()
    assert after > before   # höherer Kontrast = größere Streuung


def test_saturation_zero_yields_grayscale_with_alpha_kept() -> None:
    arr = np.zeros((4, 4, 4), dtype=np.uint8)
    arr[:, :, 0] = 200
    arr[:, :, 1] = 50
    arr[:, :, 2] = 10
    arr[:, :, 3] = 123
    img = Image.fromarray(arr, "RGBA")
    out = np.asarray(adjust_color(img, saturation=0.0))
    assert np.array_equal(out[:, :, 0], out[:, :, 1])   # R==G==B → Graustufe
    assert np.array_equal(out[:, :, 1], out[:, :, 2])
    assert np.all(out[:, :, 3] == 123)                  # Alpha unverändert
