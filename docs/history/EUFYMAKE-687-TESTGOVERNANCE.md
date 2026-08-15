# EufyMake-Hardware-Testgovernance – Entwurf (Issue #687)

> **Status: ENTWURF.** Dies ist ein Vorschlag zur Freigabe durch den
> Repo-Owner, **keine bereits entschiedene Policy**. Nichts in diesem
> Dokument gilt als verbindlich, bis es hier ausdrücklich als freigegeben
> markiert wird (siehe Abschnitt 4). Bis dahin sind die Vorschläge eine
> Diskussionsgrundlage für #688–#690, Epic
> [#681](https://github.com/NikolayDA/picture_helper/issues/681).

Die letzten beiden mit Hardware verknüpften Akzeptanzkriterien von #687
verlangen Abbruchkriterien für Materialverbrauch/Gerätebedienung sowie
geklärte Datenschutz-/Lizenz-/Ablagefragen für Testfotos. Beides braucht eine
Entscheidung des Repo-Owners (reale Kosten, reales Gerät, ggf. reale
Personen/Umgebung auf Fotos) und kann nicht allein durch Code oder Doku
„erledigt" werden – daher dieser Entwurf statt einer stillschweigend
gesetzten Policy.

## 1. Vorschlag: Abbruchkriterien Materialverbrauch

- **Gesamtbudget für die aktuelle Matrix:** Das
  [Druckprotokoll](EUFYMAKE-687-PROTOKOLL-VORLAGEN.md) hat 8 Tabellenzeilen,
  aber zwei davon vergleichen selbst zwei physische Varianten – I-08
  (vor/nach Crop) und I-10 (Gloss-Polarität normal/invertiert) – und
  brauchen damit unabhängig von einer Wiederholungsmessung mindestens zwei
  Drucke. Maßgeblich ist daher die Zahl der **druckbaren Varianten**, nicht
  der Tabellenzeilen: I-02, I-03 8-Bit, I-03 16-Bit, I-04, I-05 konsistent,
  I-07, I-08 vor Crop, I-08 nach Crop, I-10 normal, I-10 invertiert – **10
  Varianten**. Bei „Erst- + eine Wiederholungsmessung" je Variante (nächster
  Punkt) ergibt das ein hartes Limit von **maximal 20 physischen Drucken**
  für #688–#690 in der jetzigen Fassung der Matrix.
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
  Material, offensichtlich falsche Farbe/Größe) sofort abbrechen, Ursache im
  Importprotokoll vermerken, **nicht** automatisch wiederholen. Ein
  Fehldruck zählt gegen das Gesamtbudget, auch ohne verwertbare Messung.
- Klarlack/Weißtinte/Spezialtinten gelten als knappe Ressource: Gloss-Zellen
  (#690, I-10) nur mit dem in der Testmatrix vorgesehenen Mindestsatz an
  Kombinationen drucken, keine explorativen Zusatzdrucke ohne protokollierte
  Fragestellung.
- Ein Tagesbudget (Vorschlag: so viele Zellen wie an einem Tag mit
  Wiederholungsmessung realistisch nachvollziehbar bleiben) verhindert
  Ermüdungsfehler bei Messung/Protokollierung.
- **Budget-Eskalation:** Reicht das Gesamtbudget von 20 Drucken absehbar
  nicht (wiederholte Fehldrucke, neue Testzellen aus offenen Widersprüchen),
  pausieren und den Owner ausdrücklich um eine erweiterte Freigabe bitten,
  statt stillschweigend über das Limit hinaus zu drucken.

## 2. Vorschlag: Sichere Gerätebedienung

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
  Übertemperatur sofort abbrechen (Nothalt/Netzschalter), Vorfall im
  Importprotokoll dokumentieren, **keine** Testfortsetzung ohne Klärung der
  Ursache.
- Persönliche Schutzausrüstung gemäß Hersteller-/Tintenblatt (z. B. bei
  Reinigung, Tintenwechsel, Weißtinten-Underbase-Einstellung gemäß A12 im
  Annahmeninventar) verwenden.
- Kinder/Haustiere während laufender Drucke vom Gerät fernhalten.
- Nach Testende: Gerät in den vom Hersteller empfohlenen Ruhezustand
  versetzen, nicht einfach stromlos schalten, wenn ein regulärer
  Herunterfahrvorgang existiert.

## 3. Vorschlag: Datenschutz, Lizenz und Ablage für Testfotos

- **Keine personenbezogenen Daten im Bild:** Fotos so aufnehmen, dass keine
  Personen, Gesichter, Kennzeichen oder private Räume erkennbar
  mitfotografiert werden; Hintergrund neutral halten.
- **Metadaten:** Vor jeder Weitergabe/Referenzierung EXIF-Daten prüfen und
  bei Bedarf entfernen – insbesondere GPS-Standortdaten aus
  Smartphone-Fotos, die sonst den Testort (z. B. Wohnadresse) preisgeben
  können. Gilt auch für kuratierte Ausschnitte, die in `docs/history/`
  landen.
- **Ablageort:** Rohfotos **nicht** direkt ins Git-Repository (Bildbinärdaten
  blähen die Historie dauerhaft auf). Ablage in **iCloud Drive** des
  Repo-Owners, in einem eigenen, nicht geteilten Ordner (Vorschlag:
  `iCloud Drive/BgRemover-EufyMake-Testfotos/<Issue>/<Testzelle>/`, z. B.
  `.../688-height/I-03-8bit/`); je Datei SHA-256 bilden und zusammen mit dem
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

Dieser Abschnitt bleibt leer, bis der Repo-Owner die Vorschläge oben
bestätigt oder ändert. Vorschlag für den Freigabe-Vermerk:

```
Freigegeben von: <Name/GitHub-Handle>
Datum:
Geänderte Punkte gegenüber dem Entwurf:
```

Bis zu einer Freigabe gelten die Realtests aus #688–#690 nicht als bezüglich
Materialverbrauch/Gerätesicherheit/Datenschutz governance-konform – dieses
Dokument macht nur den Vorschlag sichtbar und versionierbar, ersetzt aber
keine Owner-Entscheidung.
