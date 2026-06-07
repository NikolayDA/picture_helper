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
- **#164/#167/#168** sind erledigt (PRs #172/#174/#173); die Restbefunde laufen
  fokussiert in #176/#178 weiter.
- **Am 2026-06-06 als sauber erledigt verifiziert** (PRs #188–#193, je mit
  Regressionstest, `make check` grün – 504 passed): **#163** (CHANGELOG-Links
  auf reale, auf GitHub auflösbare Commit-SHAs umgestellt; vier fehlende
  2.3.0-Features + idna/urllib3-Eintrag; echte Git-Tags bewusst nicht vergeben),
  **#165/#180** (TESTING.md: `addopts`-Filter, `ui_smoke`, Wochen-Schedule,
  shellcheck, `make coverage`), **#184** (Load-Generation +
  `content_revision`-Recheck gegen verspätete Async-Loads), **#182**
  (`PIP_CONSTRAINT` im AppImage-Build), **#183** (license-check read-only +
  isolierter Kommentar-Job), **#177** (Behavioral-Assertions + neues
  `tests/test_history_popup.py`).

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** Deutsch und Englisch sind in der App
  umschaltbar. Die vorhandenen Dokusprachen (es/fr/uk/zh) sind noch nicht als
  Runtime-Locales umgesetzt; bei Bedarf key-für-key in `bgremover.i18n`
  ergänzen und mit Paritäts-/Smoke-Tests absichern.

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-07)

Jetzt **sechs** offene Issues: ein 🟠-CI-Blocker (#195) sowie fünf 🟡/🟢: zwei
`documentation` (#161, #166), zwei `quality/testing` (#176, #178) und ein
Privacy-Security-Befund (#185). #163/#165/#177/#180 sowie die drei höher
priorisierten Security-Befunde des Codex-Scans `8c04b92` (#182/#183/#184) sind
seit dem letzten Review geschlossen und verifiziert.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#195](https://github.com/NikolayDA/picture_helper/issues/195) | Full-CI-Blocker (mypy/3.10): `canvas_selection.py` Shape-Typing – numpy-2.2.6-Stubs | 🟠 Hoch | 🟢 Niedrig | PR-bereit; `self._mask: npt.NDArray[np.bool_]` — verifizierter Einzeiler-Fix |
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Code-Review-Folge (Low): E741, check_untyped_defs, cancel_ai-UX, shutdown_all | 🟡 Mittel | 🟢 Niedrig | PR-bereit (aus #167); `E741`/`check_untyped_defs` in `pyproject.toml` noch unverändert |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README-Audit: ein fehlerhafter Link, eine interne Begrifflichkeit | 🟡 Mittel | 🟢 Niedrig | Teilweise erledigt: „Runde 5" entfernt; nur Clone-URL offen (Owner-Entscheidung) |
| [#185](https://github.com/NikolayDA/picture_helper/issues/185) | Security: macOS-Diagnose offenbart lokale Pfade + Roh-Log-Tail (Privacy) | 🟢 Niedrig | 🟡 Mittel | PR-bereit; `$HOME`/Pfade redaktieren + `--include-raw-logs`-Flag + Shell-Test |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Test-Audit-Folge (Low): private Internals entkoppeln + Doppeltests | 🟢 Niedrig | 🟡 Mittel | PR-bereit (aus #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Kommentar-Audit: Sprachinkonsistenz & kleine Ungenauigkeit | 🟢 Niedrig | 🟢 Niedrig | PR-bereit; englische Docstrings in `right_panel.py`/`main_window.py` |

### Empfohlene PR-Reihenfolge

1. **#195** — `self._mask: npt.NDArray[np.bool_]` in `canvas_selection.py`; Full-CI-Python-3.10-Zellen wieder grün.
2. **#176** — Code-Quality-Sammlung aus #167: `E741` eingrenzen, `check_untyped_defs` inkrementell, cancel_ai-UX, `shutdown_all`-Thread-Referenzen nullen.
3. **#185** — macOS-Diagnose redaktieren (`$HOME`/Pfade) + `--include-raw-logs`-Flag + Shell-Test.
4. **#178** — Tests von privaten Internals entkoppeln + Doppeltests reduzieren (aus #168).
5. **#166** — Docstring-Sprachbereinigung als kleinen Pflege-PR.
6. **#161 zurückgestellt** — „Runde 5" erledigt; offen bleibt nur die Klon-URL (Owner-Entscheidung zur Repo-Sichtbarkeit).

## Vorige Runden

- **2026-06-01, „modest-shannon" (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt bzw.
  verworfen, wo sie Fehlalarm war.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
