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
import math
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
LIVE_GL_SCENARIOS = ("HEIGHT16-1MP", "HEIGHT16-16MP", "HEIGHT16-40MP")
LIVE_GL_METRICS = (
    "gl_upload_ms", "gl_first_frame_ms", "gl_peak_mb",
    "gl_frame_ms_p50", "gl_frame_ms_p95",
)

# Pflichtfelder des Evidenzvertrags (#640; ``waechter_ergebnisse`` seit dem
# #642-Nachtrag: strukturierte Wächter-Ergebnisse je Startphase/Artefaktklasse).
REQUIRED_FIELDS = (
    "schema", "kind", "platform", "status", "commit_sha", "quelle",
    "artefakte", "umgebung", "gl_provenance", "waechter_ergebnisse",
    "erzeugt_am", "hinweise",
)
E2E_REQUIRED_FIELDS = (
    "schema", "kind", "platform", "status", "scenario", "commit_sha",
    "native_3d_required", "native_3d_state", "erzeugt_am", "hinweise",
)


@dataclass(frozen=True)
class MatrixRow:
    """Eine Zeile der Abschlussmatrix."""

    kriterium: str
    status: str  # erfuellt | fehlgeschlagen | fehlt | pausiert | unbewertet
    nachweis: str
    provenance: str
    hinweis: str


def _platform_from_path(path: Path) -> str:
    for part in reversed(path.parts):
        if part.startswith("abnahme-"):
            return part.removeprefix("abnahme-")
    return path.parent.name


def load_evidence(root: Path) -> dict[str, dict[str, Any]]:
    """Alle ``evidenz.json`` unter *root* laden, geschlüsselt nach ``platform``."""
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("evidenz.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        platform = str(data.get("platform") or _platform_from_path(path))
        found[platform] = data
    return found


def load_e2e(root: Path) -> dict[str, dict[str, Any]]:
    """E2E-Evidenz (#644) je Plattform laden."""
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("e2e-evidenz.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        platform = str(data.get("platform") or _platform_from_path(path))
        found[platform] = data
    return found


def load_live_gl(root: Path) -> dict[str, dict[str, Any]]:
    """Jüngstes ``preview3d-live``-Ergebnis je Plattform laden."""
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*.json")):
        if path.parent.name != "preview3d-live":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("suite") != "preview3d-live":
            continue
        platform = str(data.get("platform") or _platform_from_path(path))
        found[platform] = data
    return found


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
    """Vertragsverstöße der Plattform-Evidenz zurückgeben."""
    issues = [field for field in REQUIRED_FIELDS if field not in evidence]
    if evidence.get("schema") != 1:
        issues.append("schema!=1")
    if evidence.get("kind") != "abnahme-evidenz":
        issues.append("kind!=abnahme-evidenz")
    if evidence.get("status") != "platzhalter" and not str(
        evidence.get("gl_provenance") or ""
    ).strip():
        issues.append("gl_provenance leer")
    if evidence.get("status") != "platzhalter" and not evidence.get("waechter_ergebnisse"):
        issues.append("waechter_ergebnisse leer")
    return issues


def _commit_hashes_match(left: object, right: object) -> bool:
    """Gleichen Commit trotz Git-Kurzform erkennen, ohne beliebige Präfixe zu akzeptieren."""
    first = str(left or "").strip().lower()
    second = str(right or "").strip().lower()
    if first == second:
        return bool(first)
    if min(len(first), len(second)) < 7:
        return False
    if any(char not in "0123456789abcdef" for char in first + second):
        return False
    shorter, longer = sorted((first, second), key=len)
    return longer.startswith(shorter)


def validate_e2e(
    evidence: dict[str, Any], *, platform: str, commit_sha: str,
) -> list[str]:
    """E2E-Vertrag inklusive des nativen Ready-Nachweises validieren."""
    issues = [field for field in E2E_REQUIRED_FIELDS if field not in evidence]
    if evidence.get("schema") != 1:
        issues.append("schema!=1")
    if evidence.get("kind") != "abnahme-e2e":
        issues.append("kind!=abnahme-e2e")
    if evidence.get("platform") != platform:
        issues.append(f"platform!={platform}")
    if commit_sha and not _commit_hashes_match(evidence.get("commit_sha"), commit_sha):
        issues.append("commit_sha abweichend")
    return issues


def validate_live_gl(
    result: dict[str, Any], *, platform: str, commit_sha: str,
) -> list[str]:
    """Live-GL-Ergebnis gegen Suite-, Provenance- und Metrikvertrag prüfen."""
    issues: list[str] = []
    if result.get("schema") != 3:
        issues.append("schema!=3")
    if result.get("suite") != "preview3d-live":
        issues.append("suite!=preview3d-live")
    if result.get("platform") != platform:
        issues.append(f"platform!={platform}")
    if commit_sha and not _commit_hashes_match(result.get("git_commit"), commit_sha):
        issues.append("git_commit abweichend")
    environment = result.get("environment")
    if not isinstance(environment, dict) or not str(
        environment.get("gl_provenance") or ""
    ).strip():
        issues.append("gl_provenance leer")
    formats = result.get("formats")
    if not isinstance(formats, dict):
        return [*issues, "formats fehlt"]
    for scenario in LIVE_GL_SCENARIOS:
        metrics = formats.get(scenario)
        if not isinstance(metrics, dict):
            issues.append(f"{scenario} fehlt")
            continue
        for metric in LIVE_GL_METRICS:
            value = metrics.get(metric)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or float(value) < 0.0
            ):
                issues.append(f"{scenario}.{metric} ungültig")
    return issues


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
    e2e: dict[str, dict[str, Any]] | None = None,
    live_gl: dict[str, dict[str, Any]] | None = None,
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
        evidence_status = _status_from_evidence(ev)
        status = (
            evidence_status
            if evidence_status == "fehlgeschlagen" or not missing
            else "unbewertet"
        )
        rows.append(MatrixRow(
            kriterium, status, "evidenz.json",
            str(ev.get("gl_provenance") or "—"), note,
        ))

    # Pausierter x86_64-Pfad: explizit sichtbar, nie stille Lücke.
    px = evidences.get(PAUSED_PLATFORM)
    if x86_64_enabled:
        if px is None:
            rows.append(MatrixRow(
                PAUSED_LABEL, "fehlt", "—", "—", "Kein Evidenz-Artefakt.",
            ))
        else:
            missing = validate_evidence(px)
            evidence_status = _status_from_evidence(px)
            status = (
                evidence_status
                if evidence_status == "fehlgeschlagen" or not missing
                else "unbewertet"
            )
            note = "" if not missing else f"Vertragsverstoß: {missing}"
            rows.append(MatrixRow(
                PAUSED_LABEL, status, "evidenz.json",
                str(px.get("gl_provenance") or "—"), note,
            ))
    else:
        rows.append(MatrixRow(
            PAUSED_LABEL, "pausiert", "—", "—",
            "Pausiert (kein GPU-Zugang) – siehe RELEASE_AUTOMATION.md §5.",
        ))

    active_platforms = [*EXPECTED_PLATFORMS]
    if x86_64_enabled:
        active_platforms.append(PAUSED_PLATFORM)
    e2e = e2e or {}
    live_gl = live_gl or {}
    for platform in active_platforms:
        platform_evidence = evidences.get(platform)
        commit_sha = str((platform_evidence or {}).get("commit_sha") or "")

        e2e_result = e2e.get(platform)
        e2e_label = f"{platform}: Native 3D-E2E (Projekt→HEIGHT→Undo/Save)"
        if e2e_result is None:
            rows.append(MatrixRow(
                e2e_label, "fehlt", "—", "—", "Keine E2E-Evidenz.",
            ))
        else:
            issues = validate_e2e(
                e2e_result, platform=platform, commit_sha=commit_sha,
            )
            if e2e_result.get("status") != "bestanden":
                status = "fehlgeschlagen"
                note = (
                    f"E2E-Szenario fehlgeschlagen; Vertragsverstoß: {issues}"
                    if issues else "E2E-Szenario fehlgeschlagen."
                )
            elif issues:
                status = "unbewertet"
                note = f"Vertragsverstoß: {issues}"
            elif (
                e2e_result.get("native_3d_required") is not True
                or e2e_result.get("native_3d_state") != "ready"
            ):
                status = "fehlgeschlagen"
                note = "Kein nativer 3D-Ready-Nachweis."
            else:
                status = "erfuellt"
                note = "Nativer GL-Viewer ready und Geometrie gerendert."
            rows.append(MatrixRow(
                e2e_label, status, "e2e-evidenz.json", "—", note,
            ))

        live_result = live_gl.get(platform)
        live_label = f"{platform}: Live-GL-Performance"
        if live_result is None:
            rows.append(MatrixRow(
                live_label, "fehlt", "—", "—", "Kein preview3d-live-Ergebnis.",
            ))
        else:
            issues = validate_live_gl(
                live_result, platform=platform, commit_sha=commit_sha,
            )
            environment = live_result.get("environment")
            provenance = str(
                environment.get("gl_provenance") or "—"
                if isinstance(environment, dict) else "—"
            )
            rows.append(MatrixRow(
                live_label, "unbewertet" if issues else "erfuellt",
                "preview3d-live/*.json", provenance,
                f"Vertragsverstoß: {issues}" if issues else "Alle 5 Metriken für 1/16/40 MP.",
            ))

    rows.append(_vision_row(vision or []))
    return rows


def has_blocking_gaps(rows: list[MatrixRow]) -> bool:
    """Blockierende Lücken; nur die beratende Vision darf unbewertet bleiben."""
    return any(
        r.status in ("fehlgeschlagen", "fehlt")
        or (
            r.status == "unbewertet"
            and r.kriterium != "Screenshots (Vision-Vorbewertung)"
        )
        for r in rows
    )


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
    live_gl = load_live_gl(args.artifacts_dir)
    vision = load_vision(args.artifacts_dir)
    rows = build_matrix(
        evidences, x86_64_enabled=args.x86_64_enabled, e2e=e2e,
        live_gl=live_gl, vision=vision,
    )
    markdown = render_markdown(rows, commit_sha=args.commit_sha)
    args.output.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"\nMatrix geschrieben: {args.output}")
    # Blockierende Lücken sind ein Signal, kein harter Fehler (Mensch entscheidet).
    return 0


if __name__ == "__main__":
    sys.exit(main())
