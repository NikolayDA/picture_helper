"""Vertrags-, Registry-, Golden- und Legacy-Tests des Zielprofils (#691)."""
from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from bgremover.eufymake_profile import (
    DEFAULT_TARGET_PROFILE,
    EvidenceStatus,
    InvalidProfileReferenceError,
    ProfileContractMismatchError,
    ProfileRegistry,
    ProfileStatus,
    UnknownProfileError,
    UnsupportedProfileVersionError,
    resolve_manifest_profile,
)
from bgremover.eufymake_validate import ExportCheckCode
from bgremover.project_model import LayerRole


def _canonical_json() -> str:
    return json.dumps(
        DEFAULT_TARGET_PROFILE.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def test_profile_v1_matches_reviewed_golden_contract() -> None:
    """Jede Vertragsänderung erfordert eine bewusste Profilversionsentscheidung."""
    digest = hashlib.sha256(_canonical_json().encode("utf-8")).hexdigest()
    assert digest == "caa7d34abc48b215355fe13b8a69b1c70a241878b371885eabecf05f41c8fdea"


def test_profile_contract_is_json_roundtrip_safe() -> None:
    encoded = _canonical_json()
    decoded = json.loads(encoded)
    assert decoded == DEFAULT_TARGET_PROFILE.to_dict()
    resolved = resolve_manifest_profile({"profile_contract": decoded})
    assert resolved.profile is DEFAULT_TARGET_PROFILE
    assert resolved.legacy_reference is False


def test_legacy_manifest_reference_is_resolved_but_marked() -> None:
    resolved = resolve_manifest_profile(
        {
            "profile": DEFAULT_TARGET_PROFILE.profile_id,
            "profile_version": DEFAULT_TARGET_PROFILE.profile_version,
        }
    )
    assert resolved.profile is DEFAULT_TARGET_PROFILE
    assert resolved.legacy_reference is True


def test_frozen_legacy_manifest_remains_a_readable_reference() -> None:
    manifest_path = (
        Path(__file__).parent
        / "fixtures/eufymake_profile/legacy_manifest_v1.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    resolved = resolve_manifest_profile(manifest)
    assert resolved.profile is DEFAULT_TARGET_PROFILE
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
    registry = ProfileRegistry((DEFAULT_TARGET_PROFILE,))
    with pytest.raises(UnknownProfileError, match="Unbekanntes"):
        registry.resolve("vendor-unknown", 1)
    with pytest.raises(UnsupportedProfileVersionError, match="verfügbar: 1"):
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
        validation_rules=DEFAULT_TARGET_PROFILE.validation_rules[:-1],
    )
    with pytest.raises(ValueError, match="unvollständige"):
        ProfileRegistry((profile,))


def test_profile_keeps_hardware_unknowns_open() -> None:
    profile = DEFAULT_TARGET_PROFILE
    assert profile.status is ProfileStatus.PROVISIONAL
    assert profile.asset_for(LayerRole.HEIGHT_MAP).default_bit_depth == 16
    assert profile.asset_for(LayerRole.HEIGHT_MAP).semantics_status is EvidenceStatus.PROVISIONAL
    assert profile.asset_for(LayerRole.GLOSS_MASK).semantics_status is EvidenceStatus.OPEN
    assert profile.dimensions.dpi_status is EvidenceStatus.OBSERVED
    assert profile.dimensions.print_size_status is EvidenceStatus.OPEN
    assert "height_grayscale_to_mm_mapping" in profile.open_properties
    assert "gloss_mask_polarity_and_intensity" in profile.open_properties


def test_profile_defines_every_stable_validation_code_and_remedy() -> None:
    rules = {rule.code: rule for rule in DEFAULT_TARGET_PROFILE.validation_rules}
    assert set(rules) == {code.value for code in ExportCheckCode}
    assert all(rule.remedy for rule in rules.values())
