#!/usr/bin/env python3
"""Anonymer Öffentlichkeitsnachweis der Release-Assets (#916, Epic #914).

`PUBLIC-DOWNLOAD-01` verlangt, dass alle fünf veröffentlichten Assets **ohne
GitHub-Anmeldung** über ihre ``browser_download_url`` erreichbar sind und
bytegenau den im Freigabemanifest gebundenen Hashes entsprechen. Bei v2.9.0
wurde der Nachweis rund sieben Stunden nach dem Publish von Hand erbracht
(#881); dieses Skript erzeugt ihn stattdessen unmittelbar nach der
Veröffentlichung als unveränderliches Actions-Artefakt.

Warum ein eigener Schritt und nicht die Prüfung im Publish-Job: Der dortige
Verifikationsschritt lädt **vor** der Veröffentlichung authentifiziert aus dem
Draft. Draft-Assets sind anonym gar nicht erreichbar – dieser Pfad belegt also
nie, dass ein Anwender das Artefakt bekommt. Deshalb läuft der Nachweis
**nach** ``gh release edit --draft=false`` und schickt zu keinem Zeitpunkt
einen ``Authorization``-Header, weder für die Release-Metadaten noch für die
Nutzlast. Ein versehentlich privat gebliebenes Release fällt damit auf.

Referenz der Sollwerte bleibt ausschließlich das Freigabemanifest, nicht der
von GitHub gemeldete Asset-Digest – sonst würde dieselbe Quelle zweimal
befragt. Die Vergleichsregel selbst kommt aus ``release_contract`` und ist
damit identisch zu ``verify-artifacts``: Der Bericht kann nie etwas anderes
behaupten als das Verdikt, das den Lauf scheitern lässt.

Fail-closed: Jede Hash-Abweichung, jedes fehlende oder zusätzliche Asset und
jeder HTTP-Fehler beenden das Skript mit Exit-Code 2. Der Bericht wird
**trotzdem** geschrieben, damit die Evidenz eines Fehlschlags erhalten bleibt
(Incident-Pfad: Runbook Schritt 9, „Rollback und Teilzustände“).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, cast

try:  # Dateiaufruf: ``python scripts/public_download_check.py``
    import release_contract as rc
except ModuleNotFoundError:  # Import als ``scripts.public_download_check`` in Tests
    from scripts import release_contract as rc

REPORT_SCHEMA: Final = 1
REPORT_KIND: Final = "release-public-download"
API_ROOT: Final = "https://api.github.com"
USER_AGENT: Final = "bgremover-public-download-check"
REQUEST_TIMEOUT_S: Final = 600.0
#: Nur transiente Fehler werden wiederholt; eine 404 (Release fehlt/privat)
#: oder ein Hash-Unterschied sind Befunde und werden nie weggepollt.
RETRY_STATUS: Final = (429, 500, 502, 503, 504)
DEFAULT_ATTEMPTS: Final = 3
RETRY_DELAYS_S: Final = (5.0, 15.0)

Fetcher = Callable[[urllib.request.Request], bytes]
Sleeper = Callable[[float], None]


class PublicDownloadError(RuntimeError):
    """Der öffentliche Download-Nachweis ist gescheitert."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def anonymous_request(url: str, accept: str) -> urllib.request.Request:
    """Anfrage **ohne** ``Authorization`` – der einzige Weg in diesem Skript.

    Es gibt bewusst keinen Token-Parameter: Ein Aufrufer kann den Nachweis
    nicht versehentlich authentifiziert führen und damit entwerten.
    """
    headers = {"Accept": accept, "User-Agent": USER_AGENT}
    return urllib.request.Request(url, headers=headers)  # noqa: S310


def _default_fetcher(request: urllib.request.Request) -> bytes:
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_S) as response:  # noqa: S310
        return cast(bytes, response.read())


def fetch(
    request: urllib.request.Request,
    fetcher: Fetcher,
    *,
    what: str,
    attempts: int = DEFAULT_ATTEMPTS,
    sleeper: Sleeper = time.sleep,
) -> bytes:
    """Anfrage mit eng begrenztem Wiederholungsfenster für transiente Fehler.

    Wiederholt werden ausschließlich Antworten, die nichts über die Sache
    aussagen (429/5xx, Netzabbruch). Eine 404 – privates, fehlendes oder falsch
    getaggtes Release – ist ein Befund und wird nie weggepollt.
    """
    total = max(1, attempts)
    last: Exception | None = None
    for attempt in range(1, total + 1):
        try:
            return fetcher(request)
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRY_STATUS:
                raise PublicDownloadError(f"{what}: HTTP {exc.code} {exc.reason}") from exc
            last = exc
        except OSError as exc:  # URLError und Verbindungsabbruch im Transfer
            last = exc
        if attempt < total:
            sleeper(RETRY_DELAYS_S[min(attempt - 1, len(RETRY_DELAYS_S) - 1)])
    raise PublicDownloadError(f"{what}: {last}")


def fetch_release(
    repo: str,
    tag: str,
    fetcher: Fetcher,
    *,
    sleeper: Sleeper = time.sleep,
) -> dict[str, Any]:
    """Release-Metadaten anonym beziehen; ein Draft ist hier nicht sichtbar.

    Auch die Metadaten laufen ohne Token: Erst damit belegt der Lauf, dass das
    Release oeffentlich sichtbar ist. Der Preis ist das unauthentifizierte
    API-Kontingent — deshalb nennt der Fehlertext beide moeglichen Ursachen,
    statt einen Rate-Limit-Treffer wie einen Releasefehler aussehen zu lassen.
    """
    try:
        raw = fetch(
            anonymous_request(
                f"{API_ROOT}/repos/{repo}/releases/tags/{tag}", "application/vnd.github+json"
            ),
            fetcher,
            what=f"Release {tag} anonym abrufen",
            sleeper=sleeper,
        )
    except PublicDownloadError as exc:
        raise PublicDownloadError(
            f"{exc} - entweder ist das Release nicht oeffentlich (Draft, privat, falscher Tag) "
            "oder das unauthentifizierte API-Kontingent ist erschoepft; beides ist ein Befund, "
            "kein stiller Wiederholungsfall (Runbook Schritt 9)."
        ) from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicDownloadError(f"Release {tag}: Antwort ist kein gueltiges JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise PublicDownloadError(f"Release {tag}: unerwartete Antwortstruktur")
    release = cast(dict[str, Any], payload)
    if release.get("draft") is True:
        raise PublicDownloadError(f"Release {tag} ist noch ein Draft und damit nicht oeffentlich")
    return release


def public_asset_urls(release: dict[str, Any], expected_names: set[str]) -> dict[str, str]:
    """``browser_download_url`` je erwartetem Asset; Abweichungen blockieren."""
    assets_raw = release.get("assets")
    if not isinstance(assets_raw, list):
        raise PublicDownloadError("Release ohne Asset-Liste")
    urls: dict[str, str] = {}
    for item in assets_raw:
        if not isinstance(item, dict):
            raise PublicDownloadError("Release mit ungueltigem Asset-Eintrag")
        asset = cast(dict[str, Any], item)
        name = str(asset.get("name") or "")
        url = str(asset.get("browser_download_url") or "")
        if name in urls:
            raise PublicDownloadError(f"Release enthaelt {name} doppelt")
        if not url:
            raise PublicDownloadError(f"Asset {name} hat keine browser_download_url")
        urls[name] = url
    missing = sorted(expected_names - set(urls))
    extra = sorted(set(urls) - expected_names)
    if missing or extra:
        raise PublicDownloadError(
            f"Oeffentliche Assetmenge weicht vom Manifest ab: fehlend={missing}, "
            f"zusaetzlich={extra}"
        )
    return urls


def download_assets(
    urls: dict[str, str],
    directory: Path,
    fetcher: Fetcher,
    *,
    sleeper: Sleeper = time.sleep,
) -> dict[str, str]:
    """Alle Assets anonym laden; liefert je Datei den Zeitstempel des Abrufs."""
    directory.mkdir(parents=True, exist_ok=True)
    timestamps: dict[str, str] = {}
    for name in sorted(urls):
        payload = fetch(
            anonymous_request(urls[name], "application/octet-stream"),
            fetcher,
            what=f"Asset {name} anonym laden",
            sleeper=sleeper,
        )
        (directory / name).write_bytes(payload)
        timestamps[name] = _utc_now()
    return timestamps


def build_report(
    *,
    manifest: dict[str, Any],
    repo: str,
    tag: str,
    release: dict[str, Any],
    urls: dict[str, str],
    timestamps: dict[str, str],
    directory: Path,
    run_url: str = "",
    error: str = "",
) -> dict[str, Any]:
    """Protokoll je Datei plus Gesamtverdikt aus der Vertrags-Vergleichsregel.

    ``error`` traegt einen Abbruch **vor** dem vollstaendigen Download (HTTP-
    Fehler, privates Release, abweichende Assetmenge) in denselben Bericht:
    Der Nachweis bleibt auch im Fehlerfall verlinkbar, statt nur im Joblog zu
    stehen.
    """
    candidate = cast(dict[str, Any], manifest["candidate"])
    acceptance = cast(dict[str, Any], manifest["acceptance"])
    assets: list[dict[str, Any]] = []
    for entry in rc.compare_artifact_directory(manifest, directory):
        name = str(entry["name"])
        assets.append(
            {
                "name": name,
                "url": urls.get(name, ""),
                "bytes": entry["bytes"],
                "sha256": entry["sha256"],
                "expected_bytes": entry["expected_bytes"],
                "expected_sha256": entry["expected_sha256"],
                "downloaded_at": timestamps.get(name, ""),
                "result": entry["status"],
                "detail": entry["detail"],
            }
        )
    ok = bool(assets) and not error and all(item["result"] == "PASS" for item in assets)
    return {
        "schema": REPORT_SCHEMA,
        "kind": REPORT_KIND,
        "verdict": "PASS" if ok else "FAIL",
        "error": error,
        # Der Nachweis ist nur so viel wert wie diese Zusage: kein
        # Authorization-Header, weder fuer Metadaten noch fuer die Nutzlast.
        "authenticated": False,
        "release": {
            "repo": repo,
            "tag": tag,
            "version": candidate["version"],
            "candidate_sha": candidate["head_sha"],
            "html_url": str(release.get("html_url") or ""),
            "published_at": str(release.get("published_at") or ""),
        },
        "reference": {
            "source": "release-approval-manifest",
            "approval_artifact_name": acceptance["approval_artifact_name"],
            "candidate_run_id": candidate["run_id"],
            "acceptance_run_id": acceptance["run_id"],
        },
        "run_url": run_url,
        "assets": assets,
        "generated_at": _utc_now(),
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Job-Summary und Issue-Kommentar rendern (identischer Text)."""
    release = cast(dict[str, Any], report["release"])
    reference = cast(dict[str, Any], report["reference"])
    verdict = str(report["verdict"])
    headline = "bestanden" if verdict == "PASS" else "**fehlgeschlagen**"
    lines = [
        f"## Öffentlicher Download-Nachweis `PUBLIC-DOWNLOAD-01`: {headline}",
        "",
        f"- Release: `{release['tag']}` ({release['repo']}), Version {release['version']}",
        f"- Kandidaten-Commit: `{release['candidate_sha']}`",
        f"- Sollwerte: `{reference['approval_artifact_name']}` "
        f"(Build-Run {reference['candidate_run_id']}, Abnahme-Run {reference['acceptance_run_id']})",
        "- Bezug: anonym über `browser_download_url`, ohne `Authorization`-Header",
    ]
    if report.get("run_url"):
        lines.append(f"- Nachweis-Lauf: {report['run_url']}")
    lines += [
        "",
        "| Datei | Ergebnis | Größe (Byte) | SHA-256 | Geladen (UTC) |",
        "|---|---|---:|---|---|",
    ]
    for asset in cast(list[dict[str, Any]], report["assets"]):
        digest = asset["sha256"] or "–"
        size = asset["bytes"] if asset["bytes"] is not None else "–"
        lines.append(
            f"| [{asset['name']}]({asset['url']}) | {asset['result']} | {size} | "
            f"`{digest}` | {asset['downloaded_at'] or '–'} |"
        )
    findings = [f"- {report['error']}"] if report.get("error") else []
    findings += [
        f"- `{item['name']}`: {item['detail']}"
        for item in cast(list[dict[str, Any]], report["assets"])
        if item["detail"]
    ]
    if findings:
        lines += ["", "### Befunde", "", *findings]
    lines += [
        "",
        (
            "Alle fünf Assets sind ohne GitHub-Anmeldung erreichbar und byteidentisch "
            "zum Freigabemanifest."
            if verdict == "PASS"
            else "Der Nachweis ist ein Incident nach Runbook Schritt 9 "
            "(„Rollback und Teilzustände“). Release nicht als abgeschlossen markieren."
        ),
        "",
        f"_Erzeugt {report['generated_at']} von `scripts/public_download_check.py` (#916)._",
    ]
    return "\n".join(lines) + "\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(
    *,
    manifest_path: Path,
    repo: str,
    tag: str,
    download_dir: Path,
    report_path: Path,
    markdown_path: Path | None = None,
    run_url: str = "",
    fetcher: Fetcher | None = None,
    sleeper: Sleeper | None = None,
) -> dict[str, Any]:
    """Nachweis führen; wirft ``PublicDownloadError``, wenn er nicht hält.

    ``fetcher``/``sleeper`` werden erst hier aufgelöst (nicht als
    Default-Argument gebunden), damit Tests den echten Netzpfad zuverlässig
    ersetzen können.
    """
    fetch_with = fetcher if fetcher is not None else _default_fetcher
    wait = sleeper if sleeper is not None else time.sleep
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicDownloadError(f"Freigabemanifest nicht lesbar: {manifest_path}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PublicDownloadError("Freigabemanifest muss ein Objekt sein")
    manifest = cast(dict[str, Any], manifest)
    candidate = manifest.get("candidate")
    if not isinstance(candidate, dict) or not isinstance(manifest.get("acceptance"), dict):
        raise PublicDownloadError("Freigabemanifest ohne Kandidaten-/Abnahmebindung")
    expected_tag = str(cast(dict[str, Any], candidate).get("expected_tag") or "")
    if tag != expected_tag:
        raise PublicDownloadError(
            f"Tag {tag} weicht vom Freigabemanifest ab (erwartet {expected_tag})"
        )
    try:
        expected_names = {str(item["name"]) for item in rc.manifest_artifacts(manifest)}
    except rc.ContractError as exc:
        raise PublicDownloadError(str(exc)) from exc

    # Auch ein Abbruch mitten im Bezug muss als Bericht sichtbar werden, statt
    # nur im Joblog zu stehen: Der Fehler wandert in den Bericht, das Verdikt
    # bleibt fail-closed FAIL.
    download_dir.mkdir(parents=True, exist_ok=True)
    release: dict[str, Any] = {}
    urls: dict[str, str] = {}
    timestamps: dict[str, str] = {}
    error = ""
    try:
        release = fetch_release(repo, tag, fetch_with, sleeper=wait)
        urls = public_asset_urls(release, expected_names)
        timestamps = download_assets(urls, download_dir, fetch_with, sleeper=wait)
    except PublicDownloadError as exc:
        error = str(exc)

    report = build_report(
        manifest=manifest,
        repo=repo,
        tag=tag,
        release=release,
        urls=urls,
        timestamps=timestamps,
        directory=download_dir,
        run_url=run_url,
        error=error,
    )
    _write(report_path, json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    if markdown_path is not None:
        _write(markdown_path, render_markdown(report))
    if report["verdict"] != "PASS":
        findings = [error] if error else []
        findings += [
            f"{item['name']}: {item['detail']}"
            for item in cast(list[dict[str, Any]], report["assets"])
            if item["detail"]
        ]
        raise PublicDownloadError("PUBLIC-DOWNLOAD-01 nicht erfuellt: " + "; ".join(findings))
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--download-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--run-url", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = run(
            manifest_path=args.manifest,
            repo=args.repo,
            tag=args.tag,
            download_dir=args.download_dir,
            report_path=args.report,
            markdown_path=args.markdown,
            run_url=args.run_url,
        )
    except PublicDownloadError as exc:
        print(f"::error title=PUBLIC-DOWNLOAD-01::{exc}", file=sys.stderr)
        return 2
    print(f"PUBLIC-DOWNLOAD-01 bestanden: {len(report['assets'])} Assets anonym byteidentisch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
