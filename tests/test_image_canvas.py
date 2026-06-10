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
from bgremover.canvas_history import CanvasHistory

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


# ── Undo-Stack: Speicherlimit-Eviction ─────────────────────────────────

def test_undo_stack_evicts_oldest_under_memory_limit():
    """Überschreitet der Undo-Stack das Byte-Limit, fallen älteste
    Einträge raus – aber nie der letzte (mind. 1 Schritt bleibt)."""
    one_image = 8 * 8 * 4                       # RGBA-Rohdaten eines 8×8-Bilds
    history = CanvasHistory(memory_limit=one_image)

    current = Image.new("RGBA", (8, 8), (0, 0, 0, 255))
    for i in range(6):
        history.push(current, f"edit{i}")
        current = Image.new("RGBA", (8, 8), (i, i, i, 255))

    assert history.descriptions() == ["edit5"]  # nur 1 Eintrag passt rein
    assert history.undo(current) is not None     # bleibt funktionsfähig
    assert history.undo(current) is None


def test_history_descriptions_track_push_undo_and_redo():
    """Die öffentliche Verlaufsliste folgt Push/Undo/Redo-Bewegungen."""
    history = CanvasHistory()
    first = Image.new("RGBA", (8, 8), (1, 2, 3, 255))
    second = Image.new("RGBA", (8, 8), (4, 5, 6, 255))
    current = Image.new("RGBA", (8, 8), (7, 8, 9, 255))
    history.push(first, "a")
    history.push(second, "b")
    assert history.descriptions() == ["b", "a"]
    undone = history.undo(current)
    assert undone is not None
    assert history.descriptions() == ["a"]
    redone = history.redo(undone[0])
    assert redone is not None
    assert history.descriptions() == ["b", "a"]
