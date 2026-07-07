"""Tests für ImageCanvas: Laden, Speichern und Undo/Redo/Restore-Logik.

Verteidigt:

- ``save_image`` mit JPEG-Pfad funktioniert auch für RGB-Bilder
  ohne Alpha-Kanal (defensives ``convert("RGBA")``).
- ``restore_original`` schiebt den aktuellen Stand in den Undo-Stack,
  statt den Verlauf zu verwerfen.
- ``load_image`` wendet EXIF-Orientierung an, damit
  Smartphone-Fotos nicht gekippt erscheinen.
- ``save_image`` schreibt TIFF mit Transparenz.
- ``redo()`` macht ein ``undo()`` rückgängig; neue Aktionen
  verwerfen den Redo-Stapel.
"""
import numpy as np
import pytest
from PIL import Image

from bgremover import ImageCanvas

# ── Speichern ──────────────────────────────────────────────────────────

def test_save_jpeg_with_rgb_input_does_not_crash(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas.apply_loaded_image(
        Image.new("RGB", (32, 24), (200, 50, 50)).convert("RGBA"), "seed.png")
    out = tmp_path / "test.jpg"
    canvas.save_image(str(out))
    assert out.exists()
    saved = Image.open(out)
    assert saved.size == (32, 24)
    assert saved.mode in ("RGB", "L")


# Hinweis: Das JPEG-Alpha-auf-Weiß-Kompositing prüft test_image_ops.py
# (test_save_image_file_composites_jpeg_alpha_on_white) auf Unit-Ebene;
# das Canvas-Wiring deckt test_save_jpeg_with_rgb_input_does_not_crash ab.

def test_save_png_keeps_alpha(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (10, 10), (0, 255, 0, 0)), "seed.png")
    out = tmp_path / "transparent.png"
    canvas.save_image(str(out))
    saved = Image.open(out)
    assert saved.mode == "RGBA"
    assert (np.array(saved)[:, :, 3] == 0).all()


def test_save_webp(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (12, 12), (50, 50, 250, 255)), "seed.png")
    out = tmp_path / "out.webp"
    canvas.save_image(str(out))
    assert out.exists()


def test_save_image_without_loaded_image_is_noop(qapp, tmp_path):
    canvas = ImageCanvas()
    # image ist None → save_image darf nicht crashen und nichts schreiben
    out = tmp_path / "should_not_exist.png"
    canvas.save_image(str(out))
    assert not out.exists()


# ── Original wiederherstellen ──────────────────────────────────────────

def test_restore_original_pushes_current_state_to_undo(qapp):
    canvas = ImageCanvas()
    history: list[list[str]] = []
    canvas.historyChanged.connect(history.append)
    canvas.apply_loaded_image(Image.new("RGBA", (20, 20), (255, 0, 0, 255)), "orig.png")
    canvas.apply_edit(Image.new("RGBA", (20, 20), (0, 255, 0, 255)), desc="edit")
    assert history[-1] == ["edit"]
    canvas.restore_original()
    assert history[-1] == ["🔄 Original wiederhergestellt", "edit"]
    assert canvas.image is not None
    assert np.array(canvas.image)[0, 0].tolist() == [255, 0, 0, 255]


def test_undo_after_restore_recovers_edited_state(qapp):
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (20, 20), (255, 0, 0, 255)), "orig.png")
    canvas.apply_edit(Image.new("RGBA", (20, 20), (0, 255, 0, 255)), desc="edit")
    canvas.restore_original()
    canvas.undo()
    assert canvas.image is not None
    assert np.array(canvas.image)[0, 0].tolist() == [0, 255, 0, 255]


def test_restore_original_without_original_is_noop(qapp):
    canvas = ImageCanvas()
    canvas.restore_original()
    assert canvas.image is None


# ── EXIF-Orientierung beim Laden ───────────────────────────────────────

@pytest.mark.parametrize(
    ("orientation", "expected"),
    [
        (2, [[2, 1, 0], [5, 4, 3]]),
        (3, [[5, 4, 3], [2, 1, 0]]),
        (4, [[3, 4, 5], [0, 1, 2]]),
        (5, [[0, 3], [1, 4], [2, 5]]),
        (6, [[3, 0], [4, 1], [5, 2]]),
        (7, [[5, 2], [4, 1], [3, 0]]),
        (8, [[2, 5], [1, 4], [0, 3]]),
    ],
)
def test_load_image_applies_all_exif_orientations(
    qapp, tmp_path, orientation, expected,
):
    """Alle EXIF-Spiegelungs- und Rotationswerte werden beim Laden normalisiert."""
    pixels = np.zeros((2, 3, 3), dtype=np.uint8)
    pixels[:, :, 0] = np.arange(6, dtype=np.uint8).reshape(2, 3)
    src = Image.fromarray(pixels, "RGB")
    exif = src.getexif()
    exif[0x0112] = orientation
    p = tmp_path / f"orientation-{orientation}.png"
    src.save(p, exif=exif)

    canvas = ImageCanvas()
    canvas.load_image(str(p))

    assert canvas.image is not None
    assert np.array(canvas.image)[:, :, 0].tolist() == expected


def test_load_image_without_exif_keeps_orientation(qapp, tmp_path):
    """Ohne EXIF-Tag bleibt die Bildgröße unverändert."""
    src = Image.new("RGB", (30, 15), (200, 100, 50))
    p = tmp_path / "plain.png"
    src.save(p)

    canvas = ImageCanvas()
    canvas.load_image(str(p))
    assert canvas.image is not None
    assert canvas.image.size == (30, 15)


def test_load_image_handles_decompression_bomb(qapp, tmp_path, monkeypatch):
    """Der synchrone ``load_image``-Pfad (Drag&Drop/öffentliche API) darf bei
    einem Bomb-Bild nicht mit einer ungefangenen ``DecompressionBombError``
    abstürzen, sondern muss es als Statusmeldung abweisen und kein Bild laden.
    """
    src = Image.new("RGB", (100, 100), (1, 2, 3))
    p = tmp_path / "bomb.png"
    src.save(p)
    # 100×100 = 10 000 px > 2×5 → Pillow wirft DecompressionBombError.
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 5)

    canvas = ImageCanvas()
    msgs: list[str] = []
    canvas.statusMsg.connect(msgs.append)

    canvas.load_image(str(p))   # darf NICHT werfen

    assert not canvas.has_image
    assert any("zu groß" in m for m in msgs)


# ── TIFF-Speichern ─────────────────────────────────────────────────────
# Hinweis: Den TIFF-Alpha-Erhalt prüft test_image_ops.py
# (test_save_image_file_preserves_tiff_alpha) auf Unit-Ebene.

def test_save_tiff_with_tiff_extension(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (8, 8), (50, 100, 200, 255)), "seed.png")
    out = tmp_path / "explicit.tiff"
    canvas.save_image(str(out))
    assert out.exists()


# ── Robustheit: save_image-Fehlerpfad ───────────────────────────────────

def test_save_image_returns_true_on_success(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (8, 8), (10, 20, 30, 255)), "seed.png")
    assert canvas.save_image(str(tmp_path / "ok.png")) is True


def test_save_image_io_error_reports_and_returns_false(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (8, 8), (10, 20, 30, 255)), "seed.png")
    msgs: list[str] = []
    canvas.statusMsg.connect(msgs.append)
    # Zielverzeichnis existiert nicht → Pillow wirft FileNotFoundError.
    out = tmp_path / "kein_ordner" / "out.png"
    result = canvas.save_image(str(out))
    assert result is False
    assert not out.exists()
    assert any("fehlgeschlagen" in m.lower() for m in msgs), msgs


def test_save_image_without_image_reports_and_returns_false(qapp, tmp_path):
    canvas = ImageCanvas()
    msgs: list[str] = []
    canvas.statusMsg.connect(msgs.append)
    out = tmp_path / "nichts.png"
    assert canvas.save_image(str(out)) is False
    assert not out.exists()
    assert any("kein bild" in m.lower() for m in msgs), msgs


# ── Physische Größe / DPI-Einbettung (#377/#378) ───────────────────────

def test_set_physical_size_mm_records_unsaved_change(qapp):
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (300, 600), (1, 2, 3, 255)), "seed.png")
    before = canvas.content_revision
    canvas.set_physical_size_mm(25.4, 50.8)
    assert canvas.project is not None
    assert canvas.project.physical_size_mm == (25.4, 50.8)
    # Reine mm-/DPI-Änderung muss als ungespeicherte Änderung zählen.
    assert canvas.content_revision != before


def test_save_embeds_project_dpi(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (300, 300), (1, 2, 3, 255)), "seed.png")
    canvas.set_physical_size_mm(25.4, 25.4)  # 300 px / 25,4 mm = 300 DPI
    out = tmp_path / "dpi.png"
    assert canvas.save_image(str(out)) is True
    dpi = Image.open(out).info.get("dpi")
    assert dpi is not None and round(dpi[0]) == 300


# ── Redo-Stack ─────────────────────────────────────────────────────────

def _seed_canvas(color):
    """Erzeugt einen Canvas mit einem definierten Startbild."""
    c = ImageCanvas()
    c.apply_loaded_image(Image.new("RGBA", (8, 8), color), "seed.png")
    return c


def test_redo_restores_state_after_undo(qapp):
    c = _seed_canvas((255, 0, 0, 255))
    c.apply_edit(Image.new("RGBA", (8, 8), (0, 255, 0, 255)), desc="grün")
    assert c.image is not None
    assert np.array(c.image)[0, 0].tolist() == [0, 255, 0, 255]
    c.undo()
    assert c.image is not None
    assert np.array(c.image)[0, 0].tolist() == [255, 0, 0, 255]
    c.redo()
    assert c.image is not None
    assert np.array(c.image)[0, 0].tolist() == [0, 255, 0, 255]


def test_new_action_clears_redo_stack(qapp):
    c = _seed_canvas((255, 0, 0, 255))
    c.apply_edit(Image.new("RGBA", (8, 8), (0, 255, 0, 255)), desc="grün")
    c.undo()
    assert c.image is not None
    assert np.array(c.image)[0, 0].tolist() == [255, 0, 0, 255]
    # Neue Aktion ⇒ Redo-Branch verworfen
    c.apply_edit(Image.new("RGBA", (8, 8), (0, 0, 255, 255)), desc="blau")
    c.redo()
    assert c.image is not None
    assert np.array(c.image)[0, 0].tolist() == [0, 0, 255, 255]


def test_redo_on_empty_stack_is_noop(qapp):
    c = _seed_canvas((100, 100, 100, 255))
    # Darf nicht crashen, image bleibt identisch
    c.redo()
    assert c.image is not None
    assert np.array(c.image)[0, 0].tolist() == [100, 100, 100, 255]


def test_load_image_clears_both_stacks(qapp, tmp_path):
    """Beim Laden eines neuen Bildes werden Undo und Redo geleert."""
    c = _seed_canvas((10, 20, 30, 255))
    c.apply_edit(Image.new("RGBA", (8, 8), (40, 50, 60, 255)), desc="x")
    c.undo()
    p = tmp_path / "fresh.png"
    Image.new("RGB", (12, 12), (200, 200, 200)).save(p)
    c.load_image(str(p))
    assert c.image is not None
    assert c.image.size == (12, 12)
    assert np.array(c.image)[0, 0].tolist() == [200, 200, 200, 255]
    c.undo()
    assert c.image is not None
    assert np.array(c.image)[0, 0].tolist() == [200, 200, 200, 255]
    c.redo()
    assert c.image is not None
    assert np.array(c.image)[0, 0].tolist() == [200, 200, 200, 255]


# ── Größe ändern / Resample (#359) ──────────────────────────────────────

def test_apply_resize_scales_project_and_is_undoable(qapp):
    c = _seed_canvas((10, 20, 30, 255))
    c.apply_resize(16, 24)
    assert c.project.size == (16, 24)
    assert c.image is not None and c.image.size == (16, 24)
    for layer in c.project.layers:
        assert layer.size == (16, 24)

    c.undo()
    assert c.project.size == (8, 8)
    assert c.image.size == (8, 8)
    c.redo()
    assert c.project.size == (16, 24)


def test_apply_resize_links_nothing_but_uses_explicit_size(qapp):
    c = _seed_canvas((0, 0, 0, 255))
    c.apply_resize(20, 5)
    assert c.project.size == (20, 5)


def test_apply_resize_rejects_oversize_via_megapixel_gate(qapp):
    from bgremover.constants import _MAX_MEGAPIXELS

    c = _seed_canvas((1, 2, 3, 255))
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    # 8000×8000 = 64 MP > 40 MP-Limit ⇒ Ablehnung, keine Allokation/Änderung.
    edge = int((_MAX_MEGAPIXELS * 1_000_000) ** 0.5) + 2000
    c.apply_resize(edge, edge)
    assert c.project.size == (8, 8)               # unverändert
    assert any("MP" in m for m in msgs)           # übersetzte Gate-Meldung


def test_apply_resize_without_image_is_noop(qapp):
    c = ImageCanvas()
    c.apply_resize(10, 10)                          # darf nicht crashen
    assert c.project is None


# ── Kantenglättung / Feather (#361) ─────────────────────────────────────

def _hard_edge_canvas(qapp):
    arr = np.zeros((10, 10, 4), dtype=np.uint8)
    arr[:, :, 0] = 120
    arr[:, :, 1] = 130
    arr[:, :, 2] = 140
    arr[:, :5, 3] = 255          # linke Hälfte opak, rechte transparent
    c = ImageCanvas()
    c.apply_loaded_image(Image.fromarray(arr, "RGBA"), "edge.png")
    return c, arr


def test_feather_active_edges_softens_and_is_undoable(qapp):
    c, arr = _hard_edge_canvas(qapp)
    rgb_before = np.array(c.image)[:, :, :3].copy()

    c.feather_active_edges(2)
    out = np.array(c.image)
    assert np.array_equal(out[:, :, :3], rgb_before)            # RGB unverändert
    assert ((out[:, :, 3] > 0) & (out[:, :, 3] < 255)).any()    # Kante geglättet

    c.undo()
    assert np.array_equal(np.array(c.image)[:, :, 3], arr[:, :, 3])  # Alpha verlustfrei zurück
    c.redo()
    assert ((np.array(c.image)[:, :, 3] > 0) & (np.array(c.image)[:, :, 3] < 255)).any()


def test_feather_radius_zero_is_noop_with_hint(qapp):
    c, arr = _hard_edge_canvas(qapp)
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)
    c.feather_active_edges(0)
    assert np.array_equal(np.array(c.image), arr)              # unverändert
    assert any("Radius" in m for m in msgs)


def test_feather_active_edges_respects_selection(qapp):
    c, arr = _hard_edge_canvas(qapp)
    mask = np.zeros((10, 10), dtype=bool)
    mask[:, :5] = True                                         # nur linke Hälfte
    c._mask = mask
    c.feather_active_edges(3)
    out = np.array(c.image)
    assert np.array_equal(out[:, 5:, 3], arr[:, 5:, 3])        # außerhalb unverändert


def test_canvas_apply_palette_updates_checkerboard(qapp):
    """Issue #478: ein Theme-Umschalten erneuert das Canvas-Schachbrett live,
    ohne Neustart der App."""
    from PyQt6.QtGui import QColor

    from bgremover.theme import DARK, LIGHT

    c = ImageCanvas()
    c.apply_palette(LIGHT)
    light_img = c.backgroundBrush().texture().toImage()
    assert light_img.pixelColor(0, 0) == QColor(LIGHT.checker_b)

    c.apply_palette(DARK)
    dark_img = c.backgroundBrush().texture().toImage()
    assert dark_img.pixelColor(0, 0) == QColor(DARK.checker_b)
    assert dark_img.pixelColor(0, 0) != light_img.pixelColor(0, 0)
