"""Tests für die Smoke-Orchestrierung (#642/#643) mit gefälschten Kommandos."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, filename: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


smoke = _load("abnahme_smoke", "abnahme_smoke.py")
probe = _load("abnahme_probe", "abnahme_probe.py")


def test_probe_require_rejects_software_and_missing(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(probe, "probe_diagnostic", lambda: "")
    assert probe.main(["--require"]) == 2

    monkeypatch.setattr(probe, "probe_diagnostic", lambda: "Mesa / llvmpipe / 4.5")
    assert probe.main(["--require"]) == 3

    monkeypatch.setattr(probe, "probe_diagnostic", lambda: "Apple / M3 / 2.1 Metal")
    assert probe.main(["--require"]) == 0


def test_probe_without_require_always_zero(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(probe, "probe_diagnostic", lambda: "")
    assert probe.main([]) == 0


def _runner_factory(results: dict[str, smoke.CommandResult], default_rc: int = 0):
    """Fake-Runner: matcht anhand eines Substrings im Kommando."""

    def runner(cmd: list[str]) -> smoke.CommandResult:
        joined = " ".join(cmd)
        for token, result in results.items():
            if token in joined:
                return result
        return smoke.CommandResult(default_rc)

    return runner


def _recording_runner(results: dict[str, smoke.CommandResult], default_rc: int = 0):
    """Wie ``_runner_factory``, protokolliert zusätzlich jedes Kommando (join)."""
    calls: list[str] = []

    def runner(cmd: list[str]) -> smoke.CommandResult:
        joined = " ".join(cmd)
        calls.append(joined)
        for token, result in results.items():
            if token in joined:
                return result
        return smoke.CommandResult(default_rc)

    return runner, calls


# Vollständiger, sauberer Linux-Artefaktsatz: nicht installiert nach Remove
# (dpkg -s != 0), keine bekannten Pfade übrig (test -e != 0).
_LINUX_ARTEFACTS = [
    "/tmp/BgRemover-linux-raspberrypi-arm64-ai.AppImage",
    "/tmp/BgRemover-linux-raspberrypi-arm64-ai.deb",
]
_CLEAN_DEB = {"dpkg -s": smoke.CommandResult(1), "test -e": smoke.CommandResult(1)}


def test_linux_smoke_passes_with_hardware_renderer_and_clean_deb() -> None:
    report = smoke.SmokeReport()
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, _runner_factory(_CLEAN_DEB),
        prober=lambda: "Broadcom / V3D 7.1 / 3.1",
    )
    assert result.passed
    assert result.gl_diagnostic == "Broadcom / V3D 7.1 / 3.1"


def test_linux_smoke_requires_complete_artifact_set() -> None:
    report = smoke.SmokeReport()
    # Nur AppImage, .deb fehlt → unvollständig, darf nicht bestehen.
    result = smoke.run_linux_smoke(
        ["/tmp/only.AppImage"], report, _runner_factory(_CLEAN_DEB),
        prober=lambda: "Broadcom / V3D 7.1 / 3.1",
    )
    assert not result.passed
    assert any("fehlen" in n for n in result.notes)


def test_linux_smoke_fails_on_software_renderer() -> None:
    report = smoke.SmokeReport()
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, _runner_factory(_CLEAN_DEB),
        prober=lambda: "Mesa / llvmpipe / 4.5",
    )
    assert not result.passed
    assert any("Software-Renderer" in n for n in result.notes)


def test_linux_smoke_fails_on_deb_residue() -> None:
    report = smoke.SmokeReport()
    # test -e == 0 → bekannter Pfad liegt noch auf der Platte (Rückstand).
    runner = _runner_factory({"dpkg -s": smoke.CommandResult(1), "test -e": smoke.CommandResult(0)})
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
    )
    assert not result.passed
    assert any("Rückstände" in n for n in result.notes)


def test_linux_smoke_fails_when_appimage_start_fails() -> None:
    report = smoke.SmokeReport()
    runner = _runner_factory({**_CLEAN_DEB, "smoke_launch.py": smoke.CommandResult(1)})
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
    )
    assert not result.passed
    assert any("AppImage-Start fehlgeschlagen" in n for n in result.notes)


def test_parse_mount_point() -> None:
    stdout = (
        "/dev/disk4          GUID_partition_scheme\n"
        "/dev/disk4s1        Apple_HFS        /Volumes/BgRemover 1.0\n"
    )
    assert smoke.parse_mount_point(stdout) == "/Volumes/BgRemover 1.0"
    assert smoke.parse_mount_point("no volumes here") is None


_MACOS_MOUNT = {
    "hdiutil attach": smoke.CommandResult(0, "/dev/disk4s1 Apple_HFS /Volumes/BgRemover"),
    "ls -d": smoke.CommandResult(0, "/Volumes/BgRemover/BgRemover.app"),
}


def test_macos_smoke_passes_with_retina_and_hardware() -> None:
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64-ai.dmg"], report, _runner_factory(_MACOS_MOUNT),
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
    )
    assert result.passed
    assert result.gl_diagnostic == "Apple / Apple M3 Max / 2.1 Metal - 90.5"


def test_macos_smoke_fails_on_low_dpi() -> None:
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/x.dmg"], report, _runner_factory({}),
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=1.0,
    )
    assert not result.passed
    assert any("Retina" in n for n in result.notes)


def test_macos_smoke_copies_to_temp_and_clears_quarantine() -> None:
    """#643-Fund: Start muss von einer Temp-Kopie laufen, nicht vom read-only
    DMG-Mount – sonst laesst sich die Quarantaene nie entfernen (Gatekeeper)."""
    runner, calls = _recording_runner(_MACOS_MOUNT)
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64.dmg"], report, runner,
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
    )
    assert result.passed
    assert any(c.startswith("cp -R /Volumes/BgRemover/BgRemover.app") for c in calls)
    assert any("xattr -r -d com.apple.quarantine" in c and smoke.TEMP_DMG_ROOT in c for c in calls)
    assert any(f"{smoke.TEMP_DMG_ROOT}/BgRemover.app/Contents/MacOS/BgRemover" in c for c in calls)
    # Original bleibt unangetastet – kein xattr/App-Start direkt auf dem Mount.
    assert not any(c.startswith("xattr") and "/Volumes/" in c for c in calls)


def test_macos_smoke_detaches_when_mount_point_unparseable() -> None:
    """Cleanup-Trap (#643-Fund): ``attach`` erfolgreich, aber Mount-Pfad nicht
    geparst – detach muss trotzdem ueber die Geraete-Kennung laufen, sonst
    bleibt ein Volume haengen."""
    results = {
        "hdiutil attach": smoke.CommandResult(0, "/dev/disk9         GUID_partition_scheme"),
    }
    runner, calls = _recording_runner(results)
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/x.dmg"], report, runner,
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
    )
    assert not result.passed
    assert any("Mount-Pfad nicht erkannt" in n for n in result.notes)
    assert any(c == "hdiutil detach /dev/disk9" for c in calls)


def test_macos_smoke_runs_ai_selfcheck_for_ai_variant() -> None:
    runner, calls = _recording_runner(_MACOS_MOUNT)
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64-ai.dmg"], report, runner,
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
    )
    assert result.passed
    assert any("KI-Selbsttest ok" in n for n in result.notes)
    assert any("BGREMOVER_AI_SELFCHECK=1" in c for c in calls)


def test_macos_smoke_skips_ai_selfcheck_for_non_ai_variant() -> None:
    runner, calls = _recording_runner(_MACOS_MOUNT)
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64.dmg"], report, runner,
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
    )
    assert result.passed
    assert not any("KI-Selbsttest" in n for n in result.notes)
    assert not any("BGREMOVER_AI_SELFCHECK" in c for c in calls)


def test_macos_smoke_reports_startup_time() -> None:
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64.dmg"], report, _runner_factory(_MACOS_MOUNT),
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
    )
    assert result.passed
    assert any("Startzeit" in n for n in result.notes)


def test_main_writes_failed_evidence_and_returns_nonzero(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import json

    # Keine echten Subprozesse: Default-Runner/-Probe fälschen.
    monkeypatch.setattr(smoke, "_default_runner", lambda cmd: smoke.CommandResult(0))
    monkeypatch.setattr(smoke, "_default_prober", lambda: "Apple / M3 / 2.1 Metal")

    # Vorbereitete Platzhalter-Evidenz wie von release_abnahme.py.
    (tmp_path / "artefakte").mkdir()
    evidence = {
        "schema": 1, "kind": "abnahme-evidenz", "platform": "macos-arm64",
        "status": "platzhalter", "commit_sha": "abc",
        "quelle": {"art": "release-tag", "wert": "v2.7.0"},
        "artefakte": [{"name": "x.dmg", "sha256": "cafe", "bytes": 1}],
        "umgebung": {"os": "mac", "arch": "arm64", "python": "3.12", "runner": "r"},
        "gl_provenance": None, "erzeugt_am": "2026-07-20T00:00:00+00:00",
        "hinweise": ["Platzhalter-Smoke aus #641 – echte Smokes folgen mit #642/#643."],
    }
    (tmp_path / "evidenz.json").write_text(json.dumps(evidence), encoding="utf-8")

    # scale-factor 1.0 → Retina scheitert → Exit 1, Evidenz fehlgeschlagen.
    rc = smoke.main(
        ["--platform", "macos-arm64", "--evidence-dir", str(tmp_path), "--scale-factor", "1.0"]
    )
    assert rc == 1
    written = json.loads((tmp_path / "evidenz.json").read_text(encoding="utf-8"))
    assert written["status"] == "fehlgeschlagen"
