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
- Folgende Python-Pakete:
  - `PyQt6`
  - `Pillow`
  - `numpy`
  - `rembg` (optional, nur für die KI-Funktion)

## Installation

### Variante A: Als macOS-App installieren (empfohlen)

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
pip3 install PyQt6 Pillow numpy rembg
bash create_BgRemover_app.sh
```

Das Skript erstellt `BgRemover.app` unter `~/Applications` (oder optional `~/Desktop` bzw. `/Applications`) inklusive Icon. Danach kann die App per Doppelklick aus dem Finder oder dem Dock gestartet werden.

### Variante B: Per Doppelklick auf `BgRemover.command`

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
pip3 install PyQt6 Pillow numpy rembg
chmod +x BgRemover.command
```

Anschließend `BgRemover.command` im Finder doppelklicken — ein Terminalfenster startet die App.

### Variante C: Direkt aus dem Terminal

```bash
pip3 install PyQt6 Pillow numpy rembg
python3 BgRemover.py
```

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
| Rückgängig | ⌘Z |
| 90° links drehen | ⌘← |
| 90° rechts drehen | ⌘→ |
| Auswahl aufheben | Esc |
| Fit to View | ⌘0 |

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
