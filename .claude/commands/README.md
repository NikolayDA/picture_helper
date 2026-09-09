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

## Befunde als Issues

Jede Routine liefert strukturierte Befunde, die direkt als GitHub-Issue
verwendbar sind: Titel, Schweregrad, `Datei:Zeile`, Reproduktion/Beleg,
Vorschlag und Akzeptanzkriterium. Ein Lauf ohne Befund meldet „kein Befund"
und erzeugt nichts. Es gibt kein Empfehlungs- oder Tabellenformat und keine
Katalog-IDs mehr (#1040/#1042); Priorität und Blocker stehen im Issue selbst
(Labels `prio:*`, native Abhängigkeiten, `blocked:extern` – Regeln in
[`CONTRIBUTING.md`](../../CONTRIBUTING.md), Abschnitt „Issue-Triage").

## GitHub-Issues (optional)

Bei Bedarf können die Routinen Issues im Repo `NikolayDA/picture_helper` anlegen
oder kommentieren:

- Auslösen über das Argument `issues` (z. B. `/analyze-bugs issues`) oder auf
  ausdrückliche Bitte.
- Duplikatsuche ist Pflicht und umfasst offene **und** geschlossene Issues;
  ein bestehendes Issue wird nur bei materiell neuer Evidenz oder geändertem
  Befund kommentiert. Ein identischer Wiederholungslauf erzeugt null
  Schreibvorgänge (Idempotenz).
- Verwandte Befunde werden gebündelt; der Issue-Body trägt Reproduktion,
  Vorschlag und Akzeptanzkriterium, die Priorität wird als `prio:*`-Label
  vorgeschlagen.
- Vor jedem Schreibvorgang auf GitHub wird kurz rückgefragt.
- **Sicherheitsausnahme:** Ein plausibler, noch nicht veröffentlichter
  Schwachstellen-Befund aus `/analyze-security` nimmt nie den öffentlichen
  Pfad, sondern wird als vertraulicher Bericht für GitHub Private
  Vulnerability Reporting ausgegeben (Format aus
  [`SECURITY.md`](../../SECURITY.md)).

## Wiederkehrende Ausführung

- **Geplant/Intervall:** per `/loop` koppeln, z. B. `/loop 1d /analyze-security`.
- **An Events:** als Hook in `.claude/settings.json` einhängen.

## Sicherheit & Berechtigungen

Die `allowed-tools`-Frontmatter jeder Routine beschränkt sie auf das Nötige:
Lese-/Suchtools, die passenden `make`-Aufrufe und die GitHub-Issue-Tools. Es
werden keine Quelldateien verändert; die einzigen Schreibvorgänge sind
GitHub-Issues und -Kommentare, sie erfordern Bestätigung, sind idempotent und
schließen vertrauliche Sicherheitsbefunde aus.

## Pflege

Diese Dateien liegen außerhalb der i18n-/CHANGELOG-Governance (kein Eintrag in
`docs/i18n/` nötig). Beim Hinzufügen lokaler Markdown-Links beachten, dass
`tests/test_markdown_links.py` alle `*.md` repo-weit prüft — Links müssen
auflösen.
