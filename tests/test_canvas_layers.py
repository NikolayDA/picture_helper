"""Mehr-Ebenen-Verhalten des Canvas (#332).

Belegt die nutzersichtbare Umstellung auf „ebenenbasiert": Das Komposit mehrerer
Ebenen wird korrekt gerendert, Werkzeuge verändern nur die **aktive** Ebene, und
Undo/Redo sowie „Original wiederherstellen" funktionieren end-to-end über den
Canvas. Größenändernde Geometrie (Drehen/Zuschnitt) wirkt – invariantenwahrend –
einheitlich auf alle Ebenen.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from PyQt6.QtGui import QColor

from bgremover import ImageCanvas
from bgremover.project_model import LayerKind, Project


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
