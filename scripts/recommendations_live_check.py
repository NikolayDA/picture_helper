#!/usr/bin/env python3
"""GitHub-Live-Check fuer den Recommendations-Kurzstatus (#752).

`RECOMMENDATIONS.md` driftete wiederholt kurz nach einer Aktualisierung vom
tatsaechlichen GitHub-Stand ab (#669, #728, erneut #752). Dieses Modul
vergleicht die **Triage-Tabelle** (Abschnitt ``## Offene GitHub-Issues``, vor
dem historischen Archiv ``## Vorige Runden``) mit den tatsaechlich offenen
GitHub-Issues und meldet:

- offene Issues, die in der Tabelle fehlen,
- Issues, die die Tabelle als offen fuehrt, obwohl sie auf GitHub bereits
  geschlossen sind.

Die Anzahl offener Issues wird **abgeleitet**, nicht deklariert (#821,
Stufe 1): Frueher nannte der Kurzstatus sie zusaetzlich als eigene Zahl, die
in sechs Sprachfassungen von Hand gepflegt werden musste. Sie war gegenueber
dem Mengenvergleich redundant - stimmen die Mengen ueberein, stimmen auch die
Anzahlen - und driftete regelmaessig gegen die Tabelle (#669, #728, #752,
#777). Der Bericht nennt die Anzahl weiterhin, liest sie aber aus der Tabelle.

Nur die Zeilen des Triage-Abschnitts zaehlen; das Archiv ``## Vorige Runden``
ist bewusst historisch und wird nicht geprueft (siehe TESTING.md). Referenziert
wird ausschliesslich ueber vollstaendige Issue-Markdown-Links
(``[#NNN](.../issues/NNN)``) in Spalte 1 jeder Tabellenzeile - das loest
gruppierte Zeilen wie ``[#680](...) / [#685](...) / [#686](...)`` korrekt in
drei Nummern auf, ohne PR-Erwaehnungen oder Zahlen-Ranges in Fliesstext
("#742-#747") faelschlich als Issue-Referenz zu werten.

Mit ``--write`` schreibt dasselbe Werkzeug den Bestand zurueck (#821, Stufe 2):
Zeilen geschlossener Issues entfallen, neu offene Issues bekommen eine Zeile mit
Nummer und Titel aus der API sowie ``TODO`` in den redaktionellen Spalten.
Bestehende Zeilen werden **nie** veraendert - Relevanz, Komplexitaet, Modell und
"Naechster Schritt" sind die eigentliche redaktionelle Leistung, die kein
Generator ersetzt, und Spalte 2 bleibt unangetastet, damit handgepflegte
Uebersetzungen erhalten bleiben. Auch die Reihenfolge bleibt erhalten (sie ist
thematisch gruppiert, nicht sortiert); neue Zeilen haengen hinten an.

Eine **gruppierte** Zeile (mehrere Issue-Links in Spalte 1, z. B.
``[#680](...) / [#685](...) / [#686](...)``) bleibt unveraendert stehen,
solange **mindestens eines** ihrer Issues offen ist - auch wenn andere Issues
der Gruppe bereits geschlossen sind. ``--write`` trennt eine solche Zeile
nicht automatisch auf (das waere ein Eingriff in eine redaktionelle Zeile
und widerspraeche der Regel oben); der Live-Check meldet die geschlossene
Nummer in diesem Fall dauerhaft als ``closed_but_listed``, bis die Zeile von
Hand aufgeteilt wird (#829, Befund 4).

Die Kernlogik (``parse_triage_issue_numbers``, ``open_issues_from_api_payload``,
``compare``, ``update_triage_table``) ist rein und netzfrei; nur
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

#: Der Triage-Abschnitt beginnt bei der Bestands-Ueberschrift und endet vor der
#: naechsten Ueberschrift zweiter Ordnung (insbesondere "## Vorige Runden").
#: Je Sprachfassung ein eigener Anker - die **einzige** Quelle dieser Muster,
#: aus der auch tests/test_recommendations_freeze_consistency.py liest (#821).
TRIAGE_SECTION_PATTERNS: Final[dict[str, re.Pattern[str]]] = {
    "de": re.compile(r"(?ms)^## Offene GitHub-Issues.*?(?=^## |\Z)"),
    "en": re.compile(r"(?ms)^## Open GitHub Issues.*?(?=^## |\Z)"),
    "es": re.compile(r"(?ms)^## Incidencias abiertas de GitHub.*?(?=^## |\Z)"),
    "fr": re.compile(r"(?ms)^## Tickets GitHub ouverts.*?(?=^## |\Z)"),
    "uk": re.compile(r"(?ms)^## Відкриті задачі GitHub.*?(?=^## |\Z)"),
    "zh": re.compile(r"(?ms)^## GitHub 未结议题.*?(?=^## |\Z)"),
}
_DEFAULT_LANG: Final = "de"

#: Pfad je Sprachfassung, relativ zum Repository-Wurzelverzeichnis.
RECOMMENDATION_DOCS: Final[dict[str, str]] = {
    "de": "RECOMMENDATIONS.md",
    "en": "docs/i18n/en/RECOMMENDATIONS.md",
    "es": "docs/i18n/es/RECOMMENDATIONS.md",
    "fr": "docs/i18n/fr/RECOMMENDATIONS.md",
    "uk": "docs/i18n/uk/RECOMMENDATIONS.md",
    "zh": "docs/i18n/zh/RECOMMENDATIONS.md",
}

#: Platzhalter in den redaktionellen Spalten einer frisch generierten Zeile.
#: Exakt verglichen (Zellinhalt == Marker), damit ein "TODO" im Fliesstext
#: einer bewerteten Zeile nicht faelschlich als unbewertet gilt.
UNRATED_PLACEHOLDER: Final = "TODO"
#: Spalte 1 jeder Tabellenzeile (Text zwischen dem ersten und zweiten "|").
_TABLE_FIRST_CELL_RE: Final = re.compile(r"(?m)^\|([^|]*)\|")


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

    actual_count: int
    missing_open: tuple[int, ...]
    closed_but_listed: tuple[int, ...]

    @property
    def has_findings(self) -> bool:
        return bool(self.missing_open or self.closed_but_listed)


class LiveCheckError(RuntimeError):
    """Dokument-, Netzwerk- oder Antwortfehler beim Live-Check."""


def extract_triage_section(markdown: str, lang: str = _DEFAULT_LANG) -> str:
    """Der Text des Triage-Abschnitts, ohne das historische Archiv.

    Wirft :class:`LiveCheckError`, wenn der Abschnitt fehlt - ein umbenannter
    oder geloeschter Abschnitt soll den Check sichtbar scheitern lassen statt
    still eine leere Tabelle zu melden.
    """
    pattern = TRIAGE_SECTION_PATTERNS.get(lang)
    if pattern is None:
        raise LiveCheckError(f"Unbekannte Sprachfassung: {lang!r}")
    match = pattern.search(markdown)
    if match is None:
        raise LiveCheckError(f"Triage-Abschnitt nicht gefunden (Sprache {lang}).")
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


def parse_triage_issue_numbers(
    markdown: str, repo: str = _DEFAULT_REPO, lang: str = _DEFAULT_LANG
) -> tuple[int, ...]:
    """Alle in Spalte 1 der Triage-Tabelle referenzierten Issue-Nummern (#752)."""
    return issue_numbers_in_first_column(extract_triage_section(markdown, lang), repo)


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
) -> LiveCheckReport:
    """Vergleicht Triage-Nummern gegen tatsaechlich offene Issues."""
    triage_set = set(triage_numbers)
    open_set = {issue.number for issue in open_issues}
    return LiveCheckReport(
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
    return compare(parse_triage_issue_numbers(markdown, repo), open_issues)



# ── Schreibmodus: Triage-Tabelle aus dem Live-Stand fortschreiben (#821) ──


def table_span(lines: list[str]) -> tuple[int, int]:
    """Index der ersten und letzten Tabellenzeile (Kopf, Trenner, Datenzeilen).

    Wirft :class:`LiveCheckError`, wenn keine oder eine unterbrochene Tabelle
    gefunden wird - lieber sichtbar abbrechen als eine halbe Tabelle
    ueberschreiben.

    Bewusst oeffentlich (#851): Auch ``tests/test_recommendations_docs.py``
    muss Kopfzeile und Datenzeilenmenge genau so bestimmen wie der
    ``--write``-Pfad. Eine eigene Heuristik dort wuerde still untererfassen -
    eine Zeile, die nicht mit einem Issue-Link beginnt, faellt durchs Raster,
    und genau sie kann das unmaskierte Pipe tragen.
    """
    indices = [i for i, line in enumerate(lines) if line.startswith("|")]
    if len(indices) < 3:
        raise LiveCheckError("Triage-Abschnitt enthaelt keine vollstaendige Tabelle.")
    if indices != list(range(indices[0], indices[-1] + 1)):
        raise LiveCheckError("Triage-Tabelle ist durch Fremdzeilen unterbrochen.")
    return indices[0], indices[-1]


#: Zellentrenner einer GFM-Tabellenzeile: ein Pipe, das **nicht** mit einem
#: Backslash maskiert ist. Ein maskiertes ``\|`` gehoert zum Zellinhalt und
#: rendert dort als literales Pipe - genau die Schreibweise, die
#: :func:`render_triage_row` fuer Titel mit Pipe selbst erzeugt.
_CELL_SEPARATOR: Final = re.compile(r"(?<!\\)\|")


def cells(row: str) -> list[str]:
    r"""Die Zellen einer Markdown-Tabellenzeile (ohne fuehrende/schliessende Pipe).

    Maskierungsbewusst und bewusst oeffentlich (#851): Es gibt genau **eine**
    Regel, was eine Zelle ist, und sowohl das Skript als auch
    ``tests/test_recommendations_docs.py`` benutzen sie.

    Die naive Fassung (``split("|")``) hat ein maskiertes ``\|`` als Trenner
    mitgezaehlt. Folge, an einer handgepflegten Bewertungszelle reproduziert:
    ``Fix in a \| TODO`` zerfiel in ``Fix in a \`` und ``TODO`` - der zweite
    Teil ist exakt :data:`UNRATED_PLACEHOLDER`, also meldete
    :func:`unrated_issue_numbers` eine vollstaendig bewertete Zeile als
    unbewertet und ``--write`` endete mit Exit 1. Ausgeloest wurde das
    ausgerechnet von der Empfehlung des Doku-Waechters, ein Pipe in einer
    Zelle als ``\|`` zu schreiben.

    Die aeusseren Delimiter werden mit ``removeprefix``/``removesuffix``
    genau einmal entfernt, nicht mit ``strip("|")``: Letzteres frisst eine
    leere Randzelle mit (``| a | b ||`` ergaebe 2 statt 3 Zellen) und liesse
    den Doku-Waechter falsch-rot anschlagen - die Gegenrichtung des Schadens,
    den er finden soll.
    """
    inner = row.strip().removeprefix("|").removesuffix("|")
    return [cell.strip() for cell in _CELL_SEPARATOR.split(inner)]


def render_triage_row(issue: OpenIssue, columns: int, repo: str = _DEFAULT_REPO) -> str:
    """Eine neue, noch unbewertete Tabellenzeile fuer *issue*.

    Nummer und Titel stammen aus der API, alle redaktionellen Spalten tragen
    :data:`UNRATED_PLACEHOLDER`. Pipes im Titel werden maskiert, damit ein
    Titel wie ``a | b`` die Tabellenstruktur nicht zerlegt.

    Spalte 2 (Titel) erhaelt bewusst den unuebersetzten API-Titel, identisch
    in allen sechs Sprachfassungen - anders als die redaktionellen Spalten
    gibt es dafuer keinen Platzhalter, der die fehlende Uebersetzung sichtbar
    machen wuerde. Das ist eine akzeptierte Eigenschaft, keine Luecke:
    ``unrated_issue_numbers()`` und die Freeze-Konsistenzpruefung
    (``tests/test_recommendations_freeze_consistency.py``) melden nichts,
    sobald die redaktionellen Spalten ausgefuellt sind, auch wenn der Titel
    in einer nicht-deutschen Fassung unuebersetzt geblieben ist. Die
    Uebersetzung bleibt Handarbeit, die TESTING.md benennt, aber keine
    Pruefung erzwingt (#829, Befund 5).
    """
    title = issue.title.replace("|", "\\|").strip()
    link = f"[#{issue.number}](https://github.com/{repo}/issues/{issue.number})"
    rest = [UNRATED_PLACEHOLDER] * max(columns - 2, 0)
    return "| " + " | ".join([link, title, *rest]) + " |"


def update_triage_table(
    section: str, open_issues: Sequence[OpenIssue], repo: str = _DEFAULT_REPO
) -> str:
    """Schreibt die Tabelle in *section* auf den Stand von *open_issues* fort.

    Bestehende Zeilen bleiben **wortgleich und in ihrer Reihenfolge** erhalten,
    solange ihr Issue offen ist; Zeilen geschlossener Issues entfallen; neu
    offene Issues haengen als unbewertete Zeilen hinten an. Alles ausserhalb
    der Tabelle (Ueberschrift, Folgeabschnitte) bleibt unberuehrt.

    Eine gruppierte Zeile mit mehreren Issue-Nummern bleibt komplett stehen,
    solange eines ihrer Issues offen ist - eine bereits geschlossene Nummer
    darin wird nicht entfernt (siehe Modul-Docstring, #829 Befund 4).
    """
    lines = section.split("\n")
    first, last = table_span(lines)
    header, separator = lines[first], lines[first + 1]
    columns = len(cells(header))
    link_re = _issue_link_re(repo)
    open_numbers = {issue.number for issue in open_issues}

    kept: list[str] = []
    covered: set[int] = set()
    for row in lines[first + 2 : last + 1]:
        numbers = {int(m.group(1)) for m in link_re.finditer(cells(row)[0])}
        if numbers and not (numbers & open_numbers):
            continue  # jedes Issue dieser Zeile ist geschlossen
        kept.append(row)
        covered |= numbers

    new_rows = [
        render_triage_row(issue, columns, repo)
        for issue in open_issues
        if issue.number not in covered
    ]
    table = [header, separator, *kept, *new_rows]
    return "\n".join([*lines[:first], *table, *lines[last + 1 :]])


def update_markdown(
    markdown: str,
    open_issues: Sequence[OpenIssue],
    repo: str = _DEFAULT_REPO,
    lang: str = _DEFAULT_LANG,
) -> str:
    """Ersetzt den Triage-Abschnitt in *markdown* durch seine fortgeschriebene Fassung."""
    section = extract_triage_section(markdown, lang)
    return markdown.replace(section, update_triage_table(section, open_issues, repo), 1)


def unrated_issue_numbers(
    markdown: str, repo: str = _DEFAULT_REPO, lang: str = _DEFAULT_LANG
) -> tuple[int, ...]:
    """Issue-Nummern der Zeilen, die noch :data:`UNRATED_PLACEHOLDER` tragen."""
    section = extract_triage_section(markdown, lang)
    lines = section.split("\n")
    first, last = table_span(lines)
    link_re = _issue_link_re(repo)
    numbers: set[int] = set()
    for row in lines[first + 2 : last + 1]:
        row_cells = cells(row)
        if any(cell == UNRATED_PLACEHOLDER for cell in row_cells):
            numbers.update(int(m.group(1)) for m in link_re.finditer(row_cells[0]))
    return tuple(sorted(numbers))


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
    if not lines:
        lines.append(f"ok      Live-Stand deckungsgleich ({report.actual_count} offene Issues).")
    return "\n".join(lines)


def write_report(path: Path, text: str) -> None:
    """Persistiert den Bericht fuer Actions-Summary und Diagnose-Artefakt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")



def _load_open_issues(args: argparse.Namespace) -> tuple[OpenIssue, ...]:
    """Offene Issues aus der API oder aus einer gespeicherten Antwort (``--data``)."""
    if args.data is not None:
        return open_issues_from_api_payload(json.loads(args.data.read_text(encoding="utf-8")))
    return fetch_open_issues(args.repo, token=args.token)


def _write_all(open_issues: Sequence[OpenIssue], repo: str) -> int:
    """Schreibt alle sechs Sprachfassungen fort und meldet unbewertete Zeilen.

    Rueckgabe 1, wenn danach Zeilen ohne Bewertung stehen - der Generator
    liefert nur Nummer und Titel, die redaktionellen Spalten bleiben Handarbeit
    (#821). Ein Aufrufer soll das als offene Aufgabe sehen, nicht als Erfolg.
    """
    unrated: dict[str, tuple[int, ...]] = {}
    for lang, relative in RECOMMENDATION_DOCS.items():
        path = _REPO_ROOT / relative
        markdown = path.read_text(encoding="utf-8")
        updated = update_markdown(markdown, open_issues, repo, lang)
        if updated != markdown:
            path.write_text(updated, encoding="utf-8")
            print(f"{lang}: aktualisiert ({relative})")
        else:
            print(f"{lang}: unveraendert ({relative})")
        found = unrated_issue_numbers(updated, repo, lang)
        if found:
            unrated[lang] = found
    if unrated:
        for lang, numbers in sorted(unrated.items()):
            joined = ", ".join(f"#{n}" for n in numbers)
            print(f"OFFEN   {lang}: unbewertete Zeilen ({UNRATED_PLACEHOLDER}): {joined}")
        print("Bewertungsspalten von Hand ausfuellen, dann erneut pruefen.")
        return 1
    return 0


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
    parser.add_argument(
        "--write",
        action="store_true",
        help="Triage-Tabellen aller sechs Sprachfassungen auf den Live-Stand "
             "fortschreiben, statt nur zu pruefen (#821, Stufe 2)",
    )
    args = parser.parse_args(argv)

    if args.write:
        try:
            open_issues = _load_open_issues(args)
        except (LiveCheckError, OSError, json.JSONDecodeError) as exc:
            print(f"::error::{exc}", file=sys.stderr)
            return 2
        return _write_all(open_issues, args.repo)

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
