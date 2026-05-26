"""Gemeinsame Widget-Helfer fuer das rechte Panel."""
from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from bgremover.icons import make_tool_icon
from bgremover.theme import SLD_STYLE, _Theme


def _make_section(title: str, accent: str = "#4a90d9") -> tuple[QWidget, QVBoxLayout]:
    """Sektion ohne QGroupBox – farbiger Titel + dünne Trennlinie."""
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    v = QVBoxLayout(container)
    v.setSpacing(10)
    v.setContentsMargins(0, 14, 0, 10)
    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(f"""
        color: {accent};
        font-size: 13px;
        font-weight: bold;
        background: transparent;
        padding: 2px 0 4px 8px;
        border-left: 3px solid {accent};
    """)
    v.addWidget(title_lbl)
    return container, v


def _make_label(text: str, color: str = "#888", size: int = 12) -> QLabel:
    """Einfaches Info-Label mit anpassbarer Farbe und Schriftgrösse."""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {color}; font-size: {size}px; background: transparent;")
    lbl.setWordWrap(True)
    return lbl


def _make_icon_row(icon_name: str, text: str, color: str = "#888",
                   size: int = 12, icon_px: int = 18) -> QWidget:
    """Info-Zeile: Werkzeug-Icon (wie in der Toolbar) + Text, klein."""
    row = QWidget()
    row.setStyleSheet("background: transparent;")
    h = QHBoxLayout(row)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(8)
    ic = QLabel()
    ic.setPixmap(make_tool_icon(icon_name, icon_px)
                 .pixmap(QSize(icon_px, icon_px)))
    ic.setFixedSize(icon_px, icon_px)
    ic.setStyleSheet("background: transparent;")
    txt = QLabel(text)
    txt.setStyleSheet(
        f"color: {color}; font-size: {size}px; background: transparent;")
    txt.setWordWrap(True)
    h.addWidget(ic, 0, Qt.AlignmentFlag.AlignVCenter)
    h.addWidget(txt, 1)
    return row


def _make_hdivider() -> QWidget:
    """Dünne horizontale Trennlinie für das rechte Panel."""
    f = QWidget()
    f.setFixedHeight(1)
    f.setStyleSheet(f"background: {_Theme.DIVIDER};")
    return f


def _make_scroll_tab() -> tuple[QWidget, QVBoxLayout]:
    """Gibt (outer_widget, inner_layout) mit ScrollArea zurück."""
    outer_w = QWidget()
    outer_w.setStyleSheet(f"background: {_Theme.BG_PANEL};")
    outer_lay = QVBoxLayout(outer_w)
    outer_lay.setContentsMargins(0, 0, 0, 0)
    outer_lay.setSpacing(0)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setStyleSheet("""
        QScrollArea { background: #1a1a1a; border: none; }
        QScrollBar:vertical { background: #1a1a1a; width: 6px; margin: 0; }
        QScrollBar::handle:vertical {
            background: #3a3a3a; border-radius: 3px; min-height: 20px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    """)
    inner_w = QWidget()
    inner_w.setStyleSheet(f"background: {_Theme.BG_PANEL};")
    inner_lay = QVBoxLayout(inner_w)
    inner_lay.setContentsMargins(16, 16, 16, 16)
    inner_lay.setSpacing(14)
    scroll.setWidget(inner_w)
    outer_lay.addWidget(scroll)
    return outer_w, inner_lay


def _make_panel_btn(label: str, bg: str, fg: str, hover: str,
                    tooltip: str = "", height: int = 36,
                    icon_name: str = "") -> QPushButton:
    """Stilisierter Aktions-Button für das rechte Panel."""
    b = QPushButton(label)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {bg}; color: {fg}; border: none;
            border-radius: 8px; padding: 0 14px;
            font-size: 12px; font-weight: 500;
            min-height: {height}px; text-align: center;
        }}
        QPushButton:hover {{ background: {hover}; }}
        QPushButton:pressed {{ background: {bg}; }}
        QPushButton:disabled {{ background: #252525; color: #555; }}
    """)
    if icon_name:
        b.setIcon(make_tool_icon(icon_name, 22))
        b.setIconSize(QSize(22, 22))
    if tooltip:
        b.setToolTip(tooltip)
    return b


def _make_slider(lo: int, hi: int, val: int, tip: str = "") -> QSlider:
    """Horizontaler Schieberegler mit einheitlichem Panel-Stil."""
    s = QSlider(Qt.Orientation.Horizontal)
    s.setRange(lo, hi)
    s.setValue(val)
    s.setStyleSheet(SLD_STYLE)
    if tip:
        s.setToolTip(tip)
    return s


_SPIN_STYLE = (
    "QSpinBox { background:#222; color:#ddd; border:1px solid #3a3a3a;"
    " border-radius:6px; padding:3px 5px; font-size:12px; }"
    "QSpinBox::up-button, QSpinBox::down-button { width:18px; }"
)
