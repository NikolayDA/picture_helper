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

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The documentation languages es/fr/uk/zh are not runtime locales;
  add them key-for-key in `bgremover.i18n` if needed and cover them with tests.

## Open GitHub Issues — Priority Assessment (2026-06-14)

There are currently **15** open issues. Reviewing their descriptions against the
code, tests, and documentation shows: **nine** findings are well-scoped and
ready for a PR, two (#231/#235) need an architecture or scope decision first,
#245 is an infrastructure/billing problem (not a code defect), and three
(#161/#203/#204) do not establish a repository task without further evidence.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: clone URL returns 404 for anonymous users | 🟢 Low | 🟢 Low | The HTTPS URL is correct; close as `not planned` while the repo is private, or define the intended publication path |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — CVE collection | 🟢 Low | 🟢 Low | Not present in the project snapshot; close as `not planned` without a reproducible dependency path and do not retain incorrect severity data |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | PyJWT 2.7.0 — CVE collection | 🟢 Low | 🟢 Low | Not present in the project snapshot; close as `not planned` without a reproducible dependency path, and correct severities plus the broken GHSA link |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | INSTALL review: releases, Raspberry Pi, and macOS diagnostics | 🟡 Medium | 🟢 Low | Ready for PR: all three findings remain valid; update the root document and five translations together, with an honest release-artifact availability note |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` can abort workers unsafely | 🟡 Medium | 🟠 High | Needs refinement: blocking native calls need an architecture decision (subprocess); the current test preserves the unsafe behavior |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` loads the full PyQt6 GUI | 🟡 Medium | 🟡 Medium | Ready for PR: preserve the public API with PEP 562 lazy exports and add an import regression test |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Missing migration still bumps `schema_version` | 🟡 Medium | 🟢 Low | Ready for PR: prevent the version bump, invert the test, and define version-0 semantics |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo memory limit excludes the redo stack | 🟢 Low | 🟡 Medium | Needs refinement: narrow scope to a shared undo/redo budget; include the original image and Qt allocations only after measurement |
| [#244](https://github.com/NikolayDA/picture_helper/issues/244) | Dead code: `ImageCanvas._zoom` and unused `launch_worker` wrapper | 🟢 Low | 🟢 Low | Ready for PR: remove `_zoom`, decide remove vs. documented API for `launch_worker`; small cleanup PR |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | Infrastructure/billing: restore the OpenAI quota account-side; make the workflow resilient to quota outages and bump `setup-node` to Node 24 |
| [#247](https://github.com/NikolayDA/picture_helper/issues/247) | Active crop survives image transforms and produces wrong pixels | 🟠 High | 🟡 Medium | Ready for PR (top): reset transient state on every image change; regression test (400×200 + 90° rotation) described in the issue |
| [#248](https://github.com/NikolayDA/picture_helper/issues/248) | Escape clears the selection instead of cancelling the polygon lasso | 🟡 Medium | 🟡 Medium | Ready for PR: Escape priority crop → lasso → clear selection; shares the transient-state contract with #247 |
| [#249](https://github.com/NikolayDA/picture_helper/issues/249) | File associations pass image paths but the app does not open them | 🟡 Medium | 🟡 Medium | Ready for PR: open startup paths and macOS `QFileOpenEvent` through the validated load path |
| [#250](https://github.com/NikolayDA/picture_helper/issues/250) | Release workflow publishes artifacts without a full-CI gate | 🟠 High | 🟡 Medium | Ready for PR (before next tag): enforce full CI via `needs`, check tag/`project.version`, remove `\|\| true` |
| [#251](https://github.com/NikolayDA/picture_helper/issues/251) | Empty selection keeps the overlay QPixmap after erasing | 🟡 Medium | 🟢 Low | Ready for PR (quick win): release the overlay pixmap when the mask is empty; exact patch in the issue |

### Recommended PR Order

1. **#247** — High: correctness/data bug (stale crop rectangle yields transparent padding pixels); fully scoped including a regression test.
2. **#250** — High before the next release tag: enforce the full-CI gate via `needs`, reconcile tag/version, remove `|| true`.
3. **#251** — quick memory fix: an empty mask releases the overlay pixmap; the exact patch is in the issue.
4. **#244** — dead-code cleanup (remove `_zoom`, decide on `launch_worker`); small, low-risk cleanup PR.
5. **#234** — prevent version advancement when a migration is missing and correct the test that currently expects it.
6. **#248** — Escape priority crop → lasso → clear selection; shares the transient-state contract with #247 and can be bundled.
7. **#232** — PEP 562 lazy exports with an import regression test.
8. **#249** — open startup paths and macOS `QFileOpenEvent` through the validated load path.
9. **#226** — documentation fix across all six languages; document release availability honestly.
10. **#245** — restore OpenAI billing account-side; make the scan workflow resilient to quota outages and bump `setup-node` to Node 24.
11. **#231** — decide the cancellation model first (subprocess for permanently blocked native calls), then implement.
12. **#235** — implement a shared undo/redo memory budget only after defining the scope.
13. **#161/#203/#204** — close as `not planned` unless a concrete publication or dependency path is supplied.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
