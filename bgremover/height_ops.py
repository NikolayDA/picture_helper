"""Qt-freie Optimierungs-Operationen für Höhenkarten (#348).

Macht Reliefkarten **druckbarer**: Tonwert, Glättung und Begrenzung als reine,
deterministische Funktionen auf :class:`~bgremover.height_map.HeightField`.
Konventionen analog ``image_ops``/``image_utils``: keine Qt-, Datei- oder
Netzzugriffe, deutsche Docstrings, englische Identifier, strikte mypy-Typisierung.

Geteilte Engine (#344-Synergie): Dieselben Tonwert-/Graustufen-Primitive brauchen
auch die geplante „geteilte Tonwert-/Graustufen-Engine" (Rang #6) und der
Laser-Graustufenworkflow. Die Funktionen sind daher **16-Bit-tauglich** angelegt –
sie rechnen im Höhenwertebereich ``0..field.max_value`` (float-Zwischenrechnung,
am Ende auf ``uint16`` geklemmt) und hängen nicht an 8-Bit-Annahmen.

Jede Operation gibt ein **neues** Höhenfeld zurück (Eingabe unverändert) und lässt
die Deckung unberührt; fehlerhafte Parameter werfen
:class:`~bgremover.height_map.HeightMapError`.
"""
from __future__ import annotations

import numpy as np

from bgremover.height_map import HeightField, HeightMapError


def _with_values(field: HeightField, values: np.ndarray) -> HeightField:
    """Baut ein neues Höhenfeld mit *values* (geklemmt) und unveränderter Deckung."""
    clamped = np.clip(np.rint(values), 0, field.max_value).astype(np.uint16)
    return HeightField(clamped, field.coverage.copy(), field.max_value)


# ── Tonwert ──────────────────────────────────────────────────────────────


def levels(field: HeightField, black: int, white: int) -> HeightField:
    """Tonwertspreizung: bildet ``[black, white]`` linear auf ``[0, max_value]`` ab.

    Werte unterhalb ``black`` werden ``0``, oberhalb ``white`` werden
    ``max_value``; dazwischen linear gestreckt. Verlangt
    ``0 <= black < white <= max_value``.
    """
    if not 0 <= black < white <= field.max_value:
        raise HeightMapError(
            f"levels verlangt 0 <= black < white <= {field.max_value}, "
            f"war black={black}, white={white}"
        )
    norm = np.clip((field.values.astype(np.float64) - black) / (white - black), 0.0, 1.0)
    return _with_values(field, norm * field.max_value)


def gamma(field: HeightField, value: float) -> HeightField:
    """Gamma-Kennlinie: ``(höhe / max_value) ** value * max_value``.

    ``value > 1`` senkt die Mitten ab, ``< 1`` hebt sie an; ``value`` muss positiv
    sein. Schwarz/Weiß bleiben erhalten.
    """
    if value <= 0.0:
        raise HeightMapError(f"gamma muss positiv sein, war {value}")
    norm = (field.values.astype(np.float64) / field.max_value) ** value
    return _with_values(field, norm * field.max_value)


# ── Glättung ─────────────────────────────────────────────────────────────


def _gaussian_kernel1d(sigma: float) -> np.ndarray:
    """Normalisierter 1D-Gauß-Kernel; Radius ``ceil(3*sigma)`` (mind. 1)."""
    radius = max(1, int(np.ceil(3.0 * sigma)))
    x = np.arange(-radius, radius + 1, dtype=np.float64)
    kernel = np.exp(-(x * x) / (2.0 * sigma * sigma))
    return kernel / float(kernel.sum())


def _convolve1d(arr: np.ndarray, kernel: np.ndarray, axis: int) -> np.ndarray:
    """Separable 1D-Faltung entlang ``axis`` mit Reflexions-Rand (vektorisiert)."""
    radius = kernel.shape[0] // 2
    pad_width = [(radius, radius) if a == axis else (0, 0) for a in range(arr.ndim)]
    padded = np.pad(arr, pad_width, mode="reflect")
    out = np.zeros(arr.shape, dtype=np.float64)
    n = arr.shape[axis]
    for i in range(kernel.shape[0]):
        sl: list[slice] = [slice(None)] * arr.ndim
        sl[axis] = slice(i, i + n)
        out += float(kernel[i]) * padded[tuple(sl)]
    return out


def gaussian_blur(field: HeightField, sigma: float) -> HeightField:
    """Gauß-Glättung (separabel, Reflexions-Rand). ``sigma`` muss positiv sein.

    Eine konstante Höhe bleibt durch den auf 1 normierten Kernel und den
    Reflexions-Rand exakt erhalten.
    """
    if sigma <= 0.0:
        raise HeightMapError(f"sigma muss positiv sein, war {sigma}")
    kernel = _gaussian_kernel1d(sigma)
    vals = field.values.astype(np.float64)
    blurred = _convolve1d(_convolve1d(vals, kernel, 0), kernel, 1)
    return _with_values(field, blurred)


def median_blur(field: HeightField, radius: int) -> HeightField:
    """Median-Glättung (kantenerhaltend) über ein ``(2*radius+1)²``-Fenster.

    Reflexions-Rand; die ungerade Fenstergröße liefert einen exakten Median-Wert
    (keine Mittelung, daher kantenerhaltend und ausreißerrobust). ``radius >= 1``.
    """
    if radius < 1:
        raise HeightMapError(f"radius muss >= 1 sein, war {radius}")
    vals = field.values
    padded = np.pad(vals, radius, mode="reflect")
    h, w = vals.shape[:2]
    windows: list[np.ndarray] = []
    for dy in range(2 * radius + 1):
        for dx in range(2 * radius + 1):
            windows.append(padded[dy:dy + h, dx:dx + w])
    median = np.median(np.stack(windows, axis=0), axis=0)
    return _with_values(field, median)


# ── Begrenzung / Stufen ──────────────────────────────────────────────────


def threshold(field: HeightField, value: int) -> HeightField:
    """Binäre Schwelle: ``höhe >= value`` → ``max_value``, sonst ``0``.

    ``value`` muss in ``0..max_value`` liegen.
    """
    if not 0 <= value <= field.max_value:
        raise HeightMapError(f"threshold {value} außerhalb 0..{field.max_value}")
    binary = np.where(field.values >= value, field.max_value, 0)
    return _with_values(field, binary)


def quantize(field: HeightField, steps: int) -> HeightField:
    """Stufenreduzierung: quantisiert die Höhe auf ``steps`` gleichmäßige Stufen.

    Bei ``steps`` Stufen entstehen die Werte ``round(k/(steps-1) * max_value)`` für
    ``k = 0..steps-1`` (Endpunkte ``0`` und ``max_value`` bleiben erreichbar).
    ``steps >= 2``.
    """
    if steps < 2:
        raise HeightMapError(f"steps muss >= 2 sein, war {steps}")
    span = steps - 1
    norm = field.values.astype(np.float64) / field.max_value
    quantized = np.rint(norm * span) / span
    return _with_values(field, quantized * field.max_value)


def clamp_range(field: HeightField, min_height: int, max_height: int) -> HeightField:
    """Höhenbereich-Clamp: klemmt die Höhe auf ``[min_height, max_height]``.

    Reine Begrenzung ohne Streckung (Mindest-/Maximalhöhe für den Druck).
    Verlangt ``0 <= min_height < max_height <= max_value``.
    """
    if not 0 <= min_height < max_height <= field.max_value:
        raise HeightMapError(
            f"clamp_range verlangt 0 <= min < max <= {field.max_value}, "
            f"war min={min_height}, max={max_height}"
        )
    clamped = np.clip(field.values, min_height, max_height)
    return _with_values(field, clamped)
