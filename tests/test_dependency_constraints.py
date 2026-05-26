"""Checks for the pinned dependency constraints used by CI/build scripts."""

from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parent.parent
CONSTRAINTS = ROOT / "requirements" / "constraints.txt"


def _constraint_names() -> set[str]:
    names: set[str] = set()
    for raw in CONSTRAINTS.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        names.add(canonicalize_name(Requirement(line).name))
    return names


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
    license_ci = (ROOT / ".github/workflows/license-check.yml").read_text(encoding="utf-8")

    assert "PIP_CONSTRAINT" in makefile
    assert "requirements/constraints.txt" in app_builder
    assert "--constraint requirements/constraints.txt" in license_ci
