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

Damit stehen `pytest`, `pytest-qt`, `ruff`, `mypy` und `PyYAML` (für die
Workflow-Wächter, #1016) bereit. Auf macOS
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
| `make doctor` | Prüft Python-Version, Test-Abhängigkeiten, Paketinstallation (editable Link auf diesen Checkout **oder** nicht-editable Install, #1053), Console-Script und Qt-`offscreen`; `make pr-check` ruft ihn mit `--require-installed` |
| `make pr-check` | **PR-Prüfung:** `install-test` + `doctor` + `ruff` + `mypy` + `pytest` (volle UI-Suite ausgeschlossen, `ui_smoke` läuft mit) + fail-closed Release-Pfadklassifikation |
| `make check` | Schnelle Wiederholung ohne Neuinstallation/Doctor: `ruff` + `mypy` + `pytest` |
| `make ui`    | Volle lokale UI-Interaktionssuite inkl. `ui_smoke`                         |
| `make all`   | Alles zusammen (`check` + `ui`)                                            |
| `make lint`  | `shellcheck` für Shell-Skripte (falls installiert) + `ruff` (Stil/Fehler)  |
| `make type`  | Nur `mypy` (Typprüfung)                                                    |
| `make test`  | Nur `pytest` (volle UI-Suite ausgeschlossen, `ui_smoke` läuft mit); `PYTEST_ARGS=…` reicht Zusatzargumente durch |
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

Für `make pr-check` müssen der Basis-Tag und die Git-Historie lokal vorhanden
sein; die PR-CI checkt sie deshalb mit `fetch-depth: 0` aus. So blockiert ein
neuer, noch nicht bewusst klassifizierter Pfad bereits den verursachenden PR
statt erst den späteren Release-Lauf.

Alles grün ⇒ der Stand entspricht lokal den automatischen PR-Prüfungen;
`make all` deckt zusätzlich die bewusst lokalen UI-Interaktionstests ab.

<!-- Achtung Maschinenformat: Die beiden folgenden Absätze werden von
tests/test_marker_governance.py geparst (Anker: _UI_LIST_RE,
_UI_SMOKE_LIST_RE, _BOTH_MARKERS_RE - die Muster dort zitieren die
tragenden Formulierungen; bewusst nicht hier wiederholt, damit dieser
Kommentar nie selbst zur Fundstelle wird). Jede in Backticks genannte
test_*.py-Datei innerhalb der Absätze zählt als dokumentiert - bei
Umformulierung die Anker in den Mustern nachziehen (gleiches Muster wie
beim gl_smoke-Absatz unten, #847/#852). -->
## Die UI-Tests

`tests/test_ui_interactions.py` enthält automatische, qtbot-gesteuerte
UI-Tests (Smoke, Zeichentools, Menü/Toolbar, Crop-Overlay,
SettingsDialog). Sie sind mit dem Marker `ui` versehen, ebenso
`tests/test_e2e_release_regression.py` und `tests/test_height16_e2e.py`.
Nur diese `ui`-markierten Tests laufen bei `make ui`/`pytest -m ui`
(volle, nightly UI-Suite).

Daneben trägt ein kleines, stabiles Subset schnellerer qtbot-Tests den
Marker `ui_smoke` – in `tests/test_workflow.py`,
`tests/test_right_panel.py`, `tests/test_resize_dialog.py`,
`tests/test_viewer_3d.py`, `tests/test_preview3d_integration.py`,
`tests/test_preview3d_acceptance.py`, `tests/test_screenshot3d.py`,
`tests/test_ai_model_dialog.py`, `tests/test_ai_install_dialog.py`,
`tests/test_eufymake_export_dialog.py`, `tests/test_acceptance_smoke.py`,
`tests/test_e2e_release_regression.py` und `tests/test_ui_interactions.py`.
Die meisten dieser Module tragen
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
tests/test_marker_governance.py geparst – bei Umformulierung dort
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
`tests/test_marker_governance.py` (#832/#847) ab: Der Test lässt pytest
in einem Subprozess ungefiltert sammeln und liest die Marker über das
Mini-Plugin `tests/_marker_collect_plugin.py` direkt aus den Item-Objekten
aus; verglichen werden sowohl die Dateiliste als auch die
Granularitätsaussage (modulweit vs. je ein markierter Test) gegen die oben
genannten Angaben. Die Inventur kostet je Testlauf einmalig eine zweite,
ungefilterte Kollektion des `tests/`-Baums (einige Sekunden, geteilt
zwischen den Prüfungen) – die kurze Pause beim ersten dieser Tests ist
also erwartet, kein Hänger. Dieselbe Inventur sichert seit #847 auch die
`ui`- und `ui_smoke`-Aufzählungen weiter oben ab – Dateilisten und die
Aussage „nur … tragen beide Marker", jeweils auf exakte Gleichheit. Das
frühere „u. a." vor der `ui_smoke`-Liste ist dabei entfallen: Eine
ausdrücklich unvollständige Aufzählung lässt sich gegen genau den Schaden
nicht absichern, um den es hier geht (#826 – die Liste wird unbemerkt
unvollständig).

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

### Gegenprobe auf Zielhardware: deutsche Locale, echte GPU (#1009)

Zwei Fehlerklassen kann die Offscreen-CI prinzipiell nicht sehen: Verhalten,
das von der Locale abhängt (die Runner laufen englisch; #1001), und das
GL-Gating auf echter GPU (die Runner haben keine; #1002, #1004). Beide
Befunde kamen aus einem `make check` auf einem deutsch eingerichteten
Raspberry Pi 5 (Debian 13, Broadcom V3D). Die Gegenprobe nach einem solchen
Fix ist deshalb ein Lauf auf dem Gerät – in drei Schritten, damit die
Ergebnisse zwischen Geräten und Ständen vergleichbar bleiben:

```bash
# 1. Standard-Gate unter deutscher Locale; make setzt QT_QPA_PLATFORM=offscreen.
#    -rs listet jeden Skip mit Grund – die Skips sind hier die Aussage.
LC_ALL=de_DE.UTF-8 make check PYTEST_ARGS=-rs

# 2. Die sechs Prüfstellen der Tabelle unten unter der Sitzungsplattform
#    (wayland oder xcb); die gl_smoke-Tests liegen in diesen Dateien.
LC_ALL=de_DE.UTF-8 make test QT_QPA_PLATFORM=wayland PYTEST_ARGS="-rs \
  tests/test_viewer_3d_gl.py tests/test_screenshot3d.py \
  tests/test_benchmark_preview3d_live.py tests/test_preview3d_capability.py \
  tests/test_scan_release_artifacts.py tests/test_e2e_release_regression.py"

# 3. Provenienz als eine JSON-Zeile: Plattform, Vendor, Renderer, Mesa-Version.
QT_QPA_PLATFORM=wayland python scripts/qt_gl_probe.py
```

`PYTEST_ARGS` reicht Zusatzargumente an `pytest` durch – Schritt 2 wählt
damit genau die Dateien der Tabelle aus, der Standardfilter aus
`pyproject.toml` bleibt wie in `make check` aktiv (ein bloßes `-m gl_smoke`
würde vier Prüfstellen der Tabelle deselektieren, statt sie laufen zu
lassen). Die Locale muss installiert sein (`locale -a | grep de_DE`;
Debian: `sudo dpkg-reconfigure locales`) – fehlt sie, überspringt sich die
Locale-Prüfung sichtbar, statt zu messen. Ein Software-Renderer (llvmpipe,
etwa unter `xvfb-run`) ist kein gültiges Ziel für Schritt 2 – seit #1013 aber
auch kein roter Lauf mehr: Live-Benchmark **und** nativer Screenshot-Lauf
überspringen sich dort sichtbar mit Grund, und der Gegenpfad in
`test_screenshot3d.py` prüft an derselben Stelle real nach, dass unter
llvmpipe **kein** Nachweis entsteht – und, sofern der Viewer `ready` erreicht,
dass es die Provenienz-Abweisung (#642) ist. Festgeschrieben wird der Zustand
bewusst nicht (die Capability-Probe ist notwendig, nicht hinreichend). Für die Gegenprobe zählt weiterhin
allein die echte GPU: Ein Skip ist kein Nachweis.

Erwartung je Prüfstelle – eine Abweichung ist ein neuer Befund mit eigenem
Issue, kein Anlass, den Test umzubauen:

| Prüfstelle | Schritt 1 (`offscreen`) | Schritt 2 (Sitzungsplattform, Hardware-GL) |
|---|---|---|
| `test_preview3d_capability.py::test_offscreen_default_probe_reports_unavailable` | misst deterministisch, kein Skip (Plattformregel aus #1002) | Skip „Testlauf auf einer renderfähigen Plattform" |
| `test_scan_release_artifacts.py::test_signature_state_is_locale_independent` | läuft echt, kein Locale-Skip | ebenso |
| `gl_smoke` in `test_viewer_3d_gl.py` (fünf Tests) | Skip „kann QOpenGLWidget nicht rendern" | laufen: Freispruch nach dem ersten Frame, ein verborgener Viewer wird nie abgestuft (#1004), eine fremde Freigabe mitten in `paintGL` reißt den Frame nicht ab (#1024) |
| `test_screenshot3d.py`: Fallback-Zweig und nativer Lauf | Fallback läuft, nativer Lauf skippt | Fallback skippt („GL-Capability vorhanden"), nativer Lauf schreibt PNG und Sidecar |
| `test_benchmark_preview3d_live.py`: Live-Test | Skip (Plattform) | läuft mit echtem Hardware-Kontext |
| 3D-Zustand in `test_e2e_release_regression.py` | läuft mit der produktiven GL-Regel | ebenso |

Das Ergebnis gehört als Kommentar in das auslösende Issue, in diesem Format:

```text
Gerät · OS · Locale     : Raspberry Pi 5 · Debian 13 · de_DE.UTF-8
Provenienz (Schritt 3)  : <JSON-Zeile von qt_gl_probe.py>
Schritt 1 (offscreen)   : <N passed, M skipped> + Skips mit Grund aus -rs
Schritt 2 (wayland/xcb) : <N passed, M skipped> + Skips mit Grund aus -rs
```

Die Container-Referenz für dieselben drei Schritte (`xvfb-run` + `xcb`,
llvmpipe) liegt im PR zu #1009; sie deckt die Locale-Klasse ab, die
GPU-Klasse nur das Gerät.

### Renderbeweis-Sonde: `frameSwapped` je Plattform messen (#1010)

Der Renderbeweis aus #1004 (`bgremover/viewer_3d.py`) spricht einen Viewer
frei, sobald Qt `frameSwapped` sendet, und stuft ihn nach drei
aufeinanderfolgenden Paints ohne Widget-Framebuffer ab. Weil
`bgremover/screenshot3d.py` seither `state`/`has_failed` liest, trägt der
Beweis das MUSS-Kriterium `MACOS-ARM-DMG-01` mit: Ein gesunder Viewer, der
seinen ersten Frame erst nach drei Paints tauschte, machte den nativen
3D-Nachweis rot – als Wächter-Fehlalarm, nicht als Renderfehler. Die
Messwerte je Plattform und Lage (Container `xcb`/`offscreen`, Abnahme-Runner
`cocoa`) hält der ADR-Nachtrag
[`docs/history/ADR-2026-3d-reliefvorschau-renderer.md`](docs/history/ADR-2026-3d-reliefvorschau-renderer.md);
neu fällig ist die Messung vor dem ersten Abnahmelauf auf einer neuen
Plattform und nach einem Qt-Sprung.

Die Sonde ist `scripts/render_proof_probe.py`: eine Unterklasse des Viewers,
die nur mitzählt, was der Beweis ohnehin auswertet, gegen den Quellbaum läuft
(nicht gegen ein Artefakt) und **nicht bewertet** – Exit 0 heißt „gemessen",
Exit 2 „nicht ausführbar". Zwei Größen entscheiden die Frage: der
`defaultFramebufferObject()`-Wert **je** Paint (nur eine 0 lässt die
Abweisungszählung überhaupt anlaufen) und `erster_swap` – nach wie vielen
Paints und wie vielen Millisekunden nach `show()` Qt den ersten Frame
tauscht. Die Endzähler allein beantworten sie nicht. Zwei Wege auf ein Gerät:

```bash
# Von Hand, aus dem Repo-Wurzelverzeichnis, in der angemeldeten Sitzung und
# OHNE gesetztes QT_QPA_PLATFORM (macOS: cocoa · Linux: wayland oder xcb):
.venv/bin/python scripts/render_proof_probe.py
# optional: --lage sichtbar --ms 2000 --json-out sonde.json --summary sonde.md
```

```bash
# Über den Heartbeat-Workflow, auf jedem aktiven Self-hosted Runner:
gh workflow run runner-heartbeat.yml --repo NikolayDA/picture_helper -f render_probe=true
```

Der Dispatch fährt die Sonde nach dem Preflight in einem eigenen venv (`-e .`
mit den Pins aus `requirements/constraints.txt`); die Kopfzeile und die drei
Zeilen stehen im Joblog des Plattform-Jobs, die Tabelle in dessen
Job-Zusammenfassung. Die Sonde trägt nie das Heartbeat-Verdikt: eigenes
Zeitbudget, Wheel-only-Install, `continue-on-error` – ein Scheitern steht als
Schritt-Warnung im Lauf, nicht als Gerätebefund in der Auswertung
([`docs/RELEASE_AUTOMATION.md`](docs/RELEASE_AUTOMATION.md) §7). Drei Wächter
halten die Sonde: `tests/test_viewer_3d.py` bindet sie an die Viewer-API und
an die echten Signaturen von `HeightField`/`build_relief_mesh`,
`tests/test_render_proof_probe.py` prüft Zeilenformat, Tabelle, JSON und die
Lage `verborgen` (dort malt Qt nie – alle Zähler 0, in jeder Umgebung),
`tests/test_runner_heartbeat_workflow.py` hält den Dispatch-Schalter.

Erwartung je Lage **auf einer renderfähigen Sitzungsplattform** – eine
Abweichung ist ein neuer Befund mit eigenem Issue, kein Anlass,
`_MAX_REFUSED_PAINTS` zu erhöhen:

| Lage | Erwartung |
|---|---|
| sichtbar | `frameSwapped` ≥ 1, `erster_swap` gesetzt, `_has_rendered=True`, `_refused_paints=0`, `has_failed=False` |
| verborgen | Qt malt gar nicht: alle Zähler 0, `has_failed=False` (kein Urteil) |
| verdeckt | wie „sichtbar" **oder** wie „verborgen" – nie `has_failed=True` |

Zwei Lesefallen. Erstens ist die Vorbedingung wörtlich gemeint: Unter
`offscreen` misst die Sonde gemessen `has_failed=True` – das ist dort der
**richtige** Befund (kein Widget-Framebuffer) und keine Abweichung. Zweitens
entscheidet nicht `has_failed` allein, sondern `grund` (`failure_reason`) –
die Sonde druckt ihn mit. Gesucht ist `has_failed=True` bei
`_has_rendered=False`, `frameSwapped=0` und einem `grund`, der
`Widget-Framebuffer` nennt. Derselbe `grund` **zusammen mit**
`_has_rendered=True` kann seit dem Fix am Freispruchsweg nicht mehr entstehen:
Ein Frame nach der Schwelle nimmt die angeforderte Abstufung zurück
(`_clear_pending_failure`, Regressionstests in `tests/test_viewer_3d.py`);
tritt die Kombination trotzdem auf, ist sie ein **neuer** Befund dort und
**nicht** der Anlass, `_MAX_REFUSED_PAINTS` plattformbewusst zu machen. Jeder
andere `grund` (`initializeGL:`, `paintGL:`, `_ensure_buffers:`) ist ein
gewöhnlicher GL-Fehler und gehört nicht in diesen Abschnitt – der Viewer
scheitert dort **nach** einem gelieferten Frame, `_has_rendered=True` ist dann
regulär. Die verdeckte Lage braucht
zusätzlich einen echten Fenstermanager: Unter `xvfb-run` ohne WM verdeckt das
zweite Fenster nichts und die Zeile misst dasselbe wie „sichtbar". Und
`setGeometry`/`raise_()` sind nur Wünsche an den Fenstermanager – die Sonde
hängt der Zeile deshalb ein `hinweis=` an: Unter Wayland setzt der Compositor
Position und Stapelung selbst, die Verdeckung bleibt dort **unbestätigt** und
die Zeile belegt nur „nie `has_failed`"; auf `cocoa`/`xcb` steht drin, ob der
Deckel den Viewer geometrisch umschließt und ob dessen Fenster noch `exposed`
ist.

Das Ergebnis gehört in den ADR-Nachtrag (eine Tabellenzeile je Lage; die
`--summary`-Tabelle hat dasselbe Spaltenschema, nur die letzte Zelle
„Ergebnis" trägt dort den `grund` des Viewers und wird beim Übernehmen zur
Einordnung gesund / kein Urteil / [F]) und als Kommentar in das auslösende
Issue – Kopfzeile und die drei Ausgabezeilen der Sonde wörtlich:

```text
Gerät · OS · Qt : <Modell> · <OS> (<Arch>) · Qt <Version> / PyQt <Version> · Plattform <cocoa|xcb|wayland> · Renderer <GL_RENDERER>
<die drei Zeilen „sichtbar/verborgen/verdeckt" der Sonde, unverändert>
```

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

### Wo liegen die Tests zu Modul X? (#869)

Die meisten Module haben eine gleichnamige Testdatei
(`bgremover/height_ops.py` → `tests/test_height_ops.py`) – wer sie ändert,
findet die Tests über den Dateinamen. Für die folgenden Module gilt das
**nicht**: Sie werden bewusst in größeren Sammeldateien mitgeprüft (vor allem
`tests/test_right_panel.py`). Ein Contributor, der etwa
`bgremover/expert_mode_toggle.py` isoliert ändert, übersieht die zugehörigen
Tests sonst leicht.

Die Tabelle nennt die Suiten, die nach einer Änderung am Modul laufen sollten
– nicht dessen vollständige Abdeckung. Sie ist **vollständig** und wird von
`tests/test_module_test_map.py` netzfrei in beide Richtungen erzwungen: jedes
Modul ohne gleichnamige Testdatei hat genau eine Zeile, jede Zeile nennt ein
Modul ohne gleichnamige Testdatei, und jede genannte Datei **importiert** das
Modul – direkt (`from bgremover.<modul> import …`) oder über ein
Paket-Re-Export-Symbol (`from bgremover import CropOverlayItem`). Bewusst zählt
nur die Import-Anweisung, nicht der freie Dateitext: Ein Texttreffer auf kurze,
allgegenwärtige Exporte wie `tr` hätte fast jede Testdatei als „Beleg"
durchgehen lassen. Bekommt ein Modul später eine eigene Testdatei, ist seine
Zeile zu entfernen.

| Modul | Mitgeprüft in |
| --- | --- |
| `bgremover/_version.py` | `tests/test_version.py` |
| `bgremover/canvas.py` | `tests/test_image_canvas.py`, `tests/test_canvas_layers.py`, `tests/test_canvas_events.py` |
| `bgremover/canvas_lasso.py` | `tests/test_lasso.py` |
| `bgremover/canvas_transform.py` | `tests/test_geometry.py` |
| `bgremover/canvas_viewport.py` | `tests/test_viewport.py`, `tests/test_zoom_control.py` |
| `bgremover/constants.py` | `tests/test_canvas_events.py`, `tests/test_height_tools.py` |
| `bgremover/crop.py` | `tests/test_crop_overlay.py`, `tests/test_ui_interactions.py` |
| `bgremover/expert_mode_toggle.py` | `tests/test_right_panel.py` |
| `bgremover/height_map_panel.py` | `tests/test_right_panel.py` |
| `bgremover/i18n.py` | `tests/test_i18n_runtime.py`, `tests/test_i18n_rollout.py`, `tests/test_i18n_coverage.py` |
| `bgremover/image_loading.py` | `tests/test_workers.py`, `tests/test_canvas_layers.py` |
| `bgremover/image_utils.py` | `tests/test_helpers.py`, `tests/test_flood_fill.py` |
| `bgremover/layer_panel.py` | `tests/test_right_panel.py` |
| `bgremover/logging_config.py` | `tests/test_logging.py`, `tests/test_settings_dialog.py` |
| `bgremover/main_toolbar.py` | `tests/test_icons.py` |
| `bgremover/preview_mode.py` | `tests/test_canvas_layers.py`, `tests/test_right_panel.py` |
| `bgremover/project_schema.py` | `tests/test_project_io.py`, `tests/test_project_v270_upgrade.py` |
| `bgremover/right_panel_tabs.py` | `tests/test_right_panel.py`, `tests/test_i18n_coverage.py` |
| `bgremover/status_messages.py` | `tests/test_i18n_runtime.py`, `tests/test_canvas_events.py` |
| `bgremover/stepper.py` | `tests/test_workflow.py`, `tests/test_right_panel.py` |

## Doku-Governance-Tests

Dokumentation wird wie Code geprüft: netzfrei, fail-closed, im Standard-Gate.
Diese Wächter laufen mit `make check` und brauchen weder Qt noch Netzzugang.

| Wächter | Hält fest |
| --- | --- |
| `tests/test_markdown_links.py` | Repo-weit: jedes lokale Link-/Bildziel existiert **und** jeder dokumentinterne Anker (`](#abschnitt)`, auch `pfad.md#abschnitt`) zeigt auf eine echte Überschrift (#965) |
| `tests/test_i18n_docs.py` | Struktur-Parität der sechs Sprachfassungen (Überschriften, Codeblöcke, Tabellen) plus inhaltliche Marker |
| `tests/test_screenshot_references.py` | Eingebettete Screenshots zeigen auf den aktuellen Satz |
| `tests/test_anleitung_pdf_sync.py` | `ANLEITUNG.pdf` fällt weder hinter `ANLEITUNG.md` noch hinter `scripts/generate_anleitung_pdf.py` zurück — geprüft über die Git-Mitänderung, nicht über Bytes (#974) |
| `tests/test_resource_docs.py` | `RESOURCES.md` gegen den CI-Stand |
| `tests/test_changelog_metadata.py` | CHANGELOG-Abschnitte und AppStream-Metadaten |

Die Ankerprüfung bildet die GitHub-Slug-Regel nach (Kleinschreibung,
Satzzeichen entfallen ersatzlos, Leerzeichen zu `-`, Dubletten mit `-1`);
Umlaute, Kyrillisch und CJK bleiben dabei erhalten. Überschriften in
Codeblöcken erzeugen keinen Anker. Die geteilten Helfer dafür liegen in
`tests/_markdown_utils.py` – wer eine Markdown-Prüfung ergänzt, nutzt sie von
dort, statt sie ein drittes Mal zu kopieren. Dasselbe gilt für den
Qt-frei-Wächter `tests/_qt_free_check.py` (#1044): `assert_module_is_qt_free`
prüft per AST, dass ein Modul kein Qt-Binding importiert; die vier Tests, die
diese Regel zuvor als Kopie trugen, nennen ihm nur noch ihr Modul, und
`tests/test_qt_free_check.py` hält die Regel selbst mit einer Negativkontrolle
(`viewer_3d`) fest. Externe `http(s)`-Links prüft
bewusst niemand: Das bräuchte Netzzugang und gehört nicht ins Standard-Gate.

`ANLEITUNG.pdf` wird von Hand erzeugt und lässt sich nicht über Bytes
prüfen — der Bau ist nicht deterministisch. Der Wächter prüft deshalb die
Mitänderung in der Git-Historie — für die Quelle **und** für den Generator,
denn dessen `_css()` geht ebenso ins PDF ein. Trägt die Historie keine
Aussage, wird mit
Begründung übersprungen: In einem flachen Klon ist der Grenzcommit
elternlos und gilt `git log` als Hinzufüger jeder Datei, sodass beide Pfade
auf denselben Commit auflösen — das sähe wie „synchron" aus, ohne es zu
sein. Ein flacher Klon genügt aber, solange die letzten Commits beider
Dateien innerhalb seiner Tiefe liegen. Die PR-CI checkt mit
`fetch-depth: 0` aus und prüft dort immer; `coverage.yml` und
`ui-nightly.yml` laufen mit Tiefe 1 und überspringen sichtbar.

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
  importierbar ist und ob das Console-Script auf `PATH` liegt. Ein editable
  Link auf diesen Checkout (wie ihn der SessionStart-Hook anlegt) ist dort
  seit #1053 `OK`, nicht `FAIL`; nur `make pr-check` verlangt per
  `--require-installed` den nicht-editable Install. Meldet der Doctor
  „matches neither contract", liegt ein Link auf einen fremden Checkout oder
  eine veraltete Kopie neben dem Link vor – dann `make install-test`
  (pr-check) oder `pip install -e ".[test]"` (Session), nicht beides.
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
