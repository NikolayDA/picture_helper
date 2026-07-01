"""Aufbau des rechten Inspector-Panels als geführter 6-Schritte-Workflow.

Epic #418 (Geführter Workflow) und #413 (Karten-Inspector): Die rechte Spalte
ist keine durchlaufende Tab-Liste mehr, sondern ein Inspector mit **Kopf**
(Schritt-Titel + Beschreibung), einem :class:`QStackedWidget` mit genau sechs
Schritt-Seiten und einer fixen **Navigations-Fußzeile** (Zurück / Weiter).

Jede Schritt-Seite wiederverwendet die bestehenden Tab-Bausteine
(``right_panel_tabs`` + Ebenen-/Höhen-Panel) – die Aktions-Verdrahtung
(``RightPanelActions``/``LayerPanelActions``/``HeightMapActions``) bleibt damit
unverändert. Das MainWindow schaltet über :meth:`RightPanel.set_step` den
aktiven Schritt (Sichtbarkeit, Kopf- und Weiter-Beschriftung) und verbindet die
Navigations-Buttons.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from bgremover.color_ops import ColorOp
from bgremover.constants import _RIGHT_PANEL_WIDTH
from bgremover.height_map_panel import HeightMapActions, HeightMapPanel
from bgremover.i18n import tr
from bgremover.layer_panel import LayerPanel, LayerPanelActions
from bgremover.preview_mode import PreviewMode
from bgremover.right_panel_tabs import (
    AdjustTab,
    BackgroundTab,
    PreviewTab,
    SelectionTab,
    ShapeTab,
    TransformTab,
)
from bgremover.stepper import WorkflowStep
from bgremover.theme import (
    NAV_BACK_STYLE,
    NAV_BAR_STYLE,
    NAV_NEXT_STYLE,
    PRIMARY_BTN_STYLE,
    _Theme,
)

# Wird von ``tests/test_theme.py`` referenziert und hält den Akzent-Token für
# die (weiterhin verfügbare) Tab-Optik bereit; der geführte Workflow selbst
# nutzt den QStackedWidget-Aufbau.
TAB_STYLE = f"""
    QTabWidget::pane {{ border: none; background: {_Theme.BG_PANEL}; }}
    QTabBar::tab:selected {{ border-bottom: 3px solid {_Theme.ACCENT}; }}
"""

_PANEL_STYLE = f"QFrame {{ background: {_Theme.BG_PANEL}; border-left: 1px solid {_Theme.BORDER}; }}"


# Literale ``tr``-Keys je Schritt (Konvention wie ``layer_panel._role_label``:
# hält die i18n-Coverage grün, die nur eigenständige Literal-Aufrufe von tr zählt).
def _step_title(step: WorkflowStep) -> str:
    """Schritt-Titel im Inspector-Kopf (Spec §9)."""
    if step is WorkflowStep.OPEN:
        return tr("workflow.title.open")
    if step is WorkflowStep.CUTOUT:
        return tr("workflow.title.cutout")
    if step is WorkflowStep.ADJUST:
        return tr("workflow.title.adjust")
    if step is WorkflowStep.SHAPE:
        return tr("workflow.title.shape")
    if step is WorkflowStep.RELIEF:
        return tr("workflow.title.relief")
    return tr("workflow.title.export")


def _step_desc(step: WorkflowStep) -> str:
    """Schritt-Beschreibung im Inspector-Kopf (Spec §9)."""
    if step is WorkflowStep.OPEN:
        return tr("workflow.desc.open")
    if step is WorkflowStep.CUTOUT:
        return tr("workflow.desc.cutout")
    if step is WorkflowStep.ADJUST:
        return tr("workflow.desc.adjust")
    if step is WorkflowStep.SHAPE:
        return tr("workflow.desc.shape")
    if step is WorkflowStep.RELIEF:
        return tr("workflow.desc.relief")
    return tr("workflow.desc.export")


def _step_next(step: WorkflowStep) -> str:
    """„Weiter"-Beschriftung je Schritt (Spec §7)."""
    if step is WorkflowStep.OPEN:
        return tr("workflow.next.open")
    if step is WorkflowStep.CUTOUT:
        return tr("workflow.next.cutout")
    if step is WorkflowStep.ADJUST:
        return tr("workflow.next.adjust")
    if step is WorkflowStep.SHAPE:
        return tr("workflow.next.shape")
    if step is WorkflowStep.RELIEF:
        return tr("workflow.next.relief")
    return tr("workflow.next.export")


@dataclass(frozen=True)
class RightPanelActions:
    """Callbacks des rechten Panels – ohne Abhängigkeit vom MainWindow."""

    set_tolerance: Callable[[int], None]
    set_brush_size: Callable[[int], None]
    clear_selection: Callable[[], None]
    invert_selection: Callable[[], None]
    expand_selection: Callable[[int], None]
    shrink_selection: Callable[[int], None]
    remove_background: Callable[[], None]
    pick_color: Callable[[], None]
    replace_background: Callable[[], None]
    feather: Callable[[int], None]
    rotate: Callable[[int], None]
    flip: Callable[[bool], None]
    resize: Callable[[], None]
    round_corners: Callable[[int], None]
    start_crop_circle: Callable[[], None]
    start_crop_ratio: Callable[[int, int], None]
    preview_color: Callable[[ColorOp], None]
    apply_color: Callable[[ColorOp], None]
    cancel_color_preview: Callable[[], None]
    set_preview_mode: Callable[[PreviewMode], None]
    set_relief_strength: Callable[[int], None]
    set_gloss_visible: Callable[[bool], None]


@dataclass(frozen=True)
class RightPanel:
    """Fertig gebautes Panel samt Widgets, die das MainWindow weiter direkt nutzt."""

    frame: QFrame
    # Geführter Workflow (Epic #418)
    stack: QStackedWidget
    step_title: QLabel
    step_desc: QLabel
    nav_prev: QPushButton
    nav_next: QPushButton
    open_button: QPushButton
    # Von Tab-Bausteinen weitergereichte Widgets (unveränderte Verdrahtung)
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
    preview_mode_combo: QComboBox
    preview_relief_label: QLabel
    preview_relief_slider: QSlider
    preview_gloss_visible: QCheckBox
    layer_panel: LayerPanel
    height_panel: HeightMapPanel

    # ── Schritt-Steuerung (vom MainWindow aufgerufen) ────────────────────
    def set_step(self, step: WorkflowStep) -> None:
        """Zeigt die Karten des Schritts und aktualisiert Kopf + Weiter-Label."""
        self.stack.setCurrentIndex(int(step) - 1)
        self.step_title.setText(_step_title(step))
        self.step_desc.setText(_step_desc(step))
        self.nav_next.setText(_step_next(step))
        self.nav_prev.setEnabled(step is not WorkflowStep.OPEN)


def build_right_panel(
    actions: RightPanelActions,
    layer_actions: LayerPanelActions,
    height_actions: HeightMapActions,
    *,
    on_open: Callable[[], None] | None = None,
) -> RightPanel:
    return _RightPanelBuilder(actions, layer_actions, height_actions, on_open).build()


class _RightPanelBuilder:
    """Orchestriert die Schritt-Seiten und befüllt das ``RightPanel``-DTO."""

    def __init__(
        self,
        actions: RightPanelActions,
        layer_actions: LayerPanelActions,
        height_actions: HeightMapActions,
        on_open: Callable[[], None] | None,
    ) -> None:
        self._actions = actions
        self._on_open = on_open
        self._layer_panel = LayerPanel(layer_actions)
        self._height_panel = HeightMapPanel(height_actions)

    def build(self) -> RightPanel:
        refs: dict[str, QWidget] = {}

        # Tab-Bausteine bauen (Aktions-Verdrahtung unverändert).
        preview_w, preview_refs = PreviewTab(self._actions).build()
        sel_w, sel_refs = SelectionTab(self._actions).build()
        bg_w, bg_refs = BackgroundTab(self._actions).build()
        adjust_w, adjust_refs = AdjustTab(self._actions).build()
        transform_w, transform_refs = TransformTab(self._actions).build()
        shape_w, shape_refs = ShapeTab(self._actions).build()
        layer_w, layer_refs = self._layer_panel.build()
        height_w, height_refs = self._height_panel.build()
        for r in (preview_refs, sel_refs, bg_refs, adjust_refs, transform_refs,
                  shape_refs, layer_refs, height_refs):
            refs.update(r)

        # Schritt-Seiten (Reihenfolge = WorkflowStep). Die Tab-Namen/-Tooltips
        # bleiben als barrierefreie Bezeichner referenziert (i18n-Coverage).
        open_page, open_button = self._build_open_page()
        stack = QStackedWidget()
        stack.addWidget(open_page)                                    # 1 Öffnen
        stack.addWidget(self._content_page([                          # 2 Freistellen
            (tr("right_panel.tab.selection"),
             tr("right_panel.tab.selection.tooltip"), sel_w),
            (tr("right_panel.tab.background"),
             tr("right_panel.tab.background.tooltip"), bg_w),
        ]))
        stack.addWidget(self._content_page([                          # 3 Anpassen
            (tr("right_panel.tab.adjust"),
             tr("right_panel.tab.adjust.tooltip"), adjust_w),
        ]))
        stack.addWidget(self._content_page([                          # 4 Form & Maße
            (tr("right_panel.tab.transform"),
             tr("right_panel.tab.transform.tooltip"), transform_w),
            (tr("right_panel.tab.shape"),
             tr("right_panel.tab.shape.tooltip"), shape_w),
        ]))
        stack.addWidget(self._content_page([                          # 5 Relief & Ebenen
            (tr("right_panel.tab.layers"),
             tr("right_panel.tab.layers.tooltip"), layer_w),
            (tr("right_panel.tab.height"),
             tr("right_panel.tab.height.tooltip"), height_w),
        ]))
        stack.addWidget(self._content_page([                          # 6 Export
            (tr("right_panel.tab.preview"),
             tr("right_panel.tab.preview.tooltip"), preview_w),
        ]))

        frame, title, desc, nav_prev, nav_next = self._assemble(stack)

        panel = RightPanel(
            frame=frame,
            stack=stack,
            step_title=title,
            step_desc=desc,
            nav_prev=nav_prev,
            nav_next=nav_next,
            open_button=open_button,
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
            preview_mode_combo=cast(QComboBox, refs["preview_mode_combo"]),
            preview_relief_label=cast(QLabel, refs["preview_relief_label"]),
            preview_relief_slider=cast(QSlider, refs["preview_relief_slider"]),
            preview_gloss_visible=cast(QCheckBox, refs["preview_gloss_visible"]),
            layer_panel=self._layer_panel,
            height_panel=self._height_panel,
        )
        panel.set_step(WorkflowStep.OPEN)
        return panel

    def _assemble(
        self, stack: QStackedWidget,
    ) -> tuple[QFrame, QLabel, QLabel, QPushButton, QPushButton]:
        """Baut Rahmen mit Kopf, Schritt-Stack und Navigations-Fußzeile."""
        frame = QFrame()
        frame.setFixedWidth(_RIGHT_PANEL_WIDTH)
        frame.setStyleSheet(_PANEL_STYLE)
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        head_lay = QVBoxLayout(header)
        head_lay.setContentsMargins(18, 16, 18, 8)
        head_lay.setSpacing(4)
        title = QLabel()
        title.setStyleSheet(
            f"color: {_Theme.TEXT_BRIGHT}; font-size: 16px; font-weight: 700;"
            " background: transparent;")
        desc = QLabel()
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {_Theme.TEXT_3}; font-size: 12px; background: transparent;")
        head_lay.addWidget(title)
        head_lay.addWidget(desc)
        outer.addWidget(header)
        outer.addWidget(stack, 1)

        nav = QFrame()
        nav.setFixedHeight(62)
        nav.setStyleSheet(NAV_BAR_STYLE)
        nav_lay = QHBoxLayout(nav)
        nav_lay.setContentsMargins(18, 0, 18, 0)
        nav_lay.setSpacing(10)
        nav_prev = QPushButton(tr("workflow.back"))
        nav_prev.setStyleSheet(NAV_BACK_STYLE)
        nav_next = QPushButton()
        nav_next.setStyleSheet(NAV_NEXT_STYLE)
        nav_lay.addWidget(nav_prev)
        nav_lay.addWidget(nav_next, 1)
        outer.addWidget(nav)
        return frame, title, desc, nav_prev, nav_next

    def _build_open_page(self) -> tuple[QWidget, QPushButton]:
        """Schritt 1: Ablagefeld + „Datei öffnen…" (Spec §9)."""
        page = QWidget()
        page.setStyleSheet(f"background: {_Theme.BG_PANEL};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        drop = QFrame()
        drop.setStyleSheet(
            f"QFrame {{ border: 2px dashed {_Theme.BORDER}; border-radius: 12px;"
            f" background: transparent; }}")
        drop_lay = QVBoxLayout(drop)
        drop_lay.setContentsMargins(18, 30, 18, 30)
        drop_lay.setSpacing(6)
        drop_title = QLabel(tr("workflow.open.drop"))
        drop_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_title.setStyleSheet(
            f"color: {_Theme.TEXT_BRIGHT}; font-size: 13px; font-weight: 600;"
            " background: transparent; border: none;")
        drop_fmt = QLabel(tr("workflow.open.formats"))
        drop_fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_fmt.setStyleSheet(
            f"color: {_Theme.TEXT_3}; font-size: 12px; background: transparent;"
            " border: none;")
        drop_lay.addWidget(drop_title)
        drop_lay.addWidget(drop_fmt)
        lay.addWidget(drop)

        open_btn = QPushButton(tr("workflow.open.button"))
        open_btn.setStyleSheet(PRIMARY_BTN_STYLE)
        on_open = self._on_open
        if on_open is not None:
            open_btn.clicked.connect(lambda _=False: on_open())
        lay.addWidget(open_btn)
        lay.addStretch()
        return page, open_btn

    @staticmethod
    def _content_page(items: list[tuple[str, str, QWidget]]) -> QWidget:
        """Baut eine Schritt-Seite aus (Name, Tooltip, Inhalt)-Tripeln.

        Der Tab-Name/-Tooltip bleibt als barrierefreier Bezeichner am Inhalt
        gesetzt (nutzt die bestehenden ``right_panel.tab.*``-Übersetzungen) –
        ohne zusätzliche sichtbare Überschrift.
        """
        page = QWidget()
        page.setStyleSheet(f"background: {_Theme.BG_PANEL};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        for name, tooltip, widget in items:
            widget.setAccessibleName(name)
            widget.setToolTip(tooltip)
            lay.addWidget(widget, 1)
        return page
