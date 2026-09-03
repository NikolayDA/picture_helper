# EufyMake-E1-Testdrucke auf A4-Karton

Dieser Ordner bereitet die noch offenen physischen Drucktests des Epics #681
als 13 A4-Layouts vor. Die Aufteilung hält die bereits festgelegten
Vergleichsgruppen zusammen und verändert keine der versionierten Testdateien.

## Fertiger Stand

- In jedem nummerierten Unterordner liegt genau eine gleichnamige `.empf`-Datei.
- Die Projekte sind selbstständig: COLOR-, HEIGHT- und Gloss-Daten sind jeweils
  als eigene native Ebene eingebettet.
- Alle Projekte liegen auf dem Standard-Flatbed des E1 (335 × 420 mm, in
  Studio 4.2.2 die Arbeitsfläche **Standard Flatbed**), A4 hochkant und mittig
  bei X = 62,50 mm / Y = 61,50 mm in Studio-Koordinaten (siehe *Feste Geometrie*).
- Die Projekte 04 (HEIGHT + Crop + Gloss), 05 (nur Gloss) und 06 (COLOR / mm-DPI)
  wurden in eufyMake Studio 4.2.2 mit Editor v1.20.0 geöffnet. Dabei wurden
  weder **Preview** noch **Print** ausgelöst.
- `projects.json` bindet jedes Projekt handgepflegt an Layout, Prüfsumme,
  eingebetteten Beschriftungsträger und Studio-Ebenen. Der Generator prüft
  diese Bindung fail-closed (siehe *Bindung und Neuerzeugung*), und
  `tests/test_eufymake_a4_layouts.py` hält den committeten Satz dagegen.
- Ein gegebenenfalls lokal vorhandener Ordner `_vorherige_studio_tabs` ist nur
  eine nicht versionierte Sicherung und gehört **nicht** zu den 13
  Druckprojekten.

## Vorgesehene Druckreihenfolge

| Projekt | Inhalt | Druck | A4-Kartons | Budgetzuordnung |
| --- | --- | --- | ---: | --- |
| 01 | I-02 / I-04 – HEIGHT-Pixelgröße | frei | 1 | I-02, I-04 |
| 02 | I-03 / I-14 – Bittiefe und Filterung | frei | 1 | I-03 8 Bit, I-03 16 Bit, I-14 |
| 03 | I-07 / I-11 / I-13 – Grenzen, Stufen, Alpha | frei, nur nicht-weißer Karton | 1 | I-07, I-11, I-13 |
| 04 | I-08 – Registrierung vor/nach Crop | frei | 1 | I-08 vor/nach Crop |
| 05 | I-10 – Gloss-Polarität | **gesperrt** bis Owner-Entscheidung | 1 | I-10 normal/invertiert |
| 06 | I-05 – mm/DPI-Referenz | frei | 1 | I-05 konsistent |
| 07 | G-01 / G-03 – Gloss-Grenzen und Kennlinie | frei | 1 | G-01, G-03 |
| 08 | G-02 – Gloss-Polarität (zweimal drucken) | frei | **2** | normal/invertiert jeweils Lauf 1+2 |
| 09 | G-04 – fehlend / Null / Voll | frei | 1 | G-04a/b/c |
| 10 | G-05 – abweichende Gloss-Dimension | frei | 1 | G-05 |
| 11 | G-06 – Alpha × Gloss | frei, nur nicht-weißer Karton | 1 | G-06 |
| 12 | G-07 – HEIGHT × Gloss | frei | 1 | G-07 |
| 13 | G-08 – Registrierung und Mindeststruktur | frei | 1 | G-08 |

Damit werden für die Erstläufe 14 A4-Kartons eingeplant; 13 davon sind sofort
druckbar. Karton 05 bleibt gesperrt, bis der Freigabe-Vermerk zur
Owner-Entscheidung I-10 gegen G-02 in
`docs/history/EUFYMAKE-687-TESTGOVERNANCE.md` §4 vorliegt (Optionen in §5.3
dort und in `docs/history/EUFYMAKE-687-DRUCK-CHECKLISTE.md` §0): Unter
Option A wird I-10 gar nicht gedruckt; unter Option B gehört I-10 zum
Spot-UV-Zweipass (Pfad 2), und Projekt 05 ist dafür neu aufzubauen. Es enthält
heute den nativen Gloss-Varnish-Pfad und würde G-02 nur wiederholen. Die
Sperre steht auch im Feld `print_blocked` der Aufbau-JSON.

Ein Karton mit mehreren Feldern verbraucht im 35er-Testbudget weiterhin die
Budgetplätze aller darauf enthaltenen Varianten. Projekt 08 wird auf zwei
**verschiedenen** Kartons gedruckt; ein zweiter Durchlauf auf demselben Karton
ist keine unabhängige Wiederholung.

## Substrat

- Karton 03 (wegen I-13) und Karton 11 (G-06) werden auf demselben, in
  `docs/history/EUFYMAKE-687-PROTOKOLL-VORLAGEN.md` §3.0 eingetragenen
  **nicht-weißen** Substrat gedruckt: Deckung und Weiß-Unterlage der
  Alpha-Felder 0/128/255 bleiben auf weißem Material unsichtbar
  (Druck-Checkliste §0, Gloss-Vertrag „Substrat für G-06"). Die Vorgabe steht
  je Layout im Feld `substrate` der Aufbau-JSON.
- Innerhalb eines Vergleichs bleibt das Substrat identisch; für die übrigen
  Kartons gilt der in §3.0 festgelegte Karton.

## Feste Geometrie

- Bezugssystem aller Studio-Koordinaten (`e1_flatbed_geometry_mm`) ist das
  Standard-Flatbed des E1 mit **335 × 420 mm** (`STANDARD_FLATBED_MM` in
  `bgremover/eufymake_export.py`, vom Owner am 2026-09-03 bestätigt). Es ist
  dieselbe Fläche, die Studio 4.2.2 als Arbeitsfläche „Standard Flatbed“
  anzeigt; belegt ist das Maß zusätzlich durch die Zentrierung eines
  101,60-mm-Objekts auf X = 116,70 mm im Studio-Protokoll vom 2026-09-02/03
  (`docs/history/EUFYMAKE-689-MM-DPI-VERTRAG.md`).
- Die 13 Projekte sind auf genau dieser Fläche gebaut. Ändert sich die
  Konstante, bricht der Generator ab, statt die Aufbau-JSONs still von den
  realen Studio-Koordinaten der Projekte zu entkoppeln.
- A4 hochkant, exakt mittig auf dem Flatbed: Ursprung
  X = 62,50 mm, Y = 61,50 mm; A4-Rand X = 62,50…272,50 mm, Y = 61,50…358,50 mm.
- Rotation aller Objekte: 0°. Keine automatische Skalierung; die in
  `layout_manifest.json` hinterlegten Maße und Positionen gelten verbindlich.
- G-05: Die 45,16 × 90,31 mm große Glossmaske bleibt nativ und liegt oben und
  links bündig auf dem 90,31 × 90,31 mm großen COLOR-Feld. Die rechte Hälfte
  bleibt ohne Glossobjekt.
- I-08 nach Crop: Das COLOR/HEIGHT-Objekt behält die rechte Bildhälfte und ist
  mit 44,86 × 90,31 mm rechtsbündig im unveränderten Glossfeld platziert.
  `crop_fraction` `[0.5, 0, 1, 1]` beschreibt diese Hälfte nur für die
  Vorschau; der Crop selbst geschieht in Studio.

## Dateien je Projekt

- `NN_name/NN_name.empf` ist das fertige, direkt in eufyMake Studio zu öffnende
  Druckprojekt. Nur diese Datei wird zum Drucken benötigt.
- `*_A4_Beschriftung.png` ist der transparente, exakt 210 × 297 mm große
  Beschriftungs- und Eckmarkenträger. Er wird im nativen Studio-Projekt als
  COLOR-Ebene „A4 Beschriftung und Eckmarken" mitgeführt und ist damit an die
  `.empf` gebunden (siehe *Bindung und Neuerzeugung*).
- `*_NUR_VORSCHAU.png` zeigt die geplante Platzierung. Gloss-Felder über
  COLOR-/HEIGHT-Feldern sind gedämpft gezeichnet, die Glossform bleibt dabei
  sichtbar; 16-Bit-Höhen sind auf die Anzeige skaliert. Diese Datei darf
  **nicht** anstelle der nativen HEIGHT-/Gloss-Objekte gedruckt werden.
- `*_Aufbau.json` enthält jede Quelldatei mit SHA-256 (beim Erzeugen gegen
  `tests/fixtures/eufymake_hardware/fixtures_manifest.json` geprüft), Rolle,
  A4-Position, Studio-Position, Größe, Ink Mode sowie `crop_fraction`,
  `print_blocked` und `substrate`.
- `projects.json` ist die **handgepflegte** Bindung: je Projekt Pfad, SHA-256,
  SHA-256 des eingebetteten Trägers und die Studio-Ebenen; dazu
  `carrier_font` und `project_format`. Nach jedem Neuaufbau in Studio wird sie
  bewusst nachgezogen.
- `layout_manifest.json` bündelt alle 13 Projekte samt Bezugsflächen, Quellen
  und Bindungsregel.

## Bindung und Neuerzeugung

Erzeugt wird der Satz mit `python scripts/prepare_eufymake_a4_layouts.py`
(Linux und macOS; Schrift Arial unter macOS, sonst Liberation Sans oder
DejaVu Sans – der Lauf nennt die verwendete Schrift). Der Generator

1. prüft **vor dem ersten Schreibzugriff** alle Quelldateien gegen
   `fixtures_manifest.json` und jedes Projekt gegen `projects.json` (Pfad,
   SHA-256, Studio-Ebenen, eingebetteter Träger) und bricht bei jeder
   Abweichung ab;
2. schreibt Aufbau-JSONs, Vorschauen und Manifest neu;
3. lässt die gebundenen Träger unverändert, wenn der gerenderte Träger davon
   abweicht (etwa durch eine andere Schrift oder eine geänderte Beschriftung),
   und meldet das als Hinweis.

`--check` prüft den committeten Stand ohne Schreibzugriff und ohne Schrift
(so läuft es im Test). `--rebuild-carriers` überschreibt abweichende Träger
bewusst; danach in Studio die Ebene „A4 Beschriftung und Eckmarken" der
betroffenen Projekte ersetzen, speichern und in `projects.json`
`project_sha256`, `carrier_sha256` und `carrier_font` nachziehen. Bis dahin
bricht jeder Lauf ohne `--rebuild-carriers` ab; ein Manifest kann so keinen
Träger behaupten, den die `.empf` nicht enthält.

**Offener Nachzug (Stand 2026-09-03):** Die gebundenen Träger 04 und 10
stammen noch aus dem Stand, in dem ein späterer Beschriftungskasten eine
frühere Zeile übermalte (bei 10 fehlt „G-05 · COLOR 256×256", bei 04
„I-08 · nach Crop"). Der Generator setzt kollidierende Zeilen jetzt versetzt.
Die beiden Träger sind unter macOS mit `--rebuild-carriers` neu zu erzeugen,
die Projekte 04 und 10 in Studio neu aufzubauen und `projects.json` ist
nachzuziehen; danach diesen Absatz entfernen.

## Vor jedem Drucktag

1. Voraussetzungen aus `docs/history/EUFYMAKE-687-DRUCK-CHECKLISTE.md` §0
   erledigt: Owner-Entscheidung I-10 gegen G-02 (sonst bleibt Projekt 05
   gesperrt), Substrat und Messmittel in
   `docs/history/EUFYMAKE-687-PROTOKOLL-VORLAGEN.md` §3.0 eingetragen, und
   `python scripts/prepare_eufymake_a4_layouts.py --check` läuft grün.
2. Nur exakt die vorbereitete `.empf`-Datei öffnen.
3. Kurz warten, bis alle Ebenen und der Bereich **Print area** vollständig
   geladen sind. Reine Glossfelder können auf der Arbeitsfläche sehr blass oder
   unsichtbar erscheinen; maßgeblich sind ihre Ebenen und der Ink Mode
   **Gloss Varnish × 1**.
4. **Vorschau-Preflight (Phase 2b, Druck-Checkliste §4.1) vor dem ersten
   Druck:** erst nach ausdrücklicher Owner-Freigabe die Vorschau (`Preview`)
   nur bis zur Druckvorbereitungsseite öffnen und je Druckvariante Warnungen,
   Objektmaße und Position, Ink Mode, Texturhöhe sowie, falls angezeigt,
   geschätzte Druckzeit und Tintenmenge in Protokoll §3.1 eintragen. Eine
   Warnung sperrt die Variante bis zur Klärung; `Print` wird in diesem Schritt
   nie ausgelöst.
5. Den passenden, für den verwendeten A4-Karton sicheren Material-/Geräte-
   profilwert wählen und für alle Vergleichsprojekte unverändert lassen;
   Karton 03 und 11 nur auf dem eingetragenen nicht-weißen Substrat.
6. Prüfen, dass der Karton hochkant mittig und plan aufliegt.
7. Projekt 08 beim zweiten Lauf auf einen neuen Karton drucken; dafür dieselbe
   `.empf`-Datei unverändert ein zweites Mal öffnen bzw. verwenden.
8. Druck nicht unbeaufsichtigt lassen; bei Fehler, ungewöhnlichem Geräusch,
   Geruch oder Übertemperatur abbrechen und nicht automatisch wiederholen.

Die Vorschau- und Aufbauhilfen ersetzen nicht das Mess- und Fotoprotokoll in
`docs/history/EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`.
