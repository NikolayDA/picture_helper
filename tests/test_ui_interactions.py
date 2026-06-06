"""qtbot-gesteuerte UI-Interaktionstests.

Die *volle* Suite laeuft NICHT in der PR-/Full-CI: ``pyproject.toml`` setzt
``addopts = "-q -m 'not ui or ui_smoke'"``, sodass ein einfaches ``pytest``
(wie es die CI ausfuehrt) die ``ui``-markierten Tests deselektiert – mit
Ausnahme des kleinen, zusaetzlich ``ui_smoke``-markierten Subsets, das als
Frueh-Smoke ueberall mitlaeuft. Die komplette Suite laeuft nightly via
``make ui`` (``pytest -m ui`` ueberschreibt das Default-Filter).

Headless-Strategie (Begruendung):
- Menue-Aktionen werden ueber ``QAction.trigger()`` ausgeloest, nie ueber
  Klicks auf die Menueleisten-Geometrie – damit immun gegen das native
  macOS-Menue.
- ``QFileDialog`` / ``SettingsDialog.exec`` werden auf dem ``BgRemover``-
  Modulobjekt gepatcht (die Datei nutzt ``from PyQt6.QtWidgets import
  QFileDialog``; ein Patch auf die PyQt-Klasse selbst greift nicht).
- Canvas wird synchron via ``apply_loaded_image`` befuellt statt ueber den
  Async-Worker-Thread.
- Assertions pruefen den Modellzustand (``_mask``/``image``/``_crop_overlay``),
  nicht View-Pixel.
"""
import pytest
from PIL import Image
from PyQt6.QtCore import QEvent, QPointF, QSettings, Qt
from PyQt6.QtGui import QAction, QMouseEvent
from PyQt6.QtWidgets import QToolButton

import bgremover
from bgremover import (
    TOOL_BRUSH,
    TOOL_ERASER,
    TOOL_LASSO,
    TOOL_WAND,
    CropOverlayItem,
    ImageCanvas,
    MainWindow,
    SettingsDialog,
)

# Alle Tests dieser Datei sind lokale UI-Tests (siehe Modul-Docstring).
pytestmark = pytest.mark.ui


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def isolated_settings(tmp_path):
    """Leitet QSettings in ein tmp-Verzeichnis um (1:1 wie test_recent_files).

    Pflicht: ohne das wuerden UI-Tests die echten macOS-Preferences mutieren.
    """
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat,
                      QSettings.Scope.UserScope, str(tmp_path))
    yield tmp_path


@pytest.fixture
def main_window(qtbot, isolated_settings, monkeypatch):
    # rembg-Warmup-Thread unterdruecken (nicht-deterministisch / langsam).
    monkeypatch.setattr(MainWindow, "_start_rembg_warmup", lambda self: None)
    w = MainWindow()
    qtbot.addWidget(w)
    return w


@pytest.fixture
def loaded_window(main_window, tmp_path):
    """MainWindow mit synchron geladenem, einfarbigem Testbild (40x30)."""
    img = Image.new("RGBA", (40, 30), (120, 30, 30, 255))
    path = tmp_path / "sample.png"
    img.save(path)
    main_window._canvas.apply_loaded_image(img, str(path))
    return main_window


class _FakeFileDialog:
    """Ersetzt ``bgremover.QFileDialog`` in Tests (keine nativen Dialoge)."""
    open_ret: tuple = ("", "")
    dir_ret: str = ""

    @staticmethod
    def getOpenFileName(*args, **kwargs):
        return _FakeFileDialog.open_ret

    @staticmethod
    def getExistingDirectory(*args, **kwargs):
        return _FakeFileDialog.dir_ret


def _canvas_image(c: ImageCanvas) -> Image.Image:
    img = c.image
    assert img is not None
    return img


def _action(window, text: str) -> QAction:
    for act in window.findChildren(QAction):
        if act.text() == text:
            return act
    raise AssertionError(f"QAction {text!r} nicht gefunden")


# ── Smoke ────────────────────────────────────────────────────────────────

@pytest.mark.ui_smoke
def test_mainwindow_builds(main_window):
    w = main_window
    assert isinstance(w._canvas, ImageCanvas)
    assert w.menuBar() is not None
    for attr in ("_btn_wand", "_btn_brush", "_btn_eraser",
                 "_btn_lasso", "_btn_ai", "_btn_history"):
        assert isinstance(getattr(w, attr), QToolButton)


def test_imagecanvas_builds(qtbot):
    c = ImageCanvas()
    qtbot.addWidget(c)
    assert c.has_image is False
    assert c._tool == TOOL_WAND


# ── Zeichentools ─────────────────────────────────────────────────────────

@pytest.mark.ui_smoke
def test_toolbar_selects_tools(main_window, qtbot):
    w = main_window
    c = w._canvas
    qtbot.mouseClick(w._btn_brush, Qt.MouseButton.LeftButton)
    assert c._tool == TOOL_BRUSH
    qtbot.mouseClick(w._btn_eraser, Qt.MouseButton.LeftButton)
    assert c._tool == TOOL_ERASER
    qtbot.mouseClick(w._btn_lasso, Qt.MouseButton.LeftButton)
    assert c._tool == TOOL_LASSO
    qtbot.mouseClick(w._btn_wand, Qt.MouseButton.LeftButton)
    assert c._tool == TOOL_WAND


def test_brush_paints_and_eraser_clears(loaded_window):
    c = loaded_window._canvas
    c.set_tool(TOOL_BRUSH)
    c._mask[:] = False
    c._paint_brush(20, 15, additive=True)
    assert c._mask.any()
    assert c._mask[15, 20]
    c.set_tool(TOOL_ERASER)
    c._paint_brush(20, 15, additive=False)
    assert not c._mask[15, 20]


def test_magic_wand_selects_region(loaded_window, qtbot):
    c = loaded_window._canvas
    c.set_tool(TOOL_WAND)
    c._mask[:] = False
    # Deterministisches View→Scene-Mapping: Widget-Groesse setzen + einpassen,
    # dann die Viewport-Position aus dem Scene-Punkt zurueckrechnen.
    c.resize(300, 300)
    c.fit_to_view()
    vp = c.mapFromScene(QPointF(20, 15))
    pos = QPointF(vp)
    ev = QMouseEvent(QEvent.Type.MouseButtonPress, pos, pos,
                     Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier)
    c.mousePressEvent(ev)
    # Flood-Fill laeuft im Worker; auf das Maskenupdate warten, bevor
    # die Auswahlflaeche geprueft wird. Einfarbiges Bild ⇒ alles selektiert.
    qtbot.waitUntil(lambda: c._mask.sum() > 0, timeout=3000)


# ── Menue / Toolbar ──────────────────────────────────────────────────────

def test_menu_actions_present(main_window):
    texts = {a.text() for a in main_window.findChildren(QAction)}
    expected = {
        "Öffnen…", "Speichern", "Speichern unter…",
        "Rückgängig", "Wiederherstellen",
        "90° links drehen", "90° rechts drehen", "180° drehen",
        "Horizontal spiegeln", "Vertikal spiegeln",
        "Auswahl aufheben", "Auswahl invertieren",
        "Original wiederherstellen", "Fit to View", "Einstellungen…",
    }
    assert expected <= texts


def test_undo_redo_actions(loaded_window):
    w = loaded_window
    c = w._canvas
    c.apply_rotate(90)  # 40x30 → 30x40, legt Undo-Schritt an
    assert (_canvas_image(c).width, _canvas_image(c).height) == (30, 40)
    _action(w, "Rückgängig").trigger()
    assert (_canvas_image(c).width, _canvas_image(c).height) == (40, 30)
    _action(w, "Wiederherstellen").trigger()
    assert (_canvas_image(c).width, _canvas_image(c).height) == (30, 40)


@pytest.mark.ui_smoke
def test_rotate_flip_actions(loaded_window):
    w = loaded_window
    c = w._canvas
    _action(w, "90° rechts drehen").trigger()
    assert (_canvas_image(c).width, _canvas_image(c).height) == (30, 40)
    _action(w, "Horizontal spiegeln").trigger()
    assert (_canvas_image(c).width, _canvas_image(c).height) == (30, 40)
    _action(w, "Rückgängig").trigger()
    assert (_canvas_image(c).width, _canvas_image(c).height) == (30, 40)
    _action(w, "Rückgängig").trigger()
    assert (_canvas_image(c).width, _canvas_image(c).height) == (40, 30)


def test_selection_actions(loaded_window):
    w = loaded_window
    c = w._canvas
    c._mask[:] = True
    _action(w, "Auswahl invertieren").trigger()
    assert not c._mask.any()
    c._mask[5, 5] = True
    _action(w, "Auswahl aufheben").trigger()
    assert not c._mask.any()


def test_fit_to_view_action(loaded_window, monkeypatch):
    calls: list[bool] = []
    monkeypatch.setattr(
        loaded_window._canvas._viewport,
        "fit_to_view",
        lambda: calls.append(True),
    )

    _action(loaded_window, "Fit to View").trigger()

    assert calls == [True]


def test_open_button_invokes_dialog(main_window, qtbot, monkeypatch, tmp_path):
    w = main_window
    import bgremover.main_window as _mw
    monkeypatch.setattr(_mw, "QFileDialog", _FakeFileDialog)

    btns = [b for b in w.findChildren(QToolButton)
            if b.toolTip().startswith("Bild öffnen")]
    assert btns, "Open-Mini-Button nicht gefunden"
    btn = btns[0]

    # Abbruch (leerer Pfad) ⇒ kein Lade-Thread.
    _FakeFileDialog.open_ret = ("", "")
    qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
    assert w._worker_controller.load_thread is None

    # Echter Pfad ⇒ _load_image_async wird mit genau diesem Pfad gerufen.
    png = tmp_path / "pic.png"
    Image.new("RGBA", (5, 5)).save(png)
    called: list[str] = []
    monkeypatch.setattr(w, "_load_image_async", called.append)
    _FakeFileDialog.open_ret = (str(png), "PNG (*.png)")
    qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
    assert called == [str(png)]


# ── Crop-Overlay ─────────────────────────────────────────────────────────

def test_crop_activate_and_confirm(loaded_window, qtbot):
    w = loaded_window
    c = w._canvas
    with qtbot.waitSignal(c.cropModeChanged, timeout=1000) as blocker:
        c.start_crop_ratio(1, 1)
    assert blocker.args == [True]
    assert isinstance(c._crop_overlay, CropOverlayItem)
    assert w._crop_bar.isVisibleTo(w)
    c.confirm_crop()
    assert c._crop_overlay is None
    assert not w._crop_bar.isVisibleTo(w)
    assert _canvas_image(c).width == _canvas_image(c).height  # 1:1 aus 40x30 → 30x30


def test_crop_cancel(loaded_window):
    w = loaded_window
    c = w._canvas
    c.start_crop_ratio(1, 1)
    assert c._crop_overlay is not None
    c.cancel_crop()
    assert c._crop_overlay is None
    assert not w._crop_bar.isVisibleTo(w)


# ── SettingsDialog ───────────────────────────────────────────────────────

def test_settings_dialog_load_save(main_window, qtbot, tmp_path):
    dlg = SettingsDialog(main_window._settings, main_window)
    qtbot.addWidget(dlg)
    assert dlg._fmt_combo.count() == len(SettingsDialog.FORMATS)
    assert dlg._log_path_edit.isReadOnly()
    dlg._open_dir_edit.setText(str(tmp_path))
    dlg._fmt_combo.setCurrentIndex(1)  # JPEG
    dlg._save_and_accept()
    assert main_window._settings.value("open_dir") == str(tmp_path)
    assert main_window._settings.value("preferred_format") == "JPEG"


def test_settings_opened_from_menu(main_window, monkeypatch):
    opened: list[SettingsDialog] = []

    def record_exec(dialog):
        opened.append(dialog)
        return 0

    monkeypatch.setattr(bgremover.SettingsDialog, "exec", record_exec)

    _action(main_window, "Einstellungen…").trigger()

    assert len(opened) == 1
    assert opened[0].parent() is main_window


def test_settings_pick_dirs(main_window, qtbot, monkeypatch, tmp_path):
    import bgremover.settings_dialog as _sd
    monkeypatch.setattr(_sd, "QFileDialog", _FakeFileDialog)
    _FakeFileDialog.dir_ret = str(tmp_path)
    dlg = SettingsDialog(main_window._settings, main_window)
    qtbot.addWidget(dlg)
    dlg._pick_open_dir()
    assert dlg._open_dir_edit.text() == str(tmp_path)
    dlg._pick_save_dir()
    assert dlg._save_dir_edit.text() == str(tmp_path)
