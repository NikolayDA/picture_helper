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
- Ältere geschlossene Befunde (**#163–#290**, u. a. EufyMake-Epic **#351/#352–#355**, rembg/ONNX-Subprozess **#270/#285/#286**) sind in den dokumentierten PRs erledigt, durch Tests/CI abgesichert und archiviert.

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

## Offene GitHub-Issues – Triage-Stand (2026-06-24, aktualisiert)

Stand 2026-06-24 zeigt GitHub **14** offene Issues. Das Epic **#375** (maßgenaue
mm/DPI-Ausgabe + allgemeine Exportprüfung) ist über **#376–#380** abgeschlossen
(PR #382/#383) und geschlossen. Seit der letzten Triage sind **zwei neue Epics**
hinzugekommen, die den Abschluss von Phase 0/1 strukturieren:

- **#384 – Kombinierte 2D-Vorschau** (Reliefkern-MVP, letzter offener
  Funktionspunkt von Phase 1, heute ~55 %) mit den Sub-Issues **#385**
  (Relief-Shading-Renderer, Qt-frei), **#386** (Gloss-Visualisierung, Qt-frei),
  **#387** (Canvas-Vorschaumodi + Komposit-Pipeline) und **#388** (UI-Toggles +
  i18n).
- **#389 – Nutzer-Doku aktualisieren & Release v2.5.0 schneiden** mit den
  Sub-Issues **#390** (Nutzerhandbuch ANLEITUNG, 6 Sprachen – schließt **#357**
  mit ab), **#391** (README + Screenshots + i18n) und **#392** (Release v2.5.0).

Daneben verbleiben die Doku-Lücken **#357** (jetzt von #390 abgedeckt) und
**#339** sowie die Test-/CI-Befunde **#318**, **#299** und **#245**.

**Kommentar-Durchsicht (2026-06-24):** Die Kommentare zu **#245**, **#299** und
**#339** stammen ausschließlich vom Maintainer (Triage) und bestätigen den
dokumentierten Stand: #245 bleibt extern über Quota/Billing blockiert, #299
bleibt niedrig priorisierte Test-Hygiene, #339 ist als bewusster HEIC-Ausschluss
bestätigt. Kein Kommentar erfordert eine inhaltliche Issue-Aktualisierung; neue
Folge-Issues sind nicht nötig.

Bewertung: **Relevanz** = Bedeutung für Roadmap/Nutzer, **Komplexität** =
geschätzter Umsetzungsaufwand.

| # | Titel | Relevanz | Komplexität | Empfohlener nächster Schritt |
|---|-------|----------|-------------|------------------------------|
| [#384](https://github.com/NikolayDA/picture_helper/issues/384) | [Epic] Kombinierte 2D-Vorschau (Farbe/Transparenz/Relief/Gloss) | 🟠 Hoch | 🔴 Hoch (Epic) | **In Arbeit (Epic)** – letzter Funktionspunkt von Phase 1. Reihenfolge: #385/#386 parallel → #387 → #388. |
| [#385](https://github.com/NikolayDA/picture_helper/issues/385) | Relief-Shading-Renderer (Qt-frei) | 🟠 Hoch | 🟡 Mittel | **✅ Ready for PR** – sauber abgegrenzt, keine Abhängigkeiten, Qt-frei + strikt getypt. Stärkster nächster PR; entsperrt #387. |
| [#386](https://github.com/NikolayDA/picture_helper/issues/386) | Gloss-Visualisierungs-Renderer (Qt-frei) | 🟡 Mittel | 🟢 Niedrig–Mittel | **✅ Ready for PR** – parallel zu #385, keine Abhängigkeiten; Qt-freie reine Bildlogik. |
| [#387](https://github.com/NikolayDA/picture_helper/issues/387) | Canvas: Vorschaumodi + Komposit-Pipeline | 🟠 Hoch | 🟠 Mittel–Hoch | **Blocked** – braucht #385 + #386; #363-Export-Vertrag per Regressionstest wahren. |
| [#388](https://github.com/NikolayDA/picture_helper/issues/388) | UI: Vorschaumodus-Auswahl + Relief-/Gloss-Toggles + i18n | 🟡 Mittel | 🟡 Mittel | **Blocked** – braucht #387; schließt Epic #384 ab. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | [Epic] Nutzer-Doku aktualisieren & Release schneiden | 🟠 Hoch | 🟡 Mittel (Epic) | **In Arbeit (Epic)** – #390/#391 parallel jetzt → (Epic #384 mergen) → #392. |
| [#390](https://github.com/NikolayDA/picture_helper/issues/390) | Nutzerhandbuch ANLEITUNG (+ 5 i18n) auf neue Features | 🟠 Hoch | 🔴 Hoch (L, 6 Sprachen) | **Ready for PR** – gut abgegrenzt, aber umfangreich; schließt **#357** mit ab. |
| [#391](https://github.com/NikolayDA/picture_helper/issues/391) | README + Screenshots + i18n aktualisieren | 🟡 Mittel–Hoch | 🟡 Mittel | **Ready for PR (mit Vorbehalt)** – Textanteil sofort umsetzbar; Screenshots brauchen einen aktuellen App-Lauf. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Release v2.5.0 schneiden (CHANGELOG/Version/Tag/Artefakte) | 🟠 Hoch | 🟡 Mittel | **Blocked** – braucht #390 + #391, idealerweise nach #384. |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Doku: Start-mit-Pfad/Finder-Öffnen fehlt in ANLEITUNG §4 | 🟢 Niedrig | 🟢 Niedrig | **In #390 zusammengeführt** – als kleine Einzel-PR weiterhin möglich, wird aber regulär mit #390 geschlossen. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF nicht als Eingabeformat unterstützt | 🟢 Niedrig | 🟢 Niedrig | **Ready for PR (Doku)** – HEIC bewusst ausgeschlossen (Kommentar 2026-06-21). Nur noch README/ANLEITUNG klarstellen, dann schließen. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟢 Niedrig | **Ready for PR (opportunistisch)** – kein Produkt-/CI-Blocker; höchster Nutzen zuerst (Lasso-Endpunkt asserten, `test_helpers`-Zeile, `set_brush_size`-Tests konsolidieren). |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: Job-Level-Permission-Overrides im Reusable-WF berücksichtigen | 🟢 Niedrig | 🟡 Mittel | **Needs refinement** – erst die GitHub-Semantik (Top-Level vs. effektiv-per-Job) belegen; OIDC-Guard aus #303 darf nicht aufgeweicht werden. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | **Blocked (extern)** – Repo-Härtung über #322/#342 (geschlossen) erledigt; verbleibender Blocker ist die OpenAI-/Billing-Quota. Nach Quota-Fix den geplanten Scan einmal manuell anstoßen, dann schließen. |

### Als Nächstes empfohlen (PR-Reihenfolge)

1. **#385** und **#386** (Qt-freie Relief-/Gloss-Renderer) als kleine,
   parallelisierbare PRs umsetzen – die besten „ready & well-scoped“-Kandidaten;
   sie entsperren #387.
2. **#387** → **#388** anschließen und damit Epic **#384** (kombinierte
   2D-Vorschau) abschließen; den #363-Export-Vertrag per Regressionstest wahren.
3. **#390** und **#391** parallel als Doku-PRs (schließt **#357** mit ab);
   **#339** als kleine Einzel-PR einstreuen.
4. **#392** (Release v2.5.0) erst nach #390/#391 und idealerweise nach #384.
5. **#299** opportunistisch bereinigen; **#318** bis zum Semantik-Beleg
   zurückstellen und **#245** extern blockiert lassen.

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
