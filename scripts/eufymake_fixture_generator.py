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
  ``pHYs`` bei gleichem Pixelmaß.
- **Gloss** (#690-Testdesign): Volltonauszüge min/max, monotoner Keil,
  invertierter Keil, diskrete Stufen, Schachbrettmuster (Registrierung/
  Bleeding).

Jede erzeugte Datei wird zusammen mit Rolle, Bittiefe, PNG-Modus, Maßen,
Erzeugungsparametern und SHA-256 in ``fixtures_manifest.json`` im selben
Verzeichnis dokumentiert (Schema :data:`SCHEMA_VERSION`). Die Sollbeziehung
zwischen Pixelmaß und physischer Größe ist ``mm = Pixel / DPI × 25,4``
(:func:`px_to_mm`), gerundet auf drei Nachkommastellen.

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
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgremover.height_map import (  # noqa: E402  (Pfad muss vor dem Import stehen)
    HEIGHT_MAX_16BIT,
    HeightField,
    resize_height_field,
)

DEFAULT_OUT_DIR = ROOT / "tests" / "fixtures" / "eufymake_hardware"
MANIFEST_FILENAME = "fixtures_manifest.json"
# Schema 1: erste Fassung (Rolle, Muster, Bittiefe, PNG-Modus, Maße, Parameter,
# SHA-256, Bytegröße je Fixture). Schema 2 bindet den für #688 erweiterten
# Satz inklusive Alpha- und Registrierkontrollen; ein alter 31er-Satz kann so
# am Zielrechner nicht mehr still als aktuell gelten.
SCHEMA_VERSION = 2

HEIGHT_SIZE = (256, 256)  # (Breite, Höhe) px – klein genug fürs Repo, groß
# genug für eine sichtbare Stufen-/Keilauflösung.
COLOR_HEIGHT_PAIR_SIZE = HEIGHT_SIZE
ALPHA_FIELD_LEVELS = (0, 128, 255)
ALPHA_FIELD_RGB = (40, 80, 220)
REGISTRATION_PATTERN = "registration_landmarks"
GLOSS_SIZE = (256, 256)
CHECKER_SQUARE = 16  # px je Schachbrettfeld bei 256 px Kantenlänge → 16×16 Felder.
STEP_LEVELS = 8  # diskrete Stufen für Höhen-/Gloss-„Treppenkeil"-Fixtures.
MM_PER_INCH = 25.4
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
            px_to_mm(combo.width, combo.conflict_dpi),
            px_to_mm(combo.height, combo.conflict_dpi),
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
    return specs


# ── Gloss-Fixtures (#690-Testdesign) ────────────────────────────────────────

_GLOSS_PATTERNS: tuple[tuple[str, Callable[[int, int], np.ndarray]], ...] = (
    ("min", _pattern_zero),
    ("max", _pattern_max),
    ("wedge", _pattern_wedge),
    ("wedge_inverted", _pattern_wedge_inverted),
    ("steps", _pattern_steps),
    ("checkerboard", _pattern_checkerboard),
)


def generate_gloss_fixtures() -> list[FixtureSpec]:
    width, height = GLOSS_SIZE
    specs: list[FixtureSpec] = []
    for name, builder in _GLOSS_PATTERNS:
        pattern = builder(width, height)
        params = {"width_px": width, "height_px": height}
        if name == "checkerboard":
            params["square_px"] = CHECKER_SQUARE
        specs.append(FixtureSpec(
            filename=f"gloss_{name}.png", role="gloss_mask", pattern=name,
            bit_depth=8, png_mode="L", image=_to_8bit_l(pattern), params=params,
        ))
    return specs


def generate_all_fixtures() -> list[FixtureSpec]:
    """Alle HEIGHT-, mm/DPI- und Gloss-Fixtures (reine In-Memory-Erzeugung)."""
    return [
        *generate_height_fixtures(),
        *generate_pixel_size_variant_fixture(),
        *generate_aspect_ratio_variant_fixture(),
        *generate_color_height_control_fixtures(),
        *generate_mm_dpi_fixtures(),
        *generate_gloss_fixtures(),
    ]


# ── Schreiben + Manifest ─────────────────────────────────────────────────────

def write_fixtures(specs: Iterable[FixtureSpec], out_dir: Path) -> dict[str, Any]:
    """Schreibt alle ``specs`` als PNG nach ``out_dir`` und das SHA-256-Manifest.

    Nach Dateiname sortiert, damit das Manifest unabhängig von der
    Erzeugungsreihenfolge byteidentisch bleibt (Determinismus-Test).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    for spec in sorted(specs, key=lambda s: s.filename):
        path = out_dir / spec.filename
        spec.image.save(path, "PNG", **spec.save_kwargs)
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
    manifest = {
        "schema": SCHEMA_VERSION,
        "generated_by": "scripts/eufymake_fixture_generator.py",
        "fixture_count": len(entries),
        "fixtures": entries,
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
    print(
        f"{manifest['fixture_count']} Fixtures geschrieben nach "
        f"{_rel(args.out_dir)} ({total_bytes / 1024:.1f} KiB), "
        f"Manifest: {_rel(args.out_dir / MANIFEST_FILENAME)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
