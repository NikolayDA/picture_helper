"""Schwebende Zoom-Kontrolle auf der Arbeitsfläche (#464).

Glas-Pille unten rechts auf dem Canvas, 1:1 zum Prototyp: „−" · Live-
Prozentwert · „+" · Fixier-Schloss. Die eigentliche Zoom-Logik (Klemmen,
Schrittweite, Lock) liegt im bedienten Ziel (:class:`ZoomTarget`): auf der
2D-Leinwand ist das der :class:`~bgremover.canvas_viewport.CanvasViewport`,
in der 3D-Reliefvorschau die :class:`~bgremover.viewer_3d.Relief3DView`
(Kamera-Zoom, 100 % = eingepasste Ansicht). Dieses Widget ist reine Anzeige +
Bedienung und hält keinen eigenen Anwendungszustand. Der Zoom-/Lock-Zustand
ist reiner UI-State ohne Undo-/Redo-Eintrag.
"""
from __future__ import annotations

from typing import Protocol

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QWidget

from bgremover.constants import _ZOOM_CTRL_STEP_PCT
from bgremover.i18n import tr
from bgremover.icons import make_tool_icon
from bgremover.theme import Palette, active_palette, zoom_pill_style

# Abstand der Pille zur unteren/rechten Canvas-Kante (Prototyp: 14 px).
_MARGIN = 14
_BTN_SIZE = 24


class ZoomTarget(Protocol):
    """Minimaler Vertrag des von der Pille bedienten Zoom-Ziels.

    Klemmen, Schrittweite und Lock-Semantik implementiert das Ziel selbst;
    die Live-Prozentanzeige speist es über ``set_percent`` (Signalanbindung
    beim Aufbau, siehe ``canvas.py`` bzw. ``viewer_3d.py``).
    """

    def step_zoom(self, delta_pct: int) -> None: ...

    def set_zoom_locked(self, locked: bool) -> None: ...


class ZoomControl(QFrame):
    """Glas-Pille mit −/+, Prozentanzeige und Fixier-Lock (#464)."""

    def __init__(self, target: ZoomTarget, parent: QWidget) -> None:
        super().__init__(parent)
        self._target = target
        self.setObjectName("zoomPill")
        # Nötig, damit die Stylesheet-Fläche auf dem QFrame-Kind über dem
        # QGraphicsView-Viewport tatsächlich gemalt wird.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(2)

        self.btn_out = self._make_button("−", tr("zoom.out.tooltip"))
        self.btn_out.clicked.connect(
            lambda _=False: self._target.step_zoom(-_ZOOM_CTRL_STEP_PCT))
        lay.addWidget(self.btn_out)

        self.label = QLabel("100%")
        self.label.setObjectName("zoomLabel")
        self.label.setMinimumWidth(40)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.label)

        self.btn_in = self._make_button("+", tr("zoom.in.tooltip"))
        self.btn_in.clicked.connect(
            lambda _=False: self._target.step_zoom(_ZOOM_CTRL_STEP_PCT))
        lay.addWidget(self.btn_in)

        self.btn_lock = QToolButton()
        self.btn_lock.setIcon(make_tool_icon("lock", 26))
        self.btn_lock.setIconSize(QSize(13, 13))
        self.btn_lock.setCheckable(True)
        self.btn_lock.setFixedSize(_BTN_SIZE, _BTN_SIZE)
        self.btn_lock.setToolTip(tr("zoom.lock.tooltip"))
        self.btn_lock.toggled.connect(self._on_lock_toggled)
        lay.addWidget(self.btn_lock)

        self.apply_palette(active_palette())
        self.set_percent(100.0)

    @staticmethod
    def _make_button(text: str, tip: str) -> QToolButton:
        b = QToolButton()
        b.setText(text)
        b.setToolTip(tip)
        b.setFixedSize(_BTN_SIZE, _BTN_SIZE)
        return b

    # ── Zustand von außen (Canvas-Signale) ───────────────────

    def set_percent(self, percent: float) -> None:
        """Aktualisiert die Live-Prozentanzeige."""
        self.label.setText(f"{round(percent)}%")
        self.adjustSize()

    def apply_palette(self, p: Palette) -> None:
        """Restylt die Pille für ein Schema-Umschalten (#428)."""
        self.setStyleSheet(zoom_pill_style(p))

    def reposition(self) -> None:
        """Verankert die Pille unten rechts im Eltern-Widget."""
        parent = self.parentWidget()
        if parent is None:
            return
        self.adjustSize()
        self.move(parent.width() - self.width() - _MARGIN,
                  parent.height() - self.height() - _MARGIN)
        self.raise_()

    # ── Fixier-Lock ──────────────────────────────────────────

    def _on_lock_toggled(self, locked: bool) -> None:
        """Friert den Zoom ein bzw. gibt ihn frei; +/− folgen dem Zustand."""
        self._target.set_zoom_locked(locked)
        self.btn_in.setEnabled(not locked)
        self.btn_out.setEnabled(not locked)
        self.btn_lock.setToolTip(
            tr("zoom.unlock.tooltip") if locked else tr("zoom.lock.tooltip"))
