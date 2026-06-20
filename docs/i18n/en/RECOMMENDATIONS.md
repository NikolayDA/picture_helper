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

## Open GitHub Issues — Priority Assessment (2026-06-20)

As of 2026-06-20, **14** issues are open. Since the 2026-06-19 assessment,
**#311** (release body) was closed. New arrivals are the epic **#329**
(project/layer data model — foundation for height map, gloss & EufyMake export)
with its six sub-issues **#330–#335**, plus the test-coverage finding **#326**
(GIF declared as an input format but untested). The layers epic is the
prioritized roadmap rank #1: **#330** (Qt-free domain model) is the
dependency-free keystone and doable right away, while the remaining sub-issues
are blocked along the dependency chain
(#330 → #331 → #332/#333 → #334 → #335). Still open from the previous round:
**#318** (permission guard), **#245** (CI quota, externally blocked), the three
**#245** hardening follow-ups **#322–#324**, and the low-priority test hygiene
item **#299**. All open issues were re-verified against the current code.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#329](https://github.com/NikolayDA/picture_helper/issues/329) | [Epic] Project/layer data model (foundation for height map/gloss/EufyMake) | 🟠 High | 🟠 High | **Epic / tracking** — roadmap rank #1; work through the six sub-issues, not its own PR |
| [#330](https://github.com/NikolayDA/picture_helper/issues/330) | Domain model `Project` + `Layer` (Qt-free) | 🟠 High | 🟡 Medium | **Ready for PR** — dependency-free keystone; Qt-free, strictly typed, compositing/roles, `tests/test_project_model.py`. Starting point of the epic |
| [#331](https://github.com/NikolayDA/picture_helper/issues/331) | Project-wide undo/redo (layer-aware history) | 🟠 High | 🟠 High | **Blocked by #330** — layer-aware history, testable in isolation before canvas wiring |
| [#332](https://github.com/NikolayDA/picture_helper/issues/332) | Canvas: composite rendering + active layer | 🟠 High | 🟠 High | **Blocked by #330/#331** — largest chunk; behavior switch to layer-based, single-layer parity |
| [#333](https://github.com/NikolayDA/picture_helper/issues/333) | Project file format: save/load (versioned, atomic, validated) | 🟠 High | 🟠 High | **Blocked by #330** (parallel to #332) — `.bgrproj` ZIP container, atomic/validated/versioned |
| [#334](https://github.com/NikolayDA/picture_helper/issues/334) | UI: layers panel + project menu + i18n | 🟠 High | 🟠 High | **Blocked by #330/#332/#333** — panel + menu actions, i18n de/en parity |
| [#335](https://github.com/NikolayDA/picture_helper/issues/335) | Migration & integration (image→project, recent, settings, export) | 🟠 High | 🟡 Medium | **Blocked by #330/#332/#333/#334** — closing issue of the epic; no regressions in existing flows |
| [#326](https://github.com/NikolayDA/picture_helper/issues/326) | Tests: GIF input format is declared but untested | 🟡 Medium | 🟢 Low | **Ready for PR, doable now** — a load test via `ImageLoadWorker` covers the `_ALLOWED_IMAGE_FORMATS` gate for GIF; no save/export |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟡 Medium | 🟡 Medium | **Needs refinement** — first confirm GitHub's startup-validation semantics (top-level vs. effective-per-job); currently a purely theoretical false positive (no job-level overrides in `ci.yml`), and the OIDC guard #303 must not get weaker |
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: add a maintenance/skip path for the scheduled Codex Security Scan | 🟡 Medium | 🟡 Medium | **#245 follow-up** — scope decision manual switch vs. visible auto-graceful-skip (vs. both); gate in the `cadence` job, "disabled → skipped, not failed", keep least privilege (no `issues: write` in the scan job), static test |
| [#323](https://github.com/NikolayDA/picture_helper/issues/323) | Tests: cover the security-issue sync for severity filter and empty findings | 🟢 Low | 🟢 Low | **#245 follow-up, doable now** — regression tests for `reportable: false`, the severity threshold, and "No reportable findings"; network-free via `--dry-run`/direct calls |
| [#324](https://github.com/NikolayDA/picture_helper/issues/324) | Security: doc-governance test for the Codex scan prompt vs. repo scope | 🟢 Low | 🟢 Low | **#245 follow-up, doable now** — static test that the prompt still names the current top-level security surfaces; complements the existing prompt assertions |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | No correctness bug; highest value first (endpoint move, consolidate `set_brush_size`), the rest as needed |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | **Blocked (external):** restore quota account-side. Repo-side hardening is tracked in **#322–#324**; the graceful skip is #322 variant B |

### Bundleable Issues

- The layers epic **#329** is worked through via its sub-issues in the prescribed order; **#332** and **#333** can be parallelized after #330.
- **#323/#324** (both #245 follow-ups, network-free static security-scan tests) can be bundled into one PR.
- **#318** stays separate — it first needs documented GitHub semantics before `_required_permissions` is touched.
- **#299** is opportunistic test hygiene and should only ride along when an already-touched test is affected.

### Recommended PR Order

1. **#330** — the dependency-free keystone of the layers epic; unblocks #331/#332/#333.
2. **#326** — quick, well-scoped win (GIF load test) that closes a coverage gap.
3. **#323 / #324** — network-free security-scan hardening, doable anytime.
4. **#331 → #332 / #333 → #334 → #335** — the layers epic along its dependency chain.
5. **#322** — maintenance/skip path after a deliberate auto/manual decision (#245 follow-up).
6. **#318** — refine the permission guard once GitHub's semantics are documented, without weakening the OIDC regression case.
7. **#245** — restore quota account-side (externally blocked).
8. **#299** — test hygiene as needed.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
