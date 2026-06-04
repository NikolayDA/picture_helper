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

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** Deutsch und Englisch sind in der App
  umschaltbar. Die vorhandenen Dokusprachen (es/fr/uk/zh) sind noch nicht als
  Runtime-Locales umgesetzt; bei Bedarf key-für-key in `bgremover.i18n`
  ergänzen und mit Paritäts-/Smoke-Tests absichern.

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-04)

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#168](https://github.com/NikolayDA/picture_helper/issues/168) | Test-Suite-Audit: veraltete Tests, fehlende Assertions, private Kopplung, Coverage-Lücken | 🔴 Hoch | 🔴 Hoch | 🔴-Befunde in PR #173; Rest aufteilen & verfeinern |
| [#167](https://github.com/NikolayDA/picture_helper/issues/167) | Code-Review: Qualität, Wartbarkeit & kleinere Issues | 🔴 Hoch | 🟡 Mittel | Medium-Befunde (Race, TOCTOU) in PR #174; Low-Befunde bündeln |
| [#164](https://github.com/NikolayDA/picture_helper/issues/164) | Doc-Review: INSTALL_MAC.md & INSTALL_LINUX.md — 4 Issues | 🔴 Hoch | 🟢 Niedrig | PR #172 offen |
| [#163](https://github.com/NikolayDA/picture_helper/issues/163) | CHANGELOG.md: fehlerhafte Versionslinks + fehlende 2.3.0-Einträge | 🔴 Hoch | 🟡 Mittel | Inhaltsänderungen PR-bereit; Git-Tags brauchen Klärung |
| [#165](https://github.com/NikolayDA/picture_helper/issues/165) | TESTING.md: 3 Ungenauigkeiten gegenüber dem aktuellen Code | 🟡 Mittel | 🟢 Niedrig | PR-bereit |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README-Audit: ein fehlerhafter Link, eine interne Begrifflichkeit | 🟡 Mittel | 🟢 Niedrig | „Runde 5"-Fix PR-bereit; Clone-URL blockiert (Repo-Sichtbarkeit) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Kommentar-Audit: Sprachinkonsistenz & kleine Ungenauigkeit | 🟢 Niedrig | 🟢 Niedrig | PR-bereit |

### Empfohlene PR-Reihenfolge

1. **#164** — Install-Docs (Python-3.11-KI-Hinweis, Releases-Link + lokalisierte UI-Strings): umgesetzt in **PR #172** (alle sechs Sprachfassungen; Merge ausstehend).
2. **#168 🔴** — `test_canvas_events.py:174` (Locale-Assertion in CI bereits kaputt) und `test_async_load.py:34` (schwache OR-Assertion): umgesetzt in **PR #173** (Merge ausstehend; übrige #168-Befunde separat).
3. **#167 Medium** — Double-checked Lock in `_ensure_rembg_remove()` + TOCTOU-Fenster in `open_validated_image`: umgesetzt in **PR #174** (Merge ausstehend; Low-Befunde separat).
4. **#165** — TESTING.md-Korrekturen: risikoarm und gut abgegrenzt.
5. **#163 Inhalt** — Fehlende 2.3.0-Features + `[Unreleased]`-Einträge in CHANGELOG nachpflegen; Git-Tags separat klären.
6. **#161 teilweise** — „Runde 5" aus dem README-Architekturtext entfernen (Clone-URL erfordert Entscheidung über Repo-Sichtbarkeit).
7. **#166** — Docstring-Sprachbereinigung als kleinen Pflege-PR.

## Vorige Runden

- **2026-06-01, „modest-shannon" (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt bzw.
  verworfen, wo sie Fehlalarm war.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
