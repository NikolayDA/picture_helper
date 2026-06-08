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

Der Vergleich rechnet die prozentuale Änderung je Format aus; ein Format gilt als
**degradiert**, wenn es sich um mehr als `--threshold` Prozent (Default **10 %**)
verschlechtert hat. Sind alle Formate innerhalb der Schwelle, meldet der Report
kurz „Benchmarks stabil".

## CI / Issues

- `--fail-on-regression` setzt Exit-Code 1, sobald ein Format degradiert ist –
  gedacht für einen geplanten CI-Job.
- `--post-issues` legt für jedes geflaggte Format ein GitHub-Issue an
  (idempotent über einen Dedupe-Marker; braucht `GITHUB_TOKEN` und
  `GITHUB_REPOSITORY`). `--dry-run-issues` simuliert das nur.

> Hinweis: Absolute Zeiten hängen stark von der Maschine ab. Aussagekräftig ist
> die **relative** Veränderung zwischen Läufen auf vergleichbarer Hardware, nicht
> der Vergleich von Zahlen über verschiedene Rechner hinweg.
