#!/usr/bin/env python3
"""Reproduzierbare A4-Platzierungsträger und Layout-Manifeste für #681 erzeugen.

Die erzeugten Vorschauen dienen nur zur Orientierung. Test-Fixtures werden nie
in sie reduziert: Native HEIGHT- und Gloss-Varnish-Zuweisungen müssen in
eufyMake Studio getrennte Objekte bleiben, damit die Hardwaretests aussagekräftig
bleiben.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "eufymake_hardware"
OUT = ROOT / "eufymake_a4_prints"

A4_W_MM = 210.0
A4_H_MM = 297.0
BED_W_MM = 335.0
BED_H_MM = 420.0
BED_X_MM = (BED_W_MM - A4_W_MM) / 2.0
BED_Y_MM = (BED_H_MM - A4_H_MM) / 2.0
PX_PER_MM = 10


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
    notes: str | None = None


@dataclass(frozen=True)
class Layout:
    number: int
    slug: str
    title: str
    budget_slots: list[str]
    copies: int
    objects: list[Obj] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


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
    notes: str | None = None,
) -> Obj:
    return Obj(label, source, role, x, y, w, h, ink, height, crop, notes)


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
            ["I-07 bleibt eine Budgetvariante mit zwei Messfeldern (Null und Maximum)."],
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
            ["I-10 normal Lauf 1", "I-10 invertiert Lauf 1"],
            1,
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def mm(value: float) -> int:
    return round(value * PX_PER_MM)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    filename = "Arial Bold.ttf" if bold else "Arial.ttf"
    return ImageFont.truetype(f"/System/Library/Fonts/Supplemental/{filename}", size=size)


def draw_carrier(layout: Layout) -> Image.Image:
    image = Image.new("RGBA", (mm(A4_W_MM), mm(A4_H_MM)), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    title = load_font(42, bold=True)
    small = load_font(30, bold=True)

    if layout.number == 7:
        draw.text(
            (mm(4), mm(291.5)),
            f"{layout.number:02d} · {layout.title}",
            font=small,
            fill=(0, 0, 0, 255),
        )
    else:
        draw.text(
            (mm(5), mm(5)), f"{layout.number:02d} · {layout.title}", font=title, fill=(0, 0, 0, 255)
        )

    seen: set[tuple[float, float, float, float]] = set()
    for item in layout.objects:
        key = (item.x_mm, item.y_mm, item.width_mm, item.height_mm)
        if key in seen:
            continue
        seen.add(key)
        label_y = max(0.8, item.y_mm - 4.4)
        draw.rectangle(
            (
                mm(item.x_mm),
                mm(label_y),
                mm(min(A4_W_MM, item.x_mm + item.width_mm)),
                mm(item.y_mm - 0.4),
            ),
            fill=(255, 255, 255, 220),
        )
        draw.text(
            (mm(item.x_mm + 0.7), mm(label_y + 0.2)), item.label, font=small, fill=(0, 0, 0, 255)
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
        draw.line((corner, horizontal), fill=(0, 0, 0, 255), width=width)
        draw.line((corner, vertical), fill=(0, 0, 0, 255), width=width)
    return image


def source_preview(item: Obj) -> Image.Image:
    if item.source is None:
        return Image.new("RGB", (32, 32), "white")
    path = FIXTURES / item.source
    with Image.open(path) as opened:
        image = opened.convert("RGBA")
    if item.role == "GLOSS":
        # Die Cyanfärbung unterscheidet ein natives Lackobjekt von COLOR in der Hilfe.
        gray = image.convert("L")
        cyan = Image.new("RGBA", image.size, (0, 150, 190, 205))
        cyan.putalpha(gray.point(lambda v: 40 + round(v * 0.65)))
        image = cyan
    elif item.height_source:
        height_path = FIXTURES / item.height_source
        with Image.open(height_path) as opened:
            height = opened.convert("L").resize(image.size, Image.Resampling.NEAREST)
        purple = Image.new("RGBA", image.size, (130, 50, 190, 255))
        purple.putalpha(height.point(lambda v: 45 + round(v * 0.55)))
        image = Image.alpha_composite(image, purple)
    return image


def draw_preview(layout: Layout, carrier: Image.Image) -> Image.Image:
    canvas = Image.new("RGBA", carrier.size, "white")
    for item in layout.objects:
        if item.role == "GLOSS" and any(
            other.role != "GLOSS"
            and abs(other.x_mm - item.x_mm) < 0.01
            and abs(other.y_mm - item.y_mm) < 0.01
            for other in layout.objects
        ):
            alpha = 115
        else:
            alpha = 255
        sample = source_preview(item)
        sample = sample.resize(
            (max(1, mm(item.width_mm)), max(1, mm(item.height_mm))), Image.Resampling.NEAREST
        )
        if alpha != 255:
            sample.putalpha(alpha)
        canvas.alpha_composite(sample, (mm(item.x_mm), mm(item.y_mm)))
    canvas.alpha_composite(carrier)
    return canvas.convert("RGB")


def object_record(item: Obj) -> dict[str, Any]:
    source_path = FIXTURES / item.source if item.source else None
    height_path = FIXTURES / item.height_source if item.height_source else None
    return {
        "label": item.label,
        "role": item.role,
        "source": item.source,
        "source_sha256": sha256(source_path) if source_path else None,
        "height_source": item.height_source,
        "height_source_sha256": sha256(height_path) if height_path else None,
        "a4_geometry_mm": {
            "x": item.x_mm,
            "y": item.y_mm,
            "width": item.width_mm,
            "height": item.height_mm,
            "rotation_degrees": 0,
        },
        "e1_flatbed_geometry_mm": {
            "x": round(BED_X_MM + item.x_mm, 3),
            "y": round(BED_Y_MM + item.y_mm, 3),
            "width": item.width_mm,
            "height": item.height_mm,
            "rotation_degrees": 0,
        },
        "ink_mode": item.ink_mode,
        "crop": item.crop,
        "notes": item.notes,
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    all_layouts = layouts()
    existing_manifest = (
        json.loads((OUT / "layout_manifest.json").read_text(encoding="utf-8"))
        if (OUT / "layout_manifest.json").exists()
        else {}
    )
    existing_layouts = {
        item["number"]: item for item in existing_manifest.get("layouts", [])
    }
    manifest: dict[str, Any] = {
        "schema": 1,
        "purpose": "Vorbereitung der physischen EufyMake-A4-Testdrucke für #681",
        "a4_mm": {"width": A4_W_MM, "height": A4_H_MM},
        "e1_flatbed_mm": {"width": BED_W_MM, "height": BED_H_MM},
        "a4_on_flatbed": {
            "rule": "zentriert, hochkant, Oberkante parallel zur Flatbed-Oberkante",
            "x": BED_X_MM,
            "y": BED_Y_MM,
        },
        "warnings": [
            "Vorschau-PNGs sind Platzierungshilfen und ersetzen KEINE nativen Fixture-Objekte.",
            "HEIGHT- oder GLOSS-Objekte nicht reduzieren.",
            "Beim bloßen Vorbereiten oder Prüfen weder Preview noch Print auslösen.",
        ],
        "layouts": [],
    }
    if "project_format" in existing_manifest:
        manifest["project_format"] = existing_manifest["project_format"]

    for layout in all_layouts:
        stem = f"{layout.number:02d}_{layout.slug}"
        layout_dir = OUT / stem
        layout_dir.mkdir(exist_ok=True)
        carrier = draw_carrier(layout)
        carrier_path = layout_dir / f"{stem}_A4_Beschriftung.png"
        carrier.save(carrier_path, dpi=(254, 254), compress_level=9)
        preview_path = layout_dir / f"{stem}_NUR_VORSCHAU.png"
        draw_preview(layout, carrier).save(preview_path, dpi=(254, 254), compress_level=9)

        record = {
            "number": layout.number,
            "slug": layout.slug,
            "title": layout.title,
            "budget_slots": layout.budget_slots,
            "physical_a4_copies": layout.copies,
            "carrier": str(carrier_path.relative_to(ROOT)),
            "carrier_sha256": sha256(carrier_path),
            "preview": str(preview_path.relative_to(ROOT)),
            "notes": layout.notes,
            "objects": [object_record(item) for item in layout.objects],
        }
        existing = existing_layouts.get(layout.number, {})
        project = existing.get("project")
        project_path = ROOT / project if project else None
        if project_path and project_path.is_file():
            record["project"] = project
            record["project_sha256"] = sha256(project_path)
            if "project_layers" in existing:
                record["project_layers"] = existing["project_layers"]
        (layout_dir / f"{stem}_Aufbau.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        manifest["layouts"].append(record)

    (OUT / "layout_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
