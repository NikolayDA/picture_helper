"""Gemeinsame pytest-Fixtures.

Setzt das Qt-Platform-Plugin auf ``offscreen``, damit die Tests headless
laufen (CI, lokale Server ohne Display) und stellt eine geteilte
``QApplication`` als Session-Fixture bereit.
"""
import os
import sys
import subprocess
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Repo-Root in sys.path aufnehmen, damit ``import BgRemover`` funktioniert,
# wenn das Paket nicht per ``pip install -e .`` installiert wurde.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
    py = "%d.%d.%d" % sys.version_info[:3]
    hint = ""
    if sys.version_info[:2] >= (3, 14):
        hint = (
            f"\nHinweis: Python {py} ist offiziell nicht getestet "
            "(Classifier: 3.10–3.13), funktioniert aber mit "
            "PyQt6 >= 6.11 (cp314-Wheels mit lauffähigem "
            "'offscreen'-Plugin).\n"
            "  -> zuerst:  pip install -U PyQt6\n"
            "  -> hilft das nicht, venv auf 3.12/3.13 neu aufbauen:\n"
            "     rm -rf .venv && python3.12 -m venv .venv && "
            "source .venv/bin/activate && pip install -e \".[test]\"\n"
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
    import BgRemover

    monkeypatch.setattr(
        BgRemover.MainWindow, "_start_rembg_warmup",
        lambda self: None, raising=False,
    )
