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


def _parse_color(spec: str) -> tuple[float, float, float, float]:
    """``#rrggbb``/``#rgb``/``rgba(r,g,b,a)`` → (r, g, b, a) in 0..1."""
    spec = spec.strip()
    if spec.startswith("rgba"):
        parts = spec[spec.index("(") + 1:spec.rindex(")")].split(",")
        r, g, b = (float(v) / 255 for v in parts[:3])
        return r, g, b, float(parts[3])
    h = spec.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (1.0,)  # type: ignore[return-value]


def _composite(fg_spec: str, bg_spec: str) -> tuple[float, float, float]:
    """Legt eine (ggf. teiltransparente) Farbe über einen opaken Hintergrund."""
    fr, fg_, fb, fa = _parse_color(fg_spec)
    br, bg_, bb, _ = _parse_color(bg_spec)
    return (
        fa * fr + (1 - fa) * br,
        fa * fg_ + (1 - fa) * bg_,
        fa * fb + (1 - fa) * bb,
    )


def _luminance(rgb: tuple[float, float, float]) -> float:
    """WCAG-Relativluminanz eines linearen sRGB-Tripels (0..1 je Kanal)."""
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(fg: str, bg: str, *, under: str | None = None) -> float:
    """WCAG-Kontrast; ``under`` komponiert einen rgba-Hintergrund über eine Fläche."""
    bg_rgb = _composite(bg, under) if under is not None else _composite(bg, bg)
    fg_rgb = _composite(fg, "#000000") if not fg.startswith("rgba") else _composite(fg, bg)
    hi, lo = sorted((_luminance(fg_rgb), _luminance(bg_rgb)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_palettes_meet_wcag_contrast_matrix():
    """A11y-Kontrastmatrix (#429/#441): alle zentralen Farbpaare beider Schemata.

    Schwellen: normaler Text ≥ 4.5:1 (WCAG AA), UI-Komponenten/Fokus-/
    Akzentzustände ≥ 3.0:1 (WCAG 1.4.11). **Disabled**-Zustände sind nach
    WCAG 1.4.3 ausgenommen; ein dokumentierter Boden von ≥ 2.0:1 bewacht sie
    trotzdem gegen unlesbare Regressionen. ``muted`` ist vertraglich nur für
    Disabled/Placeholder zulässig (siehe ``Palette``-Docstring) – aktiver
    Hinweistext nutzt ``text3``.
    """
    from bgremover.theme import DARK, LIGHT

    for p in (DARK, LIGHT):
        # ── Normaler Text ≥ 4.5:1 auf jeder Fläche, auf der er vorkommt ──
        text_pairs = [
            (p.text, p.bg), (p.text, p.inspector), (p.text, p.card_bg),
            (p.text, p.surface), (p.text, p.stepper), (p.text, p.nav),
            (p.text2, p.card_bg), (p.text2, p.surface), (p.text2, p.toolbar),
            (p.text2, p.nav), (p.text2, p.surface_hover),
            (p.text3, p.card_bg), (p.text3, p.inspector), (p.text3, p.stepper),
            (p.text3, p.status), (p.text3, p.toolbar),
        ]
        for fg, bg in text_pairs:
            ratio = _contrast(fg, bg)
            assert ratio >= 4.5, f"Text {fg} auf {bg}: {ratio:.2f} < 4.5"
        # Akzenttext auf weicher Akzentfläche (ausgewählte Buttons, ✓-Kreis).
        soft = _contrast(p.accent_text, p.accent_soft, under=p.card_bg)
        assert soft >= 4.5, f"accent_text auf accent_soft: {soft:.2f} < 4.5"
        # Tooltip (QToolTip: text auf surface) ist über text/surface abgedeckt.

        # ── UI-Komponenten / Fokus / Akzent ≥ 3.0:1 ──
        ui_pairs = [
            (p.on_accent, p.accent), (p.on_accent, p.accent2),
            # Fokusring (accent-Rahmen) gegen die Flächen, auf denen er liegt.
            (p.accent, p.card_bg), (p.accent, p.inspector),
            (p.accent, p.surface), (p.accent, p.bg), (p.accent, p.stepper),
        ]
        for fg, bg in ui_pairs:
            ratio = _contrast(fg, bg)
            assert ratio >= 3.0, f"UI {fg} auf {bg}: {ratio:.2f} < 3.0"

        # ── Disabled (WCAG-exempt, dokumentierter Regressions-Boden) ──
        disabled_pairs = [(p.muted, p.divider), (p.muted, p.surface)]
        for fg, bg in disabled_pairs:
            ratio = _contrast(fg, bg)
            assert ratio >= 2.0, f"Disabled {fg} auf {bg}: {ratio:.2f} < 2.0"


def test_interactive_style_builders_carry_focus_state():
    """A11y (#441): Jeder interaktive Stil-Baustein trägt seinen Fokuszustand selbst.

    Widget-Stylesheets überstimmen die App-QSS-``:focus``-Regel bei
    ``border``-Konflikten – die globale Fallback-Regel genügt daher nicht.
    Der Vertrag gilt in beiden Schemata.
    """
    from bgremover import theme

    builders = (
        theme.panel_btn_style, theme.primary_btn_style, theme.nav_back_style,
        theme.nav_next_style, theme.tool_style, theme.history_button_style,
        theme.num_style, theme.slider_style,
    )
    for build in builders:
        for p in (theme.DARK, theme.LIGHT):
            assert ":focus" in build(p), build.__name__
    # Statische Crop-Leisten-Stile (border:none) ebenso.
    assert ":focus" in theme.CROP_CONFIRM_STYLE
    assert ":focus" in theme.CROP_CANCEL_STYLE


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
