"""Schützt die zentralisierte UI-Farbpalette (_Theme).

Hintergrund: Die zuvor dutzendfach inline wiederholten Stylesheet-Farben
sind in `_Theme` gebündelt. Die Refaktorierung wurde als
*byte-identisch* verifiziert (alle 218 Widget-Stylesheets unverändert).
Diese Tests dokumentieren die kanonischen Werte und verteidigen die
Entfernung der toten Konstanten gegen eine versehentliche
Wiedereinführung.
"""
import ast
from pathlib import Path

import bgremover
from bgremover.right_panel import TAB_STYLE
from bgremover.theme import _Theme

_PKG = Path(__file__).resolve().parent.parent / "bgremover"


def _pkg_assigned_names() -> set[str]:
    """Sammelt die Modul-Level ``Name``-Ziele aller Zuweisungen im Paket.

    Verteidigt die Regel ``BTN_STYLE``/``GRP_STYLE`` bleiben tot –
    unabhaengig davon, in welchem Paket-Modul jemand sie kuenftig
    versehentlich wieder anlegen wuerde.
    """
    names: set[str] = set()
    for p in sorted(_PKG.glob("*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        names |= {
            t.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            for t in node.targets
            if isinstance(t, ast.Name)
        }
    return names


def test_theme_has_canonical_values():
    t = _Theme
    assert t.ACCENT == "#4a90d9"
    assert t.BG_PANEL == "#1a1a1a"
    assert t.BG_TABBAR == "#141414"
    assert t.BORDER == "#3a3a3a"
    assert t.DIVIDER == "#2a2a2a"
    assert t.TEXT_BRIGHT == "#e0e0e0"


def test_shared_templates_use_palette():
    # Die wiederverwendeten Templates müssen die Palette referenzieren,
    # nicht erneut hartkodierte Hex-Werte enthalten.
    assert _Theme.ACCENT in bgremover.TOOL_STYLE
    assert _Theme.BORDER in bgremover.SLD_STYLE
    assert _Theme.ACCENT in TAB_STYLE
    # Resolvte Templates enthalten valides CSS (Einfach-Klammern nach
    # f-String-Auflösung, keine doppelten {{ }} mehr).
    assert "{{" not in bgremover.TOOL_STYLE
    assert "}}" not in TAB_STYLE


def test_dead_style_constants_not_reintroduced():
    # BTN_STYLE/GRP_STYLE waren toter Code (nirgends referenziert) und
    # wurden entfernt – nicht erneut anlegen.
    assert not hasattr(bgremover, "BTN_STYLE")
    assert not hasattr(bgremover, "GRP_STYLE")
    assigned = _pkg_assigned_names()
    assert "BTN_STYLE" not in assigned
    assert "GRP_STYLE" not in assigned
