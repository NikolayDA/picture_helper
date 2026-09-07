"""Wächter über die zentrale QSettings-Isolation aus ``tests/conftest.py``.

Die Suite baut ``MainWindow``-Instanzen, und ``MainWindow.__init__`` liest
``QSettings("BgRemover", "BgRemover")`` – ohne Umlenkung also die *echte*
Nutzerkonfiguration. Daraus kommt auch die prozessweite UI-Locale: eine dort
gespeicherte englische Oberflächensprache ließ jeden Test scheitern, der
deutsche Meldungen erwartet. Umgekehrt schrieb der Lauf Testwerte zurück.

Die Umlenkung (``QStandardPaths.setTestModeEnabled``) wirkt nur, solange vor
``conftest.py`` noch kein ``QSettings`` konstruiert wurde. Diese Annahme ist
still: greift sie nicht mehr, bleibt der Lauf grün und leert dabei die
Konfiguration des Nutzers. Deshalb hier fail-closed geprüft.
"""
import os
from pathlib import Path

from PyQt6.QtCore import QSettings

from bgremover.i18n import DEFAULT_LOCALE, current_locale


def _resolved_settings_path() -> Path:
    return Path(QSettings("BgRemover", "BgRemover").fileName()).resolve()


def test_qsettings_liegt_im_testmodus_zweig() -> None:
    """Der aufgelöste Pfad liegt im ``~/.qttest``-Zweig, nicht im Nutzerprofil."""
    assert ".qttest" in _resolved_settings_path().parts, (
        "QSettings zeigt nicht in den Qt-Testmodus-Zweig – die Isolation aus "
        "tests/conftest.py greift nicht."
    )


def test_qsettings_meidet_die_echten_konfigurationsorte() -> None:
    """Weder der XDG- noch der macOS-Ablageort des Nutzers wird berührt."""
    path = _resolved_settings_path()
    home = Path.home().resolve()
    for verboten in (home / ".config", home / "Library" / "Preferences"):
        assert not path.is_relative_to(verboten), (
            f"QSettings schreibt nach {path} und damit in die echte "
            f"Nutzerkonfiguration unter {verboten}."
        )


def test_subprozesse_erben_ein_umgelenktes_konfigverzeichnis() -> None:
    """Die App-Smoke-Tests starten eigene Prozesse; der Testmodus wirkt dort
    nicht (er ist prozesslokal). Für sie trägt allein ``XDG_CONFIG_HOME``."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    assert xdg, "XDG_CONFIG_HOME ist nicht gesetzt – Subprozesse schreiben real."
    assert not Path(xdg).resolve().is_relative_to((Path.home() / ".config").resolve())


def test_locale_startet_je_test_auf_dem_default() -> None:
    """Die autouse-Fixture setzt die prozessweite Locale vor jedem Test zurück –
    sonst entscheidet die Testreihenfolge über die erwartete Sprache."""
    assert current_locale() == DEFAULT_LOCALE
