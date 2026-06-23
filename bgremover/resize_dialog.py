"""Dialog „Größe ändern…" – Zielgröße in Pixeln **oder** mm/DPI (#359, #377).

Zwei Maßeinheiten-Modi:

- **Pixel** (Standard, #359): Breite/Höhe in px, optionale Seitenverhältnis-Kopplung,
  Resample-Verfahren.
- **Millimeter** (#377): physische Breite/Höhe in mm plus **DPI**; die resultierende
  **Pixelgröße** wird live über die geteilte Geometrie (:mod:`bgremover.units`, #376)
  angezeigt. Zusätzlich vergleicht eine **Druckflächenprüfung** das Motiv gegen eine
  wählbare Zielmediumgröße und warnt bei Überschreitung.

Das eigentliche Megapixel-Gate greift beim Anwenden im Canvas
(``CanvasTransform.apply_resize``); hier dienen die Hinweis-Labels der Orientierung.
Im mm-Modus liefert der Dialog zusätzlich physische Größe (mm) und DPI, die der
Aufrufer über die ``project_model``-Setter (#376) im Projekt verankert; das
Resampling selbst bleibt rein pixelbasiert.
"""
from __future__ import annotations

from PIL import Image
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
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
from bgremover.units import mm_from_px_dpi, pixel_size_for_size_mm

# Obergrenze je Achse: am Megapixel-Gate ausgerichtet, damit eine gültige
# Ausgangsgröße beim Vorbelegen **nie** stillschweigend geklemmt wird (eine
# einzelne Kante kann bei der anderen ≥ 1 px höchstens ``_MAX_MEGAPIXELS`` · 1e6
# groß sein und das Bild bleibt dennoch unter dem Limit). Das verbindliche Gate
# greift weiterhin im Canvas (#359-Review).
_MAX_EDGE = _MAX_MEGAPIXELS * 1_000_000

# Standard-Auflösung für die Vorbelegung des mm-Modus, falls das Projekt noch
# keine physische Größe trägt (300 DPI ist ein verbreiteter Druck-Default).
_DEFAULT_DPI = 300.0

# Voreingestellte Zielmedien (Name → (Breite, Höhe) in mm) für die
# Druckflächenprüfung. Namen sind Eigennamen und werden nicht übersetzt.
_MEDIA: tuple[tuple[str, tuple[float, float]], ...] = (
    ("A3", (297.0, 420.0)),
    ("A4", (210.0, 297.0)),
    ("A5", (148.0, 210.0)),
    ("Letter", (215.9, 279.4)),
)
_DEFAULT_MEDIUM_INDEX = 1  # A4


class ResizeDialog(QDialog):
    """Fragt eine Zielgröße in Pixeln **oder** mm/DPI samt Resample-Verfahren ab."""

    def __init__(
        self,
        width: int,
        height: int,
        parent: QWidget | None = None,
        *,
        dpi: tuple[float, float] | None = None,
    ) -> None:
        super().__init__(parent)
        self._orig_w = width
        self._orig_h = height
        # mm-/DPI-Vorbelegung: das DPI-Feld ist **uniform** (eine Auflösung für
        # beide Achsen). Damit ein Öffnen-und-Bestätigen ohne Änderung die
        # Pixelgröße exakt erhält (kein überraschendes Resampling), werden die
        # mm-Felder aus der **aktuellen Pixelgröße bei dieser DPI** abgeleitet –
        # auch für Projekte mit (seltener) achsenungleicher DPI. Für die übliche
        # uniforme DPI deckt sich das exakt mit der gespeicherten physischen Größe.
        self._init_dpi = dpi[0] if dpi is not None else _DEFAULT_DPI
        self._init_mm = (
            mm_from_px_dpi(width, self._init_dpi),
            mm_from_px_dpi(height, self._init_dpi),
        )
        self.setWindowTitle(tr("resize.title"))
        self.setMinimumWidth(380)
        self._build_ui(width, height)
        self._on_mode_changed()

    # ── Aufbau ──────────────────────────────────────────────────────────
    def _build_ui(self, width: int, height: int) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(20, 20, 20, 20)

        # Maßeinheit-Umschaltung (Pixel ↔ mm/DPI).
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel(tr("resize.mode.label")))
        self._mode = QComboBox()
        self._mode.addItem(tr("resize.mode.pixel"), "px")
        self._mode.addItem(tr("resize.mode.mm"), "mm")
        mode_row.addWidget(self._mode, 1)
        lay.addLayout(mode_row)

        lay.addWidget(self._build_px_group(width, height))
        lay.addWidget(self._build_mm_group())

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

        self._print_label = QLabel()
        self._print_label.setWordWrap(True)
        self._print_label.setStyleSheet("font-size: 11px;")
        lay.addWidget(self._print_label)

        self._mode.currentIndexChanged.connect(self._on_mode_changed)
        self._link.toggled.connect(self._on_link_toggled)
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

    def _build_px_group(self, width: int, height: int) -> QWidget:
        group = QWidget()
        grid = QGridLayout(group)
        grid.setContentsMargins(0, 0, 0, 0)
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
        self._px_group = group
        return group

    def _build_mm_group(self) -> QWidget:
        group = QWidget()
        grid = QGridLayout(group)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel(tr("resize.width_mm")), 0, 0)
        self._w_mm = QDoubleSpinBox()
        self._w_mm.setRange(0.1, 1_000_000.0)
        self._w_mm.setDecimals(1)
        self._w_mm.setSuffix(" mm")
        self._w_mm.setValue(round(self._init_mm[0], 1))
        grid.addWidget(self._w_mm, 0, 1)

        grid.addWidget(QLabel(tr("resize.height_mm")), 1, 0)
        self._h_mm = QDoubleSpinBox()
        self._h_mm.setRange(0.1, 1_000_000.0)
        self._h_mm.setDecimals(1)
        self._h_mm.setSuffix(" mm")
        self._h_mm.setValue(round(self._init_mm[1], 1))
        grid.addWidget(self._h_mm, 1, 1)

        grid.addWidget(QLabel(tr("resize.dpi")), 2, 0)
        self._dpi = QDoubleSpinBox()
        self._dpi.setRange(1.0, 10_000.0)
        self._dpi.setDecimals(0)
        self._dpi.setSuffix(" DPI")
        self._dpi.setValue(round(self._init_dpi))
        grid.addWidget(self._dpi, 2, 1)

        grid.addWidget(QLabel(tr("resize.medium.label")), 3, 0)
        self._medium = QComboBox()
        for name, size in _MEDIA:
            self._medium.addItem(name, size)
        self._medium.setCurrentIndex(_DEFAULT_MEDIUM_INDEX)
        grid.addWidget(self._medium, 3, 1)

        self._w_mm.valueChanged.connect(self._on_w_mm_changed)
        self._h_mm.valueChanged.connect(self._on_h_mm_changed)
        self._dpi.valueChanged.connect(self._refresh_mm)
        self._medium.currentIndexChanged.connect(self._refresh_mm)
        self._mm_group = group
        return group

    # ── Modus ───────────────────────────────────────────────────────────
    def _is_mm_mode(self) -> bool:
        return self._mode.currentData() == "mm"

    def _on_mode_changed(self) -> None:
        mm = self._is_mm_mode()
        self._px_group.setVisible(not mm)
        self._mm_group.setVisible(mm)
        if mm:
            self._refresh_mm()
        else:
            self._print_label.setText("")
            self._update_megapixels()

    def _on_link_toggled(self, _checked: bool) -> None:
        # Beim (Wieder-)Einschalten der Kopplung die abhängige Kante angleichen.
        if self._link.isChecked():
            if self._is_mm_mode():
                self._on_w_mm_changed(self._w_mm.value())
            else:
                self._on_width_changed(self._w_spin.value())

    # ── Pixel-Modus (Seitenverhältnis-Kopplung) ─────────────────────────
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
        w, h = self._w_spin.value(), self._h_spin.value()
        self._mp_label.setText(tr(
            "resize.megapixels", mp=w * h / 1_000_000, maximum=_MAX_MEGAPIXELS))

    # ── mm/DPI-Modus ─────────────────────────────────────────────────────
    def _on_w_mm_changed(self, value: float) -> None:
        if self._link.isChecked() and self._orig_w > 0:
            ratio = self._orig_h / self._orig_w
            self._h_mm.blockSignals(True)
            self._h_mm.setValue(round(value * ratio, 1))
            self._h_mm.blockSignals(False)
        self._refresh_mm()

    def _on_h_mm_changed(self, value: float) -> None:
        if self._link.isChecked() and self._orig_h > 0:
            ratio = self._orig_w / self._orig_h
            self._w_mm.blockSignals(True)
            self._w_mm.setValue(round(value * ratio, 1))
            self._w_mm.blockSignals(False)
        self._refresh_mm()

    def _refresh_mm(self) -> None:
        w_px, h_px = self._mm_pixel_size()
        self._mp_label.setText(tr(
            "resize.pixels_result", width=w_px, height=h_px, mp=round(w_px * h_px / 1_000_000, 1)))
        medium = self._medium.currentData()
        name = self._medium.currentText()
        w_mm, h_mm = self._w_mm.value(), self._h_mm.value()
        if self.print_area_exceeded():
            self._print_label.setStyleSheet("color: #b00; font-size: 11px;")
            self._print_label.setText(tr(
                "resize.print_area_exceeded",
                width=round(w_mm, 1), height=round(h_mm, 1),
                medium=name, medium_w=round(medium[0], 1), medium_h=round(medium[1], 1)))
        else:
            self._print_label.setStyleSheet("color: #888; font-size: 11px;")
            self._print_label.setText(tr(
                "resize.print_area_ok",
                medium=name, medium_w=round(medium[0], 1), medium_h=round(medium[1], 1)))

    def _mm_pixel_size(self) -> tuple[int, int]:
        return pixel_size_for_size_mm(
            (self._w_mm.value(), self._h_mm.value()),
            (self._dpi.value(), self._dpi.value()),
        )

    def print_area_exceeded(self) -> bool:
        """True, wenn die mm-Zielgröße die gewählte Zielmediumgröße überschreitet."""
        if not self._is_mm_mode():
            return False
        medium = self._medium.currentData()
        if medium is None:
            return False
        return self._w_mm.value() > medium[0] or self._h_mm.value() > medium[1]

    # ── Ergebnis ────────────────────────────────────────────────────────
    def selected_size(self) -> tuple[int, int]:
        """Gewählte Zielgröße als ``(width, height)`` px (im mm-Modus abgeleitet)."""
        if self._is_mm_mode():
            return self._mm_pixel_size()
        return (self._w_spin.value(), self._h_spin.value())

    def selected_resample(self) -> Image.Resampling:
        """Gewähltes Resample-Verfahren als Pillow-Enum."""
        return self._resample.currentData()

    def selected_physical_size_mm(self) -> tuple[float, float] | None:
        """Physische Zielgröße ``(w, h)`` in mm – nur im mm-Modus, sonst ``None``."""
        if self._is_mm_mode():
            return (self._w_mm.value(), self._h_mm.value())
        return None

    def selected_dpi(self) -> tuple[float, float] | None:
        """Zielauflösung ``(x, y)`` in DPI – nur im mm-Modus, sonst ``None``."""
        if self._is_mm_mode():
            value = self._dpi.value()
            return (value, value)
        return None
