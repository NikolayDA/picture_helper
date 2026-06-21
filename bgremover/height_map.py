"""Qt-freie Höhen-Repräsentation und 2D-Visualisierung (#345).

Fundament des Height-Map-Arbeitsbereichs (Epic #344): Eine HEIGHT-Ebene hält ihre
Höhe als **Graustufe** in den vorhandenen RGBA-Layerdaten – Konvention
``R == G == B == Höhe`` und ``A == Deckung``. Dieses Modul kapselt die
verlustfreie Konvertierung Höhe ↔ Array, eine Normalisierung beliebiger Werte auf
den Höhenbereich, die Canvas-Größen-Validierung sowie den Graustufen-Anzeigepfad,
der eine aktive HEIGHT-Ebene neben dem COLOR-Komposit sichtbar macht. Konventionen
analog ``image_ops``/``image_utils``: reine Logik ohne Qt-, Datei- oder
Netzzugriffe, deutsche Docstrings, englische Identifier, strikte mypy-Typisierung.

16-Bit-Erweiterbarkeit: Höhen werden intern als ``uint16`` geführt und über
``max_value`` interpretiert; aktuell ist ``max_value == HEIGHT_MAX_8BIT`` (volle
Parität zu den 8-Bit-RGBA-Layerdaten). Eine spätere 16-Bit-Tiefe (Rang #6/#7)
erhöht nur ``max_value`` und ändert die Skalierung in :func:`height_to_layer`,
ohne die öffentliche API zu brechen.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

# Voller Wertebereich einer 8-Bit-Höhe. Die Höhen-Repräsentation ist über
# ``HeightField.max_value`` 16-Bit-erweiterbar; dieser Standard hält die
# bitgenaue Parität zu den RGBA-Layerdaten.
HEIGHT_MAX_8BIT = 255

# Standard-Kanalgewichtung (Rec. 601 Luma): wahrnehmungsnahe Graustufe aus R/G/B.
# Die Summe ist 1.0, sodass die gewichtete Luminanz im Bereich 0..255 bleibt.
LUMA_WEIGHTS_REC601 = (0.299, 0.587, 0.114)


class HeightMapError(ValueError):
    """Fehler bei Höhen-Konvertierung, Normalisierung oder Größen-Validierung."""


@dataclass(frozen=True)
class HeightField:
    """Qt-freie Höhen-Repräsentation: ein 2D-Höhenfeld plus Deckungs-Alpha.

    ``values`` hält die Höhe je Pixel als ``uint16`` im Bereich ``0..max_value``
    (Form ``(H, W)``); ``coverage`` ist der Deckungs-Alphakanal als ``uint8``
    (``0..255``, gleiche Form). ``max_value`` trennt die logische Höhenauflösung
    von der 8-Bit-Speicherung der Ebene und ist der Hebel für eine spätere
    16-Bit-Tiefe (Standard ``HEIGHT_MAX_8BIT``).

    Die Invarianten (Form, dtype, Wertebereich) werden beim Anlegen geprüft;
    danach ist das Feld unveränderlich (``frozen``). Vergleich/Hashing über die
    – teuren – Pixelinhalte ist bewusst nicht vorgesehen.
    """

    values: np.ndarray
    coverage: np.ndarray
    max_value: int = HEIGHT_MAX_8BIT

    def __post_init__(self) -> None:
        if self.max_value <= 0:
            raise HeightMapError(f"max_value muss positiv sein, war {self.max_value}")
        if self.values.ndim != 2 or self.coverage.ndim != 2:
            raise HeightMapError("values und coverage müssen 2D-Arrays sein")
        if self.values.shape != self.coverage.shape:
            raise HeightMapError(
                f"Form von values {self.values.shape} passt nicht zu "
                f"coverage {self.coverage.shape}"
            )
        if self.values.dtype != np.uint16:
            raise HeightMapError(f"values muss uint16 sein, war {self.values.dtype}")
        if self.coverage.dtype != np.uint8:
            raise HeightMapError(f"coverage muss uint8 sein, war {self.coverage.dtype}")
        if self.values.size and int(self.values.max()) > self.max_value:
            raise HeightMapError(
                f"values überschreitet max_value ({self.max_value})"
            )

    @property
    def size(self) -> tuple[int, int]:
        """Größe als ``(width, height)`` – analog zu ``Layer.size``/``Project.size``."""
        h, w = self.values.shape[:2]
        return (w, h)


def _to_gray8(field: HeightField) -> np.ndarray:
    """Skaliert das Höhenfeld auf 8-Bit-Grau (``uint8``, ``0..255``).

    Bei ``max_value == HEIGHT_MAX_8BIT`` ist die Abbildung die Identität (und
    damit verlustfrei); für größere ``max_value`` (16-Bit-Pfad) wird linear auf
    ``0..255`` heruntergerechnet.
    """
    if field.max_value == HEIGHT_MAX_8BIT:
        return field.values.astype(np.uint8)
    scaled = np.rint(
        field.values.astype(np.float64) * (HEIGHT_MAX_8BIT / field.max_value)
    )
    return np.clip(scaled, 0, HEIGHT_MAX_8BIT).astype(np.uint8)


def layer_to_height(image: Image.Image) -> HeightField:
    """Liest eine HEIGHT-Ebene als :class:`HeightField` (verlustfrei für Graustufen).

    Konvention ``R == G == B == Höhe``: Der Rotkanal ist die kanonische Höhe, der
    Alphakanal die Deckung. Beliebige Eingaben werden zunächst nach RGBA
    normalisiert; für eine bereits graustufige Ebene gilt damit
    ``height_to_layer(layer_to_height(img))`` bitgenau gleich ``img``.
    """
    rgba = image if image.mode == "RGBA" else image.convert("RGBA")
    arr = np.asarray(rgba)
    # astype kopiert: das Feld besitzt seine Puffer unabhängig vom Eingabebild.
    values = arr[:, :, 0].astype(np.uint16)
    coverage = arr[:, :, 3].astype(np.uint8)
    return HeightField(values=values, coverage=coverage)


def height_to_layer(field: HeightField) -> Image.Image:
    """Baut aus einem Höhenfeld die graustufige RGBA-Ebene (``R == G == B == Höhe``).

    Höhen werden von ``0..max_value`` auf den 8-Bit-Graubereich ``0..255``
    skaliert (bei ``max_value == HEIGHT_MAX_8BIT`` identisch, also verlustfrei),
    auf alle drei Farbkanäle gelegt und mit dem Deckungs-Alphakanal versehen.
    Inverse von :func:`layer_to_height` für graustufige Ebenen.
    """
    gray = _to_gray8(field)
    h, w = field.values.shape[:2]
    rgba = np.empty((h, w, 4), dtype=np.uint8)
    rgba[:, :, 0] = gray
    rgba[:, :, 1] = gray
    rgba[:, :, 2] = gray
    rgba[:, :, 3] = field.coverage
    return Image.fromarray(rgba, "RGBA")


def layer_to_gray_image(image: Image.Image) -> Image.Image:
    """Graustufen-Anzeigebild einer HEIGHT-Ebene für den 2D-Canvas.

    Erzwingt die Graustufen-Darstellung (``R == G == B == Höhe``, ``A == Deckung``)
    als ``height_to_layer(layer_to_height(image))`` – auch falls die gespeicherten
    Pixel von ``R == G == B`` abweichen sollten. So zeigt der Canvas eine aktive
    HEIGHT-Ebene konsistent grau an, während das COLOR-Komposit unberührt bleibt.
    """
    return height_to_layer(layer_to_height(image))


def generate_from_image(
    image: Image.Image,
    *,
    weights: tuple[float, float, float] = LUMA_WEIGHTS_REC601,
    black: int = 0,
    white: int = HEIGHT_MAX_8BIT,
    gamma: float = 1.0,
    invert: bool = False,
    max_value: int = HEIGHT_MAX_8BIT,
) -> HeightField:
    """Erzeugt **deterministisch** ein Höhenfeld aus einem Farbbild (#346).

    Reine, reproduzierbare Pipeline (kein Zufall, keine globalen Statistiken):

    1. **Kanalgewichtung/Luminanz:** gewichteter Mittelwert von R/G/B mit
       ``weights`` (intern auf ihre Summe normiert; Standard Rec. 601). Ergebnis
       liegt in ``0..255``.
    2. **Tonwert-Kennlinie:** linearer Schwarz-/Weißpunkt – ``black`` wird ``0``,
       ``white`` wird ``1``; dazwischen linear, außerhalb geklemmt.
    3. **Gamma:** ``wert ** gamma`` auf dem normierten ``0..1``-Wert (``gamma > 1``
       senkt die Mitten ab, ``< 1`` hebt sie an).
    4. **Invertieren:** optional ``1 - wert`` (Vertiefungen ↔ Erhebungen tauschen).

    Die normierte Höhe wird auf ``0..max_value`` skaliert (``uint16``); die
    **Deckung** übernimmt den Alphakanal des Bildes, sodass transparente Bereiche
    höhenlos bleiben. Quelle ist die aktive COLOR-Ebene bzw. das Farb-Komposit;
    importierte Graustufen (``R==G==B``) ergeben mit den Standardgewichten genau
    ihren Grauwert als Höhe. Fehlerhafte Parameter werfen :class:`HeightMapError`.
    """
    if max_value <= 0:
        raise HeightMapError(f"max_value muss positiv sein, war {max_value}")
    if len(weights) != 3:
        raise HeightMapError("weights braucht genau drei Werte (R, G, B)")
    if any(w < 0 for w in weights):
        raise HeightMapError("weights müssen nicht-negativ sein")
    wsum = float(sum(weights))
    if wsum <= 0.0:
        raise HeightMapError("Summe der weights muss > 0 sein")
    if not 0 <= black < white <= HEIGHT_MAX_8BIT:
        raise HeightMapError(
            f"Tonwert verlangt 0 <= black < white <= {HEIGHT_MAX_8BIT}, "
            f"war black={black}, white={white}"
        )
    if gamma <= 0.0:
        raise HeightMapError(f"gamma muss positiv sein, war {gamma}")

    rgba = image if image.mode == "RGBA" else image.convert("RGBA")
    src = np.asarray(rgba)
    rgb = src[:, :, :3].astype(np.float64)
    wr, wg, wb = weights[0] / wsum, weights[1] / wsum, weights[2] / wsum
    luma = rgb[:, :, 0] * wr + rgb[:, :, 1] * wg + rgb[:, :, 2] * wb
    norm = np.clip((luma - black) / (white - black), 0.0, 1.0)
    if gamma != 1.0:
        norm = norm ** gamma
    if invert:
        norm = 1.0 - norm
    values = np.rint(norm * max_value).astype(np.uint16)
    coverage = src[:, :, 3].astype(np.uint8)
    return HeightField(values=values, coverage=coverage, max_value=max_value)


def normalize_to_height(
    data: np.ndarray, *, max_value: int = HEIGHT_MAX_8BIT
) -> np.ndarray:
    """Skaliert beliebige endliche Werte linear auf ``0..max_value`` (``uint16``).

    Min-Max-Normalisierung: das kleinste Eingangselement wird ``0``, das größte
    ``max_value``. Eine konstante Eingabe (Spannweite ``0``) ergibt ein Nullfeld.
    Leere Eingaben, nicht-endliche Werte (NaN/Inf) und ``max_value <= 0`` werden
    mit :class:`HeightMapError` abgelehnt. Geteiltes Primitiv für Erzeugung/Import
    (#346) und Optimierung (#348); die Form der Eingabe bleibt erhalten.
    """
    if max_value <= 0:
        raise HeightMapError(f"max_value muss positiv sein, war {max_value}")
    if data.size == 0:
        raise HeightMapError("Eingabe für die Normalisierung ist leer")
    work = data.astype(np.float64)
    if not bool(np.all(np.isfinite(work))):
        raise HeightMapError("Eingabe enthält nicht-endliche Werte (NaN/Inf)")
    lo = float(work.min())
    hi = float(work.max())
    if hi <= lo:
        return np.zeros(data.shape, dtype=np.uint16)
    scaled = (work - lo) / (hi - lo) * max_value
    return np.rint(scaled).astype(np.uint16)


def validate_canvas_size(field: HeightField, size: tuple[int, int]) -> None:
    """Prüft die Canvas-Größen-Invariante einer HEIGHT-Ebene.

    ``size`` ist ``(width, height)`` wie ``Project.size``/``Layer.size``; die
    Höhenfeld-Form ``(H, W)`` muss exakt dazu passen, sonst
    :class:`HeightMapError`. Spiegelt die Modell-Invariante „jede Ebene in
    Canvas-Größe" (siehe ``project_model``) für den Qt-freien Höhenpfad.
    """
    if field.size != size:
        raise HeightMapError(
            f"Höhenfeld-Größe {field.size} passt nicht zur Canvas-Größe {size}"
        )
