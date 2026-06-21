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

## Offene GitHub-Issues – Triage-Stand (2026-06-21)

Stand 2026-06-21 zeigt GitHub noch **5** offene Issues: **#245**, **#299**,
**#318**, **#322** und **#339**. Die zuvor noch gelisteten
Projekt-/Ebenen- und Security-Test-Issues **#323**, **#324**, **#326** und
**#329–#335** sind in den Merge-Commits **#337**, **#338** und **#340**
inhaltlich erledigt und nicht mehr offen. Für **#322** existiert inzwischen
zusätzlich **#342**; der Issue sollte nach Merge-Verifikation kommentiert und
geschlossen werden.

| # | Titel | Labels/Status-Empfehlung | Kommentar-/Status-Vorschlag |
|---|-------|--------------------------|------------------------------|
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan scheitert an „Quota exceeded“ | `security`; **offen lassen / blocked external** | Kommentar ergänzen: Repo-seitige Härtungen sind mit #323/#324 und #322/#342 abgedeckt; verbleibender Blocker ist die OpenAI-/Billing-Quota. Nach Quota-Fix einmal den geplanten Scan manuell anstoßen und dann schließen. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | `quality`, `testing`; **offen / low priority** | Kommentar ergänzen: Kein Produkt-/CI-Blocker; als opportunistischer Cleanup bündeln, sobald betroffene Tests ohnehin geändert werden. Keine Statusänderung nötig. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: Job-Level-Permission-Overrides im Reusable-WF berücksichtigen | `enhancement`, `testing`; **needs refinement** | Kommentar ergänzen: Vor einer Codeänderung GitHub-Semantik für Top-Level- vs. Job-Level-Permissions im aufgerufenen Workflow belegen; OIDC-Guard aus #303 darf nicht aufgeweicht werden. |
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: Wartungs-/Skip-Pfad für geplanten Codex Security Scan | `security`; **nach #342 schließen** | Kommentar ergänzen: #342 implementiert den konservativen manuellen Wartungsschalter (`CODEX_SECURITY_SCAN_ENABLED=false`) inklusive Skip-Output und Regressionstests; nach verifiziertem Merge als erledigt schließen. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF nicht als Eingabeformat unterstützt | **Labels ergänzen:** `enhancement`, `documentation` (oder `question`, falls vorhanden); **needs decision** | Kommentar ergänzen: Produktentscheidung treffen – entweder HEIC bewusst nicht unterstützen und README/ANLEITUNG klarstellen, oder optionales `pillow-heif`/`HEIF`-Allowlist + Lade-Test planen. Bis zur Entscheidung offen lassen. |

### Empfohlene Issue-Aktionen

1. **#322** kommentieren und schließen, sobald der Merge von #342 auf `main`
   verifiziert ist.
2. **#339** labeln und mit einer expliziten Produktentscheidung versehen
   (Doku-Klarstellung vs. HEIC-Feature).
3. **#245** weiter offen halten, aber als extern blockiert markieren; #322/#342
   dort als abgeschlossenen Repo-Teil verlinken.
4. **#318** nicht sofort umsetzen, sondern zunächst die GitHub-Permissions-
   Semantik dokumentieren.
5. **#299** als niedrig priorisierten Test-Cleanup offen lassen.

## Vorige Runden

- **2026-06-01, „modest-shannon“ (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer“ (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
