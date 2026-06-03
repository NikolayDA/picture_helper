"""Right-side tab panel construction for the main window."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, cast

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from bgremover.constants import _RIGHT_PANEL_WIDTH, _TAB_ICON_PX
from bgremover.i18n import tr
from bgremover.icons import make_tool_icon
from bgremover.right_panel_tabs import (
    BackgroundTab,
    SelectionTab,
    ShapeTab,
    TransformTab,
)
from bgremover.theme import _Theme
from bgremover.widgets import TopIconTabWidget

TAB_STYLE = f"""
    QTabWidget::pane {{ border: none; background: {_Theme.BG_PANEL}; }}
    QTabBar {{ background: {_Theme.BG_TABBAR}; }}
    QTabBar::tab {{
        background: #1e1e1e; color: #666;
        padding: 10px 0px; min-width: 94px;
        font-size: 12px; border: none;
        border-bottom: 3px solid transparent;
    }}
    QTabBar::tab:selected {{
        color: {_Theme.TEXT_BRIGHT}; background: {_Theme.BG_PANEL};
        border-bottom: 3px solid {_Theme.ACCENT}; font-weight: bold;
    }}
    QTabBar::tab:hover:!selected {{ color: #aaa; background: #242424; }}
"""


@dataclass(frozen=True)
class RightPanelActions:
    """Callbacks used by the right-side panel without depending on MainWindow."""

    set_tolerance: Callable[[int], None]
    set_brush_size: Callable[[int], None]
    clear_selection: Callable[[], None]
    invert_selection: Callable[[], None]
    expand_selection: Callable[[int], None]
    shrink_selection: Callable[[int], None]
    remove_background: Callable[[], None]
    pick_color: Callable[[], None]
    replace_background: Callable[[], None]
    rotate: Callable[[int], None]
    flip: Callable[[bool], None]
    round_corners: Callable[[int], None]
    start_crop_circle: Callable[[], None]
    start_crop_ratio: Callable[[int, int], None]


@dataclass(frozen=True)
class RightPanel:
    """Constructed panel plus widgets MainWindow still updates directly."""

    frame: QFrame
    tolerance_label: QLabel
    tolerance_slider: QSlider
    brush_label: QLabel
    brush_slider: QSlider
    morph_spin: QSpinBox
    color_button: QPushButton
    rotation_slider: QSlider
    rotation_spin: QSpinBox
    corner_label: QLabel
    corner_slider: QSlider


class _TabBuilder(Protocol):
    def build(self) -> tuple[QWidget, dict[str, QWidget]]: ...


def build_right_panel(actions: RightPanelActions) -> RightPanel:
    return _RightPanelBuilder(actions).build()


class _RightPanelBuilder:
    """Orchestriert die vier Tab-Klassen und befüllt das ``RightPanel``-DTO."""

    def __init__(self, actions: RightPanelActions) -> None:
        self._actions = actions

    def build(self) -> RightPanel:
        frame = QFrame()
        frame.setFixedWidth(_RIGHT_PANEL_WIDTH)
        frame.setStyleSheet("QFrame { background: #1a1a1a; border-left: 1px solid #333; }")
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        tabs = TopIconTabWidget(_TAB_ICON_PX)
        tabs.setDocumentMode(True)
        tabs.setStyleSheet(TAB_STYLE)
        tabs.setUsesScrollButtons(False)
        tabs.setIconSize(QSize(_TAB_ICON_PX, _TAB_ICON_PX))
        outer.addWidget(tabs)

        builders: list[_TabBuilder] = [
            SelectionTab(self._actions),
            BackgroundTab(self._actions),
            TransformTab(self._actions),
            ShapeTab(self._actions),
        ]
        tab_specs = [
            (
                tr("right_panel.tab.selection"),
                "clear_sel",
                tr("right_panel.tab.selection.tooltip"),
            ),
            (
                tr("right_panel.tab.background"),
                "bg",
                tr("right_panel.tab.background.tooltip"),
            ),
            (
                tr("right_panel.tab.transform"),
                "transparency",
                tr("right_panel.tab.transform.tooltip"),
            ),
            (
                tr("right_panel.tab.shape"),
                "form",
                tr("right_panel.tab.shape.tooltip"),
            ),
        ]
        refs: dict[str, QWidget] = {}
        for builder, (name, icon, tip) in zip(builders, tab_specs, strict=True):
            widget, widget_refs = builder.build()
            idx = tabs.addTab(widget, name)
            tabs.setTabIcon(idx, make_tool_icon(icon, _TAB_ICON_PX))
            tabs.setTabToolTip(idx, tip)
            refs.update(widget_refs)

        return RightPanel(
            frame=frame,
            tolerance_label=cast(QLabel, refs["tolerance_label"]),
            tolerance_slider=cast(QSlider, refs["tolerance_slider"]),
            brush_label=cast(QLabel, refs["brush_label"]),
            brush_slider=cast(QSlider, refs["brush_slider"]),
            morph_spin=cast(QSpinBox, refs["morph_spin"]),
            color_button=cast(QPushButton, refs["color_button"]),
            rotation_slider=cast(QSlider, refs["rotation_slider"]),
            rotation_spin=cast(QSpinBox, refs["rotation_spin"]),
            corner_label=cast(QLabel, refs["corner_label"]),
            corner_slider=cast(QSlider, refs["corner_slider"]),
        )
