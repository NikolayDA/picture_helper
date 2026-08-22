"""Drift-Schutz für die ``gl_smoke``-Markerangaben in ``TESTING.md`` (#832).

``TESTING.md`` zählt die ``gl_smoke``-markierten Testdateien samt
Granularität (modulweit vs. Einzeldekorator) von Hand auf; #826 zeigte, dass
so eine Liste unbemerkt unvollständig wird. Analog zu
``test_ci_qt_packages.py`` (Befund N6) hält dieser Test Doku und Bestand
synchron: pytest sammelt die Marker selbst – über die Hook-API des
Mini-Plugins ``tests/_marker_collect_plugin.py``, nicht über das
Terminal-Ausgabeformat von ``--collect-only``.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from functools import cache
from pathlib import Path
from typing import NamedTuple

import pytest

ROOT = Path(__file__).resolve().parent.parent
TESTING_MD = ROOT / "TESTING.md"

# Die Klammer identifiziert sich über ihren Inhalt („modulweit nur in")
# statt als erste Klammer nach dem Anker - ein später eingeschobener
# Klammer-Einschub im selben Satz würde den Capture sonst still verschieben.
# ``[^()]`` verhindert zusätzlich, dass der Match über eine geschachtelte
# Klammer hinweg in einen späteren Absatz rutscht (TESTING.md nennt
# „modulweit" weiter unten erneut in einer Klammer).
_GL_SMOKE_FILE_LIST_RE = re.compile(
    r"Ein weiterer Marker, `gl_smoke`.*?\(([^()]*modulweit nur in[^()]*)\)",
    re.DOTALL,
)
# Nur Backtick-umschlossene Pfade; das ``tests/``-Präfix ist in beiden
# Regexes optional, damit eine redaktionelle Vereinheitlichung in beide
# Richtungen keinen Fehlalarm auslöst - normalisiert wird auf
# ``tests/<name>``.
_TEST_FILE_RE = re.compile(r"`(?:tests/)?(test_\w+\.py)`")
_MODULE_WIDE_RE = re.compile(r"modulweit nur in\s*`(?:tests/)?(test_\w+\.py)`")


class _DocumentedGlSmoke(NamedTuple):
    """Beide TESTING.md-Aussagen aus derselben Klammer."""

    files: frozenset[str]
    module_wide: frozenset[str]


def _tail(text: str, limit: int = 2000) -> str:
    """Kürzt lange Kind-Ausgaben in Fehlermeldungen auf das lesbare Ende
    (die Ursache steht bei pytest am Schluss, ``-q`` druckt davor je
    gesammeltem Test eine Zeile)."""
    if len(text) <= limit:
        return text
    return f"... [{len(text) - limit} Zeichen gekürzt] ...{text[-limit:]}"


def _documented_gl_smoke() -> _DocumentedGlSmoke:
    text = TESTING_MD.read_text(encoding="utf-8")
    match = _GL_SMOKE_FILE_LIST_RE.search(text)
    assert match is not None, (
        "gl_smoke-Klammer-Aufzählung in TESTING.md nicht gefunden - Wortlaut "
        "geändert? Anker in _GL_SMOKE_FILE_LIST_RE nachziehen."
    )
    # Dateiliste endet vor der "; modulweit ..."-Klausel; die Prosa danach
    # darf keine Datei beisteuern (eine dort ergänzte, voll qualifizierte
    # Nennung wäre sonst eine falsche vierte "dokumentierte" Datei).
    parts = re.split(r";\s*modulweit", match.group(1), maxsplit=1)
    assert len(parts) == 2, (
        '„; modulweit …"-Klausel in der TESTING.md-Aufzählung nicht gefunden '
        "- Wortlaut geändert? Anker im re.split hier nachziehen."
    )
    files = frozenset(f"tests/{name}" for name in _TEST_FILE_RE.findall(parts[0]))
    # Der Parser versteht genau EINE modulweite Datei (fester Präfix vor dem
    # Namen) - nennt die Doku künftig mehrere, Regex zur Aufzählung erweitern.
    module_wide_match = _MODULE_WIDE_RE.search("modulweit" + parts[1])
    assert module_wide_match is not None, (
        "„modulweit nur in `…`\"-Nennung in TESTING.md nicht gefunden - "
        "Wortlaut geändert? Anker in _MODULE_WIDE_RE nachziehen."
    )
    module_wide = frozenset({f"tests/{module_wide_match.group(1)}"})
    assert module_wide <= files, (
        f"Als modulweit dokumentierte Dateien {sorted(module_wide)} fehlen in "
        f"der dokumentierten Dateiliste {sorted(files)} - TESTING.md in sich "
        "inkonsistent."
    )
    return _DocumentedGlSmoke(files=files, module_wide=module_wide)


@cache
def _collect_markers() -> dict[str, dict[str, list[str]]] | str:
    """Marker-Inventur per pytest-Subprozess (Pfad -> {Funktion -> [Marker]}).

    Eigener Prozess, damit Konfiguration/Plugins des äußeren Laufs unberührt
    bleiben; kostet eine zweite Kollektion aller ``tests/*.py`` (wenige
    Sekunden, einmal je Testlauf - ``@cache`` teilt das Ergebnis zwischen
    den Testfunktionen). ``-o addopts=`` und leeres ``PYTEST_ADDOPTS``
    entfernen den Standard-Markerfilter ``-m 'not ui or ui_smoke'`` - die
    Kollektion muss für die Modulweite-Prüfung ungefiltert sein. Fehler
    kommen als ``str`` zurück statt als Exception, damit auch sie gecacht
    werden (``functools.cache`` speichert nur erfolgreiche Rückgaben; ein
    Timeout liefe sonst je Aufrufer erneut 300 s).
    """
    json_fd, json_path = tempfile.mkstemp(suffix=".json", prefix="gl_smoke_markers_")
    os.close(json_fd)
    # ``tests/`` ist ein Paket (``tests/__init__.py``) und via cwd=ROOT
    # bereits importierbar - kein PYTHONPATH-Eingriff nötig, der ``tests/``
    # sonst vorn in den Suchpfad des Kindes stellte.
    env = dict(os.environ, PYTEST_ADDOPTS="", MARKER_COLLECT_JSON=json_path)
    argv = [
        sys.executable, "-m", "pytest",
        "-o", "addopts=",
        "-p", "no:cacheprovider",
        "-p", "tests._marker_collect_plugin",
        "--collect-only", "-q", "tests",
    ]
    try:
        try:
            result = subprocess.run(
                argv, cwd=ROOT, capture_output=True, text=True, timeout=300, env=env,
            )
        except subprocess.TimeoutExpired:
            return (
                "pytest-Sammlung für die Marker-Inventur nach 300s abgebrochen "
                "(Timeout, überlasteter Runner?)."
            )
        if result.returncode != 0:
            return (
                f"pytest-Sammlung für die Marker-Inventur fehlgeschlagen (exit "
                f"{result.returncode}; ggf. Folgefehler eines unbeteiligten "
                f"Kollektionsfehlers im Testbaum):\n"
                f"{_tail(result.stdout)}\n{_tail(result.stderr)}"
            )
        raw = Path(json_path).read_text(encoding="utf-8")
    finally:
        Path(json_path).unlink(missing_ok=True)
    if not raw:
        return (
            "Marker-Plugin hat keine Daten geschrieben - Plugin nicht geladen "
            "oder Kollektion leer?\n" + _tail(result.stdout)
        )
    try:
        data: dict[str, dict[str, list[str]]] = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Auch dieser Fehler muss als str durch den @cache - eine Exception
        # liefe je Aufrufer erneut durch den vollen Subprozess.
        return f"Marker-Inventur nicht lesbar ({exc}):\n{_tail(raw)}"
    if not data:
        return "Marker-Inventur leer - Kollektion kaputt?\n" + _tail(result.stdout)
    return data


def _marker_inventory() -> dict[str, dict[str, list[str]]]:
    """Gecachtes Sammelergebnis; Fehler -> ``pytest.fail``."""
    result = _collect_markers()
    if isinstance(result, str):
        pytest.fail(result)
    return result


def _gl_smoke_counts(inventory: dict[str, dict[str, list[str]]]) -> dict[str, int]:
    """Datei -> Anzahl ``gl_smoke``-markierter Testfunktionen (nur > 0)."""
    counts = {
        path: sum(1 for markers in functions.values() if "gl_smoke" in markers)
        for path, functions in inventory.items()
    }
    return {path: n for path, n in counts.items() if n}


def test_testing_md_gl_smoke_list_matches_actual_markers() -> None:
    documented = _documented_gl_smoke().files
    actual = set(_gl_smoke_counts(_marker_inventory()))
    assert actual, "Kein gl_smoke-markierter Test gefunden - Marker versehentlich entfernt?"
    assert documented == actual, (
        f"TESTING.md nennt {sorted(documented)}, tatsächlich gl_smoke-markiert "
        f"sind {sorted(actual)}. Liste in TESTING.md nachziehen (#832, gleiches "
        f"Drift-Muster wie #826)."
    )


def test_gl_smoke_marker_granularity_matches_testing_md() -> None:
    """Granularitätsaussage in beide Richtungen: „modulweit" genannte Dateien
    tragen den Marker an allen Tests, die übrigen dokumentierten an genau
    einem. Beide Doku-Mengen kommen aus derselben Klammer, der Ist-Zustand
    aus der ungefilterten Inventur."""
    documented = _documented_gl_smoke()
    inventory = _marker_inventory()
    marked = _gl_smoke_counts(inventory)

    not_module_wide = {
        path: (marked.get(path, 0), len(inventory.get(path, {})))
        for path in documented.module_wide
        if marked.get(path, 0) == 0
        or marked.get(path, 0) != len(inventory.get(path, {}))
    }
    assert not not_module_wide, (
        f"Als modulweit dokumentiert, aber nicht alle Tests tragen gl_smoke "
        f"(Datei -> (markiert, gesamt)): {not_module_wide}. TESTING.md-Aussage "
        f'„modulweit nur in …" nachziehen.'
    )

    wrong = {
        path: marked.get(path, 0)
        for path in documented.files - documented.module_wide
        if marked.get(path, 0) != 1
    }
    assert not wrong, (
        f"Erwartet genau ein gl_smoke-markierter Test je Datei, tatsächlich: "
        f"{wrong}. TESTING.md-Aussage „in den übrigen Modulen an je einem "
        f'Test" nachziehen.'
    )
