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

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** Deutsch und Englisch sind in der App
  umschaltbar. Die Dokusprachen es/fr/uk/zh sind noch keine Runtime-Locales;
  bei Bedarf key-für-key in `bgremover.i18n` ergänzen und mit Tests absichern.
- **O7 🟠 — Subprozess für rembg/ONNX (Folge aus #231, verfolgt in #270).**
  PR #267 begrenzt den Shutdown-Fallback, doch die nicht unterbrechbare
  KI-Arbeit läuft weiter im Thread mit `terminate()` als Notfall. Die
  vollständige Lösung verschiebt rembg/ONNX in einen Subprozess.

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-14, Abschluss-Triage)

Nach Abschluss der PRs **#263–#269** und der Schließung von **#261** (erledigt
durch PR #268) sind **5** Issues offen. Neun zuvor offene Issues — **#231, #234,
#248, #249, #257, #258, #259, #260** und **#261** — wurden über die gemergten
PRs geschlossen. Für den vertagten Architektur-Follow-up aus #231 (rembg/ONNX-
Subprozess, Roadmap **O7**) wurde **#270** neu eröffnet. Alle offenen Issues
wurden gegen den aktuellen Code verifiziert.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#270](https://github.com/NikolayDA/picture_helper/issues/270) | rembg/ONNX-Inferenz in einen Subprozess auslagern (Folge aus #231) | 🟠 Hoch | 🟡 Mittel | Eigener Architektur-PR: PR #267 begrenzte nur den Shutdown. rembg/ONNX in Subprozess auslagern, damit `terminate()` als KI-Notfall entfällt; Tests für Schließen/Cancel/blockierten Aufruf |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` lädt die vollständige PyQt6-GUI | 🟡 Mittel | 🟡 Mittel | Bereit für PR: öffentliche API per PEP-562-Lazy-Exports erhalten, Import-Regressionstest ergänzen. Code unverändert: `__init__.py:15-43` re-exportiert weiter die GUI |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | Quota account-seitig beheben; repo-seitig nur klare Fehlerbehandlung und optionaler Node-24-Bump, kein erzwungener `setup-node`-Fix |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo-Speicherlimit erfasst den Redo-Stack nicht | 🟢 Niedrig | 🟡 Mittel | Gemeinsames Undo/Redo-Budget; Original/Qt-Speicher nur messen. Code unverändert: `canvas_history.py` zählt nur `_undo_bytes`, Redo nur per `maxlen` |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: Clone-URL führt für anonyme Nutzer zu 404 | 🟢 Niedrig | 🟢 Niedrig | „Runde 5“ ist erledigt; für die Clone-Doku zuerst öffentlich vs. privat/invite-only entscheiden, dann ändern oder schließen |

### Empfohlene PR-Reihenfolge

1. **#232** — leichte Paketimporte über PEP-562-Lazy-Exports herstellen.
2. **#245** — Quota extern wiederherstellen; optionale Workflow-Härtung (Node 24) separat.
3. **#235** — gemeinsames Undo/Redo-Verlaufsbudget implementieren.
4. **#161** — Veröffentlichungsmodell entscheiden, dann Doku ändern oder schließen.
5. **#270** — rembg/ONNX-Subprozess als eigenen Architektur-PR planen (Folge aus #231).

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
