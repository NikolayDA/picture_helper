# Performance-Benchmarks

Misst die Verarbeitungszeit der Bild-Pipeline **pro Ausgabeformat**
(PNG, JPEG, WebP, TIFF) und vergleicht aufeinanderfolgende Läufe, um
Performance-Regressionen früh zu erkennen.

Der Benchmark läuft über die echten Code-Pfade aus `bgremover.image_ops`
(`save_image_file`, `rotate_image`, `round_corners`, `crop_image`) – kein
Mock, kein Mikro-Benchmark einzelner Zeilen.

## Ausführen

```sh
make bench            # Lauf + Vergleich gegen den letzten gespeicherten Lauf
make bench-compare    # Die letzten zwei gespeicherten Läufe vergleichen
```

Oder direkt:

```sh
QT_QPA_PLATFORM=offscreen python scripts/benchmark.py run --iterations 7
QT_QPA_PLATFORM=offscreen python scripts/benchmark.py compare \
    --baseline benchmarks/results/2026-06-01.json \
    --current  benchmarks/results/2026-06-08.json
```

## Metriken

Pro Format werden gemessen (Median über `--iterations` Läufe, in Millisekunden):

| Metrik       | Bedeutung                                                        |
|--------------|------------------------------------------------------------------|
| `encode_ms`  | Speichern über `save_image_file` (Encode + atomare Ablage)       |
| `decode_ms`  | Vollständiges Laden/Dekodieren via `PIL.Image.open(...).load()`  |
| `process_ms` | End-to-End: Laden → Drehen → Ecken runden → Zuschneiden → Speichern |

`process_ms` ist die **Standard-Vergleichsmetrik** (`--metric` überschreibt das).

## Ergebnisse & Vergleich

Jeder Lauf wird als datiertes JSON unter `benchmarks/results/<JJJJ-MM-TT>.json`
abgelegt. „Letzte Woche" ist schlicht die jüngste Datei vor dem aktuellen Lauf.
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

## Vergleichbarkeit & Bestätigung (Schema 2)

Damit kein Mess- oder Umgebungsartefakt fälschlich als Regression gemeldet wird
(#277/#278/#279), trägt jedes Ergebnis seit Schema 2 einen **Umgebungs-
Fingerprint** (`environment`): Python-, Pillow- und NumPy-Version, Betriebssystem,
Architektur, logische CPU-Anzahl und der GitHub-Runner. Zusammen mit den
Benchmark-Parametern (Iterationszahl, Bildabmessungen) entscheidet er, ob zwei
Läufe überhaupt vergleichbar sind:

- **Nicht vergleichbar** (nur Anzeige, *keine* Regressionsmeldung): die Baseline
  hat keinen Fingerprint, oder Python-Minor-/Pillow-/NumPy-Version bzw.
  Iterationszahl/Bildabmessungen weichen ab.
- **Bedingt vergleichbar** (Bestätigungslauf nötig): nur die Hardware
  (Architektur/CPU-Anzahl) weicht ab.
- **Vergleichbar**: alles passt.

Wird gegen eine vergleichbare Baseline eine Auffälligkeit über der Schwelle
gemessen, läuft der Benchmark im selben Durchgang `--confirm-runs` Mal komplett
nach (Default **3**); verglichen wird der **Median**. Nur eine im
Bestätigungslauf weiterhin überschrittene Schwelle gilt als echte Regression.

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
