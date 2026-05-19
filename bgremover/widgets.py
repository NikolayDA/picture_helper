"""TopIconTabBar / TopIconTabWidget – Tabs mit grossem Icon oben.

Verbatim aus ``BgRemover.py`` verschoben (Runde 5, Phase B – Schritt 10).
Keine Verhaltensaenderung.
"""
from __future__ import annotations

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QIcon
from PyQt6.QtWidgets import (
    QStyle,
    QStyleOptionTab,
    QStylePainter,
    QTabBar,
    QTabWidget,
)


class TopIconTabBar(QTabBar):
    """Tab-Bar mit großem Icon oben und zentriertem Text darunter.

    Qt zeichnet das Icon standardmäßig links neben dem Text – ein reines
    Stylesheet kann das nicht ändern. Deshalb wird das Tab hier manuell
    gemalt: Tab-Hintergrund/-Rahmen weiter über den Stil (Stylesheet),
    Icon und Text aber selbst und vertikal gestapelt.
    """

    _ICON_TOP_PAD = 11    # Abstand Tab-Oberkante → Icon
    _ICON_TEXT_GAP = 6    # Abstand Icon → Text
    _TEXT_BOTTOM_PAD = 9  # Abstand Text → Tab-Unterkante
    _TEXT_SIDE_PAD = 8    # seitlicher Mindestabstand Text → Tab-Rand

    def __init__(self, icon_px: int = 30, parent=None) -> None:
        super().__init__(parent)
        self._icon_px = icon_px
        # Breiten werden selbst gleichmäßig auf die volle Breite verteilt –
        # Qts proportionale Expand-Heuristik darf das nicht verändern.
        self.setExpanding(False)

    def _text_font(self, bold: bool = False) -> QFont:
        f = self.font()
        f.setPixelSize(12)
        f.setBold(bold)
        return f

    def _wrap(self, text: str, fm: QFontMetrics, max_w: int) -> list:
        """Bricht ein zu breites Label in max. 2 Zeilen um (an '/' oder Space)."""
        if max_w <= 0 or fm.horizontalAdvance(text) <= max_w:
            return [text]
        if "/" in text:
            i = text.index("/")
            return [text[:i + 1], text[i + 1:].strip()]
        if " " in text:
            i = text.index(" ")
            return [text[:i], text[i + 1:]]
        mid = len(text) // 2
        return [text[:mid], text[mid:]]

    def _equal_width(self, index: int) -> int:
        """Volle Spaltenbreite gleichmäßig auf alle Tabs aufteilen.

        Die Bar-Breite leitet sich aus der Summe der Tab-SizeHints ab –
        deshalb wird hier die Breite des übergeordneten QTabWidget
        verwendet (sonst zirkuläre Abhängigkeit → degenerierte Breite).
        """
        n = self.count() or 1
        parent = self.parentWidget()
        total = parent.width() if parent is not None else 0
        if total <= 0:
            total = self.width()
        if total <= 0:                  # vor dem ersten Layout
            return max(self._icon_px + 20, 80)
        base = total // n
        rem = total - base * n          # Restpixel auf die ersten Tabs verteilen
        return base + (1 if index < rem else 0)

    def tabSizeHint(self, index: int) -> QSize:
        fm = QFontMetrics(self._text_font(bold=True))
        # immer Platz für 2 Zeilen → alle Tabs gleich hoch
        height = (self._ICON_TOP_PAD + self._icon_px + self._ICON_TEXT_GAP
                  + 2 * fm.height() + self._TEXT_BOTTOM_PAD)
        return QSize(self._equal_width(index), height)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Tab-Geometrie an die neue Bar-Breite anpassen (gleiche Breiten).
        self.updateGeometry()

    def paintEvent(self, event) -> None:
        painter = QStylePainter(self)
        opt = QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            rect = self.tabRect(i)

            # Tab-Form (Hintergrund, Auswahl-Unterstrich) über den Stil –
            # Icon/Text vom Stil ausblenden, da selbst gezeichnet wird.
            opt.text = ""
            opt.icon = QIcon()
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, opt)

            selected = bool(opt.state & QStyle.StateFlag.State_Selected)
            hovered = bool(opt.state & QStyle.StateFlag.State_MouseOver)
            enabled = bool(opt.state & QStyle.StateFlag.State_Enabled)

            # Icon zentriert oben
            icon = self.tabIcon(i)
            if not icon.isNull():
                mode = (QIcon.Mode.Normal if enabled
                        else QIcon.Mode.Disabled)
                pm = icon.pixmap(QSize(self._icon_px, self._icon_px), mode)
                ix = rect.x() + (rect.width() - self._icon_px) // 2
                iy = rect.y() + self._ICON_TOP_PAD
                painter.drawPixmap(ix, iy, pm)

            # Text (1–2 Zeilen) zentriert darunter
            if not enabled:
                color = QColor("#555")
            elif selected:
                color = QColor("#e0e0e0")
            elif hovered:
                color = QColor("#aaaaaa")
            else:
                color = QColor("#777777")
            font = self._text_font(bold=selected)
            painter.setFont(font)
            painter.setPen(color)
            fm = QFontMetrics(font)
            lines = self._wrap(self.tabText(i), fm,
                               rect.width() - 2 * self._TEXT_SIDE_PAD)
            line_h = fm.height()
            block_top = (rect.y() + self._ICON_TOP_PAD + self._icon_px
                         + self._ICON_TEXT_GAP)
            # Zeilenblock vertikal in der für 2 Zeilen reservierten Höhe zentrieren
            y0 = block_top + (2 * line_h - len(lines) * line_h) // 2
            for k, line in enumerate(lines):
                r = QRect(rect.x(), y0 + k * line_h, rect.width(), line_h)
                painter.drawText(
                    r,
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                    line)


class TopIconTabWidget(QTabWidget):
    """QTabWidget, das die TopIconTabBar verwendet (setTabBar ist protected)."""

    def __init__(self, icon_px: int = 30, parent=None) -> None:
        super().__init__(parent)
        self.setTabBar(TopIconTabBar(icon_px, self))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Bar deterministisch auf die volle Spaltenbreite ziehen – das löst
        # in der Bar layoutTabs() aus, sodass alle Tabs gleich breit werden
        # und die ganze Breite füllen.
        bar = self.tabBar()
        g = bar.geometry()
        if g.width() != self.width():
            bar.setGeometry(0, g.y(), self.width(), g.height())

