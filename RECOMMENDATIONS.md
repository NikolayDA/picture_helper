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

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** Deutsch und Englisch sind in der App
  umschaltbar. Die Dokusprachen es/fr/uk/zh sind noch keine Runtime-Locales;
  bei Bedarf key-für-key in `bgremover.i18n` ergänzen und mit Tests absichern.
- **O7 ✅ — Subprozess für rembg/ONNX erledigt (PR #283, Issue #270 geschlossen).**
  Die nicht unterbrechbare KI-Inferenz läuft jetzt in einem per `spawn`
  gestarteten Prozess (`ai_process.py`); `QThread.terminate()` als KI-Notausgang
  ist entfallen. Die Robustheits-/Speicher-Folgebefunde sind in **#285**
  (PR #289) behoben und geschlossen.

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-21)

Stand 2026-06-21 sind nach Prüfung der PRs von gestern und heute nur noch **4**
Roadmap-/Follow-up-Issues offen. Die Merge-Commits **#337**, **#338** und
**#340** schließen die gestern noch offenen Punkte **#326**, **#329–#335**,
**#323** und **#324** sauber ab: Der GIF-Ladepfad ist regressionsgetestet, das
Projekt-/Ebenen-Epic ist durchgängig von Domänenmodell bis UI/Integration
umgesetzt, und die Security-Scan-Tests decken Severity-Filter, Leerbefunde
sowie Prompt-Scope ab. Offene Restpunkte sind damit nur noch **#322**
(Wartungs-/Skip-Pfad für den geplanten Codex Security Scan), **#318**
(Permission-Guard-Semantik), **#245** (extern blockierte Quota) und **#299**
(Test-Hygiene).

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: Wartungs-/Skip-Pfad für geplanten Codex Security Scan | 🟡 Mittel | 🟡 Mittel | **Nächster repo-seitiger Schritt zu #245** – bewusst entscheiden, ob manueller Schalter, sichtbarer Auto-Graceful-Skip oder beides; Gate im `cadence`-Job, „disabled → skipped, nicht failed“, Least-Privilege wahren und statisch testen |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: Job-Level-Permission-Overrides im Reusable-WF berücksichtigen | 🟡 Mittel | 🟡 Mittel | **Needs refinement** – zuerst GitHubs Startup-Validierungssemantik (Top-Level vs. effektiv-per-Job) belegen; aktuell kein beobachteter Repo-Fehler, OIDC-Guard #303 darf nicht geschwächt werden |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | **Extern blockiert** – Quota account-seitig wiederherstellen; repo-seitig sind #323/#324 erledigt, #322 bleibt als Wartungs-/Skip-Härtung offen |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟢 Niedrig | Kein Korrektheitsfehler; opportunistisch verbessern, wenn ohnehin Tests berührt werden (höchster Nutzen: Endpunkt-Move, `set_brush_size` konsolidieren) |

### Bündelbare Issues

- **#322** kann als alleinstehender CI-Härtungs-PR umgesetzt werden und ergänzt
  die bereits erledigten #323/#324.
- **#318** bleibt separat, weil vor einer Codeänderung die GitHub-Semantik
  dokumentiert werden muss.
- **#299** sollte nur mitlaufen, wenn ein betroffener Test ohnehin angefasst wird.

### Empfohlene PR-Reihenfolge

1. **#322** — letzter repo-seitiger #245-Follow-up mit direktem Betriebsnutzen.
2. **#318** — Permission-Guard nach belegter Semantik verfeinern, ohne den
   OIDC-Regressionsfall zu schwächen.
3. **#245** — Quota account-seitig wiederherstellen (extern blockiert).
4. **#299** — Test-Hygiene nach Bedarf.

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
