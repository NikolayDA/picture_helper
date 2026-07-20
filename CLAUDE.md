# CLAUDE.md

Kurzanleitung für Claude Code in diesem Repository. **BgRemover** ist ein
Desktop-Tool zum Entfernen von Bildhintergründen und für einfache
Bildbearbeitung (PyQt6, macOS + Linux, Python ≥ 3.10).

## Standard-Gate (vor jedem PR)

Alles läuft über den Makefile-Wrapper. Er nutzt `python -m <tool>` (robust
gegen PATH-/venv-Eigenheiten) und setzt `QT_QPA_PLATFORM=offscreen` für den
headless-Qt-Betrieb:

- `make check` — Lint + Typecheck + Tests. **Die maßgebliche Baseline.**
- `make lint` — `ruff check bgremover scripts tests` (+ shellcheck, falls installiert)
- `make type` — `mypy`
- `make test` — `pytest` (ohne volle UI-Suite, das `ui_smoke`-Subset läuft mit)
- `make coverage` — Coverage-Report (`fail_under = 86`)
- `make ui` — volle qtbot-UI-Suite (sonst nur nightly)
- `make pr-check` — wie die PR-CI: nicht-editable Install + `doctor` + `check`
- `make doctor` — prüft die Test-Umgebung (`scripts/check_test_env.py`)

Bei direkten `pytest`-Aufrufen `QT_QPA_PLATFORM=offscreen` setzen; `make` und
`tests/conftest.py` (per `setdefault`) erledigen das selbst. Das PR-Template
(`.github/PULL_REQUEST_TEMPLATE.md`) führt die Standard-Gate-Checkliste (#557).

## Architektur

Ein Paket, `bgremover/`:

- **Einstieg:** `app.py` (`main()`), `__main__.py` → `python -m bgremover`;
  `main_window.py` verdrahtet die UI.
- **Canvas/Bearbeitung:** `canvas.py` + `canvas_*.py` (Selection, Lasso,
  Transform, Viewport, Crop), `crop.py`, `image_ops.py`, `image_utils.py`;
  `image_loading.py` ist der gemeinsame Lade-Helfer für Canvas und Worker. Der
  Canvas hält ein `Project` (#330) und rendert/speichert das **Komposit**;
  Werkzeuge wirken auf die **aktive Ebene** (`self._pil`/`_arr` sind deren Cache),
  größenändernde Geometrie (Drehen/Zuschnitt via `apply_geometry`) auf alle Ebenen;
  Undo/Redo läuft über `ProjectHistory`. Einzel-COLOR-Ebene = bitgenaue Parität
  zum bisherigen Einzelbild-Editor (#332). Die Anzeige ist seit #387 explizit über
  `PreviewMode` gesteuert (Enum in `preview_mode.py`) und unabhängig von der aktiven
  Editierebene; der getrennte Exportpfad schreibt weiterhin ausschließlich das
  COLOR-Komposit (#363).
- **Grundbildbearbeitung (Phase 0, Epic #358):** **Skalieren** auf Zielgröße
  (`image_ops.resize_image`/`resized_size`, `Project.resize` skaliert alle Ebenen +
  Canvas-Größe mit Megapixel-Gate, Dialog `resize_dialog.py`, #359);
  **Farbkorrektur** Helligkeit/Kontrast/Sättigung in `color_ops.py` (Qt-frei,
  `adjust_color`, alpha-erhaltend) mit generischer Canvas-Live-Vorschau
  (`preview_color_op`/`cancel_color_preview`/`apply_color_op`, transientes
  `_preview` hat in `_refresh_image` Vorrang – wie #348) auf der aktiven
  COLOR-Ebene (#360); **Kantenglättung/Feather** der Alphakante
  (`image_ops.feather_alpha`, nur Alpha, auswahlbegrenzt, `feather_active_edges`,
  #361). Alles undo-/redobar über die bestehenden Apply-Pfade.
- **Höhenkarten:** `height_map.py` — Qt-freie, strikt getypte Höhen-Repräsentation
  (Fundament des Height-Map-Epics #344/#345): verlustfreie Konvertierung Höhe ↔
  Graustufen-Array (`HeightField`, Konvention `R=G=B=Höhe`, `A=Deckung`),
  Normalisierung beliebiger Werte auf den Höhenbereich und Canvas-Größen-Validierung.
  Seit #587 gilt der 16-Bit-Vertrag aus ADR #586: `max_value` ist auf **255**
  (Legacy) und **65535** (kanonisch) beschränkt, die Arrays sind nach Konstruktion
  write-gelockt (Aliasing-Verstöße werfen), `expand_to_16bit` ist die
  deterministische ×257-Migration und `resize_height_field` skaliert
  präzisionserhaltend (Werte als `float32`, Deckung als `L`, gleicher Filter). `generate_from_image`
  erzeugt deterministisch eine Höhenkarte (Kanalgewichtung/Luminanz → Tonwert-Kennlinie
  → Gamma → Invertieren) (#346), seit #589 im Canvas direkt auf `0..65535` skaliert.
  `image_to_height_field` ist die dokumentierte Import-Regel (#589): 16-Bit-Graustufen
  (`I;16*`/wertebereichsgeprüftes `I`) nativ mit allen 65536 Stufen, 8-Bit-/Farbquellen
  über die Luminanz-Regel ×257-äquivalent, Float-Modi abgewiesen
  (`UnsupportedHeightSourceError`); das Modul-Docstring führt das verbindliche
  Operations-Inventar (16-Bit-sicher / bewusst quantisierend / nicht anwendbar).
  Der Canvas verdrahtet das (`generate_height_map` aus aktiver COLOR-Ebene/Komposit,
  `import_height_map` via `open_validated_height_image` ohne RGBA-Zwang, fremde
  Größen präzisionserhaltend über `resize_height_field`) als neue, aktive
  HEIGHT-Ebene mit Rolle `HEIGHT_MAP` direkt aus der kanonischen Payload,
  undo-/redobar. Höhen-Editor (#347): `adjust_height`/`set_height`/`invert_height`
  (auswahlbewusst, geklemmt, verlustfrei) – im Canvas als `lighten_/darken_/set_/
  invert_active_height` an der aktiven HEIGHT-Ebene verdrahtet (Auswahl bzw. global,
  undo-/redobar; auf COLOR-Ebenen wirkungslos).
- **Höhen-Optimierung:** `height_ops.py` — Qt-freie, strikt getypte, 16-Bit-taugliche
  Operationen auf `HeightField` (#348): `levels`/`gamma` (Tonwert), `gaussian_blur`/
  `median_blur` (Glättung, separabel bzw. kantenerhaltend, rein in numpy), `threshold`,
  `quantize` (Stufen), `clamp_range`. `median_blur` rechnet **zeilenbandweise** und
  begrenzt seinen Fensterstapel hart über `_MEDIAN_MAX_TEMP_BYTES` – der Zusatzspeicher
  ist vom Bildmaß unabhängig (kein `O(H × W × (2r+1)²)`-Vollstapel mehr), bitgenau zur
  alten Variante; `gaussian_blur` ist separabel und damit `O(H × W)`/radiusunabhängig
  (#365). Geteilte Tonwert-/Graustufen-Primitive (Synergie
  mit der späteren geteilten Engine). Im Canvas als generische Live-Vorschau verdrahtet:
  `preview_height_op`/`cancel_height_preview` (transient, ohne Modelländerung) und
  `apply_height_op` (Commit, undo-/redobar); transiente Farb-/Höhenpixel werden als
  temporärer Layer-Override durch die explizite Vorschau-Pipeline gerendert und bei
  jedem Zustandswechsel verworfen (#397).
- **2D-Relief-/Gloss-Vorschau:** `relief_preview.py` (#385) berechnet aus einem
  `HeightField` ein neutrales, richtungsabhängiges Hillshade (Azimut/Elevation,
  8-/16-Bit-äquivalent, `coverage`-bewusst) und komponiert es multiplikativ über
  RGBA. `gloss_preview.py` (#386) rendert eine Gloss-Maske als kühlen Sheen und
  mischt ihn über RGBA. Beide Module sind Qt-frei, strikt getypt, größenvalidiert
  und erhalten den Alpha-Kanal des Farbmotivs bitgenau. Die Canvas-Pipeline (#387)
  bietet `COLOR`/`RELIEF`/`HEIGHT`/`GLOSS`/`COMBINED`, gecacht auf genau ein Bild
  je Content-Revision + Anzeigeparameter. Modus, Relief-Stärke und Gloss-Sichtbarkeit
  sind reiner UI-Zustand (keine History-/Dirty-Revision); unsichtbare Datenrollen
  werden ignoriert und Relief-Stärke 0 überspringt das Hillshade vollständig (#397).
  Seit #590 rechnet das Relief-Hillshade direkt aus der kanonischen 16-Bit-Payload
  (`layer.height_data`); nur eine transiente Live-Vorschau (Override) nutzt die
  getauschte 8-Bit-Ansicht als dokumentierte Anzeige-Ausnahme.
  Ein Vorschau-Tab und das exklusive Ansicht-Untermenü halten sich signalbasiert
  synchron; der UI-Hinweis macht den unveränderten Bildexport ausdrücklich sichtbar
  (#388).
- **Echte 3D-Reliefvorschau (Epic #582, umgesetzt #592–#595):** Qt-nativer
  OpenGL-Viewer über einem Qt-freien, backend-neutralen Geometriekern – ADR
  [`docs/history/ADR-2026-3d-reliefvorschau-renderer.md`](docs/history/ADR-2026-3d-reliefvorschau-renderer.md)
  (#591), UX-Vertrag [`docs/UX_3D_PREVIEW.md`](docs/UX_3D_PREVIEW.md).
  `relief_mesh.py` — Qt-freier, strikt getypter Geometriekern (#592): erzeugt
  aus einem `HeightField` deterministisch ein **hart begrenztes** Grid-Mesh
  (`ReliefMesh`, frozen numpy-DTO). Block-Decimation ist **coverage-gewichtet**
  und läuft **zeilenbandweise** mit hartem 64-MiB-Temp-Deckel (Muster von
  `height_ops._MEDIAN_MAX_TEMP_BYTES`, #365) – die Decimation greift **vor**
  jeder float-Expansion auf dem `uint16`-Feld, ein 40-MP-Bild erzeugt daher nie
  ein Vollmesh. Vertex-/Dreiecksbudget je `MeshQuality` (REDUCED/STANDARD/HIGH),
  Winding CCW von `+Z`, Löcher statt Brückendreiecke (Vertex gültig ⇔ Deckung
  ≥ 128); Normalen analytisch, `slope` exaggerations-unabhängig für den
  Uniform-Pfad des Viewers; `mesh_cache_key` deckt genau die geometrie-
  bestimmenden Größen ab (nicht Kamera/Licht/Überhöhung). Quelldaten werden nie
  mutiert (Hash-Tests), Abbruch über Cancel-Token wirft `MeshBuildCancelled`.
  `preview3d_camera.py` — Qt-freie Orbit-Kamera (Polhöhen-Klemme ±88°,
  Zoom-/Fit-Klemmen, `look_at`/`perspective`, Spaltenvektor-Konvention).
  `preview3d_capability.py` — Laufzeit-Probe (`probe_3d_capability`, über
  `probe_fn` mockbar) für Desktop-GL ≥ 2.1; wirft nie, liefert strukturiertes
  `RendererCapability`, je Sitzung gecacht (`reset_capability_cache` = „Erneut
  versuchen"). Der Offscreen-CI-Pfad trifft real den Fallback-Zweig.
  `viewer_3d.py` — `GLReliefViewer` (`QOpenGLWidget`, GL-2.1-Shaderpfad über
  `QOpenGLVersionFunctionsFactory`, alle GL-Hooks gekapselt → `initFailed`,
  keine neue Laufzeitabhängigkeit) und der einbettbare, GL-frei testbare
  Zustandscontainer `Relief3DView` (Empty/Unavailable/Loading/Error/Ready).
  `preview3d_controller.py` (`Preview3DController`, #594) orchestriert Gating,
  entprellten (200 ms) asynchronen Mesh-Build (`MeshBuildWorker` über den
  `WorkerController`) mit **Generation-IDs** (stale-result-Schutz) und einem
  **Ein-Mesh-Cache**; Kamera/Licht/Überhöhung sind reine Uniforms ohne Rebuild.
  Verdrahtung im `MainWindow`: Canvas-Stack (2D-Leinwand ↔ 3D-Viewer), Segment
  **Darstellung [2D|3D]** oben im Höhen-Tab (`height_map_panel.Preview3DActions`)
  und „Ansicht → 3D-Relief anzeigen"; Qualität als QSettings-Präferenz
  (`PREVIEW3D_QUALITY_KEY`). Der Viewer ist **reine Darstellung ohne Schreibpfad
  ins Modell** – „Bild speichern", EufyMake- und Projekt-Export bleiben
  unverändert; die 2D-`PreviewMode`-Pipeline bleibt der garantierte Fallback.
  i18n-Keys `preview3d.*` (de/en). Abnahme-Nachweise (#595): Mesh-Build-Benchmark
  (`scripts/benchmark.py`, `mesh_*`-Metriken je 1/16/40 MP, reproduzierbar via
  `--suite height`), headless-Abnahme in
  `tests/test_preview3d_acceptance.py`, Kriterien↔Nachweis in
  [`docs/history/EPIC-582-ABNAHME.md`](docs/history/EPIC-582-ABNAHME.md), manuelle
  Plattform-/Packaging-/Screenshot-Prozeduren (Release-Scope) in
  [`docs/PACKAGING_SMOKE.md`](docs/PACKAGING_SMOKE.md).
- **Domänenmodell:** `project_model.py` — Qt-freies, strikt getyptes Projekt-/
  Ebenen-Modell (`Project`/`Layer`, `LayerKind`/`LayerRole`, reine Operationen
  inkl. Farb-Komposit). Fundament des Ebenen-Epics (#329); ohne Render-/
  Persistenz-/History-Anbindung. **Kind↔Rollen-Vertrag (#364):** Eine Ebene ist
  *genau dann* höhenfähig, wenn `kind is LayerKind.HEIGHT`; `LayerRole.HEIGHT_MAP`
  darf nur auf einer HEIGHT-Ebene liegen. Die zentrale Qt-freie Regel
  `role_allowed_for_kind(role, kind)` ist die *einzige* Quelle der Wahrheit –
  `Layer.__init__` und `assign_role` lehnen inkompatible Kombinationen mit
  `IncompatibleRoleError` ab; Modell, Persistenz, Layer-/Height-Panel und Canvas
  konsultieren ausschließlich diese Funktion (kein Drift). Das Laden
  inkompatibler Altzustände normalisiert verlustfrei (siehe Persistenz).
  **16-Bit-HEIGHT-Payload (#587, ADR #586):** Eine HEIGHT-Ebene hält ihre Höhen
  kanonisch in `Layer.height_data` (`HeightField`, `uint16`, `max_value=65535`);
  `Layer.image` ist dort nur die abgeleitete 8-Bit-Ansicht (je Payload-Änderung
  einmal neu berechnet, nie zurückgelesen). Schreibpfad: `set_height_data`/
  `Project.set_layer_height_data` (canvas-validiert); 8-Bit-Zuweisungen an
  `layer.image` laufen über einen befristeten, geloggten Legacy-Adapter (×257,
  verbleibt seit #589 nur als geloggter Rückfall für generische
  RGBA-Pixelwerkzeuge auf HEIGHT-Ebenen und für v1-Projekte).
  `duplicate_layer` teilt die unveränderliche Payload,
  `Project.resize` skaliert sie über `resize_height_field`; die transiente
  Canvas-Vorschau tauscht nur die Ansicht (`swap_display_view`). `project_history.py` (`ProjectHistory`) ist die
  ebenenbewusste, Qt-freie Undo/Redo-Historie darauf: leichte Struktur-Snapshots
  + deduplizierter Pixelpool (geteiltes Undo-/Redo-Budget; unveränderte Ebenen
  zählen nur einmal) – im Canvas verdrahtet (#331/#332). HEIGHT-Snapshots
  referenzieren die Payload (3 B/px statt 4-B/px-Ansicht) und stellen sie bei
  Undo/Redo bitgenau wieder her (#587).
- **Projekt-Persistenz:** `project_io.py` + `project_schema.py` — Qt-freier
  `.bgrproj`-Round-Trip (ZIP: `manifest.json` + eine RGBA-PNG je Ebene), atomar
  geschrieben (`mkstemp`+`os.replace`) und defensiv geladen (Größen-/Megapixel-
  Limits, Zip-Slip-Abwehr, klare i18n-Meldungen); versioniertes Schema mit
  Migrationshaken (#333). Eine **neuere** (Zukunfts-)Formatversion wird seit
  #614 vor jeder Payload-Verarbeitung strikt mit verständlicher, übersetzter
  Meldung abgewiesen (`project.error.future_version`, Datei bleibt
  unangetastet) – kein Best-effort-Laden mehr, damit ein alter Stand fremde
  Formatdaten nicht unbemerkt verlieren kann.
  **Formatversion 2 (#588, ADR #586):** je HEIGHT-Ebene zusätzlich eine
  16-Bit-Graustufen-PNG (`layer_NNNN_height16.png`) mit den kanonischen
  `uint16`-Höhen – endianness-kontrolliert über numpy geschrieben/gelesen,
  per `height16_sha256` im Manifest gegen abgeschnittene/vertauschte Payloads
  gesichert und mit eigenem 2-B/px-Entry-Limit; der Roundtrip ist bitgenau
  inkl. Niederbits. v1 lädt unverändert über den ×257-Adapter (#587) und wird
  beim Speichern kontrolliert v2; echte v2-Dateien verlangen die Payload-
  Deklaration je HEIGHT-Ebene (Ursprungsversion wird vor der Migration
  geprüft), ältere Stände (≤ 2.6.0) weisen v2 als unerwarteten Eintrag ab
  (klarer Fehler statt stiller Beschädigung). Formatreferenz:
  [`docs/PROJECT_FORMAT.md`](docs/PROJECT_FORMAT.md). Beim Laden wird
  ein historisch inkompatibler Rollen-Zustand (z. B. `HEIGHT_MAP` auf einer
  COLOR-Ebene) deterministisch normalisiert: nur die unzulässige Rolle wird
  entfernt (Kind/Name/Pixel/Reihenfolge/Metadaten bleiben wertgleich), und
  `load_project(..., warnings=...)` reicht eine übersetzte Warnung an die UI
  (Statusleiste) durch (#364). Menü-/Dialog-Anbindung über das „Projekt"-Menü
  in `menu_actions.py` (#334/#335).
- **EufyMake-Export (Plan, Epic #351):** `eufymake_export.py` — Qt-freies, strikt
  getyptes Export-**Datenmodell** (#352): `build_export_plan(project)` bildet die
  Ebenenrollen deterministisch auf `ExportAsset`s in einem `ExportPlan` ab –
  `COLOR_MOTIF` ergibt das **erforderliche** RGBA-Farbmotiv (explizite Rolle oder
  COLOR-Komposit-Fallback, sonst `MissingColorMotifError`), `HEIGHT_MAP`/`GLOSS_MASK`
  je ein **optionales** Graustufen-Asset (Gloss `experimental`). Dateinamen
  (`color_motif.png`/`height_map.png`/`gloss_mask.png`), Profilkennung
  (`EXPORT_PROFILE`/`EXPORT_PROFILE_VERSION`) und Defaults sind **BgRemover-
  Konventionen**, keine offizielle EufyMake-Spezifikation. Höhensemantik
  **hell = hoch** ist im Typvertrag (`HeightSemantics`) fixiert; offene Bittiefen-/
  Gloss-Fragen und der Verzicht auf natives `.empf` sind über `OpenQuestion`
  explizit markiert. Ziel-Bittiefe/physische Größe/DPI werden reproduzierbar aus
  `META_BIT_DEPTH`/`META_PHYSICAL_SIZE_MM` plus Defaults abgeleitet; ungültige
  Werte werfen strukturierte `EufyMakeExportError`-Subtypen. `can_render_color_motif`
  ist die geteilte Farbmotiv-Regel für Plan und Prüfung. Entscheidung/Quellenlage:
  ADR [`docs/history/ADR-2026-eufymake-exportpaket.md`](docs/history/ADR-2026-eufymake-exportpaket.md).
  `eufymake_validate.py` — Qt-freie **Konsistenzprüfung** (#354):
  `validate_export(project, ...)` sammelt **alle** strukturierten Befunde
  (`ExportFinding`: stabiler `ExportCheckCode`, `error`/`warning`, Rolle, i18n-Key,
  Platzhalter) deterministisch sortiert. Harte Fehler (fehlendes Farbmotiv, fehlende
  ausgewählte Rolle, Größen-Mismatch, ungültige Zielparameter) blockieren;
  Warnungen (leere/konstante Height-/Gloss-Daten, 16-Bit unbestätigt,
  8-Bit-Ziel mit echten 16-Bit-Höhen = Präzisionsverlust (#590), Gloss=Ink-Mode-
  Hilfsasset, physische Größe ohne Herstellervertrag) erlauben den Export erst nach
  Bestätigung; die Height-Prüfungen arbeiten auf der kanonischen Payload. `format_finding` liefert die de/en-Meldung (literale `tr`-Keys
  `eufymake.export.*`). Das Befund-Fundament (`Severity`, `severity_rank`,
  `has_blocking_errors`, `split_findings`) liegt seit #379 geteilt in
  `export_checks.py` und wird hier re-exportiert (Rückwärtskompatibilität).
- **Allgemeine Pre-Export-Prüfung:** `export_checks.py` — Qt-freie, strikt getypte,
  geteilte Basis (#379): generischer `Finding`/`CheckCode`/`Severity`-Vertrag mit
  deterministischer Sortierung und `format_finding` (literale `tr`-Keys
  `export.checks.*`). Einzeln testbare, formatunabhängige Prüfungen `check_dimensions`
  (px>0, Megapixel-Limit), `check_resolution` (DPI-Plausibilität aus #376),
  `check_color_space` (erwartet RGBA), `check_transparency` (vollständig transparent /
  unerwartetes Teil-Alpha), `check_print_area` (Motiv > Zielmedium) plus der
  Orchestrator `check_export(project, ...)` (inkl. `OUTPUT_EMPTY` für leere Projekte).
  `eufymake_validate` baut darauf auf, ohne seine produktspezifischen Codes zu ändern. `eufymake_writer.py` — Qt-freies **Rendern + atomares
  Schreiben** (#353): `render_export` erzeugt die Pixel (Farbmotiv = Komposit/RGBA
  alpha-erhaltend, Height graustufig hell=hoch als `L`/`I;16`, Gloss graustufig) in
  Zielgröße plus `manifest.json`; `write_export` validiert (Fehler→`ExportValidationError`,
  Warnungen→`ExportConfirmationRequired` ohne `confirm_warnings`), rendert in ein
  Temp-Verzeichnis und veröffentlicht via **einem** `os.replace` (vorhandenes Ziel
  bleibt bei Fehlern unversehrt, Temp wird aufgeräumt; `overwrite` steuert
  Kollisionen). Kein natives `.empf`. UI/Settings (#355): `eufymake_export_dialog.py`
  (`EufyMakeExportDialog`) bietet Options-Gating (Height/Gloss nur bei kompatibler
  Projektlage, Bittiefe 8/16), abgeleitete Zielinfos und eine **Live-Befundanzeige**
  (Fehler sperren, Warnungen brauchen Bestätigung); das MainWindow verdrahtet die
  Menüaktion „Assets für EufyMake Studio exportieren…" (`Strg+Alt+E`), atomares
  Schreiben mit Überschreib-Nachfrage, Erfolgsdialog mit nächsten Studio-Schritten
  und merkt Zielordner/Optionen in den QSettings (Schema v2). `build_export_plan`/
  `write_export`/`validate_export` nehmen `optional_roles`/`bit_depth` als UI-Auswahl
  ohne Projekt-Mutation entgegen.
- **Hintergrund-Entfernung:** `workers.py` / `worker_controller.py`; die nicht
  unterbrechbare rembg/ONNX-Inferenz läuft in einem eigenen, per `spawn`
  gestarteten Prozess (`ai_process.py`), den der KI-Worker nur pollt – Abbruch
  und Schließen beenden ihn hart, ohne `QThread.terminate()` (#270). `rembg` ist
  optionales `ai`-Extra und wird erst im Kindprozess lazy importiert.
- **App-Update & KI-Modell-Status (Epic #563, abgeschlossen):** `app_update.py` —
  Qt-freie `check_for_update(current_version)` fragt
  `https://api.github.com/repos/NikolayDA/picture_helper/releases/latest`
  über `urllib.request` ab (kurzer Timeout, keine Pflichtabhängigkeit) und
  liefert ein strukturiertes `UpdateCheckResult`
  (`UP_TO_DATE`/`UPDATE_AVAILABLE`/`CHECK_FAILED`) – jeder Netzwerk-/
  Parsing-Fehler wird als `CHECK_FAILED` zurückgegeben, nie als Exception
  (#564). `ai_model_status.py` — Qt-freie `get_model_status()` erkennt den
  rembg-Cache-Zustand (`U2NET_HOME`/`XDG_DATA_HOME`/`~/.u2net`, Standardmodell
  `u2net.onnx`) rein über Pfad-/Dateigrößenprüfung, ohne `rembg` zu
  importieren (#568). UI-Anbindung (#565/#569): Extras-Menü „Nach Updates
  suchen…" startet `UpdateCheckWorker` (`workers.py`) nicht-blockierend über
  `WorkerController.start_update_check` (Re-Entrancy-Schutz analog Warmup,
  in `shutdown_all` mitverdrahtet) und zeigt je nach `UpdateStatus` einen
  passenden `QMessageBox`-Dialog (`MainWindow._on_update_check_result`;
  „Release-Seite öffnen" via `QDesktopServices.openUrl`, `CHECK_FAILED` ohne
  technischen Stacktrace). Optionaler automatischer Start-Check (#566):
  Checkbox „Beim Start automatisch nach Updates suchen" in `settings_dialog.py`
  (`settings_schema.AUTO_UPDATE_CHECK_KEY`, additiv, Default **aus**); bei
  Aktivierung läuft `MainWindow._start_automatic_update_check` still im
  Hintergrund – nur `UPDATE_AVAILABLE` zeigt einen dezenten, klickbaren
  Statusleisten-Button (`_update_hint_btn`), der über das gecachte Ergebnis
  (`_update_available_result`) denselben Dialog wie der manuelle Check öffnet,
  ohne erneuten Netzwerkzugriff; `CHECK_FAILED` bleibt beim Start komplett
  still. „KI-Modell verwalten…" ist **immer aktiv** (#575: Qt zeigt Tooltips
  in Menüs nicht an – ein still deaktivierter Eintrag wirkte wie „Klick tut
  nichts") und öffnet `ai_model_dialog.py` (`AiModelDialog`): zeigt den Status
  aus `get_model_status()` (bei `REMBG_UNAVAILABLE` inkl. der aktiven
  Python-Umgebung `sys.executable`, um venv-/Interpreter-Mismatches sichtbar
  zu machen) und meldet Download-/Cancel-Klicks über die Signale
  `download_requested`/`cancel_requested`. Die echte Verdrahtung
  (#570) läuft über `WorkerController.start_warmup`, das jetzt mehrere
  Beobachter unterstützt: läuft bereits ein Warmup (Start-Warmup oder ein
  vorheriger Dialog-Download), hängen sich weitere `start_warmup`-Aufrufer an
  denselben `RembgWarmupWorker` an (`worker_controller.warmup_worker`), statt
  einen zweiten Prozess zu starten – Statusleiste und Dialog werden dadurch
  nie widersprüchliche Zustände zeigen. `RembgWarmupWorker` unterstützt
  kooperativen Abbruch (`cancel()`/`should_cancel`, analog `AIWorker`) mit
  drei getrennten Signalen (`finished` nur Erfolg, `error` nur Fehler,
  `cancelled` nur Abbruch, `done` immer als Thread-Lifecycle-Signal);
  `WorkerController.cancel_warmup()` bricht sauber ab, ohne den Abbruch
  fälschlich als Erfolg oder Fehler zu melden. `MainWindow._last_warmup_error`
  merkt sich die technische Meldung eines fehlgeschlagenen automatischen
  Start-Warmups (#575): landet der Fehler (z. B. `ModuleNotFoundError` bei
  venv-/Interpreter-Mismatch des Inferenz-Kindprozesses oder ein
  Verbindungsabbruch) sonst nur im Log, zeigt `AiModelDialog` sie beim
  nächsten Öffnen sofort an (`download_failed`), statt den neutralen
  „Nicht heruntergeladen"-Status ohne jeden Hinweis zu zeigen. Ergänzend
  öffnet der ebenfalls immer aktive Extras-Eintrag „KI-Hintergrundentfernung
  installieren…" den `ai_install_dialog.py` (`AiInstallDialog`, #578): zeigt
  den plattformabhängigen Terminal-Befehl zum Nachrüsten des rembg-Backends
  (Linux: Projekt-venv-Rezept, macOS: Verweis auf das App-Bundle-Skript aus
  `INSTALL_MAC.md`) inkl. Kopieren-Button und warnt, wenn der laufende
  Python älter als das rembg-/onnxruntime-Minimum (3.11+) ist; er
  installiert bewusst **nicht** selbst per Subprocess (PEP 668, frisch
  installierte Pakete wären erst nach Neustart sichtbar).
- **UI-Bausteine:** `main_toolbar.py`, `right_panel.py` + `right_panel_tabs.py`
  (zentraler Builder + je Tab eine Tab-Klasse, liefert `(Widget, dict)`-DTO),
  `layer_panel.py` (Ebenen-Tab, getrieben vom `ImageCanvas.layersChanged`-Signal,
  #334), `height_map_panel.py` (Höhen-Tab #349: Beschaffen/Bearbeiten/Optimieren,
  ebenfalls `layersChanged`-getrieben; Bearbeiten/Optimieren nur im HEIGHT-Kontext
  aktiv, Optimierung mit Live-Vorschau über `preview_height_op`/`apply_height_op`),
  `settings_dialog.py`, `menu_actions.py` (inkl. „Projekt"-Menü: Neu/Öffnen/
  Speichern für `.bgrproj`), `crop_bar.py`, `history_popup.py`,
  `theme.py`, `icons*.py`.
- **Geführter Workflow & Redesign (Epics #413/#418/#424/#455/#463):** Das
  MainWindow führt durch **sechs Schritte** (`WorkflowStep` in `stepper.py`:
  OPEN/CUTOUT/ADJUST/SHAPE/RELIEF/EXPORT). `stepper.py` (`Stepper`) ist die
  zustandslose Schrittleiste – Klick sendet `stepSelected`, das MainWindow
  entscheidet über Navigation/Gating (`set_current`/`set_locked`, ohne Bild nur
  Schritt 1); `_apply_toolbar_for_step` schaltet die kontextuellen Werkzeuge.
  `zoom_control.py` (`ZoomControl`) ist die schwebende Glas-Zoom-Pille unten
  rechts (−/Prozent/+/Lock, #464); die Zoom-Logik (Klemmen, Schrittweite, Lock)
  liegt in `CanvasViewport` (`step_zoom`/`set_zoom_locked`, Grenzen
  `_ZOOM_CTRL_MIN_PCT`/`_MAX_PCT` in `constants.py`) – reiner UI-State, keine
  Undo-/Redo-Einträge. Das Design-System/Theming liegt in `theme.py`
  (palettengetriebene `*_style`-Builder, u. a. `card_style`/`stepper_style`/
  `zoom_pill_style`, Tokens `ACCENT`/`CARD_STYLE`, hell/dunkel). Referenz-Spec:
  [`docs/REDESIGN_SPEC.md`](docs/REDESIGN_SPEC.md), Prototyp unter `design/`.
- **Maßeinheiten/Geometrie:** `units.py` — Qt-freie, strikt getypte px↔mm↔DPI-Mathematik
  (#376): leitet aus je zwei bekannten Größen die dritte deterministisch ab
  (`MM_PER_INCH = 25.4`), validiert Eingaben und meldet ungültige Werte als strukturierte
  `UnitsError`-Subtypen statt stiller Korrektur. Einzige Quelle der Geometrie für
  `eufymake_export` (`_derive_target` zieht physische Größe/DPI über die
  Projektmodell-Getter `project.physical_size_mm`/`project.dpi`, `MM_PER_INCH` wird
  re-exportiert) und für die validierten mm/DPI-Setter/Getter in `Project` (physische Größe ist kanonisch
  in `META_PHYSICAL_SIZE_MM`, DPI daraus + Pixelgröße abgeleitet – kein Drift, round-trippt
  im `.bgrproj`).
- **Infrastruktur:** `constants.py` + `logging_config.py` (Logger/Log-Pfad),
  `qt_plugins.py` (Qt-Pluginpfade), `settings_schema.py` (QSettings-Versionierung),
  `status_messages.py` (zentrale Meldungsstrings), `recent_files.py`
  („Zuletzt geöffnet"-Persistenz für Bilder **und** `.bgrproj`-Projekte,
  Dispatch nach Endung im MainWindow, #335).
- **i18n:** `i18n.py` — Runtime-Sprachen **de/en** umschaltbar; Doku-Übersetzungen
  (en/es/fr/uk/zh) unter `docs/i18n/`.

## Konventionen

- **Kommentare & Docstrings auf Deutsch** (Code-Identifier englisch). Den
  bestehenden, bewusst kompakten Stil treffen.
- **ruff:** line-length 100, Regeln `E,F,W,I,B,UP,SIM`, `E501` ignoriert, Ziel
  py310. In `bgremover/*` ist `E702` erlaubt (kompakter Stil), in
  `tests/conftest.py` `E402`.
- **mypy:** Die Qt-armen Logikmodule sind streng getypt (`disallow_untyped_defs`
  + `check_untyped_defs`): `ai_model_status`, `ai_process`, `app_update`,
  `image_ops`, `image_utils`, `color_ops`,
  `eufymake_export/_validate/_writer`, `export_checks`, `gloss_preview`,
  `relief_preview`, `height_map`, `height_ops`, `preview_mode`, `crop`,
  `project_model/_history/_schema/_io`, `recent_files`, `units` und
  `canvas_selection/_lasso/_transform/_viewport`. Die zustandsbehafteten
  Qt-Module `canvas`, `main_window`, `worker_controller` laufen mit
  `check_untyped_defs` (inhaltliche Prüfung der Callbacks, aber kein
  Annotationszwang); die übrigen UI-Module bleiben bewusst laxer.
- **Tests:** Marker `ui` (nightly, voll) vs. `ui_smoke` (läuft in CI mit).
  Default-`addopts`: `-m 'not ui or ui_smoke'`. Viele Doku-Governance-Tests
  (Markdown-Links, i18n-Parität, CHANGELOG, Lizenzen) — Docs als Code behandeln.
- **Befunde** werden in `RECOMMENDATIONS.md` mit IDs geführt (`N#`/`O#`);
  Historie unter `docs/history/`.

## CI-Automatisierung

- `.github/workflows/claude.yml` — interaktiver Claude-Agent, reagiert auf
  `@claude`-Erwähnungen in Issues/PR-Kommentaren; `claude-code-review.yml` —
  automatisches Claude-Review neuer PRs (#555).
- `.github/agents/` — Agent-Konfigurationen (Code Review, Bug Fix,
  Documentation, Test, Performance; #547/#548), Details in
  [`.github/agents/README.md`](.github/agents/README.md).
- `benchmark.yml` trägt seine Baseline seit #546 als Workflow-Artefakt statt
  per Push nach `main`.

## Wichtig: Drift-Disziplin (Befund N6)

Die Qt-apt-Paketliste muss in **sechs** Dateien identisch bleiben:
`.github/workflows/ci.yml`, `pr-ci.yml`, `ui-nightly.yml`, `benchmark.yml`,
`coverage.yml` und `.claude/hooks/session-start.sh`.
`tests/test_ci_qt_packages.py` erzwingt das — beim Ändern einer Liste alle sechs
anpassen, sonst schlägt der Test fehl (und `import PyQt6` bricht andernorts mit
`libGL.so.1: cannot open shared object file`).

## Web-/Remote-Umgebung

Der `SessionStart`-Hook (`.claude/hooks/session-start.sh`) installiert in
Web-Sessions die Qt-Systembibliotheken + `.[test]` und setzt
`QT_QPA_PLATFORM=offscreen`. Er läuft nur, wenn `CLAUDE_CODE_REMOTE=true`; lokal
richtest du deine venv selbst ein (siehe `INSTALL_MAC.md` / `INSTALL_LINUX.md`).
