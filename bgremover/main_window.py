"""MainWindow – die Top-Level-Fensterklasse."""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import cast

from PIL import Image
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QAction, QColor, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QColorDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from bgremover import __version__
from bgremover.canvas import ImageCanvas
from bgremover.constants import (
    _THREAD_SHUTDOWN_MS,
    _WINDOW_MIN_H,
    _WINDOW_MIN_W,
    TOOL_BRUSH,
    TOOL_ERASER,
    TOOL_LASSO,
    TOOL_WAND,
    logger,
)
from bgremover.crop_bar import CropBar
from bgremover.eufymake_export_dialog import EufyMakeExportDialog
from bgremover.eufymake_validate import format_finding
from bgremover.eufymake_writer import (
    EufyMakeWriteError,
    ExportTargetExistsError,
    ExportTargetNotDirectoryError,
    ExportValidationError,
    write_export,
)
from bgremover.export_checks import CheckCode, check_export, split_findings
from bgremover.export_checks import format_finding as format_check_finding
from bgremover.height_map_panel import HeightMapActions
from bgremover.history_popup import HistoryPopup
from bgremover.i18n import SETTINGS_LOCALE_KEY, init_locale_from_settings, tr
from bgremover.image_ops import (
    DEFAULT_SAVE_FORMAT,
    ensure_save_extension,
    save_dialog_filter,
)
from bgremover.layer_panel import LayerPanelActions
from bgremover.main_toolbar import Toolbar, ToolbarActions, build_toolbar
from bgremover.menu_actions import MainMenuCallbacks, build_main_menu
from bgremover.preview_mode import PreviewMode
from bgremover.project_io import (
    PROJECT_SUFFIX,
    ProjectFileError,
    load_project,
    save_project,
)
from bgremover.project_model import LayerKind, LayerRole, Project
from bgremover.recent_files import (
    RECENT_MAX,
    SETTINGS_RECENT_KEY,
    RecentFiles,
    RecentFilesMenu,
)
from bgremover.resize_dialog import ResizeDialog
from bgremover.right_panel import (
    RightPanelActions,
    build_right_panel,
)
from bgremover.settings_dialog import SettingsDialog
from bgremover.settings_schema import (
    EXPORT_BIT_DEPTH_KEY,
    EXPORT_DIR_KEY,
    EXPORT_INCLUDE_GLOSS_KEY,
    EXPORT_INCLUDE_HEIGHT_KEY,
    is_future_schema,
)
from bgremover.settings_schema import migrate as migrate_settings
from bgremover.status_messages import StatusMessages as SM
from bgremover.stepper import Stepper, WorkflowStep
from bgremover.theme import (
    CANVAS_CONTAINER_STYLE,
    STATUS_BAR_STYLE,
)
from bgremover.units import UnitsError
from bgremover.worker_controller import WorkerController
from bgremover.workers import REMBG_AVAILABLE

# Standard-Canvas-Größe eines per „Neues Projekt" erzeugten leeren Projekts.
_NEW_PROJECT_SIZE = (1024, 1024)

# Befunde, die vor einem **normalen** Raster-Speichern (#380) bewusst NICHT
# angezeigt werden: BgRemover ist ein Freistellungswerkzeug, Teiltransparenz ist
# das erwartete Ergebnis und keine warnwürdige Auffälligkeit. Alle übrigen Befunde
# der allgemeinen Prüfung (#379) – Fehler wie Warnungen – werden gezeigt.
_SAVE_CHECK_SKIP_CODES = frozenset({CheckCode.UNEXPECTED_ALPHA})


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"BgRemover Pro {__version__}")
        self.setMinimumSize(_WINDOW_MIN_W, _WINDOW_MIN_H)
        self._bg_color   = QColor(255, 255, 255)
        # Canvas-Version zum Startzeitpunkt der KI: verhindert, dass ein
        # verspätet eintreffendes Ergebnis ein inzwischen geladenes anderes
        # Bild überschreibt. Robuster als Objekt-Identität (is-Vergleich).
        self._ai_input_version: int = -1
        # Monotone ID fuer asynchrone Bildlade-Auftraege. Zusammen mit der
        # Canvas-Revision verhindert sie, dass ein verspaeteter Callback einen
        # neueren Ladeauftrag oder zwischenzeitliche Bearbeitungen ueberschreibt.
        self._load_generation: int = 0
        # True, sobald der rembg-Warmup mit Fehler endete: unterdrückt die
        # irreführende „KI bereit"-Meldung im Abschluss-Callback.
        self._warmup_failed: bool = False
        # Speicher-Pfad des aktuellen Bildes (für Quick-Save ⌘S).
        # Wird beim Laden eines neuen Bildes zurückgesetzt.
        self._save_path: str | None = None
        # Speicher-Pfad des aktuellen Projekts (.bgrproj) für „Projekt speichern".
        self._project_path: str | None = None
        # Canvas-Revision zum Zeitpunkt des letzten Speicherns/Ladens.
        # „Ungespeicherte Änderungen" = aktuelle Revision weicht davon ab.
        # Schützt vor stillem Arbeitsverlust beim Schließen/Bildwechsel.
        self._saved_revision: int = 0
        # Persistente Einstellungen (Recent-Files etc.). Schema-Migration
        # vor dem ersten Lese-/Schreibzugriff, damit kuenftige Format-
        # Wechsel an einem zentralen Punkt greifen koennen.
        self._settings = QSettings("BgRemover", "BgRemover")
        migrate_settings(self._settings)
        future_schema = is_future_schema(self._settings)
        init_locale_from_settings(
            self._settings.value(SETTINGS_LOCALE_KEY, None))
        self._recent_files = RecentFiles(
            self._settings,
            SETTINGS_RECENT_KEY,
            RECENT_MAX,
            read_only=future_schema,
        )
        # Beschädigte/alte recent_files-Werte einmalig beim Start bereinigen,
        # damit ein unerwarteter gespeicherter Typ den Menü-/App-Aufbau nicht
        # abbrechen kann (Befund #233). Bei einem ZUKUENFTIGEN Schema NICHT
        # umschreiben: ein neueres recent_files-Layout (z. B. ein Mapping) wuerde
        # sonst faelschlich als beschaedigt mit [] ueberschrieben – Downgrade-
        # Datenverlust, den migrate() bewusst vermeidet (Befund #240). Der
        # Read-only-Modus schützt zusätzlich indirekte Writes beim Menüaufbau
        # und bei späteren Recent-Files-Aktionen (Befund #259).
        if not future_schema:
            self._recent_files.sanitize()
        # Submenü-Adapter wird in _build_menu gesetzt
        self._recent_menu: RecentFilesMenu | None = None
        self._worker_controller = WorkerController(
            self, shutdown_ms=_THREAD_SHUTDOWN_MS)
        self._tool_shortcuts: list[QShortcut] = []
        self._build_ui()
        self._build_menu()
        self._build_tool_shortcuts()
        if REMBG_AVAILABLE:
            self._start_rembg_warmup()

    # ── UI aufbauen ──────────────────────────────────────────

    def _build_ui(self) -> None:
        # Status-Bar zuerst anlegen und als typisiertes Attribut cachen,
        # damit `self._sb.showMessage(...)` ohne None-Narrowing auskommt
        # (QMainWindow.statusBar() liefert `QStatusBar | None`).
        self._sb = QStatusBar()
        self._sb.setStyleSheet(STATUS_BAR_STYLE)
        self.setStatusBar(self._sb)

        root_w = QWidget()
        self.setCentralWidget(root_w)
        # Vertikaler Stapel: Schrittleiste (oben, volle Breite) über dem
        # dreispaltigen Body (Werkzeugleiste | Leinwand | Inspector) – der
        # geführte Workflow (Epic #418).
        root = QVBoxLayout(root_w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._stepper = Stepper()
        self._stepper.stepSelected.connect(self._on_step_selected)
        root.addWidget(self._stepper)

        body_w = QWidget()
        body = QHBoxLayout(body_w)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        body.addWidget(self._build_toolbar())

        # Canvas + Crop-Bestätigungsleiste in vertikalem Container
        canvas_container = QWidget()
        canvas_container.setStyleSheet(CANVAS_CONTAINER_STYLE)
        cv_lay = QVBoxLayout(canvas_container)
        cv_lay.setContentsMargins(0, 0, 0, 0)
        cv_lay.setSpacing(0)

        self._canvas = ImageCanvas()
        self._canvas.statusMsg.connect(self._sb.showMessage)
        self._canvas.historyChanged.connect(self._on_history_changed)
        self._canvas.imageLoaded.connect(self._on_image_loaded)
        self._canvas.loadRequested.connect(self._load_image_async)
        self._canvas.wandRequested.connect(self._start_flood_fill_async)
        self._history_popup = HistoryPopup(
            self, self._toolbar.btn_history, on_jump=self._canvas.undo_to)

        self._crop_bar = CropBar()
        self._crop_bar.bind(self._canvas)
        cv_lay.addWidget(self._crop_bar)

        cv_lay.addWidget(self._canvas, 1)

        body.addWidget(canvas_container, 1)
        body.addWidget(self._build_right_panel())
        root.addWidget(body_w, 1)

        # Startzustand: Schritt 1, Schritte 2–6 gesperrt bis ein Bild geladen ist.
        self._step = WorkflowStep.OPEN
        self._apply_toolbar_for_step(WorkflowStep.OPEN)
        self._sync_workflow_availability()
        self._sb.showMessage(SM.START_HINWEIS)

    def _build_toolbar(self) -> QFrame:
        self._toolbar = build_toolbar(
            ToolbarActions(
                set_tool=self._set_tool,
                run_ai=self._run_ai,
                undo=lambda: self._canvas.undo(),
                redo=lambda: self._canvas.redo(),
                restore_original=lambda: self._canvas.restore_original(),
                toggle_history=lambda: self._history_popup.toggle(),
                open_image=self._open_image,
                save=self._save,
            ),
            rembg_available=REMBG_AVAILABLE,
        )
        return self._toolbar.frame

    @property
    def toolbar(self) -> Toolbar:
        """Die Toolbar-Bausteine (DTO mit öffentlichen Widget-Feldern); nur lesen."""
        return self._toolbar

    def _build_right_panel(self) -> QFrame:
        panel = build_right_panel(
            RightPanelActions(
                set_tolerance=self._canvas.set_tolerance,
                set_brush_size=self._canvas.set_brush_size,
                clear_selection=self._canvas.clear_selection,
                invert_selection=self._canvas.invert_selection,
                expand_selection=self._canvas.expand_selection,
                shrink_selection=self._canvas.shrink_selection,
                remove_background=self._canvas.apply_remove,
                pick_color=self._pick_color,
                replace_background=lambda: self._canvas.apply_replace(self._bg_color),
                feather=self._canvas.feather_active_edges,
                rotate=self._canvas.apply_rotate,
                flip=self._canvas.apply_flip,
                resize=self._resize_image,
                round_corners=self._canvas.apply_round_corners,
                start_crop_circle=self._canvas.start_crop_circle,
                start_crop_ratio=self._canvas.start_crop_ratio,
                preview_color=self._canvas.preview_color_op,
                apply_color=self._canvas.apply_color_op,
                cancel_color_preview=self._canvas.cancel_color_preview,
                set_preview_mode=self._canvas.set_preview_mode,
                set_relief_strength=self._canvas.set_relief_strength,
                set_gloss_visible=self._canvas.set_gloss_visible,
                run_ai=self._run_ai,
                apply_resize=lambda w, h: self._canvas.apply_resize(w, h),
                save=self._save,
                export_eufymake=self._export_eufymake,
                set_save_format=self._set_preferred_format,
            ),
            LayerPanelActions(
                add_layer=self._canvas.add_layer,
                delete_active=self._canvas.delete_active_layer,
                duplicate_active=self._canvas.duplicate_active_layer,
                move_active_up=lambda: self._canvas.move_active_layer(up=True),
                move_active_down=lambda: self._canvas.move_active_layer(up=False),
                rename_active=self._rename_active_layer,
                set_active=self._canvas.set_active_layer,
                set_visible=self._canvas.set_layer_visible,
                set_opacity=self._canvas.set_layer_opacity,
                set_active_role=self._canvas.set_active_layer_role,
            ),
            HeightMapActions(
                generate=self._canvas.generate_height_map,
                import_file=self._import_height_map,
                lighten=self._canvas.lighten_active_height,
                darken=self._canvas.darken_active_height,
                set_height=self._canvas.set_active_height,
                invert=self._canvas.invert_active_height,
                preview_op=self._canvas.preview_height_op,
                apply_op=self._canvas.apply_height_op,
                cancel_preview=self._canvas.cancel_height_preview,
            ),
            on_open=self._open_image,
            on_open_path=self._open_recent_path,
            recent=self._recent_files.paths()[:3],
        )
        self._right_panel = panel
        panel.nav_prev.clicked.connect(lambda _=False: self._prev_step())
        panel.nav_next.clicked.connect(lambda _=False: self._next_step())
        self._color_btn = panel.color_button
        self._layer_panel = panel.layer_panel
        self._height_panel = panel.height_panel
        self._preview_mode_segments = panel.preview_mode_segments
        self._preview_relief_label = panel.preview_relief_label
        self._preview_relief_slider = panel.preview_relief_slider
        self._preview_gloss_visible = panel.preview_gloss_visible
        self._canvas.layersChanged.connect(self._layer_panel.refresh)
        self._canvas.layersChanged.connect(self._height_panel.refresh)
        self._canvas.previewSettingsChanged.connect(self._sync_preview_controls)
        self._update_color_btn()
        return panel.frame

    def _sync_preview_controls(
        self, mode: PreviewMode, relief_strength: int, gloss_visible: bool
    ) -> None:
        """Spiegelt Canvas-Anzeigezustand in Panel und Ansicht-Menü (#388)."""
        # Segmented-Control spiegelt den Modus rein visuell (kombinierter Modus
        # hebt alle Segmente auf; er ist über das Ansicht-Menü erreichbar).
        self._preview_mode_segments.set_mode(mode)

        slider = self._preview_relief_slider
        slider.blockSignals(True)
        slider.setValue(relief_strength)
        slider.blockSignals(False)
        self._preview_relief_label.setText(
            tr("right_panel.preview.relief_strength", value=relief_strength)
        )

        checkbox = self._preview_gloss_visible
        checkbox.blockSignals(True)
        checkbox.setChecked(gloss_visible)
        checkbox.blockSignals(False)

        for action in self.findChildren(QAction):
            if action.objectName().startswith("preview_mode_"):
                action.setChecked(action.data() is mode)

    def _import_height_map(self) -> None:
        """Öffnet eine Graustufendatei und importiert sie als HEIGHT-Ebene (#346)."""
        start_dir = self._settings.value("open_dir", "")
        path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.import_height.title"), start_dir,
            tr("dialog.open.filter"),
        )
        if path:
            self._canvas.import_height_map(path)

    def _resize_image(self) -> None:
        """Öffnet „Größe ändern…" und skaliert das Projekt auf die Zielgröße (#359)."""
        project = self._canvas.project
        if project is None:
            self._sb.showMessage(SM.KEIN_BILD_GELADEN)
            return
        try:
            pre_dpi = project.dpi
        except UnitsError:
            pre_dpi = None
        dlg = ResizeDialog(project.width, project.height, self, dpi=pre_dpi)
        if dlg.exec():
            width, height = dlg.selected_size()
            self._canvas.apply_resize(
                width, height, resample=dlg.selected_resample())
            # Im mm-Modus die physische Zielgröße (mm) als kanonische Quelle (#376)
            # im Projekt verankern – nur **wenn** das Resampling die Zielgröße auch
            # erreicht hat (No-op eingeschlossen). Wurde es am Megapixel-Gate
            # abgelehnt, bleibt die alte Pixelgröße bestehen und dürfte nicht mit
            # einer neuen mm-Größe gepaart werden. Das Setzen läuft über den Canvas,
            # der die content_revision anhebt (sonst ginge eine reine mm-Änderung im
            # No-op-Fall am „ungespeicherte Änderungen"-Schutz vorbei).
            mm = dlg.selected_physical_size_mm()
            if mm is not None and project.size == (width, height):
                self._canvas.set_physical_size_mm(*mm)

    def _set_tool(self, tool: str) -> None:
        """Wählt ein Canvas-Werkzeug und spiegelt die Wahl in der Toolbar."""
        self._canvas.set_tool(tool)
        buttons = {
            TOOL_WAND: self._toolbar.btn_wand,
            TOOL_BRUSH: self._toolbar.btn_brush,
            TOOL_ERASER: self._toolbar.btn_eraser,
            TOOL_LASSO: self._toolbar.btn_lasso,
        }
        if tool in buttons:
            buttons[tool].setChecked(True)

    def _cancel_or_clear(self) -> None:
        """Bricht aktive Interaktionen ab oder hebt sonst die Auswahl auf."""
        if not self._canvas.cancel_active_interaction():
            self._canvas.clear_selection()

    # ── Geführter Workflow (Epic #418) ───────────────────────────────────

    def _sync_workflow_availability(self) -> None:
        """Sperrt die Schritte 2–6, solange kein Bild geladen ist (Spec §13)."""
        self._stepper.set_locked(not self._canvas.has_image)

    def _on_step_selected(self, step_value: int) -> None:
        """Klick auf einen Schritt in der Schrittleiste (mit Gating)."""
        step = WorkflowStep(step_value)
        if not self._canvas.has_image and step is not WorkflowStep.OPEN:
            # Gesperrt: aktiven Schritt beibehalten, Hinweis zeigen.
            self._stepper.set_current(int(self._step))
            self._sb.showMessage(tr("workflow.locked"))
            return
        self._go_to_step(step)

    def _go_to_step(self, step: WorkflowStep) -> None:
        """Wechselt den aktiven Schritt und aktualisiert die gesamte UI."""
        self._step = step
        self._stepper.set_current(int(step))
        self._right_panel.set_step(step)
        self._apply_toolbar_for_step(step)

    def _next_step(self) -> None:
        """„Weiter": in Schritt 1 ohne Bild öffnen, sonst zum nächsten Schritt."""
        if self._step is WorkflowStep.OPEN and not self._canvas.has_image:
            self._open_image()
            return
        if self._step is WorkflowStep.EXPORT:
            # Letzter Schritt: „Exportieren ✓" löst das Speichern aus
            # (statt wirkungslos zu sein, PR #423-Review).
            self._save()
            return
        self._go_to_step(WorkflowStep(int(self._step) + 1))

    def _prev_step(self) -> None:
        """„Zurück": einen Schritt zurück (in Schritt 1 wirkungslos)."""
        if self._step is WorkflowStep.OPEN:
            return
        self._go_to_step(WorkflowStep(int(self._step) - 1))

    def _apply_toolbar_for_step(self, step: WorkflowStep) -> None:
        """Kontextuelle Werkzeugleiste: Auswahlwerkzeuge nur im Schritt Freistellen.

        Außerhalb von Freistellen werden die Auswahlwerkzeuge nicht nur
        ausgeblendet, sondern die Canvas-Werkzeug-Interaktion abgeschaltet –
        sonst würde ein noch aktives Pinsel-/Radier-/Lasso-Werkzeug das Bild
        unsichtbar weiterbearbeiten (PR #423-Review).
        """
        sel_visible = step is WorkflowStep.CUTOUT
        for button in (
            self._toolbar.btn_wand, self._toolbar.btn_brush,
            self._toolbar.btn_eraser, self._toolbar.btn_lasso,
        ):
            button.setVisible(sel_visible)
        self._toolbar.sel_separator.setVisible(sel_visible)
        self._canvas.set_tools_enabled(sel_visible)

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        assert menu_bar is not None
        self._recent_menu = build_main_menu(
            self,
            menu_bar,
            self._recent_files,
            MainMenuCallbacks(
                open_image=self._open_image,
                open_recent_path=self._open_recent_path,
                recent_path_missing=self._on_recent_missing,
                save=self._save,
                save_as=self._save_as,
                new_project=self._new_project,
                open_project=self._open_project,
                save_project=self._save_project,
                save_project_as=self._save_project_as,
                export_eufymake=self._export_eufymake,
                undo=self._canvas.undo,
                redo=self._canvas.redo,
                rotate=self._canvas.apply_rotate,
                flip=self._canvas.apply_flip,
                resize=self._resize_image,
                clear_selection=self._canvas.clear_selection,
                invert_selection=self._canvas.invert_selection,
                restore_original=self._canvas.restore_original,
                fit_to_view=self._canvas.fit_to_view,
                set_preview_mode=self._canvas.set_preview_mode,
                open_settings=self._open_settings,
            ),
        )

    def _build_tool_shortcuts(self) -> None:
        for key, tool in (
            ("W", TOOL_WAND),
            ("B", TOOL_BRUSH),
            ("E", TOOL_ERASER),
            ("L", TOOL_LASSO),
        ):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(lambda t=tool: self._set_tool(t))
            self._tool_shortcuts.append(shortcut)
        self._escape_action = QAction(self)
        self._escape_action.setShortcut(QKeySequence("Escape"))
        self._escape_action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self._escape_action.triggered.connect(
            lambda _checked=False: self._cancel_or_clear())
        self.addAction(self._escape_action)

    # ── Sauberes Thread-Shutdown beim Schliessen ──────────────

    def closeEvent(self, event) -> None:
        """Fragt bei ungespeicherten Änderungen nach und stoppt dann alle
        Hintergrund-Threads, bevor das Fenster (und damit die
        QThread-C++-Objekte) zerstört wird – sonst stürzt Python beim
        Schliessen ab, solange z. B. der KI-Warmup noch läuft.

        Bricht der Nutzer in der Speichern-Nachfrage ab oder kann ein Thread
        nicht innerhalb der festen Fristen beendet werden, wird das
        Close-Event verworfen und das Fenster bleibt offen.
        """
        if not self._confirm_discard_changes():
            event.ignore()
            return
        self._sb.showMessage(SM.BEENDE)
        self._sb.repaint()
        if not self._worker_controller.shutdown_all():
            self._sb.showMessage(SM.BEENDEN_FEHLGESCHLAGEN)
            event.ignore()
            return
        super().closeEvent(event)

    # ── Ungespeicherte Änderungen ─────────────────────────────

    def _mark_saved(self) -> None:
        """Setzt den „sauber"-Punkt auf den aktuellen Canvas-Zustand."""
        self._saved_revision = self._canvas.content_revision

    def _has_unsaved_changes(self) -> bool:
        """True, wenn seit dem letzten Speichern/Laden bearbeitet wurde.

        Stützt sich auf den monoton steigenden ``content_revision``-Zähler:
        jede Zustandsänderung (Bearbeitung, KI, Crop, Undo/Redo) erhöht ihn.
        Bewusst konservativ – im Zweifel lieber einmal zu viel nachfragen,
        als Arbeit stillschweigend zu verlieren.
        """
        return (self._canvas.has_image
                and self._canvas.content_revision != self._saved_revision)

    def _confirm_discard_changes(self) -> bool:
        """Fragt vor dem Verwerfen bearbeiteter, ungespeicherter Bilder nach.

        Gibt ``True`` zurück, wenn der Aufrufer fortfahren darf (nichts zu
        verlieren, erfolgreich gespeichert oder bewusst verworfen), und
        ``False``, wenn die Aktion abgebrochen werden soll.
        """
        if not self._has_unsaved_changes():
            return True
        reply = QMessageBox.warning(
            self, tr("dialog.unsaved.title"),
            tr("dialog.unsaved.body"),
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return False
        if reply == QMessageBox.StandardButton.Save:
            self._save()
            # Speichern abgebrochen (kein Pfad gewählt) oder fehlgeschlagen →
            # Aktion abbrechen, damit die Arbeit nicht doch verloren geht.
            return not self._has_unsaved_changes()
        return True  # Discard – bewusst verwerfen

    # ── Slots ─────────────────────────────────────────────────

    def _open_image(self) -> None:
        start_dir = self._settings.value("open_dir", "")
        path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.open.title"), start_dir,
            tr("dialog.open.filter"),
        )
        if path:
            self._load_image_async(path)

    def _load_image_async(self, path: str) -> None:
        """Lädt ein Bild im Hintergrund-Thread, damit die UI nicht blockt."""
        if self._worker_controller.is_loading:
            self._sb.showMessage(SM.LAEDT_BEREITS)
            return
        # Vor dem Verwerfen des aktuellen Bildes (Öffnen/Recent/Drag&Drop)
        # bei ungespeicherten Änderungen nachfragen.
        if not self._confirm_discard_changes():
            return
        ai_was_running = self._worker_controller.is_ai_running
        self._worker_controller.cancel_ai()
        # Eine laufende Zauberstab-Berechnung gehört zum bisherigen Bild.
        # Abbrechen spart CPU; der stille Canvas-Reset hält den Zauberstab
        # auch dann bedienbar, wenn das anschließende Laden fehlschlägt.
        self._worker_controller.cancel_flood_fill()
        self._canvas.reset_pending_wand()
        if ai_was_running:
            # rembg selbst ist nicht unterbrechbar. Das Ergebnis wird
            # verworfen, aber bis zur Rückkehr des C-Aufrufs bleibt der
            # KI-Button gesperrt; diese Wartezeit soll sichtbar sein.
            self._sb.showMessage(SM.KI_ABBRUCH_WARTET)
        else:
            self._sb.showMessage(SM.LAEDT(Path(path).name))
        previous_generation = self._load_generation
        load_generation = previous_generation + 1
        self._load_generation = load_generation
        content_revision = self._canvas.content_revision
        started = self._worker_controller.start_image_load(
            path,
            on_loaded=lambda img, loaded_path: self._on_image_load_done(
                img, loaded_path, load_generation, content_revision),
            on_error=self._on_image_load_error,
        )
        if not started:
            self._load_generation = previous_generation

    def open_paths(self, paths: Sequence[str]) -> None:
        """Öffentliche, schmale Fassade zum Öffnen übergebener Bildpfade.

        Quelle sind Startargumente (CLI / Linux-Desktop ``%F``) und macOS-
        ``QFileOpenEvent``s. Semantik bei mehreren Pfaden: den ersten öffnen,
        die übrigen ignorieren und ihre Anzahl in der Statusleiste melden – die
        App bearbeitet bewusst nur ein Bild gleichzeitig (Befund #249).

        Geladen wird über denselben validierten, asynchronen Pfad wie Datei-
        Dialog, Recent Files und Drag & Drop (``_load_image_async`` →
        ``open_validated_image``): fehlende oder nicht unterstützte Dateien
        enden dort als Statusmeldung statt als Startabbruch, und vor dem
        Verwerfen eines bearbeiteten Bildes greift die Nachfrage zu
        ungespeicherten Änderungen.
        """
        candidates = [p for p in paths if p]
        if not candidates:
            return
        first, *rest = candidates
        self._load_image_async(first)
        if rest:
            self._sb.showMessage(tr(
                "canvas.opened_extra", name=Path(first).name, extra=len(rest)))

    def report_unopenable_remote(self) -> None:
        """Meldet ein Betriebssystem-Open-Event ohne lokale Datei.

        macOS kann eine nicht-lokale URL (z. B. Remote) als ``QFileOpenEvent``
        liefern; ``QFileOpenEvent.file()`` ist dann leer. Statt still nichts zu
        tun, wird dies kontrolliert in der Statusleiste gemeldet (Befund #249).
        """
        self._sb.showMessage(SM.OEFFNEN_NICHT_LOKAL)

    def shutdown_workers(self) -> None:
        """Beendet alle Hintergrund-Worker beim App-Quit.

        Wird in ``app.main`` an ``QApplication.aboutToQuit`` gehängt. Anders als
        ``closeEvent`` (Fenster schließen) greift das AUCH, wenn die App über
        ``QApplication.quit()`` endet, ohne dass das Fenster geschlossen wird –
        etwa direkt nach einem Start-Open. Ohne diesen Haken würde ein noch
        laufender Lade-/KI-Thread beim C++-Teardown abgeräumt und könnte den
        Prozess mit einem Crash beenden (Befund #249). ``shutdown_all`` ist
        idempotent; ein bereits über ``closeEvent`` beendeter Stand ist ein
        No-op.
        """
        self._worker_controller.shutdown_all()

    def _on_image_load_done(
        self,
        img: object,
        path: str,
        load_generation: int,
        content_revision: int,
    ) -> None:
        if (load_generation != self._load_generation
                or content_revision != self._canvas.content_revision):
            self._sb.showMessage(SM.LADEERGEBNIS_VERWORFEN)
            return
        self._canvas.apply_loaded_image(cast(Image.Image, img), path)

    def _on_image_load_error(self, msg: str) -> None:
        self._sb.showMessage(SM.LADEFEHLER(msg))

    # ── Zauberstab (asynchron) ──────────────────────────────────

    def _start_flood_fill_async(
        self, arr, x: int, y: int, tolerance: int,
    ) -> None:
        """Reicht den Wand-Klick an den Worker weiter.

        Der Canvas blockt selbst weitere Wand-Klicks waehrend der
        Berechnung; ein zweiter Aufruf hier wuerde der Controller mit
        ``False`` ablehnen – das verbleibende ``_wand_busy`` im Canvas
        wuerde haengen. Deshalb ist das ``start_flood_fill``-Ergebnis
        hier defensiv geprueft und der Canvas-State im Konfliktfall
        zurueckgesetzt.
        """
        started = self._worker_controller.start_flood_fill(
            arr, x, y, tolerance,
            on_done=self._canvas.apply_wand_result,
            on_error=self._canvas.cancel_pending_wand,
        )
        if not started:
            self._canvas.cancel_pending_wand(
                "Eine Wand-Berechnung läuft bereits")

    # ── rembg-Warmup ────────────────────────────────────────────

    def _start_rembg_warmup(self) -> None:
        """Lädt das rembg-Modell im Hintergrund, damit der erste KI-Klick
        nicht spürbar wartet."""
        self._warmup_failed = False
        self._sb.showMessage(SM.KI_MODELL_LADEN)
        # KI-Button bis Warmup-Ende sperren: ein KI-Klick während des Warmups
        # würde rembg parallel initialisieren (doppelter Modell-Load / Race).
        self._toolbar.btn_ai.setEnabled(False)
        self._worker_controller.start_warmup(
            on_finished=self._on_warmup_done,
            on_error=self._on_warmup_error,
        )

    def _on_warmup_done(self) -> None:
        # Läuft als Thread-Abschluss IMMER (auch nach Fehler). Button wieder
        # freigeben; ein fehlgeschlagener Warmup darf dennoch nicht als
        # „KI bereit" gemeldet werden – on_error hat das Flag bereits gesetzt.
        self._toolbar.btn_ai.setEnabled(True)
        if self._warmup_failed:
            return
        self._sb.showMessage(SM.KI_BEREIT)

    def _on_warmup_error(self, _msg: str) -> None:
        """Warmup fehlgeschlagen (z. B. Modell-Download offline nicht möglich).

        Wird vor ``_on_warmup_done`` zugestellt; setzt das Flag, das dort die
        falsche Bereitschaftsmeldung verhindert. Den Fehler protokolliert
        bereits der Worker (``_Worker.run`` → ``logger.exception``). Die KI
        bleibt nutzbar – ein späterer Klick versucht rembg erneut und meldet
        Fehler ggf. sichtbar.
        """
        self._warmup_failed = True
        self._sb.showMessage(SM.KI_FEHLER_WARMUP)

    def _confirm_pre_save_checks(self) -> bool:
        """Allgemeine Pre-Export-Prüfung (#379) vor dem Speichern (#380).

        Führt :func:`export_checks.check_export` auf dem aktuellen Projekt aus und
        zeigt die Befunde analog zum EufyMake-Flow: **Fehler blockieren** das
        Speichern (kein Schreibaufruf), **Warnungen** erfordern eine bewusste
        Bestätigung. Gibt ``True`` zurück, wenn geschrieben werden darf. Die Prüfung
        läuft **vor** dem eigentlichen Schreiben, sodass ein Abbruch weder das
        Projekt noch ein bestehendes Ziel verändert und keine Temporärdateien
        hinterlässt. ``UNEXPECTED_ALPHA`` wird hier bewusst unterdrückt
        (Teiltransparenz ist das normale Ergebnis eines Freistellungswerkzeugs).
        """
        project = self._canvas.project
        if project is None:
            return True
        findings = tuple(
            f for f in check_export(project) if f.code not in _SAVE_CHECK_SKIP_CODES
        )
        errors, warnings = split_findings(findings)
        if errors:
            details = "\n".join(format_check_finding(f) for f in errors)
            QMessageBox.critical(
                self, tr("export.check.error.title"),
                tr("export.check.blocked", details=details))
            return False
        if warnings:
            details = "\n".join(format_check_finding(f) for f in warnings)
            reply = QMessageBox.question(
                self, tr("export.check.warning.title"),
                tr("export.check.confirm", details=details))
            return reply == QMessageBox.StandardButton.Yes
        return True

    def _save(self) -> None:
        """Quick-Save: speichert in den bekannten Pfad, sonst „Speichern unter…"."""
        if self._save_path is None:
            self._save_as()
            return
        if not self._canvas.has_image:
            self._sb.showMessage(SM.KEIN_BILD_ZUM_SPEICHERN)
            return
        if not self._confirm_pre_save_checks():
            return
        if self._canvas.save_image(self._save_path):
            self._mark_saved()

    def _save_as(self) -> None:
        """Speichern unter…: öffnet immer den Datei-Dialog."""
        if not self._canvas.has_image:
            self._sb.showMessage(SM.KEIN_BILD_ZUM_SPEICHERN)
            return
        # Pre-Export-Prüfung (#380) vor dem Datei-Dialog: blockierende Befunde
        # verhindern das Schreiben, ohne den Nutzer erst einen Pfad wählen zu lassen.
        if not self._confirm_pre_save_checks():
            return
        save_dir = self._settings.value("save_dir", "")
        if self._save_path:
            suggest = self._save_path
        elif save_dir:
            suggest = str(Path(save_dir) / "bild_bearbeitet")
        else:
            suggest = "bild_bearbeitet"
        preferred = self._settings.value("preferred_format", DEFAULT_SAVE_FORMAT)
        path, selected = QFileDialog.getSaveFileName(
            self, tr("dialog.save.title"), suggest,
            save_dialog_filter(preferred),
        )
        if not path:
            return
        # Fehlt die Endung, aus dem gewählten Filter ableiten – sonst würde
        # save_image_file still als PNG speichern, obwohl ein anderes Format
        # gewählt war. Eine getippte Endung bleibt unangetastet.
        path = ensure_save_extension(path, selected, preferred)
        # Pfad nur als Quick-Save-Ziel merken, wenn das Speichern klappte.
        if self._canvas.save_image(path):
            self._save_path = path
            self._mark_saved()

    # ── Ebenen-Panel ────────────────────────────────────────────

    def _rename_active_layer(self) -> None:
        """Fragt einen neuen Namen für die aktive Ebene ab und wendet ihn an."""
        project = self._canvas.project
        if project is None:
            return
        active = project.active_layer()
        if active is None:
            return
        name, ok = QInputDialog.getText(
            self, tr("dialog.rename.title"), tr("dialog.rename.label"),
            text=active.name)
        if ok and name.strip():
            self._canvas.rename_active_layer(name)

    # ── Projekt-Dateien (.bgrproj) ──────────────────────────────

    def _adopt_new_document(self) -> None:
        """Setzt die Speicher-/Sauber-Marker nach Neu/Öffnen eines Projekts."""
        self._save_path = None
        self._mark_saved()
        # Geführter Workflow: Ein geladenes Projekt gibt die Schritte frei und
        # steigt beim Freistellen neu ein (Spec §13, PR #423-Review).
        self._sync_workflow_availability()
        if self._canvas.has_image:
            self._go_to_step(WorkflowStep.CUTOUT)

    def _new_project(self) -> None:
        """Erzeugt ein leeres Projekt mit einer transparenten COLOR-Ebene."""
        if not self._confirm_discard_changes():
            return
        width, height = _NEW_PROJECT_SIZE
        project = Project(width, height)
        project.create_layer(
            Image.new("RGBA", (width, height), (0, 0, 0, 0)),
            name=tr("layers.new_name", n=1), kind=LayerKind.COLOR)
        self._canvas.set_project(project)
        self._project_path = None
        self._adopt_new_document()
        self._sb.showMessage(tr("project.new"))

    def _open_project(self) -> None:
        """Öffnet eine ``.bgrproj``-Datei über einen Datei-Dialog."""
        if not self._confirm_discard_changes():
            return
        start_dir = self._settings.value("project_dir", "")
        path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.open_project.title"), start_dir,
            tr("dialog.open_project.filter"))
        if path:
            self._load_project_into_canvas(path)

    def _open_project_path(self, path: str) -> None:
        """Öffnet ein Projekt aus „Zuletzt geöffnet" (mit Verwerfen-Nachfrage)."""
        if not self._confirm_discard_changes():
            return
        self._load_project_into_canvas(path)

    def _load_project_into_canvas(self, path: str) -> None:
        """Lädt ``path`` als Projekt in den Canvas; meldet Fehler verständlich.

        Gemeinsamer Pfad für Datei-Dialog und „Zuletzt geöffnet". Die Nachfrage
        zu ungespeicherten Änderungen liegt bei den Aufrufern, damit sie vor dem
        Datei-Dialog greifen kann.
        """
        load_warnings: list[str] = []
        try:
            project = load_project(path, warnings=load_warnings)
        except ProjectFileError as exc:
            self._report_project_error(str(exc))
            return
        self._canvas.set_project(project)
        self._project_path = path
        self._adopt_new_document()
        self._remember_project(path)
        # Verlustfrei geheilte Altzustände (z. B. entfernte inkompatible Rolle,
        # #364) als Warnung statt der neutralen „geöffnet"-Meldung zeigen.
        if load_warnings:
            self._sb.showMessage(" · ".join(load_warnings))
        else:
            self._sb.showMessage(tr("project.opened", name=Path(path).name))

    def _save_project(self) -> None:
        """Quick-Save des Projekts in den bekannten Pfad, sonst „Speichern unter…"."""
        if self._project_path is None:
            self._save_project_as()
            return
        self._write_project(self._project_path)

    def _save_project_as(self) -> None:
        """Speichert das Projekt unter einem im Dialog gewählten Pfad."""
        if self._canvas.project is None:
            self._sb.showMessage(tr("project.no_project"))
            return
        if self._project_path:
            suggest = self._project_path
        else:
            project_dir = self._settings.value("project_dir", "")
            suggest = str(Path(project_dir) / "projekt") if project_dir else "projekt"
        path, _ = QFileDialog.getSaveFileName(
            self, tr("dialog.save_project.title"), suggest,
            tr("dialog.open_project.filter"))
        if not path:
            return
        if not path.lower().endswith(PROJECT_SUFFIX):
            path += PROJECT_SUFFIX
        if self._write_project(path):
            self._project_path = path

    def _write_project(self, path: str) -> bool:
        """Schreibt das aktuelle Projekt atomar; meldet Fehler verständlich."""
        project = self._canvas.project
        if project is None:
            self._sb.showMessage(tr("project.no_project"))
            return False
        try:
            save_project(project, path)
        except OSError as exc:
            logger.exception("Projekt speichern fehlgeschlagen: %s", path)
            self._sb.showMessage(tr("project.save_failed", error=exc))
            return False
        self._mark_saved()
        self._remember_project(path)
        self._sb.showMessage(tr("project.saved", name=Path(path).name))
        return True

    def _remember_project(self, path: str) -> None:
        """Merkt ein Projekt in „Zuletzt geöffnet" und sein Verzeichnis."""
        self._add_recent(path)
        self._settings.setValue("project_dir", str(Path(path).resolve().parent))

    def _report_project_error(self, message: str) -> None:
        """Zeigt einen Projekt-Lade-/Speicherfehler in Statusleiste + Dialog."""
        self._sb.showMessage(message)
        QMessageBox.warning(self, tr("dialog.project_error.title"), message)

    # ── EufyMake-Studio-Import-Export (#355) ────────────────────

    def _export_eufymake(self) -> None:
        """Exportiert Import-Assets für EufyMake Studio: Dialog → Prüfung → Schreiben.

        Der Dialog blockt schon bei Fehlern und verlangt für Warnungen eine
        bewusste Bestätigung (#354). Abbruch bleibt seiteneffektfrei; geschrieben
        wird atomar über ``write_export``.
        """
        project = self._canvas.project
        if project is None:
            self._sb.showMessage(tr("eufymake.status.no_project"))
            return
        dlg = EufyMakeExportDialog(
            project,
            include_height=self._settings.value(EXPORT_INCLUDE_HEIGHT_KEY, True, type=bool),
            include_gloss=self._settings.value(EXPORT_INCLUDE_GLOSS_KEY, True, type=bool),
            bit_depth=self._settings.value(EXPORT_BIT_DEPTH_KEY, 8, type=int),
            dest_dir=self._settings.value(EXPORT_DIR_KEY, "", type=str),
            parent=self,
        )
        if not dlg.exec():
            self._sb.showMessage(tr("eufymake.status.cancelled"))
            return
        roles = dlg.selected_optional_roles()
        bits = dlg.selected_bit_depth()
        dest = dlg.selected_destination()
        self._remember_export_options(dest, roles, bits)
        self._write_eufymake(project, dest, roles, bits, dlg.warnings_confirmed())

    def _write_eufymake(
        self,
        project: Project,
        dest: str,
        roles: list[LayerRole],
        bits: int,
        confirm: bool,
        *,
        overwrite: bool = False,
    ) -> None:
        """Schreibt das Importpaket atomar und meldet Erfolg/Fehler verständlich."""
        try:
            written = write_export(
                project, dest,
                optional_roles=roles, bit_depth=bits,
                confirm_warnings=confirm, overwrite=overwrite,
            )
        except ExportTargetExistsError:
            if self._confirm_overwrite(dest):
                self._write_eufymake(project, dest, roles, bits, confirm, overwrite=True)
            else:
                self._sb.showMessage(tr("eufymake.status.cancelled"))
            return
        except ExportTargetNotDirectoryError:
            # Vorhandene Datei als Ziel: niemals überschreiben anbieten.
            QMessageBox.critical(
                self, tr("eufymake.error.title"), tr("eufymake.error.not_directory", path=dest))
            return
        except ExportValidationError as exc:
            details = "\n".join(format_finding(finding) for finding in exc.findings)
            QMessageBox.critical(
                self, tr("eufymake.error.title"), tr("eufymake.error.blocked", details=details))
            return
        except (EufyMakeWriteError, OSError) as exc:
            logger.exception("EufyMake-Export fehlgeschlagen: %s", dest)
            QMessageBox.critical(
                self, tr("eufymake.error.title"), tr("eufymake.error.write", error=str(exc)))
            return
        self._sb.showMessage(tr("eufymake.status.exported", path=str(written)))
        QMessageBox.information(
            self, tr("eufymake.success.title"), tr("eufymake.success.body", path=str(written)))

    def _confirm_overwrite(self, dest: str) -> bool:
        """Fragt nach, ob ein bereits vorhandener Exportordner ersetzt werden darf."""
        reply = QMessageBox.question(
            self, tr("eufymake.overwrite.title"), tr("eufymake.overwrite.body", path=dest))
        return reply == QMessageBox.StandardButton.Yes

    def _remember_export_options(
        self, dest: str, roles: list[LayerRole], bits: int,
    ) -> None:
        """Persistiert Zielordner und allgemeine (nicht projektspezifische) Optionen."""
        self._settings.setValue(EXPORT_DIR_KEY, dest)
        self._settings.setValue(EXPORT_INCLUDE_HEIGHT_KEY, LayerRole.HEIGHT_MAP in roles)
        self._settings.setValue(EXPORT_INCLUDE_GLOSS_KEY, LayerRole.GLOSS_MASK in roles)
        self._settings.setValue(EXPORT_BIT_DEPTH_KEY, bits)

    # ── Recent-Files ────────────────────────────────────────────

    def _open_recent_path(self, path: str) -> None:
        """Öffnet einen „Zuletzt geöffnet"-Eintrag – Projekt (.bgrproj) oder Bild.

        Projekte laufen über den Projekt-Lader (#333), Bilder über den
        validierten, asynchronen Bildladepfad. So listet „Zuletzt geöffnet"
        beide Typen und öffnet jeden korrekt (#335).
        """
        if path.lower().endswith(PROJECT_SUFFIX):
            self._open_project_path(path)
        else:
            self._load_image_async(path)

    def _add_recent(self, path: str) -> None:
        if self._recent_menu is None:
            self._recent_files.add(path)
            return
        self._recent_menu.add(path)

    def _on_recent_missing(self, path: str) -> None:
        self._sb.showMessage(SM.DATEI_NICHT_VORHANDEN(Path(path).name))

    def _on_image_loaded(self, path: str) -> None:
        """Wird nach jedem load_image vom Canvas aufgerufen."""
        self._save_path = None
        # Frisch geladenes Bild gilt als „sauber" (= keine ungespeicherten
        # Änderungen), bis der Nutzer es bearbeitet.
        self._mark_saved()
        self._add_recent(path)
        # Geführter Workflow: Schritte freigeben und immer beim Freistellen
        # neu einsteigen – auch wenn ein späteres Bild einen bereits
        # fortgeschrittenen Schritt ersetzt (Spec §13, PR #423-Review).
        self._sync_workflow_availability()
        self._go_to_step(WorkflowStep.CUTOUT)

    def _set_preferred_format(self, fmt: str) -> None:
        """Merkt das im Export-Schritt gewählte Speicherformat (§9, #439)."""
        self._settings.setValue("preferred_format", fmt)

    def _pick_color(self) -> None:
        c = QColorDialog.getColor(self._bg_color, self, tr("dialog.color.title"))
        if c.isValid():
            self._bg_color = c
            self._update_color_btn()

    def _update_color_btn(self) -> None:
        self._color_btn.setStyleSheet(
            f"background: {self._bg_color.name()}; border-radius: 5px; border: 2px solid #555;"
        )

    def _run_ai(self) -> None:
        if not self._canvas.has_image:
            self._sb.showMessage(SM.KEIN_BILD_GELADEN)
            return
        if self._worker_controller.is_ai_running:
            self._sb.showMessage(SM.KI_LAEUFT_BEREITS)
            return
        self._sb.showMessage(SM.KI_VERARBEITET)
        self._toolbar.btn_ai.setEnabled(False)

        # Revision merken, damit verspätete KI-Ergebnisse verworfen werden.
        self._ai_input_version = self._canvas.version

        img = self._canvas.image
        assert img is not None  # has_image-Check oben garantiert das
        self._worker_controller.start_ai(
            img,
            on_done=self._on_ai_done,
            on_error=self._on_ai_error,
            on_finished=self._on_ai_thread_finished,
        )

    def _on_ai_thread_finished(self) -> None:
        self._toolbar.btn_ai.setEnabled(True)
        self._ai_input_version = -1
        if self._sb.currentMessage() == SM.KI_ABBRUCH_WARTET:
            self._sb.showMessage(SM.KI_ABGEBROCHEN)

    def _on_ai_done(self, img: Image.Image) -> None:
        # Ergebnis nur übernehmen, wenn sich der Canvas seit KI-Start nicht geändert hat.
        if self._canvas.version != self._ai_input_version:
            self._sb.showMessage(SM.KI_ERGEBNIS_VERWORFEN)
            return
        self._canvas.apply_ai_result(img)

    def _on_ai_error(self, msg: str) -> None:
        self._sb.showMessage(SM.KI_FEHLER(msg))
        QMessageBox.warning(self, tr("dialog.ai_error.title"),
                            tr("dialog.ai_error.body", msg=msg))

    def _on_history_changed(self, history: list[str]) -> None:
        self._history_popup.update_entries(history)

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._settings, self)
        dlg.exec()
