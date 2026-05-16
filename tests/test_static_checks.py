"""Statische AST-Prüfungen für Fixes, die zur Laufzeit nur schwer
zuverlässig isoliert werden können (KI-Worker, Qt-Connection-Topologie).
Sie schützen vor einer versehentlichen Re-Introduktion der Bugs durch
spätere Refaktorierungen.
"""
import ast
from pathlib import Path

import pytest


SRC_PATH = Path(__file__).resolve().parent.parent / "BgRemover.py"


@pytest.fixture(scope="module")
def source() -> str:
    return SRC_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def functions(source: str) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(source)
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


# ── Fix #1: KI-Race ────────────────────────────────────────────────────

def test_run_ai_records_ai_input_version(functions):
    body = ast.unparse(functions["_run_ai"])
    assert "self._ai_input_version" in body, (
        "_run_ai muss self._ai_input_version setzen, damit veraltete "
        "KI-Ergebnisse anhand des Canvas-Versionszählers erkannt werden."
    )


def test_on_ai_done_checks_version(functions):
    body = ast.unparse(functions["_on_ai_done"])
    assert "self._ai_input_version" in body
    assert "!=" in body, (
        "_on_ai_done muss die Canvas-Version mit _ai_input_version vergleichen."
    )


# ── Fix #6: Thread-Cleanup ─────────────────────────────────────────────

def test_launch_worker_uses_delete_later(functions):
    body = ast.unparse(functions["_launch_worker"])
    assert "deleteLater" in body, (
        "_launch_worker muss deleteLater an Worker und Thread anhängen, um "
        "Qt-Lecks zu vermeiden."
    )


def test_thread_finished_handler_resets_refs(functions):
    body = ast.unparse(functions["_on_ai_thread_finished"])
    assert "self._ai_thread = None" in body
    assert "self._ai_worker = None" in body


# ── Fix: closeEvent stoppt Hintergrund-Threads ─────────────────────────

def test_main_window_has_close_event(functions):
    assert "closeEvent" in functions, (
        "MainWindow muss closeEvent überschreiben, sonst crasht Python "
        "beim Schliessen während ein QThread noch läuft."
    )


def test_close_event_shuts_down_all_threads(functions):
    body = ast.unparse(functions["closeEvent"])
    for ref in ("_ai_thread", "_load_thread", "_warmup_thread"):
        assert ref in body, f"closeEvent muss self.{ref} herunterfahren."


def test_shutdown_helper_uses_wait_and_terminate(functions):
    body = ast.unparse(functions["_shutdown_thread"])
    assert "isRunning" in body
    assert ".quit()" in body
    assert ".wait(" in body
    assert ".terminate()" in body, (
        "Notbremse terminate() nötig, weil rembg-run() blockierende "
        "C-Aufrufe macht und auf quit() nicht reagiert."
    )


# ── Fix #4: 270°-Button-Vorzeichen ─────────────────────────────────────

def test_270_button_uses_positive_value(source: str):
    # Das Tuple in der Toolbar muss '270' und nicht '-270' enthalten
    assert "270°\",  270," in source or '270°", 270,' in source, (
        "270°-Button muss positiven Winkel verwenden, damit Drehrichtung "
        "der Pfeilbeschriftung entspricht."
    )
    # Sicherstellen, dass kein -270 mehr im Quelltext steckt
    assert "-270" not in source


# ── Fix #8: dropEvent meldet ignorierte Dateien ────────────────────────

def test_drop_event_reports_extra_files(functions):
    body = ast.unparse(functions["dropEvent"]).lower()
    assert "weitere" in body, (
        "dropEvent muss melden, wenn weitere Dateien verworfen wurden."
    )


# ── B3: rembg-Warmup ────────────────────────────────────────────────────

def test_warmup_worker_class_exists(source: str):
    tree = ast.parse(source)
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    assert "RembgWarmupWorker" in names, (
        "RembgWarmupWorker muss als eigene Worker-Klasse existieren."
    )


def test_main_window_starts_warmup_when_rembg_available(source: str):
    assert "_start_rembg_warmup" in source
    # Aufruf an REMBG_AVAILABLE-Bedingung gekoppelt
    assert "REMBG_AVAILABLE" in source
    assert "self._start_rembg_warmup()" in source
