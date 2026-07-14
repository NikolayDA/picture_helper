"""UI-Smoke-Tests für den Dialog „KI-Hintergrundentfernung installieren…".

Deckt den Befehlstext, den Copy-Button (Zwischenablage) und den bedingten
„bereits installiert"-Hinweis ab. Headless ohne qtbot, analog zu
``test_ai_model_dialog.py``.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QLabel

from bgremover.ai_install_dialog import INSTALL_COMMAND, AiInstallDialog
from bgremover.ai_model_status import ModelStatus, ModelStatusResult
from bgremover.i18n import tr


def _status(status: ModelStatus, **kwargs) -> ModelStatusResult:
    return ModelStatusResult(status=status, model_path=Path("/tmp/u2net.onnx"), **kwargs)


def _label_texts(dlg: AiInstallDialog) -> list[str]:
    return [label.text() for label in dlg.findChildren(QLabel)]


@pytest.mark.ui_smoke
def test_shows_install_command(qapp) -> None:
    dlg = AiInstallDialog(status_provider=lambda: _status(ModelStatus.REMBG_UNAVAILABLE))
    assert dlg._command_view.toPlainText() == INSTALL_COMMAND
    assert 'pip install "rembg[cpu]"' in INSTALL_COMMAND


@pytest.mark.ui_smoke
def test_no_already_installed_hint_when_rembg_unavailable(qapp) -> None:
    dlg = AiInstallDialog(status_provider=lambda: _status(ModelStatus.REMBG_UNAVAILABLE))
    assert tr("ai_install.dialog.already_installed") not in _label_texts(dlg)


@pytest.mark.ui_smoke
def test_shows_already_installed_hint_when_rembg_present(qapp) -> None:
    dlg = AiInstallDialog(status_provider=lambda: _status(ModelStatus.NOT_DOWNLOADED))
    assert tr("ai_install.dialog.already_installed") in _label_texts(dlg)


@pytest.mark.ui_smoke
def test_copy_button_puts_command_on_clipboard(qapp) -> None:
    dlg = AiInstallDialog(status_provider=lambda: _status(ModelStatus.REMBG_UNAVAILABLE))

    dlg._copy_btn.click()

    assert QGuiApplication.clipboard().text() == INSTALL_COMMAND
    assert not dlg._copied_label.isHidden()
