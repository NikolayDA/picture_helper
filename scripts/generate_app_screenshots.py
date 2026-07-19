"""Generate a reproducible BgRemover UI screenshot set.

The script drives the Qt widgets directly, using the offscreen platform by
default. For local visual acceptance runs it can switch to the native platform
and capture the real OpenGL-backed 3D relief viewer. It does not open native
file dialogs, does not run rembg, and replaces QSettings with an in-memory
implementation so local app preferences stay untouched.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_HEADLESS_QT_PLATFORMS = {"minimal", "minimalegl", "offscreen"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a full BgRemover UI screenshot set.")
    parser.add_argument(
        "--output-root",
        default="app_screenshots",
        help="Directory under which a timestamped screenshot folder is created.",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Exact output directory. Overrides --output-root when set.",
    )
    parser.add_argument("--width", type=int, default=1320)
    parser.add_argument("--height", type=int, default=820)
    parser.add_argument(
        "--qt-platform",
        choices=("offscreen", "native", "env"),
        default="offscreen",
        help=(
            "Qt platform to use. 'offscreen' is reproducible/headless; "
            "'native' enables live 3D OpenGL screenshots on a local desktop; "
            "'env' leaves QT_QPA_PLATFORM unchanged."
        ),
    )
    parser.add_argument(
        "--include-live-3d",
        action="store_true",
        help=(
            "Generate the full headless set, then overlay ready/adjusted 3D "
            "viewer screenshots from a native OpenGL-backed run."
        ),
    )
    parser.add_argument("--live-3d-only", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def _configure_qt_platform(mode: str) -> None:
    if mode == "offscreen":
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    elif mode == "native":
        if sys.platform == "darwin":
            os.environ["QT_QPA_PLATFORM"] = "cocoa"
        elif _is_headless_qt_platform(os.environ.get("QT_QPA_PLATFORM")):
            os.environ.pop("QT_QPA_PLATFORM", None)


def _is_headless_qt_platform(value: str | None) -> bool:
    if not value:
        return False
    return value.split(":", 1)[0].lower() in _HEADLESS_QT_PLATFORMS


def _run_hybrid_live_3d(args: argparse.Namespace, out: Path) -> int:
    script = Path(__file__).resolve()
    common_args = [
        sys.executable,
        str(script),
        "--output-dir",
        str(out),
        "--width",
        str(args.width),
        "--height",
        str(args.height),
    ]
    steps = [
        [*common_args, "--qt-platform", "offscreen"],
        [*common_args, "--qt-platform", "native", "--live-3d-only"],
    ]
    for step in steps:
        completed = subprocess.run(step, cwd=REPO_ROOT, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


class MemorySettings:
    """Small QSettings stand-in for screenshot generation."""

    _store: dict[str, object] = {}

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass

    def value(self, key: str, default: object = None, type: Any = None) -> object:
        value = self._store.get(key, default)
        if type is not None and value is not None:
            try:
                if type is bool and isinstance(value, str):
                    return value.lower() in {"1", "true", "yes", "on"}
                return type(value)
            except Exception:
                return default
        return value

    def setValue(self, key: str, value: object) -> None:
        self._store[key] = value

    def remove(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def sync(self) -> None:
        pass


def main() -> int:
    args = _parse_args()

    if args.output_dir:
        out = Path(args.output_dir).expanduser()
    else:
        out = REPO_ROOT / args.output_root / f"bgremover_complete_{datetime.now():%Y%m%d_%H%M%S}"
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "_runtime").mkdir(exist_ok=True)
    (out / "_exports").mkdir(exist_ok=True)

    if args.include_live_3d and not args.live_3d_only:
        return _run_hybrid_live_3d(args, out)

    _configure_qt_platform(args.qt_platform)

    from bgremover.qt_plugins import ensure_qt_plugin_path

    ensure_qt_plugin_path()

    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from PyQt6.QtCore import QPoint
    from PyQt6.QtGui import QColor, QPalette
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import (
        QApplication,
        QColorDialog,
        QInputDialog,
        QMessageBox,
    )

    import bgremover.main_window as main_window_mod
    import bgremover.settings_dialog as settings_dialog_mod
    from bgremover import __version__
    from bgremover.ai_install_dialog import AiInstallDialog
    from bgremover.ai_model_dialog import AiModelDialog
    from bgremover.ai_model_status import ModelStatus, ModelStatusResult
    from bgremover.color_ops import adjust_color
    from bgremover.constants import TOOL_BRUSH, TOOL_ERASER, TOOL_LASSO, TOOL_WAND
    from bgremover.eufymake_export_dialog import EufyMakeExportDialog
    from bgremover.i18n import tr
    from bgremover.image_ops import remove_selection
    from bgremover.main_window import MainWindow
    from bgremover.preview3d_capability import UNAVAILABLE_KEY, RendererCapability
    from bgremover.preview_mode import PreviewMode
    from bgremover.relief_mesh import MeshQuality, build_relief_mesh
    from bgremover.resize_dialog import ResizeDialog
    from bgremover.settings_dialog import SettingsDialog
    from bgremover.stepper import WorkflowStep
    from bgremover.theme import _Theme

    app = QApplication.instance() or QApplication([])
    app.setApplicationName("BgRemover")
    app.setOrganizationName("BgRemover")
    app.setStyle("Fusion")
    _install_dark_palette(app, QColor, QPalette)

    main_window_mod.QSettings = MemorySettings
    main_window_mod.MainWindow._start_rembg_warmup = lambda self: None
    main_window_mod.MainWindow._confirm_discard_changes = lambda self: True
    fake_log = out / "_runtime" / "bgremover.log"
    fake_log.write_text("Screenshot run log placeholder\n", encoding="utf-8")
    settings_dialog_mod.current_log_file = lambda: fake_log

    records: list[tuple[str, str, int, int]] = []

    def process(ms: int = 40) -> None:
        app.processEvents()
        if ms:
            QTest.qWait(ms)
            app.processEvents()

    def snap(widget: object, filename: str, label: str, wait_ms: int = 80) -> None:
        process(wait_ms)
        pix = widget.grab()
        if not pix.save(str(out / filename)):
            raise RuntimeError(f"Could not save screenshot: {out / filename}")
        records.append((filename, label, pix.width(), pix.height()))

    def snap_dialog(widget: object, filename: str, label: str, wait_ms: int = 80) -> None:
        widget.show()
        snap(widget, filename, label, wait_ms=wait_ms)
        widget.close()
        process(40)

    def wait_preview3d_state(state: str, *, attempts: int = 30, delay_ms: int = 80) -> bool:
        for _ in range(attempts):
            process(delay_ms)
            if window._relief3d_view.state == state:
                return True
        return False

    def use_sync_mesh_builder(*, fail: bool = False) -> None:
        def start_mesh_build(
            field: object,
            quality: object,
            generation_id: int,
            on_done: object,
            *,
            on_error: object | None = None,
            physical_size_mm: tuple[float, float] | None = None,
        ) -> bool:
            if fail:
                if callable(on_error):
                    on_error("Screenshot-Demo: 3D-Mesh-Aufbau fehlgeschlagen.", generation_id)
                return False
            if not isinstance(quality, MeshQuality):
                raise TypeError(f"Unexpected mesh quality: {quality!r}")
            mesh = build_relief_mesh(
                field,
                quality,
                physical_size_mm=physical_size_mm,
            )
            if callable(on_done):
                on_done(mesh, generation_id)
            return True

        window._worker_controller.start_mesh_build = start_mesh_build
        window._worker_controller.cancel_mesh_build = lambda: None

    sample_path = out / "_runtime" / "sample_bgremover.png"
    sample_img = _make_sample_image(sample_path, Image, ImageDraw, ImageFont)
    background_mask, small_selection = _sample_masks(sample_img, np)

    window = MainWindow()
    window.resize(args.width, args.height)
    window.show()
    process(160)

    def set_step(step: WorkflowStep) -> None:
        """Navigiert den geführten Workflow wie ein Klick auf die Schrittleiste.

        Läuft über den gegateten Navigationspfad des MainWindow (Stepper,
        rechtes Panel, kontextuelle Werkzeugleiste werden gemeinsam
        umgeschaltet). Bricht hart ab, statt still falsche Screenshots zu
        erzeugen, falls der Schritt gesperrt bleibt (z. B. ohne Bild).
        """
        window._on_step_selected(int(step))
        process(60)
        if window._step is not step:
            raise RuntimeError(f"Workflow step not reachable: {step.name}")

    def load_sample(mask: np.ndarray | None = None, status: str | None = None) -> None:
        window._canvas.apply_loaded_image(sample_img.copy(), str(sample_path))
        if mask is not None:
            window._canvas._mask = mask.copy()
            window._canvas._refresh_overlay()
        window._canvas.fit_to_view()
        if status:
            window._sb.showMessage(status)
        process(100)

    def capture_live_preview3d_states() -> None:
        load_sample(None, "3D-Reliefvorschau aktiviert")
        window._canvas.generate_height_map()
        set_step(WorkflowStep.RELIEF)
        capability = window._preview3d._capability_probe()
        if not capability.ok:
            raise RuntimeError(
                "Live 3D screenshots requested, but no OpenGL 2.1 renderer is available: "
                f"{capability.detail or capability.error_key or 'unknown'}"
            )
        window._preview3d._debounce.setInterval(10_000)
        window._set_preview3d_mode(True)
        if not wait_preview3d_state("loading", attempts=10):
            raise RuntimeError("3D preview did not enter loading state")
        snap(window, "75_function_preview3d_loading.png", "Funktion: 3D-Reliefvorschau berechnet Mesh")

        use_sync_mesh_builder()
        window._preview3d._debounce.stop()
        window._preview3d._start_build()
        if not wait_preview3d_state("ready", attempts=30):
            raise RuntimeError("3D preview did not reach ready state")
        process(250)
        snap(window, "76_function_preview3d_ready.png", "Funktion: 3D-Reliefvorschau gerendert")

        window._set_preview3d_exaggeration(3.0)
        window._set_preview3d_light(125.0, 70.0)
        window._sync_preview3d_controls()
        viewer = window._relief3d_view.viewer()
        if viewer is not None:
            viewer.camera.orbit(28.0, 14.0)
            viewer.update()
        process(250)
        snap(window, "77_function_preview3d_adjusted.png", "Funktion: 3D-Reliefvorschau mit Anzeigeparametern")
        window._set_preview3d_mode(False)

        set_step(WorkflowStep.RELIEF)
        use_sync_mesh_builder(fail=True)
        window._preview3d._capability_probe = lambda: RendererCapability(ok=True, diagnostic="screenshot")
        window._preview3d._debounce.setInterval(10_000)
        window._set_preview3d_mode(True)
        window._preview3d._debounce.stop()
        window._preview3d._start_build()
        if not wait_preview3d_state("error", attempts=10):
            raise RuntimeError("3D preview did not enter error state")
        snap(window, "78_function_preview3d_error.png", "Funktion: 3D-Reliefvorschau Fehlerzustand")
        window._set_preview3d_mode(False)

    if args.live_3d_only:
        labels = _read_manifest_labels(out)
        capture_live_preview3d_states()
        labels.update({filename: label for filename, label, _width, _height in records})
        refreshed = _refresh_output_index(out, labels, Image, ImageDraw, ImageFont, live_3d=True)
        window._saved_revision = window._canvas.content_revision
        window.close()
        app.quit()
        print(out)
        print(f"screenshots={len([r for r in refreshed if r[0].endswith('.png')])}")
        return 0

    snap(window, "01_main_empty.png", "Hauptfenster ohne geladenes Bild")

    load_sample(background_mask, "Beispielbild geladen, Hintergrundbereich ausgewaehlt")
    snap(window, "02_main_loaded_selection.png", "Hauptfenster mit Beispielbild und Auswahlmaske")

    toolbar = window.toolbar
    for filename, label, button, tool in [
        ("03_tool_wand.png", "Werkzeug: Zauberstab", toolbar.btn_wand, TOOL_WAND),
        ("04_tool_brush.png", "Werkzeug: Pinsel", toolbar.btn_brush, TOOL_BRUSH),
        ("05_tool_eraser.png", "Werkzeug: Radiergummi", toolbar.btn_eraser, TOOL_ERASER),
        ("06_tool_lasso.png", "Werkzeug: Polygon-Lasso", toolbar.btn_lasso, TOOL_LASSO),
    ]:
        button.setChecked(True)
        window._set_tool(tool)
        window._sb.showMessage(label)
        snap(window, filename, label, wait_ms=60)

    for step, filename, label in [
        (WorkflowStep.OPEN, "10_step_1_open.png", "Workflow Schritt 1: Oeffnen"),
        (WorkflowStep.CUTOUT, "11_step_2_cutout.png", "Workflow Schritt 2: Freistellen"),
        (WorkflowStep.ADJUST, "12_step_3_adjust.png", "Workflow Schritt 3: Anpassen"),
        (WorkflowStep.SHAPE, "13_step_4_shape.png", "Workflow Schritt 4: Form und Masse"),
        (WorkflowStep.RELIEF, "14_step_5_relief.png", "Workflow Schritt 5: Relief und Ebenen"),
        (WorkflowStep.EXPORT, "15_step_6_export.png", "Workflow Schritt 6: Export"),
    ]:
        set_step(step)
        window._sb.showMessage(label)
        snap(window, filename, label)

    menu_bar = window.menuBar()
    menus = {action.text(): action.menu() for action in menu_bar.actions() if action.menu() is not None}

    def snap_menu(menu: object, filename: str, label: str) -> None:
        menu.ensurePolished()
        menu.adjustSize()
        menu.popup(window.mapToGlobal(QPoint(30, 30)))
        process(100)
        snap(menu, filename, label, wait_ms=20)
        menu.hide()
        process(30)

    for title, filename, label in [
        ("Datei", "20_menu_file.png", "Menue: Datei"),
        ("Projekt", "22_menu_project.png", "Menue: Projekt"),
        ("Bearbeiten", "23_menu_edit.png", "Menue: Bearbeiten"),
        ("Ansicht", "24_menu_view.png", "Menue: Ansicht"),
        ("Extras", "26_menu_extras.png", "Menue: Extras"),
    ]:
        if title in menus:
            snap_menu(menus[title], filename, label)
    if "Datei" in menus:
        recent_menu = next((a.menu() for a in menus["Datei"].actions() if a.text() == "Zuletzt geoeffnet" or a.text() == "Zuletzt geöffnet"), None)
        if recent_menu is not None:
            snap_menu(recent_menu, "21_menu_recent_files.png", "Untermenue: Zuletzt geoeffnet")
    if "Ansicht" in menus:
        preview_menu = next((a.menu() for a in menus["Ansicht"].actions() if a.menu() is not None), None)
        if preview_menu is not None:
            snap_menu(preview_menu, "25_menu_preview_mode.png", "Untermenue: Vorschaumodus")

    settings_dlg = SettingsDialog(window._settings, window)
    settings_dlg.resize(760, 620)
    settings_dlg.show()
    snap(settings_dlg, "30_dialog_settings.png", "Dialog: Einstellungen")
    settings_dlg.close()
    process(40)

    color_dlg = QColorDialog(QColor(_Theme.ACCENT), window)
    color_dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
    color_dlg.setWindowTitle("Hintergrundfarbe waehlen")
    color_dlg.resize(720, 520)
    color_dlg.show()
    snap(color_dlg, "31_dialog_color_picker.png", "Dialog: Hintergrundfarbe waehlen")
    color_dlg.close()
    process(40)

    warning = QMessageBox(window)
    warning.setIcon(QMessageBox.Icon.Warning)
    warning.setWindowTitle("Ungueltiges Verzeichnis")
    warning.setText("Standard-Verzeichnis zum Oeffnen ist kein existierendes Verzeichnis:")
    warning.setInformativeText("/pfad/der/nicht/existiert")
    warning.setStandardButtons(QMessageBox.StandardButton.Ok)
    warning.resize(600, 260)
    warning.show()
    snap(warning, "32_dialog_warning.png", "Dialog: Warnmeldung bei ungueltiger Einstellung")
    warning.close()
    process(40)

    unsaved = QMessageBox(window)
    unsaved.setIcon(QMessageBox.Icon.Warning)
    unsaved.setWindowTitle("Ungespeicherte Aenderungen")
    unsaved.setText("Das aktuelle Bild enthaelt ungespeicherte Aenderungen.")
    unsaved.setInformativeText("Moechtest du vor dem Fortfahren speichern?")
    unsaved.setStandardButtons(
        QMessageBox.StandardButton.Save
        | QMessageBox.StandardButton.Discard
        | QMessageBox.StandardButton.Cancel
    )
    unsaved.resize(620, 260)
    unsaved.show()
    snap(unsaved, "33_dialog_unsaved_changes.png", "Dialog: Ungespeicherte Aenderungen")
    unsaved.close()
    process(40)

    rename_dlg = QInputDialog(window)
    rename_dlg.setWindowTitle("Ebene umbenennen")
    rename_dlg.setLabelText("Neuer Name:")
    rename_dlg.setTextValue("Motiv")
    rename_dlg.resize(460, 180)
    rename_dlg.show()
    snap(rename_dlg, "34_dialog_rename_layer.png", "Dialog: Ebene umbenennen")
    rename_dlg.close()
    process(40)

    resize_dlg = ResizeDialog(sample_img.width, sample_img.height, window)
    resize_dlg.resize(520, 420)
    resize_dlg.show()
    snap(resize_dlg, "35_dialog_resize_pixels.png", "Dialog: Groesse aendern Pixelmodus")
    resize_dlg._mode.setCurrentIndex(1)
    process(80)
    snap(resize_dlg, "36_dialog_resize_mm.png", "Dialog: Groesse aendern mm/DPI-Modus")
    resize_dlg.close()
    process(40)

    def model_status(status: ModelStatus, *, size_bytes: int | None = None) -> ModelStatusResult:
        return ModelStatusResult(
            status=status,
            model_path=Path("/tmp/bgremover-model/u2net.onnx"),
            size_bytes=size_bytes,
        )

    ai_model_missing = AiModelDialog(
        status_provider=lambda: model_status(ModelStatus.NOT_DOWNLOADED),
        parent=window,
    )
    ai_model_missing.resize(560, 260)
    snap_dialog(ai_model_missing, "38_dialog_ai_model_missing.png", "Dialog: KI-Modell verwalten, Modell fehlt")

    ai_model_downloading = AiModelDialog(
        status_provider=lambda: model_status(ModelStatus.NOT_DOWNLOADED),
        parent=window,
    )
    ai_model_downloading.resize(560, 280)
    ai_model_downloading.start_downloading()
    snap_dialog(ai_model_downloading, "39_dialog_ai_model_downloading.png", "Dialog: KI-Modell verwalten, Download laeuft")

    ai_model_error = AiModelDialog(
        status_provider=lambda: model_status(ModelStatus.NOT_DOWNLOADED),
        parent=window,
    )
    ai_model_error.resize(560, 300)
    ai_model_error.download_failed("Screenshot-Demo: Modell-Download nicht erreichbar.")
    snap_dialog(ai_model_error, "45_dialog_ai_model_error.png", "Dialog: KI-Modell verwalten, Fehler und Retry")

    ai_model_ready = AiModelDialog(
        status_provider=lambda: model_status(ModelStatus.DOWNLOADED, size_bytes=176_300_000),
        parent=window,
    )
    ai_model_ready.resize(560, 260)
    snap_dialog(ai_model_ready, "46_dialog_ai_model_ready.png", "Dialog: KI-Modell verwalten, Modell vorhanden")

    ai_install = AiInstallDialog(
        status_provider=lambda: model_status(ModelStatus.REMBG_UNAVAILABLE),
        platform="darwin",
        python_version=(3, 11),
        parent=window,
    )
    ai_install.resize(640, 380)
    snap_dialog(ai_install, "47_dialog_ai_install_backend.png", "Dialog: KI-Hintergrundentfernung installieren")

    update_available = QMessageBox(window)
    update_available.setIcon(QMessageBox.Icon.Information)
    update_available.setWindowTitle(tr("dialog.update_check.title"))
    update_available.setText(tr("dialog.update_check.available.body", current=__version__, latest="v9.9.9"))
    update_available.addButton(tr("dialog.update_check.open_release"), QMessageBox.ButtonRole.ActionRole)
    update_available.addButton(QMessageBox.StandardButton.Close)
    update_available.resize(560, 220)
    snap_dialog(update_available, "48_dialog_update_available.png", "Dialog: Update verfuegbar")

    update_current = QMessageBox(window)
    update_current.setIcon(QMessageBox.Icon.Information)
    update_current.setWindowTitle(tr("dialog.update_check.title"))
    update_current.setText(tr("dialog.update_check.up_to_date.body", version=__version__))
    update_current.setStandardButtons(QMessageBox.StandardButton.Ok)
    update_current.resize(520, 180)
    snap_dialog(update_current, "49_dialog_update_current.png", "Dialog: App ist aktuell")

    update_failed = QMessageBox(window)
    update_failed.setIcon(QMessageBox.Icon.Warning)
    update_failed.setWindowTitle(tr("dialog.update_check.title"))
    update_failed.setText(tr("dialog.update_check.failed.body"))
    update_failed.setStandardButtons(QMessageBox.StandardButton.Ok)
    update_failed.resize(520, 180)
    snap_dialog(update_failed, "49b_dialog_update_failed.png", "Dialog: Update-Check fehlgeschlagen")

    load_sample(None, "Hoehenkarte erzeugt")
    window._canvas.generate_height_map()
    set_step(WorkflowStep.RELIEF)
    snap(window, "40_function_height_generated.png", "Funktion: Hoehenkarte erzeugen")

    project_for_export = window._canvas.project
    if project_for_export is not None:
        eufy_dlg = EufyMakeExportDialog(
            project_for_export,
            include_height=True,
            include_gloss=True,
            bit_depth=8,
            dest_dir=str(out / "_exports" / "eufymake_import_assets"),
            parent=window,
        )
        eufy_dlg.resize(700, 660)
        eufy_dlg.show()
        snap(eufy_dlg, "37_dialog_eufymake_export.png", "Dialog: EufyMake Studio Import-Assets exportieren")
        eufy_dlg.close()
        process(40)

    for mode, filename, label in [
        (PreviewMode.RELIEF, "41_preview_relief.png", "Vorschau: Relief"),
        (PreviewMode.HEIGHT, "42_preview_height.png", "Vorschau: Hoehenkarte"),
        (PreviewMode.COMBINED, "43_preview_combined.png", "Vorschau: Kombiniert"),
    ]:
        window._canvas.set_preview_mode(mode)
        set_step(WorkflowStep.EXPORT)
        window._sb.showMessage(label)
        snap(window, filename, label)
    window._canvas.set_preview_mode(PreviewMode.COLOR)

    load_sample(None, "Verlauf mit Bearbeitungsschritten")
    window._canvas.apply_rotate(90)
    window._canvas.apply_flip(True)
    window._canvas.apply_round_corners(70)
    window._history_popup.toggle()
    process(120)
    if window._history_popup._popup is not None:
        snap(window._history_popup._popup, "44_popup_history.png", "Popup: Aenderungshistorie")
        window._history_popup._popup.hide()
    process(40)

    load_sample(small_selection, "Auswahl vor Morphologie")
    window._canvas.expand_selection(35)
    set_step(WorkflowStep.CUTOUT)
    snap(window, "50_function_selection_expand.png", "Funktion: Auswahl erweitern")
    window._canvas.shrink_selection(18)
    snap(window, "51_function_selection_shrink.png", "Funktion: Auswahl schrumpfen")

    load_sample(background_mask, "Hintergrundauswahl fuer Entfernen")
    set_step(WorkflowStep.CUTOUT)
    window._canvas.apply_remove()
    window._canvas.fit_to_view()
    snap(window, "52_function_remove_background.png", "Funktion: Hintergrund transparent entfernen")
    window._canvas.feather_active_edges(4)
    window._canvas.fit_to_view()
    snap(window, "53_function_feather_edges.png", "Funktion: Alphakanten glaetten")

    load_sample(background_mask, "Hintergrundauswahl fuer Farbe ersetzen")
    window._bg_color = QColor("#f6c445")
    window._update_color_btn()
    set_step(WorkflowStep.CUTOUT)
    window._canvas.apply_replace(window._bg_color)
    window._canvas.fit_to_view()
    snap(window, "54_function_replace_color.png", "Funktion: Hintergrundfarbe ersetzen")

    load_sample(background_mask, "Simuliertes KI-Ergebnis ohne Modellaufruf")
    ai_result = remove_selection(np.asarray(sample_img.convert("RGBA")), background_mask)
    window._canvas.apply_ai_result(ai_result)
    window._canvas.fit_to_view()
    snap(window, "55_function_ai_result.png", "Funktion: KI-Hintergrundentfernung Ergebnis")

    load_sample(None, "Farbkorrektur Vorschau")
    set_step(WorkflowStep.ADJUST)

    def color_op(img: object) -> object:
        return adjust_color(img, brightness=1.18, contrast=1.22, saturation=0.72)

    window._canvas.preview_color_op(color_op)
    window._canvas.fit_to_view()
    snap(window, "56_function_adjust_preview.png", "Funktion: Farbkorrektur Live-Vorschau")
    window._canvas.apply_color_op(color_op)
    window._canvas.fit_to_view()
    snap(window, "57_function_adjust_apply.png", "Funktion: Farbkorrektur anwenden")

    load_sample(None, "Freier Winkel angewendet")
    set_step(WorkflowStep.SHAPE)
    window._canvas.apply_rotate(27)
    window._canvas.fit_to_view()
    snap(window, "58_function_rotate_free_angle.png", "Funktion: Freier Drehwinkel")

    load_sample(None, "Horizontal gespiegelt")
    set_step(WorkflowStep.SHAPE)
    window._canvas.apply_flip(True)
    window._canvas.fit_to_view()
    snap(window, "59_function_flip_horizontal.png", "Funktion: Horizontal spiegeln")

    load_sample(None, "Groesse geaendert")
    set_step(WorkflowStep.SHAPE)
    window._canvas.apply_resize(640, 426)
    window._canvas.fit_to_view()
    snap(window, "60_function_resize.png", "Funktion: Groesse aendern")

    load_sample(None, "Ecken abgerundet")
    set_step(WorkflowStep.SHAPE)
    window._canvas.apply_round_corners(95)
    window._canvas.fit_to_view()
    snap(window, "61_function_round_corners.png", "Funktion: Ecken abrunden")

    load_sample(None, "Quadratischer Zuschnitt aktiv")
    set_step(WorkflowStep.SHAPE)
    window._canvas.start_crop_ratio(1, 1)
    window._canvas.fit_to_view()
    snap(window, "62_crop_ratio_overlay.png", "Zuschnitt: 1:1 Overlay mit Bestaetigungsleiste")
    window._canvas.cancel_crop()

    load_sample(None, "Kreis-Zuschnitt aktiv")
    set_step(WorkflowStep.SHAPE)
    window._canvas.start_crop_circle()
    window._canvas.fit_to_view()
    snap(window, "63_crop_circle_overlay.png", "Zuschnitt: Kreis Overlay mit Bestaetigungsleiste")
    window._canvas.confirm_crop()
    window._canvas.fit_to_view()
    snap(window, "64_crop_circle_confirmed.png", "Zuschnitt: Kreis angewendet")

    load_sample(None, "Ebenen bearbeitet")
    window._canvas.duplicate_active_layer()
    active_id = window._canvas.project.active_layer_id if window._canvas.project is not None else None
    if active_id is not None:
        window._canvas.rename_active_layer("Motiv Kopie")
        window._canvas.set_layer_opacity(active_id, 0.55)
    set_step(WorkflowStep.RELIEF)
    snap(window, "70_function_layers_duplicate_opacity.png", "Funktion: Ebene duplizieren und Opazitaet setzen")
    window._canvas.add_layer()
    set_step(WorkflowStep.RELIEF)
    snap(window, "71_function_layers_add.png", "Funktion: Neue Ebene hinzufuegen")

    load_sample(None, "Hoehenkarte bearbeiten")
    window._canvas.generate_height_map()
    set_step(WorkflowStep.RELIEF)
    window._canvas.lighten_active_height(32)
    window._canvas.fit_to_view()
    snap(window, "72_function_height_lighten.png", "Funktion: Hoehenkarte aufhellen")
    window._canvas.invert_active_height()
    window._canvas.fit_to_view()
    snap(window, "73_function_height_invert.png", "Funktion: Hoehenkarte invertieren")
    window._canvas.preview_height_op(lambda field: field)
    window._canvas.apply_height_op(lambda field: field)
    window._canvas.fit_to_view()
    snap(window, "74_function_height_optimize_apply.png", "Funktion: Hoehen-Optimierung anwenden")

    load_sample(None, "3D-Reliefvorschau aktiviert")
    window._canvas.generate_height_map()
    set_step(WorkflowStep.RELIEF)
    if args.include_live_3d:
        capture_live_preview3d_states()
    else:
        window._preview3d._capability_probe = lambda: RendererCapability(ok=True, diagnostic="screenshot")
        window._preview3d._debounce.setInterval(10_000)
        window._set_preview3d_mode(True)
        process(120)
        snap(window, "75_function_preview3d_loading.png", "Funktion: 3D-Reliefvorschau aktiv")
        window._set_preview3d_mode(False)

    window._preview3d._capability_probe = lambda: RendererCapability(
        ok=False,
        error_key=UNAVAILABLE_KEY,
        detail="Screenshot-Headless-Fallback",
    )
    window._preview3d._debounce.setInterval(200)
    window._preview3d_capability = None
    window._set_preview3d_mode(True)
    process(120)
    snap(window, "79_function_preview3d_fallback.png", "Funktion: 3D-Reliefvorschau Headless-Fallback")
    window._set_preview3d_mode(False)

    load_sample(None, "Speichern ausgefuehrt")
    save_path = out / "_exports" / "saved_sample.png"
    window._canvas.save_image(str(save_path))
    snap(window, "80_function_save_status.png", "Funktion: Bild speichern Statusmeldung")
    project_path = out / "_exports" / "sample_project.bgrproj"
    window._write_project(str(project_path))
    snap(window, "81_function_project_save_status.png", "Funktion: Projekt speichern Statusmeldung")

    _write_contact_sheet(out, records, Image, ImageDraw, ImageFont)
    records.insert(0, _image_record(out / "00_contact_sheet.png", "Uebersicht aller erstellten Screenshots", Image))
    _write_manifest(out, records, live_3d=args.include_live_3d)

    window._saved_revision = window._canvas.content_revision
    window.close()
    QApplication.closeAllWindows()
    process(120)

    print(out)
    print(f"screenshots={len([r for r in records if r[0].endswith('.png')])}")
    return 0


def _install_dark_palette(app: object, QColor: Any, QPalette: Any) -> None:
    palette = QPalette()
    dark = QColor(30, 30, 30)
    for role, color in [
        (QPalette.ColorRole.Window, QColor(37, 37, 37)),
        (QPalette.ColorRole.WindowText, QColor(220, 220, 220)),
        (QPalette.ColorRole.Base, dark),
        (QPalette.ColorRole.AlternateBase, QColor(53, 53, 53)),
        (QPalette.ColorRole.Text, QColor(220, 220, 220)),
        (QPalette.ColorRole.Button, QColor(53, 53, 53)),
        (QPalette.ColorRole.ButtonText, QColor(220, 220, 220)),
        (QPalette.ColorRole.Highlight, QColor(74, 144, 217)),
        (QPalette.ColorRole.HighlightedText, QColor(255, 255, 255)),
        (QPalette.ColorRole.ToolTipBase, QColor(50, 50, 50)),
        (QPalette.ColorRole.ToolTipText, QColor(220, 220, 220)),
    ]:
        palette.setColor(role, color)
    app.setPalette(palette)


def _load_bundled_font(ImageFont: Any, size: int) -> object:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _make_sample_image(path: Path, Image: Any, ImageDraw: Any, ImageFont: Any) -> object:
    width, height = 900, 600
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(1, height - 1)
        draw.line(
            (0, y, width, y),
            fill=(int(43 + 45 * t), int(128 + 52 * (1 - t)), int(166 + 30 * t), 255),
        )
    draw.rounded_rectangle((80, 70, 820, 530), radius=42, fill=(245, 247, 240, 245), outline=(255, 255, 255, 255), width=5)
    draw.ellipse((220, 120, 660, 520), fill=(235, 76, 96, 255), outline=(120, 38, 54, 255), width=8)
    draw.polygon([(110, 475), (335, 180), (520, 475)], fill=(40, 167, 126, 230), outline=(16, 95, 74, 255))
    draw.rounded_rectangle((560, 165, 770, 360), radius=28, fill=(44, 104, 219, 235), outline=(19, 62, 150, 255), width=6)
    draw.arc((260, 170, 620, 500), start=205, end=330, fill=(255, 238, 128, 255), width=22)
    draw.line((135, 120, 780, 470), fill=(33, 43, 54, 80), width=18)
    font_big = _load_bundled_font(ImageFont, 80)
    font_small = _load_bundled_font(ImageFont, 34)
    draw.text((330, 245), "BG", fill=(255, 255, 255, 245), font=font_big, anchor="mm")
    draw.text((610, 405), "Sample", fill=(36, 47, 58, 230), font=font_small, anchor="mm")
    img.save(path)
    return img


def _sample_masks(sample_img: object, np: Any) -> tuple[object, object]:
    width, height = sample_img.size
    yy, xx = np.ogrid[:height, :width]
    object_ellipse = ((xx - 450) / 250) ** 2 + ((yy - 320) / 230) ** 2 <= 1
    object_rect = (xx > 540) & (xx < 790) & (yy > 135) & (yy < 395)
    object_tri = (
        (xx > 105)
        & (xx < 535)
        & (yy > 170)
        & (yy < 500)
        & (yy > (-1.35 * xx + 650))
        & (yy > (1.55 * xx - 20))
    )
    background_mask = ~(object_ellipse | object_rect | object_tri)
    small_selection = ((xx - 450) / 130) ** 2 + ((yy - 310) / 95) ** 2 <= 1
    return background_mask, small_selection


def _write_contact_sheet(out: Path, records: list[tuple[str, str, int, int]], Image: Any, ImageDraw: Any, ImageFont: Any) -> None:
    thumbs = []
    for filename, label, _width, _height in records:
        img = Image.open(out / filename).convert("RGB")
        img.thumbnail((360, 220), Image.Resampling.LANCZOS)
        thumbs.append((filename, label, img.copy()))
    font_label = _load_bundled_font(ImageFont, 16)
    font_title = _load_bundled_font(ImageFont, 22)
    cols = 3
    cell_w, cell_h = 400, 285
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, 74 + rows * cell_h), (28, 28, 28))
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 22), "BgRemover Screenshot-Uebersicht", fill=(235, 235, 235), font=font_title)
    for idx, (filename, label, img) in enumerate(thumbs):
        col = idx % cols
        row = idx // cols
        x = col * cell_w + 20
        y = 74 + row * cell_h + 12
        frame = Image.new("RGB", (360, 220), (48, 48, 48))
        px = x + (360 - img.width) // 2
        py = y + (220 - img.height) // 2
        sheet.paste(frame, (x, y))
        sheet.paste(img, (px, py))
        draw.text((x, y + 228), filename, fill=(135, 190, 245), font=font_label)
        short = label[:44] + ("..." if len(label) > 44 else "")
        draw.text((x, y + 250), short, fill=(220, 220, 220), font=font_label)
    sheet.save(out / "00_contact_sheet.png")


def _image_record(path: Path, label: str, Image: Any) -> tuple[str, str, int, int]:
    img = Image.open(path)
    return path.name, label, img.width, img.height


def _read_manifest_labels(out: Path) -> dict[str, str]:
    manifest = out / "manifest.md"
    if not manifest.exists():
        return {}
    labels: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        filename = cells[0].strip("`")
        if filename:
            labels[filename] = cells[1]
    return labels


def _folder_image_records(
    out: Path,
    labels: dict[str, str],
    Image: Any,
) -> list[tuple[str, str, int, int]]:
    records: list[tuple[str, str, int, int]] = []
    for path in sorted(out.glob("*.png")):
        if path.name == "00_contact_sheet.png":
            continue
        label = labels.get(path.name, path.stem.replace("_", " "))
        records.append(_image_record(path, label, Image))
    return records


def _refresh_output_index(
    out: Path,
    labels: dict[str, str],
    Image: Any,
    ImageDraw: Any,
    ImageFont: Any,
    *,
    live_3d: bool,
) -> list[tuple[str, str, int, int]]:
    records = _folder_image_records(out, labels, Image)
    _write_contact_sheet(out, records, Image, ImageDraw, ImageFont)
    records.insert(0, _image_record(out / "00_contact_sheet.png", "Uebersicht aller erstellten Screenshots", Image))
    _write_manifest(out, records, live_3d=live_3d)
    return records


def _write_manifest(
    out: Path,
    records: list[tuple[str, str, int, int]],
    *,
    live_3d: bool = False,
) -> None:
    lines = [
        "# BgRemover Screenshots",
        "",
        "Quelle: Repository-Root",
        "",
        "| Datei | Inhalt | Pixel |",
        "|---|---|---:|",
    ]
    for filename, label, width, height in records:
        lines.append(f"| `{filename}` | {label} | {width}x{height} |")
    lines += [
        "",
        "Hinweis: Die KI-Ergebnis-Ansicht wurde ohne echten rembg-Modellaufruf erzeugt, damit kein Modell-Download oder langer Hintergrundprozess startet.",
        "Die macOS-nativen Datei-Oeffnen/Speichern-Dialoge sind Systemdialoge; die zugehoerigen App-Einstiege sind in Datei-/Projekt-Menue und Speicherstatus enthalten.",
        "Der Lauf nutzt In-Memory-QSettings, damit echte macOS-App-Preferences unveraendert bleiben.",
    ]
    if live_3d:
        lines.append(
            "Die 3D-Ready- und Anzeigeparameter-Screenshots wurden mit nativer Qt-Plattform und echtem OpenGL-Viewer erzeugt; Loading, Fallback und Fehlerzustand werden deterministisch hergestellt."
        )
    else:
        lines.append(
            "Der headless Standardlauf zeigt 3D-Loading und Fallback; fuer gerenderte 3D-Ready-Screenshots nutze --qt-platform native --include-live-3d."
        )
    (out / "manifest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
