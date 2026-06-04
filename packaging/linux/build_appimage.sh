#!/usr/bin/env bash
#
# Build a portable BgRemover AppImage.
#
# Approach: python-appimage bundles a relocatable manylinux CPython together
# with the installed `bgremover` wheel and its dependencies (PyQt6/Pillow/numpy)
# into a single self-contained *.AppImage — no system Python required at run
# time, analogous to the macOS .app bundle.
#
# Requirements (build host only):
#   - Linux x86_64 or aarch64 (build on the same arch you target, e.g. a
#     Raspberry Pi for the Pi build)
#   - python3 + pip, and network access (fetches python-appimage + wheels)
#   - FUSE is NOT needed to build, only to *run* the result (or run with
#     `--appimage-extract-and-run`)
#
# Usage:
#   ./packaging/linux/build_appimage.sh            # GUI only (smaller)
#   ./packaging/linux/build_appimage.sh --ai       # bundle rembg (large)
#   PYVER=3.12 ./packaging/linux/build_appimage.sh # pick the bundled Python
#
set -euo pipefail

APP_ID="de.bgremover.app"
APP_NAME="BgRemover"
PYVER="${PYVER:-3.12}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
BUILD="${BUILD_DIR:-$ROOT/build/appimage}"
RECIPE="$BUILD/recipe"

WITH_AI=0
[ "${1:-}" = "--ai" ] && WITH_AI=1

VERSION="$(sed -nE 's/^version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' "$ROOT/pyproject.toml" | head -1)"
ARCH="$(uname -m)"
echo ">> Building ${APP_NAME} ${VERSION} AppImage (python ${PYVER}, arch ${ARCH}, ai=${WITH_AI})"

command -v python3 >/dev/null || { echo "!! python3 not found"; exit 1; }

# Tooling: python-appimage (bundler) + build (wheel builder), in an isolated venv
# so we never touch the system site-packages.
TOOLENV="$BUILD/toolenv"
python3 -m venv "$TOOLENV"
# shellcheck disable=SC1091
. "$TOOLENV/bin/activate"
python -m pip install --upgrade pip >/dev/null
python -m pip install --upgrade build python-appimage >/dev/null

# 1) Build the bgremover wheel from the repo.
rm -rf "$BUILD/dist"
python -m build --wheel --outdir "$BUILD/dist" "$ROOT"
WHEEL="$(ls -1 "$BUILD/dist"/bgremover-*.whl | head -1)"
echo ">> Wheel: $WHEEL"

# 2) Assemble the python-appimage recipe directory.
rm -rf "$RECIPE"; mkdir -p "$RECIPE"
if [ "$WITH_AI" = "1" ]; then
  printf '%s[ai]\n' "$WHEEL" > "$RECIPE/requirements.txt"
else
  printf '%s\n' "$WHEEL" > "$RECIPE/requirements.txt"
fi
# python-appimage derives the entry point from the desktop Exec; strip the
# field codes (%F/%U) so only the `bgremover` console script remains.
sed -E 's/[[:space:]]*%[fFuU]//g' "$HERE/$APP_ID.desktop" > "$RECIPE/$APP_ID.desktop"
cp "$ROOT/BgRemover_icon.png" "$RECIPE/$APP_ID.png"

# 3) Bundle everything into a single AppImage.
( cd "$BUILD" && python-appimage build app -p "$PYVER" "$RECIPE" )

OUT="$(ls -1t "$BUILD"/*.AppImage 2>/dev/null | head -1 || true)"
[ -n "$OUT" ] || { echo "!! python-appimage produced no .AppImage"; exit 1; }
FINAL="$BUILD/${APP_NAME}-${VERSION}-${ARCH}.AppImage"
mv -f "$OUT" "$FINAL"
chmod +x "$FINAL"

deactivate
echo ">> Done: $FINAL"
echo "   Run it with:  \"$FINAL\"   (or add --appimage-extract-and-run without FUSE)"
