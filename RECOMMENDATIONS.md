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

Aktuell sind **15** Issues offen. Die Prüfung von Beschreibung, Code, Tests und
Dokumentation ergibt: **neun** Befunde sind gut umrissen und PR-bereit, zwei
(#231/#235) brauchen zuerst eine Architektur- bzw. Scope-Entscheidung, #245 ist
ein Infrastruktur-/Billing-Problem (kein Code-Defekt) und drei (#161/#203/#204)
beschreiben ohne weiteren Nachweis keine Aufgabe für dieses Repository.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: Clone-URL führt für anonyme Nutzer zu 404 | 🟢 Niedrig | 🟢 Niedrig | HTTPS-URL ist korrekt; bei privatem Repo als `not planned` schließen, sonst Veröffentlichungsweg festlegen |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 – CVE-Sammlung | 🟢 Niedrig | 🟢 Niedrig | Nicht im Projekt-Snapshot; ohne reproduzierbaren Abhängigkeitspfad als `not planned` schließen, fehlerhafte Schweregrade nicht übernehmen |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | PyJWT 2.7.0 – CVE-Sammlung | 🟢 Niedrig | 🟢 Niedrig | Nicht im Projekt-Snapshot; ohne reproduzierbaren Abhängigkeitspfad als `not planned` schließen, Schweregrade und defekten GHSA-Link korrigieren |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | INSTALL-Review: Releases, Raspberry Pi und macOS-Diagnose | 🟡 Mittel | 🟢 Niedrig | Bereit für PR: alle drei Befunde gelten; Root-Doku und fünf Übersetzungen gemeinsam korrigieren, Verfügbarkeit der Release-Artefakte ehrlich dokumentieren |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` kann Worker unsicher abbrechen | 🟡 Mittel | 🟠 Hoch | Verfeinern: Architekturentscheidung für blockierende native Aufrufe nötig (Subprozess); bestehender Test konserviert derzeit das Fehlverhalten |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` lädt die vollständige PyQt6-GUI | 🟡 Mittel | 🟡 Mittel | Bereit für PR: öffentliche API mit Lazy-Exports nach PEP 562 erhalten, Import-Regressionstest ergänzen |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Fehlende Migration hebt `schema_version` trotzdem an | 🟡 Mittel | 🟢 Niedrig | Bereit für PR: Versionssprung verhindern, Test umkehren und Semantik für Version 0 festlegen |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo-Speicherlimit erfasst den Redo-Stack nicht | 🟢 Niedrig | 🟡 Mittel | Verfeinern: auf gemeinsames Undo/Redo-Budget eingrenzen; Originalbild und Qt-Speicher erst nach Messung einbeziehen |
| [#244](https://github.com/NikolayDA/picture_helper/issues/244) | Dead-Code: `ImageCanvas._zoom` und ungenutzter `launch_worker`-Wrapper | 🟢 Niedrig | 🟢 Niedrig | Bereit für PR: `_zoom` entfernen, für `launch_worker` Entfernen vs. dokumentierte API entscheiden; kleiner Aufräum-PR |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | Infrastruktur/Billing: OpenAI-Kontingent account-seitig wiederherstellen; Workflow gegen Quota-Ausfälle robust machen und `setup-node` auf Node 24 heben |
| [#247](https://github.com/NikolayDA/picture_helper/issues/247) | Aktiver Crop überlebt Bildtransformationen und erzeugt falsche Pixel | 🟠 Hoch | 🟡 Mittel | Bereit für PR (Top): transienten Zustand bei jedem Bildwechsel zurücksetzen; Regressionstest 400×200 + 90°-Drehung im Issue beschrieben |
| [#248](https://github.com/NikolayDA/picture_helper/issues/248) | Escape löscht die Auswahl, statt das Polygon-Lasso abzubrechen | 🟡 Mittel | 🟡 Mittel | Bereit für PR: Escape-Priorität Crop → Lasso → Auswahl aufheben; teilt den transienten-Zustand-Vertrag mit #247 |
| [#249](https://github.com/NikolayDA/picture_helper/issues/249) | Dateizuordnungen übergeben Bildpfade, App öffnet sie aber nicht | 🟡 Mittel | 🟡 Mittel | Bereit für PR: Startpfade und macOS-`QFileOpenEvent` über den validierten Ladepfad öffnen |
| [#250](https://github.com/NikolayDA/picture_helper/issues/250) | Release-Workflow veröffentlicht Artefakte ohne Full-CI-Gate | 🟠 Hoch | 🟡 Mittel | Bereit für PR (vor nächstem Tag): Full-CI per `needs` erzwingen, Tag/`project.version` prüfen, `\|\| true` entfernen |
| [#251](https://github.com/NikolayDA/picture_helper/issues/251) | Leere Auswahl behält nach dem Radieren die Overlay-QPixmap | 🟡 Mittel | 🟢 Niedrig | Bereit für PR (Quick Win): bei leerer Maske Overlay-Pixmap freigeben; exakter Patch im Issue |

### Empfohlene PR-Reihenfolge

1. **#247** — Hoch: Korrektheits-/Datenfehler (veraltetes Crop-Rechteck erzeugt transparente Padding-Pixel); vollständig umrissen inkl. Regressionstest.
2. **#250** — Hoch vor dem nächsten Release-Tag: Full-CI-Gate per `needs` erzwingen, Tag/Version abgleichen, `|| true` entfernen.
3. **#251** — schneller Speicher-Fix: leere Maske gibt die Overlay-Pixmap frei; exakter Patch liegt im Issue.
4. **#244** — Dead-Code-Bereinigung (`_zoom` entfernen, `launch_worker` entscheiden); kleiner, risikoarmer Aufräum-PR.
5. **#234** — Versionssprung bei fehlender Migration verhindern und den aktuell gegenteiligen Test korrigieren.
6. **#248** — Escape-Priorität Crop → Lasso → Auswahl aufheben; teilt den transienten-Zustand-Vertrag mit #247 und lässt sich bündeln.
7. **#232** — Lazy-Exports per PEP 562 mit Import-Regressionstest.
8. **#249** — Startpfade und macOS-`QFileOpenEvent` über den validierten Ladepfad öffnen.
9. **#226** — Doku-Fix in allen sechs Sprachen; Release-Verfügbarkeit ehrlich dokumentieren.
10. **#245** — OpenAI-Billing account-seitig wiederherstellen; Scan-Workflow gegen Quota-Ausfälle robust machen und `setup-node` auf Node 24 heben.
11. **#231** — erst Abbruchmodell festlegen (Subprozess für dauerhaft blockierende native Aufrufe), dann umsetzen.
12. **#235** — gemeinsames Undo/Redo-Speicherbudget erst nach klarer Scope-Definition implementieren.
13. **#161/#203/#204** — als `not planned` schließen, sofern kein konkreter Veröffentlichungs- beziehungsweise Abhängigkeitsnachweis nachgereicht wird.

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
