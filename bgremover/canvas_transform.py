"""Geometrie-Transformationen für ``ImageCanvas``.

Kapselt Drehen, Spiegeln und Ecken-Abrunden, damit ``canvas.py`` analog zu
``CanvasCrop`` / ``CanvasHistory`` / ``CanvasLasso`` / ``CanvasSelection``
weniger Zuständigkeiten trägt.

Die Methoden setzen voraus, dass auf dem Canvas ein Bild geladen ist;
der ``None``-Guard und das ``statusMsg``-Signal leben weiter auf der
``ImageCanvas``-Fassade (Tests verbinden sich auf das Canvas-Signal).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from bgremover.constants import _MAX_MEGAPIXELS
from bgremover.image_ops import flip_image, rotate_image, rotated_size, round_corners

if TYPE_CHECKING:
    from bgremover.canvas import ImageCanvas


class CanvasTransform:
    """Wendet Geometrie-Transformationen auf den Canvas-Bildzustand an."""

    def __init__(self, canvas: ImageCanvas) -> None:
        self._canvas = canvas

    def apply_round_corners(self, radius: int) -> None:
        """Rundet die Ecken des Bildes mit dem gegebenen Radius ab."""
        img = self._canvas.image
        assert img is not None  # ImageCanvas-Fassade garantiert das via Guard
        if radius <= 0:
            self._canvas.statusMsg.emit("Radius muss > 0 sein")
            return
        result, r = round_corners(img, radius)
        self._canvas.apply_edit(result, desc=f"Ecken abgerundet ({r} px)")
        self._canvas.statusMsg.emit(f"Ecken abgerundet: {r} px Radius")

    def apply_rotate(self, degrees: int) -> None:
        """Dreht das Bild um den angegebenen Winkel (gegen den Uhrzeigersinn).

        Bei 90° / 270° werden Breite und Höhe getauscht. Bei beliebigen
        Winkeln wird die Canvas so vergrößert, dass nichts abgeschnitten wird.
        Eine schräge Drehung kann die Fläche bis ~2× aufblähen; überschreitet
        das Ergebnis das Megapixel-Limit, wird sie abgelehnt (Statusmeldung)
        statt eine ungebremste Speicherspitze zu riskieren – analog zum
        Lade-Gate, das nur die *Eingabe* prüft, nicht das Rotationsergebnis.
        """
        img = self._canvas.image
        assert img is not None  # ImageCanvas-Fassade garantiert das via Guard
        new_w, new_h = rotated_size(img.width, img.height, degrees)
        if new_w * new_h / 1_000_000 > _MAX_MEGAPIXELS:
            self._canvas.statusMsg.emit(
                f"Drehung um {abs(degrees)}° würde das Bild zu groß machen "
                f"({new_w * new_h / 1_000_000:.0f} MP) – Maximum: {_MAX_MEGAPIXELS} MP"
            )
            return
        result = rotate_image(img, degrees)
        direction = "↺" if degrees > 0 else "↻"
        self._canvas.apply_edit(result, desc=f"{direction} Gedreht {abs(degrees)}°")
        self._canvas.statusMsg.emit(
            f"{direction} Gedreht: {abs(degrees)}°  "
            f"({result.width} × {result.height} px)"
        )

    def apply_flip(self, horizontal: bool) -> None:
        """Spiegelt das Bild horizontal oder vertikal."""
        img = self._canvas.image
        assert img is not None  # ImageCanvas-Fassade garantiert das via Guard
        result = flip_image(img, horizontal)
        if horizontal:
            self._canvas.apply_edit(result, desc="↔ Horizontal gespiegelt")
            self._canvas.statusMsg.emit("↔ Horizontal gespiegelt")
        else:
            self._canvas.apply_edit(result, desc="↕ Vertikal gespiegelt")
            self._canvas.statusMsg.emit("↕ Vertikal gespiegelt")
