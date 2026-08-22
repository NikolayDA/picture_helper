"""Pytest-Plugin für den ``gl_smoke``-Governance-Test (#832, #845-Review).

Schreibt während der Kollektion je Testdatei die Marker aller Testfunktionen
als JSON (Pfad -> {Funktionsname -> [Markernamen]}) in die über die
Umgebungsvariable ``BGREMOVER_MARKER_COLLECT_JSON`` benannte Datei. Der Governance-Test
lädt es per ``-p tests._marker_collect_plugin`` in einen
Kollektions-Subprozess (Paketname - ``cwd`` = Repo-Wurzel genügt, kein
``PYTHONPATH``-Eingriff) und
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

import pytest


# ``trylast``: erst nach den anderen Implementierungen dieses Hooks laufen
# (u. a. dem eingebauten ``mark``-Plugin, das den ``-m``-Filter deselektiert,
# und möglichen ``conftest``-Hooks, die Marker nachträglich setzen) – die
# Inventur liest damit garantiert den Endstand.
@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items) -> None:
    target = os.environ.get("BGREMOVER_MARKER_COLLECT_JSON")
    if not target:  # ohne Zielpfad still wirkungslos (versehentlich geladen)
        return
    out: dict[str, dict[str, list[str]]] = {}
    for item in items:
        file_path = item.nodeid.split("::", 1)[0]
        # Node-ID ohne Datei-Präfix und ohne ``[...]``-Parametrisierung:
        # dedupliziert parametrisierte Varianten (Marker werden vereinigt),
        # hält aber gleichnamige Tests aus verschiedenen Klassen auseinander
        # (``originalname`` würde sie zu einem Eintrag verschmelzen).
        rest = item.nodeid.split("::", 1)[1] if "::" in item.nodeid else item.name
        name = rest.split("[", 1)[0]
        markers = {m.name for m in item.iter_markers()}
        per_file = out.setdefault(file_path, {})
        per_file[name] = sorted(set(per_file.get(name, [])) | markers)
    with open(target, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
