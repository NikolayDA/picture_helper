"""Tests fuer die QSettings-Schema-Versionierung.

Die Migration ist heute nur ein Grundstein – sie hebt die Version, fuehrt
aber noch keine echten Datenumbauten durch. Die Tests sichern die drei
relevanten Pfade fuer kuenftige Migrationen ab:

- Frische QSettings bekommen ``SCHEMA_VERSION``.
- Pre-Schema-Stand (Settings ohne ``schema_version``) wird geupgradet,
  ohne dass vorhandene Schluessel verloren gehen.
- Ein in der Zukunft liegender Wert wird nicht heruntergeschrieben und
  loest stattdessen nur eine Warnung aus.
"""
from __future__ import annotations

import logging

import pytest
from PyQt6.QtCore import QSettings

from bgremover.settings_schema import (
    SCHEMA_VERSION,
    SCHEMA_VERSION_KEY,
    migrate,
)


@pytest.fixture
def isolated_settings(tmp_path):
    """Isoliert QSettings im tmp_path und leert prozess-internen Cache."""
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat,
                      QSettings.Scope.UserScope, str(tmp_path))
    QSettings("BgRemover", "BgRemover").clear()
    yield tmp_path


def _settings() -> QSettings:
    return QSettings("BgRemover", "BgRemover")


def test_migrate_initializes_fresh_settings(isolated_settings):
    settings = _settings()
    assert settings.value(SCHEMA_VERSION_KEY, None) is None

    migrate(settings)

    # Wert wird auf der Platte landen – Sync zwingt das vor dem Re-Read.
    settings.sync()
    assert int(_settings().value(SCHEMA_VERSION_KEY)) == SCHEMA_VERSION


def test_migrate_upgrades_pre_schema_settings_without_data_loss(isolated_settings):
    """Bestehende Settings ohne ``schema_version`` – etwa aus einer aelteren
    App-Version – muessen geupgradet werden, ohne dass vorhandene
    Schluessel (z. B. ``recent_files``) angefasst werden.
    """
    pre = _settings()
    pre.setValue("recent_files", ["/tmp/a.png", "/tmp/b.png"])
    pre.setValue("open_dir", "/home/u/Bilder")
    pre.sync()
    assert pre.value(SCHEMA_VERSION_KEY, None) is None

    migrate(pre)
    pre.sync()

    after = _settings()
    assert int(after.value(SCHEMA_VERSION_KEY)) == SCHEMA_VERSION
    assert after.value("recent_files") == ["/tmp/a.png", "/tmp/b.png"]
    assert after.value("open_dir") == "/home/u/Bilder"


def test_migrate_is_idempotent(isolated_settings):
    settings = _settings()
    migrate(settings)
    migrate(settings)  # kein Crash, kein Datenverlust
    settings.sync()
    assert int(_settings().value(SCHEMA_VERSION_KEY)) == SCHEMA_VERSION


def test_migrate_with_future_version_warns_but_does_not_crash(
    isolated_settings, caplog,
):
    """Eine zukuenftige Version darf NICHT zurueckgeschrieben werden –
    sonst wuerde ein Downgrade User-Daten implizit beschneiden. Stattdessen
    nur warnen.
    """
    future = SCHEMA_VERSION + 99
    settings = _settings()
    settings.setValue(SCHEMA_VERSION_KEY, future)
    settings.sync()

    with caplog.at_level(logging.WARNING, logger="BgRemover"):
        migrate(settings)

    settings.sync()
    assert int(_settings().value(SCHEMA_VERSION_KEY)) == future
    assert any(
        "schema_version" in record.message and "neuer" in record.message
        for record in caplog.records
    )


def test_migrate_with_corrupt_version_recovers(isolated_settings, caplog):
    """Ein nicht-numerischer ``schema_version``-Wert (z. B. manuell
    editierte INI) darf den Start nicht abreissen lassen – die Migration
    behandelt ihn wie 'nicht gesetzt' und ueberschreibt mit der aktuellen
    Version.
    """
    settings = _settings()
    settings.setValue(SCHEMA_VERSION_KEY, "kaputt")
    settings.sync()

    with caplog.at_level(logging.WARNING, logger="BgRemover"):
        migrate(settings)

    settings.sync()
    assert int(_settings().value(SCHEMA_VERSION_KEY)) == SCHEMA_VERSION
    assert any("unleserlicher" in record.message for record in caplog.records)


def test_main_window_runs_migration_on_construction(qapp, isolated_settings):
    """``MainWindow.__init__`` muss die Migration direkt nach der
    QSettings-Konstruktion aufrufen, sonst wuerden kuenftige
    Migrationsschritte erst nach dem ersten Lese-Zugriff greifen.
    """
    from bgremover import MainWindow

    w = MainWindow()
    w._settings.sync()
    assert int(_settings().value(SCHEMA_VERSION_KEY)) == SCHEMA_VERSION
