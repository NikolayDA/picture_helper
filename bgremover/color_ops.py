"""Reine Farbkorrektur-Operationen für den Canvas (Qt-frei).

Wie :mod:`image_ops`/:mod:`height_ops` kennt dieses Modul keine Qt-Widgets,
Signale oder Einstellungen – nur Pillow/numpy. Es ist die **wiederverwendbare
Tonwert-Primitive** für die Farbkorrektur der aktiven COLOR-Ebene (#360) und
zugleich Fundament für die spätere geteilte Tonwert-/Graustufen-Engine (Rang #6),
damit diese darauf aufsetzt statt zu duplizieren. Konventionen analog
``image_ops``: reine Logik, deutsche Docstrings, englische Identifier, strikte
mypy-Typisierung.
"""
from __future__ import annotations

from collections.abc import Callable

from PIL import Image, ImageEnhance

# Reine Farb-Operation; UI-Closures lesen ihre Reglerwerte beim Aufruf (analog
# ``HeightOp`` im Höhen-Panel).
ColorOp = Callable[[Image.Image], Image.Image]


def adjust_color(
    img: Image.Image,
    *,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
) -> Image.Image:
    """Passt Helligkeit, Kontrast und Sättigung der **RGB-Kanäle** an.

    Jeder Faktor ist multiplikativ um den Neutralwert ``1.0`` herum
    (``> 1.0`` verstärkt, ``< 1.0`` schwächt, ``0.0`` entsättigt vollständig zu
    Graustufen). Angewandt wird die Pillow-Kette
    ``Brightness → Contrast → Color`` – deterministisch und in plausibler
    Richtung.

    **Alpha bleibt exakt erhalten:** Die Anpassung läuft nur auf den
    RGB-Kanälen; der Alphakanal des Originals wird unverändert wieder
    angehängt (``ImageEnhance`` würde sonst über den mitskalierten Alphakanal
    die Deckung verfälschen). **Neutralwerte (1.0/1.0/1.0)** geben das
    Eingabebild **bitidentisch** (dasselbe Objekt) zurück – ein echtes No-op;
    jeder einzelne Neutralfaktor überspringt seinen Schritt verlustfrei.
    """
    if brightness == 1.0 and contrast == 1.0 and saturation == 1.0:
        return img
    rgba = img if img.mode == "RGBA" else img.convert("RGBA")
    bands = rgba.split()
    rgb = Image.merge("RGB", bands[:3])
    if brightness != 1.0:
        rgb = ImageEnhance.Brightness(rgb).enhance(brightness)
    if contrast != 1.0:
        rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    if saturation != 1.0:
        rgb = ImageEnhance.Color(rgb).enhance(saturation)
    return Image.merge("RGBA", (*rgb.split(), bands[3]))
