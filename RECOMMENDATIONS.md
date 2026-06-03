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

Gezielte Folge-Prüfung nach „modest-shannon", Schwerpunkt Speicher-, Lade- und CI-Pfad. **8 Punkte (N1–N8):** 7 behoben mit Regressionstests – gemergt über **PR #142** (N1), **#143** (N6, N8), **#144** (N4, N5) und **#148** (N2, N7); 1 bereits abgedeckt (N3). Baseline weiter grün: Ruff/mypy sauber, Suite grün.

### Erledigungsstand

| Status | Punkte |
|--------|--------|
| ✅ Erledigt | N1, N2, N4, N5, N6, N7, N8 |
| ⏳ Offen | – |

### Befunde

- **N1 🟠 — Zauberstab-Gate im Fehlerpfad freigeben** (PR #142). Folgebefund zu „modest-shannon"-B: Beim Bildwechsel bricht `_load_image_async` den Flood-Fill ab, der dann weder `finished` noch `error` emittiert. Der Gate-Reset lief nur über den Erfolgspfad (`apply_loaded_image`) – schlug das Laden fehl, blieb `_wand_busy` gesetzt und der Zauberstab auf dem alten Bild blockiert. Neue stille `reset_pending_wand()` direkt neben `cancel_flood_fill()`.
- **N2 🟡 — Rotations-Größenlimit** (PR #148). `rotate_image` (`image_ops.py`) dreht mit `expand=True`; der Megapixel-Schutz griff nur beim Laden (`Image.MAX_IMAGE_PIXELS`), nicht auf dem Ergebnis – eine knapp zulässige Vorlage konnte sich bei ~45° auf ~2× aufblähen. Jetzt schätzt `rotated_size()` die expand-Bounding-Box vorab; `apply_rotate` lehnt Ergebnisse über dem Limit mit Statusmeldung ab.
- **N3 ➖ — History-Speicherbudget** (bereits abgedeckt). `CanvasHistory` (`canvas_history.py`) erzwingt das Undo-Budget längst über `_trim()`/`_UNDO_MEMORY_LIMIT`, Redo ist über `_REDO_MAX_ENTRIES` gedeckelt. Kein Handlungsbedarf.
- **N4 🟢 — Endungs-Ehrlichkeit beim Speichern** (PR #144). `save_image_file` schrieb für unbekannte Endungen still PNG-Bytes; jetzt klare `ValueError`-Ablehnung, leere Endung bleibt PNG-Default.
- **N5 🟡 — Atomares Speichern** (PR #144). Direktes Schreiben ans Ziel zerstörte bei Abbruch die vorhandene Datei. Jetzt `mkstemp` → `os.replace` im Zielverzeichnis (Muster wie `qt_plugins._copy_if_needed`), mit Rechte-Erhalt und temp-Aufräumen.
- **N6 🟡 — `libgl1` in CI-Vollmatrix + Drift-Test** (PR #143). Die Vollmatrix installierte `libgl1` nicht (anders als die übrigen Qt-Paketquellen) → `import PyQt6` riskierte `libGL.so.1`. Ergänzt; neuer `test_ci_qt_packages.py` hält alle vier Paketlisten konsistent.
- **N7 🟢 — Eager-Imports** (PR #148). `workers.py` importierte `rembg` (zieht onnxruntime) auf Modulebene; da `main_window` `workers` lädt, fielen die Importkosten schon beim Start an – auch ohne KI-Nutzung. Jetzt `find_spec`-Probe für `REMBG_AVAILABLE` und Lazy-Import von `rembg` erst im Worker-Thread (Warmup/erster KI-Klick).
- **N8 🟢 — Veralteter `load_image`-Docstring** (PR #143). Nannte den Drop-Pfad als synchronen Aufrufer, obwohl Drag & Drop längst asynchron läuft. Korrigiert.

---

## Offene Empfehlungen

Aus der zweiten Analyse hervorgegangene, noch offene Verbesserungen (Produkt/Prozess):

- **O1 🟠 — App-Lokalisierung.** Die UI ist hartkodiert Deutsch; es gibt keine Laufzeit-i18n (kein `QTranslator`/`tr()`), obwohl die Doku in fünf Sprachen vorliegt. Statusmeldungen liegen bereits zentral (`status_messages.py`). Schrittweise via Qt Linguist (`.ts`) oder leichtgewichtige `QLocale`-Stringtabelle.
- **O2 🟡 — Linux-App / Paketierung.** Kein App-Bundle für Linux; Start nur via `python -m bgremover` aus einer venv. Ein installierbares Paket (AppImage/Flatpak/`.deb`) für **Raspberry Pi OS** und große Distributionen (Debian/Ubuntu/Fedora) senkt die Einstiegshürde für Nicht-Entwickler – analog zum macOS-`.app`-Bundle.
**✅ Erledigt:** O4/O6 — Ein-Tasten-Werkzeugwechsel (`W`/`B`/`E`/`L`) & plattformgerechte `Cmd`/`Ctrl`-Hinweise (PR #146, `test_tool_shortcuts.py`); O3 — Vollmatrix zusätzlich wöchentlich per Cron (PR #149); O5 — `ui_smoke`-Subset läuft in PR/Full-CI mit, volle qtbot-Suite bleibt nightly (PR #149).

## Umsetzungsplan in PR-Paketen (ab 2026-06-02)

- **PR 0 — Code-Härtung (N2 + N7).** ✅ Erledigt (PR #148). N2 — Megapixel-Gate auch auf das Rotationsergebnis (`rotated_size()` schätzt die Zielgröße vorab, `apply_rotate` lehnt über dem Limit mit Statusmeldung ab); N7 — `rembg` lazy importieren und `REMBG_AVAILABLE` per `find_spec` proben (das bestehende Warmup-Fehler-Handling deckt ein defektes Backend ab).
- **PR 1 — Tool-Shortcuts & Shortcut-Hinweise.** ✅ Erledigt (PR #146). O4 + O6: Ein-Tasten-Wechsel (`W`/`B`/`E`/`L`), Toolbar-Checked-State synchronisiert, Tooltips/README/Anleitung aktualisiert, Regressionstest für Shortcut-Wiring.
- **PR 2 — CI früher absichern.** ✅ Erledigt (PR #149). O3 — Vollmatrix zusätzlich wöchentlich (Cron); O5 — `ui_smoke`-Subset in PR/Full-CI, Nightly-UI als ausführliche Suite behalten.
- **PR 3 — i18n-Grundgerüst.** ✅ Erledigt. O1 vorbereitet: `bgremover.i18n` mit Runtime-Locale/Fallback, Deutsch als stabiler Default, erste zentrale String-Tabelle für Statusmeldungen, Menü, Toolbar, Tabs, Verlauf und Crop-Leiste; Regressionstests für Locale-Normalisierung, Fallback und UI-Wiring.
- **PR 4 — i18n-Rollout.** O1 nutzbar machen: mindestens Englisch als Runtime-Sprache, danach weitere vorhandene Dokusprachen, Smoke-Checks pro Locale.
- **PR 5 — Linux-Packaging Foundation.** O2 starten: Zielartefakt festlegen (AppImage/`.deb`/Flatpak), Desktop-Datei/Icon/AppStream-Metadaten und Linux-Build-Smoke.
- **PR 6 — Linux-Packaging erweitern.** O2 abrunden: Raspberry-Pi-OS-Variante, optionale zweite Paketform und Release-Workflow für Linux-Artefakte.

---

## Vorige Runden

- **2026-06-01, „modest-shannon" (A–E)** — 5 Befunde, alle erledigt (PR #135/#136); u. a. Decompression-Bomb-Handling und der Zauberstab-Lebenszyklus, den N1 nun im Fehlerpfad vervollständigt.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, #1–#15 erledigt, #4 verworfen (Fehlalarm).

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
