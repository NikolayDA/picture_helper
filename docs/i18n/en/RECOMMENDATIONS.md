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
- **#167 / #168** are closed: the High/Medium findings shipped via PR
  #173/#174; the remaining findings continue focused in #176/#177/#178.

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The existing documentation languages (es/fr/uk/zh) are not yet
  runtime locales; add them key-for-key in `bgremover.i18n` if needed and
  protect them with parity/smoke tests.

## Open GitHub Issues — Priority Assessment (2026-06-04)

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#163](https://github.com/NikolayDA/picture_helper/issues/163) | CHANGELOG.md: broken version links + missing 2.3.0 entries | 🔴 High | 🟡 Medium | Content changes → Ready for PR; git tagging needs refinement |
| [#177](https://github.com/NikolayDA/picture_helper/issues/177) | Test-audit follow-up (Medium): behavioral assertions + coverage gaps | 🟠 High | 🟡 Medium | Ready for PR (from #168) |
| [#165](https://github.com/NikolayDA/picture_helper/issues/165) | TESTING.md: three inaccuracies vs. current codebase | 🟡 Medium | 🟢 Low | Ready for PR |
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Code-review follow-up (Low): E741, check_untyped_defs, cancel_ai UX, shutdown_all | 🟡 Medium | 🟢 Low | Ready for PR (from #167) |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README audit: one broken external link, one internal-jargon note | 🟡 Medium | 🟢 Low | "Runde 5" jargon fixed; clone URL deferred (owner decision) |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Test-audit follow-up (Low): decouple from private internals + dedupe | 🟢 Low | 🟡 Medium | Ready for PR (from #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Comment audit: language inconsistencies and minor phrasing inaccuracy | 🟢 Low | 🟢 Low | Ready for PR |

### Recommended PR Order

1. **#165** — TESTING.md corrections: low-risk and well-scoped.
2. **#163 content** — Add missing 2.3.0 features + `[Unreleased]` entries to CHANGELOG; handle git tagging separately.
3. **#177** — Test hardening: add behavioral assertions + close coverage gaps (from #168).
4. **#176** — Code-quality batch from #167: E741, check_untyped_defs, cancel_ai UX, shutdown_all.
5. **#178** — Decouple tests from private internals + reduce duplicate tests (from #168).
6. **#166** — Docstring language cleanup as a small housekeeping PR.
7. **#161 deferred** — "Runde 5" done; only the clone URL remains (owner decision on repo visibility).

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, done or discarded
  where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
