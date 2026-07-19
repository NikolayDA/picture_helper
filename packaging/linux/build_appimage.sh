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
CONSTRAINTS_FILE="${PIP_CONSTRAINT:-$ROOT/requirements/constraints.txt}"

[ -f "$CONSTRAINTS_FILE" ] || {
  echo "!! Dependency constraints not found: $CONSTRAINTS_FILE"
  exit 1
}
CONSTRAINTS_DIR="$(cd "$(dirname "$CONSTRAINTS_FILE")" && pwd)"
CONSTRAINTS_FILE="$CONSTRAINTS_DIR/$(basename "$CONSTRAINTS_FILE")"
# python-appimage installs the recipe with pip in a subprocess. Exporting the
# absolute path constrains that resolver as well as this script's own pip calls.
export PIP_CONSTRAINT="$CONSTRAINTS_FILE"

WITH_AI=0
[ "${1:-}" = "--ai" ] && WITH_AI=1

VERSION="$(sed -nE 's/^version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' "$ROOT/pyproject.toml" | head -1)"
ARCH="$(uname -m)"
# Plattform-Tag fuer den Artefaktnamen: OS + Geraet statt der rohen
# uname-Architektur, sonst laesst sich z. B. "arm64" nicht von der
# gleichnamigen macOS-.dmg unterscheiden (#584).
case "$ARCH" in
  x86_64)  PLATFORM_TAG="linux-x86_64" ;;
  aarch64) PLATFORM_TAG="linux-raspberrypi-arm64" ;;
  *)       PLATFORM_TAG="linux-${ARCH}" ;;
esac
AI_SUFFIX=""
[ "$WITH_AI" = "1" ] && AI_SUFFIX="-ai"
echo ">> Building ${APP_NAME} ${VERSION} AppImage (python ${PYVER}, arch ${ARCH}, ai=${WITH_AI})"
echo ">> Constraints: $PIP_CONSTRAINT"

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
# The desktop file feeds icon/name/mimetype desktop-integration metadata
# only; strip the field codes (%F/%U), python-appimage doesn't need them.
sed -E 's/[[:space:]]*%[fFuU]//g' "$HERE/$APP_ID.desktop" > "$RECIPE/$APP_ID.desktop"
cp "$ROOT/BgRemover_icon.png" "$RECIPE/$APP_ID.png"

# python-appimage's AppRun invocation is generated from a recipe/entrypoint.*
# file (see python_appimage/commands/build/app.py: it globs `entrypoint.*`,
# and only rewrites AppDir/AppRun if found). Without one, the base image's
# generic AppRun (a bare passthrough to the interpreter) stays in place and
# running the AppImage with no arguments starts an *interactive* Python REPL
# instead of the app (found via manual Raspberry Pi testing, #595). Run the
# console-script entry point through `-m bgremover` rather than the
# `bgremover` wrapper script directly, since that wrapper's shebang is an
# absolute build-time path and isn't relocatable.
cat > "$RECIPE/entrypoint.sh" <<'EOF'
#! /bin/bash
exec "{{ python-executable }}" -m bgremover "$@"
EOF

# 3) Bundle everything into a single AppImage.
( cd "$BUILD" && python-appimage build app -p "$PYVER" "$RECIPE" )

OUT="$(ls -1t "$BUILD"/*.AppImage 2>/dev/null | head -1 || true)"
[ -n "$OUT" ] || { echo "!! python-appimage produced no .AppImage"; exit 1; }
FINAL="$BUILD/${APP_NAME}-${VERSION}-${PLATFORM_TAG}${AI_SUFFIX}.AppImage"
mv -f "$OUT" "$FINAL"
chmod +x "$FINAL"

deactivate
echo ">> Done: $FINAL"
echo "   Run it with:  \"$FINAL\"   (or add --appimage-extract-and-run without FUSE)"
