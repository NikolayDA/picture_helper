# Performance-Benchmarks

Misst die Verarbeitungszeit der Bild-Pipeline **pro Ausgabeformat**
(PNG, JPEG, WebP, TIFF) und vergleicht aufeinanderfolgende Läufe, um
Performance-Regressionen früh zu erkennen.

Der Benchmark läuft über die echten Code-Pfade aus `bgremover.image_ops`
(`save_image_file`, `rotate_image`, `round_corners`, `crop_image`) – kein
Mock, kein Mikro-Benchmark einzelner Zeilen.

## Ausführen

```sh
make bench            # isolierte PNG/JPEG/WebP/TIFF-Suite
make bench-height     # isolierte HEIGHT16-/3D-Suite
make bench-compare    # die letzten zwei Format-Läufe vergleichen
```

Oder direkt:

```sh
QT_QPA_PLATFORM=offscreen python scripts/benchmark.py run \
    --suite formats --iterations 7
QT_QPA_PLATFORM=offscreen python scripts/benchmark.py run --suite height
QT_QPA_PLATFORM=offscreen python scripts/benchmark.py compare \
    --baseline benchmarks/results/formats/2026-06-01.json \
    --current  benchmarks/results/formats/2026-06-08.json
```

## Metriken

Pro Format werden gemessen (Median über `--iterations` Läufe, in Millisekunden):

| Metrik       | Bedeutung                                                        |
|--------------|------------------------------------------------------------------|
| `encode_ms`  | Speichern über `save_image_file` (Encode + atomare Ablage)       |
| `decode_ms`  | Vollständiges Laden/Dekodieren via `PIL.Image.open(...).load()`  |
| `process_ms` | End-to-End: Laden → Drehen → Ecken runden → Zuschneiden → Speichern |

`process_ms` ist die **Standard-Vergleichsmetrik** (`--metric` überschreibt das).

### 16-Bit-Höhen- und 3D-Reliefmesh-Baseline

Die eigenständige Suite `--suite height` (Alias: `--height-bench`) misst die
16-Bit-Höhenpipeline **und** den 3D-Reliefmesh-Aufbau je Projektgröße
(`HEIGHT16-1MP`/`-16MP`/`-40MP`). Neben `import_ms`/`process_ms`/`roundtrip_ms`/
`preview_ms` (2D) trägt jede Größe die 3D-Metriken aus dem echten Geometriekern
(`bgremover.relief_mesh.build_relief_mesh` – derselbe Pfad wie der
`MeshBuildWorker` des Viewers, nur ohne Qt/GL):

| Metrik           | Bedeutung                                                             |
|------------------|-----------------------------------------------------------------------|
| `mesh_build_ms`  | Median-Bauzeit des begrenzten Grid-Meshes (Näherung „Zeit bis erste sichtbare Vorschau"; GPU-Upload/Framerate sind hardwaregebunden, siehe Plattform-Smoke) |
| `mesh_peak_mb`   | Transienter Peak-Speicher **eines** Baus (`tracemalloc`) – belegt reproduzierbar, dass auch 40 MP kein Vollmesh materialisiert (64-MiB-Decimation-Deckel + Gitterbudget) |
| `mesh_vertices`  | Tatsächliche Vertexzahl gegen `MeshQuality.STANDARD.max_vertices` (262 144) |
| `mesh_triangles` | Tatsächliche Dreieckszahl gegen `max_triangles`                        |
| `mesh_decimation`| Vereinfachungsfaktor (`1` = keine Decimation)                          |

`mesh_build_ms` ist eine reguläre Zeit-Metrik und läuft durch dieselbe
Regressions-/Bestätigungslogik wie `process_ms`
(`--metric mesh_build_ms --fail-on-regression`). GPU-/Renderer-Upload,
interaktive Framerate und Update-Latenz hängen an der Grafikhardware und werden
im manuellen Plattform-Smoke belegt (siehe
[`docs/PACKAGING_SMOKE.md`](../docs/PACKAGING_SMOKE.md)).

## Ergebnisse & Vergleich

Jeder Lauf wird suite-getrennt als datiertes JSON unter
`benchmarks/results/formats/` bzw. `benchmarks/results/height/` abgelegt.
„Letzte Woche" ist die jüngste Datei derselben Suite vor dem aktuellen Lauf.
Der wöchentliche GitHub-Actions-Lauf schreibt neue Baselines **nicht** nach
`main` (der geschützte Branch lässt sich vom `GITHUB_TOKEN` weder direkt noch
über einen Auto-PR beschreiben, Issue #545). Stattdessen trägt jeder Lauf seine
Ergebnisse als **Workflow-Artefakt** (`benchmark-results`) weiter: Vor dem Messen
lädt der Job das Artefakt des letzten *erfolgreichen* **main**-Laufs nach
`benchmarks/results/` zurück und vergleicht gegen dessen jüngste Datei – so
gleitet die Baseline von Woche zu Woche, ganz ohne Schreibzugriff auf `main`.
(Nur `main`-Läufe zählen, damit ein manueller `workflow_dispatch` auf einem
Feature-Branch die Baseline nicht verfälscht.)
Fehlt das Artefakt (erster Lauf nach der Umstellung, abgelaufene Aufbewahrung),
bleibt die im Repo eingecheckte Baseline die Referenz; der Job wird dadurch nie
fälschlich rot. Eine eingecheckte Baseline lässt sich bei Bedarf jederzeit über
einen regulären PR aktualisieren.

Der Vergleich rechnet die prozentuale Änderung je Format aus; ein Format gilt als
**degradiert**, wenn es sich um mehr als `--threshold` Prozent (Default **10 %**)
verschlechtert hat. Sind alle Formate innerhalb der Schwelle, meldet der Report
kurz „Benchmarks stabil".

## Vergleichbarkeit, Rohwerte & Bestätigung (Schema 3)

Damit kein Mess- oder Umgebungsartefakt fälschlich als Regression gemeldet wird
(#277/#278/#279/#630), trägt jedes Ergebnis seit Schema 3 einen vollständigen
**Umgebungs-Fingerprint** (`environment`): Python-, Pillow- und NumPy-Version,
Betriebssystem/Kernel, Architektur, exaktes CPU-Modell, logische CPU-Anzahl sowie
GitHub-Runner-Image und -Version. Zusammen mit Suite und Benchmark-Parametern
entscheidet er, ob zwei Läufe überhaupt vergleichbar sind:

- **Nicht vergleichbar** (nur Anzeige, *keine* Regressionsmeldung): Schema,
  Suite, Parameter, Software, Kernel, CPU oder Runner-Image weichen ab.
- **Vergleichbar**: alle leistungsrelevanten Merkmale stimmen überein.

Wird gegen eine vergleichbare Baseline eine Auffälligkeit über der Schwelle
gemessen, werden insgesamt `--confirm-runs` vollständige Läufe ausgeführt
(Default **3**); verglichen wird der **Median**. Das JSON bewahrt zusätzlich die
Einzelzeiten je Iteration (`samples`) und alle vollständigen Bestätigungsläufe
(`runs`) auf. Nur eine danach weiterhin überschrittene Schwelle gilt als echte
Regression.

Format- und HEIGHT/3D-Suite laufen in CI in getrennten Prozessen. Dadurch können
die großen 16-/40-MP-Höhenläufe die PNG-Messung nicht durch Speicher-, Wärme-
oder Scheduler-Effekte verfälschen.

### Gepaarter Commitvergleich

Der manuelle Workflow-Modus `paired` misst einen Baseline-Commit und den
aktuellen Commit abwechselnd auf **demselben GitHub-Runner**. Beide Quellstände
verwenden denselben Schema-3-Benchmark-Harness und dieselben Dependency-Pins.
Der Workflow verlangt mindestens vier und stets eine gerade Zahl von Paaren,
damit beide Commits gleich oft zuerst laufen. `paired-compare` berechnet zuerst
das logarithmische Current/Baseline-Zeitverhältnis innerhalb jedes Paars und
bildet anschließend dessen Median. Reziproke Reihenfolgeeffekte heben sich damit
symmetrisch auf; Runner-Drift zwischen den Paaren kann den Schwellenentscheid
nicht verfälschen. Die Report-Zeiten sind paar-normalisierte, mathematisch zum
Delta passende Repräsentativwerte; alle beobachteten Einzelwerte bleiben im
JSON erhalten. Jede Kohorte muss genau einen Commit enthalten. Sämtliche Läufe
und Paar-Deltas landen im Artefakt `benchmark-ab-results`. Dieser Modus ist der
belastbare Nachweis, wenn sich die Hosted-Runner-Umgebung zwischen zwei
Wochenläufen geändert hat.

## CI / Issues

- `--fail-on-regression` setzt Exit-Code 1, sobald eine **bestätigte** Regression
  gegen eine vergleichbare Baseline vorliegt – gedacht für den geplanten CI-Job.
- `--post-issues` legt für jedes bestätigte Format ein GitHub-Issue an
  (idempotent über einen Dedupe-Marker; braucht `GITHUB_TOKEN` und
  `GITHUB_REPOSITORY`). Der Issue-Text nennt Baseline, Commit, Umgebungs-
  Fingerprint und die Zahl der Bestätigungsläufe. `--dry-run-issues` simuliert
  das nur.
- Der CI-Job pinnt Python (3.12) sowie Pillow/NumPy, damit aufeinanderfolgende
  Wochenläufe vergleichbar bleiben; ein bewusster Versionssprung setzt die
  Baseline ohne Fehlalarm zurück.

> Hinweis: Absolute Zeiten hängen stark von der Maschine ab. Aussagekräftig ist
> die **relative** Veränderung zwischen Läufen auf vergleichbarer Hardware, nicht
> der Vergleich von Zahlen über verschiedene Rechner hinweg.
