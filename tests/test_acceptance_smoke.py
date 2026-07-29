"""Tests für den EufyMake-Export-/2.7.0-Projekt-Automationshook (#685-Review).

Braucht kein GL (anders als ``test_screenshot3d.py``): läuft vollständig
offscreen mit einem echten ``MainWindow``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from bgremover import MainWindow
from bgremover.acceptance_smoke import run_acceptance_extra
from bgremover.height_map import HEIGHT_MAX_16BIT, generate_from_image
from bgremover.project_io import save_project
from bgremover.project_model import LayerKind, LayerRole, Project

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

    export_dir = output_json.parent / f"{output_json.stem}_eufymake_export"
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


def test_run_acceptance_extra_detects_a_tampered_lookalike_project(  # type: ignore[no-untyped-def]
    qapp, qtbot, tmp_path: Path,
) -> None:
    """Negativkontrolle (#685-Review nach PR #721): eine strukturell gleiche,
    aber inhaltlich andere Datei (frische IDs statt der Fixture-Referenz)
    muss der Hook als Abweichung erkennen, statt fälschlich ``ok`` zu melden –
    genau der Codex-Fund, den die verschärfte Prüfung schließt."""
    img = Image.new("RGBA", (16, 16), (1, 2, 3, 255))
    project = Project(16, 16, version=1, metadata={
        "physical_size_mm": [50.0, 30.0],
        "fixture_source": "v2.7.0 (echter Release-Code, #685-Nachweis)",
    })
    color = project.create_layer(img, name="Farbmotiv", kind=LayerKind.COLOR)
    field = generate_from_image(img, max_value=HEIGHT_MAX_16BIT)
    height = project.create_layer(name="Höhenkarte", kind=LayerKind.HEIGHT, height_data=field)
    project.assign_role(height.id, LayerRole.HEIGHT_MAP)
    project.set_active(color.id)
    lookalike = tmp_path / "lookalike.bgrproj"
    save_project(project, lookalike)

    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    output_json = tmp_path / "acceptance_extra.json"
    try:
        result = run_acceptance_extra(win, output_json, lookalike)
    finally:
        win.close()

    assert not result.ok
    assert not result.v270_ok
    assert "verändert" in result.v270_message or "weichen ab" in result.v270_message


def test_run_acceptance_extra_detects_opacity_drift_on_matching_ids(  # type: ignore[no-untyped-def]
    qapp, qtbot, tmp_path: Path,
) -> None:
    """Codex-Fund (#722): IDs/Namen können übereinstimmen, während visible/
    opacity/locked/active_layer_id trotzdem abweichen (z. B. eine Farb-Ebene
    mit halber statt voller Deckkraft) – muss ebenfalls erkannt werden, nicht
    nur ein reiner ID-Unterschied."""
    img = Image.new("RGBA", (16, 16), (1, 2, 3, 255))
    project = Project(16, 16, version=1, metadata={
        "physical_size_mm": [50.0, 30.0],
        "fixture_source": "v2.7.0 (echter Release-Code, #685-Nachweis)",
    })
    color = project.create_layer(img, name="Farbmotiv", kind=LayerKind.COLOR)
    color.id = "50530890db2d4515baec0862fb89cc49"
    color.opacity = 0.5  # exakt das Codex-Beispiel: sonst identisch, nur die Deckkraft weicht ab.
    field = generate_from_image(img, max_value=HEIGHT_MAX_16BIT)
    height = project.create_layer(name="Höhenkarte", kind=LayerKind.HEIGHT, height_data=field)
    height.id = "eed93ecfb5264b278ee2e5e0782ca86a"
    project.assign_role(height.id, LayerRole.HEIGHT_MAP)
    project.set_active(color.id)
    drifted = tmp_path / "opacity_drift.bgrproj"
    save_project(project, drifted)

    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    output_json = tmp_path / "acceptance_extra.json"
    try:
        result = run_acceptance_extra(win, output_json, drifted)
    finally:
        win.close()

    assert not result.ok
    assert not result.v270_ok
    assert "Zustand verändert" in result.v270_message


def test_run_acceptance_extra_twice_in_same_evidence_dir_does_not_collide(  # type: ignore[no-untyped-def]
    qapp, qtbot, tmp_path: Path,
) -> None:
    """Regression (2026-07-29 Hardware-Abnahme, Pi 5, Kandidat 9845147):
    ``scripts/abnahme_smoke.py`` ruft ``_acceptance_extra`` für jede
    Artefaktklasse (AppImage/.deb/.dmg) mit demselben ``evidence_dir`` auf,
    nur der JSON-Dateiname unterscheidet sich je Klasse
    (``acceptance_extra_appimage.json``/``acceptance_extra_deb.json``/...).
    Ein fester Exportordnername ``eufymake_export`` kollidierte deshalb mit
    dem der zuerst gelaufenen Klasse: `write_export` (ohne `overwrite`) schlug
    für die zweite Klasse mit `ExportTargetExistsError` fehl, obwohl beide
    Läufe unabhängig voneinander erfolgreich hätten sein müssen – exakt das
    auf der echten Hardware beobachtete Bild (AppImage ok, .deb
    `write_export fehlgeschlagen: <derselbe Pfad>`)."""
    evidence_dir = tmp_path / "acceptance_extra"
    evidence_dir.mkdir(parents=True)  # wie scripts/abnahme_smoke.py._acceptance_extra vor dem Aufruf

    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    try:
        first = run_acceptance_extra(
            win, evidence_dir / "acceptance_extra_appimage.json", _V270_FIXTURE,
        )
        second = run_acceptance_extra(
            win, evidence_dir / "acceptance_extra_deb.json", _V270_FIXTURE,
        )
    finally:
        win.close()

    assert first.ok, (first.v270_message, first.eufymake_message)
    assert second.ok, (second.v270_message, second.eufymake_message)
    assert (evidence_dir / "acceptance_extra_appimage_eufymake_export" / "color_motif.png").is_file()
    assert (evidence_dir / "acceptance_extra_deb_eufymake_export" / "color_motif.png").is_file()
