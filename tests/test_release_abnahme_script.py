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


def test_default_fetcher_strips_auth_header_on_cross_host_redirect() -> None:
    # Regression: GitHub-Artefakt-/Asset-Downloads redirecten auf signierte
    # Blob-Storage-URLs; ein weitergereichter Authorization-Header lässt den
    # Blob-Store dort mit 401 scheitern (live auf dem macOS-Runner beobachtet).
    handler = ra._StripAuthOnRedirect()
    original = urllib.request.Request(
        "https://api.github.com/repos/o/r/actions/artifacts/1/zip",
        headers={"Authorization": "Bearer secret-token", "Accept": "application/vnd.github+json"},
    )
    redirected = handler.redirect_request(
        original, None, 302, "Found", None,
        "https://example.blob.core.windows.net/artifacts/1.zip?sig=abc",
    )
    assert redirected is not None
    assert not redirected.has_header("Authorization")
    # Andere Header bleiben erhalten, nur Authorization wird entfernt.
    assert redirected.has_header("Accept")


def test_default_fetcher_keeps_auth_header_on_same_host_redirect() -> None:
    # Bleibt der Redirect auf demselben Host (z. B. api.github.com nach einer
    # Repo-Umbenennung), muss der Token erhalten bleiben – sonst scheitern
    # private Downloads dort unautorisiert (Codex-Review zu PR #654).
    handler = ra._StripAuthOnRedirect()
    original = urllib.request.Request(
        "https://api.github.com/repos/o/old-name/releases/assets/1",
        headers={"Authorization": "Bearer secret-token"},
    )
    redirected = handler.redirect_request(
        original, None, 301, "Moved Permanently", None,
        "https://api.github.com/repos/o/new-name/releases/assets/1",
    )
    assert redirected is not None
    assert redirected.has_header("Authorization")


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
    # #642-Nachtrag: das Feld muss von Anfang an vorhanden sein (nie fehlend).
    assert evidence["waechter_ergebnisse"] == []


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


def test_finalize_evidence_carries_structured_guard_results() -> None:
    """#642-Nachtrag: Wächter-Ergebnisse (Exit-Code/Peak-Instanzen/Status/Log je
    Startphase und Artefaktklasse) müssen strukturiert in die Evidenz übernommen
    werden, nicht nur als Freitext-Notiz."""
    records = [ra.ArtifactRecord(name="a.AppImage", sha256="cafe", bytes=7)]
    base = ra.build_evidence(
        "linux-arm64", "abc", {"art": "release-tag", "wert": "v2.7.0"}, records, [],
    )
    guard_results = [
        {
            "phase": "start", "artefaktklasse": "appimage", "exit_code": 0,
            "peak_instanzen": 1, "status": "ok", "log": "smoke_launch OK",
        },
        {
            "phase": "nativer_3d_screenshot", "artefaktklasse": "appimage", "exit_code": 0,
            "peak_instanzen": 1, "status": "ok", "log": "smoke_launch OK",
        },
    ]
    finalized = ra.finalize_evidence(
        base, passed=True, gl_provenance="Broadcom / V3D 7.1 / 3.1",
        guard_results=guard_results,
    )
    assert finalized["waechter_ergebnisse"] == guard_results

    # Ohne Angabe bleibt das Feld eine leere Liste statt zu fehlen.
    without = ra.finalize_evidence(base, passed=True, gl_provenance="x")
    assert without["waechter_ergebnisse"] == []


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


def test_write_evidence_includes_guard_results_table_when_present(tmp_path: Path) -> None:
    records = [ra.ArtifactRecord(name="a.AppImage", sha256="cafe", bytes=7)]
    evidence = ra.build_evidence(
        "linux-arm64", "abc", {"art": "release-tag", "wert": "v2.7.0"}, records, [],
    )
    finalized = ra.finalize_evidence(
        evidence, passed=True, gl_provenance="Broadcom / V3D 7.1 / 3.1",
        guard_results=[{
            "phase": "start", "artefaktklasse": "appimage", "exit_code": 0,
            "peak_instanzen": 1, "status": "ok", "log": "smoke_launch OK",
        }],
    )
    ra.write_evidence(tmp_path, finalized)
    manifest = (tmp_path / "manifest.md").read_text(encoding="utf-8")
    assert "| Phase | Artefaktklasse | Status | Exit-Code | Peak-Instanzen |" in manifest
    assert "| start | appimage | ok | 0 | 1 |" in manifest


def test_write_evidence_omits_guard_results_table_when_empty(tmp_path: Path) -> None:
    records = [ra.ArtifactRecord(name="a.AppImage", sha256="cafe", bytes=7)]
    evidence = ra.build_evidence(
        "linux-arm64", "abc", {"art": "release-tag", "wert": "v2.7.0"}, records, [],
    )
    ra.write_evidence(tmp_path, evidence)
    manifest = (tmp_path / "manifest.md").read_text(encoding="utf-8")
    assert "Artefaktklasse" not in manifest


def test_fetch_release_assets_filters_and_hashes(tmp_path: Path) -> None:
    payload = b"binary-artifact"
    expected = hashlib.sha256(payload).hexdigest()

    def fake_fetcher(request: urllib.request.Request) -> bytes:
        url = request.full_url
        if url.endswith("/releases/tags/v2.7.0"):
            return json.dumps(
                {
                    "assets": [
                        {
                            "name": "BgRemover-2.7.0-macos-arm64-ai.dmg",
                            "url": "https://api.x/1",
                            "browser_download_url": "https://dl.x/1",
                        },
                        {
                            "name": "BgRemover-2.7.0-linux-x86_64-ai.deb",
                            "url": "https://api.x/2",
                            "browser_download_url": "https://dl.x/2",
                        },
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


def test_fetch_release_assets_downloads_anonymously_from_public_url(tmp_path: Path) -> None:
    """#686: Die Nutzlast muss über ``browser_download_url`` **ohne** Token
    kommen – nur das belegt „Download über die öffentliche Release-Seite ohne
    Maintainer-Sitzung". Der vorherige Bezug über die authentifizierte
    REST-Asset-URL hätte ein versehentlich privat gebliebenes Release
    anstandslos durchgewinkt. Die Metadaten dürfen weiterhin authentifiziert
    geholt werden – sie sind die Vertrauenswurzel für den Digest-Abgleich."""
    payload = b"binary-artifact"
    seen: list[tuple[str, str | None]] = []

    def fake_fetcher(request: urllib.request.Request) -> bytes:
        seen.append((request.full_url, request.get_header("Authorization")))
        if request.full_url.endswith("/releases/tags/v2.7.1"):
            return json.dumps({"assets": [{
                "name": "BgRemover-2.7.1-macos-arm64-ai.dmg",
                "url": "https://api.github.com/…/assets/1",
                "browser_download_url": "https://github.com/o/r/releases/download/v2.7.1/x.dmg",
            }]}).encode("utf-8")
        return payload

    ra.fetch_release_assets(
        "o/r", "v2.7.1", "macos-arm64", tmp_path, "geheimes-token", fake_fetcher,
    )

    metadata_url, metadata_auth = seen[0]
    download_url, download_auth = seen[1]
    assert metadata_url.endswith("/releases/tags/v2.7.1")
    assert metadata_auth == "Bearer geheimes-token"
    assert download_url.startswith("https://github.com/o/r/releases/download/")
    assert download_auth is None
    # Die authentifizierte Asset-URL darf gar nicht mehr angefragt werden.
    assert not any("/assets/1" in url for url, _ in seen)


def test_evidence_marks_assets_without_a_usable_digest_as_unverified(tmp_path: Path) -> None:
    """Codex-P2 (#734): ``verify_digest`` lässt Assets ohne prüfbaren
    ``sha256:``-Digest bewusst durch. Die Evidenz darf dann **nicht** behaupten,
    der anonym geladene Inhalt sei gegen die Assetliste bestätigt worden –
    sonst steht in der Release-Evidenz eine Prüfung, die nie stattgefunden hat."""
    payload = b"dmg-bytes"

    def fake_fetcher(request: urllib.request.Request) -> bytes:
        if request.full_url.endswith("/releases/tags/v2.7.1"):
            return json.dumps({"assets": [{
                "name": "BgRemover-2.7.1-macos-arm64-ai.dmg",
                "url": "https://api.x/1",
                "browser_download_url": "https://dl.x/1",
                # kein "digest" – GitHub liefert ihn nicht immer
            }]}).encode("utf-8")
        return payload

    rc = ra.main(
        [
            "--platform", "macos-arm64", "--repo", "o/r", "--commit-sha", "abc",
            "--release-tag", "v2.7.1", "--output", str(tmp_path),
        ],
        fetcher=fake_fetcher,
    )
    assert rc == 0
    loaded = json.loads((tmp_path / "evidenz.json").read_text(encoding="utf-8"))
    assert loaded["artefakte"][0]["digest_geprueft"] is False
    hinweise = " ".join(loaded["hinweise"])
    assert "OHNE unabhängige Digest-Bestätigung" in hinweise
    assert "bestätigt." not in hinweise.replace("OHNE unabhängige Digest-Bestätigung", "")
    assert "nein" in (tmp_path / "manifest.md").read_text(encoding="utf-8")


def test_evidence_confirms_digest_when_the_release_supplies_one(tmp_path: Path) -> None:
    """Gegenprobe: Mit prüfbarem Digest darf die Evidenz die Bestätigung auch
    aussprechen – sonst wäre die Notiz nutzlos vorsichtig."""
    payload = b"dmg-bytes"
    digest = hashlib.sha256(payload).hexdigest()

    def fake_fetcher(request: urllib.request.Request) -> bytes:
        if request.full_url.endswith("/releases/tags/v2.7.1"):
            return json.dumps({"assets": [{
                "name": "BgRemover-2.7.1-macos-arm64-ai.dmg",
                "url": "https://api.x/1",
                "browser_download_url": "https://dl.x/1",
                "digest": f"sha256:{digest}",
            }]}).encode("utf-8")
        return payload

    ra.main(
        [
            "--platform", "macos-arm64", "--repo", "o/r", "--commit-sha", "abc",
            "--release-tag", "v2.7.1", "--output", str(tmp_path),
        ],
        fetcher=fake_fetcher,
    )
    loaded = json.loads((tmp_path / "evidenz.json").read_text(encoding="utf-8"))
    assert loaded["artefakte"][0]["digest_geprueft"] is True
    hinweise = " ".join(loaded["hinweise"])
    assert "OHNE unabhängige Digest-Bestätigung" not in hinweise
    assert "gegen den Digest der" in hinweise


def test_has_usable_digest_is_the_shared_rule() -> None:
    """Geteilte Regel für ``verify_digest`` und die Evidenz-Notiz – zwei
    getrennte Implementierungen würden auseinanderlaufen."""
    assert ra.has_usable_digest("sha256:abc")
    assert not ra.has_usable_digest(None)
    assert not ra.has_usable_digest("")
    assert not ra.has_usable_digest("md5:abc")
    assert not ra.has_usable_digest("sha256:")


def test_version_from_artifact_name() -> None:
    """Sollwert für die sichtbare Produktversion (#686)."""
    assert ra.version_from_artifact_name("BgRemover-2.7.1-linux-x86_64-ai.deb") == "2.7.1"
    assert ra.version_from_artifact_name("BgRemover-10.0.3-macos-arm64-ai.dmg") == "10.0.3"
    # Fremdes Schema → None statt geraten (der Aufrufer prüft dann ohne Sollwert).
    assert ra.version_from_artifact_name("coverage-html.zip") is None
    assert ra.version_from_artifact_name("BgRemover-linux-x86_64-ai.deb") is None


def test_verify_digest_matches_and_rejects() -> None:
    computed = hashlib.sha256(b"x").hexdigest()
    # Kein/ungültiger Digest → keine Ausnahme (nur protokolliert).
    ra.verify_digest("a", computed, None)
    ra.verify_digest("a", computed, "md5:whatever")
    # Passender sha256-Digest → ok.
    ra.verify_digest("a", computed, f"sha256:{computed}")
    # Mismatch → harter Abbruch.
    with pytest.raises(SystemExit):
        ra.verify_digest("a", computed, "sha256:deadbeef")


def test_fetch_release_assets_verifies_trusted_digest(tmp_path: Path) -> None:
    payload = b"binary-artifact"
    good = hashlib.sha256(payload).hexdigest()

    def make_fetcher(digest: str):  # type: ignore[no-untyped-def]
        def fetcher(request: urllib.request.Request) -> bytes:
            if request.full_url.endswith("/releases/tags/v2.7.0"):
                return json.dumps(
                    {"assets": [{
                        "name": "BgRemover-2.7.0-macos-arm64-ai.dmg",
                        "url": "https://api.x/1",
                        "browser_download_url": "https://dl.x/1",
                        "digest": digest,
                    }]}
                ).encode("utf-8")
            return payload
        return fetcher

    # Passender Digest → ok.
    records = ra.fetch_release_assets(
        "o/r", "v2.7.0", "macos-arm64", tmp_path, None, make_fetcher(f"sha256:{good}"),
    )
    assert records[0].sha256 == good
    # Manipulierter Digest → Abbruch.
    with pytest.raises(SystemExit):
        ra.fetch_release_assets(
            "o/r", "v2.7.0", "macos-arm64", tmp_path, None, make_fetcher("sha256:dead"),
        )


def test_fetch_release_assets_errors_when_platform_absent(tmp_path: Path) -> None:
    def fake_fetcher(request: urllib.request.Request) -> bytes:
        return json.dumps(
            {"assets": [{
                "name": "BgRemover-2.7.0-linux-x86_64-ai.deb",
                "url": "https://api.x/2",
                "browser_download_url": "https://dl.x/2",
            }]}
        ).encode("utf-8")

    with pytest.raises(SystemExit):
        ra.fetch_release_assets(
            "owner/repo", "v2.7.0", "macos-arm64", tmp_path, None, fake_fetcher,
        )


def test_fetch_run_artifacts_unzips_only_the_product_container(tmp_path: Path) -> None:
    """Artefaktcontainer heissen ``bgremover-<platform_tag>``, nicht wie die Dateien.

    Seit #920 laedt derselbe Kandidatenlauf zusaetzlich
    ``security-scan-<platform_tag>`` hoch. Ein Teilstring-Vergleich auf den
    Plattform-Tag wuerde Bericht, Job-Summary und Phasen-Logs als
    Produktartefakte in die Abnahme-Evidenz ziehen – deshalb ist der
    Containername exakt zu treffen.
    """
    inner = b"the-appimage-bytes"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("BgRemover-2.7.0-linux-raspberrypi-arm64-ai.AppImage", inner)
    zip_bytes = buffer.getvalue()
    fetched: list[str] = []

    def fake_fetcher(request: urllib.request.Request) -> bytes:
        url = request.full_url
        if url.endswith("/artifacts"):
            return json.dumps(
                {
                    "artifacts": [
                        {
                            "name": "bgremover-linux-raspberrypi-arm64",
                            "archive_download_url": "https://x/zip",
                        },
                        {
                            "name": "security-scan-linux-raspberrypi-arm64",
                            "archive_download_url": "https://x/security",
                        },
                        {
                            "name": "bgremover-macos-arm64",
                            "archive_download_url": "https://x/other",
                        },
                    ]
                }
            ).encode("utf-8")
        fetched.append(url)
        return zip_bytes

    records = ra.fetch_run_artifacts(
        "owner/repo", "12345", "linux-arm64", tmp_path, "token", fake_fetcher,
    )
    assert fetched == ["https://x/zip"]
    assert len(records) == 1
    assert records[0].sha256 == hashlib.sha256(inner).hexdigest()


def test_fetch_run_artifacts_fails_closed_without_the_product_container(tmp_path: Path) -> None:
    """Nur der Sicherheitsbericht da? Dann fehlt das Produkt – kein Weiterlaufen."""
    def fake_fetcher(request: urllib.request.Request) -> bytes:
        assert request.full_url.endswith("/artifacts")
        return json.dumps(
            {
                "artifacts": [
                    {
                        "name": "security-scan-linux-raspberrypi-arm64",
                        "archive_download_url": "https://x/security",
                    }
                ]
            }
        ).encode("utf-8")

    with pytest.raises(SystemExit, match="bgremover-linux-raspberrypi-arm64"):
        ra.fetch_run_artifacts(
            "owner/repo", "12345", "linux-arm64", tmp_path, "token", fake_fetcher,
        )


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
                {"assets": [{
                    "name": "BgRemover-2.7.0-macos-arm64-ai.dmg",
                    "url": "https://api.x/1",
                    "browser_download_url": "https://dl.x/1",
                }]}
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
