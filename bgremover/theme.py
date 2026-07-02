"""Zentrale UI-Farbpalette, Token-System (hell/dunkel) und Stylesheet-Vorlagen.

Das Redesign (Epic #424) führt ein token-basiertes Theming ein: :class:`Palette`
bündelt alle Rollen (Hintergründe, Text, Akzent, Karten …) für ein Schema;
``DARK``/``LIGHT`` sind die beiden Ausprägungen. ``build_qpalette`` liefert die
passende ``QPalette`` (Standard-Widgets/Dialoge), ``build_app_stylesheet`` das
anwendungsweite QSS für die Redesign-Chrome (über Objektnamen/Typ-Selektoren) –
so schaltet ein einziges ``app.setStyleSheet`` das ganze Erscheinungsbild um.

``_Theme`` und die ``*_STYLE``-Konstanten bleiben als dunkle Rückwärts-
kompatibilität erhalten (Tests/Imports); die laufende Umschaltung nutzt jedoch
die Palette-Builder.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """Alle Farb-Tokens eines Schemas (§2/§3 der Spezifikation)."""

    # Fensterregionen
    bg: str
    panel: str
    inspector: str
    tabbar: str
    stepper: str
    nav: str
    status: str
    toolbar: str
    # Linien / Flächen
    border: str
    divider: str
    hairline: str
    surface: str
    surface_hover: str
    hover: str
    card_bg: str
    card_border: str
    # Text. Vertrag (#441): ``text``/``text2``/``text3`` sind für **aktiven** Text
    # gedacht und halten ≥ 4.5:1 auf ihren Flächen; ``muted`` ist ausschließlich
    # für Disabled-/Placeholder-Zustände reserviert (WCAG-1.4.3-Ausnahme).
    text: str
    text2: str
    text3: str
    muted: str
    # Akzent
    accent: str
    accent2: str
    accent_soft: str
    accent_line: str
    accent_text: str
    accent_shadow: str
    on_accent: str
    # Semantik
    good: str
    good_soft: str
    bad: str
    bad_soft: str
    # Schema-Kennung
    is_dark: bool


DARK = Palette(
    bg="#1f242b", panel="#1a1a1a", inspector="#1a1a1a", tabbar="#141414",
    stepper="#161a20", nav="#20252e", status="#1a1a1a", toolbar="#242424",
    border="#3a3a3a", divider="#2a2a2a", hairline="#333333",
    surface="#2a2a2a", surface_hover="#363636", hover="rgba(255,255,255,.06)",
    card_bg="#22262d", card_border="rgba(255,255,255,.07)",
    text="#e0e0e0", text2="#cdd4de", text3="#8b94a2", muted="#727b89",
    accent="#4a90d9", accent2="#3f7fce", accent_soft="rgba(74,144,217,.16)",
    accent_line="rgba(74,144,217,.42)", accent_text="#9fc0ff",
    accent_shadow="rgba(74,144,217,.35)", on_accent="#ffffff",
    good="#7fe0aa", good_soft="rgba(80,200,140,.16)",
    bad="#f29aa6", bad_soft="rgba(229,104,122,.16)",
    is_dark=True,
)

LIGHT = Palette(
    bg="#e9edf3", panel="#f2f4f8", inspector="#f5f7fb", tabbar="#e6eaf1",
    stepper="#eef1f6", nav="#eaeef3", status="#dee3eb", toolbar="#e6eaf1",
    border="#c9d2df", divider="#dbe1ea", hairline="#d4dae4",
    surface="#ffffff", surface_hover="#eef1f6", hover="rgba(22,32,52,.06)",
    card_bg="#ffffff", card_border="rgba(22,32,52,.10)",
    # text3 bewusst dunkler als die frühere Wahl (#69727f): erst damit erreicht
    # Hinweistext auch auf der hellen Statusleiste ≥ 4.5:1 (WCAG AA, #441).
    text="#1b2230", text2="#3a4351", text3="#59626f", muted="#8b95a3",
    accent="#3a6fd0", accent2="#2f5fcf", accent_soft="rgba(58,111,208,.14)",
    accent_line="rgba(58,111,208,.34)", accent_text="#2f5fcf",
    accent_shadow="rgba(58,111,208,.26)", on_accent="#ffffff",
    good="#1f9d63", good_soft="rgba(31,157,99,.14)",
    bad="#d65060", bad_soft="rgba(214,80,96,.13)",
    is_dark=False,
)

# Aktives Schema (prozesslokal). Wird vom App-Start/Umschalter gesetzt.
_active: Palette = DARK


def active_palette() -> Palette:
    """Gibt die aktive Palette zurück (Default dunkel)."""
    return _active


def set_active_palette(palette: Palette) -> None:
    """Setzt die aktive Palette (Chrome-Neubau/Restyle liegt beim Aufrufer)."""
    global _active
    _active = palette


def palette_for(mode: str) -> Palette:
    """``"light"`` → :data:`LIGHT`, sonst :data:`DARK`."""
    return LIGHT if str(mode).lower() == "light" else DARK


# ── Palette-parametrierte Stil-Bausteine (für die Redesign-Chrome) ──────────

def card_style(p: Palette) -> str:
    return (f"background: {p.card_bg}; border: 1px solid {p.card_border};"
            " border-radius: 12px;")


def section_header_style(p: Palette) -> str:
    """Kartenkopf-Titel (§5.2): 11 px/700, VERSALIEN (Aufrufer setzen ``.upper()``),
    blauer Akzentstrich links – immer Akzentfarbe, nie Amber/Coral (Issue #416)."""
    return (f"color: {p.text2}; font-size: 11px; font-weight: bold;"
            " letter-spacing: .05em; background: transparent;"
            f" padding: 2px 0 4px 8px; border-left: 3px solid {p.accent};")


def primary_btn_style(p: Palette) -> str:
    return f"""
    QPushButton {{
        background: qlineargradient(x1:0 y1:0 x2:0 y2:1,
            stop:0 {p.accent}, stop:1 {p.accent2});
        color: {p.on_accent}; border: none; border-radius: 9px;
        font-size: 13px; font-weight: 600; min-height: 40px; padding: 0 12px;
    }}
    QPushButton:hover {{ background: {p.accent}; }}
    QPushButton:focus {{ outline: none; border: 2px solid {p.on_accent}; }}
    QPushButton:disabled {{ background: {p.surface}; color: {p.muted}; }}
"""


def stepper_style(p: Palette) -> str:
    return f"background: {p.stepper}; border-bottom: 1px solid {p.border};"


def nav_bar_style(p: Palette) -> str:
    return f"background: {p.nav}; border-top: 1px solid {p.border};"


def nav_back_style(p: Palette) -> str:
    return f"""
    QPushButton {{
        background: transparent; color: {p.text2};
        border: 1px solid {p.border}; border-radius: 9px;
        font-size: 13px; padding: 0 12px; min-height: 36px;
    }}
    QPushButton:hover {{ border-color: {p.accent}; }}
    QPushButton:focus {{ outline: none; border: 2px solid {p.accent}; }}
    QPushButton:disabled {{ color: {p.muted}; border-color: {p.divider}; }}
"""


def nav_next_style(p: Palette) -> str:
    return f"""
    QPushButton {{
        background: {p.accent}; color: {p.on_accent}; border: none;
        border-radius: 9px; font-size: 13px; font-weight: 600; min-height: 36px;
    }}
    QPushButton:hover {{ background: {p.accent2}; }}
    QPushButton:focus {{ outline: none; border: 2px solid {p.on_accent}; }}
"""


def panel_frame_style(p: Palette) -> str:
    return f"QFrame {{ background: {p.inspector}; border-left: 1px solid {p.border}; }}"


def scroll_style(p: Palette) -> str:
    return f"""
    QScrollArea {{ background: {p.inspector}; border: none; }}
    QScrollBar:vertical {{ background: {p.inspector}; width: 6px; margin: 0; }}
    QScrollBar::handle:vertical {{
        background: {p.border}; border-radius: 3px; min-height: 20px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


def panel_btn_style(p: Palette) -> str:
    """Sekundärbutton der Inspector-Karten (neutrale Fläche, §5.3)."""
    return f"""
    QPushButton {{
        background: {p.surface}; color: {p.text2}; border: 1px solid {p.border};
        border-radius: 8px; padding: 0 10px; font-size: 12px; min-height: 34px;
    }}
    QPushButton:hover {{ background: {p.surface_hover}; }}
    QPushButton:focus {{ outline: none; border: 1px solid {p.accent}; }}
    QPushButton:disabled {{ background: {p.divider}; color: {p.muted}; }}
"""


def num_style(p: Palette) -> str:
    """Zahlenfelder/Combos in den Inspector-Karten (Trefferfläche ≥ 24 px, #441)."""
    return (
        f"QSpinBox, QComboBox {{ background:{p.surface}; color:{p.text};"
        f" border:1px solid {p.border}; border-radius:6px; padding:3px 6px;"
        " font-size:12px; min-height:24px; }"
        f" QSpinBox:focus, QComboBox:focus {{ border:1px solid {p.accent}; }}"
        f" QComboBox QAbstractItemView {{ background:{p.surface}; color:{p.text}; }}"
    )


def slider_style(p: Palette) -> str:
    """Slider: Klickziel ist der gesamte Groove; der Fokus markiert den Griff (#441)."""
    return f"""
    QSlider::groove:horizontal {{ height: 4px; background: {p.border}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        background: {p.accent}; width: 14px; height: 14px;
        margin: -5px 0; border-radius: 7px;
    }}
    QSlider::handle:horizontal:focus {{ border: 2px solid {p.text}; }}
"""


def tool_style(p: Palette) -> str:
    """Werkzeug-Button der linken Leiste (§5.9): ruht transparent in der Leiste,
    aktiv nur sanft akzent-getönt (kein voller Farbfüllton wie beim Primärbutton).
    """
    return f"""
    QToolButton {{
        color: {p.text3}; font-size: 20px; border: 1px solid transparent;
        border-radius: 10px; background: transparent;
    }}
    QToolButton:checked        {{ background: {p.accent_soft}; border-color: {p.accent_line}; color: {p.accent_text}; }}
    QToolButton:hover          {{ background: {p.hover}; color: {p.text2}; }}
    QToolButton:checked:hover  {{ background: {p.accent_soft}; border-color: {p.accent_line}; color: {p.accent_text}; }}
    QToolButton:focus          {{ outline: none; border: 1px solid {p.accent}; }}
    QToolButton:checked:focus  {{ border: 2px solid {p.accent}; }}
    QToolButton:disabled       {{ color: {p.muted}; background: transparent; }}
"""


def status_bar_style(p: Palette) -> str:
    return (f"QStatusBar {{ background:{p.status}; color:{p.text3};"
            f" font-size:11px; border-top:1px solid {p.border}; }}")


def toolbar_frame_style(p: Palette) -> str:
    return f"QFrame {{ background: {p.toolbar}; border-right: 1px solid {p.border}; }}"


def menu_style(p: Palette) -> str:
    return f"""
    QMenuBar {{ background: {p.status}; color: {p.text2}; }}
    QMenuBar::item:selected {{ background: {p.surface_hover}; }}
    QMenu {{ background: {p.surface}; color: {p.text2}; border: 1px solid {p.border}; }}
    QMenu::item:selected {{ background: {p.accent}; color: {p.on_accent}; }}
"""


def history_button_style(p: Palette) -> str:
    return f"""
    QToolButton {{
        color: {p.text3}; font-size: 20px; border: none;
        border-radius: 9px; background: {p.surface};
    }}
    QToolButton:hover    {{ background: {p.surface_hover}; }}
    QToolButton:pressed  {{ background: {p.divider}; }}
    QToolButton:focus    {{ outline: none; border: 1px solid {p.accent}; }}
    QToolButton:disabled {{ color: {p.muted}; background: {p.divider}; }}
"""


def build_app_stylesheet(p: Palette) -> str:
    """Anwendungsweites QSS für die Redesign-Chrome (Objektnamen/Typen).

    Kombiniert mit :func:`build_qpalette` (Standard-Widgets/Dialoge) themt dies
    die gesamte sichtbare Oberfläche; ein Umschalten ist ein einzelnes
    ``app.setStyleSheet`` + ``app.setPalette`` – ohne Neustart (#428).
    """
    return f"""
    QFrame#sectionCard, QFrame#recentCard {{
        background: {p.card_bg}; border: 1px solid {p.card_border};
        border-radius: 12px;
    }}
    QLabel#sectionHeader {{
        color: {p.text2}; font-size: 11px; font-weight: bold;
        letter-spacing: .05em; background: transparent; padding: 2px 0 4px 8px;
        border-left: 3px solid {p.accent};
    }}
    QFrame#inspectorPanel {{ background: {p.inspector}; border-left: 1px solid {p.border}; }}
    QWidget#stepPage, QWidget#inspectorHeader {{ background: {p.inspector}; }}
    /* Fokusring für Tastaturbedienung (#429) */
    QPushButton:focus, QToolButton:focus, QComboBox:focus, QSpinBox:focus,
    QCheckBox:focus, QSlider:focus {{
        outline: none; border: 1px solid {p.accent};
    }}
    QToolTip {{
        background: {p.surface}; color: {p.text};
        border: 1px solid {p.border};
    }}
    """


def build_qpalette(p: Palette):  # -> QPalette (Import lokal, Qt-frei halten)
    """Baut die ``QPalette`` für ein Schema (Standard-Widgets + Dialoge)."""
    from PyQt6.QtGui import QColor, QPalette

    def c(spec: str) -> QColor:
        return QColor(spec)

    pal = QPalette()
    R = QPalette.ColorRole
    pal.setColor(R.Window, c(p.bg))
    pal.setColor(R.WindowText, c(p.text))
    pal.setColor(R.Base, c(p.surface if p.is_dark else "#ffffff"))
    pal.setColor(R.AlternateBase, c(p.card_bg))
    pal.setColor(R.Text, c(p.text))
    pal.setColor(R.Button, c(p.surface))
    pal.setColor(R.ButtonText, c(p.text))
    pal.setColor(R.Highlight, c(p.accent))
    pal.setColor(R.HighlightedText, c(p.on_accent))
    pal.setColor(R.ToolTipBase, c(p.surface))
    pal.setColor(R.ToolTipText, c(p.text))
    pal.setColor(R.PlaceholderText, c(p.muted))
    disabled = QPalette.ColorGroup.Disabled
    pal.setColor(disabled, R.WindowText, c(p.muted))
    pal.setColor(disabled, R.Text, c(p.muted))
    pal.setColor(disabled, R.ButtonText, c(p.muted))
    return pal


class _Theme:
    """Zentrale UI-Farbpalette (dunkle Rückwärtskompatibilität).

    Bündelt die gemeinsam genutzten Farbwerte an einer Stelle; die kanonischen
    Werte sind vertraglich (siehe ``tests/test_theme.py``). Neues Theming läuft
    über :class:`Palette`/:func:`active_palette`.
    """
    ACCENT      = "#4a90d9"   # Hervorhebung: aktiver Tab, Slider, Auswahl
    BG_PANEL    = "#1a1a1a"   # rechtes Panel / Tab-Pane / Statusleiste
    BG_TABBAR   = "#141414"   # Tab-Leisten-Hintergrund
    BORDER      = "#3a3a3a"   # Rahmen / Trennlinien / Slider-Groove
    DIVIDER     = "#2a2a2a"   # dünne Trennflächen
    TEXT_BRIGHT = "#e0e0e0"   # heller Text (aktiver Tab)

    ACCENT_SOFT   = DARK.accent_soft
    ACCENT_LINE   = DARK.accent_line
    ACCENT_TEXT   = DARK.accent_text
    ACCENT_2      = DARK.accent2
    ACCENT_SHADOW = DARK.accent_shadow
    CARD_BG       = DARK.card_bg
    CARD_BORDER   = DARK.card_border
    STEPPER_BG    = DARK.stepper
    NAV_BG        = DARK.nav
    MUTED         = DARK.muted
    TEXT_3        = DARK.text3


# ── Rückwärtskompatible, dunkel gebaute Konstanten (Tests/Alt-Imports) ──────
CARD_STYLE = card_style(DARK)
SECTION_HEADER_STYLE = section_header_style(DARK)
PRIMARY_BTN_STYLE = primary_btn_style(DARK)
STEPPER_STYLE = stepper_style(DARK)
NAV_BAR_STYLE = nav_bar_style(DARK)
NAV_BACK_STYLE = nav_back_style(DARK)
NAV_NEXT_STYLE = nav_next_style(DARK)
TOOL_STYLE = tool_style(DARK)
SLD_STYLE = slider_style(DARK)
STATUS_BAR_STYLE = status_bar_style(DARK)
CANVAS_CONTAINER_STYLE = "background: transparent;"
TOOLBAR_FRAME_STYLE = toolbar_frame_style(DARK)
HISTORY_BUTTON_STYLE = history_button_style(DARK)
CROP_BAR_STYLE = "QFrame { background: #1e3020; border-bottom: 1px solid #3a7a4a; }"
CROP_LABEL_STYLE = "color: #8fdd9f; font-size: 12px; font-weight: bold; background: transparent;"
CROP_CONFIRM_STYLE = (
    "QPushButton { background:#2a6a2a; color:white; border:none;"
    " border-radius:5px; padding:7px 16px; font-size:12px; font-weight:bold; }"
    "QPushButton:hover { background:#3a8a3a; }"
    "QPushButton:focus { outline:none; border:2px solid #ffffff; }"
)
CROP_CANCEL_STYLE = (
    "QPushButton { background:#5a2525; color:white; border:none;"
    " border-radius:5px; padding:7px 14px; font-size:12px; }"
    "QPushButton:hover { background:#7a3535; }"
    "QPushButton:focus { outline:none; border:2px solid #ffffff; }"
)
SETTINGS_TITLE_STYLE = "font-size: 15px; font-weight: bold;"
