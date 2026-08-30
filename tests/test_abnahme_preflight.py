"""Tests des Runner-Readiness-Preflights (#915, Epic #914)."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "abnahme_preflight", ROOT / "scripts" / "abnahme_preflight.py"
)
assert _SPEC is not None and _SPEC.loader is not None
preflight = importlib.util.module_from_spec(_SPEC)
sys.modules["abnahme_preflight"] = preflight
_SPEC.loader.exec_module(preflight)


class _Usage:
    def __init__(self, free: int) -> None:
        self.free = free


def test_check_python_and_venv_pass_on_test_interpreter() -> None:
    # Die Testumgebung selbst erfuellt die Mindestanforderungen (>= 3.10, venv).
    assert preflight.check_python() is None
    assert preflight.check_venv() is None


def test_check_disk_reports_shortage(tmp_path: Path) -> None:
    ok = preflight.check_disk(tmp_path, 2.0, usage=lambda _p: _Usage(4 * 1024**3))
    assert ok is None
    error = preflight.check_disk(tmp_path, 2.0, usage=lambda _p: _Usage(1 * 1024**3))
    assert error is not None and "GB frei" in error


def test_check_graphical_session_linux_requires_display() -> None:
    assert preflight.check_graphical_session("linux-arm64", {"DISPLAY": ":0"}) is None
    error = preflight.check_graphical_session("linux-arm64", {})
    assert error is not None and "DISPLAY" in error


def test_check_graphical_session_linux_wayland_needs_runtime_dir() -> None:
    error = preflight.check_graphical_session("linux-arm64", {"WAYLAND_DISPLAY": "wayland-0"})
    assert error is not None and "XDG_RUNTIME_DIR" in error
    ok = preflight.check_graphical_session(
        "linux-arm64",
        {"WAYLAND_DISPLAY": "wayland-0", "XDG_RUNTIME_DIR": "/run/user/1001"},
    )
    assert ok is None


def test_check_graphical_session_macos_compares_console_user() -> None:
    ok = preflight.check_graphical_session(
        "macos-arm64", {}, console_user=lambda: "runner", current_user=lambda: "runner",
    )
    assert ok is None
    error = preflight.check_graphical_session(
        "macos-arm64", {}, console_user=lambda: "alice", current_user=lambda: "runner",
    )
    assert error is not None and "Konsolenbenutzer" in error


def test_check_graphical_session_macos_handles_probe_failure() -> None:
    def _raise() -> str:
        raise subprocess.SubprocessError("stat kaputt")

    error = preflight.check_graphical_session(
        "macos-arm64", {}, console_user=_raise, current_user=lambda: "runner",
    )
    assert error is not None and "nicht ermittelbar" in error


def test_check_gl_linux_reports_unloadable_library() -> None:
    def _fail(_name: str) -> object:
        raise OSError("libGL.so.1: cannot open shared object file")

    error = preflight.check_gl(
        "linux-arm64", find_library=lambda _n: None, load_library=_fail,
    )
    assert error is not None and "libGL.so.1" in error
    ok = preflight.check_gl(
        "linux-arm64", find_library=lambda _n: "libGL.so.1",
        load_library=lambda _n: object(),
    )
    assert ok is None


def test_check_gl_macos_checks_framework(tmp_path: Path) -> None:
    assert preflight.check_gl("macos-arm64", macos_framework=tmp_path) is None
    error = preflight.check_gl("macos-arm64", macos_framework=tmp_path / "fehlt")
    assert error is not None and "OpenGL-Framework" in error


def test_check_network_counts_http_error_as_reachable() -> None:
    def _http_error(_request: object, timeout: float) -> object:
        raise urllib.error.HTTPError("https://api.github.com", 403, "rate", None, None)

    assert preflight.check_network("https://api.github.com", opener=_http_error) is None

    def _unreachable(_request: object, timeout: float) -> object:
        raise urllib.error.URLError("dns kaputt")

    error = preflight.check_network("https://api.github.com", opener=_unreachable)
    assert error is not None and "nicht erreichbar" in error

    class _Response:
        def close(self) -> None:
            pass

    assert preflight.check_network(
        "https://api.github.com", opener=lambda _r, timeout: _Response(),
    ) is None


def _completed(returncode: int) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout="", stderr="")


def test_check_deb_sudo_requires_sudo_and_permissions() -> None:
    error = preflight.check_deb_sudo(which=lambda _n: None, runner=lambda *a, **k: _completed(0))
    assert error is not None and "sudo" in error

    ok = preflight.check_deb_sudo(
        which=lambda name: f"/usr/bin/{name}", runner=lambda *a, **k: _completed(0),
    )
    assert ok is None

    denied = preflight.check_deb_sudo(
        which=lambda name: f"/usr/bin/{name}", runner=lambda *a, **k: _completed(1),
    )
    assert denied is not None and "verweigert" in denied


def test_check_deb_sudo_reports_missing_commands() -> None:
    def _which(name: str) -> str | None:
        return "/usr/bin/sudo" if name == "sudo" else None

    error = preflight.check_deb_sudo(which=_which, runner=lambda *a, **k: _completed(0))
    assert error is not None and "nicht im PATH" in error


def test_main_reports_all_failures_and_exit_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        preflight, "run_preflight",
        lambda platform, min_free_gb: [
            ("python", None), ("session", "kaputt"), ("netz", "auch kaputt"),
        ],
    )
    rc = preflight.main(["--platform", "linux-arm64"])
    out = capsys.readouterr().out
    assert rc == 1
    # Alle Verstoesse gesammelt, nicht nur der erste.
    assert out.count("::error title=Preflight linux-arm64::") == 3
    assert "session: kaputt" in out
    assert "netz: auch kaputt" in out
    assert "RELEASE_AUTOMATION.md" in out


def test_main_passes_when_all_checks_ok(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        preflight, "run_preflight", lambda platform, min_free_gb: [("python", None)],
    )
    rc = preflight.main(["--platform", "macos-arm64"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "einsatzbereit" in out
    assert "::error" not in out


def test_run_preflight_includes_deb_sudo_only_on_linux(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Netz-/Session-/GL-Checks neutralisieren, damit der Test hermetisch bleibt.
    monkeypatch.setattr(preflight, "check_network", lambda *a, **k: None)
    monkeypatch.setattr(preflight, "check_graphical_session", lambda *a, **k: None)
    monkeypatch.setattr(preflight, "check_gl", lambda *a, **k: None)
    monkeypatch.setattr(preflight, "check_deb_sudo", lambda *a, **k: None)
    linux_names = [name for name, _ in preflight.run_preflight("linux-arm64")]
    macos_names = [name for name, _ in preflight.run_preflight("macos-arm64")]
    assert "deb-sudo" in linux_names
    assert "deb-sudo" not in macos_names
