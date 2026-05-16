# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Muss behoben werden – führt zu Fehlern, Abstürzen oder Inkonsistenzen |
| 🟠 | Hoch | Sollte bald behoben werden – beeinträchtigt Zuverlässigkeit oder Wartbarkeit erheblich |
| 🟡 | Mittel | Empfohlen – verbessert Code-Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optional – Polishing, ergänzende Verbesserungen |

---

## Priorisierte Zusammenfassung

| # | Empfehlung | Priorität | Aufwand |
|---|-----------|-----------|---------|
| 1 | ~~Python-Versionskonflikt bei Type Hints~~ | ✅ Behoben | – |
| 2 | ~~Breites Exception-Catching bei rembg-Import~~ | ✅ Behoben | – |
| 3 | ~~Race Conditions in Worker-Threads~~ | ✅ Behoben | – |
| 4 | ~~Bildgrössen-Validierung beim Laden~~ | ✅ Behoben | – |
| 5 | ~~Speicherverbrauch Undo-Stack~~ | ✅ Behoben | – |
| 6 | ~~God-Klassen aufteilen~~ | ✅ Behoben | – |
| 7 | ~~Überlange Methoden refaktorieren~~ | ✅ Behoben | – |
| 8 | ~~Magic Numbers ersetzen~~ | ✅ Behoben | – |
| 9 | ~~Tests für Thread-Szenarien~~ | ✅ Behoben | – |
| 10 | ~~Rückgabe-Type-Hints ergänzen~~ | ✅ Behoben | – |
| 11 | Docstrings ergänzen | 🟢 Niedrig | Gering |
| 12 | Log-Dateipfad plattformunabhängig | 🟢 Niedrig | Gering |
| 13 | Thread-Boilerplate deduplizieren | 🟢 Niedrig | Gering |

---

## Empfehlungen im Detail

### ✅ 1. Python-Versionskonflikt bei Type Hints *(behoben)*

**Datei**: `pyproject.toml`

`requires-python` auf `>=3.10` angehoben, `ruff target-version` auf `py310` aktualisiert. Die im Code verwendete `X | Y`-Syntax (PEP 604) ist damit durch die deklarierten Mindestanforderungen abgedeckt.

---

### ✅ 2. Zu breites Exception-Catching beim rembg-Import *(behoben)*

**Datei**: `BgRemover.py` (Zeile 41)

`except BaseException:` ersetzt durch `except (ImportError, RuntimeError, OSError, SystemExit):`. `KeyboardInterrupt` und andere kritische Signale werden nicht mehr abgefangen. `SystemExit` bleibt explizit enthalten, da bekannte rembg/onnxruntime-Versionen diesen beim Import auslösen können.

---

### ✅ 3. Race Conditions bei Worker-Threads *(behoben)*

**Datei**: `BgRemover.py`

- Neuer `_launch_worker()`-Helper in `MainWindow` kapselt den identischen Thread-Boilerplate (war dreifach dupliziert). Alle drei Flows (Image Load, AI, Warmup) nutzen ihn jetzt.
- Stale-Check in `_on_ai_done()` verwendet jetzt `_canvas._version` (monotoner Integer-Zähler, der bei jedem Bildwechsel in `apply_loaded_image()` erhöht wird) statt dem fragilen `is`-Objektidentitäts-Vergleich. `_ai_input_version` in `MainWindow` speichert den Wert zum KI-Start.

---

### ✅ 4. Fehlende Bildgrössen-Validierung beim Laden *(behoben)*

**Datei**: `BgRemover.py`

Konstante `_MAX_MEGAPIXELS = 100` eingeführt. Prüfung nach dem Lazy-`Image.open()` an zwei Stellen:
- `ImageLoadWorker.run()`: emittiert `error`-Signal mit Fehlermeldung (Dateidialog-Pfad)
- `ImageCanvas.load_image()`: emittiert `statusMsg` und bricht ab (Drag-&-Drop-Pfad)

---

### ✅ 5. Hoher Speicherverbrauch des Undo-Stacks *(behoben)*

**Datei**: `BgRemover.py`

Konstante `_UNDO_MEMORY_LIMIT = 256 MB` eingeführt. Der Undo-Stack hat kein hartes `maxlen` mehr – stattdessen wird nach jedem Push die Gesamtgrösse (geschätzt als `width × height × 4` Bytes pro RGBA-Image) berechnet und älteste Einträge werden entfernt, solange das Limit überschritten ist.

---

### ✅ 6. God-Klassen aufteilen *(behoben)*

**Datei**: `BgRemover.py`

Die 6 nested-Helper-Funktionen aus `_build_right_panel()` (`sec`, `lbl`, `hdivider`, `scroll_tab`, `btn`, `slider_row`) wurden als `@staticmethod`-Klassenmethoden von `MainWindow` extrahiert: `_make_section`, `_make_label`, `_make_hdivider`, `_make_scroll_tab`, `_make_panel_btn`, `_make_slider`. `_TAB_STYLE` wurde als Klassenattribut ausgelagert.

---

### ✅ 7. Überlange Methoden refaktorieren *(behoben)*

**Datei**: `BgRemover.py`

Die 8 Icon-Zeichenzweige aus `make_tool_icon()` (175 Zeilen, if-elif-Kaskade) wurden als eigene Modulfunktionen extrahiert: `_draw_wand_icon`, `_draw_brush_icon`, `_draw_eraser_icon`, `_draw_ai_icon`, `_draw_open_icon`, `_draw_save_icon`, `_draw_undo_icon`, `_draw_restore_icon`. `make_tool_icon()` ist jetzt ein schlanker Dispatcher über ein `dict`.

---

### ✅ 8. Magic Numbers durch benannte Konstanten ersetzen *(behoben)*

**Datei**: `BgRemover.py`

Neuer Konstanten-Block im Modulkopf:
- UI-Layout: `_TOOLBAR_WIDTH`, `_TOOLBAR_BTN_SIZE`, `_TOOLBAR_ICON_SIZE`, `_RIGHT_PANEL_WIDTH`, `_CROP_BAR_HEIGHT`, `_HISTORY_LIST_H`, `_COLOR_BTN_SIZE`, `_TAB_ICON_PX`, `_WINDOW_MIN_W/H`
- Canvas-Defaults: `_DEFAULT_TOLERANCE`, `_DEFAULT_BRUSH_RADIUS`, `_ZOOM_FACTOR`
- Overlay-Farbe: `_OVERLAY_COLOR`

Alle Verwendungsstellen im Code wurden auf die Konstanten umgestellt.

---

### ✅ 9. Tests für Worker-Fehlerpfade *(behoben)*

**Datei**: `tests/test_workers.py` (neu, 9 Tests)

Neue Tests:
- `ImageLoadWorker`: fehlende Datei, korrupte Datei, überdimensioniertes Bild (via Mock)
- `ImageLoadWorker`: Normalfall (kein Fehler erwartet)
- `ImageCanvas.load_image()`: überdimensioniertes Bild (Drag-&-Drop-Pfad)
- `AIWorker`: Fehlersignal bei `rembg_remove`-Exception, Erfolgsfall (via Mock)
- Canvas `_version`-Zähler: inkrementiert bei `apply_loaded_image`, unverändert bei Undo

---

### ✅ 10. Rückgabe-Type-Hints ergänzt *(behoben)*

**Datei**: `BgRemover.py`

77 Funktionen und Methoden ohne Rückgabe-Annotation wurden mit `-> None` (oder spezifischem Typ) versehen. Ausserdem wurde `QFont` zum PyQt6-Import hinzugefügt (benötigt für `_text_font() -> QFont`).

---

### 🟢 11. Fehlende Docstrings bei Hilfsmethoden

**Datei**: `BgRemover.py` (Zeilen 107–184, 1811–1905)

**Problem**: Cursor-Generatoren (`make_wand_cursor`, `make_brush_cursor`, `make_eraser_cursor`) und intern definierte Widget-Helfer (`sec()`, `lbl()`, `btn()`) haben keine Docstrings.

**Lösung**: Kurze Ein-Zeiler-Docstrings ergänzen, die Zweck und Rückgabewert beschreiben.

---

### 🟢 12. Log-Dateipfad plattformunabhängig machen

**Datei**: `BgRemover.py` (Zeile ~2561)

**Problem**: Die Log-Datei landet als `~/.bgremover.log` im Home-Verzeichnis. Auf Linux und Windows gibt es dafür Konventionen (`~/.local/share/`, `%APPDATA%`), die nicht eingehalten werden.

**Lösung**: Qt-Standard-Pfade nutzen:
```python
log_path = Path(QStandardPaths.writableLocation(
    QStandardPaths.StandardLocation.AppDataLocation)) / "bgremover.log"
```

---

### 🟢 13. Duplizierter Thread-Boilerplate deduplizieren

**Datei**: `BgRemover.py` (Zeilen 2333–2351, 2364–2377, 2495–2509)

**Problem**: Dasselbe Muster zum Erstellen und Verbinden von QThread-Workern wird dreimal nahezu identisch wiederholt.

**Lösung**: Gemeinsame Hilfsmethode in `MainWindow`:
```python
def _start_worker_thread(self, worker, on_done, on_error=None):
    thread = QThread(self)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.done.connect(on_done)
    if on_error:
        worker.error.connect(on_error)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread
```
