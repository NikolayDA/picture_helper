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

## Offene Empfehlungen

Aus der zweiten Analyse hervorgegangene, noch offene Verbesserungen (Produkt/Prozess):

- **O1 🟠 — App-Lokalisierung.** Die UI ist hartkodiert Deutsch; es gibt keine Laufzeit-i18n (kein `QTranslator`/`tr()`), obwohl die Doku in fünf Sprachen vorliegt. Statusmeldungen liegen bereits zentral (`status_messages.py`). Schrittweise via Qt Linguist (`.ts`) oder leichtgewichtige `QLocale`-Stringtabelle.
- **O2 🟡 — Linux-App / Paketierung.** Kein App-Bundle für Linux; Start nur via `python -m bgremover` aus einer venv. Ein installierbares Paket (AppImage/Flatpak/`.deb`) für **Raspberry Pi OS** und große Distributionen (Debian/Ubuntu/Fedora) senkt die Einstiegshürde für Nicht-Entwickler – analog zum macOS-`.app`-Bundle.
- **O3 🟡 — Volle CI-Matrix früher.** Die Vollmatrix (Linux/macOS × 3.10–3.13) läuft nur bei Tags/Release; Regressionen unter macOS oder Python 3.10/3.13 fallen erst spät auf. Zusätzlich bei Push auf `main` oder als wöchentlicher Cron laufen lassen.
- **O4 🟢 — Tastatur-Kürzel für Werkzeuge.** Zauberstab/Pinsel/Radierer/Lasso sind nur per Maus erreichbar; Ein-Tasten-Wechsel (z. B. `B`/`E`) ergänzen.


## Umsetzungspakete aus dem Qualitäts-Gegencheck

Die bestätigten Qualitäts- und Stabilitätsbefunde werden in vier getrennten Paketen umgesetzt:

- **P1 ✅ — Zauberstab-/CI-Quick-Wins (N1, N6, N8).** Das Wand-Gate wird beim Start eines Bildwechsels still freigegeben, damit ein anschließender Ladefehler den Zauberstab nicht blockiert. Die Linux-Vollmatrix installiert nun ebenfalls `libgl1`; ein statischer Drift-Test schützt die Qt-Systempaketlisten. Der veraltete synchrone Drop-Hinweis wurde korrigiert.
- **P2 🟡 — Speichern härten (N4, N5).** Export-Endungen explizit validieren und bestehende Dateien über temporäre Datei + atomaren Replace ersetzen.
- **P3 🟠 — Adaptives Speicherbudget (N2, N3).** Erwartete Größe vor freien Rotationen prüfen; Undo, Redo, Originalzustand und speicherintensive Operationen gemeinsam budgetieren, insbesondere für Raspberry Pi.
- **P4 🟡 — Paketimporte entkoppeln (N7).** Eager GUI-Re-Exporte vorsichtig reduzieren oder lazy laden, damit reine Logikmodule ohne vollständige Qt-Laufzeit testbar und wiederverwendbar sind. Kein Bootstrap-Bug; öffentliche Imports müssen kompatibel bleiben.


---

## Vorige Runde (v2.2, „admiring-mayer")

Externe 15-Punkte-Liste gegen die Codebasis geprüft: **#1–#15 erledigt, #4 verworfen** (Fehlalarm). Details in den gemergten PRs und im Archiv.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
