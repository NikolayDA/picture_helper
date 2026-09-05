# Druckvorbereitung Epic #681 – 2026-09-05

**Status: Dateisatz geprüft; Druckfreigabe blockiert. Kein physischer Druck.**

Auftrag: „Erledige Punkt 1 für mich“ – Druckvorbereitung einschließlich
Beschriftungsnachzug, I-10/G-02-Entscheidung, Gerätedaten, Material/Messmitteln
und Vorschau-Preflight. Der Auftrag umfasst keinen Druck und keinen
Firmwarewechsel. Budgetverbrauch weiterhin 0/35.

## Erledigt

- Vorhandene lokale Arbeit vor der Bearbeitung gesichert (lokale Sicherung
  `/private/tmp/eufymake-point1-before-20260905.tar.gz`, kein dauerhafter
  Evidenzablageort).
- Bereits lokal überarbeitete Träger aller 13 Projekte beibehalten. 04 enthält
  „I-08 · nach Crop“, 10 „G-05 · COLOR 256×256“; beide Beschriftungsgruppen sind
  vollständig. Träger und eingebettete Quellen stimmen in den Prüfsummen überein.
- Die auf `main` bereits vorhandene Flatbed-Korrektur aus Commit `737be2b`
  beibehalten: **335 × 420 mm**, keine zusätzliche 330-mm-Fläche und
  kein angenommener 2,50-mm-Rand. Die realen Objektpositionen bleiben erhalten.
- Im nativen Projekt 04 zeigte Studio beim Träger `Y = NaN`. Im Canvas stand
  `originY: left` (ungültig). Der Fehler betraf in allen 13 Projekten insgesamt
  37 COLOR-/Gloss-/Trägerebenen. `originY` wurde zu `top` korrigiert; Pixel,
  HEIGHT-Quellen, Gloss-Quellen, Skalierung und numerische Positionen blieben
  unverändert. Studio zeigt nach der Korrektur die Beschriftung und gültige
  Y-Positionen. Gültige `center`-Ursprünge der HEIGHT-Objekte bleiben erhalten.
- Reparaturgrundlage waren die vorhandenen entpackten lokalen Projektarchive;
  vor jeder Übernahme wurden sämtliche eingebetteten Fixture- und Trägerbytes
  gegen `projects.json` und das kanonische Fixture-Manifest geprüft.
  Die reparierten Projekte 04 und 10 wurden als native ZIP-kompatible `.empf`
  in Studio 4.2.2 geöffnet; alle 13 Container wurden automatisch geprüft. Der produktive BgRemover-PNG-Exportvertrag ändert sich nicht.
- Die bestehende `projects.json`-Bindung von `main`, Aufbau-JSONs und
  Gesamtmanifest neu gebunden. Vorschauen mit dem aktuellen Generator
  abgeleitet; native Thumbnails separat gehasht, keine Gleichheitsannahme.
  Der Generator prüft nun direkt im Projektcontainer Rollen, Quellen je Ebene,
  Träger, Thumbnail, Ursprünge, endliche Zahlen und Sollgeometrie; nicht nur
  einen äußeren Hash. `--check` prüft den Satz ohne Schreibzugriff.
- I-10/G-02: Im delegierten Vorbereitungsauftrag **Option A** gewählt und in
  der Governance dokumentiert. I-10 entfällt physisch; G-02 bleibt mit je zwei
  unabhängigen Läufen pro Richtung. Plätze 9–10 bleiben unzugeordnet. Projekt
  05 ist im Manifest ausdrücklich gesperrt. Für die Erstläufe bleiben 13 A4-
  Kartons vorgesehen; weitere Kernaussagen-Wiederholungen separat einplanen.

## Live-Beobachtung in Studio

Evidenzart: **Import-/UI-Beobachtung**, keine Druckmessung. Beobachtet über die
lokale Studio-Oberfläche am 2026-09-05. Screenshots sind im Codex-Sitzungsverlauf
sichtbar; ein separates dauerhaftes Screenshot-/iCloud-Artefakt wurde noch
nicht angelegt. Vor dem Drucktag ist diese Ablage zu ergänzen.

| Parameter | Beobachtung |
| --- | --- |
| Studio / Editor | 4.2.2 / v1.20.0 |
| Gerät / Verbindung | eufyMake UV Printer E1 / online |
| Installierte Firmware | **V4.0.2**, unter Printer Settings → About Device abgelesen |
| Updateangebot | 4.0.9 angeboten, nicht installiert |
| Betriebsstatus | **Unavailable**: gelbe Tinte abgelaufen, Austausch gefordert |
| Weitere Gerätemeldungen | Scraper und Air Filter abgelaufen; können Druckleistung beeinflussen |
| C/M/Y/K/W/G | Balken sichtbar; keine belastbaren ml-/Prozentwerte angezeigt |
| Kartuschenhinweise | C: Good, gültig bis 2026-10-14; M: Ablauf in 25 Tagen; Y: abgelaufen; K: Ablauf in 10 Tagen |
| Nutzerangabe zum Material | „Schwarz, 0,1 mm“; als schwarzer Karton mit 0,1 mm Dicke verstanden, Zuordnung der 0,1 mm noch zur Bestätigung nachgefragt |
| Messmittel | Noch nicht angegeben; Rückfrage zu Messschieber/Mikrometer und Höhenprofilmessung offen |
| Materialtest in Projekt 10 | `Cardboard` gewählt, dunkle Materialfarbe zur Ansicht gewählt; **Warnung: „Please do not use gloss oil on current platform type“** |
| Weißtinte auf Cardboard | Studio fordert bei weichen Materialien Flexible White Ink zur Vermeidung von Verformung/Rissen; tatsächlicher Tintentyp nicht bestätigt, kein Wechsel ausgeführt |

Die Cardboard-Warnung ist ein Befund der getesteten Studio-Version, keine
allgemeine Behauptung über jeden Karton. Der Gloss-Pfad bleibt damit für diese
Materialwahl gesperrt. Die Warnung wird nicht durch eine falsche Materialwahl
oder einen Druckversuch umgangen.

## Vorschau und feste Projektparameter

Die unveränderten Projektparameter sind je Ebene in `layout_manifest.json`
und den jeweiligen Aufbau-Dateien enthalten: A4-Ursprung 62,50/61,50 mm,
Rotation 0°, HEIGHT `Color Raised`/`Customize Texture` mit 2,50 mm und native
Gloss-Ebenen mit `Gloss Varnish × 1`. Die Positionen unterscheiden sich nach
A4-Feld; die frühere Einzelmotiv-Zentrierung gilt nicht für jede Ebene.
Material/Qualität/Tintenoptionen sind **noch keine bestätigten Druckparameter**.
Die Quelldateien wurden deshalb nicht pauschal auf Cardboard umgestellt.

| Projekt | Preflight am 2026-09-05 | Zeit / Tinte | Druckfreigabe |
| --- | --- | --- | --- |
| 04 / I-08 vor und nach Crop | Repariertes Prüfprojekt in Studio geöffnet; Beschriftungen sichtbar, native HEIGHT- und Gloss-Ebenen erhalten. `Preview` sowie `Estimate Ink & Time` ausgeführt. | **1 h 40 min 43 s; ca. 1,84 ml**. Angezeigt: W 0,9 ml, G 0,9 ml, C/M/Y/K jeweils <0,01 ml. Einstellungen dabei: Material `Unknown`, Qualität `Standard`, White Underbase Choke 0,2 mm. Nur vorläufige Schätzung. | Nein: Gerät/Material/Messmittel offen |
| 10 / G-05 | Finales repariertes Projekt geöffnet; beide Beschriftungszeilen sichtbar, Glossmaske auf der linken Hälfte des COLOR-Felds. Materialtest `Cardboard` erzeugt die oben genannte Warnung. | Keine belastbare Schätzung für den freizugebenden Materialpfad | Nein: konkrete Materialwarnung |
| 05 / I-10 | Nicht ausführen; Option A | entfällt | entfällt |
| 01–03, 06–09, 11–13 | Native Container, Geometrie und Quellen automatisch geprüft; zellspezifische Studio-Vorschau noch ausstehend | nach Klärung der gemeinsamen Material-/Geräteparameter erheben | Nein |

Die Vorschau von 04 verwendete eine temporäre Prüffassung mit identischem
repariertem Canvas und identischen eingebetteten Bildern wie der finalen
Projektdatei. Die temporäre Datei wurde anschließend entfernt. Die Schätzung
bestätigt weder die tatsächlich verbrauchte Tinte noch einen Druckbefund.

## Noch erforderlich für eine vollständige Druckvorbereitung

1. Abgelaufene Y-Kartusche sowie Scraper-/Luftfilterstatus am Gerät klären.
   Gerätewarnungen erneut dokumentieren; kein automatischer Firmwarewechsel.
2. Gloss-taugliches Material bzw. einen für das konkrete Substrat ausdrücklich
   geeigneten Studio-Pfad bestimmen. Für I-13/G-06 dasselbe nicht-weiße Substrat
   verwenden. Weißtintentyp passend zum Material bestätigen.
3. Messgeräte, Auflösung und Messunsicherheit benennen: Relief ≤0,05 mm;
   I-14 lateral ≤0,1 mm und vertikal ≤0,05 mm; Länge/Breite ≤0,1 mm bei
   Messbereich ≥150 mm. Für I-03 die Auswertungsregel vor dem Druck festlegen.
4. Unter den anschließend festen Laufparametern alle aktiven Varianten in
   Studio vorprüfen und Zeit-/Tintenwerte sowie Warnungen protokollieren.
   Bestehende Schätzung für 04 bei geänderten Parametern erneuern.
5. Screenshots/Studio-Projekte mit SHA-256 dauerhaft im vorgesehenen privaten
   iCloud-Evidenzordner ablegen. Druckfreigabe erst nach Auflösung der Sperren.

## Gebundener Projektsatz

Die vollständigen SHA-256-Werte stehen zusätzlich in `projects.json`.

| Projekt | SHA-256 | Status |
| --- | --- | --- |
| 01 height_pixelgroesse_i02_i04 | `748d245c9fdb5ae0f6b11205ff0f2fee08a73bcf7fd791f5e94640c9c77384bc` | Dateisatz geprüft; Druck nicht freigegeben |
| 02 height_bittiefe_filter_i03_i14 | `cc619f1f652ef2f1b5d983efa966a40b694ae4ed02898d0cfbf01c079f1e1a98` | Dateisatz geprüft; Druck nicht freigegeben |
| 03 height_grenzen_stufen_alpha_i07_i11_i13 | `184995cdffa1e3e337c82625ca585c74f66377a19f8872928d516aeffbb213d3` | Dateisatz geprüft; Druck nicht freigegeben |
| 04 registrierung_crop_i08 | `d6ba1003d3645ad0dc59006ea5925a8941f1c2609d5ac11a41433aae293af045` | Dateisatz geprüft; Druck nicht freigegeben |
| 05 gloss_polaritaet_i10 | `f71ab397d13f3f824abe850a86c91948b10f98d680d644f4a2d432199833f688` | entfällt |
| 06 mm_dpi_i05 | `f75cd29f63f957768d3d38ab1e8ce3bb607b6a2759479be3bda2bfd6c5aa69b0` | Dateisatz geprüft; Druck nicht freigegeben |
| 07 gloss_kennlinie_g01_g03 | `32d922db36f37fb6ab6899125812c459dcbdd6f0085ac3fadb41d945b7bc21cd` | Dateisatz geprüft; Druck nicht freigegeben |
| 08 gloss_polaritaet_g02 | `92743ba1282949013904045859b47d9dc58b6b0215860cc564dfff6c47862ef8` | Dateisatz geprüft; Druck nicht freigegeben |
| 09 gloss_optionalitaet_g04 | `2b360f56d9812b9ada7c1db32916ad24de0ffd62b6e09f53e770825e7184ea7a` | Dateisatz geprüft; Druck nicht freigegeben |
| 10 gloss_dimension_g05 | `84073c92504c8f7c31f91c051b0982885ad26b29b15b66b6ccfb9478999b30ef` | Dateisatz geprüft; Druck nicht freigegeben |
| 11 gloss_alpha_g06 | `8af830ac0418ee827e048fbe11588f2191921176d546f9e81cbbf62b686ab7e5` | Dateisatz geprüft; Druck nicht freigegeben |
| 12 gloss_height_g07 | `79f78c3b88c82a321aaa2b570e42196be0b6b93c0a9c63a7b1089a54710ae079` | Dateisatz geprüft; Druck nicht freigegeben |
| 13 gloss_registrierung_g08 | `3fd347a980c729e7be100976ac7547c6117f9e6870f143eab4f26b3b51d72890` | Dateisatz geprüft; Druck nicht freigegeben |

## Verifikation

- `make PYTHON=<bestehende-venv>/bin/python check` auf dem PR-Zweig auf Basis
  des aktuellen `main`: erfolgreich; Ruff und mypy ohne Befund,
  **3017 Tests bestanden, 73 übersprungen, 14 abgewählt**. Der Qt-Testprozess
  benötigte einen Lauf außerhalb der Sandbox. Shellcheck lokal nicht
  installiert; die CI übernimmt das Shell-Lint.
- `make PYTHON=<bestehende-venv>/bin/python release-freeze-check`:
  0 Fehler, 0 Warnungen nach Aufnahme dieses Protokolls als exakter neutraler
  Dokumentpfad in Pfadpolicy 16; bestehende Regeln unverändert.
- `python scripts/prepare_eufymake_a4_layouts.py --check`: alle 13 nativen
  Projektbindungen, Quellen, Geometrien, Träger, Vorschauen und Manifeste gültig.
- Unabhängiger Vergleich mit den Reparaturquellen: exakt 37 Änderungen von
  `originY: left` zu `originY: top`; alle übrigen JSON-Werte sowie sämtliche
  Bildbytes unverändert.
- Negativtests weisen ungültige Ursprünge, verschobene Geometrie und eine
  verloren gegangene Gloss-Zuweisung zurück.
- `git diff --check`: ohne Befund. Veröffentlichung und aktuelle CI-Ergebnisse
  werden im zugehörigen PR dokumentiert.
