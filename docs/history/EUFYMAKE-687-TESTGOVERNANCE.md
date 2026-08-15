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

- Je Testzelle (I-01…I-10, siehe
  [Protokollvorlagen](EUFYMAKE-687-PROTOKOLL-VORLAGEN.md)) maximal **zwei**
  physische Drucke einplanen (Erst- + eine Wiederholungsmessung); ein dritter
  Druck derselben Zelle braucht eine bewusste Owner-Entscheidung.
- Vor jeder druckenden Zelle zuerst die materialsparenden Import-only-Zellen
  (Dateivalidierung + Importprotokoll) vollständig abschließen – ein Druck
  startet nie ohne bereits protokollierten, plausiblen Import.
- Bei sichtbar fehlgeschlagenem Druck (Papier-/Substratstau, falsches
  Material, offensichtlich falsche Farbe/Größe) sofort abbrechen, Ursache im
  Importprotokoll vermerken, **nicht** automatisch wiederholen.
- Klarlack/Weißtinte/Spezialtinten gelten als knappe Ressource: Gloss-Zellen
  (#690) nur mit dem in der Testmatrix vorgesehenen Mindestsatz an
  Kombinationen drucken, keine explorativen Zusatzdrucke ohne protokollierte
  Fragestellung.
- Ein Tagesbudget (Vorschlag: so viele Zellen wie an einem Tag mit
  Wiederholungsmessung realistisch nachvollziehbar bleiben) verhindert
  Ermüdungsfehler bei Messung/Protokollierung.

## 2. Vorschlag: Sichere Gerätebedienung

- Herstellerhandbuch/Sicherheitshinweise des eufyMake E1 vor dem ersten Test
  lesen und griffbereit halten; dieses Dokument ersetzt sie nicht.
- Gerät während eines laufenden Druck-/Importvorgangs nicht unbeaufsichtigt
  lassen.
- Bei Fehlercode, ungewöhnlichem Geräusch, Geruch oder sichtbarer
  Übertemperatur sofort abbrechen (Nothalt/Netzschalter), Vorfall im
  Importprotokoll dokumentieren, **keine** Testfortsetzung ohne Klärung der
  Ursache.
- Persönliche Schutzausrüstung gemäß Hersteller-/Tintenblatt (z. B. bei
  Reinigung, Tintenwechsel) verwenden.
- Kinder/Haustiere während laufender Drucke vom Gerät fernhalten.
- Nach Testende: Gerät in den vom Hersteller empfohlenen Ruhezustand
  versetzen, nicht einfach stromlos schalten, wenn ein regulärer
  Herunterfahrvorgang existiert.

## 3. Vorschlag: Datenschutz, Lizenz und Ablage für Testfotos

- **Keine personenbezogenen Daten im Bild:** Fotos so aufnehmen, dass keine
  Personen, Gesichter, Kennzeichen oder private Räume erkennbar
  mitfotografiert werden; Hintergrund neutral halten.
- **Ablageort:** Rohfotos **nicht** direkt ins Git-Repository (Bildbinärdaten
  blähen die Historie dauerhaft auf). Vorschlag: separate, nicht-öffentliche
  Ablage (z. B. privates Cloud-Verzeichnis des Repo-Owners) plus SHA-256 und
  Verweis im jeweiligen Protokoll; nur kuratierte, für die Dokumentation
  nötige Ausschnitte werden bei Bedarf verkleinert/beschnitten in
  `docs/history/` referenziert.
- **Herstellerantworten (E-Mail an `support@eufymake.com`, siehe
  Annahmeninventar):** Zitate auf das für die Dokumentation nötige Minimum
  beschränken, keine vollständigen E-Mail-Header/Kontaktdaten des
  Antwortenden veröffentlichen.
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
