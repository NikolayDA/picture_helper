"""Tests für ImageCanvas: Speichern und Undo/Restore-Logik.

Verteidigt:

* Fix #7 — ``save_image`` mit JPEG-Pfad funktioniert auch für RGB-Bilder
  ohne Alpha-Kanal (defensives ``convert("RGBA")``).
* Fix #9 — ``restore_original`` schiebt den aktuellen Stand in den Undo-Stack,
  statt den Verlauf zu verwerfen.
"""
import numpy as np
from PIL import Image

from BgRemover import ImageCanvas


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
