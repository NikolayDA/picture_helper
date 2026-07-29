# Release 2.7.1 – Scope-Freeze & Freigabenotiz

Teil von Epic #680, Umsetzung von #683, **korrigiert und maschinell abgesichert
nach #699.** Dokumentiert den fixierten Umfang des Patch-Release-Kandidaten
v2.7.1, damit Build, Release-Notizen und Anwendung denselben Stand ausweisen.

## Was #699 gefunden hat – und was daraus folgt

Die erste Fassung dieses Dokuments (Commit `6dde3c6b…`, PR #698) nannte
`ba7e7cd` als verbindliche Freeze-Basis. An genau diesem Commit stand
`pyproject.toml` aber noch auf `2.7.0`; Versionsschnitt, `[2.7.1]`-CHANGELOG und
dieses Dokument kamen erst mit dem *nächsten* Commit. Ein Build gegen `ba7e7cd`
hätte also ein 2.7.0-Artefakt unter dem Namen 2.7.1 erzeugt.

Das war kein Tippfehler, sondern ein strukturelles Problem: **ein Dokument kann
seinen eigenen Commit-SHA nicht enthalten.** Ein handkopierter Freeze-Hash liegt
deshalb *immer* einen Commit hinter dem Stand, den er beschreibt. Die Korrektur
ersetzt die Handarbeit durch eine abgeleitete, prüfbare Regel:

- Der Kandidat wird **aus Git abgeleitet**, nicht abgeschrieben
  (`scripts/verify_release_freeze.py`).
- Der abgeleitete, vollständige 40-stellige SHA wird **nach** dem
  Kandidaten-Commit protokolliert – durch einen reinen Protokoll-Commit, der
  den Kandidaten nachweislich nicht verändert (siehe „Freeze-Regel").
- Alle übrigen Zusicherungen (Versionsquellen, CHANGELOG, AppStream,
  Lizenz-Snapshots, Commit-Klassifizierung, Release-Body) werden gegen genau
  diesen Commit maschinell geprüft, statt per Sichtprüfung zugesichert.

## Kandidatenbestimmung (verbindlich)

- **Basis-Tag:** `v2.7.0` (= `6f103edde7c4394e378ade7f84cad6a02828bbad`)
- **Kandidatenversion:** `2.7.1`
- **Kandidatenregel:** Kandidat ist der **jüngste Commit der Mainline
  (`--first-parent`) in `v2.7.0..main`, der einen kandidatenrelevanten Pfad
  ändert.** Reine Protokoll-Commits darüber (siehe Pfadklassen unten)
  verschieben den Kandidaten nicht. First-parent, damit ein Merge mit dem
  Baum zählt, den er **netto** in die Release-Linie eingebracht hat: ein
  Seitenzweig-Commit, dessen Änderung nie ankam (Konfliktauflösung, `-s ours`,
  späterer Revert), darf nicht Kandidat werden. Die *Klassifizierung* unten
  bleibt dagegen auf **allen** Commits des Fensters (Obermenge, fail-closed).
- **Commits im Fenster:** 31 (`v2.7.0..<Kandidat>`, siehe Tabelle – jede Zeile
  entspricht genau einem Commit; Stand nach dem Kandidatenwechsel durch #725,
  per Squash-Merge auf `main` bestätigt).
- **Protokollierter Kandidaten-SHA:** `42807350cecffbb07581e0909323abd1310f26de`
  (`feat: automate three more #685 acceptance criteria (#725)`,
  Squash-Merge von PR #725 auf `main`)

Der protokollierte SHA ist die einzige verbindliche Freeze-Basis für #685
(Artefakte) und #686 (Tag/Veröffentlichung). Steht dort `nachzutragen`, ist der
Freeze **nicht** abnahmefähig; `verify_release_freeze.py --require-pin` schlägt
in diesem Zustand bewusst fehl. Kurz-SHAs dürfen im Text zusätzlich vorkommen,
gelten aber nirgends als Nachweis.

Abzuleiten und zu prüfen mit:

```bash
python scripts/verify_release_freeze.py --print-candidate   # voller 40-stelliger SHA
make release-freeze-check                                   # vollständige Prüfung
```

### Pfadklassen (fail-closed)

| Klasse | Pfade | Wirkung |
|---|---|---|
| **Protokoll** (nicht kandidatenrelevant) | `docs/history/**`, `RECOMMENDATIONS.md`, `docs/i18n/*/RECOMMENDATIONS.md`, `CLAUDE.md` | Änderung verschiebt den Kandidaten **nicht**, bleibt aber nachweispflichtig: innerhalb des Fensters in der Klassifizierungstabelle, oberhalb des Kandidaten unter „Protokoll-Commits über dem Kandidaten". |
| **Kandidatenrelevant** | **alles andere** – u. a. `bgremover/**`, `tests/**`, `scripts/**`, `packaging/**`, `requirements/**`, `.github/**`, `pyproject.toml`, `Makefile`, `CHANGELOG.md`, `LICENSES.md`, `docs/i18n/*/CHANGELOG.md`, `docs/i18n/*/LICENSES.md`, restliche `docs/**` | Änderung erzeugt einen **neuen Kandidaten** und erzwingt die vollständige Wiederholung dieses Dokuments. |

Die Liste ist absichtlich fail-closed: ein neu eingeführter, unbekannter Pfad
gilt als kandidatenrelevant. Eine zu strenge Einordnung erzwingt höchstens eine
bewusste Entscheidung – eine zu lockere würde eine Änderung stillschweigend am
Freeze vorbeilassen (genau der Fehlerfall aus #699).

## Kategorisierung aller Änderungen seit v2.7.0

Jeder Commit im Fenster `v2.7.0..<Kandidat>` ist mit **vollem SHA** erfasst; es
gibt keine unbewertete Änderung. Reihenfolge: älteste zuerst.

| Commit | Zweck | Risiko | Testnachweis | Patch-Scope-Entscheidung |
|---|---|---|---|---|
| `36c53b8a16460a47bf602cad80f4c42734ea3348` (#671, kurz `36c53b8`) | Dokumentation – RECOMMENDATIONS-Reconciliation für den Abschluss von v2.7.0. | Keins – reine Statusdoku. | – (Doku-Snapshot). | Protokoll. Nicht release-relevant für Anwender:innen; nicht in Release Notes. |
| `06218695f587be49102f8b6cc639e1d9546539c3` (#668/#673, kurz `0621869`) | Dokumentation + Test – `ANLEITUNG.md`/`README.md` auf aktuellen Screenshot-Satz migriert (alle sechs Sprachen), neuer Governance-Test `tests/test_screenshot_references.py` gegen künftige Drift. | Niedrig – Doku-Referenzen und ein neuer, isolierter Test; keine Laufzeitänderung der Anwendung. | Neuer Test selbst ist der Nachweis; `make check` grün. | Aufnehmen (kandidatenrelevant über `tests/`), aber ohne Anwendungsfunktion – nicht in Release Notes. |
| `da5839da918c7d3f0a917aa2129d7b73b3fe7b3c` (#674, kurz `da5839d`) | Dokumentation – RECOMMENDATIONS-Snapshot (PR-/Issue-Audit 22.–23. Juli). | Keins – reine Statusdoku in sechs Sprachen. | – (Doku-Snapshot). | Protokoll. Nicht in Release Notes. |
| `0e1e799c133b6b5f43e1b5faf3d8961ee809b7b4` (#675, kurz `0e1e799`) | Dokumentation – neun veraltete/ungenaue Code-Kommentare und Docstrings korrigiert (keine Codeänderung außerhalb von Kommentaren). | Keins – Kommentar-/Docstring-only, laut Commit-Nachricht ausdrücklich ohne Verhaltensänderung; ruff clean. | ruff clean (im Commit vermerkt); keine Logikänderung, daher kein zusätzlicher Testbedarf. | Aufnehmen (berührt `bgremover/**`), aber ohne sichtbare Wirkung – nicht in Release Notes. |
| `427b9ce498373e1c9fd2ff0d948b85f5d56f9aef` (PR #676, kurz `427b9ce`) | **Fehlerbehebung.** `GLReliefViewer._ensure_buffers` reallozierte GL-Puffer/VAO der 3D-Reliefvorschau bei jedem (Wieder-)Upload, ohne die Vorgänger freizugeben – verwaiste GPU-Ressourcen akkumulierten über die Sitzung. Freigabe (`_release_gl_objects`) läuft jetzt zu Beginn von `_ensure_buffers`. | Niedrig – reiner Darstellungscode der optionalen 3D-Vorschau, kein Schreibpfad ins Modell, keine Bild-/Projekt-/Exportdaten betroffen. | Dedizierte GL-freie Regressionstests für Freigabe- und (Wieder-)Upload-Pfad (`tests/test_viewer_3d.py`, +87 Zeilen); `make check` grün. | **Aufnehmen – der namensgebende Fix dieses Patch-Release.** In CHANGELOG `[2.7.1]` unter „Behoben" dokumentiert. |
| `9c93de6bbf10705aba2b6b3a3a5c693cb7e27839` (#678, kurz `9c93de6`) | Dokumentation – `CLAUDE.md` auf aktuellen Repo-Stand gebracht (Standard-Gate, Architektur-Abschnitte, CI-Inventar). | Keins – reine Doku, keine Code-/Verhaltensänderung. | `make check` grün (im Commit vermerkt). | Protokoll. Nicht in Release Notes. |
| `45ebac3929b8520a650b00abd1ce7ec722cd3cda` (#677/#679, kurz `45ebac3`) | **Chore/Aufräumen.** Entfernt 4 per `vulture --min-confidence 60` + manueller Verifikation nachgewiesene, reposweit unreferenzierte Symbole (zwei ungenutzte Properties, ein Skript-Wrapper, eine Konstanten-Duplizierung). | Niedrig – laut Commit-Nachricht **keine funktionale Verhaltensänderung**; `make check` grün, vulture bestätigt alle 4 Funde verschwunden ohne neue Kandidaten. | Volle Testsuite (`make check`) vor und nach dem Commit grün; vulture-Re-Scan ohne neue Funde. | **Aufnehmen, mit expliziter Risikoentscheidung:** tote-Code-Entfernung, keine Architektur- oder Verhaltensänderung, damit kein „opportunistisches Refactoring" im Sinne des Freeze-Kriteriums (siehe Abgrenzung unten). Kein separater Revert vor dem Tag nötig. |
| `ba7e7cd7ce65b24a1d0f223def25bbaf79834cb0` (#697, kurz `ba7e7cd`) | Dokumentation – RECOMMENDATIONS um drei neue Epics (#680–#682) ergänzt. **Historisch:** in der ersten Fassung fälschlich als Freeze-Commit benannt (siehe #699); der Commit selbst enthält weder Versionsschnitt noch dieses Dokument. | Keins – reine Statusdoku. | – (Doku-Snapshot). | Protokoll. Nicht in Release Notes; **nicht** als Freeze-Basis verwendbar. |
| `6dde3c6beb9aca00306cab7d4453c85fb813c383` (#683 via PR #698, kurz `6dde3c6`) | **Versionsschnitt + erste Fassung dieses Dokuments.** `pyproject.toml` 2.7.0 → 2.7.1; `[2.7.1]`-Abschnitt in `CHANGELOG.md` und allen fünf Übersetzungen; Titel-/Datumszeile in `LICENSES.md` (6 Sprachen); `<release version="2.7.1" date="2026-07-26"/>` in `packaging/linux/de.bgremover.app.metainfo.xml`; neues Scope-Freeze-Dokument. | Niedrig für die Anwendung (keine Logikänderung), **hoch für den Release-Prozess**: dieser Commit ist der eigentliche Versionsschnitt und damit der früheste Stand, der überhaupt 2.7.1 heißen darf. Der von ihm dokumentierte Freeze-Hash war inkonsistent (#699). | PR-CI von #698 grün (Lint/Typecheck/Tests, inkl. `tests/test_changelog_metadata.py`, `tests/test_licenses_version.py`, `tests/test_version.py`); Nachprüfung über `make check` auf dem Korrektur-Commit dieses Dokuments. | **Aufnehmen – kandidatenrelevant und unverzichtbar** (ohne ihn gibt es keine Version 2.7.1). Inhaltlich unverändert übernommen; korrigiert wird ausschließlich die Freeze-Basis-Aussage, hier in dieser Datei. Kein Anwender-CHANGELOG-Eintrag (Release-Metadaten). |
| `9b27527d1db7aa7bacc84f125ea969eceba0abc4` (#700, kurz `9b27527`) | Dokumentation – RECOMMENDATIONS-Reconciliation nach dem PR-/Issue-Audit vom 26.07. (führt #699 als Folge-Issue ein). | Keins – reine Statusdoku in sechs Sprachen. | – (Doku-Snapshot); PR-CI von #700 grün. | Protokoll (`RECOMMENDATIONS.md` + 5 Übersetzungen, sonst nichts). Verschiebt den Kandidaten nicht; nicht in Release Notes. |
| `480a5fc0008ded401b02b15373d8474d67c83382` (#699 via PR #701, kurz `480a5fc`) | **Freeze-Korrektur, als Squash auf `main` eingebracht.** Fasst die gesamte Korrektur aus PR #701 zusammen: `scripts/verify_release_freeze.py` (abgeleitete, maschinelle Kandidatenbestimmung) + `tests/test_release_freeze.py`, `make release-freeze-check`, das Freeze-Gate als harte Vorbedingung in `release-linux.yml`, `[2.7.1]`-CHANGELOG in allen sechs Sprachen um „Hinweise zu diesem Release" ergänzt und dieses Dokument vollständig neu klassifiziert. Enthält die Ergebnisse beider Codex-Reviewrunden — u. a.: (1) **Umbenennungen** – `git diff --name-only` meldete mit Rename-Erkennung nur das Ziel, `git mv bgremover/x.py docs/history/x.py` sah damit wie ein reiner Protokoll-Commit aus, obwohl er Anwendungscode aus dem Baum entfernt (jetzt `--no-renames` in beiden Diff-Pfaden). (2) **Basis-Tag** – geprüft wurde nur, dass `v2.7.0` auflöst; ein verschobenes Tag auf einen Geschwister-Commit erzeugt dasselbe Fenster. Die Basis ist jetzt als voller SHA eingefroren (Pflichtfeld), wird mit dem aufgelösten Tag verglichen und muss Vorfahr des geprüften Commits sein. (3) **Release-Gate** – `verify-tag` in `release-linux.yml` führt das Freeze-Gate jetzt mit `--require-pin` aus (Checkout `fetch-depth: 0`); vorher war die Prüfung rein opt-in und jeder Commit mit passender pyproject-Version taggbar. (4) **Übersetzte Datumszeilen** – alle sechs CHANGELOG-Überschriften werden gegen das Datum der Wurzel-Datei geprüft. | Niedrig für die Anwendung – Prüfwerkzeug, Tests und Release-Workflow, kein `bgremover/**`-Code, nur Release-Metadaten im CHANGELOG-Text. **Erhöht für den Release-Prozess, aber nur verschärfend:** ein Tag-Push ohne passendes Freeze-Dokument scheitert ab jetzt bewusst (fail-closed). | `make check` grün auf dem Zweigstand (**2042 passed**, 5 skipped, 14 deselected); Regressionstests gegen echte Mini-Repositories (Umbenennung in einen Protokollpfad, verschobenes Basis-Tag, Basis außerhalb der Release-Linie, Datumsdrift einer Übersetzung, `-s ours`-Merge, echter Merge, Extraktor-Herkunft, beide Pin-Fälle) plus Test der Workflow-Verdrahtung; Negativkontrolle für die Rename-Erkennung in git nachgestellt; PR-CI von #701 grün; `make release-freeze-check` auf `main` 0 Fehler/0 Warnungen. | **Aufnehmen – der Kandidat.** Der Squash ist nachweislich **freeze-äquivalent** zum geprüften Zweigstand `5e7b7e30baa5…`: `verify_release_freeze.py` meldete beim Übergang `candidate-sha-equivalent` (identischer kandidatenrelevanter Baum) – genau der dokumentierte Merge-Fall, aufgelöst durch diesen Protokoll-Commit. |
| `b0a8faed7921fb4da0b24e29118cf5085e63748b` (#699 via PR #703, kurz `b0a8fae`) | Protokoll – trägt den vollen Kandidaten-SHA von PR #701, die Fensterzahl und die Gate-Nachweise in dieses Dokument nach. | Keins – ändert ausschließlich `docs/history/RELEASE-2.7.1-scope-freeze.md`. | `make release-freeze-check` danach 0 Fehler/0 Warnungen. | Protokoll. Verschiebt den Kandidaten nicht; nicht in Release Notes. Lag zum Zeitpunkt seiner Entstehung *über* dem Kandidaten und liegt seit dem Kandidatenwechsel durch #684 *im* Fenster – daher hier klassifiziert. |
| `d97d2260f26ab2289fe411d8c57eaac730204143` (#704, kurz `d97d226`) | Dokumentation – RECOMMENDATIONS-Reconciliation nach dem Audit vom 27.07. | Keins – reine Statusdoku in sechs Sprachen. | PR-CI von #704 grün. | Protokoll (`RECOMMENDATIONS.md` + 5 Übersetzungen). Nicht in Release Notes. |
| `a0f6ef15b7fac67e79135809963fb2235ca76e6a` (#705, kurz `a0f6ef1`) | Dokumentation – Abgleich der offenen Issue-Definitionen gegen den Code, Statusdoku. | Keins – reine Statusdoku. | PR-CI von #705 grün. | Protokoll. Nicht in Release Notes. |
| `65a656aa41416219bbcdcedba92e06047d2a8ed0` (#684 via PR #706, kurz `65a656a`) | **GL-Ressourcen-Langzeitnachweis und Regressionsgate.** Ergänzt den messbaren Nachweis für den Fix aus PR #676: `viewer_3d` bekommt zwei reine Diagnose-Zähler (`gl_resource_stats()` prozessweit, `GLReliefViewer.gl_object_count` je Viewer), `scripts/gl_stress_probe.py` ist die geteilte Messsonde (`make gl-stress`, JSON-Nachweis, `--mode gl` für echten Kontext), `tests/test_viewer_3d_gl_lifecycle.py` sichert den Lebenszyklus über 110 Zyklen je Datensatzgröße samt Fehler-/Abbruchpfaden und Negativkontrolle ab, `tests/test_viewer_3d_gl.py` denselben Nachweis unter echtem GL. Testbericht: [`RELEASE-2.7.1-gl-langzeittest.md`](RELEASE-2.7.1-gl-langzeittest.md). | Niedrig für die Anwendung – am Renderpfad ändert sich nichts; die Zähler sind zwei Integer ohne GL-Aufruf, kein Schreibpfad ins Modell, keine neue Abhängigkeit, keine Formatänderung. Der übrige Diff ist Test-, Werkzeug- und Doku-Code. | `make check` grün (**2069 passed**, 6 skipped, 14 deselected), `make ui` grün (20 passed), `make coverage` 93 % (`fail_under = 86`), `make gl-stress` und ein 1000-Zyklen-Langlauf ohne Befund; Details und Zählerstände im Testbericht. | **Aufnehmen.** Kandidatenrelevant über `bgremover/**`, `tests/**`, `scripts/**`, `pyproject.toml` und `Makefile`; nach der Freeze-Regel als Nachweis-/Regressionsarbeit an einer release-relevanten Prüfung zulässig. Kein Anwender-CHANGELOG-Eintrag (keine sichtbare Verhaltensänderung). War bis zum Kandidatenwechsel durch #711 der Kandidat (siehe „Historie der Kandidatenwechsel"). |
| `5c25e3b71f6be42e454e58712cd2dfad2dfb6c3a` (#684 via PR #707, kurz `5c25e3b`) | Protokoll – trug den vollen Kandidaten-SHA von PR #706, die Fensterzahl (15) und die Gate-Nachweise in dieses Dokument nach. | Keins – ändert ausschließlich `docs/history/RELEASE-2.7.1-scope-freeze.md`. | `make release-freeze-check` danach 0 Fehler/0 Warnungen. | Protokoll. Verschiebt den Kandidaten nicht; nicht in Release Notes. Lag zum Zeitpunkt seiner Entstehung *über* dem Kandidaten und liegt seit dem Kandidatenwechsel durch #711 *im* Fenster – daher hier klassifiziert. |
| `ac053638c1d81864043798a55bf41e4fb4c877c6` (#702 via PR #708, kurz `ac05363`) | Dokumentation – korrigiert die Tab-Zuordnung im Architektur-Abschnitt von `README.md` (alle sechs Sprachen): Ebenen- und Höhen-Tab leben in eigenen Modulen (`layer_panel.LayerPanel`, `height_map_panel.HeightMapPanel`), waren aber pauschal `right_panel_tabs` zugeschrieben. | Keins – reine Textkorrektur in `README.md`/Übersetzungen, keine Code- oder Verhaltensänderung. | PR-CI von #708 grün; `test_i18n_docs`/`test_markdown_links` unberührt. | Aufnehmen (kandidatenrelevant, da `README.md` nicht unter die Protokoll-Pfadklasse fällt), aber ohne Anwendungswirkung – nicht in Release Notes. **Erfüllt das Freeze-Kriterium nicht wörtlich** (keine Regressions-/Sicherheitsbehebung); explizite Ausnahmebegründung siehe „Scope-Ausnahme für `ac053638c1d8…` (#708)" unten. |
| `1b04887f7aafa4fd1ddd2636f41d3b768022db31` (PR #709, kurz `1b04887`) | **CI-Härtung.** Erzwingt das Freeze-Gate (`verify_release_freeze.py --require-pin`) jetzt auch für manuelle `workflow_dispatch`-Kandidatenbauten (vorher nur bei Tag-Pushes), ergänzt einen zusätzlichen Schritt, der exakte Gleichheit von `GITHUB_SHA` und dem abgeleiteten Kandidaten erzwingt (ein Kandidatenbau auf einem Protokoll-Commit *über* dem Kandidaten schlägt damit fehl statt eines anderen Standes als den dokumentierten zu bauen), und protokolliert Produktversion/Commit-SHA/Run-ID sowie die tatsächlich verwendeten Bundler-Versionen (`python-appimage`/`build`/PyInstaller aus der isolierten `toolenv`-venv) im Build-Log jedes Matrix-Legs. | Niedrig für die Anwendung – reine Workflow-/Test-Änderung, kein `bgremover/**`-Code. Erhöht (bewusst verschärfend) für den Release-Prozess: ein Kandidatenbau ist jetzt ausschließlich auf dem exakten Kandidaten-Commit möglich, nicht mehr auf einem Protokoll-Commit darüber. | Neuer Regressionstest in `tests/test_release_gate.py` (+67 Zeilen); PR-CI von #709 grün. | **Aufnehmen – kandidatenrelevant** (`.github/workflows/release-linux.yml`, `tests/**`). Ändert den Build-/Tag-SHA-Vertrag; siehe aktualisierte Freeze-Regel „Tag (#686)" unten. Kein Anwender-CHANGELOG-Eintrag (reiner Release-Prozess). |
| `0b021ccfa5f7145f2ae4eba24b6ded8772501b4a` (#712, kurz `0b021cc`) | Dokumentation – RECOMMENDATIONS-Reconciliation nach dem Release-Audit vom 28.07. | Keins – reine Statusdoku in sechs Sprachen. | PR-CI von #712 grün. | Protokoll (`RECOMMENDATIONS.md` + 5 Übersetzungen). Nicht in Release Notes. |
| `5e947ee816a2d481fa6ea901790281293aced4d5` (#711 via PR #713, kurz `5e947ee`) | **GL-Puffer-Fehlererkennung hart erzwungen.** `QOpenGLBuffer.create()`/`bind()` melden einen Fehlschlag ausschließlich über ihren booleschen Rückgabewert; `GLReliefViewer._make_buffer` (jetzt `_new_buffer`) ignorierte ihn. Ein Wrapper ohne GL-Namen blieb dann referenziert, `has_failed` blieb `false`, und `gl_object_count`/die GL-Sonde konnten `verdict: ok` melden, ohne dass je ein Puffer entstanden war – genau das falsche Grün, das der Hardware-Nachweis in #685 hätte liefern können. Neue `GLBufferError`; ein Teilerfolg gibt VAO und bereits erzeugte Puffer genau einmal frei und schaltet über `_fail` in den bekannten Fehlerzustand mit 2D-Rückfall statt einer leeren „bereiten" 3D-Ansicht. Sonde: `MIN_LIVE_PER_VIEWER = 3` – ein unvollständiger Puffersatz ergibt im `--mode gl` `ProbeNotExecutable`/Exit 2, im `--mode fake` einen harten Befund statt `ok`. Testbericht: [`RELEASE-2.7.1-gl-langzeittest.md`](RELEASE-2.7.1-gl-langzeittest.md) Abschnitt 4.4/7.1. | Niedrig für die Anwendung – reiner Fehlerpfad der optionalen 3D-Vorschau, kein Schreibpfad ins Modell; der VAO bleibt als GL-2.1-Erweiterung weiterhin optional (kein neuer Fehlerfall). Erhöht die Verlässlichkeit des Release-Nachweises selbst (das war der Zweck von #711). | `make check` grün (ruff „All checks passed", mypy „no issues found in 70 source files", pytest **2082 passed**, 6 skipped, 14 deselected), `make ui` (20 passed), `make coverage` 93 % (`fail_under = 86`), `make gl-stress` (Exit 0, `ok`); neun neue deterministische, GL-freie Regressionstests in `tests/test_viewer_3d_gl_lifecycle.py` (`create()==false`, `bind()==false`, Teilerfolg, 110 wiederholte Fehlschläge ohne Restbestand, 110 Reuploads im Erfolgsfall, Sonden-CLI-Fälle); PR-CI von #713 grün (Lightweight PR checks, CodeQL, License Check, Dependency Audit, Claude Code Review). | **Aufnehmen.** Kandidatenrelevant über `bgremover/**`, `scripts/**`, `tests/**` und `CHANGELOG.md`. CHANGELOG-Eintrag unter `[2.7.1] → Behoben` in allen sechs Sprachen: die 3D-Vorschau zeigt auf einem Treiber mit fehlgeschlagenem Puffer-Upload jetzt den Fehlerzustand mit 2D-Rückfall statt einer leeren 3D-Ansicht. War bis zum Kandidatenwechsel durch #715 der Kandidat (siehe „Historie der Kandidatenwechsel"). |
| `adb2205960619b9b5c29a9a05feda163310782a6` (PR #715, kurz `adb2205`) | **Deadlock im Freeze-Gate aus #709 aufgelöst.** Der von #709 ergänzte Schritt „Gebauter Commit ist exakt der abgeleitete Kandidat" (`github.sha == verify_release_freeze.py --print-candidate`) machte jeden künftigen Kandidatenbau strukturell unmöglich: ein Freeze-Dokument kann seinen eigenen Commit-SHA nicht enthalten (der SHA existiert erst nach dem Commit), also pinnt der Kandidaten-Commit selbst immer noch den *vorherigen* Kandidaten und scheitert an `--require-pin`; der nachträgliche Protokoll-Commit, der den Pin einträgt, scheiterte dann seinerseits am neuen `github.sha`-Abgleich. Kein Commit konnte je beide Gates gleichzeitig bestehen (gefunden bei der Codex-Review von PR #714). Der #709-Schritt ist entfernt; `--require-pin` allein reicht (prüft bereits den *abgeleiteten* Kandidaten gegen den dokumentierten Pin) – exakt das Modell, das vor #709 funktionierte (z. B. beim Squash-Übergang PR #701/#703). | Niedrig für die Anwendung – reine Workflow-/Test-Änderung, kein `bgremover/**`-Code. Für den Release-Prozess **korrigierend**: macht Kandidatenbauten (#685/#686) wieder möglich, ohne die #709-Provenienz-Garantie (Freeze-Pin muss weiterhin zum gebauten Baum passen) aufzugeben. | `make check` grün (ruff „All checks passed", mypy „no issues found in 70 source files", pytest **2082 passed**, 6 skipped, 14 deselected); `tests/test_release_gate.py` um die Gegenprobe `test_freeze_gate_allows_a_protocol_commit_above_the_candidate` ersetzt (stellt sicher, dass der `github.sha`-Abgleich nicht wieder eingeführt wird); PR-CI von #715 grün. | **Aufnehmen.** Kandidatenrelevant über `.github/workflows/release-linux.yml` und `tests/test_release_gate.py`. Behebt nachweislich einen Regressionsfund in einer release-relevanten Prüfung (das Freeze-Gate selbst, `tests/test_release_gate.py`/`verify_release_freeze.py`/`release-linux.yml`) – erfüllt die Freeze-Ausnahme wörtlich, anders als #708 oben. Kein Anwender-CHANGELOG-Eintrag (reiner Release-Prozess). War bis zum Kandidatenwechsel durch #720 der Kandidat (siehe „Historie der Kandidatenwechsel"). |
| `aa4369d023db087793ddc3e402be6925781426e7` (#710 via PR #714, kurz `aa4369d`) | Protokoll – Freeze-Nachtrag in zwei Schritten derselben PR: trägt zunächst den vollen Kandidaten-SHA von PR #713 (#711) nach, klassifiziert #707/#708/#709/#712 und behebt zwei Codex-Reviewbefunde (falsch zugeordnete Gate-Fehler, fehlende Scope-Ausnahme für #708); trägt danach den vollen Kandidaten-SHA von PR #715 nach, wandelt die vorherige `Kandidaten-Commit`-Platzhalterzeile für #711/#713 in eine Zeile mit vollem SHA um, ergänzt eine Zeile für #715, aktualisiert die Fensterzahl 20 → 21. | Keins – ändert ausschließlich `docs/history/RELEASE-2.7.1-scope-freeze.md`. | `make release-freeze-check` danach 0 Fehler/0 Warnungen. | Protokoll. Verschiebt den Kandidaten nicht; nicht in Release Notes. Lag zum Zeitpunkt seiner Entstehung *über* dem Kandidaten und liegt seit dem Kandidatenwechsel durch #720 *im* Fenster – daher hier klassifiziert. |
| `b90d92a6468e0a275a84a137359b3991d7ceb00d` (#717, kurz `b90d92a`) | Dokumentation – Issue-Triage nach Schließen von #710/#711 aufgefrischt, #685 als startbereit markiert. | Keins – reine Statusdoku in sechs Sprachen. | PR-CI von #717 grün. | Protokoll (`RECOMMENDATIONS.md` + 5 Übersetzungen). Nicht in Release Notes. |
| `07de38fdd77cce54272c9e0d0e0ceb7be0d6c7d2` (#718, kurz `07de38f`) | Dokumentation – neues Issue #716 (Test-Suite-Audit) nach erneuter Prüfung aller offenen Issues in die Triage aufgenommen. | Keins – reine Statusdoku in sechs Sprachen. | PR-CI von #718 grün. | Protokoll (`RECOMMENDATIONS.md` + 5 Übersetzungen). Nicht in Release Notes. |
| `dcdeeecbca08440a8f976d547216128e685866da` (#719, kurz `dcdeeec`) | Dokumentation – RECOMMENDATIONS-Audit nach Remote-Sync erweitert. | Keins – reine Statusdoku in sechs Sprachen. | PR-CI von #719 grün. | Protokoll (`RECOMMENDATIONS.md` + 5 Übersetzungen). Nicht in Release Notes. |
| `f8143db7899149447743cf20a28c8ffcf2a98acc` (PR #720, kurz `f8143db`) | **Zwei fehlende Hardware-Abnahme-Nachweise für #685 ergänzt.** Der reale Hardware-Abnahmelauf (macOS arm64 + Linux aarch64) deckte Start, GPU-Provenienz, nativen 3D-Viewer und Live-GL-Performance ab, ließ aber zwei in den Akzeptanzkriterien von #685 genannte Prüfungen automatisiert unbelegt: Öffnen eines echten 2.7.0-Projekts ohne unbeabsichtigte Formatmigration/Datenänderung, und mindestens ein EufyMake-Export-Smoke-Test. Ergänzt `tests/fixtures/project_v2_7_0.bgrproj` (mit dem tatsächlichen v2.7.0-Release-Code gebaut, kein Nachbau), `tests/test_project_v270_upgrade.py` (Qt-frei, Struktur-/Pixel-Nachweis gegen die vollständigen persistierten Felder), Erweiterungen in `tests/test_e2e_release_regression.py` (EufyMake-Export-Smoke über den echten `write_export`-Pfad + 2.7.0-Projekt-Open/Weiterarbeiten über `MainWindow`, bereits Teil des `release-abnahme.yml`-Hardware-Pfads) sowie `bgremover/acceptance_smoke.py` (neuer GL-freier Automatisierungshook, analog `screenshot3d.py`/`BGREMOVER_SCREENSHOT_3D`, bindet beide Nachweise an das gepackte Kandidatenartefakt statt nur an den Source-Checkout – **Stand bei Merge:** prüft dort Öffnen ohne Migrationshinweis, Ebenenstruktur/-rolle und bitgenaue Weiterbearbeitbarkeit (Höhen-Op + Undo) sowie den vollständigen EufyMake-Export; der volle Feld-/Pixel-Vergleich (IDs, Namen, Metadaten, Farbmotiv-/Höhenkarten-Payload gegen die Fixture-Referenz) blieb zu diesem Zeitpunkt nur im Source-Checkout-Test `tests/test_project_v270_upgrade.py` abgesichert, verdrahtet über `bgremover/app.py` und `scripts/abnahme_smoke.py`). | Niedrig für die Anwendung – ausschließlich Test-/Fixture-/Automatisierungscode; kein Eingriff in Farbmotiv-, Höhen- oder Exportlogik selbst, Exportvertrag unverändert. | `make check` grün (**2099 passed**, 6 skipped, 14 deselected); PR-CI von #720 grün; unabhängige Codex-Review (2× P1, 1× P2) vor dem Merge behoben (Höhenebene vor `apply_height_op` aktivieren und Hash-Änderung verifizieren, vollständiger Feldvergleich inkl. IDs/Namen/Metadaten/Version im Fixture-Test, Bindung an das gepackte Artefakt statt nur den Checkout) – **Nachtrag:** eine zweite Reviewrunde (auf diesem Freeze-Nachtrag, PR #721) fand die artefaktgebundene 2.7.0-Prüfung strukturell schwächer als den Source-Checkout-Test; Nachbesserung folgt als eigener kandidatenrelevanter Commit, siehe „Verweise auf denselben Kandidaten". | **Aufnehmen – der neue Kandidat.** Kandidatenrelevant über `bgremover/**`, `tests/**`, `scripts/**`. Erfüllt die Freeze-Ausnahme wörtlich: schließt einen Nachweislückenfund in einer release-relevanten Prüfung (den eigenen Akzeptanzkriterien von #685). Kein Anwender-CHANGELOG-Eintrag (reine Abnahme-Automatisierung, keine sichtbare Verhaltensänderung). War bis zum Kandidatenwechsel durch #722 der Kandidat (siehe „Historie der Kandidatenwechsel"). |
| `9845147ea708819dc68001763633401d322a36cb` (PR #722, kurz `9845147`) | **`acceptance_smoke.py`s 2.7.0-Prüftiefe an den Source-Checkout-Test angeglichen.** Zwei Codex-Reviewrunden auf PR #721 bzw. #722 fanden, dass die artefaktgebundene 2.7.0-Projektprüfung aus #720 strukturell schwächer war als behauptet und als `tests/test_project_v270_upgrade.py`: (1) `project.version` ist das separate, semantische `project_version`-Feld (immer 1), nicht die tatsächliche `.bgrproj`-Manifest-Formatversion – ein Paket mit abweichendem `PROJECT_FORMAT_VERSION` hätte den (warnungsfreien) Migrationspfad nehmen können, ohne dass der Hook es bemerkt; jetzt liest der Hook die rohe Manifest-Version direkt aus der Fixture-ZIP und vergleicht sie mit der im gepackten Prozess geltenden Konstante. (2) `visible`/`opacity`/`locked`/`role` beider Ebenen sowie `active_layer_id` wurden nie verglichen – ein Loader, der z. B. die Farb-Ebenen-Deckkraft von 1.0 auf 0.5 änderte, hätte weiterhin `ok` gemeldet; jetzt vollständig ergänzt. Neue Regressionstests (Lookalike-Projekt mit frischen IDs, gezielte Deckkraft-Drift bei identischen IDs) beweisen, dass die verschärften Prüfungen tatsächlich diskriminieren. | Niedrig für die Anwendung – ausschließlich der interne Abnahme-Hook und seine Tests; kein Eingriff in Farbmotiv-, Höhen- oder Exportlogik selbst. | `make check` grün (**2101 passed**, 6 skipped, 14 deselected); PR-CI von #722 grün; beide Codex-Reviewrunden (insgesamt 3× P1) vor dem Merge behoben. | **Aufnehmen – der neue Kandidat.** Kandidatenrelevant über `bgremover/**`, `tests/**`. Erfüllt die Freeze-Ausnahme wörtlich: schließt einen in #721/#722 selbst gefundenen Nachweislückenfund in einer release-relevanten Prüfung (den eigenen Akzeptanzkriterien von #685). Kein Anwender-CHANGELOG-Eintrag (reine Abnahme-Automatisierung, keine sichtbare Verhaltensänderung). War bis zum Kandidatenwechsel durch #723 der Kandidat (siehe „Historie der Kandidatenwechsel"). |
| `c9fb5cd96d0804815493cce0176a9b537b78c841` (PR #721, kurz `c9fb5cd`) | Protokoll – Freeze-Nachtrag, der die Kandidatenwechsel durch #720 **und** #722 in einem konsolidierten Schritt nachzieht (statt zweimal hintereinander): trägt den vollen Kandidaten-SHA von PR #722 nach, wandelt die vorherige `Kandidaten-Commit`-Platzhalterzeile für #720 in eine Zeile mit vollem SHA um, klassifiziert `aa4369d` (#710 via PR #714), `b90d92a` (#717), `07de38f` (#718) und `dcdeeec` (#719) sowie #720 selbst vollständig, aktualisiert die Fensterzahl 21 → 27. | Keins – ändert ausschließlich `docs/history/RELEASE-2.7.1-scope-freeze.md`. | `make release-freeze-check` danach 0 Fehler/0 Warnungen. | Protokoll. Verschiebt den Kandidaten nicht; nicht in Release Notes. Lag zum Zeitpunkt seiner Entstehung *über* dem Kandidaten und liegt seit dem Kandidatenwechsel durch #723 *im* Fenster – daher hier klassifiziert. |
| `e65e9380c0160bbf59415c6f883c7ee12d1e44c7` (PR #723, kurz `e65e938`) | **EufyMake-Exportordner-Kollision zwischen Artefaktklassen behoben.** Der erste echte Hardware-Abnahmelauf gegen den #722-Kandidaten (Raspberry Pi 5) fand einen realen Bug: `scripts/abnahme_smoke.py` ruft `_acceptance_extra` je Artefaktklasse (AppImage/.deb/.dmg) mit *demselben* `evidence_dir` auf, nur der JSON-Dateiname unterscheidet sich je Klasse. `run_acceptance_extra` leitete den EufyMake-Exportordner bisher als hartkodiertes `eufymake_export` unterhalb dieses gemeinsamen Elternordners ab – die zuerst gelaufene Klasse (AppImage) legte den Ordner an, jede folgende Klasse (.deb) kollidierte damit (`write_export` ohne `overwrite=True`) und meldete `write_export fehlgeschlagen: <Pfad>`. Der Exportordnername wird jetzt vom JSON-Ausgabedateinamen abgeleitet (`output_json.stem + "_eufymake_export"`), sodass jede Artefaktklasse ihren eigenen Ordner bekommt. Neuer Regressionstest reproduziert das exakte Szenario (zwei Aufrufe, gemeinsamer `evidence_dir`, beide müssen unabhängig erfolgreich sein). | Niedrig für die Anwendung – ausschließlich der interne Abnahme-Hook und sein Test; kein Eingriff in Farbmotiv-, Höhen- oder Exportlogik selbst. | `make check` grün (**2102 passed**, 6 skipped, 14 deselected); PR-CI von #723 grün. | **Aufnehmen.** Kandidatenrelevant über `bgremover/**`, `tests/**`. Erfüllt die Freeze-Ausnahme wörtlich: schließt einen bei der echten Hardware-Abnahme in #685 gefundenen Regressionsfund. Kein Anwender-CHANGELOG-Eintrag (reiner Bugfix eines internen Abnahme-Hooks, keine sichtbare Verhaltensänderung für Anwender:innen). War bis zum Kandidatenwechsel durch #725 der Kandidat (siehe „Historie der Kandidatenwechsel"). |
| `d0f8ea277ddd14e2cad13522668e2dee8be22633` (PR #724, kurz `d0f8ea2`) | Protokoll – Freeze-Nachtrag, der den vollen Kandidaten-SHA von PR #723 nachträgt, die vorherige `Kandidaten-Commit`-Platzhalterzeile für #722 in eine Zeile mit vollem SHA umwandelt, `c9fb5cd` (#721) klassifiziert, die Fensterzahl 27 → 29 aktualisiert. | Keins – ändert ausschließlich `docs/history/RELEASE-2.7.1-scope-freeze.md`. | `make release-freeze-check` danach 0 Fehler/0 Warnungen. | Protokoll. Verschiebt den Kandidaten nicht; nicht in Release Notes. Lag zum Zeitpunkt seiner Entstehung *über* dem Kandidaten und liegt seit dem Kandidatenwechsel durch #725 *im* Fenster – daher hier klassifiziert. |
| `Kandidaten-Commit` (PR #725, voller SHA unter „Protokollierter Kandidaten-SHA") | **Drei weitere #685-Akzeptanzkriterien automatisiert.** (1) Fehlende optionale Komponenten: `bgremover/acceptance_smoke.py` erzwingt `REMBG_AVAILABLE = False` im laufenden, gepackten Prozess und prüft, dass die KI-Aktion die etablierte, übersetzte Meldung zeigt statt eines stillen Ausfalls (dieselbe Prüfung wie `tests/test_main_window.py`, jetzt zusätzlich artefaktgebunden). (2) Abschlussmatrix: `scripts/abnahme_aggregate.py` ergänzt Gerät/OS (aus den Umgebungs-Pflichtfeldern der Evidenz), Datum (aus dem jeweils eigenen `erzeugt_am`/`timestamp` der Zeile, nicht pauschal aus der Plattform-Evidenz), ein Testperson-Feld (`automatisiert (kein manueller Tester)`) und einen Link auf den erzeugenden Workflow-Lauf. (3) Virenscan: `release-linux.yml` scannt die fünf gebauten Artefakte zusätzlich zu `scan_release_artifacts.py` mit ClamAV (Definitionsaktualisierung best-effort, ein tatsächlicher Fund blockiert hart). Unabhängige Codex-Review (1× P1, 2× P2) vor dem Merge vollständig behoben: Homebrews aktive `Example`-Direktive in `freshclam.conf` verhinderte auf macOS jede Datenbankaktualisierung (jetzt entfernt + expliziter Datenbank-Präsenz-Check vor `clamscan`); E2E-/Live-GL-Zeilen zeigten bei einem UTC-Datumswechsel während des Jobs das Datum der (früher erzeugten) Plattform-Evidenz statt ihres eigenen Zeitstempels; ein reiner Fehlschlag der Fehlende-Komponente-Prüfung blieb im Job-Log unsichtbar (nur zwei der drei Meldungen wurden gedruckt). | Niedrig für die Anwendung – ausschließlich interne Abnahme-Automatisierung (Hook, Matrix-Aggregation, CI-Workflow); kein Eingriff in Farbmotiv-, Höhen- oder Exportlogik selbst. | `make check` grün (**2108 passed**, 6 skipped, 14 deselected); PR-CI von #725 grün; unabhängige Codex-Review (1× P1, 2× P2) vor dem Merge behoben. | **Aufnehmen – der neue Kandidat.** Kandidatenrelevant über `bgremover/**`, `scripts/**`, `.github/workflows/**`. Erfüllt die Freeze-Ausnahme wörtlich: schließt drei bei der Akzeptanzkriterien-Durchsicht von #685 identifizierte Automatisierungslücken. Kein Anwender-CHANGELOG-Eintrag (reine Abnahme-Automatisierung, keine sichtbare Verhaltensänderung). |

### Protokoll-Commits über dem Kandidaten

Diese Commits liegen **außerhalb** des Fensters `v2.7.0..<Kandidat>` und sind
deshalb nicht Teil der Tabelle oben. Sie berühren ausschließlich Protokoll-Pfade,
verschieben den Kandidaten also nicht (`verify_release_freeze.py` weist sie als
„+N Protokoll-Commit(s) darüber" aus):

- **Freeze-Nachtrag für den #720-Kandidaten** (PR #721, zwei Commits): trägt
  den vollen 40-stelligen SHA von PR #720 nach, klassifiziert `aa4369d`
  (#710 via PR #714), `b90d92a` (#717), `07de38f` (#718) und `dcdeeec` (#719)
  als Protokoll sowie `f8143db` (#720) als (zu diesem Zeitpunkt) neuen
  Kandidaten in der Tabelle, aktualisiert die Fensterzahl 21 → 26 und die
  Gate-Nachweise; der zweite Commit korrigiert zwei Codex-Reviewbefunde
  derselben PR (veraltete „aktueller Kandidat"-Markierung bei #715,
  überzogener Anspruch zur artefaktgebundenen 2.7.0-Prüfung).
- **Fortführung dieses Nachtrags für den Kandidatenwechsel durch #722**
  (PR #721, dritter Commit): trägt den vollen 40-stelligen SHA von PR #722
  nach, wandelt die vorherige `Kandidaten-Commit`-Platzhalterzeile für #720
  in eine Zeile mit vollem SHA um, ergänzt eine neue Zeile für #722,
  aktualisiert die Fensterzahl 26 → 27 und die Gate-Nachweise; ändert
  ebenfalls nur `docs/history/RELEASE-2.7.1-scope-freeze.md`.
- **Freeze-Nachtrag für den #723-Kandidaten** (PR #724): trägt den
  vollen 40-stelligen SHA von PR #723 nach, wandelt die vorherige
  `Kandidaten-Commit`-Platzhalterzeile für #722 in eine Zeile mit vollem SHA
  um, klassifiziert `c9fb5cd` (#721, Fortführungs-Nachtrag) als Protokoll
  und ergänzt eine neue Zeile für #723, aktualisiert die Fensterzahl
  27 → 29 und die Gate-Nachweise; ändert ebenfalls nur
  `docs/history/RELEASE-2.7.1-scope-freeze.md`.
- **Freeze-Nachtrag für den #725-Kandidaten** (dieser Commit): trägt den
  vollen 40-stelligen SHA von PR #725 nach, wandelt die vorherige
  `Kandidaten-Commit`-Platzhalterzeile für #723 in eine Zeile mit vollem SHA
  um, klassifiziert `d0f8ea2` (#724, Freeze-Nachtrag) als Protokoll und
  ergänzt eine neue Zeile für #725, aktualisiert die Fensterzahl 29 → 31
  und die Gate-Nachweise; ändert ebenfalls nur
  `docs/history/RELEASE-2.7.1-scope-freeze.md`.

Die zuvor hier geführten Protokoll-Commits (`5c25e3b`, `ac05363`, `1b04887`,
`0b021cc`, `aa4369d`, `c9fb5cd`, `d0f8ea2`) liegen seit dem Kandidatenwechsel
durch #711 bzw. #720 bzw. #723 bzw. #725 **im** Fenster und stehen in der
Klassifizierungstabelle oben.

**Zur Squash-Historie:** PR #701 wurde als **Squash** eingebracht. Die sechs
Zweig-Commits (`bba18044755c…`, `09a328863e6a…`, `ad63e362062a…`,
`24fe4cc56af9…`, `f06a9cba01ce…`, `a97e5a12a6e3…`) existieren auf `main` nicht
mehr und stehen deshalb nicht in der Klassifizierungstabelle – sie bildet exakt
das Fenster `v2.7.0..<Kandidat>` ab. Ihr Inhalt steckt vollständig im
Kandidaten; ihre Entstehung ist unten unter „Historie der Kandidatenwechsel"
und in PR #701 nachvollziehbar. Das ist der in der Freeze-Regel vorgesehene
Merge-Fall: der Squash wurde zum abgeleiteten Kandidaten, war freeze-äquivalent
zum geprüften Zweigstand, und dieser Protokoll-Commit zieht den SHA nach.

### Abgrenzung „opportunistisches Refactoring" vs. `45ebac3929b8…`

Das Freeze-Kriterium schließt Feature-Erweiterungen und opportunistische
Refactorings aus einem Patch-Release aus, sofern sie nicht ausdrücklich mit
Risikoentscheidung freigegeben werden. `45ebac3929b8520a650b00abd1ce7ec722cd3cda`
fällt nicht unter „opportunistisches Refactoring" im problematischen Sinn (Umbau
lebender Logik, geänderte Kontrollflüsse, neue Abstraktionen), sondern ist reine
Entfernung toter, unreferenzierter Symbole – nachweislich ohne Aufrufer im
gesamten Repository (vulture + manuelle Verifikation) und mit grüner Vollsuite
vor/nach dem Commit. Risikoentscheidung: **aufnehmen**, weil das Risiko eines
stillen Verhaltensunterschieds hier nicht höher liegt als bei den übrigen
Dokumentations-Commits, während ein nachträglicher Revert (Cherry-Pick-Historie,
neuer Freeze-Commit) mehr Risiko einführen würde als er vermeidet.

### Scope-Ausnahme für `ac053638c1d8…` (#708)

Das Freeze-Kriterium erlaubt kandidatenrelevante Nachfreeze-Commits nur, wenn
sie „nachweislich einen Regressionsfund in einer release-relevanten Prüfung …
oder eine Sicherheitslücke" beheben. `ac053638c1d81864043798a55bf41e4fb4c877c6`
(#708) erfüllt das wörtlich **nicht**: es korrigiert eine falsche
Tab-Zuordnung in der Architekturbeschreibung von `README.md` (alle sechs
Sprachen) – eine reine Dokumentationskorrektur ohne Bezug zu einer
release-relevanten Prüfung oder Sicherheitslücke.

Der Commit ist trotzdem Teil der Kandidatenlinie: er liegt bereits auf der
Mainline zwischen dem vorherigen und dem aktuellen Kandidaten, first-parent
eingebettet. Ihn nachträglich auszuschließen, hieße, ihn zu reverten – das
wäre selbst ein neuer kandidatenrelevanter Commit und würde den Kandidaten
ein weiteres Mal verschieben, ohne das eigentliche Ziel (ein sauberer 2.7.1
ohne #708) zu erreichen, solange #708 nicht vor #711 aus der Historie entfernt
wird.

Risikoentscheidung: **aufnehmen, mit derselben Begründung wie bei
`45ebac3929b8…` oben.** Reine Textkorrektur in sechs README-Dateien, keine
Code-, Verhaltens- oder Formatänderung, PR-CI grün, kein Bezug zu einer
Sicherheitslücke. Das Risiko eines stillen Verhaltensunterschieds ist nicht
höher als bei den übrigen Dokumentations-Commits in diesem Fenster; ein
Revert vor dem Tag würde mehr Risiko (neue Kandidatenrunde, Cherry-Pick-
Historie) einführen, als er vermeidet. Diese Ausnahme ist damit explizit
dokumentiert, nicht stillschweigend über die Klassifizierungstabelle
mitgelaufen.

## Versionssynchronisierung

Alle Versionsquellen melden am Kandidaten konsistent `2.7.1` – maschinell
geprüft (`verify_release_freeze.py`, Codes `pyproject-version`,
`changelog-section`, `appstream-release`, `license-versions`):

- `pyproject.toml` (`[project].version`) – die kanonische Quelle.
- `CHANGELOG.md` + alle fünf Übersetzungen (`docs/i18n/*/CHANGELOG.md`):
  `[2.7.1] – 2026-07-26`, leerer `[Unreleased]`-Abschnitt bleibt darüber
  bestehen.
- `LICENSES.md` + alle fünf Übersetzungen: Titelzeile `… – bgremover 2.7.1` und
  Datumsangabe (Dependency-Datenbasis unverändert – kein Commit im Fenster
  ändert Laufzeit- oder Build-Abhängigkeiten).
- `packaging/linux/de.bgremover.app.metainfo.xml`:
  `<release version="2.7.1" date="2026-07-26"/>` vor dem `2.7.0`-Eintrag; Datum
  und CHANGELOG-Datum werden gegeneinander geprüft.

`bgremover.__version__` liest `pyproject.toml` zur Laufzeit (bzw. die
Paket-Metadaten nach Installation) – kein weiterer Ort im Code hält die Version
separat vor (siehe `tests/test_version.py`). Die sichtbare „Über"-Anzeige und
alle Build-/Paketnamen (`BgRemover-2.7.1-<platform>…`) leiten sich transitiv aus
derselben Quelle ab.

**Bewusst nicht geändert:** Die Kopfzeile „Letzter Release-Stand" in `CLAUDE.md`
bleibt bei `v2.7.0`. Sie dokumentiert den zuletzt tatsächlich **getaggten und
veröffentlichten** Stand, nicht den in Vorbereitung befindlichen Kandidaten.
Tag und Veröffentlichung sind Aufgabe von #686; dort wird diese Zeile zusammen
mit dem tatsächlichen Tag aktualisiert.

## Update-Metadaten / Release-Konfiguration

`app_update.py` bezieht die installierte Version ausschließlich über
`bgremover.__version__` (→ `pyproject.toml`) und vergleicht sie mit der
GitHub-Releases-API zur Laufzeit; es gibt keine separat gepflegte
Versionskonstante, die von `2.7.1` abweichen könnte.
`.github/workflows/release-linux.yml` verifiziert bei der Tag-Erstellung (#686)
`GITHUB_REF_NAME` gegen `pyproject.toml`
(`tests/test_release_gate.py::test_release_verifies_tag_matches_project_version`)
– ein Tag `v2.7.1`, der nicht exakt zu `project.version` passt, schlägt dort
fehl, statt eine widersprüchliche Version zu veröffentlichen.

## Release Notes – jetzt im CHANGELOG selbst

Der Release-Workflow veröffentlicht **ausschließlich** den aus `CHANGELOG.md`
extrahierten `[2.7.1]`-Abschnitt (`scripts/extract_release_notes.py`,
`--notes-file`). Ein ausführlicher Entwurf, der nur in diesem Dokument steht,
erreicht die Releases-Seite also nie – genau das hat #699 beanstandet.

Konsequenz: Die in #683 verlangten anwenderorientierten Angaben stehen jetzt im
CHANGELOG-Abschnitt `[2.7.1]` selbst, im Unterabschnitt „Hinweise zu diesem
Release", in allen sechs Sprachen:

- **Auswirkung** – reines Patch-Release, ausschließlich zwei Fehlerbehebungen
  der optionalen 3D-Reliefvorschau: der GPU-Leak-Fix aus PR #676 und die
  GL-Puffer-Fehlererkennung aus #711 (Squash-Merge PR #713, seit #710 der
  Kandidat); keine neuen Funktionen, kein geändertes Bild-/Projekt-/
  Exportverhalten.
- **Betroffene Anwender:innen** – nur Nutzer:innen der 3D-Reliefvorschau; die
  beobachtbaren Symptome (wachsender GPU-Speicherbedarf bei wiederholtem
  2D↔3D-Wechsel; auf problematischen Treibern eine leere „bereite" 3D-Ansicht
  statt eines sichtbaren Fehlerzustands mit 2D-Rückfall) sind benannt.
- **Upgrade-Relevanz** – empfohlen für 3D-Nutzer:innen, sonst optional; kein
  Migrationsschritt, `.bgrproj`/Exportformate/Einstellungen unverändert
  kompatibel (auch abwärts).
- **Bekannte Einschränkungen** – keine neuen gegenüber 2.7.0; die Langzeit-/
  Speichermessung unter echtem GL-Kontext ist separat als #684 erfasst, die
  verschärfte False-Green-Abwehr der GL-Sonde in
  [`RELEASE-2.7.1-gl-langzeittest.md`](RELEASE-2.7.1-gl-langzeittest.md).

Diese Zusammenfassung spiegelt den Unterabschnitt „Hinweise zu diesem Release"
in `CHANGELOG.md` (`[2.7.1]`) wider, der beide Fixes im „Behoben"-Abschnitt
darüber gemeinsam als „das oben genannte" fasst – dort namentlich nicht auf
PR #676 beschränkt. Eine Änderung an `CHANGELOG.md` selbst ist kandidatenrelevant
und daher nicht Teil dieses Protokoll-Nachtrags.

`tests/test_release_freeze.py` prüft, dass der **tatsächlich erzeugte**
Release-Body (Ausgabe von `extract_release_notes.py`) diese vier Angaben in
allen sechs Sprachen enthält – ein Entfernen fällt sofort auf, statt erst auf
der Releases-Seite.

## Freeze-Regel und Verfahren für Änderungen nach dem Freeze

- **Freeze-Kriterium:** Ab dem protokollierten Kandidaten-Commit fließen keine
  kandidatenrelevanten Commits mehr in den 2.7.1-Kandidaten ein, außer sie
  beheben nachweislich einen Regressionsfund in einer release-relevanten
  Prüfung (`make check`, `make ui`, `make release-freeze-check`,
  `tests/test_release_gate.py`, `tests/test_ci_qt_packages.py` u. ä.) oder eine
  Sicherheitslücke.
- **Kandidatenrelevante Nachfreeze-Änderung:** erzeugt einen **neuen
  Kandidaten** und erzwingt die vollständige Wiederholung dieses Dokuments
  (neue Tabelle mit vollen SHAs, neue Fensterzahl, erneute
  Versionssynchronisierungsprüfung, erneutes `make check` +
  `make release-freeze-check` auf dem neuen Kandidaten, neuer Protokoll-Eintrag).
  Korrektur per Edit **dieser** Datei, nicht per neuer Datei – die Historie
  bleibt in einer Datei nachvollziehbar.
- **Protokoll-Commit (erlaubte Ausnahme):** Ein Commit, der ausschließlich
  Protokoll-Pfade berührt (Pfadklassen oben), verschiebt den Kandidaten nicht.
  Genau ein solcher Commit trägt nach dem Kandidaten-Commit den vollen
  40-stelligen SHA im Protokollfeld nach (plus Gate-Nachweise). Er wird unter
  „Protokoll-Commits über dem Kandidaten" geführt – nicht in der
  Klassifizierungstabelle, die genau das Fenster `v2.7.0..<Kandidat>` abbildet.
  Protokoll-Commits *innerhalb* des Fensters gehören dagegen in die Tabelle;
  `verify_release_freeze.py` meldet dort fehlende Einträge als Warnung.
- **Einbringen nach `main`:** Entsteht beim Merge ein neuer Commit
  (Merge-/Squash-Commit), wird dieser zum abgeleiteten Kandidaten. Ist sein
  kandidatenrelevanter Baum identisch zum protokollierten Kandidaten, ist das
  **kein** Freeze-Bruch: `verify_release_freeze.py` meldet
  `candidate-sha-equivalent`. Ohne `--require-pin` ist das eine Warnung (der
  normale Übergang), **mit** `--require-pin` – also im Release-Gate – ein
  Fehler: gebaut und getaggt wird nur der exakt protokollierte SHA, sonst
  weichen Dokument und Artefakt wieder auseinander. Ein Protokoll-Commit auf
  `main` zieht den SHA nach. Weicht der Inhalt ab, ist es ein Fehler
  (`candidate-sha-mismatch`) und die vollständige Wiederholung greift.
- **Tag/Build-SHA-Vertrag (#686/#685):** Der Tag `v2.7.1` bzw. ein manueller
  `workflow_dispatch`-Kandidatenbau darf nur auf einem Commit laufen, für den
  `make release-freeze-check` (mit `--require-pin`) fehlerfrei läuft – also
  auf dem protokollierten Kandidaten selbst **oder** einem reinen
  Protokoll-Commit darüber (z. B. diesem Freeze-Nachtrag). Technisch
  erzwungen über den Job `verify-tag`
  (`.github/workflows/release-linux.yml`): er führt das Gate bei jedem
  Tag-Push und jedem manuellen Kandidatenbau aus, bevor gebaut oder
  veröffentlicht wird. Fehlt das Freeze-Dokument der getaggten Version oder
  weicht der abgeleitete vom dokumentierten Kandidaten ab, bricht das Gate
  bewusst ab (fail-closed) – ein Release ohne dokumentierten Freeze ist damit
  unmöglich.

  **Kurzzeitig (#709, wieder entfernt durch #715):** ein zusätzlicher Schritt
  erzwang exakte Gleichheit `github.sha ==
  $(verify_release_freeze.py --print-candidate)` und verbot damit
  ausgerechnet den Fall oben (Build/Tag auf einem Protokoll-Commit über dem
  Kandidaten). Das machte jeden Kandidatenbau strukturell unmöglich: ein
  Freeze-Dokument kann seinen eigenen Commit-SHA nicht enthalten, also pinnt
  der Kandidaten-Commit selbst immer noch den *vorherigen* Kandidaten und
  scheitert an `--require-pin`; der nachträgliche Protokoll-Commit, der den
  Pin einträgt, scheiterte dann am neuen `github.sha`-Abgleich. Gefunden bei
  der Codex-Review von PR #714, behoben durch PR #715 (siehe
  Kandidatenwechsel 8. unten).
- **Basis-Tag:** Die Basis ist mit ihrem vollen SHA eingefroren (oben in der
  Zeile „Basis-Tag"). Ein Tag ist verschiebbar: zeigte `v2.7.0` nachträglich auf
  einen Geschwister-Commit mit demselben Parent, entstünde dasselbe
  `base..head`-Fenster, während alle Prüfungen gegen die falsche Basis liefen.
  `verify_release_freeze.py` vergleicht deshalb den aufgelösten Tag mit dem
  eingefrorenen SHA und verlangt zusätzlich, dass die Basis ein Vorfahr des
  geprüften Commits ist.
- **Zweite Prüfung:** Die Korrektur wird als Pull Request zu #699 eingereicht
  und braucht **mindestens eine eingereichte, unabhängige GitHub-Review** auf
  dem finalen Korrektur-Commit (bei #698 fehlte genau dieser Nachweis). Der
  Review-Link wird in #699 hinterlegt, bevor #685/#686 starten.

## Gate-Nachweise

Alle Läufe erfolgen auf dem Kandidaten-Commit
`480a5fc0008ded401b02b15373d8474d67c83382` (bzw. auf dem inhaltsgleichen
Zweigstand `5e7b7e30baa5…` vor dem Squash), lokal unter Linux mit Python 3.12
und `QT_QPA_PLATFORM=offscreen` (nicht-editable Installation aus
`pyproject.toml` + `requirements/constraints.txt`).

| Prüfung | Lauf/Ergebnis |
|---|---|
| `make check` (ruff + mypy + pytest-Default-Set) | grün: ruff „All checks passed", mypy „no issues found in 69 source files", pytest **2042 passed, 5 skipped, 14 deselected** |
| `python scripts/verify_release_freeze.py` (auf `main`) | 0 Fehler, 0 Warnungen; abgeleiteter Kandidat == protokollierter SHA, „11 Commits vollständig klassifiziert", Basis-Tag gegen den eingefrorenen SHA geprüft, Versionsquellen, Release-Body und alle sechs Datumszeilen ok |
| Merge-Übergang (Squash von PR #701) | vor diesem Protokoll-Commit meldete das Werkzeug `candidate-sha-equivalent` – identischer kandidatenrelevanter Baum, abweichender SHA. Genau das von der Freeze-Regel vorhergesagte Verhalten; unter `--require-pin` ein Fehler, bis der SHA nachgezogen ist |
| `make release-freeze-check` (`--require-pin`) | ohne Fehler, nachdem der Protokoll-Commit den SHA nachgetragen hat |
| Flacher Klon (`git clone --depth 1`) | `tests/test_release_freeze.py` grün, der git-Test meldet sich dort als *skipped* |
| Negativkontrolle Rename-Erkennung | `git mv bgremover/x.py docs/history/x.py` in einem Mini-Repository: `git diff --name-only` meldet nur das Ziel, `--no-renames` beide Seiten – der Commit ist damit korrekt kandidatenrelevant |
| PR-CI von #701 auf `a97e5a12a6e3…` | alle 16 Checks grün bzw. übersprungen (Lightweight PR checks, CodeQL/Analyze, license-check, pip-audit 3.10/3.12, review, license summary) |
| release-relevante Einzeltests: `tests/test_release_freeze.py`, `tests/test_release_gate.py`, `tests/test_changelog_metadata.py`, `tests/test_licenses_version.py`, `tests/test_version.py`, `tests/test_i18n_docs.py`, `tests/test_markdown_links.py` | grün (Teil des `make check`-Laufs oben) |

| Prüfung auf dem #684-Kandidaten (Zweig `claude/github-issue-684-jume86`) | Lauf/Ergebnis |
|---|---|
| `make check` | grün: ruff „All checks passed", mypy „no issues found in 70 source files", pytest **2069 passed, 6 skipped, 14 deselected** |
| `make ui` | grün: **20 passed** |
| `make coverage` (`fail_under = 86`) | grün: **93 %** |
| `make gl-stress` (120 Zyklen) und Langlauf (1000 Zyklen) | Exit 0, Urteil `ok`; lebende GL-Objekte konstant, erzeugt == freigegeben, 0 nach dem Aufräumen (Zählerstände im Testbericht) |
| `python scripts/verify_release_freeze.py` (auf `main`, vor diesem Protokoll-Commit) | 0 Fehler, 1 Warnung `candidate-sha-unpinned`; abgeleiteter Kandidat `65a656aa4141…`, „15 Commits vollständig klassifiziert" |
| `make release-freeze-check` (`--require-pin`, nach diesem Protokoll-Commit) | 0 Fehler, 0 Warnungen – der Freeze ist wieder abnahmefähig |
| PR-CI von #706 auf `973a7034f3c2…` | alle 12 Checks grün bzw. übersprungen (Lightweight PR checks, CodeQL/Analyze, license-check, pip-audit 3.10/3.12, review, license summary); beide Codex-Befunde (falsches Grün bei fehlgeschlagenem GL-Viewer, nicht erzwungene Mindestzyklen) vor dem Merge behoben |

| Prüfung auf dem #711-Kandidaten (Zweig `claude/github-issue-711-p4ru14`, PR #713) | Lauf/Ergebnis |
|---|---|
| `make check` | grün: ruff „All checks passed", mypy „no issues found in 70 source files", pytest **2082 passed, 6 skipped, 14 deselected** |
| `make ui` | grün: **20 passed** |
| `make coverage` (`fail_under = 86`) | grün: **93 %** |
| `make gl-stress` | Exit 0, Urteil `ok` |
| Neue Regressionstests `tests/test_viewer_3d_gl_lifecycle.py` (9 Fälle) | decken `create()==false`, `bind()==false`, Teilerfolg (genau eine Freigabe je Objekt), 110 wiederholte Fehlschläge ohne Restbestand, 110 Reuploads im Erfolgsfall, sowie die Sonden-Fälle (Fake-Modus meldet Befund, CLI liefert Exit 1, `--mode gl` liefert `ProbeNotExecutable`/Exit 2) ab; alle grün |
| `python scripts/verify_release_freeze.py --print-candidate` (auf `main`, vor diesem Protokoll-Commit) | `5e947ee816a2d481fa6ea901790281293aced4d5` |
| `make release-freeze-check` (auf `main`, vor diesem Protokoll-Commit) | 5 Fehler, 2 Warnungen (`candidate-sha-mismatch` gegen den alten Pin `65a656aa…`, `commit-count-mismatch` 20 vs. 15, drei `unclassified-candidate-commit` für #706/#708/#709, zwei `unclassified-protocol-commit`-Warnungen für #707/#712 – exakt der erwartete Zustand vor dem Nachtrag) |
| `make release-freeze-check` (`--require-pin`, nach diesem Protokoll-Commit) | 0 Fehler, 0 Warnungen – der Freeze ist wieder abnahmefähig |
| PR-CI von #713 auf `6415e91c15da…` | alle Checks grün (Lightweight PR checks/PR CI, CodeQL, License Check, Dependency Audit, Claude Code Review); ein Codex-Reviewbefund vor dem Merge behoben (Buchung/Aufräumen/Zyklenzahl, Folgecommit `6415e91`) |

| Prüfung auf dem #715-Kandidaten (Zweig `claude/github-issue-710-release-gate-fix`, PR #715) | Lauf/Ergebnis |
|---|---|
| `make check` (auf dem Fix-Zweig, Basis `main` = `5e947ee816a2…`) | grün: ruff „All checks passed", mypy „no issues found in 70 source files", pytest **2082 passed, 6 skipped, 14 deselected** |
| `tests/test_release_gate.py::test_freeze_gate_allows_a_protocol_commit_above_the_candidate` | grün – ersetzt den #709-Test, der den `github.sha`-Abgleich forderte; stellt sicher, dass er nicht wieder eingeführt wird |
| `python scripts/verify_release_freeze.py --require-pin` (auf `main`, vor diesem Protokoll-Nachtrag) | scheitert weiterhin mit dem bekannten Pre-Nachtrag-Mismatch (Dokument pinnt `5e947ee…`, abgeleitet ist `adb220596061…`) – erwartet, PR #715 trägt den Freeze-Pin bewusst nicht selbst nach |
| PR-CI von #715 | grün |
| `make release-freeze-check` (`--require-pin`, nach diesem Protokoll-Nachtrag) | 0 Fehler, 0 Warnungen – der Freeze ist wieder abnahmefähig |

| Prüfung auf dem #720-Kandidaten (Zweig `claude/github-issue-685-lob9a4`, PR #720) | Lauf/Ergebnis |
|---|---|
| `make check` (auf dem Zweig, Basis `main` = `adb2205960619…`) | grün: ruff „All checks passed", mypy „no issues found in 71 source files", pytest **2099 passed, 6 skipped, 14 deselected** |
| Unabhängige Codex-Review auf PR #720 | 2× P1, 1× P2 – vor dem Merge vollständig behoben: (1) das Fixture aktiviert die COLOR- statt der HEIGHT-Ebene, `apply_height_op()` war dadurch ein stiller No-op und das folgende Undo bewies nichts – jetzt Höhenebene aktivieren und die Hash-Änderung vor dem Undo verifizieren; (2) der Struktur-/Migrationstest verglich nur Kind/Rolle/Flags/physische Größe, nicht IDs/Namen/vollständige Metadaten/Schemaversion – jetzt vollständiger Feldvergleich gegen die beim Fixture-Bau protokollierten Werte; (3) beide neuen Prüfungen liefen nur gegen den Source-Checkout, nicht gegen das gepackte Kandidatenartefakt – neuer Hook `bgremover/acceptance_smoke.py` (analog `screenshot3d.py`/`BGREMOVER_SCREENSHOT_3D`) bindet sie zusätzlich an den laufenden, gepackten Prozess. |
| `python scripts/verify_release_freeze.py --require-pin` (auf `main`, vor diesem Protokoll-Nachtrag) | 3 Fehler, 4 Warnungen (`candidate-sha-mismatch` gegen den alten Pin `adb220596061…`, `commit-count-mismatch` 26 vs. 21, ein `unclassified-candidate-commit` für #715, vier `unclassified-protocol-commit`-Warnungen für #719/#718/#717/#714 – erwarteter Zustand vor dem Nachtrag) |
| `make release-freeze-check` (`--require-pin`, nach diesem Protokoll-Nachtrag) | 0 Fehler, 0 Warnungen – der Freeze ist wieder abnahmefähig |

| Prüfung auf dem #722-Kandidaten (Zweig `claude/acceptance-smoke-v270-parity`, PR #722) | Lauf/Ergebnis |
|---|---|
| `make check` (auf dem Zweig, Basis `main` = `f8143db78991…`) | grün: pytest **2100 passed, 6 skipped, 14 deselected** (Prüftiefen-Erweiterung) bzw. **2101 passed** (nach den beiden Codex-Nachbesserungen unten) |
| Erste Codex-Reviewrunde auf PR #722 | 1× P1 – behoben: `_run_v270_project_smoke` verglich nur Ebenenkind/-rolle und Bearbeitbarkeit, nicht IDs/Namen/Metadaten/Version/Pixel-Payload gegen die Fixture-Referenz; jetzt vollständiger Feldvergleich analog `tests/test_project_v270_upgrade.py`, plus Negativtest mit einem strukturell identischen, frisch generierten „Lookalike"-Projekt. |
| Zweite Codex-Reviewrunde auf PR #722 | 2× P1 – behoben: (1) der Versionscheck prüfte `project.version` (das separate, immer-1 `project_version`-Feld) statt der tatsächlichen `.bgrproj`-Manifest-Formatversion – jetzt liest der Hook `manifest["version"]` direkt aus der Fixture-ZIP und vergleicht sie mit dem im gepackten Prozess geltenden `PROJECT_FORMAT_VERSION`; (2) `visible`/`opacity`/`locked`/`active_layer_id` fehlten – jetzt ergänzt, mit Regressionstest für das genannte Beispiel (Farb-Ebenen-Deckkraft 1.0 → 0.5 bei sonst identischen IDs). |
| `python scripts/verify_release_freeze.py --require-pin` (nach Rebase auf den #722-Merge, vor diesem Protokoll-Nachtrag) | 3 Fehler (`candidate-sha-mismatch` gegen den alten Pin `f8143db78991…`, `commit-count-mismatch` 27 vs. 26, ein `unclassified-candidate-commit` für #720 – erwarteter Zustand vor dem Nachtrag) |
| `make release-freeze-check` (`--require-pin`, nach diesem Protokoll-Nachtrag) | 0 Fehler, 0 Warnungen – der Freeze ist wieder abnahmefähig |

| Prüfung auf dem #723-Kandidaten (Zweig `claude/acceptance-smoke-export-dir-collision`, PR #723) | Lauf/Ergebnis |
|---|---|
| `make check` (auf dem Zweig, Basis `main` = `c9fb5cd96d08…`) | grün: pytest **2102 passed, 6 skipped, 14 deselected** |
| Echter Hardware-Abnahmelauf gegen den #722-Kandidaten (Raspberry Pi 5, `release-abnahme.yml`-Run 30492821131) | AppImage: `acceptance_extra` ok; **.deb: `acceptance_extra` fehlgeschlagen** (`write_export fehlgeschlagen: <Pfad>`, `ExportTargetExistsError`) – erster echter Hardware-Fund des neuen Zusatznachweises aus #720/#722, siehe Ursache/Fix in der Tabellenzeile oben. macOS arm64 lief zeitgleich vollständig durch. |
| Regressionstest `test_run_acceptance_extra_twice_in_same_evidence_dir_does_not_collide` | reproduziert das exakte Szenario (zwei `run_acceptance_extra`-Aufrufe, gemeinsamer `evidence_dir`, unterschiedliche Artefaktklassen); grün nach dem Fix |
| PR-CI von #723 | grün |
| `python scripts/verify_release_freeze.py --require-pin` (auf `main`, vor diesem Protokoll-Nachtrag) | 3 Fehler, 1 Warnung (`candidate-sha-mismatch` gegen den alten Pin `9845147ea708…`, `commit-count-mismatch` 29 vs. 27, ein `unclassified-candidate-commit` für #722, eine `unclassified-protocol-commit`-Warnung für #721 – erwarteter Zustand vor dem Nachtrag) |
| `make release-freeze-check` (`--require-pin`, nach diesem Protokoll-Nachtrag) | 0 Fehler, 0 Warnungen – der Freeze ist wieder abnahmefähig |

| Prüfung auf dem #725-Kandidaten (Zweig `claude/issue-685-automation-follow-up`, PR #725) | Lauf/Ergebnis |
|---|---|
| `make check` (auf dem Zweig, Basis `main` = `d0f8ea277ddd1…`) | grün: ruff „All checks passed", mypy „no issues found in 71 source files", pytest **2108 passed, 6 skipped, 14 deselected** |
| Codex-Reviewrunde auf PR #725 | 1× P1, 2× P2 – vor dem Merge vollständig behoben: (1) Homebrews `freshclam.conf.sample` trägt eine aktive `Example`-Direktive, die `freshclam` auf einem sauberen macOS-Runner als unkonfiguriert ablehnt – die Direktive wird jetzt entfernt und ein expliziter Datenbank-Präsenz-Check läuft vor `clamscan`, damit eine fehlende Datenbank klar fehlschlägt statt mit `clamscan`s mehrdeutigem Exit-Code 2; (2) die E2E-/Live-GL-Zeilen der Abschlussmatrix zeigten bei einem UTC-Datumswechsel während des Jobs das Datum der (früher erzeugten) Plattform-Evidenz statt ihres eigenen `erzeugt_am`/`timestamp` – jetzt liest jede Zeile ihr eigenes Zeitstempelfeld, mit Fallback auf die Plattform-Evidenz nur wenn das Ergebnis selbst keinen trägt; (3) ein reiner Fehlschlag der neuen Fehlende-Komponente-Prüfung blieb im Job-Log unsichtbar, weil der Hook nur zwei der drei Meldungen druckte – jetzt werden alle drei gedruckt. |
| `python scripts/verify_release_freeze.py --require-pin` (auf `main`, vor diesem Protokoll-Nachtrag) | 3 Fehler, 1 Warnung (`candidate-sha-mismatch` gegen den alten Pin `e65e9380c016…`, `commit-count-mismatch` 31 vs. 29, ein `unclassified-candidate-commit` für #723, eine `unclassified-protocol-commit`-Warnung für #724 – erwarteter Zustand vor diesem Nachtrag) |
| `make release-freeze-check` (`--require-pin`, nach diesem Protokoll-Nachtrag) | 0 Fehler, 0 Warnungen – der Freeze ist wieder abnahmefähig |

Historie der Kandidatenwechsel (jeder nach der Freeze-Regel vollständig
wiederholt, keiner still nachgezogen):

1. `bba18044755cf27e53f4505a297f33349e67091a` – Freeze-Korrektur; lokal grün,
   PR-CI rot (git-Test nicht flach-klon-tauglich).
2. `ad63e362062acebe41fa04ae50b9376923cfd9d8` – Nachfreeze-Fix dazu; PR-CI grün.
3. `f06a9cba01ce3b3b013461e383cd5931e17b1144` – Reviewkorrektur (erste
   Codex-Runde): Ableitung `--first-parent`, Release-Body-Extraktor vom
   geprüften Commit, `--require-pin` verlangt exakte SHA-Übereinstimmung.
4. `5e7b7e30baa500c4dd3c640eb3b1e7a238044994` – Reviewkorrektur (zweite
   Codex-Runde): `--no-renames` in der Pfadklassifizierung, eingefrorener
   Basis-SHA statt bloßem Tag-Namen, Freeze-Gate als harte Vorbedingung im
   Release-Workflow, Datumsprüfung aller sechs CHANGELOGs.
5. `480a5fc0008ded401b02b15373d8474d67c83382` – Squash-Merge von PR #701 auf
   `main`. Kein inhaltlicher Wechsel: derselbe
   kandidatenrelevante Baum wie 4., nur ein neuer SHA durch das Einbringen.
6. **Kandidatenwechsel durch #684** (GL-Ressourcen-/Langzeittest, Squash-Merge
   von PR #706, `65a656aa4141…`): erste kandidatenrelevante Änderung nach dem
   Freeze. Fiel unter die in der Freeze-Regel vorgesehene Ausnahme (Nachweis-
   und Regressionsarbeit an einer release-relevanten Prüfung) und wurde
   deshalb nicht abgelehnt, sondern nach dem vorgeschriebenen Verfahren
   vollständig nachgezogen: Tabelle um die drei zuvor darüber liegenden
   Protokoll-Commits und den neuen Kandidaten ergänzt, Fensterzahl 11 → 15,
   Kandidaten-SHA auf `nachzutragen` zurückgesetzt, Gate-Nachweise wiederholt.
   Der Protokoll-Commit #707 (`5c25e3b71f6b…`) trug den SHA nach.
7. **Kandidatenwechsel durch #711** (GL-Puffer-Fehlererkennung, Squash-Merge
   von PR #713, `5e947ee816a2…`): kandidatenrelevantes Follow-up zu #684 – ein
   stiller Fehlschlag von `QOpenGLBuffer.create()`/`bind()` konnte ein
   falsches `verdict: ok` in der GL-Sonde erzeugen (siehe Tabelle oben).
   Zwischen dem alten und dem neuen Kandidaten liegen zusätzlich zwei weitere
   kandidatenrelevante Commits (#708 README-Korrektur, #709 CI-Härtung des
   Build-/Tag-SHA-Vertrags) sowie zwei reine Protokoll-Commits (#707, #712),
   die alle nach dem vorgeschriebenen Verfahren vollständig in die Tabelle
   nachgezogen wurden: Fensterzahl 15 → 20, Kandidaten-SHA auf den neuen Stand
   gesetzt, Gate-Nachweise wiederholt, Tag-/Build-SHA-Vertrag-Text an die seit
   #709 erzwungene exakte Gleichheit `GITHUB_SHA == Kandidat` angepasst.
   Dieser Freeze-Nachtrag selbst (#710, PR #714) änderte ausschließlich
   Protokoll-/Statusdokumentation und verschob den Kandidaten nicht – wurde
   aber durch #715 (Punkt 8.) noch vor dem Merge überholt.
8. **Kandidatenwechsel durch #715** (Deadlock im Freeze-Gate aufgelöst,
   `adb2205960619…`, **nicht mehr aktueller Kandidat, seit dem
   Kandidatenwechsel durch #720 im Fenster**): Codex-Review auf PR #714 (P1)
   deckte auf, dass #709s exakter `GITHUB_SHA == Kandidat`-Abgleich jeden
   künftigen Kandidatenbau strukturell unmöglich machte (siehe „Tag/Build-
   SHA-Vertrag" oben) – #685/#686 wären für 2.7.1 blockiert gewesen. PR #715
   entfernt den #709-Schritt wieder; `--require-pin` allein bleibt
   ausreichend. Kandidatenrelevant über `.github/workflows/release-linux.yml`
   und `tests/test_release_gate.py`; erfüllt die Freeze-Ausnahme wörtlich
   (Regressionsfund in einer release-relevanten Prüfung – dem Freeze-Gate
   selbst). Nach dem vorgeschriebenen Verfahren vollständig nachgezogen:
   Fensterzahl 20 → 21, die vorherige `Kandidaten-Commit`-Platzhalterzeile für
   #711/#713 zu einer Zeile mit vollem SHA gewandelt, neue Zeile für #715
   ergänzt, Gate-Nachweise wiederholt, Tag/Build-SHA-Vertrag-Text auf den
   wiederhergestellten Vor-#709-Stand korrigiert. Dieser (fortgeführte)
   Freeze-Nachtrag (#710, PR #714) ändert weiterhin ausschließlich Protokoll-/
   Statusdokumentation und verschiebt den Kandidaten nicht.
9. **Kandidatenwechsel durch #720** (zwei fehlende Hardware-Abnahme-Nachweise
   für #685 ergänzt, `f8143db78991…`, **nicht mehr aktueller Kandidat, seit
   dem Kandidatenwechsel durch #722 im Fenster**): Die reale
   Hardware-Abnahme in #685 (macOS arm64 + Linux aarch64) deckte Start,
   GPU-Provenienz, nativen 3D-Viewer und Live-GL-Performance ab, ließ aber
   zwei Akzeptanzkriterien automatisiert unbelegt – Öffnen eines echten
   2.7.0-Projekts ohne unbeabsichtigte Migration/Datenänderung und einen
   EufyMake-Export-Smoke-Test. PR #720 schließt beide Lücken (siehe Tabelle
   oben) und erfüllt die Freeze-Ausnahme wörtlich: Nachweislückenfund in einer
   release-relevanten Prüfung (den eigenen Akzeptanzkriterien von #685).
   Zwischen dem alten und dem neuen Kandidaten liegen zusätzlich vier reine
   Protokoll-Commits (`aa4369d` Fortführung des #710-Nachtrags, `b90d92a`
   #717, `07de38f` #718, `dcdeeec` #719), die alle nach dem vorgeschriebenen
   Verfahren vollständig in die Tabelle nachgezogen wurden: Fensterzahl
   21 → 26, Kandidaten-SHA auf den neuen Stand gesetzt, Gate-Nachweise
   wiederholt. Dieser Freeze-Nachtrag selbst änderte ausschließlich
   Protokoll-/Statusdokumentation und verschiebt den Kandidaten nicht.
10. **Kandidatenwechsel durch #722** (`acceptance_smoke.py`s 2.7.0-Prüftiefe
    an den Source-Checkout-Test angeglichen, `9845147ea708…`, **nicht mehr
    aktueller Kandidat, seit dem Kandidatenwechsel durch #723 im Fenster**):
    Zwei Codex-Reviewrunden (auf PR #721 bzw. #722, siehe Tabelle
    oben) fanden die in #720 eingeführte artefaktgebundene 2.7.0-Prüfung
    strukturell schwächer als behauptet. PR #722 schließt die Lücke und
    erfüllt die Freeze-Ausnahme wörtlich: Nachweislückenfund in einer
    release-relevanten Prüfung (den eigenen Akzeptanzkriterien von #685).
    Kandidatenrelevant über `bgremover/**`, `tests/**`; kein weiterer
    Protokoll-Commit dazwischen. Nach dem vorgeschriebenen Verfahren
    vollständig nachgezogen: Fensterzahl 26 → 27, die vorherige
    `Kandidaten-Commit`-Platzhalterzeile für #720 zu einer Zeile mit vollem
    SHA gewandelt, neue Zeile für #722 ergänzt, Gate-Nachweise wiederholt.
    Dieser Freeze-Nachtrag (PR #721, fortgeführt) ändert weiterhin
    ausschließlich Protokoll-/Statusdokumentation.
11. **Kandidatenwechsel durch #723** (EufyMake-Exportordner-Kollision zwischen
    Artefaktklassen behoben, `e65e9380c016…`, **nicht mehr aktueller
    Kandidat, seit dem Kandidatenwechsel durch #725 im Fenster**): Der
    erste echte Hardware-Abnahmelauf gegen den #722-Kandidaten (Raspberry
    Pi 5) fand einen realen Bug im neuen `acceptance_extra`-Hook (siehe
    Tabelle oben) – AppImage bestand die Prüfung, das aus demselben Payload
    gebaute `.deb` scheiterte an einer Exportordner-Kollision. PR #723
    schließt die Lücke und erfüllt die Freeze-Ausnahme wörtlich:
    Regressionsfund in der release-relevanten Hardware-Abnahme selbst (#685).
    Kandidatenrelevant über `bgremover/**`, `tests/**`; ein Protokoll-Commit
    (`c9fb5cd`, PR #721) liegt dazwischen. Nach dem vorgeschriebenen Verfahren
    vollständig nachgezogen: Fensterzahl 27 → 29, die vorherige
    `Kandidaten-Commit`-Platzhalterzeile für #722 zu einer Zeile mit vollem
    SHA gewandelt, `c9fb5cd` klassifiziert, neue Zeile für #723 ergänzt,
    Gate-Nachweise wiederholt. Dieser Freeze-Nachtrag ändert ausschließlich
    Protokoll-/Statusdokumentation.
12. **Kandidatenwechsel durch #725** (drei weitere #685-Akzeptanzkriterien
    automatisiert – fehlende optionale Komponenten, Abschlussmatrix-Felder
    (Gerät/OS, Datum, Testperson, Link), Virenscan der gebauten Artefakte,
    `42807350cecf…`, **aktueller Kandidat**): Bei der Durchsicht der
    verbleibenden offenen #685-Akzeptanzkriterien identifiziert, die sich
    ohne Bezug zum Veröffentlichungs-Issue #686 automatisieren ließen (siehe
    Tabelle oben). PR #725 erfüllt die Freeze-Ausnahme wörtlich:
    Nachweislückenfund in den eigenen Akzeptanzkriterien von #685.
    Kandidatenrelevant über `bgremover/**`, `scripts/**`,
    `.github/workflows/**`; ein Protokoll-Commit (`d0f8ea2`, PR #724) liegt
    dazwischen. Nach dem vorgeschriebenen Verfahren vollständig
    nachgezogen: Fensterzahl 29 → 31, die vorherige
    `Kandidaten-Commit`-Platzhalterzeile für #723 zu einer Zeile mit vollem
    SHA gewandelt, `d0f8ea2` klassifiziert, neue Zeile für #725 ergänzt,
    Gate-Nachweise wiederholt. Dieser Freeze-Nachtrag ändert ausschließlich
    Protokoll-/Statusdokumentation.

Die Punkte 1.–4. liegen als Commits nicht mehr auf `main` (Squash); sie sind
über PR #701 einsehbar und hier bewusst als Entstehungsgeschichte protokolliert.

Hinweis zur Reproduktion: `tests/test_version.py::test_exported_version_matches_pyproject`
vergleicht `bgremover.__version__` mit `pyproject.toml`. In einer Umgebung, deren
Installation noch vom Stand vor dem Versionsschnitt stammt, meldet
`importlib.metadata` weiterhin `2.7.0` – vor dem Gate-Lauf also `pip install
--constraint requirements/constraints.txt ".[test]"` (bzw. `make install-test`)
ausführen. Das ist ein Umgebungs-, kein Kandidatenbefund.

Die PR-CI (`pr-ci.yml`) wiederholt Lint/Typecheck/Tests auf demselben Stand;
#685 wiederholt sie zusätzlich in der vollen Matrix gegen den protokollierten
SHA. Weicht der auf `main` abgeleitete Kandidat vom protokollierten SHA ab (z. B.
durch einen Merge-Commit), verlangt `--require-pin` den Protokoll-Nachtrag, bevor
gebaut oder getaggt wird.

## Verweise auf denselben Kandidaten

- **#680 (Epic):** führt 2.7.1; Freeze-Basis ist der hier protokollierte SHA.
- **#683:** Freeze-Ergebnis gilt erst mit dieser Korrektur als belastbar; die
  ursprüngliche Aussage zu `ba7e7cd` ist überholt.
- **#685 (Artefakte/Hardware-Abnahme):** baut ausschließlich gegen den hier
  protokollierten SHA; vor dem Build `make release-freeze-check` ausführen.
- **#686 (Tag/Veröffentlichung):** taggt denselben Stand (siehe Freeze-Regel,
  Punkt „Tag") und veröffentlicht den aus `CHANGELOG.md` extrahierten Body.
- **#699:** dieses Korrekturverfahren; der SHA und der Review-Link werden dort
  als Abschlussnachweis hinterlegt.
- **#684:** GL-Ressourcen-/Langzeitnachweis. **Nicht mehr unabhängig:** die
  Arbeit berührt `bgremover/**`, `tests/**`, `scripts/**`, `pyproject.toml` und
  das `Makefile` (Squash-Merge `65a656aa4141…`, PR #706; siehe
  Kandidatenwechsel 6.). Ergebnisse:
  [`RELEASE-2.7.1-gl-langzeittest.md`](RELEASE-2.7.1-gl-langzeittest.md).
- **#711:** GL-Puffer-Fehlererkennung. (Squash-Merge `5e947ee816a2…`, PR #713;
  siehe Kandidatenwechsel 7.) und ergänzt denselben Testbericht um die
  verschärfte False-Green-Abwehr. **Nicht mehr aktueller Kandidat**, seit dem
  Kandidatenwechsel durch #715 im Fenster.
- **#715:** Deadlock im Freeze-Gate aus #709 aufgelöst. (Squash-Merge
  `adb2205960619…`; siehe Kandidatenwechsel 8.) – ohne diesen Fix wären
  #685/#686 für 2.7.1 dauerhaft blockiert gewesen. **Nicht mehr aktueller
  Kandidat**, seit dem Kandidatenwechsel durch #720 im Fenster.
- **#710:** Freeze-Nachtrag (#714) – zieht zunächst den Kandidatenwechsel
  durch #711 vollständig nach, dann (in derselben PR #714, vor deren Merge)
  den Kandidatenwechsel durch #715; ändert selbst nur Protokoll-/
  Statusdokumentation.
- **#685 (zwei fehlende Hardware-Abnahme-Nachweise, PR #720):** Öffnen eines
  echten 2.7.0-Projekts und EufyMake-Export-Smoke, gefunden bei der
  Gegenprüfung der rohen Evidenz aus dem ersten Hardware-Abnahmelauf.
  (Squash-Merge `f8143db78991…`; siehe Kandidatenwechsel 9.). **Nicht mehr
  aktueller Kandidat**, seit dem Kandidatenwechsel durch #722 im Fenster.
- **#685 (Nachbesserung des artefaktgebundenen 2.7.0-Nachweises, PR #722):**
  Zwei Codex-Reviewrunden (auf PR #721 bzw. #722) fanden
  `bgremover/acceptance_smoke.py`s 2.7.0-Projektprüfung aus #720 strukturell
  schwächer als behauptet und als `tests/test_project_v270_upgrade.py` –
  fehlende IDs-/Namen-/Metadaten-/Versions-/Pixel-Vergleiche, eine falsch
  geprüfte Versionsangabe (`project.version` statt der tatsächlichen
  Manifest-Formatversion) sowie fehlende `visible`/`opacity`/`locked`/
  `active_layer_id`-Vergleiche. (Squash-Merge `9845147ea708…`; siehe
  Kandidatenwechsel 10.). **Nicht mehr aktueller Kandidat**, seit dem
  Kandidatenwechsel durch #723 im Fenster.
- **#721:** konsolidierter Freeze-Nachtrag für #720+#722 (Squash-Merge
  `c9fb5cd96d08…`) – ändert selbst nur Protokoll-/Statusdokumentation.
- **#685 (echter Hardware-Abnahme-Fund, PR #723):** Der erste echte
  Hardware-Abnahmelauf gegen den #722-Kandidaten (Raspberry Pi 5) fand eine
  EufyMake-Exportordner-Kollision zwischen Artefaktklassen (AppImage lief
  zuerst und legte den gemeinsam genutzten Ordner an, `.deb` scheiterte
  danach an `write_export`s `ExportTargetExistsError`). (Squash-Merge
  `e65e9380c016…`; siehe Kandidatenwechsel 11.). **Nicht mehr aktueller
  Kandidat**, seit dem Kandidatenwechsel durch #725 im Fenster.
- **#724:** Freeze-Nachtrag für den #723-Kandidaten (Squash-Merge
  `d0f8ea277ddd…`) – ändert selbst nur Protokoll-/Statusdokumentation.
- **#685 (drei weitere Akzeptanzkriterien automatisiert, PR #725):** Fehlende
  optionale Komponenten (Fehlende-Komponente-Smoke), Abschlussmatrix-Felder
  (Gerät/OS, Datum, Testperson, Link) und ein Virenscan der fünf gebauten
  Artefakte (ClamAV). **Erzeugt den aktuellen Kandidaten** (Squash-Merge
  `42807350cecf…`; siehe Kandidatenwechsel 12.).

## Ausdrücklich nicht in diesem Scope-Freeze enthalten

- Bauen oder Veröffentlichen der finalen Artefakte (AppImage/`.deb`/`.dmg`) –
  Aufgabe von #685/#686.
- Erneuter GL-Ressourcen-/Langzeittest als zusätzlicher Nachweis für PR #676 –
  eigenständiges Teil-Issue #684. **Nachtrag:** dessen Umsetzung ist inzwischen
  kandidatenrelevant und in der Tabelle oben klassifiziert; der Scope-Freeze
  selbst bleibt davon inhaltlich unberührt (keine Anwendungsfunktion).
- Erweiterung der Produktfunktionalität.
- Neuimplementierung des Fixes aus PR #676 (bereits auf `main` gemergt,
  unverändert übernommen).

## Verantwortlichkeit für den Kandidaten-Gate

Freigabe und Tag-Erstellung liegen bei #685 (Kandidatenartefakte +
Hardware-Abnahme) und #686 (Tag, Veröffentlichung, Post-Release-Verifikation)
unter Epic #680; #683 samt Korrektur #699 liefert ausschließlich den geprüften,
versionssynchronen Scope-Freeze-Stand als Grundlage dafür.
