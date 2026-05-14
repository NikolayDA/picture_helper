#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  create_BgRemover_app.sh  v2.0
#  Erstellt BgRemover.app + setzt Icon auf BgRemover.command
#  Ausführen: bash ~/Downloads/create_BgRemover_app.sh
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
echo -e "${BLUE}${BOLD}  BgRemover.app – Setup v2.0${NC}"
echo -e "${BLUE}${BOLD}══════════════════════════════════════════${NC}"
echo ""

# ── Python finden ─────────────────────────────────────────────
export PATH="/opt/homebrew/bin:/opt/homebrew/opt/python@3.13/bin:/opt/homebrew/opt/python@3.12/bin:/opt/homebrew/opt/python@3.11/bin:/opt/homebrew/opt/python@3.10/bin:/usr/local/bin:/usr/local/opt/python@3.12/bin:/usr/local/opt/python@3.11/bin:$HOME/.pyenv/shims:$HOME/Library/Python/3.12/bin:$HOME/Library/Python/3.11/bin:$HOME/Library/Python/3.10/bin:/Library/Frameworks/Python.framework/Versions/3.12/bin:/Library/Frameworks/Python.framework/Versions/3.11/bin:/usr/bin:$PATH"

PY_CANDIDATES=(
    python3.13 python3.12 python3.11 python3.10 python3.9 python3 python
    /opt/homebrew/bin/python3 /opt/homebrew/bin/python3.13
    /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11
    /opt/homebrew/bin/python3.10 /opt/homebrew/bin/python3.9
    /usr/local/bin/python3 /usr/bin/python3
    "$HOME/.pyenv/shims/python3"
)

PYTHON=""
for py in "${PY_CANDIDATES[@]}"; do
    FULL_PATH=$(command -v "$py" 2>/dev/null || echo "$py")
    [ -x "$FULL_PATH" ] || continue
    ver=$("$FULL_PATH" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
    major=${ver%%.*}; minor=${ver#*.}; minor=${minor%%.*}
    if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
        PYTHON="$FULL_PATH"
        echo -e "${GREEN}✅  Python $ver:${NC} $PYTHON"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${YELLOW}⚠️  Python 3.9+ nicht automatisch gefunden.${NC}"
    read -p "    Python-Pfad angeben (z.B. /usr/bin/python3): " USER_PY
    FULL_PATH=$(command -v "$USER_PY" 2>/dev/null || echo "$USER_PY")
    [ -x "$FULL_PATH" ] || { echo -e "${RED}❌ Nicht ausführbar.${NC}"; exit 1; }
    PYTHON="$FULL_PATH"
fi

# ── Dateien prüfen ────────────────────────────────────────────
[ -f "$BGREMOVER_PY" ] || { echo -e "${RED}❌ BgRemover.py nicht gefunden.${NC}"; exit 1; }
echo -e "${GREEN}✅  BgRemover.py gefunden${NC}"

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

# ── Launcher (sourct Shell-Profile → Python wird gefunden) ────
LAUNCHER="$APP_PATH/Contents/MacOS/$APP_NAME"
cat > "$LAUNCHER" << LAUNCHER_EOF
#!/bin/zsh
# BgRemover Launcher v2 – lädt Nutzer-Umgebung bevor Python gestartet wird
export PATH="/opt/homebrew/bin:/opt/homebrew/opt/python@3.13/bin:/opt/homebrew/opt/python@3.12/bin:/opt/homebrew/opt/python@3.11/bin:/opt/homebrew/opt/python@3.10/bin:/usr/local/bin:/usr/bin:\$PATH"

[ -f "\$HOME/.zprofile" ]     && source "\$HOME/.zprofile"     2>/dev/null || true
[ -f "\$HOME/.zshrc" ]        && source "\$HOME/.zshrc"        2>/dev/null || true
[ -f "\$HOME/.bash_profile" ] && source "\$HOME/.bash_profile" 2>/dev/null || true

PYTHON="$PYTHON"
BGREMOVER="$BGREMOVER_PY"

exec "\$PYTHON" "\$BGREMOVER" "\$@"
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
    <key>CFBundleVersion</key>           <string>2.0.0</string>
    <key>CFBundleShortVersionString</key><string>2.0</string>
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
    ICONSET_DIR="$(mktemp -d)/AppIcon.iconset"
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
    rm -rf "$(dirname "$ICONSET_DIR")"
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
