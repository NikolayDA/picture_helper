#!/usr/bin/env python3
"""Reproduzierbare EufyMake-Hardware-Testfixtures (#687, Epic #681).

Erzeugt deterministisch (keine Zufallszahlen, reine Formel-/Rastermuster) die
PNG-Testdateien, die das Testdesign der Teil-Issues #688 (HEIGHT), #689
(mm/DPI) und #690 (Gloss) sowie die Testmatrix im Annahmeninventar
(``docs/history/EUFYMAKE-687-ANNAHMENINVENTAR.md``, Abschnitt „Testmatrix"/
„Aktualisierte Testmatrix") voraussetzen. Ohne dieses Skript wären die
späteren Hardware-Tests nicht reproduzierbar: jede Fixture bekäme sonst bei
jedem Testlauf leicht andere Bytes, und ein SHA-256-Abgleich vor dem Import
(„war das wirklich die getestete Datei?") wäre nicht möglich.

Drei Fixture-Rollen, alle unter ``tests/fixtures/eufymake_hardware/``:

- **HEIGHT** (#688-Testdesign): sieben Muster (Nullfläche, Maximalfläche,
  monotoner Keil, invertierter Keil, diskrete Stufen, Impuls/Kante,
  konstanter Mittelwert), je als 8-Bit ``L`` und 16-Bit ``I;16``.
- **COLOR/HEIGHT-Kontrollen** (#688-Testdesign): ein voll opakes
  Registriermotiv mit exakt demselben Pixelmaß wie die HEIGHT-Referenz sowie
  ein dreigeteiltes RGBA-Motiv mit 0/50/100 % Alpha. Letzteres wird mit einer
  konstanten, nicht-null HEIGHT-Map kombiniert und trennt dadurch
  Alpha/Coverage vom digitalen Höhenwert.
- **mm/DPI** (#689-Testdesign): ein Kontrollmotiv mit Messrahmen und
  Achsenmarkern (asymmetrische Markierungsdichte auf X- vs. Y-Achse, damit
  ein achsenspezifischer Skalierungsfehler sichtbar wird) in drei
  Pixelmaß/DPI-Kombinationen (klein/typisch/groß), je ohne ``pHYs``-Chunk,
  mit konsistentem ``pHYs`` und mit einem bewusst widersprüchlichen
  ``pHYs`` bei gleichem Pixelmaß. Eine weitere Variante kodiert getrennte
  X-/Y-DPI, damit Studio beide Achsen unabhängig offenlegen muss.
- **Gloss** (#690-Testdesign): Volltonauszüge min/mittel/max, monotoner und
  invertierter Keil, ein auf 64…192 begrenzter Normalisierungskeil, diskrete
  Stufen, Schachbrettmuster, eine dimensionsfremde Maske sowie dieselben
  Registriermarker wie COLOR und HEIGHT. Eigene COLOR-/HEIGHT-Kontrollen
  isolieren Alpha×Gloss und HEIGHT×Gloss.

Zusätzlich entsteht unter ``export_mm_dpi_conflict/`` ein echtes, über den
Produktionspfad :func:`bgremover.eufymake_writer.write_export` erzeugtes
BgRemover-Paket mit den kanonischen Assets ``color_motif.png``,
``height_map.png``, ``gloss_mask.png`` und ``manifest.json``. Das Manifest
fordert 300×300 DPI, während die PNGs absichtlich 150×150 DPI im ``pHYs``
tragen. Damit prüft I-06 genau die Priorität zwischen Paketmanifest und
Bildmetadaten, statt das Fixture-Katalogmanifest fälschlich als Exportpaket
zu behandeln.

Sechs weitere, ebenfalls über den Produktionswriter erzeugte Pakete trennen
für #690 fehlendes, Null- und voll gesetztes Gloss, Alpha×Gloss, HEIGHT×Gloss
und eine kontrolliert nach dem Writerlauf dimensionsfremd ersetzte Gloss-Datei.
So bleiben Dateivertrag und Studio-/Druckbeobachtung orthogonal.

Jede erzeugte Datei wird zusammen mit Rolle, Bittiefe, PNG-Modus, Maßen,
Erzeugungsparametern und SHA-256 in ``fixtures_manifest.json`` im selben
Verzeichnis dokumentiert (Schema :data:`SCHEMA_VERSION`). Die Sollbeziehung
zwischen Pixelmaß und physischer Größe ist ``mm = Pixel / DPI × 25,4``
(:func:`px_to_mm`), gerundet auf drei Nachkommastellen.

Die PNG-Bytes werden nach der Bilderzeugung mit einer lokalen kanonischen
Serialisierung geschrieben: fester Filtertyp, feste zlib-Parameter, genau die
vertraglich vorgesehenen Chunks. Bereits vorhandene Dateien werden nie als
Quelle wiederverwendet. Damit ist der Katalog eine reine Funktion der
Fixture-Spezifikation; Encoder- oder Altdatei-Drift wird im Bytevergleich
sichtbar und kann keinen neuen Manifest-Hash still überdecken.

Zwei weitere, kein eigenständiges Muster im obigen Sinn: die
**Pixelmaß-Variante** (I-04, #688/#689-Testdesign) ist eine
präzisionserhaltende 128×128-Kopie von ``height_wedge_16bit.png`` (halbe
Kantenlänge, gleiches Seitenverhältnis wie die 256×256-Referenz) über
``bgremover.height_map.resize_height_field`` – das ist derselbe
Resampling-Pfad, den die App selbst für Höhenfelder verwendet, nicht eine
zufällig andere Downsampling-Implementierung. Die **Seitenverhältnis-Variante**
(I-12, H-03, #688-Testdesign) ist demgegenüber bewusst **kein** Resize,
sondern ein direkt bei 256×128 (2:1) neu erzeugter Keil – anders als bei I-04
soll hier ein echtes, anderes Seitenverhältnis getestet werden, keine
verzerrte Ableitung eines quadratischen Musters.

Aufruf: ``python scripts/eufymake_fixture_generator.py generate``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgremover.eufymake_export import (  # noqa: E402
    EXPORT_PROFILE,
    EXPORT_PROFILE_VERSION,
)
from bgremover.eufymake_writer import (  # noqa: E402
    MANIFEST_FILENAME as EXPORT_MANIFEST_FILENAME,
)
from bgremover.eufymake_writer import (  # noqa: E402
    write_export,
)
from bgremover.height_map import (  # noqa: E402  (Pfad muss vor dem Import stehen)
    HEIGHT_MAX_16BIT,
    HeightField,
    resize_height_field,
)
from bgremover.project_model import (  # noqa: E402
    LayerKind,
    LayerRole,
    Project,
)

DEFAULT_OUT_DIR = ROOT / "tests" / "fixtures" / "eufymake_hardware"
MANIFEST_FILENAME = "fixtures_manifest.json"
# Schema 1: erste Fassung (Rolle, Muster, Bittiefe, PNG-Modus, Maße, Parameter,
# SHA-256, Bytegröße je Fixture). Schema 2 bindet den für #688 erweiterten
# Satz inklusive Alpha- und Registrierkontrollen. Schema 3 ergänzt getrennte
# X-/Y-DPI, die dreifache COLOR/HEIGHT/GLOSS-Registrierung und echte
# BgRemover-Exportpakete unter ``bundles``. Schema 4 ergänzt die isolierten
# Gloss-Szenarien aus #690: fehlend/Null/Voll, Alpha×Gloss, HEIGHT×Gloss und
# eine kontrolliert dimensionsfremde Gloss-Datei.
SCHEMA_VERSION = 4

HEIGHT_SIZE = (256, 256)  # (Breite, Höhe) px – klein genug fürs Repo, groß
# genug für eine sichtbare Stufen-/Keilauflösung.
COLOR_HEIGHT_PAIR_SIZE = HEIGHT_SIZE
ALPHA_FIELD_LEVELS = (0, 128, 255)
ALPHA_FIELD_RGB = (40, 80, 220)
REGISTRATION_PATTERN = "registration_landmarks"
GLOSS_SIZE = (256, 256)
CHECKER_SQUARE = 16  # px je Schachbrettfeld bei 256 px Kantenlänge → 16×16 Felder.
STEP_LEVELS = 8  # diskrete Stufen für Höhen-/Gloss-„Treppenkeil"-Fixtures.
GLOSS_LIMITED_RANGE = (64, 192)
GLOSS_DIMENSION_MISMATCH_SIZE = (GLOSS_SIZE[0] // 2, GLOSS_SIZE[1])
GLOSS_CROSS_LEVELS_16BIT = (0, 32768, HEIGHT_MAX_16BIT)
GLOSS_CROSS_COLOR = (80, 120, 160, 255)
MM_PER_INCH = 25.4
NON_SQUARE_DPI = (300, 150)
EXPORT_BUNDLE_DIRNAME = "export_mm_dpi_conflict"
EXPORT_TARGET_DPI = (300.0, 300.0)
EXPORT_PHYS_DPI = (150, 150)
GLOSS_BUNDLE_DIRNAMES = (
    "export_gloss_absent",
    "export_gloss_zero",
    "export_gloss_full",
    "export_gloss_alpha_coverage",
    "export_gloss_height_cross",
    "export_gloss_dimension_mismatch",
)
# I-04 (#688/#689): halbe Kantenlänge von HEIGHT_SIZE, gleiches Seitenverhältnis.
PIXEL_SIZE_VARIANT_SIZE = (HEIGHT_SIZE[0] // 2, HEIGHT_SIZE[1] // 2)
PIXEL_SIZE_VARIANT_PATTERN = "wedge_pixelsize_half"
PIXEL_SIZE_VARIANT_SOURCE = "height_wedge_16bit.png"
# I-12 (H-03, #688): bewusst *anderes* Seitenverhältnis als HEIGHT_SIZE (2:1 statt
# 1:1) – abzugrenzen von I-04 (Pixelmaß bei gleichem Seitenverhältnis).
ASPECT_RATIO_VARIANT_SIZE = (HEIGHT_SIZE[0], HEIGHT_SIZE[1] // 2)
ASPECT_RATIO_VARIANT_PATTERN = "wedge_aspect_ratio"


def px_to_mm(px: int, dpi: float) -> float:
    """Sollbeziehung ``mm = Pixel / DPI × 25,4``, gerundet auf 3 Nachkommastellen."""
    return round(px / dpi * MM_PER_INCH, 3)


def px_to_mm_from_png_dpi(px: int, dpi: float) -> float:
    """Physische Größe aus dem ganzzahligen PNG-``pHYs``-Wert.

    Pillow kodiert DPI als gerundete Pixel pro Meter. Der Manifestwert muss
    deshalb aus genau diesem gespeicherten Integer zurückgerechnet werden und
    darf nicht nochmals die angeforderte Fließkomma-DPI verwenden.
    """
    pixels_per_meter = int(dpi / (MM_PER_INCH / 1000.0) + 0.5)
    return round(px / pixels_per_meter * 1000.0, 3)


# ── Normalisierte Muster (0..1, Formel-/Rastermuster, keine Zufallszahlen) ──

def _pattern_zero(width: int, height: int) -> np.ndarray:
    return np.zeros((height, width), dtype=np.float64)


def _pattern_max(width: int, height: int) -> np.ndarray:
    return np.ones((height, width), dtype=np.float64)


def _pattern_mean(width: int, height: int) -> np.ndarray:
    return np.full((height, width), 0.5, dtype=np.float64)


def _pattern_wedge(width: int, height: int) -> np.ndarray:
    ramp = np.linspace(0.0, 1.0, width, dtype=np.float64)
    return np.broadcast_to(ramp, (height, width)).copy()


def _pattern_wedge_inverted(width: int, height: int) -> np.ndarray:
    return 1.0 - _pattern_wedge(width, height)


def _pattern_wedge_limited(width: int, height: int) -> np.ndarray:
    """Keil 64…192 statt 0…255, um automatische Normalisierung zu erkennen."""
    low, high = GLOSS_LIMITED_RANGE
    return low / 255.0 + _pattern_wedge(width, height) * ((high - low) / 255.0)


def _pattern_steps(width: int, height: int, levels: int = STEP_LEVELS) -> np.ndarray:
    """``levels`` gleich breite, diskrete Stufen von 0 bis 1 (Quantisierungstest)."""
    idx = (np.arange(width) * levels) // width
    row = idx.astype(np.float64) / (levels - 1)
    return np.broadcast_to(row, (height, width)).copy()


def _pattern_impulse_edge(width: int, height: int) -> np.ndarray:
    """Harte Kante (rechte Bildhälfte) plus isolierter, schmaler Impuls links davon.

    Deckt beide in #688 genannten Fälle ab: eine scharfe Kante (Filterung an
    einem Übergang) und einen einzelnen, isolierten Impuls (Glättung/
    automatische Normalisierung eines Ausreißers).
    """
    field = np.zeros((height, width), dtype=np.float64)
    field[:, width // 2 :] = 1.0
    impulse_center = width // 4
    half = max(1, width // 128)
    field[:, max(0, impulse_center - half) : impulse_center + half] = 1.0
    return field


def _pattern_checkerboard(width: int, height: int, square: int = CHECKER_SQUARE) -> np.ndarray:
    xx, yy = np.meshgrid(np.arange(width) // square, np.arange(height) // square)
    return ((xx + yy) % 2).astype(np.float64)


def _pattern_vertical_fields(
    width: int,
    height: int,
    levels: tuple[float, ...],
) -> tuple[np.ndarray, list[dict[str, float | int]]]:
    """Gleich breite vertikale Felder und ihre exakten Pixelgrenzen erzeugen."""
    boundaries = [round(index * width / len(levels)) for index in range(len(levels) + 1)]
    field = np.empty((height, width), dtype=np.float64)
    fields: list[dict[str, float | int]] = []
    for index, level in enumerate(levels):
        start, end = boundaries[index], boundaries[index + 1]
        field[:, start:end] = level
        fields.append({
            "x_start": start,
            "x_end_exclusive": end,
            "normalized_value": level,
        })
    return field, fields


def _to_8bit_l(pattern: np.ndarray) -> Image.Image:
    arr = np.rint(pattern * 255.0).astype(np.uint8)
    return Image.fromarray(arr, mode="L")


def _to_16bit_i16(pattern: np.ndarray) -> Image.Image:
    """16-Bit-Graustufen-PNG, analog zum ``I;16``-Pfad in ``scripts/benchmark.py``."""
    arr = np.rint(pattern * 65535.0).astype(np.uint16)
    raw = np.ascontiguousarray(arr, dtype="<u2").tobytes()
    return Image.frombytes("I;16", (arr.shape[1], arr.shape[0]), raw)


# ── Fixture-Beschreibung ────────────────────────────────────────────────────

@dataclass(frozen=True)
class FixtureSpec:
    """Eine geplante Fixture-Datei (Bild + Manifest-Metadaten, ohne Dateisystem)."""

    filename: str
    role: str  # "height_map" | "color_motif" | "gloss_mask"
    pattern: str
    bit_depth: int
    png_mode: str
    image: Image.Image
    save_kwargs: dict[str, Any] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)


# ── HEIGHT-Fixtures (#688-Testdesign) ───────────────────────────────────────

_HEIGHT_PATTERNS: tuple[tuple[str, Callable[[int, int], np.ndarray]], ...] = (
    ("zero", _pattern_zero),
    ("max", _pattern_max),
    ("wedge", _pattern_wedge),
    ("wedge_inverted", _pattern_wedge_inverted),
    ("steps", _pattern_steps),
    ("impulse_edge", _pattern_impulse_edge),
    ("mean", _pattern_mean),
)


def generate_height_fixtures() -> list[FixtureSpec]:
    width, height = HEIGHT_SIZE
    specs: list[FixtureSpec] = []
    for name, builder in _HEIGHT_PATTERNS:
        pattern = builder(width, height)
        params = {"width_px": width, "height_px": height}
        specs.append(FixtureSpec(
            filename=f"height_{name}_8bit.png", role="height_map", pattern=name,
            bit_depth=8, png_mode="L", image=_to_8bit_l(pattern), params=params,
        ))
        specs.append(FixtureSpec(
            filename=f"height_{name}_16bit.png", role="height_map", pattern=name,
            bit_depth=16, png_mode="I;16", image=_to_16bit_i16(pattern), params=params,
        ))
    return specs


# ── Pixelmaß-Variante (I-04, #688/#689-Testdesign) ──────────────────────────

def generate_pixel_size_variant_fixture() -> list[FixtureSpec]:
    """128×128-Kopie von ``height_wedge_16bit.png``, präzisionserhaltend resized.

    Bewusst **kein** eigenständig bei 128×128 neu erzeugtes Keilmuster – das
    würde den Pixelmaß-Test (I-04) mit einer zusätzlichen, unabhängigen
    Musterrealisierung vermischen. Stattdessen läuft der 256×256-Keil aus
    :func:`_pattern_wedge` durch denselben ``resize_height_field``-Pfad, den
    die App für Höhenfelder verwendet (float32-Zwischenpräzision, LANCZOS,
    ``rint`` + Clamp auf ``uint16`` – siehe ``bgremover/height_map.py``).
    """
    width, height = HEIGHT_SIZE
    pattern = _pattern_wedge(width, height)
    values = np.rint(pattern * HEIGHT_MAX_16BIT).astype(np.uint16)
    coverage = np.full(values.shape, 255, dtype=np.uint8)
    field_full = HeightField(values, coverage, HEIGHT_MAX_16BIT)

    half_w, half_h = PIXEL_SIZE_VARIANT_SIZE
    field_half = resize_height_field(field_full, half_w, half_h)
    raw = np.ascontiguousarray(field_half.values, dtype="<u2").tobytes()
    image = Image.frombytes("I;16", (half_w, half_h), raw)

    params = {
        "width_px": half_w,
        "height_px": half_h,
        "source_pattern": "wedge",
        "source_file": PIXEL_SIZE_VARIANT_SOURCE,
        "source_size_px": [width, height],
        "resize_method": "bgremover.height_map.resize_height_field (LANCZOS)",
    }
    return [FixtureSpec(
        filename="height_wedge_16bit_half.png", role="height_map",
        pattern=PIXEL_SIZE_VARIANT_PATTERN, bit_depth=16, png_mode="I;16",
        image=image, params=params,
    )]


# ── Seitenverhältnis-Variante (I-12, H-03, #688-Testdesign) ─────────────────

def generate_aspect_ratio_variant_fixture() -> list[FixtureSpec]:
    """Höhenkarte mit einem echten, anderen Seitenverhältnis als ``HEIGHT_SIZE``.

    Anders als die Pixelmaß-Variante (I-04, gleiches Seitenverhältnis, halbe
    Kantenlänge) prüft I-12, wie Studio eine Höhenkarte behandelt, deren
    Breite/Höhe-Verhältnis vom übrigen Testmotiv abweicht (strecken,
    zentrieren, ablehnen? – H-03). Direkt bei Zielgröße neu generiert (keine
    Verzerrung eines quadratischen Musters durch nachträgliches Resizing),
    derselbe deterministische Keil wie die übrigen Höhen-Fixtures.
    """
    width, height = ASPECT_RATIO_VARIANT_SIZE
    pattern = _pattern_wedge(width, height)
    image = _to_16bit_i16(pattern)
    params = {
        "width_px": width,
        "height_px": height,
        "reference_size_px": list(HEIGHT_SIZE),
        "note": "Seitenverhältnis 2:1 statt 1:1 wie die übrigen Höhen-Fixtures (H-03).",
    }
    return [FixtureSpec(
        filename="height_wedge_16bit_aspect.png", role="height_map",
        pattern=ASPECT_RATIO_VARIANT_PATTERN, bit_depth=16, png_mode="I;16",
        image=image, params=params,
    )]


# ── mm/DPI-Fixtures (#689-Testdesign) ───────────────────────────────────────

@dataclass(frozen=True)
class MmDpiCombo:
    """Eine Pixelmaß/DPI-Kombination des Kontrollmotivs."""

    label: str  # "klein" | "typisch" | "gross"
    width: int
    height: int
    nominal_dpi: int
    conflict_dpi: int  # bewusst abweichender DPI-Wert bei gleichem Pixelmaß


MM_DPI_COMBOS: tuple[MmDpiCombo, ...] = (
    MmDpiCombo("klein", 300, 300, 150, 300),
    MmDpiCombo("typisch", 1200, 1200, 300, 150),
    MmDpiCombo("gross", 2400, 1800, 300, 600),
)


def _draw_control_motif(width: int, height: int) -> Image.Image:
    """Messrahmen + Achsenmarker als Kontrollmotiv für den mm/DPI-Test.

    Rote Ticks oben (X-Achse, 11 Marken) und blaue Ticks links (Y-Achse,
    6 Marken) haben bewusst unterschiedliche Anzahl/Abstand, damit ein
    achsenspezifischer Skalierungsfehler (nicht-quadratisches DPI) beim
    Vergleich mit dem Ausdruck erkennbar bleibt. Ein Ursprungsmarker
    (gefüllter Kreis oben links) und eine Diagonale machen Rotation/
    Seitenverhältnis-Verzerrung sichtbar. Reine Formzeichnung, keine
    Zufallszahlen.
    """
    img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    margin = max(4, min(width, height) // 20)
    x0, y0 = margin, margin
    x1, y1 = width - 1 - margin, height - 1 - margin
    draw.rectangle((x0, y0, x1, y1), outline=(0, 0, 0, 255), width=max(1, margin // 4))

    x_marks = 11
    for i in range(x_marks):
        x = x0 + round(i * (x1 - x0) / (x_marks - 1))
        tick = margin if i % 5 == 0 else margin // 2
        draw.line([(x, y0), (x, y0 - tick)], fill=(200, 0, 0, 255), width=2)

    y_marks = 6
    for i in range(y_marks):
        y = y0 + round(i * (y1 - y0) / (y_marks - 1))
        tick = margin if i % 5 == 0 else margin // 2
        draw.line([(x0, y), (x0 - tick, y)], fill=(0, 0, 200, 255), width=2)

    draw.line((x0, y0, x1, y1), fill=(0, 128, 0, 255), width=2)
    r = max(3, margin // 2)
    draw.ellipse((x0 - r, y0 - r, x0 + r, y0 + r), fill=(0, 0, 0, 255))
    return img


def _draw_alpha_coverage_motif(width: int, height: int) -> tuple[Image.Image, list[dict[str, int]]]:
    """Drei gleich große Felder mit gleichem RGB und 0/128/255 Alpha erzeugen.

    Der RGB-Payload bleibt über alle Felder exakt konstant, damit beobachtete
    Deckungs-/Underbase-Unterschiede nur vom Alpha-Wert abhängen können. Die
    256 Pixel Breite sind nicht durch drei teilbar; die deterministischen
    Grenzen verteilen das eine Restpixel auf das mittlere Feld.
    """
    boundaries = [round(index * width / len(ALPHA_FIELD_LEVELS)) for index in range(4)]
    array = np.empty((height, width, 4), dtype=np.uint8)
    array[:, :, :3] = ALPHA_FIELD_RGB
    fields: list[dict[str, int]] = []
    for index, alpha in enumerate(ALPHA_FIELD_LEVELS):
        start, end = boundaries[index], boundaries[index + 1]
        array[:, start:end, 3] = alpha
        fields.append({"x_start": start, "x_end_exclusive": end, "alpha": alpha})
    return Image.fromarray(array, mode="RGBA"), fields


def _height_registration_from_color(reference: Image.Image) -> Image.Image:
    """Nicht-weiße COLOR-Marker pixelgenau als 16-Bit-Relief-Landmarks abbilden."""
    rgb = np.array(reference.convert("RGB"), dtype=np.uint8)
    landmarks = np.any(rgb != 255, axis=2)
    values = np.where(landmarks, HEIGHT_MAX_16BIT, 0).astype(np.uint16)
    raw = np.ascontiguousarray(values, dtype="<u2").tobytes()
    return Image.frombytes("I;16", reference.size, raw)


def _gloss_registration_from_color(reference: Image.Image) -> Image.Image:
    """Nicht-weiße COLOR-Marker pixelgenau als 8-Bit-Gloss-Landmarks abbilden."""
    rgb = np.array(reference.convert("RGB"), dtype=np.uint8)
    landmarks = np.any(rgb != 255, axis=2)
    return Image.fromarray(np.where(landmarks, 255, 0).astype(np.uint8), mode="L")


def generate_color_height_control_fixtures() -> list[FixtureSpec]:
    """Dimensionsgleiche COLOR-Referenz und Alpha/Coverage-Kontrolle für #688."""
    width, height = COLOR_HEIGHT_PAIR_SIZE
    reference = _draw_control_motif(width, height)
    registration_height = _height_registration_from_color(reference)
    alpha_motif, alpha_fields = _draw_alpha_coverage_motif(width, height)
    return [
        FixtureSpec(
            filename="color_height_reference.png",
            role="color_motif",
            pattern="height_registration_reference",
            bit_depth=8,
            png_mode="RGBA",
            image=reference,
            params={
                "width_px": width,
                "height_px": height,
                "paired_height_files": [
                    "height_wedge_16bit.png",
                    "height_registration_16bit.png",
                ],
                "alpha_levels": [255],
                "purpose": (
                    "I-02: dimensionsgleich mit HEIGHT-Keil; I-08: "
                    "pixelgleiche Registriermarker"
                ),
            },
        ),
        FixtureSpec(
            filename="height_registration_16bit.png",
            role="height_map",
            pattern=REGISTRATION_PATTERN,
            bit_depth=16,
            png_mode="I;16",
            image=registration_height,
            params={
                "width_px": width,
                "height_px": height,
                "paired_color_file": "color_height_reference.png",
                "background_value": 0,
                "landmark_value": HEIGHT_MAX_16BIT,
                "source_rule": "COLOR-Pixel ungleich RGB(255,255,255) ist Landmark",
                "purpose": "I-08: horizontale und vertikale Crop-Registrierung",
            },
        ),
        FixtureSpec(
            filename="color_alpha_coverage.png",
            role="color_motif",
            pattern="alpha_coverage_fields",
            bit_depth=8,
            png_mode="RGBA",
            image=alpha_motif,
            params={
                "width_px": width,
                "height_px": height,
                "paired_height_file": "height_mean_16bit.png",
                "paired_height_value": 32768,
                "rgb_payload": list(ALPHA_FIELD_RGB),
                "alpha_fields": alpha_fields,
                "purpose": "I-13: Alpha/Coverage bei konstanter nicht-null HEIGHT",
            },
        ),
    ]


def generate_mm_dpi_fixtures() -> list[FixtureSpec]:
    specs: list[FixtureSpec] = []
    for combo in MM_DPI_COMBOS:
        image = _draw_control_motif(combo.width, combo.height)
        expected_mm = [
            px_to_mm(combo.width, combo.nominal_dpi),
            px_to_mm(combo.height, combo.nominal_dpi),
        ]
        base_params = {
            "size_label": combo.label,
            "width_px": combo.width,
            "height_px": combo.height,
            "nominal_dpi": combo.nominal_dpi,
            "expected_mm_at_nominal_dpi": expected_mm,
        }

        specs.append(FixtureSpec(
            filename=f"mm_{combo.label}_no_phys.png", role="color_motif",
            pattern="control_motif", bit_depth=8, png_mode="RGBA", image=image,
            params={**base_params, "phys_dpi": None},
        ))
        specs.append(FixtureSpec(
            filename=f"mm_{combo.label}_phys.png", role="color_motif",
            pattern="control_motif", bit_depth=8, png_mode="RGBA", image=image,
            save_kwargs={"dpi": (combo.nominal_dpi, combo.nominal_dpi)},
            params={**base_params, "phys_dpi": combo.nominal_dpi, "phys_mm": expected_mm},
        ))
        conflict_mm = [
            px_to_mm_from_png_dpi(combo.width, combo.conflict_dpi),
            px_to_mm_from_png_dpi(combo.height, combo.conflict_dpi),
        ]
        specs.append(FixtureSpec(
            filename=f"mm_{combo.label}_phys_conflict.png", role="color_motif",
            pattern="control_motif", bit_depth=8, png_mode="RGBA", image=image,
            save_kwargs={"dpi": (combo.conflict_dpi, combo.conflict_dpi)},
            params={
                **base_params,
                "phys_dpi": combo.conflict_dpi,
                "mm_implied_by_phys_chunk": conflict_mm,
                "note": (
                    "pHYs widerspricht bewusst der nominalen DPI-Annahme bei "
                    "gleichem Pixelmaß (I-05)."
                ),
            },
        ))

    combo = next(item for item in MM_DPI_COMBOS if item.label == "typisch")
    x_dpi, y_dpi = NON_SQUARE_DPI
    image = _draw_control_motif(combo.width, combo.height)
    specs.append(FixtureSpec(
        filename="mm_typisch_phys_xy.png",
        role="color_motif",
        pattern="control_motif_xy_dpi",
        bit_depth=8,
        png_mode="RGBA",
        image=image,
        save_kwargs={"dpi": (x_dpi, y_dpi)},
        params={
            "size_label": combo.label,
            "width_px": combo.width,
            "height_px": combo.height,
            "nominal_dpi": combo.nominal_dpi,
            "expected_mm_at_nominal_dpi": [
                px_to_mm(combo.width, combo.nominal_dpi),
                px_to_mm(combo.height, combo.nominal_dpi),
            ],
            "phys_dpi": [x_dpi, y_dpi],
            "mm_implied_by_phys_chunk": [
                px_to_mm_from_png_dpi(combo.width, x_dpi),
                px_to_mm_from_png_dpi(combo.height, y_dpi),
            ],
            "note": (
                "pHYs kodiert absichtlich getrennte X-/Y-DPI. Studio muss "
                "anzeigen, koppeln, normalisieren oder ablehnen (I-05)."
            ),
        },
    ))
    return specs


# ── Gloss-Fixtures (#690-Testdesign) ────────────────────────────────────────

_GLOSS_PATTERNS: tuple[tuple[str, Callable[[int, int], np.ndarray]], ...] = (
    ("min", _pattern_zero),
    ("mean", _pattern_mean),
    ("max", _pattern_max),
    ("wedge", _pattern_wedge),
    ("wedge_inverted", _pattern_wedge_inverted),
    ("wedge_limited", _pattern_wedge_limited),
    ("steps", _pattern_steps),
    ("checkerboard", _pattern_checkerboard),
)


def generate_gloss_fixtures() -> list[FixtureSpec]:
    width, height = GLOSS_SIZE
    specs: list[FixtureSpec] = []
    for name, builder in _GLOSS_PATTERNS:
        pattern = builder(width, height)
        params: dict[str, Any] = {"width_px": width, "height_px": height}
        if name == "checkerboard":
            params["square_px"] = CHECKER_SQUARE
        elif name == "mean":
            params.update({
                "value": 128,
                "paired_color_files": [
                    "color_alpha_coverage.png",
                    "color_gloss_height_cross.png",
                ],
                "paired_height_files": [
                    "height_mean_16bit.png",
                    "height_gloss_cross_16bit.png",
                ],
                "purpose": "konstantes nicht-null Gloss für isolierte Kreuztests",
            })
        elif name == "wedge_limited":
            params.update({
                "value_range": list(GLOSS_LIMITED_RANGE),
                "purpose": (
                    "GL-01: automatische Min/Max-Normalisierung von echter "
                    "Intensitätsabbildung unterscheiden"
                ),
            })
        specs.append(FixtureSpec(
            filename=f"gloss_{name}.png", role="gloss_mask", pattern=name,
            bit_depth=8, png_mode="L", image=_to_8bit_l(pattern), params=params,
        ))
    reference = _draw_control_motif(width, height)
    specs.append(FixtureSpec(
        filename="gloss_registration.png",
        role="gloss_mask",
        pattern=REGISTRATION_PATTERN,
        bit_depth=8,
        png_mode="L",
        image=_gloss_registration_from_color(reference),
        params={
            "width_px": width,
            "height_px": height,
            "paired_color_file": "color_height_reference.png",
            "paired_height_file": "height_registration_16bit.png",
            "background_value": 0,
            "landmark_value": 255,
            "source_rule": "COLOR-Pixel ungleich RGB(255,255,255) ist Landmark",
            "purpose": "I-08: COLOR/HEIGHT/GLOSS-Registrierung auf beiden Achsen",
        },
    ))
    mismatch_width, mismatch_height = GLOSS_DIMENSION_MISMATCH_SIZE
    mismatch = _pattern_checkerboard(
        mismatch_width,
        mismatch_height,
        square=CHECKER_SQUARE,
    )
    specs.append(FixtureSpec(
        filename="gloss_dimensions_half_width.png",
        role="gloss_mask",
        pattern="checkerboard_dimension_mismatch",
        bit_depth=8,
        png_mode="L",
        image=_to_8bit_l(mismatch),
        params={
            "width_px": mismatch_width,
            "height_px": mismatch_height,
            "reference_size_px": list(GLOSS_SIZE),
            "square_px": CHECKER_SQUARE,
            "purpose": (
                "#690: Scaling, Zentrierung, Beschnitt oder Ablehnung einer "
                "dimensionsfremden Gloss-Datei unterscheiden"
            ),
        },
    ))
    return specs


def generate_gloss_interaction_fixtures() -> list[FixtureSpec]:
    """Isolierte COLOR/HEIGHT-Kontrollen für Alpha×Gloss und HEIGHT×Gloss."""
    width, height = GLOSS_SIZE
    color = Image.new("RGBA", (width, height), GLOSS_CROSS_COLOR)
    normalized_levels = tuple(value / HEIGHT_MAX_16BIT for value in GLOSS_CROSS_LEVELS_16BIT)
    height_pattern, fields = _pattern_vertical_fields(width, height, normalized_levels)
    for field_metadata, value in zip(fields, GLOSS_CROSS_LEVELS_16BIT, strict=True):
        field_metadata["value_16bit"] = value
    return [
        FixtureSpec(
            filename="color_gloss_height_cross.png",
            role="color_motif",
            pattern="constant_opaque_gloss_height_cross",
            bit_depth=8,
            png_mode="RGBA",
            image=color,
            params={
                "width_px": width,
                "height_px": height,
                "rgba": list(GLOSS_CROSS_COLOR),
                "paired_height_file": "height_gloss_cross_16bit.png",
                "paired_gloss_file": "gloss_mean.png",
                "purpose": "#690: konstante COLOR-Kontrolle für HEIGHT×Gloss",
            },
        ),
        FixtureSpec(
            filename="height_gloss_cross_16bit.png",
            role="height_map",
            pattern="gloss_height_cross_fields",
            bit_depth=16,
            png_mode="I;16",
            image=_to_16bit_i16(height_pattern),
            params={
                "width_px": width,
                "height_px": height,
                "fields": fields,
                "paired_color_file": "color_gloss_height_cross.png",
                "paired_gloss_file": "gloss_mean.png",
                "purpose": (
                    "#690: HEIGHT 0/32768/65535 bei konstantem nicht-null Gloss"
                ),
            },
        ),
    ]


def generate_all_fixtures() -> list[FixtureSpec]:
    """Alle HEIGHT-, mm/DPI- und Gloss-Fixtures (reine In-Memory-Erzeugung)."""
    return [
        *generate_height_fixtures(),
        *generate_pixel_size_variant_fixture(),
        *generate_aspect_ratio_variant_fixture(),
        *generate_color_height_control_fixtures(),
        *generate_mm_dpi_fixtures(),
        *generate_gloss_interaction_fixtures(),
        *generate_gloss_fixtures(),
    ]


# ── Schreiben + Manifest ─────────────────────────────────────────────────────

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_MODE_CONTRACT: dict[str, tuple[int, int]] = {
    "L": (8, 0),
    "RGBA": (8, 6),
    "I;16": (16, 0),
}


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    """Einen PNG-Chunk mit deterministischer Länge und CRC serialisieren."""
    crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)


def _canonical_png_bytes(
    image: Image.Image,
    *,
    dpi: tuple[float, float] | None = None,
) -> bytes:
    """PNG mit fester Filter-/Kompressionsstrategie plattformneutral kodieren.

    Pillow bleibt für die Pixelmodelle zuständig; die PNG-Serialisierung ist
    absichtlich lokal festgelegt. Damit hängen Fixture-Hashes weder von
    vorhandenen Zieldateien noch von Pillows PNG-Encoderheuristiken ab. Eine
    Änderung dieser Regel erzeugt sichtbaren Byte-/Manifest-Drift in den Tests.
    """
    if image.mode not in _PNG_MODE_CONTRACT:
        raise ValueError(f"Nicht unterstützter kanonischer PNG-Modus: {image.mode}")
    bit_depth, color_type = _PNG_MODE_CONTRACT[image.mode]
    width, height = image.size
    if image.mode == "L":
        pixels = np.asarray(image, dtype=np.uint8).tobytes(order="C")
        row_size = width
    elif image.mode == "RGBA":
        pixels = np.asarray(image, dtype=np.uint8).tobytes(order="C")
        row_size = width * 4
    else:
        pixels = np.asarray(image, dtype=np.uint16).astype(">u2", copy=False).tobytes()
        row_size = width * 2

    # Filtertyp 0 pro Zeile verhindert plattformabhängige Encoderheuristiken.
    raw = b"".join(
        b"\x00" + pixels[offset : offset + row_size]
        for offset in range(0, len(pixels), row_size)
    )
    compressor = zlib.compressobj(
        level=9,
        method=zlib.DEFLATED,
        wbits=zlib.MAX_WBITS,
        memLevel=9,
        strategy=zlib.Z_FIXED,
    )
    compressed = compressor.compress(raw) + compressor.flush()
    ihdr = struct.pack(">IIBBBBB", width, height, bit_depth, color_type, 0, 0, 0)
    chunks = [_png_chunk(b"IHDR", ihdr)]
    if dpi is not None:
        x_ppm = int(float(dpi[0]) / 0.0254 + 0.5)
        y_ppm = int(float(dpi[1]) / 0.0254 + 0.5)
        chunks.append(_png_chunk(b"pHYs", struct.pack(">IIB", x_ppm, y_ppm, 1)))
    chunks.extend((_png_chunk(b"IDAT", compressed), _png_chunk(b"IEND", b"")))
    return _PNG_SIGNATURE + b"".join(chunks)


def _write_canonical_png(
    image: Image.Image,
    path: Path,
    *,
    dpi: tuple[float, float] | None = None,
) -> None:
    """Ein Fixture-PNG ausschließlich nach dem kanonischen Vertrag schreiben."""
    path.write_bytes(_canonical_png_bytes(image, dpi=dpi))

def _write_mm_dpi_export_bundle(out_dir: Path) -> dict[str, Any]:
    """Erzeugt I-06 über den echten Writer und versieht PNGs mit Konflikt-pHYs."""
    width, height = COLOR_HEIGHT_PAIR_SIZE
    reference = _draw_control_motif(width, height)
    height_image = _height_registration_from_color(reference)
    gloss_image = _gloss_registration_from_color(reference)

    project = Project(width, height)
    color_layer = project.create_layer(reference, name="I-06 COLOR")
    project.assign_role(color_layer.id, LayerRole.COLOR_MOTIF)
    height_values = np.array(height_image, dtype=np.uint16)
    height_layer = project.create_layer(
        name="I-06 HEIGHT",
        kind=LayerKind.HEIGHT,
        height_data=HeightField(
            height_values,
            np.full(height_values.shape, 255, dtype=np.uint8),
            HEIGHT_MAX_16BIT,
        ),
    )
    project.assign_role(height_layer.id, LayerRole.HEIGHT_MAP)
    gloss_layer = project.create_layer(
        gloss_image.convert("RGBA"), name="I-06 GLOSS", kind=LayerKind.GLOSS,
    )
    project.assign_role(gloss_layer.id, LayerRole.GLOSS_MASK)
    project.set_dpi(*EXPORT_TARGET_DPI)

    bundle_dir = out_dir / EXPORT_BUNDLE_DIRNAME
    write_export(
        project,
        bundle_dir,
        bit_depth=16,
        overwrite=True,
        confirm_warnings=True,
    )

    # Der Produktionswriter erzeugt absichtlich metadatenneutrale PNGs. Nur für
    # dieses empirische Konfliktfixture wird anschließend ein pHYs-Chunk gesetzt;
    # manifest.json bleibt unverändert und fordert weiterhin 300×300 DPI.
    png_contracts = {
        "color_motif.png": ("color_motif", "RGBA", 8),
        "height_map.png": ("height_map", "I;16", 16),
        "gloss_mask.png": ("gloss_mask", "L", 8),
    }
    for filename in png_contracts:
        path = bundle_dir / filename
        with Image.open(path) as source:
            image = source.copy()
        # Erst nach dem Schließen des Quell-Handles überschreiben, damit die
        # Fixture-Erzeugung auch auf Windows funktioniert.
        _write_canonical_png(image, path, dpi=EXPORT_PHYS_DPI)

    files: list[dict[str, Any]] = []
    for filename, (role, png_mode, bit_depth) in png_contracts.items():
        path = bundle_dir / filename
        data = path.read_bytes()
        files.append({
            "filename": filename,
            "media_type": "image/png",
            "role": role,
            "pattern": REGISTRATION_PATTERN,
            "bit_depth": bit_depth,
            "png_mode": png_mode,
            "width": width,
            "height": height,
            "params": {"phys_dpi": list(EXPORT_PHYS_DPI)},
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        })

    export_manifest_path = bundle_dir / EXPORT_MANIFEST_FILENAME
    export_manifest_data = export_manifest_path.read_bytes()
    files.append({
        "filename": EXPORT_MANIFEST_FILENAME,
        "media_type": "application/json",
        "sha256": hashlib.sha256(export_manifest_data).hexdigest(),
        "bytes": len(export_manifest_data),
    })
    return {
        "id": "i06_manifest_vs_phys",
        "directory": EXPORT_BUNDLE_DIRNAME,
        "purpose": (
            "I-06: Priorität des BgRemover-Manifests (300×300 DPI) gegenüber "
            "widersprüchlichem PNG-pHYs (150×150 DPI) messen."
        ),
        "generated_via": "bgremover.eufymake_writer.write_export",
        "manifest_contract": {
            "profile": EXPORT_PROFILE,
            "profile_version": EXPORT_PROFILE_VERSION,
            "kind": "eufymake_import_assets",
            "pixel_size": [width, height],
            "bit_depth": 16,
            "physical_size_mm": [
                width / EXPORT_TARGET_DPI[0] * MM_PER_INCH,
                height / EXPORT_TARGET_DPI[1] * MM_PER_INCH,
            ],
            "dpi": list(EXPORT_TARGET_DPI),
            "assets": [
                "color_motif.png",
                "height_map.png",
                "gloss_mask.png",
            ],
        },
        "file_count": len(files),
        "files": sorted(files, key=lambda item: item["filename"]),
    }


def _create_export_project(
    color_image: Image.Image,
    *,
    height_image: Image.Image | None = None,
    gloss_image: Image.Image | None = None,
) -> Project:
    """Produktionsnahes Projekt für ein isoliertes #690-Szenario aufbauen."""
    width, height = color_image.size
    project = Project(width, height)
    color_layer = project.create_layer(color_image.convert("RGBA"), name="#690 COLOR")
    project.assign_role(color_layer.id, LayerRole.COLOR_MOTIF)
    if height_image is not None:
        height_values = np.array(height_image, dtype=np.uint16)
        height_layer = project.create_layer(
            name="#690 HEIGHT",
            kind=LayerKind.HEIGHT,
            height_data=HeightField(
                height_values,
                np.full(height_values.shape, 255, dtype=np.uint8),
                HEIGHT_MAX_16BIT,
            ),
        )
        project.assign_role(height_layer.id, LayerRole.HEIGHT_MAP)
    if gloss_image is not None:
        gloss_layer = project.create_layer(
            gloss_image.convert("RGBA"),
            name="#690 GLOSS",
            kind=LayerKind.GLOSS,
        )
        project.assign_role(gloss_layer.id, LayerRole.GLOSS_MASK)
    return project


def _bundle_png_entry(
    path: Path,
    *,
    role: str,
    pattern: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Katalogzeile aus den tatsächlich geschriebenen PNG-Eigenschaften bilden."""
    data = path.read_bytes()
    with Image.open(path) as image:
        png_mode = image.mode
        width, height = image.size
    return {
        "filename": path.name,
        "media_type": "image/png",
        "role": role,
        "pattern": pattern,
        "bit_depth": 16 if png_mode == "I;16" else 8,
        "png_mode": png_mode,
        "width": width,
        "height": height,
        "params": {"phys_dpi": None, **(params or {})},
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def _write_gloss_scenario_bundle(
    out_dir: Path,
    *,
    scenario_id: str,
    directory: str,
    purpose: str,
    color_image: Image.Image,
    color_pattern: str,
    height_image: Image.Image | None = None,
    height_pattern: str | None = None,
    gloss_image: Image.Image | None = None,
    gloss_pattern: str | None = None,
    replacement_gloss: Image.Image | None = None,
    scenario_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ein echtes Writer-Paket erzeugen und optional Gloss gezielt dimensionsbrechen."""
    project = _create_export_project(
        color_image,
        height_image=height_image,
        gloss_image=gloss_image,
    )
    bundle_dir = out_dir / directory
    write_export(
        project,
        bundle_dir,
        bit_depth=16,
        overwrite=True,
        confirm_warnings=True,
    )
    if replacement_gloss is not None:
        _write_canonical_png(replacement_gloss, bundle_dir / "gloss_mask.png")
    for path in sorted(bundle_dir.glob("*.png")):
        with Image.open(path) as source:
            image = source.copy()
        _write_canonical_png(image, path)

    png_contracts: list[tuple[str, str, str, dict[str, Any]]] = [
        ("color_motif.png", "color_motif", color_pattern, {}),
    ]
    if height_image is not None:
        assert height_pattern is not None
        png_contracts.append(("height_map.png", "height_map", height_pattern, {}))
    if gloss_image is not None:
        assert gloss_pattern is not None
        gloss_params: dict[str, Any] = {}
        if replacement_gloss is not None:
            gloss_params = {
                "intentional_dimension_mismatch": True,
                "reference_size_px": list(color_image.size),
            }
        png_contracts.append(("gloss_mask.png", "gloss_mask", gloss_pattern, gloss_params))

    files = [
        _bundle_png_entry(
            bundle_dir / filename,
            role=role,
            pattern=pattern,
            params=params,
        )
        for filename, role, pattern, params in png_contracts
    ]
    export_manifest_path = bundle_dir / EXPORT_MANIFEST_FILENAME
    export_manifest_data = export_manifest_path.read_bytes()
    files.append({
        "filename": EXPORT_MANIFEST_FILENAME,
        "media_type": "application/json",
        "sha256": hashlib.sha256(export_manifest_data).hexdigest(),
        "bytes": len(export_manifest_data),
    })
    asset_names = [filename for filename, _, _, _ in png_contracts]
    return {
        "id": scenario_id,
        "directory": directory,
        "purpose": purpose,
        "generated_via": (
            "bgremover.eufymake_writer.write_export"
            if replacement_gloss is None
            else (
                "bgremover.eufymake_writer.write_export + kontrollierter "
                "Dimensionsersatz von gloss_mask.png"
            )
        ),
        "scenario_params": scenario_params or {},
        "manifest_contract": {
            "profile": EXPORT_PROFILE,
            "profile_version": EXPORT_PROFILE_VERSION,
            "kind": "eufymake_import_assets",
            "pixel_size": list(color_image.size),
            "bit_depth": 16,
            "physical_size_mm": None,
            "dpi": None,
            "assets": asset_names,
        },
        "file_count": len(files),
        "files": sorted(files, key=lambda item: item["filename"]),
    }


def _write_gloss_scenario_bundles(out_dir: Path) -> list[dict[str, Any]]:
    """Sechs orthogonale #690-Pakete über den Produktionswriter erzeugen."""
    width, height = GLOSS_SIZE
    opaque_color = Image.new("RGBA", GLOSS_SIZE, GLOSS_CROSS_COLOR)
    alpha_color, alpha_fields = _draw_alpha_coverage_motif(width, height)
    gloss_zero = _to_8bit_l(_pattern_zero(width, height))
    gloss_mean = _to_8bit_l(_pattern_mean(width, height))
    gloss_full = _to_8bit_l(_pattern_max(width, height))
    height_mean = _to_16bit_i16(_pattern_mean(width, height))
    normalized_levels = tuple(value / HEIGHT_MAX_16BIT for value in GLOSS_CROSS_LEVELS_16BIT)
    height_cross_pattern, _ = _pattern_vertical_fields(width, height, normalized_levels)
    height_cross = _to_16bit_i16(height_cross_pattern)
    mismatch_width, mismatch_height = GLOSS_DIMENSION_MISMATCH_SIZE
    gloss_mismatch = _to_8bit_l(
        _pattern_checkerboard(mismatch_width, mismatch_height, square=CHECKER_SQUARE)
    )

    bundles = [
        _write_gloss_scenario_bundle(
            out_dir,
            scenario_id="gloss_absent",
            directory=GLOSS_BUNDLE_DIRNAMES[0],
            purpose=(
                "#690: sicherer Default ohne explizite Gloss-Rolle; Paket darf "
                "keine gloss_mask.png referenzieren oder schreiben."
            ),
            color_image=opaque_color,
            color_pattern="constant_opaque",
        ),
        _write_gloss_scenario_bundle(
            out_dir,
            scenario_id="gloss_zero",
            directory=GLOSS_BUNDLE_DIRNAMES[1],
            purpose="#690: vorhandene gültige 0-GLOSS-Datei getrennt von fehlendem Gloss.",
            color_image=opaque_color,
            color_pattern="constant_opaque",
            gloss_image=gloss_zero,
            gloss_pattern="zero",
            scenario_params={"gloss_value_range": [0, 0]},
        ),
        _write_gloss_scenario_bundle(
            out_dir,
            scenario_id="gloss_full",
            directory=GLOSS_BUNDLE_DIRNAMES[2],
            purpose="#690: voll gesetzte 255-GLOSS-Datei als Gegenprobe zur 0-Datei.",
            color_image=opaque_color,
            color_pattern="constant_opaque",
            gloss_image=gloss_full,
            gloss_pattern="max",
            scenario_params={"gloss_value_range": [255, 255]},
        ),
        _write_gloss_scenario_bundle(
            out_dir,
            scenario_id="gloss_alpha_coverage",
            directory=GLOSS_BUNDLE_DIRNAMES[3],
            purpose=(
                "#690: COLOR-Alpha 0/128/255 bei konstantem RGB, konstanter "
                "nicht-null HEIGHT und konstantem nicht-null Gloss."
            ),
            color_image=alpha_color,
            color_pattern="alpha_coverage_fields",
            height_image=height_mean,
            height_pattern="mean",
            gloss_image=gloss_mean,
            gloss_pattern="mean",
            scenario_params={
                "alpha_fields": alpha_fields,
                "height_value": 32768,
                "gloss_value": 128,
            },
        ),
        _write_gloss_scenario_bundle(
            out_dir,
            scenario_id="gloss_height_cross",
            directory=GLOSS_BUNDLE_DIRNAMES[4],
            purpose=(
                "#690: HEIGHT 0/32768/65535 bei konstant opakem COLOR und "
                "konstantem nicht-null Gloss."
            ),
            color_image=opaque_color,
            color_pattern="constant_opaque_gloss_height_cross",
            height_image=height_cross,
            height_pattern="gloss_height_cross_fields",
            gloss_image=gloss_mean,
            gloss_pattern="mean",
            scenario_params={
                "height_values": list(GLOSS_CROSS_LEVELS_16BIT),
                "gloss_value": 128,
            },
        ),
        _write_gloss_scenario_bundle(
            out_dir,
            scenario_id="gloss_dimension_mismatch",
            directory=GLOSS_BUNDLE_DIRNAMES[5],
            purpose=(
                "#690: Manifest/COLOR 256×256 gegen Gloss 128×256; Scaling, "
                "Beschnitt, Zentrierung oder Ablehnung getrennt beobachten."
            ),
            color_image=opaque_color,
            color_pattern="constant_opaque",
            gloss_image=gloss_mean,
            gloss_pattern="checkerboard_dimension_mismatch",
            replacement_gloss=gloss_mismatch,
            scenario_params={
                "reference_size_px": list(GLOSS_SIZE),
                "gloss_size_px": list(GLOSS_DIMENSION_MISMATCH_SIZE),
            },
        ),
    ]
    assert tuple(bundle["directory"] for bundle in bundles) == GLOSS_BUNDLE_DIRNAMES
    return bundles


def write_fixtures(specs: Iterable[FixtureSpec], out_dir: Path) -> dict[str, Any]:
    """Schreibt alle ``specs`` als PNG nach ``out_dir`` und das SHA-256-Manifest.

    Nach Dateiname sortiert, damit das Manifest unabhängig von der
    Erzeugungsreihenfolge byteidentisch bleibt (Determinismus-Test).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    for spec in sorted(specs, key=lambda s: s.filename):
        path = out_dir / spec.filename
        unsupported_kwargs = set(spec.save_kwargs) - {"dpi"}
        if unsupported_kwargs:
            raise ValueError(
                f"Nicht unterstützte PNG-Optionen für {spec.filename}: "
                f"{sorted(unsupported_kwargs)}"
            )
        dpi = spec.save_kwargs.get("dpi")
        _write_canonical_png(spec.image, path, dpi=dpi)
        data = path.read_bytes()
        entries.append({
            "filename": spec.filename,
            "role": spec.role,
            "pattern": spec.pattern,
            "bit_depth": spec.bit_depth,
            "png_mode": spec.png_mode,
            "width": spec.image.width,
            "height": spec.image.height,
            "params": spec.params,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        })
    bundles = [
        _write_mm_dpi_export_bundle(out_dir),
        *_write_gloss_scenario_bundles(out_dir),
    ]
    manifest = {
        "schema": SCHEMA_VERSION,
        "generated_by": "scripts/eufymake_fixture_generator.py",
        "fixture_count": len(entries),
        "fixtures": entries,
        "bundle_count": len(bundles),
        "bundles": bundles,
    }
    manifest_path = out_dir / MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    return manifest


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    gen_p = sub.add_parser(
        "generate", help="Fixtures + fixtures_manifest.json (neu) schreiben.",
    )
    gen_p.add_argument(
        "--out-dir", type=Path, default=DEFAULT_OUT_DIR,
        help=f"Zielverzeichnis (Default: {_rel(DEFAULT_OUT_DIR)}).",
    )

    args = parser.parse_args(argv)
    if args.command != "generate":  # pragma: no cover - einziger Unterbefehl
        parser.error(f"Unbekannter Befehl: {args.command}")

    manifest = write_fixtures(generate_all_fixtures(), args.out_dir)
    total_bytes = sum(entry["bytes"] for entry in manifest["fixtures"])
    total_bytes += sum(
        entry["bytes"]
        for bundle in manifest["bundles"]
        for entry in bundle["files"]
    )
    bundle_label = "Exportpaket" if manifest["bundle_count"] == 1 else "Exportpakete"
    print(
        f"{manifest['fixture_count']} Fixtures und {manifest['bundle_count']} "
        f"{bundle_label} geschrieben nach "
        f"{_rel(args.out_dir)} ({total_bytes / 1024:.1f} KiB), "
        f"Manifest: {_rel(args.out_dir / MANIFEST_FILENAME)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
