# Das `.bgrproj`-Projektformat (v1/v2)

Technische Referenz des Projektcontainers von BgRemover: Aufbau, Manifest,
Formatversionen, Migration, Integritäts- und Fehlerverhalten. Der verbindliche
16-Bit-Datenvertrag hinter Formatversion 2 ist im ADR
[ADR-2026-height-16bit-datenvertrag.md](history/ADR-2026-height-16bit-datenvertrag.md)
beschlossen (#586); die Persistenz-Umsetzung ist #588. Nutzerdokumentation:
[ANLEITUNG.md](../ANLEITUNG.md) (Abschnitt „Projektdateien").

## Container

Eine `.bgrproj`-Datei ist ein ZIP-Archiv (Deflate) mit **flachen**
Dateinamen (keine Pfadanteile – Zip-Slip wird beim Laden abgewiesen):

| Eintrag | Inhalt |
|---|---|
| `manifest.json` | Formatversion, Canvas-Größe, geordnete Ebenenliste, aktive Ebene, Metadaten |
| `layer_NNNN.png` | RGBA-PNG je Ebene (Index von unten gezählt); für HEIGHT-Ebenen die **abgeleitete 8-Bit-Ansicht**, deren Alphakanal die Deckung trägt |
| `layer_NNNN_height16.png` | **nur v2, nur HEIGHT-Ebenen:** 16-Bit-Graustufen-PNG (`I;16`) mit den kanonischen `uint16`-Höhenwerten |

Geschrieben wird **atomar**: erst vollständig in eine Temp-Datei im
Zielverzeichnis, dann genau ein `os.replace`. Ein Abbruch (voller
Datenträger, Encoder-Fehler) lässt eine bestehende Zieldatei unversehrt und
räumt die Temp-Datei auf – es entsteht nie eine gültig wirkende Teil-Datei.

## Manifest

Gemeinsame Felder (v1 und v2): `version`, `project_version`, `width`,
`height`, `active_layer_id`, `metadata` sowie je Ebene `id`, `name`, `kind`
(`color`/`height`/`gloss`/`generic`), `visible`, `opacity`, `locked`, `role`,
`bit_depth` (informativ), `file`.

**Zusätzlich in v2 je HEIGHT-Ebene:**

| Feld | Bedeutung |
|---|---|
| `height16_file` | Dateiname der 16-Bit-Payload im Container |
| `height16_sha256` | sha256-Hexdigest der PNG-Bytes (Integritätsvertrag) |
| `height16_max_value` | Wertebereichs-Kennung, immer `65535` |

Die 16-Bit-Payload wird endianness-kontrolliert über numpy geschrieben und
gelesen (Rohbytes explizit als Little-Endian, kein Verlass auf
PIL-Modusdetails); PNG speichert 16-Bit-Grau verlustfrei, der Roundtrip ist
bitgenau inklusive der Niederbits.

## Formatversionen und Migration

- **v1** (bis BgRemover 2.6.0): alle Ebenen ausschließlich als 8-Bit-RGBA-PNG.
  HEIGHT-Höhen liegen als Graustufe im RGB (Konvention `R = G = B = Höhe`).
- **v2** (#588): zusätzlich die kanonische 16-Bit-Payload je HEIGHT-Ebene
  (siehe oben). Die 8-Bit-Ansicht bleibt **redundant** enthalten – Absicht:
  Abwärts-Lesbarkeit.
- **v1 → v2 (Öffnen):** deterministisch und verlustfrei im Sinne der
  ursprünglichen 256 Stufen – HEIGHT-Ebenen ohne `height16_file` erhalten
  `v16 = v8 × 257` aus dem R-Kanal ihres RGBA-PNGs (Adapter aus #587).
  COLOR/GLOSS, Reihenfolge und Metadaten bleiben unverändert. Beim nächsten
  Speichern entsteht kontrolliert eine v2-Datei.
- **Alte Anwendungsstände mit v2-Dateien:** Der Zukunfts-Versions-Pfad lädt
  best-effort (Warnung im Log); die 8-Bit-Ansicht wird korrekt angezeigt.
  **Speichert** ein alter Stand das Projekt erneut, entsteht eine v1-Datei
  ohne 16-Bit-Payload – die Niederbits gehen dabei kontrolliert auf die
  dokumentierte 16→8-Abbildung (`v8 = rint(v16 / 257)`) verloren.
- **Zukunftsversionen (≥ 3):** Warnung + Best-effort-Lesen, die Datei wird
  **nie** umgeschrieben.

## Validierung und Fehlerfälle

Das Laden ist defensiv; jeder Verstoß bricht mit einer übersetzten
`ProjectFileError`-Meldung ab, **bevor** etwas in das aktuell geöffnete
Projekt gelangt (ein fehlgeschlagener Open-Vorgang lässt es unverändert):

- Dateigrößen-Limit des Containers; Zip-Bomb-Schutz je Eintrag
  (RGBA-Einträge 4 B/px-Limit, `height16`-Einträge eigenes 2-B/px-Limit).
- Zip-Slip-Abwehr und Abweisung unerwarteter Einträge (erlaubt ist exakt die
  im Manifest deklarierte Menge plus `manifest.json`).
- Manifest-Strukturprüfung: fehlende/falsch typisierte Felder, unbekannte
  Kinds/Rollen, doppelte IDs/Rollen/Dateinamen, `height16_*` auf einer
  Nicht-HEIGHT-Ebene, fehlender `height16_sha256`, `height16_max_value ≠ 65535`.
- **Integrität:** Der sha256-Digest der Payload-Bytes muss dem Manifest
  entsprechen – abgeschnittene oder untereinander vertauschte
  `height16`-Dateien fallen vor dem Dekodieren auf.
- **Payload-Prüfung:** Megapixel-Limit, exakte Canvas-Größe, gültiger
  16-Bit-Grau-Modus (`I;16`/`I;16B` bzw. wertebereichsgeprüftes `I`);
  8-Bit-Grau oder Farbbilder sind keine gültige Payload (kein stilles
  Hochrechnen an dieser Grenze).
- Historisch inkompatible Rollen (z. B. `HEIGHT_MAP` auf COLOR) werden beim
  Laden verlustfrei normalisiert und als Warnung an die UI gereicht (#364).

## Größen- und Laufzeitwerte (repräsentativ, #588)

Ein HEIGHT-Layer kostet unkomprimiert 4 B/px (Ansicht) + 2 B/px (Payload).
Gemessen (ein HEIGHT-Layer, Save + Open, Linux-CI-Klasse):

| Projekt | Inhalt | Dateigröße | Speichern | Öffnen |
|---|---|---|---|---|
| 1 MP | Gradient | < 0,1 MB | 0,10 s | 0,04 s |
| 1 MP | Rauschen (Worst Case) | 4,5 MB | 0,71 s | 0,09 s |
| 16 MP | Gradient | 0,1 MB | 1,33 s | 0,88 s |
| 16 MP | Rauschen (Worst Case) | 71,0 MB | 11,3 s | 1,8 s |
| 40 MP | Gradient | 0,1 MB | 3,3 s | 4,6 s |

Das bestehende 1-GiB-Dateilimit und das 40-MP-Gate je Ebene bleiben die
harten Grenzen; die v2-Redundanz (Ansicht + Payload) ist zugunsten der
Abwärts-Lesbarkeit akzeptiert (ADR #586).
