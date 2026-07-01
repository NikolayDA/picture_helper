"""Schützt die zentralisierte UI-Farbpalette (_Theme).

Die Tests dokumentieren die kanonischen Werte und verteidigen die
Entfernung der toten Konstanten gegen eine versehentliche Wiedereinführung.
"""
import ast
from pathlib import Path

import bgremover
from bgremover.right_panel import TAB_STYLE
from bgremover.theme import _Theme

_PKG = Path(__file__).resolve().parent.parent / "bgremover"


def _pkg_assigned_names() -> set[str]:
    """Sammelt die Modul-Level ``Name``-Ziele aller Zuweisungen im Paket.

    Prüft paketweit, dass ``BTN_STYLE``/``GRP_STYLE`` nicht erneut als
    Modulkonstanten auftauchen.
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


def test_palette_for_selects_scheme_case_insensitively():
    from bgremover.theme import DARK, LIGHT, palette_for

    assert palette_for("light") is LIGHT
    assert palette_for("LIGHT") is LIGHT
    assert palette_for("dark") is DARK
    assert palette_for("anything-else") is DARK
    assert LIGHT.is_dark is False
    assert DARK.is_dark is True


def test_active_palette_round_trips():
    from bgremover.theme import DARK, LIGHT, active_palette, set_active_palette

    assert active_palette() is DARK  # Prozess-Default dunkel
    try:
        set_active_palette(LIGHT)
        assert active_palette() is LIGHT
    finally:
        set_active_palette(DARK)
    assert active_palette() is DARK


def test_style_builders_track_their_palette():
    from bgremover.theme import (
        DARK,
        LIGHT,
        card_style,
        menu_style,
        section_header_style,
        slider_style,
    )

    # Jeder Builder zieht seine Farben aus der übergebenen Palette (kein Drift).
    assert LIGHT.card_bg in card_style(LIGHT)
    assert DARK.card_bg in card_style(DARK)
    assert LIGHT.accent in section_header_style(LIGHT)
    assert LIGHT.border in slider_style(LIGHT)
    assert LIGHT.accent in menu_style(LIGHT)
    # Aufgelöste f-Strings enthalten keine doppelten Klammern mehr.
    assert "{{" not in card_style(LIGHT)


def test_build_qpalette_uses_scheme_colors(qapp):
    from PyQt6.QtGui import QColor, QPalette

    from bgremover.theme import LIGHT, build_qpalette

    pal = build_qpalette(LIGHT)
    assert pal.color(QPalette.ColorRole.Window) == QColor(LIGHT.bg)
    assert pal.color(QPalette.ColorRole.Highlight) == QColor(LIGHT.accent)


def test_build_app_stylesheet_has_focus_ring_and_tooltip():
    """A11y (#429): der App-QSS trägt Fokusring und getönten Tooltip."""
    from bgremover.theme import LIGHT, build_app_stylesheet

    sheet = build_app_stylesheet(LIGHT)
    assert ":focus" in sheet
    assert LIGHT.accent in sheet
    assert "QToolTip" in sheet


def _relative_luminance(hex_color: str) -> float:
    """WCAG-Relativluminanz einer ``#rrggbb``-Farbe."""
    h = hex_color.lstrip("#")
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
              for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(fg: str, bg: str) -> float:
    hi, lo = sorted((_relative_luminance(fg), _relative_luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_palettes_meet_wcag_contrast():
    """A11y (#429): Text- und Button-Kontraste erfüllen die WCAG-AA-Schwellen."""
    from bgremover.theme import DARK, LIGHT

    for p in (DARK, LIGHT):
        # Fließtext auf allen Flächen ≥ 4.5:1 (AA für normalen Text).
        for bg in (p.bg, p.inspector, p.card_bg):
            assert _contrast(p.text, bg) >= 4.5
        # Sekundär-/gedämpfter Text auf Karten ≥ 4.5:1.
        assert _contrast(p.text2, p.card_bg) >= 4.5
        assert _contrast(p.text3, p.card_bg) >= 4.5
        assert _contrast(p.text3, p.inspector) >= 4.5
        # Button-Beschriftung auf Akzent ≥ 3.0:1 (AA für UI-Komponenten/fett).
        assert _contrast(p.on_accent, p.accent) >= 3.0


def test_stepper_apply_palette_restyles(qapp):
    from bgremover.stepper import Stepper
    from bgremover.theme import DARK, LIGHT

    stepper = Stepper()
    try:
        stepper.apply_palette(LIGHT)
        assert LIGHT.stepper in stepper.styleSheet()
        stepper.apply_palette(DARK)
        assert DARK.stepper in stepper.styleSheet()
    finally:
        stepper.deleteLater()


def test_dead_style_constants_not_reintroduced():
    # BTN_STYLE/GRP_STYLE waren toter Code (nirgends referenziert) und
    # wurden entfernt – nicht erneut anlegen.
    assert not hasattr(bgremover, "BTN_STYLE")
    assert not hasattr(bgremover, "GRP_STYLE")
    assigned = _pkg_assigned_names()
    assert "BTN_STYLE" not in assigned
    assert "GRP_STYLE" not in assigned
