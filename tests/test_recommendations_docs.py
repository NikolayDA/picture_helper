"""Static checks for the recommendation/roadmap documentation."""

from pathlib import Path

from scripts import recommendations_live_check as lc

ROOT = Path(__file__).resolve().parent.parent
RECOMMENDATION_DOCS = lc.recommendation_doc_paths(ROOT)
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

    Die Zellentrennung kommt aus dem Skript (``lc.cells``) — dort erzeugt
    ``render_triage_row`` die Maskierung, dort gehört auch ihr Gegenstück
    hin. Eine zweite, test-lokale Fassung wäre genau die Drift, gegen die
    dieser Wächter antritt; die Negativkontrolle des Splitters liegt neben
    ihm in ``tests/test_recommendations_live_check.py``.

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
        # Ab first + 1, also inklusive Trennzeile: Stimmt deren Spaltenzahl
        # nicht mit dem Kopf ueberein, erkennt GFM den Block gar nicht erst
        # als Tabelle und zeigt rohes "| … |" - derselbe Schaden, nur groesser.
        for offset, row in enumerate(lines[first + 1 : last + 1]):
            actual = len(lc.cells(row))
            if actual == columns:
                continue
            # Beide Richtungen sind ein Fehler, aber nicht derselbe: zu viele
            # Zellen heißt „unmaskiertes Pipe, GFM verwirft den Rest", zu wenige
            # heißt „Spalte fehlt". Für die Trennzeile gilt in *beiden*
            # Richtungen die härtere Folge — GFM erkennt den Block dann gar
            # nicht als Tabelle —, deshalb ERSETZT ihre Meldung die
            # Richtungsdiagnose, statt neben einer irreführenden zu stehen
            # (#852-Review). Erkannt wird sie über die Position statt über
            # `row is lines[first + 1]` — die Absicht „erste Zeile nach dem
            # Kopf" steht damit direkt im Code statt in geteilter
            # Slice-Referenzidentität.
            if offset == 0:
                reason = (
                    "die Trennzeile passt nicht zum Kopf; GFM erkennt den "
                    "Block dann gar nicht als Tabelle."
                )
            elif actual > columns:
                reason = (
                    "ein unmaskiertes `|` in einer Zelle; GFM verwirft alles "
                    "danach. Als `\\|` schreiben."
                )
            else:
                reason = "eine Spalte fehlt; GFM füllt sie still leer auf."
            excerpt = row[:80] + ("…" if len(row) > 80 else "")
            raise AssertionError(
                f"{lang}: {actual} Zellen statt {columns} — {reason} Zeile: {excerpt}"
            )


#: Obergrenze der Kurzform *ohne* die Datenzeilen der Triage-Tabelle. Die
#: Schranke bewacht die Prosa - dass der Kurzstatus kurz bleibt und
#: Ausfuehrliches ins Archiv unter docs/history/ wandert.
#:
#: Bis zum 2026-09-09 zaehlte sie die Gesamtzeilen und damit auch die Tabelle,
#: die aber mit dem *offenen Bestand* waechst, nicht mit der Laenge des Textes:
#: Fuenfzehn neue Issues rissen die Schranke, ohne dass jemand ein Wort
#: geschrieben haette, und die einzige Abhilfe waere gewesen, Statustext zu
#: opfern - den kein Leser weniger braucht, nur weil mehr Issues offen sind.
#:
#: Die *Absicht* bleibt, die Zahl ist bewusst neu kalibriert: Aus "120 gesamt"
#: folgte je nach Bestand ein wanderndes Prosa-Budget (bei den 41 Zeilen des
#: Vorstands 79, bei 56 nur noch 64). 120 auf die Prosa anzuwenden haette das
#: Budget still auf das Anderthalbfache gehoben und die Schranke auf absehbare
#: Zeit wirkungslos gemacht. 90 liegt knapp ueber dem Ist-Stand (laengste
#: Fassung 83 Zeilen) und damit ungefaehr dort, wo die alte Regel real lag.
#: Wer sie reisst, archiviert eine Runde - er hebt nicht die Zahl.
_MAX_SHORTFORM_PROSE_LINES = 90


def _prose_line_count(text: str, lang: str) -> int:
    """Zeilen der Kurzform ohne die Datenzeilen der Triage-Tabelle.

    Die Datenzeilen kommen ueber :func:`lc.table_span` - dieselbe Quelle wie
    im ``--write``-Pfad und im Nachbartest oben. Eine eigene Heuristik (etwa
    ``line.startswith("| [#")``) zaehlt jede Zeile als Prosa, deren erste
    Spalte nicht mit einem Issue-Link beginnt (gruppierte Zeilen, ein
    vorangestelltes Symbol, ein Sonderfall von Hand) - die Schranke risse dann
    wieder wegen des offenen Bestands, nur seltener und schwerer zu deuten.
    """
    lines = lc.extract_triage_section(text, lang).split("\n")
    first, last = lc.table_span(lines)
    # Ab first + 2: Kopf- und Trennzeile sind Struktur, keine Datenzeilen.
    return len(text.splitlines()) - max(last - first - 1, 0)


def test_recommendations_docs_have_current_shortform_structure() -> None:
    for lang, path in RECOMMENDATION_DOCS.items():
        assert path.exists()
        text = _read(path)
        assert text.strip()
        prose = _prose_line_count(text, lang)
        assert prose <= _MAX_SHORTFORM_PROSE_LINES, (
            f"{lang}: {prose} Prosazeilen (max. {_MAX_SHORTFORM_PROSE_LINES}) - "
            "aeltere Runden gehoeren ins Archiv unter docs/history/."
        )
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
