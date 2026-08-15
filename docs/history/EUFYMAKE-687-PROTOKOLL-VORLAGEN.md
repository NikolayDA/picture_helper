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

| Testzelle | Fixture-Datei(en) | Erwarteter SHA-256 (aus Manifest) | Tatsächlicher SHA-256 | Rolle | PNG-Modus | Bittiefe | `pHYs` vorhanden/Wert | Sonstige relevante Chunks | Ergebnis (OK/Abweichung) | Anmerkung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| I-01 | `mm_typisch_phys.png` | | | | | | | | | |
| I-02 | `mm_typisch_phys.png` + `height_wedge_16bit.png` | | | | | | | | | |
| I-03 | `height_wedge_8bit.png` / `height_wedge_16bit.png` | | | | | | | | | |
| I-04 | `height_wedge_16bit.png` (Referenz) + halbierte Kopie | | | | | | | | | |
| I-05 | `mm_klein_no_phys.png` / `mm_klein_phys.png` / `mm_klein_phys_conflict.png` | | | | | | | | | |
| I-06 | `fixtures_manifest.json` + kompletter Fixture-Ordner | – (kein Bild-Asset) | | | | | | | | |
| I-07 | `height_max_8bit.png` / `height_max_16bit.png` | | | | | | | | | |
| I-08 | `mm_gross_phys.png` + `height_wedge_16bit.png` | | | | | | | | | |
| I-09 | Legacy-`.empf` (extern) / aktuell exportiertes `.empf` | – (kein PNG) | | | | | | | | |
| I-10 | `gloss_wedge.png` / `gloss_wedge_inverted.png` | | | | | | | | | |

Zusätzliche Zeilen für weitere Fixtures aus `fixtures_manifest.json` (z. B.
`height_zero_*`, `height_steps_*`, `height_impulse_edge_*`, `gloss_steps.png`,
`gloss_checkerboard.png`, die übrigen `mm_*`-Kombinationen) nach demselben
Muster ergänzen.

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
