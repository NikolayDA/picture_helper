"""Linux packaging smoke checks (PR 5 — packaging foundation).

Validates the AppImage packaging metadata without any external tooling
(`desktop-file-validate`/`appstreamcli` are not assumed to be installed), so it
runs in the normal PR CI. It keeps the desktop entry, the AppStream metainfo and
the build script self-consistent and in sync with ``pyproject.toml`` (app id,
license, version, the ``bgremover`` entry point).
"""
from __future__ import annotations

import configparser
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "packaging" / "linux"
APP_ID = "de.bgremover.app"

DESKTOP = PKG / f"{APP_ID}.desktop"
METAINFO = PKG / f"{APP_ID}.metainfo.xml"
BUILD_SH = PKG / "build_appimage.sh"
ICON = ROOT / "BgRemover_icon.png"

_PYPROJECT = (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def _pyproject_version() -> str:
    m = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', _PYPROJECT)
    assert m, "version not found in pyproject.toml"
    return m.group(1)


def test_packaging_files_exist() -> None:
    for path in (DESKTOP, METAINFO, BUILD_SH, PKG / "README.md", ICON):
        assert path.exists(), f"missing packaging file: {path}"


# ── Desktop entry ──────────────────────────────────────────────────────

@pytest.fixture
def desktop_entry() -> configparser.SectionProxy:
    # interpolation=None: the Exec line contains %F field codes that would
    # otherwise trip configparser's %-interpolation.
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str  # keep keys case-sensitive (Desktop spec)
    cp.read(DESKTOP, encoding="utf-8")
    assert cp.has_section("Desktop Entry")
    return cp["Desktop Entry"]


def test_desktop_required_keys(desktop_entry) -> None:
    assert desktop_entry["Type"] == "Application"
    assert desktop_entry["Name"] == "BgRemover"
    assert desktop_entry["Icon"] == APP_ID
    assert desktop_entry["Terminal"] == "false"
    assert desktop_entry.get("TryExec") == "bgremover"


def test_desktop_exec_uses_entry_point(desktop_entry) -> None:
    # First token must be the console script defined in [project.scripts].
    assert desktop_entry["Exec"].split()[0] == "bgremover"


def test_desktop_categories_valid(desktop_entry) -> None:
    cats = desktop_entry["Categories"]
    assert cats.endswith(";"), "Categories must be ';'-terminated"
    values = [c for c in cats.split(";") if c]
    # Exactly one registered freedesktop main category is required.
    assert "Graphics" in values


def test_desktop_mimetypes_match_supported_formats(desktop_entry) -> None:
    mimes = desktop_entry["MimeType"]
    for expected in ("image/png", "image/jpeg", "image/webp"):
        assert expected in mimes


# ── AppStream metainfo ─────────────────────────────────────────────────

@pytest.fixture
def metainfo_root() -> ET.Element:
    # ET.parse raises on malformed XML → this also covers well-formedness.
    return ET.parse(METAINFO).getroot()


def _text(root: ET.Element, path: str) -> str | None:
    el = root.find(path)
    return el.text.strip() if el is not None and el.text else None


def test_metainfo_is_desktop_application(metainfo_root) -> None:
    assert metainfo_root.tag == "component"
    assert metainfo_root.get("type") == "desktop-application"


def test_metainfo_required_fields(metainfo_root) -> None:
    assert _text(metainfo_root, "id") == APP_ID
    assert _text(metainfo_root, "name") == "BgRemover"
    assert _text(metainfo_root, "summary")
    assert _text(metainfo_root, "metadata_license")
    assert _text(metainfo_root, "project_license") == "GPL-3.0-or-later"
    assert metainfo_root.find("description") is not None
    # Developer name in either the modern or the legacy form.
    dev = _text(metainfo_root, "developer/name") or _text(metainfo_root, "developer_name")
    assert dev and "NikolayDA" in dev


def test_metainfo_launchable_matches_desktop(metainfo_root) -> None:
    launch = metainfo_root.find("launchable")
    assert launch is not None and launch.get("type") == "desktop-id"
    assert (launch.text or "").strip() == DESKTOP.name


def test_metainfo_provides_entry_point(metainfo_root) -> None:
    assert _text(metainfo_root, "provides/binary") == "bgremover"


def test_metainfo_release_matches_pyproject_version(metainfo_root) -> None:
    rel = metainfo_root.find("releases/release")
    assert rel is not None, "metainfo needs at least one <release>"
    assert rel.get("version") == _pyproject_version()


# ── Cross-file + project consistency ───────────────────────────────────

def test_app_id_consistent_everywhere(desktop_entry, metainfo_root) -> None:
    # desktop filename, icon name, metainfo id all identical.
    assert DESKTOP.stem == APP_ID
    assert METAINFO.name == f"{APP_ID}.metainfo.xml"
    assert desktop_entry["Icon"] == APP_ID
    assert _text(metainfo_root, "id") == APP_ID


def test_pyproject_declares_entry_point_and_license() -> None:
    assert re.search(r'(?m)^\s*bgremover\s*=\s*"bgremover\.app:main"', _PYPROJECT)
    assert re.search(r'(?m)^\s*license\s*=\s*"GPL-3\.0-or-later"', _PYPROJECT)


def test_icon_is_png() -> None:
    assert ICON.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_app_sets_desktop_file_name() -> None:
    # The running app must associate its window with the .desktop id.
    src = (ROOT / "bgremover" / "app.py").read_text(encoding="utf-8")
    assert f'setDesktopFileName("{APP_ID}")' in src


# ── Build script ───────────────────────────────────────────────────────

def test_build_script_is_executable_and_sane() -> None:
    assert os.access(BUILD_SH, os.X_OK), "build script must be executable"
    txt = BUILD_SH.read_text(encoding="utf-8")
    assert txt.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in txt
    assert "python-appimage" in txt
    assert APP_ID in txt
