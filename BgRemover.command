#!/bin/zsh
# shellcheck shell=bash
# BgRemover – Doppelklick-Starter
# Dieses Script öffnet BgRemover direkt aus dem Finder (Terminalfenster).
# BgRemover ist als Paket (`bgremover/`) installiert; das Script startet
# das Programm via `python3 -m bgremover`.
#
# Hinweis Linter: Wir laufen unter zsh (macOS-Default), nutzen aber nur
# Syntax, die in bash und zsh identisch funktioniert – daher shell=bash
# (siehe Direktive oben), damit das Skript geprueft werden kann.

# user-site (~/Library/Python/*) ausblenden: dort liegende Pakete sind
# oft arch-fremd (Apple Silicon: arm64 vs x86_64) und brachten BgRemover
# bisher mit einem numpy-ImportError zum Absturz.
export PYTHONNOUSERSITE=1

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Bevorzugt die vom App-Setup angelegte venv (saubere, arch-passende
# Pakete inkl. installiertem bgremover-Paket) – erst danach Projekt-venv,
# dann System-/Homebrew-Python (dort ist `bgremover` typisch NICHT
# installiert; wir prüfen das gleich explizit).
PYTHON=""
for py in \
    "$HOME/Library/Application Support/BgRemover/venv/bin/python3" \
    "$SCRIPT_DIR/.venv/bin/python3" \
    "$SCRIPT_DIR/venv/bin/python3" \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    /usr/bin/python3 \
    python3; do
    CAND="$(command -v "$py" 2>/dev/null || echo "$py")"
    [ -x "$CAND" ] || continue
    # Erstes Python nehmen, in dem `import bgremover` funktioniert
    # (sonst startet `python3 -m bgremover` mit „No module named bgremover").
    if "$CAND" -c 'import bgremover' >/dev/null 2>&1; then
        PYTHON="$CAND"
        break
    fi
    # Fallback merken (erstes existierendes Python überhaupt) – wird
    # unten nur für die Fehlermeldung benutzt.
    [ -z "$PYTHON" ] && PYTHON="$CAND"
done

if [ -z "$PYTHON" ]; then
    echo "❌ Python 3 nicht gefunden."
    printf 'Enter zum Schließen drücken...'
    read -r _
    exit 1
fi

# Sanity-Check: in dem ausgewählten Python muss das bgremover-Paket
# wirklich importierbar sein – sonst macht ein -m-Start keinen Sinn.
if ! "$PYTHON" -c 'import bgremover' >/dev/null 2>&1; then
    echo "❌ Das bgremover-Paket ist im ausgewählten Python NICHT installiert:"
    echo "   $PYTHON"
    echo ""
    echo "   Fix: einmal  bash create_BgRemover_app.sh  ausführen –"
    echo "   das legt die venv an und installiert das Paket."
    printf 'Enter zum Schließen drücken...'
    read -r _
    exit 1
fi

# Native CPU-Architektur erzwingen: sonst läuft Python unter Rosetta
# evtl. als x86_64 und kann arm64-Pakete nicht laden (und umgekehrt).
NATIVE_ARCH="$(uname -m 2>/dev/null)"
RUN=("$PYTHON")
if [ -n "$NATIVE_ARCH" ] && /usr/bin/arch -"$NATIVE_ARCH" "$PYTHON" -c 'pass' >/dev/null 2>&1; then
    RUN=(/usr/bin/arch -"$NATIVE_ARCH" "$PYTHON")
fi

echo "🎨 BgRemover startet..."
echo "   Python: $PYTHON  (arch $NATIVE_ARCH)"
echo "   Paket:  bgremover  (via python -m)"
echo ""

if ! "${RUN[@]}" -m bgremover; then
    echo ""
    echo "❌ BgRemover ist mit einem Fehler beendet worden (siehe oben)."
    echo "   Häufige Ursache: PyQt6/numpy fehlen oder arch-Mismatch."
    echo "   Fix: einmal  bash create_BgRemover_app.sh  ausführen und die"
    echo "        venv neu anlegen lassen (ggf. vorher: brew install python)."
    printf 'Enter zum Schließen drücken...'
    read -r _
    exit 1
fi

exit 0
