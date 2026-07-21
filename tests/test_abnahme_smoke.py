"""Tests für die Smoke-Orchestrierung (#642/#643, nativer 3D-Screenshot #648) mit
gefälschten Kommandos."""
from __future__ import annotations

import importlib.util
import json
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


def test_probe_diagnostic_bootstraps_qapplication(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Regression: probe_3d_capability baut einen QOpenGLContext, der ohne
    # QApplication mangels Plattformintegration scheitert – live auf den
    # Mac-/Pi-Abnahme-Runnern als leere Diagnose beobachtet, obwohl derselbe
    # GL-Kontext im gepackten Artefakt (das immer eine QApplication laufen
    # hat) klaglos funktioniert. Patcht nur das Modul-lokale ``probe.
    # QApplication`` (nicht die geteilte PyQt6.QtWidgets-Klasse) – sonst
    # verwechselt pytest-qt die Fake-Instanz mit der echten Session-App und
    # reißt die ganze restliche Suite mit.
    import bgremover.preview3d_capability as cap

    calls: list[str] = []

    class _FakeApp:
        _instance: object | None = None

        @classmethod
        def instance(cls):  # type: ignore[no-untyped-def]
            return cls._instance

        def __init__(self, argv: list[str]) -> None:
            calls.append("constructed")
            _FakeApp._instance = self

    monkeypatch.setattr(probe, "QApplication", _FakeApp)
    monkeypatch.setattr(
        cap, "probe_3d_capability",
        lambda *, use_cache=True: cap.RendererCapability(ok=True, diagnostic="Fake / GPU / 1.0"),
    )

    assert probe.probe_diagnostic() == "Fake / GPU / 1.0"
    assert calls == ["constructed"]


def _fake_native_screenshot(
    cmd: list[str], diagnostic: str | None, rc: int,
) -> smoke.CommandResult | None:
    """Simuliert den echten Automationshook (``bgremover.screenshot3d``) für den
    ``smoke_launch.py --native``-Aufruf: schreibt PNG + Provenance-Sidecar an den
    per ``--env BGREMOVER_SCREENSHOT_3D=...`` übergebenen Pfad, genau wie der
    laufende gepackte Prozess es täte. ``diagnostic=None`` lässt den Aufruf
    unbehandelt (fällt auf die normale Substring-Matching-Logik zurück)."""
    if diagnostic is None or "--native" not in cmd:
        return None
    target: Path | None = None
    for arg in cmd:
        if arg.startswith("BGREMOVER_SCREENSHOT_3D="):
            target = Path(arg.split("=", 1)[1])
    if target is None:
        return None
    if rc != 0:
        return smoke.CommandResult(rc, stderr="nativer Screenshot-Hook fehlgeschlagen")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"fake-png-bytes")
    target.with_name(target.name + ".json").write_text(
        json.dumps({"gl_provenance": diagnostic}), encoding="utf-8",
    )
    return smoke.CommandResult(0)


def _runner_factory(
    results: dict[str, smoke.CommandResult],
    default_rc: int = 0,
    native_screenshot_diagnostic: str | None = "Broadcom / V3D 7.1 / 3.1",
    native_screenshot_rc: int = 0,
):
    """Fake-Runner: matcht anhand eines Substrings im Kommando; simuliert den
    nativen 3D-Screenshot-Hook standardmäßig als Erfolg (siehe
    ``_fake_native_screenshot``)."""

    def runner(cmd: list[str]) -> smoke.CommandResult:
        handled = _fake_native_screenshot(cmd, native_screenshot_diagnostic, native_screenshot_rc)
        if handled is not None:
            return handled
        joined = " ".join(cmd)
        for token, result in results.items():
            if token in joined:
                return result
        return smoke.CommandResult(default_rc)

    return runner


def _recording_runner(
    results: dict[str, smoke.CommandResult],
    default_rc: int = 0,
    native_screenshot_diagnostic: str | None = "Broadcom / V3D 7.1 / 3.1",
    native_screenshot_rc: int = 0,
):
    """Wie ``_runner_factory``, protokolliert zusätzlich jedes Kommando (join)."""
    calls: list[str] = []

    def runner(cmd: list[str]) -> smoke.CommandResult:
        calls.append(" ".join(cmd))
        handled = _fake_native_screenshot(cmd, native_screenshot_diagnostic, native_screenshot_rc)
        if handled is not None:
            return handled
        joined = " ".join(cmd)
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


def test_linux_smoke_passes_with_hardware_renderer_and_clean_deb(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    report = smoke.SmokeReport()
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, _runner_factory(_CLEAN_DEB),
        prober=lambda: "Broadcom / V3D 7.1 / 3.1", screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    assert result.gl_diagnostic == "Broadcom / V3D 7.1 / 3.1"


def test_linux_smoke_requires_complete_artifact_set(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    report = smoke.SmokeReport()
    # Nur AppImage, .deb fehlt → unvollständig, darf nicht bestehen.
    result = smoke.run_linux_smoke(
        ["/tmp/only.AppImage"], report, _runner_factory(_CLEAN_DEB),
        prober=lambda: "Broadcom / V3D 7.1 / 3.1", screenshot_dir=tmp_path / "shots",
    )
    assert not result.passed
    assert any("fehlen" in n for n in result.notes)


def test_linux_smoke_fails_on_software_renderer(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    report = smoke.SmokeReport()
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, _runner_factory(_CLEAN_DEB),
        prober=lambda: "Mesa / llvmpipe / 4.5", screenshot_dir=tmp_path / "shots",
    )
    assert not result.passed
    assert any("Software-Renderer" in n for n in result.notes)


def test_linux_smoke_fails_on_deb_residue(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    report = smoke.SmokeReport()
    # test -e == 0 → bekannter Pfad liegt noch auf der Platte (Rückstand).
    runner = _runner_factory({"dpkg -s": smoke.CommandResult(1), "test -e": smoke.CommandResult(0)})
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
        screenshot_dir=tmp_path / "shots",
    )
    assert not result.passed
    assert any("Rückstände" in n for n in result.notes)


def test_linux_smoke_fails_when_appimage_start_fails(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    report = smoke.SmokeReport()
    runner = _runner_factory({**_CLEAN_DEB, "smoke_launch.py": smoke.CommandResult(1)})
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
        screenshot_dir=tmp_path / "shots",
    )
    assert not result.passed
    assert any("AppImage-Start fehlgeschlagen" in n for n in result.notes)


def test_linux_smoke_runs_cleanup_after_failed_deb_install(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """#651-Review-Fund (Codex): eine fehlgeschlagene ``apt-get install`` darf
    den Cleanup (dpkg -r + Rückstandsprüfung) nicht überspringen – ``apt-get``
    kann vor dem Fehlschlag schon Dateien/Paketeinträge hinterlassen haben."""
    results = {"apt-get install": smoke.CommandResult(1)}
    runner, calls = _recording_runner(results)
    report = smoke.SmokeReport()
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
        screenshot_dir=tmp_path / "shots",
    )
    assert not result.passed
    assert any("deb-Installation fehlgeschlagen" in n for n in result.notes)
    assert any(c.startswith("sudo dpkg -r bgremover") for c in calls)
    assert any(c.startswith("dpkg -s bgremover") for c in calls)
    # Kein Start-Versuch für das installierte AppImage nach Fehlschlag.
    assert not any("smoke_launch.py" in c and "BgRemover.AppImage" in c for c in calls)


def test_linux_smoke_runs_ai_selfcheck_for_ai_variant(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """#642-Fund: KI-Selbsttest fehlte im Abnahme-Smoke, obwohl release-linux.yml
    ihn fuer -ai-Artefakte beim Build bereits faehrt."""
    runner, calls = _recording_runner(_CLEAN_DEB)
    report = smoke.SmokeReport()
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
        screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    selfcheck_notes = [n for n in result.notes if "KI-Selbsttest ok" in n]
    assert len(selfcheck_notes) == 2  # AppImage + deb
    assert any("BGREMOVER_AI_SELFCHECK=1" in c for c in calls)


def test_linux_smoke_skips_ai_selfcheck_for_non_ai_variant(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    artefacts = [
        "/tmp/BgRemover-linux-raspberrypi-arm64.AppImage",
        "/tmp/BgRemover-linux-raspberrypi-arm64.deb",
    ]
    runner, calls = _recording_runner(_CLEAN_DEB)
    report = smoke.SmokeReport()
    result = smoke.run_linux_smoke(
        artefacts, report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
        screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    assert not any("KI-Selbsttest" in n for n in result.notes)
    assert not any("BGREMOVER_AI_SELFCHECK" in c for c in calls)


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


def test_macos_smoke_passes_with_retina_and_hardware(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64-ai.dmg"], report, _runner_factory(_MACOS_MOUNT),
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
        screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    assert result.gl_diagnostic == "Apple / Apple M3 Max / 2.1 Metal - 90.5"


def test_macos_smoke_fails_on_low_dpi(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/x.dmg"], report, _runner_factory({}),
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=1.0,
        screenshot_dir=tmp_path / "shots",
    )
    assert not result.passed
    assert any("Retina" in n for n in result.notes)


def test_macos_smoke_copies_to_temp_and_clears_quarantine(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """#643-Fund: Start muss von einer Temp-Kopie laufen, nicht vom read-only
    DMG-Mount – sonst laesst sich die Quarantaene nie entfernen (Gatekeeper)."""
    runner, calls = _recording_runner(_MACOS_MOUNT)
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64.dmg"], report, runner,
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
        screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    assert any(c.startswith("cp -R /Volumes/BgRemover/BgRemover.app") for c in calls)
    assert any("xattr -r -d com.apple.quarantine" in c and smoke.TEMP_DMG_ROOT in c for c in calls)
    assert any(f"{smoke.TEMP_DMG_ROOT}/BgRemover.app/Contents/MacOS/BgRemover" in c for c in calls)
    # Original bleibt unangetastet – kein xattr/App-Start direkt auf dem Mount.
    assert not any(c.startswith("xattr") and "/Volumes/" in c for c in calls)


def test_macos_smoke_detaches_dmg_before_starting_app(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """#651-Review-Fund (Codex): das DMG darf nicht waehrend des (bis zu 240s
    langen) App-Starts gemountet bleiben – detach muss vor dem ersten
    Start-Guard-Aufruf passieren, sonst bleibt bei einem abgebrochenen Job
    ein Volume unnoetig lange haengen."""
    runner, calls = _recording_runner(_MACOS_MOUNT)
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64.dmg"], report, runner,
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
        screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    detach_index = next(i for i, c in enumerate(calls) if c.startswith("hdiutil detach"))
    guard_index = next(i for i, c in enumerate(calls) if "smoke_launch.py" in c)
    assert detach_index < guard_index


def test_macos_smoke_detaches_when_mount_point_unparseable(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
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
        screenshot_dir=tmp_path / "shots",
    )
    assert not result.passed
    assert any("Mount-Pfad nicht erkannt" in n for n in result.notes)
    assert any(c == "hdiutil detach /dev/disk9" for c in calls)


def test_macos_smoke_runs_ai_selfcheck_for_ai_variant(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    runner, calls = _recording_runner(_MACOS_MOUNT)
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64-ai.dmg"], report, runner,
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
        screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    assert any("KI-Selbsttest ok" in n for n in result.notes)
    assert any("BGREMOVER_AI_SELFCHECK=1" in c for c in calls)


def test_macos_smoke_skips_ai_selfcheck_for_non_ai_variant(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    runner, calls = _recording_runner(_MACOS_MOUNT)
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64.dmg"], report, runner,
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
        screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    assert not any("KI-Selbsttest" in n for n in result.notes)
    assert not any("BGREMOVER_AI_SELFCHECK" in c for c in calls)


def test_macos_smoke_reports_startup_time(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64.dmg"], report, _runner_factory(_MACOS_MOUNT),
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
        screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    assert any("Startzeit" in n for n in result.notes)


# ── Nativer 3D-Screenshot-Nachweis (#648) ───────────────────────────────────


def test_linux_smoke_writes_native_3d_screenshot_and_provenance(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    screenshot_dir = tmp_path / "shots"
    report = smoke.SmokeReport()
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, _runner_factory(_CLEAN_DEB),
        prober=lambda: "Broadcom / V3D 7.1 / 3.1", screenshot_dir=screenshot_dir,
    )
    assert result.passed
    assert sum("Nativer 3D-Screenshot ok" in n for n in result.notes) == 2
    for artifact_class in ("appimage", "deb"):
        target = screenshot_dir / smoke.NATIVE_3D_SCREENSHOT_NAMES[artifact_class]
        assert target.is_file()
        sidecar = json.loads(
            target.with_name(target.name + ".json").read_text(encoding="utf-8"),
        )
        assert sidecar["gl_provenance"] == "Broadcom / V3D 7.1 / 3.1"


def test_linux_smoke_native_3d_screenshot_runs_for_appimage_and_deb(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """AppImage und installiertes ``.deb`` erhalten getrennte Nachweise."""
    runner, calls = _recording_runner(_CLEAN_DEB)
    report = smoke.SmokeReport()
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
        screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    native_calls = [c for c in calls if "smoke_launch.py" in c and "--native" in c]
    assert len(native_calls) == 2
    assert any(
        smoke.NATIVE_3D_SCREENSHOT_NAMES["appimage"] in call for call in native_calls
    )
    assert any(smoke.NATIVE_3D_SCREENSHOT_NAMES["deb"] in call for call in native_calls)


def test_native_3d_screenshot_passes_readiness_timeout_to_hook(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Reicht ``NATIVE_3D_READINESS_TIMEOUT_MS`` als ``--env`` an den
    Automationshook durch (Codex-Fund, PR #652) – sonst bliebe das für
    schwache Zielhardware großzügigere ``NATIVE_3D_TIMEOUT`` für den Hook
    selbst wirkungslos, weil er an seinem eigenen 25s-Default scheitert."""
    runner, calls = _recording_runner({})
    report = smoke.SmokeReport()
    smoke._native_3d_screenshot(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, screenshot_dir=tmp_path / "shots",
        screenshot_name=smoke.NATIVE_3D_SCREENSHOT_NAMES["appimage"],
    )
    native_calls = [c for c in calls if "smoke_launch.py" in c and "--native" in c]
    assert len(native_calls) == 1
    assert (
        f"BGREMOVER_SCREENSHOT_3D_TIMEOUT_MS={smoke.NATIVE_3D_READINESS_TIMEOUT_MS}"
        in native_calls[0]
    )
    assert smoke.NATIVE_3D_READINESS_TIMEOUT_MS < smoke.NATIVE_3D_TIMEOUT * 1000


def test_macos_smoke_writes_native_3d_screenshot_and_provenance(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    screenshot_dir = tmp_path / "shots"
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64.dmg"], report, _runner_factory(_MACOS_MOUNT),
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
        screenshot_dir=screenshot_dir,
    )
    assert result.passed
    assert any("Nativer 3D-Screenshot ok" in n for n in result.notes)
    assert (screenshot_dir / smoke.NATIVE_3D_SCREENSHOT_NAMES["dmg"]).is_file()


def test_native_3d_screenshot_fails_on_software_renderer(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    report = smoke.SmokeReport()
    runner = _runner_factory({}, native_screenshot_diagnostic="Mesa / llvmpipe / 4.5")
    smoke._native_3d_screenshot(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, screenshot_dir=tmp_path / "shots",
        screenshot_name=smoke.NATIVE_3D_SCREENSHOT_NAMES["appimage"],
    )
    assert not report.passed
    assert any("Software-Renderer" in n for n in report.notes)


def test_native_3d_screenshot_fails_when_process_exits_nonzero(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    report = smoke.SmokeReport()
    runner = _runner_factory({}, native_screenshot_rc=1)
    smoke._native_3d_screenshot(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, screenshot_dir=tmp_path / "shots",
        screenshot_name=smoke.NATIVE_3D_SCREENSHOT_NAMES["appimage"],
    )
    assert not report.passed
    assert any(
        "Nativer 3D-Screenshot fehlgeschlagen" in n and "x.AppImage" in n for n in report.notes
    )
    assert not (
        tmp_path / "shots" / smoke.NATIVE_3D_SCREENSHOT_NAMES["appimage"]
    ).exists()


def test_native_3d_screenshot_fails_when_sidecar_missing(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Der Automationshook meldet Exit 0, schreibt aber (unerwartet) keine
    Provenance-Sidecar – der Nachweis darf das nicht stillschweigend als
    erfüllt werten."""
    screenshot_name = smoke.NATIVE_3D_SCREENSHOT_NAMES["appimage"]
    target = tmp_path / "shots" / screenshot_name

    def runner(cmd: list[str]) -> smoke.CommandResult:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"png-ohne-sidecar")
        return smoke.CommandResult(0)

    report = smoke.SmokeReport()
    smoke._native_3d_screenshot(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, screenshot_dir=tmp_path / "shots", screenshot_name=screenshot_name,
    )
    assert not report.passed
    assert any("Provenance-JSON" in n or "kein Screenshot" in n for n in report.notes)


def test_native_3d_screenshot_runs_once_even_when_called_directly_twice(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    calls: list[list[str]] = []

    def runner(cmd: list[str]) -> smoke.CommandResult:
        calls.append(cmd)
        return _fake_native_screenshot(cmd, "Broadcom / V3D 7.1 / 3.1", 0) or smoke.CommandResult(0)

    report = smoke.SmokeReport()
    screenshot_dir = tmp_path / "shots"
    screenshot_name = smoke.NATIVE_3D_SCREENSHOT_NAMES["appimage"]
    smoke._native_3d_screenshot(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, screenshot_dir=screenshot_dir, screenshot_name=screenshot_name,
    )
    smoke._native_3d_screenshot(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, screenshot_dir=screenshot_dir, screenshot_name=screenshot_name,
    )
    assert len(calls) == 1
    assert report.native_3d_attempted == {screenshot_name}


def test_main_writes_failed_evidence_and_returns_nonzero(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
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
