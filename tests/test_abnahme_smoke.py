"""Tests für die Smoke-Orchestrierung (#642/#643, nativer 3D-Screenshot #648) mit
gefälschten Kommandos."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

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


def test_probe_diagnostic_keeps_qapplication_alive_through_probe(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Regression: probe_3d_capability baut einen QOpenGLContext, der ohne
    # QApplication mangels Plattformintegration scheitert – live auf den
    # Mac-/Pi-Abnahme-Runnern als leere Diagnose beobachtet, obwohl derselbe
    # GL-Kontext im gepackten Artefakt (das immer eine QApplication laufen
    # hat) klaglos funktioniert. Patcht nur das Modul-lokale ``probe.
    # QApplication`` (nicht die geteilte PyQt6.QtWidgets-Klasse) – sonst
    # verwechselt pytest-qt die Fake-Instanz mit der echten Session-App und
    # reißt die ganze restliche Suite mit.
    #
    # Codex-Fund zu PR #655 (P1): eine unzugewiesene Ausdrucksanweisung
    # "QApplication.instance() or QApplication(sys.argv)" hält in CPython
    # keine Referenz – das Objekt kann sofort nach der Anweisung wieder
    # freigegeben werden, bevor probe_3d_capability() den GL-Kontext
    # aufbaut. ``__del__`` macht diese Lebensdauer beobachtbar (statt sie wie
    # in der Vorversion künstlich per Klassenattribut zu verlängern, was den
    # Fund erst maskiert hatte). ``instance()`` gibt immer ``None`` zurück,
    # damit jeder Aufruf eine frische Instanz erzwingt.
    import bgremover.preview3d_capability as cap

    class _FakeApp:
        live_count = 0

        @classmethod
        def instance(cls):  # type: ignore[no-untyped-def]
            return None

        def __init__(self, argv: list[str]) -> None:
            _FakeApp.live_count += 1

        def __del__(self) -> None:
            _FakeApp.live_count -= 1

    def fake_probe_3d_capability(*, use_cache: bool = True):  # type: ignore[no-untyped-def]
        assert _FakeApp.live_count == 1, "QApplication wurde vor dem GL-Probe bereits freigegeben"
        return cap.RendererCapability(ok=True, diagnostic="Fake / GPU / 1.0")

    monkeypatch.setattr(probe, "QApplication", _FakeApp)
    monkeypatch.setattr(cap, "probe_3d_capability", fake_probe_3d_capability)

    assert probe.probe_diagnostic() == "Fake / GPU / 1.0"


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


def _fake_acceptance_extra(
    cmd: list[str], ok: bool | None, rc: int,
) -> smoke.CommandResult | None:
    """Simuliert den echten Automationshook (``bgremover.acceptance_smoke``) für
    den ``smoke_launch.py --native``-Aufruf mit ``BGREMOVER_ACCEPTANCE_EXTRA``:
    schreibt die Evidenz-JSON an den übergebenen Pfad, genau wie der laufende
    gepackte Prozess es täte. ``ok=None`` lässt den Aufruf unbehandelt (fällt auf
    die normale Substring-Matching-Logik zurück)."""
    if ok is None or "--native" not in cmd:
        return None
    target: Path | None = None
    for arg in cmd:
        if arg.startswith("BGREMOVER_ACCEPTANCE_EXTRA="):
            target = Path(arg.split("=", 1)[1])
    if target is None:
        return None
    if rc != 0:
        return smoke.CommandResult(rc, stderr="acceptance-extra-Hook fehlgeschlagen")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps({
            "schema": smoke.ACCEPTANCE_EXTRA_SCHEMA,
            "ok": ok,
            "eufymake_export": {"ok": ok, "message": "ok" if ok else "nope"},
            "v270_project_open": {"ok": ok, "message": "ok" if ok else "nope"},
            "visible_version": {"ok": ok, "message": "ok" if ok else "nope"},
            "project_copy": {"ok": ok, "message": "ok" if ok else "nope"},
            "missing_component": {"ok": ok, "message": "ok" if ok else "nope"},
            "laufzeit_herkunft": {
                "bgremover_datei": "/opt/bundle/bgremover/__init__.py",
                "ai_process_datei": "/opt/bundle/bgremover/ai_process.py",
                "interpreter": "/opt/bundle/python", "eingefroren": True,
                "arbeitsverzeichnis": "/tmp", "sys_path_0": "/opt/bundle",
                "kindprozess": {
                    "bgremover_datei": "/opt/bundle/bgremover/__init__.py",
                    "ai_process_datei": "/opt/bundle/bgremover/ai_process.py",
                    "sys_path_0": "/opt/bundle",
                },
            },
        }),
        encoding="utf-8",
    )
    return smoke.CommandResult(0)


def _runner_factory(
    results: dict[str, smoke.CommandResult],
    default_rc: int = 0,
    native_screenshot_diagnostic: str | None = "Broadcom / V3D 7.1 / 3.1",
    native_screenshot_rc: int = 0,
    acceptance_extra_ok: bool | None = True,
    acceptance_extra_rc: int = 0,
):
    """Fake-Runner: matcht anhand eines Substrings im Kommando; simuliert den
    nativen 3D-Screenshot- und den EufyMake/2.7.0-Zusatz-Hook standardmäßig als
    Erfolg (siehe ``_fake_native_screenshot``/``_fake_acceptance_extra``)."""

    def runner(cmd: list[str]) -> smoke.CommandResult:
        handled = _fake_native_screenshot(cmd, native_screenshot_diagnostic, native_screenshot_rc)
        if handled is not None:
            return handled
        handled = _fake_acceptance_extra(cmd, acceptance_extra_ok, acceptance_extra_rc)
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
    acceptance_extra_ok: bool | None = True,
    acceptance_extra_rc: int = 0,
):
    """Wie ``_runner_factory``, protokolliert zusätzlich jedes Kommando (join)."""
    calls: list[str] = []

    def runner(cmd: list[str]) -> smoke.CommandResult:
        calls.append(" ".join(cmd))
        handled = _fake_native_screenshot(cmd, native_screenshot_diagnostic, native_screenshot_rc)
        if handled is not None:
            return handled
        handled = _fake_acceptance_extra(cmd, acceptance_extra_ok, acceptance_extra_rc)
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
    native_calls = [c for c in calls if "BGREMOVER_SCREENSHOT_3D=" in c]
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


# ── EufyMake-Export-/2.7.0-Projekt-Zusatznachweis (#685-Review) ─────────────


def test_acceptance_extra_ok_records_success(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    runner = _runner_factory({})
    report = smoke.SmokeReport()
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, evidence_dir=tmp_path / "acceptance_extra", artifact_class="appimage",
    )
    assert report.passed
    assert any("EufyMake/2.7.0-Zusatznachweis ok" in n for n in report.notes)
    target = tmp_path / "acceptance_extra" / smoke.ACCEPTANCE_EXTRA_NAMES["appimage"]
    assert target.is_file()


def test_acceptance_extra_passes_v270_fixture_path(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Der laufende gepackte Prozess bekommt den Fixture-Pfad aus dem
    Source-Checkout durchgereicht (#685)."""
    runner, calls = _recording_runner({})
    report = smoke.SmokeReport()
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, evidence_dir=tmp_path / "acceptance_extra", artifact_class="appimage",
    )
    native_calls = [c for c in calls if "BGREMOVER_ACCEPTANCE_EXTRA=" in c]
    assert len(native_calls) == 1
    assert f"BGREMOVER_ACCEPTANCE_EXTRA_V270_PROJECT={smoke.V270_FIXTURE}" in native_calls[0]


def test_acceptance_extra_fails_when_process_exits_nonzero(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    runner = _runner_factory({}, acceptance_extra_rc=1)
    report = smoke.SmokeReport()
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, evidence_dir=tmp_path / "acceptance_extra", artifact_class="appimage",
    )
    assert not report.passed
    assert any(
        "EufyMake/2.7.0-Zusatznachweis fehlgeschlagen" in n and "x.AppImage" in n
        for n in report.notes
    )


def test_acceptance_extra_fails_when_evidence_missing(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Exit 0, aber (unerwartet) keine Evidenz-JSON – darf nicht stillschweigend
    als erfüllt gelten."""

    def runner(cmd: list[str]) -> smoke.CommandResult:
        return smoke.CommandResult(0)

    report = smoke.SmokeReport()
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, evidence_dir=tmp_path / "acceptance_extra", artifact_class="appimage",
    )
    assert not report.passed
    assert any("keine Evidenz erzeugt" in n for n in report.notes)


def test_acceptance_extra_fails_on_unreadable_evidence(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    evidence_dir = tmp_path / "acceptance_extra"
    target = evidence_dir / smoke.ACCEPTANCE_EXTRA_NAMES["appimage"]

    def runner(cmd: list[str]) -> smoke.CommandResult:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{kaputt", encoding="utf-8")
        return smoke.CommandResult(0)

    report = smoke.SmokeReport()
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, evidence_dir=evidence_dir, artifact_class="appimage",
    )
    assert not report.passed
    assert any("Evidenz-JSON unlesbar" in n for n in report.notes)


def test_acceptance_extra_fails_when_payload_reports_not_ok(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    runner = _runner_factory({}, acceptance_extra_ok=False)
    report = smoke.SmokeReport()
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, evidence_dir=tmp_path / "acceptance_extra", artifact_class="appimage",
    )
    assert not report.passed
    assert any(
        "EufyMake/2.7.0-Zusatznachweis fehlgeschlagen" in n
        and "eufymake_export=" in n and "v270_project_open=" in n
        for n in report.notes
    )


def test_acceptance_extra_runs_once_even_when_called_directly_twice(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    calls: list[list[str]] = []

    def runner(cmd: list[str]) -> smoke.CommandResult:
        calls.append(cmd)
        return _fake_acceptance_extra(cmd, True, 0) or smoke.CommandResult(0)

    report = smoke.SmokeReport()
    evidence_dir = tmp_path / "acceptance_extra"
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, evidence_dir=evidence_dir, artifact_class="appimage",
    )
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage",
        report=report, evidence_dir=evidence_dir, artifact_class="appimage",
    )
    assert len(calls) == 1
    assert report.acceptance_extra_attempted == {"appimage"}


def test_linux_smoke_runs_acceptance_extra_for_appimage_and_deb(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    runner, calls = _recording_runner(_CLEAN_DEB)
    report = smoke.SmokeReport()
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
        screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    acceptance_calls = [c for c in calls if "BGREMOVER_ACCEPTANCE_EXTRA=" in c]
    assert len(acceptance_calls) == 2
    assert any(smoke.ACCEPTANCE_EXTRA_NAMES["appimage"] in c for c in acceptance_calls)
    assert any(smoke.ACCEPTANCE_EXTRA_NAMES["deb"] in c for c in acceptance_calls)


def test_acceptance_extra_rejects_schema3_evidence_without_provenance(  # type: ignore[no-untyped-def]
    tmp_path: Path,
) -> None:
    """Codex-P2 (#738): Schema 3 sagt zu, die Herkunft bei jedem Lauf
    auszuweisen. Fehlt sie trotz passender Schemaversion, ist der Erzeuger
    defekt – still durchwinken hieße, genau die Zusicherung zu brechen, für
    die die Schemaversion angehoben wurde."""
    def runner(cmd: list[str]) -> smoke.CommandResult:
        target = next(
            Path(a.split("=", 1)[1]) for a in cmd
            if a.startswith("BGREMOVER_ACCEPTANCE_EXTRA=")
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({
            "schema": smoke.ACCEPTANCE_EXTRA_SCHEMA,
            "ok": True,
            **{k: {"ok": True, "message": "ok"} for k in smoke.ACCEPTANCE_EXTRA_REQUIRED},
            # laufzeit_herkunft fehlt
        }), encoding="utf-8")
        return smoke.CommandResult(0)

    report = smoke.SmokeReport()
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage", report=report,
        evidence_dir=tmp_path / "acceptance_extra", artifact_class="appimage",
    )
    assert not report.passed
    assert any("laufzeit_herkunft" in n for n in report.notes)


def test_acceptance_extra_prints_parent_and_child_provenance(  # type: ignore[no-untyped-def]
    tmp_path: Path, capsys,
) -> None:
    """Die Herkunft muss bei JEDEM Lauf im Joblog stehen – auch bei Erfolg;
    ein grüner Lauf aus dem falschen Pfad ist der gefährlichere Fall. Der
    spawn-Kindprozess bekommt eine eigene Zeile, weil er Module aus einem
    anderen Pfad laden kann als sein Elternprozess (#738)."""
    runner = _runner_factory({})
    report = smoke.SmokeReport()
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage", report=report,
        evidence_dir=tmp_path / "acceptance_extra", artifact_class="appimage",
    )
    assert report.passed
    out = capsys.readouterr().out
    assert "[herkunft] x.AppImage:" in out
    assert "[herkunft-kind] x.AppImage:" in out
    assert "/opt/bundle/bgremover/ai_process.py" in out

    # Und bei einem FEHLSCHLAG erst recht: Dort ist die Frage „stammte der
    # geprüfte Code überhaupt aus dem Bundle?" am wichtigsten.
    failing = _runner_factory({}, acceptance_extra_ok=False)
    report2 = smoke.SmokeReport()
    smoke._acceptance_extra(
        failing, ["launch"], match="x", max_instances=1, label="y.AppImage", report=report2,
        evidence_dir=tmp_path / "acceptance_extra2", artifact_class="appimage",
    )
    assert not report2.passed
    out2 = capsys.readouterr().out
    assert "[herkunft] y.AppImage:" in out2
    assert "[herkunft-kind] y.AppImage:" in out2


def test_acceptance_extra_rejects_older_hook_schema(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Codex-P1 (#734): Ein Kandidat mit dem **Vorgänger-Hook** schreibt
    dieselbe Struktur mit ``ok: true``, aber ohne ``visible_version``/
    ``project_copy``. Der frühere ``ok``-Kurzschluss meldete ihn grün, obwohl
    die neuen Prüfungen dort gar nicht existieren – ein umbenanntes oder
    veraltetes Artefakt wäre so unbemerkt durch die Abnahme gelaufen."""
    def runner(cmd: list[str]) -> smoke.CommandResult:
        target = next(
            Path(a.split("=", 1)[1]) for a in cmd
            if a.startswith("BGREMOVER_ACCEPTANCE_EXTRA=")
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({
            "schema": 1,  # alter Hook
            "ok": True,
            "eufymake_export": {"ok": True, "message": "ok"},
            "v270_project_open": {"ok": True, "message": "ok"},
            "missing_component": {"ok": True, "message": "ok"},
        }), encoding="utf-8")
        return smoke.CommandResult(0)

    report = smoke.SmokeReport()
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage", report=report,
        evidence_dir=tmp_path / "acceptance_extra", artifact_class="appimage",
    )
    assert not report.passed
    assert any("Evidenz-Schema 1" in n and "älteren Hook" in n for n in report.notes)


def test_acceptance_extra_rejects_missing_sub_results_despite_top_level_ok(  # type: ignore[no-untyped-def]
    tmp_path: Path,
) -> None:
    """Auch bei passender Schemaversion muss **jede** erwartete Teilprüfung
    vorhanden sein: Ein fehlender Schlüssel ist ein Fehlschlag, nicht
    „nicht zutreffend" (Codex-P1, #734)."""
    def runner(cmd: list[str]) -> smoke.CommandResult:
        target = next(
            Path(a.split("=", 1)[1]) for a in cmd
            if a.startswith("BGREMOVER_ACCEPTANCE_EXTRA=")
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({
            "schema": smoke.ACCEPTANCE_EXTRA_SCHEMA,
            "ok": True,
            "eufymake_export": {"ok": True, "message": "ok"},
            "v270_project_open": {"ok": True, "message": "ok"},
            "missing_component": {"ok": True, "message": "ok"},
            "visible_version": {"ok": True, "message": "ok"},
            # project_copy fehlt
        }), encoding="utf-8")
        return smoke.CommandResult(0)

    report = smoke.SmokeReport()
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage", report=report,
        evidence_dir=tmp_path / "acceptance_extra", artifact_class="appimage",
    )
    assert not report.passed
    assert any("Teilergebnisse fehlen" in n and "project_copy" in n for n in report.notes)


def test_acceptance_extra_passes_expected_version_from_artifact_name(  # type: ignore[no-untyped-def]
    tmp_path: Path,
) -> None:
    """#686: Die Soll-Version für die sichtbare Produktversion kommt aus dem
    Artefaktdateinamen und wird als eigene Umgebungsvariable durchgereicht –
    nur so prüft das Paket gegen einen *externen* Wert statt gegen sich selbst."""
    runner, calls = _recording_runner({})
    report = smoke.SmokeReport()
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1,
        label="BgRemover-2.7.1-linux-x86_64-ai.AppImage", report=report,
        evidence_dir=tmp_path / "acceptance_extra", artifact_class="appimage",
    )
    assert report.passed
    assert any("BGREMOVER_ACCEPTANCE_EXTRA_VERSION=2.7.1" in c for c in calls)


def test_acceptance_extra_omits_version_for_unversioned_artifact_name(  # type: ignore[no-untyped-def]
    tmp_path: Path,
) -> None:
    """Folgt der Name nicht dem Release-Schema, wird **kein** Sollwert gesetzt –
    die Prüfung fällt auf die schwächere Selbstauskunft zurück, statt einen
    geratenen Wert zu vergleichen und dadurch falsch rot zu werden."""
    runner, calls = _recording_runner({})
    report = smoke.SmokeReport()
    smoke._acceptance_extra(
        runner, ["launch"], match="x", max_instances=1, label="x.AppImage", report=report,
        evidence_dir=tmp_path / "acceptance_extra", artifact_class="appimage",
    )
    assert report.passed
    assert not any("BGREMOVER_ACCEPTANCE_EXTRA_VERSION" in c for c in calls)


def test_macos_smoke_runs_acceptance_extra(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    report = smoke.SmokeReport()
    result = smoke.run_macos_smoke(
        ["/tmp/BgRemover-macos-arm64.dmg"], report, _runner_factory(_MACOS_MOUNT),
        prober=lambda: "Apple / Apple M3 Max / 2.1 Metal - 90.5", scale_factor=2.0,
        screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    assert any("EufyMake/2.7.0-Zusatznachweis ok" in n for n in result.notes)


# ── Strukturierte Wächter-Ergebnisse (#642-Nachtrag) ────────────────────────


def test_record_guard_parses_structured_result_line() -> None:
    report = smoke.SmokeReport()
    stdout = smoke.sl.format_result_line(
        match_token="x", timeout=120.0, max_instances=2, peak_instances=2,
        exit_code=0, status="ok", detail="sauber gestartet",
    )
    smoke._record_guard(
        report, smoke.CommandResult(0, stdout=stdout, stderr=""),
        phase="start", artifact_class="appimage",
    )
    assert report.guard_results == [{
        "phase": "start", "artefaktklasse": "appimage", "exit_code": 0,
        "peak_instanzen": 2, "status": "ok", "log": f"stdout:\n{stdout}",
    }]


def test_record_guard_falls_back_to_unbekannt_without_result_line() -> None:
    """Ein gefälschter Test-Runner ohne echten Subprozess liefert keine
    ``SMOKE_LAUNCH_RESULT``-Zeile – das darf den Smoke nicht zum Scheitern
    bringen, sondern degradiert nur die Wächter-Daten zu ``unbekannt``."""
    report = smoke.SmokeReport()
    smoke._record_guard(
        report, smoke.CommandResult(1, stderr="boom"),
        phase="start", artifact_class="deb",
    )
    entry = report.guard_results[0]
    assert entry["status"] == "unbekannt"
    assert entry["peak_instanzen"] is None
    assert entry["exit_code"] == 1
    assert entry["log"] == "stderr:\nboom"


def test_record_guard_prefers_parsed_exit_code_over_smoke_launch_returncode() -> None:
    """Codex-Fund zu PR #657: ``smoke_launch.py`` normalisiert seinen eigenen
    Exit-Code auf 0/1 – der echte Exit-Code des gewächten Prozesses (z. B. 7
    bei einem Start-Crash) steckt nur in der geparsten Nutzlast und darf nicht
    durch den gröberen 0/1-Wert überschrieben werden."""
    report = smoke.SmokeReport()
    stdout = smoke.sl.format_result_line(
        match_token="x", timeout=120.0, max_instances=1, peak_instances=1,
        exit_code=7, status="start_crash", detail="Bundle endete mit Exit-Code 7",
    )
    smoke._record_guard(
        report, smoke.CommandResult(1, stdout=stdout, stderr=""),
        phase="start", artifact_class="appimage",
    )
    assert report.guard_results[0]["exit_code"] == 7


def test_record_guard_combines_stdout_and_stderr_in_log() -> None:
    """Codex-Fund zu PR #657: Diagnose kann auf stdout ODER stderr landen –
    ``log`` darf nicht nur einen der beiden Streams behalten."""
    report = smoke.SmokeReport()
    smoke._record_guard(
        report, smoke.CommandResult(1, stdout="app-diagnose auf stdout", stderr="wächter-fehler"),
        phase="start", artifact_class="deb",
    )
    log = report.guard_results[0]["log"]
    assert "app-diagnose auf stdout" in log
    assert "wächter-fehler" in log


def test_record_guard_prints_summary_for_the_workflow_log(capsys) -> None:  # type: ignore[no-untyped-def]
    """Codex-Fund zu PR #657: ``_default_runner`` fängt den Subprozess mit
    ``capture_output=True`` ab – ohne einen eigenen Print landet die
    Wächter-Zusammenfassung nie im Actions-Job-Log, obwohl genau das der
    Zweck der Aufgabe war."""
    report = smoke.SmokeReport()
    stdout = smoke.sl.format_result_line(
        match_token="x", timeout=120.0, max_instances=1, peak_instances=1,
        exit_code=0, status="ok", detail="sauber gestartet",
    )
    smoke._record_guard(
        report, smoke.CommandResult(0, stdout=stdout, stderr=""),
        phase="start", artifact_class="appimage",
    )
    out = capsys.readouterr().out
    assert "phase=start" in out
    assert "artefaktklasse=appimage" in out
    assert "status=ok" in out
    assert "exit_code=0" in out
    assert "peak_instanzen=1" in out


def _guarded_runner(*, clean_deb: dict[str, smoke.CommandResult] = _CLEAN_DEB):
    """Fake-Runner, der ``smoke_launch.py``-Startaufrufe (ohne ``--native``)
    mit einer echten ``SMOKE_LAUNCH_RESULT``-Zeile beantwortet – simuliert den
    strukturierten Ausgabepfad aus dem #642-Nachtrag."""

    def runner(cmd: list[str]) -> smoke.CommandResult:
        handled = _fake_native_screenshot(cmd, "Broadcom / V3D 7.1 / 3.1", 0)
        if handled is not None:
            return handled
        handled = _fake_acceptance_extra(cmd, True, 0)
        if handled is not None:
            return handled
        joined = " ".join(cmd)
        if "smoke_launch.py" in joined and "--native" not in cmd:
            stdout = smoke.sl.format_result_line(
                match_token="x", timeout=120.0, max_instances=1, peak_instances=1,
                exit_code=0, status="ok", detail="sauber gestartet",
            )
            return smoke.CommandResult(0, stdout=stdout)
        for token, result in clean_deb.items():
            if token in joined:
                return result
        return smoke.CommandResult(0)

    return runner


def test_linux_smoke_collects_structured_guard_results_per_phase_and_class(
    tmp_path: Path,
) -> None:
    """Vertragstest zum #642-Schließkriterium: Artefaktklasse+Phase, Exit-Code,
    Peak-Instanzen, Status und Log müssen je Wächter-Aufruf strukturiert
    vorliegen – für Start, KI-Selbsttest und nativen 3D-Screenshot-Nachweis,
    getrennt für AppImage und deb."""
    report = smoke.SmokeReport()
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, _guarded_runner(), prober=lambda: "Broadcom / V3D 7.1 / 3.1",
        screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    phases = {(g["phase"], g["artefaktklasse"]) for g in result.guard_results}
    assert phases == {
        ("ki_selbsttest", "appimage"), ("start", "appimage"), ("nativer_3d_screenshot", "appimage"),
        ("acceptance_extra", "appimage"),
        ("ki_selbsttest", "deb"), ("start", "deb"), ("nativer_3d_screenshot", "deb"),
        ("acceptance_extra", "deb"),
    }
    required_keys = {"phase", "artefaktklasse", "exit_code", "peak_instanzen", "status", "log"}
    for entry in result.guard_results:
        assert required_keys <= set(entry)
    start_entries = [g for g in result.guard_results if g["phase"] == "start"]
    assert all(g["status"] == "ok" and g["peak_instanzen"] == 1 for g in start_entries)


def test_linux_smoke_records_guard_result_even_on_start_failure(tmp_path: Path) -> None:
    """Ein fehlgeschlagener Start darf nicht stillschweigend ohne Wächter-Eintrag
    bleiben – sonst fehlt genau im interessanten Fall die Diagnose."""
    report = smoke.SmokeReport()
    runner = _runner_factory({**_CLEAN_DEB, "smoke_launch.py": smoke.CommandResult(1)})
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, runner, prober=lambda: "Broadcom / V3D 7.1 / 3.1",
        screenshot_dir=tmp_path / "shots",
    )
    assert not result.passed
    start_entries = [g for g in result.guard_results if g["phase"] == "start"]
    assert start_entries
    assert all(g["exit_code"] == 1 for g in start_entries)


def test_main_writes_guard_results_into_evidence(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Der volle ``main()``-Pfad muss ``waechter_ergebnisse`` ins
    ``evidenz.json`` schreiben (#642-Schließkriterium)."""
    inner_runner = _guarded_runner()
    monkeypatch.setattr(smoke, "_default_runner", lambda cmd: inner_runner(cmd))
    monkeypatch.setattr(smoke, "_default_prober", lambda: "Broadcom / V3D 7.1 / 3.1")

    (tmp_path / "artefakte").mkdir()
    evidence = {
        "schema": 1, "kind": "abnahme-evidenz", "platform": "linux-arm64",
        "status": "platzhalter", "commit_sha": "abc",
        "quelle": {"art": "release-tag", "wert": "v2.7.0"},
        "artefakte": [
            {"name": "x-ai.AppImage", "sha256": "cafe", "bytes": 1},
            {"name": "x-ai.deb", "sha256": "babe", "bytes": 1},
        ],
        "umgebung": {"os": "linux", "arch": "aarch64", "python": "3.12", "runner": "r"},
        "gl_provenance": None, "waechter_ergebnisse": [],
        "erzeugt_am": "2026-07-22T00:00:00+00:00",
        "hinweise": ["Platzhalter-Smoke aus #641 – echte Smokes folgen mit #642/#643."],
    }
    (tmp_path / "evidenz.json").write_text(json.dumps(evidence), encoding="utf-8")

    rc = smoke.main(["--platform", "linux-arm64", "--evidence-dir", str(tmp_path)])
    assert rc == 0
    written = json.loads((tmp_path / "evidenz.json").read_text(encoding="utf-8"))
    assert written["waechter_ergebnisse"]
    for entry in written["waechter_ergebnisse"]:
        assert {"phase", "artefaktklasse", "exit_code", "peak_instanzen", "status", "log"} <= set(
            entry
        )


def test_command_detail_prefers_stderr_and_falls_back(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Ungewächte Kommandos (apt-get, hdiutil) laufen mit ``capture_output``;
    ohne diesen Helfer landete ihre Diagnose nirgends im Joblog (Codex-Fund
    auf PR #735)."""
    assert smoke._command_detail(smoke.CommandResult(1, stderr="  boom  ")) == "boom"
    # Kein stderr → stdout, damit auch Werkzeuge erfasst sind, die auf stdout melden.
    assert smoke._command_detail(smoke.CommandResult(1, stdout="details")) == "details"
    assert smoke._command_detail(smoke.CommandResult(1)) == "keine Ausgabe"


def test_dmg_mount_failure_reports_the_command_output(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Ein fehlgeschlagener DMG-Mount muss sagen, *woran* er scheiterte."""
    def runner(cmd: list[str]) -> smoke.CommandResult:
        if cmd[:2] == ["hdiutil", "attach"]:
            return smoke.CommandResult(1, stderr="hdiutil: attach failed - no mountable file systems")
        return smoke.CommandResult(0)

    report = smoke.SmokeReport()
    smoke._macos_dmg("/tmp/x.dmg", report, runner, tmp_path / "shots")
    assert not report.passed
    assert any("no mountable file systems" in n for n in report.notes)


def test_main_prints_guard_log_for_a_failing_phase(tmp_path, monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    """Die Notiz allein lautet nur "…-Start fehlgeschlagen (1)"; die Ausgabe des
    gewächten Prozesses liegt in ``guard_results[*]["log"]`` und blieb bisher
    im Evidenz-Artefakt verborgen (Codex-Fund auf PR #735)."""
    def fake_smoke(artefacts, report, runner, prober, screenshot_dir, **_kwargs):  # type: ignore[no-untyped-def]
        # ``main()`` verwendet den *übergebenen* Report, nicht den Rückgabewert.
        report.fail("AppImage-Start fehlgeschlagen (1): x-ai.AppImage")
        report.guard_results.append({
            "phase": "start", "artefaktklasse": "appimage", "exit_code": 1,
            "peak_instanzen": 1, "status": "crash",
            "log": "stderr:\nSegmentation fault (core dumped)",
        })
        # Ein erfolgreicher Wächter darf das Log NICHT fluten.
        report.guard_results.append({
            "phase": "start", "artefaktklasse": "deb", "exit_code": 0,
            "peak_instanzen": 1, "status": "ok", "log": "stdout:\nalles gut",
        })
        return report

    monkeypatch.setattr(smoke, "run_linux_smoke", fake_smoke)
    (tmp_path / "artefakte").mkdir()
    evidence = {
        "schema": 1, "kind": "abnahme-evidenz", "platform": "linux-arm64",
        "status": "platzhalter", "commit_sha": "abc",
        "quelle": {"art": "release-tag", "wert": "v2.7.1"},
        "artefakte": [{"name": "x-ai.AppImage", "sha256": "cafe", "bytes": 1}],
        "umgebung": {"os": "linux", "arch": "aarch64", "python": "3.12", "runner": "r"},
        "gl_provenance": None, "waechter_ergebnisse": [],
        "erzeugt_am": "2026-07-30T00:00:00+00:00", "hinweise": [],
    }
    (tmp_path / "evidenz.json").write_text(json.dumps(evidence), encoding="utf-8")

    rc = smoke.main(["--platform", "linux-arm64", "--evidence-dir", str(tmp_path)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "Segmentation fault (core dumped)" in out
    assert "phase=start artefaktklasse=appimage" in out
    assert "alles gut" not in out


def test_main_writes_failed_evidence_and_returns_nonzero(tmp_path, monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
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
    # Der Grund muss im Joblog stehen, nicht nur in der Evidenz: Ein roter
    # Abnahme-Lauf zeigte bisher ausschließlich "FEHLGESCHLAGEN", die Diagnose
    # steckte in einem mehrere hundert MB großen Artefakt (beobachtet am
    # macOS-Leg von Lauf 30578506340).
    out = capsys.readouterr().out
    assert "[befund]" in out
    assert "FEHLGESCHLAGEN" in out


def test_guard_starts_artifacts_outside_the_checkout(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Der Wächter bekommt ein neutrales, leeres Arbeitsverzeichnis (#740).

    Sonst beschattet das ``bgremover/`` des Checkouts das gebündelte Paket und
    der Abnahme-Smoke belegt den Checkout statt des Artefakts.
    """
    report = smoke.SmokeReport()
    runner, calls = _recording_runner(_CLEAN_DEB)
    smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, runner,
        prober=lambda: "Broadcom / V3D 7.1 / 3.1", screenshot_dir=tmp_path / "shots",
    )
    guard_calls = [c for c in calls if "smoke_launch.py" in c]
    assert guard_calls, "kein Wächter-Aufruf protokolliert"
    for call in guard_calls:
        assert "--workdir" in call, f"Wächter ohne --workdir: {call}"

    neutral = smoke.neutral_workdir()
    assert neutral.is_dir()
    # Entscheidend: dort darf kein bgremover-Paket liegen, sonst wirkungslos.
    assert not (neutral / "bgremover").exists()
    assert neutral.resolve() != smoke.REPO_ROOT.resolve()


# ── Update-Check-Vorgängernachweis (UPDATE-01, #748) ────────────────────────

_PREDECESSOR_VERSION = "2.7.1"
_CANDIDATE_VERSION = "2.7.2"
# Unterscheidet „nicht übergeben" (Standardrolle bauen) von „bewusst None"
# (Rolle fehlt) in ``_run_update_check``.
_SENTINEL = object()
_PREDECESSOR_OUT = smoke.UPDATE_CHECK_OUTPUT_NAMES[smoke.UPDATE_CHECK_ROLE_PREDECESSOR]
_CANDIDATE_OUT = smoke.UPDATE_CHECK_OUTPUT_NAMES[smoke.UPDATE_CHECK_ROLE_CANDIDATE]


def _evidence_dir(
    root: Path, name: str, *, source: dict[str, str], version: str,
    platform: str = "linux-arm64", artefact_names: list[str] | None = None,
) -> Path:
    """Evidenzverzeichnis wie von ``release_abnahme.py`` geschrieben."""
    directory = root / name
    (directory / "artefakte").mkdir(parents=True, exist_ok=True)
    names = artefact_names if artefact_names is not None else [
        f"BgRemover-{version}-linux-raspberrypi-arm64-ai.AppImage",
        f"BgRemover-{version}-linux-raspberrypi-arm64-ai.deb",
    ]
    (directory / "evidenz.json").write_text(
        json.dumps({
            "schema": 1, "kind": "abnahme-evidenz", "platform": platform,
            "status": "offen", "commit_sha": "deadbeef", "quelle": source,
            "artefakte": [
                {"name": n, "sha256": f"sha256-of-{n}", "bytes": 1, "digest_geprueft": True}
                for n in names
            ],
        }),
        encoding="utf-8",
    )
    return directory


def _predecessor_subject(root: Path, version: str = _PREDECESSOR_VERSION) -> Any:
    return smoke.build_update_check_subject(
        _evidence_dir(
            root, "predecessor", version=version,
            source={"art": "release-tag", "wert": f"v{version}"},
        ),
        smoke.UPDATE_CHECK_ROLE_PREDECESSOR,
    )


def _candidate_subject(root: Path, version: str = _CANDIDATE_VERSION) -> Any:
    return smoke.build_update_check_subject(
        _evidence_dir(
            root, "candidate", version=version, source={"art": "run-id", "wert": "4711"},
        ),
        smoke.UPDATE_CHECK_ROLE_CANDIDATE, expected_version=version,
    )


def _update_check_runner(
    statuses: dict[str, str],
    latest_versions: dict[str, str | None] | None = None,
    *,
    versions: dict[str, str] | None = None,
    find_python_ok: bool = True,
    extraction_ok: bool = True,
):
    """Fake-Runner für den Update-Check-Zweig, auf ``_runner_factory``
    aufgesetzt (deckt weiterhin sauberen deb-Cleanup und die Standard-Fakes
    für den 3D-Screenshot-/Zusatz-Hook ab, damit ein Update-Check-Test nicht an
    unabhängigen Sub-Prüfungen scheitert).

    ``versions`` ist die vom jeweils „laufenden Artefakt" gemeldete
    Ausgangsversion – im Normalfall genau die der Rolle."""
    base = _runner_factory(_CLEAN_DEB)
    latest_versions = latest_versions or {}
    versions = versions or {
        _PREDECESSOR_OUT: _PREDECESSOR_VERSION, _CANDIDATE_OUT: _CANDIDATE_VERSION,
    }

    def runner(cmd: list[str]) -> smoke.CommandResult:
        joined = " ".join(cmd)
        if cmd[:1] == ["/bin/sh"] and "python3.*" in joined:
            if not find_python_ok:
                return smoke.CommandResult(0, stdout="")
            return smoke.CommandResult(0, stdout="/fake/squashfs-root/usr/bin/python3.12\n")
        if cmd[:1] == ["/bin/sh"] and "--appimage-extract" in joined:
            if not extraction_ok:
                return smoke.CommandResult(1, stderr="Entpacken fehlgeschlagen")
            return smoke.CommandResult(0)
        if str(smoke.UPDATE_CHECK_PROBE) in cmd and "--output" in cmd:
            target = Path(cmd[cmd.index("--output") + 1])
            key = target.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps({
                    "schema": 1, "kind": "abnahme-update-check-probe",
                    "current_version": versions.get(key, "unbekannt"),
                    "status": statuses.get(key, "CHECK_FAILED"),
                    "latest_version": latest_versions.get(key),
                    "release_url": None, "error": None,
                    "interpreter": "/fake/squashfs-root/usr/bin/python3.12",
                }),
                encoding="utf-8",
            )
            return smoke.CommandResult(0)
        return base(cmd)

    return runner


def _run_update_check(
    tmp_path: Path, runner, *, predecessor: Any = _SENTINEL, candidate: Any = _SENTINEL,
) -> smoke.SmokeReport:
    """``run_linux_smoke`` mit dem UPDATE-01-Zweig, Standardrollen vorbelegt."""
    report = smoke.SmokeReport()
    return smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, runner,
        prober=lambda: "Broadcom / V3D 7.1 / 3.1", screenshot_dir=tmp_path / "shots",
        predecessor=_predecessor_subject(tmp_path) if predecessor is _SENTINEL else predecessor,
        candidate=_candidate_subject(tmp_path) if candidate is _SENTINEL else candidate,
    )


def _summary(tmp_path: Path) -> dict[str, Any]:
    return json.loads(
        (
            tmp_path / smoke.UPDATE_CHECK_EVIDENCE_DIR_NAME / smoke.UPDATE_CHECK_SUMMARY_NAME
        ).read_text(encoding="utf-8")
    )


# ── Subjektaufbau aus der Bezugs-Evidenz ────────────────────────────────────


def test_update_check_subject_carries_provenance(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Quelle, Hash, Digest-Bestätigung und Plattform stammen aus der
    Bezugs-Evidenz; die erwartete Ausgangsversion des Vorgängers aus seinem
    Release-Tag (ohne führendes ``v``)."""
    subject = _predecessor_subject(tmp_path)
    assert subject.expected_version == _PREDECESSOR_VERSION
    assert subject.source_kind == "release-tag"
    assert subject.source_value == f"v{_PREDECESSOR_VERSION}"
    assert subject.sha256.startswith("sha256-of-")
    assert subject.digest_verified is True
    assert subject.platform == "linux-arm64"
    assert subject.path.endswith(".AppImage")


def test_update_check_subject_rejects_wrong_source_kind(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Ein „Vorgänger" aus dem Kandidaten-Build wäre eine Selbstbestätigung –
    die Quellart muss zur Rolle passen."""
    directory = _evidence_dir(
        tmp_path, "wrong", version=_PREDECESSOR_VERSION,
        source={"art": "run-id", "wert": "4711"},
    )
    with pytest.raises(ValueError, match="Evidenzquelle"):
        smoke.build_update_check_subject(directory, smoke.UPDATE_CHECK_ROLE_PREDECESSOR)


def test_update_check_subject_requires_exactly_one_appimage(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Ein Vorgänger-Artefaktsatz ohne (oder mit mehreren) AppImages darf nicht
    stillschweigend eine Auswahl treffen."""
    directory = _evidence_dir(
        tmp_path, "no-appimage", version=_PREDECESSOR_VERSION,
        source={"art": "release-tag", "wert": f"v{_PREDECESSOR_VERSION}"},
        artefact_names=["BgRemover-2.7.1-linux-raspberrypi-arm64-ai.deb"],
    )
    with pytest.raises(ValueError, match="genau eine AppImage"):
        smoke.build_update_check_subject(directory, smoke.UPDATE_CHECK_ROLE_PREDECESSOR)


# ── Nachweis-Ablauf ─────────────────────────────────────────────────────────


def test_linux_smoke_update_check_passes_with_real_predecessor(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Vorgänger meldet UPDATE_AVAILABLE (mit passender latest_version), der
    aktuelle Kandidat UP_TO_DATE – beide über den echten Interpreter-Pfad."""
    runner = _update_check_runner(
        {_PREDECESSOR_OUT: "UPDATE_AVAILABLE", _CANDIDATE_OUT: "UP_TO_DATE"},
        {_PREDECESSOR_OUT: _CANDIDATE_VERSION},
    )
    result = _run_update_check(tmp_path, runner)
    assert result.passed, result.notes
    assert any("Update-Check ok" in n and "vorgaenger" in n for n in result.notes)
    assert any("Update-Check ok" in n and "kandidat" in n for n in result.notes)


def test_linux_smoke_update_check_skipped_without_predecessor(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Ohne Rollen bleibt UPDATE-01 unangetastet (PENDING), statt eine
    ungeprüfte Annahme als PASS zu fabrizieren."""
    report = smoke.SmokeReport()
    result = smoke.run_linux_smoke(
        _LINUX_ARTEFACTS, report, _runner_factory(_CLEAN_DEB),
        prober=lambda: "Broadcom / V3D 7.1 / 3.1", screenshot_dir=tmp_path / "shots",
    )
    assert result.passed
    assert not any("Update-Check" in n for n in result.notes)


def test_linux_smoke_update_check_requires_both_roles(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Nur eine Seite übergeben ist ein Konfigurationsfehler: die halbe Prüfung
    still durchzuwinken wäre schlimmer als sie auszulassen."""
    result = _run_update_check(tmp_path, _runner_factory(_CLEAN_DEB), candidate=None)
    assert not result.passed
    assert any("nur eine der beiden Rollen" in n for n in result.notes)


def test_linux_smoke_update_check_fails_on_identical_versions(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Vorgänger und Kandidat mit derselben Version prüften ein Release gegen
    sich selbst – das ist kein Nachweis."""
    result = _run_update_check(
        tmp_path,
        _update_check_runner({_PREDECESSOR_OUT: "UPDATE_AVAILABLE", _CANDIDATE_OUT: "UP_TO_DATE"}),
        predecessor=_predecessor_subject(tmp_path, version=_CANDIDATE_VERSION),
    )
    assert not result.passed
    assert any("dieselbe Version" in n for n in result.notes)


def test_linux_smoke_update_check_fails_when_predecessor_reports_up_to_date(  # type: ignore[no-untyped-def]
    tmp_path: Path,
) -> None:
    """Ein Vorgänger, der fälschlich UP_TO_DATE meldet (z. B. weil das Release
    noch nicht öffentlich war), muss den Smoke scheitern lassen statt es
    stillschweigend als Erfolg zu werten."""
    result = _run_update_check(
        tmp_path,
        _update_check_runner({_PREDECESSOR_OUT: "UP_TO_DATE", _CANDIDATE_OUT: "UP_TO_DATE"}),
    )
    assert not result.passed
    assert any("erwartet UPDATE_AVAILABLE" in n for n in result.notes)
    assert _summary(tmp_path)["pruefungen"][0]["befund"] == smoke.UPDATE_CHECK_VERDICT_STATUS


def test_linux_smoke_update_check_fails_on_latest_version_mismatch(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """UPDATE_AVAILABLE allein genügt nicht: ``latest_version`` muss auf den
    tatsächlich geprüften Kandidaten zeigen, sonst bliebe ein veraltetes oder
    falsches Release unbemerkt."""
    result = _run_update_check(
        tmp_path,
        _update_check_runner(
            {_PREDECESSOR_OUT: "UPDATE_AVAILABLE", _CANDIDATE_OUT: "UP_TO_DATE"},
            {_PREDECESSOR_OUT: "2.7.0"},
        ),
    )
    assert not result.passed
    assert any("weicht vom erwarteten Kandidaten" in n for n in result.notes)
    assert (
        _summary(tmp_path)["pruefungen"][0]["befund"]
        == smoke.UPDATE_CHECK_VERDICT_TARGET_VERSION
    )


def test_linux_smoke_update_check_fails_when_predecessor_reports_foreign_version(  # type: ignore[no-untyped-def]
    tmp_path: Path,
) -> None:
    """Die Ausgangsversion kommt aus dem laufenden Artefakt – meldet es eine
    andere als die des bezogenen Releases, lief nicht das geprüfte Bundle
    (etwa weil ein Checkout das gebündelte Paket beschattet hat, #740)."""
    result = _run_update_check(
        tmp_path,
        _update_check_runner(
            {_PREDECESSOR_OUT: "UPDATE_AVAILABLE", _CANDIDATE_OUT: "UP_TO_DATE"},
            {_PREDECESSOR_OUT: _CANDIDATE_VERSION},
            versions={_PREDECESSOR_OUT: "2.6.0", _CANDIDATE_OUT: _CANDIDATE_VERSION},
        ),
    )
    assert not result.passed
    assert any("das laufende Artefakt meldet Version" in n for n in result.notes)
    assert (
        _summary(tmp_path)["pruefungen"][0]["befund"]
        == smoke.UPDATE_CHECK_VERDICT_SOURCE_VERSION
    )


def test_linux_smoke_update_check_fails_when_candidate_reports_other_version(  # type: ignore[no-untyped-def]
    tmp_path: Path,
) -> None:
    """Auch der Kandidat muss sich als die Version ausweisen, die veröffentlicht
    wurde: eine abweichende Paketversion ergäbe sonst still UP_TO_DATE."""
    result = _run_update_check(
        tmp_path,
        _update_check_runner(
            {_PREDECESSOR_OUT: "UPDATE_AVAILABLE", _CANDIDATE_OUT: "UP_TO_DATE"},
            {_PREDECESSOR_OUT: _CANDIDATE_VERSION},
            versions={_PREDECESSOR_OUT: _PREDECESSOR_VERSION, _CANDIDATE_OUT: "2.7.3"},
        ),
    )
    assert not result.passed
    assert any("das laufende Artefakt meldet Version" in n for n in result.notes)


def test_linux_smoke_update_check_fails_on_check_failed(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """``CHECK_FAILED`` ist in keiner Rolle ein Erfolg – ein Netzwerkfehler
    darf nicht als bestandener Nachweis durchgehen und bekommt einen eigenen
    Befund in der Evidenz."""
    result = _run_update_check(
        tmp_path,
        _update_check_runner({_PREDECESSOR_OUT: "CHECK_FAILED", _CANDIDATE_OUT: "UP_TO_DATE"}),
    )
    assert not result.passed
    assert any("Netzwerk-Roundtrip fehlgeschlagen" in n for n in result.notes)
    assert (
        _summary(tmp_path)["pruefungen"][0]["befund"] == smoke.UPDATE_CHECK_VERDICT_CHECK_FAILED
    )


def test_linux_smoke_update_check_fails_without_bundled_interpreter(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Kein gefundener Interpreter (z. B. unerwartetes AppImage-Layout) muss
    scheitern statt eine leere Prüfung als bestanden zu werten – und die
    Herkunft trotzdem dokumentieren."""
    result = _run_update_check(
        tmp_path,
        _update_check_runner(
            {_PREDECESSOR_OUT: "UPDATE_AVAILABLE", _CANDIDATE_OUT: "UP_TO_DATE"},
            find_python_ok=False,
        ),
    )
    assert not result.passed
    assert any("kein gebündelter Interpreter gefunden" in n for n in result.notes)
    record = _summary(tmp_path)["pruefungen"][0]
    assert record["befund"] == smoke.UPDATE_CHECK_VERDICT_NO_EVIDENCE
    assert record["sha256"].startswith("sha256-of-")


# ── Evidenzvertrag (#748: Quelle, Hash, Plattform, Versionen, Status) ───────


def test_update_check_summary_documents_source_hash_platform_and_versions(  # type: ignore[no-untyped-def]
    tmp_path: Path,
) -> None:
    """Der Nachweis muss ohne Rückgriff auf andere Dateien belegen, WAS geprüft
    wurde (Artefakt, Quelle, Hash, Plattform) und WAS herauskam (Ausgangs-/
    Zielversion, Antwortstatus)."""
    runner = _update_check_runner(
        {_PREDECESSOR_OUT: "UPDATE_AVAILABLE", _CANDIDATE_OUT: "UP_TO_DATE"},
        {_PREDECESSOR_OUT: _CANDIDATE_VERSION},
    )
    assert _run_update_check(tmp_path, runner).passed

    summary = _summary(tmp_path)
    assert summary["schema"] == smoke.UPDATE_CHECK_SUMMARY_SCHEMA
    assert summary["kind"] == smoke.UPDATE_CHECK_SUMMARY_KIND
    assert summary["ok"] is True
    assert summary["kandidaten_version"] == _CANDIDATE_VERSION

    predecessor, candidate = summary["pruefungen"]
    assert [predecessor["rolle"], candidate["rolle"]] == [
        smoke.UPDATE_CHECK_ROLE_PREDECESSOR, smoke.UPDATE_CHECK_ROLE_CANDIDATE,
    ]
    assert predecessor["artefakt"].endswith(".AppImage")
    assert predecessor["quelle"] == {"art": "release-tag", "wert": f"v{_PREDECESSOR_VERSION}"}
    assert predecessor["sha256"].startswith("sha256-of-")
    assert predecessor["digest_geprueft"] is True
    assert predecessor["plattform"] == "linux-arm64"
    assert predecessor["gemeldete_ausgangsversion"] == _PREDECESSOR_VERSION
    assert predecessor["erwartete_ausgangsversion"] == _PREDECESSOR_VERSION
    assert predecessor["status"] == "UPDATE_AVAILABLE"
    assert predecessor["zielversion"] == _CANDIDATE_VERSION
    assert predecessor["befund"] == smoke.UPDATE_CHECK_VERDICT_OK
    assert candidate["quelle"]["art"] == "run-id"
    assert candidate["status"] == "UP_TO_DATE"


def test_update_check_summary_carries_no_secrets(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """„ohne sensible Daten": die Evidenz enthält nur öffentlich Bekanntes –
    kein Token, keine Authorization-Header."""
    runner = _update_check_runner(
        {_PREDECESSOR_OUT: "UPDATE_AVAILABLE", _CANDIDATE_OUT: "UP_TO_DATE"},
        {_PREDECESSOR_OUT: _CANDIDATE_VERSION},
    )
    _run_update_check(tmp_path, runner)
    raw = (
        tmp_path / smoke.UPDATE_CHECK_EVIDENCE_DIR_NAME / smoke.UPDATE_CHECK_SUMMARY_NAME
    ).read_text(encoding="utf-8").lower()
    for forbidden in ("token", "authorization", "secret", "password", "bearer"):
        assert forbidden not in raw


# ── CLI-Verdrahtung ─────────────────────────────────────────────────────────


def test_cli_requires_candidate_version_with_predecessor(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    """Ohne Sollversion bliebe vom Nachweis nur „irgendein Update sichtbar";
    #748 verlangt UPDATE_AVAILABLE mit exakt der neuen Zielversion."""
    candidate_dir = _evidence_dir(
        tmp_path, "candidate", version=_CANDIDATE_VERSION,
        source={"art": "run-id", "wert": "4711"},
    )
    predecessor_dir = _evidence_dir(
        tmp_path, "predecessor", version=_PREDECESSOR_VERSION,
        source={"art": "release-tag", "wert": f"v{_PREDECESSOR_VERSION}"},
    )
    with pytest.raises(SystemExit):
        smoke.main([
            "--platform", "linux-arm64", "--evidence-dir", str(candidate_dir),
            "--predecessor-evidence-dir", str(predecessor_dir),
        ])
    assert "--candidate-version" in capsys.readouterr().err


def test_cli_rejects_unusable_predecessor_evidence(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    """Ein unbrauchbares Vorgänger-Evidenzverzeichnis bricht den Lauf ab, statt
    den Nachweis still auszulassen (das sähe wie „nicht angefordert" aus)."""
    candidate_dir = _evidence_dir(
        tmp_path, "candidate", version=_CANDIDATE_VERSION,
        source={"art": "run-id", "wert": "4711"},
    )
    with pytest.raises(SystemExit):
        smoke.main([
            "--platform", "linux-arm64", "--evidence-dir", str(candidate_dir),
            "--predecessor-evidence-dir", str(tmp_path / "fehlt"),
            "--candidate-version", _CANDIDATE_VERSION,
        ])
    assert "nicht aufsetzbar" in capsys.readouterr().err
