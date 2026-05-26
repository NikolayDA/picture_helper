"""Tests fuer ``SettingsDialog._save_and_accept``-Validierung.

Stellt sicher, dass leere Felder weiterhin akzeptiert werden (= "zuletzt
verwendet"), aber dass ein nicht existierendes Verzeichnis eine
QMessageBox-Warnung ausloest und die Settings nicht ueberschreibt.
"""
from __future__ import annotations

import pytest
from PyQt6.QtCore import QSettings

import bgremover.settings_dialog as _sd
from bgremover import SettingsDialog


@pytest.fixture
def isolated_settings(tmp_path):
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat,
                      QSettings.Scope.UserScope, str(tmp_path))
    yield tmp_path


def _settings() -> QSettings:
    return QSettings("BgRemover", "BgRemover")


def test_save_rejects_nonexistent_open_dir(qapp, isolated_settings, monkeypatch, tmp_path):
    warnings: list[tuple[str, str]] = []
    monkeypatch.setattr(
        _sd.QMessageBox, "warning",
        lambda parent, title, text: warnings.append((title, text)) or 0,
    )
    accepted: list[bool] = []
    settings = _settings()
    settings.setValue("open_dir", str(tmp_path))  # bestehender, gueltiger Wert

    dlg = SettingsDialog(settings)
    monkeypatch.setattr(dlg, "accept",
                        lambda: accepted.append(True))

    bogus = str(tmp_path / "does-not-exist-xyz")
    dlg._open_dir_edit.setText(bogus)
    dlg._save_dir_edit.setText("")
    dlg._save_and_accept()

    assert accepted == []
    assert len(warnings) == 1
    assert bogus in warnings[0][1]
    # Der zuvor gueltige Wert bleibt unveraendert.
    assert settings.value("open_dir") == str(tmp_path)


def test_save_rejects_nonexistent_save_dir(qapp, isolated_settings, monkeypatch, tmp_path):
    warnings: list[tuple[str, str]] = []
    monkeypatch.setattr(
        _sd.QMessageBox, "warning",
        lambda parent, title, text: warnings.append((title, text)) or 0,
    )
    settings = _settings()

    dlg = SettingsDialog(settings)
    accepted: list[bool] = []
    monkeypatch.setattr(dlg, "accept",
                        lambda: accepted.append(True))

    dlg._open_dir_edit.setText("")
    bogus = str(tmp_path / "missing-target")
    dlg._save_dir_edit.setText(bogus)
    dlg._save_and_accept()

    assert accepted == []
    assert len(warnings) == 1
    assert bogus in warnings[0][1]
    # Settings wurden nicht beruehrt.
    assert settings.value("save_dir", "<sentinel>") == "<sentinel>"


def test_save_accepts_empty_dirs(qapp, isolated_settings, monkeypatch):
    """Leerer String bleibt erlaubt – heisst "zuletzt verwendet"."""
    warnings: list[tuple[str, str]] = []
    monkeypatch.setattr(
        _sd.QMessageBox, "warning",
        lambda parent, title, text: warnings.append((title, text)) or 0,
    )
    settings = _settings()

    dlg = SettingsDialog(settings)
    accepted: list[bool] = []
    monkeypatch.setattr(dlg, "accept",
                        lambda: accepted.append(True))

    dlg._open_dir_edit.setText("")
    dlg._save_dir_edit.setText("")
    dlg._save_and_accept()

    assert warnings == []
    assert accepted == [True]
    assert settings.value("open_dir") == ""
    assert settings.value("save_dir") == ""


def test_save_accepts_existing_dirs(qapp, isolated_settings, monkeypatch, tmp_path):
    warnings: list[tuple[str, str]] = []
    monkeypatch.setattr(
        _sd.QMessageBox, "warning",
        lambda parent, title, text: warnings.append((title, text)) or 0,
    )
    settings = _settings()

    dlg = SettingsDialog(settings)
    accepted: list[bool] = []
    monkeypatch.setattr(dlg, "accept",
                        lambda: accepted.append(True))

    open_dir = tmp_path / "open"
    save_dir = tmp_path / "save"
    open_dir.mkdir()
    save_dir.mkdir()

    dlg._open_dir_edit.setText(str(open_dir))
    dlg._save_dir_edit.setText(str(save_dir))
    dlg._save_and_accept()

    assert warnings == []
    assert accepted == [True]
    assert settings.value("open_dir") == str(open_dir)
    assert settings.value("save_dir") == str(save_dir)
