"""Qt-freie Gloss-Visualisierung für die kombinierte 2D-Vorschau (#386).

Eine vorhandene Gloss-Maske wird als kühler, halbtransparenter Sheen sichtbar
gemacht und ohne Änderung des Motiv-Alphas über ein RGBA-Farbkomposit gelegt.
Alle Operationen sind deterministisch und frei von Qt-, Datei- und Netzwerkzugriffen.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

GLOSS_TINT = (210, 240, 255)
GLOSS_MAX_ALPHA = 192


class GlossPreviewError(ValueError):
    """Ungültiger Parameter oder inkompatible Bildgröße der Gloss-Vorschau."""


def _validate_intensity(intensity: float) -> None:
    """Prüft einen endlichen Mischfaktor im geschlossenen Bereich ``0..1``."""
    if not math.isfinite(intensity) or not 0.0 <= intensity <= 1.0:
        raise GlossPreviewError(
            f"intensity muss endlich und in [0.0, 1.0] sein, war {intensity!r}"
        )


def _gloss_mask(gloss_layer: Image.Image) -> np.ndarray:
    """Liest Helligkeit × Deckung der Gloss-Ebene als normierte Maske."""
    if gloss_layer.mode in {"I;16", "I;16L", "I;16B"}:
        values = np.asarray(gloss_layer, dtype=np.uint16).astype(np.float64)
        return np.clip(values / 65535.0, 0.0, 1.0)

    rgba = np.asarray(gloss_layer.convert("RGBA"), dtype=np.uint8)
    rgb = rgba[:, :, :3].astype(np.float64)
    luminance = (
        rgb[:, :, 0] * 0.299 + rgb[:, :, 1] * 0.587 + rgb[:, :, 2] * 0.114
    ) / 255.0
    coverage = rgba[:, :, 3].astype(np.float64) / 255.0
    return np.clip(luminance * coverage, 0.0, 1.0)


def gloss_overlay(gloss_layer: Image.Image, *, intensity: float) -> Image.Image:
    """Rendert ``gloss_layer`` als sichtbaren RGBA-Sheen.

    Die Maskenhelligkeit und ein vorhandener Quell-Alpha werden multipliziert.
    Schwarz bzw. transparente Gloss-Pixel ergeben einen vollständig transparenten
    Overlay; ``intensity=0`` ebenso. Der feste kühle Tint bleibt auch auf sehr
    hellen Motiven erkennbar. 16-Bit-Graustufenbilder werden über ``0..65535``
    normiert, bestehende RGBA-Layer über ``0..255``.
    """
    _validate_intensity(intensity)
    mask = _gloss_mask(gloss_layer)
    height, width = mask.shape
    overlay = np.empty((height, width, 4), dtype=np.uint8)
    overlay[:, :, 0] = GLOSS_TINT[0]
    overlay[:, :, 1] = GLOSS_TINT[1]
    overlay[:, :, 2] = GLOSS_TINT[2]
    overlay[:, :, 3] = np.rint(mask * GLOSS_MAX_ALPHA * intensity).astype(np.uint8)
    return Image.fromarray(overlay, "RGBA")


def compose_over(
    base_rgba: Image.Image,
    overlay: Image.Image,
    *,
    intensity: float,
) -> Image.Image:
    """Mischt ``overlay`` über ``base_rgba`` und erhält dessen Alpha exakt.

    Die Overlay-Deckung wird zusätzlich mit ``intensity`` skaliert. Größe und
    RGBA-Modus des Farbmotivs bleiben gleich. Bei Stärke ``0`` oder vollständig
    transparentem Overlay wird dasselbe Eingabeobjekt zurückgegeben.
    """
    _validate_intensity(intensity)
    if base_rgba.mode != "RGBA":
        raise GlossPreviewError(
            f"base_rgba muss Modus RGBA haben, war {base_rgba.mode!r}"
        )
    if overlay.size != base_rgba.size:
        raise GlossPreviewError(
            f"Overlay-Größe {overlay.size} passt nicht zur Basis {base_rgba.size}"
        )

    over = np.asarray(overlay.convert("RGBA"), dtype=np.uint8)
    if intensity == 0.0 or not bool(np.any(over[:, :, 3])):
        return base_rgba

    base = np.asarray(base_rgba, dtype=np.uint8)
    blend = over[:, :, 3].astype(np.float64) / 255.0 * intensity
    rgb = np.rint(
        base[:, :, :3].astype(np.float64) * (1.0 - blend[:, :, None])
        + over[:, :, :3].astype(np.float64) * blend[:, :, None]
    )
    result = base.copy()
    result[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return Image.fromarray(result, "RGBA")
