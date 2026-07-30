# Release 2.7.2 – Scope-Freeze & Freigabenotiz

Nachfolger von [`RELEASE-2.7.1-scope-freeze.md`](RELEASE-2.7.1-scope-freeze.md).
Dokumentiert den fixierten Umfang des Patch-Release-Kandidaten v2.7.2 nach
denselben Regeln, die #699 für 2.7.1 eingeführt hat.

## Warum ein neues Dokument statt eines Nachtrags

Mit der Veröffentlichung von v2.7.1 (Tag → `a3de137a0c0873f93f84186f9bba32d684a48808`,
[Release](https://github.com/NikolayDA/picture_helper/releases/tag/v2.7.1)) hat das
2.7.1-Dokument seinen Zweck erfüllt. Sein Fenster `v2.7.0..main` wächst danach
mit jedem weiteren Commit weiter, obwohl **keiner** davon noch in 2.7.1 landen
kann. Ein Nachtrag hätte dort einen nach dem Release entstandenen Commit als
„Kandidat für 2.7.1" protokolliert – eine nachweislich falsche Aussage in
genau dem Dokument, das als Nachweis dient.

`verify_release_freeze.py` leitet den Dokumentpfad aus
`pyproject.toml → project.version` ab
(`FREEZE_DOC_TEMPLATE = "docs/history/RELEASE-{version}-scope-freeze.md"`).
Der Versionsschnitt auf 2.7.2 schaltet die Prüfung deshalb automatisch auf
dieses Dokument um; das 2.7.1-Dokument bleibt unverändert als abgeschlossene
Historie stehen und wird nicht mehr fortgeschrieben.

## Kandidatenbestimmung (verbindlich)

- **Basis-Tag:** `v2.7.1` (= `a3de137a0c0873f93f84186f9bba32d684a48808`)
- **Kandidatenversion:** `2.7.2`
- **Kandidatenregel:** Kandidat ist der **jüngste Commit der Mainline
  (`--first-parent`) in `v2.7.1..main`, der einen kandidatenrelevanten Pfad
  ändert.** Reine Protokoll-Commits darüber (siehe Pfadklassen) verschieben
  den Kandidaten **nicht**. Unverändert übernommen aus dem 2.7.1-Dokument –
  die Regel hat sich in vier Kandidatenwechseln (#720, #723, #725, #732)
  bewährt und wird hier bewusst nicht angefasst.
- **Commits im Fenster:** 2 (`v2.7.1..<Kandidat>`, siehe Tabelle – jede Zeile
  entspricht genau einem Commit).
- **Protokollierter Kandidaten-SHA:** `nachzutragen`

Solange dort `nachzutragen` steht, ist der Freeze **nicht** abnahmefähig;
`verify_release_freeze.py --require-pin` schlägt in diesem Zustand bewusst
fehl. Das ist kein Versehen: Ein Dokument kann seinen eigenen Commit-SHA nicht
enthalten (#699), und der Versionsschnitt in diesem Commit ist selbst
kandidatenrelevant. Der SHA wird deshalb durch einen **reinen
Protokoll-Commit** darüber nachgetragen, der den Kandidaten nachweislich nicht
verändert.

Abzuleiten und zu prüfen mit:

```bash
python scripts/verify_release_freeze.py --print-candidate   # voller 40-stelliger SHA
make release-freeze-check                                   # vollständige Prüfung
```

### Pfadklassen (fail-closed)

Unverändert gegenüber 2.7.1 – die Klassen sind im Skript hinterlegt, diese
Tabelle gibt sie nur wieder:

| Klasse | Pfade | Wirkung |
|---|---|---|
| **Protokoll** (nicht kandidatenrelevant) | `docs/history/**`, `RECOMMENDATIONS.md`, `docs/i18n/*/RECOMMENDATIONS.md`, `CLAUDE.md` | Änderung verschiebt den Kandidaten **nicht**, bleibt aber nachweispflichtig. |
| **Kandidatenrelevant** | **alles andere** – u. a. `bgremover/**`, `tests/**`, `scripts/**`, `packaging/**`, `requirements/**`, `.github/**`, `pyproject.toml`, `Makefile`, `CHANGELOG.md`, `LICENSES.md`, `docs/i18n/*/CHANGELOG.md`, `docs/i18n/*/LICENSES.md`, restliche `docs/**` | Änderung erzeugt einen **neuen Kandidaten** und erzwingt die Wiederholung dieses Dokuments. |

Fail-closed: Ein neu eingeführter, unbekannter Pfad gilt als
kandidatenrelevant. `ANLEITUNG.md` und `README.md` gehören ausdrücklich dazu –
das war bei #732 die Überraschung, die den Kandidaten verschoben hat.

## Kategorisierung aller Änderungen seit v2.7.1

Jeder Commit im Fenster `v2.7.1..<Kandidat>` ist mit **vollem SHA** erfasst;
es gibt keine unbewertete Änderung. Reihenfolge: älteste zuerst.

| Commit | Zweck | Risiko | Testnachweis | Patch-Scope-Entscheidung |
|---|---|---|---|---|
| `1813e8b412375a835fc6fa6fc06f71ce112d2b09` (#734, kurz `1813e8b`) | Schließt vier Nachweise aus #686, die nach der 2.7.1-Veröffentlichung nur teilweise belegt waren: anonymer Download über `browser_download_url`, sichtbare Produktversion gegen den Sollwert aus dem Artefaktnamen, kontrollierte Projekt-Kopie über `save_project`, differenzierter Digest-Ausweis in der Evidenz. Zusätzlich Evidenz-Schema 2 mit Pflichtfeldprüfung. | Gering für Anwender:innen – berührt ausschließlich Abnahme-/Release-Werkzeug (`scripts/`, `bgremover/acceptance_smoke.py`, `bgremover/app.py`-Hook). Kein Pfad im normalen Programmablauf. Erhöht das Abnahme-Risiko bewusst *nach oben*: Ein Artefakt mit altem Hook wird jetzt abgewiesen statt still akzeptiert. | `make check` grün (2125 passed, 6 skipped); neun neue Tests, darunter `test_fetch_release_assets_downloads_anonymously_from_public_url`, `test_acceptance_extra_rejects_older_hook_schema`, `test_visible_version_rejects_a_prefix_match_in_the_title`, `test_project_copy_detects_reordered_layers`, `test_evidence_marks_assets_without_a_usable_digest_as_unverified`. | Kandidatenrelevant (`scripts/**`, `bgremover/**`, `CHANGELOG.md`, `docs/**`). In 2.7.2 aufgenommen; in den Release Notes als Werkzeugänderung ohne Anwenderwirkung ausgewiesen. |
| `Kandidaten-Commit` (dieser Commit) | Versionsschnitt auf 2.7.2 (`pyproject.toml`, `[2.7.2]`-CHANGELOG in sechs Sprachen, AppStream-Release-Eintrag, sechs Lizenz-Snapshots) plus dieses Freeze-Dokument. | Gering – reine Versions-/Dokumentationsangaben. Das Risiko liegt in der *Konsistenz* der sechs Sprachstände, nicht im Code. | `make check` grün; `verify_release_freeze.py` prüft pyproject, CHANGELOG-Datum, AppStream, Lizenz-Snapshots und Release-Body-Pflichtangaben in sechs Sprachen maschinell. | Kandidatenrelevant (`pyproject.toml`, `CHANGELOG.md`, `packaging/**`, `LICENSES.md`). Definiert den 2.7.2-Kandidaten. |

## Protokoll-Commits über dem Kandidaten

Noch keine. Der Nachtrag des protokollierten Kandidaten-SHA wird der erste
sein – er ändert ausschließlich `docs/history/**` und verschiebt den
Kandidaten damit nicht.

## Zusicherungen

Maschinell geprüft durch `scripts/verify_release_freeze.py` (Prüfcodes in
Klammern), nicht per Sichtprüfung zugesichert:

- `pyproject.toml` ist die einzige Versionsquelle (`pyproject-version`).
- `CHANGELOG.md` trägt einen datierten `[2.7.2]`-Abschnitt
  (`changelog-section`), in allen sechs Sprachen mit demselben Datum
  (`release-dates`).
- Der aus dem CHANGELOG abgeleitete Release-Body nennt in allen sechs Sprachen
  Auswirkung, betroffene Anwender:innen, Upgrade-Relevanz und bekannte
  Einschränkungen (`release-body`).
- Der AppStream-Eintrag stimmt in Version und Datum mit dem CHANGELOG überein
  (`appstream-release`).
- Alle sechs Lizenz-Snapshots tragen die Kandidatenversion
  (`license-versions`).
- Jeder Commit des Fensters ist klassifiziert (`unclassified-candidate-commit`
  / `unclassified-protocol-commit`), die Anzahl stimmt (`commit-count-mismatch`),
  und der protokollierte SHA entspricht dem abgeleiteten Kandidaten
  (`candidate-sha-mismatch`).

## Offen für dieses Release

- **Post-Release-Kriterien aus #686**, die erst gegen ein neu gebautes
  Artefakt belegbar sind: sichtbare Produktversion und kontrollierte
  Projekt-Kopie. Beide Prüfungen leben **im gepackten Artefakt**; die
  v2.7.1-Assets tragen noch den Vorgänger-Hook (Evidenz-Schema 1) und werden
  von der neuen Auswertung bewusst abgewiesen. Der erste 2.7.2-Kandidatenbau
  liefert den Nachweis.
- **Prüfsummen-Lücke:** Der Release-Workflow baut die Artefakte neu, statt die
  abgenommenen wiederzuverwenden – die auf Hardware abgenommenen Bytes sind
  deshalb nicht die veröffentlichten. Für 2.7.1 wurde das durch einen zweiten
  Abnahmelauf gegen das Release aufgefangen; die saubere Lösung (Wiederverwendung
  der Kandidatenartefakte) steht als Folgearbeit aus.
- **ClamAV-Virenscan** bleibt optionale Zusatzschicht (#731); die verbindliche
  Supply-Chain-Prüfung ist `scan_release_artifacts.py`.
- **macOS-Signatur:** weiterhin ad-hoc, keine Developer-ID-Notarisierung.
  Unveränderter Stand seit 2.7.0, in den Release Notes ausgewiesen.
