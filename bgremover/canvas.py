"""Bild-Canvas: Werkzeuge, Auswahl-Maske, Undo/Redo, Crop-UI.

Reine PIL/NumPy-Bildoperationen liegen in ``bgremover.image_ops``; diese
Klasse besitzt UI-Zustand, Undo/Redo, Qt-Signale und interaktive Overlays.
"""
from __future__ import annotations

import functools
from collections.abc import Callable
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, UnidentifiedImageError
from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QDragEnterEvent,
    QDropEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
)

from bgremover.canvas_crop import CanvasCrop
from bgremover.canvas_history import CanvasHistory
from bgremover.canvas_lasso import CanvasLasso
from bgremover.canvas_selection import CanvasSelection
from bgremover.canvas_transform import CanvasTransform
from bgremover.canvas_viewport import CanvasViewport
from bgremover.constants import (
    _DEFAULT_BRUSH_RADIUS,
    _DEFAULT_TOLERANCE,
    TOOL_BRUSH,
    TOOL_ERASER,
    TOOL_LASSO,
    TOOL_WAND,
    logger,
)
from bgremover.crop import CropOverlayItem
from bgremover.icons import make_brush_cursor, make_eraser_cursor, make_wand_cursor
from bgremover.image_loading import open_validated_image
from bgremover.image_ops import save_image_file
from bgremover.image_utils import (
    make_checker_brush,
    mask_to_overlay,
    pil_to_numpy_readonly,
)
from bgremover.status_messages import StatusMessages as SM


def _requires_image(method: Callable[..., None]) -> Callable[..., None]:
    """Frühausstieg-Guard für ImageCanvas-Methoden ohne geladenes Bild.

    Ersetzt den mehrfach byte-identisch wiederholten Block
    ``if self._pil is None: self.statusMsg.emit("Kein Bild geladen"); return``.
    """
    @functools.wraps(method)
    def wrapper(self: ImageCanvas, *args: object, **kwargs: object) -> None:
        if self._pil is None:
            self.statusMsg.emit(SM.KEIN_BILD_GELADEN)
            return
        method(self, *args, **kwargs)
    return wrapper


def _selection_mode_from_modifiers(
    mods: Qt.KeyboardModifier,
) -> Literal["set", "add", "subtract"]:
    if mods & Qt.KeyboardModifier.ShiftModifier:
        return "add"
    if mods & Qt.KeyboardModifier.ControlModifier:
        return "subtract"
    return "set"


class ImageCanvas(QGraphicsView):
    statusMsg      = pyqtSignal(str)
    historyChanged = pyqtSignal(list)   # list[str] – Beschreibungen, neueste zuerst
    cropModeChanged = pyqtSignal(bool)  # True = Crop-Overlay aktiv
    imageLoaded    = pyqtSignal(str)    # absoluter Pfad eines frisch geladenen Bildes
    loadRequested  = pyqtSignal(str)    # Drop/Recent → MainWindow lädt asynchron
    wandRequested  = pyqtSignal(object, int, int, int)  # arr, x, y, tolerance

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
        # Persistentes Overlay-Pixmap für inkrementelle Pinsel-Updates;
        # None = kein Overlay aktiv (leere Auswahl).
        self._overlay_pixmap: QPixmap | None = None

        self._pil:  Image.Image | None = None
        self._arr:  np.ndarray  | None = None
        self._selection = CanvasSelection(0, 0)
        # _content_revision ändert sich bei jeder sichtbaren Bildzustandsänderung.
        # Externe Worker nutzen diese Revision als Stale-Check statt
        # Objektidentität.
        self._content_revision: int = 0
        self._history = CanvasHistory()

        self._tool      = TOOL_WAND
        self._tolerance = _DEFAULT_TOLERANCE
        self._brush_r   = _DEFAULT_BRUSH_RADIUS
        self._drawing   = False

        # Zauberstab-Berechnung laeuft asynchron im Worker – damit grosse
        # einfarbige Flaechen die UI nicht einfrieren. Diese Felder halten
        # den Aufruf-Kontext (Modus und Bildrevision) ueber den Async-
        # Sprung, damit das Ergebnis korrekt mit der bestehenden Auswahl
        # verrechnet und ein veraltetes Ergebnis (Bild inzwischen
        # gewechselt) verworfen werden kann. ``_wand_busy`` blockt
        # gleichzeitig weitere Wand-Klicks, solange die Berechnung laeuft.
        self._wand_busy = False
        self._wand_pending_mode: Literal["set", "add", "subtract"] = "set"
        self._wand_pending_revision: int = -1

        # Polygon-Lasso-Werkzeug
        self._lasso = CanvasLasso(self._scene)

        # Crop-Overlay (Zustand + Mausgesten in eigener Klasse)
        self._crop = CanvasCrop(
            self._scene, self, self.cropModeChanged.emit)

        # Geometrie-Transformationen (Drehen/Spiegeln/Ecken abrunden)
        self._transform = CanvasTransform(self)

        # Viewport (Zoom, Pan, Fit-to-View, Pixmap-Refresh)
        self._viewport = CanvasViewport(
            self, self._scene, self._img_item, self._vp)

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
    def current_tool(self) -> str:
        """Aktuell aktives Werkzeug-Token (TOOL_WAND/BRUSH/ERASER/LASSO)."""
        return self._tool

    @property
    def version(self) -> int:
        """Öffentliche Stale-Revision; erhöht sich bei jeder Bildänderung."""
        return self._content_revision

    @property
    def content_revision(self) -> int:
        """Monoton steigender Zähler; erhöht sich bei jeder Bildänderung."""
        return self._content_revision

    @property
    def _crop_overlay(self) -> CropOverlayItem | None:
        """Delegator auf ``CanvasCrop`` — von Tests/Debug-Code gelesen."""
        return self._crop.overlay

    @property
    def _mask(self) -> np.ndarray | None:
        """Übergangs-Accessor für ältere Tests und interne Debug-Zugriffe."""
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

    def fit_to_view(self) -> None:
        """Bild in die Ansicht einpassen (ohne internen Item-Zugriff von aussen)."""
        self._viewport.fit_to_view()

    # ── Laden ────────────────────────────────────────────────

    def load_image(self, path: str) -> None:
        """Synchroner Lade-Pfad – wird vom Drop-Event und von Tests genutzt.

        Für den File-Dialog läuft der gleiche Vorgang in einem Worker
        (siehe ``MainWindow._load_image_async`` + ``apply_loaded_image``).
        Beide Pfade nutzen denselben Validierungs-Helfer, damit
        Format-Whitelist, ``verify()`` und Megapixel-Schutz nicht nur dem
        Worker zugutekommen.
        """
        img, err = open_validated_image(path)
        if err is not None:
            self.statusMsg.emit(err)
            return
        assert img is not None
        self.apply_loaded_image(img, path)

    def apply_loaded_image(self, img: Image.Image, path: str) -> None:
        """Übernimmt ein bereits geladenes (PIL-)Bild als neuen Canvas-State."""
        self._history.clear()
        self._history.set_original(img)
        self._reset_transient_state()
        self._apply_pil(img, push=False)
        self._viewport.fit_to_view()
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
            self._history.push(self._pil, desc)
            self._emit_history()
        self._set_image_state(img)

    def _refresh_image(self) -> None:
        self._viewport.refresh_image(self._pil)

    def _refresh_overlay(self, dirty: tuple[int, int, int, int] | None = None) -> None:
        """Aktualisiert das rote Auswahl-Overlay.

        Ohne *dirty* wird das Overlay vollständig neu aufgebaut – bei leerer
        Maske aber nur geleert, statt ein volles RGBA-Bild (bei 40 MP rund
        160 MiB) zu allokieren. Mit *dirty* = ``(x0, y0, x1, y1)`` wird nur
        dieses Rechteck in das bestehende Pixmap gemalt (Pinselstrich); das
        spart die wiederholte Vollallokation bei jeder Mausbewegung.
        """
        if self._pil is None:
            return
        mask = self._selection.mask
        if dirty is not None and self._overlay_pixmap is not None:
            x0, y0, x1, y1 = dirty
            patch = mask_to_overlay(mask[y0:y1, x0:x1], x1 - x0, y1 - y0)
            painter = QPainter(self._overlay_pixmap)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Source)
            painter.drawPixmap(x0, y0, patch)
            painter.end()
            self._overlay_item.setPixmap(self._overlay_pixmap)
            return
        if not self._selection.has_selection:
            self._overlay_pixmap = None
            self._overlay_item.setPixmap(QPixmap())
            return
        h, w = mask.shape
        self._overlay_pixmap = mask_to_overlay(mask, w, h)
        self._overlay_item.setPixmap(self._overlay_pixmap)

    def _set_image_state(self, img: Image.Image) -> None:
        """Übernimmt *img* als aktuellen Bildzustand (Pixmap + leere Maske).

        Kapselt den Anzeigezustand und die Content-Revision. Die
        Undo-/Redo-Stapelpflege liegt in ``CanvasHistory``.
        """
        self._pil  = img
        # Read-only-Sicht reicht: flood_fill/remove_selection/replace_selection
        # lesen nur und kopieren bei Bedarf selbst. Spart eine grosse
        # Heap-Allokation pro Bildwechsel.
        self._arr  = pil_to_numpy_readonly(img)
        self._selection.reset(img.width, img.height)
        self._content_revision += 1
        self._refresh_image()
        self._refresh_overlay()

    def _reset_transient_state(self) -> None:
        """Verwirft schwebende Werkzeug-Interaktionen vor einem Inhaltswechsel.

        Entfernt ein Crop-Overlay und meldet das Modus-Ende nur, wenn ein
        Overlay aktiv war – sonst bliebe ein ``cropModeChanged(True)`` ohne
        passendes ``False`` hängen und die Crop-Leiste verschwände nicht.
        Bricht außerdem ein begonnenes Polygon-Lasso ab, damit alte Punkte
        und Vorschaulinien nicht auf das neue Bild übertragen werden.
        """
        was_cropping = self._crop.active
        self._crop.cancel_overlay_only()
        if was_cropping:
            self.cropModeChanged.emit(False)
        self._lasso.cancel()

    def _emit_history(self) -> None:
        """Sendet die aktuelle Verlaufsliste (neueste zuerst)."""
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
        if self._crop.active:
            self.cancel_crop()
            return
        self._apply_history_step(
            self._history.undo(self._pil),
            "Nichts mehr zum Rückgängigmachen",
            "↩  Rückgängig: {desc}",
        )

    def redo(self) -> None:
        if self._crop.active:
            return
        self._apply_history_step(
            self._history.redo(self._pil),
            "Nichts mehr zum Wiederherstellen",
            "↪  Wiederherstellen: {desc}",
        )

    def undo_to(self, steps: int) -> None:
        if self._crop.active:
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
        self._reset_transient_state()
        self._set_image_state(restored)
        self._emit_history()
        self.statusMsg.emit("🔄  Original wiederhergestellt")

    @_requires_image
    def clear_selection(self) -> None:
        self._selection.clear()
        self._refresh_overlay()
        self.statusMsg.emit("Auswahl aufgehoben")

    @_requires_image
    def invert_selection(self) -> None:
        pixels = self._selection.invert()
        self._refresh_overlay()
        self.statusMsg.emit(f"Auswahl invertiert: {pixels:,} Pixel")

    def _morphology(self, radius: int, kind: Literal["expand", "shrink"]) -> None:
        if radius <= 0:
            return
        pixels = self._selection.morphology(radius, kind)
        self._refresh_overlay()
        label = "erweitert" if kind == "expand" else "geschrumpft"
        self.statusMsg.emit(f"Auswahl um {radius} px {label}: {pixels:,} Pixel")

    @_requires_image
    def expand_selection(self, radius: int) -> None:
        self._morphology(radius, "expand")

    @_requires_image
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
            self.statusMsg.emit("Hintergrund entfernt (transparent)")
        except (OSError, ValueError, UnidentifiedImageError) as e:
            # Bewusst eng gefasst: erwartete Bild-/IO-Probleme landen als
            # Statusmeldung, echte Bugs (AttributeError, IndexError, …)
            # propagieren stattdessen sichtbar nach oben.
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
            self.statusMsg.emit(f"Hintergrund ersetzt: {color.name()}")
        except (OSError, ValueError, UnidentifiedImageError) as e:
            logger.exception("Fehler beim Ersetzen")
            self.statusMsg.emit(f"Fehler beim Ersetzen: {e}")

    def apply_ai_result(self, img: Image.Image) -> None:
        self._apply_pil(img, desc="KI-Hintergrundentfernung")
        self.statusMsg.emit("✅ KI-Hintergrundentfernung abgeschlossen")

    def apply_wand_result(self, mask: np.ndarray) -> None:
        """Uebernimmt die im Worker berechnete Zauberstab-Maske.

        Verwirft das Ergebnis, falls die Canvas-Revision sich seit Klick
        veraendert hat (Bild gewechselt/editiert) – das verhindert, dass
        die Auswahl auf das falsche Bild gemalt wird.
        """
        if not self._wand_busy:
            return
        self._wand_busy = False
        if self._content_revision != self._wand_pending_revision:
            self.statusMsg.emit(SM.WAND_VERWORFEN)
            return
        pixels = self._selection.set_wand_result(
            mask, self._wand_pending_mode)
        self._refresh_overlay()
        self.statusMsg.emit(f"Auswahl: {pixels:,} Pixel")

    def cancel_pending_wand(self, msg: str) -> None:
        """Bricht eine laufende Wand-Berechnung im Fehlerfall ab."""
        if not self._wand_busy:
            return
        self._wand_busy = False
        self.statusMsg.emit(f"Auswahl-Fehler: {msg}")

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
            self.statusMsg.emit(SM.KEIN_BILD_ZUM_SPEICHERN)
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
            self.statusMsg.emit(SM.KEIN_BILD_GELADEN)
            return False
        if not self._selection.has_selection:
            self.statusMsg.emit(SM.KEINE_AUSWAHL)
            return False
        return True

    # ── Maus-Events ──────────────────────────────────────────

    def _handle_tool_press(
        self,
        x: int,
        y: int,
        mods: Qt.KeyboardModifier,
    ) -> None:
        """Werkzeug-spezifische Reaktion auf linken Maus-Press."""
        if self._tool == TOOL_WAND:
            assert self._pil is not None and self._arr is not None
            if self._wand_busy:
                self.statusMsg.emit(SM.ZAUBERSTAB_ARBEITET)
                return
            w, h = self._pil.size
            if 0 <= x < w and 0 <= y < h:
                self._wand_busy = True
                self._wand_pending_mode = _selection_mode_from_modifiers(mods)
                self._wand_pending_revision = self._content_revision
                self.statusMsg.emit(SM.AUSWAHL_BERECHNUNG)
                self.wandRequested.emit(
                    self._arr, x, y, self._tolerance)
        elif self._tool == TOOL_LASSO:
            assert self._pil is not None
            w, h = self._pil.size
            if 0 <= x < w and 0 <= y < h:
                self._lasso.set_modifiers_if_first(mods)
                self.statusMsg.emit(self._lasso.add_point(x, y))
        else:
            self._drawing = True
            self._paint_brush(x, y, additive=self._tool == TOOL_BRUSH)

    def mousePressEvent(self, event) -> None:
        if self._pil is None or self._arr is None:
            return super().mousePressEvent(event)

        btn  = event.button()
        sp   = self.mapToScene(event.position().toPoint())
        mods = QApplication.keyboardModifiers()

        if self._crop.handle_press(btn, sp):
            return

        if self._viewport.start_pan_if_requested(btn, mods, event.position()):
            return

        if btn != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)

        x, y = int(sp.x()), int(sp.y())

        self._handle_tool_press(x, y, mods)

    def mouseMoveEvent(self, event) -> None:
        sp = self.mapToScene(event.position().toPoint())

        # Pinsel-Vorschau (außerhalb von Crop-/Pan-Modi)
        if not self._crop.active and not self._viewport.is_panning:
            self._update_brush_preview(sp)
            # Lasso-Vorschaulinie vom letzten Punkt zur Mausposition
            if self._tool == TOOL_LASSO:
                self._lasso.update_preview_line(sp.x(), sp.y())

        if self._crop.handle_move(sp):
            return

        if self._viewport.is_panning:
            self._viewport.update_pan(event.position())
            return
        if self._drawing and event.buttons() & Qt.MouseButton.LeftButton:
            self._paint_brush(
                int(sp.x()), int(sp.y()),
                additive=self._tool == TOOL_BRUSH,
            )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._crop.handle_release():
            return
        if self._viewport.is_panning:
            self._viewport.stop_pan()
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

    def _paint_brush(self, cx: int, cy: int, *, additive: bool) -> None:
        if self._pil is None:
            return
        dirty = self._selection.paint_brush(
            cx, cy, self._brush_r, additive=additive)
        if dirty is not None:
            self._refresh_overlay(dirty)

    # Zoom-Grenzen werden von ``CanvasViewport`` definiert; hier nur als
    # Convenience-Reexport, damit bestehende Tests ``canvas.ZOOM_MIN`` /
    # ``canvas.ZOOM_MAX`` weiter ohne Umweg lesen können.
    ZOOM_MIN = CanvasViewport.ZOOM_MIN
    ZOOM_MAX = CanvasViewport.ZOOM_MAX

    def _zoom(self, factor: float) -> None:
        self._viewport.zoom(factor)

    def wheelEvent(self, event) -> None:
        self._viewport.handle_wheel(event.angleDelta().y())

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

    # ── Geometrie-Transformationen (Delegatoren) ─────────────

    @_requires_image
    def apply_round_corners(self, radius: int) -> None:
        """Rundet die Ecken des Bildes mit dem gegebenen Radius ab."""
        self._transform.apply_round_corners(radius)

    @_requires_image
    def apply_rotate(self, degrees: int) -> None:
        """Dreht das Bild um den angegebenen Winkel (gegen den Uhrzeigersinn)."""
        self._transform.apply_rotate(degrees)

    @_requires_image
    def apply_flip(self, horizontal: bool) -> None:
        """Spiegelt das Bild horizontal oder vertikal."""
        self._transform.apply_flip(horizontal)

    # ── Ausgabeformat – Crop-Overlay (Delegatoren) ───────────

    def start_crop_circle(self) -> None:
        """Startet den interaktiven Kreis-Zuschnitt."""
        self._crop.start_circle()

    def start_crop_ratio(self, ratio_w: int, ratio_h: int) -> None:
        """Startet den interaktiven Zuschnitt für ein Seitenverhältnis."""
        self._crop.start_ratio(ratio_w, ratio_h)

    def confirm_crop(self) -> None:
        """Wendet den aktuellen Crop-Overlay als Zuschnitt an."""
        self._crop.confirm()

    def cancel_crop(self) -> None:
        """Bricht den Zuschnitt ab ohne Änderung."""
        self._crop.cancel()

