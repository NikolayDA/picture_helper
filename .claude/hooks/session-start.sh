#!/bin/bash
# SessionStart-Hook für Claude Code on the web.
#
# Richtet die Umgebung so ein, dass ruff, mypy und pytest in einer
# frischen Web-Session sofort laufen. Hintergrund: BgRemover nutzt
# PyQt6; die headless-Qt-Plattform braucht einige System-
# bibliotheken (libEGL & xcb-Familie), die im Web-Container nicht
# vorinstalliert sind.
#
# Synchron (kein async): die Session startet erst, wenn alle
# Abhängigkeiten stehen – verhindert, dass Claude Tests/Linter
# startet, bevor sie verfügbar sind.
set -euo pipefail

# Klarer Fehler statt stillem Abbruch (Issue #553): set -e beendet das
# Skript bei jedem fehlgeschlagenen Befehl, aber ohne Kontext sieht das wie
# ein Hook aus, der gar nicht gelaufen ist. Der Trap meldet Skript+Zeile.
trap 'echo "SessionStart-Hook: FEHLGESCHLAGEN in ${BASH_SOURCE[0]}:${LINENO} – ruff/mypy/pytest sind ggf. nicht installiert. Siehe Ausgabe oberhalb für die Ursache." >&2' ERR

# Nur in der entfernten Web-Umgebung ausführen. Lokal richtet die
# Entwicklerin ihre venv selbst ein (siehe README / INSTALL_*).
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}"

# Headless-Qt für alle Session-Befehle persistent setzen. conftest.py
# setzt es für pytest ohnehin per setdefault – das hier deckt direkte
# Qt-Aufrufe (z. B. `import bgremover` in einem Ad-hoc-Skript) mit ab.
# Muss VOR der Vorprüfung unten stehen (Review-Fund zu #553): sonst bekommt
# eine Session, die den Kurzschluss nimmt, nie QT_QPA_PLATFORM gesetzt.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export QT_QPA_PLATFORM=offscreen' >> "$CLAUDE_ENV_FILE"
fi

# Idempotente Vorprüfung (#553): Läuft der Hook in einer Folge-Session mit
# gecachtem Container erneut, sind Systemlibs + editable Install oft schon
# vorhanden. Dann apt/pip-Arbeit überspringen statt sie folgenlos zu
# wiederholen – spart Zeit und reduziert die Fläche für neue Fehlschläge.
#
# Jede Teilprüfung deckt genau die Lücke ab, die apt/pip weiter unten
# schließen (Review-Funde zu #553):
# - `PyQt6.QtWidgets` statt nur `PyQt6` laden, weil das Namespace-Paket
#   ohne die Qt-Systemlibs (libGL/libEGL) importierbar bleibt – erst
#   QtWidgets zieht sie tatsächlich.
# - pip-Version explizit gegen die Mindestversion prüfen, statt sie beim
#   Überspringen stillschweigend unterhalb des CVE-Floors zu belassen.
# - `bgremover`-Paketmetadaten (nicht nur den Quellbaum-Import) und
#   `pytest-qt` prüfen, sonst kann der Kurzschluss greifen, obwohl
#   `.[test]` nie installiert wurde.
if python3 -m ruff --version >/dev/null 2>&1 \
  && python3 -m mypy --version >/dev/null 2>&1 \
  && python3 -m pytest --version >/dev/null 2>&1 \
  && python3 -c "
import sys
from importlib import metadata
from packaging.version import Version
import PyQt6.QtWidgets  # noqa: F401 -- erzwingt libGL/libEGL-Ladeversuch
import pytestqt  # noqa: F401
metadata.version('bgremover')
sys.exit(0 if Version(metadata.version('pip')) >= Version('26.1.2') else 1)
" >/dev/null 2>&1; then
  echo "SessionStart-Hook: Umgebung bereits vollständig (ruff/mypy/pytest/PyQt6/pytest-qt/bgremover/pip>=26.1.2) – überspringe Install."
  exit 0
fi

# Qt-Systembibliotheken – dieselbe Qt-Lib-Liste wie in den CI-Workflows
# (.github/workflows/ci.yml, pr-ci.yml, ui-nightly.yml, benchmark.yml), dort auf
# ubuntu-latest erprobt. Ein Drift-Test (tests/test_ci_qt_packages.py)
# haelt diese Listen konsistent – fehlt z. B. libgl1 irgendwo, schlaegt
# beim Import von PyQt6 sonst nur „libGL.so.1: cannot open shared object".
if command -v apt-get >/dev/null 2>&1; then
  # Best-effort: defekte Fremd-PPAs (z. B. deadsnakes/php in manchen
  # Containern) dürfen das Setup nicht abbrechen – die benötigten
  # Qt-Pakete liegen im Haupt-Archiv. Schlägt der eigentliche
  # install-Schritt fehl, bricht der Hook (set -e) ohnehin laut ab.
  sudo apt-get update -qq \
    || echo "Hinweis: apt-get update teilweise fehlgeschlagen (fremde PPAs) – fahre fort."
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    libegl1 libgl1 libfontconfig1 libxkbcommon0 libdbus-1-3 \
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
    libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xkb1
fi

# pip>=26.1.2 vor dem Install erzwingen: schliesst den pip-CVE-Batch (#202,
# Path-Traversal/Symlink/Modul-Hijacking) auch in der Web-Session – pip ist das
# Installationswerkzeug selbst und laesst sich daher nicht ueber constraints.txt
# anheben. Gleiche Mindestversion wie in den CI-Workflows (tests/test_ci_pip_pin.py).
#
# --ignore-installed ist hier zwingend (Befund zu #553): Der Web-Container
# bringt pip 24.0 als Debian-Paket mit (apt, nicht pip-verwaltet) – ohne
# RECORD-Metadatei kann pip sein eigenes Debian-Paket nicht sauber
# deinstallieren ("Cannot uninstall pip 24.0, RECORD file not found") und
# bricht unter set -e sofort ab, VOR dem eigentlichen Projekt-Install in
# Zeile unten. Das war die tatsächliche Ursache des in #553 beobachteten
# stillen Fehlschlags (weder Qt-Systemlibs- noch pip-Install-Schritt selbst
# waren defekt). --ignore-installed installiert die neue Version daneben,
# ohne das kaputte RECORD zu benötigen.
python3 -m pip install -q --upgrade --ignore-installed "pip>=26.1.2"

# Projekt inkl. Test-/Lint-Werkzeuge (pytest, pytest-qt, ruff, mypy).
# Idempotent; -e nutzt den Container-Cache bei Folge-Sessions. Mit dem
# Constraints-Pinning des Projekts wie in Makefile/CI (#205/#206: haelt
# u. a. urllib3/idna auf den gepatchten Releases) – sonst loest pip im
# Web-Container frei auf und kann verwundbare Versionen einspielen.
python3 -m pip install -q --constraint requirements/constraints.txt -e ".[test]"

echo "SessionStart-Hook: Umgebung bereit (ruff/mypy/pytest lauffähig)."
