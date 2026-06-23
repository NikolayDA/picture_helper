"""Qt-freies Domänenmodell für Mehr-Ebenen-Projekte.

Dieses Modul ist die *Keystone* des Projekt-/Ebenen-Datenmodells (#329): ein
reines, strikt getyptes Modell aus :class:`Project` und :class:`Layer` ganz ohne
Qt-, Render-, Persistenz- oder History-Anbindung. Alle Operationen sind frei von
Seiteneffekten außerhalb des Modells (keine Datei-/Netz-/Qt-Zugriffe) und
arbeiten direkt auf den gehaltenen Pillow-Bildern. Konventionen analog
``image_ops``/``image_utils``: reine Logik, deutsche Docstrings, englische
Identifier, strikte mypy-Typisierung.

Invarianten:

- Die Ebenenliste ist **geordnet**: Index 0 ist die *unterste*, der letzte Index
  die *oberste* Ebene. Das Farb-Komposit zeichnet von unten nach oben.
- Ein **nicht-leeres** Projekt hat genau eine aktive Ebene; ein leeres Projekt
  hat keine (``active_layer_id is None``).
- Jede Ebene führt RGBA-Pixeldaten in **Canvas-Größe**; abweichende Größen werden
  beim Einfügen abgelehnt.
- Eine **Rolle** ist projektweit eindeutig: höchstens eine Ebene je Rolle.
- Operationen auf einer unbekannten Ebenen-ID werfen :class:`LayerNotFoundError`.
"""
from __future__ import annotations

import uuid
from collections.abc import Iterable, Iterator
from enum import Enum
from typing import Any

import numpy as np
from PIL import Image

# ``image_ops`` ist seit dem #359-Review import-zeitlich Qt-frei (lazy ``numpy_to_pil``),
# daher kann das Domänenmodell die reine ``resize_image``-Primitive direkt nutzen,
# ohne PyQt6 einzuziehen – ``Project.resize`` bleibt headless aufrufbar.
from bgremover.height_map import layer_to_gray_image
from bgremover.image_ops import resize_image
from bgremover.units import dpi_for_size, parse_size_mm, size_mm_for_dpi

# Aktuelle Modellversion. Eigener Schlüssel mit Migrationshaken folgt mit dem
# Dateiformat (#333), Muster wie ``settings_schema``.
PROJECT_VERSION = 1

# Schlüssel in ``Project.metadata`` für die maßgenaue Ausgabe (#329/#376):
# ``META_PHYSICAL_SIZE_MM`` hält die validierte physische Zielgröße ``(w, h)`` in
# mm (siehe :attr:`Project.physical_size_mm`/:meth:`Project.set_physical_size_mm`);
# die DPI ergeben sich daraus zusammen mit der Pixelgröße und werden nicht separat
# gespeichert (kein Drift). ``META_BIT_DEPTH`` bleibt für die Bittiefe reserviert –
# das Modell wertet sie selbst nicht aus.
META_BIT_DEPTH = "bit_depth"
META_PHYSICAL_SIZE_MM = "physical_size_mm"


class LayerKind(Enum):
    """Fachliche Art einer Ebene.

    Nur ``COLOR`` fließt ins Farb-Komposit; ``HEIGHT``/``GLOSS`` sind
    Daten-Ebenen für spätere UV-Druck-Features, ``GENERIC`` ein neutraler
    Auffangtyp.
    """

    COLOR = "color"
    HEIGHT = "height"
    GLOSS = "gloss"
    GENERIC = "generic"


class LayerRole(Enum):
    """Optionale, projektweit eindeutige Rolle einer Ebene."""

    COLOR_MOTIF = "color_motif"
    HEIGHT_MAP = "height_map"
    GLOSS_MASK = "gloss_mask"


class ProjectModelError(Exception):
    """Basisklasse aller Fehler des Domänenmodells."""


class LayerNotFoundError(ProjectModelError):
    """Eine Ebenen-ID ist im Projekt unbekannt."""


class IncompatibleRoleError(ProjectModelError):
    """Eine Rolle ist mit dem Ebenen-Typ unvereinbar (siehe :func:`role_allowed_for_kind`)."""


# Zentrale, Qt-freie Kompatibilitätsregel zwischen Ebenen-Typ und -Rolle (#364):
# verbindlicher Vertrag des Höhen-Kontexts. Eine Ebene ist *genau dann*
# höhenfähig, wenn ``kind is LayerKind.HEIGHT``; ``LayerRole.HEIGHT_MAP`` darf
# daher ausschließlich auf einer HEIGHT-Ebene liegen und markiert dort die
# projektweit relevante Height Map (z. B. für Export und automatische Auswahl).
# Diese eine Regel verhindert Drift zwischen Modell, Persistenz, UI und Canvas;
# bewusst wird nur der HEIGHT_MAP↔HEIGHT-Vertrag erzwungen – übrige Rollen
# bleiben (noch) typunabhängig (Scope #364).
_ROLE_REQUIRED_KIND: dict[LayerRole, LayerKind] = {
    LayerRole.HEIGHT_MAP: LayerKind.HEIGHT,
}


def role_allowed_for_kind(role: LayerRole | None, kind: LayerKind) -> bool:
    """True, wenn ``role`` auf einer Ebene vom Typ ``kind`` liegen darf.

    ``None`` (keine Rolle) ist immer zulässig. Sonst greift die zentrale Tabelle
    ``_ROLE_REQUIRED_KIND``: eine eingeschränkte Rolle ist nur auf dem
    geforderten Typ erlaubt, alle übrigen Rollen sind typunabhängig. Modell, UI
    und Canvas konsultieren ausschließlich diese Funktion, damit der Vertrag an
    einer einzigen Stelle definiert bleibt.
    """
    if role is None:
        return True
    required = _ROLE_REQUIRED_KIND.get(role)
    return required is None or required is kind


def _ensure_rgba(image: Image.Image | np.ndarray) -> Image.Image:
    """Normalisiert Eingabe-Pixeldaten auf eine **eigenständige** RGBA-``Image``.

    Akzeptiert ein Pillow-Bild (beliebiger Modus) oder ein RGBA-numpy-Array. Das
    Ergebnis ist immer eine eigene Kopie in RGBA: ``Image.fromarray`` (via
    ``astype``) und ``convert`` liefern bereits neue Objekte, der bereits-RGBA-
    Fall kopiert explizit. So besitzt jede Ebene ihre Pixeldaten allein –
    spätere In-place-Änderungen am übergebenen Bild (``putpixel``/``paste``/
    ``resize`` …) erreichen weder Projekt noch Komposit und können die
    Canvas-Größen-Invariante nicht nachträglich verletzen. Garantierte RGBA-Daten
    machen das Komposit (``Image.alpha_composite``) zudem ohne Sonderfälle korrekt.
    """
    if isinstance(image, np.ndarray):
        return Image.fromarray(image.astype(np.uint8), "RGBA")
    if image.mode != "RGBA":
        return image.convert("RGBA")
    return image.copy()


def _validate_opacity(opacity: float) -> float:
    """Stellt sicher, dass ``opacity`` in ``[0.0, 1.0]`` liegt."""
    if not 0.0 <= opacity <= 1.0:
        raise ValueError(f"opacity muss in [0.0, 1.0] liegen, war {opacity!r}")
    return opacity


def _scale_alpha(image: Image.Image, opacity: float) -> Image.Image:
    """Gibt ``image`` mit um ``opacity`` skaliertem Alphakanal zurück."""
    arr = np.array(image, dtype=np.uint8)
    arr[:, :, 3] = np.rint(arr[:, :, 3].astype(np.float32) * opacity).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


class Layer:
    """Eine einzelne Bild-Ebene mit stabiler ID und RGBA-Pixeldaten.

    ``image`` akzeptiert ein Pillow-Bild *oder* ein RGBA-numpy-Array und wird
    stets als **eigenständige** RGBA-Kopie gehalten (siehe :func:`_ensure_rgba`);
    so können typisierte Bildverarbeitungsmodule numpy-Puffer ohne
    ``# type: ignore`` übergeben. ``opacity`` liegt in ``[0.0, 1.0]``. Eine
    optionale ``role`` ist projektweit eindeutig (siehe :class:`Project`). ``id``
    bleibt stabil; ohne Angabe wird eine UUID erzeugt. Ebenen werden per Identität
    verglichen, nicht über die – teuren und mehrdeutigen – Pixelinhalte.
    """

    def __init__(
        self,
        name: str,
        kind: LayerKind,
        image: Image.Image | np.ndarray,
        id: str | None = None,
        visible: bool = True,
        opacity: float = 1.0,
        locked: bool = False,
        role: LayerRole | None = None,
    ) -> None:
        if not role_allowed_for_kind(role, kind):
            raise IncompatibleRoleError(
                f"Rolle {role} ist mit Ebenen-Typ {kind} unvereinbar"
            )
        self.name = name
        self.kind = kind
        self.image = _ensure_rgba(image)
        self.id = id if id is not None else uuid.uuid4().hex
        self.visible = visible
        self.opacity = _validate_opacity(opacity)
        self.locked = locked
        self.role = role

    @property
    def size(self) -> tuple[int, int]:
        """Pixelgröße der Ebene als ``(width, height)``."""
        return self.image.size


class Project:
    """Geordnetes Mehr-Ebenen-Projekt fester Canvas-Größe.

    Hält die geordnete Ebenenliste, die aktive Ebene und ein freies
    ``metadata``-Dict. Alle Mutatoren erhalten die in der Modul-Doku genannten
    Invarianten; Lesezugriffe geben unveränderliche Sichten zurück.
    """

    def __init__(
        self,
        width: int,
        height: int,
        *,
        version: int = PROJECT_VERSION,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError(f"Canvas-Größe muss positiv sein, war {width}x{height}")
        self.width = width
        self.height = height
        self.version = version
        # Defensive Kopie: spätere Mutationen am übergebenen Dict dürfen das
        # Projekt nicht heimlich verändern.
        self.metadata: dict[str, Any] = dict(metadata) if metadata else {}
        self._layers: list[Layer] = []
        self._active_layer_id: str | None = None

    # ── Lesezugriffe ────────────────────────────────────────────────────
    @property
    def size(self) -> tuple[int, int]:
        """Canvas-Größe als ``(width, height)``."""
        return (self.width, self.height)

    @property
    def layers(self) -> tuple[Layer, ...]:
        """Ebenen von unten (Index 0) nach oben – unveränderliche Sicht."""
        return tuple(self._layers)

    @property
    def active_layer_id(self) -> str | None:
        return self._active_layer_id

    def __len__(self) -> int:
        return len(self._layers)

    def __iter__(self) -> Iterator[Layer]:
        return iter(self._layers)

    def has_layer(self, layer_id: str) -> bool:
        return any(layer.id == layer_id for layer in self._layers)

    def index_of(self, layer_id: str) -> int:
        """Listenindex (von unten) einer Ebene; wirft sonst ``LayerNotFoundError``."""
        for i, layer in enumerate(self._layers):
            if layer.id == layer_id:
                return i
        raise LayerNotFoundError(layer_id)

    def layer_by_id(self, layer_id: str) -> Layer:
        return self._layers[self.index_of(layer_id)]

    def active_layer(self) -> Layer | None:
        """Aktive Ebene oder ``None`` bei leerem Projekt."""
        if self._active_layer_id is None:
            return None
        return self.layer_by_id(self._active_layer_id)

    def layer_by_role(self, role: LayerRole) -> Layer | None:
        """Ebene mit der gegebenen Rolle oder ``None``."""
        for layer in self._layers:
            if layer.role is role:
                return layer
        return None

    # ── Ebenen-Operationen ──────────────────────────────────────────────
    def add_layer(
        self,
        layer: Layer,
        *,
        index: int | None = None,
        make_active: bool = True,
    ) -> Layer:
        """Fügt ``layer`` ein (Standard: ganz oben) und gibt sie zurück.

        ``index`` zählt von unten (0) nach oben; ``None`` hängt oben an. Die
        Ebene muss Canvas-Größe haben sowie eine projektweit eindeutige ID und
        Rolle tragen. Das *erste* Einfügen aktiviert die Ebene zwingend –
        ``make_active=False`` greift nur, solange bereits eine aktive Ebene
        existiert (Invariante: nicht-leeres Projekt hat genau eine aktive Ebene).
        """
        if self.has_layer(layer.id):
            raise ProjectModelError(f"Ebenen-ID bereits vergeben: {layer.id!r}")
        if layer.size != self.size:
            raise ValueError(
                f"Ebenengröße {layer.size} passt nicht zur Canvas-Größe {self.size}"
            )
        if layer.role is not None and self.layer_by_role(layer.role) is not None:
            raise ProjectModelError(f"Rolle bereits vergeben: {layer.role}")
        if index is None:
            pos = len(self._layers)
        elif 0 <= index <= len(self._layers):
            pos = index
        else:
            raise IndexError(f"index {index} außerhalb [0, {len(self._layers)}]")
        self._layers.insert(pos, layer)
        if make_active or self._active_layer_id is None:
            self._active_layer_id = layer.id
        return layer

    def create_layer(
        self,
        image: Image.Image,
        *,
        name: str,
        kind: LayerKind = LayerKind.COLOR,
        index: int | None = None,
        make_active: bool = True,
        visible: bool = True,
        opacity: float = 1.0,
        locked: bool = False,
        role: LayerRole | None = None,
    ) -> Layer:
        """Baut eine Ebene mit frischer ID und fügt sie via :meth:`add_layer` ein."""
        layer = Layer(
            name=name,
            kind=kind,
            image=image,
            visible=visible,
            opacity=opacity,
            locked=locked,
            role=role,
        )
        return self.add_layer(layer, index=index, make_active=make_active)

    def remove_layer(self, layer_id: str) -> Layer:
        """Entfernt eine Ebene und gibt sie zurück.

        War sie aktiv, rückt die Ebene an gleicher Position nach (bzw. die neue
        oberste); beim Entfernen der letzten Ebene wird ``active_layer_id`` zu
        ``None``.
        """
        idx = self.index_of(layer_id)
        removed = self._layers.pop(idx)
        if self._active_layer_id == removed.id:
            if self._layers:
                self._active_layer_id = self._layers[min(idx, len(self._layers) - 1)].id
            else:
                self._active_layer_id = None
        return removed

    def move_layer(self, layer_id: str, new_index: int) -> None:
        """Verschiebt eine Ebene an ``new_index`` (gezählt von unten)."""
        idx = self.index_of(layer_id)
        if not 0 <= new_index < len(self._layers):
            raise IndexError(
                f"new_index {new_index} außerhalb [0, {len(self._layers) - 1}]"
            )
        layer = self._layers.pop(idx)
        self._layers.insert(new_index, layer)

    def reorder(self, ordered_ids: Iterable[str]) -> None:
        """Setzt die komplette Reihenfolge anhand einer ID-Permutation.

        ``ordered_ids`` muss exakt die vorhandenen IDs enthalten (Permutation),
        sonst ``ProjectModelError`` – ein Schutz gegen versehentliches Verlieren
        oder Duplizieren von Ebenen.
        """
        ids = list(ordered_ids)
        current = [layer.id for layer in self._layers]
        if sorted(ids) != sorted(current):
            raise ProjectModelError(
                "reorder erwartet genau die vorhandenen Ebenen-IDs als Permutation"
            )
        by_id = {layer.id: layer for layer in self._layers}
        self._layers = [by_id[i] for i in ids]

    def duplicate_layer(self, layer_id: str, *, make_active: bool = True) -> Layer:
        """Dupliziert eine Ebene (tiefe Bildkopie) direkt darüber.

        Die Kopie erhält eine neue ID, einen abgeleiteten Namen und **keine**
        Rolle (Rollen sind eindeutig). ``Layer`` kopiert die Bilddaten beim
        Anlegen ohnehin, sodass Bearbeitungen der einen Ebene die andere nicht
        beeinflussen.
        """
        src = self.layer_by_id(layer_id)
        idx = self.index_of(layer_id)
        clone = Layer(
            name=f"{src.name} Kopie",
            kind=src.kind,
            image=src.image,
            visible=src.visible,
            opacity=src.opacity,
            locked=src.locked,
            role=None,
        )
        return self.add_layer(clone, index=idx + 1, make_active=make_active)

    def rename_layer(self, layer_id: str, name: str) -> None:
        self.layer_by_id(layer_id).name = name

    # ── Zustands-Operationen ────────────────────────────────────────────
    def set_active(self, layer_id: str) -> None:
        self._active_layer_id = self.layer_by_id(layer_id).id

    def set_visible(self, layer_id: str, visible: bool) -> None:
        self.layer_by_id(layer_id).visible = visible

    def set_opacity(self, layer_id: str, opacity: float) -> None:
        self.layer_by_id(layer_id).opacity = _validate_opacity(opacity)

    def set_locked(self, layer_id: str, locked: bool) -> None:
        self.layer_by_id(layer_id).locked = locked

    def assign_role(self, layer_id: str, role: LayerRole) -> None:
        """Weist ``role`` zu und entzieht sie ggf. der bisherigen Trägerin.

        Da eine Rolle projektweit eindeutig ist, wird sie effektiv *übertragen*:
        hielt eine andere Ebene die Rolle, verliert sie diese. Ist ``role`` mit
        dem Typ der Zielebene unvereinbar (siehe :func:`role_allowed_for_kind`),
        wird sie mit :class:`IncompatibleRoleError` abgelehnt – ohne das Projekt
        zu verändern.
        """
        layer = self.layer_by_id(layer_id)
        if not role_allowed_for_kind(role, layer.kind):
            raise IncompatibleRoleError(
                f"Rolle {role} ist mit Ebenen-Typ {layer.kind} unvereinbar"
            )
        holder = self.layer_by_role(role)
        if holder is not None and holder.id != layer.id:
            holder.role = None
        layer.role = role

    def clear_role(self, layer_id: str) -> None:
        self.layer_by_id(layer_id).role = None

    # ── Physische Zielgröße / Auflösung (mm/DPI) ────────────────────────
    @property
    def physical_size_mm(self) -> tuple[float, float] | None:
        """Physische Zielgröße ``(Breite, Höhe)`` in mm oder ``None`` (Schlüssel fehlt).

        **Nur ein fehlender Schlüssel** bedeutet „nicht gesetzt". Ein *vorhandener*
        Wert – auch ein explizites ``None`` aus einem korrupten Manifest – wird über
        :func:`bgremover.units.parse_size_mm` validiert (akzeptiert auch eine aus
        JSON geladene Liste) und löst bei Ungültigkeit
        :class:`bgremover.units.InvalidLengthError` aus, statt still als „nicht
        gesetzt" durchzurutschen. :meth:`clear_physical_size` entfernt den Schlüssel
        ganz.
        """
        if META_PHYSICAL_SIZE_MM not in self.metadata:
            return None
        return parse_size_mm(self.metadata[META_PHYSICAL_SIZE_MM])

    def set_physical_size_mm(self, width_mm: float, height_mm: float) -> None:
        """Setzt die physische Zielgröße (mm) validiert in ``META_PHYSICAL_SIZE_MM``.

        ``width_mm``/``height_mm`` müssen endlich und positiv sein; sonst
        :class:`bgremover.units.InvalidLengthError` (keine stille Korrektur). Die
        DPI ergeben sich daraus zusammen mit der Pixelgröße (siehe :attr:`dpi`).
        """
        self.metadata[META_PHYSICAL_SIZE_MM] = parse_size_mm((width_mm, height_mm))

    def clear_physical_size(self) -> None:
        """Entfernt physische Zielgröße und damit die abgeleitete DPI."""
        self.metadata.pop(META_PHYSICAL_SIZE_MM, None)

    @property
    def dpi(self) -> tuple[float, float] | None:
        """Auflösung ``(x, y)`` in DPI, abgeleitet aus Pixel- und physischer Größe.

        ``None``, solange keine physische Größe gesetzt ist (keine erfundene
        Auflösung). Single Source of Truth bleibt die physische Größe (mm); die
        DPI ist nur die abgeleitete Sicht über die aktuelle Pixelgröße und kann so
        nicht von der Canvas-Größe driften.
        """
        physical = self.physical_size_mm
        if physical is None:
            return None
        return dpi_for_size(self.size, physical)

    def set_dpi(self, dpi_x: float, dpi_y: float | None = None) -> None:
        """Setzt die Zielauflösung (DPI) und legt die implizierte physische Größe ab.

        ``dpi_y`` ist standardmäßig ``dpi_x`` (uniforme Auflösung). Die Werte
        müssen endlich und positiv sein; sonst
        :class:`bgremover.units.InvalidResolutionError`. Da die physische Größe
        (mm) die kanonische Größe ist, wird sie aus Pixelgröße und DPI berechnet
        und in ``META_PHYSICAL_SIZE_MM`` gespeichert; :attr:`dpi` liest sie
        anschließend deterministisch zurück.
        """
        resolution = (dpi_x, dpi_x if dpi_y is None else dpi_y)
        self.metadata[META_PHYSICAL_SIZE_MM] = size_mm_for_dpi(self.size, resolution)

    # ── Geometrie ───────────────────────────────────────────────────────
    def resize(
        self,
        width: int,
        height: int,
        *,
        resample: Image.Resampling = Image.Resampling.LANCZOS,
    ) -> None:
        """Resampelt **alle** Ebenen und die Canvas-Größe auf ``(width, height)``.

        Hält die Invariante „jede Ebene in Canvas-Größe": jede Ebene wird mit
        demselben *resample*-Verfahren skaliert, sodass das Farb-Komposit
        deckungsgleich bleibt. ``COLOR``-/Daten-Ebenen laufen direkt über das
        Resampling; eine ``HEIGHT``-Ebene wird zusätzlich über die
        Höhen-Repräsentation normalisiert (``R==G==B==Höhe`` bleibt erhalten –
        verlustfrei für 8 Bit, robust für die spätere 16-Bit-Erweiterung).

        Gleiche Zielgröße ist ein **No-op**. Die reservierte physische Zielgröße
        (``META_PHYSICAL_SIZE_MM``) bleibt bewusst unangetastet: dies ist ein
        reines Pixel-Resampling; mm/DPI-Editing ist späteren Rängen vorbehalten.
        """
        if width <= 0 or height <= 0:
            raise ValueError(f"Canvas-Größe muss positiv sein, war {width}x{height}")
        if (width, height) == self.size:
            return
        for layer in self._layers:
            resized = resize_image(layer.image, width, height, resample=resample)
            if layer.kind is LayerKind.HEIGHT:
                resized = layer_to_gray_image(resized)
            layer.image = resized
        self.width = width
        self.height = height

    # ── Komposit ────────────────────────────────────────────────────────
    def composite_color(self) -> Image.Image:
        """Rechnet die sichtbaren ``COLOR``-Ebenen zu einem RGBA-Bild zusammen.

        Gezeichnet wird von unten nach oben mit „over"-Alpha-Blending und
        Pro-Ebene-Opazität. Unsichtbare Ebenen, Opazität ``0`` sowie alle
        Nicht-``COLOR``-Ebenen (Daten-Ebenen ``HEIGHT``/``GLOSS``/``GENERIC``)
        bleiben außen vor. Das Ergebnis hat immer Canvas-Größe; ohne beitragende
        Ebene ist es vollständig transparent.
        """
        base = Image.new("RGBA", self.size, (0, 0, 0, 0))
        for layer in self._layers:
            if layer.kind is not LayerKind.COLOR or not layer.visible:
                continue
            if layer.opacity <= 0.0:
                continue
            top = (
                layer.image
                if layer.opacity >= 1.0
                else _scale_alpha(layer.image, layer.opacity)
            )
            base = Image.alpha_composite(base, top)
        return base
