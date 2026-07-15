#!/usr/bin/env bash
#
# Build a self-contained BgRemover macOS app bundle (.app) and wrap it in a
# .dmg — the macOS counterpart to packaging/linux/build_appimage.sh.
#
# Approach: PyInstaller bundles a relocatable CPython together with the
# installed `bgremover` package and its dependencies (PyQt6/Pillow/numpy, and
# with --ai also rembg/onnxruntime) into BgRemover.app — no system Python
# required at run time, just like the Linux AppImage.
#
# Requirements (build host only):
#   - macOS on Apple Silicon (arm64); the produced bundle is arm64-only
#   - python3 + pip and network access (fetches PyInstaller + wheels)
#   - Xcode command line tools provide `iconutil`, `hdiutil`, `codesign`
#
# Signing: the bundle is ad-hoc signed (`codesign -s -`) so Gatekeeper does not
# reject the arm64 app as "damaged". It is NOT Developer-ID signed / notarized
# yet, so on first launch users open it once via right-click -> "Open".
#
# Usage:
#   ./packaging/mac/build_macos.sh            # GUI only (smaller)
#   ./packaging/mac/build_macos.sh --ai       # bundle rembg (large)
set -euo pipefail

APP_ID="de.bgremover.app"
APP_NAME="BgRemover"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
BUILD="${BUILD_DIR:-$ROOT/build/macos}"
CONSTRAINTS_FILE="${PIP_CONSTRAINT:-$ROOT/requirements/constraints.txt}"

[ -f "$CONSTRAINTS_FILE" ] || {
  echo "!! Dependency constraints not found: $CONSTRAINTS_FILE"
  exit 1
}
CONSTRAINTS_DIR="$(cd "$(dirname "$CONSTRAINTS_FILE")" && pwd)"
CONSTRAINTS_FILE="$CONSTRAINTS_DIR/$(basename "$CONSTRAINTS_FILE")"
# PyInstaller and the project install run pip in this script's venv; exporting
# the absolute constraints path pins those resolves to the committed snapshot.
export PIP_CONSTRAINT="$CONSTRAINTS_FILE"

WITH_AI=0
[ "${1:-}" = "--ai" ] && WITH_AI=1

VERSION="$(sed -nE 's/^version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' "$ROOT/pyproject.toml" | head -1)"
ARCH="$(uname -m)"   # arm64 on Apple Silicon
# Gleiches OS+Geraet-Vokabular wie build_appimage.sh/build_deb.sh, damit z. B.
# "arm64" nicht gleichzeitig macOS UND Linux/Raspi meinen kann (#584).
PLATFORM_TAG="macos-${ARCH}"
AI_SUFFIX=""
[ "$WITH_AI" = "1" ] && AI_SUFFIX="-ai"
echo ">> Building ${APP_NAME} ${VERSION} .app/.dmg (arch ${ARCH}, ai=${WITH_AI})"
echo ">> Constraints: $PIP_CONSTRAINT"

command -v python3 >/dev/null || { echo "!! python3 not found"; exit 1; }

# Tooling venv: PyInstaller + the project (installed non-editable so PyInstaller
# bundles a real package copy incl. icons/ package-data), never touching the
# system site-packages.
TOOLENV="$BUILD/toolenv"
rm -rf "$BUILD/dist" "$BUILD/work" "$TOOLENV"
python3 -m venv "$TOOLENV"
# shellcheck disable=SC1091
. "$TOOLENV/bin/activate"
python -m pip install --upgrade pip >/dev/null
python -m pip install --upgrade pyinstaller >/dev/null

# Install the project (non-editable) into the venv; PyInstaller analyses this
# installed copy. With --ai, pull rembg[cpu]/onnxruntime as well.
if [ "$WITH_AI" = "1" ]; then
  ( cd "$ROOT" && python -m pip install ".[ai]" )
else
  ( cd "$ROOT" && python -m pip install "." )
fi

# Build the .icns from the repository PNG (iconutil ships with the Xcode command
# line tools). Without iconutil, hand the PNG straight to PyInstaller.
ICON_PNG="$ROOT/BgRemover_icon.png"
ICNS=""
if [ -f "$ICON_PNG" ] && command -v iconutil >/dev/null 2>&1; then
  ICONSET="$BUILD/AppIcon.iconset"
  rm -rf "$ICONSET"; mkdir -p "$ICONSET"
  python - "$ICON_PNG" "$ICONSET" <<'PYEOF'
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
img = Image.open(src).convert("RGBA")
for px, name in [
    (16, "icon_16x16.png"), (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"), (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"), (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"), (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"), (1024, "icon_512x512@2x.png"),
]:
    img.resize((px, px), Image.LANCZOS).save(f"{dst}/{name}")
PYEOF
  ICNS="$BUILD/AppIcon.icns"
  iconutil -c icns "$ICONSET" -o "$ICNS"
elif [ -f "$ICON_PNG" ]; then
  ICNS="$ICON_PNG"
fi

# Hand version, icon and the AI flag to the PyInstaller spec.
export BGREMOVER_VERSION="$VERSION"
export BGREMOVER_ICON="$ICNS"
export BGREMOVER_WITH_AI="$WITH_AI"

pyinstaller --noconfirm --clean \
  --distpath "$BUILD/dist" --workpath "$BUILD/work" \
  "$HERE/bgremover.spec"

APP="$BUILD/dist/$APP_NAME.app"
[ -d "$APP" ] || { echo "!! PyInstaller produced no $APP_NAME.app"; exit 1; }

# Ad-hoc sign so Gatekeeper does not flag the arm64 bundle as "damaged".
# (Not Developer-ID signed / not notarized yet — users open via right-click.)
if command -v codesign >/dev/null 2>&1; then
  codesign --force --deep --sign - "$APP"
fi

# Wrap the .app into a compressed, read-only .dmg (hdiutil ships with macOS),
# with the usual drag-to-Applications symlink.
DMG="$BUILD/${APP_NAME}-${VERSION}-${PLATFORM_TAG}${AI_SUFFIX}.dmg"
rm -f "$DMG"
STAGE="$BUILD/dmg"
rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE" -ov -format UDZO "$DMG"

deactivate
echo ">> Done: $DMG"
echo "   App id: $APP_ID"
echo "   First launch (unsigned build): right-click the app -> Open."
