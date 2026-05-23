[Deutsch](../../../README.md) · **English** · [Español](../es/README.md) · [Français](../fr/README.md) · [Українська](../uk/README.md) · [简体中文](../zh/README.md)

# BgRemover

An image-editing tool for macOS for **removing, replacing, and editing backgrounds** — with AI-based automatic cutout, magic-wand selection, brush/eraser, cropping in various formats, rotating, flipping, and corner rounding.

## Features

- **🤖 AI background removal** via [rembg](https://github.com/danielgatis/rembg) – one click, done.
- **🪄 Magic wand** – selects contiguous color areas via flood fill (with a tolerance slider).
- **🖌 Brush / eraser** – paint or remove a selection manually.
- **🎨 Replace background** – fill the selection with any color or set it to transparent.
- **✂ Crop** with a rule-of-thirds grid: circle, 1:1, 16:9, 4:3, 3:2, 2:1, 14:9, 9:16, 3:4.
- **⟲ Rotate** in 90° steps or by any angle; **↔ flip** horizontally/vertically.
- **⬤ Round corners** with an adjustable radius.
- **↩ History** with undo and jumping to any earlier step.
- **📥 Drag & drop** for images directly onto the window.
- Save as **PNG** (with transparency), **JPEG** (on a white background), **WebP**, or **TIFF**.
- **⚙ Persistent settings** – default directories and preferred file format are remembered.

## Screenshots

<!--
  Before the release, place a screenshot/GIF at docs/screenshot.png
  and uncomment the following line (the placeholder deliberately
  does not render a broken image while the file is missing):

![BgRemover – main window](../../screenshot.png)
-->

> _Screenshot to follow._ An image of the main window (toolbar, canvas with
> selection, right-hand tab panel) belongs here before publication —
> recommended path `docs/screenshot.png`.

## Requirements

- **macOS** (the bundled app uses macOS-specific tools such as `iconutil`)
- **Python 3.10 or newer** (the code uses PEP 604 type annotations
  like `QThread | None` directly in signatures — Python 3.9 fails)
- Dependencies (`PyQt6`, `Pillow`, `numpy`, optionally `rembg` for the
  AI feature) are installed via `pyproject.toml`.

## Installation

**Recommended (macOS): build the app bundle.** The script automatically
creates an isolated venv, installs all dependencies (including
`onnxruntime` for the AI), handles Apple Silicon correctly, and produces
a standalone `BgRemover.app`:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Confirm the venv prompt with **Enter**. Afterwards, double-click
`BgRemover.app` (under `~/Applications`) to start it — functionally
identical to the bundled **`BgRemover.command`**. The project may stay in
`~/Documents` (the app is built as a standalone).

**Alternatively, directly in the terminal** — on modern macOS in a venv,
since system Python blocks `pip install` via PEP 668:

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

`.[ai]` pulls in the AI dependencies (`rembg[cpu]` including `onnxruntime`);
without the AI feature, `python3 -m pip install -c requirements/constraints.txt -e .` is sufficient.

**Linux:** There is no app bundle; the application runs by starting it
directly from a venv:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

Beforehand, a few Qt system libraries are required — for details, see
**[INSTALL_LINUX.md](INSTALL_LINUX.md)**.

On **Raspberry Pi OS (Desktop)** it is particularly simple — entirely
without venv/pip (PyQt6, Pillow, numpy as system packages via `apt`); see
the Raspberry Pi section in **[INSTALL_LINUX.md](INSTALL_LINUX.md)**.

> Detailed instructions — including **installation from a branch**
> (to test open pull requests) and **troubleshooting** — are available in
> **[INSTALL_MAC.md](INSTALL_MAC.md)** (macOS) and
> **[INSTALL_LINUX.md](INSTALL_LINUX.md)** (Linux).

## Usage

1. **Open an image** via `File → Open` (⌘O) or by dragging and dropping it onto the window.
2. **Make a selection** with the magic wand, brush, or eraser (tab *🎯 Selection*).
   - `Shift+Click` adds to the selection, `Ctrl+Click` subtracts.
3. **Edit the background** (tab *🖼 Backgr.*): make it transparent or replace the color — or use **AI** directly in the toolbar.
4. **Transform the image** (tab *⟲ Trans.*): rotate, flip.
5. **Shape & crop** (tab *⬤ Shape*): round corners or crop to a format — move/resize the frame, then ✓ Apply.
6. **Save** via `File → Save` (⌘S) as PNG, JPEG, WebP, or TIFF.

### Settings

Via `Tools → Settings…` (⌘,) three user settings can be saved permanently:

| Setting | Description |
|---|---|
| Default directory for opening | Start directory of the open dialog; empty = last used directory |
| Default directory for export/save | Start directory of the save dialog; empty = last used directory |
| Preferred image file format | PNG, JPEG, WebP, or TIFF – appears as the first option in the save dialog |

The settings are stored persistently via **QSettings** and automatically restored the next time the program starts.

### Keyboard shortcuts

| Action | Shortcut |
|--------|----------|
| Open image | ⌘O |
| Save image | ⌘S |
| Save image as… | ⇧⌘S |
| Undo | ⌘Z |
| Redo | ⇧⌘Z |
| Rotate 90° left | ⌘← |
| Rotate 90° right | ⌘→ |
| Clear selection | Esc |
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
The full Linux/macOS matrix under Python 3.10 and 3.12 runs on release
publishing or manually. All local/CI test installs use
`requirements/constraints.txt`; override it with
`make PIP_CONSTRAINT=/path/to/file pr-check` when needed. See
[TESTING.md](../../../TESTING.md) for the full testing workflow.

Code-style check and static type checking:

```bash
make lint
make type
```

## Architecture (brief overview)

Since round 5, BgRemover is an installable package (`bgremover/`,
launched via `python -m bgremover` or the `bgremover` console script):

- **`ImageCanvas`** (QGraphicsView) holds the image state, the selection mask,
  undo/redo stacks, and the tools (magic wand, brush, lasso, crop).
- **`MainWindow`** builds the toolbar, the right-hand tab panel (four `_build_tab_*`
  builders), the menu, and connects everything to the canvas.
- **`RecentFiles`** encapsulates persistence, de-duplication, and the menu
  adapter for "Open Recent", so `MainWindow` only delegates the load path.
- **Workers** (`ImageLoadWorker`, `AIWorker`, `RembgWarmupWorker`) run in
  their own `QThread`s; `_launch_worker()` encapsulates the thread lifecycle.
- A monotonic **version counter** in the canvas discards stale AI results
  if a different image was loaded in the meantime.
- The undo stack is limited not by `maxlen` but by a **memory limit**
  (`_UNDO_MEMORY_LIMIT`); a running byte sum evicts the oldest entries.

## Known limitations

- **Maximum image size: 40 megapixels.** Larger images are rejected with a
  status message. The magic-wand selection (flood fill) runs synchronously
  in the UI thread; beyond this limit even the vectorized variant would
  cause a noticeable delay. Pillow is additionally protected against
  "decompression bomb" images.
- The **app bundle build** is macOS-specific; on Linux/Windows the
  application runs by starting `python -m bgremover` directly.

## Log file

When the program starts, a log file `bgremover.log` is created in the
platform-specific app data directory
(macOS: `~/Library/Application Support/BgRemover/`,
Linux: `~/.local/share/BgRemover/`). It contains stack traces and
status messages and is the first place to look when problems occur.

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
