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
- **Commits im Fenster:** 15 (`v2.7.0..<Kandidat>`, siehe Tabelle – jede Zeile
  entspricht genau einem Commit).
- **Protokollierter Kandidaten-SHA:** `f06a9cba01ce3b3b013461e383cd5931e17b1144`
  (`fix(release-freeze): Codex-Reviewbefunde zur Kandidatenableitung beheben
  (#699)`, Stand des Korrektur-Zweigs `claude/github-issue-699-buighx`)

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
| `bba18044755cf27e53f4505a297f33349e67091a` (#699, kurz `bba1804`) | **Freeze-Korrektur.** Diese Datei vollständig neu klassifiziert (volle SHAs, Kandidatenregel, Pfadklassen); `scripts/verify_release_freeze.py` als abgeleitete, maschinelle Kandidatenbestimmung; `tests/test_release_freeze.py`; `[2.7.1]`-CHANGELOG in allen sechs Sprachen um „Hinweise zu diesem Release" (Auswirkung/Betroffene/Upgrade-Relevanz/Einschränkungen) ergänzt, damit der veröffentlichte Release-Body diese Angaben wirklich enthält; `make release-freeze-check`. | Niedrig – kein `bgremover/**`-Code berührt, keine Verhaltensänderung der Anwendung; Änderungen betreffen Release-Metadaten (CHANGELOG-Text), ein Prüfskript und Tests. | `make check` grün auf diesem Commit (2031 passed, 5 skipped, 14 deselected); PR-CI #701 rot in genau einem Punkt: der neue git-Test war nicht flach-klon-tauglich (siehe Folgezeile). | **Aufnehmen – war Kandidat, jetzt durch den Nachfreeze-Fix ersetzt.** |
| `09a328863e6a6c42078c6850b9d7dcaed7469ab3` (#699, kurz `09a3288`) | Protokoll – trug den damaligen Kandidaten-SHA und die Gate-Nachweise nach. Ändert nur `docs/history/**`. | Keins. | – (Protokoll); `make release-freeze-check` lief danach mit 0 Fehlern/0 Warnungen. | Protokoll-Commit; verschiebt den Kandidaten nicht. Liegt seit dem Nachfreeze-Fix **innerhalb** des Fensters und ist deshalb hier klassifiziert. |
| `ad63e362062acebe41fa04ae50b9376923cfd9d8` (#699, kurz `ad63e36`) | **Nachfreeze-Fix (Regressionsfund in einer release-relevanten Prüfung).** `tests/test_release_freeze.py` wertete in einem flachen Klon (`actions/checkout`, `fetch-depth: 1`) den git-Exit 128 „Not a valid commit name" als „kein Vorfahr" und färbte die PR-CI rot. Jetzt wird „Objekt nicht im Klon" (nur flach zulässig → *skipped*) von „vorhanden, aber kein Vorfahr" (echter Befund) unterschieden. | Niedrig – reine Testlogik, kein Anwendungscode, keine Release-Metadaten. | `make check` grün (2031 passed, 5 skipped, 14 deselected); zusätzlich in einem simulierten `--depth 1`-Klon geprüft. | **Aufnehmen – war Kandidat, jetzt durch die Reviewkorrektur ersetzt.** |
| `24fe4cc56af93adabeb36373ee9cd80f9a1ec347` (#699, kurz `24fe4cc`) | Protokoll – Wiederholung des Dokuments nach dem Nachfreeze-Fix (Fensterzahl, Nachklassifizierung, Kandidaten-SHA, Gate-Nachweise). Ändert nur `docs/history/**`. | Keins. | – (Protokoll); `make release-freeze-check` danach 0 Fehler/0 Warnungen. | Protokoll-Commit; verschiebt den Kandidaten nicht. Liegt seit der Reviewkorrektur **innerhalb** des Fensters und ist deshalb hier klassifiziert. |
| `Kandidaten-Commit` (#699, voller SHA unter „Protokollierter Kandidaten-SHA") | **Reviewkorrektur (unabhängige Review auf PR #701).** Drei Befunde am Prüfwerkzeug behoben: Kandidatenableitung folgt `--first-parent` (ein Seitenzweig-Commit eines unsquashed Merge, dessen Baum nie ankam, kann nicht mehr Kandidat werden); der Release-Body wird mit dem `extract_release_notes.py` **des geprüften Commits** erzeugt statt mit der lokalen Fassung; `--require-pin` verlangt exakte SHA-Übereinstimmung (Freeze-Äquivalenz genügt als Release-Gate nicht). | Niedrig – Prüfwerkzeug und Tests, kein Anwendungscode, keine Release-Metadaten; die Verschärfung kann einen Release nur strenger, nie lockerer machen. | `make check` grün (2036 passed, 5 skipped, 14 deselected); neue Tests gegen ein echtes Mini-Repository (`-s ours`-Merge, echter Merge, Extraktor-Version, Pin-Fälle); `make release-freeze-check` 0 Fehler/0 Warnungen. | **Aufnehmen – neuer Kandidat.** Behebung von Reviewbefunden am Freeze-Werkzeug ist ein zulässiger Nachfreeze-Grund; Dokument, Fensterzahl und Protokollfeld sind mit diesem Eintrag vollständig wiederholt. |

### Protokoll-Commits über dem Kandidaten

Diese Commits liegen **außerhalb** des Fensters `v2.7.0..<Kandidat>` und sind
deshalb nicht Teil der Tabelle oben. Sie berühren ausschließlich Protokoll-Pfade,
verschieben den Kandidaten also nicht (`verify_release_freeze.py` weist sie als
„+N Protokoll-Commit(s) darüber" aus):

- **Protokollierung des Kandidaten-SHA nach der Reviewkorrektur** (#699): trägt
  den vollen 40-stelligen SHA oben, die neue Fensterzahl, die
  nachklassifizierten Commits und die Gate-Nachweise unten nach; ändert nur
  `docs/history/RELEASE-2.7.1-scope-freeze.md`.

Frühere Protokoll-Commits (`09a328863e6a…`, `24fe4cc56af9…`) liegen seit den
jeweils folgenden Kandidatenwechseln innerhalb des Fensters und stehen deshalb
oben in der Klassifizierungstabelle. Das ist der Normalfall: Jeder neue
Kandidat zieht die bisherigen Protokoll-Commits in die Tabelle.

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

- **Auswirkung** – reines Patch-Release, ausschließlich der GPU-Leak-Fix aus
  PR #676; keine neuen Funktionen, kein geändertes Bild-/Projekt-/Exportverhalten.
- **Betroffene Anwender:innen** – nur Nutzer:innen der 3D-Reliefvorschau; das
  beobachtbare Symptom (wachsender GPU-Speicherbedarf bei wiederholtem
  2D↔3D-Wechsel) ist benannt.
- **Upgrade-Relevanz** – empfohlen für 3D-Nutzer:innen, sonst optional; kein
  Migrationsschritt, `.bgrproj`/Exportformate/Einstellungen unverändert
  kompatibel (auch abwärts).
- **Bekannte Einschränkungen** – keine neuen gegenüber 2.7.0; die Langzeit-/
  Speichermessung unter echtem GL-Kontext ist separat als #684 erfasst.

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
- **Tag (#686):** Der Tag `v2.7.1` darf nur auf einen Commit gesetzt werden, für
  den `make release-freeze-check` (mit `--require-pin`) fehlerfrei läuft – also
  auf den protokollierten Kandidaten oder einen darüber liegenden reinen
  Protokoll-Commit.
- **Zweite Prüfung:** Die Korrektur wird als Pull Request zu #699 eingereicht
  und braucht **mindestens eine eingereichte, unabhängige GitHub-Review** auf
  dem finalen Korrektur-Commit (bei #698 fehlte genau dieser Nachweis). Der
  Review-Link wird in #699 hinterlegt, bevor #685/#686 starten.

## Gate-Nachweise

Alle Läufe erfolgen auf dem Kandidaten-Commit
`f06a9cba01ce3b3b013461e383cd5931e17b1144`, lokal unter Linux mit Python 3.12
und `QT_QPA_PLATFORM=offscreen` (nicht-editable Installation aus
`pyproject.toml` + `requirements/constraints.txt`).

| Prüfung | Lauf/Ergebnis |
|---|---|
| `make check` (ruff + mypy + pytest-Default-Set) | grün: ruff „All checks passed", mypy „no issues found in 69 source files", pytest **2036 passed, 5 skipped, 14 deselected** |
| `python scripts/verify_release_freeze.py` | 0 Fehler, 0 Warnungen; abgeleiteter Kandidat == protokollierter SHA, „15 Commits vollständig klassifiziert", Versionsquellen und Release-Body ok |
| `make release-freeze-check` (`--require-pin`) | ohne Fehler, nachdem der Protokoll-Commit den SHA nachgetragen hat |
| Flacher Klon (`git clone --depth 1`) | `tests/test_release_freeze.py` grün, der git-Test meldet sich dort als *skipped* |
| PR-CI von #701 auf `24fe4cc56af9…` | alle acht Checks grün (Lightweight PR checks, CodeQL/Analyze, license-check, pip-audit 3.10/3.12, review, license summary) |
| release-relevante Einzeltests: `tests/test_release_freeze.py`, `tests/test_release_gate.py`, `tests/test_changelog_metadata.py`, `tests/test_licenses_version.py`, `tests/test_version.py`, `tests/test_i18n_docs.py`, `tests/test_markdown_links.py` | grün (Teil des `make check`-Laufs oben) |

Historie der Kandidatenwechsel (jeder nach der Freeze-Regel vollständig
wiederholt, keiner still nachgezogen):

1. `bba18044755cf27e53f4505a297f33349e67091a` – Freeze-Korrektur; lokal grün,
   PR-CI rot (git-Test nicht flach-klon-tauglich).
2. `ad63e362062acebe41fa04ae50b9376923cfd9d8` – Nachfreeze-Fix dazu; PR-CI grün.
3. `f06a9cba01ce3b3b013461e383cd5931e17b1144` – Reviewkorrektur (aktueller
   Kandidat): Ableitung `--first-parent`, Release-Body-Extraktor vom geprüften
   Commit, `--require-pin` verlangt exakte SHA-Übereinstimmung.

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
- **#684:** unabhängig; GL-Langzeitnachweis, kein Freeze-Bestandteil.

## Ausdrücklich nicht in diesem Scope-Freeze enthalten

- Bauen oder Veröffentlichen der finalen Artefakte (AppImage/`.deb`/`.dmg`) –
  Aufgabe von #685/#686.
- Erneuter GL-Ressourcen-/Langzeittest als zusätzlicher Nachweis für PR #676 –
  eigenständiges Teil-Issue #684.
- Erweiterung der Produktfunktionalität.
- Neuimplementierung des Fixes aus PR #676 (bereits auf `main` gemergt,
  unverändert übernommen).

## Verantwortlichkeit für den Kandidaten-Gate

Freigabe und Tag-Erstellung liegen bei #685 (Kandidatenartefakte +
Hardware-Abnahme) und #686 (Tag, Veröffentlichung, Post-Release-Verifikation)
unter Epic #680; #683 samt Korrektur #699 liefert ausschließlich den geprüften,
versionssynchronen Scope-Freeze-Stand als Grundlage dafür.
