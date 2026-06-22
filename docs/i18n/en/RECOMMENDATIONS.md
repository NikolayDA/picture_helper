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

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The documentation languages es/fr/uk/zh are not runtime locales;
  add them key-for-key in `bgremover.i18n` if needed and cover them with tests.
- **O7 ✅ — Subprocess for rembg/ONNX done (PR #283, issue #270 closed).** The
  non-interruptible AI inference now runs in a `spawn`-started process
  (`ai_process.py`); `QThread.terminate()` as the AI emergency exit is gone.
  The robustness/memory follow-up findings are fixed and closed in **#285**
  (PR #289).

## Open GitHub Issues — Triage Status (2026-06-22)

As of 2026-06-22, GitHub shows **13** open issues. Alongside the **EufyMake
export epic #351** and sub-issues **#352–#355** (roadmap rank #3), the docs gap
**#357** and three post-merge height-map findings are open: **#363** (wrong
image export with an active HEIGHT layer), **#364** (conflicting kind/role
context), and **#365** (unbounded median-filter memory). The maintenance/skip
path **#322** was delivered via **#342** and is closed.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort.

| # | Title | Relevance | Complexity | Recommended next step |
|---|-------|-----------|------------|-----------------------|
| [#363](https://github.com/NikolayDA/picture_helper/issues/363) | Regression: Save Image exports the active HEIGHT view instead of the COLOR composite | 🔴 Critical | 🟢 Low | **Ready for PR — fix first.** Separate display and export rendering; normal image export must write the COLOR composite regardless of the active layer. Reproduced silent wrong export. |
| [#364](https://github.com/NikolayDA/picture_helper/issues/364) | Height-map context: UI and canvas disagree on the `HEIGHT_MAP` role | 🟠 High | 🟡 Medium | **Needs decision, then PR.** Choose whether `LayerKind.HEIGHT` is authoritative or the role is sufficient, then align model, deserialization, layer/height panels, and canvas. Resolve before #352 because EufyMake uses the same role mapping. |
| [#365](https://github.com/NikolayDA/picture_helper/issues/365) | Height-map median filter can exhaust memory on large projects | 🟠 High | 🟡 Medium | **Ready for PR.** Compute median in bounded blocks instead of a full `(2r+1)² × H × W` stack; validate the 40-MP/radius contract for median and Gaussian with a memory benchmark. |
| [#351](https://github.com/NikolayDA/picture_helper/issues/351) | [Epic] Consistent EufyMake export package | 🟠 High | 🔴 High (epic) | **Needs refinement** – per the deep research (issue comment), sharpen scope to "robust import assets for EufyMake Studio"; native `.empf` generation is **not** the default goal. Driven via #352–#355. |
| [#352](https://github.com/NikolayDA/picture_helper/issues/352) | Export data model & package definition (Qt-free) + ADR | 🟠 High | 🟡 Medium | **Ready for PR — ADR first** – deep research done (issue comments), but the convention/ADR decision is **not yet recorded in-repo** and must be written down as the first step of this PR (it is an acceptance criterion of #352). Qt-free `eufymake_export.py` with `ExportPlan`/`ExportAsset` (color motif PNG+alpha, height grayscale bright=high, gloss mask); scope = import assets for EufyMake Studio; mark 16-bit/gloss semantics/native `.empf` as "open". Foundation — unblocks #353–#355. |
| [#353](https://github.com/NikolayDA/picture_helper/issues/353) | Asset rendering & atomic package write | 🟠 High | 🟡 Medium | **Blocked** – needs #352; cleanly scoped afterwards (rendering + atomic write). |
| [#354](https://github.com/NikolayDA/picture_helper/issues/354) | Pre-export consistency check | 🟠 High | 🟡 Medium | **Blocked** – needs #352. Keep the check building blocks reusable (synergy with the general pre-export error check). |
| [#355](https://github.com/NikolayDA/picture_helper/issues/355) | UI: EufyMake export dialog + menu + i18n + settings | 🟠 High | 🟡 Medium | **Blocked** – needs #352–#354. UI wording per deep research: "prepare assets for EufyMake Studio", not "produce a finished project". |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | **Blocked (external)** – repo-side hardening via #322/#342 (closed) is done; the remaining blocker is OpenAI/billing quota. After the quota is restored, trigger the scheduled scan once manually, then close. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟢 Low | 🟡 Medium | **Needs refinement** – first document the GitHub semantics (top-level vs. effective-per-job); the #303 OIDC guard must not be weakened. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF is not supported as an input format | 🟢 Low | 🟢 Low | **Ready for PR (docs)** – the maintainer **deliberately excluded** HEIC (comment 2026-06-21). Only clarify README/ANLEITUNG, then close. |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Docs: startup-path/Finder opening is missing from ANLEITUNG §4 | 🟢 Low | 🟢 Low | **Ready for PR (docs).** Update the canonical guide and all five i18n copies; clarify that Recent Files includes images and `.bgrproj` projects. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | **Ready for PR (opportunistic)** – not a product or CI blocker; highest value first (assert the lasso endpoint, the `test_helpers` line, consolidate the `set_brush_size` tests). |

### Recommended Next (PR order)

1. Fix **#363** first to restore the COLOR export contract.
2. Decide and implement **#364** before EufyMake role mapping.
3. Harden **#365** in parallel before large height maps use median preview.
4. Then implement **#352**, ADR first; it unblocks #353/#354.
5. Implement **#353** and **#354** in parallel, followed by **#355**.
6. Use **#357**, **#339**, and **#299** as lower-priority fillers.
7. Defer **#318** until GitHub permission semantics are documented.
8. Keep **#245** externally blocked (no repo patch restores the quota).

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
