# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Spec für das selbst-enthaltene macOS-App-Bundle (BgRemover.app).

Wird von ``packaging/mac/build_macos.sh`` aufgerufen. Version, Icon und das
KI-Flag kommen über Umgebungsvariablen (``BGREMOVER_VERSION``/``-ICON``/
``-WITH_AI``), die das Build-Skript setzt – analog zum python-appimage-Rezept
unter ``packaging/linux``. Das Bundle ist arm64-only (Apple Silicon).
"""
import os

from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_submodules,
)

_VERSION = os.environ.get("BGREMOVER_VERSION", "0.0.0")
_ICON = os.environ.get("BGREMOVER_ICON") or None
_WITH_AI = os.environ.get("BGREMOVER_WITH_AI") == "1"

# Einstiegsskript liegt neben dieser Spec. ``SPEC`` injiziert PyInstaller.
_HERE = os.path.dirname(os.path.abspath(SPEC))  # noqa: F821 (PyInstaller-Global)

# bgremover-Paketdaten (icons/*.png) und alle Submodule mitnehmen: das Paket
# lädt Icons über importlib.resources und nutzt vereinzelt dynamische Importe,
# die die statische Analyse sonst übersehen würde.
datas = collect_data_files("bgremover")
binaries = []
hiddenimports = collect_submodules("bgremover")

# Optionale KI-Hintergrundentfernung: rembg/onnxruntime bringen dynamische
# Bibliotheken und Datendateien mit, die PyInstaller nur über collect_all
# zuverlässig findet.
if _WITH_AI:
    for _pkg in ("rembg", "onnxruntime"):
        _d, _b, _h = collect_all(_pkg)
        datas += _d
        binaries += _b
        hiddenimports += _h

block_cipher = None

a = Analysis(
    [os.path.join(_HERE, "bgremover_launcher.py")],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BgRemover",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    # Finder-„Öffnen mit"/Doppelklick verarbeitet die App selbst über Qts
    # QFileOpenEvent (#249); argv_emulation würde dieses Event abfangen.
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
    icon=_ICON,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="BgRemover",
)
app = BUNDLE(
    coll,
    name="BgRemover.app",
    icon=_ICON,
    bundle_identifier="de.bgremover.app",
    version=_VERSION,
    info_plist={
        "CFBundleName": "BgRemover",
        "CFBundleDisplayName": "BgRemover",
        "CFBundleShortVersionString": _VERSION,
        "CFBundleVersion": _VERSION,
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": False,
        "LSMinimumSystemVersion": "11.0",
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeName": "Bilddatei",
                "CFBundleTypeRole": "Editor",
                "CFBundleTypeExtensions": [
                    "png", "jpg", "jpeg", "webp", "bmp", "tiff", "gif",
                ],
            }
        ],
    },
)
