"""Pure image operations used by the Qt canvas.

The functions in this module do not know about Qt widgets, signals, undo
stacks, or application settings. ``ImageCanvas`` owns that UI state and calls
these helpers for the pixel work.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from bgremover.image_utils import numpy_to_pil


def remove_selection(arr: np.ndarray, mask: np.ndarray) -> Image.Image:
    """Return a copy of ``arr`` with the selected pixels made transparent."""
    result = arr.copy()
    result[mask, 3] = 0
    return numpy_to_pil(result)


def replace_selection(arr: np.ndarray, mask: np.ndarray,
                      color: tuple[int, int, int]) -> Image.Image:
    """Return a copy of ``arr`` with the selected pixels replaced by ``color``."""
    result = arr.copy()
    result[mask] = [color[0], color[1], color[2], 255]
    return numpy_to_pil(result)


def save_image_file(img: Image.Image, path: str | Path) -> None:
    """Save ``img`` to ``path`` using the app's format-specific defaults."""
    out = Path(path)
    ext = out.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        # JPEG has no alpha channel. Composite transparencies onto white.
        src = img if img.mode == "RGBA" else img.convert("RGBA")
        bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
        bg.paste(src, mask=src.split()[3])
        bg.convert("RGB").save(out, quality=95)
    elif ext == ".webp":
        img.save(out, "WEBP", quality=90)
    elif ext in (".tif", ".tiff"):
        img.save(out, "TIFF", compression="tiff_lzw")
    else:
        img.save(out, "PNG")


def round_corners(img: Image.Image, radius: int) -> tuple[Image.Image, int]:
    """Return ``img`` with rounded alpha corners and the clamped radius used."""
    rgba = img.convert("RGBA")
    w, h = rgba.size
    r = min(radius, w // 2, h // 2)

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)

    orig_a = np.array(rgba.split()[3])
    new_a = np.minimum(orig_a, np.array(mask))
    channels = list(rgba.split())
    channels[3] = Image.fromarray(new_a.astype(np.uint8))
    return Image.merge("RGBA", channels), r


def rotate_image(img: Image.Image, degrees: int) -> Image.Image:
    """Rotate ``img`` by ``degrees`` while expanding the canvas as needed."""
    rgba = img.convert("RGBA")
    if degrees % 90 == 0:
        return rgba.rotate(degrees, expand=True)
    return rgba.rotate(degrees, expand=True, resample=Image.Resampling.BICUBIC)


def flip_image(img: Image.Image, horizontal: bool) -> Image.Image:
    """Mirror ``img`` horizontally or vertically."""
    rgba = img.convert("RGBA")
    if horizontal:
        return rgba.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return rgba.transpose(Image.Transpose.FLIP_TOP_BOTTOM)


def crop_size_for_ratio(size: tuple[int, int], ratio_w: int,
                        ratio_h: int) -> tuple[int, int]:
    """Return the largest centered crop size for ``size`` and aspect ratio."""
    iw, ih = size
    if iw / ih > ratio_w / ratio_h:
        return int(ih * ratio_w / ratio_h), ih
    return iw, int(iw * ratio_h / ratio_w)


def crop_image(img: Image.Image, rect: tuple[int, int, int, int],
               is_circle: bool) -> Image.Image:
    """Crop ``img`` to ``rect`` and optionally apply a circular alpha mask."""
    x, y, w, h = rect
    cropped = img.convert("RGBA").crop((x, y, x + w, y + h))
    if not is_circle:
        return cropped

    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, w - 1, h - 1], fill=255)
    orig_a = np.array(cropped.split()[3])
    new_a = np.minimum(orig_a, np.array(mask))
    channels = list(cropped.split())
    channels[3] = Image.fromarray(new_a.astype(np.uint8))
    return Image.merge("RGBA", channels)
