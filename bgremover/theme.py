"""Zentrale UI-Farbpalette und davon abhängige Stylesheet-Vorlagen.

Verbatim aus ``BgRemover.py`` verschoben (Runde 5, Phase B – Schritt 5).
``_Theme`` und die beiden f-Strings ``TOOL_STYLE``/``SLD_STYLE`` bleiben
bewusst zusammen (die f-Strings werden beim Import ausgewertet und
referenzieren ``_Theme``). Keine Verhaltensänderung.
"""
from __future__ import annotations


class _Theme:
    """Zentrale UI-Farbpalette.

    Bündelt die im Stylesheet mehrfach wiederholten Farbwerte an einer
    Stelle, damit künftige UI-Erweiterungen konsistente Farben nutzen.
    Die Werte sind exakt die zuvor inline verwendeten – das
    Erscheinungsbild ändert sich nicht (Stylesheets bleiben
    byte-identisch).
    """
    ACCENT      = "#4a90d9"   # Hervorhebung: aktiver Tab, Slider, Auswahl
    BG_PANEL    = "#1a1a1a"   # rechtes Panel / Tab-Pane / Statusleiste
    BG_TABBAR   = "#141414"   # Tab-Leisten-Hintergrund
    BORDER      = "#3a3a3a"   # Rahmen / Trennlinien / Slider-Groove
    DIVIDER     = "#2a2a2a"   # dünne Trennflächen
    TEXT_BRIGHT = "#e0e0e0"   # heller Text (aktiver Tab)


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
