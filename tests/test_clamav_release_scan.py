"""Fail-closed ClamAV-Nachweis für gebaute Release-Artefakte (#731)."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "scripts" / "scan_release_artifacts.py"

_spec = importlib.util.spec_from_file_location("scan_release_artifacts_clamav", _SCRIPT)
assert _spec is not None and _spec.loader is not None
scan_release_artifacts = importlib.util.module_from_spec(_spec)
# Ohne Eintrag in sys.modules kann @dataclass seinen Namensraum nicht aufloesen
sys.modules["scan_release_artifacts_clamav"] = scan_release_artifacts
_spec.loader.exec_module(scan_release_artifacts)

_ZERO_BYTE_SCAN = """----------- SCAN SUMMARY -----------
Scanned files: 2
Infected files: 0
Data scanned: 0 B
Data read: 492.16 MiB (ratio 0.00:1)
"""

_CLEAN_SCAN = """----------- SCAN SUMMARY -----------
Scanned files: 42
Infected files: 0
Data scanned: 128.50 MiB
Data read: 130.00 MiB (ratio 0.99:1)
"""


def test_clamav_rejects_historical_zero_byte_false_success() -> None:
    """#731: Exit 0 allein ist keine Evidenz, wenn ClamAV 0 Byte scannt."""
    result = subprocess.CompletedProcess(["clamscan"], 0, stdout=_ZERO_BYTE_SCAN)
    assert scan_release_artifacts.clamav_scan_succeeded(result) is False


def test_clamav_accepts_clean_nonzero_scan() -> None:
    result = subprocess.CompletedProcess(["clamscan"], 0, stdout=_CLEAN_SCAN)
    assert scan_release_artifacts.clamav_scan_succeeded(result) is True


def test_clamav_rejects_limit_alert_even_with_zero_exit() -> None:
    output = _CLEAN_SCAN + "payload.bin: Heuristics.Limits.Exceeded.MaxFileSize FOUND\n"
    result = subprocess.CompletedProcess(["clamscan"], 0, stdout=output)
    assert scan_release_artifacts.clamav_scan_succeeded(result) is False


def test_clamav_rejects_malware_finding() -> None:
    output = _CLEAN_SCAN.replace("Infected files: 0", "Infected files: 1")
    result = subprocess.CompletedProcess(["clamscan"], 1, stdout=output + "bad.bin: Malware FOUND\n")
    assert scan_release_artifacts.clamav_scan_succeeded(result) is False


def test_clamav_command_scans_raw_and_extracted_payload_with_fail_closed_limits(
    tmp_path: Path, monkeypatch,
) -> None:
    artifact = tmp_path / "BgRemover.AppImage"
    artifact.write_bytes(b"raw package")
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    (extracted / "payload.bin").write_bytes(b"payload")
    database = tmp_path / "db"
    database.mkdir()
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout=_CLEAN_SCAN)

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", fake_run)
    assert scan_release_artifacts.scan_artifact_with_clamav(
        artifact, extracted, database,
    ).ok is True

    assert len(calls) == 2
    raw_cmd, raw_kwargs = calls[0]
    payload_cmd, payload_kwargs = calls[1]
    for cmd in (raw_cmd, payload_cmd):
        assert "--max-filesize=2000M" in cmd
        assert "--max-scansize=2000M" in cmd
        assert "--max-files=2000000" in cmd
        assert "--max-recursion=100" in cmd
        assert "--max-recursion=2000000" not in cmd
        assert "--alert-exceeds-max=yes" in cmd
        assert "--recursive" in cmd
    assert raw_cmd[-1] == str(artifact)
    assert payload_cmd[-1] == str(extracted)
    assert raw_kwargs["stderr"] is subprocess.STDOUT
    assert raw_kwargs["text"] is True
    assert payload_kwargs["stderr"] is subprocess.STDOUT
    assert payload_kwargs["text"] is True


def test_clamav_rejects_empty_extracted_payload(tmp_path: Path, monkeypatch) -> None:
    artifact = tmp_path / "BgRemover.AppImage"
    artifact.write_bytes(b"raw package")
    extracted = tmp_path / "empty"
    extracted.mkdir()
    database = tmp_path / "db"
    database.mkdir()

    def must_not_run(*args, **kwargs):
        raise AssertionError("ClamAV darf eine leere Payload nicht kaschieren")

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", must_not_run)
    assert scan_release_artifacts.scan_artifact_with_clamav(
        artifact, extracted, database,
    ).ok is False


def test_clamav_eicar_control_requires_real_detection(tmp_path: Path, monkeypatch) -> None:
    database = tmp_path / "db"
    database.mkdir()
    observed = {}

    def fake_run(cmd, **kwargs):
        control = Path(cmd[-1])
        observed["bytes"] = control.read_bytes()
        return subprocess.CompletedProcess(
            cmd, 1,
            stdout=f"{control}: Win.Test.EICAR_HDB-1 FOUND\nInfected files: 1\nData scanned: 68 B\n",
        )

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", fake_run)
    assert scan_release_artifacts.verify_clamav_eicar(database, tmp_path) is True
    assert observed["bytes"].startswith(b"X5O!P%")
    assert not any(tmp_path.glob("eicar-*")), "EICAR-Kontrolldatei muss entfernt werden"


def test_clamav_eicar_control_fails_if_signature_is_not_detected(
    tmp_path: Path, monkeypatch,
) -> None:
    database = tmp_path / "db"
    database.mkdir()

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout=_CLEAN_SCAN)

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", fake_run)
    assert scan_release_artifacts.verify_clamav_eicar(database, tmp_path) is False


def test_main_rejects_requested_but_empty_clamav_database(tmp_path: Path, capsys) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "artifact.AppImage").write_bytes(b"placeholder")
    database = tmp_path / "empty-db"
    database.mkdir()

    assert scan_release_artifacts.main(
        ["--clamav-database", str(database), str(dist)],
    ) == 1
    assert "Signaturdatenbank fehlt oder ist leer" in capsys.readouterr().out


def test_main_runs_eicar_then_scans_real_extracted_appimage_boundary(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    """Entry-Point-Harness mit echten Subprozessen an beiden Toolgrenzen.

    Das AppImage-Testprogramm erzeugt wie die echte Runtime ein
    ``squashfs-root``. Der ClamAV-Doppel erkennt die temporäre EICAR-Datei und
    liefert danach eine saubere, nichtleere Summary für Rohdatei + Payload.
    """
    tools = tmp_path / "tools"
    tools.mkdir()
    clamscan = tools / "clamscan"
    clamscan.write_text(
        "#!/bin/sh\n"
        "for arg in \"$@\"; do\n"
        "  case \"$arg\" in\n"
        "    *eicar-clamav-control.com)\n"
        "      echo \"$arg: Win.Test.EICAR_HDB-1 FOUND\"\n"
        "      echo \"Infected files: 1\"\n"
        "      echo \"Data scanned: 68 B\"\n"
        "      exit 1\n"
        "      ;;\n"
        "  esac\n"
        "done\n"
        "echo \"Scanned files: 2\"\n"
        "echo \"Infected files: 0\"\n"
        "echo \"Data scanned: 1.00 MiB\"\n"
        "echo \"Data read: 1.00 MiB (ratio 1.00:1)\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    clamscan.chmod(0o755)

    dist = tmp_path / "dist"
    dist.mkdir()
    appimage = dist / "BgRemover-test.AppImage"
    appimage.write_text(
        "#!/bin/sh\n"
        "test \"$1\" = \"--appimage-extract\" || exit 2\n"
        "mkdir -p squashfs-root/usr/lib\n"
        "echo harmless-payload > squashfs-root/usr/lib/payload.bin\n",
        encoding="utf-8",
    )
    appimage.chmod(0o755)

    database = tmp_path / "clamav-db"
    database.mkdir()
    (database / "daily.cvd").write_bytes(b"test database marker")
    monkeypatch.setenv("PATH", f"{tools}{os.pathsep}{os.environ['PATH']}")

    assert scan_release_artifacts.main(
        ["--clamav-database", str(database), str(dist)],
    ) == 0
    output = capsys.readouterr().out
    assert "ClamAV-EICAR-Selbsttest" in output
    assert "Rohdatei + entpackter Inhalt, getrennt" in output
    assert "Malware-Scan (#731)" in output
