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
    _REDO_MAX_ENTRIES,
    _UNDO_MEMORY_LIMIT,
    _ZOOM_FACTOR,
    logger,
)
from bgremover.canvas_history import (
    emit_history as _emit_history_impl,
    img_bytes as _img_bytes_impl,
    redo as _redo_impl,
    restore_original as _restore_original_impl,
    undo as _undo_impl,
    undo_to as _undo_to_impl,
)
from bgremover.canvas_lasso import CanvasLasso
from bgremover.canvas_crop_flow import (
    cancel_crop as _cancel_crop_impl,
    cancel_crop_overlay as _cancel_crop_overlay_impl,
    confirm_crop as _confirm_crop_impl,
    start_crop_overlay as _start_crop_overlay_impl,
)
from bgremover.canvas_events import (
    drag_enter_event as _drag_enter_event_impl,
    drag_move_event as _drag_move_event_impl,
    drop_event as _drop_event_impl,
    handle_crop_press as _handle_crop_press_impl,
    handle_tool_press as _handle_tool_press_impl,
    start_pan_if_requested as _start_pan_if_requested_impl,
    to_img_xy as _to_img_xy_impl,
    zoom as _zoom_impl,
)
from bgremover.canvas_selection import (
    apply_remove as _apply_remove_impl,
    apply_replace as _apply_replace_impl,
    check_selection as _check_selection_impl,
    clear_selection as _clear_selection_impl,
    invert_selection as _invert_selection_impl,
    morphology as _morphology_impl,
    paint_brush as _paint_brush_impl,
)
from bgremover.crop import CropOverlayItem
from bgremover.icons import make_brush_cursor, make_eraser_cursor, make_wand_cursor
from bgremover.image_ops import (
    crop_size_for_ratio,
    flip_image,
    rotate_image,
    round_corners,
    save_image_file,
)
from bgremover.image_utils import (
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
        self._redo:     deque = deque(maxlen=_REDO_MAX_ENTRIES)

        self._tool      = TOOL_WAND
        self._tolerance = _DEFAULT_TOLERANCE
        self._brush_r   = _DEFAULT_BRUSH_RADIUS
        self._panning   = False
        self._pan_start = QPointF()
        self._drawing   = False

        # Polygon-Lasso-Werkzeug
        self._lasso = CanvasLasso(self._scene)

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

    # ── Backward-Compat für bestehende Tests (Refactor-Übergang) ───────
    @property
    def _lasso_pts(self) -> list[tuple[int, int]]:
        return self._lasso.points

    @_lasso_pts.setter
    def _lasso_pts(self, pts: list[tuple[int, int]]) -> None:
        self._lasso.points = pts

    @property
    def _lasso_mods(self) -> Qt.KeyboardModifier:
        return self._lasso.modifiers

    @_lasso_mods.setter
    def _lasso_mods(self, mods: Qt.KeyboardModifier) -> None:
        self._lasso.modifiers = mods

    def fit_to_view(self) -> None:
        """Bild in die Ansicht einpassen (ohne internen Item-Zugriff von aussen)."""
        self.fitInView(self._img_item, Qt.AspectRatioMode.KeepAspectRatio)

    @staticmethod
    def _img_bytes(img: Image.Image) -> int:
        """Geschätzte RGBA-Rohdatengrösse eines Bildes in Bytes."""
        return _img_bytes_impl(img)

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

    def apply_edit(self, img: Image.Image, desc: str = "Bearbeitung") -> None:
        """Wendet einen neuen Bildzustand als Undo-fähige Bearbeitung an."""
        self._apply_pil(img, push=True, desc=desc)

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
            _emit_history_impl(self)
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
        _emit_history_impl(self)

    # ── Undo / Original ──────────────────────────────────────

    def undo(self) -> None:
        _undo_impl(self)

    def redo(self) -> None:
        _redo_impl(self)

    def undo_to(self, steps: int) -> None:
        _undo_to_impl(self, steps)

    def restore_original(self) -> None:
        _restore_original_impl(self)

    def clear_selection(self) -> None:
        _clear_selection_impl(self)

    def invert_selection(self) -> None:
        _invert_selection_impl(self)

    def _morphology(self, radius: int, kind: str) -> None:
        _morphology_impl(self, radius, kind)

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
        _apply_remove_impl(self, _checked)

    def apply_replace(self, color: QColor) -> None:
        _apply_replace_impl(self, color)

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
        return _check_selection_impl(self)

    # ── Maus-Events ──────────────────────────────────────────

    def _to_img_xy(self, event) -> tuple[int, int]:
        return _to_img_xy_impl(self, event)

    def _handle_crop_press(self, btn: Qt.MouseButton, sp: QPointF) -> bool:
        return _handle_crop_press_impl(self, btn, sp)

    def _start_pan_if_requested(
        self,
        btn: Qt.MouseButton,
        mods: Qt.KeyboardModifier,
        pos: QPointF,
    ) -> bool:
        return _start_pan_if_requested_impl(self, btn, mods, pos)

    def _handle_tool_press(
        self,
        x: int,
        y: int,
        mods: Qt.KeyboardModifier,
    ) -> None:
        _handle_tool_press_impl(self, x, y, mods)

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
        if self._mask is None or self._pil is None:
            return
        self._mask = self._lasso.close_to_mask(self._mask)
        self._refresh_overlay()
        self.statusMsg.emit(
            f"Polygon-Lasso: {int(self._mask.sum()):,} Pixel ausgewählt")

    def _lasso_cancel(self) -> None:
        self._lasso.cancel()

    def _paint_brush(self, cx: int, cy: int) -> None:
        _paint_brush_impl(self, cx, cy)

    # Zoom-Grenzen: verhindert dass Bild auf 0 schrumpft (kein Klick mehr
    # möglich) oder so groß wird, dass Qt-Rasterung sichtbar wird.
    ZOOM_MIN = 0.05
    ZOOM_MAX = 40.0

    def _zoom(self, factor: float) -> None:
        _zoom_impl(self, factor)

    def wheelEvent(self, event) -> None:
        self._zoom(_ZOOM_FACTOR if event.angleDelta().y() > 0 else 1 / _ZOOM_FACTOR)

    def leaveEvent(self, event) -> None:
        # Pinsel-Vorschau verstecken, sobald die Maus den View verlässt
        self._brush_preview.setVisible(False)
        super().leaveEvent(event)

    # ── Drag & Drop ──────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent | None) -> None:
        _drag_enter_event_impl(self, event)

    def dragMoveEvent(self, event) -> None:  # ← PFLICHT: ohne dies wird Drop abgelehnt
        _drag_move_event_impl(self, event)

    def dropEvent(self, event: QDropEvent | None) -> None:
        _drop_event_impl(self, event)

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
        _start_crop_overlay_impl(self, cw, ch, is_circle)

    def confirm_crop(self) -> None:
        """Wendet den aktuellen Crop-Overlay als Zuschnitt an."""
        _confirm_crop_impl(self)

    def cancel_crop(self) -> None:
        """Bricht den Zuschnitt ab ohne Änderung."""
        _cancel_crop_impl(self)

    def _cancel_crop_overlay(self) -> None:
        _cancel_crop_overlay_impl(self)
