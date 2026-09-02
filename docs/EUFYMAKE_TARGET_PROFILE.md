# Versioniertes EufyMake-Zielprofil

Stand: 2026-09-02 · Profil `bgremover-eufymake-import@1` · Schema 1

## Zweck und Status

BgRemover verwendet für Planung, Prüfung, Dialog, Writer und Manifest dasselbe
unveränderliche Zielprofil aus `bgremover/eufymake_profile.py`. Das Profil ist
eine **BgRemover-Konvention für manuell importierbare Dateien**, keine offizielle
EufyMake-Spezifikation und kein `.empf`-Containervertrag.

Profil v1 ist **vorläufig**. Studio-Importbeobachtungen aus Version 4.2.2 sind
erfasst; die physischen Druckmessungen aus #688–#690 fehlen. Deshalb werden
16-Bit-Nutzung, Grauwert→mm-Abbildung, Druckmaß/Registrierung sowie
Gloss-Polarität und -Intensität nicht als bestätigt ausgegeben.

## Referenz und Zielumgebung

| Feld | Wert | Status |
| --- | --- | --- |
| Profilschema | 1 | interner Maschinenvertrag |
| Profil-ID / Version | `bgremover-eufymake-import` / `1` | stabil |
| Gerät | eufyMake E1 | Zielgrenze |
| Studio | 4.2.2 | beobachtet |
| Firmware | nicht protokolliert | offen |
| BgRemover-Version | zur Laufzeit im Manifest | ausdrücklich getrennt vom Zielprofil |

Eine neue Semantik oder Zielumgebung verändert nicht rückwirkend v1. Sie erhält
eine neue Profilversion beziehungsweise eine neue Profil-ID und wird im
`ProfileRegistry` registriert. Unbekannte IDs und nicht unterstützte Versionen
werden getrennt und verständlich abgewiesen.

Die Registry akzeptiert nur intern konsistente Verträge: Profilversionen sind
echte Integer (keine booleschen Ersatzwerte), COLOR und HEIGHT sind als von den
aktuellen Consumern benötigte Rollen vorhanden, Asset-Dateinamen sind
eindeutige Basenames außerhalb des reservierten `manifest.json`, jede
unterstützte Bittiefe besitzt genau einen Wertebereich und sämtliche stabilen
Validator-Codes sind mit Abhilfe definiert. Als `required` markierte Rollen
werden unabhängig von einer optionalen UI-Auswahl immer geprüft und exportiert.

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
- Studio 4.2.2 hat `pHYs` je Achse und ohne `pHYs` einen 72-dpi-Startwert
  beobachtbar verwendet. Manuelle Studio-Maße können diesen Startwert ersetzen.
- Priorität im vollständigen Rollenverbund, Rundung, Registrierung und
  tatsächliches Druckmaß bleiben bis #689 physisch offen.

## Validierung und Abhilfe

Jeder Befund enthält einen stabilen Code, Schweregrad, betroffene Rolle,
kanonischen Dateinamen und eine maschinenlesbare Abhilfe. Die Regel selbst liegt
im Profil. Fehler blockieren; Warnungen benötigen eine bewusste Bestätigung.
Beispiele sind `asset_size_mismatch` + `match_canvas_dimensions`,
`bit_depth_unconfirmed` + `confirm_height_carrier` und `gloss_ink_mode` +
`assign_native_gloss_in_studio`.

## Manifest und Legacy-Zuordnung

Neue Manifeste behalten die alten Felder `profile` und `profile_version` und
ergänzen:

- `profile_contract`: vollständiger Profilsnapshot mit Schema, Zielumgebung,
  Rollen-, Maß-, Validierungs- und Evidenzvertrag;
- `producer`: Anwendung und BgRemover-Version;
- `target`: Pixelmaße, physische mm und getrennte X-/Y-DPI;
- `assets[].channel_interpretation`: Wertebereich, Richtung, Semantik,
  Alpha-Regel, Status und Evidenz-IDs.

`resolve_manifest_profile()` liest alte Manifeste mit nur `profile` und
`profile_version`, kennzeichnet sie aber als Legacy-Referenz. Fehlende
Snapshot-/Evidenzfelder werden nicht erfunden und das Manifest wird nicht
stillschweigend umgeschrieben. Das Manifest bleibt interne Provenienz; Studio
4.2.2 hat es im Bildimport nicht als Paketvertrag verwendet.

## Evidenz- und Freigaberegel

Der Golden-Test fixiert den serialisierten v1-Vertrag. Automatisierte
Roundtrip-/Writer-/Validator-/UI-Tests sichern den internen Vertrag. Reale
Studio-Beobachtungen sind `observed`, Herstellerhinweise je nach Beleg
`confirmed` oder `provisional`, ausstehende Druckeigenschaften `open`.

Erst vollständig protokollierte, freigegebene Hardwareläufe aus #688–#690
dürfen offene Eigenschaften hochstufen. Eine solche Hochstufung erfordert
Profil- und Golden-Review; widersprechende Ergebnisse erzeugen eine neue
Profilversion statt einer stillen Bedeutungsänderung.
