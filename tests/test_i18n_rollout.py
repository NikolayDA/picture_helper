"""Rollout guards for the i18n runtime languages (PR 4b).

PR 4b adds English as a runtime language plus a language selector in the
settings dialog. These tests enforce that every locale stays key-for-key and
placeholder-for-placeholder in sync with German, that the whole UI builds under
each locale, and that the selector persists the choice with a restart hint.
"""
from __future__ import annotations

import string

import pytest
from PyQt6.QtCore import QSettings

import bgremover.i18n as i18n
from bgremover.i18n import (
    DEFAULT_LOCALE,
    SETTINGS_LOCALE_KEY,
    available_locales,
    configure_locale,
    current_locale,
)


def _placeholders(text: str) -> set[str]:
    return {
        field for _, field, _, _ in string.Formatter().parse(text)
        if field is not None
    }


@pytest.fixture(autouse=True)
def reset_locale():
    configure_locale(DEFAULT_LOCALE)
    yield
    configure_locale(DEFAULT_LOCALE)


def _use_settings_path(tmp_path) -> QSettings:
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    settings = QSettings("BgRemover", "BgRemover")
    settings.clear()
    return settings


# ── Cross-locale table invariants ──────────────────────────────────────

def test_every_locale_matches_german_keys() -> None:
    de_keys = set(i18n._TRANSLATIONS[DEFAULT_LOCALE])
    for locale, table in i18n._TRANSLATIONS.items():
        assert set(table) == de_keys, f"{locale}: Key-Abweichung gegenüber de"


def test_every_locale_matches_german_placeholders() -> None:
    de_table = i18n._TRANSLATIONS[DEFAULT_LOCALE]
    for locale, table in i18n._TRANSLATIONS.items():
        for key, value in table.items():
            assert _placeholders(value) == _placeholders(de_table[key]), (
                f"{locale}:{key} – Platzhalter weichen von de ab"
            )


def test_every_string_formats_without_error() -> None:
    sample = {
        "name": "x", "msg": "m", "value": 1, "modifier": "Ctrl",
        "shortcut": "Ctrl+S", "label": "L", "target": "/t",
    }
    for locale, table in i18n._TRANSLATIONS.items():
        for key, value in table.items():
            # Numeric default so fields with numeric specs ({pixels:,}, {mp:.0f})
            # also format cleanly; text fields are supplied as strings above.
            kwargs = {f: sample.get(f, 1000) for f in _placeholders(value)}
            try:
                value.format(**kwargs)  # malformed braces / unknown placeholder
            except (KeyError, ValueError, IndexError) as exc:
                pytest.fail(f"{locale}:{key} formatiert nicht: {exc!r}")


def test_available_locales_have_display_names() -> None:
    for code in available_locales():
        assert code in i18n.LOCALE_NAMES, f"Kein Anzeigename für Locale {code}"


def test_english_is_available() -> None:
    assert "en" in available_locales()


# ── Per-locale UI smoke ────────────────────────────────────────────────

@pytest.mark.parametrize("locale", list(available_locales()))
def test_main_window_builds_in_every_locale(qapp, tmp_path, locale) -> None:
    settings = _use_settings_path(tmp_path)
    settings.setValue(SETTINGS_LOCALE_KEY, locale)
    settings.sync()
    from bgremover import MainWindow

    window = MainWindow()
    try:
        assert current_locale() == locale
    finally:
        window.close()


def test_english_locale_wires_through_to_ui(qapp, tmp_path) -> None:
    settings = _use_settings_path(tmp_path)
    settings.setValue(SETTINGS_LOCALE_KEY, "en")
    settings.sync()
    from bgremover import MainWindow

    window = MainWindow()
    try:
        assert current_locale() == "en"
        assert window.menuBar().actions()[0].text() == "File"
        status_bar = window.statusBar()
        assert status_bar is not None
        assert status_bar.currentMessage() == (
            "Open an image: File → Open  or  drag & drop onto the canvas"
        )
    finally:
        window.close()


# ── Settings dialog language selector ──────────────────────────────────

def test_language_selector_persists_choice_and_hints(qapp, tmp_path, monkeypatch) -> None:
    settings = _use_settings_path(tmp_path)
    settings.sync()
    configure_locale("de")  # running app is German
    import bgremover.settings_dialog as sd
    from bgremover.settings_dialog import SettingsDialog

    hints: list = []
    monkeypatch.setattr(
        sd.QMessageBox, "information", lambda *a, **k: hints.append(a))

    dlg = SettingsDialog(settings)
    try:
        codes = {
            dlg._lang_combo.itemData(i) for i in range(dlg._lang_combo.count())
        }
        assert codes == set(available_locales())
        assert dlg._lang_combo.currentData() == "de"  # mirrors active locale

        dlg._lang_combo.setCurrentIndex(dlg._lang_combo.findData("en"))
        dlg._save_and_accept()

        assert settings.value(SETTINGS_LOCALE_KEY) == "en"
        assert hints, "Neustart-Hinweis muss beim Sprachwechsel erscheinen"
    finally:
        dlg.close()


def test_language_selector_no_hint_when_unchanged(qapp, tmp_path, monkeypatch) -> None:
    settings = _use_settings_path(tmp_path)
    settings.sync()
    configure_locale("de")
    import bgremover.settings_dialog as sd
    from bgremover.settings_dialog import SettingsDialog

    hints: list = []
    monkeypatch.setattr(
        sd.QMessageBox, "information", lambda *a, **k: hints.append(a))

    dlg = SettingsDialog(settings)
    try:
        dlg._save_and_accept()  # keep German
        assert settings.value(SETTINGS_LOCALE_KEY) == "de"
        assert not hints, "Ohne Sprachwechsel darf kein Neustart-Hinweis erscheinen"
    finally:
        dlg.close()
