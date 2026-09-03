# EufyMake-Gloss-/Coverage-Vertrag – Ergebnisakte für Issue #690

> **Status: reproduzierbarer Datei- und Studio-Importtestsatz vollständig;
> allgemeine Verfügbarkeit des nativen `Gloss Varnish`-Pfads belegt,
> zellspezifischer Preflight und physische Klarlackmessung ausstehend.** Dieses Dokument trennt Herstellerangabe,
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
| Material/Tinte/Klarlack/Ink-Mode | nativer Studio-Modus `Gloss Varnish` auswählbar; Material/Geräteparameter ausstehend; kein Druck gestartet |
| Beleuchtung/Messmittel | ausstehend |
| Fixture-Katalog | Schema 5; 42 Einzel-Fixtures; 7 unveränderte Exportpakete |
| Manifest-Vertrauensanker | `7c0b788cb614068c5e1d2a9ea4453929b2278d0e60fd8206d0c5ff5ed213627a` |
| Pre-Import-Report | 42/42 Fixtures und 7/7 Pakete OK; Report-SHA-256 `4c418ccceac01b43b3aee615d89574f590a342da88dd4ad9941522e026b3603b` |

Vor jedem weiteren Studio- oder Drucklauf ist der Report neu zu erzeugen:

```bash
.venv/bin/python scripts/eufymake_fixture_inspector.py \
  --fixture-dir tests/fixtures/eufymake_hardware \
  --expected-manifest-sha256 7c0b788cb614068c5e1d2a9ea4453929b2278d0e60fd8206d0c5ff5ed213627a \
  --output eufymake-690-pre-import.json
```

Schema 5 ergänzt ausschließlich das I-14-HEIGHT-Einzelfixture. Die sieben
Writer-Pakete und ihre Manifeste bleiben bytegleich zum in Studio geprüften
Stand; die Gloss-Evidenz wird durch die Katalogerweiterung nicht umgedeutet.

## 2. Belegter Ausgangsstand

| Aussage | Evidenzklasse | Quelle | Status |
| --- | --- | --- | --- |
| Der Hersteller beschreibt einen separaten Spot-UV-Dateiworkflow; in dessen Schwarz-Weiß-Maske bedeutet Schwarz „Gloss auftragen“, Weiß „nichts“. | Herstellerangabe | A11 in `EUFYMAKE-687-ANNAHMENINVENTAR.md` | belegt für den beschriebenen Workflow; noch nicht als Verhalten unseres Assets gedruckt |
| `gloss_mask.png` ist eine experimentelle BgRemover-Konvention, kein bestätigter nativer Studio-Paketvertrag. | Produkt-/Repositoryvertrag | `eufymake_export.py`, ADR | belegt |
| Ohne explizite GLOSS-Rolle erzeugt der Writer weder Datei noch Manifestreferenz. | Repositoryprüfung | Paket `gloss_absent`, Generator- und Writer-Tests | belegt |
| Eine vorhandene Nullfläche und eine fehlende Gloss-Datei sind unterschiedliche Pakete. | Repositoryprüfung | `gloss_zero` gegenüber `gloss_absent` | belegt |
| Studio trägt bei einem importierten Graustufenbild tatsächlich Klarlack auf. | – | kein Druckbefund | offen |

## 3. Isolierte Testzellen

Alle Einzelbilder sind deterministisch auf Pixel-/Metadatenebene, ohne
Zufallszahlen, 8-Bit-Graustufen für Gloss und – sofern vorhanden – pixelgenau
über das Schema-4-Manifest gebunden. Der Manifest-SHA bindet die exakt
committeten Transportbytes; eine Neu-Kompression auf einer anderen zlib-Laufzeit
darf semantisch identische Deflate-Bytes erzeugen und wird deshalb nicht als
plattformübergreifender Bytevertrag behandelt. HEIGHT bleibt 16 Bit. Die Pakete
entstehen über den Produktionswriter und behalten dessen PNG-Bytes; nur das
Dimensionsfehlerpaket ersetzt anschließend kontrolliert die Gloss-Datei.

| Zelle | Dateien/Paket | Isolierte Variable | Digitaler Sollwert | Import | Druck |
| --- | --- | --- | --- | --- | --- |
| G-01 | `gloss_min.png`, `gloss_mean.png`, `gloss_max.png` | Minimum/Mitte/Maximum | 0 / 128 / 255 | als drei getrennte „Flat“-Ebenen importiert | ausstehend |
| G-02 | `gloss_wedge.png`, `gloss_wedge_inverted.png` | Polarität | 0→255 / 255→0 | beide getrennt und ohne Warnung importiert | ausstehend |
| G-03 | `gloss_steps.png`, `gloss_wedge_limited.png` | kontinuierlich, quantisiert, binär oder normalisiert | 8 Stufen 0…255 / Keil 64…192 | beide getrennt und ohne Warnung importiert | ausstehend |
| G-04a | `export_gloss_absent/` | keine Gloss-Rolle | keine Datei/Referenz | Paket semantisch geprüft; Studio-Bilddialog importiert kein Manifest | ausstehend |
| G-04b | `export_gloss_zero/` | vorhandene Nullfläche | 0 | tatsächliche `gloss_mask.png` am 2026-09-03 ohne Warnung als sichtbare schwarze „Flat“-Ebene importiert; 90,31×90,31 mm | ausstehend |
| G-04c | `export_gloss_full/` | voll gesetzte Fläche | 255 | tatsächliche `gloss_mask.png` am 2026-09-03 ohne Warnung als sichtbare weiße „Flat“-Ebene importiert; 90,31×90,31 mm | ausstehend |
| G-05 | `export_gloss_dimension_mismatch/` | Dimensionsregel | COLOR/Manifest 256×256; Gloss 128×256 | Gloss separat als 45,16×90,31 mm importiert; kein Scaling/Fehler | nur falls Import sicher interpretierbar |
| G-06 | `export_gloss_alpha_coverage/` | COLOR-Alpha bei konstantem Gloss/HEIGHT | Alpha 0/128/255; RGB konstant; Gloss 128; HEIGHT 32768 | drei PNGs als unabhängige „Flat“-Ebenen importiert | ausstehend |
| G-07 | `export_gloss_height_cross/` | HEIGHT bei konstantem Gloss/COLOR | HEIGHT 0/32768/65535; Gloss 128; COLOR opak | drei PNGs als unabhängige „Flat“-Ebenen importiert | ausstehend |
| G-08 | `gloss_registration.png`, `gloss_checkerboard.png` | Registrierung, Filterung, Bleeding | Landmarkmaske 0/255; 16-px-Schachbrett | beide als getrennte „Flat“-Ebenen importiert | ausstehend |

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

## 5. Studio-Import- und Rollenprotokoll

Live-Sitzung am 2026-09-02 mit Studio 4.2.2 / Editor 1.20.0 und online
angezeigtem E1. Die Dateien wurden nach erfolgreichem Inspectorlauf einzeln
über den Bilddialog importiert. Es wurde weder **Preview** noch **Print**
ausgelöst. Alle 256×256-PNGs ohne `pHYs` erschienen bei 72-dpi-Fallback mit
90,31×90,31 mm, X/Y 122,34/164,84 mm und 0°. Studio leitete aus Dateiname,
Graustufenmodus oder gemeinsamem Exportordner keine COLOR-/HEIGHT-/GLOSS-Rolle
und keine Beziehung zwischen den Ebenen ab.

| Zelle | Datum/Version | Warnung | Darstellung/Größe | automatische Änderung | „Nichts passiert"? (EM-S03) | Aussagegrenze |
| --- | --- | --- | --- | --- | --- | --- |
| G-01 | 2026-09-02; 4.2.2/1.20.0 | keine | 0/128/255 sichtbar; je 90,31×90,31 mm; drei getrennte „Flat“-Ebenen | keine | Nein; alle drei sichtbar | Keine Aussage über Klarlack ohne Druck |
| G-02 | 2026-09-02; 4.2.2/1.20.0 | keine | normaler und invertierter Keil je 90,31×90,31 mm; getrennte „Flat“-Ebenen | keine | Nein; beide sichtbar | Invertierte Bilddarstellung ist noch keine Polaritätsbestätigung |
| G-03 | 2026-09-02; 4.2.2/1.20.0 | keine | Stufen und 64…192-Keil je 90,31×90,31 mm; Tonwerte sichtbar | keine | Nein; beide sichtbar | Tonwertanzeige ist noch keine Intensitätskennlinie |
| G-04a/b/c | 2026-09-02/03; 4.2.2/1.20.0 | keine PNG-Warnung | fehlend nur als Paketvertrag prüfbar; tatsächliche Null-/Voll-Writer-Assets schwarz/weiß sichtbar, je 90,31×90,31 mm und „Flat“ | keine; JSON im bereits geprüften Bilddialog nicht auswählbar | G-04a: n. z. (keine Gloss-Datei); G-04b/c: Nein, beide Writer-Assets sichtbar | Studio-Bildimport besitzt keinen beobachtbaren Paket-/Optionalitätsvertrag; Writer-Asset-Import belegt, Gloss-Semantik und physische Optionalität bleiben offen |
| G-05 | 2026-09-02; 4.2.2/1.20.0 | keine | 128×256 px separat als 45,16×90,31 mm, X/Y 144,91/164,84 mm, 0° | kein Scaling, kein Beschnitt, keine Ablehnung | Nein; sichtbar | Studio erkennt keinen Dimensionskonflikt, weil es keine Rollen verknüpft |
| G-06 | 2026-09-02; 4.2.2/1.20.0 | keine | COLOR, HEIGHT und konstantes Gloss je separat 90,31×90,31 mm; Alpha-Felder im COLOR sichtbar | alle „Flat“; keine Rollenzuordnung oder Maskenkopplung | Nein; alle drei sichtbar | COLOR-Alpha-Wirkung auf physischen Gloss-Auftrag bleibt offen |
| G-07 | 2026-09-02; 4.2.2/1.20.0 | keine | COLOR, 16-Bit-HEIGHT 0/32768/65535 und Gloss je separat 90,31×90,31 mm | alle „Flat“; keine Rollenzuordnung oder Maskenkopplung | Nein; alle drei sichtbar | HEIGHT-Wirkung auf physischen Gloss-Auftrag bleibt offen |
| G-08 | 2026-09-02; 4.2.2/1.20.0 | keine | Registrierung und Schachbrett je separat 90,31×90,31 mm | beide „Flat“; keine gemeinsame Registrierung erzeugt | Nein; beide sichtbar | Registrierung, Filterung und Bleeding im Druck separat messen |

**Importbefund:** Der Studio-Bilddialog akzeptiert die kontrollierten 8-Bit-
Gloss-Träger und den 16-Bit-HEIGHT-Kreuzträger als sichtbare Bildobjekte. Das
ist ausschließlich ein Akzeptanz- und Geometriebefund. Die getrennten Ebenen
belegen gerade **keine** native Gloss-Semantik; eine physische Polarität,
Mengenkennlinie, Alpha-Maskierung oder HEIGHT-Wechselwirkung lässt sich daraus
nicht ableiten.

Für G-04b/c wurden am 2026-09-03 die tatsächlichen
`export_gloss_zero/full/gloss_mask.png`-Dateien sichtbar importiert. Beide
erschienen ohne Warnung als getrennte „Flat“-Ebenen (Null schwarz, Voll weiß),
je 90,31×90,31 mm und X/Y 122,34/164,84 mm. EM-S03 ist damit für beide
Writer-Assets mit „Nein" protokolliert. Weder **Preview** noch **Print** wurde
ausgelöst; Gloss-Rollenzuordnung und physische Wirkung bleiben offen.

### Nativer Gloss-Preflight vom 2026-09-03

Auf der separat importierten `gloss_registration.png` wurde im rechten
Eigenschaftenbereich der Ink Mode geöffnet. Studio 4.2.2 bot unter anderem
`Gloss Varnish`, `CMYK > Gloss Varnish` und
`White > CMYK > Gloss Varnish` an. Nach Auswahl von `Gloss Varnish` zeigte das
Objekt ausdrücklich Ink Mode `Gloss Varnish` und `Gloss Varnish × 1`; eine
Warnung erschien nicht. Damit ist Pfad 1 aus Abschnitt 6.1 für diese
Studio-Version grundsätzlich verfügbar. Der Preflight belegt weder
Schwarz/Weiß-Polarität noch Intensitätskennlinie, Materialeignung oder
physischen Klarlackauftrag. Weder `Preview` noch `Print` wurde ausgelöst.

## 6. Physisches Mess- und Fotoprotokoll

### 6.1 Verbindliche Gloss-Zuweisung vor jedem physischen Lauf

Die in Abschnitt 5 beobachteten **Flat**-Ebenen dürfen nicht direkt als
Graustufen-CMYK-/Normalbild gedruckt und anschließend als Gloss-Befund gewertet
werden. Vor dem ersten Materialverbrauch ist genau einer der folgenden
Gloss-Pfade auszuwählen und vollständig zu protokollieren:

1. **Nativer Studio-Pfad:** Eine in der verwendeten Studio-/Editor-Version
   sichtbare Funktion weist das importierte Maskenbild ausdrücklich der Rolle
   „Gloss“, „Spot UV“ oder „Varnish“ zu. Menüpfad, UI-Bezeichnung, Version,
   Polaritätsanzeige und Geräteoption werden notiert. Ohne eine solche
   ausdrückliche Rollenzuweisung ist dieser Pfad nicht zulässig.
2. **Dokumentierter Spot-UV-Zweipass:** COLOR/HEIGHT werden im ersten Pass
   gedruckt; im zweiten Pass wird ausschließlich die Schwarz-Weiß-Maske im
   Hersteller-Modus für Spot UV/Gloss/Klarlack ausgegeben. Dabei gilt die
   Herstellerzuordnung Schwarz = Gloss auftragen, Weiß = nichts. Die Maske
   bleibt unskaliert und unverändert; eine vom Gerät verlangte Invertierung
   muss als eigene Transformation samt resultierendem Hash dokumentiert werden.

Für beide Pfade bleiben Material, Geräteprofil, Ink-/Gloss-Modus, Passreihenfolge,
Ursprung, X/Y-Position, Skalierung und Rotation über alle Vergleichszellen
fixiert. Registrierung erfolgt über die G-08-Marken; zwischen Basis- und
Gloss-Pass werden weder Material noch Ursprung neu eingelegt. G-06 und G-07
verwenden COLOR/HEIGHT im Basispass und die konstante Gloss-Maske im exakt
registrierten Gloss-Pass. G-05 darf nur laufen, wenn vorab eine explizite
Dimensions-/Registrierungsregel festgelegt wurde; automatisches Skalieren ist
kein gültiger Befund.

Für **G-07** ist zusätzlich vor dem Basispass eine sichtbare native
HEIGHT-/Texture-Zuweisung erforderlich. Texturmodus, Relief-/Maximalhöhe,
Underbase, Passzahl und jede weitere HEIGHT-relevante Studio-/Geräteoption
werden einmal festgelegt und für 0/32768/65535 unverändert protokolliert. Ist
diese native Zuweisung in der verwendeten Version nicht eindeutig verfügbar,
bleibt G-07 blockiert; drei gewöhnliche Flat-Graustufenbilder sind kein Ersatz.

NikolayDA hat am 2026-09-02 das harte Gesamtbudget auf **35 physische Drucke**
erhöht. Elf zusätzliche Plätze sind G-01 bis G-08 fest zugeordnet: G-01
einmal, G-02 normal und invertiert jeweils zweimal sowie G-03, G-04a/b/c,
G-05, G-06, G-07 und G-08 jeweils einmal. Die konkrete Zuordnung zu den
Budgetplätzen 25–35 steht in `EUFYMAKE-687-DRUCK-CHECKLISTE.md`. Diese
Materialfreigabe ersetzt keinen HEIGHT-/Gloss-Preflight; ohne eindeutigen
nativen Pfad bzw. die für G-05 verlangte Dimensions-/Registrierungsregel
bleibt der jeweilige physische Lauf blockiert.

Der allgemeine Verfügbarkeits-Preflight des nativen Pfads ist seit 2026-09-03
für Studio 4.2.2 erfüllt (`Ink Mode` → `Gloss Varnish`). Vor jedem Lauf bleiben
die zellspezifischen Parameter und die Registrierung verbindlich festzulegen.
Für G-05 fehlt weiterhin die geforderte Dimensionsregel; für G-07 sind native
HEIGHT- und Gloss-Pfade zwar einzeln belegt, Reliefwerte und gemeinsamer
registrierter Aufbau aber noch offen.

**Abbruchkriterium:** Wenn weder eine native Gloss-Rolle noch der dokumentierte
Spot-UV-Zweipass eindeutig auswählbar ist, bleibt der physische Teil blockiert.
Dann wird weder **Preview** noch **Print** gestartet und insbesondere kein
gewöhnlicher Flat-Graustufendruck als Ersatz verwendet.

### 6.2 Messung und Nachweis

Für jeden ausdrücklich freigegebenen Lauf sind Material, Druckmodus,
Geräteoptionen, Klarlack-/Tintenstand, Position und Skalierung zu dokumentieren.
Fotos erhalten eine konstante Kameraposition, Belichtung, Weißabgleich und zwei
definierte Beleuchtungswinkel (frontal und streifend). Mindestens G-02 wird
zweimal unabhängig gedruckt; G-01/G-03 benötigen identische Parameter im selben
Vergleichslayout.

| Zelle/Feld | Lauf | Digitalwert | Gloss-Pfad/Pass + Registrierung | sichtbarer Gloss | Mess-/Fotoreferenz | Material/Ink-Mode | Abweichung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G-01 min/mittel/max | 1 | 0/128/255 | | | | | |
| G-02 normal | 1 | 0→255 | | | | | |
| G-02 normal | 2 | 0→255 | | | | | |
| G-02 invertiert | 1 | 255→0 | | | | | |
| G-02 invertiert | 2 | 255→0 | | | | | |
| G-03 Stufen/64…192 | 1 | laut Fixture | | | | | |
| G-04 fehlend/Null/voll | 1 | –/0/255 | | | | | |
| G-05 Dimensionsabweichung | 1 | Gloss 128×256 gegen COLOR 256×256 | | | | | |
| G-06 Alpha 0/128/255 | 1 | Gloss 128 | | | | | |
| G-07 HEIGHT 0/32768/65535 | 1 | Gloss 128 | | | | | |
| G-08 Registrierung/Schachbrett | 1 | 0/255 | | | | | |

## 7. Entscheidungstabelle nach dem Druck

| Frage | Bestätigter Wert | Evidenz | Status |
| --- | --- | --- | --- |
| Wertebereich/Bittiefe/Modus | 0…255 / 8 Bit / `L` als Testträger; nativer Ink Mode `Gloss Varnish` auswählbar | Repositoryprüfung + Studio-Import/-Preflight | Träger akzeptiert und ausdrücklicher Gloss-Modus verfügbar; physische Gloss-Semantik offen |
| Richtung | | G-02 + Hersteller A11 | offen |
| kontinuierlich/quantisiert/binär/normalisiert | | G-03 | offen |
| Maskierung durch COLOR-Alpha | | G-06 | offen |
| Abhängigkeit von HEIGHT | | G-07 | offen |
| Optionalität/Nullverhalten | keine Rolle schreibt keine Datei; Studio-Bilddialog hat keinen Paketvertrag | G-04a + Import; Druckvergleich G-04 offen | digital belegt; physisch offen |
| Dimensionsregel | Writer blockiert; Studio importiert 128×256 separat als 45,16×90,31 mm | G-05 | Writer und isolierter Studio-Import belegt; Rollenverbund offen |
| Registrierung/minimale Struktur | | G-08 | offen |

#691 führt bereits ein **vorläufiges** versioniertes Zielprofil ein, ersetzt die
experimentelle Gloss-Warnung aber ausdrücklich nicht. Erst wenn diese Tabelle
physisch befüllt ist, darf eine neue Profilversion Gloss-Richtung oder
-Intensität als bestätigt führen. Versions-, Material- oder Ink-Mode-
Abweichungen bleiben sichtbare Profilgrenzen oder werden als Folge-Issue erfasst.
