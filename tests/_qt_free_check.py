"""Geteilter Wächter: Ein Modul importiert keine Qt-Bindings (#1044).

Vier Testdateien trugen dieselbe ~15-zeilige AST-Prüfung als Kopie
(`test_gloss_preview`, `test_relief_preview`, `test_project_history`,
`test_project_io`). Die Regel liegt jetzt an genau einer Stelle; die Tests
nennen nur noch das zu prüfende Modul. Geprüft wird der Quelltext, nicht der
Laufzeitzustand: Ein Qt-Import hinter einem ``if TYPE_CHECKING`` oder in einer
Funktion zählt genauso – die Module gelten als Qt-frei testbar, weil sie Qt
gar nicht erst nennen.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import ModuleType

#: Die Bindings, die ein Qt-freies Modul nicht importieren darf.
QT_BINDINGS: frozenset[str] = frozenset({"PyQt6", "PyQt5", "PySide6"})


def imported_top_level_names(module: ModuleType) -> set[str]:
    """Oberste Paketnamen aller ``import``/``from … import`` des Modulquelltexts."""
    assert module.__file__ is not None, module.__name__
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    return {name.split(".")[0] for name in imported}


def assert_module_is_qt_free(*modules: ModuleType) -> None:
    """Schlägt mit Modulname und Fundliste fehl, sobald ein Modul Qt importiert."""
    for module in modules:
        offending = sorted(imported_top_level_names(module) & QT_BINDINGS)
        assert not offending, f"{module.__name__} importiert Qt-Bindings: {offending}"
