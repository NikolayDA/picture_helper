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
    """Der Container enthält genau das Manifest plus eine PNG je Ebene."""
    project = _sample_project()
    path = tmp_path / f"layout{PROJECT_SUFFIX}"
    save_project(project, path)

    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
    assert MANIFEST_NAME in names
    assert names == {MANIFEST_NAME, "layer_0000.png", "layer_0001.png", "layer_0002.png"}


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
