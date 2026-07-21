#!/usr/bin/env python3
"""Evidenz-Aggregation und Abschlussmatrix der Release-Abnahme (#646, Epic #639).

Sammelt die von den Plattform-Jobs hochgeladenen Evidenz-Artefakte, validiert
sie gegen den Vertrag aus #640 und erzeugt eine Abschlussmatrix: je
Abnahmekriterium der Zustand (erfüllt / fehlgeschlagen / fehlt / pausiert /
unbewertet) mit Nachweis und GL-Provenance. Der pausierte Linux-x86_64-Pfad
erscheint explizit als „pausiert", fehlende Artefakte als „fehlt" – keine
stillen Lücken. Die Go-/No-Go-Entscheidung bleibt ein menschlicher Schritt.

Qt-frei und ohne Netz; die Vision-Vorbewertung (``abnahme_vision_check.py``)
liefert optionale Screenshot-Verdikte, die hier nur eingebettet werden.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Erwartete Plattform-Evidenzen und ihr Matrix-Kriterium.
EXPECTED_PLATFORMS: dict[str, str] = {
    "macos-arm64": "macOS arm64: DMG-Smoke + Retina",
    "linux-arm64": "Linux aarch64: AppImage/.deb-Smoke",
}
PAUSED_PLATFORM = "linux-x86_64"
PAUSED_LABEL = "Linux x86_64: Hardware-Smoke"

# Pflichtfelder des Evidenzvertrags (#640).
REQUIRED_FIELDS = (
    "schema", "kind", "platform", "status", "commit_sha", "quelle",
    "artefakte", "umgebung", "erzeugt_am",
)


@dataclass(frozen=True)
class MatrixRow:
    """Eine Zeile der Abschlussmatrix."""

    kriterium: str
    status: str  # erfuellt | fehlgeschlagen | fehlt | pausiert | unbewertet
    nachweis: str
    provenance: str
    hinweis: str


def load_evidence(root: Path) -> dict[str, dict[str, Any]]:
    """Alle ``evidenz.json`` unter *root* laden, geschlüsselt nach ``platform``."""
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("evidenz.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        platform = str(data.get("platform", path.parent.name))
        found[platform] = data
    return found


def load_e2e(root: Path) -> dict[str, Any] | None:
    """Optionale E2E-Evidenz (#644) laden, falls vorhanden."""
    for path in sorted(root.rglob("e2e-evidenz.json")):
        try:
            return json.loads(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
        except (json.JSONDecodeError, OSError):
            continue
    return None


def load_vision(root: Path) -> list[dict[str, Any]]:
    """Optionale Vision-Verdikte (#646) laden (leer, wenn keine)."""
    for path in sorted(root.rglob("vision-verdikte.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return list(data.get("verdikte", []))
        except (json.JSONDecodeError, OSError):
            continue
    return []


def _vision_row(verdicts: list[dict[str, Any]]) -> MatrixRow:
    """Screenshots-Zeile aus den Vision-Verdikten zusammenfassen."""
    if not verdicts:
        # Vision ist fail-safe/beratend: keine Verdikte blockiert nie (kein GPU/
        # kein API-Zugang ist zulässig). Nur ``nicht_erfuellt`` blockiert (s. u.).
        return MatrixRow(
            "Screenshots (Vision-Vorbewertung)", "unbewertet", "—", "—",
            "Keine bewertbaren Screenshots (beratend, nicht blockierend).",
        )
    counts = {"erfuellt": 0, "nicht_erfuellt": 0, "unsicher": 0, "unbewertet": 0}
    for v in verdicts:
        counts[str(v.get("verdict", "unbewertet"))] = counts.get(
            str(v.get("verdict", "unbewertet")), 0) + 1
    if counts["nicht_erfuellt"]:
        status = "fehlgeschlagen"
    elif counts["unsicher"]:
        status = "unbewertet"
    elif counts["erfuellt"] and not counts["unbewertet"]:
        status = "erfuellt"
    else:
        status = "unbewertet"
    note = (f"{counts['erfuellt']}✓ / {counts['nicht_erfuellt']}✗ / "
            f"{counts['unsicher']}? / {counts['unbewertet']}—")
    return MatrixRow("Screenshots (Vision-Vorbewertung)", status, f"{len(verdicts)} Kriterien",
                     "—", note)


def validate_evidence(evidence: dict[str, Any]) -> list[str]:
    """Fehlende Pflichtfelder des Vertrags zurückgeben (leer = gültig)."""
    return [field for field in REQUIRED_FIELDS if field not in evidence]


def _status_from_evidence(evidence: dict[str, Any]) -> str:
    raw = str(evidence.get("status", ""))
    if raw == "bestanden":
        return "erfuellt"
    if raw == "fehlgeschlagen":
        return "fehlgeschlagen"
    return "unbewertet"  # platzhalter o. Ä. → nicht als erfüllt werten


def build_matrix(
    evidences: dict[str, dict[str, Any]],
    *,
    x86_64_enabled: bool = False,
    e2e: dict[str, Any] | None = None,
    vision: list[dict[str, Any]] | None = None,
) -> list[MatrixRow]:
    """Abschlussmatrix aus den gesammelten Evidenzen bauen."""
    rows: list[MatrixRow] = []
    for platform, kriterium in EXPECTED_PLATFORMS.items():
        ev = evidences.get(platform)
        if ev is None:
            rows.append(MatrixRow(kriterium, "fehlt", "—", "—", "Kein Evidenz-Artefakt."))
            continue
        missing = validate_evidence(ev)
        note = "" if not missing else f"Vertragsverstoß: fehlende Felder {missing}"
        status = "unbewertet" if missing else _status_from_evidence(ev)
        rows.append(MatrixRow(
            kriterium, status, "evidenz.json",
            str(ev.get("gl_provenance") or "—"), note,
        ))

    # Pausierter x86_64-Pfad: explizit sichtbar, nie stille Lücke.
    px = evidences.get(PAUSED_PLATFORM)
    if x86_64_enabled and px is not None:
        status = _status_from_evidence(px)
        rows.append(MatrixRow(
            PAUSED_LABEL, status, "evidenz.json", str(px.get("gl_provenance") or "—"), "",
        ))
    else:
        rows.append(MatrixRow(
            PAUSED_LABEL, "pausiert", "—", "—",
            "Pausiert (kein GPU-Zugang) – siehe RELEASE_AUTOMATION.md §5.",
        ))

    if e2e is not None:
        status = "erfuellt" if str(e2e.get("status")) == "bestanden" else "fehlgeschlagen"
        rows.append(MatrixRow(
            "E2E-Regression (Projekt→HEIGHT→3D→Undo/Save)", status,
            "e2e-evidenz.json", "—", "",
        ))
    else:
        rows.append(MatrixRow(
            "E2E-Regression (Projekt→HEIGHT→3D→Undo/Save)", "fehlt", "—", "—",
            "Keine E2E-Evidenz.",
        ))

    rows.append(_vision_row(vision or []))
    return rows


def has_blocking_gaps(rows: list[MatrixRow]) -> bool:
    """Ob die Matrix blockierende Lücken enthält (nicht erfüllt/fehlt, außer pausiert)."""
    return any(r.status in ("fehlgeschlagen", "fehlt") for r in rows)


def render_markdown(rows: list[MatrixRow], *, commit_sha: str = "unbekannt") -> str:
    """Abschlussmatrix als Markdown-Protokoll rendern."""
    icon = {
        "erfuellt": "✅", "fehlgeschlagen": "❌", "fehlt": "⚠️",
        "pausiert": "⏸️", "unbewertet": "❓",
    }
    lines = [
        "## Release-Abnahme – Abschlussmatrix",
        "",
        f"Commit: `{commit_sha}`. Automatisiert aus den Evidenz-Artefakten (Epic #639).",
        "",
        "| Kriterium | Status | Nachweis | GL-Provenance | Hinweis |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        mark = f"{icon.get(r.status, '')} {r.status}".strip()
        lines.append(
            f"| {r.kriterium} | {mark} | {r.nachweis} | `{r.provenance}` | {r.hinweis} |"
        )
    lines += [
        "",
        "> Go/No-Go entscheidet ein Mensch auf Basis dieser Matrix. "
        "Pausierte Kriterien gelten als **offen deklariert**, nicht erfüllt.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", type=Path, required=True,
                        help="Verzeichnis mit heruntergeladenen abnahme-*-Artefakten.")
    parser.add_argument("--output", type=Path, required=True, help="Ziel-Markdown der Matrix.")
    parser.add_argument("--commit-sha", default="unbekannt")
    parser.add_argument("--x86-64-enabled", action="store_true")
    args = parser.parse_args(argv)

    evidences = load_evidence(args.artifacts_dir)
    e2e = load_e2e(args.artifacts_dir)
    vision = load_vision(args.artifacts_dir)
    rows = build_matrix(
        evidences, x86_64_enabled=args.x86_64_enabled, e2e=e2e, vision=vision,
    )
    markdown = render_markdown(rows, commit_sha=args.commit_sha)
    args.output.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"\nMatrix geschrieben: {args.output}")
    # Blockierende Lücken sind ein Signal, kein harter Fehler (Mensch entscheidet).
    return 0


if __name__ == "__main__":
    sys.exit(main())
