"""Pure-Domänenmodell-Tests (Qt-frei) für ``bgremover.project_model``."""

import numpy as np
import pytest
from PIL import Image

from bgremover.project_model import (
    PROJECT_VERSION,
    Layer,
    LayerKind,
    LayerNotFoundError,
    LayerRole,
    Project,
    ProjectModelError,
)


def _solid(size: tuple[int, int], color: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", size, color)


# ── Layer-Grundlagen ────────────────────────────────────────────────────

def test_layer_gets_unique_id_and_defaults() -> None:
    a = Layer(name="a", kind=LayerKind.COLOR, image=_solid((2, 2), (0, 0, 0, 0)))
    b = Layer(name="b", kind=LayerKind.COLOR, image=_solid((2, 2), (0, 0, 0, 0)))
    assert a.id != b.id
    assert a.visible is True and a.opacity == 1.0 and a.locked is False
    assert a.role is None
    assert a.size == (2, 2)


def test_layer_normalizes_non_rgba_image_to_rgba() -> None:
    rgb = Image.new("RGB", (3, 3), (10, 20, 30))
    layer = Layer(name="x", kind=LayerKind.COLOR, image=rgb)
    assert layer.image.mode == "RGBA"


def test_layer_accepts_numpy_rgba_array() -> None:
    arr = np.zeros((4, 5, 4), dtype=np.uint8)
    arr[..., 0] = 200
    arr[..., 3] = 255
    layer = Layer(name="np", kind=LayerKind.COLOR, image=arr)
    assert layer.image.mode == "RGBA"
    assert layer.size == (5, 4)
    assert layer.image.getpixel((0, 0)) == (200, 0, 0, 255)


def test_layer_copies_rgba_input_so_external_mutation_is_isolated() -> None:
    # Bereits-RGBA-Eingaben müssen kopiert werden: eine spätere In-place-Änderung
    # am übergebenen Bild darf die Ebene (und damit das Komposit) nicht erreichen.
    src = Image.new("RGBA", (2, 2), (10, 20, 30, 255))
    layer = Layer(name="x", kind=LayerKind.COLOR, image=src)
    src.putpixel((0, 0), (1, 1, 1, 1))
    assert layer.image.getpixel((0, 0)) == (10, 20, 30, 255)


def test_layer_rejects_out_of_range_opacity() -> None:
    with pytest.raises(ValueError):
        Layer(name="x", kind=LayerKind.COLOR, image=_solid((2, 2), (0, 0, 0, 0)), opacity=1.5)


# ── Projekt-Konstruktion & Invarianten ──────────────────────────────────

def test_new_project_is_empty_with_defaults() -> None:
    proj = Project(8, 6)
    assert proj.size == (8, 6)
    assert len(proj) == 0
    assert proj.active_layer_id is None
    assert proj.active_layer() is None
    assert proj.version == PROJECT_VERSION
    assert proj.metadata == {}


def test_project_rejects_nonpositive_size() -> None:
    with pytest.raises(ValueError):
        Project(0, 10)
    with pytest.raises(ValueError):
        Project(10, -1)


def test_project_metadata_is_isolated_copy() -> None:
    src = {"a": 1}
    proj = Project(2, 2, metadata=src)
    src["a"] = 2
    assert proj.metadata == {"a": 1}


def test_layers_view_is_immutable_tuple() -> None:
    proj = Project(2, 2)
    proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="l0")
    assert isinstance(proj.layers, tuple)
    assert len(proj.layers) == 1


def test_project_iterates_layers_bottom_to_top() -> None:
    proj = Project(2, 2)
    bottom = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="bottom")
    top = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="top")
    assert list(proj) == [bottom, top]


def test_active_layer_returns_the_active_object() -> None:
    proj = Project(2, 2)
    first = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="first")
    second = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="second")
    assert proj.active_layer() is second
    proj.set_active(first.id)
    assert proj.active_layer() is first


# ── add / active-Logik ──────────────────────────────────────────────────

def test_first_layer_becomes_active_even_without_make_active() -> None:
    proj = Project(2, 2)
    layer = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="l0", make_active=False)
    assert proj.active_layer_id == layer.id


def test_make_active_false_keeps_existing_active() -> None:
    proj = Project(2, 2)
    first = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="l0")
    proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="l1", make_active=False)
    assert proj.active_layer_id == first.id


def test_add_appends_on_top_and_index_inserts() -> None:
    proj = Project(2, 2)
    bottom = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="bottom")
    top = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="top")
    mid = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="mid", index=1)
    assert [layer.name for layer in proj.layers] == ["bottom", "mid", "top"]
    assert proj.index_of(bottom.id) == 0
    assert proj.index_of(top.id) == 2
    assert proj.index_of(mid.id) == 1


def test_add_rejects_wrong_size() -> None:
    proj = Project(4, 4)
    with pytest.raises(ValueError):
        proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="bad")


def test_add_rejects_duplicate_id() -> None:
    proj = Project(2, 2)
    layer = Layer(name="x", kind=LayerKind.COLOR, image=_solid((2, 2), (0, 0, 0, 0)))
    proj.add_layer(layer)
    twin = Layer(name="y", kind=LayerKind.COLOR, image=_solid((2, 2), (0, 0, 0, 0)), id=layer.id)
    with pytest.raises(ProjectModelError):
        proj.add_layer(twin)


def test_add_rejects_out_of_range_index() -> None:
    proj = Project(2, 2)
    proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="l0")
    with pytest.raises(IndexError):
        proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="l1", index=5)


# ── remove ──────────────────────────────────────────────────────────────

def test_remove_active_promotes_neighbor_at_same_index() -> None:
    proj = Project(2, 2)
    proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="bottom")
    middle = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="middle")
    top = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="top")
    proj.set_active(middle.id)

    proj.remove_layer(middle.id)
    # An Index 1 (vormals middle) liegt jetzt 'top'.
    assert proj.active_layer_id == top.id


def test_remove_active_top_falls_back_to_new_top() -> None:
    proj = Project(2, 2)
    bottom = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="bottom")
    top = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="top")
    proj.set_active(top.id)

    proj.remove_layer(top.id)
    assert proj.active_layer_id == bottom.id


def test_remove_last_layer_clears_active() -> None:
    proj = Project(2, 2)
    only = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="only")
    removed = proj.remove_layer(only.id)
    assert removed is only
    assert proj.active_layer_id is None
    assert len(proj) == 0


def test_remove_inactive_keeps_active() -> None:
    proj = Project(2, 2)
    keep = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="keep")
    drop = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="drop", make_active=False)
    proj.remove_layer(drop.id)
    assert proj.active_layer_id == keep.id


# ── move / reorder ──────────────────────────────────────────────────────

def test_move_layer_reorders() -> None:
    proj = Project(2, 2)
    a = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="a")
    b = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="b")
    c = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="c")
    proj.move_layer(a.id, 2)
    assert [layer.id for layer in proj.layers] == [b.id, c.id, a.id]


def test_move_layer_rejects_out_of_range() -> None:
    proj = Project(2, 2)
    a = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="a")
    with pytest.raises(IndexError):
        proj.move_layer(a.id, 3)


def test_reorder_applies_permutation() -> None:
    proj = Project(2, 2)
    a = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="a")
    b = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="b")
    proj.reorder([b.id, a.id])
    assert [layer.id for layer in proj.layers] == [b.id, a.id]


def test_reorder_requires_exact_permutation() -> None:
    proj = Project(2, 2)
    a = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="a")
    proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="b")
    with pytest.raises(ProjectModelError):
        proj.reorder([a.id])  # zu wenige IDs


# ── duplicate / rename ──────────────────────────────────────────────────

def test_duplicate_places_deep_copy_above_original() -> None:
    proj = Project(2, 2)
    src = proj.create_layer(_solid((2, 2), (10, 20, 30, 255)), name="orig")
    clone = proj.duplicate_layer(src.id)

    assert proj.index_of(clone.id) == proj.index_of(src.id) + 1
    assert clone.id != src.id
    assert proj.active_layer_id == clone.id
    assert "Kopie" in clone.name

    # Tiefe Kopie: das Original bleibt unberührt, wenn die Kopie verändert wird.
    clone.image.putpixel((0, 0), (1, 2, 3, 4))
    assert src.image.getpixel((0, 0)) == (10, 20, 30, 255)


def test_duplicate_drops_role() -> None:
    proj = Project(2, 2)
    src = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="orig", role=LayerRole.COLOR_MOTIF)
    clone = proj.duplicate_layer(src.id)
    assert clone.role is None
    assert proj.layer_by_role(LayerRole.COLOR_MOTIF) is src


def test_rename_layer() -> None:
    proj = Project(2, 2)
    layer = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="old")
    proj.rename_layer(layer.id, "neu")
    assert proj.layer_by_id(layer.id).name == "neu"


# ── Zustands-Setter ─────────────────────────────────────────────────────

def test_state_setters() -> None:
    proj = Project(2, 2)
    layer = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="l")
    proj.set_visible(layer.id, False)
    proj.set_opacity(layer.id, 0.25)
    proj.set_locked(layer.id, True)
    assert layer.visible is False
    assert layer.opacity == 0.25
    assert layer.locked is True


def test_set_opacity_validates_range() -> None:
    proj = Project(2, 2)
    layer = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="l")
    with pytest.raises(ValueError):
        proj.set_opacity(layer.id, -0.1)


# ── Rollen ──────────────────────────────────────────────────────────────

def test_assign_role_is_unique_and_transfers() -> None:
    proj = Project(2, 2)
    a = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="a")
    b = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="b")
    proj.assign_role(a.id, LayerRole.HEIGHT_MAP)
    assert proj.layer_by_role(LayerRole.HEIGHT_MAP) is a

    proj.assign_role(b.id, LayerRole.HEIGHT_MAP)
    # Rolle ist eindeutig → von a auf b übertragen.
    assert a.role is None
    assert proj.layer_by_role(LayerRole.HEIGHT_MAP) is b


def test_clear_role() -> None:
    proj = Project(2, 2)
    a = proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="a", role=LayerRole.GLOSS_MASK)
    proj.clear_role(a.id)
    assert a.role is None
    assert proj.layer_by_role(LayerRole.GLOSS_MASK) is None


def test_add_rejects_duplicate_role() -> None:
    proj = Project(2, 2)
    proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="a", role=LayerRole.COLOR_MOTIF)
    with pytest.raises(ProjectModelError):
        proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="b", role=LayerRole.COLOR_MOTIF)


# ── Fehlerfälle: unbekannte ID ──────────────────────────────────────────

@pytest.mark.parametrize(
    "op",
    [
        lambda p: p.index_of("nope"),
        lambda p: p.layer_by_id("nope"),
        lambda p: p.remove_layer("nope"),
        lambda p: p.move_layer("nope", 0),
        lambda p: p.duplicate_layer("nope"),
        lambda p: p.rename_layer("nope", "x"),
        lambda p: p.set_active("nope"),
        lambda p: p.set_visible("nope", True),
        lambda p: p.set_opacity("nope", 0.5),
        lambda p: p.set_locked("nope", True),
        lambda p: p.assign_role("nope", LayerRole.COLOR_MOTIF),
        lambda p: p.clear_role("nope"),
    ],
)
def test_unknown_layer_id_raises(op) -> None:
    proj = Project(2, 2)
    proj.create_layer(_solid((2, 2), (0, 0, 0, 0)), name="exists")
    with pytest.raises(LayerNotFoundError):
        op(proj)


# ── Komposit ────────────────────────────────────────────────────────────

def test_composite_empty_is_transparent_canvas_size() -> None:
    proj = Project(3, 4)
    out = proj.composite_color()
    assert out.mode == "RGBA"
    assert out.size == (3, 4)
    assert np.array(out)[..., 3].max() == 0


def test_composite_opaque_top_covers_bottom() -> None:
    proj = Project(2, 2)
    proj.create_layer(_solid((2, 2), (0, 0, 255, 255)), name="bottom")
    proj.create_layer(_solid((2, 2), (255, 0, 0, 255)), name="top")
    out = np.array(proj.composite_color())
    assert out[0, 0].tolist() == [255, 0, 0, 255]


def test_composite_alpha_blends_overlapping_color_layers() -> None:
    # Halbtransparentes Rot (Alpha 128) über deckendem Blau → „over"-Mischung.
    proj = Project(1, 1)
    proj.create_layer(_solid((1, 1), (0, 0, 255, 255)), name="bottom")
    proj.create_layer(_solid((1, 1), (255, 0, 0, 128)), name="top")
    r, g, b, a = np.array(proj.composite_color())[0, 0].tolist()
    assert a == 255
    assert g == 0
    assert abs(r - 128) <= 2   # 255 * 128/255
    assert abs(b - 127) <= 2   # 255 * (1 - 128/255)


def test_composite_applies_per_layer_opacity() -> None:
    proj = Project(1, 1)
    proj.create_layer(_solid((1, 1), (255, 0, 0, 255)), name="fg", opacity=0.5)
    r, g, b, a = np.array(proj.composite_color())[0, 0].tolist()
    assert (r, g, b) == (255, 0, 0)
    assert abs(a - 128) <= 1   # 255 * 0.5


def test_composite_skips_hidden_zero_opacity_and_non_color_layers() -> None:
    proj = Project(1, 1)
    proj.create_layer(_solid((1, 1), (0, 255, 0, 255)), name="hidden", visible=False)
    proj.create_layer(_solid((1, 1), (0, 255, 0, 255)), name="transparent", opacity=0.0)
    proj.create_layer(_solid((1, 1), (255, 255, 255, 255)), name="height", kind=LayerKind.HEIGHT)
    proj.create_layer(_solid((1, 1), (255, 255, 0, 255)), name="gloss", kind=LayerKind.GLOSS)
    proj.create_layer(_solid((1, 1), (0, 0, 0, 255)), name="generic", kind=LayerKind.GENERIC)
    out = np.array(proj.composite_color())[0, 0]
    assert out.tolist() == [0, 0, 0, 0]   # nichts trägt zum Farb-Komposit bei


def test_composite_respects_layer_order_after_reorder() -> None:
    proj = Project(1, 1)
    red = proj.create_layer(_solid((1, 1), (255, 0, 0, 255)), name="red")
    blue = proj.create_layer(_solid((1, 1), (0, 0, 255, 255)), name="blue")
    # blue liegt oben → deckt rot ab.
    assert np.array(proj.composite_color())[0, 0].tolist() == [0, 0, 255, 255]
    proj.reorder([blue.id, red.id])  # rot nach oben
    assert np.array(proj.composite_color())[0, 0].tolist() == [255, 0, 0, 255]


# ── Größe ändern / Resample (#359) ──────────────────────────────────────

def test_resize_scales_all_layers_and_canvas_keeping_composite_aligned() -> None:
    proj = Project(8, 4)
    proj.create_layer(_solid((8, 4), (200, 0, 0, 255)), name="C", kind=LayerKind.COLOR)
    harr = np.zeros((4, 8, 4), dtype=np.uint8)
    harr[:, :, 0] = 100
    harr[:, :, 3] = 255
    proj.create_layer(Image.fromarray(harr, "RGBA"), name="H", kind=LayerKind.HEIGHT)

    proj.resize(16, 8)

    assert proj.size == (16, 8)
    for layer in proj.layers:
        assert layer.size == (16, 8)
    # Farb-Komposit bleibt deckungsgleich (neue Größe, Vollton erhalten).
    composite = np.array(proj.composite_color())
    assert composite.shape == (8, 16, 4)
    assert composite[0, 0].tolist() == [200, 0, 0, 255]


def test_resize_keeps_height_layer_grayscale() -> None:
    proj = Project(4, 4)
    harr = np.zeros((4, 4, 4), dtype=np.uint8)
    harr[:, :2, 0] = 200   # links hoch, rechts 0 → Resampling erzeugt Verläufe
    harr[:, :, 3] = 255
    proj.create_layer(Image.fromarray(harr, "RGBA"), name="H", kind=LayerKind.HEIGHT)

    proj.resize(16, 16)

    arr = np.array(proj.active_layer().image)
    assert np.array_equal(arr[:, :, 0], arr[:, :, 1])   # R==G==B==Höhe bleibt
    assert np.array_equal(arr[:, :, 1], arr[:, :, 2])


def test_resize_same_size_is_noop_and_keeps_objects() -> None:
    proj = Project(10, 10)
    proj.create_layer(_solid((10, 10), (1, 2, 3, 255)), name="C")
    before = proj.layers[0].image
    proj.resize(10, 10)
    assert proj.size == (10, 10)
    assert proj.layers[0].image is before   # echtes No-op ohne Resampling


def test_resize_rejects_nonpositive() -> None:
    proj = Project(4, 4)
    proj.create_layer(_solid((4, 4), (0, 0, 0, 255)), name="C")
    with pytest.raises(ValueError):
        proj.resize(0, 4)
    with pytest.raises(ValueError):
        proj.resize(4, -2)
