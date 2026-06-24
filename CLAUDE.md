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
`tests/conftest.py` (per `setdefault`) erledigen das selbst.

## Architektur

Ein Paket, `bgremover/`:

- **Einstieg:** `app.py` (`main()`), `__main__.py` → `python -m bgremover`;
  `main_window.py` verdrahtet die UI.
- **Canvas/Bearbeitung:** `canvas.py` + `canvas_*.py` (History, Selection, Lasso,
  Transform, Viewport, Crop), `crop.py`, `image_ops.py`, `image_utils.py`;
  `image_loading.py` ist der gemeinsame Lade-Helfer für Canvas und Worker. Der
  Canvas hält ein `Project` (#330) und rendert/speichert das **Komposit**;
  Werkzeuge wirken auf die **aktive Ebene** (`self._pil`/`_arr` sind deren Cache),
  größenändernde Geometrie (Drehen/Zuschnitt via `apply_geometry`) auf alle Ebenen;
  Undo/Redo läuft über `ProjectHistory`. Einzel-COLOR-Ebene = bitgenaue Parität
  zum bisherigen Einzelbild-Editor (#332). Die Anzeige ist seit #387 explizit über
  `PreviewMode` gesteuert und unabhängig von der aktiven Editierebene; der getrennte
  Exportpfad schreibt weiterhin ausschließlich das COLOR-Komposit (#363).
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
  Normalisierung beliebiger Werte auf den Höhenbereich und Canvas-Größen-Validierung;
  als `uint16` geführt und damit 16-Bit-erweiterbar (`max_value`). `generate_from_image`
  erzeugt deterministisch eine Höhenkarte (Kanalgewichtung/Luminanz → Tonwert-Kennlinie
  → Gamma → Invertieren) (#346). Der Canvas verdrahtet das (`generate_height_map` aus
  aktiver COLOR-Ebene/Komposit, `import_height_map` via `open_validated_image` mit
  Skalierung auf Canvas-Größe) als neue, aktive HEIGHT-Ebene mit Rolle `HEIGHT_MAP`,
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
  Ein Vorschau-Tab und das exklusive Ansicht-Untermenü halten sich signalbasiert
  synchron; der UI-Hinweis macht den unveränderten Bildexport ausdrücklich sichtbar
  (#388).
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
  inkompatibler Altzustände normalisiert verlustfrei (siehe Persistenz). `project_history.py` (`ProjectHistory`) ist die
  ebenenbewusste, Qt-freie Undo/Redo-Historie darauf: leichte Struktur-Snapshots
  + deduplizierter Pixelpool (geteiltes Undo-/Redo-Budget; unveränderte Ebenen
  zählen nur einmal) – noch nicht im Canvas verdrahtet (#331, folgt #332).
- **Projekt-Persistenz:** `project_io.py` + `project_schema.py` — Qt-freier
  `.bgrproj`-Round-Trip (ZIP: `manifest.json` + eine RGBA-PNG je Ebene), atomar
  geschrieben (`mkstemp`+`os.replace`) und defensiv geladen (Größen-/Megapixel-
  Limits, Zip-Slip-Abwehr, klare i18n-Meldungen); versioniertes Schema mit
  Migrationshaken (Zukunfts-Version bleibt unangetastet) (#333). Beim Laden wird
  ein historisch inkompatibler Rollen-Zustand (z. B. `HEIGHT_MAP` auf einer
  COLOR-Ebene) deterministisch normalisiert: nur die unzulässige Rolle wird
  entfernt (Kind/Name/Pixel/Reihenfolge/Metadaten bleiben wertgleich), und
  `load_project(..., warnings=...)` reicht eine übersetzte Warnung an die UI
  (Statusleiste) durch (#364). Noch ohne
  Menü-/Dialog-Anbindung (folgt #334/#335).
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
  Warnungen (leere/konstante Height-/Gloss-Daten, 16-Bit unbestätigt, Gloss=Ink-Mode-
  Hilfsasset, physische Größe ohne Herstellervertrag) erlauben den Export erst nach
  Bestätigung. `format_finding` liefert die de/en-Meldung (literale `tr`-Keys
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
- **UI-Bausteine:** `main_toolbar.py`, `right_panel*.py`, `layer_panel.py`
  (Ebenen-Tab, getrieben vom `ImageCanvas.layersChanged`-Signal, #334),
  `height_map_panel.py` (Höhen-Tab #349: Beschaffen/Bearbeiten/Optimieren,
  ebenfalls `layersChanged`-getrieben; Bearbeiten/Optimieren nur im HEIGHT-Kontext
  aktiv, Optimierung mit Live-Vorschau über `preview_height_op`/`apply_height_op`),
  `settings_dialog.py`, `menu_actions.py` (inkl. „Projekt"-Menü: Neu/Öffnen/
  Speichern für `.bgrproj`), `crop_bar.py`, `history_popup.py`, `widgets.py`,
  `theme.py`, `icons*.py`.
- **Maßeinheiten/Geometrie:** `units.py` — Qt-freie, strikt getypte px↔mm↔DPI-Mathematik
  (#376): leitet aus je zwei bekannten Größen die dritte deterministisch ab
  (`MM_PER_INCH = 25.4`), validiert Eingaben und meldet ungültige Werte als strukturierte
  `UnitsError`-Subtypen statt stiller Korrektur. Einzige Quelle der Geometrie für
  `eufymake_export` (`_derive_physical_size`/`_derive_dpi`/`MM_PER_INCH` konsumieren sie)
  und für die validierten mm/DPI-Setter/Getter in `Project` (physische Größe ist kanonisch
  in `META_PHYSICAL_SIZE_MM`, DPI daraus + Pixelgröße abgeleitet – kein Drift, round-trippt
  im `.bgrproj`).
- **Infrastruktur:** `constants.py` + `logging_config.py` (Logger/Log-Pfad),
  `qt_plugins.py` (Qt-Pluginpfade), `settings_schema.py` (QSettings-Versionierung),
  `status_messages.py` (zentrale Meldungsstrings), `recent_files.py`
  („Zuletzt geöffnet"-Persistenz für Bilder **und** `.bgrproj`-Projekte,
  Dispatch nach Endung im MainWindow, #335).
- **i18n:** `i18n.py` — Runtime-Sprachen **de/en** umschaltbar; Doku-Übersetzungen
  unter `docs/i18n/`.

## Konventionen

- **Kommentare & Docstrings auf Deutsch** (Code-Identifier englisch). Den
  bestehenden, bewusst kompakten Stil treffen.
- **ruff:** line-length 100, Regeln `E,F,W,I,B,UP,SIM`, `E501` ignoriert, Ziel
  py310. In `bgremover/*` ist `E702` erlaubt (kompakter Stil), in
  `tests/conftest.py` `E402`.
- **mypy:** Qt-arme Logikmodule (`image_ops`, `image_utils`, `crop`,
  `project_model`, `recent_files`,
  `canvas_history/_selection/_lasso/_transform/_viewport`) sind streng getypt
  (`disallow_untyped_defs`); Qt-lastige Module bewusst laxer.
- **Tests:** Marker `ui` (nightly, voll) vs. `ui_smoke` (läuft in CI mit).
  Default-`addopts`: `-m 'not ui or ui_smoke'`. Viele Doku-Governance-Tests
  (Markdown-Links, i18n-Parität, CHANGELOG, Lizenzen) — Docs als Code behandeln.
- **Befunde** werden in `RECOMMENDATIONS.md` mit IDs geführt (`N#`/`O#`);
  Historie unter `docs/history/`.

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
