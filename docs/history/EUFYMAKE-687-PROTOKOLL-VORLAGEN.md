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
und ihre Bedeutung stehen im
[Annahmeninventar](EUFYMAKE-687-ANNAHMENINVENTAR.md), Abschnitt „Testmatrix"
(V1) bzw. „Aktualisierte Testmatrix" (V2).

**Hinweis zu pHYs/DPI:** PNGs `pHYs`-Chunk speichert Pixel je Meter als
Ganzzahl; der Rückweg zu DPI rundet deshalb minimal (< 0,01 %, z. B. 150 dpi →
angezeigt ggf. 150,012). Das ist ein Format-Artefakt, kein Fehler der
Fixture-Erzeugung.

## Testzellen-Referenz (aus dem Annahmeninventar)

| Zelle | Eingabe | Variierter Faktor | Ziel-Issue |
| --- | --- | --- | --- |
| I-01 | `color_motif.png` allein | – | #689 |
| I-02 | `color_motif.png` + `height_map.png` | Höhenkarte zugeordnet | #688 |
| I-03 | Höhenkarte 8 Bit vs. 16 Bit, identisches Motiv | Bittiefe | #688 |
| I-04 | Höhenkarte mit halber Kantenlänge | Pixelmaß | #688/#689 |
| I-05 | PNG mit `pHYs` konsistent vs. widersprüchlich vs. ohne | `pHYs` | #689 |
| I-06 | `manifest.json` allein und kompletter BgRemover-Ordner | Träger | #687 |
| I-07 | Vollweiße Höhenkarte | Sättigung | #688 |
| I-08 | Motiv samt Höhenkarte vor/nach Crop in Studio | Crop | #689 |
| I-09 | Legacy-`.empf` vs. aktuell exportiertes `.empf` | Containergeneration | #687 |
| I-10 | Gloss-Maske schwarz/weiß invertiert | Polarität | #690 |

---

## 1. Dateivalidierungsprotokoll

Vor **jedem** Import in EufyMake Studio: Datei unabhängig von der App prüfen
(z. B. `python -c "from PIL import Image; ..."`, `file`, ein Hex-/PNG-Chunk-
Viewer) und mit `fixtures_manifest.json` abgleichen, **bevor** Studio die
Datei sieht.

**Repository-Basisprüfung (2026-08-15, automatisiert, kein Studio-Zugriff):**
Alle 29 im Repository committeten Fixtures wurden direkt gegen
`fixtures_manifest.json` geprüft – SHA-256 der Datei, Bytegröße, PNG-Modus/
IHDR-Bittiefe/-Farbtyp, Maße sowie eine vollständige Chunk-Liste (per
struct-Parsing der PNG-Bytes, nicht nur über PIL). Ergebnis: **alle 29
Dateien stimmen exakt mit dem Manifest überein**, keine Datei enthält
Chunks außer `IHDR`/`IDAT`/`IEND` und – wo im Manifest dokumentiert –
`pHYs`. Das ersetzt **nicht** die Prüfung unmittelbar vor dem Import bei dir
(falls die Dateien z. B. per USB/Cloud auf einen anderen Rechner übertragen
wurden, dort erneut per `sha256sum` gegenchecken) – es bestätigt nur, dass
der Ausgangszustand im Repository korrekt ist, bevor du davon kopierst.

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
| I-02 | `mm_typisch_phys.png` | `e6db39fc9e98bef6df6783214a2e19cdca051f0ed42ef0dfb7ef029d206e2740` | `e6db39fc9e98bef6df6783214a2e19cdca051f0ed42ef0dfb7ef029d206e2740` | color_motif | RGBA | 8 Bit | vorhanden (11811×11811 px/m ≈ 299.999×299.999 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | |
| I-02 | `height_wedge_16bit.png` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-03 (8 Bit) | `height_wedge_8bit.png` | `c908eb760796043c54c42ddc167defcd6b2d489af96667a81bf18aa03da020e8` | `c908eb760796043c54c42ddc167defcd6b2d489af96667a81bf18aa03da020e8` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_wedge.png` – siehe Hinweis oben |
| I-03 (16 Bit) | `height_wedge_16bit.png` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-04 (Referenz) | `height_wedge_16bit.png` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-04 (halbierte Kopie) | *manuell aus `height_wedge_16bit.png` zu erzeugen* | – | – | – | – | – | – | – | n. z. | Keine vorgefertigte Fixture – erst im Test aus der 256×256-Referenz eine **128×128**-Kopie erzeugen (beide Kanten halbiert, gleiches Seitenverhältnis), sonst vermischt sich der Pixelmaß-Test mit einer zusätzlichen Seitenverhältnis-Verzerrung; dann Zeile hier ergänzen |
| I-05 (ohne `pHYs`) | `mm_klein_no_phys.png` | `6eabe8ece8b79a3836e44a710263ad64c1c119432c755e89cbf3252d1dce25e0` | `6eabe8ece8b79a3836e44a710263ad64c1c119432c755e89cbf3252d1dce25e0` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-05 (konsistent) | `mm_klein_phys.png` | `37a78c832895222f3ee659f64589fc9096f9e8925c6058f65394db6e1cfb37c8` | `37a78c832895222f3ee659f64589fc9096f9e8925c6058f65394db6e1cfb37c8` | color_motif | RGBA | 8 Bit | vorhanden (5906×5906 px/m ≈ 150.012×150.012 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | 150 dpi → 150,012 ist Rundungsartefakt des `pHYs`-Ganzzahlformats, kein Fehler |
| I-05 (widersprüchlich) | `mm_klein_phys_conflict.png` | `1e02f7004559030c7aa859a2c34ecbd7bfce9c4f786a4406eb0b5b5b69fba983` | `1e02f7004559030c7aa859a2c34ecbd7bfce9c4f786a4406eb0b5b5b69fba983` | color_motif | RGBA | 8 Bit | vorhanden (11811×11811 px/m ≈ 299.999×299.999 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | Pixelmaß wie `mm_klein_*`, `pHYs` bewusst auf 300 statt 150 dpi gesetzt |
| I-06 (`manifest.json` allein) | `fixtures_manifest.json` | – (kein Bild-Asset) | – | – | – | – | – | – | n. z. | Kein PNG – Validierung hier bedeutungslos, Testzweck ist Studios Reaktion auf die Datei |
| I-06 (kompletter Ordner) | alle 30 Dateien in `tests/fixtures/eufymake_hardware/` (29 PNG-Fixtures + `fixtures_manifest.json`) | siehe alle Zeilen dieser Tabelle | siehe alle Zeilen dieser Tabelle | – | – | – | – | – | ✅ OK (29 PNGs hash-verifiziert; `fixtures_manifest.json` liegt vor, hat aber keinen Selbst-Hash) | Beim Import den **kompletten** Ordner inkl. Manifest verwenden, nicht nur die 29 Bilder – sonst wird nicht das reale BgRemover-Lieferbündel getestet. Auf Bytegleichheit über Rollen hinweg achten, siehe Hinweis oben |
| I-07 | `height_max_8bit.png` | `f19e1d8eb9a3e5be118fd10d537b1ac5a9e6fbb7eae5b5ccd49eb51ebf768a44` | `f19e1d8eb9a3e5be118fd10d537b1ac5a9e6fbb7eae5b5ccd49eb51ebf768a44` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_max.png` |
| I-07 | `height_max_16bit.png` | `f9e865c79a144fc5f90144136aafae9391e4a8f2efd1e388b8593019a6bdc0ad` | `f9e865c79a144fc5f90144136aafae9391e4a8f2efd1e388b8593019a6bdc0ad` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-08 (vor/nach Crop) | `mm_gross_phys.png` | `7aec7e7e67549481f1c97a4069696e00ed51b98ffbeef121037ca2c389b0b318` | `7aec7e7e67549481f1c97a4069696e00ed51b98ffbeef121037ca2c389b0b318` | color_motif | RGBA | 8 Bit | vorhanden (11811×11811 px/m ≈ 299.999×299.999 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | |
| I-08 (vor/nach Crop) | `height_wedge_16bit.png` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | `5e9cf1c3c2f41bc84a9adc9e946dc80c425dc3e74373cfeeb888c85068911a0f` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| I-09 (Legacy) | externes `.empf` (nicht im Repo) | – | – | – | – | – | – | – | n. z. | Kein BgRemover-Fixture – aus Community-Quelle B1 (`empf-generator`) zu beschaffen |
| I-09 (aktuell) | ein **aktuell von EufyMake Studio selbst** exportiertes `.empf` (nicht von BgRemover) | – | – | – | – | – | – | – | offen | Kein BgRemover-Fixture – erfordert ein reales Studio-Projekt, aus der aktuellen Studio-Version exportiert. Testzweck laut Annahmeninventar (V2, I-09): prüfen, ob das seit 2.7.0.6 verschlüsselt gekapselte aktuelle `.empf`-Format importierbar bleibt bzw. sich vom alten Legacy-ZIP unterscheidet – **nicht** ob BgRemover `.empf` erzeugen kann (das bleibt bewusst Nicht-Ziel, `OpenQuestion.NATIVE_EMPF_PROJECT`) |
| I-10 | `gloss_wedge.png` | `c908eb760796043c54c42ddc167defcd6b2d489af96667a81bf18aa03da020e8` | `c908eb760796043c54c42ddc167defcd6b2d489af96667a81bf18aa03da020e8` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_wedge_8bit.png` |
| I-10 | `gloss_wedge_inverted.png` | `ae9f9c1c4d33b7edea15acb9843b0ddda139134383fd9f33f443edafe43c63d6` | `ae9f9c1c4d33b7edea15acb9843b0ddda139134383fd9f33f443edafe43c63d6` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_wedge_inverted_8bit.png` |

**Zusätzliche Fixtures** (nicht in einer I-01…I-10-Zelle referenziert, aber
Teil des Testdesigns aus #688/#689/#690 und hiermit vollständig
mitverifiziert – bei Bedarf einer eigenen Testzelle zuordnen):

| Testzelle | Fixture-Datei | Erwarteter SHA-256 (aus Manifest) | Tatsächlicher SHA-256 | Rolle | PNG-Modus | Bittiefe | `pHYs` vorhanden/Wert | Sonstige relevante Chunks | Ergebnis (OK/Abweichung) | Anmerkung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| zusätzlich | `height_zero_8bit.png` | `39962cd5bc9f4f0446341d3e6e0c6c37336ddeb2e026a17a3d06bb6cb3266daf` | `39962cd5bc9f4f0446341d3e6e0c6c37336ddeb2e026a17a3d06bb6cb3266daf` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_min.png` |
| zusätzlich | `height_zero_16bit.png` | `2d81bac9f13468076f96a4173ea21535bbf2de69d917dfe5b3ee08934b963e89` | `2d81bac9f13468076f96a4173ea21535bbf2de69d917dfe5b3ee08934b963e89` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_mean_8bit.png` | `b5d195a24d1de3dd3f3939292a7adb9447aa93ec0680b5bf25e998d70f6c2e73` | `b5d195a24d1de3dd3f3939292a7adb9447aa93ec0680b5bf25e998d70f6c2e73` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_mean_16bit.png` | `37390f6ab68310bd3f5a2f43615d5c7d6784b414cba6ca48a52a6fe1310ec475` | `37390f6ab68310bd3f5a2f43615d5c7d6784b414cba6ca48a52a6fe1310ec475` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_steps_8bit.png` | `2d940cfad6c57f9678a82b7b19641ecf41f9100f816ca84981bc51535bb6e13a` | `2d940cfad6c57f9678a82b7b19641ecf41f9100f816ca84981bc51535bb6e13a` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_steps.png` |
| zusätzlich | `height_steps_16bit.png` | `ec6de68fca3a77c895f44f90a1550574501ed533202bad9531f1fcaa390344fc` | `ec6de68fca3a77c895f44f90a1550574501ed533202bad9531f1fcaa390344fc` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_impulse_edge_8bit.png` | `596a89aa72df7fda9984491b7a7f52d33ca8bf8cf2e705b21f51db2363df5161` | `596a89aa72df7fda9984491b7a7f52d33ca8bf8cf2e705b21f51db2363df5161` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_impulse_edge_16bit.png` | `7f61d3329d263a2da6cd3635feb22c7bc9f6ffd71c9cf9a8be7762d496e1b1ba` | `7f61d3329d263a2da6cd3635feb22c7bc9f6ffd71c9cf9a8be7762d496e1b1ba` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `height_wedge_inverted_8bit.png` | `ae9f9c1c4d33b7edea15acb9843b0ddda139134383fd9f33f443edafe43c63d6` | `ae9f9c1c4d33b7edea15acb9843b0ddda139134383fd9f33f443edafe43c63d6` | height_map | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `gloss_wedge_inverted.png` |
| zusätzlich | `height_wedge_inverted_16bit.png` | `ca42428dbd0617bf239eb4e1048ed4d05c4b0a9498fd857177cac8139252a198` | `ca42428dbd0617bf239eb4e1048ed4d05c4b0a9498fd857177cac8139252a198` | height_map | I;16 | 16 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `mm_gross_no_phys.png` | `e1a6a4f82300079b6071c3541db613f0d082000df5f9fb66d661c0c5187e3e26` | `e1a6a4f82300079b6071c3541db613f0d082000df5f9fb66d661c0c5187e3e26` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `mm_gross_phys_conflict.png` | `9cf2866558041a29c4abca636d62cf4e8c196a45d750633014e45517698dac27` | `9cf2866558041a29c4abca636d62cf4e8c196a45d750633014e45517698dac27` | color_motif | RGBA | 8 Bit | vorhanden (23622×23622 px/m ≈ 599.999×599.999 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | Pixelmaß wie `mm_gross_*`, `pHYs` bewusst auf 600 statt 300 dpi gesetzt |
| zusätzlich | `mm_typisch_no_phys.png` | `2f20942d06bfa4c6b2065cbda72353ac4cf07f015a925cf3466e90a5405ccd8a` | `2f20942d06bfa4c6b2065cbda72353ac4cf07f015a925cf3466e90a5405ccd8a` | color_motif | RGBA | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |
| zusätzlich | `mm_typisch_phys_conflict.png` | `c9b0e26c8cf86c0a766b3e37a19bbe53a49da86cb392277c955d3bdaffb7f83d` | `c9b0e26c8cf86c0a766b3e37a19bbe53a49da86cb392277c955d3bdaffb7f83d` | color_motif | RGBA | 8 Bit | vorhanden (5906×5906 px/m ≈ 150.012×150.012 dpi) | keine (nur IHDR/IDAT/IEND/pHYs) | ✅ OK | Pixelmaß wie `mm_typisch_*`, `pHYs` bewusst auf 150 statt 300 dpi gesetzt |
| zusätzlich | `gloss_min.png` | `39962cd5bc9f4f0446341d3e6e0c6c37336ddeb2e026a17a3d06bb6cb3266daf` | `39962cd5bc9f4f0446341d3e6e0c6c37336ddeb2e026a17a3d06bb6cb3266daf` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_zero_8bit.png` |
| zusätzlich | `gloss_max.png` | `f19e1d8eb9a3e5be118fd10d537b1ac5a9e6fbb7eae5b5ccd49eb51ebf768a44` | `f19e1d8eb9a3e5be118fd10d537b1ac5a9e6fbb7eae5b5ccd49eb51ebf768a44` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_max_8bit.png` |
| zusätzlich | `gloss_steps.png` | `2d940cfad6c57f9678a82b7b19641ecf41f9100f816ca84981bc51535bb6e13a` | `2d940cfad6c57f9678a82b7b19641ecf41f9100f816ca84981bc51535bb6e13a` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | SHA identisch mit `height_steps_8bit.png` |
| zusätzlich | `gloss_checkerboard.png` | `b6f2791be91d19ade1de1f05c858d321201c3b231060b9633ef1dd8323fc161d` | `b6f2791be91d19ade1de1f05c858d321201c3b231060b9633ef1dd8323fc161d` | gloss_mask | L | 8 Bit | nicht vorhanden | keine (nur IHDR/IDAT/IEND) | ✅ OK | |

**Ergebnis der Basisprüfung: 29/29 Fixtures OK, 0 Abweichungen.** Damit ist
die im Repository committete Fixture-Menge nachweislich konsistent mit
`fixtures_manifest.json`. Das ersetzt **nicht** die Prüfung am Zielrechner:
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
| I-05 (konsistent) | | | | | | | Ja / Nein | | |
| I-05 (ohne `pHYs`) | | | | | | | Ja / Nein | | |
| I-05 (widersprüchlich) | | | | | | | Ja / Nein | | |
| I-06 (`manifest.json` allein) | | | | | | | Ja / Nein | | |
| I-06 (kompletter Ordner) | | | | | | | Ja / Nein | | |
| I-07 | | | | | | | Ja / Nein | | |
| I-08 (vor Crop) | | | | | | | Ja / Nein | | |
| I-08 (nach Crop) | | | | | | | Ja / Nein | | |
| I-09 (Legacy) | | | | | | | Ja / Nein | | |
| I-09 (aktuell) | | | | | | | Ja / Nein | | |
| I-10 | | | | | | | Ja / Nein | | |

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
[`EUFYMAKE-687-TESTGOVERNANCE.md`](EUFYMAKE-687-TESTGOVERNANCE.md) (Entwurf).

| Testzelle | Datum | Druckeinstellung (Texturmodus/Ink-Mode/Bittiefe) | Position/Skalierung im Layout | Physischer Messwert (Breite × Höhe, ggf. Reliefhöhe, mm) | Messmittel | Geschätzte Messunsicherheit | Fotoreferenz | Wiederholungsmessung (2. Lauf) | Abweichung 1. vs. 2. Lauf | Anmerkung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| I-02 | | | | | | | | | | |
| I-03 (8 Bit) | | | | | | | | | | |
| I-03 (16 Bit) | | | | | | | | | | |
| I-04 | | | | | | | | | | |
| I-05 (konsistent) | | | | | | | | | | |
| I-07 | | | | | | | | | | |
| I-08 (vor/nach Crop) | | | | | | | | | | |
| I-10 | | | | | | | | | | |

**Wiederholungsmessung:** Mindestens die in #688/#689/#690 als Kernaussage
markierten Zeilen (Nullpunkt/Grundfläche, monotoner Keil, mm/DPI-Referenz,
Gloss-Polarität) zweimal unabhängig drucken und messen, um einen einzelnen
Fehldruck von einem systematischen Ergebnis zu unterscheiden (vgl. #687-AC
„Wiederholungsmessungen … zeigen, dass das Ergebnis nicht auf einem einzelnen
Fehldruck beruht").

**Kennzeichnung jeder Aussage:** Beim Zusammenfassen der Protokolle in einen
Vertrag (#688/#689/#690-Ziel) jede Aussage explizit als „Herstellerangabe",
„Importbeobachtung" oder „Druckmessung" markieren (#687-AC).
