"""Tests für den Secret-/Entwicklerpfad-Scan gebauter Release-Artefakte (#584).

Deckt insbesondere die Codex-Review-Befunde auf PR #608 ab: Geheimnisse
dürfen nicht im Klartext geloggt werden (nur Fingerprint), komprimierte
Nutzdaten (AppImage/`.deb`/`.dmg`) müssen vor dem Scan entpackt werden, und
ein unbekannter Entwicklerpfad muss den Scan hart fehlschlagen lassen.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "scripts" / "scan_release_artifacts.py"

_spec = importlib.util.spec_from_file_location("scan_release_artifacts", _SCRIPT)
assert _spec is not None and _spec.loader is not None
scan_release_artifacts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scan_release_artifacts)

_AWS_KEY = b"AKIAIOSFODNN7EXAMPLE"  # oeffentliches AWS-Beispiel, kein echtes Secret.

pytestmark = pytest.mark.skipif(
    shutil.which("dpkg-deb") is None, reason="dpkg-deb not available"
)


def _build_deb(stage: Path, out: Path, payload_files: dict[str, bytes]) -> None:
    """Baut ein reales .deb (nur fuer Tests) mit den gegebenen Nutzdateien."""
    (stage / "DEBIAN").mkdir(parents=True, exist_ok=True)
    (stage / "DEBIAN" / "control").write_text(
        "Package: test\nVersion: 1.0\nArchitecture: amd64\n"
        "Maintainer: test <test@example.com>\nDescription: test\n"
    )
    for rel, content in payload_files.items():
        target = stage / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    subprocess.run(
        ["dpkg-deb", "--build", "--root-owner-group", str(stage), str(out)],
        check=True, capture_output=True,
    )


def test_script_exists() -> None:
    assert _SCRIPT.is_file()


# ── scan_bytes: Muster-Erkennung ohne Geheimnis-Leck ins Log ────────────

def test_scan_bytes_clean_data_has_no_findings() -> None:
    assert scan_release_artifacts.scan_bytes(b"just a harmless blob") == []


def test_scan_bytes_detects_aws_access_key() -> None:
    findings = scan_release_artifacts.scan_bytes(b"...%s..." % _AWS_KEY)
    assert any("AWS Access Key ID" in f for f in findings)


def test_scan_bytes_finding_never_contains_the_raw_secret() -> None:
    """Codex P1: das Log darf das Geheimnis nicht im Klartext enthalten."""
    findings = scan_release_artifacts.scan_bytes(b"token=%s" % _AWS_KEY)
    joined = " ".join(findings)
    assert _AWS_KEY.decode() not in joined
    assert "Fingerprint" in joined
    assert "Position" in joined


def test_scan_bytes_detects_github_token() -> None:
    findings = scan_release_artifacts.scan_bytes(b"ghp_" + b"a1b2c3" * 7)
    assert any("GitHub-Token" in f for f in findings)


def test_scan_bytes_detects_pem_private_key() -> None:
    body = b"MIIEowIBAAKCAQEA1234567890abcdefABCDEF" * 3
    findings = scan_release_artifacts.scan_bytes(
        b"-----BEGIN RSA PRIVATE KEY-----\n%s\n-----END RSA PRIVATE KEY-----" % body
    )
    assert any("PEM-Schlüssel" in f for f in findings)


def test_scan_bytes_ignores_pem_header_without_key_body() -> None:
    """Codex-Nachbesserung (#608): OpenSSLs eigene, in Qt6/libqopensslbackend
    einkompilierte Typtabelle listet alle PEM-Kopfzeilen als NUL-separierte
    Strings ohne jeden Schluesselkoerper – das darf nicht als Fund gelten
    (empirisch aus den echten PyQt6-Qt6-Binaries nachgebildet)."""
    findings = scan_release_artifacts.scan_bytes(
        b"-----BEGIN PRIVATE KEY-----\x00-----END PUBLIC KEY-----"
        b"\x00-----END RSA PRIVATE KEY-----\x00-----END DSA PRIVATE KEY-----"
    )
    assert findings == []


def test_scan_bytes_pem_header_followed_by_short_garbage_is_ignored() -> None:
    findings = scan_release_artifacts.scan_bytes(b"-----BEGIN EC PRIVATE KEY-----\x00\x00abc")
    assert findings == []


def test_scan_bytes_finds_every_occurrence_not_just_the_first() -> None:
    """Ein frueherer Treffer (z. B. ein zugelassener Fehlalarm) darf einen
    zweiten, andersartigen Fund desselben Musters nicht verdecken (#608:
    reale CI-Artefakte zeigten mehrere unabhaengige Treffer pro Muster)."""
    other_key = b"AKIAZZZZZZZZZZZZZZZZ"
    assert other_key != _AWS_KEY
    findings = scan_release_artifacts.scan_bytes(b"%s ... %s" % (_AWS_KEY, other_key))
    fingerprints = {f.split("Fingerprint ")[1].rstrip(")") for f in findings}
    assert len(fingerprints) == 2


def test_scan_bytes_deduplicates_repeated_identical_matches() -> None:
    findings = scan_release_artifacts.scan_bytes(b"%s ... %s" % (_AWS_KEY, _AWS_KEY))
    assert len(findings) == 1


def test_scan_bytes_ignores_aws_key_embedded_mid_identifier() -> None:
    """Codex-Nachbesserung (#608): Pillows ``PIL/ImageFont.py`` enthaelt eine
    Base64-kodierte Schriftmetrik-Tabelle, in der "AKIA" + 16 passende Zeichen
    zufaellig vorkommt – aber eingebettet mitten in einem laengeren
    Base64-Lauf, nie als eigenstaendiger Wert. Ein echter Schluessel steht
    immer freistehend (Anfuehrungszeichen/Gleichheitszeichen/Leerraum davor
    und danach)."""
    findings = scan_release_artifacts.scan_bytes(b"AwAaAKIAAQAAAAAABAAHAM0AAQAAAAAABQA8AU8AAQAA")
    assert findings == []


def test_scan_bytes_ignores_github_token_embedded_mid_identifier() -> None:
    """Codex-Nachbesserung (#608): scipys HiGHS-Solver-Bindung
    (``scipy/optimize/_highspy/_core*.so``) benennt jede exportierte
    C-API-Funktion "Highs_...", was im C++-Mangling "ghs_..." als
    Teilzeichenkette ergibt – bei 43 verschiedenen Funktionsnamen in
    derselben Datei ist ein Fingerprint-Allowlist-Eintrag pro Symbol nicht
    wartbar. Die Wortgrenzen-Anker greifen strukturell fuer die gesamte
    Namensfamilie."""
    findings = scan_release_artifacts.scan_bytes(
        b"hi" + b"ghs_setCallbackP5HighsSt8functionIFviRKNSt7"
    )
    assert findings == []


def test_scan_bytes_detects_github_token_with_realistic_boundaries() -> None:
    """Ein echtes Token in typischem Kontext (z. B. in JSON gequotet) muss
    trotz der Wortgrenzen-Anker weiterhin erkannt werden."""
    findings = scan_release_artifacts.scan_bytes(b'{"token": "ghp_' + b"a1b2c3" * 7 + b'"}')
    assert any("GitHub-Token" in f for f in findings)


# ── dev_path_users: Allowlist ────────────────────────────────────────────

def test_dev_path_users_allows_known_ci_and_build_infra_users() -> None:
    data = (
        b"/home/runner/work/x /Users/default/Desktop "
        b"/home/qt/work/qt/qtbase /root/build"
    )
    assert scan_release_artifacts.dev_path_users(data) == set()


def test_dev_path_users_flags_unknown_user() -> None:
    assert scan_release_artifacts.dev_path_users(b"/Users/alice/dev/project") == {"alice"}


# ── extract_payload: reales .deb (echtes dpkg-deb) ───────────────────────

def test_extract_payload_deb_recovers_compressed_payload(tmp_path: Path) -> None:
    """Codex P2: ein Secret in einer normalen Payload-Datei darf nicht durch
    die .deb-Kompression verdeckt werden."""
    stage = tmp_path / "stage"
    deb = tmp_path / "test.deb"
    _build_deb(stage, deb, {"opt/test/secret.txt": _AWS_KEY})

    # Die rohen .deb-Bytes enthalten das Secret NICHT im Klartext (komprimiert).
    assert _AWS_KEY not in deb.read_bytes()

    dest = tmp_path / "out"
    scan_release_artifacts.extract_payload(deb, dest)
    extracted = dest / "opt" / "test" / "secret.txt"
    assert extracted.is_file()
    assert extracted.read_bytes() == _AWS_KEY


def test_extract_payload_unknown_suffix_raises(tmp_path: Path) -> None:
    stray = tmp_path / "stray.bin"
    stray.write_bytes(b"nothing")
    with pytest.raises(ValueError, match="unbekanntes Artefaktformat"):
        scan_release_artifacts.extract_payload(stray, tmp_path / "out")


# ── extract_payload: AppImage/.dmg über gemockte Subprozesse ────────────
# (Weder ein echtes AppImage-Runtime noch macOS/hdiutil sind in dieser
# Sandbox verfuegbar; die Orchestrierung wird an der Subprozess-Grenze
# getestet, ``dpkg-deb`` bleibt echt.)

def test_extract_payload_appimage_invokes_extract_flag(tmp_path, monkeypatch) -> None:
    appimage = tmp_path / "Fake-ai.AppImage"
    appimage.write_bytes(b"#!/bin/sh\nexit 0\n")
    calls = []

    def fake_run(cmd, check=True, capture_output=True, **kwargs):
        calls.append((cmd, kwargs.get("cwd")))
        cwd = Path(kwargs["cwd"])
        (cwd / "squashfs-root").mkdir(parents=True, exist_ok=True)
        (cwd / "squashfs-root" / "embedded.txt").write_bytes(_AWS_KEY)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", fake_run)
    dest = tmp_path / "out"
    scan_release_artifacts.extract_payload(appimage, dest)

    assert len(calls) == 1
    cmd, cwd = calls[0]
    assert cmd[-1] == "--appimage-extract"
    assert Path(cwd) == dest
    assert (dest / "squashfs-root" / "embedded.txt").read_bytes() == _AWS_KEY


def test_extract_payload_deb_recurses_into_wrapped_appimage(tmp_path, monkeypatch) -> None:
    """Eine in der .deb gewrappte AppImage wird ebenfalls entpackt (#584)."""
    real_run = subprocess.run

    def fake_run(cmd, check=True, capture_output=True, **kwargs):
        if cmd[0] == "dpkg-deb":
            return real_run(cmd, check=check, capture_output=capture_output, **kwargs)
        assert cmd[-1] == "--appimage-extract"
        cwd = Path(kwargs["cwd"])
        (cwd / "squashfs-root").mkdir(parents=True, exist_ok=True)
        (cwd / "squashfs-root" / "site-packages.txt").write_bytes(_AWS_KEY)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", fake_run)

    stage = tmp_path / "stage"
    deb = tmp_path / "wrapper.deb"
    _build_deb(stage, deb, {"opt/BgRemover/BgRemover.AppImage": b"#!/bin/sh\nexit 0\n"})

    dest = tmp_path / "out"
    scan_release_artifacts.extract_payload(deb, dest)

    nested = (
        dest / "opt" / "BgRemover" / "BgRemover.AppImage.extracted"
        / "squashfs-root" / "site-packages.txt"
    )
    assert nested.read_bytes() == _AWS_KEY


def test_extract_payload_dmg_mounts_copies_and_always_detaches(tmp_path, monkeypatch) -> None:
    dmg = tmp_path / "Fake.dmg"
    dmg.write_bytes(b"not a real dmg")
    detach_calls = []

    def fake_run(cmd, check=True, capture_output=True, **kwargs):
        if cmd[0] == "hdiutil" and cmd[1] == "attach":
            mount_point = Path(cmd[cmd.index("-mountpoint") + 1])
            (mount_point / "BgRemover.app").mkdir(parents=True, exist_ok=True)
            (mount_point / "BgRemover.app" / "secret.txt").write_bytes(_AWS_KEY)
            return subprocess.CompletedProcess(cmd, 0)
        if cmd[0] == "hdiutil" and cmd[1] == "detach":
            detach_calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", fake_run)
    dest = tmp_path / "out"
    scan_release_artifacts.extract_payload(dmg, dest)

    assert len(detach_calls) == 1
    copied = dest / "contents" / "BgRemover.app" / "secret.txt"
    assert copied.read_bytes() == _AWS_KEY


def test_extract_payload_dmg_detaches_even_if_copy_fails(tmp_path, monkeypatch) -> None:
    dmg = tmp_path / "Fake.dmg"
    dmg.write_bytes(b"not a real dmg")
    detach_calls = []

    def fake_run(cmd, check=True, capture_output=True, **kwargs):
        if cmd[0] == "hdiutil" and cmd[1] == "attach":
            mount_point = Path(cmd[cmd.index("-mountpoint") + 1])
            (mount_point / "file.txt").write_bytes(b"data")
            return subprocess.CompletedProcess(cmd, 0)
        if cmd[0] == "hdiutil" and cmd[1] == "detach":
            detach_calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)
        raise AssertionError(f"unexpected command: {cmd}")

    def fake_copy2(src: Path, dst: Path) -> None:
        raise OSError("simulierter Kopierfehler")

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", fake_run)
    monkeypatch.setattr(scan_release_artifacts.shutil, "copy2", fake_copy2)
    with pytest.raises(OSError):
        scan_release_artifacts.extract_payload(dmg, tmp_path / "out")
    assert len(detach_calls) == 1, "hdiutil detach muss auch bei einem Fehler laufen"


# ── main(): Ende-zu-Ende über ein reales .deb ───────────────────────────

def test_main_passes_for_clean_deb(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    dist = tmp_path / "dist"
    _build_deb(
        tmp_path / "stage", dist_deb := tmp_path / "clean.deb",
        {"opt/test/readme.txt": b"nothing interesting here"},
    )
    dist.mkdir()
    shutil.copy2(dist_deb, dist / "clean.deb")
    assert scan_release_artifacts.main([str(dist)]) == 0


def test_main_fails_for_deb_with_secret(tmp_path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    _build_deb(tmp_path / "stage", dist / "leaky.deb", {"opt/test/secret.txt": _AWS_KEY})
    assert scan_release_artifacts.main([str(dist)]) == 1


def test_main_fails_for_deb_with_unknown_dev_path(tmp_path) -> None:
    """Codex P2: ein unbekannter Entwicklerpfad muss den Scan fehlschlagen lassen."""
    dist = tmp_path / "dist"
    dist.mkdir()
    _build_deb(
        tmp_path / "stage", dist / "leaky.deb",
        {"opt/test/build_log.txt": b"/Users/alice/dev/picture_helper/build.log"},
    )
    assert scan_release_artifacts.main([str(dist)]) == 1


def test_main_returns_one_for_empty_directory(tmp_path: Path) -> None:
    rc = scan_release_artifacts.main([str(tmp_path)])
    assert rc == 1
