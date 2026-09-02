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
- **Studio-Beobachtung:** offen. Ein Import ist eine externe Dateiübertragung
  und wird erst nach ausdrücklicher Bestätigung der konkreten Dateien
  durchgeführt.
- **Druckmessung:** offen. Es wurde kein Druck ausgelöst. Vor einem Druck sind
  die E1-Warnungen zu abgelaufenem Scraper, Luftfilter und gelber Tinte zu
  klären und die freigegebene Geräte-/Material-Governance anzuwenden.
- **Kanonischer Produktvertrag:** noch nicht festlegbar. Ohne Studio- und
  Druckevidenz darf weder Manifest-, `pHYs`- noch manuelle Priorität behauptet
  werden.

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

## Noch zu füllender empirischer Vertrag

| Frage | Studio-Beobachtung | Druckmessung | Vertragsentscheidung |
| --- | --- | --- | --- |
| Startgröße ohne `pHYs` | offen | offen | offen |
| konsistentes `pHYs` | offen | offen | offen |
| widersprüchliches `pHYs` bei konstanten Pixeln | offen | offen | offen |
| nicht quadratische X/Y-DPI | offen | offen | offen |
| Manifest 300 dpi gegen PNG 150 dpi | offen | offen | offen |
| manuelle Studio-Größe gegen Dateiwerte | offen | offen | offen |
| COLOR/HEIGHT/GLOSS-Ausdehnung und Registrierung | offen | offen | offen |
| Crop, Rand, Offset, Zentrierung, Rotation | offen | offen | offen |

Nach den Realtests muss jede Zeile genau eine beobachtete Priorität oder eine
explizite Profilgrenze nennen. Erst dann dürfen Validator, Writer und Dialog
im Integrations-Issue #691 gehärtet werden.
