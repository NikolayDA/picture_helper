"""UI-Smoke-Tests für den „Größe ändern…"-Dialog (#359)."""
from __future__ import annotations

import pytest
from PIL import Image

from bgremover.resize_dialog import ResizeDialog


@pytest.mark.ui_smoke
def test_dialog_builds_and_seeds_current_size(qapp) -> None:
    dlg = ResizeDialog(640, 480)
    try:
        assert dlg.windowTitle() == "Größe ändern"
        assert dlg.selected_size() == (640, 480)
        assert dlg.selected_resample() == Image.Resampling.LANCZOS
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_dialog_aspect_lock_follows_edited_edge(qapp) -> None:
    dlg = ResizeDialog(100, 50)
    try:
        assert dlg._link.isChecked()
        dlg._w_spin.setValue(200)
        assert dlg.selected_size() == (200, 100)   # zweite Kante folgt proportional
        dlg._h_spin.setValue(25)
        assert dlg.selected_size() == (50, 25)
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_dialog_unlinked_keeps_edges_independent(qapp) -> None:
    dlg = ResizeDialog(100, 50)
    try:
        dlg._link.setChecked(False)
        dlg._w_spin.setValue(200)
        dlg._h_spin.setValue(33)
        assert dlg.selected_size() == (200, 33)
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_dialog_resample_choice_returns_pillow_enum(qapp) -> None:
    dlg = ResizeDialog(10, 10)
    try:
        idx = dlg._resample.findData(Image.Resampling.NEAREST)
        assert idx >= 0
        dlg._resample.setCurrentIndex(idx)
        assert dlg.selected_resample() == Image.Resampling.NEAREST
    finally:
        dlg.close()


# ── mm/DPI-Modus (#377) ──────────────────────────────────────────────────

@pytest.mark.ui_smoke
def test_pixel_mode_has_no_physical_size_by_default(qapp) -> None:
    dlg = ResizeDialog(100, 100)
    try:
        assert dlg.selected_physical_size_mm() is None
        assert dlg.selected_dpi() is None
        assert dlg.print_area_exceeded() is False
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_mm_mode_derives_pixel_size_from_mm_and_dpi(qapp) -> None:
    dlg = ResizeDialog(300, 300)
    try:
        dlg._mode.setCurrentIndex(1)  # mm
        dlg._link.setChecked(False)
        dlg._w_mm.setValue(25.4)
        dlg._h_mm.setValue(50.8)
        dlg._dpi.setValue(300)
        assert dlg.selected_size() == (300, 600)  # 25,4 mm @ 300 DPI = 300 px
        assert dlg.selected_physical_size_mm() == (25.4, 50.8)
        assert dlg.selected_dpi() == (300.0, 300.0)
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_mm_mode_dpi_change_updates_pixel_size(qapp) -> None:
    dlg = ResizeDialog(300, 300)
    try:
        dlg._mode.setCurrentIndex(1)
        dlg._link.setChecked(False)
        dlg._w_mm.setValue(25.4)
        dlg._h_mm.setValue(25.4)
        dlg._dpi.setValue(300)
        assert dlg.selected_size() == (300, 300)
        dlg._dpi.setValue(600)
        assert dlg.selected_size() == (600, 600)
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_mm_mode_aspect_lock_follows_edited_edge(qapp) -> None:
    dlg = ResizeDialog(100, 50)  # Seitenverhältnis 2:1
    try:
        dlg._mode.setCurrentIndex(1)
        assert dlg._link.isChecked()
        dlg._w_mm.setValue(200.0)
        assert dlg._h_mm.value() == 100.0  # Höhe folgt proportional
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_mm_mode_print_area_warning(qapp) -> None:
    dlg = ResizeDialog(100, 100)
    try:
        dlg._mode.setCurrentIndex(1)
        dlg._link.setChecked(False)
        dlg._w_mm.setValue(500.0)  # > A4-Breite (210 mm)
        assert dlg.print_area_exceeded() is True
        dlg._w_mm.setValue(100.0)
        dlg._h_mm.setValue(100.0)
        assert dlg.print_area_exceeded() is False
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_mm_mode_values_persist_via_project_round_trip(qapp, tmp_path) -> None:
    from bgremover.project_io import PROJECT_SUFFIX, load_project, save_project
    from bgremover.project_model import Project

    project = Project(300, 600)
    project.create_layer(Image.new("RGBA", (300, 600), (1, 2, 3, 255)), name="C")
    dlg = ResizeDialog(300, 600)
    try:
        dlg._mode.setCurrentIndex(1)
        dlg._link.setChecked(False)
        dlg._w_mm.setValue(25.4)
        dlg._h_mm.setValue(50.8)
        dlg._dpi.setValue(300)
        mm = dlg.selected_physical_size_mm()
    finally:
        dlg.close()
    assert mm is not None
    project.set_physical_size_mm(*mm)

    path = tmp_path / f"projekt{PROJECT_SUFFIX}"
    save_project(project, path)
    loaded = load_project(path)
    assert loaded.physical_size_mm == (25.4, 50.8)
    assert loaded.dpi == pytest.approx((300.0, 300.0))
