"""Schützt die zentralisierte UI-Farbpalette (_Theme).

Die Tests dokumentieren die kanonischen Werte und verteidigen die
Entfernung der toten Konstanten gegen eine versehentliche Wiedereinführung.
"""
import ast
import re
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
    from bgremover.theme import DARK

    # Die wiederverwendeten Templates müssen die Palette referenzieren,
    # nicht erneut hartkodierte Hex-Werte enthalten. ``_Theme.BORDER``/
    # ``_Theme.ACCENT`` bleiben als Rückwärtskompatibilitäts-Snapshot beim
    # alten Opak-Grauton bzw. alten Akzentblau (#476 macht ``DARK.border``
    # zum teiltransparenten Overlay, #477 hellt ``DARK.accent`` auf) – der
    # Live-Vertrag von ``TOOL_STYLE``/``SLD_STYLE`` prüft daher gegen die
    # aktuellen ``DARK``-Werte, nicht gegen die eingefrorenen Konstanten.
    # ``TAB_STYLE`` wird dagegen direkt aus ``_Theme.ACCENT`` gebaut (siehe
    # right_panel.py) – dort bleibt der Vergleich gegen ``_Theme`` korrekt.
    assert DARK.accent in bgremover.TOOL_STYLE
    assert DARK.border in bgremover.SLD_STYLE
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
            (p.text3, p.inspector), (p.text3, p.stepper),
            (p.text3, p.status), (p.text3, p.toolbar),
        ]
        if not p.is_dark:
            # Im dunklen Schema folgt card_bg jetzt dem abgenommenen Prototyp-
            # Token (#2e353f). Dort ist text3 auf Karten ein sekundärer
            # UI-Farbton statt ein AA-Textvertrag.
            text_pairs.append((p.text3, p.card_bg))
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


def test_make_checker_brush_uses_palette_checker_tokens(qapp):
    """Issue #478: das Canvas-Schachbrett zieht seine Farben aus der Palette."""
    from PyQt6.QtGui import QColor

    from bgremover.image_utils import make_checker_brush
    from bgremover.theme import DARK, LIGHT

    for p in (DARK, LIGHT):
        img = make_checker_brush(p, size=4).texture().toImage()
        # Aufbau laut make_checker_brush: Basisfüllung checker_a, zwei
        # gegenüberliegende size×size-Quadrate (oben-links/unten-rechts) in
        # checker_b übermalt – ein klassisches 2×2-Schachbrettmuster.
        assert img.pixelColor(0, 0) == QColor(p.checker_b)
        assert img.pixelColor(6, 0) == QColor(p.checker_a)
        assert img.pixelColor(0, 6) == QColor(p.checker_a)
        assert img.pixelColor(6, 6) == QColor(p.checker_b)
    # Dunkles und helles Schema unterscheiden sich sichtbar.
    dark_img = make_checker_brush(DARK, size=4).texture().toImage()
    light_img = make_checker_brush(LIGHT, size=4).texture().toImage()
    assert dark_img.pixelColor(0, 0) != light_img.pixelColor(0, 0)


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


def test_card_metric_tokens_are_named_constants():
    """Issue #414 (§5.1): Karten-Maße existieren zentral als benannte Tokens.

    Radius, Innenpolster, Binnen- und Sektionsabstand liegen ausschließlich in
    ``theme`` – die Panels lesen diese Tokens statt verstreuter Magic Numbers.
    """
    from bgremover import right_panel_tabs as rpt
    from bgremover import theme

    assert theme.CARD_RADIUS_PX == 12
    assert theme.CARD_PADDING == (14, 13, 14, 13)   # Innenpolster 14/13 (§5.1)
    assert theme.CARD_CONTENT_SPACING == 10          # Binnenabstand (§5.1)
    assert theme.CARD_STACK_SPACING == 11            # Sektionsabstand im Stapel (§5.1)
    # Der Radius-Token bestimmt den aufgelösten Karten-Stil (kein zweiter Wert).
    assert f"{theme.CARD_RADIUS_PX}px" in theme.CARD_STYLE
    # Die Panels ziehen exakt diese Tokens (kein Drift zur Spec).
    assert rpt._CARD_STACK_SPACING == theme.CARD_STACK_SPACING
    assert rpt._CARD_STACK_SIDE_MARGIN == theme.CARD_STACK_SIDE_MARGIN
    assert rpt._CARD_STACK_TOP_MARGIN == theme.CARD_STACK_TOP_MARGIN
    assert rpt._CARD_STACK_BOTTOM_MARGIN == theme.CARD_STACK_BOTTOM_MARGIN


def test_card_style_defined_for_both_schemes():
    """Issue #414: Der Karten-Stil ist im hellen UND dunklen Schema definiert."""
    from bgremover.theme import CARD_RADIUS_PX, DARK, LIGHT, card_style

    for p in (DARK, LIGHT):
        style = card_style(p)
        assert p.card_bg in style
        assert p.card_border in style
        assert f"{CARD_RADIUS_PX}px" in style
    # Hell und dunkel unterscheiden sich sichtbar (verschiedener Kartengrund).
    assert card_style(DARK) != card_style(LIGHT)


def _accent_hexes() -> set[str]:
    """Kanonische Akzent-Hexwerte beider Schemata (``accent`` + ``accent2``)."""
    from bgremover.theme import DARK, LIGHT

    values = {DARK.accent, DARK.accent2, LIGHT.accent, LIGHT.accent2}
    return {v.lower() for v in values if v.startswith("#")}


def test_no_hardcoded_accent_hex_outside_theme():
    """Issue #414: Kein Modul außer ``theme`` bäckt einen Akzent-Hexwert ein.

    Akzentfarben kommen ausschließlich aus der Palette; Widgets referenzieren
    Tokens, nie den rohen Hexwert. Der Scan deckt das Paket (ohne ``theme.py``)
    und ``scripts`` ab – die lint-relevanten Quellbäume.
    """
    accents = _accent_hexes()
    assert accents, "Erwartet mindestens einen Akzent-Hexwert in der Palette."
    scripts = Path(__file__).resolve().parent.parent / "scripts"
    sources = [p for p in sorted(_PKG.glob("*.py")) if p.name != "theme.py"]
    sources += sorted(scripts.glob("*.py"))
    offenders: list[str] = []
    for path in sources:
        text = path.read_text(encoding="utf-8").lower()
        offenders += [f"{path.name}: {hexval}" for hexval in accents if hexval in text]
    assert not offenders, "Hartkodierte Akzent-Hexwerte: " + ", ".join(offenders)


def test_dead_style_constants_not_reintroduced():
    # BTN_STYLE/GRP_STYLE waren toter Code (nirgends referenziert) und
    # wurden entfernt – nicht erneut anlegen.
    assert not hasattr(bgremover, "BTN_STYLE")
    assert not hasattr(bgremover, "GRP_STYLE")
    assigned = _pkg_assigned_names()
    assert "BTN_STYLE" not in assigned
    assert "GRP_STYLE" not in assigned


# ── Drift-Schutz: theme.py vs. docs/REDESIGN_SPEC.md (#480) ─────────────────
#
# REDESIGN_SPEC.md §2/§3 beansprucht, die maßgebliche Wertquelle zu sein –
# das gilt nur, wenn Code und Doku garantiert nicht auseinanderlaufen können.
# Analog zum bestehenden Drift-Test-Muster des Projekts
# (``test_ci_qt_packages.py`` für die Qt-apt-Paketliste, CLAUDE.md „Wichtig:
# Drift-Disziplin") parst dieser Test die kanonischen Farb-Tabellen aus der
# Spec und vergleicht sie Feld für Feld gegen die echten ``DARK``/``LIGHT``-
# Paletten. Nur Tabellen mit der exakten Kopfzeile ``| Token | Wert | Rolle |``
# zählen als kanonisch – die separaten Vergleichstabellen (Epic-Übersicht,
# dokumentierte Restabweichung des hellen Schemas) nutzen bewusst andere
# Kopfzeilen und werden hier ignoriert.
_SPEC_PATH = Path(__file__).resolve().parent.parent / "docs" / "REDESIGN_SPEC.md"
_CANONICAL_HEADER = "| Token | Wert | Rolle |"


def _parse_canonical_color_table(section_text: str) -> dict[str, str]:
    """Extrahiert ``{token: wert}`` aus jeder kanonischen Tabelle im Abschnitt.

    Eine Tabellenzeile darf mehrere Token in einer Zelle bündeln
    (`` `panel` / `inspector` ``); teilen sie sich einen einzigen Wert (eine
    Werte-Zelle, mehrere Token-Zellen), gilt dieser für alle. Ansonsten müssen
    Token- und Wertanzahl je Zeile exakt übereinstimmen.
    """
    values: dict[str, str] = {}
    lines = section_text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() != _CANONICAL_HEADER:
            i += 1
            continue
        i += 2  # Kopfzeile + Trennzeile (|---|---|---|) überspringen
        while i < len(lines) and lines[i].strip().startswith("|"):
            cols = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if len(cols) >= 2:
                tokens = re.findall(r"`([^`]+)`", cols[0])
                cell_values = re.findall(r"`([^`]+)`", cols[1])
                if tokens and len(cell_values) == 1:
                    cell_values = cell_values * len(tokens)
                assert len(tokens) == len(cell_values), (
                    f"Token-/Wert-Anzahl passt nicht zusammen: {lines[i]!r}")
                values.update(zip(tokens, cell_values, strict=True))
            i += 1
    return values


def _spec_sections() -> tuple[str, str]:
    """Liefert die Rohtexte von §2 (dunkel) und §3 (hell) aus der Spec-Datei."""
    text = _SPEC_PATH.read_text(encoding="utf-8")
    start = text.index("## §2 Farb-Tokens")
    mid = text.index("## §3 Farb-Tokens", start)
    end = text.index("## §4 Typografie", mid)
    return text[start:mid], text[mid:end]


def test_redesign_spec_color_tables_match_theme_palettes():
    """#480: REDESIGN_SPEC.md §2/§3 dürfen nie von ``theme.DARK``/``LIGHT``
    abweichen – dieser Test schlägt fehl, sobald jemand nur die Palette oder
    nur die Doku ändert, ohne die jeweils andere Seite nachzuziehen."""
    from dataclasses import fields

    from bgremover.theme import DARK, LIGHT

    sec2, sec3 = _spec_sections()
    dark_documented = _parse_canonical_color_table(sec2)
    light_documented = _parse_canonical_color_table(sec3)

    all_fields = {f.name for f in fields(DARK)} - {"is_dark"}
    for name, documented, palette in (
        ("DARK", dark_documented, DARK), ("LIGHT", light_documented, LIGHT),
    ):
        missing = all_fields - documented.keys()
        assert not missing, f"§{'2' if name == 'DARK' else '3'}: undokumentierte Token {missing}"
        extra = documented.keys() - all_fields
        assert not extra, f"§{'2' if name == 'DARK' else '3'}: unbekannte Token {extra}"
        mismatches = {
            token: (documented[token], getattr(palette, token))
            for token in documented
            if documented[token] != getattr(palette, token)
        }
        assert not mismatches, (
            f"theme.{name} weicht von REDESIGN_SPEC.md ab (Spec-Wert, Code-Wert): "
            f"{mismatches}")


# ── Drift-Schutz: theme.py vs. Prototyp-Bundle direkt (#480, optional) ──────
#
# Dritte Ecke des Dreiecks Prototyp ↔ Spec ↔ Code: die vorige Prüfung sichert
# nur Spec↔Code ab. Dieser Test liest die tatsächlich eingebetteten
# CSS-Variablen aus dem Prototyp-Bundle und vergleicht sie direkt gegen
# ``theme.DARK`` – nur das dunkle Schema, denn das helle wurde in diesem Epic
# bewusst nicht Zeile für Zeile angeglichen (Nicht-Ziel von #474/#480, siehe
# die dokumentierte Restabweichung in REDESIGN_SPEC.md §3).
_PROTOTYPE_PATH = (
    Path(__file__).resolve().parent.parent
    / "design" / "Prototyp A - Geführter Workflow.dc.html")

# CSS-Custom-Property → Palette-Feld. Nur Variablen mit einem echten
# Palette-Gegenstück; die übrigen (s. u.) sind dokumentierte Ausnahmen.
_PROTOTYPE_VAR_TO_FIELD = {
    "--bg": "bg", "--stepper": "stepper", "--nav": "nav", "--status": "status",
    "--rail": "toolbar", "--inspector": "inspector",
    "--border": "border", "--border-2": "border_2", "--hairline": "hairline",
    "--text": "text", "--text-2": "text2", "--text-3": "text3", "--muted": "muted",
    "--label": "label",
    "--accent": "accent", "--accent-2": "accent2", "--accent-soft": "accent_soft",
    "--accent-line": "accent_line", "--accent-text": "accent_text",
    "--accent-shadow": "accent_shadow",
    "--surface": "surface", "--surface-hover": "surface_hover", "--hover": "hover",
    "--inset": "inset", "--card": "card_bg", "--card-border": "card_border",
    "--checker-a": "checker_a", "--checker-b": "checker_b",
    "--glass": "glass",
    "--good": "good", "--good-soft": "good_soft", "--good-line": "good_line",
    "--bad": "bad", "--bad-soft": "bad_soft",
}
# Prototyp-Variablen ohne Palette-Gegenstück – jeweils bewusst, nicht vergessen:
# --titlebar/--menubar (App nutzt natives Fenster-Chrome bzw. den toolbar-Ton
# für QMenuBar, §2), --amber/--amber-2/--amber-shadow/--coral (keine
# Amber-/Coral-Sonderfarben, Issue #416).
_PROTOTYPE_VARS_WITHOUT_FIELD = {
    "--titlebar", "--menubar", "--amber", "--amber-2", "--amber-shadow", "--coral",
}
# Das dunkle Schema soll die Prototyp-Tokens direkt übernehmen; bewusste
# Ausnahmen werden über _PROTOTYPE_VARS_WITHOUT_FIELD statt über Feld-Drift
# dokumentiert.
_DARK_ALLOWED_DRIFT: set[str] = set()


def _prototype_dark_root_vars() -> dict[str, str]:
    """Liest die ``--*``-Variablen des **dunklen** ``:root``-Blocks aus dem
    Prototyp-Bundle. Das Bundle enthält zwei Blöcke (dunkel, dann hell); ein
    zweites Auftreten von ``--bg`` markiert den Beginn des hellen Blocks.
    """
    text = _PROTOTYPE_PATH.read_text(encoding="utf-8")
    pairs = re.findall(r"(--[a-zA-Z0-9-]+):\s*([^;]+);", text)
    bg_positions = [i for i, (k, _v) in enumerate(pairs) if k == "--bg"]
    assert len(bg_positions) >= 2, "Erwarte zwei :root-Blöcke (dunkel, hell) im Bundle"
    return dict(pairs[:bg_positions[1]])


def test_dark_palette_matches_prototype_bundle_directly():
    """#480 (optional): ``theme.DARK`` direkt gegen die im Prototyp-Bundle
    eingebetteten CSS-Variablen geprüft – unabhängig von REDESIGN_SPEC.md.
    Verhindert, dass Spec und Code gemeinsam vom Prototyp abdriften.
    """
    from bgremover.theme import DARK

    prototype_vars = _prototype_dark_root_vars()
    checked = _PROTOTYPE_VAR_TO_FIELD.keys() | _PROTOTYPE_VARS_WITHOUT_FIELD
    unexpected = prototype_vars.keys() - checked
    assert not unexpected, (
        f"Neue Prototyp-Variablen ohne Zuordnung: {unexpected} – "
        "in _PROTOTYPE_VAR_TO_FIELD aufnehmen oder als bewusste Ausnahme "
        "in _PROTOTYPE_VARS_WITHOUT_FIELD dokumentieren.")

    mismatches = {}
    for css_var, field in _PROTOTYPE_VAR_TO_FIELD.items():
        prototype_value = prototype_vars[css_var].replace(" ", "")
        actual = getattr(DARK, field).replace(" ", "")
        if prototype_value != actual and field not in _DARK_ALLOWED_DRIFT:
            mismatches[css_var] = (prototype_value, actual)
    assert not mismatches, (
        f"theme.DARK weicht vom Prototyp ab (Prototyp-Wert, Code-Wert): {mismatches}")
