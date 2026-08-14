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
import re
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
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


# Vollautomatisierter Lauf ohne manuellen Tester (#685-Review): das
# "Testperson"-Feld der Abnahmematrix macht das explizit statt es leer zu
# lassen (eine leere Zelle könnte wie eine vergessene Angabe aussehen).
AUTOMATED_TESTPERSON = "automatisiert (kein manueller Tester)"


@dataclass(frozen=True)
class MatrixRow:
    """Eine Zeile der Abschlussmatrix."""

    kriterium: str
    status: str  # erfuellt | fehlgeschlagen | fehlt | pausiert | unbewertet
    nachweis: str
    provenance: str
    hinweis: str
    geraet_os: str = "—"
    datum: str = "—"
    testperson: str = AUTOMATED_TESTPERSON
    nachweis_link: str = "—"


def _geraet_os(evidence: dict[str, Any] | None) -> str:
    """``Gerät/OS`` aus den Umgebungs-Pflichtfeldern (#640) ableiten."""
    if not evidence:
        return "—"
    umgebung = evidence.get("umgebung")
    if not isinstance(umgebung, dict):
        return "—"
    os_name = str(umgebung.get("os") or "").strip()
    runner = str(umgebung.get("runner") or "").strip()
    if runner and runner != "unbekannt":
        return f"{runner} ({os_name or 'unbekannt'})"
    return os_name or "—"


def _datum(evidence: dict[str, Any] | None, *, field: str = "erzeugt_am") -> str:
    """Nur das Datum (nicht die Uhrzeit) aus dem gegebenen Zeitstempelfeld
    extrahieren. Live-GL-Ergebnisse (``scripts/benchmark.py``) tragen ihren
    Zeitstempel unter ``timestamp`` statt ``erzeugt_am`` – daher der
    konfigurierbare Feldname (#685-Review, Codex)."""
    if not evidence:
        return "—"
    value = str(evidence.get(field) or "")
    return value[:10] if len(value) >= 10 else "—"


def _platform_from_path(path: Path) -> str:
    for part in reversed(path.parts):
        if part.startswith("abnahme-"):
            return part.removeprefix("abnahme-")
    return path.parent.name


def _attempt_from_path(path: Path, platform: str) -> int:
    pattern = re.compile(rf"^abnahme-{re.escape(platform)}-(\d+)$")
    for part in reversed(path.parts):
        match = pattern.fullmatch(part)
        if match:
            return int(match.group(1))
    return 0


def load_evidence(root: Path) -> dict[str, dict[str, Any]]:
    """Alle ``evidenz.json`` unter *root* laden, geschlüsselt nach ``platform``."""
    selected: dict[str, tuple[int, dict[str, Any]]] = {}
    for path in sorted(root.rglob("evidenz.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        platform = str(data.get("platform") or _platform_from_path(path))
        attempt = _attempt_from_path(path, platform)
        if platform not in selected or attempt >= selected[platform][0]:
            selected[platform] = (attempt, data)
    return {platform: item[1] for platform, item in selected.items()}


def load_e2e(root: Path) -> dict[str, dict[str, Any]]:
    """E2E-Evidenz (#644) je Plattform laden."""
    selected: dict[str, tuple[int, dict[str, Any]]] = {}
    for path in sorted(root.rglob("e2e-evidenz.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        platform = str(data.get("platform") or _platform_from_path(path))
        attempt = _attempt_from_path(path, platform)
        if platform not in selected or attempt >= selected[platform][0]:
            selected[platform] = (attempt, data)
    return {platform: item[1] for platform, item in selected.items()}


def load_live_gl(root: Path) -> dict[str, dict[str, Any]]:
    """Jüngstes ``preview3d-live``-Ergebnis je Plattform laden."""
    selected: dict[str, tuple[int, dict[str, Any]]] = {}
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
        attempt = _attempt_from_path(path, platform)
        if platform not in selected or attempt >= selected[platform][0]:
            selected[platform] = (attempt, data)
    return {platform: item[1] for platform, item in selected.items()}


def load_vision(root: Path) -> list[dict[str, Any]]:
    """Optionale Vision-Verdikte (#646) laden (leer, wenn keine)."""
    for path in sorted(root.rglob("vision-verdikte.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return list(data.get("verdikte", []))
        except (json.JSONDecodeError, OSError):
            continue
    return []


def _sanitize_cell(text: str, *, max_len: int = 90) -> str:
    """Freitext für eine Markdown-Tabellenzelle sichern (#781).

    Entfernt Zeilenumbrüche (brechen sonst die Tabellenzeile) und maskiert
    Pipe-Zeichen (trennen sonst Spalten); LLM-generierte Begründungen landen
    unbereinigt in ``begruendung`` und dürfen die Matrix nicht zerstören.
    Backslashes zuerst verdoppeln, sonst macht ein bereits vorhandenes
    ``\\|`` aus der Pipe-Maskierung ein escapetes ``\\`` gefolgt von einem
    wieder freien, trennenden ``|`` (Codex-Review #787).
    """
    flat = " ".join(text.split()).replace("\\", "\\\\").replace("|", "\\|")
    if len(flat) > max_len:
        flat = flat[: max_len - 1].rstrip() + "…"
    return flat


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
    # Details zu nicht erfüllten/unsicheren Kriterien direkt in der Matrix
    # zeigen (#781) – bislang stand nur die Zählung da, die Begründung lag
    # ausschließlich im separaten Vision-Verdikte-Artefakt.
    details = [
        f"{'✗' if v.get('verdict') == 'nicht_erfuellt' else '?'} "
        f"{_sanitize_cell(str(v.get('criterion', '?')), max_len=40)} "
        f"({_sanitize_cell(str(v.get('screenshot', '?')), max_len=40)})"
        + (f": {_sanitize_cell(str(v['begruendung']))}" if v.get("begruendung") else "")
        for v in verdicts
        if v.get("verdict") in ("nicht_erfuellt", "unsicher")
    ]
    if details:
        note += " — " + "; ".join(details)
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
    run_url: str = "—",
) -> list[MatrixRow]:
    """Abschlussmatrix aus den gesammelten Evidenzen bauen.

    ``run_url`` verlinkt jede Zeile auf den erzeugenden Workflow-Lauf (Logs/
    Screenshots liegen dort als Artefakte); "—", wenn kein Lauf bekannt ist
    (z. B. lokale Aufrufe außerhalb von CI, #685-Review).
    """
    rows: list[MatrixRow] = []
    for platform, kriterium in EXPECTED_PLATFORMS.items():
        ev = evidences.get(platform)
        if ev is None:
            rows.append(MatrixRow(
                kriterium, "fehlt", "—", "—", "Kein Evidenz-Artefakt.",
                nachweis_link=run_url,
            ))
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
            geraet_os=_geraet_os(ev), datum=_datum(ev), nachweis_link=run_url,
        ))

    # Pausierter x86_64-Pfad: explizit sichtbar, nie stille Lücke.
    px = evidences.get(PAUSED_PLATFORM)
    if x86_64_enabled:
        if px is None:
            rows.append(MatrixRow(
                PAUSED_LABEL, "fehlt", "—", "—", "Kein Evidenz-Artefakt.",
                nachweis_link=run_url,
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
                geraet_os=_geraet_os(px), datum=_datum(px), nachweis_link=run_url,
            ))
    else:
        rows.append(MatrixRow(
            PAUSED_LABEL, "pausiert", "—", "—",
            "Pausiert (kein GPU-Zugang) – siehe RELEASE_AUTOMATION.md §5.",
            nachweis_link=run_url,
        ))

    active_platforms = [*EXPECTED_PLATFORMS]
    if x86_64_enabled:
        active_platforms.append(PAUSED_PLATFORM)
    e2e = e2e or {}
    live_gl = live_gl or {}
    for platform in active_platforms:
        platform_evidence = evidences.get(platform)
        commit_sha = str((platform_evidence or {}).get("commit_sha") or "")
        # E2E-/Live-GL-Nachweise tragen kein eigenes ``umgebung`` (nicht Teil
        # ihres Vertrags) – dieselbe Plattform-Evidenz aus demselben Job liefert
        # Gerät/OS trotzdem verlässlich mit. Das Datum kommt dagegen bevorzugt
        # aus dem jeweils eigenen Zeitstempel (``erzeugt_am``/``timestamp``):
        # der Plattform-Evidenz-Zeitstempel entsteht *vor* Smoke/E2E/Live-GL,
        # ein UTC-Datumswechsel während des Jobs würde sonst ein falsches
        # Datum für diese später gelaufenen Kriterien zeigen (#685-Review, Codex).
        platform_geraet_os = _geraet_os(platform_evidence)
        platform_datum = _datum(platform_evidence)

        e2e_result = e2e.get(platform)
        e2e_label = f"{platform}: Native 3D-E2E (Projekt→HEIGHT→Undo/Save)"
        if e2e_result is None:
            rows.append(MatrixRow(
                e2e_label, "fehlt", "—", "—", "Keine E2E-Evidenz.",
                geraet_os=platform_geraet_os, datum=platform_datum, nachweis_link=run_url,
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
                geraet_os=platform_geraet_os,
                datum=_datum(e2e_result) if _datum(e2e_result) != "—" else platform_datum,
                nachweis_link=run_url,
            ))

        live_result = live_gl.get(platform)
        live_label = f"{platform}: Live-GL-Performance"
        if live_result is None:
            rows.append(MatrixRow(
                live_label, "fehlt", "—", "—", "Kein preview3d-live-Ergebnis.",
                geraet_os=platform_geraet_os, datum=platform_datum, nachweis_link=run_url,
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
            live_datum = _datum(live_result, field="timestamp")
            rows.append(MatrixRow(
                live_label, "unbewertet" if issues else "erfuellt",
                "preview3d-live/*.json", provenance,
                f"Vertragsverstoß: {issues}" if issues else "Alle 5 Metriken für 1/16/40 MP.",
                geraet_os=platform_geraet_os,
                datum=live_datum if live_datum != "—" else platform_datum,
                nachweis_link=run_url,
            ))

    rows.append(replace(_vision_row(vision or []), nachweis_link=run_url))
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


def build_acceptance_summary(
    rows: list[MatrixRow], *, commit_sha: str, x86_64_enabled: bool = False,
) -> dict[str, Any]:
    """Maschinenlesbare Plattformentscheidung fuer das Freigabemanifest (#744).

    Nur die drei technischen Pflichtzeilen je aktiver Plattform zaehlen. Die
    Vision-Vorbewertung bleibt wie im ADR festgelegt beratend. Linux x86_64
    ist in Policy-Version 1 explizit pausiert; eine spaetere Reaktivierung
    braucht bewusst einen Policy-Sprung im Freigabevertrag.
    """
    by_criterion = {row.kriterium: row for row in rows}
    platforms: dict[str, str] = {}
    for platform, smoke_label in EXPECTED_PLATFORMS.items():
        required = (
            smoke_label,
            f"{platform}: Native 3D-E2E (Projekt→HEIGHT→Undo/Save)",
            f"{platform}: Live-GL-Performance",
        )
        platforms[platform] = (
            "approved"
            if all(
                by_criterion.get(label) is not None
                and by_criterion[label].status == "erfuellt"
                for label in required
            )
            else "blocked"
        )
    if x86_64_enabled:
        required = (
            PAUSED_LABEL,
            f"{PAUSED_PLATFORM}: Native 3D-E2E (Projekt→HEIGHT→Undo/Save)",
            f"{PAUSED_PLATFORM}: Live-GL-Performance",
        )
        platforms[PAUSED_PLATFORM] = (
            "approved"
            if all(
                by_criterion.get(label) is not None
                and by_criterion[label].status == "erfuellt"
                for label in required
            )
            else "blocked"
        )
    else:
        platforms[PAUSED_PLATFORM] = "paused"
    return {
        "schema": 1,
        "kind": "release-acceptance-summary",
        "commit_sha": commit_sha,
        "platforms": platforms,
        "blocking": any(status == "blocked" for status in platforms.values()),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


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
        "| Kriterium | Status | Nachweis | GL-Provenance | Gerät/OS | Datum | "
        "Testperson | Link | Hinweis |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        mark = f"{icon.get(r.status, '')} {r.status}".strip()
        link = f"[Lauf]({r.nachweis_link})" if r.nachweis_link != "—" else "—"
        lines.append(
            f"| {r.kriterium} | {mark} | {r.nachweis} | `{r.provenance}` | "
            f"{r.geraet_os} | {r.datum} | {r.testperson} | {link} | {r.hinweis} |"
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
    parser.add_argument(
        "--run-url", default="—",
        help="Link auf den erzeugenden Workflow-Lauf (Logs/Screenshots als Artefakte dort).",
    )
    parser.add_argument(
        "--summary-output", type=Path,
        help="Optionales maschinenlesbares Plattform-Fazit fuer #744.",
    )
    args = parser.parse_args(argv)

    evidences = load_evidence(args.artifacts_dir)
    e2e = load_e2e(args.artifacts_dir)
    live_gl = load_live_gl(args.artifacts_dir)
    vision = load_vision(args.artifacts_dir)
    rows = build_matrix(
        evidences, x86_64_enabled=args.x86_64_enabled, e2e=e2e,
        live_gl=live_gl, vision=vision, run_url=args.run_url,
    )
    markdown = render_markdown(rows, commit_sha=args.commit_sha)
    args.output.write_text(markdown, encoding="utf-8")
    if args.summary_output is not None:
        summary = build_acceptance_summary(
            rows, commit_sha=args.commit_sha, x86_64_enabled=args.x86_64_enabled,
        )
        args.summary_output.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(markdown)
    print(f"\nMatrix geschrieben: {args.output}")
    # Blockierende Lücken sind ein Signal, kein harter Fehler (Mensch entscheidet).
    return 0


if __name__ == "__main__":
    sys.exit(main())
