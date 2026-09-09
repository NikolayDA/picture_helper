---
description: Test- & Coverage-Analyse der gesamten Codebase
argument-hint: "[optionales Modul, z. B. crop oder canvas_history]"
allowed-tools: Read, Grep, Glob, Bash(make:*), Bash(python -m coverage:*), Bash(python -m pytest:*), mcp__github__search_issues, mcp__github__list_issues, mcp__github__issue_read, mcp__github__issue_write, mcp__github__add_issue_comment
---
Führe eine **Test- und Coverage-Analyse der gesamten Codebase** durch
(`bgremover/`, `tests/`).

Vorgehen:
1. Baseline: `make coverage` ausführen (`fail_under = 86`) und Report auswerten.
2. Abdeckungslücken identifizieren: ungetestete Module/Pfade, fehlende
   Edge-Case-Tests, schwach getestete Logikmodule (z. B. `image_ops`,
   `image_utils`, `crop`, `canvas_*`).
3. Test-Balance bewerten: UI (`ui`/`ui_smoke`) vs. Logik, Governance-Tests
   (Markdown-Links, i18n-Parität, CHANGELOG, Lizenzen, Qt-apt-Drift N6).

Ausgabe: priorisierte Liste fehlender/sinnvoller Tests mit Modul, Begründung und
Skizze des Testfalls. Jeder Befund ist direkt als Issue verwendbar: Titel, Schweregrad, `Datei:Zeile`,
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

Optionales Modul: $ARGUMENTS
