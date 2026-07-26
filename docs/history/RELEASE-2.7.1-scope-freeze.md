# Release 2.7.1 – Scope-Freeze & Freigabenotiz

Teil von Epic #680, Umsetzung von #683. Dokumentiert den fixierten Umfang des
Patch-Release-Kandidaten v2.7.1, damit Build, Release-Notizen und Anwendung
denselben Stand ausweisen.

## Release-Commit

- **Fixierter Freeze-Commit:** `ba7e7cd` (`docs: update RECOMMENDATIONS for
  three new epics (#680–#682) (#697)`), letzter Commit auf `main` vor diesem
  Scope-Freeze.
- Ab diesem Commit werden nur noch begründete Release-Blocker in den
  Kandidaten aufgenommen (z. B. eine Regression in einer der
  release-relevanten Prüfungen, siehe „Freeze-Regel" unten). Neue Funktionen
  laufen über den nächsten Zyklus.
- Vergleichsbasis: `v2.7.0...ba7e7cd` (8 Commits).

## Kategorisierung aller Änderungen seit v2.7.0

Jede Änderung im Vergleich `v2.7.0...ba7e7cd` ist einer Kategorie zugeordnet.
Es gibt keine unbewertete Änderung.

| Commit | Zweck | Risiko | Testnachweis | Patch-Scope-Entscheidung |
|---|---|---|---|---|
| `427b9ce` (PR #676) | **Fehlerbehebung.** `GLReliefViewer._ensure_buffers` reallozierte GL-Puffer/VAO der 3D-Reliefvorschau bei jedem (Wieder-)Upload, ohne die Vorgänger freizugeben – verwaiste GPU-Ressourcen akkumulierten über die Sitzung. Freigabe (`_release_gl_objects`) läuft jetzt zu Beginn von `_ensure_buffers`. | Niedrig – reiner Darstellungscode der optionalen 3D-Vorschau, kein Schreibpfad ins Modell, keine Bild-/Projekt-/Exportdaten betroffen. | Dedizierte GL-freie Regressionstests für Freigabe- und (Wieder-)Upload-Pfad (`tests/test_viewer_3d.py`, +87 Zeilen); `make check` grün. | **Aufnehmen – der namensgebende Fix dieses Patch-Release.** In CHANGELOG `[2.7.1]` unter „Behoben" dokumentiert. |
| `45ebac3` (PR #677/#679) | **Chore/Aufräumen.** Entfernt 4 per `vulture --min-confidence 60` + manueller Verifikation nachgewiesene, reposweit unreferenzierte Symbole (zwei ungenutzte Properties, ein Skript-Wrapper, eine Konstanten-Duplizierung). | Niedrig – laut Commit-Nachricht **keine funktionale Verhaltensänderung**; `make check` grün, vulture bestätigt alle 4 Funde verschwunden ohne neue Kandidaten. | Volle Testsuite (`make check`) vor und nach dem Commit grün; vulture-Re-Scan ohne neue Funde. | **Aufnehmen, mit expliziter Risikoentscheidung:** Dies ist tote-Code-Entfernung, keine Architektur- oder Verhaltensänderung, und damit keine „opportunistische Refactoring" im Sinne des Freeze-Kriteriums (siehe Abgrenzung unten). Kein separater Revert vor dem Tag nötig. |
| `9c93de6` (#678) | Dokumentation – `CLAUDE.md` auf aktuellen Repo-Stand gebracht (Standard-Gate, Architektur-Abschnitte, CI-Inventar). | Keins – reine Doku, kein Code-/Verhaltensänderung. | `make check` grün (im Commit vermerkt). | Nicht release-relevant für Anwender:innen-CHANGELOG; nicht in Release Notes. |
| `0e1e799` (#675) | Dokumentation – neun veraltete/ungenaue Code-Kommentare und Docstrings korrigiert (keine Codeänderung außerhalb von Kommentaren). | Keins – Kommentar-/Docstring-only, laut Commit-Nachricht ausdrücklich ohne Verhaltensänderung; ruff clean. | ruff clean (im Commit vermerkt); keine Logikänderung, daher kein zusätzlicher Testbedarf. | Nicht release-relevant für Anwender:innen-CHANGELOG; nicht in Release Notes. |
| `da5839d` (#674) | Dokumentation – RECOMMENDATIONS-Snapshot (PR-/Issue-Audit 22.–23. Juli). | Keins – reine Statusdoku in sechs Sprachen. | – (Doku-Snapshot). | Nicht release-relevant für Anwender:innen-CHANGELOG; nicht in Release Notes. |
| `0621869` (#668/#673) | Dokumentation + Test – `ANLEITUNG.md`/`README.md` auf aktuellen Screenshot-Satz migriert (alle sechs Sprachen), neuer Governance-Test `tests/test_screenshot_references.py` gegen künftige Drift. | Niedrig – Doku-Referenzen und ein neuer, isolierter Test; keine Laufzeitänderung der Anwendung. | Neuer Test selbst ist der Nachweis; `make check` grün. | Nicht release-relevant für Anwender:innen-CHANGELOG (keine Anwendungsfunktion); nicht in Release Notes. |
| `36c53b8` (#671) | Dokumentation – RECOMMENDATIONS-Reconciliation für den Abschluss von v2.7.0. | Keins – reine Statusdoku. | – (Doku-Snapshot). | Nicht release-relevant für Anwender:innen-CHANGELOG; nicht in Release Notes. |
| `ba7e7cd` (#697) | Dokumentation – RECOMMENDATIONS um drei neue Epics (#680–#682) ergänzt (auch dieser Scope-Freeze und sein Epic). | Keins – reine Statusdoku. | – (Doku-Snapshot). | Nicht release-relevant für Anwender:innen-CHANGELOG; nicht in Release Notes. |

### Abgrenzung „opportunistisches Refactoring" vs. `45ebac3`

Das Freeze-Kriterium schließt Feature-Erweiterungen und opportunistische
Refactorings aus einem Patch-Release aus, sofern sie nicht ausdrücklich mit
Risikoentscheidung freigegeben werden. `45ebac3` fällt nicht unter
„opportunistisches Refactoring" im problematischen Sinn (Umbau lebender
Logik, geänderte Kontrollflüsse, neue Abstraktionen), sondern ist reine
Entfernung toter, unreferenzierter Symbole – nachweislich ohne
Aufrufer im gesamten Repository (vulture + manuelle Verifikation) und mit
grüner Vollsuite vor/nach dem Commit. Risikoentscheidung: **aufnehmen**,
weil das Risiko eines stillen Verhaltensunterschieds hier nicht höher liegt
als bei den übrigen Dokumentations-Commits, während ein nachträglicher
Revert (Cherry-Pick-Historie, neuer Freeze-Commit) mehr Risiko einführen
würde als er vermeidet.

## Versionssynchronisierung

Alle gefundenen Versionsquellen melden konsistent `2.7.1`:

- `pyproject.toml` (`[project].version`) – die kanonische Quelle.
- `CHANGELOG.md` + alle fünf Übersetzungen (`docs/i18n/*/CHANGELOG.md`):
  `[2.7.1] – 2026-07-26`, leerer `[Unreleased]`-Abschnitt bleibt darüber
  bestehen; fehlender `[2.7.0]`-Vergleichslink im Fußbereich (aller sechs
  Sprachdateien) wurde bei dieser Gelegenheit nachgetragen.
- `LICENSES.md` + alle fünf Übersetzungen: Titelzeile und Datumsangabe
  aktualisiert (Dependency-Datenbasis unverändert – keiner der 8 Commits
  seit v2.7.0 ändert Laufzeit- oder Build-Abhängigkeiten).
- `packaging/linux/de.bgremover.app.metainfo.xml`: neuer
  `<release version="2.7.1" date="2026-07-26"/>`-Eintrag vor dem
  bestehenden `2.7.0`-Eintrag.

`bgremover.__version__` liest `pyproject.toml` zur Laufzeit (bzw. die
Paket-Metadaten nach Installation) – kein weiterer Ort im Code hält die
Version separat vor (siehe `tests/test_version.py`). Die sichtbare
„Über"-Anzeige und alle Build-/Paketnamen (`BgRemover-2.7.1-<platform>…`)
leiten sich transitiv aus derselben Quelle ab.

**Bewusst nicht geändert:** Die Kopfzeile „Letzter Release-Stand" in
`CLAUDE.md` bleibt bei `v2.7.0`. Sie dokumentiert den zuletzt tatsächlich
**getaggten und veröffentlichten** Stand, nicht den in Vorbereitung
befindlichen Kandidaten – ein vorzeitiges Umschreiben auf `v2.7.1` würde
einen noch nicht erfolgten Release vortäuschen. Tag und Veröffentlichung
sind Aufgabe von #686 (nachfolgend in Epic #680); dort wird diese Zeile
zusammen mit dem tatsächlichen Tag aktualisiert.

## Update-Metadaten / Release-Konfiguration

`app_update.py` bezieht die aktuell installierte Version ausschließlich über
`bgremover.__version__` (→ `pyproject.toml`) und vergleicht sie mit der
GitHub-Releases-API zur Laufzeit; es gibt keine separat gepflegte
Versionskonstante, die von `2.7.1` abweichen könnte.
`.github/workflows/release-linux.yml` verifiziert bei der eigentlichen
Tag-Erstellung (#686) `GITHUB_REF_NAME` gegen `pyproject.toml`
(`tests/test_release_gate.py::test_release_verifies_tag_matches_project_version`)
– ein Tag `v2.7.1`, der nicht exakt zu `project.version` passt, schlägt
dort fehl, statt eine widersprüchliche Version zu veröffentlichen.

## Release Notes (Entwurf für #686)

**Auswirkung:** Dieser Patch behebt ausschließlich einen GPU-Ressourcenleck
in der optionalen 3D-Reliefvorschau (PR #676); keine neuen Funktionen, keine
Änderung an Bild-, Projekt- oder Exportverhalten.

**Betroffene Anwender:innen:** Nur wer die 3D-Reliefvorschau (Workflow-Schritt
„Relief", Segment „Darstellung [3D]") tatsächlich nutzt; wer ausschließlich
die 2D-Vorschau verwendet, ist von diesem Fix nicht betroffen. Beobachtbares
Verhalten vor dem Fix: In einer längeren Sitzung mit wiederholtem
2D↔3D-Wechsel bzw. wiederholter Anzeige desselben zwischengespeicherten Mesh
wuchs der GPU-Speicherbedarf kontinuierlich, da alte OpenGL-Puffer und das
Vertex-Array-Objekt nicht freigegeben wurden. Nach dem Fix wird vor jedem
(Wieder-)Upload zuerst freigegeben.

**Upgrade-Hinweis:** Kein Handlungsbedarf – reiner Bugfix ohne Änderung an
Projektdateien (`.bgrproj`), Exportformaten oder Einstellungen. Ein Update
auf 2.7.1 ist ohne Migrationsschritt möglich.

**Bekannte Einschränkungen:** Keine über v2.7.0 hinausgehenden neuen
Einschränkungen. Der Fix wurde durch dedizierte, GL-freie Regressionstests
gegen Fake-Ressourcen abgesichert (`tests/test_viewer_3d.py`); ein
Langzeit-/Speichermessung unter echtem GL-Kontext ist Gegenstand des
separaten Teil-Issues #684 (Epic #680), nicht dieses Scope-Freeze.

Der endgültige, in GitHub Releases veröffentlichte Notiztext wird bei
Tag-Erstellung automatisiert aus `CHANGELOG.md` Abschnitt `[2.7.1]`
extrahiert (`scripts/extract_release_notes.py`,
`tests/test_release_gate.py`); der obige Entwurf ergänzt dort Kontext
(Auswirkung/Zielgruppe/Upgrade-Hinweis/Einschränkungen), der bewusst nicht
im knappen CHANGELOG-Eintrag selbst steht.

## Freeze-Regel und Verfahren für Änderungen nach dem Freeze

- **Freeze-Kriterium:** Ab dem oben genannten Freeze-Commit (`ba7e7cd`)
  fließen keine neuen Commits mehr in den 2.7.1-Kandidaten ein, außer sie
  behe­ben nachweislich einen Regressionsfund in einer release-relevanten
  Prüfung (`make check`, `make ui`, `tests/test_release_gate.py`,
  `tests/test_ci_qt_packages.py` u. ä.) oder eine Sicherheitslücke.
- **Verfahren bei notwendiger Nachfreeze-Änderung:** Jeder zusätzliche
  Commit auf dem Kandidaten-Zweig erzwingt die vollständige Wiederholung
  dieses Scope-Freeze-Dokuments (neue Vergleichsbasis, neue
  Commit-Klassifizierungstabelle, erneute Versionssynchronisierungsprüfung)
  – kein stillschweigendes Nachziehen einzelner Zeilen. Der neue
  Freeze-Commit-Hash ersetzt `ba7e7cd` in diesem Dokument (per Edit, nicht
  per neuer Datei, damit die Historie in einer Datei nachvollziehbar
  bleibt).
- **Zweite Prüfung:** Dieses Dokument wird als Teil des Pull Requests zu
  #683 erstellt und durchläuft damit die reguläre PR-Review (mindestens ein
  zweiter Blick auf Commit-Liste und Versionsfundstellen), bevor #685/#686
  darauf aufbauen.

## Ausdrücklich nicht in diesem Scope-Freeze enthalten

- Bauen oder Veröffentlichen der finalen Artefakte (AppImage/`.deb`/`.dmg`) –
  Aufgabe von #685/#686.
- Erneuter GL-Ressourcen-/Langzeittest als zusätzlicher Nachweis für
  PR #676 – eigenständiges Teil-Issue #684.
- Erweiterung der Produktfunktionalität.
- Neuimplementierung des Fixes aus PR #676 (bereits auf `main` gemergt,
  unverändert übernommen).

## Verantwortlichkeit für den Kandidaten-Gate

Freigabe und Tag-Erstellung liegen bei den nachfolgenden Teil-Issues #685
(Kandidatenartefakte + Hardware-Abnahme) und #686 (Tag, Veröffentlichung,
Post-Release-Verifikation) unter Epic #680; dieses Issue (#683) liefert
ausschließlich den geprüften, versionssynchronen Scope-Freeze-Stand als
Grundlage dafür.
