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
from bgremover.preview_mode import PreviewMode
from bgremover.project_model import LayerKind, LayerRole, Project


def _solid(w: int, h: int, color: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", (w, h), color)


def _two_layer_project(w: int = 8, h: int = 8) -> Project:
    """Unten opakes Rot, oben (aktiv) Grün; B ist als zuletzt erzeugte Ebene aktiv."""
    project = Project(w, h)
    project.create_layer(_solid(w, h, (200, 0, 0, 255)), name="A", kind=LayerKind.COLOR)
    project.create_layer(_solid(w, h, (0, 200, 0, 255)), name="B", kind=LayerKind.COLOR)
    return project


def _preview_project(w: int = 8, h: int = 8) -> Project:
    """Farbe + gerichtete Höhe + halbflächiges Gloss + Generic, alle Rollen gesetzt."""
    project = Project(w, h)
    project.create_layer(
        _solid(w, h, (100, 80, 60, 200)), name="Motiv", kind=LayerKind.COLOR
    )
    heights = np.tile(np.linspace(0, 255, w, dtype=np.uint8), (h, 1))
    height_rgba = np.zeros((h, w, 4), dtype=np.uint8)
    height_rgba[:, :, 0] = heights
    height_rgba[:, :, 3] = 255
    project.create_layer(
        Image.fromarray(height_rgba, "RGBA"),
        name="Height",
        kind=LayerKind.HEIGHT,
        role=LayerRole.HEIGHT_MAP,
    )
    gloss_rgba = np.zeros((h, w, 4), dtype=np.uint8)
    gloss_rgba[:, w // 2:, :3] = 255
    gloss_rgba[:, :, 3] = 255
    project.create_layer(
        Image.fromarray(gloss_rgba, "RGBA"),
        name="Gloss",
        kind=LayerKind.GLOSS,
        role=LayerRole.GLOSS_MASK,
    )
    project.create_layer(
        _solid(w, h, (1, 2, 3, 255)), name="Data", kind=LayerKind.GENERIC
    )
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

    # Aktive Ebene ist COLOR: eine typverträgliche Rolle (COLOR_MOTIF) ist
    # zuweisbar und undo-fähig.
    canvas.set_active_layer_role(LayerRole.COLOR_MOTIF)
    assert canvas.project.active_layer().role is LayerRole.COLOR_MOTIF
    canvas.undo()
    assert canvas.project.active_layer().role is None


def test_set_active_layer_role_rejects_incompatible_height_map(qapp) -> None:
    """HEIGHT_MAP auf einer COLOR-Ebene wird abgewiesen – ohne Modell-/Verlaufs-
    änderung, mit verständlicher Meldung (Vertrag #364)."""
    canvas = ImageCanvas()
    canvas.set_project(_two_layer_project())          # aktive Ebene ist COLOR
    msgs: list[str] = []
    canvas.statusMsg.connect(msgs.append)
    history_before = canvas._history.descriptions()

    canvas.set_active_layer_role(LayerRole.HEIGHT_MAP)

    assert canvas.project.active_layer().role is None
    assert canvas._history.descriptions() == history_before   # kein Undo-Eintrag
    assert any("höhenebene" in m.lower() for m in msgs)
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


@pytest.mark.parametrize("preview_mode", list(PreviewMode))
@pytest.mark.parametrize("active_kind", list(LayerKind))
def test_save_image_exports_color_composite_for_every_active_layer_kind(
    qapp, tmp_path, active_kind: LayerKind, preview_mode: PreviewMode,
) -> None:
    """Export bleibt in jedem Modus/Layer ausschließlich COLOR (#363/#387)."""
    from PIL import Image as PILImage

    canvas = ImageCanvas()
    project = _preview_project(4, 4)
    active_id = next(layer.id for layer in project.layers if layer.kind is active_kind)
    project.set_active(active_id)
    canvas.set_project(project)
    canvas.set_preview_mode(preview_mode)
    expected = np.array(project.composite_color())

    out = tmp_path / f"export-{active_kind.value}-{preview_mode.value}.png"
    assert canvas.save_image(str(out)) is True
    reloaded = np.array(PILImage.open(out).convert("RGBA"))

    assert np.array_equal(reloaded, expected)


@pytest.mark.parametrize("preview_mode", list(PreviewMode))
def test_save_single_color_layer_preserves_rgb_below_transparency(
    qapp, tmp_path, preview_mode: PreviewMode
) -> None:
    """Der bitgenaue Single-Layer-Schnellpfad bleibt beim PNG-Export erhalten."""
    from PIL import Image as PILImage

    arr = np.zeros((4, 4, 4), dtype=np.uint8)
    arr[:] = (123, 45, 67, 0)
    arr[0, 0] = (10, 20, 30, 255)
    canvas = ImageCanvas()
    canvas.apply_loaded_image(PILImage.fromarray(arr, "RGBA"), "x.png")
    canvas.set_preview_mode(preview_mode)

    out = tmp_path / f"single-color-{preview_mode.value}.png"
    assert canvas.save_image(str(out)) is True
    reloaded = np.array(PILImage.open(out).convert("RGBA"))

    assert np.array_equal(reloaded, arr)


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
    """Der explizite HEIGHT-Modus zeigt die Rollen-Ebene grau."""
    canvas = ImageCanvas()
    project = Project(8, 8)
    project.create_layer(_solid(8, 8, (200, 0, 0, 255)), name="A", kind=LayerKind.COLOR)
    project.create_layer(
        Image.fromarray(_height_layer_arr(120), "RGBA"),
        name="H", kind=LayerKind.HEIGHT, role=LayerRole.HEIGHT_MAP)
    canvas.set_project(project)        # HEIGHT zuletzt erzeugt ⇒ aktiv
    canvas.set_preview_mode(PreviewMode.HEIGHT)

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


@pytest.mark.parametrize("mode", list(PreviewMode))
def test_preview_mode_is_independent_of_active_layer(
    qapp, mode: PreviewMode
) -> None:
    """Aktive Editierebene beeinflusst keinen expliziten Vorschaumodus (#387)."""
    canvas = ImageCanvas()
    project = _preview_project()
    canvas.set_project(project)
    canvas.set_preview_mode(mode)
    expected = np.array(canvas._render_image())

    for layer in project.layers:
        canvas.set_active_layer(layer.id)
        assert np.array_equal(np.array(canvas._render_image()), expected)


def test_all_preview_modes_render_distinct_expected_content(qapp) -> None:
    canvas = ImageCanvas()
    project = _preview_project()
    canvas.set_project(project)
    outputs: dict[PreviewMode, np.ndarray] = {}
    for mode in PreviewMode:
        canvas.set_preview_mode(mode)
        outputs[mode] = np.array(canvas._render_image())

    color = outputs[PreviewMode.COLOR]
    assert tuple(color[0, 0]) == (100, 80, 60, 200)
    height = outputs[PreviewMode.HEIGHT]
    assert np.all(height[:, 0, :3] == 0)
    assert np.all(height[:, -1, :3] == 255)
    gloss = outputs[PreviewMode.GLOSS]
    assert np.all(gloss[:, :4, 3] == 0)
    assert np.all(gloss[:, 4:, 3] == 192)
    relief = outputs[PreviewMode.RELIEF]
    combined = outputs[PreviewMode.COMBINED]
    assert not np.array_equal(relief[:, :, :3], color[:, :, :3])
    assert not np.array_equal(combined[:, :, :3], relief[:, :, :3])
    assert np.array_equal(relief[:, :, 3], color[:, :, 3])
    assert np.array_equal(combined[:, :, 3], color[:, :, 3])


def test_preview_controls_are_live_but_do_not_dirty_document(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_preview_project())
    revision = canvas.content_revision
    received: list[tuple[PreviewMode, int, bool]] = []
    canvas.previewSettingsChanged.connect(
        lambda mode, strength, gloss: received.append((mode, strength, gloss))
    )

    canvas.set_preview_mode(PreviewMode.RELIEF)
    canvas.set_relief_strength(0)
    assert np.array_equal(
        np.array(canvas._render_image()), np.array(canvas.project.composite_color())
    )
    canvas.set_preview_mode(PreviewMode.COMBINED)
    with_gloss = np.array(canvas._render_image())
    canvas.set_gloss_visible(False)
    without_gloss = np.array(canvas._render_image())

    assert not np.array_equal(with_gloss, without_gloss)
    assert canvas.content_revision == revision
    assert received == [
        (PreviewMode.RELIEF, 70, True),
        (PreviewMode.RELIEF, 0, True),
        (PreviewMode.COMBINED, 0, True),
        (PreviewMode.COMBINED, 0, False),
    ]


def test_transient_color_preview_rerenders_for_display_settings(qapp) -> None:
    """Modus/Relief/Gloss bleiben während einer Farb-Live-Vorschau wirksam."""
    canvas = ImageCanvas()
    project = _preview_project()
    color = next(layer for layer in project.layers if layer.kind is LayerKind.COLOR)
    project.set_active(color.id)
    canvas.set_project(project)
    model_before = np.array(color.image).copy()
    export_before = np.array(project.composite_color())
    revision = canvas.content_revision

    canvas.preview_color_op(lambda image: _solid(*image.size, (180, 120, 90, 200)))
    color_preview = np.array(canvas._preview)
    canvas.set_preview_mode(PreviewMode.COMBINED)
    combined = np.array(canvas._preview)
    canvas.set_relief_strength(0)
    without_relief = np.array(canvas._preview)
    canvas.set_gloss_visible(False)
    without_gloss = np.array(canvas._preview)

    assert not np.array_equal(combined, color_preview)
    assert not np.array_equal(without_relief, combined)
    assert not np.array_equal(without_gloss, without_relief)
    assert canvas._preview_layer_override is not None
    assert np.array_equal(np.array(color.image), model_before)
    assert np.array_equal(np.array(project.composite_color()), export_before)
    assert canvas.content_revision == revision


def test_transient_height_preview_rerenders_for_display_settings(qapp) -> None:
    """HEIGHT-Live-Pixel laufen als temporärer Layer durch die Modus-Pipeline."""
    canvas = ImageCanvas()
    project = _color_plus_height(100)
    canvas.set_project(project)
    model_before = np.array(project.active_layer().image).copy()
    canvas.set_preview_mode(PreviewMode.HEIGHT)

    canvas.preview_height_op(_levels_op)
    height_preview = np.array(canvas._preview)
    canvas.set_preview_mode(PreviewMode.RELIEF)
    relief_preview = np.array(canvas._preview)
    canvas.set_relief_strength(0)
    no_relief = np.array(canvas._preview)

    assert np.all(height_preview[:, :, :3] == 128)
    assert not np.array_equal(relief_preview, height_preview)
    assert np.array_equal(no_relief, np.array(project.composite_color()))
    assert canvas._preview_layer_override is not None
    assert np.array_equal(np.array(project.active_layer().image), model_before)


def test_hidden_data_layers_are_excluded_from_all_preview_modes(qapp) -> None:
    canvas = ImageCanvas()
    project = _preview_project()
    canvas.set_project(project)
    color = np.array(project.composite_color())
    height = project.layer_by_role(LayerRole.HEIGHT_MAP)
    gloss = project.layer_by_role(LayerRole.GLOSS_MASK)
    assert height is not None and gloss is not None

    canvas.set_layer_visible(height.id, False)
    canvas.set_layer_visible(gloss.id, False)
    for mode in (
        PreviewMode.HEIGHT,
        PreviewMode.RELIEF,
        PreviewMode.GLOSS,
        PreviewMode.COMBINED,
    ):
        canvas.set_preview_mode(mode)
        assert np.array_equal(np.array(canvas._render_image()), color)

    canvas.set_layer_visible(height.id, True)
    canvas.set_preview_mode(PreviewMode.RELIEF)
    assert not np.array_equal(np.array(canvas._render_image()), color)
    canvas.set_layer_visible(gloss.id, True)
    canvas.set_preview_mode(PreviewMode.GLOSS)
    assert not np.array_equal(np.array(canvas._render_image()), color)


def _shrink_layer_image(project: Project, role: LayerRole, size: tuple[int, int]) -> None:
    """Setzt die Pixel einer Datenebene auf eine canvas-fremde Größe (anomaler Zustand).

    Simuliert den von #404 adressierten Robustheitsfall: ein Daten-Layer, dessen
    Größe nicht zur Canvas-/Basisgröße passt. Das Modell verhindert das beim
    regulären Einfügen; hier wird es bewusst nach dem Aufbau erzwungen.
    """
    layer = project.layer_by_role(role)
    assert layer is not None
    w, h = size
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = np.tile(np.linspace(0, 255, w, dtype=np.uint8), (h, 1))
    arr[:, :, 3] = 255
    layer.image = Image.fromarray(arr, "RGBA")


def test_relief_degrades_to_color_on_height_size_mismatch(qapp) -> None:
    """Eine größenfremde HEIGHT-Ebene degradiert im RELIEF-Modus auf COLOR (#404).

    Der Mismatch wird vor :meth:`set_project` erzwungen, damit kein Render je den
    gültigen Zustand cacht – getestet wird ausschließlich der Degrade-Pfad.
    """
    canvas = ImageCanvas()
    project = _preview_project()
    _shrink_layer_image(project, LayerRole.HEIGHT_MAP, (4, 4))
    canvas.set_project(project)
    canvas.set_preview_mode(PreviewMode.RELIEF)

    rendered = canvas._render_image()  # darf nicht werfen
    assert np.array_equal(np.array(rendered), np.array(project.composite_color()))


def test_combined_degrades_per_overlay_on_size_mismatch(qapp) -> None:
    """COMBINED degradiert je betroffenes Overlay einzeln statt zu werfen (#404)."""
    color = np.array(_preview_project().composite_color())

    # Referenz: reines RELIEF eines vollständig gültigen Projekts.
    ref_canvas = ImageCanvas()
    ref_canvas.set_project(_preview_project())
    ref_canvas.set_preview_mode(PreviewMode.RELIEF)
    relief_only = np.array(ref_canvas._render_image())

    # Nur das Gloss ist größenfremd: das gültige Relief bleibt erhalten, der
    # Gloss-Schritt wird übersprungen – Ergebnis identisch zum reinen RELIEF.
    gloss_bad = _preview_project()
    _shrink_layer_image(gloss_bad, LayerRole.GLOSS_MASK, (4, 4))
    gloss_canvas = ImageCanvas()
    gloss_canvas.set_project(gloss_bad)
    gloss_canvas.set_preview_mode(PreviewMode.COMBINED)
    combined = np.array(gloss_canvas._render_image())  # darf nicht werfen
    assert np.array_equal(combined, relief_only)
    assert not np.array_equal(combined, color)

    # Sind beide Daten-Layer größenfremd, fällt COMBINED ganz auf COLOR zurück.
    both = _preview_project()
    _shrink_layer_image(both, LayerRole.HEIGHT_MAP, (4, 4))
    _shrink_layer_image(both, LayerRole.GLOSS_MASK, (4, 4))
    both_canvas = ImageCanvas()
    both_canvas.set_project(both)
    both_canvas.set_preview_mode(PreviewMode.COMBINED)
    assert np.array_equal(
        np.array(both_canvas._render_image()), np.array(both.composite_color())
    )


def test_zero_relief_strength_skips_hillshade(qapp, monkeypatch) -> None:
    import bgremover.canvas as canvas_module

    calls = 0
    real_relief = canvas_module.relief_shading

    def count_relief(*args, **kwargs):
        nonlocal calls
        calls += 1
        return real_relief(*args, **kwargs)

    canvas = ImageCanvas()
    project = _preview_project()
    canvas.set_project(project)
    monkeypatch.setattr(canvas_module, "relief_shading", count_relief)
    canvas.set_relief_strength(0)
    canvas.set_preview_mode(PreviewMode.RELIEF)

    assert calls == 0
    assert np.array_equal(
        np.array(canvas._render_image()), np.array(project.composite_color())
    )

    canvas.set_relief_strength(1)
    assert calls == 1


def test_preview_cache_reuses_and_invalidates_one_render(
    qapp, monkeypatch
) -> None:
    import bgremover.canvas as canvas_module

    relief_calls = 0
    gloss_calls = 0
    real_relief = canvas_module.relief_shading
    real_gloss = canvas_module.gloss_overlay

    def count_relief(*args, **kwargs):
        nonlocal relief_calls
        relief_calls += 1
        return real_relief(*args, **kwargs)

    def count_gloss(*args, **kwargs):
        nonlocal gloss_calls
        gloss_calls += 1
        return real_gloss(*args, **kwargs)

    canvas = ImageCanvas()
    project = _preview_project()
    canvas.set_project(project)
    monkeypatch.setattr(canvas_module, "relief_shading", count_relief)
    monkeypatch.setattr(canvas_module, "gloss_overlay", count_gloss)

    canvas.set_preview_mode(PreviewMode.COMBINED)  # rendert beim Live-Wechsel
    first = canvas._render_image()
    second = canvas._render_image()
    assert first is second
    assert (relief_calls, gloss_calls) == (1, 1)

    color = next(layer for layer in project.layers if layer.kind is LayerKind.COLOR)
    canvas.set_layer_visible(color.id, False)       # Content-Revision invalidiert
    assert (relief_calls, gloss_calls) == (2, 2)


def test_preview_parameter_validation(qapp) -> None:
    canvas = ImageCanvas()
    with pytest.raises(TypeError):
        canvas.set_preview_mode("color")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        canvas.set_relief_strength(-1)
    with pytest.raises(ValueError):
        canvas.set_relief_strength(101)


def test_modes_without_height_or_gloss_fall_back_to_color(qapp) -> None:
    canvas = ImageCanvas()
    source = _solid(4, 3, (11, 22, 33, 44))
    canvas.apply_loaded_image(source, "color-only.png")
    for mode in PreviewMode:
        canvas.set_preview_mode(mode)
        assert np.array_equal(np.array(canvas._render_image()), np.array(source))


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
    # Expliziter Modus statt implizitem Wechsel über die aktive Ebene (#387).
    canvas.set_preview_mode(PreviewMode.HEIGHT)
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


# ── Höhen-Optimierung mit Live-Vorschau (#348) ────────────────────────────


def _levels_op(field):
    from bgremover.height_ops import levels
    return levels(field, 0, 200)            # Höhe 100 → 0.5*255 → 128


def test_height_op_preview_is_nondestructive(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_color_plus_height(100))
    canvas.set_preview_mode(PreviewMode.HEIGHT)

    canvas.preview_height_op(_levels_op)
    assert canvas._preview is not None
    assert np.all(np.array(canvas._preview)[:, :, 0] == 128)   # Vorschau zeigt Ergebnis
    assert np.all(np.array(canvas.project.active_layer().image)[:, :, 0] == 100)  # Modell unberührt


def test_height_op_commit_is_undoable(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_color_plus_height(100))

    canvas.preview_height_op(_levels_op)
    canvas.apply_height_op(_levels_op)
    assert canvas._preview is None
    assert canvas._preview_layer_override is None
    assert np.all(np.array(canvas.project.active_layer().image)[:, :, 0] == 128)

    canvas.undo()
    assert np.all(np.array(canvas.project.active_layer().image)[:, :, 0] == 100)


def test_height_op_cancel_restores_model(qapp) -> None:
    canvas = ImageCanvas()
    canvas.set_project(_color_plus_height(100))

    canvas.preview_height_op(_levels_op)
    canvas.cancel_height_preview()
    assert canvas._preview is None
    assert canvas._preview_layer_override is None
    assert np.all(np.array(canvas.project.active_layer().image)[:, :, 0] == 100)


def test_height_preview_cleared_on_layer_switch(qapp) -> None:
    canvas = ImageCanvas()
    project = _color_plus_height(100)
    canvas.set_project(project)
    color_id = project.layers[0].id

    canvas.preview_height_op(_levels_op)
    assert canvas._preview is not None
    canvas.set_active_layer(color_id)               # Zustandswechsel verwirft Vorschau
    assert canvas._preview is None
    assert canvas._preview_layer_override is None


def test_height_op_requires_height_layer(qapp) -> None:
    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (10, 20, 30, 255)), "x.png")
    before = np.array(canvas.image).copy()

    msgs: list[str] = []
    canvas.statusMsg.connect(msgs.append)
    canvas.preview_height_op(_levels_op)
    canvas.apply_height_op(_levels_op)
    assert canvas._preview is None
    assert np.array_equal(np.array(canvas.image), before)
    assert any("höhenebene" in m.lower() for m in msgs)


def test_height_workflow_end_to_end_bgrproj_roundtrip(qapp, tmp_path) -> None:
    """Kompletter Ablauf (#349): erzeugen → malen → optimieren → invertieren →
    in ``.bgrproj`` speichern/wieder laden – verlustfrei."""
    from bgremover import height_ops
    from bgremover.project_io import load_project, save_project

    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (180, 90, 40, 255)), "x.png")

    canvas.generate_height_map()                       # erzeugen
    assert canvas.project.active_layer().kind is LayerKind.HEIGHT
    canvas.lighten_active_height(20)                   # malen (global)
    canvas.apply_height_op(lambda f: height_ops.quantize(f, 4))   # optimieren
    canvas.invert_active_height()                      # invertieren
    expected = np.array(canvas.project.active_layer().image)

    path = tmp_path / "relief.bgrproj"
    save_project(canvas.project, str(path))            # speichern
    reloaded = load_project(str(path))                 # wieder laden

    layer = reloaded.layer_by_role(LayerRole.HEIGHT_MAP)
    assert layer is not None
    assert layer.kind is LayerKind.HEIGHT
    assert np.array_equal(np.array(layer.image), expected)   # verlustfrei

    # Wiederhergestellte HEIGHT-Ebene zeigt sich graustufig (via #345).
    canvas2 = ImageCanvas()
    canvas2.set_project(reloaded)
    canvas2.set_active_layer(layer.id)
    canvas2.set_preview_mode(PreviewMode.HEIGHT)
    rendered = np.array(canvas2._render_image())
    assert np.array_equal(rendered[:, :, 0], rendered[:, :, 1])
    assert np.array_equal(rendered[:, :, 1], rendered[:, :, 2])


# ── Farbkorrektur mit Live-Vorschau (#360) ────────────────────────────────


def _brighten_op(img):
    from bgremover.color_ops import adjust_color
    return adjust_color(img, brightness=1.5)


def test_color_preview_is_nondestructive(qapp) -> None:
    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (100, 100, 100, 255)), "seed.png")
    before = np.array(canvas.image).copy()

    canvas.preview_color_op(_brighten_op)
    assert canvas._preview is not None
    assert np.all(np.array(canvas._preview)[:, :, 0] == 150)        # Vorschau zeigt Ergebnis
    assert np.array_equal(np.array(canvas.image), before)           # Modell unberührt


def test_color_commit_is_single_undoable_step(qapp) -> None:
    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (100, 100, 100, 255)), "seed.png")
    before = np.array(canvas.image).copy()

    canvas.preview_color_op(_brighten_op)
    canvas.apply_color_op(_brighten_op)
    assert canvas._preview is None
    assert canvas._preview_layer_override is None
    assert np.all(np.array(canvas.image)[:, :, 0] == 150)
    assert canvas._history.descriptions() == ["Farbkorrektur"]      # genau ein Schritt

    canvas.undo()
    assert np.array_equal(np.array(canvas.image), before)
    canvas.redo()
    assert np.all(np.array(canvas.image)[:, :, 0] == 150)


def test_color_cancel_restores_model(qapp) -> None:
    canvas = ImageCanvas()
    canvas.apply_loaded_image(_solid(8, 8, (100, 100, 100, 255)), "seed.png")
    before = np.array(canvas.image).copy()

    canvas.preview_color_op(_brighten_op)
    canvas.cancel_color_preview()
    assert canvas._preview is None
    assert canvas._preview_layer_override is None
    assert np.array_equal(np.array(canvas.image), before)


def test_color_preview_cleared_on_layer_switch(qapp) -> None:
    canvas = ImageCanvas()
    project = _color_plus_height(100)        # COLOR unten (Index 0), HEIGHT aktiv oben
    canvas.set_project(project)
    canvas.set_active_layer(project.layers[0].id)   # COLOR aktiv
    canvas.preview_color_op(_brighten_op)
    assert canvas._preview is not None
    canvas.set_active_layer(project.layers[1].id)   # Zustandswechsel verwirft Vorschau
    assert canvas._preview is None
    assert canvas._preview_layer_override is None


def test_color_tools_ignore_non_color_layer(qapp) -> None:
    """Farbkorrektur wirkt nicht auf HEIGHT-Ebenen (keine Regression)."""
    canvas = ImageCanvas()
    canvas.set_project(_color_plus_height(100))      # HEIGHT-Ebene ist aktiv
    before = np.array(canvas.project.active_layer().image).copy()

    msgs: list[str] = []
    canvas.statusMsg.connect(msgs.append)
    canvas.preview_color_op(_brighten_op)
    assert canvas._preview is None                   # Vorschau still übersprungen
    canvas.apply_color_op(_brighten_op)
    assert np.array_equal(np.array(canvas.project.active_layer().image), before)
    assert any("farbebene" in m.lower() for m in msgs)
