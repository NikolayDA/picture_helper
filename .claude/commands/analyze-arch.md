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
konkretem Verbesserungsvorschlag. Schlage Einträge im `RECOMMENDATIONS.md`-Format
(IDs `N#`/`O#`) vor; die Datei nur nach Bestätigung ändern.

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
