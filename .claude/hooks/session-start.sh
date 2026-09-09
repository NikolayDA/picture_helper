#!/bin/bash
# SessionStart-Hook für Claude Code on the web.
#
# Richtet die Umgebung so ein, dass ruff, mypy und pytest in einer
# frischen Web-Session sofort laufen. Hintergrund: BgRemover nutzt
# PyQt6; die headless-Qt-Plattform braucht einige System-
# bibliotheken (libEGL & xcb-Familie), die im Web-Container nicht
# vorinstalliert sind.
#
# Installiert wird seit #1048 in eine projekt-lokale venv (`.venv`, in
# .gitignore; das Makefile bevorzugt `.venv/bin/python` von selbst), nicht
# mehr in den System-Interpreter: Der Web-Container bringt Debian-Pakete
# ohne RECORD-Datei mit (pip 24.0 aus #553, PyYAML 6.0.1 aus #1048), die
# pip beim Anheben auf die Constraints nicht deinstallieren kann
# („Cannot uninstall …: no RECORD file was found") – der Projekt-Install
# brach damit ab, bevor irgendetwas installiert war. In einer venv ohne
# System-Site-Packages steht kein Debian-Paket im Weg, auch nicht das
# nächste dieser Klasse.
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
PROJECT_DIR="$(pwd -P)"
VENV_DIR="$PROJECT_DIR/.venv"
VENV_PY="$VENV_DIR/bin/python"

# Headless-Qt und die venv für alle Session-Befehle persistent setzen.
# conftest.py setzt QT_QPA_PLATFORM für pytest ohnehin per setdefault – das
# hier deckt direkte Qt-Aufrufe (z. B. `import bgremover` in einem
# Ad-hoc-Skript) mit ab. PATH voran, damit `python3`/`pytest`/`ruff` in der
# Session die venv treffen (#1048) – auch `make` findet sie, weil es
# `.venv/bin/python` bevorzugt. Aufgerufen an BEIDEN Erfolgsausgängen
# (Kurzschluss und Skriptende), damit auch eine Session, die den
# Kurzschluss nimmt, QT_QPA_PLATFORM und den venv-PATH bekommt (Review-Fund
# zu #553) – und NUR dort (Review PR #1049): Ein Fehlerpfad darf kein
# ungeprüftes `bin/` (fremdes `.venv`, halbfertige venv nach abgebrochenem
# Install) an den Anfang des Session-PATH stellen; die Session fällt dann
# wie zuvor auf den System-Interpreter zurück.
persist_session_env() {
  if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    {
      echo 'export QT_QPA_PLATFORM=offscreen'
      printf 'export VIRTUAL_ENV=%q\n' "$VENV_DIR"
      # `$PATH` bewusst literal: Es wird erst beim Laden der Env-Datei expandiert.
      # shellcheck disable=SC2016
      printf 'export PATH=%q:"$PATH"\n' "$VENV_DIR/bin"
    } >> "$CLAUDE_ENV_FILE"
  fi
}

# Provenienzprüfung der bgremover-Installation (#1031). Sie läuft bewusst
# als Skript über den Dateipfad (sys.path[0] = scripts/), nicht als
# `python -c` aus der Repo-Wurzel: Dort steht das Arbeitsverzeichnis vorn
# auf sys.path, und `import bgremover` träfe den Checkout selbst dann, wenn
# in site-packages eine veraltete nicht-editable Kopie liegt – der Import
# wäre kein Beleg. Das Skript wertet nur Distributions-Metadaten aus und
# prüft den Import zusätzlich aus einem neutralen Arbeitsverzeichnis. Es
# läuft mit dem venv-Interpreter, denn dessen Suchpfad ist der der Session.
PROVENANCE_CHECK="scripts/check_install_provenance.py"

# Idempotente Vorprüfung (#553): Läuft der Hook in einer Folge-Session mit
# gecachtem Container erneut, sind Systemlibs + venv oft schon vorhanden.
# Dann apt/pip-Arbeit überspringen statt sie folgenlos zu wiederholen –
# spart Zeit und reduziert die Fläche für neue Fehlschläge.
#
# Jede Teilprüfung deckt genau die Lücke ab, die apt/pip weiter unten
# schließen (Review-Funde zu #553), und alle laufen mit dem venv-Python:
# - `PyQt6.QtWidgets` statt nur `PyQt6` laden, weil das Namespace-Paket
#   ohne die Qt-Systemlibs (libGL/libEGL) importierbar bleibt – erst
#   QtWidgets zieht sie tatsächlich.
# - pip-Version explizit gegen die Mindestversion prüfen, statt sie beim
#   Überspringen stillschweigend unterhalb des CVE-Floors zu belassen.
# - `pytest-qt` prüfen, sonst kann der Kurzschluss greifen, obwohl
#   `.[test]` nie installiert wurde.
# - `bgremover` nicht nur als vorhandene Distribution, sondern nach seiner
#   Installationsprovenienz prüfen (#1031): `make pr-check` installiert
#   bewusst nicht-editable (Makefile, `install-test`), dieser Zustand
#   überlebt im gecachten Container, und der Kurzschluss zementierte ihn –
#   per Dateipfad gestartete Subprozess-Tests maßen dann eine Kopie aus
#   einem fremden Commit, während In-Prozess-Tests über den von pytest
#   eingetragenen Checkout unauffällig blieben. Gültig ist nur ein
#   editierbarer Link (PEP 660 oder Legacy) auf genau diesen Checkout.
tools_ready=0
if [ -x "$VENV_PY" ] \
  && "$VENV_PY" -m ruff --version >/dev/null 2>&1 \
  && "$VENV_PY" -m mypy --version >/dev/null 2>&1 \
  && "$VENV_PY" -m pytest --version >/dev/null 2>&1 \
  && "$VENV_PY" -c "
import sys
from packaging.version import Version
from importlib import metadata
import PyQt6.QtWidgets  # noqa: F401 -- erzwingt libGL/libEGL-Ladeversuch
import pytestqt  # noqa: F401
sys.exit(0 if Version(metadata.version('pip')) >= Version('26.1.2') else 1)
" >/dev/null 2>&1; then
  tools_ready=1
fi
provenance_ready=0
provenance_report=""
if [ -x "$VENV_PY" ] && provenance_report="$("$VENV_PY" "$PROVENANCE_CHECK" 2>&1)"; then
  provenance_ready=1
fi
if [ "$tools_ready" = 1 ] && [ "$provenance_ready" = 1 ]; then
  persist_session_env
  echo "SessionStart-Hook: Umgebung bereits vollständig (.venv mit ruff/mypy/pytest/PyQt6/pytest-qt/pip>=26.1.2, bgremover editable auf diesen Checkout) – überspringe Install."
  exit 0
fi
if [ "$tools_ready" = 1 ]; then
  # Der Grund gehört ins Log: Ohne ihn sähe die Neuinstallation wie ein
  # verfehlter Kurzschluss aus, nicht wie die Korrektur einer fremden Kopie.
  echo "SessionStart-Hook: Werkzeuge vorhanden, aber die bgremover-Installation ist kein editierbarer Link auf diesen Checkout (#1031) – installiere neu:"
  printf '%s\n' "$provenance_report"
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

# Projekt-lokale venv (#1048). Brauchbar heißt: Interpreter läuft UND pip
# ist da – eine bei ensurepip abgebrochene oder mit `--without-pip` gebaute
# venv importiert `sys` noch, scheiterte aber in jeder Folge-Session am
# `-m pip` (Review PR #1049). Eine unbrauchbare venv wird neu angelegt –
# aber nur, wenn es wirklich eine venv ist (pyvenv.cfg): Ein fremdes `.venv`
# (Symlink, Fremdverzeichnis, toter Symlink – `-e` folgt ihm, daher auch
# `-L`) wird nicht gelöscht, sondern ist ein benannter Fehler.
# `python3 -m venv` braucht ensurepip; Debian/Ubuntu liefern es getrennt –
# nur dann nachinstallieren, und zwar für die **laufende** Minor-Version
# (`python3.11-venv`), nicht das Metapaket `python3-venv`, das auf Ubuntu
# 24.04 `python3.12-venv` zöge, während `python3` hier 3.11 ist (Review
# PR #1049); das Metapaket bleibt nur Rückfall.
if ! "$VENV_PY" -m pip --version >/dev/null 2>&1; then
  if [ -e "$VENV_DIR" ] || [ -L "$VENV_DIR" ]; then
    if [ -f "$VENV_DIR/pyvenv.cfg" ] && [ ! -L "$VENV_DIR" ]; then
      echo "SessionStart-Hook: $VENV_DIR ist unbrauchbar – lege die venv neu an."
      rm -rf "$VENV_DIR"
    else
      echo "SessionStart-Hook: $VENV_DIR existiert, ist aber keine venv (kein pyvenv.cfg oder Symlink) – bitte von Hand prüfen." >&2
      exit 1
    fi
  fi
  if ! python3 -c "import ensurepip" >/dev/null 2>&1 && command -v apt-get >/dev/null 2>&1; then
    py_minor="$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')"
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "python${py_minor}-venv" \
      || sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-venv
  fi
  python3 -m venv "$VENV_DIR"
fi

# pip>=26.1.2 vor dem Install erzwingen: schliesst den pip-CVE-Batch (#202,
# Path-Traversal/Symlink/Modul-Hijacking) auch in der Web-Session – pip ist das
# Installationswerkzeug selbst und laesst sich daher nicht ueber constraints.txt
# anheben. Gleiche Mindestversion wie in den CI-Workflows (tests/test_ci_pip_pin.py).
# In der venv ohne `--ignore-installed`: Das RECORD-lose Debian-pip aus #553
# liegt im System-Interpreter, nicht hier.
"$VENV_PY" -m pip install -q --upgrade "pip>=26.1.2"

# Projekt inkl. Test-/Lint-Werkzeuge (pytest, pytest-qt, ruff, mypy).
# Idempotent; -e nutzt den Container-Cache bei Folge-Sessions. Mit dem
# Constraints-Pinning des Projekts wie in Makefile/CI (#205/#206: haelt
# u. a. urllib3/idna auf den gepatchten Releases) – sonst loest pip im
# Web-Container frei auf und kann verwundbare Versionen einspielen.
# Eine vorhandene nicht-editable Kopie (z. B. aus `make pr-check`) wird
# dabei von pip durch den editierbaren Link ersetzt.
#
# `bgremover.egg-info` in der Repo-Wurzel ist im PEP-660-Pfad (pip 26 +
# setuptools, Metadaten in site-packages) nur das setuptools-Nebenprodukt
# des editierbaren Baus; ein erfolgreicher Bau schreibt es ohnehin neu. Was
# ein **abgebrochener** Lauf davon anlegt, wird wieder aufgeräumt (#1048):
# Es ist Unrat im Arbeitsbaum, und aus `python -c` in der Repo-Wurzel sähe
# es wie eine installierte Distribution aus. Aufgeräumt wird aber nur, was
# vor dem Install noch nicht da war: Für eine Legacy-editable-Installation
# ist genau dieses Verzeichnis die Metadatenquelle, und die darf ein
# fehlgeschlagener Neuinstall nicht mitnehmen (Review PR #1049).
egg_info="$PROJECT_DIR/bgremover.egg-info"
egg_info_existed=0
[ -e "$egg_info" ] && egg_info_existed=1
if ! "$VENV_PY" -m pip install -q --constraint requirements/constraints.txt -e ".[test]"; then
  [ "$egg_info_existed" = 0 ] && rm -rf "$egg_info"
  echo "SessionStart-Hook: FEHLGESCHLAGEN – pip install -e \".[test]\" in $VENV_DIR ist abgebrochen; siehe pip-Ausgabe oberhalb." >&2
  exit 1
fi

# Postcondition (#1031), hart: Nach dem Install muss jede Distribution
# `bgremover` ein editierbarer Link auf diesen Checkout sein und der Import
# aus einem neutralen Arbeitsverzeichnis `bgremover/` dieses Checkouts
# treffen. Scheitert das, würde die Session fremden Code messen – der Hook
# bricht dann laut ab (set -e + Trap), statt still fortzufahren.
"$VENV_PY" "$PROVENANCE_CHECK"

persist_session_env
echo "SessionStart-Hook: Umgebung bereit (.venv mit ruff/mypy/pytest lauffähig, bgremover editable auf diesen Checkout)."
