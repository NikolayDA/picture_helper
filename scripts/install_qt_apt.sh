#!/usr/bin/env bash
# Einzige Quelle der Qt-System-Paketliste (#1036, löst Befund N6 ab).
#
# Bis #1036 stand dieselbe apt-Liste in fünf Workflows und im
# SessionStart-Hook; ein Wächtertest hielt die sechs Kopien gegeneinander.
# Jetzt rufen alle sechs dieses Skript auf, und der Wächter
# (tests/test_ci_qt_packages.py) prüft die Liste hier sowie die Aufrufer
# über eine Negativkontrolle (kein Paketname mehr inline).
#
# Aufruf:  bash scripts/install_qt_apt.sh [--best-effort-update] [ZUSATZPAKET ...]
#
#   --best-effort-update  `apt-get update` darf scheitern (defekte Fremd-PPAs
#                         in manchen Containern); nur der SessionStart-Hook
#                         setzt das. In der CI bleibt `apt-get update`
#                         fail-closed – ein Runner mit kaputten Quellen soll
#                         dort laut auffallen.
#   --print-packages      gibt die Qt-Liste zeilenweise aus und beendet sich
#                         (Wächtertest); berührt apt nicht.
#   ZUSATZPAKET           weitere Pakete derselben Installation (z. B. zsh
#                         und shellcheck für `make lint`).
#
# `apt-get install` scheitert immer hart. `sudo` wird nur vorangestellt, wenn
# der Aufrufer nicht root ist (GitHub-Runner: `runner`; Web-Container: root).
set -euo pipefail

# Auf ubuntu-latest erprobt; fehlt z. B. libgl1, bricht `import PyQt6` nur
# mit „libGL.so.1: cannot open shared object file".
QT_PACKAGES=(
  libegl1 libgl1 libfontconfig1 libxkbcommon0 libdbus-1-3
  libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0
  libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xkb1
)

best_effort_update=0
extras=()
for arg in "$@"; do
  case "$arg" in
    --best-effort-update) best_effort_update=1 ;;
    --print-packages) printf '%s\n' "${QT_PACKAGES[@]}"; exit 0 ;;
    # Hilfe = der Kommentarkopf bis zur ersten Nicht-Kommentarzeile (kein
    # fester Zeilenbereich, der bei jeder Kopfänderung still driftete).
    -h|--help) awk 'NR > 1 && !/^#/ { exit } NR > 1 { sub(/^# ?/, ""); print }' "$0"; exit 0 ;;
    -*) echo "install_qt_apt.sh: unbekannte Option: $arg" >&2; exit 2 ;;
    *) extras+=("$arg") ;;
  esac
done

if ! command -v apt-get >/dev/null 2>&1; then
  echo "install_qt_apt.sh: apt-get nicht gefunden – nur Debian/Ubuntu werden unterstützt." >&2
  exit 1
fi

sudo_prefix=()
if [ "$(id -u)" -ne 0 ]; then
  sudo_prefix=(sudo)
fi

if [ "$best_effort_update" = 1 ]; then
  "${sudo_prefix[@]}" apt-get update \
    || echo "Hinweis: apt-get update teilweise fehlgeschlagen (fremde PPAs) – fahre fort."
else
  "${sudo_prefix[@]}" apt-get update
fi

"${sudo_prefix[@]}" env DEBIAN_FRONTEND=noninteractive \
  apt-get install -y "${QT_PACKAGES[@]}" "${extras[@]}"
