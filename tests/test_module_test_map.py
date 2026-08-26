"""Hält die Modul→Testdatei-Zuordnung in TESTING.md ehrlich (#869).

Nicht jedes Modul in ``bgremover/`` hat eine gleichnamige Testdatei; mehrere
aktiv gepflegte Module (u. a. ``expert_mode_toggle``, ``height_map_panel``,
``right_panel_tabs``, ``layer_panel``) werden bewusst in großen Sammeldateien
mitgeprüft. Wer ein solches Modul isoliert ändert, übersieht die zugehörigen
Tests leicht – TESTING.md führt deshalb eine Zuordnungstabelle. Eine von Hand
gepflegte Liste driftet aber genauso zuverlässig wie die Qt-apt-Paketlisten
(Befund N6) oder die Markerlisten (#845/#852), darum erzwingt dieser Test sie
netzfrei in **beide** Richtungen:

* Jedes Modul ohne gleichnamige Testdatei hat genau eine Zeile.
* Jede Zeile nennt ein existierendes Modul, das (noch) keine gleichnamige
  Testdatei hat – bekommt es eine, ist die Zeile zu entfernen.
* Jede genannte Testdatei existiert und **importiert** das Modul – direkt
  (``from bgremover.<modul> import …`` / ``import bgremover.<modul>``) oder
  über ein Paket-Re-Export-Symbol (``from bgremover import CropOverlayItem``).
  Eine Zeile, die ins Leere zeigt, wäre schlimmer als keine Zeile.

Bewusst zählen **nur Import-Anweisungen**, nicht der freie Dateitext: Ein
Modul wie ``i18n`` exportiert kurze, allgegenwärtige Namen (``tr``), und ein
Texttreffer darauf hätte fast jede Testdatei als „Beleg" durchgehen lassen –
die Rückwärtsrichtung wäre damit schwächer gewesen, als dieser Docstring
verspricht (Review-Befund auf PR #873).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "bgremover"
TESTS = ROOT / "tests"
TESTING_MD = ROOT / "TESTING.md"

#: Überschrift der Tabelle. Ändert sich der Wortlaut, soll dieser Test bewusst
#: sichtbar scheitern statt still eine andere Tabelle zu prüfen.
_SECTION_HEADING = "### Wo liegen die Tests zu Modul X? (#869)"

#: ``bgremover/<modul>.py`` in Spalte 1, ``tests/<datei>.py`` in Spalte 2.
_ROW_RE = re.compile(r"^\|\s*`bgremover/(\w+)\.py`\s*\|([^|]*)\|\s*$", re.MULTILINE)
_TESTFILE_RE = re.compile(r"`tests/(test_\w+\.py)`")

#: Module, die es bewusst nicht in die Tabelle schaffen sollen.
_PACKAGE_EXCLUDED = {"__init__", "__main__"}


def _table_section() -> str:
    text = TESTING_MD.read_text(encoding="utf-8")
    start = text.find(_SECTION_HEADING)
    assert start >= 0, f"Abschnitt fehlt in TESTING.md: {_SECTION_HEADING}"
    rest = text[start + len(_SECTION_HEADING):]
    end = rest.find("\n## ")
    return rest if end < 0 else rest[:end]


def _documented_map() -> dict[str, tuple[str, ...]]:
    """Die in TESTING.md dokumentierte Zuordnung Modul → Testdateien."""
    section = _table_section()
    mapping: dict[str, tuple[str, ...]] = {}
    for module, cell in _ROW_RE.findall(section):
        assert module not in mapping, f"{module} steht mehrfach in der Tabelle"
        mapping[module] = tuple(_TESTFILE_RE.findall(cell))
    assert mapping, "Zuordnungstabelle in TESTING.md ist leer"
    return mapping


def _modules_without_own_test_file() -> set[str]:
    """Module in ``bgremover/`` ohne gleichnamige ``tests/test_<modul>.py``."""
    return {
        path.stem
        for path in PACKAGE.glob("*.py")
        if path.stem not in _PACKAGE_EXCLUDED
        and not (TESTS / f"test_{path.stem}.py").is_file()
    }


def _public_symbols(module: str) -> frozenset[str]:
    """Öffentliche Top-Level-Klassen/-Funktionen eines Moduls."""
    text = (PACKAGE / f"{module}.py").read_text(encoding="utf-8")
    return frozenset(re.findall(r"(?m)^(?:class|def)\s+([A-Za-z]\w*)", text))


def _imported_names(test_file: Path) -> frozenset[str]:
    """Aus ``bgremover`` importierte Modul- bzw. Paket-Symbolnamen.

    Ausgewertet wird der Syntaxbaum, nicht der Dateitext: So zählen auch
    funktionslokale und über mehrere Zeilen geklammerte Importe, während ein
    bloßer ``tr(...)``-Aufruf im Rumpf **kein** Beleg mehr ist.
    """
    tree = ast.parse(test_file.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:                      # import bgremover.canvas
                parts = alias.name.split(".")
                if parts[0] == "bgremover" and len(parts) > 1:
                    names.add(parts[1])
        elif isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if parts[0] != "bgremover":
                continue
            if len(parts) > 1:
                names.add(parts[1])                       # from bgremover.canvas import …
            else:
                names.update(a.name for a in node.names)  # from bgremover import canvas|Symbol
    return frozenset(names)


def _imports_module(test_file: Path, module: str) -> bool:
    """True, wenn *test_file* das Modul importiert.

    Neben dem Modulpfad zählt der Paket-Re-Export: ``test_crop_overlay.py``
    holt ``CropOverlayItem`` über ``from bgremover import …`` statt über
    ``bgremover.crop``. Symbolnamen sind modulspezifisch genug, um das
    zuzulassen, ohne die Schärfe des Import-Kriteriums aufzugeben.
    """
    imported = _imported_names(test_file)
    return module in imported or bool(imported & _public_symbols(module))


def test_every_module_without_own_test_file_is_documented() -> None:
    """Kein Modul fällt aus der Zuordnung – sonst bliebe es unauffindbar."""
    missing = _modules_without_own_test_file() - set(_documented_map())
    assert not missing, (
        "Module ohne gleichnamige Testdatei fehlen in der TESTING.md-Tabelle "
        f"'{_SECTION_HEADING}': {sorted(missing)}"
    )


def test_documented_rows_still_describe_modules_without_own_test_file() -> None:
    """Veraltete Zeilen fallen auf: gelöschtes Modul oder neue eigene Testdatei."""
    documented = set(_documented_map())
    unknown = {m for m in documented if not (PACKAGE / f"{m}.py").is_file()}
    assert not unknown, f"Tabelle nennt nicht existierende Module: {sorted(unknown)}"

    obsolete = documented - _modules_without_own_test_file()
    assert not obsolete, (
        "Diese Module haben inzwischen eine eigene tests/test_<modul>.py – "
        f"Zeile in TESTING.md entfernen: {sorted(obsolete)}"
    )


def test_documented_test_files_exist_and_import_their_module() -> None:
    """Jede genannte Datei existiert und importiert das Modul tatsächlich."""
    broken: list[str] = []
    for module, files in _documented_map().items():
        if not files:
            broken.append(f"{module}: keine Testdatei genannt")
            continue
        for name in files:
            path = TESTS / name
            if not path.is_file():
                broken.append(f"{module}: tests/{name} existiert nicht")
            elif not _imports_module(path, module):
                broken.append(
                    f"{module}: tests/{name} importiert weder bgremover.{module} "
                    "noch eines seiner öffentlichen Symbole")
    assert not broken, "Zuordnung in TESTING.md zeigt ins Leere:\n" + "\n".join(broken)
