"""Bild-Canvas: Werkzeuge, Auswahl-Maske, Undo/Redo, Crop-UI.

Reine PIL/NumPy-Bildoperationen liegen in ``bgremover.image_ops``; diese
Klasse besitzt UI-Zustand, Undo/Redo, Qt-Signale und interaktive Overlays.
"""
from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass
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
from bgremover.canvas_lasso import CanvasLasso
from bgremover.canvas_selection import CanvasSelection
from bgremover.canvas_transform import CanvasTransform
from bgremover.canvas_viewport import CanvasViewport
from bgremover.constants import (
    _DEFAULT_BRUSH_RADIUS,
    _DEFAULT_HEIGHT_STEP,
    _DEFAULT_TOLERANCE,
    BRUSH_CURSOR_MAX_SCREEN_PX,
    BRUSH_TOOLS,
    TOOL_BRUSH,
    TOOL_ERASER,
    TOOL_HEIGHT_DARKEN,
    TOOL_HEIGHT_LIGHTEN,
    TOOL_LASSO,
    TOOL_MOVE,
    TOOL_WAND,
    logger,
)
from bgremover.crop import CropOverlayItem
from bgremover.gloss_preview import compose_over as compose_gloss
from bgremover.gloss_preview import gloss_overlay
from bgremover.height_map import (
    HEIGHT_MAX_8BIT,
    HEIGHT_MAX_16BIT,
    LUMA_WEIGHTS_REC601,
    HeightField,
    HeightMapError,
    UnsupportedHeightSourceError,
    adjust_height,
    generate_from_image,
    height_to_layer,
    image_to_height_field,
    invert_height,
    is_native_16bit_source,
    layer_to_gray_image,
    layer_to_height,
    resize_height_field,
    scale_8bit_height_value,
    set_height,
)
from bgremover.i18n import tr
from bgremover.icons import make_brush_cursor, make_eraser_cursor, make_wand_cursor
from bgremover.image_loading import open_validated_height_image, open_validated_image
from bgremover.image_ops import feather_alpha, save_image_file
from bgremover.image_utils import (
    make_checker_brush,
    mask_to_overlay,
    pil_to_numpy_readonly,
)
from bgremover.preview_mode import PreviewMode
from bgremover.project_history import ProjectHistory
from bgremover.project_model import (
    Layer,
    LayerKind,
    LayerRole,
    Project,
    role_allowed_for_kind,
)
from bgremover.relief_preview import compose_over as compose_relief
from bgremover.relief_preview import relief_shading
from bgremover.status_messages import StatusMessages as SM
from bgremover.theme import Palette, active_palette
from bgremover.units import UnitsError
from bgremover.zoom_control import ZoomControl


@dataclass(frozen=True)
class LayerInfo:
    """Schlanke, Qt-freie Sicht auf eine Ebene für das Ebenen-Panel (#334).

    Reine Anzeigedaten (keine Pixel) – Nutzlast des ``layersChanged``-Signals.
    """

    id: str
    name: str
    kind: LayerKind
    visible: bool
    opacity: float
    locked: bool
    role: LayerRole | None
    active: bool


@dataclass
class _HeightStroke:
    """Arbeitszustand eines malenden Höhen-Strichs (#457).

    Hält die ``uint16``-Arbeitskopie der Höhenwerte, die je Strich bereits
    angepassten Pixel (``touched`` – jedes Pixel wird pro Strich genau einmal
    um ``amount`` verschoben, geklemmt wie ``adjust_height``) und die signierte
    Stärke. Das Modell bleibt während des Strichs unverändert; committet wird
    beim Loslassen als **ein** Undo-Schritt.
    """

    layer_id: str
    values: np.ndarray
    coverage: np.ndarray
    max_value: int
    touched: np.ndarray
    preview_image: Image.Image
    amount: int


def _requires_image(method: Callable[..., None]) -> Callable[..., None]:
    """Frühausstieg-Guard für ImageCanvas-Methoden ohne geladenes Bild.

    Sorgt für eine einheitliche Statusmeldung statt stiller No-ops.
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
    layersChanged  = pyqtSignal(list)   # list[LayerInfo] – oberste Ebene zuerst
    cropModeChanged = pyqtSignal(bool)  # True = Crop-Overlay aktiv
    imageLoaded    = pyqtSignal(str)    # absoluter Pfad eines frisch geladenen Bildes
    loadRequested  = pyqtSignal(str)    # Drop/Recent → MainWindow lädt asynchron
    wandRequested  = pyqtSignal(object, int, int, int)  # arr, x, y, tolerance
    previewSettingsChanged = pyqtSignal(object, int, bool)  # mode, Relief-%, Gloss
    zoomChanged    = pyqtSignal(float)  # Zoom in Prozent (Zoom-Kontrolle, #464)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(make_checker_brush(active_palette()))
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

        # Projektmodell ist die Quelle der Wahrheit (#332). ``self._pil``/
        # ``self._arr`` sind nur Caches des Bildes der **aktiven** Ebene – das
        # Editierziel aller Werkzeuge; angezeigt/gespeichert wird das Komposit
        # (mit Einzel-Ebenen-Schnellpfad für exakte Parität).
        self._project: Project | None = None
        self._pil:  Image.Image | None = None
        self._arr:  np.ndarray  | None = None
        # Transiente Vorschau (#348 Höhen-Optimierung, #360 Farbkorrektur): Der
        # Layer-Override wird nur für das Rendern eingesetzt; ``_preview`` hält
        # das daraus erzeugte Anzeigebild. So bleiben Modus/Relief/Gloss auch
        # während einer Live-Bearbeitung wirksam, ohne das Modell zu verändern.
        self._preview: Image.Image | None = None
        self._preview_layer_override: tuple[str, Image.Image] | None = None
        # Explizite 2D-Anzeige (#387), unabhängig von aktiver Ebene und Export.
        # Der Cache hält absichtlich nur das zuletzt gerenderte Bild: selbst bei
        # 40 MP wächst der Speicher damit nicht pro Modus/Reglerstellung weiter.
        self._preview_mode = PreviewMode.COLOR
        self._relief_strength = 70
        self._gloss_visible = True
        self._preview_render_cache: tuple[
            tuple[int, PreviewMode, int, bool], Image.Image
        ] | None = None
        self._selection = CanvasSelection(0, 0)
        # _content_revision ändert sich bei jeder sichtbaren Bildzustandsänderung.
        # Externe Worker nutzen diese Revision als Stale-Check statt
        # Objektidentität.
        self._content_revision: int = 0
        self._history = ProjectHistory()

        self._tool      = TOOL_WAND
        # Werkzeug-Interaktion (Klick/Zeichnen) global freigeben. Im geführten
        # Workflow lässt das MainWindow dies nur in den Werkzeug-Schritten
        # (Freistellen, Relief) zu, damit ausgeblendete Werkzeuge das Bild nicht
        # unsichtbar weiterbearbeiten (PR #423-Review). Pan/Zoom bleiben unberührt.
        self._tools_enabled = True
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

        # Schwebende Zoom-Kontrolle (#464): sichtbar sobald ein Bild geladen
        # ist, ansonsten ausgeblendet; folgt der Viewport-Größe (resizeEvent).
        self._zoom_control = ZoomControl(self._viewport, self._vp)
        self._zoom_control.setVisible(False)
        self.zoomChanged.connect(self._zoom_control.set_percent)
        # Pinsel-Cursor skaliert mit dem Zoom (#509): jeder Zoompfad
        # (Mausrad, Zoom-Kontrolle, Fit-to-View) erneuert den Bitmap-Cursor.
        self.zoomChanged.connect(self._on_zoom_changed)

        # Laufender Höhen-Malstrich (#457); None = kein Strich aktiv.
        self._height_stroke: _HeightStroke | None = None

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
        """Bild der **aktiven Ebene** – das Editierziel (oder ``None``).

        Bewusst die aktive Ebene und nicht das Komposit: Werkzeuge und Tests
        arbeiten auf dem Editierziel. Das angezeigte Komposit liefert
        ``_render_image``, das gespeicherte/exportierte ``_render_export_image``
        (#363-Vertrag). Bei genau einer Ebene sind beide identisch (Parität).
        """
        return self._pil

    @property
    def project(self) -> Project | None:
        """Aktuelles Projektmodell (oder ``None``); nur lesen."""
        return self._project

    @property
    def has_image(self) -> bool:
        """True, sobald ein Bild/Projekt geladen ist."""
        return self._pil is not None

    @property
    def current_tool(self) -> str:
        """Aktuell aktives Werkzeug-Token (TOOL_WAND/BRUSH/ERASER/LASSO/MOVE/HEIGHT_*)."""
        return self._tool

    @property
    def can_undo(self) -> bool:
        """True, wenn mindestens ein Undo-Schritt vorliegt (Rail-Fuß, #458)."""
        return self._history.can_undo

    @property
    def can_redo(self) -> bool:
        """True, wenn mindestens ein Redo-Schritt vorliegt (Rail-Fuß, #458)."""
        return self._history.can_redo

    @property
    def zoom_control(self) -> ZoomControl:
        """Die schwebende Zoom-Kontrolle (#464); für Theme-Restyle und Tests."""
        return self._zoom_control

    @property
    def preview_mode(self) -> PreviewMode:
        """Aktueller expliziter Vorschaumodus (reiner Anzeigezustand)."""
        return self._preview_mode

    @property
    def relief_strength(self) -> int:
        """Relief-Stärke als UI-Prozentwert ``0..100``."""
        return self._relief_strength

    @property
    def gloss_visible(self) -> bool:
        """Ob Gloss in Gloss-/Kombiniert-Modi sichtbar ist."""
        return self._gloss_visible

    @property
    def selection_tolerance(self) -> int:
        """Aktuelle Zauberstab-Toleranz als UI-Wert."""
        return self._tolerance

    @property
    def brush_size(self) -> int:
        """Aktueller Pinsel-Durchmesser als UI-Wert."""
        return self._brush_r * 2

    def set_preview_mode(self, mode: PreviewMode) -> None:
        """Wechselt den Vorschaumodus ohne Modell-, History- oder Exportänderung."""
        if not isinstance(mode, PreviewMode):
            raise TypeError(f"mode muss PreviewMode sein, war {type(mode).__name__}")
        if mode is self._preview_mode:
            return
        self._preview_mode = mode
        self._preview_settings_updated()

    def set_relief_strength(self, value: int) -> None:
        """Setzt die live wirksame Relief-Stärke in Prozent (``0..100``)."""
        if not 0 <= value <= 100:
            raise ValueError(f"Relief-Stärke muss in 0..100 liegen, war {value}")
        if value == self._relief_strength:
            return
        self._relief_strength = value
        self._preview_settings_updated()

    def set_gloss_visible(self, visible: bool) -> None:
        """Schaltet Gloss live ein/aus, ohne das Projekt zu mutieren."""
        if visible == self._gloss_visible:
            return
        self._gloss_visible = visible
        self._preview_settings_updated()

    def _preview_settings_updated(self) -> None:
        """Invalidiert den Ein-Bild-Cache und synchronisiert Canvas sowie UI."""
        self._preview_render_cache = None
        self._refresh_image()
        self.previewSettingsChanged.emit(
            self._preview_mode, self._relief_strength, self._gloss_visible
        )

    @property
    def version(self) -> int:
        """Alias für ``content_revision``; von Worker-Stale-Checks genutzt."""
        return self._content_revision

    @property
    def content_revision(self) -> int:
        """Monotoner Zähler; erhöht sich bei jeder sichtbaren Bildänderung."""
        return self._content_revision

    @property
    def wand_busy(self) -> bool:
        """True, solange ein Zauberstab-Ergebnis aussteht (``_wand_busy``-Gate)."""
        return self._wand_busy

    @property
    def overlay_pixmap(self) -> QPixmap | None:
        """Aktuelles Auswahl-Overlay-Pixmap (``None`` bei leerer Auswahl); nur lesen."""
        return self._overlay_pixmap

    @property
    def selection_mask(self) -> np.ndarray | None:
        """Aktuelle Auswahlmaske als Read-only-Sicht (``None`` ohne Bild)."""
        return self._mask

    @property
    def _crop_overlay(self) -> CropOverlayItem | None:
        """Test-/Debug-Accessor für das aktive Crop-Overlay."""
        return self._crop.overlay

    @property
    def _mask(self) -> np.ndarray | None:
        """Read-only-Test-/Debug-Accessor für die aktuelle Auswahlmaske."""
        if self._pil is None:
            return None
        return self._selection.mask

    @_mask.setter
    def _mask(self, mask: np.ndarray | None) -> None:
        if mask is None:
            if self._pil is not None:
                self._selection.reset(self._pil.width, self._pil.height)
            return
        self._selection.set_mask(mask)

    def fit_to_view(self) -> None:
        """Bild in die Ansicht einpassen (ohne internen Item-Zugriff von aussen)."""
        self._viewport.fit_to_view()

    def apply_palette(self, p: Palette) -> None:
        """Erneuert das Transparenz-Schachbrett für ein Schema-Umschalten (#478)."""
        self.setBackgroundBrush(make_checker_brush(p))

    # ── Laden ────────────────────────────────────────────────

    def load_image(self, path: str) -> None:
        """Synchroner Lade-Pfad – wird von direkten Aufrufern und Tests genutzt.

        Die interaktiven Pfade (Datei-Dialog, Drag & Drop, Zuletzt geöffnet)
        laufen dagegen asynchron im Worker (``dropEvent`` emittiert
        ``loadRequested`` → ``MainWindow._load_image_async`` →
        ``apply_loaded_image``). Beide Pfade nutzen denselben
        Validierungs-Helfer, damit Format-Whitelist, ``verify()`` und
        Megapixel-Schutz nicht nur dem Worker zugutekommen.
        """
        img, err = open_validated_image(path)
        if err is not None:
            self.statusMsg.emit(err)
            return
        assert img is not None
        self.apply_loaded_image(img, path)

    @staticmethod
    def _single_layer_project(img: Image.Image) -> Project:
        """Baut ein Projekt mit genau einer COLOR-Ebene aus einem Einzelbild.

        Garantiert die heutige Single-Layer-Welt: solange es nur diese eine,
        sichtbare, voll deckende COLOR-Ebene gibt, ist das Komposit identisch zu
        ihrem Bild (Parität).
        """
        project = Project(img.width, img.height)
        layer = project.create_layer(
            img, name=tr("layers.new_name", n=1), kind=LayerKind.COLOR)
        # Objekt-Identität wie bisher bewahren (Parität: ``canvas.image is img``
        # ohne zusätzlichen Kopiersprung; Tests prüfen darüber, welches Ladeergebnis
        # gewann – die Async-Lade-Logik selbst entscheidet über Generationszähler).
        # ``img`` ist auf den Lade-Pfaden bereits RGBA (open_validated_image);
        # sonst bleibt die RGBA-Kopie der Ebene.
        if img.mode == "RGBA":
            layer.image = img
        return project

    def apply_loaded_image(self, img: Image.Image, path: str) -> None:
        """Übernimmt ein bereits geladenes (PIL-)Bild als neues Projekt."""
        self._history.clear()
        self._project = self._single_layer_project(img)
        self._history.set_original(self._project)
        self._reset_transient_state()
        self._set_image_state()
        self._emit_history()
        self._emit_layers()
        self._viewport.fit_to_view()
        self.statusMsg.emit(tr(
            "canvas.opened", name=Path(path).name, w=img.width, h=img.height))
        self.imageLoaded.emit(str(Path(path).resolve()))

    def set_project(self, project: Project) -> None:
        """Übernimmt ein komplettes Projekt als neues Dokument.

        Projektbasierter, öffentlicher Gegenpart zu :meth:`apply_loaded_image`:
        setzt Historie/Original zurück, rendert das Komposit und passt die Ansicht
        ein. Genutzt vom Mehr-Ebenen-Pfad (Projekt öffnen/anlegen, #334/#335) und
        von Tests. Das Projekt wird **übernommen** (nicht kopiert); der Aufrufer
        gibt es danach aus der Hand.
        """
        self._history.clear()
        self._project = project
        self._history.set_original(project)
        self._reset_transient_state()
        self._set_image_state()
        self._emit_history()
        self._emit_layers()
        self._viewport.fit_to_view()

    def apply_edit(self, img: Image.Image, desc: str | None = None) -> None:
        """Wendet einen neuen Bildzustand der **aktiven Ebene** als Undo-fähige
        Bearbeitung an (gleiche Geometrie; größenändernde Geometrie läuft über
        :meth:`apply_geometry`)."""
        self._apply_pil(img, push=True, desc=desc)

    def _apply_pil(
        self,
        img: Image.Image,
        push: bool = True,
        desc: str | None = None,
    ) -> None:
        """Ersetzt das Bild der aktiven Ebene (Editierziel) durch *img*.

        Für eine Einzel-Ebene entspricht das exakt dem bisherigen Verhalten. Bei
        mehreren Ebenen bleibt nur die aktive Ebene betroffen. *img* hat in der
        Regel Canvas-Größe (Pixel-/Alpha-Edits, Spiegeln, Eckenrundung); eine
        abweichende Größe (nur einlagig zu erwarten) passt die Canvas-Größe an.
        """
        if self._project is None:
            return
        if push:
            self._history.push(self._project, desc or tr("history.desc.generic"))
            self._emit_history()
        active = self._project.active_layer()
        assert active is not None
        rgba = img if img.mode == "RGBA" else img.convert("RGBA")
        if rgba.size != self._project.size:
            self._project.width, self._project.height = rgba.size
        active.image = rgba
        self._set_image_state()

    def _apply_height_field(
        self,
        field: HeightField,
        *,
        push: bool = True,
        desc: str | None = None,
    ) -> None:
        """Ersetzt die kanonische Payload der aktiven HEIGHT-Ebene.

        Anders als :meth:`_apply_pil` führt dieser Pfad weder beim Lesen noch
        beim Schreiben über die abgeleitete 8-Bit-Ansicht. History und
        Canvas-Größenvalidierung bleiben identisch zum übrigen Modellpfad.
        """
        if self._project is None:
            return
        active = self._project.active_layer()
        if active is None or active.kind is not LayerKind.HEIGHT:
            raise HeightMapError("Aktive Ebene ist keine HEIGHT-Ebene")
        if push:
            self._history.push(self._project, desc or tr("history.desc.generic"))
            self._emit_history()
        self._project.set_layer_height_data(active.id, field)
        self._set_image_state()

    def apply_geometry(
        self,
        transform: Callable[[Image.Image], Image.Image],
        desc: str,
        *,
        height_transform: Callable[[HeightField], HeightField],
    ) -> None:
        """Wendet eine **größenändernde** Geometrie auf das **ganze** Projekt an.

        Drehen und Zuschnitt ändern die Canvas-Größe; um die Modell-Invariante
        (alle Ebenen in Canvas-Größe) zu wahren, wird *transform* einheitlich auf
        **jede** Ebene angewandt (Canvas-Drehung/-Zuschnitt). Für ein Projekt mit
        genau einer Ebene ist das exakt das bisherige Verhalten. Ein einziger
        Undo-Schritt erfasst den Gesamtzustand vor der Operation.
        """
        if self._project is None:
            return
        transformed: list[tuple[Layer, Image.Image | HeightField]] = []
        for layer in self._project.layers:
            if layer.kind is LayerKind.HEIGHT:
                field = layer.height_data
                assert field is not None
                transformed.append((layer, height_transform(field)))
            else:
                result = transform(layer.image)
                transformed.append(
                    (layer, result if result.mode == "RGBA" else result.convert("RGBA"))
                )
        if not transformed:
            return
        target_size = transformed[0][1].size
        if any(result.size != target_size for _layer, result in transformed):
            raise HeightMapError("Geometrie lieferte uneinheitliche Ebenengrößen")
        self._history.push(self._project, desc)
        self._emit_history()
        for layer, transformed_result in transformed:
            if isinstance(transformed_result, HeightField):
                layer.set_height_data(transformed_result)
            else:
                layer.image = transformed_result
        self._project.width, self._project.height = target_size
        self._set_image_state()

    def _render_export_image(self) -> Image.Image | None:
        """Das als normales Bild zu speichernde COLOR-Komposit (#363).

        Der Export ist bewusst unabhängig von der **aktiven** Ebene: HEIGHT-,
        GLOSS- und GENERIC-Ebenen sind Bearbeitungs-/Datenschichten und werden
        über ``.bgrproj`` beziehungsweise eigene Exportpfade persistiert. Der
        normale Bildexport schreibt ausschließlich das definierte
        :meth:`Project.composite_color`.

        Schnellpfad für die Single-Layer-Welt: genau eine sichtbare, voll
        deckende COLOR-Ebene wird **direkt** (ohne Alpha-Komposit) zurückgegeben.
        So bleiben RGB-Werte unter transparenten Pixeln erhalten;
        ``alpha_composite`` würde sie auf 0 setzen.
        """
        if self._project is None:
            return None
        layers = self._project.layers
        if (
            len(layers) == 1
            and layers[0].kind is LayerKind.COLOR
            and layers[0].visible
            and layers[0].opacity >= 1.0
        ):
            return layers[0].image
        return self._project.composite_color()

    def _render_preview_uncached(self) -> Image.Image | None:
        """Rendert die modusgesteuerte Vorschau einmalig aus dem Projektzustand.

        Fehlende, unsichtbare oder größenfremde Height-/Gloss-Rollen degradieren
        bewusst auf das COLOR-Komposit, statt eine leere, veraltete oder falsch
        dimensionierte Ansicht zu zeigen bzw. den Renderpfad mit einer Ausnahme
        abzubrechen (#404). Ein Daten-Layer mit canvas-fremder Pixelgröße tritt nur
        in anomalen/fremden Projektzuständen auf und wird – wie eine fehlende Rolle –
        in *jedem* Modus (auch im eigenständigen HEIGHT-/GLOSS-Modus) auf ``base``
        zurückgeführt. Der Gloss-Modus zeigt bei vorhandener Maske deren getönten
        Overlay allein; „kombiniert" legt Relief und optional Gloss in dieser
        Reihenfolge über das Farbmotiv.
        """
        if self._project is None:
            return None
        base = self._render_export_image()
        assert base is not None
        height = self._project.layer_by_role(LayerRole.HEIGHT_MAP)
        gloss = self._project.layer_by_role(LayerRole.GLOSS_MASK)
        # Eine transiente Bearbeitung einer HEIGHT-Ebene soll genau deren
        # temporäre Pixel zeigen, auch wenn die Ebene (noch) keine Rolle trägt.
        # Das betrifft nur den synchronen Override-Render und ändert keine Rolle.
        if self._preview_layer_override is not None:
            override = self._project.layer_by_id(self._preview_layer_override[0])
            if override.kind is LayerKind.HEIGHT:
                height = override
        # Der Augen-Schalter gilt auch für Datenebenen. Unsichtbare Rollen
        # verhalten sich wie fehlende Rollen und degradieren auf das Farbmotiv.
        if height is not None and not height.visible:
            height = None
        if gloss is not None and not gloss.visible:
            gloss = None
        # Größeninkompatible Datenebenen (anomaler/fremder Projektzustand) ebenso:
        # in jedem Modus wie eine fehlende Rolle behandeln, damit weder eine falsch
        # dimensionierte Ansicht (eigenständiger HEIGHT-/GLOSS-Modus) entsteht noch
        # ein compose_* mit Größen-Mismatch wirft (#404).
        if height is not None and height.image.size != base.size:
            height = None
        if gloss is not None and gloss.image.size != base.size:
            gloss = None

        if self._preview_mode is PreviewMode.COLOR:
            return base
        if self._preview_mode is PreviewMode.HEIGHT:
            return layer_to_gray_image(height.image) if height is not None else base
        if self._preview_mode is PreviewMode.GLOSS:
            if gloss is None or not self._gloss_visible:
                return base
            return gloss_overlay(gloss.image, intensity=1.0)

        rendered = base
        if height is not None and self._relief_strength > 0:
            # Hillshade direkt aus der kanonischen 16-Bit-Payload (#590):
            # feine Höhenverläufe unterhalb einer 8-Bit-Stufe werden im Relief
            # sichtbar. Nur während einer transienten Live-Vorschau (Override)
            # zählt die getauschte 8-Bit-Ansicht – sie trägt die Vorschaupixel
            # und ist als Anzeigeableitung die dokumentierte Ausnahme.
            overridden = (
                self._preview_layer_override is not None
                and self._preview_layer_override[0] == height.id
            )
            if height.height_data is not None and not overridden:
                shading_source = height.height_data
            else:
                shading_source = layer_to_height(height.image)
            shading = relief_shading(
                shading_source,
                azimuth=315.0,
                elevation=45.0,
                strength=1.0,
            )
            rendered = compose_relief(
                rendered, shading, strength=self._relief_strength / 100.0
            )
        if (
            self._preview_mode is PreviewMode.COMBINED
            and gloss is not None
            and self._gloss_visible
        ):
            overlay = gloss_overlay(gloss.image, intensity=1.0)
            rendered = compose_gloss(rendered, overlay, intensity=1.0)
        return rendered

    def _render_image(self) -> Image.Image | None:
        """Gibt die gecachte, explizite 2D-Vorschau zurück (#387).

        Der Schlüssel koppelt genau ein Cache-Bild an Content-Revision, Modus und
        beide Anzeigeparameter. Aktive Ebene, Undo/Redo und Pixel-/Layeränderungen
        laufen durch die bestehenden Revisionserhöhungen und invalidieren damit
        automatisch. Der getrennte Export nutzt weiterhin ausschließlich
        :meth:`_render_export_image` (#363-Vertrag).
        """
        if self._project is None:
            return None
        key = (
            self._content_revision,
            self._preview_mode,
            self._relief_strength,
            self._gloss_visible,
        )
        if self._preview_render_cache is not None:
            cached_key, cached_image = self._preview_render_cache
            if cached_key == key:
                return cached_image
        rendered = self._render_preview_uncached()
        if rendered is not None:
            self._preview_render_cache = (key, rendered)
        return rendered

    def _clear_transient_preview(self) -> None:
        """Entfernt Quell-Override und gerendertes Bild einer Live-Vorschau."""
        self._preview_layer_override = None
        self._preview = None

    def _render_transient_preview(self) -> Image.Image | None:
        """Rendert einen temporären Layer-Inhalt durch die aktuelle Pipeline.

        Das Projekt wird nur für die Dauer dieses synchronen Renderaufrufs
        substituiert. Revision, History, Dirty-State und Export sehen weiterhin
        ausschließlich das unveränderte Modell. Der normale Ein-Bild-Cache wird
        beidseitig verworfen, damit weder Modell- noch Vorschaupixel darin hängen
        bleiben.
        """
        if self._project is None or self._preview_layer_override is None:
            return None
        layer_id, preview_image = self._preview_layer_override
        layer = self._project.layer_by_id(layer_id)
        self._preview_render_cache = None
        # Nur die Anzeige-Sicht tauschen (#587): die kanonische Höhen-Payload
        # einer HEIGHT-Ebene bleibt unberührt – eine abgeleitete Vorschau kann
        # so nie in den 16-Bit-Zustand zurückgeschrieben werden (ADR #586).
        original = layer.swap_display_view(preview_image)
        try:
            return self._render_image()
        finally:
            layer.swap_display_view(original)
            self._preview_render_cache = None

    def _refresh_image(self) -> None:
        # Live-Bearbeitungen liefern temporäre Layerpixel in dieselbe explizite
        # Vorschau-Pipeline. Anzeigeparameter können sie dadurch sofort neu
        # rendern, ohne Projekt- oder Exportzustand zu mutieren (#397).
        if self._preview_layer_override is not None:
            self._preview = self._render_transient_preview()
            self._viewport.refresh_image(self._preview)
            return
        self._viewport.refresh_image(self._render_image())

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
        # Der O(1)-Zähler im Selection-Modell erkennt auch im Dirty-Pfad sofort,
        # wenn der Eraser das letzte Pixel entfernt hat, ohne bei jeder
        # Mausbewegung die vollständige Maske zu scannen (#251, #261).
        if not self._selection.has_selection:
            self._overlay_pixmap = None
            self._overlay_item.setPixmap(QPixmap())
            return
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
        h, w = mask.shape
        self._overlay_pixmap = mask_to_overlay(mask, w, h)
        self._overlay_item.setPixmap(self._overlay_pixmap)

    def _set_image_state(self) -> None:
        """Synchronisiert Caches/Anzeige mit der **aktiven Ebene** des Projekts.

        ``self._pil``/``self._arr`` spiegeln das Bild der aktiven Ebene (das
        Editierziel), angezeigt wird das Komposit. Kapselt den Anzeigezustand und
        die Content-Revision; die Undo-/Redo-Stapelpflege liegt in
        ``ProjectHistory``.

        Verwirft vor dem Wechsel geometrieabhängige Overlays (Crop/Lasso):
        Jeder sichtbare Bildzustandswechsel – Transformation, KI-Ergebnis,
        Undo/Redo/Undo-to, Original-Wiederherstellung, Crop-Bestätigung und
        Laden – kann die Bildgeometrie ändern. Ein altes Crop-Rechteck würde sonst
        beim nächsten ``confirm_crop()`` auf das neue Bild angewendet und – wenn
        es über die neuen Grenzen hinausragt – transparente Padding-Pixel
        erzeugen (#247).
        """
        self._discard_overlay_interactions()
        # Eine transiente Höhen-Vorschau (#348) gilt nur für den vorherigen
        # Zustand; jeder Bildzustandswechsel (Edit/Commit/Undo/Laden/Ebenenwechsel)
        # verwirft sie, bevor neu gerendert wird. Ein laufender Höhen-Malstrich
        # (#457) gehört ebenso zum vorherigen Zustand.
        self._height_stroke = None
        self._clear_transient_preview()
        active = self._project.active_layer() if self._project is not None else None
        self._pil = active.image if active is not None else None
        # Read-only-Sicht reicht: flood_fill/remove_selection/replace_selection
        # lesen nur und kopieren bei Bedarf selbst. Spart eine grosse
        # Heap-Allokation pro Bildwechsel.
        if self._pil is not None:
            self._arr = pil_to_numpy_readonly(self._pil)
            self._selection.reset(self._pil.width, self._pil.height)
        else:
            self._arr = None
            self._selection.reset(0, 0)
        self._content_revision += 1
        self._refresh_image()
        self._refresh_overlay()
        # Zoom-Kontrolle folgt dem Geladen-Zustand (#464): sichtbar, sobald ein
        # Bild da ist; ihre Position folgt der aktuellen Canvas-Größe.
        self._zoom_control.setVisible(self._pil is not None)
        if self._pil is not None:
            self._zoom_control.reposition()

    def _discard_overlay_interactions(self) -> None:
        """Verwirft geometrieabhängige Overlays (Crop, Lasso) vor einem
        sichtbaren Bildzustandswechsel.

        Entfernt ein Crop-Overlay und meldet das Modus-Ende **genau einmal**,
        wenn ein Overlay aktiv war – sonst bliebe ein ``cropModeChanged(True)``
        ohne passendes ``False`` hängen und die Crop-Leiste verschwände nicht.
        Bricht außerdem ein begonnenes Polygon-Lasso ab, damit alte Punkte und
        Vorschaulinien nicht auf die neue Bildgeometrie übertragen werden.

        Idempotent: Ist kein Overlay aktiv, passiert nichts und es wird kein
        ``cropModeChanged`` gefeuert. Läuft daher auf den Lade-/Restore-Pfaden
        (über ``_reset_transient_state``) und in ``_set_image_state`` doppelt
        gefahrlos.
        """
        self._crop.discard()
        self._lasso.cancel()

    def _reset_transient_state(self) -> None:
        """Verwirft schwebende Werkzeug-Interaktionen vor einem Inhaltswechsel.

        Räumt zunächst die geometrieabhängigen Overlays
        (``_discard_overlay_interactions``: Crop + Lasso) ab und setzt
        zusätzlich das ``_wand_busy``-Gate zurück: läuft beim Bildwechsel/
        Restore noch eine Zauberstab-Berechnung, bliebe das Gate sonst gesetzt
        und blockierte den Zauberstab auf dem neuen Bild, bis der alte Worker
        fertig ist. ``apply_wand_result`` ignoriert ein verspätetes Ergebnis
        dank des ``if not self._wand_busy``-Guards sauber; den alten Worker
        bricht ``MainWindow._load_image_async`` zusätzlich ab, damit er keine
        CPU mehr verbrennt.

        Wird beim Laden eines neuen Bildes und beim Wiederherstellen des
        Originals genutzt. Die reine Overlay-Bereinigung läuft inzwischen bei
        **jedem** Bildzustandswechsel über ``_set_image_state``; hier kommt nur
        der Wand-Gate-Reset hinzu, den ein bloßer ``_set_image_state``-Aufruf
        (Edit/Transform) bewusst nicht auslöst.
        """
        self._discard_overlay_interactions()
        self._wand_busy = False

    def _emit_history(self) -> None:
        """Sendet die aktuelle Verlaufsliste (neueste zuerst)."""
        self.historyChanged.emit(self._history.descriptions())

    def _layer_infos(self) -> list[LayerInfo]:
        """Aktuelle Ebenen als Anzeigedaten – **oberste zuerst** (Panel-Reihenfolge)."""
        if self._project is None:
            return []
        active = self._project.active_layer_id
        return [
            LayerInfo(
                id=layer.id,
                name=layer.name,
                kind=layer.kind,
                visible=layer.visible,
                opacity=layer.opacity,
                locked=layer.locked,
                role=layer.role,
                active=(layer.id == active),
            )
            for layer in reversed(self._project.layers)
        ]

    def _emit_layers(self) -> None:
        """Sendet die aktuelle Ebenenliste an das Ebenen-Panel."""
        self.layersChanged.emit(self._layer_infos())

    def resync_panels(self) -> None:
        """Re-emittiert Ebenen- und Vorschauzustand (z. B. nach Panel-Neuaufbau, #428)."""
        self._emit_layers()
        self.previewSettingsChanged.emit(
            self._preview_mode, self._relief_strength, self._gloss_visible
        )

    # ── Ebenen-Operationen (Panel-getrieben, undo-fähig) ─────────────────
    def _push_layers(self, desc: str) -> None:
        """Erfasst den Projektzustand vor einer Ebenen-Operation für Undo."""
        assert self._project is not None
        self._history.push(self._project, desc)

    def _commit_active_change(self) -> None:
        """Abschluss einer Operation, die die **aktive Ebene wechselt**.

        Resynchronisiert Caches/Auswahl auf die neue aktive Ebene
        (``_set_image_state`` setzt die Auswahl zurück – passend bei
        Ebenenwechsel) und benachrichtigt Verlauf + Panel.
        """
        self._set_image_state()
        self._emit_history()
        self._emit_layers()

    def _commit_state_change(self) -> None:
        """Abschluss einer Operation, die nur Komposit/Metadaten ändert.

        Die aktive Ebene (und damit ``_pil``/``_arr``/Auswahl) bleibt erhalten;
        nur das Komposit wird neu gerendert. Verlauf + Panel werden aktualisiert.
        """
        self._content_revision += 1
        self._refresh_image()
        self._emit_history()
        self._emit_layers()

    @_requires_image
    def add_layer(self) -> None:
        """Legt eine neue, transparente COLOR-Ebene oben an und aktiviert sie."""
        assert self._project is not None
        self._push_layers(tr("history.desc.layer_added"))
        blank = Image.new("RGBA", self._project.size, (0, 0, 0, 0))
        self._project.create_layer(
            blank, name=tr("layers.new_name", n=len(self._project) + 1),
            kind=LayerKind.COLOR)
        self._commit_active_change()
        self.statusMsg.emit(tr("canvas.layer_added"))

    @_requires_image
    def delete_active_layer(self) -> None:
        """Löscht die aktive Ebene; die letzte Ebene bleibt erhalten."""
        assert self._project is not None
        active = self._project.active_layer_id
        if active is None:
            return
        if len(self._project) <= 1:
            self.statusMsg.emit(tr("canvas.cannot_delete_last"))
            return
        self._push_layers(tr("history.desc.layer_removed"))
        self._project.remove_layer(active)
        self._commit_active_change()
        self.statusMsg.emit(tr("canvas.layer_removed"))

    @_requires_image
    def duplicate_active_layer(self) -> None:
        """Dupliziert die aktive Ebene (Kopie darüber, wird aktiv)."""
        assert self._project is not None
        active = self._project.active_layer_id
        if active is None:
            return
        self._push_layers(tr("history.desc.layer_duplicated"))
        self._project.duplicate_layer(active)
        self._commit_active_change()
        self.statusMsg.emit(tr("canvas.layer_duplicated"))

    @_requires_image
    def move_active_layer(self, *, up: bool) -> None:
        """Verschiebt die aktive Ebene im Stapel (``up`` = nach oben)."""
        assert self._project is not None
        active = self._project.active_layer_id
        if active is None:
            return
        idx = self._project.index_of(active)
        new_idx = idx + 1 if up else idx - 1
        if not 0 <= new_idx < len(self._project):
            return
        self._push_layers(tr("history.desc.layer_reordered"))
        self._project.move_layer(active, new_idx)
        self._commit_state_change()

    @_requires_image
    def rename_active_layer(self, name: str) -> None:
        """Benennt die aktive Ebene um (leerer Name wird ignoriert)."""
        assert self._project is not None
        active = self._project.active_layer_id
        if active is None or not name.strip():
            return
        self._push_layers(tr("history.desc.layer_renamed"))
        self._project.rename_layer(active, name.strip())
        self._commit_state_change()

    @_requires_image
    def set_active_layer(self, layer_id: str) -> None:
        """Setzt die aktive (Editier-)Ebene."""
        assert self._project is not None
        if self._project.active_layer_id == layer_id:
            return
        self._push_layers(tr("history.desc.layer_active"))
        self._project.set_active(layer_id)
        self._commit_active_change()

    @_requires_image
    def set_layer_visible(self, layer_id: str, visible: bool) -> None:
        """Schaltet die Sichtbarkeit einer Ebene um."""
        assert self._project is not None
        if self._project.layer_by_id(layer_id).visible == visible:
            return
        self._push_layers(tr("history.desc.layer_visibility"))
        self._project.set_visible(layer_id, visible)
        self._commit_state_change()

    @_requires_image
    def set_layer_opacity(self, layer_id: str, opacity: float) -> None:
        """Setzt die Opazität einer Ebene (0.0–1.0)."""
        assert self._project is not None
        if self._project.layer_by_id(layer_id).opacity == opacity:
            return
        self._push_layers(tr("history.desc.layer_opacity"))
        self._project.set_opacity(layer_id, opacity)
        self._commit_state_change()

    @_requires_image
    def set_active_layer_role(self, role: LayerRole | None) -> None:
        """Weist der aktiven Ebene eine Rolle zu bzw. entfernt sie.

        Eine mit dem Ebenen-Typ unverträgliche Rolle (etwa ``HEIGHT_MAP`` auf
        einer COLOR-Ebene, #364) wird *vor* jeder Zustandsänderung mit einer
        Statusmeldung abgewiesen – der Verlauf bleibt unangetastet. Die UI
        verhindert das bereits, der Guard sichert den Vertrag zusätzlich ab.
        """
        assert self._project is not None
        active = self._project.active_layer_id
        if active is None:
            return
        layer = self._project.layer_by_id(active)
        if layer.role == role:
            return
        if role is not None and not role_allowed_for_kind(role, layer.kind):
            self.statusMsg.emit(tr("canvas.role_incompatible"))
            return
        self._push_layers(tr("history.desc.layer_role"))
        if role is None:
            self._project.clear_role(active)
        else:
            self._project.assign_role(active, role)
        self._commit_state_change()

    # ── Höhenkarten: Erzeugung & Import (#346) ──────────────────────────
    def _add_height_layer(self, field: HeightField, desc: str) -> None:
        """Fügt *field* als neue, aktive HEIGHT-Ebene mit Rolle HEIGHT_MAP ein.

        Erfasst den Projektzustand für Undo und legt die Ebene **direkt aus
        der kanonischen 16-Bit-Payload** an (#589) – ohne Umweg über die
        8-Bit-Ansicht (``create_layer`` mit ``height_data`` → oben, aktiv).
        Die projektweit eindeutige Rolle wird via ``assign_role`` zugewiesen –
        sie wird damit von einer etwaigen bestehenden Höhenkarte übertragen,
        statt an der Eindeutigkeit zu scheitern. Anzeige wechselt durch die
        neue aktive HEIGHT-Ebene in die Höhensicht (#345);
        ``_commit_active_change`` resynchronisiert Caches, Verlauf und Panel.
        """
        assert self._project is not None
        self._push_layers(desc)
        layer = self._project.create_layer(
            name=tr("layers.height_name"), kind=LayerKind.HEIGHT,
            height_data=field)
        self._project.assign_role(layer.id, LayerRole.HEIGHT_MAP)
        self._commit_active_change()

    @_requires_image
    def generate_height_map(
        self,
        *,
        weights: tuple[float, float, float] = LUMA_WEIGHTS_REC601,
        black: int = 0,
        white: int = HEIGHT_MAX_8BIT,
        gamma: float = 1.0,
        invert: bool = False,
    ) -> None:
        """Erzeugt algorithmisch eine HEIGHT-Ebene aus dem Farbbild (#346).

        Quelle ist die **aktive** Ebene, sofern sie COLOR ist, sonst das
        Farb-Komposit (``composite_color``). Kanalgewichtung, Tonwert-Kennlinie
        (``black``/``white``, bezogen auf die 8-Bit-Quell-Luminanz), Gamma und
        Invertieren laufen in ``height_map.generate_from_image`` – seit #589
        skaliert die float64-Pipeline direkt auf den kanonischen
        16-Bit-Wertebereich (keine 8-Bit-Zwischenquantisierung). Die neue
        Ebene wird aktiv (Höhensicht via #345) und ist undo-/redobar.
        """
        assert self._project is not None
        active = self._project.active_layer()
        if active is not None and active.kind is LayerKind.COLOR:
            source = active.image
        else:
            source = self._project.composite_color()
        field = generate_from_image(
            source, weights=weights, black=black, white=white,
            gamma=gamma, invert=invert, max_value=HEIGHT_MAX_16BIT)
        self._add_height_layer(field, tr("history.desc.height_generated"))
        self.statusMsg.emit(tr("canvas.height_generated"))

    @_requires_image
    def import_height_map(self, path: str) -> None:
        """Importiert eine Höhenkarten-Datei als HEIGHT-Ebene (#346/#589).

        Validiertes Laden über ``open_validated_height_image`` (Format-
        Whitelist, Dateigrößen- und Megapixel-Schutz) **ohne** RGBA-Zwang:
        16-Bit-Graustufen (PNG/TIFF) behalten nativ alle 65536 Stufen,
        8-Bit-/Farbquellen laufen über die dokumentierte Luminanz-Regel
        direkt in den 16-Bit-Vertrag (``image_to_height_field``). Eine von
        der Canvas-Größe abweichende Datei wird präzisionserhaltend über
        ``resize_height_field`` skaliert (Modell-Invariante). Fehler –
        auch nicht unterstützte Modi wie Float-Bilder – erscheinen als
        übersetzte Statusmeldung, ohne einen Teil-Layer anzulegen.
        Undo-/redobar.
        """
        assert self._project is not None
        img, err = open_validated_height_image(path)
        if err is not None:
            self.statusMsg.emit(err)
            return
        assert img is not None
        try:
            field = image_to_height_field(img)
            if field.size != self._project.size:
                field = resize_height_field(field, *self._project.size)
        except UnsupportedHeightSourceError as exc:
            self.statusMsg.emit(
                tr("status.height_source_unsupported", mode=exc.mode))
            return
        except HeightMapError as exc:
            logger.warning("Höhen-Import fehlgeschlagen: %s", exc)
            self.statusMsg.emit(tr("status.height_import_failed"))
            return
        self._add_height_layer(field, tr("history.desc.height_imported"))
        # Quell-Bittiefe benennen (#590): native 16-Bit-Quelle vs. Ableitung
        # aus einer 8-Bit-Basis (Luminanz-Regel, ×257-äquivalent).
        if is_native_16bit_source(img):
            self.statusMsg.emit(
                tr("canvas.height_imported_16bit", name=Path(path).name))
        else:
            self.statusMsg.emit(tr("canvas.height_imported", name=Path(path).name))

    # ── Höhen-Editor: Aufhellen/Abdunkeln/Setzen/Invertieren (#347) ─────
    def _height_edit_context(self) -> tuple[HeightField, np.ndarray | None] | None:
        """Liefert (Höhenfeld der aktiven HEIGHT-Ebene, Auswahlmaske|None).

        Gibt ``None`` zurück und meldet, wenn die aktive Ebene keine HEIGHT-Ebene
        ist – so wirken die Höhenwerkzeuge ausschließlich auf Höhenebenen und das
        COLOR-Editing bleibt unangetastet. Die Maske ist die **vorhandene**
        Auswahl (begrenzt die Wirkung), sonst ``None`` (global).
        """
        assert self._project is not None
        active = self._project.active_layer()
        if active is None or active.kind is not LayerKind.HEIGHT:
            self.statusMsg.emit(tr("canvas.not_height_layer"))
            return None
        mask = self._selection.mask if self._selection.has_selection else None
        field = active.height_data
        assert field is not None
        return field, mask

    def _run_height_edit(self, new_field: HeightField, desc: str, status: str) -> None:
        """Schreibt ein bearbeitetes Höhenfeld undo-fähig in die aktive Ebene."""
        self._apply_height_field(new_field, desc=desc)
        self.statusMsg.emit(status)

    @_requires_image
    def lighten_active_height(self, amount: int = _DEFAULT_HEIGHT_STEP) -> None:
        """Hellt die aktive HEIGHT-Ebene auf (Auswahl bzw. global), undo-fähig."""
        ctx = self._height_edit_context()
        if ctx is None:
            return
        field, mask = ctx
        self._run_height_edit(
            adjust_height(field, scale_8bit_height_value(amount, field), mask=mask),
            tr("history.desc.height_lighten"), tr("canvas.height_lightened"))

    @_requires_image
    def darken_active_height(self, amount: int = _DEFAULT_HEIGHT_STEP) -> None:
        """Dunkelt die aktive HEIGHT-Ebene ab (Auswahl bzw. global), undo-fähig."""
        ctx = self._height_edit_context()
        if ctx is None:
            return
        field, mask = ctx
        self._run_height_edit(
            adjust_height(field, -scale_8bit_height_value(amount, field), mask=mask),
            tr("history.desc.height_darken"), tr("canvas.height_darkened"))

    @_requires_image
    def set_active_height(self, value: int) -> None:
        """Setzt die aktive HEIGHT-Ebene auf einen Festwert (Auswahl bzw. global)."""
        ctx = self._height_edit_context()
        if ctx is None:
            return
        field, mask = ctx
        self._run_height_edit(
            set_height(field, scale_8bit_height_value(value, field), mask=mask),
            tr("history.desc.height_set"), tr("canvas.height_set"))

    @_requires_image
    def invert_active_height(self) -> None:
        """Invertiert die aktive HEIGHT-Ebene (Auswahl bzw. global), undo-fähig."""
        ctx = self._height_edit_context()
        if ctx is None:
            return
        field, mask = ctx
        self._run_height_edit(
            invert_height(field, mask=mask),
            tr("history.desc.height_invert"), tr("canvas.height_inverted"))

    # ── Malende Höhen-Werkzeuge: Aufhellen/Abdunkeln je Strich (#457) ───
    def _start_height_stroke(self, x: int, y: int) -> None:
        """Beginnt einen Höhen-Malstrich auf der aktiven HEIGHT-Ebene.

        Auf COLOR-/Daten-Ebenen wirkungslos (Meldung statt Pixeländerung –
        der Kind↔Rollen-Vertrag #364 bleibt unangetastet); die Rail-Buttons
        sind ohne aktive HEIGHT-Ebene ohnehin deaktiviert.
        """
        assert self._project is not None
        active = self._project.active_layer()
        if active is None or active.kind is not LayerKind.HEIGHT:
            self.statusMsg.emit(tr("canvas.not_height_layer"))
            return
        field = active.height_data
        assert field is not None
        ui_amount = (
            _DEFAULT_HEIGHT_STEP
            if self._tool == TOOL_HEIGHT_LIGHTEN else -_DEFAULT_HEIGHT_STEP
        )
        amount = (
            scale_8bit_height_value(ui_amount, field)
            if ui_amount >= 0
            else -scale_8bit_height_value(-ui_amount, field)
        )
        self._height_stroke = _HeightStroke(
            layer_id=active.id,
            values=field.values.copy(),
            coverage=field.coverage,
            max_value=field.max_value,
            touched=np.zeros(field.values.shape, dtype=bool),
            preview_image=active.image.copy(),
            amount=amount,
        )
        self._drawing = True
        self._extend_height_stroke(x, y)

    def _extend_height_stroke(self, cx: int, cy: int) -> None:
        """Stempelt den Pinselkreis an (cx, cy) in den laufenden Strich.

        Jedes Pixel wird pro Strich genau **einmal** um ``amount`` verschoben
        (geklemmt auf ``0..max_value`` – ``adjust_height``-Semantik); die
        Anzeige läuft transient über die explizite Vorschau-Pipeline (#397),
        das Modell bleibt bis zum Loslassen unverändert.
        """
        stroke = self._height_stroke
        if stroke is None:
            return
        h, w = stroke.values.shape
        r = self._brush_r
        y0, y1 = max(0, cy - r), min(h, cy + r + 1)
        x0, x1 = max(0, cx - r), min(w, cx + r + 1)
        if y0 >= y1 or x0 >= x1:
            return
        yy, xx = np.ogrid[y0:y1, x0:x1]
        circle = (yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2
        touched_region = stroke.touched[y0:y1, x0:x1]
        fresh = circle & ~touched_region
        if not fresh.any():
            return
        region = stroke.values[y0:y1, x0:x1]
        adjusted = np.clip(
            region.astype(np.int32) + stroke.amount, 0, stroke.max_value)
        region[fresh] = adjusted[fresh].astype(np.uint16)
        touched_region |= circle
        dirty = HeightField(
            region.copy(), stroke.coverage[y0:y1, x0:x1].copy(),
            stroke.max_value)
        stroke.preview_image.paste(height_to_layer(dirty), (x0, y0))
        self._preview_layer_override = (stroke.layer_id, stroke.preview_image)
        self._refresh_image()

    @staticmethod
    def _stroke_field(stroke: _HeightStroke) -> HeightField:
        """Baut ein eigenständiges Höhenfeld aus dem Strich-Arbeitszustand."""
        return HeightField(
            stroke.values.copy(), stroke.coverage.copy(), stroke.max_value)

    def _finish_height_stroke(self) -> None:
        """Committet den Strich als genau **einen** Undo-Schritt (#457)."""
        stroke = self._height_stroke
        if stroke is None:
            return
        self._height_stroke = None
        self._clear_transient_preview()
        if not stroke.touched.any():
            self._refresh_image()
            return
        if stroke.amount > 0:
            desc, status = (
                tr("history.desc.height_lighten"), tr("canvas.height_lightened"))
        else:
            desc, status = (
                tr("history.desc.height_darken"), tr("canvas.height_darkened"))
        # Das Modell ist noch unverändert (Strich lief nur als Vorschau);
        # _apply_pil pusht genau diesen Vorzustand → ein History-Eintrag.
        self._run_height_edit(self._stroke_field(stroke), desc, status)

    def _abort_height_stroke(self) -> None:
        """Verwirft einen laufenden Strich ohne Commit (Werkzeug-Gate, #457)."""
        if self._height_stroke is None:
            return
        self._height_stroke = None
        self._clear_transient_preview()
        self._refresh_image()

    # ── Höhen-Optimierung mit Live-Vorschau (#348) ──────────────────────
    @_requires_image
    def preview_height_op(self, op: Callable[[HeightField], HeightField]) -> None:
        """Zeigt das Ergebnis von *op* auf der aktiven HEIGHT-Ebene als Vorschau.

        ``op`` ist eine reine ``HeightField → HeightField``-Funktion (z. B. eine
        an ihre Parameter gebundene ``height_ops``-Operation). Die Ebene bleibt
        **unverändert** – nur die Anzeige zeigt das Resultat. Wiederholtes Aufrufen
        aktualisiert die Vorschau live (Reglerbewegung im Höhen-Tab #349).
        """
        ctx = self._height_edit_context()
        if ctx is None:
            return
        field, _mask = ctx
        try:
            result = op(field)
        except HeightMapError:
            # Ungültige Parameter (z. B. black >= white) während des Reglerns:
            # Vorschau still überspringen statt den Nutzer mit Meldungen zu
            # fluten; der Commit (apply_height_op) meldet den Fehler dagegen.
            return
        assert self._project is not None
        active = self._project.active_layer()
        assert active is not None
        self._preview_layer_override = (active.id, height_to_layer(result))
        self._refresh_image()

    def cancel_height_preview(self) -> None:
        """Verwirft eine aktive Höhen-Vorschau und zeigt wieder den Modellzustand."""
        if self._preview_layer_override is None:
            return
        self._clear_transient_preview()
        self._refresh_image()

    @_requires_image
    def apply_height_op(
        self,
        op: Callable[[HeightField], HeightField],
        *,
        desc: str | None = None,
        status: str | None = None,
    ) -> None:
        """Wendet *op* undo-fähig auf die aktive HEIGHT-Ebene an (Commit der Vorschau).

        Berechnet das Ergebnis aus dem **aktuellen** Ebenenzustand (deterministisch
        identisch zur Vorschau) und schreibt es wie eine normale Bearbeitung
        zurück. ``desc``/``status`` erlauben der UI (#349) operationsspezifische
        Texte; ohne Angabe greifen generische Höhen-Optimierungs-Meldungen.
        """
        ctx = self._height_edit_context()
        if ctx is None:
            return
        field, _mask = ctx
        try:
            result = op(field)
        except HeightMapError as e:
            self._clear_transient_preview()
            self._refresh_image()
            self.statusMsg.emit(tr("canvas.height_op_error", error=e))
            return
        self._clear_transient_preview()
        self._run_height_edit(
            result,
            desc if desc is not None else tr("history.desc.height_optimized"),
            status if status is not None else tr("canvas.height_optimized"))

    # ── Farbkorrektur mit Live-Vorschau (#360) ──────────────────────────
    def _active_color_layer(self) -> Layer | None:
        """Aktive Ebene, sofern sie eine COLOR-Ebene ist – sonst ``None``.

        Farbkorrektur wirkt ausschließlich auf COLOR-Ebenen; auf Daten-Ebenen
        (HEIGHT/GLOSS/GENERIC) liefert der Helfer ``None``, ohne zu melden – der
        Aufrufer entscheidet, ob das stille Überspringen (Vorschau) oder eine
        Statusmeldung (Commit) angebracht ist.
        """
        if self._project is None:
            return None
        active = self._project.active_layer()
        if active is None or active.kind is not LayerKind.COLOR:
            return None
        return active

    @_requires_image
    def preview_color_op(self, op: Callable[[Image.Image], Image.Image]) -> None:
        """Zeigt *op* auf der aktiven COLOR-Ebene als transiente Vorschau.

        ``op`` ist eine reine ``Image → Image``-Funktion (z. B. eine an ihre
        Reglerwerte gebundene ``color_ops.adjust_color``-Closure). Die Ebene bleibt
        **unverändert**; gerendert wird das Komposit, als hätte die aktive Ebene
        bereits das Ergebnis – so stimmt die Vorschau auch bei mehreren Ebenen mit
        dem späteren Commit überein. Ohne aktive COLOR-Ebene passiert nichts
        (stilles Überspringen, kein Meldungs-Spam beim Reglern).
        """
        active = self._active_color_layer()
        if active is None:
            return
        self._preview_layer_override = (active.id, op(active.image))
        self._refresh_image()

    def cancel_color_preview(self) -> None:
        """Verwirft eine aktive Farb-Vorschau und zeigt wieder den Modellzustand."""
        if self._preview_layer_override is None:
            return
        self._clear_transient_preview()
        self._refresh_image()

    @_requires_image
    def apply_color_op(
        self,
        op: Callable[[Image.Image], Image.Image],
        *,
        desc: str | None = None,
        status: str | None = None,
    ) -> None:
        """Wendet *op* undo-fähig auf die aktive COLOR-Ebene an (Commit der Vorschau).

        Berechnet das Ergebnis aus dem **aktuellen** Ebenenzustand (deterministisch
        identisch zur Vorschau) und schreibt es wie eine normale Bearbeitung
        zurück (genau **ein** Undo-Schritt über ``_apply_pil``). Ohne aktive
        COLOR-Ebene wird gemeldet statt still nichts zu tun.
        """
        active = self._active_color_layer()
        if active is None:
            self._clear_transient_preview()
            self._refresh_image()
            self.statusMsg.emit(tr("canvas.not_color_layer"))
            return
        result = op(active.image)
        self._clear_transient_preview()
        self._apply_pil(
            result,
            desc=desc if desc is not None else tr("history.desc.color_adjusted"))
        self.statusMsg.emit(
            status if status is not None else tr("canvas.color_adjusted"))

    def _adopt_project(self, project: Project) -> None:
        """Übernimmt einen aus der Historie rekonstruierten Projektzustand."""
        self._project = project
        self._set_image_state()
        self._emit_layers()

    def _apply_history_step(
        self,
        result: tuple[Project, str] | None,
        empty_message: str,
        status_template: str,
    ) -> None:
        if result is None:
            self.statusMsg.emit(empty_message)
            return
        project, desc = result
        self._adopt_project(project)
        self._emit_history()
        self.statusMsg.emit(status_template.format(desc=desc))

    # ── Undo / Original ──────────────────────────────────────

    def undo(self) -> None:
        if self._crop.active:
            self.cancel_crop()
            return
        self._apply_history_step(
            self._history.undo(self._project),
            tr("canvas.undo_none"),
            tr("canvas.undo_done"),
        )

    def redo(self) -> None:
        if self._crop.active:
            return
        self._apply_history_step(
            self._history.redo(self._project),
            tr("canvas.redo_none"),
            tr("canvas.redo_done"),
        )

    def undo_to(self, steps: int) -> None:
        if self._crop.active:
            self.cancel_crop()
            return
        result = self._history.undo_to(self._project, steps)
        if result is None:
            return
        project, desc, actual = result
        self._adopt_project(project)
        self._emit_history()
        self.statusMsg.emit(tr("canvas.undo_to", steps=actual, desc=desc))

    def restore_original(self) -> None:
        restored = self._history.restore(
            self._project,
            tr("history.desc.original_restored"),
        )
        if restored is None:
            return
        self._reset_transient_state()
        self._adopt_project(restored)
        self._emit_history()
        self.statusMsg.emit(tr("canvas.original_restored"))

    def cancel_active_interaction(self) -> bool:
        """Bricht die höchstpriorisierte aktive Canvas-Interaktion ab.

        Crop hat Vorrang vor einem begonnenen Polygon-Lasso. ``False`` zeigt
        dem Aufrufer, dass keine Interaktion aktiv war und Escape stattdessen
        die Auswahl aufheben darf.
        """
        if self._crop.active:
            self._crop.cancel()
            return True
        if self._lasso.has_points:
            self._lasso_cancel()
            self.statusMsg.emit(tr("canvas.lasso_cancelled"))
            return True
        return False

    @_requires_image
    def clear_selection(self) -> None:
        self._selection.clear()
        self._refresh_overlay()
        self.statusMsg.emit(tr("canvas.selection_cleared"))

    @_requires_image
    def invert_selection(self) -> None:
        pixels = self._selection.invert()
        self._refresh_overlay()
        self.statusMsg.emit(tr("canvas.selection_inverted", pixels=pixels))

    def _morphology(self, radius: int, kind: Literal["expand", "shrink"]) -> None:
        if radius <= 0:
            return
        pixels = self._selection.morphology(radius, kind)
        self._refresh_overlay()
        if kind == "expand":
            self.statusMsg.emit(
                tr("canvas.selection_expanded", radius=radius, pixels=pixels))
        else:
            self.statusMsg.emit(
                tr("canvas.selection_shrunk", radius=radius, pixels=pixels))

    @_requires_image
    def expand_selection(self, radius: int) -> None:
        self._morphology(radius, "expand")

    @_requires_image
    def shrink_selection(self, radius: int) -> None:
        self._morphology(radius, "shrink")

    @_requires_image
    def feather_active_edges(self, radius: int) -> None:
        """Glättet die Alphakante der aktiven Ebene (Feinschliff, #361).

        Weichzeichnet **nur den Alphakanal** der aktiven Ebene gaußsch (RGB bleibt
        erhalten) – der Politurschritt nach KI- oder manueller Freistellung. Eine
        vorhandene Auswahl begrenzt die Wirkung (sonst global); der Schritt ist
        über ``_apply_pil`` undo-/redobar. ``radius <= 0`` ist ein No-op mit
        Hinweis.
        """
        if radius <= 0:
            self.statusMsg.emit(tr("canvas.radius_positive"))
            return
        assert self._pil is not None  # @_requires_image garantiert das
        mask = self._selection.mask if self._selection.has_selection else None
        result = feather_alpha(self._pil, radius, mask=mask)
        self._apply_pil(result, desc=tr("history.desc.feathered", radius=radius))
        self.statusMsg.emit(tr("canvas.feathered", radius=radius))

    # ── Tool-Einstellungen ───────────────────────────────────

    def set_tool(self, tool: str) -> None:
        if self._tool == TOOL_LASSO and tool != TOOL_LASSO:
            self._lasso_cancel()
        self._tool = tool
        self._apply_tool_cursor()
        if tool not in BRUSH_TOOLS:
            self._brush_preview.setVisible(False)

    def _apply_tool_cursor(self) -> None:
        """Setzt den Cursor des aktiven Werkzeugs; Pinsel-artige zoom-bewusst (#509).

        Pinsel/Radiergummi/Höhen-Pinsel (#457) zeigen den Pinseldurchmesser in
        **Bildschirm**-Pixeln: Bildpixel (``_brush_r * 2``) × View-Skalierung –
        damit deckt sich der Cursor mit der tatsächlich bemalten Fläche.
        Oberhalb von ``BRUSH_CURSOR_MAX_SCREEN_PX`` übernimmt ein neutrales
        Fadenkreuz; die Größe zeigt dann allein die Vorschau-Ellipse.
        """
        tool = self._tool
        if tool == TOOL_WAND:
            self.setCursor(make_wand_cursor())
        elif tool in BRUSH_TOOLS:
            d = round(self._brush_r * 2 * self.transform().m11())
            if d > BRUSH_CURSOR_MAX_SCREEN_PX:
                self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
            elif tool == TOOL_ERASER:
                self.setCursor(make_eraser_cursor(d))
            else:
                self.setCursor(make_brush_cursor(d))
        elif tool == TOOL_LASSO:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        elif tool == TOOL_MOVE:
            # Verschieben/Zoom (#456): offene Hand als Ruhe-Cursor; während des
            # Ziehens setzt der Pan-Helfer die geschlossene Hand.
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def _on_zoom_changed(self, _pct: float) -> None:
        """Zoomwechsel (#509): aktiver Pinsel-Cursor folgt der Bildschirmgröße."""
        if self._tool in BRUSH_TOOLS:
            self._apply_tool_cursor()

    def set_tolerance(self, v: int) -> None:
        self._tolerance = v

    def set_brush_size(self, v: int) -> None:
        self._brush_r = max(1, v // 2)
        # Cursor sofort aktualisieren
        if self._tool in BRUSH_TOOLS:
            self._apply_tool_cursor()

    def _update_brush_preview(self, sp: QPointF) -> None:
        """Aktualisiert Position/Sichtbarkeit des Pinsel-Vorschau-Kreises."""
        if self._tool not in BRUSH_TOOLS or self._pil is None:
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
                desc=tr("history.desc.bg_removed"),
            )
            self.statusMsg.emit(tr("canvas.bg_removed"))
        except (OSError, ValueError, UnidentifiedImageError) as e:
            # Bewusst eng gefasst: erwartete Bild-/IO-Probleme landen als
            # Statusmeldung, echte Bugs (AttributeError, IndexError, …)
            # propagieren stattdessen sichtbar nach oben.
            logger.exception("Fehler beim Entfernen")
            self.statusMsg.emit(tr("canvas.remove_error", error=e))

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
                desc=tr("history.desc.color_replaced", color=color.name()),
            )
            self.statusMsg.emit(tr("canvas.bg_replaced", color=color.name()))
        except (OSError, ValueError, UnidentifiedImageError) as e:
            logger.exception("Fehler beim Ersetzen")
            self.statusMsg.emit(tr("canvas.replace_error", error=e))

    def apply_ai_result(self, img: Image.Image) -> None:
        self._apply_pil(img, desc=tr("history.desc.ai_bg"))
        self.statusMsg.emit(tr("canvas.ai_done"))

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
        self.statusMsg.emit(tr("canvas.selection_pixels", pixels=pixels))

    def cancel_pending_wand(self, msg: str) -> None:
        """Bricht eine laufende Wand-Berechnung im Fehlerfall ab."""
        if not self._wand_busy:
            return
        self._wand_busy = False
        self.statusMsg.emit(tr("canvas.selection_error", msg=msg))

    def reset_pending_wand(self) -> None:
        """Gibt das ``_wand_busy``-Gate ohne Statusmeldung frei (stiller Abbruch).

        Beim Bildwechsel kann der Flood-Fill-Worker abgebrochen werden, ohne
        ``finished`` oder ``error`` zu emittieren. Diese Methode hält den
        Canvas in diesem Fall bedienbar und zeigt bewusst keine
        „Auswahl-Fehler"-Meldung.
        """
        self._wand_busy = False

    def _export_dpi(self) -> tuple[float, float] | None:
        """Projekt-DPI für die Metadaten-Einbettung beim Speichern (#378).

        Liefert die aus physischer Größe + Pixelgröße abgeleitete Auflösung des
        Projekts oder ``None``, wenn keine physische Größe gesetzt ist. Ein
        (defensiv) korrupter Metadatenwert blockiert das Speichern nicht – die
        Datei wird dann ohne DPI geschrieben (bisheriges Verhalten).
        """
        if self._project is None:
            return None
        try:
            return self._project.dpi
        except UnitsError:
            return None

    def save_image(self, path: str) -> bool:
        """Speichert das aktuelle Komposit; gibt ``True`` bei Erfolg zurück.

        Gespeichert wird unabhängig von der aktiven Bearbeitungsebene das
        COLOR-Komposit (``_render_export_image``); bei genau einer Ebene bleibt
        der Export bitgenau wie bisher. E/A-Fehler (nicht beschreibbarer Pfad,
        voller Datenträger, unbekanntes Format …) werden protokolliert und als
        Statusmeldung gemeldet, statt unbehandelt zu propagieren – konsistent zu
        ``apply_remove``/``apply_replace``. Der Rückgabewert erlaubt dem Aufrufer,
        einen fehlgeschlagenen Pfad nicht als Quick-Save-Ziel zu merken.
        """
        export = self._render_export_image()
        if export is None:
            self.statusMsg.emit(SM.KEIN_BILD_ZUM_SPEICHERN)
            return False
        try:
            save_image_file(export, path, dpi=self._export_dpi())
        except Exception as e:
            logger.exception("Speichern fehlgeschlagen: %s", path)
            self.statusMsg.emit(tr("canvas.save_failed", error=e))
            return False
        self.statusMsg.emit(tr("canvas.saved", name=Path(path).name))
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

    def set_tools_enabled(self, enabled: bool) -> None:
        """Schaltet die Werkzeug-Interaktion (Klick/Zeichnen) frei oder ab.

        Beim Abschalten wird eine begonnene Interaktion (Crop/Lasso) verworfen,
        damit kein halbfertiger Zustand hängen bleibt. Pan/Zoom sind nicht
        betroffen. Wird vom MainWindow schrittabhängig gesetzt (PR #423-Review).
        """
        self._tools_enabled = enabled
        if not enabled:
            self._drawing = False
            self._abort_height_stroke()
            self.cancel_active_interaction()

    def _handle_tool_press(
        self,
        x: int,
        y: int,
        mods: Qt.KeyboardModifier,
    ) -> None:
        """Werkzeug-spezifische Reaktion auf linken Maus-Press."""
        if not self._tools_enabled:
            return
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
        elif self._tool in (TOOL_HEIGHT_LIGHTEN, TOOL_HEIGHT_DARKEN):
            self._start_height_stroke(x, y)
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

        # Move-Werkzeug (#456): Linksklick-Ziehen pannt den Ausschnitt.
        # Bewusst vor dem Werkzeug-Gate – Pan/Zoom bleiben in jedem Schritt frei.
        if btn == Qt.MouseButton.LeftButton and self._tool == TOOL_MOVE:
            self._viewport.start_pan(event.position())
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
            if self._height_stroke is not None:
                self._extend_height_stroke(int(sp.x()), int(sp.y()))
            else:
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
        if self._height_stroke is not None:
            self._finish_height_stroke()
            return
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
        if (
            event.key() == Qt.Key.Key_Escape
            and self.cancel_active_interaction()
        ):
            return
        super().keyPressEvent(event)

    def _lasso_close(self) -> None:
        if self._pil is None:
            return
        mode = _selection_mode_from_modifiers(self._lasso.modifiers)
        # mask.shape ist typseitig tuple[int, ...]; die 2D-Selektionsmaske
        # liefert immer (H, W). Explizit als tuple[int, int] uebergeben, damit
        # close_to_selection_mask(tuple[int, int]) unter strengeren numpy-Stubs
        # (z. B. numpy 2.2.x) typkorrekt bleibt.
        h, w = self._selection.mask.shape
        new_mask = self._lasso.close_to_selection_mask((h, w))
        pixels = self._selection.set_polygon_result(new_mask, mode)
        self._refresh_overlay()
        self.statusMsg.emit(tr("canvas.lasso_selected", pixels=pixels))

    def _lasso_cancel(self) -> None:
        self._lasso.cancel()

    def _paint_brush(self, cx: int, cy: int, *, additive: bool) -> None:
        if self._pil is None:
            return
        dirty = self._selection.paint_brush(
            cx, cy, self._brush_r, additive=additive)
        if dirty is not None:
            self._refresh_overlay(dirty)

    # Zoom-Grenzen werden von ``CanvasViewport`` definiert; hier als
    # Convenience-Reexport gespiegelt, damit ``canvas.ZOOM_MIN`` / ``canvas.ZOOM_MAX``
    # ohne Umweg über den Viewport lesbar bleiben.
    ZOOM_MIN = CanvasViewport.ZOOM_MIN
    ZOOM_MAX = CanvasViewport.ZOOM_MAX

    def wheelEvent(self, event) -> None:
        self._viewport.handle_wheel(event.angleDelta().y())

    def resizeEvent(self, event) -> None:
        # Zoom-Kontrolle bleibt unten rechts verankert (#464).
        super().resizeEvent(event)
        self._zoom_control.reposition()

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
            self.statusMsg.emit(tr("canvas.format_unsupported"))
            return
        # Asynchron laden (gleicher Worker-Pfad wie der Datei-Dialog),
        # damit ein grosses Foto die UI nicht einfriert.
        self.loadRequested.emit(valid[0])
        if len(valid) > 1:
            self.statusMsg.emit(tr(
                "canvas.opened_extra", name=Path(valid[0]).name,
                extra=len(valid) - 1))

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

    @_requires_image
    def apply_resize(
        self,
        width: int,
        height: int,
        *,
        resample: Image.Resampling = Image.Resampling.LANCZOS,
    ) -> None:
        """Skaliert das gesamte Projekt auf eine Zielgröße in Pixeln (#359).

        Gateprüfung (Megapixel-Limit), No-op-Erkennung und Statusmeldung liegen in
        :meth:`CanvasTransform.apply_resize`; die eigentliche, undo-fähige
        Anwendung in :meth:`resize_project`.
        """
        self._transform.apply_resize(width, height, resample)

    def set_physical_size_mm(self, width_mm: float, height_mm: float) -> None:
        """Verankert die physische Zielgröße (mm) im Projekt und markiert Änderung (#377).

        Schreibt die kanonische physische Größe über den Projektmodell-Setter (#376)
        und hebt die ``content_revision`` an, damit der „ungespeicherte Änderungen"-
        Schutz auch dann greift, wenn die Größenänderung selbst ein No-op war (reine
        DPI-/mm-Metadaten-Änderung) – sonst ginge sie beim Schließen/Bildwechsel
        unbemerkt verloren. Ohne Projekt ein No-op.
        """
        if self._project is None:
            return
        self._project.set_physical_size_mm(width_mm, height_mm)
        self._content_revision += 1

    def resize_project(
        self,
        width: int,
        height: int,
        resample: Image.Resampling,
        desc: str,
    ) -> None:
        """Wendet eine **größenändernde** Skalierung auf das **ganze** Projekt an.

        Größenändernde Operation analog :meth:`apply_geometry`, jedoch über die
        height-bewusste Modelloperation :meth:`Project.resize` (COLOR/Daten via
        Resampling, HEIGHT verlustfrei über die Höhen-Repräsentation). Ein
        einziger Undo-Schritt erfasst den Gesamtzustand vor der Skalierung; das
        Gate hat der Aufrufer (``CanvasTransform``) bereits gesetzt.
        """
        if self._project is None:
            return
        self._history.push(self._project, desc)
        self._emit_history()
        self._project.resize(width, height, resample=resample)
        self._set_image_state()

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
