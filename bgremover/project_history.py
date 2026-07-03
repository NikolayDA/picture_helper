"""Qt-freie, ebenenbewusste Undo/Redo-Historie für :class:`Project`.

Diese Historie hebt das Modell von :mod:`bgremover.canvas_history` (vollständige
RGBA-**Einzelbild**-Snapshots) auf das **Projektmodell** (#331): Undo/Redo deckt
sowohl **strukturelle** Änderungen (Ebene anlegen/löschen/umsortieren/duplizieren,
aktive Ebene, Sichtbarkeit/Opazität/Sperre/Rolle) als auch **Pixel**-Änderungen
je Ebene (Freistellung, Pinsel/Radierer, Transform, Crop) ab. Sie bleibt – wie
``canvas_history`` – ganz ohne Qt isoliert testbar; der Canvas verdrahtet sie
seit #332 (``ImageCanvas._history``).

Speicherstrategie (Kernpunkt des Issues)
----------------------------------------

Eine Vollkopie *aller* Ebenen je Verlaufsschritt wäre bei mehreren Ebenen sehr
groß. Stattdessen besteht ein Snapshot (:class:`_ProjectState`) nur aus

1. **strukturellen Metadaten** (Canvas-Größe, Version, ``metadata``, geordnete
   Ebenenliste mit ID/Name/Kind/Sichtbarkeit/Opazität/Sperre/Rolle, aktiver ID) –
   durchweg kleine, unveränderliche Werte, die beim Erfassen kopiert werden, und
2. **Referenzen** auf die RGBA-Pixeldaten je Ebene (keine Pixelkopie).

Die Pixelpuffer landen in einem **deduplizierenden Pool** (:class:`_PoolEntry`),
der jeden Puffer über *Objektidentität* refzählt: gleiche Ebenen-Bilder werden
über viele Snapshots hinweg **nur einmal** im Speicherbudget gezählt. Da
strukturelle Operationen die Bildobjekte nicht anfassen und Pixel-Operationen
das Bild einer Ebene **ersetzen** (statt es in-place zu mutieren), teilen sich
aufeinanderfolgende Snapshots automatisch alle *unveränderten* Ebenen. Effektiv
kostet ein Schritt nur die **betroffene/aktive** Ebene plus die winzigen
Metadaten – genau die im Issue geforderte Strategie.

Vertrag (wichtig): Aufrufer behandeln Ebenen-Pixeldaten als **unveränderlich**
(ersetzen, nicht in-place mutieren). Nur so bleiben erfasste Snapshots gültig und
ist die Identitäts-Deduplizierung tragfähig (der Pool hält starke Referenzen auf
alle gezählten Puffer, deshalb kann eine ``id`` nie fälschlich wiederverwendet
auf einen falschen Puffer zeigen). Das Modell erfüllt diesen Vertrag bereits:
:class:`~bgremover.project_model.Layer` kopiert Eingabe-Pixeldaten beim Anlegen
und reine Operationen erzeugen neue Bildobjekte.

Budget/Trim (analog ``canvas_history``)
---------------------------------------

Undo- und Redo-Stapel teilen sich ein Byte-Budget (``memory_limit``). Beim
Überschreiten fallen zuerst die **ältesten** Undo-Zustände – jedoch nie der
letzte Undo-Schritt –, danach die am weitesten entfernten Redo-Zustände. Das
**Original** (``set_original``) und der **aktuelle** (live) Projektzustand zählen
bewusst nicht ins Budget. Rückgaben von ``undo``/``redo``/``undo_to``/``restore``
sind eigenständige, frisch aufgebaute :class:`Project`-Instanzen des jeweils
vorherigen Zustands.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, NamedTuple

from PIL import Image

from bgremover.constants import _HISTORY_MEMORY_LIMIT, _REDO_MAX_ENTRIES
from bgremover.project_model import Layer, LayerKind, LayerRole, Project


class _LayerState(NamedTuple):
    """Unveränderlicher Snapshot einer Ebene (Metadaten + Bildreferenz)."""

    id: str
    name: str
    kind: LayerKind
    image: Image.Image
    visible: bool
    opacity: float
    locked: bool
    role: LayerRole | None


class _ProjectState(NamedTuple):
    """Unveränderlicher Snapshot eines Projektzustands inkl. Beschreibung."""

    width: int
    height: int
    version: int
    metadata: dict[str, Any]
    layers: tuple[_LayerState, ...]
    active_layer_id: str | None
    desc: str


class _PoolEntry:
    """Refzähl-Eintrag eines geteilten Pixelpuffers im Dedup-Pool."""

    __slots__ = ("image", "count")

    def __init__(self, image: Image.Image) -> None:
        self.image = image
        self.count = 1


def _capture_state(project: Project, desc: str) -> _ProjectState:
    """Erfasst den aktuellen Projektzustand als leichten, geteilten Snapshot.

    Pixeldaten werden nur **referenziert** (siehe Modul-Doku zur Speicher-
    strategie und zum Unveränderlichkeits-Vertrag); ``metadata`` wird dagegen
    **tief** kopiert, damit auch verschachtelte, veränderliche Werte vom späteren
    Projektzustand entkoppelt sind und ``undo``/``restore`` exakt den erfassten
    Zustand liefern. Das Dict bleibt klein (die physische Zielgröße plus das
    noch reservierte Bittiefen-Feld), die Kopie ist also vernachlässigbar.
    """
    layers = tuple(
        _LayerState(
            layer.id,
            layer.name,
            layer.kind,
            layer.image,
            layer.visible,
            layer.opacity,
            layer.locked,
            layer.role,
        )
        for layer in project.layers
    )
    return _ProjectState(
        project.width,
        project.height,
        project.version,
        deepcopy(project.metadata),
        layers,
        project.active_layer_id,
        desc,
    )


def _build_project(state: _ProjectState) -> Project:
    """Baut aus einem Snapshot ein **eigenständiges** Projekt des Zustands.

    Über die öffentliche Modell-API; ``Layer`` kopiert die Pixeldaten dabei, das
    Ergebnis ist also vom Verlauf entkoppelt und exakt der erfasste Zustand.
    """
    project = Project(
        state.width,
        state.height,
        version=state.version,
        metadata=deepcopy(state.metadata),
    )
    for ls in state.layers:
        project.add_layer(
            Layer(
                name=ls.name,
                kind=ls.kind,
                image=ls.image,
                id=ls.id,
                visible=ls.visible,
                opacity=ls.opacity,
                locked=ls.locked,
                role=ls.role,
            ),
            make_active=False,
        )
    if state.active_layer_id is not None:
        project.set_active(state.active_layer_id)
    return project


class ProjectHistory:
    """Verwaltet ebenenbewusste Undo/Redo-Projektzustände ohne Qt.

    Die öffentliche Schnittstelle spiegelt :class:`CanvasHistory`, arbeitet aber
    auf :class:`Project` statt auf einem Einzelbild. Intern teilen sich die
    Snapshots Pixelpuffer über einen deduplizierenden Pool (siehe Modul-Doku).
    """

    def __init__(
        self,
        memory_limit: int = _HISTORY_MEMORY_LIMIT,
        redo_max: int = _REDO_MAX_ENTRIES,
    ) -> None:
        if redo_max < 0:
            raise ValueError("redo_max must be non-negative")
        self._undo: deque[_ProjectState] = deque()
        self._redo: deque[_ProjectState] = deque(maxlen=redo_max)
        self._original: _ProjectState | None = None
        self._memory_limit: int = memory_limit
        # Identitäts-Pool: id(image) -> Refzähl-Eintrag. ``_pool_bytes`` ist die
        # deduplizierte Größe von Undo + Redo zusammen (geteiltes Budget).
        self._pool: dict[int, _PoolEntry] = {}
        self._pool_bytes: int = 0

    @property
    def _history_bytes(self) -> int:
        return self._pool_bytes

    @staticmethod
    def _img_bytes(img: Image.Image) -> int:
        return img.width * img.height * 4

    # ── Pool-Buchhaltung ────────────────────────────────────────────────
    def _register(self, state: _ProjectState) -> None:
        """Zählt die Pixelpuffer eines neu gestapelten Snapshots ein."""
        for layer in state.layers:
            key = id(layer.image)
            entry = self._pool.get(key)
            if entry is None:
                self._pool[key] = _PoolEntry(layer.image)
                self._pool_bytes += self._img_bytes(layer.image)
            else:
                entry.count += 1

    def _unregister(self, state: _ProjectState) -> None:
        """Zählt die Pixelpuffer eines entfernten Snapshots wieder aus."""
        for layer in state.layers:
            key = id(layer.image)
            entry = self._pool[key]
            entry.count -= 1
            if entry.count == 0:
                del self._pool[key]
                self._pool_bytes -= self._img_bytes(layer.image)

    # ── Stapel-Primitive ────────────────────────────────────────────────
    def _append_undo(self, state: _ProjectState) -> None:
        self._undo.append(state)
        self._register(state)

    def _append_redo(self, state: _ProjectState) -> None:
        if self._redo.maxlen == 0:
            return
        # Manuell den ältesten Eintrag verdrängen, bevor ``deque`` ihn selbst
        # (an der Buchhaltung vorbei) bei vollem ``maxlen`` herauswirft.
        if len(self._redo) == self._redo.maxlen:
            self._evict_oldest_redo()
        self._redo.append(state)
        self._register(state)

    def _pop_undo(self) -> _ProjectState:
        state = self._undo.pop()
        self._unregister(state)
        return state

    def _pop_redo(self) -> _ProjectState:
        state = self._redo.pop()
        self._unregister(state)
        return state

    def _evict_oldest_undo(self) -> None:
        self._unregister(self._undo.popleft())

    def _evict_oldest_redo(self) -> None:
        self._unregister(self._redo.popleft())

    def _clear_redo(self) -> None:
        while self._redo:
            self._unregister(self._redo.popleft())

    def _trim(self) -> None:
        """Setzt das gemeinsame Undo-/Redo-Speicherbudget durch.

        Zuerst fallen die ältesten Undo-Zustände, jedoch nie der letzte
        Undo-Schritt. Reicht das nicht, werden die am weitesten entfernten
        Redo-Zustände entfernt. Dank Deduplizierung zählt ein über mehrere
        Snapshots geteilter Puffer nur einmal; Original und aktueller Zustand
        sind ohnehin nicht Teil dieses Budgets.
        """
        while self._history_bytes > self._memory_limit:
            if len(self._undo) > 1:
                self._evict_oldest_undo()
            elif self._redo:
                self._evict_oldest_redo()
            else:
                break

    # ── Öffentliche API ─────────────────────────────────────────────────
    @property
    def can_undo(self) -> bool:
        """True, wenn mindestens ein Undo-Schritt vorliegt."""
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        """True, wenn mindestens ein Redo-Schritt vorliegt."""
        return bool(self._redo)

    def push(self, current: Project, desc: str) -> None:
        self._append_undo(_capture_state(current, desc))
        self._clear_redo()
        self._trim()

    def undo(self, current: Project | None) -> tuple[Project, str] | None:
        if not self._undo:
            return None
        state = self._pop_undo()
        if current is not None:
            self._append_redo(_capture_state(current, state.desc))
            self._trim()
        return _build_project(state), state.desc

    def redo(self, current: Project | None) -> tuple[Project, str] | None:
        if not self._redo:
            return None
        state = self._pop_redo()
        if current is not None:
            self._append_undo(_capture_state(current, state.desc))
            self._trim()
        return _build_project(state), state.desc

    def undo_to(
        self,
        current: Project | None,
        steps: int,
    ) -> tuple[Project, str, int] | None:
        actual = min(steps, len(self._undo))
        if actual <= 0:
            return None

        # Der live übergebene Zustand wandert als erster auf den Redo-Stapel,
        # danach die übersprungenen Zwischenstände; die Beschreibungen wandern
        # dabei – wie in ``canvas_history`` – um einen Schritt mit.
        redo_state: _ProjectState | None = (
            _capture_state(current, "") if current is not None else None
        )
        target: _ProjectState | None = None
        for _ in range(actual):
            target = self._pop_undo()
            if redo_state is not None:
                self._append_redo(redo_state._replace(desc=target.desc))
            redo_state = target

        assert target is not None
        self._trim()
        return _build_project(target), target.desc, actual

    def set_original(self, project: Project) -> None:
        # Referenz-Snapshot des Ausgangszustands; nicht Teil des Budgets.
        self._original = _capture_state(project, "")

    def restore(
        self,
        current: Project | None,
        desc: str,
    ) -> Project | None:
        if self._original is None:
            return None
        self._clear_redo()
        if current is not None:
            self._append_undo(_capture_state(current, desc))
            self._trim()
        return _build_project(self._original)

    def descriptions(self) -> list[str]:
        return [state.desc for state in reversed(self._undo)]

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._pool.clear()
        self._pool_bytes = 0
        self._original = None
