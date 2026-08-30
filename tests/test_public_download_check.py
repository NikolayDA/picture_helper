"""Anonymer Öffentlichkeitsnachweis der Release-Assets (#916, Epic #914).

Der Nachweis ist nur dann einer, wenn er drei Dinge zugleich hält: Er läuft
ohne jeden ``Authorization``-Header, er vergleicht ausschließlich gegen das
Freigabemanifest, und er scheitert sichtbar statt still. Diese Tests binden
genau das fest — inklusive der Regel, dass die Evidenz auch im Fehlerfall
geschrieben wird.
"""
from __future__ import annotations

import hashlib
import http.server
import importlib.util
import json
import sys
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# release_contract zuerst: public_download_check importiert es als Modul.
rc = _load("release_contract")
pdc = _load("public_download_check")

VERSION = "2.9.1"
TAG = f"v{VERSION}"
REPO = "NikolayDA/picture_helper"
HEAD = "b" * 40
NAMES = rc.expected_artifact_names(VERSION, with_ai=True)


def _payloads() -> dict[str, bytes]:
    return {name: f"public-bytes-of-{name}".encode() for name in NAMES}


def _manifest(payloads: dict[str, bytes]) -> dict[str, Any]:
    return {
        "schema": rc.MANIFEST_SCHEMA,
        "kind": rc.MANIFEST_KIND,
        "candidate": {
            "run_id": 101,
            "head_sha": HEAD,
            "version": VERSION,
            "expected_tag": TAG,
        },
        "acceptance": {
            "run_id": 202,
            "approval_artifact_name": "release-approval-manifest-1",
        },
        "artifacts": [
            {
                "name": name,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "platform": rc.platform_for_artifact(name),
            }
            for name, payload in sorted(payloads.items())
        ],
    }


def _download_url(name: str) -> str:
    return f"https://github.com/{REPO}/releases/download/{TAG}/{name}"


def _release(names: tuple[str, ...] = NAMES, *, draft: bool = False) -> dict[str, Any]:
    return {
        "draft": draft,
        "html_url": f"https://github.com/{REPO}/releases/tag/{TAG}",
        "published_at": "2026-08-30T12:00:00Z",
        "assets": [
            {"name": name, "browser_download_url": _download_url(name)} for name in names
        ],
    }


class _Github:
    """Antwortet auf Metadaten- und Asset-Anfragen; protokolliert jede Anfrage."""

    def __init__(
        self,
        release: dict[str, Any],
        payloads: dict[str, bytes],
        *,
        failures: list[Exception] | None = None,
    ) -> None:
        self.release = release
        self.payloads = payloads
        self.failures = list(failures or [])
        self.requests: list[urllib.request.Request] = []

    def __call__(self, request: urllib.request.Request) -> bytes:
        self.requests.append(request)
        if self.failures:
            raise self.failures.pop(0)
        url = request.full_url
        if url.startswith(pdc.API_ROOT):
            return json.dumps(self.release).encode("utf-8")
        for name, payload in self.payloads.items():
            if url == _download_url(name):
                return payload
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)  # type: ignore[arg-type]


def _run(
    tmp_path: Path,
    fetcher: _Github,
    *,
    manifest: dict[str, Any] | None = None,
    tag: str = TAG,
    sleeps: list[float] | None = None,
) -> dict[str, Any]:
    manifest_path = tmp_path / "release-approval-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest if manifest is not None else _manifest(_payloads())),
        encoding="utf-8",
    )
    return pdc.run(
        manifest_path=manifest_path,
        repo=REPO,
        tag=tag,
        download_dir=tmp_path / "download",
        report_path=tmp_path / "evidence" / "public-download-report.json",
        markdown_path=tmp_path / "evidence" / "public-download-report.md",
        run_url="https://github.com/run/1",
        fetcher=fetcher,
        sleeper=(sleeps.append if sleeps is not None else lambda _seconds: None),
    )


def _report(tmp_path: Path) -> dict[str, Any]:
    return json.loads(
        (tmp_path / "evidence" / "public-download-report.json").read_text(encoding="utf-8")
    )


def test_report_documents_every_asset_and_confirms_byte_equality(tmp_path: Path) -> None:
    payloads = _payloads()
    report = _run(tmp_path, _Github(_release(), payloads))

    assert report["schema"] == pdc.REPORT_SCHEMA
    assert report["kind"] == pdc.REPORT_KIND
    assert report["verdict"] == "PASS"
    assert report["authenticated"] is False
    assert report["release"]["tag"] == TAG
    assert report["release"]["version"] == VERSION
    assert report["release"]["candidate_sha"] == HEAD
    assert report["reference"]["source"] == "release-approval-manifest"
    assert [item["name"] for item in report["assets"]] == sorted(NAMES)
    for asset in report["assets"]:
        payload = payloads[asset["name"]]
        assert asset["result"] == "PASS"
        assert asset["detail"] == ""
        assert asset["bytes"] == len(payload)
        assert asset["sha256"] == hashlib.sha256(payload).hexdigest()
        assert asset["url"] == _download_url(asset["name"])
        assert asset["downloaded_at"]
    assert _report(tmp_path) == report


def test_no_request_ever_carries_an_authorization_header(tmp_path: Path) -> None:
    """Ohne diese Zusage belegt der Nachweis nichts (#686/#916)."""
    fetcher = _Github(_release(), _payloads())
    _run(tmp_path, fetcher)

    assert len(fetcher.requests) == 1 + len(NAMES)
    for request in fetcher.requests:
        assert request.get_header("Authorization") is None
        assert not any(key.lower() == "authorization" for key in request.headers)
    payload_urls = {request.full_url for request in fetcher.requests[1:]}
    assert payload_urls == {_download_url(name) for name in NAMES}


def test_public_download_uses_only_manifest_hashes_as_reference(tmp_path: Path) -> None:
    """Referenz ist das Freigabemanifest, nie ein von GitHub gemeldeter Digest."""
    payloads = _payloads()
    tampered = dict(payloads)
    victim = sorted(NAMES)[0]
    # Gleiche Laenge, andere Bytes: erzwingt den Hash-Befund statt des Groessen-Befunds.
    tampered[victim] = b"x" * len(payloads[victim])
    release = _release()
    # Selbst ein "passender" Anbieter-Digest darf den Befund nicht aufweichen.
    for asset in release["assets"]:
        asset["digest"] = "sha256:" + hashlib.sha256(tampered[asset["name"]]).hexdigest()

    with pytest.raises(pdc.PublicDownloadError, match="SHA-256 weicht ab"):
        _run(tmp_path, _Github(release, tampered), manifest=_manifest(payloads))

    report = _report(tmp_path)
    assert report["verdict"] == "FAIL"
    findings = {item["name"]: item for item in report["assets"] if item["result"] != "PASS"}
    assert set(findings) == {victim}
    assert findings[victim]["detail"] == "SHA-256 weicht ab"
    assert findings[victim]["sha256"] != findings[victim]["expected_sha256"]


def test_missing_public_asset_blocks_and_stays_visible_in_the_report(tmp_path: Path) -> None:
    payloads = _payloads()
    incomplete = tuple(sorted(NAMES)[1:])

    with pytest.raises(pdc.PublicDownloadError, match="fehlend="):
        _run(tmp_path, _Github(_release(incomplete), payloads))

    report = _report(tmp_path)
    assert report["verdict"] == "FAIL"
    assert "fehlend=" in report["error"]
    assert {item["result"] for item in report["assets"]} == {"MISSING"}


def test_unexpected_public_asset_blocks(tmp_path: Path) -> None:
    payloads = _payloads()
    payloads["BgRemover-2.9.1-windows-x86_64.exe"] = b"nicht-teil-des-vertrags"

    with pytest.raises(pdc.PublicDownloadError, match="zusaetzlich="):
        _run(
            tmp_path,
            _Github(_release(tuple(sorted(payloads))), payloads),
            manifest=_manifest(_payloads()),
        )
    assert _report(tmp_path)["verdict"] == "FAIL"


def test_draft_release_is_never_accepted_as_public(tmp_path: Path) -> None:
    with pytest.raises(pdc.PublicDownloadError, match="Draft"):
        _run(tmp_path, _Github(_release(draft=True), _payloads()))
    assert _report(tmp_path)["verdict"] == "FAIL"


def test_http_error_fails_visibly_and_is_not_polled_away(tmp_path: Path) -> None:
    """Eine 404 (privates/fehlendes Release) ist ein Befund, kein Flake."""
    error = urllib.error.HTTPError(
        f"{pdc.API_ROOT}/repos/{REPO}/releases/tags/{TAG}", 404, "Not Found", {}, None
    )
    fetcher = _Github(_release(), _payloads(), failures=[error])
    sleeps: list[float] = []

    with pytest.raises(pdc.PublicDownloadError, match="HTTP 404"):
        _run(tmp_path, fetcher, sleeps=sleeps)

    assert sleeps == []
    assert len(fetcher.requests) == 1
    report = _report(tmp_path)
    assert report["verdict"] == "FAIL"
    assert "HTTP 404" in report["error"]
    # Beide plausiblen Ursachen benennen, statt einen Kontingent-Treffer wie
    # einen Releasefehler aussehen zu lassen.
    assert "nicht oeffentlich" in report["error"]
    assert "API-Kontingent" in report["error"]


def test_transient_answers_are_retried_within_a_bounded_window(tmp_path: Path) -> None:
    failures: list[Exception] = [
        urllib.error.HTTPError("https://example.invalid", 503, "Service Unavailable", {}, None),
        urllib.error.URLError("connection reset"),
    ]
    fetcher = _Github(_release(), _payloads(), failures=failures)
    sleeps: list[float] = []

    report = _run(tmp_path, fetcher, sleeps=sleeps)

    assert report["verdict"] == "PASS"
    assert sleeps == list(pdc.RETRY_DELAYS_S)
    assert len(fetcher.requests) == 1 + 2 + len(NAMES)


def test_persistent_transient_failure_still_ends_the_run(tmp_path: Path) -> None:
    failures: list[Exception] = [urllib.error.URLError("timeout") for _ in range(9)]
    fetcher = _Github(_release(), _payloads(), failures=failures)

    with pytest.raises(pdc.PublicDownloadError, match="anonym abrufen"):
        _run(tmp_path, fetcher)
    assert len(fetcher.requests) == pdc.DEFAULT_ATTEMPTS


def test_tag_must_match_the_pinned_manifest_before_any_request(tmp_path: Path) -> None:
    fetcher = _Github(_release(), _payloads())
    with pytest.raises(pdc.PublicDownloadError, match="weicht vom Freigabemanifest ab"):
        _run(tmp_path, fetcher, tag="v9.9.9")
    assert fetcher.requests == []


def test_markdown_renders_verdict_all_assets_and_the_incident_hint(tmp_path: Path) -> None:
    payloads = _payloads()
    _run(tmp_path, _Github(_release(), payloads))
    passed = (tmp_path / "evidence" / "public-download-report.md").read_text(encoding="utf-8")

    assert "PUBLIC-DOWNLOAD-01" in passed
    assert "bestanden" in passed
    assert "ohne `Authorization`-Header" in passed
    for name in NAMES:
        assert name in passed
        assert hashlib.sha256(payloads[name]).hexdigest() in passed

    failing = dict(payloads)
    victim = sorted(NAMES)[0]
    failing[victim] = b"y" * len(payloads[victim])
    other = tmp_path / "failing"
    other.mkdir()
    with pytest.raises(pdc.PublicDownloadError):
        _run(other, _Github(_release(), failing), manifest=_manifest(payloads))
    text = (other / "evidence" / "public-download-report.md").read_text(encoding="utf-8")
    assert "fehlgeschlagen" in text
    assert "### Befunde" in text
    assert "Rollback und Teilzustände" in text


def test_cli_reports_exit_code_two_on_a_failed_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payloads = _payloads()
    manifest_path = tmp_path / "release-approval-manifest.json"
    manifest_path.write_text(json.dumps(_manifest(payloads)), encoding="utf-8")
    tampered = dict(payloads)
    tampered[sorted(NAMES)[0]] = b"ersetzt"
    monkeypatch.setattr(pdc, "_default_fetcher", _Github(_release(), tampered))
    monkeypatch.setattr(pdc.time, "sleep", lambda _seconds: None)

    argv = [
        "--manifest", str(manifest_path),
        "--repo", REPO,
        "--tag", TAG,
        "--download-dir", str(tmp_path / "download"),
        "--report", str(tmp_path / "evidence" / "public-download-report.json"),
        "--markdown", str(tmp_path / "evidence" / "public-download-report.md"),
    ]
    assert pdc.main(argv) == 2
    assert "::error title=PUBLIC-DOWNLOAD-01::" in capsys.readouterr().err
    assert _report(tmp_path)["verdict"] == "FAIL"


def test_cli_succeeds_on_a_clean_public_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payloads = _payloads()
    manifest_path = tmp_path / "release-approval-manifest.json"
    manifest_path.write_text(json.dumps(_manifest(payloads)), encoding="utf-8")
    monkeypatch.setattr(pdc, "_default_fetcher", _Github(_release(), payloads))

    assert (
        pdc.main(
            [
                "--manifest", str(manifest_path),
                "--repo", REPO,
                "--tag", TAG,
                "--download-dir", str(tmp_path / "download"),
                "--report", str(tmp_path / "evidence" / "public-download-report.json"),
            ]
        )
        == 0
    )
    assert _report(tmp_path)["verdict"] == "PASS"


def test_downloaded_bytes_pass_the_same_verify_artifacts_gate(tmp_path: Path) -> None:
    """Der Publish-Workflow prueft dasselbe Verzeichnis noch einmal mit dem Vertrag."""
    payloads = _payloads()
    manifest = _manifest(payloads)
    _run(tmp_path, _Github(_release(), payloads), manifest=manifest)
    rc.verify_artifact_directory(manifest, tmp_path / "download")


class _RecordingServer(http.server.BaseHTTPRequestHandler):
    received: dict[str, str] = {}

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler-Vertrag
        type(self).received = {key.lower(): value for key, value in self.headers.items()}
        body = b"echte-bytes-ueber-die-leitung"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:
        pass


@pytest.fixture
def _local_server() -> Iterator[str]:
    server = http.server.HTTPServer(("127.0.0.1", 0), _RecordingServer)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/asset"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_real_transport_puts_no_authorization_on_the_wire(
    _local_server: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nicht nur das Request-Objekt: was tatsaechlich gesendet wird, zaehlt."""
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    _RecordingServer.received = {}

    payload = pdc._default_fetcher(
        pdc.anonymous_request(_local_server, "application/octet-stream")
    )

    assert payload == b"echte-bytes-ueber-die-leitung"
    assert "authorization" not in _RecordingServer.received
    assert _RecordingServer.received["user-agent"] == pdc.USER_AGENT
