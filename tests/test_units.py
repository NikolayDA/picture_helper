"""Qt-freie Tests für die geteilte px↔mm↔DPI-Geometrie (#376).

Deckt die drei Ableitungsrichtungen (aus zwei bekannten Größen die dritte)
inklusive der 25,4-Konvention, die zweidimensionalen Helfer, die Rundungs-/
Mindestgröße-Regel sowie die strukturierten Fehler bei ungültigen Eingaben ab.
Reine Logik – keine Pixel, keine Dateien, kein Qt.
"""
from __future__ import annotations

import math

import pytest

from bgremover.units import (
    MM_PER_INCH,
    InvalidLengthError,
    InvalidPixelSizeError,
    InvalidResolutionError,
    UnitsError,
    dpi_for_size,
    dpi_from_px_mm,
    mm_from_px_dpi,
    parse_size_mm,
    pixel_size_for_size_mm,
    px_from_mm_dpi,
    size_mm_for_dpi,
)

# ── Konvention ─────────────────────────────────────────────────────────────

def test_mm_per_inch_is_the_25_4_convention() -> None:
    assert MM_PER_INCH == 25.4


# ── Skalare Ableitungen (je Achse) ─────────────────────────────────────────

def test_dpi_from_px_and_mm() -> None:
    # 1 Zoll = 25,4 mm → 300 px auf 25,4 mm sind genau 300 dpi.
    assert dpi_from_px_mm(300, 25.4) == 300.0
    assert math.isclose(dpi_from_px_mm(254, 50.8), 127.0)
    # Explizit gegen die Konvention gerechnet.
    assert dpi_from_px_mm(300, 25.4) == 300 * MM_PER_INCH / 25.4


def test_mm_from_px_and_dpi() -> None:
    assert math.isclose(mm_from_px_dpi(300, 300), 25.4)
    assert math.isclose(mm_from_px_dpi(600, 300), 50.8)
    assert mm_from_px_dpi(300, 300) == 300 * MM_PER_INCH / 300


def test_px_from_mm_and_dpi() -> None:
    assert px_from_mm_dpi(25.4, 300) == 300
    assert px_from_mm_dpi(50.8, 127) == 254


def test_round_trip_between_all_three() -> None:
    # Aus (px, mm) abgeleitete DPI reproduziert mm und px deterministisch.
    px, mm = 300, 25.4
    dpi = dpi_from_px_mm(px, mm)
    assert math.isclose(mm_from_px_dpi(px, dpi), mm)
    assert px_from_mm_dpi(mm, dpi) == px


def test_px_rounds_half_up_and_keeps_minimum_one() -> None:
    # 25,4 mm · 2,5 dpi / 25,4 = 2,5 → kaufmännisch (halb-auf) auf 3 gerundet.
    assert px_from_mm_dpi(25.4, 2.5) == 3
    # Eine winzige, aber gültige Zielgröße ergibt nie 0 px.
    assert px_from_mm_dpi(0.001, 1) == 1


def test_px_rounds_exact_half_pixel_despite_float_error() -> None:
    # 2,667 mm bei 300 dpi sind exakt 31,5 px; die Rohrechnung ergibt jedoch
    # 31.499999999999996. Halb-auf muss trotzdem auf 32 runden, nicht auf 31.
    assert px_from_mm_dpi(2.667, 300) == 32
    assert pixel_size_for_size_mm((2.667, 2.667), (300, 300)) == (32, 32)


# ── Zweidimensionale Helfer ────────────────────────────────────────────────

def test_dpi_for_size_per_axis() -> None:
    dpi_x, dpi_y = dpi_for_size((254, 127), (50.8, 25.4))
    assert math.isclose(dpi_x, 127.0)
    assert math.isclose(dpi_y, 127.0)


def test_size_mm_for_dpi_per_axis() -> None:
    mm_w, mm_h = size_mm_for_dpi((300, 600), (300, 300))
    assert math.isclose(mm_w, 25.4)
    assert math.isclose(mm_h, 50.8)


def test_pixel_size_for_size_mm_per_axis() -> None:
    assert pixel_size_for_size_mm((25.4, 50.8), (300, 300)) == (300, 600)


def test_parse_size_mm_accepts_tuple_and_list() -> None:
    assert parse_size_mm((50.8, 25.4)) == (50.8, 25.4)
    # Aus JSON geladene Listen werden zu einem float-Paar normalisiert.
    assert parse_size_mm([1, 2]) == (1.0, 2.0)


# ── Ungültige Eingaben → strukturierte Fehler ──────────────────────────────

@pytest.mark.parametrize("bad", [0, -1, 0.0, -2.5, float("inf"), float("nan"), "10", True, None])
def test_invalid_scalar_pixels_raise(bad: object) -> None:
    with pytest.raises(InvalidPixelSizeError):
        dpi_from_px_mm(bad, 25.4)


@pytest.mark.parametrize("bad", [0, -1, float("inf"), float("nan"), "10", True, None])
def test_invalid_scalar_mm_raise(bad: object) -> None:
    with pytest.raises(InvalidLengthError):
        dpi_from_px_mm(300, bad)


@pytest.mark.parametrize("bad", [0, -1, float("inf"), float("nan"), "10", True, None])
def test_invalid_scalar_dpi_raise(bad: object) -> None:
    with pytest.raises(InvalidResolutionError):
        mm_from_px_dpi(300, bad)


@pytest.mark.parametrize(
    "bad",
    [
        (0.0, 10.0),
        (-1.0, 10.0),
        (10.0, 0.0),
        (10.0,),
        (10.0, 10.0, 10.0),
        "10x10",
        10.0,
        (float("inf"), 10.0),
        (float("nan"), 10.0),
        ("10", "10"),
        (True, 10.0),
        None,
    ],
)
def test_parse_size_mm_rejects_invalid(bad: object) -> None:
    with pytest.raises(InvalidLengthError):
        parse_size_mm(bad)


def test_dpi_for_size_rejects_wrong_shapes() -> None:
    with pytest.raises(InvalidPixelSizeError):
        dpi_for_size((10,), (10.0, 10.0))
    with pytest.raises(InvalidLengthError):
        dpi_for_size((10, 10), "nope")


def test_structured_errors_share_common_base() -> None:
    for cls in (InvalidPixelSizeError, InvalidLengthError, InvalidResolutionError):
        assert issubclass(cls, UnitsError)
        assert issubclass(cls, ValueError)
