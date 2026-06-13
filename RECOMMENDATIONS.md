**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-06-04)

Die laufende Codeanalyse-Liste ist leer. Ruff, mypy und die lokale Testsuite
bleiben die maßgebliche Baseline vor neuen PRs.

### Erledigt seit dem letzten Review

- **N1/N2/N4/N5/N6/N7/N8** sind erledigt: Fehlerpfade, Größenlimit,
  Dateiendungen, atomisches Speichern, CI-Qt-Pakete, Lazy-Import und Docstring.
- **O2/O3/O4/O5/O6** sind umgesetzt: Linux-Pakete, Release-Workflow,
  Vollmatrix, `ui_smoke` und plattformgerechte Werkzeug-Shortcuts.
- Die Befunde **#163–#206** wurden in den dokumentierten PRs geschlossen und
  mit Regressionstests beziehungsweise CI-Prüfungen abgesichert.

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** Deutsch und Englisch sind in der App
  umschaltbar. Die Dokusprachen es/fr/uk/zh sind noch keine Runtime-Locales;
  bei Bedarf key-für-key in `bgremover.i18n` ergänzen und mit Tests absichern.

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-14)

Aktuell sind **8** Issues offen. Die erneute Prüfung von Beschreibung, Code,
Tests und Dokumentation bestätigt fünf umsetzbare Befunde. Drei Issues
(#161/#203/#204) beschreiben dagegen ohne weitere Nachweise keine Aufgabe für
dieses Repository und sollten geschlossen oder neu belegt werden.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: Clone-URL führt für anonyme Nutzer zu 404 | 🟢 Niedrig | 🟢 Niedrig | HTTPS-URL ist korrekt; bei privatem Repo als `not planned` schließen, sonst Veröffentlichungsweg festlegen |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 – CVE-Sammlung | 🟢 Niedrig | 🟢 Niedrig | Nicht im Projekt-Snapshot; ohne reproduzierbaren Abhängigkeitspfad als `not planned` schließen und fehlerhafte Schweregrade nicht übernehmen |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | PyJWT 2.7.0 – CVE-Sammlung | 🟢 Niedrig | 🟢 Niedrig | Nicht im Projekt-Snapshot; ohne reproduzierbaren Abhängigkeitspfad als `not planned` schließen, Schweregrade und defekten GHSA-Link korrigieren |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | INSTALL-Review: Releases, Raspberry Pi und macOS-Diagnose | 🟡 Mittel | 🟢 Niedrig | Alle drei Befunde gelten noch; Root-Doku und fünf Übersetzungen gemeinsam korrigieren, Verfügbarkeit der Release-Artefakte ehrlich dokumentieren |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` kann Worker unsicher abbrechen | 🟡 Mittel | 🟠 Hoch | Relevanter Sicherheits-/Stabilitätsbefund; Architekturentscheidung für blockierende native Aufrufe nötig, bestehender Test konserviert derzeit das Fehlverhalten |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` lädt die vollständige PyQt6-GUI | 🟡 Mittel | 🟡 Mittel | Vollständig dokumentiert und bereit für PR; öffentliche API mit Lazy-Exports nach PEP 562 erhalten |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Fehlende Migration hebt `schema_version` trotzdem an | 🟡 Mittel | 🟢 Niedrig | Bug bestätigt; Test umkehren und Semantik für Version 0 explizit festlegen, bevor echte Migrationen hinzukommen |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo-Speicherlimit erfasst den Redo-Stack nicht | 🟢 Niedrig | 🟡 Mittel | Auf gemeinsames Undo/Redo-Budget eingrenzen; Originalbild und Qt-Speicher erst nach Messung einbeziehen |

### Empfohlene PR-Reihenfolge

1. **#226** — kleiner, vollständig bestätigter Doku-Fix in allen sechs Sprachen; Release-Verfügbarkeit muss dabei entschieden oder klar eingeschränkt werden.
2. **#232** — Lazy-Exports per PEP 562 mit Import-Regressionstests; Issue ist ohne weitere Klärung umsetzbar.
3. **#234** — Versionssprung bei fehlender Migration verhindern und den aktuell gegenteiligen Test korrigieren.
4. **#231** — erst Abbruchmodell festlegen; für dauerhaft blockierende native Aufrufe ist ein Subprozess die belastbare Lösung.
5. **#235** — optionales gemeinsames Undo/Redo-Speicherbudget nach klarer Scope-Definition implementieren.
6. **#161/#203/#204** — als `not planned` schließen, sofern kein konkreter Veröffentlichungs- beziehungsweise Abhängigkeitspfad nachgereicht wird.

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
