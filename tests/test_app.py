"""Dedizierte Unit-Tests für den Anwendungs-Einstiegspunkt ``bgremover.app``.

Ergänzt die Subprozess-Smoke-Tests (``test_app_smoke.py``): die starten die
App in einem echten Kindprozess und zählen daher nicht zur Coverage. Hier
läuft ``main()`` in-process mit gefälschtem ``QApplication``/``MainWindow``.
So sind Verdrahtung (App-Name, Style, Palette, ``show()``) und Exit-Code
deterministisch prüfbar, ohne ein zweites echtes ``QApplication`` neben der
Test-Session anzulegen.
"""
from __future__ import annotations

import pytest

from bgremover import app as app_module


class _FakeSignal:
    """Minimaler Signal-Ersatz: merkt sich verbundene Slots."""

    def __init__(self) -> None:
        self.slots: list = []

    def connect(self, slot) -> None:
        self.slots.append(slot)


class _FakeApp:
    """Minimaler QApplication-Ersatz, der die Konfigurationsaufrufe mitschreibt."""

    # Von ``main()`` über ``arguments()[1:]`` gelesen; Default = keine
    # Startpfade. Einzelne Tests überschreiben das, um das Öffnen zu prüfen.
    arguments_result = ["bgremover"]

    def __init__(self, argv) -> None:
        self.argv = argv
        self.calls: dict = {}
        self.aboutToQuit = _FakeSignal()

    def arguments(self) -> list:
        return self.arguments_result

    def installEventFilter(self, obj) -> None:
        self.calls["event_filter"] = obj

    def setApplicationName(self, name) -> None:
        self.calls["app_name"] = name

    def setOrganizationName(self, name) -> None:
        self.calls["org_name"] = name

    def setDesktopFileName(self, name) -> None:
        self.calls["desktop"] = name

    def setStyle(self, style) -> None:
        self.calls["style"] = style

    def setPalette(self, palette) -> None:
        self.calls["palette"] = palette

    def setStyleSheet(self, sheet) -> None:
        self.calls["stylesheet"] = sheet

    def quit(self) -> None:
        self.calls["quit"] = True

    def exec(self) -> int:
        self.calls["exec"] = True
        return 0


class _FakeWindow:
    def __init__(self) -> None:
        self.shown = False
        self.open_paths_calls: list = []

    def show(self) -> None:
        self.shown = True

    def open_paths(self, paths) -> None:
        self.open_paths_calls.append(list(paths))

    def shutdown_workers(self) -> None:
        self.shutdown_workers_called = True


@pytest.fixture
def patched_app(monkeypatch):
    """Verdrahtet ``main()`` mit Fakes; gibt die erzeugten Objekte zurück.

    Bewusst KEINE ``qapp``-Fixture: ``main()`` würde sonst ein zweites echtes
    ``QApplication`` neben der Session-Instanz konstruieren (Qt bricht das mit
    einer Warnung/abort ab). Der Fake umgeht das vollständig.
    """
    created: dict = {}

    def make_app(argv):
        app = _FakeApp(argv)
        created["app"] = app
        return app

    def make_window():
        win = _FakeWindow()
        created["window"] = win
        return win

    monkeypatch.setattr(app_module, "QApplication", make_app)
    monkeypatch.setattr(app_module, "MainWindow", make_window)
    monkeypatch.setattr(app_module, "_setup_logging",
                        lambda: created.__setitem__("logging", True))
    monkeypatch.setattr(app_module, "init_runtime",
                        lambda: created.__setitem__("runtime", True))
    monkeypatch.delenv("BGREMOVER_SMOKE_TEST", raising=False)
    monkeypatch.delenv("BGREMOVER_AI_SELFCHECK", raising=False)
    return created


def test_main_configures_application(patched_app):
    """``main()`` setzt App-Identität, Style, Palette und zeigt das Fenster."""
    rc = app_module.main()
    app = patched_app["app"]

    assert rc == 0
    assert app.calls["app_name"] == "BgRemover"
    assert app.calls["org_name"] == "BgRemover"
    assert app.calls["desktop"] == "de.bgremover.app"
    assert app.calls["style"] == "Fusion"
    assert "palette" in app.calls
    assert patched_app["window"].shown is True
    # Reihenfolge-Verträge: Runtime-Init und Logging laufen beide an.
    assert patched_app["runtime"] is True
    assert patched_app["logging"] is True


def test_main_returns_exec_exit_code(patched_app, monkeypatch):
    """Der Rückgabewert von ``main()`` ist der Exit-Code von ``app.exec()``."""
    monkeypatch.setattr(_FakeApp, "exec", lambda self: 42)
    assert app_module.main() == 42


def test_main_without_smoke_hook_does_not_schedule_quit(patched_app):
    """Ohne ``BGREMOVER_SMOKE_TEST`` wird kein Selbst-Quit eingeplant."""
    app_module.main()
    assert "quit" not in patched_app["app"].calls


def test_main_smoke_hook_schedules_self_quit(patched_app, monkeypatch):
    """Mit ``BGREMOVER_SMOKE_TEST`` plant ``main()`` ``app.quit`` für den
    ersten Event-Loop-Tick ein – der Selbsttest-Hook für CI/Smoke."""
    scheduled: dict = {}

    class _FakeTimer:
        @staticmethod
        def singleShot(ms, callback) -> None:
            scheduled["ms"] = ms
            scheduled["callback"] = callback

    # Der Import ``from PyQt6.QtCore import QTimer`` im Hook löst erst beim
    # Aufruf auf – Patch am Quellmodul greift daher zur Laufzeit.
    monkeypatch.setattr("PyQt6.QtCore.QTimer", _FakeTimer)
    monkeypatch.setenv("BGREMOVER_SMOKE_TEST", "1")

    app_module.main()

    assert scheduled["ms"] == 0
    # Der eingeplante Callback ist ``app.quit``.
    scheduled["callback"]()
    assert patched_app["app"].calls.get("quit") is True


# ── #249: Startpfade & macOS-FileOpen-Verdrahtung ────────────────────────

@pytest.mark.parametrize("args, expected", [
    ([], []),                                        # normaler Start ohne Pfad
    (["/bilder/a.png"], ["/bilder/a.png"]),          # ein Pfad
    (["/a.png", "/b.png"], ["/a.png", "/b.png"]),    # mehrere, Reihenfolge bleibt
    (["", "/a.png", ""], ["/a.png"]),                # leere Einträge raus
    (["--debug", "/a.png"], ["/a.png"]),             # Rest-Optionen raus
])
def test_startup_image_paths_filters_args(args, expected) -> None:
    assert app_module._startup_image_paths(args) == expected


def test_main_installs_file_open_filter(patched_app) -> None:
    """``main()`` hängt einen ``_FileOpenFilter`` an die App (macOS-FileOpen)."""
    app_module.main()
    filt = patched_app["app"].calls.get("event_filter")
    assert isinstance(filt, app_module._FileOpenFilter)


def test_main_without_startup_path_does_not_open(patched_app) -> None:
    """Ohne Startpfad wird ``open_paths`` nicht eingeplant (Start unverändert)."""
    app_module.main()
    assert patched_app["window"].open_paths_calls == []


def test_main_schedules_startup_path_open(patched_app, monkeypatch, tmp_path) -> None:
    """Ein Startpfad wird per ``QTimer.singleShot(0, …)`` an
    ``MainWindow.open_paths`` weitergereicht – erst nach dem Fensteraufbau."""
    png = tmp_path / "shot.png"
    scheduled: dict = {}

    class _FakeTimer:
        @staticmethod
        def singleShot(ms, callback) -> None:
            scheduled["ms"] = ms
            scheduled["callback"] = callback

    monkeypatch.setattr("PyQt6.QtCore.QTimer", _FakeTimer)
    monkeypatch.setattr(_FakeApp, "arguments_result", ["bgremover", str(png)])

    app_module.main()

    assert scheduled["ms"] == 0
    # Noch nichts geöffnet – erst der Timer-Callback löst das Laden aus.
    assert patched_app["window"].open_paths_calls == []
    scheduled["callback"]()
    assert patched_app["window"].open_paths_calls == [[str(png)]]


def test_main_connects_about_to_quit_to_shutdown(patched_app) -> None:
    """``main()`` hängt das Worker-Shutdown an ``aboutToQuit`` – ein App-Quit
    (auch ohne Fensterschließen) beendet laufende Threads sauber (#249)."""
    app_module.main()
    slots = patched_app["app"].aboutToQuit.slots
    assert patched_app["window"].shutdown_workers in slots
