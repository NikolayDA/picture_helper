# ADR (2026-06-22): EufyMake-Exportpaket-Konvention

Kurz-ADR zu #352 („Export-Datenmodell & Paketdefinition (Qt-frei) +
Konventions-ADR") im Epic #351 („Konsistentes EufyMake-Exportpaket").
Status: **beschlossen, Implementierung folgt** (#352–#355).

## Kontext

BgRemover kann Projekte inzwischen als mehrschichtige `.bgrproj`-Dateien
speichern: Farbmotiv, Höhenkarte und eine optionale Gloss-/Klarlackmaske sind
als Ebenenrollen modelliert. Für den nächsten Roadmap-Schritt soll daraus ein
konsistentes Paket für EufyMake Studio entstehen. Issue #352 fordert dafür
zuerst die Konvention, damit das spätere Qt-freie Exportmodul deterministisch
planen kann und UI, Rendering sowie Konsistenzprüfung dieselben Begriffe nutzen.

Die recherchierte EufyMake-E1-Konvention ist zum ADR-Zeitpunkt nicht vollständig
öffentlich und stabil genug belegt, um ein natives Studio-Projektformat
festzuschreiben. Daher dokumentiert diese Entscheidung eine konservative,
importorientierte Paketkonvention: verlustfreie Bild-Assets mit klaren Rollen,
Metadaten und bewusst markierten offenen Punkten. So bleibt die spätere Korrektur
lokal im Exportmodul, falls EufyMake Studio eine strengere Namens-, Container-
oder Manifest-Konvention verlangt.

## Entscheidung

1. **Paketumfang:** BgRemover erzeugt zunächst ein Import-Asset-Paket für
   EufyMake Studio, kein natives `.empf`-/Studio-Projekt. Das Paket kann als
   Ordner oder ZIP-Container repräsentiert werden; die logische Struktur bleibt
   identisch und wird im Exportplan beschrieben.
2. **Rollenabbildung:** `LayerRole.COLOR_MOTIF` wird zum Farbmotiv,
   `LayerRole.HEIGHT_MAP` zur Höhen-Graustufe und `LayerRole.GLOSS_MASK` zur
   optionalen Gloss-/Klarlackmaske. Andere Ebenenrollen sind nicht Teil des
   EufyMake-Pakets.
3. **Dateikonvention:** Die kanonischen Asset-Namen sind
   `color_motif.png`, `height_map.png` und optional `gloss_mask.png`. Ein
   optionales Manifest `manifest.json` darf dieselben Assets, Projektgröße,
   DPI/Auflösung, Bittiefe und Annahmen maschinenlesbar wiederholen, ist aber
   nicht Voraussetzung für den ersten Render-/Schreibschritt.
4. **Bildformate:** Alle Assets werden verlustfrei geplant. Das Farbmotiv ist
   ein PNG mit Alpha (`RGBA`). Die Höhenkarte ist ein Graustufen-PNG, bei dem
   **hell = hoch** und **dunkel = niedrig** gilt. Die Gloss-Maske ist ein
   Graustufen-PNG; bis zur Bestätigung durch EufyMake-Doku/Studio-Beispiele gilt
   **hell = mehr Glanz/Klarlack** als dokumentierte Annahme.
5. **Parameterableitung:** Physische Zielgröße wird aus
   `META_PHYSICAL_SIZE_MM` gelesen, sofern vorhanden; sonst bleibt sie
   unbekannt. DPI/Auflösung werden aus Projektpixelgröße plus physischer Größe
   abgeleitet, wenn beide Angaben vorliegen. `META_BIT_DEPTH` steuert die
   geplante Bittiefe; Standard ist 8 Bit pro Kanal. Ein 16-Bit-Hook bleibt im
   Datenmodell vorgesehen, wird aber nicht als bestätigte EufyMake-Anforderung
   behauptet.
6. **Qt-freie Planungslogik:** #352 führt ein strikt getyptes Modul
   `bgremover/eufymake_export.py` ein, das nur Domänenobjekte/DTOs wie
   `ExportPlan` und `ExportAsset` definiert und befüllt. Rendering, atomisches
   Schreiben, UI und allgemeine Preflight-Prüfung bleiben den Folge-Issues
   #353–#355 vorbehalten.
7. **Konfigurierbarkeit:** Pakettyp, Dateinamen und optionale Manifestfelder
   werden nicht tief in UI oder Renderer eingebrannt. Änderungen an einer später
   bestätigten EufyMake-Konvention sollen im Exportmodul und seinen Tests
   vorgenommen werden können, ohne das Projektmodell zu ändern.

## Offene Punkte

- Ob EufyMake Studio ein natives `.empf`-Projektformat importieren oder erzeugen
  muss, bleibt offen und ist ausdrücklich **nicht** Teil des ersten Pakets.
- Ob Höhenkarten in EufyMake E1 16 Bit statt 8 Bit erwarten oder davon
  profitieren, bleibt offen; der Exportplan hält die Bittiefe trotzdem explizit.
- Die genaue Gloss-Semantik (binär oder Intensität; Weiß/Schwarz-Zuordnung) muss
  anhand belastbarer Studio-Beispiele oder Herstellerdokumentation bestätigt
  werden.
- Falls EufyMake Studio ein verbindliches Manifest oder feste Ordnernamen
  verlangt, ersetzt diese bestätigte Konvention die hier genannten
  importorientierten Defaults.

## Konsequenzen

- #352 kann mit einem kleinen, testbaren Datenmodell starten und muss keine Qt-,
  Rendering- oder Schreiblogik enthalten.
- #353 rendert gegen denselben `ExportPlan` und kann atomares Schreiben später
  für Ordner oder ZIP implementieren.
- #354 prüft fehlende Rollen, uneinheitliche Größen, unklare Bittiefe und offene
  Annahmen gegen dieselbe Konvention.
- #355 zeigt dieselben Rollen und Annahmen in der UI an, ohne eigene
  Dateinamenslogik zu duplizieren.
- Die ADR macht bewusst kenntlich, welche Aussagen bestätigt sind
  (BgRemover-Rollen, Verlustfreiheit, Qt-freie Planung) und welche Annahmen bis
  zur Hersteller-/Studio-Bestätigung reversibel bleiben.
