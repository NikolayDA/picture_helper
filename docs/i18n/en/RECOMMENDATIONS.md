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
- PR **#274** closed **#232**: `import bgremover` no longer loads the Qt stack
  thanks to PEP 562 lazy exports; a subprocess regression test covers it.
- The PR wave **#280–#284** landed the weekly benchmark, implemented three
  findings — **#235** (shared undo/redo budget, PR #281), **#275** (localized
  megapixel message, PR #282), and **#270** (rembg/ONNX subprocess via
  `ai_process.py`, PR #283) — and refreshed the roadmap (PR #284). **#235, #270,
  and #275 are now closed.**
- The two post-merge Codex follow-up findings from #283 and #264 are likewise
  fixed **and closed**: **#285** (robustness/memory of the rembg subprocess,
  PR #289) and **#286** (memory peaks in the capped file read, PR #290).

- **N9 ✅ — Project/layer data model (epic #329) delivered.** Qt-free domain
  model (#330), layer-aware history (#331), composite canvas (#332), `.bgrproj`
  format (#333), layer panel/project menu (#334) and migration/integration
  (#335) — single-image parity preserved, `make check`/`make ui` green.
- **N10 ✅ — Height-map workspace (epic #344) delivered.** Qt-free height
  representation and 2D visualization (#345), algorithmic generation and
  grayscale import (#346), height editing (#347), `height_ops` optimization
  with live preview (#348), and the mode-aware Height tab (#349).
- **N11 ✅ — Phase-0 polish (epic #358) delivered.** Target-size project resize
  (#359), alpha-preserving brightness/contrast/saturation with live preview
  (#360), and selection-bounded alpha-edge feathering (#361), all undoable and
  persisted losslessly in `.bgrproj` (PR #362).
- **#363 ✅ — Export regression fixed (PR #367).** Save Image once again writes
  the COLOR composite regardless of the active layer; display and export
  rendering are separated, covered by a pixel regression test.

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The documentation languages es/fr/uk/zh are not runtime locales;
  add them key-for-key in `bgremover.i18n` if needed and cover them with tests.
- **O7 ✅ — Subprocess for rembg/ONNX done (PR #283, issue #270 closed).** The
  non-interruptible AI inference now runs in a `spawn`-started process
  (`ai_process.py`); `QThread.terminate()` as the AI emergency exit is gone.
  The robustness/memory follow-up findings are fixed and closed in **#285**
  (PR #289).

## Open GitHub Issues — Triage Status (2026-06-23, updated)

As of 2026-06-23, GitHub shows **11** open issues. The EufyMake epic **#351**
is closed after today's merged PRs **#372–#374**: **#352** (ADR/data model),
**#353** (rendering/atomic writer), **#354** (consistency check) and **#355**
(dialog/menu/settings) are fully represented in the repo and covered by focused
tests. The follow-up review fix in **#374** also fixes `optional_roles` generator
exhaustion and prevents an export folder from replacing an existing file target.
Today's new roadmap-rank-#4 epic **#375** and sub-issues **#376–#380** now cover
physical mm/DPI output and a general export check. The docs gaps **#357** and
**#339** plus the test/CI findings **#318**, **#299** and **#245** also remain;
the EufyMake review itself did not require new follow-up issues.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort.

| # | Title | Relevance | Complexity | Recommended next step |
|---|-------|-----------|------------|-----------------------|
| [#375](https://github.com/NikolayDA/picture_helper/issues/375) | [Epic] Physical-size output (mm/DPI) + general export validation | 🟠 High | 🔴 High (epic) | **Ready for PR — foundation first:** #376 (Qt-free geometry + project metadata), then #377/#378/#379 in parallel; #380 completes the UI integration and epic. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | **Blocked (external)** – repo-side hardening via #322/#342 (closed) is done; the remaining blocker is OpenAI/billing quota. After the quota is restored, trigger the scheduled scan once manually, then close. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟢 Low | 🟡 Medium | **Needs refinement** – first document the GitHub semantics (top-level vs. effective-per-job); the #303 OIDC guard must not be weakened. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF is not supported as an input format | 🟢 Low | 🟢 Low | **Ready for PR (docs)** – the maintainer deliberately excluded HEIC (comment 2026-06-21). Only clarify README/ANLEITUNG, then close. |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Docs: startup-path/Finder opening is missing from ANLEITUNG §4 | 🟢 Low | 🟢 Low | **Ready for PR (docs).** Update the canonical guide and all five i18n copies; clarify that Recent Files includes images and `.bgrproj` projects. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | **Ready for PR (opportunistic)** – not a product or CI blocker; highest value first (assert the lasso endpoint, the `test_helpers` line, consolidate the `set_brush_size` tests). |

### Review of PRs/issues closed on 2026-06-23

Reviewed today's closed PRs **#372**, **#373** and **#374**, plus issues **#351**
and **#355** (also the sub-issues **#352–#354** closed by #372, based on the
merge content). The EufyMake work is cleanly complete: ADR, Qt-free plan/check/
writer modules, UI integration, settings persistence and the follow-up #373
review fix are present. The local review of the affected modules and tests found
no open follow-up; comments or new issues are therefore not required.

### Recommended Next (PR order)

1. Implement **#376** as the roadmap-rank-#4 foundation; then **#377**, **#378**
   and **#379** can proceed in parallel, followed by **#380**.
2. Fit **#357** and **#339** in as small, independent docs PRs.
3. Clean up **#299** opportunistically; defer **#318** until the semantics are
   evidenced and keep **#245** externally blocked.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
