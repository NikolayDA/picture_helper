**Deutsch** · [README](README.md) · [Anleitung](ANLEITUNG.md) · [Installation macOS](INSTALL_MAC.md) · [Installation Linux](INSTALL_LINUX.md)

# BgRemover – Tests ausführen

Diese Anleitung beschreibt, wie die Tests **lokal auf dem Mac** laufen
und **wann sie auf GitHub** automatisch ausgeführt werden.

## Warum diese Änderung?

Die GitHub-Actions-Test-Matrix (Ubuntu + macOS × Python 3.10–3.13) lief
früher bei **jedem Push und jedem Pull Request** – das wurde auf Dauer
zu teuer (vor allem die macOS-Runner). Seit jetzt gilt:

| Wo                 | Wann                                                                 |
|--------------------|----------------------------------------------------------------------|
| **GitHub PR CI**   | bei jedem Pull Request auf `main`/`master` (Ubuntu + Python 3.12)     |
| **GitHub Full CI** | als **Kandidaten-Gate** vor jedem manuell gestarteten Release-Build (vom Release-Workflow als wiederverwendbarer Workflow aufgerufen, **vor** dem Bau der Artefakte), wöchentlich sonntags 06:00 UTC oder **manuell** |
| **GitHub UI Nightly** | jede Nacht und manuell (Ubuntu + Python 3.12, UI-Interaktionstests) |
| **GitHub Coverage** | bei Push auf `main` (Coverage-Report/Badge; `.github/workflows/coverage.yml` triggert **nicht** auf `master`) |
| **Lokal/Mac**      | jederzeit per `make` – dieselben Prüfungen wie die PR-CI plus UI bei Bedarf |

Der Workflow `License Check` ist davon **nicht** betroffen und
läuft weiterhin bei Pull Requests und auf `main`/`master`.

## Voraussetzungen (einmalig)

Im Projektordner eine virtuelle Umgebung anlegen und die Test-Werkzeuge
installieren:

```bash
python3 -m venv .venv
source .venv/bin/activate
make install-test
```

Damit stehen `pytest`, `pytest-qt`, `ruff` und `mypy` bereit. Auf macOS
sind **keine zusätzlichen System-Bibliotheken** nötig – die PyQt6-Wheels
bringen Qt mit. Das Projekt staged die kleinen Qt-Platform-Plugins bei
Bedarf in das System-Temp-Verzeichnis, damit lokale macOS-Headless-Läufe
nicht daran scheitern, dass Qt Plugin-Dateien im Projektpfad nicht
auflisten kann.

Für die Test-Referenz wird bewusst eine normale Paketinstallation
verwendet. So prüfen die Smoke-Tests das installierte Paket aus einem
fremden Arbeitsverzeichnis – genau wie CI, Release-Build und App-Bundle.
`make pr-check` führt diese Installation vor jedem PR-Check automatisch
erneut aus; für schnelle Einzelprüfungen gibt es weiterhin `make check`.
Die Installation läuft mit `requirements/constraints.txt`, damit lokale
Checks, PR-CI, Lizenzreport und App-Bundle denselben getesteten
Dependency-Snapshot verwenden. Für gezielte Aktualisierungstests kann der
Pfad überschrieben werden:

```bash
make PIP_CONSTRAINT=/pfad/zur/constraints.txt pr-check
```

> **Nur `[test]` ins Test-venv** – **nicht** `[ai]` oder `[docs]`. Das
> `ai`-Extra (`rembg`) gehört in die *Anwendungs*-Umgebung (das
> App-Bundle bringt sein eigenes venv mit), nicht in die Test-Umgebung.
> Die CI installiert ebenfalls nur `[test]`. Ein im Test-venv
> installiertes `rembg` würde den rembg-Warmup scharf schalten (Modell-
> Download über das Netz) – die Tests fangen das zwar zentral ab (kein
> echter Warmup im Testlauf), aber das Extra hat dort schlicht nichts
> verloren und bläht die Umgebung nur auf.

> Bei manuellen `python -m ...`-Aufrufen zuerst
> `source .venv/bin/activate`. Die Makefile-Targets finden eine lokale
> `.venv/bin/python` automatisch; bei Bedarf lässt sich der Interpreter
> mit `make PYTHON=/pfad/zur/python ...` überschreiben.

### Unterstützte Python-Version

Offiziell getestet ist **Python 3.10–3.13** (siehe `pyproject.toml`-
Classifier). **Python 3.14 ist für das lokale Test-venv derzeit nicht
empfohlen**, weil das Projekt diese Version noch nicht in der Matrix
absichert. Welche Version das venv nutzt, zeigt `python --version`
(bzw. der Pfad `.venv/lib/pythonX.Y/`).

Bei `Fatal Python error: Aborted` / `Abort trap: 6` das venv gezielt auf
einer offiziell getesteten Version neu aufbauen:

```bash
rm -rf .venv
python3.12 -m venv .venv          # oder python3.13
source .venv/bin/activate
make install-test
```

`tests/conftest.py` prüft die Qt-Umgebung vor dem ersten GUI-Test in
einem isolierten Subprozess. Schlägt der QApplication-Start fehl, bricht
der Lauf **sauber mit einer erklärenden Meldung** (inkl. der echten
Qt-Fehlerausgabe) ab – statt mit einem unleserlichen SIGABRT-Stacktrace.

## Tests lokal ausführen (`make`)

Im Projektordner (venv aktiv):

| Befehl       | Was passiert                                                              |
|--------------|---------------------------------------------------------------------------|
| `make install-test` | Installiert das Paket nicht-editable mit `[test]` und `requirements/constraints.txt` in das Test-venv |
| `make doctor` | Prüft Python-Version, Test-Abhängigkeiten, Paketinstallation, Console-Script und Qt-`offscreen` |
| `make pr-check` | **Schnelle PR-Prüfung:** `install-test` + `doctor` + `ruff` + `mypy` + `pytest` (volle UI-Suite ausgeschlossen, `ui_smoke` läuft mit) |
| `make check` | Schnelle Wiederholung ohne Neuinstallation/Doctor: `ruff` + `mypy` + `pytest` |
| `make ui`    | Volle lokale UI-Interaktionssuite inkl. `ui_smoke`                         |
| `make all`   | Alles zusammen (`check` + `ui`)                                            |
| `make lint`  | `shellcheck` für Shell-Skripte (falls installiert) + `ruff` (Stil/Fehler)  |
| `make type`  | Nur `mypy` (Typprüfung)                                                    |
| `make test`  | Nur `pytest` (volle UI-Suite ausgeschlossen, `ui_smoke` läuft mit)         |
| `make coverage` | `pytest` mit Coverage-Messung und HTML-Report (`fail_under = 86`)      |
| `make gl-stress` | GL-Ressourcen-Langzeitsonde der 3D-Vorschau (`scripts/gl_stress_probe.py`) |

Empfohlener Ablauf vor einem Pull Request:

```bash
make pr-check
```

Empfohlener Ablauf vor einem Release:

```bash
make all
```

Alles grün ⇒ der Stand entspricht lokal den automatischen PR-Prüfungen;
`make all` deckt zusätzlich die bewusst lokalen UI-Interaktionstests ab.

## Die UI-Tests

`tests/test_ui_interactions.py` enthält automatische, qtbot-gesteuerte
UI-Tests (Smoke, Zeichentools, Menü/Toolbar, Crop-Overlay,
SettingsDialog). Sie sind mit dem Marker `ui` versehen, ebenso
`tests/test_e2e_release_regression.py` und `tests/test_height16_e2e.py`.
Nur diese `ui`-markierten Tests laufen bei `make ui`/`pytest -m ui`
(volle, nightly UI-Suite).

Daneben trägt ein kleines, stabiles Subset schnellerer qtbot-Tests den
Marker `ui_smoke` – u. a. in `tests/test_workflow.py`,
`tests/test_right_panel.py`, `tests/test_resize_dialog.py`,
`tests/test_viewer_3d.py`, `tests/test_preview3d_integration.py`,
`tests/test_preview3d_acceptance.py`, `tests/test_screenshot3d.py`,
`tests/test_ai_model_dialog.py`, `tests/test_ai_install_dialog.py`,
`tests/test_eufymake_export_dialog.py`, `tests/test_acceptance_smoke.py`
und `tests/test_ui_interactions.py`. Die meisten dieser Module tragen
**nur** `ui_smoke`, nicht zusätzlich `ui` – nur `test_ui_interactions.py`
und `test_e2e_release_regression.py` tragen beide Marker.

- `pytest` (Standard, und damit auch PR-CI/Full-CI) überspringt die
  volle UI-Suite, nimmt aber alles mit dem Marker `ui_smoke` mit –
  konfiguriert über `addopts = "-q -m 'not ui or ui_smoke'"` in
  `pyproject.toml`.
- `make ui` bzw. `pytest -m ui` führt dagegen **ausschließlich** die
  `ui`-markierten Tests aus (das explizite `-m ui` ersetzt den
  Standard-Ausschluss statt ihn nur aufzuheben). Reine
  `ui_smoke`-Module ohne `ui`-Marker – die meisten der oben genannten –
  laufen dabei **nicht** zusätzlich mit; sie sind bereits über jeden
  normalen `pytest`-Lauf abgedeckt.

<!-- Achtung Maschinenformat: Der Satzanfang "Ein weiterer Marker,
`gl_smoke`", die Klammer-Aufzählung und die Klausel "; modulweit nur in
`…`" im folgenden Absatz werden von
tests/test_gl_smoke_marker_governance.py geparst – bei Umformulierung dort
die Anker nachziehen (gleiches Muster wie die N6-Hinweise in den
Qt-Paketlisten). -->
Ein weiterer Marker, `gl_smoke`, kennzeichnet die wenigen Tests mit echtem
OpenGL-Rendering (`tests/test_viewer_3d_gl.py`, `tests/test_screenshot3d.py`,
`tests/test_benchmark_preview3d_live.py`, ADR #591; modulweit nur in
`test_viewer_3d_gl.py`, in den übrigen Modulen an je einem Test). Sie
laufen in jedem normalen `pytest`-Lauf mit, überspringen sich aber automatisch,
sobald keine renderfähige Qt-Plattform verfügbar ist – das trifft auf
`offscreen` (und damit auf CI sowie diese Anleitung) zu.
Details zum manuellen Nachweis unter echtem GL:
[`docs/PACKAGING_SMOKE.md`](docs/PACKAGING_SMOKE.md).

Die Liste oben synchron zum tatsächlichen Marker-Bestand zu halten, sichert
`tests/test_gl_smoke_marker_governance.py` (#832) ab: Der Test lässt pytest
in einem Subprozess ungefiltert sammeln und liest die Marker über das
Mini-Plugin `tests/_marker_collect_plugin.py` direkt aus den Item-Objekten
aus; verglichen werden sowohl die Dateiliste als auch die
Granularitätsaussage (modulweit vs. je ein markierter Test) gegen die oben
genannten Angaben. Die Inventur kostet je Testlauf einmalig eine zweite,
ungefilterte Kollektion des `tests/`-Baums (einige Sekunden, geteilt
zwischen den Prüfungen) – die kurze Pause beim ersten dieser Tests ist
also erwartet, kein Hänger. Die `ui`-/`ui_smoke`-Aufzählungen weiter oben
bleiben dagegen vorerst Handarbeit; die Erweiterung auf dieselbe
Marker-Inventur ist als #847 notiert.

### GL-Ressourcen-Langzeittest (#684)

`tests/test_viewer_3d_gl_lifecycle.py` sichert den Lebenszyklus der
GL-Puffer/VAO der 3D-Vorschau ab (Fix aus PR #676): über 110 Zyklen je
Datensatzgröße darf die Zahl lebender GL-Objekte nicht wachsen. Die Tests laufen
im normalen `pytest`-Lauf mit und brauchen **keinen** GL-Kontext – sie fahren den
echten Kontrollfluss mit instrumentierten Puffer-Attrappen.

Dieselbe Messsonde erzeugt den reproduzierbaren Nachweis für ein Release:

```bash
make gl-stress                                  # 120 Zyklen, klein/typisch/groß
python scripts/gl_stress_probe.py --cycles 1000 --json-out gl-stress.json
QT_QPA_PLATFORM=xcb python scripts/gl_stress_probe.py --mode gl   # echter Kontext
```

Exit 0 = kein Befund, 1 = Ressourcenbefund, 2 = in dieser Umgebung nicht
ausführbar (keine renderfähige Plattform, fehlgeschlagener Viewer oder
ausgebliebener Upload). Läufe unter 100 Zyklen lehnt die Sonde ab – für einen
bewusst nicht abnahmefähigen Diagnoselauf `--allow-short-run` setzen. Ergebnisse und Hardware-Prozedur:
[`docs/history/RELEASE-2.7.1-gl-langzeittest.md`](docs/history/RELEASE-2.7.1-gl-langzeittest.md).

Die Tests laufen headless über `QT_QPA_PLATFORM=offscreen` – es öffnet
sich also **kein Fenster**.

## Recommendations-Live-Check (#752)

`RECOMMENDATIONS.md` driftete wiederholt kurz nach einer Aktualisierung vom
tatsächlichen GitHub-Stand ab (#669, #728, erneut #752). Zwei getrennte
Prüfungen sichern das ab:

- **Netzfrei, läuft in der Default-Suite mit:**
  `tests/test_recommendations_freeze_consistency.py` bestimmt das aktive
  Freeze-Dokument aus `pyproject.toml` und prüft, dass alle sechs
  Sprachfassungen dasselbe Kurzstatus-Datum und dieselbe Menge an
  Triage-Issue-Nummern führen (der Mengenvergleich ersetzt seit #821 den
  früheren Vergleich einer separat deklarierten Anzahl: gleiche Mengen heißt
  gleiche Anzahl, und die Zahl musste zuvor sechsfach von Hand gepflegt
  werden). `tests/test_recommendations_live_check.py`
  deckt die Kernlogik von `scripts/recommendations_live_check.py` (Triage-
  Tabellen-Parsing inkl. gruppierter Zeilen wie `#680 / #685 / #686`,
  Vergleichslogik) über gespeicherte Fixtures ab – ohne Netzwerk oder
  GitHub-Token.
- **Netzwerkzugriff, separat ausführbar:**
  `python scripts/recommendations_live_check.py` fragt die tatsächlich
  offenen GitHub-Issues ab und vergleicht sie gegen die Triage-Tabelle in
  `RECOMMENDATIONS.md` (Abschnitt `## Offene GitHub-Issues`). Gemeldet
  werden offene Issues, die in der Tabelle fehlen, sowie Issues, die die
  Tabelle weiterhin als offen führt, obwohl sie auf GitHub bereits
  geschlossen sind. Die Anzahl offener Issues nennt der Bericht, leitet sie
  aber aus der Tabelle ab (#821, Stufe 1). Offline/reproduzierbar mit einer
  gespeicherten API-Antwort:

  ```bash
  python scripts/recommendations_live_check.py                     # Live-Abfrage
  python scripts/recommendations_live_check.py \
    --data tests/fixtures/recommendations_live_check/open_issues_sample.json
  ```

  Exit 0 = deckungsgleich, 1 = mindestens ein Befund, 2 = Aufruf-/
  Netzwerkfehler.

**Wann ausführen:** vor jedem PR, der `RECOMMENDATIONS.md` (oder eine der
fünf Übersetzungen) inhaltlich ändert – insbesondere nach dem Schließen
oder Neuerfassen von Issues, nicht erst als nachträgliche Korrektur wie bei
#669/#728. Das Archiv **„Vorige Runden"** ist bewusst historisch: einmal
geschriebene Einträge dort bleiben unverändert und werden weder vom
netzfreien Paritätstest noch vom Live-Check angefasst – nur der Kurzstatus
(„## Aktueller Stand") und die Triage-Tabelle darunter müssen den aktuellen
GitHub-Stand widerspiegeln.

- **Schreibmodus (#821, Stufe 2):** `python scripts/recommendations_live_check.py --write`
  schreibt die Triage-Tabellen **aller sechs** Sprachfassungen auf den
  Live-Stand fort: Zeilen geschlossener Issues entfallen, neu offene Issues
  bekommen eine Zeile mit Nummer und Titel aus der API sowie `TODO` in den
  redaktionellen Spalten. Bestehende Zeilen bleiben wortgleich und in ihrer
  Reihenfolge – Relevanz, Komplexität, Modell und „Nächster Schritt" sind
  Handarbeit, ebenso die Übersetzung des Titels: Anders als die
  redaktionellen Spalten trägt Spalte 2 keinen Platzhalter, eine
  unübersetzt gebliebene Fassung wird von keinem Test gemeldet (#829,
  Befund 5). Der Lauf endet mit Exit 1,
  solange ein `TODO` offen ist; `tests/test_recommendations_freeze_consistency.py`
  prüft dasselbe netzfrei für alle sechs Fassungen, damit ein unbewerteter
  Platzhalter nicht gemergt wird. Das Werkzeug läuft bewusst **lokal**, sein
  Ergebnis geht wie jede andere Änderung durch einen PR – der CI-Check bleibt
  read-only. Eine **gruppierte** Zeile (mehrere Issue-Links in Spalte 1)
  bleibt komplett stehen, solange eines ihrer Issues offen ist – eine
  bereits geschlossene Nummer darin trennt `--write` nicht automatisch ab;
  das erfordert Handarbeit (#829, Befund 4).

- **Automatisiert, wiederkehrend (#777):** `recommendations-live-check.yml`
  führt genau diesen Live-Check ohne menschliches Zutun aus – täglich
  (06:30 UTC), zusätzlich bei jedem `issues`-Ereignis (opened/closed/
  reopened), und manuell per `workflow_dispatch`. Der Job schlägt sichtbar
  fehl, sobald `RECOMMENDATIONS.md` vom echten GitHub-Stand abweicht. Das
  manuelle Nachziehen allein hatte den Drift in #669/#728/#752 mehrfach und
  in #777 sogar zweimal am selben Tag reproduziert; die wiederkehrende
  Ausführung schließt genau diese Lücke. Unabhängig vom Exit-Status sichert
  der Workflow den Bericht in der Job-Zusammenfassung und 30 Tage als
  Actions-Artefakt. **Owner ist der Repository-Owner:** Ein roter Lauf bleibt
  ein aktiver Dokumentationsbefund, bis Kurzstatus und Triage in der deutschen
  Fassung sowie allen fünf Übersetzungen aktualisiert sind und der Live-Check
  erneut grün ist. Die Reaktion erfolgt vor dem nächsten Merge mit Issue- oder
  Recommendations-Bezug, spätestens innerhalb eines Arbeitstags. Der Check
  bleibt bewusst read-only und eröffnet kein Tracking-Issue, weil dieses den
  zu prüfenden offenen Bestand selbst verändern würde.

## Einzelne Tests / nützliche Aufrufe

```bash
# Eine einzelne Testdatei
python -m pytest tests/test_viewport.py

# Ein einzelner Test, ausführlich
python -m pytest tests/test_ui_interactions.py::test_crop_cancel -v

# Alle UI-Tests ausführlich
QT_QPA_PLATFORM=offscreen python -m pytest -m ui -v

# Registrierte Marker anzeigen (enthält 'ui' und 'ui_smoke')
python -m pytest --markers
```

## GitHub-Tests bei PR, manuell oder Release

**Pull Request:** Der Workflow **PR CI** läuft automatisch auf
Ubuntu/Python 3.12 und führt `make pr-check` aus.

**Manuell:** Auf GitHub → Reiter **Actions** → Workflow **Full CI** →
Schaltfläche **Run workflow** → Branch wählen → starten. (Möglich dank
`workflow_dispatch`.)

**Release-Kandidat (nur manuell, kein Tag-Trigger):** Der Workflow
**Release artifacts (Linux + macOS)** (`release-linux.yml`) startet
ausschließlich per `workflow_dispatch` – ein Tag-Push allein baut nichts.
Der erste harte Gate ist `verify-candidate`: der gebaute Laufkopf muss mit
`GITHUB_SHA` übereinstimmen und alle Commits/Pfade seit der eingefrorenen
Basis müssen als release-relevant/-neutral klassifiziert sein (Freeze-
Provenienz, `scripts/verify_release_freeze.py`). **Erst danach** ruft der
Workflow die volle Matrix als wiederverwendbaren Workflow (`Full CI`) auf;
Build hängt per `needs: [verify-candidate, test]` an beiden Ergebnissen:
nur wenn sowohl die Freeze-Provenienz als auch die volle Matrix für genau
diesen Commit grün sind, werden AppImage und `.deb` (x86_64 + aarch64/
Raspberry Pi OS) sowie ein macOS-`.dmg` (Apple Silicon/arm64) gebaut. Der
Workflow **veröffentlicht selbst nichts** und hat keine Schreibrechte.
Zusätzlich läuft die volle Matrix wöchentlich sonntags um 06:00 UTC per
Schedule und lässt sich jederzeit manuell auslösen. Der Workflow
**UI Nightly** führt die UI-Interaktionstests jede Nacht und bei manueller
Auslösung separat aus; **Coverage** läuft bei jedem Push auf `main` (nicht
`master`).

Die eigentliche Veröffentlichung ist ein separater, rein manueller Ablauf
**nach** einem grünen Kandidatenbau, mit einem zwingenden Zwischenschritt:
**Release-Abnahme (Self-hosted Hardware)** (`release-abnahme.yml`) sammelt
die Hardware-Abnahme-Evidenz zu genau diesem Build-Run und erzeugt
Freigabemanifest + Release-Instanz; **danach muss ein Release-Tag exakt auf
den abgenommenen Commit gesetzt werden** (`git tag` + Push, siehe Runbook
Schritt 7 – der Publish-Workflow verlangt einen bereits existierenden Tag
und prüft, dass er auf den im Manifest gebundenen Kandidaten zeigt); erst
dann veröffentlicht **Publish accepted release artifacts**
(`release-publish.yml`) ausschließlich die im Freigabemanifest
gespeicherten, byteidentischen fünf Dateien unter diesem Tag (Draft-first,
kein Neubau, kein Clobber). Der verbindliche Ablauf steht im
[Release-Runbook](docs/RELEASE_PROCESS.md), die Kriterien in der
[Abnahme-Checkliste](docs/RELEASE_ACCEPTANCE_CHECKLIST.md) – diese Anleitung
hier beschreibt nur die Testautomatisierung, nicht den vollständigen
Release-Prozess.

## Fehlerbehebung

- **`ModuleNotFoundError: No module named 'PyQt6'`** – venv nicht
  aktiviert oder Abhängigkeiten fehlen: `source .venv/bin/activate`
  und `make install-test`.
- **`python: No such file or directory` / falscher Interpreter** – das
  Makefile bevorzugt automatisch `.venv/bin/python`, danach `python`,
  danach `python3`. Bei Sonderfällen explizit setzen:
  `make PYTHON=/pfad/zur/python pr-check`.
- **Paket- oder Qt-Diagnose unklar** – `make doctor` ausführen. Der
  Doctor prüft auch, ob `bgremover` aus einem neutralen Arbeitsverzeichnis
  importierbar ist und ob das Console-Script auf `PATH` liegt.
- **UI-Test öffnet ein Fenster / hängt** –
  `QT_QPA_PLATFORM=offscreen` setzen (geschieht in `make`/`conftest.py`
  automatisch).
- **Die volle UI-Suite läuft bei `pytest` nicht mit** – das ist
  beabsichtigt; nur das `ui_smoke`-Subset läuft standardmäßig. Für die
  vollständige Suite `make ui` bzw. `pytest -m ui` verwenden.
- **`Fatal Python error: Aborted` / `Abort trap: 6` beim `qapp`-Fixture**
  – Qt kann das `offscreen`-Plugin nicht laden. Erst `make install-test`
  und danach `make doctor` ausführen; hilft das nicht, das venv auf
  Python 3.12/3.13 neu aufbauen (siehe „Unterstützte Python-Version“
  oben). `conftest.py` fängt den Fall ab und gibt eine klare Diagnose
  mit der echten Qt-Meldung aus statt eines unleserlichen
  SIGABRT-Stacktrace.
- **`Fatal Python error: Aborted` mit `rembg`/`pooch`/`download_models`
  im Stacktrace** – im Test-venv ist (fälschlich) das `ai`-Extra
  installiert; `MainWindow` startet dann den rembg-Warmup, der ein
  ~176 MB Modell übers Netz lädt – mehrere Tests parallel reißen den
  Prozess ab. `conftest.py` unterbindet den Warmup inzwischen zentral
  in allen Tests, der Lauf ist also auch dann offline und stabil.
  Sauber ist trotzdem ein Test-venv **ohne** `ai`/`docs`:
  `make install-test` (siehe Hinweis unter „Voraussetzungen“).
