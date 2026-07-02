"""Öffnen von Bildern über Startargumente und macOS-FileOpen (#249).

Prüft die schmale Fassade ``MainWindow.open_paths`` und den ``_FileOpenFilter``
in-process mit echten temporären Bildern: der Pfad läuft über denselben
validierten, asynchronen Ladepfad wie Datei-Dialog, Recent Files und
Drag & Drop. Die Subprozess-Variante (echter App-Start mit Pfad) liegt in
``test_app_smoke.py``.
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest
from PIL import Image
from PyQt6.QtCore import QEvent, QSettings

from bgremover import MainWindow
from bgremover.app import _FileOpenFilter
from bgremover.i18n import tr
from bgremover.status_messages import StatusMessages as SM


@pytest.fixture
def isolated_settings(tmp_path):
    """QSettings in ein temporäres Verzeichnis umleiten (kein realer Cache)."""
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat,
                      QSettings.Scope.UserScope, str(tmp_path))
    yield tmp_path


@pytest.fixture
def win(qapp, isolated_settings):
    w = MainWindow()
    yield w
    w.close()


def _drain(qapp, predicate, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qapp.processEvents()
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("Bedingung nicht innerhalb des Timeouts erfüllt")


def _png(path: Path) -> str:
    Image.new("RGB", (8, 8), (10, 20, 30)).save(path)
    return str(path)


class _FakeFileOpenEvent:
    """Dupliziert die für den Filter relevante ``QFileOpenEvent``-Schnittstelle.

    ``QFileOpenEvent`` lässt sich aus Python nicht konstruieren; der Filter
    nutzt nur ``type()`` und ``file()`` – beides hier nachgebildet.
    """

    def __init__(self, file_path: str = "") -> None:
        self._file = file_path

    def type(self) -> QEvent.Type:
        return QEvent.Type.FileOpen

    def file(self) -> str:
        return self._file


# ── open_paths-Fassade ───────────────────────────────────────────────────

def test_open_paths_loads_single_image(qapp, win, tmp_path) -> None:
    win.open_paths([_png(tmp_path / "a.png")])
    _drain(qapp, lambda: win._canvas.has_image)
    assert win._canvas.has_image


def test_open_paths_opens_first_and_ignores_extras(qapp, win, tmp_path) -> None:
    a = _png(tmp_path / "a.png")
    b = _png(tmp_path / "b.png")
    win.open_paths([a, b])
    # Die Statusmeldung über ignorierte Extras wird synchron gesetzt – also
    # bevor das asynchrone Laden zurückkehrt und die Statuszeile mit der
    # Schritt-Meldung des geführten Workflows (#420) weiterzieht.
    assert win._sb.currentMessage() == tr(
        "canvas.opened_extra", name=Path(a).name, extra=1)
    _drain(qapp, lambda: win._canvas.has_image)
    assert win._canvas.has_image


def test_open_paths_empty_inputs_are_noop(qapp, win) -> None:
    win.open_paths([])
    win.open_paths([""])
    qapp.processEvents()
    assert not win._canvas.has_image


def test_open_paths_missing_file_reports_error_without_crash(qapp, win, tmp_path) -> None:
    win.open_paths([str(tmp_path / "does_not_exist.png")])
    _drain(qapp, lambda: not win._worker_controller.is_loading)
    assert not win._canvas.has_image
    assert win._sb.currentMessage()   # kontrollierte Meldung statt Absturz


def test_open_paths_respects_unsaved_changes_prompt(
    qapp, win, tmp_path, monkeypatch,
) -> None:
    """Lehnt der Nutzer das Verwerfen ab, wird NICHT geladen (#249, AC #8)."""
    monkeypatch.setattr(win, "_confirm_discard_changes", lambda: False)
    win.open_paths([_png(tmp_path / "a.png")])
    qapp.processEvents()
    assert not win._worker_controller.is_loading
    assert not win._canvas.has_image


# ── macOS-FileOpen-Event-Filter ──────────────────────────────────────────

def test_file_open_filter_opens_local_file(qapp, win, tmp_path) -> None:
    filt = _FileOpenFilter(win)
    handled = filt.eventFilter(win, _FakeFileOpenEvent(_png(tmp_path / "a.png")))
    assert handled is True
    _drain(qapp, lambda: win._canvas.has_image)
    assert win._canvas.has_image


def test_file_open_filter_remote_url_reports_message(qapp, win) -> None:
    filt = _FileOpenFilter(win)
    handled = filt.eventFilter(win, _FakeFileOpenEvent(""))
    assert handled is True
    assert win._sb.currentMessage() == SM.OEFFNEN_NICHT_LOKAL
    assert not win._canvas.has_image


def test_shutdown_workers_joins_running_load(qapp, win, tmp_path) -> None:
    """``shutdown_workers`` (App-Quit-Haken) beendet einen laufenden Ladethread,
    damit ein App-Quit direkt nach einem Start-Open keinen mitlaufenden Worker
    beim Teardown abräumt (#249)."""
    win.open_paths([_png(tmp_path / "a.png")])
    win.shutdown_workers()
    assert not win._worker_controller.is_loading


def test_file_open_filter_ignores_other_events(qapp, win) -> None:
    filt = _FileOpenFilter(win)

    class _Other:
        def type(self) -> QEvent.Type:
            return QEvent.Type.None_

    assert filt.eventFilter(win, _Other()) is False
