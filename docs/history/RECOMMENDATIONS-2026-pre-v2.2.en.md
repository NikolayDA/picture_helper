# Historical work log: recommendations rounds 1-5

Frozen on: 2026-05-24, commit 1cf8461.
Current status: ../i18n/en/RECOMMENDATIONS.md.

---

[Deutsch](../../RECOMMENDATIONS.md) · **English** · [Español](../i18n/es/RECOMMENDATIONS.md) · [Français](../i18n/fr/RECOMMENDATIONS.md) · [Українська](../i18n/uk/RECOMMENDATIONS.md) · [简体中文](../i18n/zh/RECOMMENDATIONS.md)

# Code analysis & rated recommendations: BgRemover

## Rating scale

| Symbol | Priority | Meaning |
|--------|-----------|-----------|
| 🔴 | Critical | Must be fixed – leads to errors, crashes, or inconsistencies |
| 🟠 | High | Should be fixed soon – significantly impairs reliability or maintainability |
| 🟡 | Medium | Recommended – improves code quality, readability, or testability |
| 🟢 | Low | Optional – polishing, supplementary improvements |

---

## Current Status (Round 6)

This file intentionally keeps historical findings from the monolith
phase. The current codebase is now the `bgremover/` package;
`BgRemover.py` has been deleted. The latest post-package-cut PR series
is captured here as a compact work log:

| # | Package | Status |
|---|---------|--------|
| 1 | AI state revision: discard late `rembg` results after intervening edits | ✅ #72 |
| 2 | Lightweight PR CI + testing docs synchronization | ✅ #73 |
| 3 | CI app smoke test and starter syntax checks | ✅ #70 |
| 4 | Release/changelog hygiene | ✅ #74/#75 |
| 5 | More robust local test environment (`make doctor`, `make pr-check`) | ✅ #76 |
| 6 | Dependency/build reproducibility (`requirements/constraints.txt`) | ✅ #77 |
| 7 | Resource docs synchronized with package layout, constraints, and workflows | ✅ #78 |
| 8 | Recommendations/roadmap docs brought up to current status | ✅ this PR |

The static test `tests/test_recommendations_docs.py` keeps this section
from becoming stale again; the resource inventory is additionally guarded
by `tests/test_resource_docs.py`.

---

## Prioritized summary

| # | Recommendation | Priority | Effort |
|---|-----------|-----------|---------|
| 1 | ~~Python version conflict in type hints~~ | ✅ Fixed | – |
| 2 | ~~Broad exception catching on rembg import~~ | ✅ Fixed | – |
| 3 | ~~Race conditions in worker threads~~ | ✅ Fixed | – |
| 4 | ~~Image-size validation on load~~ | ✅ Fixed | – |
| 5 | ~~Undo-stack memory consumption~~ | ✅ Fixed | – |
| 6 | ~~Split up god classes~~ | ✅ Fixed | – |
| 7 | ~~Refactor overly long methods~~ | ✅ Fixed | – |
| 8 | ~~Replace magic numbers~~ | ✅ Fixed | – |
| 9 | ~~Tests for thread scenarios~~ | ✅ Fixed | – |
| 10 | ~~Add return type hints~~ | ✅ Fixed | – |
| 11 | ~~Add docstrings~~ | ✅ Fixed | – |
| 12 | ~~Platform-independent log file path~~ | ✅ Fixed | – |
| 13 | ~~Deduplicate thread boilerplate~~ | ✅ Fixed | – |

---

## Recommendations in detail

### ✅ 1. Python version conflict in type hints *(fixed)*

**File**: `pyproject.toml`

`requires-python` raised to `>=3.10`, `ruff target-version` updated to `py310`. The `X | Y` syntax (PEP 604) used in the code is thereby covered by the declared minimum requirements.

---

### ✅ 2. Overly broad exception catching on the rembg import *(fixed)*

**File**: `BgRemover.py` (line 41)

`except BaseException:` replaced with `except (ImportError, RuntimeError, OSError, SystemExit):`. `KeyboardInterrupt` and other critical signals are no longer caught. `SystemExit` is explicitly kept, since known rembg/onnxruntime versions can raise it on import.

---

### ✅ 3. Race conditions in worker threads *(fixed)*

**File**: `BgRemover.py`

- A new `_launch_worker()` helper in `MainWindow` encapsulates the identical thread boilerplate (it was duplicated three times). All three flows (image load, AI, warmup) now use it.
- The stale check in `_on_ai_done()` now uses `_canvas._version` (a monotonic integer counter that is incremented on every image change in `apply_loaded_image()`) instead of the fragile `is` object-identity comparison. `_ai_input_version` in `MainWindow` stores the value at AI start.

---

### ✅ 4. Missing image-size validation on load *(fixed)*

**File**: `BgRemover.py`

Introduced the constant `_MAX_MEGAPIXELS = 100`. Check after the lazy `Image.open()` in two places:
- `ImageLoadWorker.run()`: emits an `error` signal with an error message (file-dialog path)
- `ImageCanvas.load_image()`: emits `statusMsg` and aborts (drag-and-drop path)

---

### ✅ 5. High memory consumption of the undo stack *(fixed)*

**File**: `BgRemover.py`

Introduced the constant `_UNDO_MEMORY_LIMIT = 256 MB`. The undo stack no longer has a hard `maxlen` – instead, after every push the total size (estimated as `width × height × 4` bytes per RGBA image) is calculated and the oldest entries are removed as long as the limit is exceeded.

---

### ✅ 6. Split up god classes *(fixed)*

**File**: `BgRemover.py`

The 6 nested helper functions from `_build_right_panel()` (`sec`, `lbl`, `hdivider`, `scroll_tab`, `btn`, `slider_row`) were extracted as `@staticmethod` class methods of `MainWindow`: `_make_section`, `_make_label`, `_make_hdivider`, `_make_scroll_tab`, `_make_panel_btn`, `_make_slider`. `_TAB_STYLE` was factored out as a class attribute.

---

### ✅ 7. Refactor overly long methods *(fixed)*

**File**: `BgRemover.py`

The 8 icon-drawing branches from `make_tool_icon()` (175 lines, an if-elif cascade) were extracted as separate module functions: `_draw_wand_icon`, `_draw_brush_icon`, `_draw_eraser_icon`, `_draw_ai_icon`, `_draw_open_icon`, `_draw_save_icon`, `_draw_undo_icon`, `_draw_restore_icon`. `make_tool_icon()` is now a lean dispatcher via a `dict`.

---

### ✅ 8. Replace magic numbers with named constants *(fixed)*

**File**: `BgRemover.py`

New constants block at the module head:
- UI layout: `_TOOLBAR_WIDTH`, `_TOOLBAR_BTN_SIZE`, `_TOOLBAR_ICON_SIZE`, `_RIGHT_PANEL_WIDTH`, `_CROP_BAR_HEIGHT`, `_HISTORY_LIST_H`, `_COLOR_BTN_SIZE`, `_TAB_ICON_PX`, `_WINDOW_MIN_W/H`
- Canvas defaults: `_DEFAULT_TOLERANCE`, `_DEFAULT_BRUSH_RADIUS`, `_ZOOM_FACTOR`
- Overlay color: `_OVERLAY_COLOR`

All usages in the code were switched over to the constants.

---

### ✅ 9. Tests for worker error paths *(fixed)*

**File**: `tests/test_workers.py` (new, 9 tests)

New tests:
- `ImageLoadWorker`: missing file, corrupt file, oversized image (via mock)
- `ImageLoadWorker`: normal case (no error expected)
- `ImageCanvas.load_image()`: oversized image (drag-and-drop path)
- `AIWorker`: error signal on a `rembg_remove` exception, success case (via mock)
- Canvas `_version` counter: increments on `apply_loaded_image`, unchanged on undo

---

### ✅ 10. Added return type hints *(fixed)*

**File**: `BgRemover.py`

77 functions and methods without a return annotation were given `-> None` (or a specific type). In addition, `QFont` was added to the PyQt6 import (needed for `_text_font() -> QFont`).

---

### ✅ 11. Missing docstrings on helper methods *(fixed)*

**File**: `BgRemover.py`

Added one-line docstrings to `_make_label`, `_make_hdivider`, `_make_panel_btn`, and `_make_slider`. The cursor generators (`make_wand_cursor`, `make_brush_cursor`, `make_eraser_cursor`) already had docstrings.

---

### ✅ 12. Make the log file path platform-independent *(fixed)*

**File**: `BgRemover.py`

Added `QStandardPaths` to the PyQt6 imports. Log path switched from `Path.home() / ".bgremover.log"` to `QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) / "bgremover.log"` (Linux: `~/.local/share/BgRemover/`, macOS: `~/Library/Application Support/BgRemover/`).

---

### ✅ 13. Deduplicate duplicated thread boilerplate *(fixed)*

**File**: `BgRemover.py`

The `_launch_worker()` helper was already introduced as part of fix #3 (race conditions). All three worker flows (image load, AI, warmup) have used it since then.

---

## Round 2 – Follow-up review (code, tests, docs, license)

> Correction to round 1: Items **#6 (god classes)** and **#8 (magic
> numbers)** were marked as ✅ but only applied _partially_
> (`MainWindow`/`_build_right_panel` remained ~300 lines; several
> stylesheet/layout numbers stayed inline). Round 2 addresses the
> remaining points.

| # | Recommendation | Priority | Status |
|---|-----------|-----------|--------|
| R1 | Logging setup: called before `QApplication`, directory not created | 🔴 | ✅ Fixed |
| R2 | Flood fill blocks the UI; 100-MP limit too high | 🟠 | ✅ Fixed |
| R3 | Drag&Drop / "Open Recent" bypassed the async worker | 🟠 | ✅ Fixed |
| R4 | Encapsulation breach (`_pil`/`_version`/`_img_item`/`_cx…`) | 🟡 | ✅ Fixed |
| R5 | `undo_to` inconsistent (not recoverable) | 🟡 | ✅ Fixed |
| R6 | `MainWindow` god object / `_build_right_panel` | 🟡 | ✅ Fixed |
| R7 | No type check in CI | 🟡 | ✅ Fixed |
| R8 | `pyproject` ignored `F401` globally | 🟢 | ✅ Fixed |
| R9 | `make_tool_icon`: import in a loop, silent `except` | 🟢 | ✅ Fixed |
| R10 | `_apply_pil` summed the undo stack O(n) per action | 🟢 | ✅ Fixed |
| R11 | No decompression-bomb protection | 🟡 | ✅ Fixed |
| R12 | Test gaps (undo eviction, geometry, lasso, drop) | 🔴/🟠 | ✅ Fixed |
| R13 | Docs: wrong Python version, missing license | 🟠 | ✅ Fixed |

**R1** — Logging factored out into `_setup_logging()`; it is called in
`__main__` **after** `QApplication` + `setApplicationName/setOrganizationName`.
The target directory is created via `mkdir(parents=True, exist_ok=True)`
(fallback `~/.bgremover`).

**R2** — `flood_fill` is vectorized (similarity mask in a few
NumPy operations, then region growth); `_MAX_MEGAPIXELS` from 100 → 40.

**R3** — New signal `ImageCanvas.loadRequested`; `dropEvent` and
`_open_recent` now go through `_load_image_async` (worker path).
`load_image` remains as a synchronous path for tests/drop fallback.

**R4** — Public accessors: `ImageCanvas.image/has_image/version/
fit_to_view()` and `CropOverlayItem.top_left/size`. `MainWindow` and
`ImageCanvas` no longer access privates cross-class.

**R5** — `undo_to()` behaves like multiple `undo()` calls (each step
onto the redo stack) and is thus recoverable via `redo()`; in addition,
a crop guard like in `undo()`.

**R6** — `_build_right_panel()` is a lean dispatcher; four
`_build_tab_selection/background/transform/shape` builders each attach a
tab (tab index from `addTab()`).

**R7** — `mypy` configured in `pyproject.toml` (pragmatically: Qt-override
and tuple-lambda noise silenced via `disable_error_code`) and
added as a CI step.

**R8/R9/R10/R11** — `F401` ignore removed, two unused imports
deleted; `make_tool_icon` uses the module `Image` import and logs
failures with `logger.debug`; running undo byte sum `_undo_bytes`
(O(1)); `Image.MAX_IMAGE_PIXELS` coupled to `_MAX_MEGAPIXELS`.

**R12** — New tests (81 → 108): undo memory-limit eviction +
byte tracking, `tests/test_geometry.py` (rotate/flip/corners/crop),
lasso + `_paint_brush` + `apply_remove/replace` success case,
`tests/test_drop_and_history.py` (async drop, `undo_to` redo),
`_setup_logging` directory creation.

**R13** — README/INSTALL_MAC: Python **3.10+**; README extended with
architecture, known limitations, the correct log path, and a **license
section**; `LICENSE` (GPL-3.0) added; `pyproject.toml` with
`license`/`authors`/`urls`/`classifiers`. License recommendation:
**GPL-3.0-or-later** (matches PyQt6's GPL obligation; permissive only with
a switch to PySide6).

---

## Round 3 – Before the feature extension

> Two optimization rounds are complete; round 3 collects the low-risk
> cleanups worth doing before a planned feature extension.
> Recommendation **#1 (monolith → package)** is deliberately deferred:
> high priority, but also high effort/risk and in conflict with the
> documented single-file design decision — a separate decision. The
> status column references the implementing PR.

| # | Recommendation | Priority | Effort | Status |
|---|-----------|-----------|---------|--------|
| 1 | Monolith → package (`bgremover/` with modules) | 🟠 High | High | ✅ resolved (round 5) |
| 2 | ~~`save_image()` without error handling~~ | 🟡 Medium | Low | ✅ #48 |
| 3 | ~~State duplication in `undo/redo/undo_to/restore_original/_apply_pil`~~ | 🟡 Medium | Low | ✅ #52 |
| 4 | ~~Scattered inline stylesheets, no theme module~~ | 🟡 Medium | Medium | ✅ #53 |
| 5 | ~~No SessionStart hook for Claude Code on the web~~ | 🟡 Medium | Low | ✅ #51 |
| 6 | ~~Repeated "no image loaded" guards (~8×)~~ | 🟢 Low | Low | ✅ 2.1.0 |
| 7 | ~~Worker boilerplate (try/except/log/emit) → base class~~ | 🟢 Low | Low | ✅ 2.1.0 |
| 8 | ~~Maintain `CHANGELOG [Unreleased]`~~ | 🟢 Low | Low | ✅ ongoing |
| 9 | ~~`mypy` very permissive (7 disabled codes)~~ | 🟢 Low | Medium | ✅ round 4 #4 |

**#1** — `BgRemover.py` is still a single file (~3000 lines: helpers,
worker, canvas, UI, dialogs, logging, main). The biggest lever for
feature growth, but the highest risk (risk: high) and in conflict with
the documented single-file decision. **Open — deliberately deferred**,
needs a separate design decision.

→ **Resolved in round 5** (design decision: clean package break – see below).

**#2** — Fixed in **PR #48**: `save_image()` returns `bool` and wraps
the write operations in `try/except` (logging + status message),
consistent with `apply_remove/replace`; "Save as…" no longer remembers
a failed path as the quick-save target (`BgRemover.py:1080–1113`).

**#3** — Fixed in **PR #52** (originally #49, cleanly re-created after a
merge conflict): the identical image-state block was merged into the
helpers `_set_image_state()` / `_emit_history()`; behavior unchanged
(`BgRemover.py:877`, `:891`).

**#4** — Fixed in **PR #53** (originally #50): a central `_Theme` color
palette that the reused templates reference (byte-identical verified,
218 stylesheets, no visual difference). Dead constants
`BTN_STYLE`/`GRP_STYLE` removed (`BgRemover.py:1547`).

**#5** — Fixed in **PR #51**: a synchronous `SessionStart` hook
(`.claude/hooks/session-start.sh`, git mode 100755) installs the Qt
system libraries + the project and sets `QT_QPA_PLATFORM=offscreen`
persistently; registered in `.claude/settings.json`.

**#6** — **✅ Done (2.1.0).** The "no image loaded" early-return of the
five affected `ImageCanvas` methods is consolidated in the
`@_requires_image` decorator (`bgremover/canvas.py`).

**#7** — **✅ Done (2.1.0).** `AIWorker` and `ImageLoadWorker` share the
`_Worker` base class, which encapsulates the
`try/except → logger.exception → error.emit` flow
(`bgremover/workers.py`); `RembgWarmupWorker` deliberately stays
standalone.

**#8** — Honored: the round-3 PRs #48/#52/#53 each maintain the
`CHANGELOG [Unreleased]` section; this entry additionally documents
round 3 itself. An ongoing practice rather than a single PR.

**#9** — **✅ Done (round 4 #4).** `disable_error_code` is fully removed
from `pyproject.toml` – all formerly 8 disabled error classes are
active (details see round 4 #4 below).

---

## Round 4 – Status check & next step

> Analysis state: `ruff` clean, `mypy` clean, **140 tests green**
> (16 UI tests intentionally deselected). Code quality is high – round 4
> therefore prioritizes **what to tackle next concretely**, rather than
> hunting for new defects.

| # | Recommendation | Priority | Effort | Status |
|---|----------------|----------|--------|--------|
| 1 | ~~Release cut 2.1.0 + git tag~~ | 🟠 High | Low | ✅ Done (tag after merge) |
| 2 | ~~"No image loaded" guard helper (round 3 #6)~~ | 🟢 Low | Low | ✅ Done |
| 3 | ~~Worker base class (round 3 #7)~~ | 🟢 Low | Low | ✅ Done |
| 4 | ~~Tighten `mypy` step by step (round 3 #9)~~ | 🟢 Low | Medium | ✅ Done (all 8 codes active) |
| 5 | Monolith → package (round 3 #1) | 🟠 High | High | ✅ resolved (round 5) |

### ✅ 1. Release cut 2.1.0 + git tag *(done)*

**Done in this PR:** `pyproject.toml` and the `__version__` fallback
(`BgRemover.py`) bumped to `2.1.0`; the `[Unreleased]` block in
`CHANGELOG.md` (+ i18n en/es/fr/uk/zh) dated as `[2.1.0] – 2026-05-19`
and a fresh empty `[Unreleased]` block added. The `git tag v2.1.0` is
**deliberately not** set on the feature branch; it belongs on the merge
commit in `main` after merge (see the PR description).

**Finding (for the record):** there was **not a single git tag**
(`git tag -l` empty), even though the CHANGELOG claims a "first
publicly tagged release 2.0.0". Since 2.0.0 the `[Unreleased]` block
had accumulated substantial changes (PR #48 save error handling, #52
state dedup, #53 `_Theme`, INSTALL_LINUX docs, #55 local test runner),
while `pyproject.toml` and the `__version__` fallback still read
`2.0.0`.

### ✅ 2. "No image loaded" guard helper *(done, round 3 #6)*

The byte-identical early-return `if self._pil is None:
self.statusMsg.emit("Kein Bild geladen"); return` of the five
`ImageCanvas` methods `apply_round_corners`, `apply_rotate`,
`apply_flip`, `start_crop_circle`, `start_crop_ratio` is consolidated
in the `@_requires_image` decorator. Behavior unchanged (140 unit + 16
UI tests green). The three `MainWindow` `has_image` guards
intentionally stay inline: differing messages and order-dependent
secondary checks – consolidating them there would add more risk than
value.

### ✅ 3. Worker base class *(done, round 3 #7)*

`AIWorker` and `ImageLoadWorker` now inherit from the base class
`_Worker`, which encapsulates the identical
`try/except → logger.exception → error.emit` flow; subclasses only
implement `_work()`. `RembgWarmupWorker` intentionally stays standalone
(no `error` signal, `finished` always in `finally` – different
contract).

### ✅ 4. Tighten `mypy` step by step *(round 3 #9 / round 4 #4 – done)*

**All previously disabled error classes are now active.** After the
monolith → package cut (round 5), the remaining six codes could be
activated file by file:

| Code | Was | Strategy |
|------|-----|----------|
| `arg-type` | 2 | `_pil`/`_arr` invariant via double-guard + loop `assert` |
| `attr-defined` | 2 | `setattr(thread, "_worker", ...)`; `_Worker \| RembgWarmupWorker` param |
| `assignment` | 4 | explicit first-time annotations (`Image.Image`, `RankFilter`, `QMenu \| None`) |
| `func-returns-value` | 4 | UI lambda tuples → local `def` slots |
| `override` | 7 | signatures aligned with the PyQt6 stubs (`QPainter \| None` etc.) |
| `union-attr` | 67 | status/menu bar and viewport cached; targeted asserts |

In `pyproject.toml`, only `check_untyped_defs = false` remains as a
pragmatic Qt noise dampener (covers Qt override signatures
event/option/widget).

### 🟠 5. Monolith → package *(round 3 #1, intentionally deferred)*

`BgRemover.py` is still a single file at **3003 lines**. Biggest lever
for feature growth, but highest risk and in conflict with the
documented single-file design decision. Remains a deliberate, separate
architectural decision – to be reconsidered at the latest before the
next larger feature expansion. Quick wins #2/#3 already shrink the file
slightly and prepare a later split.

→ **Resolved in round 5** (design decision: clean package break – see below).

---

## Round 5 – Design decision: monolith → package (resolved)

> The "separate design decision" explicitly demanded in round 3 #1 and
> round 4 #5 is hereby made and thus resolved. The documented
> single-file design decision is **deliberately reversed**.

**Decision.** `BgRemover.py` (3026 lines) is split into a Python package
`bgremover/`. Modules: `constants`, `image_utils`, `icons`, `theme`,
`workers`, `crop`, `canvas`, `widgets`, `settings_dialog`,
`logging_config`, `main_window`, `app`, `__main__`, `__init__`.

**Clean package break (no compatibility shim).** `BgRemover.py` is
removed outright. The app is launched via the `bgremover` console script
**and** `python -m bgremover`. The previous `python -m bgremover` mode is
**deliberately dropped**; the build scripts (`create_BgRemover_app.sh`,
`BgRemover.command`), `pyproject.toml`, Makefile/CI, tests and docs
(incl. i18n) are migrated in the same cut.

**Rationale.** Per round 3 #1 / round 4 #5 the single file was the
biggest lever for feature growth; the only blocker was the documented
single-file decision – which is hereby explicitly reversed. The risk
stays high but is controlled by the method.

**Method.** Phased with a hard gate: **Phase A** (preparation – this ADR
+ layout/design, no code moved) → **Gate** (green baseline captured:
`ruff`/`mypy` clean, **140 unit + 16 UI tests green**) → **Phase B**
(purely mechanical, byte-identical split; code moved verbatim, only
imports adjusted; tests stay green). The single intentional code change:
asset resolution in `make_tool_icon` (`importlib.resources` instead of
`__file__`/`argv`/`cwd`), behavior-preserving.

**Order / preparatory work.** Precondition met: `git tag v2.1.0` is set
(at the PR #60 merge) and published as a GitHub prerelease – the last
pure single-file state is thus marked (round 4 #1). That the tag sits a
few commits behind `main` HEAD is an optional maintainer release
decision and irrelevant to the cut.

**Deliberately after, not before.** The incremental mypy hardening
(round 4 #4, 6 remaining `disable_error_code`) happens **after** the
split – a large move invalidates per-file type progress. Internal
cleanups (guard/worker consolidation) likewise stay out of this cut.

**Status impact.** Round 3 #1 and round 4 #5 are **resolved** with this
decision; the status columns of the respective tables are updated
accordingly.

**Phase B complete.** The mechanical split has landed (13 steps, each
gated on the green oracle: `make test` 140, `make ui` 16, `make type`,
`make lint`; both entry points `python -m bgremover` and `bgremover`
start stably). `BgRemover.py` is deleted. The package consists of 14
modules under `bgremover/`; icons ship as `package-data`
(`bgremover/icons/`). The only intentional code change remained the one
promised: asset resolution via `importlib.resources` in
`make_tool_icon` (contract unchanged). Build script, Makefile/CI and
documentation (incl. i18n) have followed.

**Recommended next step.** With the file-based layout, round 4 #4
(incremental mypy tightening) now makes sense: remove one
`disable_error_code` per module, fix, repeat. The internal cleanups
marked optional in rounds 3/4 (guard/worker unification) are also less
risky per file.
