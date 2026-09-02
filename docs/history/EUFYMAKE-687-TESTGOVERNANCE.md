# EufyMake-Hardware-Testgovernance (Issue #687)

> **Status: FREIGEGEBEN** (siehe Abschnitt 4, 2026-08-15). Die Regeln unten
> sind damit verbindlich für die Realtests aus #688–#690, Epic
> [#681](https://github.com/NikolayDA/picture_helper/issues/681). Für den
> Testtag selbst siehe die daraus abgeleitete
> [`EUFYMAKE-687-DRUCK-CHECKLISTE.md`](EUFYMAKE-687-DRUCK-CHECKLISTE.md).

Die letzten beiden mit Hardware verknüpften Akzeptanzkriterien von #687
verlangen Abbruchkriterien für Materialverbrauch/Gerätebedienung sowie
geklärte Datenschutz-/Lizenz-/Ablagefragen für Testfotos. Beides braucht eine
Entscheidung des Repo-Owners (reale Kosten, reales Gerät, ggf. reale
Personen/Umgebung auf Fotos) und konnte nicht allein durch Code oder Doku
„erledigt" werden – daher zunächst ein Entwurf statt einer stillschweigend
gesetzten Policy, jetzt mit expliziter Freigabe (Abschnitt 4).

## 1. Abbruchkriterien Materialverbrauch (verbindlich)

- **Gesamtbudget für die aktuelle Matrix:** Das
  [Druckprotokoll](EUFYMAKE-687-PROTOKOLL-VORLAGEN.md) hat 12 Tabellenzeilen,
  je eine physisch zu druckende Variante: I-02, I-03 8-Bit, I-03 16-Bit,
  I-04, I-05 konsistent, I-07, I-08 vor Crop, I-08 nach Crop, I-10 normal,
  I-10 invertiert, I-11 (Treppenkeil, H-02) und I-13 (Alpha/Coverage bei
  nicht-null HEIGHT) – **12 Varianten**. I-02 ist dabei zugleich die
  druckbare 256×256-Referenz für den H-03-Vergleich mit I-04
  (128×128 bei gleicher Seitenrelation). I-12 bleibt als abgeschlossener
  Import-Negativtest erhalten, ist nach der ausdrücklichen Ablehnung durch
  Studio aber **import-only** und besitzt keine druckbare Variante. I-08
  und I-10 vergleichen dabei inhaltlich je zwei
  Ausprägungen (vor/nach Crop bzw. normal/invertiert), stehen aber bereits
  als zwei getrennte Tabellenzeilen mit je eigener Wiederholungsmessung im
  Druckprotokoll – Zeilenzahl und Variantenzahl sind hier deckungsgleich.
  Zusätzlich sind für #690 **elf Gloss-Läufe** fest eingeplant: G-01 einmal,
  G-02 normal und invertiert jeweils zweimal sowie G-03, G-04a/b/c, G-05,
  G-06, G-07 und G-08 jeweils einmal. Das freigegebene harte Limit beträgt
  als hartes Limit weiterhin **maximal 35 physische Drucke** für #688–#690.
  Nach je einem Erstlauf der 12 Stammvarianten und den elf fest eingeplanten
  Gloss-Läufen bleiben die zuvor freigegebenen höchstens elf Wiederholungen
  für die Stammvarianten; die Kernaussagen aus dem Druckprotokoll haben
  Vorrang. Der aktuelle Plan umfasst damit höchstens 34 Drucke. Der durch den
  Wegfall von I-12 rechnerisch freie 35. Platz bleibt unzugeordnet und ist
  weder für eine neue Variante noch für eine zwölfte Wiederholung automatisch
  freigegeben. Ein zweiter Lauf jeder einzelnen Variante ist auch mit dem
  erhöhten harten Limit nicht automatisch freigegeben.
- Erweitert sich die Matrix später (neue Testzellen aus offenen
  Widersprüchen), ist die daraus rechnerisch folgende neue Zahl nur ein
  **Vorschlag** – kein automatisches Zusatzbudget. Neue Zellen lösen immer
  die Budget-Eskalation unten aus: erst pausieren und die
  Owner-Bestätigung einholen, bevor über das zuletzt freigegebene Limit
  hinaus gedruckt wird.
- Je Variante maximal **zwei** physische Drucke einplanen (Erst- + eine
  Wiederholungsmessung); ein dritter Druck derselben Variante braucht eine
  bewusste Owner-Entscheidung **und** zählt gegen das Gesamtbudget oben.
- Vor jeder druckenden Zelle zuerst die materialsparenden Import-only-Zellen
  (Dateivalidierung + Importprotokoll) vollständig abschließen – ein Druck
  startet nie ohne bereits protokollierten, plausiblen Import.
- Bei sichtbar fehlgeschlagenem Druck (Papier-/Substratstau, falsches
  Material, offensichtlich falsche Farbe/Größe) sofort abbrechen, Ursache in
  der Zeile der betroffenen Variante im **Druckprotokoll** vermerken (nicht
  im Importprotokoll – der Vorfall passiert beim Druck, nicht beim Import,
  und muss dem physischen Lauf zuordenbar bleiben, der das Budget belastet),
  **nicht** automatisch wiederholen. Ein Fehldruck zählt gegen das
  Gesamtbudget, auch ohne verwertbare Messung.
- Klarlack/Weißtinte/Spezialtinten gelten als knappe Ressource: Gloss-Zellen
  (#690, I-10) nur mit dem in der Testmatrix vorgesehenen Mindestsatz an
  Kombinationen drucken, keine explorativen Zusatzdrucke ohne protokollierte
  Fragestellung.
- Ein Tagesbudget (Richtwert: so viele Zellen wie an einem Tag mit
  Wiederholungsmessung realistisch nachvollziehbar bleiben – bewusst kein
  fixer Zahlenwert, sondern nach eigenem Ermessen am Testtag zu bestimmen)
  verhindert Ermüdungsfehler bei Messung/Protokollierung.
- **Budget-Eskalation:** Reicht das Gesamtbudget von 35 Drucken absehbar
  nicht (wiederholte Fehldrucke, neue Testzellen aus offenen Widersprüchen),
  pausieren und den Owner ausdrücklich um eine erweiterte Freigabe bitten,
  statt stillschweigend über das Limit hinaus zu drucken.

## 2. Sichere Gerätebedienung (verbindlich)

- Herstellerhandbuch/Sicherheitshinweise des eufyMake E1 vor dem ersten Test
  lesen und griffbereit halten; dieses Dokument ersetzt sie nicht.
- **UV-Belichtung:** Der E1 ist laut Herstellerquellen (A1/A15 im
  [Annahmeninventar](EUFYMAKE-687-ANNAHMENINVENTAR.md)) ein UV-Drucker mit
  UV-Härtungslampe. Nicht direkt in Lampe/Druckkopf blicken, auch nicht
  längere Zeit durch ein Sichtfenster; bei Wartungs-/Reinigungsarbeiten am
  Druckkopf Herstellerangaben zur Lampenabschaltung beachten. Haut-/
  Augenkontakt mit unausgehärteter UV-Tinte vermeiden.
- Für ausreichende Belüftung des Raums während Druck-/Härtungsvorgängen
  sorgen (Tinten-/Härtungsdämpfe); eine dokumentierte Hersteller-Empfehlung
  zu Raumgröße/Lüftung vor dem ersten Test prüfen, falls vorhanden.
- Gerät während eines laufenden Druck-/Importvorgangs nicht unbeaufsichtigt
  lassen.
- Bei Fehlercode, ungewöhnlichem Geräusch, Geruch oder sichtbarer
  Übertemperatur sofort abbrechen (Nothalt/Netzschalter). Vorfall dort
  dokumentieren, wo er auftritt: während eines laufenden Druckvorgangs in
  der Zeile der betroffenen Variante im **Druckprotokoll** (mit Verweis auf
  den Import, falls relevant), während eines reinen Importvorgangs ohne
  bereits gestarteten Druck im Importprotokoll. **Keine** Testfortsetzung
  ohne Klärung der Ursache.
- Persönliche Schutzausrüstung gemäß Hersteller-/Tintenblatt (z. B. bei
  Reinigung, Tintenwechsel, Weißtinten-Underbase-Einstellung gemäß A12 im
  Annahmeninventar) verwenden.
- Kinder/Haustiere während laufender Drucke vom Gerät fernhalten.
- Nach Testende: Gerät in den vom Hersteller empfohlenen Ruhezustand
  versetzen, nicht einfach stromlos schalten, wenn ein regulärer
  Herunterfahrvorgang existiert.

## 3. Datenschutz, Lizenz und Ablage für Testfotos (verbindlich)

- **Keine personenbezogenen Daten im Bild:** Fotos so aufnehmen, dass keine
  Personen, Gesichter, Kennzeichen oder private Räume erkennbar
  mitfotografiert werden; Hintergrund neutral halten.
- **Metadaten:** Vor jeder Weitergabe/Referenzierung EXIF-Daten prüfen und
  bei Bedarf entfernen – insbesondere GPS-Standortdaten aus
  Smartphone-Fotos, die sonst den Testort (z. B. Wohnadresse) preisgeben
  können. Gilt auch für kuratierte Ausschnitte, die in `docs/history/`
  landen.
- **Ablageort:** Rohfotos **nicht** direkt ins Git-Repository (Bildbinärdaten
  blähen die Historie dauerhaft auf). Verbindlich ist **iCloud Drive** des
  Repo-Owners, in einem eigenen, nicht geteilten Ordner; die konkrete
  Ordnerbenennung ist frei wählbar, Beispielkonvention:
  `iCloud Drive/BgRemover-EufyMake-Testfotos/<Issue>/<Testzelle>/`, z. B.
  `.../688-height/I-03-8bit/`. Je Datei SHA-256 bilden und zusammen mit dem
  iCloud-Pfad (kein öffentlicher Freigabelink) in der Spalte
  „Fotoreferenz" des jeweiligen Protokolls eintragen. Nur kuratierte, für
  die Dokumentation nötige Ausschnitte werden bei Bedarf verkleinert/
  beschnitten in `docs/history/` referenziert.
- **Herstellerantworten (E-Mail an `support@eufymake.com`, siehe
  Annahmeninventar):** Zitate auf das für die Dokumentation nötige Minimum
  beschränken, keine vollständigen E-Mail-Header/Kontaktdaten – weder des
  Antwortenden noch der eigenen Absenderadresse des Repo-Owners.
- **Lizenz:** Eigene Testfotos/-videos stehen zur Aufnahme in
  `docs/history/` unter derselben Projektlizenz
  (GPL-3.0-or-later, siehe `LICENSES.md`) zur Verfügung, sofern sie kein
  Material Dritter (Herstellerlogos in Nahaufnahme, fremde Screenshots ohne
  Freigabe) unkommentiert enthalten.
- **Aufbewahrungsdauer:** Rohfotos mindestens bis zum formalen Abschluss von
  #688–#690 aufbewahren (Nachvollziehbarkeit bei Rückfragen); danach liegt
  die weitere Aufbewahrung im Ermessen des Repo-Owners.

## 4. Freigabe

```
Freigegeben von: NikolayDA
Datum: 2026-08-15 (ursprüngliche Freigabe)
Aktualisiert: 2026-08-15 – Testmatrix um I-11 (H-02, Treppenkeil-Druck) und
  I-12 (H-03, Seitenverhältnis) erweitert, nachdem sich zeigte, dass die
  ursprünglich freigegebene 10-Varianten-Matrix zwei im Annahmeninventar als
  offen markierte #688-Fragen (H-02/H-03) noch keiner Testzelle zugeordnet
  hatte. Gesamtbudget entsprechend von 20 auf 24 physische Drucke erhöht
  (12 Varianten × max. 2). UV-Sicherheitshinweise und iCloud-Drive-Ablage
  (Abschnitte 2–3) unverändert gegenüber der ursprünglichen Freigabe.
Aktualisiert: 2026-09-02 – I-13 für Alpha/Coverage bei nicht-null HEIGHT
  ergänzt, I-02 auf ein dimensionsgleiches COLOR/HEIGHT-Paar umgestellt und
  I-08 mit einem pixelgenauen COLOR/HEIGHT-Registrierungspaar abgesichert.
  Das Gesamtbudget bleibt unverändert bei 24 Drucken; nach 13
  Erstläufen werden Wiederholungen auf die Kernaussagen priorisiert. Es ist
  kein zusätzlicher Materialverbrauch über die bisherige Freigabe hinaus
  freigegeben.
Aktualisiert: 2026-09-02 – Owner-Entscheidung von NikolayDA: Gesamtbudget von
  24 auf 35 physische Drucke erhöht. Die elf zusätzlichen Plätze 25–35 sind
  ausschließlich dem #690-Mindestsatz G-01 bis G-08 zugeordnet; G-02 normal
  und invertiert erhalten je zwei unabhängige Läufe. Die elf bisherigen
  Wiederholungsplätze der 13 Stammvarianten bleiben erhalten. Fehldrucke
  zählen mit; Lauf 36 oder jede Umwidmung eines Gloss-Platzes braucht eine
  neue ausdrückliche Owner-Freigabe. Alle HEIGHT-/Gloss-Preflights und
  Sicherheits-Abbruchkriterien bleiben unverändert verbindlich.
Aktualisiert: 2026-09-03 – I-12 nach der expliziten Studio-Ablehnung als
  abgeschlossener Import-Negativtest und nicht druckbare Zelle eingestuft.
  Die physische Stammvariantenmatrix enthält dadurch 12 statt 13 Zeilen;
  I-02 (256×256) und I-04 (128×128 bei gleicher Seitenrelation) bilden das
  ausführbare physische H-03-Vergleichspaar. Das harte Limit von 35 bleibt
  bestehen, der ausführbare und freigegebene Plan umfasst jedoch höchstens
  12 Erstläufe + 11 Wiederholungen + 11 Gloss-Läufe = 34 Drucke. Der freie
  Platz darf ohne neue Owner-Freigabe nicht umgewidmet werden.
```

Damit gelten die Regeln aus den Abschnitten 1–3 für die Realtests aus
#688–#690 als bezüglich Materialverbrauch/Gerätesicherheit/Datenschutz
governance-konform. Eine inhaltliche Änderung der Regeln (z. B. bei
Erweiterung der Testmatrix, siehe Budget-Eskalation in Abschnitt 1) braucht
erneut eine explizite Owner-Entscheidung und einen aktualisierten
Freigabe-Vermerk hier.
