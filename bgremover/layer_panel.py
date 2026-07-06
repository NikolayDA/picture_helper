"""Ebenen-Panel (#334): Liste + Aktionen für das Mehr-Ebenen-Projektmodell.

Wird in eine Schritt-Seite des geführten Workflows im rechten Panel
(``right_panel.py``) eingebettet (Schritt „Relief & Ebenen"). Das
Panel ist zustandslos gegenüber dem Modell: ``MainWindow`` verbindet das
``ImageCanvas.layersChanged``-Signal mit :meth:`LayerPanel.refresh`, das die
Liste aus den übergebenen :class:`~bgremover.canvas.LayerInfo` neu aufbaut. Alle
Interaktionen laufen über die Callbacks in :class:`LayerPanelActions` – ohne
direkte Abhängigkeit vom Canvas oder MainWindow.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QStandardItemModel
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from bgremover.canvas import LayerInfo
from bgremover.i18n import tr
from bgremover.icons import make_tool_icon
from bgremover.project_model import LayerRole, role_allowed_for_kind
from bgremover.right_panel_tabs import _make_scroll_tab, _make_section
from bgremover.theme import active_palette, combo_style, slider_style

# Reihenfolge der Rollen-Auswahl im Kombinationsfeld (None = keine Rolle).
_ROLE_ORDER: list[LayerRole | None] = [
    None,
    LayerRole.COLOR_MOTIF,
    LayerRole.HEIGHT_MAP,
    LayerRole.GLOSS_MASK,
]


def _role_label(role: LayerRole | None) -> str:
    """Übersetztes Label einer Rolle (literale ``tr``-Keys für die i18n-Coverage)."""
    if role is LayerRole.COLOR_MOTIF:
        return tr("layers.role.color_motif")
    if role is LayerRole.HEIGHT_MAP:
        return tr("layers.role.height_map")
    if role is LayerRole.GLOSS_MASK:
        return tr("layers.role.gloss")
    return tr("layers.role.none")


@dataclass(frozen=True)
class LayerPanelActions:
    """Callbacks des Ebenen-Panels – ohne Abhängigkeit vom MainWindow."""

    add_layer: Callable[[], None]
    delete_active: Callable[[], None]
    duplicate_active: Callable[[], None]
    move_active_up: Callable[[], None]
    move_active_down: Callable[[], None]
    rename_active: Callable[[], None]
    set_active: Callable[[str], None]
    set_visible: Callable[[str, bool], None]
    set_opacity: Callable[[str, float], None]
    set_active_role: Callable[[LayerRole | None], None]


class LayerPanel:
    """Baut und pflegt den Ebenen-Tab; ``refresh`` rendert die aktuelle Liste."""

    def __init__(self, actions: LayerPanelActions) -> None:
        self._actions = actions
        self._list_layout: QVBoxLayout | None = None
        self._role_combo: QComboBox | None = None
        self._action_buttons: list[QPushButton] = []

    # ── Aufbau ───────────────────────────────────────────────────────────
    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()
        section, body = _make_section(tr("right_panel.layers.section"))

        body.addLayout(self._build_action_bar())

        p = active_palette()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        # Mindesthöhe, damit die Ebenenliste im Einzel-Scroll-Schritt (#440)
        # nicht auf ihre winzige sizeHint zusammenfällt.
        scroll.setMinimumHeight(150)
        scroll.setStyleSheet(f"QScrollArea {{ background: {p.inspector}; border: none; }}")
        list_host = QWidget()
        list_host.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(list_host)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()
        scroll.setWidget(list_host)
        body.addWidget(scroll, 1)

        body.addLayout(self._build_role_row())
        layout.addWidget(section)
        layout.addStretch()

        self.refresh([])
        return outer, {"layer_role_combo": self._role_combo or QComboBox()}

    def _action_button(
        self, icon_name: str, tip: str, slot: Callable[[], None],
    ) -> QPushButton:
        p = active_palette()
        btn = QPushButton()
        btn.setObjectName("layerActionButton")
        btn.setToolTip(tip)
        btn.setFixedSize(32, 30)
        btn.setIcon(make_tool_icon(icon_name, 14, QColor(p.text2)))
        btn.setIconSize(QSize(14, 14))
        btn.setProperty("prototypeIconName", icon_name)
        btn.setStyleSheet(
            f"QPushButton {{ background:{p.surface}; color:{p.text2};"
            f" border:1px solid {p.border_2}; border-radius:7px; }}"
            f"QPushButton:hover {{ background:{p.surface_hover}; }}"
            f"QPushButton:focus {{ outline:none; border:1px solid {p.accent}; }}"
            f"QPushButton:disabled {{ background:{p.divider}; color:{p.muted}; }}")
        btn.clicked.connect(lambda _=False: slot())
        self._action_buttons.append(btn)
        return btn

    def _build_action_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(7)
        for icon_name, tip, slot in (
            ("layer_add", tr("right_panel.layers.add.tooltip"), self._actions.add_layer),
            ("layer_duplicate", tr("right_panel.layers.duplicate.tooltip"),
             self._actions.duplicate_active),
            ("layer_delete", tr("right_panel.layers.delete.tooltip"),
             self._actions.delete_active),
            ("layer_move_up", tr("right_panel.layers.move_up.tooltip"),
             self._actions.move_active_up),
            ("layer_move_down", tr("right_panel.layers.move_down.tooltip"),
             self._actions.move_active_down),
            ("layer_rename", tr("right_panel.layers.rename.tooltip"),
             self._actions.rename_active),
        ):
            row.addWidget(self._action_button(icon_name, tip, slot))
        row.addStretch()
        return row

    def _build_role_row(self) -> QHBoxLayout:
        p = active_palette()
        row = QHBoxLayout()
        row.setSpacing(6)
        label = QLabel(tr("right_panel.layers.role_label"))
        label.setStyleSheet(f"color:{p.text3}; font-size:12px; background:transparent;")
        combo = QComboBox()
        combo.setToolTip(tr("right_panel.layers.role.tooltip"))
        combo.setStyleSheet(combo_style(p))
        for role in _ROLE_ORDER:
            combo.addItem(_role_label(role), role)
        combo.currentIndexChanged.connect(self._on_role_changed)
        self._role_combo = combo
        row.addWidget(label)
        row.addWidget(combo, 1)
        return row

    # ── Aktualisierung ───────────────────────────────────────────────────
    def refresh(self, layers: list[LayerInfo]) -> None:
        """Baut die Ebenenliste aus ``layers`` (oberste zuerst) neu auf."""
        layout = self._list_layout
        if layout is None:
            return
        # Bestehende Zeilen entfernen (das abschließende Stretch bleibt).
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for info in layers:
            layout.insertWidget(layout.count() - 1, self._build_row(info))

        has_layers = bool(layers)
        for btn in self._action_buttons:
            btn.setEnabled(has_layers)
        self._sync_role_combo(layers)

        if not has_layers:
            hint = QLabel(tr("right_panel.layers.empty"))
            hint.setWordWrap(True)
            # Aktiver Hinweistext: text3 statt muted (Kontrastvertrag #441).
            hint.setStyleSheet(
                f"color:{active_palette().text3}; font-size:11px; background:transparent;")
            layout.insertWidget(0, hint)

    def _sync_role_combo(self, layers: list[LayerInfo]) -> None:
        combo = self._role_combo
        if combo is None:
            return
        active = next((info for info in layers if info.active), None)
        combo.setEnabled(active is not None)
        self._sync_role_options(active)
        target = active.role if active is not None else None
        index = next(
            (i for i, role in enumerate(_ROLE_ORDER) if role == target), 0)
        combo.blockSignals(True)
        combo.setCurrentIndex(index)
        combo.blockSignals(False)

    def _sync_role_options(self, active: LayerInfo | None) -> None:
        """Deaktiviert typunverträgliche Rollen-Optionen (Vertrag #364).

        ``HEIGHT_MAP`` ist nur für eine aktive ``LayerKind.HEIGHT``-Ebene
        wählbar; so kann das Panel keinen inkompatiblen Zustand erzeugen. Die
        Option „Keine“ bleibt stets verfügbar.
        """
        combo = self._role_combo
        if combo is None:
            return
        model = combo.model()
        if not isinstance(model, QStandardItemModel):
            return
        for index, role in enumerate(_ROLE_ORDER):
            item = model.item(index)
            if item is None:
                continue
            if active is None or role is None:
                enabled = True
            else:
                enabled = role_allowed_for_kind(role, active.kind)
            item.setEnabled(enabled)

    def _build_row(self, info: LayerInfo) -> QWidget:
        p = active_palette()
        row = QWidget()
        # card_bg statt surface (#482-Review): inaktive Zeilen bleiben damit
        # als Kartenbestandteil konsistent zum Prototyp und kontrastreicher
        # als auf dem helleren surface-Ton (#475/#496).
        row.setStyleSheet(
            f"background:{p.accent_soft}; border-radius:6px;" if info.active
            else f"background:{p.card_bg}; border-radius:6px;")
        h = QHBoxLayout(row)
        h.setContentsMargins(6, 4, 6, 4)
        h.setSpacing(6)

        vis = QPushButton()
        vis.setCheckable(True)
        vis.setChecked(info.visible)
        vis.setFixedWidth(30)
        vis.setMinimumHeight(24)
        vis.setIcon(make_tool_icon(
            "layer_visible", 15, QColor(p.text2 if info.visible else p.text3)))
        vis.setIconSize(QSize(15, 15))
        vis.setProperty("prototypeIconName", "layer_visible")
        vis.setToolTip(tr("right_panel.layers.visible.tooltip"))
        vis.setStyleSheet(
            "QPushButton { background:transparent; border:none; font-size:14px; }"
            f"QPushButton:focus {{ outline:none; border:1px solid {p.accent};"
            " border-radius:4px; }")
        vis.toggled.connect(
            lambda checked, lid=info.id: self._actions.set_visible(lid, checked))
        h.addWidget(vis)

        name = QPushButton(info.name)
        name.setMinimumHeight(24)
        name.setToolTip(tr("right_panel.layers.select.tooltip"))
        name.setStyleSheet(
            "QPushButton { background:transparent; border:none; text-align:left;"
            f" color:{p.text if info.active else p.text3}; font-size:12px;"
            f" font-weight:{'bold' if info.active else 'normal'}; }}"
            f"QPushButton:focus {{ outline:none; border:1px solid {p.accent};"
            " border-radius:4px; }")
        name.clicked.connect(lambda _=False, lid=info.id: self._actions.set_active(lid))
        h.addWidget(name, 1)

        opacity = QSlider(Qt.Orientation.Horizontal)
        opacity.setRange(0, 100)
        opacity.setValue(int(round(info.opacity * 100)))
        opacity.setFixedWidth(90)
        opacity.setStyleSheet(slider_style(p))
        opacity.setToolTip(tr("right_panel.layers.opacity.tooltip"))
        opacity.sliderReleased.connect(
            lambda lid=info.id, s=opacity: self._actions.set_opacity(lid, s.value() / 100))
        h.addWidget(opacity)
        return row

    def _on_role_changed(self, _index: int) -> None:
        combo = self._role_combo
        if combo is None:
            return
        self._actions.set_active_role(combo.currentData())
