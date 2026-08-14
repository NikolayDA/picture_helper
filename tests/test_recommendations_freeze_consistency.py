"""Verknüpft den Recommendations-Kurzstatus mit kanonischen, lokalen Quellen (#752).

Der ursprüngliche Plan verlangte, den "Protokollierten Kandidaten-SHA" aus dem
Freeze-Dokument gegen alle sechs Sprachfassungen zu prüfen. PR #754 (siehe
Issue-Kommentar auf #752) hat dieses Feld bewusst entfernt: Ein
kandidatenrelevanter Commit kann seinen eigenen SHA nicht enthalten, der
Kandidaten-SHA ist seither erst nach dem Merge über die First-Parent-Historie
ableitbar. Recommendations dürfen daher nicht mehr gezwungen werden, einen
solchen SHA zu wiederholen.

Was lokal, netzfrei und sinnvoll bleibt:

1. Das aktive Freeze-Dokument lässt sich allein aus ``pyproject.toml``
   bestimmen (unverändert Teil des #752-Plans).
2. Alle sechs Sprachfassungen führen dasselbe Kurzstatus-Datum und dieselbe
   im Live-Stand genannte offene Issue-Anzahl - der Teil von #752, der ohne
   GitHub-Zugriff prüfbar bleibt. Der GitHub-Live-Check selbst lebt in
   ``scripts/recommendations_live_check.py`` / ``tests/test_recommendations_live_check.py``.
"""
from __future__ import annotations

import re
from pathlib import Path

from scripts import recommendations_live_check as lc
from scripts import verify_release_freeze as vrf

ROOT = Path(__file__).resolve().parent.parent

RECOMMENDATION_DOCS = {
    "de": ROOT / "RECOMMENDATIONS.md",
    "en": ROOT / "docs/i18n/en/RECOMMENDATIONS.md",
    "es": ROOT / "docs/i18n/es/RECOMMENDATIONS.md",
    "fr": ROOT / "docs/i18n/fr/RECOMMENDATIONS.md",
    "uk": ROOT / "docs/i18n/uk/RECOMMENDATIONS.md",
    "zh": ROOT / "docs/i18n/zh/RECOMMENDATIONS.md",
}

#: Anker für die Kurzstatus-Überschrift je Sprache; Gruppe 1 ist das Datum.
#: Sprachneutral je Datei fest verdrahtet - ändert sich der Wortlaut einer
#: Übersetzung, soll dieser Test bewusst sichtbar scheitern statt still eine
#: falsche Zeile zu matchen.
_STATUS_HEADER_RE = {
    "de": re.compile(r"^## Aktueller Stand \((\d{4}-\d{2}-\d{2})", re.MULTILINE),
    "en": re.compile(r"^## Current Status \((\d{4}-\d{2}-\d{2})", re.MULTILINE),
    "es": re.compile(r"^## Estado actual \((\d{4}-\d{2}-\d{2})", re.MULTILINE),
    "fr": re.compile(r"^## État actuel \((\d{4}-\d{2}-\d{2})", re.MULTILINE),
    "uk": re.compile(r"^## Поточний стан \((\d{4}-\d{2}-\d{2})", re.MULTILINE),
    "zh": re.compile(r"^## 当前状态（(\d{4}-\d{2}-\d{2})", re.MULTILINE),
}

#: Anker für die "Live-Stand"-Zeile je Sprache; Gruppe 1 ist die Anzahl.
_LIVE_COUNT_RE = {
    "de": re.compile(r"Live-Stand nach GitHub-Abfrage: \*\*(\d+)\*\*"),
    "en": re.compile(r"Live state after the GitHub query: \*\*(\d+)\*\*"),
    "es": re.compile(r"Estado en vivo tras la consulta a GitHub: \*\*(\d+)\*\*"),
    "fr": re.compile(r"requête GitHub : \*\*(\d+)\*\*"),
    "uk": re.compile(r"Live-стан після запиту до GitHub: \*\*(\d+)\*\*"),
    "zh": re.compile(r"查询后的实时状态：\*\*(\d+)\*\*"),
}

#: Anker für den Beginn des Triage-Abschnitts je Sprache; endet vor der
#: nächsten Überschrift zweiter Ordnung (dasselbe Muster wie
#: ``recommendations_live_check._TRIAGE_SECTION_RE``, nur je Sprache verdrahtet
#: statt fest auf die deutsche Überschrift beschränkt).
_TRIAGE_SECTION_RE = {
    "de": re.compile(r"(?ms)^## Offene GitHub-Issues.*?(?=^## |\Z)"),
    "en": re.compile(r"(?ms)^## Open GitHub Issues.*?(?=^## |\Z)"),
    "es": re.compile(r"(?ms)^## Incidencias abiertas de GitHub.*?(?=^## |\Z)"),
    "fr": re.compile(r"(?ms)^## Tickets GitHub ouverts.*?(?=^## |\Z)"),
    "uk": re.compile(r"(?ms)^## Відкриті задачі GitHub.*?(?=^## |\Z)"),
    "zh": re.compile(r"(?ms)^## GitHub 未结议题.*?(?=^## |\Z)"),
}


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version = "([^"]+)"$', text)
    assert match is not None
    return match.group(1)


def _active_freeze_doc() -> vrf.FreezeDoc:
    path = ROOT / vrf.FREEZE_DOC_TEMPLATE.format(version=_pyproject_version())
    assert path.is_file(), f"Aktives Freeze-Dokument fehlt: {path}"
    return vrf.parse_freeze_doc(path.read_text(encoding="utf-8"))


def _extract(pattern_map: dict[str, re.Pattern[str]], docs: dict[str, Path]) -> dict[str, str]:
    """Wendet je Sprache den passenden Anker auf die zugehörige Datei an."""
    values: dict[str, str] = {}
    for lang, path in docs.items():
        text = path.read_text(encoding="utf-8")
        match = pattern_map[lang].search(text)
        assert match is not None, f"{lang}: Anker nicht gefunden in {path}"
        values[lang] = match.group(1)
    return values


def test_active_freeze_document_is_resolvable_from_pyproject() -> None:
    """#752: Der aktive Kandidatenstand beginnt beim über pyproject.toml gefundenen Dokument."""
    doc = _active_freeze_doc()
    assert doc.version == _pyproject_version()


def test_recommendations_kurzstatus_date_matches_across_languages() -> None:
    dates = _extract(_STATUS_HEADER_RE, RECOMMENDATION_DOCS)
    assert len(set(dates.values())) == 1, f"Kurzstatus-Datum weicht zwischen Sprachen ab: {dates}"


def test_recommendations_live_issue_count_matches_across_languages() -> None:
    counts = _extract(_LIVE_COUNT_RE, RECOMMENDATION_DOCS)
    assert len(set(counts.values())) == 1, f"Live-Stand-Anzahl weicht zwischen Sprachen ab: {counts}"


def _triage_issue_numbers(docs: dict[str, Path]) -> dict[str, tuple[int, ...]]:
    """Die Menge der Spalte-1-Issue-Nummern je Sprache (nicht nur ihre Größe).

    Ein reiner Zahlenvergleich (siehe oben) übersieht, dass eine Übersetzung
    ein geschlossenes Issue behält und ein neu offenes weglässt, solange die
    Gesamtzahl zufällig gleich bleibt - deshalb vergleicht dieser Test die
    tatsächlichen Nummern-Mengen (#752, Codex-Review auf PR #783).
    """
    numbers: dict[str, tuple[int, ...]] = {}
    for lang, path in docs.items():
        text = path.read_text(encoding="utf-8")
        match = _TRIAGE_SECTION_RE[lang].search(text)
        assert match is not None, f"{lang}: Triage-Abschnitt nicht gefunden in {path}"
        numbers[lang] = lc.issue_numbers_in_first_column(match.group(0))
    return numbers


def test_recommendations_triage_issue_sets_match_across_languages() -> None:
    issue_sets = _triage_issue_numbers(RECOMMENDATION_DOCS)
    reference = issue_sets["de"]
    mismatched = {lang: nums for lang, nums in issue_sets.items() if nums != reference}
    assert not mismatched, f"Triage-Issue-Mengen weichen von der deutschen Fassung ab: {mismatched}"


def _write_synthetic_docs(tmp_path: Path, *, stale_lang: str, stale_date: str) -> dict[str, Path]:
    """Sechs Sprachdateien, die die echten Kurzstatus-Header/Live-Stand-Zeilen
    nachbilden - bis auf *stale_lang*, die ein veraltetes Datum behält.

    Baut damit das reale Symptom von #669/#728 nach: eine einzelne
    Sprachfassung bleibt nach einer Aktualisierung stehen.
    """
    headers = {
        "de": "## Aktueller Stand ({date}, Test)",
        "en": "## Current Status ({date}, Test)",
        "es": "## Estado actual ({date}, Test)",
        "fr": "## État actuel ({date}, Test)",
        "uk": "## Поточний стан ({date}, Test)",
        "zh": "## 当前状态（{date}，Test）",
    }
    live_lines = {
        "de": "Live-Stand nach GitHub-Abfrage: **23** offene Issues.",
        "en": "Live state after the GitHub query: **23** open issues.",
        "es": "Estado en vivo tras la consulta a GitHub: **23** incidencias abiertas.",
        "fr": "État en direct après la requête GitHub : **23** tickets ouverts.",
        "uk": "Live-стан після запиту до GitHub: **23** відкритих задачі.",
        "zh": "GitHub 查询后的实时状态：**23** 个未结议题。",
    }
    docs: dict[str, Path] = {}
    for lang in headers:
        date = stale_date if lang == stale_lang else "2026-08-13"
        path = tmp_path / f"RECOMMENDATIONS.{lang}.md"
        path.write_text(f"{headers[lang].format(date=date)}\n\n{live_lines[lang]}\n", encoding="utf-8")
        docs[lang] = path
    return docs


def test_date_drift_between_languages_is_detected(tmp_path: Path) -> None:
    """Regressionsfixtur für das #669/#728-Drift-Muster: eine Sprache bleibt stehen.

    Nutzt dieselbe Extraktionslogik wie der echte Paritätstest oben, aber
    gegen synthetische Dateien, in denen genau eine Sprachfassung ihr
    Stichtagsdatum nicht mitgezogen hat - reproduziert damit mechanisch,
    dass ein solcher Drift den Test scheitern lässt statt still durchzugehen.
    """
    docs = _write_synthetic_docs(tmp_path, stale_lang="es", stale_date="2026-08-06")
    dates = _extract(_STATUS_HEADER_RE, docs)
    assert dates["es"] != dates["de"]
    assert len(set(dates.values())) != 1


def _issue_link(number: int) -> str:
    return f"[#{number}](https://github.com/{lc._DEFAULT_REPO}/issues/{number})"


def _write_synthetic_triage_docs(
    tmp_path: Path, *, stale_lang: str, stale_rows: str, normal_rows: str
) -> dict[str, Path]:
    """Sechs Sprachdateien mit Triage-Tabellen - *stale_lang* mit abweichenden
    Zeilen (*stale_rows* statt *normal_rows*), aber derselben Zeilenzahl,
    damit ein reiner Zahlenvergleich den Drift nicht sähe.
    """
    headers = {
        "de": "## Offene GitHub-Issues – Triage-Stand (2026-08-01)",
        "en": "## Open GitHub Issues — Triage Status (2026-08-01)",
        "es": "## Incidencias abiertas de GitHub — Clasificación (2026-08-01)",
        "fr": "## Tickets GitHub ouverts — Triage (2026-08-01)",
        "uk": "## Відкриті задачі GitHub — Стан тріажу (2026-08-01)",
        "zh": "## GitHub 未结议题 — 分诊状态（2026-08-01）",
    }
    docs: dict[str, Path] = {}
    for lang, header in headers.items():
        rows = stale_rows if lang == stale_lang else normal_rows
        path = tmp_path / f"RECOMMENDATIONS.{lang}.md"
        path.write_text(
            f"{header}\n\n| # | Titel |\n|---|---|\n{rows}\n## Vorige Runden\n", encoding="utf-8"
        )
        docs[lang] = path
    return docs


def test_triage_issue_set_drift_with_equal_row_count_is_detected(tmp_path: Path) -> None:
    """Regressionsfixtur für den Codex-Review-Befund auf PR #783.

    Eine Übersetzung kann ein bereits geschlossenes Issue behalten und ein
    neu offenes weglassen, sodass die Zeilenzahl (und damit ein reiner
    Zahlenvergleich) zufällig gleich bleibt. Diese Fixtur baut genau das
    nach: zwei Zeilen in jeder Sprache, aber die veraltete Fassung führt
    #740 statt des tatsächlich neuen #758.
    """
    normal_rows = f"| {_issue_link(741)} | Epic |\n| {_issue_link(758)} | Neu |\n"
    stale_rows = f"| {_issue_link(741)} | Epic |\n| {_issue_link(740)} | Veraltet |\n"
    docs = _write_synthetic_triage_docs(
        tmp_path, stale_lang="es", stale_rows=stale_rows, normal_rows=normal_rows
    )
    issue_sets = _triage_issue_numbers(docs)
    assert len({len(numbers) for numbers in issue_sets.values()}) == 1
    assert issue_sets["es"] != issue_sets["de"]


def test_declared_count_drift_after_merged_fix_is_detected(tmp_path: Path) -> None:
    """Regressionsfixtur für das #740/#750-Drift-Muster aus #752.

    #750 hat #740 geschlossen; die Recommendations-Datei behauptete den
    alten offenen Stand trotzdem unverändert weiter. Baut das mit derselben
    Extraktionslogik nach, die der echte Paritätstest gegen die realen
    Dateien anwendet: eine Datei, die nach dem Fix nicht aktualisiert wurde,
    weicht vom tatsächlich niedrigeren Live-Stand ab - die GitHub-Gegenprobe
    selbst übernimmt der separate Live-Check
    (``scripts/recommendations_live_check.py``).
    """
    stale = tmp_path / "RECOMMENDATIONS.md"
    stale.write_text(
        "## Aktueller Stand (2026-08-01, vor #750)\n\n"
        "Live-Stand nach GitHub-Abfrage: **30** offene Issues.\n",
        encoding="utf-8",
    )
    declared = _LIVE_COUNT_RE["de"].search(stale.read_text(encoding="utf-8"))
    assert declared is not None
    actual_after_fix = 29  # #740 tatsächlich geschlossen (#750 gemergt)
    assert int(declared.group(1)) != actual_after_fix
