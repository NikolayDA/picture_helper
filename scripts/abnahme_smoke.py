#!/usr/bin/env python3
"""Release-Abnahme-Smoke auf echter Hardware (#642 Linux, #643 macOS).

Baut auf ``release_abnahme.py`` auf: bezieht die Artefakte, startet sie auf dem
Self-hosted Runner (Start-/Fork-Bomb-/Hänger-Invarianten über den bestehenden
``smoke_launch.py``-Wächter), erfasst die GL-Provenance (echte Runner-Hardware)
und einen Screenshot und schreibt die zum Ergebnis fortgeschriebene Evidenz.

Alle Pass/Fail-Entscheidungen liegen in den getesteten Funktionen von
``release_abnahme`` (``evaluate_gl_provenance``/``evaluate_retina``/
``evaluate_deb_cleanup``/``finalize_evidence``). Die OS-Kommandos laufen über
einen injizierbaren ``Runner``, damit der Orchestrierungs-Fluss ohne echte
Hardware getestet werden kann. Betrieb/Kriterien: ``docs/RELEASE_AUTOMATION.md``,
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


def _guard(runner: Runner, launch_cmd: list[str], max_instances: int, timeout: int) -> CommandResult:
    """Artefakt über den Fork-Bomb-/Hänger-Wächter starten (smoke_launch.py)."""
    return runner(
        [
            sys.executable, str(SMOKE_LAUNCH),
            "--max-instances", str(max_instances),
            "--timeout", str(timeout),
            "--", *launch_cmd,
        ]
    )


def run_linux_smoke(
    artefacts: list[str], report: SmokeReport, runner: Runner, prober: Prober,
) -> SmokeReport:
    """AppImage- und ``.deb``-Smoke auf einem Linux-Runner (#642)."""
    verdict = ra.evaluate_gl_provenance(prober())
    report.gl_diagnostic = verdict.diagnostic or None
    report.ok(verdict.note) if verdict.ok else report.fail(verdict.note)

    for artefact in artefacts:
        if artefact.endswith(".AppImage"):
            _linux_appimage(artefact, report, runner)
        elif artefact.endswith(".deb"):
            _linux_deb(artefact, report, runner)
    return report


def _linux_appimage(path: str, report: SmokeReport, runner: Runner) -> None:
    runner(["chmod", "+x", path])
    result = _guard(runner, [path], max_instances=5, timeout=120)
    if result.returncode == 0:
        report.ok(f"AppImage-Start ok: {Path(path).name}")
    else:
        report.fail(f"AppImage-Start fehlgeschlagen ({result.returncode}): {Path(path).name}")


def _linux_deb(path: str, report: SmokeReport, runner: Runner) -> None:
    name = Path(path).name
    if runner(["sudo", "apt-get", "install", "-y", path]).returncode != 0:
        report.fail(f"deb-Installation fehlgeschlagen: {name}")
        return
    started = _guard(runner, ["bgremover"], max_instances=5, timeout=120)
    report.ok(f"deb-Start ok: {name}") if started.returncode == 0 else report.fail(
        f"deb-Start fehlgeschlagen ({started.returncode}): {name}"
    )
    # Rückstandsfreie Deinstallation prüfen.
    runner(["sudo", "apt-get", "purge", "-y", "bgremover"])
    installed = runner(["dpkg", "-s", "bgremover"]).returncode == 0
    leftover = [
        line for line in runner(["dpkg", "-L", "bgremover"]).stdout.splitlines() if line.strip()
    ]
    if ra.evaluate_deb_cleanup(installed, leftover):
        report.ok(f"deb rückstandsfrei entfernt: {name}")
    else:
        report.fail(f"deb-Rückstände nach purge: {name}")


def run_macos_smoke(
    artefacts: list[str], report: SmokeReport, runner: Runner, prober: Prober, scale_factor: float,
) -> SmokeReport:
    """DMG-Smoke inkl. Retina-Nachweis auf einem macOS-Runner (#643)."""
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
        if not artefact.endswith(".dmg"):
            continue
        result = _guard(runner, ["open-dmg", artefact], max_instances=5, timeout=120)
        report.ok(f"DMG-Start ok: {Path(artefact).name}") if result.returncode == 0 else (
            report.fail(f"DMG-Start fehlgeschlagen ({result.returncode}): {Path(artefact).name}")
        )
    return report


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
