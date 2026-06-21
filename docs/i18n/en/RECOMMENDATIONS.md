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

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The documentation languages es/fr/uk/zh are not runtime locales;
  add them key-for-key in `bgremover.i18n` if needed and cover them with tests.
- **O7 ✅ — Subprocess for rembg/ONNX done (PR #283, issue #270 closed).** The
  non-interruptible AI inference now runs in a `spawn`-started process
  (`ai_process.py`); `QThread.terminate()` as the AI emergency exit is gone.
  The robustness/memory follow-up findings are fixed and closed in **#285**
  (PR #289).

## Open GitHub Issues — Priority Assessment (2026-06-21)

As of 2026-06-21, only **4** roadmap/follow-up issues remain open after
reviewing yesterday's and today's PRs. Merge commits **#337**, **#338**, and
**#340** cleanly complete the items that were still open yesterday: **#326**,
**#329–#335**, **#323**, and **#324**. The GIF load path is regression-tested,
the project/layer epic is implemented end-to-end from the domain model through
UI/integration, and the security-scan tests cover severity filtering, empty
findings, and prompt scope. The remaining open items are **#322**
(maintenance/skip path for the scheduled Codex Security Scan), **#318**
(permission-guard semantics), **#245** (externally blocked quota), and **#299**
(test hygiene).

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: add a maintenance/skip path for the scheduled Codex Security Scan | 🟡 Medium | 🟡 Medium | **Next repo-side step for #245** — choose manual switch, visible auto graceful-skip, or both; gate in the `cadence` job, "disabled → skipped, not failed", keep least privilege and add a static test |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟡 Medium | 🟡 Medium | **Needs refinement** — first document GitHub's startup-validation semantics (top-level vs. effective-per-job); no observed repo failure right now, and OIDC guard #303 must not be weakened |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | **Externally blocked** — restore quota account-side; #323/#324 are complete repo-side, #322 remains open as maintenance/skip hardening |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | No correctness bug; improve opportunistically when related tests are touched (highest value: endpoint move, consolidate `set_brush_size`) |

### Bundleable Issues

- **#322** can be implemented as a standalone CI-hardening PR and complements
  the already completed #323/#324.
- **#318** stays separate because GitHub's semantics must be documented before
  changing code.
- **#299** should only ride along when an affected test is already being edited.

### Recommended PR Order

1. **#322** — final repo-side #245 follow-up with direct operational value.
2. **#318** — refine the permission guard once semantics are documented, without
   weakening the OIDC regression case.
3. **#245** — restore quota account-side (externally blocked).
4. **#299** — test hygiene as needed.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
