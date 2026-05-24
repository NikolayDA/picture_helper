[Deutsch](../../../CHANGELOG.md) · **English** · [Español](../es/CHANGELOG.md) · [Français](../fr/CHANGELOG.md) · [Українська](../uk/CHANGELOG.md) · [简体中文](../zh/CHANGELOG.md)

# Changelog

All notable changes to BgRemover are documented in this file. The format
is based on [Keep a Changelog](https://keepachangelog.com/de/1.1.0/);
the project follows [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Added

- **Reproducible dependency snapshot** (`requirements/constraints.txt`).
  The Makefile, license workflow, and macOS app build use the same
  committed constraint set for test, CI, license, and app-bundle installs.
- **Local test-environment doctor** (`make doctor`,
  `scripts/check_test_env.py`). Checks the Python version, `[test]`
  dependencies, non-editable package installation, the `bgremover`
  console script, and Qt `offscreen` before a local run fails deep in
  pytest.
- **CI smoke test for application start** (`tests/test_app_smoke.py`).
  The existing UI tests are excluded from CI via `-m 'not ui'`, so CI
  never checked whether the application starts up at all – exactly the
  gap that let the macOS start failures slip through. New, without the
  `ui` marker (so it runs in CI): `python -m bgremover` and the
  `bgremover` console script are fully started from a neutral working
  directory (new self-test hook `BGREMOVER_SMOKE_TEST` quits after the
  first event-loop tick with exit code 0); the Qt plugin setup is
  checked to yield a valid plugin path; the starter scripts
  (`create_BgRemover_app.sh`, `BgRemover.command`, `diagnose_mac.sh`)
  and the launcher baked into the app bundle are shell-syntax checked.
  `zsh` is installed in the Linux CI job for this.

### Changed

- **MainWindow modularized further.** Persistence and menu semantics for
  "Open Recent" now live in `bgremover/recent_files.py`; `MainWindow`
  only delegates loading, status messages, and File-menu integration.
- **Menu/action construction extracted from `MainWindow`.**
  `bgremover/menu_actions.py` builds the menu bar, `QAction`s, shortcuts,
  and Recent-Files submenu; `MainWindow` only passes domain callbacks.
- **Right-side tab panel extracted from `MainWindow`.**
  `bgremover/right_panel.py` builds the Selection, Background, Transform,
  and Shape tabs including sliders, spin boxes, and panel buttons;
  `MainWindow` only passes canvas callbacks.

### Fixed

- **Release/changelog links corrected to real refs.** `[Unreleased]`
  now compares from `v2.1.0`; `[2.1.0]` uses the documented 2.0.0
  release commit as its base because the repository has no historical
  `v2.0.0` tag.
- **App bundle: `bgremover` detection in setup independent of the
  working directory.** `create_BgRemover_app.sh` treated the venv as
  “ready” even though `bgremover` was not installed there: the
  `has_deps` check ran with `cwd` inside the project folder, and
  Python automatically prepends the current directory to
  `sys.path[0]` – so `import bgremover` found the repo's `bgremover/`
  **source directory** instead of a real venv installation. The app
  launcher starts with a different `cwd`, does not see the source
  directory, and therefore reported “The bgremover package is missing
  in the venv”. `has_deps` and the final sanity check now run from
  `$HOME` (subshell `cd "$HOME"`), so they check the same reality as
  the launcher; if the package is missing, the pip-install fast path
  kicks in. `diagnose_mac.sh` also tests from `$HOME` and additionally
  shows `pip show bgremover` of the app venv (cwd-independent proof of
  whether/where the package is installed).
- **macOS launch paths working again.** After the package cut (round
  5), `BgRemover.command` was still looking for the no-longer-existing
  `BgRemover.py` and bailed out with “not found”; the German
  `INSTALL_MAC.md` plus the i18n versions of `INSTALL_LINUX.md` and
  `README.md` also kept some old commands (round-5 step 15 had missed
  the German `INSTALL_MAC.md` and the i18n install docs in the glob,
  plus `Exec=python3 /PATH/.../BgRemover.py` in the i18n `.desktop`
  snippets). Net effect: on macOS none of the three documented launch
  paths (app bundle, double-click `.command`, terminal) was reliably
  usable. `BgRemover.command` now starts via `python3 -m bgremover`
  and pre-checks `import bgremover` (otherwise prints a clear hint to
  `create_BgRemover_app.sh`). INSTALL_MAC + all i18n docs reflect the
  current package model (incl. non-editable install of the package
  into the app venv and `importlib.resources` asset lookup).
- **`create_BgRemover_app.sh`: existing venv migrated cleanly.** A
  venv from the monolith era (PyQt6/Pillow/numpy installed, but of
  course not yet `bgremover`) was wrongly treated as “ready” because
  the setup check `has_deps` did not test `bgremover`. On re-run, the
  package install was therefore skipped — and the app launcher then
  reported at runtime “The bgremover package is missing in the venv”.
  The check now also includes `import bgremover`; additionally there
  is a fast path: if the app venv already has PyQt6/Pillow/numpy,
  only `pip install ".[ai]"` is added (seconds) instead of rebuilding
  the venv with all dependencies (minutes).

### Changed

- **Pure image operations extracted from `ImageCanvas`.**
  `bgremover/image_ops.py` now owns background remove/replace, saving,
  rotation, flipping, rounded corners, and crop masking as Qt-free
  PIL/NumPy functions. `ImageCanvas` keeps UI state, undo/redo, signals,
  and overlays; `tests/test_image_ops.py` checks the pixel operations
  directly without a `QApplication`.
- **Recommendations documentation brought up to current status.**
  `RECOMMENDATIONS.md` and the i18n versions now include a round-6
  status block for the latest PR series (#70, #72–#78) and explicitly
  mark the old monolith findings as historical context.
  `tests/test_recommendations_docs.py` guards this block.
- **Resource documentation synchronized.** `RESOURCES.md` and the i18n
  versions now reflect the package layout (`bgremover/` instead of
  `BgRemover.py`), package data under `bgremover/icons/`, the
  reproducible constraints snapshot, and PR/full/license workflows. A
  static test guards those references against becoming stale again.
- **`make pr-check` makes the local PR check more robust.** The target
  refreshes the `[test]` package installation, runs the doctor, and then
  starts `ruff`, `mypy`, and `pytest`. The Makefile finds
  `.venv/bin/python` automatically and otherwise falls back to
  `python`/`python3`; GitHub PR CI and Full CI use the same target. The
  shared Qt plugin setup stages platform plugins into the system temp
  directory when needed so local macOS headless runs do not fail on Qt
  plugin listing issues inside the project path.
- **Lightweight PR CI added and testing docs synchronized.** Pull
  requests now get a cheap Ubuntu/Python 3.12 workflow with
  `make pr-check`; the full Linux/macOS matrix remains reserved for
  release and manual runs. The test workflows install the package
  non-editably so the app smoke tests check the installed reality from
  a foreign `cwd`. `README`, i18n READMEs, `TESTING.md`, and `Makefile`
  now describe the same workflow.
- **Monolith → package (round 5).** The single-file `BgRemover.py`
  (3026 lines) has been split into the installable package `bgremover/`
  (14 modules: `constants`, `image_utils`, `icons`, `theme`, `workers`,
  `crop`, `canvas`, `widgets`, `settings_dialog`, `logging_config`,
  `main_window`, `app`, `__main__`, `__init__`). Launched via
  `python -m bgremover` or the `bgremover` console script; the old
  `python BgRemover.py` form is removed without replacement.
  `BgRemover.py` is deleted. Performed in **13 mechanical steps**,
  each gated on the green test oracle (140 unit + 16 UI tests, ruff,
  mypy). The single intentional, behaviour-neutral code change:
  `make_tool_icon` now resolves icons via `importlib.resources` from
  package data (`bgremover/icons/`) instead of `__file__`/`sys.argv`/
  `cwd` – contract unchanged. `pyproject.toml`, `Makefile`, CI workflow
  and the macOS build script (`create_BgRemover_app.sh`) followed in
  the same cut; the venv installs the package non-editably (incl.
  package-data), making the app independent of the project folder.
- Transitional re-exports in `BgRemover.py` (phase B) and all
  `BgRemover` test imports were switched to the package in the final
  step.

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

First documented 2.0.0 release state. The repository has no historical
`v2.0.0` Git tag.

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

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1...v2.1.0
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1
