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

import bgremover.settings_schema as _ss
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


def test_migrate_from_older_version_without_registered_step(
    isolated_settings, caplog,
):
    """Eine bestehende, aber ältere Version (0) durchläuft die
    Migrationsschleife. Da für 0→1 (noch) kein Schritt registriert ist,
    wird gewarnt und die Version direkt auf ``SCHEMA_VERSION`` gehoben –
    ohne Datenverlust und ohne Crash.
    """
    settings = _settings()
    settings.setValue("recent_files", ["/tmp/x.png"])
    settings.setValue(SCHEMA_VERSION_KEY, 0)
    settings.sync()

    with caplog.at_level(logging.WARNING, logger="BgRemover"):
        migrate(settings)

    settings.sync()
    after = _settings()
    assert int(after.value(SCHEMA_VERSION_KEY)) == SCHEMA_VERSION
    assert after.value("recent_files") == ["/tmp/x.png"]
    assert any("keine Migration" in record.message for record in caplog.records)


def test_migrate_runs_registered_step(isolated_settings, monkeypatch):
    """Sichert das Migrationsmuster für künftige Schritte: ist ein Schritt
    für die aktuelle Version registriert, wird er ausgeführt und die
    Version anschließend hochgezogen. Aktuell ist ``_MIGRATIONS`` leer,
    daher wird hier ein Schritt für 0→1 temporär eingehängt.
    """
    calls: list[bool] = []
    monkeypatch.setitem(_ss._MIGRATIONS, 0, lambda s: calls.append(True))

    settings = _settings()
    settings.setValue(SCHEMA_VERSION_KEY, 0)
    settings.sync()

    migrate(settings)
    settings.sync()

    assert calls == [True]
    assert int(_settings().value(SCHEMA_VERSION_KEY)) == SCHEMA_VERSION


def test_main_window_runs_migration_on_construction(qapp, isolated_settings):
    """``MainWindow.__init__`` muss die Migration direkt nach der
    QSettings-Konstruktion aufrufen, sonst wuerden kuenftige
    Migrationsschritte erst nach dem ersten Lese-Zugriff greifen.
    """
    from bgremover import MainWindow

    w = MainWindow()
    w._settings.sync()
    assert int(_settings().value(SCHEMA_VERSION_KEY)) == SCHEMA_VERSION


def test_is_future_schema_detects_newer_version(isolated_settings):
    """``is_future_schema`` erkennt eine gespeicherte Version, die neuer ist als
    die vom Code unterstuetzte – Grundlage dafuer, Zukunfts-Settings (z. B.
    ``recent_files``) nicht zu ueberschreiben (#240)."""
    from bgremover.settings_schema import is_future_schema

    settings = _settings()
    assert is_future_schema(settings) is False        # nicht gesetzt -> keine Zukunft
    settings.setValue(SCHEMA_VERSION_KEY, SCHEMA_VERSION)
    assert is_future_schema(settings) is False        # aktuelle Version
    settings.setValue(SCHEMA_VERSION_KEY, SCHEMA_VERSION + 1)
    assert is_future_schema(settings) is True         # Zukunft
    settings.setValue(SCHEMA_VERSION_KEY, "kaputt")
    assert is_future_schema(settings) is False        # unleserlich -> wie nicht gesetzt
