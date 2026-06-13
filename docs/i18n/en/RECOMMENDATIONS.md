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

There are currently **8** open issues. Reviewing their descriptions against the
code, tests, and documentation confirms five actionable findings. Three issues
(#161/#203/#204) do not establish a repository task without further evidence
and should be closed or supported with a concrete reproduction path.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: clone URL returns 404 for anonymous users | 🟢 Low | 🟢 Low | The HTTPS URL is correct; close as `not planned` while the repo is private, or define the intended publication path |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — CVE collection | 🟢 Low | 🟢 Low | Not present in the project snapshot; close as `not planned` without a reproducible dependency path and do not retain incorrect severity data |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | PyJWT 2.7.0 — CVE collection | 🟢 Low | 🟢 Low | Not present in the project snapshot; close as `not planned` without a reproducible dependency path, and correct severities plus the broken GHSA link |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | INSTALL review: releases, Raspberry Pi, and macOS diagnostics | 🟡 Medium | 🟢 Low | All three findings remain valid; update the root document and five translations together, with an honest release-artifact availability note |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` can abort workers unsafely | 🟡 Medium | 🟠 High | Relevant safety/stability finding; blocking native calls need an architecture decision, while the current test explicitly preserves the unsafe behavior |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` loads the full PyQt6 GUI | 🟡 Medium | 🟡 Medium | Correct, sufficiently documented, and ready for PR; preserve the public API with PEP 562 lazy exports |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Missing migration still bumps `schema_version` | 🟡 Medium | 🟢 Low | Bug confirmed; invert the test and define version-0 semantics explicitly before real migrations are added |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo memory limit excludes the redo stack | 🟢 Low | 🟡 Medium | Narrow scope to a shared undo/redo budget; include the original image and Qt allocations only after measurement |

### Recommended PR Order

1. **#226** — small, fully confirmed documentation fix across all six languages; release availability must be decided or explicitly qualified.
2. **#232** — PEP 562 lazy exports with import regression tests; no further clarification is needed.
3. **#234** — prevent version advancement when a migration is missing and correct the test that currently expects it.
4. **#231** — decide the cancellation model first; a subprocess is the robust option for permanently blocked native calls.
5. **#235** — optionally implement a shared undo/redo memory budget after defining the scope.
6. **#161/#203/#204** — close as `not planned` unless a concrete publication or dependency path is supplied.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
