"""Drift-Schutz für die ``gl_smoke``-Markerliste in ``TESTING.md`` (#832).

``TESTING.md`` zählt die ``gl_smoke``-markierten Testdateien von Hand auf
(``tests/test_viewer_3d_gl.py``, ``tests/test_screenshot3d.py``,
``tests/test_benchmark_preview3d_live.py``). Kein Test hielt diese Liste
bisher synchron mit dem tatsächlichen Marker-Bestand – genau das war die
Ursache für #826 (die Liste war bereits einmal unvollständig, unbemerkt bis
zum nächsten manuellen Audit). Analog zu ``test_ci_qt_packages.py`` (Befund
N6) und ``test_recommendations_freeze_consistency.py`` sichert dieser Test
die Drift-Klasse „von Hand gepflegte Liste vs. tatsächlicher Bestand" ab –
netzfrei, ohne die Testdateien selbst zu parsen: pytest fragt sich hier
schlicht selbst, welche Module ``gl_smoke``-markierte Tests enthalten
(einzige Quelle der Wahrheit, keine zweite Kopie der Marker-Logik).
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TESTING_MD = ROOT / "TESTING.md"

#: Nur die Klammer-Aufzählung nach „gl_smoke`" matchen, nicht den ganzen
#: Absatz: Ein Prosa-Zusatz danach (z. B. eine klärende Ergänzung, die ein
#: *anderes* ``tests/test_*.py`` beim Namen nennt, ohne dass es tatsächlich
#: gl_smoke-markiert ist) darf keinen falschen Treffer erzeugen. Anker
#: bewusst eng am Wortlaut, damit eine Umformulierung diesen Test sichtbar
#: scheitern lässt statt still den falschen Abschnitt zu matchen.
_GL_SMOKE_FILE_LIST_RE = re.compile(
    r"Ein weiterer Marker, `gl_smoke`.*?\(([^)]*)\)", re.DOTALL
)
_TEST_FILE_RE = re.compile(r"tests/test_\w+\.py")

#: TESTING.md behauptet zusätzlich zur Dateimenge, dass der Marker in diesen
#: beiden Modulen an genau einem Test hängt (Einzeldekorator statt
#: modulweitem ``pytestmark`` wie in ``test_viewer_3d_gl.py``, #832-Review).
#: Bewusst als expliziter Vertrag statt als Prosa-Parsing der Zahl „einem" -
#: Freitext-Regex auf natürlichsprachliche Zahlwörter wäre genau die
#: Fragilität, die _GL_SMOKE_FILE_LIST_RE oben schon vermeidet.
_SINGLE_TEST_GL_SMOKE_FILES = (
    "tests/test_screenshot3d.py",
    "tests/test_benchmark_preview3d_live.py",
)


def _documented_gl_smoke_files() -> set[str]:
    text = TESTING_MD.read_text(encoding="utf-8")
    match = _GL_SMOKE_FILE_LIST_RE.search(text)
    assert match is not None, (
        "gl_smoke-Klammer-Aufzählung in TESTING.md nicht gefunden - Wortlaut "
        "geändert? Anker in _GL_SMOKE_FILE_LIST_RE nachziehen."
    )
    return set(_TEST_FILE_RE.findall(match.group(1)))


def _actual_gl_smoke_counts() -> Counter[str]:
    """Fragt pytest selbst, welche Module tatsächlich ``gl_smoke``-markierte
    Tests enthalten (Datei -> Anzahl markierter Tests).

    Läuft als eigener Prozess (nicht ``pytest.main`` im laufenden Lauf), damit
    Konfiguration/Plugins des äußeren Laufs unberührt bleiben – kostet dafür
    eine zweite Kollektion aller ``tests/*.py`` (~1,7 s lokal gemessen, #832-
    Review; fällt bei jedem ``make check``/``make coverage``/PR-CI-Lauf an,
    nicht nur bei Doku-Änderungen, wurde als vertretbar eingeordnet).
    ``--collect-only -q`` liefert nur bei Verbosity **-1** stabile Node-IDs
    (``pfad::testname``); Verbosity 0 (kein ``-q``) druckt einen Baum ohne
    ``tests/…``-Zeilen, und ein zweites ``-q`` obendrauf ergäbe Verbosity -2
    (``pfad: N`` statt Node-IDs) – deshalb neutralisieren ``-o addopts=``
    **und** eine leere ``PYTEST_ADDOPTS``-Umgebungsvariable jede geerbte
    Verbosity (aus ``pyproject.toml`` bzw. der Aufrufumgebung), bevor das
    hier gesetzte einzige ``-q`` greift. ``-p no:warnings`` unterdrückt die
    abschließende „warnings summary": deren Zeilen können je nach
    Warnungsursprung ebenfalls mit ``tests/`` beginnen und ``::`` enthalten
    und würden sonst als falsche Node-IDs durch den Filter unten rutschen.
    """
    env = dict(os.environ, PYTEST_ADDOPTS="")
    argv = [
        sys.executable, "-m", "pytest",
        "-o", "addopts=",
        "-p", "no:cacheprovider",
        "-p", "no:warnings",
        "--collect-only", "-q", "-m", "gl_smoke", "tests",
    ]
    try:
        result = subprocess.run(
            argv, cwd=ROOT, capture_output=True, text=True, timeout=120, env=env,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(
            "pytest-Sammlung für gl_smoke nach 120s abgebrochen (Timeout) - "
            f"stdout bisher:\n{exc.stdout}\nstderr bisher:\n{exc.stderr}"
        )
    # 5 = NO_TESTS_COLLECTED (kein gl_smoke-Test mehr vorhanden) - kein
    # Kollektionsfehler, sondern genau der Drift-Fall, den die zweite
    # Assertion unten praezise meldet.
    assert result.returncode in (0, 5), (
        f"pytest-Sammlung für gl_smoke fehlgeschlagen (exit {result.returncode}):\n"
        f"{result.stdout}\n{result.stderr}"
    )
    counts = Counter(
        line.split("::", 1)[0]
        for line in result.stdout.splitlines()
        if line.startswith("tests/") and "::" in line
    )
    assert counts, (
        "Kein gl_smoke-markierter Test gefunden - Marker versehentlich entfernt "
        "oder Sammlung kaputt?\n" + result.stdout
    )
    return counts


def test_testing_md_gl_smoke_list_matches_actual_markers() -> None:
    documented = _documented_gl_smoke_files()
    actual = set(_actual_gl_smoke_counts())
    assert documented == actual, (
        f"TESTING.md nennt {sorted(documented)}, tatsächlich gl_smoke-markiert "
        f"sind {sorted(actual)}. Liste in TESTING.md nachziehen (#832, gleiches "
        f"Drift-Muster wie #826)."
    )


def test_single_test_gl_smoke_files_have_exactly_one_marked_test() -> None:
    """Sichert die zweite TESTING.md-Aussage ab: In den beiden Nicht-
    ``test_viewer_3d_gl.py``-Modulen hängt der Marker an genau einem Test
    (Einzeldekorator), nicht modulweit. ``test_viewer_3d_gl.py`` selbst bleibt
    hier bewusst ungeprüft: „modulweit" verspricht keine feste Testanzahl,
    ein künftig dort ergänzter Test würde den Marker automatisch mitführen,
    ohne dass TESTING.md falsch würde.
    """
    counts = _actual_gl_smoke_counts()
    wrong = {
        path: counts.get(path, 0)
        for path in _SINGLE_TEST_GL_SMOKE_FILES
        if counts.get(path, 0) != 1
    }
    assert not wrong, (
        f"Erwartet genau ein gl_smoke-markierter Test je Datei, tatsächlich: "
        f"{wrong}. TESTING.md-Aussage „in den beiden anderen Modulen an je "
        f'einem Test" nachziehen (#832-Review).'
    )
