#!/usr/bin/env python3
"""Runner-Readiness-Preflight der Release-Abnahme (#915, Epic #914).

Läuft als eigener, schneller Job auf dem Self-hosted Runner, *bevor* die
schweren Abnahme-Jobs starten: prüft die realen Einsatzvoraussetzungen aus
``docs/RELEASE_AUTOMATION.md`` §1–§2.1 und meldet **alle** Verstöße gesammelt
als ``::error``-Annotationen, statt beim ersten abzubrechen.

Bewusst nur Standardbibliothek: ein echter Qt-Aufruf bräuchte das
PyQt6-venv (Minuten statt Sekunden). Der GL-Ladetest plus Session-Prüfung
deckt die real beobachteten Ausfallmodi ab (headless gestarteter Dienst,
fehlende GL-Bibliotheken); die vollständige Qt-/GL-Probe bleibt Teil der
Plattform-Jobs (``abnahme_probe.py``) und wird hier nicht ersetzt.

Der zugehörige Queue-Watchdog (``abnahme_watchdog.py``) bricht den Lauf ab,
wenn dieser Preflight mangels Online-Runner gar nicht erst startet.
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import getpass
import os
import plistlib
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Protocol

MIN_PYTHON = (3, 10)
MIN_FREE_GB = 2.0
NETWORK_TIMEOUT_S = 10.0
MACOS_PLATFORM = "macos-arm64"
KNOWN_PLATFORMS = (MACOS_PLATFORM, "linux-arm64", "linux-x86_64")
MACOS_OPENGL_FRAMEWORK = Path("/System/Library/Frameworks/OpenGL.framework")
# Repräsentative Kommandos des eng begrenzten sudo für den .deb-Zyklus
# (RELEASE_AUTOMATION §3): geprüft wird nur die Berechtigung (``sudo -l``),
# ausgeführt wird nichts.
DEB_SUDO_CHECKS = (("apt-get", ("install", "bgremover")), ("dpkg", ("-r", "bgremover")))

# ── Geraete-Haertung (#921) ────────────────────────────────────────────
# Zwei Befunde aus den offiziellen Runner-Vorlagen (actions/runner, main):
# ``actions.runner.service.template`` enthaelt **kein** ``Restart=`` und
# ``actions.runner.plist.template`` **kein** ``KeepAlive`` – ein abgestuerzter
# Runner-Dienst bleibt also auf beiden Plattformen unten, bis jemand ihn von
# Hand startet. Und auf einem schlafenden Mac nimmt der Runner gar keine Jobs
# an. Beides senkt die Verfuegbarkeit zwischen den Laeufen, ohne dass es im
# Lauf selbst je auffiele; RELEASE_AUTOMATION §2.1/§2.2 beschreibt die
# Gegenmittel, diese Pruefungen belegen sie.
LAUNCHAGENT_GLOB = "Library/LaunchAgents/actions.runner.*.plist"
SYSTEMD_UNIT_PATTERN = "actions.runner.*.service"
ACCEPTED_SYSTEMD_RESTART = ("always", "on-failure", "on-abnormal")
# ``pmset -g custom`` gliedert nach Stromquelle; nur der Netzbetrieb zaehlt –
# ein Abnahme-Runner haengt am Netzteil (RELEASE_AUTOMATION §2.1).
_PMSET_AC_HEADING = re.compile(r"(?m)^AC Power:")
_PMSET_SOURCE_HEADING = re.compile(r"(?m)^[A-Z][A-Za-z ]*:\s*$")
_PMSET_SETTING = re.compile(r"(?m)^\s*(\w+)\s+(-?\d+)\s*$")
# Eine aktive caffeinate-Assertion ist die dokumentierte Alternative zum
# pmset-Profil; beide verhindern denselben Zustand.
_ASSERTION_LINE = re.compile(r"(?m)^\s*(\w+)\s+(\d+)\s*$")
SLEEP_ASSERTIONS = ("PreventUserIdleSystemSleep", "PreventUserIdleDisplaySleep")


def check_python() -> str | None:
    """Python-Mindestversion des System-Interpreters (venv-Basis der Jobs)."""
    if sys.version_info[:2] >= MIN_PYTHON:
        return None
    found = ".".join(str(part) for part in sys.version_info[:3])
    wanted = ".".join(str(part) for part in MIN_PYTHON)
    return f"Python {found} ist zu alt (mindestens {wanted})."


def check_venv() -> str | None:
    """venv + ensurepip verfügbar (Debian/Pi braucht dafür ``python3-venv``)."""
    import importlib.util as _importlib_util

    missing = [
        name for name in ("venv", "ensurepip") if _importlib_util.find_spec(name) is None
    ]
    if not missing:
        return None
    return (
        f"Python-Module fehlen: {', '.join(missing)} "
        "(Debian/Raspberry Pi: Paket python3-venv installieren)."
    )


class DiskUsage(Protocol):
    """Strukturvertrag für ``shutil.disk_usage``-artige Ergebnisse."""

    @property
    def free(self) -> int: ...


def check_disk(
    path: Path,
    min_free_gb: float = MIN_FREE_GB,
    *,
    usage: Callable[[Path], DiskUsage] = shutil.disk_usage,
) -> str | None:
    """Freier Speicher im Runner-Arbeitsverzeichnis (Artefakte ≥ 2 GB)."""
    free_gb = usage(path).free / 1024**3
    if free_gb >= min_free_gb:
        return None
    return (
        f"Nur {free_gb:.1f} GB frei unter {path} "
        f"(mindestens {min_free_gb:.0f} GB für die Release-Artefakte nötig)."
    )


def _console_user() -> str:
    """Angemeldeter macOS-Konsolenbenutzer (Besitzer von /dev/console)."""
    result = subprocess.run(
        ["stat", "-f", "%Su", "/dev/console"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def check_graphical_session(
    platform: str,
    env: Mapping[str, str],
    *,
    console_user: Callable[[], str] = _console_user,
    current_user: Callable[[], str] = getpass.getuser,
) -> str | None:
    """Grafische Sitzung erreichbar – dieselbe Regel wie das In-Job-Gate.

    macOS: Runner-Benutzer muss der angemeldete Konsolenbenutzer sein
    (LaunchAgent in dessen GUI-Sitzung). Linux: ``DISPLAY`` oder
    ``WAYLAND_DISPLAY`` muss gesetzt sein, Wayland zusätzlich
    ``XDG_RUNTIME_DIR`` (RELEASE_AUTOMATION §2.1).
    """
    if platform == MACOS_PLATFORM:
        try:
            console = console_user()
        except (OSError, subprocess.SubprocessError) as exc:
            return f"Konsolenbenutzer nicht ermittelbar ({exc})."
        runner = current_user()
        if runner != console:
            return (
                f"Runner-Benutzer {runner!r} ist nicht der angemeldete "
                f"Konsolenbenutzer {console!r} (LaunchAgent-Einrichtung prüfen)."
            )
        return None
    if not env.get("DISPLAY") and not env.get("WAYLAND_DISPLAY"):
        return (
            "Weder DISPLAY noch WAYLAND_DISPLAY ist gesetzt – der Runner-Dienst "
            "läuft nicht in der angemeldeten grafischen Sitzung."
        )
    if env.get("WAYLAND_DISPLAY") and not env.get("XDG_RUNTIME_DIR"):
        return "WAYLAND_DISPLAY ist gesetzt, aber XDG_RUNTIME_DIR fehlt."
    return None


def check_gl(
    platform: str,
    *,
    find_library: Callable[[str], str | None] = ctypes.util.find_library,
    load_library: Callable[[str], object] = ctypes.CDLL,
    macos_framework: Path = MACOS_OPENGL_FRAMEWORK,
) -> str | None:
    """GL-Bibliothek ladbar (schneller Ersatz für eine volle Qt-Probe).

    Fängt den real beobachteten Fehlermodus ``libGL.so.1: cannot open shared
    object file`` ab, ohne PyQt6 zu installieren. Ob der Kontext hardware-
    beschleunigt ist, entscheidet weiterhin die GL-Provenance im Plattform-Job.
    """
    if platform == MACOS_PLATFORM:
        if macos_framework.exists():
            return None
        return f"OpenGL-Framework fehlt unter {macos_framework}."
    candidate = find_library("GL") or "libGL.so.1"
    try:
        load_library(candidate)
    except OSError as exc:
        return (
            f"GL-Bibliothek {candidate!r} nicht ladbar ({exc}) – "
            "Qt-Systembibliotheken der Desktop-Session prüfen."
        )
    return None


def check_network(
    api_url: str,
    *,
    timeout: float = NETWORK_TIMEOUT_S,
    opener: Callable[..., object] = urllib.request.urlopen,
) -> str | None:
    """GitHub-API erreichbar; jede HTTP-Antwort zählt (Statuscode egal)."""
    request = urllib.request.Request(
        api_url, headers={"User-Agent": "bgremover-abnahme-preflight"},
    )
    try:
        response = opener(request, timeout=timeout)
    except urllib.error.HTTPError:
        return None
    except OSError as exc:
        return f"{api_url} nicht erreichbar ({exc})."
    close = getattr(response, "close", None)
    if callable(close):
        close()
    return None


def check_deb_sudo(
    *,
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str | None:
    """Eng begrenztes sudo für den .deb-Zyklus vorhanden (nur Berechtigungsprüfung)."""
    sudo = which("sudo")
    if sudo is None:
        return "sudo ist nicht installiert (für den .deb-Smoke nötig, RELEASE_AUTOMATION §3)."
    problems: list[str] = []
    for command, args in DEB_SUDO_CHECKS:
        path = which(command)
        if path is None:
            problems.append(f"{command} nicht im PATH")
            continue
        probe = runner(
            [sudo, "-n", "-l", path, *args], capture_output=True, text=True, check=False,
        )
        if probe.returncode != 0:
            problems.append(f"sudo -n -l {path} {' '.join(args)} verweigert")
    if not problems:
        return None
    return (
        f"{'; '.join(problems)} – eng begrenztes NOPASSWD-sudo gemäß "
        "RELEASE_AUTOMATION §3 einrichten."
    )


# ── Geraete-Haertung: Sleep-Schutz und Dienst-Neustartpolicy (#921) ────


def parse_pmset_ac(text: str) -> dict[str, int]:
    """Liest den ``AC Power``-Block aus ``pmset -g custom``.

    Bewusst nur dieser Block: ``pmset -g custom`` listet Netz- und
    Akkubetrieb getrennt, und ein Abnahme-Runner arbeitet am Netzteil. Die
    Akkuwerte duerfen die Bewertung nicht verfaelschen – weder positiv noch
    negativ.
    """
    match = _PMSET_AC_HEADING.search(text)
    if match is None:
        return {}
    rest = text[match.end():]
    following = _PMSET_SOURCE_HEADING.search(rest)
    block = rest[: following.start()] if following is not None else rest
    return {key: int(value) for key, value in _PMSET_SETTING.findall(block)}


def parse_pmset_assertions(text: str) -> dict[str, int]:
    """Liest die systemweiten Assertions aus ``pmset -g assertions``."""
    head, _, _ = text.partition("Listed by owning process")
    return {key: int(value) for key, value in _ASSERTION_LINE.findall(head)}


def check_macos_sleep(
    *, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str | None:
    """Der Mac darf waehrend der Abnahme-Bereitschaft nicht einschlafen.

    Ein schlafender Runner nimmt keine Jobs an – genau der Zustand, den der
    Heartbeat (#921) taeglich sucht. Akzeptiert werden beide dokumentierten
    Wege: das dauerhafte ``pmset``-Profil (``sleep``/``displaysleep`` am Netz
    auf 0) oder eine aktive ``caffeinate``-Assertion. Der Display-Schlaf
    zaehlt mit, weil die Abnahme native Screenshots erzeugt.
    """
    try:
        custom = runner(
            ["pmset", "-g", "custom"], capture_output=True, text=True, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"pmset nicht ausfuehrbar ({exc})."
    if custom.returncode != 0:
        return f"pmset -g custom fehlgeschlagen (Exit {custom.returncode})."
    settings = parse_pmset_ac(custom.stdout or "")
    if not settings:
        return "pmset -g custom liefert keinen AC-Power-Block – Ausgabe unerwartet."
    awake = [name for name in ("sleep", "displaysleep") if settings.get(name, 1) != 0]
    if not awake:
        return None
    try:
        assertions = runner(
            ["pmset", "-g", "assertions"], capture_output=True, text=True, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        assertions = subprocess.CompletedProcess(["pmset"], 1, stdout="")
    active = parse_pmset_assertions(assertions.stdout or "")
    if all(active.get(name) == 1 for name in SLEEP_ASSERTIONS):
        return None
    values = ", ".join(f"{name}={settings.get(name)}" for name in awake)
    return (
        f"Ruhezustand am Netz nicht abgeschaltet ({values}) und keine aktive "
        "caffeinate-Assertion. Ein schlafender Mac nimmt keine Jobs an – "
        "RELEASE_AUTOMATION §2.1."
    )


def check_launchagent_keepalive(
    *, home: Path | None = None, agents: Callable[[Path], Iterable[Path]] | None = None,
) -> str | None:
    """LaunchAgent startet den Runner nach einem Absturz neu.

    Die offizielle Vorlage (``actions.runner.plist.template``) setzt nur
    ``RunAtLoad``; ohne ``KeepAlive`` bleibt ein abgestuerzter Runner unten,
    bis sich jemand am Geraet anmeldet.
    """
    root = home if home is not None else Path.home()
    found = list(agents(root) if agents is not None else root.glob(LAUNCHAGENT_GLOB))
    if not found:
        return (
            f"Kein Runner-LaunchAgent unter ~/{LAUNCHAGENT_GLOB} gefunden – "
            "Dienst als angemeldeter Runner-Benutzer einrichten (§2.1)."
        )
    without = []
    for path in sorted(found):
        try:
            with path.open("rb") as handle:
                plist = plistlib.load(handle)
        except (OSError, ValueError) as exc:
            return f"LaunchAgent {path.name} nicht lesbar ({exc})."
        if not plist.get("KeepAlive"):
            without.append(path.name)
    if not without:
        return None
    return (
        f"LaunchAgent ohne KeepAlive: {', '.join(without)} – ein abgestuerzter "
        "Runner-Dienst startet nicht von selbst neu (RELEASE_AUTOMATION §2.1)."
    )


def check_systemd_restart(
    *, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str | None:
    """systemd startet den Runner-Dienst nach einem Absturz neu.

    Die offizielle Unit-Vorlage (``actions.runner.service.template``) enthaelt
    kein ``Restart=``; das Gegenmittel ist ein Drop-in per ``systemctl edit``
    (RELEASE_AUTOMATION §2.2), damit es ein ``svc.sh install`` ueberlebt.
    """
    try:
        listing = runner(
            ["systemctl", "list-units", "--type=service", "--all", "--no-legend",
             SYSTEMD_UNIT_PATTERN],
            capture_output=True, text=True, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"systemctl nicht ausfuehrbar ({exc})."
    units = [
        line.split()[0].lstrip("\u25cf ")
        for line in (listing.stdout or "").splitlines()
        if line.strip()
    ]
    units = [unit for unit in units if unit.endswith(".service")]
    if not units:
        return (
            "Kein actions.runner-*.service gefunden – Runner-Dienst per "
            "`sudo ./svc.sh install` einrichten (RELEASE_AUTOMATION §2)."
        )
    weak = []
    for unit in sorted(set(units)):
        probe = runner(
            ["systemctl", "show", unit, "-p", "Restart", "--value"],
            capture_output=True, text=True, check=False,
        )
        policy = (probe.stdout or "").strip()
        if policy not in ACCEPTED_SYSTEMD_RESTART:
            weak.append(f"{unit}: Restart={policy or 'no'}")
    if not weak:
        return None
    return (
        f"Dienst ohne Neustart-Policy ({'; '.join(weak)}) – Drop-in mit "
        "Restart=always anlegen (RELEASE_AUTOMATION §2.2)."
    )


def run_hardening(platform: str) -> list[tuple[str, str | None]]:
    """Geraete-Haertung je Plattform (#921).

    Getrennt von ``run_preflight``: Diese Punkte entscheiden ueber die
    Verfuegbarkeit **zwischen** den Laeufen, nicht ueber die Gueltigkeit
    eines laufenden Nachweises. Im Abnahme-Preflight sind sie deshalb
    Hinweise (ein Release soll nicht an einer Display-Sleep-Einstellung
    scheitern), im taeglichen Heartbeat dagegen bindend.
    """
    if platform == MACOS_PLATFORM:
        return [
            ("sleep-schutz", check_macos_sleep()),
            ("dienst-neustart", check_launchagent_keepalive()),
        ]
    return [("dienst-neustart", check_systemd_restart())]


def default_api_url(env: Mapping[str, str] = os.environ) -> str:
    return env.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")


def run_preflight(
    platform: str, *, min_free_gb: float = MIN_FREE_GB,
) -> list[tuple[str, str | None]]:
    """Alle Checks der Plattform ausführen; je Check ``(name, fehler-oder-None)``."""
    checks: list[tuple[str, str | None]] = [
        ("python", check_python()),
        ("venv", check_venv()),
        ("speicher", check_disk(Path.cwd(), min_free_gb)),
        ("session", check_graphical_session(platform, os.environ)),
        ("gl", check_gl(platform)),
        ("netz", check_network(default_api_url())),
    ]
    if platform != MACOS_PLATFORM:
        checks.append(("deb-sudo", check_deb_sudo()))
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=KNOWN_PLATFORMS)
    parser.add_argument("--min-free-gb", type=float, default=MIN_FREE_GB)
    parser.add_argument(
        "--hardening-strict",
        action="store_true",
        help=(
            "Geraete-Haertung (#921) als harten Fehler werten – so laeuft der "
            "taegliche Heartbeat. Im Abnahme-Preflight bleibt sie ein Hinweis."
        ),
    )
    args = parser.parse_args(argv)

    failures = 0
    for name, error in run_preflight(args.platform, min_free_gb=args.min_free_gb):
        if error is None:
            print(f"[preflight] ok: {name}")
        else:
            failures += 1
            print(f"::error title=Preflight {args.platform}::{name}: {error}")
    for name, error in run_hardening(args.platform):
        if error is None:
            print(f"[haertung] ok: {name}")
        elif args.hardening_strict:
            failures += 1
            print(f"::error title=Haertung {args.platform}::{name}: {error}")
        else:
            print(f"::warning title=Haertung {args.platform}::{name}: {error}")
    if failures:
        print(
            f"::error title=Preflight {args.platform}::{failures} Prüfung(en) "
            "fehlgeschlagen – Runner ist nicht einsatzbereit. Abhilfe: "
            "docs/RELEASE_AUTOMATION.md §2/§6; danach die Abnahme mit "
            "unveränderten Eingaben neu dispatchen (reiner Runnerfehler)."
        )
        return 1
    print(f"[preflight] {args.platform}: Runner ist einsatzbereit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
