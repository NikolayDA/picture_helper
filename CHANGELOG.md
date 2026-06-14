**Deutsch** · [English](docs/i18n/en/CHANGELOG.md) · [Español](docs/i18n/es/CHANGELOG.md) · [Français](docs/i18n/fr/CHANGELOG.md) · [Українська](docs/i18n/uk/CHANGELOG.md) · [简体中文](docs/i18n/zh/CHANGELOG.md)

# Changelog

Alle nennenswerten Änderungen an BgRemover werden in dieser Datei
dokumentiert. Das Format orientiert sich an
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/); das Projekt
folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Hinzugefügt

- **Performance-Benchmark der Bild-Pipeline.** `scripts/benchmark.py` misst die
  Verarbeitungszeit pro Ausgabeformat (PNG/JPEG/WebP/TIFF) über die echten
  `image_ops`-Pfade, legt datierte Ergebnisse unter `benchmarks/results/` ab und
  vergleicht aufeinanderfolgende Läufe; Formate mit über 10 % Regression werden
  geflaggt und optional als GitHub-Issue gemeldet (`make bench` /
  `make bench-compare`). Ein wöchentlicher CI-Workflow
  (`.github/workflows/benchmark.yml`) führt Lauf und Vergleich auf konstanter
  Hardware aus und schreibt das Ergebnis als Baseline zurück.
- **Verhaltensbasierte Tests gehärtet.** Die Behavioral-Test-Coverage für
  bislang lückenhafte Pfade wurde ausgebaut (#177, #192).
- **Dedizierte Unit-Tests für `app.py` und `main_window.py`.** Coverage von
  `app.py` 0 % → 100 % und `main_window.py` 68 % → 100 %; die Gesamt-Coverage
  stieg auf 94 % (#214).

### Geändert

- **Abhängigkeiten aktualisiert.** `idna` wurde auf 3.15 und `urllib3`
  auf 2.7.0 angehoben; `LICENSES.md` ist mit dem neuen Dependency-Snapshot
  synchronisiert.
- **Build-Backend gegen Supply-Chain-CVEs gepinnt.** `setuptools` wird in
  `pyproject.toml` (`[build-system]`) und `requirements/constraints.txt` auf
  `>=78.1.1` angehoben (CVE-2024-6345 RCE, CVE-2025-47273 Path-Traversal),
  `wheel` in `constraints.txt` auf `==0.46.2` (CVE-2026-24049). So zieht der
  isolierte Wheel-Build keine verwundbaren Build-Werkzeuge mehr (#200, #201).
- **pip in CI/Dev auf eine gepatchte Version angehoben.** Die
  pip-installierenden CI-Workflows (`ci.yml`, `pr-ci.yml`, `ui-nightly.yml`,
  `benchmark.yml`, `license-check.yml`) und der Web-SessionStart-Hook heben
  `pip` vor dem Installieren auf `>=26.1.2` an; die Dev-Install-Doku
  (`README.md`/`INSTALL_MAC.md`/`INSTALL_LINUX.md`) ebenso. Schliesst den
  `pip-audit`-Batch um Path-Traversal-, Symlink- und Modul-Hijacking-CVEs;
  pip ist das Installationswerkzeug selbst und daher nicht über
  `constraints.txt` pinbar (#202).
- **macOS-Diagnose redaktiert sensible Pfade.** `diagnose_mac.sh` ersetzt
  standardmäßig `$HOME` durch `~`, kürzt übrige `/Users/<name>`-Pfade und gibt
  statt der rohen letzten 40 Log-Zeilen nur noch eine gefilterte
  Fehler-Zusammenfassung mit redaktierten Pfaden aus – die Ausgabe kann damit
  bedenkenlos an Bug-Reports angehängt werden. Die volle Diagnose (inklusive
  Roh-Log) liefert das neue Flag `--include-raw-logs`; ein Shell-Test
  (`tests/test_diagnose_mac.py`) stellt sicher, dass Home-Verzeichnis und
  Bildpfade die Standard-Ausgabe nicht erreichen (#185).
- **AppImage-Release-Dependencies eingepinnt.** Ein
  `requirements/constraints.txt`-Snapshot fixiert die Versionen für den
  AppImage-Build-Workflow (#182, #191).
- **License-Workflow-Permissions gehärtet.** Der Workflow läuft jetzt mit
  minimalen Rechten (#183, #193).
- **`CanvasHistory._redo_max` entfernt.** Das write-only-Attribut wurde nirgends
  gelesen; die Redo-Begrenzung erfolgt ausschließlich über `deque(maxlen=…)`
  (#199, #215).

### Behoben

- **Dateigrößen-Limit vor dem Einlesen.** `open_validated_image` prüft die
  Eingabedatei jetzt per `os.fstat()` gegen ein dokumentiertes Byte-Limit
  (`_MAX_INPUT_FILE_BYTES`, 512 MB), **bevor** ihr Inhalt vollständig in den
  Arbeitsspeicher gelesen wird; ein zusätzliches begrenztes `read()` fängt
  ungewöhnliche Fileobjekte und eine Größenänderung zwischen `fstat()` und
  `read()` (TOCTOU) ab. Die Meldung unterscheidet Dateigröße (MB) von der
  Megapixel-Grenze (MP). Synchroner und asynchroner Ladepfad nutzen dieselbe
  Prüfung; das bestehende Megapixel-Limit und der TOCTOU-Schutz bleiben
  erhalten (#230).
- **rembg-Inferenz-Session wird wiederverwendet.** Der Warmup erzeugt jetzt
  über `new_session()` genau eine rembg-/ONNX-Session und legt sie modulweit
  ab; jeder spätere `AIWorker` übergibt sie an `remove(..., session=...)`, statt
  das Modell erneut zu initialisieren. Die Erzeugung ist per
  Double-Checked-Locking threadsicher und läuft über mehrere KI-Aufrufe hinweg
  höchstens einmal; ein fehlgeschlagener Init meldet weiterhin den Worker-Fehler
  und hinterlässt keinen fälschlich „bereiten" Zustand. Der irreführende
  Kommentar (ein Dummy-`remove()` cache die Session) ist mit korrigiert (#229).
- **`recent_files` ist robust gegen beschädigte Einstellungen.**
  `RecentFiles.paths()` behandelt jetzt jeden gespeicherten Roh-Typ defensiv:
  ein einzelner String bleibt ein Eintrag, Listen/Tupel werden elementweise auf
  nicht-leere Strings gefiltert, und jeder andere Wert (z. B. Ganzzahl, `None`)
  ergibt eine leere Liste statt eines `TypeError`. Das neue `sanitize()` schreibt
  einen tatsächlich beschädigten Wert beim Start einmalig bereinigt zurück (mit
  Logwarnung); der harmlose QSettings-Ein-Element-String bleibt unangetastet. So
  bricht ein manuell bearbeiteter oder veralteter `recent_files`-Wert weder den
  Menü- noch den Anwendungsaufbau ab; ein neueres (zukünftiges) Schema bleibt
  dabei unangetastet, um Downgrade-Datenverlust zu vermeiden (#233, #240).
- **Double-Checked Lock für den rembg-Lazy-Import und TOCTOU-Schutz in
  `open_validated_image`.** Zwei Threads konnten gleichzeitig den Import betreten
  (Race), und die Datei wurde doppelt geöffnet (TOCTOU-Fenster); beides ist mit
  Regressionstests abgesichert (#174).
- **Veraltete asynchrone Bildlade-Ergebnisse werden verworfen.** Ein monotoner
  `_load_generation`-Zähler in `MainWindow` verhindert, dass ein verspäteter
  Load-Callback ein neueres Bild überschreibt (analog zum AI-Stale-Check) (#190).
- **Canvas-Selection-Mask-Typing korrigiert.** Ein falscher Typ löste einen
  mypy-Fehler im Full-CI-Lauf aus (#196, #197).
- **CI-Workflow-YAML repariert.** Der nicht gequotete Name des pip-Upgrade-Steps
  brach das Parsen des Workflows (#213).
- **Aktiver Crop übersteht keinen Bildzustandswechsel mehr.** Jeder sichtbare
  Bildwechsel (Drehen, Spiegeln, KI-Ergebnis, Undo/Redo, Original-
  Wiederherstellung, Crop-Bestätigung) verwirft jetzt zentral in
  `_set_image_state` ein aktives Crop-Overlay sowie ein begonnenes Lasso und
  meldet `cropModeChanged(False)` genau einmal. So lässt sich ein veraltetes
  Crop-Rechteck nicht mehr auf das neue Bild anwenden und kann keine
  transparenten Padding-Pixel mehr erzeugen (#247).
- **Release-Workflow veröffentlicht nur nach grünem Full-CI-Gate.**
  `release-linux.yml` ruft die maßgebliche Full-CI-Matrix (`ci.yml`) jetzt als
  wiederverwendbaren Workflow auf und bindet Build und Publish per `needs` daran;
  ein separater `verify-tag`-Job bricht ab, wenn der Tag nicht dem Format
  `vX.Y.Z` entspricht oder von `project.version` abweicht. AppImage/`.deb` werden
  vor dem Upload auf Name, Architektur, Ausführbarkeit und Debian-Metadaten
  geprüft, und `gh release create`-Fehler werden nicht mehr mit `|| true`
  verschluckt (ein bestehendes Release wird explizit wiederverwendet). So
  gelangen keine Artefakte aus einem Commit mit roten Tests oder abweichender
  Version mehr in ein Release (#250).
- **Leere Auswahl gibt das Overlay-Pixmap sofort frei.** `_refresh_overlay`
  prüft den Leerzustand der Maske jetzt **vor** dem inkrementellen Dirty-Pfad.
  Radiert der Radiergummi den letzten Auswahlpixel weg, werden
  `_overlay_pixmap` und das `QGraphicsPixmapItem` umgehend geleert, statt eine
  transparente Vollbild-QPixmap (bei 40 MP rund 160 MiB) bis zum nächsten
  Vollaufbau zu halten. Teilweises Radieren aktualisiert weiterhin nur das
  Dirty-Rechteck (#251).

### Entfernt

- **Toter Code entfernt (#244).** Die nirgends aufgerufene Methode
  `ImageCanvas._zoom` und der produktiv ungenutzte Wrapper
  `WorkerController.launch_worker` wurden ersatzlos entfernt; die
  Thread-Lifecycle-Tests laufen jetzt über den real genutzten
  `_build_thread`-Pfad.

## [2.3.0] – 2026-06-04

### Hinzugefügt

- **Test-Coverage auf 88 % erhöht (zweite Runde, zuvor 82 %).** Neue Datei
  `tests/test_canvas_events.py` deckt die bislang ungetesteten Event-Handler
  und die Steuerlogik von `canvas.py` ab: Maus-, Tastatur-, Wheel- und
  Drag-Handler (über synthetische Qt-Events, bewusst ohne `ui`-Marker, damit
  sie in die CI-Coverage zählen), die Zauberstab-Ergebnisflüsse (Treffer,
  veraltete Revision, nicht-aktiv), Tool-Einstellungen, Undo/Redo/Undo-to bei
  aktivem Crop sowie die Guard-Pfade ohne geladenes Bild. Damit steigt
  `canvas.py` von 64 % auf 99 %; die Coverage-Schwelle `fail_under` wurde von
  80 auf 86 angehoben.
- **Test-Coverage auf 82 % erhöht (zuvor 74 %).** Neue, verhaltensbasierte
  Tests für bislang dünn abgedeckte Logikmodule: `tests/test_lasso.py`
  (Polygon-Lasso-Zustand, Vorschaulinie, Doppelklick-Duplikat, Polygon→Maske),
  `tests/test_canvas_crop.py` (Crop-Gesten Press/Move/Release, Guards ohne
  geladenes Bild) und `tests/test_viewport.py` (Zoom-Grenzen, Pan-Routing,
  Scrollbar-Verschiebung). `tests/test_crop_overlay.py` deckt jetzt das
  Resize von allen vier Ecken, `inside`/Properties und den `paint`-Pfad
  (offscreen) ab; `tests/test_settings_schema.py` den Migrationsschritt-Pfad
  und `tests/test_settings_dialog.py` die Verzeichnis-/Log-Ordner-Auswahl.
  Damit stehen `crop.py`, `canvas_lasso.py`, `canvas_viewport.py`,
  `settings_schema.py` und `settings_dialog.py` bei 100 %, `canvas_crop.py`
  bei 98 %. Die Coverage-Schwelle `fail_under` wurde von 68 auf 80 angehoben.
- **ANLEITUNG.md i18n.** Fünf Übersetzungen der deutschen Nutzungsanleitung
  angelegt: `docs/i18n/{en,es,fr,uk,zh}/ANLEITUNG.md`. Das DOC_NAMES-Tuple
  in `tests/test_i18n_docs.py` wurde um `"ANLEITUNG.md"` erweitert, sodass
  die strukturelle Synchronitätsprüfung alle fünf Kopien automatisch erfasst.
  Ein Hinweis in jedem i18n-Header erklärt, dass `ANLEITUNG.pdf` nur für das
  deutsche Original erzeugt wird.
- **Soft-Drift-Test `tests/test_i18n_sync.py`.** Prüft Heading-Hierarchie
  und Code-Block-Anzahl von `CHANGELOG.md`, `INSTALL_MAC.md` und
  `INSTALL_LINUX.md` gegen die deutschen Originale. Abweichungen erzeugen
  lesbare Warnungen statt harter Testfehler, damit das CI grün bleibt.
- **`bgremover/status_messages.py` – zentrale Status-Meldungen.** Alle
  UI-sichtbaren Status-Strings aus `canvas.py`, `canvas_crop.py` und
  `main_window.py` in die neue Klasse `StatusMessages` gezogen. Kein
  i18n-Framework – nur ein zentraler Sammelpunkt als Vorbereitung für
  künftige Lokalisierung.
- **Runtime-i18n mit Englisch-Unterstützung.** Deutsch und Englisch sind
  zur Laufzeit umschaltbar; der Settings-Dialog enthält eine persistente
  Sprachauswahl mit Neustart-Hinweis, und die UI-Strings in Canvas,
  Dialogen und rechtem Panel laufen über die zentrale Übersetzungslogik.
- **Werkzeug-Shortcuts.** Die Bildbearbeitungswerkzeuge lassen sich jetzt
  per Tastatur wechseln; Toolbar-Tooltips und Dokumentation nennen die
  plattformgerechten Tastenkürzel.
- **Linux-AppImage-Paketierung.** Der Release-Build erzeugt ein AppImage
  als empfohlenen Linux-Endnutzerpfad inklusive Packaging-Skripten,
  CI-Abdeckung und Installationshinweisen.
- **Linux-`.deb`, aarch64/Raspberry Pi und Release-Workflow.** Die
  Linux-Paketierung wurde um Debian-Pakete, aarch64-/Pi-Unterstützung und
  den zugehörigen Release-Workflow erweitert.

- **QSettings-Schema-Version eingefuehrt.** Neuer Helfer
  `bgremover/settings_schema.py` mit `SCHEMA_VERSION = 1` und
  `migrate(settings)`; `MainWindow.__init__` ruft die Migration direkt
  nach der `QSettings`-Konstruktion auf. Aktuell ist nur die
  Initialisierung aktiv – kuenftige Format-Wechsel (z. B. Layout der
  `recent_files`-Liste) haengen sich an dieser zentralen Stelle ein,
  ohne dass alte gespeicherte Werte den Start crashen lassen. Zukuenftige
  Versionen werden nicht zurueckgeschrieben (Downgrade-Schutz) und nur
  geloggt; ein nicht-numerischer `schema_version`-Wert wird wie
  "nicht gesetzt" behandelt. Tests in `tests/test_settings_schema.py`
  decken Initialisierung, Pre-Schema-Upgrade ohne Datenverlust,
  Idempotenz, Future-Version-Warnung und korrupten Wert ab.
- **Laufzeit-Test für `RembgWarmupWorker`.** Zwei neue Tests in
  `tests/test_workers.py` prüfen den Always-emit-`finished`-Vertrag
  (Erfolgs- und Fehlerfall des Warmups) mit gepatchtem `rembg_remove`.
  Ein neuer Controller-Test in `tests/test_worker_controller.py`
  verifiziert zusätzlich, dass der `WorkerController` den Thread-
  Lifecycle auch dann sauber abschließt (Worker freigegeben,
  `warmup_done` gesetzt, `on_finished` aufgerufen), wenn `rembg_remove`
  beim ersten Start eine Exception wirft – sonst hängt der Bootstrap,
  falls das ONNX-Modell offline nicht geladen werden kann.

### Geändert

- **Dokumentation und Kommentare bereinigt.** Lebende Doku und Code-Kommentare
  sind von alten PR-/Rundenmarkern befreit, veraltete macOS-Hinweise sind
  aktualisiert und `RECOMMENDATIONS.md` plus i18n-Kopien sind wieder als
  kurzer aktueller Review-/Roadmap-Stand lesbar.
- **Version auf 2.3.0 angehoben.** `pyproject.toml`, AppStream-Metainfo,
  Lizenzübersichten und Changelog-Vergleichslinks spiegeln den neuen
  Versionsschnitt.
- **Docstring-Sprache vereinheitlicht.** `bgremover/image_ops.py`,
  `bgremover/recent_files.py` und `bgremover/worker_controller.py` hatten
  englische Modul- und Methoden-Docstrings; alle drei auf Deutsch gebracht,
  konsistent mit dem Rest des Projekts.

- **Nutzerdokumentation für Linux-Pakete und Spracheinstellung aktualisiert.**
  README, `INSTALL_LINUX.md` und `ANLEITUNG.md` nennen AppImage/`.deb` als
  empfohlenen Linux-Endnutzerpfad und dokumentieren die persistente
  Spracheinstellung inklusive Neustart-Hinweis; die i18n-Kopien sind
  entsprechend synchronisiert.

- **Code-Hygiene-Sammelrunde (kleine, voneinander unabhängige Cleanups).**
  - `bgremover/__init__.py` + neues `bgremover/_version.py`: Das
    Source-Lauf-Fallback für `__version__` liest jetzt `pyproject.toml`
    direkt (`tomllib` ab Py3.11, Regex auf Py3.10) statt eines
    hardgecodeten Versions-Literals; pyproject.toml ist damit Single
    Source of Truth, ein Versionsbump kann den Fallback nicht mehr
    vergessen. `tests/test_version.py` validiert das neue Verhalten.
  - `bgremover/canvas.py`: `_paint_brush(cx, cy)` liest nicht mehr
    `self._tool` intern; der Aufrufer übergibt das `additive`-Flag
    explizit (keyword-only), Tests entsprechend angepasst.
  - `bgremover/canvas.py`: `apply_remove`/`apply_replace` fangen statt
    `Exception` nur noch `OSError`/`ValueError`/`PIL.UnidentifiedImageError`;
    echte Bugs (AttributeError, IndexError …) propagieren wieder
    sichtbar nach oben, statt als Statusmeldung verschluckt zu werden.
  - `bgremover/constants.py`: Docstring von `init_runtime` benennt den
    prozessweiten Seiteneffekt auf `Image.MAX_IMAGE_PIXELS` ausdrücklich;
    außerdem dokumentiert ein Kommentar neben dem zentralen
    `logger`-Objekt die Empfehlung, in neuem Sub-Modul-Code
    `logging.getLogger(__name__)` zu verwenden.
  - `bgremover/recent_files.py`: Kommentar erklärt den QSettings-Sonderfall,
    in dem eine Ein-Element-Liste als roher String zurückkommt.
  - `Makefile`: `make clean` räumt jetzt zusätzlich `*.egg-info/`,
    `build/` und `dist/` (Reste von `pip install -e .`).
  - `pyproject.toml`: `description` reflektiert den dokumentierten
    Linux-Support („macOS und Linux") statt nur macOS.
- **Wand-Auswahl friert die UI nicht mehr ein.** Der Flood-Fill der
  Zauberstab-Auswahl lief bisher synchron im UI-Thread; bei 40-MP-Bildern
  mit grossen einfarbigen Flaechen war der Klick spuerbar laggy. Die
  Berechnung laeuft jetzt im neuen ``FloodFillWorker`` auf einem
  kurzlebigen ``QThread`` (analog zu ``ImageLoadWorker``); das Ergebnis
  kommt per ``finished``-Signal zurueck und wird via Stale-Check auf
  ``content_revision`` verworfen, falls der Nutzer das Bild
  zwischenzeitlich gewechselt oder editiert hat. Pannen/Zoomen bleibt
  waehrend der Berechnung reaktiv; nur ein paralleler Wand-Klick wird
  mit einer Statusmeldung blockiert.
- **CI-Testmatrix erweitert.** Der Full-CI-Workflow prüft jetzt Python
  3.10, 3.11, 3.12 und 3.13 auf Ubuntu und macOS.
- **`RembgWarmupWorker` erbt von `_Worker`.** Der Warmup-Worker war
  bisher der einzige Worker mit eigenem `try/except/finally`-Boilerplate
  außerhalb der gemeinsamen Basis. `_Worker.run` bekommt einen
  `_always_finished()`-Hook im `finally`-Zweig (Default no-op), den
  `RembgWarmupWorker` überschreibt, um sein parameterloses
  `finished`-Signal weiterhin sowohl im Erfolgs- als auch im Fehlerfall
  zu feuern – der `WorkerController` braucht das, um den Thread-
  Lifecycle abzuschließen. Konsistente Logging-/Error-Semantik (jetzt
  via `_error_context = "rembg-Warmup"`); `WorkerController`-
  Typannotationen vereinheitlicht (`_Worker | RembgWarmupWorker` →
  `_Worker`).
- **Canvas-Submodule nutzen die öffentliche Edit-API.** `CanvasCrop` und
  `CanvasTransform` riefen bislang `ImageCanvas._apply_pil(...)` direkt
  auf, obwohl `ImageCanvas` dafür den öffentlichen Eintritt
  `apply_edit(img, desc=...)` anbietet; analog griff `CanvasCrop.cancel`
  auf das private `_tool` zu. Beide Submodule nutzen jetzt
  `apply_edit(...)` bzw. die neue Read-Only-Property
  `ImageCanvas.current_tool`. `_apply_pil` bleibt intern für
  `apply_loaded_image`/`apply_edit`/Undo-/AI-Pfade. Zusätzlich nutzen
  `clear_selection`, `invert_selection`, `expand_selection` und
  `shrink_selection` jetzt den vorhandenen `_requires_image`-Decorator
  statt vier verschiedener inline-Guards; `clear_selection` meldet im
  Leerzustand jetzt einheitlich „Kein Bild geladen" statt stumm zu
  bleiben.
- **Öffentliche Paket-API entschlackt (kleiner Breaking Change für externe
  Konsumenten).** Privates Vokabular ist nicht länger vom `bgremover`-
  Top-Level re-exportiert: `_MAX_MEGAPIXELS`, `_THREAD_SHUTDOWN_MS`,
  `_UNDO_MEMORY_LIMIT`, `_Theme`, `_setup_logging` und `_resolve_log_dir`
  sind aus `bgremover/__init__.py` (Import-Block und `__all__`) entfernt.
  Code, der diese Symbole braucht, importiert direkt aus den Submodulen
  (`bgremover.constants`, `bgremover.theme`, `bgremover.logging_config`).
  `logger`, `LOG_FILENAME`, `REMBG_AVAILABLE` und `current_log_file`
  bleiben als legitime öffentliche API erhalten. Zusätzlich entfällt die
  reine Test-Vorderkante `MainWindow._recent_paths()`; die drei Tests in
  `tests/test_recent_files.py` greifen direkt auf
  `w._recent_files.paths()` zu.

### Behoben

- **`apply_remove`/`apply_replace` verschlucken keine echten Bugs mehr.**
  Der frühere `except Exception` schluckte u. a. `AttributeError` und
  `AssertionError` – also genau die Klasse Fehler, die als Bug sichtbar
  werden sollte. Der neue, enge Filter (`OSError`, `ValueError`,
  `PIL.UnidentifiedImageError`) lässt diese Bugs wieder propagieren,
  fängt aber erwartete Bild-/IO-Fehler weiterhin als Statusmeldung ab.
- **Synchroner Lade-Pfad nutzt dieselben Schutzprüfungen wie der Worker.**
  `ImageCanvas.load_image` (Drag & Drop, Tests) ging bislang am
  strukturellen `verify()`, an der Format-Whitelist
  (`_ALLOWED_IMAGE_FORMATS`) und am sauberen Decode-Fehlerpfad vorbei,
  die der `ImageLoadWorker` seit der Format-/Struktur-Härtung leistet –
  nur der Megapixel-Check war gemeinsam. Beide Wege rufen jetzt den
  neuen Helfer `bgremover.image_loading.open_validated_image` auf, sodass
  manipulierte Dateien und nicht unterstützte Formate auch via
  Drag & Drop sauber als Statusmeldung enden statt mit unbehandelten
  PIL-Exceptions.
- **License-Check stabilisiert.** `coverage` ist jetzt in
  `requirements/constraints.txt` gepinnt (`==7.14.0`), damit ein neuer
  `coverage`-Upstream-Release den `LICENSES.md`-Drift-Vergleich der
  License-Workflow nicht mehr rot färbt.
- **License-Check gegen Zeitzonen-Drift gehärtet.** Das `gen_date` aus
  `git log -1 --format=%cs -- LICENSES.md` formatiert das Datum sonst im
  Committer-TZ des betroffenen Commits – ein Merge-Commit mit
  `+02:00`-Offset (web-flow + CEST-Region) verschob den Tag dann um eine
  Position, sobald die UTC-Zeit knapp vor Mitternacht lag (Beispiel:
  `2026-05-26T23:10:10Z` ≡ `2026-05-27T01:10:10+02:00` → `%cs` =
  `2026-05-27`). Zusätzlich gewann das Datum des Merge-Commits dadurch
  Bedeutung, dass `actions/checkout@v5` bei `pull_request`-Events
  standardmäßig den synthetischen `refs/pull/N/merge`-Commit shallow
  auscheckt – ohne Parent vergleicht `git log -- LICENSES.md` nichts,
  und der Merge-Commit erscheint als „letzte Änderung". Fix:
  `fetch-depth: 0` in `actions/checkout` plus `TZ=UTC` und
  `--date=short-local` für den `git log`-Aufruf, sodass sowohl der echte
  Edit-Commit gefunden als auch das Datum deterministisch in UTC
  formatiert wird.

### Entfernt

- **Toten Code aus Canvas, Lasso und MainWindow entfernt.** Der ungenutzte
  Schatten-Zähler `ImageCanvas._version`, die nicht mehr referenzierte
  Methode `CanvasLasso.close_to_mask` und die ungenutzte Toolbar-Button-
  Group-Referenz `MainWindow._btn_grp` sind ersatzlos entfallen.

## [2.2.0] – 2026-05-25

### Hinzugefügt

- **Reproduzierbarer Dependency-Snapshot** (`requirements/constraints.txt`).
  Makefile, Lizenz-Workflow und macOS-App-Build verwenden denselben
  committeten Constraint-Satz für Test-, CI-, Lizenz- und App-Bundle-
  Installationen.
- **Lokaler Testumgebungs-Doctor** (`make doctor`,
  `scripts/check_test_env.py`). Prüft Python-Version, `[test]`-
  Abhängigkeiten, nicht-editable Paketinstallation, `bgremover`-
  Console-Script und Qt-`offscreen`, bevor ein lokaler Lauf tief in
  Pytest scheitert.
- **CI-Smoke-Test für den App-Start** (`tests/test_app_smoke.py`). Die
  bisherigen UI-Tests sind in der CI über `-m 'not ui'` ausgeschlossen,
  d. h. die CI prüfte nie, ob sich die Anwendung überhaupt vollständig
  starten lässt – genau die Lücke, durch die die macOS-Startfehler
  unbemerkt blieben. Neu, ohne `ui`-Marker (läuft also in der CI):
  `python -m bgremover` und das Console-Script `bgremover` werden aus
  einem neutralen Arbeitsverzeichnis vollständig hochgefahren (neuer
  Selbsttest-Hook `BGREMOVER_SMOKE_TEST` beendet nach dem ersten
  Event-Loop-Tick mit Exit-Code 0); das Qt-Plugin-Setup wird auf einen
  gültigen Plugin-Pfad geprüft; die Starter-Skripte
  (`create_BgRemover_app.sh`, `BgRemover.command`, `diagnose_mac.sh`)
  sowie der ins App-Bundle eingebackene Launcher werden auf
  Shell-Syntax geprüft. `zsh` wird dafür im Linux-CI-Job mitinstalliert.

### Geändert

- **MainWindow weiter modularisiert.** Die Persistenz- und Menülogik für
  „Zuletzt geöffnet“ liegt jetzt in `bgremover/recent_files.py`; `MainWindow`
  delegiert nur noch Laden, Statusmeldung und Einbindung ins Dateimenü.
- **Menü-/Action-Aufbau aus `MainWindow` extrahiert.** `bgremover/menu_actions.py`
  baut Menüleiste, `QAction`s, Shortcuts und Recent-Files-Untermenü; `MainWindow`
  übergibt nur noch die fachlichen Callbacks.
- **Rechtes Tab-Panel aus `MainWindow` extrahiert.** `bgremover/right_panel.py`
  baut Auswahl-, Hintergrund-, Transform- und Form-Tab inklusive Slider,
  Spinboxen und Panel-Buttons; `MainWindow` übergibt nur noch Canvas-Callbacks.
- **Worker-Steuerung aus `MainWindow` gekapselt.** `bgremover/worker_controller.py`
  besitzt jetzt Lade-, KI- und Warmup-Threads inklusive starker Worker-Referenz,
  `deleteLater`-Verdrahtung und gemeinsamem Shutdown.

### Behoben

- **Release-/Changelog-Links auf reale Refs korrigiert.**
  `[Unreleased]` vergleicht ab `v2.1.0`; `[2.1.0]` nutzt den
  dokumentierten 2.0.0-Release-Commit als Basis, weil im Repo kein
  historischer `v2.0.0`-Tag existiert.
- **KI-Ergebnisse werden nach Zwischenbearbeitungen verworfen.** Der
  Stale-Check nutzt eine öffentliche Canvas-Version, die der
  Content-Revision folgt und bei jeder sichtbaren Bildänderung steigt
  (z. B. Drehen, Zuschnitt, Undo). Dadurch überschreibt ein spät
  eintreffendes `rembg`-Ergebnis keine inzwischen bearbeiteten Bilder
  mehr.
- **App-Bundle: `bgremover`-Erkennung im Setup unabhängig vom
  Arbeitsverzeichnis.** `create_BgRemover_app.sh` stufte die venv als
  „fertig" ein, obwohl `bgremover` dort gar nicht installiert war: der
  `has_deps`-Check lief mit `cwd` im Projektordner, und Python hängt
  das aktuelle Verzeichnis automatisch an `sys.path[0]` – dadurch fand
  `import bgremover` das `bgremover/`-**Quellverzeichnis** des Repos
  statt einer echten venv-Installation. Der App-Launcher startet mit
  anderem `cwd`, sieht das Quellverzeichnis nicht und meldete deshalb
  „Das bgremover-Paket fehlt in der venv". `has_deps` und der finale
  Sanity-Check laufen jetzt aus `$HOME` (Subshell `cd "$HOME"`), prüfen
  also dieselbe Realität wie der Launcher; fehlt das Paket, greift der
  pip-Install-Schnellpfad. `diagnose_mac.sh` testet ebenfalls aus
  `$HOME` und zeigt zusätzlich `pip show bgremover` der App-venv
  (cwd-unabhängiger Beweis, ob/wohin das Paket installiert ist).
- **macOS-Startwege wieder funktionsfähig.** Nach dem Paket-Schnitt
  (Runde 5) suchte `BgRemover.command` weiterhin die nicht mehr
  existierende `BgRemover.py` und brach mit „nicht gefunden" ab; auch
  `INSTALL_MAC.md` (deutsch) plus die i18n-Versionen von
  `INSTALL_LINUX.md`/`README.md` zeigten teils noch die alten Kommandos
  (Schritt 15 des Paket-Schnitts hatte das deutsche `INSTALL_MAC.md`
  und die i18n-Installations-Doku im Glob übersehen, sowie
  `Exec=python3 /PFAD/.../BgRemover.py` in den i18n-`.desktop`-Mustern).
  Folge: auf macOS war keiner der drei dokumentierten Start-Wege
  (App-Bundle, Doppelklick auf `.command`, Terminal) verlässlich
  benutzbar. `BgRemover.command` startet jetzt via `python3 -m
  bgremover` und prüft vorab `import bgremover` (sonst sprechender
  Hinweis auf `create_BgRemover_app.sh`). INSTALL_MAC + alle i18n-Docs
  spiegeln das aktuelle Paket-Modell (inkl. nicht-editable Install des
  Pakets in die App-venv und `importlib.resources`-Asset-Lookup).
- **`create_BgRemover_app.sh`: bestehende venv wird sauber migriert.**
  Eine venv aus der Monolith-Ära (PyQt6/Pillow/numpy installiert, aber
  natürlich noch ohne `bgremover`) galt fälschlich als „ready", weil
  der Setup-Check `has_deps` `bgremover` nicht prüfte. Beim re-run des
  Skripts wurde das Paket-Install daher übersprungen – und der
  App-Launcher meldete dann zur Laufzeit „Das bgremover-Paket fehlt
  in der venv". Der Check umfasst nun auch `import bgremover`;
  zusätzlich gibt es einen Schnellpfad: existiert die App-venv schon
  mit PyQt6/Pillow/numpy, wird nur `pip install ".[ai]"` darin
  nachgeschoben (Sekunden), statt die venv mit allen Dependencies neu
  zu bauen (Minuten).

### Geändert

- **Pure Image-Operationen aus `ImageCanvas` gelöst.**
  `bgremover/image_ops.py` kapselt nun Hintergrund entfernen/ersetzen,
  Speichern, Drehen, Spiegeln, Ecken abrunden und Crop-Maskierung als
  Qt-freie PIL/NumPy-Funktionen. `ImageCanvas` behält UI-Zustand,
  Undo/Redo, Signale und Overlays; `tests/test_image_ops.py` prüft die
  Pixeloperationen direkt ohne `QApplication`.
- **Recommendations-Doku auf aktuellen Status gebracht.**
  `RECOMMENDATIONS.md` und die i18n-Versionen enthalten nun einen
  Runde-6-Statusblock für die jüngste PR-Serie (#70, #72–#78) und
  markieren die alten Monolith-Befunde ausdrücklich als historischen
  Kontext. `tests/test_recommendations_docs.py` schützt diesen Block.
- **Ressourcen-Doku synchronisiert.** `RESOURCES.md` und die i18n-
  Versionen spiegeln jetzt das Paketlayout (`bgremover/` statt
  `BgRemover.py`), die Paketdaten unter `bgremover/icons/`, den
  reproduzierbaren Constraints-Snapshot sowie PR-/Full-/Lizenz-
  Workflows. Ein statischer Test schützt diese Angaben gegen erneutes
  Veralten.
- **`make pr-check` macht die lokale PR-Prüfung robuster.** Der Target
  installiert das Paket frisch mit `[test]`, führt den Doctor aus und
  startet danach `ruff`, `mypy` und `pytest`. Das Makefile findet
  `.venv/bin/python` automatisch und fällt sonst auf `python`/`python3`
  zurück; GitHub PR CI und Full CI nutzen denselben Target. Das
  gemeinsame Qt-Plugin-Setup staged die Platform-Plugins bei Bedarf ins
  System-Temp-Verzeichnis, damit lokale macOS-Headless-Läufe nicht an
  Qt-Plugin-Listing-Problemen im Projektpfad scheitern.
- **Leichte PR-CI ergänzt und Test-Doku synchronisiert.** Pull Requests
  bekommen jetzt einen günstigen Ubuntu/Python-3.12-Workflow mit
  `make pr-check`; die volle Linux/macOS-Matrix bleibt Release- und
  manuellen Läufen vorbehalten. Die Test-Workflows installieren das
  Paket nicht-editable, damit die App-Smoke-Tests die installierte
  Realität aus fremdem `cwd` prüfen. `README`, i18n-READMEs,
  `TESTING.md` und `Makefile` beschreiben nun denselben Ablauf.
- **Monolith → Paket (Runde 5).** Die Einzeldatei `BgRemover.py`
  (3026 Zeilen) wurde in das installierbare Paket `bgremover/`
  aufgeteilt (14 Module: `constants`, `image_utils`, `icons`, `theme`,
  `workers`, `crop`, `canvas`, `widgets`, `settings_dialog`,
  `logging_config`, `main_window`, `app`, `__main__`, `__init__`).
  Start künftig via `python -m bgremover` oder dem Console-Script
  `bgremover`; die alte `python BgRemover.py`-Form entfällt
  ersatzlos. `BgRemover.py` ist gelöscht. Phasiert in **13 mechanischen
  Schritten** durchgeführt, jeder mit dem grünen Test-Oracle als Gate
  (140 Unit- + 16 UI-Tests, ruff, mypy). Einzige bewusste, verhaltens-
  neutrale Code-Änderung: `make_tool_icon` löst Icons jetzt über
  `importlib.resources` aus den Paket-Daten (`bgremover/icons/`) auf
  statt über `__file__`/`sys.argv`/`cwd` – Kontrakt unverändert.
  `pyproject.toml`, `Makefile`, CI-Workflow und macOS-Build-Skript
  (`create_BgRemover_app.sh`) sind im selben Schnitt mitgezogen; die
  venv installiert das Paket nicht-editierbar (inkl. package-data),
  daher unabhängig vom Projektordner.
- Übergangs-Re-Exporte in `BgRemover.py` (Phase B) und alle
  `BgRemover`-Test-Importe sind im finalen Schritt auf das Paket
  umgestellt.

## [2.1.0] – 2026-05-19

### Geändert

- Frühausstieg-Guard „Kein Bild geladen“ der fünf `ImageCanvas`-
  Methoden (`apply_round_corners`, `apply_rotate`, `apply_flip`,
  `start_crop_circle`, `start_crop_ratio`) im Decorator
  `@_requires_image` zusammengefasst – der zuvor byte-identisch
  wiederholte Block entfällt; Verhalten unverändert (durch die
  bestehende Test-Suite verteidigt).
- Hintergrund-Worker `AIWorker` und `ImageLoadWorker` nutzen jetzt die
  gemeinsame Basisklasse `_Worker`, die den identischen
  `try/except → logger.exception → error.emit`-Ablauf kapselt;
  Unterklassen implementieren nur noch `_work()`. `RembgWarmupWorker`
  bleibt bewusst eigenständig (kein `error`-Signal, `finished` stets im
  `finally`).
- Versions-Schnitt **2.1.0**: `pyproject.toml` und der
  `__version__`-Fallback in `BgRemover.py` auf `2.1.0` gehoben; die
  zuvor unter `[Unreleased]` gesammelten Änderungen (#48/#52/#53,
  INSTALL_LINUX, Runde 3/4) sind hiermit als 2.1.0 datiert.
- Interne Refaktorierung: Der in `_apply_pil`, `undo`, `redo`,
  `undo_to` und `restore_original` identische Bildzustands-Block
  (Pixmap setzen, Maske leeren, Ansicht aktualisieren) ist in die
  Helfer `_set_image_state()` / `_emit_history()` zusammengeführt.
  Verhalten unverändert (verteidigt durch die bestehende Test-Suite).
- UI-Farbpalette in `_Theme` zentralisiert: die mehrfach wiederholten
  Stylesheet-Farben (Akzent, Panel-/Tab-Hintergrund, Rahmen,
  Trennlinien, heller Text) verweisen jetzt auf eine zentrale Stelle,
  damit künftige UI-Erweiterungen konsistente Farben nutzen. Als
  byte-identisch verifiziert – alle 218 Widget-Stylesheets unverändert,
  kein visueller Unterschied.

### Entfernt

- Tote Stylesheet-Konstanten `BTN_STYLE` und `GRP_STYLE` (nirgends
  referenziert) entfernt.

### Behoben

- `save_image()` fängt E/A-Fehler ab (nicht beschreibbarer Pfad, voller
  Datenträger, unbekanntes Format) und meldet sie als Statusmeldung,
  statt unbehandelt zu propagieren – konsistent zu `apply_remove`/
  `apply_replace`. „Speichern unter…“ merkt einen fehlgeschlagenen Pfad
  nicht mehr als Quick-Save-Ziel.

### Dokumentation

- Installationsanleitung für Linux (`INSTALL_LINUX.md`) ergänzt:
  Systempakete je Distribution (apt/dnf/pacman), venv-Setup,
  Starter-Skript bzw. `.desktop`-Eintrag und Troubleshooting; im README
  verlinkt. Inkl. besonders einfachem Weg für Raspberry Pi OS (Desktop)
  ohne venv/pip (PyQt6/Pillow/numpy als Systempakete via `apt`), mit
  optionalem KI-Nachrüst-Schritt.
- `RECOMMENDATIONS.md` (+ i18n en/es/fr/uk/zh) um die Sektion „Runde 3"
  ergänzt: die bewertete Empfehlungsliste mit Status (erledigt #48/#52/
  #53/#51 bzw. offen), damit der Optimierungsstand dauerhaft im Repo
  nachvollziehbar ist.
- `RECOMMENDATIONS.md` (+ i18n en/es/fr/uk/zh) um „Runde 4 –
  Standortbestimmung & nächster Schritt" ergänzt: Code-Gesundheit
  (ruff/mypy sauber, 140 Tests grün) plus priorisierte Liste, was als
  Nächstes anzugehen ist. Empfohlener nächster Schritt: Release-Schnitt
  2.1.0 + git-Tag (kein git-Tag vorhanden trotz CHANGELOG-Behauptung;
  `[Unreleased]` seit 2.0.0 mit #48/#52/#53/#55 gefüllt).

## [2.0.0] – 2026-05-17

Erster dokumentierter 2.0.0-Release-Stand. Ein historischer
`v2.0.0`-Git-Tag existiert im Repo nicht.

### Funktionen

- KI-Hintergrundentfernung über `rembg` (optionales `ai`-Extra) inkl.
  Hintergrund-Warmup, damit der erste Klick nicht blockiert.
- Auswahlwerkzeuge: Zauberstab (vektorisierter Flood-Fill mit
  Toleranz-Slider), Pinsel, Radiergummi und Polygon-Lasso; Shift/Ctrl
  für additive bzw. subtraktive Auswahl.
- Hintergrund transparent setzen oder mit Farbe ersetzen.
- Transformationen: Drehen (90°-Schritte und freier Winkel), Spiegeln,
  Ecken abrunden, Zuschnitt in mehreren Formaten mit Rule-of-Thirds-Raster.
- Verlauf mit Undo/Redo (Toolbar-Buttons) und Sprung zu beliebigem
  früheren Schritt über ein schwebendes Historien-Popup.
- Drag & Drop sowie „Zuletzt geöffnet" (10 Einträge), beide über den
  asynchronen Lade-Worker – kein UI-Freeze.
- Speichern als PNG, JPEG, WebP oder TIFF.
- Persistente Einstellungen (Standard-Verzeichnisse, bevorzugtes
  Dateiformat) via `QSettings`.
- macOS-App-Bundle-Build (`create_BgRemover_app.sh`) inkl. isolierter
  venv, Apple-Silicon-Handling und Icon-Setzung; unterstützt Python
  3.10–3.15.

### Stabilität & Qualität

- Worker-Threads abgesichert (kein verfrühtes GC des Workers,
  sauberes Thread-Shutdown im `closeEvent`, KI-Race über monotonen
  Canvas-Versionszähler).
- Bildgrößen-Limit (40 MP) und Decompression-Bomb-Schutz beim Laden.
- Speicherbegrenzter Undo-Stack (256 MB) mit O(1)-Byte-Tracking.
- Plattformunabhängiger Log-Pfad (`bgremover.log` im App-Datenverzeichnis).
- 108 Tests; `ruff` und `mypy` als CI-Schritte; CI auf Ubuntu und macOS
  unter Python 3.10 und 3.12.
- `__version__` wird aus den Paket-Metadaten gelesen (Single Source);
  Version erscheint im Fenstertitel.

### Dokumentation & Lizenz

- Lizenz **GPL-3.0-or-later** (`LICENSE`); bedingt durch das
  GPL-lizenzierte PyQt6-Binding.
- `RESOURCES.md` (alle Bibliotheken/Werkzeuge/Assets samt Lizenzen),
  `LICENSES.md` und automatisierter Lizenz-/Compliance-Workflow.
- README mit Architektur, bekannten Einschränkungen und Installations-
  anleitung; ausführliche `INSTALL_MAC.md`.

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/5fa8025dbabd997484e4739b1f547e9c59aed319...HEAD
[2.3.0]: https://github.com/NikolayDA/picture_helper/compare/da7186869e63cf9612897b31d80a84c1cc409062...5fa8025dbabd997484e4739b1f547e9c59aed319
[2.2.0]: https://github.com/NikolayDA/picture_helper/compare/4f4bfc2a3adf154d86d4aa2f46b0149bb863bc66...da7186869e63cf9612897b31d80a84c1cc409062
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1...4f4bfc2a3adf154d86d4aa2f46b0149bb863bc66
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1
