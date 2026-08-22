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


def _decode(data: bytes | str | None) -> str:
    """``TimeoutExpired.stdout``/``.stderr`` sind unter POSIX auch mit
    ``text=True`` rohe ``bytes`` (``Popen._check_timeout`` fügt sie vor der
    Decode-Behandlung zusammen) – ohne das landen escapte ``\\n`` in der
    Fehlermeldung statt lesbarer Zeilen (#832-Review)."""
    if isinstance(data, bytes):
        return data.decode(errors="replace")
    return data or ""


@cache
def _collect_gl_smoke() -> Counter[str] | str:
    """Fragt pytest selbst, welche Module tatsächlich ``gl_smoke``-markierte
    Tests enthalten (Datei -> Anzahl markierter Test*funktionen*, nicht
    Node-IDs – siehe unten). Rückgabe im Fehlerfall ein ``str`` mit der
    Diagnose statt einer Exception: ``functools.cache`` speichert nur
    erfolgreiche Rückgaben, ein geworfener Fehler liefe also bei jedem der
    beiden Aufrufer erneut durch den vollen Subprozess (im Timeout-Fall
    2 × 300 s) – als gecachter Wert fällt er nur einmal an (#845-Review);
    die Testfunktionen unten übersetzen ihn in ``pytest.fail``.

    Läuft als eigener Prozess (nicht ``pytest.main`` im laufenden Lauf), damit
    Konfiguration/Plugins des äußeren Laufs unberührt bleiben – kostet dafür
    eine zweite Kollektion aller ``tests/*.py`` (wenige Sekunden bei warmem
    Import-Cache lokal gemessen, #832-Review; auf CI-Runnern mit kaltem
    Cache und wachsender Testanzahl tendenziell mehr – fällt dafür einmal
    **je Testlauf** an, ``@cache`` teilt Ergebnis wie Fehler zwischen den
    beiden Testfunktionen unten). ``--collect-only -q`` liefert nur bei
    Verbosity **-1** stabile Node-IDs (``pfad::testname``); Verbosity 0
    (kein ``-q``) druckt einen Baum ohne ``tests/…``-Zeilen, und ein zweites
    ``-q`` obendrauf ergäbe Verbosity -2 (``pfad: N`` statt Node-IDs) –
    deshalb neutralisieren ``-o addopts=`` **und** eine leere
    ``PYTEST_ADDOPTS``-Umgebungsvariable jede geerbte Verbosity (aus
    ``pyproject.toml`` bzw. der Aufrufumgebung), bevor das hier gesetzte
    einzige ``-q`` greift. ``-p no:warnings`` unterdrückt die abschließende
    „warnings summary": deren Zeilen können je nach Warnungsursprung
    ebenfalls mit ``tests/`` beginnen und ``::`` enthalten und würden sonst
    als falsche Node-IDs durch den Filter unten rutschen.

    Gezählt werden **Testfunktionen**, nicht rohe Node-IDs: Eine spätere
    Parametrisierung eines der Einzeldekorator-Tests (``test_x.py::
    test_y[a]``, ``…[b]``) verdoppelt sonst den Node-ID-Zähler, obwohl die
    TESTING.md-Aussage „an je einem Test" (Einzeldekorator statt
    modulweitem ``pytestmark``) unverändert stimmt – der ``[...]``-Suffix
    wird deshalb vor dem Zählen abgeschnitten.
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
            argv, cwd=ROOT, capture_output=True, text=True, timeout=300, env=env,
        )
    except subprocess.TimeoutExpired as exc:
        return (
            "pytest-Sammlung für gl_smoke nach 300s abgebrochen (Timeout, "
            "überlasteter Runner?) - stdout bisher:\n"
            f"{_decode(exc.stdout)}\nstderr bisher:\n{_decode(exc.stderr)}"
        )
    # 5 = NO_TESTS_COLLECTED (kein gl_smoke-Test mehr vorhanden) - kein
    # Kollektionsfehler, sondern genau der Drift-Fall, den die praezisere
    # Meldung unten abdeckt.
    if result.returncode not in (0, 5):
        return (
            f"pytest-Sammlung für gl_smoke fehlgeschlagen (exit "
            f"{result.returncode}; ggf. Folgefehler eines unbeteiligten "
            f"Kollektionsfehlers im Testbaum):\n{result.stdout}\n{result.stderr}"
        )
    per_file_functions: dict[str, set[str]] = {}
    for line in result.stdout.splitlines():
        if not line.startswith("tests/") or "::" not in line:
            continue
        file_path, test_part = line.split("::", 1)
        base_name = test_part.split("[", 1)[0]  # Parametrisierung abschneiden
        per_file_functions.setdefault(file_path, set()).add(base_name)
    if not per_file_functions:
        return (
            "Kein gl_smoke-markierter Test gefunden - Marker versehentlich "
            "entfernt oder Sammlung kaputt?\n" + result.stdout
        )
    return Counter({path: len(names) for path, names in per_file_functions.items()})


def _actual_gl_smoke_counts() -> Counter[str]:
    """Wertet das gecachte Sammelergebnis aus; Fehler -> ``pytest.fail``."""
    result = _collect_gl_smoke()
    if isinstance(result, str):
        pytest.fail(result)
    return result


def test_testing_md_gl_smoke_list_matches_actual_markers() -> None:
    documented = _documented_gl_smoke().files
    actual = set(_actual_gl_smoke_counts())
    assert documented == actual, (
        f"TESTING.md nennt {sorted(documented)}, tatsächlich gl_smoke-markiert "
        f"sind {sorted(actual)}. Liste in TESTING.md nachziehen (#832, gleiches "
        f"Drift-Muster wie #826)."
    )


def test_single_test_gl_smoke_files_have_exactly_one_marked_test() -> None:
    """Sichert die zweite TESTING.md-Aussage ab: In allen dokumentierten
    Modulen außer den als „modulweit" genannten hängt der Marker an genau
    einem Test (Einzeldekorator). Beide Mengen kommen aus derselben
    TESTING.md-Klammer (``_documented_gl_smoke``) – keine separat zu
    pflegende Hand-Liste, ein künftiges weiteres Einzeldekorator-Modul wird
    automatisch mitgeprüft (#845-Review). Ob eine „modulweit" genannte Datei
    tatsächlich modulweit markiert ist (alle ihre Tests, nicht nur zufällig
    genau einer), wird bewusst nicht verifiziert – das bräuchte eine zweite,
    ungefilterte Kollektion und bleibt eine dokumentierte Grenze.
    """
    documented = _documented_gl_smoke()
    single_test_files = documented.files - documented.module_wide
    counts = _actual_gl_smoke_counts()
    wrong = {
        path: counts.get(path, 0)
        for path in single_test_files
        if counts.get(path, 0) != 1
    }
    assert not wrong, (
        f"Erwartet genau ein gl_smoke-markierter Test je Datei, tatsächlich: "
        f"{wrong}. TESTING.md-Aussage „in den übrigen Modulen an je einem "
        f'Test" nachziehen (#832-Review).'
    )
