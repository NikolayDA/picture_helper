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

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTING_MD = ROOT / "TESTING.md"

#: Der Absatz, der die gl_smoke-Dateien aufzählt – Anker bewusst eng am
#: Wortlaut, damit eine Umformulierung diesen Test sichtbar scheitern lässt
#: statt still den falschen Abschnitt zu matchen.
_GL_SMOKE_PARAGRAPH_RE = re.compile(
    r"Ein weiterer Marker, `gl_smoke`.*?\n\n", re.DOTALL
)
_TEST_FILE_RE = re.compile(r"tests/test_\w+\.py")


def _documented_gl_smoke_files() -> set[str]:
    text = TESTING_MD.read_text(encoding="utf-8")
    match = _GL_SMOKE_PARAGRAPH_RE.search(text)
    assert match is not None, (
        "gl_smoke-Absatz in TESTING.md nicht gefunden - Wortlaut geändert? "
        "Anker in _GL_SMOKE_PARAGRAPH_RE nachziehen."
    )
    return set(_TEST_FILE_RE.findall(match.group(0)))


def _actual_gl_smoke_files() -> set[str]:
    """Fragt pytest selbst nach den tatsächlich ``gl_smoke``-markierten Modulen.

    Läuft als eigener Prozess (nicht ``pytest.main`` im laufenden Lauf), damit
    Konfiguration/Plugins des äußeren Laufs unberührt bleiben. ``--collect-only``
    ohne ``-q`` liefert stabile Node-IDs (``pfad::testname``) statt eines
    Format, das sich zwischen pytest-Versionen ändern könnte.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-m", "gl_smoke", "tests"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
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
