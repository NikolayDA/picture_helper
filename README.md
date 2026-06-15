**Deutsch** · [English](docs/i18n/en/README.md) · [Español](docs/i18n/es/README.md) · [Français](docs/i18n/fr/README.md) · [Українська](docs/i18n/uk/README.md) · [简体中文](docs/i18n/zh/README.md)

# BgRemover

[![CI](https://github.com/NikolayDA/picture_helper/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/NikolayDA/picture_helper/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/NikolayDA/picture_helper/branch/main/graph/badge.svg)](https://codecov.io/gh/NikolayDA/picture_helper)
[![License Check](https://github.com/NikolayDA/picture_helper/actions/workflows/license-check.yml/badge.svg?branch=main)](https://github.com/NikolayDA/picture_helper/actions/workflows/license-check.yml)
[![Latest release](https://img.shields.io/github/v/release/NikolayDA/picture_helper)](https://github.com/NikolayDA/picture_helper/releases/latest)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/github/license/NikolayDA/picture_helper)](https://github.com/NikolayDA/picture_helper/blob/main/LICENSE)
[![Platform: macOS | Linux](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)](https://github.com/NikolayDA/picture_helper)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

Ein Bildbearbeitungs-Tool für macOS und Linux zum **Entfernen, Ersetzen und Bearbeiten von Hintergründen** — mit KI-basierter automatischer Freistellung, Zauberstab-Auswahl, Pinsel/Radierer, Polygon-Lasso, Zuschnitt in verschiedenen Formaten, Drehen, Spiegeln und Eckenrundung.

## Funktionen

- **🤖 KI-Hintergrundentfernung** über [rembg](https://github.com/danielgatis/rembg) – ein Klick, fertig.
- **🪄 Zauberstab** – wählt zusammenhängende Farbflächen per Flood-Fill (mit Toleranz-Slider).
- **🖌 Pinsel / Radiergummi** – Auswahl manuell aufmalen oder entfernen.
- **➰ Polygon-Lasso** – Auswahl durch gesetzte Eckpunkte präzise eingrenzen.
- **🎨 Hintergrund ersetzen** – Auswahl mit beliebiger Farbe füllen oder auf Transparenz setzen.
- **✂ Zuschnitt** mit Rule-of-Thirds-Raster: Kreis, 1:1, 16:9, 4:3, 3:2, 2:1, 14:9, 9:16, 3:4.
- **⟲ Drehen** in 90°-Schritten oder beliebigem Winkel; **↔ Spiegeln** horizontal/vertikal.
- **⬤ Ecken abrunden** mit einstellbarem Radius.
- **↩ Verlauf** mit Undo und Sprung zu beliebigem früheren Schritt.
- **📥 Drag & Drop** für Bilder direkt aufs Fenster.
- Speichern als **PNG** (mit Transparenz), **JPEG** (auf weißem Hintergrund), **WebP** oder **TIFF**.
- **⚙ Persistente Einstellungen** – Standard-Verzeichnisse und bevorzugtes Dateiformat bleiben gespeichert; die Log-Datei lässt sich direkt aus den Einstellungen auffinden und ihr Ordner öffnen.

## Screenshots

![BgRemover – Hauptfenster](docs/screenshot.png)

## Voraussetzungen

- **macOS** oder eine **Linux-Desktop-Umgebung** (das optionale App-Bundle
  nutzt macOS-spezifische Tools wie `iconutil`)
- **Python 3.10 oder neuer** (der Code nutzt PEP-604-Typannotationen
  wie `QThread | None` direkt in Signaturen — Python 3.9 schlägt fehl)
- Abhängigkeiten (`PyQt6`, `Pillow`, `numpy`, optional `rembg` für die
  KI-Funktion) werden über `pyproject.toml` installiert.

Für den reproduzierbaren KI-/App-Snapshot wird **Python 3.11 oder neuer**
empfohlen: Einige aktuelle transitive KI-Abhängigkeiten sind unter Python
3.10 nicht mehr verfügbar. Die Basis-App ohne KI unterstützt weiterhin
Python 3.10.

## Installation

**Empfohlen (macOS): App-Bundle bauen.** Das Skript legt automatisch
eine isolierte App-venv an, versucht die KI-Abhängigkeiten inklusive
`onnxruntime` zu installieren, behandelt Apple Silicon korrekt und erzeugt
einen `BgRemover.app`-Launcher:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Falls die App-venv neu angelegt wird, den Hinweis mit **Enter** bestätigen.
Danach `BgRemover.app` (unter `~/Applications`) per Doppelklick starten —
funktionsgleich zur mitgelieferten **`BgRemover.command`**. Der Launcher
nutzt die separat installierte venv unter
`~/Library/Application Support/BgRemover/venv`; das Projekt darf daher in
`~/Documents` liegen bleiben. App und App-venv gehören jedoch zusammen:
Die `.app` ist nicht als einzelne Datei portabel. Schlägt die Installation
der KI-Abhängigkeiten fehl, baut das Skript eine nutzbare App ohne KI.

Nach einem Update oder Branch-Wechsel `bash create_BgRemover_app.sh`
erneut ausführen. Das Skript installiert das aktuelle Checkout
nicht-editierbar über die vorhandene App-venv und baut den Launcher neu.

**Alternativ direkt im Terminal** — auf modernem macOS in einer venv,
da System-Python `pip install` per PEP 668 blockiert:

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

`.[ai]` zieht die KI-Abhängigkeiten (`rembg[cpu]` inkl. `onnxruntime`)
mit; ohne KI-Funktion reicht `python3 -m pip install -c requirements/constraints.txt -e .`.

**Linux:** Für Endnutzerinnen und Endnutzer sind die Release-Artefakte
empfohlen: ein portables **AppImage** und ein installierbares **`.deb`**
(jeweils für x86_64 und aarch64/Raspberry Pi OS). Details stehen in
**[INSTALL_LINUX.md](INSTALL_LINUX.md)**; die Build-/Paketierungsdetails in
**[packaging/linux/README.md](packaging/linux/README.md)**. Solche Artefakte
gibt es ab **v2.3.0** — bis dahin den venv-Weg unten nutzen.

Der direkte Start aus einer venv bleibt der beste Weg für Entwicklung,
Branch-Tests und lokale Änderungen:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

Vor dem venv-Start werden einige Qt-Systembibliotheken benötigt — Details
siehe **[INSTALL_LINUX.md](INSTALL_LINUX.md)**. Auf **Raspberry Pi OS
(Desktop)** geht es auch ganz ohne venv/pip (PyQt6, Pillow, numpy als
Systempakete via `apt`); siehe ebenfalls **[INSTALL_LINUX.md](INSTALL_LINUX.md)**.

> Ausführliche Anleitungen — inklusive **Installation aus einem Branch**
> (zum Testen offener Pull Requests) und **Troubleshooting** — stehen in
> **[INSTALL_MAC.md](INSTALL_MAC.md)** (macOS) bzw.
> **[INSTALL_LINUX.md](INSTALL_LINUX.md)** (Linux).

## Bedienung

> 📖 **Ausführliche Schritt-für-Schritt-Anleitung:**
> **[ANLEITUNG.md](ANLEITUNG.md)** (auch als
> [ANLEITUNG.pdf](ANLEITUNG.pdf)) — mit Oberflächen-Überblick, allen
> Werkzeugen und Tabs, typischen Arbeitsabläufen und Fehlerbehebung.

Kurzüberblick:

1. **Bild öffnen** über `Datei → Öffnen` (⌘O) oder per Drag & Drop ins Fenster.
2. **Auswahl treffen** mit Zauberstab, Pinsel, Radiergummi oder Polygon-Lasso (Tab *🎯 Auswahl*).
   - `Shift+Klick` addiert zur Auswahl, `⌘+Klick` (macOS) bzw. `Ctrl+Klick` (Linux) zieht ab.
   - Werkzeuge wechseln per Tastatur: `W` Zauberstab, `B` Pinsel, `E` Radiergummi, `L` Lasso.
3. **Hintergrund bearbeiten** (Tab *🖼 Hintergr.*): transparent machen oder Farbe ersetzen — oder direkt **KI** in der Werkzeugleiste.
4. **Bild transformieren** (Tab *⟲ Trans.*): drehen, spiegeln.
5. **Form & Zuschnitt** (Tab *⬤ Form*): Ecken abrunden oder Format zuschneiden — Rahmen verschieben/skalieren, dann ✓ Anwenden.
6. **Speichern** über `Datei → Speichern` (⌘S) als PNG, JPEG, WebP oder TIFF.

### Einstellungen

Über `Extras → Einstellungen…` (⌘,) lassen sich folgende Einstellungen verwalten:

| Einstellung | Beschreibung |
|---|---|
| Standard-Verzeichnis zum Öffnen | Startverzeichnis des Öffnen-Dialogs; leer = zuletzt verwendetes Verzeichnis |
| Standard-Verzeichnis für Export/Speichern | Startverzeichnis des Speichern-Dialogs; leer = zuletzt verwendetes Verzeichnis |
| Bevorzugtes Bilddateiformat | PNG, JPEG, WebP oder TIFF – erscheint als erste Option im Speichern-Dialog |
| Sprache | Deutsch oder Englisch; die Änderung wird nach einem Neustart wirksam |
| Protokolldatei | Zeigt den Pfad der Log-Datei; Knopf „Ordner öffnen" öffnet das Verzeichnis im Dateimanager |

Die Verzeichnisse, das bevorzugte Dateiformat und die Sprache werden über
**QSettings** persistent gespeichert und beim nächsten Programmstart
automatisch wiederhergestellt.

### Tastatur-Kürzel

Unter macOS ist die Modifikatortaste **⌘ (Cmd)**, unter Linux **Ctrl**.

| Aktion | Shortcut |
|--------|----------|
| Zauberstab wählen | W |
| Pinsel wählen | B |
| Radiergummi wählen | E |
| Polygon-Lasso wählen | L |
| Bild öffnen | ⌘O |
| Bild speichern | ⌘S |
| Bild speichern unter… | ⇧⌘S |
| Rückgängig | ⌘Z |
| Wiederherstellen | ⇧⌘Z |
| 90° links drehen | ⌘← |
| 90° rechts drehen | ⌘→ |
| Auswahl aufheben (wenn kein Crop/Lasso aktiv ist) | Esc |
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
python3 -m venv .venv
source .venv/bin/activate
make pr-check
```

Die Test-Suite läuft headless (Qt-Platform `offscreen`) und prüft die
Bildoperationen, die Crop-Geometrie und die Speicher-Logik. Pull
Requests laufen auf GitHub über eine leichte PR-CI (Ubuntu, Python
3.12, `make pr-check`). Die volle Matrix auf Linux und macOS unter Python
3.10, 3.11, 3.12 und 3.13 läuft als Release-Gate: Beim Push eines
Versions-Tags ruft der Release-Workflow sie vor dem Veröffentlichen auf;
außerdem wöchentlich (sonntags) und manuell.
Alle lokalen/CI-Testinstallationen nutzen `requirements/constraints.txt`;
bei Bedarf kann der Pfad mit `make PIP_CONSTRAINT=/pfad/zur/datei pr-check`
überschrieben werden.
Details stehen in [TESTING.md](TESTING.md).

Code-Style-Check und statische Typprüfung:

```bash
make lint
make type
```

### Anleitung-PDF neu erzeugen

`ANLEITUNG.pdf` wird aus `ANLEITUNG.md` generiert (Markdown → HTML →
PDF via WeasyPrint, GitHub-ähnliches Layout). Nach Änderungen an der
Markdown-Quelle die PDF reproduzierbar neu bauen. Unter Linux werden die
DejaVu-Schriften (System-Paket `fonts-dejavu-core`) sowie die
WeasyPrint-Systembibliotheken benötigt (Pango/Cairo/GDK-Pixbuf, unter
Debian/Ubuntu z. B. `libpango-1.0-0 libpangoft2-1.0-0 libcairo2
libgdk-pixbuf-2.0-0`). Unter macOS verwendet der Generator die
Systemschriften Arial/Courier New; Pango lässt sich mit
`brew install pango` installieren:

```bash
pip install -e ".[docs]"
python scripts/generate_anleitung_pdf.py
```

## Architektur (Kurzüberblick)

BgRemover ist ein installierbares Paket (`bgremover/`, gestartet via
`python -m bgremover` oder dem Console-Script `bgremover`):

- **`ImageCanvas`** (QGraphicsView) hält den Bildzustand, die Auswahl­maske,
  Undo-/Redo-Stapel und die Werkzeuge (Zauberstab, Pinsel, Lasso, Crop).
- **`MainWindow`** baut Toolbar, Status-/Crop-Leiste und verbindet Canvas,
  Menüs, rechtes Panel und Worker.
- **`right_panel`** baut die vier rechten Tabs für Auswahl, Hintergrund,
  Drehen/Spiegeln und Form/Zuschnitt aus einem Callback-Satz.
- **`menu_actions`** baut Menüleiste, Actions und Shortcuts; `MainWindow`
  liefert dafür nur noch Callbacks.
- **`RecentFiles`** kapselt Persistenz, Deduplizierung und Menüadapter für
  „Zuletzt geöffnet“, sodass `MainWindow` nur noch den Ladepfad delegiert.
- **Worker** (`ImageLoadWorker`, `AIWorker`, `RembgWarmupWorker`,
  `FloodFillWorker`) laufen in
  eigenen `QThread`s; `WorkerController` kapselt Start, starke Worker-
  Referenzen, `deleteLater` und Shutdown.
- Ein monotoner **Versionszähler** im Canvas verwirft veraltete KI- und
  Flood-Fill-Ergebnisse, falls zwischenzeitlich ein anderes Bild geladen
  oder der Bildzustand geändert wurde.
- Undo und Redo teilen sich ein **Speicherlimit**
  (`_HISTORY_MEMORY_LIMIT`); laufende Byte-Summen evakuieren die ältesten
  History-Einträge. Originalbild und aktueller Canvas-Zustand liegen bewusst
  außerhalb dieses Budgets.

## Bekannte Einschränkungen

- **Maximale Bildgröße: 40 Megapixel.** Größere Bilder werden mit einer
  Statusmeldung abgelehnt, um Speicherbedarf und Verarbeitungszeit zu
  begrenzen. Die Zauberstab-Auswahl (Flood-Fill) läuft asynchron in einem
  eigenen `QThread`, damit die Oberfläche während der Berechnung bedienbar
  bleibt. Pillow ist zusätzlich gegen „Decompression-Bomb"-Bilder
  abgesichert.
- Der **App-Bundle-Build** ist macOS-spezifisch; unter Linux läuft die
  Anwendung über den direkten `python -m bgremover`-Start. Windows gehört
  derzeit nicht zur offiziell getesteten Matrix.

## Log-Datei

Der interne App-Logger verwendet eine Log-Datei `bgremover.log` im von Qt
ermittelten App-Datenverzeichnis. Der genaue Pfad hängt von Plattform und
Qt-Konfiguration ab; mit der aktuellen macOS-Konfiguration ist es
`~/Library/Application Support/BgRemover/BgRemover/bgremover.log`, unter
Linux liegt die Datei unter `~/.local/share/`. Sie enthält Laufzeitmeldungen
und Stacktraces protokollierter Fehler und wird beim ersten Log-Eintrag
angelegt.

Der macOS-App-Bundle-Launcher schreibt Startdiagnosen zusätzlich nach
`~/Library/Application Support/BgRemover/bgremover.log`.

Den genauen Pfad zeigt der Dialog `Extras → Einstellungen… →
Protokolldatei` an; der Knopf „Ordner öffnen" öffnet das Verzeichnis
direkt im Dateimanager – praktisch, um die Datei zu finden oder an eine
Support-Mail anzuhängen.

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
