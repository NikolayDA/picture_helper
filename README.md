# BgRemover

Ein Bildbearbeitungs-Tool für macOS zum **Entfernen, Ersetzen und Bearbeiten von Hintergründen** — mit KI-basierter automatischer Freistellung, Zauberstab-Auswahl, Pinsel/Radierer, Zuschnitt in verschiedenen Formaten, Drehen, Spiegeln und Eckenrundung.

## Funktionen

- **🤖 KI-Hintergrundentfernung** über [rembg](https://github.com/danielgatis/rembg) – ein Klick, fertig.
- **🪄 Zauberstab** – wählt zusammenhängende Farbflächen per Flood-Fill (mit Toleranz-Slider).
- **🖌 Pinsel / Radiergummi** – Auswahl manuell aufmalen oder entfernen.
- **🎨 Hintergrund ersetzen** – Auswahl mit beliebiger Farbe füllen oder auf Transparenz setzen.
- **✂ Zuschnitt** mit Rule-of-Thirds-Raster: Kreis, 1:1, 16:9, 4:3, 3:2, 2:1, 14:9, 9:16, 3:4.
- **⟲ Drehen** in 90°-Schritten oder beliebigem Winkel; **↔ Spiegeln** horizontal/vertikal.
- **⬤ Ecken abrunden** mit einstellbarem Radius.
- **↩ Verlauf** mit Undo und Sprung zu beliebigem früheren Schritt.
- **📥 Drag & Drop** für Bilder direkt aufs Fenster.
- Speichern als **PNG** (mit Transparenz), **JPEG** (auf weißem Hintergrund), **WebP** oder **TIFF**.
- **⚙ Persistente Einstellungen** – Standard-Verzeichnisse und bevorzugtes Dateiformat bleiben gespeichert.

## Voraussetzungen

- **macOS** (das mitgelieferte App-Bundle nutzt macOS-spezifische Tools wie `iconutil`)
- **Python 3.10 oder neuer** (der Code nutzt PEP-604-Typannotationen
  wie `QThread | None` direkt in Signaturen — Python 3.9 schlägt fehl)
- Abhängigkeiten (`PyQt6`, `Pillow`, `numpy`, optional `rembg` für die
  KI-Funktion) werden über `pyproject.toml` installiert.

## Installation

**Empfohlen (macOS): App-Bundle bauen.** Das Skript legt automatisch
eine isolierte venv an, installiert alle Abhängigkeiten (inkl.
`onnxruntime` für die KI), behandelt Apple Silicon korrekt und erzeugt
ein eigenständiges `BgRemover.app`:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Beim venv-Hinweis mit **Enter** bestätigen. Danach `BgRemover.app`
(unter `~/Applications`) per Doppelklick starten — funktionsgleich zur
mitgelieferten **`BgRemover.command`**. Das Projekt darf in
`~/Documents` liegen bleiben (die App wird eigenständig gebaut).

**Alternativ direkt im Terminal** — auf modernem macOS in einer venv,
da System-Python `pip install` per PEP 668 blockiert:

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e ".[ai]"
python3 BgRemover.py
```

`.[ai]` zieht die KI-Abhängigkeiten (`rembg[cpu]` inkl. `onnxruntime`)
mit; ohne KI-Funktion reicht `python3 -m pip install -e .`.

> Eine ausführliche Anleitung — inklusive **Installation aus einem
> Branch** (zum Testen offener Pull Requests) und **Troubleshooting** —
> steht in **[INSTALL_MAC.md](INSTALL_MAC.md)**.

## Bedienung

1. **Bild öffnen** über `Datei → Öffnen` (⌘O) oder per Drag & Drop ins Fenster.
2. **Auswahl treffen** mit Zauberstab, Pinsel oder Radiergummi (Tab *🎯 Auswahl*).
   - `Shift+Klick` addiert zur Auswahl, `Ctrl+Klick` zieht ab.
3. **Hintergrund bearbeiten** (Tab *🖼 Hintergr.*): transparent machen oder Farbe ersetzen — oder direkt **KI** in der Werkzeugleiste.
4. **Bild transformieren** (Tab *⟲ Trans.*): drehen, spiegeln.
5. **Form & Zuschnitt** (Tab *⬤ Form*): Ecken abrunden oder Format zuschneiden — Rahmen verschieben/skalieren, dann ✓ Anwenden.
6. **Speichern** über `Datei → Speichern` (⌘S) als PNG, JPEG, WebP oder TIFF.

### Einstellungen

Über `Extras → Einstellungen…` (⌘,) lassen sich drei Nutzereinstellungen dauerhaft speichern:

| Einstellung | Beschreibung |
|---|---|
| Standard-Verzeichnis zum Öffnen | Startverzeichnis des Öffnen-Dialogs; leer = zuletzt verwendetes Verzeichnis |
| Standard-Verzeichnis für Export/Speichern | Startverzeichnis des Speichern-Dialogs; leer = zuletzt verwendetes Verzeichnis |
| Bevorzugtes Bilddateiformat | PNG, JPEG, WebP oder TIFF – erscheint als erste Option im Speichern-Dialog |

Die Einstellungen werden über **QSettings** persistent gespeichert und beim nächsten Programmstart automatisch wiederhergestellt.

### Tastatur-Kürzel

| Aktion | Shortcut |
|--------|----------|
| Bild öffnen | ⌘O |
| Bild speichern | ⌘S |
| Bild speichern unter… | ⇧⌘S |
| Rückgängig | ⌘Z |
| Wiederherstellen | ⇧⌘Z |
| 90° links drehen | ⌘← |
| 90° rechts drehen | ⌘→ |
| Auswahl aufheben | Esc |
| Auswahl invertieren | ⌘⇧I |
| Fit to View | ⌘0 |
| Einstellungen öffnen | ⌘, |

Im Datei-Menü gibt es zusätzlich ein Submenü **„Zuletzt geöffnet"** mit
den 10 zuletzt geladenen Bildern — der Zustand wird zusammen mit den
übrigen Einstellungen über QSettings persistiert.

## Entwicklung & Tests

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
pip install -e ".[test]"
pytest
```

Die Test-Suite läuft headless (Qt-Platform `offscreen`) und prüft die
Bildoperationen, die Crop-Geometrie und die Speicher-Logik. Bei jedem
Push und Pull-Request wird sie zusätzlich automatisch auf Linux und
macOS unter Python 3.10 und 3.12 via GitHub Actions ausgeführt.

Code-Style-Check und statische Typprüfung (beide auch im CI):

```bash
ruff check BgRemover.py tests
mypy
```

## Architektur (Kurzüberblick)

BgRemover ist eine Einzeldatei-Anwendung (`BgRemover.py`):

- **`ImageCanvas`** (QGraphicsView) hält den Bildzustand, die Auswahl­maske,
  Undo-/Redo-Stapel und die Werkzeuge (Zauberstab, Pinsel, Lasso, Crop).
- **`MainWindow`** baut Toolbar, das rechte Tab-Panel (vier `_build_tab_*`-
  Builder), Menü und verbindet alles mit dem Canvas.
- **Worker** (`ImageLoadWorker`, `AIWorker`, `RembgWarmupWorker`) laufen in
  eigenen `QThread`s; `_launch_worker()` kapselt den Thread-Lebenszyklus.
- Ein monotoner **Versionszähler** im Canvas verwirft veraltete KI-Ergebnisse,
  falls zwischenzeitlich ein anderes Bild geladen wurde.
- Der Undo-Stapel ist nicht über `maxlen`, sondern über ein
  **Speicherlimit** (`_UNDO_MEMORY_LIMIT`) begrenzt; eine laufende
  Byte-Summe evakuiert die ältesten Einträge.

## Bekannte Einschränkungen

- **Maximale Bildgröße: 40 Megapixel.** Größere Bilder werden mit einer
  Statusmeldung abgelehnt. Die Zauberstab-Auswahl (Flood-Fill) läuft
  synchron im UI-Thread; jenseits dieser Grenze würde selbst die
  vektorisierte Variante spürbar verzögern. Pillow ist zusätzlich gegen
  „Decompression-Bomb"-Bilder abgesichert.
- Der **App-Bundle-Build** ist macOS-spezifisch; unter Linux/Windows
  läuft die Anwendung über den direkten `python BgRemover.py`-Start.

## Log-Datei

Beim Programmstart wird eine Log-Datei `bgremover.log` im
plattformspezifischen App-Datenverzeichnis angelegt
(macOS: `~/Library/Application Support/BgRemover/`,
Linux: `~/.local/share/BgRemover/`). Sie enthält Stacktraces und
Status-Meldungen und ist bei Problemen die erste Anlaufstelle.

## Lizenz

BgRemover steht unter der **GNU General Public License v3.0 oder
später** (`GPL-3.0-or-later`) — siehe [LICENSE](LICENSE).

Eine vollständige Auflistung aller verwendeten Bibliotheken, Werkzeuge
und Assets samt Lizenzen steht in **[RESOURCES.md](RESOURCES.md)**.

> **Hinweis zu PyQt6:** Die GUI-Abhängigkeit PyQt6 (Riverbank) ist
> selbst GPL-v3-lizenziert (oder kommerziell). Die GPL-3.0 wurde
> bewusst gewählt, damit die verteilte Anwendung — insbesondere das
> gebündelte `BgRemover.app` — lizenzkonform ist. Wer ein permissives
> Modell (MIT/Apache-2.0) anstrebt, müsste PyQt6 durch das LGPL-
> lizenzierte **PySide6** ersetzen.
