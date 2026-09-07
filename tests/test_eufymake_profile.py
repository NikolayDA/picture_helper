"""Vertrags-, Registry-, Golden- und Legacy-Tests des Zielprofils (#691)."""
from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from bgremover.eufymake_profile import (
    DEFAULT_PROFILE_REGISTRY,
    DEFAULT_TARGET_PROFILE,
    TARGET_PROFILE_V1,
    TARGET_PROFILE_V2,
    EvidenceStatus,
    InvalidProfileReferenceError,
    ProfileContractMismatchError,
    ProfileRegistry,
    ProfileStatus,
    UnknownProfileError,
    UnsupportedProfileVersionError,
    ValidationRule,
    ValidationSeverity,
    resolve_manifest_profile,
)
from bgremover.eufymake_validate import ExportCheckCode
from bgremover.project_model import LayerRole


def _canonical_json(profile=TARGET_PROFILE_V1) -> str:
    return json.dumps(
        profile.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def test_profile_v1_matches_reviewed_golden_contract() -> None:
    """Jede Vertragsänderung erfordert eine bewusste Profilversionsentscheidung.

    Neu gesetzt am 2026-09-02: Die Evidenzreferenz ``manufacturer-height-direction``
    zeigte auf eine nie angelegte Datei (``EUFYMAKE-687-QUELLENREGISTER.md``) und
    verweist jetzt auf das Annahmeninventar. Die Korrektur blieb innerhalb von
    v1, weil noch kein Release Profil v1 ausgeliefert hat und kein eingechecktes
    Manifest einen Snapshot trug; ab jetzt verlangt jede Snapshot-Änderung eine
    neue Profilversion.
    """
    digest = hashlib.sha256(_canonical_json().encode("utf-8")).hexdigest()
    assert digest == "11b8053e5d79938aea0e19cf137f5111524de21192e1de8f3c4e5861839f845d"


def test_profile_v2_matches_reviewed_golden_contract() -> None:
    digest = hashlib.sha256(_canonical_json(TARGET_PROFILE_V2).encode("utf-8")).hexdigest()
    assert digest == "731710a0ec1a60eb73e363891060f9714b83acd075f2c9386d9f9bf871953f33"


def test_profile_v2_is_the_additive_default_for_updated_target() -> None:
    assert DEFAULT_TARGET_PROFILE is TARGET_PROFILE_V2
    assert TARGET_PROFILE_V1.profile_version == 1
    assert TARGET_PROFILE_V2.profile_version == 2
    assert TARGET_PROFILE_V1.profile_id == TARGET_PROFILE_V2.profile_id
    assert TARGET_PROFILE_V2.target_environment.studio_version == "4.3.3"
    assert TARGET_PROFILE_V2.target_environment.firmware_version == "4.0.9"
    assert TARGET_PROFILE_V2.status is ProfileStatus.PROVISIONAL
    assert DEFAULT_PROFILE_REGISTRY.profiles() == (TARGET_PROFILE_V1, TARGET_PROFILE_V2)


def test_profile_v2_records_new_environment_unknowns_and_negative_evidence() -> None:
    added_open_properties = set(TARGET_PROFILE_V2.open_properties) - set(
        TARGET_PROFILE_V1.open_properties
    )
    assert added_open_properties == {
        "bidirectional_print_direction_calibration",
        "gloss_x_field_semantics_and_physical_registration",
    }
    evidence = next(
        item
        for item in TARGET_PROFILE_V2.evidence
        if item.evidence_id == "epic-681-preflight-2026-09-07"
    )
    assert evidence.status is EvidenceStatus.OBSERVED
    assert "Bidirectional-Kalibrierung offen" in evidence.scope
    assert "X-Feld-Semantik" in evidence.scope
    assert "Canvas-left=122,345" in evidence.scope
    assert "Auswahlbox und Print-Preview linksbündig" in evidence.scope
    assert "Properties-X=167,50" in evidence.scope
    assert "W=45,16 der sichtbaren rechten Kante" in evidence.scope
    assert "kein Runtime-/Preview-Versatz belegt" in evidence.scope
    assert "epic-681-preflight-2026-09-07" in TARGET_PROFILE_V2.dimensions.evidence_ids
    assert TARGET_PROFILE_V1.dimensions.evidence_ids == ("issue-689-studio-import",)
    assert evidence.reference == "docs/history/EUFYMAKE-681-PREFLIGHT-2026-09-07.md"


def test_evidence_references_point_to_existing_repository_files() -> None:
    """Ein Repo-Pfad im Evidenzvertrag landet in jedem Manifest – er muss existieren.

    Negativregel statt Präfixfilter (#956-Review): Alles, was weder URL noch der
    Sentinel ``automated-tests`` ist, muss als Datei existieren – so fällt auch
    ein künftiger ``tests/…``-, ``scripts/…``- oder relativer Verweis auf.
    """
    root = Path(__file__).resolve().parent.parent
    for profile in DEFAULT_PROFILE_REGISTRY.profiles():
        for item in profile.evidence:
            if (
                item.reference.startswith(("http://", "https://"))
                or item.reference == "automated-tests"
            ):
                continue
            assert (root / item.reference).is_file(), item.reference


@pytest.mark.parametrize("profile", [TARGET_PROFILE_V1, TARGET_PROFILE_V2])
def test_profile_contract_is_json_roundtrip_safe(profile) -> None:
    encoded = _canonical_json(profile)
    decoded = json.loads(encoded)
    assert decoded == profile.to_dict()
    resolved = resolve_manifest_profile({"profile_contract": decoded})
    assert resolved.profile is profile
    assert resolved.legacy_reference is False


def test_legacy_manifest_reference_is_resolved_but_marked() -> None:
    resolved = resolve_manifest_profile(
        {
            "profile": DEFAULT_TARGET_PROFILE.profile_id,
            "profile_version": TARGET_PROFILE_V1.profile_version,
        }
    )
    assert resolved.profile is TARGET_PROFILE_V1
    assert resolved.legacy_reference is True


def test_frozen_legacy_manifest_remains_a_readable_reference() -> None:
    manifest_path = (
        Path(__file__).parent
        / "fixtures/eufymake_profile/legacy_manifest_v1.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    resolved = resolve_manifest_profile(manifest)
    assert resolved.profile is TARGET_PROFILE_V1
    assert resolved.legacy_reference is True


@pytest.mark.parametrize(
    "manifest",
    [
        {},
        {"profile": "x", "profile_version": True},
        {"profile_contract": {"id": "x", "version": "1"}},
        {"profile": DEFAULT_TARGET_PROFILE.profile_id, "profile_version": 1, "profile_contract": None},
    ],
)
def test_invalid_manifest_reference_is_understandable(manifest: dict[str, object]) -> None:
    with pytest.raises(InvalidProfileReferenceError, match="Manifest enthält"):
        resolve_manifest_profile(manifest)


def test_changed_snapshot_under_same_version_is_rejected() -> None:
    snapshot = DEFAULT_TARGET_PROFILE.to_dict()
    snapshot["status"] = "validated"
    with pytest.raises(ProfileContractMismatchError, match="widerspricht"):
        resolve_manifest_profile({"profile_contract": snapshot})


def test_registry_distinguishes_unknown_id_and_unsupported_version() -> None:
    registry = ProfileRegistry((TARGET_PROFILE_V1, TARGET_PROFILE_V2))
    with pytest.raises(UnknownProfileError, match="Unbekanntes"):
        registry.resolve("vendor-unknown", 1)
    with pytest.raises(UnsupportedProfileVersionError, match="verfügbar: 1, 2"):
        registry.resolve(DEFAULT_TARGET_PROFILE.profile_id, 99)


def test_registry_accepts_a_future_profile_without_consumer_branch() -> None:
    registry = ProfileRegistry((DEFAULT_TARGET_PROFILE,))
    future = dataclasses.replace(
        DEFAULT_TARGET_PROFILE,
        profile_id="bgremover-eufymake-future",
        profile_version=2,
        display_name="Future target",
    )
    registry.register(future)
    assert registry.resolve(future.profile_id, future.profile_version) is future
    with pytest.raises(ValueError, match="bereits registriert"):
        registry.register(future)


def test_registry_requires_roles_used_by_every_consumer() -> None:
    profile = dataclasses.replace(
        DEFAULT_TARGET_PROFILE,
        assets=tuple(
            asset
            for asset in DEFAULT_TARGET_PROFILE.assets
            if asset.role is not LayerRole.HEIGHT_MAP
        ),
    )
    with pytest.raises(ValueError, match="Consumer-Rollen.*height_map"):
        ProfileRegistry((profile,))


@pytest.mark.parametrize(
    "filename",
    ["manifest.json", "Manifest.JSON", "../outside.png", "nested/asset.png", r"..\outside.png"],
)
def test_registry_rejects_reserved_or_non_basename_asset_filenames(
    filename: str,
) -> None:
    assets = list(DEFAULT_TARGET_PROFILE.assets)
    assets[0] = dataclasses.replace(assets[0], filename=filename)
    profile = dataclasses.replace(DEFAULT_TARGET_PROFILE, assets=tuple(assets))
    with pytest.raises(ValueError, match="Asset-Dateiname"):
        ProfileRegistry((profile,))


def test_registry_rejects_duplicate_asset_filenames_case_insensitively() -> None:
    assets = list(DEFAULT_TARGET_PROFILE.assets)
    assets[1] = dataclasses.replace(assets[1], filename="COLOR_MOTIF.PNG")
    profile = dataclasses.replace(DEFAULT_TARGET_PROFILE, assets=tuple(assets))
    with pytest.raises(ValueError, match="Asset-Dateiname"):
        ProfileRegistry((profile,))


def test_registry_rejects_unknown_dimension_evidence_id() -> None:
    profile = dataclasses.replace(
        DEFAULT_TARGET_PROFILE,
        dimensions=dataclasses.replace(
            DEFAULT_TARGET_PROFILE.dimensions,
            evidence_ids=(
                *DEFAULT_TARGET_PROFILE.dimensions.evidence_ids,
                "missing-dimension-evidence",
            ),
        ),
    )
    with pytest.raises(ValueError, match="Evidenz-ID für Dimensionen"):
        ProfileRegistry((profile,))


@pytest.mark.parametrize("version", [True, "1", 1.0])
def test_registry_rejects_non_integer_profile_versions(version: object) -> None:
    profile = dataclasses.replace(
        DEFAULT_TARGET_PROFILE,
        profile_version=version,  # type: ignore[arg-type]
    )
    with pytest.raises(ValueError, match="Profilversion"):
        ProfileRegistry((profile,))


def test_registry_rejects_duplicate_bit_depth_ranges() -> None:
    assets = list(DEFAULT_TARGET_PROFILE.assets)
    height = assets[1]
    assets[1] = dataclasses.replace(
        height,
        value_ranges=height.value_ranges + ((8, (0, 255)),),
    )
    profile = dataclasses.replace(DEFAULT_TARGET_PROFILE, assets=tuple(assets))
    with pytest.raises(ValueError, match="Wertebereiche"):
        ProfileRegistry((profile,))


def test_registry_requires_every_stable_validation_code() -> None:
    profile = dataclasses.replace(
        DEFAULT_TARGET_PROFILE,
        validation_rules=tuple(
            rule
            for rule in DEFAULT_TARGET_PROFILE.validation_rules
            if rule.code != ExportCheckCode.PRINT_AREA_EXCEEDED.value
        ),
    )
    with pytest.raises(ValueError, match="unvollständige"):
        ProfileRegistry((profile,))


def test_registry_rejects_unknown_profile_specific_validation_code() -> None:
    profile = dataclasses.replace(
        DEFAULT_TARGET_PROFILE,
        validation_rules=(
            *DEFAULT_TARGET_PROFILE.validation_rules,
            ValidationRule("unknown_future_code", ValidationSeverity.WARNING, "review"),
        ),
    )
    with pytest.raises(ValueError, match="unvollständige"):
        ProfileRegistry((profile,))


def test_registry_requires_complete_validation_codes_for_default_profile() -> None:
    incomplete_default = dataclasses.replace(
        DEFAULT_TARGET_PROFILE,
        validation_rules=TARGET_PROFILE_V1.validation_rules,
    )
    with pytest.raises(ValueError, match="Defaultprofil.*unvollständige"):
        ProfileRegistry((incomplete_default,), default_profile=incomplete_default)


@pytest.mark.parametrize("profile", [TARGET_PROFILE_V1, TARGET_PROFILE_V2])
def test_profile_keeps_hardware_unknowns_open(profile) -> None:
    assert profile.status is ProfileStatus.PROVISIONAL
    assert profile.asset_for(LayerRole.HEIGHT_MAP).default_bit_depth == 16
    assert profile.asset_for(LayerRole.HEIGHT_MAP).semantics_status is EvidenceStatus.PROVISIONAL
    assert profile.asset_for(LayerRole.GLOSS_MASK).semantics_status is EvidenceStatus.OPEN
    assert profile.dimensions.dpi_status is EvidenceStatus.OBSERVED
    assert profile.dimensions.print_size_status is EvidenceStatus.OPEN
    assert "height_grayscale_to_mm_mapping" in profile.open_properties
    assert "gloss_mask_polarity_and_intensity" in profile.open_properties


def test_profiles_define_version_specific_validation_codes_and_remedies() -> None:
    v1_rules = {rule.code: rule for rule in TARGET_PROFILE_V1.validation_rules}
    v2_rules = {rule.code: rule for rule in TARGET_PROFILE_V2.validation_rules}
    default_rules = {
        rule.code: rule for rule in DEFAULT_TARGET_PROFILE.validation_rules
    }
    missing = ExportCheckCode.PHYSICAL_SIZE_MISSING.value
    assert set(v1_rules) == {code.value for code in ExportCheckCode} - {missing}
    assert set(v2_rules) == {code.value for code in ExportCheckCode}
    assert set(default_rules) == {code.value for code in ExportCheckCode}
    assert not TARGET_PROFILE_V1.supports_validation(missing)
    assert TARGET_PROFILE_V2.supports_validation(missing)
    assert all(rule.remedy for rule in (*v1_rules.values(), *v2_rules.values()))
