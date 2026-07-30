"""Tests für den EufyMake-Export-/2.7.0-Projekt-Automationshook (#685-Review).

Braucht kein GL (anders als ``test_screenshot3d.py``): läuft vollständig
offscreen mit einem echten ``MainWindow``.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from bgremover import MainWindow
from bgremover.acceptance_smoke import run_acceptance_extra
from bgremover.height_map import HEIGHT_MAX_16BIT, generate_from_image
from bgremover.project_io import save_project
from bgremover.project_model import LayerKind, LayerRole, Project
from bgremover.project_schema import PROJECT_FORMAT_VERSION

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

    assert result.ok, (result.v270_message, result.eufymake_message, result.missing_component_message)
    assert result.v270_ok
    assert result.eufymake_ok
    assert result.missing_component_ok, result.missing_component_message

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["v270_project_open"]["ok"] is True
    assert payload["eufymake_export"]["ok"] is True
    assert payload["missing_component"]["ok"] is True

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
    assert not result.missing_component_ok
    assert "übersprungen" in result.missing_component_message

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


def test_run_acceptance_extra_accepts_matching_expected_version(  # type: ignore[no-untyped-def]
    qapp, qtbot, tmp_path: Path,
) -> None:
    """Stimmt die Soll-Version aus dem Artefaktnamen mit der paketierten
    Version überein, ist die Prüfung grün und sagt das auch (#686)."""
    from bgremover import __version__

    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    output_json = tmp_path / "acceptance_extra.json"
    try:
        result = run_acceptance_extra(win, output_json, _V270_FIXTURE, __version__)
    finally:
        win.close()

    assert result.visible_version_ok, result.visible_version_message
    assert __version__ in result.visible_version_message
    assert json.loads(output_json.read_text(encoding="utf-8"))["visible_version"]["ok"] is True


def test_run_acceptance_extra_rejects_mismatching_expected_version(  # type: ignore[no-untyped-def]
    qapp, qtbot, tmp_path: Path,
) -> None:
    """Kernpunkt von #686: Ein Paket, dessen sichtbare Version nicht zum
    Artefaktnamen passt (falsch paketierte Version), muss auffallen – ohne
    externen Sollwert verglich die Prüfung das Paket nur mit sich selbst und
    wäre immer grün gewesen."""
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    output_json = tmp_path / "acceptance_extra.json"
    try:
        result = run_acceptance_extra(win, output_json, _V270_FIXTURE, "9.9.9")
    finally:
        win.close()

    assert not result.ok
    assert not result.visible_version_ok
    assert "9.9.9" in result.visible_version_message
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert payload["visible_version"]["ok"] is False
    # Die übrigen Prüfungen laufen trotzdem durch – der Fehlschlag darf sie
    # nicht verdecken, sonst wäre im Joblog nicht erkennbar, was sonst noch gilt.
    assert payload["v270_project_open"]["ok"] is True
    assert payload["project_copy"]["ok"] is True


def test_run_acceptance_extra_writes_and_reloads_a_controlled_project_copy(  # type: ignore[no-untyped-def]
    qapp, qtbot, tmp_path: Path,
) -> None:
    """#686: Der ``save_project``-Schreibpfad des gepackten Artefakts wird
    geprüft – ``write_export`` (EufyMake) deckt ihn nicht ab. Die v1-Fixture
    wird dabei kontrolliert auf die aktuelle Formatversion gehoben."""
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    output_json = tmp_path / "acceptance_extra.json"
    try:
        result = run_acceptance_extra(win, output_json, _V270_FIXTURE)
    finally:
        win.close()

    assert result.project_copy_ok, result.project_copy_message
    copy_path = tmp_path / "acceptance_extra_kopie.bgrproj"
    assert copy_path.is_file()
    with zipfile.ZipFile(copy_path) as zf:
        assert json.loads(zf.read("manifest.json"))["version"] == PROJECT_FORMAT_VERSION
    assert json.loads(output_json.read_text(encoding="utf-8"))["project_copy"]["ok"] is True


def test_run_acceptance_extra_project_copy_reports_write_failure(  # type: ignore[no-untyped-def]
    qapp, qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Negativkontrolle: Schlägt das Schreiben fehl, muss die Prüfung rot
    werden – nicht still durchgehen, weil ``_write_project`` seine Fehler nur
    in der Statusleiste meldet und keine Ausnahme wirft."""

    def boom(project, path):  # type: ignore[no-untyped-def]
        raise OSError("Ziel nicht beschreibbar")

    monkeypatch.setattr("bgremover.main_window.save_project", boom)

    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    output_json = tmp_path / "acceptance_extra.json"
    try:
        result = run_acceptance_extra(win, output_json, _V270_FIXTURE)
    finally:
        win.close()

    assert not result.ok
    assert not result.project_copy_ok
    assert "fehlgeschlagen" in result.project_copy_message


def test_visible_version_rejects_a_prefix_match_in_the_title(  # type: ignore[no-untyped-def]
    qapp, qtbot,
) -> None:
    """Codex-P2 (#734): ``"2.7.1" in "BgRemover Pro 2.7.10"`` ist wahr, obwohl
    der Titel eine **andere** Version zeigt. Genau der Fall – Titel aus einer
    anderen Quelle als ``__version__`` – ist der, den die Prüfung fangen soll;
    ein Substring-Test hätte ihn durchgewinkt."""
    from bgremover import __version__
    from bgremover.acceptance_smoke import _run_visible_version_smoke

    win = MainWindow()
    qtbot.addWidget(win)
    try:
        win.setWindowTitle(f"BgRemover Pro {__version__}0")
        ok, message = _run_visible_version_smoke(win, __version__)
        assert not ok
        assert f"{__version__}0" in message

        # Gegenprobe: der echte Titel bleibt grün.
        win.setWindowTitle(f"BgRemover Pro {__version__}")
        ok, _ = _run_visible_version_smoke(win, __version__)
        assert ok
    finally:
        win.close()


def test_visible_version_rejects_a_title_without_any_version(  # type: ignore[no-untyped-def]
    qapp, qtbot,
) -> None:
    """Ein Titel ganz ohne Versionsangabe ist ein Fehlschlag, kein stiller
    Durchlauf – sonst wäre der Nachweis „sichtbare Versionsnummer" wertlos."""
    from bgremover.acceptance_smoke import _run_visible_version_smoke

    win = MainWindow()
    qtbot.addWidget(win)
    try:
        win.setWindowTitle("BgRemover Pro")
        ok, message = _run_visible_version_smoke(win, None)
        assert not ok
        assert "keine Versionsangabe" in message
    finally:
        win.close()


def test_project_copy_detects_reordered_layers(qapp, qtbot, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Codex-P2 (#734): Ein Vergleich per Dict nach Ebenen-ID hielt eine
    vertauschte Ebenenreihenfolge – also ein sichtbar anderes Komposit – für
    gleich. Der Zustand wird deshalb geordnet verglichen."""
    from bgremover.acceptance_smoke import _project_state

    img = Image.new("RGBA", (8, 8), (1, 2, 3, 255))
    project = Project(8, 8, version=1)
    first = project.create_layer(img, name="A", kind=LayerKind.COLOR)
    second = project.create_layer(img, name="B", kind=LayerKind.COLOR)
    before = _project_state(project)

    project.move_layer(first.id, 1)
    assert _project_state(project) != before
    # Dieselbe Ebenenmenge, nur andere Reihenfolge – genau der Fall, den ein
    # Dict-Vergleich nach Ebenen-ID nicht bemerkt hätte.
    assert {first.id, second.id} == {layer.id for layer in project.layers}


def test_project_copy_detects_persisted_field_drift(qapp, qtbot) -> None:  # type: ignore[no-untyped-def]
    """Name, Sichtbarkeit, Deckkraft, Sperre und der Projektzustand gehören
    zum gespeicherten Zustand – ein Vergleich nur über IDs, Rollen und Pixel
    hätte eine Abweichung dort nicht bemerkt (Codex-P2, #734)."""
    from bgremover.acceptance_smoke import _project_state

    img = Image.new("RGBA", (8, 8), (1, 2, 3, 255))

    def fresh() -> Project:
        project = Project(8, 8, version=1, metadata={"physical_size_mm": [10.0, 10.0]})
        layer = project.create_layer(img, name="A", kind=LayerKind.COLOR)
        project.create_layer(img, name="B", kind=LayerKind.COLOR)
        project.set_active(layer.id)
        return project

    baseline = _project_state(fresh())
    for mutate in (
        lambda p: setattr(p.layers[0], "name", "anders"),
        lambda p: setattr(p.layers[0], "visible", False),
        lambda p: setattr(p.layers[0], "opacity", 0.5),
        lambda p: setattr(p.layers[0], "locked", True),
        lambda p: p.metadata.update({"physical_size_mm": [20.0, 20.0]}),
        lambda p: p.set_active(p.layers[1].id),
    ):
        drifted = fresh()
        mutate(drifted)
        assert _project_state(drifted) != baseline, mutate


def test_run_acceptance_extra_missing_component_restores_rembg_available(  # type: ignore[no-untyped-def]
    qapp, qtbot, tmp_path: Path,
) -> None:
    """Die Fehlende-Komponente-Prüfung erzwingt ``REMBG_AVAILABLE = False`` nur
    für ihre eigene Dauer und muss den Originalwert danach zurücksetzen –
    sonst würde eine erfolgreiche Prüfung den laufenden, gepackten Prozess
    dauerhaft in den "kein KI-Backend"-Zustand versetzen (#685-Review)."""
    import bgremover.main_window as main_window_module

    original = main_window_module.REMBG_AVAILABLE
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    output_json = tmp_path / "acceptance_extra.json"
    try:
        result = run_acceptance_extra(win, output_json, _V270_FIXTURE)
    finally:
        win.close()

    assert result.missing_component_ok, result.missing_component_message
    assert main_window_module.REMBG_AVAILABLE is original

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["missing_component"]["ok"] is True
