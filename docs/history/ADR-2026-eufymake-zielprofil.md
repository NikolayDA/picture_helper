# ADR: Ein versioniertes Zielprofil für den EufyMake-Export

**Status:** angenommen, Profil v1 vorläufig · **Datum:** 2026-09-02 ·
**Bezug:** #681, #687–#691

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
