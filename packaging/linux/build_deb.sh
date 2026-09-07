#!/usr/bin/env bash
#
# Build a .deb that installs the self-contained AppImage system-wide
# The package ships the AppImage built by build_appimage.sh under /opt and
# adds a desktop launcher + icon + AppStream metadata, so apt users get menu
# integration and clean install/remove without Python packaging complexity.
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

# DEB_ARCH ist die von dpkg/apt verlangte Architekturkennung (Control-Datei);
# PLATFORM_TAG ist der menschenlesbare Teil des Dateinamens, im selben
# OS+Geraet-Vokabular wie build_appimage.sh (#584).
#
# LIBC_MIN ist die glibc-Untergrenze des Pakets (#994). Ohne sie installiert
# apt auf einem zu alten System anstandslos und die App stirbt erst beim Start
# mit "GLIBC_2.xx not found" - genau der Fehler, den der Kommentar in
# requirements/constraints.txt als real beobachtet zitiert.
#
# Massgeblich ist das MAXIMUM ueber alle gebuendelten Binaerwheels, nicht eine
# einzelne Distribution: Die AppImage traegt neben PyQt6-Qt6 auch PyQt6,
# PyQt6_sip und im --ai-Bundle numpy/scipy/onnxruntime/scikit-image (Review
# PR #999). Gemessen am 2026-09-06 ueber alle Pins aus
# requirements/constraints.txt bestimmen PyQt6 UND PyQt6-Qt6 das Maximum
# gemeinsam: beide liefern manylinux_2_34_x86_64 und manylinux_2_39_aarch64.
# Die naechsthoeheren sind numpy, scipy, onnxruntime und pillow mit je 2.27.
# Mehrfach getaggte Wheels zaehlen mit ihrem niedrigsten Tag, weil sie ab dort
# laufen.
#
# Beim Anheben IRGENDEINES gebuendelten Pins neu bestimmen: die manylinux-Tags
# der Wheel-Dateinamen auf PyPI vergleichen und das Maximum je Architektur
# eintragen. tests/test_linux_packaging.py haelt die Literale netzfrei gegen
# beide Qt-Pins; eine Verschiebung durch ein anderes Paket faellt dort NICHT
# auf und braucht diese Handmessung.
#
# armv7l traegt bewusst denselben Wert wie x86_64, ohne eigene Messung: Fuer
# PyQt6/PyQt6-Qt6 gibt es keine armv7l-Wheels, und der Release-Vertrag kennt
# nur x86_64 und arm64 (CLAUDE.md). Der Zweig bleibt fuer selbst gebaute
# Pakete bestehen; die Zahl ist dort ein geerbter Platzhalter, kein Messwert.
case "$(uname -m)" in
  x86_64)  DEB_ARCH=amd64; PLATFORM_TAG="linux-x86_64"; LIBC_MIN="2.34" ;;
  aarch64) DEB_ARCH=arm64; PLATFORM_TAG="linux-raspberrypi-arm64"; LIBC_MIN="2.39" ;;
  armv7l)  DEB_ARCH=armhf; PLATFORM_TAG="linux-raspberrypi-armhf"; LIBC_MIN="2.34" ;;
  *) echo "!! Unsupported architecture: $(uname -m)"; exit 1 ;;
esac

# Der KI-Hinweis im Dateinamen spiegelt die gewrappte AppImage wider, statt
# einen eigenen --ai-Schalter zu pflegen, der von ihr abweichen koennte.
AI_SUFFIX=""
case "$(basename "$APPIMAGE")" in
  *-ai.AppImage) AI_SUFFIX="-ai" ;;
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
Depends: libc6 (>= $LIBC_MIN), libfuse2 | libfuse2t64
Section: graphics
Priority: optional
Homepage: https://github.com/NikolayDA/picture_helper
Description: Background removal and image editing tool
 BgRemover removes image backgrounds and does quick edits: selection tools
 (magic wand, brush, eraser, polygon lasso), transparency and color replace,
 rotate/flip/crop/round corners, and optional AI background removal.
 .
 This package installs the self-contained AppImage under /opt and adds a
 desktop launcher. Needs FUSE to run the bundled AppImage and glibc
 $LIBC_MIN or newer for the bundled Qt.
CONTROL

OUT="$BUILD/deb/${APP_NAME}-${VERSION}-${PLATFORM_TAG}${AI_SUFFIX}.deb"
mkdir -p "$BUILD/deb"
dpkg-deb --build --root-owner-group "$STAGE" "$OUT"
echo ">> Done: $OUT"
