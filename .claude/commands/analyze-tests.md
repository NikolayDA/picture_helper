---
description: Test- & Coverage-Analyse der gesamten Codebase
argument-hint: "[optionales Modul, z. B. crop oder canvas_history]"
allowed-tools: Read, Grep, Glob, Bash(make:*), Bash(python -m coverage:*), Bash(python -m pytest:*)
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
Skizze des Testfalls. Schlage Einträge im `RECOMMENDATIONS.md`-Format (IDs `N#`/`O#`)
vor; die Datei nur nach Bestätigung ändern.

Optionales Modul: $ARGUMENTS
