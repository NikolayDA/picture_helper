"""Crop-Bestätigungsleiste für das ``MainWindow``.

Wird über dem Canvas eingeblendet, sobald ein Crop-Overlay aktiv ist,
und blendet sich beim Bestätigen/Abbrechen wieder aus. Kapselt damit
Aufbau und Sichtbarkeitslogik weg vom ``MainWindow``.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from bgremover.constants import _CROP_BAR_HEIGHT
from bgremover.i18n import tr
from bgremover.theme import (
    CROP_BAR_STYLE,
    CROP_CANCEL_STYLE,
    CROP_CONFIRM_STYLE,
    CROP_LABEL_STYLE,
)

if TYPE_CHECKING:
    from bgremover.canvas import ImageCanvas


class CropBar(QFrame):
    """Bestätigungs-/Abbrechen-Leiste für den interaktiven Zuschnitt."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(CROP_BAR_STYLE)
        self.setFixedHeight(_CROP_BAR_HEIGHT)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 4, 14, 4)
        lay.setSpacing(10)

        label = QLabel(tr("crop_bar.label"))
        label.setStyleSheet(CROP_LABEL_STYLE)
        lay.addWidget(label)
        lay.addStretch()

        self._btn_confirm = QPushButton(tr("crop_bar.confirm"))
        self._btn_confirm.setStyleSheet(CROP_CONFIRM_STYLE)
        self._btn_cancel = QPushButton(tr("crop_bar.cancel"))
        self._btn_cancel.setStyleSheet(CROP_CANCEL_STYLE)
        lay.addWidget(self._btn_confirm)
        lay.addWidget(self._btn_cancel)

        self.setVisible(False)

    def bind(self, canvas: ImageCanvas) -> None:
        """Verbindet Buttons und Sichtbarkeit mit dem ``ImageCanvas``."""
        self._btn_confirm.clicked.connect(lambda: canvas.confirm_crop())
        self._btn_cancel.clicked.connect(lambda: canvas.cancel_crop())
        canvas.cropModeChanged.connect(self.setVisible)
