---
description: Korrektheits- & Bug-Analyse der gesamten Codebase
argument-hint: "[optionaler Fokus, z. B. workers oder canvas]"
allowed-tools: Read, Grep, Glob, Bash(make:*), Bash(python -m pytest:*), Agent, mcp__github__search_issues, mcp__github__list_issues, mcp__github__issue_read, mcp__github__issue_write, mcp__github__add_issue_comment
---
Führe eine systematische **Korrektheits-Analyse der gesamten Codebase** durch
(`bgremover/`, `scripts/`, `tests/`) — nicht nur des Diffs.

Vorgehen:
1. Baseline: `make check` ausführen und Fehler auswerten.
2. Architektur-Bereiche aus CLAUDE.md durchgehen (Canvas/Bearbeitung,
   Worker/AI-Prozess, UI-Bausteine, Infrastruktur, i18n). Für Breite parallele
   Explore-Agenten nutzen.
3. Achte besonders auf: Logikfehler, Race Conditions (AI-Prozess/Worker, `spawn`,
   harter Abbruch #270), Edge Cases bei Bild-/Datei-Verarbeitung,
   Fehlerbehandlung, Ressourcen-/Prozess-Lecks.

Ausgabe: Befunde mit Schweregrad, `Datei:Zeile`, kurzer Begründung und
Fix-Vorschlag. Schlage neue Einträge im `RECOMMENDATIONS.md`-Format (IDs `N#`/`O#`)
vor; die Datei nur nach ausdrücklicher Bestätigung ändern.

GitHub-Issues (optional, „bei Bedarf"):
- Mit dem Argument `issues` (oder auf ausdrückliche Bitte) darf die Routine im
  Repo `NikolayDA/picture_helper` Issues anlegen bzw. kommentieren.
- Zuerst per `search_issues`/`list_issues` nach bestehenden Issues suchen und
  Duplikate vermeiden; passende Befunde lieber als Kommentar ergänzen
  (`add_issue_comment`) als ein neues Issue zu öffnen.
- Verwandte Befunde bündeln statt pro Kleinigkeit ein Issue. Im Issue-Body die
  zugehörige `RECOMMENDATIONS.md`-ID (`N#`/`O#`) referenzieren.
- Vor jedem Schreibvorgang auf GitHub kurz bestätigen lassen.

Optionaler Fokus: $ARGUMENTS
