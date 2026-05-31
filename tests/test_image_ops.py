"""Pure image operation tests that do not need a QApplication."""

import numpy as np
from PIL import Image

from bgremover.image_ops import (
    DEFAULT_SAVE_FORMAT,
    SAVE_FORMATS,
    crop_image,
    crop_size_for_ratio,
    ensure_save_extension,
    flip_image,
    normalize_save_format,
    remove_selection,
    replace_selection,
    rotate_image,
    round_corners,
    save_dialog_filter,
    save_image_file,
)
from bgremover.image_utils import pil_to_numpy


def test_remove_selection_makes_selected_pixels_transparent() -> None:
    img = Image.new("RGBA", (4, 4), (10, 20, 30, 255))
    arr = pil_to_numpy(img)
    mask = np.zeros((4, 4), dtype=bool)
    mask[1:3, 1:3] = True

    result = np.array(remove_selection(arr, mask))

    assert (result[1:3, 1:3, 3] == 0).all()
    assert result[0, 0, 3] == 255


def test_replace_selection_fills_selected_pixels() -> None:
    img = Image.new("RGBA", (4, 4), (10, 20, 30, 255))
    arr = pil_to_numpy(img)
    mask = np.zeros((4, 4), dtype=bool)
    mask[0:2, 0:2] = True

    result = np.array(replace_selection(arr, mask, (255, 0, 0)))

    assert result[0, 0].tolist() == [255, 0, 0, 255]
    assert result[3, 3].tolist() == [10, 20, 30, 255]


def test_save_image_file_composites_jpeg_alpha_on_white(tmp_path) -> None:
    out = tmp_path / "transparent.jpg"

    save_image_file(Image.new("RGBA", (8, 8), (200, 50, 50, 0)), out)

    saved = np.array(Image.open(out).convert("RGB"))
    assert (saved >= 250).all()


def test_save_image_file_preserves_tiff_alpha(tmp_path) -> None:
    out = tmp_path / "alpha.tiff"

    save_image_file(Image.new("RGBA", (8, 8), (0, 255, 0, 128)), out)

    saved = Image.open(out)
    assert saved.mode == "RGBA"
    assert (np.array(saved)[:, :, 3] == 128).all()


def test_round_corners_clamps_radius_and_clears_corner_alpha() -> None:
    result, radius = round_corners(Image.new("RGBA", (20, 20), (0, 0, 0, 255)), 50)
    arr = np.array(result)

    assert radius == 10
    assert arr[0, 0, 3] == 0
    assert arr[10, 10, 3] == 255


def test_rotate_and_flip_images() -> None:
    img = Image.new("RGBA", (4, 2), (0, 0, 0, 255))
    img.putpixel((0, 0), (255, 0, 0, 255))

    rotated = rotate_image(img, 90)
    flipped = flip_image(img, horizontal=True)

    assert rotated.size == (2, 4)
    assert flipped.getpixel((3, 0)) == (255, 0, 0, 255)


def test_crop_size_for_ratio_uses_largest_centered_crop() -> None:
    assert crop_size_for_ratio((40, 20), 1, 1) == (20, 20)
    assert crop_size_for_ratio((20, 40), 16, 9) == (20, 11)


def test_crop_image_can_apply_circle_alpha_mask() -> None:
    result = crop_image(
        Image.new("RGBA", (20, 20), (0, 0, 0, 255)),
        (0, 0, 20, 20),
        is_circle=True,
    )
    arr = np.array(result)

    assert arr[0, 0, 3] == 0
    assert arr[10, 10, 3] == 255


# ── Ausgabeformat-Modell (Fix #8) ──────────────────────────────────────

def test_normalize_save_format_falls_back_on_unknown() -> None:
    assert normalize_save_format("JPEG") == "JPEG"
    assert normalize_save_format("EXR") == DEFAULT_SAVE_FORMAT
    assert normalize_save_format(None) == DEFAULT_SAVE_FORMAT


def test_save_dialog_filter_lists_preferred_first_without_keyerror() -> None:
    # Unbekanntes preferred darf nicht mehr werfen (früher KeyError).
    flt = save_dialog_filter("EXR")
    assert flt.startswith(SAVE_FORMATS[DEFAULT_SAVE_FORMAT][0])
    # JPEG zuerst, alle vier Formate enthalten.
    jpeg = save_dialog_filter("JPEG")
    assert jpeg.startswith("JPEG (*.jpg)")
    assert jpeg.count(";;") == len(SAVE_FORMATS) - 1


def test_ensure_save_extension_appends_from_selected_filter() -> None:
    assert ensure_save_extension("/x/y", "JPEG (*.jpg)", "PNG") == "/x/y.jpg"
    assert ensure_save_extension("/x/y", "WebP (*.webp)", "PNG") == "/x/y.webp"


def test_ensure_save_extension_keeps_existing_suffix() -> None:
    assert ensure_save_extension("/x/y.png", "JPEG (*.jpg)", "PNG") == "/x/y.png"


def test_ensure_save_extension_uses_preferred_when_filter_unknown() -> None:
    # Kein zuordenbarer Filter → Default-Suffix des (normalisierten) preferred.
    assert ensure_save_extension("/x/y", "Alle (*)", "TIFF") == "/x/y.tif"
    assert ensure_save_extension("/x/y", "Alle (*)", "EXR") == "/x/y.png"
