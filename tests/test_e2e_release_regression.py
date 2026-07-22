"""E2E-Release-Regression über das echte ``MainWindow`` (#644, Epic #639).

Fährt das in #595 geforderte Szenario end-to-end durch das MainWindow –
**nicht** über einen Modul-Kurzschluss: Bild öffnen → Höhenkarte erzeugen →
3D-Vorschau aktivieren (headless: dokumentierter Fallback) → Höhen-Operation +
Undo/Redo → Projekt speichern/wieder laden. Geprüft werden der 3D-Fallback-
Zweig, die Nicht-Mutation der Höhendaten durch den 2D↔3D-Wechsel und die
**bitgenaue** 16-Bit-Payload über Undo/Redo und den ``.bgrproj``-Roundtrip
(#587/#588).

Läuft headless/offscreen deterministisch (Marker ``ui_smoke`` → im normalen
CI-Gate **und** ``ui`` → zusätzlich in ``make ui``/der Nightly-Suite, #644-
Nachtrag). Auf einem Self-hosted Runner mit echtem GL erreicht dasselbe
Szenario den Ready-Zweig – gesteuert nur über die Umgebung, ohne Testcode-Fork.
Ist ``ABNAHME_EVIDENCE_DIR`` gesetzt (Abnahme-Workflow), wird zusätzlich ein
Evidenz-JSON nach dem Vertrag aus #640 geschrieben.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from PIL import Image

from bgremover import MainWindow, height_ops
from bgremover.project_model import LayerKind, LayerRole, Project

# ``ui`` UND ``ui_smoke`` gemeinsam (#644-Nachtrag): ``ui_smoke`` allein hält
# das Szenario nur im normalen Check/PR-CI-Lauf (Default-``addopts`` "not ui or
# ui_smoke"), ``make ui``/die Nightly-Suite selektieren dagegen strikt "-m ui"
# – ohne den zusätzlichen ``ui``-Marker liefe der Test dort gar nicht mit.
pytestmark = [pytest.mark.ui, pytest.mark.ui_smoke]


def _gradient(size: int = 16) -> Image.Image:
    """Unterscheidbares Farbmotiv (horizontaler Verlauf) für reproduzierbare Höhen."""
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for x in range(size):
        for y in range(size):
            px[x, y] = (x * 16 % 256, y * 16 % 256, (x + y) * 8 % 256, 255)
    return img


_LayerSignature = tuple[str, LayerKind, LayerRole | None, str, bool, float, bool]


def _project_signature(
    project: Project,
) -> tuple[list[_LayerSignature], str | None, dict[str, object]]:
    """Vollständige Struktur-/Metadaten-Signatur für den Save/Open-Vergleich
    (#644-Nachtrag): Ebenenreihenfolge, stabile IDs, Sichtbarkeit/Deckkraft/
    Sperre je Ebene, aktive Ebene und Projekt-Metadaten – nicht nur
    ``(kind, role, name)`` wie zuvor. Die Metadaten laufen durch einen
    JSON-Roundtrip: ``.bgrproj`` persistiert sie als JSON, ein Tupel wie
    ``physical_size_mm`` kommt beim Laden also als Liste zurück – bewusst
    dieselbe (verlustfreie) Normalisierung wie die echte Datei, sonst würde
    ein reiner Python-Typunterschied (Tuple vs. Liste) fälschlich als
    Roundtrip-Fehler erscheinen.
    """
    layers = [
        (
            layer.id, layer.kind, layer.role, layer.name,
            layer.visible, layer.opacity, layer.locked,
        )
        for layer in project.layers
    ]
    metadata = json.loads(json.dumps(dict(project.metadata)))
    return layers, project.active_layer_id, metadata


def _payload_hash(win: MainWindow) -> str:
    """SHA256 der kanonischen 16-Bit-Payload der aktiven HEIGHT-Ebene."""
    layer = win._canvas.project.active_layer()
    assert layer is not None and layer.kind is LayerKind.HEIGHT
    field = layer.height_data
    assert field is not None and field.max_value == 65535
    digest = hashlib.sha256()
    digest.update(field.values.tobytes())
    digest.update(field.coverage.tobytes())
    return digest.hexdigest()


def _emit_evidence(status: str, notes: list[str], native_3d_state: str) -> None:
    """Evidenz-JSON nach Vertrag #640 schreiben, wenn im Abnahme-Workflow."""
    target = os.environ.get("ABNAHME_EVIDENCE_DIR")
    if not target:
        return
    out = Path(target)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": 1,
        "kind": "abnahme-e2e",
        "platform": os.environ.get("ABNAHME_PLATFORM", "unbekannt"),
        "status": status,
        "scenario": "open->height->3d->op->undo/redo->save/open",
        "commit_sha": os.environ.get("GITHUB_SHA", "unbekannt"),
        "erzeugt_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "native_3d_required": os.environ.get("ABNAHME_REQUIRE_NATIVE_3D") == "1",
        "native_3d_state": native_3d_state,
        "hinweise": notes,
    }
    (out / "e2e-evidenz.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )


def _assert_preview3d_state(
    win: MainWindow, qtbot, *, require_native: bool, phase: str,  # type: ignore[no-untyped-def]
) -> str:
    """Aktiviert 3D und belegt je nach Umgebung Ready oder Headless-Fallback."""
    win._set_preview3d_mode(True)
    qtbot.waitUntil(
        lambda: win._relief3d_view.state in {"ready", "unavailable", "error"},
        timeout=30_000,
    )
    state = win._relief3d_view.state
    if not require_native:
        assert state == "unavailable", f"unerwarteter Headless-3D-Zustand ({phase}): {state}"
        return state

    assert state == "ready", f"nativer 3D-Zweig nicht bereit ({phase}): {state}"
    viewer = win._relief3d_view.viewer()
    assert viewer is not None, f"Ready-Zustand ohne GL-Viewer ({phase})"
    qtbot.waitUntil(
        lambda: (
            viewer.has_failed
            or (
                viewer.isValid()
                and viewer._gl_ready
                and viewer._mesh is not None
                and viewer._pending_mesh is None
            )
        ),
        timeout=30_000,
    )
    state = win._relief3d_view.state
    assert not viewer.has_failed and state == "ready", (
        f"nativer GL-Frame fehlgeschlagen ({phase})"
    )
    assert viewer._index_count > 0, f"keine 3D-Geometrie hochgeladen ({phase})"
    return state


def _run_scenario(win: MainWindow, tmp_path: Path, qtbot) -> tuple[list[str], str]:  # type: ignore[no-untyped-def]
    notes: list[str] = []

    # 1) Bild über die öffentliche MainWindow-Fassade und den echten
    # asynchronen Loader öffnen → genau eine COLOR-Ebene.
    source_path = tmp_path / "src.png"
    _gradient().save(source_path)
    win.open_paths([str(source_path)])
    qtbot.waitUntil(
        lambda: (
            win._canvas.project is not None
            and len(win._canvas.project.layers) == 1
        ),
        timeout=30_000,
    )
    project = win._canvas.project
    assert project is not None
    assert [layer.kind for layer in project.layers] == [LayerKind.COLOR]
    notes.append("Bild geöffnet: 1 COLOR-Ebene.")

    # 2) Höhenkarte erzeugen → aktive HEIGHT-Ebene mit 16-Bit-Payload.
    win._canvas.generate_height_map()
    active = win._canvas.project.active_layer()
    assert active is not None and active.kind is LayerKind.HEIGHT
    assert active.role is LayerRole.HEIGHT_MAP
    assert active.height_data is not None and active.height_data.max_value == 65535
    hash_after_generate = _payload_hash(win)
    notes.append("Höhenkarte erzeugt: aktive HEIGHT-Ebene, 16-Bit-Payload.")

    # 3) 3D-Vorschau aktivieren. Headless muss im dokumentierten Fallback
    # landen; die Hardware-Abnahme verlangt dagegen ausdrücklich den fertig
    # initialisierten nativen GL-Viewer samt hochgeladenem Mesh.
    require_native = os.environ.get("ABNAHME_REQUIRE_NATIVE_3D") == "1"
    state = _assert_preview3d_state(
        win, qtbot, require_native=require_native, phase="vor Save/Open",
    )
    if require_native:
        notes.append("Nativer 3D-GL-Zweig ready; Mesh hochgeladen und Frame gerendert.")
    else:
        notes.append("Dokumentierter Headless-3D-Fallback erreicht.")
    # 2D↔3D-Wechsel mutiert die Höhendaten nicht.
    assert _payload_hash(win) == hash_after_generate
    win._set_preview3d_mode(False)
    assert win._canvas_stack.currentIndex() == 0
    assert _payload_hash(win) == hash_after_generate
    notes.append(f"3D-Zustand {state}; Höhendaten beim 2D↔3D-Wechsel unverändert.")

    # 4) Höhen-Operation anwenden → Undo → Redo (bitgenau, #587).
    win._canvas.apply_height_op(lambda f: height_ops.quantize(f, 4))
    hash_after_op = _payload_hash(win)
    assert hash_after_op != hash_after_generate
    win._canvas.undo()
    assert _payload_hash(win) == hash_after_generate, "Undo nicht bitgenau"
    win._canvas.redo()
    assert _payload_hash(win) == hash_after_op, "Redo nicht bitgenau"
    notes.append("Höhen-Op + Undo/Redo bitgenau.")

    # 5) Projekt über die MainWindow-Pfade speichern und wieder laden – nicht
    # direkt über project_io am UI vorbei. Payload und Struktur bleiben gleich.
    # Nicht-Default-Zustand auf der COLOR-Ebene + physische Zielgröße als
    # Metadaten-Beleg (#644-Nachtrag): sonst prüfte der Vergleich nur
    # triviale, ohnehin unveränderte Default-Werte.
    before = win._canvas.project
    color_layer = before.layers[0]
    assert color_layer.kind is LayerKind.COLOR
    color_layer.visible = False
    color_layer.opacity = 0.5
    color_layer.locked = True
    before.set_physical_size_mm(50.0, 30.0)

    path = tmp_path / "regression.bgrproj"
    before_signature = _project_signature(before)
    assert win._write_project(str(path)), "MainWindow-Speicherpfad fehlgeschlagen"
    win._load_project_into_canvas(str(path))
    reloaded = win._canvas.project
    assert _project_signature(reloaded) == before_signature, (
        "Ebenen-/Metadaten-Struktur (ID/Sichtbarkeit/Deckkraft/Sperre/aktive "
        "Ebene/Metadaten) nach Save/Open nicht wertgleich"
    )
    reloaded_active = reloaded.active_layer()
    assert reloaded_active is not None and reloaded_active.kind is LayerKind.HEIGHT
    assert reloaded_active.height_data is not None
    rd = hashlib.sha256()
    rd.update(reloaded_active.height_data.values.tobytes())
    rd.update(reloaded_active.height_data.coverage.tobytes())
    assert rd.hexdigest() == hash_after_op, "Payload nach Save/Open nicht bitgenau"

    # Der Roundtrip ist erst vollständig bewiesen, wenn die neu geladene
    # HEIGHT-Ebene erneut durch den echten 3D-Pfad gerendert werden kann. Dabei
    # darf die 16-Bit-Payload ebenfalls nicht mutieren.
    state = _assert_preview3d_state(
        win, qtbot, require_native=require_native, phase="nach Save/Open",
    )
    assert _payload_hash(win) == hash_after_op, "3D nach Save/Open mutiert die Payload"
    notes.append(
        "Save/Open (v2) bitgenau, Ebenenstruktur wertgleich; "
        f"3D-Zustand nach Reload erneut {state}.",
    )
    return notes, state


def test_e2e_release_regression(qapp, qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    win = MainWindow()
    native_3d_state = "nicht-erreicht"
    qtbot.addWidget(win)
    win.show()
    try:
        notes, native_3d_state = _run_scenario(win, tmp_path, qtbot)
    except Exception as exc:  # noqa: BLE001 - Evidenz auch bei Fehlschlag schreiben.
        native_3d_state = win._relief3d_view.state
        _emit_evidence("fehlgeschlagen", [f"Abbruch: {exc}"], native_3d_state)
        raise
    else:
        _emit_evidence("bestanden", notes, native_3d_state)
    finally:
        win.close()
