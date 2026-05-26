"""Crop-Bestaetigungsleiste fuer ``MainWindow``."""
from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from bgremover.constants import _CROP_BAR_HEIGHT
from bgremover.theme import (
    CROP_BAR_STYLE,
    CROP_CANCEL_STYLE,
    CROP_CONFIRM_STYLE,
    CROP_LABEL_STYLE,
)


class CropBar(QFrame):
    """Kleine Leiste zum Anwenden oder Abbrechen eines aktiven Zuschnitts."""

    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(CROP_BAR_STYLE)
        self.setFixedHeight(_CROP_BAR_HEIGHT)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 4, 14, 4)
        layout.setSpacing(10)

        crop_label = QLabel("✂  Ausschnitt positionieren, dann bestätigen:")
        crop_label.setStyleSheet(CROP_LABEL_STYLE)
        layout.addWidget(crop_label)
        layout.addStretch()

        self.btn_confirm = QPushButton("✓  Zuschnitt anwenden")
        self.btn_confirm.setStyleSheet(CROP_CONFIRM_STYLE)
        self.btn_cancel = QPushButton("✗  Abbrechen")
        self.btn_cancel.setStyleSheet(CROP_CANCEL_STYLE)
        layout.addWidget(self.btn_confirm)
        layout.addWidget(self.btn_cancel)
        self.setVisible(False)

    def bind(self, canvas) -> None:
        canvas.cropModeChanged.connect(self.setVisible)
        self.btn_confirm.clicked.connect(lambda: canvas.confirm_crop())
        self.btn_cancel.clicked.connect(lambda: canvas.cancel_crop())
