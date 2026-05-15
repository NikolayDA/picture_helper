#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  create_BgRemover_app.sh  v3.1
#  Erstellt BgRemover.app + setzt Icon auf BgRemover.command
#  Ausführen: bash ~/Downloads/create_BgRemover_app.sh
#
#  v3: wählt nur ein Python mit installiertem PyQt6 (oder legt
#      bei Bedarf eine venv an) und der App-Launcher zeigt Fehler
#      sichtbar als Dialog statt lautlos zu scheitern.
# ══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BGREMOVER_PY="$SCRIPT_DIR/BgRemover.py"
ICON_PNG="$SCRIPT_DIR/BgRemover_icon.png"
COMMAND_FILE="$SCRIPT_DIR/BgRemover.command"
APP_NAME="BgRemover"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'

echo ""
echo -e "${BLUE}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${BLUE}${BOLD}  BgRemover.app – Setup v3.1${NC}"
echo -e "${BLUE}${BOLD}══════════════════════════════════════════${NC}"
echo ""

# ── Python finden ─────────────────────────────────────────────
# Wichtig: Die App ist eine PyQt6-GUI. Sie startet NUR, wenn das
# eingebackene Python auch "import PyQt6" kann. Wir bevorzugen
# daher einen Interpreter, in dem die Abhängigkeiten wirklich
# installiert sind (inkl. projekteigener venv) – und legen sonst
# eine venv an, statt eine garantiert kaputte App zu erzeugen.
export PATH="/opt/homebrew/bin:/opt/homebrew/opt/python@3.13/bin:/opt/homebrew/opt/python@3.12/bin:/opt/homebrew/opt/python@3.11/bin:/opt/homebrew/opt/python@3.10/bin:/usr/local/bin:/usr/local/opt/python@3.12/bin:/usr/local/opt/python@3.11/bin:$HOME/.pyenv/shims:$HOME/Library/Python/3.12/bin:$HOME/Library/Python/3.11/bin:$HOME/Library/Python/3.10/bin:/Library/Frameworks/Python.framework/Versions/3.12/bin:/Library/Frameworks/Python.framework/Versions/3.11/bin:/usr/bin:$PATH"

py_version_ok() {
    local ver major minor
    ver=$("$1" -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null) || return 1
    major=${ver%%.*}; minor=${ver#*.}
    [ "${major:-0}" -ge 3 ] && [ "${minor:-0}" -ge 9 ]
}
# PYTHONNOUSERSITE: ~/Library/Python/* (user-site) ignorieren. Dort
# liegende Pakete sind oft arch-inkompatibel (Apple Silicon: arm64 vs
# x86_64) und bringen sonst die App zum Absturz. Wir wollen Pakete im
# venv/Interpreter selbst – nicht im fragilen user-site.
has_deps() { PYTHONNOUSERSITE=1 "$1" -c 'import PyQt6.QtWidgets, PIL, numpy' >/dev/null 2>&1; }

# Die venv liegt bewusst NICHT im Projektordner: Liegt das Projekt in
# ~/Documents, ~/Desktop, ~/Downloads oder iCloud, blockiert macOS
# (TCC) den Zugriff einer aus dem Finder gestarteten .app. Application
# Support ist nicht geschützt und überlebt ein Verschieben des Projekts.
APPSUPPORT_DIR="$HOME/Library/Application Support/BgRemover"
VENV_DIR="$APPSUPPORT_DIR/venv"
VENV_PY="$VENV_DIR/bin/python3"

PY_CANDIDATES=(
    "$VENV_PY"
    "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/venv/bin/python3"
    python3.13 python3.12 python3.11 python3.10 python3.9 python3 python
    /opt/homebrew/bin/python3 /opt/homebrew/bin/python3.13
    /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11
    /opt/homebrew/bin/python3.10 /opt/homebrew/bin/python3.9
    /usr/local/bin/python3 /usr/bin/python3
    "$HOME/.pyenv/shims/python3"
)

PYTHON=""        # erstes brauchbares Python 3.9+
PYTHON_READY=""  # erstes Python 3.9+ MIT PyQt6/Pillow/numpy
for py in "${PY_CANDIDATES[@]}"; do
    FULL_PATH=$(command -v "$py" 2>/dev/null || echo "$py")
    [ -x "$FULL_PATH" ] || continue
    py_version_ok "$FULL_PATH" || continue
    if [ -z "$PYTHON" ]; then PYTHON="$FULL_PATH"; fi
    if has_deps "$FULL_PATH"; then
        PYTHON_READY="$FULL_PATH"
        break
    fi
done

if [ -n "$PYTHON_READY" ]; then
    PYTHON="$PYTHON_READY"
    ver=$("$PYTHON" -c 'import sys;print("%d.%d"%sys.version_info[:2])')
    echo -e "${GREEN}✅  Python $ver mit PyQt6:${NC} $PYTHON"
else
    if [ -z "$PYTHON" ]; then
        echo -e "${YELLOW}⚠️  Python 3.9+ nicht automatisch gefunden.${NC}"
        read -p "    Python-Pfad angeben (z.B. /opt/homebrew/bin/python3): " USER_PY
        FULL_PATH=$(command -v "$USER_PY" 2>/dev/null || echo "$USER_PY")
        { [ -x "$FULL_PATH" ] && py_version_ok "$FULL_PATH"; } \
            || { echo -e "${RED}❌ Kein nutzbares Python 3.9+.${NC}"; exit 1; }
        PYTHON="$FULL_PATH"
    fi

    echo -e "${YELLOW}⚠️  PyQt6 ist in keinem gefundenen Python installiert.${NC}"
    echo -e "    Genau deshalb startet die App nicht (lautloser Import-Fehler)."
    echo ""
    echo "    Empfohlen: eine isolierte venv anlegen unter"
    echo "    $VENV_DIR"
    echo "    und dort die Abhängigkeiten installieren. Die venv ignoriert"
    echo "    das fragile ~/Library/Python (genau dort entsteht z.B. der"
    echo "    numpy-Architekturfehler arm64 vs x86_64)."
    read -p "    venv anlegen & installieren? [J/n]: " mkvenv
    if [[ "$mkvenv" =~ ^[nN] ]]; then
        echo -e "${RED}❌ Ohne venv kann keine lauffähige App erstellt werden.${NC}"
        echo "   Bitte erneut ausführen und die venv anlegen lassen –"
        echo "   ggf. vorab nativen Python installieren:  brew install python"
        exit 1
    fi
    echo "🐍 Erstelle venv in $VENV_DIR …"
    mkdir -p "$APPSUPPORT_DIR"
    rm -rf "$VENV_DIR"
    "$PYTHON" -m venv "$VENV_DIR" \
        || { echo -e "${RED}❌ venv konnte nicht erstellt werden.${NC}"; exit 1; }
    echo "📦 Installiere Abhängigkeiten … (kann einige Minuten dauern)"
    "$VENV_PY" -m pip install --upgrade pip >/dev/null 2>&1 || true
    if ( cd "$SCRIPT_DIR" && "$VENV_PY" -m pip install -e ".[ai]" ); then
        PYTHON="$VENV_PY"
        echo -e "${GREEN}✅  venv bereit (inkl. KI):${NC} $PYTHON"
    elif ( cd "$SCRIPT_DIR" && "$VENV_PY" -m pip install -e "." ); then
        PYTHON="$VENV_PY"
        echo -e "${YELLOW}✅  venv bereit (ohne KI – rembg-Install schlug fehl):${NC} $PYTHON"
    else
        echo -e "${RED}❌ Installation fehlgeschlagen.${NC}"
        echo "   Manuell:  \"$PYTHON\" -m venv \"$VENV_DIR\""
        echo "             cd \"$SCRIPT_DIR\" && \"$VENV_PY\" -m pip install -e \".[ai]\""
        exit 1
    fi
fi

# Letzter Sicherheitscheck: kann das gewählte Python die Pakete
# wirklich importieren? Fängt z.B. arm64/x86_64-Mismatch ab, BEVOR
# eine garantiert kaputte App ausgeliefert wird.
if ! IMPERR=$(PYTHONNOUSERSITE=1 "$PYTHON" -c 'import PyQt6.QtWidgets, PIL, numpy' 2>&1); then
    echo -e "${RED}❌ $PYTHON kann PyQt6/Pillow/numpy nicht importieren:${NC}"
    echo "$IMPERR" | tail -n 1
    echo "   Häufige Ursache: Architektur-Mismatch auf Apple Silicon"
    echo "   (x86_64 vs arm64). Abhilfe: nativen Python installieren und"
    echo "   das Skript erneut ausführen:  brew install python"
    exit 1
fi

# ── Dateien prüfen ────────────────────────────────────────────
[ -f "$BGREMOVER_PY" ] || { echo -e "${RED}❌ BgRemover.py nicht gefunden.${NC}"; exit 1; }
echo -e "${GREEN}✅  BgRemover.py gefunden${NC}"

case "$SCRIPT_DIR/" in
    "$HOME/Documents/"*|"$HOME/Desktop/"*|"$HOME/Downloads/"*|"$HOME/Library/Mobile Documents/"*)
        echo -e "${YELLOW}ℹ️  Projekt liegt in einem macOS-geschützten Ordner.${NC}"
        echo "    Kein Problem: die App wird in sich geschlossen gebaut"
        echo "    (BgRemover.py wird ins Bundle kopiert, venv liegt in"
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
read -p "Auswahl [1/2/3] (Enter = 1): " choice
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

# BgRemover.py IN das Bundle kopieren. Damit ist die App in sich
# geschlossen: sie liest beim Start nicht mehr aus dem Projektordner
# (der in ~/Documents etc. von macOS gesperrt sein oder verschoben/
# gelöscht werden kann), sondern aus dem eigenen Bundle.
BUNDLED_BGREMOVER="$APP_PATH/Contents/Resources/BgRemover.py"
cp "$BGREMOVER_PY" "$BUNDLED_BGREMOVER"

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
BGREMOVER="$BUNDLED_BGREMOVER"
LOG="\$HOME/.bgremover.log"

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
if [ ! -f "\$BGREMOVER" ]; then
    fail "BgRemover.py fehlt im App-Bundle:"\$'\\n'"\$BGREMOVER"\$'\\n\\n'"Das Bundle ist unvollständig. Bitte create_BgRemover_app.sh erneut ausführen."
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

{ echo "--- \$(date '+%Y-%m-%d %H:%M:%S') BgRemover-Start ---"
  echo "Python: \$PYTHON  (arch \$NATIVE_ARCH)"; } >> "\$LOG" 2>&1

if ! "\${RUN[@]}" "\$BGREMOVER" "\$@" >> "\$LOG" 2>&1; then
    LASTERR=\$(grep -E 'Error|Exception|Traceback' "\$LOG" 2>/dev/null | tail -n 1)
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
    <key>CFBundleVersion</key>           <string>3.0.0</string>
    <key>CFBundleShortVersionString</key><string>3.0</string>
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

# ── Icon auch auf BgRemover.command setzen ────────────────────
if [ -f "$COMMAND_FILE" ] && [ -f "$ICON_PNG" ]; then
    echo ""
    echo "🎨 Setze Icon auf BgRemover.command …"
    "$PYTHON" - "$ICON_PNG" "$COMMAND_FILE" << 'PYEOF'
import sys, os
icon_path = os.path.abspath(sys.argv[1])
target    = os.path.abspath(sys.argv[2])
try:
    from AppKit import NSWorkspace, NSImage
    icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
    ok   = NSWorkspace.sharedWorkspace().setIcon_forFile_options_(icon, target, 0)
    print("  ✅ Dock-Icon gesetzt" if ok else "  ⚠️  Icon konnte nicht gesetzt werden")
except Exception as e:
    print(f"  ⚠️  AppKit nicht verfügbar ({e}) – Icon muss manuell gesetzt werden")
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

read -p "App jetzt starten? [j/N]: " run_now
[[ "$run_now" =~ ^[jJyY] ]] && open "$APP_PATH"
