"""Pure image operation tests that do not need a QApplication."""

import numpy as np
import pytest
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
    rotated_size,
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


def test_save_image_file_overwrites_existing_atomically(tmp_path) -> None:
    out = tmp_path / "pic.png"
    save_image_file(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), out)
    save_image_file(Image.new("RGBA", (4, 4), (0, 255, 0, 255)), out)

    with Image.open(out) as saved:
        assert saved.convert("RGBA").getpixel((0, 0)) == (0, 255, 0, 255)
    # Nach erfolgreichem os.replace bleibt keine .pic.png.*-Zwischendatei übrig.
    assert list(tmp_path.glob(".pic.png.*")) == []


def test_save_image_file_keeps_original_when_encoding_fails(
    tmp_path, monkeypatch,
) -> None:
    out = tmp_path / "keep.png"
    out.write_bytes(b"ORIGINAL")

    def boom(*_a, **_k):
        raise OSError("kein Platz auf dem Gerät")

    # Encoder schlägt mitten im Schreiben fehl: die vorhandene Datei darf nicht
    # beschädigt werden und die temporäre Datei muss aufgeräumt sein.
    monkeypatch.setattr(Image.Image, "save", boom)
    with pytest.raises(OSError):
        save_image_file(Image.new("RGBA", (4, 4)), out)

    assert out.read_bytes() == b"ORIGINAL"
    assert list(tmp_path.glob(".keep.png.*")) == []


def test_save_image_file_rejects_unknown_extension(tmp_path) -> None:
    out = tmp_path / "pic.bmp"
    # Lieber ein klarer Fehler als still PNG-Bytes unter falschem Namen.
    with pytest.raises(ValueError, match=r"\.bmp"):
        save_image_file(Image.new("RGBA", (4, 4)), out)
    assert list(tmp_path.iterdir()) == []


def test_save_image_file_empty_extension_defaults_to_png(tmp_path) -> None:
    out = tmp_path / "noext"
    save_image_file(Image.new("RGBA", (4, 4), (1, 2, 3, 255)), out)
    with Image.open(out) as saved:
        assert saved.format == "PNG"


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


def test_rotated_size_quarter_turns_are_exact() -> None:
    # 0/180/360° unverändert, 90/270/-90° vertauscht – exakt wie Pillow.
    assert rotated_size(40, 20, 0) == (40, 20)
    assert rotated_size(40, 20, 180) == (40, 20)
    assert rotated_size(40, 20, 360) == (40, 20)
    assert rotated_size(40, 20, 90) == (20, 40)
    assert rotated_size(40, 20, 270) == (20, 40)
    assert rotated_size(40, 20, -90) == (20, 40)


def test_rotated_size_oblique_grows_and_is_symmetric() -> None:
    base = rotated_size(40, 20, 45)
    w, h = base
    assert w > 40 and h > 20                   # schräg ⇒ Arbeitsfläche wächst
    assert rotated_size(40, 20, -45) == base   # spiegelsymmetrisch
    assert rotated_size(40, 20, 135) == base   # Bounding-Box ist 180°-periodisch


@pytest.mark.parametrize("size", [(40, 20), (123, 57), (640, 480)])
@pytest.mark.parametrize("deg", [15, 30, 45, 60, 75, 137, -30])
def test_rotated_size_tracks_pillow_within_one_pixel(size, deg) -> None:
    """Die Schätzung muss Pillows echte expand-Größe eng treffen und darf sie
    nie überschreiten – sonst gatete das Megapixel-Limit am falschen Wert.
    Pillow rundet die Eckpunkte einzeln und liegt je Achse bis ~1 px höher."""
    w, h = size
    ew, eh = Image.new("RGBA", (w, h)).rotate(deg, expand=True).size
    gw, gh = rotated_size(w, h, deg)
    assert 0 <= ew - gw <= 2
    assert 0 <= eh - gh <= 2


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


# ── Ausgabeformat-Modell ───────────────────────────────────────────────

def test_normalize_save_format_falls_back_on_unknown() -> None:
    assert normalize_save_format("JPEG") == "JPEG"
    assert normalize_save_format("EXR") == DEFAULT_SAVE_FORMAT
    assert normalize_save_format(None) == DEFAULT_SAVE_FORMAT


def test_save_dialog_filter_lists_preferred_first_without_keyerror() -> None:
    # Unbekanntes preferred fällt auf das Default-Format zurück.
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
