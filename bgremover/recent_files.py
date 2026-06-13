"""Persistenz-Helfer für die „Zuletzt geöffnet"-Liste.

Das UI-Menü liegt weiterhin in ``MainWindow``; dieses Modul besitzt die
Listensemantik: QSettings-I/O, Pfad-Kanonisierung, Deduplizierung,
Begrenzung der Einträge und Entfernung fehlender Dateien.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import QObject, QSettings
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu

from bgremover.constants import logger

RECENT_MAX = 10
SETTINGS_RECENT_KEY = "recent_files"


class RecentFiles:
    """Kleine Wrapper-Klasse um die persistierte Liste zuletzt geöffneter Dateien."""

    def __init__(
        self,
        settings: QSettings,
        key: str = SETTINGS_RECENT_KEY,
        limit: int = RECENT_MAX,
    ) -> None:
        self._settings = settings
        self._key = key
        self._limit = limit

    @property
    def limit(self) -> int:
        return self._limit

    @property
    def key(self) -> str:
        return self._key

    def paths(self) -> list[str]:
        """Liefert die bereinigte Liste gültiger Pfade.

        Defensiv gegen beschädigte, alte oder fremde QSettings-Werte
        (Befund #233) – das Settings-Schema verfolgt ausdrücklich das Ziel,
        unerwartete gespeicherte Werte nicht zum Absturz führen zu lassen:

        - Ein einzelner String wird als Ein-Element-Liste behandelt. QSettings
          serialisiert eine Liste mit genau einem Eintrag als rohen String
          zurück; sonst zerlegte ``list(raw)`` den Pfad zeichenweise.
        - Listen/Tupel werden elementweise gefiltert – nur nicht-leere Strings
          bleiben übrig, Nicht-String- und Leer-Einträge werden ignoriert.
        - Jeder andere Typ (z. B. Ganzzahl, ``None``) ergibt eine leere Liste
          statt eines ``TypeError`` aus ``list(raw)``, der sonst den
          Menü-/Anwendungsaufbau abbrechen könnte.
        """
        raw = self._settings.value(self._key, [])
        if isinstance(raw, str):
            candidates: list[object] = [raw]
        elif isinstance(raw, (list, tuple)):
            candidates = list(raw)
        else:
            candidates = []
        return [value for value in candidates if isinstance(value, str) and value]

    def sanitize(self) -> list[str]:
        """Bereinigt den persistierten Wert und schreibt ihn bei Bedarf zurück.

        Optionaler Aufruf (z. B. beim Start): hebt einen beschädigten oder
        veralteten gespeicherten Wert dauerhaft auf eine gültige Liste, sodass
        nachfolgende Lesezugriffe mit sauberem Zustand starten. Geschrieben
        (und einmalig als Warnung geloggt) wird nur, wenn der Rohwert wirklich
        bereinigt werden musste – der harmlose QSettings-Ein-Element-String und
        eine bereits saubere Liste lösen weder Schreibzugriff noch Warnung aus.
        """
        cleaned = self.paths()
        raw = self._settings.value(self._key, [])
        if not (raw == cleaned or (isinstance(raw, str) and cleaned == [raw])):
            logger.warning(
                "QSettings: ungültige %r-Einträge bereinigt (%r -> %r).",
                self._key, raw, cleaned,
            )
            self._settings.setValue(self._key, cleaned)
        return cleaned

    def add(self, path: str) -> list[str]:
        canonical = str(Path(path).resolve())
        items = [p for p in self.paths() if p != canonical]
        items.insert(0, canonical)
        items = items[:self._limit]
        self._settings.setValue(self._key, items)
        return items

    def remove(self, path: str) -> list[str]:
        items = [p for p in self.paths() if p != path]
        self._settings.setValue(self._key, items)
        return items

    def clear(self) -> None:
        self._settings.setValue(self._key, [])


class RecentFilesMenu:
    """Qt-Menü-Adapter für ``RecentFiles``."""

    def __init__(
        self,
        parent: QObject,
        menu: QMenu,
        recent_files: RecentFiles,
        open_path: Callable[[str], None],
        missing_path: Callable[[str], None] | None = None,
    ) -> None:
        self._parent = parent
        self._menu = menu
        self._recent_files = recent_files
        self._open_path = open_path
        self._missing_path = missing_path
        self.rebuild()

    def paths(self) -> list[str]:
        return self._recent_files.paths()

    def add(self, path: str) -> None:
        self._recent_files.add(path)
        self.rebuild()

    def rebuild(self) -> None:
        self._menu.clear()
        # Inzwischen geloeschte Dateien stumm aussortieren, bevor sie sichtbar
        # werden. Der missing_path-Callback bleibt aktiven Klicks vorbehalten;
        # der Rebuild soll keine Warnungen produzieren, sondern lediglich den
        # persistierten Zustand mit dem Dateisystem abgleichen.
        items = self._recent_files.paths()
        existing = [p for p in items if Path(p).exists()]
        if existing != items:
            for stale in items:
                if stale not in existing:
                    self._recent_files.remove(stale)
        if not existing:
            empty = QAction("(keine)", self._parent)
            empty.setEnabled(False)
            self._menu.addAction(empty)
            return
        for path in existing:
            act = QAction(Path(path).name, self._parent)
            act.setToolTip(path)
            act.triggered.connect(lambda _=False, pp=path: self.open(pp))
            self._menu.addAction(act)

    def open(self, path: str) -> None:
        if not Path(path).exists():
            self._recent_files.remove(path)
            if self._missing_path is not None:
                self._missing_path(path)
            self.rebuild()
            return
        self._open_path(path)
