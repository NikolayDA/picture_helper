# ADR: Ein versioniertes Zielprofil für den EufyMake-Export

**Status:** angenommen, Profile v1 und v2 vorläufig · **Datum:** 2026-09-02,
Nachtrag 2026-09-07 · **Bezug:** #681, #687–#691

## Kontext

Planer, Validator, Writer und Dialog hielten Profilkennung, Dateinamen,
Bittiefen und Warnungsannahmen teilweise getrennt. Neue Erkenntnisse aus
Studio- und Hardwaretests hätten dadurch an mehreren Stellen synchron geändert
werden müssen. Zugleich dürfen Studio-Akzeptanz und Herstellerhypothesen nicht
als physisch bestätigter Druckvertrag erscheinen.

## Entscheidung

1. `EufyMakeTargetProfile` ist der einzige unveränderliche Vertrag für Rollen,
   Kanäle, Defaults, Maße, Validierungsregeln, Zielumgebung und Evidenzstatus.
2. Ein Registry-Schlüssel besteht aus Profil-ID und Profilversion. Das
   Profilschema wird davon separat versioniert.
3. Dialog, Validator, Planer und Writer reichen dasselbe Profilobjekt weiter.
   Produktcode verzweigt nicht nach Profilnamen.
4. Das Manifest enthält zusätzlich zur Legacy-Referenz einen vollständigen
   Snapshot und die separat bestimmte BgRemover-Version.
5. `confirmed`, `observed`, `provisional` und `open` bleiben unterschiedliche
   Evidenzklassen. Profil v1 ist bis zu den physischen #688–#690-Nachweisen
   `provisional`; 16-Bit-HEIGHT und Gloss bleiben warnpflichtig.
6. Ein Golden-Test macht jede semantische v1-Änderung reviewpflichtig. Neue
   Bedeutung oder Zielumgebung verlangt eine neue Version statt stillen Drifts.

## Alternativen

- **Konstanten in jedem Modul behalten:** verworfen wegen Driftgefahr.
- **Nur eine Manifestversion einführen:** verworfen, weil sie weder UI noch
  Validator/Writersicht vereinheitlicht.
- **Offene Hardwarewerte schon als v1-Defaults bestätigen:** verworfen, weil
  Studio-Import keinen physischen Druckbefund liefert.
- **Vor #688–#690 gar kein Profil veröffentlichen:** verworfen, weil ein
  ausdrücklich vorläufiger, konservativer Vertrag bereits Drift verhindert und
  Unsicherheiten maschinenlesbar macht.

## Folgen

Der Export ist nachvollziehbarer und für weitere Profile erweiterbar. Manifeste
werden größer, bleiben durch ihre Legacy-Felder aber kompatibel. HEIGHT-Exporte
benötigen vorerst auch bei 16 Bit eine Warnungsbestätigung. Die Profilfreigabe
bleibt fachlich blockiert, bis die genehmigten physischen Tests dokumentiert
sind; diese ADR autorisiert keinen Druck.

## Nachtrag 2026-09-07: additives Profil v2

Profil v1 bleibt unverändert als historische Studio-4.2.2-Referenz registriert.
Zusätzlich wird `bgremover-eufymake-import@2` zum Defaultprofil. Es übernimmt
den v1-Rollen- und Kanalvertrag, setzt die beobachtete Zielumgebung auf Studio
4.3.3 und Firmware 4.0.9 und ergänzt die Warnung `physical_size_missing` mit
der Abhilfe `set_project_physical_size`.

Für v2 ist `Unidirectional` die am 2026-09-07 verwendete Vorschau-Baseline;
`Bidirectional` bleibt ungetestet. Der
[zugehörige Preflight](EUFYMAKE-681-PREFLIGHT-2026-09-07.md) dokumentiert für
G-05 eine **mehrdeutige X-Feld-Semantik**: Im gespeicherten Canvas haben COLOR
und Gloss dieselbe linke Position X = 122,345 mm. Das Eigenschaftenfeld der
45,16 mm breiten Glossmaske zeigt X = 167,50 mm und damit die sichtbare rechte
Kante; Canvas, Auswahlbox und Vorschau stellen die Maske linksbündig dar. Ein
tatsächlicher Runtime- oder Preview-Versatz ist nicht belegt. Das Projekt wurde
nicht in den kanonischen Projektsatz zurückgespeichert. Der getrennte
G-05-Rohimport entspricht der historischen Studio-4.2.2-Baseline. Die
druckfreie Regression ist mit 29/29 Rohimportzellen vollständig; funktional
entsprechen alle Zellen der Baseline. Bei I-06 ist `manifest.json` in 4.3.3
auswählbar und wird erst danach mit `Unsupported file type.` abgewiesen,
bleibt also wie zuvor fail-closed. Die Gloss-Registrierungsabnahme unter v2
und die physischen Hardwaretests aus #688–#690 bleiben offen; dieser Lauf
löste keinen Druck aus.
