# Protokollvorlagen für EufyMake-Hardware-Tests (Issue #687)

Ausfüllbare Vorlagen für die Realtests aus #688 (HEIGHT), #689 (mm/DPI) und
#690 (Gloss), Epic [#681](https://github.com/NikolayDA/picture_helper/issues/681).
Sie setzen die letzten drei mit Hardware durchführbaren Akzeptanzkriterien von
#687 um: ein Dateivalidierungs-, ein Import- und ein Druckprotokoll. Die
Fixtures selbst kommen aus
[`scripts/eufymake_fixture_generator.py`](../../scripts/eufymake_fixture_generator.py)
(`python scripts/eufymake_fixture_generator.py generate`), abgelegt unter
[`tests/fixtures/eufymake_hardware/`](../../tests/fixtures/eufymake_hardware/)
mit SHA-256 je Datei in `fixtures_manifest.json`. Die Testzellen I-01 bis I-10
und ihre ursprüngliche Bedeutung stehen im
[Annahmeninventar](EUFYMAKE-687-ANNAHMENINVENTAR.md), Abschnitt „Testmatrix"
(V1) bzw. „Aktualisierte Testmatrix" (V2). **I-11 bis I-13 sind dort erst in
Nachträgen gelistet**: I-11 und I-12 wurden ergänzt, um die im
Annahmeninventar (Abschnitt 3)
ausdrücklich als offen markierten Fragen H-02 (Graustufe→mm-Kennlinie,
Treppenkeil) und H-03 (Verhalten bei abweichendem Höhenkarten-Seitenverhältnis)
mit einer konkreten, druckbaren Testzelle zu versehen; beide hatten bis dahin
weder Fixture-Zuordnung noch Protokollzeile. I-13 schließt die in #688
geforderte Alpha/Coverage-Kreuzung mit einer konstanten, nicht-null HEIGHT-Map.

Für den eigentlichen Testtag bündelt
[`EUFYMAKE-687-DRUCK-CHECKLISTE.md`](EUFYMAKE-687-DRUCK-CHECKLISTE.md) die
Reihenfolge dieser drei Protokolle mit dem Budget-Fortschritt und den
Sicherheitsregeln aus der Governance an einer Stelle – die Protokolltabellen
hier bleiben die Datenquelle. Die #688-Ergebnisse werden anschließend ohne
Vermischung der Evidenzarten in
[`EUFYMAKE-688-HEIGHT-VERTRAG.md`](EUFYMAKE-688-HEIGHT-VERTRAG.md)
zusammengeführt; für #689 übernimmt dies
[`EUFYMAKE-689-MM-DPI-VERTRAG.md`](EUFYMAKE-689-MM-DPI-VERTRAG.md).

**Hinweis zu pHYs/DPI:** PNGs `pHYs`-Chunk speichert Pixel je Meter als
Ganzzahl; der Rückweg zu DPI rundet deshalb minimal (< 0,01 %, z. B. 150 dpi →
angezeigt ggf. 150,012). Das ist ein Format-Artefakt, kein Fehler der
Fixture-Erzeugung.

## Testzellen-Referenz (aus dem Annahmeninventar)

| Zelle | Eingabe | Variierter Faktor | Ziel-Issue |
| --- | --- | --- | --- |
| I-01 | `color_motif.png` allein | – | #689 |
| I-02 | `color_height_reference.png` + `height_wedge_16bit.png` | Höhenkarte zugeordnet | #688 |
| I-03 | Höhenkarte 8 Bit vs. 16 Bit, identisches Motiv | Bittiefe | #688 |
| I-04 | Höhenkarte mit halber Kantenlänge | Pixelmaß | #688/#689 |
| I-05 | PNG mit `pHYs` konsistent vs. widersprüchlich vs. ohne sowie X/Y-DPI 300/150 | `pHYs` und Achse | #689 |
| I-06 | `export_mm_dpi_conflict/manifest.json` allein und kompletter Vier-Dateien-Exportordner | Träger/Priorität | #687/#689 |
| I-07 | Vollweiße Höhenkarte | Sättigung | #688 |
| I-08 | `color_height_reference.png`, `height_registration_16bit.png` und `gloss_registration.png` vor/nach Crop in Studio | Crop/Registrierung | #689/#690 |
| I-09 | Legacy-`.empf` vs. aktuell exportiertes `.empf` | Containergeneration | #687 |
| I-10 | Gloss-Maske schwarz/weiß invertiert | Polarität | #690 |
| I-11 | Höhenkarte mit Treppenkeil (bekannte, diskrete Stufen) | Graustufe→mm-Kennlinie (H-02) | #688 |
| I-12 | Höhenkarte mit abweichendem Seitenverhältnis (256×128 statt 256×256) | Seitenverhältnis (H-03) | #688 |
| I-13 | RGBA mit 0/50/100 % Alpha + konstante nicht-null HEIGHT | Alpha/Coverage | #688 |

---

## 1. Dateivalidierungsprotokoll

Vor **jedem** Import in EufyMake Studio: Datei unabhängig von der App prüfen
und mit `fixtures_manifest.json` abgleichen, **bevor** Studio die Datei sieht.
Der reproduzierbare Standardaufruf am Zielrechner ist:

```bash
python scripts/eufymake_fixture_inspector.py \
  --fixture-dir tests/fixtures/eufymake_hardware \
  --expected-manifest-sha256 be71d47fe0f4aab8a80aedd181a91ecf611087840216b2e4f0cf1dda79d2de5c \
  --output eufymake-pre-import-report.json
```

Der Report liest SHA-256, Bytegröße, Pillow-Lesbarkeit/-Version,
IHDR-Bittiefe/-Farbtyp, vollständige Chunkfolge, `pHYs` und Chunk-CRCs direkt
aus den übertragenen Dateien. Der Pillow-Modus ist nur ein Diagnosefeld; die
Formatentscheidung beruht auf IHDR. Der im Befehl fest vorgegebene
Manifest-SHA bindet das kopierte Verzeichnis an den versionierten Sollsatz.
Nur Exitcode 0, `"ok": true`, Manifest-Schema 4 und derselbe Soll-Hash erlauben
den anschließenden Import; der Report wird mit den Nachweisen abgelegt.

**Repository-Gesamtprüfung (2026-09-02, automatisiert, kein Studio-Zugriff):**
Alle 36 im Repository committeten Einzel-Fixtures und das Vier-Dateien-
Exportpaket wurden direkt gegen `fixtures_manifest.json` geprüft – SHA-256
der Datei, Bytegröße, PNG-Modus/
IHDR-Bittiefe/-Farbtyp, Maße sowie eine vollständige Chunk-Liste (per
struct-Parsing der PNG-Bytes, nicht nur über PIL). Ergebnis: **41/41
Einzel-Fixtures und 7/7 Exportpakete stimmen mit dem Manifest überein**;
keine PNG-Datei enthält
Chunks außer `IHDR`/`IDAT`/`IEND` und – wo im Manifest dokumentiert –
`pHYs`. Das ersetzt **nicht** die Prüfung unmittelbar vor dem Import bei dir
(falls die Dateien z. B. per USB/Cloud auf einen anderen Rechner übertragen
wurden, dort den Inspector erneut ausführen) – es bestätigt nur, dass
der Ausgangszustand im Repository korrekt ist, bevor du davon kopierst.

**Ergänzung (I-04-Pixelmaß-Variante, nach der Basisprüfung hinzugekommen):**
`height_wedge_16bit_half.png` (128×128, präzisionserhaltend aus
`height_wedge_16bit.png` resized über `bgremover.height_map.resize_height_field`
– derselbe Pfad, den die App für Höhenfelder verwendet, siehe
`scripts/eufymake_fixture_generator.py`) war **nicht** Teil der ursprünglichen
manuellen Struct-Parsing-Session vom 15. August. In der Gesamtprüfung ist sie
durch den Inspector und die Generator-Regressionstests abgesichert
(`tests/test_eufymake_fixture_generator.py::test_checked_in_fixtures_match_current_generator`
und `::test_pixel_size_variant_fixture_is_precision_preserving_half_size`,
Letzterer prüft die Pixelwerte explizit gegen eine unabhängig berechnete
Erwartung). Damit entfällt der bisherige manuelle Erzeugungsschritt für I-04.

**Ergänzung (I-11/I-12, Matrixerweiterung):** `height_steps_8bit.png`/
`height_steps_16bit.png` (bereits vorhandene, bis dahin keiner Zelle
zugeordnete Fixtures – siehe „Zusätzliche Fixtures" unten, wo sie jetzt nicht
mehr stehen) sind ab sofort I-11 zugeordnet. `height_wedge_16bit_aspect.png`
(256×128, **bewusst kein** Resize eines quadratischen Musters, sondern direkt
bei Zielgröße neu erzeugt – siehe Modul-Docstring in
`scripts/eufymake_fixture_generator.py`) ist neu und deckt I-12 ab. Beide
sind über dieselben Generator-Regressionstests abgesichert wie die
I-04-Variante (`tests/test_eufymake_fixture_generator.py`, dort
`test_aspect_ratio_variant_fixture_has_genuinely_different_ratio` für I-12).

**Ergänzung (#688-Vorbereitung, I-02/I-08/I-13):**
`color_height_reference.png` ist 256×256 px groß und damit dimensionsgleich
zu `height_wedge_16bit.png` (I-02). Für I-08 bildet
`height_registration_16bit.png` alle nicht-weißen, asymmetrischen
COLOR-Landmarks pixelgenau als 0/65535-Relief ab; dadurch wird ein Versatz auf
X und Y nach Crop sichtbar. `color_alpha_coverage.png` enthält bei konstantem
RGB-Payload 40/80/220 drei Felder mit Alpha 0/128/255 und wird in I-13 mit der
durchgehend nicht-null `height_mean_16bit.png` (digitaler Wert 32768)
kombiniert. Die Generator-Tests prüfen Landmarks, Feldgrenzen, Alphawerte,
identische Maße sowie konstante RGB- und HEIGHT-Werte bitgenau.

**Ergänzung (#689-Vorbereitung, I-05/I-06/I-08):**
`mm_typisch_phys_xy.png` trägt getrennte X-/Y-Werte von ca. 300/150 dpi.
Der Unterordner `export_mm_dpi_conflict/` stammt aus dem produktiven
BgRemover-Writer und enthält die kanonischen vier Paketdateien; sein
`manifest.json` fordert 300×300 dpi, während die drei PNGs 150×150 dpi im
`pHYs` tragen. `gloss_registration.png` ergänzt die I-08-Landmarks zur
pixelgleichen COLOR/HEIGHT/GLOSS-Dreiergruppe. Der Inspector prüft
nicht-quadratische `pHYs` achsweise und das Exportmanifest zusätzlich
semantisch. Das Katalogmanifest `fixtures_manifest.json` ist weiterhin nur
der Vertrauensanker und **kein** Studio-Eingabemanifest.

**Ergänzung (#690-Vorbereitung, G-01…G-08):** Fünf neue Einzel-Fixtures
ergänzen Mittelwert, begrenzten 64…192-Keil, dimensionsfremdes Gloss sowie
die isolierte HEIGHT×Gloss-Kontrolle. Sechs zusätzliche Writer-Pakete trennen
fehlendes, Null- und voll gesetztes Gloss, Alpha×Gloss, HEIGHT×Gloss und den
kontrollierten Dimensionsfehler. Die vollständige Zuordnung und die
Import-/Druckgrenzen stehen in
[`EUFYMAKE-690-GLOSS-VERTRAG.md`](EUFYMAKE-690-GLOSS-VERTRAG.md).

**Wichtiger Befund dabei:** Mehrere Fixtures mit unterschiedlicher **Rolle**
sind **bytegleich**, weil sie denselben normalisierten Muster-Generator bei
gleicher Größe/Bittiefe/PNG-Modus verwenden: `gloss_min.png` ↔
`height_zero_8bit.png`, `gloss_max.png` ↔ `height_max_8bit.png`,
`gloss_steps.png` ↔ `height_steps_8bit.png`, `gloss_wedge.png` ↔
`height_wedge_8bit.png`, `gloss_wedge_inverted.png` ↔
`height_wedge_inverted_8bit.png` (jeweils identischer SHA-256). Der
SHA-256 allein identifiziert also **nicht** die Rolle einer Datei – beim
Import (insbesondere I-06, kompletter Ordner) immer zusätzlich den
Dateinamen prüfen, nicht nur den Hash.

| Testzelle | Fixture-Datei | Erwarteter SHA-256 (aus Manifest) | Tatsächlicher SHA-256 | Rolle | PNG-Modus | Bittiefe | `pHYs` vorhanden/Wert | Sonstige relevante Chunks | Ergebnis (OK/Abweichung) | Anmerkung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| I-01 | `mm_typisch_phys.png` | `e6db39fc9e98bef6df6783214a2e19cdca051f0ed42ef0dfb7ef029d206e2740` | `e6db39fc9e98bef6df6783214a2e19cdca051f0ed42ef0dfb7ef029d206e2740` | color_motif | RGBA | 8 Bit | vorhanden (11811×11811 px/m ≈ 299.999×299.999 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | |
| I-02 | `color_height_reference.png` | `8f8cdc241d084ee84ce91cda584cdd826356076a0b831876996345bd59b19493` | `8f8cdc241d084ee84ce91cda584cdd826356076a0b831876996345bd59b19493` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | 256×256, voll opak; dimensionsgleich zur HEIGHT-Referenz |
| I-02 | `height_wedge_16bit.png` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-03 (8 Bit) | `height_wedge_8bit.png` | `c908eb760796043c54c42ddc167defcd6b2d489af96667a81bf18aa03da020e8` | `c908eb760796043c54c42ddc167defcd6b2d489af96667a81bf18aa03da020e8` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_wedge.png` – siehe Hinweis oben |
| I-03 (16 Bit) | `height_wedge_16bit.png` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-04 (Referenz) | `height_wedge_16bit.png` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-04 (halbierte Kopie) | `height_wedge_16bit_half.png` | `61f4bea48ec290021db7110d55d49281c0ee9dacca54d424a444e95c8709120b` | `61f4bea48ec290021db7110d55d49281c0ee9dacca54d424a444e95c8709120b` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | 128×128, präzisionserhaltend aus `height_wedge_16bit.png` resized (siehe Ergänzung oben); gleiches Seitenverhältnis wie die 256×256-Referenz |
| I-05 (ohne `pHYs`) | `mm_klein_no_phys.png` | `6eabe8ece8b79a3836e44a710263ad64c1c119432c755e89cbf3252d1dce25e0` | `6eabe8ece8b79a3836e44a710263ad64c1c119432c755e89cbf3252d1dce25e0` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-05 (konsistent) | `mm_klein_phys.png` | `37a78c832895222f3ee659f64589fc9096f9e8925c6058f65394db6e1cfb37c8` | `37a78c832895222f3ee659f64589fc9096f9e8925c6058f65394db6e1cfb37c8` | color_motif | RGBA | 8 Bit | vorhanden (5906×5906 px/m ≈ 150.012×150.012 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | 150 dpi → 150,012 ist Rundungsartefakt des `pHYs`-Ganzzahlformats, kein Fehler |
| I-05 (widersprüchlich) | `mm_klein_phys_conflict.png` | `1e02f7004559030c7aa859a2c34ecbd7bfce9c4f786a4406eb0b5b5b69fba983` | `1e02f7004559030c7aa859a2c34ecbd7bfce9c4f786a4406eb0b5b5b69fba983` | color_motif | RGBA | 8 Bit | vorhanden (11811×11811 px/m ≈ 299.999×299.999 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | Pixelmaß wie `mm_klein_*`, `pHYs` bewusst auf 300 statt 150 dpi gesetzt |
| I-05 (X/Y getrennt) | `mm_typisch_phys_xy.png` | `525fc2c88875c5c7bb53e73f169964173fabd66470d2d1ee74b29fcdfae6382f` | `525fc2c88875c5c7bb53e73f169964173fabd66470d2d1ee74b29fcdfae6382f` | color_motif | RGBA | 8 Bit | vorhanden (11811×5906 px/m ≈ 299.999×150.012 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | 1200×1200 px; `pHYs` impliziert 101,600×203,183 mm und prüft beide Achsen getrennt |
| I-06 (`manifest.json` allein) | `export_mm_dpi_conflict/manifest.json` | `23dc74b2ea547ed8708cff59f5abcb08658457d71b1756f9abdc2e40fa3ffb7b` | `23dc74b2ea547ed8708cff59f5abcb08658457d71b1756f9abdc2e40fa3ffb7b` | – | JSON | – | Manifest: 300×300 dpi, 21,674666… mm | – | ✅ OK (Hash + Semantik) | Echtes BgRemover-Exportmanifest; **nicht** `fixtures_manifest.json` |
| I-06 (kompletter Ordner) | exakt vier Dateien in `export_mm_dpi_conflict/` | siehe Bundle-Einträge in `fixtures_manifest.json` | siehe Bundle-Einträge in `fixtures_manifest.json` | COLOR/HEIGHT/GLOSS + Manifest | RGBA/I;16/L/JSON | 8/16/8 Bit | PNGs: ca. 150×150 dpi; Manifest: 300×300 dpi | keine zusätzlichen PNG-Chunks | ✅ OK (4/4 Dateien, Manifestsemantik, Hashes) | Kontrollierter Prioritätstest: 256×256 px und identische Landmarkmasken, aber Manifest- und PNG-Größe widersprechen sich |
| I-07 | `height_max_8bit.png` | `f19e1d8eb9a3e5be118fd10d537b1ac5a9e6fbb7eae5b5ccd49eb51ebf768a44` | `f19e1d8eb9a3e5be118fd10d537b1ac5a9e6fbb7eae5b5ccd49eb51ebf768a44` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_max.png` |
| I-07 | `height_max_16bit.png` | `f9e865c79a144fc5f90144136aafae9391e4a8f2efd1e388b8593019a6bdc0ad` | `f9e865c79a144fc5f90144136aafae9391e4a8f2efd1e388b8593019a6bdc0ad` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-08 (vor/nach Crop) | `color_height_reference.png` | `8f8cdc241d084ee84ce91cda584cdd826356076a0b831876996345bd59b19493` | `8f8cdc241d084ee84ce91cda584cdd826356076a0b831876996345bd59b19493` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Asymmetrische X-/Y-Marker; pixelgleich zur HEIGHT-Registriermap |
| I-08 (vor/nach Crop) | `height_registration_16bit.png` | `aad17d01503fb53e55d50ffb306c8bf05f2842dc53b0eb4c0ce07ad65e18f8d7` | `aad17d01503fb53e55d50ffb306c8bf05f2842dc53b0eb4c0ce07ad65e18f8d7` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Nicht-weiße COLOR-Pixel exakt als 65535-Landmarks, Hintergrund 0 |
| I-08 (vor/nach Crop) | `gloss_registration.png` | `50bdc5019f79819b9f019259b4710840e21a3d51d77b06367af5c455ece78a04` | `50bdc5019f79819b9f019259b4710840e21a3d51d77b06367af5c455ece78a04` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Dieselben COLOR-Landmarks exakt als 0/255-GLOSS-Maske; gemeinsames 256×256-Tripel |
| I-09 (Legacy) | externes `.empf` (nicht im Repo) | – | – | – | – | – | – | – | n. z. | Kein BgRemover-Fixture – aus Community-Quelle B1 (`empf-generator`) zu beschaffen |
| I-09 (aktuell) | ein **aktuell von EufyMake Studio selbst** exportiertes `.empf` (nicht von BgRemover) | – | – | – | – | – | – | – | offen | Kein BgRemover-Fixture – erfordert ein reales Studio-Projekt, aus der aktuellen Studio-Version exportiert. Testzweck laut Annahmeninventar (V2, I-09): prüfen, ob das seit 2.7.0.6 verschlüsselt gekapselte aktuelle `.empf`-Format importierbar bleibt bzw. sich vom alten Legacy-ZIP unterscheidet – **nicht** ob BgRemover `.empf` erzeugen kann (das bleibt bewusst Nicht-Ziel, `OpenQuestion.NATIVE_EMPF_PROJECT`) |
| I-10 (normal) | `gloss_wedge.png` | `c908eb760796043c54c42ddc167defcd6b2d489af96667a81bf18aa03da020e8` | `c908eb760796043c54c42ddc167defcd6b2d489af96667a81bf18aa03da020e8` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_wedge_8bit.png` |
| I-10 (invertiert) | `gloss_wedge_inverted.png` | `ae9f9c1c4d33b7edea15acb9843b0ddda139134383fd9f33f443edafe43c63d6` | `ae9f9c1c4d33b7edea15acb9843b0ddda139134383fd9f33f443edafe43c63d6` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_wedge_inverted_8bit.png` |
| I-11 | `height_steps_8bit.png` | `2d940cfad6c57f9678a82b7b19641ecf41f9100f816ca84981bc51535bb6e13a` | `2d940cfad6c57f9678a82b7b19641ecf41f9100f816ca84981bc51535bb6e13a` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_steps.png` – siehe Hinweis oben; validiert, aber nicht die für den Druck vorgesehene Variante (siehe I-11 16 Bit) |
| I-11 | `height_steps_16bit.png` | `ec6de68fca3a77c895f44f90a1550574501ed533202bad9531f1fcaa390344fc` | `ec6de68fca3a77c895f44f90a1550574501ed533202bad9531f1fcaa390344fc` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Für I-11 gedruckte Variante (16-Bit-kanonisch) |
| I-12 | `height_wedge_16bit_aspect.png` | `9067d1ecabfc0067ba64c7036e28004e210945637b2c2ba53886596c90f45053` | `9067d1ecabfc0067ba64c7036e28004e210945637b2c2ba53886596c90f45053` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | 256×128 (2:1), direkt neu erzeugt statt aus der 256×256-Referenz resized (siehe Ergänzung oben) |
| I-13 | `color_alpha_coverage.png` | `1d2b8c9a0824ccc7bf669c8c1d89ea448440adde88af55f333242d9d1001f3b3` | `1d2b8c9a0824ccc7bf669c8c1d89ea448440adde88af55f333242d9d1001f3b3` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Drei Felder Alpha 0/128/255; RGB-Payload in allen Feldern konstant 40/80/220 |
| I-13 | `height_mean_16bit.png` | `37390f6ab68310bd3f5a2f43615d5c7d6784b414cba6ca48a52a6fe1310ec475` | `37390f6ab68310bd3f5a2f43615d5c7d6784b414cba6ca48a52a6fe1310ec475` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | 256×256, konstanter digitaler Wert 32768 (> 0) unter allen drei Alpha-Feldern |

**Zusätzliche Fixtures** (nicht in einer I-01…I-13-Zelle referenziert, aber
Teil des Testdesigns aus #688/#689/#690 und hiermit vollständig
mitverifiziert – bei Bedarf einer eigenen Testzelle zuordnen):

| Testzelle | Fixture-Datei | Erwarteter SHA-256 (aus Manifest) | Tatsächlicher SHA-256 | Rolle | PNG-Modus | Bittiefe | `pHYs` vorhanden/Wert | Sonstige relevante Chunks | Ergebnis (OK/Abweichung) | Anmerkung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| zusätzlich | `height_zero_8bit.png` | `39962cd5bc9f4f0446341d3e6e0c6c37336ddeb2e026a17a3d06bb6cb3266daf` | `39962cd5bc9f4f0446341d3e6e0c6c37336ddeb2e026a17a3d06bb6cb3266daf` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_min.png` |
| zusätzlich | `height_zero_16bit.png` | `2d81bac9f13468076f96a4173ea21535bbf2de69d917dfe5b3ee08934b963e89` | `2d81bac9f13468076f96a4173ea21535bbf2de69d917dfe5b3ee08934b963e89` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_mean_8bit.png` | `b5d195a24d1de3dd3f3939292a7adb9447aa93ec0680b5bf25e998d70f6c2e73` | `b5d195a24d1de3dd3f3939292a7adb9447aa93ec0680b5bf25e998d70f6c2e73` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_impulse_edge_8bit.png` | `596a89aa72df7fda9984491b7a7f52d33ca8bf8cf2e705b21f51db2363df5161` | `596a89aa72df7fda9984491b7a7f52d33ca8bf8cf2e705b21f51db2363df5161` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_impulse_edge_16bit.png` | `7f61d3329d263a2da6cd3635feb22c7bc9f6ffd71c9cf9a8be7762d496e1b1ba` | `7f61d3329d263a2da6cd3635feb22c7bc9f6ffd71c9cf9a8be7762d496e1b1ba` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_wedge_inverted_8bit.png` | `ae9f9c1c4d33b7edea15acb9843b0ddda139134383fd9f33f443edafe43c63d6` | `ae9f9c1c4d33b7edea15acb9843b0ddda139134383fd9f33f443edafe43c63d6` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_wedge_inverted.png` |
| zusätzlich | `height_wedge_inverted_16bit.png` | `ca42428dbd0617bf239eb4e1048ed4d05c4b0a9498fd857177cac8139252a198` | `ca42428dbd0617bf239eb4e1048ed4d05c4b0a9498fd857177cac8139252a198` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `mm_gross_no_phys.png` | `e1a6a4f82300079b6071c3541db613f0d082000df5f9fb66d661c0c5187e3e26` | `e1a6a4f82300079b6071c3541db613f0d082000df5f9fb66d661c0c5187e3e26` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `mm_gross_phys_conflict.png` | `9cf2866558041a29c4abca636d62cf4e8c196a45d750633014e45517698dac27` | `9cf2866558041a29c4abca636d62cf4e8c196a45d750633014e45517698dac27` | color_motif | RGBA | 8 Bit | vorhanden (23622×23622 px/m ≈ 599.999×599.999 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | Pixelmaß wie `mm_gross_*`, `pHYs` bewusst auf 600 statt 300 dpi gesetzt |
| zusätzlich | `mm_gross_phys.png` | `7aec7e7e67549481f1c97a4069696e00ed51b98ffbeef121037ca2c389b0b318` | `7aec7e7e67549481f1c97a4069696e00ed51b98ffbeef121037ca2c389b0b318` | color_motif | RGBA | 8 Bit | vorhanden (11811×11811 px/m ≈ 299.999×299.999 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | Nach Entkonfundierung von I-08 weiterhin als zusätzliche mm/DPI-Fixture verifiziert |
| zusätzlich | `mm_typisch_no_phys.png` | `2f20942d06bfa4c6b2065cbda72353ac4cf07f015a925cf3466e90a5405ccd8a` | `2f20942d06bfa4c6b2065cbda72353ac4cf07f015a925cf3466e90a5405ccd8a` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `mm_typisch_phys_conflict.png` | `c9b0e26c8cf86c0a766b3e37a19bbe53a49da86cb392277c955d3bdaffb7f83d` | `c9b0e26c8cf86c0a766b3e37a19bbe53a49da86cb392277c955d3bdaffb7f83d` | color_motif | RGBA | 8 Bit | vorhanden (5906×5906 px/m ≈ 150.012×150.012 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | Pixelmaß wie `mm_typisch_*`, `pHYs` bewusst auf 150 statt 300 dpi gesetzt |
| zusätzlich | `gloss_min.png` | `39962cd5bc9f4f0446341d3e6e0c6c37336ddeb2e026a17a3d06bb6cb3266daf` | `39962cd5bc9f4f0446341d3e6e0c6c37336ddeb2e026a17a3d06bb6cb3266daf` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_zero_8bit.png` |
| zusätzlich | `gloss_max.png` | `f19e1d8eb9a3e5be118fd10d537b1ac5a9e6fbb7eae5b5ccd49eb51ebf768a44` | `f19e1d8eb9a3e5be118fd10d537b1ac5a9e6fbb7eae5b5ccd49eb51ebf768a44` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_max_8bit.png` |
| zusätzlich | `gloss_steps.png` | `2d940cfad6c57f9678a82b7b19641ecf41f9100f816ca84981bc51535bb6e13a` | `2d940cfad6c57f9678a82b7b19641ecf41f9100f816ca84981bc51535bb6e13a` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_steps_8bit.png` |
| zusätzlich | `gloss_checkerboard.png` | `b6f2791be91d19ade1de1f05c858d321201c3b231060b9633ef1dd8323fc161d` | `b6f2791be91d19ade1de1f05c858d321201c3b231060b9633ef1dd8323fc161d` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |

**Ergebnis der Basisprüfung: 41/41 Einzel-Fixtures und 7/7 Exportpakete OK,
0 Abweichungen** (36 Fixtures aus Schema 3 plus fünf isolierte #690-Fixtures;
das frühere mm/DPI-Paket plus sechs Gloss-Szenariopakete). Die Zuordnung der
älteren I-01…I-13-Zellen bleibt unverändert; G-01…G-08 verwenden die neuen
Dateien und Pakete aus der #690-Ergebnisakte.
Damit ist die im Repository committete Fixture-Menge nachweislich konsistent
mit `fixtures_manifest.json`. Das ersetzt **nicht** die Prüfung am Zielrechner:
die vorausgefüllten „Erwarteter SHA-256"-Werte dienen dort als Referenz, aber
**„Tatsächlicher SHA-256" muss am Zielrechner neu berechnet** werden (z. B.
`sha256sum tests/fixtures/eufymake_hardware/<datei>.png`), **bevor** du ihn
mit dem erwarteten Wert abgleichst und als OK einträgst. Den vorausgefüllten
Wert unverändert als „tatsächlich" zu übernehmen, würde genau die
Eigenschaft voraussetzen, die dieser Schritt erst beweisen soll (dass die
Bytes am Zielrechner unverändert sind) – bei Übertragung per USB/Cloud kann
das nicht angenommen werden.

---

## 2. Importprotokoll

Je Testzelle **ein** Importvorgang in Studio, direkt im Anschluss an das
Dateivalidierungsprotokoll derselben Zeile.

| Testzelle | Datum/Zeit | Studio-Version | Firmware | Angezeigte Warnung(en) | Vorschau-Verhalten | Automatisch veränderte Einstellungen | „Nichts passiert"-Fall? (EM-S03) | Screenshot-Referenz | Anmerkung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| I-01 | | | | | | | Ja / Nein | | |
| I-02 | | | | | | | Ja / Nein | | |
| I-03 (8 Bit) | | | | | | | Ja / Nein | | |
| I-03 (16 Bit) | | | | | | | Ja / Nein | | |
| I-04 | | | | | | | Ja / Nein | | |
| I-05 (konsistent) | 2026-09-02 (Uhrzeit nicht protokolliert) | Studio 4.2.2 / Editor 1.20.0 | nicht angezeigt | keine | sichtbar, zentriert, 101,60×101,60 mm | keine | Nein | Live-Sitzung, kein Screenshot-Artefakt | E1 online; Standard Flatbed 335×420 mm; kein Druck |
| I-05 (ohne `pHYs`) | 2026-09-02 (Uhrzeit nicht protokolliert) | Studio 4.2.2 / Editor 1.20.0 | nicht angezeigt | Motiv überschreitet Arbeitsfläche; automatische Verkleinerung angeboten | nach bestätigtem Beibehalten der Originalgröße sichtbar, 423,33×423,33 mm | keine; angebotene Verkleinerung abgelehnt | Nein | Live-Sitzung, kein Screenshot-Artefakt | 72-dpi-Fallback; kein Druck |
| I-05 (widersprüchlich) | 2026-09-02 (Uhrzeit nicht protokolliert) | Studio 4.2.2 / Editor 1.20.0 | nicht angezeigt | keine | sichtbar, zentriert, 203,18×203,18 mm | keine | Nein | Live-Sitzung, kein Screenshot-Artefakt | `pHYs`-Quantisierung wird sichtbar; kein Druck |
| I-05 (X/Y 300/150 dpi) | 2026-09-02 (Uhrzeit nicht protokolliert) | Studio 4.2.2 / Editor 1.20.0 | nicht angezeigt | keine | sichtbar, zentriert, 101,60×203,18 mm; nach Rotation und Crop sichtbare gewählte Hälfte | Rotation 90° ohne Skalierung; bestätigter Crop halbiert intrinsische Breite auf 50,80 mm | Nein | Live-Sitzung, kein Screenshot-Artefakt | Achsen getrennt; nach Crop H 203,18 mm, Winkel 90°, X/Y 65,91/210,00 mm; kein Druck |
| I-06 (`manifest.json` allein) | 2026-09-02 (Uhrzeit nicht protokolliert) | Studio 4.2.2 / Editor 1.20.0 | nicht angezeigt | keine Studio-Warnung | JSON im Bilddialog ausgegraut; „Öffnen“ deaktiviert | keine | Ja | Live-Sitzung, kein Screenshot-Artefakt | dieser Importweg unterstützt das Manifest nicht |
| I-06 (kompletter Ordner) | 2026-09-02 (Uhrzeit nicht protokolliert) | Studio 4.2.2 / Editor 1.20.0 | nicht angezeigt | keine | nur die drei PNGs gemeinsam auswählbar; drei überlagerte „Flat“-Ebenen, je 43,35×43,35 mm | keine automatische Rollenzuordnung | Nein für PNGs; JSON nicht importierbar | Live-Sitzung, kein Screenshot-Artefakt | gleiche Werte bei Wiederholungsimport; kein Druck |
| I-07 | | | | | | | Ja / Nein | | |
| I-08 (vor Crop) | 2026-09-02 (Uhrzeit nicht protokolliert) | Studio 4.2.2 / Editor 1.20.0 | nicht angezeigt | keine | drei Rollen einzeln sichtbar, jeweils 90,31×90,31 mm und gleich zentriert | alle als „Flat“, keine Rollenzuordnung | Nein | Live-Sitzung, kein Screenshot-Artefakt | gemeinsame Startausdehnung belegt; Produktionsregistrierung und Druck offen |
| I-08 (nach Crop) | | | | | | | Ja / Nein | | |
| I-09 (Legacy) | | | | | | | Ja / Nein | | |
| I-09 (aktuell) | | | | | | | Ja / Nein | | |
| I-10 (normal) | 2026-09-02 (Uhrzeit nicht protokolliert) | Studio 4.2.2 / Editor 1.20.0 | nicht angezeigt | keine | sichtbar, 90,31×90,31 mm | „Flat“; keine Rollenzuordnung | Nein | Live-Sitzung, kein Screenshot-Artefakt | Bildimport belegt keine Gloss-Polarität; kein Druck |
| I-10 (invertiert) | 2026-09-02 (Uhrzeit nicht protokolliert) | Studio 4.2.2 / Editor 1.20.0 | nicht angezeigt | keine | sichtbar, 90,31×90,31 mm | „Flat“; keine Rollenzuordnung | Nein | Live-Sitzung, kein Screenshot-Artefakt | Bildimport belegt keine Gloss-Polarität; kein Druck |
| I-11 | | | | | | | Ja / Nein | | |
| I-12 | | | | | | | Ja / Nein | | |
| I-13 (Alpha/Coverage) | 2026-09-02 (Uhrzeit nicht protokolliert) | Studio 4.2.2 / Editor 1.20.0 | nicht angezeigt | keine | drei PNGs sichtbar, je 90,31×90,31 mm | drei getrennte „Flat“-Ebenen; keine Rollenzuordnung | Nein | Live-Sitzung, kein Screenshot-Artefakt | Alpha-Felder im COLOR sichtbar; Wirkung auf Gloss/HEIGHT ohne Druck offen |

### 2.1 mm/DPI-Detailwerte für #689

Die allgemeine Importtabelle reicht für #689 nicht aus: Breite und Höhe sind
achsweise und als **exakter Studio-Anzeigetext** zu erfassen. Eine manuelle
Größe nur eintragen, wenn sie in dieser Zelle tatsächlich gesetzt wurde;
sonst „nicht gesetzt". Vorher-/Nachher-Werte nicht in einer Zelle vermischen.

| Testzelle/Datei | Pixel X/Y | Datei-`pHYs` X/Y | Manifest-mm/DPI | Manuelle Studio-mm X/Y | Studio vor Bestätigung: mm X/Y + Dezimalstellen | Studio nach Bestätigung: mm X/Y | Seitenverhältnis/Rotation | X-/Y-Offset, Crop, Zentrierung | Priorisierte Quelle/Beobachtung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| I-01 `mm_typisch_phys.png` | 1200/1200 | ca. 300/300 dpi | keines | nicht gesetzt | 101,60/101,60 mm; 2 Dezimalstellen | unverändert | 1:1; 0° | X/Y 116,70/159,19; automatisch zentriert | PNG-`pHYs` |
| I-05 `mm_typisch_no_phys.png` | 1200/1200 | fehlt | keines | nicht gesetzt | Warnung vor Import; 72-dpi-Soll 423,333/423,333 mm | 423,33/423,33 mm nach „Originalgröße behalten“ | 1:1; 0° | X/Y −44,17/−1,67; automatisch zentriert und größer als Fläche | Studio-Fallback 72 dpi |
| I-05 `mm_typisch_phys.png` | 1200/1200 | ca. 300/300 dpi | keines | nicht gesetzt | 101,60/101,60 mm; 2 Dezimalstellen | unverändert | 1:1; 0° | X/Y 116,70/159,19; automatisch zentriert | PNG-`pHYs` |
| I-05 `mm_typisch_phys_conflict.png` | 1200/1200 | ca. 150/150 dpi | keines | nicht gesetzt | 203,18/203,18 mm; 2 Dezimalstellen | unverändert | 1:1; 0° | X/Y 65,91/108,41; automatisch zentriert | PNG-`pHYs`; Rundung aus `pHYs`-Quantisierung |
| I-05 `mm_typisch_phys_xy.png` | 1200/1200 | ca. 300/150 dpi | keines | nicht gesetzt | 101,60/203,18 mm; 2 Dezimalstellen | nach bestätigtem Crop 50,80/203,18 mm | 90°; Höhe und Winkel durch Crop unverändert | X/Y 116,70/108,41 bei 0°; 65,91/159,19 bei 90°; 65,91/210,00 nach Halbbreiten-Crop | X/Y-`pHYs` separat; Crop verändert intrinsische Breite und Position |
| I-06 `export_mm_dpi_conflict/manifest.json` allein | – | – | 21,674666… mm / 300 dpi | nicht gesetzt | nicht anwendbar | nicht importierbar | nicht anwendbar | JSON ausgegraut; „Öffnen“ deaktiviert | Manifest über Bildimport nicht unterstützt |
| I-06 kompletter Exportordner | 256/256 je PNG | ca. 150/150 dpi je PNG | 21,674666… mm / 300 dpi | nicht gesetzt | je PNG 43,35/43,35 mm; 2 Dezimalstellen | unverändert | je 1:1; 0° | je X/Y 145,83/188,33; überlagert und zentriert | PNG-`pHYs`; Manifest nicht auswählbar; alle Ebenen „Flat“ |
| I-06 kompletter Exportordner + manuelle Größe | 256/256 je PNG | ca. 150/150 dpi je PNG | 21,674666… mm / 300 dpi | auf ausgewähltem PNG 21,67/21,67 mm | 43,35/43,35 mm | 21,67/21,67 mm | gekoppelt 1:1; nach Nullwertversuch instabil | Extremversuch: 1000/1254,78 mm und X/Y −810,83/−1023,11 ohne Warnung | manuell überschreibt `pHYs`; Null-/Extremwertvalidierung erforderlich |
| I-08 COLOR/HEIGHT/GLOSS vor Crop | 256/256 je Rolle | fehlt | keines | nicht gesetzt | je 90,31/90,31 mm; 2 Dezimalstellen | unverändert | je 1:1; 0° | je X/Y 122,34/164,84; identisch zentriert | 72-dpi-Fallback; gleiche Ausdehnung, aber keine automatische Rollenzuordnung |
| I-08 COLOR/HEIGHT/GLOSS nach Crop | 256/256 je Rolle | fehlt | keines | unverändert | | | | | |
| I-12 abweichende HEIGHT-Dimension | COLOR 256/256; HEIGHT 256/128 | fehlt | keines | hier exakt eintragen | | | | | |

Rundung wird nach der Regel in
[`EUFYMAKE-689-MM-DPI-VERTRAG.md`](EUFYMAKE-689-MM-DPI-VERTRAG.md)
bewertet. „Nichts passiert" bleibt auch hier ein Ergebnis und wird zusätzlich
in der allgemeinen Importtabelle markiert.

### 2.2 Gloss-Importdetailwerte für #690

Live-Sitzung am 2026-09-02 mit Studio 4.2.2 / Editor 1.20.0; E1 online,
Firmware nicht angezeigt. Der unmittelbar vorher erzeugte Inspectorreport
bestätigte 41/41 Einzel-Fixtures und 7/7 Pakete. Es wurde weder **Preview**
noch **Print** ausgelöst.

| Zelle | Importierte Dateien | Studio-Ergebnis | Warnung/Änderung | Belegte Grenze |
| --- | --- | --- | --- | --- |
| G-01 | `gloss_min.png`, `gloss_mean.png`, `gloss_max.png` | je 90,31×90,31 mm; getrennte „Flat“-Ebenen | keine | 0/128/255 werden als Bilder akzeptiert, nicht als Glossmenge bestätigt |
| G-02 | `gloss_wedge.png`, `gloss_wedge_inverted.png` | je 90,31×90,31 mm; sichtbar und getrennt | keine | keine Polaritätsaussage ohne Druck |
| G-03 | `gloss_steps.png`, `gloss_wedge_limited.png` | je 90,31×90,31 mm; Stufen bzw. begrenzter Keil sichtbar | keine | keine Aussage über kontinuierlichen, quantisierten, binären oder normalisierten Auftrag |
| G-04a/b/c | `export_gloss_absent/` digital; Null/voll über bytegleiche `gloss_min.png`/`gloss_max.png` | fehlend im Paketvertrag; Null/voll als normale Einzelbilder | keine PNG-Warnung; JSON im Bilddialog nicht auswählbar | Bilddialog hat keinen beobachtbaren Paket-/Optionalitätsvertrag |
| G-05 | `gloss_dimensions_half_width.png` | 128×256 px → 45,16×90,31 mm; X/Y 144,91/164,84 mm; 0° | kein Scaling, Beschnitt oder Fehler | Studio verknüpft die Datei nicht mit COLOR/Manifest und erkennt deshalb keinen Konflikt |
| G-06 | drei PNGs aus `export_gloss_alpha_coverage/` | je 90,31×90,31 mm; drei unabhängige „Flat“-Ebenen; Alpha-Felder im COLOR sichtbar | keine Rollenzuordnung oder Maskenkopplung | physische Alpha×Gloss-Wirkung offen |
| G-07 | drei PNGs aus `export_gloss_height_cross/` | je 90,31×90,31 mm; 16-Bit-HEIGHT 0/32768/65535 sichtbar; drei unabhängige „Flat“-Ebenen | keine Rollenzuordnung oder Maskenkopplung | physische HEIGHT×Gloss-Wirkung offen |
| G-08 | `gloss_registration.png`, `gloss_checkerboard.png` | je 90,31×90,31 mm; getrennte „Flat“-Ebenen | keine | Druckregistrierung, Filterung und Bleeding offen |

Bei allen 256×256-Dateien ohne `pHYs` verwendete Studio den bereits in #689
belegten 72-dpi-Fallback: 90,31×90,31 mm, X/Y 122,34/164,84 mm, 0°. Namen,
PNG-Modus und gemeinsamer Exportordner erzeugten keine automatische
COLOR-/HEIGHT-/GLOSS-Semantik.

**„Nichts passiert"-Fall (EM-S03):** Laut Annahmeninventar wurde für Studio
2.6.0.2 ein still geladener, aber unsichtbarer Import berichtet; spätere
Community-Kommentare widersprechen einem generellen Problem. Ein „Ja" in
dieser Spalte ist daher **kein** automatischer Fehlschlag der Testzelle,
sondern ein eigener, explizit zu protokollierender Ausgang (keine
Fehlermeldung, aber auch kein sichtbares Ergebnis) – bei „Ja" zusätzlich
festhalten: Wartezeit bis zum Abbruch, ob ein Neustart von Studio das Problem
behebt, und ob das Motiv beim erneuten Öffnen des Projekts sichtbar wird.

---

## 3. Druckprotokoll

Nur nach abgeschlossenem Import- und Vorschauprotokoll derselben Zelle.
Materialverbrauch beachten – siehe
[`EUFYMAKE-687-TESTGOVERNANCE.md`](EUFYMAKE-687-TESTGOVERNANCE.md) (freigegeben).

| Testzelle | Datum | Druckeinstellung (Texturmodus/Ink-Mode/Bittiefe) | Position/Skalierung im Layout | Physischer Messwert (Breite × Höhe, ggf. Reliefhöhe, mm) | Messmittel | Geschätzte Messunsicherheit | Fotoreferenz | Wiederholungsmessung (2. Lauf) | Abweichung 1. vs. 2. Lauf | Anmerkung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| I-02 | | | | | | | | | | |
| I-03 (8 Bit) | | | | | | | | | | |
| I-03 (16 Bit) | | | | | | | | | | |
| I-04 | | | | | | | | | | |
| I-05 (konsistent) | | | | | | | | | | |
| I-07 | | | | | | | | | | |
| I-08 (vor Crop) | | | | | | | | | | |
| I-08 (nach Crop) | | | | | | | | | | |
| I-10 (normal) | | | | | | | | | | |
| I-10 (invertiert) | | | | | | | | | | |
| I-11 | | | | | | | | | | |
| I-12 | | | | | | | | | | |
| I-13 (Alpha/Coverage) | | | | | | | | | | |

**Je Zeile eine eigene physische Variante:** I-08 und I-10 vergleichen selbst
zwei Ausprägungen (vor/nach Crop bzw. normal/invertiert) – das sind zwei
eigenständig zu druckende und zu protokollierende Varianten, nicht zwei
Aspekte eines einzigen Drucks. Die Spalte „Wiederholungsmessung (2. Lauf)"
bezieht sich je Zeile ausschließlich auf einen zweiten, unabhängigen Druck
**derselben** Variante – nicht auf die jeweils andere Variante. Zusammen mit
den 13 Zeilen dieser Tabelle ergibt das die 13 druckbaren Varianten aus dem
Materialbudget in
[`EUFYMAKE-687-TESTGOVERNANCE.md`](EUFYMAKE-687-TESTGOVERNANCE.md).

**Wiederholungsmessung:** Mindestens die in #688/#689/#690 als Kernaussage
markierten Zeilen (Nullpunkt/Grundfläche, monotoner Keil, mm/DPI-Referenz,
Gloss-Polarität) zweimal unabhängig drucken und messen, um einen einzelnen
Fehldruck von einem systematischen Ergebnis zu unterscheiden (vgl. #687-AC
„Wiederholungsmessungen … zeigen, dass das Ergebnis nicht auf einem einzelnen
Fehldruck beruht").

**Kennzeichnung jeder Aussage:** Beim Zusammenfassen der Protokolle in einen
Vertrag (#688/#689/#690-Ziel) jede Aussage explizit als „Herstellerangabe",
„Importbeobachtung" oder „Druckmessung" markieren (#687-AC).
