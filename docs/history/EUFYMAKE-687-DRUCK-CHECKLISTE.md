# Konsolidierte Druck-Checkliste für EufyMake-Hardware-Tests (Issue #687)

Diese Datei ist eine **Ablauf-Checkliste**, keine eigene Datenquelle: SHA-256-
Werte, Studio-Meldungen und Messwerte gehören weiterhin ausschließlich in die
Protokolltabellen aus
[`EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`](EUFYMAKE-687-PROTOKOLL-VORLAGEN.md).
Diese Datei bündelt nur die **Reihenfolge**, den **Budget-Fortschritt** und
die **Sicherheits-/Ablageregeln** aus
[`EUFYMAKE-687-TESTGOVERNANCE.md`](EUFYMAKE-687-TESTGOVERNANCE.md)
(Status: FREIGEGEBEN) an einer Stelle, damit am Testtag nicht zwischen drei
Dokumenten gesprungen werden muss. Bei Widerspruch gelten die beiden
Quelldokumente.

## 0. Einmalig vor dem ersten Testtag

- [ ] Governance-Status geprüft: `EUFYMAKE-687-TESTGOVERNANCE.md` zeigt
      **FREIGEGEBEN** (Abschnitt 4).
- [ ] Herstellerhandbuch/Sicherheitsblatt des eufyMake E1 griffbereit.
- [ ] Persönliche Schutzausrüstung gemäß Hersteller-/Tintenblatt bereit
      (Reinigung, Tintenwechsel, Weißtinten-Underbase-Einstellung A12).
- [ ] Raum ausreichend belüftet; Hersteller-Empfehlung zu Raumgröße/Lüftung
      geprüft, falls dokumentiert.
- [ ] UV-Warnhinweis verinnerlicht: nicht in Lampe/Druckkopf blicken (auch
      nicht durch ein Sichtfenster), kein Haut-/Augenkontakt mit
      unausgehärteter Tinte.
- [ ] Kinder/Haustiere werden während laufender Drucke vom Gerät ferngehalten.
- [ ] iCloud-Drive-Ordner angelegt (nicht geteilt), z. B.
      `iCloud Drive/BgRemover-EufyMake-Testfotos/687/`.
- [ ] Exakt die committeten Fixtures aus
      `tests/fixtures/eufymake_hardware/` verwenden; am Zielrechner nicht neu
      erzeugen, weil der folgende Vertrauens-Hash die Repository-Bytes bindet.
- [ ] Unabhängigen Pre-Import-Report am Zielrechner erzeugt:
      `python scripts/eufymake_fixture_inspector.py
      --expected-manifest-sha256
      7c0b788cb614068c5e1d2a9ea4453929b2278d0e60fd8206d0c5ff5ed213627a
      --output eufymake-pre-import-report.json`; Ergebnis `ok: true`, Schema 5,
      42/42 Fixtures und 7/7 Pakete bestätigt; Report-SHA-256
      `4c418ccceac01b43b3aee615d89574f590a342da88dd4ad9941522e026b3603b`.
- [ ] Fixture-Ordner am Zielrechner frei von Fremddateien (macOS legt
      `.DS_Store` an, Finder-Kopien ggf. `._*`-Dateien): Der Inspector ist
      fail-closed und meldet jede unerwartete Datei als Fehler – vorher
      entfernen, den Report nicht „gutlesen".
- [ ] Die drei Protokolltabellen aus `EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`
      griffbereit (digital oder ausgedruckt), um sie parallel zu dieser
      Checkliste auszufüllen.
- [ ] **Firmware-Version des E1** abgelesen (am Gerät bzw. in den
      Geräteinformationen von Studio/App) und in `PROTOKOLL-VORLAGEN.md`
      §3.0 sowie in den drei Ergebnisakten eingetragen. „nicht angezeigt"
      ist ab Phase 3 kein zulässiger Wert mehr; die Testmatrix verlangt die
      Firmware je Lauf.
- [ ] **Gerätewarnungen geklärt:** Die in `EUFYMAKE-689-MM-DPI-VERTRAG.md`
      notierten E1-Hinweise (abgelaufener Scraper, Luftfilter, gelbe Tinte)
      sind behoben oder mit Begründung als unkritisch protokolliert;
      Tintenstände aller Kanäle in §3.0 notiert.
- [ ] **Messmittel je Messgröße festgelegt** (Gerät, Auflösung, geschätzte
      Unsicherheit) nach `EUFYMAKE-688-HEIGHT-VERTRAG.md` §4.0 und in §3.0
      eingetragen. Ohne Profilmessmethode bleibt I-14 gesperrt, ohne die
      vorab festgelegte Auswertungsregel bleibt der I-03-Vergleich gesperrt.
- [ ] **Substrat festgelegt** (Material, Farbe, Dicke, Charge) und in §3.0
      eingetragen; für I-13 und G-06 zwingend **nicht-weiß**, weil
      Weiß-Unterlage und Deckung auf weißem Material unsichtbar bleiben.
      Innerhalb eines Vergleichs bleibt das Substrat identisch.
- [ ] **Evidenzablage für die Studio-Phase** angelegt: je Zelle ein
      Unterordner `…/<Issue>/<Zelle>/studio/` im iCloud-Ordner für
      Screenshots und gespeicherte Studio-Projekte (Governance §3 und der
      vorbereitete Nachtrag in Governance Abschnitt 5).
- [ ] **Owner-Entscheidung I-10/G-02** getroffen und als Freigabe-Vermerk in
      Governance §4 eingetragen (siehe Abschnitt 5 dieser Checkliste); bis
      dahin werden die Zeilen 9–10 der Stammvariantentabelle nicht gedruckt.

## 1. Vor jedem Testtag (auch an Folgetagen erneut)

Dieser Abschnitt gilt **nicht nur einmalig** – bei mehrtägigen Testreihen an
jedem einzelnen Testtag erneut durchgehen (Anschluss an den
Ermüdungsfehler-Check in Abschnitt 6):

- [ ] Tagesbudget für **heute** festgelegt (Richtwert, kein fixer Wert –
      siehe Governance Abschnitt 1).
- [ ] Bisherigen Budget-Stand aus Abschnitt 5 (Phase 3) übertragen: wie
      viele der insgesamt 35 Drucke sind aus vorherigen Testtagen bereits
      verbraucht?
- [ ] Tintenstände und Gerätewarnungen erneut geprüft und in
      `PROTOKOLL-VORLAGEN.md` §3.0 nachgetragen; feste Laufparameter
      (Substrat, Layoutgröße, Texturhöhe, Ink Mode, Gloss-Pfad) unverändert –
      sonst beginnt eine neue, getrennt protokollierte Vergleichsreihe.

## 2. Sicherheits-Abbruchkriterien (Kurzreferenz, gilt jederzeit)

Vollständiger Wortlaut in `EUFYMAKE-687-TESTGOVERNANCE.md`, Abschnitte 1–2:

- **Gerät nie unbeaufsichtigt lassen**, solange ein Druck- oder
  Importvorgang läuft.
- **Fehlgeschlagener Druck** (Papier-/Substratstau, falsches Material,
  offensichtlich falsche Farbe/Größe) → sofort abbrechen, **nicht**
  automatisch wiederholen, Ursache in der Zeile der betroffenen Variante im
  **Druckprotokoll** vermerken. Zählt gegen das Budget, auch ohne
  verwertbare Messung.
- **Fehlercode/ungewöhnliches Geräusch/Geruch/Übertemperatur** → Nothalt/
  Netzschalter, keine Fortsetzung ohne Ursachenklärung. Dokumentation im
  Druckprotokoll (falls während eines Druckvorgangs) oder Importprotokoll
  (falls während eines reinen Importvorgangs ohne gestarteten Druck).
- **Dritter (oder weiterer) Druck derselben Variante** → braucht eine
  bewusste Owner-Entscheidung, bevor gedruckt wird, **und** zählt gegen das
  Budget wie jeder andere Druck (siehe Abschnitt 5, Spalte „Lauf 3+").
- **Budget erschöpft oder absehbar knapp** → pausieren, Owner ausdrücklich
  um erweiterte Freigabe bitten – nie stillschweigend über das Limit hinaus
  drucken.
- Vor **jeder** druckenden Zelle muss die eigene Dateivalidierung + der
  eigene Import bereits abgeschlossen und protokolliert sein.

## 3. Phase 1 — Dateivalidierung + Import (kein Materialverbrauch)

Reihenfolge aus `EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`, Abschnitte 1–2. Diese
Phase komplett abschließen, **bevor** in Phase 3 der erste Druck startet –
das ist die materialsparende Vorprüfung aus Governance Abschnitt 1. SHA-256
je Fixture-Datei am Zielrechner neu berechnen und mit dem in
`fixtures_manifest.json`/`PROTOKOLL-VORLAGEN.md` hinterlegten Wert
abgleichen (**nicht** ungeprüft übernehmen).

| # | Zelle | ☐ Dateivalidierung (§1) | ☐ Import + Importprotokoll (§2) |
| --- | --- | --- | --- |
| 1 | I-01 | ☑ | ☑ |
| 2 | I-02 | ☑ | ☑ |
| 3 | I-03 (8 Bit) | ☑ | ☑ |
| 4 | I-03 (16 Bit) | ☑ | ☑ |
| 5 | I-04 (Referenz + halbierte Kopie) | ☑ | ☑ |
| 6 | I-05 (ohne `pHYs`) | ☑ | ☑ |
| 7 | I-05 (konsistent) | ☑ | ☑ |
| 8 | I-05 (widersprüchlich) | ☑ | ☑ |
| 9 | I-05 (X/Y 300/150 dpi) | ☑ | ☑ |
| 10 | I-06 (`export_mm_dpi_conflict/manifest.json` allein) | ☑ | ☑ |
| 11 | I-06 (kompletter Vier-Dateien-Exportordner) | ☑ | ☑ |
| 12 | I-07 | ☑ | ☑ |
| 13 | I-08 (COLOR/HEIGHT/GLOSS vor Crop) | ☑ | ☑ |
| 14 | I-08 (COLOR/HEIGHT/GLOSS nach Crop) | ☑ | ☑ |
| 15 | I-09 (Legacy) | — (n. z.) | — (n. z.) |
| 16 | I-09 (aktuell) | — (n. z.) | — (n. z.) |
| 17 | I-10 (normal) | ☑ | ☑ |
| 18 | I-10 (invertiert) | ☑ | ☑ |
| 19 | I-11 | ☑ | ☑ |
| 20 | I-12 | ☑ | ☑ |
| 21 | I-13 (Alpha/Coverage) | ☑ | ☑ |
| 22 | I-14 (direkte 256×256-Referenz) | ☑ | ☑ |
| 23 | I-14 (direkte 128×128-Kontrolle) | ☑ | ☑ |
| 24 | G-01 (Gloss min/mittel/max) | ☑ | ☑ |
| 25 | G-02 (normal/invertiert) | ☑ | ☑ |
| 26 | G-03 (Stufen + 64…192-Keil) | ☑ | ☑ |
| 27 | G-04a/b/c (fehlend/Null/voll) | ☑ | ☑ |
| 28 | G-05 (Gloss 128×256 gegen COLOR 256×256) | ☑ | ☑ |
| 29 | G-06 (Alpha 0/128/255 × Gloss 128) | ☑ | ☑ |
| 30 | G-07 (HEIGHT 0/32768/65535 × Gloss 128) | ☑ | ☑ |
| 31 | G-08 (Registrierung/Schachbrett) | ☑ | ☑ |

Die #688-Zeile 21 (I-13) wurde am 2026-09-02 dateivalidiert und zunächst über
den Bilddialog importiert. Am 2026-09-03 wurde `height_mean_16bit.png` zusätzlich
im selben `color_alpha_coverage.png`-Objekt nativ über `Customize Texture`
zugewiesen; `3D` und die drei Alpha-/Farbfelder blieben in der Vorschau sichtbar.
Die #688-Zeilen 22–23 (I-14) wurden am 2026-09-03 dateivalidiert und in
Studio 4.2.2 über `Customize Texture` vorgeprüft. Die direkt erzeugten
16-Bit-Fixtures mit 256×256 und 128×128 Pixeln wurden ohne Warnung akzeptiert;
beim Ersetzen blieb das Objekt jeweils 90,31×90,31 mm. Nach der Erweiterung
auf den begrenzten 1/4…3/4-Wertebereich und die feine Kalibrierfläche wurden
die endgültigen Bytes aller drei Dateien bis 03:00 CEST erneut ohne Warnung
akzeptiert. Die #690-Zeilen 24–26 und 28–31 wurden am 2026-09-02 mit
Studio 4.2.2 / Editor 1.20.0 abgeschlossen. Zeile 27 (G-04) folgte am
2026-09-03 mit dem
Import der tatsächlichen Null-/Voll-Writer-Assets; G-04a ist mangels
Gloss-Datei nicht anwendbar. Damit sind die #690-Importzeilen vollständig in
der Ergebnisakte protokolliert. „Import“ bedeutet weiterhin ausdrücklich den
Bilddialog-Grenzbefund ohne native Gloss-Maskenkopplung. Es wurde weder
**Preview** noch **Print** ausgelöst; die physischen Aussagen bleiben offen.

I-08 wurde am 2026-09-03 ergänzt: Die 16-Bit-HEIGHT-Datei wurde über den
nativen `Customize Texture`-Pfad dem COLOR-Objekt zugewiesen. Der Crop blieb
innerhalb dieses Objekts gekoppelt; die separate Gloss-Ebene blieb unverändert.
I-09 wurde am selben Tag ausdrücklich als **nicht blockierend/nicht
anwendbar** eingestuft: `.empf` ist ein separater nativer Projektpfad und kein
Bestandteil des bestätigten BgRemover-PNG-Workflows. Die Zeilen bleiben zur
Transparenz erhalten und werden nur bei einer späteren Produktentscheidung für
native `.empf`-Projekte reaktiviert.

Die bis dahin noch offenen HEIGHT-/mm-DPI-Pflichtzeilen wurden am 2026-09-03
abgeschlossen.
I-02 und I-03 akzeptierten 16- und 8-Bit-HEIGHT nativ; I-04 skalierte die
pixelhalbierte, aber seitenverhältnisgleiche HEIGHT-Datei auf die unveränderte
COLOR-Fläche. Die invertierte 16-Bit-Gegenprobe kehrte die Neigungsrichtung der
3D-Keilvorschau um; I-07 zeigte Null-Grundfläche und Vollweiß-Plateau, I-11 die
diskreten Stufen und I-13 die native Alpha×HEIGHT-Kopplung. I-12 wurde mit der
ausdrücklichen Warnung `Depth image ratio does not match the original image`
abgelehnt und ersetzte die bestehende HEIGHT-Zuweisung nicht. Alle Ergebnisse
stehen im Importprotokoll. Es wurde weiterhin weder **Preview** noch **Print**
ausgelöst; der Budgetstand bleibt **0/35**.

Für G-04b/c wurden am 2026-09-03 anschließend auch die tatsächlichen
`export_gloss_zero/full/gloss_mask.png`-Writer-Assets importiert. Studio zeigte
beide ohne Warnung als sichtbare schwarze beziehungsweise weiße
`gloss_mask`-Ebene, jeweils „Flat“ und 90,31×90,31 mm. G-04a bleibt mangels
Gloss-Datei nicht anwendbar. Weder **Preview** noch **Print** wurde ausgelöst;
der Budgetstand bleibt **0/35**.

## 4. Phase 2 — Vorschau-Verhalten geprüft, Budget-Startstand notiert

- [x] Alle 29 verpflichtenden Zeilen aus Phase 1 abgeschlossen; I-09 Legacy/
      aktuell sind gemäß Scope-Entscheid vom 2026-09-03 nicht anwendbar;
      G-04b/c wurden mit den tatsächlichen Writer-Assets abgeschlossen.
- [x] „Nichts passiert"-Fälle (EM-S03, Spalte in §2) für alle Zeilen
      protokolliert, nicht nur bei „Ja" übersprungen.
- [x] Budget-Startstand notiert (**0 von 35**, 2026-09-03; sonst der
      aus Abschnitt 1 übertragene Vortagesstand).

### 4.1 Phase 2b — Vorschau ohne Druck und feste Laufparameter (kein Materialverbrauch)

Erst nach Phase 2 und **vor** dem ersten Druck. Die Vorschau (`Preview`)
wird nur bis zur Druckvorbereitungsseite geöffnet, `Print` wird nie
ausgelöst. Ein von der Vorschau selbst gestarteter Gerätevorgang (etwa ein
Kamerascan des Betts) verbraucht kein Material und zählt nicht gegen das
Budget; er wird trotzdem nur nach ausdrücklicher Owner-Freigabe ausgelöst,
weil bisher bewusst weder `Preview` noch `Print` gestartet wurde.

- [ ] Feste Laufparameter in `PROTOKOLL-VORLAGEN.md` §3.0 eingetragen:
      Layoutgröße und Position, Texturmodus/Ink Mode/Texturhöhe,
      Qualitätsprofil, Substrat, Gloss-Pfad samt Ursprung, Skalierung,
      Rotation und Registrierung. Vorgabe für die HEIGHT-Vergleiche:
      90,31 × 90,31 mm aus dem 72-dpi-Import und 2,50 mm `Color Raised`,
      solange Zeit- und Tintenschätzung das zulassen; innerhalb eines
      Vergleichs (I-02/I-04, I-03/I-14, G-01…G-08) identisch.
- [ ] Für jede Druckvariante aus Abschnitt 5 die Vorschau geöffnet und in
      `PROTOKOLL-VORLAGEN.md` §3.1 protokolliert: Warnungen, Objektmaße und
      Position, Ink Mode, Texturhöhe sowie, falls Studio sie anzeigt,
      geschätzte Druckzeit und Tintenmenge. Eine Warnung in der Vorschau ist
      ein eigener Befund und sperrt die Variante bis zur Klärung.
- [ ] Tintenbedarf gegen die Tintenstände geprüft. Grobe Planungsannahme,
      solange Studio keine Schätzung zeigt: Volumen der Erhebung entspricht
      etwa dem Tintenvolumen, also rund 10 ml je 90-mm-Keil und bis rund
      20 ml je Vollfläche bei 2,50 mm, ohne Underbase. Reicht der Vorrat
      absehbar nicht für die 13 Erstläufe, greift die Budget-Eskalation aus
      Abschnitt 2 **vor** dem ersten Druck (Layout kleiner oder Texturhöhe
      geringer festlegen, dann für die ganze Vergleichsreihe).
- [ ] Gloss-Pfad je Zelle nach `EUFYMAKE-690-GLOSS-VERTRAG.md` §6.1 gewählt
      und in §3.0 protokolliert; ohne eindeutigen Pfad bleibt die Zelle
      gesperrt.

## 5. Phase 3 — Druck je Variante (13 Stammvarianten + 11 Gloss-Läufe, maximal 35 Drucke)

Nur Zellen, die tatsächlich im Druckprotokoll (§3) stehen. Je Variante:
Budget prüfen → Vorschau-Protokoll §3.1 der Variante liegt vor → drucken →
vermessen → Foto → Screenshots und gespeichertes Studio-Projekt sichern →
Druckprotokoll-Zeile ausfüllen → Budget-Zähler fortschreiben. Bei Fehldruck:
Abschnitt 2 dieser Checkliste anwenden, **nicht** automatisch wiederholen.

**I-12 nicht drucken:** Die abweichende Seitenrelation wurde von Studio
fail-closed abgelehnt; I-12 ist damit ein abgeschlossener Import-Negativtest
ohne druckbares Objekt und ohne Materialplatz. Der abgelehnte 2:1-Fall besitzt
daher keine physische H-03-Messung. I-02 (256×256-HEIGHT-Referenz) und I-04
(128×128-HEIGHT bei gleicher Seitenrelation) werden bei identischen Layout-
und Druckparametern als kombinierter Pixelgrößen-/Resampling-End-to-End-Test
verglichen. Da I-04 bereits im Fixture-Generator per LANCZOS verkleinert und
gerundet wird, darf das Ergebnis weder als isolierte Studio-Filterwirkung noch
dem abweichenden Seitenverhältnis zugerechnet werden.

**I-14 kontrolliert drucken:** Die 256×256-Referenz
`height_impulse_edge_16bit.png` ist zugleich die I-03-16-Bit-Variante; I-03
8 Bit verwendet das pixelgleiche `height_impulse_edge_8bit.png`. I-14 fügt
nur `height_impulse_edge_direct_half_16bit.png` (128×128) als eigenen Druck
hinzu. Beide I-14-Dateien wurden direkt aus derselben normierten Formel
erzeugt (Kante bei x=1/2, Impulszentrum bei 1/4, Impulsbreite 1/64), nicht
auseinander skaliert. Der Wertebereich ist auf 1/4…3/4 begrenzt; im unteren
Viertel liegen 4096 feine 16-Bit-Sollstufen für den I-03-Präzisionsvergleich.
Layout W/H und Position, `Customize Texture`,
`Color Raised`, 2,50 mm, Material und Qualitätsprofil müssen identisch sein.
Kantenbreite (10–90 %) und Impulsbreite (FWHM) auf der Scanlinie y=1/2,
Peak-, Plateau- und Basishöhe sowie die Trennbarkeit der feinen Kalibrierstufen
mit Messunsicherheit erfassen. Eine Verschiebung von 1/4…3/4 auf den vollen
Höhenbereich als Normalisierung protokollieren. Die Studio-Vorschau getrennt vom physischen
Druck bewerten. Ohne zugängliches Studio-Ausgaberaster ist ein physischer
Unterschied dem kombinierten Studio-/Druckpfad zuzurechnen, nicht Studio allein.

**I-08 nach Crop drucken:** Studio koppelt den bestätigten Crop nur an das
native COLOR/HEIGHT-Objekt (W/H 44,86/90,31 mm, X/Y 167,79/164,84 mm); die
separate Gloss-Ebene blieb bei 90,31 × 90,31 mm und X/Y 122,34/164,84 mm.
Für den Druck „nach Crop" bleibt die Gloss-Ebene **unverändert** – weder
beschnitten noch verschoben. Weil der Crop die rechte Kante des Objekts
festhielt, liegen ihre Landmarken über der verbliebenen COLOR/HEIGHT-Fläche
weiterhin an derselben physischen Stelle und prüfen die Registrierung; der
Rest der Gloss-Ebene druckt Gloss ohne Farbe und wird als solcher
protokolliert. Ein manuelles Nachbeschneiden der Gloss-Ebene ist nicht
zulässig, weil es Bedienfehler mit Studio-Verhalten vermischen würde. Die
Regel steht in `PROTOKOLL-VORLAGEN.md` §3 und
`EUFYMAKE-689-MM-DPI-VERTRAG.md`.

**I-10 gegen G-02 (Owner-Entscheidung vor dem ersten Gloss-Druck):** I-10
normal/invertiert und G-02 verwenden dieselben Dateien `gloss_wedge.png`
und `gloss_wedge_inverted.png` über denselben Gloss-Pfad; der bisherige Plan
druckte damit jede Richtung dreimal. Bis zur Entscheidung in Governance §4
werden die Zeilen 9–10 der Stammvariantentabelle **nicht** gedruckt.
Vorbereitete Optionen: **(A, empfohlen)** I-10 physisch streichen – die
Polarität liefert G-02 mit je zwei unabhängigen Läufen je Richtung, die
Plätze 9–10 bleiben unzugeordnet und werden ohne neue Owner-Freigabe nicht
umgewidmet; **(B)** I-10 dem in `EUFYMAKE-690-GLOSS-VERTRAG.md` §6.1
dokumentierten Spot-UV-Zweipass zuordnen, um den Zweipass gegen den nativen
`Gloss Varnish`-Pfad zu vergleichen (GL-02). Beide Optionen verändern das
harte Limit von 35 nicht.

**Zusätzlicher #690-Gloss-Preflight:** Ein importiertes „Flat“-Graustufenbild
ist keine Gloss-Zuweisung. Vor jeder Gloss-Zelle muss der in
`EUFYMAKE-690-GLOSS-VERTRAG.md` Abschnitt 6.1 festgelegte native Gloss-/Spot-UV-
Pfad oder der dort dokumentierte Zweipass ausgewählt und mit identischem
Ursprung, Skalierung, Rotation und Registrierung protokolliert sein. Ist keiner
der beiden Pfade eindeutig verfügbar, bleibt die Zelle blockiert und wird nicht
als gewöhnliches Graustufenbild gedruckt.

**Freigegebenes #690-Zusatzbudget:** NikolayDA hat am 2026-09-02 das harte
Gesamtlimit auf 35 Drucke erhöht. Die Plätze 25–35 sind den folgenden elf
Gloss-Läufen fest zugeordnet. Die Budgetfreigabe ersetzt keinen technischen
Preflight: Solange die jeweilige native HEIGHT-/Gloss-Zuweisung oder feste
Dimensions-/Registrierungsregel nicht belegt ist, bleibt der Lauf trotz
Budgetplatz blockiert.

| Zelle | Owner-Freigabe (Datum/Verweis) | Budgetplatz/ersetzte Variante | HEIGHT-/Gloss-Preflight | Status |
| --- | --- | --- | --- | --- |
| G-01 | NikolayDA, 2026-09-02; Governance §4 | 25 | nativer Gloss-/Spot-UV-Pfad | freigegeben; `Gloss Varnish`-Pfad belegt, Laufparameter offen |
| G-02 | NikolayDA, 2026-09-02; Governance §4 | 26–29 (normal 1/2, invertiert 1/2) | nativer Gloss-/Spot-UV-Pfad | freigegeben; `Gloss Varnish`-Pfad belegt, Polarität/Laufparameter offen |
| G-03 | NikolayDA, 2026-09-02; Governance §4 | 30 | nativer Gloss-/Spot-UV-Pfad | freigegeben; `Gloss Varnish`-Pfad belegt, Laufparameter offen |
| G-04a/b/c | NikolayDA, 2026-09-02; Governance §4 | 31 | Produktionswriter-Assets importieren; nativer Gloss-/Spot-UV-Pfad | freigegeben; tatsächliche Null-/Voll-Writer-Assets im Bildimport belegt, nativer Gloss-/Spot-UV-Pfad und Laufparameter offen |
| G-05 | NikolayDA, 2026-09-02; Governance §4 | 32 | feste Dimensions-/Registrierungsregel | freigegeben; Dimensions-/Registrierungsregel offen |
| G-06 | NikolayDA, 2026-09-02; Governance §4 | 33 | nativer Gloss-/Spot-UV-Pfad; Basispass fixiert | freigegeben; nativer Pfad belegt, Basispass/Registrierung offen |
| G-07 | NikolayDA, 2026-09-02; Governance §4 | 34 | native HEIGHT-/Texture- und Gloss-Zuweisung; Reliefwerte fixiert | freigegeben; beide nativen Pfade belegt, Reliefwerte/Registrierung offen |
| G-08 | NikolayDA, 2026-09-02; Governance §4 | 35 | nativer Gloss-/Spot-UV-Pfad; Registrierung fixiert | freigegeben; nativer Pfad belegt, Registrierung offen |

**Vor jedem Foto (Governance Abschnitt 3, verbindlich):**

- [ ] Keine Personen, Gesichter, Kennzeichen oder private Räume im Bild;
      Hintergrund neutral.
- [ ] EXIF-Daten geprüft, GPS-Standortdaten bei Bedarf entfernt.
- [ ] Foto **nicht** ins Git-Repository – nur nach iCloud Drive (nicht
      geteilter Ordner), SHA-256 + iCloud-Pfad in Fotoreferenz-Spalte des
      Druckprotokolls eingetragen.

**Kernaussage-Zeilen** (mindestens zweimal unabhängig drucken, siehe
`PROTOKOLL-VORLAGEN.md` §3): Nullpunkt/Grundfläche, monotoner Keil,
mm/DPI-Referenz, Gloss-Polarität (Letztere ist bei Option A des
I-10/G-02-Entscheids bereits durch die zwei G-02-Läufe je Richtung
abgedeckt). Welche der Varianten unten das im Einzelnen
sind, ist am Testtag anhand der Kategorien zuzuordnen – nicht vorab
festgelegt. Nach je einem Erstlauf der 13 Stammvarianten und den elf fest
eingeplanten Gloss-Läufen bleiben höchstens elf bereits freigegebene
Wiederholungen der Stammvarianten. Der ausführbare Plan umfasst daher maximal
35 Drucke. Im für Stammvarianten vorgesehenen Bereich 1–24 ist
**Budgetplatz 24** mit Owner-Freigabe vom 2026-09-03 I-14 zugeordnet; die
Gloss-Plätze 25–35 bleiben unverändert belegt. Deshalb zuerst die Kernaussagen
wiederholen und nicht automatisch jede Variante zweimal drucken.

| # | Variante | Lauf 1 | Lauf 2 (max. elf; Kernaussagen zuerst) | Lauf 3+ (nur mit Owner-Freigabe, Vermerk wo/warum) | Fotoreferenz eingetragen | Druckprotokoll-Zeile ausgefüllt |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | I-02 | ☐ | ☐ | | ☐ | ☐ |
| 2 | I-03 (8 Bit, Impuls/Kante) | ☐ | ☐ | | ☐ | ☐ |
| 3 | I-03 (16 Bit, Impuls/Kante; I-14-Referenz) | ☐ | ☐ | | ☐ | ☐ |
| 4 | I-04 (halbierte Pixelkante; Referenz I-02) | ☐ | ☐ | | ☐ | ☐ |
| 5 | I-05 (konsistent) | ☐ | ☐ | | ☐ | ☐ |
| 6 | I-07 | ☐ | ☐ | | ☐ | ☐ |
| 7 | I-08 (vor Crop) | ☐ | ☐ | | ☐ | ☐ |
| 8 | I-08 (nach Crop) | ☐ | ☐ | | ☐ | ☐ |
| 9 | I-10 (normal) – ⛔ gesperrt bis Owner-Entscheidung I-10/G-02 | ☐ | ☐ | | ☐ | ☐ |
| 10 | I-10 (invertiert) – ⛔ gesperrt bis Owner-Entscheidung I-10/G-02 | ☐ | ☐ | | ☐ | ☐ |
| 11 | I-11 | ☐ | ☐ | | ☐ | ☐ |
| 12 | I-13 (Alpha/Coverage) | ☐ | ☐ | | ☐ | ☐ |
| 13 | I-14 (direkte 128×128-Kontrolle; Referenz I-03 16 Bit) | ☐ | ☐ | | ☐ | ☐ |

**Fest zugeordnete Gloss-Läufe (Budgetplätze 25–35):**

| Budgetplatz | Zelle/Lauf | Druck | Fotoreferenz eingetragen | Gloss-Druckprotokoll-Zeile ausgefüllt |
| --- | --- | --- | --- | --- |
| 25 | G-01 Lauf 1 | ☐ | ☐ | ☐ |
| 26 | G-02 normal Lauf 1 | ☐ | ☐ | ☐ |
| 27 | G-02 normal Lauf 2 | ☐ | ☐ | ☐ |
| 28 | G-02 invertiert Lauf 1 | ☐ | ☐ | ☐ |
| 29 | G-02 invertiert Lauf 2 | ☐ | ☐ | ☐ |
| 30 | G-03 Lauf 1 | ☐ | ☐ | ☐ |
| 31 | G-04a/b/c Lauf 1 | ☐ | ☐ | ☐ |
| 32 | G-05 Lauf 1 | ☐ | ☐ | ☐ |
| 33 | G-06 Lauf 1 | ☐ | ☐ | ☐ |
| 34 | G-07 Lauf 1 | ☐ | ☐ | ☐ |
| 35 | G-08 Lauf 1 | ☐ | ☐ | ☐ |

**Budget-Laufsumme:** Jede angekreuzte oder mit einem Vermerk versehene
Zelle in **Lauf 1, Lauf 2 oder Lauf 3+** ist ein physischer Druck und zählt
mit – auch ein Fehldruck ohne verwertbare Messung (Abschnitt 2), auch ein
mit Owner-Freigabe genehmigter dritter Lauf. Ohne neue Owner-Freigabe darf die
Summe über alle drei Spalten der Stammvariantentabelle sowie die elf Zeilen der
Gloss-Tabelle **35 nicht überschreiten**. Bei 31/35 oder mehr die
Budget-Eskalation aus Abschnitt 2 dieser
Checkliste prüfen, bevor weitergedruckt wird. Sobald elf Kästchen in „Lauf 2"
belegt sind, alle übrigen Kästchen dieser Spalte sichtbar streichen.
**Budgetplatz 24** ist I-14 zugeordnet; Platz 35 bleibt fest G-08 zugeordnet.
Ein wegen fehlendem Preflight ungenutzter Gloss-Platz wird nicht automatisch
zu einem Zusatz- oder Wiederholungslauf; jede Umwidmung braucht einen
Owner-Vermerk und erhöht das Gesamtlimit nicht.

## 6. Am Ende des Testtags

- [ ] Gerät in den vom Hersteller empfohlenen Ruhezustand versetzt, nicht
      einfach stromlos geschaltet.
- [ ] Alle Fotos aus Phase 3 gesichert (iCloud Drive, SHA-256 dokumentiert).
- [ ] Screenshots und gespeicherte Studio-Projekte je Zelle gesichert
      (iCloud Drive, SHA-256 in der Spalte „Screenshot-Referenz" des
      Importprotokolls bzw. in §3.1); Konto- oder Nutzernamen in
      Studio-Screenshots vorher abgedeckt oder beschnitten.
- [ ] Protokolltabellen in `EUFYMAKE-687-PROTOKOLL-VORLAGEN.md` mit den
      heutigen Einträgen aktualisiert und committed.
- [ ] Jede Aussage bereits jetzt oder spätestens beim Zusammenfassen in
      einen Vertrag als „Herstellerangabe", „Importbeobachtung" oder
      „Druckmessung" gekennzeichnet (#687-AC).
- [ ] #688-Resultate samt Messpunkten und finaler Default-/Validator-
      Entscheidung in `EUFYMAKE-688-HEIGHT-VERTRAG.md` übertragen; keine
      leeren Felder als negatives oder positives Ergebnis gewertet.
- [ ] #689-Resultate samt X-/Y-, Prioritäts-, Rundungs- und
      Registrierungsbefunden in `EUFYMAKE-689-MM-DPI-VERTRAG.md` übertragen;
      keine leeren Felder als Ergebnis gewertet.
- [ ] #690-Resultate samt Polarität, Intensitäts-/Normalisierungsbefund,
      Alpha-/HEIGHT-Kreuzung und Material-/Ink-Mode-Profilgrenze in
      `EUFYMAKE-690-GLOSS-VERTRAG.md` übertragen. Zusätzliche Druckvarianten
      jenseits der bestehenden 35er-Governance erst nach ausdrücklicher
      Owner-Freigabe starten.
- [ ] Kurzer Ermüdungsfehler-Check: passen Anzahl bearbeiteter Zellen und
      Sorgfalt der Protokollierung zusammen? Falls nicht, betroffene Zeilen
      am nächsten Testtag erneut prüfen statt unklare Werte stehen zu
      lassen.
