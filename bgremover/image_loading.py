"""Shared image-load helper for the sync canvas path and the async worker.

Both ``ImageCanvas.load_image`` (direct callers and tests) and
``ImageLoadWorker._work`` (file dialog, recent files and drag & drop) route
through ``open_validated_image``
so they share the same structural verify, format whitelist and megapixel
cap. Without it, the synchronous path silently accepted formats and
malformed files the worker had been rejecting since the format/structure
hardening landed.
"""
from __future__ import annotations

from PIL import Image, ImageOps, UnidentifiedImageError

from bgremover.constants import _ALLOWED_IMAGE_FORMATS, _MAX_MEGAPIXELS


def _too_large_message(mp: float | None = None) -> str:
    """Einheitliche „Bild zu groß"-Meldung – mit Megapixel-Angabe, wenn bekannt."""
    if mp is None:
        return f"Bild zu groß – Maximum: {_MAX_MEGAPIXELS} MP"
    return f"Bild zu groß ({mp:.0f} MP) – Maximum: {_MAX_MEGAPIXELS} MP"


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
    except Image.DecompressionBombError:
        # Pillow lehnt Bilder über 2× MAX_IMAGE_PIXELS bereits hier ab –
        # noch bevor die Megapixel-Prüfung unten greift. DecompressionBombError
        # ist KEINE OSError-Subklasse und entkäme sonst dem except-Tupel
        # (im synchronen load_image-Pfad als ungefangene Exception). Auf
        # dieselbe nutzerfreundliche „zu groß"-Meldung abbilden statt den
        # rohen DOS-Schutz-Text durchzureichen.
        return None, _too_large_message()
    except (UnidentifiedImageError, SyntaxError, OSError) as e:
        return None, f"{type(e).__name__}: {e}"

    try:
        img: Image.Image = Image.open(path)
        if img.format not in _ALLOWED_IMAGE_FORMATS:
            return None, f"Format nicht unterstützt: {img.format}"
        mp = img.width * img.height / 1_000_000
        if mp > _MAX_MEGAPIXELS:
            return None, _too_large_message(mp)
        img.load()
    except Image.DecompressionBombError:
        return None, _too_large_message()
    except (UnidentifiedImageError, OSError) as e:
        return None, f"{type(e).__name__}: {e}"

    img = ImageOps.exif_transpose(img).convert("RGBA")
    return img, None
