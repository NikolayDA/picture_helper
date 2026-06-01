"""Statische AST-Prüfungen für Fixes, die zur Laufzeit nur schwer
zuverlässig isoliert werden können (KI-Worker, Qt-Connection-Topologie).
Sie schützen vor einer versehentlichen Re-Introduktion der Bugs durch
spätere Refaktorierungen.

Die ``#N``-/``Bn``-Marken in den Abschnittsüberschriften verweisen auf die
**historischen** Review-Runden vor v2.2
(``docs/history/RECOMMENDATIONS-2026-pre-v2.2.md``) – NICHT auf die
Nummerierung der aktuellen ``RECOMMENDATIONS.md`` (dort ist #4 z. B. ein
anderer, verworfener Befund). Die Marken bleiben als Herkunftshinweis
stehen; maßgeblich ist jeweils der beschreibende Titel.
"""
import ast
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent


def _source_files() -> list[Path]:
    """Alle Paketmodule unter ``bgremover/`` (je Datei einzeln geparst).

    Der frühere Monolith ``BgRemover.py`` ist vollständig nach ``bgremover/``
    migriert; die statischen Garantien gelten unabhängig davon, in welchem
    Modul ein Symbol liegt. ``from __future__`` muss je Datei zuerst stehen,
    daher wird pro Datei geparst statt über konkatenierten Quelltext.
    """
    return sorted((_ROOT / "bgremover").glob("*.py"))


@pytest.fixture(scope="module")
def source() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in _source_files())


@pytest.fixture(scope="module")
def functions() -> dict[str, ast.FunctionDef]:
    out: dict[str, ast.FunctionDef] = {}
    for p in _source_files():
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.FunctionDef):
                out.setdefault(n.name, n)
    return out


@pytest.fixture(scope="module")
def classes() -> set[str]:
    names: set[str] = set()
    for p in _source_files():
        tree = ast.parse(p.read_text(encoding="utf-8"))
        names |= {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    return names


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
    body = ast.unparse(functions["_build_thread"])
    assert "deleteLater" in body, (
        "WorkerController._build_thread muss deleteLater an Worker und "
        "Thread anhängen, um Qt-Lecks zu vermeiden."
    )


def test_thread_finished_handler_resets_refs(functions):
    body = ast.unparse(functions["_finish_ai_thread"])
    assert "self.ai_thread = None" in body
    assert "self.ai_worker = None" in body


# ── Fix: closeEvent stoppt Hintergrund-Threads ─────────────────────────

def test_main_window_has_close_event(functions):
    assert "closeEvent" in functions, (
        "MainWindow muss closeEvent überschreiben, sonst crasht Python "
        "beim Schliessen während ein QThread noch läuft."
    )


def test_close_event_shuts_down_all_threads(functions):
    body = ast.unparse(functions["closeEvent"])
    assert "self._worker_controller.shutdown_all()" in body


def test_shutdown_helper_uses_wait_and_terminate(functions):
    body = ast.unparse(functions["shutdown_thread"])
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

def test_warmup_worker_class_exists(classes: set[str]):
    assert "RembgWarmupWorker" in classes, (
        "RembgWarmupWorker muss als eigene Worker-Klasse existieren."
    )


def test_main_window_starts_warmup_when_rembg_available(source: str):
    assert "_start_rembg_warmup" in source
    # Aufruf an REMBG_AVAILABLE-Bedingung gekoppelt
    assert "REMBG_AVAILABLE" in source
    assert "self._start_rembg_warmup()" in source
