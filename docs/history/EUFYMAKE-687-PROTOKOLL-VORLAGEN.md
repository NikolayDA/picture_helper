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
  --expected-manifest-sha256 8e799f245f177947d0401c431feb0d41df0cde9b5007e4243c1add679a8e8758 \
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
Alle 41 im Repository committeten Einzel-Fixtures und alle sieben
Exportpakete wurden direkt gegen `fixtures_manifest.json` geprüft – SHA-256
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

**Writer-Stand der sieben Exportpakete (Nachtrag 2026-09-02):** Alle Pakete
(`export_mm_dpi_conflict/` und die sechs `export_gloss_*/`) stammen aus dem
Writer-Stand `c814945` (PR #952), also von **vor** #953. Ihre `manifest.json`
tragen weder `profile_contract` noch `producer` noch
`assets[].channel_interpretation`; sie bleiben bewusst die am 2026-09-02 in
Studio 4.2.2 importierten Bytes (Studio liest das Manifest ohnehin nicht). Eine
Neuerzeugung schriebe diese Felder und plattformabhängige Paket-PNGs und damit
einen neuen Manifest-Vertrauensanker – sie ist nur bewusst zulässig, mit Nachzug
des Ankers in allen vier Dokumenten, dieser Tabelle und der Legacy-Projektion in
`tests/test_eufymake_fixture_generator.py`.

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
| I-01 | `mm_typisch_phys.png` | `c0525c34ab4b689c59031551ecb2e5ea869724f74ef4a6f5870b619c5dd0f2a3` | `c0525c34ab4b689c59031551ecb2e5ea869724f74ef4a6f5870b619c5dd0f2a3` | color_motif | RGBA | 8 Bit | vorhanden (11811×11811 px/m ≈ 299.999×299.999 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | |
| I-02 | `color_height_reference.png` | `f59737eca203c74eb301232aa18efabc5a67d5e4ecc496eb3eb3deb87562689a` | `f59737eca203c74eb301232aa18efabc5a67d5e4ecc496eb3eb3deb87562689a` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | 256×256, voll opak; dimensionsgleich zur HEIGHT-Referenz |
| I-02 | `height_wedge_16bit.png` | `45cabeedc8215b9318fb7ff356aa52fc2287b1be4741f14720a3bb71faa6ca41` | `45cabeedc8215b9318fb7ff356aa52fc2287b1be4741f14720a3bb71faa6ca41` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-03 (8 Bit) | `height_wedge_8bit.png` | `1d6df1bfbb11c044d74110fb0ba5511b1813870c38ea9044e1be52c2159d5dd2` | `1d6df1bfbb11c044d74110fb0ba5511b1813870c38ea9044e1be52c2159d5dd2` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_wedge.png` – siehe Hinweis oben |
| I-03 (16 Bit) | `height_wedge_16bit.png` | `45cabeedc8215b9318fb7ff356aa52fc2287b1be4741f14720a3bb71faa6ca41` | `45cabeedc8215b9318fb7ff356aa52fc2287b1be4741f14720a3bb71faa6ca41` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-04 (Referenz) | `height_wedge_16bit.png` | `45cabeedc8215b9318fb7ff356aa52fc2287b1be4741f14720a3bb71faa6ca41` | `45cabeedc8215b9318fb7ff356aa52fc2287b1be4741f14720a3bb71faa6ca41` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-04 (halbierte Kopie) | `height_wedge_16bit_half.png` | `17ab1efde6ee96be20cf4fa1de935d52f8dcf1d06d8516adf08e7a72f48a59cf` | `17ab1efde6ee96be20cf4fa1de935d52f8dcf1d06d8516adf08e7a72f48a59cf` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | 128×128, präzisionserhaltend aus `height_wedge_16bit.png` resized (siehe Ergänzung oben); gleiches Seitenverhältnis wie die 256×256-Referenz |
| I-05 (ohne `pHYs`) | `mm_klein_no_phys.png` | `24e7b0ded8a855673cc0188d6e6eb9aea2e75af1b977d3379f0d4d4a9a7914e6` | `24e7b0ded8a855673cc0188d6e6eb9aea2e75af1b977d3379f0d4d4a9a7914e6` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-05 (konsistent) | `mm_klein_phys.png` | `2c9231761c55a9f6c4ee2141960a761155614f3ea4a5f44f4590a1861b88b697` | `2c9231761c55a9f6c4ee2141960a761155614f3ea4a5f44f4590a1861b88b697` | color_motif | RGBA | 8 Bit | vorhanden (5906×5906 px/m ≈ 150.012×150.012 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | 150 dpi → 150,012 ist Rundungsartefakt des `pHYs`-Ganzzahlformats, kein Fehler |
| I-05 (widersprüchlich) | `mm_klein_phys_conflict.png` | `a3362711dd6c5165a88cf206175c2cddfcea3dfe13255d8c844addef1900abf0` | `a3362711dd6c5165a88cf206175c2cddfcea3dfe13255d8c844addef1900abf0` | color_motif | RGBA | 8 Bit | vorhanden (11811×11811 px/m ≈ 299.999×299.999 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | Pixelmaß wie `mm_klein_*`, `pHYs` bewusst auf 300 statt 150 dpi gesetzt |
| I-05 (X/Y getrennt) | `mm_typisch_phys_xy.png` | `2eb364226343cc0ba8c58b3df8d2962d34793922f401bb4182ce660b573f2660` | `2eb364226343cc0ba8c58b3df8d2962d34793922f401bb4182ce660b573f2660` | color_motif | RGBA | 8 Bit | vorhanden (11811×5906 px/m ≈ 299.999×150.012 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | 1200×1200 px; `pHYs` impliziert 101,600×203,183 mm und prüft beide Achsen getrennt |
| I-06 (`manifest.json` allein) | `export_mm_dpi_conflict/manifest.json` | `67c6310f49a5f6ce93f38dcccce60383d03829143bea6b5372305a1d0aa95128` | `67c6310f49a5f6ce93f38dcccce60383d03829143bea6b5372305a1d0aa95128` | – | JSON | – | Manifest: 300×300 dpi, 21,674666… mm | – | ✅ OK (Hash + Semantik) | Echtes BgRemover-Exportmanifest; **nicht** `fixtures_manifest.json` |
| I-06 (kompletter Ordner) | exakt vier Dateien in `export_mm_dpi_conflict/` | siehe Bundle-Einträge in `fixtures_manifest.json` | siehe Bundle-Einträge in `fixtures_manifest.json` | COLOR/HEIGHT/GLOSS + Manifest | RGBA/I;16/L/JSON | 8/16/8 Bit | PNGs: ca. 150×150 dpi; Manifest: 300×300 dpi | keine zusätzlichen PNG-Chunks | ✅ OK (4/4 Dateien, Manifestsemantik, Hashes) | Kontrollierter Prioritätstest: 256×256 px und identische Landmarkmasken, aber Manifest- und PNG-Größe widersprechen sich |
| I-07 | `height_max_8bit.png` | `d695fc28e6e329415214cc1f3529299024f999f881289b73d49b9418c900f463` | `d695fc28e6e329415214cc1f3529299024f999f881289b73d49b9418c900f463` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_max.png` |
| I-07 | `height_max_16bit.png` | `1c56a015e60acb327528a3da4c654dd6a33b49d9b85d44c3929ba77717a4cb0a` | `1c56a015e60acb327528a3da4c654dd6a33b49d9b85d44c3929ba77717a4cb0a` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-08 (vor/nach Crop) | `color_height_reference.png` | `f59737eca203c74eb301232aa18efabc5a67d5e4ecc496eb3eb3deb87562689a` | `f59737eca203c74eb301232aa18efabc5a67d5e4ecc496eb3eb3deb87562689a` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Asymmetrische X-/Y-Marker; pixelgleich zur HEIGHT-Registriermap |
| I-08 (vor/nach Crop) | `height_registration_16bit.png` | `355c5f1626fe26d34c83eb22cade8da68acaa650fdde4a10638818c026a17e4f` | `355c5f1626fe26d34c83eb22cade8da68acaa650fdde4a10638818c026a17e4f` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Nicht-weiße COLOR-Pixel exakt als 65535-Landmarks, Hintergrund 0 |
| I-08 (vor/nach Crop) | `gloss_registration.png` | `7e3c9734ab47bfbf5771b5c7ca28d6cf3899c44291aab4cc81b024710bab4a63` | `7e3c9734ab47bfbf5771b5c7ca28d6cf3899c44291aab4cc81b024710bab4a63` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Dieselben COLOR-Landmarks exakt als 0/255-GLOSS-Maske; gemeinsames 256×256-Tripel |
| I-09 (Legacy) | externes `.empf` (nicht im Repo) | – | – | – | – | – | – | – | n. z. | Kein BgRemover-Fixture – aus Community-Quelle B1 (`empf-generator`) zu beschaffen |
| I-09 (aktuell) | ein **aktuell von EufyMake Studio selbst** exportiertes `.empf` (nicht von BgRemover) | – | – | – | – | – | – | – | offen | Kein BgRemover-Fixture – erfordert ein reales Studio-Projekt, aus der aktuellen Studio-Version exportiert. Testzweck laut Annahmeninventar (V2, I-09): prüfen, ob das seit 2.7.0.6 verschlüsselt gekapselte aktuelle `.empf`-Format importierbar bleibt bzw. sich vom alten Legacy-ZIP unterscheidet – **nicht** ob BgRemover `.empf` erzeugen kann (das bleibt bewusst Nicht-Ziel, `OpenQuestion.NATIVE_EMPF_PROJECT`) |
| I-10 (normal) | `gloss_wedge.png` | `1d6df1bfbb11c044d74110fb0ba5511b1813870c38ea9044e1be52c2159d5dd2` | `1d6df1bfbb11c044d74110fb0ba5511b1813870c38ea9044e1be52c2159d5dd2` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_wedge_8bit.png` |
| I-10 (invertiert) | `gloss_wedge_inverted.png` | `885c911ff6fc532ad19141c5a12be65513d54deaccc3e41ed47819ffc840151c` | `885c911ff6fc532ad19141c5a12be65513d54deaccc3e41ed47819ffc840151c` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_wedge_inverted_8bit.png` |
| I-11 | `height_steps_8bit.png` | `41a5c094e5712e398ed6ba6b446fcae30f3187e1a5efd6df72733c8d7a435324` | `41a5c094e5712e398ed6ba6b446fcae30f3187e1a5efd6df72733c8d7a435324` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_steps.png` – siehe Hinweis oben; validiert, aber nicht die für den Druck vorgesehene Variante (siehe I-11 16 Bit) |
| I-11 | `height_steps_16bit.png` | `484ec7250b1d65bc05c72c4f689acf0041253dc1ed531245b309782c4e4e1545` | `484ec7250b1d65bc05c72c4f689acf0041253dc1ed531245b309782c4e4e1545` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Für I-11 gedruckte Variante (16-Bit-kanonisch) |
| I-12 | `height_wedge_16bit_aspect.png` | `b2ff2d49707123230b73ec193bce2becde174465c723d2f07285cf27a6a0f9a3` | `b2ff2d49707123230b73ec193bce2becde174465c723d2f07285cf27a6a0f9a3` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | 256×128 (2:1), direkt neu erzeugt statt aus der 256×256-Referenz resized (siehe Ergänzung oben) |
| I-13 | `color_alpha_coverage.png` | `a9fb75773d24ab2df21fd27591d32f7717cba79be4e12a6bf5731094fe6efb34` | `a9fb75773d24ab2df21fd27591d32f7717cba79be4e12a6bf5731094fe6efb34` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Drei Felder Alpha 0/128/255; RGB-Payload in allen Feldern konstant 40/80/220 |
| I-13 | `height_mean_16bit.png` | `5d32c766fc13ec624b4ad78c5628ceeea3669b0650649cda82de9400d5ee0706` | `5d32c766fc13ec624b4ad78c5628ceeea3669b0650649cda82de9400d5ee0706` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | 256×256, konstanter digitaler Wert 32768 (> 0) unter allen drei Alpha-Feldern |

**Zusätzliche Fixtures** (nicht in einer I-01…I-13-Zelle referenziert, aber
Teil des Testdesigns aus #688/#689/#690 und hiermit vollständig
mitverifiziert – bei Bedarf einer eigenen Testzelle zuordnen):

| Testzelle | Fixture-Datei | Erwarteter SHA-256 (aus Manifest) | Tatsächlicher SHA-256 | Rolle | PNG-Modus | Bittiefe | `pHYs` vorhanden/Wert | Sonstige relevante Chunks | Ergebnis (OK/Abweichung) | Anmerkung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| zusätzlich | `height_zero_8bit.png` | `94c35c51dc6f9e7bf6c98e14d5864781c654e5f2373e033e669b0b0a39143c03` | `94c35c51dc6f9e7bf6c98e14d5864781c654e5f2373e033e669b0b0a39143c03` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_min.png` |
| zusätzlich | `height_zero_16bit.png` | `0632d82f3e9c363f50885749e58a3ff680c4f1bec2a744c4ad06b6ecebbef008` | `0632d82f3e9c363f50885749e58a3ff680c4f1bec2a744c4ad06b6ecebbef008` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_mean_8bit.png` | `0eebc165bb858dcd3da81133373152591fe476623a8160642282764a0b3b61b9` | `0eebc165bb858dcd3da81133373152591fe476623a8160642282764a0b3b61b9` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_impulse_edge_8bit.png` | `461a9742e19d84f7e99c776297ad42f8c3858fa2147e5b6bba0ce1f5587d7418` | `461a9742e19d84f7e99c776297ad42f8c3858fa2147e5b6bba0ce1f5587d7418` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_impulse_edge_16bit.png` | `a89993f4da39b3a70865cc982657faa2407f29747d02fadcd1eb959b19c34125` | `a89993f4da39b3a70865cc982657faa2407f29747d02fadcd1eb959b19c34125` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_wedge_inverted_8bit.png` | `885c911ff6fc532ad19141c5a12be65513d54deaccc3e41ed47819ffc840151c` | `885c911ff6fc532ad19141c5a12be65513d54deaccc3e41ed47819ffc840151c` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_wedge_inverted.png` |
| zusätzlich | `height_wedge_inverted_16bit.png` | `7a1a9989196f74464f48d2496a65240d616d9c6c32662505b685435038142f9b` | `7a1a9989196f74464f48d2496a65240d616d9c6c32662505b685435038142f9b` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `mm_gross_no_phys.png` | `5e43da317812d3fca68ded78a6576237f10622a724449485429afeb6da6f8a92` | `5e43da317812d3fca68ded78a6576237f10622a724449485429afeb6da6f8a92` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `mm_gross_phys_conflict.png` | `a83a8e3f3df2ea3d752a228006f61a3f6edbd57d125597d8f3415333fbf6c00a` | `a83a8e3f3df2ea3d752a228006f61a3f6edbd57d125597d8f3415333fbf6c00a` | color_motif | RGBA | 8 Bit | vorhanden (23622×23622 px/m ≈ 599.999×599.999 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | Pixelmaß wie `mm_gross_*`, `pHYs` bewusst auf 600 statt 300 dpi gesetzt |
| zusätzlich | `mm_gross_phys.png` | `145bf93d8e1bbc6bc0967bcaccd4fdf6d845d9dc7b1fc3fc446ad3d17e1c6863` | `145bf93d8e1bbc6bc0967bcaccd4fdf6d845d9dc7b1fc3fc446ad3d17e1c6863` | color_motif | RGBA | 8 Bit | vorhanden (11811×11811 px/m ≈ 299.999×299.999 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | Nach Entkonfundierung von I-08 weiterhin als zusätzliche mm/DPI-Fixture verifiziert |
| zusätzlich | `mm_typisch_no_phys.png` | `248b71c11e35a3e255035fcfb92de3ce4514d1b2c7c1a46a0948a323453e945f` | `248b71c11e35a3e255035fcfb92de3ce4514d1b2c7c1a46a0948a323453e945f` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `mm_typisch_phys_conflict.png` | `ec30dfac21d1ca4695b4c811f3764cb4fd874e2b096811e813c940b5423af8d8` | `ec30dfac21d1ca4695b4c811f3764cb4fd874e2b096811e813c940b5423af8d8` | color_motif | RGBA | 8 Bit | vorhanden (5906×5906 px/m ≈ 150.012×150.012 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | Pixelmaß wie `mm_typisch_*`, `pHYs` bewusst auf 150 statt 300 dpi gesetzt |
| zusätzlich | `color_gloss_height_cross.png` | `aef6004a6efe91876df31a2cd934f5440489fa5fb30517e92faac72f039b67aa` | `aef6004a6efe91876df31a2cd934f5440489fa5fb30517e92faac72f039b67aa` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Konstantes opakes COLOR für die isolierte HEIGHT×Gloss-Zelle G-07 |
| zusätzlich | `height_gloss_cross_16bit.png` | `b655327cf42f8dd29a0c6c969ac1e67c61f45f3f7ec56c5ed761b6350e0a983b` | `b655327cf42f8dd29a0c6c969ac1e67c61f45f3f7ec56c5ed761b6350e0a983b` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Drei Felder 0/32768/65535 für G-07 |
| zusätzlich | `gloss_min.png` | `94c35c51dc6f9e7bf6c98e14d5864781c654e5f2373e033e669b0b0a39143c03` | `94c35c51dc6f9e7bf6c98e14d5864781c654e5f2373e033e669b0b0a39143c03` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_zero_8bit.png` |
| zusätzlich | `gloss_mean.png` | `0eebc165bb858dcd3da81133373152591fe476623a8160642282764a0b3b61b9` | `0eebc165bb858dcd3da81133373152591fe476623a8160642282764a0b3b61b9` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Konstanter Wert 128 für G-01/G-06/G-07 |
| zusätzlich | `gloss_max.png` | `d695fc28e6e329415214cc1f3529299024f999f881289b73d49b9418c900f463` | `d695fc28e6e329415214cc1f3529299024f999f881289b73d49b9418c900f463` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_max_8bit.png` |
| zusätzlich | `gloss_steps.png` | `41a5c094e5712e398ed6ba6b446fcae30f3187e1a5efd6df72733c8d7a435324` | `41a5c094e5712e398ed6ba6b446fcae30f3187e1a5efd6df72733c8d7a435324` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_steps_8bit.png` |
| zusätzlich | `gloss_wedge_limited.png` | `540d8f08e573944cbd7cb7dc5640f5fca92c3227207f88759c45e8b67a28a4a5` | `540d8f08e573944cbd7cb7dc5640f5fca92c3227207f88759c45e8b67a28a4a5` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | Monotoner 64…192-Keil zur Normalisierungsprobe G-03 |
| zusätzlich | `gloss_dimensions_half_width.png` | `9553e045df957630098ad7e12bdfacef5dbd39a38fe74691de68d93b9c33f6b7` | `9553e045df957630098ad7e12bdfacef5dbd39a38fe74691de68d93b9c33f6b7` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | 128×256 gegen 256×256-Referenz für G-05 |
| zusätzlich | `gloss_checkerboard.png` | `b15cd8d2c922053b35d117f3d68d12ad4df828853a3ddc34abb44061a1d70f65` | `b15cd8d2c922053b35d117f3d68d12ad4df828853a3ddc34abb44061a1d70f65` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |

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
