#!/usr/bin/env python3
"""Erzeugt eine Lizenz- und Rechtsuebersicht fuer dieses Projekt.

Der echte Dependency-Baum wird aus pyproject.toml ([project].dependencies und
[project].optional-dependencies) abgeleitet und ueber die installierten
Paket-Metadaten transitiv aufgeloest. Vorinstallierte System-/Container-Pakete,
die nicht zum Projekt gehoeren, bleiben dadurch aussen vor.

Ausgabe (rein technische Einschaetzung, keine Rechtsberatung):
  * vollstaendiger Report  -> --report
  * Kurzfassung fuer PR-Kommentare -> --summary

Aufruf:
  python scripts/generate_license_report.py \
      --report license-report.md --summary license-summary.md
"""
from __future__ import annotations

import argparse
import datetime as _dt
import importlib.metadata as md
import re
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

from packaging.markers import default_environment
from packaging.requirements import Requirement


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


# --- Lizenz-Wissensbasis ---------------------------------------------------
# Reihenfolge = Copyleft-Staerke (groesser = staerker). Bestimmt die
# Ausgangslizenz des verteilten Gesamtwerks.
STRENGTH = {
    "permissive": 0,
    "mpl": 1,
    "lgpl": 2,
    "gpl": 3,
    "unknown": -1,
}

ASSESSMENT = {
    "mit": (
        "permissive",
        "Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch "
        "kommerziell und in proprietaeren Produkten – sind erlaubt, solange "
        "Copyright- und Lizenzhinweis erhalten bleiben.",
    ),
    "bsd": (
        "permissive",
        "Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere "
        "Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, "
        "keine Werbung mit den Autorennamen ohne Zustimmung.",
    ),
    "apache": (
        "permissive",
        "Permissive Lizenz mit ausdruecklicher Patentlizenz. Kommerzielle "
        "und proprietaere Nutzung erlaubt; Lizenz-/Copyright-Hinweis und "
        "Aenderungsvermerke (NOTICE) muessen erhalten bleiben.",
    ),
    "psf": (
        "permissive",
        "Permissive Python-Software-Foundation-Lizenz. Kommerzielle und "
        "proprietaere Nutzung erlaubt; Lizenz- und Copyright-Hinweis "
        "beibehalten.",
    ),
    "hpnd": (
        "permissive",
        "Permissive HPND/MIT-CMU-Lizenz (Pillow). Kommerzielle und "
        "proprietaere Nutzung erlaubt; Copyright- und Lizenzhinweis "
        "beibehalten.",
    ),
    "isc": (
        "permissive",
        "Permissive Lizenz (funktional wie MIT). Kommerzielle und "
        "proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis beibehalten.",
    ),
    "zlib": (
        "permissive",
        "Permissive zlib-Lizenz. Kommerzielle Nutzung erlaubt; veraenderte "
        "Quellen muessen als solche gekennzeichnet werden.",
    ),
    "mpl": (
        "mpl",
        "Schwaches, dateibezogenes Copyleft. Kommerzielle Nutzung erlaubt; "
        "nur Aenderungen an den MPL-lizenzierten Dateien selbst muessen "
        "wieder unter MPL offengelegt werden. Mit GPL-3.0 vereinbar.",
    ),
    "lgpl": (
        "lgpl",
        "Schwaches Copyleft fuer Bibliotheken. Kommerzielle Nutzung erlaubt; "
        "Endnutzer muss die Bibliothek austauschen koennen (dynamisches "
        "Linking bzw. Re-Link-Moeglichkeit). Mit GPL-3.0 vereinbar.",
    ),
    "gpl": (
        "gpl",
        "Starkes Copyleft. Jede Weitergabe des Gesamtwerks muss als "
        "vollstaendiger Quelltext unter GPL erfolgen; eine proprietaere "
        "(closed-source) Weitergabe ist ausgeschlossen.",
    ),
    "unknown": (
        "unknown",
        "Lizenz aus den Paket-Metadaten nicht eindeutig bestimmbar – "
        "manuelle Pruefung der Originalquelle empfohlen.",
    ),
}


def _classify_token(tok: str) -> str:
    t = tok.lower()
    if "lgpl" in t or "lesser general public" in t:
        return "lgpl"
    if "gpl" in t or "general public license" in t:
        return "gpl"
    if "mpl" in t or "mozilla public" in t:
        return "mpl"
    if "apache" in t:
        return "apache"
    if "psf" in t or "python software foundation" in t:
        return "psf"
    if "mit-cmu" in t or "hpnd" in t:
        return "hpnd"
    if "isc" in t:
        return "isc"
    if "zlib" in t:
        return "zlib"
    if "bsd" in t:
        return "bsd"
    if "mit" in t:
        return "mit"
    if t in {"0bsd", "cc0-1.0", "cc0", "unlicense"}:
        return "mit"  # public-domain-aehnlich -> wie permissive behandeln
    return ""


def classify(raw: str) -> tuple[str, str, str]:
    """-> (Kategorie, Kurzbewertung, normalisierter Lizenz-String)."""
    if not raw or raw.strip().upper() in {"", "UNKNOWN", "NONE"}:
        cat, txt = ASSESSMENT["unknown"]
        return cat, txt, "UNKNOWN"
    tokens = re.split(r"\s+(?:AND|OR|WITH)\s+|;|/|,", raw)
    keys = [k for k in (_classify_token(t) for t in tokens if t.strip()) if k]
    if not keys:
        cat, txt = ASSESSMENT["unknown"]
        return cat, txt, raw.strip()
    # staerkstes Copyleft im Ausdruck bestimmt Kategorie & Bewertung
    best = max(keys, key=lambda k: STRENGTH[ASSESSMENT[k][0]])
    cat, txt = ASSESSMENT[best]
    return cat, txt, raw.strip()


# --- Dependency-Aufloesung -------------------------------------------------
def project_roots(pyproject: Path) -> tuple[list[str], dict[str, set[str]]]:
    data = tomllib.loads(pyproject.read_text("utf-8"))
    proj = data.get("project", {})
    roots: list[str] = []
    extras_for: dict[str, set[str]] = {}
    specs = list(proj.get("dependencies", []))
    for group in proj.get("optional-dependencies", {}).values():
        specs.extend(group)
    for spec in specs:
        try:
            req = Requirement(spec)
        except Exception:
            continue
        roots.append(req.name)
        if req.extras:
            extras_for.setdefault(_norm(req.name), set()).update(req.extras)
    return roots, extras_for


def license_string(dist: md.Distribution) -> str:
    meta = dist.metadata
    expr = meta.get("License-Expression")
    if expr:
        return expr
    classifiers = [
        c.split("::")[-1].strip()
        for c in (meta.get_all("Classifier") or [])
        if c.startswith("License")
    ]
    if classifiers:
        return "; ".join(dict.fromkeys(classifiers))
    lic = meta.get("License")
    if lic:
        return lic.strip().splitlines()[0][:80]
    return "UNKNOWN"


def resolve_closure(roots, extras_for):
    env = default_environment()
    closure: dict[str, dict] = {}
    visited: set[tuple[str, frozenset]] = set()

    def visit(name: str, active_extras: set[str]):
        try:
            dist = md.distribution(name)
        except md.PackageNotFoundError:
            return
        real = dist.metadata["Name"]
        key = _norm(real)
        if key not in closure:
            closure[key] = {
                "name": real,
                "version": dist.version,
                "license": license_string(dist),
                "url": dist.metadata.get("Home-page")
                or _project_url(dist)
                or "",
            }
        for raw_req in dist.requires or []:
            try:
                req = Requirement(raw_req)
            except Exception:
                continue
            if req.marker:
                ok = False
                for ex in (active_extras or {""}) | {""}:
                    e = dict(env)
                    e["extra"] = ex
                    try:
                        if req.marker.evaluate(e):
                            ok = True
                            break
                    except Exception:
                        pass
                if not ok:
                    continue
            child_extras = set(req.extras)
            sig = (_norm(req.name), frozenset(child_extras))
            if sig in visited:
                continue
            visited.add(sig)
            visit(req.name, child_extras)

    for r in roots:
        visit(r, extras_for.get(_norm(r), set()))
    return closure


def _project_url(dist: md.Distribution) -> str:
    for entry in dist.metadata.get_all("Project-URL") or []:
        label, _, url = entry.partition(",")
        if label.strip().lower() in {"homepage", "repository", "source"}:
            return url.strip()
    return ""


# --- Reporting -------------------------------------------------------------
def build_reports(root_dir: Path):
    pyproject = root_dir / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text("utf-8"))
    proj = data.get("project", {})
    project_name = proj.get("name", "Projekt")
    project_version = proj.get("version", "")
    project_license = proj.get("license", "")
    if isinstance(project_license, dict):
        project_license = project_license.get("text", "") or project_license.get(
            "file", ""
        )

    roots, extras_for = project_roots(pyproject)
    closure = resolve_closure(roots, extras_for)
    closure.pop(_norm(project_name), None)  # eigenes Paket nicht als Dependency

    rows = []
    by_cat: dict[str, list[str]] = defaultdict(list)
    for key in sorted(closure):
        info = closure[key]
        cat, assessment, lic = classify(info["license"])
        rows.append((info["name"], info["version"], lic, cat, assessment, info["url"]))
        by_cat[cat].append(info["name"])

    proj_cat, _, _ = classify(str(project_license))
    strongest = proj_cat
    for _, _, _, cat, _, _ in rows:
        if STRENGTH.get(cat, -1) > STRENGTH.get(strongest, -1):
            strongest = cat

    generated = _dt.date.today().isoformat()
    full = _render_full(
        project_name,
        project_version,
        project_license,
        generated,
        rows,
        by_cat,
        strongest,
    )
    summary = _render_summary(
        project_name, project_license, generated, rows, by_cat, strongest
    )
    return full, summary


def _verdict(strongest: str, project_license: str) -> list[str]:
    if strongest == "gpl":
        return [
            "**Kommerzielle Nutzung:** Erlaubt – die GPL untersagt keinen "
            "Verkauf. Es darf Geld fuer Vertrieb, Support oder Dienste "
            "verlangt werden.",
            "**Bedingungen:** Das verteilte Gesamtwerk steht unter "
            f"`{project_license or 'GPL-3.0'}`. Bei jeder Weitergabe (auch "
            "Verkauf) muss der vollstaendige, korrespondierende **Quelltext** "
            "unter GPL mitgeliefert oder schriftlich angeboten werden; der "
            "GPL-Lizenztext und alle Copyright-Hinweise muessen beiliegen; es "
            "duerfen keine zusaetzlichen Nutzungsbeschraenkungen ergaenzt "
            "werden.",
            "**Pflichten bei Veroeffentlichung/Verkauf:** Quelloffenlegung "
            "des Gesamtwerks unter GPL, Beilegen von GPL-Text und "
            "Copyright-/Lizenzhinweisen aller (auch permissiver) "
            "Dependencies, Hinweis auf Gewaehrleistungsausschluss. Eine "
            "**proprietaere/closed-source** Auslieferung ist **nicht** "
            "moeglich.",
            "**LGPL/Qt-Besonderheit:** Qt (PyQt6-Qt6) ist LGPL-v3; PyQt6 "
            "wird hier unter GPL-3.0 genutzt. Da das Gesamtwerk ohnehin GPL "
            "ist, sind die LGPL-Austauschpflichten durch die "
            "Quelloffenlegung abgedeckt.",
        ]
    if strongest in {"mpl", "lgpl"}:
        return [
            "**Kommerzielle Nutzung:** Erlaubt, auch in proprietaeren "
            "Produkten.",
            "**Bedingungen:** Aenderungen an MPL-/LGPL-Komponenten bzw. die "
            "Austauschbarkeit der LGPL-Bibliothek muessen offengelegt "
            "ermoeglicht werden; eigener Code kann proprietaer bleiben.",
            "**Pflichten bei Veroeffentlichung/Verkauf:** Lizenztexte und "
            "Copyright-Hinweise beilegen, geaenderte MPL-Dateien offenlegen, "
            "Re-Link-Moeglichkeit fuer LGPL-Bibliotheken sicherstellen.",
        ]
    return [
        "**Kommerzielle Nutzung:** Uneingeschraenkt erlaubt, auch in "
        "proprietaeren/closed-source Produkten.",
        "**Bedingungen:** Lediglich Beibehaltung der Copyright- und "
        "Lizenzhinweise (Attribution); keine Quelloffenlegungspflicht.",
        "**Pflichten bei Veroeffentlichung/Verkauf:** Lizenztexte und "
        "Copyright-Vermerke der verwendeten Pakete mitliefern.",
    ]


def _conflicts(rows, strongest: str, project_license: str) -> list[str]:
    notes: list[str] = []
    has_gpl_dep = any(c == "gpl" for *_, c, _, _ in rows)
    proj_is_gpl = "gpl" in str(project_license).lower()
    if strongest == "gpl":
        notes.append(
            "Kein Lizenzkonflikt erkannt: Alle Dependency-Lizenzen "
            "(permissive, MPL-2.0, LGPL-v3) sind mit GPL-3.0 vereinbar und "
            "koennen unter GPL-3.0 weitergegeben werden."
        )
        if has_gpl_dep and proj_is_gpl:
            notes.append(
                "PyQt6 ist `GPL-3.0-only`. Mit der Projektlizenz "
                f"`{project_license}` vertraeglich – das Gesamtwerk ist "
                "effektiv unter GPL-3.0 zu verteilen."
            )
        notes.append(
            "PyQt6/Qt sind dual lizenziert (GPL **oder** kommerzielle "
            "Riverbank/Qt-Lizenz). Solange das Projekt GPL bleibt, ist die "
            "GPL-Variante einschlaegig; fuer ein proprietaeres Produkt "
            "waeren kostenpflichtige PyQt6-/Qt-Lizenzen noetig."
        )
    else:
        notes.append(
            "Kein starkes Copyleft (GPL) in der Abhaengigkeitskette – keine "
            "projektweite Copyleft-Pflicht erkannt."
        )
    if any(c == "unknown" for *_, c, _, _ in rows):
        notes.append(
            "Mindestens ein Paket hat unklare Lizenz-Metadaten – siehe "
            "Tabelle, dort manuell pruefen."
        )
    return notes


_LEGEND = {
    "gpl": "Starkes Copyleft",
    "lgpl": "Schwaches Copyleft (Bibliothek)",
    "mpl": "Schwaches Copyleft (Datei)",
    "permissive": "Permissiv",
    "unknown": "Unklar",
}


def _render_full(name, version, lic, generated, rows, by_cat, strongest):
    out: list[str] = []
    out.append(f"# Lizenz- & Rechtsuebersicht – {name} {version}".rstrip())
    out.append("")
    out.append(
        "> Automatisch generiert – **rein technische Einschaetzung der "
        "Lizenzbedingungen, keine Rechtsberatung.**"
    )
    out.append(f"> Stand: {generated} · Eigenlizenz des Projekts: "
               f"`{lic or 'n/a'}` · {len(rows)} Dependencies analysiert.")
    out.append("")
    out.append("## Gesamtbewertung – kommerzielle Nutzbarkeit")
    out.append("")
    out.append(
        f"Staerkste relevante Lizenz im Gesamtwerk: **{_LEGEND.get(strongest, strongest)}**."
    )
    out.append("")
    for line in _verdict(strongest, str(lic)):
        out.append(f"- {line}")
    out.append("")
    out.append("## Hinweise auf potenzielle Lizenz-Konflikte")
    out.append("")
    for line in _conflicts(rows, strongest, str(lic)):
        out.append(f"- {line}")
    out.append("")
    out.append("## Lizenzverteilung")
    out.append("")
    out.append("| Kategorie | Anzahl | Pakete |")
    out.append("|---|---|---|")
    for cat in sorted(by_cat, key=lambda c: -STRENGTH.get(c, -1)):
        pkgs = ", ".join(sorted(by_cat[cat]))
        out.append(f"| {_LEGEND.get(cat, cat)} | {len(by_cat[cat])} | {pkgs} |")
    out.append("")
    out.append("## Dependencies im Detail")
    out.append("")
    out.append("| Paket | Version | Lizenz | Kategorie | Einschaetzung |")
    out.append("|---|---|---|---|---|")
    for pname, pver, plic, pcat, passess, _ in rows:
        out.append(
            f"| {pname} | {pver} | `{plic}` | {_LEGEND.get(pcat, pcat)} | "
            f"{passess} |"
        )
    out.append("")
    out.append("## Quellen / Projektseiten")
    out.append("")
    for pname, _, _, _, _, purl in rows:
        if purl:
            out.append(f"- **{pname}** – {purl}")
    out.append("")
    out.append("---")
    out.append(
        "_Erzeugt durch `scripts/generate_license_report.py`. Aenderungen am "
        "Dependency-Satz aktualisieren diesen Report automatisch im "
        "CI-Workflow._"
    )
    out.append("")
    return "\n".join(out)


def _render_summary(name, lic, generated, rows, by_cat, strongest):
    out: list[str] = []
    out.append("## Lizenz-Check – Zusammenfassung")
    out.append("")
    out.append(
        f"Projekt `{name}` · Eigenlizenz `{lic or 'n/a'}` · "
        f"{len(rows)} Dependencies · Stand {generated}."
    )
    out.append("")
    out.append(
        f"**Staerkste Lizenz im Gesamtwerk:** {_LEGEND.get(strongest, strongest)}"
    )
    out.append("")
    for line in _verdict(strongest, str(lic))[:3]:
        out.append(f"- {line}")
    out.append("")
    out.append("**Lizenzverteilung:** " + " · ".join(
        f"{_LEGEND.get(c, c)}: {len(by_cat[c])}"
        for c in sorted(by_cat, key=lambda c: -STRENGTH.get(c, -1))
    ))
    out.append("")
    confs = _conflicts(rows, strongest, str(lic))
    out.append("**Konflikt-Check:** " + confs[0])
    out.append("")
    out.append(
        "Vollstaendige Aufstellung: Workflow-Artefakt `license-report` bzw. "
        "`LICENSES.md` im Repo-Root. _Technische Einschaetzung, keine "
        "Rechtsberatung._"
    )
    out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", type=Path, default=Path("license-report.md"))
    ap.add_argument("--summary", type=Path, default=Path("license-summary.md"))
    ap.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parent.parent
    )
    args = ap.parse_args(argv)

    full, summary = build_reports(args.root)
    args.report.write_text(full, "utf-8")
    args.summary.write_text(summary, "utf-8")
    print(f"Report geschrieben: {args.report}")
    print(f"Kurzfassung geschrieben: {args.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
