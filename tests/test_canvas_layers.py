"""Mehr-Ebenen-Verhalten des Canvas (#332).

Belegt die nutzersichtbare Umstellung auf „ebenenbasiert": Das Komposit mehrerer
Ebenen wird korrekt gerendert, Werkzeuge verändern nur die **aktive** Ebene, und
Undo/Redo sowie „Original wiederherstellen" funktionieren end-to-end über den
Canvas. Größenändernde Geometrie (Drehen/Zuschnitt) wirkt – invariantenwahrend –
einheitlich auf alle Ebenen.
"""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image
from PyQt6.QtGui import QColor

from bgremover import ImageCanvas
from bgremover.project_model import LayerKind, LayerRole, Project


def _solid(w: int, h: int, color: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", (w, h), color)


def _two_layer_project(w: int = 8, h: int = 8) -> Project:
    """Unten opakes Rot, oben (aktiv) Grün; B ist als zuletzt erzeugte Ebene aktiv."""
    project = Project(w, h)
    project.create_layer(_solid(w, h, (200, 0, 0, 255)), name="A", kind=LayerKind.COLOR)
    project.create_layer(_solid(w, h, (0, 200, 0, 255)), name="B", kind=LayerKind.COLOR)
    return project


def test_composite_blends_visible_layers(qapp) -> None:
    """Mit ≥2 Ebenen wird das korrekte Komposit angezeigt (oben über unten)."""
    canvas = ImageCanvas()
    project = Project(8, 8)
    project.create_layer(_solid(8, 8, (200, 0, 0, 255)), name="A", kind=LayerKind.COLOR)
    # Obere Ebene: linke Hälfte opak grün, rechte Hälfte transparent.
    top = np.zeros((8, 8, 4), dtype=np.uint8)
    top[:, :4] = (0, 200, 0, 255)
    project.create_layer(Image.fromarray(top, "RGBA"), name="B", kind=LayerKind.COLOR)
    canvas.set_project(project)

    composite = canvas._render_image()
    assert composite is not None
    arr = np.array(composite)
    assert tuple(arr[0, 0]) == (0, 200, 0, 255)   # links: obere Ebene
    assert tuple(arr[0, 7]) == (200, 0, 0, 255)   # rechts: untere Ebene scheint durch


def test_hidden_layer_is_excluded_from_composite(qapp) -> None:
    canvas = ImageCanvas()
    project = _two_layer_project()
    project.set_visible(project.layers[1].id, False)   # obere (grüne) Ebene aus
    canvas.set_project(project)

    arr = np.array(canvas._render_image())
    assert tuple(arr[0, 0]) == (200, 0, 0, 255)        # nur noch Rot sichtbar


def test_tool_modifies_only_active_layer(qapp) -> None:
    """Werkzeuge wirken ausschließlich auf die aktive Ebene."""
    canvas = ImageCanvas()
    project = _two_layer_project()
    canvas.set_project(project)
    bottom_id, top_id = project.layers[0].id, project.layers[1].id
    bottom_before = np.array(project.layer_by_id(bottom_id).image).copy()

    canvas.invert_selection()                  # leere Maske invertiert ⇒ alles
    canvas.apply_replace(QColor(0, 0, 255))

    top_after = np.array(canvas.project.layer_by_id(top_id).image)
    assert np.all(top_after[:, :, 2] == 255)   # aktive (obere) Ebene jetzt blau
    assert np.all(top_after[:, :, 3] == 255)
    bottom_after = np.array(canvas.project.layer_by_id(bottom_id).image)
    assert np.array_equal(bottom_after, bottom_before)   # untere Ebene unverändert


def test_undo_redo_end_to_end_with_layers(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_two_layer_project())
    before = np.array(canvas.image).copy()     # aktive (obere) Ebene

    canvas.invert_selection()
    canvas.apply_replace(QColor(0, 0, 255))
    after = np.array(canvas.image).copy()
    assert not np.array_equal(before, after)

    canvas.undo()
    assert np.array_equal(np.array(canvas.image), before)
    assert len(canvas.project.layers) == 2     # Struktur erhalten

    canvas.redo()
    assert np.array_equal(np.array(canvas.image), after)


def test_restore_original_with_layers(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_two_layer_project())
    top_before = np.array(canvas.image).copy()

    canvas.invert_selection()
    canvas.apply_replace(QColor(0, 0, 255))
    canvas.restore_original()

    assert np.array_equal(np.array(canvas.image), top_before)
    assert len(canvas.project.layers) == 2


def test_rotate_transforms_all_layers(qapp) -> None:
    """Größenändernde Geometrie wirkt invariantenwahrend auf alle Ebenen."""
    canvas = ImageCanvas()
    canvas.set_project(_two_layer_project(8, 4))
    canvas.apply_rotate(90)

    assert canvas.project.size == (4, 8)
    for layer in canvas.project.layers:
        assert layer.size == (4, 8)

    canvas.undo()
    assert canvas.project.size == (8, 4)
    for layer in canvas.project.layers:
        assert layer.size == (8, 4)


def test_crop_transforms_all_layers(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_two_layer_project(40, 20))
    canvas.start_crop_ratio(1, 1)
    canvas.confirm_crop()

    w, h = canvas.project.size
    assert w == h
    for layer in canvas.project.layers:
        assert layer.size == (w, h)


def test_selection_mask_tracks_active_layer_size(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_two_layer_project(12, 6))
    assert canvas.selection_mask is not None
    assert canvas.selection_mask.shape == (6, 12)   # (H, W) der aktiven Ebene


def test_apply_edit_with_resized_image_resizes_single_layer_canvas(qapp) -> None:
    """``apply_edit`` mit abweichender Größe passt die Canvas (einlagig) an."""
    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (1, 2, 3, 255)), "x.png")
    canvas.apply_edit(_solid(4, 6, (9, 9, 9, 255)), desc="resize")

    assert canvas.project.size == (4, 6)
    assert canvas.image is not None and canvas.image.size == (4, 6)
    assert canvas.project.layers[0].size == (4, 6)


# ── Ebenen-Verwaltung über den Canvas (#334) ─────────────────────────────


def test_add_layer_is_active_transparent_and_undoable(qapp) -> None:
    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (200, 0, 0, 255)), "x.png")
    assert len(canvas.project.layers) == 1

    canvas.add_layer()
    assert len(canvas.project.layers) == 2
    active = canvas.project.active_layer()
    assert active is canvas.project.layers[-1]                 # neue Ebene oben & aktiv
    assert int(np.array(active.image)[:, :, 3].max()) == 0     # transparent
    # Komposit zeigt weiterhin das rote Motiv (transparente Ebene darüber).
    assert tuple(np.array(canvas._render_image())[0, 0]) == (200, 0, 0, 255)

    canvas.undo()
    assert len(canvas.project.layers) == 1


def test_delete_active_layer_and_keep_last(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_two_layer_project())
    canvas.delete_active_layer()
    assert len(canvas.project.layers) == 1

    msgs: list[str] = []
    canvas.statusMsg.connect(msgs.append)
    canvas.delete_active_layer()                                # letzte bleibt
    assert len(canvas.project.layers) == 1
    assert any("letzte" in m.lower() for m in msgs)

    canvas.undo()
    assert len(canvas.project.layers) == 2


def test_duplicate_visible_opacity_rename_role_are_undoable(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_two_layer_project())
    top_id = canvas.project.active_layer_id

    canvas.duplicate_active_layer()
    assert len(canvas.project.layers) == 3
    canvas.undo()
    assert len(canvas.project.layers) == 2

    canvas.set_layer_visible(top_id, False)
    assert canvas.project.layer_by_id(top_id).visible is False
    canvas.undo()
    assert canvas.project.layer_by_id(top_id).visible is True

    canvas.set_layer_opacity(top_id, 0.3)
    assert canvas.project.layer_by_id(top_id).opacity == pytest.approx(0.3)
    canvas.undo()
    assert canvas.project.layer_by_id(top_id).opacity == pytest.approx(1.0)

    canvas.rename_active_layer("Motiv")
    assert canvas.project.active_layer().name == "Motiv"
    canvas.undo()
    assert canvas.project.active_layer().name != "Motiv"

    canvas.set_active_layer_role(LayerRole.HEIGHT_MAP)
    assert canvas.project.active_layer().role is LayerRole.HEIGHT_MAP
    canvas.undo()
    assert canvas.project.active_layer().role is None


def test_move_and_set_active_layer(qapp) -> None:
    canvas = ImageCanvas()
    project = _two_layer_project()
    canvas.set_project(project)
    bottom_id = project.layers[0].id
    active = canvas.project.active_layer_id          # obere Ebene (Index 1)

    canvas.move_active_layer(up=False)
    assert canvas.project.index_of(active) == 0      # nach unten verschoben
    canvas.undo()
    assert canvas.project.index_of(active) == 1

    canvas.set_active_layer(bottom_id)
    assert canvas.project.active_layer_id == bottom_id
    canvas.undo()
    assert canvas.project.active_layer_id == active


def test_layers_changed_signal_reports_top_first_with_active(qapp) -> None:
    canvas = ImageCanvas()
    received: list = []
    canvas.layersChanged.connect(received.append)

    canvas.apply_loaded_image(_solid(8, 8, (1, 2, 3, 255)), "x.png")
    assert received and len(received[-1]) == 1
    assert received[-1][0].active is True

    canvas.add_layer()
    infos = received[-1]
    assert len(infos) == 2
    assert infos[0].active is True                   # oberste (neue) Ebene zuerst & aktiv


def test_save_image_exports_composite_of_layers(qapp, tmp_path) -> None:
    """Einzelbild-Export schreibt das Komposit der Ebenen (#335)."""
    from PIL import Image as PILImage

    canvas = ImageCanvas()
    project = Project(8, 8)
    project.create_layer(_solid(8, 8, (200, 0, 0, 255)), name="A", kind=LayerKind.COLOR)
    top = np.zeros((8, 8, 4), dtype=np.uint8)
    top[:, :4] = (0, 200, 0, 255)                 # linke Hälfte opak grün
    project.create_layer(PILImage.fromarray(top, "RGBA"), name="B", kind=LayerKind.COLOR)
    canvas.set_project(project)

    out = tmp_path / "export.png"
    assert canvas.save_image(str(out)) is True
    reloaded = np.array(PILImage.open(out).convert("RGBA"))
    assert tuple(reloaded[0, 0]) == (0, 200, 0, 255)     # oben (grün)
    assert tuple(reloaded[0, 7]) == (200, 0, 0, 255)     # unten scheint durch (rot)


def test_restore_original_returns_loaded_document_after_layer_edits(qapp) -> None:
    """„Original wiederherstellen" liefert das Dokument, wie es geladen wurde –
    auch nach strukturellen Ebenen-Operationen (#335)."""
    canvas = ImageCanvas()
    canvas.set_project(_two_layer_project())
    assert len(canvas.project.layers) == 2

    canvas.add_layer()
    canvas.delete_active_layer()
    canvas.set_layer_opacity(canvas.project.layers[0].id, 0.2)

    canvas.restore_original()
    project = canvas.project
    assert len(project.layers) == 2                       # Ausgangsstruktur
    assert all(layer.opacity == pytest.approx(1.0) for layer in project.layers)


def test_single_color_layer_matches_plain_image(qapp) -> None:
    """Parität: ein einzelnes COLOR-Ebenen-Projekt rendert identisch zum Bild."""
    canvas = ImageCanvas()
    # Bild mit RGB-Werten unter transparenten Pixeln – das Komposit dürfte sie
    # NICHT auf 0 ziehen (Schnellpfad gibt die Ebene direkt zurück).
    arr = np.zeros((4, 4, 4), dtype=np.uint8)
    arr[:] = (123, 45, 67, 0)          # voll transparent, aber RGB gesetzt
    arr[0, 0] = (10, 20, 30, 255)
    img = Image.fromarray(arr, "RGBA")
    canvas.apply_loaded_image(img, "x.png")

    rendered = canvas._render_image()
    assert rendered is not None
    assert np.array_equal(np.array(rendered), arr)   # bitgenau, inkl. RGB unter Alpha


# ── HEIGHT-Ebene: graustufige 2D-Visualisierung (#345) ───────────────────


def _height_layer_arr(height: int) -> np.ndarray:
    """RGBA-Array einer HEIGHT-Ebene: Höhe nur im Rotkanal (G/B bewusst 0)."""
    arr = np.zeros((8, 8, 4), dtype=np.uint8)
    arr[:, :, 0] = height          # Höhe = Rotkanal
    arr[:, :, 3] = 255
    return arr


def test_active_height_layer_renders_as_grayscale(qapp) -> None:
    """Eine aktive HEIGHT-Ebene wird graustufig dargestellt (R==G==B==Höhe)."""
    canvas = ImageCanvas()
    project = Project(8, 8)
    project.create_layer(_solid(8, 8, (200, 0, 0, 255)), name="A", kind=LayerKind.COLOR)
    project.create_layer(
        Image.fromarray(_height_layer_arr(120), "RGBA"),
        name="H", kind=LayerKind.HEIGHT)
    canvas.set_project(project)        # HEIGHT zuletzt erzeugt ⇒ aktiv

    rendered = np.array(canvas._render_image())
    assert np.all(rendered[:, :, 0] == 120)
    assert np.all(rendered[:, :, 1] == 120)   # grau: G == Höhe
    assert np.all(rendered[:, :, 2] == 120)   # grau: B == Höhe
    assert np.all(rendered[:, :, 3] == 255)


def test_color_composite_unchanged_when_color_layer_active(qapp) -> None:
    """Mit aktiver COLOR-Ebene bleibt das Komposit unberührt – HEIGHT leckt nicht."""
    canvas = ImageCanvas()
    project = Project(8, 8)
    color_id = project.create_layer(
        _solid(8, 8, (200, 0, 0, 255)), name="A", kind=LayerKind.COLOR).id
    project.create_layer(
        Image.fromarray(_height_layer_arr(120), "RGBA"),
        name="H", kind=LayerKind.HEIGHT)
    project.set_active(color_id)
    canvas.set_project(project)

    arr = np.array(canvas._render_image())
    assert tuple(arr[0, 0]) == (200, 0, 0, 255)   # nur COLOR sichtbar


def test_switching_active_layer_toggles_height_view(qapp) -> None:
    """Auswahl einer HEIGHT-Ebene schaltet in die Höhensicht und zurück."""
    canvas = ImageCanvas()
    project = Project(8, 8)
    color_id = project.create_layer(
        _solid(8, 8, (200, 0, 0, 255)), name="A", kind=LayerKind.COLOR).id
    height_id = project.create_layer(
        Image.fromarray(_height_layer_arr(90), "RGBA"),
        name="H", kind=LayerKind.HEIGHT).id
    canvas.set_project(project)

    canvas.set_active_layer(height_id)
    assert np.all(np.array(canvas._render_image())[:, :, :3] == 90)   # Höhensicht

    canvas.set_active_layer(color_id)
    assert tuple(np.array(canvas._render_image())[0, 0]) == (200, 0, 0, 255)


# ── Höhenkarte: Erzeugung & Import (#346) ─────────────────────────────────


def test_generate_height_map_creates_role_layer_and_is_undoable(qapp) -> None:
    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (200, 50, 10, 255)), "x.png")

    canvas.generate_height_map(weights=(1, 0, 0))   # Höhe = Rotkanal
    assert len(canvas.project.layers) == 2
    active = canvas.project.active_layer()
    assert active.kind is LayerKind.HEIGHT
    assert active.role is LayerRole.HEIGHT_MAP
    arr = np.array(active.image)
    assert np.all(arr[:, :, :3] == 200)            # grau = R
    assert np.all(arr[:, :, 3] == 255)
    # Anzeige wechselt in die Höhensicht (#345).
    assert np.all(np.array(canvas._render_image())[:, :, :3] == 200)

    canvas.undo()
    assert len(canvas.project.layers) == 1
    assert canvas.project.active_layer().kind is LayerKind.COLOR


def test_generate_height_map_invert_through_canvas(qapp) -> None:
    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (51, 0, 0, 255)), "x.png")
    canvas.generate_height_map(weights=(1, 0, 0), invert=True)
    assert np.all(np.array(canvas.project.active_layer().image)[:, :, 0] == 204)


def test_generate_height_map_transfers_existing_role(qapp) -> None:
    """Rolle HEIGHT_MAP ist eindeutig: eine zweite Erzeugung übernimmt sie."""
    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (120, 120, 120, 255)), "x.png")
    canvas.generate_height_map()
    first_height_id = canvas.project.active_layer_id

    canvas.set_active_layer(canvas.project.layers[0].id)   # zurück auf COLOR
    canvas.generate_height_map()
    holders = [
        layer for layer in canvas.project.layers
        if layer.role is LayerRole.HEIGHT_MAP
    ]
    assert len(holders) == 1                               # weiterhin eindeutig
    assert holders[0].id != first_height_id                # neue Ebene trägt sie


def test_import_height_map_creates_layer(qapp, tmp_path) -> None:
    from PIL import Image as PILImage

    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (0, 0, 0, 255)), "base.png")

    ramp = np.arange(64, dtype=np.uint8).reshape(8, 8)     # 0..63 Graustufen
    path = tmp_path / "height.png"
    PILImage.fromarray(ramp, "L").save(path)

    canvas.import_height_map(str(path))
    active = canvas.project.active_layer()
    assert active.kind is LayerKind.HEIGHT
    assert active.role is LayerRole.HEIGHT_MAP
    assert np.array_equal(np.array(active.image)[:, :, 0], ramp)   # Luminanz = Höhe

    canvas.undo()
    assert len(canvas.project.layers) == 1


def test_import_height_map_resizes_to_canvas(qapp, tmp_path) -> None:
    from PIL import Image as PILImage

    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (0, 0, 0, 255)), "base.png")
    PILImage.new("L", (16, 16), 100).save(tmp_path / "big.png")

    canvas.import_height_map(str(tmp_path / "big.png"))
    active = canvas.project.active_layer()
    assert active.kind is LayerKind.HEIGHT
    assert active.size == (8, 8)                           # auf Canvas skaliert


def test_import_height_map_rejects_invalid_file(qapp, tmp_path) -> None:
    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (0, 0, 0, 255)), "base.png")
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")

    msgs: list[str] = []
    canvas.statusMsg.connect(msgs.append)
    canvas.import_height_map(str(bad))
    assert len(canvas.project.layers) == 1                 # keine Ebene angelegt
    assert msgs                                            # Fehlermeldung emittiert


# ── Höhen-Editor: Aufhellen/Abdunkeln/Setzen/Invertieren (#347) ───────────


def _color_plus_height(height_value: int = 100, w: int = 8, h: int = 8) -> Project:
    """COLOR-Basis + aktive HEIGHT-Ebene mit konstanter Höhe (Höhe = Rotkanal)."""
    project = Project(w, h)
    project.create_layer(_solid(w, h, (200, 0, 0, 255)), name="C", kind=LayerKind.COLOR)
    harr = np.zeros((h, w, 4), dtype=np.uint8)
    harr[:, :, 0] = height_value
    harr[:, :, 3] = 255
    project.create_layer(Image.fromarray(harr, "RGBA"), name="H", kind=LayerKind.HEIGHT)
    return project


def test_height_lighten_only_active_and_undoable(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_color_plus_height(100))
    color_before = np.array(canvas.project.layers[0].image).copy()

    canvas.lighten_active_height(50)
    active = canvas.project.active_layer()
    assert active.kind is LayerKind.HEIGHT
    assert np.all(np.array(active.image)[:, :, :3] == 150)        # grau aufgehellt
    assert np.array_equal(np.array(canvas.project.layers[0].image), color_before)  # COLOR unberührt

    canvas.undo()
    assert np.all(np.array(canvas.project.active_layer().image)[:, :, 0] == 100)


def test_height_darken_and_set(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_color_plus_height(100))

    canvas.darken_active_height(40)
    assert np.all(np.array(canvas.project.active_layer().image)[:, :, 0] == 60)

    canvas.set_active_height(0)
    assert np.all(np.array(canvas.project.active_layer().image)[:, :, 0] == 0)


def test_height_invert_global(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_color_plus_height(0))
    canvas.invert_active_height()
    assert np.all(np.array(canvas.project.active_layer().image)[:, :, 0] == 255)


def test_height_edit_respects_selection(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_color_plus_height(0))
    mask = np.zeros((8, 8), dtype=bool)
    mask[:, :4] = True                          # linke Hälfte auswählen
    canvas._mask = mask

    canvas.invert_active_height()
    arr = np.array(canvas.project.active_layer().image)
    assert np.all(arr[:, :4, 0] == 255)         # Auswahl invertiert
    assert np.all(arr[:, 4:, 0] == 0)           # außerhalb unverändert


def test_height_tools_ignore_color_layer(qapp) -> None:
    """Höhenwerkzeuge wirken nicht auf COLOR-Ebenen (keine Regression)."""
    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (10, 20, 30, 255)), "x.png")
    before = np.array(canvas.image).copy()

    msgs: list[str] = []
    canvas.statusMsg.connect(msgs.append)
    canvas.lighten_active_height(50)
    canvas.invert_active_height()
    canvas.set_active_height(0)

    assert np.array_equal(np.array(canvas.image), before)        # COLOR unverändert
    assert len(canvas.project.layers) == 1
    assert any("höhenebene" in m.lower() for m in msgs)
