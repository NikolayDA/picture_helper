"""Dedizierte Unit-Tests für ``MainWindow``-Slots und -Hilfslogik.

Ergänzt die verstreuten ``MainWindow``-Checks in ``test_workers.py`` /
``test_worker_controller.py`` um die bislang ungetesteten Menü-/Toolbar-
Slots: Öffnen, Speichern (Quick-Save + „Speichern unter…"), KI-Start,
Farbwahl, die „Ungespeicherte Änderungen"-Nachfrage und der Einstellungs-
Dialog. Alle Tests laufen headless ohne qtbot – die modalen Dialoge werden
gezielt gepatcht, statt eine echte Event-Loop zu starten.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QColorDialog, QFileDialog, QMessageBox

from bgremover import MainWindow
from bgremover import main_window as mw
from bgremover.constants import TOOL_BRUSH, TOOL_WAND
from bgremover.status_messages import StatusMessages as SM

# Die echte ``_confirm_discard_changes`` zum Importzeitpunkt sichern: die
# autouse-Fixture ``_auto_confirm_discard`` (conftest) ersetzt sie pro Test
# klassenweit durch ``-> True``. Für die gezielten Verwerfen-Tests wird die
# Originalmethode hier festgehalten und je Instanz wieder eingebunden.
_REAL_CONFIRM_DISCARD = MainWindow._confirm_discard_changes


@pytest.fixture
def win(qapp):
    w = MainWindow()
    try:
        yield w
    finally:
        w.close()


def _load_dummy_image(win, tmp_path, color=(10, 20, 30, 255)):
    """Lädt ein winziges Bild in den Canvas (markiert es als gespeichert)."""
    img = Image.new("RGBA", (4, 4), color)
    win._canvas.apply_loaded_image(img, str(tmp_path / "src.png"))
    return img


class _RunningThread:
    """Stand-in für einen laufenden QThread (nur ``isRunning``)."""

    @staticmethod
    def isRunning() -> bool:
        return True


# ── _set_tool ────────────────────────────────────────────────

def test_set_tool_checks_matching_toolbar_button(win):
    win._set_tool(TOOL_BRUSH)
    assert win._toolbar.btn_brush.isChecked()
    win._set_tool(TOOL_WAND)
    assert win._toolbar.btn_wand.isChecked()


def test_set_tool_ignores_unknown_tool(win, monkeypatch):
    """Unbekanntes Tool wird an den Canvas gereicht, selektiert aber keinen
    Button (deckt den ``tool not in buttons``-Zweig)."""
    recorded: dict = {}
    monkeypatch.setattr(win._canvas, "set_tool",
                        lambda t: recorded.__setitem__("tool", t))
    win._set_tool("does-not-exist")
    assert recorded["tool"] == "does-not-exist"


# ── _confirm_discard_changes ─────────────────────────────────

def test_confirm_discard_true_without_unsaved_changes(win, monkeypatch):
    monkeypatch.setattr(win, "_confirm_discard_changes",
                        _REAL_CONFIRM_DISCARD.__get__(win))
    # Kein Bild → nichts zu verlieren → keine Nachfrage.
    assert win._confirm_discard_changes() is True


def test_confirm_discard_cancel_aborts(win, monkeypatch):
    monkeypatch.setattr(win, "_confirm_discard_changes",
                        _REAL_CONFIRM_DISCARD.__get__(win))
    monkeypatch.setattr(win, "_has_unsaved_changes", lambda: True)
    monkeypatch.setattr(QMessageBox, "warning",
                        lambda *a, **k: QMessageBox.StandardButton.Cancel)
    assert win._confirm_discard_changes() is False


def test_confirm_discard_discard_proceeds(win, monkeypatch):
    monkeypatch.setattr(win, "_confirm_discard_changes",
                        _REAL_CONFIRM_DISCARD.__get__(win))
    monkeypatch.setattr(win, "_has_unsaved_changes", lambda: True)
    monkeypatch.setattr(QMessageBox, "warning",
                        lambda *a, **k: QMessageBox.StandardButton.Discard)
    assert win._confirm_discard_changes() is True


def test_confirm_discard_save_proceeds_when_saved(win, monkeypatch):
    monkeypatch.setattr(win, "_confirm_discard_changes",
                        _REAL_CONFIRM_DISCARD.__get__(win))
    # Erst „dirty", nach erfolgreichem Speichern „clean".
    state = {"dirty": True}
    monkeypatch.setattr(win, "_has_unsaved_changes", lambda: state["dirty"])
    monkeypatch.setattr(win, "_save",
                        lambda: state.__setitem__("dirty", False))
    monkeypatch.setattr(QMessageBox, "warning",
                        lambda *a, **k: QMessageBox.StandardButton.Save)
    assert win._confirm_discard_changes() is True


def test_confirm_discard_save_aborts_when_still_dirty(win, monkeypatch):
    monkeypatch.setattr(win, "_confirm_discard_changes",
                        _REAL_CONFIRM_DISCARD.__get__(win))
    # Speichern bricht ab (kein Pfad gewählt) → bleibt dirty → Aktion stoppt.
    monkeypatch.setattr(win, "_has_unsaved_changes", lambda: True)
    monkeypatch.setattr(win, "_save", lambda: None)
    monkeypatch.setattr(QMessageBox, "warning",
                        lambda *a, **k: QMessageBox.StandardButton.Save)
    assert win._confirm_discard_changes() is False


# ── _open_image ──────────────────────────────────────────────

def test_open_image_loads_selected_path(win, monkeypatch):
    monkeypatch.setattr(QFileDialog, "getOpenFileName",
                        lambda *a, **k: ("/some/pic.png", "filter"))
    loaded: dict = {}
    monkeypatch.setattr(win, "_load_image_async",
                        lambda p: loaded.__setitem__("path", p))
    win._open_image()
    assert loaded["path"] == "/some/pic.png"


def test_open_image_noop_on_cancel(win, monkeypatch):
    monkeypatch.setattr(QFileDialog, "getOpenFileName",
                        lambda *a, **k: ("", ""))
    called: dict = {}
    monkeypatch.setattr(win, "_load_image_async",
                        lambda p: called.__setitem__("path", p))
    win._open_image()
    assert "path" not in called


# ── _load_image_async (Gate) ─────────────────────────────────

def test_load_image_async_rejects_while_loading(win, monkeypatch):
    win._worker_controller.load_thread = _RunningThread()
    started: dict = {}

    def _fake_start(*a, **k):
        started["called"] = True
        return True

    monkeypatch.setattr(win._worker_controller, "start_image_load", _fake_start)
    try:
        win._load_image_async("/x.png")
        assert win.statusBar().currentMessage() == SM.LAEDT_BEREITS
        assert "called" not in started
    finally:
        win._worker_controller.load_thread = None


# ── _start_flood_fill_async ──────────────────────────────────

def test_start_flood_fill_async_passes_through_when_started(win, monkeypatch):
    monkeypatch.setattr(win._worker_controller, "start_flood_fill",
                        lambda *a, **k: True)
    cancelled: dict = {}
    monkeypatch.setattr(win._canvas, "cancel_pending_wand",
                        lambda msg: cancelled.__setitem__("msg", msg))
    win._start_flood_fill_async(object(), 1, 2, 3)
    assert "msg" not in cancelled


def test_start_flood_fill_async_resets_canvas_when_rejected(win, monkeypatch):
    monkeypatch.setattr(win._worker_controller, "start_flood_fill",
                        lambda *a, **k: False)
    cancelled: dict = {}
    monkeypatch.setattr(win._canvas, "cancel_pending_wand",
                        lambda msg: cancelled.__setitem__("msg", msg))
    win._start_flood_fill_async(object(), 1, 2, 3)
    assert "msg" in cancelled


# ── _save / _save_as ─────────────────────────────────────────

def test_save_without_path_delegates_to_save_as(win, monkeypatch):
    win._save_path = None
    called: dict = {}
    monkeypatch.setattr(win, "_save_as",
                        lambda: called.__setitem__("save_as", True))
    win._save()
    assert called.get("save_as") is True


def test_save_without_image_reports_status(win):
    win._save_path = "/tmp/out.png"
    win._save()
    assert win.statusBar().currentMessage() == SM.KEIN_BILD_ZUM_SPEICHERN


def test_save_writes_to_known_path_and_marks_saved(win, tmp_path, monkeypatch):
    _load_dummy_image(win, tmp_path)
    target = str(tmp_path / "out.png")
    win._save_path = target
    saved: dict = {}

    def _save_ok(path):
        saved["path"] = path
        return True

    monkeypatch.setattr(win._canvas, "save_image", _save_ok)
    marked: dict = {}
    monkeypatch.setattr(win, "_mark_saved",
                        lambda: marked.__setitem__("marked", True))
    win._save()
    assert saved["path"] == target
    assert marked.get("marked") is True


def test_save_does_not_mark_when_write_fails(win, tmp_path, monkeypatch):
    _load_dummy_image(win, tmp_path)
    win._save_path = str(tmp_path / "out.png")
    monkeypatch.setattr(win._canvas, "save_image", lambda p: False)
    marked: dict = {}
    monkeypatch.setattr(win, "_mark_saved",
                        lambda: marked.__setitem__("marked", True))
    win._save()
    assert "marked" not in marked


def test_save_as_without_image_reports_status(win):
    win._save_as()
    assert win.statusBar().currentMessage() == SM.KEIN_BILD_ZUM_SPEICHERN


def test_save_as_cancelled_dialog_does_not_save(win, tmp_path, monkeypatch):
    _load_dummy_image(win, tmp_path)
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        lambda *a, **k: ("", ""))
    saved: dict = {}

    def _save_ok(path):
        saved["path"] = path
        return True

    monkeypatch.setattr(win._canvas, "save_image", _save_ok)
    win._save_as()
    assert "path" not in saved
    assert win._save_path is None


def test_save_as_writes_and_remembers_path(win, tmp_path, monkeypatch):
    _load_dummy_image(win, tmp_path)
    target = str(tmp_path / "export.png")
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        lambda *a, **k: (target, "PNG (*.png)"))
    saved: dict = {}

    def _save_ok(path):
        saved["path"] = path
        return True

    monkeypatch.setattr(win._canvas, "save_image", _save_ok)
    win._save_as()
    assert saved["path"].endswith(".png")
    # Pfad wird nur bei erfolgreichem Schreiben als Quick-Save-Ziel gemerkt.
    assert win._save_path == saved["path"]


def test_save_as_suggests_known_save_path(win, tmp_path, monkeypatch):
    """Steht bereits ein Quick-Save-Pfad fest, dient er als Vorschlag."""
    _load_dummy_image(win, tmp_path)
    win._save_path = str(tmp_path / "vorher.png")
    suggested: dict = {}

    def _capture(parent, title, suggest, filt):
        suggested["value"] = suggest
        return ("", "")

    monkeypatch.setattr(QFileDialog, "getSaveFileName", _capture)
    win._save_as()
    assert suggested["value"] == str(tmp_path / "vorher.png")


def test_save_as_suggests_save_dir_when_no_path(win, tmp_path, monkeypatch):
    """Ohne Quick-Save-Pfad, aber mit gemerktem Verzeichnis: dort vorschlagen."""
    _load_dummy_image(win, tmp_path)
    # ``_save_path`` ist nach dem Laden None; Verzeichnis über QSettings simulieren.
    monkeypatch.setattr(
        win._settings, "value",
        lambda key, default=None: str(tmp_path) if key == "save_dir" else default)
    suggested: dict = {}

    def _capture(parent, title, suggest, filt):
        suggested["value"] = suggest
        return ("", "")

    monkeypatch.setattr(QFileDialog, "getSaveFileName", _capture)
    win._save_as()
    assert suggested["value"] == str(tmp_path / "bild_bearbeitet")


def test_save_as_does_not_remember_path_when_write_fails(win, tmp_path, monkeypatch):
    """Schlägt das Schreiben fehl, wird der Pfad nicht als Ziel gemerkt."""
    _load_dummy_image(win, tmp_path)
    target = str(tmp_path / "export.png")
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        lambda *a, **k: (target, "PNG (*.png)"))
    monkeypatch.setattr(win._canvas, "save_image", lambda p: False)
    win._save_as()
    assert win._save_path is None


# ── Recent-Files ─────────────────────────────────────────────

def test_add_recent_uses_recent_files_when_menu_absent(win, monkeypatch):
    win._recent_menu = None
    added: dict = {}
    monkeypatch.setattr(win._recent_files, "add",
                        lambda p: added.__setitem__("path", p))
    win._add_recent("/a/b.png")
    assert added["path"] == "/a/b.png"


def test_on_recent_missing_reports_status(win):
    win._on_recent_missing("/gone/pic.png")
    assert win.statusBar().currentMessage() == SM.DATEI_NICHT_VORHANDEN("pic.png")


# ── _pick_color ──────────────────────────────────────────────

def test_pick_color_updates_background_when_valid(win, monkeypatch):
    monkeypatch.setattr(QColorDialog, "getColor",
                        lambda *a, **k: QColor(10, 20, 30))
    win._pick_color()
    assert win._bg_color == QColor(10, 20, 30)
    assert "#0a141e" in win._color_btn.styleSheet()


def test_pick_color_keeps_background_when_invalid(win, monkeypatch):
    before = QColor(win._bg_color)
    # Ein abgebrochener Dialog liefert eine ungültige Farbe.
    monkeypatch.setattr(QColorDialog, "getColor", lambda *a, **k: QColor())
    win._pick_color()
    assert win._bg_color == before


# ── _run_ai ──────────────────────────────────────────────────

def test_run_ai_reports_when_no_image(win):
    win._run_ai()
    assert win.statusBar().currentMessage() == SM.KEIN_BILD_GELADEN


def test_run_ai_reports_when_already_running(win, tmp_path):
    _load_dummy_image(win, tmp_path)
    win._worker_controller.ai_thread = _RunningThread()
    try:
        win._run_ai()
        assert win.statusBar().currentMessage() == SM.KI_LAEUFT_BEREITS
    finally:
        win._worker_controller.ai_thread = None


def test_run_ai_starts_worker_and_disables_button(win, tmp_path, monkeypatch):
    _load_dummy_image(win, tmp_path)
    started: dict = {}

    def _fake_start_ai(img, on_done, on_error, on_finished):
        started["img"] = img
        return True

    monkeypatch.setattr(win._worker_controller, "start_ai", _fake_start_ai)
    win._run_ai()
    assert win.statusBar().currentMessage() == SM.KI_VERARBEITET
    assert not win._toolbar.btn_ai.isEnabled()
    assert win._ai_input_version == win._canvas.version
    assert "img" in started


# ── KI-Abschluss / -Ergebnis / -Fehler ───────────────────────

def test_on_ai_thread_finished_reenables_button(win):
    win._toolbar.btn_ai.setEnabled(False)
    win._ai_input_version = 5
    win._sb.showMessage("irgendwas")
    win._on_ai_thread_finished()
    assert win._toolbar.btn_ai.isEnabled()
    assert win._ai_input_version == -1
    # Nur die Abbruch-Wartemeldung würde umgeschaltet – sonst bleibt sie stehen.
    assert win.statusBar().currentMessage() == "irgendwas"


def test_on_ai_done_applies_result_when_version_matches(win, tmp_path, monkeypatch):
    _load_dummy_image(win, tmp_path)
    win._ai_input_version = win._canvas.version
    applied: dict = {}
    monkeypatch.setattr(win._canvas, "apply_ai_result",
                        lambda img: applied.__setitem__("img", img))
    result = Image.new("RGBA", (4, 4), (1, 2, 3, 255))
    win._on_ai_done(result)
    assert applied["img"] is result


def test_on_ai_error_reports_status_and_shows_dialog(win, monkeypatch):
    shown: dict = {}
    monkeypatch.setattr(QMessageBox, "warning",
                        lambda *a, **k: shown.setdefault("warned", True))
    win._on_ai_error("boom")
    assert win.statusBar().currentMessage() == SM.KI_FEHLER("boom")
    assert shown.get("warned") is True


# ── _open_settings ───────────────────────────────────────────

def test_open_settings_opens_dialog(win, monkeypatch):
    opened: dict = {}

    class _FakeDialog:
        def __init__(self, settings, parent) -> None:
            opened["constructed"] = True

        def exec(self) -> None:
            opened["exec"] = True

    monkeypatch.setattr(mw, "SettingsDialog", _FakeDialog)
    win._open_settings()
    assert opened.get("constructed") is True
    assert opened.get("exec") is True


# ── closeEvent (Abbruch-Zweig) ───────────────────────────────

def test_close_event_cancelled_keeps_window_open(win, monkeypatch):
    monkeypatch.setattr(win, "_confirm_discard_changes", lambda: False)
    shut: dict = {}
    monkeypatch.setattr(win._worker_controller, "shutdown_all",
                        lambda: shut.__setitem__("called", True))

    class _Event:
        def __init__(self) -> None:
            self.ignored = False

        def ignore(self) -> None:
            self.ignored = True

        def accept(self) -> None:
            pass

    ev = _Event()
    win.closeEvent(ev)
    assert ev.ignored is True
    assert "called" not in shut


# ── __init__: rembg-Warmup-Zweig ─────────────────────────────

def test_init_starts_warmup_when_rembg_available(qapp, monkeypatch):
    """Ist rembg installiert, stößt ``__init__`` den Warmup an (Zeile 106)."""
    called: dict = {}
    monkeypatch.setattr(mw, "REMBG_AVAILABLE", True)
    monkeypatch.setattr(MainWindow, "_start_rembg_warmup",
                        lambda self: called.__setitem__("warmup", True))
    w = MainWindow()
    try:
        assert called.get("warmup") is True
    finally:
        w.close()


# ── Projekt-Menü (.bgrproj) (#334) ───────────────────────────

def test_new_project_creates_blank_active_layer(win):
    from bgremover.i18n import tr

    win._new_project()
    project = win._canvas.project
    assert project is not None
    assert len(project.layers) == 1
    assert project.active_layer() is project.layers[0]
    assert win._project_path is None
    assert win.statusBar().currentMessage() == tr("project.new")


def test_save_and_open_project_round_trip(win, tmp_path, monkeypatch):
    from bgremover.i18n import tr

    _load_dummy_image(win, tmp_path, color=(200, 10, 10, 255))
    win._canvas.add_layer()                              # zweite (transparente) Ebene
    assert len(win._canvas.project.layers) == 2

    target = str(tmp_path / "projekt")                   # ohne Endung → wird ergänzt
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        lambda *a, **k: (target, ""))
    win._save_project_as()
    assert win._project_path == target + ".bgrproj"
    assert win.statusBar().currentMessage() == tr(
        "project.saved", name="projekt.bgrproj")

    saved_path = target + ".bgrproj"

    # Dokument wechseln und Projekt zurückladen.
    win._new_project()
    assert len(win._canvas.project.layers) == 1

    monkeypatch.setattr(QFileDialog, "getOpenFileName",
                        lambda *a, **k: (saved_path, ""))
    win._open_project()

    project = win._canvas.project
    assert project is not None
    assert len(project.layers) == 2                      # verlustfrei zurückgeladen
    assert project.size == (4, 4)
    assert win._project_path == saved_path


def test_open_project_error_shows_translated_message(win, tmp_path, monkeypatch):
    from bgremover.i18n import tr

    broken = tmp_path / "broken.bgrproj"
    broken.write_bytes(b"not a zip")
    monkeypatch.setattr(QFileDialog, "getOpenFileName",
                        lambda *a, **k: (str(broken), ""))
    warned: dict = {}
    monkeypatch.setattr(
        QMessageBox, "warning",
        lambda *a, **k: warned.__setitem__("msg", a[2]) or QMessageBox.StandardButton.Ok)

    win._open_project()

    assert warned.get("msg") == tr("project.error.corrupt")
    assert win.statusBar().currentMessage() == tr("project.error.corrupt")


def test_save_project_without_project_reports_status(win):
    from bgremover.i18n import tr

    win._save_project_as()
    assert win.statusBar().currentMessage() == tr("project.no_project")


# ── #335: Recent Files (Bilder + Projekte), Verzeichnis, Export ──

def test_open_recent_path_dispatches_image_vs_project(win, monkeypatch):
    """„Zuletzt geöffnet" öffnet ein Projekt über den Projekt-Lader, ein Bild
    über den Bildladepfad – Unterscheidung an der Endung (#335)."""
    calls: list[tuple] = []
    monkeypatch.setattr(win, "_load_project_into_canvas",
                        lambda p: calls.append(("project", p)))
    monkeypatch.setattr(win, "_load_image_async",
                        lambda p: calls.append(("image", p)))

    win._open_recent_path("/x/foto.png")
    win._open_recent_path("/x/motiv.bgrproj")
    win._open_recent_path("/x/GROSS.BGRPROJ")     # Endung case-insensitiv

    assert calls == [
        ("image", "/x/foto.png"),
        ("project", "/x/motiv.bgrproj"),
        ("project", "/x/GROSS.BGRPROJ"),
    ]


def _isolated_window(tmp_path):
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                      str(tmp_path / "settings"))
    win = MainWindow()
    win._recent_files.clear()
    return win


def test_save_project_remembers_recent_and_directory(tmp_path, qapp, monkeypatch):
    win = _isolated_window(tmp_path)
    try:
        _load_dummy_image(win, tmp_path)
        target = str(tmp_path / "p")            # ohne Endung → wird ergänzt
        monkeypatch.setattr(QFileDialog, "getSaveFileName",
                            lambda *a, **k: (target, ""))
        win._save_project_as()

        saved = str(Path(target + ".bgrproj").resolve())
        assert saved in win._recent_files.paths()
        assert win._settings.value("project_dir") == str(Path(saved).parent)
    finally:
        win.close()


def test_open_project_from_recent_round_trips(tmp_path, qapp, monkeypatch):
    win = _isolated_window(tmp_path)
    try:
        _load_dummy_image(win, tmp_path, color=(7, 8, 9, 255))
        win._canvas.add_layer()
        saved = str(tmp_path / "doc.bgrproj")
        monkeypatch.setattr(QFileDialog, "getSaveFileName",
                            lambda *a, **k: (saved, ""))
        win._save_project_as()
        assert str(Path(saved).resolve()) in win._recent_files.paths()

        win._new_project()
        assert len(win._canvas.project.layers) == 1

        # Über „Zuletzt geöffnet" zurückladen (Dispatch an der Endung).
        win._open_recent_path(str(Path(saved).resolve()))
        assert len(win._canvas.project.layers) == 2
        assert win._project_path == str(Path(saved).resolve())
    finally:
        win.close()
