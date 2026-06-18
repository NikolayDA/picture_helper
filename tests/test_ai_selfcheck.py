"""Tests für den KI-Selbsttest des --ai-Artefakts (#308).

Übt ``bgremover.ai_process.run_ai_selfcheck`` über echte ``spawn``-Kindprozesse
(mit injizierten Zielen ohne ``rembg``) und den App-Hook ``BGREMOVER_AI_SELFCHECK``
in ``bgremover.app.main``. Der echte rembg-Pfad wird zusätzlich abgedeckt,
soweit das Extra installiert ist.
"""
from __future__ import annotations

import importlib.util

import pytest

from bgremover.ai_process import run_ai_selfcheck
from tests import _ai_selfcheck_helpers as helpers


def test_selfcheck_success_via_spawned_child() -> None:
    ok, message = run_ai_selfcheck(target=helpers.ok_target, timeout=30)
    assert ok is True
    assert "importierbar" in message


def test_selfcheck_reports_child_error_message() -> None:
    ok, message = run_ai_selfcheck(target=helpers.error_target, timeout=30)
    assert ok is False
    assert "absichtlicher Fehler" in message


def test_selfcheck_handles_child_that_dies_without_answer() -> None:
    ok, message = run_ai_selfcheck(target=helpers.raising_target, timeout=30)
    assert ok is False
    # Kein Absturz des Aufrufers; klare Fehlermeldung.
    assert message


def test_selfcheck_times_out_on_unresponsive_child() -> None:
    ok, message = run_ai_selfcheck(target=helpers.slow_target, timeout=0.5)
    assert ok is False
    assert "Zeit" in message or "beendet" in message


def test_selfcheck_default_target_exercises_real_rembg_chain() -> None:
    """Der Default-Pfad startet einen echten Spawn-Kindprozess und importiert
    die rembg-Kette. Ist ``rembg`` (Extra ``ai``) installiert, muss der Import
    inkl. der pymatting-Metadaten gelingen; sonst meldet der Selbsttest einen
    klaren Importfehler – beides ohne Netz/Modell-Download.
    """
    ok, message = run_ai_selfcheck(timeout=60)
    rembg_installed = importlib.util.find_spec("rembg") is not None
    if rembg_installed:
        assert ok is True, message
        assert "importierbar" in message
    else:
        assert ok is False
        assert "rembg" in message.lower() or "modulenotfound" in message.lower()


# ── App-Hook: BGREMOVER_AI_SELFCHECK ────────────────────────────────────

def test_app_hook_runs_selfcheck_and_skips_gui(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mit ``BGREMOVER_AI_SELFCHECK`` läuft der Selbsttest, ohne die GUI zu
    starten; der Exit-Code spiegelt das Ergebnis."""
    import bgremover.ai_process as ai_process
    import bgremover.app as app_module

    monkeypatch.setattr(ai_process, "run_ai_selfcheck", lambda: (True, "alles gut"))

    def _no_qapp(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("QApplication darf im Selbsttest-Modus nicht entstehen")

    monkeypatch.setattr(app_module, "QApplication", _no_qapp)
    monkeypatch.setenv("BGREMOVER_AI_SELFCHECK", "1")

    assert app_module.main() == 0


def test_app_hook_returns_failure_code(monkeypatch: pytest.MonkeyPatch) -> None:
    import bgremover.ai_process as ai_process
    import bgremover.app as app_module

    monkeypatch.setattr(
        ai_process, "run_ai_selfcheck", lambda: (False, "rembg fehlt"))

    def _no_qapp(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("QApplication darf im Selbsttest-Modus nicht entstehen")

    monkeypatch.setattr(app_module, "QApplication", _no_qapp)
    monkeypatch.setenv("BGREMOVER_AI_SELFCHECK", "1")

    assert app_module.main() == 1
