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
- The PR wave **#280–#283** landed the weekly benchmark and implemented three
  findings: **#235** (shared undo/redo budget, PR #281, closed), **#275**
  (localized megapixel message, PR #282), and **#270** (rembg/ONNX subprocess
  via `ai_process.py`, PR #283). #275 and #270 are done in code and only need
  their issues closed.

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The documentation languages es/fr/uk/zh are not runtime locales;
  add them key-for-key in `bgremover.i18n` if needed and cover them with tests.
- **O7 ✅ — Subprocess for rembg/ONNX done (PR #283, issue #270).** The
  non-interruptible AI inference now runs in a `spawn`-started process
  (`ai_process.py`); `QThread.terminate()` as the AI emergency exit is gone.
  Issue #270 only needs to be closed.

## Open GitHub Issues — Priority Assessment (2026-06-15)

After the PR wave **#280–#283**, **7** issues are open. **#235** was closed via
PR #281. **#270** (PR #283) and **#275** (PR #282) are already implemented in
the code and only need their issues closed. New are three performance findings —
**#277/#278/#279** — from the weekly benchmark run (#280); per the owner's
triage they are **not yet** confirmed as code regressions, because the
2026-06-08 baseline carries no environment fingerprint. All open issues were
re-verified against the current code.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#270](https://github.com/NikolayDA/picture_helper/issues/270) | Move rembg/ONNX inference into a subprocess (follow-up from #231) | 🟠 High | 🟡 Medium | **Done in code (PR #283, `ai_process.py`).** Verify and close the issue; roadmap O7 complete |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | Performance regression: JPEG (+38.4%) | 🟡 Medium | 🟡 Medium | Refinement: not yet confirmed as a code regression. Extend the benchmark with an environment fingerprint + confirmation runs (median), then compare only against a compatible baseline. Bundle with #278/#279 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | Performance regression: TIFF (+21.8%) | 🟡 Medium | 🟡 Medium | Like #277: shared benchmark hardening; investigate the encode path (`save_image_file`) only after a compatible confirmation run |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | Performance regression: WebP (+13.7%) | 🟡 Medium | 🟡 Medium | Like #277/#278: one shared PR for fingerprint + median confirmation; report only confirmed regressions |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | Blocked (external): restore quota account-side. Repo scope is only clearer failure handling (graceful skip) + an optional Node 24 bump, not a forced `setup-node` fix |
| [#275](https://github.com/NikolayDA/picture_helper/issues/275) | Megapixel "image too large" message is not localized | 🟢 Low | 🟢 Low | **Done in code (PR #282).** `_too_large_message` now routes through `tr("status.image_too_large[_mp]", …)` (de/en); verify and close the issue |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: clone URL returns 404 for anonymous users | 🟢 Low | 🟢 Low | Decision needed: public vs. private/invite-only, then update the clone guidance or close ("Round 5" is already fixed) |

### Recommended PR Order

1. **#270 + #275** — both are done in code (PR #283 / #282): verify and close the issues.
2. **#277/#278/#279** — one shared PR: extend the benchmark with an environment fingerprint and confirmation runs (median); report a regression only against a compatible baseline. Well-scoped, ready for PR.
3. **#245** — restore quota externally; optional workflow hardening (graceful skip + Node 24) as a small separate PR.
4. **#161** — decide the publication model, then update docs or close.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
