"""Tests für den Schutz vor Datenverlust bei ungespeicherten Änderungen.

``MainWindow`` verfolgt über ``content_revision`` einen „sauber"-Punkt und
fragt vor dem Verwerfen bearbeiteter Bilder (Schließen, Bildwechsel) nach.
Die modale Nachfrage selbst ist in ``conftest._auto_confirm_discard`` global
auf „fortfahren" gepatcht; hier wird die Logik direkt bzw. über
instanzweise Overrides geprüft.
"""
from __future__ import annotations

from PIL import Image
from PyQt6.QtGui import QCloseEvent

from bgremover import MainWindow


def _load(win: MainWindow, color=(10, 20, 30, 255)) -> None:
    win._canvas.apply_loaded_image(Image.new("RGBA", (8, 8), color), "seed.png")


def _edit(win: MainWindow) -> None:
    win._canvas.apply_edit(Image.new("RGBA", (8, 8), (1, 2, 3, 255)), desc="edit")


def test_no_image_is_not_dirty(qapp) -> None:
    win = MainWindow()
    try:
        assert win._has_unsaved_changes() is False
    finally:
        win.close()


def test_fresh_load_is_clean(qapp) -> None:
    win = MainWindow()
    try:
        _load(win)
        assert win._has_unsaved_changes() is False
    finally:
        win.close()


def test_edit_marks_dirty_and_save_clears_it(qapp, tmp_path) -> None:
    win = MainWindow()
    try:
        _load(win)
        _edit(win)
        assert win._has_unsaved_changes() is True
        win._save_path = str(tmp_path / "out.png")
        win._save()  # Quick-Save ohne Dialog
        assert (tmp_path / "out.png").exists()
        assert win._has_unsaved_changes() is False
    finally:
        win.close()


def test_close_event_aborts_when_discard_declined(qapp, monkeypatch) -> None:
    win = MainWindow()
    try:
        _load(win)
        _edit(win)
        # Nutzer wählt „Abbrechen" in der Speichern-Nachfrage.
        monkeypatch.setattr(win, "_confirm_discard_changes", lambda: False)
        shutdown: list[bool] = []
        monkeypatch.setattr(
            win._worker_controller, "shutdown_all",
            lambda: shutdown.append(True))
        evt = QCloseEvent()
        win.closeEvent(evt)
        assert evt.isAccepted() is False  # Fenster bleibt offen
        assert shutdown == []             # Threads NICHT heruntergefahren
    finally:
        monkeypatch.setattr(win, "_confirm_discard_changes", lambda: True)
        win.close()


def test_close_event_proceeds_when_allowed(qapp, monkeypatch) -> None:
    win = MainWindow()
    try:
        _load(win)
        _edit(win)
        monkeypatch.setattr(win, "_confirm_discard_changes", lambda: True)
        shutdown: list[bool] = []
        monkeypatch.setattr(
            win._worker_controller, "shutdown_all",
            lambda: shutdown.append(True))
        evt = QCloseEvent()
        win.closeEvent(evt)
        assert evt.isAccepted() is True
        assert shutdown == [True]
    finally:
        win.close()


def test_load_image_async_aborts_when_discard_declined(qapp, monkeypatch) -> None:
    win = MainWindow()
    try:
        _load(win)
        _edit(win)
        monkeypatch.setattr(win, "_confirm_discard_changes", lambda: False)
        started: list = []

        def _fake_start(*a, **k):
            started.append(a)
            return True

        monkeypatch.setattr(
            win._worker_controller, "start_image_load", _fake_start)
        win._load_image_async("/beliebiger/pfad.png")
        assert started == []  # Laden abgebrochen, kein Worker gestartet
    finally:
        win.close()
