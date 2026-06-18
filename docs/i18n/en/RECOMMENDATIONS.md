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

## Open GitHub Issues — Priority Assessment (2026-06-18)

As of 2026-06-18, **11** issues are open. This update also closes the snapshot
meta issue **#313**, which previously counted itself as the 12th open issue.
Since the 2026-06-15 assessment, **#161** (README clone URL) was **closed** on
2026-06-17; the v2.4.x release cycle brought a wave of test/release hardening
issues (**#299, #307–#312**). Still open are the three performance findings
**#277/#278/#279** (weekly benchmark #280, per the owner's triage **not yet**
confirmed as code regressions) and **#245** (CI quota, externally blocked). All
open issues were re-verified against the current code.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#312](https://github.com/NikolayDA/picture_helper/issues/312) | CI: bump node20 actions to Node 24 | 🟠 High | 🟢 Low | GitHub already forces Node 24 with a warning; bump the affected actions (`github-script`, `upload/download-artifact`) to node24 majors uniformly, optional guard test |
| [#311](https://github.com/NikolayDA/picture_helper/issues/311) | Release: fill release body from CHANGELOG | 🟡 Medium | 🟡 Medium | Backfill the v2.4.1 body manually; have `release-linux.yml` derive notes from `## [X.Y.Z]` instead of a hardcoded string — also on reuse |
| [#310](https://github.com/NikolayDA/picture_helper/issues/310) | Test: LICENSES.md version == pyproject | 🟡 Medium | 🟢 Low | Fast pytest comparing the title version against `[project].version` — catches bump drift before the heavy License Check |
| [#309](https://github.com/NikolayDA/picture_helper/issues/309) | Test: caller covers reusable-WF permissions | 🟡 Medium | 🟢 Low | Generalize `test_release_gate.py`: the caller job must grant every permission the called workflow declares (OIDC `id-token: write`) |
| [#308](https://github.com/NikolayDA/picture_helper/issues/308) | Test: AI chain importable in `--ai` artifact | 🟠 High | 🟡 Medium | Network-free spawn self-test in the `--ai` build that loads `rembg`+`pymatting` metadata (regression #306) |
| [#307](https://github.com/NikolayDA/picture_helper/issues/307) | Test: launch built artifact headless | 🟠 High | 🟡 Medium | Launch the bundle headless in the build job (catch start crash #304 / fork bomb #305); `publish` stays gated via `needs: build` |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | No correctness bug; highest value first (endpoint move, consolidate `set_brush_size`), the rest as needed |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | Performance regression: JPEG (+38.4%) | 🟡 Medium | 🟡 Medium | Not yet confirmed as a code regression. Extend the benchmark with an environment fingerprint + confirmation runs (median); bundle with #278/#279 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | Performance regression: TIFF (+21.8%) | 🟡 Medium | 🟡 Medium | Like #277: shared benchmark hardening; investigate the encode path (`save_image_file`) only after a compatible confirmation run |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | Performance regression: WebP (+13.7%) | 🟡 Medium | 🟡 Medium | Like #277/#278: one shared PR for fingerprint + median confirmation; report only confirmed regressions |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | Blocked (external): restore quota account-side. Repo scope is only clearer failure handling (graceful skip) + an optional Node 24 bump |

### Bundleable Issues

- **#307/#308** belong together: one release-artifact verification PR can launch GUI and `--ai` bundles headlessly and add the AI spawn self-check.
- **#309/#310** are small guard tests and can share one test-hardening PR; **#311** is better kept separate because it touches the release workflow, CHANGELOG extraction, and existing release notes.
- **#277/#278/#279** should be handled together as a benchmark reliability PR; format-specific encode analysis only pays off after that.
- **#312** is its own CI modernization PR across all workflows; the Node 24 part of **#245** can ride there, while OpenAI quota remains external.
- **#299** is opportunistic test hygiene and should only ride along when an already-touched test is affected.

### Recommended PR Order

1. **#307/#308** — headless smoke-test the release bundles (GUI + `--ai`); prevents shipping start crashes/fork bombs again.
2. **#312** — bump node20 actions to Node 24 before GitHub removes the fallback.
3. **#309/#310** — generic workflow permissions and LICENSES version as a quick test-hardening PR.
4. **#311** — derive release bodies from CHANGELOG and backfill the v2.4.1 notes.
5. **#277/#278/#279** — shared benchmark fingerprint + median confirmation; report a regression only against a compatible baseline.
6. **#245** — restore quota externally; repo-side work afterwards is only clearer failure handling.
7. **#299** — test hygiene as needed.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
