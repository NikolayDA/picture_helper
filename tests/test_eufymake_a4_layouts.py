"""Wächter für den A4-Drucksatz der EufyMake-Hardwaretests (#681, Review zu PR #971).

Der committete Satz unter ``eufymake_a4_prints/`` ist handgepflegtes
Testmaterial (``.empf``-Projekte, ``projects.json``) mit generierten
Ableitungen (Träger, Vorschauen, Aufbau-JSONs, Manifest). Dieser Test hält ihn
netzfrei zusammen:

* ``--check`` des Generators: Quell-Hashes gegen ``fixtures_manifest.json``,
  Projekt-/Träger-/Ebenen-Bindung gegen ``projects.json``, Aufbau-JSONs,
  Manifest und Vorschau-Pixel gegen den Generatorstand – ohne Schreibzugriff
  und ohne Schrift.
* README-Tabelle gegen das Manifest (13 Layouts, Kartonzahl, Sperre, Substrat).
* Bezugsflächen: Studio-Arbeitsfläche 335 × 420 mm und bedruckbare Fläche aus
  ``STANDARD_FLATBED_MM`` getrennt; Studio-Koordinaten = A4-Koordinaten + Ursprung.
* Vorschau-Regeln aus den Review-Befunden: Glossform überlebt die Dämpfung,
  16-Bit-Höhen werden skaliert statt geklemmt, der I-08-Crop wird angewendet.
* Beschriftungen: kollidierende Zeilen werden gestapelt statt übermalt
  (schriftabhängig; ohne installierte Schrift übersprungen).
* Negativfälle der fail-closed Bindung und des Fixture-Abgleichs.
"""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from bgremover.eufymake_export import STANDARD_FLATBED_MM
from scripts import prepare_eufymake_a4_layouts as gen

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eufymake_a4_prints"
README = OUT / "README.md"

#: ``| 05 | Titel | Druckzelle | 1 | Budget |`` – die Kartonzahl darf fett sein.
_ROW_RE = re.compile(r"^\| (\d{2}) \| (.+?) \| (.+?) \| \**(\d+)\** \| (.+?) \|$", re.MULTILINE)


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads((OUT / "layout_manifest.json").read_text(encoding="utf-8"))


def _fonts_or_skip() -> gen.Fonts:
    try:
        return gen.load_fonts()
    except gen.PreparationError:
        pytest.skip("keine Beschriftungsschrift installiert")


# ── committeter Satz ──────────────────────────────────────────────────────


def test_committed_set_passes_generator_check(capsys: pytest.CaptureFixture[str]) -> None:
    assert gen.main(["--check"]) == 0
    captured = capsys.readouterr()
    assert "DRIFT" not in captured.out
    assert "FEHLER" not in captured.err


def test_readme_table_matches_manifest(manifest: dict) -> None:
    text = README.read_text(encoding="utf-8")
    rows = _ROW_RE.findall(text)
    layouts = {record["number"]: record for record in manifest["layouts"]}
    assert [int(number) for number, *_ in rows] == sorted(layouts) == list(range(1, 14))
    for number, title, print_cell, copies, _budget in rows:
        record = layouts[int(number)]
        assert title == record["title"], number
        assert int(copies) == record["physical_a4_copies"], number
        assert ("gesperrt" in print_cell) == (record["print_blocked"] is not None), number
        assert ("nicht-weiß" in print_cell) == (record["substrate"] is not None), number
    total = sum(record["physical_a4_copies"] for record in layouts.values())
    free = sum(
        record["physical_a4_copies"]
        for record in layouts.values()
        if record["print_blocked"] is None
    )
    assert f"{total} A4-Kartons" in text
    assert f"{free} davon" in text


def test_layout_05_is_omitted_under_option_a(manifest: dict) -> None:
    blocked = [record["number"] for record in manifest["layouts"] if record["print_blocked"]]
    assert blocked == [5]
    assert "Option A" in manifest["layouts"][4]["print_blocked"]
    assert manifest["layouts"][4]["physical_a4_copies"] == 0
    assert manifest["layouts"][4]["budget_slots"] == []
    assert any("print_blocked" in warning for warning in manifest["warnings"])


def test_non_white_substrate_is_shared_by_i13_and_g06(manifest: dict) -> None:
    with_substrate = [record["number"] for record in manifest["layouts"] if record["substrate"]]
    assert with_substrate == [3, 11]
    assert len({record["substrate"] for record in manifest["layouts"] if record["substrate"]}) == 1


def test_flatbed_reference_comes_from_the_validator_constant(manifest: dict) -> None:
    flatbed = manifest["e1_flatbed_mm"]
    assert (flatbed["width"], flatbed["height"]) == STANDARD_FLATBED_MM == (335.0, 420.0)
    assert flatbed["source"] == "bgremover.eufymake_export.STANDARD_FLATBED_MM"
    assert flatbed["evidence"]
    assert "printable_area_mm" not in manifest and "studio_flatbed_mm" not in manifest
    # Die gebundenen Projekte sind auf genau dieser Fläche gebaut.
    assert gen.EMPF_CANVAS_MM == STANDARD_FLATBED_MM
    origin = manifest["a4_on_flatbed"]
    assert origin["coordinate_reference"] == "e1_flatbed_mm"
    assert (origin["x"], origin["y"]) == ((335.0 - 210.0) / 2, (420.0 - 297.0) / 2)
    for record in manifest["layouts"]:
        for item in record["objects"]:
            a4, flatbed_geometry = item["a4_geometry_mm"], item["e1_flatbed_geometry_mm"]
            assert flatbed_geometry["x"] == pytest.approx(a4["x"] + origin["x"], abs=1e-6)
            assert flatbed_geometry["y"] == pytest.approx(a4["y"] + origin["y"], abs=1e-6)
            assert a4["x"] >= 0 and a4["y"] >= 0
            assert a4["x"] + a4["width"] <= 210.0 + 1e-9
            assert a4["y"] + a4["height"] <= 297.0 + 1e-9


def test_changed_flatbed_constant_blocks_the_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gen, "FLATBED_MM", (330.0, 420.0))
    with pytest.raises(gen.PreparationError, match="STANDARD_FLATBED_MM"):
        gen.run(mode="check", log=lambda *_: None)


def test_manifest_binds_every_layout_to_a_verified_project(manifest: dict) -> None:
    projects = gen.load_projects(OUT / gen.PROJECTS_FILENAME)
    assert sorted(projects.bindings) == list(range(1, 14))
    for record in manifest["layouts"]:
        binding = projects.bindings[record["number"]]
        assert record["project"] == binding.project
        assert record["project_sha256"] == binding.project_sha256
        assert record["carrier_sha256"] == binding.carrier_sha256
        assert record["project_layers"] == list(binding.layers)
    assert manifest["sources"]["carrier_font"] == projects.carrier_font
    fixtures_manifest = gen.FIXTURES / gen.FIXTURES_MANIFEST_FILENAME
    assert manifest["sources"]["fixtures_manifest_sha256"] == gen.sha256_file(fixtures_manifest)


# ── Vorschau-Regeln ───────────────────────────────────────────────────────


def _gloss(source: str) -> gen.Obj:
    return gen.obj("x", source, "GLOSS", 0.0, 0.0, ink="Gloss Varnish × 1")


def test_dimmed_gloss_preview_keeps_mask_shape_and_level() -> None:
    zero = gen.dim_alpha(gen.object_sample(_gloss("export_gloss_zero/gloss_mask.png")), 115)
    full = gen.dim_alpha(gen.object_sample(_gloss("export_gloss_full/gloss_mask.png")), 115)
    zero_alpha, full_alpha = zero.getchannel("A").getextrema(), full.getchannel("A").getextrema()
    assert zero_alpha[1] < full_alpha[0], "Gloss 0 und Gloss 255 müssen sich unterscheiden"
    registration = gen.dim_alpha(gen.object_sample(_gloss("gloss_registration.png")), 115)
    low, high = registration.getchannel("A").getextrema()
    assert low < high, "die Registrierstruktur muss die Dämpfung überleben"
    assert high <= 115


def test_dim_alpha_scales_instead_of_replacing() -> None:
    image = Image.new("RGBA", (2, 1))
    image.putdata([(0, 0, 0, 255), (0, 0, 0, 51)])
    dimmed = gen.dim_alpha(image, 115)
    assert np.asarray(dimmed.getchannel("A")).tolist() == [[115, 23]]
    assert gen.dim_alpha(image, 255) is image


def test_height_preview_scales_16bit_instead_of_clipping() -> None:
    sixteen = gen.height_display(gen.FIXTURES / "height_impulse_edge_16bit.png")
    eight = Image.open(gen.FIXTURES / "height_impulse_edge_8bit.png").convert("L")
    assert sixteen.size == eight.size
    low, high = sixteen.getextrema()
    assert low < high, "das 16-Bit-Feld darf nicht einfarbig werden"
    difference = np.abs(np.asarray(sixteen, dtype=np.int16) - np.asarray(eight, dtype=np.int16))
    assert int(difference.max()) <= 1, "8- und 16-Bit-Zwilling zeigen dasselbe Muster"
    wedge = gen.height_display(gen.FIXTURES / "height_wedge_16bit.png")
    assert len(np.unique(np.asarray(wedge))) > 100


def test_crop_fraction_selects_right_half_for_i08() -> None:
    layout = next(item for item in gen.layouts() if item.number == 4)
    cropped = next(item for item in layout.objects if item.crop_fraction)
    assert cropped.crop_fraction == (0.5, 0.0, 1.0, 1.0)
    full = gen.object_sample(replace(cropped, crop_fraction=None))
    half = gen.object_sample(cropped)
    assert half.size == (full.width // 2, full.height)
    expected = full.crop((full.width // 2, 0, full.width, full.height))
    assert half.tobytes() == expected.tobytes()


def test_gloss_over_color_field_is_dimmed_even_when_offset() -> None:
    layout = next(item for item in gen.layouts() if item.number == 4)
    by_label = {item.label: item for item in layout.objects}
    # Das unveränderte Glossfeld (x = 110) überlappt das beschnittene COLOR-Feld
    # (x = 155,45) nur teilweise – es muss trotzdem gedämpft werden.
    assert gen.overlay_alpha(by_label["I-08 · nach Crop · Gloss unverändert"], layout) == 115
    assert gen.overlay_alpha(by_label["I-08 · nach Crop"], layout) == 255
    standalone = next(item for item in gen.layouts() if item.number == 7)
    assert all(gen.overlay_alpha(item, standalone) == 255 for item in standalone.objects)


# ── Beschriftungen ────────────────────────────────────────────────────────


def test_labels_stack_instead_of_overpainting() -> None:
    fonts = _fonts_or_skip()
    by_number = {layout.number: layout for layout in gen.layouts()}
    boxes = gen.plan_labels(by_number[10], fonts.label)
    assert [box.text for box in boxes] == [
        "G-05 · COLOR 256×256",
        "G-05 · GLOSS 128×256 auf COLOR 256×256",
    ]
    assert boxes[1].rows_up == 1
    assert boxes[1].bottom_mm <= boxes[0].top_mm
    boxes_04 = {box.text: box for box in gen.plan_labels(by_number[4], fonts.label)}
    assert boxes_04["I-08 · nach Crop · Gloss unverändert"].rows_up == 1
    assert boxes_04["I-08 · nach Crop"].rows_up == 0
    stacked: list[int] = []
    for layout in gen.layouts():
        placed = gen.plan_labels(layout, fonts.label)
        if any(box.rows_up for box in placed):
            stacked.append(layout.number)
        for index, first in enumerate(placed):
            for second in placed[index + 1 :]:
                assert not gen._overlaps(
                    (first.left_mm, first.top_mm, first.extent_right_mm, first.bottom_mm),
                    (second.left_mm, second.top_mm, second.extent_right_mm, second.bottom_mm),
                ), (layout.number, first.text, second.text)
    assert stacked == [4, 10]


def test_carrier_keeps_every_label_readable() -> None:
    fonts = _fonts_or_skip()
    layout = next(item for item in gen.layouts() if item.number == 10)
    image, labels = gen.draw_carrier(layout, fonts)
    assert len(labels) == 2
    for box in labels:
        # Im Bereich jeder Zeile muss Tinte liegen – vorher wurde die erste Zeile übermalt.
        region = image.crop(
            (gen.mm(box.left_mm), gen.mm(box.top_mm), gen.mm(box.right_mm), gen.mm(box.bottom_mm))
        )
        assert region.getchannel("R").getextrema()[0] == 0, box.text


# ── fail-closed ───────────────────────────────────────────────────────────


def test_stale_project_hash_is_rejected() -> None:
    projects = gen.load_projects(OUT / gen.PROJECTS_FILENAME)
    stale = dict(projects.bindings)
    stale[1] = replace(stale[1], project_sha256="0" * 64)
    errors = gen.verify_bindings(
        gen.layouts(),
        replace(projects, bindings=stale),
        OUT,
        require_carriers=True,
        allow_missing=False,
    )
    assert len(errors) == 1
    assert "01_height_pixelgroesse_i02_i04" in errors[0] and "SHA-256" in errors[0]


def test_missing_binding_and_drifted_layers_are_rejected() -> None:
    projects = gen.load_projects(OUT / gen.PROJECTS_FILENAME)
    bindings = dict(projects.bindings)
    del bindings[13]
    bindings[2] = replace(bindings[2], layers=bindings[2].layers[:-1])
    errors = gen.verify_bindings(
        gen.layouts(),
        replace(projects, bindings=bindings),
        OUT,
        require_carriers=True,
        allow_missing=False,
    )
    assert any(
        "13_gloss_registrierung_g08" in error and "keine Bindung" in error for error in errors
    )
    assert any(
        "02_height_bittiefe_filter_i03_i14" in error and "Ebenen" in error for error in errors
    )
    relaxed = gen.verify_bindings(
        gen.layouts(),
        replace(projects, bindings=bindings),
        OUT,
        require_carriers=False,
        allow_missing=True,
    )
    assert not any("keine Bindung" in error for error in relaxed)


def test_unbound_carrier_is_rejected(tmp_path: Path) -> None:
    copy = tmp_path / "eufymake_a4_prints"
    shutil.copytree(OUT, copy)
    carrier = gen.carrier_path_for(gen.layouts()[0], copy)
    carrier.write_bytes(carrier.read_bytes() + b"\n")
    with pytest.raises(gen.PreparationError, match="eingebettete Stand"):
        gen.run(out_dir=copy, mode="check", log=lambda *_: None)


def test_unknown_or_changed_fixture_source_is_rejected() -> None:
    expected = gen.fixture_hashes(
        json.loads((gen.FIXTURES / gen.FIXTURES_MANIFEST_FILENAME).read_text(encoding="utf-8"))
    )
    typo = [gen.Layout(99, "typo", "T", [], 1, [gen.obj("x", "does_not_exist.png", "COLOR", 0, 0)])]
    _hashes, errors = gen.verify_sources(typo, expected, gen.FIXTURES)
    assert errors == ["Quelle does_not_exist.png: nicht in fixtures_manifest.json"]
    tampered = dict(expected)
    tampered["gloss_min.png"] = "f" * 64
    changed = [gen.Layout(98, "x", "T", [], 1, [_gloss("gloss_min.png")])]
    _hashes, errors = gen.verify_sources(changed, tampered, gen.FIXTURES)
    assert len(errors) == 1 and "weicht vom Manifest-Sollwert" in errors[0]


def test_write_run_reproduces_committed_outputs_and_keeps_bound_carriers(tmp_path: Path) -> None:
    _fonts_or_skip()
    copy = tmp_path / "eufymake_a4_prints"
    shutil.copytree(OUT, copy)
    assert gen.run(out_dir=copy, mode="write", log=lambda *_: None) == 0
    for path in sorted(OUT.rglob("*")):
        if path.is_dir():
            continue
        twin = copy / path.relative_to(OUT)
        if path.name.endswith("_NUR_VORSCHAU.png"):
            with Image.open(path) as committed, Image.open(twin) as generated:
                assert committed.convert("RGB").tobytes() == generated.convert("RGB").tobytes(), (
                    path.name
                )
        else:
            assert twin.read_bytes() == path.read_bytes(), path.name


@pytest.mark.parametrize("mutation", ["origin", "position", "gloss"])
def test_native_project_rejects_corrupted_geometry_and_roles(tmp_path: Path, mutation: str) -> None:
    layout = gen.layouts()[3]
    projects = gen.load_projects(OUT / gen.PROJECTS_FILENAME)
    binding = projects.bindings[4]
    hashes = gen.fixture_hashes(gen.load_json(gen.FIXTURES / gen.FIXTURES_MANIFEST_FILENAME))
    changed = tmp_path / "changed.empf"
    with (
        zipfile.ZipFile(gen.ROOT / binding.project) as source,
        zipfile.ZipFile(changed, "w") as output,
    ):
        for name in source.namelist():
            data = source.read(name)
            if name.startswith("Asset/project_file/canvas_"):
                document = json.loads(data)
                if mutation == "origin":
                    document["objects"][0]["originY"] = "left"
                elif mutation == "position":
                    document["objects"][0]["top"] += 10
                else:
                    document["objects"][2]["subPrintModel"] = 0
                data = json.dumps(document).encode()
            output.writestr(name, data)
    with pytest.raises(ValueError, match="Ursprung|Geometrie|Gloss"):
        gen.verify_native_project(changed, layout, binding, hashes)


@pytest.mark.parametrize(
    ("number", "index", "changes", "message"),
    [
        pytest.param(4, 3, {"cropX": 0}, "Crop", id="crop-wrong-half"),
        pytest.param(4, 3, {"cropY": 1}, "Crop", id="crop-y-offset"),
        pytest.param(4, 3, {"cropX": float("nan")}, "Crop", id="crop-nan"),
        pytest.param(4, 3, {"cropX": None}, "Crop", id="crop-null"),
        pytest.param(4, 1, {"cropX": 1}, "Crop", id="unexpected-height-crop"),
        pytest.param(10, 0, {"cropY": 1}, "Crop", id="unexpected-carrier-crop"),
        pytest.param(10, 1, {"subPrintModel": 2}, "COLOR-Rolle", id="color-as-gloss"),
        pytest.param(4, 1, {"subPrintModel": 2}, "HEIGHT-Rolle", id="height-as-gloss"),
        pytest.param(4, 1, {"subPrintModel": 0}, "HEIGHT-Rolle", id="height-as-color"),
        pytest.param(10, 0, {"subPrintModel": 2}, "COLOR-Rolle", id="carrier-as-gloss"),
        pytest.param(10, 1, {"_isCustomizeTexture": True}, "COLOR-Rolle", id="color-texture"),
        pytest.param(4, 1, {"_isCustomizeTexture": False}, "HEIGHT-Rolle", id="height-flat"),
        pytest.param(4, 2, {"varnishLayerNum": 2}, "Gloss-Passzahl", id="gloss-two-passes"),
        pytest.param(4, 2, {"varnishLayerNum": 0}, "Gloss-Passzahl", id="gloss-zero-passes"),
        pytest.param(4, 2, {"varnishLayerNum": None}, "Gloss-Passzahl", id="gloss-null-passes"),
        pytest.param(4, 2, {"varnishLayerNum": True}, "Gloss-Passzahl", id="gloss-bool-passes"),
        pytest.param(4, 1, {"visible": False}, "Sichtbarkeit", id="hidden-height"),
        pytest.param(4, 2, {"visible": False}, "Sichtbarkeit", id="hidden-gloss"),
        pytest.param(10, 0, {"visible": False}, "Sichtbarkeit", id="hidden-carrier"),
        pytest.param(10, 1, {"opacity": 0}, "Deckkraft", id="transparent-color"),
        pytest.param(4, 1, {"opacity": 0}, "Deckkraft", id="transparent-height"),
        pytest.param(4, 2, {"opacity": 0.5}, "Deckkraft", id="dimmed-gloss"),
        pytest.param(4, 2, {"opacity": float("nan")}, "Deckkraft", id="nan-opacity"),
        pytest.param(4, 2, {"opacity": None}, "Deckkraft", id="null-opacity"),
    ],
)
def test_rehashed_native_rendering_drift_blocks_writes(
    tmp_path: Path, number: int, index: int, changes: dict, message: str
) -> None:
    """Auch mit nachgezogenem äußerem Hash darf ein falscher Druckinhalt nicht passieren."""
    copy = tmp_path / "eufymake_a4_prints"
    shutil.copytree(OUT, copy)
    layout = next(item for item in gen.layouts() if item.number == number)
    project_path = gen.project_path_for(layout, copy)
    with zipfile.ZipFile(project_path) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    canvas = next(name for name in entries if name.startswith("Asset/project_file/canvas_"))
    document = json.loads(entries[canvas])
    document["objects"][index].update(changes)
    entries[canvas] = json.dumps(document).encode()
    with zipfile.ZipFile(project_path, "w") as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    bindings_path = copy / gen.PROJECTS_FILENAME
    bindings = gen.load_json(bindings_path)
    binding = next(item for item in bindings["projects"] if item["number"] == number)
    binding["project_sha256"] = gen.sha256_file(project_path)
    bindings_path.write_text(json.dumps(bindings), encoding="utf-8")
    before = {
        path.relative_to(copy): gen.sha256_file(path) for path in copy.rglob("*") if path.is_file()
    }
    with pytest.raises(gen.PreparationError, match=message):
        gen.run(out_dir=copy, mode="write", log=lambda *_: None)
    after = {
        path.relative_to(copy): gen.sha256_file(path) for path in copy.rglob("*") if path.is_file()
    }
    assert after == before, "Vor dem Abbruch dürfen keine Ableitungen geschrieben werden"


def test_native_crop_extent_cannot_be_hidden_by_rescaling() -> None:
    layout = gen.layouts()[3]
    with zipfile.ZipFile(gen.project_path_for(layout, OUT)) as archive:
        canvas = next(
            name for name in archive.namelist() if name.startswith("Asset/project_file/canvas_")
        )
        native = json.loads(archive.read(canvas))["objects"][3]
    native["width"] /= 2
    native["scaleX"] *= 2  # Die angezeigte mm-Breite bleibt trotzdem gleich.
    with pytest.raises(ValueError, match="Crop"):
        gen.verify_native_rendering(native, layout.objects[2])


def test_gloss_pass_count_follows_declared_ink_mode() -> None:
    layout = gen.layouts()[3]
    with zipfile.ZipFile(gen.project_path_for(layout, OUT)) as archive:
        canvas = next(
            name for name in archive.namelist() if name.startswith("Asset/project_file/canvas_")
        )
        native = json.loads(archive.read(canvas))["objects"][2]
    two_passes = replace(layout.objects[1], ink_mode="Gloss Varnish × 2")
    with pytest.raises(ValueError, match="Gloss-Passzahl"):
        gen.verify_native_rendering(native, two_passes)
    native["varnishLayerNum"] = 2
    gen.verify_native_rendering(native, two_passes)
