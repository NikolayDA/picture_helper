---
description: Sicherheits-Analyse der gesamten Codebase
argument-hint: "[optionaler Fokus, z. B. image_loading oder ai_process]"
allowed-tools: Read, Grep, Glob, Bash(make:*), Agent
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

Optionaler Fokus: $ARGUMENTS
