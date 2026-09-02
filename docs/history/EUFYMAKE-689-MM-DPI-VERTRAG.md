# Ergebnisakte: EufyMake-mm/DPI-Vertrag (Issue #689)

Diese Akte trennt den reproduzierbaren Dateivertrag von Beobachtungen in
EufyMake Studio und von Messungen an einem physischen Druck. Sie ist das
Ergebnisdokument für
[#689](https://github.com/NikolayDA/picture_helper/issues/689), baut auf dem
[Annahmeninventar](EUFYMAKE-687-ANNAHMENINVENTAR.md) auf und verwendet die
[Protokollvorlagen](EUFYMAKE-687-PROTOKOLL-VORLAGEN.md).

## Status am 2026-09-02

- **Dateievidenz:** vollständig und automatisiert geprüft. Es gibt 36
  Einzel-Fixtures sowie ein echtes BgRemover-Exportpaket mit vier Dateien.
- **Studio-Beobachtung:** für Startgröße, DPI-Priorität, X/Y-DPI,
  Mehrfachimport, manuelle Größe und Rotation am 2026-09-02 durchgeführt.
  Der Crop ist vorbereitet, aber wegen seiner destruktiven Wirkung noch nicht
  angewendet. Alle Importe wurden vom Benutzer für die konkret benannten
  Dateien freigegeben.
- **Druckmessung:** offen. Es wurde kein Druck ausgelöst. Vor einem Druck sind
  die E1-Warnungen zu abgelaufenem Scraper, Luftfilter und gelber Tinte zu
  klären und die freigegebene Geräte-/Material-Governance anzuwenden.
- **Kanonischer Produktvertrag:** der Studio-Teil ist vorläufig festgelegt;
  Drucktoleranzen und der vollständige Produktvertrag bleiben bis zu
  freigegebenen, wiederholten Druckmessungen offen.

## Reproduzierbarer Sollsatz

Vertrauensanker des eingecheckten Satzes:

```text
fixtures_manifest.json
SHA-256 f9028246d0c07de185b032a11414ac06e64e8425798a59ad7d637501f663d585
Schema 3 · 36 Einzel-Fixtures · 1 Exportpaket
```

Prüfbefehl vor jedem Import:

```bash
python scripts/eufymake_fixture_inspector.py \
  --fixture-dir tests/fixtures/eufymake_hardware \
  --expected-manifest-sha256 f9028246d0c07de185b032a11414ac06e64e8425798a59ad7d637501f663d585 \
  --output eufymake-pre-import-report.json
```

Der Inspector liest die PNG-Struktur unabhängig vom Generator: IHDR,
Chunkfolge, CRC, `pHYs`, SHA-256 und Bytegröße. Für das Exportpaket validiert
er zusätzlich Dateiliste und Semantik des echten `manifest.json`.

### I-05: PNG-Auflösung bei konstantem Pixelmaß

| Variante | Pixelmaß | `pHYs` X/Y | Daraus folgende Größe X/Y | Zweck |
| --- | --- | --- | --- | --- |
| `mm_klein_no_phys.png` | 300×300 px | fehlt | ohne manuelle/Studio-Regel nicht bestimmt | Fallback bei fehlender Auflösung |
| `mm_klein_phys.png` | 300×300 px | ca. 150/150 dpi | 50,8×50,8 mm | konsistente Referenz |
| `mm_klein_phys_conflict.png` | 300×300 px | ca. 300/300 dpi | 25,4×25,4 mm | gleicher Pixelinhalt, widersprüchliche Auflösung |
| `mm_typisch_phys_xy.png` | 1200×1200 px | ca. 300/150 dpi | 101,6×203,2 mm | X/Y getrennt; Koppeln, Normalisieren oder Ablehnen sichtbar machen |

Die bereits vorhandenen kleinen, typischen und großen Reihen decken darüber
hinaus 300×300, 1200×1200 und 2400×1800 px bei 150/300/600 dpi ab. Für alle
Werte gilt die Referenzformel `mm = Pixel / DPI × 25,4`, auf drei
Nachkommastellen gerundet.

### I-06: Manifest gegen eingebettete PNG-Auflösung

`tests/fixtures/eufymake_hardware/export_mm_dpi_conflict/` wird zuerst über den
Produktionspfad `bgremover.eufymake_writer.write_export` erzeugt. Es enthält
die kanonischen Namen:

```text
color_motif.png
height_map.png
gloss_mask.png
manifest.json
```

Das BgRemover-Manifest fordert 256×256 px, 21,674666…×21,674666… mm und
300×300 dpi. Alle drei PNGs tragen anschließend für diesen kontrollierten
Widerspruch ca. 150×150 dpi im `pHYs`, entsprechend 43,349333… mm je Achse.
Das Paket variiert damit nur die konkurrierenden Größenquellen; Dateinamen,
Pixelmaß und Registriermarken bleiben konstant.

Der Einzeldateitest verwendet
`export_mm_dpi_conflict/manifest.json`, nicht das Provenienzmanifest
`fixtures_manifest.json`. Beim Ordnertest werden exakt die vier Dateien des
Unterordners verwendet.

### I-08: gemeinsame physische Ausdehnung und Registrierung

`color_height_reference.png`, `height_registration_16bit.png` und
`gloss_registration.png` sind jeweils 256×256 px. Jeder nicht-weiße
COLOR-Marker liegt pixelgenau auf einem HEIGHT-Wert 65535 und einem
GLOSS-Wert 255; der Hintergrund ist jeweils 0. Asymmetrische horizontale und
vertikale Marker machen Versatz, Crop, Rotation und Achsenvertauschung
sichtbar. Generator-Regressionstests vergleichen die drei Masken bitgenau.

## Mess- und Rundungsregel

Die drei Stufen werden getrennt ausgewertet:

1. **PNG-Metadaten:** `pHYs` speichert ganzzahlige Pixel pro Meter. Eine
   Rückrechnung darf deshalb um höchstens 0,02 dpi vom angeforderten Wert
   abweichen; das ist Formatquantisierung, keine Studio-Toleranz.
2. **Studio-Anzeige:** Exakten Anzeigetext, Dezimalstellen, Einheit und
   automatische Änderung protokollieren. Der Vergleich erfolgt gegen alle
   konkurrierenden Sollwerte. Als reine Rundungsabweichung gilt höchstens eine
   halbe Einheit der kleinsten angezeigten Dezimalstelle; größere Abweichungen
   sind Priorisierung, Skalierung oder ein Fehler und werden nicht weggerundet.
3. **Druck:** Breite und Höhe separat mit benanntem Messmittel protokollieren.
   Messunsicherheit, Rand-/Offsetmessung und Wiederholung werden als Rohwerte
   erfasst. Eine zulässige Drucktoleranz wird erst aus Geräteangabe und
   Wiederholungsstreuung begründet; bis dahin gibt es keinen erfundenen
   Pass/Fail-Grenzwert.

## Studio-Protokoll vom 2026-09-02

Testprofil: EufyMake Studio 4.2.2, Editor 1.20.0, E1 online, Standard Flatbed
335×420 mm. Die Firmware-Version wurde in der Sitzung nicht angezeigt und
deshalb nicht geraten. Es wurde kein Druck ausgelöst.

| Eingabe/Aktion | Exakte Studio-Beobachtung |
| --- | --- |
| `mm_typisch_no_phys.png`, 1200×1200 px, kein `pHYs` | Warnung wegen Überschreitung der Arbeitsfläche; nach „Originalgröße behalten“ 423,33×423,33 mm bei X/Y −44,17/−1,67 mm. Das entspricht 72 dpi und Zentrierung auf 335×420 mm. |
| `mm_typisch_phys.png`, ca. 300/300 dpi | 101,60×101,60 mm bei X/Y 116,70/159,19 mm; keine Warnung. |
| `mm_typisch_phys_conflict.png`, ca. 150/150 dpi | 203,18×203,18 mm bei X/Y 65,91/108,41 mm; keine Warnung. 203,18 mm statt nominal 203,20 mm folgt der ganzzahligen `pHYs`-Quantisierung. |
| `mm_typisch_phys_xy.png`, ca. 300/150 dpi | 101,60×203,18 mm bei X/Y 116,70/108,41 mm. X und Y werden getrennt ausgewertet. |
| `export_mm_dpi_conflict/manifest.json` | Im Bilddialog ausgegraut; „Öffnen“ bleibt deaktiviert. Das Manifest kann über diesen Importweg weder allein noch zusammen mit den PNGs importiert werden. |
| drei PNGs aus `export_mm_dpi_conflict/` | Einzeln und gemeinsam jeweils 43,35×43,35 mm bei X/Y 145,83/188,33 mm. Beim Mehrfachimport entstehen drei überlagerte, gewöhnliche „Flat“-Ebenen; Dateinamen erzeugen keine COLOR-/HEIGHT-/GLOSS-Zuordnung. Ein Wiederholungsimport lieferte dieselben Werte. |
| manuelle Größe auf einem ausgewählten Bundle-PNG | 21,67 mm Breite ergab bei gekoppeltem Seitenverhältnis 21,67 mm Höhe und überschreibt damit die Datei-Startgröße. Der Nullwertversuch wurde auf einen kleinen positiven Wert begrenzt; danach zeigte die Kopplung ein instabiles Verhältnis. Eine anschließende Breite von 1000 mm ergab 1000×1254,78 mm und X/Y −810,83/−1023,11 ohne Warnung. Der Ablauf ist ein Validierungs-Warnfall, kein belastbarer Extremwertvertrag. |
| I-08 `color_height_reference.png`, `height_registration_16bit.png`, `gloss_registration.png` | Alle drei Dateien ohne `pHYs` starteten einzeln mit 90,31×90,31 mm und X/Y 122,34/164,84 mm. Die gemeinsame Ausdehnung und Zentrierung bleiben erhalten; Studio ordnet die Rollen jedoch nicht automatisch zu, sondern importiert sie als „Flat“. |
| Rotation von `mm_typisch_phys_xy.png` um 90° | Die intrinsischen Felder bleiben 101,60×203,18 mm, Winkel 90°. Die sichtbare Bounding Box wird ohne Skalierung gedreht und auf X/Y 65,91/159,19 mm neu zentriert. |
| Crop-Vorschau | Auf der rotierten X/Y-Fixture ist eine Halbierung der intrinsischen Breite auf 50,80 mm bei 203,18 mm Höhe vorbereitet. Der destruktive „Crop“-Schritt wurde noch nicht bestätigt und nicht angewendet. |

## Empirischer Vertrag und offene Grenzen

| Frage | Studio-Beobachtung | Druckmessung | Vorläufige Vertragsentscheidung |
| --- | --- | --- | --- |
| Startgröße ohne `pHYs` | 72-dpi-Fallback; bei 1200×1200 px 423,33×423,33 mm und Überschreitungswarnung | offen | PNGs ohne `pHYs` dürfen nicht als physisch eindeutig gelten; Writer/Validator muss warnen oder eine explizite Zielgröße verlangen. |
| konsistentes `pHYs` | ca. 300/300 dpi ergeben 101,60×101,60 mm | offen | Studio verwendet PNG-`pHYs` für die Startgröße. |
| widersprüchliches `pHYs` bei konstanten Pixeln | ca. 150/150 dpi ergeben 203,18×203,18 mm | offen | Geändertes `pHYs` ändert die Startgröße; Quantisierung ist aus den gespeicherten Pixeln pro Meter zu berechnen. |
| nicht quadratische X/Y-DPI | 101,60×203,18 mm bei ca. 300/150 dpi | offen | Studio wertet beide Achsen unabhängig aus; Validator darf X/Y nicht still koppeln oder normalisieren. |
| Manifest 300 dpi gegen PNG 150 dpi | JSON im Bildimport nicht auswählbar; drei PNGs starten gemäß `pHYs` mit je 43,35 mm | offen | Für den beobachteten Bildimport hat das Manifest keine Wirkung. Ein anderer, ausdrücklich dokumentierter Paketimportweg wäre separat zu prüfen. |
| manuelle Studio-Größe gegen Dateiwerte | 21,67×21,67 mm überschreibt 43,35×43,35 mm | offen | Manuelle Größe hat nach dem Import Vorrang. Null-/Extremwerte benötigen produktseitige Grenzen und Warnungen; das Studio-Verhalten allein ist nicht sicher genug. |
| COLOR/HEIGHT/GLOSS-Ausdehnung und Registrierung | gleiche 90,31-mm-Ausdehnung und identische Zentrierung; alle Rollen als unabhängige „Flat“-Ebenen | offen | Gleiche Pixelmaße führen zur gleichen Startausdehnung. Semantische Zuordnung und pixelgenaue Registrierung im Produktionsmodus sind noch nicht belegt. |
| Crop, Rand, Offset, Zentrierung, Rotation | Zentrierung rechnerisch konsistent; 90° rotiert ohne Skalierung, W/H-Felder bleiben intrinsisch; Crop nur vorbereitet | offen | Rotation ist für dieses Profil belegt. Crop-Wirkung sowie Druckrand und physischer Offset bleiben offen. |

Für #691 darf der vorläufige Studio-Teilvertrag bereits als
Validierungsgrundlage dienen. Drucktoleranzen, Crop-Wirkung und semantische
Rollenregistrierung dürfen erst nach den noch offenen Realtests festgeschrieben
werden. Versionsabhängige Abweichungen sind gegen Studio 4.2.2 / Editor 1.20.0
zu bewerten.
