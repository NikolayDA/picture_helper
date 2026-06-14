[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-06-04)

The active code-analysis list is empty. Ruff, mypy, and the local test suite
remain the baseline before new PRs.

### Completed Since The Last Review

- **N1/N2/N4/N5/N6/N7/N8** are done: error paths, size limit, file
  extensions, atomic save, CI Qt packages, lazy import, and docstring.
- **O2/O3/O4/O5/O6** are implemented: Linux packages, release workflow,
  full matrix, `ui_smoke`, and platform-correct tool shortcuts.
- Findings **#163–#206** were closed in the documented PRs and protected by
  regression tests or CI checks.
- PRs **#263–#269** closed **#257, #258, #234 + #259, #248 + #260, #231** and
  **#249**; **#261** was resolved via PR #268 and closed.

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The documentation languages es/fr/uk/zh are not runtime locales;
  add them key-for-key in `bgremover.i18n` if needed and cover them with tests.
- **O7 🟠 — Subprocess for rembg/ONNX (follow-up from #231, tracked in #270).**
  PR #267 bounded the shutdown fallback, but the non-interruptible AI work still
  runs in the thread with `terminate()` as the emergency exit. The full fix
  moves rembg/ONNX into a subprocess.

## Open GitHub Issues — Priority Assessment (2026-06-14, closing triage)

After PRs **#263–#269** merged and **#261** was closed (resolved by PR #268),
**5** issues remain open. Nine previously open issues — **#231, #234, #248,
#249, #257, #258, #259, #260** and **#261** — were closed via the merged PRs.
The deferred architecture follow-up from #231 (rembg/ONNX subprocess, roadmap
**O7**) was filed as **#270**. All open issues were re-verified against the
current code.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#270](https://github.com/NikolayDA/picture_helper/issues/270) | Move rembg/ONNX inference into a subprocess (follow-up from #231) | 🟠 High | 🟡 Medium | Dedicated architecture PR: PR #267 only bounded the shutdown. Move rembg/ONNX into a subprocess so `terminate()` is no longer the AI emergency exit; tests for close/cancel/blocked call |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` loads the full PyQt6 GUI | 🟡 Medium | 🟡 Medium | Ready for PR: preserve the public API with PEP 562 lazy exports, add an import regression test. Code unchanged: `__init__.py:15-43` still re-exports the GUI |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | Fix quota account-side; repo scope is clearer failure handling plus an optional Node 24 bump, not a forced `setup-node` fix |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo memory limit excludes the redo stack | 🟢 Low | 🟡 Medium | Shared undo/redo budget; only measure original/Qt memory. Code unchanged: `canvas_history.py` counts only `_undo_bytes`, redo bounded by `maxlen` only |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: clone URL returns 404 for anonymous users | 🟢 Low | 🟢 Low | “Round 5” is fixed; decide public vs. private/invite-only first, then update clone guidance or close |

### Recommended PR Order

1. **#232** — make package imports lightweight with PEP 562 lazy exports.
2. **#245** — restore quota externally; keep optional workflow hardening (Node 24) separate.
3. **#235** — implement a shared undo/redo history budget.
4. **#161** — decide the publication model, then update docs or close.
5. **#270** — plan the rembg/ONNX subprocess as a dedicated architecture PR (follow-up from #231).

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
