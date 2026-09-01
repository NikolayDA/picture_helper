# ADR (2026-09-01): COLOR-Tonwert-, Histogramm- und Graustufen-Datenvertrag

ADR zu #692 („[COLOR] ADR und Datenvertrag für Tonwert-, Histogramm- und
Graustufenoperationen") im Epic #682 („COLOR-Tonwert-/Graustufen-Engine –
gemeinsame, testbare Basis für Bildoptimierung und Laser").
Status: **beschlossen, Implementierung folgt** (#693–#696; produktive
Core-Arbeit beginnt erst nach Review und Merge dieses ADRs – das ist das
letzte Akzeptanzkriterium von #692).

## Kontext

`bgremover/color_ops.py` stellt mit `adjust_color()` die einzige
COLOR-Tonwert-Primitive bereit (Helligkeit/Kontrast/Sättigung, #360); der
Tab „Anpassen" nutzt sie mit Live-Vorschau über
`Canvas.preview_color_op()`/`apply_color_op()`. Histogramm, Levels, Gamma
und ein expliziter Graustufenvertrag fehlen. Gleichzeitig existieren
Levels, Gamma und die Rec.-601-Luminanz bereits Qt-frei im Höhenpfad
(`height_ops.py`, `height_map.py`) und einmal literal dupliziert in
`gloss_preview.py`. Dieses ADR legt den Datenvertrag fest, gegen den Core
(#693), UI (#694), Integration (#695) und Abnahme (#696) gebaut und
getestet werden – und entscheidet je bestehender Fundstelle, ob COLOR sie
teilt, formelgleich nachbildet oder begründet abweicht, damit keine zweite,
abweichende Tonwert-Mathematik entsteht.

## Ist-Analyse: Inventar der bestehenden Verträge

### COLOR-Pfad (`color_ops.py`, `canvas.py`, `right_panel_tabs.py`)

| Stelle | Funktion | Vertrag heute |
|---|---|---|
| Primitive | `adjust_color(img, *, brightness=1.0, contrast=1.0, saturation=1.0)` (`color_ops.py:22-55`) | Pillow-Kette `Brightness → Contrast → Color` auf den abgespaltenen RGB-Kanälen; Original-Alpha wird bitgenau wieder angehängt; Neutralwerte `1.0/1.0/1.0` geben **dasselbe Eingabeobjekt** zurück (echtes No-op), jeder einzelne Neutralfaktor überspringt seinen Schritt; Nicht-RGBA wird intern per `convert("RGBA")` konvertiert; Eingabe wird nie mutiert |
| Validierung | – | keine: keine Parameterprüfung, keine eigene Fehlerklasse, kein eigenes Clipping/Runden (alles in Pillows `Image.blend`, C-seitig auf `uint8` geklemmt) |
| Vorschau | `preview_color_op(op)` (`canvas.py:1486-1500`) | **synchron im UI-Thread**: `op(active.image)` sofort, Ergebnis als transienter Layer-Override `(active.id, Bild)`; ohne aktive COLOR-Ebene stilles Überspringen; **kein** Exception-Fang (Asymmetrie zu `preview_height_op`, das `HeightMapError` still schluckt); Modell/History/Dirty unberührt |
| Verwerfen | `cancel_color_preview()` (`canvas.py:1502-1507`), `_set_image_state()` (`canvas.py:858-865`) | Override wird bei jedem Bildzustandswechsel verworfen; expliziter Cancel hat genau **einen** Aufrufer („Zurücksetzen"-Button); beim Schrittwechsel verlässt sich der Farbpfad darauf, dass `cancel_height_preview()` dasselbe Feld leert – Direktsprung „Anpassen" → „Relief & Ebenen" lässt eine Farb-Vorschau stehen (Nachprüfung in #694) |
| Commit | `apply_color_op(op)` (`canvas.py:1510-1536`) | rechnet `op(active.image)` **neu** aus dem aktuellen Modellzustand (Vorschaubild wird nie übernommen), committet das **volle** Ebenenbild als genau einen Undo-Schritt über `_apply_pil` → `ProjectHistory.push` (Vor-Zustand, `history.desc.color_adjusted`); **kein** No-op-Check (auch wertgleiche Ergebnisse erzeugen einen Undo-Eintrag), **kein** Exception-Fang (anders als `apply_height_op`); ohne aktive COLOR-Ebene wird die Vorschau verworfen und `canvas.not_color_layer` gemeldet; die Auswahlmaske wird im gesamten Farbpfad **ignoriert** |
| UI | `AdjustTab` (`right_panel_tabs.py:755-810`) | drei Slider 0..200 (Neutral 100), Mapping `value/100.0` → Faktor 0.0..2.0; **kein Debounce** – jedes `valueChanged` rechnet synchron das volle Bild; „Zurücksetzen" stellt 100 her und ruft `cancel_color_preview()` |
| Dirty | `main_window.py:951-964` | kein Flag; `content_revision != _saved_revision`; die transiente Vorschau erhöht die Revision nie |

### Bestehende Tonwert-/Luminanz-Definitionen (Entscheid je Fundstelle nötig)

| Fundstelle | Definition heute |
|---|---|
| `height_ops.levels(field, black, white)` (`height_ops.py:40-53`) | `out = rint(clip((v − black) / (white − black), 0, 1) · max_value)`, float64-Zwischenrechnung; Validierung `0 ≤ black < white ≤ max_value` (Schwarz==Weiß abgewiesen, keine Division durch 0) |
| `height_ops.gamma(field, value)` (`height_ops.py:56-65`) | `out = rint((v / max_value)^value · max_value)`; `value ≤ 0` abgewiesen, **kein** `isfinite`-Check (NaN/Inf passieren die Prüfung); `value > 1` senkt Mitten |
| Finalisierung `_with_values` (`height_ops.py:31-34`) | einheitlich `np.clip(np.rint(x), 0, max_value).astype(np.uint16)` – `np.rint` = round-half-to-even |
| `height_map.generate_from_image(...)` (`height_map.py:408-469`) | float64-Luminanz `Σ (w_c/Σw)·c` (jedes Gewicht einzeln normiert; `Σw` in float64 nicht exakt 1.0) mit `LUMA_WEIGHTS_REC601 = (0.299, 0.587, 0.114)` (`height_map.py:67`), dann `clip((luma − black)/(white − black), 0, 1)` (black/white immer im 8-Bit-Raum), optional `^gamma`, optional `1 − x`, `rint(norm · max_value)` → `uint16` |
| `gloss_preview._gloss_mask` (`gloss_preview.py:30-42`) | dieselben Koeffizienten **literal dupliziert** (`R·0.299 + G·0.587 + B·0.114`, ohne Summen-Normierung, ÷255); 16-Bit-Zweig akzeptiert `I;16/I;16L/I;16B`, aber nicht `I;16N` (Abweichung von `height_map._NATIVE_16BIT_MODES`) |
| `color_ops`-Sättigung | `ImageEnhance.Color` entsättigt gegen `convert("L")` – Pillows ITU-R-601-Festkomma-Luminanz (siehe Messung unten) |

Repo-weiter Grep: Die Koeffizienten `0.299/0.587/0.114` existieren in
`bgremover/` exakt zweimal – als geteilte Konstante `LUMA_WEIGHTS_REC601`
und als Literal in `gloss_preview.py:39`.

### Empirische Messung der Pillow-Luminanz (Pillow 12.3.0, gepinnt)

Exhaustiv über alle 2²⁴ RGB-Kombinationen gemessen (Skript analog
`tests/`-Fixtures, Pin `pillow==12.3.0` in `requirements/constraints.txt`):

- `convert("L")` ist exakt die Festkomma-Formel
  `L = (19595·R + 38470·G + 7471·B + 0x8000) >> 16`
  (Gewichte ÷65536 ≈ 0.29900/0.58701/0.11400, Summe exakt 65536; 0 Abweichungen).
- `ImageEnhance.Color(...).enhance(0.0)` liefert exakt `convert("L")` auf
  allen drei Kanälen (R=G=B) – `saturation=0` **ist** heute eine
  wohldefinierte Graustufenumwandlung.
- Gegen die float64-Referenz `rint(0.299·R + 0.587·G + 0.114·B)` weichen
  9 443 von 16 777 216 Werten (0,056 %) um genau ±1 ab; max |Δ| = 1.
- Die echte `generate_from_image`-Codeformel (jedes Gewicht einzeln über
  `Σw` normiert, `Σw` ist in float64 `0.9999999999999999`, nicht exakt 1.0)
  weicht von der Pillow-Festkomma-Formel in 9 128 von 16 777 216 Werten
  (0,054 %) um genau ±1 ab.

### Auswahlsemantik heute

| Aspekt | Ist-Zustand |
|---|---|
| Repräsentation | `CanvasSelection` hält ein **binäres** `numpy`-Bool-Array `(H, W)` (`canvas_selection.py:16-25`); keine Zwischenwerte, kein Antialiasing; 8-Bit-Zwischenschritte (Morphologie, Lasso-Rasterung) werden sofort mit Schwelle `> 127` rebinarisiert (`canvas_selection.py:54-63`, `canvas_lasso.py:102-111`) |
| Anwendung | überall hart (`np.where`/Fancy-Indexing), nirgends gewichtet: `remove/replace_selection` (`image_ops.py:24-38`), `feather_alpha` (`image_ops.py:194`), Höhen-Edits (`height_map.py:517-568`) |
| Leere Auswahl | zwei Semantiken: `apply_remove/apply_replace` brechen mit Meldung ab (`canvas.py:1846-1853`); `feather_active_edges` und alle Höhen-Edits wirken global (`mask=None`, `canvas.py:1665`, `:1218`) |
| Validierung | nur der Höhenpfad prüft Form/Dtype (`height_map.py:507-514`, `HeightMapError`); `image_ops` prüft nichts |
| Lebensdauer | `_set_image_state` resettet die Auswahl bei **jedem** Zustandswechsel auf Ebenengröße und leer (`canvas.py:873`) – Größen-Mismatch ist im Canvas strukturell ausgeschlossen |
| COLOR/Höhen-Ops | Farbkorrektur und Höhen-Optimierungen (`height_ops`) ignorieren die Auswahl vollständig (`canvas.py:1486-1536`, `:1405-1467`) |

Eine gewichtete Mischung über weiche Maskenkanten existiert heute in
keinem Pfad; dieses ADR definiert sie neu.

### Nebenläufigkeits-Referenzmuster im Repo

`Preview3DController` (#594): 200-ms-Single-Shot-Debounce
(`preview3d_controller.py:31-32`), monotone Generation-ID, die schon beim
Parameterwechsel erhöht wird und laufende Builds entwertet, Verwerfen
verspäteter Ergebnisse in `_on_mesh_ready`/`_on_mesh_error`
(`preview3d_controller.py:215-275`), Ein-Ergebnis-Cache mit
inhaltsbasiertem Key (`content_revision`, ohne reine Anzeigeparameter).
`WorkerController.start_mesh_build` (`worker_controller.py:382-438`):
Superseding mit kooperativem `cancel()`, Draining-Liste,
identitätsgeprüftes Handle-Cleanup; `shutdown_all`
(`worker_controller.py:440-512`) für den Fenster-Lebenszyklus.
`ProjectHistory.push` (`project_history.py:464-467`): genau ein Push des
Vor-Zustands je Commit, Payloads referenziert im Dedup-Pool
(256-MiB-Budget), kein eigener No-op-Check.

## Optionen

### Option A: Qt-freie Erweiterung von `color_ops` + geteilter wertebereichsunabhängiger Tonwert-Kern

Histogramm, Graustufe, Levels/Gamma und Maskenmischung als reine
numpy-/Pillow-Funktionen in `color_ops.py`; die Levels-/Gamma-Kurvenmathematik
zieht in ein neues Qt-freies Modul `tone_curve.py`, auf das `height_ops`
verhaltensgleich delegiert. Helligkeit/Kontrast/Sättigung und die
Graustufenumwandlung bleiben exakt die bestehende Pillow-Semantik
(Bitparität mit `adjust_color` und `saturation=0`).

### Option B: Linearisierte Pipeline (sRGB → linear → Operationen → sRGB)

Tonwertoperationen rechnen in linearem Licht statt im kodierten
sRGB-Tonwert.

### Option C: Wiederverwendung von `height_ops` direkt (COLOR-Kanäle als `HeightField`)

R/G/B werden je Operation per ×257 in drei `uint16`-`HeightField`s
gehoben, mit `height_ops.levels/gamma` bearbeitet und zurückquantisiert.

### Option D: UI-nahe Qt-Implementierung

Histogramm/Levels direkt im Panel (QImage/QPainter), ohne Qt-freien Core.

### Bewertung

| Kriterium | A (geteilter Kern) | B (linear) | C (`HeightField`-Umweg) | D (Qt-nah) |
|---|---|---|---|---|
| Bitparität zu `adjust_color`/`saturation=0` | garantiert (identische Pillow-Schritte) | gebrochen (andere Tonwertdomäne) | gebrochen (±1-Fälle durch 0..65535-Umweg) | offen, je Implementierung |
| Eine Tonwert-Mathematik im Repo | ja: Kern geteilt, Höhenpfad bitgenau unverändert | nein: zweite Domäne neben `height_ops` | scheinbar ja, aber Rundungsdomäne weicht ab | nein: dritte, UI-gebundene Definition |
| Headless-Testbarkeit (Epic-Prinzip) | voll (Qt-frei, deterministische Fixtures) | voll | voll | nicht gegeben |
| Performance/Speicher | uint8/float64 nur je Stufe | float-Pipeline durchgängig nötig (8-Bit-Linear bandet in Schatten) → ×4-Puffer | 3×2 B/px Zusatzkopien + Konvertierungen je Regler-Tick | UI-Thread-Last wie heute |
| Laser-Adapter (#696: Core importierbar ohne UI) | ja | ja | ja, aber semantisch verrenkt (`max_value`-Whitelist, Coverage passen nicht auf Farbkanäle) | nein |

**Verworfen: Option B**, konkrete Nachteile: (1) bricht die geforderte
Bitparität mit der bestehenden `adjust_color`-Kette und Pillows
`ImageEnhance`-Semantik – jede heutige Reglerstellung ergäbe andere Pixel;
(2) in 8 Bit erzeugt Linearlicht sichtbares Banding in den Schatten, eine
durchgängige float-Pipeline kostete das Vierfache an Zwischenspeichern;
(3) der visuelle „Fehler" des kodierten Arbeitens ist die etablierte
Konvention aller Referenz-Editoren (Photoshop-/GIMP-Levels arbeiten
default kodiert), und die Ziel-Consumer (Anzeige, Laser-Graustufen)
erwarten kodierte Tonwerte. **Verworfen: Option C**: (1) drei
`uint16`-Umwege plus Rückquantisierung je Interaktion (Speicher und Zeit)
für mathematisch identische Kurven; (2) der `HeightField`-Vertrag
(`max_value`-Whitelist {255, 65535}, orthogonale Coverage, ADR #586) passt
semantisch nicht auf Farbkanäle; (3) die Rundungsdomäne 0..65535 → 0..255
erzeugt gegenüber direkter 8-Bit-Rechnung neue ±1-Fälle – Parität wäre nur
scheinbar erreicht. **Verworfen: Option D**: (1) verletzt das
Epic-Prinzip „Core kennt kein Qt, deterministisch testbar"; (2) schafft
genau den zweiten, abweichenden Bedienpfad, den #692 ausschließt;
(3) Laser-Consumer müssten UI-Closures nachahmen – von #696 ausdrücklich
verboten.

## Entscheidung: Option A – verbindlicher Datenvertrag

### 1. Kanonisches Eingabe-/Ausgabeformat

- **Kanonisch ist 8-Bit-RGBA** (PIL `RGBA`, `uint8`) – die
  Layer-Invariante aus ADR #586 §7 (COLOR-Ebenen bleiben `uint8`-RGBA)
  gilt unverändert; das Epic-Nicht-Ziel „keine 16-Bit-Pipeline im MVP"
  wird hiermit **bestätigt**: Dieses ADR legt 16 Bit ausdrücklich *nicht*
  als zwingend fest. Konsequenz und bekannte Grenze: 8-Bit-Levels können
  bei extremen Spreizungen Banding erzeugen (#696 dokumentiert das unter
  „Bekannte Grenzen").
- **Konvertierungsregel an der Engine-Grenze:** `RGB`, `L`, `LA` und `P`
  werden deterministisch per `convert("RGBA")` übernommen (Pillow-Regel,
  wie heute in `adjust_color`). **Unerwartete Modi** – alle 16-Bit- und
  Float-Modi (`I`, `I;16*`, `F`) sowie sonstige Exoten – werden von den
  neuen Engine-Funktionen mit `ColorOpsError` abgewiesen statt still
  verlustbehaftet konvertiert (Muster
  `UnsupportedHeightSourceError`, #589). Im Canvas-Pfad ist die Eingabe
  durch die Layer-Invariante ohnehin immer RGBA.
- **Kompatibilität:** `adjust_color()` behält Signatur und tolerantes
  `convert("RGBA")` unverändert (kein Migrationszwang für bestehende
  Aufrufer, #693-Kriterium). Die strengere Modus-Regel gilt nur für die
  neuen Funktionen – die einzige Alt/Neu-Abweichung der
  Modus-/Konvertierungsregel, hier einzeln begründet: Ein 16-Bit-Graubild
  durch `convert("RGBA")` zu quetschen wäre stiller Präzisionsverlust,
  den #589 für Höhen bereits verbietet. (Alle beabsichtigten
  Verhaltensänderungen dieses Vertrags bündelt Abschnitt 12.)
- Ausgaben sind immer `RGBA`; die Bildgröße bleibt exakt erhalten. Das
  gilt auch im Neutralfall: Der Same-Object-No-op (Abschnitt 6) greift
  nur, wenn die Eingabe bereits `RGBA` ist – akzeptierte
  Nicht-RGBA-Modi werden auch bei Neutralparametern konvertiert (die
  Ausgaberegel schlägt die Objektidentität; beides zusammen wäre für
  `RGB`/`L`/`LA`/`P` unerfüllbar). Das weicht bewusst vom heutigen
  `adjust_color`-Neutral-Guard ab, der **vor** der Konvertierung steht
  und ein `RGB`-Objekt unverändert zurückgibt (Abschnitt 12).

### 2. Farbraum und Transferfunktion

Das MVP arbeitet **im kodierten sRGB-Tonwert** (nicht linearisiert), ohne
Farbmanagement. Visuelle Folge: Tonwertoperationen wirken wie in den
Referenz-Editoren (Levels/Gamma auf kodierten Werten); Mischungen sind
photometrisch nicht exakt, was für die Zielworkflows (Anzeige,
Laser-Graustufen) irrelevant ist. Technische Folge: dieselbe
Tonwertdomäne wie alle bestehenden Pfade und keine 2×-Konvertierung;
**Bitparität** besteht konkret mit der `ImageEnhance`-Kette aus
`adjust_color` (Abschnitt 6) – gegenüber `generate_from_image`/
`gloss_preview` bleibt die in Abschnitt 3/4 dokumentierte
±1-Festkomma-Abweichung. Performance-Folge: keine
zusätzlichen float-Vollbildpuffer über die je Stufe ohnehin nötigen
hinaus. ICC/Softproofing bleibt Nicht-Ziel des Epics.

### 3. Graustufen-/Luminanzvertrag

- **Preset-Registry:** Graustufenpresets haben stabile String-IDs in
  einem zentralen Mapping (`GRAYSCALE_PRESETS`); unbekannte IDs werden mit
  `ColorOpsError` abgewiesen. Das MVP definiert genau **ein** Preset:
  - `"rec601"` – verständlicher Name „Luminanz (Rec. 601)";
    dokumentierte Gewichte: Festkomma `19595/38470/7471` (÷65536, Summe
    exakt 65536; nominell 0.299/0.587/0.114).
- **Formel (bindend):** `L = (19595·R + 38470·G + 7471·B + 32768) >> 16`
  – exakt Pillows `convert("L")`-Festkomma-Arithmetik, empirisch für die
  gepinnte Pillow-Version über alle 2²⁴ RGB-Werte verifiziert (siehe
  Ist-Analyse). Reine Ganzzahlarithmetik: keine Rundungs-, keine
  Normalisierungsfreiheit. Output: `R = G = B = L`, **Alpha bitgenau
  unverändert**.
- **`saturation=0` ⇔ Preset `"rec601"`:** bindend und zu testen (#693) –
  `adjust_color(img, saturation=0.0)` und die Graustufenumwandlung mit
  Preset `"rec601"` liefern identische RGB-Werte. Das ist heute empirisch
  exakt erfüllt (`ImageEnhance.Color.enhance(0.0)` ≡ `convert("L")`); der
  Test macht die Pillow-Abhängigkeit zum Wächter: Verschiebt ein
  Pillow-Update die `convert("L")`-Arithmetik, schlägt die Parität
  sichtbar fehl, statt still zu driften.
- **Kein Neutralwert:** Die Graustufenumwandlung hat bewusst kein
  No-op-Preset; „Graustufe aus" ist die Abwesenheit des Schritts in der
  Pipeline (Abschnitt 6), nicht ein Identitäts-Preset.
- Die float64-Referenz `rint(0.299·R + 0.587·G + 0.114·B)` weicht in
  0,056 % der Werte um ±1 ab – deshalb ist die **Festkomma-Formel** und
  nicht die float-Formel der Vertrag: Nur sie garantiert die
  `saturation=0`-Äquivalenz bitgenau.

### 4. Entscheid je bestehender Fundstelle (Reaudit-Kriterium aus #692)

| Fundstelle | Entscheid |
|---|---|
| `height_ops.levels` / `height_ops.gamma` | **Teilen über einen gemeinsamen, wertebereichsunabhängigen Kern.** Neues Qt-freies, streng getyptes Modul `tone_curve.py` mit reinen float64-Kurvenprimitiven `levels_norm(values, black, white)` = `clip((values − black) / (white − black), 0, 1)` und `gamma_norm(norm, exponent)` = `norm ** exponent` – ohne Validierung, ohne Rundung, ohne Wertebereichsannahme (Validierung und Finalisierung bleiben bei den Aufrufern). `height_ops.levels/gamma` delegieren darauf mit **identischer Operationsfolge** – das bitgenaue Verhalten der Höhenpfade bleibt unverändert und wird per Regressionstest gegen die heutige Implementierung gepinnt (Spiegelkriterium in #693). Die `height_ops`-Validierungen (`0 ≤ black < white ≤ max_value`, `gamma > 0` ohne `isfinite`) bleiben exakt wie heute. |
| `height_map.generate_from_image` | **Bleibt eigenständig, formelgleich in den Koeffizienten.** Die float64-Luminanz über `LUMA_WEIGHTS_REC601` dient der Höhenerzeugung (Skalierung auf `0..max_value`, eigene Kennlinie), nicht der Anzeige-Graustufe; sie delegiert im MVP nicht auf `tone_curve` (kein Umbau ohne Not am 16-Bit-Pfad). Die **bewusste Abweichung** zur COLOR-Graustufe (float64-`rint` vs. Pillow-Festkomma; gemessen an der echten Codeformel: ±1 in 9 128 von 2²⁴ Werten, 0,054 %) wird im Docstring beider Seiten dokumentiert; ein Test pinnt die Koeffizienten beider Definitionen gegeneinander (gleiche nominelle Gewichte). |
| Luminanz-Literale in `gloss_preview._gloss_mask` | **Konsolidieren:** importiert künftig `LUMA_WEIGHTS_REC601` statt der Literale – bitgleich, weil die Werte identisch sind; die Begründung („eine Quelle der Wahrheit für Rec.-601-Gewichte") steht dann im Code. Kleinaufgabe in #693. Die COLOR-Graustufe weicht von dieser float64-Luminanz **bewusst** ab (Festkomma-Vertrag, Abschnitt 3). Die dort beobachtete `I;16N`-Lücke des 16-Bit-Zweigs ist nicht Teil dieses Vertrags (separater Kleinbefund). |
| `color_ops.adjust_color` (Sättigung) | **Ist die COLOR-Graustufen-Definition** (Abschnitt 3): `saturation=0` ≡ Preset `"rec601"`, bindend getestet. |

### 5. Histogrammvertrag

- **Kanäle:** `R`, `G`, `B` und `LUMA` (Preset-`"rec601"`-Formel,
  Ganzzahlarithmetik – exakt derselbe Wert, den die Graustufenumwandlung
  erzeugen würde).
- **Bins:** exakt 256 je Kanal; Bin `i` zählt genau die Pixel mit
  Tonwert `i` (keine Bereichs-Bins, keine Normalisierung im Core).
- **Zählertyp:** `int64` (natives `np.bincount`-dtype; überlaufsicher –
  das 40-MP-Gate begrenzt auf < 2³⁶ zählbare Pixel).
- **Transparenz:** Pixel mit `A == 0` werden **nicht** gezählt (nach
  Hintergrund-Entfernung würden die bedeutungslosen RGB-Werte großer
  transparenter Flächen das Histogramm dominieren); Pixel mit `A > 0`
  zählen voll (keine Bruchgewichtung – ganzzahlige, deterministische
  Zähler).
- **Auswahlbezug:** `compute_histogram(image, *, mask=None)` unterstützt
  **beides** – ganzes Bild (`mask=None`) und Auswahl. Einbezogen sind
  Pixel mit Maskenwert `> 127` – dieselbe Mehrheitsschwelle, mit der die
  bestehende Auswahl-Pipeline rebinarisiert (`canvas_selection.py:54-63`).
  Diese Schwelle ist ein **bewusster Unterschied** zur anteiligen
  `m/255`-Mischung der Bearbeitung (Abschnitt 8): Die Statistik zählt
  ganzzahlig und deterministisch (ein Pixel zählt ganz oder gar nicht),
  die Bearbeitung mischt anteilig – dasselbe Muster wie der
  `A == 0`-Unterschied unten. Welcher Bezug angezeigt wird, macht die UI
  sichtbar (#694).
- **Leere Menge:** eine übergebene Maske ohne einen einzigen Wert
  `> 127`, ein vollständig transparentes Bild oder 0 Pixel ergeben ein
  **Nullhistogramm** (alle Bins 0, `total == 0`) – definiertes Ergebnis,
  kein Fehler (#693 testet diesen Fall). Eine *leere Canvas-Auswahl*
  (`has_selection == False`) erreicht die Engine dagegen als `mask=None`
  (Abbildungsregel in Abschnitt 8) und ergibt das Ganzbild-Histogramm –
  dieselbe Regel wie bei der Bearbeitung, kein Widerspruch.
- **Ergebnis-DTO:** frozen Dataclass `Histogram` mit vier
  `(256,)`-`int64`-Arrays (write-locked, Muster `HeightField`) und
  `total` (Zahl der gezählten Pixel). Das Histogramm beschreibt den
  **Modellzustand** der aktiven COLOR-Ebene (Eingangsdaten), nicht die
  laufende Vorschau.
- **Speicher:** gezählt wird über Views (`np.bincount` je Kanal); es
  entsteht keine zusätzliche RGBA-Vollkopie allein zur Zählung
  (#693/#696-Kriterium).

### 6. Levels-/Gamma-Formel und Pipeline-Reihenfolge

- **Parameter:** frozen Dataclass `ColorToneParams` mit
  `grayscale: str | None` (Preset-ID), `brightness/contrast/saturation:
  float` (Neutral 1.0), `black: int`, `white: int` (Neutral 0/255),
  `gamma: float` (Neutral 1.0). Validierung vollständig in
  `__post_init__`, **vor** jeder Pixelberechnung: Faktoren endlich und
  `≥ 0`; `0 ≤ black < white ≤ 255` (Schwarz == Weiß abgewiesen wie in
  `height_ops.levels` – kein Stufen-Sonderfall); `gamma` endlich und
  `> 0` (NaN/Inf **abgewiesen** – bewusst strenger als die dokumentierte
  `height_ops.gamma`-Lücke); unbekannte Preset-IDs abgewiesen. Fehler:
  `ColorOpsError` mit Ist/Soll-Meldung.
- **Levels-Formel (bindend, je RGB-Kanal, Alpha unberührt):**
  `out = clip(rint(255 · gamma_norm(levels_norm(x, black, white), 1/γ)), 0, 255)`
  – ausgeschrieben: `out = clip(rint(255 · clip((x − black) / (white − black), 0, 1)^(1/γ)), 0, 255)`.
  Zwischenrechnung float64; genau **eine** Rundung am Ende
  (`np.rint`, round-half-to-even), Finalisierungsfolge `rint → clip →
  astype(uint8)` identisch zum `_with_values`-Muster. `black` bildet auf
  0 ab, `white` auf 255, Werte außerhalb werden geclippt.
- **Gamma-Richtung:** Der UI-/Vertragswert γ folgt der
  Photoshop-/GIMP-Konvention: `γ > 1` **hellt Mitteltöne auf** (Exponent
  `1/γ`), `γ = 1.0` ist Identität. Das ist die **bewusst andere
  Richtung** als `height_ops.gamma` (direkter Exponent, `> 1` senkt) –
  beide Konventionen bleiben je Domäne erhalten und sind an beiden
  Stellen zu dokumentieren; der geteilte Kern `gamma_norm` nimmt den
  rohen Exponenten und ist konventionsfrei.
- **Reihenfolge der kombinierten Pipeline (bindend):**
  1. Graustufe (falls `grayscale` gesetzt),
  2. Helligkeit,
  3. Kontrast,
  4. Sättigung (Stufen 2–4 sind exakt die bestehende Pillow-Kette aus
     `adjust_color`, inklusive ihrer Überspring-Regel je Neutralfaktor),
  5. Levels/Gamma (als letzte Stufe, damit Schwarz-/Weißpunkt exakt im
     Endergebnis stehen).
  Begründung der Graustufe zuerst: Sie definiert das Tonwertmaterial und
  macht die Sättigung nachweislich exakt wirkungslos (die Luminanz eines
  Graupixels ist er selbst – Festkomma-Summe 65536), statt subtil
  doppeldeutig; die UI darf Sättigung im Graustufen-Modus deaktivieren
  (#694).
- **Skalenfestes Kontrast-Degenerat (bindend):** `ImageEnhance.Contrast`
  bildet sein Degenerat aus dem globalen Bildmittelwert des übergebenen
  Bildes (`int(mean_L + 0.5)`, konstantes Grau) – als einzige Stufe der
  Kette ist sie damit von einer globalen Bildstatistik abhängig, und der
  Mittelwert eines verkleinerten Proxys ist im Allgemeinen ein anderer
  Integer als der des Vollbilds (empirisch belegt: bimodales Testbild,
  Δ = 1 bereits bei 4:1-Verkleinerung). Deshalb wird das Degenerat
  **immer am Vollbild-Zwischenbild** (der Vollauflösungs-Eingabe der
  Kontraststufe, also nach Graustufe/Helligkeit) bestimmt und als
  expliziter Parameter in die Stufe gereicht; eine Proxy-Vorschau
  blendet gegen denselben Wert. Auf dem Vollbild ist das bitidentisch zu
  `ImageEnhance.Contrast` (gleicher Mittelwert, gleiche Blend-Formel) –
  die Paritätsgarantie unten bleibt unberührt. Erst damit ist die
  Pipeline skaleninvariant und die Proxy-Abgrenzung in Abschnitt 10
  („Differenzen nur durch Anzeigeverkleinerung") tatsächlich haltbar –
  ohne diese Regel wäre eine Kontrast-Vorschau auf dem Proxy eine
  **globale Tonwertverschiebung** (`out = mean + f·(x − mean)`: ein
  Mittelwert-Δ von 1 verschiebt bei f = 2.0 flächendeckend um ~1
  Tonwert), kein lokales Resampling-Artefakt.
- **Paritätsgarantie (bindend, getestet):** Mit `grayscale=None` und
  neutralen Levels (`0/255/1.0`) ist das Pipeline-Ergebnis **bitidentisch**
  zu `adjust_color(img, brightness=…, contrast=…, saturation=…)` – die
  Stufen 2–4 sind wörtlich dieselben Pillow-Aufrufe in derselben
  Reihenfolge (inklusive der uint8-Quantisierung je Stufe, die damit
  ausdrücklich Vertragsbestandteil bleibt).
- **Identität/No-op:** Vollständig neutrale Parameter
  (`grayscale=None`, Faktoren 1.0, Levels 0/255/1.0) geben bei einer
  bereits `RGBA`-modigen Eingabe **dasselbe Eingabeobjekt** zurück –
  der bestehende Same-Object-Vertrag von `adjust_color` wird insoweit
  auf die Pipeline ausgedehnt; für akzeptierte Nicht-RGBA-Eingaben
  liefert auch der Neutralfall das konvertierte `RGBA`-Ergebnis
  (Ausgaberegel aus Abschnitt 1, O(1)-Modusprüfung vor dem Shortcut).
  `ColorToneParams` bietet dafür `is_neutral` als O(1)-Prüfung.

### 7. Wertebereiche: Core-API vs. UI

| Parameter | Core-Domäne (Engine validiert) | UI-Bereich (nur Reglergrenze) |
|---|---|---|
| brightness/contrast/saturation | endliche floats `≥ 0` | Slider 0..200 % → 0.00..2.00 |
| black, white | ints, `0 ≤ black < white ≤ 255` | Spinner/Slider 0..255, UI verhindert `black ≥ white` (#694) |
| gamma | endlicher float `> 0` | z. B. 0,10..10,00 (Festlegung in #694) |
| grayscale | registrierte Preset-ID oder `None` | Schalter/Auswahl |

Die Core-API ist bewusst **nicht** an Reglergrenzen gekoppelt: Werte wie
`brightness=3.0` sind gültige Engine-Eingaben (Pillow extrapoliert
definiert); die UI-Grenzen sind reine Bedienentscheidungen und dürfen
sich ohne Core-Änderung verschieben.

### 8. Auswahlsemantik (mathematisch)

- **Maskenvertrag:** `mask` ist ein `uint8`-Array `(H, W)` in exakt der
  Bildgröße; `0` = nicht ausgewählt, `255` = voll ausgewählt,
  Zwischenwerte = weiche Kante. Form- oder Dtype-Mismatch wird mit
  `ColorOpsError` abgewiesen (kein stilles Broadcasting – Muster
  `height_map._validate_mask`).
- **Mischformel (bindend, je RGB-Kanal):**
  `out = rint((m / 255) · bearbeitet + (1 − m / 255) · original)`
  in float64; `out_A = original_A` (Alpha immer bitgenau vom Original).
  Garantien: `m == 0` → Pixel **bitgenau** unverändert; `m == 255` →
  Pixel erhält **bitgenau** das volle Engine-Ergebnis (beide Fälle sind
  in float64 exakt, nicht nur toleranznah); Zwischenwerte → gewichtete
  Mischung mit genau einer Rundung. Referenztests bei 64/128/192 (#695).
- **Arbeitsteilung und Einstiegspunkt:** Die Engine-Operationen selbst
  bleiben maskenfrei (ganzes Bild); die Mischung ist ein geteilter
  Compositor `blend_by_mask(original, bearbeitet, mask)` in `color_ops`.
  Vorschau und Commit rufen beide den **einen** Einstiegspunkt
  `apply_color_pipeline(image, params, mask=None, cancel=None)`: Er
  validiert zuerst **alle** Eingaben (Bildmodus, Maskenform/-dtype;
  `params` sind per DTO bereits validiert) und komponiert erst danach
  intern Pipeline und Mischung – die Maskenvalidierung läuft damit
  garantiert **vor** der ersten Pixelberechnung (Abschnitt 9);
  `blend_by_mask` prüft als eigenständige Funktion defensiv erneut.
  `cancel` ist ein optionales **kooperatives Abbruch-Token**
  (`Callable[[], bool]`, Muster `build_relief_mesh`) mit Prüfpunkten
  mindestens zwischen den Stufen und vor der Mischung; Abbruch wirft
  `ColorOpCancelled` (kein Teilresultat) – so bricht ein überholter
  40-MP-Vorschau-Job vor dem Ende ab, statt Speicher und Latenz zu
  binden (Abschnitt 10).
- **Anbindung der heutigen Bool-Auswahl:** `CanvasSelection` bleibt im
  MVP binär; die Canvas-Grenze bildet `True/False` auf `255/0` ab. Damit
  treten heute nur die bitgenauen Randfälle auf; der Vertrag für weiche
  Kanten steht bereit, sobald eine künftige Auswahl Zwischenwerte
  liefert.
- **Leere Auswahl** (`has_selection == False`) → `mask=None` → Wirkung
  auf die gesamte aktive COLOR-Ebene – konsistent mit
  `feather_active_edges` und den Höhen-Edits (#695: „Ohne aktive Auswahl
  wirkt die Operation auf die gesamte Ziel-COLOR-Ebene"); der
  Abbruch-Pfad von `apply_remove/apply_replace` wird **nicht** übernommen.
- **Vollständig transparente Pixel:** Ihre RGB-Werte werden wie alle
  anderen verarbeitet (keine Alpha-Sonderbehandlung in Pipeline und
  Mischung – deterministisch, konsistent mit `adjust_color` heute und
  robust gegen späteres Anheben des Alphas z. B. durch Feather). Nur das
  **Histogramm** schließt `A == 0` aus (Abschnitt 5) – dieser bewusste
  Unterschied zwischen Bearbeitung und Statistik ist Vertragsbestandteil.

### 9. Mutabilität, Ownership, Fehlerverhalten

- Keine Engine-Funktion mutiert Eingaben (Bild, Maske, Parameter);
  Rückgaben sind neue Objekte im Besitz des Aufrufers. Einzige Ausnahme:
  der dokumentierte Same-Object-No-op (Abschnitt 6). Histogramm-Arrays
  sind write-locked; `ColorToneParams` ist frozen.
- Die Engine hält keinen globalen Zustand und keine Referenzen auf
  übergebene Bilder über den Aufruf hinaus.
- **Fehler vor der Berechnung:** Der Einstiegspunkt
  `apply_color_pipeline` (Abschnitt 8) führt alle Validierungen
  (Parameter, Modus, Maskenform) aus, bevor Pixel angefasst werden; ein
  Fehler hinterlässt weder Teilresultat noch veränderten Projektzustand
  (Funktionen sind rein; der Commit-Pfad mutiert erst nach erfolgreicher
  Berechnung – Reihenfolge `push → mutate` wie heute in `_apply_pil`).
- Fehlerklasse: `ColorOpsError(ValueError)` in `color_ops` (Muster
  `HeightMapError`/`GlossPreviewError`); übersetzte Nutzertexte entstehen
  an der UI-Grenze (i18n-Keys, #694/#695), nicht im Core.
- **Härtung des Commit-Pfads:** `apply_color_op`/der neue Commit-Pfad
  fängt `ColorOpsError` und meldet ihn als Statusmeldung bei verworfener
  Vorschau und unverändertem Modell – Angleichung an das bestehende
  `apply_height_op`-Muster (`canvas.py:1456-1462`); heute propagiert eine
  Exception aus `op` ungefangen. Beabsichtigte, hier begründete
  Verhaltensänderung.
- **Fehlervertrag der Vorschau:** Ein Engine-Fehler während einer
  Vorschau-Berechnung verwirft die Vorschau, lässt Modell, History und
  Dirty-State unberührt und wird verständlich angezeigt (#694) – kein
  stilles Verschlucken wie heute in `preview_height_op`. Da
  `ColorToneParams` bereits an der UI-Grenze validiert, ist das der
  Ausnahme-, nicht der Reglerbetriebsfall.

### 10. Vorschau-/Commit-Semantik und Nebenläufigkeit

- **Eine fachliche Pipeline:** Vorschau und Commit rufen exakt dieselbe
  reine Funktionskette mit demselben `ColorToneParams`-Objekt (und
  derselben Maske). Es gibt keine zweite „Vorschau-Mathematik".
- **Downsampling ist reine Anzeigeoptimierung:** Die Vorschau darf auf
  einem verkleinerten Proxy rechnen (Proxy-Grenze legt #694 fest); der
  Commit rechnet **immer** in voller Auflösung aus dem aktuellen
  Modellzustand mit Originalbild und Originalmaske. „Dieselbe Maske"
  meint denselben Modell-Auswahlzustand: Auf dem Proxy werden Bild
  **und** Maske mit demselben benannten, deterministischen Verfahren
  skaliert (Filterwahl in #694); diese Maskenskalierung zählt
  ausdrücklich zur Anzeigeoptimierung. Die Kontraststufe blendet auch
  auf dem Proxy gegen das am Vollbild bestimmte Degenerat (Abschnitt 6)
  – der einzige von einer globalen Bildstatistik abhängige Parameter der
  Kette ist damit skalenfest. Erst dadurch gilt: Sichtbare Differenzen
  zwischen Vorschau und Ergebnis sind ausschließlich durch diese
  Anzeigeverkleinerung erklärbar (lokale Resampling-Effekte, keine
  globale Tonwertverschiebung) und werden in #696 mit dokumentierter
  Toleranz abgenommen. Die bitgenauen `m == 0`/`m == 255`-Garantien aus
  Abschnitt 8 gelten für den Commit-Pfad und jede
  Vollauflösungs-Vorschau; auf dem Proxy-Pfad gelten sie in
  Proxy-Auflösung vor der Rückskalierung – die angezeigten Pixel sind
  dort ausdrücklich Anzeige-Näherung.
- **Anzeigemechanik:** unverändert der transiente Layer-Override
  (#397/`swap_display_view`): kein Schreibpfad ins Modell, Verwerfen bei
  jedem Zustandswechsel (`_set_image_state`), `content_revision` bleibt
  unberührt → eine nicht committete Vorschau macht das Projekt **nie**
  dirty und wird **nie** persistiert. Der Override enthält **immer ein
  Bild in Ebenengröße**: Ein Proxy-Ergebnis wird vor dem Einsetzen
  deterministisch auf die Ebenengröße zurückskaliert (benannter Filter,
  dieselbe Festlegung wie die Hinskalierung, #694) – `swap_display_view`
  änderte sonst die gemeldete Ebenengröße (`Layer.size` ist die Größe
  der gehaltenen Ansicht), und Komposit (`alpha_composite`) wie
  Auswahl-Overlay liefen gegen ein größenfremdes Bild. Hin- und
  Rückskalierung samt zusätzlicher Rundung zählen zur
  Anzeigeoptimierung.
- **Expliziter Verwerfen-Vertrag:** Wird eine aktive COLOR-Vorschau
  unbedienbar (Verlassen des Schritts „Anpassen" in *jeden* anderen
  Schritt, Wechsel Experten→Standard-Modus, Ebenen-/Projektwechsel),
  verwirft die UI sie **explizit über `cancel_color_preview()`** und
  stellt die zugehörigen Regler neutral – nie über den Nebeneffekt, dass
  `cancel_height_preview()` dasselbe Override-Feld leert (Befund der
  #694-Nachprüfung; der heutige Direktsprung „Anpassen" → „Relief &
  Ebenen" lässt eine Farb-Vorschau stehen).
- **Nebenläufigkeit (Muster `Preview3DController`):** Die
  Vorschau-Berechnung läuft entprellt (200 ms, wie ADR #591) und
  asynchron über den `WorkerController` (Superseding-Muster
  `start_mesh_build`: laufender Job wird kooperativ abgebrochen, Handles
  identitätsgeprüft aufgeräumt, `shutdown_all` deckt den
  Fenster-Lebenszyklus). Jede Berechnung trägt eine **monotone
  Generation**, die bei jedem Parameterwechsel **und bei jedem
  expliziten Verwerfen** (`cancel_color_preview()` – auch aus Schritt-/
  Modus-/Ebenen-/Projektwechsel) erhöht wird; Verwerfen bricht den
  laufenden Job zusätzlich kooperativ ab und deaktiviert den Controller
  (Aktiv-Flag, Muster `Preview3DController._active`). Zu den beim Start
  erfassten Bezügen gehören `content_revision`, Ebenen-ID **und eine
  neue monotone Auswahl-Revision** an `CanvasSelection` (jede
  Maskenmutation – set/add/subtract/invert/clear/Pinsel – erhöht sie;
  nötig, weil Auswahländerungen die `content_revision` nachweislich
  nicht erhöhen, und als Zähler statt Masken-Identität, weil
  `CanvasSelection` das Backing-Array in-place mutiert und der
  `mask`-Getter je Zugriff eine frische View liefert – ein
  Identitätsvergleich wäre in beide Richtungen unzuverlässig). Ein
  Ergebnis wird
  **nur** angezeigt, wenn das Aktiv-Flag gesetzt ist und Generation und
  alle erfassten Bezüge noch aktuell sind – eine ältere
  Berechnungsgeneration kann einen neueren UI-Zustand nie überschreiben;
  verspätete Ergebnisse werden verworfen, nie gecacht. Die bestehenden
  B/C/S-Slider migrieren in #694
  auf denselben Mechanismus (heute rechnet jedes `valueChanged` synchron
  im UI-Thread – dokumentierter Ist-Mangel).
- **Commit:** „Anwenden" berechnet deterministisch und synchron aus dem
  aktuellen Modellzustand mit dem neuesten Parametersatz (wie heute –
  das sichtbare Vorschaubild wird nie übernommen, ein älteres Ergebnis
  kann nicht committet werden) und erzeugt **genau einen** Undo-Schritt
  (`ProjectHistory.push` des Vor-Zustands, unabhängig von der Zahl der
  Vorschauen). Latenzbudgets: #696 (16 MP ≤ 3 s, 40 MP ≤ 8 s).
- **No-op-Commit:** Ist `params.is_neutral` (und keine Maske macht das
  Ergebnis dennoch partiell – bei neutralen Parametern ist es das nie),
  wird **kein** History-Eintrag erzeugt und das Projekt nicht dirty
  (#695-Kriterium; O(1)-Parameterprüfung statt teurem Pixelvergleich).
  Wertgleiche Ergebnisse aus *nicht* neutralen Parametern erzeugen
  weiterhin einen Undo-Schritt – ein 40-MP-Pixelvergleich je Commit wäre
  unverhältnismäßig; das ist die dokumentierte, bewusste Grenze der
  No-op-Erkennung und eine begründete Abweichung vom heutigen Verhalten
  (heute pusht auch der Neutral-Commit).
- Undo/Redo, History-Budget (Payload-Referenzen, Dedup-Pool, 256 MiB)
  und Dirty-Mechanik (`content_revision`) bleiben unverändert.

### 11. Stabiler Adapter für spätere Laser-Consumer

- Qt-freie Funktion in `color_ops` (Arbeitstitel
  `render_luminance_map(image, params, preset_id)`), die aus einem
  RGBA-Bild plus explizitem `ColorToneParams` und Preset die normierte
  Luminanzrepräsentation erzeugt: frozen DTO `LuminanceMap` mit
  `values: uint8 (H, W)` (Grauwerte nach Pipeline + Preset, write-locked),
  `alpha: uint8 (H, W)` (Deckung, bitgenau aus dem Quellbild),
  `size: (Breite, Höhe)`, `value_range = (0, 255)`, `preset_id` und dem
  Parameter-Echo als Transformationsprovenienz.
- **Preset↔Parameter-Regel (deterministisch):** `preset_id` ist kein
  zweiter Graustufenpfad, sondern **setzt** das `grayscale`-Feld der
  angewandten Parameter: Der Adapter ruft exakt
  `apply_color_pipeline(image, params_mit_grayscale=preset_id)` auf –
  es gilt die Stufenreihenfolge aus Abschnitt 6 (Graustufe zuerst), die
  Graustufe läuft genau einmal. Ein bereits gesetztes, **abweichendes**
  `params.grayscale` wird mit `ColorOpsError` abgewiesen (gleicher Wert
  ist erlaubt). Da alle Folgestufen `R = G = B` erhalten (Sättigung ist
  auf Grau exakt wirkungslos, Abschnitt 6; Helligkeit/Kontrast/Levels
  wirken kanalgleich), ist der Graukanal des Pipeline-Ergebnisses
  wohldefiniert – der Contract-Test hat genau ein erwartetes Ergebnis.
- **Bindend:** Der Adapter ruft ausschließlich die Primitiven dieses
  Vertrags auf – ein Contract-Test (#696) belegt, dass UI-Pipeline und
  Adapter für identische Eingaben identische Core-Ergebnisse erhalten.
- **Ausgeschlossen:** Der Adapter enthält keinerlei Geräte-, DPI-,
  Raster-, Vorschub- oder G-Code-Logik und keine EufyMake-Kopplung;
  physische Maße bleiben bei den `units.py`-Konsumenten. Offene
  Laser-Entscheidungen (Rasterstrategie, Gerätebindung) bleiben
  ausdrücklich offen und sind hier nur als Andockpunkt beschrieben.

### 12. Beabsichtigte Verhaltensänderungen gegenüber heute (Sammelinventar)

Jede Abweichung vom Ist-Verhalten ist genau eine bewusste Entscheidung
dieses Vertrags; alles hier nicht Gelistete bleibt verhaltensgleich:

1. **Strenge Modus-Regel der neuen Engine-Funktionen** (Abschnitt 1):
   16-Bit-/Float-Modi werden abgewiesen statt still konvertiert;
   `adjust_color` selbst bleibt tolerant. Ebenfalls Teil dieser
   Abgrenzung: Der Same-Object-No-op der Pipeline gilt nur für
   `RGBA`-Eingaben (Abschnitte 1/6), während der
   `adjust_color`-Neutral-Guard vor der Konvertierung steht und heute
   auch ein `RGB`-Objekt unverändert zurückgibt.
2. **Parametervalidierung mit `ColorOpsError`** (Abschnitte 6/9): Die
   Pipeline weist ungültige Parameter vor jeder Berechnung ab, während
   `adjust_color` heute unvalidiert an Pillow durchreicht (definierte
   Extrapolation); `adjust_color` bleibt unverändert – die Validierung
   sitzt im `ColorToneParams`-DTO.
3. **Auswahl wirkt auf COLOR-Operationen** (Abschnitt 8) – die größte
   nutzersichtbare Änderung: Heute ignoriert der gesamte Farbpfad die
   Auswahl (Vollbild-Korrektur trotz aktiver Auswahl); künftig begrenzen
   Vorschau und Commit die Wirkung auf die Auswahl, auch für die
   bestehenden Helligkeits-/Kontrast-/Sättigungs-Regler nach ihrer
   Migration (#694/#695). Begründung: Epic-Produktprinzip „Alpha und
   nicht ausgewählte Pixel bleiben unverändert" – das heutige Verhalten
   ist daran gemessen eine Lücke, keine Zusicherung.
4. **Commit fängt Engine-Fehler** statt ungefangener Exceptions, und die
   Vorschau zeigt Engine-Fehler an statt sie still zu schlucken
   (Abschnitt 9).
5. **Neutral-Commit ist ein No-op** (Abschnitt 10): kein History-Eintrag,
   kein Dirty – heute erzeugt auch ein „Anwenden" mit Neutralwerten
   einen Undo-Schritt mit wertgleichen Pixeln.
6. **Expliziter Verwerfen-Vertrag inkl. Regler-Neutralstellung**
   (Abschnitt 10) statt des impliziten
   `cancel_height_preview`-Nebeneffekts mit Leck beim Direktsprung.
7. **Asynchrone, entprellte Vorschau mit Generationsschutz**
   (Abschnitt 10) statt synchroner Vollbild-Berechnung je
   `valueChanged`.

## Nicht-Ziele

- **Keine Implementierung** in diesem ADR – Code entsteht erst in
  #693–#695 gegen diesen Vertrag.
- **Keine 16-Bit-COLOR-Pipeline** im MVP (Abschnitt 1; die
  Layer-Invariante aus ADR #586 §7 bleibt).
- **Keine Kurvenbearbeitung**, kein Auto-Levels, keine Pipetten.
- **Kein ICC-/Farbmanagement**, kein Softproofing (Abschnitt 2).
- **Keine Laser-Rasterung/-Ausgabe** und keine Geräteansteuerung
  (Abschnitt 11 definiert nur den neutralen Adapter).
- **Keine finalen UI-Texte/-Layouts** – i18n-Keys und Bedienoberfläche
  sind Sache von #694.

## Konsequenzen und Abbildung auf die Folge-Issues

- **#693 – Qt-freier Kern:** setzt Abschnitte 1, 3–9 um
  (`tone_curve.py`-Kern + Delegation aus `height_ops` mit bitgenauem
  Regressionstest, `GRAYSCALE_PRESETS`, `compute_histogram`,
  `ColorToneParams`/`apply_color_pipeline` (inkl. Abbruch-Token/
  `ColorOpCancelled`), `blend_by_mask`, `ColorOpsError`,
  `saturation=0`-Paritätstest, Pillow-Wächtertest der
  Festkomma-Luminanz, `LUMA_WEIGHTS_REC601`-Import in `gloss_preview`).
- **#694 – Live-Vorschau/UI:** setzt Abschnitte 7 und 10 um (Debounce,
  Worker-Generationen, Proxy-Grenze, expliziter Verwerfen-Vertrag inkl.
  Schritt-/Moduswechsel und Regler-Neutralstellung, UI-Bereiche,
  Histogramm-Bezugs-Anzeige).
- **#695 – Integration:** setzt Abschnitte 8–10 um (Maskenmischung mit
  64/128/192-Referenztests, No-op-Commit ohne History-Eintrag, genau ein
  Undo-Schritt, monotone Auswahl-Revision an `CanvasSelection` für die
  Stale-Prüfung, Persistenz angewendeter Ergebnisse).
- **#696 – Abnahme:** misst die Budgets (Abschnitt 10), nimmt den
  Laser-Adapter-Contract-Test ab (Abschnitt 11) und dokumentiert die
  bekannten Grenzen (8 Bit, kodiertes sRGB, kein ICC).
- Reviewt und akzeptiert wird dieses ADR über den regulären PR-Prozess;
  die produktive Core-Implementierung (#693) beginnt erst danach.

## Offene Risiken

- **Pillow-Kopplung:** Festkomma-Luminanz und `ImageEnhance`-Semantik
  sind C-Interna der gepinnten Version (`pillow==12.3.0`, erlaubt
  `>=10,<13`). Der Paritätstest aus Abschnitt 3 ist der Wächter; ein
  Major-Update, das ihn bricht, erzwingt eine dokumentierte
  Vertragsrevision statt stiller Drift.
- **`height_ops`-Delegation:** Die Bitparität der Delegation auf
  `tone_curve` hängt an identischer float64-Operationsfolge; der
  Regressionstest in #693 muss gezielte Grenzmuster (black/white nahe
  beieinander, große `max_value`-Spreizung) pinnen, nicht nur
  Zufallsdaten.
- **Synchroner Ist-Zustand bis #694:** Bis die asynchrone Vorschau
  steht, bleibt jedes `valueChanged` ein synchroner Vollbild-Durchlauf –
  auf 40-MP-Bildern spürbar. Das ADR ändert daran nichts; die Reihenfolge
  der Teil-Issues (Core vor UI) nimmt das bewusst in Kauf.
- **Bool→uint8-Übergang der Auswahl:** Solange `CanvasSelection` binär
  ist, bleiben die weichen Misch-Pfade nur core-getestet (direkte
  uint8-Masken in #693/#695), nicht UI-erreichbar – ein späteres
  Weiche-Kanten-Feature muss den Vertrag nur noch anschließen, nicht neu
  verhandeln.
- **NaN-Lücke in `height_ops.gamma`:** bleibt bestehen (dokumentiert in
  der Ist-Analyse); eine Angleichung an die strengere COLOR-Validierung
  wäre eine eigene, kleine Folgeentscheidung außerhalb dieses Epics.
