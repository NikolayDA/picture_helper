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
from bgremover.theme import active_palette


class _HistoryList(QListWidget):
    """Verlaufsliste mit explizitem Enter-Sprung (#441).

    Bewusst über ``keyPressEvent`` statt ``itemActivated``: Letzteres feuert
    plattformabhängig zusätzlich zum Doppelklick, und ``undo_to`` ist
    **relativ** (Schrittanzahl) – ein Doppel-Sprung wäre ein Bug.
    """

    def __init__(self, on_enter: Callable[[], None]) -> None:
        super().__init__()
        self._on_enter = on_enter

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt-Override)
        if event is not None and event.key() in (
            Qt.Key.Key_Return, Qt.Key.Key_Enter,
        ):
            self._on_enter()
            return
        super().keyPressEvent(event)


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
        self._hint: QLabel | None = None
        self._history_list: QListWidget | None = None

    def toggle(self) -> None:
        if self._popup is None:
            self._build()
        assert self._popup is not None
        if self._popup.isVisible():
            self._popup.hide()
            return

        # Vor jedem Öffnen neu stylen: das lazy gebaute Popup folgt so auch
        # einem zwischenzeitlichen Theme-Wechsel (#428/#441).
        self._apply_palette()
        gp = self._anchor.mapToGlobal(self._anchor.rect().topRight())
        self._popup.move(gp.x() + 4, gp.y())
        self._popup.show()
        self._popup.raise_()

    def update_entries(self, descriptions: list[str]) -> None:
        self._entries = list(descriptions)
        self._refresh_list()

    @property
    def is_open(self) -> bool:
        """Sichtbarkeitsvertrag für Aufrufer/Tests, ohne das lazy gebaute
        ``QDialog`` selbst offenzulegen."""
        return self._popup is not None and self._popup.isVisible()

    def item_texts(self) -> list[str]:
        """Tatsächlich gerenderter Listeninhalt (öffentlicher Test-/Inspektionspfad)."""
        if self._history_list is None:
            return []
        texts = []
        for i in range(self._history_list.count()):
            item = self._history_list.item(i)
            assert item is not None
            texts.append(item.text())
        return texts

    @property
    def list_widget(self) -> QListWidget | None:
        """Zielwidget für echte Maus-/Tastatur-Ereignisse (Tests)."""
        return self._history_list

    def _build(self) -> None:
        popup = QDialog(self._parent, Qt.WindowType.Tool)
        popup.setWindowTitle(tr("history.window_title"))
        popup.setMinimumWidth(270)

        lay = QVBoxLayout(popup)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        lbl = QLabel(tr("history.hint"))
        lay.addWidget(lbl)

        history_list = _HistoryList(self._jump_to_current)
        history_list.setMinimumHeight(200)
        history_list.setToolTip(tr("history.list.tooltip"))
        history_list.itemDoubleClicked.connect(self._jump_to_item)
        lay.addWidget(history_list)

        self._popup = popup
        self._hint = lbl
        self._history_list = history_list
        self._apply_palette()
        self._refresh_list()

    def _apply_palette(self) -> None:
        """Setzt die Popup-Stile aus der aktiven Palette (hell/dunkel)."""
        if self._popup is None or self._hint is None or self._history_list is None:
            return
        p = active_palette()
        self._popup.setStyleSheet(f"QDialog {{ background: {p.inspector}; }}")
        self._hint.setStyleSheet(
            f"color: {p.text3}; font-size: 10px; background: transparent;")
        self._history_list.setStyleSheet(f"""
            QListWidget {{
                background: {p.tabbar}; color: {p.text2};
                border: 1px solid {p.divider};
                border-radius: 6px; font-size: 11px;
            }}
            QListWidget:focus {{ border: 1px solid {p.accent}; }}
            QListWidget::item {{ padding: 6px 10px; border-bottom: 1px solid {p.hairline}; }}
            QListWidget::item:selected {{ background: {p.accent_soft}; color: {p.accent_text}; }}
            QListWidget::item:hover:!selected {{ background: {p.surface}; }}
        """)

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

    def _jump_to_current(self) -> None:
        """Tastatur-Sprung (Enter/Return) auf den aktuell gewählten Eintrag."""
        if self._history_list is None:
            return
        item = self._history_list.currentItem()
        if item is not None:
            self._jump_to_item(item)
