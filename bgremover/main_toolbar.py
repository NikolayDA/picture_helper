"""Aufbau der linken Werkzeugleiste für das Hauptfenster.

Rail-Umfang 1:1 zum Prototyp (Epic #455): oben das permanente
„Verschieben / Zoom"-Werkzeug (#456), darunter kontextuell die
Auswahlwerkzeuge (nur Schritt 2) bzw. die malenden Höhen-Werkzeuge
(nur Schritt 5, #457) – je mit eigenem Trenner. Unten der schritt-
unabhängige **Rail-Fuß** (#458): Trenner, Rückgängig, Wiederholen,
Theme-Umschalter. KI, Original, Verlauf sowie Öffnen/Speichern liegen
nicht mehr in der Rail (Menü/Kürzel/Schritt-Inspector decken sie ab).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QButtonGroup, QFrame, QToolButton, QVBoxLayout

from bgremover.constants import (
    _IS_MACOS,
    _TOOLBAR_BTN_SIZE,
    _TOOLBAR_ICON_SIZE,
    _TOOLBAR_WIDTH,
    TOOL_BRUSH,
    TOOL_ERASER,
    TOOL_HEIGHT_DARKEN,
    TOOL_HEIGHT_LIGHTEN,
    TOOL_LASSO,
    TOOL_MOVE,
    TOOL_WAND,
)
from bgremover.i18n import tr
from bgremover.icons import make_stateful_tool_icon, make_tool_icon
from bgremover.theme import (
    Palette,
    active_palette,
    tool_style,
    toolbar_frame_style,
)

# Icongröße der Rail-Fuß-Buttons (Prototyp: 18 px gegenüber 20 px der Werkzeuge).
_FOOT_ICON_SIZE = 18
# Rendergröße der Icon-Pixmaps: größer als die Anzeigegröße (20/18 px), damit
# Qt beim Skalieren auf die tatsächliche Icon-Größe glatte Kanten liefert.
_ICON_RENDER_PX = 38


def _shortcut_label(shortcut: str) -> str:
    return shortcut.replace("Ctrl", "Cmd" if _IS_MACOS else "Ctrl")


@dataclass(frozen=True)
class ToolbarActions:
    """Callbacks der Toolbar – ohne Abhängigkeit vom MainWindow."""

    set_tool: Callable[[str], None]
    undo: Callable[[], None]
    redo: Callable[[], None]
    toggle_theme: Callable[[], None]


@dataclass(frozen=True)
class Toolbar:
    """Fertig gebaute Toolbar samt Widgets, die das MainWindow weiterhin direkt aktualisiert."""

    frame: QFrame
    button_group: QButtonGroup
    btn_move: QToolButton
    btn_wand: QToolButton
    btn_brush: QToolButton
    btn_eraser: QToolButton
    btn_lasso: QToolButton
    btn_height_lighten: QToolButton
    btn_height_darken: QToolButton
    # Rail-Fuß (#458): in allen Schritten sichtbar, unten gepinnt.
    btn_undo: QToolButton
    btn_redo: QToolButton
    btn_theme: QToolButton
    # Trenner der kontextuellen Gruppen – zusammen mit ihren Werkzeugen
    # schrittabhängig ein-/ausgeblendet (kontextuelle Werkzeugleiste #422/#455).
    sel_separator: QFrame
    height_separator: QFrame
    foot_separator: QFrame
    # Für das Live-Umfärben beim Theme-Wechsel (#428): alle Rail-Buttons teilen
    # den Werkzeug-Look des Prototyps (`.tool`), dazu die Trenner.
    tool_buttons: list[QToolButton] = field(default_factory=list)
    separators: list[QFrame] = field(default_factory=list)
    # Icon-Namen je Button (#486), getrennt nach checkbar (braucht eine
    # Aus-/An-Zustandsfarbe) und Rail-Fuß (nur ein statischer Ton) – zum
    # Neu-Rendern der Icon-Pixel beim Theme-Wechsel.
    checkable_icons: list[tuple[QToolButton, str]] = field(default_factory=list)
    foot_icons: list[tuple[QToolButton, str]] = field(default_factory=list)

    def apply_palette(self, p: Palette) -> None:
        """Restylt Rahmen, Buttons, Trenner und Icon-Farben für ein
        Schema-Umschalten (#428/#486)."""
        self.frame.setStyleSheet(toolbar_frame_style(p))
        tool = tool_style(p)
        for btn in self.tool_buttons:
            btn.setStyleSheet(tool)
        for sep in self.separators:
            sep.setStyleSheet(f"background: {p.hairline}; border: none;")
        idle, active = QColor(p.text3), QColor(p.accent_text)
        for btn, name in self.checkable_icons:
            btn.setIcon(make_stateful_tool_icon(name, _ICON_RENDER_PX, idle, active))
        for btn, name in self.foot_icons:
            btn.setIcon(make_tool_icon(name, _ICON_RENDER_PX, idle))


def build_toolbar(actions: ToolbarActions, *, light_mode: bool = False) -> Toolbar:
    builder = _ToolbarBuilder(actions, light_mode=light_mode)
    return builder.build()


def theme_toggle_tooltip(light_mode: bool) -> str:
    """Tooltip des Theme-Umschalters – nennt das Ziel-Schema (#458)."""
    return (
        tr("toolbar.theme.to_dark.tooltip")
        if light_mode else tr("toolbar.theme.to_light.tooltip")
    )


class _ToolbarBuilder:
    def __init__(self, actions: ToolbarActions, *, light_mode: bool) -> None:
        self._actions = actions
        self._light_mode = light_mode
        self._pal = active_palette()
        # Nach Stil gruppierte Widgetlisten für das spätere Live-Umfärben (#428).
        self._tool_buttons: list[QToolButton] = []
        self._separators: list[QFrame] = []
        # Icon-Namen je Button für das Neu-Rendern der Icon-Farben (#486).
        self._checkable_icons: list[tuple[QToolButton, str]] = []
        self._foot_icons: list[tuple[QToolButton, str]] = []

    def build(self) -> Toolbar:
        frame = QFrame()
        frame.setFixedWidth(_TOOLBAR_WIDTH)
        frame.setStyleSheet(toolbar_frame_style(self._pal))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 12, 0, 12)
        lay.setSpacing(8)

        button_group = QButtonGroup(frame)
        button_group.setExclusive(True)

        # Oberster, in allen Schritten sichtbarer Button (#456).
        btn_move = self._tool_button(
            lay, button_group, "move", tr("toolbar.move.tooltip"), TOOL_MOVE)

        sel_separator = self._add_separator(lay)

        btn_wand = self._tool_button(
            lay,
            button_group,
            "wand",
            tr("toolbar.wand.tooltip", modifier=_shortcut_label("Ctrl")),
            TOOL_WAND,
        )
        btn_brush = self._tool_button(
            lay,
            button_group,
            "brush",
            tr("toolbar.brush.tooltip"),
            TOOL_BRUSH,
        )
        btn_eraser = self._tool_button(
            lay,
            button_group,
            "eraser",
            tr("toolbar.eraser.tooltip"),
            TOOL_ERASER,
        )
        btn_lasso = self._tool_button(
            lay,
            button_group,
            "lasso",
            tr("toolbar.lasso.tooltip", modifier=_shortcut_label("Ctrl")),
            TOOL_LASSO,
        )
        btn_wand.setChecked(True)

        # Malende Höhen-Werkzeuge (#457): nur in Schritt 5 sichtbar; ohne
        # aktive HEIGHT-Ebene deaktiviert (Tooltip nennt den Grund).
        height_separator = self._add_separator(lay)
        btn_height_lighten = self._tool_button(
            lay,
            button_group,
            "height_lighten",
            tr("toolbar.height_lighten.tooltip"),
            TOOL_HEIGHT_LIGHTEN,
        )
        btn_height_darken = self._tool_button(
            lay,
            button_group,
            "height_darken",
            tr("toolbar.height_darken.tooltip"),
            TOOL_HEIGHT_DARKEN,
        )
        # Ohne aktive HEIGHT-Ebene deaktiviert; das MainWindow synchronisiert
        # Zustand + Begründungs-Tooltip über ``layersChanged`` (#457).
        btn_height_lighten.setEnabled(False)
        btn_height_darken.setEnabled(False)

        lay.addStretch()

        # Rail-Fuß (#458): unten gepinnt, in allen Schritten identisch.
        foot_separator = self._add_separator(lay)
        btn_undo = self._foot_button(
            lay,
            "undo",
            tr("toolbar.undo.tooltip", shortcut=_shortcut_label("Ctrl+Z")),
            self._actions.undo,
        )
        btn_redo = self._foot_button(
            lay,
            "redo",
            tr("toolbar.redo.tooltip", shortcut=_shortcut_label("Ctrl+Shift+Z")),
            self._actions.redo,
        )
        btn_theme = self._foot_button(
            lay,
            "theme",
            theme_toggle_tooltip(self._light_mode),
            self._actions.toggle_theme,
        )
        # Ohne geladenes Bild gibt es nichts rückgängig zu machen.
        btn_undo.setEnabled(False)
        btn_redo.setEnabled(False)

        return Toolbar(
            frame=frame,
            button_group=button_group,
            btn_move=btn_move,
            btn_wand=btn_wand,
            btn_brush=btn_brush,
            btn_eraser=btn_eraser,
            btn_lasso=btn_lasso,
            btn_height_lighten=btn_height_lighten,
            btn_height_darken=btn_height_darken,
            btn_undo=btn_undo,
            btn_redo=btn_redo,
            btn_theme=btn_theme,
            sel_separator=sel_separator,
            height_separator=height_separator,
            foot_separator=foot_separator,
            tool_buttons=self._tool_buttons,
            separators=self._separators,
            checkable_icons=self._checkable_icons,
            foot_icons=self._foot_icons,
        )

    def _tool_button(
        self,
        lay: QVBoxLayout,
        button_group: QButtonGroup,
        icon_name: str,
        tip: str,
        tool: str,
    ) -> QToolButton:
        b = QToolButton()
        b.setIcon(make_stateful_tool_icon(
            icon_name, _ICON_RENDER_PX,
            QColor(self._pal.text3), QColor(self._pal.accent_text)))
        b.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
        b.setToolTip(tip)
        b.setCheckable(True)
        b.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
        b.setStyleSheet(tool_style(self._pal))
        b.clicked.connect(lambda checked=False, t=tool: self._actions.set_tool(t))
        button_group.addButton(b)
        self._tool_buttons.append(b)
        self._checkable_icons.append((b, icon_name))
        lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
        return b

    def _foot_button(
        self,
        lay: QVBoxLayout,
        icon_name: str,
        tip: str,
        slot: Callable[[], None],
    ) -> QToolButton:
        """Nicht-checkbarer Aktions-Button des Rail-Fußes (Werkzeug-Look, #458)."""
        b = QToolButton()
        b.setIcon(make_tool_icon(icon_name, _ICON_RENDER_PX, QColor(self._pal.text3)))
        b.setIconSize(QSize(_FOOT_ICON_SIZE, _FOOT_ICON_SIZE))
        b.setToolTip(tip)
        b.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
        b.setStyleSheet(tool_style(self._pal))
        b.clicked.connect(slot)
        self._tool_buttons.append(b)
        self._foot_icons.append((b, icon_name))
        lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
        return b

    def _add_separator(self, lay: QVBoxLayout) -> QFrame:
        """Trenner zwischen Werkzeuggruppen: 30 × 1 px, zentriert (§5.9)."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.NoFrame)
        sep.setFixedSize(30, 1)
        sep.setStyleSheet(f"background: {self._pal.hairline}; border: none;")
        lay.addSpacing(2)
        lay.addWidget(sep, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(2)
        self._separators.append(sep)
        return sep
