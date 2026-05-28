[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code analysis & rated recommendations: BgRemover

## Rating scale

| Symbol | Priority | Meaning |
|--------|-----------|-----------|
| 🔴 | Critical | Must be fixed – leads to errors, crashes, or inconsistencies |
| 🟠 | High | Should be fixed soon – significantly impairs reliability or maintainability |
| 🟡 | Medium | Recommended – improves code quality, readability, or testability |
| 🟢 | Low | Optional – polishing, supplementary improvements |

---

## Current status (2026, post-round-5)

The monolith→package cut is complete: `BgRemover.py` has been replaced by the `bgremover/` package. Canvas state is encapsulated in `CanvasHistory`, `CanvasLasso`, and `CanvasSelection`; `MainWindow` has been split into toolbar, history popup, worker controller, RightPanel, MenuActions, and RecentFiles. Tests no longer couple to Canvas private fields, and mypy runs without the formerly disabled per-code error classes.

The full historical findings and work logs from rounds 1-5 are archived at [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).

---

## Open polish items

All previously noted polish items have been resolved. The project currently
has no open recommendations.
