"""Drift-Schutz für die ``gl_smoke``-Markerliste in ``TESTING.md`` (#832).

``TESTING.md`` zählt die ``gl_smoke``-markierten Testdateien von Hand auf
(``tests/test_viewer_3d_gl.py``, ``tests/test_screenshot3d.py``,
``tests/test_benchmark_preview3d_live.py``). Kein Test hielt diese Liste
bisher synchron mit dem tatsächlichen Marker-Bestand – genau das war die
Ursache für #826 (die Liste war bereits einmal unvollständig, unbemerkt bis
zum nächsten manuellen Audit). Analog zu ``test_ci_qt_packages.py`` (Befund
N6) und ``test_recommendations_freeze_consistency.py`` sichert dieser Test
die Drift-Klasse „von Hand gepflegte Liste vs. tatsächlicher Bestand" ab –
netzfrei, ohne die Testdateien selbst zu parsen: pytest sammelt die Marker
selbst, über die öffentliche Hook-/Item-API des Mini-Plugins
``tests/_marker_collect_plugin.py`` (einzige Quelle der Wahrheit, keine
zweite Kopie der Marker-Logik und kein Parsing der Terminal-Ausgabe,
#845-Review).
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

#: Die Klammer identifiziert sich über ihren eigenen Inhalt („modulweit"),
#: statt blind die erste Klammer nach dem Anker zu greifen – ein später in
#: denselben Satz eingeschobener Klammer-Einschub (z. B. „(siehe ADR #591)")
#: würde den Capture sonst still verschieben und die Fehlermeldung auf den
#: falschen Anker zeigen lassen (#845-Review).
_GL_SMOKE_FILE_LIST_RE = re.compile(
    r"Ein weiterer Marker, `gl_smoke`.*?\(([^)]*modulweit[^)]*)\)", re.DOTALL
)
#: Nur Backtick-umschlossene ``tests/test_*.py``-Pfade – reiner Fließtext
#: (z. B. „ADR #591") darf nicht als Datei zählen.
_TEST_FILE_RE = re.compile(r"`(tests/test_\w+\.py)`")
#: Die „modulweit nur in `X`"-Klausel ist die dokumentierte Quelle der
#: modulweiten Markierung – der Test leitet sie von hier ab, statt sie als
#: Hand-Konstante zu doppeln (#845-Review). Das ``tests/``-Präfix ist
#: optional, damit eine redaktionelle Vereinheitlichung mit den drei
#: Nennungen daneben (alle *mit* Präfix) keinen Fehlalarm auslöst;
#: normalisiert wird unten ohnehin auf ``tests/<name>``.
_MODULE_WIDE_RE = re.compile(r"modulweit nur in\s*`(?:tests/)?(test_\w+\.py)`")


class _DocumentedGlSmoke(NamedTuple):
    """Beide TESTING.md-Aussagen aus derselben Klammer: Dateiliste +
    modulweit markierte Teilmenge."""

    files: frozenset[str]
    module_wide: frozenset[str]


def _documented_gl_smoke() -> _DocumentedGlSmoke:
    text = TESTING_MD.read_text(encoding="utf-8")
    match = _GL_SMOKE_FILE_LIST_RE.search(text)
    assert match is not None, (
        "gl_smoke-Klammer-Aufzählung in TESTING.md nicht gefunden - Wortlaut "
        "geändert? Anker in _GL_SMOKE_FILE_LIST_RE nachziehen."
    )
    # Die eigentliche Dateiliste endet vor der "; modulweit ..."-Klausel;
    # danach folgt reine Prosa über die Marker-*Granularität*, keine weitere
    # Datei-Nennung. Ohne diesen Schnitt würde eine später ergänzte,
    # vollständig referenzierte Klarstellung (z. B. „… im Unterschied zu
    # `tests/test_viewer_3d_gl_lifecycle.py`, das keinen GL-Kontext
    # braucht") fälschlich als vierte dokumentierte Datei gelesen –
    # Backticks + ``tests/``-Präfix allein schützen davor nicht, weil genau
    # so eine Ergänzung beides trägt (#832-Review).
    parts = re.split(r";\s*modulweit", match.group(1), maxsplit=1)
    assert len(parts) == 2, (
        '„; modulweit …"-Klausel in der TESTING.md-Aufzählung nicht gefunden '
        "- Wortlaut geändert? Anker im re.split hier nachziehen (sonst würde "
        "der Schnitt stillschweigend entfallen und Prosa mitscannen)."
    )
    files = frozenset(_TEST_FILE_RE.findall(parts[0]))
    # Die modulweite Teilmenge aus derselben Klausel ableiten, gegen die der
    # Schnitt oben trennt - Doku-Wortlaut und Prüfung haben damit eine
    # gemeinsame Quelle statt einer separat zu pflegenden Hand-Konstante.
    module_wide_names = _MODULE_WIDE_RE.findall("modulweit" + parts[1])
    assert module_wide_names, (
        "„modulweit nur in `…`\"-Nennung in TESTING.md nicht gefunden - "
        "Wortlaut geändert? Anker in _MODULE_WIDE_RE nachziehen."
    )
    module_wide = frozenset(f"tests/{name}" for name in module_wide_names)
    assert module_wide <= files, (
        f"Die als modulweit dokumentierten Dateien {sorted(module_wide)} "
        f"fehlen in der dokumentierten Dateiliste {sorted(files)} - "
        "TESTING.md in sich inkonsistent."
    )
    return _DocumentedGlSmoke(files=files, module_wide=module_wide)


@cache
def _collect_markers() -> dict[str, dict[str, list[str]]] | str:
    """Sammelt über einen pytest-Subprozess je Testdatei die Marker aller
    Testfunktionen (Pfad -> {Funktionsname -> [Markernamen]}).

    Läuft als eigener Prozess (nicht ``pytest.main`` im laufenden Lauf),
    damit Konfiguration/Plugins des äußeren Laufs unberührt bleiben –
    kostet dafür eine zweite Kollektion aller ``tests/*.py`` (wenige
    Sekunden bei warmem Import-Cache lokal gemessen, #832-Review; auf
    CI-Runnern mit kaltem Cache und wachsender Testanzahl tendenziell mehr;
    ``@cache`` teilt Ergebnis wie Fehler zwischen den Testfunktionen unten,
    es fällt also einmal je Testlauf an). Die Marker liest das Mini-Plugin
    ``tests/_marker_collect_plugin.py`` direkt aus den ``Item``-Objekten
    (öffentliche Hook-API) und schreibt sie als JSON – der frühere Vertrag
    mit dem Terminal-Ausgabeformat von ``--collect-only`` (Verbosity-
    Choreografie, ``-p no:warnings``, Zeilenfilter, ``[...]``-Abschneiden)
    entfällt damit vollständig (#845-Review).

    ``-o addopts=`` **und** eine leere ``PYTEST_ADDOPTS``-Umgebungsvariable
    neutralisieren die geerbten addopts – hier nicht wegen der Verbosity,
    sondern wegen des Standard-Markerfilters ``-m 'not ui or ui_smoke'``
    aus ``pyproject.toml``: die Kollektion muss **ungefiltert** sein, damit
    „alle Tests einer Datei" (Modulweite-Prüfung unten) stimmt.

    Rückgabe im Fehlerfall ein ``str`` mit der Diagnose statt einer
    Exception: ``functools.cache`` speichert nur erfolgreiche Rückgaben,
    ein geworfener Fehler liefe also bei jedem Aufrufer erneut durch den
    vollen Subprozess (im Timeout-Fall 2 × 300 s) – als gecachter Wert
    fällt er nur einmal an (#845-Review); die Testfunktionen unten
    übersetzen ihn in ``pytest.fail``.
    """
    json_fd, json_path = tempfile.mkstemp(suffix=".json", prefix="gl_smoke_markers_")
    os.close(json_fd)
    env = dict(
        os.environ,
        PYTEST_ADDOPTS="",
        MARKER_COLLECT_JSON=json_path,
        # ``-p _marker_collect_plugin`` lädt früh über importlib; ``tests/``
        # liegt dann noch nicht auf sys.path.
        PYTHONPATH=os.pathsep.join(
            p for p in (str(ROOT / "tests"), os.environ.get("PYTHONPATH")) if p
        ),
    )
    argv = [
        sys.executable, "-m", "pytest",
        "-o", "addopts=",
        "-p", "no:cacheprovider",
        "-p", "_marker_collect_plugin",
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
                f"Kollektionsfehlers im Testbaum):\n{result.stdout}\n{result.stderr}"
            )
        raw = Path(json_path).read_text(encoding="utf-8")
    finally:
        Path(json_path).unlink(missing_ok=True)
    if not raw:
        return (
            "Marker-Plugin hat keine Daten geschrieben - Plugin nicht geladen "
            "oder Kollektion leer?\n" + result.stdout
        )
    data: dict[str, dict[str, list[str]]] = json.loads(raw)
    if not data:
        return "Marker-Inventur leer - Kollektion kaputt?\n" + result.stdout
    return data


def _marker_inventory() -> dict[str, dict[str, list[str]]]:
    """Wertet das gecachte Sammelergebnis aus; Fehler -> ``pytest.fail``."""
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
    """Sichert die zweite TESTING.md-Aussage ab – vollständig, in beide
    Richtungen: Die als „modulweit" genannten Dateien tragen den Marker an
    **allen** ihren Tests, die übrigen dokumentierten Dateien an **genau
    einem**. Beide Doku-Mengen kommen aus derselben TESTING.md-Klammer
    (``_documented_gl_smoke``), der Ist-Zustand aus der ungefilterten
    Marker-Inventur – seit dem Plugin-Umbau (#845-Review) ist damit auch
    die früher als bewusste Grenze dokumentierte Modulweite-Prüfung
    abgedeckt (ohne ``-m``-Filter kennt die Inventur alle Tests je Datei).
    """
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
        f'„modulweit nur in …" nachziehen (#832-Review).'
    )

    single_test_files = documented.files - documented.module_wide
    wrong = {
        path: marked.get(path, 0)
        for path in single_test_files
        if marked.get(path, 0) != 1
    }
    assert not wrong, (
        f"Erwartet genau ein gl_smoke-markierter Test je Datei, tatsächlich: "
        f"{wrong}. TESTING.md-Aussage „in den übrigen Modulen an je einem "
        f'Test" nachziehen (#832-Review).'
    )
