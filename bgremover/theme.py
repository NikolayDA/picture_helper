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
    border_2: str
    divider: str
    hairline: str
    surface: str
    surface_hover: str
    hover: str
    # Rezessierte/eingelassene Fläche (Prototyp ``--inset``, z. B. Container
    # des Vorschau-Segmented-Controls) – nicht zu verwechseln mit ``surface``
    # (erhabene Bedienflächen wie Buttons/Inputs).
    inset: str
    card_bg: str
    card_border: str
    # Canvas-Transparenz-Schachbrett (Prototyp ``--checker-a``/``--checker-b``,
    # #478) – schemaeigen statt fest kodiertem Grau, damit es sich im Dark
    # Mode nicht als heller Fleck von der restlichen UI absetzt.
    checker_a: str
    checker_b: str
    # Halbtransparente „Glas"-Fläche für schwebende Canvas-Overlays (#464).
    glass: str
    # Text. Vertrag (#441/#496): ``text``/``text2``/``text3`` sind für aktiven
    # Text gedacht und halten ≥ 4.5:1 auf den geprüften Einsatzflächen;
    # ``muted`` ist ausschließlich für Disabled-/Placeholder-Zustände reserviert
    # (WCAG-1.4.3-Ausnahme).
    text: str
    text2: str
    text3: str
    muted: str
    # Gedämpfte Feldbeschriftung (Prototyp ``--label``, heller als ``text3``,
    # dunkler als ``text``). Im Prototyp selbst aktuell ungenutzt – die dortige
    # ``.lab``-Feldbeschriftungsklasse greift auf ``text2``, nicht ``label``.
    # Nur der Vollständigkeit halber übernommen (#479); kein App-Verbraucher.
    label: str
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
    # Rand-Ton zu good/good_soft (Prototyp ``--good-line``, analog zu
    # accent_line). Im Prototyp nur am Canvas-Erfolgs-Badge nach der
    # KI-Freistellung genutzt („✓ Hintergrund entfernt"), das es in der App
    # noch nicht gibt – Token ohne Verbraucher übernommen (#479).
    good_line: str
    bad: str
    bad_soft: str
    # Schema-Kennung
    is_dark: bool


DARK = Palette(
    # Hintergrundflächen 1:1 aus dem Prototyp (design/Prototyp A - Geführter
    # Workflow.dc.html, dunkler :root-Block) übernommen (#475) – ein kühler
    # Blaugrau-Ton statt des früheren neutralen Nah-Schwarz. ``status`` deckt
    # bewusst nur die Statusleiste ab; die Menüleiste teilt sich stattdessen
    # (wie im Prototyp: ``--menubar`` == ``--rail``) den ``toolbar``-Ton
    # (``menu_style``). Eine reine Fenster-Titelleiste gibt es im Qt-Fenster
    # (natives Chrome) nicht.
    bg="#1f242b", panel="#272d36", inspector="#272d36", tabbar="#141414",
    stepper="#1c2128", nav="#222831", status="#1a1e24", toolbar="#242a32",
    # border/hairline als teiltransparente Weiß-Overlays statt opaker
    # Grautöne (#476) – setzen sich je nach Untergrund unterschiedlich ab,
    # wie im Prototyp. border_2 ist der sekundäre Rand-Ton (u. a. neutrale
    # Sekundärbuttons, ``panel_btn_style`` – Prototyp-Klasse ``.bs``).
    border="rgba(255,255,255,.06)", border_2="rgba(255,255,255,.12)",
    divider="#2a2a2a", hairline="rgba(255,255,255,.1)",
    surface="#30373f", surface_hover="#3a424c", hover="rgba(255,255,255,.05)",
    inset="#1c2128",
    # Karten übernehmen den Prototyp-Token ``--card`` direkt (#475/#496).
    card_bg="#2e353f", card_border="rgba(255,255,255,.07)",
    checker_a="#2c313a", checker_b="#353b45",
    glass="rgba(26,30,37,.82)",
    text="#e9edf3", text2="#cdd4de", text3="#8b94a2", muted="#727b89",
    label="#aeb6c2",
    # Akzent 1:1 aus dem Prototyp (#477): ein helleres, periwinkle-artiges
    # Blau statt des dumpferen früheren Tons – bildet Primärbutton-Verlauf,
    # aktive Werkzeuge/Stepper-Kreis, Slider-Griff und Fokusringe.
    accent="#5b8cff", accent2="#4f81f5", accent_soft="rgba(91,140,255,.16)",
    accent_line="rgba(91,140,255,.3)", accent_text="#9fc0ff",
    accent_shadow="rgba(79,129,245,.35)", on_accent="#ffffff",
    good="#7fe0aa", good_soft="rgba(80,200,140,.16)", good_line="rgba(80,200,140,.4)",
    bad="#f29aa6", bad_soft="rgba(229,104,122,.16)",
    is_dark=True,
)

LIGHT = Palette(
    # Seit #499 1:1 am hellen :root-Block des Prototyps (Restdrift aus
    # #474/#480 aufgelöst); einzige bewusste Ausnahme ist text3 (s. u.).
    bg="#e9edf3", panel="#f2f4f8", inspector="#f5f7fb", tabbar="#e6eaf1",
    stepper="#f1f4f8", nav="#eaeef3", status="#dee3eb", toolbar="#e6eaf1",
    # border/hairline wie im Prototyp als teiltransparente Blaugrau-Overlays
    # statt opaker Grautöne (Gegenstück zu #476 im dunklen Schema).
    border="rgba(22,32,52,.09)", border_2="rgba(22,32,52,.16)",
    divider="#dbe1ea", hairline="rgba(22,32,52,.11)",
    surface="#ffffff", surface_hover="#eef1f6", hover="rgba(22,32,52,.05)",
    inset="#e3e8ef",
    card_bg="#ffffff", card_border="rgba(22,32,52,.09)",
    checker_a="#dde2ea", checker_b="#eef1f5",
    glass="rgba(255,255,255,.86)",
    # text3 bewusst dunkler als der Prototyp-Wert (#69727f): erst damit erreicht
    # Hinweistext auch auf der hellen Statusleiste ≥ 4.5:1 (WCAG AA, #441).
    text="#1b2230", text2="#3a4351", text3="#59626f", muted="#8b95a3",
    label="#7b8492",
    accent="#3f6fe0", accent2="#3464d6", accent_soft="rgba(63,111,224,.12)",
    accent_line="rgba(63,111,224,.32)", accent_text="#2f5fcf",
    accent_shadow="rgba(63,111,224,.28)", on_accent="#ffffff",
    good="#1f9d63", good_soft="rgba(31,157,99,.14)", good_line="rgba(31,157,99,.4)",
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


# ── Karten-Metriken (§5.1 der Spezifikation) ────────────────────────────────
# Benannte Tokens für Radius, Innenpolster und Abstände der Inspector-Karten –
# die **einzige** Quelle dieser Maße (#414). Die Panels lesen ausschließlich
# diese Konstanten statt verstreuter Magic Numbers (kein Drift zur Spec).
CARD_RADIUS_PX = 12              # Eckenradius der Karten
CARD_PADDING = (14, 13, 14, 13)  # Innenpolster L/O/R/U (14 horizontal / 13 vertikal)
CARD_CONTENT_SPACING = 10        # Binnenabstand der Elemente innerhalb einer Karte
CARD_STACK_SPACING = 11          # Sektionsabstand zwischen Karten im Schritt-Stapel
CARD_STACK_SIDE_MARGIN = 18      # seitlicher Innenabstand des Karten-Stapels (§1)
CARD_STACK_TOP_MARGIN = 20       # oberer Innenabstand des Karten-Stapels (§1)
CARD_STACK_BOTTOM_MARGIN = 18    # unterer Innenabstand des Karten-Stapels (§1)


# ── Palette-parametrierte Stil-Bausteine (für die Redesign-Chrome) ──────────

def card_style(p: Palette) -> str:
    return (f"background: {p.card_bg}; border: 1px solid {p.card_border};"
            f" border-radius: {CARD_RADIUS_PX}px;")


def section_header_style(p: Palette) -> str:
    """Kartenkopf-Titel (§5.2): 11 px/700, VERSALIEN (Aufrufer setzen ``.upper()``),
    blauer Akzentstrich links – immer Akzentfarbe, nie Amber/Coral (Issue #416)."""
    return (f"color: {p.text2}; font-size: 11px; font-weight: bold;"
            " letter-spacing: .05em; background: transparent;"
            f" padding: 0 0 0 8px; border-left: 3px solid {p.accent};"
            " min-height: 13px; max-height: 13px;")


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
    """Rahmen des Inspector-Panels (Objektname ``inspectorPanel``, right_panel).

    ID-Selektor statt ``QFrame``: QLabel erbt von QFrame – ein typweiter
    Selektor kaskadiert ``border-left`` sonst als senkrechten Störstrich auf
    alle rahmenlosen Labels der Karten (z. B. vor „ד/„px" in „Größe ändern").
    """
    return (f"QFrame#inspectorPanel {{ background: {p.inspector};"
            f" border-left: 1px solid {p.border}; }}")


def scroll_style(p: Palette) -> str:
    return f"""
    QScrollArea {{ background: {p.inspector}; border: none; }}
    QScrollBar:vertical {{ background: {p.inspector}; width: 6px; margin: 0; }}
    QScrollBar::handle:vertical {{
        background: {p.border}; border-radius: 3px; min-height: 20px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


def panel_btn_style(p: Palette) -> str:
    """Sekundärbutton der Inspector-Karten (neutrale Fläche, §5.3/§5.6 – Prototyp-Klasse ``.bs``)."""
    return f"""
    QPushButton {{
        background: {p.surface}; color: {p.text2}; border: 1px solid {p.border_2};
        border-radius: 8px; padding: 0 10px; font-size: 12px; min-height: 34px;
    }}
    QPushButton:hover {{ background: {p.surface_hover}; }}
    QPushButton:focus {{ outline: none; border: 1px solid {p.accent}; }}
    QPushButton:disabled {{ background: {p.divider}; color: {p.muted}; }}
"""


def num_style(p: Palette) -> str:
    """Zahlenfelder/Combos in den Inspector-Karten (Trefferfläche ≥ 24 px, #441).

    Die ±-Stepper der SpinBoxen sind explizit gestylt (§5.5, #516) statt
    nativ: eine 18 px breite Stepper-Spalte innerhalb des 1-px-Rahmens
    (``subcontrol-origin: padding``; die Style-Engine hält das Edit-Feld
    automatisch von der Spalte frei) und Trennlinien in Palettenfarbe statt
    der themenunabhängigen Default-Striche der Style-Engine. Die ±-Glyphen
    selbst malt ``_PanelSpinBox`` (right_panel_tabs) – der QSS-Subcontrol-
    Pfad zeichnet keine PlusMinus-Primitives. QComboBox bleibt bewusst ohne
    Stepper-Pseudoelemente (``combo_style``).
    """
    return (
        f"QSpinBox, QComboBox {{ background:{p.surface}; color:{p.text};"
        f" border:1px solid {p.border}; border-radius:6px; padding:3px 6px;"
        " font-size:12px; min-height:24px; }"
        " QSpinBox::up-button, QSpinBox::down-button {"
        " subcontrol-origin:padding; width:18px; background:transparent;"
        f" border:none; border-left:1px solid {p.border}; }}"
        " QSpinBox::up-button { subcontrol-position:top right;"
        " border-top-right-radius:5px; }"
        " QSpinBox::down-button { subcontrol-position:bottom right;"
        f" border-top:1px solid {p.border}; border-bottom-right-radius:5px; }}"
        " QSpinBox::up-button:hover, QSpinBox::down-button:hover {"
        f" background:{p.surface_hover}; }}"
        f" QSpinBox:focus, QComboBox:focus {{ border:1px solid {p.accent}; }}"
        f" QComboBox QAbstractItemView {{ background:{p.surface}; color:{p.text}; }}"
    )


def combo_style(p: Palette) -> str:
    """ComboBox-Stil ohne SpinBox-Stepper-Pseudoelemente."""
    return (
        f"QComboBox {{ background:{p.surface}; color:{p.text};"
        f" border:1px solid {p.border}; border-radius:6px; padding:3px 6px;"
        " font-size:12px; min-height:24px; }"
        f" QComboBox:focus {{ border:1px solid {p.accent}; }}"
        f" QComboBox QAbstractItemView {{ background:{p.surface}; color:{p.text}; }}"
    )


def slider_style(p: Palette) -> str:
    """Slider: nativer Prototyp-Range-Look mit weissem Griff (#441/#496).

    Der weisse Griff braucht im hellen Schema einen 1-px-``text3``-Ring, sonst
    verschwindet er auf weissen Karten (WCAG 1.4.11 ≥ 3:1; Codex-Befund auf
    #496); im dunklen Schema traegt er selbst genug Kontrast und bleibt
    randlos wie im Prototyp. Tastatur-Fokus markiert den Griff sichtbar mit
    dem 2-px-``accent``-Ring aller interaktiven Bausteine (#441).
    """
    rest = "#e6e6e6" if p.is_dark else "#d4d9e2"
    # Qt zeichnet Sub-Control-Raender INNERHALB der 16-px-Griff-Box
    # (Border-Box); Radius 8 = Boxhaelfte bleibt daher fuer alle Zustaende
    # der Kreis – ein groesserer Radius wuerde von Qt komplett verworfen.
    handle_border = "none" if p.is_dark else f"1px solid {p.text3}"
    return f"""
    QSlider {{ margin: 9px 0 2px 0; min-height: 22px; }}
    QSlider::groove:horizontal {{ height: 8px; background: transparent; border-radius: 4px; }}
    QSlider::sub-page:horizontal {{ background: {p.accent}; border: none; border-radius: 4px; }}
    QSlider::add-page:horizontal {{ background: {rest}; border: none; border-radius: 4px; }}
    QSlider::handle:horizontal {{
        background: {p.on_accent}; border: {handle_border}; width: 16px; height: 16px;
        margin: -4px 0; border-radius: 8px;
    }}
    QSlider::sub-page:horizontal:disabled {{ background: {p.muted}; }}
    QSlider::add-page:horizontal:disabled {{ background: {p.divider}; }}
    QSlider::handle:horizontal:disabled {{ background: {p.muted}; }}
    QSlider::handle:horizontal:focus {{ border: 2px solid {p.accent}; }}
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
    """``QMenuBar`` teilt sich den ``toolbar``-Ton mit der Werkzeugleiste
    (Prototyp: ``--menubar`` == ``--rail`` in beiden Schemata) – nicht
    ``status``, das der eigenständigen, dunkleren Statusleiste vorbehalten bleibt.
    """
    return f"""
    QMenuBar {{ background: {p.toolbar}; color: {p.text2}; }}
    QMenuBar::item:selected {{ background: {p.surface_hover}; }}
    QMenu {{ background: {p.surface}; color: {p.text2}; border: 1px solid {p.border}; }}
    QMenu::item:selected {{ background: {p.accent}; color: {p.on_accent}; }}
"""


def zoom_pill_style(p: Palette) -> str:
    """Schwebende Zoom-Kontrolle auf der Arbeitsfläche (#464, Glas-Pille).

    Halbtransparente ``glass``-Fläche mit ``border``-Haarlinie; die
    +/−-Buttons ruhen transparent, der Fixier-Button zeigt seinen aktiven
    Zustand akzent-getönt wie die Rail-Werkzeuge (§5.9).
    """
    return f"""
    QFrame#zoomPill {{
        background: {p.glass}; border: 1px solid {p.card_border};
        border-radius: 10px;
    }}
    QLabel#zoomLabel {{
        color: {p.text2}; font-size: 12px; font-weight: 600;
        background: transparent; border: none;
    }}
    QToolButton {{
        color: {p.text2}; font-size: 14px; font-weight: 600;
        border: 1px solid transparent; border-radius: 7px; background: transparent;
    }}
    QToolButton:hover    {{ background: {p.hover}; }}
    QToolButton:checked  {{ background: {p.accent_soft}; border-color: {p.accent_line}; color: {p.accent_text}; }}
    QToolButton:focus    {{ outline: none; border: 1px solid {p.accent}; }}
    QToolButton:disabled {{ color: {p.muted}; background: transparent; }}
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
        border-radius: {CARD_RADIUS_PX}px;
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
    über :class:`Palette`/:func:`active_palette`. Die früheren, aus ``DARK``
    gespiegelten Zusatzattribute (``ACCENT_SOFT`` … ``TEXT_3``) waren
    referenzlos und sind entfernt (#503).
    """
    ACCENT      = "#4a90d9"   # Hervorhebung: aktiver Tab, Slider, Auswahl
    BG_PANEL    = "#1a1a1a"   # rechtes Panel / Tab-Pane / Statusleiste
    BG_TABBAR   = "#141414"   # Tab-Leisten-Hintergrund
    BORDER      = "#3a3a3a"   # Rahmen / Trennlinien / Slider-Groove
    DIVIDER     = "#2a2a2a"   # dünne Trennflächen
    TEXT_BRIGHT = "#e0e0e0"   # heller Text (aktiver Tab)


# ── Rückwärtskompatible, dunkel gebaute Konstanten (Tests/Alt-Imports) ──────
# Nur die tatsächlich referenzierten Alt-Konstanten; die übrigen ``*_STYLE``-
# Aliase waren toter Code und sind entfernt (#503) – die laufende UI baut
# ihre Stile über die ``*_style``-Builder mit der aktiven Palette.
CARD_STYLE = card_style(DARK)
TOOL_STYLE = tool_style(DARK)
SLD_STYLE = slider_style(DARK)
CANVAS_CONTAINER_STYLE = "background: transparent;"
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
