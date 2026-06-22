"""Qt-freies EufyMake-Export-Datenmodell und Planungslogik (#352).

Fundament des EufyMake-Export-Epics (#351): ein rein deklaratives, strikt
getyptes Modell, das beschreibt, **welche Import-Assets BgRemover für EufyMake
Studio erzeugen würde** – ohne Pixel zu rendern, Dateien zu schreiben, Qt zu
ziehen oder eine vollständige Preflight-Prüfung durchzuführen (das ist #353/#354/
#355 vorbehalten). Konventionen analog ``project_model``/``height_map``: reine
Logik ohne Datei-/Netz-/Qt-Zugriffe, deutsche Docstrings, englische Identifier,
strikte mypy-Typisierung.

Die hier festgehaltenen Dateinamen, die Profilkennung und die Defaults sind
**BgRemover-Konventionen** und ausdrücklich *keine* offizielle EufyMake-
Spezifikation. Hintergrund, Quellenlage und offene Annahmen dokumentiert die ADR
``docs/history/ADR-2026-eufymake-exportpaket.md``. Gesichert ist allein die
Height-Semantik **hell = hoch / dunkel = niedrig**; unbekannt bleiben die von
EufyMake erwartete Bittiefe und eine etwaige Gloss-Masken-Semantik – beide werden
im Plan über :class:`OpenQuestion` bzw. ``ExportAsset.experimental`` *explizit*
markiert, statt sie stillschweigend als Herstellervertrag zu behandeln.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from bgremover.project_model import (
    META_BIT_DEPTH,
    META_PHYSICAL_SIZE_MM,
    LayerKind,
    LayerRole,
    Project,
)

# Profil-/Versionskennung des Pakets. **BgRemover-Konvention**, keine offizielle
# EufyMake-Kennung: trennt spätere Konventionsänderungen sauber vom Projektmodell
# und erlaubt #353–#355, gegen eine stabile Version zu planen.
EXPORT_PROFILE = "bgremover-eufymake-import"
EXPORT_PROFILE_VERSION = 1

# Kanonische, deterministische Asset-Dateinamen (BgRemover-Konvention). Bewusst
# verlustfreie PNGs; die logische Paketstruktur bleibt für Ordner *und* ZIP gleich.
_ASSET_FILENAMES: dict[LayerRole, str] = {
    LayerRole.COLOR_MOTIF: "color_motif.png",
    LayerRole.HEIGHT_MAP: "height_map.png",
    LayerRole.GLOSS_MASK: "gloss_mask.png",
}

# Standard-Bittiefe pro Kanal. 8 Bit ist der dokumentierte, konservative Default;
# 16 Bit bleibt als Hook für die (offiziell nicht bestätigte) Höhen-Tiefe möglich.
DEFAULT_BIT_DEPTH = 8
_SUPPORTED_BIT_DEPTHS = (8, 16)

# Reine Geometriekonstante für die DPI-Ableitung aus Pixel- und mm-Größe.
MM_PER_INCH = 25.4


class AssetPixelFormat(Enum):
    """Logisches Pixelformat eines Assets (PIL-Modus erst beim Rendern in #353)."""

    RGBA = "rgba"  # Farbe mit Alpha – Farbmotiv
    GRAYSCALE = "grayscale"  # einkanalige Graustufe – Höhenkarte / Gloss-Maske


class HeightSemantics(Enum):
    """Vertraglich fixierte Höhen-Interpretation einer Graustufenkarte."""

    LIGHT_IS_HIGH = "light_is_high"  # hell = hoch, dunkel = niedrig (offiziell belegt)


# Der eine, vertraglich garantierte Höhenkonventionswert. Modul, Plan und spätere
# Render-/UI-Schichten konsultieren ausschließlich diese Konstante (kein Drift).
HEIGHT_SEMANTICS = HeightSemantics.LIGHT_IS_HIGH


class OpenQuestion(Enum):
    """Explizit offene Annahmen, die *kein* bestätigter EufyMake-Vertrag sind.

    Werden im :class:`ExportPlan` mitgeführt, damit Folge-Issues und die spätere
    UI sie sichtbar machen können, statt sie als gesichert zu behandeln.
    """

    # Ob EufyMake Höhenkarten in 8 oder 16 Bit erwartet/nutzt, ist offiziell offen.
    HEIGHT_MAP_BIT_DEPTH = "height_map_bit_depth"
    # Schwarz/Weiß-Bedeutung bzw. Intensitäts-Semantik einer Gloss-Maske ist offen.
    GLOSS_MASK_SEMANTICS = "gloss_mask_semantics"
    # Native ``.empf``-Projekte werden bewusst nicht erzeugt (kein Reverse Engineering).
    NATIVE_EMPF_PROJECT = "native_empf_project"


class EufyMakeExportError(ValueError):
    """Basis aller strukturierten Fehler der Export-Planung."""


class MissingColorMotifError(EufyMakeExportError):
    """Das erforderliche Farbmotiv lässt sich aus dem Projekt nicht ableiten."""


class InvalidBitDepthError(EufyMakeExportError):
    """``META_BIT_DEPTH`` hält einen ungültigen Wert (kein 8/16-Bit-Integer)."""


class InvalidPhysicalSizeError(EufyMakeExportError):
    """``META_PHYSICAL_SIZE_MM`` hält keine gültige positive (Breite, Höhe) in mm."""


@dataclass(frozen=True)
class ExportAsset:
    """Ein geplantes Import-Asset des EufyMake-Pakets (rein deklarativ).

    ``role`` ist die abgebildete Ebenenrolle, ``filename`` der deterministische
    BgRemover-Dateiname. ``source_layer_id`` benennt die Quell-Ebene; für ein
    Farbmotiv ohne explizite ``COLOR_MOTIF``-Rolle ist es ``None`` und meint das
    **COLOR-Komposit** (siehe :attr:`from_color_composite`). ``required`` ist nur
    für das Farbmotiv ``True``; ``experimental`` markiert Assets mit offener
    Semantik (Gloss-Maske). Es werden hier **keine Pixel** gehalten – das Rendern
    übernimmt #353.
    """

    role: LayerRole
    filename: str
    pixel_format: AssetPixelFormat
    bit_depth: int
    required: bool
    source_layer_id: str | None
    experimental: bool = False

    @property
    def from_color_composite(self) -> bool:
        """True, wenn das Farbmotiv aus dem COLOR-Komposit statt einer Rolle stammt."""
        return self.role is LayerRole.COLOR_MOTIF and self.source_layer_id is None


@dataclass(frozen=True)
class ExportTarget:
    """Aus Projektmetadaten bzw. dokumentierten Defaults abgeleitete Zielparameter.

    ``pixel_size`` ist die Canvas-Pixelgröße ``(width, height)``. ``physical_size_mm``
    stammt aus ``META_PHYSICAL_SIZE_MM`` (sonst ``None``). ``dpi`` wird nur
    abgeleitet, wenn die physische Größe vorliegt; sonst ``None``. ``bit_depth``
    folgt ``META_BIT_DEPTH`` (Default :data:`DEFAULT_BIT_DEPTH`).
    """

    pixel_size: tuple[int, int]
    bit_depth: int
    physical_size_mm: tuple[float, float] | None
    dpi: tuple[float, float] | None


@dataclass(frozen=True)
class ExportPlan:
    """Deterministischer Export-Plan: Profil, Zielparameter, Assets, offene Punkte.

    Die ``assets`` sind in stabiler Reihenfolge (Farbmotiv, Höhenkarte,
    Gloss-Maske – jeweils nur sofern vorhanden) abgelegt; das Farbmotiv ist
    garantiert enthalten. ``height_semantics`` hält die vertraglich fixierte
    Höhen-Interpretation, ``open_questions`` die explizit offenen Annahmen.
    """

    profile: str
    profile_version: int
    target: ExportTarget
    assets: tuple[ExportAsset, ...]
    height_semantics: HeightSemantics
    open_questions: tuple[OpenQuestion, ...]

    def asset_for(self, role: LayerRole) -> ExportAsset | None:
        """Geplantes Asset zur Rolle oder ``None``, falls nicht im Paket."""
        for asset in self.assets:
            if asset.role is role:
                return asset
        return None

    @property
    def color_motif(self) -> ExportAsset:
        """Das stets vorhandene, erforderliche Farbmotiv-Asset."""
        asset = self.asset_for(LayerRole.COLOR_MOTIF)
        if asset is None:  # pragma: no cover - durch build_export_plan garantiert
            raise MissingColorMotifError("ExportPlan ohne Farbmotiv")
        return asset

    @property
    def optional_assets(self) -> tuple[ExportAsset, ...]:
        """Alle nicht erforderlichen Assets (Höhenkarte/Gloss-Maske) im Paket."""
        return tuple(asset for asset in self.assets if not asset.required)

    @property
    def filenames(self) -> tuple[str, ...]:
        """Deterministische Dateinamen aller geplanten Assets in Paketreihenfolge."""
        return tuple(asset.filename for asset in self.assets)


def _derive_bit_depth(metadata: dict[str, object]) -> int:
    """Liest ``META_BIT_DEPTH`` strukturiert aus oder fällt auf den Default zurück.

    Fehlt der Schlüssel, gilt :data:`DEFAULT_BIT_DEPTH`. Ein vorhandener Wert muss
    ein Integer aus :data:`_SUPPORTED_BIT_DEPTHS` sein (``bool`` ist als
    Integer-Subtyp ausgeschlossen); sonst :class:`InvalidBitDepthError` – keine
    stille Korrektur.
    """
    raw = metadata.get(META_BIT_DEPTH)
    if raw is None:
        return DEFAULT_BIT_DEPTH
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise InvalidBitDepthError(f"{META_BIT_DEPTH} muss ein Integer sein, war {raw!r}")
    if raw not in _SUPPORTED_BIT_DEPTHS:
        raise InvalidBitDepthError(
            f"{META_BIT_DEPTH} muss in {_SUPPORTED_BIT_DEPTHS} liegen, war {raw}"
        )
    return raw


def _derive_physical_size(metadata: dict[str, object]) -> tuple[float, float] | None:
    """Liest ``META_PHYSICAL_SIZE_MM`` strukturiert als positive ``(w, h)`` in mm.

    Fehlt der Schlüssel, bleibt die physische Größe unbekannt (``None``). Ein
    vorhandener Wert muss eine Zweier-Sequenz endlicher, positiver Zahlen sein
    (``bool`` ausgeschlossen); sonst :class:`InvalidPhysicalSizeError`.
    """
    raw = metadata.get(META_PHYSICAL_SIZE_MM)
    if raw is None:
        return None
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence) or len(raw) != 2:
        raise InvalidPhysicalSizeError(
            f"{META_PHYSICAL_SIZE_MM} muss (Breite, Höhe) in mm sein, war {raw!r}"
        )
    dims: list[float] = []
    for value in raw:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InvalidPhysicalSizeError(
                f"{META_PHYSICAL_SIZE_MM} braucht Zahlen, war {raw!r}"
            )
        number = float(value)
        if not math.isfinite(number) or number <= 0.0:
            raise InvalidPhysicalSizeError(
                f"{META_PHYSICAL_SIZE_MM} muss endlich und positiv sein, war {raw!r}"
            )
        dims.append(number)
    return (dims[0], dims[1])


def _derive_dpi(
    pixel_size: tuple[int, int], physical_size_mm: tuple[float, float] | None
) -> tuple[float, float] | None:
    """Leitet die Auflösung (DPI) aus Pixel- und physischer mm-Größe ab.

    Nur wenn beide Angaben vorliegen, sonst ``None`` (keine erfundene Auflösung).
    ``dpi = px / (mm / 25.4)`` je Achse.
    """
    if physical_size_mm is None:
        return None
    px_w, px_h = pixel_size
    mm_w, mm_h = physical_size_mm
    return (px_w * MM_PER_INCH / mm_w, px_h * MM_PER_INCH / mm_h)


def _derive_target(project: Project) -> ExportTarget:
    """Baut die :class:`ExportTarget`-Parameter reproduzierbar aus dem Projekt."""
    bit_depth = _derive_bit_depth(project.metadata)
    physical_size = _derive_physical_size(project.metadata)
    dpi = _derive_dpi(project.size, physical_size)
    return ExportTarget(
        pixel_size=project.size,
        bit_depth=bit_depth,
        physical_size_mm=physical_size,
        dpi=dpi,
    )


def _plan_color_motif(project: Project) -> ExportAsset:
    """Plant das **erforderliche** Farbmotiv aus Rolle oder COLOR-Komposit.

    Trägt eine Ebene die Rolle ``COLOR_MOTIF``, ist sie die explizite Quelle.
    Sonst dient das Komposit aller COLOR-Ebenen als Quelle (``source_layer_id``
    ``None``). Gibt es weder eine ``COLOR_MOTIF``-Rolle noch irgendeine
    COLOR-Ebene, lässt sich kein Farbmotiv ableiten → :class:`MissingColorMotifError`.
    Das Farbmotiv bleibt konservativ 8-Bit-RGBA, unabhängig von ``META_BIT_DEPTH``.
    """
    role_layer = project.layer_by_role(LayerRole.COLOR_MOTIF)
    if role_layer is not None:
        source_id: str | None = role_layer.id
    elif any(layer.kind is LayerKind.COLOR for layer in project.layers):
        source_id = None
    else:
        raise MissingColorMotifError(
            "Kein Farbmotiv: weder eine COLOR_MOTIF-Rolle noch eine COLOR-Ebene vorhanden"
        )
    return ExportAsset(
        role=LayerRole.COLOR_MOTIF,
        filename=_ASSET_FILENAMES[LayerRole.COLOR_MOTIF],
        pixel_format=AssetPixelFormat.RGBA,
        bit_depth=DEFAULT_BIT_DEPTH,
        required=True,
        source_layer_id=source_id,
    )


def build_export_plan(project: Project) -> ExportPlan:
    """Bildet ein :class:`Project` deterministisch auf einen :class:`ExportPlan` ab.

    Rollen→Assets: ``COLOR_MOTIF`` ergibt das **erforderliche** Farbmotiv (RGBA,
    8 Bit), ``HEIGHT_MAP`` und ``GLOSS_MASK`` jeweils ein **optionales**
    Graustufen-Asset – Letzteres ``experimental`` wegen offener Gloss-Semantik.
    Die Höhenkarte erbt die geplante Bittiefe aus ``META_BIT_DEPTH`` (8/16), die
    Gloss-Maske bleibt konservativ 8-Bit. Zielparameter (Pixelgröße, physische
    Größe, DPI, Bittiefe) werden reproduzierbar aus den Projektmetadaten bzw.
    dokumentierten Defaults abgeleitet; ungültige Metadaten werfen strukturierte
    Fehler (:class:`EufyMakeExportError`-Subtypen). Es wird **kein** natives
    ``.empf`` geplant.
    """
    target = _derive_target(project)

    assets: list[ExportAsset] = [_plan_color_motif(project)]
    open_questions: list[OpenQuestion] = [OpenQuestion.NATIVE_EMPF_PROJECT]

    height_layer = project.layer_by_role(LayerRole.HEIGHT_MAP)
    if height_layer is not None:
        assets.append(
            ExportAsset(
                role=LayerRole.HEIGHT_MAP,
                filename=_ASSET_FILENAMES[LayerRole.HEIGHT_MAP],
                pixel_format=AssetPixelFormat.GRAYSCALE,
                bit_depth=target.bit_depth,
                required=False,
                source_layer_id=height_layer.id,
            )
        )
        open_questions.append(OpenQuestion.HEIGHT_MAP_BIT_DEPTH)

    gloss_layer = project.layer_by_role(LayerRole.GLOSS_MASK)
    if gloss_layer is not None:
        assets.append(
            ExportAsset(
                role=LayerRole.GLOSS_MASK,
                filename=_ASSET_FILENAMES[LayerRole.GLOSS_MASK],
                pixel_format=AssetPixelFormat.GRAYSCALE,
                bit_depth=DEFAULT_BIT_DEPTH,
                required=False,
                source_layer_id=gloss_layer.id,
                experimental=True,
            )
        )
        open_questions.append(OpenQuestion.GLOSS_MASK_SEMANTICS)

    return ExportPlan(
        profile=EXPORT_PROFILE,
        profile_version=EXPORT_PROFILE_VERSION,
        target=target,
        assets=tuple(assets),
        height_semantics=HEIGHT_SEMANTICS,
        open_questions=tuple(open_questions),
    )
