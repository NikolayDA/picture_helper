#!/usr/bin/env python3
"""GitHub-Live-Check fuer den Recommendations-Kurzstatus (#752).

`RECOMMENDATIONS.md` driftete wiederholt kurz nach einer Aktualisierung vom
tatsaechlichen GitHub-Stand ab (#669, #728, erneut #752). Dieses Modul
vergleicht die **Triage-Tabelle** (Abschnitt ``## Offene GitHub-Issues``, vor
dem historischen Archiv ``## Vorige Runden``) mit den tatsaechlich offenen
GitHub-Issues und meldet:

- offene Issues, die in der Tabelle fehlen,
- Issues, die die Tabelle als offen fuehrt, obwohl sie auf GitHub bereits
  geschlossen sind,
- eine von der im Kurzstatus genannten Zahl abweichende Gesamtzahl.

Nur die Zeilen des Triage-Abschnitts zaehlen; das Archiv ``## Vorige Runden``
ist bewusst historisch und wird nicht geprueft (siehe TESTING.md). Referenziert
wird ausschliesslich ueber vollstaendige Issue-Markdown-Links
(``[#NNN](.../issues/NNN)``) in Spalte 1 jeder Tabellenzeile - das loest
gruppierte Zeilen wie ``[#680](...) / [#685](...) / [#686](...)`` korrekt in
drei Nummern auf, ohne PR-Erwaehnungen oder Zahlen-Ranges in Fliesstext
("#742-#747") faelschlich als Issue-Referenz zu werten.

Die Kernlogik (``parse_triage_issue_numbers``, ``parse_declared_open_count``,
``open_issues_from_api_payload``, ``compare``) ist rein und netzfrei; nur
``fetch_open_issues``/``main`` sprechen das Netzwerk an. Die Default-Testsuite
deckt ausschliesslich die Kernlogik ueber gespeicherte Fixtures ab (#752).
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

_REPO_ROOT: Final = Path(__file__).resolve().parent.parent
_DEFAULT_RECOMMENDATIONS_PATH: Final = _REPO_ROOT / "RECOMMENDATIONS.md"
_DEFAULT_REPO: Final = "NikolayDA/picture_helper"
_ISSUES_API_URL: Final = "https://api.github.com/repos/{repo}/issues"
_REQUEST_HEADERS: Final = {"Accept": "application/vnd.github+json"}

#: Der Triage-Abschnitt beginnt bei "## Offene GitHub-Issues" und endet vor der
#: naechsten Ueberschrift zweiter Ordnung (insbesondere "## Vorige Runden").
_TRIAGE_SECTION_RE: Final = re.compile(r"(?ms)^## Offene GitHub-Issues.*?(?=^## |\Z)")
#: Spalte 1 jeder Tabellenzeile (Text zwischen dem ersten und zweiten "|").
_TABLE_FIRST_CELL_RE: Final = re.compile(r"(?m)^\|([^|]*)\|")
_LIVE_COUNT_RE: Final = re.compile(r"Live-Stand nach GitHub-Abfrage: \*\*(\d+)\*\*")


def _issue_link_re(repo: str) -> re.Pattern[str]:
    return re.compile(r"\[#(\d+)]\(https://github\.com/" + re.escape(repo) + r"/issues/(\d+)\)")


@dataclass(frozen=True)
class OpenIssue:
    """Ein auf GitHub offenes, reguläres Issue (keine Pull Requests)."""

    number: int
    title: str


@dataclass(frozen=True)
class LiveCheckReport:
    """Ergebnis eines Abgleichs von Triage-Tabelle gegen den GitHub-Live-Stand."""

    declared_count: int | None
    actual_count: int
    missing_open: tuple[int, ...]
    closed_but_listed: tuple[int, ...]

    @property
    def has_findings(self) -> bool:
        count_mismatch = (
            self.declared_count is not None and self.declared_count != self.actual_count
        )
        return bool(self.missing_open or self.closed_but_listed or count_mismatch)


class LiveCheckError(RuntimeError):
    """Dokument-, Netzwerk- oder Antwortfehler beim Live-Check."""


def extract_triage_section(markdown: str) -> str:
    """Der Text des Triage-Abschnitts, ohne das historische Archiv.

    Wirft :class:`LiveCheckError`, wenn der Abschnitt fehlt - ein umbenannter
    oder geloeschter Abschnitt soll den Check sichtbar scheitern lassen statt
    still eine leere Tabelle zu melden.
    """
    match = _TRIAGE_SECTION_RE.search(markdown)
    if match is None:
        raise LiveCheckError("Abschnitt 'Offene GitHub-Issues' nicht gefunden.")
    return match.group(0)


def issue_numbers_in_first_column(section: str, repo: str = _DEFAULT_REPO) -> tuple[int, ...]:
    """Alle Issue-Nummern aus Spalte 1 jeder Tabellenzeile in *section*.

    Zaehlt nur vollstaendige Issue-Markdown-Links (``[#NNN](.../issues/NNN)``)
    in der ersten Spalte und loest damit gruppierte Zeilen wie
    ``#680 / #685 / #686`` korrekt in getrennte Nummern auf (#752). Links in
    anderen Spalten (Titel, Nächster Schritt) zählen bewusst nicht mit - nur
    Spalte 1 ist der dokumentierte, kanonische Issue-Bezug einer Zeile; ein
    Verweis auf eine andere Issue in der Beschreibung ist keine eigene
    Triage-Zeile.
    """
    link_re = _issue_link_re(repo)
    numbers: set[int] = set()
    for row in _TABLE_FIRST_CELL_RE.finditer(section):
        numbers.update(int(m.group(1)) for m in link_re.finditer(row.group(1)))
    return tuple(sorted(numbers))


def parse_triage_issue_numbers(markdown: str, repo: str = _DEFAULT_REPO) -> tuple[int, ...]:
    """Alle in Spalte 1 der Triage-Tabelle referenzierten Issue-Nummern (#752)."""
    return issue_numbers_in_first_column(extract_triage_section(markdown), repo)


def parse_declared_open_count(markdown: str) -> int:
    """Die im Kurzstatus genannte Anzahl offener Issues.

    Wirft :class:`LiveCheckError`, wenn die "Live-Stand"-Zeile fehlt oder
    umformuliert wurde - eine fehlende Deklaration soll den Check sichtbar
    scheitern lassen statt als stillschweigend erfolgreicher Abgleich
    durchzugehen (analog zum fehlenden Triage-Abschnitt).
    """
    match = _LIVE_COUNT_RE.search(markdown)
    if match is None:
        raise LiveCheckError(
            "Zeile 'Live-Stand nach GitHub-Abfrage: **N** offene Issues' nicht gefunden."
        )
    return int(match.group(1))


def open_issues_from_api_payload(payload: object) -> tuple[OpenIssue, ...]:
    """Filtert Pull Requests aus einer GitHub-Issues-API-Antwort heraus.

    Die ``/issues``-API liefert Issues **und** Pull Requests gemeinsam; nur
    Eintraege ohne ``pull_request``-Schluessel sind reguläre Issues.
    """
    if not isinstance(payload, list):
        raise LiveCheckError("Ungueltige Issues-Nutzlast (keine Liste).")
    issues: list[OpenIssue] = []
    for item in payload:
        if not isinstance(item, dict) or "pull_request" in item:
            continue
        number = item.get("number")
        title = item.get("title")
        if isinstance(number, int) and isinstance(title, str):
            issues.append(OpenIssue(number=number, title=title))
    return tuple(issues)


def fetch_open_issues(
    repo: str = _DEFAULT_REPO,
    *,
    token: str | None = None,
    timeout: float = 10.0,
) -> tuple[OpenIssue, ...]:
    """Alle offenen regulären Issues aus der GitHub-API (paginiert).

    Wirft :class:`LiveCheckError` bei jedem Netzwerk-/Antwortfehler - anders
    als ``app_update.check_for_update`` ist dies ein aktiv ausgefuehrtes
    Diagnosewerkzeug, kein still tolerierter Hintergrund-Check.
    """
    headers = dict(_REQUEST_HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    issues: list[OpenIssue] = []
    page = 1
    while True:
        url = f"{_ISSUES_API_URL.format(repo=repo)}?state=open&per_page=100&page={page}"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise LiveCheckError(f"GitHub-Issues-Abfrage fehlgeschlagen (HTTP {e.code}).") from e
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as e:
            raise LiveCheckError(f"GitHub-Issues-Abfrage nicht erreichbar: {e}") from e
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise LiveCheckError(f"Ungueltige Antwort der GitHub-Issues-API: {e}") from e

        if not isinstance(payload, list):
            raise LiveCheckError("Ungueltige Antwort der GitHub-Issues-API (keine Liste).")
        issues.extend(open_issues_from_api_payload(payload))
        if len(payload) < 100:
            break
        page += 1
    return tuple(issues)


def compare(
    triage_numbers: Sequence[int],
    open_issues: Sequence[OpenIssue],
    declared_count: int | None,
) -> LiveCheckReport:
    """Vergleicht Triage-Nummern gegen tatsaechlich offene Issues."""
    triage_set = set(triage_numbers)
    open_set = {issue.number for issue in open_issues}
    return LiveCheckReport(
        declared_count=declared_count,
        actual_count=len(open_issues),
        missing_open=tuple(sorted(open_set - triage_set)),
        closed_but_listed=tuple(sorted(triage_set - open_set)),
    )


def run(
    markdown: str,
    open_issues: Sequence[OpenIssue],
    repo: str = _DEFAULT_REPO,
) -> LiveCheckReport:
    """Parst *markdown* und vergleicht es gegen *open_issues*."""
    return compare(
        parse_triage_issue_numbers(markdown, repo),
        open_issues,
        parse_declared_open_count(markdown),
    )


def format_report(report: LiveCheckReport) -> str:
    """Menschenlesbarer, deterministisch sortierter Bericht (Fehler zuerst)."""
    lines: list[str] = []
    if report.missing_open:
        lines.append(
            "FEHLER  fehlende offene Issues (offen auf GitHub, nicht in der Triage-Tabelle): "
            + ", ".join(f"#{n}" for n in report.missing_open)
        )
    if report.closed_but_listed:
        lines.append(
            "FEHLER  weiterhin als offen gefuehrte, tatsaechlich geschlossene Issues: "
            + ", ".join(f"#{n}" for n in report.closed_but_listed)
        )
    if report.declared_count is not None and report.declared_count != report.actual_count:
        lines.append(
            f"FEHLER  abweichende Gesamtzahl: Datei nennt {report.declared_count}, "
            f"GitHub meldet {report.actual_count} offene Issues."
        )
    if not lines:
        lines.append(f"ok      Live-Stand deckungsgleich ({report.actual_count} offene Issues).")
    return "\n".join(lines)


def write_report(path: Path, text: str) -> None:
    """Persistiert den Bericht fuer Actions-Summary und Diagnose-Artefakt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=_DEFAULT_REPO, help="owner/repo (Default: %(default)s)")
    parser.add_argument(
        "--file",
        type=Path,
        default=_DEFAULT_RECOMMENDATIONS_PATH,
        help="Zu pruefende Recommendations-Datei (Default: RECOMMENDATIONS.md)",
    )
    parser.add_argument(
        "--data",
        type=Path,
        help="Gespeicherte GitHub-Issues-API-Antwort (JSON-Liste) statt Live-Abfrage",
    )
    parser.add_argument(
        "--token", default=None, help="GitHub-Token (optional, erhoeht das Rate-Limit)"
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        help="Bericht zusaetzlich als UTF-8-Datei sichern (auch bei Fehlern)",
    )
    args = parser.parse_args(argv)

    try:
        markdown = args.file.read_text(encoding="utf-8")
        if args.data is not None:
            payload = json.loads(args.data.read_text(encoding="utf-8"))
            open_issues = open_issues_from_api_payload(payload)
        else:
            open_issues = fetch_open_issues(args.repo, token=args.token)
        report = run(markdown, open_issues, args.repo)
    except (LiveCheckError, OSError, json.JSONDecodeError) as exc:
        error_report = f"FEHLER  Live-Check nicht ausfuehrbar: {exc}"
        print(f"::error::{exc}", file=sys.stderr)
        if args.report_output is not None:
            try:
                write_report(args.report_output, error_report)
            except OSError as report_exc:
                print(
                    f"::error::Bericht konnte nicht geschrieben werden: {report_exc}",
                    file=sys.stderr,
                )
        return 2

    report_text = format_report(report)
    if args.report_output is not None:
        try:
            write_report(args.report_output, report_text)
        except OSError as exc:
            print(f"::error::Bericht konnte nicht geschrieben werden: {exc}", file=sys.stderr)
            return 2
    print(report_text)
    return 1 if report.has_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
