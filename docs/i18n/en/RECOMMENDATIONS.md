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

The active code-analysis list is empty. The latest follow-up review has been
implemented and covered by tests; ruff, mypy, and the local suite remain the
baseline before new PRs.

### Completed Since The Last Review

- **N1/N2/N4/N5/N6/N7/N8** are done: magic-wand error path, rotation size
  limit, honest file extensions, atomic save, CI Qt packages, lazy `rembg`
  import, and the `load_image` docstring.
- **O2/O3/O4/O5/O6** are implemented: Linux AppImage/`.deb`, release workflow,
  weekly full matrix, `ui_smoke` in PR/Full CI, and tool shortcuts with
  platform-correct hints.
- **#164** is done and merged (PR #172): Python 3.11 AI note, Releases link,
  and localized UI strings in the install guides.

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The existing documentation languages (es/fr/uk/zh) are not yet
  runtime locales; add them key-for-key in `bgremover.i18n` if needed and
  protect them with parity/smoke tests.

## Open GitHub Issues — Priority Assessment (2026-06-04)

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#168](https://github.com/NikolayDA/picture_helper/issues/168) | Test suite audit: stale tests, missing assertions, private coupling, coverage gaps | 🔴 High | 🔴 High | 🔴 findings done (PR #173); 🟠/🟡 open — split & refine |
| [#167](https://github.com/NikolayDA/picture_helper/issues/167) | Code review: quality, maintainability & minor issues | 🔴 High | 🟡 Medium | Medium findings (race, TOCTOU) → in PR #174; Low findings: batch together |
| [#163](https://github.com/NikolayDA/picture_helper/issues/163) | CHANGELOG.md: broken version links + missing 2.3.0 entries | 🔴 High | 🟡 Medium | Content changes → Ready for PR; git tagging needs refinement |
| [#165](https://github.com/NikolayDA/picture_helper/issues/165) | TESTING.md: three inaccuracies vs. current codebase | 🟡 Medium | 🟢 Low | Ready for PR |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README audit: one broken external link, one internal-jargon note | 🟡 Medium | 🟢 Low | "Runde 5" jargon fix → Ready for PR; clone URL → Blocked (repo visibility decision) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Comment audit: language inconsistencies and minor phrasing inaccuracy | 🟢 Low | 🟢 Low | Ready for PR |

### Recommended PR Order

1. **#167 Medium** — Double-checked lock in `_ensure_rembg_remove()` + TOCTOU window in `open_validated_image`: implemented in **PR #174** (merge pending; Low findings separate).
2. **#165** — TESTING.md corrections: low-risk and well-scoped.
3. **#163 content** — Add missing 2.3.0 features + `[Unreleased]` entries to CHANGELOG; handle git tagging separately.
4. **#161 partial** — Remove "Runde 5" jargon from README architecture text (clone URL fix requires a repo-visibility decision).
5. **#166** — Docstring language cleanup as a small housekeeping PR.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, done or discarded
  where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
