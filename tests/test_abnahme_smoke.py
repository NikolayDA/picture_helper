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


def test_linux_smoke_passes_with_hardware_renderer_and_clean_deb() -> None:
    report = smoke.SmokeReport()
    # dpkg -s (nach purge) != 0 → nicht installiert; dpkg -L → keine Reste.
    runner = _runner_factory(
        {
            "dpkg -s": smoke.CommandResult(1),
            "dpkg -L": smoke.CommandResult(0, stdout=""),
        }
    )
    result = smoke.run_linux_smoke(
        ["/tmp/BgRemover-linux-raspberrypi-arm64-ai.AppImage",
         "/tmp/BgRemover-linux-raspberrypi-arm64-ai.deb"],
        report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
    )
    assert result.passed
    assert result.gl_diagnostic == "Broadcom / V3D 7.1 / 3.1"


def test_linux_smoke_fails_on_software_renderer() -> None:
    report = smoke.SmokeReport()
    runner = _runner_factory({"dpkg -s": smoke.CommandResult(1)})
    result = smoke.run_linux_smoke(
        ["/tmp/x.AppImage"], report, runner, prober=lambda: "Mesa / llvmpipe / 4.5",
    )
    assert not result.passed
    assert any("Software-Renderer" in n for n in result.notes)


def test_linux_smoke_fails_on_deb_residue() -> None:
    report = smoke.SmokeReport()
    # dpkg -s == 0 → noch installiert (purge-Rückstand).
    runner = _runner_factory(
        {"dpkg -s": smoke.CommandResult(0), "dpkg -L": smoke.CommandResult(0, "/usr/bin/bgremover")}
    )
    result = smoke.run_linux_smoke(
        ["/tmp/x.deb"], report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
    )
    assert not result.passed
    assert any("Rückstände" in n for n in result.notes)


def test_linux_smoke_fails_when_appimage_start_fails() -> None:
    report = smoke.SmokeReport()
    runner = _runner_factory({"smoke_launch.py": smoke.CommandResult(1)})
    result = smoke.run_linux_smoke(
        ["/tmp/x.AppImage"], report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
    )
    assert not result.passed
    assert any("AppImage-Start fehlgeschlagen" in n for n in result.notes)


def test_macos_smoke_passes_with_retina_and_hardware() -> None:
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64-ai.dmg"], report, _runner_factory({}),
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
    )
    assert result.passed


def test_macos_smoke_fails_on_low_dpi() -> None:
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/x.dmg"], report, _runner_factory({}),
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=1.0,
    )
    assert not result.passed
    assert any("Retina" in n for n in result.notes)


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
