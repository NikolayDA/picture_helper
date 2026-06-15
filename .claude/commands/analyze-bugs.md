---
description: Korrektheits- & Bug-Analyse der gesamten Codebase
argument-hint: "[optionaler Fokus, z. B. workers oder canvas]"
allowed-tools: Read, Grep, Glob, Bash(make:*), Bash(python -m pytest:*), Agent
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

Optionaler Fokus: $ARGUMENTS
