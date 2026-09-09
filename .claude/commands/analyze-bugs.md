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
Fix-Vorschlag. Jeder Befund ist direkt als Issue verwendbar: Titel, Schweregrad, `Datei:Zeile`,
Reproduktion/Beleg, Vorschlag und Akzeptanzkriterium. Kein Empfehlungs- oder
Tabellenformat, keine Katalog-IDs; ohne Befund die Aussage „kein Befund".

GitHub-Issues (nur nach ausdrücklicher Bestätigung):
- Mit dem Argument `issues` (oder auf ausdrückliche Bitte) darf die Routine im
  Repo `NikolayDA/picture_helper` Issues anlegen bzw. kommentieren – vor jedem
  Schreibvorgang kurz bestätigen lassen.
- Duplikatsuche ist Pflicht und umfasst offene **und** geschlossene Issues
  (`search_issues`/`list_issues`); ein bestehendes Issue wird nur bei
  materiell neuer Evidenz oder geändertem Befund kommentiert
  (`add_issue_comment`), sonst nichts. Ein Lauf ohne Befund und ein
  identischer Wiederholungslauf erzeugen null Schreibvorgänge.
- Verwandte Befunde bündeln statt pro Kleinigkeit ein Issue; Priorität als
  `prio:now`/`prio:next`/`prio:later` vorschlagen (Regeln in
  `CONTRIBUTING.md`, Abschnitt „Issue-Triage").

Optionaler Fokus: $ARGUMENTS
