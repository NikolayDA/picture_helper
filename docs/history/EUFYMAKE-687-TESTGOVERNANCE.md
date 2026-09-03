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
  [Druckprotokoll](EUFYMAKE-687-PROTOKOLL-VORLAGEN.md) hat 13 Tabellenzeilen,
  je eine physisch zu druckende Variante: I-02, I-03 8-Bit, I-03 16-Bit,
  I-04, I-05 konsistent, I-07, I-08 vor Crop, I-08 nach Crop, I-10 normal,
  I-10 invertiert, I-11 (Treppenkeil, H-02), I-13 (Alpha/Coverage bei
  nicht-null HEIGHT) und I-14 (direktes Kanten-/Impuls-Kontrollpaar) –
  **13 Varianten**. I-02 (256×256) und I-04
  (128×128 bei gleicher Seitenrelation) bilden dabei das druckbare
  kombinierte Pixelgrößen-/Resampling-End-to-End-Paar. I-04 wurde bereits bei
  der Fixture-Erzeugung über den HEIGHT-Pfad mit float32-Zwischenpräzision,
  LANCZOS sowie `rint` und Clamp verkleinert; der spätere Vergleich kann die
  Studio-Filterung daher nicht isolieren. I-14 verwendet dagegen die direkt
  aus derselben normierten Formel erzeugten 256×256- und 128×128-Fixtures
  `height_impulse_edge_16bit.png` und
  `height_impulse_edge_direct_half_16bit.png`; kein Fixture wurde aus dem
  anderen resampled. Damit ist eine Vorfilterung durch den Generator als
  Störvariable ausgeschlossen. Beide verwenden nur den normierten Wertebereich
  1/4…3/4; ihr unteres Viertel enthält 4096 feine 16-Bit-Sollstufen. Dadurch
  werden neben Filterung auch Vollbereichsnormalisierung und zusätzliche
  16-Bit-Präzision beobachtbar. Ohne zugängliches Studio-Ausgaberaster bleibt
  eine physische Differenz trotzdem dem kombinierten Studio-/Druckpfad
  zuzurechnen, nicht Studio allein. I-12 bleibt als abgeschlossener H-03-
  Import-Negativtest erhalten, ist nach der ausdrücklichen Ablehnung durch
  Studio aber **import-only** und besitzt keine druckbare Variante. Das
  I-02/I-04-Paar liefert keine Evidenz für den abgelehnten 2:1-Fall. I-08
  und I-10 vergleichen dabei inhaltlich je zwei
  Ausprägungen (vor/nach Crop bzw. normal/invertiert), stehen aber bereits
  als zwei getrennte Tabellenzeilen mit je eigener Wiederholungsmessung im
  Druckprotokoll – Zeilenzahl und Variantenzahl sind hier deckungsgleich.
  Zusätzlich sind für #690 **elf Gloss-Läufe** fest eingeplant: G-01 einmal,
  G-02 normal und invertiert jeweils zweimal sowie G-03, G-04a/b/c, G-05,
  G-06, G-07 und G-08 jeweils einmal. Das freigegebene harte Limit beträgt
  als hartes Limit weiterhin **maximal 35 physische Drucke** für #688–#690.
  Nach je einem Erstlauf der 13 Stammvarianten und den elf fest eingeplanten
  Gloss-Läufen bleiben die zuvor freigegebenen höchstens elf Wiederholungen
  für die Stammvarianten; die Kernaussagen aus dem Druckprotokoll haben
  Vorrang. Der aktuelle Plan umfasst damit höchstens 35 Drucke. Im für die
  Stammvarianten vorgesehenen Bereich 1–24 ist **Budgetplatz 24** durch die
  Owner-Freigabe vom 2026-09-03 I-14 zugeordnet; die Gloss-Plätze 25–35 bleiben
  unverändert belegt. Ein zweiter Lauf jeder einzelnen Variante ist auch mit dem
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
  I-12 besitzt keine physische Messzeile. I-02 (256×256) und I-04
  (128×128 bei gleicher Seitenrelation) bleiben als getrennter druckbarer,
  kombinierter Pixelgrößen-/Resampling-End-to-End-Vergleich erhalten. Weil
  I-04 bereits im Fixture-Generator per LANCZOS verkleinert und gerundet wird,
  darf das Ergebnis weder als isolierte Studio-Filterwirkung noch als
  physische Evidenz für den abgelehnten 2:1-Fall gewertet werden. Das harte
  Limit von 35 bleibt
  bestehen, der ausführbare und freigegebene Plan umfasst jedoch höchstens
  12 Erstläufe + 11 Wiederholungen + 11 Gloss-Läufe = 34 Drucke. Budgetplatz
  24 bleibt frei und darf ohne neue Owner-Freigabe nicht umgewidmet werden;
  Platz 35 bleibt G-08 zugeordnet.
Aktualisiert: 2026-09-03 – NikolayDA hat mit dem Auftrag, die zwei
  vorgeschlagenen Punkte vollständig umzusetzen, die Zuordnung des zuvor
  freien Budgetplatzes 24 zu I-14 bestätigt. I-14 ergänzt ein direkt
  erzeugtes, nicht vorgefiltertes 256×256-/128×128-Kanten-/Impuls-Paar; beide
  Dateien wurden in Studio 4.2.2 ohne Warnung nativ als HEIGHT akzeptiert und
  bei identischer Objektgröße von 90,31×90,31 mm vorgeprüft. Das harte Limit
  bleibt 35: 13 Erstläufe + höchstens 11 priorisierte Wiederholungen + 11
  Gloss-Läufe = 35. Es gibt keinen unzugeordneten Materialplatz mehr. Die
  physische I-14-Auswertung misst den kombinierten Studio-/Druckpfad; ohne
  zugängliches Studio-Ausgaberaster darf sie nicht als Studio-only-Befund
  bezeichnet werden.
```

Damit gelten die Regeln aus den Abschnitten 1–3 für die Realtests aus
#688–#690 als bezüglich Materialverbrauch/Gerätesicherheit/Datenschutz
governance-konform. Eine inhaltliche Änderung der Regeln (z. B. bei
Erweiterung der Testmatrix, siehe Budget-Eskalation in Abschnitt 1) braucht
erneut eine explizite Owner-Entscheidung und einen aktualisierten
Freigabe-Vermerk hier.

## 5. Vorbereiteter Nachtrag vom 2026-09-03 (Owner-Freigabe ausstehend)

Dieser Abschnitt ist ein **Vorschlag** aus der Qualitätsprüfung des Epics
#681 vor den Testdrucken. Er wird erst mit einem Freigabe-Vermerk in
Abschnitt 4 verbindlich; bis dahin gelten die Abschnitte 1–3 unverändert.
Die zugehörigen Ablaufschritte stehen bereits in
[`EUFYMAKE-687-DRUCK-CHECKLISTE.md`](EUFYMAKE-687-DRUCK-CHECKLISTE.md)
(§0 und Phase 2b), die Felder in
[`EUFYMAKE-687-PROTOKOLL-VORLAGEN.md`](EUFYMAKE-687-PROTOKOLL-VORLAGEN.md)
(§3.0 und §3.1).

### 5.1 Voraussetzungen vor Phase 3 (Ergänzung zu Abschnitt 1)

- Ein Druck startet erst, wenn Firmware-Version, Gerätewarnungen (Scraper,
  Luftfilter, Tinte) samt Tintenständen, Substrat, Messmittel je Messgröße
  und die festen Laufparameter in Protokoll §3.0 eingetragen sind.
- Die Vorschau (`Preview`) jeder Druckvariante wird vor dem ersten Druck ohne
  `Print` geöffnet und in Protokoll §3.1 protokolliert. Ein von der Vorschau
  ausgelöster Gerätevorgang verbraucht kein Material und zählt nicht gegen
  das Budget, wird aber nur nach ausdrücklicher Owner-Freigabe ausgelöst.
- Der Tintenbedarf wird vor dem ersten Druck gegen die Tintenstände geprüft.
  Planungsannahme, solange Studio keine Schätzung anzeigt: rund 10 ml je
  90-mm-Keil und bis rund 20 ml je Vollfläche bei 2,50 mm Texturhöhe, ohne
  Underbase. Reicht der Vorrat absehbar nicht für die 13 Erstläufe, greift
  die Budget-Eskalation aus Abschnitt 1 vor dem Druck.
- Ohne Profilmessmittel wird I-14 nicht gedruckt; ohne die vorab festgelegte
  Auswertungsregel wird der I-03-Vergleich nicht gedruckt
  (`EUFYMAKE-688-HEIGHT-VERTRAG.md` §4.0).

### 5.2 Screenshots und Studio-Projekte (Ergänzung zu Abschnitt 3)

- Screenshots aus Studio und je Zelle gespeicherte Studio-Projekte gelten
  als Rohartefakte wie Testfotos: Ablage im nicht geteilten iCloud-Ordner
  unter `…/<Issue>/<Zelle>/studio/`, SHA-256 je Datei, Referenz in der
  Spalte „Screenshot-Referenz" des Importprotokolls bzw. in Protokoll §3.1.
- Konto- oder Nutzernamen und E-Mail-Adressen in Studio-Fenstern werden vor
  der Ablage abgedeckt oder beschnitten; die Metadaten-, Lizenz- und
  Aufbewahrungsregeln aus Abschnitt 3 gelten unverändert.

### 5.3 Owner-Entscheidung I-10 gegen G-02

I-10 normal/invertiert und G-02 verwenden dieselben Dateien
(`gloss_wedge.png`, `gloss_wedge_inverted.png`) über denselben Gloss-Pfad;
der bisherige Plan druckte jede Richtung dreimal. Vor dem ersten Gloss-Druck
ist zu entscheiden:

- **Option A (empfohlen):** I-10 physisch streichen. Die Polarität liefert
  G-02 mit je zwei unabhängigen Läufen je Richtung. Die Plätze 9–10 der
  Stammvarianten bleiben unzugeordnet und werden ohne neue Owner-Freigabe
  nicht umgewidmet; die physische Matrix umfasst dann 11 Stammvarianten.
- **Option B:** I-10 dem in `EUFYMAKE-690-GLOSS-VERTRAG.md` §6.1
  dokumentierten Spot-UV-Zweipass (Pfad 2) zuordnen und G-02 **fest** dem
  nativen `Gloss Varnish`-Pfad (Pfad 1), um Zweipass und nativen Pfad zu
  vergleichen (GL-02). Die Pfadwahl je Reihe wird in Protokoll §3.0
  festgeschrieben; ohne diese Bindung wären beide Zellen erneut redundant.
  Die Registrierung zwischen den Durchgängen wird über die G-08-Marken
  protokolliert.

Beide Optionen lassen das harte Limit von 35 Drucken unverändert. Bis zur
Entscheidung bleiben die Zeilen 9–10 gesperrt. Diese Sperre wirkt bis zur
Freigabe ausschließlich als Voraussetzung in §0 der Druck-Checkliste, die vor
Phase 3 erledigt sein muss; Abschnitt 1 dieser Governance bleibt bis dahin
unverändert und führt I-10 formal in der 13-Varianten-Matrix. Erst der
Freigabe-Vermerk in Abschnitt 4 macht die Entscheidung Teil der verbindlichen
Regeln.

### 5.4 Gloss-Ebene bei I-08 nach Crop

Die separate Gloss-Ebene bleibt unbeschnitten und unverschoben; die
Registrierung wird nur in der Überlappung mit dem beschnittenen
COLOR/HEIGHT-Objekt bewertet (Regel in `EUFYMAKE-689-MM-DPI-VERTRAG.md`).
Das ist Testdesign, keine Budgetänderung, und hier nur zur Vollständigkeit
verlinkt.

Vorbereiteter Freigabe-Vermerk für Abschnitt 4 (erst nach Entscheidung
übernehmen):

```
Aktualisiert: (Datum) – Owner-Entscheidung von NikolayDA: Nachtrag 5.1–5.2
  übernommen (Voraussetzungen vor Phase 3, Screenshots/Studio-Projekte als
  Rohartefakte); I-10/G-02 nach Option (A|B) – bei B: I-10 Zweipass, G-02
  fest nativ; Gloss-Ebene bei I-08 nach Crop bleibt unverändert. Hartes Limit
  weiterhin 35 Drucke.
```
