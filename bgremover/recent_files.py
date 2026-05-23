"""Persistence helper for the "recent files" list.

The UI menu still lives in ``MainWindow``; this module owns the list
semantics: QSettings I/O, path canonicalization, de-duplication, capping,
and removal of missing entries.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import QObject, QSettings
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu


RECENT_MAX = 10
SETTINGS_RECENT_KEY = "recent_files"


class RecentFiles:
    """Small wrapper around the persisted recent-file list."""

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
        raw = self._settings.value(self._key, [])
        if isinstance(raw, str):
            return [raw]
        return list(raw) if raw else []

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
    """Qt menu adapter for ``RecentFiles``."""

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
        items = self._recent_files.paths()
        if not items:
            empty = QAction("(keine)", self._parent)
            empty.setEnabled(False)
            self._menu.addAction(empty)
            return
        for path in items:
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
