"""Linux packaging smoke checks.

Validates the AppImage/.deb packaging metadata, the build scripts and the
release workflow. The metadata checks need no external tooling
(`desktop-file-validate`/`appstreamcli` are not assumed to be installed), so they
run in the normal PR CI; the end-to-end ``.deb`` build runs only where
``dpkg-deb`` is available. Everything stays in sync with ``pyproject.toml``
(app id, license, version, the ``bgremover`` entry point).
"""
from __future__ import annotations

import configparser
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "packaging" / "linux"
APP_ID = "de.bgremover.app"

DESKTOP = PKG / f"{APP_ID}.desktop"
METAINFO = PKG / f"{APP_ID}.metainfo.xml"
BUILD_SH = PKG / "build_appimage.sh"
BUILD_DEB = PKG / "build_deb.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "release-linux.yml"
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


# Format → MIME-Typ; muss jeden Eintrag aus ``_ALLOWED_IMAGE_FORMATS`` abdecken,
# sonst schlägt der Test mit KeyError fehl und erzwingt die Pflege beim Hinzufügen
# eines neuen Formats.
_FORMAT_TO_MIME = {
    "PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp",
    "TIFF": "image/tiff", "BMP": "image/bmp", "GIF": "image/gif",
}


def test_desktop_mimetypes_exactly_cover_supported_formats(desktop_entry) -> None:
    """Die deklarierten MIME-Typen entsprechen GENAU den tatsächlich
    unterstützten Formaten (Befund #249, AC #10): keine Format-Lücke und kein
    Versprechen für ein nicht ladbares Format. So bleibt die Dateizuordnung mit
    dem validierten Ladepfad konsistent.
    """
    from bgremover.constants import _ALLOWED_IMAGE_FORMATS

    declared = {m for m in desktop_entry["MimeType"].split(";") if m}
    expected = {_FORMAT_TO_MIME[fmt] for fmt in _ALLOWED_IMAGE_FORMATS}
    assert declared == expected


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


def test_icon_is_valid_rgba_master() -> None:
    assert ICON.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    with Image.open(ICON) as icon:
        assert icon.size == (1024, 1024)
        assert icon.mode == "RGBA"
        assert icon.getchannel("A").getextrema() == (0, 255)


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


def test_appimage_names_with_platform_tag_and_ai_suffix() -> None:
    """Dateiname traegt OS+Geraet statt roher Architektur (Befund/#584).

    Ein blosses ``arm64`` waere sowohl fuer den Linux/Raspi- als auch den
    macOS-Build gueltig; ``linux-raspberrypi-arm64`` ist eindeutig. Der
    ``-ai``-Suffix macht sichtbar, ob rembg/onnxruntime tatsaechlich gebuendelt
    sind (dieselbe Bedingung wie ``requirements.txt`` weiter oben im Skript).
    """
    txt = BUILD_SH.read_text(encoding="utf-8")
    assert 'PLATFORM_TAG="linux-x86_64"' in txt
    assert 'PLATFORM_TAG="linux-raspberrypi-arm64"' in txt
    assert 'AI_SUFFIX="-ai"' in txt
    assert 'FINAL="$BUILD/${APP_NAME}-${VERSION}-${PLATFORM_TAG}${AI_SUFFIX}.AppImage"' in txt


def test_appimage_build_exports_constraints_to_bundler(tmp_path) -> None:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_python = fake_bin / "python3"
    fake_python.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "-m" ] && [ "${2:-}" = "venv" ]; then
  toolenv="$3"
  mkdir -p "$toolenv/bin"
  cp "$0" "$toolenv/bin/python"
  cat > "$toolenv/bin/activate" <<EOF
PATH="$toolenv/bin:\\$PATH"
export PATH
deactivate() { :; }
EOF
  cat > "$toolenv/bin/python-appimage" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
test "${PIP_CONSTRAINT:-}" = "${EXPECTED_CONSTRAINTS:?}"
test -f "$PIP_CONSTRAINT"
touch "$PWD/python-appimage-stub.AppImage"
EOF
  chmod +x "$toolenv/bin/python" "$toolenv/bin/python-appimage"
  exit 0
fi

if [ "${1:-}" = "-m" ] && [ "${2:-}" = "build" ]; then
  shift 2
  outdir=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --outdir)
        outdir="$2"
        shift 2
        ;;
      *)
        shift
        ;;
    esac
  done
  test -n "$outdir"
  mkdir -p "$outdir"
  touch "$outdir/bgremover-2.3.0-py3-none-any.whl"
fi
""",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    build_dir = tmp_path / "build"
    constraints = ROOT / "requirements" / "constraints.txt"
    env = {
        **os.environ,
        "BUILD_DIR": str(build_dir),
        "EXPECTED_CONSTRAINTS": str(constraints),
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
    }
    subprocess.run(
        ["bash", str(BUILD_SH)],
        cwd=str(ROOT),
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    outputs = list(build_dir.glob("BgRemover-*-*.AppImage"))
    assert len(outputs) == 1


# ── .deb package format ────────────────────────────────────────────────

def test_deb_build_script_sane() -> None:
    assert os.access(BUILD_DEB, os.X_OK), ".deb build script must be executable"
    txt = BUILD_DEB.read_text(encoding="utf-8")
    assert txt.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in txt
    assert "dpkg-deb --build" in txt
    assert APP_ID in txt
    assert "libfuse2" in txt  # FUSE dep so the wrapped AppImage runs


def test_deb_names_with_platform_tag_and_ai_suffix_from_wrapped_appimage() -> None:
    """Wie test_appimage_names_with_platform_tag_and_ai_suffix, fuers .deb (#584).

    Der KI-Suffix wird aus dem Dateinamen der gewrappten AppImage abgeleitet
    (kein eigener --ai-Schalter), kann also nie von ihr abweichen.
    """
    txt = BUILD_DEB.read_text(encoding="utf-8")
    assert 'PLATFORM_TAG="linux-x86_64"' in txt
    assert 'PLATFORM_TAG="linux-raspberrypi-arm64"' in txt
    assert '*-ai.AppImage) AI_SUFFIX="-ai" ;;' in txt
    assert 'OUT="$BUILD/deb/${APP_NAME}-${VERSION}-${PLATFORM_TAG}${AI_SUFFIX}.deb"' in txt


@pytest.mark.skipif(shutil.which("dpkg-deb") is None, reason="dpkg-deb not available")
def test_deb_build_produces_valid_package(tmp_path) -> None:
    # Build a .deb from a stub AppImage and inspect it — no network needed.
    appimage = tmp_path / "BgRemover-stub.AppImage"
    appimage.write_bytes(b"#!/bin/sh\nexit 0\n")
    env = {**os.environ, "BUILD_DIR": str(tmp_path / "build")}
    subprocess.run(
        ["bash", str(BUILD_DEB), str(appimage)],
        cwd=str(ROOT), env=env, check=True, capture_output=True, text=True,
    )
    debs = list((tmp_path / "build" / "deb").glob("*.deb"))
    assert len(debs) == 1, f"expected one .deb, got {debs}"
    # Kein --ai-Tag im Namen: die gewrappte Stub-AppImage heisst nicht *-ai.AppImage.
    assert re.match(
        r"BgRemover-.+-linux-(x86_64|raspberrypi-(arm64|armhf))\.deb$", debs[0].name
    ), debs[0].name

    info = subprocess.run(
        ["dpkg-deb", "--info", str(debs[0])],
        check=True, capture_output=True, text=True).stdout
    assert "Package: bgremover" in info
    assert f"Version: {_pyproject_version()}" in info
    assert re.search(r"Architecture: (amd64|arm64|armhf)", info)
    assert "Depends: libfuse2" in info

    contents = subprocess.run(
        ["dpkg-deb", "--contents", str(debs[0])],
        check=True, capture_output=True, text=True).stdout
    for expected in (
        "/opt/BgRemover/BgRemover.AppImage",
        f"/usr/share/applications/{APP_ID}.desktop",
        f"/usr/share/icons/hicolor/512x512/apps/{APP_ID}.png",
        f"/usr/share/metainfo/{APP_ID}.metainfo.xml",
    ):
        assert expected in contents, f"missing from .deb: {expected}"


@pytest.mark.skipif(shutil.which("dpkg-deb") is None, reason="dpkg-deb not available")
def test_deb_build_propagates_ai_suffix_from_appimage_name(tmp_path) -> None:
    """Eine ``*-ai.AppImage`` ergibt ein ``*-ai.deb`` (Befund/#584).

    Der KI-Hinweis im .deb-Namen wird bewusst aus dem Namen der gewrappten
    AppImage abgeleitet statt ueber einen zweiten, unabhaengig zu pflegenden
    --ai-Schalter — so kann das .deb nie faelschlich "AI bundled" behaupten,
    waehrend die tatsaechlich verpackte AppImage keine ist (oder umgekehrt).
    """
    appimage = tmp_path / "BgRemover-2.6.0-linux-x86_64-ai.AppImage"
    appimage.write_bytes(b"#!/bin/sh\nexit 0\n")
    env = {**os.environ, "BUILD_DIR": str(tmp_path / "build")}
    subprocess.run(
        ["bash", str(BUILD_DEB), str(appimage)],
        cwd=str(ROOT), env=env, check=True, capture_output=True, text=True,
    )
    debs = list((tmp_path / "build" / "deb").glob("*.deb"))
    assert len(debs) == 1, f"expected one .deb, got {debs}"
    assert debs[0].name.endswith("-ai.deb"), debs[0].name


# ── Release workflow ───────────────────────────────────────────────────

def test_release_workflow_builds_both_arches_and_formats() -> None:
    # Text-based (no PyYAML dependency — matches tests/test_ci_qt_packages.py
    # and keeps the test runnable with only the declared ``[test]`` extras).
    text = WORKFLOW.read_text(encoding="utf-8")
    # Triggers: version tags + manual dispatch.
    assert "'v*'" in text
    assert "workflow_dispatch:" in text
    # Release upload needs write permission.
    assert re.search(r"(?m)^\s*contents:\s*write\b", text)
    # Both target architectures, with a native arm64 runner (Raspberry Pi OS).
    assert "arch: x86_64" in text
    assert "arch: aarch64" in text
    assert re.search(r"runner:\s*ubuntu-\S*-arm\b", text), "needs a native arm64 runner"
    # Builds both formats and publishes them to the GitHub Release.
    assert "build_appimage.sh" in text
    assert "build_deb.sh" in text
    assert "gh release" in text


def test_release_workflow_uses_unambiguous_platform_tags() -> None:
    """Jedes Matrix-Leg traegt ein OS+Geraet-Tag statt der rohen Architektur.

    #584: ein blosses ``arm64`` liesse den Linux/Raspi-Build nicht vom
    macOS-Build unterscheiden (beide melden ``uname -m`` = ``arm64``/``aarch64``
    fuer denselben CPU-Typ). Die Verify-Schritte muessen denselben Tag lesen,
    den der jeweilige Build-Schritt tatsaechlich erzeugt.
    """
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "platform_tag: linux-x86_64" in text
    assert "platform_tag: linux-raspberrypi-arm64" in text
    assert "platform_tag: macos-arm64" in text
    assert text.count("matrix.platform_tag") >= 3
