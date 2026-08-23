"""Drift-Schutz für **alle drei** Markerlisten in ``TESTING.md`` (#832, #847).

``TESTING.md`` zählt von Hand auf, welche Testdateien ``gl_smoke``, ``ui``
und ``ui_smoke`` tragen; #826 zeigte, dass so eine Liste unbemerkt
unvollständig wird. Analog zu ``test_ci_qt_packages.py`` (Befund N6) hält
dieser Test Doku und Bestand synchron: pytest sammelt die Marker selbst –
über die Hook-API des Mini-Plugins ``tests/_marker_collect_plugin.py``,
nicht über das Terminal-Ausgabeformat von ``--collect-only``.

Die teure Hälfte – die ungefilterte Zweit-Kollektion – ist seit #832 ohnehin
je Testlauf bezahlt und über ``@cache`` geteilt; die ``ui``-/``ui_smoke``-
Prüfungen aus #847 kosten daher nur je einen Doku-Parser. Das Modul hieß bis
#847 ``test_gl_smoke_marker_governance.py`` und deckt jetzt alle drei Listen
ab, daher der allgemeinere Name.
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


# Die beiden UI-Aufzählungen (#847). Beide Captures enden an einem Satz, der
# nicht mehr zur Liste gehört - sie können dadurch nicht in den Folgeabsatz
# rutschen und dort eine Datei aufsammeln.
_UI_LIST_RE = re.compile(r"## Die UI-Tests\n(.*?)Nur diese `ui`-markierten Tests", re.DOTALL)
_UI_SMOKE_LIST_RE = re.compile(
    r"Marker `ui_smoke`\s*[–-]\s*(.*?)Die meisten dieser Module", re.DOTALL
)
# Zwischen allen Tokens ``\s+`` statt fester Leerzeichen: TESTING.md ist auf
# ~76 Zeichen umbrochen, ein Zeilenumbruch kann redaktionell an jeder Stelle
# des Satzes landen. Ein Muster mit festen Leerzeichen scheitert dann laut,
# aber grundlos.
_BOTH_MARKERS_RE = re.compile(
    r"nur\s+`(?:tests/)?(test_\w+\.py)`\s+und\s+`(?:tests/)?(test_\w+\.py)`"
    r"\s+tragen\s+beide\s+Marker"
)


class _DocumentedGlSmoke(NamedTuple):
    """Beide TESTING.md-Aussagen aus derselben Klammer."""

    files: frozenset[str]
    module_wide: frozenset[str]


class _DocumentedUiSmoke(NamedTuple):
    """Die ``ui_smoke``-Aufzählung und die Aussage zur Doppelmarkierung."""

    files: frozenset[str]
    both: frozenset[str]


def _tail(text: str, limit: int = 2000) -> str:
    """Kürzt lange Kind-Ausgaben in Fehlermeldungen auf das lesbare Ende
    (die Ursache steht bei pytest am Schluss, ``-q`` druckt davor je
    gesammeltem Test eine Zeile)."""
    if len(text) <= limit:
        return text
    return f"... [{len(text) - limit} Zeichen gekürzt] ...{text[-limit:]}"


def _documented_gl_smoke(text: str | None = None) -> _DocumentedGlSmoke:
    """Parst die beiden Doku-Aussagen; *text* nur für die Negativkontrollen."""
    if text is None:
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


def _documented_ui_modules(text: str | None = None) -> frozenset[str]:
    """Die als ``ui``-markiert dokumentierten Module (#847).

    *text* nur für die Negativkontrollen.
    """
    if text is None:
        text = TESTING_MD.read_text(encoding="utf-8")
    match = _UI_LIST_RE.search(text)
    assert match is not None, (
        "ui-Aufzählung in TESTING.md nicht gefunden - Wortlaut geändert? "
        "Anker in _UI_LIST_RE nachziehen."
    )
    files = frozenset(f"tests/{name}" for name in _TEST_FILE_RE.findall(match.group(1)))
    assert files, (
        "ui-Aufzählung geparst, aber leer - ohne diese Zusicherung wäre ein zu "
        "enger Anker von einer korrekt leeren Liste nicht zu unterscheiden."
    )
    return files


def _documented_ui_smoke(text: str | None = None) -> _DocumentedUiSmoke:
    """Die ``ui_smoke``-Aufzählung und die Aussage zur Doppelmarkierung (#847)."""
    if text is None:
        text = TESTING_MD.read_text(encoding="utf-8")
    match = _UI_SMOKE_LIST_RE.search(text)
    assert match is not None, (
        "ui_smoke-Aufzählung in TESTING.md nicht gefunden - Wortlaut geändert? "
        "Anker in _UI_SMOKE_LIST_RE nachziehen."
    )
    files = frozenset(f"tests/{name}" for name in _TEST_FILE_RE.findall(match.group(1)))
    assert files, "ui_smoke-Aufzählung geparst, aber leer - Anker zu eng?"
    both_match = _BOTH_MARKERS_RE.search(text)
    assert both_match is not None, (
        '„nur `…` und `…` tragen beide Marker"-Aussage in TESTING.md nicht '
        "gefunden - Wortlaut geändert? Anker in _BOTH_MARKERS_RE nachziehen."
    )
    both = frozenset(f"tests/{name}" for name in both_match.groups())
    assert both <= files, (
        f"Als doppelt markiert dokumentiert {sorted(both)}, steht aber nicht in "
        f"der ui_smoke-Aufzählung {sorted(files)} - TESTING.md in sich "
        "inkonsistent."
    )
    return _DocumentedUiSmoke(files=files, both=both)


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
    env = dict(os.environ, PYTEST_ADDOPTS="", BGREMOVER_MARKER_COLLECT_JSON=json_path)
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
    if "__filtered__" in data:
        return (
            f"Marker-Inventur entstand unter aktivem Filter ({data['__filtered__']}) "
            "- das Plugin verlangt eine ungefilterte Kollektion."
        )
    if not data:
        return "Marker-Inventur leer - Kollektion kaputt?\n" + _tail(result.stdout)
    return data


def _marker_inventory() -> dict[str, dict[str, list[str]]]:
    """Gecachtes Sammelergebnis; Fehler -> ``pytest.fail``.

    Gibt je Datei/Funktion eigene Container zurück - ``@cache`` teilt sonst
    dieselben verschachtelten Objekte zwischen allen Aufrufern, und eine
    spätere In-place-Normalisierung (naheliegend bei der #847-Erweiterung)
    würde still testreihenfolge-abhängig."""
    result = _collect_markers()
    if isinstance(result, str):
        pytest.fail(result)
    return {
        path: {name: list(markers) for name, markers in functions.items()}
        for path, functions in result.items()
    }


def _modules_with_marker(inventory: dict[str, dict[str, list[str]]], marker: str) -> set[str]:
    """Alle Dateien, in denen mindestens ein Test *marker* trägt (#847)."""
    return {
        path
        for path, functions in inventory.items()
        if any(marker in markers for markers in functions.values())
    }


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


def test_gl_smoke_tests_run_in_the_default_selection() -> None:
    """TESTING.md: „Sie laufen in jedem normalen ``pytest``-Lauf mit" - gilt
    nur, solange kein ``gl_smoke``-Test zusätzlich ``ui`` ohne ``ui_smoke``
    trägt; sonst deselektiert ihn der Default-Filter ``-m 'not ui or
    ui_smoke'`` still."""
    deselected = {
        f"{path}::{name}"
        for path, functions in _marker_inventory().items()
        for name, markers in functions.items()
        if "gl_smoke" in markers and "ui" in markers and "ui_smoke" not in markers
    }
    assert not deselected, (
        f"gl_smoke-Tests mit ``ui`` ohne ``ui_smoke`` werden vom Default-"
        f"Filter deselektiert und laufen nicht mehr in jedem normalen Lauf "
        f"mit: {sorted(deselected)}."
    )


def test_default_marker_filter_matches_documented_claim() -> None:
    """Anker für die zweite Hälfte der Default-Selektions-Aussage: der Filter
    selbst. Ändert sich ``addopts`` in ``pyproject.toml`` (z. B. um einen
    ``gl_smoke``-Ausschluss), stimmt „laufen in jedem normalen pytest-Lauf
    mit" nicht mehr - dann TESTING.md und diese Prüfungen mit anpassen."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^addopts = "(.*)"$', text)
    assert match is not None, "addopts in pyproject.toml nicht gefunden."
    # Bewusst nur der Markerausdruck: andere addopts-Ergänzungen (z. B.
    # --strict-markers, -ra) berühren die Default-Selektion nicht.
    assert "-m 'not ui or ui_smoke'" in match.group(1), (
        f"Default-Markerfilter geändert ({match.group(1)!r}) - TESTING.md-"
        "Aussage zur Default-Selektion und diese Governance-Prüfungen nachziehen."
    )


def test_testing_md_ui_list_matches_actual_markers() -> None:
    """Die ``ui``-Aufzählung gegen den Ist-Bestand (#847).

    Exakte Gleichheit: Der Absatz zählt die drei Module abschließend auf
    („Sie sind mit dem Marker `ui` versehen, ebenso … und …"), und
    ``make ui`` führt genau diese Menge aus.
    """
    documented = _documented_ui_modules()
    actual = _modules_with_marker(_marker_inventory(), "ui")
    assert actual, "Kein ui-markierter Test gefunden - Marker versehentlich entfernt?"
    assert documented == actual, (
        f"TESTING.md nennt als ui-markiert {sorted(documented)}, tatsächlich "
        f"sind es {sorted(actual)}. Liste in TESTING.md nachziehen (#847, "
        f"gleiches Drift-Muster wie #826/#832)."
    )


def test_testing_md_ui_smoke_list_matches_actual_markers() -> None:
    """Die ``ui_smoke``-Aufzählung gegen den Ist-Bestand (#847).

    Ebenfalls exakte Gleichheit. Die Aufzählung stand bis #847 unter „u. a."
    und war damit ausdrücklich unvollständig — eine so formulierte Liste ist
    gegen genau den Schaden nicht absicherbar, um den es hier geht (#826: die
    Liste wird unbemerkt unvollständig). Das „u. a." ist deshalb entfallen und
    das dort fehlende ``test_e2e_release_regression.py`` ergänzt.
    """
    documented = _documented_ui_smoke().files
    actual = _modules_with_marker(_marker_inventory(), "ui_smoke")
    assert actual, "Kein ui_smoke-markierter Test gefunden - Marker versehentlich entfernt?"
    assert documented == actual, (
        f"TESTING.md nennt als ui_smoke-markiert {sorted(documented)}, "
        f"tatsächlich sind es {sorted(actual)}. Liste in TESTING.md nachziehen."
    )


def test_testing_md_double_marker_claim_matches_actual_markers() -> None:
    """„nur X und Y tragen beide Marker" gegen den Ist-Bestand (#847)."""
    documented = _documented_ui_smoke().both
    inventory = _marker_inventory()
    actual = _modules_with_marker(inventory, "ui") & _modules_with_marker(inventory, "ui_smoke")
    assert documented == actual, (
        f"TESTING.md nennt {sorted(documented)} als doppelt markiert, "
        f"tatsächlich tragen {sorted(actual)} beide Marker. Aussage in "
        f"TESTING.md nachziehen."
    )


def test_ui_doc_parsers_detect_synthetic_drift() -> None:
    """Negativkontrollen für die beiden UI-Parser (#847).

    Ohne sie wäre ein zu großzügiger oder ins Leere laufender Capture von
    einem korrekten nicht zu unterscheiden - derselbe Grund wie bei
    ``test_doc_parser_detects_synthetic_drift`` für ``gl_smoke``.
    """
    ui_text = (
        "## Die UI-Tests\n\n`tests/test_a.py` enthält X, ebenso\n"
        "`tests/test_b.py`. Nur diese `ui`-markierten Tests laufen bei make ui.\n"
        "Spaeterer Absatz nennt `tests/test_zzz.py`.\n"
    )
    assert _documented_ui_modules(ui_text) == {"tests/test_a.py", "tests/test_b.py"}, (
        "Capture reicht in den Folgeabsatz - test_zzz.py darf nicht mitzählen."
    )

    smoke_text = (
        "Subset trägt den Marker `ui_smoke` – in `tests/test_a.py` und\n"
        "`tests/test_b.py`. Die meisten dieser Module tragen nur `ui_smoke`,\n"
        "nicht zusätzlich `ui` – nur `test_a.py` und `test_b.py` tragen beide\n"
        "Marker. Danach `tests/test_zzz.py`.\n"
    )
    parsed = _documented_ui_smoke(smoke_text)
    assert parsed.files == {"tests/test_a.py", "tests/test_b.py"}
    assert parsed.both == {"tests/test_a.py", "tests/test_b.py"}

    with pytest.raises(AssertionError, match="_UI_LIST_RE"):
        _documented_ui_modules("Kein UI-Abschnitt hier.")
    with pytest.raises(AssertionError, match="_UI_SMOKE_LIST_RE"):
        _documented_ui_smoke("Kein ui_smoke-Absatz hier.")
    with pytest.raises(AssertionError, match="in sich\ninkonsistent|in sich inkonsistent"):
        _documented_ui_smoke(
            "Marker `ui_smoke` – in `tests/test_a.py`. Die meisten dieser Module "
            "tragen nur das – nur `test_a.py` und `test_c.py` tragen beide Marker."
        )


def test_doc_parser_detects_synthetic_drift() -> None:
    """Negativkontrolle für den Doku-Parser (Muster von
    ``test_recommendations_freeze_consistency``): synthetische Fassungen des
    Absatzes müssen erkennbar anders parsen bzw. laut scheitern - sonst wäre
    ein leerer oder zu großzügiger Capture von einem korrekten nicht zu
    unterscheiden."""
    base = (
        "Ein weiterer Marker, `gl_smoke`, kennzeichnet X\n"
        "(`tests/test_a.py`, `tests/test_b.py`; modulweit nur in\n"
        "`test_a.py`, Rest je ein Test). Prosa danach."
    )
    parsed = _documented_gl_smoke(base)
    assert parsed.files == {"tests/test_a.py", "tests/test_b.py"}
    assert parsed.module_wide == {"tests/test_a.py"}

    entfernt = _documented_gl_smoke(base.replace("`tests/test_b.py`", ""))
    assert entfernt.files == {"tests/test_a.py"}

    ergaenzt = _documented_gl_smoke(
        base.replace("`tests/test_b.py`", "`tests/test_b.py`, `tests/test_c.py`")
    )
    assert "tests/test_c.py" in ergaenzt.files

    # Prosa hinter der ``modulweit``-Klausel darf keine Datei beisteuern.
    prosa = _documented_gl_smoke(
        base.replace("Rest je ein Test", "Rest je ein Test, siehe `tests/test_z.py`")
    )
    assert "tests/test_z.py" not in prosa.files

    # Eine frühere Klammer im selben Satz darf den Capture nicht kapern.
    frueher = _documented_gl_smoke(
        base.replace("kennzeichnet X", "kennzeichnet X (siehe `tests/test_y.py`)")
    )
    assert frueher.files == {"tests/test_a.py", "tests/test_b.py"}

    with pytest.raises(AssertionError, match="modulweit"):
        _documented_gl_smoke(base.replace("; modulweit nur in", " – modulweit nur in"))
