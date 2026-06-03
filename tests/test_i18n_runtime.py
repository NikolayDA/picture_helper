"""Tests for the lightweight runtime-i18n foundation."""
from __future__ import annotations

import pytest
from PyQt6.QtCore import QSettings

import bgremover.i18n as i18n
from bgremover.i18n import (
    DEFAULT_LOCALE,
    SETTINGS_LOCALE_KEY,
    configure_locale,
    current_locale,
    normalize_locale,
    tr,
)
from bgremover.status_messages import StatusMessages as SM


@pytest.fixture(autouse=True)
def reset_locale():
    configure_locale(DEFAULT_LOCALE)
    yield
    configure_locale(DEFAULT_LOCALE)


def test_normalize_locale_uses_supported_language_and_german_fallback() -> None:
    assert normalize_locale(None) == "de"
    assert normalize_locale("") == "de"
    assert normalize_locale("de-DE") == "de"
    assert normalize_locale("de_AT.UTF-8") == "de"
    assert normalize_locale("en-US") == "de"


def test_translate_uses_active_locale_then_german_fallback(monkeypatch) -> None:
    monkeypatch.setitem(i18n._TRANSLATIONS, "zz", {"menu.file": "File"})

    assert configure_locale("zz-ZZ") == "zz"
    assert tr("menu.file") == "File"
    assert tr("action.save") == "Speichern"


def test_translate_unknown_key_raises_key_error() -> None:
    with pytest.raises(KeyError, match="Unbekannter UI-String"):
        tr("missing.key")


def test_status_messages_are_runtime_translated(monkeypatch) -> None:
    monkeypatch.setitem(
        i18n._TRANSLATIONS,
        "zz",
        {"status.no_image_loaded": "No image loaded"},
    )
    configure_locale("zz")

    assert SM.KEIN_BILD_GELADEN == "No image loaded"
    assert SM.KEIN_BILD_ZUM_SPEICHERN == "Kein Bild zum Speichern"


def test_main_window_initializes_locale_from_settings(qapp, tmp_path, monkeypatch) -> None:
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    settings = QSettings("BgRemover", "BgRemover")
    settings.clear()
    settings.setValue(SETTINGS_LOCALE_KEY, "zz")
    settings.sync()
    monkeypatch.setitem(
        i18n._TRANSLATIONS,
        "zz",
        {
            "menu.file": "File",
            "status.start_hint": "Open an image",
        },
    )

    from bgremover import MainWindow

    monkeypatch.setattr(MainWindow, "_start_rembg_warmup", lambda self: None)
    window = MainWindow()
    try:
        assert current_locale() == "zz"
        assert window.menuBar().actions()[0].text() == "File"
        status_bar = window.statusBar()
        assert status_bar is not None
        assert status_bar.currentMessage() == "Open an image"
    finally:
        window.close()
