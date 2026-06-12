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
- **Security-Batch vom 2026-06-07 abgeschlossen** (#200/#201/#202/#205/#206
  via PRs #209/#211/#222): setuptools/wheel/pip/urllib3/idna gepinnt bzw.
  erzwungen, je mit CVE-gebundenem Regressionstest.

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** Deutsch und Englisch sind in der App
  umschaltbar. Die vorhandenen Dokusprachen (es/fr/uk/zh) sind noch nicht als
  Runtime-Locales umgesetzt; bei Bedarf key-für-key in `bgremover.i18n`
  ergänzen und mit Paritäts-/Smoke-Tests absichern.

## Offene GitHub-Issues – Prioritätsbewertung (2026-06-12)

Jetzt **14** offene Issues: die Beobachtungsposten #203/#204, das
zurückgestellte #161, die Doku-/Audit-Befunde #218/#226/#227/#236 sowie der
Code-Qualitäts-Batch #229–#235 aus dem Audit vom 2026-06-11. #203/#204 sind
keine Projekt-Abhängigkeiten (rein transitiv/systemseitig) → informativ,
keine `constraints.txt`-Änderung.

| # | Titel | Relevanz | Komplexität | Empfehlung |
|---|-------|----------|-------------|------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README-Audit: Clone-URL führt ins Leere | 🟡 Mittel | 🟢 Niedrig | Blockiert (Owner-Entscheidung zur Repo-Sichtbarkeit) |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — 6 CVEs | 🟢 Niedrig | 🟢 Niedrig | Beobachtungsposten, keine Projekt-Aktion |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — 5 CVEs | 🟢 Niedrig | 🟢 Niedrig | Beobachtungsposten, keine Projekt-Aktion |
| [#218](https://github.com/NikolayDA/picture_helper/issues/218) | CHANGELOG: `[Unreleased]`-Einträge fehlen | 🟡 Mittel | 🟢 Niedrig | Bereit für PR (sieben Einträge im bestehenden Stil nachtragen) |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | INSTALL-Review: Verweis auf leere Releases + zwei Kleinigkeiten | 🟡 Mittel | 🟢 Niedrig | Bereit für PR (Doku-Fixes); Release-Artefakte-Hinweis hängt an Tagging-Entscheidung |
| [#227](https://github.com/NikolayDA/picture_helper/issues/227) | RECOMMENDATIONS-Audit: Issue-Übersicht veraltet | 🟡 Mittel | 🟢 Niedrig | Durch dieses Update erledigt → Issue schließen |
| [#229](https://github.com/NikolayDA/picture_helper/issues/229) | rembg-Warmup ohne wiederverwendbare Inferenz-Session | 🟠 Hoch | 🟡 Mittel | Bereit für PR (Session via `new_session` cachen) |
| [#230](https://github.com/NikolayDA/picture_helper/issues/230) | Datei wird vor Größenprüfung voll eingelesen | 🟠 Hoch | 🟢 Niedrig | Bereit für PR (Byte-Limit vor dem `read()`) |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` kann Worker unsicher abbrechen | 🟡 Mittel | 🟠 Hoch | Verfeinerung nötig (Option A/B/C entscheiden; kurzfristig Option C) |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` lädt volle PyQt6-GUI | 🟡 Mittel | 🟡 Mittel | Bereit für PR (Lazy-Exports per PEP 562) |
| [#233](https://github.com/NikolayDA/picture_helper/issues/233) | Beschädigte recent_files brechen Menüaufbau | 🟡 Mittel | 🟢 Niedrig | Bereit für PR (defensives `paths()` + parametrisierte Tests) |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Fehlende Migration hebt `schema_version` trotzdem an | 🟢 Niedrig | 🟢 Niedrig | Bereit für PR (vor der ersten echten Migration) |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo-Limit ignoriert Redo/Originalbild | 🟢 Niedrig | 🟡 Mittel | Verfeinerung nötig (Doku-only vs. Gesamtbudget entscheiden) |
| [#236](https://github.com/NikolayDA/picture_helper/issues/236) | session-start.sh-Kommentar: `benchmark.yml` fehlt | 🟢 Niedrig | 🟢 Niedrig | Bereit für PR (Einzeiler-Kommentarfix) |

### Empfohlene PR-Reihenfolge

1. **#230** — höchste Relevanz bei geringer Komplexität: Dateigrößen-Limit vor dem Einlesen, deckt sync- und async-Pfad zentral ab.
2. **#229** — Warmup-Session wiederverwenden; größter Gewinn für die KI-Pipeline, der falsche Kommentar wird mit korrigiert.
3. **#233** — defensives `paths()` mit parametrisierten Tests; passt zum Robustheitsziel des Settings-Schemas.
4. **#236 + #218** — kleine Kommentar-/Doku-Fixes, gerne gebündelt; **#227** ist mit diesem Update erledigt und kann geschlossen werden.
5. **#232** — Lazy-Exports per PEP 562; mittlerer Umfang wegen Test-/Import-Migration.
6. **#234** — kleiner Fix, spätestens vor der ersten echten Schema-Migration einplanen.
7. **#226** — Doku-Fixes jetzt; der Release-Artefakte-Hinweis hängt an der Tagging-Entscheidung des Owners.
8. **#235** — zuerst Semantik entscheiden (reine Doku vs. gemeinsames Budget), dann umsetzen.
9. **#231** — kurzfristig Option C (begrenzte Waits + Logging), langfristig Option B (Subprozess) bewerten.
10. **#203/#204** bleiben Beobachtungsposten; **#161** bleibt blockiert (Owner-Entscheidung).

## Vorige Runden

- **2026-06-01, „modest-shannon" (A–E)** — 5 Befunde, alle erledigt.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt bzw.
  verworfen, wo sie Fehlalarm war.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
