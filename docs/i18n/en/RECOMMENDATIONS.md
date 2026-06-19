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

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The documentation languages es/fr/uk/zh are not runtime locales;
  add them key-for-key in `bgremover.i18n` if needed and cover them with tests.
- **O7 ✅ — Subprocess for rembg/ONNX done (PR #283, issue #270 closed).** The
  non-interruptible AI inference now runs in a `spawn`-started process
  (`ai_process.py`); `QThread.terminate()` as the AI emergency exit is gone.
  The robustness/memory follow-up findings are fixed and closed in **#285**
  (PR #289).

## Open GitHub Issues — Priority Assessment (2026-06-19)

As of 2026-06-19, **7** issues are open. Since the 2026-06-18 assessment, the
test/release hardening wave was largely merged: **#307, #308, #309, #310**, and
**#312** are now **closed** (as is the snapshot meta issue **#313**). PR **#317**
(which closed #309/#310) spawned a new follow-up **#318** from its Codex review
(job-level permission overrides in the reusable-workflow guard). Still open are
**#311** (release body), the three performance findings **#277/#278/#279**
(weekly benchmark #280, per the owner's triage **not yet** confirmed as code
regressions), **#245** (CI quota, externally blocked), and the low-priority test
hygiene item **#299**. All open issues were re-verified against the current code.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#311](https://github.com/NikolayDA/picture_helper/issues/311) | Release: fill release body from CHANGELOG | 🟡 Medium | 🟡 Medium | **Ready for PR** — well-scoped: backfill the v2.4.1 body manually; have `release-linux.yml` derive notes from `## [X.Y.Z]` instead of a hardcoded string (also on reuse), with a regression test in `test_release_gate.py` |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟡 Medium | 🟡 Medium | **Needs refinement** — first confirm GitHub's startup-validation semantics (top-level vs. effective-per-job); currently a purely theoretical false positive (no job-level overrides in `ci.yml`), and the OIDC guard #303 must not get weaker |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | Performance regression: JPEG (+38.4%) | 🟡 Medium | 🟡 Medium | Not yet confirmed as a code regression. Extend the benchmark with an environment fingerprint + confirmation runs (median); bundle with #278/#279 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | Performance regression: TIFF (+21.8%) | 🟡 Medium | 🟡 Medium | Like #277: shared benchmark hardening; investigate the encode path (`save_image_file`) only after a compatible confirmation run |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | Performance regression: WebP (+13.7%) | 🟡 Medium | 🟡 Medium | Like #277/#278: one shared PR for fingerprint + median confirmation; report only confirmed regressions |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | **Blocked (external):** restore quota account-side. Repo scope is only clearer failure handling (graceful skip) |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | No correctness bug; highest value first (endpoint move, consolidate `set_brush_size`), the rest as needed |

### Bundleable Issues

- **#277/#278/#279** should be handled together as a benchmark reliability PR; format-specific encode analysis only pays off after that.
- **#318** is the follow-up to the already-merged permission guard (#309/#310) and stays separate — it first needs documented GitHub semantics before `_required_permissions` is touched.
- **#311** stays standalone because it touches the release workflow, CHANGELOG extraction, and existing release notes.
- **#299** is opportunistic test hygiene and should only ride along when an already-touched test is affected.

### Recommended PR Order

1. **#311** — derive release bodies from CHANGELOG and backfill the v2.4.1 notes; well-scoped and user-visible (shipped fixes are otherwise invisible on the release page).
2. **#277/#278/#279** — shared benchmark fingerprint + median confirmation; report a regression only against a compatible baseline.
3. **#318** — refine the permission guard once GitHub's semantics are documented, without weakening the OIDC regression case.
4. **#245** — restore quota externally; repo-side work afterwards is only clearer failure handling.
5. **#299** — test hygiene as needed.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
