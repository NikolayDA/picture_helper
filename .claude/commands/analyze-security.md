---
description: Sicherheits-Analyse der gesamten Codebase
argument-hint: "[optionaler Fokus, z. B. image_loading oder ai_process]"
allowed-tools: Read, Grep, Glob, Bash(make:*), Agent, mcp__github__search_issues, mcp__github__list_issues, mcp__github__issue_read, mcp__github__issue_write, mcp__github__add_issue_comment
---
Führe eine **Sicherheits-Analyse der gesamten Codebase** durch
(`bgremover/`, `scripts/`) — breiter als `/security-review`, das nur den Branch-Diff
betrachtet.

Vorgehen:
1. Eintritts-/Vertrauensgrenzen kartieren: Bild-/Datei-Input (`image_loading.py`,
   `image_ops`, `image_utils`), Subprozess/`spawn` (`ai_process.py`, `workers.py`),
   Dateipfade & „Zuletzt geöffnet" (`recent_files.py`), QSettings
   (`settings_schema.py`), optionale Abhängigkeiten (`rembg`/ONNX).
2. Prüfen auf: unsichere Pfad-/Dateibehandlung, fehlende Input-Validierung,
   unkontrollierte Ressourcen, unsichere Deserialisierung, Injection in
   Subprozess-Aufrufe, riskante Defaults.

Ausgabe: Befunde mit Schweregrad, `Datei:Zeile`, Angriffsszenario und
Gegenmaßnahme. Schlage Einträge im `RECOMMENDATIONS.md`-Format (IDs `N#`/`O#`) vor;
die Datei nur nach Bestätigung ändern.

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
