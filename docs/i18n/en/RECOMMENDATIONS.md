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

After triage, **13** issues remain open. **#203/#204** were closed as
`not planned` because they are not project dependencies; **#226/#244** were
already completed by PR #246 and #256. Eleven issues have an actionable
repository scope. #161 needs a publication decision, while #245 primarily
requires an account-side billing/quota fix.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: clone URL returns 404 for anonymous users | 🟢 Low | 🟢 Low | “Round 5” is fixed; decide public vs. private/invite-only before changing clone guidance |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` can abort workers unsafely | 🟠 High | 🟡 Medium | First PR: bound the second wait, log and test failure handling; treat subprocess architecture separately |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` loads the full PyQt6 GUI | 🟡 Medium | 🟡 Medium | Ready for PR: preserve the public API with PEP 562 lazy exports and add an import regression test |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Missing migration still bumps `schema_version` | 🟡 Medium | 🟢 Low | Bundle with #259: missing migration steps must neither mark nor alter settings |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo memory limit excludes the redo stack | 🟢 Low | 🟡 Medium | Use a shared undo/redo budget; only measure/document the original image and Qt memory |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | Fix quota account-side; repo scope is clearer failure handling, not a `setup-node` change |
| [#248](https://github.com/NikolayDA/picture_helper/issues/248) | Escape clears the selection instead of cancelling the polygon lasso | 🟡 Medium | 🟡 Medium | Bundle with #260: central cancellation priority crop → lasso → clear selection |
| [#249](https://github.com/NikolayDA/picture_helper/issues/249) | File associations pass image paths but the app does not open them | 🟡 Medium | 🟡 Medium | Ready for PR: open startup paths and macOS `QFileOpenEvent` through the validated load path |
| [#257](https://github.com/NikolayDA/picture_helper/issues/257) | Release follow-ups: publish context, tag gate, and rerun artifacts | 🟠 High | 🟡 Medium | Standalone top PR before the next release tag; change workflow, docs, and governance tests together |
| [#258](https://github.com/NikolayDA/picture_helper/issues/258) | Image-load limit may preallocate 512 MiB | 🟠 High | 🟡 Medium | Standalone PR: chunked read, localized size error, and precise boundary display |
| [#259](https://github.com/NikolayDA/picture_helper/issues/259) | Recent-files menu mutates a future settings schema | 🟠 High | 🟡 Medium | Bundle with #234: keep future schemas read-only throughout startup |
| [#260](https://github.com/NikolayDA/picture_helper/issues/260) | Automatic crop discard leaves the wrong tool cursor | 🟡 Medium | 🟢 Low | Bundle with #248; test central interaction cancellation and cursor restoration |
| [#261](https://github.com/NikolayDA/picture_helper/issues/261) | Brush overlay scans the full mask on every move | 🟡 Medium | 🟡 Medium | Standalone performance PR with a selected-pixel counter and spy test |

### Recommended PR Order

1. **#257** — make the release workflow reliable before the next tag.
2. **#258** — remove preallocation and fix mixed/misleading size errors.
3. **#234 + #259** — QSettings migration and future-schema protection in one PR.
4. **#248 + #260** — central Escape/crop cancellation with the correct cursor.
5. **#231** — deliver a bounded shutdown fallback; handle subprocess work later.
6. **#261** — remove the O(image-size) scan from the common brush path.
7. **#249** — actually process file associations and macOS open events.
8. **#232** — make package imports lightweight with PEP 562 lazy exports.
9. **#235** — implement a shared undo/redo history budget.
10. **#245** — restore quota externally; keep optional workflow hardening separate.
11. **#161** — decide the publication model, then update docs or close.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
