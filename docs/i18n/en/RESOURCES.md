[Deutsch](../../../RESOURCES.md) · **English** · [Español](../es/RESOURCES.md) · [Français](../fr/RESOURCES.md) · [Українська](../uk/RESOURCES.md) · [简体中文](../zh/RESOURCES.md)

# Resources used

This document lists **all external resources** that BgRemover
uses or requires: libraries (Python packages), other software
and tools, third-party code, as well as the project's own assets — each
with its purpose, license, and source.

> Version notes: "Min." comes from `pyproject.toml` (the binding
> minimum requirement), "Verified" is the Python 3.12 baseline pinned in
> `requirements/constraints.txt` for the current local/CI checks. The
> bundled license text of the respective package is always authoritative.

---

## 1. Runtime dependencies (Python packages)

Declared in `pyproject.toml` under `[project] dependencies`.

| Package | Purpose in the program | Min. | Verified | License |
|-------|-------------------|------|---------|--------|
| **PyQt6** | The complete GUI (window, canvas, widgets, events, QSettings, QThread) | `>=6.5` | 6.11.0 | **GPL v3** or commercial Riverbank license |
| **Pillow** (PIL) | Image I/O, EXIF transpose, rotate/flip, masks/alpha, saving (PNG/JPEG/WebP/TIFF) | `>=10` | 12.2.0 | HPND (also "MIT-CMU"; the open-source PIL license) |
| **NumPy** | Pixel arrays, flood fill, mask operations | `>=1.24` | 2.4.5 | BSD-3-Clause |

Via PyQt6, the **Qt 6** framework (The Qt Company) is additionally bound.
Qt itself is licensed under LGPL v3 / GPL / commercial license; the
**PyQt6 binding** is GPL v3 — see section 8.

## 2. Optional AI dependency

Declared under `[project.optional-dependencies] ai` — needed only for the
automatic background removal (the `rembg` tool):

| Resource | Purpose | Min. | Verified | License | Source |
|-----------|-------|------|---------|--------|-------|
| **rembg[cpu]** | AI-assisted background removal (`rembg.remove`) | `>=2.0` | 2.0.75 | MIT | PyPI |
| **onnxruntime** | ONNX inference backend (transitive dependency of `rembg[cpu]`) | (transitive) | 1.26.0 | MIT (Microsoft) | PyPI |
| **U²-Net model** (`u2net.onnx`) | The default segmentation model that rembg **downloads at runtime** (not included in the repo) | – | – | Apache-2.0 (project *U-2-Net*) | Downloaded by rembg into the user cache directory |

Without the `ai` extras the program starts normally; the AI button is
then disabled (`REMBG_AVAILABLE = False`).

## 3. Python standard library

Part of CPython, **no additional installation** needed
(license: PSF License Agreement):

`sys`, `os`, `io`, `logging`, `collections.deque`, `pathlib.Path`,
`importlib.metadata`, `importlib.resources`, `contextlib`, `tempfile`.

## 4. Development & test tools

Declared under `[project.optional-dependencies] test`:

| Tool | Purpose | Min. | Verified | License |
|----------|-------|------|---------|--------|
| **pytest** | Test runner | `>=8` | 9.0.3 | MIT |
| **pytest-qt** | Qt fixtures (headless `offscreen`) | `>=4.4` | 4.5.0 | MIT |
| **ruff** | Linting / style check | `>=0.6` | 0.15.13 | MIT |
| **mypy** | Static type checking (CI step) | `>=1.10` | 2.1.0 | MIT |
| **packaging** | Parses dependency constraints in tests | `>=24` | 24.0 | Apache-2.0 or BSD-2-Clause |

Optional documentation/PDF tooling is declared under
`[project.optional-dependencies] docs`:

| Tool | Purpose | Min. | License |
|----------|-------|------|--------|
| **Markdown** | Markdown to HTML for `ANLEITUNG.pdf` | `>=3.5` | BSD |
| **WeasyPrint** | PDF rendering from HTML/CSS | `>=61` | BSD-3-Clause |
| **fonttools** | Font inspection for PDF generation | `>=4.0` | MIT |

PDF generation also needs system resources such as DejaVu fonts and
Pango/Cairo/GDK-Pixbuf (distro-packaged).

## 5. Build & distribution tools (macOS)

Required by the app bundle script `create_BgRemover_app.sh`. It bundles
**none** of these programs, but calls them via the system:

| Tool | Purpose | Origin |
|----------|-------|----------|
| `python3` + `venv` + `pip` | Create the isolated venv, install dependencies with `requirements/constraints.txt` | Python / PyPA |
| `setuptools` (build backend) | Packaging according to `[build-system]` (`>=61`) | MIT |
| `/usr/bin/arch`, `uname` | Enforce the native CPU architecture (Apple Silicon) | macOS |
| `iconutil` | Generate the `.icns` app icon from an iconset (fallback: PNG) | macOS |
| `osascript` | Display the app launcher's error messages | macOS |
| Standard shell tools | `mkdir`, `cp`, `cat`, `command`, among others | POSIX/macOS |

`BgRemover.command` is the bundled double-click starter (the project's
own code).

## 6. Continuous integration

Defined in `.github/workflows/pr-ci.yml`, `.github/workflows/ci.yml`,
and `.github/workflows/license-check.yml`. Pull requests run a
lightweight Ubuntu/Python 3.12 job; the full matrix runs on Ubuntu +
macOS with Python 3.10/3.12 for releases or manual runs; the license
workflow generates the dependency/license report.

| Resource | Purpose | License |
|-----------|-------|--------|
| `actions/checkout@v5` | Check out the repository | MIT |
| `actions/setup-python@v6` | Set up Python + pip cache | MIT |
| `actions/upload-artifact@v4` | Upload license report artifacts | MIT |
| `actions/github-script@v7` | Comment the license summary on pull requests | MIT |
| `pip-licenses` | Raw dump of installed package licenses | MIT |
| `requirements/constraints.txt` | Reproducible dependency snapshot for local checks, CI, license report, and app bundle | Project file |
| Qt system libraries via `apt` (Linux) | Headless Qt runtime: `libegl1`, `libfontconfig1`, `libxkbcommon0`, `libdbus-1-3`, `libxcb-*` | distro-packaged, various permissive/copyleft licenses (Mesa, fontconfig, libxkbcommon, libxcb, dbus …) |

## 7. The project's own resources

The project's own work, covered by the project license
(GPL-3.0-or-later, see `LICENSE`):

- **Source code**: the installable package `bgremover/`, the test suite
  under `tests/`, and project scripts under `scripts/`.
- **Toolbar/tab icons**: `bgremover/icons/*.png` (`ai`, `bg`, `brush`,
  `clear_sel`, `close`, `eraser`, `form`, `open`, `redo`, `restore`,
  `save`, `transparency`, `undo`, `wand`). Loaded by `make_tool_icon()`
  via `importlib.resources` as package data.
- **Drawn vector icons**: If a PNG is unavailable, `make_tool_icon()`
  draws the icon programmatically with `QPainter`
  (`_draw_*_icon` functions) — no external asset.
- **App icon**: `BgRemover_icon.png` (source for the macOS `.icns`).
- **Cursors**: drawn at runtime (`make_wand_cursor`,
  `make_brush_cursor`, `make_eraser_cursor`) — no external files.

**No third-party source code** is embedded in the repository
(no `vendor/` or `third_party/`); external functionality is obtained
exclusively via the packages listed above.

## 8. License compatibility (note)

BgRemover is licensed under **GPL-3.0-or-later** (`LICENSE`). This choice
is required by **PyQt6**: the binding is licensed under GPL v3 (or
commercially), so the application distributed as a whole —
in particular the bundled `BgRemover.app` — must be GPL-compliant. The
remaining runtime/AI dependencies (Pillow HPND, NumPy BSD, rembg MIT,
onnxruntime MIT, U²-Net Apache-2.0) are GPL-v3-compatible.

A **permissive** license model (MIT/Apache-2.0) would only be possible if
PyQt6 were replaced by the LGPL-v3-licensed **PySide6**.

---

*Maintenance note:* When making changes to `pyproject.toml`,
`requirements/constraints.txt`, `.github/workflows/pr-ci.yml`,
`.github/workflows/ci.yml`, `.github/workflows/license-check.yml`,
`create_BgRemover_app.sh`, or the package data under `bgremover/icons/`,
please update this document as well.
