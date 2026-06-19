#!/usr/bin/env python3
"""Leitet die GitHub-Release-Notes einer Version aus CHANGELOG.md ab (#311).

Der ``publish``-Job in ``release-linux.yml`` füllte den Release-Body früher mit
einem fest verdrahteten ``Automated build…``-Satz; die echten, nutzersichtbaren
Notizen standen nur in ``CHANGELOG.md`` und mussten von Hand nachgetragen werden
(für v2.4.1 vergessen → die drei kritischen macOS-Fixes blieben auf der
Releases-Seite unsichtbar). Dieses Skript extrahiert den ``## [X.Y.Z]``-Abschnitt
bis zur nächsten ``## [``-Überschrift, sodass der Workflow ihn via
``--notes-file`` an ``gh release create``/``gh release edit`` übergeben kann.

Fehlt der Abschnitt zur gefragten Version, bricht das Skript mit Exit 2 ab –
kein stiller generischer Fallback (Akzeptanzkriterium #311). Nur Standard-
bibliothek, damit es im Release-Runner ohne Zusatzpakete läuft.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_DEFAULT_CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"


def extract_release_notes(changelog: str, version: str) -> str:
    """Gibt den Notizen-Block der *version* aus *changelog* zurück (ohne Überschrift).

    Sucht die Überschrift ``## [<version>]`` (optional gefolgt von Datum o. Ä.)
    und liefert alles bis zur nächsten ``## [``-Überschrift bzw. zum Dateiende,
    an den Rändern getrimmt. Wirft ``KeyError(version)``, wenn der Abschnitt
    fehlt oder leer ist.
    """
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\][^\n]*\n(?P<body>.*?)(?=^## \[|\Z)",
        re.M | re.S,
    )
    match = pattern.search(changelog)
    if match is None:
        raise KeyError(version)
    body = match.group("body").strip()
    if not body:
        raise KeyError(version)
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Version, mit oder ohne führendes 'v' (z. B. 2.4.1)")
    parser.add_argument(
        "--changelog",
        type=Path,
        default=_DEFAULT_CHANGELOG,
        help="Pfad zur CHANGELOG.md (Default: Repo-Wurzel)",
    )
    args = parser.parse_args(argv)
    version = args.version.lstrip("v")
    text = args.changelog.read_text(encoding="utf-8")
    try:
        notes = extract_release_notes(text, version)
    except KeyError:
        print(
            f"::error::Kein '## [{version}]'-Abschnitt in {args.changelog} – "
            f"Release-Notes können nicht abgeleitet werden (#311).",
            file=sys.stderr,
        )
        return 2
    print(notes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
