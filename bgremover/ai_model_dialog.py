"""Dialog „KI-Modell verwalten…" (#569, Teil von Epic #563).

Zeigt den Cache-Status des rembg-Standardmodells (``ai_model_status.get_model_status``)
und bietet Download-/Retry- sowie Abbrechen-Buttons. Die eigentliche Ausführung
(Anbindung an den bestehenden Warmup-/Inferenzprozess, Anhängen an einen bereits
laufenden Start-Warmup, Race-Vermeidung, prozessseitiger Abbruch) ist bewusst über
die Signale ``download_requested``/``cancel_requested`` sowie die von außen
getriebenen Zustandsmethoden entkoppelt – laut Scope-Klarstellung auf #569 reicht
hier ein testbarer, gemockter Download-/Retry-/Cancel-Pfad; die echte
``WorkerController``/``InferenceProcess``-Anbindung folgt in #570.
"""
from __future__ import annotations

import sys
from collections.abc import Callable

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from bgremover.ai_model_status import ModelStatus, ModelStatusResult, get_model_status
from bgremover.i18n import tr


def _format_size(size_bytes: int) -> str:
    """Menschenlesbare Größe in MB (eine Nachkommastelle) für die Anzeige."""
    return f"{size_bytes / (1024 * 1024):.1f} MB"


class AiModelDialog(QDialog):
    """Zeigt/aktualisiert den Modellstatus; Download/Retry/Cancel laufen über Signale."""

    download_requested = pyqtSignal()
    cancel_requested = pyqtSignal()

    def __init__(
        self,
        *,
        status_provider: Callable[[], ModelStatusResult] = get_model_status,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._status_provider = status_provider
        self._downloading = False
        self.setWindowTitle(tr("ai_model.dialog.title"))
        self.setMinimumWidth(420)
        self._build_ui()
        self.refresh_status()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(20, 20, 20, 20)

        title = QLabel(tr("ai_model.dialog.title"))
        lay.addWidget(title)

        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        lay.addWidget(self._status_label)

        self._error_label = QLabel()
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        lay.addWidget(self._error_label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # unbestimmt – rembg liefert keinen Fortschritt
        self._progress.setVisible(False)
        lay.addWidget(self._progress)

        lay.addStretch()

        btn_row = QHBoxLayout()
        self._cancel_btn = QPushButton(tr("ai_model.dialog.cancel"))
        self._cancel_btn.setVisible(False)
        self._cancel_btn.clicked.connect(self.cancel_requested.emit)
        btn_row.addWidget(self._cancel_btn)
        btn_row.addStretch()
        self._download_btn = QPushButton(tr("ai_model.dialog.download"))
        self._download_btn.clicked.connect(self.download_requested.emit)
        btn_row.addWidget(self._download_btn)
        close_btn = QPushButton(tr("ai_model.dialog.close"))
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        lay.addLayout(btn_row)

    # ── Von außen getriebene Zustände (MainWindow bzw. Tests) ───────────

    def refresh_status(self) -> None:
        """Fragt den aktuellen Modellstatus ab und zeigt ihn an (kein Download)."""
        self._error_label.setVisible(False)
        self._set_downloading(False)
        self._render_status(self._status_provider())

    def start_downloading(self) -> None:
        """Zeigt den Busy-Zustand während eines laufenden Downloads."""
        self._error_label.setVisible(False)
        self._set_downloading(True)

    def download_succeeded(self) -> None:
        """Download abgeschlossen: Status neu abfragen, Busy-Zustand beenden."""
        self.refresh_status()

    def download_failed(self, message: str) -> None:
        """Download fehlgeschlagen (oder abgebrochen): zeigt Fehler + Retry."""
        self._set_downloading(False)
        self._error_label.setText(message)
        self._error_label.setVisible(True)
        self._download_btn.setText(tr("ai_model.dialog.retry"))
        self._download_btn.setEnabled(True)

    @property
    def is_downloading(self) -> bool:
        return self._downloading

    # ── Interna ──────────────────────────────────────────────────────────

    def _render_status(self, result: ModelStatusResult) -> None:
        if result.status is ModelStatus.DOWNLOADED:
            size = _format_size(result.size_bytes) if result.size_bytes else ""
            self._status_label.setText(
                tr("ai_model.status.downloaded", path=str(result.model_path), size=size)
            )
            self._download_btn.setText(tr("ai_model.dialog.download"))
            self._download_btn.setEnabled(False)
        elif result.status is ModelStatus.NOT_DOWNLOADED:
            self._status_label.setText(tr("ai_model.status.not_downloaded"))
            self._download_btn.setText(tr("ai_model.dialog.download"))
            self._download_btn.setEnabled(True)
        else:
            # Die aktive Python-Umgebung mit anzeigen (#575): „rembg nicht
            # installiert" heißt oft nur „falscher Interpreter" (z. B. App per
            # Desktop-Icon mit System-Python gestartet, rembg liegt aber in
            # einer venv). Mit dem Pfad ist der Mismatch sofort erkennbar.
            self._status_label.setText(
                tr("ai_model.status.rembg_unavailable")
                + "\n"
                + tr("ai_model.status.python_hint", path=sys.executable)
            )
            self._download_btn.setText(tr("ai_model.dialog.download"))
            self._download_btn.setEnabled(False)

    def _set_downloading(self, downloading: bool) -> None:
        self._downloading = downloading
        self._progress.setVisible(downloading)
        self._cancel_btn.setVisible(downloading)
        self._download_btn.setEnabled(not downloading)
