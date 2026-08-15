"""Netz- und Qt-freie Vertragstests für die native 3D-Screenshot-Sidecar."""
from __future__ import annotations

from scripts import abnahme_smoke as smoke


def _valid_payload() -> dict[str, object]:
    return {
        "schema": smoke.NATIVE_3D_PROVENANCE_SCHEMA,
        "preview3d_controls_visible": True,
        "preview3d_visible_controls": list(smoke.NATIVE_3D_REQUIRED_CONTROLS),
    }


def test_valid_controls_evidence_is_accepted() -> None:
    ok, detail = smoke.validate_native_3d_provenance(_valid_payload())
    assert ok, detail


def test_old_schema_is_rejected() -> None:
    payload = _valid_payload()
    payload["schema"] = 1
    ok, detail = smoke.validate_native_3d_provenance(payload)
    assert not ok
    assert "Schema 1" in detail


def test_missing_or_partial_controls_evidence_is_rejected() -> None:
    payload = _valid_payload()
    payload["preview3d_visible_controls"] = ["preview3d_azimuth"]
    ok, detail = smoke.validate_native_3d_provenance(payload)
    assert not ok
    assert "preview3d_azimuth" in detail


def test_non_object_or_non_string_control_is_rejected_without_exception() -> None:
    assert smoke.validate_native_3d_provenance([])[0] is False
    payload = _valid_payload()
    payload["preview3d_visible_controls"] = [
        "preview3d_azimuth",
        "preview3d_elevation",
        {"unexpected": "object"},
    ]
    assert smoke.validate_native_3d_provenance(payload)[0] is False
