#!/usr/bin/env python3
"""Diagnose the local BgRemover test environment.

Der Installationszustand von ``bgremover`` wird seit #1053 gegen **zwei**
Verträge geprüft, die sich gegenseitig ausschließen:

* **editable** – der SessionStart-Hook (#1031/#1047) installiert bewusst
  ``pip install -e ".[test]"``: ein editierbarer Link auf genau diesen
  Checkout, damit per Dateipfad gestartete Subprozess-Tests denselben Code
  messen wie der In-Prozess-Import. Gültig ist genau das, was
  ``scripts/check_install_provenance.py`` als gültig einstuft – die Regel hat
  nur diese eine Quelle und wird hier importiert, nicht kopiert.
* **installed** – ``make pr-check`` installiert bewusst nicht-editable, damit
  die App-Smoke-Tests die installierte Paketrealität sehen (Console-Script,
  Ressourcen, Einstieg wie CI/Release/App-Bundle).

Ohne Option akzeptiert der Doctor **einen** der beiden Zustände und benennt
ihn; ``--require-installed`` (``make pr-check``) lässt nur den zweiten gelten.
Ein Link auf einen fremden Checkout, eine veraltete Kopie neben einem
gültigen Link oder mehrere Distributionen sind in beiden Modi ein Fehler.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_PACKAGE = ROOT / "bgremover"
REQUIRED_DISTS = ("pytest", "pytest-qt", "ruff", "mypy", "PyQt6", "PyQt6-Qt6", "PyYAML")
PROVENANCE_SCRIPT = ROOT / "scripts" / "check_install_provenance.py"


def _load_provenance_module():  # type: ignore[no-untyped-def]
    """``scripts/`` ist kein Paket; die Regel wird ueber den Dateipfad geladen."""
    spec = importlib.util.spec_from_file_location("check_install_provenance", PROVENANCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PROVENANCE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    # Dataclasses loesen Annotationen ueber sys.modules auf – ohne Eintrag
    # bricht ``exec_module`` in ``dataclasses._is_type``.
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


cip = _load_provenance_module()

#: Die beiden Installationsvertraege (siehe Modul-Docstring).
CONTRACT_EDITABLE = "editable"
CONTRACT_INSTALLED = "installed"


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def ok(self, msg: str) -> None:
        print(f"OK   {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        print(f"WARN {msg}")

    def fail(self, msg: str) -> None:
        self.errors.append(msg)
        print(f"FAIL {msg}")


def _dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _check_python(reporter: Reporter) -> None:
    version = ".".join(str(x) for x in sys.version_info[:3])
    # Defensive Pruefung im Diagnose-Skript: die App selbst setzt 3.10+ via
    # `requires-python` voraus, das Skript laeuft aber u.U. mit dem
    # System-Python und soll dann verstaendlich abbrechen.
    if sys.version_info < (3, 10):  # noqa: UP036
        reporter.fail(f"Python {version} is too old; use Python 3.10+.")
    else:
        reporter.ok(f"Python {version}: {sys.executable}")


def _check_required_dists(reporter: Reporter) -> None:
    missing: list[str] = []
    for name in REQUIRED_DISTS:
        version = _dist_version(name)
        if version is None:
            missing.append(name)
        else:
            reporter.ok(f"{name} {version} installed")
    if missing:
        reporter.fail(
            "Missing test dependencies: "
            + ", ".join(missing)
            + ". Run: make install-test"
        )


def _neutral_import_location(python: str = sys.executable) -> tuple[Path | None, str]:
    """Woher ``import bgremover`` aus einem leeren Arbeitsverzeichnis kommt.

    Liefert ``(Pfad, "")`` bei Erfolg, sonst ``(None, stderr)``.
    """
    with tempfile.TemporaryDirectory() as td:
        proc = subprocess.run(
            [
                python,
                "-c",
                "import pathlib, bgremover; print(pathlib.Path(bgremover.__file__).resolve())",
            ],
            cwd=td,
            text=True,
            capture_output=True,
            timeout=30,
        )
    if proc.returncode != 0:
        return None, (proc.stderr or "").strip()
    printed = [line for line in proc.stdout.splitlines() if line.strip()]
    return (Path(printed[-1].strip()) if printed else Path("")), ""


def classify_install(findings: Sequence[object]) -> tuple[str | None, str]:
    """Metadaten-Befunde der Provenienzregel auf genau einen Vertrag abbilden.

    Rueckgabe ``(Vertrag, Begruendung)``; ``None`` heisst: passt zu keinem –
    fremder Checkout, veraltete Kopie neben einem Link, unlesbare Metadaten
    oder mehrere Distributionen. Die Gueltigkeit eines editierbaren Links
    entscheidet ``check_install_provenance`` (``Finding.ok``); hier wird nur
    der nicht-editable Fall als zweiter, eigener Vertrag anerkannt.
    """
    if not findings:
        # Fail-closed wie ``ProvenanceReport.ok``: ``all([])`` waere True.
        return None, "keine Befunde"
    details = "; ".join(f"{f.kind}: {f.detail}" for f in findings)  # type: ignore[attr-defined]
    if all(f.ok for f in findings):  # type: ignore[attr-defined]
        return CONTRACT_EDITABLE, details
    kinds = {f.kind for f in findings}  # type: ignore[attr-defined]
    if len(findings) == 1 and kinds == {cip.KIND_NON_EDITABLE}:
        return CONTRACT_INSTALLED, details
    return None, details


def _check_bgremover_install(
    reporter: Reporter,
    *,
    require_installed: bool = False,
    repo_root: Path = ROOT,
    search_path: Sequence[str] | None = None,
    python: str = sys.executable,
) -> None:
    findings = cip.check_metadata_provenance(repo_root, search_path=search_path)
    if any(f.kind == cip.KIND_MISSING for f in findings):
        reporter.fail("bgremover is not installed. Run: make install-test")
        return
    version = _dist_version("bgremover") or "?"
    contract, details = classify_install(findings)
    if contract is None:
        reporter.fail(
            "bgremover installation matches neither contract (editable link on this "
            f"checkout, or one non-editable install): {details}. "
            "Run: make install-test (pr-check) or pip install -e '.[test]' (session)"
        )
        return
    if contract == CONTRACT_EDITABLE and require_installed:
        reporter.fail(
            "bgremover is installed editable; --require-installed (make pr-check) needs "
            "the installed package reality. Run: make install-test"
        )
    elif contract == CONTRACT_EDITABLE:
        reporter.ok(
            f"bgremover {version} is an editable link on this checkout "
            "(SessionStart hook contract, #1031)"
        )
    else:
        reporter.ok(f"bgremover {version} installed non-editable (pr-check contract)")

    script = shutil.which("bgremover")
    if script is None:
        reporter.fail(
            "Console script 'bgremover' is not on PATH. Activate the venv "
            "or run through make, which prepends .venv/bin."
        )
    else:
        reporter.ok(f"console script found: {script}")

    if contract == CONTRACT_EDITABLE:
        # Postcondition des Hook-Vertrags: der neutrale Import trifft den
        # Checkout – dieselbe Pruefung, die der Hook selbst faehrt.
        finding = cip.check_neutral_import(repo_root, python=python)
        if finding.ok:
            reporter.ok(f"bgremover imports from this checkout in a neutral cwd ({finding.detail})")
        else:
            reporter.fail(f"neutral-cwd import does not hit this checkout: {finding.detail}")
        return

    imported_from, stderr = _neutral_import_location(python)
    source_package = repo_root / "bgremover"
    if imported_from is None:
        reporter.fail(
            "Cannot import bgremover from a neutral cwd. "
            "Run: make install-test\n"
            f"stderr: {stderr}"
        )
    elif imported_from == source_package or source_package in imported_from.parents:
        reporter.warn(
            "bgremover imports from the source tree in a neutral cwd although the "
            "distribution is non-editable; a clean non-editable test install is recommended."
        )
    else:
        reporter.ok(f"bgremover imports from installed package: {imported_from}")


def _check_optional_ai_extra(reporter: Reporter) -> None:
    if importlib.util.find_spec("rembg") is not None:
        reporter.warn(
            "rembg is installed in this test environment. Tests disable the "
            "warmup, but a plain [test] environment is faster and cleaner."
        )


def _check_qt_offscreen(reporter: Reporter) -> None:
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    probe = (
        "from bgremover.qt_plugins import ensure_qt_plugin_path; "
        "ensure_qt_plugin_path(); "
        "from PyQt6.QtWidgets import QApplication; "
        "QApplication([]); print('QAPP_OK')"
    )
    with tempfile.TemporaryDirectory() as td:
        try:
            proc = subprocess.run(
                [sys.executable, "-c", probe],
                cwd=td,
                env=env,
                text=True,
                capture_output=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            reporter.fail("Qt offscreen probe timed out after 60 seconds.")
            return
    if proc.returncode == 0 and "QAPP_OK" in proc.stdout:
        reporter.ok("Qt offscreen QApplication starts")
        return

    stderr = (proc.stderr or "").strip() or "(no Qt stderr captured)"
    reporter.fail(
        "Qt offscreen QApplication failed. Run: make install-test; if that "
        "does not help, rebuild the venv with Python 3.12/3.13.\n"
        f"Qt stderr:\n{stderr}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--require-installed",
        action="store_true",
        help="nur den nicht-editable Vertrag akzeptieren (make pr-check); "
        "ohne Option gilt auch der editable Link des SessionStart-Hooks",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    reporter = Reporter()
    _check_python(reporter)
    _check_required_dists(reporter)
    _check_bgremover_install(reporter, require_installed=args.require_installed)
    _check_optional_ai_extra(reporter)
    _check_qt_offscreen(reporter)

    if reporter.warnings:
        print(f"\nWarnings: {len(reporter.warnings)}")
    if reporter.errors:
        print(f"\nTest environment check failed: {len(reporter.errors)} issue(s).")
        return 1
    print("\nTest environment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
