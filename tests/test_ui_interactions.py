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
- ``QFileDialog`` wird in den jeweiligen Submodulen (``bgremover.main_window`` /
  ``bgremover.settings_dialog``) gepatcht, ``SettingsDialog.exec`` an der Klasse
  ``bgremover.SettingsDialog`` (die Module nutzen ``from PyQt6.QtWidgets import
  QFileDialog``; ein Patch auf die PyQt-Klasse selbst greift nicht).
- Canvas wird synchron via ``apply_loaded_image`` befuellt statt ueber den
  Async-Worker-Thread.
- Assertions pruefen den Modellzustand (``_mask``/``image``/``_crop_overlay``),
  nicht View-Pixel.
"""
import numpy as np
import pytest
from PIL import Image
from PyQt6.QtCore import QEvent, QPointF, QSettings, Qt
from PyQt6.QtGui import QAction, QKeySequence, QMouseEvent
from PyQt6.QtWidgets import QLabel, QToolButton

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
from bgremover.i18n import tr
from bgremover.preview_mode import PreviewMode
from bgremover.project_model import LayerKind, LayerRole, Project

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
    """Ersetzt ``QFileDialog`` in den Submodulen in Tests (keine nativen Dialoge)."""
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
    for btn in (w.toolbar.btn_move, w.toolbar.btn_wand, w.toolbar.btn_brush,
                w.toolbar.btn_eraser, w.toolbar.btn_lasso,
                w.toolbar.btn_height_lighten, w.toolbar.btn_height_darken,
                w.toolbar.btn_undo, w.toolbar.btn_redo, w.toolbar.btn_theme):
        assert isinstance(btn, QToolButton)


def test_imagecanvas_builds(qtbot):
    c = ImageCanvas()
    qtbot.addWidget(c)
    assert c.has_image is False
    assert c.current_tool == TOOL_WAND


# ── Zeichentools ─────────────────────────────────────────────────────────

@pytest.mark.ui_smoke
def test_toolbar_selects_tools(main_window, qtbot):
    w = main_window
    c = w._canvas
    # Auswahlwerkzeuge sind kontextuell nur im Schritt „Freistellen" sichtbar
    # (kontextuelle Werkzeugleiste #422) – dorthin wechseln, dann klicken.
    from bgremover.stepper import WorkflowStep
    w._go_to_step(WorkflowStep.CUTOUT)
    qtbot.mouseClick(w.toolbar.btn_brush, Qt.MouseButton.LeftButton)
    assert c.current_tool == TOOL_BRUSH
    qtbot.mouseClick(w.toolbar.btn_eraser, Qt.MouseButton.LeftButton)
    assert c.current_tool == TOOL_ERASER
    qtbot.mouseClick(w.toolbar.btn_lasso, Qt.MouseButton.LeftButton)
    assert c.current_tool == TOOL_LASSO
    qtbot.mouseClick(w.toolbar.btn_wand, Qt.MouseButton.LeftButton)
    assert c.current_tool == TOOL_WAND


def test_brush_paints_and_eraser_clears(loaded_window):
    c = loaded_window._canvas
    c.set_tool(TOOL_BRUSH)
    c._mask = np.zeros((30, 40), dtype=bool)
    c._paint_brush(20, 15, additive=True)
    assert c._mask.any()
    assert c._mask[15, 20]
    c.set_tool(TOOL_ERASER)
    c._paint_brush(20, 15, additive=False)
    assert not c._mask[15, 20]


def test_magic_wand_selects_region(loaded_window, qtbot):
    c = loaded_window._canvas
    c.set_tool(TOOL_WAND)
    c._mask = np.zeros((30, 40), dtype=bool)
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
        "Farbe", "Relief über Farbe", "Höhe (Graustufe)", "Gloss", "Kombiniert",
    }
    assert expected <= texts


@pytest.mark.ui_smoke
def test_preview_menu_and_panel_drive_live_canvas_without_dirtying(main_window):
    w = main_window
    project = Project(4, 4)
    project.create_layer(
        Image.new("RGBA", (4, 4), (100, 80, 60, 200)),
        name="Motiv",
        kind=LayerKind.COLOR,
    )
    height = np.zeros((4, 4, 4), dtype=np.uint8)
    height[:, :, 0] = np.array([0, 85, 170, 255], dtype=np.uint8)
    height[:, :, 3] = 255
    project.create_layer(
        Image.fromarray(height, "RGBA"),
        name="Height",
        kind=LayerKind.HEIGHT,
        role=LayerRole.HEIGHT_MAP,
    )
    gloss = np.zeros((4, 4, 4), dtype=np.uint8)
    gloss[:, 2:, :3] = 255
    gloss[:, :, 3] = 255
    project.create_layer(
        Image.fromarray(gloss, "RGBA"),
        name="Gloss",
        kind=LayerKind.GLOSS,
        role=LayerRole.GLOSS_MASK,
    )
    w._canvas.set_project(project)
    revision = w._canvas.content_revision

    # Ansicht-Menü → Canvas + Panel synchron.
    _action(w, "Relief über Farbe").trigger()
    assert w._canvas.preview_mode is PreviewMode.RELIEF
    assert w._preview_mode_segments.current_mode() is PreviewMode.RELIEF
    assert not np.array_equal(
        np.array(w._canvas._render_image()), np.array(project.composite_color())
    )

    # Regler wirkt live; Stärke 0 ist Farb-No-op.
    w._preview_relief_slider.setValue(0)
    assert w._canvas.relief_strength == 0
    assert np.array_equal(
        np.array(w._canvas._render_image()), np.array(project.composite_color())
    )

    # Ansicht-Menü → Canvas + Panel synchron; Gloss-Toggle wirkt live. Der
    # kombinierte Modus ist bewusst nur über das Menü erreichbar (Segmented
    # zeigt Farbe/Relief/Höhe/Gloss).
    _action(w, "Kombiniert").trigger()
    with_gloss = np.array(w._canvas._render_image())
    assert _action(w, "Kombiniert").isChecked()
    w._preview_gloss_visible.setChecked(False)
    without_gloss = np.array(w._canvas._render_image())
    assert not np.array_equal(with_gloss, without_gloss)
    assert w._canvas.content_revision == revision

    w._canvas.set_relief_strength(25)
    assert w._preview_relief_slider.value() == 25
    assert "25 %" in w._preview_relief_label.text()

    # Auch während einer bestehenden Farb-Live-Vorschau rendert der Menüwechsel
    # sofort neu, statt das alte transiente Bild darüber liegen zu lassen (#397).
    color = project.layers[0]
    w._canvas.set_active_layer(color.id)
    color_before = np.array(color.image).copy()
    w._canvas.preview_color_op(
        lambda image: Image.new("RGBA", image.size, (180, 120, 90, 200))
    )
    transient_combined = np.array(w._canvas._preview)
    _action(w, "Höhe (Graustufe)").trigger()
    transient_height = np.array(w._canvas._preview)
    assert not np.array_equal(transient_height, transient_combined)
    assert w._canvas.preview_mode is PreviewMode.HEIGHT
    assert w._canvas._preview_layer_override is not None
    assert np.array_equal(np.array(color.image), color_before)
    w._canvas.cancel_color_preview()

    hints = [label.text() for label in w.findChildren(QLabel)]
    assert any("Nur Anzeige" in text and "Bild speichern" in text for text in hints)


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
    c._mask = np.ones((30, 40), dtype=bool)
    _action(w, "Auswahl invertieren").trigger()
    assert not c._mask.any()
    mask = np.zeros((30, 40), dtype=bool)
    mask[5, 5] = True
    c._mask = mask
    _action(w, "Auswahl aufheben").trigger()
    assert not c._mask.any()


@pytest.mark.ui_smoke
def test_escape_prioritizes_crop_then_lasso_then_selection(loaded_window):
    """Regression #248: der echte Window-Shortcut darf nicht sofort die
    Auswahl löschen, solange eine höher priorisierte Interaktion aktiv ist.
    """
    w = loaded_window
    c = w._canvas
    mask = np.zeros((30, 40), dtype=bool)
    mask[5, 5] = True
    c._mask = mask
    c._refresh_overlay()
    c.set_tool(TOOL_LASSO)
    c._lasso.add_point(3, 3)
    c._lasso.update_preview_line(10, 10)
    c.start_crop_ratio(1, 1)
    assert w._escape_action.shortcut() == QKeySequence("Escape")
    assert (
        w._escape_action.shortcutContext()
        == Qt.ShortcutContext.WindowShortcut
    )

    w._escape_action.trigger()
    assert c._crop.active is False
    assert c._lasso.points == [(3, 3)]
    assert c._lasso._path_item is not None
    assert c._lasso._line_item is not None
    assert c._mask.any()
    assert w.statusBar().currentMessage() == tr("canvas.crop_cancelled")

    w._escape_action.trigger()
    assert c._lasso.points == []
    assert c._lasso._path_item is None
    assert c._lasso._line_item is None
    assert c._mask.any()
    assert w.statusBar().currentMessage() == tr("canvas.lasso_cancelled")

    w._escape_action.trigger()
    assert not c._mask.any()
    assert w.statusBar().currentMessage() == tr("canvas.selection_cleared")


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
    """Seit #458 gibt es keinen Rail-Öffnen-Button mehr; der Schritt-1-
    Primärbutton des Inspectors bleibt der klickbare Öffnen-Einstieg."""
    w = main_window
    import bgremover.main_window as _mw
    monkeypatch.setattr(_mw, "QFileDialog", _FakeFileDialog)

    btn = w._right_panel.open_button
    assert btn is not None, "Öffnen-Primärbutton nicht gefunden"

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
