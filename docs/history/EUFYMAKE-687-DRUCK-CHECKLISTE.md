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
- [ ] Fixtures aktuell: entweder die committeten Fixtures aus
      `tests/fixtures/eufymake_hardware/` verwenden oder frisch erzeugen
      (`python scripts/eufymake_fixture_generator.py generate`).
- [ ] Die drei Protokolltabellen aus `EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`
      griffbereit (digital oder ausgedruckt), um sie parallel zu dieser
      Checkliste auszufüllen.
- [ ] Tagesbudget für heute festgelegt (Richtwert, kein fixer Wert – siehe
      Governance Abschnitt 1).

## 1. Sicherheits-Abbruchkriterien (Kurzreferenz, gilt jederzeit)

Vollständiger Wortlaut in `EUFYMAKE-687-TESTGOVERNANCE.md`, Abschnitte 1–2:

- **Fehlgeschlagener Druck** (Papier-/Substratstau, falsches Material,
  offensichtlich falsche Farbe/Größe) → sofort abbrechen, **nicht**
  automatisch wiederholen, Ursache in der Zeile der betroffenen Variante im
  **Druckprotokoll** vermerken. Zählt gegen das Budget, auch ohne
  verwertbare Messung.
- **Fehlercode/ungewöhnliches Geräusch/Geruch/Übertemperatur** → Nothalt/
  Netzschalter, keine Fortsetzung ohne Ursachenklärung. Dokumentation im
  Druckprotokoll (falls während eines Druckvorgangs) oder Importprotokoll
  (falls während eines reinen Importvorgangs ohne gestarteten Druck).
- **Dritter Druck derselben Variante** → braucht eine bewusste
  Owner-Entscheidung, bevor gedruckt wird.
- **Budget erschöpft oder absehbar knapp** → pausieren, Owner ausdrücklich
  um erweiterte Freigabe bitten – nie stillschweigend über das Limit hinaus
  drucken.
- Vor **jeder** druckenden Zelle muss die eigene Dateivalidierung + der
  eigene Import bereits abgeschlossen und protokolliert sein.

## 2. Phase 1 — Dateivalidierung + Import (kein Materialverbrauch)

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
| 9 | I-06 (`manifest.json` allein) | ☐ | ☐ |
| 10 | I-06 (kompletter Ordner) | ☐ | ☐ |
| 11 | I-07 | ☐ | ☐ |
| 12 | I-08 (vor Crop) | ☐ | ☐ |
| 13 | I-08 (nach Crop) | ☐ | ☐ |
| 14 | I-09 (Legacy) | ☐ | ☐ |
| 15 | I-09 (aktuell) | ☐ | ☐ |
| 16 | I-10 (normal) | ☐ | ☐ |
| 17 | I-10 (invertiert) | ☐ | ☐ |
| 18 | I-11 | ☐ | ☐ |
| 19 | I-12 | ☐ | ☐ |

## 3. Phase 2 — Vorschau-Verhalten geprüft, Budget-Startstand notiert

- [ ] Alle 19 Zeilen aus Phase 1 abgeschlossen; keine ungeklärten
      Sicherheits-/Fehlerfälle offen.
- [ ] „Nichts passiert"-Fälle (EM-S03, Spalte in §2) für alle Zeilen
      protokolliert, nicht nur bei „Ja" übersprungen.
- [ ] Budget-Startstand: **0 von 24** physischen Drucken verbraucht.

## 4. Phase 3 — Druck je Variante (12 Varianten, max. 24 Drucke gesamt)

Nur Zellen, die tatsächlich im Druckprotokoll (§3) stehen. Je Variante:
Budget prüfen → drucken → vermessen → Foto (EXIF/GPS geprüft, iCloud
abgelegt, SHA-256 + Pfad in Fotoreferenz-Spalte) → Druckprotokoll-Zeile
ausfüllen → Budget-Zähler fortschreiben. Bei Fehldruck: Abschnitt 1 dieser
Checkliste anwenden, **nicht** automatisch wiederholen.

**Kernaussage-Zeilen** (mindestens zweimal unabhängig drucken, siehe
`PROTOKOLL-VORLAGEN.md` §3): Nullpunkt/Grundfläche, monotoner Keil,
mm/DPI-Referenz, Gloss-Polarität. Welche der Varianten unten das im Einzelnen
sind, ist am Testtag anhand der Kategorien zuzuordnen – nicht vorab
festgelegt. Solange das Budget nicht überschritten wird, ist es am
einfachsten, grundsätzlich jede Variante zweimal zu drucken (12 × 2 = 24,
schöpft das freigegebene Budget genau aus).

| # | Variante | Lauf 1 | Lauf 2 | Fotoreferenz eingetragen | Druckprotokoll-Zeile ausgefüllt |
| --- | --- | --- | --- | --- | --- |
| 1 | I-02 | ☐ | ☐ | ☐ | ☐ |
| 2 | I-03 (8 Bit) | ☐ | ☐ | ☐ | ☐ |
| 3 | I-03 (16 Bit) | ☐ | ☐ | ☐ | ☐ |
| 4 | I-04 | ☐ | ☐ | ☐ | ☐ |
| 5 | I-05 (konsistent) | ☐ | ☐ | ☐ | ☐ |
| 6 | I-07 | ☐ | ☐ | ☐ | ☐ |
| 7 | I-08 (vor Crop) | ☐ | ☐ | ☐ | ☐ |
| 8 | I-08 (nach Crop) | ☐ | ☐ | ☐ | ☐ |
| 9 | I-10 (normal) | ☐ | ☐ | ☐ | ☐ |
| 10 | I-10 (invertiert) | ☐ | ☐ | ☐ | ☐ |
| 11 | I-11 | ☐ | ☐ | ☐ | ☐ |
| 12 | I-12 | ☐ | ☐ | ☐ | ☐ |

**Budget-Laufsumme:** Jede angekreuzte Lauf-1/Lauf-2-Zelle ist ein Druck.
Summe darf **24 nicht überschreiten**; bei 20/24 oder mehr die
Budget-Eskalation aus Abschnitt 1 dieser Checkliste prüfen, bevor
weitergedruckt wird.

## 5. Am Ende des Testtags

- [ ] Gerät in den vom Hersteller empfohlenen Ruhezustand versetzt, nicht
      einfach stromlos geschaltet.
- [ ] Alle Fotos aus Phase 3 gesichert (iCloud Drive, SHA-256 dokumentiert).
- [ ] Protokolltabellen in `EUFYMAKE-687-PROTOKOLL-VORLAGEN.md` mit den
      heutigen Einträgen aktualisiert und committed.
- [ ] Jede Aussage bereits jetzt oder spätestens beim Zusammenfassen in
      einen Vertrag als „Herstellerangabe", „Importbeobachtung" oder
      „Druckmessung" gekennzeichnet (#687-AC).
- [ ] Kurzer Ermüdungsfehler-Check: passen Anzahl bearbeiteter Zellen und
      Sorgfalt der Protokollierung zusammen? Falls nicht, betroffene Zeilen
      am nächsten Testtag erneut prüfen statt unklare Werte stehen zu
      lassen.
