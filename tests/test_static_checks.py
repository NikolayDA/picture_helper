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

def test_run_ai_records_ai_input_identity(functions):
    body = ast.unparse(functions["_run_ai"])
    assert "self._ai_input" in body, (
        "_run_ai muss self._ai_input setzen, damit veraltete KI-Ergebnisse "
        "erkannt werden können."
    )


def test_on_ai_done_checks_image_identity(functions):
    body = ast.unparse(functions["_on_ai_done"])
    assert "self._ai_input" in body
    assert (" is not " in body) or ("!=" in body), (
        "_on_ai_done muss prüfen, ob das Eingabe-Bild noch identisch ist."
    )


# ── Fix #6: Thread-Cleanup ─────────────────────────────────────────────

def test_run_ai_uses_delete_later(functions):
    body = ast.unparse(functions["_run_ai"])
    assert "deleteLater" in body, (
        "_run_ai muss deleteLater an Worker und Thread anhängen, um Qt-"
        "Lecks zu vermeiden."
    )


def test_thread_finished_handler_resets_refs(functions):
    body = ast.unparse(functions["_on_ai_thread_finished"])
    assert "self._ai_thread = None" in body
    assert "self._ai_worker = None" in body


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
