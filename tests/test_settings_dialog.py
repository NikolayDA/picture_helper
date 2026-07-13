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
    # QSettings cached Werte im Prozess; ohne explizites clear() leckt der
    # vorige Test seine open_dir/save_dir-Eintraege herueber.
    QSettings("BgRemover", "BgRemover").clear()
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


# ── Verzeichnis-Auswahl (QFileDialog gepatcht) ─────────────────────────

def test_pick_open_dir_sets_text_on_selection(qapp, isolated_settings, monkeypatch, tmp_path):
    dlg = SettingsDialog(_settings())
    monkeypatch.setattr(
        _sd.QFileDialog, "getExistingDirectory",
        lambda *a, **k: str(tmp_path),
    )
    dlg._pick_open_dir()
    assert dlg._open_dir_edit.text() == str(tmp_path)


def test_pick_open_dir_cancel_keeps_previous_text(qapp, isolated_settings, monkeypatch):
    dlg = SettingsDialog(_settings())
    dlg._open_dir_edit.setText("/zuvor")
    # Abbruch des Dialogs liefert leeren String → Text bleibt unverändert.
    monkeypatch.setattr(
        _sd.QFileDialog, "getExistingDirectory", lambda *a, **k: "",
    )
    dlg._pick_open_dir()
    assert dlg._open_dir_edit.text() == "/zuvor"


def test_pick_save_dir_sets_text_on_selection(qapp, isolated_settings, monkeypatch, tmp_path):
    dlg = SettingsDialog(_settings())
    monkeypatch.setattr(
        _sd.QFileDialog, "getExistingDirectory",
        lambda *a, **k: str(tmp_path),
    )
    dlg._pick_save_dir()
    assert dlg._save_dir_edit.text() == str(tmp_path)


def test_pick_save_dir_cancel_keeps_previous_text(qapp, isolated_settings, monkeypatch):
    dlg = SettingsDialog(_settings())
    dlg._save_dir_edit.setText("/zuvor")
    monkeypatch.setattr(
        _sd.QFileDialog, "getExistingDirectory", lambda *a, **k: "",
    )
    dlg._pick_save_dir()
    assert dlg._save_dir_edit.text() == "/zuvor"


def test_load_ignores_unknown_preferred_format(qapp, isolated_settings):
    """Ein nicht in ``FORMATS`` enthaltenes gespeichertes Format darf den
    Combo-Index nicht verstellen – ``findText`` liefert -1, der Default
    bleibt erhalten."""
    settings = _settings()
    settings.setValue("preferred_format", "EXR")  # unbekannt
    dlg = SettingsDialog(settings)
    # Index bleibt beim ersten Eintrag (PNG), nicht negativ.
    assert dlg._fmt_combo.currentIndex() == 0


# ── Log-Ordner öffnen (QDesktopServices gepatcht) ──────────────────────

def test_open_log_dir_opens_folder(qapp, isolated_settings, monkeypatch):
    dlg = SettingsDialog(_settings())
    opened: list[object] = []
    monkeypatch.setattr(
        _sd.QDesktopServices, "openUrl",
        lambda url: opened.append(url) or True,
    )
    dlg._open_log_dir()
    assert len(opened) == 1


def test_open_log_dir_warns_when_open_fails(qapp, isolated_settings, monkeypatch):
    dlg = SettingsDialog(_settings())
    monkeypatch.setattr(_sd.QDesktopServices, "openUrl", lambda url: False)
    warnings: list[tuple] = []
    monkeypatch.setattr(
        _sd.QMessageBox, "warning",
        lambda *a, **k: warnings.append(a) or 0,
    )
    dlg._open_log_dir()
    assert len(warnings) == 1


# ── Automatischer Update-Check beim Start (#566) ───────────────────────

def test_auto_update_check_defaults_to_disabled(qapp, isolated_settings):
    """Explizites Opt-in: ohne gespeicherten Wert bleibt die Checkbox aus."""
    dlg = SettingsDialog(_settings())
    assert dlg._auto_update_check.isChecked() is False


def test_auto_update_check_persists_when_enabled(qapp, isolated_settings):
    from bgremover.settings_schema import AUTO_UPDATE_CHECK_KEY

    settings = _settings()
    dlg = SettingsDialog(settings)
    dlg._auto_update_check.setChecked(True)
    dlg._save_and_accept()

    assert settings.value(AUTO_UPDATE_CHECK_KEY, False, type=bool) is True

    # Ueberlebt einen "Neustart" (frischer Dialog liest denselben Settings-Wert).
    reloaded = SettingsDialog(settings)
    assert reloaded._auto_update_check.isChecked() is True


def test_auto_update_check_persists_when_disabled_again(qapp, isolated_settings):
    from bgremover.settings_schema import AUTO_UPDATE_CHECK_KEY

    settings = _settings()
    settings.setValue(AUTO_UPDATE_CHECK_KEY, True)

    dlg = SettingsDialog(settings)
    assert dlg._auto_update_check.isChecked() is True
    dlg._auto_update_check.setChecked(False)
    dlg._save_and_accept()

    assert settings.value(AUTO_UPDATE_CHECK_KEY, True, type=bool) is False
