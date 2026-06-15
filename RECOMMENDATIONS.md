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
- Die PRs **#263–#269** haben **#257, #258, #234 + #259, #248 + #260, #231**
  und **#249** geschlossen; **#261** wurde über PR #268 erledigt und geschlossen.
- PR **#274** hat **#232** geschlossen: `import bgremover` lädt über PEP-562-
  Lazy-Exports keinen Qt-Stack mehr; ein Subprozess-Regressionstest sichert das ab.
- Die PR-Welle **#280–#283** hat den Wochen-Benchmark abgelegt und drei Befunde
  umgesetzt: **#235** (gemeinsames Undo/Redo-Budget, PR #281, geschlossen),
  **#275** (lokalisierte Megapixel-Meldung, PR #282) und **#270**
  (rembg/ONNX-Subprozess via `ai_process.py`, PR #283). #275 und #270 sind im
  Code erledigt und müssen nur noch als Issue geschlossen werden.

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** Deutsch und Englisch sind in der App
  umschaltbar. Die Dokusprachen es/fr/uk/zh sind noch keine Runtime-Locales;
  bei Bedarf key-für-key in `bgremover.i18n` ergänzen und mit Tests absichern.
- **O7 ✅ — Subprozess für rembg/ONNX erledigt (PR #283, Issue #270).** Die
  nicht unterbrechbare KI-Inferenz läuft jetzt in einem per `spawn` gestarteten
  Prozess (`ai_process.py`); `QThread.terminate()` als KI-Notausgang ist
  entfallen. Issue #270 ist nur noch zu schließen.

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-15)

Nach der PR-Welle **#280–#283** sind **7** Issues offen. **#235** wurde über
PR #281 geschlossen. **#270** (PR #283) und **#275** (PR #282) sind im Code
bereits umgesetzt und müssen nur noch als Issue geschlossen werden. Neu sind
drei Performance-Befunde — **#277/#278/#279** — aus dem Wochen-Benchmark-Lauf
(#280); laut Owner-Triage sind sie **noch nicht** als Code-Regression
bestätigt, weil die Baseline vom 2026-06-08 keinen Umgebungs-Fingerprint trägt.
Alle offenen Issues wurden gegen den aktuellen Code verifiziert.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#270](https://github.com/NikolayDA/picture_helper/issues/270) | rembg/ONNX-Inferenz in einen Subprozess auslagern (Folge aus #231) | 🟠 Hoch | 🟡 Mittel | **Erledigt im Code (PR #283, `ai_process.py`).** Verifizieren und Issue schließen; Roadmap O7 abgeschlossen |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | Performance-Regression: JPEG (+38.4%) | 🟡 Mittel | 🟡 Mittel | Refinement: noch nicht als Code-Regression bestätigt. Benchmark um Umgebungs-Fingerprint + Bestätigungsläufe (Median) erweitern, dann erst gegen kompatible Baseline vergleichen. Mit #278/#279 bündeln |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | Performance-Regression: TIFF (+21.8%) | 🟡 Mittel | 🟡 Mittel | Wie #277: gemeinsame Benchmark-Härtung; den Encode-Pfad (`save_image_file`) erst nach einem kompatiblen Bestätigungslauf untersuchen |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | Performance-Regression: WebP (+13.7%) | 🟡 Mittel | 🟡 Mittel | Wie #277/#278: ein gemeinsamer PR für Fingerprint + Median-Bestätigung; nur bestätigte Regressionen melden |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | Blockiert (extern): Quota account-seitig wiederherstellen. Repo-seitig nur klare Fehlerbehandlung (graceful skip) + optionaler Node-24-Bump, kein erzwungener `setup-node`-Fix |
| [#275](https://github.com/NikolayDA/picture_helper/issues/275) | Megapixel-„Bild zu groß“-Meldung ist nicht lokalisiert | 🟢 Niedrig | 🟢 Niedrig | **Erledigt im Code (PR #282).** `_too_large_message` läuft über `tr("status.image_too_large[_mp]", …)` (de/en); verifizieren und Issue schließen |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: Clone-URL führt für anonyme Nutzer zu 404 | 🟢 Niedrig | 🟢 Niedrig | Entscheidung nötig: öffentlich vs. privat/invite-only, dann Clone-Doku ändern oder schließen („Runde 5“ ist bereits erledigt) |

### Empfohlene PR-Reihenfolge

1. **#270 + #275** — beide sind im Code erledigt (PR #283 / #282): verifizieren und die Issues schließen.
2. **#277/#278/#279** — ein gemeinsamer PR: Benchmark um Umgebungs-Fingerprint und Bestätigungsläufe (Median) erweitern; Regression nur bei kompatibler Baseline melden. Gut abgegrenzt, PR-bereit.
3. **#245** — Quota extern wiederherstellen; optionale Workflow-Härtung (graceful skip + Node 24) als kleiner separater PR.
4. **#161** — Veröffentlichungsmodell entscheiden, dann Doku ändern oder schließen.

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
