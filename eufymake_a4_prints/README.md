# EufyMake-E1-Testdrucke auf A4-Karton

Dieser Ordner bereitet die noch offenen physischen Drucktests des Epics #681
als 13 A4-Layouts vor. Die Aufteilung hält die bereits festgelegten
Vergleichsgruppen zusammen und verändert keine der versionierten Testdateien.

## Fertiger Stand

- In jedem nummerierten Unterordner liegt genau eine gleichnamige `.empf`-Datei.
- Die Projekte sind selbstständig: COLOR-, HEIGHT- und Gloss-Daten sind jeweils
  als eigene native Ebene eingebettet.
- Alle Projekte verwenden das 335 × 420 mm große Standard-Flatbed, A4 hochkant
  und mittig bei X = 62,50 mm / Y = 61,50 mm.
- Die Projekte 04 (HEIGHT + Crop + Gloss), 05 (nur Gloss) und 06 (COLOR / mm-DPI)
  wurden in eufyMake Studio 4.2.2 mit Editor v1.20.0 geöffnet. Dabei wurden
  weder **Preview** noch **Print** ausgelöst.
- Der vollständige Satz wurde zusätzlich auf Containerstruktur, eingebettete
  Quelldateien und Prüfsummen, Ebenenrollen, Maße, Positionen und
  HEIGHT-/Gloss-Einstellungen geprüft.
- Ein gegebenenfalls lokal vorhandener Ordner `_vorherige_studio_tabs` ist nur
  eine nicht versionierte Sicherung und gehört **nicht** zu den 13
  Druckprojekten.

## Vorgesehene Druckreihenfolge

| Projekt | Inhalt | A4-Kartons | Budgetzuordnung |
| --- | --- | ---: | --- |
| 01 | I-02 / I-04 – HEIGHT-Pixelgröße | 1 | I-02, I-04 |
| 02 | I-03 / I-14 – Bittiefe und Filterung | 1 | I-03 8 Bit, I-03 16 Bit, I-14 |
| 03 | I-07 / I-11 / I-13 – Grenzen, Stufen, Alpha | 1 | I-07, I-11, I-13 |
| 04 | I-08 – Registrierung vor/nach Crop | 1 | I-08 vor/nach Crop |
| 05 | I-10 – Gloss-Polarität | 1 | I-10 normal/invertiert |
| 06 | I-05 – mm/DPI-Referenz | 1 | I-05 konsistent |
| 07 | G-01 / G-03 – Gloss-Grenzen und Kennlinie | 1 | G-01, G-03 |
| 08 | G-02 – Gloss-Polarität | **2** | normal/invertiert jeweils Lauf 1+2 |
| 09 | G-04 – fehlend / Null / Voll | 1 | G-04a/b/c |
| 10 | G-05 – abweichende Gloss-Dimension | 1 | G-05 |
| 11 | G-06 – Alpha × Gloss | 1 | G-06 |
| 12 | G-07 – HEIGHT × Gloss | 1 | G-07 |
| 13 | G-08 – Registrierung/Mindeststruktur | 1 | G-08 |

Damit werden für die Erstläufe 14 A4-Kartons benötigt. Ein Karton mit mehreren
Feldern verbraucht im 35er-Testbudget weiterhin die Budgetplätze aller darauf
enthaltenen Varianten. Projekt 08 wird auf zwei **verschiedenen** Kartons
gedruckt; ein zweiter Durchlauf auf demselben Karton ist keine unabhängige
Wiederholung.

## Feste Geometrie

- A4 hochkant, exakt mittig auf dem 335 × 420 mm großen E1-Flatbed.
- A4-Ursprung im Studio: X = 62,50 mm, Y = 61,50 mm.
- A4-Rand im Flatbed: X = 62,50…272,50 mm, Y = 61,50…358,50 mm.
- Rotation aller Objekte: 0°.
- Keine automatische Skalierung; die in `layout_manifest.json` hinterlegten
  Maße und Positionen gelten verbindlich.
- G-05: Die 45,16 × 90,31 mm große Glossmaske bleibt nativ und liegt oben und
  links bündig auf dem 90,31 × 90,31 mm großen COLOR-Feld. Die rechte Hälfte
  bleibt ohne Glossobjekt.
- I-08 nach Crop: Das COLOR/HEIGHT-Objekt behält die rechte Bildhälfte und ist
  mit 44,86 × 90,31 mm rechtsbündig im unveränderten Glossfeld platziert.

## Dateien je Projekt

- `NN_name/NN_name.empf` ist das fertige, direkt in eufyMake Studio zu öffnende
  Druckprojekt. Nur diese Datei wird zum Drucken benötigt.
- `*_A4_Beschriftung.png` ist der transparente, exakt 210 × 297 mm große
  Beschriftungs- und Eckmarkenträger. Er wird im nativen Studio-Projekt als
  COLOR-Objekt mitgeführt.
- `*_NUR_VORSCHAU.png` zeigt die geplante Platzierung. Diese Datei darf
  **nicht** anstelle der nativen HEIGHT-/Gloss-Objekte gedruckt werden.
- `*_Aufbau.json` enthält jede Quelldatei mit SHA-256, Rolle, A4-Position,
  Flatbed-Position, Größe und Ink Mode.
- `layout_manifest.json` bündelt alle 13 Projekte.
- Die fertigen `*.empf`-Dateien sind selbstständige eufyMake-Studio-Projekte;
  sie betten die Quellbilder und Einstellungen ein.

## Vor jedem Drucktag

1. Nur exakt die vorbereitete `.empf`-Datei öffnen.
2. Kurz warten, bis alle Ebenen und der Bereich **Print area** vollständig
   geladen sind. Reine Glossfelder können auf der Arbeitsfläche sehr blass oder
   unsichtbar erscheinen; maßgeblich sind ihre Ebenen und der Ink Mode
   **Gloss Varnish × 1**.
3. Den passenden, für den verwendeten A4-Karton sicheren Material-/Geräte-
   profilwert wählen und für alle Vergleichsprojekte unverändert lassen.
4. Prüfen, dass der Karton hochkant mittig und plan aufliegt.
5. Projekt 08 beim zweiten Lauf auf einen neuen Karton drucken; dafür dieselbe
   `.empf`-Datei unverändert ein zweites Mal öffnen bzw. verwenden.
6. Druck nicht unbeaufsichtigt lassen; bei Fehler, ungewöhnlichem Geräusch,
   Geruch oder Übertemperatur abbrechen und nicht automatisch wiederholen.

Die Vorschau- und Aufbauhilfen ersetzen nicht das Mess- und Fotoprotokoll in
`docs/history/EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`.
