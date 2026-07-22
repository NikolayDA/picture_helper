#!/usr/bin/env python3
"""Vision-Vorbewertung der Abnahme-Screenshots (#646, Epic #639).

Bewertet die auf echter Hardware aufgenommenen Screenshots gegen einen
Kriterienkatalog über die Claude API (Vision, Modell ``claude-opus-4-8``). Die
Bewertung ist ein **fail-safe Zusatz**: ohne ``ANTHROPIC_API_KEY``, ohne
installiertes ``anthropic``-SDK oder bei API-/Parsing-Fehler wird jedes
Kriterium als ``unbewertet`` markiert – der Abnahme-Lauf scheitert daran nie.
``unsicher``/``nicht_erfuellt`` blockieren nicht automatisch; sie werden in der
Matrix (#646, ``abnahme_aggregate.py``) sichtbar, die Go-/No-Go-Entscheidung
bleibt beim Menschen.

Der eigentliche API-Aufruf ist in ``_default_vision_fn`` isoliert (nicht im
CI-Test ausführbar); die Katalog-/Verdikt-/Fail-safe-Logik ist über eine
injizierbare ``vision_fn`` Qt-frei getestet.
"""
from __future__ import annotations

import base64
import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

MODEL = "claude-opus-4-8"

# Erlaubte Verdikte je Kriterium.
VERDICTS = ("erfuellt", "nicht_erfuellt", "unsicher", "unbewertet")

# Kriterienkatalog je Screenshot-Typ (Daten, kein Code). Der Screenshot-Typ
# wird aus dem Dateinamen abgeleitet (siehe ``criteria_for``).
CRITERIA: dict[str, tuple[tuple[str, str], ...]] = {
    "hauptfenster": (
        ("fenster_sichtbar", "Das App-Fenster ist sichtbar und nicht leer/schwarz."),
        ("workflow_leiste", "Die Workflow-Schrittleiste ist erkennbar."),
    ),
    "preview3d_ready": (
        ("relief_sichtbar", "Eine 3D-Reliefoberfläche ist erkennbar, kein schwarzes Viewport."),
        ("controls_sichtbar", "Die 3D-Inspector-Bedienelemente (Qualität/Licht) sind sichtbar."),
    ),
    "retina": (
        ("scharf", "Die UI ist scharf gerendert, keine sichtbaren Skalierungsartefakte."),
    ),
}

# Injektionspunkt für Tests: (bild_b64, medientyp, prompt) → JSON-Text der Antwort.
VisionFn = Callable[[str, str, str], str]


@dataclass(frozen=True)
class CriterionVerdict:
    """Bewertung eines Einzelkriteriums."""

    criterion: str
    verdict: str
    begruendung: str


def criteria_for(filename: str) -> tuple[tuple[str, str], ...]:
    """Kriterienliste anhand des Screenshot-Dateinamens (leere Liste = kein Katalog)."""
    name = filename.lower()
    if "preview3d" in name and ("ready" in name or "adjusted" in name or "controls" in name):
        return CRITERIA["preview3d_ready"]
    if "retina" in name or "dpi" in name:
        return CRITERIA["retina"]
    if "main" in name or "hauptfenster" in name or "loaded" in name:
        return CRITERIA["hauptfenster"]
    return ()


def _media_type(filename: str) -> str:
    return "image/jpeg" if filename.lower().endswith((".jpg", ".jpeg")) else "image/png"


def _build_prompt(criteria: tuple[tuple[str, str], ...]) -> str:
    lines = [
        "Du bewertest einen Screenshot einer Desktop-App gegen Kriterien.",
        "Antworte NUR mit JSON: {\"ergebnisse\": [{\"criterion\": id, "
        "\"verdict\": \"erfuellt\"|\"nicht_erfuellt\"|\"unsicher\", "
        "\"begruendung\": kurz}]}.",
        "Kriterien:",
    ]
    lines += [f"- {cid}: {desc}" for cid, desc in criteria]
    return "\n".join(lines)


def _unrated(criteria: tuple[tuple[str, str], ...], reason: str) -> list[CriterionVerdict]:
    return [CriterionVerdict(cid, "unbewertet", reason) for cid, _ in criteria]


def _parse_response(text: str, criteria: tuple[tuple[str, str], ...]) -> list[CriterionVerdict]:
    """Modellantwort robust zu Verdikten parsen; alles Unklare → unbewertet."""
    try:
        data = json.loads(text)
        by_id = {str(e["criterion"]): e for e in data.get("ergebnisse", [])}
    except (json.JSONDecodeError, TypeError, KeyError, AttributeError):
        return _unrated(criteria, "Antwort nicht als JSON interpretierbar.")
    results: list[CriterionVerdict] = []
    for cid, _desc in criteria:
        entry = by_id.get(cid)
        if entry is None:
            results.append(CriterionVerdict(cid, "unbewertet", "Kein gültiges Verdikt geliefert."))
            continue
        verdict = str(entry.get("verdict", ""))
        if verdict not in ("erfuellt", "nicht_erfuellt", "unsicher"):
            results.append(CriterionVerdict(cid, "unbewertet", "Kein gültiges Verdikt geliefert."))
        else:
            results.append(
                CriterionVerdict(cid, verdict, str(entry.get("begruendung", "")))
            )
    return results


def evaluate_screenshot(
    image_bytes: bytes, filename: str, vision_fn: VisionFn | None = None,
) -> list[CriterionVerdict]:
    """Einen Screenshot gegen seinen Katalog bewerten (fail-safe)."""
    criteria = criteria_for(filename)
    if not criteria:
        return []
    fn = vision_fn or _default_vision_fn
    if fn is None:  # kein SDK/Key → gesamter Satz unbewertet
        return _unrated(criteria, "Vision nicht verfügbar (kein API-Zugang).")
    try:
        b64 = base64.standard_b64encode(image_bytes).decode("ascii")
        text = fn(b64, _media_type(filename), _build_prompt(criteria))
    except Exception as exc:  # noqa: BLE001 - fail-safe: nie propagieren
        return _unrated(criteria, f"Vision-Aufruf fehlgeschlagen: {type(exc).__name__}")
    return _parse_response(text, criteria)


def _default_vision_fn(image_b64: str, media_type: str, prompt: str) -> str:  # pragma: no cover
    """Realer Claude-API-Vision-Aufruf (nur mit Key + SDK; im CI nicht ausgeführt)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY nicht gesetzt")
    import anthropic  # lazy: keine Projekt-Pflichtabhängigkeit

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": media_type, "data": image_b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return next((b.text for b in response.content if b.type == "text"), "")


def scan_and_evaluate(
    screenshots_dir: Path, vision_fn: VisionFn | None = None,
) -> list[dict[str, str]]:
    """Alle bewertbaren Screenshots im Verzeichnis bewerten (fail-safe)."""
    from pathlib import Path as _Path

    root = _Path(screenshots_dir)
    verdicts: list[dict[str, str]] = []
    for path in sorted(root.rglob("*.png")) + sorted(root.rglob("*.jpg")):
        if not criteria_for(path.name):
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        for cv in evaluate_screenshot(data, path.name, vision_fn):
            verdicts.append({
                "screenshot": path.name, "criterion": cv.criterion,
                "verdict": cv.verdict, "begruendung": cv.begruendung,
            })
    return verdicts


def main(argv: list[str] | None = None) -> int:
    import argparse
    from pathlib import Path as _Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshots-dir", type=_Path, required=True)
    parser.add_argument("--output", type=_Path, required=True,
                        help="Ziel-JSON mit den Verdikten (vision-verdikte.json).")
    args = parser.parse_args(argv)

    verdicts = scan_and_evaluate(args.screenshots_dir)
    args.output.write_text(
        json.dumps({"verdikte": verdicts}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    rated = sum(1 for v in verdicts if v["verdict"] != "unbewertet")
    print(f"Vision: {len(verdicts)} Kriterien, {rated} bewertet → {args.output}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
