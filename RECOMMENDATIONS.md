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
  Höhen-Repräsentation + 2D-Visualisierung (#345), algorithmische Erzeugung aus
  Bild + Graustufen-Import (#346), Höhen-Editor Aufhellen/Abdunkeln/Setzen/
  Invertieren (#347), Optimierung `height_ops` mit Live-Vorschau (#348) und der
  bedienbare, moduskontextuelle Height-Map-Tab (#349). Kompletter Ablauf
  erzeugen → malen → optimieren → invertieren → verlustfrei im `.bgrproj`;
  COLOR-Editing ohne Regression, i18n de/en in Parität, `make check`/`make ui` grün.

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** Deutsch und Englisch sind in der App
  umschaltbar. Die Dokusprachen es/fr/uk/zh sind noch keine Runtime-Locales;
  bei Bedarf key-für-key in `bgremover.i18n` ergänzen und mit Tests absichern.
- **O7 ✅ — Subprozess für rembg/ONNX erledigt (PR #283, Issue #270 geschlossen).**
  Die nicht unterbrechbare KI-Inferenz läuft jetzt in einem per `spawn`
  gestarteten Prozess (`ai_process.py`); `QThread.terminate()` als KI-Notausgang
  ist entfallen. Die Robustheits-/Speicher-Folgebefunde sind in **#285**
  (PR #289) behoben und geschlossen.

## Offene GitHub-Issues – Triage-Stand (2026-06-22)

Stand 2026-06-22 zeigt GitHub **9** offene Issues. Neu hinzugekommen ist das
**EufyMake-Export-Epic #351** mit den Sub-Issues **#352–#355** (Roadmap-Rang #3).
Der zuvor gelistete Wartungs-/Skip-Pfad **#322** ist über **#342** erledigt und
inzwischen **geschlossen**; die Projekt-/Ebenen- und Security-Test-Issues
**#323/#324/#326** und **#329–#335** bleiben in **#337/#338/#340** abgeschlossen.

Bewertung: **Relevanz** = Bedeutung für Roadmap/Nutzer, **Komplexität** =
geschätzter Umsetzungsaufwand.

| # | Titel | Relevanz | Komplexität | Empfohlener nächster Schritt |
|---|-------|----------|-------------|------------------------------|
| [#351](https://github.com/NikolayDA/picture_helper/issues/351) | [Epic] Konsistentes EufyMake-Exportpaket | 🟠 Hoch | 🔴 Hoch (Epic) | **Needs refinement** – Scope laut Deep-Research (Issue-Kommentar) auf „robuste Import-Assets für EufyMake Studio“ schärfen; native `.empf`-Erzeugung **nicht** als Default-Ziel. Wird über #352–#355 abgewickelt. |
| [#352](https://github.com/NikolayDA/picture_helper/issues/352) | Export-Datenmodell & Paketdefinition (Qt-frei) + ADR | 🟠 Hoch | 🟡 Mittel | **Ready for PR** – Rechercheaufgabe erledigt, ADR-Entscheidung steht in den Kommentaren. Qt-freies `eufymake_export.py` mit `ExportPlan`/`ExportAsset` (Farbmotiv-PNG+Alpha, Höhe-Graustufe hell=hoch, Gloss-Maske); 16-Bit/Gloss-Semantik/natives `.empf` als „offen“ markieren. Fundament – entsperrt #353–#355. |
| [#353](https://github.com/NikolayDA/picture_helper/issues/353) | Asset-Rendering & atomares Paket-Schreiben | 🟠 Hoch | 🟡 Mittel | **Blocked** – benötigt #352; danach sauber geschnitten (Rendering + atomares Schreiben). |
| [#354](https://github.com/NikolayDA/picture_helper/issues/354) | Pre-Export-Konsistenzprüfung | 🟠 Hoch | 🟡 Mittel | **Blocked** – benötigt #352. Prüf-Bausteine wiederverwendbar halten (Synergie mit der allgemeinen Fehlerprüfung vor Export). |
| [#355](https://github.com/NikolayDA/picture_helper/issues/355) | UI: EufyMake-Export-Dialog + Menü + i18n + Settings | 🟠 Hoch | 🟡 Mittel | **Blocked** – benötigt #352–#354. UI-Text laut Deep-Research: „Assets für EufyMake Studio vorbereiten“, nicht „fertiges Projekt erzeugen“. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | **Blocked (extern)** – Repo-Härtung über #322/#342 (geschlossen) erledigt; verbleibender Blocker ist die OpenAI-/Billing-Quota. Nach Quota-Fix den geplanten Scan einmal manuell anstoßen, dann schließen. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: Job-Level-Permission-Overrides im Reusable-WF berücksichtigen | 🟢 Niedrig | 🟡 Mittel | **Needs refinement** – erst die GitHub-Semantik (Top-Level vs. effektiv-per-Job) belegen; OIDC-Guard aus #303 darf nicht aufgeweicht werden. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF nicht als Eingabeformat unterstützt | 🟢 Niedrig | 🟢 Niedrig | **Ready for PR (Doku)** – Maintainer hat HEIC **bewusst ausgeschlossen** (Kommentar 2026-06-21). Nur noch README/ANLEITUNG klarstellen, dann schließen. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟢 Niedrig | **Ready for PR (opportunistisch)** – kein Produkt-/CI-Blocker; höchster Nutzen zuerst (Lasso-Endpunkt asserten, `test_helpers`-Zeile, `set_brush_size`-Tests konsolidieren). |

### Als Nächstes empfohlen (PR-Reihenfolge)

1. **#352** zuerst – Fundament des Epics, nach dem ADR-Refinement well-scoped;
   entsperrt #353/#354.
2. **#353** und **#354** parallel, sobald #352 steht.
3. **#355** als Abschluss des Epics.
4. **#339** (kleine Doku-PR) und **#299** (Test-Cleanup) als niedrig
   priorisierte Lückenfüller dazwischen.
5. **#318** zurückstellen, bis die GitHub-Permissions-Semantik belegt ist.
6. **#245** extern blockiert lassen (kein Repo-Patch bringt die Quota zurück).

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
