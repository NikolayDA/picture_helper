[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-09)

The active code-analysis list is empty. Ruff, mypy, and the local test suite
remain the baseline before new PRs. Since the 2026-07-06 snapshot, all three
redesign follow-ups **#499/#500/#501** (PR #504) and the dead-code finding
**#503** (PR #506; #505 was an accidental empty-diff merge, the content
landed via #506) are closed; on top of that, the icon/status-bar polish
**PR #507/#508**. New are the UI bug **#509** (tool cursor ignores canvas
zoom) and **#510** (this snapshot refresh). GitHub currently shows **13**
open issues.

### Completed Since The Last Review

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8** and **O2–O7** remain done;
  epics **#329/#344/#358/#384** (N9–N12) plus export fix **#363** are merged
  and archived.
- **Closed since the 2026-06-25 review:** **#404/#406/#408** (PR #412) —
  preview/dead-code/audit findings done.
- **Redesign core, rail/zoom, card inspector, Dark Mode:** **#413/#414/
  #455–#464/#474–#489** landed via PR #412/#423/#466/#467/#473/#482/#489;
  **#490** and **#433/#434** likewise (epic **#426** now hinges only on
  **#435**).
- **Closed since 2026-07-06:** **#499/#500/#501** (PR #504 — light theme
  aligned with the prototype, screenshot generator repaired, dead widgets
  removed; the #500 blocker in front of **#432** is gone) and **#503**
  (PR #506 — `CanvasHistory`/`_make_panel_btn`/dead theme constants removed).

### New Since The Last Review

- **#509 🟠:** brush/eraser cursor does not scale with the canvas zoom —
  displayed tool size ≠ actual affected area (also hits the height brushes;
  cause precisely located in `set_tool`/`set_brush_size`).
- **#510 🟢:** triage snapshot was overtaken by PR #504 merged 30 minutes
  later — resolved by this update.

### Still Open

- **O1 🟠 — Additional runtime languages.** DE/EN are switchable; es/fr/uk/zh
  are still missing as runtime locales (matches **#430**).
- **O8 🟢 — Prototype inaccuracy:** height tools stay locked in the mockup
  after generation; mockup-only, the real app is unaffected (#347).

## Open GitHub Issues — Triage Status (2026-07-09)

As of 2026-07-09, GitHub shows **13** open issues: UI bug (**#509**), this
docs snapshot (**#510**), i18n/docs (**#425/#430/#431/#432**), rollout/release
(**#426/#435/#392/#389**), and backlog/external items (**#299/#318/#245**).

### Sensible Bundles

- **UI bug:** #509 is precisely located (the cursor is never recomputed on
  `zoomChanged`) and the only open code finding — a good next PR.
- **i18n/docs:** #430 unblocks the parity tests; #431/#432 follow after the
  UI freeze (the #500 blocker in front of #432 fell with PR #504).
- **Rollout/release:** #426 hinges only on #435; coordinate with #392, then
  close #426/#389.
- **Backlog:** #299 after the release; refine #318 first; #245 stays
  externally blocked.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort.

| # | Title | Relevance | Complexity | Recommended next step |
|---|-------|-----------|------------|-----------------------|
| [#509](https://github.com/NikolayDA/picture_helper/issues/509) | Brush/eraser cursor ignores canvas zoom | 🟠 High | 🟡 Medium | **Ready for PR** – rescale the cursor on `zoomChanged`/size changes. |
| [#510](https://github.com/NikolayDA/picture_helper/issues/510) | Triage snapshot outdated (as of 2026-07-06) | 🟢 Low | 🟢 Low | **In progress** – this snapshot resolves it. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internationalization & documentation | 🟠 High | 🟡 Medium | **In progress** – #430/#431/#432 open. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | New UI strings (steps/cards/navigation) | 🟠 High | 🟡 Medium | **Ready for PR** – ES/FR/UK/ZH; DE/EN via PR #423. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Update ANLEITUNG & README to guided workflow | 🟡 Medium | 🟡 Medium | **After UI freeze** – 6-language mirror, link tests. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Recreate app screenshots for the redesign | 🟢 Low | 🟢 Low | **After UI freeze** – #500 blocker gone (PR #504). |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: QA & rollout of the redesign | 🟠 High | 🟢 Low | **Nearly done** – only #435 remains open. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG & version bump for the redesign | 🟡 Medium | 🟢 Low | **Align with #392** – settle the release sequence. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Cut release v2.5.0 | 🟠 High | 🟡 Medium | **Ready** – decide the sequence with the redesign. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Update user docs & cut release | 🟠 High | 🟢 Low | **Close after #392** – only the release remains. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | **After the release** – highest impact first. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Job-level permission overrides in reusable WF | 🟢 Low | 🟡 Medium | **Needs refinement** – prove GitHub semantics. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan "Quota exceeded" | 🟡 Medium | 🟢 Low | **Blocked (external)** – OpenAI billing/quota. |

### Recommended Next (PR order)

1. **#509** first — the only open code bug, cause already located.
2. Pull **#430** forward — unblocks i18n parity; then **#431**/**#432**.
3. **Release:** run **#435** + **#392** in a coordinated way, then close
   **#426**/**#389**.
4. **#299** after the release; research **#318** only; keep **#245**
   externally blocked.

## Previous Rounds

- **2026-07-06** — #499/#500/#501 (PR #504) and #503 (PR #506) completed;
  icon/status-bar polish via PR #507/#508.
- **2026-07-05** — #490 (snapshot drift) in progress, Dark Mode/rail-icon
  wave and card inspector (#413/#414) completed.
- **2026-06-29** — #404/#406/#408 completed (PR #412), redesign wave opened.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
