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
