# EufyMake-Gloss-/Coverage-Vertrag – Ergebnisakte für Issue #690

> **Status: reproduzierbarer Datei- und Importtestsatz vollständig; physische
> Klarlackmessung ausstehend.** Dieses Dokument trennt Herstellerangabe,
> Repositoryprüfung, Studio-Importbeobachtung und Druckbefund. Ein sichtbares
> Graustufenbild im Editor beweist weder die Gloss-Polarität noch einen
> Klarlackauftrag.

## 1. Geltungsbereich und Testumgebung

| Merkmal | Wert/Nachweis |
| --- | --- |
| EufyMake Studio | 4.2.2 |
| Editor-Version | 1.20.0 |
| E1/Firmware | E1 im Editor online; Firmware nicht protokolliert |
| Betriebssystem | macOS 26.6.2 (Build 25G83) |
| Material/Tinte/Klarlack/Ink-Mode | ausstehend; kein Druck gestartet |
| Beleuchtung/Messmittel | ausstehend |
| Fixture-Katalog | Schema 4; 41 Einzel-Fixtures; 7 Exportpakete |
| Manifest-Vertrauensanker | `be71d47fe0f4aab8a80aedd181a91ecf611087840216b2e4f0cf1dda79d2de5c` |
| Pre-Import-Report | 41/41 Fixtures und 7/7 Pakete OK; Report-SHA-256 `a0f1ac56c34674fb899255a38fbab962c3eb44004fab2273cddce5767b1535da` |

Vor jedem weiteren Studio- oder Drucklauf ist der Report neu zu erzeugen:

```bash
.venv/bin/python scripts/eufymake_fixture_inspector.py \
  --fixture-dir tests/fixtures/eufymake_hardware \
  --expected-manifest-sha256 be71d47fe0f4aab8a80aedd181a91ecf611087840216b2e4f0cf1dda79d2de5c \
  --output eufymake-690-pre-import.json
```

## 2. Belegter Ausgangsstand

| Aussage | Evidenzklasse | Quelle | Status |
| --- | --- | --- | --- |
| Der Hersteller beschreibt einen separaten Spot-UV-Dateiworkflow; in dessen Schwarz-Weiß-Maske bedeutet Schwarz „Gloss auftragen“, Weiß „nichts“. | Herstellerangabe | A11 in `EUFYMAKE-687-ANNAHMENINVENTAR.md` | belegt für den beschriebenen Workflow; noch nicht als Verhalten unseres Assets gedruckt |
| `gloss_mask.png` ist eine experimentelle BgRemover-Konvention, kein bestätigter nativer Studio-Paketvertrag. | Produkt-/Repositoryvertrag | `eufymake_export.py`, ADR | belegt |
| Ohne explizite GLOSS-Rolle erzeugt der Writer weder Datei noch Manifestreferenz. | Repositoryprüfung | Paket `gloss_absent`, Generator- und Writer-Tests | belegt |
| Eine vorhandene Nullfläche und eine fehlende Gloss-Datei sind unterschiedliche Pakete. | Repositoryprüfung | `gloss_zero` gegenüber `gloss_absent` | belegt |
| Studio trägt bei einem importierten Graustufenbild tatsächlich Klarlack auf. | – | kein Druckbefund | offen |

## 3. Isolierte Testzellen

Alle Einzelbilder sind deterministisch, ohne Zufallszahlen, 8-Bit-Graustufen
für Gloss und – sofern vorhanden – pixelgenau über das Schema-4-Manifest
gebunden. HEIGHT bleibt 16 Bit. Die Pakete entstehen über den Produktionswriter;
nur das Dimensionsfehlerpaket ersetzt anschließend kontrolliert die Gloss-Datei.

| Zelle | Dateien/Paket | Isolierte Variable | Digitaler Sollwert | Import | Druck |
| --- | --- | --- | --- | --- | --- |
| G-01 | `gloss_min.png`, `gloss_mean.png`, `gloss_max.png` | Minimum/Mitte/Maximum | 0 / 128 / 255 | ausstehend | ausstehend |
| G-02 | `gloss_wedge.png`, `gloss_wedge_inverted.png` | Polarität | 0→255 / 255→0 | ausstehend | ausstehend |
| G-03 | `gloss_steps.png`, `gloss_wedge_limited.png` | kontinuierlich, quantisiert, binär oder normalisiert | 8 Stufen 0…255 / Keil 64…192 | ausstehend | ausstehend |
| G-04a | `export_gloss_absent/` | keine Gloss-Rolle | keine Datei/Referenz | ausstehend | ausstehend |
| G-04b | `export_gloss_zero/` | vorhandene Nullfläche | 0 | ausstehend | ausstehend |
| G-04c | `export_gloss_full/` | voll gesetzte Fläche | 255 | ausstehend | ausstehend |
| G-05 | `export_gloss_dimension_mismatch/` | Dimensionsregel | COLOR/Manifest 256×256; Gloss 128×256 | ausstehend | nur falls Import sicher interpretierbar |
| G-06 | `export_gloss_alpha_coverage/` | COLOR-Alpha bei konstantem Gloss/HEIGHT | Alpha 0/128/255; RGB konstant; Gloss 128; HEIGHT 32768 | ausstehend | ausstehend |
| G-07 | `export_gloss_height_cross/` | HEIGHT bei konstantem Gloss/COLOR | HEIGHT 0/32768/65535; Gloss 128; COLOR opak | ausstehend | ausstehend |
| G-08 | `gloss_registration.png`, `gloss_checkerboard.png` | Registrierung, Filterung, Bleeding | Landmarkmaske 0/255; 16-px-Schachbrett | Import-Grundlage aus #689; neuer Gloss-Lauf ausstehend | ausstehend |

Die Zellen G-06 und G-07 sind absichtlich getrennt. G-06 variiert ausschließlich
COLOR-Alpha; G-07 ausschließlich HEIGHT. Dadurch darf eine spätere Abweichung
nicht beiden Einflussgrößen zugleich zugeschrieben werden.

## 4. Repositoryvertrag und sichere Defaults

1. `gloss_mask.png` ist optional und bleibt 8-Bit-`L`. Die akzeptierte
   Studio-/Drucksemantik ist noch nicht bestätigt.
2. **Sicherer Default:** Ohne explizite GLOSS-Rolle wird keine Gloss-Datei
   geschrieben. Eine vorhandene, auch komplett schwarze oder weiße Gloss-Rolle
   ist dagegen eine bewusste Anforderung und bleibt warnpflichtig.
3. „Null-Gloss“ bedeutet in dieser Akte eine syntaktisch gültige PNG-Datei mit
   ausschließlich Digitalwert 0 – keine leere/0-Byte-Datei. Ein beschädigtes
   oder leeres Dateisystemobjekt gehört in die allgemeine Importfehlerprüfung.
4. Abweichende Gloss-Dimensionen sind im produktiven BgRemover-Export bereits
   ein blockierender Größenfehler. Das Paket G-05 ist ausschließlich ein
   kontrolliertes Fremddatenfixture, um das Studio-Verhalten zu dokumentieren;
   es legitimiert kein Scaling im Writer.
5. Bis zum physischen Gegenbeleg darf BgRemover keinen Grauwert als bestätigte
   Klarlackmenge bezeichnen. Die Herstellerpolarität Schwarz=Auftrag ist der
   sichere Prüfanker, aber noch kein bestätigter Vertrag für `gloss_mask.png`.

## 5. Studio-Importprotokoll

| Zelle | Datum/Version | Warnung | Darstellung/Größe | automatische Änderung | Aussagegrenze |
| --- | --- | --- | --- | --- | --- |
| G-01 | | | | | Keine Aussage über Klarlack ohne Druck |
| G-02 | | | | | Invertierte Bilddarstellung ist noch keine Polaritätsbestätigung |
| G-03 | | | | | Tonwertanzeige ist noch keine Intensitätskennlinie |
| G-04a/b/c | | | | | Manifest- und Einzelbildimport getrennt festhalten |
| G-05 | | | | | Scaling/Beschnitt/Ablehnung exakt protokollieren |
| G-06 | | | | | COLOR-Alpha-Wirkung von Gloss-Auftrag trennen |
| G-07 | | | | | HEIGHT-Wirkung von Gloss-Auftrag trennen |
| G-08 | | | | | Registrierung im Druck separat messen |

## 6. Physisches Mess- und Fotoprotokoll

Für jeden freigegebenen Lauf sind Material, Druckmodus, Geräteoptionen,
Klarlack-/Tintenstand, Position und Skalierung zu dokumentieren. Fotos erhalten
eine konstante Kameraposition, Belichtung, Weißabgleich und zwei definierte
Beleuchtungswinkel (frontal und streifend). Mindestens G-02 wird zweimal
unabhängig gedruckt; G-01/G-03 benötigen identische Parameter im selben
Vergleichslayout.

| Zelle/Feld | Lauf | Digitalwert | sichtbarer Gloss | Mess-/Fotoreferenz | Material/Ink-Mode | Abweichung |
| --- | --- | --- | --- | --- | --- | --- |
| G-01 min/mittel/max | 1 | 0/128/255 | | | | |
| G-02 normal | 1 | 0→255 | | | | |
| G-02 normal | 2 | 0→255 | | | | |
| G-02 invertiert | 1 | 255→0 | | | | |
| G-02 invertiert | 2 | 255→0 | | | | |
| G-03 Stufen/64…192 | 1 | laut Fixture | | | | |
| G-04 fehlend/Null/voll | 1 | –/0/255 | | | | |
| G-06 Alpha 0/128/255 | 1 | Gloss 128 | | | | |
| G-07 HEIGHT 0/32768/65535 | 1 | Gloss 128 | | | | |
| G-08 Registrierung/Schachbrett | 1 | 0/255 | | | | |

## 7. Entscheidungstabelle nach dem Druck

| Frage | Bestätigter Wert | Evidenz | Status |
| --- | --- | --- | --- |
| Wertebereich/Bittiefe/Modus | 0…255 / 8 Bit / `L` als Testträger | Repositoryprüfung | Träger belegt; Studioakzeptanz offen |
| Richtung | | G-02 + Hersteller A11 | offen |
| kontinuierlich/quantisiert/binär/normalisiert | | G-03 | offen |
| Maskierung durch COLOR-Alpha | | G-06 | offen |
| Abhängigkeit von HEIGHT | | G-07 | offen |
| Optionalität/Nullverhalten | keine Rolle schreibt keine Datei | G-04a; Druckvergleich G-04 offen | teilweise belegt |
| Dimensionsregel | Writer blockiert; Studio-Fremddatenverhalten | G-05 | Writer belegt, Studio offen |
| Registrierung/minimale Struktur | | G-08 | offen |

Erst wenn diese Tabelle physisch befüllt ist, darf #691 die experimentelle
Gloss-Warnung durch ein versioniertes Zielprofil ersetzen. Versions-, Material-
oder Ink-Mode-Abweichungen bleiben sichtbare Profilgrenzen oder werden als
Folge-Issue erfasst.
