"""Statische AST-Prüfungen für Regeln, die zur Laufzeit nur schwer
zuverlässig isoliert werden können (Fenster-Lifecycle, UI-Verdrahtung).
Sie schützen vor einer versehentlichen Re-Introduktion von Bugs durch
spätere Refaktorierungen.
"""
import ast
import re
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


# Hinweis: Die früheren AST-Checks zum KI-Race (_ai_input_version) und zum
# Thread-Cleanup (deleteLater, Referenz-Reset) sind durch Verhaltenstests
# ersetzt: Stale-KI-Ergebnisse deckt test_workers.py (verworfenes Ergebnis
# nach Bildwechsel) bzw. test_main_window.py (Versionsvergabe) ab; das
# Qt-Aufräumen testet test_worker_controller.py (Worker-Freigabe nach
# Threadende, tatsächliche C++-Löschung via deleteLater, ai_thread/ai_worker
# wieder None) – Methodenrümpfe werden dafür nicht mehr als Text geparst.


# ── closeEvent stoppt Hintergrund-Threads ──────────────────────────────

def test_main_window_has_close_event(functions):
    assert "closeEvent" in functions, (
        "MainWindow muss closeEvent überschreiben, sonst crasht Python "
        "beim Schliessen während ein QThread noch läuft."
    )


def test_close_event_shuts_down_all_threads(functions):
    body = ast.unparse(functions["closeEvent"])
    assert "self._worker_controller.shutdown_all()" in body


def test_shutdown_helper_uses_wait_and_terminate(functions):
    function = functions["shutdown_thread"]
    body = ast.unparse(function)
    wait_calls = [
        node for node in ast.walk(function)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "wait"
        )
    ]
    assert "isRunning" in body
    assert ".quit()" in body
    assert len(wait_calls) == 2
    assert all(call.args for call in wait_calls), (
        "Jeder QThread.wait()-Aufruf braucht ein festes Timeout."
    )
    assert ".terminate()" in body, (
        "terminate() bleibt als begrenzte Notbremse für einen wider Erwarten "
        "hängenden Thread erhalten. Seit #270 läuft die nicht unterbrechbare "
        "ONNX-Inferenz im Inferenz-Kindprozess (nicht im Thread), sodass die "
        "KI kooperativ stoppt; terminate() kann hier keinen nativen Zustand "
        "mehr zerreißen."
    )


# ── 270°-Button-Vorzeichen ─────────────────────────────────────────────

def test_270_button_uses_positive_value(source: str):
    # Der 270°-Dreh-Button muss den positiven Winkel 270 (nicht -270) übergeben,
    # damit die Drehrichtung der Pfeilbeschriftung entspricht. Seit der i18n-
    # Umstellung steht die Beschriftung als tr()-Key direkt neben dem Winkelwert
    # (``tr("…rotate_270"), 270,``) – whitespace-tolerant geprüft.
    assert re.search(r'rotate_270"\)\s*,\s*270\b', source), (
        "270°-Button muss positiven Winkel 270 verwenden, damit Drehrichtung "
        "der Pfeilbeschriftung entspricht."
    )
    # Sicherstellen, dass kein -270 mehr im Quelltext steckt
    assert "-270" not in source


# ── dropEvent meldet ignorierte Dateien ────────────────────────────────

def test_drop_event_reports_extra_files(functions):
    # Die Meldung über ignorierte Zusatzdateien läuft seit der i18n-Umstellung
    # über tr("canvas.opened_extra") statt eines inline-deutschen Literals.
    body = ast.unparse(functions["dropEvent"])
    assert "canvas.opened_extra" in body, (
        "dropEvent muss melden, wenn weitere Dateien verworfen wurden "
        "(Statusmeldung über tr('canvas.opened_extra'))."
    )


# ── rembg-Warmup ───────────────────────────────────────────────────────

def test_warmup_worker_class_exists(classes: set[str]):
    assert "RembgWarmupWorker" in classes, (
        "RembgWarmupWorker muss als eigene Worker-Klasse existieren."
    )


def test_main_window_starts_warmup_when_rembg_available(source: str):
    assert "_start_rembg_warmup" in source
    # Aufruf an REMBG_AVAILABLE-Bedingung gekoppelt
    assert "REMBG_AVAILABLE" in source
    assert "self._start_rembg_warmup()" in source
