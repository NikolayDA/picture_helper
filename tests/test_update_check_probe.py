"""Tests für den Update-Check-Automationshook (#748).

HTTP-Layer vollständig gemockt (über ``bgremover.app_update.check_for_update``,
selbst bereits in ``tests/test_app_update.py`` gegen echten HTTP-Mock geprüft)
– hier geht es nur um die Evidenz-/Exit-Code-Verdrahtung des Hooks und seine
Anbindung in ``bgremover.app.main``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from bgremover.app_update import UpdateCheckResult, UpdateStatus
from bgremover.update_check_probe import EVIDENCE_SCHEMA, run_update_check_probe


def test_probe_writes_up_to_date_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import bgremover.update_check_probe as probe_module

    monkeypatch.setattr(probe_module, "get_version", lambda: "2.7.2")
    monkeypatch.setattr(
        probe_module, "check_for_update",
        lambda current: UpdateCheckResult(status=UpdateStatus.UP_TO_DATE),
    )

    target = tmp_path / "evidenz.json"
    ok, message = run_update_check_probe(target)

    assert ok is True
    assert "UP_TO_DATE" in message
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["schema"] == EVIDENCE_SCHEMA
    assert payload["kind"] == "abnahme-update-check-probe"
    assert payload["current_version"] == "2.7.2"
    assert payload["status"] == "UP_TO_DATE"
    assert payload["latest_version"] is None
    assert payload["error"] is None


def test_probe_writes_update_available_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import bgremover.update_check_probe as probe_module

    monkeypatch.setattr(probe_module, "get_version", lambda: "2.7.1")
    monkeypatch.setattr(
        probe_module, "check_for_update",
        lambda current: UpdateCheckResult(
            status=UpdateStatus.UPDATE_AVAILABLE,
            latest_version="v2.7.2", release_url="https://example/v2.7.2",
        ),
    )

    target = tmp_path / "nested" / "evidenz.json"
    ok, message = run_update_check_probe(target)

    assert ok is True
    assert "UPDATE_AVAILABLE" in message
    assert "2.7.2" in message
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["status"] == "UPDATE_AVAILABLE"
    assert payload["latest_version"] == "v2.7.2"
    assert payload["release_url"] == "https://example/v2.7.2"


def test_probe_reports_check_failed_as_not_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``CHECK_FAILED`` ist ein bestimmbares, aber technisch nicht erfolgreiches
    Ergebnis – der Aufrufer (Abnahme-Smoke) entscheidet über Pass/Fail anhand
    der geschriebenen Evidenz, dieser Hook meldet nur den Roundtrip-Erfolg."""
    import bgremover.update_check_probe as probe_module

    monkeypatch.setattr(probe_module, "get_version", lambda: "2.7.2")
    monkeypatch.setattr(
        probe_module, "check_for_update",
        lambda current: UpdateCheckResult(status=UpdateStatus.CHECK_FAILED, error="Timeout"),
    )

    target = tmp_path / "evidenz.json"
    ok, message = run_update_check_probe(target)

    assert ok is False
    assert "CHECK_FAILED" in message
    assert "Timeout" in message
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["status"] == "CHECK_FAILED"
    assert payload["error"] == "Timeout"


# ── App-Hook: BGREMOVER_UPDATE_CHECK_PROBE ──────────────────────────────────

def test_app_hook_runs_probe_and_skips_gui(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import bgremover.app as app_module
    import bgremover.update_check_probe as probe_module

    monkeypatch.setattr(probe_module, "get_version", lambda: "2.7.2")
    monkeypatch.setattr(
        probe_module, "check_for_update",
        lambda current: UpdateCheckResult(status=UpdateStatus.UP_TO_DATE),
    )

    def _no_qapp(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("QApplication darf im Update-Check-Probe-Modus nicht entstehen")

    monkeypatch.setattr(app_module, "QApplication", _no_qapp)
    target = tmp_path / "evidenz.json"
    monkeypatch.setenv("BGREMOVER_UPDATE_CHECK_PROBE", str(target))

    assert app_module.main() == 0
    assert target.is_file()


def test_app_hook_returns_failure_code_on_check_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import bgremover.app as app_module
    import bgremover.update_check_probe as probe_module

    monkeypatch.setattr(probe_module, "get_version", lambda: "2.7.2")
    monkeypatch.setattr(
        probe_module, "check_for_update",
        lambda current: UpdateCheckResult(status=UpdateStatus.CHECK_FAILED, error="boom"),
    )

    def _no_qapp(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("QApplication darf im Update-Check-Probe-Modus nicht entstehen")

    monkeypatch.setattr(app_module, "QApplication", _no_qapp)
    monkeypatch.setenv("BGREMOVER_UPDATE_CHECK_PROBE", str(tmp_path / "evidenz.json"))

    assert app_module.main() == 1
