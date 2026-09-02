"""Versionierter Zielprofil-Vertrag für den EufyMake-Import-Export (#691).

Das Modul ist die einzige Quelle für Rollen, Dateinamen, Kanalinterpretation,
Defaults, Zielumgebung, Validierungsregeln und Evidenzstatus. Es bleibt Qt- und
dateisystemfrei; Writer, Validator und Dialog erhalten dasselbe unveränderliche
Profilobjekt. Herstellerannahmen und reine Studio-Beobachtungen werden nicht zu
bestätigten Druckeigenschaften hochgestuft.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from bgremover.project_model import LayerRole

PROFILE_SCHEMA_VERSION = 1


class AssetPixelFormat(Enum):
    """Logisches Pixelformat eines Profil-Assets."""

    RGBA = "rgba"
    GRAYSCALE = "grayscale"


class HeightSemantics(Enum):
    """Bestätigte Richtung der Höhenwerte."""

    LIGHT_IS_HIGH = "light_is_high"


class EvidenceStatus(Enum):
    """Reifegrad einer einzelnen Profilbehauptung."""

    CONFIRMED = "confirmed"
    OBSERVED = "observed"
    PROVISIONAL = "provisional"
    OPEN = "open"


class ProfileStatus(Enum):
    """Reifegrad des gesamten Zielprofils."""

    PROVISIONAL = "provisional"
    VALIDATED = "validated"
    RETIRED = "retired"


class ValueDirection(Enum):
    """Richtung eines einkanaligen Wertebereichs."""

    NOT_APPLICABLE = "not_applicable"
    LIGHT_IS_HIGH = "light_is_high"
    OPEN = "open"


class ValidationSeverity(Enum):
    """Schweregrad einer profilgebundenen Validierungsregel."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class TargetEnvironment:
    """Vom BgRemover-App-Release getrennte Zielumgebung."""

    device: str
    studio_version: str
    firmware_version: str | None
    status: EvidenceStatus

    def to_dict(self) -> dict[str, object]:
        return {
            "device": self.device,
            "studio_version": self.studio_version,
            "firmware_version": self.firmware_version,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class EvidenceReference:
    """Nachvollziehbare Quelle für eine oder mehrere Profilbehauptungen."""

    evidence_id: str
    status: EvidenceStatus
    scope: str
    reference: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.evidence_id,
            "status": self.status.value,
            "scope": self.scope,
            "reference": self.reference,
        }


@dataclass(frozen=True)
class AssetRule:
    """Kanal- und Dateivertrag einer Rollenabbildung."""

    role: LayerRole
    filename: str
    pixel_format: AssetPixelFormat
    supported_bit_depths: tuple[int, ...]
    default_bit_depth: int
    value_ranges: tuple[tuple[int, tuple[int, int]], ...]
    direction: ValueDirection
    required: bool
    experimental: bool
    semantics: str
    semantics_status: EvidenceStatus
    alpha_semantics: str | None
    alpha_status: EvidenceStatus | None
    evidence_ids: tuple[str, ...]

    def value_range_for(self, bit_depth: int) -> tuple[int, int]:
        """Liefert den Wertebereich des konkreten Transportträgers."""
        for known_depth, value_range in self.value_ranges:
            if known_depth == bit_depth:
                return value_range
        raise KeyError(
            f"Rolle {self.role.value!r} unterstützt keine {bit_depth}-Bit-Werte"
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role.value,
            "filename": self.filename,
            "pixel_format": self.pixel_format.value,
            "supported_bit_depths": list(self.supported_bit_depths),
            "default_bit_depth": self.default_bit_depth,
            "value_ranges": {
                str(bit_depth): list(value_range)
                for bit_depth, value_range in self.value_ranges
            },
            "direction": self.direction.value,
            "required": self.required,
            "experimental": self.experimental,
            "semantics": self.semantics,
            "semantics_status": self.semantics_status.value,
            "alpha_semantics": self.alpha_semantics,
            "alpha_status": self.alpha_status.value if self.alpha_status else None,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True)
class DimensionRule:
    """Vertrag für Pixelmaße, mm und PNG-Dichteinformationen."""

    equal_pixel_dimensions_required: bool
    png_phys_axes_independent: bool
    studio_fallback_dpi: float
    physical_size_source: str
    dpi_status: EvidenceStatus
    print_size_status: EvidenceStatus
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "equal_pixel_dimensions_required": self.equal_pixel_dimensions_required,
            "png_phys_axes_independent": self.png_phys_axes_independent,
            "studio_fallback_dpi": self.studio_fallback_dpi,
            "physical_size_source": self.physical_size_source,
            "dpi_status": self.dpi_status.value,
            "print_size_status": self.print_size_status.value,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True)
class ValidationRule:
    """Stabiler Befundcode mit Schweregrad und maschinenlesbarer Abhilfe."""

    code: str
    severity: ValidationSeverity
    remedy: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "remedy": self.remedy,
        }


@dataclass(frozen=True)
class EufyMakeTargetProfile:
    """Vollständiger, versionierter Vertrag eines Exportziels."""

    profile_id: str
    profile_version: int
    display_name: str
    status: ProfileStatus
    target_environment: TargetEnvironment
    assets: tuple[AssetRule, ...]
    dimensions: DimensionRule
    validation_rules: tuple[ValidationRule, ...]
    open_properties: tuple[str, ...]
    evidence: tuple[EvidenceReference, ...]
    schema_version: int = PROFILE_SCHEMA_VERSION

    def asset_for(self, role: LayerRole) -> AssetRule:
        """Liefert die Rollenregel oder signalisiert ein ungültiges Profil."""
        for asset in self.assets:
            if asset.role is role:
                return asset
        raise KeyError(f"Profil {self.reference} enthält Rolle {role.value!r} nicht")

    def validation_for(self, code: str) -> ValidationRule:
        """Liefert die Validierungsregel zu einem stabilen Befundcode."""
        for rule in self.validation_rules:
            if rule.code == code:
                return rule
        raise KeyError(f"Profil {self.reference} enthält Befundcode {code!r} nicht")

    @property
    def reference(self) -> str:
        return f"{self.profile_id}@{self.profile_version}"

    @property
    def optional_roles(self) -> tuple[LayerRole, ...]:
        return tuple(asset.role for asset in self.assets if not asset.required)

    @property
    def height_bit_depths(self) -> tuple[int, ...]:
        return self.asset_for(LayerRole.HEIGHT_MAP).supported_bit_depths

    @property
    def default_height_bit_depth(self) -> int:
        return self.asset_for(LayerRole.HEIGHT_MAP).default_bit_depth

    def to_dict(self) -> dict[str, object]:
        """Serialisiert den Vertrag deterministisch für Manifest und Golden-Test."""
        return {
            "schema_version": self.schema_version,
            "id": self.profile_id,
            "version": self.profile_version,
            "display_name": self.display_name,
            "status": self.status.value,
            "target_environment": self.target_environment.to_dict(),
            "assets": [asset.to_dict() for asset in self.assets],
            "dimensions": self.dimensions.to_dict(),
            "validation_rules": [rule.to_dict() for rule in self.validation_rules],
            "open_properties": list(self.open_properties),
            "evidence": [item.to_dict() for item in self.evidence],
        }


class ProfileResolutionError(ValueError):
    """Basis verständlicher Profilauflösungsfehler."""


class UnknownProfileError(ProfileResolutionError):
    """Die Profilkennung ist nicht registriert."""


class UnsupportedProfileVersionError(ProfileResolutionError):
    """Die Kennung ist bekannt, die angeforderte Version aber nicht."""


class InvalidProfileReferenceError(ProfileResolutionError):
    """Ein Manifest enthält keine typkorrekte Profilreferenz."""


class ProfileContractMismatchError(ProfileResolutionError):
    """Snapshot und registrierter Vertrag derselben Version widersprechen sich."""


class ProfileRegistry:
    """Explizites Register für bestehende und künftige Zielprofile."""

    def __init__(self, profiles: tuple[EufyMakeTargetProfile, ...] = ()) -> None:
        self._profiles: dict[tuple[str, int], EufyMakeTargetProfile] = {}
        for profile in profiles:
            self.register(profile)

    def register(self, profile: EufyMakeTargetProfile) -> None:
        key = (profile.profile_id, profile.profile_version)
        if key in self._profiles:
            raise ValueError(f"Profil bereits registriert: {profile.reference}")
        if profile.schema_version != PROFILE_SCHEMA_VERSION:
            raise ValueError(
                f"Profilschema {profile.schema_version} wird nicht unterstützt; "
                f"erwartet ist {PROFILE_SCHEMA_VERSION}"
            )
        roles = [asset.role for asset in profile.assets]
        if len(set(roles)) != len(roles) or LayerRole.COLOR_MOTIF not in roles:
            raise ValueError(f"Profil {profile.reference} hat keine eindeutigen Rollen")
        evidence_ids = {item.evidence_id for item in profile.evidence}
        for asset in profile.assets:
            range_depths = {bit_depth for bit_depth, _ in asset.value_ranges}
            if asset.default_bit_depth not in asset.supported_bit_depths:
                raise ValueError(
                    f"Profil {profile.reference}: Default-Tiefe für {asset.role.value} "
                    "ist nicht unterstützt"
                )
            if range_depths != set(asset.supported_bit_depths):
                raise ValueError(
                    f"Profil {profile.reference}: Wertebereiche für {asset.role.value} "
                    "decken die unterstützten Tiefen nicht exakt ab"
                )
            if not set(asset.evidence_ids) <= evidence_ids:
                raise ValueError(
                    f"Profil {profile.reference}: unbekannte Evidenz-ID für {asset.role.value}"
                )
        codes = [rule.code for rule in profile.validation_rules]
        if len(set(codes)) != len(codes) or any(not rule.remedy for rule in profile.validation_rules):
            raise ValueError(
                f"Profil {profile.reference} hat doppelte Codes oder leere Abhilfen"
            )
        self._profiles[key] = profile

    def resolve(self, profile_id: str, profile_version: int) -> EufyMakeTargetProfile:
        key = (profile_id, profile_version)
        profile = self._profiles.get(key)
        if profile is not None:
            return profile
        versions = sorted(version for known_id, version in self._profiles if known_id == profile_id)
        if not versions:
            raise UnknownProfileError(f"Unbekanntes EufyMake-Zielprofil: {profile_id!r}")
        supported = ", ".join(str(version) for version in versions)
        raise UnsupportedProfileVersionError(
            f"EufyMake-Zielprofil {profile_id!r} Version {profile_version} wird nicht "
            f"unterstützt; verfügbar: {supported}"
        )

    def profiles(self) -> tuple[EufyMakeTargetProfile, ...]:
        return tuple(
            self._profiles[key]
            for key in sorted(self._profiles, key=lambda item: (item[0], item[1]))
        )


_VALIDATION_RULES = (
    ValidationRule("color_motif_missing", ValidationSeverity.ERROR, "assign_color_motif"),
    ValidationRule("optional_role_missing", ValidationSeverity.ERROR, "assign_requested_role"),
    ValidationRule("asset_size_mismatch", ValidationSeverity.ERROR, "match_canvas_dimensions"),
    ValidationRule("invalid_target_params", ValidationSeverity.ERROR, "correct_target_parameters"),
    ValidationRule("height_map_empty", ValidationSeverity.WARNING, "review_height_values"),
    ValidationRule("gloss_mask_empty", ValidationSeverity.WARNING, "review_gloss_values"),
    ValidationRule("bit_depth_unconfirmed", ValidationSeverity.WARNING, "confirm_height_carrier"),
    ValidationRule("height_precision_loss", ValidationSeverity.WARNING, "select_16_bit_height"),
    ValidationRule("gloss_ink_mode", ValidationSeverity.WARNING, "assign_native_gloss_in_studio"),
    ValidationRule("physical_size_unverified", ValidationSeverity.WARNING, "verify_print_dimensions"),
    ValidationRule("print_area_exceeded", ValidationSeverity.WARNING, "fit_standard_flatbed"),
)


DEFAULT_TARGET_PROFILE = EufyMakeTargetProfile(
    profile_id="bgremover-eufymake-import",
    profile_version=1,
    display_name="eufyMake E1 / Studio 4.2.2",
    status=ProfileStatus.PROVISIONAL,
    target_environment=TargetEnvironment(
        device="eufyMake E1",
        studio_version="4.2.2",
        firmware_version=None,
        status=EvidenceStatus.OBSERVED,
    ),
    assets=(
        AssetRule(
            role=LayerRole.COLOR_MOTIF,
            filename="color_motif.png",
            pixel_format=AssetPixelFormat.RGBA,
            supported_bit_depths=(8,),
            default_bit_depth=8,
            value_ranges=((8, (0, 255)),),
            direction=ValueDirection.NOT_APPLICABLE,
            required=True,
            experimental=False,
            semantics="rgba_color_with_straight_alpha",
            semantics_status=EvidenceStatus.CONFIRMED,
            alpha_semantics="straight_alpha_coverage",
            alpha_status=EvidenceStatus.CONFIRMED,
            evidence_ids=("writer-roundtrip",),
        ),
        AssetRule(
            role=LayerRole.HEIGHT_MAP,
            filename="height_map.png",
            pixel_format=AssetPixelFormat.GRAYSCALE,
            supported_bit_depths=(8, 16),
            default_bit_depth=16,
            value_ranges=((8, (0, 255)), (16, (0, 65535))),
            direction=ValueDirection.LIGHT_IS_HIGH,
            required=False,
            experimental=False,
            semantics="grayscale_height_carrier_without_mm_mapping",
            semantics_status=EvidenceStatus.PROVISIONAL,
            alpha_semantics=None,
            alpha_status=None,
            evidence_ids=("issue-688-studio-import", "manufacturer-height-direction"),
        ),
        AssetRule(
            role=LayerRole.GLOSS_MASK,
            filename="gloss_mask.png",
            pixel_format=AssetPixelFormat.GRAYSCALE,
            supported_bit_depths=(8,),
            default_bit_depth=8,
            value_ranges=((8, (0, 255)),),
            direction=ValueDirection.OPEN,
            required=False,
            experimental=True,
            semantics="helper_mask_requiring_native_studio_gloss_assignment",
            semantics_status=EvidenceStatus.OPEN,
            alpha_semantics=None,
            alpha_status=None,
            evidence_ids=("issue-690-studio-import", "manufacturer-spot-uv-hypothesis"),
        ),
    ),
    dimensions=DimensionRule(
        equal_pixel_dimensions_required=True,
        png_phys_axes_independent=True,
        studio_fallback_dpi=72.0,
        physical_size_source="project_physical_size_mm_to_png_phys",
        dpi_status=EvidenceStatus.OBSERVED,
        print_size_status=EvidenceStatus.OPEN,
        evidence_ids=("issue-689-studio-import",),
    ),
    validation_rules=_VALIDATION_RULES,
    open_properties=(
        "height_map_bit_depth_utilization",
        "height_grayscale_to_mm_mapping",
        "gloss_mask_polarity_and_intensity",
        "physical_print_size_and_registration",
        "native_empf_project",
    ),
    evidence=(
        EvidenceReference(
            "writer-roundtrip",
            EvidenceStatus.CONFIRMED,
            "BgRemover-Pixel-, Alpha- und Manifestvertrag",
            "automated-tests",
        ),
        EvidenceReference(
            "manufacturer-height-direction",
            EvidenceStatus.CONFIRMED,
            "hell = hoch / dunkel = niedrig",
            "docs/history/EUFYMAKE-687-QUELLENREGISTER.md",
        ),
        EvidenceReference(
            "issue-688-studio-import",
            EvidenceStatus.OBSERVED,
            "8-/16-Bit-Trägerimport; physische Nutzung und mm-Abbildung offen",
            "https://github.com/NikolayDA/picture_helper/issues/688",
        ),
        EvidenceReference(
            "issue-689-studio-import",
            EvidenceStatus.OBSERVED,
            "pHYs X/Y und 72-dpi-Fallback in Studio 4.2.2; Druckmaß offen",
            "https://github.com/NikolayDA/picture_helper/issues/689",
        ),
        EvidenceReference(
            "issue-690-studio-import",
            EvidenceStatus.OBSERVED,
            "Gloss-PNG bleibt Flat; native Gloss-Zuweisung und Druckwirkung offen",
            "https://github.com/NikolayDA/picture_helper/issues/690",
        ),
        EvidenceReference(
            "manufacturer-spot-uv-hypothesis",
            EvidenceStatus.PROVISIONAL,
            "Schwarz = Auftrag / Weiß = kein Auftrag ist nur Herstellerhypothese",
            "docs/history/EUFYMAKE-690-GLOSS-VERTRAG.md",
        ),
    ),
)

DEFAULT_PROFILE_REGISTRY = ProfileRegistry((DEFAULT_TARGET_PROFILE,))


@dataclass(frozen=True)
class ResolvedManifestProfile:
    """Aufgelöste Profilreferenz samt Kennzeichnung des Legacy-Formats."""

    profile: EufyMakeTargetProfile
    legacy_reference: bool


def resolve_manifest_profile(
    manifest: Mapping[str, Any],
    *,
    registry: ProfileRegistry = DEFAULT_PROFILE_REGISTRY,
) -> ResolvedManifestProfile:
    """Löst neue und alte Manifestreferenzen ohne stilles Versionsraten auf.

    Neue Manifeste tragen ``profile_contract.id/version``. Alte Manifeste aus
    BgRemover 2.8/2.9 werden über ``profile/profile_version`` gelesen und als
    ``legacy_reference=True`` markiert; fehlende Snapshot-Felder werden nicht
    erfunden oder zurückgeschrieben.
    """
    has_contract = "profile_contract" in manifest
    raw_contract = manifest.get("profile_contract")
    if has_contract and not isinstance(raw_contract, Mapping):
        raise InvalidProfileReferenceError(
            "Manifest enthält einen ungültigen EufyMake-Profilsnapshot"
        )
    if isinstance(raw_contract, Mapping):
        legacy = False
        source: Mapping[str, Any] = raw_contract
    else:
        legacy = True
        source = manifest
    id_key = "profile" if legacy else "id"
    version_key = "profile_version" if legacy else "version"
    profile_id = source.get(id_key)
    profile_version = source.get(version_key)
    if not isinstance(profile_id, str) or isinstance(profile_version, bool) or not isinstance(
        profile_version, int
    ):
        raise InvalidProfileReferenceError(
            "Manifest enthält keine gültige EufyMake-Profilkennung und -version"
        )
    profile = registry.resolve(profile_id, profile_version)
    if not legacy and dict(source) != profile.to_dict():
        raise ProfileContractMismatchError(
            f"EufyMake-Profilsnapshot widerspricht {profile.reference}"
        )
    return ResolvedManifestProfile(profile=profile, legacy_reference=legacy)
