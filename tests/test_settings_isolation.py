"""Wächter über die zentrale QSettings-Isolation aus ``tests/conftest.py``.

Die Suite baut ``MainWindow``-Instanzen, und ``MainWindow.__init__`` liest
``QSettings("BgRemover", "BgRemover")`` – ohne Umlenkung also die *echte*
Nutzerkonfiguration. Daraus kommt auch die prozessweite UI-Locale: eine dort
gespeicherte englische Oberflächensprache ließ jeden Test scheitern, der
deutsche Meldungen erwartet. Umgekehrt schrieb der Lauf Testwerte zurück.

Die Umlenkung ist still: greift sie nicht mehr, bleibt der Lauf grün und
verändert dabei die Konfiguration des Nutzers. Deshalb hier je Lauf geprüft.
"""
import os
import sys
from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings

from bgremover.i18n import DEFAULT_LOCALE, current_locale


def _resolved_settings_path() -> Path:
    return Path(QSettings("BgRemover", "BgRemover").fileName()).resolve()


def test_qsettings_meidet_die_echten_konfigurationsorte(settings_isolated) -> None:
    """Der aufgelöste Pfad liegt nicht in der Ablage des Nutzers."""
    if not settings_isolated:
        pytest.skip("Plattform ohne umlenkbare QSettings-Ablage (macOS/CFPreferences)")
    path = _resolved_settings_path()
    home = Path.home().resolve()
    for verboten in (home / ".config", home / "Library" / "Preferences"):
        assert not path.is_relative_to(verboten), (
            f"QSettings schreibt nach {path} und damit in die echte "
            f"Nutzerkonfiguration unter {verboten}."
        )


def test_qsettings_liegt_im_wegwerf_verzeichnis(settings_isolated) -> None:
    """Positiv geprüft: die Ablage liegt im temporären Verzeichnis des Laufs."""
    if not settings_isolated:
        pytest.skip("Plattform ohne umlenkbare QSettings-Ablage (macOS/CFPreferences)")
    assert "bgremover-tests-qsettings-" in str(_resolved_settings_path())


def test_umlenkung_greift_ausserhalb_von_macos(settings_isolated) -> None:
    """Nur macOS darf ohne Umlenkung laufen (CFPreferences statt Datei).

    Anderswo ist ein Ausfall ein Fehler, kein hinzunehmender Zustand – dort
    bricht ``conftest.py`` bereits beim Import ab. Dieser Test hält fest,
    dass die Ausnahme nicht unbemerkt auf weitere Plattformen wächst.
    """
    assert settings_isolated or sys.platform == "darwin"


@pytest.mark.parametrize(
    ("variable", "echter_ort"),
    [
        ("XDG_CONFIG_HOME", ".config"),   # QSettings der Subprozesse
        ("XDG_DATA_HOME", ".local"),      # Log-Verzeichnis aus logging_config
        ("XDG_CACHE_HOME", ".cache"),
    ],
)
def test_subprozesse_erben_umgelenkte_standardpfade(variable, echter_ort) -> None:
    """Die App-Smoke-Tests starten eigene Prozesse; die Umlenkungen im Prozess
    wirken dort nicht. Für sie tragen allein die XDG-Variablen (Linux)."""
    wert = os.environ.get(variable)
    assert wert, f"{variable} ist nicht gesetzt – Subprozesse schreiben real."
    assert not Path(wert).resolve().is_relative_to((Path.home() / echter_ort).resolve())


def test_locale_startet_je_test_auf_dem_default() -> None:
    """Die autouse-Fixture setzt die prozessweite Locale vor jedem Test zurück –
    sonst entscheidet die Testreihenfolge über die erwartete Sprache."""
    assert current_locale() == DEFAULT_LOCALE
