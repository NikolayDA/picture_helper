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
| Vorschau | `preview_color_op(op)` (`canvas.py:1486-1500`) | **synchron im UI-Thread**: `op(active.image)` sofort, Ergebnis als transienter Layer-Override `(active.id, Bild)`; ohne aktive COLOR-Ebene stilles Überspringen; Modell/History/Dirty unberührt |
| Verwerfen | `cancel_color_preview()` (`canvas.py:1502-1507`), `_set_image_state()` (`canvas.py:858-865`) | Override wird bei jedem Bildzustandswechsel verworfen; expliziter Cancel hat genau **einen** Aufrufer („Zurücksetzen"-Button); beim Schrittwechsel verlässt sich der Farbpfad darauf, dass `cancel_height_preview()` dasselbe Feld leert – Direktsprung „Anpassen" → „Relief & Ebenen" lässt eine Farb-Vorschau stehen (Nachprüfung in #694) |
| Commit | `apply_color_op(op)` (`canvas.py:1510-1536`) | rechnet `op(active.image)` **neu** aus dem aktuellen Modellzustand (Vorschaubild wird nie übernommen), committet das **volle** Ebenenbild als genau einen Undo-Schritt über `_apply_pil` → `ProjectHistory.push` (Vor-Zustand, `history.desc.color_adjusted`); **kein** No-op-Check (auch wertgleiche Ergebnisse erzeugen einen Undo-Eintrag), **kein** Exception-Fang (anders als `apply_height_op`); die Auswahlmaske wird im gesamten Farbpfad **ignoriert** |
| UI | `AdjustTab` (`right_panel_tabs.py:755-810`) | drei Slider 0..200 (Neutral 100), Mapping `value/100.0` → Faktor 0.0..2.0; **kein Debounce** – jedes `valueChanged` rechnet synchron das volle Bild; „Zurücksetzen" stellt 100 her und ruft `cancel_color_preview()` |
| Dirty | `main_window.py:951-964` | kein Flag; `content_revision != _saved_revision`; die transiente Vorschau erhöht die Revision nie |

### Bestehende Tonwert-/Luminanz-Definitionen (Entscheid je Fundstelle nötig)

| Fundstelle | Definition heute |
|---|---|
| `height_ops.levels(field, black, white)` (`height_ops.py:40-53`) | `out = rint(clip((v − black) / (white − black), 0, 1) · max_value)`, float64-Zwischenrechnung; Validierung `0 ≤ black < white ≤ max_value` (Schwarz==Weiß abgewiesen, keine Division durch 0) |
| `height_ops.gamma(field, value)` (`height_ops.py:56-65`) | `out = rint((v / max_value)^value · max_value)`; `value ≤ 0` abgewiesen, **kein** `isfinite`-Check (NaN/Inf passieren die Prüfung); `value > 1` senkt Mitten |
| Finalisierung `_with_values` (`height_ops.py:31-34`) | einheitlich `np.clip(np.rint(x), 0, max_value).astype(np.uint16)` – `np.rint` = round-half-to-even |
| `height_map.generate_from_image(...)` (`height_map.py:408-469`) | float64-Luminanz `Σ w_c·c / Σw` mit `LUMA_WEIGHTS_REC601 = (0.299, 0.587, 0.114)` (`height_map.py:67`), dann `clip((luma − black)/(white − black), 0, 1)` (black/white immer im 8-Bit-Raum), optional `^gamma`, optional `1 − x`, `rint(norm · max_value)` → `uint16` |
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
  (Gewichte ÷65536 ≈ 0.29898/0.58700/0.11400, Summe exakt 65536; 0 Abweichungen).
- `ImageEnhance.Color(...).enhance(0.0)` liefert exakt `convert("L")` auf
  allen drei Kanälen (R=G=B) – `saturation=0` **ist** heute eine
  wohldefinierte Graustufenumwandlung.
- Gegen die float64-Referenz `rint(0.299·R + 0.587·G + 0.114·B)` weichen
  9 443 von 16 777 216 Werten (0,056 %) um genau ±1 ab; max |Δ| = 1.

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
  neuen Funktionen – das ist die einzige beabsichtigte Abweichung
  zwischen alt und neu und hier einzeln begründet: Ein 16-Bit-Graubild
  durch `convert("RGBA")` zu quetschen wäre stiller Präzisionsverlust,
  den #589 für Höhen bereits verbietet.
- Ausgaben sind immer `RGBA`; die Bildgröße bleibt exakt erhalten.

### 2. Farbraum und Transferfunktion

Das MVP arbeitet **im kodierten sRGB-Tonwert** (nicht linearisiert), ohne
Farbmanagement. Visuelle Folge: Tonwertoperationen wirken wie in den
Referenz-Editoren (Levels/Gamma auf kodierten Werten); Mischungen sind
photometrisch nicht exakt, was für die Zielworkflows (Anzeige,
Laser-Graustufen) irrelevant ist. Technische Folge: Bitparität mit allen
bestehenden Pfaden (`ImageEnhance`, `generate_from_image`,
`gloss_preview`), keine 2×-Konvertierung. Performance-Folge: keine
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
| `height_map.generate_from_image` | **Bleibt eigenständig, formelgleich in den Koeffizienten.** Die float64-Luminanz über `LUMA_WEIGHTS_REC601` dient der Höhenerzeugung (Skalierung auf `0..max_value`, eigene Kennlinie), nicht der Anzeige-Graustufe; sie delegiert im MVP nicht auf `tone_curve` (kein Umbau ohne Not am 16-Bit-Pfad). Die **bewusste Abweichung** zur COLOR-Graustufe (float64-`rint` vs. Pillow-Festkomma, ±1 in 0,056 % der Werte) wird im Docstring beider Seiten dokumentiert; ein Test pinnt die Koeffizienten beider Definitionen gegeneinander (gleiche nominelle Gewichte). |
| Luminanz-Literale in `gloss_preview._gloss_mask` | **Konsolidieren:** importiert künftig `LUMA_WEIGHTS_REC601` statt der Literale – bitgleich, weil die Werte identisch sind; die Begründung („eine Quelle der Wahrheit für Rec.-601-Gewichte") steht dann im Code. Kleinaufgabe in #693. Die dort beobachtete `I;16N`-Lücke des 16-Bit-Zweigs ist nicht Teil dieses Vertrags (separater Kleinbefund). |
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
  Welcher Bezug angezeigt wird, macht die UI sichtbar (#694).
- **Leere Menge:** leere Auswahl, vollständig transparentes Bild oder
  0 Pixel ergeben ein **Nullhistogramm** (alle Bins 0, `total == 0`) –
  definiertes Ergebnis, kein Fehler (#693 testet diesen Fall).
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
  2. Helligkeit, 3. Kontrast, 4. Sättigung
     (exakt die bestehende Pillow-Kette aus `adjust_color`, inklusive
     ihrer Überspring-Regel je Neutralfaktor),
  3. Levels/Gamma (als letzte Stufe, damit Schwarz-/Weißpunkt exakt im
     Endergebnis stehen).
  Begründung der Graustufe zuerst: Sie definiert das Tonwertmaterial und
  macht die Sättigung nachweislich exakt wirkungslos (die Luminanz eines
  Graupixels ist er selbst – Festkomma-Summe 65536), statt subtil
  doppeldeutig; die UI darf Sättigung im Graustufen-Modus deaktivieren
  (#694).
- **Paritätsgarantie (bindend, getestet):** Mit `grayscale=None` und
  neutralen Levels (`0/255/1.0`) ist das Pipeline-Ergebnis **bitidentisch**
  zu `adjust_color(img, brightness=…, contrast=…, saturation=…)` – die
  Stufen 2–4 sind wörtlich dieselben Pillow-Aufrufe in derselben
  Reihenfolge (inklusive der uint8-Quantisierung je Stufe, die damit
  ausdrücklich Vertragsbestandteil bleibt).
- **Identität/No-op:** Vollständig neutrale Parameter
  (`grayscale=None`, Faktoren 1.0, Levels 0/255/1.0) geben **dasselbe
  Eingabeobjekt** zurück – der bestehende Same-Object-Vertrag von
  `adjust_color` wird auf die Pipeline ausgedehnt. `ColorToneParams`
  bietet dafür `is_neutral` als O(1)-Prüfung.

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
- **Arbeitsteilung:** Die Engine-Operationen selbst bleiben maskenfrei
  (ganzes Bild); die Mischung ist ein geteilter Compositor
  `blend_by_mask(original, bearbeitet, mask)` in `color_ops`. Vorschau
  und Commit rufen damit dieselbe Kette
  `blend_by_mask(img, pipeline(img, params), mask)`.
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
- **Fehler vor der Berechnung:** Alle Validierungen (Parameter, Modus,
  Maskenform) laufen, bevor Pixel angefasst werden; ein Fehler
  hinterlässt weder Teilresultat noch veränderten Projektzustand
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

### 10. Vorschau-/Commit-Semantik und Nebenläufigkeit

- **Eine fachliche Pipeline:** Vorschau und Commit rufen exakt dieselbe
  reine Funktionskette mit demselben `ColorToneParams`-Objekt (und
  derselben Maske). Es gibt keine zweite „Vorschau-Mathematik".
- **Downsampling ist reine Anzeigeoptimierung:** Die Vorschau darf auf
  einem verkleinerten Proxy rechnen (Proxy-Grenze legt #694 fest); der
  Commit rechnet **immer** in voller Auflösung aus dem aktuellen
  Modellzustand. Sichtbare Differenzen zwischen Vorschau und Ergebnis
  sind ausschließlich durch diese Anzeigeverkleinerung erklärbar und
  werden in #696 mit dokumentierter Toleranz abgenommen.
- **Anzeigemechanik:** unverändert der transiente Layer-Override
  (#397/`swap_display_view`): kein Schreibpfad ins Modell, Verwerfen bei
  jedem Zustandswechsel (`_set_image_state`), `content_revision` bleibt
  unberührt → eine nicht committete Vorschau macht das Projekt **nie**
  dirty und wird **nie** persistiert.
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
  Generation**, die bereits beim Parameterwechsel erhöht wird, plus die
  beim Start erfasste `content_revision` und Ebenen-ID. Ein Ergebnis
  wird **nur** angezeigt, wenn Generation, `content_revision` und aktive
  Ebene noch aktuell sind – eine ältere Berechnungsgeneration kann einen
  neueren UI-Zustand nie überschreiben; verspätete Ergebnisse werden
  verworfen, nie gecacht. Die bestehenden B/C/S-Slider migrieren in #694
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
- **Bindend:** Der Adapter ruft ausschließlich die Primitiven dieses
  Vertrags auf – ein Contract-Test (#696) belegt, dass UI-Pipeline und
  Adapter für identische Eingaben identische Core-Ergebnisse erhalten.
- **Ausgeschlossen:** Der Adapter enthält keinerlei Geräte-, DPI-,
  Raster-, Vorschub- oder G-Code-Logik und keine EufyMake-Kopplung;
  physische Maße bleiben bei den `units.py`-Konsumenten. Offene
  Laser-Entscheidungen (Rasterstrategie, Gerätebindung) bleiben
  ausdrücklich offen und sind hier nur als Andockpunkt beschrieben.

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
  `ColorToneParams`/Pipeline, `blend_by_mask`, `ColorOpsError`,
  `saturation=0`-Paritätstest, Pillow-Wächtertest der
  Festkomma-Luminanz, `LUMA_WEIGHTS_REC601`-Import in `gloss_preview`).
- **#694 – Live-Vorschau/UI:** setzt Abschnitte 7 und 10 um (Debounce,
  Worker-Generationen, Proxy-Grenze, expliziter Verwerfen-Vertrag inkl.
  Schritt-/Moduswechsel und Regler-Neutralstellung, UI-Bereiche,
  Histogramm-Bezugs-Anzeige).
- **#695 – Integration:** setzt Abschnitte 8–10 um (Maskenmischung mit
  64/128/192-Referenztests, No-op-Commit ohne History-Eintrag, genau ein
  Undo-Schritt, Persistenz angewendeter Ergebnisse).
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
