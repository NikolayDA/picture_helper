---
description: Architektur- & Struktur-Analyse der gesamten Codebase
argument-hint: "[optionaler Fokus, z. B. canvas_* oder right_panel]"
allowed-tools: Read, Grep, Glob, Bash(make:*), Agent
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

Optionaler Fokus: $ARGUMENTS
