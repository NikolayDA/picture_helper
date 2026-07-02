"""Aufbau der linken Werkzeugleiste für das Hauptfenster."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QButtonGroup, QFrame, QToolButton, QVBoxLayout

from bgremover.constants import (
    _IS_MACOS,
    _TOOLBAR_BTN_SIZE,
    _TOOLBAR_ICON_SIZE,
    _TOOLBAR_WIDTH,
    TOOL_BRUSH,
    TOOL_ERASER,
    TOOL_LASSO,
    TOOL_WAND,
)
from bgremover.i18n import tr
from bgremover.icons import make_tool_icon
from bgremover.theme import (
    Palette,
    active_palette,
    history_button_style,
    tool_style,
    toolbar_frame_style,
)


def _shortcut_label(shortcut: str) -> str:
    return shortcut.replace("Ctrl", "Cmd" if _IS_MACOS else "Ctrl")


@dataclass(frozen=True)
class ToolbarActions:
    """Callbacks der Toolbar – ohne Abhängigkeit vom MainWindow."""

    set_tool: Callable[[str], None]
    run_ai: Callable[[], None]
    undo: Callable[[], None]
    redo: Callable[[], None]
    restore_original: Callable[[], None]
    toggle_history: Callable[[], None]
    open_image: Callable[[], None]
    save: Callable[[], None]


@dataclass(frozen=True)
class Toolbar:
    """Fertig gebaute Toolbar samt Widgets, die das MainWindow weiterhin direkt aktualisiert."""

    frame: QFrame
    button_group: QButtonGroup
    btn_wand: QToolButton
    btn_brush: QToolButton
    btn_eraser: QToolButton
    btn_lasso: QToolButton
    btn_ai: QToolButton
    btn_history: QToolButton
    # Trenner nach den Auswahlwerkzeugen – zusammen mit btn_wand/brush/eraser/
    # lasso schrittabhängig ein-/ausgeblendet (kontextuelle Werkzeugleiste #422).
    sel_separator: QFrame
    # Nach Stil gruppierte Widgetlisten für das Live-Umfärben beim Theme-Wechsel
    # (#428): Werkzeug-/Mini-Buttons (tool_style), History-Buttons und Trenner.
    tool_buttons: list[QToolButton] = field(default_factory=list)
    history_buttons: list[QToolButton] = field(default_factory=list)
    separators: list[QFrame] = field(default_factory=list)

    def apply_palette(self, p: Palette) -> None:
        """Restylt Rahmen, Buttons und Trenner für ein Schema-Umschalten (#428)."""
        self.frame.setStyleSheet(toolbar_frame_style(p))
        tool = tool_style(p)
        for btn in self.tool_buttons:
            btn.setStyleSheet(tool)
        hist = history_button_style(p)
        for btn in self.history_buttons:
            btn.setStyleSheet(hist)
        for sep in self.separators:
            sep.setStyleSheet(f"background: {p.hairline}; border: none;")


def build_toolbar(actions: ToolbarActions, *, rembg_available: bool) -> Toolbar:
    builder = _ToolbarBuilder(actions, rembg_available=rembg_available)
    return builder.build()


class _ToolbarBuilder:
    def __init__(self, actions: ToolbarActions, *, rembg_available: bool) -> None:
        self._actions = actions
        self._rembg_available = rembg_available
        self._pal = active_palette()
        # Nach Stil gruppierte Widgetlisten für das spätere Live-Umfärben (#428).
        self._tool_buttons: list[QToolButton] = []
        self._history_buttons: list[QToolButton] = []
        self._separators: list[QFrame] = []

    def build(self) -> Toolbar:
        frame = QFrame()
        frame.setFixedWidth(_TOOLBAR_WIDTH)
        frame.setStyleSheet(toolbar_frame_style(self._pal))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 12, 0, 12)
        lay.setSpacing(8)

        button_group = QButtonGroup(frame)
        button_group.setExclusive(True)

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

        sel_separator = self._add_separator(lay)

        btn_ai = QToolButton()
        btn_ai.setIcon(make_tool_icon("ai", 38))
        btn_ai.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
        btn_ai.setToolTip(
            tr("toolbar.ai.available.tooltip")
            if self._rembg_available else
            tr("toolbar.ai.missing.tooltip")
        )
        btn_ai.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
        btn_ai.setStyleSheet(tool_style(self._pal))
        btn_ai.setEnabled(self._rembg_available)
        btn_ai.clicked.connect(self._actions.run_ai)
        self._tool_buttons.append(btn_ai)
        lay.addWidget(btn_ai, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._add_separator(lay)

        self._history_button(
            lay,
            "undo",
            tr("toolbar.undo.tooltip", shortcut=_shortcut_label("Ctrl+Z")),
            self._actions.undo,
        )
        self._history_button(
            lay,
            "redo",
            tr("toolbar.redo.tooltip", shortcut=_shortcut_label("Ctrl+Shift+Z")),
            self._actions.redo,
        )
        self._history_button(
            lay,
            "restore",
            tr("toolbar.restore.tooltip"),
            self._actions.restore_original,
        )
        btn_history = self._history_button(
            lay,
            "history",
            tr("toolbar.history.tooltip"),
            self._actions.toggle_history,
        )

        lay.addStretch()

        self._mini_button(
            lay, "open", tr("toolbar.open.tooltip", shortcut=_shortcut_label("Ctrl+O")),
            self._actions.open_image)
        self._mini_button(
            lay, "save", tr("toolbar.save.tooltip", shortcut=_shortcut_label("Ctrl+S")),
            self._actions.save)

        return Toolbar(
            frame=frame,
            button_group=button_group,
            btn_wand=btn_wand,
            btn_brush=btn_brush,
            btn_eraser=btn_eraser,
            btn_lasso=btn_lasso,
            btn_ai=btn_ai,
            btn_history=btn_history,
            sel_separator=sel_separator,
            tool_buttons=self._tool_buttons,
            history_buttons=self._history_buttons,
            separators=self._separators,
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
        b.setIcon(make_tool_icon(icon_name, 38))
        b.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
        b.setToolTip(tip)
        b.setCheckable(True)
        b.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
        b.setStyleSheet(tool_style(self._pal))
        b.clicked.connect(lambda checked=False, t=tool: self._actions.set_tool(t))
        button_group.addButton(b)
        self._tool_buttons.append(b)
        lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
        return b

    def _history_button(
        self,
        lay: QVBoxLayout,
        icon_name: str,
        tip: str,
        slot: Callable[[], None],
    ) -> QToolButton:
        b = QToolButton()
        b.setIcon(make_tool_icon(icon_name, 38))
        b.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
        b.setToolTip(tip)
        b.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
        b.setStyleSheet(history_button_style(self._pal))
        b.clicked.connect(slot)
        self._history_buttons.append(b)
        lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
        return b

    def _mini_button(
        self,
        lay: QVBoxLayout,
        icon_name: str,
        tip: str,
        slot: Callable[[], None],
    ) -> QToolButton:
        b = QToolButton()
        b.setIcon(make_tool_icon(icon_name, 38))
        b.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
        b.setToolTip(tip)
        b.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
        b.setStyleSheet(tool_style(self._pal))
        b.clicked.connect(slot)
        self._tool_buttons.append(b)
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
