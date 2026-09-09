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
Gegenmaßnahme. Jeder Befund ist direkt als Issue verwendbar: Titel, Schweregrad, `Datei:Zeile`,
Reproduktion/Beleg, Vorschlag und Akzeptanzkriterium. Kein Empfehlungs- oder
Tabellenformat, keine Katalog-IDs; ohne Befund die Aussage „kein Befund".

**Sicherheitsausnahme (verbindlich, siehe `SECURITY.md`):** Ein plausibler,
noch nicht veröffentlichter Schwachstellen-Befund wird **nie** per
`issue_write` oder `add_issue_comment` öffentlich geschrieben. Er wird nur als
vertraulicher Bericht für GitHub Private Vulnerability Reporting ausgegeben
(betroffene Version, Reproduktion, Auswirkung, Fix-Vorschlag – das Format aus
`SECURITY.md`). Nur Befunde, die ausdrücklich als nicht vertraulich
eingestuft sind (Hardening, Doku), nehmen den Issue-Pfad.

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
