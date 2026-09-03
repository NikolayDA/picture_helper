# EufyMake-HEIGHT-Vertrag – Ergebnisakte für Issue #688

> **Status: Druckmessung ausstehend; alle verpflichtenden druckfreien
> HEIGHT-Importzellen sind protokolliert.** Dieses Dokument trennt Herstellerangaben,
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
| Texturmodus und Höhenregler | `Customize Texture`; Ink Mode `Color Raised`; Stärke 2,50 mm; Regler nicht verändert |
| Messmittel | |
| Geschätzte Messunsicherheit | |
| Pre-Import-Report | 41/41 Fixtures und 7/7 Exportpakete erfolgreich; Manifest-Schema 4; erwarteter und tatsächlicher Manifest-SHA-256 `8e799f245f177947d0401c431feb0d41df0cde9b5007e4243c1add679a8e8758`; Report-SHA-256 `8c7264f842395a21a55b93006f2f598b08eb71cc95c528a53b21b5531daf885f` |
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
| 8 Bit vs. 16 Bit akzeptiert/genutzt | I-03, `height_wedge_8bit.png`, `height_wedge_16bit.png` | beide nativ ohne Warnung akzeptiert; vergleichbare 3D-Keilvorschau | | Import belegt; tatsächliche Präzisionsnutzung offen |
| Minimal-/Mittel-/Maximalwert | `height_zero_*`, `height_mean_*`, I-07 `height_max_*`, I-11 Stufen | Null und Vollweiß nativ als konstante Grenzflächen, Mittelwert im nativen I-13-Paar sowie acht Stufen sichtbar | | Studio-Teil belegt; physische Höhe offen |
| Richtung und Monotonie | I-02/I-03 Keil, invertierte HEIGHT-Fixtures als Gegenprobe | Normaler 16-Bit-Keil 0→65535 von links nach rechts und invertierte Gegenprobe 65535→0 nativ akzeptiert; die 3D-Neigungsrichtung kehrte sich beim direkten Wechsel sichtbar um | | Editorseitige Richtung/Polarität belegt; physische Monotonie offen |
| Quantisierung/Clipping/Tonwertauflösung | I-03, I-07, I-11 | Vollweiß als Plateau, acht Sollstufen getrennt sichtbar; 8/16 Bit ohne sichtbare Differenz bei dieser Vorschau | | Editorbeobachtung belegt; Druckauflösung/Clipping offen |
| Nullpunkt/Grundfläche | `height_zero_16bit.png`, Kontrollkörper | Null-HEIGHT nativ ohne Warnung akzeptiert und als ebene Grundfläche dargestellt | | Import belegt; tatsächlicher physischer Nullpunkt offen |
| Digitalwert → physische Höhe | I-11; Messpunkte je Stufe in mm | | | offen |
| Höhenregler/Texturmodus als Skalierungsachse | konstante Einstellung je Vergleich; ggf. eigene Matrixzeile | `Customize Texture`, `Color Raised`, 2,50 mm für die Vergleiche unverändert | | Vergleichsparameter belegt; physische Skalierung offen |
| Fehlend/Nullfläche/konstant/Dimensionsabweichung | I-01, `height_zero_16bit.png`, `height_mean_16bit.png`, I-04/I-12 | COLOR allein akzeptiert; Null, konstante Mitte und Maximum nativ akzeptiert; halbe Pixelkante bei gleichem Verhältnis auf volle Fläche abgebildet; abweichendes Seitenverhältnis ausdrücklich abgelehnt | | Importvertrag belegt; physische Auswirkung nur für akzeptierte Varianten offen, I-12 ist import-only |
| Alpha/Coverage bei nicht-null HEIGHT | I-13, `color_alpha_coverage.png` + `height_mean_16bit.png` | HEIGHT im selben COLOR-Objekt nativ zugewiesen; `3D`-Vorschau mit drei weiterhin sichtbaren Alpha-/Farbfeldern | | Importkopplung belegt; physische Coverage/Underbase offen |
| Crop-/Registrierungstreue | I-08, `color_height_reference.png` + `height_registration_16bit.png` mit pixelgleichen X/Y-Landmarken | | | offen |
| Filterung/Glättung/Normalisierung | I-02/I-04 als 256×256-/128×128-Vergleich bei gleicher Seitenrelation; `height_impulse_edge_*`, Keile | | | offen |
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
| I-02 | `color_height_reference.png` + `height_wedge_16bit.png` | Beide Dateien wurden ohne sichtbare Importwarnung akzeptiert. COLOR und HEIGHT besitzen 256×256 Pixel; Studio zeigte für COLOR 90,31×90,31 mm. `Customize Texture` erzeugte eine sichtbare 3D-Vorschau. | Importbeobachtung; akzeptierter 16-Bit-Träger und dimensionsgleiche Kopplung. Dieses Paar allein belegt weder physische Monotonie noch Bittiefennutzung oder mm-Höhe; die editorseitige Richtung wird durch die I-03-Gegenprobe abgesichert. Dieses Paar wird nicht mehr für I-08 verwendet. |
| I-03 | `color_height_reference.png` + `height_wedge_8bit.png`, `height_wedge_16bit.png` und `height_wedge_inverted_16bit.png` | Beide Bittiefen wurden nativ ohne Warnung akzeptiert und zeigten bei identischem `Color Raised`-/2,50-mm-Aufbau eine vergleichbare Keilvorschau. Beim direkten Wechsel vom Normalkeil 0→65535 links→rechts zur invertierten Gegenprobe 65535→0 kehrte sich die 3D-Neigungsrichtung sichtbar um. | Importbeobachtung: Trägerakzeptanz und editorseitige Fixture-Polarität belegt; die Ausnutzung zusätzlicher 16-Bit-Stufen sowie physische Monotonie bleiben Druckmessung. |
| I-04 | `color_height_reference.png` + `height_wedge_16bit_half.png` | Die 128×128-HEIGHT-Datei mit gleichem 1:1-Seitenverhältnis wurde ohne Warnung auf dem 256×256-COLOR-Objekt akzeptiert. Das Objekt blieb 90,31×90,31 mm; die Höhenvorschau belegte die volle Fläche. | Importbeobachtung: absolute Pixelgleichheit ist für diesen Pfad nicht erforderlich, das Seitenverhältnis dagegen relevant. Filterung/Interpolation und Druckwirkung bleiben offen. |
| I-07 | `color_height_reference.png` + `height_max_16bit.png` beziehungsweise `height_zero_16bit.png` | Vollweiß wurde ohne Warnung als gleichmäßiges Plateau dargestellt; die anschließend nativ geladene Null-Gegenprobe ebenfalls ohne Warnung als ebene Grundfläche. `Color Raised` und 2,50 mm blieben unverändert. | Importbeobachtung: beide konstanten Grenzträger akzeptiert; tatsächliche Null-/Maximalhöhe, Sättigung und Clipping bleiben offen. |
| I-11 | `color_height_reference.png` + `height_steps_16bit.png` | Die 16-Bit-Treppenkarte wurde ohne Warnung akzeptiert; acht diskrete Plateaus waren in der 3D-Vorschau erkennbar. | Importbeobachtung: Stufentrennung im Editor belegt; Digitalwert→mm-Kennlinie und Reproduzierbarkeit bleiben Druckmessung. |
| I-12 | `color_height_reference.png` + `height_wedge_16bit_aspect.png` | Studio zeigte exakt `Depth image ratio does not match the original image`. Die 256×128-HEIGHT-Datei wurde für das 256×256-COLOR-Objekt nicht übernommen; die vorherige Treppen-HEIGHT-Zuweisung und Objektgeometrie blieben unverändert. | Importbeobachtung: abweichende Seitenrelation wird fail-closed abgelehnt; keine stille Skalierung. |
| I-13 | `color_alpha_coverage.png` + `height_mean_16bit.png` (konstant 32768) | Das COLOR-Fixture wurde importiert und die 16-Bit-HEIGHT-Datei anschließend im selben Objekt nativ über `Customize Texture` zugewiesen. Studio akzeptierte die Kopplung ohne Warnung, kennzeichnete das Objekt mit `3D` und zeigte eine gleichmäßig hohe Vorschau, in der die drei Alpha-/Farbfelder weiter erkennbar blieben. | Importbeobachtung: Alpha×konstantes nicht-null HEIGHT ist im nativen COLOR/HEIGHT-Pfad vorgeprüft. Unterbase, Deckung und physische Reliefhöhe bleiben ohne Druck offen. |
| I-08 | `color_height_reference.png` + `height_registration_16bit.png` | Am 2026-09-03 wurde COLOR importiert und über `Customize Texture` → `Upload Height Map Image` die 16-Bit-HEIGHT-Datei nativ zugewiesen. Studio akzeptierte sie ohne Warnung, kennzeichnete das Objekt mit `3D` und zeigte die asymmetrischen Landmarken in der 3D-Vorschau. Ein anschließend bestätigter Crop reduzierte W von 90,31 auf 44,86 mm und verschob X von 122,34 auf 167,79 mm; H 90,31 mm und Y 164,84 mm blieben erhalten. Die `3D`-Zuordnung und die passend beschnittene 3D-Vorschau blieben bestehen. Die separat importierte `gloss_registration.png` blieb dagegen unverändert bei 90,31×90,31 mm und X/Y 122,34/164,84 mm. | Importbeobachtung: nativer 16-Bit-HEIGHT-Träger und Crop-Kopplung innerhalb des COLOR/HEIGHT-Objekts belegt. Keine Aussage zur Nutzung aller 65.536 Werte, mm-Höhe oder physischen Registrierung; ein separater Gloss-Layer folgt dem Crop nicht automatisch. Weder `Preview` noch `Print` wurde ausgelöst. |

I-12 ist damit ein abgeschlossener **Import-Negativtest**: Weil Studio die
HEIGHT-Datei nicht übernimmt, existiert kein I-12-Objekt für Vorschau oder
Druck. Die Zelle hat deshalb keine physische Messzeile; für den abgelehnten
2:1-Seitenverhältnis-Fall ist eine Druckmessung nicht anwendbar. Die
akzeptierten I-02- und I-04-Objekte bleiben bei identischer Layoutgröße,
Texturhöhe und Druckeinstellung als separate Pixelgrößen-/Filterprüfung
erhalten. Ihre Filter-/Interpolationsmessung bei gleicher 1:1-Seitenrelation
darf nicht als physische Evidenz für I-12 gewertet werden.

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
