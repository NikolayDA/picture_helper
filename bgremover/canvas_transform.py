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

from PIL import Image

from bgremover.constants import _MAX_MEGAPIXELS
from bgremover.i18n import tr
from bgremover.image_ops import (
    flip_image,
    resized_size,
    rotate_image,
    rotated_size,
    round_corners,
)

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
            self._canvas.statusMsg.emit(tr("canvas.radius_positive"))
            return
        result, r = round_corners(img, radius)
        self._canvas.apply_edit(result, desc=tr("history.desc.round_corners", r=r))
        self._canvas.statusMsg.emit(tr("canvas.corners_rounded", r=r))

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
            self._canvas.statusMsg.emit(tr(
                "canvas.rotate_too_large",
                degrees=abs(degrees),
                mp=new_w * new_h / 1_000_000,
                maximum=_MAX_MEGAPIXELS,
            ))
            return
        direction = "↺" if degrees > 0 else "↻"
        # Drehen ändert die Canvas-Größe → über apply_geometry auf alle Ebenen
        # einheitlich (Canvas-Drehung; bei genau einer Ebene wie bisher).
        self._canvas.apply_geometry(
            lambda im: rotate_image(im, degrees),
            desc=tr("history.desc.rotated", direction=direction, degrees=abs(degrees)),
        )
        result = self._canvas.image
        assert result is not None
        self._canvas.statusMsg.emit(tr(
            "canvas.rotated", direction=direction, degrees=abs(degrees),
            w=result.width, h=result.height))

    def apply_flip(self, horizontal: bool) -> None:
        """Spiegelt das Bild horizontal oder vertikal."""
        img = self._canvas.image
        assert img is not None  # ImageCanvas-Fassade garantiert das via Guard
        result = flip_image(img, horizontal)
        msg = tr("canvas.flipped_h") if horizontal else tr("canvas.flipped_v")
        self._canvas.apply_edit(result, desc=msg)
        self._canvas.statusMsg.emit(msg)

    def apply_resize(
        self, width: int, height: int, resample: Image.Resampling
    ) -> None:
        """Skaliert das gesamte Projekt (alle Ebenen) auf ``(width, height)`` px.

        Das Megapixel-Gate prüft die Zielgröße über :func:`resized_size` **vor**
        jeder Allokation und lehnt eine Überschreitung von ``_MAX_MEGAPIXELS`` mit
        übersetzter Statusmeldung ab – analog zum Rotations-Gate, das so die
        ungebremste Speicherspitze vermeidet. Eine Zielgröße gleich der aktuellen
        ist ein No-op (kein Verlaufseintrag). Sonst läuft die Größenänderung über
        den undo-/redobaren, height-bewussten ``resize_project``-Pfad.
        """
        img = self._canvas.image
        assert img is not None  # ImageCanvas-Fassade garantiert das via Guard
        new_w, new_h = resized_size(img.width, img.height, width, height)
        if new_w * new_h / 1_000_000 > _MAX_MEGAPIXELS:
            self._canvas.statusMsg.emit(tr(
                "canvas.resize_too_large",
                w=new_w, h=new_h,
                mp=new_w * new_h / 1_000_000,
                maximum=_MAX_MEGAPIXELS,
            ))
            return
        if (new_w, new_h) == img.size:
            self._canvas.statusMsg.emit(tr("canvas.resized", w=new_w, h=new_h))
            return
        self._canvas.resize_project(
            new_w, new_h, resample,
            tr("history.desc.resized", w=new_w, h=new_h))
        self._canvas.statusMsg.emit(tr("canvas.resized", w=new_w, h=new_h))
