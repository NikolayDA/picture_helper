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
