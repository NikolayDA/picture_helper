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
from pathlib import Path
from typing import cast

from PyQt6.QtCore import QSignalBlocker, Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
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
    _CARD_STACK_SPACING,
    AdjustTab,
    BackgroundTab,
    PreviewTab,
    SelectionTab,
    ShapeTab,
    TransformTab,
    _ModeSegments,
)
from bgremover.stepper import WorkflowStep
from bgremover.theme import (
    _Theme,
    active_palette,
    card_style,
    nav_back_style,
    nav_bar_style,
    nav_next_style,
    panel_frame_style,
    primary_btn_style,
    scroll_style,
    section_header_style,
)

# Wird von ``tests/test_theme.py`` referenziert und hält den Akzent-Token für
# die (weiterhin verfügbare) Tab-Optik bereit; der geführte Workflow selbst
# nutzt den QStackedWidget-Aufbau.
TAB_STYLE = f"""
    QTabWidget::pane {{ border: none; background: {_Theme.BG_PANEL}; }}
    QTabBar::tab:selected {{ border-bottom: 3px solid {_Theme.ACCENT}; }}
"""


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


# Vom Ablagefeld (Schritt 1) akzeptierte Bild-Endungen – deckungsgleich mit dem
# Canvas-Drop (``ImageCanvas.dropEvent``); die eigentliche Validierung erledigt
# der gemeinsame asynchrone Ladepfad.
_DROP_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".gif")


class _DropFrame(QFrame):
    """Ablagefeld in Schritt 1: nimmt Bild-Dateien per Drag & Drop entgegen und
    leitet den Pfad an den validierten Ladepfad weiter; ein Klick öffnet den
    Datei-Dialog (PR #423-Review). Tastatur (#441): fokussierbar, Enter/Leertaste
    öffnen ebenfalls den Dialog – redundant zum „Datei öffnen…"-Button darunter."""

    def __init__(
        self,
        on_open: Callable[[], None] | None,
        on_open_path: Callable[[str], None] | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_open = on_open
        self._on_open_path = on_open_path
        self.setAcceptDrops(on_open_path is not None)
        if on_open is not None:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt-Override)
        if (event is not None
                and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space)
                and self._on_open is not None):
            self._on_open()
            return
        super().keyPressEvent(event)

    @staticmethod
    def _image_paths(event: QDragEnterEvent | QDropEvent) -> list[str]:
        mime = event.mimeData()
        if mime is None:
            return []
        return [
            url.toLocalFile() for url in mime.urls()
            if Path(url.toLocalFile()).suffix.lower() in _DROP_EXTS
        ]

    def dragEnterEvent(self, event: QDragEnterEvent | None) -> None:  # noqa: N802
        if event is not None and self._image_paths(event):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent | None) -> None:  # noqa: N802
        if event is None:
            return
        paths = self._image_paths(event)
        if paths and self._on_open_path is not None:
            event.acceptProposedAction()
            self._on_open_path(paths[0])

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        if (event is not None
                and event.button() == Qt.MouseButton.LeftButton
                and self._on_open is not None):
            self._on_open()
        super().mousePressEvent(event)


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
    # §9-Angleich (#436–#440): Aktionen, die vorher nur über Toolbar/Menü
    # erreichbar waren, sind jetzt direkt im Schritt-Inspector verdrahtet.
    run_ai: Callable[[], None]
    apply_resize: Callable[[int, int], None]
    save: Callable[[], None]
    export_eufymake: Callable[[], None]
    set_save_format: Callable[[str], None]


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
    ai_button: QPushButton
    # Von Tab-Bausteinen weitergereichte Widgets (unveränderte Verdrahtung)
    tolerance_label: QLabel
    tolerance_slider: QSlider
    brush_label: QLabel
    brush_slider: QSlider
    morph_spin: QSpinBox
    resize_w: QSpinBox
    resize_h: QSpinBox
    color_button: QPushButton
    rotation_slider: QSlider
    rotation_spin: QSpinBox
    corner_label: QLabel
    corner_slider: QSlider
    preview_mode_segments: _ModeSegments
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
        # QPushButton behandelt „&" sonst als Mnemonic-Marker und verschluckt es
        # (z. B. „Relief & Ebenen" → „Relief _benen"); Labels sind reiner Text.
        self.nav_next.setText(_step_next(step).replace("&", "&&"))
        self.nav_prev.setEnabled(step is not WorkflowStep.OPEN)

    def set_selection_values(self, *, tolerance: int, brush_size: int) -> None:
        """Spiegelt Canvas-Auswahlwerte nach einem Panel-Neuaufbau ohne Feedback."""
        _set_value_silently(self.tolerance_slider, tolerance)
        self.tolerance_label.setText(
            tr("right_panel.selection.tolerance", value=tolerance))
        _set_value_silently(self.brush_slider, brush_size)
        self.brush_label.setText(
            tr("right_panel.selection.brush_size", value=brush_size))

    def set_project_size(self, width: int, height: int) -> None:
        """Spiegelt die aktuelle Projektgröße in die Inline-Resize-Felder."""
        _set_value_silently(self.resize_w, width)
        _set_value_silently(self.resize_h, height)


def build_right_panel(
    actions: RightPanelActions,
    layer_actions: LayerPanelActions,
    height_actions: HeightMapActions,
    *,
    on_open: Callable[[], None] | None = None,
    on_open_path: Callable[[str], None] | None = None,
    recent: list[str] | None = None,
    rembg_available: bool = True,
) -> RightPanel:
    return _RightPanelBuilder(
        actions, layer_actions, height_actions, on_open, on_open_path, recent,
        rembg_available).build()


def _set_value_silently(widget: QSlider | QSpinBox, value: int) -> None:
    blocker = QSignalBlocker(widget)
    try:
        widget.setValue(value)
    finally:
        del blocker


class _RightPanelBuilder:
    """Orchestriert die Schritt-Seiten und befüllt das ``RightPanel``-DTO."""

    def __init__(
        self,
        actions: RightPanelActions,
        layer_actions: LayerPanelActions,
        height_actions: HeightMapActions,
        on_open: Callable[[], None] | None,
        on_open_path: Callable[[str], None] | None,
        recent: list[str] | None,
        rembg_available: bool,
    ) -> None:
        self._actions = actions
        self._on_open = on_open
        self._on_open_path = on_open_path
        self._recent = recent or []
        self._rembg_available = rembg_available
        self._layer_panel = LayerPanel(layer_actions)
        self._height_panel = HeightMapPanel(height_actions)

    def build(self) -> RightPanel:
        refs: dict[str, QWidget] = {}

        # Tab-Bausteine bauen (Aktions-Verdrahtung unverändert).
        preview_w, preview_refs = PreviewTab(self._actions).build()
        sel_w, sel_refs = SelectionTab(
            self._actions, rembg_available=self._rembg_available).build()
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
            ai_button=cast(QPushButton, refs["ai_remove"]),
            tolerance_label=cast(QLabel, refs["tolerance_label"]),
            tolerance_slider=cast(QSlider, refs["tolerance_slider"]),
            brush_label=cast(QLabel, refs["brush_label"]),
            brush_slider=cast(QSlider, refs["brush_slider"]),
            morph_spin=cast(QSpinBox, refs["morph_spin"]),
            resize_w=cast(QSpinBox, refs["resize_w"]),
            resize_h=cast(QSpinBox, refs["resize_h"]),
            color_button=cast(QPushButton, refs["color_button"]),
            rotation_slider=cast(QSlider, refs["rotation_slider"]),
            rotation_spin=cast(QSpinBox, refs["rotation_spin"]),
            corner_label=cast(QLabel, refs["corner_label"]),
            corner_slider=cast(QSlider, refs["corner_slider"]),
            preview_mode_segments=cast(_ModeSegments, refs["preview_mode_segments"]),
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
        p = active_palette()
        frame = QFrame()
        frame.setObjectName("inspectorPanel")
        frame.setFixedWidth(_RIGHT_PANEL_WIDTH)
        frame.setStyleSheet(panel_frame_style(p))
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header.setObjectName("inspectorHeader")
        head_lay = QVBoxLayout(header)
        head_lay.setContentsMargins(18, 16, 18, 8)
        head_lay.setSpacing(4)
        title = QLabel()
        title.setStyleSheet(
            f"color: {p.text}; font-size: 16px; font-weight: 700;"
            " background: transparent;")
        desc = QLabel()
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {p.text3}; font-size: 12px; background: transparent;")
        head_lay.addWidget(title)
        head_lay.addWidget(desc)
        outer.addWidget(header)
        outer.addWidget(stack, 1)

        nav = QFrame()
        nav.setFixedHeight(62)
        nav.setStyleSheet(nav_bar_style(p))
        nav_lay = QHBoxLayout(nav)
        nav_lay.setContentsMargins(18, 0, 18, 0)
        nav_lay.setSpacing(10)
        nav_prev = QPushButton(tr("workflow.back"))
        nav_prev.setStyleSheet(nav_back_style(p))
        nav_next = QPushButton()
        nav_next.setStyleSheet(nav_next_style(p))
        nav_lay.addWidget(nav_prev)
        nav_lay.addWidget(nav_next, 1)
        outer.addWidget(nav)
        return frame, title, desc, nav_prev, nav_next

    def _build_open_page(self) -> tuple[QWidget, QPushButton]:
        """Schritt 1: Ablagefeld + „Datei öffnen…" (Spec §9)."""
        p = active_palette()
        page = QWidget()
        page.setObjectName("stepPage")
        page.setStyleSheet(f"background: {p.inspector};")
        lay = QVBoxLayout(page)
        # Scrollbereich-Innenabstand 1:1 aus dem Prototyp (§1).
        lay.setContentsMargins(18, 20, 18, 18)
        lay.setSpacing(11)

        drop = _DropFrame(self._on_open, self._on_open_path)
        drop.setStyleSheet(
            f"QFrame {{ border: 2px dashed {p.border}; border-radius: 12px;"
            f" background: transparent; }}"
            f"QFrame:focus {{ border: 2px dashed {p.accent}; }}")
        drop_lay = QVBoxLayout(drop)
        drop_lay.setContentsMargins(18, 30, 18, 30)
        drop_lay.setSpacing(6)
        drop_title = QLabel(tr("workflow.open.drop"))
        drop_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_title.setStyleSheet(
            f"color: {p.text}; font-size: 13px; font-weight: 600;"
            " background: transparent; border: none;")
        drop_fmt = QLabel(tr("workflow.open.formats"))
        drop_fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_fmt.setStyleSheet(
            f"color: {p.text3}; font-size: 12px; background: transparent;"
            " border: none;")
        drop_lay.addWidget(drop_title)
        drop_lay.addWidget(drop_fmt)
        lay.addWidget(drop)

        open_btn = QPushButton(tr("workflow.open.button"))
        open_btn.setStyleSheet(primary_btn_style(p))
        on_open = self._on_open
        if on_open is not None:
            open_btn.clicked.connect(lambda _=False: on_open())
        lay.addWidget(open_btn)

        recent_card = self._build_recent_card()
        if recent_card is not None:
            lay.addWidget(recent_card)

        lay.addStretch()
        return page, open_btn

    def _build_recent_card(self) -> QWidget | None:
        """Karte „Zuletzt geöffnet" mit bis zu drei Einträgen (§9 Schritt 1, #436)."""
        entries = self._recent[:3]
        if not entries or self._on_open_path is None:
            return None
        on_open_path = self._on_open_path
        pal = active_palette()
        card = QFrame()
        card.setObjectName("recentCard")
        card.setStyleSheet(f"QFrame#recentCard {{ {card_style(pal)} }}")
        v = QVBoxLayout(card)
        v.setContentsMargins(14, 13, 14, 13)
        v.setSpacing(6)
        title = QLabel(tr("workflow.open.recent").upper())
        title.setStyleSheet(section_header_style(pal))
        v.addWidget(title)
        for path in entries:
            row = QPushButton(Path(path).name)
            row.setToolTip(path)
            row.setStyleSheet(
                "QPushButton { background:transparent; border:none; text-align:left;"
                f" color:{pal.text}; font-size:12px;"
                " padding:7px 8px; border-radius:8px; }"
                f"QPushButton:hover {{ background:{pal.hover}; }}"
                f"QPushButton:focus {{ outline:none; border:1px solid {pal.accent}; }}")
            row.clicked.connect(lambda _=False, p=path: on_open_path(p))
            v.addWidget(row)
        return card

    @staticmethod
    def _normalize_content_block_margins(
        widget: QWidget, *, first: bool, last: bool,
    ) -> None:
        """Verhindert doppelte Außenabstände zwischen kombinierten Schritt-Blöcken."""
        layout = widget.layout()
        if layout is None:
            return
        while layout.count():
            item = layout.itemAt(layout.count() - 1)
            if item.widget() is not None or item.layout() is not None:
                break
            layout.takeAt(layout.count() - 1)
        if first and last:
            return
        left, top, right, bottom = layout.getContentsMargins()
        layout.setContentsMargins(
            left,
            top if first else _CARD_STACK_SPACING,
            right,
            bottom if last else 0,
        )

    @staticmethod
    def _content_page(items: list[tuple[str, str, QWidget]]) -> QWidget:
        """Baut eine Schritt-Seite aus (Name, Tooltip, Inhalt)-Tripeln.

        Der Tab-Name/-Tooltip bleibt als barrierefreier Bezeichner am Inhalt
        gesetzt (nutzt die bestehenden ``right_panel.tab.*``-Übersetzungen) –
        ohne zusätzliche sichtbare Überschrift.
        """
        p = active_palette()
        page = QWidget()
        page.setObjectName("stepPage")
        page.setStyleSheet(f"background: {p.inspector};")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(scroll_style(p))
        container = QWidget()
        container.setStyleSheet(f"background: {p.inspector};")
        clay = QVBoxLayout(container)
        clay.setContentsMargins(0, 0, 0, 0)
        clay.setSpacing(0)
        for index, (name, tooltip, widget) in enumerate(items):
            widget.setAccessibleName(name)
            widget.setToolTip(tooltip)
            _RightPanelBuilder._normalize_content_block_margins(
                widget, first=index == 0, last=index == len(items) - 1)
            clay.addWidget(widget)
        clay.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)
        return page
