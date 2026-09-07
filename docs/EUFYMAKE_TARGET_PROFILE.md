# Versioniertes EufyMake-Zielprofil

Stand: 2026-09-07 · Profil `bgremover-eufymake-import@1` und `@2` · Schema 1

## Zweck und Status

BgRemover verwendet für Planung, Prüfung, Dialog, Writer und Manifest dasselbe
unveränderliche, versionierte Zielprofil aus `bgremover/eufymake_profile.py`.
Das Profil ist eine **BgRemover-Konvention für manuell importierbare Dateien**,
keine offizielle EufyMake-Spezifikation und kein `.empf`-Containervertrag.

Profil v1 bleibt die unveränderte historische Referenz für Studio 4.2.2. Das
additive Profil v2 ist das aktuelle Defaultprofil für Studio 4.3.3 und Firmware
4.0.9. Beide Profile sind **vorläufig**. Die physischen Druckmessungen aus
#688–#690 fehlen; zusätzlich bleibt die unter 4.3.3 beobachtete
G-05-X-Feld-Semantik mehrdeutig. Deshalb werden
16-Bit-Nutzung, Grauwert→mm-Abbildung, Druckmaß/Registrierung sowie
Gloss-Polarität und -Intensität nicht als bestätigt ausgegeben.

## Referenz und Zielumgebung

| Feld | Wert | Status |
| --- | --- | --- |
| Profilschema | 1 | interner Maschinenvertrag |
| Profil-ID | `bgremover-eufymake-import` | stabil |
| Profil v1 | `1`; Studio 4.2.2; Firmware nicht protokolliert | historische, vorläufige Referenz |
| Profil v2 | `2`; Studio 4.3.3; Firmware 4.0.9 | aktuelles Defaultprofil, vorläufig |
| Gerät | eufyMake E1 | Zielgrenze |
| Print Direction v2 | `Unidirectional` | beobachtete Vorschau-Baseline; `Bidirectional` ungetestet |
| BgRemover-Version | zur Laufzeit im Manifest | ausdrücklich getrennt vom Zielprofil |

Eine neue Semantik oder Zielumgebung verändert nicht rückwirkend v1. Sie erhält
eine neue Profilversion beziehungsweise eine neue Profil-ID und wird im
`ProfileRegistry` registriert. Unbekannte IDs und nicht unterstützte Versionen
werden getrennt und verständlich abgewiesen.

Die Registry akzeptiert nur intern konsistente Verträge: Profilversionen sind
echte Integer (keine booleschen Ersatzwerte), COLOR und HEIGHT sind als von den
aktuellen Consumern benötigte Rollen vorhanden, Asset-Dateinamen sind
eindeutige Basenames außerhalb des reservierten `manifest.json` und jede
unterstützte Bittiefe besitzt genau einen Wertebereich. Jede Version enthält
den eingefrorenen v1-Basissatz stabiler Validator-Codes samt Abhilfe; spätere
Versionen dürfen daraus nur bekannte additive `ExportCheckCode`-Regeln
aktivieren. Profil v2 ergänzt so `physical_size_missing`, ohne den v1-Vertrag
zu verändern. Als `required` markierte Rollen werden unabhängig von einer
optionalen UI-Auswahl immer geprüft und exportiert.

## Rollen- und Kanalvertrag

| Rolle / Datei | Format | Tiefe / Default | Werte / Richtung | Alpha | Status |
| --- | --- | --- | --- | --- | --- |
| `color_motif` / `color_motif.png` | RGBA | 8 Bit / 8 Bit | 0…255 je Kanal | Straight Alpha bleibt erhalten | interner Writervertrag bestätigt |
| `height_map` / `height_map.png` | Graustufe | 8 oder 16 Bit / **16 Bit** | 0…65535; hell = hoch | keiner | Richtung belegt; Trägernutzung und mm-Abbildung vorläufig/offen |
| `gloss_mask` / `gloss_mask.png` | Graustufe | 8 Bit / 8 Bit | 0…255; Richtung offen | keiner | experimentell; native Studio-Zuweisung erforderlich |

16 Bit ist der konservative HEIGHT-Default, weil er vorhandene Niederbits nicht
vor dem Import verwirft. Das ist **keine** Behauptung, Studio oder E1 nutzten
diese Niederbits physisch. Darum bleibt `BIT_DEPTH_UNCONFIRMED` sowohl bei 8 als
auch bei 16 Bit warnpflichtig; bei tatsächlichem 16-Bit-Quellinhalt warnt 8 Bit
zusätzlich vor Präzisionsverlust.

Für Gloss gilt bis zum Realtest: Eine Datei wird nur bei expliziter GLOSS-Rolle
geschrieben. Sie ist ein Hilfsasset und wird im Studio nicht automatisch zur
Gloss-/Spot-UV-Rolle. Schwarz=Auftrag/Weiß=kein Auftrag bleibt eine
Herstellerhypothese für den dokumentierten Spot-UV-Workflow, nicht der bestätigte
Vertrag dieses Assets.

## Maße und DPI

- Alle gewählten Rollen müssen dieselben Pixelmaße besitzen; Abweichungen
  blockieren den Writer.
- Physische Maße stammen ausschließlich aus `physical_size_mm` des Projekts.
- Daraus berechnete X- und Y-DPI werden getrennt behandelt und im Dialog sowie
  Manifest getrennt angezeigt.
- Der Writer schreibt genau diese X-/Y-DPI als PNG-`pHYs` in **jedes** Asset
  (`eufymake_writer.png_dpi_for` = Manifest-`target.dpi`; das ist die
  `physical_size_source` des Profils). `pHYs` speichert ganzzahlige Pixel pro
  Meter je Achse, der Rückweg weicht deshalb um höchstens 0,02 dpi vom Sollwert
  ab. Pixeldaten und Manifest bleiben davon unberührt; nicht kodierbare
  Extremwerte (0 bzw. > 2^32 − 1 Pixel pro Meter, nur über handeditierte
  Projektmetadaten erreichbar) brechen mit `EufyMakeWriteError` ab.
- Ohne physische Projektgröße entsteht **kein** `pHYs` – keine erfundene
  Auflösung. Studio 4.2.2 und 4.3.3 starten dann beobachtet mit 72 dpi
  (1200 px → 423,33 mm samt Arbeitsflächenwarnung). Profil v1 enthält für
  diesen Fall keinen eigenen Befund; Profil v2 warnt mit
  `physical_size_missing` und der Abhilfe `set_project_physical_size`.
  Manuelle Studio-Maße können den aus `pHYs` übernommenen Startwert ersetzen
  (#689-Beobachtung).
- Priorität im vollständigen Rollenverbund, Rundung, Registrierung und
  tatsächliches Druckmaß bleiben bis #689 physisch offen.
- Das eufyMake-Standard-Flatbed (335 × 420 mm, `STANDARD_FLATBED_MM` in
  `bgremover/eufymake_export.py`) ist bewusst **nicht** Teil des Profils: Der
  Validator warnt mit `print_area_exceeded`/`fit_standard_flatbed`, wenn das
  Motiv es überschreitet. Das Maß ist seit 2026-09-03 vom Owner bestätigt und
  deckt sich mit der in Studio 4.2.2 angezeigten Arbeitsfläche (#689, #971);
  die frühere Lesart 330 × 420 mm aus der Suchmaschinen-Extraktion (Grad S) ist
  überholt. Die Aufnahme in eine Profilversion bleibt ein eigener Schritt.

## Validierung und Abhilfe

Jeder Befund enthält einen stabilen Code, Schweregrad, betroffene Rolle,
kanonischen Dateinamen und eine maschinenlesbare Abhilfe. Die Regel selbst liegt
im Profil. Fehler blockieren; Warnungen benötigen eine bewusste Bestätigung.
Beispiele sind `asset_size_mismatch` + `match_canvas_dimensions`,
`bit_depth_unconfirmed` + `confirm_height_carrier` und `gloss_ink_mode` +
`assign_native_gloss_in_studio`. Profil v2 ergänzt `physical_size_missing` +
`set_project_physical_size`; v1 bleibt unverändert.

## Manifest und Legacy-Zuordnung

Neue Manifeste behalten die bisherigen Felder – `profile`, `profile_version`,
`kind`, `note`, `height_semantics`, `open_questions`, `target` (Pixelmaße,
Bittiefe, physische mm und getrennte X-/Y-DPI) und `assets[]` – und ergänzen
seit #691:

- `profile_contract`: vollständiger Profilsnapshot mit Schema, Zielumgebung,
  Rollen-, Maß-, Validierungs- und Evidenzvertrag;
- `producer`: Anwendung und BgRemover-Version;
- `assets[].channel_interpretation`: Wertebereich, Richtung, Semantik,
  Alpha-Regel, Status und Evidenz-IDs.

`resolve_manifest_profile()` liest alte Manifeste mit nur `profile` und
`profile_version`, kennzeichnet sie aber als Legacy-Referenz. Fehlende
Snapshot-/Evidenzfelder werden nicht erfunden und das Manifest wird nicht
stillschweigend umgeschrieben. Das Manifest bleibt interne Provenienz; Studio
4.2.2 hat es im Bildimport nicht als Paketvertrag verwendet.

## Studio-4.3.3-Abnahmegrenze

Der [Preflight vom 2026-09-07](history/EUFYMAKE-681-PREFLIGHT-2026-09-07.md)
belegt Studio 4.3.3, Editor 1.20.0 und die direkt angezeigte Firmware 4.0.9.
Die protokollierten Vorschauen liefen mit `Unidirectional`; `Bidirectional` ist
keine abgedeckte Profilvariante.

Die verpflichtende druckfreie Rohimportmatrix ist unter dieser Zielumgebung mit
**29/29 Zellen vollständig**. Alle Zellen entsprechen funktional der
Studio-4.2.2-Baseline. Nur die Bedienfolge von I-06 änderte sich:
`manifest.json` ist auswählbar und wird anschließend mit
`Unsupported file type.` abgewiesen; der Import bleibt damit fail-closed.
Die 13 nativen Projekte bestanden die Strukturprüfung, und alle zwölf aktiven
Projekte erreichten die Vorschau ohne Warnung. Bei Projekt 03 schlug lediglich
die Zeit-/Tintenschätzung zweimal mit `Estimation failed` fehl.

Bei G-05 bleibt die **X-Feld-Semantik mehrdeutig**: Im gespeicherten Canvas
haben COLOR und Gloss dieselbe linke Position X = 122,345 mm. Das
Gloss-Eigenschaftenfeld zeigt bei W = 45,16 mm X = 167,50 mm und damit die
sichtbare rechte Kante. Canvas, Auswahlbox und Vorschau stellen die Glossmaske
linksbündig dar; ein tatsächlicher Runtime- oder Preview-Versatz ist nicht
belegt. Das betroffene Projekt wurde nicht in den kanonischen Projektsatz
zurückgespeichert, und v2 darf daraus keine bestätigte Gloss-Registrierung
ableiten. G-05 entspricht beim getrennten Rohimport der historischen
Studio-4.2.2-Baseline. Sämtliche physischen HEIGHT-, Maß-, Gloss- und
Registrierungstests bleiben offen; im GUI-Lauf wurde kein Druck ausgelöst.

## Evidenz- und Freigaberegel

Golden-Tests fixieren die serialisierten v1- und v2-Verträge. Automatisierte
Roundtrip-/Writer-/Validator-/UI-Tests sichern den internen Vertrag. Reale
Studio-Beobachtungen sind `observed`, Herstellerhinweise je nach Beleg
`confirmed` oder `provisional`, ausstehende Druckeigenschaften `open`.

Erst vollständig protokollierte, freigegebene Hardwareläufe aus #688–#690
dürfen offene Eigenschaften hochstufen. Eine solche Hochstufung erfordert
Profil- und Golden-Review; widersprechende Ergebnisse erzeugen eine neue
Profilversion statt einer stillen Bedeutungsänderung.

Der Snapshot in `profile_contract` wird beim Lesen strikt mit dem registrierten
Vertrag verglichen (`resolve_manifest_profile`): Jede Änderung an einer
registrierten Version – auch an Freitextfeldern wie `scope` oder `reference` –
macht früher geschriebene Manifeste derselben Version unlesbar
(`ProfileContractMismatchError`). Deshalb erhält jede inhaltliche Änderung eine
neue Profilversion; die Golden-Tests erzwingen diese bewusste Entscheidung.

Einmalige Korrektur innerhalb von v1 (2026-09-02): Die Evidenzreferenz
`manufacturer-height-direction` zeigte auf eine nie angelegte Datei
(`EUFYMAKE-687-QUELLENREGISTER.md`) und verweist jetzt auf das
[Annahmeninventar](history/EUFYMAKE-687-ANNAHMENINVENTAR.md) (Abschnitt
„2. Quellen-/Evidenzverzeichnis"). Das blieb ohne neue Profilversion vertretbar,
weil noch kein Release Profil v1 ausgeliefert hatte und kein eingechecktes
Manifest einen Snapshot trug (die sieben Hardware-Pakete sind Legacy-Referenzen
ohne `profile_contract`); der Golden-Digest wurde bewusst neu gesetzt, und ein
Test hält seither fest, dass jeder `docs/`-Pfad im Evidenzvertrag existiert.
Ab jetzt gilt ohne Ausnahme: Jede Snapshot-Änderung ist eine neue Profilversion.
