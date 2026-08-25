"""Persistenter Standard-/Experten-Umschalter im Inspector-Kopf (#806, Epic #805).

Pille 40×22 px mit 18-px-Knopf (Spec §15): „Aus" = Standard-Modus (Fläche
``inset``, Rand ``border_2``), „An" = Experten-Modus (Fläche/Rand ``accent``).
Gemalt statt über QSS-Indikatoren, weil eine gleitende Knopf-Position keine
Standard-``QCheckBox``-Subcontrol-Geometrie ist (Muster wie ``_DropFrame``,
``_recent_thumbnail_icon`` in ``right_panel.py``: eigene ``QPainter``-Fläche für
Layout, das die Style-Engine nicht abbildet). ``QAbstractButton`` liefert
Checkable-Zustand, Klick-/Space-Aktivierung und ``toggled``-Signal bereits;
Enter/Return wird zusätzlich verdrahtet (Spec-Anforderung „Enter/Leertaste").
"""
from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QKeyEvent, QPainter, QPaintEvent
from PyQt6.QtWidgets import QAbstractButton, QToolTip, QWidget

from bgremover.theme import Palette, active_palette

_WIDTH = 40
_HEIGHT = 22
_KNOB = 18
_MARGIN = 2
_KNOB_COLOR = "#ffffff"


class ExpertModeToggle(QAbstractButton):
    """Checkbare Pille: ``isChecked()`` True = Experten-Modus."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(_WIDTH, _HEIGHT)
        self._palette = active_palette()

    def apply_palette(self, p: Palette) -> None:
        """Restylt die Pille für ein Schema-Umschalten (analog ``ZoomControl``)."""
        self._palette = p
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802 (Qt-Override)
        return QSize(_WIDTH, _HEIGHT)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:  # noqa: N802
        # Space aktiviert QAbstractButton bereits nativ; Enter/Return ist bei
        # Checkables sonst wirkungslos (dem Prototyp-Kontrakt „Enter/Leertaste"
        # nach aber explizit gefordert) – Muster wie ``_DropFrame.keyPressEvent``.
        if event is not None and event.key() in (
            Qt.Key.Key_Return, Qt.Key.Key_Enter,
        ):
            self.click()
            return
        super().keyPressEvent(event)

    def show_mode_tooltip(self) -> None:
        """Zeigt den Tooltip aktiv unter der Pille an.

        Qt blendet Tooltips nur bei Maus-Hover ein; für Tastatur- und
        Touch-Bedienung wird die Modus-Erklärung deshalb beim Fokus (und vom
        Panel nach einem Umschalten mit gehaltenem Fokus) explizit gezeigt.
        """
        if self.toolTip():
            QToolTip.showText(
                self.mapToGlobal(self.rect().bottomLeft()), self.toolTip(), self)

    def focusInEvent(self, event) -> None:  # noqa: N802
        super().focusInEvent(event)
        self.update()
        self.show_mode_tooltip()

    def focusOutEvent(self, event) -> None:  # noqa: N802
        super().focusOutEvent(event)
        QToolTip.hideText()
        self.update()

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        p = self._palette
        on = self.isChecked()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0.5, 0.5, _WIDTH - 1, _HEIGHT - 1)
        radius = _HEIGHT / 2
        painter.setPen(QColor(p.accent if on else p.border_2))
        painter.setBrush(QColor(p.accent if on else p.inset))
        painter.drawRoundedRect(rect, radius, radius)

        knob_x = _WIDTH - _MARGIN - _KNOB if on else _MARGIN
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(_KNOB_COLOR))
        painter.drawEllipse(QRectF(knob_x, _MARGIN, _KNOB, _KNOB))

        if self.hasFocus():
            focus_pen = QColor(p.accent)
            painter.setPen(focus_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)

        painter.end()
