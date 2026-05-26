#!/usr/bin/env python3
"""Diagnose the local BgRemover test environment."""

from __future__ import annotations

import importlib.metadata as metadata
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_PACKAGE = ROOT / "bgremover"
REQUIRED_DISTS = ("pytest", "pytest-qt", "ruff", "mypy", "PyQt6", "PyQt6-Qt6")


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


def _check_bgremover_install(reporter: Reporter) -> None:
    try:
        dist = metadata.distribution("bgremover")
    except metadata.PackageNotFoundError:
        reporter.fail("bgremover is not installed. Run: make install-test")
        return

    reporter.ok(f"bgremover {dist.version} installed")
    direct_url = dist.read_text("direct_url.json")
    if direct_url:
        try:
            data = json.loads(direct_url)
        except json.JSONDecodeError:
            data = {}
        if data.get("dir_info", {}).get("editable"):
            reporter.fail(
                "bgremover is installed editable; app smoke tests need the "
                "installed package reality. Run: make install-test"
            )

    script = shutil.which("bgremover")
    if script is None:
        reporter.fail(
            "Console script 'bgremover' is not on PATH. Activate the venv "
            "or run through make, which prepends .venv/bin."
        )
    else:
        reporter.ok(f"console script found: {script}")

    with tempfile.TemporaryDirectory() as td:
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "import pathlib, bgremover; "
                "print(pathlib.Path(bgremover.__file__).resolve())",
            ],
            cwd=td,
            text=True,
            capture_output=True,
            timeout=30,
        )
    if proc.returncode != 0:
        reporter.fail(
            "Cannot import bgremover from a neutral cwd. "
            "Run: make install-test\n"
            f"stderr: {(proc.stderr or '').strip()}"
        )
    else:
        imported_from = Path(proc.stdout.strip())
        if imported_from == SOURCE_PACKAGE or SOURCE_PACKAGE in imported_from.parents:
            reporter.warn(
                "bgremover imports from the source tree in a neutral cwd; "
                "a non-editable test install is recommended."
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


def main() -> int:
    reporter = Reporter()
    _check_python(reporter)
    _check_required_dists(reporter)
    _check_bgremover_install(reporter)
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
