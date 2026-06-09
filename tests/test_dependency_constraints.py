"""Checks for the pinned dependency constraints used by CI/build scripts."""

import re
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

ROOT = Path(__file__).resolve().parent.parent
CONSTRAINTS = ROOT / "requirements" / "constraints.txt"
PYPROJECT = ROOT / "pyproject.toml"


def _constraint_names() -> set[str]:
    names: set[str] = set()
    for raw in CONSTRAINTS.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        names.add(canonicalize_name(Requirement(line).name))
    return names


def _constraint_requirements() -> dict[str, Requirement]:
    """Erster Constraint-Eintrag je Paketname (Marker-Duplikate wie numpy
    teilen sich denselben Namen; fuer setuptools/wheel gibt es nur einen)."""
    reqs: dict[str, Requirement] = {}
    for raw in CONSTRAINTS.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        req = Requirement(line)
        reqs.setdefault(canonicalize_name(req.name), req)
    return reqs


def _build_system_setuptools() -> Requirement:
    """setuptools-Requirement aus pyproject.toml [build-system].requires.

    Bewusst per Regex statt tomllib geparst, damit die Pruefung auch auf
    Python 3.10 (ohne tomllib) Teil der Matrix bleibt."""
    text = PYPROJECT.read_text(encoding="utf-8")
    section = re.search(r"^\[build-system\](.*?)^\[", text, re.M | re.S)
    block = section.group(1) if section else text
    requires = re.search(r"requires\s*=\s*\[(.*?)\]", block, re.S)
    assert requires is not None, "pyproject.toml [build-system] needs requires = [...]"
    for spec in re.findall(r"""["']([^"']+)["']""", requires.group(1)):
        req = Requirement(spec)
        if canonicalize_name(req.name) == "setuptools":
            return req
    raise AssertionError("setuptools not listed in [build-system].requires")


def test_constraints_cover_runtime_test_and_ai_direct_dependencies() -> None:
    names = _constraint_names()
    expected = {
        "mypy",
        "numpy",
        "packaging",
        "pillow",
        "pyqt6",
        "pytest",
        "pytest-qt",
        "rembg",
        "ruff",
    }
    assert expected <= names


def test_constraints_include_qt_wheel_companions() -> None:
    names = _constraint_names()
    assert {"pyqt6-qt6", "pyqt6-sip"} <= names


def test_installers_use_constraints_file() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    app_builder = (ROOT / "create_BgRemover_app.sh").read_text(encoding="utf-8")
    linux_app_builder = (
        ROOT / "packaging" / "linux" / "build_appimage.sh"
    ).read_text(encoding="utf-8")
    license_ci = (ROOT / ".github/workflows/license-check.yml").read_text(encoding="utf-8")

    assert "PIP_CONSTRAINT" in makefile
    assert "requirements/constraints.txt" in app_builder
    assert "PIP_CONSTRAINT" in linux_app_builder
    assert "requirements/constraints.txt" in linux_app_builder
    assert "--constraint requirements/constraints.txt" in license_ci


def test_build_system_setuptools_excludes_known_rce() -> None:
    """[build-system].requires darf keine setuptools-Version vor 78.1.1 zulassen
    (CVE-2024-6345 RCE, CVE-2025-47273 Path-Traversal)."""
    spec = _build_system_setuptools().specifier
    assert Version("78.1.1") in spec
    assert Version("78.1.0") not in spec
    assert Version("68.1.2") not in spec  # die in CI/Dev vorgefundene Altversion


def test_constraints_pin_patched_build_backend() -> None:
    """constraints.txt pinnt setuptools/wheel auf die gepatchten Releases, damit
    eingeschraenkte Installs/Wheel-Builds keine verwundbaren Versionen ziehen."""
    reqs = _constraint_requirements()

    assert "setuptools" in reqs, "setuptools fehlt in requirements/constraints.txt"
    setuptools_spec = reqs["setuptools"].specifier
    assert Version("78.1.1") in setuptools_spec
    assert Version("78.1.0") not in setuptools_spec  # CVE-2025-47273

    assert "wheel" in reqs, "wheel fehlt in requirements/constraints.txt"
    wheel_spec = reqs["wheel"].specifier
    assert Version("0.46.2") in wheel_spec
    assert Version("0.46.1") not in wheel_spec  # CVE-2026-24049
