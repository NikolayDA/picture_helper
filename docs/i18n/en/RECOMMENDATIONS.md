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

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The existing documentation languages (es/fr/uk/zh) are not yet
  runtime locales; add them key-for-key in `bgremover.i18n` if needed and
  protect them with parity/smoke tests.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, done or discarded
  where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
