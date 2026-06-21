"""Unit-Tests für ``ProjectHistory`` (reine Logik, kein QApplication).

Die Historie ist ebenenbewusst: Undo/Redo deckt strukturelle **und** Pixel-
Änderungen am :class:`Project`-Modell ab. Geprüft werden exakte Zustands-
Rekonstruktion über gemischte Folgen, Sprung-Undo, „Original wiederherstellen"
sowie das deduplizierende Speicherbudget (geteilter Undo-/Redo-Pool, der gleiche
Ebenenpuffer nur einmal zählt).
"""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from bgremover.project_history import ProjectHistory
from bgremover.project_model import LayerKind, LayerRole, Project

# ── Helfer ──────────────────────────────────────────────────────────────


def _solid(width: int, height: int, color: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", (width, height), color)


def _project(width: int = 8, height: int = 8) -> Project:
    """Frisches Projekt mit genau einer roten COLOR-Ebene."""
    project = Project(width, height)
    project.create_layer(_solid(width, height, (255, 0, 0, 255)), name="Basis")
    return project


def _layer_signature(project: Project) -> tuple:
    """Struktur + Pixelinhalt aller Ebenen als vergleichbarer Fingerabdruck."""
    return tuple(
        (
            layer.id,
            layer.name,
            layer.kind,
            layer.visible,
            round(layer.opacity, 6),
            layer.locked,
            layer.role,
            np.asarray(layer.image).tobytes(),
        )
        for layer in project.layers
    )


def _signature(project: Project) -> tuple:
    """Vollständiger, vergleichbarer Fingerabdruck eines Projektzustands."""
    return (
        project.size,
        project.version,
        dict(project.metadata),
        project.active_layer_id,
        _layer_signature(project),
    )


def _assert_same(a: Project, b: Project) -> None:
    assert _signature(a) == _signature(b)


def _pool_bytes(history: ProjectHistory) -> int:
    """Unabhängig nachgerechnete, deduplizierte Pool-Größe."""
    return sum(history._img_bytes(entry.image) for entry in history._pool.values())


def _assert_accounting(history: ProjectHistory) -> None:
    """Pool-Refzählung und Byte-Bilanz müssen exakt konsistent sein."""
    assert history._pool_bytes == _pool_bytes(history)
    assert history._history_bytes == history._pool_bytes
    # Jeder gestapelte Snapshot muss mit genau einem Refzähl-Beitrag im Pool
    # stehen; verwaiste oder fehlende Einträge fielen hier auf.
    expected: dict[int, int] = {}
    for state in (*history._undo, *history._redo):
        for layer in state.layers:
            expected[id(layer.image)] = expected.get(id(layer.image), 0) + 1
    assert {key: e.count for key, e in history._pool.items()} == expected


# ── Speicherbudget & Deduplizierung ─────────────────────────────────────


def test_unchanged_layers_are_shared_in_the_budget() -> None:
    """Strukturelle Schritte kosten nur Metadaten, keine Pixelkopien."""
    history = ProjectHistory()
    project = _project()

    history.push(project, "s1")
    bytes_after_first = history._history_bytes
    assert bytes_after_first == history._img_bytes(project.layers[0].image)

    # Rein strukturelle Folge: Sichtbarkeit, Opazität, aktive Ebene. Das
    # Bildobjekt der Ebene bleibt identisch → kein zusätzliches Pixelbudget.
    project.set_visible(project.layers[0].id, False)
    history.push(project, "s2")
    project.set_opacity(project.layers[0].id, 0.5)
    history.push(project, "s3")

    assert history._history_bytes == bytes_after_first
    _assert_accounting(history)


def test_pixel_edit_adds_only_the_changed_layer() -> None:
    """Eine Pixeländerung erhöht das Budget nur um die betroffene Ebene."""
    history = ProjectHistory()
    project = _project(8, 8)
    second = project.create_layer(_solid(8, 8, (0, 255, 0, 255)), name="Oben")
    history.push(project, "zwei ebenen")
    base_bytes = history._history_bytes
    assert base_bytes == 2 * history._img_bytes(project.layers[0].image)

    # Nur das Bild der aktiven Ebene ersetzen (Vertrag: ersetzen, nicht mutieren).
    project.layer_by_id(second.id).image = _solid(8, 8, (0, 0, 255, 255))
    history.push(project, "pinsel")

    # Drei Snapshots teilen die unveränderte Basis; nur die geänderte Ebene
    # kommt einmal hinzu.
    assert history._history_bytes == base_bytes + history._img_bytes(second.image)
    _assert_accounting(history)


def test_push_evicts_oldest_states_from_shared_budget() -> None:
    one = 8 * 8 * 4
    history = ProjectHistory(memory_limit=2 * one)
    project = _project(8, 8)

    history.push(project, "a")
    # Jede Pixeländerung ist ein eigener Puffer (eindeutige Farbe).
    project.layer_by_id(project.layers[0].id).image = _solid(8, 8, (1, 1, 1, 255))
    history.push(project, "b")
    project.layer_by_id(project.layers[0].id).image = _solid(8, 8, (2, 2, 2, 255))
    history.push(project, "c")

    assert history.descriptions() == ["c", "b"]
    assert history._history_bytes == 2 * one
    _assert_accounting(history)


def test_trim_keeps_at_least_one_undo_entry() -> None:
    history = ProjectHistory(memory_limit=1)
    project = _project(8, 8)
    history.push(project, "a")
    project.layer_by_id(project.layers[0].id).image = _solid(8, 8, (9, 9, 9, 255))
    history.push(project, "b")

    assert history.descriptions() == ["b"]
    assert history._history_bytes == 8 * 8 * 4
    assert history._history_bytes > history._memory_limit
    _assert_accounting(history)


# ── Undo/Redo über strukturelle UND Pixel-Operationen ───────────────────


def test_mixed_structural_and_pixel_undo_redo_restores_exact_states() -> None:
    """Gemischte Folge: jeder Undo-Schritt liefert exakt den Vorzustand."""
    history = ProjectHistory()
    project = _project(8, 8)

    states: list[Project] = []

    def snapshot(desc: str) -> None:
        # Vor jeder Änderung den aktuellen Zustand erfassen (Canvas-Muster).
        states.append(_build_clone(project))
        history.push(project, desc)

    base = project.layers[0]

    snapshot("add green")           # S0: nur Basis
    green = project.create_layer(_solid(8, 8, (0, 255, 0, 128)), name="Grün")

    snapshot("pixel edit base")     # S1: Basis + Grün
    project.layer_by_id(base.id).image = _solid(8, 8, (10, 20, 30, 255))

    snapshot("set opacity")         # S2: Basis(blau) + Grün
    project.set_opacity(green.id, 0.25)

    snapshot("assign role")         # S3: + Opazität
    project.assign_role(green.id, LayerRole.COLOR_MOTIF)

    snapshot("reorder")             # S4: + Rolle
    project.reorder([green.id, base.id])

    snapshot("duplicate")           # S5: + Reihenfolge
    project.duplicate_layer(base.id)

    snapshot("remove")              # S6: + Duplikat
    project.remove_layer(green.id)
    # S7 (Endzustand) wird nicht gepusht – er ist der „aktuelle" Zustand.

    # Schrittweises Undo muss die erfassten Vorzustände exakt zurückgeben.
    current = project
    for expected in reversed(states):
        result = history.undo(current)
        assert result is not None
        current = result[0]
        _assert_same(current, expected)
        _assert_accounting(history)

    # Und Redo muss die Folge exakt wieder vorwärts abspielen.
    for expected in states[1:]:
        result = history.redo(current)
        assert result is not None
        current = result[0]
        _assert_same(current, expected)
        _assert_accounting(history)


def _build_clone(project: Project) -> Project:
    """Eigenständiger Klon eines Projektzustands (für Erwartungswerte)."""
    clone = Project(
        project.width,
        project.height,
        version=project.version,
        metadata=dict(project.metadata),
    )
    for layer in project.layers:
        clone.add_layer(
            type(layer)(
                name=layer.name,
                kind=layer.kind,
                image=layer.image,
                id=layer.id,
                visible=layer.visible,
                opacity=layer.opacity,
                locked=layer.locked,
                role=layer.role,
            ),
            make_active=False,
        )
    if project.active_layer_id is not None:
        clone.set_active(project.active_layer_id)
    return clone


def test_returned_project_is_independent_of_history() -> None:
    """Die Rückgabe ist entkoppelt: spätere Bearbeitung verändert den Verlauf nicht."""
    history = ProjectHistory()
    project = _project(8, 8)
    history.push(project, "a")
    project.layer_by_id(project.layers[0].id).image = _solid(8, 8, (5, 5, 5, 255))

    restored = history.undo(project)
    assert restored is not None
    prev = restored[0]

    # Den zurückgegebenen Zustand mutieren …
    prev.create_layer(_solid(8, 8, (7, 7, 7, 255)), name="Neu")
    prev.layer_by_id(prev.layers[0].id).image = _solid(8, 8, (8, 8, 8, 255))

    # … erneutes Redo liefert weiterhin den ursprünglich erfassten Zustand.
    redone = history.redo(_project(8, 8))
    assert redone is not None
    assert redone[1] == "a"


# ── Sprung-Undo (undo_to) ───────────────────────────────────────────────


def test_undo_to_jumps_multiple_steps_and_fills_redo() -> None:
    history = ProjectHistory()
    project = _project(8, 8)

    s_a = _build_clone(project)            # Zustand vor Bearbeitung "a"
    history.push(project, "a")
    project.layer_by_id(project.layers[0].id).image = _solid(8, 8, (1, 1, 1, 255))
    s_b = _build_clone(project)            # Zustand vor "b"
    history.push(project, "b")
    project.layer_by_id(project.layers[0].id).image = _solid(8, 8, (2, 2, 2, 255))
    s_c = _build_clone(project)            # Zustand vor "c"
    history.push(project, "c")
    project.layer_by_id(project.layers[0].id).image = _solid(8, 8, (3, 3, 3, 255))
    s_final = _build_clone(project)        # aktueller (nicht gepushter) Zustand

    result = history.undo_to(project, 3)
    assert result is not None
    restored, desc, actual = result
    assert (desc, actual) == ("a", 3)
    _assert_same(restored, s_a)            # Sprung landet exakt auf dem Vorzustand
    assert history.descriptions() == []
    assert len(history._redo) == 3
    _assert_accounting(history)

    # Redo spielt die übersprungenen Zustände inhaltlich exakt vorwärts ab.
    current: Project = restored
    for expected in (s_b, s_c, s_final):
        forward = history.redo(current)
        assert forward is not None
        current = forward[0]
        _assert_same(current, expected)
        _assert_accounting(history)


def test_undo_to_clamps_to_available_steps() -> None:
    history = ProjectHistory()
    project = _project(8, 8)
    history.push(project, "a")
    assert history.undo_to(project, 0) is None
    assert history.undo_to(None, 5) is not None  # einziger Schritt, geklemmt
    assert history.undo_to(project, 5) is None   # Stapel nun leer


# ── „Original wiederherstellen" ─────────────────────────────────────────


def test_restore_returns_original_state_and_clears_redo() -> None:
    history = ProjectHistory()
    project = _project(8, 8)
    original = _build_clone(project)
    history.set_original(project)

    history.push(project, "edit")
    project.layer_by_id(project.layers[0].id).image = _solid(8, 8, (4, 4, 4, 255))
    undone = history.undo(project)
    assert undone is not None
    assert history._redo  # Redo gefüllt

    restored = history.restore(undone[0], "restored")
    assert restored is not None
    _assert_same(restored, original)
    assert not history._redo
    _assert_accounting(history)


def test_restore_without_original_returns_none() -> None:
    history = ProjectHistory()
    assert history.restore(_project(8, 8), "x") is None


def test_repeated_restore_stays_within_budget() -> None:
    one = 8 * 8 * 4
    history = ProjectHistory(memory_limit=2 * one)
    project = _project(8, 8)
    history.set_original(project)
    current: Project = project

    for i in range(15):
        current.layer_by_id(current.layers[0].id).image = _solid(8, 8, (i, i, i, 255))
        restored = history.restore(current, "restored")
        assert restored is not None
        current = restored
        assert history._history_bytes <= history._memory_limit
        _assert_accounting(history)


# ── Redo-Cap, Leerfälle, Clear ──────────────────────────────────────────


def test_undo_redo_on_empty_history_returns_none() -> None:
    history = ProjectHistory()
    assert history.undo(_project()) is None
    assert history.redo(_project()) is None
    assert history.descriptions() == []


def test_push_clears_redo() -> None:
    history = ProjectHistory()
    project = _project(8, 8)
    history.push(project, "a")
    undone = history.undo(project)
    assert undone is not None
    assert history._redo

    history.push(undone[0], "new branch")
    assert not history._redo
    _assert_accounting(history)


def test_redo_cap_limits_entries_and_budget() -> None:
    cap = 3
    history = ProjectHistory(redo_max=cap)
    assert history._redo.maxlen == cap
    project = _project(8, 8)

    for i in range(cap + 5):
        project.layer_by_id(project.layers[0].id).image = _solid(8, 8, (i, i, i, 255))
        history.push(project, f"edit{i}")

    current: Project = project
    for _ in range(cap + 5):
        result = history.undo(current)
        if result is None:
            break
        current = result[0]
        _assert_accounting(history)

    assert len(history._redo) == cap
    _assert_accounting(history)


def test_zero_redo_cap_drops_redo_entirely() -> None:
    history = ProjectHistory(redo_max=0)
    project = _project(8, 8)
    history.push(project, "edit")

    result = history.undo(project)
    assert result is not None
    assert not history._redo
    assert history.redo(result[0]) is None
    _assert_accounting(history)


def test_negative_redo_cap_is_rejected() -> None:
    with pytest.raises(ValueError, match="redo_max"):
        ProjectHistory(redo_max=-1)


def test_undo_with_none_current_does_not_fill_redo() -> None:
    history = ProjectHistory()
    project = _project(8, 8)
    history.push(project, "a")
    undone = history.undo(None)
    assert undone is not None
    assert not history._redo
    _assert_accounting(history)


def test_redo_with_none_current_does_not_fill_undo() -> None:
    history = ProjectHistory()
    project = _project(8, 8)
    history.push(project, "a")
    undone = history.undo(project)
    assert undone is not None and history._redo
    undo_len = len(history._undo)

    redone = history.redo(None)
    assert redone is not None
    assert len(history._undo) == undo_len  # kein neuer Undo-Eintrag
    _assert_accounting(history)


def test_restore_with_none_current_does_not_push_undo() -> None:
    history = ProjectHistory()
    project = _project(8, 8)
    history.set_original(project)
    restored = history.restore(None, "r")
    assert restored is not None
    assert not history._undo
    _assert_accounting(history)


def test_trim_evicts_redo_when_undo_cannot_shrink_further() -> None:
    """Bei minimalem Undo-Stapel verdrängt das Budget die Redo-Zustände."""
    history = ProjectHistory(memory_limit=1)  # kleiner als ein Bild (256 B)
    project = _project(8, 8)
    history.push(project, "a")  # einziger Undo-Schritt bleibt trotz Überschreitung
    assert history._history_bytes > history._memory_limit

    project.layer_by_id(project.layers[0].id).image = _solid(8, 8, (9, 9, 9, 255))
    undone = history.undo(project)  # Undo leert sich; Redo-Append + Trim wirft Redo raus
    assert undone is not None
    assert not history._redo
    assert history._history_bytes == 0
    _assert_accounting(history)


def test_empty_project_state_round_trips() -> None:
    """Ein leerer Projektzustand (keine Ebene, aktive ID ``None``) wird exakt rekonstruiert."""
    history = ProjectHistory()
    project = Project(8, 8)
    assert project.active_layer_id is None
    history.push(project, "empty")
    project.create_layer(_solid(8, 8, (1, 1, 1, 255)), name="L")

    undone = history.undo(project)
    assert undone is not None
    restored = undone[0]
    assert len(restored) == 0
    assert restored.active_layer_id is None
    assert restored.size == (8, 8)


def test_clear_resets_stacks_pool_and_original() -> None:
    history = ProjectHistory()
    project = _project(8, 8)
    history.set_original(project)
    history.push(project, "a")
    undone = history.undo(project)
    assert undone is not None

    history.clear()

    assert not history._undo
    assert not history._redo
    assert history._pool == {}
    assert history._pool_bytes == 0
    assert history._history_bytes == 0
    assert history._original is None


def test_repeated_undo_redo_never_exceeds_shared_budget() -> None:
    one = 8 * 8 * 4
    history = ProjectHistory(memory_limit=3 * one)
    project = _project(8, 8)
    for i in range(3):
        project.layer_by_id(project.layers[0].id).image = _solid(8, 8, (i, i, i, 255))
        history.push(project, f"s{i}")
    current: Project = project

    for _ in range(50):
        undone = history.undo(current)
        assert undone is not None
        current = undone[0]
        assert history._history_bytes <= history._memory_limit
        _assert_accounting(history)

        redone = history.redo(current)
        assert redone is not None
        current = redone[0]
        assert history._history_bytes <= history._memory_limit
        _assert_accounting(history)


def test_module_is_qt_free() -> None:
    """Das History-Modul darf keine Qt-Importe enthalten (Qt-frei testbar)."""
    import ast
    from pathlib import Path

    import bgremover.project_history as ph

    tree = ast.parse(Path(ph.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    assert not any(name.split(".")[0] in {"PyQt6", "PyQt5", "PySide6"} for name in imported)


def test_kind_is_preserved_for_data_layers() -> None:
    """Auch Nicht-COLOR-Ebenen (HEIGHT/GLOSS) werden korrekt rekonstruiert."""
    history = ProjectHistory()
    project = Project(8, 8)
    project.create_layer(_solid(8, 8, (1, 2, 3, 255)), name="C", kind=LayerKind.COLOR)
    project.create_layer(
        _solid(8, 8, (4, 5, 6, 255)),
        name="H",
        kind=LayerKind.HEIGHT,
        role=LayerRole.HEIGHT_MAP,
    )
    expected = _build_clone(project)
    history.push(project, "two kinds")
    project.remove_layer(project.layers[0].id)

    restored = history.undo(project)
    assert restored is not None
    _assert_same(restored[0], expected)
