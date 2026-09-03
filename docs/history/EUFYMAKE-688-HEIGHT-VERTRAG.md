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
| E1-Firmware | vor Phase 3 abzulesen (Checkliste §0); Wert: |
| Hardware/Flatbed | E1 im Editor online; kein Druck gestartet |
| Betriebssystem | macOS 26.6.2 (Build 25G83) |
| Material/Tinte/Ink-Mode | Substrat vor Phase 3 festzulegen (Protokoll §3.0); Wert: |
| Texturmodus und Höhenregler | `Customize Texture`; Ink Mode `Color Raised`; Stärke 2,50 mm; Regler nicht verändert |
| Messmittel | vor Phase 3 nach §4.0 festzulegen (Protokoll §3.0); Wert: |
| Geschätzte Messunsicherheit | je Messgröße aus §4.0; Wert: |
| Pre-Import-Report | 42/42 Fixtures und 7/7 Exportpakete erfolgreich; Manifest-Schema 5; erwarteter und tatsächlicher Manifest-SHA-256 `7c0b788cb614068c5e1d2a9ea4453929b2278d0e60fd8206d0c5ff5ed213627a`; Report-SHA-256 `4c418ccceac01b43b3aee615d89574f590a342da88dd4ad9941522e026b3603b` |
| Foto-/Messdatenablage | gemäß `EUFYMAKE-687-TESTGOVERNANCE.md` |

## 2. Bereits belegter Ausgangsstand

| Aussage | Kategorie | Evidenz | Status |
| --- | --- | --- | --- |
| PNG-Graustufen-HEIGHT wird vom Hersteller beschrieben; 16 Bit/Kanal wird empfohlen, wenn verfügbar. | Herstellerangabe | A2 in `EUFYMAKE-687-ANNAHMENINVENTAR.md` | belegt |
| Weiß entspricht hoch, Schwarz niedrig. | Herstellerangabe | A2/A3 im Annahmeninventar | belegt |
| Die Datei trägt relative Grauwerte, keine absolute mm-Höhe. | Herstellerangabe/Ableitung | EM-H03 V2 | belegt; mm-Abbildung offen |
| Stand #948 (Schema 2), erweitert in #952 auf Schema 4 mit 41 Fixtures/7 Paketen und jetzt auf Schema 5 mit 42 Fixtures/7 unveränderten Paketen: Sämtliche versionierten Dateien stimmen in SHA-256, Bytegröße, IHDR, Chunkfolge, `pHYs` und CRC mit dem separat per SHA-256 verankerten Manifest überein. Der von Pillow gemeldete Modus wird diagnostisch protokolliert, ist aber wegen möglicher Versionsunterschiede kein hartes Kriterium. | Dateiprüfung, keine Studioaussage | `scripts/eufymake_fixture_inspector.py`; aktueller Schema-5-Report | belegt |
| Studio nutzt tatsächlich alle 65.536 Werte und bildet sie auf eine bestimmte mm-Kennlinie ab. | – | keine Hardwaremessung | offen |

## 3. Kriterien- und Evidenzmatrix

Die Zellen stehen im Detail in
[`EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`](EUFYMAKE-687-PROTOKOLL-VORLAGEN.md).
Vor jedem Import muss der unabhängige JSON-Report am Zielrechner erfolgreich
neu erzeugt werden.

| #688-Kriterium | Zelle/Fixture | Importnachweis | Druck-/Messnachweis | Ergebnis |
| --- | --- | --- | --- | --- |
| 8 Bit vs. 16 Bit akzeptiert/genutzt | I-03, `height_impulse_edge_8bit.png`, `height_impulse_edge_16bit.png` | beide nativ ohne Warnung akzeptiert; pixelgleiche Impuls-/Kantengeometrie und Kalibrierfläche in der 3D-Vorschau; 16 Bit enthält 4096 Sollstufen, 8 Bit quantisiert gröber | | Import belegt; tatsächliche Präzisionsnutzung offen |
| Minimal-/Mittel-/Maximalwert | `height_zero_*`, `height_mean_*`, I-07 `height_max_*`, I-11 Stufen | Null und Vollweiß nativ als konstante Grenzflächen, Mittelwert im nativen I-13-Paar sowie acht Stufen sichtbar | | Studio-Teil belegt; physische Höhe offen |
| Richtung und Monotonie | I-02/I-03 Keil, invertierte HEIGHT-Fixtures als Gegenprobe | Normaler 16-Bit-Keil 0→65535 von links nach rechts und invertierte Gegenprobe 65535→0 nativ akzeptiert; die 3D-Neigungsrichtung kehrte sich beim direkten Wechsel sichtbar um | | Editorseitige Richtung/Polarität belegt; physische Monotonie offen |
| Quantisierung/Clipping/Tonwertauflösung | I-03, I-07, I-11 | Vollweiß als Plateau, acht Sollstufen getrennt sichtbar; 8/16 Bit ohne sichtbare Differenz bei dieser Vorschau | | Editorbeobachtung belegt; Druckauflösung/Clipping offen |
| Nullpunkt/Grundfläche | `height_zero_16bit.png`, Kontrollkörper | Null-HEIGHT nativ ohne Warnung akzeptiert und als ebene Grundfläche dargestellt | | Import belegt; tatsächlicher physischer Nullpunkt offen |
| Digitalwert → physische Höhe | I-11; Messpunkte je Stufe in mm | | | offen |
| Höhenregler/Texturmodus als Skalierungsachse | konstante Einstellung je Vergleich; ggf. eigene Matrixzeile | `Customize Texture`, `Color Raised`, 2,50 mm für die Vergleiche unverändert | | Vergleichsparameter belegt; physische Skalierung offen |
| Fehlend/Nullfläche/konstant/Dimensionsabweichung | I-01, `height_zero_16bit.png`, `height_mean_16bit.png`, I-04/I-12 | COLOR allein akzeptiert; Null, konstante Mitte und Maximum nativ akzeptiert; halbe Pixelkante bei gleichem Verhältnis auf volle Fläche abgebildet; abweichendes Seitenverhältnis ausdrücklich abgelehnt | | Importvertrag belegt; physische Auswirkung nur für akzeptierte Varianten offen, I-12 ist import-only |
| Alpha/Coverage bei nicht-null HEIGHT | I-13, `color_alpha_coverage.png` + `height_mean_16bit.png` | HEIGHT im selben COLOR-Objekt nativ zugewiesen; `3D`-Vorschau mit drei weiterhin sichtbaren Alpha-/Farbfeldern | | Importkopplung belegt; physische Coverage/Underbase offen |
| Crop-/Registrierungstreue | I-08, `color_height_reference.png` + `height_registration_16bit.png` mit pixelgleichen X/Y-Landmarken | | | offen |
| Pixelmaß/Resampling (End-to-End) | I-02/I-04 als 256×256-/128×128-Vergleich bei gleicher Seitenrelation | I-04 wurde bereits im Fixture-Generator über float32, LANCZOS, `rint` und Clamp verkleinert | | kombinierter physischer End-to-End-Effekt offen; keine isolierte Studio-Filteraussage |
| Filterung/Glättung/Normalisierung | I-14: `height_impulse_edge_16bit.png` (256×256; zugleich I-03-Referenz) und `height_impulse_edge_direct_half_16bit.png` (128×128), beide direkt aus derselben normierten Formel und auf 1/4…3/4 begrenzt | beide nativ ohne Warnung akzeptiert; identische Objektgröße 90,31×90,31 mm; kein Fixture-Resampling; Vollbereichsnormalisierung würde Basis/Plateau messbar verschieben | | sauberer Import-Preflight belegt; physischer kombinierter Studio-/Druckpfad offen |
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
| I-03 | `color_height_reference.png` + `height_impulse_edge_8bit.png`, `height_impulse_edge_16bit.png`; Keile als Polaritätskontrolle | Beide Bittiefen der begrenzten Impuls-/Kanten-Druckvariante wurden nativ ohne Warnung akzeptiert; die untere Kalibrierfläche war sichtbar. Die 16-Bit-Datei enthält dort 4096 Sollstufen, die 8-Bit-Datei dieselbe Geometrie gröber quantisiert. Zusätzlich kehrte sich beim Wechsel zum invertierten Keil die 3D-Neigungsrichtung sichtbar um. | Importbeobachtung: Trägerakzeptanz, aussagefähige Bittiefen-Gegenprobe und editorseitige Fixture-Polarität belegt; tatsächliche Präzisionsnutzung und physische Monotonie bleiben Druckmessung. |
| I-04 | `color_height_reference.png` + `height_wedge_16bit_half.png` | Die 128×128-HEIGHT-Datei mit gleichem 1:1-Seitenverhältnis wurde ohne Warnung auf dem 256×256-COLOR-Objekt akzeptiert. Das Objekt blieb 90,31×90,31 mm; die Höhenvorschau belegte die volle Fläche. | Importbeobachtung: absolute Pixelgleichheit ist für diesen Pfad nicht erforderlich, das Seitenverhältnis dagegen relevant. Die kombinierte Pixelgrößen-/Resampling-Druckwirkung bleibt offen. Weil die Datei bereits im Fixture-Generator per LANCZOS verkleinert und gerundet wurde, ist keine isolierte Studio-Filteraussage möglich. |
| I-07 | `color_height_reference.png` + `height_max_16bit.png` beziehungsweise `height_zero_16bit.png` | Vollweiß wurde ohne Warnung als gleichmäßiges Plateau dargestellt; die anschließend nativ geladene Null-Gegenprobe ebenfalls ohne Warnung als ebene Grundfläche. `Color Raised` und 2,50 mm blieben unverändert. | Importbeobachtung: beide konstanten Grenzträger akzeptiert; tatsächliche Null-/Maximalhöhe, Sättigung und Clipping bleiben offen. |
| I-11 | `color_height_reference.png` + `height_steps_16bit.png` | Die 16-Bit-Treppenkarte wurde ohne Warnung akzeptiert; acht diskrete Plateaus waren in der 3D-Vorschau erkennbar. | Importbeobachtung: Stufentrennung im Editor belegt; Digitalwert→mm-Kennlinie und Reproduzierbarkeit bleiben Druckmessung. |
| I-12 | `color_height_reference.png` + `height_wedge_16bit_aspect.png` | Studio zeigte exakt `Depth image ratio does not match the original image`. Die 256×128-HEIGHT-Datei wurde für das 256×256-COLOR-Objekt nicht übernommen; die vorherige Treppen-HEIGHT-Zuweisung und Objektgeometrie blieben unverändert. | Importbeobachtung: abweichende Seitenrelation wird fail-closed abgelehnt; keine stille Skalierung. |
| I-13 | `color_alpha_coverage.png` + `height_mean_16bit.png` (konstant 32768) | Das COLOR-Fixture wurde importiert und die 16-Bit-HEIGHT-Datei anschließend im selben Objekt nativ über `Customize Texture` zugewiesen. Studio akzeptierte die Kopplung ohne Warnung, kennzeichnete das Objekt mit `3D` und zeigte eine gleichmäßig hohe Vorschau, in der die drei Alpha-/Farbfelder weiter erkennbar blieben. | Importbeobachtung: Alpha×konstantes nicht-null HEIGHT ist im nativen COLOR/HEIGHT-Pfad vorgeprüft. Unterbase, Deckung und physische Reliefhöhe bleiben ohne Druck offen. |
| I-14 | `height_impulse_edge_16bit.png` + `height_impulse_edge_direct_half_16bit.png` | Die endgültigen, auf 1/4…3/4 begrenzten 16-Bit-Fixtures wurden nativ über `Customize Texture` ohne Warnung akzeptiert. Beim Ersetzen blieb das COLOR-Objekt bei W/H 90,31/90,31 mm und X/Y 122,34/164,84 mm; Kante, Impuls und Kalibrierfläche blieben in der 3D-Vorschau erkennbar. | Importbeobachtung: direkte, nicht vorgefilterte 256-/128-px-Kontrolle für Filterung und Normalisierung ist ausführbar. Physische Differenzen erfassen mangels Studio-Ausgaberaster den kombinierten Studio-/Druckpfad, nicht Studio allein. |
| I-08 | `color_height_reference.png` + `height_registration_16bit.png` | Am 2026-09-03 wurde COLOR importiert und über `Customize Texture` → `Upload Height Map Image` die 16-Bit-HEIGHT-Datei nativ zugewiesen. Studio akzeptierte sie ohne Warnung, kennzeichnete das Objekt mit `3D` und zeigte die asymmetrischen Landmarken in der 3D-Vorschau. Ein anschließend bestätigter Crop reduzierte W von 90,31 auf 44,86 mm und verschob X von 122,34 auf 167,79 mm; H 90,31 mm und Y 164,84 mm blieben erhalten. Die `3D`-Zuordnung und die passend beschnittene 3D-Vorschau blieben bestehen. Die separat importierte `gloss_registration.png` blieb dagegen unverändert bei 90,31×90,31 mm und X/Y 122,34/164,84 mm. | Importbeobachtung: nativer 16-Bit-HEIGHT-Träger und Crop-Kopplung innerhalb des COLOR/HEIGHT-Objekts belegt. Keine Aussage zur Nutzung aller 65.536 Werte, mm-Höhe oder physischen Registrierung; ein separater Gloss-Layer folgt dem Crop nicht automatisch. Weder `Preview` noch `Print` wurde ausgelöst. |

I-12 ist damit ein abgeschlossener **Import-Negativtest**: Weil Studio die
HEIGHT-Datei nicht übernimmt, existiert kein I-12-Objekt für Vorschau oder
Druck. Die Zelle hat deshalb keine physische Messzeile; für den abgelehnten
2:1-Seitenverhältnis-Fall ist eine Druckmessung nicht anwendbar. Die
akzeptierten I-02- und I-04-Objekte bleiben bei identischer Layoutgröße,
Texturhöhe und Druckeinstellung als separater kombinierter Pixelgrößen-/
Resampling-End-to-End-Vergleich erhalten. I-04 wurde jedoch bereits im
Fixture-Generator über float32, LANCZOS, `rint` und Clamp verkleinert. Der
Druckvergleich darf deshalb weder als isolierte Studio-Filtermessung noch als
physische Evidenz für I-12 gewertet werden. Die isolierte Studio-Filterung
war bislang offen. I-14 schließt nun die Fixture-Lücke: Beide Varianten sind
direkt aus identischer normierter Geometrie erzeugt, sodass keine
Generator-Vorfilterung in den Vergleich eingeht. Offen bleibt nur die physische
Messung; ohne zugängliches Studio-Ausgaberaster darf ihr Ergebnis nicht als
isolierte Studio-Filterung bezeichnet werden.

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

### 4.0 Messmittel, Auflösung und Auswertungsregel (vor Phase 3 festlegen)

Alle Messmittel-Felder dieser Akte bleiben leer, bis sie in
[`EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`](EUFYMAKE-687-PROTOKOLL-VORLAGEN.md)
§3.0 eingetragen sind. Die Tabelle setzt die Sollgrößen der Druckvarianten
(Layout 90,31 mm Kantenlänge, Texturhöhe 2,50 mm) in die Mindestauflösung
um, die ein Messmittel haben muss, damit die Zelle überhaupt ein Ergebnis
liefern kann. Maßgeblich ist die **Messunsicherheit** einschließlich
Wiederholpräzision, nicht die Anzeigeauflösung des Geräts. Laterale und
vertikale Sollgrößen skalieren unabhängig voneinander:

- **Lateral** mit der Layoutkantenlänge `L` (Vorgabe 90,31 mm): Pixel
  `L / 256` bzw. `L / 128`, Impulsbreite `L / 64`, Objektbreite nach Crop
  `L × 44,86 / 90,31`. Die Texturhöhe ändert diese Werte nicht.
- **Vertikal** mit der Texturhöhe `H` (Vorgabe 2,50 mm): 8-Bit-Stufe
  `H / 255`, Kalibrierstufe `H / 2 / 4096`, I-11-Stufe `H / 7`, lineare
  Vorhersage für Basis und Plateau `H / 4` und `3 H / 4`. Die Layoutgröße
  ändert diese Werte nicht.
- I-05 (101,60 mm) folgt allein aus dem `pHYs` der Datei, nicht aus dem
  Layout.

| Messgröße | Zellen | Sollgröße | Mindestanforderung (Messunsicherheit inkl. Wiederholpräzision) | Geeignete Mittel |
| --- | --- | --- | --- | --- |
| Reliefhöhe absolut (Stufe, Plateau, Basis) | I-11, I-07, I-02/I-04, I-13 | I-11-Stufe 0,357 mm; Basis/Plateau I-14 0,625/1,875 mm | ≤ 0,05 mm | Messschieber mit Tiefenmaß, Messuhr mit Messstativ |
| Höhenprofil quer zur Kante (Kantenbreite 10–90 %, FWHM) | I-14, I-03 | Pixel 0,353 mm (256 px) bzw. 0,706 mm (128 px); Impulsbreite 1,41 mm | lateral ≤ 0,1 mm, vertikal ≤ 0,05 mm | Messuhr auf Schlitten oder Kreuztisch; Schnitt quer zur Kante plus Makrofoto mit Maßstab; 3D-Scan |
| 8-Bit-Höhenstufe | I-03 | 0,0098 mm | ≤ 0,002 mm | mit Handmessmitteln nicht auflösbar; Profilometer oder vergleichbar |
| 16-Bit-Kalibrierstufe (1,25 mm / 4096) | I-03, I-14 | 0,0003 mm | – | physisch nicht auflösbar |
| Länge und Breite (mm/DPI) | I-05, I-08 | 101,60 mm bzw. 90,31/44,86 mm | ≤ 0,1 mm | Messschieber mit Messbereich ≥ 150 mm |

**Auswertungsregel I-03 (8 gegen 16 Bit), vorab festgelegt:**

1. Zeigt die untere Kalibrierfläche mit dem eingetragenen Messmittel in der
   16-Bit-Variante mehr unterscheidbare Höhenstufen als in der 8-Bit-Variante
   und übersteigt der Unterschied die in §3.0 eingetragene Messunsicherheit,
   gilt „16-Bit-Nutzung im Druckpfad belegt" (Druckmessung).
2. Ist keine Differenz messbar und liegt die eingetragene Messunsicherheit
   einschließlich Wiederholpräzision bei ≤ 0,002 mm, also deutlich unter der
   8-Bit-Stufe von 0,0098 mm, gilt „Studio-/Druckpfad quantisiert auf
   8-Bit-Niveau oder gröber" (Druckmessung). Eine Anzeigeauflösung von
   0,002 mm genügt dafür nicht.
3. Ist keine Differenz messbar und ist die Messunsicherheit größer, lautet
   das Ergebnis „nicht entscheidbar": H-01 bleibt offen, Profil v1 bleibt
   vorläufig, und es wird kein Wiederholungslauf für I-03 angesetzt.
4. Unabhängig davon wird aus I-03 und I-11 die kleinste physisch
   unterscheidbare Höhenstufe (Stufenkanten, sichtbare Schichtdicke) als
   „praktisch nutzbare Tonwertauflösung" protokolliert; sie erfüllt das
   #688-Kriterium zur Tonwertauflösung auch dann, wenn H-01 unentschieden
   bleibt.

**Auswertungsregel I-14, vorab festgelegt:** Filterung gilt als belegt, wenn
die Kantenbreite 10–90 % der 128-px-Variante die der 256-px-Variante um mehr
als die Messunsicherheit übersteigt. Für Normalisierung gilt: `H / 4` und
`3 H / 4` sind nur die lineare Vorhersage; die tatsächliche
Digitalwert→mm-Kennlinie ist unbekannt und kann bildunabhängig nichtlinear
sein. Sollhöhen für Basis und Plateau sind deshalb die aus der
I-11-Stufenkennlinie (Vollbereichs-Fixture 0…65535, ergänzt um die
I-07-Null- und Maximalhöhe) für die Digitalwerte 16384 und 49152
interpolierten Höhen. Normalisierung gilt als belegt, wenn Basis und Plateau
von diesen Sollhöhen um mehr als die Messunsicherheit in Richtung der
gemessenen Null- bzw. Maximalhöhe abweichen; stimmen sie mit der
I-11-Kennlinie überein, liegt keine Normalisierung vor, auch wenn die
Kennlinie nichtlinear ist. Voraussetzung ist, dass I-11 und I-07 mit
demselben Reihenparametersatz (Protokoll §3.0) gedruckt und gemessen wurden.
Ohne ein in Protokoll §3.0 eingetragenes Profilmessmittel wird I-14 nicht
gedruckt.

### 4.1 Kontrollierte Filtermessung I-14

Die I-03-16-Bit-Variante `height_impulse_edge_16bit.png` ist zugleich die
256×256-Referenz; I-14 fügt nur die direkte 128×128-Variante als eigenen
Druck hinzu. Layoutgröße/-position, `Customize Texture`, `Color Raised`,
2,50 mm, Material und Qualitätsprofil bleiben identisch. Das obere
Dreiviertel enthält die begrenzte Kante/den Impuls; das untere Viertel die
4096-stufige 16-Bit-Kalibrierfläche.

| Variante | Studio-Vorschau | Kantenbreite 10–90 % bei y=1/2 (mm) | Impulsbreite FWHM bei y=1/2 (mm) | Peak (mm) | Plateau (mm) | Basis (mm) | sicht-/messbare Kalibrierstufen | Unsicherheit/Einordnung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 256×256, I-03-16-Bit/I-14-Referenz | | | | | | | | |
| 128×128, I-14 direkt | | | | | | | | |

Die Vorschau ist eine eigene Beobachtung und kein Ersatz für die Messwerte.
Basis und Plateau entsprechen im Fixture 1/4 bzw. 3/4 des Digitalbereichs;
ihre Sollhöhen kommen aus der I-11-Kennlinie nach §4.0, und erst eine
Verschiebung auf die gemessene Null- bzw. Maximalhöhe ist als automatische
Normalisierung zu werten. Eine Differenz zwischen den beiden Druckzeilen ist dem kombinierten
Studio-/Druckpfad zuzuordnen. Das Ergebnis darf weder als Studio-only-Filter
noch als Evidenz zum abgelehnten I-12-Seitenverhältnisfall ausgegeben werden.

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
| Filterung/Glättung (kombinierter Studio-/Druckpfad) | | | |
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
