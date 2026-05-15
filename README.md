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
- Speichern als **PNG** (mit Transparenz), **JPEG** (auf weißem Hintergrund) oder **WebP**.

## Voraussetzungen

- **macOS** (das mitgelieferte App-Bundle nutzt macOS-spezifische Tools wie `iconutil`)
- **Python 3.9 oder neuer**
- Abhängigkeiten (`PyQt6`, `Pillow`, `numpy`, optional `rembg` für die
  KI-Funktion) werden über `pyproject.toml` installiert.

## Installation

**Schnellstart aus `main`:**

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m pip install -e ".[ai]"
python3 BgRemover.py
```

`.[ai]` zieht `rembg` mit; ohne KI-Funktion reicht
`python3 -m pip install -e .`.

Statt direkt im Terminal zu starten, kann auch ein **App-Bundle**
gebaut (`bash create_BgRemover_app.sh`) oder die mitgelieferte
**`BgRemover.command`** per Doppelklick im Finder genutzt werden.

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
6. **Speichern** über `Datei → Speichern` (⌘S) als PNG, JPEG oder WebP.

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

Im Datei-Menü gibt es zusätzlich ein Submenü **„Zuletzt geöffnet"** mit
den 10 zuletzt geladenen Bildern — der Zustand wird über QSettings
persistiert.

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

Code-Style-Check:

```bash
ruff check BgRemover.py tests
```

## Log-Datei

Beim Programmstart wird eine Log-Datei unter `~/.bgremover.log` angelegt,
in der Stacktraces und Status-Meldungen mitlaufen. Bei Problemen ist sie
die erste Anlaufstelle für die Diagnose.
