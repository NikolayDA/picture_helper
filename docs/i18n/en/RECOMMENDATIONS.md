[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code analysis & rated recommendations: BgRemover

## Rating scale

| Symbol | Priority | Meaning |
|--------|-----------|-----------|
| 🔴 | Critical | Must be fixed – leads to errors, crashes, or inconsistencies |
| 🟠 | High | Should be fixed soon – significantly impairs reliability or maintainability |
| 🟡 | Medium | Recommended – improves code quality, readability, or testability |
| 🟢 | Low | Optional – polishing, supplementary improvements |

---

## Current status (2026-06-01, "modest-shannon" review)

Deep review of the post-v2.2 codebase (code, docs, tests). Baseline excellent: ruff/mypy clean, test suite green, coverage 88%. Found **5 findings (A–E)** — all implemented, with regression tests, and merged via **PR #135** (A, B) and **PR #136** (C–E). Evidence given with a file/function reference.

### Completion status

| Status | Items |
|--------|-------|
| ✅ Done | A, B, C, D, E |

### Findings

- **A 🟠 — Catch `DecompressionBombError`.** `image_loading.py` did not catch Pillow's `DecompressionBombError` (not an `OSError` subclass) → images above 2× `MAX_IMAGE_PIXELS` (80 MP) bypassed the friendly "too large" message and propagated uncaught on the synchronous `load_image` path. Now caught in both open phases and mapped to the standard message; the regression test triggers Pillow's real bomb guard (no `Image.open` mock).
- **B 🟡 — Magic-wand lifecycle on image change.** `_reset_transient_state` (`canvas.py`) did not reset `_wand_busy`, and `_load_image_async` (`main_window.py`) did not cancel the flood fill — asymmetric with `cancel_ai()`. Result: the wand stayed blocked after an image change/restore, plus wasted CPU. Central flag reset + `cancel_flood_fill()` on load.
- **C 🟡 — Logging isolation.** `_setup_logging` (`logging_config.py`) used `basicConfig(force=True)` on the root → third-party logs (rembg/onnxruntime/Pillow) ended up in the support log file, and foreign handlers were torn off. Now the named `BgRemover` logger with its own handlers (`propagate=False`).
- **D 🟢 — Test cruft.** `test_static_checks.py` probed for the removed `BgRemover.py` monolith and carried misleading `#N` markers (historical rounds ≠ current numbering). Monolith branch removed, origin clarified in the docstring.
- **E 🟢 — i18n safety net.** The soft-drift check covered only 3 of 8 translated docs. `WATCHED_DOCS` extended to all 8 (all currently in structural sync).

---

## Open recommendations

Improvements from the second analysis that are not yet implemented (product/process):

- **O1 🟠 — App localization.** The UI is hardcoded German; there is no runtime i18n (no `QTranslator`/`tr()`), although the docs exist in five languages. Status messages are already centralized (`status_messages.py`). Incrementally via Qt Linguist (`.ts`) or a lightweight `QLocale` string table.
- **O2 🟡 — Linux app / packaging.** No app bundle for Linux; launch only via `python -m bgremover` from a venv. An installable package (AppImage/Flatpak/`.deb`) for **Raspberry Pi OS** and major distributions (Debian/Ubuntu/Fedora) lowers the entry barrier for non-developers — analogous to the macOS `.app` bundle.
- **O3 🟡 — Full CI matrix earlier.** The full matrix (Linux/macOS × 3.10–3.13) runs only on tags/release; regressions on macOS or Python 3.10/3.13 surface late. Also run it on push to `main` or as a weekly cron.
- **O4 🟢 — Keyboard shortcuts for tools.** Magic wand/brush/eraser/lasso are reachable only by mouse; add single-key switching (e.g. `B`/`E`).

---

## Previous round (v2.2, "admiring-mayer")

External 15-point list checked against the codebase: **#1–#15 done, #4 discarded** (false positive). Details in the merged PRs and the archive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
