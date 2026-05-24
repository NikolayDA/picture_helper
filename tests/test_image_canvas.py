"""Tests für ImageCanvas: Laden, Speichern und Undo/Redo/Restore-Logik.

Verteidigt:

* Fix #7 — ``save_image`` mit JPEG-Pfad funktioniert auch für RGB-Bilder
  ohne Alpha-Kanal (defensives ``convert("RGBA")``).
* Fix #9 — ``restore_original`` schiebt den aktuellen Stand in den Undo-Stack,
  statt den Verlauf zu verwerfen.
* A1 — ``load_image`` wendet EXIF-Orientierung an, damit
  Smartphone-Fotos nicht gekippt erscheinen.
* A4 — ``save_image`` schreibt TIFF mit Transparenz.
* A8 — ``redo()`` macht ein ``undo()`` rückgängig; neue Aktionen
  verwerfen den Redo-Stapel.
"""
import numpy as np
from PIL import Image

from bgremover import ImageCanvas
from bgremover.canvas_history import CanvasHistory


# ── Fix #7: save_image ─────────────────────────────────────────────────

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


def test_save_jpeg_composites_alpha_on_white(qapp, tmp_path):
    canvas = ImageCanvas()
    # RGBA: vollständig transparent → muss als weiß rauskommen
    canvas.apply_loaded_image(Image.new("RGBA", (16, 16), (200, 50, 50, 0)), "seed.png")
    out = tmp_path / "transparent.jpg"
    canvas.save_image(str(out))
    saved = np.array(Image.open(out).convert("RGB"))
    # Alle Pixel sollen (praktisch) weiß sein
    assert (saved >= 250).all()


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


# ── Fix #9: restore_original schiebt in Undo ───────────────────────────

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


# ── A1: EXIF-Orientierung beim Laden ────────────────────────────────────

def test_load_image_applies_exif_rotation(qapp, tmp_path):
    """JPEG mit EXIF-Orientation=6 (90° im Uhrzeigersinn) muss beim Laden
    automatisch rotiert werden — sonst erscheinen iPhone-Fotos gekippt."""
    src = Image.new("RGB", (40, 20), (10, 20, 30))
    exif = src.getexif()
    exif[0x0112] = 6  # Orientation tag → 90° CW
    p = tmp_path / "rot.jpg"
    src.save(p, exif=exif)

    canvas = ImageCanvas()
    canvas.load_image(str(p))
    # Nach exif_transpose sind Breite und Höhe getauscht
    assert canvas.image is not None
    assert canvas.image.size == (20, 40)


def test_load_image_without_exif_keeps_orientation(qapp, tmp_path):
    """Ohne EXIF-Tag bleibt die Bildgröße unverändert."""
    src = Image.new("RGB", (30, 15), (200, 100, 50))
    p = tmp_path / "plain.png"
    src.save(p)

    canvas = ImageCanvas()
    canvas.load_image(str(p))
    assert canvas.image is not None
    assert canvas.image.size == (30, 15)


# ── A4: TIFF-Speichern mit Transparenz ──────────────────────────────────

def test_save_tiff_keeps_alpha(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (10, 10), (0, 255, 0, 128)), "seed.png")
    out = tmp_path / "test.tif"
    canvas.save_image(str(out))
    assert out.exists()
    saved = Image.open(out)
    assert saved.mode == "RGBA"
    assert (np.array(saved)[:, :, 3] == 128).all()


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


# ── A8: Redo-Stack ──────────────────────────────────────────────────────

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


# ── Undo-Stack: Speicherlimit-Eviction (Fix #5) ────────────────────────

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
