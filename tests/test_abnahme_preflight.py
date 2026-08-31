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


# ── Echter Qt-/GL-Probeaufruf (#934) ───────────────────────────────────


def _probe_result(stdout: str = "", stderr: str = "", code: int = 0):
    return subprocess.CompletedProcess(["probe"], code, stdout, stderr)


def _probe_runner(payload: dict | None, *, stderr: str = "", code: int = 0):
    """Runner, der die Sonde durch ihre JSON-Zeile ersetzt."""
    import json as _json

    stdout = "" if payload is None else _json.dumps(payload)
    return lambda *_a, **_kw: _probe_result(stdout, stderr, code)


def _check(runner, *, runtime: Path | None = None, **kwargs) -> str | None:
    return preflight.check_qt_gl(
        "linux-arm64",
        ensure_runtime=(lambda: runtime or Path("/usr/bin/python3")),
        runner=runner,
        **kwargs,
    )


def test_qt_probe_success_needs_a_real_renderer() -> None:
    ok = _check(_probe_runner({
        "ok": True, "platform": "cocoa",
        "vendor": "Apple", "renderer": "Apple M2", "version": "2.1 Metal",
    }))
    assert ok is None


def test_qt_probe_reports_a_missing_runtime_by_name() -> None:
    """Fehlende PyQt-/Qt-Runtime ist ein benannter Befund, kein stiller Skip."""
    def _no_runtime() -> Path:
        raise preflight.PreflightError("pip install fehlgeschlagen: no wheel")

    error = preflight.check_qt_gl("linux-arm64", ensure_runtime=_no_runtime)
    assert error is not None
    assert "PyQt6/Qt-Runtime nicht ladbar" in error and "no wheel" in error


def test_qt_probe_names_each_failing_stage() -> None:
    """Jede Stufe der Sonde wird als eigener Befund gemeldet."""
    cases = {
        "import": "PyQt6/Qt-Runtime nicht ladbar",
        "plugin": "Natives Qt-Platform-Plugin startet nicht",
        "kontext": "Kein gueltiger OpenGL-Kontext",
        "renderer": "Unerwuenschter Software-Renderer",
    }
    assert set(cases) == set(preflight.PROBE_STAGE_HINTS)
    for stage, hint in cases.items():
        error = _check(_probe_runner(
            {"ok": False, "stage": stage, "detail": f"detail-{stage}"}, code=1
        ))
        assert error is not None and error.startswith(hint), stage
        assert f"detail-{stage}" in error


def test_qt_probe_treats_a_hard_qt_abort_as_a_plugin_failure() -> None:
    """Qt ruft bei fehlendem Platform-Plugin ``qFatal`` – es gibt kein JSON.

    Real beobachtet (Exit 134/SIGABRT): Ohne diesen Zweig sähe der
    schwerwiegendste Ausfallmodus wie „keine Ausgabe, also nichts gefunden" aus.
    """
    stderr = (
        'qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in ""\n'
        "This application failed to start because no Qt platform plugin could "
        "be initialized.\n"
        "Available platform plugins are: offscreen, xcb, wayland.\n"
    )
    error = _check(_probe_runner(None, stderr=stderr, code=134))
    assert error is not None
    assert error.startswith("Natives Qt-Platform-Plugin startet nicht")
    # Die tragende Zeile darf nicht von der Plugin-Liste verdrängt werden.
    assert "no Qt platform plugin could be initialized" in error


def test_qt_probe_reports_a_timeout_instead_of_hanging() -> None:
    def _timeout(*_a, **_kw):
        raise subprocess.TimeoutExpired(["probe"], 90.0)

    error = _check(_timeout, timeout=90.0)
    assert error is not None and "nach 90s ohne Ergebnis" in error


def test_qt_probe_reports_an_unstartable_process() -> None:
    def _oserror(*_a, **_kw):
        raise OSError("Permission denied")

    error = _check(_oserror)
    assert error is not None and "nicht startbar" in error


def test_qt_probe_ignores_qt_chatter_before_the_json_line() -> None:
    """Qt schreibt gern Warnungen auf stdout – die letzte JSON-Zeile zählt."""
    import json as _json

    noisy = "qt.qpa: irgendeine Warnung\n" + _json.dumps({"ok": True})
    assert _check(lambda *_a, **_kw: _probe_result(noisy)) is None


def test_the_preflight_runs_the_real_probe_on_every_platform() -> None:
    """Kein Plattform-Sonderweg: Der Nachweis gehört zu jedem Readiness-Job."""
    for platform in preflight.KNOWN_PLATFORMS:
        names = [name for name, _ in preflight.run_preflight(platform)]
        assert "qt-gl" in names, platform
        # Der billige Ladetest bleibt und läuft davor.
        assert names.index("gl") < names.index("qt-gl"), platform


# ── Bereitstellung der schlanken Runtime (#934) ────────────────────────


def test_probe_requirements_come_from_the_release_constraints() -> None:
    """Dieselbe Quelle wie das Release-venv – kein zweiter Pin-Stand."""
    pins = preflight.probe_requirements()
    assert pins and all(pin.lower().startswith("pyqt6") for pin in pins)
    assert any(pin.startswith("PyQt6==") for pin in pins)


def test_probe_requirements_fail_closed_without_pins(tmp_path: Path) -> None:
    missing = tmp_path / "fehlt.txt"
    with pytest.raises(preflight.PreflightError, match="nicht lesbar"):
        preflight.probe_requirements(missing)
    empty = tmp_path / "constraints.txt"
    empty.write_text("# nur ein Kommentar\nPillow==11.0.0\n", encoding="utf-8")
    with pytest.raises(preflight.PreflightError, match="Keine pyqt6-Pins"):
        preflight.probe_requirements(empty)


def test_a_changed_pin_changes_the_runtime_key() -> None:
    """Das ist die Aktualisierung bei Dependency-Änderungen: neuer Schlüssel."""
    old = preflight.probe_runtime_key(["PyQt6==6.7.1"], python_version="3.11")
    new = preflight.probe_runtime_key(["PyQt6==6.8.0"], python_version="3.11")
    other_python = preflight.probe_runtime_key(["PyQt6==6.7.1"], python_version="3.12")
    assert old != new and old != other_python
    assert old == preflight.probe_runtime_key(["PyQt6==6.7.1"], python_version="3.11")


class _FakeBuilder:
    """Baut das venv wie ``python -m venv`` es täte – ohne Netz."""

    def __init__(self, venv: Path, *, fail_at: str = "") -> None:
        self.venv = venv
        self.fail_at = fail_at
        self.commands: list[list[str]] = []

    def __call__(self, command, **_kwargs):
        self.commands.append(list(command))
        if self.fail_at and self.fail_at in " ".join(command):
            return _probe_result(code=1, stderr="Netzwerkfehler beim Wheel-Download")
        if "venv" in command:
            (self.venv / "bin").mkdir(parents=True, exist_ok=True)
            (self.venv / "bin" / "python").write_text("#!/bin/sh\n", encoding="utf-8")
        return _probe_result()


def test_the_runtime_is_built_once_and_then_reused(tmp_path: Path) -> None:
    venv = tmp_path / "qt"
    builder = _FakeBuilder(venv)
    first = preflight.ensure_probe_runtime(
        venv=venv, requirements=["PyQt6==6.7.1"], runner=builder
    )
    assert first == venv / "bin" / "python"
    built = len(builder.commands)
    assert built == 2, builder.commands
    # Wheels statt Quellbau: ein Compilerlauf auf dem Pi spränge jedes Budget.
    assert any("--only-binary=:all:" in cmd for cmd in builder.commands)

    preflight.ensure_probe_runtime(
        venv=venv, requirements=["PyQt6==6.7.1"], runner=builder
    )
    assert len(builder.commands) == built, "Runtime wurde erneut gebaut"


def test_a_changed_pin_rebuilds_the_runtime(tmp_path: Path) -> None:
    venv = tmp_path / "qt"
    builder = _FakeBuilder(venv)
    preflight.ensure_probe_runtime(venv=venv, requirements=["PyQt6==6.7.1"], runner=builder)
    preflight.ensure_probe_runtime(venv=venv, requirements=["PyQt6==6.8.0"], runner=builder)
    assert len(builder.commands) == 4, builder.commands


def test_a_failed_build_never_looks_fresh(tmp_path: Path) -> None:
    """Marker erst nach erfolgreicher Installation – sonst bliebe ein halbes
    venv liegen und der nächste Lauf hielte es für einsatzbereit."""
    venv = tmp_path / "qt"
    builder = _FakeBuilder(venv, fail_at="pip")
    with pytest.raises(preflight.PreflightError, match="Netzwerkfehler"):
        preflight.ensure_probe_runtime(
            venv=venv, requirements=["PyQt6==6.7.1"], runner=builder
        )
    assert not (venv / preflight.PROBE_MARKER_NAME).exists()


def test_a_build_timeout_is_a_named_error(tmp_path: Path) -> None:
    """Das Budget kommt aus der Quelle, nicht aus einem Literal im Test."""
    budget = preflight.RUNTIME_BUILD_TIMEOUT_S

    def _timeout(*_a, **_kw):
        raise subprocess.TimeoutExpired(["venv"], budget)

    with pytest.raises(preflight.PreflightError, match=f"nach {budget:.0f}s abgebrochen"):
        preflight.ensure_probe_runtime(
            venv=tmp_path / "qt", requirements=["PyQt6==6.7.1"], runner=_timeout
        )


def test_the_runtime_location_is_overridable(tmp_path: Path) -> None:
    assert preflight.probe_venv_path({}) == preflight.PROBE_VENV_DEFAULT
    chosen = preflight.probe_venv_path({preflight.PROBE_VENV_ENV: str(tmp_path / "eigen")})
    assert chosen == tmp_path / "eigen"


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
