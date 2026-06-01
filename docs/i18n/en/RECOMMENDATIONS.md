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

## Current status (2026, "admiring-mayer" review)

Review of an externally submitted recommendation list (15 findings) against the actual codebase. Result: **14 confirmed, 1 false positive** (#4). The confirmed findings are grouped below into **six implementation packages**; the package order is also the recommended order of work. Each entry records the original finding, the evidence (`file:line`), and the direction of the fix; the table below is authoritative for the current implementation status. The numbering (#1–#15) matches the original review list.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).

### Completion status (checked 2026-06-01)

| Status | Items |
|--------|-------|
| ✅ Done | #1, #2, #3, #5, #6, #7, #8, #10, #11, #12, #13, #14, #15 |
| ➖ Discarded | #4 – false positive |

---

## Recommendation packages

**Package 1 — Do immediately** 🔴

- **#1 AI cancellation must finish the thread.** `AIWorker._work` (`bgremover/workers.py:74`) returns on cancel without emitting a signal; `quit_on=(finished, error)` (`bgremover/worker_controller.py:152`) then never fires → the QThread keeps running, `ai_thread`/`ai_worker` stay set, and the AI button stays disabled for the rest of the session (trigger: "load an image while the AI is running"). Fix: emit a parameterless `done` signal in the `finally` branch (`_always_finished`) and add it to `quit_on` — the infrastructure already exists (warmup worker). **Implemented in this PR, incl. a cancel-lifecycle test.**

**Package 2 — Quick, safe wins (done)** 🟠 🟡

- **#2 Reset transient canvas state centrally.** `apply_loaded_image` (`canvas.py:234`) calls `cancel_overlay_only()` without `cropModeChanged(False)` and does not cancel the lasso → the crop signal sequence stays `[True]`, old lasso points survive. Introduce a `_reset_transient_state()` method.
- **#11 Configure logging independently of foreign handlers.** `logging.basicConfig()` (`logging_config.py:61`) is a no-op once the root logger already has handlers → the displayed log path ≠ the one actually written. Configure the named `BgRemover` logger explicitly (cleaner than `force=True`).
- **#10 Point the diagnostic script at the current log path.** `diagnose_mac.sh:178` still reads `~/.bgremover.log`; the logger actually writes to `~/Library/Application Support/BgRemover/bgremover.log` (QStandardPaths). Align the path.
- **#8 Normalize the export format robustly.** `_save_as` (`main_window.py:304`) discards the chosen dialog filter; `save_image_file` (`image_ops.py:46`) silently saves as PNG when the extension is missing. Central format model with a default suffix; merge the duplicated format dicts (dialog vs. MainWindow). *(The reported EXR `KeyError` is only reachable via tampered settings/dict drift — the missing-extension case is the user-facing core.)*
- **#14 Sync CI and doc checks.** `RESOURCES.md:102` and `TESTING.md:10` still say "3.10/3.12" (actually 3.10–3.13); `ui-nightly.yml` is missing from the workflow lists and from `test_resource_docs.py:35`. Check the workflow list and the Python matrix too.
- **#15 Make the release CI a real gate.** `ci.yml` runs the full matrix only on `release: published` (too late as a gate); `ui-nightly.yml:18` `continue-on-error: true` masks failures. Add a tag/pre-release candidate run and let nightly failures escalate visibly.

**Package 3 — Substance with measurement (done)** 🟠

- **#5 Don't reallocate the overlay on every brush move.** `_refresh_overlay` (`canvas.py:263`) → `mask_to_overlay` builds a full RGBA overlay (40 MP ≈ 160 MiB) — even for an empty mask and on every mouse move. Build it lazily, update a dirty region, or coalesce events.
- **#6 Bound the magic wand, make it cancellable, benchmark it.** `flood_fill` (`image_utils.py:48`) grows the region in Python; measured ≈ 3.3 s at 2.25 MP (→ double-digit seconds at 40 MP). Add a scanline/native implementation (e.g. `scipy.ndimage.label`) and a cancel path.
- **#7 Serialize the rembg warmup and the AI call.** `_on_warmup_done` (`main_window.py:270`) shows "AI ready" even after warmup errors; the AI button stays usable during warmup → parallel model init. Separate success/error, gate the button until warmup finishes.
- **#3 Enforce the history memory budget.** `restore` (`canvas_history.py:81`) and `redo` (`:47`) append to the undo stack but bypass the eviction in `push` → repeated restoring grows unbounded. Use a shared trim helper and test the total budget.

**Package 4 — Security (done)** 🟡

- **#12 Harden the temporary Qt plugin staging.** `qt_plugins.py` (lines 26/29/48) uses a predictable path under `/private/tmp` on macOS, fixed `.tmp` files, and only a size comparison. Since executable Qt plugins are loaded from there, pre-seeding is a local code-injection vector. Use a user-specific `0700` directory, unique temp files, and a content/hash check.

**Package 5 — Tests & methodology** 🟡

- **#13 Orient tests toward behavior, not source text.** The AST checks in `test_static_checks.py` only check for string occurrences and do not catch the AI cancellation bug (#1). Add dynamic tests for the cancel lifecycle, loading during crop/lasso, warmup error, unknown export format, logging with an existing handler, and the memory budget after restore.

**Package 6 — Discard / repurpose** 🟢

- **#4 macOS Cmd subtraction — false positive.** Without `AA_MacDontSwapCtrlAndMeta` (set nowhere), Qt maps Cmd→`ControlModifier` on macOS; the check in `canvas.py:80` therefore already responds to Cmd+click and the UI text is correct. Additionally accepting `MetaModifier` would wrongly bind the physical Control key to "subtract". **Discard the code change**; at most add a platform test that locks in the Qt mapping.
