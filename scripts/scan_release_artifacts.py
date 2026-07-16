#!/usr/bin/env python3
"""Sekret-/Entwicklerpfad-Scan für gebaute Release-Artefakte (#584).

Liest jede Datei in einem Verzeichnis (z. B. ``dist/``) binär und prüft sie auf
hochkonfidente Geheimnis-Muster (AWS-Keys, GitHub-Tokens, private PEM-Schlüssel).
Ein Treffer beendet den Scan mit Exit 1 und einer ``::error::``-Annotation, damit
der Release-Build fehlschlägt, statt ein kompromittiertes Artefakt hochzuladen.

Absolute Pfade unter ``/home/<user>`` bzw. ``/Users/<user>`` werden separat
gemeldet, aber nicht hart durchgesetzt: gebaute Wheels/Bundles enthalten
erwartungsgemäß den CI-Benutzernamen (``runner``/``root``); ein davon
abweichender Benutzername deutet auf einen versehentlich eingebetteten
Pfad einer echten Entwicklermaschine hin und wird als Hinweis ausgegeben.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_SECRET_PATTERNS: dict[str, re.Pattern[bytes]] = {
    "AWS Access Key ID": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "GitHub-Token": re.compile(rb"gh[oprsu]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,}"),
    "privater PEM-Schlüssel": re.compile(
        rb"-----BEGIN (RSA |EC |OPENSSH |DSA |ENCRYPTED |)PRIVATE KEY-----"
    ),
    "Slack-Token": re.compile(rb"xox[baprs]-[0-9A-Za-z-]{10,}"),
}
_DEV_PATH = re.compile(rb"/(?:home|Users)/([A-Za-z0-9_.-]+)/")
_KNOWN_CI_USERS = {"runner", "root"}


def scan_file(path: Path) -> tuple[list[str], set[str]]:
    """Prüft eine Datei; liefert (Geheimnis-Treffer, unbekannte Pfad-Benutzer)."""
    data = path.read_bytes()
    findings = []
    for label, pattern in _SECRET_PATTERNS.items():
        match = pattern.search(data)
        if match:
            findings.append(f"{label}: {match.group(0)[:40]!r}")
    users = {
        m.group(1).decode("ascii", errors="replace") for m in _DEV_PATH.finditer(data)
    }
    return findings, users - _KNOWN_CI_USERS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="dist", help="zu scannendes Verzeichnis")
    args = parser.parse_args(argv)

    directory = Path(args.directory)
    files = sorted(p for p in directory.iterdir() if p.is_file())
    if not files:
        print(f"::error::Keine Dateien in {directory} gefunden.")
        return 1

    failed = False
    for path in files:
        size_mb = path.stat().st_size / 1_000_000
        print(f">> Scanne {path.name} ({size_mb:.1f} MB)")
        findings, unknown_users = scan_file(path)
        for finding in findings:
            print(f"::error::{path.name}: möglicher Fund – {finding}")
            failed = True
        if unknown_users:
            print(f"   Hinweis: unbekannte Pfad-Benutzer in {path.name}: {sorted(unknown_users)}")
        else:
            print("   OK: keine Entwicklerpfade außerhalb runner/root gefunden")

    if failed:
        print("::error::Secret-Scan fehlgeschlagen – siehe obige Funde.")
        return 1
    print(">> Secret-/Pfad-Scan (#584): keine hochkonfidenten Funde in allen Artefakten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
