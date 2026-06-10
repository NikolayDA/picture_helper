"""Tests für Geometrie-Operationen: Drehen, Spiegeln, Ecken abrunden,
interaktiver Zuschnitt (Ratio + Kreis).

Diese Pfade waren bislang nur statisch bzw. über das Overlay-Item
abgedeckt – hier wird der tatsächliche Pixel-Output geprüft.
"""
import numpy as np
from PIL import Image

from bgremover import ImageCanvas


def _canvas(color=(10, 20, 30, 255), size=(40, 20)):
    c = ImageCanvas()
    img = Image.new("RGBA", size, color)
    # apply_loaded_image initialisiert auch die (leere) Auswahlmaske.
    c.apply_loaded_image(img, "seed.png")
    return c


def _canvas_image(c: ImageCanvas) -> Image.Image:
    img = c.image
    assert img is not None
    return img


# ── Drehen ─────────────────────────────────────────────────────────────

def test_rotate_90_swaps_dimensions(qapp):
    c = _canvas(size=(40, 20))
    c.apply_rotate(90)
    assert _canvas_image(c).size == (20, 40)


def test_rotate_270_swaps_dimensions(qapp):
    c = _canvas(size=(40, 20))
    c.apply_rotate(270)
    assert _canvas_image(c).size == (20, 40)


def test_rotate_180_keeps_dimensions(qapp):
    c = _canvas(size=(40, 20))
    c.apply_rotate(180)
    assert _canvas_image(c).size == (40, 20)


def test_rotate_free_angle_expands_canvas(qapp):
    c = _canvas(size=(40, 20))
    c.apply_rotate(45)
    w, h = _canvas_image(c).size
    assert w > 40 and h > 20            # Expand verhindert Abschneiden


def test_rotate_rejected_when_result_exceeds_pixel_limit(qapp, monkeypatch):
    """N2: Eine schräge Drehung, deren expandiertes Ergebnis das
    Megapixel-Limit überschreitet, wird abgelehnt – das Bild bleibt
    unverändert und der Nutzer sieht eine „zu groß"-Meldung. Ohne dieses
    Gate griffe der Megapixel-Schutz nur beim Laden, nicht auf dem
    Rotationsergebnis (das schräg bis ~2× aufblähen kann).
    """
    import bgremover.canvas_transform as ct
    monkeypatch.setattr(ct, "_MAX_MEGAPIXELS", 0.001)   # Limit: 1000 px

    c = _canvas(size=(40, 20))           # 45° ⇒ ~43×43 ≈ 1849 px > Limit
    before = _canvas_image(c).size
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)

    c.apply_rotate(45)

    assert _canvas_image(c).size == before           # nicht gedreht
    assert any("zu groß" in m for m in msgs)


def test_rotate_quarter_turn_unaffected_by_pixel_limit(qapp, monkeypatch):
    """90°-Drehung vergrößert die Fläche nicht und darf daher auch unter einem
    knappen Limit nicht abgelehnt werden – nur schräge Drehungen expandieren."""
    import bgremover.canvas_transform as ct
    monkeypatch.setattr(ct, "_MAX_MEGAPIXELS", 0.001)   # Limit: 1000 px

    c = _canvas(size=(40, 20))           # 90° ⇒ 20×40 = 800 px < Limit
    c.apply_rotate(90)
    assert _canvas_image(c).size == (20, 40)          # gedreht


def test_rotate_without_image_is_noop(qapp):
    c = ImageCanvas()
    c.apply_rotate(90)                  # darf nicht crashen
    assert c.image is None


# ── Spiegeln ───────────────────────────────────────────────────────────

def test_flip_horizontal_mirrors(qapp):
    # Markierungspixel VOR dem Laden setzen – so bleibt der Test komplett
    # auf der Public API (kein nachträglicher _arr-Resync nötig).
    img = Image.new("RGBA", (4, 1), (10, 20, 30, 255))
    img.putpixel((0, 0), (255, 0, 0, 255))
    c = ImageCanvas()
    c.apply_loaded_image(img, "seed.png")
    c.apply_flip(True)
    assert _canvas_image(c).getpixel((3, 0)) == (255, 0, 0, 255)


def test_flip_vertical_mirrors(qapp):
    img = Image.new("RGBA", (1, 4), (10, 20, 30, 255))
    img.putpixel((0, 0), (0, 255, 0, 255))
    c = ImageCanvas()
    c.apply_loaded_image(img, "seed.png")
    c.apply_flip(False)
    assert _canvas_image(c).getpixel((0, 3)) == (0, 255, 0, 255)


# ── Ecken abrunden ─────────────────────────────────────────────────────

def test_round_corners_makes_corner_transparent(qapp):
    c = _canvas(color=(0, 0, 0, 255), size=(40, 40))
    c.apply_round_corners(15)
    arr = np.array(_canvas_image(c))
    assert arr[0, 0, 3] == 0           # Ecke transparent
    assert arr[20, 20, 3] == 255       # Mitte opak


def test_round_corners_zero_radius_is_noop(qapp):
    c = _canvas(color=(0, 0, 0, 255), size=(20, 20))
    before = np.array(_canvas_image(c)).copy()
    c.apply_round_corners(0)
    np.testing.assert_array_equal(np.array(_canvas_image(c)), before)


# ── Interaktiver Zuschnitt ─────────────────────────────────────────────

def test_confirm_crop_ratio_changes_size(qapp):
    c = _canvas(color=(5, 5, 5, 255), size=(40, 20))
    c.start_crop_ratio(1, 1)
    assert c._crop_overlay is not None
    c.confirm_crop()
    assert c._crop_overlay is None
    w, h = _canvas_image(c).size
    assert w == h                      # 1:1 zugeschnitten


def test_confirm_crop_circle_adds_alpha_mask(qapp):
    c = _canvas(color=(0, 0, 0, 255), size=(40, 40))
    c.start_crop_circle()
    c.confirm_crop()
    arr = np.array(_canvas_image(c))
    h, w = arr.shape[:2]
    assert arr[0, 0, 3] == 0                   # Ecke ausserhalb des Kreises
    assert arr[h // 2, w // 2, 3] == 255       # Mitte opak


def test_cancel_crop_removes_overlay_without_change(qapp):
    c = _canvas(color=(9, 9, 9, 255), size=(30, 30))
    before = _canvas_image(c).size
    c.start_crop_ratio(16, 9)
    c.cancel_crop()
    assert c._crop_overlay is None
    assert _canvas_image(c).size == before
