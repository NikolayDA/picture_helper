"""UI-Smoke-Tests für den Dialog „KI-Hintergrundentfernung installieren…".

Deckt den plattformabhängigen Befehlstext, den Copy-Button (Zwischenablage),
den bedingten „bereits installiert"-Hinweis und die Python-Versionswarnung
ab (#578-Review). Headless ohne qtbot, analog zu ``test_ai_model_dialog.py``.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QLabel

from bgremover.ai_install_dialog import (
    LINUX_INSTALL_COMMAND,
    MACOS_INSTALL_COMMAND,
    AiInstallDialog,
    install_command_for_platform,
)
from bgremover.ai_model_status import ModelStatus, ModelStatusResult
from bgremover.i18n import tr


def _status(status: ModelStatus, **kwargs) -> ModelStatusResult:
    return ModelStatusResult(status=status, model_path=Path("/tmp/u2net.onnx"), **kwargs)


def _label_texts(dlg: AiInstallDialog) -> list[str]:
    return [label.text() for label in dlg.findChildren(QLabel)]


@pytest.mark.ui_smoke
def test_shows_linux_install_command(qapp) -> None:
    dlg = AiInstallDialog(
        status_provider=lambda: _status(ModelStatus.REMBG_UNAVAILABLE),
        platform="linux",
        python_version=(3, 12),
    )
    assert dlg._command_view.toPlainText() == LINUX_INSTALL_COMMAND
    assert 'pip install "rembg[cpu]"' in LINUX_INSTALL_COMMAND


@pytest.mark.ui_smoke
def test_shows_macos_install_command(qapp) -> None:
    """#578-Review: macOS hat eine eigene, App-Bundle-verwaltete venv – das
    Linux-Rezept mit einer eigenen Projekt-.venv wuerde den Interpreter der
    gepackten App gar nicht erreichen."""
    dlg = AiInstallDialog(
        status_provider=lambda: _status(ModelStatus.REMBG_UNAVAILABLE),
        platform="darwin",
        python_version=(3, 12),
    )
    assert dlg._command_view.toPlainText() == MACOS_INSTALL_COMMAND
    assert install_command_for_platform("darwin") == MACOS_INSTALL_COMMAND
    assert install_command_for_platform("linux") == LINUX_INSTALL_COMMAND


@pytest.mark.ui_smoke
def test_no_already_installed_hint_when_rembg_unavailable(qapp) -> None:
    dlg = AiInstallDialog(
        status_provider=lambda: _status(ModelStatus.REMBG_UNAVAILABLE),
        python_version=(3, 12),
    )
    assert tr("ai_install.dialog.already_installed") not in _label_texts(dlg)


@pytest.mark.ui_smoke
def test_shows_already_installed_hint_when_rembg_present(qapp) -> None:
    dlg = AiInstallDialog(
        status_provider=lambda: _status(ModelStatus.NOT_DOWNLOADED),
        python_version=(3, 12),
    )
    assert tr("ai_install.dialog.already_installed") in _label_texts(dlg)


@pytest.mark.ui_smoke
def test_no_python_too_old_warning_on_supported_version(qapp) -> None:
    dlg = AiInstallDialog(
        status_provider=lambda: _status(ModelStatus.REMBG_UNAVAILABLE),
        python_version=(3, 11),
    )
    assert tr("ai_install.dialog.python_too_old", version="3.10") not in _label_texts(dlg)


@pytest.mark.ui_smoke
def test_python_too_old_warning_shown_below_min_version(qapp) -> None:
    """#578-Review: rembg/onnxruntime brauchen Python 3.11+; ein kopierter
    Befehl auf Python 3.10 wuerde sonst stillschweigend fehlschlagen."""
    dlg = AiInstallDialog(
        status_provider=lambda: _status(ModelStatus.REMBG_UNAVAILABLE),
        python_version=(3, 10),
    )
    assert tr("ai_install.dialog.python_too_old", version="3.10") in _label_texts(dlg)


@pytest.mark.ui_smoke
def test_copy_button_puts_command_on_clipboard(qapp) -> None:
    dlg = AiInstallDialog(
        status_provider=lambda: _status(ModelStatus.REMBG_UNAVAILABLE),
        platform="linux",
        python_version=(3, 12),
    )

    dlg._copy_btn.click()

    assert QGuiApplication.clipboard().text() == LINUX_INSTALL_COMMAND
    assert not dlg._copied_label.isHidden()
