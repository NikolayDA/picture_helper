"""macOS packaging smoke checks.

Validates the PyInstaller spec, the ``.dmg`` build script and the release
workflow's macOS leg. All checks are text-based and need no external tooling
(``pyinstaller``/``iconutil``/``hdiutil`` are not assumed to be installed), so
they run in the normal PR CI. Everything stays in sync with ``pyproject.toml``
(app id, version source, the arm64 target, AI bundling and the ``.dmg`` name).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "packaging" / "mac"
APP_ID = "de.bgremover.app"

BUILD_SH = PKG / "build_macos.sh"
SPEC = PKG / "bgremover.spec"
LAUNCHER = PKG / "bgremover_launcher.py"
README = PKG / "README.md"
WORKFLOW = ROOT / ".github" / "workflows" / "release-linux.yml"

_PYPROJECT = (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def _pyproject_version() -> str:
    m = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', _PYPROJECT)
    assert m, "version not found in pyproject.toml"
    return m.group(1)


def test_packaging_files_exist() -> None:
    for path in (BUILD_SH, SPEC, LAUNCHER, README):
        assert path.exists(), f"missing macOS packaging file: {path}"


# ── Build script ───────────────────────────────────────────────────────

def test_build_script_is_executable_and_sane() -> None:
    assert os.access(BUILD_SH, os.X_OK), "build script must be executable"
    txt = BUILD_SH.read_text(encoding="utf-8")
    assert txt.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in txt
    assert "pyinstaller" in txt
    assert APP_ID in txt
    assert "hdiutil" in txt
    # Ad-hoc signing so Gatekeeper does not flag the arm64 bundle as "damaged".
    assert "codesign" in txt


def test_build_script_names_dmg_with_version_and_arch() -> None:
    txt = BUILD_SH.read_text(encoding="utf-8")
    assert 'ARCH="$(uname -m)"' in txt
    assert 'DMG="$BUILD/${APP_NAME}-${VERSION}-${ARCH}.dmg"' in txt


def test_build_script_reads_version_and_constraints() -> None:
    txt = BUILD_SH.read_text(encoding="utf-8")
    assert "pyproject.toml" in txt
    assert "PIP_CONSTRAINT" in txt
    assert "requirements/constraints.txt" in txt


# ── PyInstaller spec ───────────────────────────────────────────────────

def test_spec_builds_arm64_app_bundle() -> None:
    txt = SPEC.read_text(encoding="utf-8")
    assert "BUNDLE(" in txt
    assert 'name="BgRemover.app"' in txt
    assert f'bundle_identifier="{APP_ID}"' in txt
    # arm64-only target (Apple Silicon).
    assert 'target_arch="arm64"' in txt


def test_spec_collects_package_data_and_version() -> None:
    txt = SPEC.read_text(encoding="utf-8")
    assert 'collect_data_files("bgremover")' in txt
    # Version flows from the build script through the environment.
    assert "BGREMOVER_VERSION" in txt


def test_spec_bundles_package_metadata_for_version_lookup() -> None:
    """Das Bundle muss die ``*.dist-info``-Metadaten mitnehmen.

    ``import bgremover`` liest ``__version__`` über
    ``importlib.metadata.version("bgremover")``. Ohne eingebackene Metadaten
    scheitert das im eingefrorenen Bundle mit ``PackageNotFoundError`` – und
    da dort keine ``pyproject.toml`` als Fallback liegt, brach früher der
    komplette Start der macOS-.dmg-App ab.
    """
    txt = SPEC.read_text(encoding="utf-8")
    assert "copy_metadata" in txt
    assert 'copy_metadata("bgremover")' in txt


def test_spec_bundles_ai_backend() -> None:
    txt = SPEC.read_text(encoding="utf-8")
    assert "collect_all" in txt
    assert "rembg" in txt
    assert "onnxruntime" in txt


def test_spec_document_types_cover_supported_formats() -> None:
    """Die macOS-``CFBundleTypeExtensions`` des Bundles entsprechen genau den
    tatsächlich unterstützten Formaten – konsistent zum Ladepfad und zum
    ``create_BgRemover_app.sh``-Bundle (Befund #249, AC #10).
    """
    from bgremover.constants import _ALLOWED_IMAGE_FORMATS

    txt = SPEC.read_text(encoding="utf-8")
    block = re.search(r"CFBundleTypeExtensions.*?\[(.*?)\]", txt, re.S)
    assert block, "CFBundleTypeExtensions block not found in spec"
    declared = set(re.findall(r'"([^"]+)"', block.group(1)))

    fmt_to_exts = {
        "PNG": {"png"}, "JPEG": {"jpg", "jpeg"}, "WEBP": {"webp"},
        "TIFF": {"tiff"}, "BMP": {"bmp"}, "GIF": {"gif"},
    }
    expected = set().union(*(fmt_to_exts[fmt] for fmt in _ALLOWED_IMAGE_FORMATS))
    assert declared == expected


# ── Launcher ───────────────────────────────────────────────────────────

def test_launcher_calls_app_main() -> None:
    txt = LAUNCHER.read_text(encoding="utf-8")
    assert "from bgremover.app import main" in txt
    assert "main()" in txt


# ── Release workflow (macOS leg) ───────────────────────────────────────

def test_release_workflow_builds_macos_dmg() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    # A native Apple Silicon runner produces the .dmg via the build script.
    assert "os: macos" in text
    assert re.search(r"runner:\s*macos-\S*", text), "needs a native macOS runner"
    assert "arch: arm64" in text
    assert "build_macos.sh" in text
    # Publish gathers and verifies the .dmg alongside the Linux artifacts.
    assert "dist/*.dmg" in text
