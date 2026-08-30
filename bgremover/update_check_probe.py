"""Update-Check-Automationshook des gepackten Artefakts (#748).

``bgremover.app_update.check_for_update`` ist bereits Qt-frei und wird von der
UI nur interaktiv angestoßen (Extras-Menü, optionaler Start-Check). Für die
Release-Abnahme braucht es einen headless auslösbaren, strukturiert
protokollierenden Aufruf desselben echten Netzwerk-Roundtrips – analog zu
``bgremover.acceptance_smoke``/``bgremover.screenshot3d``, aber ohne jeden
Qt-Bezug (kein Fenster, kein Event-Loop-Tick nötig).

Aktiviert über ``BGREMOVER_UPDATE_CHECK_PROBE`` (Ziel-JSON-Pfad) in
``bgremover.app.main``, dort noch **vor** ``QApplication`` geprüft (wie
``BGREMOVER_AI_SELFCHECK``).

Wichtig für #748: Dieser Hook existiert erst ab dem Kandidaten, der ihn zuerst
mitbaut – er kann keine bereits veröffentlichten Artefakte rückwirkend
erreichen. Der Vorgänger-Nachweis (echtes älteres Artefakt meldet
``UPDATE_AVAILABLE``) läuft für Linux stattdessen über
``scripts/update_probe_cli.py`` direkt mit dem im Artefakt gebündelten
Interpreter (siehe dortige Modul-Dokumentation). Für die PyInstaller-gebündelte
macOS-.app existiert kein vergleichbarer Weg – dort trägt seit #917 genau
dieser Hook den Vorgängernachweis (``UPDATE-MACOS-ARM-01``), was einen
Vorgänger ab v2.7.3 voraussetzt.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from bgremover._version import get_version
from bgremover.app_update import UpdateStatus, check_for_update

# Schema 1: erster Entwurf. Bei inhaltlichen Änderungen der Nutzlast anheben,
# damit ein Aufrufer mit fest verdrahteten Erwartungen das nicht stillschweigend
# übersieht (Muster aus ``bgremover.acceptance_smoke._EVIDENCE_SCHEMA``).
EVIDENCE_SCHEMA = 1
EVIDENCE_KIND = "abnahme-update-check-probe"


def run_update_check_probe(output_json: Path) -> tuple[bool, str]:
    """Führt den echten Update-Check aus und schreibt strukturierte Evidenz.

    ``ok`` meldet ausschließlich, ob der Netzwerk-Roundtrip ein bestimmbares
    Ergebnis lieferte (``UP_TO_DATE``/``UPDATE_AVAILABLE`` statt
    ``CHECK_FAILED``) – **nicht**, ob dieses Ergebnis zum je nach geprüftem
    Artefakt (Vorgänger vs. aktueller Kandidat) erwarteten Status passt. Diese
    Entscheidung trifft der Aufrufer anhand der geschriebenen ``status``-/
    ``latest_version``-Felder, weil dieser Hook selbst nicht weiß, welche
    Rolle das gerade laufende Artefakt in der Abnahme spielt.
    """
    current_version = get_version()
    result = check_for_update(current_version)
    payload = {
        "schema": EVIDENCE_SCHEMA,
        "kind": EVIDENCE_KIND,
        "erzeugt_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "current_version": current_version,
        "status": result.status.name,
        "latest_version": result.latest_version,
        "release_url": result.release_url,
        "error": result.error,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    ok = result.status is not UpdateStatus.CHECK_FAILED
    message = f"Update-Check: Version {current_version!r} -> {result.status.name}"
    if result.latest_version:
        message += f" (neueste: {result.latest_version!r})"
    if result.error:
        message += f" Fehler: {result.error}"
    return ok, message
