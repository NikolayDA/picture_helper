#!/bin/zsh
# BgRemover – Doppelklick-Starter
# Dieses Script öffnet BgRemover direkt aus dem Finder (Terminalfenster).

# user-site (~/Library/Python/*) ausblenden: dort liegende Pakete sind
# oft arch-fremd (Apple Silicon: arm64 vs x86_64) und brachten BgRemover
# bisher mit einem numpy-ImportError zum Absturz.
export PYTHONNOUSERSITE=1

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BGREMOVER="$SCRIPT_DIR/BgRemover.py"

if [ ! -f "$BGREMOVER" ]; then
    echo "❌ BgRemover.py nicht gefunden in: $SCRIPT_DIR"
    echo "   Bitte BgRemover.py und BgRemover.command im selben Ordner lassen."
    read "?Enter zum Schließen drücken..."
    exit 1
fi

# Bevorzugt die vom App-Setup angelegte venv (saubere, arch-passende
# Pakete) – erst danach System-/Homebrew-Python.
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
    PYTHON="$CAND"
    break
done

if [ -z "$PYTHON" ]; then
    echo "❌ Python 3 nicht gefunden."
    read "?Enter zum Schließen drücken..."
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
echo "   Script: $BGREMOVER"
echo ""

if ! "${RUN[@]}" "$BGREMOVER"; then
    echo ""
    echo "❌ BgRemover ist mit einem Fehler beendet worden (siehe oben)."
    echo "   Häufige Ursache: PyQt6/numpy fehlen oder arch-Mismatch."
    echo "   Fix: einmal  bash create_BgRemover_app.sh  ausführen und die"
    echo "        venv anlegen lassen (ggf. vorher: brew install python)."
    read "?Enter zum Schließen drücken..."
    exit 1
fi

exit 0
