"""Dialog „KI-Hintergrundentfernung installieren…".

Zeigt Nutzer:innen ohne installiertes rembg-Backend (z. B. nach der
Minimal-Installation auf dem Raspberry Pi, siehe INSTALL_LINUX.md) den
passenden Terminal-Befehl zum Nachrüsten. Installiert bewusst **nicht**
selbst per Subprocess: Auf Systemen ohne venv blockiert PEP 668
(„externally-managed-environment") ein `pip install` ins System-Python
ohnehin, und ein frisch installiertes Paket wäre im laufenden Prozess erst
nach einem Neustart sichtbar – ein automatischer Install-Versuch aus der
App heraus würde also entweder scheitern oder nur Verwirrung stiften.
"""
from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from bgremover.ai_model_status import ModelStatus, ModelStatusResult, get_model_status
from bgremover.i18n import tr

INSTALL_COMMAND = (
    'python3 -m venv --system-site-packages .venv\n'
    'source .venv/bin/activate\n'
    'pip install "rembg[cpu]"\n'
    'python3 -m bgremover'
)


class AiInstallDialog(QDialog):
    """Zeigt den Nachrüst-Befehl fürs rembg-Backend; kein Auto-Install (Modul-Docstring)."""

    def __init__(
        self,
        *,
        status_provider: Callable[[], ModelStatusResult] = get_model_status,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._status_provider = status_provider
        self.setWindowTitle(tr("ai_install.dialog.title"))
        self.setMinimumWidth(480)
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(20, 20, 20, 20)

        title = QLabel(tr("ai_install.dialog.title"))
        lay.addWidget(title)

        intro = QLabel(tr("ai_install.dialog.intro"))
        intro.setWordWrap(True)
        lay.addWidget(intro)

        if self._status_provider().status is not ModelStatus.REMBG_UNAVAILABLE:
            already = QLabel(tr("ai_install.dialog.already_installed"))
            already.setWordWrap(True)
            lay.addWidget(already)

        self._command_view = QPlainTextEdit(INSTALL_COMMAND)
        self._command_view.setReadOnly(True)
        self._command_view.setFixedHeight(96)
        lay.addWidget(self._command_view)

        venv_note = QLabel(tr("ai_install.dialog.venv_note"))
        venv_note.setWordWrap(True)
        lay.addWidget(venv_note)

        self._copied_label = QLabel(tr("ai_install.dialog.copied"))
        self._copied_label.setVisible(False)
        lay.addWidget(self._copied_label)

        lay.addStretch()

        btn_row = QHBoxLayout()
        self._copy_btn = QPushButton(tr("ai_install.dialog.copy"))
        self._copy_btn.clicked.connect(self._copy_command)
        btn_row.addWidget(self._copy_btn)
        btn_row.addStretch()
        close_btn = QPushButton(tr("ai_model.dialog.close"))
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        lay.addLayout(btn_row)

    def _copy_command(self) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(INSTALL_COMMAND)
        self._copied_label.setVisible(True)
