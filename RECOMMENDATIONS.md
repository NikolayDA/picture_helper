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
| 11 | ~~Docstrings ergänzen~~ | ✅ Behoben | – |
| 12 | ~~Log-Dateipfad plattformunabhängig~~ | ✅ Behoben | – |
| 13 | ~~Thread-Boilerplate deduplizieren~~ | ✅ Behoben | – |

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

### ✅ 11. Fehlende Docstrings bei Hilfsmethoden *(behoben)*

**Datei**: `BgRemover.py`

Ein-Zeiler-Docstrings zu `_make_label`, `_make_hdivider`, `_make_panel_btn` und `_make_slider` ergänzt. Die Cursor-Generatoren (`make_wand_cursor`, `make_brush_cursor`, `make_eraser_cursor`) hatten bereits Docstrings.

---

### ✅ 12. Log-Dateipfad plattformunabhängig machen *(behoben)*

**Datei**: `BgRemover.py`

`QStandardPaths` zu den PyQt6-Importen hinzugefügt. Log-Pfad von `Path.home() / ".bgremover.log"` auf `QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) / "bgremover.log"` umgestellt (Linux: `~/.local/share/BgRemover/`, macOS: `~/Library/Application Support/BgRemover/`).

---

### ✅ 13. Duplizierter Thread-Boilerplate deduplizieren *(behoben)*

**Datei**: `BgRemover.py`

`_launch_worker()`-Helper wurde bereits als Teil von Fix #3 (Race Conditions) eingeführt. Alle drei Worker-Flows (Image Load, AI, Warmup) nutzen ihn seither.

---

## Runde 2 – Folge-Review (Code, Tests, Doku, Lizenz)

> Korrektur zur Runde 1: Die Punkte **#6 (God-Klassen)** und **#8 (Magic
> Numbers)** waren als ✅ markiert, traten aber nur _teilweise_ zu
> (`MainWindow`/`_build_right_panel` blieb ~300 Zeilen; etliche
> Stylesheet-/Layout-Zahlen blieben inline). Runde 2 adressiert die
> verbleibenden Punkte.

| # | Empfehlung | Priorität | Status |
|---|-----------|-----------|--------|
| R1 | Logging-Setup: Aufruf vor `QApplication`, Verzeichnis nicht angelegt | 🔴 | ✅ Behoben |
| R2 | Flood-Fill blockiert UI; 100-MP-Limit zu hoch | 🟠 | ✅ Behoben |
| R3 | Drag&Drop / „Zuletzt geöffnet" umgingen den Async-Worker | 🟠 | ✅ Behoben |
| R4 | Kapselungsbruch (`_pil`/`_version`/`_img_item`/`_cx…`) | 🟡 | ✅ Behoben |
| R5 | `undo_to` inkonsistent (nicht wiederherstellbar) | 🟡 | ✅ Behoben |
| R6 | `MainWindow` God-Object / `_build_right_panel` | 🟡 | ✅ Behoben |
| R7 | Kein Typecheck in CI | 🟡 | ✅ Behoben |
| R8 | `pyproject` ignorierte `F401` global | 🟢 | ✅ Behoben |
| R9 | `make_tool_icon`: Import in Schleife, stiller `except` | 🟢 | ✅ Behoben |
| R10 | `_apply_pil` summierte Undo-Stack O(n) pro Aktion | 🟢 | ✅ Behoben |
| R11 | Kein Decompression-Bomb-Schutz | 🟡 | ✅ Behoben |
| R12 | Testlücken (Undo-Eviction, Geometrie, Lasso, Drop) | 🔴/🟠 | ✅ Behoben |
| R13 | Doku: falsche Python-Version, fehlende Lizenz | 🟠 | ✅ Behoben |

**R1** — Logging in `_setup_logging()` ausgelagert; wird in `__main__`
**nach** `QApplication` + `setApplicationName/​setOrganizationName`
aufgerufen. Zielverzeichnis wird via `mkdir(parents=True, exist_ok=True)`
angelegt (Fallback `~/.bgremover`).

**R2** — `flood_fill` ist vektorisiert (Ähnlichkeitsmaske in wenigen
NumPy-Operationen, danach Region-Wachstum); `_MAX_MEGAPIXELS` von 100 → 40.

**R3** — Neues Signal `ImageCanvas.loadRequested`; `dropEvent` und
`_open_recent` laufen jetzt über `_load_image_async` (Worker-Pfad).
`load_image` bleibt als synchroner Pfad für Tests/Drop-Fallback.

**R4** — Öffentliche Accessors: `ImageCanvas.image/has_image/version/
fit_to_view()` und `CropOverlayItem.top_left/size`. `MainWindow` und
`ImageCanvas` greifen nicht mehr cross-class auf Private zu.

**R5** — `undo_to()` verhält sich wie mehrfaches `undo()` (jeder Schritt
auf den Redo-Stapel) und ist damit per `redo()` wiederherstellbar; zudem
Crop-Guard wie bei `undo()`.

**R6** — `_build_right_panel()` ist ein schlanker Dispatcher; vier
`_build_tab_selection/background/transform/shape`-Builder hängen je einen
Tab an (Tab-Index aus `addTab()`).

**R7** — `mypy` in `pyproject.toml` konfiguriert (pragmatisch: Qt-Override-
und Tuple-Lambda-Rauschen via `disable_error_code` stummgeschaltet) und
als CI-Schritt ergänzt.

**R8/R9/R10/R11** — `F401`-Ignore entfernt, zwei ungenutzte Importe
gelöscht; `make_tool_icon` nutzt den Modul-`Image`-Import und loggt
Fehlschläge mit `logger.debug`; laufende Undo-Byte-Summe `_undo_bytes`
(O(1)); `Image.MAX_IMAGE_PIXELS` an `_MAX_MEGAPIXELS` gekoppelt.

**R12** — Neue Tests (81 → 108): Undo-Speicherlimit-Eviction +
Byte-Tracking, `tests/test_geometry.py` (Drehen/Spiegeln/Ecken/Crop),
Lasso + `_paint_brush` + `apply_remove/replace`-Erfolgsfall,
`tests/test_drop_and_history.py` (Async-Drop, `undo_to`-Redo),
`_setup_logging`-Verzeichnisanlage.

**R13** — README/INSTALL_MAC: Python **3.10+**; README um Architektur,
bekannte Einschränkungen, korrekten Log-Pfad und **Lizenz-Abschnitt**
erweitert; `LICENSE` (GPL-3.0) ergänzt; `pyproject.toml` mit
`license`/`authors`/`urls`/`classifiers`. Lizenzempfehlung:
**GPL-3.0-or-later** (passt zur GPL-Pflicht von PyQt6; permissiv nur mit
Wechsel auf PySide6).

---

## Runde 3 – Vor der Feature-Erweiterung

> Zwei Optimierungsrunden sind abgeschlossen; Runde 3 sammelt die vor
> einer geplanten Feature-Erweiterung sinnvollen, risikoarmen Cleanups.
> Empfehlung **#1 (Monolith → Paket)** ist bewusst zurückgestellt: hohe
> Priorität, aber auch hoher Aufwand/hohes Risiko und Widerspruch zur
> dokumentierten Einzeldatei-Designentscheidung — eine separate
> Entscheidung. Die Status-Spalte verweist auf den umsetzenden PR.

| # | Empfehlung | Priorität | Aufwand | Status |
|---|-----------|-----------|---------|--------|
| 1 | Monolith → Paket (`bgremover/` mit Modulen) | 🟠 Hoch | Hoch | Offen |
| 2 | ~~`save_image()` ohne Fehlerbehandlung~~ | 🟡 Mittel | Niedrig | ✅ #48 |
| 3 | ~~Zustands-Duplizierung in `undo/redo/undo_to/restore_original/_apply_pil`~~ | 🟡 Mittel | Niedrig | ✅ #52 |
| 4 | ~~Verstreute Inline-Stylesheets, kein Theme-Modul~~ | 🟡 Mittel | Mittel | ✅ #53 |
| 5 | ~~Kein SessionStart-Hook für Claude Code on the web~~ | 🟡 Mittel | Niedrig | ✅ #51 |
| 6 | Wiederholte „Kein Bild geladen"-Guards (~8×) | 🟢 Niedrig | Niedrig | Offen |
| 7 | Worker-Boilerplate (try/except/log/emit) → Basisklasse | 🟢 Niedrig | Niedrig | Offen |
| 8 | ~~`CHANGELOG [Unreleased]` mitpflegen~~ | 🟢 Niedrig | Niedrig | ✅ laufend |
| 9 | `mypy` sehr permissiv (7 disabled codes) | 🟢 Niedrig | Mittel | Offen |

**#1** — `BgRemover.py` ist weiterhin eine Einzeldatei (~3000 Zeilen:
Helfer, Worker, Canvas, UI, Dialoge, Logging, Main). Größter Hebel für
Feature-Wachstum, aber höchstes Risiko (Risiko: Hoch) und Widerspruch
zur dokumentierten Einzeldatei-Entscheidung. **Offen — bewusst
zurückgestellt**, separate Designentscheidung nötig.

**#2** — Behoben in **PR #48**: `save_image()` gibt `bool` zurück und
kapselt die Schreiboperationen in `try/except` (Logging + Statusmeldung),
konsistent zu `apply_remove/replace`; „Speichern unter…" merkt
fehlgeschlagene Pfade nicht mehr als Quick-Save-Ziel
(`BgRemover.py:1080–1113`).

**#3** — Behoben in **PR #52** (ursprünglich #49, nach Merge-Konflikt
sauber neu aufgelegt): der identische Bildzustands-Block ist in die
Helfer `_set_image_state()` / `_emit_history()` zusammengeführt;
Verhalten unverändert (`BgRemover.py:877`, `:891`).

**#4** — Behoben in **PR #53** (ursprünglich #50): zentrale
`_Theme`-Farbpalette, die wiederverwendeten Templates referenzieren sie
(byte-identisch verifiziert, 218 Stylesheets, kein visueller
Unterschied). Tote Konstanten `BTN_STYLE`/`GRP_STYLE` entfernt
(`BgRemover.py:1547`).

**#5** — Behoben in **PR #51**: synchroner `SessionStart`-Hook
(`.claude/hooks/session-start.sh`, Git-Mode 100755) installiert die
Qt-Systembibliotheken + das Projekt und setzt `QT_QPA_PLATFORM=offscreen`
persistent; registriert in `.claude/settings.json`.

**#6** — **Offen.** Der „kein Bild geladen"-Frühausstieg wiederholt
sich in ~8 Methoden; ein kleiner Guard-Helfer würde das bündeln.

**#7** — **Offen.** Die drei Worker-Flows teilen sich
`try/except/log/emit`-Boilerplate; eine optionale Basisklasse würde die
Wiederholung reduzieren.

**#8** — Eingehalten: Die Runde-3-PRs #48/#52/#53 pflegen jeweils den
`CHANGELOG [Unreleased]`-Abschnitt; dieser Eintrag dokumentiert
zusätzlich Runde 3 selbst. Laufende Praxis statt Einzel-PR.

**#9** — **Offen.** `mypy` ist in `pyproject.toml` pragmatisch entschärft
(7 `disable_error_code`); schrittweises Verschärfen verbessert die
Typsicherheit (Aufwand/Risiko: Mittel).

---

## Runde 4 – Standortbestimmung & nächster Schritt

> Stand der Analyse: `ruff` sauber, `mypy` sauber, **140 Tests grün**
> (16 UI-Tests bewusst deselektiert). Die Code-Qualität ist hoch –
> Runde 4 priorisiert daher, **was als Nächstes konkret anzugehen ist**,
> statt neue Mängel zu suchen.

| # | Empfehlung | Priorität | Aufwand | Status |
|---|-----------|-----------|---------|--------|
| 1 | ~~Release-Schnitt 2.1.0 + git-Tag~~ | 🟠 Hoch | Niedrig | ✅ Umgesetzt (Tag nach Merge) |
| 2 | ~~Guard-Helfer „Kein Bild geladen" (Runde 3 #6)~~ | 🟢 Niedrig | Niedrig | ✅ Umgesetzt |
| 3 | ~~Worker-Basisklasse (Runde 3 #7)~~ | 🟢 Niedrig | Niedrig | ✅ Umgesetzt |
| 4 | `mypy` schrittweise verschärfen (Runde 3 #9) | 🟢 Niedrig | Mittel | 🟢 Schritt 1 umgesetzt |
| 5 | Monolith → Paket (Runde 3 #1) | 🟠 Hoch | Hoch | Zurückgestellt |

### ✅ 1. Release-Schnitt 2.1.0 + git-Tag *(umgesetzt)*

**Umgesetzt in diesem PR:** `pyproject.toml` und der
`__version__`-Fallback (`BgRemover.py`) auf `2.1.0` gehoben; der
`[Unreleased]`-Block in `CHANGELOG.md` (+ i18n en/es/fr/uk/zh) als
`[2.1.0] – 2026-05-19` datiert und ein frischer leerer
`[Unreleased]`-Block angelegt. Der `git tag v2.1.0` wird **bewusst
nicht** auf dem Feature-Branch gesetzt, sondern gehört nach dem Merge
auf den Merge-Commit in `main` (siehe PR-Beschreibung).

**Befund (zur Nachvollziehbarkeit):** Es existierte **kein einziger
git-Tag** (`git tag -l` ist
leer), obwohl der CHANGELOG eine „erste öffentlich getaggte
Veröffentlichung 2.0.0" behauptet. Seit 2.0.0 hat der
`[Unreleased]`-Block substantielle Änderungen gesammelt (PR #48
Save-Fehlerbehandlung, #52 Zustands-Dedup, #53 `_Theme`,
INSTALL_LINUX-Doku, #55 lokaler Test-Runner). `pyproject.toml`
(`version = "2.0.0"`) und der `__version__`-Fallback
(`BgRemover.py:51`) stehen weiterhin auf `2.0.0` – der ausgelieferte
Stand ist also nicht von 2.0.0 unterscheidbar.

**Warum zuerst:** geringster Aufwand bei maximaler Klarheit. Ohne
Versions-/Tag-Schnitt lässt sich nicht nachvollziehen, welcher Code
ausgeliefert wurde – das blockiert jede saubere Feature-Iteration.

### ✅ 2. Guard-Helfer „Kein Bild geladen" *(umgesetzt, Runde 3 #6)*

Der byte-identische Frühausstieg `if self._pil is None:
self.statusMsg.emit("Kein Bild geladen"); return` der fünf
`ImageCanvas`-Methoden `apply_round_corners`, `apply_rotate`,
`apply_flip`, `start_crop_circle`, `start_crop_ratio` ist im Decorator
`@_requires_image` zusammengefasst. Verhalten unverändert (140 Unit-
+ 16 UI-Tests grün). Die drei `MainWindow`-`has_image`-Guards bleiben
bewusst inline: abweichende Meldungen und reihenfolgeabhängige
Zweitprüfungen – eine Bündelung brächte dort mehr Risiko als Nutzen.

### ✅ 3. Worker-Basisklasse *(umgesetzt, Runde 3 #7)*

`AIWorker` und `ImageLoadWorker` erben jetzt von der Basisklasse
`_Worker`, die den identischen
`try/except → logger.exception → error.emit`-Ablauf kapselt;
Unterklassen implementieren nur noch `_work()`. `RembgWarmupWorker`
bleibt bewusst eigenständig (kein `error`-Signal, `finished` stets im
`finally` – anderer Kontrakt).

### 🟢 4. `mypy` schrittweise verschärfen *(Runde 3 #9 – Schritt 1 umgesetzt)*

`disable_error_code` von **8 auf 6** reduziert: `index` und `operator`
sind bereits sauber (je **0 Fehler**, gemessen) und daher in
`pyproject.toml` reaktiviert – ohne Code-Änderung, ohne Risiko.
Gemessene Roadmap für die verbleibenden Codes (ein Schritt pro PR, wie
empfohlen):

| Code | Offene Fehler | Charakter |
|------|---------------|-----------|
| `arg-type` | 2 | None-Verengung durch Guards/Decorator |
| `attr-defined` | 2 | dynamisches `QThread._worker`, `QObject.run` |
| `func-returns-value` | 4 | Void-Rückgabe in UI-Lambda-Tupeln |
| `assignment` | 4 | gemischte Zuweisungstypen |
| `override` | 7 | Qt-Override-Signaturen |
| `union-attr` | 67 | sehr breit – zuletzt angehen |

Nächster sinnvoller Schritt: `arg-type` oder `attr-defined` (je 2 kleine,
echte Verbesserungen). Aufwand/Risiko der Restschritte: Mittel.

### 🟠 5. Monolith → Paket *(Runde 3 #1, bewusst zurückgestellt)*

`BgRemover.py` ist mit **3003 Zeilen** weiter eine Einzeldatei.
Größter Hebel für Feature-Wachstum, aber höchstes Risiko und im
Widerspruch zur dokumentierten Einzeldatei-Designentscheidung. Bleibt
eine bewusste, separate Architekturentscheidung – spätestens vor der
nächsten größeren Feature-Erweiterung erneut abzuwägen. Die Quick-Wins
#2/#3 verkleinern die Datei bereits leicht und bereiten einen späteren
Schnitt vor.
