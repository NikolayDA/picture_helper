#!/usr/bin/env bash
#
# Build a .deb that installs the self-contained AppImage system-wide
# (PR 6 — Linux packaging expansion). The package ships the AppImage built by
# build_appimage.sh under /opt and adds a desktop launcher + icon + AppStream
# metadata, so apt users get menu integration and clean install/remove without
# any Python packaging complexity.
#
# Usage:
#   ./packaging/linux/build_appimage.sh          # produce the AppImage first
#   ./packaging/linux/build_deb.sh               # wrap the newest AppImage
#   ./packaging/linux/build_deb.sh path/to.AppImage
#
set -euo pipefail

APP_ID="de.bgremover.app"
APP_NAME="BgRemover"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
BUILD="${BUILD_DIR:-$ROOT/build}"

command -v dpkg-deb >/dev/null || { echo "!! dpkg-deb not found (install dpkg-dev)"; exit 1; }

VERSION="$(sed -nE 's/^version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' "$ROOT/pyproject.toml" | head -1)"

# AppImage: explicit argument, or the newest build_appimage.sh output.
APPIMAGE="${1:-$(ls -1t "$BUILD/appimage"/*.AppImage 2>/dev/null | head -1 || true)}"
[ -n "$APPIMAGE" ] && [ -f "$APPIMAGE" ] || {
  echo "!! No AppImage found — run build_appimage.sh first or pass its path."; exit 1; }

case "$(uname -m)" in
  x86_64)  DEB_ARCH=amd64 ;;
  aarch64) DEB_ARCH=arm64 ;;
  armv7l)  DEB_ARCH=armhf ;;
  *) echo "!! Unsupported architecture: $(uname -m)"; exit 1 ;;
esac

echo ">> Packaging $APP_NAME $VERSION ($DEB_ARCH) from $(basename "$APPIMAGE")"
STAGE="$BUILD/deb/stage"
rm -rf "$STAGE"

install -Dm755 "$APPIMAGE" "$STAGE/opt/$APP_NAME/$APP_NAME.AppImage"
install -Dm644 "$ROOT/BgRemover_icon.png" \
  "$STAGE/usr/share/icons/hicolor/512x512/apps/$APP_ID.png"
install -Dm644 "$HERE/$APP_ID.metainfo.xml" \
  "$STAGE/usr/share/metainfo/$APP_ID.metainfo.xml"

# Desktop entry pointing at the installed AppImage (not the pip console script,
# which this package does not provide).
mkdir -p "$STAGE/usr/share/applications"
sed -E \
  -e "s#^Exec=.*#Exec=/opt/$APP_NAME/$APP_NAME.AppImage %F#" \
  -e "s#^TryExec=.*#TryExec=/opt/$APP_NAME/$APP_NAME.AppImage#" \
  "$HERE/$APP_ID.desktop" > "$STAGE/usr/share/applications/$APP_ID.desktop"

INSTALLED_KB="$(du -sk "$STAGE" | cut -f1)"
mkdir -p "$STAGE/DEBIAN"
cat > "$STAGE/DEBIAN/control" <<CONTROL
Package: bgremover
Version: $VERSION
Architecture: $DEB_ARCH
Maintainer: NikolayDA <noreply@github.com>
Installed-Size: $INSTALLED_KB
Depends: libfuse2 | libfuse2t64
Section: graphics
Priority: optional
Homepage: https://github.com/NikolayDA/picture_helper
Description: Background removal and image editing tool
 BgRemover removes image backgrounds and does quick edits: selection tools
 (magic wand, brush, eraser, polygon lasso), transparency and color replace,
 rotate/flip/crop/round corners, and optional AI background removal.
 .
 This package installs the self-contained AppImage under /opt and adds a
 desktop launcher. Needs FUSE to run the bundled AppImage.
CONTROL

OUT="$BUILD/deb/${APP_NAME}-${VERSION}-${DEB_ARCH}.deb"
mkdir -p "$BUILD/deb"
dpkg-deb --build --root-owner-group "$STAGE" "$OUT"
echo ">> Done: $OUT"
