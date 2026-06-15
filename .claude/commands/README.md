# Code-Analyse-Routinen

Vier wiederholbare, einzeln aufrufbare Slash-Commands für die Analyse der
**gesamten** Codebase von BgRemover. Jede Routine ist eine Datei in diesem
Verzeichnis (`.claude/commands/`) und steht in Claude Code als `/<name>` zur
Verfügung.

## Überblick

| Befehl | Fokus | Baseline-Check | Datei |
|---|---|---|---|
| `/analyze-bugs` | Korrektheit & Bugs (Logik, Race Conditions, Edge Cases) | `make check` | [analyze-bugs.md](analyze-bugs.md) |
| `/analyze-arch` | Architektur & Struktur (Coupling, Verantwortlichkeiten) | – | [analyze-arch.md](analyze-arch.md) |
| `/analyze-security` | Sicherheit (Input, Subprozess, Pfade, Settings) | – | [analyze-security.md](analyze-security.md) |
| `/analyze-tests` | Tests & Coverage (Lücken, Edge-Case-Tests) | `make coverage` | [analyze-tests.md](analyze-tests.md) |

## Aufruf

- **Einzeln, on-demand:** den gewünschten Befehl tippen, z. B. `/analyze-bugs`.
- **Mit Fokus-Argument:** ein Modul/Bereich einschränken, z. B.
  `/analyze-security ai_process` oder `/analyze-tests crop`.
- **Alle vier nacheinander:** die Befehle hintereinander aufrufen oder einfach
  „lass alle vier Analyse-Routinen laufen" sagen.

## Befunde & RECOMMENDATIONS.md

Jede Routine liefert strukturierte Befunde (Schweregrad, `Datei:Zeile`,
Begründung, Vorschlag) und schlägt Einträge im Format von
[`RECOMMENDATIONS.md`](../../RECOMMENDATIONS.md) vor (IDs `N#`/`O#`, siehe
Konvention in [`CLAUDE.md`](../../CLAUDE.md)). Die Datei wird **nur nach
ausdrücklicher Bestätigung** geändert.

## GitHub-Issues (optional)

Bei Bedarf können die Routinen Issues im Repo `NikolayDA/picture_helper` anlegen
oder kommentieren:

- Auslösen über das Argument `issues` (z. B. `/analyze-bugs issues`) oder auf
  ausdrückliche Bitte.
- Vorher wird nach bestehenden Issues gesucht, um Duplikate zu vermeiden;
  passende Befunde werden lieber als Kommentar ergänzt.
- Verwandte Befunde werden gebündelt; der Issue-Body referenziert die
  zugehörige `RECOMMENDATIONS.md`-ID.
- Vor jedem Schreibvorgang auf GitHub wird kurz rückgefragt.

## Wiederkehrende Ausführung

- **Geplant/Intervall:** per `/loop` koppeln, z. B. `/loop 1d /analyze-security`.
- **An Events:** als Hook in `.claude/settings.json` einhängen.

## Sicherheit & Berechtigungen

Die `allowed-tools`-Frontmatter jeder Routine beschränkt sie auf das Nötige:
Lese-/Suchtools, die passenden `make`-Aufrufe und die GitHub-Issue-Tools. Es
werden keine Quelldateien verändert; Schreibvorgänge (RECOMMENDATIONS.md,
GitHub-Issues) erfordern Bestätigung.

## Pflege

Diese Dateien liegen außerhalb der i18n-/CHANGELOG-Governance (kein Eintrag in
`docs/i18n/` nötig). Beim Hinzufügen lokaler Markdown-Links beachten, dass
`tests/test_markdown_links.py` alle `*.md` repo-weit prüft — Links müssen
auflösen.
