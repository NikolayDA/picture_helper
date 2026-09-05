#!/usr/bin/env python3
"""A4-Beschriftungsträger, Vorschauen und Layout-Manifeste für die Hardwaretests (#681).

Je Layout entstehen im Ordner ``eufymake_a4_prints/NN_<slug>/`` drei abgeleitete
Dateien: der transparente Beschriftungs- und Eckmarkenträger
(``*_A4_Beschriftung.png``), eine reine Platzierungshilfe
(``*_NUR_VORSCHAU.png``) und die Aufbau-Beschreibung (``*_Aufbau.json``); dazu
das Gesamtmanifest ``layout_manifest.json``. Die Vorschauen dienen nur zur
Orientierung. Test-Fixtures werden nie in sie reduziert: Native HEIGHT- und
Gloss-Varnish-Zuweisungen bleiben in eufyMake Studio getrennte Objekte, damit
die Hardwaretests aussagekräftig bleiben.

Bindungsmodell (fail-closed, Review-Befunde zu PR #971):

- ``projects.json`` im Ausgabeordner ist die **handgepflegte** Quelle der
  ``.empf``-Bindung: je Layout Projektpfad, SHA-256 des Projekts, SHA-256 des
  darin eingebetteten Trägers und die Studio-Ebenen. Der Generator liest sie
  nur. Fehlt eine Zuordnung, fehlt die Datei oder weicht ein Hash ab, bricht er
  **vor dem ersten Schreibzugriff** ab, statt still Felder wegzulassen.
- Jede referenzierte Quelldatei wird gegen ``tests/fixtures/eufymake_hardware/
  fixtures_manifest.json`` geprüft (unbekannter Pfad oder abweichender Hash =
  Abbruch), damit kein lokal veränderter Satz als Sollwert festgeschrieben wird.
- Träger sind an die ``.empf`` gebunden: Der gerenderte Träger wird nur
  geschrieben, wenn er byteidentisch zum gebundenen Stand ist oder
  ``--rebuild-carriers`` gesetzt ist. Sonst bleibt der gebundene Träger liegen,
  und der Lauf meldet die Abweichung (etwa durch eine andere Schrift). Nach
  ``--rebuild-carriers`` sind die betroffenen Projekte in Studio neu aufzubauen
  und ``projects.json`` ist nachzuziehen; bis dahin bleibt der Lauf rot.
- ``--check`` prüft den committeten Stand ohne Schreibzugriff (Bindung,
  Fixtures, Aufbau-JSONs, Manifest, Vorschau-Pixel) und ist der Wächter in
  ``tests/test_eufymake_a4_layouts.py``. Er braucht keine Schrift.

Die Studio-Koordinaten (``e1_flatbed_geometry_mm``) beziehen sich auf das
Standard-Flatbed des E1 (``STANDARD_FLATBED_MM``, 335 × 420 mm – vom Owner
bestätigt und identisch mit der in Studio 4.2.2 angezeigten Arbeitsfläche). Die
13 Projekte sind auf genau dieser Fläche gebaut; ändert sich die Konstante,
bricht der Generator ab, statt die Aufbau-JSONs still von den realen
Studio-Koordinaten der Projekte zu entkoppeln.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgremover.eufymake_export import STANDARD_FLATBED_MM  # noqa: E402
from bgremover.height_map import image_to_height_field  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "eufymake_hardware"
FIXTURES_MANIFEST_FILENAME = "fixtures_manifest.json"
OUT = ROOT / "eufymake_a4_prints"
PROJECTS_FILENAME = "projects.json"
MANIFEST_FILENAME = "layout_manifest.json"
CARRIER_LAYER_NAME = "A4 Beschriftung und Eckmarken"
STUDIO_ROLES = ("COLOR", "HEIGHT", "GLOSS")

A4_W_MM = 210.0
A4_H_MM = 297.0
PX_PER_MM = 10  # Träger und Vorschau mit 254 dpi

# Einzige Quelle des Flatbed-Maßes ist die Validator-Konstante (335 × 420 mm,
# Owner-Bestätigung 2026-09-03 in #971). Sie ist das Bezugssystem aller
# Studio-Koordinaten in den .empf-Projekten und identisch mit der Arbeitsfläche
# „Standard Flatbed“, die Studio 4.2.2 anzeigt (Zentrierung eines 101,60-mm-
# Objekts auf X = 116,70 mm im Studio-Protokoll, docs/history/EUFYMAKE-689-
# MM-DPI-VERTRAG.md; Importprotokoll I-05 in EUFYMAKE-687-PROTOKOLL-VORLAGEN.md).
FLATBED_MM = STANDARD_FLATBED_MM
# Fläche, auf der die 13 gebundenen .empf-Projekte tatsächlich aufgebaut wurden.
# Weicht die Konstante je davon ab, sind die Projekte in Studio neu aufzubauen;
# der Generator bricht dann ab (verify_flatbed_binding), statt Aufbau-JSONs zu
# schreiben, die nicht mehr zu den Projekten passen.
EMPF_CANVAS_MM = (335.0, 420.0)
A4_ORIGIN_MM = (
    (FLATBED_MM[0] - A4_W_MM) / 2.0,
    (FLATBED_MM[1] - A4_H_MM) / 2.0,
)

TITLE_FONT_PX = 42
LABEL_FONT_PX = 30
LABEL_GAP_MM = 0.4  # Abstand Kastenunterkante → Objektoberkante
LABEL_STEP_MM = 4.4  # Zeilenhöhe eines Beschriftungskastens inkl. Abstand
LABEL_PAD_MM = 0.7  # horizontaler Textabstand zum Kastenrand
LABEL_TOP_MIN_MM = 0.8
LABEL_FILL = (255, 255, 255, 220)
INK = (0, 0, 0, 255)
GLOSS_TINT = (0, 150, 190, 205)
HEIGHT_TINT = (130, 50, 190, 255)
OVERLAY_ALPHA = 115  # Gloss-Feld über einem COLOR-/HEIGHT-Feld: gedämpft zeichnen

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class PreparationError(RuntimeError):
    """Fail-closed-Abbruch: Bindung, Fixtures oder Schrift sind nicht belastbar."""


# ── Schrift ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FontCandidate:
    name: str
    bold: Path


# Reihenfolge = Präferenz. Die gebundenen Träger wurden mit Arial (macOS) erzeugt;
# Liberation Sans ist metrisch kompatibel zu Arial, DejaVu Sans der Rückfall.
# Eine andere Schrift ergibt andere Trägerbytes – deshalb meldet der Lauf
# immer, womit er gerendert hat, und überschreibt gebundene Träger nie still.
FONT_CANDIDATES: tuple[FontCandidate, ...] = (
    FontCandidate(
        "Arial Bold (macOS Supplemental)",
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ),
    FontCandidate(
        "Liberation Sans Bold (fonts-liberation)",
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ),
    FontCandidate(
        "DejaVu Sans Bold (fonts-dejavu-core)",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ),
)


def find_font() -> FontCandidate:
    for candidate in FONT_CANDIDATES:
        if candidate.bold.is_file():
            return candidate
    checked = ", ".join(str(candidate.bold) for candidate in FONT_CANDIDATES)
    raise PreparationError(
        "Keine Beschriftungsschrift gefunden. Geprüft: "
        f"{checked}. Unter Linux 'fonts-liberation' oder 'fonts-dejavu-core' "
        "installieren; die gebundenen Träger wurden mit Arial (macOS) erzeugt."
    )


@dataclass(frozen=True)
class Fonts:
    candidate: FontCandidate
    title: ImageFont.FreeTypeFont
    label: ImageFont.FreeTypeFont


def load_fonts(candidate: FontCandidate | None = None) -> Fonts:
    chosen = candidate or find_font()
    return Fonts(
        chosen,
        ImageFont.truetype(str(chosen.bold), size=TITLE_FONT_PX),
        ImageFont.truetype(str(chosen.bold), size=LABEL_FONT_PX),
    )


# ── Layout-Definition ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class Obj:
    label: str
    source: str | None
    role: str
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    ink_mode: str
    height_source: str | None = None
    crop: str | None = None
    #: Bildausschnitt (links, oben, rechts, unten) als Anteil 0..1, wie ihn der
    #: Studio-Crop erzeugt; nur für die Vorschau, die Quelldatei bleibt unberührt.
    crop_fraction: tuple[float, float, float, float] | None = None
    notes: str | None = None

    @property
    def studio_layer_role(self) -> str:
        return "HEIGHT" if self.role == "COLOR+HEIGHT" else self.role


@dataclass(frozen=True)
class Layout:
    number: int
    slug: str
    title: str
    budget_slots: list[str]
    copies: int
    objects: list[Obj] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    #: Begründung, warum der Karton bis zu einer Owner-Entscheidung nicht gedruckt wird.
    print_blocked: str | None = None
    #: Substratvorgabe aus Druck-Checkliste bzw. Gloss-Vertrag (None = keine Vorgabe).
    substrate: str | None = None

    @property
    def stem(self) -> str:
        return f"{self.number:02d}_{self.slug}"

    def expected_layers(self) -> list[dict[str, str]]:
        """Studio-Ebenen, die das gebundene Projekt laut Layout-Definition tragen muss."""
        layers = [{"name": CARRIER_LAYER_NAME, "role": "COLOR"}]
        layers.extend({"name": item.label, "role": item.studio_layer_role} for item in self.objects)
        return layers


def obj(
    label: str,
    source: str | None,
    role: str,
    x: float,
    y: float,
    w: float = 90.31,
    h: float = 90.31,
    *,
    ink: str = "Color Raised; Customize Texture; 2.50 mm",
    height: str | None = None,
    crop: str | None = None,
    crop_fraction: tuple[float, float, float, float] | None = None,
    notes: str | None = None,
) -> Obj:
    return Obj(label, source, role, x, y, w, h, ink, height, crop, crop_fraction, notes)


NON_WHITE_SUBSTRATE = (
    "nicht-weiß (Druck-Checkliste §0: Deckung und Weiß-Unterlage bleiben auf weißem "
    "Material unsichtbar); dasselbe in Protokoll §3.0 eingetragene Substrat für "
    "Karton 03 (I-13) und Karton 11 (G-06)"
)
I10_BLOCK_REASON = (
    "Option A im delegierten Owner-Auftrag vom 2026-09-05 (TESTGOVERNANCE): "
    "I-10 entfällt physisch; G-02 prüft beide Polaritäten mit je zwei unabhängigen Läufen. "
    "Projekt 05 bleibt gesperrt; Budgetplätze 9–10 bleiben unzugeordnet."
)


def layouts() -> list[Layout]:
    x1, x2, xc = 9.69, 110.00, 59.845
    y_mid = 103.345
    y_top, y_bottom = 30.0, 170.0
    y_top4, y_bottom4 = 27.0, 164.0
    return [
        Layout(
            1,
            "height_pixelgroesse_i02_i04",
            "I-02 / I-04 – HEIGHT-Pixelgröße",
            ["I-02 Lauf 1", "I-04 Lauf 1"],
            1,
            [
                obj(
                    "I-02 · 256 px",
                    "color_height_reference.png",
                    "COLOR+HEIGHT",
                    x1,
                    y_mid,
                    height="height_wedge_16bit.png",
                ),
                obj(
                    "I-04 · 128 px",
                    "color_height_reference.png",
                    "COLOR+HEIGHT",
                    x2,
                    y_mid,
                    height="height_wedge_16bit_half.png",
                ),
            ],
            ["Beide Objekte unverändert 90,31 × 90,31 mm; keine automatische Größenanpassung."],
        ),
        Layout(
            2,
            "height_bittiefe_filter_i03_i14",
            "I-03 / I-14 – Bittiefe und Filterung",
            ["I-03 8 Bit Lauf 1", "I-03 16 Bit Lauf 1 / I-14 Referenz", "I-14 128 px Lauf 1"],
            1,
            [
                obj(
                    "I-03 · 8 Bit",
                    "color_height_reference.png",
                    "COLOR+HEIGHT",
                    x1,
                    y_top,
                    height="height_impulse_edge_8bit.png",
                ),
                obj(
                    "I-03 · 16 Bit",
                    "color_height_reference.png",
                    "COLOR+HEIGHT",
                    x2,
                    y_top,
                    height="height_impulse_edge_16bit.png",
                ),
                obj(
                    "I-14 · direkt 128 px",
                    "color_height_reference.png",
                    "COLOR+HEIGHT",
                    xc,
                    y_bottom,
                    height="height_impulse_edge_direct_half_16bit.png",
                ),
            ],
            [
                "Alle drei COLOR-Objekte und alle HEIGHT-Parameter identisch; nur die bezeichnete HEIGHT-Datei wechselt."
            ],
        ),
        Layout(
            3,
            "height_grenzen_stufen_alpha_i07_i11_i13",
            "I-07 / I-11 / I-13 – Grenzen, Stufen, Alpha",
            ["I-07 Lauf 1", "I-11 Lauf 1", "I-13 Lauf 1"],
            1,
            [
                obj(
                    "I-07 · Null",
                    "color_height_reference.png",
                    "COLOR+HEIGHT",
                    x1,
                    y_top4,
                    height="height_zero_16bit.png",
                ),
                obj(
                    "I-07 · Maximum",
                    "color_height_reference.png",
                    "COLOR+HEIGHT",
                    x2,
                    y_top4,
                    height="height_max_16bit.png",
                ),
                obj(
                    "I-11 · 8 Stufen",
                    "color_height_reference.png",
                    "COLOR+HEIGHT",
                    x1,
                    y_bottom4,
                    height="height_steps_16bit.png",
                ),
                obj(
                    "I-13 · Alpha 0/128/255",
                    "color_alpha_coverage.png",
                    "COLOR+HEIGHT",
                    x2,
                    y_bottom4,
                    height="height_mean_16bit.png",
                ),
            ],
            [
                "I-07 bleibt eine Budgetvariante mit zwei Messfeldern (Null und Maximum).",
                "Wegen I-13 wird der ganze Karton auf nicht-weißem Substrat gedruckt (siehe substrate).",
            ],
            substrate=NON_WHITE_SUBSTRATE,
        ),
        Layout(
            4,
            "registrierung_crop_i08",
            "I-08 – Registrierung vor/nach Crop",
            ["I-08 vor Crop Lauf 1", "I-08 nach Crop Lauf 1"],
            1,
            [
                obj(
                    "I-08 · vor Crop",
                    "color_height_reference.png",
                    "COLOR+HEIGHT",
                    x1,
                    y_mid,
                    height="height_registration_16bit.png",
                ),
                obj(
                    "I-08 · Gloss vor",
                    "gloss_registration.png",
                    "GLOSS",
                    x1,
                    y_mid,
                    ink="Gloss Varnish × 1",
                ),
                obj(
                    "I-08 · nach Crop",
                    "color_height_reference.png",
                    "COLOR+HEIGHT",
                    155.45,
                    y_mid,
                    44.86,
                    90.31,
                    height="height_registration_16bit.png",
                    crop="rechte Bildhälfte; Studio-Crop, nicht extern vorbeschneiden",
                    crop_fraction=(0.5, 0.0, 1.0, 1.0),
                ),
                obj(
                    "I-08 · nach Crop · Gloss unverändert",
                    "gloss_registration.png",
                    "GLOSS",
                    x2,
                    y_mid,
                    ink="Gloss Varnish × 1",
                ),
            ],
            [
                "Nach-Crop-COLOR/HEIGHT rechtsbündig im unveränderten 90,31-mm-Glossfeld; X-Versatz 45,45 mm."
            ],
        ),
        Layout(
            5,
            "gloss_polaritaet_i10",
            "I-10 – Gloss-Polarität",
            [],
            0,
            [
                obj(
                    "I-10 · normal", "gloss_wedge.png", "GLOSS", x1, y_mid, ink="Gloss Varnish × 1"
                ),
                obj(
                    "I-10 · invertiert",
                    "gloss_wedge_inverted.png",
                    "GLOSS",
                    x2,
                    y_mid,
                    ink="Gloss Varnish × 1",
                ),
            ],
            [
                "Option A vom 2026-09-05: I-10 entfällt physisch; dieses historische Projekt nicht drucken."
            ],
            print_blocked=I10_BLOCK_REASON,
        ),
        Layout(
            6,
            "mm_dpi_i05",
            "I-05 – mm/DPI-Referenz",
            ["I-05 konsistent Lauf 1"],
            1,
            [
                obj(
                    "I-05 · 300 dpi · 101,60 mm",
                    "mm_typisch_phys.png",
                    "COLOR",
                    54.20,
                    97.70,
                    101.60,
                    101.60,
                    ink="Flat / Standard COLOR",
                )
            ],
            ["Native Studio-Ausdehnung 101,60 × 101,60 mm beibehalten."],
        ),
        Layout(
            7,
            "gloss_kennlinie_g01_g03",
            "G-01 / G-03 – Gloss-Grenzen und Kennlinie",
            ["G-01", "G-03"],
            1,
            [
                obj("G-01 · Wert 0", "gloss_min.png", "GLOSS", x1, 6.0, ink="Gloss Varnish × 1"),
                obj("G-01 · Wert 128", "gloss_mean.png", "GLOSS", x2, 6.0, ink="Gloss Varnish × 1"),
                obj(
                    "G-01 · Wert 255", "gloss_max.png", "GLOSS", x1, 103.35, ink="Gloss Varnish × 1"
                ),
                obj(
                    "G-03 · 8 Stufen",
                    "gloss_steps.png",
                    "GLOSS",
                    x2,
                    103.35,
                    ink="Gloss Varnish × 1",
                ),
                obj(
                    "G-03 · Keil 64…192",
                    "gloss_wedge_limited.png",
                    "GLOSS",
                    xc,
                    200.0,
                    ink="Gloss Varnish × 1",
                ),
            ],
            [
                "Alle fünf Felder mit identischem nativen Gloss-Varnish-Modus und identischer Passzahl."
            ],
        ),
        Layout(
            8,
            "gloss_polaritaet_g02",
            "G-02 – Gloss-Polarität (zweimal drucken)",
            ["G-02 normal Lauf 1+2", "G-02 invertiert Lauf 1+2"],
            2,
            [
                obj(
                    "G-02 · normal", "gloss_wedge.png", "GLOSS", x1, y_mid, ink="Gloss Varnish × 1"
                ),
                obj(
                    "G-02 · invertiert",
                    "gloss_wedge_inverted.png",
                    "GLOSS",
                    x2,
                    y_mid,
                    ink="Gloss Varnish × 1",
                ),
            ],
            ["Zwei unabhängige A4-Kartons; nicht zweimal auf denselben Karton drucken."],
        ),
        Layout(
            9,
            "gloss_optionalitaet_g04",
            "G-04 – fehlend / Null / Voll",
            ["G-04a/b/c"],
            1,
            [
                obj(
                    "G-04a · Gloss fehlt",
                    "export_gloss_absent/color_motif.png",
                    "COLOR",
                    x1,
                    y_top,
                    ink="Flat / Standard COLOR",
                    notes="Kein GLOSS-Objekt über diesem Feld.",
                ),
                obj(
                    "G-04b · Digitalwert 0",
                    "export_gloss_zero/color_motif.png",
                    "COLOR",
                    x2,
                    y_top,
                    ink="Flat / Standard COLOR",
                ),
                obj(
                    "G-04b · Gloss 0",
                    "export_gloss_zero/gloss_mask.png",
                    "GLOSS",
                    x2,
                    y_top,
                    ink="Gloss Varnish × 1",
                ),
                obj(
                    "G-04c · Digitalwert 255",
                    "export_gloss_full/color_motif.png",
                    "COLOR",
                    xc,
                    y_bottom,
                    ink="Flat / Standard COLOR",
                ),
                obj(
                    "G-04c · Gloss 255",
                    "export_gloss_full/gloss_mask.png",
                    "GLOSS",
                    xc,
                    y_bottom,
                    ink="Gloss Varnish × 1",
                ),
            ],
            [
                "G-04a enthält bewusst kein Gloss-Objekt; Schwarz/Weiß nicht semantisch umbenennen, bevor der Druck ausgewertet ist."
            ],
        ),
        Layout(
            10,
            "gloss_dimension_g05",
            "G-05 – abweichende Gloss-Dimension",
            ["G-05"],
            1,
            [
                obj(
                    "G-05 · COLOR 256×256",
                    "export_gloss_dimension_mismatch/color_motif.png",
                    "COLOR",
                    xc,
                    y_mid,
                    ink="Flat / Standard COLOR",
                ),
                obj(
                    "G-05 · GLOSS 128×256 auf COLOR 256×256",
                    "export_gloss_dimension_mismatch/gloss_mask.png",
                    "GLOSS",
                    xc,
                    y_mid,
                    45.16,
                    90.31,
                    ink="Gloss Varnish × 1",
                    notes="Oberkante und linke Kante deckungsgleich mit COLOR; keine Skalierung.",
                ),
            ],
            [
                "Verbindliche Regel: native 45,16 × 90,31 mm, oben/links bündig; rechte COLOR-Hälfte bleibt ohne Glossobjekt."
            ],
        ),
        Layout(
            11,
            "gloss_alpha_g06",
            "G-06 – Alpha × Gloss",
            ["G-06"],
            1,
            [
                obj(
                    "G-06 · Alpha 0/128/255",
                    "export_gloss_alpha_coverage/color_motif.png",
                    "COLOR+HEIGHT",
                    xc,
                    y_mid,
                    height="export_gloss_alpha_coverage/height_map.png",
                ),
                obj(
                    "G-06 · Gloss konstant 128",
                    "export_gloss_alpha_coverage/gloss_mask.png",
                    "GLOSS",
                    xc,
                    y_mid,
                    ink="Gloss Varnish × 1",
                ),
            ],
            ["COLOR/HEIGHT-Basis und konstante Glossmaske exakt deckungsgleich."],
            substrate=NON_WHITE_SUBSTRATE,
        ),
        Layout(
            12,
            "gloss_height_g07",
            "G-07 – HEIGHT × Gloss",
            ["G-07"],
            1,
            [
                obj(
                    "G-07 · HEIGHT 0/32768/65535",
                    "export_gloss_height_cross/color_motif.png",
                    "COLOR+HEIGHT",
                    xc,
                    y_mid,
                    height="export_gloss_height_cross/height_map.png",
                ),
                obj(
                    "G-07 · Gloss konstant 128",
                    "export_gloss_height_cross/gloss_mask.png",
                    "GLOSS",
                    xc,
                    y_mid,
                    ink="Gloss Varnish × 1",
                ),
            ],
            ["Color Raised 2,50 mm und Gloss Varnish × 1; beide Objekte exakt deckungsgleich."],
        ),
        Layout(
            13,
            "gloss_registrierung_g08",
            "G-08 – Registrierung und Mindeststruktur",
            ["G-08"],
            1,
            [
                obj(
                    "G-08 · Registrierung",
                    "color_height_reference.png",
                    "COLOR",
                    x1,
                    y_mid,
                    ink="Flat / Standard COLOR",
                ),
                obj(
                    "G-08 · Registriermaske",
                    "gloss_registration.png",
                    "GLOSS",
                    x1,
                    y_mid,
                    ink="Gloss Varnish × 1",
                ),
                obj(
                    "G-08 · 16-px-Schachbrett",
                    "gloss_checkerboard.png",
                    "GLOSS",
                    x2,
                    y_mid,
                    ink="Gloss Varnish × 1",
                ),
            ],
            [
                "Registriermaske deckungsgleich mit der Farbreferenz; Schachbrett als separates natives Glossfeld."
            ],
        ),
    ]


# ── Hilfen ────────────────────────────────────────────────────────────────


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path, base: Path = ROOT) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreparationError(f"{rel(path)}: {exc}") from exc
    if not isinstance(data, dict):
        raise PreparationError(f"{rel(path)}: Wurzel ist kein Objekt")
    return data


def mm(value: float) -> int:
    return round(value * PX_PER_MM)


def png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", dpi=(254, 254), compress_level=9)
    return buffer.getvalue()


# ── Flatbed-Bindung ───────────────────────────────────────────────────────


def verify_flatbed_binding() -> None:
    """Bricht ab, wenn die Konstante nicht mehr die Fläche der gebundenen Projekte ist."""
    if tuple(FLATBED_MM) != EMPF_CANVAS_MM:
        raise PreparationError(
            f"STANDARD_FLATBED_MM = {tuple(FLATBED_MM)} weicht von der Fläche "
            f"{EMPF_CANVAS_MM} ab, auf der die gebundenen .empf-Projekte aufgebaut sind – "
            "Projekte in Studio neu aufbauen, projects.json nachziehen und EMPF_CANVAS_MM "
            "bewusst anpassen"
        )


# ── Fixture-Abgleich ──────────────────────────────────────────────────────


def fixture_hashes(manifest: dict[str, Any]) -> dict[str, str]:
    """Sollwerte je Fixture-Pfad (Einzeldateien und Paketdateien) aus dem Manifest."""
    expected: dict[str, str] = {}
    for entry in manifest.get("fixtures", []):
        expected[str(entry["filename"])] = str(entry["sha256"])
    for bundle in manifest.get("bundles", []):
        directory = str(bundle["directory"])
        for entry in bundle.get("files", []):
            expected[f"{directory}/{entry['filename']}"] = str(entry["sha256"])
    if not expected:
        raise PreparationError("fixtures_manifest.json enthält keine Fixtures")
    return expected


def referenced_sources(all_layouts: list[Layout]) -> list[str]:
    names: list[str] = []
    for layout in all_layouts:
        for item in layout.objects:
            for name in (item.source, item.height_source):
                if name and name not in names:
                    names.append(name)
    return names


def verify_sources(
    all_layouts: list[Layout], expected: dict[str, str], fixtures_dir: Path
) -> tuple[dict[str, str], list[str]]:
    """Prüft jede referenzierte Quelldatei gegen das Fixture-Manifest; liefert die Hashes."""
    hashes: dict[str, str] = {}
    errors: list[str] = []
    for name in referenced_sources(all_layouts):
        path = fixtures_dir / name
        if name not in expected:
            errors.append(f"Quelle {name}: nicht in {FIXTURES_MANIFEST_FILENAME}")
            continue
        if not path.is_file():
            errors.append(f"Quelle {name}: Datei fehlt unter {rel(fixtures_dir)}")
            continue
        actual = sha256_file(path)
        if actual != expected[name]:
            errors.append(
                f"Quelle {name}: SHA-256 {actual[:12]}… weicht vom Manifest-Sollwert "
                f"{expected[name][:12]}… ab – Fixture-Satz verändert oder neu erzeugt?"
            )
            continue
        hashes[name] = actual
    return hashes, errors


# ── Handgepflegte Projektbindung ──────────────────────────────────────────


@dataclass(frozen=True)
class ProjectBinding:
    number: int
    project: str
    project_sha256: str
    carrier_sha256: str
    layers: tuple[dict[str, str], ...]
    thumbnail_sha256: str


@dataclass(frozen=True)
class ProjectsFile:
    carrier_font: str
    project_format: dict[str, Any]
    bindings: dict[int, ProjectBinding]


def _binding_from(raw: object, index: int) -> ProjectBinding:
    if not isinstance(raw, dict):
        raise PreparationError(f"projects.json: Eintrag {index} ist kein Objekt")
    number = raw.get("number")
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise PreparationError(f"projects.json: Eintrag {index} ohne gültige Layoutnummer")
    project = raw.get("project")
    if not isinstance(project, str) or not project.endswith(".empf"):
        raise PreparationError(f"projects.json: Layout {number:02d} ohne .empf-Pfad")
    for key in ("project_sha256", "carrier_sha256", "thumbnail_sha256"):
        value = raw.get(key)
        if not isinstance(value, str) or not _HEX64.match(value):
            raise PreparationError(
                f"projects.json: Layout {number:02d}: {key} ist kein SHA-256-Hexwert"
            )
    layers_raw = raw.get("layers")
    if not isinstance(layers_raw, list) or not layers_raw:
        raise PreparationError(f"projects.json: Layout {number:02d} ohne Studio-Ebenen")
    layers: list[dict[str, str]] = []
    for layer in layers_raw:
        if (
            not isinstance(layer, dict)
            or not isinstance(layer.get("name"), str)
            or layer.get("role") not in STUDIO_ROLES
        ):
            raise PreparationError(
                f"projects.json: Layout {number:02d}: Ebene {layer!r} braucht name und "
                f"role aus {STUDIO_ROLES}"
            )
        layers.append({"name": layer["name"], "role": layer["role"]})
    return ProjectBinding(
        number,
        project,
        raw["project_sha256"],
        raw["carrier_sha256"],
        tuple(layers),
        raw["thumbnail_sha256"],
    )


def load_projects(path: Path) -> ProjectsFile:
    """Liest die handgepflegte Bindungsdatei; jede Formverletzung ist ein Abbruch."""
    if not path.is_file():
        raise PreparationError(
            f"{rel(path)} fehlt – die handgepflegte .empf-Bindung ist Pflicht "
            "(siehe README, Abschnitt Bindung)"
        )
    data = load_json(path)
    if data.get("schema") != 1:
        raise PreparationError(f"{rel(path)}: unbekanntes Schema {data.get('schema')!r}")
    carrier_font = data.get("carrier_font")
    if not isinstance(carrier_font, str) or not carrier_font.strip():
        raise PreparationError(f"{rel(path)}: carrier_font fehlt")
    project_format = data.get("project_format")
    if not isinstance(project_format, dict) or not project_format:
        raise PreparationError(f"{rel(path)}: project_format fehlt")
    entries = data.get("projects")
    if not isinstance(entries, list) or not entries:
        raise PreparationError(f"{rel(path)}: projects ist keine nichtleere Liste")
    bindings: dict[int, ProjectBinding] = {}
    for index, raw in enumerate(entries):
        binding = _binding_from(raw, index)
        if binding.number in bindings:
            raise PreparationError(f"{rel(path)}: Layout {binding.number:02d} doppelt")
        bindings[binding.number] = binding
    return ProjectsFile(carrier_font, project_format, bindings)


def carrier_path_for(layout: Layout, out_dir: Path) -> Path:
    return out_dir / layout.stem / f"{layout.stem}_A4_Beschriftung.png"


def preview_path_for(layout: Layout, out_dir: Path) -> Path:
    return out_dir / layout.stem / f"{layout.stem}_NUR_VORSCHAU.png"


def record_path_for(layout: Layout, out_dir: Path) -> Path:
    return out_dir / layout.stem / f"{layout.stem}_Aufbau.json"


def project_path_for(layout: Layout, out_dir: Path) -> Path:
    return out_dir / layout.stem / f"{layout.stem}.empf"


def verify_bindings(
    all_layouts: list[Layout],
    projects: ProjectsFile,
    out_dir: Path,
    *,
    require_carriers: bool,
    allow_missing: bool,
) -> list[str]:
    """Bindung jedes Layouts an Projekt, Ebenen und eingebetteten Träger prüfen.

    ``require_carriers=False`` (nur ``--rebuild-carriers``) lässt die Trägerprüfung
    aus, weil die Träger gleich neu geschrieben werden; ``allow_missing=True``
    erlaubt Layouts ohne Bindung, damit ein neuer Karton überhaupt einen Träger
    bekommen kann, bevor sein Projekt in Studio existiert.
    """
    base = out_dir.parent
    errors: list[str] = []
    known = {layout.number for layout in all_layouts}
    for number in sorted(projects.bindings):
        if number not in known:
            errors.append(f"projects.json: Layout {number:02d} existiert nicht im Generator")
    for layout in all_layouts:
        binding = projects.bindings.get(layout.number)
        if binding is None:
            if not allow_missing:
                errors.append(
                    f"Layout {layout.stem}: keine Bindung in projects.json – erst das "
                    "Studio-Projekt aufbauen und eintragen"
                )
            continue
        project_path = project_path_for(layout, out_dir)
        expected_project = rel(project_path, base)
        if binding.project != expected_project:
            errors.append(
                f"Layout {layout.stem}: project muss {expected_project} sein, ist {binding.project}"
            )
        if not project_path.is_file():
            errors.append(f"Layout {layout.stem}: Projektdatei {expected_project} fehlt")
        else:
            actual = sha256_file(project_path)
            if actual != binding.project_sha256:
                errors.append(
                    f"Layout {layout.stem}: {expected_project} hat SHA-256 {actual[:12]}…, "
                    f"gebunden ist {binding.project_sha256[:12]}… – Projekt in Studio "
                    "geändert? projects.json (Hash und Ebenen) nachziehen"
                )
        if list(binding.layers) != layout.expected_layers():
            errors.append(
                f"Layout {layout.stem}: Studio-Ebenen in projects.json weichen von der "
                "Layout-Definition ab (Trägerebene + eine Ebene je Objekt, in Reihenfolge)"
            )
        if not require_carriers:
            continue
        carrier_path = carrier_path_for(layout, out_dir)
        if not carrier_path.is_file():
            errors.append(
                f"Layout {layout.stem}: gebundener Träger {rel(carrier_path, base)} fehlt – "
                "mit --rebuild-carriers erzeugen"
            )
            continue
        actual = sha256_file(carrier_path)
        if actual != binding.carrier_sha256:
            errors.append(
                f"Layout {layout.stem}: Träger {actual[:12]}… ist nicht der in "
                f"{expected_project} eingebettete Stand {binding.carrier_sha256[:12]}… – "
                ".empf in Studio neu aufbauen und projects.json nachziehen"
            )
    return errors


def verify_native_project(
    path: Path, layout: Layout, binding: ProjectBinding, source_hashes: dict[str, str]
) -> None:
    """Native Ebenen statt ausschließlich eines äußeren Prüfsummenvermerks prüfen."""
    with zipfile.ZipFile(path) as archive:
        canvases = [
            name
            for name in archive.namelist()
            if name.startswith("Asset/project_file/canvas_") and name.endswith(".json")
        ]
        if len(canvases) != 1:
            raise ValueError("Genau ein nativer Canvas erforderlich")
        metadata = json.loads(archive.read("Metadata/project_info.json"))
        print_params = json.loads(metadata["canvases"][0]["print_param"])
        if (print_params["format_size_w"], print_params["format_size_h"]) != EMPF_CANVAS_MM:
            raise ValueError("Native Flatbed-Fläche weicht ab")
        document = json.loads(archive.read(canvases[0]))
        objects = document["objects"]
        if len(objects) != len(layout.objects) + 1:
            raise ValueError("Native Ebenenzahl weicht ab")
        hashes: set[str] = set()

        def collect(value: Any) -> None:
            if isinstance(value, dict):
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)
            elif isinstance(value, str) and value.startswith("data:") and ";base64," in value:
                hashes.add(
                    sha256_bytes(base64.b64decode(value.split(";base64,", 1)[1], validate=True))
                )

        collect(document)
        required = {
            binding.carrier_sha256,
            *(source_hashes[source] for source in referenced_sources([layout])),
        }
        if not required <= hashes:
            raise ValueError("Native eingebettete Quellen oder Beschriftung weichen ab")
        if sha256_bytes(archive.read("Asset/images/thumbnail.png")) != binding.thumbnail_sha256:
            raise ValueError("Native Vorschau weicht ab")
        for index, native in enumerate(objects):
            if native.get("originX") not in ("left", "center", "right") or native.get(
                "originY"
            ) not in ("top", "center", "bottom"):
                raise ValueError("Ungültiger nativer Ursprung: originX/originY")
            values = [
                native[key]
                for key in ("left", "top", "width", "height", "scaleX", "scaleY", "angle")
            ]
            if not all(
                isinstance(value, (int, float)) and math.isfinite(value) for value in values
            ):
                raise ValueError("Nicht endliche native Geometrie")
            width = native["width"] * native["scaleX"] * 0.508
            height = native["height"] * native["scaleY"] * 0.508
            x = (
                native["left"] * 0.508
                - {"left": 0, "center": 0.5, "right": 1}[native["originX"]] * width
            )
            y = (
                native["top"] * 0.508
                - {"top": 0, "center": 0.5, "bottom": 1}[native["originY"]] * height
            )
            if index == 0:
                carrier_hash = sha256_bytes(
                    base64.b64decode(native["src"].split(";base64,", 1)[1], validate=True)
                )
                if carrier_hash != binding.carrier_sha256:
                    raise ValueError(
                        "Nativer Beschriftungsträger ist der falschen Ebene zugewiesen"
                    )
                expected = (A4_ORIGIN_MM[0], A4_ORIGIN_MM[1], A4_W_MM, A4_H_MM)
            else:
                item = layout.objects[index - 1]
                if (
                    item.source
                    and sha256_bytes(
                        base64.b64decode(native["src"].split(";base64,", 1)[1], validate=True)
                    )
                    != source_hashes[item.source]
                ):
                    raise ValueError("Native Quelle ist der falschen Ebene zugewiesen")
                if (
                    item.height_source
                    and sha256_bytes(
                        base64.b64decode(native["grayscale"].split(";base64,", 1)[1], validate=True)
                    )
                    != source_hashes[item.height_source]
                ):
                    raise ValueError("Native HEIGHT-Quelle ist der falschen Ebene zugewiesen")
                expected = (
                    A4_ORIGIN_MM[0] + item.x_mm,
                    A4_ORIGIN_MM[1] + item.y_mm,
                    item.width_mm,
                    item.height_mm,
                )
                if item.role == "GLOSS" and native.get("subPrintModel") != 2:
                    raise ValueError("Native Gloss-Zuweisung fehlt")
                if item.height_source and (
                    not native.get("_isCustomizeTexture") or native.get("thickness") != 2.5
                ):
                    raise ValueError("Native HEIGHT-Zuweisung oder Texturhöhe weicht ab")
            if (
                any(
                    abs(actual - wanted) > 0.02
                    for actual, wanted in zip((x, y, width, height), expected, strict=True)
                )
                or native["angle"] != 0
            ):
                raise ValueError(
                    f"Native Geometrie weicht ab: Layout {layout.number:02d}, Ebene {index}: {(x, y, width, height)} statt {expected}"
                )
            if native.get("_layerNameCus") != binding.layers[index]["name"]:
                raise ValueError("Native Ebenenbezeichnung weicht ab")


# ── Beschriftungsträger ───────────────────────────────────────────────────


@dataclass(frozen=True)
class LabelBox:
    text: str
    left_mm: float
    top_mm: float
    right_mm: float  # gezeichneter Kasten: Objektbreite, auf die A4-Breite geklemmt
    bottom_mm: float
    extent_right_mm: float  # Kollisionsfläche einschließlich überstehendem Text
    rows_up: int = 0  # 0 = direkt über dem Objekt, sonst um so viele Zeilen versetzt
    collides_with: str | None = None


def _overlaps(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def plan_labels(layout: Layout, label_font: ImageFont.FreeTypeFont) -> list[LabelBox]:
    """Beschriftungskästen platzieren; kollidierende Zeilen wandern nach oben.

    Objekte mit exakt gleicher Geometrie teilen sich eine Beschriftung (die des
    ersten Objekts). Überlappt der Kasten oder der überstehende Text eine schon
    gesetzte Zeile nur teilweise, wird er zeilenweise nach oben versetzt, statt
    die frühere Zeile zu übermalen.
    """
    placed: list[LabelBox] = []
    seen: set[tuple[float, float, float, float]] = set()
    for item in layout.objects:
        key = (item.x_mm, item.y_mm, item.width_mm, item.height_mm)
        if key in seen:
            continue
        seen.add(key)
        left = item.x_mm
        right = min(A4_W_MM, item.x_mm + item.width_mm)
        text_right = min(
            A4_W_MM,
            left + LABEL_PAD_MM + label_font.getlength(item.label) / PX_PER_MM + LABEL_PAD_MM,
        )
        extent_right = max(right, text_right)
        top = item.y_mm - LABEL_STEP_MM
        bottom = item.y_mm - LABEL_GAP_MM
        rows_up = 0
        collides_with: str | None = None
        while True:
            hit = next(
                (
                    other
                    for other in placed
                    if _overlaps(
                        (left, top, extent_right, bottom),
                        (other.left_mm, other.top_mm, other.extent_right_mm, other.bottom_mm),
                    )
                ),
                None,
            )
            if hit is None:
                break
            collides_with = collides_with or hit.text
            top -= LABEL_STEP_MM
            bottom -= LABEL_STEP_MM
            rows_up += 1
        if top < LABEL_TOP_MIN_MM:
            raise PreparationError(
                f"Layout {layout.stem}: Beschriftung {item.label!r} passt nicht über das "
                f"Objekt (Oberkante {top:.2f} mm)"
            )
        placed.append(
            LabelBox(item.label, left, top, right, bottom, extent_right, rows_up, collides_with)
        )
    return placed


def draw_carrier(layout: Layout, fonts: Fonts) -> tuple[Image.Image, list[LabelBox]]:
    image = Image.new("RGBA", (mm(A4_W_MM), mm(A4_H_MM)), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    caption = f"{layout.number:02d} · {layout.title}"
    if layout.number == 7:
        # Layout 07 belegt den oberen Rand; der Titel weicht nach unten aus.
        draw.text((mm(4), mm(291.5)), caption, font=fonts.label, fill=INK)
    else:
        draw.text((mm(5), mm(5)), caption, font=fonts.title, fill=INK)

    labels = plan_labels(layout, fonts.label)
    # Erst alle Kästen, dann alle Texte: ein später gezeichneter Kasten kann so
    # keine bereits gesetzte Zeile mehr löschen.
    for box in labels:
        draw.rectangle(
            (mm(box.left_mm), mm(box.top_mm), mm(box.right_mm), mm(box.bottom_mm)),
            fill=LABEL_FILL,
        )
    for box in labels:
        draw.text(
            (mm(box.left_mm + LABEL_PAD_MM), mm(box.top_mm + 0.2)),
            box.text,
            font=fonts.label,
            fill=INK,
        )

    # Vier nach innen versetzte Eckmarken machen den angenommenen A4-Ursprung prüfbar.
    mark = mm(5)
    inset = mm(3)
    width = max(2, mm(0.3))
    corners = [
        ((inset, inset), (inset + mark, inset), (inset, inset + mark)),
        (
            (mm(A4_W_MM) - inset, inset),
            (mm(A4_W_MM) - inset - mark, inset),
            (mm(A4_W_MM) - inset, inset + mark),
        ),
        (
            (inset, mm(A4_H_MM) - inset),
            (inset + mark, mm(A4_H_MM) - inset),
            (inset, mm(A4_H_MM) - inset - mark),
        ),
        (
            (mm(A4_W_MM) - inset, mm(A4_H_MM) - inset),
            (mm(A4_W_MM) - inset - mark, mm(A4_H_MM) - inset),
            (mm(A4_W_MM) - inset, mm(A4_H_MM) - inset - mark),
        ),
    ]
    for corner, horizontal, vertical in corners:
        draw.line((corner, horizontal), fill=INK, width=width)
        draw.line((corner, vertical), fill=INK, width=width)
    return image, labels


# ── Vorschau ──────────────────────────────────────────────────────────────


def height_display(path: Path) -> Image.Image:
    """8-Bit-Ansicht einer 8-/16-Bit-Höhenquelle über die kanonische Import-Regel (#589).

    Pillows ``convert("L")`` würde 16-Bit-Werte über 255 abschneiden statt zu
    skalieren; die 16-Bit-Fixtures erschienen dann als einfarbige Flächen.
    """
    with Image.open(path) as opened:
        opened.load()
        field_16bit = image_to_height_field(opened)
    display = (field_16bit.values.astype(np.uint32) * 255 // field_16bit.max_value).astype(np.uint8)
    return Image.fromarray(display, "L")


def object_sample(item: Obj, fixtures_dir: Path = FIXTURES) -> Image.Image:
    """Vorschaubild eines Objekts in Quellauflösung, Studio-Crop bereits angewendet."""
    if item.source is None:
        return Image.new("RGBA", (32, 32), "white")
    with Image.open(fixtures_dir / item.source) as opened:
        image = opened.convert("RGBA")
    if item.role == "GLOSS":
        # Die Cyanfärbung unterscheidet ein natives Lackobjekt von COLOR in der Hilfe;
        # die Glossform steckt allein im Alphakanal.
        gray = image.convert("L")
        cyan = Image.new("RGBA", image.size, GLOSS_TINT)
        cyan.putalpha(gray.point(lambda v: 40 + round(v * 0.65)))
        image = cyan
    elif item.height_source:
        height = height_display(fixtures_dir / item.height_source).resize(
            image.size, Image.Resampling.NEAREST
        )
        purple = Image.new("RGBA", image.size, HEIGHT_TINT)
        purple.putalpha(height.point(lambda v: 45 + round(v * 0.55)))
        image = Image.alpha_composite(image, purple)
    if item.crop_fraction is not None:
        left, top, right, bottom = item.crop_fraction
        width, height_px = image.size
        image = image.crop(
            (
                round(width * left),
                round(height_px * top),
                round(width * right),
                round(height_px * bottom),
            )
        )
    return image


def dim_alpha(image: Image.Image, alpha: int) -> Image.Image:
    """Skaliert den vorhandenen Alphakanal, statt ihn zu ersetzen (Glossform bleibt)."""
    if alpha >= 255:
        return image
    result = image.copy()
    result.putalpha(image.getchannel("A").point(lambda v: v * alpha // 255))
    return result


def _fields_overlap(a: Obj, b: Obj) -> bool:
    return _overlaps(
        (a.x_mm, a.y_mm, a.x_mm + a.width_mm, a.y_mm + a.height_mm),
        (b.x_mm, b.y_mm, b.x_mm + b.width_mm, b.y_mm + b.height_mm),
    )


def overlay_alpha(item: Obj, layout: Layout) -> int:
    """Gloss-Felder über COLOR-/HEIGHT-Feldern werden gedämpft, damit beide sichtbar bleiben."""
    if item.role == "GLOSS" and any(
        other.role != "GLOSS" and _fields_overlap(item, other) for other in layout.objects
    ):
        return OVERLAY_ALPHA
    return 255


def draw_preview(
    layout: Layout, carrier: Image.Image, fixtures_dir: Path = FIXTURES
) -> Image.Image:
    canvas = Image.new("RGBA", carrier.size, "white")
    for item in layout.objects:
        sample = object_sample(item, fixtures_dir).resize(
            (max(1, mm(item.width_mm)), max(1, mm(item.height_mm))), Image.Resampling.NEAREST
        )
        sample = dim_alpha(sample, overlay_alpha(item, layout))
        canvas.alpha_composite(sample, (mm(item.x_mm), mm(item.y_mm)))
    canvas.alpha_composite(carrier)
    return canvas.convert("RGB")


# ── Aufbau-JSON und Manifest ──────────────────────────────────────────────


def object_record(item: Obj, hashes: dict[str, str]) -> dict[str, Any]:
    return {
        "label": item.label,
        "role": item.role,
        "source": item.source,
        "source_sha256": hashes[item.source] if item.source else None,
        "height_source": item.height_source,
        "height_source_sha256": hashes[item.height_source] if item.height_source else None,
        "a4_geometry_mm": {
            "x": item.x_mm,
            "y": item.y_mm,
            "width": item.width_mm,
            "height": item.height_mm,
            "rotation_degrees": 0,
        },
        "e1_flatbed_geometry_mm": {
            "x": round(A4_ORIGIN_MM[0] + item.x_mm, 3),
            "y": round(A4_ORIGIN_MM[1] + item.y_mm, 3),
            "width": item.width_mm,
            "height": item.height_mm,
            "rotation_degrees": 0,
        },
        "ink_mode": item.ink_mode,
        "crop": item.crop,
        "crop_fraction": list(item.crop_fraction) if item.crop_fraction else None,
        "notes": item.notes,
    }


def layout_record(
    layout: Layout,
    *,
    out_dir: Path,
    carrier_sha256: str,
    hashes: dict[str, str],
    binding: ProjectBinding | None,
) -> dict[str, Any]:
    base = out_dir.parent
    record: dict[str, Any] = {
        "number": layout.number,
        "slug": layout.slug,
        "title": layout.title,
        "budget_slots": layout.budget_slots,
        "physical_a4_copies": layout.copies,
        "print_blocked": layout.print_blocked,
        "substrate": layout.substrate,
        "carrier": rel(carrier_path_for(layout, out_dir), base),
        "carrier_sha256": carrier_sha256,
        "preview": rel(preview_path_for(layout, out_dir), base),
        "notes": layout.notes,
        "objects": [object_record(item, hashes) for item in layout.objects],
    }
    if binding is not None:
        record["project"] = binding.project
        record["project_sha256"] = binding.project_sha256
        record["project_layers"] = [dict(layer) for layer in binding.layers]
    return record


def build_manifest(
    records: list[dict[str, Any]],
    projects: ProjectsFile,
    *,
    out_dir: Path,
    fixtures_manifest_sha256: str,
) -> dict[str, Any]:
    return {
        "schema": 1,
        "generated_by": "scripts/prepare_eufymake_a4_layouts.py",
        "purpose": "Vorbereitung der physischen EufyMake-A4-Testdrucke für #681",
        "a4_mm": {"width": A4_W_MM, "height": A4_H_MM},
        "e1_flatbed_mm": {
            "width": FLATBED_MM[0],
            "height": FLATBED_MM[1],
            "source": "bgremover.eufymake_export.STANDARD_FLATBED_MM",
            "meaning": (
                "Standard-Flatbed des E1: Arbeitsfläche „Standard Flatbed“ in eufyMake "
                "Studio 4.2.2 und Bezugssystem aller e1_flatbed_geometry_mm-Werte der "
                ".empf-Projekte"
            ),
            "evidence": [
                "Owner-Bestätigung 2026-09-03 (PR #971): Standard-Flatbed 335 × 420 mm",
                "docs/history/EUFYMAKE-689-MM-DPI-VERTRAG.md: Studio-Protokoll vom 2026-09-02/03 "
                "(101,60 mm zentriert auf X = 116,70 mm)",
                "docs/history/EUFYMAKE-687-PROTOKOLL-VORLAGEN.md: Importprotokoll I-05 "
                "(Standard Flatbed 335×420 mm)",
            ],
        },
        "a4_on_flatbed": {
            "rule": "zentriert, hochkant, Oberkante parallel zur Flatbed-Oberkante",
            "coordinate_reference": "e1_flatbed_mm",
            "x": A4_ORIGIN_MM[0],
            "y": A4_ORIGIN_MM[1],
        },
        "sources": {
            "fixtures_manifest": rel(FIXTURES / FIXTURES_MANIFEST_FILENAME),
            "fixtures_manifest_sha256": fixtures_manifest_sha256,
            "projects": rel(out_dir / PROJECTS_FILENAME, out_dir.parent),
            "carrier_font": projects.carrier_font,
        },
        "binding_rule": (
            "project_sha256 und carrier_sha256 jedes Layouts sind beim Erzeugen gegen "
            "projects.json und die Dateien geprüft. Träger werden nur byteidentisch oder "
            "bewusst mit --rebuild-carriers überschrieben; danach ist das Projekt in Studio "
            "neu aufzubauen und projects.json nachzuziehen."
        ),
        "warnings": [
            "Vorschau-PNGs sind Platzierungshilfen und ersetzen KEINE nativen Fixture-Objekte.",
            "HEIGHT- oder GLOSS-Objekte nicht reduzieren.",
            "Beim bloßen Vorbereiten oder Prüfen weder Preview noch Print auslösen.",
            "Layouts mit print_blocked werden nicht gedruckt; I-10 entfällt gemäß Option A.",
            "Druckfreigabe aller aktiven Layouts offen: Gerät, Gloss-Material und Messmittel klären "
            "(docs/history/EUFYMAKE-681-VORBEREITUNG-2026-09-05.md).",
        ],
        "project_format": projects.project_format,
        "layouts": records,
    }


# ── Lauf ──────────────────────────────────────────────────────────────────


def _dumps(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def run(
    *,
    out_dir: Path = OUT,
    fixtures_dir: Path = FIXTURES,
    mode: str = "write",
    log: Any = print,
) -> int:
    """Erzeugt (``write``/``rebuild``) oder prüft (``check``) den Satz; 0 = in Ordnung."""
    if mode not in ("write", "check", "rebuild"):
        raise ValueError(f"unbekannter Modus {mode!r}")
    verify_flatbed_binding()
    all_layouts = layouts()
    fixtures_manifest_path = fixtures_dir / FIXTURES_MANIFEST_FILENAME
    expected = fixture_hashes(load_json(fixtures_manifest_path))
    hashes, errors = verify_sources(all_layouts, expected, fixtures_dir)
    projects = load_projects(out_dir / PROJECTS_FILENAME)
    errors.extend(
        verify_bindings(
            all_layouts,
            projects,
            out_dir,
            require_carriers=mode != "rebuild",
            allow_missing=mode == "rebuild",
        )
    )
    if errors:
        raise PreparationError("\n".join(errors))
    for layout in all_layouts:
        binding = projects.bindings.get(layout.number)
        if binding is None:
            continue
        try:
            verify_native_project(project_path_for(layout, out_dir), layout, binding, hashes)
        except (ValueError, KeyError, TypeError, IndexError, zipfile.BadZipFile) as exc:
            errors.append(f"Layout {layout.stem}: nativer Projektcontainer ungültig: {exc}")
    if errors:
        raise PreparationError("\n".join(errors))
    log(f"[a4-layouts] ok: {len(hashes)} Quelldateien gegen {FIXTURES_MANIFEST_FILENAME} geprüft")
    bound = sum(1 for layout in all_layouts if layout.number in projects.bindings)
    log(
        f"[a4-layouts] ok: Bindung von {bound}/{len(all_layouts)} Projekten gegen projects.json geprüft"
    )

    fonts: Fonts | None = None
    try:
        fonts = load_fonts()
    except PreparationError:
        if mode != "check":
            raise
        log("[a4-layouts] keine Schrift gefunden – Render-Abgleich der Träger übersprungen")
    if fonts is not None:
        log(f"[a4-layouts] Schrift: {fonts.candidate.name} ({fonts.candidate.bold})")

    base = out_dir.parent
    records: list[dict[str, Any]] = []
    drift: list[str] = []
    rebuilt: list[str] = []
    render_drift: list[str] = []
    for layout in all_layouts:
        carrier_path = carrier_path_for(layout, out_dir)
        preview_path = preview_path_for(layout, out_dir)
        record_path = record_path_for(layout, out_dir)
        rendered: bytes | None = None
        if fonts is not None:
            image, labels = draw_carrier(layout, fonts)
            for box in labels:
                if box.rows_up:
                    log(
                        f"[a4-layouts] Beschriftung {layout.stem}: {box.text!r} um "
                        f"{box.rows_up} Zeile(n) nach oben versetzt (Kollision mit "
                        f"{box.collides_with!r})"
                    )
            rendered = png_bytes(image)
        bound_bytes = carrier_path.read_bytes() if carrier_path.is_file() else None
        if mode == "rebuild":
            assert rendered is not None
            if bound_bytes != rendered:
                carrier_path.parent.mkdir(parents=True, exist_ok=True)
                carrier_path.write_bytes(rendered)
                rebuilt.append(layout.stem)
            carrier_bytes = rendered
        else:
            assert bound_bytes is not None  # durch verify_bindings gesichert
            carrier_bytes = bound_bytes
            if rendered is not None and rendered != bound_bytes:
                render_drift.append(layout.stem)
        with Image.open(io.BytesIO(carrier_bytes)) as opened:
            carrier_image = opened.convert("RGBA")
        preview = draw_preview(layout, carrier_image, fixtures_dir)
        record = layout_record(
            layout,
            out_dir=out_dir,
            carrier_sha256=sha256_bytes(carrier_bytes),
            hashes=hashes,
            binding=projects.bindings.get(layout.number),
        )
        record_text = _dumps(record)
        if mode == "check":
            if not record_path.is_file() or record_path.read_text(encoding="utf-8") != record_text:
                drift.append(rel(record_path, base))
            if not preview_path.is_file():
                drift.append(rel(preview_path, base))
            else:
                with Image.open(preview_path) as opened:
                    stored = opened.convert("RGB")
                    if stored.size != preview.size or stored.tobytes() != preview.tobytes():
                        drift.append(rel(preview_path, base))
        else:
            preview_path.parent.mkdir(parents=True, exist_ok=True)
            preview.save(preview_path, dpi=(254, 254), compress_level=9)
            record_path.write_text(record_text, encoding="utf-8")
        records.append(record)

    manifest_text = _dumps(
        build_manifest(
            records,
            projects,
            out_dir=out_dir,
            fixtures_manifest_sha256=sha256_file(fixtures_manifest_path),
        )
    )
    manifest_path = out_dir / MANIFEST_FILENAME
    if mode == "check":
        if (
            not manifest_path.is_file()
            or manifest_path.read_text(encoding="utf-8") != manifest_text
        ):
            drift.append(rel(manifest_path, base))
        for path in drift:
            log(f"[a4-layouts] DRIFT: {path} weicht vom Generatorstand ab")
        if drift:
            return 1
        log(
            f"[a4-layouts] ok: {len(records)} Aufbau-JSONs, Vorschauen und {MANIFEST_FILENAME} stimmen"
        )
        return 0

    manifest_path.write_text(manifest_text, encoding="utf-8")
    log(
        f"[a4-layouts] geschrieben: {len(records)} Aufbau-JSONs, {len(records)} Vorschauen, {MANIFEST_FILENAME}"
    )
    for stem in render_drift:
        log(
            f"[a4-layouts] HINWEIS {stem}: gerenderter Träger weicht vom gebundenen Stand ab – "
            "gebundener Träger bleibt; bewusst neu erzeugen mit --rebuild-carriers"
        )
    if rebuilt:
        log(
            "[a4-layouts] WARNUNG: Träger neu geschrieben für "
            + ", ".join(rebuilt)
            + " – in Studio die Ebene "
            f"{CARRIER_LAYER_NAME!r} ersetzen, Projekt speichern und in projects.json "
            "project_sha256, carrier_sha256 und carrier_font nachziehen; bis dahin bricht der "
            "Lauf ohne --rebuild-carriers ab."
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="A4-Träger, Vorschauen und Manifeste der EufyMake-Hardwaretests erzeugen."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--check",
        action="store_true",
        help="nur prüfen, nichts schreiben; Exit 1 bei Abweichung vom Generatorstand",
    )
    group.add_argument(
        "--rebuild-carriers",
        action="store_true",
        help="gerenderte Träger auch schreiben, wenn sie vom gebundenen Stand abweichen",
    )
    parser.add_argument("--out", type=Path, default=OUT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    mode = "check" if args.check else "rebuild" if args.rebuild_carriers else "write"
    try:
        return run(out_dir=args.out.resolve(), mode=mode)
    except PreparationError as exc:
        print(f"[a4-layouts] FEHLER: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
