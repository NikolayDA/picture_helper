# ADR (2026-07-15): Kanonischer 16-Bit-HEIGHT-Datenvertrag, Migration und Speicherbudget

ADR zu #586 („[16-Bit] ADR: kanonischer HEIGHT-Datenvertrag, Migration und
Speicherbudget") im Epic #581 („Durchgängige 16-Bit-Höhenpipeline").
Status: **beschlossen, Implementierung folgt** (#587–#590; produktive
Umsetzung erst nach der v2.6.0-Veröffentlichung aus #585, damit der
Projektformatwechsel nicht in den Release-Scope-Freeze aus #583 fällt).

## Kontext

`HeightField` (in `bgremover/height_map.py`) führt Höhen bereits als
`numpy.uint16`, arbeitet im Standardpfad aber mit `max_value=255`. Beim
Übergang in Layer-/Projektpfade wird HEIGHT als 8-Bit-RGBA materialisiert
(`height_to_layer`), im `.bgrproj` als 8-Bit-RGBA-PNG persistiert und beim
16-Bit-Export nur gespreizt (`×257`) – ohne echte Quellpräzision. Dieses ADR
legt fest, **wo** die hochpräzisen Werte künftig leben und wie Anzeige,
Deckung, Historie, Persistenz und Export darauf zugreifen.

## Ist-Analyse: Inventar aller HEIGHT-Pfade

Legende: ⚠ = Stelle mit 8-Bit-Konvertierung bzw. möglichem Präzisionsverlust
im künftigen 16-Bit-Betrieb (bei `max_value=255` heute verlustfrei).

### Repräsentation & Konvertierung (`bgremover/height_map.py`)

| Stelle | Funktion | Befund |
|---|---|---|
| Domänenobjekt | `HeightField` (`values: uint16 (H,W)`, `coverage: uint8 (H,W)`, `max_value`, frozen, invariantengeprüft) | 16-Bit-fähig; Standard `max_value=HEIGHT_MAX_8BIT` |
| Layer→Höhe | `layer_to_height(image)` | liest **R-Kanal** einer RGBA-Ebene → nur 8-Bit-Quelle ⚠ |
| Höhe→Layer | `height_to_layer(field)` / `_to_gray8` | skaliert auf 8-Bit-Grau-RGBA; bei `max_value>255` **verlustbehaftet** ⚠ |
| Anzeige | `layer_to_gray_image(image)` | erzwungene Grau-Ansicht = `height_to_layer(layer_to_height(…))` ⚠ |
| Erzeugung | `generate_from_image(…, max_value=…)` | float64-Pipeline, skaliert auf `0..max_value` – bereits 16-Bit-tauglich |
| Normalisierung | `normalize_to_height(data, max_value=…)` | Min-Max auf `0..max_value`, `np.rint` – 16-Bit-tauglich |
| Editieren | `adjust_height`/`set_height`/`invert_height` | rechnen in `int32` relativ zu `max_value`, neue Felder, Deckung kopiert – 16-Bit-tauglich |
| Größen-Invariante | `validate_canvas_size(field, size)` | bitiefenneutral |

### Optimierung (`bgremover/height_ops.py`)

`levels`, `gamma`, `gaussian_blur`, `median_blur`, `threshold`, `quantize`,
`clamp_range` rechnen ausdrücklich im Bereich `0..field.max_value`
(float64-Zwischenrechnung, `_with_values` klemmt auf `uint16`) – **bereits
16-Bit-tauglich**, keine 255-Annahmen. Speicherverhalten: `gaussian_blur`
separabel `O(H×W)`, `median_blur` zeilenbandweise mit hartem
`_MEDIAN_MAX_TEMP_BYTES = 64 MiB`-Deckel (#365).

### Canvas-Verdrahtung (`bgremover/canvas.py`)

| Stelle | Funktion | Befund |
|---|---|---|
| Erzeugen/Import | `generate_height_map` (Z. ~1040), `import_height_map` (~1071, via `open_validated_image` aus `image_loading.py`) | Ergebnis wird sofort via `height_to_layer` als 8-Bit-RGBA-Ebene angelegt ⚠; 16-Bit-PNG-Quellen (`I;16`) werden beim Laden nach RGBA konvertiert ⚠ |
| Editier-Kontext | `_height_edit_context` (~1094) → `layer_to_height(active.image)` | liest aus der 8-Bit-Ebene ⚠ |
| Commit | `_run_height_edit` (~1110) → `_apply_pil(height_to_layer(field))` | **jeder** Editier-Commit quantisiert auf 8 Bit ⚠ |
| Menü-Ops | `lighten_/darken_/set_/invert_active_height` (~1116–1159) | über `_height_edit_context`/`_run_height_edit` ⚠ (transitiv) |
| Malstrich | `_start_/_extend_/_finish_height_stroke` (~1160–1258), `_stroke_field` | Strich-Puffer über `HeightField`, Commit via `height_to_layer` ⚠ |
| Live-Vorschau | `preview_height_op`/`cancel_height_preview`/`apply_height_op` (~1260–1300) | transienter Layer-Override als 8-Bit-RGBA (`height_to_layer`) – reine Anzeige, aber der **Apply**-Pfad committet 8-Bit ⚠ |
| Anzeige-Pipeline | `_render_preview` (~620–650): `PreviewMode.HEIGHT` → `layer_to_gray_image`; `RELIEF/COMBINED` → `relief_shading(layer_to_height(…))` | Anzeigeableitung – gemäß Leitplanke zulässig, solange nichts zurückgeschrieben wird |

### Modell, Historie, Persistenz

| Stelle | Funktion | Befund |
|---|---|---|
| `project_model.py` | `Layer.__init__`/`_ensure_rgba` | materialisiert **jede** Ebene als 8-Bit-RGBA (`astype(np.uint8)`) ⚠ |
| `project_model.py` | `Project.resize` (Z. ~509): `resize_image` (PIL, RGBA) + `layer_to_gray_image` für HEIGHT | Interpolation auf 8-Bit-Kanälen ⚠ |
| `project_model.py` | `Project.duplicate_layer`/Kopierpfade (`image.copy()`) | bitiefenneutral, aber nur `Layer.image` |
| `project_history.py` | `_capture_state`/`_PoolEntry`: Struktur-Snapshots + deduplizierter Pixelpool über `id(layer.image)`; Budget `_HISTORY_MEMORY_LIMIT = 256 MiB` | snapshottet nur `Layer.image` (8-Bit-RGBA) ⚠ |
| `project_io.py` | `save_project`: je Ebene `layer.image.save(…, format="PNG")` (8-Bit-RGBA), atomar via `mkstemp`+`os.replace`; `load_project` mit Größen-/Megapixel-/Zip-Slip-Abwehr | Persistenz ist 8-Bit-RGBA-PNG ⚠ |
| `project_schema.py` | `PROJECT_FORMAT_VERSION = 1`, `_MIGRATIONS`-Haken, Zukunfts-Version → Warnung + Best-effort | Migrationsmechanik vorhanden, Formatwechsel nötig |

### Vorschau & Export

| Stelle | Funktion | Befund |
|---|---|---|
| `relief_preview.py` | `relief_shading(field)` | rechnet in float64 relativ zu `max_value`, `coverage`-bewusst – 16-Bit-äquivalent |
| `gloss_preview.py` | Gloss-Sheen | GLOSS bleibt 8-Bit – nicht betroffen |
| `eufymake_validate.py` | Z. ~226: `layer_to_height(layer.image)` für Leer-/Konstanz-Checks | liest 8-Bit-Ebene ⚠ (transitiv) |
| `eufymake_writer.py` | `_render_height` (Z. ~146): 8-Bit `L`, oder 16-Bit via `values × 257` → `I;16` | Spreizung erzeugt **keine** echte Präzision ⚠ |

**Kern-Befund:** Der einzige strukturelle Verlustpunkt ist die
Materialisierung als 8-Bit-RGBA in `Layer.image` – alle ⚠-Stellen oben sind
Folgen dieser einen Entscheidung. Rechenlogik (`height_ops`,
`generate_from_image`, `relief_shading`) ist bereits 16-Bit-tauglich.

## Optionen

### Option A: Eigene HEIGHT-Payload am Layer (kanonisches `HeightField`)

HEIGHT-Ebenen erhalten eine zusätzliche kanonische Payload
`Layer.height_data: HeightField` (`uint16`-Werte, `uint8`-Coverage,
`max_value=65535`). `Layer.image` bleibt für HEIGHT-Ebenen erhalten, wird
aber zur **abgeleiteten 8-Bit-Ansicht** (aus `height_to_layer` berechnet,
nie zurückgelesen).

### Option B: 16-Bit-fähige Bildrepräsentation für `Layer.image`

`Layer.image` wird für HEIGHT-Ebenen auf ein 16-Bit-Bild umgestellt
(PIL `I;16` plus separat geführtes Alpha, oder ein
`uint16`-RGBA-numpy-Array als neue einheitliche Layer-Repräsentation).

### Option C (Status quo): 8-Bit überall, Spreizung nur am Export

Verworfen ohne Detailvergleich: erfüllt das Epic-Ziel (Niederbits
überleben die Pipeline) per Definition nicht.

### Bewertung

| Kriterium | Option A (HEIGHT-Payload) | Option B (16-Bit-`Layer.image`) |
|---|---|---|
| Korrektheit | Kanonische Werte an genau einer Stelle; Anzeige strikt abgeleitet | PIL `I;16` hat kein Alpha → Coverage muss doch separat geführt werden (faktisch Option A durch die Hintertür); `uint16`-RGBA für alle Ebenen ändert COLOR/GLOSS mit |
| Speicher (je HEIGHT-Layer) | 3 B/px kanonisch + 4 B/px Ansicht = 7 B/px | `I;16`+Alpha: 3 B/px, aber zusätzlich 8-Bit-Ansicht für Canvas nötig → gleich; `uint16`-RGBA: 8 B/px und COLOR verdoppelt sich mit ⚠ |
| Laufzeit | Ableitung 8-Bit-Ansicht 1× je Content-Revision (gecacht wie heute) | PIL-Operationen auf `I;16` sind lückenhaft (kein `I;16`-Compose/Paste); ständige Konvertierungen |
| Qt/PIL/NumPy-Kompatibilität | `Layer.image` bleibt RGBA-uint8 → **alle** bestehenden Compose-/Anzeige-/Persistenzpfade und PIL-RGBA-erwartende Operationen unverändert | Qt-Anzeige und PIL-Compose können `I;16` nicht direkt; jeder Konsument von `Layer.image` muss Fallunterscheidung lernen |
| Testbarkeit | Qt-freier Vertrag in `height_map.py`/`project_model.py`, präzise Einheitstests | Verhalten hängt an PIL-`I;16`-Interna (Resampling/Modus-Konvertierungen sind historisch fehleranfällig) |
| Migration | Additiv: `Layer.image` bleibt, v1-Projekte laden unverändert; nur HEIGHT-Ebenen bekommen die Payload dazu | Bruch der Layer-Invariante „RGBA-uint8"; alle Ebenen-Konsumenten anfassen |
| 3D-Nutzung (#582) | 3D konsumiert direkt `HeightField` (uint16 + Coverage) – exakt der gewünschte Vertrag | 3D müsste aus `I;16`+Alpha erst wieder ein Feldobjekt bauen |

**Verworfen: Option B**, konkrete Nachteile: (1) PIL kennt kein
16-Bit-Grau-mit-Alpha – Coverage bräuchte ohnehin eine zweite Struktur;
(2) die Layer-Invariante „jede Ebene ist RGBA-uint8" bricht für alle
Konsumenten (Compose, Qt-Anzeige, Persistenz, History-Pool, EufyMake), was
COLOR/GLOSS gegen die Leitplanke mitverändert; (3) PIL-`I;16`-Resampling-
und Modus-Konvertierungspfade sind schlechter testbar als reine
numpy-Mathematik. **Verworfen: Option C** (siehe oben).

## Entscheidung: Option A – verbindlicher Datenvertrag

### 1. Kanonische Repräsentation

- **Kanonisch** für HEIGHT-Ebenen ist ein `HeightField` mit
  `values: numpy.uint16`, Shape `(H, W)` (Zeilen × Spalten, wie bisher),
  `coverage: numpy.uint8`, Shape `(H, W)`, und `max_value=65535`.
- Erlaubte `max_value`-Werte: **255** (Legacy-/Kompatibilitätspfad,
  bestehende Semantik) und **65535** (Zielvertrag). Andere Werte lehnt
  `HeightField.__post_init__` mit `HeightMapError` ab (Verschärfung der
  heutigen „nur positiv"-Prüfung).
- `Layer.height_data` hält das kanonische Feld ausschließlich auf Ebenen
  mit `kind is LayerKind.HEIGHT` (Kind↔Rollen-Vertrag aus #364 bleibt).
  `Layer.image` ist auf HEIGHT-Ebenen eine **abgeleitete 8-Bit-Ansicht**
  (`height_to_layer(height_data)`), wird bei jeder Payload-Änderung neu
  berechnet (max. 1× je Content-Revision, gecacht wie die bestehende
  Vorschau-Pipeline aus #387/#397) und **nie** zurückgelesen. Es gibt keine
  zweite Quelle der Wahrheit.

### 2. Werte-/Maskensemantik

- `values[y, x]` ist die Höhe des Pixels: `0` = niedrigste, `max_value` =
  höchste Stufe (**hell = hoch**, konsistent mit `HeightSemantics` des
  EufyMake-Vertrags).
- `coverage[y, x]` ist die Deckung (`0` = kein Material, `255` = voll).
  Höhe und Deckung sind **orthogonal**: ein Pixel mit `coverage == 0`
  behält seinen Höhenwert (kein implizites Nullen), wird aber von Anzeige
  (`height_to_layer`-Alpha), Relief (`relief_shading`-Coverage-Blende) und
  Export (Alpha bzw. Auslassung) als „kein Material" behandelt.
- **Vollständig transparenter Pixel** := `coverage == 0`. „Höhe 0 mit
  Deckung" (flaches Material) und „keine Deckung" sind ausdrücklich
  verschiedene Zustände.

### 3. Normalisierung, Clamping, Rundung

- Zwischenrechnungen laufen in `float64` (bzw. `int32` für Additionen wie
  heute in `adjust_height`); das Endergebnis wird mit
  `np.clip(np.rint(x), 0, max_value).astype(np.uint16)` geklemmt und
  gerundet (Rundung: `np.rint`, round-half-to-even – einheitlich überall).
- Min-Max-Normalisierung (unverändert `normalize_to_height`):
  `v = rint((x - lo) / (hi - lo) * max_value)`; konstante Eingabe → Nullfeld.
- **8→16-Abbildung (Migration/Import 8-Bit-Quellen):** `v16 = v8 × 257`.
  Begründung: `257 = 0x0101 = 65535 / 255` exakt; die Abbildung ist die
  Bit-Replikation `(v8 << 8) | v8`, bildet `0 → 0` und `255 → 65535` ab,
  hält die 256 Stufen äquidistant und ist **deterministisch rückrechenbar**
  (`v8 = v16 // 257` exakt für alle Vielfachen von 257).
- **16→8-Abbildung (Anzeige/8-Bit-Export):** `v8 = rint(v16 / 257)`
  (identisch zu `rint(v16 × 255 / 65535)`, wie heute `_to_gray8`).
- Beispiele (Akzeptanzkriterium):

| Eingabe | 8→16 (`×257`) | Eingabe | 16→8 (`rint(/257)`) |
|---|---|---|---|
| 0 | 0 | 0 | 0 |
| 1 | 257 | 1 | 0 |
| 128 (Mitte) | 32896 | 32768 (Mitte) | 128 |
| 254 | 65278 | 65534 | 255 |
| 255 | 65535 | 65535 | 255 |

  Round-Trip: `rint((v8 × 257) / 257) = v8` für alle 256 Stufen –
  verlustfrei im Sinne der ursprünglichen 8-Bit-Stufen.
- **Quantisierung auf 8 Bit findet nur an benannten Grenzen statt:**
  (a) Ableitung der Anzeige-Ansicht (`height_to_layer`),
  (b) 8-Bit-Export (`eufymake_writer._render_height` mit `bit_depth=8`),
  (c) explizit gewählte verlustbehaftete Operationen (`quantize`,
  `threshold`). Kein weiterer Pfad darf 8-Bit-Zwischenwerte erzeugen.

### 4. Resize/Interpolation

- Höhenwerte werden als `float32`-Bild (PIL-Modus `F`) mit demselben
  Resampling-Filter wie die COLOR-Ebenen (`Project.resize`-Parameter)
  skaliert, danach `rint`+`clip` auf `0..max_value` → `uint16`.
- `coverage` wird separat als 8-Bit-`L`-Bild mit demselben Filter skaliert
  (identisch zur heutigen Alpha-Behandlung im RGBA-Resize).
- Randverhalten: das des gewählten PIL-Filters (unverändert zur heutigen
  RGBA-Skalierung); es gibt keine Sonderbehandlung an Coverage-Kanten –
  Höhenwerte unter `coverage == 0` nehmen normal an der Interpolation teil.
- Die abgeleitete 8-Bit-Ansicht wird nach dem Resize **neu abgeleitet**,
  nie mitskaliert (sonst doppelte Quantisierung).

### 5. Copy/Duplicate/Undo/Redo/Snapshots (Ownership)

- `HeightField` bleibt `frozen`; zusätzlich gilt die Vertragsregel
  **„Arrays sind nach Konstruktion unveränderlich"** – alle Operationen
  geben neue Felder zurück (heute schon so). #587 setzt
  `values.setflags(write=False)`/`coverage.setflags(write=False)` in
  `__post_init__`, damit Aliasing-Verstöße hart fehlschlagen.
- Dadurch dürfen `Project.duplicate_layer`, History-Snapshots und
  `ProjectHistory`-Pool-Einträge die **Referenz teilen** (kein Deep-Copy
  nötig, kein unbeabsichtigtes Aliasing möglich). Der History-Pixelpool
  dedupliziert künftig über `id(layer.height_data)` für HEIGHT-Ebenen und
  zählt `values.nbytes + coverage.nbytes` (3 B/px) statt der 8-Bit-Ansicht;
  die Ansicht selbst wird **nicht** gesnapshottet, sondern nach
  Undo/Redo neu abgeleitet.

### 6. API-Grenzen & Fehlerverhalten

- `HeightField.__post_init__` prüft (wie heute) Shape/dtype/Wertebereich
  und neu die `max_value`-Whitelist `{255, 65535}`; Fehler:
  `HeightMapError` mit konkreter Ist/Soll-Meldung.
- `Layer`-Konstruktion/Persistenz prüft: HEIGHT-Ebene ⇔ `height_data`
  vorhanden und in Canvas-Größe (`validate_canvas_size`); COLOR-/GLOSS-
  Ebene ⇔ keine `height_data`. Verstöße: `ProjectModelError` bzw. beim
  Laden `ProjectFileError` mit übersetzter Meldung (i18n-Keys wie #333).
- Projektdateien mit `values > max_value`, Shape-Mismatch zwischen
  16-Bit-Payload und Ebenen-/Canvas-Größe oder ungültigem dtype werden
  beim Laden mit `ProjectFileError` abgelehnt (defensives Laden wie
  bisher, keine stillen Reparaturen an Pixeldaten).

### 7. COLOR-/GLOSS-Invarianten (unverändert)

- COLOR- und GLOSS-Ebenen bleiben **8-Bit-RGBA (`uint8`, PIL)**: keine
  Format-, Speicher- oder Persistenzänderung; `_ensure_rgba`, Komposit,
  History-Pool und `.bgrproj`-PNGs sind für sie identisch zu heute.
- Der EufyMake-Export von Farbmotiv (RGBA) und Gloss (8-Bit-`L`) bleibt
  bitgenau regressionsfrei; nur `_render_height` wechselt die Quelle.
- Operationen/Konsumenten, die PIL-RGBA erwarten, funktionieren auf
  HEIGHT-Ebenen weiter über die abgeleitete Ansicht `Layer.image`
  (lesend); schreibende Höhenänderungen laufen ausschließlich über die
  Height-API (der Canvas bündelt das heute schon in
  `_height_edit_context`/`_run_height_edit`).

## Projektformat v2 und Migration

- **`PROJECT_FORMAT_VERSION` wird 2.** Ein v2-Manifest ergänzt je
  HEIGHT-Ebene einen Eintrag auf eine zusätzliche Datei
  `layer_NNNN_height16.png`: ein 16-Bit-Graustufen-PNG (`I;16`) mit den
  kanonischen Werten. Die Deckung liegt weiterhin im Alphakanal des
  bestehenden 8-Bit-RGBA-PNGs `layer_NNNN.png`, das für HEIGHT-Ebenen die
  abgeleitete Ansicht enthält (Redundanz ist Absicht: Abwärts-Lesbarkeit).
- **v1 → v2 (8→16):** registrierter `_MIGRATIONS`-Schritt; HEIGHT-Ebenen
  ohne 16-Bit-Datei erhalten `values = v8 × 257` aus dem R-Kanal des
  RGBA-PNGs – verlustfrei im Sinne der ursprünglichen 256 Stufen und
  deterministisch rückrechenbar (siehe Abbildungstabelle). COLOR/GLOSS
  migrieren nicht (keine Änderung).
- **Alte Anwendungsstände mit v2-Dateien:** Der bestehende
  Zukunfts-Versions-Pfad (`project_schema.migrate_manifest`) warnt und
  liest best-effort – ein alter Stand zeigt die 8-Bit-Ansicht korrekt an
  (visuell äquivalent). **Erwartetes, dokumentiertes Verhalten beim
  erneuten Speichern im alten Stand:** Es entsteht eine v1-Datei ohne
  16-Bit-Payload – die Niederbits gehen dabei verloren, aber kontrolliert
  auf die dokumentierte 16→8-Abbildung (keine stillschweigende
  Beschädigung, das Ergebnis ist das definierte 8-Bit-Äquivalent).
- **Beschädigt/inkonsistent:** fehlende/undekodierbare 16-Bit-Datei bei
  v2-Manifest-Eintrag, Größen-Mismatch oder Wertebereichsverstoß →
  `ProjectFileError` (Laden schlägt fehl); die bestehenden Limits
  (`_MAX_ENTRY_UNCOMPRESSED_BYTES`, Megapixel-Gate, Zip-Slip-Abwehr)
  werden für den neuen Eintragstyp mitgezogen (16-Bit-Grau = 2 B/px,
  eigenes Entry-Limit `40 MP × 2 B + Puffer`).
- **Zukunftsversionen (≥3):** unverändert Warnung + Best-effort, keine
  Umschreibung.
- **Atomizität:** unverändert `mkstemp` + genau ein `os.replace`
  (`save_project`); ein Schreibfehler lässt die Zieldatei unversehrt,
  Temp-Dateien werden aufgeräumt.

## Import/Export

- **Import 8-Bit-Quellen** (PNG/JPEG/…): `generate_from_image(…,
  max_value=65535)` skaliert die float-Pipeline direkt auf `0..65535`
  (äquivalent zu `×257` für unbearbeitete Grauwerte).
- **Import 16-Bit-PNG (`I;16`/`I`):** `import_height_map` liest die Werte
  **nativ** (neuer Pfad in `image_loading`/Canvas, #589) statt der
  heutigen RGBA-Konvertierung – echte 16-Bit-Quellen behalten ihre
  Niederbits.
- **Export 8 Bit:** `v8 = rint(v16 / 257)` (benannte Quantisierungsgrenze).
- **Export 16 Bit:** `eufymake_writer._render_height` schreibt
  `height_data.values` direkt als `I;16` – echte Quellpräzision statt
  `×257`-Spreizung; bei Legacy-Feldern (`max_value=255`) bleibt die
  Spreizung als definierte 8→16-Abbildung.

## Ressourcen- und Speicherbudget

Alle Angaben je HEIGHT-Ebene; COLOR/GLOSS unverändert 4 B/px.

| Größe | kanonisch (`values`+`coverage`, 3 B/px) | + abgeleitete Ansicht (4 B/px) | Summe |
|---|---|---|---|
| 1 MP | 3 MB | 4 MB | 7 MB |
| 16 MP | 48 MB | 64 MB | 112 MB |
| 40 MP | 120 MB | 160 MB | 280 MB |

- **Aktives Projekt:** bestehendes 40-MP-Gate (`_MAX_MEGAPIXELS`) bleibt
  das harte Limit; eine HEIGHT-Ebene kostet künftig 7 B/px statt 4 B/px
  (Faktor 1,75).
- **History:** Budget bleibt `_HISTORY_MEMORY_LIMIT = 256 MiB`. Gezählt
  wird die **kanonische** Payload (3 B/px – *weniger* als die heute
  gesnapshottete 8-Bit-RGBA-Ansicht mit 4 B/px); die Ansicht wird nach
  Undo/Redo neu abgeleitet statt gespeichert. Worst case 40 MP: 120 MB je
  geändertem Height-Snapshot → mindestens 2 volle Schritte im Budget;
  Dedup-Pool (unveränderte Ebenen zählen einmal) und bestehende Eviction
  (`_trim`, älteste zuerst) bleiben die Strategie für viele Snapshots.
- **Preview-Cache:** unverändert genau **ein** gerendertes Bild je
  Content-Revision + Anzeigeparameter (#387); die 8-Bit-Ansicht einer
  HEIGHT-Ebene wird höchstens 1× je Content-Revision abgeleitet.
- **Temporäre Operationen:** float64-Zwischenpuffer (8 B/px) sind vom
  `max_value` unabhängig – **keine Regression** durch 16 Bit. Erlaubte
  Häufigkeit: ≤ 3 gleichzeitige Volltemps je Operation (Gauß separabel),
  `median_blur` hart über `_MEDIAN_MAX_TEMP_BYTES = 64 MiB` gedeckelt.
- **Kopien an UI-/Exportgrenzen (Inventar + Obergrenze):**
  (1) Ansicht-Ableitung ≤ 1×/Content-Revision, (2) Qt-Konvertierung des
  Render-Ergebnisses ≤ 1×/Frame (bestehend), (3) Export rendert je Asset
  genau eine Zielkopie, (4) transienter Vorschau-Override hält genau eine
  zusätzliche Ansicht.
- **Messbare Zielwerte:** werden als **Baseline-Aufgabe in #590**
  erhoben (bestehende `benchmark.yml`-Infrastruktur): Import 16-Bit-PNG,
  eine repräsentative Operation (`gaussian_blur`), `.bgrproj`-Roundtrip
  und Preview-Aktualisierung, jeweils bei 1/16/40 MP. Abnahmekriterium:
  ≤ 1,5× der 8-Bit-Baseline desselben Laufs; Speicher-Peaks innerhalb der
  Budgets dieser Tabelle.

## Konsequenzen und Abbildung auf die Folge-Issues

- **#587 – Domänenmodell & History:** setzt Abschnitte „Kanonische
  Repräsentation", „Werte-/Maskensemantik", „Copy/…/Snapshots" und
  „API-Grenzen" um (`Layer.height_data`, Ansicht-Ableitung, Pool-Zählung,
  `max_value`-Whitelist, Immutability-Flags).
- **#588 – Projektformat v2:** setzt „Projektformat v2 und Migration" um
  (Manifest v2, `layer_NNNN_height16.png`, `_MIGRATIONS`-Schritt,
  Entry-Limits, Fehlerpfade, Atomizität).
- **#589 – Import/Erzeugung/Operationen:** setzt „Normalisierung/…",
  „Resize/Interpolation" und „Import/Export"-Importteil um
  (16-Bit-Erzeugung, nativer `I;16`-Import, Editier-/Op-Pfade ohne
  8-Bit-Zwischenschritt).
- **#590 – Preview/Export/UI/E2E:** setzt „Import/Export"-Exportteil, die
  benannten Quantisierungsgrenzen in der Anzeige und die
  Baseline-/Zielwert-Messung um; End-to-End-Niederbit-Test aus dem Epic.
- **#582 (3D-Epic):** konsumiert **dieses** `HeightField`
  (`uint16`/`coverage`/`max_value=65535`) als einzige
  Höhen-Schnittstelle; eine zweite HEIGHT-Repräsentation wird nicht
  eingeführt.
- Rollback-Strategie: Da `Layer.image` als Ansicht erhalten bleibt und v2
  die 8-Bit-PNGs weiter schreibt, kann ein Rollback (Feature-Revert) v2-
  Dateien weiterhin als „v1 + ignorierte Zusatzdatei" lesen.

## Offene Risiken

- PILs `I;16`-Schreib-/Lesepfade sind plattform-/versionsabhängig weniger
  ausgetreten als RGBA – #588 braucht Roundtrip-Tests mit gezielten
  Niederbit-Mustern (inkl. Endianness-Kontrolle über numpy statt
  PIL-Modusraten).
- Der History-Umbau (Pool-Schlüssel je Payload statt je `Layer.image`)
  muss die Budget-Buchführung für gemischte Projekte (COLOR-RGBA +
  HEIGHT-Payload) exakt halten; #587 ergänzt gezielte Budget-Tests.
- Die Redundanz „8-Bit-Ansicht + 16-Bit-Payload" in v2 vergrößert
  Projektdateien um die 16-Bit-Grau-PNGs (≤ 2 B/px unkomprimiert); das
  1-GiB-Dateilimit bleibt, wird aber bei vielen 40-MP-HEIGHT-Ebenen
  schneller erreicht – akzeptiert zugunsten der Abwärts-Lesbarkeit.
