#!/usr/bin/env python3
"""Eigenständiger Update-Check-Aufruf für ein *beliebiges* bgremover-Paket (#748).

Im Unterschied zum In-Prozess-Hook ``bgremover.update_check_probe``
(``BGREMOVER_UPDATE_CHECK_PROBE`` in ``bgremover.app.main``, nur in Artefakten
verfügbar, die den Hook bereits mitbauen – frühestens der nächste Kandidat
nach dessen Einführung) läuft dieses Skript UNTER DEM INTERPRETER DES ZU
PRÜFENDEN ARTEFAKTS selbst: Die Linux-AppImage bündelt eine vollständige,
eigenständige CPython-Installation samt echtem ``bgremover``-Paket in ihrem
Site-Packages (``packaging/linux/build_appimage.sh``, python-appimage).
``bgremover.app_update``/``bgremover._version`` existieren dort unverändert
bereits seit Epic #563 (deutlich vor #748) – dieses Skript importiert
ausschließlich diese beiden Module (kein Qt, kein neuerer Hook) und
funktioniert damit retroaktiv gegen jedes bereits veröffentlichte
Release-Artefakt. Das ist der "echte Vorgänger"-Nachweis, den #748 verlangt.

Aufruf: den mit ``--appimage-extract`` entpackten AppImage-Interpreter direkt
verwenden, z. B. ``squashfs-root/usr/bin/python3.12 update_probe_cli.py
--output evidenz.json``. Muss mit einem Arbeitsverzeichnis AUSSERHALB des
Source-Checkouts laufen (siehe ``scripts/abnahme_smoke.neutral_workdir``):
sonst beschattet das lokale ``bgremover/``-Verzeichnis das des geprüften
Interpreters (#740 – derselbe Fund wie beim App-Start selbst).

Für die PyInstaller-gebündelte macOS-.app existiert kein vergleichbarer
Weg: PyInstaller bettet Python-Bytecode in ein Archiv im Bootloader ein,
statt einen eigenständig aufrufbaren Interpreter mit normalem Site-Packages
bereitzustellen. macOS nutzt deshalb seit #917 den In-Prozess-Hook
``BGREMOVER_UPDATE_CHECK_PROBE`` (``bgremover.update_check_probe``), verdrahtet
in ``abnahme_smoke._update_check_macos_probe``. Das setzt einen Vorgänger
voraus, der den Hook schon mitbringt – also mindestens v2.7.3.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Ziel-JSON-Pfad.")
    args = parser.parse_args(argv)

    # Bewusst erst hier importiert: der Interpreter, unter dem dieses Skript
    # läuft, bestimmt, WELCHES bgremover-Paket (welche Version) geprüft wird.
    from bgremover._version import get_version
    from bgremover.app_update import UpdateStatus, check_for_update

    current_version = get_version()
    result = check_for_update(current_version)
    payload = {
        "schema": 1,
        "kind": "abnahme-update-check-probe",
        "erzeugt_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "current_version": current_version,
        "status": result.status.name,
        "latest_version": result.latest_version,
        "release_url": result.release_url,
        "error": result.error,
        "interpreter": sys.executable,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    message = f"Update-Check: Version {current_version!r} -> {result.status.name}"
    if result.latest_version:
        message += f" (neueste: {result.latest_version!r})"
    if result.error:
        message += f" Fehler: {result.error}"
    print(message)
    return 0 if result.status is not UpdateStatus.CHECK_FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
