[Deutsch](../../../README.md) · **English** · [Español](../es/README.md) · [Français](../fr/README.md) · [Українська](../uk/README.md) · [简体中文](../zh/README.md)

# BgRemover

An image-editing tool for macOS and Linux for **removing, replacing, and editing backgrounds** — with AI-based automatic cutout, magic-wand selection, brush/eraser, polygon lasso, cropping in various formats, rotating, flipping, and corner rounding.

## Features

- **🤖 AI background removal** via [rembg](https://github.com/danielgatis/rembg) – one click, done.
- **🪄 Magic wand** – selects contiguous color areas via flood fill (with a tolerance slider).
- **🖌 Brush / eraser** – paint or remove a selection manually.
- **➰ Polygon lasso** – precisely narrow a selection by placing corner points.
- **🎨 Replace background** – fill the selection with any color or set it to transparent.
- **✂ Crop** with a rule-of-thirds grid: circle, 1:1, 16:9, 4:3, 3:2, 2:1, 14:9, 9:16, 3:4.
- **⟲ Rotate** in 90° steps or by any angle; **↔ flip** horizontally/vertically.
- **⬤ Round corners** with an adjustable radius.
- **↩ History** with undo and jumping to any earlier step.
- **📥 Drag & drop** for images directly onto the window.
- Save as **PNG** (with transparency), **JPEG** (on a white background), **WebP**, or **TIFF**.
- **⚙ Persistent settings** – default directories and preferred file format are remembered; the log file can be located directly from the settings and its folder can be opened.

## Screenshots

![BgRemover – main window](../../screenshot.png)

## Requirements

- **macOS** or a **Linux desktop environment** (the optional app bundle uses
  macOS-specific tools such as `iconutil`)
- **Python 3.10 or newer** (the code uses PEP 604 type annotations
  like `QThread | None` directly in signatures — Python 3.9 fails)
- Dependencies (`PyQt6`, `Pillow`, `numpy`, optionally `rembg` for the
  AI feature) are installed via `pyproject.toml`.

**Python 3.11 or newer** is recommended for the reproducible AI/app
snapshot: some current transitive AI dependencies are no longer available
under Python 3.10. The base app without AI continues to support Python 3.10.

## Installation

**Recommended (macOS): build the app bundle.** The script automatically
creates an isolated app venv, attempts to install the AI dependencies
including `onnxruntime`, handles Apple Silicon correctly, and produces a
`BgRemover.app` launcher:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

If the app venv is newly created, confirm the prompt with **Enter**.
Afterwards, double-click `BgRemover.app` (under `~/Applications`) to start
it — functionally identical to the bundled **`BgRemover.command`**. The
launcher uses the separately installed venv under
`~/Library/Application Support/BgRemover/venv`, so the project may stay in
`~/Documents`. However, the app and its venv belong together: the `.app`
is not portable as a single file. If the AI dependency installation
fails, the script builds a usable app without AI.

After an update or branch switch, run `bash create_BgRemover_app.sh`
again. The script installs the current checkout non-editably over the
existing app venv and rebuilds the launcher.

**Alternatively, directly in the terminal** — on modern macOS in a venv,
since system Python blocks `pip install` via PEP 668:

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

`.[ai]` pulls in the AI dependencies (`rembg[cpu]` including `onnxruntime`);
without the AI feature, `python3 -m pip install -c requirements/constraints.txt -e .` is sufficient.

**Linux:** For end users, the recommended path is the release artifacts:
a portable **AppImage** and an installable **`.deb`** (both for x86_64 and
aarch64/Raspberry Pi OS). See **[INSTALL_LINUX.md](INSTALL_LINUX.md)** for
installation details and **[packaging/linux/README.md](../../../packaging/linux/README.md)**
for build/packaging details. Such artifacts are available from **v2.3.0**
onwards — until then, use the venv path below.

Starting directly from a venv remains the best path for development,
branch testing, and local changes:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

Before the venv start, a few Qt system libraries are required — see
**[INSTALL_LINUX.md](INSTALL_LINUX.md)**. On **Raspberry Pi OS (Desktop)**
it is also possible entirely without venv/pip (PyQt6, Pillow, numpy as
system packages via `apt`); see **[INSTALL_LINUX.md](INSTALL_LINUX.md)** as well.

> Detailed instructions — including **installation from a branch**
> (to test open pull requests) and **troubleshooting** — are available in
> **[INSTALL_MAC.md](INSTALL_MAC.md)** (macOS) and
> **[INSTALL_LINUX.md](INSTALL_LINUX.md)** (Linux).

## Usage

1. **Open an image** via `File → Open` (⌘O) or by dragging and dropping it onto the window.
2. **Make a selection** with the magic wand, brush, eraser, or polygon lasso (tab *🎯 Selection*).
   - `Shift+Click` adds to the selection; `⌘+Click` (macOS) or `Ctrl+Click` (Linux) subtracts.
   - Switch tools from the keyboard: `W` magic wand, `B` brush, `E` eraser, `L` lasso.
3. **Edit the background** (tab *🖼 Backgr.*): make it transparent or replace the color — or use **AI** directly in the toolbar.
4. **Transform the image** (tab *⟲ Trans.*): rotate, flip.
5. **Shape & crop** (tab *⬤ Shape*): round corners or crop to a format — move/resize the frame, then ✓ Apply.
6. **Save** via `File → Save` (⌘S) as PNG, JPEG, WebP, or TIFF.

### Settings

Via `Tools → Settings…` (⌘,), the following settings can be managed:

| Setting | Description |
|---|---|
| Default directory for opening | Start directory of the open dialog; empty = last used directory |
| Default directory for export/save | Start directory of the save dialog; empty = last used directory |
| Preferred image file format | PNG, JPEG, WebP, or TIFF – appears as the first option in the save dialog |
| Language | German or English; the change takes effect after a restart |
| Log file | Shows the log-file path; the "Open Folder" button opens the directory in the file manager |

The directories, preferred file format, and language are stored persistently
via **QSettings** and automatically restored the next time the program starts.

### Keyboard shortcuts

On macOS the modifier key is **⌘ (Cmd)**, on Linux **Ctrl**.

| Action | Shortcut |
|--------|----------|
| Select magic wand | W |
| Select brush | B |
| Select eraser | E |
| Select polygon lasso | L |
| Open image | ⌘O |
| Save image | ⌘S |
| Save image as… | ⇧⌘S |
| Undo | ⌘Z |
| Redo | ⇧⌘Z |
| Rotate 90° left | ⌘← |
| Rotate 90° right | ⌘→ |
| Clear selection (when no crop/lasso is active) | Esc |
| Invert selection | ⌘⇧I |
| Fit to View | ⌘0 |
| Open settings | ⌘, |

The File menu additionally has a submenu **"Open Recent"** with the
10 most recently loaded images — the state is persisted via QSettings
together with the other settings.

## Development & tests

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv
source .venv/bin/activate
make pr-check
```

The test suite runs headless (Qt platform `offscreen`) and checks the
image operations, the crop geometry, and the save logic. Pull requests
run a lightweight GitHub PR CI job (Ubuntu, Python 3.12, `make pr-check`).
The full Linux/macOS matrix under Python 3.10, 3.11, 3.12, and 3.13 runs as the
release gate: on a version-tag push the release workflow calls it before
publishing; it also runs weekly (Sundays) and manually. All
local/CI test installs use
`requirements/constraints.txt`; override it with
`make PIP_CONSTRAINT=/path/to/file pr-check` when needed. See
[TESTING.md](../../../TESTING.md) for the full testing workflow.

Code-style check and static type checking:

```bash
make lint
make type
```

### Regenerating the guide PDF

`ANLEITUNG.pdf` is generated from `ANLEITUNG.md` (Markdown to HTML to
PDF via WeasyPrint). After changing the Markdown source, rebuild the PDF
reproducibly. On Linux this requires DejaVu fonts and the
Pango/Cairo/GDK-Pixbuf distribution packages. On macOS the generator
uses the Arial/Courier New system fonts; install Pango with
`brew install pango`:

```bash
pip install -e ".[docs]"
python scripts/generate_anleitung_pdf.py
```

## Architecture (brief overview)

BgRemover is an installable package (`bgremover/`, launched via
`python -m bgremover` or the `bgremover` console script):

- **`ImageCanvas`** (QGraphicsView) holds the image state, the selection mask,
  undo/redo stacks, and the tools (magic wand, brush, lasso, crop).
- **`MainWindow`** builds the toolbar, status/crop bar, and connects the canvas,
  menus, right panel, and workers.
- **`right_panel`** builds the four right-hand tabs for selection, background,
  rotate/flip, and shape/crop from a callback set.
- **`menu_actions`** builds the menu bar, actions, and shortcuts; `MainWindow`
  only supplies callbacks for it.
- **`RecentFiles`** encapsulates persistence, de-duplication, and the menu
  adapter for "Open Recent", so `MainWindow` only delegates the load path.
- **Workers** (`ImageLoadWorker`, `AIWorker`, `RembgWarmupWorker`,
  `FloodFillWorker`) run in
  their own `QThread`s; `WorkerController` encapsulates start, strong worker
  references, `deleteLater`, and shutdown.
- A monotonic **version counter** in the canvas discards stale AI and
  flood-fill results if another image was loaded or the image state
  changed in the meantime.
- The undo stack is limited not by `maxlen` but by a **memory limit**
  (`_UNDO_MEMORY_LIMIT`); a running byte sum evicts the oldest entries.

## Known limitations

- **Maximum image size: 40 megapixels.** Larger images are rejected with a
  status message to limit memory use and processing time. The magic-wand
  selection (flood fill) runs asynchronously in its own `QThread`, keeping
  the UI responsive during calculation. Pillow is additionally protected
  against "decompression bomb" images.
- The **app bundle build** is macOS-specific; on Linux the application
  runs by starting `python -m bgremover` directly. Windows is currently
  not part of the officially tested matrix.

## Log file

The internal app logger uses a `bgremover.log` file in the app-data
directory determined by Qt. The exact path depends on the platform and Qt
configuration; with the current macOS configuration it is
`~/Library/Application Support/BgRemover/BgRemover/bgremover.log`, while
on Linux the file is located below `~/.local/share/`. It contains runtime
messages and stack traces for logged errors and is created with the first
log entry.

The macOS app-bundle launcher additionally writes startup diagnostics to
`~/Library/Application Support/BgRemover/bgremover.log`.

The exact internal path is displayed under `Tools → Settings… → Log file`;
the "Open Folder" button opens the directory directly in the file manager.

## License

BgRemover is licensed under the **GNU General Public License v3.0 or
later** (`GPL-3.0-or-later`) — see [LICENSE](../../../LICENSE).

A complete list of all libraries, tools, and assets used, along with
their licenses, is available in **[RESOURCES.md](RESOURCES.md)**.

> **Note on PyQt6:** The GUI dependency PyQt6 (Riverbank) is itself
> licensed under GPL v3 (or commercially). GPL-3.0 was deliberately
> chosen so that the distributed application — in particular the
> bundled `BgRemover.app` — is license-compliant. Anyone aiming for a
> permissive model (MIT/Apache-2.0) would have to replace PyQt6 with the
> LGPL-licensed **PySide6**.
