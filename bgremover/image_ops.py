"""Reine Bildoperationen für den Qt-Canvas.

Die Funktionen dieses Moduls kennen keine Qt-Widgets, Signale, Undo-Stapel
oder Einstellungen. ``ImageCanvas`` hält diesen UI-Zustand und ruft diese
Hilfsfunktionen für die Pixelarbeit auf.
"""
from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from bgremover.image_utils import numpy_to_pil


def remove_selection(arr: np.ndarray, mask: np.ndarray) -> Image.Image:
    """Gibt eine Kopie von ``arr`` zurück, bei der die ausgewählten Pixel transparent sind."""
    result = arr.copy()
    result[mask, 3] = 0
    return numpy_to_pil(result)


def replace_selection(arr: np.ndarray, mask: np.ndarray,
                      color: tuple[int, int, int]) -> Image.Image:
    """Gibt eine Kopie von ``arr`` zurück, bei der die ausgewählten Pixel durch ``color`` ersetzt sind."""
    result = arr.copy()
    result[mask] = [color[0], color[1], color[2], 255]
    return numpy_to_pil(result)


# ── Ausgabeformate (einzige Quelle) ──────────────────────────────────
# label -> (Qt-Dateifilter, Default-Suffix). Wird vom Einstellungen-Dialog
# (Auswahl) und vom Speichern-Dialog (Filterliste + Endung) gemeinsam
# genutzt, damit die Liste nicht an zwei Stellen driftet und ein unbekannt
# gespeichertes ``preferred_format`` keinen KeyError mehr auslöst.
SAVE_FORMATS: dict[str, tuple[str, str]] = {
    "PNG":  ("PNG (*.png)", ".png"),
    "JPEG": ("JPEG (*.jpg)", ".jpg"),
    "WebP": ("WebP (*.webp)", ".webp"),
    "TIFF": ("TIFF (*.tif)", ".tif"),
}
DEFAULT_SAVE_FORMAT = "PNG"


def normalize_save_format(preferred: str | None) -> str:
    """Gültiges Format-Label; fällt bei Unbekanntem auf den Default zurück."""
    return preferred if preferred in SAVE_FORMATS else DEFAULT_SAVE_FORMAT


def save_dialog_filter(preferred: str | None) -> str:
    """Qt-Filterstring für den Speichern-Dialog – *preferred* zuerst."""
    pref = normalize_save_format(preferred)
    ordered = [pref] + [f for f in SAVE_FORMATS if f != pref]
    return ";;".join(SAVE_FORMATS[f][0] for f in ordered)


def ensure_save_extension(
    path: str, selected_filter: str, preferred: str | None,
) -> str:
    """Hängt einen Default-Suffix an, wenn *path* keine Endung hat.

    Der Suffix richtet sich nach dem im Dialog gewählten Filter; lässt sich
    der nicht zuordnen, nach *preferred* (bzw. dem Default). Verhindert, dass
    eine Datei ohne Endung still als PNG landet, obwohl ein anderes Format
    gewählt war. Eine bereits vorhandene Endung bleibt unangetastet.
    """
    if Path(path).suffix:
        return path
    for _label, (flt, suffix) in SAVE_FORMATS.items():
        if flt == selected_filter:
            return path + suffix
    return path + SAVE_FORMATS[normalize_save_format(preferred)][1]


def save_image_file(img: Image.Image, path: str | Path) -> None:
    """Speichert ``img`` *atomar* unter ``path`` mit den App-Format-Vorgaben.

    Geschrieben wird zuerst in eine eindeutige temporäre Datei im
    Zielverzeichnis, die anschließend per ``os.replace()`` an die Zielstelle
    gehoben wird. So zerstört ein abgebrochener Schreibvorgang (Platte voll,
    Encoder-Fehler) keine bereits vorhandene Datei – ``os.replace`` ersetzt das
    Ziel atomar über bestehende Dateien hinweg (auch unter Windows). Dasselbe
    ``mkstemp``+``os.replace``-Muster nutzt bereits
    ``qt_plugins._copy_if_needed``.

    Eine *nicht-leere, unbekannte* Endung wird mit ``ValueError`` abgelehnt,
    statt still PNG-Bytes unter einem falschen Namen abzulegen (die App kennt
    genau die Formate aus ``SAVE_FORMATS``). Eine fehlende Endung bleibt als
    PNG-Default erhalten – das ist das Sicherheitsnetz für direkte Aufrufer.
    """
    out = Path(path)
    ext = out.suffix.lower()
    encoded: Image.Image
    fmt: str
    params: dict[str, object]
    if ext in (".jpg", ".jpeg"):
        # JPEG kennt kein Alpha → Transparenz auf Weiß komponieren.
        src = img if img.mode == "RGBA" else img.convert("RGBA")
        bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
        bg.paste(src, mask=src.split()[3])
        encoded, fmt, params = bg.convert("RGB"), "JPEG", {"quality": 95}
    elif ext == ".webp":
        encoded, fmt, params = img, "WEBP", {"quality": 90}
    elif ext in (".tif", ".tiff"):
        encoded, fmt, params = img, "TIFF", {"compression": "tiff_lzw"}
    elif ext in ("", ".png"):
        encoded, fmt, params = img, "PNG", {}
    else:
        raise ValueError(
            f"Nicht unterstütztes Speicherformat: '{ext}'. "
            "Unterstützt werden .png, .jpg, .webp und .tif."
        )

    # Explizites ``fmt`` ist Pflicht, weil das temporäre Ziel die Endung nicht
    # trägt – PIL könnte das Format sonst nicht aus dem Namen ableiten.
    fd, tmp_name = tempfile.mkstemp(dir=str(out.parent), prefix=f".{out.name}.")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            encoded.save(fh, fmt, **params)
        # ``mkstemp`` legt 0600 an: beim Überschreiben den Modus der Zieldatei
        # übernehmen, sonst die üblichen umask-Default-Rechte vergeben – damit
        # gespeicherte Bilder nicht überraschend nur für den Eigentümer lesbar
        # werden.
        if out.exists():
            os.chmod(tmp, out.stat().st_mode & 0o777)
        else:
            umask = os.umask(0)
            os.umask(umask)
            os.chmod(tmp, 0o666 & ~umask)
        os.replace(tmp, out)
    except Exception:
        with contextlib.suppress(OSError):
            tmp.unlink()
        raise


def round_corners(img: Image.Image, radius: int) -> tuple[Image.Image, int]:
    """Gibt ``img`` mit abgerundeten Alpha-Ecken zurück sowie den tatsächlich verwendeten Radius."""
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
    """Dreht ``img`` um ``degrees`` und vergrößert die Arbeitsfläche bei Bedarf."""
    rgba = img.convert("RGBA")
    if degrees % 90 == 0:
        return rgba.rotate(degrees, expand=True)
    return rgba.rotate(degrees, expand=True, resample=Image.Resampling.BICUBIC)


def flip_image(img: Image.Image, horizontal: bool) -> Image.Image:
    """Spiegelt ``img`` horizontal oder vertikal."""
    rgba = img.convert("RGBA")
    if horizontal:
        return rgba.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return rgba.transpose(Image.Transpose.FLIP_TOP_BOTTOM)


def crop_size_for_ratio(size: tuple[int, int], ratio_w: int,
                        ratio_h: int) -> tuple[int, int]:
    """Gibt die größte zentrierte Zuschnittgröße für ``size`` und das Seitenverhältnis zurück."""
    iw, ih = size
    if iw / ih > ratio_w / ratio_h:
        return int(ih * ratio_w / ratio_h), ih
    return iw, int(iw * ratio_h / ratio_w)


def crop_image(img: Image.Image, rect: tuple[int, int, int, int],
               is_circle: bool) -> Image.Image:
    """Schneidet ``img`` auf ``rect`` zu und wendet optional eine kreisförmige Alpha-Maske an."""
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
