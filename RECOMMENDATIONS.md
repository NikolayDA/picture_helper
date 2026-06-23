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
- Das Epic **#351 (EufyMake-Importpaket)** ist mit **#352–#355** abgeschlossen (Datenmodell+ADR, Rendern/atomares Schreiben, Konsistenzprüfung, UI/Dialog/Settings); Import-Assets statt nativem `.empf`, durch Unit-/`ui_smoke`-Tests abgesichert.
- Die Befunde **#163–#206** wurden in den dokumentierten PRs geschlossen und
  mit Regressionstests beziehungsweise CI-Prüfungen abgesichert.
- Die PRs **#263–#269** haben **#257, #258, #234 + #259, #248 + #260, #231**
  und **#249** geschlossen; **#261** wurde über PR #268 erledigt und geschlossen.
- PR **#274** hat **#232** geschlossen: `import bgremover` lädt über PEP-562-
  Lazy-Exports keinen Qt-Stack mehr; ein Subprozess-Regressionstest sichert das ab.
- Die PR-Welle **#280–#284** hat den Wochen-Benchmark abgelegt, drei Befunde
  umgesetzt — **#235** (gemeinsames Undo/Redo-Budget, PR #281), **#275**
  (lokalisierte Megapixel-Meldung, PR #282) und **#270** (rembg/ONNX-Subprozess
  via `ai_process.py`, PR #283) — und die Roadmap nachgezogen (PR #284).
  **#235, #270 und #275 sind inzwischen geschlossen.**
- Die zwei Post-Merge-Codex-Folgebefunde aus #283 und #264 sind ebenfalls
  behoben **und geschlossen**: **#285** (Robustheit/Speicher des
  rembg-Subprozesses, PR #289) und **#286** (Speicherspitzen im gekappten
  Datei-Read, PR #290).

- **N9 ✅ — Projekt-/Ebenen-Datenmodell (Epic #329) umgesetzt.** Qt-freies
  Domänenmodell (#330), ebenenbewusste Historie (#331), Komposit-Canvas (#332),
  `.bgrproj`-Format (#333), Ebenen-Panel/Projekt-Menü (#334) und Migration/
  Integration (#335) – Einzelbild-Parität gewahrt, `make check`/`make ui` grün.
- **N10 ✅ — Height-Map-Arbeitsbereich (Epic #344) umgesetzt.** Qt-freie
  Höhen-Repräsentation + 2D-Visualisierung (#345), Erzeugung/Graustufen-Import
  (#346), Höhen-Editor (#347), `height_ops` mit Live-Vorschau (#348) und
  moduskontextueller Height-Map-Tab (#349); COLOR-Editing ohne Regression.
- **N11 ✅ — Phase-0-Politur (Epic #358) umgesetzt.** Skalieren auf Zielgröße
  (#359), Farbkorrektur Helligkeit/Kontrast/Sättigung (Qt-frei
  `color_ops.adjust_color`, alpha-erhaltend, #360) und Kantenglättung/Feather der
  Alphakante (`image_ops.feather_alpha`, #361) – alle undo-/redobar und
  verlustfrei im `.bgrproj` (PR #362).
- **#363 ✅ — Export-Regression behoben (PR #367).** „Bild speichern“ schreibt
  wieder unabhängig von der aktiven Ebene das COLOR-Komposit; Anzeige- und
  Export-Rendering sind getrennt, mit Pixel-Regressionstest abgesichert.

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** Deutsch und Englisch sind in der App
  umschaltbar. Die Dokusprachen es/fr/uk/zh sind noch keine Runtime-Locales;
  bei Bedarf key-für-key in `bgremover.i18n` ergänzen und mit Tests absichern.
- **O7 ✅ — Subprozess für rembg/ONNX erledigt (PR #283, Issue #270 geschlossen).**
  Die nicht unterbrechbare KI-Inferenz läuft jetzt in einem per `spawn`
  gestarteten Prozess (`ai_process.py`); `QThread.terminate()` als KI-Notausgang
  ist entfallen. Die Robustheits-/Speicher-Folgebefunde sind in **#285**
  (PR #289) behoben und geschlossen.

## Offene GitHub-Issues – Triage-Stand (2026-06-23, aktualisiert)

Stand 2026-06-23 zeigt GitHub noch **11** offene Issues. Das EufyMake-Epic
**#351** ist nach den heutigen Merge-PRs **#372–#374** geschlossen: **#352**
(ADR/Datenmodell), **#353** (Rendering/atomarer Writer), **#354**
(Konsistenzprüfung) und **#355** (Dialog/Menü/Settings) sind vollständig im Repo
verankert und durch gezielte Tests abgesichert. Die Review-Korrektur aus
**#374** behebt zusätzlich die Generator-Erschöpfung bei `optional_roles` und
verhindert, dass ein Exportordner versehentlich eine vorhandene Datei ersetzt.
Als nächster Roadmap-Block ist heute das Epic **#375** mit den Sub-Issues
**#376–#380** für maßgenaue mm/DPI-Ausgaben und eine allgemeine Exportprüfung
hinzugekommen. Daneben verbleiben die Doku-Lücken **#357** und **#339** sowie
die Test-/CI-Befunde **#318**, **#299** und **#245**; neue Folge-Issues aus dem
EufyMake-Review selbst sind nicht nötig.

Bewertung: **Relevanz** = Bedeutung für Roadmap/Nutzer, **Komplexität** =
geschätzter Umsetzungsaufwand.

| # | Titel | Relevanz | Komplexität | Empfohlener nächster Schritt |
|---|-------|----------|-------------|------------------------------|
| [#375](https://github.com/NikolayDA/picture_helper/issues/375) | [Epic] Maßgenaue Ausgabe (mm/DPI) + allgemeine Exportprüfung | 🟠 Hoch | 🔴 Hoch (Epic) | **Ready for PR – Fundament zuerst:** #376 (Qt-freie Geometrie + Projekt-Metadaten), danach #377/#378/#379 parallelisierbar; #380 schließt die UI-Integration und das Epic ab. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | **Blocked (extern)** – Repo-Härtung über #322/#342 (geschlossen) erledigt; verbleibender Blocker ist die OpenAI-/Billing-Quota. Nach Quota-Fix den geplanten Scan einmal manuell anstoßen, dann schließen. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: Job-Level-Permission-Overrides im Reusable-WF berücksichtigen | 🟢 Niedrig | 🟡 Mittel | **Needs refinement** – erst die GitHub-Semantik (Top-Level vs. effektiv-per-Job) belegen; OIDC-Guard aus #303 darf nicht aufgeweicht werden. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF nicht als Eingabeformat unterstützt | 🟢 Niedrig | 🟢 Niedrig | **Ready for PR (Doku)** – Maintainer hat HEIC bewusst ausgeschlossen (Kommentar 2026-06-21). Nur noch README/ANLEITUNG klarstellen, dann schließen. |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Doku: Start-mit-Pfad/Finder-Öffnen fehlt in ANLEITUNG §4 | 🟢 Niedrig | 🟢 Niedrig | **Ready for PR (Doku)** – Hauptdatei und alle fünf i18n-Fassungen synchron ergänzen; „Zuletzt geöffnet“ dabei auf Bilder und `.bgrproj`-Projekte präzisieren. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟢 Niedrig | **Ready for PR (opportunistisch)** – kein Produkt-/CI-Blocker; höchster Nutzen zuerst (Lasso-Endpunkt asserten, `test_helpers`-Zeile, `set_brush_size`-Tests konsolidieren). |

### Review der am 2026-06-23 geschlossenen PRs/Issues

Geprüft wurden die heute geschlossenen PRs **#372**, **#373** und **#374** sowie
die Issues **#351** und **#355** (zusätzlich die in #372 geschlossenen
Teil-Issues **#352–#354** anhand der Merge-Inhalte). Die EufyMake-Themen sind
sauber abgeschlossen: ADR, Qt-freie Plan-/Prüf-/Writer-Module, UI-Anbindung,
Settings-Persistenz und die nachgelagerte #373-Review-Korrektur sind vorhanden.
Die lokale Prüfung der betroffenen Module und Tests ergab keinen offenen
Folgebefund; Kommentare oder neue Issues sind daher nicht erforderlich.

### Als Nächstes empfohlen (PR-Reihenfolge)

1. **#376** als Fundament des Roadmap-Rang-#4-Epics; danach **#377**, **#378**
   und **#379** parallelisierbar, abschließend **#380**.
2. **#357** und **#339** als kleine, unabhängige Doku-PRs einstreuen.
3. **#299** opportunistisch bereinigen; **#318** bis zum Semantik-Beleg
   zurückstellen und **#245** extern blockiert lassen.

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
