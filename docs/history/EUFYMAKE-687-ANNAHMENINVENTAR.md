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
| EM-F03 | 8 Bit ist Default, 16 Bit ist „nicht offiziell bestätigt" | `eufymake_export.py`, `eufymake_validate.py` | A2, A3 (S) | **widerlegt → umgesetzt**: `BIT_DEPTH_UNCONFIRMED` feuert seit dieser Version bei 8 Bit, nicht mehr bei 16 Bit |
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
SHA-256-Protokoll – noch nicht umgesetzt.

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
