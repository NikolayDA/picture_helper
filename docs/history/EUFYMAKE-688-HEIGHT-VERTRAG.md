# EufyMake-HEIGHT-Vertrag – Ergebnisakte für Issue #688

> **Status: Druckmessung ausstehend; drei kontrollierte Studio-Importe und die
> native HEIGHT-Zuweisung sind protokolliert.** Dieses Dokument trennt Herstellerangaben,
> repositoryseitige Dateiprüfungen, Studio-Importbeobachtungen und noch offene
> Druckmessungen strikt voneinander. Leere Messfelder sind kein negatives
> Ergebnis und dürfen nicht als Bestätigung interpretiert werden.

## 1. Geltungsbereich und Testumgebung

| Merkmal | Wert/Nachweis |
| --- | --- |
| EufyMake Studio | 4.2.2 |
| Editor-Version | 1.20.0 (Versionshinweis im Editor) |
| E1-Firmware | |
| Hardware/Flatbed | E1 im Editor online; kein Druck gestartet |
| Betriebssystem | macOS 26.6.2 (Build 25G83) |
| Material/Tinte/Ink-Mode | |
| Texturmodus und Höhenregler | `Customize Texture`; Regler nicht verändert |
| Messmittel | |
| Geschätzte Messunsicherheit | |
| Pre-Import-Report | 34/34 erfolgreich; Manifest-Schema 2; erwarteter Manifest-SHA-256 `794e7890d169516900534b7a0166b5cd477589bef05d952c045db2a45d172308`; Report-SHA-256 `06314d3bd605a6535c467481b82f22de6d6a2f601207d679ddf85d9cfe2ffdcf`; Pillow 12.3.0 |
| Foto-/Messdatenablage | gemäß `EUFYMAKE-687-TESTGOVERNANCE.md` |

## 2. Bereits belegter Ausgangsstand

| Aussage | Kategorie | Evidenz | Status |
| --- | --- | --- | --- |
| PNG-Graustufen-HEIGHT wird vom Hersteller beschrieben; 16 Bit/Kanal wird empfohlen, wenn verfügbar. | Herstellerangabe | A2 in `EUFYMAKE-687-ANNAHMENINVENTAR.md` | belegt |
| Weiß entspricht hoch, Schwarz niedrig. | Herstellerangabe | A2/A3 im Annahmeninventar | belegt |
| Die Datei trägt relative Grauwerte, keine absolute mm-Höhe. | Herstellerangabe/Ableitung | EM-H03 V2 | belegt; mm-Abbildung offen |
| Stand #948 (Schema 2; seit #952 Schema 4 mit 41 Fixtures und 7 Paketen, Neuprüfung siehe `EUFYMAKE-690-GLOSS-VERTRAG.md`): Die 34 versionierten Fixtures stimmen in SHA-256, Bytegröße, IHDR, Chunkfolge, `pHYs` und CRC mit dem separat per SHA-256 verankerten Schema-2-Manifest überein. Der von Pillow gemeldete Modus wird diagnostisch protokolliert, ist aber wegen möglicher Versionsunterschiede kein hartes Kriterium. | Dateiprüfung, keine Studioaussage | `scripts/eufymake_fixture_inspector.py`; lokaler Basisreport | belegt |
| Studio nutzt tatsächlich alle 65.536 Werte und bildet sie auf eine bestimmte mm-Kennlinie ab. | – | keine Hardwaremessung | offen |

## 3. Kriterien- und Evidenzmatrix

Die Zellen stehen im Detail in
[`EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`](EUFYMAKE-687-PROTOKOLL-VORLAGEN.md).
Vor jedem Import muss der unabhängige JSON-Report am Zielrechner erfolgreich
neu erzeugt werden.

| #688-Kriterium | Zelle/Fixture | Importnachweis | Druck-/Messnachweis | Ergebnis |
| --- | --- | --- | --- | --- |
| 8 Bit vs. 16 Bit akzeptiert/genutzt | I-03, `height_wedge_8bit.png`, `height_wedge_16bit.png` | | | offen |
| Minimal-/Mittel-/Maximalwert | `height_zero_*`, `height_mean_*`, I-07 `height_max_*`, I-11 Stufen | | | offen |
| Richtung und Monotonie | I-02/I-03 Keil, invertierte HEIGHT-Fixtures als Gegenprobe | | | offen |
| Quantisierung/Clipping/Tonwertauflösung | I-03, I-07, I-11 | | | offen |
| Nullpunkt/Grundfläche | `height_zero_16bit.png`, Kontrollkörper | | | offen |
| Digitalwert → physische Höhe | I-11; Messpunkte je Stufe in mm | | | offen |
| Höhenregler/Texturmodus als Skalierungsachse | konstante Einstellung je Vergleich; ggf. eigene Matrixzeile | | | offen |
| Fehlend/Nullfläche/konstant/Dimensionsabweichung | I-01, `height_zero_16bit.png`, `height_mean_16bit.png`, I-04/I-12 | | | offen |
| Alpha/Coverage bei nicht-null HEIGHT | I-13, `color_alpha_coverage.png` + `height_mean_16bit.png` | | | offen |
| Crop-/Registrierungstreue | I-08, `color_height_reference.png` + `height_registration_16bit.png` mit pixelgleichen X/Y-Landmarken | | | offen |
| Filterung/Glättung/Normalisierung | `height_impulse_edge_*`, Keile | | | offen |
| Reproduzierbarkeit | zweiter unabhängiger Lauf der Kernaussagen | | | offen |

### Importbeobachtungen vom 2. und 3. September 2026

Die folgenden Beobachtungen entstanden nach erfolgreichem Pre-Import-Check in
einem neuen, ungespeicherten Studio-Projekt. Sie belegen ausschließlich das
Editorverhalten. Es wurde weder `Preview & Print` ausgelöst noch ein physischer
Druck gestartet. Die während der Sitzung aufgenommenen Screenshots wurden
nicht als dauerhafte Evidenz abgelegt; deshalb bleiben die zugehörigen
Abnahmekriterien bis zur reproduzierbaren Ablage und Druckmessung offen.

| Zelle | Kontrolliertes Paar | Beobachtung | Einordnung |
| --- | --- | --- | --- |
| I-02 | `color_height_reference.png` + `height_wedge_16bit.png` | Beide Dateien wurden ohne sichtbare Importwarnung akzeptiert. COLOR und HEIGHT besitzen 256×256 Pixel; Studio zeigte für COLOR 90,31×90,31 mm. `Customize Texture` erzeugte eine sichtbare 3D-Vorschau. | Importbeobachtung; akzeptierter 16-Bit-Träger und dimensionsgleiche Kopplung, aber keine belastbare Aussage zu Monotonie, Bittiefennutzung oder mm-Höhe. Dieses Paar wird nicht mehr für I-08 verwendet. |
| I-13 | `color_alpha_coverage.png` + `height_mean_16bit.png` (konstant 32768) | Das nach dem Review korrigierte COLOR-Fixture wurde erneut ohne sichtbare Importwarnung akzeptiert. Alle drei Felder tragen RGB `(40, 80, 220)`; auf der Leinwand ließ Alpha 0 den Untergrund vollständig sichtbar, Alpha 128 mischte das mittlere Feld, Alpha 255 deckte das rechte Feld. Die unveränderte nicht-null 16-Bit-HEIGHT-Datei war im selben Prüfpfad bereits akzeptiert worden und hatte eine 3D-Vorschau erzeugt. | Importbeobachtung; die COLOR-Seite variiert nur Alpha und vermeidet den früheren RGB-Störfaktor. Unterbase, Deckung und physische Reliefhöhe bleiben ohne Druck offen. |
| I-08 | `color_height_reference.png` + `height_registration_16bit.png` | Am 2026-09-03 wurde COLOR importiert und über `Customize Texture` → `Upload Height Map Image` die 16-Bit-HEIGHT-Datei nativ zugewiesen. Studio akzeptierte sie ohne Warnung, kennzeichnete das Objekt mit `3D` und zeigte die asymmetrischen Landmarken in der 3D-Vorschau. Ein anschließend bestätigter Crop reduzierte W von 90,31 auf 44,86 mm und verschob X von 122,34 auf 167,79 mm; H 90,31 mm und Y 164,84 mm blieben erhalten. Die `3D`-Zuordnung und die passend beschnittene 3D-Vorschau blieben bestehen. Die separat importierte `gloss_registration.png` blieb dagegen unverändert bei 90,31×90,31 mm und X/Y 122,34/164,84 mm. | Importbeobachtung: nativer 16-Bit-HEIGHT-Träger und Crop-Kopplung innerhalb des COLOR/HEIGHT-Objekts belegt. Keine Aussage zur Nutzung aller 65.536 Werte, mm-Höhe oder physischen Registrierung; ein separater Gloss-Layer folgt dem Crop nicht automatisch. Weder `Preview` noch `Print` wurde ausgelöst. |

## 4. Messschema für HEIGHT → mm

Für I-11 je Stufe mindestens den tatsächlichen 16-Bit-Digitalwert aus dem
Manifest/Fixture, die sichtbare Studiointerpretation und die physische Höhe
mit Unsicherheit dokumentieren. Keine Gerade erzwingen: Rohmesspunkte zuerst
eintragen, danach Linearität, Stufenbildung, Clipping oder Normalisierung
bewerten.

| Stufe | Digitalwert (16 Bit) | Studio-Anzeige/Regler | Höhe Lauf 1 (mm) | Höhe Lauf 2 (mm) | Unsicherheit (mm) | Abweichung | Bemerkung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 (Minimum) | 0 | | | | | | |
| 2 | 9362 | | | | | | |
| 3 | 18724 | | | | | | |
| 4 | 28086 | | | | | | |
| 5 | 37449 | | | | | | |
| 6 | 46811 | | | | | | |
| 7 | 56173 | | | | | | |
| 8 (Maximum) | 65535 | | | | | | |

## 5. Abschlussentscheidung

Dieser Abschnitt wird erst ausgefüllt, wenn die referenzierten Import- und
Drucknachweise vorliegen. Jede Zeile erhält eine Kategorie
„Herstellerangabe“, „Importbeobachtung“ oder „Druckmessung“.

| Vertragsfeld | Entscheidung | Kategorie | Evidenz/Begründung |
| --- | --- | --- | --- |
| Akzeptierter Träger/PNG-Farbtyp | | | |
| Empfohlene Bittiefe | | | |
| Wertebereich | | | |
| Richtung (hell/dunkel) | | | |
| Bedeutung von 0/Grundfläche | | | |
| Default für BgRemover | | | |
| Clipping-/Normalisierungsregel | | | |
| Digitalwert→mm bzw. ausdrücklich „nicht ableitbar“ | | | |
| Verhalten bei Alpha/Coverage | | | |
| Validator-Schweregrad je Abweichung | | | |
| Sichere Behandlung offener Widersprüche | | | |

### Vorläufiger sicherer Default bis zur Hardwaremessung

Aus den Herstellerangaben und dem bereits versionierten App-Vertrag folgt nur
ein **vorläufiger**, nicht hardwarevalidierter Default: 16-Bit-Graustufen-PNG,
digitaler Bereich 0…65535, Schwarz niedrig/Weiß hoch, Werte beim Schreiben
klemmen und keine mm-Höhe aus der Datei versprechen. 8-Bit bleibt als
kompatible Vergleichs-/Legacy-Variante eine Warnung statt eines Fehlers. Eine
Änderung dieses Defaults oder seiner Validator-Schweregrade braucht die
ausgefüllten Messfelder oben; fehlende Hardwareevidenz darf nicht als grüner
Test gewertet werden.
