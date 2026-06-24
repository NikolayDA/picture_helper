"""Qt-freies Relief-Shading für die kombinierte 2D-Vorschau (#385).

Das Modul berechnet aus einem :class:`~bgremover.height_map.HeightField` ein
deterministisches Hillshade und legt es über ein RGBA-Farbkomposit. Es kennt
weder Qt noch Projekt-, Datei- oder Netzwerkzustand. Höhen werden vor der
Gradientenberechnung über ``HeightField.max_value`` normiert; dadurch verhalten
sich logisch gleiche 8- und 16-Bit-Felder identisch.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from bgremover.height_map import HeightField

NEUTRAL_SHADING = 128


class ReliefPreviewError(ValueError):
    """Ungültiger Parameter oder inkompatible Bildgröße der Relief-Vorschau."""


def _validate_strength(strength: float) -> None:
    """Prüft einen endlichen Mischfaktor im geschlossenen Bereich ``0..1``."""
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ReliefPreviewError(
            f"strength muss endlich und in [0.0, 1.0] sein, war {strength!r}"
        )


def _gradient(values: np.ndarray, axis: int) -> np.ndarray:
    """Deterministische zentrale Differenz, auch für ein Pixel breite Felder."""
    result = np.zeros(values.shape, dtype=np.float64)
    length = values.shape[axis]
    if length <= 1:
        return result
    if axis == 0:
        result[0, :] = values[1, :] - values[0, :]
        result[-1, :] = values[-1, :] - values[-2, :]
        if length > 2:
            result[1:-1, :] = (values[2:, :] - values[:-2, :]) * 0.5
    else:
        result[:, 0] = values[:, 1] - values[:, 0]
        result[:, -1] = values[:, -1] - values[:, -2]
        if length > 2:
            result[:, 1:-1] = (values[:, 2:] - values[:, :-2]) * 0.5
    return result


def relief_shading(
    field: HeightField,
    *,
    azimuth: float,
    elevation: float,
    strength: float,
) -> Image.Image:
    """Berechnet ein neutrales 8-Bit-Hillshade aus ``field``.

    ``azimuth`` ist die Lichtrichtung in Grad, im Uhrzeigersinn ab Norden;
    ``elevation`` liegt zwischen Horizont (``0``) und Zenit (``90``).
    Oberflächennormalen entstehen aus zentralen Differenzen der auf ``0..1``
    normierten Höhe. Von der Beleuchtung wird die Beleuchtung einer flachen
    Fläche abgezogen: flache oder nicht gedeckte Bereiche sind deshalb exakt
    ``NEUTRAL_SHADING`` und ``strength=0`` ist ein bitgenauer neutraler No-op.

    Das Ergebnis ist ein Pillow-Bild im Modus ``L`` und in ``field.size``.
    ``field.coverage`` blendet den Reliefkontrast pro Pixel aus, ohne die
    Höhenwerte zu verändern.
    """
    _validate_strength(strength)
    if not math.isfinite(azimuth):
        raise ReliefPreviewError(f"azimuth muss endlich sein, war {azimuth!r}")
    if not math.isfinite(elevation) or not 0.0 <= elevation <= 90.0:
        raise ReliefPreviewError(
            f"elevation muss endlich und in [0.0, 90.0] sein, war {elevation!r}"
        )

    normalized = field.values.astype(np.float64) / field.max_value
    dy = _gradient(normalized, axis=0)
    dx = _gradient(normalized, axis=1)

    normal_length = np.sqrt(dx * dx + dy * dy + 1.0)
    nx = -dx / normal_length
    ny = -dy / normal_length
    nz = 1.0 / normal_length

    azimuth_rad = math.radians(azimuth % 360.0)
    elevation_rad = math.radians(elevation)
    horizontal = math.cos(elevation_rad)
    light_x = math.sin(azimuth_rad) * horizontal
    light_y = -math.cos(azimuth_rad) * horizontal
    light_z = math.sin(elevation_rad)

    illumination = nx * light_x + ny * light_y + nz * light_z
    flat_illumination = light_z
    coverage = field.coverage.astype(np.float64) / 255.0
    contrast = np.clip(illumination - flat_illumination, -1.0, 1.0)
    gray = np.rint(
        NEUTRAL_SHADING + contrast * 127.0 * strength * coverage
    )
    return Image.fromarray(np.clip(gray, 0, 255).astype(np.uint8), "L")


def compose_over(
    base_rgba: Image.Image,
    shading: Image.Image,
    *,
    strength: float,
) -> Image.Image:
    """Legt ``shading`` multiplikativ über ``base_rgba``.

    Ein Shadingwert von ``NEUTRAL_SHADING`` verändert RGB nicht; dunklere Werte
    dunkeln ab, hellere hellen auf. ``strength`` mischt zwischen Original und
    vollem Effekt. Größe, RGBA-Modus und insbesondere der Alphakanal des
    Farbmotivs bleiben exakt erhalten. Bei neutralem Shading oder Stärke ``0``
    wird dasselbe Eingabeobjekt zurückgegeben.
    """
    _validate_strength(strength)
    if base_rgba.mode != "RGBA":
        raise ReliefPreviewError(
            f"base_rgba muss Modus RGBA haben, war {base_rgba.mode!r}"
        )
    if shading.size != base_rgba.size:
        raise ReliefPreviewError(
            f"Shading-Größe {shading.size} passt nicht zur Basis {base_rgba.size}"
        )

    shade = np.asarray(shading.convert("L"), dtype=np.uint8)
    if strength == 0.0 or bool(np.all(shade == NEUTRAL_SHADING)):
        return base_rgba

    base = np.asarray(base_rgba, dtype=np.uint8)
    factor = 1.0 + strength * (
        (shade.astype(np.float64) - NEUTRAL_SHADING) / NEUTRAL_SHADING
    )
    result = base.copy()
    rgb = np.rint(base[:, :, :3].astype(np.float64) * factor[:, :, None])
    result[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return Image.fromarray(result, "RGBA")
