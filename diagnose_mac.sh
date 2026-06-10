#!/bin/zsh
# shellcheck shell=bash
# diagnose_mac.sh – sammelt alles, was zum Diagnostizieren eines
# fehlgeschlagenen BgRemover-Starts auf macOS noetig ist.
#
# Hinweis Linter: zsh-Shebang fuer macOS, aber nur bash-/zsh-kompatible
# Syntax – shell=bash (siehe Direktive oben) erlaubt die Pruefung.
#
# Aufruf:
#   bash diagnose_mac.sh                      # Pfade redaktiert, Log als
#                                             # gefilterte Zusammenfassung
#   bash diagnose_mac.sh --include-raw-logs   # volle Pfade + roher Log-Auszug
#
# Sicher: aendert nichts am System, schreibt nichts ausser auf stdout.
# Standardmaessig werden $HOME-/Nutzerpfade redaktiert und der Log nur als
# gefilterte Fehler-Zusammenfassung ausgegeben (Befund #185) – die Ausgabe
# kann damit bedenkenlos an den Bug-Report angehaengt werden. Die volle
# Diagnose (sensibler, vor dem Teilen selbst pruefen!) liefert
# --include-raw-logs.

usage() {
    echo "Aufruf: bash diagnose_mac.sh [--include-raw-logs]"
    echo "  Standard: \$HOME-/Nutzerpfade redaktiert, Log als gefilterte Zusammenfassung."
    echo "  --include-raw-logs: volle Pfade + rohe letzte 40 Log-Zeilen (sensibler!)."
}

INCLUDE_RAW_LOGS=0
for arg in "$@"; do
    case "$arg" in
        --include-raw-logs) INCLUDE_RAW_LOGS=1 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unbekannte Option: $arg" >&2; usage >&2; exit 2 ;;
    esac
done

# Auf Top-Level ermitteln: in zsh-Funktionen waere $0 der Funktionsname.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

print_header() {
    echo
    echo "========================================="
    echo "  $1"
    echo "========================================="
}

# Redaktion der Standard-Ausgabe: das eigene $HOME wird zu '~', uebrige
# /Users/<name>-Pfade (z. B. aus Log-/Launcher-Zeilen) werden gekuerzt.
# $HOME wird als Literal ersetzt – reale Home-Pfade enthalten keine
# sed-Metazeichen mit Nebenwirkung.
redact_output() {
    sed -E -e "s|$HOME|~|g" -e 's|/Users/[^/[:space:]"]+|/Users/<redacted>|g'
}

# Log-Zeilen: ab dem ersten absoluten Pfad bis zum Zeilenende redaktieren.
# Faengt so auch Pfade mit Leerzeichen ("Application Support", Bildnamen)
# und damit Bild- wie Paketpfade sicher ein (Befund #185).
redact_log_paths() {
    sed -E -e 's|^/.*$|<pfad redaktiert>|' \
           -e 's|([[:space:]"(=])/.*$|\1<pfad redaktiert>|'
}

run_diagnostics() {

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
        # Aus $HOME ausfuehren: sonst zeigt Pythons sys.path[0]=cwd-
        # Injection ein `bgremover/`-Quellverzeichnis im aktuellen
        # Ordner faelschlich als „installiert" – genau so, wie der
        # App-Launcher (anderer cwd) es eben NICHT sieht.
        if ( cd "$HOME" && /usr/bin/arch -"$NATIVE_ARCH" "$py" -c "import $mod" ) >/dev/null 2>&1; then
            echo "  ✓ $mod"
        else
            ERR="$( ( cd "$HOME" && /usr/bin/arch -"$NATIVE_ARCH" "$py" -c "import $mod" ) 2>&1)"
            LAST="$(printf '%s' "$ERR" | tail -n 1)"
            echo "  ✗ $mod   → $LAST"
        fi
    done
    # Echter Smoke-Test: QApplication-Erzeugung. `import PyQt6.QtWidgets`
    # alleine zeigt nicht, ob Qt zur Laufzeit das `cocoa`-Plugin findet
    # (typischer venv-Fehler: "Could not find the Qt platform plugin
    # 'cocoa' in ''").
    if QAOUT="$( ( cd "$HOME" && /usr/bin/arch -"$NATIVE_ARCH" "$py" -c \
        'from PyQt6.QtWidgets import QApplication; import sys; QApplication(sys.argv); print("ok")' ) 2>&1)"; then
        if printf '%s' "$QAOUT" | grep -q '^ok$'; then
            echo "  ✓ QApplication-Erzeugung (Qt-Plugin gefunden)"
        else
            LAST="$(printf '%s' "$QAOUT" | tail -n 1)"
            echo "  ✗ QApplication unerwarteter Output: $LAST"
        fi
    else
        LAST="$(printf '%s' "$QAOUT" | tail -n 1)"
        echo "  ✗ QApplication-Erzeugung scheitert → $LAST"
        # Plugin-Pfad mitschicken (haeufige Ursache: Suche in '')
        PLUGIN_PATH="$("$py" -c 'import PyQt6, os; print(os.path.join(os.path.dirname(PyQt6.__file__), "Qt6", "plugins", "platforms"))' 2>/dev/null)"
        if [ -n "$PLUGIN_PATH" ]; then
            echo "    erwarteter Plugin-Pfad: $PLUGIN_PATH"
            if [ -f "$PLUGIN_PATH/libqcocoa.dylib" ]; then
                echo "    → libqcocoa.dylib vorhanden ($(/usr/bin/file "$PLUGIN_PATH/libqcocoa.dylib" 2>/dev/null | head -1))"
            else
                echo "    ✗ libqcocoa.dylib FEHLT in $PLUGIN_PATH"
            fi
        fi
    fi
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
        # shellcheck disable=SC2016  # Literal-Pattern, $-Expansion bewusst aus.
        grep -E '^(if ! "\$\{RUN|"\$PYTHON" -m bgremover)' "$launcher" | head -1 | sed 's/^/    /'
    else
        echo "  ✗ Launcher fehlt: $launcher"
    fi
done

# ── BgRemover.command ──────────────────────────────────────────
print_header "BgRemover.command"
COMMAND_FILE="$SCRIPT_DIR/BgRemover.command"
if [ -f "$COMMAND_FILE" ]; then
    echo "Datei: $COMMAND_FILE"
    # SC2016: Literal-Pattern, $-Expansion in der grep-Suche bewusst aus.
    # shellcheck disable=SC2016
    {
        if grep -q '"$BGREMOVER"' "$COMMAND_FILE"; then
            echo '  ⚠️  ALT (sucht BgRemover.py) – `git pull` ausstehend?'
        elif grep -q '"\${RUN\[@\]}" -m bgremover' "$COMMAND_FILE"; then
            echo "  ✓ aktuell (startet via 'python -m bgremover')"
        else
            echo "  ? unbekannter Stand"
        fi
    }
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
    py_count="$(find "$SCRIPT_DIR/bgremover" -maxdepth 1 -name '*.py' 2>/dev/null | wc -l | tr -d ' ')"
    echo "bgremover/ vorhanden:  ${py_count} Module"
else
    # shellcheck disable=SC2016  # Backticks sind Anzeigetext, nicht Substitution.
    echo '  ✗ bgremover/ fehlt im Repo (`git pull` ausstehend?)'
fi

# ── bgremover in der App-venv WIRKLICH installiert? ─────────────
# `pip show` ist cwd-unabhaengig und sagt eindeutig, ob (und wohin)
# das Paket installiert ist – im Gegensatz zu `import bgremover`, das
# ein Quellverzeichnis im cwd faelschlich „findet".
print_header "bgremover-INSTALLATION (App-venv, cwd-neutral)"
if [ -x "$APP_VENV" ]; then
    SHOW="$( ( cd "$HOME" && "$APP_VENV" -m pip show bgremover ) 2>&1)"
    if printf '%s' "$SHOW" | grep -q '^Name: bgremover'; then
        printf '%s\n' "$SHOW" | grep -E '^(Name|Version|Location|Editable project location):'
    else
        echo "  ✗ bgremover ist in der App-venv NICHT via pip installiert"
        echo "    → create_BgRemover_app.sh muss es nachinstallieren"
    fi
else
    echo "  App-venv-Python fehlt: $APP_VENV"
fi

# ── Log ────────────────────────────────────────────────────────
print_header "LOG"
# Der interne Logger schreibt nach QStandardPaths AppDataLocation; auf
# macOS ist das ~/Library/Application Support/BgRemover/bgremover.log.
# Aeltere Builds nutzten ~/.bgremover.log – als Fallback mitpruefen.
LOG_PRIMARY="$HOME/Library/Application Support/BgRemover/bgremover.log"
LOG_FALLBACK="$HOME/.bgremover.log"
if [ -f "$LOG_PRIMARY" ]; then
    LOG="$LOG_PRIMARY"
else
    LOG="$LOG_FALLBACK"
fi
if [ -f "$LOG" ]; then
    echo "Log: $LOG"
    if [ "$INCLUDE_RAW_LOGS" -eq 1 ]; then
        echo "(roher Auszug – letzte 40 Zeilen)"
        tail -n 40 "$LOG"
    else
        # Statt des rohen Tails (kann Bild-/Nutzerpfade aus Fehlermeldungen
        # enthalten) nur Fehler/Warnungen mit redaktierten Pfaden zeigen.
        total="$(wc -l < "$LOG" | tr -d '[:space:]')"
        echo "(gefilterte Zusammenfassung: Fehler/Warnungen der letzten 200 von ${total} Zeilen,"
        echo " Pfade redaktiert – voller Auszug: bash diagnose_mac.sh --include-raw-logs)"
        SUMMARY="$(tail -n 200 "$LOG" | grep -E 'CRITICAL|ERROR|WARNING|Traceback' \
            | tail -n 15 | redact_log_paths)"
        if [ -n "$SUMMARY" ]; then
            printf '%s\n' "$SUMMARY"
        else
            echo "keine Fehler/Warnungen in den letzten 200 Log-Zeilen"
        fi
    fi
else
    echo "kein Log gefunden unter:"
    echo "  $LOG_PRIMARY"
    echo "  $LOG_FALLBACK"
fi

echo
echo "========================================="
if [ "$INCLUDE_RAW_LOGS" -eq 1 ]; then
    echo "  ENDE  –  ⚠️  Ausgabe enthaelt UNREDAKTIERTE Pfade und Log-Zeilen:"
    echo "  vor dem Teilen selbst pruefen."
else
    echo "  ENDE  –  bitte diese Ausgabe komplett mitschicken"
    echo "  (Pfade redaktiert, Log nur als Zusammenfassung)"
fi
echo "========================================="

}

if [ "$INCLUDE_RAW_LOGS" -eq 1 ]; then
    run_diagnostics
else
    run_diagnostics | redact_output
fi
