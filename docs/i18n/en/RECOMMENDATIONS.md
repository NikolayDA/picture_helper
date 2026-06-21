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

## Open GitHub Issues — Triage Status (2026-06-21)

As of 2026-06-21, GitHub still shows **5** open issues: **#245**, **#299**,
**#318**, **#322**, and **#339**. The previously listed project/layer and
security-test issues **#323**, **#324**, **#326**, and **#329–#335** are
complete in merge commits **#337**, **#338**, and **#340**. **#322** also now
has **#342** and should be commented on and closed after merge verification.

| # | Title | Label/status recommendation | Comment/status proposal |
|---|-------|-----------------------------|-------------------------|
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | `security`; **keep open / blocked external** | Add a comment that repo-side hardening is covered by #323/#324 and #322/#342; the remaining blocker is OpenAI/billing quota. After the quota is restored, trigger the scheduled scan once manually and then close. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | `quality`, `testing`; **open / low priority** | Add a comment that this is not a product or CI blocker; bundle as opportunistic cleanup when related tests are touched. No status change needed. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | `enhancement`, `testing`; **needs refinement** | Add a comment that GitHub semantics for top-level vs. job-level permissions in the called workflow must be documented before any code change; the #303 OIDC guard must not be weakened. |
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: add a maintenance/skip path for the scheduled Codex Security Scan | `security`; **close after #342** | Add a comment that #342 implements the conservative manual maintenance switch (`CODEX_SECURITY_SCAN_ENABLED=false`) with skip output and regression tests; close as done after verified merge. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF is not supported as an input format | **Add labels:** `enhancement`, `documentation` (or `question`, if available); **needs decision** | Add a comment requesting a product decision: either explicitly document that HEIC is unsupported, or plan optional `pillow-heif`/`HEIF` allowlisting plus a load test. Keep open until decided. |

### Recommended Issue Actions

1. Comment on and close **#322** once the merge of #342 to `main` is verified.
2. Label **#339** and make an explicit product decision (documentation
   clarification vs. HEIC feature).
3. Keep **#245** open but mark it externally blocked; link #322/#342 as the
   completed repo-side part.
4. Do not implement **#318** immediately; first document GitHub permission
   semantics.
5. Keep **#299** open as low-priority test cleanup.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
