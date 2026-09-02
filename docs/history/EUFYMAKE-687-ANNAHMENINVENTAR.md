# Annahmeninventar: EufyMake-Importträger und Exportvertrag (Issue #687)

Versionierte Evidenzgrundlage für Epic [#681](https://github.com/NikolayDA/picture_helper/issues/681)
(„EufyMake-Zielprofil – Height/Gloss/mm-DPI empirisch validieren und Exportvertrag
härten"), Deliverable von Issue
[#687](https://github.com/NikolayDA/picture_helper/issues/687) („Annahmeninventar,
Herstellerquellen und reproduzierbare Testmatrix"). Erfüllt das letzte
Akzeptanzkriterium des Issues: *„Neue Erkenntnisse können ohne Umbau der Struktur
als zusätzliche Evidenzversion eingetragen werden."*

Der Inhalt entstand als Schreibtischrecherche (kein Realtest, kein Drucker, kein
Studio) und ist der Referenztext hinter dem
[Recherchekommentar in #687](https://github.com/NikolayDA/picture_helper/issues/687#issuecomment-5302447026)
sowie dem [Kommentar in #681](https://github.com/NikolayDA/picture_helper/issues/681#issuecomment-5302452354).
Dieses Dokument ist die dauerhafte, versionierbare Ablage; die Issue-Kommentare
bleiben der punktuelle Nachweis zum Recherchedatum.

## Wie eine neue Evidenzversion ergänzt wird

1. **Nicht überschreiben.** Frühere „Evidenzversion N"-Abschnitte bleiben
   unverändert stehen – auch wenn eine spätere Version sie widerlegt.
2. Eine neue Version hängt als eigener `## Evidenzversion N (Datum)`-Abschnitt an
   das Ende an, mit derselben Gliederung (Methodik → Entscheidungspunkte →
   Quellen → Annahmeninventar → offene Punkte → Testmatrix → Konsequenzen).
3. Wird eine frühere Annahme durch einen Realtest (Grad **T**) bestätigt oder
   widerlegt, bekommt ihre Zeile in der **neuen** Version eine aktualisierte
   Status-Spalte mit Verweis auf die neue Evidenzversion; die alte Zeile bleibt
   in ihrer ursprünglichen Version unverändert (Nachvollziehbarkeit).
4. Neue Quellen bekommen fortlaufende IDs **innerhalb ihrer Version**
   (`A16`, `B9`, `C5`, … in Version 2 usw.), damit bestehende Verweise aus Issues,
   Commits und PRs stabil bleiben.

---

## Evidenzversion 1 (2026-08-15)

### 0. Methodik und ihre Grenzen

| Aspekt | Stand |
| --- | --- |
| Herstellerseiten direkt abrufbar? | **Nein.** `support.eufymake.com`, `wiki.eufymake.com`, `www.eufymake.com` waren in der Recherchesession durch die Egress-Policy des Agenten gesperrt (403 am Proxy), ebenso Reddit/Facebook/YouTube. |
| Woher kommen die Herstelleraussagen dann? | Aus der Websuche, die den Seiteninhalt extrahiert. Die Herstellerseiten wurden **nicht** im Volltext gelesen. |
| Was wurde im Original gelesen? | Der Quellcode der Community-Bibliothek `empf-generator` (über `raw.githubusercontent.com`, erreichbar). |
| Realtest / Hardware? | **Keiner.** Kein Drucker, kein Studio, kein Druck. |

Evidenzgrade, verwendet in allen Tabellen dieses Dokuments:

- **P** – Primärquelle im Volltext gelesen.
- **S** – Herstellertext, nur über Suchmaschinen-Extraktion; Formulierungen können
  gekürzt/paraphrasiert sein. Vor einem harten Vertrag am Original zu verifizieren.
- **E** – eigene Ableitung/Rechnung aus P- oder S-Material.
- **T** – Realtest. In Version 1 nirgends vergeben.

Kein Punkt in Version 1 ist mit **T** belegt. Version 1 ist damit die
Evidenzgrundlage, auf der #688–#690 ihre Realtests aufsetzen, nicht deren Ersatz.

### 1. Erster Entscheidungspunkt: Welchen Träger importiert EufyMake Studio?

Drei zuvor vermischte Ebenen:

**(a) Gestaltungsinhalte importiert Studio als Einzeldateien.**
Unterstützt: `PNG`, `JPEG`, `WEBP`, `SVG`, `AI`, `PSD`, `PDF`; nicht-rasterbasierte
Formate werden beim Upload rasterisiert und verflacht (A1, A7, A8 – Grad S). Kein
Hinweis auf einen Paket-, Ordner- oder Manifest-Import.

**(b) Die Höhenkarte ist eine separate Graustufendatei am Bildobjekt.**
Der Hersteller nennt `PNG` **oder** `TIFF` und empfiehlt „16-bit/channel during
export if the option is available" (A2, A3 – Grad S).

**(c) Das native Projektformat `.empf` ist ein ZIP, aber ohne separate Bilddateien.**
Aus dem Quellcode von `empf-generator` v1.1.0 (B1 – Grad **P**):

```text
.empf (ZIP)
├── Metadata/project_info.json          # Projekt-/Canvas-Metadaten, print_param
├── Asset/project_file/canvas_<id>.json # Canvas: Fabric.js-Serialisierung, version "5.3.0"
└── Asset/font/font_mapping.json
```

Bilder liegen base64-kodiert als Data-URI im Canvas-JSON
(`src: "data:image/png;base64,…"`), nicht als eigene Dateien.

**Konsequenz für BgRemover:** Der heutige Exportordner
(`color_motif.png`/`height_map.png`/`gloss_mask.png` + `manifest.json`) ist der
richtige Träger. Kein Container-Migrations-Arbeitspaket nötig. TIFF war nie ein
Container-Kandidat, sondern ein zulässiges Höhen-*Dateiformat* neben PNG.
Widerlegt: `manifest.json` wird von Studio ausgewertet – es ist reine
BgRemover-Innendokumentation.

### 2. Quellen-/Evidenzverzeichnis

#### A – Direkte Herstellerquellen (eufyMake/Anker), alle Grad S, Abrufdatum 2026-08-15

| ID | Titel | URL | Stand |
| --- | --- | --- | --- |
| A1 | eufyMake UV Printer E1 Supported file import types and sizes | https://support.eufymake.com/s/article/eufyMake-UV-Printer-E1-Supported-file-import-types-and-sizes | o. A. |
| A2 | Custom 3D Texture Tutorial | https://support.eufymake.com/s/article/Custom-3D-Texture-Tutorial | o. A. |
| A3 | Depth Maps Explained for UV Printing & 3D Relief | https://www.eufymake.com/blogs/printing-guides/how-to-custom-3d-texture-depth-map | o. A. |
| A4 | Guide to Process Design Parameter Settings | https://support.eufymake.com/s/article/Guide-to-Process-Design-Parameter-Settings | o. A. |
| A5 | eufyMake July Release: Height Maps Editing, 130mm Print Height | https://www.eufymake.com/blogs/news/eufymake-july-release | Studio 4.0 / Editor V17, Juli 2026 |
| A6 | Editor V17 (Wiki) | https://wiki.eufymake.com/en/Editor-v17 | Editor V17 |
| A7 | Contents Upload and Edit (Wiki) | https://wiki.eufymake.com/en/software/editing | o. A. |
| A8 | Software FAQ: Parameter Settings & File Import Tips (Wiki) | https://wiki.eufymake.com/en/FAQ/SoftwareSettings-File-Import-Tips | o. A. |
| A9 | Software Release Notes (Wiki) | https://wiki.eufymake.com/en/software/update · https://wiki.eufymake.com/en/software/update/software3-7-1 | 3.7.1 u. a. |
| A10 | What is the maximum printable size (width/depth/height) | https://support.eufymake.com/s/article/What-is-the-maximum-printable-size-width-depth-height | o. A. |
| A11 | Spot UV Printing: Benefits, Uses, & How to Apply It | https://www.eufymake.com/blogs/printing-guides/what-is-spot-uv-printing | o. A. |
| A12 | How to correctly set White Underbase Choke | https://support.eufymake.com/s/article/eufyMake-UV-Printer-E1-How-to-correctly-set-White-Underbase-Choke | o. A. |
| A13 | eufyMake Studio Apr 8 Release: Contour Recognition, Local Mode | https://www.eufymake.com/blogs/news/eufymake-studio-v371-contour-recognition-local-mode | 3.7.1, April 2026 |
| A14 | Is PNG or JPG Higher Quality for Printing? | https://www.eufymake.com/blogs/printing-guides/is-png-or-jpg-higher-quality | o. A. |
| A15 | Produktseite eufyMake E1 | https://www.eufymake.com/products/eufymake-e1 | o. A. |

#### B – Community-/Sekundärquellen (keine Herstelleraussagen)

| ID | Quelle | URL | Grad | Hinweis |
| --- | --- | --- | --- | --- |
| B1 | `empf-generator` v1.1.0, Vietbao Tran (TapuCosmo), LGPL-3.0-or-later | https://github.com/TapuCosmo/empf-generator | **P** | Reverse Engineering von `.empf`; Quellcode im Original gelesen |
| B2 | Issue #1 „Not working properly with the eufyMake Studio 2.6.0.2" (März 2026) | https://github.com/TapuCosmo/empf-generator/issues/1 | S | Datei lädt „silently … but has no visible PNG image" |
| B3 | Bitner Built – eufyMake E1 Depth Maps | https://www.bitnerbuilt.com/resources/blog-post-title-four-fen8y | S | ZBrush-Workflow, 2048×2048 |
| B4 | FB-Gruppe „eufyMake UV Printer E1 USA", Custom-Depth-Map-Beitrag | https://www.facebook.com/groups/eufymakeuvprintere1usa/posts/2110593256455974/ | S | nur Titel/Snippet |
| B5 | YouTube „How to Use eufyMake's New Depth Map Feature \| 3 Texture Modes Compared" (30.06.2026) | https://www.youtube.com/watch?v=kN4x9vYGfWk | S | nur Metadaten, Inhalt nicht gesichtet |
| B6 | Swing Design (Händler) | https://www.swingdesign.com/pages/eufymake-e1-3d-texture-uv-printer-direct-to-film-texture-printing-solutions-swing-design | S | „maximum Relief Texture setting is 5 millimeters" |
| B7 | EMPF Preview (Drittanbieter-Viewer für `.empf`) | https://empfpreview.com/ | S | nur Existenz belegt; spätere Prüfhilfe |
| B8 | The Country Chic Cottage – E1-Guide | https://www.thecountrychiccottage.net/eufymake-e1-uv-printer/ | S | Ink-Mode-/Gloss-Praxis |

**Lizenzhinweis zu B1:** LGPL-3.0-or-later ist mit BgRemovers GPL-3.0-or-later
vereinbar. Genutzt wird hier ausschließlich das Struktur-Wissen, kein Code wurde
übernommen. Bei künftiger Codeübernahme: Lizenz-/Urheberhinweis mitführen und in
`LICENSES.md` aufnehmen.

#### C – Eigene Beobachtungen und Ableitungen

| ID | Aussage | Grad |
| --- | --- | --- |
| C1 | Code-Fundstellen im Repo (Abschnitt „Annahmeninventar") | P |
| C2 | Interne E1-Einheit = 1/50 Zoll: `mmToE1Units(mm) = mm × 1.9685`, 1,9685 × 25,4 = 50,0 Einheiten/Zoll | E aus B1 |
| C3 | `standardFlatbed` = 656 × 823 Einheiten ≈ 333,2 × 418,1 mm; `miniFlatbed` = 656 × 173 ≈ 333,2 × 87,9 mm. Deckt sich mit A10/A15 („13 × 16.5 in", 330 × 420 mm) – zwei unabhängige Quellen, ähnliches Ergebnis | E aus B1 |
| C4 | `rotary` und `rollToFilm` sind in B1 als „not currently supported" auskommentiert vorhanden | P |

### 3. Annahmeninventar

Status: **bestätigt** · **widerlegt** · **teilbestätigt** · **offen**. Fundstellen
auf dem Stand von `main` zum Recherchezeitpunkt (`7ae464c`); Codeänderungen aus
dieser Version werden am Ende jeder Zeile mit „→ umgesetzt" vermerkt.

#### Träger und Paketstruktur

| ID | Annahme | Fundstelle | Evidenz | Status |
| --- | --- | --- | --- | --- |
| EM-C01 | Studio wertet ein Asset-Paket samt `manifest.json` aus | `eufymake_writer.py` | A1, A7, A8 (S) | **widerlegt** |
| EM-C02 | Kein natives `.empf` erzeugen (`OpenQuestion.NATIVE_EMPF_PROJECT`) | `eufymake_export.py` | B1 (P), B2 (S) | **bestätigt** |
| EM-C03 | TIFF ist der Zielcontainer (Alt-Formulierung des Issues) | – (nie im Code) | A2 (S) | **widerlegt** – TIFF ist Höhen-Dateiformat, kein Container |
| EM-C04 | Ordner *oder* ZIP als Paketrepräsentation (ADR-Punkt 1) | `ADR-2026-eufymake-exportpaket.md` | A1 (S) | **offen** – ZIP-Variante ohne Nutzen, solange Studio Einzeldateien nimmt |

#### Dateirollen

| ID | Annahme | Fundstelle | Evidenz | Status |
| --- | --- | --- | --- | --- |
| EM-R01 | Farbmotiv = RGBA-PNG | `eufymake_export.py`, `eufymake_writer.py` | A1, A7 (S) | **bestätigt** |
| EM-R02 | Höhenkarte = Graustufen-PNG am Bildobjekt | `eufymake_export.py` | A2, A3 (S) | **bestätigt** |
| EM-R03 | Gloss = Graustufen-Intensitätsmaske als Asset-Rolle | `eufymake_export.py` | A11 (S), B1 (P) | **teilbestätigt** – siehe unten |
| EM-R04 | Alpha/Coverage steuert die Weiß-Unterlage | `project_model.py`, `image_ops.feather_alpha` | A12, A8 (S) | **teilbestätigt** |

Zu **EM-R03**: Gloss existiert in zwei Gestalten. (1) Als Ink-Mode am
Canvas-Objekt: `subPrintModel` aus `white_cmyk=0, cmyk=1, gloss=2, white=3,
cmyk_white=4, cmyk_white_cmyk=5, cmyk_gloss=6, white_cmyk_gloss=7, sticker=111`,
dazu `whiteLayerNum`/`colorLayerNum`/`varnishLayerNum` (B1, Grad P). (2) Im
Spot-UV-Workflow als separate Schwarz-Weiß-Maskendatei für einen eigenen
Druckdurchgang (A11, Grad S). Unsere `gloss_mask.png` passt zu (2), nicht zu (1) –
die Warnung `GLOSS_INK_MODE` trifft den Sachverhalt richtig.

Zu **EM-R04**: Studio leitet die Weiß-Unterlage aus dem Motiv ab; „White
Underbase Choke" schrumpft sie unter die CMYK-Kanten (A12). Halbtransparente/graue
Ränder aus schlechter Freistellung sind eine benannte Fehlerquelle (A8) – bestätigt
indirekt den Sinn von `feather_alpha` (#361).

#### Dateiformat, Bittiefe, Metadaten

| ID | Annahme | Fundstelle | Evidenz | Status |
| --- | --- | --- | --- | --- |
| EM-F01 | PNG verlustfrei, RGBA fürs Farbmotiv | `eufymake_writer.py` | A1, A14 (S) | **bestätigt** |
| EM-F02 | Höhe als Graustufen-PNG (`L` / `I;16`) | `eufymake_writer.py` | A2, A3 (S) | **bestätigt**, TIFF zusätzlich zulässig |
| EM-F03 | 8 Bit ist Default, 16 Bit ist „nicht offiziell bestätigt" | `eufymake_export.py`, `eufymake_validate.py` | A2, A3 (S) | **widerlegt → umgesetzt**: `BIT_DEPTH_UNCONFIRMED` feuert seit dieser Version bei 8 Bit, nicht mehr bei 16 Bit; **Nachtrag #691 (2026-09-02):** seit PR #953 für beide Träger (8 und 16 Bit), Default 16 Bit |
| EM-F04 | Kein `pHYs`/DPI in den PNGs (Befund N10 in `RECOMMENDATIONS.md`) | `eufymake_writer.py` | B1 (P), A7 (S) | **teilbestätigt** – kein Mangel gegenüber Studio, siehe Abschnitt „Konsequenzen" |

**EM-F03** ist der konkreteste Codebefund: Der Hersteller empfiehlt für
Tiefenkarten selbst „16-bit/channel … if the option is available" (A2, A3). Die
Warnung `BIT_DEPTH_UNCONFIRMED` markierte bislang ausgerechnet den empfohlenen
16-Bit-Pfad als unbestätigt, während 8 Bit still durchlief. **Umgesetzt in dieser
Version:** Das Vorzeichen ist gedreht (`eufymake_validate.py`, Prüfung auf
`effective_bit_depth == 8`) – 8 Bit erzeugt jetzt `BIT_DEPTH_UNCONFIRMED`, 16 Bit
nicht mehr. `HEIGHT_PRECISION_LOSS` bleibt als zusätzliche, unabhängige Warnung
bestehen, wenn ein 8-Bit-Ziel echte 16-Bit-Quellpräzision verwirft. Die zugrunde
liegende Empfehlung ist weiterhin nur Grad S; vor einer noch schärferen
Formulierung (z. B. Fehlerstufe) steht Verifikation am Original (V-01) aus.

**EM-F04:** Das fehlende `pHYs` ist gegenüber Studio kein Mangel. Physische Größe
trägt im nativen Format die Canvas-Objektgeometrie
(`scaleX = mmToE1Units(width_mm / pixelWidth)`, B1, Grad P), nicht Bildmetadaten.
Offen bleibt, ob der *Importdialog* `pHYs` als Startgröße auswertet (Realtest
G-02). Befund N10 sollte entsprechend umformuliert werden (siehe „Konsequenzen").

#### Höhensemantik

| ID | Annahme | Fundstelle | Evidenz | Status |
| --- | --- | --- | --- | --- |
| EM-H01 | hell = hoch, dunkel = niedrig | `eufymake_export.py` | A2, A3, A6 (S) | **bestätigt** |
| EM-H02 | Schwarz = Nullpunkt = Materialebene | `height_map.py` | A6 (S) | **bestätigt** |
| EM-H03 | Die Datei trägt eine absolute mm-Höhe | Manifest `target` | A4, B6 (S) | **widerlegt** |
| EM-H04 | Clipping-/Sättigungsverhalten bei Vollweiß | – | – | **offen** |

**EM-H01/H02 bestätigt:** „pure white represents the highest point … black the
lowest" (A2/A3); Editor V17: Dodge hebt, Burn senkt, „Flatten resets an area to
zero" (A6).

**EM-H03 widerlegt:** Die Graustufe ist relativ. Die Höhenobergrenze ist ein
Prozessparameter in Studio, je Texturmodus:

| Texturmodus | Max. Höhe | Herkunft der Höhe |
| --- | --- | --- |
| Relief Texture | 5 mm | KI-Tiefenschätzung aus Bildsemantik |
| Flat Raised | 3 mm | flache Erhebung |
| Pattern Texture | 1 mm | Hell-Dunkel-Verhältnisse des Bildes |

Der Höhenregler kappt die Spitzen, statt die Kennlinie zu verschieben. BgRemover
kann keine mm-Reliefhöhe liefern und sollte das nicht suggerieren – die
Höhenkarte ist normalisiert, die mm-Zuordnung passiert in Studio (Vertragsaussage
für #688/#691, noch nicht in Dialogtexten umgesetzt).

#### Geometrie: mm, Pixel, DPI

| ID | Annahme | Fundstelle | Evidenz | Status |
| --- | --- | --- | --- | --- |
| EM-G01 | mm/DPI im Manifest erreichen Studio | `eufymake_writer.py` | A1 (S) | **widerlegt** (Folge von EM-C01) |
| EM-G02 | DPI-Plausibilität ist sinnvoll prüfbar | `export_checks.check_resolution` | A8, A14 (S), B1 (P) | **bestätigt** |
| EM-G03 | Zielmedium-Grenzen für `check_print_area` | `export_checks.check_print_area` | A10, A15 (S), C3 (E) | **bestätigt → umgesetzt** |
| EM-G04 | Seitenverhältnis-Konflikte werden von Studio gemeldet | – | – | **offen** |
| EM-G05 | `check_print_area` prüft tatsächlich gegen ein Zielmedium | `export_checks.py`, `eufymake_validate.py` | C1 (P) | **widerlegt zum Recherchezeitpunkt → umgesetzt** |

**EM-G05:** `check_print_area` lieferte bei `medium_size_mm is None` grundsätzlich
keinen Befund; der einzige produktive Aufrufer (`main_window._confirm_pre_save_checks`,
der **generische** „Bild speichern"-Pfad für PNG/JPEG/WebP/TIFF) übergab kein
Zielmedium. Wichtig für die Umsetzung: Der generische Speichern-Pfad kennt **kein**
Druckziel – ihm ein EufyMake-Flachbett-Maß aufzuzwingen hätte false positives bei
jedem großformatigen, nicht-EufyMake-bezogenen Bild erzeugt. **Umgesetzt in dieser
Version stattdessen im EufyMake-spezifischen Pfad:** `eufymake_validate.py` ruft
`export_checks.check_print_area(physical_size, STANDARD_FLATBED_MM)` auf und
übersetzt einen Treffer in den neuen, produktspezifischen Befund
`ExportCheckCode.PRINT_AREA_EXCEEDED` (Severity WARNING, nicht ERROR – die
zugrunde liegende Flachbettgröße ist weiterhin nur Grad S).
`STANDARD_FLATBED_MM = (330.0, 420.0)` lebt in `eufymake_export.py` mit
Provenienz-Kommentar. Der generische `export_checks.check_export`-Aufruf in
`main_window.py` bleibt unverändert ohne Zielmedium.

Belegte Anker: ≥ 300 DPI empfohlen (A8, A14); `.empf` trägt
`print_param.imgQuality: 300` (B1, Grad P); Druckkopf 1440 ppi (A15). Druckfläche
330 × 420 mm („13 × 16.5 in"), Objekthöhe 100 mm, seit Studio 4.0
Nullpunkt-Ausrichtung bis 130 mm; Kamera erkennt Objekte ≤ 60 mm, max.
Höhenvariation auf einem Objekt 2 mm (A10, A5). Unabhängige Rechnung aus B1 ergibt
333,2 × 418,1 mm (C2/C3) – zwei unabhängige Quellen, ähnliches Ergebnis. Für den
Code wurde die rundere, direkt herstellerseitig genannte Zahl (330 × 420 mm)
gewählt, nicht der aus Drittanbieter-Reverse-Engineering abgeleitete Wert.
`miniFlatbed` rechnet sich zu ≈ 333,2 × 87,9 mm (C3) – nicht gegengeprüft, nicht
ohne Bestätigung verwenden.

#### Software, Versionen, stilles Verhalten

| ID | Annahme | Evidenz | Status |
| --- | --- | --- | --- |
| EM-S01 | Zielversion ist benannt | A5, A9, A13, B2 (S) | **bestätigt** – Versionsachse: Studio 4.0/Editor V17 (Juli 2026, aktuell), 3.7.1 (April 2026), 2.6.0.2 (März 2026, historisch) |
| EM-S02 | Studio kann Höhenkarten nicht selbst bearbeiten | A5, A6 (S) | **widerlegt** – Editor V17 bearbeitet nativ (Brightness/Contrast/Highlights/Shadows/Gamma, Dodge/Burn/Flatten, getrennte Höhen-Layer je Text/Motiv/Hintergrund); überschneidet sich mit `height_ops.py`, verschiebt BgRemovers Mehrwert auf das *Erzeugen* sauberer 16-Bit-Karten |
| EM-S03 | Fehlerhafte Importe fallen auf | B2 (S) | **widerlegt** – generierte `.empf` lädt in Studio 2.6.0.2 „silently … but has no visible PNG image"; Import-/Testprotokolle müssen „nichts passiert" als eigenen Ausgang erfassen |

#### Validator-Schweregrade

| ID | Befund | Bewertung |
| --- | --- | --- |
| EM-V01 | `BIT_DEPTH_UNCONFIRMED` | **umgesetzt** – Vorzeichen gedreht (EM-F03) |
| EM-V02 | `GLOSS_INK_MODE` | bestätigt richtig, Wortlaut deckt sich mit B1 |
| EM-V03 | `PHYSICAL_SIZE_UNVERIFIED` | Schweregrad bleibt; Begründung könnte geschärft werden: nicht „unbestätigte Annahme", sondern „Studio liest die Größe nicht aus unseren Dateien" (noch nicht umgesetzt) |
| EM-V04 | `ASSET_SIZE_MISMATCH` als ERROR | bleibt richtig; ob Studio abweichende Höhenkartenmaße streckt oder ablehnt, ist offen (→ H-03) |
| EM-V05 | `PRINT_AREA_EXCEEDED` | **neu, umgesetzt** (EM-G05) |

### 4. Was bleibt echt offen (nur mit Hardware oder Herstelleranfrage lösbar)

| ID | Offene Frage | Weg | Ziel-Issue |
| --- | --- | --- | --- |
| H-01 | Nutzt Studio die 65536 Stufen einer 16-Bit-Karte oder quantisiert es auf 8 Bit? | Realtest: Gradientenkeil 16 Bit vs. auf 8 Bit reduziert, gleiche Höhe; Bänderung vermessen | #688 |
| H-02 | Welche Graustufe ergibt welche mm-Höhe bei gegebener Reglerstellung? | Realtest: Treppenkeil mit bekannten Stufen, Höhen mit Messuhr/Mikrometer | #688 |
| H-03 | Verhalten bei abweichenden Höhenkartenmaßen: strecken, zentrieren, ablehnen? | Realtest: gleiche Karte in 100 %, 50 %, anderes Seitenverhältnis | #688 |
| H-04 | Clipping bei Vollweiß-Flächen | Realtest: Weißplateau > Maximalhöhe | #688 |
| G-01 | Welche Startgröße setzt Studio beim Import (Pixel·DPI, feste mm, Canvas-Fit)? | Realtest: identische Pixelmaße, verschiedene `pHYs`-Werte | #689 |
| G-02 | Wertet der Importdialog `pHYs` aus? | Realtest wie G-01, mit/ohne Chunk | #689 |
| G-03 | Meldet Studio Seitenverhältnis-Konflikte oder normalisiert es still? | Realtest mit bewusst falschem Verhältnis | #689 |
| GL-01 | Grauwerte als Glanzintensität oder Schwellwert-Binarisierung? | Realtest: Gloss-Keil 0–255 | #690 |
| GL-02 | Braucht der Gloss-Durchgang einen eigenen Druckvorgang (A11) oder geht er im Ink-Mode mit? | Realtest + Herstelleranfrage | #690 |
| V-01 | Alle S-Belege am Original verifizieren | Herstellerseiten ohne Egress-Sperre abrufen | #687 |

**Herstelleranfrage (Vorschlag, `support@eufymake.com`):** (1) Wird eine
16-Bit-Graustufen-Höhenkarte intern mit voller Präzision verarbeitet? (2) Wertet
Studio `pHYs`/Auflösungs-Metadaten beim Import aus? (3) Wird eine Gloss-Maske als
Intensität oder binär interpretiert? (4) Gibt es eine dokumentierte
Graustufe→mm-Kennlinie je Texturmodus?

### 5. Testmatrix – Achsen und erste Zellen

| Achse | Werte |
| --- | --- |
| Studio-Version | 4.0 / Editor V17 · 3.7.1 · (2.6.0.2 nur historisch) |
| Druckermodell | eufyMake E1 |
| Firmware | zu protokollieren, nicht öffentlich versioniert |
| Druckbett | `standardFlatbed` · `miniFlatbed` |
| Betriebssystem | macOS · Windows |
| Texturmodus | Relief (5 mm) · Flat Raised (3 mm) · Pattern (1 mm) · Custom Depth Map |
| Ink-Mode | `white_cmyk` · `cmyk` · `cmyk_gloss` · `white_cmyk_gloss` · `gloss` |
| Material/Tinte | je Testkörper festhalten (Weißtinte ja/nein) |
| Bittiefe der Höhenkarte | 8 · 16 |

Erste, materialsparende Zellen – Import-only, kein Druck:

| Zelle | Eingabe | Variierter Faktor | Erwartete Beobachtung | Messmethode |
| --- | --- | --- | --- | --- |
| I-01 | `color_motif.png` allein | – | importiert, Größe/DPI-Anzeige protokolliert | Screenshot + Größenfeld |
| I-02 | `color_motif.png` + `height_map.png` | Höhenkarte zugeordnet | 3D-Vorschau zeigt Relief, hell = hoch | Screenshot Vorschau |
| I-03 | Höhenkarte 8 Bit vs. 16 Bit, identisches Motiv | Bittiefe | Vorschau-Unterschied bei Gradienten? | Screenshot-Differenz |
| I-04 | Höhenkarte mit halber Kantenlänge | Pixelmaß | strecken / zentrieren / Ablehnung | Screenshot + Warnungstext |
| I-05 | PNG mit `pHYs` 300 vs. 72 vs. ohne | `pHYs` | Startgröße in mm | Größenfeld ablesen |
| I-06 | `manifest.json` allein per Drag&Drop | – | Ablehnung erwartet (bestätigt EM-C01) | Fehlermeldung |
| I-07 | Vollweiße Höhenkarte | Sättigung | Plateau auf Reglermaximum | Vorschau + Höhenwert |

Ein Ergebnis „nichts passiert, keine Meldung" ist bei jeder Zelle als eigener
Ausgang zu protokollieren (EM-S03). Erst danach die druckenden Zellen
(Materialverbrauch!): Treppenkeil für H-02, Gradientenkeil für H-01, Gloss-Keil
für GL-01. Alle Import-Zellen brauchen nur generierte Testbilder (Keile,
Gradienten, Treppen), reproduzierbar als kleines Skript unter `scripts/` plus
SHA-256-Protokoll – noch nicht umgesetzt (Stand Evidenzversion 1) → umgesetzt:
`scripts/eufymake_fixture_generator.py` erzeugt HEIGHT-/mm-DPI-/Gloss-Fixtures
deterministisch nach `tests/fixtures/eufymake_hardware/` mit SHA-256 je Datei
in `fixtures_manifest.json`; ausfüllbare Protokollvorlagen liegen unter
[`EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`](EUFYMAKE-687-PROTOKOLL-VORLAGEN.md).

### 6. Konsequenzen

**In dieser Evidenzversion umgesetzt (Code):**

1. `BIT_DEPTH_UNCONFIRMED` (`eufymake_validate.py`): feuert bei 8 Bit statt bei
   16 Bit; `i18n.py` in allen sechs Runtime-Sprachen (de/en/es/fr/uk/zh)
   entsprechend umformuliert.
2. `PRINT_AREA_EXCEEDED` (neuer `ExportCheckCode`, `eufymake_validate.py`):
   `check_print_area` aus `export_checks.py` ist jetzt produktiv verdrahtet – im
   EufyMake-spezifischen Validierungspfad gegen `STANDARD_FLATBED_MM =
   (330.0, 420.0)` (`eufymake_export.py`), **nicht** im generischen „Bild
   speichern"-Pfad (der kein Druckziel kennt). Severity WARNING, i18n in allen
   sechs Sprachen.

**Noch offen (Doku/Vertrag, ohne Hardware möglich):**

3. ADR-Nachtrag: `manifest.json` explizit als BgRemover-intern kennzeichnen,
   kein Studio-Vertrag (EM-C01); ZIP-Option als nutzlos markieren (EM-C04).
4. Höhenkarte im Exportdialog/Manifest als normalisiert/relativ beschreiben,
   nicht als mm-Träger (EM-H03).
5. Befund **N10** in `RECOMMENDATIONS.md` umformulieren: von „PNGs ohne `pHYs`"
   zu „Startgröße im Studio-Importdialog unbelegt" (EM-F04).
6. `PHYSICAL_SIZE_UNVERIFIED`-Begründungstext schärfen (EM-V03).

**Bleibt bei den Realtest-Issues:** #688 (H-01…H-04), #689 (G-01…G-03), #690
(GL-01/GL-02), Verifikation der S-Belege (V-01).

---

## Evidenzversion 2 (2026-08-15)

### 0. Methodik und Grenzen

Version 2 ist die direkte Volltext-Verifikation der für den Exportvertrag
entscheidenden Quellen aus Version 1. Gelesen wurden die Herstellerseiten A1–A5,
A7–A11, A14 und A15 im Original sowie die aktuelle 4.2-Release-Note. Zusätzlich
wurden der vollständige Diskussionsverlauf von B2, der Quellcode von B1 und ein
frei zugänglicher E1-Praxisthread im PedalPCB-Forum geprüft. Reddit und der in der
Websuche gefundene Facebook-Thread waren durch deren Netzwerkschutz nicht direkt
lesbar; deren Suchtreffer gelten deshalb nicht als Tatsachennachweis.

Evidenzgrade in Version 2:

- **P** – Primär-/Herstellerquelle im Volltext gelesen.
- **C** – Communityquelle im Volltext gelesen; keine Herstellerzusage.
- **S** – nur Suchtreffer/Snippet gelesen; nicht als Bestätigung ausreichend.
- **E** – eigene Ableitung aus P- oder C-Material.
- **T** – reproduzierbarer Realtest mit protokollierter Eingabe und Ausgabe.

Es fand weiterhin kein eigener Studio-, Import- oder Drucktest statt; Grad **T**
wird daher auch in Version 2 nicht vergeben.

### 1. Verifizierte Quellen und neue Quellen

#### Direkte Revalidierung der Quellen aus Version 1

| ID | Volltextbefund am 2026-08-15 | Grad V2 |
| --- | --- | --- |
| A1 | Supportartikel vom 2026-01-23: PC/Web akzeptiert PNG, JPG, WebP (je max. 12800×12800 px), SVG (5 MB), PSD/AI/PDF (je 45 MB). Beschrieben ist Datei-Upload; ein Ordner-/Manifest-Import wird nicht beschrieben. | P |
| A2 | Supportartikel vom 2026-03-09: separate Graustufen-Tiefenkarte; Weiß = hoch, Schwarz = niedrig; PNG oder TIFF. Im ZBrush/Photoshop-Workflow soll beim Export 16 Bit/Kanal gewählt werden, **wenn verfügbar**. | P |
| A3 | Herstellerseite vom 2026-06-22, aber namentlich von Community-Autor Willem Post. Bestätigt Hell/Dunkel-Semantik und relative Grauwerte, enthält jedoch keine 16-Bit-Empfehlung. Inhaltlich Communitybeleg, nicht Herstellervertrag. | C |
| A4 | Supportartikel vom 2025-11-13: Flat, Flat Raised, Pattern, Relief und Customize Texture sowie Upload eigener Graustufenbilder. Im lesbaren Text stehen **keine** Maximalhöhen 5/3/1 mm. | P |
| A5 | Hersteller-Release vom 2026-07-31: native Height-Map-Bearbeitung in Editor V17; Zero-Point-Alignment von 100 auf 130 mm erweitert, automatische Führung dorthin bei Objekten über 60 mm. | P |
| A7 | Wiki, zuletzt 2026-04-13 bearbeitet: Content-Import und Verweis auf die unterstützten Dateitypen; kein Paket-/Manifestvertrag. | P |
| A8 | Wiki, zuletzt 2026-06-23 bearbeitet: Importqualität, Transparenz, Kanten und Texturen. Empfiehlt hochwertige Originaldateien, nennt aber **keine 300-DPI-Grenze**. | P |
| A9 | Wiki-Releaseübersicht: am 2026-08-15 aktuell sind Studio Desktop **4.2.2**, Firmware **4.0.2** und Editor **1.19.0**; die 4.2-Release-Note ist vom 2026-08-13. | P |
| A10 | Supportartikel vom 2025-12-19: maximale normale Druckabmessung **330×420×60 mm**. | P |
| A11 | Herstellerartikel vom 2026-03-04: Spot UV mit zwei Dateien und zweitem Durchgang; in der Schwarz-Weiß-Maske bedeutet **Schwarz = Gloss auftragen**, **Weiß = nichts auftragen**. | P |
| A14 | Allgemeiner Herstellerblog vom 2026-03-04: empfiehlt 300 DPI für PNG/JPG-Druckvorlagen. Das ist keine E1-Studio-Import- oder `pHYs`-Spezifikation. | P |
| A15 | Produktseite: Druckbereich bis 330×420 mm und Ausgabeauflösung bis 1440 **DPI**. Sie belegt keinen „1440-ppi-Druckkopf“. | P |

#### Neue Community-/Sekundärquellen

| ID | Quelle | Grad | Relevanter Befund |
| --- | --- | --- | --- |
| B9 | [Vollständige Kommentare zu `TapuCosmo/empf-generator` Issue #1](https://github.com/TapuCosmo/empf-generator/issues/1) | C | Ein Nutzer meldete den stillen Bildfehler in Studio 2.6.0.2. Maintainer und ein weiterer Nutzer berichteten später erfolgreiche Importe des alten unverschlüsselten ZIP-Formats; ab Studio 2.7.0.6 exportiert Studio ein verschlüsselt gekapseltes Format, soll alte ZIP-Projekte aber weiterhin importieren. |
| B10 | [PedalPCB Community Forum, „Adventures in UV Printing – Eufymake E1“](https://forum.pedalpcb.com/threads/adventures-in-uv-printing-eufymake-e1.28238/), ab 2026-01-25 | C | Belegt reale E1-Nutzung und gute Flachdruckqualität; Texturdruck wird dort ausdrücklich noch nicht bewertet. Große Canvas-/Texturdrucke werden als langsam beschrieben. Kein Beleg für Dateivertrag oder Bittiefe. |
| B11 | [Facebook-Treffer „Bug found in print depth map rendering“ in der Websuche](https://www.google.com/search?q=%22Bug+found+in+print+depth+map+rendering%22+eufymake) | S | Snippet meldet eine mögliche Entkopplung von Crop und Depth Map. Original war nicht zugänglich; nur als neuer Testimpuls I-08 verwendbar. |

### 2. Korrigierte Entscheidungspunkte

#### Statusinventar V2

Diese Tabelle ist der vollständige V2-Status-Snapshot aller Annahmen aus dem
V1-Inventar. Sie ersetzt nur deren Statusspalte; Annahmetext, Fundstelle und
historische Bewertung bleiben in V1 nachvollziehbar. Die Detailabschnitte unter
der Tabelle begründen alle in V2 geänderten Bewertungen.

| ID | Status V2 | Begründung bzw. Änderung gegenüber V1 |
| --- | --- | --- |
| EM-C01 | **nicht belegt / intern** | Für eine Studio-Auswertung von `manifest.json` gibt es keinen dokumentierten Vertrag; I-06 bleibt der erforderliche Negativtest. |
| EM-C02 | **Produktentscheidung, nicht Herstellervertrag** | Legacy-`.empf`-ZIPs funktionieren laut B9; das aktuelle Exportformat ist verschlüsselt gekapselt. |
| EM-C03 | **widerlegt** | TIFF ist nach A2 ein Tiefenkarten-Dateiformat, kein Projektcontainer. |
| EM-C04 | **teilbestätigt** | ZIP ist für Legacy-`.empf` real, aber nicht als Importträger des heutigen BgRemover-Asset-Bündels belegt. |
| EM-R01 | **bestätigt** | A1/A7 führen PNG als unterstützten Gestaltungsinhalt; am Rollenmodell ändert V2 nichts. |
| EM-R02 | **bestätigt** | A2/A3 bestätigen eine Graustufen-Höhenkarte am Bildobjekt. |
| EM-R03 | **teilbestätigt** | Eine separate Spot-UV-Maske ist bestätigt, aber A11 widerlegt die bisherige Hell-Polarität: Schwarz druckt Gloss, Weiß nicht; eine abgestufte Intensitätssemantik bleibt offen. |
| EM-R04 | **teilbestätigt** | Weiß-Unterlage und Choke sind belegt; die genaue Ableitung aus Alpha/Coverage bleibt indirekt. |
| EM-F01 | **bestätigt** | PNG/RGBA bleibt ein belegtes, verlustfreies Format für das Farbmotiv. |
| EM-F02 | **bestätigt** | PNG-Graustufen bleiben belegt; A2 nennt TIFF zusätzlich als zulässiges Höhenformat. |
| EM-F03 | **widerlegt; Warnlogik umgesetzt** | A2 empfiehlt 16 Bit ausdrücklich. Ob Studio alle 65536 Stufen nutzt, bleibt offen; 8 Bit ist weiterhin zulässig und im Code der Default. |
| EM-F04 | **teilbestätigt** | Das fehlende `pHYs` ist belegt, aber dessen Auswertung als Import-Startgröße bleibt offen; 300 DPI aus A14 sind allgemeine Druckvorbereitung, kein Studio-Importvertrag. |
| EM-H01 | **bestätigt** | A2/A3 bestätigen hell = hoch und dunkel = niedrig. |
| EM-H02 | **bestätigt** | A2/A3 bestätigen Schwarz als niedrigsten Punkt; die Material-/Nullpunktzuordnung bleibt vom Studio-Prozess abhängig. |
| EM-H03 | **widerlegt** | Die Datei trägt relative Graustufen, keine absolute mm-Höhe. Nur 5 mm für Relief sind zusätzlich durch B6 gestützt; 3 mm/1 mm und die genaue Graustufe→mm-Kennlinie bleiben offen. |
| EM-H04 | **offen** | Für Clipping bzw. Sättigung bei Vollweiß liegt weiterhin kein belastbarer Beleg vor. |
| EM-G01 | **nicht belegt / offen** | Weil EM-C01 nicht negativ getestet ist, ist auch die Übergabe von mm/DPI über das Manifest nicht widerlegt, aber ohne Studio-Vertrag rein intern. |
| EM-G02 | **teilbestätigt** | 300 DPI sind eine sinnvolle allgemeine Qualitätsheuristik (A14), jedoch keine belegte Studio-Grenze; `pHYs`-Auswertung und Startgröße bleiben Realtests. |
| EM-G03 | **bestätigt** | A10/A15 bestätigen die normale Druckfläche 330×420 mm direkt; 60 mm ist die normale Objekthöhe, 130 mm nur die Zero-Point-Alignment-Grenze. |
| EM-G04 | **offen** | Für Studio-Meldungen bei Seitenverhältnis-Konflikten liegt weiterhin kein Beleg vor. |
| EM-G05 | **bestätigt; umgesetzt** | Der EufyMake-spezifische Validator prüft gegen das belegte Standard-Flachbett; der generische Speichern-Pfad bleibt zielneutral. |
| EM-S01 | **bestätigt; aktualisiert** | Primärachse ist Studio 4.2.2, Firmware 4.0.2 und Editor 1.19.0; ältere Versionen sind Regression-/Historienachsen. |
| EM-S02 | **widerlegt** | Studio/Editor können Höhenkarten nativ bearbeiten; V2 ändert diese Bewertung nicht. |
| EM-S03 | **im Einzelfall widerlegt; allgemein offen** | B2 belegt einen stillen Fehlschlag in 2.6.0.2, spätere B9-Kommentare widersprechen aber einem generellen Importproblem. |
| EM-V01 | **umgesetzt; Textkorrektur offen** | Die Warnrichtung für 8 Bit bleibt richtig; „unbestätigt“ muss durch die verifizierte Herstellerempfehlung ersetzt werden. |
| EM-V02 | **bestätigt** | Die Ink-Mode-Warnung bleibt richtig; sie ersetzt nicht den separaten Polaritäts-/Registrierungstest für `gloss_mask.png`. |
| EM-V03 | **teilbestätigt; Textkorrektur offen** | Der Schweregrad bleibt, die Begründung muss fehlenden Datei-/Studio-Vertrag statt eine pauschal „unbestätigte Annahme“ nennen. |
| EM-V04 | **bestätigt; Studio-Verhalten offen** | Gleiche Asset-Maße bleiben für den Exportvertrag erforderlich; Strecken, Zentrieren oder Ablehnen durch Studio ist noch zu testen. |
| EM-V05 | **bestätigt; umgesetzt** | A10/A15 bestätigen die 330×420-mm-Schwelle für `PRINT_AREA_EXCEEDED` direkt. |

#### Importträger und `.empf`

Die Aussage „Studio importiert Einzeldateien, nicht Pakete“ war zu absolut.
Korrekt ist:

1. **Gestaltungsinhalte** werden als einzelne unterstützte Dateien hochgeladen
   (A1/A7, P).
2. Der BgRemover-Ordner ist ein **Lieferbündel für mehrere manuelle Imports**, kein
   dokumentierter atomarer Studio-Importträger. Für `manifest.json` ist keine
   Studio-Auswertung belegt; „widerlegt“ wäre ohne Negativtest zu stark.
3. Studio öffnet daneben native `.empf`-Projekte. B1 beschreibt das alte
   unverschlüsselte ZIP-Layout. B9 zeigt, dass neu exportierte `.empf` seit 2.7.0.6
   verschlüsselt gekapselt sind, das alte ZIP-Layout aber laut Communitytests
   rückwärtskompatibel importiert wird.

Damit bleibt „kein natives `.empf` erzeugen“ eine vernünftige Produktentscheidung,
ist aber **nicht** durch generelles Importversagen bestätigt. Der heutige
Asset-Ordner ist brauchbar, sofern UI und Dokumentation klar sagen, dass seine
Dateien einzeln in Studio importiert/zugeordnet werden müssen.

#### Bittiefe und Höhensemantik

A2 verifiziert die 16-Bit-Empfehlung im konkreten ZBrush/Photoshop-Workflow. Sie
belegt, dass Studio eine so exportierte Tiefenkarte importieren soll; sie belegt
**nicht**, dass Studio intern alle 65536 Stufen erhält oder dass 8 Bit unzulässig
ist. Die in PR #795 gedrehte Warnung bleibt als **WARNING** sachgerecht. Ihr Text
sollte künftig „verifizierte Herstellerempfehlung“ statt „unbestätigter Hinweis“
sagen. Außerdem bleibt `DEFAULT_BIT_DEPTH = 8`; der Standardpfad erzeugt damit
weiterhin die neue Warnung. Ob der Default auf 16 Bit wechseln soll, gehört nach
H-01 in #688/#691.

**Nachtrag 2026-09-02 (#691):** Das versionierte Zielprofil v1 setzt den
konservativen Default inzwischen auf 16 Bit. Beide Träger bleiben bis zur
physischen #688-Messung ausdrücklich unbestätigt; 8 Bit ist weiterhin als
Legacy-Auswahl mit Warnung verfügbar. Damit ist die hier festgehaltene offene
Default-Entscheidung umgesetzt, ohne eine Nutzung aller 65536 Stufen zu
behaupten.

Die Werte „Relief 5 mm / Flat Raised 3 mm / Pattern 1 mm“ sind durch die direkt
gelesenen A4/A5 nicht vollständig belegt. B6 trägt nur die 5-mm-Angabe für Relief.
Bis Original-UI oder weitere Herstellerquelle die Werte 3/1 mm bestätigt, dürfen
sie nur als zu prüfende Matrixwerte, nicht als bestätigte Spezifikation gelten.

#### Gloss

A11 korrigiert die bisherige Richtung der exportierten Hilfsmaske für genau den
beschriebenen Spot-UV-Dateiworkflow: **Schwarz druckt Gloss, Weiß druckt nichts**.
Das widerspricht der bisherigen ADR-Annahme „hell = mehr Glanz/Klarlack“. Zugleich
zeigt B1 native Ink-Modi (`gloss`, `cmyk_gloss`, `white_cmyk_gloss`). Es existieren
also zwei verschiedene Workflows:

- separater Schwarzmasken-/Zweitdruck-Workflow nach A11;
- integrierter nativer Ink-Mode im `.empf`-Canvas nach B1.

`GL-02` ist deshalb keine Entweder-oder-Frage mehr. Für BgRemovers separate
`gloss_mask.png` ist der A11-Workflow der direkte Anker; vor produktiver Nutzung
müssen Polarität, Registrierung und eine mögliche Intensitätsabstufung in #690
getestet werden. `GLOSS_INK_MODE` bleibt richtig, aber EM-R03 wechselt von
„teilbestätigt“ zu **„Polaritätsannahme widerlegt; Intensitätssemantik offen“**.

#### Geometrie, Auflösung und Gerätehöhe

- `STANDARD_FLATBED_MM = (330, 420)` ist nun direkt durch A10/A15 (P) bestätigt;
  `PRINT_AREA_EXCEEDED` darf auf diese Zahl verweisen. Eine Warnung bleibt sinnvoll,
  weil Ausrichtung/Drehung und Zubehörflächen gesondert zu behandeln sind.
- A10 nennt 60 mm normale Objekthöhe. A5 erweitert lediglich die
  **Zero-Point-Alignment-Grenze** von 100 auf 130 mm und führt Objekte über 60 mm
  in diesen Modus. „Objekthöhe 100 mm“ war falsch verkürzt.
- A15 beschreibt bis zu 1440 DPI Ausgabeauflösung, keinen 1440-ppi-Druckkopf.
- 300 DPI aus A14 ist allgemeine Druckvorbereitung; A8 nennt keine feste Zahl.
  `imgQuality: 300` aus B1 darf ohne weitere Formatkenntnis nicht mit Bild-DPI oder
  `pHYs` gleichgesetzt werden. G-01/G-02 bleiben Realtests.
- C3 bleibt eine plausible Rechnung aus Legacy-`.empf`-Canvasmaßen, aber keine
  unabhängige Herstellerbestätigung. Besonders die Mini-Flatbed-Ableitung darf
  nicht als physische Druckfläche verwendet werden.

#### Softwareachse und stilles Verhalten

EM-S01 war bereits am Recherchedatum veraltet. Primäre Testachse ist nun Studio
**4.2.2**, Firmware **4.0.2**, Editor **1.19.0**; 4.0/V17, 3.7.1 und 2.6.0.2 sind
Regression-/Historienachsen. Firmware ist öffentlich versioniert.

EM-S03 wird abgeschwächt: Ein stiller Fehlschlag wurde in B2 für einen konkreten
2.6.0.2-Versuch berichtet, spätere Kommentare widersprechen einem generellen
Problem. „Nichts passiert/kein Bild“ bleibt ein notwendiger Ergebniswert im
Protokoll, ist aber kein bestätigtes Standardverhalten.

### 3. Aktualisierte offene Punkte und Testmatrix

| Achse | Primärwert V2 | Regression/Variation |
| --- | --- | --- |
| Studio | 4.2.2 | 4.0, 3.7.1, 2.6.0.2 historisch |
| Editor | 1.19.0 | V17/1.17.0 historisch |
| Firmware | 4.0.2 | tatsächlich installierte Version protokollieren |
| Druckbett | Standard 330×420 mm | Mini nur nach eigener Maßverifikation |
| Bittiefe | 16 Bit empfohlen, Nutzungstiefe offen | 8 Bit als Vergleich |
| Gloss | A11-Schwarzmaske, separater Durchgang | native Ink-Modi getrennt betrachten |

Ergänzungen/Korrekturen der Importzellen:

| Zelle | Eingabe | Variierter Faktor | Erwartete Beobachtung | Messmethode |
| --- | --- | --- | --- | --- |
| I-06 | `manifest.json` allein und kompletter BgRemover-Ordner | Träger | JSON abgelehnt; Ordnerverhalten **offen**, nicht vorab „bestätigt“ | sichtbare Meldung/kein Effekt protokollieren |
| I-08 | Motiv samt Height Map vor/nach Crop in Studio | Crop | Farbmotiv und Depth Map bleiben registriert; Forumssnippet B11 meldet mögliches Auseinanderlaufen | identische Referenzmarker + Vorschau-Differenz |
| I-09 | Legacy-`.empf` aus B1 und aktuell von Studio exportiertes `.empf` | Containergeneration | Legacy importierbar; aktuelle Datei nicht als schlichtes ZIP lesbar | Dateisignatur/Importmeldung, keine Umgehung der Verschlüsselung |
| I-10 | Gloss-Maske schwarz/weiß invertiert, sonst identisch | Polarität | A11: Schwarz erhält Gloss, Weiß nicht | Vorschau und kleiner Zweitdruck nach Sicherheitsfreigabe |

Weiter offen bleiben volle 16-Bit-Nutzung (H-01), Graustufe→mm-Kennlinie (H-02),
abweichende Kartenmaße (H-03), `pHYs`/Startgröße (G-01/G-02),
Gloss-Intensitätsabstufung (GL-01) und die Registrierung des Zweitdrucks. Die bisher
genannten Texturhöhen 3/1 mm werden als eigener UI-/Herstellerquellen-Check ergänzt.

**Nachtrag (2026-08-15):** H-02 und H-03 hatten in der obigen Tabelle zunächst
keine eigene Testzelle – die Ergänzungsrunde deckte nur I-06/I-08/I-09/I-10 ab.
[`EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`](EUFYMAKE-687-PROTOKOLL-VORLAGEN.md)
ergänzt dafür **I-11** (Treppenkeil-Druck für H-02) und **I-12** (Höhenkarte
mit abweichendem Seitenverhältnis für H-03) samt Fixtures. Beide Fragen
bleiben im Sinne dieses Abschnitts weiterhin „offen“, bis der jeweilige
Realtest tatsächlich durchgeführt wurde – die Ergänzung schafft nur die
fehlende Testzelle, kein Ergebnis.

### 4. Konsequenzen aus Version 2

1. Die Codeänderung aus PR #795 zur 330×420-mm-Warnschwelle ist direkt bestätigt.
2. Die 16-Bit-Warnlogik bleibt vertretbar; nur die Formulierung „unbestätigt“ ist
   nach A2 überholt. Vollpräzisionsnutzung und Defaultwechsel bleiben offen.
3. Issue-/Dokuformulierungen müssen Asset-**Lieferbündel** und nativen
   Studio-Importträger trennen; `manifest.json` ist mangels Vertrag intern, nicht
   durch bloße Quellenabwesenheit experimentell „widerlegt“.
4. Vor Einsatz der Gloss-Maske ist die dokumentierte Hell-Polarität gegen die
   A11-Schwarzmaske zu korrigieren bzw. in #690 real zu testen.
5. Testmatrix und Protokoll müssen aktuelle öffentliche Software-/Firmwarestände,
   Containergeneration und Crop/Depth-Map-Registrierung aufnehmen.

---

## Nachtrag zur #688-Testvorbereitung (2026-09-02)

Die Prüfung des tatsächlich eingecheckten Materials ergab zwei
Konfundierungen, die vor einem Hardwarelauf geschlossen werden mussten:

1. I-02 und I-08 kombinierten COLOR mit 1200×1200 bzw. 2400×1800 px mit einer
   256×256-HEIGHT-Map. Damit waren Reliefzuordnung und Crop-Verhalten nicht von
   Größen-/Seitenverhältnisbehandlung zu trennen.
2. Alle COLOR-Fixtures waren voll opak. EM-R04 und das #688-Kriterium
   „nicht-null HEIGHT in transparenten COLOR-Bereichen" hatten weder Fixture
   noch Protokollzelle.

Der deterministische Generator ergänzt deshalb
`color_height_reference.png` (RGBA, 256×256, voll opak), die daraus
pixelgenau abgeleitete `height_registration_16bit.png` und
`color_alpha_coverage.png` (RGBA, 256×256, konstantes RGB 40/80/220, drei
Felder Alpha 0/128/255). I-02 verwendet die COLOR-Referenz mit dem
dimensionsgleichen `height_wedge_16bit.png`; I-08 verwendet sie mit der
HEIGHT-Registriermap, deren asymmetrische horizontale und vertikale Landmarks
exakt auf den nicht-weißen COLOR-Markern liegen. Die neue Zelle **I-13**
kombiniert die Alpha-Datei mit `height_mean_16bit.png`, deren digitaler
HEIGHT-Wert über die gesamte Fläche konstant 32768 und damit sicher nicht null
ist. Somit variieren in I-13 weder RGB noch HEIGHT, sondern ausschließlich die
Coverage.

| Zelle | Eingabe | Variierter Faktor | Erwartete Beobachtung | Messmethode |
| --- | --- | --- | --- | --- |
| I-02 | `color_height_reference.png` + `height_wedge_16bit.png` | HEIGHT zugeordnet, identisches Pixelmaß | Reliefzuordnung ohne Größen-Konfundierung; hell = hoch | Studio-Vorschau + Screenshot |
| I-08 | `color_height_reference.png` + `height_registration_16bit.png` vor/nach Crop | Crop | Pixelgleiche asymmetrische COLOR-/HEIGHT-Landmarks bleiben auf X und Y registriert | Vorschau-Differenz + Ausdruck |
| I-13 | `color_alpha_coverage.png` + `height_mean_16bit.png` | COLOR-Alpha 0/128/255 bei konstantem RGB und HEIGHT 32768 | Coverage-/Underbase-Effekt je Feld, ohne Farbe oder HEIGHT-Wert als Störvariable | Vorschau + Druckmessung/Fotoreferenz |

Der neue unabhängige Pre-Import-Inspector
`scripts/eufymake_fixture_inspector.py` liest am Zielrechner SHA-256,
Bytegröße, Pillow-Lesbarkeit/-Version, IHDR, vollständige Chunkfolge, `pHYs`
und CRCs aus und schreibt einen JSON-Nachweis. Der Pillow-Modus bleibt
diagnostisch; die Formatprüfung verwendet die rohen IHDR-Felder. Schema 3
(seit #952: Schema 4) und der extern vorgegebene Manifest-SHA binden den Report
an den aktuellen Satz.
Dieser Nachtrag ändert keine Hardwareaussage:
Import- und Druckresultate bleiben bis zum realen Test als **offen** markiert.

---

## Nachtrag zur #689-Testvorbereitung (2026-09-02)

Die Checkout-Prüfung aus #689 fand drei noch nicht ausführbare Zellen: I-06
verwies auf das Fixture-Provenienzmanifest statt auf ein echtes
BgRemover-Exportmanifest; nicht quadratische DPI fehlten; und I-08 hatte noch
keine gemeinsame COLOR/HEIGHT/GLOSS-Registriermap.

Schema 3 des Fixture-Katalogs schließt diese Lücken, ohne eine
Hardwarebeobachtung vorwegzunehmen:

- `mm_typisch_phys_xy.png` kodiert bei konstanten 1200×1200 px getrennte
  300 dpi auf X und 150 dpi auf Y. Der ganzzahlige `pHYs`-Chunk
  (11811×5906 px/m) impliziert 101,600×203,183 mm; 101,6×203,2 mm sind nur
  die Werte der Sollformel vor PNG-Quantisierung.
- `export_mm_dpi_conflict/` ist ein über den produktiven
  `bgremover.eufymake_writer.write_export` erzeugtes Paket mit
  `color_motif.png`, `height_map.png`, `gloss_mask.png` und `manifest.json`.
  Das Manifest nennt 300×300 dpi bzw. 21,674666… mm; die PNGs tragen
  absichtlich 150×150 dpi im `pHYs`. I-06 kann damit Manifest- gegen
  PNG-Priorität messen.
- `gloss_registration.png` bildet dieselben asymmetrischen Landmarks wie
  `color_height_reference.png` und `height_registration_16bit.png` ab. Alle
  drei Dateien haben 256×256 px; die Tests vergleichen ihre Landmarkmasken
  pixelgenau.

Der unabhängige Inspector prüft nun neben den Einzel-Fixtures (Schema 3: 36,
seit #952 Schema 4: 41) auch Dateiliste, Hashes, PNG-Metadaten und
Manifestsemantik der Exportpakete (Schema 3: eines, Schema 4: sieben).
Importanzeige, tatsächliche Druckmaße, Crop/Offset und die daraus folgende
Produktentscheidung bleiben bis zur kontrollierten Studio-/E1-Ausführung
**offen**; ihre Ergebnisakte ist
[`EUFYMAKE-689-MM-DPI-VERTRAG.md`](EUFYMAKE-689-MM-DPI-VERTRAG.md).

---

## Nachtrag zur #690-Testvorbereitung (2026-09-02)

Schema 4 ergänzt fünf isolierte Einzel-Fixtures und sechs Writer-Pakete. Damit
sind die zuvor vermischten Fragen getrennt ausführbar:

- `gloss_mean.png` belegt den Mittelwert 128; `gloss_wedge_limited.png`
  begrenzt den Wertebereich auf 64…192 und macht automatische Normalisierung
  gegenüber einer echten Intensitätsabbildung unterscheidbar.
- `gloss_dimensions_half_width.png` bzw.
  `export_gloss_dimension_mismatch/` stellen 128×256 Gloss kontrolliert einem
  256×256 COLOR-/Manifestziel gegenüber. Der Produktionswriter bleibt
  fail-closed; nur das Fremddatenfixture wird nach dem Writerlauf ersetzt.
- `export_gloss_absent/`, `export_gloss_zero/` und `export_gloss_full/`
  trennen fehlende Rolle, gültige 0-Fläche und gültige 255-Fläche.
- `export_gloss_alpha_coverage/` hält RGB, HEIGHT=32768 und Gloss=128 konstant
  und variiert nur COLOR-Alpha 0/128/255.
- `export_gloss_height_cross/` hält COLOR opak und Gloss=128 konstant und
  variiert nur HEIGHT 0/32768/65535.

Der sichere Repository-Default ist damit maschinenlesbar belegt: Ohne
explizite GLOSS-Rolle entstehen weder `gloss_mask.png` noch eine
Manifestreferenz. Polarität, Intensitätskennlinie, Alpha-/HEIGHT-Maskierung,
Registrierung und Materialabhängigkeit bleiben bis zum getrennten Studio- und
Druckbefund offen. Die Ergebnisakte ist
[`EUFYMAKE-690-GLOSS-VERTRAG.md`](EUFYMAKE-690-GLOSS-VERTRAG.md).

---

## Evidenzversion 3 (2026-09-03)

### 0. Methodik und Grenzen

Version 3 ergänzt die ältere Evidenz, ohne Version 1 oder 2 umzudeuten. Sie
stützt sich auf den kontrollierten Studio-Lauf in
`EUFYMAKE-688-HEIGHT-VERTRAG.md`, `EUFYMAKE-689-MM-DPI-VERTRAG.md` und
`EUFYMAKE-690-GLOSS-VERTRAG.md` sowie auf den unveränderten Produktvertrag im
Repository. Studio 4.2.2 / Editor 1.20.0 zeigte den E1 online; die Firmware
wurde nicht angezeigt. Es wurde weder `Preview` noch `Print` ausgelöst und es
entstand kein physischer Druckbefund.

### 1. Entscheidungspunkt I-09

Der Vergleich Legacy gegen aktuelles `.empf` validiert weder den
BgRemover-Writer noch seinen bestätigten manuellen PNG-Einzeldatei-Importpfad.
I-06 und der native HEIGHT-Import belegen den aktuell unterstützten Träger.
I-09 bleibt deshalb als optionaler, klar abgegrenzter Explorationslauf
erhalten, ist aber kein Gate für #687, #691 oder einen Release. Erst eine
bewusste Produktentscheidung, `OpenQuestion.NATIVE_EMPF_PROJECT` in den Scope
zu nehmen, macht den Lauf und ein eigenes Migrationsarbeitspaket verpflichtend.

### 2. Quellen und Evidenz

Version 3 führt keine neue externe Quelle ein. Die Entscheidung kombiniert
die in Version 2 bereits getrennten Importpfade mit folgenden aktuellen
Nachweisen:

| ID | Nachweis | Evidenzgrad |
| --- | --- | --- |
| V3-T1 | I-06: `manifest.json` im Bilddialog nicht auswählbar; PNGs nur einzeln importierbar | T (Studio-Beobachtung vom 2026-09-02) |
| V3-T2 | Native 16-Bit-HEIGHT-Zuweisung über `Customize Texture` → `Upload Height Map Image` | T (Studio-Beobachtung vom 2026-09-03) |
| V3-P1 | BgRemover erzeugt PNG-Assets und hält `OpenQuestion.NATIVE_EMPF_PROJECT` sichtbar offen | P (Repositoryvertrag und Tests) |

### 3. Aktualisiertes Annahmeninventar

| ID | Status V3 | Begründung bzw. Änderung gegenüber V2 |
| --- | --- | --- |
| EM-C02 | **Produktentscheidung; I-09 nicht blockierend** | Der aktuelle Scope erzeugt bewusst kein natives `.empf`. Ein Legacy-/Current-Containertest wird erst bei einer gegenteiligen Produktentscheidung verpflichtend. |

### 4. Offene Punkte

Offen bleiben die physischen HEIGHT-, mm/DPI- und Gloss-Nachweise aus
#688–#690 sowie danach die Abschluss-Review von #687. Die Scope-Entscheidung
für I-09 bestätigt weder `.empf`-Kompatibilität noch dessen interne Struktur.

### 5. Aktualisierte Testmatrix

| Zelle | Status V3 | Verbindlichkeit |
| --- | --- | --- |
| I-09 Legacy | nicht ausgeführt / nicht anwendbar | optionaler Explorationslauf |
| I-09 aktuell | nicht ausgeführt / nicht anwendbar | optionaler Explorationslauf |

### 6. Konsequenzen aus Version 3

1. I-09 bleibt aus Transparenzgründen in den Vorlagen erhalten, zählt aber
   nicht zu den verpflichtenden Phase-1-Zeilen.
2. #687 bleibt bei 17/18 Akzeptanzkriterien; das letzte Kriterium ist die
   Abschluss-Review nach den Realtests, nicht ein `.empf`-Vergleich.
3. Eine spätere Aufnahme nativer `.empf`-Projekte erfordert eine neue
   Produktentscheidung, den optionalen I-09-Lauf und ein eigenes
   Migrationsarbeitspaket.

---

## Evidenzversion 4 (2026-09-03)

### 0. Methodik und Grenzen

Version 4 ergänzt die unveränderten Evidenzversionen 1 bis 3 um den Abschluss
aller verpflichtenden druckfreien Importzellen. Unmittelbar vor dem Lauf
bestätigte der unabhängige Inspector 41/41 Fixtures und 7/7 Exportpakete gegen
Manifest-Schema 4 und den erwarteten Manifest-SHA-256
`8e799f245f177947d0401c431feb0d41df0cde9b5007e4243c1add679a8e8758`.
Der Test lief in Studio 4.2.2 / Editor 1.20.0 bei online angezeigtem E1; die
Firmware wurde weiterhin nicht angezeigt. Die UI wurde ausschließlich über
den sichtbaren Import- und `Customize Texture`-Pfad bedient. Weder `Preview`
noch `Print` wurde ausgelöst; der Druckbudgetstand bleibt 0/35.

Die Live-Sitzung ist im Importprotokoll dokumentiert. Sie belegt
Editorverhalten, aber weder physische Reliefhöhe noch Druckgröße, Glossauftrag
oder Registrierung auf Material.

### 1. Neue Studio-Nachweise

| ID | Nachweis | Evidenzgrad |
| --- | --- | --- |
| V4-T1 | I-02/I-03: `height_wedge_16bit.png` und `height_wedge_8bit.png` nativ ohne Warnung akzeptiert; jeweils `3D` und vergleichbare Keilvorschau bei `Color Raised`, 2,50 mm | T |
| V4-T2 | I-04: 128×128-HEIGHT bei 256×256-COLOR und gleicher 1:1-Seitenrelation ohne Warnung auf der unveränderten 90,31×90,31-mm-Objektfläche akzeptiert | T |
| V4-T3 | I-07: `height_max_16bit.png` als gleichmäßiges Plateau; I-11: `height_steps_16bit.png` mit acht sichtbaren Plateaus | T |
| V4-T4 | I-12: 256×128-HEIGHT bei 256×256-COLOR mit `Depth image ratio does not match the original image` abgelehnt; bestehende HEIGHT-Zuweisung und Geometrie blieben unverändert | T |
| V4-P1 | Pre-Import-Report: 41/41 Fixtures und 7/7 Pakete erfolgreich; Report-SHA-256 `8c7264f842395a21a55b93006f2f598b08eb71cc95c528a53b21b5531daf885f` | P |

### 2. Aktualisierte Testmatrix

| Zelle | Status V4 | Belegte Grenze |
| --- | --- | --- |
| I-01 | abgeschlossen | kanonischer COLOR-Einzelimport ist `mm_typisch_phys.png`; Paket-`color_motif.png` bleibt I-06 zugeordnet |
| I-02 | abgeschlossen | nativer dimensionsgleicher 16-Bit-HEIGHT-Import |
| I-03 (8/16 Bit) | abgeschlossen | beide Träger akzeptiert; tatsächliche Präzisionsnutzung bleibt physisch offen |
| I-04 | abgeschlossen | Pixelmaß darf bei gleicher Seitenrelation abweichen; Studio passt an die COLOR-Fläche an |
| I-05/I-06 | abgeschlossen | `pHYs`, Manifest- und Mehrfachimport-Priorität wie in Evidenzversion 2/3 protokolliert |
| I-07 | abgeschlossen | editorseitige Vollweiß-/Plateau-Darstellung |
| I-08 | abgeschlossen | nativer COLOR/HEIGHT-Crop gekoppelt; separater Gloss-Layer unabhängig |
| I-09 Legacy/aktuell | nicht anwendbar | optionaler `.empf`-Explorationslauf gemäß Evidenzversion 3 |
| I-10 | abgeschlossen | normal/invertiert als Bild akzeptiert; physische Gloss-Polarität offen |
| I-11 | abgeschlossen | diskrete Sollstufen in der Editorvorschau sichtbar |
| I-12 | abgeschlossen | abweichende Seitenrelation wird ausdrücklich und ohne stillen Ersatz abgelehnt |
| I-13 | abgeschlossen | Alpha-Felder und konstante nicht-null HEIGHT importiert; physische Wirkung offen |
| G-01 bis G-08 | abgeschlossen auf Importebene | native Gloss-Verfügbarkeit allgemein belegt; zellspezifische Druckparameter und physische Aussagen offen |

Damit sind alle 27 verpflichtenden Phase-1-Zeilen abgeschlossen und die
„Nichts passiert“-Ausgänge explizit protokolliert. Die beiden I-09-Zeilen
zählen gemäß Scope-Entscheid nicht dazu.

### 3. Aktualisierte Annahmen

| ID | Status V4 | Begründung bzw. Änderung |
| --- | --- | --- |
| EM-F03 | **teilbestätigt** | Studio akzeptiert 8- und 16-Bit-PNG nativ; ob 16 Bit im Druck mehr als 8 Bit auflöst, bleibt unbewiesen. |
| EM-H04 | **teilbestätigt** | Vollweiß erscheint im Editor als gleichmäßiges Plateau; physisches Clipping und die tatsächliche Maximalhöhe bleiben unbewiesen. |
| EM-G04 | **bestätigt** | Abweichende absolute HEIGHT-Pixelmaße sind bei gleicher Seitenrelation akzeptiert; eine abweichende Seitenrelation wird mit expliziter Warnung fail-closed abgelehnt. |
| EM-S03 | **für Studio 4.2.2 und die Pflichtmatrix bestätigt; historischer Gegenbeleg bleibt** | Keine verpflichtende Zelle endete mit stillem, unsichtbarem Import; I-06-JSON und I-12 lieferten stattdessen eindeutige Nichtauswahl beziehungsweise Warnung. Der B2-Befund aus Studio 2.6.0.2 wird dadurch nicht umgedeutet. |

### 4. Konsequenzen und offene Gates

1. Phase 1 und der Phase-2-Startstand sind abgeschlossen; das physische Budget
   steht weiterhin unverbraucht bei 0/35.
2. Die nächsten zulässigen Schritte sind Geräte-/Material-/Messmittelfreigabe,
   die zellspezifische Fixierung der Druckparameter und anschließend Phase 3.
3. Die physischen HEIGHT-, mm/DPI- und Gloss-Nachweise aus #688–#690 bleiben
   offen. Erst danach folgen die Abschluss-Review von #687 und die Entscheidung,
   Profil v1 zu bestätigen oder bei Widerspruch Profil v2 anzulegen.
