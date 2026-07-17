"""Qt-freie Höhen-Repräsentation und 2D-Visualisierung (#345).

Fundament des Height-Map-Arbeitsbereichs (Epic #344): Eine HEIGHT-Ebene hält ihre
Höhe als **Graustufe** in den vorhandenen RGBA-Layerdaten – Konvention
``R == G == B == Höhe`` und ``A == Deckung``. Dieses Modul kapselt die
verlustfreie Konvertierung Höhe ↔ Array, eine Normalisierung beliebiger Werte auf
den Höhenbereich, die Canvas-Größen-Validierung sowie den Graustufen-Anzeigepfad,
der eine aktive HEIGHT-Ebene neben dem COLOR-Komposit sichtbar macht. Konventionen
analog ``image_ops``/``image_utils``: reine Logik ohne Qt-, Datei- oder
Netzzugriffe, deutsche Docstrings, englische Identifier, strikte mypy-Typisierung.

16-Bit-Vertrag (ADR #586, umgesetzt ab #587): Höhen werden als ``uint16``
geführt und über ``max_value`` interpretiert. Erlaubt sind genau **zwei**
Auflösungen – ``HEIGHT_MAX_8BIT`` (Legacy-/Kompatibilitätspfad) und
``HEIGHT_MAX_16BIT`` (kanonischer Zielvertrag, echte 16-Bit-Präzision). Die
deterministische 8→16-Abbildung ist ``v16 = v8 × 257`` (Bit-Replikation,
:func:`expand_to_16bit`); die 16→8-Ansicht ``v8 = rint(v16 / 257)`` existiert
nur an benannten Quantisierungsgrenzen (:func:`height_to_layer`). Die Arrays
eines Feldes sind nach Konstruktion **unveränderlich** (Write-Lock), sodass
Kopien, History-Snapshots und Duplikate Referenzen gefahrlos teilen können.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

# Voller Wertebereich einer 8-Bit-Höhe (Legacy-/Kompatibilitätspfad).
HEIGHT_MAX_8BIT = 255

# Voller Wertebereich des kanonischen 16-Bit-Vertrags (ADR #586).
HEIGHT_MAX_16BIT = 65535

# Deterministische 8→16-Abbildung: ``257 = 0x0101 = 65535 / 255`` exakt; die
# Multiplikation entspricht der Bit-Replikation ``(v8 << 8) | v8`` und ist über
# ``v8 = rint(v16 / 257)`` verlustfrei rückrechenbar (ADR #586, Abschnitt 3).
_EXPAND_8_TO_16 = 257

# Whitelist der erlaubten Höhenauflösungen. Andere Werte lehnt
# ``HeightField.__post_init__`` hart ab – es gibt keine „krummen" Bittiefen im
# kanonischen Modellpfad (Verschärfung der früheren „nur positiv"-Prüfung).
_ALLOWED_MAX_VALUES = frozenset({HEIGHT_MAX_8BIT, HEIGHT_MAX_16BIT})

# Standard-Kanalgewichtung (Rec. 601 Luma): wahrnehmungsnahe Graustufe aus R/G/B.
# Die Summe ist 1.0, sodass die gewichtete Luminanz im Bereich 0..255 bleibt.
LUMA_WEIGHTS_REC601 = (0.299, 0.587, 0.114)


class HeightMapError(ValueError):
    """Fehler bei Höhen-Konvertierung, Normalisierung oder Größen-Validierung."""


@dataclass(frozen=True)
class HeightField:
    """Qt-freie Höhen-Repräsentation: ein 2D-Höhenfeld plus Deckungs-Alpha.

    ``values`` hält die Höhe je Pixel als ``uint16`` im Bereich ``0..max_value``
    (Form ``(H, W)``, ``0`` = niedrigste, ``max_value`` = höchste Stufe, **hell =
    hoch**); ``coverage`` ist die davon **orthogonale** Deckung als ``uint8``
    (``0..255``, gleiche Form): ``coverage == 0`` bedeutet „kein Material", der
    Höhenwert darunter bleibt erhalten (kein implizites Nullen). ``max_value``
    ist auf die Vertragswerte ``HEIGHT_MAX_8BIT`` (Legacy) und
    ``HEIGHT_MAX_16BIT`` (kanonisch, ADR #586) beschränkt.

    Die Invarianten (Form, dtype, Wertebereich, ``max_value``-Whitelist) werden
    beim Anlegen geprüft; danach ist das Feld unveränderlich: ``frozen`` plus
    **Write-Lock auf beiden Arrays**, damit Aliasing-Verstöße (in-place-Mutation
    geteilter Puffer, etwa aus History-Snapshots) hart fehlschlagen statt still
    Snapshots zu korrumpieren. Alle Operationen geben neue Felder zurück.
    Vergleich/Hashing über die – teuren – Pixelinhalte ist bewusst nicht
    vorgesehen.
    """

    values: np.ndarray
    coverage: np.ndarray
    max_value: int = HEIGHT_MAX_8BIT

    def __post_init__(self) -> None:
        if self.max_value not in _ALLOWED_MAX_VALUES:
            raise HeightMapError(
                f"max_value muss {HEIGHT_MAX_8BIT} oder {HEIGHT_MAX_16BIT} sein, "
                f"war {self.max_value}"
            )
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
        # Vertragsregel „Arrays sind nach Konstruktion unveränderlich" (ADR #586,
        # Abschnitt 5): Sichten auf fremde Puffer (``base``) würden trotz
        # Write-Lock über den Basis-Puffer mutierbar bleiben – solche Eingaben
        # werden deshalb in eigene Kopien überführt. Der anschließende
        # Write-Lock macht geteilte Referenzen (Duplicate, History-Pool)
        # beweisbar sicher – Schreibversuche werfen ValueError.
        if self.values.base is not None:
            object.__setattr__(self, "values", self.values.copy())
        if self.coverage.base is not None:
            object.__setattr__(self, "coverage", self.coverage.copy())
        self.values.setflags(write=False)
        self.coverage.setflags(write=False)

    @property
    def size(self) -> tuple[int, int]:
        """Größe als ``(width, height)`` – analog zu ``Layer.size``/``Project.size``."""
        h, w = self.values.shape[:2]
        return (w, h)


def scale_8bit_height_value(value: int, field: HeightField) -> int:
    """Skaliert einen bestehenden ``0..255``-UI-Wert auf ``field.max_value``.

    Diese explizite Adaptergrenze erhält die bisherige Reglersemantik, während
    Modell und Operationen direkt im kanonischen Wertebereich arbeiten.
    """
    if not 0 <= value <= HEIGHT_MAX_8BIT:
        raise HeightMapError(
            f"UI-Höhenwert {value} außerhalb 0..{HEIGHT_MAX_8BIT}"
        )
    return round(value * field.max_value / HEIGHT_MAX_8BIT)


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


# ── 16-Bit-Vertrag: Migration & Resize (#587) ────────────────────────────


def expand_to_16bit(field: HeightField) -> HeightField:
    """Hebt ein Legacy-8-Bit-Höhenfeld deterministisch auf den 16-Bit-Vertrag.

    Abbildung ``v16 = v8 × 257`` (ADR #586, Abschnitt 3): exakt, äquidistant,
    ``0 → 0`` und ``255 → 65535``, rückrechenbar über ``v8 = rint(v16 / 257)``
    – verlustfrei im Sinne der ursprünglichen 256 Stufen. Ein bereits
    kanonisches Feld (``max_value == HEIGHT_MAX_16BIT``) wird unverändert
    zurückgegeben (Identität, keine Kopie – Felder sind unveränderlich).
    Die Deckung wird unverändert übernommen (Referenz; Write-Lock schützt).
    """
    if field.max_value == HEIGHT_MAX_16BIT:
        return field
    values = (field.values.astype(np.uint32) * _EXPAND_8_TO_16).astype(np.uint16)
    return HeightField(values, field.coverage, HEIGHT_MAX_16BIT)


def resize_height_field(
    field: HeightField,
    width: int,
    height: int,
    *,
    resample: Image.Resampling = Image.Resampling.LANCZOS,
) -> HeightField:
    """Skaliert ein Höhenfeld präzisionserhaltend auf ``width × height``.

    Interpolations-/Maskenregel des ADR #586 (Abschnitt 4): die Höhenwerte
    laufen als ``float32``-Bild (PIL-Modus ``F``) durch **denselben**
    Resampling-Filter wie die COLOR-Ebenen und werden danach mit
    ``rint`` + ``clip`` auf ``0..max_value`` als ``uint16`` übernommen – ohne
    8-Bit-Zwischenschritt. Die Deckung wird separat als 8-Bit-``L``-Bild mit
    demselben Filter skaliert (identisch zur Alpha-Behandlung des
    RGBA-Resamplings); Höhenwerte unter ``coverage == 0`` nehmen normal an der
    Interpolation teil, das Randverhalten ist das des gewählten PIL-Filters.
    Gleiche Zielgröße gibt das Feld unverändert zurück (Identität).
    """
    if width <= 0 or height <= 0:
        raise HeightMapError(f"Zielgröße muss positiv sein, war {width}x{height}")
    if (width, height) == field.size:
        return field
    values_f = Image.fromarray(field.values.astype(np.float32), mode="F")
    resized = np.asarray(values_f.resize((width, height), resample), dtype=np.float64)
    values = np.clip(np.rint(resized), 0, field.max_value).astype(np.uint16)
    coverage_l = Image.fromarray(field.coverage, mode="L")
    coverage = np.array(coverage_l.resize((width, height), resample), dtype=np.uint8)
    return HeightField(values, coverage, field.max_value)


def rotate_height_field(field: HeightField, degrees: int) -> HeightField:
    """Dreht Höhe und Deckung ohne 8-Bit-Zwischenschritt.

    Rechtwinklige Drehungen sind bitgenaue Permutationen. Bei freien Winkeln
    verwendet der Helfer – analog zu :func:`bgremover.image_ops.rotate_image` –
    bikubische Interpolation; die Höhenwerte laufen dafür im exakt darstellbaren
    ``float32``-Bereich und werden erst am Ende gerundet und geklemmt. Die
    Deckung wird separat mit demselben Filter transformiert.
    """
    resample = (
        Image.Resampling.NEAREST
        if degrees % 90 == 0
        else Image.Resampling.BICUBIC
    )
    values_f = Image.fromarray(field.values.astype(np.float32), mode="F")
    rotated_values = np.asarray(
        values_f.rotate(degrees, expand=True, resample=resample),
        dtype=np.float64,
    )
    values = np.clip(
        np.rint(rotated_values), 0, field.max_value
    ).astype(np.uint16)
    coverage_l = Image.fromarray(field.coverage, mode="L")
    coverage = np.array(
        coverage_l.rotate(degrees, expand=True, resample=resample),
        dtype=np.uint8,
    )
    return HeightField(values, coverage, field.max_value)


def crop_height_field(
    field: HeightField,
    rect: tuple[int, int, int, int],
    *,
    is_circle: bool = False,
) -> HeightField:
    """Schneidet Höhe und Deckung präzisionserhaltend auf ``rect`` zu.

    Der rechteckige Zuschnitt ist eine reine Pixelkopie. Beim Kreiszuschnitt
    wird ausschließlich die orthogonale Deckung mit der Kreismaske begrenzt;
    die kanonischen Höhenwerte unter transparenten Pixeln bleiben erhalten.
    """
    x, y, width, height = rect
    if width <= 0 or height <= 0:
        raise HeightMapError(
            f"Zuschnittgröße muss positiv sein, war {width}x{height}"
        )
    box = (x, y, x + width, y + height)
    values_f = Image.fromarray(field.values.astype(np.float32), mode="F")
    values = np.asarray(values_f.crop(box), dtype=np.float64)
    values_u16 = np.clip(np.rint(values), 0, field.max_value).astype(np.uint16)
    coverage_l = Image.fromarray(field.coverage, mode="L").crop(box)
    coverage = np.array(coverage_l, dtype=np.uint8)
    if is_circle:
        mask = Image.new("L", (width, height), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, width - 1, height - 1], fill=255)
        coverage = np.minimum(coverage, np.asarray(mask)).astype(np.uint8)
    return HeightField(values_u16, coverage, field.max_value)


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
    if max_value not in _ALLOWED_MAX_VALUES:
        raise HeightMapError(
            f"max_value muss {HEIGHT_MAX_8BIT} oder {HEIGHT_MAX_16BIT} sein, "
            f"war {max_value}"
        )
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


# ── Editier-Operationen auf Höhenfeldern (#347) ──────────────────────────
# Reine, auswahlbewusste Höhenbearbeitung: alle Operationen geben ein **neues**
# Höhenfeld zurück (Eingabe bleibt unangetastet), klemmen auf ``0..max_value``
# und lassen die Deckung unverändert. Eine optionale boolesche ``mask`` (Form
# wie das Höhenfeld) begrenzt die Wirkung auf ihre True-Pixel; ``None`` wirkt
# global. So lassen sich die vorhandene Auswahl und ``project_history`` aus dem
# Canvas direkt wiederverwenden.


def _validate_mask(mask: np.ndarray, field: HeightField) -> None:
    """Stellt sicher, dass ``mask`` boolesch ist und zur Höhenfeld-Form passt."""
    if mask.shape != field.values.shape:
        raise HeightMapError(
            f"Maskenform {mask.shape} passt nicht zum Höhenfeld {field.values.shape}"
        )
    if mask.dtype != np.bool_:
        raise HeightMapError(f"Maske muss boolesch sein, war {mask.dtype}")


def adjust_height(
    field: HeightField, delta: int, *, mask: np.ndarray | None = None
) -> HeightField:
    """Hellt auf (``delta > 0``) oder dunkelt ab (``delta < 0``), geklemmt.

    Addiert ``delta`` auf die Höhe und klemmt auf ``0..max_value``; außerhalb der
    Maske bleiben die Werte unverändert. Die Rechnung läuft über ``int32``, damit
    Über-/Unterlauf vor dem Klemmen nicht den ``uint16``-Bereich umschlägt.
    """
    base = field.values.astype(np.int32)
    adjusted = np.clip(base + delta, 0, field.max_value)
    if mask is None:
        result = adjusted
    else:
        _validate_mask(mask, field)
        result = np.where(mask, adjusted, base)
    return HeightField(result.astype(np.uint16), field.coverage.copy(), field.max_value)


def set_height(
    field: HeightField, value: int, *, mask: np.ndarray | None = None
) -> HeightField:
    """Setzt die Höhe (innerhalb der Maske bzw. global) auf einen Festwert.

    ``value`` muss in ``0..max_value`` liegen, sonst :class:`HeightMapError`.
    """
    if not 0 <= value <= field.max_value:
        raise HeightMapError(f"Höhe {value} außerhalb 0..{field.max_value}")
    values = field.values.copy()
    if mask is None:
        values[...] = value
    else:
        _validate_mask(mask, field)
        values[mask] = value
    return HeightField(values, field.coverage.copy(), field.max_value)


def invert_height(
    field: HeightField, *, mask: np.ndarray | None = None
) -> HeightField:
    """Invertiert die Höhe (``max_value - Höhe``), global oder auf die Maske.

    Verlustfrei: zweimaliges Invertieren desselben Bereichs liefert exakt das
    Ausgangsfeld zurück.
    """
    inverted = (field.max_value - field.values.astype(np.int32)).astype(np.uint16)
    if mask is None:
        values = inverted
    else:
        _validate_mask(mask, field)
        values = np.where(mask, inverted, field.values).astype(np.uint16)
    return HeightField(values, field.coverage.copy(), field.max_value)


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
