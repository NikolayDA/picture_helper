"""Tests für ``CropBar`` – Verdrahtung von Buttons und Sichtbarkeit.

``CropBar`` wurde bislang in keinem Test direkt instanziiert, nur indirekt
über das MainWindow-Setup mitgerendert (Coverage ohne echten Wiring-Nachweis,
#716). Diese Tests prüfen die eigentliche Verbindung aus ``CropBar.bind``:
Klick auf Bestätigen/Abbrechen ruft die passende Canvas-Methode, und
``cropModeChanged`` steuert die Sichtbarkeit der Leiste.
"""
from __future__ import annotations

from PIL import Image

from bgremover import ImageCanvas
from bgremover.crop_bar import CropBar


def _canvas() -> ImageCanvas:
    c = ImageCanvas()
    c.apply_loaded_image(Image.new("RGBA", (40, 40), (10, 20, 30, 255)), "seed.png")
    return c


def test_bind_starts_hidden(qapp):
    bar = CropBar()
    canvas = _canvas()
    bar.bind(canvas)
    assert bar.isVisible() is False


def test_crop_mode_changed_toggles_visibility(qapp):
    bar = CropBar()
    canvas = _canvas()
    bar.bind(canvas)

    canvas.start_crop_ratio(1, 1)
    assert bar.isVisible() is True

    canvas.cancel_crop()
    assert bar.isVisible() is False


def test_confirm_button_click_calls_canvas_confirm_crop(qapp):
    # Nicht-quadratische Ausgangsgroesse: ein 1:1-Zuschnitt aendert damit
    # tatsaechlich die Bildgroesse – ein Effekt, den ``cancel_crop`` nicht
    # hat. Ohne diese Unterscheidung wuerde eine Regression, die beide
    # Buttons auf ``cancel_crop`` verdrahtet, hier unbemerkt bleiben.
    bar = CropBar()
    canvas = ImageCanvas()
    canvas.apply_loaded_image(Image.new("RGBA", (40, 60), (10, 20, 30, 255)), "seed.png")
    bar.bind(canvas)
    canvas.start_crop_ratio(1, 1)
    assert canvas._crop.overlay is not None
    assert canvas.image is not None
    assert canvas.image.size == (40, 60)

    bar._btn_confirm.click()

    assert canvas._crop.overlay is None
    assert canvas.image is not None
    assert canvas.image.size == (40, 40)  # Zuschnitt wurde angewandt
    assert bar.isVisible() is False


def test_cancel_button_click_calls_canvas_cancel_crop(qapp):
    bar = CropBar()
    canvas = _canvas()
    bar.bind(canvas)
    canvas.start_crop_ratio(1, 1)
    before = canvas.image
    assert canvas._crop.overlay is not None

    bar._btn_cancel.click()

    assert canvas._crop.overlay is None
    assert canvas.image is before  # Abbrechen wendet keine Änderung an
    assert bar.isVisible() is False
