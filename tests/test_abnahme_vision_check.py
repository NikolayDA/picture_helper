"""Tests der Vision-Vorbewertung (#646) – fail-safe, ohne echten API-Aufruf."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "abnahme_vision_check", ROOT / "scripts" / "abnahme_vision_check.py"
)
assert _SPEC is not None and _SPEC.loader is not None
vc = importlib.util.module_from_spec(_SPEC)
sys.modules["abnahme_vision_check"] = vc
_SPEC.loader.exec_module(vc)


def test_criteria_selection_by_filename() -> None:
    assert vc.criteria_for("76_function_preview3d_ready.png") == vc.CRITERIA["preview3d_ready"]
    assert vc.criteria_for("30_dialog_retina.png") == vc.CRITERIA["retina"]
    assert vc.criteria_for("02_main_loaded_selection.png") == vc.CRITERIA["hauptfenster"]
    assert vc.criteria_for("99_unknown.png") == ()


def test_no_criteria_returns_empty() -> None:
    assert vc.evaluate_screenshot(b"x", "99_unknown.png", vision_fn=lambda *a: "{}") == []


def test_good_response_maps_to_verdicts() -> None:
    def fake(b64: str, media: str, prompt: str) -> str:
        return json.dumps({"ergebnisse": [
            {"criterion": "relief_sichtbar", "verdict": "erfuellt", "begruendung": "ok"},
            {"criterion": "controls_sichtbar", "verdict": "nicht_erfuellt", "begruendung": "fehlt"},
        ]})

    results = vc.evaluate_screenshot(b"img", "76_function_preview3d_ready.png", vision_fn=fake)
    verdicts = {r.criterion: r.verdict for r in results}
    assert verdicts == {"relief_sichtbar": "erfuellt", "controls_sichtbar": "nicht_erfuellt"}


def test_api_error_degrades_to_unbewertet() -> None:
    def boom(*_a: object) -> str:
        raise RuntimeError("kein Netz")

    results = vc.evaluate_screenshot(b"img", "02_main_loaded_selection.png", vision_fn=boom)
    assert results and all(r.verdict == "unbewertet" for r in results)


def test_invalid_json_degrades_to_unbewertet() -> None:
    results = vc.evaluate_screenshot(
        b"img", "02_main_loaded_selection.png", vision_fn=lambda *a: "kein json",
    )
    assert all(r.verdict == "unbewertet" for r in results)


def test_missing_criterion_in_response_is_unbewertet() -> None:
    # Antwort lässt ein Kriterium aus → dieses wird unbewertet.
    def partial(*_a: object) -> str:
        return json.dumps({"ergebnisse": [
            {"criterion": "fenster_sichtbar", "verdict": "erfuellt", "begruendung": "ok"},
        ]})

    results = vc.evaluate_screenshot(b"img", "02_main_loaded_selection.png", vision_fn=partial)
    by = {r.criterion: r.verdict for r in results}
    assert by["fenster_sichtbar"] == "erfuellt"
    assert by["workflow_leiste"] == "unbewertet"


def test_default_vision_fn_without_key_raises(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Ohne Key wirft der Default-Aufruf → evaluate_screenshot fängt ab (unbewertet).
    results = vc.evaluate_screenshot(b"img", "02_main_loaded_selection.png")
    assert results and all(r.verdict == "unbewertet" for r in results)


def test_scan_and_evaluate_only_matching(tmp_path: Path) -> None:
    (tmp_path / "02_main_loaded_selection.png").write_bytes(b"img")
    (tmp_path / "76_function_preview3d_ready.png").write_bytes(b"img")
    (tmp_path / "99_unknown.png").write_bytes(b"img")   # kein Katalog → ignoriert
    (tmp_path / "artefakt.AppImage").write_bytes(b"bin")  # kein Bild

    verdicts = vc.scan_and_evaluate(tmp_path, vision_fn=lambda *a: "kein json")
    screenshots = {v["screenshot"] for v in verdicts}
    assert screenshots == {"02_main_loaded_selection.png", "76_function_preview3d_ready.png"}
    assert all(v["verdict"] == "unbewertet" for v in verdicts)  # kein JSON → fail-safe


def test_vision_main_writes_json(tmp_path: Path) -> None:
    (tmp_path / "02_main_loaded_selection.png").write_bytes(b"img")
    out = tmp_path / "vision-verdikte.json"
    rc = vc.main(["--screenshots-dir", str(tmp_path), "--output", str(out)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["verdikte"] and data["verdikte"][0]["screenshot"] == "02_main_loaded_selection.png"
