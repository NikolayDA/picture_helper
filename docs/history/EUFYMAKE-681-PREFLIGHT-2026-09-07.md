# Preflight-Evidenz Epic #681 – 2026-09-07

**Status: Software-, Firmware- und lokaler Testdatenstand geprüft;
29/29 verpflichtende Rohimportzellen erneut ausgeführt, G-05-X-Feld-Semantik
im nativen Projekt mehrdeutig, kein Druck; physische E1-Druck- und
Messkriterien offen.**

Diese Evidenz ergänzt die
[`EUFYMAKE-681-VORBEREITUNG-2026-09-05.md`](EUFYMAKE-681-VORBEREITUNG-2026-09-05.md)
nach der Aktualisierung von eufyMake Studio und dem vom Benutzer gestarteten
Firmware-Update. Sie hält nur die am 2026-09-07 beobachteten oder lokal
reproduzierten Ergebnisse fest. Es wurde kein Druck ausgelöst; das physische
Budget bleibt bei **0/35**.

## Beobachteter Software- und Firmwarezustand

| Gegenstand | Beobachtung | Aussagegrenze |
| --- | --- | --- |
| eufyMake Studio | **4.3.3**; Software Update meldet den Stand als aktuell | lokal angezeigter Desktop-App-Stand |
| eufyMake Editor | **1.20.0** | im geöffneten Projekt angezeigt |
| Firmware-Update-Workflow | Abschlussmeldung **`Updated successfully`** | belegt den erfolgreichen Abschluss des angezeigten Workflows |
| Direkte Geräteanzeige vor Neustart | zunächst weiterhin **V4.0.2** | war ein veralteter Vor-Neustart-Stand und wird durch die anschließende direkte Anzeige ersetzt |
| Direkte Geräteanzeige nach vollständigem Neustart | **Firmware V4.0.9** | aktueller, unmittelbar in Printer Settings → About Device abgelesener Firmwarestand |
| Erneute Updateprüfung nach Neustart | **`The firmware is already up to date.`** | bestätigt V4.0.9 als aktuellen Endstand ohne weiteres Updateangebot |
| Lokale Studio-Konfiguration | `UVCommonConfig` enthält `skipVersion` **4.0.9** | zusätzlicher lokaler Bezug auf 4.0.9; die tragende Evidenz ist die direkte Geräteanzeige nach Neustart |
| Druckoptionen | die neue Auswahl **Print Direction** ist sichtbar; die unten protokollierten Vorschauen liefen mit **Unidirectional** | belegt die gewählte Richtung dieser Vorschauen, aber keine Richtungskalibrierung |
| Sichtbare Gerätesperren | Y-Tinte abgelaufen; `Scraper` und `Air Filter` abgelaufen | vor einem physischen Lauf zu beheben oder gemäß Testgovernance zu klären |
| Verfügbares Substrat | schwarzer Karton, 0,1 mm; Charge nicht protokolliert | nur Bestandsangabe; in diesem Lauf nicht bedruckt |

Damit ist **Firmware V4.0.9 direkt und widerspruchsfrei bestätigt**. Die vor
dem Neustart noch sichtbare V4.0.2-Anzeige war ein veralteter UI-Stand und ist
kein aktueller Gegenbefund mehr.

## Reproduzierte lokale Vorprüfungen

Der unabhängige Fixture-Inspector lief gegen Manifest-Schema 5 und den
versionierten Manifest-SHA-256
`7c0b788cb614068c5e1d2a9ea4453929b2278d0e60fd8206d0c5ff5ed213627a`.

| Prüfung | Ergebnis |
| --- | --- |
| Einzel-Fixtures | **42/42 gültig** |
| Exportpakete | **7/7 gültig** |
| Native `.empf`-Projektbindungen, Träger, Vorschauen und Aufbau-Dateien | **13/13 gültig** |

Die Prüfungen belegen unveränderte Eingabebytes, Paketsemantik und die interne
Struktur der vorbereiteten Projekte. Sie belegen kein Verhalten von Studio
4.3.3 beim erneuten Import und keine physische Druckausgabe.

## Abgeschlossene Rohimportmatrix

Alle **29/29 verpflichtenden druckfreien Zellen** wurden unter Studio 4.3.3,
Editor 1.20.0 und der nach dem Neustart direkt bestätigten Firmware V4.0.9
erneut ausgeführt. Die folgende Matrix zählt die beiden nicht anwendbaren
I-09-Explorationszeilen weiterhin nicht mit. `Print` wurde nie ausgelöst.

| Nr. | Zelle | Beobachtung unter 4.3.3 | Vergleich mit 4.2.2 |
| ---: | --- | --- | --- |
| 1 | I-01 | konsistentes `pHYs`; Startgröße 101,60×101,60 mm | funktional gleich |
| 2 | I-02 | HEIGHT akzeptiert; `Color Raised`, 2,50 mm | funktional gleich |
| 3 | I-03 (8 Bit) | 8-Bit-HEIGHT akzeptiert | funktional gleich |
| 4 | I-03 (16 Bit) | 16-Bit-HEIGHT akzeptiert | funktional gleich |
| 5 | I-04 | HEIGHT mit halber Pixelkante bei gleicher Seitenrelation akzeptiert | funktional gleich |
| 6 | I-05 (konsistentes `pHYs`) | 101,60×101,60 mm | funktional gleich |
| 7 | I-05 (ohne `pHYs`) | Größenwarnung; „Originalgröße behalten“ ergibt 423,33×423,33 mm bei X/Y −44,17/−1,67 mm | funktional gleich |
| 8 | I-05 (Konflikt-`pHYs`) | 203,18×203,18 mm | funktional gleich |
| 9 | I-05 (X/Y-`pHYs`) | 101,60×203,18 mm | funktional gleich |
| 10 | I-06 (`manifest.json`) | Datei ist auswählbar; nach dem Öffnen erscheint der Toast **`Unsupported file type.`** und es wird kein Objekt importiert | Interaktion geändert: 4.2.2 zeigte die Datei ausgegraut; beide Versionen schließen den Import sicher aus |
| 11 | I-06 (Exportordner) | PNGs werden als getrennte `Flat`-Objekte importiert; Manifest erzeugt kein Objekt und keine Rolle | funktional gleich |
| 12 | I-07 | Null- und Maximal-HEIGHT akzeptiert | funktional gleich |
| 13 | I-08 (vor Crop) | COLOR, HEIGHT und Gloss zunächst je 90,31×90,31 mm bei X/Y 122,34/164,84 mm | funktional gleich |
| 14 | I-08 (nach Crop) | gekoppeltes COLOR/HEIGHT-Objekt 44,86×90,31 mm bei X/Y 167,80/164,84 mm; separate Gloss-Ebene unverändert 90,31×90,31 mm bei X/Y 122,34/164,84 mm | funktional gleich; aktuelle X-Anzeige auf zwei Dezimalstellen protokolliert |
| 15 | I-10 (normal) | mit `gloss_wedge.png` aus G-02 geprüft; sichtbares, separates `Flat`-Objekt | funktional gleich |
| 16 | I-10 (invertiert) | mit `gloss_wedge_inverted.png` aus G-02 geprüft; sichtbares, separates `Flat`-Objekt | funktional gleich |
| 17 | I-11 | HEIGHT-Treppenstufen akzeptiert | funktional gleich |
| 18 | I-12 | HEIGHT 256×128 für COLOR 256×256 weiterhin abgelehnt: **`Depth image ratio does not match the original image`** | funktional gleich; fail-closed |
| 19 | I-13 | COLOR mit Alpha 0/128/255 und konstantes Mean-HEIGHT akzeptiert | funktional gleich |
| 20 | I-14 (256×256) | Kanten-/Impuls-HEIGHT akzeptiert | funktional gleich |
| 21 | I-14 (128×128) | direkte Kanten-/Impuls-Kontrolle akzeptiert | funktional gleich |
| 22 | G-01 | importierte Gloss-Grauwerte sichtbar, getrennt und `Flat`; keine automatische Rolle oder Kopplung | funktional gleich |
| 23 | G-02 | normaler und invertierter Keil sichtbar, getrennt und `Flat`; keine automatische Rolle oder Kopplung | funktional gleich |
| 24 | G-03 | Stufen und begrenzter Keil sichtbar, getrennt und `Flat`; keine automatische Rolle oder Kopplung | funktional gleich |
| 25 | G-04a/b/c | fehlendes Gloss bleibt fehlend; vorhandene Null-/Voll-Assets sichtbar, getrennt und `Flat`; keine automatische Rolle oder Kopplung | funktional gleich |
| 26 | G-05 | COLOR 90,31×90,31 mm bei X/Y 122,34/164,84 mm; separate Glossmaske 45,16×90,31 mm bei X/Y 144,91/164,84 mm; beide 0°, sichtbar und `Flat`, COLOR mit `White > CMYK`; keine Warnung, keine Skalierung, kein Beschnitt und keine Verknüpfung | funktional gleich |
| 27 | G-06 | COLOR/Alpha, HEIGHT und Gloss sichtbar, getrennt und `Flat`; keine automatische Rolle oder Kopplung | funktional gleich |
| 28 | G-07 | COLOR, HEIGHT und Gloss sichtbar, getrennt und `Flat`; keine automatische Rolle oder Kopplung | funktional gleich |
| 29 | G-08 | Registrierungs- und Checkerboard-Assets sichtbar, getrennt und `Flat`; keine automatische Rolle oder Kopplung | funktional gleich |

Damit entsprechen alle 29 Zellen funktional der historischen
Studio-4.2.2-Baseline. Die einzige beobachtete Versionsabweichung betrifft die
Bedienfolge für I-06: `manifest.json` ist nun auswählbar und wird erst nach dem
Öffnen mit `Unsupported file type.` abgewiesen. Das bleibt fail-closed und
macht das Manifest weiterhin nicht zu einem importierbaren Studio-Asset.

Der bestandene G-05-Rohimport ist vom nativen Projekt 10 getrennt. Dessen
mehrdeutige X-Feld-Semantik ändert das Rohimportergebnis nicht.

## Vorschau-Evidenz ohne Druck

Die folgenden nativen Projekte wurden mit Studio 4.3.3, Editor 1.20.0 und
Firmware V4.0.9 bis zur Druckvorschau geöffnet. Gemeinsame Einstellungen:
Material `Unknown`, Qualität `Standard`, White Underbase Choke 0,2 mm und
Print Direction `Unidirectional`. **Print** wurde nicht ausgelöst.

| Projekt / Zelle | Sichtbarer Befund und Warnungen | Estimate Ink & Time | Kanalschätzung | Vergleichsgrenze |
| --- | --- | --- | --- | --- |
| 01 / I-02 und I-04 | Vorschau ohne Warnung | **1 h 30 min 59 s; ca. 20,61 ml** | W 10,65 ml; G 9,92 ml; C/M/Y/K je <0,01 ml | Schätzung, keine physische HEIGHT-, Größen- oder Resampling-Aussage |
| 02 / I-03 und I-14 | Vorschau ohne Warnung | **2 h 22 min 19 s; ca. 41,6 ml** | C/Y je <0,01 ml; M/K je 0,01 ml; W 21,51 ml; G 20,05 ml | Schätzung, keine physische Aussage zu Bittiefe, Filterung oder Höhenprofil |
| 03 / I-07, I-11 und I-13 | Vorschau ohne Warnung; Schätzung schlug auch nach `Retry` erneut mit `Estimation failed` fehl | **nicht verfügbar** | nicht verfügbar | reproduzierter Schätzfehler; Preview-Inhalt und physische HEIGHT-/Alpha-Wirkung bleiben getrennt zu prüfen |
| 04 / I-08 vor und nach Crop | 3D-Vorschau beider HEIGHT-Objekte und zwei Gloss-Ebenen sichtbar; keine Warnung | **1 h 40 min 43 s; ca. 1,84 ml** | W 0,9 ml; G 0,9 ml; C/M/Y/K je <0,01 ml | entspricht der Schätzung unter Studio 4.2.2; keine physische Registrierungsaussage |
| 06 / I-05 konsistent | Vorschau ohne Warnung | **10 min 19 s; ca. 0,53 ml** | W 0,49 ml; G 0 ml; C/M/Y/K je <0,01 ml | Schätzung, kein Nachweis des tatsächlichen Verbrauchs oder Druckmaßes |
| 07 / G-01 und G-03 | Vorschau ohne Warnung | **21 min 5 s; ca. 0,75 ml** | W 0,08 ml; G 0,63 ml; C/M/Y/K je <0,01 ml | Schätzung, keine Aussage zu physischer Gloss-Intensität oder Kennlinie |
| 08 / G-02 normal und invertiert | Vorschau ohne Warnung | **12 min 0 s; ca. 0,33 ml** | W 0,04 ml; G 0,25 ml; C/M/Y/K je <0,01 ml | Schätzung, keine physische Polaritätsaussage |
| 09 / G-04a/b/c | Vorschau ohne Warnung | **24 min 25 s; ca. 1,6 ml** | C 0,07 ml; M 0,08 ml; Y 0,02 ml; K <0,01 ml; W 1,17 ml; G 0,25 ml | Schätzung, keine physische Aussage zu fehlendem, Null- oder Voll-Gloss |
| 10 / G-05, natives `.empf`-Projekt | **Mehrdeutige X-Feld-Semantik:** Im gespeicherten Canvas haben COLOR und Gloss dieselbe linke Position X = 122,345 mm. Bei ausgewählter Glossmaske zeigt das Eigenschaftenfeld X = 167,50 mm bei W = 45,16 mm; dieser X-Wert entspricht der sichtbaren rechten Kante. Canvas, grüne Auswahlbox und Vorschau stellen Gloss linksbündig auf der linken COLOR-Hälfte dar (ca. 122,34…167,50 mm). Damit ist kein tatsächlicher Runtime- oder Preview-Versatz belegt. COLOR: W/H 90,31/90,31 mm, X/Y 122,34/164,84 mm, Rotation 0°, `Flat`, `White > CMYK`. Glossmaske: W/H 45,16/90,31 mm, Y 164,84 mm, Rotation 0°, `Flat`, `Gloss Varnish × 1`. Getrennte Objekte; Vorschau erfolgreich und ohne Warnung. Projekt wurde nicht gespeichert. | **13 min 7 s; ca. 0,53 ml** | C 0,02 ml; M 0,03 ml; Y/K je <0,01 ml; W 0,4 ml; G 0,06 ml | nativer Projektpfad, getrennt vom erfolgreichen G-05-Rohimport; Semantik des Gloss-X-Felds ungeklärt, physische Dimensions-, Registrierungs- und Glosswirkung offen |
| 11 / G-06 | Vorschau ohne Warnung | **1 h 11 min 38 s; ca. 20,09 ml** | C/M je 0,02 ml; Y/K je <0,01 ml; W 10,27 ml; G 9,76 ml | Schätzung, keine physische Alpha×Gloss-Aussage |
| 12 / G-07 | Vorschau ohne Warnung | **1 h 4 min 13 s; ca. 11,25 ml** | C/M je 0,02 ml; Y/K je <0,01 ml; W 5,78 ml; G 5,41 ml | Schätzung, keine physische HEIGHT×Gloss-Aussage |
| 13 / G-08 | Vorschau ohne Warnung | **17 min 2 s; ca. 0,7 ml** | W 0,41 ml; G 0,25 ml; C/M/Y/K je <0,01 ml | Schätzung, keine physische Registrierungs-, Filter- oder Bleeding-Aussage |

Für die Projekte **01, 02, 03, 04, 11 und 12** wurden Preview-Zustände
ausschließlich in temporären Kopien gespeichert; der kanonische Projektsatz
bleibt unverändert. Projekt 10 / G-05 darf wegen der mehrdeutigen
X-Feld-Semantik nicht in den kanonischen Projektsatz zurückgespeichert werden.

Damit wurden alle zwölf aktiven nativen Projekte 01–04 und 06–13 unter dem
oben genannten Versions- und Parametersatz bis zur Vorschau geöffnet.
Projekt 05 / I-10 wurde gemäß Option A nicht previewt und bleibt für den
physischen Ablauf nicht anwendbar.

## Abgeschlossene Regression und offene Druckgrenze

- Die **29/29 verpflichtenden druckfreien Importzellen** aus
  [`EUFYMAKE-687-DRUCK-CHECKLISTE.md`](EUFYMAKE-687-DRUCK-CHECKLISTE.md)
  sind unter Studio 4.3.3 abgeschlossen. Es gibt **0 offene Rohimportzellen**.
  I-06 bleibt trotz geänderter Bedienfolge fail-closed.
- Beim vom abgeschlossenen G-05-Rohimport getrennten nativen Projektpfad 10
  bleibt die **X-Feld-Semantik mehrdeutig**:
  Das Eigenschaftenfeld nennt für die 45,16 mm breite Glossmaske X = 167,50 mm
  und damit die sichtbare rechte Kante. Gespeichertes Canvas, Auswahlbox und
  Vorschau zeigen die Maske linksbündig ab ca. X = 122,34 mm. Die Bedeutung des
  X-Felds ist nicht geklärt; ein tatsächlicher Runtime- oder Preview-Versatz ist
  nicht belegt. Die physische Registrierung muss getrennt geprüft werden.
  Dieser Befund ändert den bestandenen G-05-Rohimport nicht und ersetzt keine
  physische Messung von Dimension, Registrierung oder Glossauftrag.
- **Print Direction** und ein zugehöriger Kalibrierstatus sind vor jeder
  Vorschau- oder Druckreihe festzulegen und über die Vergleichsreihe konstant
  zu halten.
- Es liegen weiterhin **keine physischen Drucke oder Messwerte** aus diesem
  Preflight vor. HEIGHT-, mm/DPI-, Gloss- und Registrierungsbefunde bleiben
  deshalb auf die vorhandene Datei- und historische Studio-Evidenz begrenzt.
- Die sichtbaren Sperren wegen abgelaufener Y-Tinte, abgelaufenem `Scraper`
  und abgelaufenem `Air Filter` sind vor einem Drucklauf zu beheben oder gemäß
  Testgovernance zu klären. Der vorhandene schwarze Karton mit 0,1 mm Dicke
  wurde in diesem Lauf nicht bedruckt.
