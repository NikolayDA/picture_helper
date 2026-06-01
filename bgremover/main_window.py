"""MainWindow – die Top-Level-Fensterklasse."""
from __future__ import annotations

from pathlib import Path

from PIL import Image
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
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
)
from bgremover.crop_bar import CropBar
from bgremover.history_popup import HistoryPopup
from bgremover.image_ops import (
    DEFAULT_SAVE_FORMAT,
    ensure_save_extension,
    save_dialog_filter,
)
from bgremover.main_toolbar import ToolbarActions, build_toolbar
from bgremover.menu_actions import MainMenuCallbacks, build_main_menu
from bgremover.recent_files import (
    RECENT_MAX,
    SETTINGS_RECENT_KEY,
    RecentFiles,
    RecentFilesMenu,
)
from bgremover.right_panel import (
    RightPanelActions,
    build_right_panel,
)
from bgremover.settings_dialog import SettingsDialog
from bgremover.settings_schema import migrate as migrate_settings
from bgremover.status_messages import StatusMessages as SM
from bgremover.theme import (
    CANVAS_CONTAINER_STYLE,
    STATUS_BAR_STYLE,
)
from bgremover.worker_controller import WorkerController
from bgremover.workers import REMBG_AVAILABLE


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
        # True, sobald der rembg-Warmup mit Fehler endete: unterdrückt die
        # irreführende „KI bereit"-Meldung im Abschluss-Callback.
        self._warmup_failed: bool = False
        # Speicher-Pfad des aktuellen Bildes (für Quick-Save ⌘S).
        # Wird beim Laden eines neuen Bildes zurückgesetzt.
        self._save_path: str | None = None
        # Persistente Einstellungen (Recent-Files etc.). Schema-Migration
        # vor dem ersten Lese-/Schreibzugriff, damit kuenftige Format-
        # Wechsel an einem zentralen Punkt greifen koennen.
        self._settings = QSettings("BgRemover", "BgRemover")
        migrate_settings(self._settings)
        self._recent_files = RecentFiles(
            self._settings, SETTINGS_RECENT_KEY, RECENT_MAX)
        # Submenü-Adapter wird in _build_menu gesetzt
        self._recent_menu: RecentFilesMenu | None = None
        self._worker_controller = WorkerController(
            self, shutdown_ms=_THREAD_SHUTDOWN_MS)
        self._build_ui()
        self._build_menu()
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
        root = QHBoxLayout(root_w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())

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

        root.addWidget(canvas_container, 1)
        root.addWidget(self._build_right_panel())

        self._sb.showMessage(SM.START_HINWEIS)

    def _build_toolbar(self) -> QFrame:
        self._toolbar = build_toolbar(
            ToolbarActions(
                set_tool=lambda tool: self._canvas.set_tool(tool),
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
        self._btn_wand = self._toolbar.btn_wand
        self._btn_brush = self._toolbar.btn_brush
        self._btn_eraser = self._toolbar.btn_eraser
        self._btn_lasso = self._toolbar.btn_lasso
        self._btn_ai = self._toolbar.btn_ai
        self._btn_history = self._toolbar.btn_history
        return self._toolbar.frame

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
                rotate=self._canvas.apply_rotate,
                flip=self._canvas.apply_flip,
                round_corners=self._canvas.apply_round_corners,
                start_crop_circle=self._canvas.start_crop_circle,
                start_crop_ratio=self._canvas.start_crop_ratio,
            )
        )
        self._color_btn = panel.color_button
        self._update_color_btn()
        return panel.frame

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        assert menu_bar is not None
        self._recent_menu = build_main_menu(
            self,
            menu_bar,
            self._recent_files,
            MainMenuCallbacks(
                open_image=self._open_image,
                open_recent_path=self._load_image_async,
                recent_path_missing=self._on_recent_missing,
                save=self._save,
                save_as=self._save_as,
                undo=self._canvas.undo,
                redo=self._canvas.redo,
                rotate=self._canvas.apply_rotate,
                flip=self._canvas.apply_flip,
                clear_selection=self._canvas.clear_selection,
                invert_selection=self._canvas.invert_selection,
                restore_original=self._canvas.restore_original,
                fit_to_view=self._canvas.fit_to_view,
                open_settings=self._open_settings,
            ),
        )

    # ── Sauberes Thread-Shutdown beim Schliessen ──────────────

    def closeEvent(self, event) -> None:
        """Stoppt alle Hintergrund-Threads, bevor das Fenster (und damit
        die QThread-C++-Objekte) zerstört wird – sonst stürzt Python
        beim Schliessen ab, solange z. B. der KI-Warmup noch läuft.
        """
        self._sb.showMessage(SM.BEENDE)
        self._worker_controller.shutdown_all()
        super().closeEvent(event)

    # ── Slots ─────────────────────────────────────────────────

    def _open_image(self) -> None:
        start_dir = self._settings.value("open_dir", "")
        path, _ = QFileDialog.getOpenFileName(
            self, "Bild öffnen", start_dir,
            "Bilder (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.gif);;"
            "Alle Dateien (*)"
        )
        if path:
            self._load_image_async(path)

    def _load_image_async(self, path: str) -> None:
        """Lädt ein Bild im Hintergrund-Thread, damit die UI nicht blockt."""
        if self._worker_controller.is_loading:
            self._sb.showMessage(SM.LAEDT_BEREITS)
            return
        self._worker_controller.cancel_ai()
        self._sb.showMessage(f"⏳ Lädt: {Path(path).name}…")
        self._worker_controller.start_image_load(
            path,
            on_loaded=self._on_image_load_done,
            on_error=self._on_image_load_error,
        )

    def _on_image_load_done(self, img, path: str) -> None:
        self._canvas.apply_loaded_image(img, path)

    def _on_image_load_error(self, msg: str) -> None:
        self._sb.showMessage(f"Ladefehler: {msg}")

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

    def _save(self) -> None:
        """Quick-Save: speichert in den bekannten Pfad, sonst „Speichern unter…"."""
        if self._save_path is None:
            self._save_as()
            return
        if not self._canvas.has_image:
            self._sb.showMessage(SM.KEIN_BILD_ZUM_SPEICHERN)
            return
        self._canvas.save_image(self._save_path)

    def _save_as(self) -> None:
        """Speichern unter…: öffnet immer den Datei-Dialog."""
        if not self._canvas.has_image:
            self._sb.showMessage(SM.KEIN_BILD_ZUM_SPEICHERN)
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
            self, "Bild speichern unter…", suggest,
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

    # ── Recent-Files ────────────────────────────────────────────

    def _add_recent(self, path: str) -> None:
        if self._recent_menu is None:
            self._recent_files.add(path)
            return
        self._recent_menu.add(path)

    def _on_recent_missing(self, path: str) -> None:
        self._sb.showMessage(f"Datei nicht mehr vorhanden: {Path(path).name}")

    def _on_image_loaded(self, path: str) -> None:
        """Wird nach jedem load_image vom Canvas aufgerufen."""
        self._save_path = None
        self._add_recent(path)

    def _pick_color(self) -> None:
        c = QColorDialog.getColor(self._bg_color, self, "Hintergrundfarbe wählen")
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

        # Canvas-Version merken: falls der Nutzer inzwischen ein anderes
        # Bild lädt, wird das verspätete KI-Ergebnis in _on_ai_done verworfen.
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

    def _on_ai_done(self, img: Image.Image) -> None:
        # Versionsprüfung: Falls der Nutzer das Bild zwischenzeitlich gewechselt
        # hat, ist die Canvas-Revision erhöht worden und das KI-Ergebnis wird verworfen.
        if self._canvas.version != self._ai_input_version:
            self._sb.showMessage(SM.KI_ERGEBNIS_VERWORFEN)
            return
        self._canvas.apply_ai_result(img)

    def _on_ai_error(self, msg: str) -> None:
        self._sb.showMessage(f"KI-Fehler: {msg}")
        QMessageBox.warning(self, "KI-Fehler",
                            f"Fehler bei der automatischen Hintergrundentfernung:\n\n{msg}")

    def _on_history_changed(self, history: list[str]) -> None:
        self._history_popup.update_entries(history)

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._settings, self)
        dlg.exec()
