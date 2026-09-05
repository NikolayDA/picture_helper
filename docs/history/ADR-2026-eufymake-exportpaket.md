# ADR (2026-06-22): EufyMake-Exportpaket-Konvention

Kurz-ADR zu #352 („Export-Datenmodell & Paketdefinition (Qt-frei) +
Konventions-ADR") im Epic #351 („Konsistentes EufyMake-Exportpaket").
Status: **beschlossen, Implementierung folgt** (#352–#355).
Nachtrag 2026-09-02: umgesetzt (#352–#355); Entscheidung 5 (Standard 8 Bit) und
der Bittiefen-Absatz unten sind seit #691 durch das versionierte Zielprofil
abgelöst – siehe [`ADR-2026-eufymake-zielprofil.md`](ADR-2026-eufymake-zielprofil.md)
und den Nachtrag am Ende.

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
   identisch und wird im Exportplan beschrieben. Die ZIP-Variante hat nach
   aktuellem Kenntnisstand keinen Nutzen: Studio importiert laut Recherche
   Einzeldateien, kein Paket (#687, EM-C04) – der Ordner bleibt die tatsächlich
   genutzte Form.
2. **Rollenabbildung:** `LayerRole.COLOR_MOTIF` wird zum Farbmotiv,
   `LayerRole.HEIGHT_MAP` zur Höhen-Graustufe und `LayerRole.GLOSS_MASK` zur
   optionalen Gloss-/Klarlackmaske. Andere Ebenenrollen sind nicht Teil des
   EufyMake-Pakets.
3. **Dateikonvention:** Die kanonischen Asset-Namen sind
   `color_motif.png`, `height_map.png` und optional `gloss_mask.png`. Ein
   optionales Manifest `manifest.json` darf dieselben Assets, Projektgröße,
   DPI/Auflösung, Bittiefe und Annahmen maschinenlesbar wiederholen, ist aber
   nicht Voraussetzung für den ersten Render-/Schreibschritt. `manifest.json`
   ist ausschließlich BgRemover-interne Dokumentation ohne belegten
   Studio-Importvertrag (#687, EM-C01) – eine Studio-Auswertung ist nicht
   dokumentiert. „Widerlegt“ wäre ohne den offenen Negativtest I-06 zu stark;
   der Status bleibt nicht belegt/intern, nicht widerlegt.
4. **Bildformate:** Alle Assets werden verlustfrei geplant. Das Farbmotiv ist
   ein PNG mit Alpha (`RGBA`). Die Höhenkarte ist ein Graustufen-PNG, bei dem
   **hell = hoch** und **dunkel = niedrig** gilt. Die Gloss-Maske ist ein
   Graustufen-PNG; die ursprüngliche Annahme **hell = mehr Glanz/Klarlack** ist
   widerlegt – die Primärquelle A11 (Volltext gelesen, #687) belegt für die
   Spot-UV-Maske **Schwarz = Gloss auftragen, Weiß = nichts**. Die echte
   Polarität einer eigenen `gloss_mask.png` (und eine mögliche
   Intensitätsabstufung) ist damit noch nicht durch einen Realtest bestätigt;
   der Gloss-Realtest in #690 steht noch aus.
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

### Nachtrag (2026-08-15, Issue #687)

Eine Schreibtischrecherche (kein Realtest, Herstellerbelege nur über
Suchmaschinen-Extraktion, Details und Quellen im versionierten
[Annahmeninventar](EUFYMAKE-687-ANNAHMENINVENTAR.md)) beantwortet den ersten
Punkt oben auf Evidenzgrad **S**: EufyMake Studio importiert Einzeldateien
(PNG/JPEG/WEBP/SVG/AI/PSD/PDF), kein Paket und kein Manifest. Der importorientierte
Exportordner aus Entscheidung 1 bleibt damit die richtige Wahl – ein Wechsel auf
ein verbindliches Manifest oder feste Ordnernamen (letzter Punkt oben) ist nach
aktuellem Kenntnisstand **nicht** zu erwarten. Der zweite Punkt (Bittiefe) hat
ebenfalls neue, unbestätigte Evidenz: der Hersteller nennt 16 Bit/Kanal für
Höhenkarten „if the option is available" – der Validator markiert seither den
8-statt den 16-Bit-Pfad als unbestätigt (`eufymake_validate.py`,
`BIT_DEPTH_UNCONFIRMED`). Alle Punkte bleiben formal **offen**, bis sie an echter
Hardware (#688–#690) oder am Original der Herstellerquellen (V-01 im
Annahmeninventar) verifiziert sind.

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

## Nachtrag 2026-09-02 (#691, PR #953)

Das versionierte Zielprofil (`bgremover/eufymake_profile.py`, Profil
`bgremover-eufymake-import@1`) ist jetzt die einzige Quelle für Rollen,
Dateinamen, Kanalinterpretation, Defaults und Validierungscodes; die hier
festgelegten Dateinamen und die Manifestkonvention bleiben darin unverändert.
Abgelöst ist Entscheidung 5 im Punkt Bittiefe: Der konservative HEIGHT-Default
ist 16 Bit, und `BIT_DEPTH_UNCONFIRMED` warnt für **beide** Träger, bis die
physische #688-Messung vorliegt. Entscheidung und Begründung:
[`ADR-2026-eufymake-zielprofil.md`](ADR-2026-eufymake-zielprofil.md).

## Nachtrag 2026-09-05 (#689/#691, PNG-`pHYs`)

Entscheidung 5 (Parameterableitung) wird um den Träger im PNG ergänzt: Der
Writer schreibt die aus Pixelmaß und physischer Größe abgeleiteten X-/Y-DPI als
`pHYs`-Chunk in jedes Asset (`eufymake_writer.png_dpi_for`, identisch mit
Manifest-`target.dpi`). Grund ist die #689-Studio-Beobachtung: Studio 4.2.2
übernimmt `pHYs` je Achse als Startgröße und startet ohne den Chunk mit 72 dpi
(1200 px → 423,33 mm). Ohne physische Projektgröße entsteht bewusst kein
`pHYs` – eine erfundene Auflösung wäre schlechter als ein sichtbar fehlender
Wert. Entscheidung 3 bleibt unberührt: `manifest.json` ist weiterhin interne
Provenienz, das `pHYs` ist der einzige Weg der physischen Größe nach Studio.
Evidenz: [`EUFYMAKE-689-MM-DPI-VERTRAG.md`](EUFYMAKE-689-MM-DPI-VERTRAG.md),
Nachtrag 2026-09-05.
