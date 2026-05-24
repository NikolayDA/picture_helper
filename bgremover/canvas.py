"""Bild-Canvas: Werkzeuge, Auswahl-Maske, Undo/Redo, Crop-UI.

Reine PIL/NumPy-Bildoperationen liegen in ``bgremover.image_ops``; diese
Klasse besitzt UI-Zustand, Undo/Redo, Qt-Signale und interaktive Overlays.
"""
from __future__ import annotations

import functools
from collections import deque
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QDragEnterEvent,
    QDropEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
)

from bgremover.constants import (
    TOOL_BRUSH,
    TOOL_ERASER,
    TOOL_LASSO,
    TOOL_WAND,
    _DEFAULT_BRUSH_RADIUS,
    _DEFAULT_TOLERANCE,
    _MAX_MEGAPIXELS,
    _UNDO_MEMORY_LIMIT,
    _ZOOM_FACTOR,
    logger,
)
from bgremover.crop import CropOverlayItem
from bgremover.icons import make_brush_cursor, make_eraser_cursor, make_wand_cursor
from bgremover.image_ops import (
    crop_image,
    crop_size_for_ratio,
    flip_image,
    remove_selection,
    replace_selection,
    rotate_image,
    round_corners,
    save_image_file,
)
from bgremover.image_utils import (
    flood_fill,
    make_checker_brush,
    mask_to_overlay,
    pil_to_numpy,
    pil_to_qpixmap,
)


def _requires_image(method: Callable[..., None]) -> Callable[..., None]:
    """Frühausstieg-Guard für ImageCanvas-Methoden ohne geladenes Bild.

    Ersetzt den mehrfach byte-identisch wiederholten Block
    ``if self._pil is None: self.statusMsg.emit("Kein Bild geladen"); return``.
    """
    @functools.wraps(method)
    def wrapper(self: "ImageCanvas", *args: object, **kwargs: object) -> None:
        if self._pil is None:
            self.statusMsg.emit("Kein Bild geladen")
            return
        method(self, *args, **kwargs)
    return wrapper


class ImageCanvas(QGraphicsView):
    statusMsg      = pyqtSignal(str)
    historyChanged = pyqtSignal(list)   # list[str] – Beschreibungen, neueste zuerst
    cropModeChanged = pyqtSignal(bool)  # True = Crop-Overlay aktiv
    imageLoaded    = pyqtSignal(str)    # absoluter Pfad eines frisch geladenen Bildes
    loadRequested  = pyqtSignal(str)    # Drop/Recent → MainWindow lädt asynchron

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(make_checker_brush())
        self.setAcceptDrops(True)
        # viewport() liefert laut Stub Optional, ist hier nach Setup aber
        # garantiert vorhanden – einmalig narrowen und cachen, damit
        # spaetere `_vp.update()`-Aufrufe ohne wiederholten Guard auskommen.
        vp = self.viewport()
        assert vp is not None
        self._vp = vp
        self._vp.setAcceptDrops(True)

        self._img_item     = QGraphicsPixmapItem()
        self._overlay_item = QGraphicsPixmapItem()
        self._scene.addItem(self._img_item)
        self._scene.addItem(self._overlay_item)
        self._overlay_item.setZValue(1)

        self._pil:      Image.Image | None = None
        self._original: Image.Image | None = None
        self._arr:      np.ndarray  | None = None
        self._mask:     np.ndarray  | None = None
        # Monotone Zähler:
        # - _version ist ein Legacy-Zähler für reine Bildwechsel (Laden).
        # - _content_revision ändert sich bei jeder sichtbaren Bildzustandsänderung.
        # Externe Worker nutzen diese content_revision als Stale-Check statt
        # Objektidentität.
        self._version:  int = 0
        self._content_revision: int = 0
        # Undo-Stack: (Image, Beschreibung der Aktion die dazu führte)
        # Kein festes maxlen – Grösse wird durch _UNDO_MEMORY_LIMIT begrenzt.
        self._undo:     deque = deque()
        # Laufende Summe der Undo-Rohdaten in Bytes (statt deque jedes Mal
        # komplett aufzusummieren – O(1) statt O(n) pro Bearbeitung).
        self._undo_bytes: int = 0
        # Redo-Stack: gespiegelt zum Undo. Wird bei jeder neuen Aktion
        # via _apply_pil(push=True) geleert.
        self._redo:     deque = deque(maxlen=20)

        self._tool      = TOOL_WAND
        self._tolerance = _DEFAULT_TOLERANCE
        self._brush_r   = _DEFAULT_BRUSH_RADIUS
        self._panning   = False
        self._pan_start = QPointF()
        self._drawing   = False

        # Polygon-Lasso-Werkzeug
        self._lasso_pts:       list[tuple[int, int]] = []
        self._lasso_path_item: QGraphicsPathItem | None = None
        self._lasso_line_item: QGraphicsLineItem | None = None
        self._lasso_mods:      Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier

        # Crop-Overlay-Zustand
        self._crop_overlay:      CropOverlayItem | None = None
        self._crop_dragging:     bool    = False
        self._crop_drag_start:   QPointF = QPointF()
        self._crop_start_pos:    QPointF = QPointF()
        self._crop_resizing:     bool    = False   # True = Resize-Drag läuft
        self._crop_resize_corner: int    = -1      # 0-3 welche Ecke

        # Pinsel-Vorschau-Kreis (sichtbar bei Tool=brush/eraser)
        self._brush_preview = QGraphicsEllipseItem()
        self._brush_preview.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
        self._brush_preview.setBrush(QBrush(QColor(74, 144, 217, 30)))
        self._brush_preview.setZValue(20)
        self._brush_preview.setVisible(False)
        self._scene.addItem(self._brush_preview)

    # ── Öffentliche Accessors (Kapselung) ────────────────────

    @property
    def image(self) -> Image.Image | None:
        """Aktuell angezeigtes PIL-Bild (oder ``None``)."""
        return self._pil

    @property
    def has_image(self) -> bool:
        """True, sobald ein Bild geladen ist."""
        return self._pil is not None

    @property
    def version(self) -> int:
        """Öffentliche Stale-Revision; erhöht sich bei jeder Bildänderung."""
        return self._content_revision

    @property
    def content_revision(self) -> int:
        """Monoton steigender Zähler; erhöht sich bei jeder Bildänderung."""
        return self._content_revision

    def fit_to_view(self) -> None:
        """Bild in die Ansicht einpassen (ohne internen Item-Zugriff von aussen)."""
        self.fitInView(self._img_item, Qt.AspectRatioMode.KeepAspectRatio)

    @staticmethod
    def _img_bytes(img: Image.Image) -> int:
        """Geschätzte RGBA-Rohdatengrösse eines Bildes in Bytes."""
        return img.width * img.height * 4

    # ── Laden ────────────────────────────────────────────────

    def load_image(self, path: str) -> None:
        """Synchroner Lade-Pfad – wird vom Drop-Event und von Tests genutzt.

        Für den File-Dialog läuft der gleiche Vorgang in einem Worker
        (siehe ``MainWindow._load_image_async`` + ``apply_loaded_image``).
        """
        # EXIF-Orientierung anwenden: Smartphone-Fotos sind oft im Sensor
        # gespeichert wie aufgenommen und werden erst über das EXIF-Tag
        # korrekt orientiert. Ohne exif_transpose() erscheinen sie gekippt.
        img: Image.Image = Image.open(path)
        mp = img.width * img.height / 1_000_000
        if mp > _MAX_MEGAPIXELS:
            self.statusMsg.emit(
                f"Bild zu groß ({mp:.0f} MP) – Maximum: {_MAX_MEGAPIXELS} MP")
            return
        img = ImageOps.exif_transpose(img).convert("RGBA")
        self.apply_loaded_image(img, path)

    def apply_loaded_image(self, img: Image.Image, path: str) -> None:
        """Übernimmt ein bereits geladenes (PIL-)Bild als neuen Canvas-State."""
        self._version += 1
        self._original = img.copy()
        self._undo.clear()
        self._undo_bytes = 0
        self._redo.clear()
        self._cancel_crop_overlay()
        self._apply_pil(img, push=False)
        self.fitInView(self._img_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.statusMsg.emit(
            f"Geöffnet: {Path(path).name}  ({img.width} × {img.height} px)")
        self.imageLoaded.emit(str(Path(path).resolve()))

    def _apply_pil(
        self,
        img: Image.Image,
        push: bool = True,
        desc: str = "Bearbeitung",
    ) -> None:
        if push and self._pil is not None:
            self._undo.append((self._pil.copy(), desc))
            self._undo_bytes += self._img_bytes(self._pil)
            # Neue Aktion ⇒ Redo-Branch verwerfen (klassisches Editor-Verhalten)
            self._redo.clear()
            # Älteste Einträge entfernen, solange das Speicherlimit überschritten ist.
            while len(self._undo) > 1 and self._undo_bytes > _UNDO_MEMORY_LIMIT:
                evicted, _ = self._undo.popleft()
                self._undo_bytes -= self._img_bytes(evicted)
            self._emit_history()
        self._set_image_state(img)

    def _refresh_image(self) -> None:
        if self._pil:
            px = pil_to_qpixmap(self._pil)
            self._img_item.setPixmap(px)
            self._scene.setSceneRect(QRectF(px.rect()))
            self._img_item.update()
            self._vp.update()

    def _refresh_overlay(self) -> None:
        if self._mask is not None and self._pil:
            h, w = self._mask.shape
            self._overlay_item.setPixmap(mask_to_overlay(self._mask, w, h))

    def _set_image_state(self, img: Image.Image) -> None:
        """Übernimmt *img* als aktuellen Bildzustand (Pixmap + leere Maske).

        Kapselt den Block, der zuvor identisch in ``_apply_pil``, ``undo``,
        ``redo``, ``undo_to`` und ``restore_original`` stand. Setzt
        ausschliesslich den Anzeigezustand und die Content-Revision –
        Undo-/Redo-Stapelpflege bleibt Sache der Aufrufer.
        """
        self._pil  = img
        self._arr  = pil_to_numpy(img)
        self._mask = np.zeros((img.height, img.width), dtype=bool)
        self._content_revision += 1
        self._refresh_image()
        self._refresh_overlay()

    def _emit_history(self) -> None:
        """Sendet die aktuelle Verlaufsliste (neueste zuerst)."""
        self.historyChanged.emit([d for _, d in reversed(list(self._undo))])

    # ── Undo / Original ──────────────────────────────────────

    def undo(self) -> None:
        if self._crop_overlay is not None:
            self.cancel_crop(); return
        if self._undo:
            img, desc = self._undo.pop()
            self._undo_bytes -= self._img_bytes(img)
            # Aktuellen Stand für mögliches Redo aufbewahren
            if self._pil is not None:
                self._redo.append((self._pil.copy(), desc))
            self._set_image_state(img)
            self._emit_history()
            self.statusMsg.emit(f"↩  Rückgängig: {desc}")
        else:
            self.statusMsg.emit("Nichts mehr zum Rückgängigmachen")

    def redo(self) -> None:
        """Macht ein zuvor mit ``undo()`` rückgängig gemachte Aktion wieder."""
        if self._crop_overlay is not None:
            return
        if self._redo:
            img, desc = self._redo.pop()
            if self._pil is not None:
                self._undo.append((self._pil.copy(), desc))
                self._undo_bytes += self._img_bytes(self._pil)
            self._set_image_state(img)
            self._emit_history()
            self.statusMsg.emit(f"↪  Wiederherstellen: {desc}")
        else:
            self.statusMsg.emit("Nichts mehr zum Wiederherstellen")

    def undo_to(self, steps: int) -> None:
        """Mehrere Schritte auf einmal rückgängig machen.

        Verhält sich wie mehrfaches ``undo()``: jeder übersprungene Stand
        wandert auf den Redo-Stapel, der Sprung ist also wiederherstellbar.
        """
        if self._crop_overlay is not None:
            self.cancel_crop(); return
        actual = min(steps, len(self._undo))
        if actual <= 0:
            return
        img, desc = None, ""
        for _ in range(actual):
            img, desc = self._undo.pop()
            self._undo_bytes -= self._img_bytes(img)
            if self._pil is not None:
                self._redo.append((self._pil.copy(), desc))
            self._pil = img
        assert img is not None  # actual > 0 (Guard oben) -> Schleife lief ≥ 1×
        self._set_image_state(img)
        self._emit_history()
        self.statusMsg.emit(f"↩  {actual} Schritt(e) rückgängig  (bis: {desc})")

    def restore_original(self) -> None:
        if self._original:
            self._cancel_crop_overlay()
            # Aktuellen Stand für Undo aufbewahren, statt den Verlauf
            # zu verwerfen – so kann der Nutzer das Zurücksetzen
            # selbst wieder rückgängig machen.
            if self._pil is not None:
                self._undo.append((self._pil.copy(), "🔄 Original wiederhergestellt"))
                self._undo_bytes += self._img_bytes(self._pil)
            # Redo verwerfen – „Original wiederherstellen" ist ein Sprung.
            self._redo.clear()
            self._set_image_state(self._original.copy())
            self._emit_history()
            self.statusMsg.emit("🔄  Original wiederhergestellt")

    def clear_selection(self) -> None:
        if self._mask is not None:
            self._mask[:] = False
            self._refresh_overlay()
            self.statusMsg.emit("Auswahl aufgehoben")

    def invert_selection(self) -> None:
        """Kehrt die aktuelle Maske um (Vorder- ↔ Hintergrund)."""
        if self._mask is None or self._pil is None:
            self.statusMsg.emit("Kein Bild geladen")
            return
        self._mask = ~self._mask
        self._refresh_overlay()
        self.statusMsg.emit(
            f"Auswahl invertiert: {int(self._mask.sum()):,} Pixel")

    def _morphology(self, radius: int, kind: str) -> None:
        """Erweitert oder schrumpft die Boolean-Maske um ``radius`` Pixel
        mittels PIL-Morphologie-Filtern."""
        if self._mask is None or self._pil is None or radius <= 0:
            return
        mask_img = Image.fromarray(
            (self._mask * 255).astype(np.uint8), mode="L")
        # PIL-Filter brauchen ungerade Kernelgrößen
        size = radius * 2 + 1
        filt: ImageFilter.RankFilter
        if kind == "expand":
            filt = ImageFilter.MaxFilter(size)
            label = "erweitert"
        else:
            filt = ImageFilter.MinFilter(size)
            label = "geschrumpft"
        result = mask_img.filter(filt)
        self._mask = np.array(result) > 127
        self._refresh_overlay()
        self.statusMsg.emit(
            f"Auswahl um {radius} px {label}: "
            f"{int(self._mask.sum()):,} Pixel")

    def expand_selection(self, radius: int) -> None:
        self._morphology(radius, "expand")

    def shrink_selection(self, radius: int) -> None:
        self._morphology(radius, "shrink")

    # ── Tool-Einstellungen ───────────────────────────────────

    def set_tool(self, tool: str) -> None:
        if self._tool == TOOL_LASSO and tool != TOOL_LASSO:
            self._lasso_cancel()
        self._tool = tool
        if tool == TOOL_WAND:
            self.setCursor(make_wand_cursor())
            self._brush_preview.setVisible(False)
        elif tool == TOOL_BRUSH:
            self.setCursor(make_brush_cursor(self._brush_r * 2))
        elif tool == TOOL_ERASER:
            self.setCursor(make_eraser_cursor(self._brush_r * 2))
        elif tool == TOOL_LASSO:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
            self._brush_preview.setVisible(False)
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self._brush_preview.setVisible(False)

    def set_tolerance(self, v: int) -> None:
        self._tolerance = v

    def set_brush_size(self, v: int) -> None:
        self._brush_r = max(1, v // 2)
        # Cursor sofort aktualisieren
        if self._tool == TOOL_BRUSH:
            self.setCursor(make_brush_cursor(v))
        elif self._tool == TOOL_ERASER:
            self.setCursor(make_eraser_cursor(v))

    def _update_brush_preview(self, sp: QPointF) -> None:
        """Aktualisiert Position/Sichtbarkeit des Pinsel-Vorschau-Kreises."""
        if self._tool not in (TOOL_BRUSH, TOOL_ERASER) or self._pil is None:
            self._brush_preview.setVisible(False)
            return
        r = self._brush_r
        self._brush_preview.setRect(sp.x() - r, sp.y() - r, r * 2, r * 2)
        self._brush_preview.setVisible(True)

    # ── Operationen ──────────────────────────────────────────

    def apply_remove(self, _checked=False) -> None:
        try:
            if not self._check_selection():
                return
            assert self._arr is not None  # _check_selection garantiert _pil; _arr ist invariant zusammen gesetzt
            assert self._mask is not None
            self._apply_pil(
                remove_selection(self._arr, self._mask),
                desc="Hintergrund entfernt",
            )
            self._vp.update()
            self.statusMsg.emit("Hintergrund entfernt (transparent)")
        except Exception as e:
            logger.exception("Fehler beim Entfernen")
            self.statusMsg.emit(f"Fehler beim Entfernen: {e}")

    def apply_replace(self, color: QColor) -> None:
        try:
            if not self._check_selection():
                return
            assert self._arr is not None  # _check_selection garantiert _pil; _arr ist invariant zusammen gesetzt
            assert self._mask is not None
            self._apply_pil(
                replace_selection(self._arr, self._mask,
                                  (color.red(), color.green(), color.blue())),
                desc=f"Farbe ersetzt ({color.name()})",
            )
            self._vp.update()
            self.statusMsg.emit(f"Hintergrund ersetzt: {color.name()}")
        except Exception as e:
            logger.exception("Fehler beim Ersetzen")
            self.statusMsg.emit(f"Fehler beim Ersetzen: {e}")

    def apply_ai_result(self, img: Image.Image) -> None:
        self._apply_pil(img, desc="KI-Hintergrundentfernung")
        self.statusMsg.emit("✅ KI-Hintergrundentfernung abgeschlossen")

    def save_image(self, path: str) -> bool:
        """Speichert das aktuelle Bild; gibt ``True`` bei Erfolg zurück.

        E/A-Fehler (nicht beschreibbarer Pfad, voller Datenträger,
        unbekanntes Format …) werden protokolliert und als Statusmeldung
        gemeldet, statt unbehandelt zu propagieren – konsistent zu
        ``apply_remove``/``apply_replace``. Der Rückgabewert erlaubt dem
        Aufrufer, einen fehlgeschlagenen Pfad nicht als Quick-Save-Ziel
        zu merken.
        """
        if self._pil is None:
            self.statusMsg.emit("Kein Bild zum Speichern")
            return False
        try:
            save_image_file(self._pil, path)
        except Exception as e:
            logger.exception("Speichern fehlgeschlagen: %s", path)
            self.statusMsg.emit(f"Speichern fehlgeschlagen: {e}")
            return False
        self.statusMsg.emit(f"💾 Gespeichert: {Path(path).name}")
        return True

    def _check_selection(self) -> bool:
        if self._pil is None:
            self.statusMsg.emit("Kein Bild geladen")
            return False
        if self._mask is None or not self._mask.any():
            self.statusMsg.emit("Keine Auswahl – erst Bereich mit Zauberstab oder Pinsel auswählen")
            return False
        return True

    # ── Maus-Events ──────────────────────────────────────────

    def _to_img_xy(self, event) -> tuple[int, int]:
        sp = self.mapToScene(event.position().toPoint())
        return int(sp.x()), int(sp.y())

    def mousePressEvent(self, event) -> None:
        if self._pil is None or self._arr is None:
            return super().mousePressEvent(event)

        btn  = event.button()
        sp   = self.mapToScene(event.position().toPoint())
        mods = QApplication.keyboardModifiers()

        # ── Crop-Modus ────────────────────────────────────────
        if self._crop_overlay is not None:
            if btn == Qt.MouseButton.LeftButton:
                corner = self._crop_overlay.corner_hit(sp.x(), sp.y())
                if corner >= 0:
                    # Resize-Drag starten
                    self._crop_resizing      = True
                    self._crop_resize_corner = corner
                    self._crop_drag_start    = sp
                    self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor
                                          if corner in (0, 3)
                                          else Qt.CursorShape.SizeBDiagCursor))
                elif self._crop_overlay.inside(sp.x(), sp.y()):
                    self._crop_dragging   = True
                    self._crop_drag_start = sp
                    self._crop_start_pos  = self._crop_overlay.top_left
                    self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            return  # alle anderen Aktionen im Crop-Modus blockieren

        # ── Pan: Alt+Drag oder Mittelklick ────────────────────
        if (btn == Qt.MouseButton.MiddleButton or
                (btn == Qt.MouseButton.LeftButton and
                 mods & Qt.KeyboardModifier.AltModifier)):
            self._panning   = True
            self._pan_start = event.position()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            return

        if btn != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)

        x, y = int(sp.x()), int(sp.y())

        if self._tool == TOOL_WAND:
            w, h = self._pil.size
            if 0 <= x < w and 0 <= y < h:
                new = flood_fill(self._arr, x, y, self._tolerance)
                if mods & Qt.KeyboardModifier.ShiftModifier:
                    self._mask |= new
                elif mods & Qt.KeyboardModifier.ControlModifier:
                    self._mask &= ~new
                else:
                    self._mask = new
                self._refresh_overlay()
                self.statusMsg.emit(f"Auswahl: {int(self._mask.sum()):,} Pixel")
        elif self._tool == TOOL_LASSO:
            w, h = self._pil.size
            if 0 <= x < w and 0 <= y < h:
                if not self._lasso_pts:
                    self._lasso_mods = mods
                self._lasso_add_point(x, y)
        else:
            self._drawing = True
            self._paint_brush(x, y)

    def mouseMoveEvent(self, event) -> None:
        sp = self.mapToScene(event.position().toPoint())

        # Pinsel-Vorschau (außerhalb von Crop-/Pan-Modi)
        if self._crop_overlay is None and not self._panning:
            self._update_brush_preview(sp)
            # Lasso-Vorschaulinie vom letzten Punkt zur Mausposition
            if self._tool == TOOL_LASSO and self._lasso_pts and self._lasso_line_item is not None:
                last = self._lasso_pts[-1]
                self._lasso_line_item.setLine(last[0], last[1], sp.x(), sp.y())

        # ── Crop-Resize ───────────────────────────────────────
        if self._crop_resizing and self._crop_overlay is not None:
            self._crop_overlay.resize_from_corner(
                self._crop_resize_corner, sp.x(), sp.y())
            cw, ch = self._crop_overlay.size
            self.statusMsg.emit(
                f"⇲ Größe: {int(round(cw))} × {int(round(ch))} px")
            return

        # ── Crop-Drag ─────────────────────────────────────────
        if self._crop_dragging and self._crop_overlay is not None:
            delta = sp - self._crop_drag_start
            self._crop_overlay.set_position(
                self._crop_start_pos.x() + delta.x(),
                self._crop_start_pos.y() + delta.y())
            return

        # Cursor im Crop-Modus anpassen
        if self._crop_overlay is not None:
            corner = self._crop_overlay.corner_hit(sp.x(), sp.y())
            if corner >= 0:
                self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor
                                       if corner in (0, 3)
                                       else Qt.CursorShape.SizeBDiagCursor))
            elif self._crop_overlay.inside(sp.x(), sp.y()):
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            return

        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            assert hbar is not None and vbar is not None
            hbar.setValue(hbar.value() - int(delta.x()))
            vbar.setValue(vbar.value() - int(delta.y()))
            return
        if self._drawing and event.buttons() & Qt.MouseButton.LeftButton:
            self._paint_brush(int(sp.x()), int(sp.y()))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._crop_resizing:
            self._crop_resizing = False
            self._crop_resize_corner = -1
            if self._crop_overlay is not None:
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            return
        if self._crop_dragging:
            self._crop_dragging = False
            if self._crop_overlay is not None:
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            return
        if self._panning:
            self._panning = False
            self.set_tool(self._tool)
            return
        self._drawing = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if self._tool == TOOL_LASSO and event.button() == Qt.MouseButton.LeftButton:
            if len(self._lasso_pts) >= 3:
                self._lasso_close()
            else:
                self._lasso_cancel()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and self._lasso_pts:
            self._lasso_cancel()
            self.statusMsg.emit("Polygon-Lasso abgebrochen")
            return
        super().keyPressEvent(event)

    def _lasso_add_point(self, x: int, y: int) -> None:
        self._lasso_pts.append((x, y))
        path = QPainterPath()
        path.moveTo(*self._lasso_pts[0])
        for px, py in self._lasso_pts[1:]:
            path.lineTo(px, py)
        pen = QPen(QColor(255, 255, 255, 220), 1.5, Qt.PenStyle.DashLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        if self._lasso_path_item is None:
            self._lasso_path_item = QGraphicsPathItem()
            self._lasso_path_item.setZValue(25)
            self._scene.addItem(self._lasso_path_item)
        self._lasso_path_item.setPen(pen)
        self._lasso_path_item.setPath(path)
        if self._lasso_line_item is None:
            line_pen = QPen(QColor(200, 200, 200, 160), 1.2, Qt.PenStyle.DotLine)
            self._lasso_line_item = QGraphicsLineItem(x, y, x, y)
            self._lasso_line_item.setPen(line_pen)
            self._lasso_line_item.setZValue(25)
            self._scene.addItem(self._lasso_line_item)
        else:
            self._lasso_line_item.setLine(x, y, x, y)
        n = len(self._lasso_pts)
        suffix = "e" if n != 1 else ""
        self.statusMsg.emit(
            f"Polygon-Lasso: {n} Punkt{suffix} — Doppelklick zum Abschließen · Esc = abbrechen")

    def _lasso_close(self) -> None:
        pts = self._lasso_pts.copy()
        mods = self._lasso_mods
        self._lasso_cancel()
        if self._mask is None or self._pil is None:
            return
        h, w = self._mask.shape
        mask_img = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask_img).polygon(pts, fill=255)
        new_mask = np.array(mask_img) > 127
        if mods & Qt.KeyboardModifier.ShiftModifier:
            self._mask |= new_mask
        elif mods & Qt.KeyboardModifier.ControlModifier:
            self._mask &= ~new_mask
        else:
            self._mask = new_mask
        self._refresh_overlay()
        self.statusMsg.emit(
            f"Polygon-Lasso: {int(self._mask.sum()):,} Pixel ausgewählt")

    def _lasso_cancel(self) -> None:
        if self._lasso_path_item is not None:
            self._scene.removeItem(self._lasso_path_item)
            self._lasso_path_item = None
        if self._lasso_line_item is not None:
            self._scene.removeItem(self._lasso_line_item)
            self._lasso_line_item = None
        self._lasso_pts.clear()
        self._lasso_mods = Qt.KeyboardModifier.NoModifier

    def _paint_brush(self, cx: int, cy: int) -> None:
        if self._mask is None or self._pil is None:
            return
        r  = self._brush_r
        h, w = self._mask.shape
        y0, y1 = max(0, cy - r), min(h, cy + r + 1)
        x0, x1 = max(0, cx - r), min(w, cx + r + 1)
        yy, xx = np.ogrid[y0:y1, x0:x1]
        circle = (yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2
        if self._tool == TOOL_BRUSH:
            self._mask[y0:y1, x0:x1][circle] = True
        else:
            self._mask[y0:y1, x0:x1][circle] = False
        self._refresh_overlay()

    # Zoom-Grenzen: verhindert dass Bild auf 0 schrumpft (kein Klick mehr
    # möglich) oder so groß wird, dass Qt-Rasterung sichtbar wird.
    ZOOM_MIN = 0.05
    ZOOM_MAX = 40.0

    def _zoom(self, factor: float) -> None:
        new_scale = self.transform().m11() * factor
        if self.ZOOM_MIN <= new_scale <= self.ZOOM_MAX:
            self.scale(factor, factor)

    def wheelEvent(self, event) -> None:
        self._zoom(_ZOOM_FACTOR if event.angleDelta().y() > 0 else 1 / _ZOOM_FACTOR)

    def leaveEvent(self, event) -> None:
        # Pinsel-Vorschau verstecken, sobald die Maus den View verlässt
        self._brush_preview.setVisible(False)
        super().leaveEvent(event)

    # ── Drag & Drop ──────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent | None) -> None:
        if event is None:
            return
        mime = event.mimeData()
        if mime is not None and mime.hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:  # ← PFLICHT: ohne dies wird Drop abgelehnt
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent | None) -> None:
        if event is None:
            return
        mime = event.mimeData()
        if mime is None:
            return
        exts = (".png", ".jpg", ".jpeg", ".webp",
                ".bmp", ".tiff", ".tif", ".gif")
        valid = [url.toLocalFile() for url in mime.urls()
                 if Path(url.toLocalFile()).suffix.lower() in exts]
        if not valid:
            self.statusMsg.emit("Format nicht unterstützt")
            return
        # Asynchron laden (gleicher Worker-Pfad wie der Datei-Dialog),
        # damit ein grosses Foto die UI nicht einfriert.
        self.loadRequested.emit(valid[0])
        if len(valid) > 1:
            self.statusMsg.emit(
                f"Geöffnet: {Path(valid[0]).name}  "
                f"({len(valid) - 1} weitere Datei(en) ignoriert)")

    # ── Ecken abrunden ───────────────────────────────────────

    @_requires_image
    def apply_round_corners(self, radius: int) -> None:
        """Rundet die Ecken des Bildes mit dem gegebenen Radius ab."""
        assert self._pil is not None  # @_requires_image-Dekorator garantiert das
        if radius <= 0:
            self.statusMsg.emit("Radius muss > 0 sein")
            return
        result, r = round_corners(self._pil, radius)
        self._apply_pil(result, desc=f"Ecken abgerundet ({r} px)")
        self.statusMsg.emit(f"Ecken abgerundet: {r} px Radius")

    # ── Drehen ───────────────────────────────────────────────

    @_requires_image
    def apply_rotate(self, degrees: int) -> None:
        """Dreht das Bild um den angegebenen Winkel (gegen den Uhrzeigersinn).
        Bei 90° / 270° werden Breite und Höhe getauscht.
        Bei beliebigen Winkeln wird die Canvas so vergrößert, dass nichts abgeschnitten wird.
        """
        assert self._pil is not None  # @_requires_image-Dekorator garantiert das
        result = rotate_image(self._pil, degrees)
        direction = "↺" if degrees > 0 else "↻"
        self._apply_pil(result, desc=f"{direction} Gedreht {abs(degrees)}°")
        self.statusMsg.emit(
            f"{direction} Gedreht: {abs(degrees)}°  "
            f"({result.width} × {result.height} px)"
        )

    # ── Spiegeln ─────────────────────────────────────────────

    @_requires_image
    def apply_flip(self, horizontal: bool) -> None:
        """Spiegelt das Bild horizontal oder vertikal."""
        assert self._pil is not None  # @_requires_image-Dekorator garantiert das
        result = flip_image(self._pil, horizontal)
        if horizontal:
            self._apply_pil(result, desc="↔ Horizontal gespiegelt")
            self.statusMsg.emit("↔ Horizontal gespiegelt")
        else:
            self._apply_pil(result, desc="↕ Vertikal gespiegelt")
            self.statusMsg.emit("↕ Vertikal gespiegelt")

    # ── Ausgabeformat – Crop-Overlay ─────────────────────────

    @_requires_image
    def start_crop_circle(self) -> None:
        """Startet den interaktiven Kreis-Zuschnitt."""
        assert self._pil is not None  # @_requires_image-Dekorator garantiert das
        size = min(self._pil.width, self._pil.height)
        self._start_crop_overlay(size, size, is_circle=True)

    @_requires_image
    def start_crop_ratio(self, ratio_w: int, ratio_h: int) -> None:
        """Startet den interaktiven Zuschnitt für ein Seitenverhältnis."""
        assert self._pil is not None  # @_requires_image-Dekorator garantiert das
        cw, ch = crop_size_for_ratio(self._pil.size, ratio_w, ratio_h)
        self._start_crop_overlay(cw, ch, is_circle=False)

    def _start_crop_overlay(self, cw: int, ch: int, is_circle: bool) -> None:
        # Aufrufer (start_crop_circle / start_crop_ratio) sind @_requires_image-
        # dekoriert; _pil ist hier garantiert nicht None.
        assert self._pil is not None
        self._cancel_crop_overlay()
        self._crop_overlay = CropOverlayItem(
            self._pil.width, self._pil.height, cw, ch, is_circle)
        self._scene.addItem(self._crop_overlay)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.cropModeChanged.emit(True)
        label = "Kreis" if is_circle else f"{cw} × {ch} px"
        self.statusMsg.emit(
            f"✂  Ausschnitt verschieben  [{label}]  —  dann ✓ Anwenden klicken")

    def confirm_crop(self) -> None:
        """Wendet den aktuellen Crop-Overlay als Zuschnitt an."""
        if self._crop_overlay is None or self._pil is None:
            return
        r = self._crop_overlay.crop_rect()
        cx, cy, cw, ch = r.x(), r.y(), r.width(), r.height()
        is_circle = self._crop_overlay.is_circle
        result = crop_image(self._pil, (cx, cy, cw, ch), is_circle=is_circle)

        if is_circle:
            desc = "Format: Kreis"
        else:
            desc = f"Format: {cw}×{ch} px"

        self._cancel_crop_overlay()
        self.cropModeChanged.emit(False)
        self._apply_pil(result, desc=desc)
        self.statusMsg.emit(f"✂  Zugeschnitten: {result.width} × {result.height} px")

    def cancel_crop(self) -> None:
        """Bricht den Zuschnitt ab ohne Änderung."""
        self._cancel_crop_overlay()
        self.cropModeChanged.emit(False)
        self.set_tool(self._tool)
        self.statusMsg.emit("Zuschnitt abgebrochen")

    def _cancel_crop_overlay(self) -> None:
        if self._crop_overlay is not None:
            self._scene.removeItem(self._crop_overlay)
            self._crop_overlay = None
        self._crop_dragging      = False
        self._crop_resizing      = False
        self._crop_resize_corner = -1
