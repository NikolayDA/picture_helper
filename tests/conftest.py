"""Gemeinsame pytest-Fixtures.

Setzt das Qt-Platform-Plugin normalerweise auf ``offscreen``, damit die Tests
headless laufen (CI, lokale Server ohne Display), und stellt eine geteilte
``QApplication`` als Session-Fixture bereit. Die explizite Hardware-Abnahme
mit ``ABNAHME_REQUIRE_NATIVE_3D=1`` lässt Qt dagegen sein natives Backend aus
der laufenden Desktop-Session wählen.
"""
import atexit
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if os.environ.get("ABNAHME_REQUIRE_NATIVE_3D") != "1":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Konfigurationspfad der *Subprozesse* umlenken: die App-Smoke-Tests starten
# ``python -m bgremover`` bzw. ein eigenes ``MainWindow`` in einem eigenen
# Prozess, den der Qt-Testmodus weiter unten nicht erreicht (der wirkt nur
# prozesslokal). Ohne diese Zeile schreibt der Testlauf ``recent_files`` &
# Co. in die echte Nutzerkonfiguration. ``XDG_CONFIG_HOME`` wird sonst
# nirgends ausgewertet, das Setzen ist also nebenwirkungsfrei -- deckt aber
# nur Linux ab; unter macOS legt Qt seine Preferences unabhängig davon an.
_XDG_CONFIG_TMP = tempfile.mkdtemp(prefix="bgremover-tests-config-")
os.environ["XDG_CONFIG_HOME"] = _XDG_CONFIG_TMP
atexit.register(shutil.rmtree, _XDG_CONFIG_TMP, ignore_errors=True)

# Qt-Testmodus: verlegt alle schreibbaren Standardpfade prozesslokal in einen
# eigenen Zweig (``~/.qttest``). Ohne ihn liest ``MainWindow.__init__`` die
# *echte* Nutzerkonfiguration (``QSettings("BgRemover", "BgRemover")``) und
# schreibt beim Schließen hinein -- der Testlauf hängt dann an den
# Einstellungen des jeweiligen Rechners (eine dort gespeicherte englische
# Oberflächensprache lässt jeden Test scheitern, der deutsche Meldungen
# erwartet) und hinterlässt darin Testwerte. Ebenfalls abgedeckt: der
# Log-Pfad aus ``logging_config`` (``QStandardPaths.AppDataLocation``).
#
# Der Aufruf steht bewusst VOR jedem Projekt-Import: Qt friert die
# aufgelösten Pfade ab dem ersten konstruierten ``QSettings`` ein, ein
# späterer Testmodus wirkt dann auch auf neu gebaute Objekte nicht mehr.
# ``QSettings.setPath()`` (früher in einzelnen Testmodulen, mit diesem Stand
# entfernt) leistet das nicht -- der Pfad blieb die echte Nutzerdatei.
from PyQt6.QtCore import QSettings, QStandardPaths

QStandardPaths.setTestModeEnabled(True)

# Fail-closed statt Vertrauen auf die Importreihenfolge: ein später
# ergänzter QSettings-Zugriff auf Modulebene -- im Paket oder in einem über
# Entry-Points geladenen pytest-Plugin (die lädt pytest VOR dieser Datei) --
# hängt die Umlenkung still aus. Der Lauf bliebe grün, während die
# autouse-Fixture unten die echte Nutzerkonfiguration leert. Deshalb hier
# hart abbrechen; ``tests/test_settings_isolation.py`` prüft dasselbe je Lauf.
_SETTINGS_PROBE = Path(QSettings("BgRemover", "BgRemover").fileName())
if ".qttest" not in _SETTINGS_PROBE.parts:
    raise RuntimeError(
        "QSettings-Isolation greift nicht: aufgelöster Pfad "
        f"{_SETTINGS_PROBE}. Vor tests/conftest.py wurde bereits ein QSettings "
        "konstruiert (Paket-Import oder pytest-Plugin); Qt hält die Pfade dann "
        "fest. Der Testlauf würde die echte Nutzerkonfiguration lesen und leeren."
    )

# Repo-Root in sys.path aufnehmen, damit Unit-Tests die aktuelle Quelle
# importieren. Die App-Smoke-Tests prüfen zusätzlich die echte Installation
# aus einem neutralen Arbeitsverzeichnis; dafür ``make install-test`` nutzen.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgremover.qt_plugins import ensure_qt_plugin_path

ensure_qt_plugin_path()

import pytest
from PyQt6.QtWidgets import QApplication

# Mini-Programm, das genau den riskanten Schritt macht: QApplication
# konstruieren. Schlägt das Plattform-Plugin fehl, ruft Qt qFatal() →
# abort() auf C-Ebene auf – das beendet *diesen* Subprozess, nicht den
# pytest-Lauf.
_PROBE_SRC = (
    "from PyQt6.QtWidgets import QApplication; "
    "QApplication([]); print('QAPP_OK')"
)


def _qt_platform_diagnosis() -> str | None:
    """Prüft in einem Wegwerf-Subprozess, ob ``QApplication`` startet.

    Qt ruft bei nicht ladbarem Plattform-Plugin ``qFatal()`` →
    ``abort()`` auf C-Ebene auf. Das lässt sich in Python **nicht** per
    ``try/except`` abfangen und würde sonst den gesamten ``pytest``-Lauf
    mit einem SIGABRT-Stacktrace abreißen. Der Subprozess isoliert
    dieses Risiko: schlägt er fehl, liefert diese Funktion eine lesbare
    Diagnose (inkl. der echten Qt-Meldung) statt eines Prozessabbruchs.
    Rückgabe ``None`` = Umgebung in Ordnung.
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _PROBE_SRC],
            env=os.environ.copy(),
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return ("Qt-Plattform-Probe hat das Zeitlimit (60 s) überschritten "
                "– QApplication konnte nicht initialisiert werden.")
    if proc.returncode == 0 and "QAPP_OK" in proc.stdout:
        return None

    qt_msg = (proc.stderr or "").strip() or "(keine Qt-Ausgabe erfasst)"
    py = "{}.{}.{}".format(*sys.version_info[:3])
    hint = ""
    if sys.version_info[:2] >= (3, 14):
        hint = (
            f"\nHinweis: Python {py} ist offiziell nicht getestet "
            "(Classifier: 3.10–3.13).\n"
            "  -> venv auf 3.12/3.13 neu aufbauen:\n"
            "     rm -rf .venv && python3.12 -m venv .venv && "
            "source .venv/bin/activate && make install-test\n"
        )
    return (
        "Qt konnte das Plattform-Plugin 'offscreen' nicht initialisieren "
        f"(Python {py}). Ein direkter QApplication-Start würde den "
        "Testlauf mit SIGABRT abbrechen – stattdessen hier ein sauberer "
        f"Abbruch mit Diagnose.\n{hint}"
        "Echte Qt-Meldung des Probe-Subprozesses:\n"
        f"  {qt_msg}\n\n"
        "Genauere Analyse:\n"
        "  QT_DEBUG_PLUGINS=1 QT_QPA_PLATFORM=offscreen python -c "
        "'from PyQt6.QtWidgets import QApplication; QApplication([])'\n"
        "Siehe auch TESTING.md (Abschnitt „Unterstützte Python-Version“)."
    )


@pytest.fixture(scope="session")
def qapp():
    diagnosis = _qt_platform_diagnosis()
    if diagnosis is not None:
        pytest.exit(diagnosis, returncode=1)
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture(autouse=True)
def _reset_settings_and_locale():
    """Startet jeden Test mit leeren Einstellungen und der Default-Locale.

    ``i18n._current_locale`` ist prozessweiter Zustand: baut ein Test ein
    ``MainWindow``, übernimmt dieses die Sprache aus den Einstellungen und
    behält sie für alle folgenden Tests bei. Zusammen mit den ebenfalls
    prozessweit wirkenden ``QSettings`` machte das die Suite von der
    Testreihenfolge abhängig. Beides wird vor *und* nach jedem Test
    zurückgesetzt; Tests, die eine andere Sprache oder vorbelegte
    Einstellungen brauchen, setzen sie wie bisher selbst.
    """
    from bgremover import i18n

    def _reset() -> None:
        settings = QSettings("BgRemover", "BgRemover")
        settings.clear()
        settings.sync()
        i18n.configure_locale(i18n.DEFAULT_LOCALE)

    _reset()
    yield
    _reset()


@pytest.fixture(autouse=True)
def _no_rembg_warmup(monkeypatch):
    """Unterbindet den echten rembg-Warmup in *allen* Tests.

    ``MainWindow.__init__`` startet bei installiertem ``rembg`` einen
    Hintergrund-Thread, der beim ersten Aufruf ein ~176 MB ONNX-Modell
    über das Netz herunterlädt (``rembg`` → ``pooch``). Im Testlauf ist
    das nicht-deterministisch, langsam und kann – mehrere Tests bauen
    ``MainWindow`` – den Prozess mit SIGABRT abreißen, sobald das
    ``ai``-Extra im Test-venv installiert ist. Die Tests sollen
    hermetisch und offline sein; einige Tests unterdrücken den Warmup
    schon einzeln, hier wird das zentral für alle erzwungen. Das
    Produktionsverhalten bleibt unverändert (nur der Testlauf ist
    betroffen). ``raising=False``: greift auch, falls die Methode mal
    umbenannt wird, ohne stillschweigend zu brechen.
    """
    import bgremover

    monkeypatch.setattr(
        bgremover.MainWindow, "_start_rembg_warmup",
        lambda self: None, raising=False,
    )


@pytest.fixture(autouse=True)
def _auto_confirm_discard(monkeypatch):
    """Neutralisiert die „Ungespeicherte Änderungen"-Nachfrage in allen Tests.

    ``MainWindow`` fragt vor dem Schließen/Bildwechsel bei ungespeicherten
    Änderungen per modalem ``QMessageBox`` nach – das würde headless ohne
    Klick eine eigene Event-Loop starten und den Testlauf blockieren. Hier
    zentral auf „fortfahren" (True) gesetzt, damit bestehende Tests wie
    bisher schließen/laden. Tests, die das Verhalten gezielt prüfen,
    überschreiben den Patch auf Instanzebene. ``raising=False``: greift auch,
    falls die Methode umbenannt wird, ohne stillschweigend zu brechen.
    """
    import bgremover

    monkeypatch.setattr(
        bgremover.MainWindow, "_confirm_discard_changes",
        lambda self: True, raising=False,
    )
