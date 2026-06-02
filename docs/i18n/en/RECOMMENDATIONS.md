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

- **O1 🟠 — App localization.** The UI is hardcoded German; there is no runtime i18n (no `QTranslator`/`tr()`), although the docs exist in five languages. Status messages are already centralized (`status_messages.py`). Incrementally via Qt Linguist (`.ts`) or a lightweight `QLocale` string table.
- **O2 🟡 — Linux app / packaging.** No app bundle for Linux; launch only via `python -m bgremover` from a venv. An installable package (AppImage/Flatpak/`.deb`) for **Raspberry Pi OS** and major distributions (Debian/Ubuntu/Fedora) lowers the entry barrier for non-developers — analogous to the macOS `.app` bundle.
**✅ Done:** O4/O6 — single-key tool switching (`W`/`B`/`E`/`L`) & platform-correct `Cmd`/`Ctrl` hints (PR #146, `test_tool_shortcuts.py`); O3 — full matrix additionally weekly via cron (PR #149); O5 — `ui_smoke` subset runs in PR/Full CI, the full qtbot suite stays nightly (PR #149).

## Implementation plan by PR package (from 2026-06-02)

- **PR 0 — Code hardening (N2 + N7).** ✅ Done (PR #148). N2 — apply the megapixel gate to the rotation result too (`rotated_size()` estimates the target size up front, `apply_rotate` rejects over-limit results with a status message); N7 — import `rembg` lazily and probe `REMBG_AVAILABLE` via `find_spec` (the existing warmup-failure handling covers a broken backend).
- **PR 1 — Tool shortcuts & shortcut hints.** ✅ Done (PR #146). O4 + O6: single-key switching (`W`/`B`/`E`/`L`), synchronized toolbar checked state, updated tooltips/README/manual, regression test for shortcut wiring.
- **PR 2 — Earlier CI coverage.** ✅ Done (PR #149). O3 — full matrix additionally weekly (cron); O5 — `ui_smoke` subset in PR/Full CI, Nightly UI remains the full suite.
- **PR 3 — i18n foundation.** Prepare O1: add runtime locale/fallback, centralize visible strings incrementally, keep German as the stable default.
- **PR 4 — i18n rollout.** Make O1 usable: at least English as a runtime language, then the other existing documentation languages, with smoke checks per locale.
- **PR 5 — Linux packaging foundation.** Start O2: choose target artifact (AppImage/`.deb`/Flatpak), add desktop file/icon/AppStream metadata and a Linux build smoke.
- **PR 6 — Linux packaging expansion.** Complete O2: Raspberry Pi OS variant, optional second package format, and release workflow for Linux artifacts.

---

## Previous rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done (PR #135/#136); among them decompression-bomb handling and the magic-wand lifecycle that N1 now completes on the error path.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, #1–#15 done, #4 discarded (false positive).

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
