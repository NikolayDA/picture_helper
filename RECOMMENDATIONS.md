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

Nach der Triage sind **13** Issues offen. **#203/#204** wurden mangels
Projekt-Abhängigkeit als `not planned` geschlossen; **#226/#244** waren durch
PR #246 beziehungsweise #256 bereits erledigt. Elf Issues haben einen
umsetzbaren Repository-Scope. #161 braucht eine Veröffentlichungsentscheidung,
#245 primär eine account-seitige Billing-/Quota-Korrektur.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: Clone-URL führt für anonyme Nutzer zu 404 | 🟢 Niedrig | 🟢 Niedrig | „Runde 5“ ist erledigt; für die Clone-Doku zuerst öffentlich vs. privat/invite-only entscheiden |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` kann Worker unsicher abbrechen | 🟠 Hoch | 🟡 Mittel | Erster PR: zweiten Wait begrenzen, Fehlerpfad loggen und testen; Subprozess-Architektur separat behandeln |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` lädt die vollständige PyQt6-GUI | 🟡 Mittel | 🟡 Mittel | Bereit für PR: öffentliche API mit Lazy-Exports nach PEP 562 erhalten, Import-Regressionstest ergänzen |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Fehlende Migration hebt `schema_version` trotzdem an | 🟡 Mittel | 🟢 Niedrig | Mit #259 bündeln: fehlende Migrationsschritte dürfen Settings weder markieren noch verändern |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo-Speicherlimit erfasst den Redo-Stack nicht | 🟢 Niedrig | 🟡 Mittel | Gemeinsames Undo/Redo-Budget; Originalbild und Qt-Speicher nur messen/dokumentieren |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | Quota account-seitig beheben; Repo-seitig nur klare Fehlerbehandlung ergänzen, kein `setup-node`-Fix |
| [#248](https://github.com/NikolayDA/picture_helper/issues/248) | Escape löscht die Auswahl, statt das Polygon-Lasso abzubrechen | 🟡 Mittel | 🟡 Mittel | Mit #260 bündeln: zentrale Abbruch-Priorität Crop → Lasso → Auswahl aufheben |
| [#249](https://github.com/NikolayDA/picture_helper/issues/249) | Dateizuordnungen übergeben Bildpfade, App öffnet sie aber nicht | 🟡 Mittel | 🟡 Mittel | Bereit für PR: Startpfade und macOS-`QFileOpenEvent` über den validierten Ladepfad öffnen |
| [#257](https://github.com/NikolayDA/picture_helper/issues/257) | Release-Follow-ups: Publish-Kontext, Tag-Gate und Re-Run-Artefakte | 🟠 Hoch | 🟡 Mittel | Eigenständiger Top-PR vor dem nächsten Release-Tag; Workflow, Doku und Governance-Tests gemeinsam ändern |
| [#258](https://github.com/NikolayDA/picture_helper/issues/258) | Bildlade-Limit allokiert bis zu 512 MiB vorab | 🟠 Hoch | 🟡 Mittel | Eigenständiger PR: chunked read, lokalisierte Größenmeldung und präzise Grenzwertanzeige |
| [#259](https://github.com/NikolayDA/picture_helper/issues/259) | Future-Schema wird beim Recent-Files-Menü verändert | 🟠 Hoch | 🟡 Mittel | Mit #234 bündeln: Future-Schema durchgehend schreibgeschützt behandeln |
| [#260](https://github.com/NikolayDA/picture_helper/issues/260) | Crop-Abbruch stellt Werkzeug-Cursor nicht wieder her | 🟡 Mittel | 🟢 Niedrig | Mit #248 bündeln; zentralen Interaktionsabbruch samt Cursor-Wiederherstellung testen |
| [#261](https://github.com/NikolayDA/picture_helper/issues/261) | Pinsel-Overlay scannt die ganze Maske bei jeder Bewegung | 🟡 Mittel | 🟡 Mittel | Eigenständiger Performance-PR mit Auswahlpixel-Zähler und Spy-Test |

### Empfohlene PR-Reihenfolge

1. **#257** — Release-Workflow vor dem nächsten Tag vollständig belastbar machen.
2. **#258** — Voraballokation und gemischte/irreführende Größenmeldung beheben.
3. **#234 + #259** — QSettings-Migration und Future-Schema-Schutz in einem PR.
4. **#248 + #260** — zentrale Escape-/Crop-Abbruchsemantik samt korrektem Cursor.
5. **#231** — begrenzten Shutdown-Fallback liefern; Subprozess später separat.
6. **#261** — O(Bildgröße)-Maskenscan aus dem häufigen Pinselpfad entfernen.
7. **#249** — Dateizuordnungen und macOS-Open-Events tatsächlich verarbeiten.
8. **#232** — leichte Paketimporte über PEP-562-Lazy-Exports herstellen.
9. **#235** — gemeinsames Undo/Redo-Verlaufsbudget implementieren.
10. **#245** — Quota extern wiederherstellen; optionale Workflow-Härtung separat.
11. **#161** — Veröffentlichungsmodell entscheiden, dann Doku ändern oder schließen.

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
