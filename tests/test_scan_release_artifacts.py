"""Tests für den Secret-/Entwicklerpfad-Scan gebauter Release-Artefakte (#584)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "scripts" / "scan_release_artifacts.py"

_spec = importlib.util.spec_from_file_location("scan_release_artifacts", _SCRIPT)
assert _spec is not None and _spec.loader is not None
scan_release_artifacts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scan_release_artifacts)


def test_script_exists() -> None:
    assert _SCRIPT.is_file()


def test_clean_file_has_no_findings(tmp_path: Path) -> None:
    target = tmp_path / "clean.bin"
    target.write_bytes(b"just a harmless binary blob, nothing to see here\x00\x01\x02")
    findings, unknown_users = scan_release_artifacts.scan_file(target)
    assert findings == []
    assert unknown_users == set()


def test_detects_aws_access_key(tmp_path: Path) -> None:
    # Öffentlich dokumentiertes AWS-Beispiel-Muster (kein echtes Secret).
    target = tmp_path / "leaky.bin"
    target.write_bytes(b"...AKIAIOSFODNN7EXAMPLE...")
    findings, _ = scan_release_artifacts.scan_file(target)
    assert any("AWS Access Key ID" in f for f in findings)


def test_detects_github_token(tmp_path: Path) -> None:
    target = tmp_path / "leaky.bin"
    target.write_bytes(b"token=ghp_" + b"a1b2c3" * 7)
    findings, _ = scan_release_artifacts.scan_file(target)
    assert any("GitHub-Token" in f for f in findings)


def test_detects_pem_private_key(tmp_path: Path) -> None:
    target = tmp_path / "leaky.bin"
    target.write_bytes(b"-----BEGIN RSA PRIVATE KEY-----\nMIIB...\n-----END RSA PRIVATE KEY-----")
    findings, _ = scan_release_artifacts.scan_file(target)
    assert any("PEM-Schlüssel" in f for f in findings)


def test_known_ci_user_paths_are_not_flagged(tmp_path: Path) -> None:
    target = tmp_path / "build.bin"
    target.write_bytes(b"/home/runner/work/picture_helper/picture_helper/bgremover/app.py")
    _, unknown_users = scan_release_artifacts.scan_file(target)
    assert unknown_users == set()


def test_unknown_dev_path_is_flagged(tmp_path: Path) -> None:
    target = tmp_path / "build.bin"
    target.write_bytes(b"/Users/alice/dev/picture_helper/bgremover/app.py")
    _, unknown_users = scan_release_artifacts.scan_file(target)
    assert unknown_users == {"alice"}


def test_main_returns_zero_for_clean_directory(tmp_path: Path, capsys: object) -> None:
    (tmp_path / "clean.bin").write_bytes(b"nothing interesting")
    rc = scan_release_artifacts.main([str(tmp_path)])
    assert rc == 0


def test_main_returns_one_when_secret_present(tmp_path: Path, capsys: object) -> None:
    (tmp_path / "leaky.bin").write_bytes(b"AKIAIOSFODNN7EXAMPLE")
    rc = scan_release_artifacts.main([str(tmp_path)])
    assert rc == 1


def test_main_returns_zero_for_unknown_dev_path_only(tmp_path: Path, capsys: object) -> None:
    """Fremde Entwicklerpfade sind nur ein Hinweis, kein harter Fehlschlag."""
    (tmp_path / "build.bin").write_bytes(b"/Users/alice/dev/picture_helper")
    rc = scan_release_artifacts.main([str(tmp_path)])
    assert rc == 0


def test_main_returns_one_for_empty_directory(tmp_path: Path) -> None:
    rc = scan_release_artifacts.main([str(tmp_path)])
    assert rc == 1
