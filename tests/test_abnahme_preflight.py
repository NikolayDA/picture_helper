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


# ── Geraete-Haertung (#921) ────────────────────────────────────────────

# Reale Ausgabeform von ``pmset -g custom``: getrennte Bloecke je Stromquelle.
_PMSET_CUSTOM = """Battery Power:
 lidwake              1
 standbydelayhigh     86400
 sleep                5
 displaysleep         2
 hibernatemode        3
AC Power:
 lidwake              1
 standbydelayhigh     86400
 sleep                0
 displaysleep         0
 disablesleep         1
 hibernatemode        3
"""
_PMSET_ASSERTIONS = """Assertion status system-wide:
   BackgroundTask                 0
   UserIsActive                   1
   PreventUserIdleDisplaySleep    1
   PreventSystemSleep             0
   PreventUserIdleSystemSleep     1
Listed by owning process:
   pid 511(caffeinate): [0x0001] 00:12:03 PreventUserIdleSystemSleep named: "caffeinate"
   pid 511(caffeinate): [0x0002] 00:12:03 PreventUserIdleDisplaySleep named: "caffeinate"
"""
_SLEEPY = _PMSET_CUSTOM.replace(
    " sleep                0", " sleep                10",
).replace(" displaysleep         0", " displaysleep         10")
# Ohne Eigentuemer-Abschnitt: niemand haelt eine Assertion.
_NO_ASSERTIONS = _PMSET_ASSERTIONS.split("Listed by owning process")[0]
# Eine fremde Anwendung haelt beide Assertions – die systemweiten Zaehler
# sehen identisch aus, aber der Schutz endet mit ihr.
_FOREIGN_ASSERTIONS = _PMSET_ASSERTIONS.replace("(caffeinate)", "(zoom.us)")


def _pmset(custom: str, assertions: str):
    def runner(cmd, **kwargs):
        text = custom if cmd[:3] == ["pmset", "-g", "custom"] else assertions
        return subprocess.CompletedProcess(cmd, 0, stdout=text)

    return runner


def test_assertion_owners_are_read_from_the_owning_process_section() -> None:
    owners = preflight.parse_pmset_assertion_owners(_PMSET_ASSERTIONS)
    assert owners["caffeinate"] == {
        "PreventUserIdleSystemSleep", "PreventUserIdleDisplaySleep",
    }


def test_a_foreign_application_holding_the_assertions_does_not_count() -> None:
    """Die systemweiten Zaehler stehen auch bei einer Videokonferenz auf 1.

    Ein solcher Zufallstreffer liesse die Haertung bestehen – und sobald das
    Programm endet, schlaeft der Mac wieder ein (Codex-Review PR #930).
    """
    error = preflight.check_macos_sleep(runner=_pmset(_SLEEPY, _FOREIGN_ASSERTIONS))
    assert error is not None and "caffeinate" in error


def test_pmset_ac_block_ignores_the_battery_values() -> None:
    """Ein Abnahme-Runner haengt am Netzteil; die Akkuwerte duerfen die
    Bewertung weder retten noch kippen."""
    parsed = preflight.parse_pmset_ac(_PMSET_CUSTOM)
    assert parsed["sleep"] == 0 and parsed["displaysleep"] == 0
    assert parsed["disablesleep"] == 1


def test_pmset_without_an_ac_block_is_reported_not_assumed_fine() -> None:
    assert preflight.parse_pmset_ac("Battery Power:\n sleep 5\n") == {}
    error = preflight.check_macos_sleep(runner=_pmset("Battery Power:\n sleep 5\n", ""))
    assert error is not None and "AC-Power-Block" in error


def test_macos_sleep_passes_with_the_documented_pmset_profile() -> None:
    assert preflight.check_macos_sleep(
        runner=_pmset(_PMSET_CUSTOM, _NO_ASSERTIONS)
    ) is None


def test_macos_sleep_accepts_an_active_caffeinate_assertion() -> None:
    """RELEASE_AUTOMATION §2.1 nennt beide Wege – der Check muss beide kennen."""
    assert preflight.check_macos_sleep(runner=_pmset(_SLEEPY, _PMSET_ASSERTIONS)) is None


def test_macos_sleep_fails_when_the_mac_may_fall_asleep() -> None:
    error = preflight.check_macos_sleep(runner=_pmset(_SLEEPY, _NO_ASSERTIONS))
    assert error is not None
    assert "sleep=10" in error and "displaysleep=10" in error


def test_display_sleep_alone_is_enough_to_fail() -> None:
    """Die Abnahme erzeugt native Screenshots – ein schlafendes Display
    entwertet genau diesen Nachweis."""
    only_display = _PMSET_CUSTOM.replace(
        " displaysleep         0", " displaysleep         10",
    )
    error = preflight.check_macos_sleep(runner=_pmset(only_display, _NO_ASSERTIONS))
    assert error is not None and "displaysleep=10" in error


def test_launchagent_without_keepalive_is_a_finding(tmp_path) -> None:
    """Die offizielle Vorlage (actions.runner.plist.template) setzt nur
    RunAtLoad – ein abgestuerzter Dienst bleibt sonst unten."""
    import plistlib

    agents = tmp_path / "Library" / "LaunchAgents"
    agents.mkdir(parents=True)
    plist = agents / "actions.runner.owner-repo.mac.plist"
    with plist.open("wb") as handle:
        plistlib.dump({"Label": "actions.runner.owner-repo.mac", "RunAtLoad": True}, handle)
    error = preflight.check_launchagent_keepalive(home=tmp_path)
    assert error is not None and "KeepAlive" in error

    with plist.open("wb") as handle:
        plistlib.dump({"Label": "x", "RunAtLoad": True, "KeepAlive": True}, handle)
    assert preflight.check_launchagent_keepalive(home=tmp_path) is None


def test_a_missing_launchagent_is_reported(tmp_path) -> None:
    error = preflight.check_launchagent_keepalive(home=tmp_path)
    assert error is not None and "LaunchAgent" in error


def _systemctl(units: str, restart: str):
    def runner(cmd, **kwargs):
        text = units if cmd[1] == "list-units" else restart
        return subprocess.CompletedProcess(cmd, 0, stdout=text)

    return runner


_UNIT_LINE = (
    "actions.runner.owner-repo.pi.service loaded active running "
    "GitHub Actions Runner\n"
)


@pytest.mark.parametrize("policy", ["always", "on-failure", "on-abnormal"])
def test_systemd_restart_policy_accepted(policy: str) -> None:
    assert preflight.check_systemd_restart(
        runner=_systemctl(_UNIT_LINE, f"{policy}\n")
    ) is None


def test_systemd_without_restart_policy_is_a_finding() -> None:
    """Die offizielle Unit-Vorlage (actions.runner.service.template) enthaelt
    kein Restart= – ohne Drop-in bleibt der Dienst nach einem Absturz unten."""
    error = preflight.check_systemd_restart(runner=_systemctl(_UNIT_LINE, "no\n"))
    assert error is not None
    assert "Restart=no" in error and "actions.runner.owner-repo.pi.service" in error


def test_a_crashed_unit_is_reported_as_a_policy_finding_not_as_missing() -> None:
    """``systemctl list-units`` setzt der Problem-Unit ein "●" voran.

    Wurde es nach dem Split entfernt, blieb der leere String uebrig, die Unit
    verschwand aus der Liste und die Meldung schickte zu ``svc.sh install`` –
    das haette ausgerechnet den Drop-in ueberschrieben (Review PR #930).
    """
    marked = "\u25cf " + _UNIT_LINE
    error = preflight.check_systemd_restart(runner=_systemctl(marked, "no\n"))
    assert error is not None
    assert "Restart=no" in error
    assert "actions.runner.owner-repo.pi.service" in error
    assert "svc.sh install" not in error


def test_a_marked_unit_with_a_restart_policy_passes() -> None:
    marked = "\u25cf " + _UNIT_LINE
    assert preflight.check_systemd_restart(runner=_systemctl(marked, "always\n")) is None


def test_a_missing_runner_unit_is_reported() -> None:
    error = preflight.check_systemd_restart(runner=_systemctl("", ""))
    assert error is not None and "actions.runner" in error


def test_hardening_is_platform_specific() -> None:
    assert [name for name, _ in preflight.run_hardening("macos-arm64")] == [
        "sleep-schutz", "dienst-neustart",
    ]
    assert [name for name, _ in preflight.run_hardening("linux-arm64")] == ["dienst-neustart"]


def test_hardening_is_advisory_in_the_acceptance_preflight(monkeypatch, capsys) -> None:
    """Ein Release darf nicht an einer Display-Sleep-Einstellung scheitern –
    der taegliche Heartbeat ist die Durchsetzungsstelle, nicht die Abnahme."""
    monkeypatch.setattr(
        preflight, "run_preflight", lambda platform, min_free_gb=0: [("x", None)],
    )
    monkeypatch.setattr(
        preflight, "run_hardening", lambda platform: [("dienst-neustart", "kaputt")],
    )
    assert preflight.main(["--platform", "linux-arm64"]) == 0
    out = capsys.readouterr().out
    assert "::warning title=Haertung linux-arm64::dienst-neustart: kaputt" in out


def test_hardening_is_binding_under_strict_mode(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        preflight, "run_preflight", lambda platform, min_free_gb=0: [("x", None)],
    )
    monkeypatch.setattr(
        preflight, "run_hardening", lambda platform: [("dienst-neustart", "kaputt")],
    )
    assert preflight.main(["--platform", "linux-arm64", "--hardening-strict"]) == 1
    assert "::error title=Haertung linux-arm64::" in capsys.readouterr().out
