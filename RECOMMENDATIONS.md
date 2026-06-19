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

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-19)

Stand 2026-06-19 sind **4** Issues offen. Seit der Bewertung vom 2026-06-18
wurde die Test-/Release-Härtungs-Welle größtenteils gemerged: **#307, #308,
#309, #310** und **#312** sind **geschlossen** (ebenso das Snapshot-Meta-Issue
**#313**). Die drei Performance-Befunde **#277/#278/#279** (Wochen-Benchmark
#280) sind über die Benchmark-Härtung dieses PRs (Umgebungs-Fingerprint +
Median-Bestätigung; nur vergleichbare Baselines melden) **geschlossen**. Aus dem
Codex-Review zu PR **#317** (der #309/#310 schloss) entstand ein neuer
Folgebefund **#318** (Job-Level-Permission-Overrides im Reusable-Workflow-Guard).
Weiterhin offen sind **#311** (Release-Body), **#318** (Permission-Guard),
**#245** (CI-Quota, extern blockiert) und die niedrigpriore Test-Hygiene
**#299**. Aus der Triage von **#245** sind drei gebündelte repo-seitige
Härtungs-Folgeissues hervorgegangen — **#322** (Wartungs-/Skip-Pfad), **#323**
(Security-Issue-Sync-Tests) und **#324** (Prompt-Scope-Governance) —, die an
#245 hängen, bis die Quota account-seitig wiederhergestellt ist. Alle offenen
Issues wurden gegen den aktuellen Code verifiziert.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#311](https://github.com/NikolayDA/picture_helper/issues/311) | Release: Release-Body aus CHANGELOG füllen | 🟡 Mittel | 🟡 Mittel | **Ready for PR** – gut umrissen: v2.4.1-Body manuell nachtragen; `release-linux.yml` Notes aus `## [X.Y.Z]` ableiten statt hardcodiertem Text (auch beim Reuse), Regressionstest in `test_release_gate.py` |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: Job-Level-Permission-Overrides im Reusable-WF berücksichtigen | 🟡 Mittel | 🟡 Mittel | **Needs refinement** – zuerst GitHubs Startup-Validierungssemantik (Top-Level vs. effektiv-per-Job) belegen; aktuell rein theoretischer False-Positive (keine Job-Level-Overrides in `ci.yml`), OIDC-Guard #303 darf nicht schwächer werden |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | **Blockiert (extern):** Quota account-seitig wiederherstellen. Repo-seitige Härtung jetzt in **#322–#324** verfolgt (Wartungs-/Skip-Pfad, Sync-Tests, Prompt-Governance); der graceful skip entspricht #322 Variante B |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟢 Niedrig | Kein Korrektheitsfehler; höchster Nutzen zuerst (Endpunkt-Move, `set_brush_size` konsolidieren), Rest nach Bedarf |

### Bündelbare Issues

- **#318** ist der Folgebefund zum bereits gemergten Permission-Guard (#309/#310) und bleibt separat – er braucht zuerst eine belegte GitHub-Semantik, bevor `_required_permissions` angefasst wird.
- **#311** bleibt eigenständig, weil es Release-Workflow, CHANGELOG-Extraktion und bestehende Release-Notes berührt.
- **#299** ist opportunistische Test-Hygiene und sollte nur mitlaufen, wenn ein ohnehin berührter Test betroffen ist.

### Empfohlene PR-Reihenfolge

1. **#311** — Release-Body aus CHANGELOG ableiten und v2.4.1-Notes nachziehen; gut umrissen und nutzersichtbar (ausgelieferte Fixes sind sonst auf der Release-Seite unsichtbar).
2. **#318** — nach belegter GitHub-Semantik den Permission-Guard verfeinern, ohne den OIDC-Regressionsfall zu schwächen.
3. **#245** — Quota extern wiederherstellen; repo-seitige Härtung in **#322–#324** (Wartungs-/Skip-Pfad, Sync-Tests, Prompt-Governance) verfolgt.
4. **#299** — Test-Hygiene nach Bedarf.

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
