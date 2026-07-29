"""Tests für den EufyMake-Export-/2.7.0-Projekt-Automationshook (#685-Review).

Braucht kein GL (anders als ``test_screenshot3d.py``): läuft vollständig
offscreen mit einem echten ``MainWindow``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from bgremover import MainWindow
from bgremover.acceptance_smoke import run_acceptance_extra

pytestmark = pytest.mark.ui_smoke

_V270_FIXTURE = Path(__file__).parent / "fixtures" / "project_v2_7_0.bgrproj"


def test_run_acceptance_extra_succeeds_for_real_v270_fixture(qapp, qtbot, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    output_json = tmp_path / "acceptance_extra.json"
    try:
        result = run_acceptance_extra(win, output_json, _V270_FIXTURE)
    finally:
        win.close()

    assert result.ok, (result.v270_message, result.eufymake_message)
    assert result.v270_ok
    assert result.eufymake_ok

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["v270_project_open"]["ok"] is True
    assert payload["eufymake_export"]["ok"] is True

    export_dir = output_json.parent / "eufymake_export"
    assert (export_dir / "color_motif.png").is_file()
    assert (export_dir / "height_map.png").is_file()
    assert (export_dir / "manifest.json").is_file()


def test_run_acceptance_extra_reports_missing_fixture(qapp, qtbot, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    output_json = tmp_path / "acceptance_extra.json"
    missing_fixture = tmp_path / "does_not_exist.bgrproj"
    try:
        result = run_acceptance_extra(win, output_json, missing_fixture)
    finally:
        win.close()

    assert not result.ok
    assert not result.v270_ok
    assert "fehlt" in result.v270_message
    # Export wird nach fehlgeschlagenem Open bewusst übersprungen, nicht
    # nochmal separat versucht (würde nur denselben Fehler verdoppeln).
    assert not result.eufymake_ok
    assert "übersprungen" in result.eufymake_message

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["ok"] is False
