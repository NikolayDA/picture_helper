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
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from bgremover.i18n import tr
from bgremover.theme import Palette, active_palette, stepper_style


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
    """Ein anklickbarer Schritt: Kreis (Ziffer/✓) + Textlabel.

    Tastaturbedienbar (#441): Die Zelle ist fokussierbar (Tab-Reihenfolge),
    Enter/Leertaste aktivieren sie wie ein Klick. Die Fokus-Markierung folgt
    ``:focus-visible``-Semantik: Nur Tastatur-Navigation (Tab/Backtab) zeigt
    eine akzentgetönte, rahmenlose Fläche; ein Maus-Klick verändert das
    Layout nicht – der aktive Schritt sieht exakt aus wie im abgenommenen
    Prototyp (Spec §6). Gesperrte Zellen sind deaktiviert und fallen damit
    aus der Tab-Reihenfolge heraus.
    """

    clicked = pyqtSignal(int)

    def __init__(self, step: WorkflowStep, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._step = step
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Nötig, damit die Stylesheet-Regel auf einem nackten QWidget
        # tatsächlich greift (sonst Bleed der nativen Fensterfarbe, #444).
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # Ruhe-Regel: hält die Zelle transparent auf der Stepper-Fläche und
        # schirmt als selektorlose Regel zugleich Kreis und Label gegen das
        # ``border-bottom`` aus ``stepper_style`` ab – ohne sie bekämen beide
        # eine durchgeschlagene Haarlinie. ``focusOutEvent`` stellt genau
        # diese Regel wieder her.
        self.setStyleSheet("background: transparent; border: none;")
        self.setMinimumHeight(32)
        self.setAccessibleName(step_label(step))
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 2, 6, 2)
        lay.setSpacing(9)
        self._circle = QLabel()
        self._circle.setFixedSize(26, 26)
        self._circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Fester 28-px-Slot (die aktive Kreisgröße) um den Kreis: Der bewusste
        # 26↔28-Sprung aus ``apply_state`` (Spec §6) bleibt im Slot zentriert
        # und ändert die Zellbreite nicht mehr – ohne den Slot ließ jeder
        # Schrittwechsel alle Nachbarzellen horizontal springen (#514).
        slot = QWidget()
        slot.setFixedSize(28, 28)
        slot_lay = QHBoxLayout(slot)
        slot_lay.setContentsMargins(0, 0, 0, 0)
        slot_lay.setSpacing(0)
        slot_lay.addWidget(self._circle, 0, Qt.AlignmentFlag.AlignCenter)
        self._label = QLabel(step_label(step))
        # Label-Breite auf die breiteste Gewichtsvariante fixieren: Der Wechsel
        # 400→700 beim aktiven Schritt (Spec §6) ändert sonst die Textmetrik
        # und damit die Zellbreite (#514).
        self._label.setFixedWidth(self._reserved_label_width())
        lay.addWidget(slot)
        lay.addWidget(self._label)

    def _reserved_label_width(self) -> int:
        """Breite der breitesten Label-Variante (13 px, Gewicht 400 und 700).

        Reserviert einmalig bei der Konstruktion, damit ``apply_state`` die
        Zellgeometrie zustandsunabhängig lässt (#514).
        """
        font = QFont(self._label.font())
        font.setPixelSize(13)
        width = 0
        for weight in (QFont.Weight.Normal, QFont.Weight.Bold):
            font.setWeight(weight)
            width = max(width, QFontMetrics(font).size(0, self._label.text()).width())
        return width + 2  # kleine Reserve gegen Render-/Hinting-Rundung

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt-Override)
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(int(self._step))
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt-Override)
        if event is not None and event.key() in (
            Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space,
        ):
            self.clicked.emit(int(self._step))
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event) -> None:  # noqa: N802 (Qt-Override)
        # Wie ``:focus-visible`` im Browser-Prototyp: Nur Tastatur-Fokus
        # (Tab/Backtab) zeigt die getönte Fläche – nach Maus-Klick bleibt das
        # Layout exakt beim Prototyp (Spec §6). ``border: none`` ist Pflicht:
        # die selektorlose Regel gilt auch für Kreis und Label, ein ``border``
        # hier erschien früher als Doppelrahmen um den aktiven Schritt.
        if event is not None and event.reason() in (
            Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason,
        ):
            p = active_palette()
            self.setStyleSheet(
                f"background: {p.accent_soft}; border: none; border-radius: 8px;")
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:  # noqa: N802 (Qt-Override)
        # Ruhe-Regel aus dem Konstruktor wiederherstellen (Schild-Funktion).
        self.setStyleSheet("background: transparent; border: none;")
        super().focusOutEvent(event)

    def apply_state(self, *, done: bool, active: bool, enabled: bool) -> None:
        """Setzt Kreis- und Label-Stil für den Zustand des Schritts (aktive Palette)."""
        self.setEnabled(enabled)
        p = active_palette()
        num = int(self._step)
        # Der aktive Kreis ist 2 px größer als ausstehend/erledigt (28 vs. 26 px,
        # Spec §6) – das gibt ihm ohne echtes ``box-shadow`` (von Qt-QSS nicht
        # unterstützt) etwas von der Fokusring-Präsenz des Prototyps.
        if active:
            self._circle.setFixedSize(28, 28)
            self._circle.setText(str(num))
            self._circle.setStyleSheet(
                f"background: {p.accent}; color: {p.on_accent}; border-radius: 14px;"
                " font-size: 12px; font-weight: 600;")
            self._label.setStyleSheet(
                f"color: {p.text}; font-size: 13px; font-weight: 700;"
                " background: transparent;")
        elif done:
            self._circle.setFixedSize(26, 26)
            self._circle.setText("✓")
            self._circle.setStyleSheet(
                f"background: {p.accent_soft}; color: {p.accent_text};"
                f" border: 1px solid {p.accent_line}; border-radius: 13px;"
                " font-size: 12px; font-weight: 600;")
            self._label.setStyleSheet(
                f"color: {p.text3}; font-size: 13px; background: transparent;")
        else:
            self._circle.setFixedSize(26, 26)
            self._circle.setText(str(num))
            # Aktive (klickbare) ausstehende Schritte nutzen ``text3`` (≥ 4.5:1);
            # ``muted``/``divider`` bleiben den gesperrten Zellen vorbehalten (#441).
            color = p.text3 if enabled else p.divider
            self._circle.setStyleSheet(
                f"background: transparent; color: {color};"
                f" border: 1px solid {p.border}; border-radius: 13px; font-size: 12px;")
            self._label.setStyleSheet(
                f"color: {p.text3 if enabled else p.muted}; font-size: 13px;"
                " background: transparent;")


class Stepper(QWidget):
    """Horizontale Schrittleiste mit sechs Schritten.

    ``stepSelected`` trägt die 1-basierte Schrittnummer; die Navigation (und ihr
    Gating) liegt beim MainWindow.
    """

    stepSelected = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(72)
        self.setStyleSheet(stepper_style(active_palette()))
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

    def apply_palette(self, pal: Palette) -> None:
        """Restylt die Schrittleiste für ein Schema-Umschalten (#428)."""
        self.setStyleSheet(stepper_style(pal))
        self._refresh()

    def _refresh(self) -> None:
        p = active_palette()
        for step, cell in self._cells.items():
            enabled = (not self._locked) or step is WorkflowStep.OPEN
            cell.apply_state(
                done=step < self._current,
                active=step == self._current,
                enabled=enabled,
            )
        # Verbinder bis zum aktuellen Schritt einfärben (Spec §6: unfilled
        # nutzt die Haarlinie, nicht den dunkleren Divider-Ton).
        for i, conn in enumerate(self._connectors):
            # Verbinder i liegt zwischen Schritt (i+1) und (i+2).
            filled = (i + 2) <= int(self._current)
            color = p.accent_line if filled else p.hairline
            conn.setStyleSheet(f"background: {color}; border: none;")
