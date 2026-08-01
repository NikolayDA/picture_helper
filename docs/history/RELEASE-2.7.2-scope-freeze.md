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
- **Commits im Fenster:** 6 (`v2.7.1..<Kandidat>`, siehe Tabelle – jede Zeile
  entspricht genau einem Commit).
- **Protokollierter Kandidaten-SHA:** `57517ecbc1e59a46bb8c7362a1bd82cf3a5facd8`
  (`fix: Linux-Abnahme prüft das gepackte Artefakt statt des Checkouts (#740)`,
  Squash-Merge von PR #750 auf `main`)

Der protokollierte SHA ist die einzige verbindliche Freeze-Basis für einen
2.7.2-Kandidatenbau. Stünde dort `nachzutragen`, wäre der Freeze **nicht**
abnahmefähig; `verify_release_freeze.py --require-pin` schlägt in diesem
Zustand bewusst fehl. Genau das war zwischen PR #735 und diesem
Protokoll-Nachtrag der Fall: Ein Dokument kann seinen eigenen Commit-SHA nicht
enthalten (#699), und der Versionsschnitt war selbst kandidatenrelevant. Der
SHA kommt deshalb durch einen **reinen Protokoll-Commit** darüber hinein, der
den Kandidaten nachweislich nicht verändert. Kurz-SHAs dürfen im Text
zusätzlich vorkommen, gelten aber nirgends als Nachweis.

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
| `61d67750b1051c7008e901005c515a31a8204aa0` (#735, kurz `61d6775`) | **Zwei Dinge, nicht nur eines.** (a) Versionsschnitt auf 2.7.2: `pyproject.toml`, `[2.7.2]`-CHANGELOG in sechs Sprachen, AppStream-Release-Eintrag, sechs Lizenz-Snapshots (H1 **und** Generierungsdatum) plus dieses Freeze-Dokument. (b) Änderung am Laufzeitverhalten von `scripts/abnahme_smoke.py`: Befunde und die Logs fehlgeschlagener Wächter-Phasen gehen bei einem roten Smoke ins Joblog, ungewächte Fehlschläge (apt-get, hdiutil) führen ihre Kommandoausgabe in der Meldung mit. | (a) Gering – Versions-/Dokumentationsangaben; das Risiko liegt in der *Konsistenz* der sechs Sprachstände. (b) Gering für Anwender:innen (kein Pfad im Programm), aber **operativ relevant**: Der Code läuft im Abnahmeweg und entscheidet mit, was ein Prüfer nach einem roten Lauf zu sehen bekommt. Zusätzliche Ausgabe kann Joblogs verlängern; erfolgreiche Läufe bleiben unverändert still, erfolgreiche Wächter-Phasen werden ausdrücklich nicht gedruckt. | `make check` grün; `verify_release_freeze.py` prüft pyproject, CHANGELOG-Datum, AppStream, Lizenz-Snapshots und Release-Body-Pflichtangaben in sechs Sprachen maschinell. Für (b) Regressionstests in `tests/test_abnahme_smoke.py`: `test_main_writes_failed_evidence_and_returns_nonzero` (Befunde im Log), `test_main_prints_guard_log_for_a_failing_phase` (inkl. Negativkontrolle, dass ein erfolgreicher Wächter *nicht* gedruckt wird), `test_dmg_mount_failure_reports_the_command_output`, `test_command_detail_prefers_stderr_and_falls_back`. | Kandidatenrelevant (`pyproject.toml`, `CHANGELOG.md`, `packaging/**`, `LICENSES.md`, **`scripts/**`**, **`tests/**`**). Definiert den 2.7.2-Kandidaten. (b) ist bewusst aufgenommen: Der Fund stammt aus dem Abnahmelauf gegen v2.7.1, bei dem ein rotes Leg keinerlei Diagnose im Joblog hinterließ – ohne den Fix wäre der nächste Kandidatenbau genauso schwer zu beurteilen. |
| `36acb866e43fd3942cdc8e1002bcedefeaa9ff5c` (#736, kurz `36acb86`) | Protokoll-Nachtrag: trägt `61d6775` als Kandidaten nach und korrigiert zwei Codex-Befunde – eine falsch behauptete maschinelle Absicherung für Protokoll-Commits sowie die doppeldeutige Bezeichnung „dieser Commit" für zwei verschiedene Commits. | Keins – reine Protokolldoku, ausschließlich `docs/history/**`. | `tests/test_release_freeze.py` grün; `verify_release_freeze.py --require-pin` meldete danach 0 Fehler / 0 Warnungen. | **Protokoll.** Verschiebt den Kandidaten nicht; liegt nur deshalb in dieser Tabelle, weil der Kandidat inzwischen darüber gewandert ist (#738). |
| `49b75b25e2a7804395c4f96dc7015391c2a7726d` (#738, kurz `49b75b2`) | Weist in der Abnahme-Evidenz aus, **aus welchem Pfad der geprüfte Code stammt** (`laufzeit_herkunft`, Schema 3) – für den Hauptprozess **und** für einen echten `spawn`-Kindprozess. Anlass ist Lauf 30581788054, in dem der Interpreter aus dem entpackten AppImage kam, `bgremover/ai_process.py` aber aus dem Source-Checkout. | Gering für Anwender:innen – reines Abnahme-Werkzeug. Operativ relevant: Die Sonde startet einen zusätzlichen Kindprozess (20 s Zeitlimit, `daemon`, `kill()` nach Join, jeder Fehler landet als `fehler`-Feld). Sie **bewertet nicht** – die Herkunft geht nicht in `ok` ein, damit der Nachweis die Abnahme nicht rot färbt, bevor die Ursache verstanden ist. | `make check` grün (2132 passed, 6 skipped); `test_evidence_records_where_the_checked_code_came_from`, `test_evidence_schema_matches_the_smoke_expectation`, `test_acceptance_extra_rejects_schema3_evidence_without_provenance`, `test_acceptance_extra_prints_parent_and_child_provenance` (Erfolgs- **und** Fehlschlagpfad). | Kandidatenrelevant (`bgremover/**`, `scripts/**`, `tests/**`). Definiert den 2.7.2-Kandidaten. Bewusst aufgenommen: Ohne diesen Nachweis ist unklar, ob die Nachweise aus gepackten Artefakten überhaupt das Bundle prüfen – eine offene Frage, die vor dem nächsten Release beantwortet sein muss. |
| `1d6d07bf37f576be45064473a8269ef8a1b2d826` (#739, kurz `1d6d07b`) | Protokoll-Nachtrag: trägt `49b75b2` als Kandidaten nach und macht `--require-pin` wieder grün. | Keins – reine Protokolldoku, ausschließlich `docs/history/**`. | `tests/test_release_freeze.py` grün; `--require-pin` meldete danach 0 Fehler / 0 Warnungen. | **Protokoll.** Verschiebt den Kandidaten nicht; steht hier, weil der Kandidat inzwischen durch #750 darüber hinweggewandert ist. |
| `Kandidaten-Commit` (= `57517ecbc1e59a46bb8c7362a1bd82cf3a5facd8`, PR #750; die Platzhalterzeile folgt der Konvention aus #699 – der volle SHA steht im Pin oben und kommt durch den Protokoll-Nachtrag darüber herein) | Behebt #740: Die Linux-Abnahme startete das Artefakt im Source-Checkout, sodass der Checkout-Code das gebündelte Paket beschattete (`python -m bgremover` stellt das cwd an den Anfang von `sys.path`). Neues `--workdir` in `smoke_launch.py`, neutrales Verzeichnis an allen drei Startpfaden von `abnahme_smoke.py` und in den drei Linux-Smokes von `release-linux.yml`; AppImage-Pfad absolut aufgelöst. | Gering für Anwender:innen – reines Abnahme-/CI-Werkzeug, kein Pfad im Programmablauf. Operativ **erhöht** es das Risiko bewusst: Die Linux-Smokes prüfen erstmals wirklich das Bundle und können Fehler zeigen, die der Checkout bisher verdeckt hat. | `make check` grün (2139 passed, 6 skipped); sieben neue Tests, darunter `test_neutral_workdir_prevents_checkout_from_shadowing_the_bundle` (beide Richtungen) und `test_linux_smoke_artifact_paths_are_absolute_when_workdir_is_set` (Negativkontrolle geprüft). | Kandidatenrelevant (`scripts/**`, `tests/**`, `.github/workflows/**`). **Definiert den 2.7.2-Kandidaten.** Bewusst aufgenommen: Ohne diesen Fix belegt kein Linux-Abnahmelauf das ausgelieferte Artefakt – die Voraussetzung für jede weitere Hardware-Abnahme (#741, U3). |

## Protokoll-Commits über dem Kandidaten

Diese Commits liegen **außerhalb** des Fensters `v2.7.1..<Kandidat>` und sind
deshalb nicht Teil der Tabelle oben. Sie berühren ausschließlich Protokoll-Pfade,
verschieben den Kandidaten also nicht; `verify_release_freeze.py` weist sie als
„+N Protokoll-Commit(s) darüber" aus.

- **Nachtrag des Kandidaten-SHA für #750** (dieser Nachtrag, PR #749): trägt
  `57517ecbc1e59a46bb8c7362a1bd82cf3a5facd8` als Kandidaten nach und macht
  `--require-pin` wieder grün. Ändert ausschließlich Protokollpfade
  (`docs/history/**`, `RECOMMENDATIONS.md` samt Übersetzungen).
  Den eigenen SHA kann dieser Commit nicht enthalten (#699); er ist über die
  „+N"-Angabe des Prüfskripts und über die zugehörige PR belegt.

Die vorherigen Protokoll-Commits `36acb86` (#736) und `1d6d07b` (#739) stehen
nicht mehr hier, sondern mit vollem SHA in der Tabelle oben: Der Kandidat ist
durch #738 bzw. #750 über sie hinweggewandert, damit liegen sie jetzt
**innerhalb** des Fensters.

> **Grenze der maschinellen Prüfung (Codex-Fund auf PR #736):** Die
> Klassifizierungsprüfung erhält nur die Commits aus `Basis..Kandidat`.
> Protokoll-Commits **oberhalb** des Kandidaten werden gezählt, aber nicht
> darauf geprüft, ob sie hier eingetragen sind – ein vergessener Eintrag
> erzeugt **keine** Warnung. Die Vollständigkeit dieses Abschnitts ist damit
> Konvention, nicht erzwungen. Eine frühere Fassung dieses Absatzes behauptete
> das Gegenteil; sie war nachweislich falsch (`--require-pin` meldet auf genau
> diesem Stand `0 Warnung(en)`).

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
