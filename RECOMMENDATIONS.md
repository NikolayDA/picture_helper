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

Die laufende Codeanalyse-Liste ist leer. Die zuletzt dokumentierte Folgeprüfung
ist umgesetzt und durch Tests abgesichert; Ruff, mypy und die lokale Suite
bleiben die maßgebliche Baseline vor neuen PRs.

### Erledigt seit dem letzten Review

- **N1/N2/N4/N5/N6/N7/N8** sind erledigt: Zauberstab-Fehlerpfad,
  Rotationsgrößenlimit, ehrliche Dateiendungen, atomisches Speichern,
  CI-Qt-Pakete, Lazy-Import von `rembg` und der `load_image`-Docstring.
- **O2/O3/O4/O5/O6** sind umgesetzt: Linux-AppImage/`.deb`, Release-Workflow,
  wöchentliche Vollmatrix, `ui_smoke` in PR/Full-CI sowie Werkzeug-Shortcuts
  mit plattformgerechten Hinweisen.
- **#164** ist umgesetzt und gemerged (PR #172): Python-3.11-KI-Hinweis,
  Releases-Link und lokalisierte UI-Strings in den Install-Guides.
- **#167 / #168** sind geschlossen: die High-/Medium-Befunde wurden via PR
  #173/#174 ausgeliefert; die übrigen Befunde laufen fokussiert in
  #176/#177/#178 weiter.

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** Deutsch und Englisch sind in der App
  umschaltbar. Die vorhandenen Dokusprachen (es/fr/uk/zh) sind noch nicht als
  Runtime-Locales umgesetzt; bei Bedarf key-für-key in `bgremover.i18n`
  ergänzen und mit Paritäts-/Smoke-Tests absichern.

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-05)

8 offene Issues, ausschließlich `documentation` und `quality/testing`. Keine
offenen Code-Fehler (🔴): die kritischen Befunde aus #167/#168 sind via
#173/#174 ausgeliefert; was bleibt, sind Doku-Korrekturen und Test-Härtung.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#163](https://github.com/NikolayDA/picture_helper/issues/163) | CHANGELOG.md: fehlerhafte Versionslinks + fehlende 2.3.0-Einträge | 🔴 Hoch | 🟡 Mittel | Inhaltsänderungen PR-bereit; Git-Tags brauchen Klärung |
| [#177](https://github.com/NikolayDA/picture_helper/issues/177) | Test-Audit-Folge (Medium): Behavioral-Assertions + Coverage-Lücken | 🟠 Hoch | 🟡 Mittel | PR-bereit (aus #168); Kommentar 2026-06-05 ergänzt `history_popup.py` (35 % Coverage) |
| [#165](https://github.com/NikolayDA/picture_helper/issues/165) | TESTING.md: 3 Ungenauigkeiten gegenüber dem aktuellen Code | 🟡 Mittel | 🟢 Niedrig | PR-bereit; mit #180 bündeln |
| [#180](https://github.com/NikolayDA/picture_helper/issues/180) | TESTING.md: 2 Ungenauigkeiten (addopts-Filter, fehlende coverage-Zeile) | 🟡 Mittel | 🟢 Niedrig | PR-bereit; überschneidet sich mit #165 (addopts) – gemeinsam erledigen |
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Code-Review-Folge (Low): E741, check_untyped_defs, cancel_ai-UX, shutdown_all | 🟡 Mittel | 🟢 Niedrig | PR-bereit (aus #167) |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README-Audit: ein fehlerhafter Link, eine interne Begrifflichkeit | 🟡 Mittel | 🟢 Niedrig | Teilweise blockiert: „Runde 5" erledigt; Clone-URL zurückgestellt (Owner-Entscheidung) |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Test-Audit-Folge (Low): private Internals entkoppeln + Doppeltests | 🟢 Niedrig | 🟡 Mittel | PR-bereit (aus #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Kommentar-Audit: Sprachinkonsistenz & kleine Ungenauigkeit | 🟢 Niedrig | 🟢 Niedrig | PR-bereit |

### Empfohlene PR-Reihenfolge

1. **#165 + #180** — TESTING.md-Korrekturen gebündelt (beide betreffen den `addopts`-Filter): risikoarm und gut abgegrenzt.
2. **#163 Inhalt** — Fehlende 2.3.0-Features + `[Unreleased]`-Einträge in CHANGELOG nachpflegen; Git-Tags separat klären.
3. **#177** — Test-Härtung: Behavioral-Assertions ergänzen + Coverage-Lücken schließen, inkl. `history_popup.py` (aus #168).
4. **#176** — Code-Quality-Sammlung aus #167: E741, check_untyped_defs, cancel_ai-UX, shutdown_all.
5. **#178** — Tests von privaten Internals entkoppeln + Doppeltests reduzieren (aus #168).
6. **#166** — Docstring-Sprachbereinigung als kleinen Pflege-PR.
7. **#161 zurückgestellt** — „Runde 5" erledigt; offen bleibt nur die Klon-URL (Owner-Entscheidung zur Repo-Sichtbarkeit).

## Vorige Runden

- **2026-06-01, „modest-shannon" (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt bzw.
  verworfen, wo sie Fehlalarm war.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
