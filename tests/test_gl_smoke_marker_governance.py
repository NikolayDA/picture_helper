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
from pathlib import Path

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


def _documented_gl_smoke_files() -> set[str]:
    text = TESTING_MD.read_text(encoding="utf-8")
    match = _GL_SMOKE_FILE_LIST_RE.search(text)
    assert match is not None, (
        "gl_smoke-Klammer-Aufzählung in TESTING.md nicht gefunden - Wortlaut "
        "geändert? Anker in _GL_SMOKE_FILE_LIST_RE nachziehen."
    )
    return set(_TEST_FILE_RE.findall(match.group(1)))


def _actual_gl_smoke_files() -> set[str]:
    """Fragt pytest selbst nach den tatsächlich ``gl_smoke``-markierten Modulen.

    Läuft als eigener Prozess (nicht ``pytest.main`` im laufenden Lauf), damit
    Konfiguration/Plugins des äußeren Laufs unberührt bleiben. ``--collect-only
    -q`` liefert nur bei Verbosity **-1** stabile Node-IDs (``pfad::testname``);
    Verbosity 0 (kein ``-q``) druckt einen Baum ohne ``tests/…``-Zeilen, und
    ein zweites ``-q`` obendrauf ergäbe Verbosity -2 (``pfad: N`` statt
    Node-IDs) – deshalb neutralisieren ``-o addopts=`` **und** eine leere
    ``PYTEST_ADDOPTS``-Umgebungsvariable jede geerbte Verbosity (aus
    ``pyproject.toml`` bzw. der Aufrufumgebung), bevor das hier gesetzte
    einzige ``-q`` greift.
    """
    env = dict(os.environ, PYTEST_ADDOPTS="")
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "-o", "addopts=",
            "-p", "no:cacheprovider",
            "--collect-only", "-q", "-m", "gl_smoke", "tests",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    # 5 = NO_TESTS_COLLECTED (kein gl_smoke-Test mehr vorhanden) - kein
    # Kollektionsfehler, sondern genau der Drift-Fall, den die zweite
    # Assertion unten praezise meldet.
    assert result.returncode in (0, 5), (
        f"pytest-Sammlung für gl_smoke fehlgeschlagen (exit {result.returncode}):\n"
        f"{result.stdout}\n{result.stderr}"
    )
    files = {
        line.split("::", 1)[0]
        for line in result.stdout.splitlines()
        if line.startswith("tests/") and "::" in line
    }
    assert files, (
        "Kein gl_smoke-markierter Test gefunden - Marker versehentlich entfernt "
        "oder Sammlung kaputt?\n" + result.stdout
    )
    return files


def test_testing_md_gl_smoke_list_matches_actual_markers() -> None:
    documented = _documented_gl_smoke_files()
    actual = _actual_gl_smoke_files()
    assert documented == actual, (
        f"TESTING.md nennt {sorted(documented)}, tatsächlich gl_smoke-markiert "
        f"sind {sorted(actual)}. Liste in TESTING.md nachziehen (#832, gleiches "
        f"Drift-Muster wie #826)."
    )
