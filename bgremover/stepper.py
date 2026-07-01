"""Schrittleiste des geführten Workflows (Epic #418, Issue #419).

Ein schlankes, zustandsloses Widget: sechs Schritte, horizontal und mittig,
durch Linien verbunden. Jeder Schritt kennt drei Zustände – **ausstehend**
(Ziffer), **erledigt** (✓) und **aktiv** (blaue Hervorhebung). Ein Klick auf
einen Schritt sendet :data:`Stepper.stepSelected` mit der 1-basierten
Schrittnummer; das MainWindow entscheidet über die Navigation (Gating).

Das Widget hält selbst keinen Anwendungszustand – ``set_current`` und
``set_locked`` werden vom MainWindow gesetzt. Alle Labels laufen über ``tr()``.
"""
from __future__ import annotations

from enum import IntEnum

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from bgremover.i18n import tr
from bgremover.theme import STEPPER_STYLE, _Theme


class WorkflowStep(IntEnum):
    """Die sechs Schritte des geführten Workflows (1-basiert)."""

    OPEN = 1
    CUTOUT = 2
    ADJUST = 3
    SHAPE = 4
    RELIEF = 5
    EXPORT = 6


def step_label(step: WorkflowStep) -> str:
    """Übersetztes Kurzlabel eines Schritts (literale ``tr``-Keys für i18n-Coverage)."""
    if step is WorkflowStep.OPEN:
        return tr("workflow.step.open")
    if step is WorkflowStep.CUTOUT:
        return tr("workflow.step.cutout")
    if step is WorkflowStep.ADJUST:
        return tr("workflow.step.adjust")
    if step is WorkflowStep.SHAPE:
        return tr("workflow.step.shape")
    if step is WorkflowStep.RELIEF:
        return tr("workflow.step.relief")
    return tr("workflow.step.export")


class _StepCell(QWidget):
    """Ein anklickbarer Schritt: Kreis (Ziffer/✓) + Textlabel."""

    clicked = pyqtSignal(int)

    def __init__(self, step: WorkflowStep, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._step = step
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(9)
        self._circle = QLabel()
        self._circle.setFixedSize(28, 28)
        self._circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label = QLabel(step_label(step))
        lay.addWidget(self._circle)
        lay.addWidget(self._label)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt-Override)
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(int(self._step))
        super().mousePressEvent(event)

    def apply_state(self, *, done: bool, active: bool, enabled: bool) -> None:
        """Setzt Kreis- und Label-Stil für den Zustand des Schritts."""
        self.setEnabled(enabled)
        num = int(self._step)
        if active:
            self._circle.setText(str(num))
            self._circle.setStyleSheet(
                f"background: {_Theme.ACCENT}; color: #fff; border-radius: 14px;"
                " font-size: 12px; font-weight: 600;")
            self._label.setStyleSheet(
                f"color: {_Theme.TEXT_BRIGHT}; font-size: 13px; font-weight: 700;"
                " background: transparent;")
        elif done:
            self._circle.setText("✓")
            self._circle.setStyleSheet(
                f"background: {_Theme.ACCENT_SOFT}; color: {_Theme.ACCENT_TEXT};"
                f" border: 1px solid {_Theme.ACCENT_LINE}; border-radius: 14px;"
                " font-size: 12px; font-weight: 600;")
            self._label.setStyleSheet(
                f"color: {_Theme.TEXT_3}; font-size: 13px; background: transparent;")
        else:
            self._circle.setText(str(num))
            color = _Theme.MUTED if enabled else _Theme.DIVIDER
            self._circle.setStyleSheet(
                f"color: {color}; border: 1px solid {_Theme.BORDER};"
                " border-radius: 14px; font-size: 12px;")
            self._label.setStyleSheet(
                f"color: {_Theme.MUTED}; font-size: 13px; background: transparent;")


class Stepper(QWidget):
    """Horizontale Schrittleiste mit sechs Schritten.

    ``stepSelected`` trägt die 1-basierte Schrittnummer; die Navigation (und ihr
    Gating) liegt beim MainWindow.
    """

    stepSelected = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(64)
        self.setStyleSheet(STEPPER_STYLE)
        self._current = WorkflowStep.OPEN
        self._locked = False
        self._cells: dict[WorkflowStep, _StepCell] = {}
        self._connectors: list[QFrame] = []

        outer = QHBoxLayout(self)
        outer.setContentsMargins(26, 0, 26, 0)
        outer.setSpacing(0)
        for i, step in enumerate(WorkflowStep):
            if i > 0:
                conn = QFrame()
                conn.setFixedHeight(2)
                conn.setFrameShape(QFrame.Shape.NoFrame)
                self._connectors.append(conn)
                outer.addWidget(conn, 1)
            cell = _StepCell(step)
            cell.clicked.connect(self.stepSelected)
            self._cells[step] = cell
            outer.addWidget(cell)
        self._refresh()

    # ── Zustandssteuerung (vom MainWindow) ───────────────────────────────
    def set_current(self, step: int) -> None:
        """Hebt den aktiven Schritt hervor und aktualisiert erledigt/ausstehend."""
        self._current = WorkflowStep(step)
        self._refresh()

    def set_locked(self, locked: bool) -> None:
        """Sperrt die Schritte 2–6 (kein Bild geladen); Schritt 1 bleibt frei."""
        self._locked = locked
        self._refresh()

    def _refresh(self) -> None:
        for step, cell in self._cells.items():
            enabled = (not self._locked) or step is WorkflowStep.OPEN
            cell.apply_state(
                done=step < self._current,
                active=step == self._current,
                enabled=enabled,
            )
        # Verbinder bis zum aktuellen Schritt einfärben.
        for i, conn in enumerate(self._connectors):
            # Verbinder i liegt zwischen Schritt (i+1) und (i+2).
            filled = (i + 2) <= int(self._current)
            color = _Theme.ACCENT_LINE if filled else _Theme.DIVIDER
            conn.setStyleSheet(f"background: {color}; border: none;")
