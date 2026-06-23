"""UI-Smoke-Tests für den EufyMake-Export-Flow im MainWindow (#355).

Deckt Menüverdrahtung, „kein Projekt", Abbruch, Erfolg (atomar geschrieben +
nächste Schritte), Validierungsfehler, Schreibfehler, Überschreib-Nachfrage und
die Settings-Persistenz ab. Die modalen Dialoge werden gezielt gepatcht.
"""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMessageBox

from bgremover import MainWindow
from bgremover import main_window as mw
from bgremover.eufymake_writer import MANIFEST_FILENAME
from bgremover.project_model import LayerKind, LayerRole
from bgremover.settings_schema import (
    EXPORT_BIT_DEPTH_KEY,
    EXPORT_DIR_KEY,
    EXPORT_INCLUDE_GLOSS_KEY,
    EXPORT_INCLUDE_HEIGHT_KEY,
)


@pytest.fixture(autouse=True)
def _safe_message_boxes(monkeypatch):
    """Macht alle modalen QMessageBox-Aufrufe nicht-blockierend (Test-Sicherheitsnetz).

    Tests, die einen konkreten Aufruf prüfen, überschreiben die jeweilige Methode
    danach mit einem eigenen Recorder.
    """
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: QMessageBox.StandardButton.Ok)
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: QMessageBox.StandardButton.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.No)


@pytest.fixture
def export_win(qapp, tmp_path):
    """MainWindow mit isolierten QSettings und einem Farb-Projekt im Canvas."""
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path / "qs"))
    QSettings("BgRemover", "BgRemover").clear()
    w = MainWindow()
    w._canvas.apply_loaded_image(
        Image.new("RGBA", (4, 4), (10, 20, 30, 255)), str(tmp_path / "src.png"))
    try:
        yield w
    finally:
        w.close()


def _fake_dialog_cls(*, accept=True, roles=(), bits=8, dest="", confirm=False):
    """Baut eine Dialog-Attrappe mit der Schnittstelle von ``EufyMakeExportDialog``."""

    class _Fake:
        def __init__(self, project, **kwargs):
            self.project = project
            self.kwargs = kwargs

        def exec(self):
            return 1 if accept else 0

        def selected_optional_roles(self):
            return list(roles)

        def selected_bit_depth(self):
            return bits

        def selected_destination(self):
            return dest

        def warnings_confirmed(self):
            return confirm

    return _Fake


def test_export_action_is_wired(export_win):
    """Die Menüaktion „Assets für EufyMake Studio exportieren…" existiert."""
    actions = export_win.findChildren(QAction)
    assert any("EufyMake Studio" in (a.text() or "") for a in actions)


def test_export_without_project_reports_status(export_win, monkeypatch):
    monkeypatch.setattr(export_win._canvas.__class__, "project", property(lambda self: None))
    shown: list[str] = []
    monkeypatch.setattr(export_win._sb, "showMessage", lambda m, *a: shown.append(m))
    export_win._export_eufymake()
    assert shown and "Projekt" in shown[-1]


def test_export_cancel_is_side_effect_free(export_win, monkeypatch, tmp_path):
    monkeypatch.setattr(mw, "EufyMakeExportDialog", _fake_dialog_cls(accept=False))
    called: list[str] = []
    monkeypatch.setattr(mw, "write_export", lambda *a, **k: called.append("write"))
    export_win._export_eufymake()
    assert called == []
    # Kein Exportziel in den Settings gemerkt.
    assert export_win._settings.value(EXPORT_DIR_KEY, "") == ""


def test_export_success_writes_and_persists(export_win, monkeypatch, tmp_path):
    dest = tmp_path / "eufymake"
    monkeypatch.setattr(
        mw, "EufyMakeExportDialog",
        _fake_dialog_cls(accept=True, roles=(), bits=8, dest=str(dest)))
    infos: list[tuple[str, str]] = []
    monkeypatch.setattr(
        QMessageBox, "information",
        lambda parent, title, text, *a, **k: infos.append((title, text)))

    export_win._export_eufymake()

    # Atomar geschriebenes Ergebnis.
    assert (dest / "color_motif.png").is_file()
    assert (dest / MANIFEST_FILENAME).is_file()
    # Erfolgsdialog nennt Pfad und nächste Studio-Schritte.
    assert infos and str(dest) in infos[-1][1]
    assert ".empf" in infos[-1][1]
    # Optionen persistiert.
    assert export_win._settings.value(EXPORT_DIR_KEY, "") == str(dest)
    assert export_win._settings.value(EXPORT_BIT_DEPTH_KEY, 0, type=int) == 8
    assert export_win._settings.value(EXPORT_INCLUDE_HEIGHT_KEY, True, type=bool) is False
    assert export_win._settings.value(EXPORT_INCLUDE_GLOSS_KEY, True, type=bool) is False


def test_export_with_height_persists_flag(export_win, monkeypatch, tmp_path):
    # Projekt um eine (nicht-konstante) Höhenebene erweitern und Höhe einbeziehen.
    project = export_win._canvas.project
    arr = np.zeros((4, 4, 4), dtype=np.uint8)
    arr[:, :, 0] = arr[:, :, 1] = arr[:, :, 2] = np.tile(
        np.linspace(0, 255, 4, dtype=np.uint8), (4, 1))
    arr[:, :, 3] = 255
    layer = project.create_layer(
        Image.fromarray(arr, "RGBA"), name="h", kind=LayerKind.HEIGHT)
    project.assign_role(layer.id, LayerRole.HEIGHT_MAP)
    dest = tmp_path / "out2"
    monkeypatch.setattr(
        mw, "EufyMakeExportDialog",
        _fake_dialog_cls(accept=True, roles=(LayerRole.HEIGHT_MAP,), dest=str(dest)))
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    export_win._export_eufymake()
    assert (dest / "height_map.png").is_file()
    assert export_win._settings.value(EXPORT_INCLUDE_HEIGHT_KEY, False, type=bool) is True


def test_export_overwrite_prompt_yes_replaces(export_win, monkeypatch, tmp_path):
    dest = tmp_path / "out"
    monkeypatch.setattr(
        mw, "EufyMakeExportDialog",
        _fake_dialog_cls(accept=True, dest=str(dest)))
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    export_win._export_eufymake()  # erstes Mal
    assert (dest / "color_motif.png").is_file()
    # Zweites Mal: Ziel existiert → Überschreib-Nachfrage „Ja".
    monkeypatch.setattr(
        QMessageBox, "question",
        lambda *a, **k: QMessageBox.StandardButton.Yes)
    export_win._export_eufymake()
    assert (dest / "color_motif.png").is_file()


def test_export_overwrite_prompt_no_aborts(export_win, monkeypatch, tmp_path):
    dest = tmp_path / "out"
    monkeypatch.setattr(
        mw, "EufyMakeExportDialog", _fake_dialog_cls(accept=True, dest=str(dest)))
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    export_win._export_eufymake()
    before = (dest / "color_motif.png").read_bytes()
    monkeypatch.setattr(
        QMessageBox, "question",
        lambda *a, **k: QMessageBox.StandardButton.No)
    shown: list[str] = []
    monkeypatch.setattr(export_win._sb, "showMessage", lambda m, *a: shown.append(m))
    export_win._export_eufymake()
    # Vorhandenes Ziel unberührt.
    assert (dest / "color_motif.png").read_bytes() == before


def test_write_eufymake_blocked_shows_error(export_win, monkeypatch, tmp_path):
    # Projekt ohne ableitbares Farbmotiv → ExportValidationError im Writer.
    from bgremover.project_model import Project

    project = Project(4, 2)
    project.create_layer(
        Image.new("RGBA", (4, 2), (50, 50, 50, 255)), name="h", kind=LayerKind.HEIGHT)
    crit: list[tuple[str, str]] = []
    monkeypatch.setattr(
        QMessageBox, "critical",
        lambda parent, title, text, *a, **k: crit.append((title, text)))
    export_win._write_eufymake(project, str(tmp_path / "out"), [], 8, False)
    assert crit and not (tmp_path / "out").exists()


def test_write_eufymake_io_error_is_reported(export_win, monkeypatch, tmp_path):
    project = export_win._canvas.project
    monkeypatch.setattr(
        mw, "write_export",
        lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    crit: list[tuple[str, str]] = []
    monkeypatch.setattr(
        QMessageBox, "critical",
        lambda parent, title, text, *a, **k: crit.append((title, text)))
    export_win._write_eufymake(project, str(tmp_path / "out"), [], 8, False)
    assert crit and "disk full" in crit[-1][1]
