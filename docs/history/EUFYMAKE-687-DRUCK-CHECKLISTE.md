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
      be71d47fe0f4aab8a80aedd181a91ecf611087840216b2e4f0cf1dda79d2de5c
      --output eufymake-pre-import-report.json`; Ergebnis `ok: true`, Schema 4
      und Soll-Hash bestätigt, Report bei den übrigen Nachweisen abgelegt.
- [ ] Die drei Protokolltabellen aus `EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`
      griffbereit (digital oder ausgedruckt), um sie parallel zu dieser
      Checkliste auszufüllen.

## 1. Vor jedem Testtag (auch an Folgetagen erneut)

Dieser Abschnitt gilt **nicht nur einmalig** – bei mehrtägigen Testreihen an
jedem einzelnen Testtag erneut durchgehen (Anschluss an den
Ermüdungsfehler-Check in Abschnitt 6):

- [ ] Tagesbudget für **heute** festgelegt (Richtwert, kein fixer Wert –
      siehe Governance Abschnitt 1).
- [ ] Bisherigen Budget-Stand aus Abschnitt 5 (Phase 3) übertragen: wie
      viele der insgesamt 24 Drucke sind aus vorherigen Testtagen bereits
      verbraucht?

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
| 1 | I-01 | ☐ | ☐ |
| 2 | I-02 | ☐ | ☐ |
| 3 | I-03 (8 Bit) | ☐ | ☐ |
| 4 | I-03 (16 Bit) | ☐ | ☐ |
| 5 | I-04 (Referenz + halbierte Kopie) | ☐ | ☐ |
| 6 | I-05 (ohne `pHYs`) | ☐ | ☐ |
| 7 | I-05 (konsistent) | ☐ | ☐ |
| 8 | I-05 (widersprüchlich) | ☐ | ☐ |
| 9 | I-05 (X/Y 300/150 dpi) | ☐ | ☐ |
| 10 | I-06 (`export_mm_dpi_conflict/manifest.json` allein) | ☐ | ☐ |
| 11 | I-06 (kompletter Vier-Dateien-Exportordner) | ☐ | ☐ |
| 12 | I-07 | ☐ | ☐ |
| 13 | I-08 (COLOR/HEIGHT/GLOSS vor Crop) | ☐ | ☐ |
| 14 | I-08 (COLOR/HEIGHT/GLOSS nach Crop) | ☐ | ☐ |
| 15 | I-09 (Legacy) | ☐ | ☐ |
| 16 | I-09 (aktuell) | ☐ | ☐ |
| 17 | I-10 (normal) | ☐ | ☐ |
| 18 | I-10 (invertiert) | ☐ | ☐ |
| 19 | I-11 | ☐ | ☐ |
| 20 | I-12 | ☐ | ☐ |
| 21 | I-13 (Alpha/Coverage) | ☐ | ☐ |
| 22 | G-01 (Gloss min/mittel/max) | ☐ | ☐ |
| 23 | G-02 (normal/invertiert) | ☐ | ☐ |
| 24 | G-03 (Stufen + 64…192-Keil) | ☐ | ☐ |
| 25 | G-04a/b/c (fehlend/Null/voll) | ☐ | ☐ |
| 26 | G-05 (Gloss 128×256 gegen COLOR 256×256) | ☐ | ☐ |
| 27 | G-06 (Alpha 0/128/255 × Gloss 128) | ☐ | ☐ |
| 28 | G-07 (HEIGHT 0/32768/65535 × Gloss 128) | ☐ | ☐ |
| 29 | G-08 (Registrierung/Schachbrett) | ☐ | ☐ |

## 4. Phase 2 — Vorschau-Verhalten geprüft, Budget-Startstand notiert

- [ ] Alle 29 Zeilen aus Phase 1 abgeschlossen; keine ungeklärten
      Sicherheits-/Fehlerfälle offen.
- [ ] „Nichts passiert"-Fälle (EM-S03, Spalte in §2) für alle Zeilen
      protokolliert, nicht nur bei „Ja" übersprungen.
- [ ] Budget-Startstand notiert (0 von 24 am allerersten Testtag, sonst der
      aus Abschnitt 1 übertragene Vortagesstand).

## 5. Phase 3 — Druck je Variante (13 Varianten, max. 24 Drucke gesamt)

Nur Zellen, die tatsächlich im Druckprotokoll (§3) stehen. Je Variante:
Budget prüfen → drucken → vermessen → Foto → Druckprotokoll-Zeile ausfüllen
→ Budget-Zähler fortschreiben. Bei Fehldruck: Abschnitt 2 dieser Checkliste
anwenden, **nicht** automatisch wiederholen.

**Vor jedem Foto (Governance Abschnitt 3, verbindlich):**

- [ ] Keine Personen, Gesichter, Kennzeichen oder private Räume im Bild;
      Hintergrund neutral.
- [ ] EXIF-Daten geprüft, GPS-Standortdaten bei Bedarf entfernt.
- [ ] Foto **nicht** ins Git-Repository – nur nach iCloud Drive (nicht
      geteilter Ordner), SHA-256 + iCloud-Pfad in Fotoreferenz-Spalte des
      Druckprotokolls eingetragen.

**Kernaussage-Zeilen** (mindestens zweimal unabhängig drucken, siehe
`PROTOKOLL-VORLAGEN.md` §3): Nullpunkt/Grundfläche, monotoner Keil,
mm/DPI-Referenz, Gloss-Polarität. Welche der Varianten unten das im Einzelnen
sind, ist am Testtag anhand der Kategorien zuzuordnen – nicht vorab
festgelegt. Nach je einem Erstlauf der 13 Varianten bleiben im unveränderten
24er-Budget höchstens elf Wiederholungen. Deshalb zuerst die Kernaussagen
wiederholen; nicht automatisch jede Variante zweimal drucken.

| # | Variante | Lauf 1 | Lauf 2 (max. elf; Kernaussagen zuerst) | Lauf 3+ (nur mit Owner-Freigabe, Vermerk wo/warum) | Fotoreferenz eingetragen | Druckprotokoll-Zeile ausgefüllt |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | I-02 | ☐ | ☐ | | ☐ | ☐ |
| 2 | I-03 (8 Bit) | ☐ | ☐ | | ☐ | ☐ |
| 3 | I-03 (16 Bit) | ☐ | ☐ | | ☐ | ☐ |
| 4 | I-04 | ☐ | ☐ | | ☐ | ☐ |
| 5 | I-05 (konsistent) | ☐ | ☐ | | ☐ | ☐ |
| 6 | I-07 | ☐ | ☐ | | ☐ | ☐ |
| 7 | I-08 (vor Crop) | ☐ | ☐ | | ☐ | ☐ |
| 8 | I-08 (nach Crop) | ☐ | ☐ | | ☐ | ☐ |
| 9 | I-10 (normal) | ☐ | ☐ | | ☐ | ☐ |
| 10 | I-10 (invertiert) | ☐ | ☐ | | ☐ | ☐ |
| 11 | I-11 | ☐ | ☐ | | ☐ | ☐ |
| 12 | I-12 | ☐ | ☐ | | ☐ | ☐ |
| 13 | I-13 (Alpha/Coverage) | ☐ | ☐ | | ☐ | ☐ |

**Budget-Laufsumme:** Jede angekreuzte oder mit einem Vermerk versehene
Zelle in **Lauf 1, Lauf 2 oder Lauf 3+** ist ein physischer Druck und zählt
mit – auch ein Fehldruck ohne verwertbare Messung (Abschnitt 2), auch ein
mit Owner-Freigabe genehmigter dritter Lauf. Summe über alle drei Spalten
und alle 13 Zeilen darf **24 nicht überschreiten**; bei 20/24 oder mehr die
Budget-Eskalation aus Abschnitt 2 dieser Checkliste prüfen, bevor
weitergedruckt wird. Sobald elf Kästchen in „Lauf 2" belegt sind, alle übrigen
Kästchen dieser Spalte sichtbar streichen; eine Umpriorisierung ersetzt eine
noch nicht gestartete Wiederholung und erhöht das Budget nicht.

## 6. Am Ende des Testtags

- [ ] Gerät in den vom Hersteller empfohlenen Ruhezustand versetzt, nicht
      einfach stromlos geschaltet.
- [ ] Alle Fotos aus Phase 3 gesichert (iCloud Drive, SHA-256 dokumentiert).
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
      jenseits der bestehenden 24er-Governance erst nach ausdrücklicher
      Owner-Freigabe starten.
- [ ] Kurzer Ermüdungsfehler-Check: passen Anzahl bearbeiteter Zellen und
      Sorgfalt der Protokollierung zusammen? Falls nicht, betroffene Zeilen
      am nächsten Testtag erneut prüfen statt unklare Werte stehen zu
      lassen.
