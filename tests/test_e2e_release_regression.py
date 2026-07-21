"""E2E-Release-Regression über das echte ``MainWindow`` (#644, Epic #639).

Fährt das in #595 geforderte Szenario end-to-end durch das MainWindow –
**nicht** über einen Modul-Kurzschluss: Bild öffnen → Höhenkarte erzeugen →
3D-Vorschau aktivieren (headless: dokumentierter Fallback) → Höhen-Operation +
Undo/Redo → Projekt speichern/wieder laden. Geprüft werden der 3D-Fallback-
Zweig, die Nicht-Mutation der Höhendaten durch den 2D↔3D-Wechsel und die
**bitgenaue** 16-Bit-Payload über Undo/Redo und den ``.bgrproj``-Roundtrip
(#587/#588).

Läuft headless/offscreen deterministisch (Marker ``ui_smoke`` → im CI-Gate).
Auf einem Self-hosted Runner mit echtem GL erreicht dasselbe Szenario den
Ready-Zweig – gesteuert nur über die Umgebung, ohne Testcode-Fork. Ist
``ABNAHME_EVIDENCE_DIR`` gesetzt (Abnahme-Workflow), wird zusätzlich ein
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
from bgremover.project_io import load_project, save_project
from bgremover.project_model import LayerKind, LayerRole

pytestmark = pytest.mark.ui_smoke


def _gradient(size: int = 16) -> Image.Image:
    """Unterscheidbares Farbmotiv (horizontaler Verlauf) für reproduzierbare Höhen."""
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for x in range(size):
        for y in range(size):
            px[x, y] = (x * 16 % 256, y * 16 % 256, (x + y) * 8 % 256, 255)
    return img


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


def _emit_evidence(status: str, notes: list[str]) -> None:
    """Evidenz-JSON nach Vertrag #640 schreiben, wenn im Abnahme-Workflow."""
    target = os.environ.get("ABNAHME_EVIDENCE_DIR")
    if not target:
        return
    out = Path(target)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": 1,
        "kind": "abnahme-e2e",
        "status": status,
        "scenario": "open->height->3d->op->undo/redo->save/open",
        "commit_sha": os.environ.get("GITHUB_SHA", "unbekannt"),
        "erzeugt_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hinweise": notes,
    }
    (out / "e2e-evidenz.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )


def _run_scenario(win: MainWindow, tmp_path: Path) -> list[str]:
    notes: list[str] = []

    # 1) Bild öffnen → genau eine COLOR-Ebene.
    win._canvas.apply_loaded_image(_gradient(), str(tmp_path / "src.png"))
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

    # 3) 3D-Vorschau aktivieren – headless: dokumentierter Fallback, kein Crash.
    win._set_preview3d_mode(True)
    state = win._relief3d_view.state
    assert state in {"unavailable", "empty", "loading"}, f"unerwarteter 3D-Zustand: {state}"
    # 2D↔3D-Wechsel mutiert die Höhendaten nicht.
    assert _payload_hash(win) == hash_after_generate
    win._set_preview3d_mode(False)
    assert win._canvas_stack.currentIndex() == 0
    assert _payload_hash(win) == hash_after_generate
    notes.append(f"3D-Fallback headless erreicht (Zustand: {state}), Höhendaten unverändert.")

    # 4) Höhen-Operation anwenden → Undo → Redo (bitgenau, #587).
    win._canvas.apply_height_op(lambda f: height_ops.quantize(f, 4))
    hash_after_op = _payload_hash(win)
    assert hash_after_op != hash_after_generate
    win._canvas.undo()
    assert _payload_hash(win) == hash_after_generate, "Undo nicht bitgenau"
    win._canvas.redo()
    assert _payload_hash(win) == hash_after_op, "Redo nicht bitgenau"
    notes.append("Höhen-Op + Undo/Redo bitgenau.")

    # 5) Projekt speichern (v2) und wieder laden – Payload bitgenau, Struktur gleich.
    path = tmp_path / "regression.bgrproj"
    save_project(win._canvas.project, str(path))
    before = win._canvas.project
    reloaded = load_project(str(path))
    assert [(layer.kind, layer.role, layer.name) for layer in reloaded.layers] == [
        (layer.kind, layer.role, layer.name) for layer in before.layers
    ]
    reloaded_active = reloaded.active_layer()
    assert reloaded_active is not None and reloaded_active.kind is LayerKind.HEIGHT
    assert reloaded_active.height_data is not None
    rd = hashlib.sha256()
    rd.update(reloaded_active.height_data.values.tobytes())
    rd.update(reloaded_active.height_data.coverage.tobytes())
    assert rd.hexdigest() == hash_after_op, "Payload nach Save/Open nicht bitgenau"
    notes.append("Save/Open (v2) bitgenau, Ebenenstruktur wertgleich.")
    return notes


def test_e2e_release_regression(qapp, tmp_path) -> None:
    win = MainWindow()
    try:
        notes = _run_scenario(win, tmp_path)
    except Exception as exc:  # noqa: BLE001 - Evidenz auch bei Fehlschlag schreiben.
        _emit_evidence("fehlgeschlagen", [f"Abbruch: {exc}"])
        raise
    else:
        _emit_evidence("bestanden", notes)
    finally:
        win.close()
