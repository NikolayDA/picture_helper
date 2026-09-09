---
description: Architektur- & Struktur-Analyse der gesamten Codebase
argument-hint: "[optionaler Fokus, z. B. canvas_* oder right_panel]"
allowed-tools: Read, Grep, Glob, Bash(make:*), Agent, mcp__github__search_issues, mcp__github__list_issues, mcp__github__issue_read, mcp__github__issue_write, mcp__github__add_issue_comment
---
Führe eine **Architektur- und Struktur-Analyse der gesamten Codebase** durch
(`bgremover/`, `scripts/`).

Vorgehen:
1. Modul-Zuschnitt entlang der CLAUDE.md-Gliederung prüfen (Canvas/Bearbeitung,
   Worker/AI-Prozess, UI-Bausteine, Infrastruktur, i18n).
2. Bewerten: Coupling/Cohesion, Verantwortlichkeiten, zyklische/überraschende
   Importe, Duplizierung, zu große Module, Konsistenz der Konventionen.
3. Vereinfachungs- und Refactoring-Potenzial benennen — ohne über das Ziel
   hinauszuschießen (Altitude beachten).

Ausgabe: Befunde mit `Datei:Zeile`, betroffener Schnittstelle, Begründung und
konkretem Verbesserungsvorschlag. Jeder Befund ist direkt als Issue verwendbar: Titel, Schweregrad, `Datei:Zeile`,
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
