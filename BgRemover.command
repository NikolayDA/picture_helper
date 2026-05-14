#!/bin/zsh
# BgRemover – Doppelklick-Starter
# Dieses Script öffnet BgRemover direkt aus dem Finder.

# Terminal-Fenster nach dem Start automatisch schließen
# (die App läuft danach eigenständig weiter)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BGREMOVER="$SCRIPT_DIR/BgRemover.py"

if [ ! -f "$BGREMOVER" ]; then
    echo "❌ BgRemover.py nicht gefunden in: $SCRIPT_DIR"
    echo "   Bitte BgRemover.py und BgRemover.command im selben Ordner lassen."
    read "?Enter zum Schließen drücken..."
    exit 1
fi

# Python suchen (alle üblichen macOS-Orte)
PYTHON=""
for py in \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    /usr/bin/python3 \
    python3; do
    if command -v "$py" &>/dev/null || [ -x "$py" ]; then
        PYTHON="$(command -v "$py" 2>/dev/null || echo "$py")"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌ Python 3 nicht gefunden."
    read "?Enter zum Schließen drücken..."
    exit 1
fi

echo "🎨 BgRemover startet..."
echo "   Python: $PYTHON"
echo "   Script: $BGREMOVER"
echo ""

# App starten – Terminal bleibt offen solange die App läuft
"$PYTHON" "$BGREMOVER"

# Terminal-Tab nach dem Beenden der App schließen
exit 0
