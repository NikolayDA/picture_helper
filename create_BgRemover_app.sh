#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  create_BgRemover_app.sh  v3.3
#  Erstellt BgRemover.app + setzt Icon auf BgRemover.command
#  Ausführen: bash ~/Downloads/create_BgRemover_app.sh
#
#  v3: wählt nur ein Python mit installiertem PyQt6 (oder legt
#      bei Bedarf eine venv an) und der App-Launcher zeigt Fehler
#      sichtbar als Dialog statt lautlos zu scheitern.
#  v3.3: pyobjc-framework-Cocoa wird best-effort in die venv
#        installiert, damit das Icon zuverlässig auf .app UND
#        .command gesetzt wird; Python 3.14/3.15 werden erkannt.
# ══════════════════════════════════════════════════════════════

set -e

# user-site (~/Library/Python/*) global ausblenden: dort liegende
# Pakete sind oft arch-fremd (Apple Silicon) und verfälschen Erkennung
# wie Laufzeit. Alle Kind-Pythons erben das.
export PYTHONNOUSERSITE=1

# Native CPU-Architektur. venv/pip MÜSSEN in derselben Arch laufen wie
# später der Launcher (der ebenfalls nativ startet), sonst arm64/x86_64-
# Mismatch unter Rosetta.
NATIVE_ARCH="$(uname -m 2>/dev/null || echo)"
arch_run() {
    if [ -n "$NATIVE_ARCH" ] && /usr/bin/arch -"$NATIVE_ARCH" "$1" -c 'pass' >/dev/null 2>&1; then
        /usr/bin/arch -"$NATIVE_ARCH" "$@"
    else
        "$@"
    fi
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# BgRemover ist als Paket (`bgremover/`) installiert; die App wird ueber
# `python -m bgremover` gestartet.
CONSTRAINTS_FILE="$SCRIPT_DIR/requirements/constraints.txt"
ICON_PNG="$SCRIPT_DIR/BgRemover_icon.png"
COMMAND_FILE="$SCRIPT_DIR/BgRemover.command"
APP_NAME="BgRemover"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'

echo ""
echo -e "${BLUE}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${BLUE}${BOLD}  BgRemover.app – Setup v3.3${NC}"
echo -e "${BLUE}${BOLD}══════════════════════════════════════════${NC}"
echo ""

# ── Python finden ─────────────────────────────────────────────
# Wichtig: Die App ist eine PyQt6-GUI. Sie startet NUR, wenn das
# eingebackene Python auch "import PyQt6" kann. Wir bevorzugen
# daher einen Interpreter, in dem die Abhängigkeiten wirklich
# installiert sind (inkl. projekteigener venv) – und legen sonst
# eine venv an, statt eine garantiert kaputte App zu erzeugen.
export PATH="/opt/homebrew/bin:/opt/homebrew/opt/python@3.15/bin:/opt/homebrew/opt/python@3.14/bin:/opt/homebrew/opt/python@3.13/bin:/opt/homebrew/opt/python@3.12/bin:/opt/homebrew/opt/python@3.11/bin:/opt/homebrew/opt/python@3.10/bin:/usr/local/bin:/usr/local/opt/python@3.14/bin:/usr/local/opt/python@3.12/bin:/usr/local/opt/python@3.11/bin:$HOME/.pyenv/shims:$HOME/Library/Python/3.12/bin:$HOME/Library/Python/3.11/bin:$HOME/Library/Python/3.10/bin:/Library/Frameworks/Python.framework/Versions/3.12/bin:/Library/Frameworks/Python.framework/Versions/3.11/bin:/usr/bin:$PATH"

py_version_ok() {
    local ver major minor
    ver=$("$1" -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null) || return 1
    major=${ver%%.*}; minor=${ver#*.}
    [ "${major:-0}" -ge 3 ] && [ "${minor:-0}" -ge 10 ]
}
# Prüft in nativer Arch + ohne user-site, ob die Pakete wirklich
# importierbar sind – also genau so, wie der Launcher später startet.
# Inklusive `bgremover`: eine venv aus der Monolith-Aera (in der nur
# PyQt6/Pillow/numpy installiert war) galt sonst als "ready", und der
# Re-Install des Pakets wurde stillschweigend uebersprungen.
#
# WICHTIG: aus `$HOME` aufrufen (subshell `cd $HOME`), damit Pythons
# automatische sys.path[0]=cwd-Injection NICHT das `bgremover/`-Quell-
# verzeichnis im Repo als „installiertes Paket" durchgehen laesst. Der
# Bundle-Launcher startet mit anderem cwd; er wuerde sonst „bgremover
# fehlt" melden, obwohl das Setup gesagt hat „ist da".
has_deps() { ( cd "$HOME" && arch_run "$1" -c 'import PyQt6.QtWidgets, PIL, numpy, bgremover' >/dev/null 2>&1 ); }

pip_install_project() {
    local py="$1"
    shift
    if [ -f "$CONSTRAINTS_FILE" ]; then
        arch_run "$py" -m pip install --constraint "$CONSTRAINTS_FILE" "$@"
    else
        arch_run "$py" -m pip install "$@"
    fi
}

install_app_project() {
    local success_label="$1"
    if ( cd "$SCRIPT_DIR" && pip_install_project "$VENV_PY" ".[ai]" ); then
        PYTHON="$VENV_PY"
        echo -e "${GREEN}✅  $success_label (inkl. KI):${NC} $PYTHON"
    elif ( cd "$SCRIPT_DIR" && pip_install_project "$VENV_PY" "." ); then
        PYTHON="$VENV_PY"
        echo -e "${YELLOW}✅  $success_label (ohne KI – rembg-Install schlug fehl):${NC} $PYTHON"
    else
        return 1
    fi
}

# Die venv liegt bewusst NICHT im Projektordner: Liegt das Projekt in
# ~/Documents, ~/Desktop, ~/Downloads oder iCloud, blockiert macOS
# (TCC) den Zugriff einer aus dem Finder gestarteten .app. Application
# Support ist nicht geschützt und überlebt ein Verschieben des Projekts.
APPSUPPORT_DIR="$HOME/Library/Application Support/BgRemover"
VENV_DIR="$APPSUPPORT_DIR/venv"
VENV_PY="$VENV_DIR/bin/python3"

PY_CANDIDATES=(
    "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/venv/bin/python3"
    python3.15 python3.14 python3.13 python3.12 python3.11 python3.10 python3 python
    /opt/homebrew/bin/python3 /opt/homebrew/bin/python3.15
    /opt/homebrew/bin/python3.14 /opt/homebrew/bin/python3.13
    /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11
    /opt/homebrew/bin/python3.10
    /usr/local/bin/python3 /usr/bin/python3
    "$HOME/.pyenv/shims/python3"
)

APP_VENV_READY=""
if [ -x "$VENV_PY" ] && py_version_ok "$VENV_PY" && has_deps "$VENV_PY"; then
    APP_VENV_READY=1
fi

# Basis-Python nur zum Erzeugen einer neuen dedizierten App-venv. Ein
# bereits eingerichtetes Projekt-/System-Python wird nie direkt in den
# Launcher eingebrannt: sonst wäre die .app wieder vom Projektpfad oder
# von einer zufälligen lokalen Umgebung abhängig.
PYTHON=""
for py in "${PY_CANDIDATES[@]}"; do
    FULL_PATH=$(command -v "$py" 2>/dev/null || echo "$py")
    [ -x "$FULL_PATH" ] || continue
    py_version_ok "$FULL_PATH" || continue
    PYTHON="$FULL_PATH"
    break
done

if [ -n "$APP_VENV_READY" ]; then
    # Nicht-editierbar aus dem aktuellen Checkout aktualisieren. Ohne
    # Re-Install würde ein erneuter Build nach git pull/Branch-Wechsel
    # weiterhin die alte Paketkopie aus der App-venv starten.
    echo -e "${YELLOW}🔁  Aktualisiere App-venv aus aktuellem Checkout …${NC}"
    if ! install_app_project "App-venv aktualisiert"; then
        echo -e "${RED}❌ Aktualisierung der App-venv fehlgeschlagen.${NC}"
        exit 1
    fi
elif [ -x "$VENV_PY" ] && py_version_ok "$VENV_PY" \
     && arch_run "$VENV_PY" -c 'import PyQt6.QtWidgets, PIL, numpy' >/dev/null 2>&1; then
    # App-venv existiert mit PyQt6/Pillow/numpy, aber `bgremover` fehlt
    # (typisch fuer einen venv aus der Monolith-Aera, vor dem Paket-
    # Schnitt). Statt die venv komplett neu zu bauen (dauert Minuten,
    # numpy/scipy/onnxruntime usw.), schieben wir nur das bgremover-
    # Paket nach – das dauert Sekunden.
    echo -e "${YELLOW}🔁  App-venv existiert (PyQt6/Pillow/numpy ok), aber bgremover fehlt –${NC}"
    echo "    wird nachinstalliert (statt venv neu zu bauen) …"
    if ! install_app_project "App-venv aktualisiert"; then
        echo -e "${RED}❌ Nachinstallation fehlgeschlagen.${NC}"
        echo "   Manuell:  cd \"$SCRIPT_DIR\" && \"$VENV_PY\" -m pip install --constraint \"$CONSTRAINTS_FILE\" \".[ai]\""
        echo "   Notfalls die alte venv loeschen und neu bauen:"
        echo "             rm -rf \"$VENV_DIR\" && bash create_BgRemover_app.sh"
        exit 1
    fi
else
    if [ -z "$PYTHON" ]; then
        echo -e "${YELLOW}⚠️  Python 3.10+ nicht automatisch gefunden.${NC}"
        read -r -p "    Python-Pfad angeben (z.B. /opt/homebrew/bin/python3): " USER_PY
        FULL_PATH=$(command -v "$USER_PY" 2>/dev/null || echo "$USER_PY")
        { [ -x "$FULL_PATH" ] && py_version_ok "$FULL_PATH"; } \
            || { echo -e "${RED}❌ Kein nutzbares Python 3.10+.${NC}"; exit 1; }
        PYTHON="$FULL_PATH"
    fi

    echo -e "${YELLOW}⚠️  Keine einsatzbereite App-venv gefunden.${NC}"
    echo ""
    echo "    Empfohlen: eine isolierte venv anlegen unter"
    echo "    $VENV_DIR"
    echo "    und dort die Abhängigkeiten installieren. Die venv ignoriert"
    echo "    das fragile ~/Library/Python (genau dort entsteht z.B. der"
    echo "    numpy-Architekturfehler arm64 vs x86_64)."
    read -r -p "    venv anlegen & installieren? [J/n]: " mkvenv
    if [[ "$mkvenv" =~ ^[nN] ]]; then
        echo -e "${RED}❌ Ohne venv kann keine lauffähige App erstellt werden.${NC}"
        echo "   Bitte erneut ausführen und die venv anlegen lassen –"
        echo "   ggf. vorab nativen Python installieren:  brew install python"
        exit 1
    fi
    echo "🐍 Erstelle venv in $VENV_DIR …"
    mkdir -p "$APPSUPPORT_DIR"
    rm -rf "$VENV_DIR"
    arch_run "$PYTHON" -m venv "$VENV_DIR" \
        || { echo -e "${RED}❌ venv konnte nicht erstellt werden.${NC}"; exit 1; }
    echo "📦 Installiere Abhängigkeiten ($NATIVE_ARCH) … (kann einige Minuten dauern)"
    arch_run "$VENV_PY" -m pip install --upgrade pip >/dev/null 2>&1 || true
    # Nicht-editierbar installieren: die venv enthaelt eine eigene Kopie
    # des Pakets (inkl. package-data icons/), damit die App vom Projekt-
    # ordner unabhaengig ist (umbenennen/loeschen bricht sie nicht).
    if ! install_app_project "App-venv bereit"; then
        echo -e "${RED}❌ Installation fehlgeschlagen.${NC}"
        echo "   Manuell:  \"$PYTHON\" -m venv \"$VENV_DIR\""
        echo "             cd \"$SCRIPT_DIR\" && \"$VENV_PY\" -m pip install --constraint \"$CONSTRAINTS_FILE\" \".[ai]\""
        exit 1
    fi
fi

# Letzter Sicherheitscheck: kann das gewählte Python die Pakete
# wirklich importieren? Fängt z.B. arm64/x86_64-Mismatch ab, BEVOR
# eine garantiert kaputte App ausgeliefert wird. `cd $HOME` aus dem
# gleichen Grund wie `has_deps` (Pythons sys.path[0]=cwd-Injection).
if ! IMPERR=$( ( cd "$HOME" && arch_run "$PYTHON" -c 'import PyQt6.QtWidgets, PIL, numpy, bgremover' ) 2>&1); then
    echo -e "${RED}❌ $PYTHON kann PyQt6/Pillow/numpy/bgremover nicht importieren:${NC}"
    echo "$IMPERR" | tail -n 1
    echo "   Häufige Ursache: Architektur-Mismatch auf Apple Silicon"
    echo "   (x86_64 vs arm64) oder Paket nicht installiert. Abhilfe:"
    echo "   nativen Python installieren oder venv neu anlegen:"
    echo "     brew install python && bash create_BgRemover_app.sh"
    exit 1
fi

if ! APP_VERSION=$( ( cd "$HOME" && arch_run "$PYTHON" -c 'import bgremover; print(bgremover.__version__)' ) 2>/dev/null); then
    echo -e "${RED}❌ Paketversion konnte nicht ermittelt werden.${NC}"
    exit 1
fi
[ -n "$APP_VERSION" ] || { echo -e "${RED}❌ Paketversion ist leer.${NC}"; exit 1; }
echo -e "${GREEN}🏷️  App-Version:${NC} $APP_VERSION"

case "$SCRIPT_DIR/" in
    "$HOME/Documents/"*|"$HOME/Desktop/"*|"$HOME/Downloads/"*|"$HOME/Library/Mobile Documents/"*)
        echo -e "${YELLOW}ℹ️  Projekt liegt in einem macOS-geschützten Ordner.${NC}"
        echo "    Kein Problem: die App wird in sich geschlossen gebaut"
        echo "    (venv inkl. installiertem bgremover-Paket liegt in"
        echo "    Application Support) – sie läuft auch von hier aus." ;;
esac

# ── Zielordner ────────────────────────────────────────────────
mkdir -p "$HOME/Applications"
echo ""
echo "Wo soll die App installiert werden?"
echo "  1) ~/Applications  (empfohlen)"
echo "  2) ~/Desktop"
echo "  3) /Applications   (systemweit, braucht Passwort)"
echo ""
read -r -p "Auswahl [1/2/3] (Enter = 1): " choice
case "$choice" in
    2) INSTALL_DIR="$HOME/Desktop" ;;
    3) INSTALL_DIR="/Applications" ;;
    *) INSTALL_DIR="$HOME/Applications" ;;
esac

APP_PATH="$INSTALL_DIR/$APP_NAME.app"
[ -d "$APP_PATH" ] && { echo -e "${YELLOW}⚠️  Alte Version wird ersetzt.${NC}"; rm -rf "$APP_PATH"; }

# ── Bundle anlegen ────────────────────────────────────────────
echo ""
echo "📁 Erstelle App-Bundle …"
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# Der Code liegt nicht im Bundle, sondern als nicht-editierbar installiertes
# Paket in der venv unter Application Support. icons/ ist Paket-Daten und liegt
# in site-packages der venv – das Bundle braucht also keine eigene Kopie.

# ── Launcher ──────────────────────────────────────────────────
LAUNCHER="$APP_PATH/Contents/MacOS/$APP_NAME"
cat > "$LAUNCHER" << LAUNCHER_EOF
#!/bin/zsh
# BgRemover Launcher v4 – sichtbare Fehlerdialoge statt lautlosem Abbruch.
# Eine aus dem Finder gestartete .app hat KEIN Terminal: ohne diese
# Diagnose würde z.B. ein fehlendes PyQt6 spurlos scheitern.
export PATH="/opt/homebrew/bin:/opt/homebrew/opt/python@3.13/bin:/opt/homebrew/opt/python@3.12/bin:/opt/homebrew/opt/python@3.11/bin:/opt/homebrew/opt/python@3.10/bin:/usr/local/bin:/usr/bin:/bin:\$PATH"

# user-site (~/Library/Python/*) ausblenden: dort liegende Pakete sind
# oft arch-inkompatibel (Apple Silicon arm64 vs x86_64) und brachten
# die App bisher mit einem numpy-ImportError zum Absturz.
export PYTHONNOUSERSITE=1

# Login-Profil laden (NICHT das interaktive .zshrc – das kann im
# Finder-/launchd-Kontext hängen oder mit Fehlern abbrechen).
[ -f "\$HOME/.zprofile" ] && source "\$HOME/.zprofile" 2>/dev/null || true

PYTHON="$PYTHON"
LOG="\$HOME/Library/Application Support/BgRemover/bgremover.log"
LOG_DIR="\${LOG%/*}"
mkdir -p "\$LOG_DIR" 2>/dev/null || true

fail() {
    /usr/bin/osascript \\
      -e 'on run argv' \\
      -e 'set b to button returned of (display dialog (item 1 of argv) with title "BgRemover" buttons {"Log öffnen", "OK"} default button "OK" with icon stop)' \\
      -e 'if b is "Log öffnen" then do shell script "open " & quoted form of (item 2 of argv)' \\
      -e 'end run' \\
      "\$1" "\$LOG" >/dev/null 2>&1
    exit 1
}

if [ ! -x "\$PYTHON" ]; then
    fail "Python wurde nicht gefunden:"\$'\\n'"\$PYTHON"\$'\\n\\n'"Bitte create_BgRemover_app.sh erneut ausführen."
fi
# Erst Exit-Code pruefen (robust gegen Warnings auf stderr); nur wenn
# der Import wirklich scheitert, den echten Fehlertext fuer den Dialog
# einholen. Sonst wuerde z.B. ein numpy/onnxruntime-Deprecation-Warning
# beim Start zum falschen "fehlt"-Dialog fuehren, obwohl das Paket
# einwandfrei importierbar ist.
if ! "\$PYTHON" -c 'import bgremover' >/dev/null 2>&1; then
    IMPORT_ERR="\$("\$PYTHON" -c 'import bgremover' 2>&1)"
    if printf '%s' "\$IMPORT_ERR" | grep -qE "No module named '?bgremover'?"; then
        fail "Das bgremover-Paket fehlt in der venv:"\$'\\n'"\$PYTHON"\$'\\n\\n'"Bitte create_BgRemover_app.sh erneut ausführen."
    fi
    LASTLINE="\$(printf '%s' "\$IMPORT_ERR" | tail -n 1)"
    fail "bgremover laesst sich nicht importieren in:"\$'\\n'"\$PYTHON"\$'\\n\\n'"\$LASTLINE"\$'\\n\\n'"Fix: bash diagnose_mac.sh fuer Details ausfuehren, ggf. venv neu bauen."
fi

# Native CPU-Architektur erzwingen: wird die .app via Rosetta
# gestartet, läuft Python sonst als x86_64 und kann arm64-Pakete
# nicht laden. Nur anwenden, wenn dieses Python die native Arch
# wirklich unterstützt, sonst normal starten.
NATIVE_ARCH="\$(/usr/bin/uname -m 2>/dev/null)"
RUN=("\$PYTHON")
if [ -n "\$NATIVE_ARCH" ] && /usr/bin/arch -"\$NATIVE_ARCH" "\$PYTHON" -c 'pass' >/dev/null 2>&1; then
    RUN=(/usr/bin/arch -"\$NATIVE_ARCH" "\$PYTHON")
fi

# Logposition VOR diesem Start merken. Die Fehlersuche unten darf nur
# Zeilen DIESES Laufs sehen – sonst zeigt der Dialog veraltete Fehler
# aus alten, längst behobenen Läufen (z. B. einen früheren
# numpy-ImportError), obwohl der aktuelle Start an etwas anderem
# scheitert (das Log wird nur angehängt, nie gekürzt).
LSTART=\$(wc -l < "\$LOG" 2>/dev/null || echo 0)

{ echo "--- \$(date '+%Y-%m-%d %H:%M:%S') BgRemover-Start ---"
  echo "Python: \$PYTHON  (arch \$NATIVE_ARCH)"; } >> "\$LOG" 2>&1

if ! "\${RUN[@]}" -m bgremover "\$@" >> "\$LOG" 2>&1; then
    LASTERR=\$(tail -n +\$((LSTART + 1)) "\$LOG" 2>/dev/null | grep -E 'Error|Exception|Traceback' | tail -n 1)
    [ -z "\$LASTERR" ] && LASTERR="(siehe Logdatei)"
    fail "BgRemover konnte nicht starten."\$'\\n\\n'"\$LASTERR"\$'\\n\\n'"Fix: create_BgRemover_app.sh erneut ausführen und die venv anlegen lassen (bei arm64/x86_64-Fehlern vorher: brew install python)."
fi
LAUNCHER_EOF
chmod +x "$LAUNCHER"

# ── Info.plist ────────────────────────────────────────────────
cat > "$APP_PATH/Contents/Info.plist" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>              <string>BgRemover</string>
    <key>CFBundleDisplayName</key>       <string>BgRemover</string>
    <key>CFBundleIdentifier</key>        <string>de.bgremover.app</string>
    <key>CFBundleVersion</key>           <string>$APP_VERSION</string>
    <key>CFBundleShortVersionString</key><string>$APP_VERSION</string>
    <key>CFBundlePackageType</key>       <string>APPL</string>
    <key>CFBundleSignature</key>         <string>BGRM</string>
    <key>CFBundleExecutable</key>        <string>BgRemover</string>
    <key>CFBundleIconFile</key>          <string>AppIcon</string>
    <key>NSHighResolutionCapable</key>   <true/>
    <key>NSRequiresAquaSystemAppearance</key><false/>
    <key>CFBundleDocumentTypes</key>
    <array><dict>
        <key>CFBundleTypeName</key>       <string>Bilddatei</string>
        <key>CFBundleTypeRole</key>       <string>Editor</string>
        <key>CFBundleTypeExtensions</key>
        <array>
            <string>png</string><string>jpg</string><string>jpeg</string>
            <string>webp</string><string>bmp</string><string>tiff</string><string>gif</string>
        </array>
    </dict></array>
</dict>
</plist>
PLIST_EOF

# ── .icns Icon erstellen ──────────────────────────────────────
ICNS_PATH="$APP_PATH/Contents/Resources/AppIcon.icns"

if [ -f "$ICON_PNG" ]; then
    echo "🎨 Erstelle .icns Icon …"
    ICONSET_TMP="$(mktemp -d)"
    # Sicherer Cleanup: nur das von mktemp angelegte Verzeichnis löschen,
    # auch wenn das Skript vorzeitig abbricht.
    trap 'rm -rf "$ICONSET_TMP"' EXIT
    ICONSET_DIR="$ICONSET_TMP/AppIcon.iconset"
    mkdir -p "$ICONSET_DIR"

    "$PYTHON" - "$ICON_PNG" "$ICONSET_DIR" << 'PYEOF'
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
img = Image.open(src).convert("RGBA")
for px, name in [
    (16,"icon_16x16.png"),(32,"icon_16x16@2x.png"),
    (32,"icon_32x32.png"),(64,"icon_32x32@2x.png"),
    (128,"icon_128x128.png"),(256,"icon_128x128@2x.png"),
    (256,"icon_256x256.png"),(512,"icon_256x256@2x.png"),
    (512,"icon_512x512.png"),(1024,"icon_512x512@2x.png"),
]:
    img.resize((px,px), Image.LANCZOS).save(f"{dst}/{name}")
print("  PNG-Varianten erstellt")
PYEOF

    if command -v iconutil &>/dev/null; then
        iconutil -c icns "$ICONSET_DIR" -o "$ICNS_PATH"
        echo -e "${GREEN}  ✅ AppIcon.icns erstellt${NC}"
    else
        cp "$ICON_PNG" "$APP_PATH/Contents/Resources/AppIcon.png"
        echo -e "${YELLOW}  ⚠️ iconutil fehlt – PNG als Fallback${NC}"
    fi
    # Cleanup übernimmt das oben gesetzte trap
else
    echo -e "${YELLOW}  ⚠️ BgRemover_icon.png nicht gefunden – kein Icon${NC}"
fi

# ── Quarantäne entfernen ──────────────────────────────────────
xattr -rd com.apple.quarantine "$APP_PATH" 2>/dev/null || true

# ── Icon auf BgRemover.app (und optional BgRemover.command) setzen ──
# setIcon:forFile: braucht PyObjC/AppKit. Das wird best-effort in die
# EIGENE venv nachgezogen (kein Laufzeit-Dependency der App, daher nicht
# in pyproject.toml). In eine fremde System-/Homebrew-Python wird bewusst
# NICHT installiert (PEP 668 externally-managed) – dort bleibt es beim
# Hinweis unten. Das .app-Icon ist über AppIcon.icns ohnehin gesetzt;
# dieser Schritt sorgt für sofortiges Anzeigen ohne Cache-Refresh.
if [ -f "$ICON_PNG" ]; then
    if ! arch_run "$PYTHON" -c 'import AppKit' >/dev/null 2>&1 \
       && [ "$PYTHON" = "$VENV_PY" ]; then
        echo "📦 Installiere pyobjc-framework-Cocoa (für Icon-Setzen) …"
        arch_run "$VENV_PY" -m pip install --quiet pyobjc-framework-Cocoa \
            >/dev/null 2>&1 || true
    fi

    ICON_TARGETS=("$APP_PATH")
    ICON_LABEL="BgRemover.app"
    if [ -f "$COMMAND_FILE" ]; then
        ICON_TARGETS+=("$COMMAND_FILE")
        ICON_LABEL="$ICON_LABEL, BgRemover.command"
    fi

    echo ""
    echo "🎨 Setze Icon ($ICON_LABEL) …"
    "$PYTHON" - "$ICON_PNG" "${ICON_TARGETS[@]}" << 'PYEOF' || true
import os, sys
icon_path = os.path.abspath(sys.argv[1])
targets   = [os.path.abspath(t) for t in sys.argv[2:]]
try:
    from AppKit import NSWorkspace, NSImage
    icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
    ws   = NSWorkspace.sharedWorkspace()
    done = []
    for t in targets:
        if ws.setIcon_forFile_options_(icon, t, 0):
            done.append(os.path.basename(t))
        else:
            print(f"  ⚠️  Icon konnte nicht gesetzt werden: {os.path.basename(t)}")
    if done:
        print("  ✅ Icon gesetzt: " + ", ".join(done))
except Exception as e:
    print(f"  ℹ️  PyObjC/AppKit nicht verfügbar ({e}).")
    print("     Das .app-Icon ist bereits über AppIcon.icns gesetzt – betroffen")
    print("     ist nur die optionale Datei BgRemover.command. Manuell setzen:")
    print("     BgRemover_icon.png im Finder öffnen, ⌘C; dann BgRemover.command")
    print("     auswählen, ⌘I (Informationen), Icon oben links anklicken, ⌘V.")
PYEOF
fi

# Finder-Datenbank aktualisieren
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
    -f "$APP_PATH" 2>/dev/null || true

echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✅  BgRemover.app fertig!${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo ""
echo -e "  Pfad: ${BOLD}$APP_PATH${NC}"
echo ""
echo "  Nächste Schritte:"
echo "  1. Im Finder auf BgRemover.app doppelklicken"
echo "  2. Oder Dock-Icon: open \"$INSTALL_DIR\" → App in Dock ziehen"
echo ""

read -r -p "App jetzt starten? [j/N]: " run_now
[[ "$run_now" =~ ^[jJyY] ]] && open "$APP_PATH"
