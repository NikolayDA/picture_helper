"""Bild-Canvas: Werkzeuge, Auswahl-Maske, Undo/Redo, Crop-UI.

Reine PIL/NumPy-Bildoperationen liegen in ``bgremover.image_ops``; diese
Klasse besitzt UI-Zustand, Undo/Redo, Qt-Signale und interaktive Overlays.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, ImageOps
from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QDragEnterEvent,
    QDropEvent,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
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
    _ZOOM_FACTOR,
    logger,
)
from bgremover.canvas_history import CanvasHistory
from bgremover.canvas_crop import CanvasCrop
from bgremover.canvas_helpers import _requires_image, _selection_mode_from_modifiers
from bgremover.canvas_lasso import CanvasLasso
from bgremover.canvas_selection import CanvasSelection
from bgremover.icons import make_brush_cursor, make_eraser_cursor, make_wand_cursor
from bgremover.image_ops import (
    flip_image,
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

        self._pil:  Image.Image | None = None
        self._arr:  np.ndarray  | None = None
        self._selection = CanvasSelection(0, 0)
        # Monotone Zähler:
        # - _version ist ein Legacy-Zähler für reine Bildwechsel (Laden).
        # - _content_revision ändert sich bei jeder sichtbaren Bildzustandsänderung.
        # Externe Worker nutzen diese content_revision als Stale-Check statt
        # Objektidentität.
        self._version:  int = 0
        self._content_revision: int = 0
        self._history = CanvasHistory()

        self._tool      = TOOL_WAND
        self._tolerance = _DEFAULT_TOLERANCE
        self._brush_r   = _DEFAULT_BRUSH_RADIUS
        self._panning   = False
        self._pan_start = QPointF()
        self._drawing   = False

        # Polygon-Lasso-Werkzeug
        self._lasso = CanvasLasso(self._scene)
        self._crop = CanvasCrop(
            self._scene,
            self,
            self.statusMsg.emit,
            self.cropModeChanged.emit,
            self.setCursor,
            lambda: self.set_tool(self._tool),
        )

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
        return self._pil

    @property
    def has_image(self) -> bool:
        return self._pil is not None

    @property
    def version(self) -> int:
        return self._content_revision

    @property
    def content_revision(self) -> int:
        return self._content_revision

    @property
    def _mask(self) -> np.ndarray | None:
        if self._pil is None:
            return None
        return self._selection.mask

    @_mask.setter
    def _mask(self, mask: np.ndarray | None) -> None:
        if mask is None:
            if self._pil is not None:
                self._selection.reset(self._pil.width, self._pil.height)
            return
        self._selection.reset(mask.shape[1], mask.shape[0])
        self._selection.mask[:] = mask

    @property
    def _crop_overlay(self):
        return self._crop.overlay

    def fit_to_view(self) -> None:
        self.fitInView(self._img_item, Qt.AspectRatioMode.KeepAspectRatio)

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
        self._history.clear()
        self._history.set_original(img)
        self._cancel_crop_overlay()
        self._apply_pil(img, push=False)
        self.fitInView(self._img_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.statusMsg.emit(
            f"Geöffnet: {Path(path).name}  ({img.width} × {img.height} px)")
        self.imageLoaded.emit(str(Path(path).resolve()))

    def apply_edit(self, img: Image.Image, desc: str = "Bearbeitung") -> None:
        self._apply_pil(img, push=True, desc=desc)

    def _apply_pil(
        self,
        img: Image.Image,
        push: bool = True,
        desc: str = "Bearbeitung",
    ) -> None:
        if push and self._pil is not None:
            self._history.push(self._pil, desc)
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
        if self._pil:
            mask = self._selection.mask
            h, w = mask.shape
            self._overlay_item.setPixmap(mask_to_overlay(mask, w, h))

    def _set_image_state(self, img: Image.Image) -> None:
        self._pil  = img
        self._arr  = pil_to_numpy(img)
        self._selection.reset(img.width, img.height)
        self._content_revision += 1
        self._refresh_image()
        self._refresh_overlay()

    def _emit_history(self) -> None:
        self.historyChanged.emit(self._history.descriptions())

    def _apply_history_step(
        self,
        result: tuple[Image.Image, str] | None,
        empty_message: str,
        status_template: str,
    ) -> None:
        if result is None:
            self.statusMsg.emit(empty_message)
            return
        img, desc = result
        self._set_image_state(img)
        self._emit_history()
        self.statusMsg.emit(status_template.format(desc=desc))

    # ── Undo / Original ──────────────────────────────────────

    def undo(self) -> None:
        if self._crop_overlay is not None:
            self.cancel_crop()
            return
        self._apply_history_step(
            self._history.undo(self._pil),
            "Nichts mehr zum Rückgängigmachen",
            "↩  Rückgängig: {desc}",
        )

    def redo(self) -> None:
        if self._crop_overlay is not None:
            return
        self._apply_history_step(
            self._history.redo(self._pil),
            "Nichts mehr zum Wiederherstellen",
            "↪  Wiederherstellen: {desc}",
        )

    def undo_to(self, steps: int) -> None:
        if self._crop_overlay is not None:
            self.cancel_crop()
            return
        result = self._history.undo_to(self._pil, steps)
        if result is None:
            return
        img, desc, actual = result
        self._set_image_state(img)
        self._emit_history()
        self.statusMsg.emit(f"↩  {actual} Schritt(e) rückgängig  (bis: {desc})")

    def restore_original(self) -> None:
        restored = self._history.restore(self._pil)
        if restored is None:
            return
        self._cancel_crop_overlay()
        self._set_image_state(restored)
        self._emit_history()
        self.statusMsg.emit("🔄  Original wiederhergestellt")

    def clear_selection(self) -> None:
        if self._pil is not None:
            self._selection.clear()
            self._refresh_overlay()
            self.statusMsg.emit("Auswahl aufgehoben")

    def invert_selection(self) -> None:
        if self._pil is None:
            self.statusMsg.emit("Kein Bild geladen")
            return
        pixels = self._selection.invert()
        self._refresh_overlay()
        self.statusMsg.emit(f"Auswahl invertiert: {pixels:,} Pixel")

    def _morphology(self, radius: int, kind: Literal["expand", "shrink"]) -> None:
        if self._pil is None or radius <= 0:
            return
        pixels = self._selection.morphology(radius, kind)
        self._refresh_overlay()
        label = "erweitert" if kind == "expand" else "geschrumpft"
        self.statusMsg.emit(f"Auswahl um {radius} px {label}: {pixels:,} Pixel")

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
            assert self._arr is not None
            self._apply_pil(
                self._selection.remove_background(self._arr),
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
            assert self._arr is not None
            self._apply_pil(
                self._selection.replace_background(
                    self._arr,
                    (color.red(), color.green(), color.blue()),
                ),
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
        if not self._selection.has_selection:
            self.statusMsg.emit("Keine Auswahl – erst Bereich mit Zauberstab oder Pinsel auswählen")
            return False
        return True

    # ── Maus-Events ──────────────────────────────────────────

    def _handle_crop_press(self, btn: Qt.MouseButton, sp: QPointF) -> bool:
        return self._crop.handle_press(btn, sp)

    def _start_pan_if_requested(
        self,
        btn: Qt.MouseButton,
        mods: Qt.KeyboardModifier,
        pos: QPointF,
    ) -> bool:
        """Startet Pan-Modus (Alt+LMB oder MMB); True => Event konsumiert."""
        if (btn == Qt.MouseButton.MiddleButton or
                (btn == Qt.MouseButton.LeftButton and
                 mods & Qt.KeyboardModifier.AltModifier)):
            self._panning = True
            self._pan_start = pos
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            return True
        return False

    def _handle_tool_press(
        self,
        x: int,
        y: int,
        mods: Qt.KeyboardModifier,
    ) -> None:
        """Werkzeug-spezifische Reaktion auf linken Maus-Press."""
        if self._tool == TOOL_WAND:
            assert self._pil is not None and self._arr is not None
            w, h = self._pil.size
            if 0 <= x < w and 0 <= y < h:
                new = flood_fill(self._arr, x, y, self._tolerance)
                pixels = self._selection.set_wand_result(
                    new, _selection_mode_from_modifiers(mods))
                self._refresh_overlay()
                self.statusMsg.emit(f"Auswahl: {pixels:,} Pixel")
        elif self._tool == TOOL_LASSO:
            assert self._pil is not None
            w, h = self._pil.size
            if 0 <= x < w and 0 <= y < h:
                self._lasso.set_modifiers_if_first(mods)
                self.statusMsg.emit(self._lasso.add_point(x, y))
        else:
            self._drawing = True
            self._paint_brush(x, y)

    def mousePressEvent(self, event) -> None:
        if self._pil is None or self._arr is None:
            return super().mousePressEvent(event)

        btn  = event.button()
        sp   = self.mapToScene(event.position().toPoint())
        mods = QApplication.keyboardModifiers()

        if self._handle_crop_press(btn, sp):
            return

        if self._start_pan_if_requested(btn, mods, event.position()):
            return

        if btn != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)

        x, y = int(sp.x()), int(sp.y())

        self._handle_tool_press(x, y, mods)

    def mouseMoveEvent(self, event) -> None:
        sp = self.mapToScene(event.position().toPoint())

        # Pinsel-Vorschau (außerhalb von Crop-/Pan-Modi)
        if self._crop_overlay is None and not self._panning:
            self._update_brush_preview(sp)
            # Lasso-Vorschaulinie vom letzten Punkt zur Mausposition
            if self._tool == TOOL_LASSO:
                self._lasso.update_preview_line(sp.x(), sp.y())

        if self._crop.handle_move(sp):
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
        sp = self.mapToScene(event.position().toPoint())
        if self._crop.handle_release(sp):
            return
        if self._panning:
            self._panning = False
            self.set_tool(self._tool)
            return
        self._drawing = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if self._tool == TOOL_LASSO and event.button() == Qt.MouseButton.LeftButton:
            # Qt liefert vor dem Doppelklick bereits ein MousePress.
            # Nur ein dadurch entstandenes Duplikat an der Klickposition verwerfen.
            sp = self.mapToScene(event.position().toPoint())
            self._lasso.undo_last_point_if_duplicate(int(sp.x()), int(sp.y()))
            if self._lasso.point_count >= 3:
                self._lasso_close()
            else:
                self._lasso_cancel()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and self._lasso.has_points:
            self._lasso_cancel()
            self.statusMsg.emit("Polygon-Lasso abgebrochen")
            return
        super().keyPressEvent(event)

    def _lasso_close(self) -> None:
        if self._pil is None:
            return
        mode = _selection_mode_from_modifiers(self._lasso.modifiers)
        new_mask = self._lasso.close_to_selection_mask(self._selection.mask.shape)
        pixels = self._selection.set_polygon_result(new_mask, mode)
        self._refresh_overlay()
        self.statusMsg.emit(
            f"Polygon-Lasso: {pixels:,} Pixel ausgewählt")

    def _lasso_cancel(self) -> None:
        self._lasso.cancel()

    def _paint_brush(self, cx: int, cy: int) -> None:
        if self._pil is None:
            return
        self._selection.paint_brush(
            cx, cy, self._brush_r, additive=self._tool == TOOL_BRUSH)
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
        self._crop.start_circle()

    @_requires_image
    def start_crop_ratio(self, ratio_w: int, ratio_h: int) -> None:
        self._crop.start_ratio(ratio_w, ratio_h)

    def _start_crop_overlay(self, cw: int, ch: int, is_circle: bool) -> None:
        self._crop.start_overlay(cw, ch, is_circle)

    def confirm_crop(self) -> None:
        self._crop.confirm()

    def cancel_crop(self) -> None:
        self._crop.cancel()

    def _cancel_crop_overlay(self) -> None:
        self._crop.clear()
