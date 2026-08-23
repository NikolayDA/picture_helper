"""Static checks for the recommendation/roadmap documentation."""

from pathlib import Path

from scripts import recommendations_live_check as lc

ROOT = Path(__file__).resolve().parent.parent
#: Pfade und Sprachanker kommen aus ``recommendations_live_check`` — CLAUDE.md
#: nennt sie als einzige Quelle, und ``test_recommendations_freeze_consistency``
#: leitet sie ebenso ab. Eine zweite, handgepflegte Liste hier hätte eine
#: siebte Sprachfassung still übergangen, obwohl ``--write`` deren Tabelle
#: mitschreibt — genau die Drift, gegen die diese Tests antreten.
RECOMMENDATION_DOCS = {
    lang: ROOT / relative for lang, relative in lc.RECOMMENDATION_DOCS.items()
}
ARCHIVE_DOCS = {
    "de": ROOT / "docs/history/RECOMMENDATIONS-2026-pre-v2.2.md",
    "en": ROOT / "docs/history/RECOMMENDATIONS-2026-pre-v2.2.en.md",
    "es": ROOT / "docs/history/RECOMMENDATIONS-2026-pre-v2.2.es.md",
    "fr": ROOT / "docs/history/RECOMMENDATIONS-2026-pre-v2.2.fr.md",
    "uk": ROOT / "docs/history/RECOMMENDATIONS-2026-pre-v2.2.uk.md",
    "zh": ROOT / "docs/history/RECOMMENDATIONS-2026-pre-v2.2.zh.md",
}
ARCHIVE_LINKS = {
    "de": "docs/history/RECOMMENDATIONS-2026-pre-v2.2.md",
    "en": "../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md",
    "es": "../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md",
    "fr": "../../history/RECOMMENDATIONS-2026-pre-v2.2.fr.md",
    "uk": "../../history/RECOMMENDATIONS-2026-pre-v2.2.uk.md",
    "zh": "../../history/RECOMMENDATIONS-2026-pre-v2.2.zh.md",
}
LANGUAGE_MARKERS = {
    "de": (
        "[English](",
        "[Español](",
        "[Français](",
        "[Українська](",
        "[简体中文](",
    ),
    "en": (
        "[Deutsch](",
        "[Español](",
        "[Français](",
        "[Українська](",
        "[简体中文](",
    ),
    "es": (
        "[Deutsch](",
        "[English](",
        "[Français](",
        "[Українська](",
        "[简体中文](",
    ),
    "fr": (
        "[Deutsch](",
        "[English](",
        "[Español](",
        "[Українська](",
        "[简体中文](",
    ),
    "uk": (
        "[Deutsch](",
        "[English](",
        "[Español](",
        "[Français](",
        "[简体中文](",
    ),
    "zh": (
        "[Deutsch](",
        "[English](",
        "[Español](",
        "[Français](",
        "[Українська](",
    ),
}
RATING_SYMBOLS = ("🔴", "🟠", "🟡", "🟢")
# Pflicht-Tokens des aktuellen Kurzstatus. Sprachneutral gewählt, damit sie
# unverändert in allen sechs Sprachdateien vorkommen.
CURRENT_STATUS_TOKENS = (
    "2026-06-25",
    "N1/N2/N4/N5/N6/N7/N8",
    "O1",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


#: Die Zellentrennung kommt aus dem Skript (``lc.cells``) — dort erzeugt
#: ``render_triage_row`` die Maskierung, dort gehört auch ihr Gegenstück hin.
#: Eine zweite, test-lokale Fassung wäre genau die Drift, gegen die dieser
#: Wächter antritt. Die Negativkontrolle des Splitters liegt neben ihm in
#: ``tests/test_recommendations_live_check.py``.


def test_triage_rows_have_exactly_the_header_column_count() -> None:
    """Ein unmaskiertes Pipe in einer Zelle verschluckt den Rest der Zeile.

    Auf PR #851 real passiert: Die Zelle „Nächster Schritt" der neuen
    #841-Zeile zitierte ein `grep -cE '(^|[[:space:]])…'`. Backticks schützen
    in GFM **nicht** vor der Zellentrennung — die Zeile bekam eine siebte
    Zelle bei sechs Kopfspalten, GFM verwirft die überzähligen, und alles ab
    dem Pipe war in der gerenderten Ansicht unsichtbar. Betroffen waren alle
    sechs Fassungen; gerade die Passage, die den Verifikationsmodus
    definiert, fiel weg.

    Kein bestehender Test fing das: ``recommendations_live_check`` wertet von
    einer Datenzeile nur ``cells(row)[0]`` aus, der Konsistenztest nur die
    Nummernmenge — ``make check`` blieb grün, der Schaden war rein visuell.
    Das Skript maskiert beim Fortschreiben längst selbst
    (``render_triage_row``); nur die handgepflegten Bewertungsspalten fallen
    nicht unter diese Automatik.

    Geprüft wird nur der Triage-Abschnitt, nicht jede Tabellenzeile der
    Datei. Das ist keine prinzipielle Grenze, sondern eine Folge der
    Vergleichsbasis: Alle Zeilen werden gegen **den** Triage-Kopf gehalten,
    eine Tabelle mit anderer Spaltenzahl — etwa unter „Vorige Runden" —
    würde deshalb falsch-rot. Vergliche man jede Tabelle gegen ihren
    **eigenen** Kopf, ließe sich der Wächter auf die Archivtabellen
    ausweiten, die denselben Renderschaden erleiden können und heute
    niemand prüft. ``table_span`` liefert dafür nicht genug (es findet
    genau die erste zusammenhängende Tabelle); das wäre ein eigener Beitrag.
    """
    for lang, path in RECOMMENDATION_DOCS.items():
        lines = lc.extract_triage_section(_read(path), lang).split("\n")
        first, last = lc.table_span(lines)
        columns = len(lc.cells(lines[first]))
        for row in lines[first + 2 : last + 1]:
            actual = len(lc.cells(row))
            assert actual == columns, (
                f"{lang}: {actual} Zellen statt {columns} — ein unmaskiertes `|` in "
                f"einer Zelle; GFM verwirft alles danach. Als `\\|` schreiben. "
                f"Zeile: {row[:80]}…"
            )


def test_recommendations_docs_have_current_shortform_structure() -> None:
    for lang, path in RECOMMENDATION_DOCS.items():
        assert path.exists()
        text = _read(path)
        assert text.strip()
        assert len(text.splitlines()) <= 120
        first_line = text.splitlines()[0]

        assert all(marker in first_line for marker in LANGUAGE_MARKERS[lang])
        assert ARCHIVE_LINKS[lang] in text
        assert all(symbol in text for symbol in RATING_SYMBOLS)
        assert all(token in text for token in CURRENT_STATUS_TOKENS)


def test_recommendations_archives_exist_and_are_linked() -> None:
    for lang, path in ARCHIVE_DOCS.items():
        assert path.exists()
        text = _read(path)
        assert text.strip()
        assert "2026-05-24" in text
        assert "1cf8461" in text
        assert ARCHIVE_LINKS[lang] in _read(RECOMMENDATION_DOCS[lang])
