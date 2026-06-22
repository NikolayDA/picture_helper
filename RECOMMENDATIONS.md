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

## Offene GitHub-Issues – Triage-Stand (2026-06-22, aktualisiert)

Stand 2026-06-22 zeigt GitHub **12** offene Issues. Der kritische
Export-Regressionsbefund **#363** ist über **PR #367** behoben und geschlossen.
Verbleibend sind das EufyMake-Epic **#351/#352–#355**, die Doku-Lücken **#357**
und **#339**, die beiden Height-Map-Folgebefunde **#364** (Kind/Rollen-Kontext)
und **#365** (Medianfilter-Speicher) sowie die Test-/CI-Befunde **#318**,
**#299** und **#245**. Der Wartungs-/Skip-Pfad **#322** ist über **#342**
erledigt und geschlossen. Für **#364** ist die Vertragsentscheidung inzwischen
gefallen (Issue-Kommentar 2026-06-22): `LayerKind.HEIGHT` ist verbindlich,
`HEIGHT_MAP` darf nur auf HEIGHT-Ebenen liegen – damit ist das Issue
umsetzungsreif.

Bewertung: **Relevanz** = Bedeutung für Roadmap/Nutzer, **Komplexität** =
geschätzter Umsetzungsaufwand.

| # | Titel | Relevanz | Komplexität | Empfohlener nächster Schritt |
|---|-------|----------|-------------|------------------------------|
| [#364](https://github.com/NikolayDA/picture_helper/issues/364) | Height-Map-Kontext: UI und Canvas widersprechen sich bei `HEIGHT_MAP`-Rolle | 🟠 Hoch | 🟡 Mittel | **Ready for PR – Entscheidung gefallen.** Vertrag steht: `LayerKind.HEIGHT` ist verbindlich, `HEIGHT_MAP` nur auf HEIGHT-Ebenen. Modell, Deserialisierung (Legacy-Normalisierung), Layer-/Height-Panel und Canvas auf diesen einen Vertrag bringen. Vor #352 umsetzen, weil der EufyMake-Export dieselbe Rollenabbildung nutzt. |
| [#365](https://github.com/NikolayDA/picture_helper/issues/365) | Height-Map-Medianfilter kann bei großen Projekten den Speicher erschöpfen | 🟠 Hoch | 🟡 Mittel | **Ready for PR.** Median block-/kachelweise statt über einen vollständigen `(2r+1)² × H × W`-Stack berechnen; 40-MP-/Radius-Vertrag für Median und Gauß mit Speicherbenchmark absichern. |
| [#351](https://github.com/NikolayDA/picture_helper/issues/351) | [Epic] Konsistentes EufyMake-Exportpaket | 🟠 Hoch | 🔴 Hoch (Epic) | **Needs refinement** – Scope laut Deep-Research (Issue-Kommentar) auf „robuste Import-Assets für EufyMake Studio“ schärfen; native `.empf`-Erzeugung **nicht** als Default-Ziel. Wird über #352–#355 abgewickelt. |
| [#352](https://github.com/NikolayDA/picture_helper/issues/352) | Export-Datenmodell & Paketdefinition (Qt-frei) + ADR | 🟠 Hoch | 🟡 Mittel | **Ready for PR – ADR zuerst** – Deep-Research erledigt (Issue-Kommentare), aber die Konventions-/ADR-Entscheidung ist **noch nicht im Repo dokumentiert** und muss als erster Schritt dieses PR schriftlich festgehalten werden (Akzeptanzkriterium von #352). Qt-freies `eufymake_export.py` mit `ExportPlan`/`ExportAsset` (Farbmotiv-PNG+Alpha, Höhe-Graustufe hell=hoch, Gloss-Maske); Scope = Import-Assets für EufyMake Studio; 16-Bit/Gloss-Semantik/natives `.empf` als „offen“ markieren. Fundament – entsperrt #353–#355. |
| [#353](https://github.com/NikolayDA/picture_helper/issues/353) | Asset-Rendering & atomares Paket-Schreiben | 🟠 Hoch | 🟡 Mittel | **Blocked** – benötigt #352; danach sauber geschnitten (Rendering + atomares Schreiben). |
| [#354](https://github.com/NikolayDA/picture_helper/issues/354) | Pre-Export-Konsistenzprüfung | 🟠 Hoch | 🟡 Mittel | **Blocked** – benötigt #352. Prüf-Bausteine wiederverwendbar halten (Synergie mit der allgemeinen Fehlerprüfung vor Export). |
| [#355](https://github.com/NikolayDA/picture_helper/issues/355) | UI: EufyMake-Export-Dialog + Menü + i18n + Settings | 🟠 Hoch | 🟡 Mittel | **Blocked** – benötigt #352–#354. UI-Text laut Deep-Research: „Assets für EufyMake Studio vorbereiten“, nicht „fertiges Projekt erzeugen“. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | **Blocked (extern)** – Repo-Härtung über #322/#342 (geschlossen) erledigt; verbleibender Blocker ist die OpenAI-/Billing-Quota. Nach Quota-Fix den geplanten Scan einmal manuell anstoßen, dann schließen. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: Job-Level-Permission-Overrides im Reusable-WF berücksichtigen | 🟢 Niedrig | 🟡 Mittel | **Needs refinement** – erst die GitHub-Semantik (Top-Level vs. effektiv-per-Job) belegen; OIDC-Guard aus #303 darf nicht aufgeweicht werden. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF nicht als Eingabeformat unterstützt | 🟢 Niedrig | 🟢 Niedrig | **Ready for PR (Doku)** – Maintainer hat HEIC **bewusst ausgeschlossen** (Kommentar 2026-06-21). Nur noch README/ANLEITUNG klarstellen, dann schließen. |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Doku: Start-mit-Pfad/Finder-Öffnen fehlt in ANLEITUNG §4 | 🟢 Niedrig | 🟢 Niedrig | **Ready for PR (Doku)** – Hauptdatei und alle fünf i18n-Fassungen synchron ergänzen; „Zuletzt geöffnet“ dabei auf Bilder und `.bgrproj`-Projekte präzisieren. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟢 Niedrig | **Ready for PR (opportunistisch)** – kein Produkt-/CI-Blocker; höchster Nutzen zuerst (Lasso-Endpunkt asserten, `test_helpers`-Zeile, `set_brush_size`-Tests konsolidieren). |

### Als Nächstes empfohlen (PR-Reihenfolge)

1. **#364** zuerst umsetzen – die nun beschlossene Kind/Rollen-Invariante
   (`LayerKind.HEIGHT` verbindlich) vor dem EufyMake-Export vereinheitlichen.
2. **#365** parallel härten, bevor große Height-Maps den Median-/Vorschaupfad
   nutzen.
3. **#352** danach – Fundament des EufyMake-Epics, ADR zuerst; entsperrt
   #353/#354.
4. **#353** und **#354** parallel, sobald #352 steht; danach **#355**.
5. **#357**, **#339** (kleine Doku-PRs) und **#299** (Test-Cleanup) als niedrig
   priorisierte Lückenfüller dazwischen.
6. **#318** zurückstellen, bis die GitHub-Permissions-Semantik belegt ist.
7. **#245** extern blockiert lassen (kein Repo-Patch bringt die Quota zurück).

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
