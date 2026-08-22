"""Pytest-Plugin für den ``gl_smoke``-Governance-Test (#832, #845-Review).

Schreibt während der Kollektion je Testdatei die Marker aller Testfunktionen
als JSON (Pfad -> {Funktionsname -> [Markernamen]}) in die über die
Umgebungsvariable ``MARKER_COLLECT_JSON`` benannte Datei. Der Governance-Test
lädt es per ``-p _marker_collect_plugin`` in einen Kollektions-Subprozess und
liest die Marker damit über die öffentliche Hook-/Item-API statt über das
Terminal-Ausgabeformat von ``--collect-only`` – das Parsing samt seiner
Verbosity-/Warnings-Choreografie entfällt vollständig.

Der Unterstrich-Präfix hält die Datei aus der normalen Testkollektion
(``test_*.py``) heraus; sie wirkt nur, wenn sie explizit als Plugin geladen
wird.
"""
from __future__ import annotations

import json
import os


def pytest_collection_modifyitems(items) -> None:
    out: dict[str, dict[str, list[str]]] = {}
    for item in items:
        file_path = item.nodeid.split("::", 1)[0]
        # ``originalname`` ist der unparametrisierte Funktionsname (ohne
        # ``[...]``-Suffix); Items ohne dieses Attribut fallen auf ``name``
        # zurück. Parametrisierte Varianten teilen sich den Funktionsnamen -
        # ihre Marker werden vereinigt statt überschrieben.
        name = getattr(item, "originalname", None) or item.name
        markers = {m.name for m in item.iter_markers()}
        per_file = out.setdefault(file_path, {})
        per_file[name] = sorted(set(per_file.get(name, [])) | markers)
    target = os.environ.get("MARKER_COLLECT_JSON")
    if not target:  # ohne Zielpfad still wirkungslos (versehentlich geladen)
        return
    with open(target, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
