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
from PyQt6.QtGui import QAction, QColor, QKeySequence
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
    QScrollArea,
    QSlider,
    QSpinBox,
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
    _COLOR_BTN_SIZE,
    _CROP_BAR_HEIGHT,
    _IS_MACOS,
    _RIGHT_PANEL_WIDTH,
    _TAB_ICON_PX,
    _THREAD_SHUTDOWN_MS,
    _TOOLBAR_BTN_SIZE,
    _TOOLBAR_ICON_SIZE,
    _TOOLBAR_WIDTH,
    _WINDOW_MIN_H,
    _WINDOW_MIN_W,
    logger,
)
from bgremover.icons import make_tool_icon
from bgremover.recent_files import (
    RECENT_MAX as DEFAULT_RECENT_MAX,
    SETTINGS_RECENT_KEY as DEFAULT_SETTINGS_RECENT_KEY,
    RecentFiles,
    RecentFilesMenu,
)
from bgremover.settings_dialog import SettingsDialog
from bgremover.theme import SLD_STYLE, TOOL_STYLE, _Theme
from bgremover.widgets import TopIconTabWidget
from bgremover.workers import (
    REMBG_AVAILABLE,
    AIWorker,
    ImageLoadWorker,
    RembgWarmupWorker,
    _Worker,
)


class MainWindow(QMainWindow):
    # Anzahl der zuletzt geöffneten Bilder, die im Datei-Menü angezeigt werden.
    RECENT_MAX = DEFAULT_RECENT_MAX
    SETTINGS_RECENT_KEY = DEFAULT_SETTINGS_RECENT_KEY

    _TAB_STYLE = f"""
        QTabWidget::pane {{ border: none; background: {_Theme.BG_PANEL}; }}
        QTabBar {{ background: {_Theme.BG_TABBAR}; }}
        QTabBar::tab {{
            background: #1e1e1e; color: #666;
            padding: 10px 0px; min-width: 94px;
            font-size: 12px; border: none;
            border-bottom: 3px solid transparent;
        }}
        QTabBar::tab:selected {{
            color: {_Theme.TEXT_BRIGHT}; background: {_Theme.BG_PANEL};
            border-bottom: 3px solid {_Theme.ACCENT}; font-weight: bold;
        }}
        QTabBar::tab:hover:!selected {{ color: #aaa; background: #242424; }}
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"BgRemover Pro {__version__}")
        self.setMinimumSize(_WINDOW_MIN_W, _WINDOW_MIN_H)
        self._bg_color   = QColor(255, 255, 255)
        self._ai_thread: QThread | None = None
        self._ai_worker: AIWorker | None = None
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
        # Asynchrones Bildladen
        self._load_thread: QThread | None = None
        # rembg-Warmup (Hintergrund-Modellladung)
        self._warmup_thread: QThread | None = None
        self._warmup_done = False
        self._build_ui()
        self._build_menu()
        if REMBG_AVAILABLE:
            self._start_rembg_warmup()

    # ── Panel-Hilfsmethoden (ehem. nested in _build_right_panel) ─

    @staticmethod
    def _make_section(title: str, accent: str = "#4a90d9") -> tuple:
        """Sektion ohne QGroupBox – farbiger Titel + dünne Trennlinie."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        v = QVBoxLayout(container)
        v.setSpacing(10)
        v.setContentsMargins(0, 14, 0, 10)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            color: {accent};
            font-size: 13px;
            font-weight: bold;
            background: transparent;
            padding: 2px 0 4px 8px;
            border-left: 3px solid {accent};
        """)
        v.addWidget(title_lbl)
        return container, v

    @staticmethod
    def _make_label(text: str, color: str = "#888", size: int = 12) -> QLabel:
        """Einfaches Info-Label mit anpassbarer Farbe und Schriftgrösse."""
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {color}; font-size: {size}px; background: transparent;")
        lbl.setWordWrap(True)
        return lbl

    @staticmethod
    def _make_icon_row(icon_name: str, text: str, color: str = "#888",
                       size: int = 12, icon_px: int = 18) -> QWidget:
        """Info-Zeile: Werkzeug-Icon (wie in der Toolbar) + Text, klein."""
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        ic = QLabel()
        ic.setPixmap(make_tool_icon(icon_name, icon_px)
                     .pixmap(QSize(icon_px, icon_px)))
        ic.setFixedSize(icon_px, icon_px)
        ic.setStyleSheet("background: transparent;")
        txt = QLabel(text)
        txt.setStyleSheet(
            f"color: {color}; font-size: {size}px; background: transparent;")
        txt.setWordWrap(True)
        h.addWidget(ic, 0, Qt.AlignmentFlag.AlignVCenter)
        h.addWidget(txt, 1)
        return row

    @staticmethod
    def _make_hdivider() -> QWidget:
        """Dünne horizontale Trennlinie für das rechte Panel."""
        f = QWidget()
        f.setFixedHeight(1)
        f.setStyleSheet(f"background: {_Theme.DIVIDER};")
        return f

    @staticmethod
    def _make_scroll_tab() -> tuple:
        """Gibt (outer_widget, inner_layout) mit ScrollArea zurück."""
        outer_w = QWidget()
        outer_w.setStyleSheet(f"background: {_Theme.BG_PANEL};")
        outer_lay = QVBoxLayout(outer_w)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: #1a1a1a; border: none; }
            QScrollBar:vertical { background: #1a1a1a; width: 6px; margin: 0; }
            QScrollBar::handle:vertical {
                background: #3a3a3a; border-radius: 3px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        inner_w = QWidget()
        inner_w.setStyleSheet(f"background: {_Theme.BG_PANEL};")
        inner_lay = QVBoxLayout(inner_w)
        inner_lay.setContentsMargins(16, 16, 16, 16)
        inner_lay.setSpacing(14)
        scroll.setWidget(inner_w)
        outer_lay.addWidget(scroll)
        return outer_w, inner_lay

    @staticmethod
    def _make_panel_btn(label: str, bg: str, fg: str, hover: str,
                        tooltip: str = "", height: int = 36,
                        icon_name: str = "") -> QPushButton:
        """Stilisierter Aktions-Button für das rechte Panel."""
        b = QPushButton(label)
        b.setStyleSheet(f"""
            QPushButton {{
                background: {bg}; color: {fg}; border: none;
                border-radius: 8px; padding: 0 14px;
                font-size: 12px; font-weight: 500;
                min-height: {height}px; text-align: center;
            }}
            QPushButton:hover {{ background: {hover}; }}
            QPushButton:pressed {{ background: {bg}; }}
            QPushButton:disabled {{ background: #252525; color: #555; }}
        """)
        if icon_name:
            b.setIcon(make_tool_icon(icon_name, 22))
            b.setIconSize(QSize(22, 22))
        if tooltip:
            b.setToolTip(tooltip)
        return b

    @staticmethod
    def _make_slider(lo: int, hi: int, val: int, tip: str = "") -> QSlider:
        """Horizontaler Schieberegler mit einheitlichem Panel-Stil."""
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(lo, hi)
        s.setValue(val)
        s.setStyleSheet(SLD_STYLE)
        if tip:
            s.setToolTip(tip)
        return s

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
        frame = QFrame()
        frame.setFixedWidth(_RIGHT_PANEL_WIDTH)
        frame.setStyleSheet("QFrame { background: #1a1a1a; border-left: 1px solid #333; }")
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Tab-Widget ────────────────────────────────────────
        tabs = TopIconTabWidget(_TAB_ICON_PX)
        tabs.setDocumentMode(True)
        tabs.setStyleSheet(self._TAB_STYLE)
        tabs.setUsesScrollButtons(False)   # niemals Scroll-Pfeile — alle Tabs sichtbar
        tabs.setIconSize(QSize(_TAB_ICON_PX, _TAB_ICON_PX))
        outer.addWidget(tabs)

        # Jeder Builder hängt genau einen Tab an – Aufrufreihenfolge = Tab-Index.
        self._build_tab_selection(tabs)
        self._build_tab_background(tabs)
        self._build_tab_transform(tabs)
        self._build_tab_shape(tabs)
        return frame

    # ── Tab-Builder (je genau ein Tab) ───────────────────────

    def _build_tab_selection(self, tabs: TopIconTabWidget) -> None:
        """Tab 1 – Auswahl 🎯: Werkzeug-Hinweise, Toleranz/Pinsel, Morphologie."""
        t1, l1 = self._make_scroll_tab()
        idx = tabs.addTab(t1, "Auswahl")
        tabs.setTabIcon(idx, make_tool_icon("clear_sel", _TAB_ICON_PX))
        tabs.setTabToolTip(idx, "Auswahl – Zauberstab, Pinsel, Radiergummi")

        g_tool, gt = self._make_section("Werkzeug", "#4a90d9")
        hint_box = QWidget()
        hint_box.setStyleSheet("background:#1e2a38; border-radius:7px;")
        hint_lay = QVBoxLayout(hint_box)
        hint_lay.setContentsMargins(10, 8, 10, 8)
        hint_lay.setSpacing(3)
        for icon_name, txt in [
            ("wand",   "Zauberstab — Farbfläche auswählen"),
            ("brush",  "Pinsel — Auswahl aufmalen"),
            ("eraser", "Radiergummi — Auswahl entfernen"),
            ("lasso",  "Polygon-Lasso — Punkte klicken, Doppelklick abschließen"),
        ]:
            hint_lay.addWidget(self._make_icon_row(icon_name, txt, "#7aacdd", 11))
        hint_lay.addWidget(self._make_hdivider())
        _sub_mod = "Cmd" if _IS_MACOS else "Ctrl"
        hint_lay.addWidget(self._make_label("Shift+Klick  →  Auswahl addieren", "#888", 11))
        hint_lay.addWidget(self._make_label(f"{_sub_mod}+Klick   →  Auswahl subtrahieren", "#888", 11))
        gt.addWidget(hint_box)
        l1.addWidget(g_tool)

        g_sel, gs = self._make_section("Einstellungen", "#4a90d9")
        self._lbl_tol = self._make_label("Toleranz (Zauberstab):  30", "#aaa")
        self._sld_tol = self._make_slider(0, 255, 30,
            "Steuert wie ähnlich Farben sein müssen um ausgewählt zu werden.\n"
            "Niedrig = nur sehr ähnliche Farben · Hoch = viele Farbtöne")
        def _on_tol(v: int) -> None:
            self._canvas.set_tolerance(v)
            self._lbl_tol.setText(f"Toleranz (Zauberstab):  {v}")
        self._sld_tol.valueChanged.connect(_on_tol)
        gs.addWidget(self._lbl_tol)
        gs.addWidget(self._sld_tol)
        gs.addWidget(self._make_hdivider())
        self._lbl_brush = self._make_label("Pinselgröße:  30 px", "#aaa")
        self._sld_brush = self._make_slider(4, 200, 30,
            "Größe des Pinsel-/Radiergummi-Werkzeugs in Pixeln")
        def _on_brush(v: int) -> None:
            self._canvas.set_brush_size(v)
            self._lbl_brush.setText(f"Pinselgröße:  {v} px")
        self._sld_brush.valueChanged.connect(_on_brush)
        gs.addWidget(self._lbl_brush)
        gs.addWidget(self._sld_brush)
        l1.addWidget(g_sel)

        btn_clr = self._make_panel_btn("Auswahl aufheben", "#2a2a2a", "#c0c0c0", "#363636",
                      "Hebt die aktuelle Auswahl auf (auch: Esc-Taste)",
                      icon_name="clear_sel")
        btn_clr.clicked.connect(lambda _=False: self._canvas.clear_selection())
        l1.addWidget(btn_clr)

        btn_inv = self._make_panel_btn("Auswahl invertieren", "#2a2a2a", "#c0c0c0", "#363636",
                      "Tauscht aus- und nicht-ausgewählte Bereiche  (⌘⇧I)",
                      icon_name="clear_sel")
        btn_inv.clicked.connect(lambda _=False: self._canvas.invert_selection())
        l1.addWidget(btn_inv)

        # Auswahl erweitern / schrumpfen mit Radius-Spinbox
        morph_row = QHBoxLayout(); morph_row.setSpacing(6)
        self._spin_morph = QSpinBox()
        self._spin_morph.setRange(1, 20); self._spin_morph.setValue(2)
        self._spin_morph.setSuffix(" px")
        self._spin_morph.setFixedWidth(72)
        self._spin_morph.setToolTip(
            "Radius in Pixeln für Erweitern/Schrumpfen der Auswahl")
        self._spin_morph.setStyleSheet(
            "QSpinBox { background:#222; color:#ddd; border:1px solid #3a3a3a;"
            " border-radius:6px; padding:3px 5px; font-size:12px; }"
            "QSpinBox::up-button, QSpinBox::down-button { width:18px; }")
        btn_expand = self._make_panel_btn("➕ Erweitern", "#1a3a1a", "#a0d0a0", "#2a5a2a",
                         "Erweitert die Auswahl um den eingestellten Radius")
        btn_expand.clicked.connect(
            lambda _=False: self._canvas.expand_selection(self._spin_morph.value()))
        btn_shrink = self._make_panel_btn("➖ Schrumpfen", "#3a1a1a", "#d0a0a0", "#5a2a2a",
                         "Schrumpft die Auswahl um den eingestellten Radius")
        btn_shrink.clicked.connect(
            lambda _=False: self._canvas.shrink_selection(self._spin_morph.value()))
        morph_row.addWidget(self._spin_morph)
        morph_row.addWidget(btn_expand, 1)
        morph_row.addWidget(btn_shrink, 1)
        l1.addLayout(morph_row)

        l1.addStretch()

    def _build_tab_background(self, tabs: TopIconTabWidget) -> None:
        """Tab 2 – Hintergrund 🖼: transparent machen oder Farbe ersetzen."""
        t2, l2 = self._make_scroll_tab()
        idx = tabs.addTab(t2, "Hintergrund")
        tabs.setTabIcon(idx, make_tool_icon("bg", _TAB_ICON_PX))
        tabs.setTabToolTip(idx, "Hintergrund – Entfernen, Farbe ersetzen")

        g_bg, gb = self._make_section("Hintergrund bearbeiten", "#e05555")
        btn_rem = self._make_panel_btn("Entfernen (transparent)", "#6a1a1a", "white", "#882020",
                      "Macht den ausgewählten Bereich vollständig transparent.\n"
                      "Tipp: Zuerst mit Zauberstab Hintergrund auswählen.",
                      height=38, icon_name="transparency")
        btn_rem.clicked.connect(lambda _=False: self._canvas.apply_remove())
        gb.addWidget(btn_rem)

        gb.addWidget(self._make_hdivider())
        gb.addWidget(self._make_label("Farbe wählen und Auswahl einfärben:", "#888"))
        color_row = QHBoxLayout(); color_row.setSpacing(8)
        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(_COLOR_BTN_SIZE, _COLOR_BTN_SIZE)
        self._color_btn.setToolTip("Klicken um Ersatz-Hintergrundfarbe zu wählen")
        self._color_btn.setStyleSheet(
            "QPushButton { border-radius:6px; border:2px solid #555; }"
            "QPushButton:hover { border-color: #4a90d9; }")
        self._color_btn.clicked.connect(lambda _=False: self._pick_color())
        self._update_color_btn()
        color_row.addWidget(self._color_btn)
        btn_repl = self._make_panel_btn("Farbe ersetzen", "#143a5a", "white", "#1e5080",
                       "Füllt den ausgewählten Bereich mit der gewählten Farbe",
                       icon_name="bg")
        btn_repl.clicked.connect(lambda _=False: self._canvas.apply_replace(self._bg_color))
        color_row.addWidget(btn_repl, 1)
        gb.addLayout(color_row)
        l2.addWidget(g_bg)

        l2.addStretch()

    def _build_tab_transform(self, tabs: TopIconTabWidget) -> None:
        """Tab 3 – Transform ⟲: Drehen (Schnell + freier Winkel) und Spiegeln."""
        t3, l3 = self._make_scroll_tab()
        idx = tabs.addTab(t3, "Drehen/Spiegeln")
        tabs.setTabIcon(idx, make_tool_icon("transparency", _TAB_ICON_PX))
        tabs.setTabToolTip(idx, "Transform – Drehen, Spiegeln")

        g_rot, gr2 = self._make_section("Drehen", "#e09a30")
        ROT_BG = "#2e2510"; ROT_FG = "#f0c060"; ROT_HV = "#4a3a18"

        # Schnell-Drehung
        gr2.addWidget(self._make_label("Schnell-Drehung:", "#888"))
        row_q1 = QHBoxLayout(); row_q1.setSpacing(6)
        for label, deg, tip in [
            ("↺ 90° links",   90,  "90° gegen den Uhrzeigersinn drehen"),
            ("↻ 90° rechts", -90, "90° im Uhrzeigersinn drehen"),
        ]:
            b = self._make_panel_btn(label, ROT_BG, ROT_FG, ROT_HV, tip)
            b.clicked.connect(lambda _=False, d=deg: self._canvas.apply_rotate(d))
            row_q1.addWidget(b)
        gr2.addLayout(row_q1)

        row_q2 = QHBoxLayout(); row_q2.setSpacing(6)
        for label, deg, tip in [
            ("↺ 180°",  180, "Bild um 180° drehen"),
            ("↺ 270°",  270, "270° gegen den Uhrzeigersinn (= 90° rechts)"),
        ]:
            b = self._make_panel_btn(label, ROT_BG, ROT_FG, ROT_HV, tip)
            b.clicked.connect(lambda _=False, d=deg: self._canvas.apply_rotate(d))
            row_q2.addWidget(b)
        gr2.addLayout(row_q2)

        gr2.addWidget(self._make_hdivider())
        gr2.addWidget(self._make_label("Freier Winkel:", "#888"))
        row_free = QHBoxLayout(); row_free.setSpacing(6)
        self._sld_rot = QSlider(Qt.Orientation.Horizontal)
        self._sld_rot.setRange(-180, 180); self._sld_rot.setValue(0)
        self._sld_rot.setStyleSheet(SLD_STYLE)
        self._sld_rot.setToolTip("Drehwinkel einstellen: −180° bis +180°")
        self._spin_rot = QSpinBox()
        self._spin_rot.setRange(-180, 180); self._spin_rot.setValue(0)
        self._spin_rot.setSuffix("°")
        self._spin_rot.setFixedWidth(66)
        self._spin_rot.setToolTip("Drehwinkel direkt eingeben")
        self._spin_rot.setStyleSheet(
            "QSpinBox { background:#222; color:#ddd; border:1px solid #3a3a3a;"
            " border-radius:6px; padding:3px 5px; font-size:12px; }"
            "QSpinBox::up-button, QSpinBox::down-button { width:18px; }")
        self._sld_rot.valueChanged.connect(lambda v: self._spin_rot.setValue(v))
        self._spin_rot.valueChanged.connect(lambda v: self._sld_rot.setValue(v))
        row_free.addWidget(self._sld_rot, 1)
        row_free.addWidget(self._spin_rot)
        gr2.addLayout(row_free)

        btn_rot_free = self._make_panel_btn("Winkel anwenden", ROT_BG, ROT_FG, ROT_HV,
                           "Dreht das Bild um den eingestellten Winkel.\n"
                           "Transparente Ecken entstehen bei schrägen Winkeln.",
                           icon_name="undo")
        btn_rot_free.clicked.connect(
            lambda _=False: self._canvas.apply_rotate(self._spin_rot.value()))
        gr2.addWidget(btn_rot_free)
        l3.addWidget(g_rot)

        g_flip, gf = self._make_section("Spiegeln", "#30a0a0")
        row_flip = QHBoxLayout(); row_flip.setSpacing(6)
        btn_fh = self._make_panel_btn("Horizontal", "#0e2a2a", "#7adada", "#1a4040",
                     "Bild horizontal spiegeln (links ↔ rechts)")
        btn_fh.clicked.connect(lambda _=False: self._canvas.apply_flip(True))
        row_flip.addWidget(btn_fh)
        btn_fv = self._make_panel_btn("Vertikal", "#0e2a2a", "#7adada", "#1a4040",
                     "Bild vertikal spiegeln (oben ↕ unten)")
        btn_fv.clicked.connect(lambda _=False: self._canvas.apply_flip(False))
        row_flip.addWidget(btn_fv)
        gf.addLayout(row_flip)
        l3.addWidget(g_flip)
        l3.addStretch()

    def _build_tab_shape(self, tabs: TopIconTabWidget) -> None:
        """Tab 4 – Form & Zuschnitt ⬤: Ecken abrunden, Format-/Crop-Auswahl."""
        t4, l4 = self._make_scroll_tab()
        idx = tabs.addTab(t4, "Form")
        tabs.setTabIcon(idx, make_tool_icon("form", _TAB_ICON_PX))
        tabs.setTabToolTip(idx, "Form & Zuschnitt – Ecken abrunden, Format-Auswahl")

        g_corner, gc = self._make_section("Ecken abrunden", "#30c060")
        self._lbl_corner = self._make_label("Radius:  0 px", "#aaa")
        self._sld_corner = self._make_slider(0, 500, 0,
            "Radius der Eckenrundung in Pixeln.\n0 = keine Rundung · 500 = maximal rund")
        self._sld_corner.valueChanged.connect(
            lambda v: self._lbl_corner.setText(f"Radius:  {v} px"))
        gc.addWidget(self._lbl_corner)
        gc.addWidget(self._sld_corner)
        btn_corner = self._make_panel_btn("Ecken abrunden", "#0e2a14", "#7add9a", "#1a4520",
                         "Wendet die Eckenrundung an.\n"
                         "Das Ergebnis wird als PNG mit transparenten Ecken gespeichert.",
                         height=38, icon_name="form")
        btn_corner.clicked.connect(
            lambda _=False: self._canvas.apply_round_corners(self._sld_corner.value()))
        gc.addWidget(btn_corner)
        l4.addWidget(g_corner)

        g_fmt, gfm = self._make_section("Ausgabe-Format & Zuschnitt", "#9060d0")

        info_box = QWidget()
        info_box.setStyleSheet("background:#1e1628; border-radius:7px;")
        info_b = QVBoxLayout(info_box)
        info_b.setContentsMargins(10, 8, 10, 8)
        info_b.addWidget(self._make_label(
            "⇲ Format wählen → Rahmen erscheint auf dem Bild\n"
            "• Rahmen verschieben: Mitte ziehen\n"
            "• Größe ändern: Ecken ziehen (Proportionen bleiben)", "#8a7aaa", 10))
        gfm.addWidget(info_box)

        # Kreis + Quadrat
        gfm.addWidget(self._make_label("Sonderformate:", "#777", 10))
        r_special = QHBoxLayout(); r_special.setSpacing(6)
        for label, tip, slot in [
            ("⬤  Kreis",  "Runden Ausschnitt positionieren und zuschneiden",
             self._canvas.start_crop_circle),
            ("■  1 : 1", "Quadratischen Ausschnitt positionieren",
             lambda: self._canvas.start_crop_ratio(1, 1)),
        ]:
            b = self._make_panel_btn(label, "#141e38", "#8aaedd", "#1e2e52", tip)
            b.clicked.connect(lambda _=False, fn=slot: fn())
            r_special.addWidget(b)
        gfm.addLayout(r_special)

        # Querformat
        gfm.addWidget(self._make_hdivider())
        gfm.addWidget(self._make_label("Querformat:", "#777", 10))
        LAND_FORMATS = [
            ("16 : 9", 16, 9), ("4 : 3",  4, 3),
            ("3 : 2",  3, 2),  ("2 : 1",  2, 1),
            ("7 : 4.5", 14, 9),
        ]
        for i in range(0, len(LAND_FORMATS), 2):
            row_fmt = QHBoxLayout(); row_fmt.setSpacing(6)
            for label, rw, rh in LAND_FORMATS[i:i+2]:
                b = self._make_panel_btn(f"▬  {label}", "#1e1428", "#c0a0f0", "#2e1e44",
                        f"Querformat {label} — Ecken ziehen für Größe, Mitte zum Verschieben")
                b.clicked.connect(
                    lambda _=False, w=rw, h=rh: self._canvas.start_crop_ratio(w, h))
                row_fmt.addWidget(b)
            gfm.addLayout(row_fmt)

        # Hochformat
        gfm.addWidget(self._make_hdivider())
        gfm.addWidget(self._make_label("Hochformat:", "#777", 10))
        PORT_FORMATS = [("9 : 16", 9, 16), ("3 : 4", 3, 4)]
        row_port = QHBoxLayout(); row_port.setSpacing(6)
        for label, rw, rh in PORT_FORMATS:
            b = self._make_panel_btn(f"▮  {label}", "#141e28", "#90c8cc", "#1e2e38",
                    f"Hochformat {label} — Ecken ziehen für Größe, Mitte zum Verschieben")
            b.clicked.connect(
                lambda _=False, w=rw, h=rh: self._canvas.start_crop_ratio(w, h))
            row_port.addWidget(b)
        gfm.addLayout(row_port)
        l4.addWidget(g_fmt)
        l4.addStretch()

    def _build_menu(self) -> None:
        mb = self.menuBar()
        # menuBar()/addMenu() liefern laut PyQt-Stub `Optional`, in der
        # Praxis aber nie None – einmalige asserts narrowen den Typ und
        # ersparen Dutzende Punkt-zu-Punkt-Guards.
        assert mb is not None
        mb.setStyleSheet("""
            QMenuBar { background: #1a1a1a; color: #ccc; }
            QMenuBar::item:selected { background: #333; }
            QMenu { background: #252525; color: #ccc; border: 1px solid #3a3a3a; }
            QMenu::item:selected { background: #4a90d9; }
        """)

        file_m = mb.addMenu("Datei")
        assert file_m is not None
        a_open = QAction("Öffnen…", self)
        a_open.setShortcut(QKeySequence("Ctrl+O"))
        a_open.triggered.connect(self._open_image)
        file_m.addAction(a_open)

        # Submenü „Zuletzt geöffnet" – wird nach dem ersten load_image
        # mit Inhalt befüllt, persistiert über QSettings.
        recent_menu = file_m.addMenu("Zuletzt geöffnet")
        assert recent_menu is not None
        self._recent_menu = RecentFilesMenu(
            self,
            recent_menu,
            self._recent_files,
            open_path=self._load_image_async,
            missing_path=self._on_recent_missing,
        )

        file_m.addSeparator()

        a_save = QAction("Speichern", self)
        a_save.setShortcut(QKeySequence("Ctrl+S"))
        a_save.triggered.connect(self._save)
        file_m.addAction(a_save)

        a_save_as = QAction("Speichern unter…", self)
        a_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        a_save_as.triggered.connect(self._save_as)
        file_m.addAction(a_save_as)

        edit_m = mb.addMenu("Bearbeiten")
        assert edit_m is not None
        a_undo = QAction("Rückgängig", self)
        a_undo.setShortcut(QKeySequence("Ctrl+Z"))
        a_undo.triggered.connect(self._canvas.undo)
        edit_m.addAction(a_undo)

        a_redo = QAction("Wiederherstellen", self)
        a_redo.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        a_redo.triggered.connect(self._canvas.redo)
        edit_m.addAction(a_redo)

        edit_m.addSeparator()
        a_rot_l = QAction("90° links drehen", self)
        a_rot_l.setShortcut(QKeySequence("Ctrl+Left"))
        a_rot_l.triggered.connect(lambda: self._canvas.apply_rotate(90))
        edit_m.addAction(a_rot_l)

        a_rot_r = QAction("90° rechts drehen", self)
        a_rot_r.setShortcut(QKeySequence("Ctrl+Right"))
        a_rot_r.triggered.connect(lambda: self._canvas.apply_rotate(-90))
        edit_m.addAction(a_rot_r)

        a_rot_180 = QAction("180° drehen", self)
        a_rot_180.triggered.connect(lambda: self._canvas.apply_rotate(180))
        edit_m.addAction(a_rot_180)

        a_flip_h = QAction("Horizontal spiegeln", self)
        a_flip_h.triggered.connect(lambda: self._canvas.apply_flip(True))
        edit_m.addAction(a_flip_h)

        a_flip_v = QAction("Vertikal spiegeln", self)
        a_flip_v.triggered.connect(lambda: self._canvas.apply_flip(False))
        edit_m.addAction(a_flip_v)
        edit_m.addSeparator()

        a_clear = QAction("Auswahl aufheben", self)
        a_clear.setShortcut(QKeySequence("Escape"))
        a_clear.triggered.connect(self._canvas.clear_selection)
        edit_m.addAction(a_clear)

        a_invert = QAction("Auswahl invertieren", self)
        a_invert.setShortcut(QKeySequence("Ctrl+Shift+I"))
        a_invert.triggered.connect(self._canvas.invert_selection)
        edit_m.addAction(a_invert)

        a_orig = QAction("Original wiederherstellen", self)
        a_orig.triggered.connect(self._canvas.restore_original)
        edit_m.addAction(a_orig)

        view_m = mb.addMenu("Ansicht")
        assert view_m is not None
        a_fit = QAction("Fit to View", self)
        a_fit.setShortcut(QKeySequence("Ctrl+0"))
        a_fit.triggered.connect(lambda: self._canvas.fit_to_view())
        view_m.addAction(a_fit)

        extras_m = mb.addMenu("Extras")
        assert extras_m is not None
        a_prefs = QAction("Einstellungen…", self)
        a_prefs.setShortcut(QKeySequence("Ctrl+,"))
        a_prefs.triggered.connect(self._open_settings)
        extras_m.addAction(a_prefs)

    # ── Thread-Hilfsmethode ───────────────────────────────────

    def _launch_worker(self, worker: _Worker | RembgWarmupWorker,
                       quit_on: tuple,
                       on_finished=None) -> QThread:
        """Startet *worker* in einem neuen QThread.

        *quit_on* ist ein Tupel von Worker-Signalen, die thread.quit() auslösen
        (typischerweise (worker.finished, worker.error)).
        *on_finished* wird an thread.finished angehängt, falls angegeben.
        """
        thread = QThread(self)
        # Starke Referenz: MainWindow → thread → worker. Ohne sie sammelt
        # CPython den Worker direkt nach dem Aufruf ein (PyQt verbindet
        # Slots gebundener Methoden nur schwach) – run() liefe nie, das
        # Bild würde lautlos nicht geladen. setattr statt Attribut-
        # Zuweisung, weil QThread den Slot nicht im Type-Stub deklariert.
        setattr(thread, "_worker", worker)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        for sig in quit_on:
            sig.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        if on_finished is not None:
            thread.finished.connect(on_finished)
        thread.start()
        return thread

    # ── Sauberes Thread-Shutdown beim Schliessen ──────────────

    def _shutdown_thread(self, thread: QThread | None, name: str) -> None:
        """Beendet *thread* sauber, bevor das Fenster zerstört wird.

        Worker-run() macht blockierende C-Aufrufe (rembg) – quit()
        allein reicht nicht. Reihenfolge: quit() → wait(timeout) →
        Notbremse terminate()+wait(), damit das QThread-Objekt nie
        zerstört wird, solange der OS-Thread noch läuft.
        """
        if thread is None or not thread.isRunning():
            return
        thread.quit()
        if not thread.wait(_THREAD_SHUTDOWN_MS):
            logger.warning(
                "Thread '%s' reagierte nicht – wird hart beendet", name)
            thread.terminate()
            thread.wait()

    def closeEvent(self, event) -> None:
        """Stoppt alle Hintergrund-Threads, bevor das Fenster (und damit
        die QThread-C++-Objekte) zerstört wird – sonst stürzt Python
        beim Schliessen ab, solange z. B. der KI-Warmup noch läuft.
        """
        self._sb.showMessage("Beende…")
        self._shutdown_thread(self._ai_thread, "KI")
        self._shutdown_thread(self._load_thread, "Bildladen")
        self._shutdown_thread(self._warmup_thread, "rembg-Warmup")
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
        if self._load_thread is not None and self._load_thread.isRunning():
            self._sb.showMessage("Lädt bereits ein Bild…")
            return
        self._sb.showMessage(f"⏳ Lädt: {Path(path).name}…")
        worker = ImageLoadWorker(path)
        worker.finished.connect(self._on_image_load_done)
        worker.error.connect(self._on_image_load_error)
        self._load_thread = self._launch_worker(
            worker,
            quit_on=(worker.finished, worker.error),
            on_finished=self._on_load_thread_finished,
        )

    def _on_image_load_done(self, img, path: str) -> None:
        self._canvas.apply_loaded_image(img, path)

    def _on_image_load_error(self, msg: str) -> None:
        self._sb.showMessage(f"Ladefehler: {msg}")

    def _on_load_thread_finished(self) -> None:
        self._load_thread = None

    # ── rembg-Warmup ────────────────────────────────────────────

    def _start_rembg_warmup(self) -> None:
        """Lädt das rembg-Modell im Hintergrund, damit der erste KI-Klick
        nicht spürbar wartet."""
        self._sb.showMessage("🤖 KI-Modell wird geladen…")
        worker = RembgWarmupWorker()
        self._warmup_thread = self._launch_worker(
            worker,
            quit_on=(worker.finished,),
            on_finished=self._on_warmup_done,
        )

    def _on_warmup_done(self) -> None:
        self._warmup_done = True
        self._warmup_thread = None
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
        if self._ai_thread is not None and self._ai_thread.isRunning():
            self._sb.showMessage("KI läuft bereits…")
            return
        self._sb.showMessage("🤖 KI verarbeitet Bild… (kann einige Sekunden dauern)")
        self._btn_ai.setEnabled(False)

        # Canvas-Version merken: falls der Nutzer inzwischen ein anderes
        # Bild lädt, wird das verspätete KI-Ergebnis in _on_ai_done verworfen.
        self._ai_input_version = self._canvas.version

        img = self._canvas.image
        assert img is not None  # has_image-Check oben garantiert das
        worker = AIWorker(img.copy())
        worker.finished.connect(self._on_ai_done)
        worker.error.connect(self._on_ai_error)
        self._ai_thread = self._launch_worker(
            worker,
            quit_on=(worker.finished, worker.error),
            on_finished=self._on_ai_thread_finished,
        )
        self._ai_worker = worker

    def _on_ai_thread_finished(self) -> None:
        self._btn_ai.setEnabled(True)
        self._ai_thread = None
        self._ai_worker = None
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
