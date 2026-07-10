"""Tests fuer die QSettings-Schema-Versionierung.

Die Migration ist heute nur ein Grundstein – Version 0→1 ist ein expliziter
No-op. Die Tests sichern die relevanten Pfade fuer kuenftige Migrationen ab:

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
    EXPORT_DIR_KEY,
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


def test_migrate_v1_to_current_keeps_keys_and_defaults_new(isolated_settings):
    """Bestehende v1-Settings werden lückenlos auf die aktuelle Version gehoben,
    ohne vorhandene Schlüssel zu verlieren; die additiven EufyMake-Export-Keys
    (#355) fehlen weiterhin und defaulten beim Lesen.
    """
    pre = _settings()
    pre.setValue("save_dir", "/home/u/Export")
    pre.setValue(SCHEMA_VERSION_KEY, 1)
    pre.sync()

    migrate(pre)
    pre.sync()

    after = _settings()
    assert int(after.value(SCHEMA_VERSION_KEY)) == SCHEMA_VERSION
    assert after.value("save_dir") == "/home/u/Export"
    # Additive Keys werden nicht erzwungen – sie defaulten erst beim Lesen.
    assert after.value(EXPORT_DIR_KEY, "FALLBACK") == "FALLBACK"


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
    isolated_settings, caplog, monkeypatch,
):
    """Fehlt der unmittelbar nächste Schritt, bleibt die Version unverändert."""
    monkeypatch.delitem(_ss._MIGRATIONS, 0)
    settings = _settings()
    settings.setValue("recent_files", ["/tmp/x.png"])
    settings.setValue(SCHEMA_VERSION_KEY, 0)
    settings.sync()

    with caplog.at_level(logging.ERROR, logger="BgRemover"):
        migrate(settings)

    settings.sync()
    after = _settings()
    assert int(after.value(SCHEMA_VERSION_KEY)) == 0
    assert after.value("recent_files") == ["/tmp/x.png"]
    assert any(
        "Version 0 -> 1" in record.message and "schema_version=0" in record.message
        for record in caplog.records
    )


def test_migrate_runs_registered_step(isolated_settings, monkeypatch):
    """Sichert das Migrationsmuster für künftige Schritte: ist ein Schritt
    für die aktuelle Version registriert, wird er ausgeführt und die
    Version anschließend hochgezogen. Der 0→1-Schritt in ``_MIGRATIONS`` wird
    hier durch einen Test-Callback überschrieben, um die Ausführung zu prüfen.
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


def test_migrate_runs_complete_chain_step_by_step(isolated_settings, monkeypatch):
    """Eine vollständige Kette persistiert jeden erfolgreich erreichten Stand."""
    calls: list[tuple[int, int]] = []

    def step(version: int):
        def run(settings: QSettings) -> None:
            calls.append((version, int(settings.value(SCHEMA_VERSION_KEY))))

        return run

    monkeypatch.setattr(_ss, "SCHEMA_VERSION", 3)
    monkeypatch.setattr(_ss, "_MIGRATIONS", {
        0: step(0),
        1: step(1),
        2: step(2),
    })
    settings = _settings()
    settings.setValue(SCHEMA_VERSION_KEY, 0)

    migrate(settings)

    assert calls == [(0, 0), (1, 1), (2, 2)]
    assert int(settings.value(SCHEMA_VERSION_KEY)) == 3


def test_migrate_does_not_start_interrupted_chain(
    isolated_settings, caplog, monkeypatch,
):
    """Eine Lücke verhindert die gesamte Kette und alle Teilmigrationen."""
    calls: list[int] = []
    monkeypatch.setattr(_ss, "SCHEMA_VERSION", 3)
    monkeypatch.setattr(_ss, "_MIGRATIONS", {
        0: lambda _settings: calls.append(0),
        2: lambda _settings: calls.append(2),
    })
    settings = _settings()
    settings.setValue(SCHEMA_VERSION_KEY, 0)

    with caplog.at_level(logging.ERROR, logger="BgRemover"):
        migrate(settings)

    assert calls == []
    assert int(settings.value(SCHEMA_VERSION_KEY)) == 0
    assert any("Version 1 -> 2" in record.message for record in caplog.records)


def test_every_supported_previous_version_has_a_registered_step():
    """Die CI muss eine versehentlich lückenhafte Registry sofort erkennen."""
    assert set(range(SCHEMA_VERSION)).issubset(_ss._MIGRATIONS)


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
