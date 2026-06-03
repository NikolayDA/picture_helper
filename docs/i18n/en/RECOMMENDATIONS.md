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

## Current status (2026-06-02, "adoring-johnson" review)

Targeted follow-up review after "modest-shannon", focused on the save, load, and CI paths. **8 items (N1–N8):** 7 fixed with regression tests – merged via **PR #142** (N1), **#143** (N6, N8), **#144** (N4, N5), and **#148** (N2, N7); 1 already covered (N3). Baseline still green: ruff/mypy clean, suite green.

### Completion status

| Status | Items |
|--------|-------|
| ✅ Done | N1, N2, N4, N5, N6, N7, N8 |
| ⏳ Open | – |

### Findings

- **N1 🟠 — Release the magic-wand gate on the error path** (PR #142). Follow-up to "modest-shannon" B: on an image change, `_load_image_async` cancels the flood fill, which then emits neither `finished` nor `error`. The gate reset ran only on the success path (`apply_loaded_image`) – if the load failed, `_wand_busy` stayed set and the wand was blocked on the old image. New silent `reset_pending_wand()` right next to `cancel_flood_fill()`.
- **N2 🟡 — Rotation size limit** (PR #148). `rotate_image` (`image_ops.py`) rotates with `expand=True`; the megapixel guard only applied on load (`Image.MAX_IMAGE_PIXELS`), not to the result – a just-under-limit source could balloon to ~2× at ~45°. Now `rotated_size()` estimates the expand bounding box up front; `apply_rotate` rejects results over the limit with a status message.
- **N3 ➖ — History memory budget** (already covered). `CanvasHistory` (`canvas_history.py`) has long enforced the undo budget via `_trim()`/`_UNDO_MEMORY_LIMIT`, with redo capped by `_REDO_MAX_ENTRIES`. No action needed.
- **N4 🟢 — Extension honesty when saving** (PR #144). `save_image_file` silently wrote PNG bytes for unknown extensions; now a clear `ValueError` rejection, while an empty extension stays the PNG default.
- **N5 🟡 — Atomic save** (PR #144). Writing straight to the target destroyed the existing file on an abort. Now `mkstemp` → `os.replace` in the target directory (the `qt_plugins._copy_if_needed` pattern), preserving permissions and cleaning up the temp file.
- **N6 🟡 — `libgl1` in the full CI matrix + drift test** (PR #143). The full matrix did not install `libgl1` (unlike the other Qt package sources) → `import PyQt6` risked `libGL.so.1`. Added; the new `test_ci_qt_packages.py` keeps all four package lists consistent.
- **N7 🟢 — Eager imports** (PR #148). `workers.py` imported `rembg` (which drags in onnxruntime) at module level; since `main_window` loads `workers`, the import cost was paid at startup – even without using the AI. Now a `find_spec` probe for `REMBG_AVAILABLE` plus a lazy import of `rembg` only in the worker thread (warmup/first AI click).
- **N8 🟢 — Stale `load_image` docstring** (PR #143). It named the drop path as a synchronous caller, although drag & drop has long run asynchronously. Corrected.

---

## Open recommendations

Improvements from the second analysis that are not yet implemented (product/process):

- **O1 🟠 — App localization.** Runtime i18n implemented: `bgremover.i18n` with a central string table and a stable German fallback; **German and English** are switchable at runtime (language selector in the settings dialog with a restart hint). The entire visible surface — including canvas status messages, history entries and dialogs — goes through `tr()`, guarded by an AST check against new untranslated literals. Open: the other existing documentation languages (es/fr/uk/zh) as runtime locales (**PR 4c**).
- **O2 🟢 — Linux app / packaging.** ✅ Done (PR 5 + PR 6): portable **AppImage** plus a **.deb** second format (desktop entry, icon, AppStream metadata); a **release workflow** builds both for **x86_64 and aarch64/Raspberry Pi OS** on native runners and attaches them to the release. Smoke tests keep the metadata and workflow consistent — lowering the entry barrier analogous to the macOS `.app` bundle.
**✅ Done:** O4/O6 — single-key tool switching (`W`/`B`/`E`/`L`) & platform-correct `Cmd`/`Ctrl` hints (PR #146, `test_tool_shortcuts.py`); O3 — full matrix additionally weekly via cron (PR #149); O5 — `ui_smoke` subset runs in PR/Full CI, the full qtbot suite stays nightly (PR #149).

## Implementation plan by PR package (from 2026-06-02)

- **PR 0 — Code hardening (N2 + N7).** ✅ Done (PR #148). N2 — apply the megapixel gate to the rotation result too (`rotated_size()` estimates the target size up front, `apply_rotate` rejects over-limit results with a status message); N7 — import `rembg` lazily and probe `REMBG_AVAILABLE` via `find_spec` (the existing warmup-failure handling covers a broken backend).
- **PR 1 — Tool shortcuts & shortcut hints.** ✅ Done (PR #146). O4 + O6: single-key switching (`W`/`B`/`E`/`L`), synchronized toolbar checked state, updated tooltips/README/manual, regression test for shortcut wiring.
- **PR 2 — Earlier CI coverage.** ✅ Done (PR #149). O3 — full matrix additionally weekly (cron); O5 — `ui_smoke` subset in PR/Full CI, Nightly UI remains the full suite.
- **PR 3 — i18n foundation.** ✅ Done. O1 prepared: `bgremover.i18n` with runtime locale/fallback, German as the stable default, first central string table for status messages, menu, toolbar, tabs, history, and crop bar; regression tests for locale normalization, fallback, and UI wiring.
- **PR 4 — i18n rollout.** ✅ Done. Made O1 usable: **4a** — extended `tr()` coverage to the right panel, settings dialog and all dialogs (German byte-identical, verified via golden diff); **4b** — complete English table + language selector (persistence, restart hint); **4b.1** — canvas status messages, history descriptions and `main_window` dialogs (open/save/color/unsaved) via `tr()`, plus an AST guard against new untranslated literals at user-facing sinks. Key/placeholder parity and per-locale UI smoke tested.
- **PR 4c — i18n further languages (optional, deferred).** If needed, add es/fr/uk/zh as runtime locales (mirror the tables key-for-key — parity/smoke/guard then apply automatically). Not currently planned.
- **PR 5 — Linux packaging foundation.** ✅ Done. AppImage as the target artifact: `packaging/linux` with a Freedesktop `.desktop`, AppStream metainfo and a `python-appimage` build script; app id `de.bgremover.app` (matching the macOS bundle), `app.py` sets `setDesktopFileName`; a self-contained smoke test (desktop/AppStream/pyproject consistency).
- **PR 6 — Linux packaging expansion.** ✅ Done. A `.deb` second format (wraps the AppImage → apt install + menu integration), the aarch64/Raspberry Pi OS variant, and a GitHub Actions release workflow (AppImage + `.deb` for x86_64 and aarch64, attached to the release); the smoke test actually builds a `.deb` and checks the workflow.

---

## Previous rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done (PR #135/#136); among them decompression-bomb handling and the magic-wand lifecycle that N1 now completes on the error path.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, #1–#15 done, #4 discarded (false positive).

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
