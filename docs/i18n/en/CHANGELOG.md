[Deutsch](../../../CHANGELOG.md) · **English** · [Español](../es/CHANGELOG.md) · [Français](../fr/CHANGELOG.md) · [Українська](../uk/CHANGELOG.md) · [简体中文](../zh/CHANGELOG.md)

# Changelog

All notable changes to BgRemover are documented in this file. The format
is based on [Keep a Changelog](https://keepachangelog.com/de/1.1.0/);
the project follows [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

## [2.1.0] – 2026-05-19

### Changed

- Consolidated the "no image loaded" early-return guard of the five
  `ImageCanvas` methods (`apply_round_corners`, `apply_rotate`,
  `apply_flip`, `start_crop_circle`, `start_crop_ratio`) into the
  `@_requires_image` decorator – the previously byte-identical block is
  gone; behavior unchanged (defended by the existing test suite).
- Background workers `AIWorker` and `ImageLoadWorker` now share the
  common base class `_Worker`, which encapsulates the identical
  `try/except → logger.exception → error.emit` flow; subclasses only
  implement `_work()`. `RembgWarmupWorker` intentionally stays
  standalone (no `error` signal, `finished` always in `finally`).
- Version cut **2.1.0**: `pyproject.toml` and the `__version__`
  fallback in `BgRemover.py` bumped to `2.1.0`; the changes previously
  collected under `[Unreleased]` (#48/#52/#53, INSTALL_LINUX, rounds
  3/4) are hereby dated as 2.1.0.

### Documentation

- Added an installation guide for Linux (`INSTALL_LINUX.md`):
  system packages per distribution (apt/dnf/pacman), venv setup,
  starter script or `.desktop` entry, and troubleshooting; linked from
  the README. Including a particularly simple path for Raspberry Pi OS
  (Desktop) without venv/pip (PyQt6/Pillow/numpy as system packages via
  `apt`), with an optional AI add-on step.

## [2.0.0] – 2026-05-17

First publicly tagged release.

### Features

- AI background removal via `rembg` (optional `ai` extra) including a
  background warmup so that the first click does not block.
- Selection tools: magic wand (vectorized flood fill with a tolerance
  slider), brush, eraser, and polygon lasso; Shift/Ctrl for additive
  or subtractive selection.
- Make the background transparent or replace it with a color.
- Transformations: rotate (90° steps and free angle), flip,
  round corners, crop in several formats with a rule-of-thirds grid.
- History with undo/redo (toolbar buttons) and jumping to any earlier
  step via a floating history popup.
- Drag & drop as well as "Open Recent" (10 entries), both via the
  asynchronous loading worker – no UI freeze.
- Save as PNG, JPEG, WebP, or TIFF.
- Persistent settings (default directories, preferred file format)
  via `QSettings`.
- macOS app bundle build (`create_BgRemover_app.sh`) including an
  isolated venv, Apple Silicon handling, and icon assignment; supports
  Python 3.10–3.15.

### Stability & quality

- Worker threads hardened (no premature GC of the worker,
  clean thread shutdown in `closeEvent`, AI race handled via a monotonic
  canvas version counter).
- Image-size limit (40 MP) and decompression-bomb protection on load.
- Memory-limited undo stack (256 MB) with O(1) byte tracking.
- Platform-independent log path (`bgremover.log` in the app data directory).
- 108 tests; `ruff` and `mypy` as CI steps; CI on Ubuntu and macOS
  under Python 3.10 and 3.12.
- `__version__` is read from the package metadata (single source);
  the version appears in the window title.

### Documentation & license

- License **GPL-3.0-or-later** (`LICENSE`); required by the
  GPL-licensed PyQt6 binding.
- `RESOURCES.md` (all libraries/tools/assets along with their licenses),
  `LICENSES.md`, and an automated license/compliance workflow.
- README with architecture, known limitations, and installation
  instructions; detailed `INSTALL_MAC.md`.

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/NikolayDA/picture_helper/releases/tag/v2.0.0
