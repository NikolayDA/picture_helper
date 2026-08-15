"""Netzfreie Tests für den Recommendations-GitHub-Live-Check (#752).

Nur ``fetch_open_issues``/``main`` sprechen das Netzwerk an; diese Suite
deckt ausschließlich die reine Kernlogik über gespeicherte Fixtures ab, wie
von #752 verlangt ("benötigt in der Default-Suite weder Netzwerk noch
GitHub-Token").
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import recommendations_live_check as lc

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "recommendations_live_check"


def _md(*, count: int, links: str, body: str = "") -> str:
    """Baut ein minimales Recommendations-Dokument mit Kurzstatus + Triage."""
    return (
        f"## Aktueller Stand (2026-08-01, Test)\n\n"
        f"Live-Stand nach GitHub-Abfrage: **{count}** offene Issues.\n\n"
        f"## Offene GitHub-Issues – Triage-Stand (2026-08-01)\n\n"
        f"| # | Titel |\n|---|---|\n{links}\n{body}"
        f"## Vorige Runden\n\n"
        f"- **2026-07-01** — [#740](https://github.com/NikolayDA/picture_helper/issues/740) "
        f"als historischer Eintrag; wird von der Triage-Extraktion ignoriert.\n"
    )


def _link(number: int, repo: str = lc._DEFAULT_REPO) -> str:
    return f"[#{number}](https://github.com/{repo}/issues/{number})"


# ── parse_triage_issue_numbers ──────────────────────────────────────────


def test_parse_triage_issue_numbers_resolves_grouped_row() -> None:
    """Eine gruppierte Zeile wie '#680 / #685 / #686' ergibt drei Nummern (#752)."""
    row = f"| {_link(680)} / {_link(685)} / {_link(686)} | v2.7.1 – überholt |\n"
    markdown = _md(count=3, links=row)
    assert lc.parse_triage_issue_numbers(markdown) == (680, 685, 686)


def test_parse_triage_issue_numbers_ignores_plain_text_mentions() -> None:
    """Reine Textnennungen wie 'PR #756' oder Ranges '#742–#747' zählen nicht.

    Nur vollständige Issue-Markdown-Links in Spalte 1 sind kanonisch; ohne
    diese Einschränkung würde die Range '#742–#747' fälschlich nur #742
    beisteuern und Prosa-Erwähnungen wie 'PR #756' als Issue-Referenz zählen.
    """
    row = f"| {_link(741)} | erledigt via PR #756/#759–#761, siehe #742–#747 |\n"
    markdown = _md(count=1, links=row)
    assert lc.parse_triage_issue_numbers(markdown) == (741,)


def test_parse_triage_issue_numbers_ignores_historical_archive() -> None:
    """Issues, die nur im Archiv 'Vorige Runden' auftauchen, zählen nicht."""
    row = f"| {_link(752)} | aktuell offen |\n"
    markdown = _md(count=1, links=row)
    # #740 kommt nur im Archiv-Teil von _md() vor.
    assert lc.parse_triage_issue_numbers(markdown) == (752,)


def test_parse_triage_issue_numbers_missing_section_raises() -> None:
    with pytest.raises(lc.LiveCheckError):
        lc.parse_triage_issue_numbers("# Nur eine Überschrift ohne Triage-Abschnitt\n")


def test_parse_declared_open_count() -> None:
    markdown = _md(count=42, links="")
    assert lc.parse_declared_open_count(markdown) == 42


def test_parse_declared_open_count_missing_raises() -> None:
    """Eine fehlende/umformulierte Live-Stand-Zeile scheitert sichtbar (fail-closed).

    Ohne das würde ein versehentlich entfernter Kurzstatus-Satz mit `exit 0`
    als "deckungsgleich" durchgehen, obwohl gar nichts geprüft wurde.
    """
    with pytest.raises(lc.LiveCheckError):
        lc.parse_declared_open_count("keine Live-Stand-Zeile hier")


def test_parse_triage_issue_numbers_ignores_links_outside_first_column() -> None:
    """Ein Issue-Link in Titel/Nächster-Schritt zählt nicht als eigene Triage-Zeile.

    Nur Spalte 1 ist der dokumentierte, kanonische Issue-Bezug einer Zeile;
    ohne diese Einschränkung würde ein beiläufiger Verweis auf eine andere
    Issue in der Beschreibung fälschlich als eigener Tabelleneintrag zählen.
    """
    row = f"| {_link(741)} | siehe auch {_link(692)} für Kontext |\n"
    markdown = _md(count=1, links=row)
    assert lc.parse_triage_issue_numbers(markdown) == (741,)


# ── open_issues_from_api_payload ────────────────────────────────────────


def test_open_issues_from_api_payload_filters_pull_requests() -> None:
    payload = json.loads((FIXTURE_DIR / "open_issues_sample.json").read_text(encoding="utf-8"))
    issues = lc.open_issues_from_api_payload(payload)
    assert {issue.number for issue in issues} == {758, 752}


def test_open_issues_from_api_payload_rejects_non_list() -> None:
    with pytest.raises(lc.LiveCheckError):
        lc.open_issues_from_api_payload({"not": "a list"})


# ── compare / Regressionsfixturen für dokumentierten Drift ─────────────


def test_compare_flags_missing_open_issue() -> None:
    """Ein auf GitHub offenes, in der Tabelle fehlendes Issue wird gemeldet.

    Reproduziert das im Issue #752 dokumentierte Drift-Muster: #758 war neu
    offen, fehlte aber vollständig in der Triage-Tabelle.
    """
    report = lc.compare(
        triage_numbers=(741, 748),
        open_issues=[
            lc.OpenIssue(741, "Epic"),
            lc.OpenIssue(748, "Update"),
            lc.OpenIssue(758, "Neu"),
        ],
        declared_count=2,
    )
    assert report.missing_open == (758,)
    assert report.closed_but_listed == ()
    assert report.has_findings


def test_compare_flags_closed_but_listed_issue() -> None:
    """Ein in der Tabelle als offen geführtes, tatsächlich geschlossenes Issue.

    Reproduziert das #752-Drift-Muster um #740: die Tabelle verlangte weiter
    dessen Umsetzung, obwohl es über #750 bereits geschlossen war.
    """
    report = lc.compare(
        triage_numbers=(740, 741),
        open_issues=[lc.OpenIssue(741, "Epic")],
        declared_count=2,
    )
    assert report.closed_but_listed == (740,)
    assert report.missing_open == ()
    assert report.has_findings


def test_compare_flags_count_mismatch_even_without_number_drift() -> None:
    """Eine abweichende Gesamtzahl wird auch ohne Einzelabweichung gemeldet."""
    report = lc.compare(
        triage_numbers=(741,),
        open_issues=[lc.OpenIssue(741, "Epic")],
        declared_count=25,
    )
    assert report.declared_count == 25
    assert report.actual_count == 1
    assert report.missing_open == ()
    assert report.closed_but_listed == ()
    assert report.has_findings


def test_compare_clean_state_has_no_findings() -> None:
    report = lc.compare(
        triage_numbers=(741, 748),
        open_issues=[lc.OpenIssue(741, "Epic"), lc.OpenIssue(748, "Update")],
        declared_count=2,
    )
    assert not report.has_findings
    assert "deckungsgleich" in lc.format_report(report)


def test_format_report_lists_every_finding_kind() -> None:
    report = lc.LiveCheckReport(
        declared_count=2,
        actual_count=3,
        missing_open=(758,),
        closed_but_listed=(740,),
    )
    text = lc.format_report(report)
    assert "#758" in text
    assert "#740" in text
    assert "Datei nennt 2" in text
    assert "GitHub meldet 3" in text


def test_write_report_creates_parent_and_trailing_newline(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "report.txt"
    lc.write_report(output, "ok      Testbericht")
    assert output.read_text(encoding="utf-8") == "ok      Testbericht\n"


def test_main_persists_report_for_findings(tmp_path: Path) -> None:
    markdown = tmp_path / "RECOMMENDATIONS.md"
    markdown.write_text(_md(count=1, links=f"| {_link(741)} | Epic |\n"), encoding="utf-8")
    payload = tmp_path / "issues.json"
    payload.write_text(
        json.dumps([{"number": 741, "title": "Epic"}, {"number": 752, "title": "Neu"}]),
        encoding="utf-8",
    )
    report = tmp_path / "report.txt"

    assert (
        lc.main(["--file", str(markdown), "--data", str(payload), "--report-output", str(report)])
        == 1
    )
    assert "#752" in report.read_text(encoding="utf-8")


def test_main_persists_report_for_input_error(tmp_path: Path) -> None:
    report = tmp_path / "report.txt"
    assert lc.main(["--file", str(tmp_path / "missing.md"), "--report-output", str(report)]) == 2
    assert "nicht ausfuehrbar" in report.read_text(encoding="utf-8")


# ── run() end-to-end auf synthetischem Dokument ─────────────────────────


def test_run_end_to_end_on_synthetic_document() -> None:
    row = f"| {_link(741)} | Epic |\n| {_link(748)} | Update |\n"
    markdown = _md(count=3, links=row)
    open_issues = [lc.OpenIssue(741, "Epic"), lc.OpenIssue(748, "Update"), lc.OpenIssue(758, "Neu")]
    report = lc.run(markdown, open_issues)
    assert report.missing_open == (758,)
    assert report.declared_count == 3
    assert report.actual_count == 3


# ── Strukturelle Smoke-Prüfung gegen das echte RECOMMENDATIONS.md ──────


def test_real_recommendations_triage_matches_its_own_declared_count() -> None:
    """RECOMMENDATIONS.md bleibt für den Live-Check parsebar (#752).

    Kein Netzwerkzugriff: prüft nur, dass die im Kurzstatus genannte Zahl mit
    der Anzahl der in der Triage-Tabelle verlinkten Issues übereinstimmt –
    die eigentliche Übereinstimmung mit GitHub prüft der separat
    ausführbare Live-Check (siehe TESTING.md).
    """
    markdown = (ROOT / "RECOMMENDATIONS.md").read_text(encoding="utf-8")
    triage_numbers = lc.parse_triage_issue_numbers(markdown)
    declared = lc.parse_declared_open_count(markdown)
    assert len(triage_numbers) == declared, (
        f"Triage-Tabelle listet {len(triage_numbers)} Issues, Kurzstatus behauptet {declared}."
    )


def test_live_workflow_keeps_actionable_report_on_failure() -> None:
    workflow = (ROOT / ".github/workflows/recommendations-live-check.yml").read_text(
        encoding="utf-8"
    )
    assert "--report-output recommendations-live-report.txt" in workflow
    assert workflow.count("if: always()") >= 2
    assert '>> "$GITHUB_STEP_SUMMARY"' in workflow
    assert "actions/upload-artifact@v7" in workflow
    assert "Owner: Repository-Owner" in workflow
    assert "innerhalb eines Arbeitstags" in workflow
