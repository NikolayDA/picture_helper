**Deutsch** · [English](docs/i18n/en/CHANGELOG.md) · [Español](docs/i18n/es/CHANGELOG.md) · [Français](docs/i18n/fr/CHANGELOG.md) · [Українська](docs/i18n/uk/CHANGELOG.md) · [简体中文](docs/i18n/zh/CHANGELOG.md)

# Changelog

Alle nennenswerten Änderungen an BgRemover werden in dieser Datei
dokumentiert. Das Format orientiert sich an
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/); das Projekt
folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

## [2.5.0] – 2026-07-11

### Hinzugefügt

- **Laufzeit-UI in sechs Sprachen (Redesign-i18n, #430).** Die komplette
  Runtime-Stringtabelle ist jetzt zusätzlich auf Spanisch, Französisch,
  Ukrainisch und vereinfachtem Chinesisch gepflegt – einschließlich der neuen
  Workflow-Strings des Redesigns (Schritt-Labels, Schritt-Titel und
  -Beschreibungen, Karten-Titel, Navigation). Die Sprachen erscheinen
  automatisch in der Sprachauswahl des Einstellungsdialogs; Deutsch bleibt
  garantierter Fallback, und die i18n-Paritätstests (Key- und
  Platzhalter-Gleichheit, UI-Smoke je Locale) decken alle sechs Sprachen ab
  (Teil von Epic #425).
- **Helles Design & Design-Tokens (UI-Redesign, Epic #424).** Ein zentrales,
  token-basiertes Theming (`Palette` mit hellem und dunklem Schema) färbt die
  gesamte Oberfläche über eine `QPalette` und ein anwendungsweites Stylesheet.
  Über „Ansicht → Helles Design“ lässt sich zur Laufzeit zwischen Hell und Dunkel
  umschalten; die Wahl wird in den Einstellungen gemerkt und beim Start angewendet.
  Barrierefreiheit: Jedes interaktive Element zeigt einen sichtbaren Fokusring
  (auch nach dem Theme-Wechsel), die Schrittleiste ist per Tastatur bedienbar
  (Tab + Enter/Leertaste), alle Bedienziele halten Mindest-Trefferflächen ein,
  und eine WCAG-AA-Kontrastmatrix sichert beide Farbschemata dauerhaft ab
  (#427–#429, #441).
- **Geführter Workflow mit Karten-Inspector (UI-Redesign, Epics #413/#418).** Die
  rechte Spalte führt jetzt in sechs klaren Schritten durch die Bearbeitung
  (Öffnen · Freistellen · Anpassen · Form & Maße · Relief & Ebenen · Export): eine
  Schrittleiste oben, ein Inspector mit Schritt-Kopf und fixer Zurück/Weiter-
  Navigation sowie eine kontextuelle Werkzeugleiste (Auswahlwerkzeuge nur im
  Freistellen-Schritt). Die Schritte 2–6 sind gesperrt, bis ein Bild geladen ist;
  danach wird automatisch zum Freistellen gewechselt. Die bestehende Aktions-
  Verdrahtung (`RightPanelActions`/`LayerPanelActions`/`HeightMapActions`) bleibt
  unverändert (#419–#422, #415–#417).

- **Nutzerwählbare kombinierte 2D-Vorschau (Phase-1-Abschluss).** Der Canvas bietet
  jetzt explizite, von der aktiven Ebene unabhängige Modi für Farbe, Relief über
  Farbe, Höhe (Graustufe), Gloss und die kombinierte Ansicht. Ein auf genau ein Bild
  begrenzter Cache invalidiert über Content-Revision, Modus und Anzeigeparameter;
  Ansicht-Menü und neuer Vorschau-Tab bleiben synchron, Relief-Stärke und Gloss-
  Sichtbarkeit wirken live. Ein klarer Hinweis und eine Modus×Layer-Testmatrix
  sichern den #363-Vertrag: „Bild speichern“ exportiert weiterhin ausschließlich
  das COLOR-Komposit (#387, #388; schließt Epic #384).
- **Qt-freie Relief- und Gloss-Renderer für die kombinierte 2D-Vorschau.** Die
  neuen, strikt getypten Module `bgremover/relief_preview.py` und
  `bgremover/gloss_preview.py` erzeugen deterministisches, richtungsabhängiges
  Hillshade aus `HeightField` (8-/16-Bit-äquivalent) sowie einen sichtbaren
  Gloss-Sheen. Beide legen ihren Effekt größenvalidiert über ein RGBA-Farbmotiv,
  erhalten dessen Alphakanal bitgenau und bieten echte neutrale No-ops; reine
  Pixel-/Grenzfalltests sichern Lichtrichtung, Deckung, Stärke und Alpha (#385,
  #386).
- **Pre-Export-Prüfung beim normalen Speichern.** „Speichern"/„Speichern unter…"
  führt jetzt vor dem Schreiben die allgemeine Prüfung (#379) auf dem Projekt aus
  und zeigt die Befunde analog zum EufyMake-Flow: **Fehler blockieren** das
  Speichern mit klarer Meldung (kein Schreibaufruf), **Warnungen** erfordern eine
  bewusste Bestätigung. Ein Abbruch ist seiteneffektfrei (kein Schreiben, keine
  Temporärdateien). Teiltransparenz wird bewusst **nicht** beanstandet – sie ist
  das normale Ergebnis eines Freistellungswerkzeugs. Alle Strings de/en; die
  Befund-Darstellung nutzt dieselbe `format_finding`-Render-Logik wie die
  EufyMake-Anzeige (#380). Damit ist Epic #375 (maßgenaue Ausgabe + Exportprüfung)
  abgeschlossen.
- **mm/DPI-Modus im „Größe ändern…"-Dialog + Druckflächenprüfung.** Der
  Resize-Dialog kennt jetzt zwei Maßeinheiten: Pixel (wie bisher) und
  **Millimeter + DPI**. Im mm-Modus werden Breite/Höhe in mm und die DPI bedient,
  die resultierende **Pixelgröße** live über die geteilte Geometrie (#376) angezeigt
  und das Seitenverhältnis optional gekoppelt. Eine **Druckflächenprüfung** vergleicht
  das Motiv gegen ein wählbares Zielmedium (A3/A4/A5/Letter) und warnt verständlich bei
  Überschreitung. Beim Anwenden wird die physische Zielgröße (mm) über die
  `project_model`-Setter im Projekt verankert (kanonisch; die DPI folgt aus mm +
  Pixelgröße) und übersteht den `.bgrproj`-Round-Trip; das Resampling bleibt rein
  pixelbasiert (`Project.resize`). Alle Strings de/en (#377).
- **Allgemeine, Qt-freie Pre-Export-Prüfung (geteiltes Framework).** Neues, strikt
  getyptes Modul `bgremover/export_checks.py` hebt das Befund-Framework aus
  `eufymake_validate` (#354) auf eine geteilte Basis: ein generischer
  `Finding`/`CheckCode`/`Severity`-Vertrag mit stabilen Codes, i18n-Keys
  (`export.checks.*`, de/en) und deterministischer Sortierung. Implementiert sind
  formatunabhängige Prüfungen für Abmessungen (px > 0, Megapixel-Limit),
  Auflösungs-Plausibilität (DPI aus #376), Farbraum (erwartet RGBA), Transparenz
  (vollständig transparent / unerwartetes Teil-Alpha), leere Ausgabe und die
  Druckflächen-/Randprüfung (physische Größe gegen Zielmedium). `eufymake_validate`
  baut nun auf der geteilten Basis auf (re-exportiert `Severity`/`has_blocking_errors`/
  `split_findings`); EufyMake-spezifische Codes bleiben dort und alle bisherigen
  EufyMake-Tests laufen unverändert grün (#379).
- **DPI/Auflösung in Ausgaben verankern.** Beim Raster-Speichern bettet
  `image_ops.save_image_file` jetzt optional die Projekt-DPI (#376) als reine
  Metadaten ein – PNG (`pHYs`), JPEG (JFIF-Dichte) und TIFF
  (`Resolution`/`ResolutionUnit`); WebP trägt keine DPI. Der Canvas-Speicherpfad
  reicht die aus physischer Größe + Pixelgröße abgeleitete Auflösung durch; ohne
  gesetzte Projekt-DPI bleibt das Verhalten unverändert und die Pixel/Alpha werden
  in keinem Fall berührt (bitgenauer Single-COLOR-Export bleibt erhalten). Der
  EufyMake-Export speist seinen `ExportTarget` nun aus den Modell-mm/DPI-Gettern
  statt aus einer export-lokalen Ableitung (#378).
- **mm/DPI als Projekt-Eigenschaft + geteilte Qt-freie Geometrie.** Neues,
  strikt getyptes Modul `bgremover/units.py` bündelt die gesamte px↔mm↔DPI-Mathematik
  an einer Stelle: aus je zwei bekannten Größen leitet es die dritte deterministisch
  ab (`MM_PER_INCH = 25,4`), validiert Eingaben und meldet ungültige Werte (≤ 0,
  nicht-numerisch, falsche Form) als strukturierte `UnitsError`-Fehler statt sie still
  zu korrigieren. `Project` erhält validierte Setter/Getter für die physische Zielgröße
  (mm) und die Auflösung (DPI) – die physische Größe ist die kanonische Quelle, die DPI
  ergibt sich daraus und der Pixelgröße (kein Drift) und übersteht den
  `.bgrproj`-Round-Trip wertgleich. Der EufyMake-Export nutzt fortan dieselbe Geometrie
  (`_derive_physical_size`/`_derive_dpi`/`MM_PER_INCH`) ohne Verhaltensänderung (#376).
- **EufyMake-Studio-Import: Menü, Dialog, Prüfungsanzeige & Settings.** Neue
  Menüaktion „Assets für EufyMake Studio exportieren…" (Projekt-Menü, Strg+Alt+E)
  öffnet einen Qt-Dialog (`eufymake_export_dialog.py`): Farbmotiv ist Pflicht,
  Höhenkarte/Gloss-Maske nur bei kompatibler Projektlage auswählbar (Gloss sichtbar
  als experimentell), Bittiefe 8/16 (16 als unbestätigt markiert), abgeleitete
  Ziel-/physische Größe sowie eine **Live-Befundanzeige** aus der Prüfung (#354):
  Fehler blockieren, Warnungen erfordern eine bewusste Bestätigung. Geschrieben wird
  atomar über `write_export`; Abbruch/Fehler verändern weder Projekt noch Ziel, die
  Überschreib-Nachfrage schützt vorhandene Ordner. Der Erfolgsdialog nennt Zielpfad
  und nächste Studio-Schritte (Import, Positionierung, Ink-Mode/Layerzuweisung,
  Speichern als `.empf`). Zielordner und allgemeine Optionen werden in den
  versionierten QSettings gemerkt (Schema v2, additive Keys mit Migration).
  `build_export_plan`/`write_export` erhielten `optional_roles`/`bit_depth` für die
  UI-Auswahl. Alle Strings de/en; die UI spricht konsequent von Import-Assets, nie
  von einem fertigen `.empf`-Projekt (#355).
- **EufyMake-Export: Rendern, atomares Schreiben & Konsistenzprüfung (Qt-frei).**
  Zwei neue strikt getypte Module bauen auf dem Plan aus #352 auf:
  `bgremover/eufymake_validate.py` (`validate_export`) sammelt deterministisch
  sortierte, strukturierte Befunde (stabiler Code, `error`/`warning`, Rolle,
  i18n-Key); harte Fehler (fehlendes Farbmotiv, fehlende ausgewählte Rolle,
  Größen-Mismatch, ungültige Zielparameter) blockieren, Warnungen (leere/konstante
  Height-/Gloss-Daten, 16 Bit unbestätigt, Gloss als Ink-Mode-Hilfsasset, physische
  Größe ohne Herstellervertrag) erlauben den Export erst nach Bestätigung – alle
  Meldungen de/en (#354). `bgremover/eufymake_writer.py`
  (`render_export`/`write_export`) rendert Farbmotiv (= Komposit, RGBA
  alpha-erhaltend), Höhenkarte (graustufig hell=hoch, 8/16 Bit) und optionale
  Gloss-Maske in Zielgröße samt `manifest.json` und schreibt sie **atomar** (Render
  in ein Temp-Verzeichnis, Veröffentlichung in einem `os.replace`-Schritt; ein
  Fehler bewahrt ein vorhandenes Ziel, Temp wird aufgeräumt; Kollisionsverhalten via
  `overwrite`). Kein natives `.empf` (#353).
- **EufyMake-Export: Datenmodell & Planung (Qt-frei).** Neues strikt getyptes
  Modul `bgremover/eufymake_export.py`: `build_export_plan(project)` bildet die
  Ebenenrollen deterministisch auf einen `ExportPlan` aus `ExportAsset`s ab –
  Farbmotiv als RGBA-PNG ist **erforderlich** (explizite `COLOR_MOTIF`-Rolle oder
  COLOR-Komposit), Höhenkarte und Gloss-Maske sind **optionale** Graustufen-PNGs
  (Gloss experimentell). Dateinamen, Profilversion und Defaults sind dokumentierte
  **BgRemover-Konventionen** (keine offizielle EufyMake-Spezifikation); die
  Höhensemantik **hell = hoch** ist im Typvertrag fixiert, offene Bittiefen-/
  Gloss-Fragen und der Verzicht auf natives `.empf` bleiben explizit markiert.
  Physische Größe, DPI und Bittiefe werden reproduzierbar aus den Projektmetadaten
  bzw. Defaults abgeleitet; ungültige Werte liefern strukturierte Fehler. Reines
  Datenmodell ohne Rendern/Schreiben/UI (folgt #353–#355) (#352).
- **EufyMake-Exportpaket-ADR.** Neue Architekturentscheidung dokumentiert die
  importorientierte Paketkonvention für #352/#351: Farbmotiv als RGBA-PNG,
  Höhenkarte als Graustufen-PNG mit hell=hoch, optionale Gloss-Maske sowie
  offene Punkte zu 16 Bit, Gloss-Semantik und nativem `.empf`-Format.
- **Feinschliff Freistellung: Kantenglättung/Feather.** Neue Qt-freie, strikt
  getypte `feather_alpha(img, radius, *, mask=None)` in `image_ops.py`: gaußsche
  Weichzeichnung **nur des Alphakanals** (RGB bitgenau erhalten; `radius = 0` =
  No-op; vollflächig deckende Ebenen bleiben randartefaktfrei). Der Canvas
  verdrahtet sie als `feather_active_edges(radius)` auf der aktiven Ebene –
  **auswahlbegrenzt** (vorhandene Auswahl) und über den bestehenden Apply-Pfad
  **undo-/redobar**. UI: Radius-Regler + Button „Kante glätten" im Hintergrund-Tab
  (nahe der Freistellung). Alle neuen Strings de/en in Parität (#361).
- **Farbkorrektur der aktiven Farbebene (Helligkeit/Kontrast/Sättigung).** Neues
  Qt-freies, strikt getyptes Modul `bgremover/color_ops.py` mit `adjust_color`
  (Pillow `ImageEnhance`, **Alphakanal exakt erhalten**, Neutralwerte =
  bitidentisches No-op) – als wiederverwendbare Tonwert-Primitive für die spätere
  geteilte Engine (Rang #6). Der Canvas bietet dafür eine generische
  **Live-Vorschau** (`preview_color_op`/`cancel_color_preview`, transient ohne
  Modelländerung; die Vorschau hat in `_refresh_image` Vorrang) und einen
  undo-/redobaren Commit (`apply_color_op`) auf der aktiven **COLOR**-Ebene (auf
  Nicht-COLOR-Ebenen wirkungslos). Neuer „Anpassen"-Tab im rechten Panel mit
  Reglern Helligkeit/Kontrast/Sättigung samt **Zurücksetzen** und **Anwenden**.
  Alle neuen Strings de/en in Parität (#360).
- **Größe ändern / auf Zielgröße skalieren (Resampling).** Neue Qt-freie, strikt
  getypte Bildoperationen `resize_image`/`resized_size` in `image_ops.py` (No-op
  bei gleicher Größe; Seitenverhältnis-/Megapixel-Gate-Helfer) sowie
  `Project.resize` in `project_model.py`, die **alle Ebenen** und die
  Canvas-Größe konsistent resampelt (COLOR über das gewählte Verfahren, HEIGHT
  verlustfrei über die Höhen-Repräsentation; das Farb-Komposit bleibt
  deckungsgleich). Der Canvas verdrahtet das undo-/redobar mit Megapixel-Gate
  (klare, übersetzte Ablehnung bei Übergröße, ohne Allokation der Übergröße); ein
  neuer Dialog „Größe ändern…" (Breite/Höhe in px, **Seitenverhältnis koppeln**,
  Resample-Verfahren) ist über das Menü „Bearbeiten" (Strg+R) und den
  Transform-Tab erreichbar. Die reservierte physische Zielgröße
  (`META_PHYSICAL_SIZE_MM`) bleibt unangetastet (mm/DPI ist späteren Rängen
  vorbehalten). Alle neuen Strings de/en in Parität (#359).
- **Höhen-Repräsentation & 2D-Visualisierung (Fundament Height-Map).** Neues
  Qt-freies, strikt getyptes Modul `bgremover/height_map.py`: verlustfreie
  Konvertierung Höhe ↔ Graustufen-Array (`HeightField`, Konvention
  `R==G==B==Höhe`, `A==Deckung`), Normalisierung beliebiger Werte auf den
  Höhenbereich sowie Canvas-Größen-Validierung – intern als `uint16` geführt und
  damit 16-Bit-erweiterbar (`max_value`). Der Canvas zeigt eine **aktive
  HEIGHT-Ebene** jetzt graustufig an; das COLOR-Komposit bleibt unverändert
  (Parität) (#345, #344).
- **Höhenkarte erzeugen & importieren (ohne KI).** `bgremover/height_map.py`
  bekommt `generate_from_image`: erzeugt **deterministisch** eine Höhenkarte aus
  einem Farbbild (Kanalgewichtung/Luminanz → Tonwert-Kennlinie → Gamma →
  Invertieren). Der Canvas verdrahtet das undo-/redobar als neue, aktive
  HEIGHT-Ebene mit Rolle `HEIGHT_MAP`: `generate_height_map` aus der aktiven
  COLOR-Ebene bzw. dem Komposit und `import_height_map` lädt eine Graustufendatei
  validiert über `open_validated_image` (Format-/Datei-/Megapixel-Schutz, klare
  übersetzte Fehlermeldung) und skaliert sie auf die Canvas-Größe (#346, #344).
- **Height-Map-Editor (Aufhellen/Abdunkeln/Setzen/Invertieren).**
  `bgremover/height_map.py` bekommt auswahlbewusste, verlustfreie Höhen-
  Operationen (`adjust_height`, `set_height`, `invert_height`; geklemmt, Eingabe
  unverändert). Der Canvas verdrahtet sie an der **aktiven HEIGHT-Ebene**
  (`lighten_/darken_/set_/invert_active_height`): sie respektieren eine
  vorhandene Auswahl (sonst global), sind undo-/redobar und wirken auf
  COLOR-Ebenen bewusst nicht (keine Regression im Farb-Editing). Maximale
  Wiederverwendung der vorhandenen Pinsel-/Auswahl-/History-Pfade (#347, #344).
- **Height-Map-Optimierung (`height_ops`).** Neues Qt-freies, strikt getyptes,
  16-Bit-taugliches Modul `bgremover/height_ops.py` mit reinen, deterministischen
  Operationen auf Höhenfeldern: Tonwert (`levels`/`gamma`), Glättung
  (`gaussian_blur` separabel, `median_blur` kantenerhaltend – rein in numpy ohne
  neue Abhängigkeit), `threshold`, Stufenreduzierung (`quantize`) und
  Höhenbereich-Clamp (`clamp_range`) – dieselben Tonwert-/Graustufen-Primitive,
  die spätere Ränge teilen. Der Canvas bietet dafür eine generische **Live-
  Vorschau** (`preview_height_op`/`cancel_height_preview`, transient ohne
  Modelländerung) und einen undo-/redobaren Commit (`apply_height_op`) auf der
  aktiven HEIGHT-Ebene (#348, #344).
- **Height-Map-Arbeitsbereich nutzbar (UI) – Epic abgeschlossen.** Neuer
  „Höhe"-Tab im rechten Panel (`height_map_panel.py`): Höhenkarte aus dem Bild
  **erzeugen** oder eine Graustufe **importieren**, mit **Aufhellen/Abdunkeln/
  Setzen/Invertieren** bearbeiten und über **Tonwert/Gamma/Glättung (Gauß,
  Median)/Schwelle/Stufen/Bereich** mit Live-Vorschau **optimieren**. Bearbeiten
  und Optimieren sind **moduskontextuell** – nur aktiv, wenn die aktive Ebene
  eine HEIGHT-Ebene ist bzw. die Rolle `HEIGHT_MAP` trägt; das COLOR-Editing
  bleibt unverändert. Damit ist der komplette Ablauf (erzeugen → malen →
  optimieren → invertieren → verlustfrei im `.bgrproj` speichern/laden) per UI
  bedienbar. Alle neuen Strings über `i18n.py` (de/en in Parität); schließt das
  Height-Map-Epic ab (#349, #344).
- **Qt-freies Projekt-/Ebenen-Datenmodell.** Neues, strikt getyptes Modul
  `bgremover/project_model.py` mit `Project` und `Layer` (`LayerKind`
  Farbe/Höhe/Gloss/Generisch, projektweit eindeutige Rollen) als Fundament des
  Ebenen-Epics: geordnete Ebenen, genau eine aktive Ebene, reine Operationen
  (Hinzufügen/Entfernen/Umsortieren/Duplizieren/Umbenennen,
  Sichtbarkeit/Opazität/Sperre/Rollen) und ein Alpha-Komposit der sichtbaren
  Farb-Ebenen – ohne Qt-, Render-, Persistenz- oder History-Anbindung
  (#330, #329).
- **Ebenenbewusste, Qt-freie Undo/Redo-Historie.** Neues, strikt getyptes Modul
  `bgremover/project_history.py` (`ProjectHistory`) hebt Undo/Redo vom Einzelbild
  auf das Projektmodell: abgedeckt werden strukturelle Änderungen (Ebene anlegen/
  löschen/umsortieren/duplizieren, aktive Ebene, Sichtbarkeit/Opazität/Sperre/
  Rolle) und Pixeländerungen je Ebene. Speicherstrategie: leichte Struktur-
  Snapshots plus ein deduplizierender Pixelpool, der unveränderte Ebenen über das
  geteilte Undo-/Redo-Budget nur einmal zählt (Original und aktueller Zustand
  außerhalb des Budgets); `descriptions()`/`undo_to()`/„Original wiederherstellen"
  bleiben erhalten. Noch ohne Canvas-Verdrahtung (#331, #329; folgt #332).
- **Projektdatei-Format `.bgrproj` (verlustfreies Speichern/Laden).** Neue
  Qt-freie Module `bgremover/project_io.py` und `bgremover/project_schema.py`
  schreiben/lesen ein komplettes Mehr-Ebenen-Projekt als ZIP-Container
  (`manifest.json` mit Formatversion, Canvas-Größe, geordneter Ebenenliste inkl.
  Rollen/Metadaten + eine RGBA-PNG je Ebene). Speichern ist atomar
  (`mkstemp`+`os.replace`), Laden validiert defensiv (Dateigrößen-Limit, Megapixel
  je Ebene, Abwehr von Zip-Slip/unerwarteten Einträgen, klare übersetzte
  Fehlermeldungen). Das Schema ist versioniert mit Migrationshaken: ältere
  Versionen migrieren, neuere bleiben unangetastet (nur Warnung). Noch ohne
  Menü-/Dialog-Anbindung (#333, #329; folgt #334/#335).
- **Ebenen-Panel und Projekt-Menü.** Das rechte Panel hat einen neuen Tab
  „Ebenen": Ebenen anlegen, auswählen (aktive Editier-Ebene), ein-/ausblenden,
  Opazität ändern, hoch/runter sortieren, duplizieren, löschen, umbenennen sowie
  eine Rolle (Farbmotiv/Height Map/Gloss) zuweisen – alle Änderungen wirken im
  Canvas-Komposit (#332) und sind undo-/redobar (#331). Neues „Projekt"-Menü mit
  „Neues Projekt" (`Ctrl+N`), „Projekt öffnen…" (`Ctrl+Shift+O`), „Projekt
  speichern" (`Ctrl+Alt+S`) und „Projekt speichern unter…" (`Ctrl+Alt+Shift+S`),
  verdrahtet an das `.bgrproj`-Format (#333); `Ctrl+O`/`Ctrl+S` bleiben den
  Bild-Workflows vorbehalten. Lade-/Speicherfehler erscheinen als verständliche,
  übersetzte Meldungen. Alle neuen Strings über `i18n.py` (de/en in Parität)
  (#334, #329; Bild→Projekt-Migration folgt #335).

### Geändert

- **Bild→Projekt-Integration und „Zuletzt geöffnet" für Projekte.** „Bild
  öffnen" und Drag & Drop erzeugen jetzt ein Ein-Ebenen-Projekt (validiertes
  Laden via `image_loading` unverändert); „Zuletzt geöffnet" führt Bilder **und**
  `.bgrproj`-Projekte und öffnet jeden Typ korrekt (Unterscheidung nach Endung).
  Das zuletzt genutzte Projektverzeichnis wird gemerkt (additiver
  Settings-Schlüssel; keine Schema-Migration nötig, der Zukunfts-Version-Schutz
  ist bereits getestet). Der Einzelbild-Export schreibt weiterhin das Komposit
  (Ein-Ebenen-Projekt bitgenau wie bisher), „Original wiederherstellen" liefert
  das Dokument im Ladezustand. Schließt das Ebenen-Epic ab (#335, #329).
- **Editor arbeitet jetzt ebenenbasiert (Komposit-Rendering + aktive Ebene).**
  Der Canvas hält statt eines Einzelbilds ein `Project` (#330) und zeigt/speichert
  das **Komposit** der sichtbaren Ebenen (Reihenfolge/Sichtbarkeit/Opazität); alle
  Werkzeuge (Zauberstab/Auswahl, Pinsel/Radierer, Lasso, KI-Freistellung,
  Hintergrund ersetzen, Spiegeln, Eckenrundung) wirken auf die **aktive Ebene**,
  die Auswahlmaske bezieht sich auf sie. Größenändernde Geometrie (Drehen,
  Zuschnitt) wirkt invariantenwahrend einheitlich auf alle Ebenen. Undo/Redo und
  „Original wiederherstellen" laufen über die ebenenbewusste `ProjectHistory`
  (#331). Ein Projekt mit genau einer COLOR-Ebene verhält sich bitgenau wie bisher
  (Parität, inkl. erhaltener RGB-Werte unter transparenten Pixeln beim Speichern);
  der KI-Abbruch bleibt ohne `QThread.terminate()`-Regression (#332, #329; UI-
  Ebenen-Panel folgt #334).
- **GitHub-Release-Notizen stammen jetzt aus dem CHANGELOG.** Der
  Release-Workflow (`release-linux.yml`) leitet den Release-Body zum Tag
  `vX.Y.Z` aus dem `## [X.Y.Z]`-Abschnitt der `CHANGELOG.md` ab und übergibt ihn
  via `--notes-file` an `gh release` – auch beim Wiederverwenden eines
  bestehenden Releases (`gh release edit`), nicht nur bei der Erstanlage. Der
  fest verdrahtete „Automated build…"-Text entfällt; fehlt der passende
  Abschnitt, schlägt der Publish-Job klar fehl (kein stiller Fallback) (#311).
- **Wochen-Benchmark meldet keine Umgebungs-Artefakte mehr als Regression.**
  Jedes Ergebnis (`benchmarks/results/`) trägt jetzt einen Umgebungs-Fingerprint
  (Python-/Pillow-/NumPy-Version, Architektur, CPU-Anzahl, Runner); der Vergleich
  überspringt nicht vergleichbare Baselines (fehlender Fingerprint, abweichende
  Versionen oder Benchmark-Parameter) und bestätigt eine Auffälligkeit im selben
  Lauf über mehrere Wiederholungen (Median), bevor ein Issue entsteht
  (#277, #278, #279).

### Behoben

- **Dunkles Farbschema an den Prototyp angeglichen.** Die Hintergrundflächen
  im Dark Mode (`theme.DARK`: Inspector-Panel, Schrittleiste, Werkzeugleiste,
  Navigations-Fußzeile, Statusleiste, Bedienflächen und Karten) nutzen jetzt
  den kühlen Blaugrau-Ton des abgenommenen Prototyps
  (`design/Prototyp A - Geführter Workflow.dc.html`) statt eines neutralen
  Nah-Schwarz. `card_bg` übernimmt nun ebenfalls den Prototyp-Wert `#2e353f`;
  `docs/REDESIGN_SPEC.md` §2 dokumentiert die übernommenen Werte und die
  verbleibende bewusste Token-Abweichung (#475, #496).
- **Ränder im Dark Mode als weiche Overlays statt harter Grautöne.** `border`
  und `hairline` sind jetzt teiltransparente Weiß-Overlays wie im Prototyp
  (setzen sich je nach Untergrund unterschiedlich ab, statt auf jeder Fläche
  gleich hart zu wirken); ein neues `border_2`-Token deckt den sekundären
  Rand-Ton neutraler Sekundärbuttons ab (Zuschnitt-Format, Speicherformat
  u. a., `panel_btn_style`). Die Menüleiste teilt sich dabei den
  `toolbar`-Ton mit der Werkzeugleiste statt der Statusleiste – wie im
  Prototyp, wo Menü- und Werkzeugleiste denselben Farbwert tragen (#476).
- **Akzentblau im Dark Mode an den Prototyp angeglichen.** `accent`/`accent2`
  (und die abgeleiteten `accent_soft`/`accent_line`/`accent_shadow`-Flächen)
  sind jetzt das hellere, periwinkle-artige Blau des Prototyps statt eines
  dumpferen Tons – sichtbar am Primärbutton-Verlauf, dem „Weiter“-Button,
  aktiven Werkzeugen, dem aktiven Stepper-Kreis und dem Slider-Griff.
  `accent_text` traf bereits 1:1 den Prototyp-Wert; `accent_shadow` bleibt
  ein reiner Farbwert ohne Glow-Effekt (Qt-QSS kennt kein `box-shadow`,
  #477).
- **Slider der rechten Spalte bilden den Prototyp nach.** Die Qt-Slider nutzen
  jetzt wie `input[type=range]` im Prototyp 8 px hohe Tracks mit `accent`
  gefüllter Strecke, hellgrauer Reststrecke, weißem Track-Rahmen, weißem
  16 px Griff und dem vertikalen Abstand `9px 0 2px`; das gilt auch für den
  Opacity-Slider im Ebenen-Panel (#496).
- **Vorschau-Segmented-Control (Schritt 6) nutzt jetzt die richtige
  Prototyp-Fläche.** Der Container von „Farbe/Relief/Höhe/Gloss“
  (`_ModeSegments`) war fälschlich mit dem `tabbar`-Ton hinterlegt; ein
  Abgleich mit den tatsächlichen CSS-Regeln des Prototyps (nicht nur den
  `:root`-Variablen) ergab die rezessierte `--inset`-Fläche als korrekten
  Wert – neu als `inset`-Token ergänzt und verdrahtet. Zwei weitere im
  Prototyp deklarierte, aber dort ungenutzte Token (`label`, `good_line`)
  sind der Vollständigkeit halber in `Palette` übernommen, ohne aktuellen
  Verbraucher; ein `bad_line`-Gegenstück existiert im Prototyp nicht und
  wurde daher nicht erfunden (#479).
- **Canvas-Transparenz-Schachbrett folgt jetzt dem aktiven Theme.** Das
  Schachbrettmuster hinter transparenten Bildbereichen war fest auf
  Hellgrau kodiert (`QColor(170,170,170)`/`(210,210,210)`) und wirkte im
  Dark Mode wie ein heller Fleck mitten in der Leinwand. `checker_a`/
  `checker_b` lösen das über die Palette (dunkel: `#2c313a`/`#353b45`,
  hell: `#dde2ea`/`#eef1f5`); `make_checker_brush` nimmt jetzt die aktive
  Palette entgegen, und `ImageCanvas.apply_palette` erneuert das Muster
  beim Theme-Umschalten live – ohne Neustart der App (#478).
- **REDESIGN_SPEC.md-Farbtabellen korrigiert + Drift-Regressionstest.** Die
  Dokumentation beanspruchte, 1:1 aus dem Prototyp übernommen zu sein, war
  laut eigenem Herkunftshinweis aber nie gegen die tatsächlichen Farbwerte
  geprüft worden – ein Zeile-für-Zeile-Abgleich deckte eigenen Doku-Drift
  auf, unabhängig von `theme.py` (u. a. fehlende `checker_a`/`checker_b`,
  `inset`, `label`, `good_line`, `border_2`; ein `helles Schema` nur als
  Prosa-Auszug statt Tabelle). §2/§3 sind jetzt vollständige Tabellen, die
  exakt `theme.DARK`/`theme.LIGHT` entsprechen; verbleibender, bewusst
  außerhalb dieses Epics belassener Drift des hellen Schemas zum Prototyp
  ist explizit dokumentiert statt stillschweigend verschwiegen. Zwei neue
  Tests in `tests/test_theme.py` sichern das dauerhaft ab: einer vergleicht
  die Spec-Tabellen gegen die Paletten, ein zweiter zusätzlich `theme.DARK`
  direkt gegen die im Prototyp-Bundle eingebetteten CSS-Variablen – beide
  schlagen fehl, sobald Code und Dokumentation wieder auseinanderlaufen
  (#480, schließt Epic #474 ab).
- **Live-Vorschau degradiert bei größenfremden Daten-Ebenen auf COLOR.** Passt die
  Pixelgröße einer HEIGHT-/GLOSS-Ebene (anomaler oder fremder Projektzustand) nicht
  zur Basis, behandelt `_render_preview_uncached` die Ebene jetzt in **jedem**
  Vorschaumodus wie eine fehlende Rolle und fällt auf das COLOR-Komposit zurück,
  statt eine falsch dimensionierte Ansicht zu zeigen oder den Renderpfad mit einer
  Ausnahme abzubrechen – analog zur bestehenden „fehlende/unsichtbare Rolle =
  degradieren"-Regel. Render-/Pixel-Regressionstests schicken eine größenabweichende
  HEIGHT/GLOSS-Ebene durch `HEIGHT`/`RELIEF`/`GLOSS`/`COMBINED` und belegen das
  COLOR-Ergebnis (#404).
- **Toten Geometrie-Pfad im EufyMake-Export entfernt.** Die seit der Umstellung auf
  die Projektmodell-Getter (#377/#378) verwaiste private Funktion
  `_derive_physical_size` und der nur dort genutzte `parse_size_mm`-Import sind
  ersatzlos entfernt; `_derive_target` zieht physische Größe und DPI unverändert aus
  `project.physical_size_mm`/`project.dpi`. Kein Verhaltenswechsel; die
  CLAUDE.md-Geometriebeschreibung zeigt jetzt auf den real genutzten Pfad (#406).
- **Konsistente Canvas-Vorschau nach dem Phase-1-Abschluss.** Farb- und Höhen-
  Live-Vorschauen laufen jetzt als temporäre Layer-Inhalte durch die gewählte
  Modus-Pipeline, sodass Modus, Relief-Stärke und Gloss-Schalter sofort wirken,
  ohne Modell oder Export zu verändern. Ausgeblendete Height-/Gloss-Rollen werden
  nicht mehr gerendert; Relief-Stärke 0 überspringt das teure Hillshade vollständig
  (#397, Follow-up zu #396).
- **Bildexport bei aktiver Höhenebene.** „Bild speichern" schreibt wieder
  unabhängig von der aktiven Bearbeitungsebene das COLOR-Komposit. Die
  graustufige HEIGHT-Ansicht bleibt eine reine Canvas-Darstellung und kann nicht
  mehr still als normales Bild exportiert werden; der bitgenaue Single-COLOR-
  Export einschließlich RGB unter transparenten Pixeln bleibt erhalten (#363).
- **Height-Map-Medianfilter ist speicherbeschränkt.** `height_ops.median_blur`
  materialisiert keinen vollständigen `(2r+1)² × H × W`-Fensterstapel mehr (bei
  40 MP/Radius 10 wären das ~33 GiB gewesen), sondern verarbeitet das Bild
  **zeilenbandweise** mit einem hart über `_MEDIAN_MAX_TEMP_BYTES` begrenzten
  Stapel je Band. Der Zusatzspeicher ist damit vom Bildmaß unabhängig und
  skaliert nicht mehr mit dem Radius; das Ergebnis bleibt **bitgenau** identisch
  (gleiche Randbehandlung, `coverage`, `max_value`, 16-Bit). `gaussian_blur` ist
  als separable Faltung ohnehin `O(H × W)` und radiusunabhängig – Bewertung im
  Docstring. Regressionstests sichern Vollstapel-Äquivalenz über alle UI-Radien
  und das Speicherbudget für den 40-MP-Fall (#365).
- **Höhen-Kontext: Modell, UI und Canvas folgen einem Vertrag.** Eine Ebene ist
  jetzt *genau dann* höhenfähig, wenn `kind == LayerKind.HEIGHT`; die Rolle
  `HEIGHT_MAP` darf nur auf einer HEIGHT-Ebene liegen. Eine neue zentrale,
  Qt-freie Regel (`role_allowed_for_kind`) ist die einzige Quelle der Wahrheit:
  Modell-APIs (`Layer`, `assign_role`) lehnen `HEIGHT_MAP` auf COLOR/GLOSS/
  GENERIC mit `IncompatibleRoleError` ab, das Ebenen-Panel bietet die Rolle nur
  für HEIGHT-Ebenen an, und der Height-Map-Tab aktiviert seine Werkzeuge nur bei
  aktiver HEIGHT-Ebene – die UI verspricht damit keine Operation mehr, die der
  Canvas anschließend ablehnt. Beim Laden eines historisch inkompatiblen
  Projekts wird nur die unzulässige Rolle verlustfrei entfernt (Kind, Name,
  Pixel, Reihenfolge und Metadaten bleiben erhalten) und eine übersetzte Warnung
  angezeigt (#364).

## [2.4.1] – 2026-06-17

### Behoben

- **macOS-Download-App (`.dmg`) öffnete nach dem Start endlos neue Fenster.**
  Im eingefrorenen Bundle startet die KI-Inferenz ihren Kindprozess per
  multiprocessing-„spawn", was dieselbe App-Binärdatei neu startet; ohne
  `multiprocessing.freeze_support()` im Bundle-Einstieg führte jeder
  Kindprozess erneut die GUI aus → Fork-Bomb mit 100+ Fenstern, die nur ein
  Neustart stoppte. Der PyInstaller-Einstieg ruft jetzt zuerst
  `freeze_support()` auf, sodass der Inferenz-Kindprozess korrekt startet statt
  die GUI zu öffnen.

- **macOS-Download-App (`.dmg`) startete nicht.** Das eingefrorene Bundle
  brach bereits beim `import bgremover` mit `PackageNotFoundError` und
  anschließendem `FileNotFoundError` ab, weil PyInstaller die
  Paket-Metadaten nicht mitnahm und im Bundle keine `pyproject.toml` als
  Fallback liegt – das Icon blinkte nur kurz, dann passierte nichts. Die
  PyInstaller-Spec backt die `*.dist-info`-Metadaten jetzt ein
  (`copy_metadata`), und die Versionsermittlung lässt den Start nie mehr
  scheitern (defensiver Fallback statt unbehandelter Ausnahme).

- **KI-Hintergrundentfernung im `.dmg` ließ sich nicht laden.** Der
  Inferenz-Kindprozess starb beim `rembg`-Import mit `PackageNotFoundError`
  („No package metadata was found for pymatting"): PyInstaller bündelt zwar den
  Code der rembg-Abhängigkeiten, nicht aber ihre `*.dist-info`-Metadaten –
  `pymatting` liest beim Import jedoch seine eigene Version. Die Spec backt nun
  die Metadaten der gesamten rembg-Kette ein (`copy_metadata(…, recursive=True)`).

## [2.4.0] – 2026-06-15

### Hinzugefügt

- **macOS-App als Download (`.dmg`).** Ein selbst-enthaltenes
  `BgRemover.app`-Bundle (PyInstaller, Apple Silicon/arm64) wird als `.dmg`
  gebaut und an das GitHub-Release gehängt – analog zur Linux-AppImage und
  ohne lokale Python-Installation. Das Bundle ist vorerst **unsigniert**:
  beim ersten Start einmal per Rechtsklick → „Öffnen" bestätigen. Build über
  `packaging/mac/build_macos.sh`.
- **Download-Artefakte enthalten die KI-Hintergrundentfernung.** Linux-
  AppImage und macOS-`.dmg` bündeln `rembg`/`onnxruntime`, sodass die
  Ein-Klick-KI ohne Nachinstallation läuft (entsprechend größere Artefakte).
- **Release-Workflow baut plattformübergreifend.** `release-linux.yml`
  erzeugt zum Tag `vX.Y.Z` zusätzlich zum Linux-AppImage und `.deb`
  (x86_64 + aarch64/Raspberry Pi OS) ein macOS-arm64-`.dmg` und
  veröffentlicht alle Artefakte gemeinsam.
- **Bilder über Dateizuordnung und Kommandozeile öffnen.** `bgremover bild.png`
  bzw. `python -m bgremover bild.png` öffnet den Pfad nach dem Fensteraufbau über
  denselben validierten, asynchronen Ladepfad wie Datei-Dialog, Recent Files und
  Drag & Drop; der Linux-Desktop-Eintrag (`%F`) und macOS-`QFileOpenEvent`s
  (Finder „Öffnen mit", Doppelklick) werden ebenso verarbeitet. Mehrere Pfade:
  der erste wird geöffnet, die übrigen mit Anzahl in der Statusleiste ignoriert;
  fehlende, nicht unterstützte oder nicht lokale Pfade werden kontrolliert
  abgewiesen statt den Start abzubrechen, und vor dem Verwerfen eines
  bearbeiteten Bildes greift die Nachfrage zu ungespeicherten Änderungen. Beim
  App-Quit werden laufende Worker-Threads zusätzlich sauber beendet (#249).
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
- **`import bgremover` lädt keinen Qt-Stack mehr.** Der Paket-Einstieg
  (`bgremover/__init__.py`) exportiert nur noch leichte Metadaten (`__version__`,
  `get_version`) direkt; die etablierten GUI-/Qt-Re-Exports (`ImageCanvas`,
  `MainWindow`, Worker …) bleiben kompatibel, werden aber per
  PEP-562-`__getattr__` erst beim ersten Attributzugriff geladen. So laufen
  Versions- und Metadatenabfragen headless ohne PyQt6; ein Subprozess-
  Regressionstest stellt sicher, dass ein leichter Import weder
  `bgremover.canvas`/`main_window` noch PyQt6 in `sys.modules` zieht (#232).

### Behoben

- **rembg-Subprozess gehärtet (Robustheit & Speicher).** Vier Folge-Befunde aus
  dem Codex-Review von #283 in `bgremover/ai_process.py`: Die rembg-Session wird
  nach einem transienten `new_session()`-Fehler beim nächsten Request neu und
  genau einmal aufgebaut, statt fortan `remove(..., session=None)` zu rufen und
  das Modell pro Aufruf neu zu laden (die #229-Garantie bleibt erhalten); der
  leerlaufende Kindprozess gibt das letzte Eingabe-PNG sofort frei, statt es
  dauerhaft zu halten; Eingabe- und Ergebnis-PNG reisen als rohe Byte-Frames
  (`send_bytes`/`recv_bytes`) statt durch die Pipe gepickelt, was die
  Speicherspitzen und das OOM-Risiko bei großen Bildern (bis 40 MP) beseitigt;
  und ein `request_stop()` genau während des Prozessstarts wird über ein
  `_proc_lock`/`_stop_pending`-Paar auf den frischen Prozess nachgezogen.
  Regressionstests decken alle vier Pfade ab (#285).
- **Speicherspitzen im gekappten Datei-Read entschärft.** Zwei Folge-Befunde aus
  dem Codex-Review von #264 in `bgremover/image_loading._read_capped`: Der Inhalt
  wird statt mit `b"".join(chunks)` (das Chunks **und** Ergebnis gleichzeitig
  hielt, ~1 GiB nahe dem 512-MiB-Limit) in einem einmal vorab dimensionierten
  `bytearray` zusammengesetzt und direkt weitergereicht – keine ~2×-Spitze mehr.
  Der erste Read wird zudem durch die per `fstat()` bekannte Größe begrenzt,
  sodass eine kleine Datei nicht ~8 MiB Headroom anfordert; ein kleiner
  Folge-Read erkennt weiterhin Wachstum zwischen `fstat()` und Lesen (TOCTOU)
  bzw. ein unzuverlässiges `st_size` (Pipes/Sockets). Die Limit-/Überschreitungs-
  Erkennung (`None`) bleibt unverändert; Regressionstests decken beide Pfade ab
  (#286).
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
- **Release-Workflow-Follow-ups gehärtet.** Der Publish-Job setzt jetzt
  `GH_REPO`, damit `gh release` ohne Checkout das richtige Repository anspricht;
  der wiederverwendbare Test-Job hängt an `verify-tag`, sodass ein ungültiger
  oder zur Paketversion unpassender Tag die Matrix gar nicht erst startet; und
  `download-artifact` lädt die Artefakte per `run-id`/`github-token` (mit
  `actions: read`) aus dem gesamten Run, sodass „Re-run failed jobs“ keine
  Artefakte eines früheren Attempts verliert. README/RESOURCES (inkl.
  Übersetzungen) beschreiben den entfernten `release: published`-Trigger nicht
  mehr (#257).
- **Bildlade-Limit ohne 512-MiB-Voraballokation und lokalisiert.**
  `open_validated_image` liest den Dateiinhalt jetzt in 8-MiB-Chunks (statt
  `read(limit + 1)`, das bei CPythons gepuffertem Reader sofort ~512 MiB
  reserviert und kleine Dateien unter knappem Speicher mit `MemoryError`
  scheitern lässt); Wachstum zwischen `fstat()` und Lesen wird weiterhin mit
  `limit + 1` erkannt. Die Größenmeldung läuft über den Translation-Key
  `status.file_too_large` (de/en vollständig lokalisiert statt gemischter
  Meldung) und rundet den Ist-Wert auf sowie den Grenzwert ab, sodass er bei
  „Limit + 1 Byte“ sichtbar größer ist (z. B. „513 MB“ bei Maximum „512 MB“,
  statt mit `.0f` beide als „512 MB“) (#258).
- **QSettings-Schema-Migration ist downgrade-sicher.** Eine fehlende Migration
  hebt `schema_version` nicht mehr ungeprüft auf den aktuellen Wert, und ein
  zukünftig höheres Schema wird beim Aufbau des Recent-Files-Menüs nicht
  zurückgeschrieben – ein versehentliches Downgrade verliert so keine
  Einstellungen (#234, #259).
- **Escape bricht zuerst das begonnene Lasso ab; Werkzeug-Cursor nach Crop
  wiederhergestellt.** Ein laufendes Polygon-Lasso wird von Escape jetzt zuerst
  abgebrochen, bevor die Auswahl gelöscht wird (Reihenfolge Crop > Lasso >
  Auswahl). Wird ein aktiver Crop automatisch verworfen, stellt `_finish_mode`
  den Cursor des aktiven Werkzeugs wieder her, statt den Crop-Cursor zu behalten
  (#248, #260).
- **Worker-Shutdown ist zeitlich begrenzt.** Beim App-Schließen wartet der
  `WorkerController` nur noch begrenzt auf `quit()`/`wait()`, bevor er als
  Notfall `terminate()` mit erneut begrenztem `wait()` aufruft; ein nicht
  reagierender Worker blockiert das Beenden nicht mehr unbegrenzt, und der
  Fehlerpfad wird geloggt. Das eigentliche `terminate()`-Risiko bei nativer
  ONNX-Arbeit wurde anschließend behoben, indem die rembg/ONNX-Inferenz in einen
  eigenen, per `spawn` gestarteten Prozess (`ai_process`) ausgelagert wurde: Der
  KI-Worker pollt nur noch auf das Ergebnis und ist kooperativ stoppbar, Abbruch
  und App-Schließen beenden den Inferenz-Prozess hart, und `terminate()` ist für
  die KI-Arbeit nicht mehr der Notausgang (#270, Folge aus #231).
- **Pinsel-Overlay vermeidet den Vollscan der Maske pro Mausbewegung.**
  `canvas_selection` führt den Auswahlzähler inkrementell und nutzt die
  Bounding-Box der Änderung, statt bei jeder Pinsel-/Radierbewegung die gesamte
  Maske zu scannen; `has_selection` ist damit O(1). Das hält große Bilder beim
  schnellen Zeichnen flüssig (#261).

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

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.4.1...HEAD
[2.4.1]: https://github.com/NikolayDA/picture_helper/compare/v2.4.0...v2.4.1
[2.4.0]: https://github.com/NikolayDA/picture_helper/compare/64c1f4c87af2a41e82122b361855f0021ec62cf3...v2.4.0
[2.3.0]: https://github.com/NikolayDA/picture_helper/compare/79f61c5514f283fae31ce9d21f31786a3acfbe16...64c1f4c87af2a41e82122b361855f0021ec62cf3
[2.2.0]: https://github.com/NikolayDA/picture_helper/compare/666d4a3932f70eabaafde8de4bfc2a0574be5d16...79f61c5514f283fae31ce9d21f31786a3acfbe16
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/d80067dbc064a8eab5774457eaaffab733c4cab6...666d4a3932f70eabaafde8de4bfc2a0574be5d16
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/d80067dbc064a8eab5774457eaaffab733c4cab6
