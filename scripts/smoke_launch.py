#!/usr/bin/env python3
"""Headless-Smoke-Launcher mit Fork-Bomb-Wächter für gebaute Artefakte (#307).

Startet ein gebautes Release-Bundle (macOS-``.app``-Binary oder Linux-AppImage)
headless – ``QT_QPA_PLATFORM=offscreen`` plus ``BGREMOVER_SMOKE_TEST=1`` lassen
die App nach dem ersten Event-Loop-Durchlauf mit Exit 0 beenden – und erzwingt
drei Invarianten, die nur am EINGEFRORENEN Artefakt sichtbar werden (der
Quell-Lauf in ``tests/test_app_smoke.py`` sieht sie nicht):

* **Start-Crash (#304):** Ein Exit-Code != 0 (z. B. fehlende ``*.dist-info``-
  Metadaten im Bundle) lässt den Launcher fehlschlagen.
* **Fork-Bomb (#305):** Ein Watchdog zählt laufende Prozesse, deren
  Kommandozeile *match_token* enthält. Übersteigt die Zahl gleichzeitig
  lebender Instanzen ``--max-instances``, schlägt der Launcher SOFORT fehl,
  statt auf das Timeout zu warten.
* **Hänger / Nicht-Terminieren:** Terminiert der Start nicht in ``--timeout``
  Sekunden, wird der komplette Prozessbaum hart beendet und der Launcher
  schlägt fehl – genau das Symptom der „endlos neue Fenster"-Fork-Bomb.

Exit 0 nur, wenn das Bundle sauber mit Exit 0 endet und nie mehr als
``--max-instances`` Instanzen gleichzeitig liefen. Der Watchdog nutzt nur die
Standardbibliothek und ``ps`` (Linux + macOS) – keine Fremdpakete.
"""
from __future__ import annotations

import argparse
import contextlib
import os
import signal
import subprocess
import sys
import time

# Smoke-Umgebung: offscreen-Qt (kein Display nötig) + Selbst-Quit nach dem
# ersten Event-Loop-Tick (Hook ``BGREMOVER_SMOKE_TEST`` in ``bgremover.app``).
_SMOKE_ENV = {"QT_QPA_PLATFORM": "offscreen", "BGREMOVER_SMOKE_TEST": "1"}


def _count_instances(match_token: str, exclude_pids: set[int]) -> int:
    """Zählt lebende Prozesse, deren Kommandozeile *match_token* enthält.

    Portabel über ``ps`` (Linux/macOS). *exclude_pids* klammert den eigenen
    Wächter-Prozess aus – dessen Kommandozeile enthält das Zielkommando (und
    damit den Token) als Argumente und würde sonst mitgezählt.
    """
    try:
        # ``-ww`` erzwingt unbegrenzte Zeilenbreite: ohne das kürzt ``ps`` die
        # Kommandozeile auf die Terminalbreite (bzw. ``$COLUMNS``) und der
        # match_token am Zeilenende (langer Bundle-Pfad) würde abgeschnitten und
        # nicht gefunden. ``-ww`` gilt für procps (Linux) wie BSD ps (macOS).
        completed = subprocess.run(
            ["ps", "-A", "-ww", "-o", "pid=", "-o", "command="],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return 0
    count = 0
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        pid_str, _, command = stripped.partition(" ")
        try:
            pid = int(pid_str)
        except ValueError:
            continue
        if pid in exclude_pids:
            continue
        if match_token in command:
            count += 1
    return count


def _terminate_tree(proc: subprocess.Popen[bytes]) -> None:
    """Beendet den gestarteten Prozess samt aller Kinder hart (Prozessgruppe)."""
    if proc.poll() is None:
        with contextlib.suppress(ProcessLookupError, OSError):
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    with contextlib.suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=10)


def _split_argv(argv: list[str]) -> tuple[list[str], list[str]]:
    """Trennt die eigenen Optionen vom Zielkommando am ersten ``--``."""
    if "--" in argv:
        index = argv.index("--")
        return argv[:index], argv[index + 1:]
    return argv, []


def run(
    command: list[str],
    *,
    match_token: str,
    timeout: float,
    max_instances: int,
    poll_interval: float = 0.25,
) -> int:
    """Startet *command* headless und überwacht es. Gibt 0 (ok) oder 1 (Fehler)."""
    env = {**os.environ, **_SMOKE_ENV}
    # Eigene Prozessgruppe (``start_new_session``): ein Fork-Bomb-Baum ist so als
    # Ganzes per ``killpg`` beendbar, statt verwaiste Kinder zu hinterlassen.
    proc = subprocess.Popen(command, env=env, start_new_session=True)
    exclude = {os.getpid()}
    peak = 0
    deadline = time.monotonic() + timeout
    failure: str | None = None
    try:
        while True:
            returncode = proc.poll()
            instances = _count_instances(match_token, exclude)
            peak = max(peak, instances)
            if instances > max_instances:
                failure = (
                    f"Fork-Bomb erkannt: {instances} gleichzeitige Instanzen von "
                    f"'{match_token}' (erlaubt: {max_instances})"
                )
                break
            if returncode is not None:
                if returncode != 0:
                    failure = f"Bundle endete mit Exit-Code {returncode} (Start-Crash?)"
                break
            if time.monotonic() > deadline:
                failure = (
                    f"Bundle terminierte nicht in {timeout:.0f}s "
                    "(Hänger oder Fork-Bomb?)"
                )
                break
            time.sleep(poll_interval)
    finally:
        _terminate_tree(proc)

    if failure is not None:
        print(f"smoke_launch FAIL: {failure} (peak Instanzen={peak})", file=sys.stderr)
        return 1
    print(
        f"smoke_launch OK: '{' '.join(command)}' sauber gestartet "
        f"(peak Instanzen={peak}, erlaubt={max_instances})"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    own_args, command = _split_argv(raw)
    parser = argparse.ArgumentParser(
        prog="smoke_launch.py",
        description="Headless-Smoke-Launch eines gebauten Artefakts mit Fork-Bomb-Wächter.",
    )
    parser.add_argument(
        "--match", required=True,
        help="Teilstring der Kommandozeile zum Zählen paralleler Instanzen.",
    )
    parser.add_argument(
        "--timeout", type=float, default=120.0,
        help="Maximale Startdauer in Sekunden (Default 120).",
    )
    parser.add_argument(
        "--max-instances", type=int, default=1,
        help="Erlaubte gleichzeitige Instanzen (Default 1; --ai-Build: höher).",
    )
    parser.add_argument(
        "--poll-interval", type=float, default=0.25,
        help="Abtastintervall des Wächters in Sekunden (Default 0.25).",
    )
    args = parser.parse_args(own_args)
    if not command:
        parser.error("kein Zielkommando nach '--' angegeben")
    return run(
        command,
        match_token=args.match,
        timeout=args.timeout,
        max_instances=args.max_instances,
        poll_interval=args.poll_interval,
    )


if __name__ == "__main__":
    raise SystemExit(main())
