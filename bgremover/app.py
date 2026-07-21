"""Anwendungs-Einstiegspunkt.

Liefert ``int`` zurueck (Exit-Code), damit ``raise SystemExit(main())``
in ``__main__.py`` korrekt durchschlaegt.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import cast

from bgremover.qt_plugins import ensure_qt_plugin_path

ensure_qt_plugin_path()

from PyQt6.QtCore import QEvent, QObject, QSettings  # noqa: E402
from PyQt6.QtGui import QFileOpenEvent  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from bgremover.constants import init_runtime  # noqa: E402
from bgremover.logging_config import _setup_logging  # noqa: E402
from bgremover.main_window import MainWindow  # noqa: E402
from bgremover.settings_schema import THEME_KEY  # noqa: E402
from bgremover.theme import (  # noqa: E402
    build_app_stylesheet,
    build_qpalette,
    palette_for,
    set_active_palette,
)


def _startup_image_paths(args: list[str]) -> list[str]:
    """Bildpfad-Kandidaten aus den (Qt-bereinigten) Startargumenten.

    ``QApplication`` entfernt erkannte Qt-Optionen aus ``arguments()``; hier
    werden zusätzlich leere Einträge und verbleibende ``-``/``--``-Optionen
    herausgefiltert. Übrig bleiben die vom Aufrufer bzw. Betriebssystem
    übergebenen Pfade (Linux-Desktop ``%F``, ``bgremover bild.png``). Existenz
    und Format prüft später der validierte Ladepfad – Dateierweiterungen allein
    wird hier bewusst nicht vertraut (Befund #249).
    """
    return [a for a in args if a and not a.startswith("-")]


class _FileOpenFilter(QObject):
    """Leitet macOS-``QFileOpenEvent``s an das Hauptfenster weiter.

    Finder-Öffnungen (Doppelklick, „Öffnen mit", Dateizuordnung) erreichen die
    App auf macOS NICHT über ``argv``, sondern als ``QFileOpenEvent`` an die
    ``QApplication`` – sowohl beim Start als auch während die App bereits läuft.
    Ein anwendungsweiter Event-Filter fängt beide Fälle ab (Befund #249).
    """

    def __init__(self, window: MainWindow) -> None:
        # Bewusst ohne Qt-Parent: der Filter wird in ``main`` an die
        # QApplication gehängt und lebt damit, solange die App läuft.
        super().__init__()
        self._window = window

    def eventFilter(self, obj: QObject | None, event: QEvent | None) -> bool:
        if event is not None and event.type() == QEvent.Type.FileOpen:
            local = cast(QFileOpenEvent, event).file()
            if local:
                self._window.open_paths([local])
            else:
                # Nicht-lokale URL (z. B. Remote): ``file()`` ist leer.
                # Kontrolliert melden statt still ignorieren.
                self._window.report_unopenable_remote()
            return True
        return False


def main() -> int:
    # KI-Selbsttest-Hook (#308): ist BGREMOVER_AI_SELFCHECK gesetzt, prüft die
    # App headless, dass im (eingefrorenen) --ai-Bundle die komplette rembg-Kette
    # im Spawn-Kindprozess importierbar ist – inkl. der pymatting-*.dist-info-
    # Metadaten, deren Fehlen die KI im .dmg lahmlegte (#306). Rein Import +
    # Metadaten-Auflösung: kein Qt, kein Modell-Download. Beendet den Prozess mit
    # 0 (ok) bzw. 1 (Fehler), ohne die GUI hochzufahren.
    if os.environ.get("BGREMOVER_AI_SELFCHECK"):
        from bgremover.ai_process import run_ai_selfcheck
        ok, message = run_ai_selfcheck()
        print(message)
        return 0 if ok else 1

    init_runtime()
    app = QApplication(sys.argv)
    app.setApplicationName("BgRemover")
    app.setOrganizationName("BgRemover")
    # Verknüpft das Fenster unter Linux (X11/Wayland) mit der installierten
    # .desktop-Datei (packaging/linux) → korrektes Task-Leisten-Icon und
    # App-Zuordnung. Auf anderen Plattformen ein harmloser No-op.
    app.setDesktopFileName("de.bgremover.app")
    # Erst jetzt – QApplication + App-Name stehen – ist der Log-Pfad korrekt.
    _setup_logging()
    app.setStyle("Fusion")

    # Farbschema (hell/dunkel, #428) aus den QSettings anwenden, BEVOR das Fenster
    # gebaut wird – so lesen alle Widget-Builder die aktive Palette. Der Schlüssel
    # ist additiv und defaultet auf „dark"; die Umschaltung zur Laufzeit läuft über
    # MainWindow (Ansicht-Menü).
    settings = QSettings("BgRemover", "BgRemover")
    mode = str(settings.value(THEME_KEY, "dark"))
    palette = palette_for(mode)
    set_active_palette(palette)
    app.setPalette(build_qpalette(palette))
    app.setStyleSheet(build_app_stylesheet(palette))

    win = MainWindow()
    win.show()

    # macOS: Finder-Öffnungen kommen als QFileOpenEvent an die QApplication
    # (nicht über argv). Ein anwendungsweiter Event-Filter reicht sie an das
    # Fenster weiter – beim Start wie auch während die App schon läuft.
    file_open_filter = _FileOpenFilter(win)
    app.installEventFilter(file_open_filter)
    # Filter VOR dem Teardown wieder abhängen: ein beim QApplication-Abbau noch
    # installierter, von Python gehaltener Filter kann sonst beim Zustellen von
    # Teardown-Events auf ein bereits abgeräumtes Wrapper-Objekt treffen und den
    # Prozess crashen lassen (#249).
    app.aboutToQuit.connect(lambda: app.removeEventFilter(file_open_filter))

    # Beim App-Quit laufende Worker-Threads sauber beenden – greift AUCH bei
    # app.quit() ohne Fensterschließen (z. B. unmittelbar nach einem
    # Start-Open). Sonst kann ein noch laufender Lade-Thread beim C++-Teardown
    # zum Crash führen (Befund #249).
    app.aboutToQuit.connect(win.shutdown_workers)

    # Start-Bildpfade (CLI / Linux-Desktop %F) erst nach vollständigem
    # Fensteraufbau laden: QTimer.singleShot(0, …) verschiebt das Öffnen auf den
    # ersten Event-Loop-Durchlauf, sodass der validierte Ladepfad auf eine
    # fertige UI trifft (Befund #249).
    startup_paths = _startup_image_paths(app.arguments()[1:])
    if startup_paths:
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: win.open_paths(startup_paths))

    # Selbsttest-Hook für CI/Smoke-Tests: ist BGREMOVER_SMOKE_TEST
    # gesetzt, beendet die App sich nach dem ersten Event-Loop-Durchlauf
    # selbst (Exit-Code 0). Sie ist dann vollständig hochgefahren –
    # QApplication, Palette, MainWindow inkl. Toolbar/Panels/Canvas –,
    # ohne dass der Test einen Fensterprozess killen muss.
    if os.environ.get("BGREMOVER_SMOKE_TEST"):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, app.quit)

    # Nativer 3D-Screenshot-Automationshook (#648): ist BGREMOVER_SCREENSHOT_3D
    # gesetzt (Zielpfad der PNG), fährt die App den Automationsablauf (Beispielbild
    # → Höhenkarte → 3D-Vorschau → Framebuffer-Grab) und beendet sich mit dem
    # Ergebnis-Exit-Code. Bewusst NICHT offscreen – anders als BGREMOVER_SMOKE_TEST
    # lässt dieser Hook QT_QPA_PLATFORM unverändert, die GL-Provenance muss aus
    # diesem laufenden, gepackten Prozess stammen.
    screenshot_target = os.environ.get("BGREMOVER_SCREENSHOT_3D")
    if screenshot_target:
        from PyQt6.QtCore import QTimer

        from bgremover.screenshot3d import run_native_3d_screenshot

        def _run_screenshot_hook() -> None:
            result = run_native_3d_screenshot(win, Path(screenshot_target))
            print(result.message)
            app.exit(0 if result.ok else 1)

        QTimer.singleShot(0, _run_screenshot_hook)

    return app.exec()
