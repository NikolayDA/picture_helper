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
Start mit Screenshot folgt mit #646; die Evidenz deklariert diese Grenze offen.

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

# Offener Nachweis: Grenze dieses Smokes bis #646 (nativer Start + Screenshot).
NATIVE_3D_CAVEAT = (
    "Nativer 3D-Render-Nachweis des gepackten Artefakts steht aus (#646): "
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
    # --appimage-extract-and-run: kein Host-FUSE nötig (wie release-linux.yml).
    result = _guard(
        runner, [path, "--appimage-extract-and-run"],
        match=name, max_instances=_fork_limit(name),
    )
    if result.returncode == 0:
        report.ok(f"AppImage-Start ok: {name}")
    else:
        report.fail(f"AppImage-Start fehlgeschlagen ({result.returncode}): {name}")


def _linux_deb(path: str, report: SmokeReport, runner: Runner) -> None:
    name = Path(path).name
    if runner(["sudo", "apt-get", "install", "-y", path]).returncode != 0:
        report.fail(f"deb-Installation fehlgeschlagen: {name}")
        return
    # Das installierte AppImage starten (kein `bgremover`-Kommando im PATH).
    started = _guard(
        runner, [DEB_INSTALLED_APPIMAGE, "--appimage-extract-and-run"],
        match="BgRemover.AppImage", max_instances=_fork_limit(name),
    )
    report.ok(f"deb-Start ok: {name}") if started.returncode == 0 else report.fail(
        f"deb-Start fehlgeschlagen ({started.returncode}): {name}"
    )
    # Rückstandsfreie Deinstallation: bekannte Pfade real prüfen (dpkg -L ist
    # nach purge wertlos, da der Paketeintrag weg ist – Codex-Fund).
    runner(["sudo", "dpkg", "-r", "bgremover"])
    installed = runner(["dpkg", "-s", "bgremover"]).returncode == 0
    leftover = [p for p in DEB_KNOWN_PATHS if runner(["test", "-e", p]).returncode == 0]
    if ra.evaluate_deb_cleanup(installed, leftover):
        report.ok(f"deb rückstandsfrei entfernt: {name}")
    else:
        report.fail(f"deb-Rückstände nach Remove: {name} ({leftover or 'Paket noch registriert'})")


def parse_mount_point(hdiutil_stdout: str) -> str | None:
    """Mount-Pfad aus der ``hdiutil attach``-Ausgabe (erste ``/Volumes/…``-Zeile)."""
    for line in hdiutil_stdout.splitlines():
        idx = line.find("/Volumes/")
        if idx != -1:
            return line[idx:].strip()
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
    mount = parse_mount_point(attach.stdout)
    if attach.returncode != 0 or not mount:
        report.fail(f"DMG-Mount fehlgeschlagen: {name}")
        return
    try:
        listing = runner(["/bin/sh", "-c", f"ls -d {mount}/*.app"])
        app = listing.stdout.strip().splitlines()[0] if listing.stdout.strip() else ""
        if not app:
            report.fail(f"Keine .app im DMG gefunden: {name}")
            return
        binary = f"{app}/Contents/MacOS/{Path(app).stem}"
        started = _guard(runner, [binary], match=Path(app).name, max_instances=5)
        report.ok(f"DMG-Start ok: {name}") if started.returncode == 0 else report.fail(
            f"DMG-Start fehlgeschlagen ({started.returncode}): {name}"
        )
    finally:
        runner(["hdiutil", "detach", mount])


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
