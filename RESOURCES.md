# Verwendete Ressourcen

Dieses Dokument listet **alle externen Ressourcen** auf, die BgRemover
verwendet oder benötigt: Bibliotheken (Python-Pakete), weitere Software
und Werkzeuge, projektfremder Code sowie projekteigene Assets — jeweils
mit Zweck, Lizenz und Bezugsquelle.

> Versionsangaben: „Min." stammt aus `pyproject.toml` (verbindliche
> Mindestanforderung), „geprüft" ist die in der aktuellen
> Entwicklungs-/CI-Umgebung installierte Version. Maßgeblich ist immer
> der jeweils mitgelieferte Lizenztext des Pakets.

---

## 1. Laufzeit-Abhängigkeiten (Python-Pakete)

Deklariert in `pyproject.toml` unter `[project] dependencies`.

| Paket | Zweck im Programm | Min. | Geprüft | Lizenz |
|-------|-------------------|------|---------|--------|
| **PyQt6** | Komplette GUI (Fenster, Canvas, Widgets, Events, QSettings, QThread) | `>=6.5` | 6.11.0 | **GPL v3** oder kommerzielle Riverbank-Lizenz |
| **Pillow** (PIL) | Bild-IO, EXIF-Transpose, Drehen/Spiegeln, Masken/Alpha, Speichern (PNG/JPEG/WebP/TIFF) | `>=10` | 12.2.0 | HPND (auch „MIT-CMU"; Open-Source-PIL-Lizenz) |
| **NumPy** | Pixel-Arrays, Flood-Fill, Maskenoperationen | `>=1.24` | 2.4.5 | BSD-3-Clause |

Über PyQt6 wird zudem das **Qt 6**-Framework (The Qt Company) gebunden.
Qt selbst steht unter LGPL v3 / GPL / kommerzieller Lizenz; das
**PyQt6-Binding** ist GPL v3 — siehe Abschnitt 8.

## 2. Optionale KI-Abhängigkeit

Deklariert unter `[project.optional-dependencies] ai` — nur nötig für die
automatische Hintergrundentfernung (`rembg`-Werkzeug):

| Ressource | Zweck | Min. | Lizenz | Bezug |
|-----------|-------|------|--------|-------|
| **rembg[cpu]** | KI-gestützte Hintergrundentfernung (`rembg.remove`) | `>=2.0` | MIT | PyPI |
| **onnxruntime** | ONNX-Inferenz-Backend (transitive Abhängigkeit von `rembg[cpu]`) | (transitiv) | MIT (Microsoft) | PyPI |
| **U²-Net-Modell** (`u2net.onnx`) | Standard-Segmentierungsmodell, das rembg **zur Laufzeit herunterlädt** (nicht im Repo enthalten) | – | Apache-2.0 (Projekt *U-2-Net*) | Download durch rembg in das Nutzer-Cache-Verzeichnis |

Ohne die `ai`-Extras startet das Programm normal; der KI-Button ist dann
deaktiviert (`REMBG_AVAILABLE = False`).

## 3. Python-Standardbibliothek

Teil von CPython, **keine zusätzliche Installation** nötig
(Lizenz: PSF License Agreement):

`sys`, `os`, `io`, `logging`, `collections.deque`, `pathlib.Path`.

## 4. Entwicklungs- & Test-Werkzeuge

Deklariert unter `[project.optional-dependencies] test`:

| Werkzeug | Zweck | Min. | Geprüft | Lizenz |
|----------|-------|------|---------|--------|
| **pytest** | Test-Runner | `>=8` | 9.0.3 | MIT |
| **pytest-qt** | Qt-Fixtures (headless `offscreen`) | `>=4.4` | 4.5.0 | MIT |
| **ruff** | Linting / Style-Check | `>=0.6` | 0.15.13 | MIT |
| **mypy** | Statische Typprüfung (CI-Schritt) | `>=1.10` | 2.1.0 | MIT |

## 5. Build- & Verteilungs-Werkzeuge (macOS)

Benötigt vom App-Bundle-Skript `create_BgRemover_app.sh`. Es bündelt
**keine** dieser Programme, sondern ruft sie über das System auf:

| Werkzeug | Zweck | Herkunft |
|----------|-------|----------|
| `python3` + `venv` + `pip` | Isolierte venv anlegen, Abhängigkeiten installieren | Python / PyPA |
| `setuptools` (Build-Backend) | Paketierung gemäß `[build-system]` (`>=61`) | MIT |
| `/usr/bin/arch`, `uname` | Native CPU-Architektur erzwingen (Apple Silicon) | macOS |
| `iconutil` | `.icns`-App-Icon aus Iconset erzeugen (Fallback: PNG) | macOS |
| `osascript` | Fehlermeldungen des App-Launchers anzeigen | macOS |
| Standard-Shell-Tools | `mkdir`, `cp`, `cat`, `command` u. a. | POSIX/macOS |

`BgRemover.command` ist der mitgelieferte Doppelklick-Starter (eigener
Code des Projekts).

## 6. Continuous Integration

Definiert in `.github/workflows/ci.yml` (läuft auf GitHub-Actions-Runnern
Ubuntu + macOS, Python 3.10/3.12):

| Ressource | Zweck | Lizenz |
|-----------|-------|--------|
| `actions/checkout@v4` | Repository auschecken | MIT |
| `actions/setup-python@v5` | Python einrichten + Pip-Cache | MIT |
| Qt-Systembibliotheken via `apt` (Linux) | Headless-Qt-Laufzeit: `libegl1`, `libfontconfig1`, `libxkbcommon0`, `libdbus-1-3`, `libxcb-*` | distro-paketiert, diverse permissive/Copyleft-Lizenzen (Mesa, fontconfig, libxkbcommon, libxcb, dbus …) |

## 7. Projekteigene Ressourcen

Eigenes Werk des Projekts, abgedeckt durch die Projektlizenz
(GPL-3.0-or-later, siehe `LICENSE`):

- **Quellcode**: `BgRemover.py` sowie die Test-Suite unter `tests/`.
- **Toolbar-/Tab-Icons**: `icons/*.png` (`ai`, `bg`, `brush`,
  `clear_sel`, `close`, `eraser`, `form`, `open`, `redo`, `restore`,
  `save`, `transparency`, `undo`, `wand`). Werden von `make_tool_icon()`
  geladen.
- **Gezeichnete Vektor-Icons**: Fällt eine PNG aus, zeichnet
  `make_tool_icon()` das Icon programmatisch mit `QPainter`
  (`_draw_*_icon`-Funktionen) — kein externes Asset.
- **App-Icon**: `BgRemover_icon.png` (Quelle für das macOS-`.icns`).
- **Cursor**: zur Laufzeit gezeichnet (`make_wand_cursor`,
  `make_brush_cursor`, `make_eraser_cursor`) — keine externen Dateien.

Es ist **kein projektfremder Quellcode** ins Repository eingebettet
(kein `vendor/` oder `third_party/`); externe Funktionalität wird
ausschließlich über die oben gelisteten Pakete bezogen.

## 8. Lizenz-Kompatibilität (Hinweis)

BgRemover steht unter **GPL-3.0-or-later** (`LICENSE`). Diese Wahl ist
durch **PyQt6** bedingt: Das Binding ist GPL-v3-lizenziert (oder
kommerziell), daher muss die als Ganzes verteilte Anwendung —
insbesondere das gebündelte `BgRemover.app` — GPL-konform sein. Die
übrigen Laufzeit-/KI-Abhängigkeiten (Pillow HPND, NumPy BSD, rembg MIT,
onnxruntime MIT, U²-Net Apache-2.0) sind GPL-v3-kompatibel.

Ein **permissives** Lizenzmodell (MIT/Apache-2.0) wäre nur möglich, wenn
PyQt6 durch das LGPL-v3-lizenzierte **PySide6** ersetzt würde.

---

*Pflege-Hinweis:* Bei Änderungen an `pyproject.toml`,
`.github/workflows/ci.yml` oder `create_BgRemover_app.sh` bitte dieses
Dokument mit aktualisieren.
