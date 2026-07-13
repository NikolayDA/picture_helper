"""UI-Smoke-Tests für den Dialog „KI-Modell verwalten…" (#569).

Deckt die drei Statusanzeigen, den Download-/Retry-/Cancel-Signalpfad und den
Busy-Zustand ab. Headless ohne qtbot – Status-Provider und Signale werden
gezielt gemockt/verbunden statt eines echten Downloads (siehe Scope-
Klarstellung auf #569: die echte ``WorkerController``/``InferenceProcess``-
Anbindung folgt in #570).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from bgremover.ai_model_dialog import AiModelDialog
from bgremover.ai_model_status import ModelStatus, ModelStatusResult


def _status(status: ModelStatus, **kwargs) -> ModelStatusResult:
    return ModelStatusResult(status=status, model_path=Path("/tmp/u2net.onnx"), **kwargs)


@pytest.mark.ui_smoke
def test_shows_downloaded_status_with_path_and_size(qapp) -> None:
    dlg = AiModelDialog(
        status_provider=lambda: _status(ModelStatus.DOWNLOADED, size_bytes=5_242_880))
    assert "u2net.onnx" in dlg._status_label.text()
    assert "5.0 MB" in dlg._status_label.text()
    assert not dlg._download_btn.isEnabled()


@pytest.mark.ui_smoke
def test_shows_not_downloaded_status_with_enabled_download(qapp) -> None:
    dlg = AiModelDialog(status_provider=lambda: _status(ModelStatus.NOT_DOWNLOADED))
    assert dlg._download_btn.isEnabled()
    assert dlg._cancel_btn.isHidden()


@pytest.mark.ui_smoke
def test_shows_rembg_unavailable_status_with_disabled_download(qapp) -> None:
    dlg = AiModelDialog(status_provider=lambda: _status(ModelStatus.REMBG_UNAVAILABLE))
    assert not dlg._download_btn.isEnabled()


@pytest.mark.ui_smoke
def test_rembg_unavailable_status_names_active_python_environment(qapp) -> None:
    """#575: „rembg nicht installiert" heißt oft nur „falscher Interpreter"
    (App per Desktop-Icon mit System-Python gestartet, rembg liegt in einer
    venv). Der Dialog zeigt daher die aktive Python-Umgebung mit an."""
    import sys

    dlg = AiModelDialog(status_provider=lambda: _status(ModelStatus.REMBG_UNAVAILABLE))

    assert sys.executable in dlg._status_label.text()


@pytest.mark.ui_smoke
def test_download_button_emits_signal(qapp) -> None:
    dlg = AiModelDialog(status_provider=lambda: _status(ModelStatus.NOT_DOWNLOADED))
    calls: list[bool] = []
    dlg.download_requested.connect(lambda: calls.append(True))

    dlg._download_btn.click()

    assert calls == [True]


@pytest.mark.ui_smoke
def test_start_downloading_shows_busy_state(qapp) -> None:
    dlg = AiModelDialog(status_provider=lambda: _status(ModelStatus.NOT_DOWNLOADED))

    dlg.start_downloading()

    assert dlg.is_downloading
    assert not dlg._progress.isHidden()
    assert not dlg._cancel_btn.isHidden()
    assert not dlg._download_btn.isEnabled()


@pytest.mark.ui_smoke
def test_cancel_button_emits_signal_while_downloading(qapp) -> None:
    dlg = AiModelDialog(status_provider=lambda: _status(ModelStatus.NOT_DOWNLOADED))
    dlg.start_downloading()
    calls: list[bool] = []
    dlg.cancel_requested.connect(lambda: calls.append(True))

    dlg._cancel_btn.click()

    assert calls == [True]


@pytest.mark.ui_smoke
def test_download_succeeded_refreshes_status_and_clears_busy(qapp) -> None:
    statuses = iter([
        _status(ModelStatus.NOT_DOWNLOADED),
        _status(ModelStatus.DOWNLOADED, size_bytes=1024),
    ])
    dlg = AiModelDialog(status_provider=lambda: next(statuses))
    dlg.start_downloading()

    dlg.download_succeeded()

    assert not dlg.is_downloading
    assert not dlg._download_btn.isEnabled()


@pytest.mark.ui_smoke
def test_download_failed_shows_error_and_retry(qapp) -> None:
    dlg = AiModelDialog(status_provider=lambda: _status(ModelStatus.NOT_DOWNLOADED))
    dlg.start_downloading()

    dlg.download_failed("Netzwerkfehler")

    assert not dlg.is_downloading
    assert not dlg._error_label.isHidden()
    assert dlg._error_label.text() == "Netzwerkfehler"
    assert dlg._download_btn.isEnabled()
    assert dlg._download_btn.text() == "Erneut versuchen"
