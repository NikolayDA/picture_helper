#!/usr/bin/env python3
"""Release-Abnahme-Smoke auf echter Hardware (#642 Linux, #643 macOS, #648 nativer 3D-Screenshot).

Baut auf ``release_abnahme.py`` auf: bezieht die Artefakte, startet sie auf dem
Self-hosted Runner (Start-/Fork-Bomb-/Hänger-Invarianten über den bestehenden
``smoke_launch.py``-Wächter – dieselben Muster wie ``release-linux.yml``),
erfasst die GL-Provenance (echte Runner-Hardware) und schreibt die zum Ergebnis
fortgeschriebene Evidenz.

**Was dieser Smoke belegt:** sauberer Start ohne Crash/Fork-Bomb/Hänger,
GL-Provenance der Runner-Hardware, rückstandsfreie ``.deb``-Installation,
(macOS) Retina/High-DPI **und** das native 3D-Rendering des gepackten
Artefakts selbst (#648): das Hauptartefakt (AppImage bzw. das aus dem DMG
kopierte ``.app``-Bundle) startet ein zweites Mal – diesmal über
``smoke_launch.py --native`` (kein erzwungenes ``offscreen``) mit dem
Automationshook ``BGREMOVER_SCREENSHOT_3D`` – und liefert Screenshot samt
Provenance-Sidecar direkt aus dem laufenden gepackten Prozess (nicht aus dem
Source-Checkout wie der native E2E-Nachweis in #644). Ein Software-Renderer
lässt diesen Nachweis scheitern (geteiltes Gate aus
``bgremover.renderer_provenance``, dieselbe Regel wie die Runner-Hardware-
Provenance oben). Ein drittes Mal startet dasselbe Artefakt mit dem
Automationshook ``BGREMOVER_ACCEPTANCE_EXTRA`` (#685-Review, Codex-Fund auf
PR #720): EufyMake-Export- und 2.7.0-Projekt-Öffnen-Nachweis direkt aus dem
gepackten Prozess statt aus dem Source-Checkout (den ``test_e2e_release_
regression.py`` bereits abdeckt, aber eben nicht am tatsächlich gebauten
Kandidaten) – ``bgremover.acceptance_smoke``.

Alle Pass/Fail-Entscheidungen liegen in den getesteten Funktionen von
``release_abnahme``. Die OS-Kommandos laufen über einen injizierbaren
``Runner``, damit der Orchestrierungs-Fluss ohne echte Hardware getestet werden
kann. Betrieb/Kriterien: ``docs/RELEASE_AUTOMATION.md``,
``docs/PACKAGING_SMOKE.md``.
"""
from __future__ import annotations

import argparse
import atexit
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

# Wegwerf-Entpackverzeichnis fuer den Update-Check-Vorgaengernachweis (#748):
# jede geprüfte AppImage bekommt ihr eigenes Unterverzeichnis (Name = Stem der
# Datei), damit Vorgänger- und Kandidaten-Entpackung sich nicht überschreiben.
TEMP_APPIMAGE_EXTRACT_ROOT = "/tmp/abnahme-update-check-appimage"
UPDATE_CHECK_EVIDENCE_DIR_NAME = "update_check"
UPDATE_CHECK_PROBE = REPO_ROOT / "scripts" / "update_probe_cli.py"

# Rollen des Vorgängernachweises. Der Vorgänger MUSS ein bereits
# veröffentlichtes Release sein (Quelle ``release-tag``), der Kandidat der
# gerade geprüfte Build (Quelle ``run-id``) – ein vertauschtes Paar wäre kein
# Nachweis, sondern eine Selbstbestätigung.
UPDATE_CHECK_ROLE_PREDECESSOR = "vorgaenger"
UPDATE_CHECK_ROLE_CANDIDATE = "kandidat"
UPDATE_CHECK_EXPECTED_STATUS = {
    UPDATE_CHECK_ROLE_PREDECESSOR: "UPDATE_AVAILABLE",
    UPDATE_CHECK_ROLE_CANDIDATE: "UP_TO_DATE",
}
UPDATE_CHECK_EXPECTED_SOURCE = {
    UPDATE_CHECK_ROLE_PREDECESSOR: "release-tag",
    UPDATE_CHECK_ROLE_CANDIDATE: "run-id",
}
UPDATE_CHECK_OUTPUT_NAMES = {
    UPDATE_CHECK_ROLE_PREDECESSOR: "predecessor.json",
    UPDATE_CHECK_ROLE_CANDIDATE: "current.json",
}
# Zusammenfassende UPDATE-01-Evidenz: verbindet die Sonden-Nutzlast beider
# Rollen mit der Herkunft der geprüften Artefakte (#748 verlangt Artefaktquelle,
# Hash, Plattform, Ausgangs- und Zielversion sowie Antwortstatus an EINER
# Stelle). Enthält bewusst nur öffentlich Bekanntes – kein Token, keine
# Authorization-Header, keine Runner-Geheimnisse.
UPDATE_CHECK_SUMMARY_NAME = "update_check.json"
UPDATE_CHECK_SUMMARY_SCHEMA = 1
UPDATE_CHECK_SUMMARY_KIND = "abnahme-update-check"
# Befunde je Rolle. ``CHECK_FAILED`` ist ein eigener, harter Zustand (#748):
# ein Netzwerk-/Parsing-Fehler darf nie als „kein Update" durchgehen.
UPDATE_CHECK_VERDICT_OK = "ok"
UPDATE_CHECK_VERDICT_CHECK_FAILED = "CHECK_FAILED"
UPDATE_CHECK_VERDICT_NO_EVIDENCE = "KEINE_EVIDENZ"
UPDATE_CHECK_VERDICT_SOURCE_VERSION = "AUSGANGSVERSION_ABWEICHEND"
UPDATE_CHECK_VERDICT_STATUS = "STATUS_UNERWARTET"
UPDATE_CHECK_VERDICT_TARGET_VERSION = "ZIELVERSION_ABWEICHEND"

# Nativer 3D-Screenshot-Nachweis (#648): großzügigeres Timeout als der
# Headless-Start – Shader-Compile + erster Mesh-Build auf echter (ggf.
# schwächerer Raspberry-Pi-)Hardware brauchen spürbar länger als der reine
# Prozessstart.
NATIVE_3D_TIMEOUT = 180
NATIVE_3D_SCREENSHOT_NAMES = {
    "appimage": "native_preview3d_ready_appimage.png",
    "deb": "native_preview3d_ready_deb.png",
    "dmg": "native_preview3d_ready_dmg.png",
}
NATIVE_3D_PROVENANCE_SCHEMA = 2
NATIVE_3D_REQUIRED_CONTROLS = (
    "preview3d_azimuth",
    "preview3d_elevation",
    "preview3d_quality_standard",
)
# Bereitschafts-Timeout des Automationshooks selbst (BGREMOVER_SCREENSHOT_3D_
# TIMEOUT_MS, siehe bgremover/app.py) – bewusst kleiner als NATIVE_3D_TIMEOUT:
# der äußere Wächter (smoke_launch.py) braucht danach noch Zeit für
# Prozessstart, Screenshot-/Provenance-Schreiben und sauberes Beenden, bevor
# sein eigenes Timeout greift (Codex-Fund, PR #652 – sonst bliebe das
# großzügigere NATIVE_3D_TIMEOUT für den Hook selbst wirkungslos).
NATIVE_3D_READINESS_TIMEOUT_MS = (NATIVE_3D_TIMEOUT - 30) * 1000

# EufyMake-Export-/2.7.0-Projekt-Zusatznachweis (#685-Review): kein GL, kein
# Shader-Compile – deutlich kürzeres Timeout als der 3D-Screenshot reicht auch
# auf schwächerer Zielhardware (Raspberry Pi).
ACCEPTANCE_EXTRA_TIMEOUT = 60
# Der Hook ruft bgremover.acceptance_smoke._runtime_provenance() auf, die
# deterministisch einen eigenen multiprocessing-spawn-Kindprozess startet
# (Herkunftsnachweis Bundle vs. Checkout, #738/#740) – zusätzlich zu GUI +
# ggf. KI-Warmup-Kind + Tracker. Ohne diesen Spielraum meldet der Fork-Bomb-
# Wächter auf realer macOS-Hardware reproduzierbar eine Fork-Bombe, obwohl
# jeder einzelne Prozess erwartet und beabsichtigt ist (beobachtet in den
# Abnahmeläufen 31971337146 und 31976909907, jeweils peak_instanzen=6 bei
# max_instances=5 in exakt dieser Phase).
ACCEPTANCE_EXTRA_INSTANCE_MARGIN = 1
ACCEPTANCE_EXTRA_NAMES = {
    "appimage": "acceptance_extra_appimage.json",
    "deb": "acceptance_extra_deb.json",
    "dmg": "acceptance_extra_dmg.json",
}
# Muss zu ``bgremover.acceptance_smoke._EVIDENCE_SCHEMA`` passen. Bei jeder
# neuen Teilprüfung mitziehen – sonst meldet ein Kandidat mit älterem Hook
# still grün, obwohl die neue Prüfung dort gar nicht existiert (#686).
ACCEPTANCE_EXTRA_SCHEMA = 3
ACCEPTANCE_EXTRA_REQUIRED = (
    "visible_version", "v270_project_open", "eufymake_export",
    "project_copy", "missing_component",
)
# Vom Source-Checkout mitgelieferte Fixture (#685): der laufende gepackte
# Prozess bekommt nur den *Pfad*, ihre Verarbeitung muss aus dem Paket kommen.
V270_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "project_v2_7_0.bgrproj"


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


def _load_smoke_launch():  # type: ignore[no-untyped-def]
    """``smoke_launch`` als Modul laden (scripts/ ist kein Paket).

    Liefert Zugriff auf ``parse_result_line`` – die maschinenlesbare
    ``SMOKE_LAUNCH_RESULT``-Zeile, die ``smoke_launch.py`` seit dem
    #642-Nachtrag zusätzlich auf stdout schreibt.
    """
    spec = importlib.util.spec_from_file_location(
        "smoke_launch", REPO_ROOT / "scripts" / "smoke_launch.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("smoke_launch", module)
    spec.loader.exec_module(module)
    return module


ra = _load_release_abnahme()
sl = _load_smoke_launch()

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
    native_3d_attempted: set[str] = field(default_factory=set)
    acceptance_extra_attempted: set[str] = field(default_factory=set)
    # Strukturierte Wächter-Ergebnisse je Startphase/Artefaktklasse (#642-Nachtrag,
    # Schließkriterium: Exit-Code/Peak-Instanzen/Timeout-Fork-Bomb-Status/Log
    # müssen in die Evidenz statt nur in Freitext-Notizen einfließen).
    guard_results: list[dict[str, Any]] = field(default_factory=list)

    def fail(self, note: str) -> None:
        self.passed = False
        self.notes.append(note)

    def ok(self, note: str) -> None:
        self.notes.append(note)


# Länge, auf die verwertbare Logausgabe je Wächter-Eintrag begrenzt wird –
# genug für die Fehlersuche, ohne die Evidenz durch komplette Prozess-Logs
# ausufern zu lassen.
_GUARD_LOG_MAX_CHARS = 2000

# Rückwärts-Lookup Screenshot-Dateiname → Artefaktklasse für den nativen
# 3D-Nachweis – aus ``NATIVE_3D_SCREENSHOT_NAMES`` abgeleitet statt dupliziert,
# damit die beiden Zuordnungen nie auseinanderlaufen können.
_SCREENSHOT_NAME_TO_CLASS = {name: cls for cls, name in NATIVE_3D_SCREENSHOT_NAMES.items()}


def _command_detail(result: CommandResult) -> str:
    """Kurzfassung der Prozessausgabe für eine Fehlermeldung.

    ``_default_runner`` fängt stdout/stderr per ``capture_output`` ab; ohne
    diesen Helfer landet die eigentliche Diagnose ungewächter Kommandos
    (apt-get, hdiutil) nirgends im Joblog. Auf ``_GUARD_LOG_MAX_CHARS``
    begrenzt – dieselbe Grenze wie für die Wächter-Logs.
    """
    detail = (result.stderr or result.stdout or "").strip()
    return detail[-_GUARD_LOG_MAX_CHARS:] if detail else "keine Ausgabe"


def _record_guard(
    report: SmokeReport, result: CommandResult, *, phase: str, artifact_class: str,
) -> None:
    """Wächter-Ergebnis eines ``smoke_launch.py``-Aufrufs strukturiert erfassen.

    Parst die maschinenlesbare ``SMOKE_LAUNCH_RESULT``-Zeile aus *result*
    (``sl.parse_result_line``); fehlt sie (z. B. gefälschter Test-Runner ohne
    echten Subprozess), bleiben ``peak_instanzen``/``status`` ``None``/
    ``"unbekannt"`` statt den Smoke zum Scheitern zu bringen – die
    Fail/Pass-Entscheidung selbst liegt weiter bei ``report.fail``/``report.ok``.

    Drei Codex-Funde zu PR #657 behoben:
    - ``exit_code`` ist – falls geparst – der Exit-Code des GEWÄCHTEN Prozesses
      (aus der Nutzlast), nicht der immer auf 0/1 normalisierte Exit-Code von
      ``smoke_launch.py`` selbst (sonst ginge z. B. ein Ziel-Exit 7 als „1"
      in die Evidenz ein). ``result.returncode`` bleibt nur der Fallback ohne
      Nutzlast.
    - ``log`` kombiniert stdout **und** stderr (statt nur stderr zu behalten,
      falls beide nicht leer sind) – sonst ginge auf stdout geschriebene
      Diagnose des gewächten Prozesses verloren.
    - Da ``_default_runner`` den Subprozess mit ``capture_output=True``
      abfängt, landet nichts davon automatisch im Actions-Job-Log; die
      Wächter-Zusammenfassung wird deshalb zusätzlich auf das eigene stdout
      von ``abnahme_smoke.py`` gedruckt (das der Job unverändert live zeigt).
    """
    parsed = sl.parse_result_line(result.stdout)
    exit_code = (parsed.get("exit_code") if parsed else None)
    if exit_code is None:
        exit_code = result.returncode
    segments = [
        f"{label}:\n{stream.strip()}"
        for label, stream in (("stdout", result.stdout), ("stderr", result.stderr))
        if stream and stream.strip()
    ]
    log = "\n".join(segments)
    entry = {
        "phase": phase,
        "artefaktklasse": artifact_class,
        "exit_code": exit_code,
        "peak_instanzen": parsed.get("peak_instances") if parsed else None,
        "status": (parsed.get("status") if parsed else None) or "unbekannt",
        "log": log[-_GUARD_LOG_MAX_CHARS:],
    }
    report.guard_results.append(entry)
    print(
        f"[waechter] phase={entry['phase']} artefaktklasse={entry['artefaktklasse']} "
        f"status={entry['status']} exit_code={entry['exit_code']} "
        f"peak_instanzen={entry['peak_instanzen']}"
    )


_neutral_dir: Path | None = None


def neutral_workdir() -> Path:
    """Leeres Arbeitsverzeichnis für Artefaktstarts (#740).

    Der AppRun-Entrypoint startet die App als ``python -m bgremover``; CPython
    stellt bei ``-m`` das aktuelle Verzeichnis an den Anfang von ``sys.path``.
    Läuft der Wächter im Checkout (``_default_runner`` nutzt ``REPO_ROOT``),
    gewinnt dessen ``bgremover/`` gegen das gebündelte Paket – der Smoke prüft
    dann den Checkout statt des Artefakts, und zwar für Haupt- **und**
    Spawn-Kindprozess. Das Verzeichnis wird einmal je Prozess angelegt und am
    Ende wieder entfernt; es darf kein ``bgremover/`` enthalten.
    """
    global _neutral_dir
    if _neutral_dir is None:
        path = Path(tempfile.mkdtemp(prefix="bgremover-abnahme-neutral-"))
        atexit.register(shutil.rmtree, path, True)
        _neutral_dir = path
    return _neutral_dir


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
    report: SmokeReport, phase: str, artifact_class: str,
) -> CommandResult:
    """Artefakt über den Fork-Bomb-/Hänger-Wächter starten (smoke_launch.py).

    ``--match`` ist Pflicht (sonst bricht argparse mit Exit 2 ab). Das
    Wächter-Ergebnis (Exit-Code/Peak-Instanzen/Status) wird strukturiert unter
    *phase*/*artifact_class* an ``report.guard_results`` angehängt (#642-Nachtrag).
    """
    result = runner(
        [
            sys.executable, str(SMOKE_LAUNCH),
            "--match", match,
            "--max-instances", str(max_instances),
            "--timeout", str(timeout),
            # Neutrales cwd: sonst beschattet der Checkout das gebündelte
            # Paket und der Smoke prüft nicht das Artefakt (#740).
            "--workdir", str(neutral_workdir()),
            "--", *launch_cmd,
        ]
    )
    _record_guard(report, result, phase=phase, artifact_class=artifact_class)
    return result


def _run_ai_selfcheck_if_needed(
    runner: Runner,
    launch_cmd: list[str],
    *,
    match: str,
    max_instances: int,
    name: str,
    artifact_class: str,
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
        report=report, phase="ki_selbsttest", artifact_class=artifact_class,
    )
    if selfcheck.returncode == 0:
        report.ok(f"KI-Selbsttest ok: {name}")
    else:
        report.fail(f"KI-Selbsttest fehlgeschlagen ({selfcheck.returncode}): {name}")


def validate_native_3d_provenance(payload: object) -> tuple[bool, str]:
    """Prüft Sidecar-Schema und den vollständigen geometrischen Controls-Nachweis."""
    if not isinstance(payload, dict):
        return False, "Provenance-Nutzlast ist kein JSON-Objekt"
    schema = payload.get("schema")
    visible_controls = payload.get("preview3d_visible_controls")
    controls_complete = (
        payload.get("preview3d_controls_visible") is True
        and isinstance(visible_controls, list)
        and all(isinstance(name, str) for name in visible_controls)
        and set(visible_controls) == set(NATIVE_3D_REQUIRED_CONTROLS)
        and len(visible_controls) == len(NATIVE_3D_REQUIRED_CONTROLS)
    )
    if schema != NATIVE_3D_PROVENANCE_SCHEMA or not controls_complete:
        return (
            False,
            f"Schema {schema!r}, Controls {visible_controls!r}",
        )
    return True, "geometrischer Controls-Nachweis vollständig"


def _native_3d_screenshot(
    runner: Runner,
    launch_cmd: list[str],
    *,
    match: str,
    max_instances: int,
    label: str,
    report: SmokeReport,
    screenshot_dir: Path,
    screenshot_name: str,
) -> None:
    """Nativer 3D-Render-Nachweis des gepackten Artefakts (#648).

    Startet dasselbe Artefakt-Kommando wie der Headless-Smoke ein zweites Mal
    – über ``smoke_launch.py --native`` (kein erzwungenes ``offscreen``/
    ``BGREMOVER_SMOKE_TEST``) mit dem Automationshook
    ``BGREMOVER_SCREENSHOT_3D``. Der Fork-Bomb-/Hänger-Wächter bleibt aktiv;
    nur der erzwungene Offscreen-Betrieb entfällt. Läuft nur einmal je
    Artefaktklasse. AppImage, installiertes ``.deb``-AppImage und DMG erhalten
    getrennte Dateinamen, damit jede der in ``PACKAGING_SMOKE.md`` geforderten
    Klassen ihren eigenen nativen Nachweis trägt. Derselbe Dateiname wird
    innerhalb eines Laufs höchstens einmal erzeugt.
    """
    if screenshot_name in report.native_3d_attempted:
        return
    report.native_3d_attempted.add(screenshot_name)

    screenshot_dir.mkdir(parents=True, exist_ok=True)
    target = (screenshot_dir / screenshot_name).resolve()
    result = runner([
        sys.executable, str(SMOKE_LAUNCH),
        "--match", match,
        "--max-instances", str(max_instances),
        "--timeout", str(NATIVE_3D_TIMEOUT),
        "--native",
        "--workdir", str(neutral_workdir()),  # nicht im Checkout starten (#740)
        "--env", f"BGREMOVER_SCREENSHOT_3D={target}",
        "--env", f"BGREMOVER_SCREENSHOT_3D_TIMEOUT_MS={NATIVE_3D_READINESS_TIMEOUT_MS}",
        "--", *launch_cmd,
    ])
    _record_guard(
        report, result, phase="nativer_3d_screenshot",
        artifact_class=_SCREENSHOT_NAME_TO_CLASS.get(screenshot_name, "unbekannt"),
    )
    sidecar = target.with_name(target.name + ".json")
    if result.returncode != 0 or not target.is_file() or not sidecar.is_file():
        detail = (result.stderr or result.stdout or "").strip()
        report.fail(f"Nativer 3D-Screenshot fehlgeschlagen ({label}): {detail or 'kein Screenshot erzeugt'}")
        return
    try:
        provenance = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report.fail(f"Nativer 3D-Screenshot: Provenance-JSON unlesbar ({label}): {exc}")
        return

    controls_ok, controls_detail = validate_native_3d_provenance(provenance)
    if not controls_ok:
        report.fail(
            "Nativer 3D-Screenshot: geometrischer Controls-Nachweis fehlt oder ist "
            f"unvollständig ({label}; {controls_detail})"
        )
        return

    verdict = ra.evaluate_gl_provenance(str(provenance.get("gl_provenance") or ""))
    if verdict.ok:
        report.ok(f"Nativer 3D-Screenshot ok ({label}): {verdict.note}")
    else:
        report.fail(f"Nativer 3D-Screenshot: {verdict.note} ({label})")


def _acceptance_extra(
    runner: Runner,
    launch_cmd: list[str],
    *,
    match: str,
    max_instances: int,
    label: str,
    report: SmokeReport,
    evidence_dir: Path,
    artifact_class: str,
) -> None:
    """EufyMake-Export-/2.7.0-Projekt-Zusatznachweis des gepackten Artefakts
    (#685-Review, Codex-Fund auf PR #720).

    Startet dasselbe Artefakt-Kommando erneut über ``smoke_launch.py --native``
    mit dem Automationshook ``BGREMOVER_ACCEPTANCE_EXTRA`` – analog
    ``_native_3d_screenshot``, aber ohne GL-Bezug. ``--native`` (statt der
    normalen ``offscreen``+``BGREMOVER_SMOKE_TEST``-Startumgebung) ist trotzdem
    nötig: ``BGREMOVER_SMOKE_TEST`` beendet den Prozess sonst schon vor dem
    ersten Event-Loop-Tick, bevor der Hook seinen eigenen ``app.exit()`` erreicht.
    Läuft nur einmal je Artefaktklasse.
    """
    if artifact_class in report.acceptance_extra_attempted:
        return
    report.acceptance_extra_attempted.add(artifact_class)

    evidence_dir.mkdir(parents=True, exist_ok=True)
    target = (evidence_dir / ACCEPTANCE_EXTRA_NAMES[artifact_class]).resolve()
    # Sollwert für die sichtbare Produktversion aus dem Artefaktdateinamen
    # (#686): ein *externer* Wert – ohne ihn verglichen sich Paket und Prüfung
    # nur selbst. ``label`` ist der Dateiname des geprüften Artefakts.
    expected_version = ra.version_from_artifact_name(Path(label).name)
    env_args = [
        "--env", f"BGREMOVER_ACCEPTANCE_EXTRA={target}",
        "--env", f"BGREMOVER_ACCEPTANCE_EXTRA_V270_PROJECT={V270_FIXTURE}",
    ]
    if expected_version:
        env_args += ["--env", f"BGREMOVER_ACCEPTANCE_EXTRA_VERSION={expected_version}"]
    # +ACCEPTANCE_EXTRA_INSTANCE_MARGIN: der Hook startet selbst einen
    # zusätzlichen, beabsichtigten spawn-Kindprozess (Herkunftsnachweis) –
    # siehe Konstantendefinition oben.
    result = runner([
        sys.executable, str(SMOKE_LAUNCH),
        "--match", match,
        "--max-instances", str(max_instances + ACCEPTANCE_EXTRA_INSTANCE_MARGIN),
        "--timeout", str(ACCEPTANCE_EXTRA_TIMEOUT),
        "--native",
        "--workdir", str(neutral_workdir()),  # nicht im Checkout starten (#740)
        *env_args,
        "--", *launch_cmd,
    ])
    _record_guard(report, result, phase="acceptance_extra", artifact_class=artifact_class)
    if result.returncode != 0 or not target.is_file():
        detail = (result.stderr or result.stdout or "").strip()
        report.fail(
            f"EufyMake/2.7.0-Zusatznachweis fehlgeschlagen ({label}): "
            f"{detail or 'keine Evidenz erzeugt'}"
        )
        return
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report.fail(f"EufyMake/2.7.0-Zusatznachweis: Evidenz-JSON unlesbar ({label}): {exc}")
        return

    # Schemaversion zuerst: Der Hook läuft im **gepackten Artefakt** und kann
    # damit älter sein als dieses Skript aus dem Checkout. Ein Kandidat mit dem
    # Vorgänger-Hook schreibt dieselbe Struktur mit ``ok: true``, aber ohne
    # ``visible_version``/``project_copy`` – ein früher ``ok``-Kurzschluss hätte
    # ihn grün gemeldet, obwohl die neuen Prüfungen nie gelaufen sind (#686).
    schema = payload.get("schema")
    if schema != ACCEPTANCE_EXTRA_SCHEMA:
        report.fail(
            f"EufyMake/2.7.0-Zusatznachweis ({label}): Evidenz-Schema {schema!r} "
            f"statt {ACCEPTANCE_EXTRA_SCHEMA!r} – das gepackte Artefakt bringt "
            "einen älteren Hook mit, die neuen Prüfungen sind nicht gelaufen."
        )
        return

    # Herkunft des geprüften Codes IMMER ausweisen – auch bei Erfolg. Der Hook
    # soll das gepackte Artefakt belegen; stammt der Code aus dem Checkout, ist
    # der Nachweis wertlos, und genau das war bisher aus dem Joblog nicht
    # erkennbar (#686-Nachtrag, beobachtet in Lauf 30581788054).
    # Herkunft ZUERST ausgeben – vor jedem Pass/Fail-Zweig. Bei einem
    # Fehlschlag ist sie am wichtigsten (stammte der geprüfte Code überhaupt
    # aus dem Bundle?), und ein grüner Lauf aus dem falschen Pfad ist der
    # gefährlichere Fall.
    herkunft = payload.get("laufzeit_herkunft") or {}
    if herkunft:
        print(
            f"[herkunft] {label}: bgremover={herkunft.get('bgremover_datei')!r} "
            f"ai_process={herkunft.get('ai_process_datei')!r} "
            f"interpreter={herkunft.get('interpreter')!r} "
            f"eingefroren={herkunft.get('eingefroren')!r} "
            f"cwd={herkunft.get('arbeitsverzeichnis')!r} "
            f"sys_path_0={herkunft.get('sys_path_0')!r}"
        )
        # Der spawn-Kindprozess ist der eigentliche Fundort (#738): Er kann
        # Module aus einem anderen Pfad laden als sein Elternprozess.
        kind = herkunft.get("kindprozess") or {}
        print(
            f"[herkunft-kind] {label}: bgremover={kind.get('bgremover_datei')!r} "
            f"ai_process={kind.get('ai_process_datei')!r} "
            f"sys_path_0={kind.get('sys_path_0')!r} fehler={kind.get('fehler')!r}"
        )

    # Jede erwartete Teilprüfung muss vorhanden UND grün sein. Ein fehlender
    # Schlüssel gilt als Fehlschlag, nicht als „nicht zutreffend".
    missing = [key for key in ACCEPTANCE_EXTRA_REQUIRED if key not in payload]
    if missing:
        report.fail(
            f"EufyMake/2.7.0-Zusatznachweis ({label}): Teilergebnisse fehlen in der "
            f"Evidenz: {sorted(missing)}"
        )
        return
    failed = [
        f"{key}={(payload.get(key) or {}).get('message')!r}"
        for key in ACCEPTANCE_EXTRA_REQUIRED
        if not (payload.get(key) or {}).get("ok")
    ]
    if failed or not payload.get("ok"):
        report.fail(
            f"EufyMake/2.7.0-Zusatznachweis fehlgeschlagen ({label}): "
            f"{' '.join(failed) or 'ok=false ohne benannte Teilprüfung'}"
        )
        return

    herkunft = payload.get("laufzeit_herkunft") or {}
    if not herkunft:
        # Schema 3 sagt zu, die Herkunft bei jedem Lauf auszuweisen. Fehlt sie
        # trotz passender Schemaversion, ist der Erzeuger defekt – das still
        # durchzuwinken hieße, genau die Zusicherung zu brechen, für die die
        # Schemaversion angehoben wurde (Codex-Fund auf PR #738).
        report.fail(
            f"EufyMake/2.7.0-Zusatznachweis ({label}): Evidenz mit Schema "
            f"{ACCEPTANCE_EXTRA_SCHEMA} ohne 'laufzeit_herkunft' – Herkunft des "
            "geprüften Codes nicht nachweisbar."
        )
        return
    report.ok(f"EufyMake/2.7.0-Zusatznachweis ok ({label})")


@dataclass(frozen=True)
class UpdateCheckSubject:
    """Ein für ``UPDATE-01`` geprüftes Artefakt samt Herkunftsnachweis (#748).

    Trägt genau die Angaben, die der Nachweis laut Issue protokollieren muss –
    Artefaktquelle, Hash, Plattform – plus die *erwartete* Ausgangsversion.
    Letztere ist der Sollwert für die Version, die das laufende Artefakt SELBST
    meldet: beim Vorgänger der Release-Tag, beim Kandidaten die
    Kandidatenversion. Ohne diesen Abgleich stünde die Ausgangsversion zwar in
    der Evidenz, wäre aber nicht falsifizierbar.
    """

    role: str
    path: str
    expected_version: str
    sha256: str
    digest_verified: bool
    source_kind: str
    source_value: str
    platform: str

    @property
    def label(self) -> str:
        return f"{self.role} {Path(self.path).name}"


def normalize_version(value: str | None) -> str:
    """Versionsvergleich ohne führendes ``v`` (Tag ``v2.7.1`` ↔ Paket ``2.7.1``)."""
    return str(value or "").strip().lstrip("vV")


def build_update_check_subject(
    evidence_dir: Path, role: str, *, expected_version: str = "",
) -> UpdateCheckSubject:
    """Baut aus einem ``release_abnahme.py``-Evidenzverzeichnis das Subjekt für
    eine Rolle des Vorgängernachweises (#748).

    Herkunft (Quelle, SHA256, Digest-Bestätigung, Plattform) kommt
    ausschließlich aus ``evidenz.json`` – dieselbe Datei, die den Bezug der
    Artefakte belegt; damit lässt sich der Update-Nachweis später lückenlos auf
    genau diese Bytes zurückführen. Die Quellart wird gegen die Rolle geprüft:
    ein „Vorgänger" aus dem Kandidaten-Build (oder umgekehrt) wäre eine
    Selbstbestätigung statt eines Nachweises.

    ``expected_version`` leer heißt beim Vorgänger: aus dem Release-Tag
    ableiten. Beim Kandidaten muss sie der Aufrufer setzen (die Version steht
    nicht in der Evidenz).
    """
    evidence = json.loads((evidence_dir / "evidenz.json").read_text(encoding="utf-8"))
    source = evidence.get("quelle") or {}
    expected_source = UPDATE_CHECK_EXPECTED_SOURCE[role]
    if source.get("art") != expected_source:
        raise ValueError(
            f"Update-Check ({role}): Evidenzquelle {source.get('art')!r} statt "
            f"{expected_source!r} – {evidence_dir}"
        )
    appimages = [
        a for a in evidence.get("artefakte", []) if str(a.get("name", "")).endswith(".AppImage")
    ]
    if len(appimages) != 1:
        # Genau eine: nur so ist eindeutig, welches Artefakt den Nachweis
        # getragen hat. Mehrere (oder keine) wären eine stille Auswahl.
        raise ValueError(
            f"Update-Check ({role}): genau eine AppImage erwartet, gefunden "
            f"{[a.get('name') for a in appimages]} – {evidence_dir}"
        )
    artefact = appimages[0]
    version = expected_version
    if not version and role == UPDATE_CHECK_ROLE_PREDECESSOR:
        # Nur beim Vorgänger steht die Sollversion in der Quelle – der Tag ist
        # sie. Beim Kandidaten wäre die Quelle eine Run-ID; sie als Version zu
        # nehmen hieße, gegen eine Zahl ohne Bedeutung zu prüfen.
        version = normalize_version(source.get("wert"))
    if not version:
        raise ValueError(
            f"Update-Check ({role}): erwartete Ausgangsversion unbekannt – "
            "expected_version übergeben."
        )
    return UpdateCheckSubject(
        role=role,
        path=str(evidence_dir / "artefakte" / str(artefact["name"])),
        expected_version=normalize_version(version),
        sha256=str(artefact.get("sha256", "")),
        digest_verified=bool(artefact.get("digest_geprueft")),
        source_kind=str(source.get("art", "")),
        source_value=str(source.get("wert", "")),
        platform=str(evidence.get("platform", "")),
    )


def _extract_appimage(runner: Runner, appimage_path: str, label: str, report: SmokeReport) -> str | None:
    """Entpackt eine AppImage in ein eigenes Wegwerfverzeichnis und liefert den
    Pfad zum darin gebündelten Python-Interpreter (#748).

    python-appimage-Layout (``packaging/linux/build_appimage.sh``): eine
    vollständige, eigenständige CPython-Installation unter
    ``squashfs-root/usr/bin/pythonX.Y`` mit dem echten ``bgremover``-Paket in
    ihrem Site-Packages – anders als bei PyInstaller (macOS) ein generisch
    aufrufbarer Interpreter, kein reiner Bootloader.
    """
    dest = f"{TEMP_APPIMAGE_EXTRACT_ROOT}/{Path(appimage_path).stem}"
    if runner(["rm", "-rf", dest]).returncode != 0:
        report.fail(f"Update-Check: Entpack-Verzeichnis konnte nicht bereinigt werden: {dest}")
        return None
    if runner(["mkdir", "-p", dest]).returncode != 0:
        report.fail(f"Update-Check: Entpack-Verzeichnis konnte nicht angelegt werden: {dest}")
        return None
    abs_appimage = str(Path(appimage_path).resolve())
    runner(["chmod", "+x", abs_appimage])
    extract = runner([
        "/bin/sh", "-c",
        f"cd {dest} && {abs_appimage} --appimage-extract >/dev/null",
    ])
    if extract.returncode != 0:
        report.fail(
            f"Update-Check: AppImage-Entpacken fehlgeschlagen ({label}): {_command_detail(extract)}"
        )
        return None
    find_python = runner([
        "/bin/sh", "-c", f"ls {dest}/squashfs-root/usr/bin/python3.* 2>/dev/null | head -1",
    ])
    interpreter = find_python.stdout.strip().splitlines()[0] if find_python.stdout.strip() else ""
    if not interpreter:
        report.fail(f"Update-Check: kein gebündelter Interpreter gefunden ({label}): {dest}")
        return None
    return interpreter


def _update_check_record(
    subject: UpdateCheckSubject, *, verdict: str, payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Herkunft + Sondenantwort einer Rolle zu einem Evidenzeintrag verbinden.

    Die Herkunftsfelder stehen auch dann drin, wenn die Sonde gar nicht lief
    (Entpackfehler): Ein Nachweis, der nur im Erfolgsfall dokumentiert, wovon
    er handelte, ist im Fehlerfall wertlos.
    """
    payload = payload or {}
    return {
        "rolle": subject.role,
        "artefakt": Path(subject.path).name,
        "quelle": {"art": subject.source_kind, "wert": subject.source_value},
        "sha256": subject.sha256,
        "digest_geprueft": subject.digest_verified,
        "plattform": subject.platform,
        "erwartete_ausgangsversion": subject.expected_version,
        "gemeldete_ausgangsversion": payload.get("current_version"),
        "erwarteter_status": UPDATE_CHECK_EXPECTED_STATUS[subject.role],
        "status": payload.get("status"),
        "zielversion": payload.get("latest_version"),
        "release_url": payload.get("release_url"),
        "interpreter": payload.get("interpreter"),
        "fehler": payload.get("error"),
        "befund": verdict,
    }


def _update_check(
    runner: Runner, subject: UpdateCheckSubject, *,
    report: SmokeReport, evidence_dir: Path, expected_latest_version: str,
) -> dict[str, Any]:
    """Echter Update-Check-Nachweis (#748) unter dem im Artefakt gebündelten
    Interpreter: ruft ``scripts/update_probe_cli.py`` auf, der ausschließlich
    ``bgremover.app_update``/``bgremover._version`` importiert – beide existieren
    unverändert seit deutlich vor #748, weshalb dieser Weg auch gegen ein
    bereits veröffentlichtes, älteres Artefakt funktioniert (kein neuer Hook
    im geprüften Artefakt nötig).

    Die Rolle des Subjekts legt den erwarteten Status fest (Vorgänger →
    ``UPDATE_AVAILABLE``, Kandidat → ``UP_TO_DATE``). Geprüft wird in dieser
    Reihenfolge, weil jede Stufe die nächste erst aussagekräftig macht:

    1. ``CHECK_FAILED`` – eigener harter Zustand, nie „kein Update".
    2. die vom Artefakt SELBST gemeldete Ausgangsversion gegen den Sollwert der
       Herkunft: erst damit steht fest, dass wirklich der Vorgänger- bzw.
       Kandidatencode lief und nicht ein danebenliegendes Bundle.
    3. der Status.
    4. beim Vorgänger die gemeldete Zielversion gegen den Kandidaten.

    Liefert den Evidenzeintrag der Rolle (auch im Fehlerfall).
    """
    interpreter = _extract_appimage(runner, subject.path, subject.label, report)
    if interpreter is None:
        return _update_check_record(subject, verdict=UPDATE_CHECK_VERDICT_NO_EVIDENCE)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    target = (evidence_dir / UPDATE_CHECK_OUTPUT_NAMES[subject.role]).resolve()
    result = runner([
        interpreter, str(UPDATE_CHECK_PROBE), "--output", str(target),
    ])
    _record_guard(report, result, phase="update_check", artifact_class=subject.label)
    if not target.is_file():
        report.fail(
            f"Update-Check ({subject.label}): keine Evidenz erzeugt: {_command_detail(result)}"
        )
        return _update_check_record(subject, verdict=UPDATE_CHECK_VERDICT_NO_EVIDENCE)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report.fail(f"Update-Check ({subject.label}): Evidenz-JSON unlesbar: {exc}")
        return _update_check_record(subject, verdict=UPDATE_CHECK_VERDICT_NO_EVIDENCE)

    verdict = _update_check_verdict(
        subject, payload, report, expected_latest_version=expected_latest_version,
    )
    if verdict == UPDATE_CHECK_VERDICT_OK:
        report.ok(f"Update-Check ok ({subject.label}): {payload.get('status')}")
    return _update_check_record(subject, verdict=verdict, payload=payload)


def _update_check_verdict(
    subject: UpdateCheckSubject, payload: dict[str, Any], report: SmokeReport, *,
    expected_latest_version: str,
) -> str:
    """Bewertet eine Sondenantwort; meldet den ersten Verstoß an *report*."""
    status = payload.get("status")
    if status == "CHECK_FAILED":
        report.fail(
            f"Update-Check ({subject.label}): Netzwerk-Roundtrip fehlgeschlagen: "
            f"{payload.get('error')}"
        )
        return UPDATE_CHECK_VERDICT_CHECK_FAILED

    reported = normalize_version(payload.get("current_version"))
    if reported != subject.expected_version:
        report.fail(
            f"Update-Check ({subject.label}): das laufende Artefakt meldet Version "
            f"{payload.get('current_version')!r}, erwartet war {subject.expected_version!r} – "
            "geprüft wurde nicht das vorgesehene Bundle."
        )
        return UPDATE_CHECK_VERDICT_SOURCE_VERSION

    expected_status = UPDATE_CHECK_EXPECTED_STATUS[subject.role]
    if status != expected_status:
        report.fail(
            f"Update-Check ({subject.label}): erwartet {expected_status}, gemeldet {status} "
            f"(current={payload.get('current_version')!r} latest={payload.get('latest_version')!r})"
        )
        return UPDATE_CHECK_VERDICT_STATUS

    if subject.role == UPDATE_CHECK_ROLE_PREDECESSOR:
        latest = normalize_version(payload.get("latest_version"))
        if latest != normalize_version(expected_latest_version):
            report.fail(
                f"Update-Check ({subject.label}): meldet UPDATE_AVAILABLE, aber latest_version "
                f"{payload.get('latest_version')!r} weicht vom erwarteten Kandidaten "
                f"{expected_latest_version!r} ab."
            )
            return UPDATE_CHECK_VERDICT_TARGET_VERSION
    return UPDATE_CHECK_VERDICT_OK


def _update_check_linux(
    predecessor: UpdateCheckSubject, candidate: UpdateCheckSubject,
    report: SmokeReport, runner: Runner, evidence_root: Path,
) -> None:
    """Echter Vorgänger-Nachweis für ``UPDATE-01`` (#748): ein bereits
    veröffentlichtes Vorgänger-Release muss ``UPDATE_AVAILABLE`` melden, der
    aktuell geprüfte Kandidat ``UP_TO_DATE`` – beide über den echten,
    unauthentifizierten GitHub-Releases-API-Roundtrip aus
    ``bgremover.app_update``, ausgeführt unter dem jeweils im Artefakt
    gebündelten Interpreter (siehe ``_update_check``).

    Schreibt anschließend die zusammenfassende Evidenz mit Artefaktquelle,
    Hash, Plattform, Ausgangs- und Zielversion sowie Antwortstatus je Rolle.
    """
    evidence_dir = evidence_root / UPDATE_CHECK_EVIDENCE_DIR_NAME
    if predecessor.expected_version == candidate.expected_version:
        # Gleiche Version auf beiden Seiten: der Vorgänger könnte gar kein
        # Update sehen, der „Nachweis" prüfte ein Release gegen sich selbst.
        report.fail(
            f"Update-Check: Vorgänger und Kandidat tragen dieselbe Version "
            f"{candidate.expected_version!r} – der Nachweis wäre gegenstandslos."
        )
        return

    records = [
        _update_check(
            runner, predecessor, report=report, evidence_dir=evidence_dir,
            expected_latest_version=candidate.expected_version,
        ),
        _update_check(
            runner, candidate, report=report, evidence_dir=evidence_dir,
            expected_latest_version=candidate.expected_version,
        ),
    ]
    _write_update_check_summary(evidence_dir, records, candidate.expected_version)


def _write_update_check_summary(
    evidence_dir: Path, records: list[dict[str, Any]], candidate_version: str,
) -> None:
    """Zusammenfassende UPDATE-01-Evidenz schreiben und ins Joblog spiegeln.

    Ins Joblog, weil ``_default_runner`` die Ausgaben der Teilschritte per
    ``capture_output`` abfängt: ohne diese Zeilen stünde die Kernaussage des
    Nachweises nur in einem mehrere hundert MB großen Evidenz-Artefakt.
    """
    evidence_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema": UPDATE_CHECK_SUMMARY_SCHEMA,
        "kind": UPDATE_CHECK_SUMMARY_KIND,
        "erzeugt_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kandidaten_version": candidate_version,
        "ok": all(r["befund"] == UPDATE_CHECK_VERDICT_OK for r in records),
        "pruefungen": records,
    }
    (evidence_dir / UPDATE_CHECK_SUMMARY_NAME).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    for record in records:
        print(
            f"[update-check] rolle={record['rolle']} artefakt={record['artefakt']} "
            f"quelle={record['quelle']['art']}:{record['quelle']['wert']} "
            f"sha256={record['sha256']} plattform={record['plattform']} "
            f"ausgangsversion={record['gemeldete_ausgangsversion']!r} "
            f"(erwartet {record['erwartete_ausgangsversion']!r}) "
            f"status={record['status']} zielversion={record['zielversion']!r} "
            f"befund={record['befund']}"
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
    screenshot_dir: Path, *,
    predecessor: UpdateCheckSubject | None = None,
    candidate: UpdateCheckSubject | None = None,
) -> SmokeReport:
    """AppImage- und ``.deb``-Smoke auf einem Linux-Runner (#642).

    ``predecessor``/``candidate`` (optional, #748): die beiden Rollen des
    echten UPDATE-01-Vorgängernachweises, gebaut über
    ``build_update_check_subject``. Beide gesetzt ⇒ der Nachweis läuft; beide
    ``None`` ⇒ er entfällt ausdrücklich (bleibt ``PENDING`` statt fabriziert
    ``PASS``). Nur eine Seite gesetzt ist ein Konfigurationsfehler und
    scheitert, statt still die halbe Prüfung zu machen.
    """
    _require_extensions(artefacts, {".AppImage", ".deb"}, report)

    verdict = ra.evaluate_gl_provenance(prober())
    report.gl_diagnostic = verdict.diagnostic or None
    report.ok(verdict.note) if verdict.ok else report.fail(verdict.note)

    for artefact in artefacts:
        if artefact.endswith(".AppImage"):
            _linux_appimage(artefact, report, runner, screenshot_dir)
        elif artefact.endswith(".deb"):
            _linux_deb(artefact, report, runner, screenshot_dir)

    if predecessor is not None and candidate is not None:
        _update_check_linux(predecessor, candidate, report, runner, screenshot_dir.parent)
    elif predecessor is not None or candidate is not None:
        report.fail(
            "Update-Check: nur eine der beiden Rollen (Vorgänger/Kandidat) übergeben – "
            "der Nachweis braucht beide."
        )

    return report


def _linux_appimage(path: str, report: SmokeReport, runner: Runner, screenshot_dir: Path) -> None:
    name = Path(path).name
    runner(["chmod", "+x", path])
    max_instances = _fork_limit(name)
    launch_cmd = [path, "--appimage-extract-and-run"]
    _run_ai_selfcheck_if_needed(
        runner, launch_cmd, match=name, max_instances=max_instances, name=name,
        artifact_class="appimage", report=report,
    )
    # --appimage-extract-and-run: kein Host-FUSE nötig (wie release-linux.yml).
    result = _guard(
        runner, launch_cmd, match=name, max_instances=max_instances,
        report=report, phase="start", artifact_class="appimage",
    )
    if result.returncode == 0:
        report.ok(f"AppImage-Start ok: {name}")
        _native_3d_screenshot(
            runner, launch_cmd, match=name, max_instances=max_instances,
            label=name, report=report, screenshot_dir=screenshot_dir,
            screenshot_name=NATIVE_3D_SCREENSHOT_NAMES["appimage"],
        )
        _acceptance_extra(
            runner, launch_cmd, match=name, max_instances=max_instances,
            label=name, report=report, evidence_dir=screenshot_dir.parent / "acceptance_extra",
            artifact_class="appimage",
        )
    else:
        report.fail(f"AppImage-Start fehlgeschlagen ({result.returncode}): {name}")


def _linux_deb(
    path: str, report: SmokeReport, runner: Runner, screenshot_dir: Path,
) -> None:
    name = Path(path).name
    install = runner(["sudo", "apt-get", "install", "-y", path])
    installed_ok = install.returncode == 0
    if not installed_ok:
        # Mit Ausgabe: apt-get sagt genau, woran es scheiterte (fehlende
        # Abhängigkeit, Signatur, Plattenplatz) – ohne sie stünde im Joblog nur
        # "fehlgeschlagen" (Codex-Fund auf PR #735).
        report.fail(f"deb-Installation fehlgeschlagen: {name}: {_command_detail(install)}")
    try:
        if installed_ok:
            # Das installierte AppImage starten (kein `bgremover`-Kommando im PATH).
            max_instances = _fork_limit(name)
            launch_cmd = [DEB_INSTALLED_APPIMAGE, "--appimage-extract-and-run"]
            _run_ai_selfcheck_if_needed(
                runner, launch_cmd, match="BgRemover.AppImage", max_instances=max_instances,
                name=name, artifact_class="deb", report=report,
            )
            started = _guard(
                runner, launch_cmd, match="BgRemover.AppImage", max_instances=max_instances,
                report=report, phase="start", artifact_class="deb",
            )
            if started.returncode == 0:
                report.ok(f"deb-Start ok: {name}")
                _native_3d_screenshot(
                    runner, launch_cmd, match="BgRemover.AppImage",
                    max_instances=max_instances, label=name, report=report,
                    screenshot_dir=screenshot_dir,
                    screenshot_name=NATIVE_3D_SCREENSHOT_NAMES["deb"],
                )
                _acceptance_extra(
                    runner, launch_cmd, match="BgRemover.AppImage",
                    max_instances=max_instances, label=name, report=report,
                    evidence_dir=screenshot_dir.parent / "acceptance_extra",
                    artifact_class="deb",
                )
            else:
                report.fail(f"deb-Start fehlgeschlagen ({started.returncode}): {name}")
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
    screenshot_dir: Path,
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
            _macos_dmg(artefact, report, runner, screenshot_dir)

    return report


def _macos_dmg(path: str, report: SmokeReport, runner: Runner, screenshot_dir: Path) -> None:
    name = Path(path).name
    attach = runner(["hdiutil", "attach", "-nobrowse", "-readonly", path])
    if attach.returncode != 0:
        report.fail(f"DMG-Mount fehlgeschlagen: {name}: {_command_detail(attach)}")
        return
    mount = parse_mount_point(attach.stdout)
    disk_id = parse_disk_identifier(attach.stdout)
    # Cleanup-Trap: ``attach`` war erfolgreich, also ist ein Volume gemountet –
    # detach in jedem Fall versuchen, auch wenn der Mount-Pfad nicht geparst
    # werden konnte (sonst bleibt es haengen, #643-Fund). Detach laeuft HIER
    # bewusst nur um die Kopie herum (#651-Review-Fund): der eigentliche
    # App-Start (120s Guard-Timeout, _guard-Default) darf das DMG nicht mehr gemountet
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
        _start_macos_app(temp_app, name, report, runner, screenshot_dir)
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


def _start_macos_app(
    app: str, dmg_name: str, report: SmokeReport, runner: Runner, screenshot_dir: Path,
) -> None:
    binary = f"{app}/Contents/MacOS/{Path(app).stem}"
    match = Path(app).name
    max_instances = _fork_limit(dmg_name)
    _run_ai_selfcheck_if_needed(
        runner, [binary], match=match, max_instances=max_instances, name=dmg_name,
        artifact_class="dmg", report=report,
    )
    start = time.monotonic()
    started = _guard(
        runner, [binary], match=match, max_instances=max_instances,
        report=report, phase="start", artifact_class="dmg",
    )
    elapsed = time.monotonic() - start
    if started.returncode == 0:
        report.ok(f"DMG-Start ok: {dmg_name} (Startzeit {elapsed:.1f}s)")
        _native_3d_screenshot(
            runner, [binary], match=match, max_instances=max_instances,
            label=dmg_name, report=report, screenshot_dir=screenshot_dir,
            screenshot_name=NATIVE_3D_SCREENSHOT_NAMES["dmg"],
        )
        _acceptance_extra(
            runner, [binary], match=match, max_instances=max_instances,
            label=dmg_name, report=report,
            evidence_dir=screenshot_dir.parent / "acceptance_extra",
            artifact_class="dmg",
        )
    else:
        report.fail(f"DMG-Start fehlgeschlagen ({started.returncode}): {dmg_name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=sorted(ra.PLATFORM_PATTERNS))
    parser.add_argument("--evidence-dir", type=Path, required=True,
                        help="Verzeichnis mit evidenz.json (aus release_abnahme.py).")
    parser.add_argument("--scale-factor", type=float, default=0.0,
                        help="devicePixelRatio des macOS-Hauptfensters (nur macOS).")
    parser.add_argument(
        "--predecessor-evidence-dir", type=Path, default=None,
        help=(
            "Evidenzverzeichnis eines bereits veröffentlichten Vorgänger-"
            "Releases (release_abnahme.py --release-tag), für den echten "
            "UPDATE-01-Vorgängernachweis (#748). Nur Linux unterstützt das "
            "rückwirkend gegen ein bereits gebautes Artefakt."
        ),
    )
    parser.add_argument(
        "--candidate-version", default="",
        help="Version des geprüften Kandidaten (z. B. 2.7.2) – Sollwert für "
        "latest_version im Vorgänger-Update-Check sowie für die vom Kandidaten "
        "selbst gemeldete Ausgangsversion. Pflicht mit "
        "--predecessor-evidence-dir.",
    )
    args = parser.parse_args(argv)

    if args.predecessor_evidence_dir and not args.candidate_version:
        # Ohne Sollversion bliebe vom Nachweis nur „irgendein Update sichtbar".
        # #748 verlangt UPDATE_AVAILABLE mit exakt der neuen Zielversion.
        parser.error("--candidate-version ist mit --predecessor-evidence-dir Pflicht.")

    evidence_path = args.evidence_dir / "evidenz.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    artefacts = [
        str(args.evidence_dir / "artefakte" / a["name"]) for a in evidence["artefakte"]
    ]

    predecessor: UpdateCheckSubject | None = None
    candidate: UpdateCheckSubject | None = None
    if args.predecessor_evidence_dir:
        try:
            predecessor = build_update_check_subject(
                args.predecessor_evidence_dir, UPDATE_CHECK_ROLE_PREDECESSOR,
            )
            candidate = build_update_check_subject(
                args.evidence_dir, UPDATE_CHECK_ROLE_CANDIDATE,
                expected_version=args.candidate_version,
            )
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            parser.error(f"Update-Check-Vorgängernachweis nicht aufsetzbar: {exc}")

    screenshot_dir = args.evidence_dir / "screenshots"
    report = SmokeReport()
    if args.platform.startswith("linux"):
        run_linux_smoke(
            artefacts, report, _default_runner, _default_prober, screenshot_dir,
            predecessor=predecessor, candidate=candidate,
        )
    else:
        run_macos_smoke(
            artefacts, report, _default_runner, _default_prober, args.scale_factor,
            screenshot_dir,
        )

    finalized = ra.finalize_evidence(
        evidence, passed=report.passed, gl_provenance=report.gl_diagnostic,
        extra_notes=report.notes, guard_results=report.guard_results,
    )
    ra.write_evidence(args.evidence_dir, finalized)
    if not report.passed:
        # Der Grund stand bisher ausschließlich in evidenz.json/manifest.md: Ein
        # roter Abnahme-Lauf zeigte im Joblog nur "FEHLGESCHLAGEN", die Diagnose
        # lag in einem mehrere hundert MB großen Evidenz-Artefakt. Die Befunde
        # gehören dorthin, wo man sie zuerst sucht.
        for note in report.notes:
            print(f"[befund] {note}")
        # Die Notiz allein reicht nicht: Bei einem abgestürzten Start lautet sie
        # nur "AppImage-Start fehlgeschlagen (1)", während die eigentliche
        # Ausgabe des gewächten Prozesses in ``guard_results[*]["log"]`` liegt
        # und ``_default_runner`` sie per ``capture_output`` abfängt. Ohne diese
        # Zeilen bliebe der Absturzgrund weiterhin nur im Evidenz-Artefakt
        # (Codex-Fund auf PR #735).
        for entry in report.guard_results:
            if entry.get("exit_code") in (0, None) and entry.get("status") in ("ok", "unbekannt"):
                continue
            if not entry.get("log"):
                continue
            print(
                f"[waechter-log] phase={entry['phase']} "
                f"artefaktklasse={entry['artefaktklasse']}:\n{entry['log']}"
            )
    print(f"Smoke {'bestanden' if report.passed else 'FEHLGESCHLAGEN'}: {args.platform}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
