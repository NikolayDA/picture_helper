"""Aufbau und Zustandsverwaltung des History-Popups für das Hauptfenster."""
from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from bgremover.i18n import tr


class HistoryPopup:
    def __init__(
        self,
        parent: QWidget,
        anchor: QWidget,
        on_jump: Callable[[int], None],
    ) -> None:
        self._parent = parent
        self._anchor = anchor
        self._on_jump = on_jump
        self._entries: list[str] = []
        self._popup: QDialog | None = None
        self._history_list: QListWidget | None = None

    def toggle(self) -> None:
        if self._popup is None:
            self._build()
        assert self._popup is not None
        if self._popup.isVisible():
            self._popup.hide()
            return

        gp = self._anchor.mapToGlobal(self._anchor.rect().topRight())
        self._popup.move(gp.x() + 4, gp.y())
        self._popup.show()
        self._popup.raise_()

    def update_entries(self, descriptions: list[str]) -> None:
        self._entries = list(descriptions)
        self._refresh_list()

    def _build(self) -> None:
        popup = QDialog(self._parent, Qt.WindowType.Tool)
        popup.setWindowTitle(tr("history.window_title"))
        popup.setMinimumWidth(270)
        popup.setStyleSheet("QDialog { background: #1a1a1a; }")

        lay = QVBoxLayout(popup)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        lbl = QLabel(tr("history.hint"))
        lbl.setStyleSheet("color: #666; font-size: 10px; background: transparent;")
        lay.addWidget(lbl)

        history_list = QListWidget()
        history_list.setStyleSheet("""
            QListWidget {
                background: #141414; color: #bbb; border: 1px solid #2a2a2a;
                border-radius: 6px; font-size: 11px;
            }
            QListWidget::item { padding: 6px 10px; border-bottom: 1px solid #1e1e1e; }
            QListWidget::item:selected { background: #1e3a5a; color: #7aacdd; }
            QListWidget::item:hover:!selected { background: #202020; }
        """)
        history_list.setMinimumHeight(200)
        history_list.setToolTip(tr("history.list.tooltip"))
        history_list.itemDoubleClicked.connect(self._jump_to_item)
        lay.addWidget(history_list)

        self._popup = popup
        self._history_list = history_list
        self._refresh_list()

    def _refresh_list(self) -> None:
        if self._history_list is None:
            return
        self._history_list.clear()
        for desc in self._entries:
            self._history_list.addItem(desc)

    def _jump_to_item(self, item: QListWidgetItem) -> None:
        assert self._history_list is not None
        row = self._history_list.row(item)
        self._on_jump(row + 1)
