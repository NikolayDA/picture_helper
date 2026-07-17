"""Tests für den ``.bgrproj``-Round-Trip (Qt-frei, ``project_io``/``project_schema``).

Geprüft werden der verlustfreie Round-Trip (Pixel + Metadaten + Rollen), die
defensive Abweisung beschädigter/zu großer/zip-slip-behafteter Dateien sowie das
versionierte Migrationsverhalten (älter → migriert, gleich → no-op, neuer →
unangetastet + Warnung).
"""
from __future__ import annotations

import io
import json
import logging
import zipfile

import numpy as np
import pytest
from PIL import Image

from bgremover.project_io import (
    PROJECT_SUFFIX,
    load_project,
    save_project,
)
from bgremover.project_model import LayerKind, LayerRole, Project
from bgremover.project_schema import (
    MANIFEST_NAME,
    PROJECT_FORMAT_VERSION,
    ProjectFileError,
    build_manifest,
    migrate_manifest,
)

# ── Helfer ──────────────────────────────────────────────────────────────


def _solid(w: int, h: int, color: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", (w, h), color)


def _sample_project() -> Project:
    """Projekt mit mehreren Ebenen, versch. Sichtbarkeit/Opazität/Rollen/Metadaten."""
    project = Project(6, 4, metadata={"export": {"dpi": 300}, "note": "hello"})
    project.create_layer(
        _solid(6, 4, (200, 10, 10, 255)),
        name="Motiv",
        kind=LayerKind.COLOR,
        role=LayerRole.COLOR_MOTIF,
    )
    project.create_layer(
        _solid(6, 4, (0, 120, 0, 128)),
        name="Höhe",
        kind=LayerKind.HEIGHT,
        role=LayerRole.HEIGHT_MAP,
        visible=False,
        opacity=0.5,
        locked=True,
    )
    project.create_layer(
        _solid(6, 4, (0, 0, 255, 255)),
        name="Glanz",
        kind=LayerKind.GLOSS,
    )
    project.set_active(project.layers[1].id)
    return project


def _assert_projects_equal(a: Project, b: Project) -> None:
    assert a.size == b.size
    assert a.version == b.version
    assert a.metadata == b.metadata
    assert a.active_layer_id == b.active_layer_id
    assert len(a) == len(b)
    for la, lb in zip(a.layers, b.layers, strict=True):
        assert la.id == lb.id
        assert la.name == lb.name
        assert la.kind == lb.kind
        assert la.visible == lb.visible
        assert la.opacity == pytest.approx(lb.opacity)
        assert la.locked == lb.locked
        assert la.role == lb.role
        assert np.array_equal(np.asarray(la.image), np.asarray(lb.image))
        # 16-Bit-Payload (v2, #588): bitgenau inklusive Deckung und max_value.
        if la.height_data is None:
            assert lb.height_data is None
        else:
            assert lb.height_data is not None
            assert lb.height_data.max_value == la.height_data.max_value
            assert np.array_equal(la.height_data.values, lb.height_data.values)
            assert np.array_equal(la.height_data.coverage, lb.height_data.coverage)


def _write_zip(path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name, data)


def _png_bytes(img: Image.Image) -> bytes:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


# ── Round-Trip ──────────────────────────────────────────────────────────


def test_round_trip_preserves_pixels_and_metadata(tmp_path) -> None:
    project = _sample_project()
    path = tmp_path / f"projekt{PROJECT_SUFFIX}"

    save_project(project, path)
    assert path.exists()
    loaded = load_project(path)

    _assert_projects_equal(loaded, project)


def test_round_trip_after_resize_preserves_resampled_project(tmp_path) -> None:
    """Nach ``Project.resize`` lässt sich das Projekt identisch sichern/laden (#359)."""
    project = _sample_project()
    project.resize(12, 8)
    assert project.size == (12, 8)
    path = tmp_path / f"resized{PROJECT_SUFFIX}"

    save_project(project, path)
    loaded = load_project(path)

    assert loaded.size == (12, 8)
    for layer in loaded.layers:
        assert layer.size == (12, 8)
    _assert_projects_equal(loaded, project)


def test_round_trip_preserves_physical_size_and_dpi(tmp_path) -> None:
    """Physische Größe (mm) und abgeleitete DPI überstehen Save/Load wertgleich (#376)."""
    project = Project(254, 127)
    project.create_layer(_solid(254, 127, (10, 20, 30, 255)), name="Motiv")
    project.set_physical_size_mm(50.8, 25.4)  # 2 in × 1 in → 127 dpi
    path = tmp_path / f"masse{PROJECT_SUFFIX}"

    save_project(project, path)
    loaded = load_project(path)

    # Über die normalisierenden Getter (JSON macht aus dem Tupel eine Liste).
    assert loaded.physical_size_mm == project.physical_size_mm == (50.8, 25.4)
    assert loaded.dpi == project.dpi
    assert loaded.dpi is not None
    assert loaded.dpi == pytest.approx((127.0, 127.0))


def test_round_trip_preserves_dpi_set_via_set_dpi(tmp_path) -> None:
    """Auch eine über ``set_dpi`` gesetzte Auflösung bleibt nach Save/Load erhalten (#376)."""
    project = Project(300, 600)
    project.create_layer(_solid(300, 600, (1, 2, 3, 255)), name="Motiv")
    project.set_dpi(300)
    path = tmp_path / f"dpi{PROJECT_SUFFIX}"

    save_project(project, path)
    loaded = load_project(path)

    assert loaded.physical_size_mm == project.physical_size_mm
    assert loaded.dpi == project.dpi
    assert loaded.dpi == pytest.approx((300.0, 300.0))


def test_round_trip_empty_metadata_and_single_layer(tmp_path) -> None:
    project = Project(3, 3)
    project.create_layer(_solid(3, 3, (1, 2, 3, 200)), name="Solo")
    path = tmp_path / f"solo{PROJECT_SUFFIX}"

    save_project(project, path)
    _assert_projects_equal(load_project(path), project)


def test_saved_container_layout(tmp_path) -> None:
    """Der v2-Container: Manifest + RGBA-PNG je Ebene + 16-Bit-Payload je HEIGHT."""
    project = _sample_project()
    path = tmp_path / f"layout{PROJECT_SUFFIX}"
    save_project(project, path)

    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
    assert MANIFEST_NAME in names
    # Ebene 1 ist die HEIGHT-Ebene → zusätzliche kanonische 16-Bit-Datei (#588).
    assert names == {
        MANIFEST_NAME,
        "layer_0000.png",
        "layer_0001.png",
        "layer_0001_height16.png",
        "layer_0002.png",
    }


def test_save_is_atomic_keeps_existing_file_on_failure(tmp_path, monkeypatch) -> None:
    project = _sample_project()
    path = tmp_path / f"atomic{PROJECT_SUFFIX}"
    save_project(project, path)
    original = path.read_bytes()

    # Beim erneuten Speichern mitten im Schreiben abbrechen.
    import bgremover.project_io as pio

    def boom(*_a, **_k):
        raise RuntimeError("disk full")

    monkeypatch.setattr(pio.json, "dumps", boom)
    with pytest.raises(RuntimeError):
        save_project(project, path)

    # Bestehende Datei unverändert, keine Temp-Reste im Verzeichnis.
    assert path.read_bytes() == original
    leftovers = [p.name for p in tmp_path.iterdir() if p.name != path.name]
    assert leftovers == []


# ── Defensive Abweisung ─────────────────────────────────────────────────


def test_corrupt_file_is_rejected(tmp_path) -> None:
    path = tmp_path / f"broken{PROJECT_SUFFIX}"
    path.write_bytes(b"this is not a zip file")
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_missing_manifest_is_rejected(tmp_path) -> None:
    path = tmp_path / f"nomani{PROJECT_SUFFIX}"
    _write_zip(path, {"layer_0000.png": _png_bytes(_solid(3, 3, (0, 0, 0, 255)))})
    with pytest.raises(ProjectFileError, match="manifest"):
        load_project(path)


def test_zip_slip_member_is_rejected(tmp_path) -> None:
    project = Project(3, 3)
    project.create_layer(_solid(3, 3, (5, 5, 5, 255)), name="L")
    manifest = build_manifest(project)
    path = tmp_path / f"slip{PROJECT_SUFFIX}"
    # Bösartiger Eintrag mit Pfad-Traversal neben dem gültigen Inhalt.
    _write_zip(
        path,
        {
            MANIFEST_NAME: json.dumps(manifest).encode("utf-8"),
            "layer_0000.png": _png_bytes(_solid(3, 3, (5, 5, 5, 255))),
            "../evil.png": b"payload",
        },
    )
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_unexpected_member_is_rejected(tmp_path) -> None:
    project = Project(3, 3)
    project.create_layer(_solid(3, 3, (5, 5, 5, 255)), name="L")
    manifest = build_manifest(project)
    path = tmp_path / f"extra{PROJECT_SUFFIX}"
    _write_zip(
        path,
        {
            MANIFEST_NAME: json.dumps(manifest).encode("utf-8"),
            "layer_0000.png": _png_bytes(_solid(3, 3, (5, 5, 5, 255))),
            "stowaway.txt": b"surprise",
        },
    )
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_layer_size_mismatch_is_rejected(tmp_path) -> None:
    project = Project(4, 4)
    project.create_layer(_solid(4, 4, (9, 9, 9, 255)), name="L")
    manifest = build_manifest(project)
    path = tmp_path / f"mismatch{PROJECT_SUFFIX}"
    # Ebenen-PNG in falscher Größe.
    _write_zip(
        path,
        {
            MANIFEST_NAME: json.dumps(manifest).encode("utf-8"),
            "layer_0000.png": _png_bytes(_solid(2, 2, (9, 9, 9, 255))),
        },
    )
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_oversized_file_is_rejected(tmp_path, monkeypatch) -> None:
    project = Project(3, 3)
    project.create_layer(_solid(3, 3, (1, 1, 1, 255)), name="L")
    path = tmp_path / f"big{PROJECT_SUFFIX}"
    save_project(project, path)

    import bgremover.project_io as pio

    monkeypatch.setattr(pio, "_MAX_PROJECT_FILE_BYTES", 1)
    with pytest.raises(ProjectFileError, match="groß|too large|MB"):
        load_project(path)


def test_missing_layer_file_is_rejected(tmp_path) -> None:
    project = Project(3, 3)
    project.create_layer(_solid(3, 3, (1, 1, 1, 255)), name="L")
    manifest = build_manifest(project)
    path = tmp_path / f"nolayer{PROJECT_SUFFIX}"
    # Manifest referenziert layer_0000.png, das fehlt.
    _write_zip(path, {MANIFEST_NAME: json.dumps(manifest).encode("utf-8")})
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_invalid_manifest_json_is_rejected(tmp_path) -> None:
    path = tmp_path / f"badjson{PROJECT_SUFFIX}"
    _write_zip(path, {MANIFEST_NAME: b"{not valid json"})
    with pytest.raises(ProjectFileError, match="Manifest|manifest"):
        load_project(path)


# ── Versionierung / Migration ───────────────────────────────────────────


def test_same_version_manifest_is_noop() -> None:
    project = _sample_project()
    manifest = build_manifest(project)
    assert manifest["version"] == PROJECT_FORMAT_VERSION
    assert migrate_manifest(dict(manifest)) == manifest


def test_older_version_manifest_is_migrated() -> None:
    project = Project(3, 3)
    project.create_layer(_solid(3, 3, (1, 1, 1, 255)), name="L")
    manifest = build_manifest(project)
    manifest["version"] = 0  # ältere (Vor-)Version

    migrated = migrate_manifest(dict(manifest))
    assert migrated["version"] == PROJECT_FORMAT_VERSION


def test_future_version_manifest_is_left_untouched_with_warning(caplog) -> None:
    project = Project(3, 3)
    project.create_layer(_solid(3, 3, (1, 1, 1, 255)), name="L")
    manifest = build_manifest(project)
    manifest["version"] = PROJECT_FORMAT_VERSION + 5

    with caplog.at_level(logging.WARNING):
        result = migrate_manifest(dict(manifest))

    assert result["version"] == PROJECT_FORMAT_VERSION + 5  # unangetastet
    assert any("neuer" in rec.message or "newer" in rec.message.lower()
               for rec in caplog.records)


def test_future_version_file_still_loads_best_effort(tmp_path, caplog) -> None:
    """Eine Datei mit neuerer Formatversion lädt best-effort (mit Warnung)."""
    project = _sample_project()
    path = tmp_path / f"future{PROJECT_SUFFIX}"
    save_project(project, path)

    # Manifest-Version im Container künstlich anheben.
    with zipfile.ZipFile(path) as zf:
        members = {name: zf.read(name) for name in zf.namelist()}
    manifest = json.loads(members[MANIFEST_NAME])
    manifest["version"] = PROJECT_FORMAT_VERSION + 1
    members[MANIFEST_NAME] = json.dumps(manifest).encode("utf-8")
    _write_zip(path, members)

    with caplog.at_level(logging.WARNING):
        loaded = load_project(path)
    _assert_projects_equal(loaded, project)
    # Die im Docstring versprochene Best-effort-Warnung wird tatsächlich geloggt.
    assert any("neuer" in rec.message or "newer" in rec.message.lower()
               for rec in caplog.records)


def test_manifest_without_version_is_rejected() -> None:
    with pytest.raises(ProjectFileError):
        migrate_manifest({"width": 3, "height": 3, "layers": []})


def test_boolean_version_is_rejected() -> None:
    # ``bool`` ist int-Subtyp – darf nicht als gültige Version durchrutschen.
    with pytest.raises(ProjectFileError):
        migrate_manifest({"version": True, "layers": []})


def test_unsupported_old_version_without_migration_step(monkeypatch) -> None:
    import bgremover.project_schema as psc

    # Migrationsschritt für die Vorversion entfernen → klarer Fehler statt Crash.
    monkeypatch.setattr(psc, "_MIGRATIONS", {})
    with pytest.raises(ProjectFileError):
        migrate_manifest({"version": 0, "layers": []})


# ── Schema-Validierung (project_from_manifest / layer_files) ─────────────


def _valid_manifest_and_images():
    project = Project(2, 2)
    project.create_layer(_solid(2, 2, (1, 2, 3, 255)), name="L")
    images = {"layer_0000.png": _solid(2, 2, (1, 2, 3, 255))}
    return build_manifest(project), images


def test_project_from_manifest_round_trips_in_memory() -> None:
    from bgremover.project_schema import project_from_manifest

    manifest, images = _valid_manifest_and_images()
    project = project_from_manifest(manifest, images)
    assert project.size == (2, 2)
    assert len(project) == 1
    assert project.active_layer_id == project.layers[0].id


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda m: m["layers"][0].update(kind="nope"), id="bad-kind"),
        pytest.param(lambda m: m["layers"][0].update(role="nope"), id="bad-role"),
        pytest.param(lambda m: m["layers"][0].update(opacity="x"), id="bad-opacity"),
        pytest.param(lambda m: m["layers"][0].update(opacity=True), id="bool-opacity"),
        pytest.param(lambda m: m["layers"][0].pop("id"), id="missing-id"),
        pytest.param(lambda m: m["layers"][0].update(visible="yes"), id="bad-visible"),
        pytest.param(lambda m: m.update(width=0), id="zero-width"),
        pytest.param(lambda m: m.update(width="x"), id="bad-width"),
        pytest.param(lambda m: m.update(metadata=[1, 2]), id="bad-metadata"),
        pytest.param(lambda m: m.update(project_version="x"), id="bad-project-version"),
        pytest.param(lambda m: m.update(layers="x"), id="layers-not-list"),
        pytest.param(lambda m: m["layers"].__setitem__(0, "x"), id="layer-not-dict"),
        pytest.param(lambda m: m.update(active_layer_id="unknown"), id="bad-active-id"),
    ],
)
def test_project_from_manifest_rejects_invalid_fields(mutate) -> None:
    from bgremover.project_schema import project_from_manifest

    manifest, images = _valid_manifest_and_images()
    mutate(manifest)
    with pytest.raises(ProjectFileError):
        project_from_manifest(manifest, images)


def test_project_from_manifest_rejects_duplicate_roles() -> None:
    from bgremover.project_schema import project_from_manifest

    project = Project(2, 2)
    project.create_layer(_solid(2, 2, (1, 1, 1, 255)), name="A", role=LayerRole.COLOR_MOTIF)
    project.create_layer(_solid(2, 2, (2, 2, 2, 255)), name="B")
    manifest = build_manifest(project)
    # Beide Ebenen auf dieselbe Rolle setzen → add_layer lehnt die zweite ab.
    manifest["layers"][1]["role"] = LayerRole.COLOR_MOTIF.value
    images = {
        "layer_0000.png": _solid(2, 2, (1, 1, 1, 255)),
        "layer_0001.png": _solid(2, 2, (2, 2, 2, 255)),
    }
    with pytest.raises(ProjectFileError):
        project_from_manifest(manifest, images)


def test_project_from_manifest_normalizes_legacy_incompatible_role() -> None:
    """Altzustand COLOR+HEIGHT_MAP (vor #364): nur die Rolle wird verlustfrei
    entfernt, alles andere bleibt wertgleich; eine Warnung wird gesammelt."""
    from bgremover.project_schema import project_from_manifest

    project = Project(2, 2)
    project.create_layer(_solid(2, 2, (7, 8, 9, 255)), name="Legacy", kind=LayerKind.COLOR)
    manifest = build_manifest(project)
    manifest["layers"][0]["role"] = LayerRole.HEIGHT_MAP.value   # historisch inkompatibel
    images = {"layer_0000.png": _solid(2, 2, (7, 8, 9, 255))}

    warnings: list[str] = []
    restored = project_from_manifest(manifest, images, warnings=warnings)

    rebuilt = restored.layers[0]
    assert rebuilt.kind is LayerKind.COLOR          # Kind unverändert
    assert rebuilt.role is None                     # nur die Rolle wurde entfernt
    assert rebuilt.name == "Legacy"
    assert np.array_equal(
        np.asarray(rebuilt.image), np.asarray(_solid(2, 2, (7, 8, 9, 255))))
    assert len(warnings) == 1 and "Legacy" in warnings[0]


def test_load_project_normalizes_legacy_incompatible_role(tmp_path) -> None:
    """Voller Ladepfad: inkompatible Rolle wird normalisiert, Reihenfolge,
    Pixel und Metadaten bleiben erhalten, die Warnung erreicht den Sink (#364)."""
    project = Project(3, 3, metadata={"note": "keep"})
    project.create_layer(_solid(3, 3, (10, 20, 30, 255)), name="Farbe", kind=LayerKind.COLOR)
    project.create_layer(_solid(3, 3, (40, 50, 60, 255)), name="Höhe", kind=LayerKind.HEIGHT)
    manifest = build_manifest(project)
    manifest["layers"][0]["role"] = LayerRole.HEIGHT_MAP.value   # COLOR trägt HEIGHT_MAP
    # Handgebauter **v1**-Alt-Container ohne 16-Bit-Payload: HEIGHT lädt über
    # den deterministischen Legacy-Pfad (×257-Adapter, #587/#588). Eine echte
    # v2-Datei ohne Payload-Deklaration würde dagegen abgewiesen.
    manifest["version"] = 1
    for entry in manifest["layers"]:
        entry.pop("height16_file", None)
        entry.pop("height16_max_value", None)
    path = tmp_path / ("legacy" + PROJECT_SUFFIX)
    _write_zip(path, {
        MANIFEST_NAME: json.dumps(manifest).encode("utf-8"),
        "layer_0000.png": _png_bytes(_solid(3, 3, (10, 20, 30, 255))),
        "layer_0001.png": _png_bytes(_solid(3, 3, (40, 50, 60, 255))),
    })

    warnings: list[str] = []
    loaded = load_project(path, warnings=warnings)

    assert [lyr.name for lyr in loaded.layers] == ["Farbe", "Höhe"]   # Reihenfolge
    assert loaded.layers[0].role is None                             # Rolle entfernt
    assert loaded.layers[0].kind is LayerKind.COLOR                  # Kind erhalten
    assert loaded.metadata == {"note": "keep"}
    assert np.array_equal(
        np.asarray(loaded.layers[0].image),
        np.asarray(_solid(3, 3, (10, 20, 30, 255))))
    assert warnings and "Farbe" in warnings[0]


def test_load_project_keeps_valid_height_map_role(tmp_path) -> None:
    """Eine gültige HEIGHT+HEIGHT_MAP-Kombination bleibt unverändert/warnungsfrei."""
    project = Project(2, 2)
    project.create_layer(_solid(2, 2, (1, 1, 1, 255)), name="C", kind=LayerKind.COLOR)
    project.create_layer(
        _solid(2, 2, (5, 5, 5, 255)), name="H", kind=LayerKind.HEIGHT,
        role=LayerRole.HEIGHT_MAP)
    path = tmp_path / ("valid" + PROJECT_SUFFIX)
    save_project(project, path)

    warnings: list[str] = []
    loaded = load_project(path, warnings=warnings)

    assert loaded.layer_by_role(LayerRole.HEIGHT_MAP) is not None
    assert not warnings


@pytest.mark.parametrize(
    "broken",
    [
        pytest.param({"layers": "x"}, id="layers-not-list"),
        pytest.param({"layers": ["x"]}, id="entry-not-dict"),
        pytest.param({"layers": [{"name": "L"}]}, id="file-not-str"),
    ],
)
def test_layer_files_rejects_invalid_manifest(broken) -> None:
    from bgremover.project_schema import layer_files

    with pytest.raises(ProjectFileError):
        layer_files(broken)


# ── Weitere I/O-Schutzpfade ──────────────────────────────────────────────


def test_entry_too_large_is_rejected(tmp_path, monkeypatch) -> None:
    project = Project(3, 3)
    project.create_layer(_solid(3, 3, (1, 1, 1, 255)), name="L")
    path = tmp_path / f"bomb{PROJECT_SUFFIX}"
    save_project(project, path)

    import bgremover.project_io as pio

    monkeypatch.setattr(pio, "_MAX_ENTRY_UNCOMPRESSED_BYTES", 1)
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_layer_exceeding_megapixel_limit_is_rejected(tmp_path, monkeypatch) -> None:
    project = Project(3, 3)
    project.create_layer(_solid(3, 3, (1, 1, 1, 255)), name="L")
    path = tmp_path / f"mp{PROJECT_SUFFIX}"
    save_project(project, path)

    import bgremover.project_io as pio

    monkeypatch.setattr(pio, "_MAX_MEGAPIXELS", 0)
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_corrupt_layer_png_is_rejected(tmp_path) -> None:
    project = Project(2, 2)
    project.create_layer(_solid(2, 2, (1, 1, 1, 255)), name="L")
    manifest = build_manifest(project)
    path = tmp_path / f"badpng{PROJECT_SUFFIX}"
    _write_zip(
        path,
        {
            MANIFEST_NAME: json.dumps(manifest).encode("utf-8"),
            "layer_0000.png": b"not a real png",
        },
    )
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_module_is_qt_free() -> None:
    import ast
    from pathlib import Path

    import bgremover.project_io as pio
    import bgremover.project_schema as psc

    for mod in (pio, psc):
        tree = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
        assert not any(
            name.split(".")[0] in {"PyQt6", "PyQt5", "PySide6"} for name in imported
        ), mod.__name__


# ── 16-Bit-HEIGHT-Payload an der v1-Formatgrenze (#587) ──────────────────


def test_v1_height_layer_loads_with_canonical_payload(tmp_path) -> None:
    """Laden migriert die 8-Bit-HEIGHT-PNG deterministisch (×257) in die Payload."""
    from bgremover.height_map import HeightField

    project = Project(2, 2)
    arr = np.zeros((2, 2, 4), dtype=np.uint8)
    arr[:, :, :3] = 100
    arr[:, :, 3] = 128
    project.create_layer(
        Image.fromarray(arr, "RGBA"), name="Höhe", kind=LayerKind.HEIGHT)
    path = tmp_path / "height.bgrproj"
    save_project(project, path)

    loaded = load_project(path)
    layer = loaded.layers[0]
    assert layer.kind is LayerKind.HEIGHT
    assert layer.height_data is not None
    assert layer.height_data.max_value == 65535
    assert np.all(layer.height_data.values == 100 * 257)
    assert np.all(layer.height_data.coverage == 128)

    # Seit Formatversion 2 (#588) schreibt Speichern die kanonische
    # 16-Bit-Payload mit – echte Niederbits überleben den Roundtrip bitgenau.
    project.set_layer_height_data(
        layer_id=project.layers[0].id,
        field=HeightField(
            np.full((2, 2), 0x1234, dtype=np.uint16),
            np.full((2, 2), 255, dtype=np.uint8),
            max_value=65535,
        ),
    )
    save_project(project, path)
    reloaded = load_project(path).layers[0].height_data
    assert reloaded is not None
    assert np.all(reloaded.values == 0x1234)


# ── Formatversion 2: Roundtrip, Migration, Integrität (#588) ─────────────


def _height16_project(values, coverage=None, *, extra_color: bool = True) -> Project:
    """Projekt mit kanonischer 16-Bit-HEIGHT-Payload (plus optionaler COLOR-Basis)."""
    from bgremover.height_map import HeightField

    arr = np.asarray(values, dtype=np.uint16)
    h, w = arr.shape
    cov = (
        np.full(arr.shape, 255, dtype=np.uint8)
        if coverage is None
        else np.asarray(coverage, dtype=np.uint8)
    )
    project = Project(w, h)
    if extra_color:
        project.create_layer(_solid(w, h, (200, 10, 10, 255)), name="Farbe")
    project.create_layer(
        name="Höhe", kind=LayerKind.HEIGHT, role=LayerRole.HEIGHT_MAP,
        height_data=HeightField(arr, cov, max_value=65535))
    return project


def test_v2_roundtrip_restores_boundary_values_bit_exactly(tmp_path) -> None:
    """Grenzwerte des Vertrags überleben Save/Open bitgenau (inkl. Deckung)."""
    values = [[0, 1, 255, 256], [257, 32767, 65534, 65535]]
    coverage = [[0, 1, 128, 255], [254, 7, 200, 0]]
    project = _height16_project(values, coverage)
    path = tmp_path / f"v2{PROJECT_SUFFIX}"
    save_project(project, path)

    loaded = load_project(path)
    _assert_projects_equal(project, loaded)
    field = loaded.layers[1].height_data
    assert field is not None
    assert field.values.dtype == np.uint16
    assert field.values.tolist() == values
    assert field.coverage.tolist() == coverage


@pytest.mark.parametrize("seed", [0, 5, 99])
def test_v2_roundtrip_random_arrays_and_masks(tmp_path, seed: int) -> None:
    """Zufällige 16-Bit-Arrays und Deckungsmasken bestehen den Roundtrip."""
    rng = np.random.default_rng(seed)
    h, w = int(rng.integers(1, 32)), int(rng.integers(1, 32))
    values = rng.integers(0, 65536, size=(h, w), dtype=np.uint16)
    coverage = rng.integers(0, 256, size=(h, w), dtype=np.uint8)
    project = _height16_project(values, coverage)
    path = tmp_path / f"rand{seed}{PROJECT_SUFFIX}"
    save_project(project, path)
    _assert_projects_equal(project, load_project(path))


def test_v2_mixed_project_roundtrip_keeps_semantics(tmp_path) -> None:
    """COLOR + HEIGHT + GLOSS: Reihenfolge, Rollen, Metadaten, Payload erhalten."""
    from bgremover.height_map import HeightField

    project = Project(4, 3, metadata={"note": "mix"})
    project.create_layer(
        _solid(4, 3, (10, 20, 30, 255)), name="Motiv", role=LayerRole.COLOR_MOTIF)
    project.create_layer(
        name="Höhe", kind=LayerKind.HEIGHT, role=LayerRole.HEIGHT_MAP,
        visible=False, opacity=0.5, locked=True,
        height_data=HeightField(
            np.full((3, 4), 0x1234, dtype=np.uint16),
            np.full((3, 4), 200, dtype=np.uint8),
            max_value=65535,
        ))
    project.create_layer(
        _solid(4, 3, (0, 0, 255, 128)), name="Glanz", kind=LayerKind.GLOSS)
    project.set_active(project.layers[1].id)
    path = tmp_path / f"mix{PROJECT_SUFFIX}"
    save_project(project, path)

    loaded = load_project(path)
    _assert_projects_equal(project, loaded)


def test_v1_fixture_loads_and_migrates_deterministically(tmp_path) -> None:
    """Realistische v1-Datei: HEIGHT → ×257, COLOR/GLOSS/Reihenfolge unverändert."""
    manifest = {
        "version": 1,
        "project_version": 1,
        "width": 2,
        "height": 2,
        "active_layer_id": "h1",
        "metadata": {"note": "legacy"},
        "layers": [
            {"id": "c1", "name": "Farbe", "kind": "color", "visible": True,
             "opacity": 1.0, "locked": False, "role": "color_motif",
             "bit_depth": 8, "file": "layer_0000.png"},
            {"id": "h1", "name": "Höhe", "kind": "height", "visible": True,
             "opacity": 1.0, "locked": False, "role": "height_map",
             "bit_depth": 8, "file": "layer_0001.png"},
            {"id": "g1", "name": "Glanz", "kind": "gloss", "visible": False,
             "opacity": 0.5, "locked": False, "role": None,
             "bit_depth": 8, "file": "layer_0002.png"},
        ],
    }
    harr = np.zeros((2, 2, 4), dtype=np.uint8)
    harr[:, :, :3] = 100
    harr[:, :, 3] = 128
    path = tmp_path / ("v1" + PROJECT_SUFFIX)
    _write_zip(path, {
        MANIFEST_NAME: json.dumps(manifest).encode("utf-8"),
        "layer_0000.png": _png_bytes(_solid(2, 2, (10, 20, 30, 255))),
        "layer_0001.png": _png_bytes(Image.fromarray(harr, "RGBA")),
        "layer_0002.png": _png_bytes(_solid(2, 2, (9, 9, 9, 64))),
    })

    loaded = load_project(path)
    assert [lyr.name for lyr in loaded.layers] == ["Farbe", "Höhe", "Glanz"]
    assert loaded.metadata == {"note": "legacy"}
    field = loaded.layers[1].height_data
    assert field is not None
    assert field.max_value == 65535
    assert np.all(field.values == 100 * 257)          # deterministisch v8 × 257
    assert np.all(field.coverage == 128)
    # COLOR/GLOSS bleiben pixelidentisch, Sichtbarkeit/Opazität erhalten.
    assert np.array_equal(
        np.asarray(loaded.layers[0].image), np.asarray(_solid(2, 2, (10, 20, 30, 255))))
    assert loaded.layers[2].visible is False
    assert loaded.layers[2].opacity == pytest.approx(0.5)
    # Erneutes Speichern schreibt kontrolliert v2 (mit 16-Bit-Payload).
    out = tmp_path / ("resaved" + PROJECT_SUFFIX)
    save_project(loaded, out)
    with zipfile.ZipFile(out) as zf:
        manifest2 = json.loads(zf.read(MANIFEST_NAME))
        assert manifest2["version"] == PROJECT_FORMAT_VERSION
        assert "layer_0001_height16.png" in zf.namelist()
    _assert_projects_equal(loaded, load_project(out))


def test_v2_repeated_open_save_has_no_cumulative_loss(tmp_path) -> None:
    """Fünf Open/Save-Zyklen: Payload bleibt bitgenau (kein kumulativer Verlust)."""
    rng = np.random.default_rng(1234)
    values = rng.integers(0, 65536, size=(9, 7), dtype=np.uint16)
    project = _height16_project(values)
    path = tmp_path / f"cycle{PROJECT_SUFFIX}"
    save_project(project, path)
    current = load_project(path)
    for _ in range(5):
        save_project(current, path)
        current = load_project(path)
    field = current.layers[1].height_data
    assert field is not None
    assert np.array_equal(field.values, values)


def test_save_abort_during_height16_write_keeps_existing_file(
    tmp_path, monkeypatch
) -> None:
    """I/O-Abbruch beim Payload-Schreiben: Zieldatei intakt, kein Temp-Rest."""
    import bgremover.project_io as pio

    project = _height16_project([[1, 2], [3, 4]])
    path = tmp_path / f"abort{PROJECT_SUFFIX}"
    save_project(project, path)
    original = path.read_bytes()

    def boom(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr(pio, "_encode_height16_png", boom)
    with pytest.raises(OSError):
        save_project(project, path)

    assert path.read_bytes() == original                  # unversehrt
    leftovers = [p for p in tmp_path.iterdir() if p.suffix == ".tmp"]
    assert leftovers == []                                # Temp aufgeräumt


# ── v2-Integritäts- und Sicherheits-Negativtests (#588) ──────────────────


def _tamper(path, mutate) -> None:
    """Schreibt den Container mit mutierten Einträgen neu (Manipulations-Helfer)."""
    with zipfile.ZipFile(path) as zf:
        members = {name: zf.read(name) for name in zf.namelist()}
    mutate(members)
    _write_zip(path, members)


def test_truncated_height16_payload_is_rejected(tmp_path) -> None:
    project = _height16_project([[1, 2], [3, 4]])
    path = tmp_path / f"trunc{PROJECT_SUFFIX}"
    save_project(project, path)
    _tamper(path, lambda m: m.__setitem__(
        "layer_0001_height16.png", m["layer_0001_height16.png"][:-7]))
    with pytest.raises(ProjectFileError) as err:
        load_project(path)
    assert "Integritätsprüfung" in str(err.value)


def test_swapped_height16_payloads_are_rejected(tmp_path) -> None:
    """Vertauschte Payload-Dateien zweier HEIGHT-Ebenen fallen per Checksumme auf."""
    from bgremover.height_map import HeightField

    project = Project(2, 2)
    project.create_layer(
        name="H1", kind=LayerKind.HEIGHT,
        height_data=HeightField(
            np.full((2, 2), 111, dtype=np.uint16),
            np.full((2, 2), 255, dtype=np.uint8), max_value=65535))
    project.create_layer(
        name="H2", kind=LayerKind.HEIGHT,
        height_data=HeightField(
            np.full((2, 2), 222, dtype=np.uint16),
            np.full((2, 2), 255, dtype=np.uint8), max_value=65535))
    path = tmp_path / f"swap{PROJECT_SUFFIX}"
    save_project(project, path)

    def swap(members: dict) -> None:
        a, b = "layer_0000_height16.png", "layer_0001_height16.png"
        members[a], members[b] = members[b], members[a]

    _tamper(path, swap)
    with pytest.raises(ProjectFileError) as err:
        load_project(path)
    assert "Integritätsprüfung" in str(err.value)


def test_manifest_without_height16_sha_is_rejected(tmp_path) -> None:
    project = _height16_project([[1, 2], [3, 4]])
    path = tmp_path / f"nosha{PROJECT_SUFFIX}"
    save_project(project, path)

    def strip_sha(members: dict) -> None:
        manifest = json.loads(members[MANIFEST_NAME])
        manifest["layers"][1].pop("height16_sha256")
        members[MANIFEST_NAME] = json.dumps(manifest).encode("utf-8")

    _tamper(path, strip_sha)
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_wrong_height16_max_value_is_rejected(tmp_path) -> None:
    project = _height16_project([[1, 2], [3, 4]])
    path = tmp_path / f"maxv{PROJECT_SUFFIX}"
    save_project(project, path)

    def wrong_max(members: dict) -> None:
        manifest = json.loads(members[MANIFEST_NAME])
        manifest["layers"][1]["height16_max_value"] = 255
        members[MANIFEST_NAME] = json.dumps(manifest).encode("utf-8")

    _tamper(path, wrong_max)
    with pytest.raises(ProjectFileError) as err:
        load_project(path)
    assert "16-Bit-Höhendaten" in str(err.value)


def test_height16_on_non_height_layer_is_rejected(tmp_path) -> None:
    """Eine height16-Deklaration auf einer COLOR-Ebene ist inkonsistent."""
    project = _height16_project([[1, 2], [3, 4]])
    path = tmp_path / f"kind{PROJECT_SUFFIX}"
    save_project(project, path)

    def move_to_color(members: dict) -> None:
        manifest = json.loads(members[MANIFEST_NAME])
        height_entry = manifest["layers"][1]
        color_entry = manifest["layers"][0]
        for key in ("height16_file", "height16_sha256", "height16_max_value"):
            color_entry[key] = height_entry.pop(key)
        members[MANIFEST_NAME] = json.dumps(manifest).encode("utf-8")

    _tamper(path, move_to_color)
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_missing_height16_file_in_container_is_rejected(tmp_path) -> None:
    project = _height16_project([[1, 2], [3, 4]])
    path = tmp_path / f"missing{PROJECT_SUFFIX}"
    save_project(project, path)
    _tamper(path, lambda m: m.pop("layer_0001_height16.png"))
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_wrong_sized_height16_payload_is_rejected(tmp_path) -> None:
    """Payload in fremder Größe: Checksumme stimmt, Größenprüfung greift."""
    import bgremover.project_io as pio

    project = _height16_project([[1, 2], [3, 4]])
    path = tmp_path / f"size{PROJECT_SUFFIX}"
    save_project(project, path)
    tiny = pio._encode_height16_png(np.array([[7]], dtype=np.uint16))

    def shrink(members: dict) -> None:
        import hashlib

        members["layer_0001_height16.png"] = tiny
        manifest = json.loads(members[MANIFEST_NAME])
        manifest["layers"][1]["height16_sha256"] = hashlib.sha256(tiny).hexdigest()
        members[MANIFEST_NAME] = json.dumps(manifest).encode("utf-8")

    _tamper(path, shrink)
    with pytest.raises(ProjectFileError) as err:
        load_project(path)
    assert "passt nicht" in str(err.value)


def test_8bit_gray_png_as_height16_payload_is_rejected(tmp_path) -> None:
    """Eine 8-Bit-Grau-PNG ist keine gültige 16-Bit-Payload (kein stilles Spreizen)."""
    project = _height16_project([[1, 2], [3, 4]])
    path = tmp_path / f"gray8{PROJECT_SUFFIX}"
    save_project(project, path)
    fake = _png_bytes(Image.new("L", (2, 2), 100))

    def replace(members: dict) -> None:
        import hashlib

        members["layer_0001_height16.png"] = fake
        manifest = json.loads(members[MANIFEST_NAME])
        manifest["layers"][1]["height16_sha256"] = hashlib.sha256(fake).hexdigest()
        members[MANIFEST_NAME] = json.dumps(manifest).encode("utf-8")

    _tamper(path, replace)
    with pytest.raises(ProjectFileError) as err:
        load_project(path)
    assert "16-Bit-Höhendaten" in str(err.value)


def test_height16_zip_slip_name_is_rejected(tmp_path) -> None:
    """Pfadanteile im height16-Namen werden wie bisher als Zip-Slip abgewiesen."""
    project = _height16_project([[1, 2], [3, 4]])
    path = tmp_path / f"slip{PROJECT_SUFFIX}"
    save_project(project, path)

    def slip(members: dict) -> None:
        payload = members.pop("layer_0001_height16.png")
        members["../escape.png"] = payload
        manifest = json.loads(members[MANIFEST_NAME])
        manifest["layers"][1]["height16_file"] = "../escape.png"
        members[MANIFEST_NAME] = json.dumps(manifest).encode("utf-8")

    _tamper(path, slip)
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_oversized_height16_entry_is_rejected(tmp_path, monkeypatch) -> None:
    """Das eigene 2-B/px-Entry-Limit greift für height16-Einträge."""
    import bgremover.project_io as pio

    project = _height16_project([[1, 2], [3, 4]])
    path = tmp_path / f"big{PROJECT_SUFFIX}"
    save_project(project, path)
    monkeypatch.setattr(pio, "_MAX_HEIGHT16_ENTRY_BYTES", 4)
    with pytest.raises(ProjectFileError) as err:
        load_project(path)
    assert "zu groß" in str(err.value)


def test_duplicate_height16_file_names_are_rejected(tmp_path) -> None:
    """Zwei Ebenen dürfen nicht dieselbe Payload-Datei referenzieren."""
    from bgremover.height_map import HeightField

    project = Project(2, 2)
    project.create_layer(
        name="H1", kind=LayerKind.HEIGHT,
        height_data=HeightField(
            np.full((2, 2), 1, dtype=np.uint16),
            np.full((2, 2), 255, dtype=np.uint8), max_value=65535))
    project.create_layer(
        name="H2", kind=LayerKind.HEIGHT,
        height_data=HeightField(
            np.full((2, 2), 2, dtype=np.uint16),
            np.full((2, 2), 255, dtype=np.uint8), max_value=65535))
    path = tmp_path / f"dup{PROJECT_SUFFIX}"
    save_project(project, path)

    def duplicate(members: dict) -> None:
        manifest = json.loads(members[MANIFEST_NAME])
        manifest["layers"][1]["height16_file"] = (
            manifest["layers"][0]["height16_file"])
        members[MANIFEST_NAME] = json.dumps(manifest).encode("utf-8")

    _tamper(path, duplicate)
    with pytest.raises(ProjectFileError):
        load_project(path)


def test_40mp_height_project_saves_and_opens_within_budget(tmp_path) -> None:
    """40-MP-HEIGHT-Projekt: Save/Open bitgenau und innerhalb großzügiger Budgets.

    Misst den vollen v2-Zyklus am harten Megapixel-Limit (ADR #586): die
    Containergröße bleibt für glatte Höhen klein (PNG/Deflate), Laufzeit in
    einer bewusst großzügigen CI-Schranke; die Grenzwerte inklusive Niederbits
    überleben bitgenau.
    """
    import time

    width, height = 8000, 5000                          # 40,0 MP
    values = np.zeros((height, width), dtype=np.uint16)
    values[0, :8] = [0, 1, 255, 256, 32767, 65534, 65535, 0x1234]
    project = _height16_project(values, extra_color=False)
    path = tmp_path / f"mp40{PROJECT_SUFFIX}"

    start = time.perf_counter()
    save_project(project, path)
    save_seconds = time.perf_counter() - start
    size_mb = path.stat().st_size / 1_000_000

    start = time.perf_counter()
    loaded = load_project(path)
    load_seconds = time.perf_counter() - start

    field = loaded.layers[0].height_data
    assert field is not None
    assert list(field.values[0, :8]) == [0, 1, 255, 256, 32767, 65534, 65535, 0x1234]
    assert field.values.shape == (height, width)
    # Großzügige Schranken gegen strukturelle Regressionen (kein Benchmark):
    # unkomprimiert wären es 240 MB – der Container muss deutlich darunter
    # bleiben, Save+Open zusammen klar unter einer Minute.
    assert size_mb < 60.0
    assert save_seconds + load_seconds < 60.0


def test_v2_height_layer_without_payload_declaration_is_rejected(tmp_path) -> None:
    """Echte v2-Datei, HEIGHT ohne height16-Deklaration: Integritätsverstoß.

    Da die Migration v1-Manifeste in-memory auf Version 2 hebt, muss der
    Loader die **Ursprungsversion** heranziehen: nur echte v1-Dateien dürfen
    auf den ×257-Adapter zurückfallen – bei einer manipulierten/abgeschnittenen
    v2-Datei wäre der stille Rückfall ein requantisierter Datenverlust
    (Codex-Review-Befund zu #588).
    """
    project = _height16_project([[1, 2], [3, 4]])
    path = tmp_path / f"nodecl{PROJECT_SUFFIX}"
    save_project(project, path)

    def strip_declaration(members: dict) -> None:
        manifest = json.loads(members[MANIFEST_NAME])
        assert manifest["version"] == PROJECT_FORMAT_VERSION
        for key in ("height16_file", "height16_sha256", "height16_max_value"):
            manifest["layers"][1].pop(key)
        members[MANIFEST_NAME] = json.dumps(manifest).encode("utf-8")
        members.pop("layer_0001_height16.png")

    _tamper(path, strip_declaration)
    with pytest.raises(ProjectFileError):
        load_project(path)
