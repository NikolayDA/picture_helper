"""Dialog „Größe ändern…" – Zielgröße eines Bildes/Projekts in Pixeln (#359).

Rein Pixel-basiertes Resampling: Breite/Höhe in px, optionale Kopplung des
Seitenverhältnisses und Wahl des Resample-Verfahrens. Das eigentliche
Megapixel-Gate greift beim Anwenden im Canvas (``CanvasTransform.apply_resize``);
hier dient ein Hinweis-Label nur der Orientierung. mm/DPI-Editing ist bewusst
nicht Teil dieses Dialogs (späterer Rang).
"""
from __future__ import annotations

from PIL import Image
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from bgremover.constants import _MAX_MEGAPIXELS
from bgremover.i18n import tr
from bgremover.image_ops import resized_size

# Obergrenze je Achse: am Megapixel-Gate ausgerichtet, damit eine gültige
# Ausgangsgröße beim Vorbelegen **nie** stillschweigend geklemmt wird (eine
# einzelne Kante kann bei der anderen ≥ 1 px höchstens ``_MAX_MEGAPIXELS`` · 1e6
# groß sein und das Bild bleibt dennoch unter dem Limit). Das verbindliche Gate
# greift weiterhin im Canvas (#359-Review).
_MAX_EDGE = _MAX_MEGAPIXELS * 1_000_000


class ResizeDialog(QDialog):
    """Fragt eine Zielgröße in Pixeln samt Resample-Verfahren ab."""

    def __init__(self, width: int, height: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._orig_w = width
        self._orig_h = height
        self.setWindowTitle(tr("resize.title"))
        self.setMinimumWidth(360)
        self._build_ui(width, height)
        self._update_megapixels()

    def _build_ui(self, width: int, height: int) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(20, 20, 20, 20)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel(tr("resize.width")), 0, 0)
        self._w_spin = QSpinBox()
        # ``max(..., width)`` ist ein zusätzliches Sicherheitsnetz: selbst eine
        # untypisch große Ausgangsbreite wird beim Vorbelegen nicht geklemmt.
        self._w_spin.setRange(1, max(_MAX_EDGE, width))
        self._w_spin.setValue(width)
        self._w_spin.setSuffix(" px")
        grid.addWidget(self._w_spin, 0, 1)

        grid.addWidget(QLabel(tr("resize.height")), 1, 0)
        self._h_spin = QSpinBox()
        self._h_spin.setRange(1, max(_MAX_EDGE, height))
        self._h_spin.setValue(height)
        self._h_spin.setSuffix(" px")
        grid.addWidget(self._h_spin, 1, 1)
        lay.addLayout(grid)

        self._link = QCheckBox(tr("resize.link_aspect"))
        self._link.setChecked(True)
        lay.addWidget(self._link)

        resample_row = QHBoxLayout()
        resample_row.addWidget(QLabel(tr("resize.resample.label")))
        self._resample = QComboBox()
        # Literale ``tr(...)`` pro Eintrag, damit die i18n-Key-Hygiene-Tests die
        # Verwendung erkennen (Variablen-Keys würden nicht als referenziert gelten).
        self._resample.addItem(tr("resize.resample.lanczos"), Image.Resampling.LANCZOS)
        self._resample.addItem(tr("resize.resample.bicubic"), Image.Resampling.BICUBIC)
        self._resample.addItem(tr("resize.resample.bilinear"), Image.Resampling.BILINEAR)
        self._resample.addItem(tr("resize.resample.nearest"), Image.Resampling.NEAREST)
        resample_row.addWidget(self._resample, 1)
        lay.addLayout(resample_row)

        self._mp_label = QLabel()
        self._mp_label.setStyleSheet("color: #888; font-size: 11px;")
        lay.addWidget(self._mp_label)

        self._w_spin.valueChanged.connect(self._on_width_changed)
        self._h_spin.valueChanged.connect(self._on_height_changed)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton(tr("resize.cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton(tr("resize.ok"))
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

    # ── Seitenverhältnis-Kopplung ───────────────────────────────────────
    def _on_width_changed(self, value: int) -> None:
        if self._link.isChecked():
            _new_w, new_h = resized_size(self._orig_w, self._orig_h, target_w=value)
            # Signale blocken, sonst löst das Setzen der zweiten Kante eine
            # rekursive Rückkopplung aus.
            self._h_spin.blockSignals(True)
            self._h_spin.setValue(new_h)
            self._h_spin.blockSignals(False)
        self._update_megapixels()

    def _on_height_changed(self, value: int) -> None:
        if self._link.isChecked():
            new_w, _new_h = resized_size(self._orig_w, self._orig_h, target_h=value)
            self._w_spin.blockSignals(True)
            self._w_spin.setValue(new_w)
            self._w_spin.blockSignals(False)
        self._update_megapixels()

    def _update_megapixels(self) -> None:
        w, h = self.selected_size()
        self._mp_label.setText(tr(
            "resize.megapixels", mp=w * h / 1_000_000, maximum=_MAX_MEGAPIXELS))

    # ── Ergebnis ────────────────────────────────────────────────────────
    def selected_size(self) -> tuple[int, int]:
        """Gewählte Zielgröße als ``(width, height)`` px."""
        return (self._w_spin.value(), self._h_spin.value())

    def selected_resample(self) -> Image.Resampling:
        """Gewähltes Resample-Verfahren als Pillow-Enum."""
        return self._resample.currentData()
