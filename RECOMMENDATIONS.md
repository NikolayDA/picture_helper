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

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-20)

Stand 2026-06-20 sind **14** Issues offen. Seit der Bewertung vom 2026-06-19
wurde **#311** (Release-Body) geschlossen. Neu hinzugekommen ist das Epic
**#329** (Projekt-/Ebenen-Datenmodell – Fundament für Height Map, Gloss &
EufyMake-Export) mit seinen sechs Sub-Issues **#330–#335**, sowie der
Test-Coverage-Befund **#326** (GIF-Eingabeformat deklariert, aber ungetestet).
Das Ebenen-Epic ist der priorisierte Roadmap-Rang #1: **#330** (Qt-freies
Domänenmodell) ist die abhängigkeitsfreie Keystone und sofort umsetzbar, die
übrigen Sub-Issues sind über die Abhängigkeitskette
(#330 → #331 → #332/#333 → #334 → #335) blockiert. Weiterhin offen aus der
vorigen Runde: **#318** (Permission-Guard), **#245** (CI-Quota, extern
blockiert), die drei **#245**-Härtungsfolgen **#322–#324** und die niedrigpriore
Test-Hygiene **#299**. Alle offenen Issues wurden gegen den aktuellen Code
verifiziert.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#329](https://github.com/NikolayDA/picture_helper/issues/329) | [Epic] Projekt-/Ebenen-Datenmodell (Fundament Height Map/Gloss/EufyMake) | 🟠 Hoch | 🟠 Hoch | **Epic / Tracking** – Roadmap-Rang #1; über die sechs Sub-Issues abarbeiten, kein eigener PR |
| [#330](https://github.com/NikolayDA/picture_helper/issues/330) | Domänenmodell `Project` + `Layer` (Qt-frei) | 🟠 Hoch | 🟡 Mittel | **Ready for PR** – abhängigkeitsfreie Keystone; Qt-frei, strikt getypt, Komposit/Rollen, `tests/test_project_model.py`. Startpunkt des Epics |
| [#331](https://github.com/NikolayDA/picture_helper/issues/331) | Undo/Redo projektweit (ebenenbewusste Historie) | 🟠 Hoch | 🟠 Hoch | **Blockiert von #330** – ebenenbewusste Historie, isoliert testbar vor der Canvas-Verdrahtung |
| [#332](https://github.com/NikolayDA/picture_helper/issues/332) | Canvas: Komposit-Rendering + aktive Ebene | 🟠 Hoch | 🟠 Hoch | **Blockiert von #330/#331** – größter Brocken; Verhaltenswechsel auf ebenenbasiert, Einzel-Ebenen-Parität |
| [#333](https://github.com/NikolayDA/picture_helper/issues/333) | Projektdatei-Format: Speichern/Laden (versioniert, atomar, validiert) | 🟠 Hoch | 🟠 Hoch | **Blockiert von #330** (parallel zu #332) – `.bgrproj` ZIP-Container, atomar/validiert/versioniert |
| [#334](https://github.com/NikolayDA/picture_helper/issues/334) | UI: Ebenen-Panel + Projekt-Menü + i18n | 🟠 Hoch | 🟠 Hoch | **Blockiert von #330/#332/#333** – Panel + Menüaktionen, i18n de/en in Parität |
| [#335](https://github.com/NikolayDA/picture_helper/issues/335) | Migration & Integration (Bild→Projekt, Recent, Settings, Export) | 🟠 Hoch | 🟡 Mittel | **Blockiert von #330/#332/#333/#334** – Abschluss-Issue des Epics; Regressionsfreiheit der bestehenden Flüsse |
| [#326](https://github.com/NikolayDA/picture_helper/issues/326) | Tests: GIF-Eingabeformat ist deklariert, aber ungetestet | 🟡 Mittel | 🟢 Niedrig | **Ready for PR, sofort umsetzbar** – ein Lade-Test via `ImageLoadWorker` sichert das `_ALLOWED_IMAGE_FORMATS`-Gate für GIF; kein Save/Export |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: Job-Level-Permission-Overrides im Reusable-WF berücksichtigen | 🟡 Mittel | 🟡 Mittel | **Needs refinement** – zuerst GitHubs Startup-Validierungssemantik (Top-Level vs. effektiv-per-Job) belegen; aktuell rein theoretischer False-Positive (keine Job-Level-Overrides in `ci.yml`), OIDC-Guard #303 darf nicht schwächer werden |
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: Wartungs-/Skip-Pfad für geplanten Codex Security Scan | 🟡 Mittel | 🟡 Mittel | **#245-Folge** – Scope-Entscheidung manueller Schalter vs. sichtbarer Auto-Graceful-Skip (vs. beides); Gate im `cadence`-Job, „disabled → skipped, nicht failed", Least-Privilege wahren (kein `issues: write` im Scan-Job), statischer Test |
| [#323](https://github.com/NikolayDA/picture_helper/issues/323) | Tests: Security-Issue-Sync für Severity-Filter und leere Findings absichern | 🟢 Niedrig | 🟢 Niedrig | **#245-Folge, sofort umsetzbar** – Regressionstests für `reportable: false`, Severity-Schwelle und „No reportable findings"; netzunabhängig via `--dry-run`/Direktaufruf |
| [#324](https://github.com/NikolayDA/picture_helper/issues/324) | Security: Doc-Governance-Test für Codex-Scan-Prompt gegen Repo-Scope | 🟢 Niedrig | 🟢 Niedrig | **#245-Folge, sofort umsetzbar** – statischer Test, dass der Prompt die aktuellen Top-Level-Security-Flächen nennt; ergänzt die bestehenden Prompt-Assertions |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟢 Niedrig | Kein Korrektheitsfehler; höchster Nutzen zuerst (Endpunkt-Move, `set_brush_size` konsolidieren), Rest nach Bedarf |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | 🟡 Mittel | 🟢 Niedrig | **Blockiert (extern):** Quota account-seitig wiederherstellen. Repo-seitige Härtung in **#322–#324** verfolgt; der graceful skip entspricht #322 Variante B |

### Bündelbare Issues

- Das Ebenen-Epic **#329** wird über seine Sub-Issues in der vorgegebenen Reihenfolge abgearbeitet; **#332** und **#333** sind nach #330 parallelisierbar.
- **#323/#324** (beide #245-Folgen, netzunabhängige statische Security-Scan-Tests) lassen sich in einem PR bündeln.
- **#318** bleibt separat – es braucht zuerst eine belegte GitHub-Semantik, bevor `_required_permissions` angefasst wird.
- **#299** ist opportunistische Test-Hygiene und sollte nur mitlaufen, wenn ein ohnehin berührter Test betroffen ist.

### Empfohlene PR-Reihenfolge

1. **#330** — abhängigkeitsfreie Keystone des Ebenen-Epics; schaltet #331/#332/#333 frei.
2. **#326** — schneller, gut umrissener Quick-Win (GIF-Lade-Test), schließt eine Coverage-Lücke.
3. **#323 / #324** — netzunabhängige Security-Scan-Härtung, jederzeit umsetzbar.
4. **#331 → #332 / #333 → #334 → #335** — Ebenen-Epic entlang der Abhängigkeitskette.
5. **#322** — Wartungs-/Skip-Pfad nach bewusster auto/manuell-Entscheidung (#245-Folge).
6. **#318** — Permission-Guard nach belegter GitHub-Semantik verfeinern, ohne den OIDC-Regressionsfall zu schwächen.
7. **#245** — Quota account-seitig wiederherstellen (extern blockiert).
8. **#299** — Test-Hygiene nach Bedarf.

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
