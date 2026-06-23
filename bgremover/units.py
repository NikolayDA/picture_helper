"""Qt-freie px↔mm↔DPI-Geometrie (#376).

Geteiltes, strikt getyptes Fundament der maßgenauen Ausgabe (Epic #375): die
gesamte Umrechnung zwischen Pixelanzahl, physischer Länge (mm) und Auflösung
(DPI) liegt an *einer* Stelle. Aus je zwei bekannten Größen wird die dritte
deterministisch abgeleitet; einzige Konvention ist :data:`MM_PER_INCH` (25,4).

Konventionen analog ``project_model``/``height_map``: reine Logik ohne Datei-/
Netz-/Qt-Zugriffe, deutsche Docstrings, englische Identifier, strikte
mypy-Typisierung. Eingaben werden **validiert**: nicht endliche, nicht-positive
oder fehlgeformte Werte lösen strukturierte :class:`UnitsError`-Subtypen aus –
keine stille Korrektur.
"""
from __future__ import annotations

import math
from collections.abc import Sequence

# 1 Zoll = 25,4 mm – die einzige Konstante der px↔mm↔DPI-Umrechnung.
MM_PER_INCH = 25.4


class UnitsError(ValueError):
    """Basis aller strukturierten Fehler der Einheiten-/Geometrie-Umrechnung."""


class InvalidPixelSizeError(UnitsError):
    """Pixelangabe ist nicht endlich/positiv bzw. kein gültiges ``(Breite, Höhe)``-Paar."""


class InvalidLengthError(UnitsError):
    """Physische Länge (mm) ist nicht endlich/positiv bzw. kein gültiges Paar."""


class InvalidResolutionError(UnitsError):
    """Auflösung (DPI) ist nicht endlich/positiv bzw. kein gültiges Paar."""


def _validate_positive_number(value: object, *, error: type[UnitsError], what: str) -> float:
    """Stellt sicher, dass ``value`` eine endliche, positive Zahl ist.

    ``bool`` ist als Integer-Subtyp ausgeschlossen (eine ``True``-Größe ist ein
    Fehler, keine 1,0); ``inf``/``nan`` und Werte ``≤ 0`` lösen ``error`` aus.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise error(f"{what} muss eine Zahl sein, war {value!r}")
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise error(f"{what} muss endlich und positiv sein, war {value!r}")
    return number


def _as_pair(value: object, *, error: type[UnitsError], what: str) -> tuple[object, object]:
    """Zerlegt ``value`` in genau zwei Elemente ``(x, y)`` oder wirft ``error``.

    Akzeptiert eine Zweier-Sequenz (Liste/Tupel); ``str``/``bytes`` sind bewusst
    ausgeschlossen, obwohl sie Sequenzen sind. Validiert hier nur die *Form* – die
    Elemente prüfen die aufrufenden Skalar-Helfer.
    """
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or len(value) != 2:
        raise error(f"{what} muss ein (Breite, Höhe)-Paar sein, war {value!r}")
    return value[0], value[1]


# ── Skalare Umrechnung (je Achse) ──────────────────────────────────────────
def dpi_from_px_mm(pixels: object, length_mm: object) -> float:
    """DPI aus Pixelanzahl und physischer Länge (mm): ``px * 25,4 / mm``."""
    px = _validate_positive_number(pixels, error=InvalidPixelSizeError, what="Pixelanzahl")
    mm = _validate_positive_number(length_mm, error=InvalidLengthError, what="Länge (mm)")
    return px * MM_PER_INCH / mm


def mm_from_px_dpi(pixels: object, dpi: object) -> float:
    """Physische Länge (mm) aus Pixelanzahl und DPI: ``px * 25,4 / dpi``."""
    px = _validate_positive_number(pixels, error=InvalidPixelSizeError, what="Pixelanzahl")
    res = _validate_positive_number(dpi, error=InvalidResolutionError, what="Auflösung (DPI)")
    return px * MM_PER_INCH / res


def px_from_mm_dpi(length_mm: object, dpi: object) -> int:
    """Pixelanzahl aus physischer Länge (mm) und DPI: ``mm * dpi / 25,4``.

    Das Ergebnis wird kaufmännisch (halb-auf) auf eine ganze Zahl gerundet und
    nie kleiner als ``1`` – eine Bildachse hat mindestens ein Pixel. Das ist eine
    Begrenzung des *Ergebnisses* einer gültigen Rechnung, keine stille Korrektur
    ungültiger Eingaben (die weiterhin strukturierte Fehler auslösen).
    """
    mm = _validate_positive_number(length_mm, error=InvalidLengthError, what="Länge (mm)")
    res = _validate_positive_number(dpi, error=InvalidResolutionError, what="Auflösung (DPI)")
    return max(1, math.floor(mm * res / MM_PER_INCH + 0.5))


# ── Zweidimensionale Helfer (Breite, Höhe) ─────────────────────────────────
def parse_size_mm(value: object) -> tuple[float, float]:
    """Validiert beliebige Eingaben zu einer positiven physischen Größe ``(w, h)`` in mm.

    Akzeptiert eine Zweier-Sequenz endlicher, positiver Zahlen (auch eine aus JSON
    geladene Liste) und gibt sie als ``float``-Paar zurück; sonst
    :class:`InvalidLengthError`. Geteilte Eingangsvalidierung für Projektmodell
    und EufyMake-Export.
    """
    width, height = _as_pair(value, error=InvalidLengthError, what="Physische Größe (mm)")
    return (
        _validate_positive_number(width, error=InvalidLengthError, what="Breite (mm)"),
        _validate_positive_number(height, error=InvalidLengthError, what="Höhe (mm)"),
    )


def dpi_for_size(
    pixel_size: object, size_mm: object
) -> tuple[float, float]:
    """DPI ``(x, y)`` aus Pixelgröße und physischer Größe (mm), je Achse."""
    px_w, px_h = _as_pair(pixel_size, error=InvalidPixelSizeError, what="Pixelgröße")
    mm_w, mm_h = _as_pair(size_mm, error=InvalidLengthError, what="Physische Größe (mm)")
    return (dpi_from_px_mm(px_w, mm_w), dpi_from_px_mm(px_h, mm_h))


def size_mm_for_dpi(
    pixel_size: object, dpi: object
) -> tuple[float, float]:
    """Physische Größe (mm) ``(w, h)`` aus Pixelgröße und DPI, je Achse."""
    px_w, px_h = _as_pair(pixel_size, error=InvalidPixelSizeError, what="Pixelgröße")
    dpi_x, dpi_y = _as_pair(dpi, error=InvalidResolutionError, what="Auflösung (DPI)")
    return (mm_from_px_dpi(px_w, dpi_x), mm_from_px_dpi(px_h, dpi_y))


def pixel_size_for_size_mm(
    size_mm: object, dpi: object
) -> tuple[int, int]:
    """Pixelgröße ``(w, h)`` aus physischer Größe (mm) und DPI, je Achse."""
    mm_w, mm_h = _as_pair(size_mm, error=InvalidLengthError, what="Physische Größe (mm)")
    dpi_x, dpi_y = _as_pair(dpi, error=InvalidResolutionError, what="Auflösung (DPI)")
    return (px_from_mm_dpi(mm_w, dpi_x), px_from_mm_dpi(mm_h, dpi_y))
