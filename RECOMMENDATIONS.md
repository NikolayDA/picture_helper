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

## Aktueller Stand (2026-06-02, Review „adoring-johnson")

Gezielte Folge-Prüfung nach „modest-shannon", Schwerpunkt Speicher-, Lade- und CI-Pfad. **8 Punkte (N1–N8):** 5 behoben mit Regressionstests – gemergt über **PR #142** (N1), **#143** (N6, N8) und **#144** (N4, N5); 2 offen (N2, N7); 1 bereits abgedeckt (N3). Baseline weiter grün: Ruff/mypy sauber, Suite grün.

### Erledigungsstand

| Status | Punkte |
|--------|--------|
| ✅ Erledigt | N1, N4, N5, N6, N8 |
| ⏳ Offen | N2, N7 |

### Befunde

- **N1 🟠 — Zauberstab-Gate im Fehlerpfad freigeben** (PR #142). Folgebefund zu „modest-shannon"-B: Beim Bildwechsel bricht `_load_image_async` den Flood-Fill ab, der dann weder `finished` noch `error` emittiert. Der Gate-Reset lief nur über den Erfolgspfad (`apply_loaded_image`) – schlug das Laden fehl, blieb `_wand_busy` gesetzt und der Zauberstab auf dem alten Bild blockiert. Neue stille `reset_pending_wand()` direkt neben `cancel_flood_fill()`.
- **N2 🟡 — Rotations-Größenlimit** (offen). `rotate_image` (`image_ops.py`) dreht mit `expand=True`; der Megapixel-Schutz greift nur beim Laden (`Image.MAX_IMAGE_PIXELS`), nicht auf dem Ergebnis. Eine knapp zulässige Vorlage kann sich bei ~45° auf ~2× aufblähen – Speicherspitze ohne Gate.
- **N3 ➖ — History-Speicherbudget** (bereits abgedeckt). `CanvasHistory` (`canvas_history.py`) erzwingt das Undo-Budget längst über `_trim()`/`_UNDO_MEMORY_LIMIT`, Redo ist über `_REDO_MAX_ENTRIES` gedeckelt. Kein Handlungsbedarf.
- **N4 🟢 — Endungs-Ehrlichkeit beim Speichern** (PR #144). `save_image_file` schrieb für unbekannte Endungen still PNG-Bytes; jetzt klare `ValueError`-Ablehnung, leere Endung bleibt PNG-Default.
- **N5 🟡 — Atomares Speichern** (PR #144). Direktes Schreiben ans Ziel zerstörte bei Abbruch die vorhandene Datei. Jetzt `mkstemp` → `os.replace` im Zielverzeichnis (Muster wie `qt_plugins._copy_if_needed`), mit Rechte-Erhalt und temp-Aufräumen.
- **N6 🟡 — `libgl1` in CI-Vollmatrix + Drift-Test** (PR #143). Die Vollmatrix installierte `libgl1` nicht (anders als die übrigen Qt-Paketquellen) → `import PyQt6` riskierte `libGL.so.1`. Ergänzt; neuer `test_ci_qt_packages.py` hält alle vier Paketlisten konsistent.
- **N7 🟢 — Eager-Imports** (offen). `workers.py` importiert `rembg` (zieht onnxruntime) auf Modulebene; da `main_window` `workers` lädt, fallen die Importkosten schon beim Start an – auch ohne KI-Nutzung. Lazy-Import + `find_spec`-Probe für `REMBG_AVAILABLE`.
- **N8 🟢 — Veralteter `load_image`-Docstring** (PR #143). Nannte den Drop-Pfad als synchronen Aufrufer, obwohl Drag & Drop längst asynchron läuft. Korrigiert.

---

## Offene Empfehlungen

Aus der zweiten Analyse hervorgegangene, noch offene Verbesserungen (Produkt/Prozess):

- **O1 🟠 — App-Lokalisierung.** Die UI ist hartkodiert Deutsch; es gibt keine Laufzeit-i18n (kein `QTranslator`/`tr()`), obwohl die Doku in fünf Sprachen vorliegt. Statusmeldungen liegen bereits zentral (`status_messages.py`). Schrittweise via Qt Linguist (`.ts`) oder leichtgewichtige `QLocale`-Stringtabelle.
- **O2 🟡 — Linux-App / Paketierung.** Kein App-Bundle für Linux; Start nur via `python -m bgremover` aus einer venv. Ein installierbares Paket (AppImage/Flatpak/`.deb`) für **Raspberry Pi OS** und große Distributionen (Debian/Ubuntu/Fedora) senkt die Einstiegshürde für Nicht-Entwickler – analog zum macOS-`.app`-Bundle.
- **O3 🟡 — Volle CI-Matrix früher.** Die Vollmatrix (Linux/macOS × 3.10–3.13) läuft nur bei Tags/Release; Regressionen unter macOS oder Python 3.10/3.13 fallen erst spät auf. Zusätzlich bei Push auf `main` oder als wöchentlicher Cron laufen lassen.
- **O4 🟢 — Tastatur-Kürzel für Werkzeuge.** Zauberstab/Pinsel/Radierer/Lasso sind nur per Maus erreichbar; Ein-Tasten-Wechsel (z. B. `B`/`E`) ergänzen.

---

## Vorige Runden

- **2026-06-01, „modest-shannon" (A–E)** — 5 Befunde, alle erledigt (PR #135/#136); u. a. Decompression-Bomb-Handling und der Zauberstab-Lebenszyklus, den N1 nun im Fehlerpfad vervollständigt.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, #1–#15 erledigt, #4 verworfen (Fehlalarm).

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
