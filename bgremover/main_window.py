"""MainWindow – die Top-Level-Fensterklasse.

Verbatim aus ``BgRemover.py`` verschoben (Runde 5, Phase B – Schritt 11).
``from __future__ import annotations`` macht alle Annotationen lazy –
kein Laufzeit-Import des Monolithen noetig (Hazard H1: Kopplung zur
Canvas nur ueber Qt-Signale). Keine Verhaltensaenderung.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image
from PyQt6.QtCore import QSettings, QSize, Qt, QThread
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QButtonGroup,
    QColorDialog,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from bgremover import __version__
from bgremover.canvas import ImageCanvas
from bgremover.constants import (
    TOOL_BRUSH,
    TOOL_ERASER,
    TOOL_LASSO,
    TOOL_WAND,
    _CROP_BAR_HEIGHT,
    _THREAD_SHUTDOWN_MS,
    _TOOLBAR_BTN_SIZE,
    _TOOLBAR_ICON_SIZE,
    _TOOLBAR_WIDTH,
    _WINDOW_MIN_H,
    _WINDOW_MIN_W,
)
from bgremover.icons import make_tool_icon
from bgremover.menu_actions import MainMenuCallbacks, build_main_menu
from bgremover.recent_files import (
    RECENT_MAX as DEFAULT_RECENT_MAX,
    SETTINGS_RECENT_KEY as DEFAULT_SETTINGS_RECENT_KEY,
    RecentFiles,
    RecentFilesMenu,
)
from bgremover.right_panel import (
    TAB_STYLE as RIGHT_PANEL_TAB_STYLE,
    RightPanelActions,
    build_right_panel,
)
from bgremover.settings_dialog import SettingsDialog
from bgremover.theme import TOOL_STYLE, _Theme
from bgremover.worker_controller import WorkerController
from bgremover.workers import AIWorker, REMBG_AVAILABLE


class MainWindow(QMainWindow):
    # Anzahl der zuletzt geöffneten Bilder, die im Datei-Menü angezeigt werden.
    RECENT_MAX = DEFAULT_RECENT_MAX
    SETTINGS_RECENT_KEY = DEFAULT_SETTINGS_RECENT_KEY

    _TAB_STYLE = RIGHT_PANEL_TAB_STYLE

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"BgRemover Pro {__version__}")
        self.setMinimumSize(_WINDOW_MIN_W, _WINDOW_MIN_H)
        self._bg_color   = QColor(255, 255, 255)
        # Canvas-Version zum Startzeitpunkt der KI: verhindert, dass ein
        # verspätet eintreffendes Ergebnis ein inzwischen geladenes anderes
        # Bild überschreibt. Robuster als Objekt-Identität (is-Vergleich).
        self._ai_input_version: int = -1
        # Speicher-Pfad des aktuellen Bildes (für Quick-Save ⌘S).
        # Wird beim Laden eines neuen Bildes zurückgesetzt.
        self._save_path: str | None = None
        # Persistente Einstellungen (Recent-Files etc.).
        self._settings = QSettings("BgRemover", "BgRemover")
        self._recent_files = RecentFiles(
            self._settings, self.SETTINGS_RECENT_KEY, self.RECENT_MAX)
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
        self._sb.setStyleSheet("QStatusBar { background:#1a1a1a; color:#777; font-size:11px; border-top:1px solid #333; }")
        self.setStatusBar(self._sb)

        root_w = QWidget()
        self.setCentralWidget(root_w)
        root = QHBoxLayout(root_w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())

        # Canvas + Crop-Bestätigungsleiste in vertikalem Container
        canvas_container = QWidget()
        canvas_container.setStyleSheet("background: transparent;")
        cv_lay = QVBoxLayout(canvas_container)
        cv_lay.setContentsMargins(0, 0, 0, 0)
        cv_lay.setSpacing(0)

        # Canvas zuerst erzeugen, damit die Crop-Leisten-Buttons weiter
        # unten auf ein bereits zugewiesenes self._canvas verweisen
        # (sonst Forward-Reference im Lambda → mypy has-type).
        self._canvas = ImageCanvas()
        self._canvas.statusMsg.connect(self._sb.showMessage)
        self._canvas.historyChanged.connect(self._on_history_changed)
        self._canvas.cropModeChanged.connect(self._on_crop_mode_changed)
        self._canvas.imageLoaded.connect(self._on_image_loaded)
        self._canvas.loadRequested.connect(self._load_image_async)

        # ── Crop-Bestätigungsleiste (initial versteckt) ───────
        self._crop_bar = QFrame()
        self._crop_bar.setStyleSheet(
            "QFrame { background: #1e3020; border-bottom: 1px solid #3a7a4a; }")
        self._crop_bar.setFixedHeight(_CROP_BAR_HEIGHT)
        cb_lay = QHBoxLayout(self._crop_bar)
        cb_lay.setContentsMargins(14, 4, 14, 4); cb_lay.setSpacing(10)
        crop_lbl = QLabel("✂  Ausschnitt positionieren, dann bestätigen:")
        crop_lbl.setStyleSheet("color: #8fdd9f; font-size: 12px; font-weight: bold;"
                               " background: transparent;")
        cb_lay.addWidget(crop_lbl)
        cb_lay.addStretch()
        btn_confirm = QPushButton("✓  Zuschnitt anwenden")
        btn_confirm.setStyleSheet(
            "QPushButton { background:#2a6a2a; color:white; border:none;"
            " border-radius:5px; padding:7px 16px; font-size:12px; font-weight:bold; }"
            "QPushButton:hover { background:#3a8a3a; }")
        btn_confirm.clicked.connect(lambda: self._canvas.confirm_crop())
        btn_cancel = QPushButton("✗  Abbrechen")
        btn_cancel.setStyleSheet(
            "QPushButton { background:#5a2525; color:white; border:none;"
            " border-radius:5px; padding:7px 14px; font-size:12px; }"
            "QPushButton:hover { background:#7a3535; }")
        btn_cancel.clicked.connect(lambda: self._canvas.cancel_crop())
        cb_lay.addWidget(btn_confirm)
        cb_lay.addWidget(btn_cancel)
        self._crop_bar.setVisible(False)
        cv_lay.addWidget(self._crop_bar)

        self._hist_popup: QDialog | None = None

        cv_lay.addWidget(self._canvas, 1)

        root.addWidget(canvas_container, 1)
        root.addWidget(self._build_right_panel())

        self._sb.showMessage("Bild öffnen: Datei → Öffnen  oder  per Drag & Drop auf die Arbeitsfläche")

    def _build_toolbar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(_TOOLBAR_WIDTH)
        frame.setStyleSheet("QFrame { background: #242424; border-right: 1px solid #3a3a3a; }")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(9, 16, 9, 16)
        lay.setSpacing(8)

        self._btn_grp = QButtonGroup(self)
        self._btn_grp.setExclusive(True)

        def tbtn(icon_name: str, tip: str, tool: str) -> QToolButton:
            b = QToolButton()
            b.setIcon(make_tool_icon(icon_name, 38))
            b.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
            b.setToolTip(tip)
            b.setCheckable(True)
            b.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
            b.setStyleSheet(TOOL_STYLE)
            b.clicked.connect(lambda checked=False, t=tool: self._canvas.set_tool(t))
            self._btn_grp.addButton(b)
            lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
            return b

        self._btn_wand   = tbtn("wand",
            "Zauberstab\nKlick wählt Farbfläche (Flood Fill)\n"
            "Shift = addieren  ·  Ctrl = subtrahieren", TOOL_WAND)
        self._btn_brush  = tbtn("brush",
            "Pinsel\nBereiche manuell zur Auswahl hinzufügen", TOOL_BRUSH)
        self._btn_eraser = tbtn("eraser",
            "Radiergummi\nAuswahl-Bereiche wieder entfernen", TOOL_ERASER)
        self._btn_lasso  = tbtn("lasso",
            "Polygon-Lasso\nKlicken setzt Punkte · Doppelklick schließt Polygon\n"
            "Shift = addieren  ·  Ctrl = subtrahieren  ·  Esc = abbrechen", TOOL_LASSO)
        self._btn_wand.setChecked(True)

        # Trennlinie
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{_Theme.BORDER}")
        lay.addSpacing(4); lay.addWidget(sep); lay.addSpacing(4)

        self._btn_ai = QToolButton()
        self._btn_ai.setIcon(make_tool_icon("ai", 38))
        self._btn_ai.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
        self._btn_ai.setToolTip(
            "KI-Hintergrundentfernung (rembg)\nEntfernt den Hintergrund vollautomatisch"
            if REMBG_AVAILABLE else
            "rembg nicht installiert\n→ bash setup_bgremover.sh")
        self._btn_ai.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
        self._btn_ai.setStyleSheet(TOOL_STYLE)
        self._btn_ai.setEnabled(REMBG_AVAILABLE)
        self._btn_ai.clicked.connect(self._run_ai)
        lay.addWidget(self._btn_ai, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Trennlinie
        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color:{_Theme.BORDER}")
        lay.addSpacing(4); lay.addWidget(sep2); lay.addSpacing(4)

        # Rückgängig + Original
        HIST_STYLE = """
            QToolButton {
                color: #bbb; font-size: 20px; border: none;
                border-radius: 9px; background: #2e2e2e;
            }
            QToolButton:hover    { background: #3e3e3e; }
            QToolButton:pressed  { background: #252525; }
            QToolButton:disabled { color: #444; background: #222; }
        """

        def hist_btn(icon_name: str, tip: str, slot) -> QToolButton:
            b = QToolButton()
            b.setIcon(make_tool_icon(icon_name, 38))
            b.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
            b.setToolTip(tip)
            b.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
            b.setStyleSheet(HIST_STYLE)
            b.clicked.connect(slot)
            lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
            return b

        hist_btn("undo",     "Rückgängig  (Cmd+Z)\nLetzten Bearbeitungsschritt rückgängig machen",
                 lambda: self._canvas.undo())
        hist_btn("redo",     "Wiederherstellen  (Cmd+Shift+Z)\nLetzten rückgängig gemachten Schritt wiederherstellen",
                 lambda: self._canvas.redo())
        hist_btn("restore",  "Original wiederherstellen\nAlle Bearbeitungen verwerfen",
                 lambda: self._canvas.restore_original())
        self._btn_history = hist_btn(
            "history",
            "Änderungshistorie\nZeigt alle bisherigen Bearbeitungsschritte.\n"
            "Doppelklick auf Eintrag → zu diesem Schritt zurück",
            self._toggle_history_popup)

        lay.addStretch()

        def mini_btn(icon_name: str, tip: str, slot) -> QToolButton:
            b = QToolButton()
            b.setIcon(make_tool_icon(icon_name, 38))
            b.setIconSize(QSize(_TOOLBAR_ICON_SIZE, _TOOLBAR_ICON_SIZE))
            b.setToolTip(tip)
            b.setFixedSize(_TOOLBAR_BTN_SIZE, _TOOLBAR_BTN_SIZE)
            b.setStyleSheet(TOOL_STYLE)
            b.clicked.connect(slot)
            lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
            return b

        mini_btn("open", "Bild öffnen  (Cmd+O)",   self._open_image)
        mini_btn("save", "Bild speichern  (Cmd+S)", self._save)
        return frame

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
        self._lbl_tol = panel.tolerance_label
        self._sld_tol = panel.tolerance_slider
        self._lbl_brush = panel.brush_label
        self._sld_brush = panel.brush_slider
        self._spin_morph = panel.morph_spin
        self._color_btn = panel.color_button
        self._sld_rot = panel.rotation_slider
        self._spin_rot = panel.rotation_spin
        self._lbl_corner = panel.corner_label
        self._sld_corner = panel.corner_slider
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

    # ── Worker-Controller-Delegation ──────────────────────────

    @property
    def _load_thread(self) -> QThread | None:
        return self._worker_controller.load_thread

    @_load_thread.setter
    def _load_thread(self, thread: QThread | None) -> None:
        self._worker_controller.load_thread = thread

    @property
    def _ai_thread(self) -> QThread | None:
        return self._worker_controller.ai_thread

    @_ai_thread.setter
    def _ai_thread(self, thread: QThread | None) -> None:
        self._worker_controller.ai_thread = thread

    @property
    def _ai_worker(self) -> AIWorker | None:
        return self._worker_controller.ai_worker

    @_ai_worker.setter
    def _ai_worker(self, worker: AIWorker | None) -> None:
        self._worker_controller.ai_worker = worker

    @property
    def _warmup_thread(self) -> QThread | None:
        return self._worker_controller.warmup_thread

    @_warmup_thread.setter
    def _warmup_thread(self, thread: QThread | None) -> None:
        self._worker_controller.warmup_thread = thread

    @property
    def _warmup_done(self) -> bool:
        return self._worker_controller.warmup_done

    @_warmup_done.setter
    def _warmup_done(self, done: bool) -> None:
        self._worker_controller.warmup_done = done

    def _launch_worker(self, worker, quit_on: tuple, on_finished=None) -> QThread:
        return self._worker_controller.launch_worker(worker, quit_on, on_finished)

    # ── Sauberes Thread-Shutdown beim Schliessen ──────────────

    def _shutdown_thread(self, thread: QThread | None, name: str) -> None:
        self._worker_controller.shutdown_thread(thread, name)

    def closeEvent(self, event) -> None:
        """Stoppt alle Hintergrund-Threads, bevor das Fenster (und damit
        die QThread-C++-Objekte) zerstört wird – sonst stürzt Python
        beim Schliessen ab, solange z. B. der KI-Warmup noch läuft.
        """
        self._sb.showMessage("Beende…")
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
            self._sb.showMessage("Lädt bereits ein Bild…")
            return
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

    # ── rembg-Warmup ────────────────────────────────────────────

    def _start_rembg_warmup(self) -> None:
        """Lädt das rembg-Modell im Hintergrund, damit der erste KI-Klick
        nicht spürbar wartet."""
        self._sb.showMessage("🤖 KI-Modell wird geladen…")
        self._worker_controller.start_warmup(on_finished=self._on_warmup_done)

    def _on_warmup_done(self) -> None:
        self._sb.showMessage("🤖 KI bereit")

    def _save(self) -> None:
        """Quick-Save: speichert in den bekannten Pfad, sonst „Speichern unter…"."""
        if self._save_path is None:
            self._save_as()
            return
        if not self._canvas.has_image:
            self._sb.showMessage("Kein Bild zum Speichern")
            return
        self._canvas.save_image(self._save_path)

    def _save_as(self) -> None:
        """Speichern unter…: öffnet immer den Datei-Dialog."""
        if not self._canvas.has_image:
            self._sb.showMessage("Kein Bild zum Speichern")
            return
        save_dir = self._settings.value("save_dir", "")
        if self._save_path:
            suggest = self._save_path
        elif save_dir:
            suggest = str(Path(save_dir) / "bild_bearbeitet")
        else:
            suggest = "bild_bearbeitet"
        preferred = self._settings.value("preferred_format", "PNG")
        all_filters = {
            "PNG":  "PNG (*.png)",
            "JPEG": "JPEG (*.jpg)",
            "WebP": "WebP (*.webp)",
            "TIFF": "TIFF (*.tif)",
        }
        ordered = [preferred] + [f for f in all_filters if f != preferred]
        filter_str = ";;".join(all_filters[f] for f in ordered)
        path, _ = QFileDialog.getSaveFileName(
            self, "Bild speichern unter…", suggest, filter_str
        )
        if path:
            # Pfad nur als Quick-Save-Ziel merken, wenn das Speichern
            # tatsächlich geklappt hat.
            if self._canvas.save_image(path):
                self._save_path = path

    # ── Recent-Files ────────────────────────────────────────────

    def _recent_paths(self) -> list[str]:
        return self._recent_files.paths()

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
            self._sb.showMessage("Kein Bild geladen")
            return
        if self._worker_controller.is_ai_running:
            self._sb.showMessage("KI läuft bereits…")
            return
        self._sb.showMessage("🤖 KI verarbeitet Bild… (kann einige Sekunden dauern)")
        self._btn_ai.setEnabled(False)

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
        self._btn_ai.setEnabled(True)
        self._ai_input_version = -1

    def _on_ai_done(self, img: Image.Image) -> None:
        # Versionsprüfung: Falls der Nutzer das Bild zwischenzeitlich gewechselt
        # hat, ist _version erhöht worden und das KI-Ergebnis wird verworfen.
        if self._canvas.version != self._ai_input_version:
            self._sb.showMessage(
                "KI-Ergebnis verworfen – Bild wurde inzwischen geändert")
            return
        self._canvas.apply_ai_result(img)

    def _on_ai_error(self, msg: str) -> None:
        self._sb.showMessage(f"KI-Fehler: {msg}")
        QMessageBox.warning(self, "KI-Fehler",
                            f"Fehler bei der automatischen Hintergrundentfernung:\n\n{msg}")

    def _build_history_popup(self) -> None:
        popup = QDialog(self, Qt.WindowType.Tool)
        popup.setWindowTitle("Änderungshistorie")
        popup.setMinimumWidth(270)
        popup.setStyleSheet("QDialog { background: #1a1a1a; }")

        lay = QVBoxLayout(popup)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        lbl = QLabel("Doppelklick auf Eintrag → zu diesem Schritt zurück")
        lbl.setStyleSheet("color: #666; font-size: 10px; background: transparent;")
        lay.addWidget(lbl)

        self._history_list = QListWidget()
        self._history_list.setStyleSheet("""
            QListWidget {
                background: #141414; color: #bbb; border: 1px solid #2a2a2a;
                border-radius: 6px; font-size: 11px;
            }
            QListWidget::item { padding: 6px 10px; border-bottom: 1px solid #1e1e1e; }
            QListWidget::item:selected { background: #1e3a5a; color: #7aacdd; }
            QListWidget::item:hover:!selected { background: #202020; }
        """)
        self._history_list.setMinimumHeight(200)
        self._history_list.setToolTip(
            "Verlauf aller Bearbeitungsschritte.\n"
            "Doppelklick auf einen Eintrag springt zu diesem Schritt zurück.")
        self._history_list.itemDoubleClicked.connect(self._undo_to_item)
        lay.addWidget(self._history_list)

        self._hist_popup = popup

    def _toggle_history_popup(self) -> None:
        if self._hist_popup is None:
            self._build_history_popup()
        # _build_history_popup setzt self._hist_popup garantiert.
        assert self._hist_popup is not None
        if self._hist_popup.isVisible():
            self._hist_popup.hide()
        else:
            gp = self._btn_history.mapToGlobal(self._btn_history.rect().topRight())
            self._hist_popup.move(gp.x() + 4, gp.y())
            self._hist_popup.show()
            self._hist_popup.raise_()

    def _on_history_changed(self, history: list) -> None:
        if not hasattr(self, '_history_list'):
            return
        self._history_list.clear()
        for desc in history:
            self._history_list.addItem(desc)

    def _on_crop_mode_changed(self, active: bool) -> None:
        self._crop_bar.setVisible(active)

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._settings, self)
        dlg.exec()

    def _undo_to_item(self, item) -> None:
        row = self._history_list.row(item)
        self._canvas.undo_to(row + 1)
