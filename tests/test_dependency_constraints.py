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


# Extras, deren Abhaengigkeiten bewusst NICHT im reproduzierbaren
# constraints.txt-Snapshot landen und daher auch nicht vom Dependency-Audit
# erfasst werden: ``docs`` erzeugt nur lokal/manuell ANLEITUNG.pdf
# (``pip install -e ".[docs]"``), wird in keinem CI-/Release-Pfad installiert
# und gehoert nicht zum getesteten Build-Set. Analog zur bewussten Ausnahme von
# release-linux.yml in test_ci_pip_pin.
_UNAUDITED_EXTRAS = {"docs"}


def _project_dependency_names() -> set[str]:
    """Direkte Requirement-Namen aus pyproject.toml: Laufzeit-``dependencies``
    plus alle optional-dependencies-Extras ausser ``_UNAUDITED_EXTRAS``.

    Bewusst per Regex statt tomllib geparst, damit die Pruefung auch auf
    Python 3.10 (ohne tomllib) Teil der Matrix bleibt. Requirement-Strings
    werden Anfuehrungszeichen-genau gelesen, damit Extra-Marker wie
    ``rembg[cpu]`` die eckigen Klammern nicht zerschiessen."""
    text = PYPROJECT.read_text(encoding="utf-8")
    names: set[str] = set()

    runtime = re.search(r"^dependencies\s*=\s*\[(.*?)\]", text, re.M | re.S)
    assert runtime is not None, "pyproject.toml [project] braucht dependencies = [...]"
    for spec in re.findall(r'"([^"]+)"', runtime.group(1)):
        names.add(canonicalize_name(Requirement(spec).name))

    optional = re.search(r"^\[project\.optional-dependencies\](.*?)^\[", text, re.M | re.S)
    assert optional is not None, "pyproject.toml braucht [project.optional-dependencies]"
    current: str | None = None
    for raw in optional.group(1).splitlines():
        header = re.match(r"\s*([A-Za-z][\w.-]*)\s*=", raw)
        if header:
            current = header.group(1)
        if current in _UNAUDITED_EXTRAS:
            continue
        for spec in re.findall(r'"([^"]+)"', raw):
            names.add(canonicalize_name(Requirement(spec).name))
    return names


def test_constraints_cover_all_audited_pyproject_dependencies() -> None:
    """Drift-Guard (#327-Review): Jede in pyproject.toml deklarierte direkte
    Abhaengigkeit – Laufzeit plus die in CI/Release installierten Extras
    (ai, test) – muss in requirements/constraints.txt gepinnt sein. Andernfalls
    koennte eine nur in pyproject.toml ergaenzte Dependency vom Dependency-Audit
    (das genau diesen Snapshot prueft) unbemerkt durchrutschen. ``docs`` ist
    bewusst ausgenommen (_UNAUDITED_EXTRAS)."""
    missing = _project_dependency_names() - _constraint_names()
    assert not missing, f"pyproject-Dependencies ohne Pin in constraints.txt: {sorted(missing)}"


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
    session_hook = (ROOT / ".claude/hooks/session-start.sh").read_text(encoding="utf-8")

    assert "PIP_CONSTRAINT" in makefile
    assert "requirements/constraints.txt" in app_builder
    assert "PIP_CONSTRAINT" in linux_app_builder
    assert "requirements/constraints.txt" in linux_app_builder
    assert "--constraint requirements/constraints.txt" in license_ci
    # Web-Session-Hook: ohne Constraints loest pip frei auf und kann aeltere
    # (verwundbare) urllib3/idna-Versionen einspielen (#205/#206-Remediation).
    assert "--constraint requirements/constraints.txt" in session_hook


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


def test_constraints_pin_patched_urllib3() -> None:
    """constraints.txt darf urllib3 nicht unter 2.7.0 zulassen
    (CVE-2026-44432 Decompression-DoS, CVE-2026-44431 Header-Leak bei
    Cross-Origin-Redirects). Befund #205 war ein reiner System-Befund –
    dieser Test friert das saubere Projekt-Pinning gegen Downgrades ein."""
    reqs = _constraint_requirements()

    assert "urllib3" in reqs, "urllib3 fehlt in requirements/constraints.txt"
    spec = reqs["urllib3"].specifier
    assert Version("2.7.0") in spec
    assert Version("2.6.3") not in spec  # die im System vorgefundene Altversion


def test_constraints_pin_patched_idna() -> None:
    """constraints.txt darf idna nicht unter 3.15 zulassen (CVE-2026-45409,
    DoS via idna.encode(); Wiederoeffnung von CVE-2024-3651). Befund #206
    war ein reiner System-Befund – dieser Test friert das saubere
    Projekt-Pinning gegen Downgrades ein."""
    reqs = _constraint_requirements()

    assert "idna" in reqs, "idna fehlt in requirements/constraints.txt"
    spec = reqs["idna"].specifier
    assert Version("3.15") in spec
    assert Version("3.11") not in spec  # die im System vorgefundene Altversion


def test_dependency_audit_pr_trigger_is_not_path_filtered() -> None:
    """Required PR check must start even for docs-only changes.

    GitHub leaves required checks in an "Expected" state when a workflow is
    skipped by a pull_request paths filter, so the dependency audit deliberately
    runs for every PR.
    """
    workflow = (ROOT / ".github/workflows/dependency-audit.yml").read_text(
        encoding="utf-8"
    )
    trigger_block = workflow.split("on:", 1)[1].split("permissions:", 1)[0]
    pull_request_block = trigger_block.split("pull_request:", 1)[1].split(
        "schedule:", 1
    )[0]

    assert "paths:" not in pull_request_block
    assert "paths-ignore:" not in pull_request_block
