#!/usr/bin/env python3
"""Release-Abnahme-Helfer: Artefaktbezug, SHA256-Verifikation, Evidenz (#641).

Läuft auf den Self-hosted Abnahme-Runnern (Betrieb: ``docs/RELEASE_AUTOMATION.md``).
Bezieht die Release-Artefakte der jeweiligen Plattform – wahlweise aus einem
veröffentlichten Release (``--release-tag``) oder aus den Workflow-Artefakten
eines ``release-linux.yml``-Laufs (``--source-run-id``) –, verifiziert sie per
SHA256 und schreibt ``evidenz.json`` + ``manifest.md`` nach dem Evidenzvertrag
aus ``docs/history/ADR-2026-release-abnahme-automatisierung.md``.

Der eigentliche Smoke-Inhalt (App-Start, GL-Provenance, Screenshots) folgt mit
#642/#643 – bis dahin trägt die Evidenz den Status ``platzhalter``.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform as platform_mod
import sys
import urllib.parse
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVIDENCE_SCHEMA = 1
EVIDENCE_KIND = "abnahme-evidenz"
STATUS_PLACEHOLDER = "platzhalter"
STATUS_PASSED = "bestanden"
STATUS_FAILED = "fehlgeschlagen"

# Retina/High-DPI gilt ab devicePixelRatio 2 als erfüllt (macOS-Panels, #643).
RETINA_MIN_SCALE = 2.0

# Plattform → Namensbestandteil der Release-Artefakte (Benennung seit #584).
PLATFORM_PATTERNS: dict[str, str] = {
    "linux-arm64": "linux-raspberrypi-arm64",
    "linux-x86_64": "linux-x86_64",
    "macos-arm64": "macos-arm64",
}

# Injektionspunkt für Tests: nimmt einen vorbereiteten Request, liefert Bytes.
Fetcher = Callable[[urllib.request.Request], bytes]


@dataclass(frozen=True)
class ArtifactRecord:
    """Ein bezogenes und gehashtes Release-Artefakt."""

    name: str
    sha256: str
    bytes: int


class _StripAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    """Entfernt ``Authorization`` nur bei Redirects auf einen anderen Host.

    Die Download-Endpunkte (``.../actions/artifacts/{id}/zip``,
    Release-Asset-``url``) antworten mit 302 auf signierte Blob-Storage-URLs
    auf einem fremden Host (Auth per Query-SAS-Token). ``urllib`` reicht
    Header bei Redirects im Gegensatz zu ``requests``/``curl`` unverändert
    weiter; ein mitgeschickter ``Authorization``-Header lässt den Blob-Store
    mit ``401 Server failed to authenticate the request`` scheitern. Bleibt
    ein Redirect dagegen auf demselben Host (z. B. api.github.com nach einer
    Repo-Umbenennung), bleibt der Token erhalten – sonst würden private
    Downloads dort unautorisiert und fehlschlagen.
    """

    def redirect_request(
        self, req: urllib.request.Request, fp: Any, code: int, msg: str,
        headers: Any, newurl: str,
    ) -> urllib.request.Request | None:
        new_request = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_request is not None:
            old_host = urllib.parse.urlsplit(req.full_url).hostname
            new_host = urllib.parse.urlsplit(newurl).hostname
            if old_host != new_host:
                new_request.remove_header("Authorization")
        return new_request


_REDIRECT_OPENER = urllib.request.build_opener(_StripAuthOnRedirect)


def _default_fetcher(request: urllib.request.Request) -> bytes:
    with _REDIRECT_OPENER.open(request, timeout=600) as response:  # noqa: S310
        return response.read()  # type: ignore[no-any-return]


def _request(url: str, token: str | None, accept: str) -> urllib.request.Request:
    headers = {"Accept": accept, "User-Agent": "bgremover-release-abnahme"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)  # noqa: S310


def _api_json(url: str, token: str | None, fetcher: Fetcher) -> Any:
    raw = fetcher(_request(url, token, "application/vnd.github+json"))
    return json.loads(raw.decode("utf-8"))


def matches_platform(name: str, platform: str) -> bool:
    """Gehört ein Asset-/Artefaktname zur angefragten Plattform?"""
    return PLATFORM_PATTERNS[platform] in name


def verify_digest(name: str, computed: str, expected: str | None) -> None:
    """Berechneten SHA256 gegen den vertrauenswürdigen Digest prüfen.

    ``expected`` ist das ``sha256:…``-Digestfeld des GitHub-Release-Assets. Ein
    Mismatch (ersetztes/beschädigtes Asset) bricht sofort ab; fehlt der Digest
    (z. B. Workflow-Artefakt-Zip ohne Feld), wird nur der berechnete Wert
    protokolliert – ohne unabhängige Bestätigung zu behaupten.
    """
    if not expected:
        return
    prefix, _, want = expected.partition(":")
    if prefix != "sha256" or not want:
        return
    if want.lower() != computed.lower():
        raise SystemExit(
            f"SHA256-Mismatch für {name}: erwartet {want}, berechnet {computed} "
            "– Asset beschädigt oder ersetzt."
        )


def _store(
    dest: Path, name: str, payload: bytes, expected_digest: str | None = None,
) -> ArtifactRecord:
    path = dest / name
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    verify_digest(name, digest, expected_digest)
    return ArtifactRecord(name=name, sha256=digest, bytes=len(payload))


def fetch_release_assets(
    repo: str, tag: str, platform: str, dest: Path, token: str | None, fetcher: Fetcher,
) -> list[ArtifactRecord]:
    """Assets des Release-Tags beziehen, die zur Plattform gehören."""
    release = _api_json(
        f"https://api.github.com/repos/{repo}/releases/tags/{tag}", token, fetcher,
    )
    records: list[ArtifactRecord] = []
    for asset in release.get("assets", []):
        name = str(asset["name"])
        if not matches_platform(name, platform):
            continue
        payload = fetcher(_request(str(asset["url"]), token, "application/octet-stream"))
        records.append(_store(dest, name, payload, asset.get("digest")))
    if not records:
        raise SystemExit(
            f"Release {tag} enthält keine Assets für Plattform {platform!r} "
            f"(erwartetes Namensmuster: {PLATFORM_PATTERNS[platform]!r})."
        )
    return records


def fetch_run_artifacts(
    repo: str, run_id: str, platform: str, dest: Path, token: str | None, fetcher: Fetcher,
) -> list[ArtifactRecord]:
    """Workflow-Artefakte eines Release-Laufs beziehen (Zip je Artefakt)."""
    if not token:
        raise SystemExit("Für --source-run-id ist GITHUB_TOKEN (actions: read) nötig.")
    listing = _api_json(
        f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts",
        token,
        fetcher,
    )
    records: list[ArtifactRecord] = []
    for artifact in listing.get("artifacts", []):
        if not matches_platform(str(artifact["name"]), platform):
            continue
        payload = fetcher(
            _request(str(artifact["archive_download_url"]), token, "application/vnd.github+json")
        )
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for member in archive.namelist():
                if member.endswith("/"):
                    continue
                records.append(_store(dest, Path(member).name, archive.read(member)))
    if not records:
        raise SystemExit(
            f"Lauf {run_id} enthält keine Artefakte für Plattform {platform!r} "
            f"(erwartetes Namensmuster: {PLATFORM_PATTERNS[platform]!r})."
        )
    return records


def environment_info() -> dict[str, str]:
    """Umgebungs-Pflichtfelder des Evidenzvertrags."""
    return {
        "os": platform_mod.platform(),
        "arch": platform_mod.machine(),
        "python": platform_mod.python_version(),
        "runner": os.environ.get("RUNNER_NAME", "unbekannt"),
    }


def build_evidence(
    platform: str,
    commit_sha: str,
    source: dict[str, str],
    artefacts: list[ArtifactRecord],
    notes: list[str],
) -> dict[str, Any]:
    """Evidenz-Dokument nach dem Vertrag aus dem ADR zusammenstellen."""
    return {
        "schema": EVIDENCE_SCHEMA,
        "kind": EVIDENCE_KIND,
        "platform": platform,
        "status": STATUS_PLACEHOLDER,
        "commit_sha": commit_sha,
        "quelle": source,
        "artefakte": [
            {"name": a.name, "sha256": a.sha256, "bytes": a.bytes} for a in artefacts
        ],
        "umgebung": environment_info(),
        "gl_provenance": None,
        "waechter_ergebnisse": [],
        "erzeugt_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hinweise": notes,
    }


def write_evidence(output: Path, evidence: dict[str, Any]) -> None:
    """``evidenz.json`` + menschenlesbares ``manifest.md`` schreiben."""
    output.mkdir(parents=True, exist_ok=True)
    (output / "evidenz.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    lines = [
        f"# Abnahme-Evidenz: {evidence['platform']}",
        "",
        f"- Status: `{evidence['status']}`",
        f"- Commit: `{evidence['commit_sha']}`",
        f"- Quelle: {evidence['quelle']['art']} `{evidence['quelle']['wert']}`",
        f"- Umgebung: `{evidence['umgebung']['os']}` ({evidence['umgebung']['arch']}), "
        f"Python {evidence['umgebung']['python']}, Runner `{evidence['umgebung']['runner']}`",
        f"- Erzeugt am: {evidence['erzeugt_am']}",
        "",
        "| Artefakt | SHA256 | Bytes |",
        "|---|---|---:|",
    ]
    lines += [
        f"| {a['name']} | `{a['sha256']}` | {a['bytes']} |" for a in evidence["artefakte"]
    ]
    guard_results = evidence.get("waechter_ergebnisse") or []
    if guard_results:
        lines += [
            "",
            "| Phase | Artefaktklasse | Status | Exit-Code | Peak-Instanzen |",
            "|---|---|---|---:|---:|",
        ]
        lines += [
            f"| {g['phase']} | {g['artefaktklasse']} | {g['status']} | {g['exit_code']} | "
            f"{g.get('peak_instanzen') if g.get('peak_instanzen') is not None else '—'} |"
            for g in guard_results
        ]
    lines += ["", *[f"> {note}" for note in evidence["hinweise"]], ""]
    (output / "manifest.md").write_text("\n".join(lines), encoding="utf-8")


# ── Smoke-Entscheidungslogik (Qt-frei, testbar) ─────────────────────────────
# Die OS-spezifischen Treiber (scripts/abnahme_smoke.py: run_linux_smoke,
# run_macos_smoke) sammeln die Rohsignale (App-Start,
# GL-Diagnose, Screenshot, Instanzzahl, .deb-Rückstände) und übergeben sie an
# diese Funktionen – so ist die Bewertung ohne echte Hardware testbar.


@dataclass(frozen=True)
class ProvenanceVerdict:
    """Bewertung einer GL-Diagnose als Hardware-Nachweis."""

    ok: bool
    diagnostic: str
    note: str


def evaluate_gl_provenance(diagnostic: str | None) -> ProvenanceVerdict:
    """Prüft, ob die GL-Diagnose einen echten Hardware-Renderer belegt.

    Fehlt die Diagnose oder nennt sie einen Software-Renderer (llvmpipe & Co.,
    geteilte Regel aus ``bgremover.renderer_provenance``), gilt der Smoke als
    **nicht erbracht** – die Offscreen-CI kann diese Nachweise nicht liefern.
    """
    from bgremover.renderer_provenance import is_software_renderer

    if not diagnostic or not diagnostic.strip():
        return ProvenanceVerdict(False, "", "Keine GL-Diagnose erfasst.")
    if is_software_renderer(diagnostic):
        return ProvenanceVerdict(
            False, diagnostic, f"Software-Renderer abgewiesen: {diagnostic}",
        )
    return ProvenanceVerdict(True, diagnostic, f"Hardware-Renderer: {diagnostic}")


def evaluate_retina(scale_factor: float) -> bool:
    """High-DPI erfüllt, wenn devicePixelRatio ≥ ``RETINA_MIN_SCALE`` (#643)."""
    return scale_factor >= RETINA_MIN_SCALE


def evaluate_deb_cleanup(package_installed: bool, leftover_paths: list[str]) -> bool:
    """Rückstandsfreie ``.deb``-Deinstallation: nicht mehr installiert, keine Reste."""
    return not package_installed and not leftover_paths


def finalize_evidence(
    evidence: dict[str, Any],
    *,
    passed: bool,
    gl_provenance: str | None,
    extra_notes: list[str] | None = None,
    guard_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Platzhalter-Evidenz zum echten Smoke-Ergebnis fortschreiben.

    Setzt ``status`` auf ``bestanden``/``fehlgeschlagen`` und trägt die
    geprüfte GL-Provenance ein; ergänzende Hinweise werden angehängt.
    ``guard_results`` trägt die strukturierten Wächter-Ergebnisse (Exit-Code,
    Peak-Instanzen, Timeout-/Fork-Bomb-Status, Log) je Startphase und
    Artefaktklasse ein (#642-Nachtrag) – ``None``/leer ergibt eine leere Liste,
    nie ein fehlendes Feld.
    """
    updated = dict(evidence)
    updated["status"] = STATUS_PASSED if passed else STATUS_FAILED
    updated["gl_provenance"] = gl_provenance
    updated["waechter_ergebnisse"] = guard_results or []
    notes = [n for n in evidence.get("hinweise", []) if "Platzhalter-Smoke" not in n]
    notes += extra_notes or []
    updated["hinweise"] = notes
    return updated


def main(argv: list[str] | None = None, fetcher: Fetcher = _default_fetcher) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=sorted(PLATFORM_PATTERNS))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA", "unbekannt"))
    parser.add_argument("--release-tag", default="")
    parser.add_argument("--source-run-id", default="")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    if bool(args.release_tag) == bool(args.source_run_id):
        parser.error("Genau eine Quelle angeben: --release-tag ODER --source-run-id.")
    if not args.repo:
        parser.error("--repo fehlt (oder GITHUB_REPOSITORY setzen).")

    token = os.environ.get("GITHUB_TOKEN") or None
    artefact_dir = args.output / "artefakte"
    artefact_dir.mkdir(parents=True, exist_ok=True)

    if args.release_tag:
        source = {"art": "release-tag", "wert": args.release_tag}
        records = fetch_release_assets(
            args.repo, args.release_tag, args.platform, artefact_dir, token, fetcher,
        )
    else:
        source = {"art": "run-id", "wert": args.source_run_id}
        records = fetch_run_artifacts(
            args.repo, args.source_run_id, args.platform, artefact_dir, token, fetcher,
        )

    evidence = build_evidence(
        args.platform,
        args.commit_sha,
        source,
        records,
        ["Platzhalter-Smoke aus #641 – echte Smokes folgen mit #642/#643."],
    )
    write_evidence(args.output, evidence)
    print(f"Evidenz geschrieben: {args.output / 'evidenz.json'} ({len(records)} Artefakte)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
