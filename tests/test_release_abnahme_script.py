"""Tests für den Release-Abnahme-Helfer (#641)."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# Das Skript via importlib laden (scripts/ ist kein Paket), analog test_benchmark.
_SPEC = importlib.util.spec_from_file_location(
    "release_abnahme", ROOT / "scripts" / "release_abnahme.py"
)
assert _SPEC is not None and _SPEC.loader is not None
ra = importlib.util.module_from_spec(_SPEC)
sys.modules["release_abnahme"] = ra
_SPEC.loader.exec_module(ra)


def test_matches_platform() -> None:
    assert ra.matches_platform("BgRemover-2.7.0-macos-arm64-ai.dmg", "macos-arm64")
    assert ra.matches_platform(
        "BgRemover-2.7.0-linux-raspberrypi-arm64-ai.AppImage", "linux-arm64"
    )
    assert ra.matches_platform("BgRemover-2.7.0-linux-x86_64-ai.deb", "linux-x86_64")
    # Raspberry-Pi-aarch64 darf nicht als generisches x86_64 durchgehen.
    assert not ra.matches_platform(
        "BgRemover-2.7.0-linux-raspberrypi-arm64-ai.deb", "linux-x86_64"
    )
    # macOS-arm64 darf nicht als linux-arm64 durchgehen.
    assert not ra.matches_platform("BgRemover-2.7.0-macos-arm64-ai.dmg", "linux-arm64")


def test_build_evidence_carries_contract_fields() -> None:
    records = [ra.ArtifactRecord(name="a.dmg", sha256="deadbeef", bytes=42)]
    evidence = ra.build_evidence(
        "macos-arm64", "abc123", {"art": "release-tag", "wert": "v2.7.0"}, records, ["hi"],
    )
    assert evidence["schema"] == ra.EVIDENCE_SCHEMA
    assert evidence["kind"] == ra.EVIDENCE_KIND
    assert evidence["platform"] == "macos-arm64"
    assert evidence["status"] == ra.STATUS_PLACEHOLDER
    assert evidence["commit_sha"] == "abc123"
    assert evidence["gl_provenance"] is None
    assert evidence["artefakte"][0]["sha256"] == "deadbeef"
    assert set(evidence["umgebung"]) == {"os", "arch", "python", "runner"}


def test_evaluate_gl_provenance_gates_software_and_missing() -> None:
    hardware = ra.evaluate_gl_provenance("Apple / Apple M3 Max / 2.1 Metal - 90.5")
    assert hardware.ok and "Hardware-Renderer" in hardware.note

    software = ra.evaluate_gl_provenance("Mesa / llvmpipe (LLVM 18) / 4.5")
    assert not software.ok and "Software-Renderer" in software.note

    for empty in (None, "", "   "):
        verdict = ra.evaluate_gl_provenance(empty)
        assert not verdict.ok and verdict.diagnostic == ""


def test_evaluate_retina_threshold() -> None:
    assert ra.evaluate_retina(2.0)
    assert ra.evaluate_retina(3.0)
    assert not ra.evaluate_retina(1.0)
    assert not ra.evaluate_retina(1.5)


def test_evaluate_deb_cleanup() -> None:
    assert ra.evaluate_deb_cleanup(package_installed=False, leftover_paths=[])
    assert not ra.evaluate_deb_cleanup(package_installed=True, leftover_paths=[])
    assert not ra.evaluate_deb_cleanup(package_installed=False, leftover_paths=["/usr/bin/x"])


def test_finalize_evidence_sets_status_and_provenance() -> None:
    records = [ra.ArtifactRecord(name="a.dmg", sha256="cafe", bytes=7)]
    base = ra.build_evidence(
        "macos-arm64", "abc", {"art": "release-tag", "wert": "v2.7.0"}, records,
        ["Platzhalter-Smoke aus #641 – echte Smokes folgen mit #642/#643."],
    )
    passed = ra.finalize_evidence(
        base, passed=True, gl_provenance="Apple / M3 / 2.1 Metal", extra_notes=["ok"],
    )
    assert passed["status"] == ra.STATUS_PASSED
    assert passed["gl_provenance"] == "Apple / M3 / 2.1 Metal"
    # Der Platzhalter-Hinweis ist ersetzt, der echte Hinweis übernommen.
    assert not any("Platzhalter-Smoke" in n for n in passed["hinweise"])
    assert "ok" in passed["hinweise"]

    failed = ra.finalize_evidence(base, passed=False, gl_provenance=None)
    assert failed["status"] == ra.STATUS_FAILED
    assert failed["gl_provenance"] is None


def test_write_evidence_emits_json_and_manifest(tmp_path: Path) -> None:
    records = [ra.ArtifactRecord(name="a.dmg", sha256="cafe", bytes=7)]
    evidence = ra.build_evidence(
        "macos-arm64", "abc", {"art": "release-tag", "wert": "v2.7.0"}, records, ["note"],
    )
    ra.write_evidence(tmp_path, evidence)

    loaded = json.loads((tmp_path / "evidenz.json").read_text(encoding="utf-8"))
    assert loaded["platform"] == "macos-arm64"
    manifest = (tmp_path / "manifest.md").read_text(encoding="utf-8")
    assert "Abnahme-Evidenz: macos-arm64" in manifest
    assert "`cafe`" in manifest
    assert "> note" in manifest


def test_fetch_release_assets_filters_and_hashes(tmp_path: Path) -> None:
    payload = b"binary-artifact"
    expected = hashlib.sha256(payload).hexdigest()

    def fake_fetcher(request: urllib.request.Request) -> bytes:
        url = request.full_url
        if url.endswith("/releases/tags/v2.7.0"):
            return json.dumps(
                {
                    "assets": [
                        {"name": "BgRemover-2.7.0-macos-arm64-ai.dmg", "url": "https://x/1"},
                        {"name": "BgRemover-2.7.0-linux-x86_64-ai.deb", "url": "https://x/2"},
                    ]
                }
            ).encode("utf-8")
        return payload

    records = ra.fetch_release_assets(
        "owner/repo", "v2.7.0", "macos-arm64", tmp_path, None, fake_fetcher,
    )
    # Nur das macOS-Asset zählt.
    assert len(records) == 1
    assert records[0].name == "BgRemover-2.7.0-macos-arm64-ai.dmg"
    assert records[0].sha256 == expected
    assert (tmp_path / records[0].name).read_bytes() == payload


def test_fetch_release_assets_errors_when_platform_absent(tmp_path: Path) -> None:
    def fake_fetcher(request: urllib.request.Request) -> bytes:
        return json.dumps(
            {"assets": [{"name": "BgRemover-2.7.0-linux-x86_64-ai.deb", "url": "https://x/2"}]}
        ).encode("utf-8")

    with pytest.raises(SystemExit):
        ra.fetch_release_assets(
            "owner/repo", "v2.7.0", "macos-arm64", tmp_path, None, fake_fetcher,
        )


def test_fetch_run_artifacts_unzips_matching(tmp_path: Path) -> None:
    inner = b"the-appimage-bytes"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("BgRemover-2.7.0-linux-raspberrypi-arm64-ai.AppImage", inner)
    zip_bytes = buffer.getvalue()

    def fake_fetcher(request: urllib.request.Request) -> bytes:
        url = request.full_url
        if url.endswith("/artifacts"):
            return json.dumps(
                {
                    "artifacts": [
                        {
                            "name": "BgRemover-2.7.0-linux-raspberrypi-arm64-ai.AppImage",
                            "archive_download_url": "https://x/zip",
                        },
                        {
                            "name": "BgRemover-2.7.0-macos-arm64-ai.dmg",
                            "archive_download_url": "https://x/other",
                        },
                    ]
                }
            ).encode("utf-8")
        return zip_bytes

    records = ra.fetch_run_artifacts(
        "owner/repo", "12345", "linux-arm64", tmp_path, "token", fake_fetcher,
    )
    assert len(records) == 1
    assert records[0].sha256 == hashlib.sha256(inner).hexdigest()


def test_fetch_run_artifacts_requires_token(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        ra.fetch_run_artifacts(
            "owner/repo", "12345", "linux-arm64", tmp_path, None, lambda r: b"",
        )


def test_main_rejects_two_sources(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        ra.main(
            [
                "--platform", "macos-arm64",
                "--repo", "owner/repo",
                "--release-tag", "v2.7.0",
                "--source-run-id", "123",
                "--output", str(tmp_path),
            ]
        )


def test_main_writes_evidence_end_to_end(tmp_path: Path) -> None:
    payload = b"dmg-bytes"

    def fake_fetcher(request: urllib.request.Request) -> bytes:
        if request.full_url.endswith("/releases/tags/v2.7.0"):
            return json.dumps(
                {"assets": [{"name": "BgRemover-2.7.0-macos-arm64-ai.dmg", "url": "https://x/1"}]}
            ).encode("utf-8")
        return payload

    rc = ra.main(
        [
            "--platform", "macos-arm64",
            "--repo", "owner/repo",
            "--commit-sha", "abc123",
            "--release-tag", "v2.7.0",
            "--output", str(tmp_path),
        ],
        fetcher=fake_fetcher,
    )
    assert rc == 0
    loaded = json.loads((tmp_path / "evidenz.json").read_text(encoding="utf-8"))
    assert loaded["commit_sha"] == "abc123"
    assert loaded["artefakte"][0]["name"] == "BgRemover-2.7.0-macos-arm64-ai.dmg"
