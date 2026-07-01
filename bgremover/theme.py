"""Zentrale UI-Farbpalette und davon abhängige Stylesheet-Vorlagen.

``_Theme`` und die beiden f-Strings ``TOOL_STYLE``/``SLD_STYLE`` bleiben
bewusst zusammen (die f-Strings werden beim Import ausgewertet und
referenzieren ``_Theme``).
"""
from __future__ import annotations


class _Theme:
    """Zentrale UI-Farbpalette.

    Bündelt die gemeinsam genutzten Farbwerte an einer Stelle, damit
    UI-Erweiterungen konsistente Farben nutzen.
    """
    ACCENT      = "#4a90d9"   # Hervorhebung: aktiver Tab, Slider, Auswahl
    BG_PANEL    = "#1a1a1a"   # rechtes Panel / Tab-Pane / Statusleiste
    BG_TABBAR   = "#141414"   # Tab-Leisten-Hintergrund
    BORDER      = "#3a3a3a"   # Rahmen / Trennlinien / Slider-Groove
    DIVIDER     = "#2a2a2a"   # dünne Trennflächen
    TEXT_BRIGHT = "#e0e0e0"   # heller Text (aktiver Tab)

    # ── Redesign „Geführter Workflow" (Epic #413/#418) ──────────────────
    # Vom Akzent abgeleitete Zustandsfarben; ein einziges Blau für alle
    # Sektionsköpfe, Schrittleiste und Primär-Buttons (Befund: kein Amber/Coral).
    ACCENT_SOFT   = "rgba(74,144,217,.16)"   # aktiver Hintergrund (Karte/Schritt)
    ACCENT_LINE   = "rgba(74,144,217,.42)"   # aktiver Rahmen / Verbinder
    ACCENT_TEXT   = "#9fc0ff"                # Text auf accent-soft
    ACCENT_2      = "#3f7fce"                # Verlauf-Endpunkt Primärbutton
    ACCENT_SHADOW = "rgba(74,144,217,.35)"   # Button-Schatten/Glow
    CARD_BG       = "#22262d"                # Karten-Hintergrund
    CARD_BORDER   = "rgba(255,255,255,.07)"  # Karten-Rahmen
    STEPPER_BG    = "#161a20"                # Schrittleiste
    NAV_BG        = "#20252e"                # Navigations-Fußzeile
    MUTED         = "#727b89"                # inaktiv / ausstehender Schritt
    TEXT_3        = "#8b94a2"                # Tertiärtext / Hinweise


# Karten-Container (Epic #413, Issue #415): jede Sektion sitzt in einer Karte
# mit dünnem Rahmen und abgerundeten Ecken. Ein einziger Radius/Innenabstand.
CARD_STYLE = (
    f"background: {_Theme.CARD_BG}; border: 1px solid {_Theme.CARD_BORDER};"
    " border-radius: 12px;"
)

# Sektionskopf (Issue #416): blauer Akzentstrich + Versalien-Titel. Immer Blau.
SECTION_HEADER_STYLE = (
    f"color: {_Theme.TEXT_BRIGHT}; font-size: 12px; font-weight: bold;"
    " letter-spacing: .04em; background: transparent;"
    f" padding: 2px 0 4px 8px; border-left: 3px solid {_Theme.ACCENT};"
)

# Primärbutton (Issue #415/#421): blauer Verlauf, weißer Text.
PRIMARY_BTN_STYLE = f"""
    QPushButton {{
        background: qlineargradient(x1:0 y1:0 x2:0 y2:1,
            stop:0 {_Theme.ACCENT}, stop:1 {_Theme.ACCENT_2});
        color: #fff; border: none; border-radius: 9px;
        font-size: 13px; font-weight: 600; min-height: 40px; padding: 0 12px;
    }}
    QPushButton:hover {{ background: {_Theme.ACCENT}; }}
    QPushButton:disabled {{ background: #2b2f36; color: #6b7079; }}
"""

# Schrittleiste (Epic #418, Issue #419): Container-Hintergrund.
STEPPER_STYLE = f"background: {_Theme.STEPPER_BG}; border-bottom: 1px solid {_Theme.BORDER};"

# Navigations-Fußzeile im Inspector (Issue #421).
NAV_BAR_STYLE = f"background: {_Theme.NAV_BG}; border-top: 1px solid {_Theme.BORDER};"
NAV_BACK_STYLE = f"""
    QPushButton {{
        background: transparent; color: {_Theme.TEXT_BRIGHT};
        border: 1px solid {_Theme.BORDER}; border-radius: 9px;
        font-size: 13px; padding: 0 14px; min-height: 36px;
    }}
    QPushButton:hover {{ border-color: {_Theme.ACCENT}; }}
    QPushButton:disabled {{ color: {_Theme.MUTED}; border-color: {_Theme.DIVIDER}; }}
"""
NAV_NEXT_STYLE = f"""
    QPushButton {{
        background: {_Theme.ACCENT}; color: #fff; border: none;
        border-radius: 9px; font-size: 13px; font-weight: 600; min-height: 36px;
    }}
    QPushButton:hover {{ background: {_Theme.ACCENT_2}; }}
"""


TOOL_STYLE = f"""
    QToolButton {{
        color: #ccc; font-size: 24px; border: none;
        border-radius: 9px; background: {_Theme.BORDER};
    }}
    QToolButton:checked        {{ background: {_Theme.ACCENT}; color: white; }}
    QToolButton:hover          {{ background: #4f4f4f; }}
    QToolButton:checked:hover  {{ background: {_Theme.ACCENT}; color: white; }}
    QToolButton:disabled       {{ color: #555; background: {_Theme.DIVIDER}; }}
"""

SLD_STYLE = f"""
    QSlider::groove:horizontal {{ height: 4px; background: {_Theme.BORDER}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        background: {_Theme.ACCENT}; width: 14px; height: 14px;
        margin: -5px 0; border-radius: 7px;
    }}
"""

STATUS_BAR_STYLE = (
    "QStatusBar { background:#1a1a1a; color:#777; font-size:11px; border-top:1px solid #333; }"
)
CANVAS_CONTAINER_STYLE = "background: transparent;"
TOOLBAR_FRAME_STYLE = "QFrame { background: #242424; border-right: 1px solid #3a3a3a; }"
CROP_BAR_STYLE = "QFrame { background: #1e3020; border-bottom: 1px solid #3a7a4a; }"
CROP_LABEL_STYLE = "color: #8fdd9f; font-size: 12px; font-weight: bold; background: transparent;"
CROP_CONFIRM_STYLE = (
    "QPushButton { background:#2a6a2a; color:white; border:none;"
    " border-radius:5px; padding:7px 16px; font-size:12px; font-weight:bold; }"
    "QPushButton:hover { background:#3a8a3a; }"
)
CROP_CANCEL_STYLE = (
    "QPushButton { background:#5a2525; color:white; border:none;"
    " border-radius:5px; padding:7px 14px; font-size:12px; }"
    "QPushButton:hover { background:#7a3535; }"
)
HISTORY_BUTTON_STYLE = """
    QToolButton {
        color: #bbb; font-size: 20px; border: none;
        border-radius: 9px; background: #2e2e2e;
    }
    QToolButton:hover    { background: #3e3e3e; }
    QToolButton:pressed  { background: #252525; }
    QToolButton:disabled { color: #444; background: #222; }
"""
SETTINGS_TITLE_STYLE = "font-size: 15px; font-weight: bold;"
