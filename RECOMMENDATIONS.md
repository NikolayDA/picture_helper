**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Muss behoben werden – führt zu Fehlern, Abstürzen oder Inkonsistenzen |
| 🟠 | Hoch | Sollte bald behoben werden – beeinträchtigt Zuverlässigkeit oder Wartbarkeit erheblich |
| 🟡 | Mittel | Empfohlen – verbessert Code-Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optional – Polishing, ergänzende Verbesserungen |

---

## Aktueller Stand (2026-06-01, Review „modest-shannon")

Tiefenprüfung der Codebasis nach v2.2 (Code, Doku, Tests). Baseline exzellent: Ruff/mypy sauber, Test-Suite grün, Coverage 88 %. Gefunden wurden **5 Befunde (A–E)** – alle umgesetzt, mit Regressionstests, und gemergt über **PR #135** (A, B) bzw. **PR #136** (C–E). Beleg jeweils mit Datei-/Funktionsbezug.

### Erledigungsstand

| Status | Punkte |
|--------|--------|
| ✅ Erledigt | A, B, C, D, E |

### Befunde

- **A 🟠 — `DecompressionBombError` abfangen.** `image_loading.py` fing Pillows `DecompressionBombError` (keine `OSError`-Subklasse) nicht ab → Bilder über 2× `MAX_IMAGE_PIXELS` (80 MP) umgingen die freundliche „zu groß"-Meldung und schlugen im synchronen `load_image`-Pfad ungefangen durch. Jetzt in beiden Öffnungs-Phasen abgefangen und auf die Standardmeldung abgebildet; der Regressionstest löst Pillows echten Bomb-Schutz aus (kein `Image.open`-Mock).
- **B 🟡 — Zauberstab-Lebenszyklus beim Bildwechsel.** `_reset_transient_state` (`canvas.py`) setzte `_wand_busy` nicht zurück, und `_load_image_async` (`main_window.py`) brach den Flood-Fill nicht ab – asymmetrisch zu `cancel_ai()`. Folge: der Zauberstab blieb nach Bildwechsel/Restore blockiert, dazu verschwendete CPU. Zentraler Flag-Reset + `cancel_flood_fill()` beim Laden.
- **C 🟡 — Logging-Isolation.** `_setup_logging` (`logging_config.py`) nutzte `basicConfig(force=True)` am Root → Fremd-Logs (rembg/onnxruntime/Pillow) landeten in der Support-Logdatei, Fremd-Handler wurden abgerissen. Jetzt benannter `BgRemover`-Logger mit eigenen Handlern (`propagate=False`).
- **D 🟢 — Test-Altlasten.** `test_static_checks.py` suchte den entfernten Monolithen `BgRemover.py` und trug irreführende `#N`-Marken (historische Runden ≠ aktuelle Nummerierung). Monolith-Zweig entfernt, Herkunft im Docstring klargestellt.
- **E 🟢 — i18n-Sicherheitsnetz.** Die Soft-Drift-Prüfung deckte nur 3 von 8 übersetzten Docs ab. `WATCHED_DOCS` auf alle 8 erweitert (alle aktuell strukturell synchron).

---

## Vorige Runde (v2.2, „admiring-mayer")

Externe 15-Punkte-Liste gegen die Codebasis geprüft: **#1–#15 erledigt, #4 verworfen** (Fehlalarm). Details in den gemergten PRs und im Archiv.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
