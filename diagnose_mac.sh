#!/bin/zsh
# diagnose_mac.sh – sammelt alles, was zum Diagnostizieren eines
# fehlgeschlagenen BgRemover-Starts auf macOS noetig ist.
#
# Aufruf:
#   bash diagnose_mac.sh
#
# Sicher: aendert nichts am System, schreibt nichts ausser auf stdout.
# Output bitte an den Bug-Report anhaengen.

print_header() {
    echo
    echo "========================================="
    echo "  $1"
    echo "========================================="
}

# ── System ─────────────────────────────────────────────────────
print_header "SYSTEM"
uname -a
sw_vers 2>/dev/null
echo "arch: $(uname -m)"
echo "shell: $SHELL  (zsh $(zsh --version 2>&1 | head -1))"
echo "TERM: $TERM"

# ── Python-Kandidaten ──────────────────────────────────────────
print_header "PYTHON-KANDIDATEN"
APP_VENV="$HOME/Library/Application Support/BgRemover/venv/bin/python3"
CANDIDATES=(
    "$APP_VENV"
    "./.venv/bin/python3"
    "./venv/bin/python3"
    /opt/homebrew/bin/python3
    /opt/homebrew/bin/python3.13
    /opt/homebrew/bin/python3.12
    /opt/homebrew/bin/python3.11
    /usr/local/bin/python3
    /usr/bin/python3
)
NATIVE_ARCH="$(uname -m)"
for py in "${CANDIDATES[@]}"; do
    [ -x "$py" ] || continue
    ver="$("$py" -c 'import sys;print("%d.%d.%d"%sys.version_info[:3])' 2>/dev/null || echo "?")"
    arch_ok="?"
    if /usr/bin/arch -"$NATIVE_ARCH" "$py" -c 'pass' >/dev/null 2>&1; then
        arch_ok="ok ($NATIVE_ARCH nativ)"
    else
        arch_ok="kein $NATIVE_ARCH"
    fi
    echo
    echo "→ $py"
    echo "  Python $ver   arch: $arch_ok"
    for mod in PyQt6.QtWidgets PIL numpy bgremover; do
        # Erst Exit-Code (robust gegen Warnings auf stderr); Output
        # nur einholen, wenn der Import wirklich scheitert.
        if /usr/bin/arch -"$NATIVE_ARCH" "$py" -c "import $mod" >/dev/null 2>&1; then
            echo "  ✓ $mod"
        else
            ERR="$(/usr/bin/arch -"$NATIVE_ARCH" "$py" -c "import $mod" 2>&1)"
            LAST="$(printf '%s' "$ERR" | tail -n 1)"
            echo "  ✗ $mod   → $LAST"
        fi
    done
done

# ── App-Bundle ─────────────────────────────────────────────────
print_header "APP-BUNDLE"
for app_dir in \
    "$HOME/Applications/BgRemover.app" \
    "/Applications/BgRemover.app" \
    "$HOME/Desktop/BgRemover.app"; do
    [ -d "$app_dir" ] || continue
    echo
    echo "→ $app_dir"
    launcher="$app_dir/Contents/MacOS/BgRemover"
    if [ -x "$launcher" ]; then
        echo "  Launcher: ok ($(stat -f '%Sm' "$launcher" 2>/dev/null))"
        echo "  PYTHON-Variable im Launcher:"
        grep '^PYTHON=' "$launcher" | head -1 | sed 's/^/    /'
        echo "  Letzte Zeile (Start-Befehl):"
        grep -E '^(if ! "\$\{RUN|"\$PYTHON" -m bgremover)' "$launcher" | head -1 | sed 's/^/    /'
    else
        echo "  ✗ Launcher fehlt: $launcher"
    fi
done

# ── BgRemover.command ──────────────────────────────────────────
print_header "BgRemover.command"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMMAND_FILE="$SCRIPT_DIR/BgRemover.command"
if [ -f "$COMMAND_FILE" ]; then
    echo "Datei: $COMMAND_FILE"
    if grep -q '"$BGREMOVER"' "$COMMAND_FILE"; then
        echo "  ⚠️  ALT (sucht BgRemover.py) – `git pull` ausstehend?"
    elif grep -q '"\${RUN\[@\]}" -m bgremover' "$COMMAND_FILE"; then
        echo "  ✓ aktuell (startet via 'python -m bgremover')"
    else
        echo "  ? unbekannter Stand"
    fi
else
    echo "  fehlt: $COMMAND_FILE"
fi

# ── Versionen pyproject/Repo ───────────────────────────────────
print_header "REPO"
if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    echo "pyproject.toml version: $(grep -E '^version\s*=' "$SCRIPT_DIR/pyproject.toml" | head -1)"
fi
if [ -d "$SCRIPT_DIR/.git" ]; then
    ( cd "$SCRIPT_DIR" && echo "git HEAD: $(git log --oneline -1 2>&1)" )
fi
if [ -d "$SCRIPT_DIR/bgremover" ]; then
    echo "bgremover/ vorhanden:  $(ls "$SCRIPT_DIR/bgremover"/*.py 2>/dev/null | wc -l | tr -d ' ') Module"
else
    echo "  ✗ bgremover/ fehlt im Repo (`git pull` ausstehend?)"
fi

# ── Log ────────────────────────────────────────────────────────
print_header "LOG (letzte 40 Zeilen)"
LOG="$HOME/.bgremover.log"
if [ -f "$LOG" ]; then
    tail -n 40 "$LOG"
else
    echo "kein Log unter $LOG"
fi

echo
echo "========================================="
echo "  ENDE  –  bitte diese Ausgabe komplett mitschicken"
echo "========================================="
