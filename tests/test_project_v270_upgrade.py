"""Öffnen eines echten 2.7.0-Projekts mit dem aktuellen Code (#685).

``tests/fixtures/project_v2_7_0.bgrproj`` wurde mit dem tatsächlichen
v2.7.0-Release-Code erzeugt (Tag ``v2.7.0``, Commit
``6f103edde7c4394e378ade7f84cad6a02828bbad``) und unverändert eingecheckt –
kein Nachbau mit aktuellem Code. Da ``PROJECT_FORMAT_VERSION`` bereits in
2.7.0 auf 2 stand (#588), darf das Laden **keine** Migration/Normalisierung
auslösen; das unterscheidet diesen Test bewusst von den v1-Fixtures in
``test_project_io.py``, die den Migrationspfad prüfen. Die 16-Bit-Höhen-
Payload wird zusätzlich gegen eine unabhängig mit aktuellem Code erzeugte
Referenz verglichen (bitgenau derselbe Algorithmus über die Versionsgrenze).
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

from bgremover.height_map import HEIGHT_MAX_16BIT, generate_from_image
from bgremover.project_io import load_project
from bgremover.project_model import LayerKind, LayerRole
from bgremover.project_schema import PROJECT_FORMAT_VERSION

FIXTURE = Path(__file__).parent / "fixtures" / "project_v2_7_0.bgrproj"


def _gradient(size: int = 16) -> Image.Image:
    """Dieselbe Quelle wie beim Bau des Fixtures (build_v270_fixture.py, #685)."""
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for x in range(size):
        for y in range(size):
            px[x, y] = (x * 16 % 256, y * 16 % 256, (x + y) * 8 % 256, 255)
    return img


def test_fixture_manifest_already_current_version() -> None:
    """Das Fixture selbst trägt bereits die aktuelle Formatversion.

    Beweist, dass ein späterer erfolgreicher Load *keine* Migration
    durchlaufen musste – die Version war schon vor dem Laden korrekt.
    """
    with zipfile.ZipFile(FIXTURE) as zf:
        manifest = json.loads(zf.read("manifest.json"))
    assert manifest["version"] == PROJECT_FORMAT_VERSION == 2


# Vom Fixture-Bau (build_v270_fixture.py, echter v2.7.0-Code) protokollierte
# Werte – hartkodiert, damit eine Regression, die IDs/Namen/Metadaten/
# Schemaversion verändert, hier auffällt statt nur bei Kind/Rolle/Flags.
_COLOR_ID = "50530890db2d4515baec0862fb89cc49"
_HEIGHT_ID = "eed93ecfb5264b278ee2e5e0782ca86a"
_EXPECTED_METADATA = {
    "physical_size_mm": [50.0, 30.0],
    "fixture_source": "v2.7.0 (echter Release-Code, #685-Nachweis)",
}


def test_open_2_7_0_project_no_unintended_migration_or_data_change() -> None:
    """Ein echtes 2.7.0-Projekt öffnet ohne Warnungen, Struktur bleibt wertgleich.

    Vergleicht **alle** persistierten Felder (IDs, Namen, Metadaten-Dict,
    Schemaversion) gegen die beim Fixture-Bau protokollierten Werte – nicht
    nur Kind/Rolle/Flags, sonst könnte ein Loader-Bug IDs neu vergeben, Namen
    verwerfen oder ``fixture_source`` stillschweigend verlieren, ohne dass
    dieser Test es bemerkt (#685-Review).
    """
    warnings: list[str] = []
    project = load_project(FIXTURE, warnings=warnings)

    assert warnings == [], f"unerwartete Normalisierung beim Laden: {warnings}"
    assert project.size == (16, 16)
    assert project.version == 1
    assert project.metadata == _EXPECTED_METADATA
    assert [layer.kind for layer in project.layers] == [LayerKind.COLOR, LayerKind.HEIGHT]

    color, height = project.layers
    assert color.id == _COLOR_ID
    assert color.name == "Farbmotiv"
    assert color.role is None
    assert color.visible and color.opacity == 1.0 and not color.locked
    assert height.id == _HEIGHT_ID
    assert height.name == "Höhenkarte"
    assert height.role is LayerRole.HEIGHT_MAP
    assert height.visible and height.opacity == 1.0 and not height.locked
    assert project.active_layer_id == color.id == _COLOR_ID

    assert project.physical_size_mm == (50.0, 30.0)


def test_open_2_7_0_project_pixels_match_current_algorithm() -> None:
    """Farbmotiv + 16-Bit-Höhe sind bitgenau, was der aktuelle Code unabhängig liefert.

    Stärkerer Nachweis als ein reiner Byte-Vergleich der Datei: das Fixture
    stammt aus v2.7.0-Code, die Referenz hier aus dem aktuellen Kandidaten –
    Übereinstimmung beweist, dass sich die Farbmotiv-/Höhenkarten-Pipeline
    über die Versionsgrenze hinweg nicht unbeabsichtigt verändert hat.
    """
    project = load_project(FIXTURE)
    color, height = project.layers

    expected_color = _gradient()
    assert np.array_equal(np.asarray(color.image), np.asarray(expected_color))

    expected_field = generate_from_image(expected_color, max_value=HEIGHT_MAX_16BIT)
    assert height.height_data is not None
    assert height.height_data.max_value == HEIGHT_MAX_16BIT == 65535
    assert np.array_equal(height.height_data.values, expected_field.values)
    assert np.array_equal(height.height_data.coverage, expected_field.coverage)
