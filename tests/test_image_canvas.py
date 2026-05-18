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

from BgRemover import ImageCanvas, pil_to_numpy


# ── Fix #7: save_image ─────────────────────────────────────────────────

def test_save_jpeg_with_rgb_input_does_not_crash(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas._pil = Image.new("RGB", (32, 24), (200, 50, 50))
    out = tmp_path / "test.jpg"
    canvas.save_image(str(out))
    assert out.exists()
    saved = Image.open(out)
    assert saved.size == (32, 24)
    assert saved.mode in ("RGB", "L")


def test_save_jpeg_composites_alpha_on_white(qapp, tmp_path):
    canvas = ImageCanvas()
    # RGBA: vollständig transparent → muss als weiß rauskommen
    canvas._pil = Image.new("RGBA", (16, 16), (200, 50, 50, 0))
    out = tmp_path / "transparent.jpg"
    canvas.save_image(str(out))
    saved = np.array(Image.open(out).convert("RGB"))
    # Alle Pixel sollen (praktisch) weiß sein
    assert (saved >= 250).all()


def test_save_png_keeps_alpha(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas._pil = Image.new("RGBA", (10, 10), (0, 255, 0, 0))
    out = tmp_path / "transparent.png"
    canvas.save_image(str(out))
    saved = Image.open(out)
    assert saved.mode == "RGBA"
    assert (np.array(saved)[:, :, 3] == 0).all()


def test_save_webp(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas._pil = Image.new("RGBA", (12, 12), (50, 50, 250, 255))
    out = tmp_path / "out.webp"
    canvas.save_image(str(out))
    assert out.exists()


def test_save_image_without_loaded_image_is_noop(qapp, tmp_path):
    canvas = ImageCanvas()
    # _pil ist None → save_image darf nicht crashen und nichts schreiben
    out = tmp_path / "should_not_exist.png"
    canvas.save_image(str(out))
    assert not out.exists()


# ── Fix #9: restore_original schiebt in Undo ───────────────────────────

def test_restore_original_pushes_current_state_to_undo(qapp):
    canvas = ImageCanvas()
    canvas._original = Image.new("RGBA", (20, 20), (255, 0, 0, 255))
    canvas._pil      = Image.new("RGBA", (20, 20), (0, 255, 0, 255))
    canvas._arr      = np.array(canvas._pil)
    canvas._mask     = np.zeros((20, 20), dtype=bool)

    assert len(canvas._undo) == 0
    canvas.restore_original()
    assert len(canvas._undo) == 1
    assert np.array(canvas._pil)[0, 0].tolist() == [255, 0, 0, 255]


def test_undo_after_restore_recovers_edited_state(qapp):
    canvas = ImageCanvas()
    canvas._original = Image.new("RGBA", (20, 20), (255, 0, 0, 255))
    canvas._pil      = Image.new("RGBA", (20, 20), (0, 255, 0, 255))
    canvas._arr      = np.array(canvas._pil)
    canvas._mask     = np.zeros((20, 20), dtype=bool)

    canvas.restore_original()
    canvas.undo()
    assert np.array(canvas._pil)[0, 0].tolist() == [0, 255, 0, 255]


def test_restore_original_without_original_is_noop(qapp):
    canvas = ImageCanvas()
    canvas._original = None
    canvas.restore_original()
    assert canvas._pil is None


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
    assert canvas._pil.size == (20, 40)


def test_load_image_without_exif_keeps_orientation(qapp, tmp_path):
    """Ohne EXIF-Tag bleibt die Bildgröße unverändert."""
    src = Image.new("RGB", (30, 15), (200, 100, 50))
    p = tmp_path / "plain.png"
    src.save(p)

    canvas = ImageCanvas()
    canvas.load_image(str(p))
    assert canvas._pil.size == (30, 15)


# ── A4: TIFF-Speichern mit Transparenz ──────────────────────────────────

def test_save_tiff_keeps_alpha(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas._pil = Image.new("RGBA", (10, 10), (0, 255, 0, 128))
    out = tmp_path / "test.tif"
    canvas.save_image(str(out))
    assert out.exists()
    saved = Image.open(out)
    assert saved.mode == "RGBA"
    assert (np.array(saved)[:, :, 3] == 128).all()


def test_save_tiff_with_tiff_extension(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas._pil = Image.new("RGBA", (8, 8), (50, 100, 200, 255))
    out = tmp_path / "explicit.tiff"
    canvas.save_image(str(out))
    assert out.exists()


# ── Robustheit: save_image-Fehlerpfad ───────────────────────────────────

def test_save_image_returns_true_on_success(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas._pil = Image.new("RGBA", (8, 8), (10, 20, 30, 255))
    assert canvas.save_image(str(tmp_path / "ok.png")) is True


def test_save_image_io_error_reports_and_returns_false(qapp, tmp_path):
    canvas = ImageCanvas()
    canvas._pil = Image.new("RGBA", (8, 8), (10, 20, 30, 255))
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
    img = Image.new("RGBA", (8, 8), color)
    c._pil  = img
    c._arr  = pil_to_numpy(img)
    c._mask = np.zeros((8, 8), dtype=bool)
    return c


def test_redo_restores_state_after_undo(qapp):
    c = _seed_canvas((255, 0, 0, 255))
    c._apply_pil(Image.new("RGBA", (8, 8), (0, 255, 0, 255)), desc="grün")
    assert np.array(c._pil)[0, 0].tolist() == [0, 255, 0, 255]
    c.undo()
    assert np.array(c._pil)[0, 0].tolist() == [255, 0, 0, 255]
    c.redo()
    assert np.array(c._pil)[0, 0].tolist() == [0, 255, 0, 255]


def test_new_action_clears_redo_stack(qapp):
    c = _seed_canvas((255, 0, 0, 255))
    c._apply_pil(Image.new("RGBA", (8, 8), (0, 255, 0, 255)), desc="grün")
    c.undo()
    assert len(c._redo) == 1
    # Neue Aktion ⇒ Redo-Branch verworfen
    c._apply_pil(Image.new("RGBA", (8, 8), (0, 0, 255, 255)), desc="blau")
    assert len(c._redo) == 0


def test_redo_on_empty_stack_is_noop(qapp):
    c = _seed_canvas((100, 100, 100, 255))
    # Darf nicht crashen, _pil bleibt identisch
    c.redo()
    assert np.array(c._pil)[0, 0].tolist() == [100, 100, 100, 255]


def test_load_image_clears_both_stacks(qapp, tmp_path):
    """Beim Laden eines neuen Bildes werden Undo und Redo geleert."""
    c = _seed_canvas((10, 20, 30, 255))
    c._apply_pil(Image.new("RGBA", (8, 8), (40, 50, 60, 255)), desc="x")
    c.undo()
    assert len(c._redo) == 1
    p = tmp_path / "fresh.png"
    Image.new("RGB", (12, 12), (200, 200, 200)).save(p)
    c.load_image(str(p))
    assert len(c._undo) == 0
    assert len(c._redo) == 0
    assert c._undo_bytes == 0


# ── Undo-Stack: Speicherlimit-Eviction (Fix #5) ────────────────────────

def test_undo_stack_evicts_oldest_under_memory_limit(qapp, monkeypatch):
    """Überschreitet der Undo-Stack das Byte-Limit, fallen älteste
    Einträge raus – aber nie der letzte (mind. 1 Schritt bleibt)."""
    import BgRemover
    one_image = 8 * 8 * 4                       # RGBA-Rohdaten eines 8×8-Bilds
    monkeypatch.setattr(BgRemover, "_UNDO_MEMORY_LIMIT", one_image)

    c = _seed_canvas((0, 0, 0, 255))
    for i in range(6):
        c._apply_pil(Image.new("RGBA", (8, 8), (i, i, i, 255)),
                     desc=f"edit{i}")

    assert len(c._undo) == 1                    # nur 1 Eintrag passt rein
    assert c._undo_bytes == one_image           # laufende Summe konsistent

    c.undo()                                    # bleibt funktionsfähig
    assert c._undo_bytes == 0


def test_undo_bytes_tracks_push_and_pop(qapp):
    """Die laufende Byte-Summe entspricht der tatsächlichen Stack-Grösse."""
    c = _seed_canvas((1, 2, 3, 255))
    c._apply_pil(Image.new("RGBA", (8, 8), (4, 5, 6, 255)), desc="a")
    c._apply_pil(Image.new("RGBA", (8, 8), (7, 8, 9, 255)), desc="b")
    assert c._undo_bytes == sum(
        i.width * i.height * 4 for i, _ in c._undo)
    c.undo()
    assert c._undo_bytes == sum(
        i.width * i.height * 4 for i, _ in c._undo)
