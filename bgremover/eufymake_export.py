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

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from bgremover.eufymake_profile import (
    DEFAULT_TARGET_PROFILE,
    AssetPixelFormat,
    EufyMakeTargetProfile,
    HeightSemantics,
    ProfileRegistry,
)
from bgremover.project_model import (
    META_BIT_DEPTH,
    META_PHYSICAL_SIZE_MM,
    LayerKind,
    LayerRole,
    Project,
)
from bgremover.units import MM_PER_INCH as MM_PER_INCH  # Re-Export (Rückwärtskompat.)
from bgremover.units import UnitsError

# Rückwärtskompatible Re-Exports. Quelle ist ausschließlich das versionierte
# Zielprofil; der konservative HEIGHT-Default ist seit #691 16 Bit. Ob Studio
# die zusätzlichen Niederbits physisch nutzt, bleibt im Profil ausdrücklich offen.
EXPORT_PROFILE = DEFAULT_TARGET_PROFILE.profile_id
EXPORT_PROFILE_VERSION = DEFAULT_TARGET_PROFILE.profile_version
DEFAULT_BIT_DEPTH = DEFAULT_TARGET_PROFILE.default_height_bit_depth
_SUPPORTED_BIT_DEPTHS = DEFAULT_TARGET_PROFILE.height_bit_depths

# Druckfläche des eufyMake-E1-Standard-Flachbetts in mm (Breite × Tiefe).
# **Herstellerquelle, aber nur über Suchmaschinen-Extraktion belegt** (Recherche
# #687, Grad S: „13 × 16.5 in" ≈ 330 × 420 mm); eine unabhängige Rückrechnung aus
# der reverse-engineerten ``.empf``-Druckbettgeometrie liegt mit ≈ 333,2 × 418,1 mm
# in derselben Größenordnung. Vor einem harten Vertrag am Original zu verifizieren
# (V-01 in #687) – bis dahin nur als Warnschwelle (Severity.WARNING), nicht als
# blockierender Fehler.
STANDARD_FLATBED_MM = (330.0, 420.0)

# Die px↔mm↔DPI-Geometrie (``MM_PER_INCH``, Ableitungen) lebt seit #376 zentral in
# :mod:`bgremover.units`; ``MM_PER_INCH`` wird oben re-exportiert, damit bisherige
# Importeure (Tests/Module) unverändert weiterfunktionieren.


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


class MissingRequiredAssetError(EufyMakeExportError):
    """Eine vom Zielprofil geforderte Nicht-COLOR-Rolle fehlt im Projekt."""


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
    **COLOR-Komposit** (siehe :attr:`from_color_composite`). ``required`` folgt
    dem gewählten Zielprofil; ``experimental`` markiert Assets mit offener
    Semantik (Gloss-Maske). Es werden hier **keine Pixel** gehalten – das
    Rendern übernimmt #353.
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
    contract: EufyMakeTargetProfile

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


def _derive_bit_depth(
    metadata: dict[str, object], profile: EufyMakeTargetProfile
) -> int:
    """Liest ``META_BIT_DEPTH`` strukturiert aus oder fällt auf den Default zurück.

    **Nur ein fehlender Schlüssel** ergibt :data:`DEFAULT_BIT_DEPTH`. Ein
    *vorhandener* Wert muss ein Integer aus :data:`_SUPPORTED_BIT_DEPTHS` sein
    (``bool`` ist als Integer-Subtyp ausgeschlossen); ein explizites ``None``
    (z. B. ``"bit_depth": null`` aus einem Manifest) zählt als vorhandener,
    ungültiger Wert und löst :class:`InvalidBitDepthError` aus – keine stille
    Korrektur, die korrupte Metadaten als 8 Bit kaschiert.
    """
    if META_BIT_DEPTH not in metadata:
        return profile.default_height_bit_depth
    raw = metadata[META_BIT_DEPTH]
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise InvalidBitDepthError(f"{META_BIT_DEPTH} muss ein Integer sein, war {raw!r}")
    if raw not in profile.height_bit_depths:
        raise InvalidBitDepthError(
            f"{META_BIT_DEPTH} muss in {profile.height_bit_depths} liegen, war {raw}"
        )
    return raw


def coerce_bit_depth(
    metadata: dict[str, object],
    override: int | None,
    *,
    profile: EufyMakeTargetProfile = DEFAULT_TARGET_PROFILE,
) -> int:
    """Effektive Bittiefe: ``override`` (validiert) hat Vorrang, sonst Metadaten.

    Geteilte Regel für Plan und Prüfung (#355): Eine explizite UI-Wahl (8/16) wird
    direkt übernommen (außerhalb von :data:`_SUPPORTED_BIT_DEPTHS` →
    :class:`InvalidBitDepthError`); ohne Override greift die Metadaten-Ableitung.
    """
    if override is None:
        return _derive_bit_depth(metadata, profile)
    if override not in profile.height_bit_depths:
        raise InvalidBitDepthError(
            f"Bittiefe muss in {profile.height_bit_depths} liegen, war {override!r}"
        )
    return override


def _derive_target(
    project: Project,
    *,
    bit_depth: int | None = None,
    profile: EufyMakeTargetProfile = DEFAULT_TARGET_PROFILE,
) -> ExportTarget:
    """Baut die :class:`ExportTarget`-Parameter reproduzierbar aus dem Projekt.

    Physische Größe und DPI stammen aus den **Projektmodell-Gettern** (#376/#378):
    ``META_PHYSICAL_SIZE_MM`` ist die kanonische Quelle, die DPI leitet das Modell
    daraus plus Pixelgröße ab (geteilte Geometrie, kein export-lokaler Zweitweg).
    Ein gespeicherter ungültiger Wert wird – deckungsgleich zur bisherigen Prüfung
    – als :class:`InvalidPhysicalSizeError` gemeldet. ``bit_depth`` überschreibt
    die aus den Metadaten abgeleitete Tiefe (UI-Wahl).
    """
    depth = coerce_bit_depth(project.metadata, bit_depth, profile=profile)
    try:
        physical_size = project.physical_size_mm
        dpi = project.dpi
    except UnitsError as exc:
        raise InvalidPhysicalSizeError(f"{META_PHYSICAL_SIZE_MM}: {exc}") from exc
    return ExportTarget(
        pixel_size=project.size,
        bit_depth=depth,
        physical_size_mm=physical_size,
        dpi=dpi,
    )


def derive_export_target(
    project: Project,
    *,
    bit_depth: int | None = None,
    profile: EufyMakeTargetProfile = DEFAULT_TARGET_PROFILE,
) -> ExportTarget:
    """Öffentliche Ableitung der Zielparameter – auch ohne vorhandenes Farbmotiv.

    Liefert Pixelgröße, physische Größe, DPI und (effektive) Bittiefe unabhängig
    davon, ob der Plan später am fehlenden Farbmotiv blockiert. Für die UI (#355),
    die Zielinfos schon zeigen will, während die Prüfung noch Fehler meldet.
    Ungültige Metadaten werfen weiterhin strukturierte Fehler.
    """
    return _derive_target(project, bit_depth=bit_depth, profile=profile)


def _has_contributing_color(project: Project) -> bool:
    """True, wenn mindestens eine COLOR-Ebene zum Komposit beiträgt.

    Beitragend = ``kind is COLOR`` **und** sichtbar **und** Opazität > 0 – exakt
    die Regel aus :meth:`Project.composite_color`. So ist das geplante Komposit
    nie vollständig transparent.
    """
    return any(
        layer.kind is LayerKind.COLOR and layer.visible and layer.opacity > 0.0
        for layer in project.layers
    )


def can_render_color_motif(project: Project) -> bool:
    """True, wenn aus ``project`` ein Farbmotiv ableitbar ist.

    Entweder trägt eine Ebene die Rolle ``COLOR_MOTIF`` (explizite Quelle, auch
    unsichtbar zulässig) **oder** es gibt eine zum Komposit beitragende
    COLOR-Ebene. Geteilte Quelle der Wahrheit für :func:`build_export_plan` und
    die Konsistenzprüfung (#354), damit beide nicht auseinanderlaufen.
    """
    if project.layer_by_role(LayerRole.COLOR_MOTIF) is not None:
        return True
    return _has_contributing_color(project)


def _plan_color_motif(
    project: Project, contract: EufyMakeTargetProfile
) -> ExportAsset:
    """Plant das **erforderliche** Farbmotiv aus Rolle oder COLOR-Komposit.

    Trägt eine Ebene die Rolle ``COLOR_MOTIF``, ist sie die explizite Quelle
    (auch wenn sie unsichtbar ist – eine bewusste Nutzerzuweisung zählt). Sonst
    dient das **Komposit der COLOR-Ebenen** als Quelle (``source_layer_id``
    ``None``); das setzt voraus, dass mindestens eine COLOR-Ebene tatsächlich zum
    Komposit beiträgt (sichtbar und Opazität > 0 – dieselbe Regel wie
    :meth:`Project.composite_color`). Andernfalls wäre das Komposit vollständig
    transparent und kein echtes Farbmotiv → :class:`MissingColorMotifError`. Das
    Farbmotiv bleibt konservativ 8-Bit-RGBA, unabhängig von ``META_BIT_DEPTH``.
    """
    role_layer = project.layer_by_role(LayerRole.COLOR_MOTIF)
    if role_layer is not None:
        source_id: str | None = role_layer.id
    elif _has_contributing_color(project):
        source_id = None
    else:
        raise MissingColorMotifError(
            "Kein Farbmotiv: weder eine COLOR_MOTIF-Rolle noch eine zum Komposit "
            "beitragende (sichtbare, opake) COLOR-Ebene vorhanden"
        )
    rule = contract.asset_for(LayerRole.COLOR_MOTIF)
    return ExportAsset(
        role=LayerRole.COLOR_MOTIF,
        filename=rule.filename,
        pixel_format=rule.pixel_format,
        bit_depth=rule.default_bit_depth,
        required=rule.required,
        source_layer_id=source_id,
        experimental=rule.experimental,
    )


def _resolve_optional_roles(
    optional_roles: Iterable[LayerRole] | None,
    contract: EufyMakeTargetProfile,
) -> frozenset[LayerRole]:
    """Welche optionalen Rollen ins Paket dürfen: ``None`` = alle, sonst die Auswahl."""
    supported = frozenset(contract.optional_roles)
    if optional_roles is None:
        return supported
    return frozenset(optional_roles) & supported


def build_export_plan(
    project: Project,
    *,
    optional_roles: Iterable[LayerRole] | None = None,
    bit_depth: int | None = None,
    profile: EufyMakeTargetProfile = DEFAULT_TARGET_PROFILE,
) -> ExportPlan:
    """Bildet ein :class:`Project` deterministisch auf einen :class:`ExportPlan` ab.

    Rollen→Assets: ``COLOR_MOTIF`` ergibt das erforderliche Farbmotiv (RGBA,
    8 Bit), ``HEIGHT_MAP`` und ``GLOSS_MASK`` Graustufen-Assets. Profilpflichten
    werden immer einbezogen; ``optional_roles`` wählt nur die optionalen Rollen:
    ``None`` (Standard) nimmt alle vorhandenen, eine Auswahl beschränkt das Paket
    darauf (für die UI-Abwahl, #355). Die Höhenkarte erbt die geplante
    Bittiefe aus ``META_BIT_DEPTH`` (8/16), die Gloss-Maske bleibt konservativ
    8-Bit. Zielparameter (Pixelgröße, physische Größe, DPI, Bittiefe) werden
    reproduzierbar aus den Projektmetadaten bzw. dokumentierten Defaults
    abgeleitet; ungültige Metadaten werfen strukturierte Fehler
    (:class:`EufyMakeExportError`-Subtypen). Es wird **kein** natives ``.empf``
    geplant.
    """
    # Direkt übergebene Profile müssen dieselben Invarianten erfüllen wie
    # Registry-Profile; insbesondere dürfen ihre Dateinamen den Zielordner
    # nicht verlassen oder mit dem Manifest kollidieren.
    ProfileRegistry((profile,))
    target = _derive_target(project, bit_depth=bit_depth, profile=profile)
    included = _resolve_optional_roles(optional_roles, profile) | frozenset(
        role for role in profile.required_roles if role is not LayerRole.COLOR_MOTIF
    )

    assets: list[ExportAsset] = [_plan_color_motif(project, profile)]
    open_questions: list[OpenQuestion] = [OpenQuestion.NATIVE_EMPF_PROJECT]

    height_layer = project.layer_by_role(LayerRole.HEIGHT_MAP)
    if LayerRole.HEIGHT_MAP in included:
        rule = profile.asset_for(LayerRole.HEIGHT_MAP)
        if height_layer is None:
            if rule.required:
                raise MissingRequiredAssetError(
                    f"Profil {profile.reference} fordert Rolle "
                    f"{LayerRole.HEIGHT_MAP.value!r}"
                )
        else:
            assets.append(
                ExportAsset(
                    role=LayerRole.HEIGHT_MAP,
                    filename=rule.filename,
                    pixel_format=rule.pixel_format,
                    bit_depth=target.bit_depth,
                    required=rule.required,
                    source_layer_id=height_layer.id,
                    experimental=rule.experimental,
                )
            )
            open_questions.append(OpenQuestion.HEIGHT_MAP_BIT_DEPTH)

    gloss_layer = project.layer_by_role(LayerRole.GLOSS_MASK)
    if LayerRole.GLOSS_MASK in included:
        rule = profile.asset_for(LayerRole.GLOSS_MASK)
        if gloss_layer is None:
            if rule.required:
                raise MissingRequiredAssetError(
                    f"Profil {profile.reference} fordert Rolle "
                    f"{LayerRole.GLOSS_MASK.value!r}"
                )
        else:
            assets.append(
                ExportAsset(
                    role=LayerRole.GLOSS_MASK,
                    filename=rule.filename,
                    pixel_format=rule.pixel_format,
                    bit_depth=rule.default_bit_depth,
                    required=rule.required,
                    source_layer_id=gloss_layer.id,
                    experimental=rule.experimental,
                )
            )
            open_questions.append(OpenQuestion.GLOSS_MASK_SEMANTICS)

    return ExportPlan(
        profile=profile.profile_id,
        profile_version=profile.profile_version,
        target=target,
        assets=tuple(assets),
        height_semantics=HEIGHT_SEMANTICS,
        open_questions=tuple(open_questions),
        contract=profile,
    )
