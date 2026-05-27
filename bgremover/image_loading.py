"""Shared image-load helper for the sync canvas path and the async worker.

Both ``ImageCanvas.load_image`` (drag & drop, tests) and
``ImageLoadWorker._work`` (file dialog) route through ``open_validated_image``
so they share the same structural verify, format whitelist and megapixel
cap. Without it, the synchronous path silently accepted formats and
malformed files the worker had been rejecting since the format/structure
hardening landed.
"""
from __future__ import annotations

from PIL import Image, ImageOps, UnidentifiedImageError

from bgremover.constants import _ALLOWED_IMAGE_FORMATS, _MAX_MEGAPIXELS


def open_validated_image(path: str) -> tuple[Image.Image | None, str | None]:
    """Open *path*, validate it, and return ``(rgba_image, None)`` on success.

    On failure returns ``(None, message)`` with a user-facing status string.
    The image is EXIF-oriented and converted to RGBA.
    """
    # verify() prueft die Struktur (Header, Chunks) ohne die Pixel zu
    # dekodieren – manipulierte oder abgeschnittene Dateien werden so
    # frueh abgewiesen, bevor load() Speicher allokiert. PIL invalidiert
    # das Image-Objekt nach verify(); fuer den echten Decode-Pfad muss
    # erneut geoeffnet werden.
    try:
        with Image.open(path) as probe:
            probe.verify()
    except (UnidentifiedImageError, SyntaxError, OSError) as e:
        return None, f"{type(e).__name__}: {e}"

    try:
        img: Image.Image = Image.open(path)
        if img.format not in _ALLOWED_IMAGE_FORMATS:
            return None, f"Format nicht unterstützt: {img.format}"
        mp = img.width * img.height / 1_000_000
        if mp > _MAX_MEGAPIXELS:
            return None, (
                f"Bild zu groß ({mp:.0f} MP) – Maximum: {_MAX_MEGAPIXELS} MP")
        img.load()
    except (UnidentifiedImageError, OSError) as e:
        return None, f"{type(e).__name__}: {e}"

    img = ImageOps.exif_transpose(img).convert("RGBA")
    return img, None
