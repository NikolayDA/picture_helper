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
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path

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


def check_disk(
    path: Path,
    min_free_gb: float = MIN_FREE_GB,
    *,
    usage: Callable[[Path], object] = shutil.disk_usage,
) -> str | None:
    """Freier Speicher im Runner-Arbeitsverzeichnis (Artefakte ≥ 2 GB)."""
    free_bytes = int(getattr(usage(path), "free", 0))
    free_gb = free_bytes / 1024**3
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
    args = parser.parse_args(argv)

    failures = 0
    for name, error in run_preflight(args.platform, min_free_gb=args.min_free_gb):
        if error is None:
            print(f"[preflight] ok: {name}")
        else:
            failures += 1
            print(f"::error title=Preflight {args.platform}::{name}: {error}")
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
