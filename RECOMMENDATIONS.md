**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-06-29)

Die laufende Codeanalyse-Liste ist leer. Ruff, mypy und die lokale Testsuite
bleiben die maßgebliche Baseline vor neuen PRs.

### Erledigt seit dem letzten Review

- **N1/N2/N4/N5/N6/N7/N8** sind erledigt: Fehlerpfade, Größenlimit,
  Dateiendungen, atomisches Speichern, CI-Qt-Pakete, Lazy-Import und Docstring.
- **O2/O3/O4/O5/O6** sind umgesetzt: Linux-Pakete, Release-Workflow,
  Vollmatrix, `ui_smoke` und plattformgerechte Werkzeug-Shortcuts.
- Ältere geschlossene Befunde (u. a. EufyMake-Epic **#351/#352–#355** und der rembg/ONNX-Subprozess **#270/#285/#286**) sind in den dokumentierten PRs erledigt, durch Tests/CI abgesichert und archiviert.

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
- **N12 ✅ — Kombinierte 2D-Vorschau (Epic #384) umgesetzt.** Qt-freie Relief-/
  Gloss-Renderer (#385/#386), explizite und aktive-Ebene-unabhängige Canvas-Modi
  mit begrenztem Cache (#387) sowie synchrones Ansicht-Menü/Vorschau-Panel mit
  Live-Stärke und Gloss-Schalter (#388); der #363-Exportvertrag bleibt durch die
  vollständige Modus×Layer-Testmatrix bitgenau geschützt. Das Review-Follow-up
  #397 (PR #398) führt transiente Farb-/Höhenvorschauen durch dieselbe Pipeline,
  respektiert ausgeblendete Datenrollen und überspringt Relief-Stärke 0 effizient.
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

## Offene GitHub-Issues – Triage-Stand (2026-06-29, aktualisiert)

Stand 2026-06-29 zeigt GitHub **7** offene Issues: **#245**, **#299**, **#318**,
**#389**, **#392**, **#404** und **#406**. Seit dem letzten Review (2026-06-25)
sind zwei neue, eng abgegrenzte Qualitäts-/Robustheits-Issues hinzugekommen: das
Dead-Code-Audit **#406** und die Preview-Degrade-Lücke **#404**. Die Doku-Pakete
**#390/#391**, der Öffnen-Hinweis **#357** sowie der dokumentierte HEIC-Ausschluss
**#339** bleiben geschlossen; im Roadmap-Epic **#389** verbleibt nur noch der
Release-Schritt **#392**.

**Kommentar-Durchsicht:** Keine neuen externen Kommentare. Die vorhandenen
Kommentare auf #392/#299/#245 sind Owner-Triage-Notizen, die mit dem aktuellen
Stand übereinstimmen – keine Issue-Aktualisierung nötig.

**Neue Befunde gegen den Code verifiziert:** #406 – `_derive_physical_size`
(`eufymake_export.py:217`) hat keinen Aufrufer (`parse_size_mm` nur dort, sonst
in `project_model.py` genutzt). #404 – `compose_relief`/`compose_gloss`
(`canvas.py:555/564`) werfen im Renderpfad, statt auf COLOR zu degradieren.

### Sinnvolle Bündelung

- **Release-Paket:** **#392** ist startbereit; nach Tag, Release-Body und
  verifizierten macOS-/Linux-Artefakten kann Epic **#389** schließen.
- **Qualitäts-Schnellschüsse:** **#406** und **#404** sind klein, eigenständig
  und ready-for-PR – ideal als kurze Quality-PRs neben dem Release-Pfad, aber
  getrennt davon (verschiedene Module, kein gemeinsamer Diff).
- **#299/#318/#245** nicht mit dem Release-Pfad mischen; sie sind unabhängige
  Qualitäts-, Forschungs- beziehungsweise externe Betriebsarbeit.

Bewertung: **Relevanz** = Bedeutung für Roadmap/Nutzer, **Komplexität** =
geschätzter Umsetzungsaufwand.

| # | Titel | Relevanz | Komplexität | Empfohlener nächster Schritt |
|---|-------|----------|-------------|------------------------------|
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Release v2.5.0 schneiden (CHANGELOG/Version/Tag/Artefakte) | 🟠 Hoch | 🟡 Mittel | **Startbereit** – #390, #391 und #384 sind geschlossen. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | [Epic] Nutzer-Doku aktualisieren & Release schneiden | 🟠 Hoch | 🟢 Niedrig (Rest) | **Fast abgeschlossen** – nur #392 ist noch offen. |
| [#404](https://github.com/NikolayDA/picture_helper/issues/404) | Vorschau-Render: Größen-Mismatch degradiert nicht auf COLOR | 🟡 Mittel | 🟢 Niedrig | **Ready for PR** – `compose_relief`/`compose_gloss` defensiv kapseln und bei Größen-Mismatch auf `base` zurückfallen, mit Render-/Pixel-Regressionstest. Latent, aber klar abgegrenzt. |
| [#406](https://github.com/NikolayDA/picture_helper/issues/406) | Dead-Code: ungenutzte `_derive_physical_size` in `eufymake_export.py` | 🟢 Niedrig | 🟢 Niedrig | **Ready for PR** – Funktion entfernen, `parse_size_mm`-Import bereinigen, CLAUDE.md-Geometriesatz auf den `_derive_target`/Projektmodell-Pfad anpassen. Trivial, vollständige Akzeptanzkriterien. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟢 Niedrig | **Nach v2.5.0** – dann höchste Wirkung zuerst (Lasso-Endpunkt, schreibbares NumPy-Ergebnis, Magic-Wand-Vollmaske, Brush-Parametrisierung). |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: Job-Level-Permission-Overrides im Reusable-WF berücksichtigen | 🟢 Niedrig | 🟡 Mittel | **Needs refinement** – GitHub-Semantik erst belegen; Code nur bei nachgewiesenem False Positive, OIDC-Guard #303 bewahren. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | **Blocked (extern)** – Repo-Härtung über #322/#342 (geschlossen) erledigt; verbleibender Blocker ist die OpenAI-/Billing-Quota. Nach Quota-Fix den geplanten Scan einmal manuell anstoßen, dann schließen. |

### Als Nächstes empfohlen (PR-Reihenfolge)

1. **#406** und **#404** als kurze Quality-PRs vorziehen – beide sind
   verifiziert, eigenständig und ready-for-PR (verschiedene Module, geringes
   Risiko).
2. **#392** ausführen und Epic **#389** schließen, sobald Tag, Release-Body und
   beide Artefakte verifiziert sind.
3. **#299** nach v2.5.0 angehen; **#318** nur erforschen (Needs refinement) und
   **#245** bis zur externen Quota-Wiederherstellung blockiert lassen.

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
