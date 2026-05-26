"""Einstellungen-Dialog (persistente Nutzereinstellungen).

Liest den aktiven Log-Pfad ueber ``current_log_file()`` aus
``logging_config`` – nie ueber den Modul-Globalwert ``_log_file_path``
direkt.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSettings, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from bgremover.logging_config import current_log_file
from bgremover.theme import SETTINGS_TITLE_STYLE


class SettingsDialog(QDialog):
    """Dialog zum Bearbeiten persistenter Nutzereinstellungen."""

    FORMATS = ["PNG", "JPEG", "WebP", "TIFF"]
    FORMAT_FILTERS = {
        "PNG":  "PNG (*.png)",
        "JPEG": "JPEG (*.jpg)",
        "WebP": "WebP (*.webp)",
        "TIFF": "TIFF (*.tif)",
    }

    def __init__(self, settings: QSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Einstellungen")
        self.setMinimumWidth(520)
        self._settings = settings
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Einstellungen")
        title.setStyleSheet(SETTINGS_TITLE_STYLE)
        lay.addWidget(title)

        # Verzeichnis zum Öffnen
        open_grp = QGroupBox("Standard-Verzeichnis zum Öffnen")
        open_lay = QHBoxLayout(open_grp)
        self._open_dir_edit = QLineEdit()
        self._open_dir_edit.setPlaceholderText("Leer = zuletzt verwendetes Verzeichnis")
        open_lay.addWidget(self._open_dir_edit)
        btn_open = QPushButton("…")
        btn_open.setFixedWidth(32)
        btn_open.clicked.connect(self._pick_open_dir)
        open_lay.addWidget(btn_open)
        lay.addWidget(open_grp)

        # Verzeichnis zum Speichern/Export
        save_grp = QGroupBox("Standard-Verzeichnis für Export / Speichern")
        save_lay = QHBoxLayout(save_grp)
        self._save_dir_edit = QLineEdit()
        self._save_dir_edit.setPlaceholderText("Leer = zuletzt verwendetes Verzeichnis")
        save_lay.addWidget(self._save_dir_edit)
        btn_save = QPushButton("…")
        btn_save.setFixedWidth(32)
        btn_save.clicked.connect(self._pick_save_dir)
        save_lay.addWidget(btn_save)
        lay.addWidget(save_grp)

        # Bevorzugtes Dateiformat
        fmt_grp = QGroupBox("Bevorzugtes Bilddateiformat")
        fmt_lay = QHBoxLayout(fmt_grp)
        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(self.FORMATS)
        self._fmt_combo.setFixedWidth(140)
        fmt_lay.addWidget(self._fmt_combo)
        fmt_lay.addStretch()
        lay.addWidget(fmt_grp)

        # Protokolldatei
        log_grp = QGroupBox("Protokolldatei")
        log_lay = QHBoxLayout(log_grp)
        self._log_path_edit = QLineEdit()
        self._log_path_edit.setReadOnly(True)
        self._log_path_edit.setToolTip(
            "Pfad der Log-Datei (markieren zum Kopieren)")
        log_lay.addWidget(self._log_path_edit)
        btn_log = QPushButton("Ordner öffnen")
        btn_log.clicked.connect(self._open_log_dir)
        log_lay.addWidget(btn_log)
        lay.addWidget(log_grp)

        lay.addStretch()

        # OK / Abbrechen
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("OK")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self._save_and_accept)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

    def _pick_open_dir(self) -> None:
        start = self._open_dir_edit.text().strip() or str(Path.home())
        d = QFileDialog.getExistingDirectory(
            self, "Verzeichnis zum Öffnen wählen", start)
        if d:
            self._open_dir_edit.setText(d)

    def _pick_save_dir(self) -> None:
        start = self._save_dir_edit.text().strip() or str(Path.home())
        d = QFileDialog.getExistingDirectory(
            self, "Verzeichnis für Export/Speichern wählen", start)
        if d:
            self._save_dir_edit.setText(d)

    def _open_log_dir(self) -> None:
        log_file = current_log_file()
        target = log_file.parent if log_file.parent.exists() else Path.home()
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(target))):
            QMessageBox.warning(
                self, "Protokolldatei",
                f"Ordner konnte nicht geöffnet werden:\n{target}")

    def _load(self) -> None:
        self._open_dir_edit.setText(self._settings.value("open_dir", ""))
        self._save_dir_edit.setText(self._settings.value("save_dir", ""))
        fmt = self._settings.value("preferred_format", "PNG")
        idx = self._fmt_combo.findText(fmt)
        if idx >= 0:
            self._fmt_combo.setCurrentIndex(idx)
        self._log_path_edit.setText(str(current_log_file()))

    def _save_and_accept(self) -> None:
        open_dir = self._open_dir_edit.text().strip()
        save_dir = self._save_dir_edit.text().strip()
        # Leerer String bleibt erlaubt und bedeutet "zuletzt verwendetes
        # Verzeichnis"; jeder andere Wert muss ein existierendes Verzeichnis
        # sein, sonst landet beim naechsten Datei-Dialog ein toter Pfad.
        for label, value in (
            ("Standard-Verzeichnis zum Öffnen", open_dir),
            ("Standard-Verzeichnis für Export / Speichern", save_dir),
        ):
            if value and not Path(value).is_dir():
                QMessageBox.warning(
                    self, "Ungültiges Verzeichnis",
                    f"{label} ist kein existierendes Verzeichnis:\n{value}",
                )
                return
        self._settings.setValue("open_dir", open_dir)
        self._settings.setValue("save_dir", save_dir)
        self._settings.setValue("preferred_format", self._fmt_combo.currentText())
        self.accept()
