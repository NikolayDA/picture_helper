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
| 6 | God-Klassen aufteilen | 🟡 Mittel | Hoch |
| 7 | Überlange Methoden refaktorieren | 🟡 Mittel | Mittel |
| 8 | Magic Numbers ersetzen | 🟡 Mittel | Gering |
| 9 | Tests für Thread-Szenarien | 🟡 Mittel | Mittel |
| 10 | Rückgabe-Type-Hints ergänzen | 🟡 Mittel | Gering |
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

### 🟡 6. God-Klassen aufteilen

**Datei**: `BgRemover.py` (MainWindow ab Zeile 1583, ImageCanvas ab Zeile 630)

**Problem**:
- `MainWindow` (~1.000 Zeilen, 60+ Methoden) vereint UI-Aufbau, Menüverwaltung, Threading, Datei-I/O, Einstellungen und Bildoperationen in einer Klasse
- `ImageCanvas` (~660 Zeilen, 40+ Methoden) enthält Bildmanipulation, Masken, Events, Undo/Redo und I/O

**Lösung**: Schrittweise Extraktion einzelner Verantwortlichkeiten:
- `HistoryManager` für Undo/Redo-Stack
- `ImageIO` für Laden/Speichern
- `SelectionManager` für Masken-Operationen
- `RightPanelBuilder` für den UI-Aufbau des rechten Panels

---

### 🟡 7. Überlange Methoden refaktorieren

**Datei**: `BgRemover.py`

**Problem**: Mehrere Methoden sind deutlich zu lang und schwer testbar:
- `make_tool_icon()`: 175 Zeilen, tiefe if-elif-Kaskaden (Zeilen 191–366)
- `_build_right_panel()`: 445 Zeilen mit 6 intern definierten Hilfsfunktionen (Zeilen 1778–2223)
- `_build_menu()`: 93 Zeilen repetitiver Menüerstellung (Zeilen 2226–2319)

**Lösung**:
- `make_tool_icon()` → Icon-Registry als `dict` von Callables pro Icon-Name
- `_build_right_panel()` → Einzelne Methoden pro Tab (`_build_selection_tab()`, `_build_bg_tab()`, etc.)
- Interne Hilfsfunktionen (`sec()`, `btn()`, etc.) als Klassen- oder Modulmethoden extrahieren

---

### 🟡 8. Magic Numbers durch benannte Konstanten ersetzen

**Datei**: `BgRemover.py` (30+ Vorkommen, u.a. Zeilen 98, 565, 603, 1591, 1635, 1680, 1780, 2052)

**Problem**: Zahlreiche hardcodierte Werte ohne semantische Benennung:
- Farben: `[220, 60, 60, 130]` (Auswahloverlay), `(255, 255, 255)` (Weiss)
- UI-Grössen: `340` (rechtes Panel), `66` (Toolbar-Breite), `46` (Crop-Bar-Höhe), `160` (History-Liste)
- Fenstergrösse: `(1100, 720)`, Undo-Limit: `20`

**Lösung**: Konstanten-Block am Anfang der Datei:
```python
_OVERLAY_COLOR       = (220, 60, 60, 130)
_TOOLBAR_WIDTH       = 66
_RIGHT_PANEL_WIDTH   = 340
_UNDO_STACK_SIZE     = 20
_WINDOW_MIN_SIZE     = (1100, 720)
```

---

### 🟡 9. Fehlende Tests für Thread-Szenarien und Fehlerpfade

**Datei**: `tests/test_async_load.py`, neue Datei `tests/test_workers.py`

**Problem**: Die Test-Suite deckt folgende Szenarien nicht ab:
- Gleichzeitige Lade- und KI-Anfragen (Race Conditions)
- Worker-Fehlersignale (`AIWorker.error`, `ImageLoadWorker.error`)
- `dropEvent()` mit ungültigen Dateitypen oder fehlenden Dateien
- Beschädigte oder fehlende QSettings-Dateien

**Lösung**:
- `unittest.mock` für Worker-Fehlerszenarien einsetzen
- Parametrisierte Tests für alle unterstützten Exportformate (PNG, JPEG, WebP, TIFF)
- Concurrent-Load-Szenario testen

---

### 🟡 10. Fehlende Rückgabe-Type-Hints

**Datei**: `BgRemover.py` (Zeilen 52, 64, 96, 189, 554)

**Problem**: Viele Funktionen haben Eingabe-Typ-Hints, aber keine Rückgabe-Annotationen:
- `pil_to_qpixmap(img: Image.Image)` → fehlt `-> QPixmap`
- `make_checker_brush(size: int = 14)` → fehlt `-> QBrush`
- `mask_to_overlay(...)` → fehlt `-> QPixmap`
- `crop_rect()` in `CropOverlayItem` → fehlt `-> QRectF`

**Lösung**: Rückgabe-Typ-Hints für alle öffentlichen Funktionen und Methoden ergänzen.

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
