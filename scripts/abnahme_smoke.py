#!/usr/bin/env python3
"""Release-Abnahme-Smoke auf echter Hardware (#642 Linux, #643 macOS).

Baut auf ``release_abnahme.py`` auf: bezieht die Artefakte, startet sie auf dem
Self-hosted Runner (Start-/Fork-Bomb-/Hänger-Invarianten über den bestehenden
``smoke_launch.py``-Wächter – dieselben Muster wie ``release-linux.yml``),
erfasst die GL-Provenance (echte Runner-Hardware) und schreibt die zum Ergebnis
fortgeschriebene Evidenz.

**Was dieser Smoke belegt:** sauberer Start ohne Crash/Fork-Bomb/Hänger,
GL-Provenance der Runner-Hardware, rückstandsfreie ``.deb``-Installation und
(macOS) Retina/High-DPI. **Was er (noch) nicht belegt:** das *native*
3D-Rendering des gepackten Artefakts – der Wächter startet headless
(``offscreen``), die Provenance stammt aus dem Source-Checkout. Der native
Start mit Screenshot ist als Folge-Issue #648 ausgelagert; die Evidenz
deklariert diese Grenze bis dahin offen (``NATIVE_3D_CAVEAT``).

Alle Pass/Fail-Entscheidungen liegen in den getesteten Funktionen von
``release_abnahme``. Die OS-Kommandos laufen über einen injizierbaren
``Runner``, damit der Orchestrierungs-Fluss ohne echte Hardware getestet werden
kann. Betrieb/Kriterien: ``docs/RELEASE_AUTOMATION.md``,
``docs/PACKAGING_SMOKE.md``.
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SMOKE_LAUNCH = REPO_ROOT / "scripts" / "smoke_launch.py"
PROBE = REPO_ROOT / "scripts" / "abnahme_probe.py"

# Von packaging/linux/build_deb.sh installierte Pfade (Ground Truth aus
# release-linux.yml „Real .deb install/start/remove smoke").
DEB_INSTALLED_APPIMAGE = "/opt/BgRemover/BgRemover.AppImage"
DEB_KNOWN_PATHS = (
    DEB_INSTALLED_APPIMAGE,
    "/usr/share/applications/de.bgremover.app.desktop",
    "/usr/share/icons/hicolor/512x512/apps/de.bgremover.app.png",
)

# Wegwerf-Kopie des App-Bundles fuer den DMG-Smoke (#643): das Original bleibt
# auf dem read-only DMG-Mount, der direkt danach detacht wird.
TEMP_DMG_ROOT = "/tmp/abnahme-macos-dmg"

# Offener Nachweis: Grenze dieses Smokes bis #648 (nativer Start + Screenshot).
NATIVE_3D_CAVEAT = (
    "Nativer 3D-Render-Nachweis des gepackten Artefakts steht aus (#648): "
    "Start-Wächter läuft headless, GL-Provenance stammt vom Runner."
)


def _load_release_abnahme():  # type: ignore[no-untyped-def]
    """``release_abnahme`` als Modul laden (scripts/ ist kein Paket)."""
    spec = importlib.util.spec_from_file_location(
        "release_abnahme", REPO_ROOT / "scripts" / "release_abnahme.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("release_abnahme", module)
    spec.loader.exec_module(module)
    return module


ra = _load_release_abnahme()

# Injektionspunkte für Tests.
Runner = Callable[[list[str]], "CommandResult"]
Prober = Callable[[], str]


@dataclass(frozen=True)
class CommandResult:
    """Ergebnis eines OS-Kommandos."""

    returncode: int
    stdout: str = ""
    stderr: str = ""


@dataclass
class SmokeReport:
    """Gesammelte Smoke-Signale einer Plattform."""

    passed: bool = True
    gl_diagnostic: str | None = None
    notes: list[str] = field(default_factory=list)

    def fail(self, note: str) -> None:
        self.passed = False
        self.notes.append(note)

    def ok(self, note: str) -> None:
        self.notes.append(note)


def _default_runner(cmd: list[str]) -> CommandResult:
    completed = subprocess.run(  # noqa: S603
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _default_prober() -> str:
    result = _default_runner([sys.executable, str(PROBE)])
    return result.stdout.strip()


def _fork_limit(name: str) -> int:
    """Fork-Bomb-Limit: 5 nur für KI-Artefakte (GUI + Warmup-Kind + Tracker),
    sonst strikt 1 – exakt wie ``release-linux.yml``."""
    return 5 if "-ai" in name else 1


def _guard(
    runner: Runner, launch_cmd: list[str], *, match: str, max_instances: int, timeout: int = 120,
) -> CommandResult:
    """Artefakt über den Fork-Bomb-/Hänger-Wächter starten (smoke_launch.py).

    ``--match`` ist Pflicht (sonst bricht argparse mit Exit 2 ab).
    """
    return runner(
        [
            sys.executable, str(SMOKE_LAUNCH),
            "--match", match,
            "--max-instances", str(max_instances),
            "--timeout", str(timeout),
            "--", *launch_cmd,
        ]
    )


def _run_ai_selfcheck_if_needed(
    runner: Runner,
    launch_cmd: list[str],
    *,
    match: str,
    max_instances: int,
    name: str,
    report: SmokeReport,
) -> None:
    """KI-Selbsttest (rembg-Kette im Spawn-Kindprozess importierbar) vor dem
    eigentlichen Start – analog ``release-linux.yml`` (#308). Läuft nur für
    ``-ai``-Artefakte (``max_instances`` > 1 über ``_fork_limit``); ``env``
    setzt ``BGREMOVER_AI_SELFCHECK=1`` nur für diesen einen Start, ohne den
    Fork-Bomb-Wächter selbst zu verändern (#642/#643-Fund: fehlte bisher im
    Abnahme-Smoke, obwohl release-linux.yml ihn beim Build bereits fährt)."""
    if max_instances <= 1:
        return
    selfcheck = _guard(
        runner, ["env", "BGREMOVER_AI_SELFCHECK=1", *launch_cmd],
        match=match, max_instances=max_instances,
    )
    if selfcheck.returncode == 0:
        report.ok(f"KI-Selbsttest ok: {name}")
    else:
        report.fail(f"KI-Selbsttest fehlgeschlagen ({selfcheck.returncode}): {name}")


def _require_extensions(artefacts: list[str], required: set[str], report: SmokeReport) -> bool:
    """Prüft, dass genau die erwarteten Artefaktklassen vorliegen (kein Teilsatz)."""
    present = {Path(a).suffix for a in artefacts}
    missing = required - present
    unexpected = [a for a in artefacts if Path(a).suffix not in required]
    ok = True
    if missing:
        report.fail(f"Erwartete Artefaktklassen fehlen: {sorted(missing)}")
        ok = False
    if unexpected:
        report.fail(f"Unerwartete Artefakte: {[Path(a).name for a in unexpected]}")
        ok = False
    return ok


def run_linux_smoke(
    artefacts: list[str], report: SmokeReport, runner: Runner, prober: Prober,
) -> SmokeReport:
    """AppImage- und ``.deb``-Smoke auf einem Linux-Runner (#642)."""
    _require_extensions(artefacts, {".AppImage", ".deb"}, report)

    verdict = ra.evaluate_gl_provenance(prober())
    report.gl_diagnostic = verdict.diagnostic or None
    report.ok(verdict.note) if verdict.ok else report.fail(verdict.note)

    for artefact in artefacts:
        if artefact.endswith(".AppImage"):
            _linux_appimage(artefact, report, runner)
        elif artefact.endswith(".deb"):
            _linux_deb(artefact, report, runner)

    report.ok(NATIVE_3D_CAVEAT)
    return report


def _linux_appimage(path: str, report: SmokeReport, runner: Runner) -> None:
    name = Path(path).name
    runner(["chmod", "+x", path])
    max_instances = _fork_limit(name)
    launch_cmd = [path, "--appimage-extract-and-run"]
    _run_ai_selfcheck_if_needed(
        runner, launch_cmd, match=name, max_instances=max_instances, name=name, report=report,
    )
    # --appimage-extract-and-run: kein Host-FUSE nötig (wie release-linux.yml).
    result = _guard(runner, launch_cmd, match=name, max_instances=max_instances)
    if result.returncode == 0:
        report.ok(f"AppImage-Start ok: {name}")
    else:
        report.fail(f"AppImage-Start fehlgeschlagen ({result.returncode}): {name}")


def _linux_deb(path: str, report: SmokeReport, runner: Runner) -> None:
    name = Path(path).name
    installed_ok = runner(["sudo", "apt-get", "install", "-y", path]).returncode == 0
    if not installed_ok:
        report.fail(f"deb-Installation fehlgeschlagen: {name}")
    try:
        if installed_ok:
            # Das installierte AppImage starten (kein `bgremover`-Kommando im PATH).
            max_instances = _fork_limit(name)
            launch_cmd = [DEB_INSTALLED_APPIMAGE, "--appimage-extract-and-run"]
            _run_ai_selfcheck_if_needed(
                runner, launch_cmd, match="BgRemover.AppImage", max_instances=max_instances,
                name=name, report=report,
            )
            started = _guard(
                runner, launch_cmd, match="BgRemover.AppImage", max_instances=max_instances,
            )
            report.ok(f"deb-Start ok: {name}") if started.returncode == 0 else report.fail(
                f"deb-Start fehlgeschlagen ({started.returncode}): {name}"
            )
    finally:
        # Cleanup laeuft IMMER, auch nach fehlgeschlagener Installation
        # (#651-Review-Fund): ``apt-get install`` kann vor dem eigentlichen
        # Fehlschlag schon Dateien/Paketeintraege hinterlassen haben – ohne
        # diesen Cleanup bliebe der dedizierte Runner dann verschmutzt.
        # Bekannte Pfade real pruefen (dpkg -L ist nach purge wertlos, da der
        # Paketeintrag weg ist – Codex-Fund).
        runner(["sudo", "dpkg", "-r", "bgremover"])
        installed = runner(["dpkg", "-s", "bgremover"]).returncode == 0
        leftover = [p for p in DEB_KNOWN_PATHS if runner(["test", "-e", p]).returncode == 0]
        if ra.evaluate_deb_cleanup(installed, leftover):
            report.ok(f"deb rückstandsfrei entfernt: {name}")
        else:
            report.fail(
                f"deb-Rückstände nach Remove: {name} ({leftover or 'Paket noch registriert'})"
            )


def parse_mount_point(hdiutil_stdout: str) -> str | None:
    """Mount-Pfad aus der ``hdiutil attach``-Ausgabe (erste ``/Volumes/…``-Zeile)."""
    for line in hdiutil_stdout.splitlines():
        idx = line.find("/Volumes/")
        if idx != -1:
            return line[idx:].strip()
    return None


def parse_disk_identifier(hdiutil_stdout: str) -> str | None:
    """Geraete-Kennung (``/dev/diskN…``) aus der ``hdiutil attach``-Ausgabe.

    Fallback fuer ``hdiutil detach``, falls der Mount-Pfad nicht geparst werden
    konnte: ``attach`` war dann trotzdem erfolgreich (ein Volume ist gemountet),
    der Cleanup-Trap muss es auch ohne bekannten Mount-Pfad wieder loesen
    (#643-Fund, sonst bleibt ein Volume haengen).
    """
    for line in hdiutil_stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("/dev/"):
            return stripped.split()[0]
    return None


def run_macos_smoke(
    artefacts: list[str], report: SmokeReport, runner: Runner, prober: Prober, scale_factor: float,
) -> SmokeReport:
    """DMG-Smoke inkl. Retina-Nachweis auf einem macOS-Runner (#643)."""
    _require_extensions(artefacts, {".dmg"}, report)

    verdict = ra.evaluate_gl_provenance(prober())
    report.gl_diagnostic = verdict.diagnostic or None
    report.ok(verdict.note) if verdict.ok else report.fail(verdict.note)

    if ra.evaluate_retina(scale_factor):
        report.ok(f"Retina/High-DPI ok: devicePixelRatio={scale_factor}")
    else:
        report.fail(
            f"Retina/High-DPI nicht erfüllt: devicePixelRatio={scale_factor} "
            f"(< {ra.RETINA_MIN_SCALE})"
        )

    for artefact in artefacts:
        if artefact.endswith(".dmg"):
            _macos_dmg(artefact, report, runner)

    report.ok(NATIVE_3D_CAVEAT)
    return report


def _macos_dmg(path: str, report: SmokeReport, runner: Runner) -> None:
    name = Path(path).name
    attach = runner(["hdiutil", "attach", "-nobrowse", "-readonly", path])
    if attach.returncode != 0:
        report.fail(f"DMG-Mount fehlgeschlagen: {name}")
        return
    mount = parse_mount_point(attach.stdout)
    disk_id = parse_disk_identifier(attach.stdout)
    # Cleanup-Trap: ``attach`` war erfolgreich, also ist ein Volume gemountet –
    # detach in jedem Fall versuchen, auch wenn der Mount-Pfad nicht geparst
    # werden konnte (sonst bleibt es haengen, #643-Fund). Detach laeuft HIER
    # bewusst nur um die Kopie herum (#651-Review-Fund): der eigentliche
    # App-Start (bis zu 240s Guard-Timeout) darf das DMG nicht mehr gemountet
    # halten, sonst bleibt bei einem abgebrochenen/gekillten Job ein Volume
    # unnoetig lange haengen – die Temp-Kopie existiert ja genau dafuer.
    try:
        temp_app = _macos_dmg_copy(name, mount, report, runner)
    finally:
        detach_target = mount or disk_id
        if detach_target:
            runner(["hdiutil", "detach", detach_target])
    if temp_app is None:
        return
    try:
        _start_macos_app(temp_app, name, report, runner)
    finally:
        runner(["rm", "-rf", temp_app])


def _macos_dmg_copy(
    dmg_name: str, mount: str | None, report: SmokeReport, runner: Runner,
) -> str | None:
    """Findet das App-Bundle auf dem Mount und kopiert es in eine Temp-Kopie.

    Laeuft ausschliesslich waehrend das DMG noch gemountet ist; der Aufrufer
    detacht direkt danach, bevor der (potenziell lange) App-Start beginnt.
    """
    if not mount:
        report.fail(f"DMG-Mount-Pfad nicht erkannt: {dmg_name}")
        return None
    listing = runner(["/bin/sh", "-c", f"ls -d {mount}/*.app"])
    app = listing.stdout.strip().splitlines()[0] if listing.stdout.strip() else ""
    if not app:
        report.fail(f"Keine .app im DMG gefunden: {dmg_name}")
        return None
    return _copy_app_to_temp(app, report, runner)


def _copy_app_to_temp(app: str, report: SmokeReport, runner: Runner) -> str | None:
    """Kopiert das App-Bundle vom read-only DMG-Mount in eine Temp-Wegwerfkopie.

    Noetig aus zwei Gruenden: (1) Quarantaene laesst sich auf einem read-only
    Mount nicht entfernen, (2) der DMG-Mount kann sofort danach detacht werden,
    statt waehrend des ganzen App-Laufs belegt zu bleiben (#643-Fund).
    """
    temp_app = f"{TEMP_DMG_ROOT}/{Path(app).name}"
    if runner(["rm", "-rf", temp_app]).returncode != 0:
        report.fail(f"Temp-Verzeichnis konnte nicht bereinigt werden: {temp_app}")
        return None
    if runner(["mkdir", "-p", TEMP_DMG_ROOT]).returncode != 0:
        report.fail(f"Temp-Verzeichnis konnte nicht angelegt werden: {TEMP_DMG_ROOT}")
        return None
    if runner(["cp", "-R", app, temp_app]).returncode != 0:
        report.fail(f"App-Bundle konnte nicht in Temp kopiert werden: {app}")
        return None
    # Quarantaene NUR auf der Temp-Kopie entfernen: das lokal gebaute,
    # unsignierte Artefakt wuerde Gatekeeper sonst beim Start blockieren. Die
    # Kopie existiert ausschliesslich fuer diesen Smoke und wird danach wieder
    # geloescht – kein dauerhafter Gatekeeper-Bypass des Originals.
    runner(["xattr", "-r", "-d", "com.apple.quarantine", temp_app])
    return temp_app


def _start_macos_app(app: str, dmg_name: str, report: SmokeReport, runner: Runner) -> None:
    binary = f"{app}/Contents/MacOS/{Path(app).stem}"
    match = Path(app).name
    max_instances = _fork_limit(dmg_name)
    _run_ai_selfcheck_if_needed(
        runner, [binary], match=match, max_instances=max_instances, name=dmg_name, report=report,
    )
    start = time.monotonic()
    started = _guard(runner, [binary], match=match, max_instances=max_instances)
    elapsed = time.monotonic() - start
    if started.returncode == 0:
        report.ok(f"DMG-Start ok: {dmg_name} (Startzeit {elapsed:.1f}s)")
    else:
        report.fail(f"DMG-Start fehlgeschlagen ({started.returncode}): {dmg_name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=sorted(ra.PLATFORM_PATTERNS))
    parser.add_argument("--evidence-dir", type=Path, required=True,
                        help="Verzeichnis mit evidenz.json (aus release_abnahme.py).")
    parser.add_argument("--scale-factor", type=float, default=0.0,
                        help="devicePixelRatio des macOS-Hauptfensters (nur macOS).")
    args = parser.parse_args(argv)

    import json

    evidence_path = args.evidence_dir / "evidenz.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    artefacts = [
        str(args.evidence_dir / "artefakte" / a["name"]) for a in evidence["artefakte"]
    ]

    report = SmokeReport()
    if args.platform.startswith("linux"):
        run_linux_smoke(artefacts, report, _default_runner, _default_prober)
    else:
        run_macos_smoke(
            artefacts, report, _default_runner, _default_prober, args.scale_factor,
        )

    finalized = ra.finalize_evidence(
        evidence, passed=report.passed, gl_provenance=report.gl_diagnostic,
        extra_notes=report.notes,
    )
    ra.write_evidence(args.evidence_dir, finalized)
    print(f"Smoke {'bestanden' if report.passed else 'FEHLGESCHLAGEN'}: {args.platform}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
