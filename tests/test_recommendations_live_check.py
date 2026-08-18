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


def _md(*, links: str, body: str = "") -> str:
    """Baut ein minimales Recommendations-Dokument mit Kurzstatus + Triage."""
    return (
        f"## Aktueller Stand (2026-08-01, Test)\n\n"
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
    markdown = _md(links=row)
    assert lc.parse_triage_issue_numbers(markdown) == (680, 685, 686)


def test_parse_triage_issue_numbers_ignores_plain_text_mentions() -> None:
    """Reine Textnennungen wie 'PR #756' oder Ranges '#742–#747' zählen nicht.

    Nur vollständige Issue-Markdown-Links in Spalte 1 sind kanonisch; ohne
    diese Einschränkung würde die Range '#742–#747' fälschlich nur #742
    beisteuern und Prosa-Erwähnungen wie 'PR #756' als Issue-Referenz zählen.
    """
    row = f"| {_link(741)} | erledigt via PR #756/#759–#761, siehe #742–#747 |\n"
    markdown = _md(links=row)
    assert lc.parse_triage_issue_numbers(markdown) == (741,)


def test_parse_triage_issue_numbers_ignores_historical_archive() -> None:
    """Issues, die nur im Archiv 'Vorige Runden' auftauchen, zählen nicht."""
    row = f"| {_link(752)} | aktuell offen |\n"
    markdown = _md(links=row)
    # #740 kommt nur im Archiv-Teil von _md() vor.
    assert lc.parse_triage_issue_numbers(markdown) == (752,)


def test_parse_triage_issue_numbers_missing_section_raises() -> None:
    with pytest.raises(lc.LiveCheckError):
        lc.parse_triage_issue_numbers("# Nur eine Überschrift ohne Triage-Abschnitt\n")


def test_parse_triage_issue_numbers_ignores_links_outside_first_column() -> None:
    """Ein Issue-Link in Titel/Nächster-Schritt zählt nicht als eigene Triage-Zeile.

    Nur Spalte 1 ist der dokumentierte, kanonische Issue-Bezug einer Zeile;
    ohne diese Einschränkung würde ein beiläufiger Verweis auf eine andere
    Issue in der Beschreibung fälschlich als eigener Tabelleneintrag zählen.
    """
    row = f"| {_link(741)} | siehe auch {_link(692)} für Kontext |\n"
    markdown = _md(links=row)
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
    )
    assert report.closed_but_listed == (740,)
    assert report.missing_open == ()
    assert report.has_findings


def test_compare_clean_state_has_no_findings() -> None:
    report = lc.compare(
        triage_numbers=(741, 748),
        open_issues=[lc.OpenIssue(741, "Epic"), lc.OpenIssue(748, "Update")],
    )
    assert not report.has_findings
    assert "deckungsgleich" in lc.format_report(report)


def test_format_report_lists_every_finding_kind() -> None:
    report = lc.LiveCheckReport(
        actual_count=3,
        missing_open=(758,),
        closed_but_listed=(740,),
    )
    text = lc.format_report(report)
    assert "#758" in text
    assert "#740" in text
    # Beide Befundarten stehen als eigene FEHLER-Zeile im Bericht.
    assert text.count("FEHLER") == 2


def test_write_report_creates_parent_and_trailing_newline(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "report.txt"
    lc.write_report(output, "ok      Testbericht")
    assert output.read_text(encoding="utf-8") == "ok      Testbericht\n"


def test_main_persists_report_for_findings(tmp_path: Path) -> None:
    markdown = tmp_path / "RECOMMENDATIONS.md"
    markdown.write_text(_md(links=f"| {_link(741)} | Epic |\n"), encoding="utf-8")
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
    markdown = _md(links=row)
    open_issues = [lc.OpenIssue(741, "Epic"), lc.OpenIssue(748, "Update"), lc.OpenIssue(758, "Neu")]
    report = lc.run(markdown, open_issues)
    assert report.missing_open == (758,)
    assert report.actual_count == 3


# ── Strukturelle Smoke-Prüfung gegen das echte RECOMMENDATIONS.md ──────


def test_real_recommendations_triage_stays_parsable() -> None:
    """RECOMMENDATIONS.md bleibt für den Live-Check parsebar (#752).

    Kein Netzwerkzugriff und keine inhaltliche Aussage über den Bestand: Der
    Triage-Abschnitt muss auffindbar sein und mindestens eine verlinkte
    Issue-Zeile enthalten, damit ein umbenannter oder leer gelaufener
    Abschnitt hier auffällt statt erst im CI-Lauf. Die Übereinstimmung mit
    GitHub prüft der separat ausführbare Live-Check (siehe TESTING.md); seit
    #821 (Stufe 1) gibt es keine zweite, handgepflegte Zahl mehr, gegen die
    hier gegengerechnet werden könnte.
    """
    markdown = (ROOT / "RECOMMENDATIONS.md").read_text(encoding="utf-8")
    triage_numbers = lc.parse_triage_issue_numbers(markdown)
    assert triage_numbers, "Triage-Tabelle enthält keine verlinkte Issue-Zeile."


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


# ── Schreibmodus: Triage-Tabelle fortschreiben (#821, Stufe 2) ─────────────


def _table(*rows: str) -> str:
    """Ein Triage-Abschnitt mit sechsspaltigem Kopf und *rows* als Datenzeilen."""
    head = (
        "## Offene GitHub-Issues – Triage-Stand (2026-08-01)\n\n"
        "| # | Titel | Relevanz | Komplexität | Modell | Nächster Schritt |\n"
        "|---|-------|----------|-------------|--------|------------------|\n"
    )
    return head + "".join(f"{row}\n" for row in rows) + "\n### Als Nächstes\n\n1. Nichts.\n"


def _rated(number: int, note: str = "Bewertung") -> str:
    return f"| {_link(number)} | Titel {number} | 🟠 Hoch | 🟡 Mittel | Opus | {note} |"


def test_update_triage_table_keeps_rated_rows_verbatim() -> None:
    """Bestehende Zeilen bleiben wortgleich - Bewertungen sind Handarbeit."""
    row = _rated(741, "Sehr spezifischer nächster Schritt")
    section = _table(row)
    updated = lc.update_triage_table(section, [lc.OpenIssue(741, "Ganz anderer Titel")])
    assert row in updated
    assert "Ganz anderer Titel" not in updated


def test_update_triage_table_drops_row_of_closed_issue() -> None:
    section = _table(_rated(741), _rated(748))
    updated = lc.update_triage_table(section, [lc.OpenIssue(741, "Epic")])
    assert _link(741) in updated
    assert _link(748) not in updated


def test_update_triage_table_appends_unrated_row_for_new_issue() -> None:
    section = _table(_rated(741))
    updated = lc.update_triage_table(section, [lc.OpenIssue(741, "Epic"), lc.OpenIssue(999, "Neu")])
    assert f"| {_link(999)} | Neu | TODO | TODO | TODO | TODO |" in updated


def test_update_triage_table_preserves_existing_order_and_appends_at_end() -> None:
    """Die Reihenfolge ist thematisch gruppiert, nicht sortiert - nie umsortieren."""
    section = _table(_rated(748), _rated(741))
    updated = lc.update_triage_table(
        section, [lc.OpenIssue(741, "Epic"), lc.OpenIssue(748, "Update"), lc.OpenIssue(300, "Neu")]
    )
    positions = [updated.index(_link(n)) for n in (748, 741, 300)]
    assert positions == sorted(positions)


def test_update_triage_table_is_idempotent() -> None:
    section = _table(_rated(741))
    issues = [lc.OpenIssue(741, "Epic"), lc.OpenIssue(999, "Neu")]
    once = lc.update_triage_table(section, issues)
    assert lc.update_triage_table(once, issues) == once


def test_update_triage_table_keeps_grouped_row_while_one_issue_stays_open() -> None:
    """Eine Zeile mit mehreren Issues bleibt, solange eines davon offen ist."""
    grouped = f"| {_link(680)} / {_link(685)} | Sammelzeile | 🟢 | 🟢 | – | offen |"
    section = _table(grouped)
    updated = lc.update_triage_table(section, [lc.OpenIssue(685, "Noch offen")])
    assert grouped in updated


def test_render_triage_row_escapes_pipe_in_title() -> None:
    """Ein Pipe im Titel darf die Tabellenstruktur nicht zerlegen."""
    row = lc.render_triage_row(lc.OpenIssue(999, "a | b"), columns=6)
    assert row.count("|") == 7 + 1  # 7 Trenner der 6 Spalten + das maskierte Pipe
    assert r"a \| b" in row


def test_update_markdown_leaves_surrounding_sections_untouched() -> None:
    markdown = (
        "## Aktueller Stand (2026-08-01, Test)\n\nKurzstatus bleibt.\n\n"
        + _table(_rated(741))
        + "\n## Vorige Runden\n\n- Archiv bleibt.\n"
    )
    updated = lc.update_markdown(markdown, [lc.OpenIssue(741, "Epic")])
    assert "Kurzstatus bleibt." in updated
    assert "- Archiv bleibt." in updated
    assert "### Als Nächstes" in updated


def test_unrated_issue_numbers_finds_generated_rows() -> None:
    markdown = _table(_rated(741), lc.render_triage_row(lc.OpenIssue(999, "Neu"), columns=6))
    assert lc.unrated_issue_numbers(markdown) == (999,)


def test_unrated_issue_numbers_ignores_todo_inside_prose() -> None:
    """Nur eine Zelle, die exakt der Marker ist, gilt als unbewertet."""
    row = _rated(741, "Noch TODO: Messwerte nachtragen")
    assert lc.unrated_issue_numbers(_table(row)) == ()


def test_update_triage_table_rejects_interrupted_table() -> None:
    section = (
        "## Offene GitHub-Issues – Triage-Stand (2026-08-01)\n\n"
        "| # | Titel |\n|---|-------|\n"
        f"{_rated(741)}\nFremdzeile mittendrin\n{_rated(748)}\n"
    )
    with pytest.raises(lc.LiveCheckError, match="unterbrochen"):
        lc.update_triage_table(section, [lc.OpenIssue(741, "Epic")])


def test_extract_triage_section_rejects_unknown_language() -> None:
    with pytest.raises(lc.LiveCheckError, match="Unbekannte Sprachfassung"):
        lc.extract_triage_section(_table(_rated(741)), lang="xx")


def test_extract_triage_section_works_for_every_shipped_language() -> None:
    """Jede der sechs Fassungen muss mit ihrem eigenen Anker parsebar sein."""
    for lang, relative in lc.RECOMMENDATION_DOCS.items():
        markdown = (ROOT / relative).read_text(encoding="utf-8")
        assert lc.issue_numbers_in_first_column(lc.extract_triage_section(markdown, lang)), lang
