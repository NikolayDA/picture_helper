**Deutsch** · [English](docs/i18n/en/RESOURCES.md) · [Español](docs/i18n/es/RESOURCES.md) · [Français](docs/i18n/fr/RESOURCES.md) · [Українська](docs/i18n/uk/RESOURCES.md) · [简体中文](docs/i18n/zh/RESOURCES.md)

# Verwendete Ressourcen

Dieses Dokument listet **alle externen Ressourcen** auf, die BgRemover
verwendet oder benötigt: Bibliotheken (Python-Pakete), weitere Software
und Werkzeuge, projektfremder Code sowie projekteigene Assets — jeweils
mit Zweck, Lizenz und Bezugsquelle.

> Versionsangaben: „Min." stammt aus `pyproject.toml` (verbindliche
> Mindestanforderung), „geprüft" ist die durch
> `requirements/constraints.txt` festgehaltene Python-3.12-Baseline der
> aktuellen lokalen/CI-Checks. Maßgeblich ist immer der jeweils
> mitgelieferte Lizenztext des Pakets.

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

| Ressource | Zweck | Min. | Geprüft | Lizenz | Bezug |
|-----------|-------|------|---------|--------|-------|
| **rembg[cpu]** | KI-gestützte Hintergrundentfernung (`rembg.remove`) | `>=2.0` | 2.0.75 | MIT | PyPI |
| **onnxruntime** | ONNX-Inferenz-Backend (transitive Abhängigkeit von `rembg[cpu]`) | (transitiv) | 1.26.0 | MIT (Microsoft) | PyPI |
| **U²-Net-Modell** (`u2net.onnx`) | Standard-Segmentierungsmodell, das rembg **zur Laufzeit herunterlädt** (nicht im Repo enthalten) | – | – | Apache-2.0 (Projekt *U-2-Net*) | Download durch rembg in das Nutzer-Cache-Verzeichnis |

Ohne die `ai`-Extras startet das Programm normal; der KI-Button ist dann
deaktiviert (`REMBG_AVAILABLE = False`).

## 3. Python-Standardbibliothek

Teil von CPython, **keine zusätzliche Installation** nötig
(Lizenz: PSF License Agreement):

`sys`, `os`, `io`, `logging`, `collections.deque`, `pathlib.Path`,
`importlib.metadata`, `importlib.resources`, `contextlib`, `tempfile`.

## 4. Entwicklungs- & Test-Werkzeuge

Deklariert unter `[project.optional-dependencies] test`:

| Werkzeug | Zweck | Min. | Geprüft | Lizenz |
|----------|-------|------|---------|--------|
| **pytest** | Test-Runner | `>=8` | 9.0.3 | MIT |
| **pytest-qt** | Qt-Fixtures (headless `offscreen`) | `>=4.4` | 4.5.0 | MIT |
| **ruff** | Linting / Style-Check | `>=0.6` | 0.15.13 | MIT |
| **mypy** | Statische Typprüfung (CI-Schritt) | `>=1.10` | 2.1.0 | MIT |
| **packaging** | Parsing der Dependency-Constraints in Tests | `>=24` | 24.0 | Apache-2.0 oder BSD-2-Clause |

Optionale Dokumentations-/PDF-Werkzeuge sind unter
`[project.optional-dependencies] docs` deklariert:

| Werkzeug | Zweck | Min. | Lizenz |
|----------|-------|------|--------|
| **Markdown** | Markdown → HTML für `ANLEITUNG.pdf` | `>=3.5` | BSD |
| **WeasyPrint** | PDF-Rendering aus HTML/CSS | `>=61` | BSD-3-Clause |
| **fonttools** | Font-Inspection für PDF-Erzeugung | `>=4.0` | MIT |

Zusätzlich benötigt die PDF-Erzeugung unter Linux DejaVu-Schriften sowie
Pango/Cairo/GDK-Pixbuf (distro-paketiert). Unter macOS verwendet der
Generator Arial/Courier New aus dem System; Pango lässt sich mit
`brew install pango` installieren.

## 5. Build- & Verteilungs-Werkzeuge (macOS)

Benötigt vom App-Bundle-Skript `create_BgRemover_app.sh`. Es bündelt
**keine** dieser Programme, sondern ruft sie über das System auf:

| Werkzeug | Zweck | Herkunft |
|----------|-------|----------|
| `python3` + `venv` + `pip` | Isolierte venv anlegen, Abhängigkeiten mit `requirements/constraints.txt` installieren | Python / PyPA |
| `setuptools` (Build-Backend) | Paketierung gemäß `[build-system]` (`>=61`) | MIT |
| `/usr/bin/arch`, `uname` | Native CPU-Architektur erzwingen (Apple Silicon) | macOS |
| `iconutil` | `.icns`-App-Icon aus Iconset erzeugen (Fallback: PNG) | macOS |
| `osascript` | Fehlermeldungen des App-Launchers anzeigen | macOS |
| Standard-Shell-Tools | `mkdir`, `cp`, `cat`, `command` u. a. | POSIX/macOS |

`BgRemover.command` ist der mitgelieferte Doppelklick-Starter (eigener
Code des Projekts).

## 6. Continuous Integration

Definiert in `.github/workflows/pr-ci.yml`,
`.github/workflows/ci.yml`, `.github/workflows/ui-nightly.yml` und
`.github/workflows/license-check.yml`.
Pull Requests laufen leichtgewichtig auf Ubuntu/Python 3.12; die volle
Matrix läuft auf Ubuntu + macOS mit Python 3.10–3.13 bei einem
Versions-Tag (Release-Kandidat), beim Release oder manuell;
`ui-nightly.yml` führt die UI-Interaktionstests nächtlich aus; der
Lizenz-Workflow erzeugt den Dependency-/Lizenzreport.

| Ressource | Zweck | Lizenz |
|-----------|-------|--------|
| `actions/checkout@v5` | Repository auschecken | MIT |
| `actions/setup-python@v6` | Python einrichten + Pip-Cache | MIT |
| `actions/upload-artifact@v4` | Lizenzreport-Artefakte hochladen | MIT |
| `actions/download-artifact@v4` | Lizenz-Kurzfassung im separaten Kommentar-Job herunterladen | MIT |
| `actions/github-script@v7` | Lizenz-Kurzfassung am Pull Request kommentieren | MIT |
| `pip-licenses` | Rohdump der installierten Paketlizenzen | MIT |
| `requirements/constraints.txt` | Reproduzierbarer Dependency-Snapshot für lokale Checks, CI, Lizenzreport und App-Bundle | Projektdatei |
| Qt-Systembibliotheken via `apt` (Linux) | Headless-Qt-Laufzeit: `libegl1`, `libfontconfig1`, `libxkbcommon0`, `libdbus-1-3`, `libxcb-*` | distro-paketiert, diverse permissive/Copyleft-Lizenzen (Mesa, fontconfig, libxkbcommon, libxcb, dbus …) |

## 7. Projekteigene Ressourcen

Eigenes Werk des Projekts, abgedeckt durch die Projektlizenz
(GPL-3.0-or-later, siehe `LICENSE`):

- **Quellcode**: das installierbare Paket `bgremover/`, die Test-Suite
  unter `tests/` sowie Projekt-Skripte unter `scripts/`.
- **Toolbar-/Tab-Icons**: `bgremover/icons/*.png` (`ai`, `bg`, `brush`,
  `clear_sel`, `close`, `eraser`, `form`, `open`, `redo`, `restore`,
  `save`, `transparency`, `undo`, `wand`). Werden von `make_tool_icon()`
  über `importlib.resources` als Paketdaten geladen.
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
`requirements/constraints.txt`, `.github/workflows/pr-ci.yml`,
`.github/workflows/ci.yml`, `.github/workflows/ui-nightly.yml`,
`.github/workflows/license-check.yml`,
`create_BgRemover_app.sh` oder den Paketdaten unter `bgremover/icons/`
bitte dieses Dokument mit aktualisieren.
