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

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** Deutsch und Englisch sind in der App
  umschaltbar. Die Dokusprachen es/fr/uk/zh sind noch keine Runtime-Locales;
  bei Bedarf key-für-key in `bgremover.i18n` ergänzen und mit Tests absichern.
- **O7 ✅ — Subprozess für rembg/ONNX erledigt (PR #283, Issue #270 geschlossen).**
  Die nicht unterbrechbare KI-Inferenz läuft jetzt in einem per `spawn`
  gestarteten Prozess (`ai_process.py`); `QThread.terminate()` als KI-Notausgang
  ist entfallen. Die Robustheits-/Speicher-Folgebefunde sind in **#285**
  (PR #289) behoben und geschlossen.

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-18)

Stand 2026-06-18 sind **12** Issues offen. Seit der letzten Bewertung
(2026-06-15) wurde **#161** (README-Clone-URL) am 2026-06-17 **geschlossen**;
zugleich kam mit dem v2.4.x-Release-Zyklus eine Welle von Test-/Release-
Härtungs-Issues hinzu (**#299, #307–#312**); **#313** trackt den
Recommendations-Snapshot selbst. Weiterhin offen sind die drei Performance-
Befunde **#277/#278/#279** (Wochen-Benchmark #280, laut Owner-Triage **noch
nicht** als Code-Regression bestätigt) und **#245** (CI-Quota, extern blockiert).
Alle offenen Issues wurden gegen den aktuellen Code verifiziert.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#313](https://github.com/NikolayDA/picture_helper/issues/313) | Docs: RECOMMENDATIONS-Issue-Snapshot aktualisieren | 🟡 Mittel | 🟢 Niedrig | Meta-Issue zum Snapshot: mit diesem Update abgleichen und danach schließen; sonst zählt es sich selbst als 12. offenes Issue mit |
| [#312](https://github.com/NikolayDA/picture_helper/issues/312) | CI: node20-Actions auf Node 24 anheben | 🟠 Hoch | 🟢 Niedrig | GitHub erzwingt Node 24 bereits per Warnung; betroffene Actions (`github-script`, `upload/download-artifact`) einheitlich auf node24-Majors heben, optional Guard-Test |
| [#311](https://github.com/NikolayDA/picture_helper/issues/311) | Release: Release-Body aus CHANGELOG füllen | 🟡 Mittel | 🟡 Mittel | v2.4.1-Body manuell nachtragen; `release-linux.yml` Notes aus `## [X.Y.Z]` ableiten statt hardcodiertem Text – auch beim Reuse |
| [#310](https://github.com/NikolayDA/picture_helper/issues/310) | Test: LICENSES.md-Version == pyproject | 🟡 Mittel | 🟢 Niedrig | Schneller Pytest, der die Titelversion gegen `[project].version` prüft – fängt Bump-Drift vor dem schweren License-Check |
| [#309](https://github.com/NikolayDA/picture_helper/issues/309) | Test: Reusable-WF-Permissions abdecken | 🟡 Mittel | 🟢 Niedrig | `test_release_gate.py` verallgemeinern: Caller-Job muss jede Permission des aufgerufenen Workflows gewähren (OIDC `id-token: write`) |
| [#308](https://github.com/NikolayDA/picture_helper/issues/308) | Test: KI-Kette im `--ai`-Artefakt importierbar | 🟠 Hoch | 🟡 Mittel | Netzfreier Spawn-Selbsttest im `--ai`-Build, der `rembg`+`pymatting`-Metadaten lädt (Regression #306) |
| [#307](https://github.com/NikolayDA/picture_helper/issues/307) | Test: gebautes Artefakt headless starten | 🟠 Hoch | 🟡 Mittel | Bundle im build-Job headless starten (Start-Crash #304 / Fork-Bomb #305 fangen); `publish` bleibt per `needs: build` gegated |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟢 Niedrig | Kein Korrektheitsfehler; höchster Nutzen zuerst (Endpunkt-Move, `set_brush_size` konsolidieren), Rest nach Bedarf |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | Performance-Regression: JPEG (+38.4%) | 🟡 Mittel | 🟡 Mittel | Noch nicht als Code-Regression bestätigt. Benchmark um Umgebungs-Fingerprint + Bestätigungsläufe (Median) erweitern; mit #278/#279 bündeln |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | Performance-Regression: TIFF (+21.8%) | 🟡 Mittel | 🟡 Mittel | Wie #277: gemeinsame Benchmark-Härtung; den Encode-Pfad (`save_image_file`) erst nach einem kompatiblen Bestätigungslauf untersuchen |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | Performance-Regression: WebP (+13.7%) | 🟡 Mittel | 🟡 Mittel | Wie #277/#278: ein gemeinsamer PR für Fingerprint + Median-Bestätigung; nur bestätigte Regressionen melden |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | Blockiert (extern): Quota account-seitig wiederherstellen. Repo-seitig nur klare Fehlerbehandlung (graceful skip) + optionaler Node-24-Bump |

### Bündelbare Issues

- **#307/#308** gehören zusammen: ein Release-Artifact-Verification-PR kann GUI- und `--ai`-Bundles headless starten und den KI-Spawn-Selfcheck ergänzen.
- **#309/#310** sind kleine Guard-Tests und können in einem Test-Härtungs-PR landen; **#311** bleibt besser separat, weil es Release-Workflow, CHANGELOG-Extraktion und bestehende Release-Notes berührt.
- **#277/#278/#279** sollten gemeinsam als Benchmark-Zuverlässigkeits-PR umgesetzt werden; erst danach lohnt die Format-spezifische Encode-Analyse.
- **#312** ist ein eigener CI-Modernisierungs-PR über alle Workflows; der Node-24-Anteil aus **#245** kann dort mitlaufen, die OpenAI-Quota selbst bleibt extern.
- **#299** ist opportunistische Test-Hygiene und sollte nur mitlaufen, wenn ein ohnehin berührter Test betroffen ist.

### Empfohlene PR-Reihenfolge

1. **#313** — diesen Snapshot aktualisieren und das Meta-Issue schließen, damit die Zählung nicht dauerhaft selbstreferenziell bleibt.
2. **#307/#308** — Release-Bundles headless smoke-testen (GUI + `--ai`); verhindert erneut ausgelieferte Start-Crashes/Fork-Bombs.
3. **#312** — node20-Actions auf Node 24 heben, bevor GitHub den Fallback entfernt.
4. **#309/#310** — generische Workflow-Permissions und LICENSES-Version als schneller Test-Härtungs-PR.
5. **#311** — Release-Body aus CHANGELOG ableiten und v2.4.1-Notes nachziehen.
6. **#277/#278/#279** — gemeinsamer Benchmark-Fingerprint + Median-Bestätigung; Regression nur bei kompatibler Baseline melden.
7. **#245** — Quota extern wiederherstellen; repo-seitig danach nur klare Fehlerbehandlung.
8. **#299** — Test-Hygiene nach Bedarf.

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
