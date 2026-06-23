"""UI-Smoke-Tests für den EufyMake-Export-Dialog (#355).

Deckt das Options-Gating (Height/Gloss nur bei kompatibler Projektlage), die
Live-Befundanzeige (#354), die Blockierung bei Fehlern, die Warnungsbestätigung
und die abgefragten Optionen ab. Headless ohne qtbot – die Dialoge werden gebaut
und direkt inspiziert.
"""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from bgremover.eufymake_export_dialog import EufyMakeExportDialog
from bgremover.project_model import LayerKind, LayerRole, Project


def _solid(size: tuple[int, int], color: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", size, color)


def _grad(size: tuple[int, int]) -> Image.Image:
    w, h = size
    row = np.linspace(0, 255, num=w, dtype=np.uint8)
    grid = np.tile(row, (h, 1))
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = arr[:, :, 1] = arr[:, :, 2] = grid
    arr[:, :, 3] = 255
    return Image.fromarray(arr, "RGBA")


def _color_project(size: tuple[int, int] = (8, 4)) -> Project:
    project = Project(*size)
    project.create_layer(_solid(size, (10, 20, 30, 255)), name="Farbe")
    return project


def _with_height(project: Project, image: Image.Image | None = None) -> Project:
    layer = project.create_layer(
        image if image is not None else _grad(project.size),
        name="Höhe", kind=LayerKind.HEIGHT)
    project.assign_role(layer.id, LayerRole.HEIGHT_MAP)
    return project


def _with_gloss(project: Project, image: Image.Image | None = None) -> Project:
    layer = project.create_layer(
        image if image is not None else _grad(project.size),
        name="Gloss", kind=LayerKind.GLOSS)
    project.assign_role(layer.id, LayerRole.GLOSS_MASK)
    return project


@pytest.mark.ui_smoke
def test_dialog_builds_with_honest_title(qapp) -> None:
    dlg = EufyMakeExportDialog(_color_project())
    try:
        assert "EufyMake Studio" in dlg.windowTitle()
        # Keine Behauptung eines fertigen .empf-Projekts.
        assert ".empf" not in dlg.windowTitle()
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_optional_assets_disabled_without_layers(qapp) -> None:
    dlg = EufyMakeExportDialog(_color_project())
    try:
        assert not dlg._height_cb.isEnabled()
        assert not dlg._gloss_cb.isEnabled()
        assert dlg.selected_optional_roles() == []
        assert dlg._findings_label.text() == "Keine Beanstandungen."
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_optional_assets_enabled_with_layers(qapp) -> None:
    project = _with_gloss(_with_height(_color_project()))
    dlg = EufyMakeExportDialog(project)
    try:
        assert dlg._height_cb.isEnabled() and dlg._height_cb.isChecked()
        assert dlg._gloss_cb.isEnabled() and dlg._gloss_cb.isChecked()
        assert set(dlg.selected_optional_roles()) == {
            LayerRole.HEIGHT_MAP, LayerRole.GLOSS_MASK}
        dlg._height_cb.setChecked(False)
        assert dlg.selected_optional_roles() == [LayerRole.GLOSS_MASK]
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_defaults_can_uncheck_capable_assets(qapp) -> None:
    project = _with_height(_color_project())
    dlg = EufyMakeExportDialog(project, include_height=False)
    try:
        assert dlg._height_cb.isEnabled() and not dlg._height_cb.isChecked()
        assert dlg.selected_optional_roles() == []
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_export_button_needs_destination(qapp) -> None:
    dlg = EufyMakeExportDialog(_color_project())
    try:
        assert not dlg._export_btn.isEnabled()
        dlg._dest_edit.setText("/tmp/export")
        assert dlg._export_btn.isEnabled()
        assert dlg.selected_destination() == "/tmp/export"
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_warning_requires_explicit_confirmation(qapp) -> None:
    project = _with_gloss(_color_project())  # Gloss → Ink-Mode-Warnung
    dlg = EufyMakeExportDialog(project)
    try:
        dlg._dest_edit.setText("/tmp/export")
        assert not dlg._confirm.isHidden()
        # Warnung vorhanden, aber nicht bestätigt → Export gesperrt.
        assert not dlg._export_btn.isEnabled()
        dlg._confirm.setChecked(True)
        assert dlg._export_btn.isEnabled()
        assert dlg.warnings_confirmed() is True
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_16bit_adds_unconfirmed_warning(qapp) -> None:
    project = _with_height(_color_project())
    dlg = EufyMakeExportDialog(project)
    try:
        assert dlg.selected_bit_depth() == 8
        assert dlg._findings_label.text() == "Keine Beanstandungen."
        dlg._bit_combo.setCurrentIndex(dlg._bit_combo.findData(16))
        assert dlg.selected_bit_depth() == 16
        assert "16-Bit" in dlg._findings_label.text()
        assert not dlg._confirm.isHidden()
    finally:
        dlg.close()


@pytest.mark.ui_smoke
def test_blocking_error_keeps_export_disabled(qapp) -> None:
    # Versteckte einzige COLOR-Ebene + Height → kein Farbmotiv ableitbar (Fehler).
    project = Project(8, 4)
    hidden = project.create_layer(_solid((8, 4), (1, 2, 3, 255)), name="c")
    project.set_visible(hidden.id, False)
    _with_height(project)
    dlg = EufyMakeExportDialog(project)
    try:
        dlg._dest_edit.setText("/tmp/export")
        assert "⛔" in dlg._findings_label.text()
        # Trotz gesetztem Ziel bleibt der Export gesperrt.
        assert not dlg._export_btn.isEnabled()
    finally:
        dlg.close()
