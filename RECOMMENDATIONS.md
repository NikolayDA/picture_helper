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
- **#164/#167/#168** sind erledigt (PRs #172/#174/#173); die Restbefunde sind
  über #176/#178 inzwischen ebenfalls abgeschlossen.
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

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-11)

Jetzt **fünf** offene Issues: die Beobachtungsposten #203/#204, das
zurückgestellte #161 sowie die Doku-Befunde #218 (CHANGELOG-Lücken) und
#226 (INSTALL-Review). **#176 ist erledigt** (Code-Quality-Sammlung via
PRs #198/#214, Issue geschlossen); zuvor #166/#178/#185 (PRs #219–#221),
#205/#206 (PR #222) und #199/#200/#201/#202 (PRs #215/#209/#211). Vom
`pip-audit`-Batch vom 2026-06-07 (#200–#206) bleiben nur die
Beobachtungsposten #203/#204 offen; #195 bleibt geschlossen und verifiziert.

Einordnung des Security-Batches gegen den tatsächlichen Projektstand
(`requirements/constraints.txt` + `pyproject.toml`):

- **#200/#201 sind erledigt (PR #209)** — `setuptools` ist jetzt in
  `pyproject.toml` (`[build-system]`) und `constraints.txt` auf `>=78.1.1`
  gepinnt, `wheel` auf `==0.46.2`; CVE-gebundene Regressionstests sichern das ab.
- **#202 (pip) ist erledigt (PR #211)** — `pip>=26.1.2` wird in den
  CI-Setup-Schritten (`ci.yml`/`pr-ci.yml`/`ui-nightly.yml`/`benchmark.yml`/
  `license-check.yml`), im Web-SessionStart-Hook und in der Dev-Install-Doku
  erzwungen; ein CVE-gebundener Regressionstest sichert das ab.
- **#203 (cryptography)/#204 (pyjwt)** sind **keine** Projekt-Abhängigkeiten
  (rein transitiv/systemseitig) → informativ, keine `constraints.txt`-Änderung.
- **#205 (urllib3)/#206 (idna) sind erledigt (PR #222)** — Projekt pinnt die
  gepatchten Releases (`urllib3==2.7.0`, `idna==3.15`); CVE-Regressionstests
  frieren das ein, der SessionStart-Hook installiert jetzt mit Constraints.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README-Audit: ein fehlerhafter Link, eine interne Begrifflichkeit | 🟡 Mittel | 🟢 Niedrig | Blockiert: „Runde 5" entfernt; nur Clone-URL offen (Owner-Entscheidung zur Repo-Sichtbarkeit) |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — HIGH/MEDIUM: 6 CVEs | 🟢 Niedrig | 🟢 Niedrig | Keine Projekt-Abhängigkeit (transitiv/systemseitig) → informativ, keine `constraints.txt`-Änderung |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — HIGH/MEDIUM: 5 CVEs | 🟢 Niedrig | 🟢 Niedrig | Keine Projekt-Abhängigkeit → informativ, keine Projekt-Aktion |
| [#218](https://github.com/NikolayDA/picture_helper/issues/218) | CHANGELOG: mehrere `[Unreleased]`-Einträge fehlen (PRs #174, #190–#215) | 🟡 Mittel | 🟢 Niedrig | Sieben fehlende Einträge per Doku-PR im bestehenden Stil nachtragen |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | INSTALL-Review: Release-Artefakte-Abschnitt verweist auf leere Releases + zwei Kleinigkeiten | 🟡 Mittel | 🟢 Niedrig | Hinweis „Artefakte ab v2.3.0" ergänzen (oder v2.3.0 taggen, Owner-Entscheidung); „Bookworm oder neuer" + `diagnose_mac.sh`-Verweis per Doku-PR |

### Empfohlene PR-Reihenfolge

1. **#200 erledigt (PR #209)** — `setuptools>=78.1.1` in `pyproject.toml` (`[build-system]`) **und** `constraints.txt` gepinnt; CRITICAL RCE geschlossen.
2. **#201 erledigt (PR #209)** — `wheel==0.46.2` in `constraints.txt` gepinnt; mit #200 als Supply-Chain-Pinning-PR gebündelt.
3. **#202 erledigt (PR #211)** — `pip>=26.1.2` in den CI-Setup-Schritten, im SessionStart-Hook + Dev-Install-Doku erzwungen; CVE-Batch (Path-Traversal/Symlink/Modul-Hijacking) geschlossen.
4. **#176 erledigt (PRs #198/#214)** — `E741`-Pauschal-Ignore entfernt, `check_untyped_defs` für `canvas`/`main_window`/`worker_controller` aktiv, cancel_ai-Wartezeit per Statusmeldung sichtbar, `shutdown_all` nullt Thread-Referenzen; dedizierte Tests für `app.py`/`main_window.py`. Am 2026-06-10 gegen `main` verifiziert (`make check` grün).
5. **#199 erledigt (PR #215)** — write-only `_redo_max` aus `canvas_history.py` entfernt; Regressionstest `test_redo_stack_capped_by_maxlen`, `make check` grün.
6. **#166 erledigt (PR #219)** — englische Docstrings/Kommentare paketweit eingedeutscht, „keine eigene Kopie"-Kommentar präzisiert.
7. **#185 erledigt (PR #220)** — Diagnose redaktiert `$HOME`/Pfade und liefert nur noch eine gefilterte Log-Zusammenfassung; `--include-raw-logs`-Flag + Shell-Test.
8. **#178 erledigt (PR #221)** — Tests auf öffentliche Accessors umgestellt, AST-Checks durch Verhaltenstests ersetzt, Doppeltests entfernt (aus #168).
9. **#205/#206 erledigt (PR #222)** — saubere Pins per CVE-Regressionstest eingefroren, SessionStart-Hook installiert mit Constraints; Issues geschlossen.
10. **#203/#204 als Beobachtungsposten** — keine Projekt-Abhängigkeiten; erst pinnen, falls ein künftiges Feature sie direkt einzieht.
11. **#161 zurückgestellt** — „Runde 5" erledigt; offen bleibt nur die Klon-URL (Owner-Entscheidung zur Repo-Sichtbarkeit).
12. **#218 als nächster Doku-PR** — die sieben fehlenden `[Unreleased]`-Einträge im CHANGELOG nachtragen.
13. **#226 danach** — INSTALL-Guides aktualisieren; der Release-Artefakte-Hinweis hängt an der Tagging-Entscheidung des Owners.

## Vorige Runden

- **2026-06-01, „modest-shannon" (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt bzw.
  verworfen, wo sie Fehlalarm war.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
