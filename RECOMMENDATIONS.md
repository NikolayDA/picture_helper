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

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-09)

Jetzt **dreizehn** offene Issues. Neu ist ein `pip-audit`-Security-Batch vom
2026-06-07 (#200–#206) sowie ein Dead-Code-Befund (#199); #195 ist seit dem
letzten Review geschlossen und verifiziert.

Einordnung des Security-Batches gegen den tatsächlichen Projektstand
(`requirements/constraints.txt` + `pyproject.toml`):

- **#200 (setuptools) ist der einzige 🟠-Befund** — `setuptools>=61` ist eine
  **direkte Build-Abhängigkeit** (`pyproject.toml`) und in `constraints.txt`
  **nicht** gepinnt. CRITICAL RCE.
- **#201 (wheel)/#202 (pip)** sind real umsetzbar: `wheel` ist nicht gepinnt,
  `pip` wird in CI/Dev unkontrolliert mitgeliefert.
- **#203 (cryptography)/#204 (pyjwt)** sind **keine** Projekt-Abhängigkeiten
  (rein transitiv/systemseitig) → informativ, keine `constraints.txt`-Änderung.
- **#205 (urllib3)/#206 (idna)** sind im Projekt **bereits sauber gepinnt**
  (`urllib3==2.7.0`, `idna==3.15`); reiner System-Befund → schließbar.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#200](https://github.com/NikolayDA/picture_helper/issues/200) | setuptools 68.1.2 — CRITICAL/HIGH: RCE + Path-Traversal | 🟠 Hoch | 🟢 Niedrig | PR-bereit; direkte Build-Abhängigkeit — `setuptools>=78.1.1` in `pyproject.toml` + `constraints.txt` pinnen |
| [#201](https://github.com/NikolayDA/picture_helper/issues/201) | wheel 0.42.0 — HIGH: Path-Traversal (Dateirechte) | 🟡 Mittel | 🟢 Niedrig | PR-bereit; `wheel==0.46.2` in `constraints.txt` pinnen (mit #200 bündeln) |
| [#202](https://github.com/NikolayDA/picture_helper/issues/202) | pip 24.0 — HIGH/MEDIUM: 5 CVEs (Path-Traversal, Symlink) | 🟡 Mittel | 🟢 Niedrig | PR-bereit; `pip>=26.1.2` in CI-Setup-Schritten + Dev-Doku |
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Code-Review-Folge (Low): E741, check_untyped_defs, cancel_ai-UX, shutdown_all | 🟡 Mittel | 🟢 Niedrig | PR-bereit (aus #167); `E741`/`check_untyped_defs` in `pyproject.toml` noch unverändert |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README-Audit: ein fehlerhafter Link, eine interne Begrifflichkeit | 🟡 Mittel | 🟢 Niedrig | Blockiert: „Runde 5" entfernt; nur Clone-URL offen (Owner-Entscheidung zur Repo-Sichtbarkeit) |
| [#199](https://github.com/NikolayDA/picture_helper/issues/199) | Dead-Code (Low): write-only `_redo_max` in `canvas_history.py` | 🟢 Niedrig | 🟢 Niedrig | PR-bereit; eine Zeile entfernen (Modul ist streng getypt — `make check`) |
| [#185](https://github.com/NikolayDA/picture_helper/issues/185) | Security: macOS-Diagnose offenbart lokale Pfade + Roh-Log-Tail (Privacy) | 🟢 Niedrig | 🟡 Mittel | PR-bereit; `$HOME`/Pfade redaktieren + `--include-raw-logs`-Flag + Shell-Test |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Test-Audit-Folge (Low): private Internals entkoppeln + Doppeltests | 🟢 Niedrig | 🟡 Mittel | PR-bereit (aus #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Kommentar-Audit: Sprachinkonsistenz & kleine Ungenauigkeit | 🟢 Niedrig | 🟢 Niedrig | PR-bereit; englische Docstrings in `right_panel.py`/`main_window.py` |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — HIGH/MEDIUM: 6 CVEs | 🟢 Niedrig | 🟢 Niedrig | Keine Projekt-Abhängigkeit (transitiv/systemseitig) → informativ, keine `constraints.txt`-Änderung |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — HIGH/MEDIUM: 5 CVEs | 🟢 Niedrig | 🟢 Niedrig | Keine Projekt-Abhängigkeit → informativ, keine Projekt-Aktion |
| [#205](https://github.com/NikolayDA/picture_helper/issues/205) | urllib3 2.6.3 — MEDIUM: 2 CVEs | 🟢 Niedrig | 🟢 Niedrig | Keine Aktion; Projekt pinnt bereits `urllib3==2.7.0` (sauber) → schließbar |
| [#206](https://github.com/NikolayDA/picture_helper/issues/206) | idna 3.11 — MEDIUM: DoS via `idna.encode()` | 🟢 Niedrig | 🟢 Niedrig | Keine Aktion; Projekt pinnt bereits `idna==3.15` (sauber) → schließbar |

### Empfohlene PR-Reihenfolge

1. **#200** — `setuptools>=78.1.1` in `pyproject.toml` (`[build-system]`) **und** `constraints.txt` pinnen. Höchste Priorität: CRITICAL RCE in einer direkten Build-Abhängigkeit.
2. **#201** — `wheel==0.46.2` in `constraints.txt` pinnen; als gemeinsamen Supply-Chain-Pinning-PR mit #200 bündeln.
3. **#202** — `pip>=26.1.2` in den CI-Setup-Schritten + Dev-Install-Doku erzwingen.
4. **#176** — Code-Quality-Sammlung aus #167: `E741` eingrenzen, `check_untyped_defs` inkrementell, cancel_ai-UX, `shutdown_all`-Thread-Referenzen nullen.
5. **#199** — write-only `_redo_max` aus `canvas_history.py` entfernen (Trivial-Fix, Regressionstest via `make check`).
6. **#166** — Docstring-Sprachbereinigung als kleinen Pflege-PR.
7. **#185** — macOS-Diagnose redaktieren (`$HOME`/Pfade) + `--include-raw-logs`-Flag + Shell-Test.
8. **#178** — Tests von privaten Internals entkoppeln + Doppeltests reduzieren (aus #168).
9. **#205/#206 schließbar** — Projekt-Pinning bereits korrekt (`urllib3==2.7.0`, `idna==3.15`); reine System-Befunde.
10. **#203/#204 als Beobachtungsposten** — keine Projekt-Abhängigkeiten; erst pinnen, falls ein künftiges Feature sie direkt einzieht.
11. **#161 zurückgestellt** — „Runde 5" erledigt; offen bleibt nur die Klon-URL (Owner-Entscheidung zur Repo-Sichtbarkeit).

## Vorige Runden

- **2026-06-01, „modest-shannon" (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt bzw.
  verworfen, wo sie Fehlalarm war.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
